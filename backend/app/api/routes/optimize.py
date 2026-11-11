from fastapi import APIRouter, HTTPException

from app.core.files import resolve_uploaded_pdf
from app.schemas.resume import LatexRequest, OptimizeRequest, RebuildRequest, RefinementRequest
from app.services.ats.ats_score import calculate_ats_score
from app.services.llm.nvidia_mistral_service import NvidiaServiceError, refine_selected_changes
from app.services.llm.resume_optimizer import enrich_supported_keywords, optimize_resume
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


@router.post("/refine")
def refine_selected_changes_route(payload: RefinementRequest):
    try:
        return refine_selected_changes(
            payload.instruction,
            payload.job_description,
            payload.summary,
            [item.model_dump() for item in payload.bullets],
        )
    except NvidiaServiceError as exc:
        message = str(exc)
        status_code = 504 if "timed out" in message.lower() else 503 if "not configured" in message.lower() else 502
        raise HTTPException(status_code=status_code, detail=message) from exc


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

    export_structured, export_optimization = prepare_selected_export(
        resume_text,
        structured,
        payload.job_description,
        payload.confirmed_keywords,
        payload.selected_summary,
        [item.model_dump() for item in payload.selected_bullets],
    )
    latex = generate_latex_resume(
        export_structured,
        export_optimization,
        payload.filename,
        payload.template,
    )
    latex["applied_changes"] = len(payload.selected_bullets) + (1 if payload.selected_summary else 0)
    return latex


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

    export_structured, export_optimization = prepare_selected_export(
        resume_text,
        structured,
        payload.job_description,
        payload.confirmed_keywords,
        payload.selected_summary,
        [item.model_dump() for item in payload.selected_bullets],
    )
    latex = generate_latex_resume(
        export_structured,
        export_optimization,
        payload.filename,
        payload.template,
    )
    try:
        return compile_latex_source(latex["latex_source"], payload.filename)
    except LatexCompilerUnavailable as exc:
        return render_latex_preview_pdf(
            export_structured,
            export_optimization,
            payload.filename,
            str(exc),
        )
    except LatexCompilationError as exc:
        return render_latex_preview_pdf(
            export_structured,
            export_optimization,
            payload.filename,
            str(exc),
        )


def prepare_selected_export(
    resume_text: str,
    structured: dict,
    job_description: str,
    confirmed_keywords: list[str],
    selected_summary: str | None,
    selected_bullets: list[dict],
) -> tuple[dict, dict]:
    baseline_ats = calculate_ats_score(resume_text, job_description)
    export_structured, _ = enrich_supported_keywords(
        structured,
        resume_text,
        baseline_ats,
        confirmed_keywords,
    )
    return export_structured, {
        "improved_summary": selected_summary or "",
        "improved_bullets": selected_bullets,
    }


def load_resume(filename: str) -> tuple[str, dict]:
    path = resolve_uploaded_pdf(filename)
    resume_text = extract_text_from_pdf(str(path))
    structured = extract_resume_data(resume_text)
    structured["links"] = {
        **structured.get("links", {}),
        **extract_links_from_pdf(str(path)),
    }
    return resume_text, structured


def get_rag_context(job_description: str) -> tuple[str, str | None]:
    try:
        return "\n".join(search_rag(job_description)), None
    except Exception:
        return "", "Local role guidance was unavailable; deterministic ATS optimization was still completed."
