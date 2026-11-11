from fastapi import APIRouter, HTTPException

from app.core.files import resolve_uploaded_pdf
from app.schemas.resume import AnalyzeRequest
from app.services.ats.ats_score import calculate_ats_score
from app.services.parser.document_profile import load_pdf_resume

router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post("/resume")
def analyze_resume(payload: AnalyzeRequest):
    try:
        pdf_path = resolve_uploaded_pdf(payload.filename)
        extracted_text, structured_resume = load_pdf_resume(pdf_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = {
        "filename": payload.filename,
        "resume_data": structured_resume,
        "raw_text_chars": len(extracted_text),
    }
    if payload.job_description:
        response["ats"] = calculate_ats_score(extracted_text, payload.job_description)
    return response
