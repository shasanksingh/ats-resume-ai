from fastapi import APIRouter, HTTPException
from copy import deepcopy
import re
from collections import Counter

from app.core.files import resolve_uploaded_pdf
from app.schemas.resume import LatexRequest, OptimizeRequest, RebuildRequest, RefinementRequest
from app.services.ats.ats_score import calculate_ats_score
from app.services.llm.nvidia_mistral_service import NvidiaServiceError, refine_selected_changes
from app.services.llm.resume_optimizer import enrich_supported_keywords, optimize_resume, project_selected_text
from app.services.parser.document_profile import load_pdf_resume
from app.services.rebuilder.preserved_pdf import preserve_pdf
from app.services.parser.resume_parser import (
    extract_text_from_pdf,
    SECTION_ALIASES,
)
from app.services.rag.rag_engine import search_rag
from app.services.rebuilder.latex_compiler import (
    LatexCompilationError,
    LatexCompilerUnavailable,
    compile_latex_source,
    compiler_status,
)
from app.services.rebuilder.latex_resume import generate_latex_resume, unique_output_path
from app.services.rebuilder.resume_rebuilder import build_docx

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
        include_local_model=not payload.use_ai,
    )
    result["filename"] = payload.filename
    result["optimization_version"] = 2
    result["optimization"]["ai_status"] = "not_requested"
    if payload.use_ai:
        optimization = result["optimization"]
        try:
            refinement = refine_selected_changes(
                "Rewrite each bullet for clarity, concision and relevance to this job. Reorganize clauses "
                "to connect the work to its purpose, rather than just repeating the original. "
                "Retain every tool, metric and achievement. Do not invent outcomes or unsupported keywords.",
                payload.job_description, structured.get("summary") or None,
                optimization["improved_bullets"],
            )
            optimization["improved_summary"] = refinement["summary"] or optimization["improved_summary"]
            optimization["improved_bullets"] = refinement["bullets"]
            optimization["refinement_provider"] = refinement["provider"]
            if refinement.get("provider_fallback"):
                optimization["warnings"].append("NVIDIA's primary model was unavailable or incomplete; its fast fallback model completed the review.")
            optimization["ai_status"] = "success"
            if refinement.get("warnings"):
                optimization["warnings"].extend(refinement["warnings"])
                optimization["ai_status"] = "partial"
            optimization["ai_message"] = "NVIDIA reviewed the selected resume content. Review the suggested changes before exporting."
            result["ats"] = calculate_ats_score(
                project_selected_text(resume_text, structured, optimization, payload.confirmed_keywords),
                payload.job_description,
            )
        except NvidiaServiceError as exc:
            optimization["ai_status"] = "fallback"
            optimization["ai_message"] = str(exc)
            optimization["warnings"].append(f"NVIDIA optimization unavailable: {exc} Local suggestions are available.")
    result["optimization"]["changed_count"] = sum(item["original"].strip() != item["improved"].strip() for item in result["optimization"]["improved_bullets"]) + int(bool(result["optimization"]["improved_summary"] and result["optimization"]["improved_summary"].strip() != structured.get("summary", "").strip()))
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

    export_structured, edits = prepare_selected_export(
        resume_text, structured, payload.job_description, payload.confirmed_keywords,
        payload.selected_summary, [item.model_dump() for item in payload.selected_bullets],
    )
    if payload.output_format == "pdf":
        return preserved_export(payload, structured, edits, resume_text)
    path = unique_output_path(payload.filename.rsplit('.', 1)[0], "docx")
    build_docx(path, export_structured, edits)
    from docx import Document
    exported_text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    return {
        **file_response(path, "docx"),
        "ats": calculate_ats_score(exported_text, payload.job_description),
        "baseline_ats": calculate_ats_score(resume_text, payload.job_description),
        "score_basis": "exported_docx_content",
        "warnings": ["DOCX page count depends on your word processor. Use PDF to preserve the original pages."],
    }


@router.post("/score")
def score_selected_changes(payload: LatexRequest):
    try:
        resume_text, structured = load_resume(payload.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _, edits = prepare_selected_export(resume_text, structured, payload.job_description,
        payload.confirmed_keywords, payload.selected_summary, [item.model_dump() for item in payload.selected_bullets])
    return {
        "baseline_ats": calculate_ats_score(resume_text, payload.job_description),
        "ats": calculate_ats_score(project_selected_text(resume_text, structured, edits, payload.confirmed_keywords), payload.job_description),
        "score_basis": "selected_changes_projection",
    }


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
    latex["applied_changes"] = sum(item.original != item.improved for item in payload.selected_bullets) + int(bool(payload.selected_summary and payload.selected_summary != structured.get("summary")))
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
        result = compile_latex_source(latex["latex_source"], payload.filename, structured.get("document_profile", {}).get("page_count"))
        from app.services.rebuilder.latex_resume import OUTPUT_DIR
        exported_text = extract_text_from_pdf(str(OUTPUT_DIR / result["filename"]))
        expected_text = project_selected_text(resume_text, structured, export_optimization)
        headings = {heading for values in SECTION_ALIASES.values() for heading in values}
        expected_text = "\n".join(line for line in expected_text.splitlines() if line.strip().lower().rstrip(":") not in headings)
        tokens = lambda value: Counter(re.findall(r"[a-z0-9]+", value.lower()))
        if tokens(expected_text) - tokens(exported_text):
            raise LatexCompilationError("Some source content could not be reconstructed faithfully. The original PDF layout was retained to prevent data loss.")
        result.update({"ats": calculate_ats_score(exported_text, payload.job_description),
            "baseline_ats": calculate_ats_score(resume_text, payload.job_description), "score_basis": "exported_pdf"})
        return result
    except (LatexCompilerUnavailable, LatexCompilationError) as exc:
        result = preserved_export(payload, structured, export_optimization, resume_text)
        result.update({"compiler": "Original PDF layout", "native_compiler": False, "fallback": True, "log_excerpt": str(exc)})
        result["warnings"].append(str(exc))
        return result


def prepare_selected_export(
    resume_text: str,
    structured: dict,
    job_description: str,
    confirmed_keywords: list[str],
    selected_summary: str | None,
    selected_bullets: list[dict],
) -> tuple[dict, dict]:
    originals = {bullet for entry in [*structured.get("experience", []), *structured.get("projects", [])] for bullet in entry.get("bullets", [])}
    if any(item["original"] not in originals for item in selected_bullets):
        raise HTTPException(status_code=422, detail="A selected bullet no longer matches this resume. Analyze it again before exporting.")
    if len({item["original"] for item in selected_bullets}) != len(selected_bullets):
        raise HTTPException(status_code=422, detail="Select each original bullet only once.")
    baseline_ats = calculate_ats_score(resume_text, job_description)
    export_structured, _ = enrich_supported_keywords(
        deepcopy(structured),
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
    return load_pdf_resume(path)


def file_response(path, format):
    return {"filename": path.name, "path": f"optimized/{path.name}",
        "download_url": f"/files/optimized/{path.name}", "format": format}


def preserved_export(payload, structured, edits, original_text):
    path = unique_output_path(payload.filename.rsplit('.', 1)[0], "pdf")
    result = preserve_pdf(resolve_uploaded_pdf(payload.filename), path, structured, edits)
    warnings = [item["reason"] for item in result["skipped_changes"]]
    if payload.confirmed_keywords:
        warnings.append("Additional skills are included in the LaTeX and DOCX layouts. The original PDF keeps its existing skills section.")
    result.update({**file_response(path, "pdf"), "warnings": list(dict.fromkeys(warnings)),
        "baseline_ats": calculate_ats_score(original_text, payload.job_description),
        "ats": calculate_ats_score(extract_text_from_pdf(str(path)), payload.job_description),
        "score_basis": "exported_pdf"})
    return result


def get_rag_context(job_description: str) -> tuple[str, str | None]:
    try:
        return "\n".join(search_rag(job_description)), None
    except Exception:
        return "", "Local role guidance was unavailable; deterministic ATS optimization was still completed."
