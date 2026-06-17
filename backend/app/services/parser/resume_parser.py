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
    "designed", "developed", "drove", "enhanced", "executed", "implemented",
    "identified", "improved", "increased", "integrated", "launched", "led",
    "managed", "optimized", "participated", "performed", "reduced", "scaled",
    "shipped", "streamlined", "supported", "validated", "contributed",
    "collaborated", "completed", "converted",
}

BULLET_PREFIX_PATTERN = re.compile(r"^(?:[•●▪◦*]|[-–—]+|â€¢|â—|â–ª|â—¦)\s*")

DATE_RANGE_PATTERN = re.compile(
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(?:19|20)\d{2}\s*[-–—]\s*"
    r"(?:Present|Current|Now|"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?(?:19|20)\d{2})",
    re.IGNORECASE,
)
DATE_POINT_PATTERN = re.compile(
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)(?:19|20)\d{2}",
    re.IGNORECASE,
)
DATE_ONLY_PATTERN = re.compile(
    rf"^\s*(?:{DATE_RANGE_PATTERN.pattern}|{DATE_POINT_PATTERN.pattern}|(?:19|20)\d{{2}})\s*$",
    re.IGNORECASE,
)


def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    text_parts: List[str] = []
    try:
        with fitz.open(path) as document:
            for page in document:
                text_parts.append(page.get_text("text"))
    except (fitz.EmptyFileError, fitz.FileDataError) as exc:
        raise ValueError("Uploaded resume is not a readable PDF") from exc

    text = normalize_text("\n".join(text_parts))
    if not text:
        raise ValueError("The PDF does not contain extractable text")
    return text


def extract_links_from_pdf(pdf_path: str) -> Dict[str, str]:
    links: Dict[str, str] = {}
    with fitz.open(pdf_path) as document:
        for page in document:
            for link in page.get_links():
                uri = str(link.get("uri") or "").strip()
                if not uri:
                    continue
                lower_uri = uri.lower()
                if "linkedin.com" in lower_uri:
                    links.setdefault("linkedin", uri)
                elif "github.com" in lower_uri:
                    links.setdefault("github", uri)
                elif lower_uri.startswith("mailto:"):
                    links.setdefault("email", uri)
                elif lower_uri.startswith(("http://", "https://")):
                    links.setdefault("portfolio", uri)
    return links


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_data(text: str) -> Dict:
    text = normalize_text(text)
    sections = detect_sections(text)
    skill_groups = extract_skill_groups(sections.get("skills", ""))

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "summary": extract_summary(sections),
        "skills": extract_skills(text, sections, skill_groups),
        "skill_groups": skill_groups,
        "experience": extract_experience(sections),
        "education": extract_list_section(sections, "education"),
        "education_entries": extract_education_entries(sections),
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


def extract_skill_groups(content: str) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    current_group = ""

    for line in [line.strip() for line in content.splitlines() if line.strip()]:
        if ":" in line:
            label, values = line.split(":", 1)
            current_group = label.strip()
            groups.setdefault(current_group, [])
            add_skill_values(groups[current_group], values)
        elif current_group:
            add_skill_values(groups[current_group], line)
        else:
            current_group = "Core Skills"
            groups.setdefault(current_group, [])
            add_skill_values(groups[current_group], line)

    return {label: values for label, values in groups.items() if values}


def add_skill_values(target: List[str], values: str) -> None:
    existing = {item.casefold() for item in target}
    for token in re.split(r"[,|;•\n]", values):
        cleaned = token.strip(" .:-\t")
        if cleaned and cleaned.casefold() not in existing:
            target.append(cleaned)
            existing.add(cleaned.casefold())


def extract_skills(
    text: str,
    sections: Dict[str, str],
    skill_groups: Dict[str, List[str]] | None = None,
) -> List[str]:
    search_space = sections.get("skills") or text
    found = set()
    lower_space = search_space.lower()
    lower_text = text.lower()

    for skill in TECH_SKILLS:
        terms = [skill, *SKILL_ALIASES.get(skill, [])]
        if any(term_in_text(term, lower_space) or term_in_text(term, lower_text) for term in terms):
            found.add(skill)

    for values in (skill_groups or {}).values():
        for token in values:
            cleaned = token.strip(" .:-").lower()
            if 1 < len(cleaned) <= 45 and not cleaned.startswith(("and ", "with ")):
                found.add(cleaned)

    return sorted(found)


def term_in_text(term: str, lower_text: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return bool(re.search(pattern, lower_text))


def extract_experience(sections: Dict[str, str]) -> List[Dict[str, object]]:
    content = sections.get("experience", "")
    dated_entries = extract_dated_entries(content, section_type="experience")
    if dated_entries:
        return dated_entries

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
    content = sections.get("projects", "")
    dated_entries = extract_dated_entries(content, section_type="project")
    if dated_entries:
        return dated_entries

    structured_entries = extract_undated_project_entries(content)
    if structured_entries:
        return structured_entries

    projects = []
    for block in split_blocks(content):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines:
            bullets = extract_bullets(block)
            projects.append(
                {
                    "name": lines[0],
                    "date": "",
                    "technologies": "",
                    "description": " ".join(lines[1:]),
                    "bullets": bullets or metadata_to_bullets(lines[1:]),
                }
            )
    return projects


def extract_education_entries(sections: Dict[str, str]) -> List[Dict[str, str]]:
    entries = extract_dated_entries(sections.get("education", ""), section_type="education")
    return [
        {
            "institution": str(entry.get("institution", "")),
            "dates": str(entry.get("dates", "")),
            "degree": str(entry.get("degree", "")),
            "details": str(entry.get("details", "")),
        }
        for entry in entries
    ]


def extract_list_section(sections: Dict[str, str], name: str) -> List[str]:
    content = sections.get(name, "")
    items = []
    for line in content.splitlines():
        cleaned = line.strip(" •-–—\t")
        if cleaned:
            items.append(cleaned)
    return items


def extract_bullets(text: str) -> List[str]:
    bullets = [item["text"] for item in normalize_section_lines(text) if item["kind"] == "bullet"]
    if bullets:
        return bullets
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(sentence.split()) >= 6
    ]


def normalize_section_lines(content: str) -> List[Dict[str, str]]:
    lines: List[Dict[str, str]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        is_bullet = bool(BULLET_PREFIX_PATTERN.match(line))
        cleaned = BULLET_PREFIX_PATTERN.sub("", line).strip()
        if not cleaned:
            continue

        if is_bullet:
            lines.append({"kind": "bullet", "text": cleaned})
            continue

        if (
            lines
            and lines[-1]["kind"] == "bullet"
            and (not re.search(r"[.!?)]$", lines[-1]["text"]) or cleaned[:1].islower())
        ):
            lines[-1]["text"] = f"{lines[-1]['text']} {cleaned}"
            continue

        lines.append({"kind": "meta", "text": cleaned})
    return lines


def extract_dated_entries(content: str, section_type: str) -> List[Dict[str, object]]:
    lines = normalize_section_lines(content)
    date_indexes = [
        index
        for index, item in enumerate(lines)
        if item["kind"] == "meta" and is_date_line(item["text"])
    ]
    if not date_indexes:
        return []

    anchors = []
    for date_index in date_indexes:
        date_line = lines[date_index]["text"]
        inline_heading = DATE_RANGE_PATTERN.sub("", date_line)
        inline_heading = DATE_POINT_PATTERN.sub("", inline_heading).strip(" |,-–—")
        heading_index = date_index
        heading = inline_heading
        if not heading:
            heading_index = previous_meta_index(lines, date_index - 1)
            heading = lines[heading_index]["text"] if heading_index >= 0 else ""
        anchors.append(
            {
                "date_index": date_index,
                "heading_index": heading_index,
                "heading": heading,
                "dates": infer_dates(date_line) or date_line,
            }
        )

    entries: List[Dict[str, object]] = []
    for index, anchor in enumerate(anchors):
        segment_end = anchors[index + 1]["heading_index"] if index + 1 < len(anchors) else len(lines)
        body = lines[anchor["date_index"] + 1:segment_end]
        metadata = [item["text"] for item in body if item["kind"] == "meta"]
        bullets = [item["text"] for item in body if item["kind"] == "bullet"]
        heading = str(anchor["heading"])
        dates = str(anchor["dates"])

        if section_type == "experience":
            if not bullets:
                bullets = metadata_to_bullets(metadata[1:])
            entries.append(
                {
                    "title": metadata[0] if metadata else heading,
                    "company": heading if metadata else "",
                    "dates": dates,
                    "bullets": bullets,
                }
            )
        elif section_type == "project":
            if not bullets:
                bullets = metadata_to_bullets(metadata[1:])
            entries.append(
                {
                    "name": heading,
                    "date": dates,
                    "technologies": metadata[0] if metadata else "",
                    "description": " ".join(metadata[1:]),
                    "bullets": bullets,
                }
            )
        elif section_type == "education":
            entries.append(
                {
                    "institution": heading,
                    "dates": dates,
                    "degree": metadata[0] if metadata else "",
                    "details": " | ".join(metadata[1:]),
                }
            )

    return [entry for entry in entries if any(entry.values())]


def extract_undated_project_entries(content: str) -> List[Dict[str, object]]:
    lines = normalize_section_lines(content)
    starts: List[int] = []
    for index, item in enumerate(lines):
        if item["kind"] != "meta" or not looks_like_project_heading(item["text"]):
            continue
        next_item = lines[index + 1] if index + 1 < len(lines) else None
        following_items = lines[index + 1:index + 4]
        has_nearby_bullet = any(candidate["kind"] == "bullet" for candidate in following_items)
        has_technology_line = bool(
            next_item
            and next_item["kind"] == "meta"
            and looks_like_technology_line(next_item["text"])
        )
        if has_nearby_bullet or has_technology_line:
            starts.append(index)

    if not starts:
        return []

    starts.append(len(lines))
    projects: List[Dict[str, object]] = []
    for offset in range(len(starts) - 1):
        start = starts[offset]
        end = starts[offset + 1]
        segment = lines[start:end]
        if not segment:
            continue
        metadata = [item["text"] for item in segment[1:] if item["kind"] == "meta"]
        bullets = [item["text"] for item in segment[1:] if item["kind"] == "bullet"]
        technologies = metadata[0] if metadata and looks_like_technology_line(metadata[0]) else ""
        description_items = metadata[1:] if technologies else metadata
        projects.append(
            {
                "name": segment[0]["text"],
                "date": "",
                "technologies": technologies,
                "description": " ".join(description_items),
                "bullets": bullets or metadata_to_bullets(description_items),
            }
        )

    return [project for project in projects if project["name"]]


def looks_like_project_heading(text: str) -> bool:
    cleaned = text.strip()
    words = cleaned.split()
    if not 2 <= len(words) <= 9:
        return False
    if looks_like_technology_line(cleaned) or is_date_line(cleaned):
        return False
    if cleaned.endswith((".", ";", ":")):
        return False
    alpha_ratio = sum(char.isalpha() or char.isspace() or char in "-'/" for char in cleaned) / max(len(cleaned), 1)
    return alpha_ratio > 0.62


def looks_like_technology_line(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if "," in cleaned or "|" in cleaned:
        return True
    lower = cleaned.lower()
    tech_terms = (
        "python", "java", "javascript", "typescript", "react", "fastapi", "flask",
        "rasa", "faiss", "langchain", "docker", "kubernetes", "aws", "sql",
        "mongodb", "mysql", "pandas", "numpy", "tensorflow", "pytorch",
    )
    return sum(1 for term in tech_terms if term in lower) >= 2


def metadata_to_bullets(items: List[str]) -> List[str]:
    bullets = []
    for item in items:
        cleaned = " ".join(str(item).strip(" •-–—\t").split())
        if len(cleaned.split()) < 6:
            continue
        first_word = re.match(r"[A-Za-z]+", cleaned)
        if first_word and first_word.group(0).lower() in ACTION_VERBS:
            bullets.append(cleaned)
        elif cleaned.endswith((".", "!", "?")):
            bullets.append(cleaned)
    return bullets


def previous_meta_index(lines: List[Dict[str, str]], start: int) -> int:
    for index in range(start, -1, -1):
        if lines[index]["kind"] == "meta":
            return index
    return -1


def is_date_line(text: str) -> bool:
    return bool(DATE_ONLY_PATTERN.match(text.strip()))


def split_blocks(content: str) -> List[str]:
    if not content.strip():
        return []
    blocks = re.split(r"\n\s*\n", content.strip())
    if len(blocks) > 1:
        return [block.strip() for block in blocks if block.strip()]
    lines = content.splitlines()
    starts: List[int] = []
    for index, line in enumerate(lines):
        if infer_dates(line) or re.search(
            r"\b(engineer|developer|intern|manager|analyst|consultant|specialist|technician)\b",
            line,
            re.I,
        ):
            starts.append(index)
    if len(starts) <= 1:
        return [content.strip()]
    starts.append(len(lines))
    return [
        "\n".join(lines[starts[i]:starts[i + 1]]).strip()
        for i in range(len(starts) - 1)
    ]


def infer_dates(text: str) -> str:
    match = DATE_RANGE_PATTERN.search(text)
    if match:
        return match.group(0)
    point_match = DATE_POINT_PATTERN.search(text)
    return point_match.group(0) if point_match else ""


def infer_company(lines: List[str]) -> str:
    for line in lines[1:3]:
        if not infer_dates(line) and len(line.split()) <= 8:
            return line
    return ""


def count_action_verbs(text: str) -> int:
    return sum(
        1
        for word in re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if word in ACTION_VERBS
    )


def quantified_bullets(bullets: List[str]) -> Tuple[int, int]:
    quantified = [
        bullet
        for bullet in bullets
        if re.search(r"\d+|%|\$|x\b", bullet, re.IGNORECASE)
    ]
    return len(quantified), len(bullets)
