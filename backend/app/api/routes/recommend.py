from fastapi import APIRouter, HTTPException

from app.core.config import UPLOAD_DIR
from app.schemas.resume import MatchRequest
from app.services.ats.recommendation_engine import generate_recommendations
from app.services.parser.resume_parser import extract_text_from_pdf

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post("/resume")
def recommend_resume(payload: MatchRequest):
    resume_text = payload.resume_text or ""
    if payload.filename:
        try:
            resume_text = extract_text_from_pdf(str(UPLOAD_DIR / payload.filename))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Provide resume_text or filename")
    return generate_recommendations(resume_text, payload.job_description)
