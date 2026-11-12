import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

import fitz

from app.data.skills import SKILL_ALIASES, TECH_SKILLS


SECTION_ALIASES = {
    "summary": [
        "summary", "professional summary", "career summary", "executive summary",
        "profile", "professional profile", "career profile", "objective", "career objective",
        "about", "about me",
    ],
    "skills": [
        "skills", "technical skills", "core skills", "key skills", "professional skills",
        "areas of expertise", "core competencies", "competencies", "technologies", "tools",
        "technical toolkit", "technology stack", "tech stack",
    ],
    "experience": [
        "experience", "work experience", "professional experience", "relevant experience",
        "employment", "employment history", "work history", "career history",
        "professional background", "internship", "internships",
    ],
    "education": [
        "education", "academic background", "academic qualifications", "education and training",
        "educational qualifications", "qualifications",
    ],
    "projects": [
        "projects", "personal projects", "key projects", "selected projects", "featured projects",
        "academic projects", "project experience", "project work",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "licenses and certifications",
        "training and certifications", "courses and certifications", "professional development",
    ],
}

ACTION_VERBS = {
    "achieved", "architected", "automated", "built", "created", "delivered",
    "designed", "developed", "drove", "enhanced", "executed", "implemented",
    "identified", "improved", "increased", "integrated", "launched", "led",
    "managed", "optimized", "participated", "performed", "reduced", "scaled",
    "shipped", "streamlined", "supported", "validated", "contributed",
    "collaborated", "completed", "converted", "engineered", "orchestrated",
    "deployed", "trained", "recorded", "benchmarked", "modeled", "modelled",
    "instrumented", "evaluated", "analyzed", "analysed", "resolved", "maintained",
}

BULLET_PREFIX_PATTERN = re.compile(
    r"^(?:[•●▪◦■◆*]|[-–—]+|â€¢|â—|â–ª|â—¦|Ã¢â‚¬Â¢)\s*"
)

MONTH_PATTERN = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
DATE_TOKEN_PATTERN = rf"(?:{MONTH_PATTERN}\s+(?:19|20)\d{{2}}|(?:0?[1-9]|1[0-2])[/-](?:19|20)\d{{2}}|(?:19|20)\d{{2}})"

DATE_RANGE_PATTERN = re.compile(
    rf"{DATE_TOKEN_PATTERN}\s*(?:-|–|—|to|until)\s*"
    rf"(?:Present|Current|Now|Ongoing|{DATE_TOKEN_PATTERN})",
    re.IGNORECASE,
)
DATE_POINT_PATTERN = re.compile(
    DATE_TOKEN_PATTERN,
    re.IGNORECASE,
)
DATE_ONLY_PATTERN = re.compile(
    rf"^\s*(?:{DATE_RANGE_PATTERN.pattern}|{DATE_POINT_PATTERN.pattern})\s*$",
    re.IGNORECASE,
)

JOB_TITLE_PATTERN = re.compile(
    r"\b(?:engineer|developer|architect|intern|manager|analyst|consultant|specialist|"
    r"technician|administrator|designer|scientist|lead|director|officer|associate|"
    r"coordinator|executive|representative|recruiter|accountant|researcher|teacher|"
    r"professor|nurse|doctor|supervisor|head|founder|owner)\b",
    re.IGNORECASE,
)

DEGREE_PATTERN = re.compile(
    r"\b(?:b\.?tech|m\.?tech|bachelor|master|ph\.?d|diploma|degree|university|college|"
    r"school|b\.?e\.?|m\.?e\.?|b\.?sc|m\.?sc|mba|bca|mca)\b",
    re.IGNORECASE,
)

ACADEMIC_CREDENTIAL_PATTERN = re.compile(
    r"\b(?:b\.?tech|m\.?tech|bachelor|master|ph\.?d|diploma|degree|"
    r"b\.?e\.?|m\.?e\.?|b\.?sc|m\.?sc|mba|bca|mca)\b",
    re.IGNORECASE,
)

MOJIBAKE_REPLACEMENTS = {
    "â€¢": "•", "â—": "●", "â–ª": "▪", "â—¦": "◦",
    "â€“": "–", "â€”": "—", "Â·": "·", "Ã¢â‚¬Â¢": "•",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    text_parts: List[str] = []
    try:
        with fitz.open(path) as document:
            if document.page_count == 0:
                raise ValueError("The PDF has no pages")
            for page in document:
                # Coordinate sorting is more reliable for resumes exported by
                # Word, Google Docs, Canva, and other layout tools.
                text_parts.append(page.get_text("text", sort=True))
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
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "-")
    for broken, replacement in MOJIBAKE_REPLACEMENTS.items():
        text = text.replace(broken, replacement)
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_data(text: str) -> Dict:
    text = normalize_text(text)
    sections = detect_sections(text)
    skill_groups = extract_skill_groups(sections.get("skills", ""))

    resume_data = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": extract_location(sections.get("header", "")),
        "links": extract_links_from_text(text),
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
    resume_data["document_stats"] = {
        "characters": len(text),
        "words": len(text.split()),
        "lines": len([line for line in text.splitlines() if line.strip()]),
    }
    resume_data["extraction_quality"] = assess_extraction_quality(resume_data)
    return resume_data


def detect_sections(text: str) -> Dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header_lookup = {
        alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
    }
    aliases = sorted(header_lookup, key=len, reverse=True)
    header_pattern = re.compile(
        r"^(?:\d+[.)]\s*)?(" + "|".join(re.escape(alias) for alias in aliases) +
        r")(?:\s*[:|\-–—]\s*(.*))?$",
        re.IGNORECASE,
    )

    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        candidate = re.sub(r"^[\s|•●▪◦*\-–—]+|[\s|•●▪◦*\-–—]+$", "", line).strip()
        match = header_pattern.match(candidate)
        if match:
            if current == "skills" and header_lookup[match.group(1).lower()] == "skills" and match.group(2):
                sections[current].append(line)
                continue
            current = header_lookup[match.group(1).lower()]
            sections.setdefault(current, [])
            inline_content = (match.group(2) or "").strip()
            if inline_content:
                sections[current].append(inline_content)
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(content).strip() for name, content in sections.items()}


def extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    header_text = "\n".join(text.splitlines()[:18])
    candidates = re.finditer(
        r"(?<![\w/])(?:\+?\d{1,3}[\s().-]*)?(?:\(?\d{2,5}\)?[\s().-]*){2,4}\d{2,5}(?![\w/])",
        header_text,
    )
    for match in candidates:
        candidate = match.group(0).strip(" .-|,")
        digits = re.sub(r"\D", "", candidate)
        if not 8 <= len(digits) <= 15:
            continue
        if DATE_RANGE_PATTERN.fullmatch(candidate) or re.fullmatch(
            r"(?:19|20)\d{2}\s*[-–—]\s*(?:19|20)\d{2}", candidate
        ):
            continue
        return candidate
    return ""


def extract_name(text: str) -> str:
    contact_pattern = re.compile(
        r"@|github|linkedin|http|www|phone|email|\+?\d[\d\s().-]{6,}", re.IGNORECASE
    )
    section_names = {alias for aliases in SECTION_ALIASES.values() for alias in aliases}
    candidates: List[Tuple[int, str]] = []
    for index, line in enumerate(text.splitlines()[:15]):
        cleaned = line.strip(" -|•\t")
        words = cleaned.split()
        if not cleaned or contact_pattern.search(cleaned):
            continue
        if (
            cleaned.casefold().rstrip(":") in section_names
            or JOB_TITLE_PATTERN.search(cleaned)
            or DEGREE_PATTERN.search(cleaned)
        ):
            continue
        if 1 <= len(words) <= 5 and len(cleaned) <= 60:
            alpha_ratio = sum(ch.isalpha() or ch.isspace() for ch in cleaned) / max(len(cleaned), 1)
            if alpha_ratio < 0.82:
                continue
            title_case_words = sum(word[:1].isupper() for word in words)
            score = max(0, 12 - index) + title_case_words * 2
            if cleaned.isupper():
                score += 2
            candidates.append((score, cleaned.title() if cleaned.isupper() else cleaned))
    return max(candidates, default=(0, ""), key=lambda item: item[0])[1]


def extract_location(header: str) -> str:
    location_words = re.compile(
        r"\b(?:remote|india|usa|united states|uk|united kingdom|canada|australia|"
        r"delhi|mumbai|bengaluru|bangalore|hyderabad|pune|chennai|kolkata|gurugram|"
        r"noida|new york|san francisco|london|toronto|sydney)\b",
        re.IGNORECASE,
    )
    for line in header.splitlines()[:12]:
        for segment in re.split(r"[|•]", line):
            cleaned = segment.strip(" |,•-")
            if location_words.search(cleaned) and "@" not in cleaned and len(cleaned) <= 80:
                return cleaned
    return ""


def extract_links_from_text(text: str) -> Dict[str, str]:
    links: Dict[str, str] = {}
    url_pattern = re.compile(
        r"(?:https?://|www\.|(?:linkedin|github)\.com/)[^\s|<>()]+", re.IGNORECASE
    )
    for raw_url in url_pattern.findall(text):
        url = raw_url.rstrip(".,;:)]}")
        normalized = url if url.lower().startswith(("http://", "https://")) else f"https://{url}"
        lower_url = normalized.lower()
        if "linkedin.com" in lower_url:
            links.setdefault("linkedin", normalized)
        elif "github.com" in lower_url:
            links.setdefault("github", normalized)
        else:
            links.setdefault("portfolio", normalized)
    return links


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
    for token in re.split(r"[,|;•●▪◦·\n]", values):
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
            and (
                cleaned[:1].islower()
                or cleaned.startswith(("and ", "or ", "with ", "using ", "across ", "for "))
                or (
                    not lines[-1]["text"].endswith((".", "!", "?"))
                    and not infer_dates(cleaned)
                    and not looks_like_project_heading(cleaned)
                )
            )
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
        if item["kind"] == "meta" and infer_dates(item["text"])
    ]
    if not date_indexes:
        return []

    anchors = []
    for date_index in date_indexes:
        date_line = lines[date_index]["text"]
        dates = infer_dates(date_line)
        inline_heading = DATE_RANGE_PATTERN.sub("", date_line, count=1)
        inline_heading = DATE_POINT_PATTERN.sub("", inline_heading, count=1).strip(" |,-–—()")

        prefix_indexes: List[int] = []
        cursor = date_index - 1
        while cursor >= 0 and len(prefix_indexes) < 3:
            if lines[cursor]["kind"] != "meta" or infer_dates(lines[cursor]["text"]):
                break
            prefix_indexes.insert(0, cursor)
            cursor -= 1

        heading_index = date_index if inline_heading else (prefix_indexes[-1] if prefix_indexes else date_index)
        heading = inline_heading or (lines[heading_index]["text"] if heading_index != date_index else "")
        prefix_start = prefix_indexes[0] if prefix_indexes else heading_index
        anchors.append(
            {
                "date_index": date_index,
                "heading_index": heading_index,
                "prefix_indexes": prefix_indexes,
                "prefix_start": prefix_start,
                "heading": heading,
                "dates": dates or date_line,
            }
        )

    entries: List[Dict[str, object]] = []
    for index, anchor in enumerate(anchors):
        segment_end = anchors[index + 1]["prefix_start"] if index + 1 < len(anchors) else len(lines)
        prefix_metadata = [
            lines[prefix_index]["text"]
            for prefix_index in anchor["prefix_indexes"]
            if prefix_index != anchor["heading_index"]
        ]
        body = lines[anchor["date_index"] + 1:segment_end]
        metadata = prefix_metadata + [item["text"] for item in body if item["kind"] == "meta"]
        bullets = [item["text"] for item in body if item["kind"] == "bullet"]
        heading = str(anchor["heading"])
        dates = str(anchor["dates"])

        if section_type == "experience":
            if not bullets:
                bullets = metadata_to_bullets(metadata)
            company, title = infer_experience_fields(heading, metadata)
            location = next((item[len(title):].strip(" |,-") for item in metadata if item.startswith(title) and len(item) > len(title) and looks_like_location(item)), "")
            if not location:
                location = next((item for item in metadata if looks_like_location(item) and not JOB_TITLE_PATTERN.search(item)), "")
            entries.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
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
            institution, degree, details = infer_education_fields(heading, metadata)
            entries.append(
                {
                    "institution": institution,
                    "dates": dates,
                    "degree": degree,
                    "details": details,
                }
            )

    return [entry for entry in entries if any(entry.values())]


def infer_experience_fields(heading: str, metadata: List[str]) -> Tuple[str, str]:
    heading_parts = [
        part.strip()
        for part in re.split(r"\s+(?:at|@)\s+|\s+[|•·–—]\s+", heading, flags=re.IGNORECASE)
        if part.strip()
    ] or ([heading] if heading else [])
    metadata_candidates = [
        item for item in metadata
        if item and not infer_dates(item)
        and (JOB_TITLE_PATTERN.search(item) or not looks_like_location(item))
    ]

    # A role immediately after a company/date row is the most common layout.
    metadata_title = next((item for item in metadata_candidates[:3] if JOB_TITLE_PATTERN.search(item)), "")
    heading_title = next((part for part in heading_parts if JOB_TITLE_PATTERN.search(part)), "")
    title = metadata_title or heading_title

    company = ""
    if metadata_title and heading:
        company = next(
            (part for part in heading_parts if part.casefold() != metadata_title.casefold()),
            heading,
        )
    elif heading_title:
        company = next(
            (
                part for part in heading_parts
                if part.casefold() != heading_title.casefold() and looks_like_company(part)
            ),
            "",
        )
        if not company:
            company = next((item for item in metadata_candidates if item != title and looks_like_company(item)), "")
    else:
        company = heading
        title = metadata_candidates[0] if metadata_candidates else ""

    if not title:
        title = heading if heading and not company else (metadata_candidates[0] if metadata_candidates else "")
    if not company and heading and heading.casefold() != title.casefold():
        company = heading
    return company.strip(" |,-–—"), title.strip(" |,-–—")


def looks_like_location(text: str) -> bool:
    lower = text.casefold()
    location_markers = (
        "remote", "india", "usa", "united states", "united kingdom", "canada",
        "australia", "delhi", "mumbai", "bengaluru", "bangalore", "hyderabad",
        "pune", "chennai", "kolkata", "gurugram", "noida", "new york",
        "san francisco", "london", "toronto", "sydney",
    )
    return any(marker in lower for marker in location_markers) or bool(
        re.search(r"\b(?:city|state|province|country)\b", lower)
    )


def looks_like_company(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned or len(cleaned.split()) > 10:
        return False
    return not (
        infer_dates(cleaned)
        or DEGREE_PATTERN.search(cleaned)
        or looks_like_location(cleaned)
        or looks_like_technology_line(cleaned)
    )


def infer_education_fields(heading: str, metadata: List[str]) -> Tuple[str, str, str]:
    heading_parts = [
        part.strip()
        for part in re.split(r"\s+[|•·–—]\s+", heading)
        if part.strip()
    ] or ([heading] if heading else [])
    candidates = heading_parts + [item for item in metadata if item]
    degree = next((item for item in candidates if ACADEMIC_CREDENTIAL_PATTERN.search(item)), "")
    institution = next(
        (
            item for item in heading_parts
            if item.casefold() != degree.casefold() and not looks_like_location(item)
        ),
        heading_parts[0] if heading_parts else "",
    )
    detail_items = [
        item for item in candidates
        if item.casefold() not in {institution.casefold(), degree.casefold()}
        and not infer_dates(item)
    ]
    return institution, degree, " | ".join(dict.fromkeys(detail_items))


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
    if not 1 <= len(words) <= 16:
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
    if "," in cleaned:
        parts = [part.strip() for part in re.split(r"[,|]", cleaned) if part.strip()]
        return len(parts) > 1 and all(len(part.split()) <= 4 for part in parts)
    if "|" in cleaned:
        parts = [part.strip().lower() for part in cleaned.split("|") if part.strip()]
        known = {skill.lower() for skill in TECH_SKILLS}
        return len(parts) > 1 and all(part in known for part in parts)
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


def assess_extraction_quality(resume_data: Dict) -> Dict[str, object]:
    experience = resume_data.get("experience") or []
    projects = resume_data.get("projects") or []
    education = resume_data.get("education_entries") or resume_data.get("education") or []
    sections = resume_data.get("sections") or {}
    bullet_count = sum(len(item.get("bullets") or []) for item in [*experience, *projects])
    detected_sections = [
        name for name, content in sections.items()
        if name != "header" and str(content).strip()
    ]

    checks = [
        (bool(resume_data.get("name")), 10),
        (bool(resume_data.get("email")), 10),
        (bool(resume_data.get("phone")), 5),
        (bool(resume_data.get("summary")), 10),
        (bool(resume_data.get("skills")), 15),
        (bool(experience), 20),
        (bool(education), 10),
        (bool(projects), 5),
        (bullet_count > 0, 10),
        (len(detected_sections) >= 4, 5),
    ]
    score = sum(weight for passed, weight in checks if passed)
    warnings: List[str] = []
    if not resume_data.get("name"):
        warnings.append("Candidate name was not confidently detected.")
    if not resume_data.get("email"):
        warnings.append("No email address was detected in the resume header.")
    if not resume_data.get("phone"):
        warnings.append("No phone number was detected in the resume header.")
    if not resume_data.get("skills"):
        warnings.append("No skills section or recognizable skill terms were found.")
    if not experience:
        warnings.append("Work experience entries could not be separated reliably.")
    if not education:
        warnings.append("Education details could not be separated reliably.")
    if experience and bullet_count == 0:
        warnings.append("Experience was found, but accomplishment bullets were not detected.")

    label = "High confidence" if score >= 85 else "Review suggested" if score >= 60 else "Low confidence"
    return {
        "score": score,
        "label": label,
        "warnings": warnings,
        "detected_sections": detected_sections,
        "counts": {
            "experience": len(experience),
            "projects": len(projects),
            "education": len(education),
            "skills": len(resume_data.get("skills") or []),
            "bullets": bullet_count,
        },
    }


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
