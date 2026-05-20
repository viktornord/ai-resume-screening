import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_BYTES = 5 * 1024 * 1024


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")
    return ext


def extract_text(content: bytes, filename: str) -> str:
    if len(content) > MAX_BYTES:
        raise ValueError(f"File {filename} exceeds 5 MB limit.")
    ext = validate_extension(filename)
    if ext == ".pdf":
        return _extract_pdf(content)
    return _extract_docx(content)


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
