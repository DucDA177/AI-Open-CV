import os
import io
import json
from typing import Dict, Any, List

import streamlit as st
import openai
import docx2txt
import pdfplumber
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# -------- OpenAI client (configure via env vars) --------
# Set these before running:
#   OPENAI_API_KEY="..."            (required)
#   OPENAI_BASE_URL="https://api.openai.com/v1"  (optional override)
client = openai.OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://aiportalapi.stu-platform.live/jpe"),
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

# Register a font (optional). Put DejaVuSans.ttf in the same folder, or comment these two lines.
try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    _PDF_FONT = 'DejaVu'
except Exception:
    _PDF_FONT = 'Helvetica'  # fallback built‑in

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

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Lỗi OpenAI API: {e}")
        return ""

# -------- DOCX / PDF export helpers --------

def create_docx_from_text(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def create_pdf_from_text(text: str) -> bytes:
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin

    # Use registered font or fallback
    c.setFont(_PDF_FONT, 11)

    # simple wrap
    lines: List[str] = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        cur = ""
        for w in words:
            trial = cur + (" " if cur else "") + w
            if len(trial) > 90:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
        lines.append("")

    for line in lines:
        if y < margin + 14:
            c.showPage()
            c.setFont(_PDF_FONT, 11)
            y = height - margin
        c.drawString(margin, y, line)
        y -= 14

    c.save()
    bio.seek(0)
    return bio.read()

# -------- File text extraction --------

def extract_text_from_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt") or name.endswith(".md"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            # docx2txt expects a path; use temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(uploaded_file.read())
                tmp.flush()
                text = docx2txt.process(tmp.name) or ""
            return text
        if name.endswith(".pdf"):
            text = []
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.warning(f"Không trích xuất được văn bản từ tệp: {e}")
        return ""

# -------- Streamlit UI --------

st.set_page_config(page_title="AI CV Builder - IT", layout="centered")
st.title("AI CV Builder - Tạo và cải thiện CV ngành CNTT")
st.markdown("Nhập thông tin hoặc tải lên CV/JD để tạo hoặc cải thiện CV chuyên nghiệp trong ngành CNTT.")

with st.expander("Thông tin cá nhân"):
    full_name = st.text_input("Họ và tên", "Nguyễn Văn A")
    email = st.text_input("Email", "nguyenvana@example.com")
    phone = st.text_input("Số điện thoại", "09xxxxxxxx")
    education = st.text_input("Học vấn", "Đại học CNTT - Khoa CNTT")
    skills_input = st.text_area("Kỹ năng (ngăn cách bằng dấu phẩy)", "Python, Django, REST API, PostgreSQL")
    skills = [s.strip() for s in skills_input.split(",") if s.strip()]

    exp_raw = st.text_area("Kinh nghiệm (mỗi dòng: vị trí | công ty | năm | mô tả)",
                           "Backend Developer | ABC Tech | 2 | Xây dựng REST API giúp tăng tốc xử lý dữ liệu")
    experiences = []
    for line in exp_raw.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        exp = {
            "position": parts[0] if len(parts) > 0 else "",
            "company": parts[1] if len(parts) > 1 else "",
            "years": parts[2] if len(parts) > 2 else "",
            "achievements": parts[3] if len(parts) > 3 else "",
        }
        experiences.append(exp)

    projects_raw = st.text_area("Dự án (mỗi dòng: tên | công nghệ | mô tả)",
                                "Hệ thống quản lý kho | Python, PostgreSQL | Quản lý tồn kho")
    projects = []
    for line in projects_raw.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        projects.append({
            "name": parts[0] if len(parts) > 0 else "",
            "tech": parts[1] if len(parts) > 1 else "",
            "desc": parts[2] if len(parts) > 2 else "",
        })

with st.expander("Mô tả công việc (JD)"):
    jd_text = st.text_area("Dán nội dung JD", "")

with st.expander("Tải lên tệp (CV/JD) — .txt/.md/.docx/.pdf"):
    uploaded = st.file_uploader("Chọn tệp", type=["txt", "md", "docx", "pdf"])
    uploaded_cv_text = extract_text_from_upload(uploaded) if uploaded else ""

st.markdown("### Hành động")
col1, col2, col3 = st.columns(3)
with col1:
    create_new = st.button("Tạo CV mới")
with col2:
    improve_jd = st.button("Cải thiện theo JD")
with col3:
    improve_upload = st.button("Cải thiện từ tệp tải lên")

user_profile = {
    "full_name": full_name,
    "email": email,
    "phone": phone,
    "education": education,
    "skills": skills,
    "experiences": experiences,
    "projects": projects,
}

generated_cv_text = ""

if create_new:
    st.info("Đang tạo CV, vui lòng chờ...")
    generated_cv_text = call_openai_generate_cv(user_profile, {"raw_text": ""})
elif improve_jd:
    st.info("Đang cải thiện CV theo JD, vui lòng chờ...")
    generated_cv_text = call_openai_generate_cv(user_profile, {"raw_text": jd_text})
elif improve_upload:
    if not uploaded_cv_text:
        st.warning("Vui lòng tải lên file CV trước.")
    else:
        st.info("Đang cải thiện CV từ file upload...")
        merged = (uploaded_cv_text + ("\n\nJD:\n" + jd_text if jd_text else ""))
        generated_cv_text = call_openai_generate_cv(user_profile, {"raw_text": merged})

if generated_cv_text:
    st.success("CV đã sẵn sàng.")
    edited_text = st.text_area("Xem và chỉnh sửa CV tại đây:", value=generated_cv_text, height=400, key="cv_preview")

    colw, colp = st.columns(2)
    with colw:
        docx_bytes = create_docx_from_text(edited_text)
        st.download_button("Tải xuống Word (.docx)", data=docx_bytes,
                           file_name=f"{full_name.replace(' ', '_')}_CV.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with colp:
        pdf_bytes = create_pdf_from_text(edited_text)
        st.download_button("Tải xuống PDF (.pdf)", data=pdf_bytes,
                           file_name=f"{full_name.replace(' ', '_')}_CV.pdf",
                           mime="application/pdf")

st.markdown("---")
st.caption("Developed with Streamlit and OpenAI API")
