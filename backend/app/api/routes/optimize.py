from fastapi import APIRouter, HTTPException

from app.core.config import UPLOAD_DIR
from app.schemas.resume import OptimizeRequest, RebuildRequest
from app.services.llm.resume_optimizer import optimize_resume
from app.services.parser.resume_parser import extract_text_from_pdf
from app.services.rag.rag_engine import search_rag
from app.services.rebuilder.resume_rebuilder import rebuild_resume

router = APIRouter(prefix="/optimize", tags=["Resume Optimization"])


@router.post("/resume")
def optimize_resume_route(payload: OptimizeRequest):
    try:
        resume_text = extract_text_from_pdf(str(UPLOAD_DIR / payload.filename))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    rag_context = "\n".join(search_rag(payload.job_description))
    return optimize_resume(resume_text, payload.job_description, rag_context)


@router.post("/rebuild")
def rebuild_resume_route(payload: RebuildRequest):
    try:
        resume_text = extract_text_from_pdf(str(UPLOAD_DIR / payload.filename))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    rag_context = "\n".join(search_rag(payload.job_description))
    return rebuild_resume(
        resume_text,
        payload.job_description,
        rag_context,
        payload.filename,
        payload.output_format,
    )
