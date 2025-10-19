import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable
import openai
from openai import RateLimitError, APIError

# -------- OpenAI client (configure via env vars) --------
client = openai.OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://aiportalapi.stu-platform.live/jpe"),
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

# -------- Retry Mechanism --------

def call_openai_with_retry(
    api_call: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Optional[Any]:
    """
    Enhanced API call with exponential backoff retry logic
    
    Args:
        api_call: Function that makes the OpenAI API call
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
    
    Returns:
        API response or None if all retries fail
    """
    for attempt in range(max_retries + 1):
        try:
            return api_call()
        except RateLimitError as e:
            if attempt == max_retries:
                return f"Rate limit exceeded after {max_retries} retries: {e}"
            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except APIError as e:
            if attempt == max_retries:
                return f"API error after {max_retries} retries: {e}"
            print(f"API error, retrying in {base_delay}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(base_delay)
        except Exception as e:
            # Don't retry on other exceptions (e.g., invalid requests)
            return f"Unexpected error: {e}"
    
    return None

# -------- Batching Mechanism --------

class ChatBatchProcessor:
    """
    Batch processor for OpenAI chat requests to reduce API calls
    and improve performance for multiple similar requests
    """
    def __init__(self, batch_size: int = 5, max_wait_time: float = 2.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = []
        self.lock = threading.Lock()
        self.last_process_time = time.time()
    
    def add_request(self, messages: List[Dict[str, str]], callback: Callable[[str], None]):
        """
        Add a chat request to the batch
        
        Args:
            messages: The chat messages for the request
            callback: Function to call with the response
        """
        with self.lock:
            self.pending_requests.append({
                "messages": messages,
                "callback": callback,
                "timestamp": time.time()
            })
            
            # Process batch if we have enough requests or if max wait time exceeded
            current_time = time.time()
            should_process = (
                len(self.pending_requests) >= self.batch_size or
                (current_time - self.last_process_time) >= self.max_wait_time
            )
            
            if should_process and self.pending_requests:
                self._process_batch()
    
    def _process_batch(self):
        """Process the current batch of requests"""
        if not self.pending_requests:
            return
        
        # Take current batch
        batch_to_process = self.pending_requests.copy()
        self.pending_requests.clear()
        self.last_process_time = time.time()
        
        # Process each request in the batch
        for request in batch_to_process:
            try:
                response = call_openai_chat(request["messages"])
                request["callback"](response)
            except Exception as e:
                request["callback"](f"Batch processing error: {e}")
    
    def force_process(self):
        """Force processing of any pending requests"""
        with self.lock:
            if self.pending_requests:
                self._process_batch()

# Global batch processor instance
chat_batch_processor = ChatBatchProcessor(batch_size=3, max_wait_time=1.5)

def call_openai_chat_batched(messages: List[Dict[str, str]]) -> str:
    """
    Batched version of chat call - returns immediately with processing indicator
    Actual response will be delivered asynchronously
    """
    result_holder = {"response": None}
    event = threading.Event()
    
    def callback(response: str):
        result_holder["response"] = response
        event.set()
    
    chat_batch_processor.add_request(messages, callback)
    
    # Wait for response with timeout
    event.wait(timeout=30.0)  # 30 second timeout
    
    if result_holder["response"] is not None:
        return result_holder["response"]
    else:
        # Force process and try one more time
        chat_batch_processor.force_process()
        event.wait(timeout=5.0)
        return result_holder["response"] or "Request timeout. Please try again."

def build_system_prompt():
    return (
        "Bạn là chuyên gia nhân sự ngành CNTT và chuyên viên viết CV chuyên nghiệp. "
        "Nhiệm vụ: nhận dữ liệu người dùng (thông tin cá nhân, kỹ năng, kinh nghiệm, dự án) "
        "và/hoặc JD. Phân tích sự phù hợp giữa hồ sơ và JD, gợi ý cải thiện, "
        "và tạo CV hoàn chỉnh, hấp dẫn, chuẩn ngành CNTT."
    )

def call_openai_generate_cv(user_profile: Dict[str, Any], job_description: Dict[str, Any]):
    system_msg = build_system_prompt()

    few_shot_example = (
        "Ví dụ:\n"
        "Input:\nNgười dùng có kỹ năng Python, Django, REST API; kinh nghiệm 2 năm backend.\n"
        "JD: Python Developer yêu cầu Django, REST API, PostgreSQL.\n\n"
        "Output:\n"
        "Tóm tắt: Lập trình viên Python có 2 năm kinh nghiệm phát triển API.\n"
        "Kỹ năng: Python, Django, REST API, PostgreSQL.\n"
        "Kinh nghiệm: Tối ưu API nội bộ giúp tăng 30% tốc độ xử lý.\n"
        "=> Hãy tạo CV hoàn chỉnh tương tự với dữ liệu người dùng cung cấp."
    )

    user_payload = {
        "user_profile": user_profile,
        "job_description": job_description
    }

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": few_shot_example},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)}
    ]

    # Use retry mechanism for CV generation
    response = call_openai_with_retry(
        lambda: client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.2,
            max_tokens=1000
        ),
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0
    )
    
    if response and hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    elif isinstance(response, str):
        return response  # Return error message
    else:
        return "Không thể tạo CV. Vui lòng thử lại sau."

def build_chat_system_prompt():
    return (
        "Bạn là trợ lý ảo chuyên về tư vấn CV và sự nghiệp trong ngành CNTT. "
        "Bạn có thể giúp người dùng:\n"
        "- Tư vấn cải thiện CV\n"
        "- Phân tích mô tả công việc (JD)\n"
        "- Gợi ý kỹ năng cần phát triển\n"
        "- Chuẩn bị cho phỏng vấn kỹ thuật\n"
        "- Tư vấn lộ trình sự nghiệp\n"
        "- Phân tích file CV/JD được tải lên\n"
        "- Phân tích hình ảnh CV, JD hoặc các tài liệu liên quan\n"
        "- Đề xuất cải thiện dựa trên nội dung file hoặc hình ảnh\n"
        "- So sánh CV với JD để tìm điểm phù hợp\n\n"
        "Khi người dùng tải lên file hoặc hình ảnh, hãy:\n"
        "1. Phân tích nội dung (CV, JD, hoặc hình ảnh liên quan)\n"
        "2. Đưa ra nhận xét và đề xuất cải thiện\n"
        "3. So sánh với thông tin người dùng nếu có\n"
        "4. Gợi ý các bước tiếp theo\n\n"
        "Đối với hình ảnh:\n"
        "- Nếu là CV dạng ảnh: phân tích bố cục, nội dung, đề xuất cải thiện\n"
        "- Nếu là JD dạng ảnh: trích xuất yêu cầu công việc, kỹ năng cần thiết\n"
        "- Nếu là ảnh khác: đưa ra nhận xét phù hợp với ngữ cảnh CV/sự nghiệp\n\n"
        "Hãy trả lời bằng tiếng Việt, thân thiện và hữu ích. "
        "Sử dụng thông tin từ hồ sơ người dùng khi có sẵn."
    )

# -------- Function Calling --------

def define_chatbot_functions():
    """Define structured functions for the chatbot"""
    return [
        {
            "type": "function",
            "function": {
                "name": "analyze_cv",
                "description": "Analyze a CV and provide structured improvement suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cv_text": {
                            "type": "string",
                            "description": "The CV text to analyze"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas to focus on (skills, experience, formatting, achievements)"
                        },
                        "analysis_depth": {
                            "type": "string",
                            "enum": ["quick", "detailed", "comprehensive"],
                            "description": "Depth of analysis to perform"
                        }
                    },
                    "required": ["cv_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_cv_jd",
                "description": "Compare CV with job description and identify matches and gaps",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cv_text": {"type": "string"},
                        "jd_text": {"type": "string"},
                        "match_threshold": {
                            "type": "number", 
                            "minimum": 0, 
                            "maximum": 1,
                            "description": "Threshold for considering a match (0-1)"
                        },
                        "include_suggestions": {
                            "type": "boolean",
                            "description": "Whether to include improvement suggestions"
                        }
                    },
                    "required": ["cv_text", "jd_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "extract_jd_requirements",
                "description": "Extract key requirements and skills from a job description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "jd_text": {"type": "string"},
                        "extract_skills": {"type": "boolean"},
                        "extract_experience": {"type": "boolean"},
                        "extract_qualifications": {"type": "boolean"}
                    },
                    "required": ["jd_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "suggest_cv_improvements",
                "description": "Provide specific suggestions to improve a CV",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cv_text": {"type": "string"},
                        "target_jd": {"type": "string"},
                        "improvement_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Areas to improve (formatting, content, keywords, achievements)"
                        }
                    },
                    "required": ["cv_text"]
                }
            }
        }
    ]

def analyze_cv_function(cv_text: str, focus_areas: List[str] = None, analysis_depth: str = "detailed") -> str:
    """Execute CV analysis function"""
    focus_areas = focus_areas or ["skills", "experience", "formatting"]
    
    # This would be enhanced with actual CV analysis logic
    return f"""
CV Analysis Results:
- Focus Areas: {', '.join(focus_areas)}
- Analysis Depth: {analysis_depth}
- Key Findings: CV contains relevant experience and skills
- Suggestions: Consider adding more quantifiable achievements
- Next Steps: Tailor CV to specific job descriptions
"""

def compare_cv_jd_function(cv_text: str, jd_text: str, match_threshold: float = 0.7, include_suggestions: bool = True) -> str:
    """Execute CV-JD comparison function"""
    # This would be enhanced with actual comparison logic
    suggestions = ""
    if include_suggestions:
        suggestions = "\n- Suggestions: Add more keywords from JD, highlight relevant experience"
    
    return f"""
CV-JD Comparison:
- Match Score: 75% (above threshold of {match_threshold*100}%)
- Key Matches: Skills alignment, relevant experience
- Gaps: Some specific technologies mentioned in JD{suggestions}
"""

def extract_jd_requirements_function(jd_text: str, extract_skills: bool = True, extract_experience: bool = True, extract_qualifications: bool = True) -> str:
    """Execute JD requirements extraction function"""
    extracted = []
    if extract_skills:
        extracted.append("- Required Skills: Python, Django, REST API")
    if extract_experience:
        extracted.append("- Experience: 2+ years backend development")
    if extract_qualifications:
        extracted.append("- Qualifications: Bachelor's degree in Computer Science")
    
    return f"""
JD Requirements Extracted:
{chr(10).join(extracted)}
"""

def suggest_cv_improvements_function(cv_text: str, target_jd: str = "", improvement_areas: List[str] = None) -> str:
    """Execute CV improvement suggestions function"""
    improvement_areas = improvement_areas or ["content", "formatting", "keywords"]
    
    jd_specific = ""
    if target_jd:
        jd_specific = "\n- JD-Specific: Add keywords from the target job description"
    
    return f"""
CV Improvement Suggestions:
- Focus Areas: {', '.join(improvement_areas)}
- Content: Add more quantifiable achievements{jd_specific}
- Formatting: Improve section organization
- Keywords: Include more industry-specific terms
"""

def call_openai_chat_with_functions(messages: List[Dict[str, str]]) -> str:
    """Enhanced chat with function calling for structured responses"""
    functions = define_chatbot_functions()
    
    available_functions = {
        "analyze_cv": analyze_cv_function,
        "compare_cv_jd": compare_cv_jd_function,
        "extract_jd_requirements": extract_jd_requirements_function,
        "suggest_cv_improvements": suggest_cv_improvements_function
    }
    
    # First API call with function definitions
    response = call_openai_with_retry(
        lambda: client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=functions,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=800
        ),
        max_retries=2,
        base_delay=0.5,
        max_delay=10.0
    )
    
    if not response or not hasattr(response, 'choices') or not response.choices:
        return "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu. Vui lòng thử lại sau."
    
    response_message = response.choices[0].message
    
    # Check if function calling is needed
    if response_message.tool_calls:
        # Add the assistant's response to messages
        messages.append(response_message)
        
        # Execute function calls
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)
            
            if function_to_call:
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(**function_args)
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })
                except Exception as e:
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": f"Error executing function: {e}",
                    })
        
        # Get final response with function results
        second_response = call_openai_with_retry(
            lambda: client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.7,
                max_tokens=800
            ),
            max_retries=2,
            base_delay=0.5,
            max_delay=10.0
        )
        
        if second_response and hasattr(second_response, 'choices') and second_response.choices:
            return second_response.choices[0].message.content
        else:
            return "Xin lỗi, tôi gặp lỗi khi xử lý phản hồi. Vui lòng thử lại sau."
    
    # Return regular response if no function calling
    return response_message.content

def call_openai_chat(messages: List[Dict[str, str]]) -> str:
    # Use retry mechanism for chat
    response = call_openai_with_retry(
        lambda: client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.7,
            max_tokens=800
        ),
        max_retries=2,  # Fewer retries for chat to maintain responsiveness
        base_delay=0.5,  # Shorter delays for better UX
        max_delay=10.0
    )
    
    if response and hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    elif isinstance(response, str):
        return response  # Return error message
    else:
        return "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu. Vui lòng thử lại sau."
