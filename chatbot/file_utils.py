import io
import tempfile
from typing import List
import docx2txt
import pdfplumber
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a font (optional). Put DejaVuSans.ttf in the same folder, or comment these two lines.
try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    _PDF_FONT = 'DejaVu'
except Exception:
    _PDF_FONT = 'Helvetica'  # fallback built‑in

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

def extract_text_from_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt") or name.endswith(".md"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            # docx2txt expects a path; use temp file
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
        return f"Không trích xuất được văn bản từ tệp: {e}"
