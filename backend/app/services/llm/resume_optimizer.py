import re
from typing import Dict, List

from app.services.ats.ats_score import calculate_ats_score
from app.services.llm.llm_router import generate_resume_optimization
from app.services.parser.resume_parser import extract_resume_data


ACTION_VERB_FALLBACKS = ["Built", "Designed", "Implemented", "Optimized", "Automated"]


def optimize_resume(resume_text: str, jd_text: str, rag_context: str) -> Dict:
    structured = extract_resume_data(resume_text)
    ats = calculate_ats_score(resume_text, jd_text)

    weak_bullets = find_weak_bullets(structured)
    rewritten = [rewrite_bullet(bullet, ats["missing_keywords"]) for bullet in weak_bullets[:8]]
    improved_summary = improve_summary(structured.get("summary", ""), ats["matched_keywords"], ats["missing_keywords"])

    llm_hint = generate_optional_llm_hint(resume_text, jd_text, rag_context, ats["missing_keywords"])

    rag_guidance = []
    seen_guidance = set()
    for line in [line.strip() for line in rag_context.splitlines() if line.strip()]:
        if line not in seen_guidance:
            rag_guidance.append(line)
            seen_guidance.add(line)

    return {
        "structured_resume": structured,
        "ats": ats,
        "optimization": {
            "improved_summary": improved_summary,
            "improved_bullets": rewritten,
            "keyword_suggestions": ats["missing_keywords"][:12],
            "rag_guidance": rag_guidance[:6],
            "local_model_hint": llm_hint,
            "warnings": [
                "Suggestions preserve the candidate's existing experience and do not invent employers, degrees, metrics, or tools.",
                "Only add missing keywords when the resume already contains truthful supporting experience.",
            ],
        },
    }


def find_weak_bullets(structured: Dict) -> List[str]:
    bullets = []
    for item in structured.get("experience", []):
        bullets.extend(item.get("bullets", []))
    for item in structured.get("projects", []):
        bullets.extend(item.get("bullets", []))

    weak = []
    for bullet in bullets:
        starts_with_action = bool(re.match(r"^(Built|Designed|Implemented|Optimized|Automated|Developed|Led|Created|Improved|Reduced|Increased)\b", bullet, re.I))
        has_metric = bool(re.search(r"\d+|%|\$|x\b", bullet, re.I))
        if not starts_with_action or not has_metric:
            weak.append(bullet)
    return weak or bullets[:5]


def rewrite_bullet(bullet: str, missing_keywords: List[str]) -> Dict:
    cleaned = bullet.strip(" •-–\t.")
    verb = next((v for v in ACTION_VERB_FALLBACKS if not cleaned.lower().startswith(v.lower())), "Improved")
    keyword = next((skill for skill in missing_keywords if skill.lower() in cleaned.lower()), "")
    improved = cleaned
    if not re.match(r"^[A-Z][a-z]+ed\b|^Led\b|^Built\b", improved):
        improved = f"{verb} {improved[0].lower() + improved[1:] if improved else 'project deliverables'}"
    if keyword and keyword not in improved.lower():
        improved = f"{improved} using {keyword}"
    if not re.search(r"\d+|%|\$|x\b", improved, re.I):
        improved = f"{improved}; add a truthful metric for scale, latency, accuracy, cost, or users"
    return {
        "original": bullet,
        "improved": improved,
        "reason": "Strengthens action verb, ATS readability, and measurable impact without inventing facts.",
    }


def improve_summary(summary: str, matched_keywords: List[str], missing_keywords: List[str]) -> str:
    skills = matched_keywords[:5] or missing_keywords[:5]
    skill_phrase = ", ".join(skills)
    base = summary.strip()
    if not base:
        return f"Software engineer with hands-on experience in {skill_phrase}. Focused on building reliable, measurable, ATS-aligned systems."
    if skill_phrase and skill_phrase.lower() not in base.lower():
        return f"{base} Core strengths include {skill_phrase}."
    return base


def generate_optional_llm_hint(resume_text: str, jd_text: str, rag_context: str, missing_keywords: List[str]) -> Dict:
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
