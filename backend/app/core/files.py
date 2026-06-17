import re
from pathlib import Path
from uuid import uuid4

from app.core.config import UPLOAD_DIR


def safe_pdf_name(filename: str | None) -> str:
    original = Path(filename or "").name
    if not original or Path(original).suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported")

    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(original).stem).strip("._-")
    return f"{stem or 'resume'}.pdf"


def unique_pdf_path(filename: str | None) -> Path:
    safe_name = safe_pdf_name(filename)
    stem = Path(safe_name).stem
    return UPLOAD_DIR / f"{stem}_{uuid4().hex[:8]}.pdf"


def resolve_uploaded_pdf(filename: str) -> Path:
    if not filename or filename != Path(filename).name:
        raise ValueError("Invalid resume filename")

    path = (UPLOAD_DIR / filename).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if path.parent != upload_root or path.suffix.lower() != ".pdf":
        raise ValueError("Invalid resume filename")
    if not path.is_file():
        raise FileNotFoundError(f"Resume PDF not found: {filename}")
    return path
