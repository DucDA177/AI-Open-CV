import streamlit as st
from typing import Dict, Any
from openai_client import call_openai_generate_cv
from chatbot.chat_interface import initialize_chat_session, render_chat_interface
from chatbot.file_utils import create_docx_from_text, create_pdf_from_text, extract_text_from_upload

# -------- Streamlit UI --------

st.set_page_config(page_title="AI CV Builder - IT", layout="wide", initial_sidebar_state="expanded")

st.title("AI CV Builder - Tạo và cải thiện CV ngành CNTT")
st.markdown("Nhập thông tin hoặc tải lên CV/JD để tạo hoặc cải thiện CV chuyên nghiệp trong ngành CNTT.")

# Initialize chat session
initialize_chat_session()

# Render chat interface in sidebar
render_chat_interface()

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

# Update session state with current form data for chatbot context
st.session_state.full_name = full_name
st.session_state.skills = skills
st.session_state.experiences = experiences
st.session_state.projects = projects
st.session_state.jd_text = jd_text

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
st.caption("Developed by OpenCV Team")
