import re
from pathlib import Path
from typing import Dict, List, Tuple

import fitz

from app.data.skills import SKILL_ALIASES, TECH_SKILLS


SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "skills": ["skills", "technical skills", "core skills", "technologies", "tools", "technical toolkit"],
    "experience": ["experience", "work experience", "professional experience", "employment", "internship", "internships"],
    "education": ["education", "academic background"],
    "projects": ["projects", "personal projects", "key projects", "academic projects", "project work"],
    "certifications": ["certifications", "certificates", "licenses"],
}

ACTION_VERBS = {
    "achieved", "architected", "automated", "built", "created", "delivered",
    "designed", "developed", "drove", "enhanced", "implemented", "improved",
    "increased", "integrated", "launched", "led", "optimized", "reduced",
    "scaled", "shipped", "streamlined",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    text_parts: List[str] = []
    with fitz.open(path) as document:
        for page in document:
            text_parts.append(page.get_text("text"))

    return normalize_text("\n".join(text_parts))


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_data(text: str) -> Dict:
    text = normalize_text(text)
    sections = detect_sections(text)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "summary": extract_summary(sections),
        "skills": extract_skills(text, sections),
        "experience": extract_experience(sections),
        "education": extract_list_section(sections, "education"),
        "projects": extract_projects(sections),
        "certifications": extract_list_section(sections, "certifications"),
        "sections": sections,
    }


def detect_sections(text: str) -> Dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header_lookup = {
        alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
    }
    header_pattern = re.compile(
        r"^(" + "|".join(re.escape(alias) for alias in header_lookup) + r")[:\s]*$",
        re.IGNORECASE,
    )

    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        cleaned = re.sub(r"[^A-Za-z/& ]", "", line).strip().lower()
        match = header_pattern.match(cleaned)
        if match:
            current = header_lookup[match.group(1).lower()]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(content).strip() for name, content in sections.items()}


def extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(
        r"(?:(?:\+?\d{1,3})[-.\s]?)?(?:\(?\d{3,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4}",
        text,
    )
    return match.group(0).strip() if match else ""


def extract_name(text: str) -> str:
    contact_pattern = re.compile(r"@|github|linkedin|http|www|phone|email", re.IGNORECASE)
    for line in text.splitlines()[:12]:
        cleaned = line.strip(" -|•\t")
        words = cleaned.split()
        if not cleaned or contact_pattern.search(cleaned):
            continue
        if 2 <= len(words) <= 4 and len(cleaned) <= 60:
            alpha_ratio = sum(ch.isalpha() or ch.isspace() for ch in cleaned) / max(len(cleaned), 1)
            if alpha_ratio > 0.8:
                return cleaned
    return ""


def extract_summary(sections: Dict[str, str]) -> str:
    summary = sections.get("summary", "")
    if summary:
        return " ".join(summary.split())
    header_lines = sections.get("header", "").splitlines()
    candidates = [
        line for line in header_lines
        if len(line.split()) >= 8 and "@" not in line and not re.search(r"\d{6,}", line)
    ]
    return " ".join(candidates[:2])


def extract_skills(text: str, sections: Dict[str, str]) -> List[str]:
    search_space = sections.get("skills") or text
    found = set()
    lower_space = search_space.lower()
    lower_text = text.lower()

    for skill in TECH_SKILLS:
        terms = [skill, *SKILL_ALIASES.get(skill, [])]
        if any(term_in_text(term, lower_space) or term_in_text(term, lower_text) for term in terms):
            found.add(skill)

    if sections.get("skills"):
        for token in re.split(r"[,|/;•\n]", sections["skills"]):
            cleaned = token.strip(" .:-").lower()
            if 1 < len(cleaned) <= 35 and not cleaned.startswith(("and ", "with ")):
                found.add(cleaned)

    return sorted(found)


def term_in_text(term: str, lower_text: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return bool(re.search(pattern, lower_text))


def extract_experience(sections: Dict[str, str]) -> List[Dict[str, object]]:
    content = sections.get("experience", "")
    blocks = split_blocks(content)
    if not blocks and content:
        blocks = [content]

    experience = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        bullets = extract_bullets("\n".join(lines[1:])) if len(lines) > 1 else extract_bullets(block)
        experience.append(
            {
                "title": lines[0],
                "company": infer_company(lines),
                "dates": infer_dates(block),
                "bullets": bullets,
            }
        )
    return experience


def extract_projects(sections: Dict[str, str]) -> List[Dict[str, object]]:
    projects = []
    for block in split_blocks(sections.get("projects", "")):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines:
            projects.append({"name": lines[0], "description": " ".join(lines[1:]), "bullets": extract_bullets(block)})
    return projects


def extract_list_section(sections: Dict[str, str], name: str) -> List[str]:
    content = sections.get(name, "")
    items = []
    for line in content.splitlines():
        cleaned = line.strip(" •-–\t")
        if cleaned:
            items.append(cleaned)
    return items


def extract_bullets(text: str) -> List[str]:
    bullets = []
    for line in text.splitlines():
        cleaned = line.strip(" •-–\t")
        if len(cleaned.split()) >= 4:
            bullets.append(cleaned)
    if bullets:
        return bullets
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if len(sentence.split()) >= 6]


def split_blocks(content: str) -> List[str]:
    if not content.strip():
        return []
    blocks = re.split(r"\n\s*\n", content.strip())
    if len(blocks) > 1:
        return [block.strip() for block in blocks if block.strip()]
    lines = content.splitlines()
    starts: List[int] = []
    for index, line in enumerate(lines):
        if infer_dates(line) or re.search(r"\b(engineer|developer|intern|manager|analyst|consultant)\b", line, re.I):
            starts.append(index)
    if len(starts) <= 1:
        return [content.strip()]
    starts.append(len(lines))
    return ["\n".join(lines[starts[i]:starts[i + 1]]).strip() for i in range(len(starts) - 1)]


def infer_dates(text: str) -> str:
    date_pattern = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s?\d{4}\s?[-–]\s?(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s?\d{4})"
    match = re.search(date_pattern, text, re.IGNORECASE)
    return match.group(0) if match else ""


def infer_company(lines: List[str]) -> str:
    for line in lines[1:3]:
        if not infer_dates(line) and len(line.split()) <= 8:
            return line
    return ""


def count_action_verbs(text: str) -> int:
    return sum(1 for word in re.findall(r"\b[a-zA-Z]+\b", text.lower()) if word in ACTION_VERBS)


def quantified_bullets(bullets: List[str]) -> Tuple[int, int]:
    quantified = [bullet for bullet in bullets if re.search(r"\d+|%|\$|x\b", bullet, re.IGNORECASE)]
    return len(quantified), len(bullets)
