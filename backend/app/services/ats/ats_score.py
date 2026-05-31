import math
import re
from collections import Counter
from typing import Dict, List

from app.data.skills import SKILL_ALIASES, TECH_SKILLS
from app.services.parser.resume_parser import (
    count_action_verbs,
    extract_resume_data,
    quantified_bullets,
)


def extract_keywords(text: str) -> List[str]:
    lower_text = text.lower()
    found = []
    for skill in TECH_SKILLS:
        terms = [skill, *SKILL_ALIASES.get(skill, [])]
        if any(term_in_text(term, lower_text) for term in terms):
            found.append(skill)
    return sorted(set(found))


def term_in_text(term: str, lower_text: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return bool(re.search(pattern, lower_text))


def extract_jd_terms(text: str) -> List[str]:
    skill_terms = extract_keywords(text)
    words = [
        word for word in re.findall(r"\b[a-zA-Z][a-zA-Z+#./-]{2,}\b", text.lower())
        if word not in STOPWORDS
    ]
    common_terms = [word for word, _ in Counter(words).most_common(25)]
    return sorted(set(skill_terms + common_terms[:12]))


def calculate_ats_score(resume_text: str, jd_text: str) -> Dict:
    structured = extract_resume_data(resume_text)
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    jd_terms = extract_jd_terms(jd_text)

    matched_keywords = sorted(set(resume_keywords).intersection(jd_keywords))
    missing_keywords = sorted(set(jd_keywords).difference(resume_keywords))
    matched_terms = sorted(term for term in jd_terms if term in resume_text.lower())
    missing_terms = sorted(term for term in jd_terms if term not in resume_text.lower())

    skill_score = ratio_score(len(matched_keywords), len(jd_keywords), empty_score=50)
    keyword_score = ratio_score(len(matched_terms), len(jd_terms), empty_score=50)
    section_score, section_weaknesses = score_sections(structured)
    length_score = score_length(resume_text)
    action_score = score_action_verbs(resume_text)
    impact_score = score_quantified_impact(structured)

    weighted = (
        skill_score * 0.32
        + keyword_score * 0.20
        + section_score * 0.18
        + length_score * 0.10
        + action_score * 0.10
        + impact_score * 0.10
    )
    score = int(max(0, min(100, round(weighted))))

    strengths = build_strengths(
        matched_keywords, section_score, length_score, action_score, impact_score
    )
    weaknesses = build_weaknesses(
        missing_keywords, section_weaknesses, length_score, action_score, impact_score
    )

    return {
        "score": score,
        "ats_score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_keywords": missing_keywords,
        "missing_terms": missing_terms[:15],
        "matched_keywords": matched_keywords,
        "resume_skills": resume_keywords,
        "jd_skills": jd_keywords,
        "section_scores": {
            "skills_match": skill_score,
            "keyword_density": keyword_score,
            "section_completeness": section_score,
            "resume_length": length_score,
            "action_verbs": action_score,
            "quantified_impact": impact_score,
        },
        "recommendations": build_recommendations(missing_keywords, section_weaknesses, action_score, impact_score),
    }


def ratio_score(numerator: int, denominator: int, empty_score: int = 0) -> int:
    if denominator == 0:
        return empty_score
    return int(round((numerator / denominator) * 100))


def score_sections(structured: Dict) -> tuple[int, List[str]]:
    required = ["name", "email", "phone", "summary", "skills", "experience", "education"]
    present = []
    weaknesses = []
    for key in required:
        value = structured.get(key)
        has_value = bool(value) and value != []
        present.append(has_value)
        if not has_value:
            weaknesses.append(f"Missing or weak {key} section")
    return int(round(sum(present) / len(required) * 100)), weaknesses


def score_length(text: str) -> int:
    words = len(text.split())
    if 350 <= words <= 900:
        return 100
    if 250 <= words < 350 or 900 < words <= 1100:
        return 75
    if 150 <= words < 250 or 1100 < words <= 1400:
        return 50
    return 25


def score_action_verbs(text: str) -> int:
    words = max(len(text.split()), 1)
    density = count_action_verbs(text) / words
    return int(min(100, round(density * 1500)))


def score_quantified_impact(structured: Dict) -> int:
    bullets = []
    for item in structured.get("experience", []):
        bullets.extend(item.get("bullets", []))
    for item in structured.get("projects", []):
        bullets.extend(item.get("bullets", []))
    quantified, total = quantified_bullets(bullets)
    return ratio_score(quantified, total, empty_score=35)


def build_strengths(matched: List[str], section_score: int, length_score: int, action_score: int, impact_score: int) -> List[str]:
    strengths = []
    if matched:
        strengths.append(f"Matches important JD skills: {', '.join(matched[:8])}")
    if section_score >= 85:
        strengths.append("Core resume sections are present and readable")
    if length_score >= 75:
        strengths.append("Resume length is within a practical ATS range")
    if action_score >= 60:
        strengths.append("Uses action-oriented language")
    if impact_score >= 60:
        strengths.append("Includes quantified business or technical impact")
    return strengths or ["Resume has enough content to begin optimization"]


def build_weaknesses(missing: List[str], section_weaknesses: List[str], length_score: int, action_score: int, impact_score: int) -> List[str]:
    weaknesses = []
    if missing:
        weaknesses.append(f"Missing JD skills: {', '.join(missing[:8])}")
    weaknesses.extend(section_weaknesses[:5])
    if length_score < 75:
        weaknesses.append("Resume length may be too short or too long for recruiter scanning")
    if action_score < 55:
        weaknesses.append("Too few bullets begin with strong action verbs")
    if impact_score < 55:
        weaknesses.append("Not enough measurable outcomes or quantified impact")
    return weaknesses


def build_recommendations(missing: List[str], section_weaknesses: List[str], action_score: int, impact_score: int) -> List[str]:
    recommendations = []
    for skill in missing[:8]:
        recommendations.append(f"Add '{skill}' only where it reflects real experience, projects, or coursework.")
    if section_weaknesses:
        recommendations.append("Complete missing core sections with plain ATS-readable headings.")
    if action_score < 55:
        recommendations.append("Rewrite weak bullets to start with verbs like Built, Designed, Automated, Improved, or Optimized.")
    if impact_score < 55:
        recommendations.append("Add metrics such as latency reduction, cost savings, accuracy, throughput, users, or deployment scale.")
    return recommendations


STOPWORDS = {
    "and", "are", "for", "the", "with", "you", "our", "will", "this", "that",
    "from", "have", "has", "using", "use", "job", "role", "team", "work",
    "experience", "looking", "engineer", "developer", "systems", "strong",
    "ability", "skills", "knowledge", "requirements", "responsibilities",
}
