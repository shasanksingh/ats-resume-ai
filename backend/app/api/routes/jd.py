from fastapi import APIRouter, HTTPException

from app.core.files import resolve_uploaded_pdf
from app.schemas.resume import MatchRequest
from app.services.ats.ats_score import calculate_ats_score
from app.services.parser.resume_parser import extract_text_from_pdf

router = APIRouter(prefix="/jd", tags=["JD Analysis"])


@router.post("/match")
def jd_match(payload: MatchRequest):
    resume_text = payload.resume_text or ""
    if payload.filename:
        try:
            pdf_path = resolve_uploaded_pdf(payload.filename)
            resume_text = extract_text_from_pdf(str(pdf_path))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Provide resume_text or filename")

    return calculate_ats_score(resume_text, payload.job_description)
