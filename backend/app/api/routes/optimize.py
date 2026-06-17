from fastapi import APIRouter, HTTPException

from app.core.files import resolve_uploaded_pdf
from app.schemas.resume import LatexRequest, OptimizeRequest, RebuildRequest
from app.services.llm.resume_optimizer import optimize_resume
from app.services.parser.resume_parser import (
    extract_links_from_pdf,
    extract_resume_data,
    extract_text_from_pdf,
)
from app.services.rag.rag_engine import search_rag
from app.services.rebuilder.latex_compiler import (
    LatexCompilationError,
    LatexCompilerUnavailable,
    compile_latex_source,
    compiler_status,
    render_latex_preview_pdf,
)
from app.services.rebuilder.latex_resume import generate_latex_resume
from app.services.rebuilder.resume_rebuilder import rebuild_resume

router = APIRouter(prefix="/optimize", tags=["Resume Optimization"])


@router.post("/resume")
def optimize_resume_route(payload: OptimizeRequest):
    try:
        resume_text, structured = load_resume(payload.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    rag_context, rag_warning = get_rag_context(payload.job_description)
    result = optimize_resume(
        resume_text,
        payload.job_description,
        rag_context,
        structured_resume=structured,
        confirmed_keywords=payload.confirmed_keywords,
    )
    if rag_warning:
        result["optimization"]["warnings"].append(rag_warning)
    return result


@router.post("/rebuild")
def rebuild_resume_route(payload: RebuildRequest):
    try:
        resume_text, structured = load_resume(payload.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    rag_context, _ = get_rag_context(payload.job_description)
    return rebuild_resume(
        resume_text,
        payload.job_description,
        rag_context,
        payload.filename,
        payload.output_format,
        structured_resume=structured,
        confirmed_keywords=payload.confirmed_keywords,
    )


@router.post("/latex")
def generate_latex_route(payload: LatexRequest):
    try:
        resume_text, structured = load_resume(payload.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    rag_context, _ = get_rag_context(payload.job_description)
    result = optimize_resume(
        resume_text,
        payload.job_description,
        rag_context,
        include_local_model=False,
        structured_resume=structured,
        confirmed_keywords=payload.confirmed_keywords,
    )
    return generate_latex_resume(
        result["structured_resume"],
        result["optimization"],
        payload.filename,
        payload.template,
    )


@router.get("/latex/status")
def latex_status_route():
    return compiler_status()


@router.post("/latex/compile")
def compile_latex_route(payload: LatexRequest):
    try:
        resume_text, structured = load_resume(payload.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    rag_context, _ = get_rag_context(payload.job_description)
    result = optimize_resume(
        resume_text,
        payload.job_description,
        rag_context,
        include_local_model=False,
        structured_resume=structured,
        confirmed_keywords=payload.confirmed_keywords,
    )
    latex = generate_latex_resume(
        result["structured_resume"],
        result["optimization"],
        payload.filename,
        payload.template,
    )
    try:
        return compile_latex_source(latex["latex_source"], payload.filename)
    except LatexCompilerUnavailable as exc:
        return render_latex_preview_pdf(
            result["structured_resume"],
            result["optimization"],
            payload.filename,
            str(exc),
        )
    except LatexCompilationError as exc:
        return render_latex_preview_pdf(
            result["structured_resume"],
            result["optimization"],
            payload.filename,
            str(exc),
        )


def load_resume(filename: str) -> tuple[str, dict]:
    path = resolve_uploaded_pdf(filename)
    resume_text = extract_text_from_pdf(str(path))
    structured = extract_resume_data(resume_text)
    structured["links"] = extract_links_from_pdf(str(path))
    return resume_text, structured


def get_rag_context(job_description: str) -> tuple[str, str | None]:
    try:
        return "\n".join(search_rag(job_description)), None
    except Exception:
        return "", "Local role guidance was unavailable; deterministic ATS optimization was still completed."
