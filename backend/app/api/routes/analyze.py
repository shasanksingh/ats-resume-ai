from fastapi import APIRouter, HTTPException

from app.core.config import UPLOAD_DIR
from app.schemas.resume import AnalyzeRequest
from app.services.ats.ats_score import calculate_ats_score
from app.services.parser.resume_parser import extract_resume_data, extract_text_from_pdf

router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post("/resume")
def analyze_resume(payload: AnalyzeRequest):
    pdf_path = UPLOAD_DIR / payload.filename
    try:
        extracted_text = extract_text_from_pdf(str(pdf_path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    structured_resume = extract_resume_data(extracted_text)
    response = {
        "filename": payload.filename,
        "resume_data": structured_resume,
        "raw_text_chars": len(extracted_text),
    }
    if payload.job_description:
        response["ats"] = calculate_ats_score(extracted_text, payload.job_description)
    return response
