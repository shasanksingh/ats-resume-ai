import hashlib
import json
import re
import time
from copy import deepcopy
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import requests
from app.services.ats.ats_score import extract_keywords

from app.core.config import (
    NVIDIA_API_KEY,
    NVIDIA_API_URL,
    NVIDIA_MAX_TOKENS,
    NVIDIA_MODEL,
    NVIDIA_FALLBACK_MODEL,
    NVIDIA_TIMEOUT_SECONDS,
)


CACHE_TTL_SECONDS = 15 * 60
CACHE_MAX_ITEMS = 64
_cache: Dict[str, tuple[float, Dict]] = {}
_cache_lock = Lock()
_session = requests.Session()


class NvidiaServiceError(RuntimeError):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


def refine_selected_changes(
    instruction: str,
    job_description: str,
    summary: str | None,
    bullets: List[Dict[str, str]],
) -> Dict:
    if not NVIDIA_API_KEY:
        raise NvidiaServiceError(
            "NVIDIA_API_KEY is not configured. Add it to backend/.env and restart the backend."
        )
    if not summary and not bullets:
        raise NvidiaServiceError("Select at least one summary or bullet change to refine.")

    # Bound reasoning and output per request. A single summary + eight-bullet
    # completion can exhaust the hosted model's deadline even with ample tokens.
    # At most four independent requests run concurrently and preserve input order.
    if len(bullets) > 2:
        started = time.perf_counter()
        batches = [bullets[index:index + 2] for index in range(0, min(len(bullets), 8), 2)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(refine_selected_changes, instruction, job_description,
                summary if index == 0 else None, batch) for index, batch in enumerate(batches)]
            results, failures = [], []
            for index, future in enumerate(futures):
                try:
                    results.append(future.result())
                except NvidiaServiceError as exc:
                    failures.append(exc)
                    retained = normalize_refinement({}, summary if index == 0 else None, batches[index])
                    for item in retained["bullets"]:
                        item["reason"] = "NVIDIA could not finish this batch; the existing suggestion was retained."
                    results.append({**retained, "provider": "", "cached": False})
            if len(failures) == len(batches):
                raise failures[0]
        return {"summary": results[0]["summary"],
            "bullets": [item for result in results for item in result["bullets"]],
            "provider": ", ".join(dict.fromkeys(result["provider"] for result in results if result["provider"])),
            "provider_fallback": any(result.get("provider_fallback") for result in results),
            "warnings": [f"{len(failures)} NVIDIA batch(es) could not be completed. Successful rewrites are available; retry to review the retained content."] if failures else [],
            "cached": all(result["cached"] for result in results),
            "latency_ms": int((time.perf_counter() - started) * 1000)}

    request_data = {
        "instruction": instruction.strip(),
        "job_description": job_description[:2400],
        "summary": summary or None,
        "bullets": [
            {
                "original": item.get("original", "")[:1600],
                "current_suggestion": item.get("improved", "")[:1600] if item.get("improved") != item.get("original") else None,
                "must_preserve": evidence_anchors(item.get("original", "")),
            }
            for item in bullets[:8]
        ],
    }
    # Cache identity uses the full selections locally. Only the bounded
    # request_data above is sent to NVIDIA; truncated prefixes can otherwise
    # return another selection's original text from the cache.
    cache_identity = {"request": request_data, "bullets": bullets}
    cache_key = hashlib.sha256(
        f"v5:{NVIDIA_MODEL}:{NVIDIA_FALLBACK_MODEL}:{NVIDIA_MAX_TOKENS}:{json.dumps(cache_identity, sort_keys=True)}".encode("utf-8")
    ).hexdigest()
    cached = get_cached(cache_key)
    if cached is not None:
        cached["cached"] = True
        cached["latency_ms"] = 0
        return cached

    prompt = (
        "Rewrite the supplied resume content for the target job, following the candidate's instruction. "
        "Return JSON with keys summary and bullets. summary must be a string or null. "
        "bullets must be an array in the same order, each with improved and reason strings. "
        "Keep every statement concise, ATS-readable, and truthful. Never invent employers, "
        "degrees, certifications, tools, responsibilities, dates, or numeric results. "
        "Do not add a metric unless it already appears in the supplied content.\n\n"
        "Produce a concrete alternative phrasing for EVERY supplied bullet, with a different sentence structure. "
        "Preserve every supplied fact, named tool, number, date, and achievement. "
        "Every must_preserve term is factual evidence and must remain in that bullet, not only in another bullet. "
        "Move the deliverable, purpose, or supported result earlier; combine clauses and replace wordy connectors. "
        "Start each bullet with an accurate action verb, not an adverb or noun phrase. "
        "Retain the original leading actions when they already describe concrete work; for example, "
        "'Architected and deployed' must retain both design and deployment, not just deployment. "
        "Do not echo the input, just substitute one synonym, or only change punctuation. "
        "Use role wording only when supported by the original. Aim for the original length or shorter. "
        "The reason must describe the specific structural change. Reword existing evidence without adding or removing facts.\n\n"
        "Example of a faithful structural rewrite:\n"
        "Original: Built services for internal teams, combining Python, FastAPI, logging, and validation.\n"
        "Improved: Built Python/FastAPI services with logging and validation for internal teams.\n"
        "Reason: Moved the tools next to the deliverable and shortened the connector.\n"
        "The example is only a writing demonstration; never add its facts to the candidate's content.\n\n"
        f"INPUT:\n{json.dumps(request_data, ensure_ascii=False)}"
    )
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise resume editor. Output valid JSON only and preserve factual accuracy.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": NVIDIA_MAX_TOKENS,
        "stream": False,
        "temperature": 0.2,
        "top_p": 0.9,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    started = time.perf_counter()
    models = list(dict.fromkeys(model for model in (NVIDIA_MODEL, NVIDIA_FALLBACK_MODEL) if model))
    for index, model in enumerate(models):
        model_payload = {**payload, "model": model}
        if "mistral-large-4" in model:
            model_payload["reasoning_effort"] = "low"
        elif "nemotron-3.5" in model:
            model_payload["chat_template_kwargs"] = {"enable_thinking": False}
            if "lightning" in model:
                model_payload["reasoning_budget"] = 0
            model_payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "resume_rewrites", "strict": True, "schema": {
                    "type": "object", "additionalProperties": False, "required": ["summary", "bullets"],
                    "properties": {
                        "summary": {"type": ["string", "null"]},
                        "bullets": {"type": "array", "minItems": len(bullets), "maxItems": len(bullets),
                            "items": {"type": "object", "additionalProperties": False,
                                "required": ["improved", "reason"], "properties": {
                                    "improved": {"type": "string", "minLength": 1}, "reason": {"type": "string"}}}}
                    }
                }
            }}
        remaining = max(1, NVIDIA_TIMEOUT_SECONDS - (time.perf_counter() - started))
        timeout = min(45, remaining / 2) if index == 0 and len(models) > 1 else remaining
        try:
            parsed = request_completion(model_payload, timeout)
            if len(parsed["bullets"]) != min(len(bullets), 8) or any(
                not isinstance(item, dict) or not isinstance(item.get("improved"), str) or not item["improved"].strip()
                for item in parsed["bullets"]
            ) or (parsed["summary"] is not None and not isinstance(parsed["summary"], str)):
                raise NvidiaServiceError("NVIDIA returned incomplete edits. Please retry optimization.")
            break
        except NvidiaServiceError as exc:
            if not exc.retryable or index == len(models) - 1:
                raise
    result = normalize_refinement(parsed, summary, bullets)
    result.update({
        "provider": model,
        "provider_fallback": index > 0,
        "cached": False,
        "latency_ms": int((time.perf_counter() - started) * 1000),
    })
    set_cached(cache_key, result)
    return result


def request_completion(payload: Dict, timeout: float) -> Dict:
    try:
        response = _session.post(
            NVIDIA_API_URL,
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_payload = response.json()
    except requests.Timeout as exc:
        raise NvidiaServiceError(
            f"NVIDIA refinement timed out after {NVIDIA_TIMEOUT_SECONDS} seconds. Try a shorter instruction."
        ) from exc
    except requests.RequestException as exc:
        status = getattr(exc.response, "status_code", None)
        message = f"NVIDIA refinement request failed{f' ({status})' if status else ''}."
        raise NvidiaServiceError(message, retryable=status not in {401, 402, 403}) from exc
    except ValueError as exc:
        raise NvidiaServiceError("NVIDIA returned an unreadable response.") from exc

    choices = response_payload.get("choices") or []
    if choices and choices[0].get("finish_reason") == "length":
        raise NvidiaServiceError("NVIDIA reached its response limit. Increase NVIDIA_MAX_TOKENS or refine fewer changes.")
    return parse_json_object(extract_message_content(response_payload))


def extract_message_content(payload: Dict) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NvidiaServiceError("NVIDIA response did not contain a completion.") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return str(content)


def parse_json_object(content: str) -> Dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise NvidiaServiceError("NVIDIA did not return the requested structured changes.")
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise NvidiaServiceError("NVIDIA returned invalid structured changes. Please retry.") from exc
    if not isinstance(value, dict):
        raise NvidiaServiceError("NVIDIA returned an unexpected response shape.")
    if "summary" not in value or not isinstance(value.get("bullets"), list):
        raise NvidiaServiceError("NVIDIA returned an incomplete response. Please retry optimization.")
    return value


def normalize_refinement(parsed: Dict, summary: str | None, bullets: List[Dict[str, str]]) -> Dict:
    refined_summary = parsed.get("summary") if summary else None
    if summary and (not isinstance(refined_summary, str) or not refined_summary.strip()):
        refined_summary = summary
    if summary and (len(refined_summary) > 4000 or not preserves_evidence(summary, refined_summary)):
        refined_summary = summary
    if summary and not distinct_rewrite(summary, refined_summary):
        refined_summary = summary

    returned_bullets = parsed.get("bullets") if isinstance(parsed.get("bullets"), list) else []
    normalized_bullets = []
    for index, source in enumerate(bullets[:8]):
        candidate = returned_bullets[index] if index < len(returned_bullets) else {}
        if not isinstance(candidate, dict):
            candidate = {}
        improved = str(candidate.get("improved") or source.get("improved") or "").strip()
        reason = str(candidate.get("reason") or "Refined from the selected suggestion.").strip()
        original = source.get("original", "")
        if len(improved) > 2000 or not preserves_evidence(original, improved):
            improved = original
            reason = "Original retained because the AI rewrite changed evidence, a number or a named skill, or exceeded the text limit."
        elif not distinct_rewrite(original, improved):
            improved = original
            reason = "Original retained; no distinct wording improvement was returned."
        normalized_bullets.append({
            "original": source.get("original", ""),
            "improved": improved[:2000],
            "reason": reason[:800],
        })

    return {
        "summary": str(refined_summary).strip()[:4000] if refined_summary else None,
        "bullets": normalized_bullets,
    }


def preserves_evidence(original: str, improved: str) -> bool:
    numbers = lambda value: {number.replace(",", "") for number in re.findall(r"\d+(?:[.,]\d+)*(?:%|\+)?", value)}
    compounds = set(re.findall(r"\b[a-zA-Z]+(?:-[a-zA-Z]+)+\b", original.lower()))
    acronyms = set(re.findall(r"\b[A-Z]{2,}\b", original))
    return (numbers(original) == numbers(improved)
        and set(extract_keywords(original)) == set(extract_keywords(improved))
        and all(term in improved.lower() for term in compounds)
        and all(re.search(r"\b" + re.escape(term) + r"\b", improved, re.I) for term in acronyms))


def evidence_anchors(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b[a-zA-Z]+(?:-[a-zA-Z]+)+\b|\b[A-Z]{2,}\b|\d+(?:[.,]\d+)*(?:%|\+)?", text)))


def distinct_rewrite(original: str, improved: str) -> bool:
    return re.findall(r"\w+", original.lower()) != re.findall(r"\w+", improved.lower())


def get_cached(key: str) -> Dict | None:
    now = time.time()
    with _cache_lock:
        cached = _cache.get(key)
        if cached is None:
            return None
        expires_at, value = cached
        if expires_at <= now:
            _cache.pop(key, None)
            return None
        return deepcopy(value)


def set_cached(key: str, value: Dict) -> None:
    with _cache_lock:
        if len(_cache) >= CACHE_MAX_ITEMS:
            oldest_key = min(_cache, key=lambda item: _cache[item][0])
            _cache.pop(oldest_key, None)
        _cache[key] = (time.time() + CACHE_TTL_SECONDS, deepcopy(value))
