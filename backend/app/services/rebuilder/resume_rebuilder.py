from pathlib import Path
from typing import Dict

from app.core.config import UPLOAD_DIR
from app.services.llm.resume_optimizer import optimize_resume
from app.services.parser.resume_parser import extract_resume_data


OUTPUT_DIR = UPLOAD_DIR / "optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def rebuild_resume(resume_text: str, jd_text: str, rag_context: str, basename: str, output_format: str = "docx") -> Dict:
    structured = extract_resume_data(resume_text)
    optimized = optimize_resume(resume_text, jd_text, rag_context)["optimization"]
    output_format = output_format.lower()

    if output_format == "pdf":
        path = OUTPUT_DIR / f"{Path(basename).stem}_optimized.pdf"
        build_pdf(path, structured, optimized, resume_text)
    else:
        path = OUTPUT_DIR / f"{Path(basename).stem}_optimized.docx"
        build_docx(path, structured, optimized, resume_text)

    return {
        "filename": path.name,
        "path": str(path),
        "download_url": f"/files/optimized/{path.name}",
        "format": output_format,
    }


def build_docx(path: Path, structured: Dict, optimized: Dict, original_text: str) -> None:
    from docx import Document

    document = Document()
    document.add_heading(structured.get("name") or "Optimized Resume", 0)
    contact = " | ".join(filter(None, [structured.get("email"), structured.get("phone")]))
    if contact:
        document.add_paragraph(contact)

    add_docx_section(document, "Targeted Summary", [optimized.get("improved_summary") or structured.get("summary", "")])
    if structured.get("summary") and structured.get("summary") != optimized.get("improved_summary"):
        add_docx_section(document, "Original Summary", [structured.get("summary", "")])
    add_docx_section(document, "Skills", [", ".join(structured.get("skills", []))])
    add_docx_experience(document, structured, optimized)
    add_docx_section(document, "Projects", format_projects(structured))
    add_docx_section(document, "Education", structured.get("education", []))
    add_docx_section(document, "Certifications", structured.get("certifications", []))
    add_docx_section(document, "Preserved Original Resume Content", [original_text])
    document.save(path)


def add_docx_section(document, title: str, items) -> None:
    cleaned = [item for item in items if item]
    if not cleaned:
        return
    document.add_heading(title, level=1)
    for item in cleaned:
        document.add_paragraph(item)


def add_docx_experience(document, structured: Dict, optimized: Dict) -> None:
    experience = structured.get("experience", [])
    if not experience:
        return
    rewrites = {item["original"]: item["improved"] for item in optimized.get("improved_bullets", [])}
    document.add_heading("Experience", level=1)
    for role in experience:
        document.add_heading(role.get("title", ""), level=2)
        meta = " | ".join(filter(None, [role.get("company"), role.get("dates")]))
        if meta:
            document.add_paragraph(meta)
        for bullet in role.get("bullets", []):
            document.add_paragraph(bullet, style="List Bullet")
            improved = rewrites.get(bullet)
            if improved and improved != bullet:
                document.add_paragraph(f"Optimized suggestion: {improved}", style="List Bullet")


def build_pdf(path: Path, structured: Dict, optimized: Dict, original_text: str) -> None:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape

    styles = getSampleStyleSheet()
    story = [Paragraph(escape(structured.get("name") or "Optimized Resume"), styles["Title"])]
    contact = " | ".join(filter(None, [structured.get("email"), structured.get("phone")]))
    if contact:
        story.append(Paragraph(escape(contact), styles["Normal"]))
    story.append(Spacer(1, 12))

    for title, items in [
        ("Targeted Summary", [optimized.get("improved_summary") or structured.get("summary", "")]),
        ("Original Summary", [structured.get("summary", "")] if structured.get("summary") != optimized.get("improved_summary") else []),
        ("Skills", [", ".join(structured.get("skills", []))]),
        ("Experience", format_experience(structured, optimized)),
        ("Projects", format_projects(structured)),
        ("Education", structured.get("education", [])),
        ("Certifications", structured.get("certifications", [])),
        ("Preserved Original Resume Content", [original_text]),
    ]:
        cleaned = [item for item in items if item]
        if not cleaned:
            continue
        story.append(Paragraph(escape(title), styles["Heading2"]))
        for item in cleaned:
            story.append(Paragraph(escape(str(item)), styles["Normal"]))
        story.append(Spacer(1, 8))

    SimpleDocTemplate(str(path), pagesize=LETTER).build(story)


def format_experience(structured: Dict, optimized: Dict):
    rewrites = {item["original"]: item["improved"] for item in optimized.get("improved_bullets", [])}
    lines = []
    for role in structured.get("experience", []):
        lines.append(" | ".join(filter(None, [role.get("title"), role.get("company"), role.get("dates")])))
        for bullet in role.get("bullets", []):
            lines.append(f"- {bullet}")
            improved = rewrites.get(bullet)
            if improved and improved != bullet:
                lines.append(f"  Optimized suggestion: {improved}")
    return lines


def format_projects(structured: Dict):
    lines = []
    for project in structured.get("projects", []):
        lines.append(project.get("name", ""))
        lines.extend([f"- {bullet}" for bullet in project.get("bullets", [])])
    return lines
