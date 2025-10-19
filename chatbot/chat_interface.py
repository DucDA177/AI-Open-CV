import time
import streamlit as st
from typing import Dict, List
from openai_client import build_chat_system_prompt, call_openai_chat, call_openai_chat_batched, call_openai_chat_with_functions
from chatbot.file_utils import extract_text_from_upload

def initialize_chat_session():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_enabled" not in st.session_state:
        st.session_state.chat_enabled = True
    if "file_processed" not in st.session_state:
        st.session_state.file_processed = False

def add_chat_message(role: str, content: str):
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": time.time()
    })

def get_user_context():
    """Get current user profile data for chatbot context"""
    return {
        "full_name": st.session_state.get("full_name", ""),
        "skills": st.session_state.get("skills", []),
        "experiences": st.session_state.get("experiences", []),
        "projects": st.session_state.get("projects", []),
        "jd_text": st.session_state.get("jd_text", "")
    }

def process_ai_response():
    """Process AI response for quick action buttons"""
    # Prepare context for AI
    user_context = get_user_context()
    context_info = ""
    if user_context["full_name"]:
        context_info += f"\n\nThông tin người dùng:\n- Tên: {user_context['full_name']}"
    if user_context["skills"]:
        context_info += f"\n- Kỹ năng: {', '.join(user_context['skills'])}"
    if user_context["jd_text"]:
        context_info += f"\n- JD hiện tại: {user_context['jd_text'][:200]}..."
    
    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": build_chat_system_prompt() + context_info}
    ]
    
    # Add conversation history (last 5 exchanges)
    recent_messages = st.session_state.chat_messages[-10:]  # Last 5 exchanges
    for msg in recent_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Get AI response using function calling for structured responses
    with st.spinner("Trợ lý đang suy nghĩ..."):
        ai_response = call_openai_chat_with_functions(messages)
        add_chat_message("assistant", ai_response)
    
    # Refresh to show new messages immediately
    st.rerun()

def render_floating_chat():
    """Render floating chat button and interface using Streamlit components"""
    # Add CSS for floating button
    st.markdown("""
    <style>
    .floating-chat-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .floating-chat-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat visibility state
    if "chat_visible" not in st.session_state:
        st.session_state.chat_visible = False
    
    # Floating button using Streamlit button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("🤖 Trợ lý AI CV", key="floating_chat_btn", 
                    use_container_width=True, 
                    help="Nhấn để mở trợ lý AI CV"):
            st.session_state.chat_visible = not st.session_state.chat_visible
            st.rerun()
    
    # Show chat interface if visible
    if st.session_state.chat_visible:
        # Create a container for the chat interface
        with st.container():
            st.markdown("---")
            st.markdown("### 💬 Trợ lý CV AI")
            
            # Quick action buttons
            st.markdown("**Hành động nhanh:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💡 Tư vấn CV", use_container_width=True, key="quick_cv"):
                    add_chat_message("user", "Hãy tư vấn giúp tôi cải thiện CV")
                    process_ai_response()
            with col2:
                if st.button("📋 Phân tích JD", use_container_width=True, key="quick_jd"):
                    add_chat_message("user", "Hãy phân tích JD này và gợi ý cải thiện")
                    process_ai_response()
            
            col3, col4 = st.columns(2)
            with col3:
                if st.button("📊 So sánh CV-JD", use_container_width=True, key="quick_compare"):
                    add_chat_message("user", "Hãy so sánh CV của tôi với JD và chỉ ra điểm phù hợp")
                    process_ai_response()
            with col4:
                if st.button("🎯 Kỹ năng cần", use_container_width=True, key="quick_skills"):
                    add_chat_message("user", "Dựa trên JD, hãy gợi ý kỹ năng tôi cần phát triển")
                    process_ai_response()
            
            # Chat messages display
            st.markdown("---")
            st.markdown("**Cuộc trò chuyện:**")
            
            # Display chat messages
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.chat_messages[-10:]:  # Show last 10 messages
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                            <strong>Bạn:</strong> {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                            <strong>Trợ lý:</strong> {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
            
            # File upload in chat
            st.markdown("---")
            st.markdown("**Tải lên file để phân tích:**")
            
            # Combined file uploader for both images and documents
            uploaded_file = st.file_uploader(
                "Chọn file CV/JD hoặc hình ảnh (.txt, .md, .docx, .pdf, .jpg, .jpeg, .png)",
                type=["txt", "md", "docx", "pdf", "jpg", "jpeg", "png"],
                key="floating_chat_file_uploader"
            )
            
            # Handle file upload
            if uploaded_file and not st.session_state.file_processed:
                # Check if it's an image file
                if uploaded_file.type.startswith('image/'):
                    # Display the uploaded image
                    st.image(uploaded_file, caption=f"Ảnh đã tải lên: {uploaded_file.name}", use_column_width=True)
                    add_chat_message("user", f"Tôi đã tải lên hình ảnh: {uploaded_file.name}")
                    # Mark file as processed
                    st.session_state.file_processed = True
                    # Process AI response for image analysis
                    process_ai_response()
                else:
                    # Handle document files
                    file_text = extract_text_from_upload(uploaded_file)
                    if file_text:
                        add_chat_message("user", f"Tôi đã tải lên file: {uploaded_file.name}\n\nNội dung file:\n{file_text[:1000]}...")
                        # Mark file as processed
                        st.session_state.file_processed = True
                        # Process AI response for file analysis
                        process_ai_response()
            
            # Reset flag when no files are uploaded
            elif not uploaded_file:
                st.session_state.file_processed = False
            
            # Chat input with form to prevent infinite loops
            st.markdown("---")
            with st.form(key="floating_chat_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Nhập câu hỏi của bạn...",
                    placeholder="Ví dụ: Làm thế nào để cải thiện phần kinh nghiệm trong CV?\n\nBạn có thể nhập nhiều dòng ở đây...",
                    height=100,
                    max_chars=2000,
                    key="floating_chat_input"
                )
                submitted = st.form_submit_button("Gửi")
                
                if submitted and user_input:
                    # Add user message
                    add_chat_message("user", user_input)
                    
                    # Prepare context for AI
                    user_context = get_user_context()
                    context_info = ""
                    if user_context["full_name"]:
                        context_info += f"\n\nThông tin người dùng:\n- Tên: {user_context['full_name']}"
                    if user_context["skills"]:
                        context_info += f"\n- Kỹ năng: {', '.join(user_context['skills'])}"
                    if user_context["jd_text"]:
                        context_info += f"\n- JD hiện tại: {user_context['jd_text'][:200]}..."
                    
                    # Prepare messages for OpenAI
                    messages = [
                        {"role": "system", "content": build_chat_system_prompt() + context_info}
                    ]
                    
                    # Add conversation history (last 5 exchanges)
                    recent_messages = st.session_state.chat_messages[-10:]  # Last 5 exchanges
                    for msg in recent_messages:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Get AI response using batched call for better performance
                    with st.spinner("Trợ lý đang suy nghĩ..."):
                        ai_response = call_openai_chat_batched(messages)
                        add_chat_message("assistant", ai_response)
                    
                    # Refresh to show new messages immediately
                    st.rerun()
            
            # Close button
            if st.button("Đóng trợ lý", key="close_chat"):
                st.session_state.chat_visible = False
                st.rerun()


def render_chat_interface():
    """Render the chat interface in sidebar"""
    with st.sidebar:
        st.markdown("### 💬 Trợ lý CV AI")
        
        # Chat toggle
        chat_enabled = st.checkbox(
            "Bật trợ lý chat", 
            value=st.session_state.get("chat_enabled", True),
            key="chat_toggle"
        )
        
        if not chat_enabled:
            st.info("Trợ lý chat đã tắt. Bật để nhận hỗ trợ.")
            return
        
        # Quick action buttons
        st.markdown("**Hành động nhanh:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💡 Tư vấn CV", use_container_width=True):
                add_chat_message("user", "Hãy tư vấn giúp tôi cải thiện CV")
                # Process AI response for quick action
                process_ai_response()
        with col2:
            if st.button("📋 Phân tích JD", use_container_width=True):
                add_chat_message("user", "Hãy phân tích JD này và gợi ý cải thiện")
                # Process AI response for quick action
                process_ai_response()
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📊 So sánh CV-JD", use_container_width=True):
                add_chat_message("user", "Hãy so sánh CV của tôi với JD và chỉ ra điểm phù hợp")
                # Process AI response for quick action
                process_ai_response()
        with col4:
            if st.button("🎯 Kỹ năng cần", use_container_width=True):
                add_chat_message("user", "Dựa trên JD, hãy gợi ý kỹ năng tôi cần phát triển")
                # Process AI response for quick action
                process_ai_response()
        
        # Chat messages display
        st.markdown("---")
        st.markdown("**Cuộc trò chuyện:**")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages[-10:]:  # Show last 10 messages
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style='background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <strong>Bạn:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <strong>Trợ lý:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        
        # File upload in chat
        st.markdown("---")
        st.markdown("**Tải lên file để phân tích:**")
        
        # Combined file uploader for both images and documents
        uploaded_file = st.file_uploader(
            "Chọn file CV/JD hoặc hình ảnh (.txt, .md, .docx, .pdf, .jpg, .jpeg, .png)",
            type=["txt", "md", "docx", "pdf", "jpg", "jpeg", "png"],
            key="chat_file_uploader"
        )
        
        # Handle file upload
        if uploaded_file and not st.session_state.file_processed:
            # Check if it's an image file
            if uploaded_file.type.startswith('image/'):
                # Display the uploaded image
                st.image(uploaded_file, caption=f"Ảnh đã tải lên: {uploaded_file.name}", use_column_width=True)
                add_chat_message("user", f"Tôi đã tải lên hình ảnh: {uploaded_file.name}")
                # Mark file as processed
                st.session_state.file_processed = True
                # Process AI response for image analysis
                process_ai_response()
            else:
                # Handle document files
                file_text = extract_text_from_upload(uploaded_file)
                if file_text:
                    add_chat_message("user", f"Tôi đã tải lên file: {uploaded_file.name}\n\nNội dung file:\n{file_text[:1000]}...")
                    # Mark file as processed
                    st.session_state.file_processed = True
                    # Process AI response for file analysis
                    process_ai_response()
        
        # Reset flag when no files are uploaded
        elif not uploaded_file:
            st.session_state.file_processed = False
        
        # Chat input with form to prevent infinite loops
        st.markdown("---")
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Nhập câu hỏi của bạn...",
                placeholder="Ví dụ: Làm thế nào để cải thiện phần kinh nghiệm trong CV?\n\nBạn có thể nhập nhiều dòng ở đây...",
                height=200,
                max_chars=2000
            )
            submitted = st.form_submit_button("Gửi")
            
            if submitted and user_input:
                # Add user message
                add_chat_message("user", user_input)
                
                # Prepare context for AI
                user_context = get_user_context()
                context_info = ""
                if user_context["full_name"]:
                    context_info += f"\n\nThông tin người dùng:\n- Tên: {user_context['full_name']}"
                if user_context["skills"]:
                    context_info += f"\n- Kỹ năng: {', '.join(user_context['skills'])}"
                if user_context["jd_text"]:
                    context_info += f"\n- JD hiện tại: {user_context['jd_text'][:200]}..."
                
                # Prepare messages for OpenAI
                messages = [
                    {"role": "system", "content": build_chat_system_prompt() + context_info}
                ]
                
                # Add conversation history (last 5 exchanges)
                recent_messages = st.session_state.chat_messages[-10:]  # Last 5 exchanges
                for msg in recent_messages:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Get AI response using batched call for better performance
                with st.spinner("Trợ lý đang suy nghĩ..."):
                    ai_response = call_openai_chat_batched(messages)
                    add_chat_message("assistant", ai_response)
                
                # Refresh to show new messages immediately
                st.rerun()
