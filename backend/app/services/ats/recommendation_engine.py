from app.services.ats.ats_score import calculate_ats_score
from app.services.rag.rag_engine import search_rag


def generate_recommendations(resume_text: str, jd_text: str):
    ats_result = calculate_ats_score(resume_text, jd_text)
    rag_results = search_rag(jd_text)

    recommendations = list(ats_result["recommendations"])
    for item in rag_results:
        if item not in recommendations:
            recommendations.append(item)

    return {
        "score": ats_result["score"],
        "ats_score": ats_result["ats_score"],
        "strengths": ats_result["strengths"],
        "weaknesses": ats_result["weaknesses"],
        "matched_keywords": ats_result["matched_keywords"],
        "missing_keywords": ats_result["missing_keywords"],
        "recommendations": recommendations,
    }
