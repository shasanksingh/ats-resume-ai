import re
from copy import deepcopy
from typing import Dict, List

from app.data.skills import SKILL_ALIASES
from app.services.ats.ats_score import calculate_ats_score, extract_keywords, term_in_text
from app.services.llm.llm_router import generate_resume_optimization
from app.services.parser.resume_parser import ACTION_VERBS, extract_resume_data


ACTION_VERB_FALLBACKS = ["Built", "Designed", "Implemented", "Optimized", "Automated"]
ACTION_OPENERS = (
    "Achieved", "Architected", "Automated", "Built", "Created", "Delivered",
    "Designed", "Developed", "Drove", "Enhanced", "Executed", "Implemented",
    "Identified", "Improved", "Increased", "Integrated", "Launched", "Led",
    "Managed", "Optimized", "Participated", "Reduced", "Scaled", "Streamlined",
    "Collaborated", "Converted", "Contributed", "Supported", "Validated", "Worked",
)

GROUP_RULES = [
    (
        {
            "javascript", "typescript", "python", "java", "sql", "html", "css",
            "c", "c++", "c#", "go", "rust", "php", "ruby", "bash",
        },
        ["Languages", "Programming Languages", "Technical Skills", "Skills"],
    ),
    (
        {
            "cypress", "playwright", "selenium", "automation testing",
            "ui automation", "functional testing", "regression testing",
            "end-to-end testing", "smoke testing", "performance testing",
            "jmeter", "pytest", "junit", "testng", "mobile testing",
        },
        ["Automation Testing", "Testing", "QA Tools", "Tools", "Skills"],
    ),
    (
        {
            "api testing", "rest api", "postman", "api validation", "swagger",
            "api integration", "graphql",
        },
        ["API Testing", "Automation Testing", "Tools", "Skills"],
    ),
    (
        {
            "quality assurance", "manual testing", "test planning",
            "test case design", "test execution", "defect tracking",
            "bug reporting", "agile", "scrum", "stlc", "sdlc", "uat",
            "release validation",
        },
        ["QA Concepts", "Testing", "Core Skills", "Skills"],
    ),
    (
        {
            "jira", "git", "github", "mysql", "mongodb", "docker", "jenkins",
            "github actions", "wireshark", "cisco", "excel", "power bi",
            "tableau", "figma", "autocad", "solidworks", "revit",
        },
        ["Tools", "Technical Skills", "Additional Skills", "Skills"],
    ),
    (
        {
            "ci/cd", "linux", "windows", "nlp", "rag", "communication",
            "documentation", "reporting", "problem solving",
        },
        ["Additional Skills", "Tools", "Technical Skills", "Skills"],
    ),
]


def optimize_resume(
    resume_text: str,
    jd_text: str,
    rag_context: str,
    include_local_model: bool = True,
    structured_resume: Dict | None = None,
    confirmed_keywords: List[str] | None = None,
) -> Dict:
    structured = deepcopy(structured_resume or extract_resume_data(resume_text))
    baseline_ats = calculate_ats_score(resume_text, jd_text)
    structured, keyword_decisions = enrich_supported_keywords(
        structured,
        resume_text,
        baseline_ats,
        confirmed_keywords or [],
    )
    remaining_missing = [
        skill
        for skill in baseline_ats["missing_keywords"]
        if skill.casefold() not in {item.casefold() for item in confirmed_keywords or []}
    ]

    weak_bullets = find_weak_bullets(structured)
    rewritten = [rewrite_bullet(bullet, remaining_missing) for bullet in weak_bullets]
    rewritten.sort(key=lambda item: item["original"].rstrip(".") == item["improved"].rstrip("."))
    rewritten = rewritten[:8]
    improved_summary = improve_summary(
        structured.get("summary", ""),
        baseline_ats["matched_keywords"],
    )
    optimization = {
        "improved_summary": improved_summary,
        "improved_bullets": rewritten,
        "keyword_suggestions": remaining_missing[:12],
        "keyword_decisions": keyword_decisions,
        "rag_guidance": unique_guidance(rag_context)[:8],
        "local_model_hint": {},
        "warnings": [
            "Evidence-backed keywords found elsewhere in the resume are promoted into the skills section automatically.",
            "Missing skills are exported only after the candidate explicitly confirms they have that skill.",
            "Employers, degrees, metrics, and tools are never invented.",
        ],
    }
    projected_text = project_selected_text(resume_text, structured, optimization, confirmed_keywords or [])
    projected_ats = calculate_ats_score(projected_text, jd_text)

    llm_hint = (
        generate_optional_llm_hint(resume_text, jd_text, rag_context, remaining_missing)
        if include_local_model
        else {
            "success": False,
            "provider": "local-model",
            "text": "Local model hint skipped during document rebuild.",
        }
    )
    optimization["local_model_hint"] = llm_hint

    return {
        "structured_resume": structured,
        "baseline_ats": baseline_ats,
        "ats": projected_ats,
        "optimization": optimization,
    }


def enrich_supported_keywords(
    structured: Dict,
    resume_text: str,
    ats: Dict,
    confirmed_keywords: List[str],
) -> tuple[Dict, List[Dict]]:
    groups = deepcopy(structured.get("skill_groups") or {})
    listed_values = [
        str(value)
        for values in groups.values()
        for value in values
    ] or [str(value) for value in structured.get("skills", [])]
    listed_keywords = set(extract_keywords(" ".join(listed_values)))
    promoted = [
        keyword
        for keyword in ats["matched_keywords"]
        if keyword not in listed_keywords
    ][:10]

    missing_lookup = {keyword.casefold(): keyword for keyword in ats["missing_keywords"]}
    confirmed = []
    for keyword in confirmed_keywords:
        canonical = missing_lookup.get(keyword.casefold())
        if canonical and canonical not in confirmed:
            confirmed.append(canonical)

    groups = add_keywords_to_existing_groups(groups, promoted + confirmed)

    structured["skill_groups"] = groups
    structured["skills"] = merge_skills(
        structured.get("skills", []),
        [display_skill(keyword) for keyword in promoted + confirmed],
    )

    decisions = []
    for keyword in promoted:
        decisions.append({
            "keyword": display_skill(keyword),
            "status": "added_from_evidence",
            "reason": "Added to the export because the resume already contains supporting evidence outside the skills section.",
            "evidence": find_keyword_evidence(resume_text, keyword),
        })
    for keyword in confirmed:
        decisions.append({
            "keyword": display_skill(keyword),
            "status": "added_after_confirmation",
            "reason": "Added to the export after the candidate confirmed this skill.",
            "evidence": "Candidate confirmation",
        })
    for keyword in ats["missing_keywords"]:
        if keyword not in confirmed:
            decisions.append({
                "keyword": display_skill(keyword),
                "status": "recommendation_only",
                "reason": "Not added because no supporting evidence was found in the resume.",
                "evidence": "",
            })
    return structured, decisions


def add_keywords_to_existing_groups(groups: Dict[str, List[str]], keywords: List[str]) -> Dict[str, List[str]]:
    updated = deepcopy(groups)
    if not updated:
        updated["Skills"] = []
    for keyword in keywords:
        group_name = choose_group_for_keyword(keyword, updated)
        updated[group_name] = merge_skills(updated.get(group_name, []), [display_skill(keyword)])
    return updated


def choose_group_for_keyword(keyword: str, groups: Dict[str, List[str]]) -> str:
    normalized = keyword.casefold()
    group_lookup = {label.casefold(): label for label in groups}
    for skills, preferred_groups in GROUP_RULES:
        if normalized not in skills:
            continue
        for preferred in preferred_groups:
            exact = group_lookup.get(preferred.casefold())
            if exact:
                return exact
        for existing in groups:
            existing_normalized = existing.casefold()
            if any(part in existing_normalized for part in ("skill", "tool", "testing", "concept", "language")):
                return existing
    return next(iter(groups))


def merge_skills(current: List[str], additions: List[str]) -> List[str]:
    merged = []
    seen = set()
    for skill in [*current, *additions]:
        cleaned = str(skill).strip()
        if cleaned and cleaned.casefold() not in seen:
            merged.append(cleaned)
            seen.add(cleaned.casefold())
    return merged


def find_keyword_evidence(resume_text: str, keyword: str) -> str:
    terms = [keyword, *SKILL_ALIASES.get(keyword, [])]
    lines = [" ".join(line.split()) for line in resume_text.splitlines() if line.strip()]
    for line in lines:
        if any(term_in_text(term, line.lower()) for term in terms):
            return line[:220]
    return f"Detected in the uploaded resume as {display_skill(keyword)}."


def render_optimized_text(structured: Dict, optimized: Dict) -> str:
    rewrites = {
        item["original"]: item["improved"]
        for item in optimized.get("improved_bullets", [])
    }
    lines = [
        structured.get("name", ""),
        structured.get("email", ""),
        structured.get("phone", ""),
    ]
    summary = optimized.get("improved_summary") or structured.get("summary", "")
    if summary:
        lines.extend(["Professional Summary", summary])
    if structured.get("skill_groups") or structured.get("skills"):
        lines.append("Skills")
    for label, values in (structured.get("skill_groups") or {}).items():
        lines.append(f"{label}: {', '.join(values)}")
    if not structured.get("skill_groups"):
        lines.append(", ".join(structured.get("skills", [])))
    if structured.get("experience"):
        lines.append("Experience")
    for item in structured.get("experience", []):
        lines.extend([item.get("company", ""), item.get("title", ""), item.get("dates", "")])
        lines.extend(f"- {rewrites.get(bullet, bullet)}" for bullet in item.get("bullets", []))
    if structured.get("projects"):
        lines.append("Projects")
    for item in structured.get("projects", []):
        lines.extend([item.get("name", ""), item.get("technologies", ""), item.get("date", "")])
        lines.extend(f"- {rewrites.get(bullet, bullet)}" for bullet in item.get("bullets", []))
        if not item.get("bullets") and item.get("description"):
            lines.append(item["description"])
    if structured.get("education_entries") or structured.get("education"):
        lines.append("Education")
    for item in structured.get("education_entries", []):
        lines.extend(item.get(key, "") for key in ("institution", "degree", "details", "dates"))
    if not structured.get("education_entries"):
        lines.extend(structured.get("education", []))
    if structured.get("certifications"):
        lines.extend(["Certifications", *structured["certifications"]])
    return "\n".join(str(line) for line in lines if line)


def project_selected_text(resume_text: str, structured: Dict, optimized: Dict, confirmed: List[str] | None = None) -> str:
    """Score edits against source text so parsing cannot manufacture a gain."""
    result = resume_text
    changes = [(item["original"], item["improved"]) for item in optimized.get("improved_bullets", [])]
    if optimized.get("improved_summary") and structured.get("summary"):
        changes.append((structured["summary"], optimized["improved_summary"]))
    for original, improved in changes:
        pattern = r"\s+".join(re.escape(word) for word in original.split())
        if pattern:
            result = re.sub(pattern, lambda _: improved, result, count=1)
    additions = [skill for skill in (confirmed or []) if not term_in_text(skill, result.lower())]
    if additions:
        result += "\nConfirmed skills: " + ", ".join(additions)
    return result


def unique_guidance(rag_context: str) -> List[str]:
    guidance = []
    seen = set()
    chunks = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", rag_context)
    for chunk in chunks:
        cleaned = " ".join(chunk.split()).strip(" -•")
        key = cleaned.casefold()
        if len(cleaned) >= 24 and key not in seen:
            guidance.append(cleaned)
            seen.add(key)
    return guidance


def find_weak_bullets(structured: Dict) -> List[str]:
    bullets = []
    for item in structured.get("experience", []):
        bullets.extend(item.get("bullets", []))
    for item in structured.get("projects", []):
        bullets.extend(item.get("bullets", []))

    weak = []
    opener_pattern = r"^(" + "|".join(ACTION_VERBS) + r")\b"
    for bullet in bullets:
        starts_with_action = bool(re.match(opener_pattern, bullet, re.I))
        has_metric = bool(re.search(r"\d+|%|\$|x\b", bullet, re.I))
        if not starts_with_action or not has_metric:
            weak.append(bullet)
    return weak or bullets[:5]


def rewrite_bullet(bullet: str, missing_keywords: List[str]) -> Dict:
    del missing_keywords
    cleaned = bullet.strip(" •-–—\t.")
    improved = cleaned
    verbs = {"developing": "Developed", "building": "Built", "managing": "Managed", "implementing": "Implemented", "designing": "Designed", "maintaining": "Maintained", "testing": "Tested", "automating": "Automated", "analyzing": "Analyzed", "deploying": "Deployed"}
    for gerund, verb in verbs.items():
        improved = re.sub(r"^(?:responsible for|worked on)\s+" + gerund + r"\b", verb, improved, flags=re.I)
    for phrase, replacement in (("in order to", "to"), ("on a daily basis", "daily"), ("on a weekly basis", "weekly")):
        improved = re.sub(r"\b" + phrase + r"\b", replacement, improved, flags=re.I)
    improved += "." if bullet.endswith(".") else ""
    reason = ("Removes wordiness while retaining the original facts, tools, and metrics."
              if improved != bullet else "Already uses clear language; select for targeted AI refinement if needed.")
    if not re.search(r"\d+|%|\$|x\b", improved, re.I):
        reason += " Add a metric only when a truthful result is available."

    return {
        "original": bullet,
        "improved": improved,
        "reason": reason,
    }


def improve_summary(summary: str, matched_keywords: List[str]) -> str:
    base = summary.strip()
    if not base:
        return ""
    return re.sub(r"\bin order to\b", "to", base, flags=re.I)


def display_skill(skill: str) -> str:
    acronyms = {
        "api": "API",
        "api testing": "API Testing",
        "aws": "AWS",
        "ci/cd": "CI/CD",
        "css": "CSS",
        "gcp": "GCP",
        "html": "HTML",
        "llm": "LLM",
        "nlp": "NLP",
        "rag": "RAG",
        "rest api": "REST API",
        "sql": "SQL",
        "ui": "UI",
        "ux": "UX",
    }
    return acronyms.get(skill.lower(), skill.title())


def generate_optional_llm_hint(
    resume_text: str,
    jd_text: str,
    rag_context: str,
    missing_keywords: List[str],
) -> Dict:
    prompt = (
        "Rewrite resume guidance as concise recruiter notes. "
        "Do not invent experience, employers, metrics, degrees, or tools. "
        f"Missing truthful keywords to consider: {', '.join(missing_keywords[:8])}. "
        f"JD: {jd_text[:900]} "
        f"ATS rules: {rag_context[:700]} "
        f"Resume: {resume_text[:1200]}"
    )
    result = generate_resume_optimization(prompt)
    if not result["success"]:
        return {
            "success": False,
            "text": "Local model unavailable; deterministic optimizer results are still returned.",
            "error": result["text"],
        }
    return result
