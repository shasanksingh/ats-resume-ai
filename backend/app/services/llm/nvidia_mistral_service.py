import hashlib
import json
import re
import time
from copy import deepcopy
from threading import Lock
from typing import Dict, List

import requests

from app.core.config import (
    NVIDIA_API_KEY,
    NVIDIA_API_URL,
    NVIDIA_MAX_TOKENS,
    NVIDIA_MODEL,
    NVIDIA_TIMEOUT_SECONDS,
)


CACHE_TTL_SECONDS = 15 * 60
CACHE_MAX_ITEMS = 64
_cache: Dict[str, tuple[float, Dict]] = {}
_cache_lock = Lock()
_session = requests.Session()


class NvidiaServiceError(RuntimeError):
    pass


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

    request_data = {
        "instruction": instruction.strip(),
        "job_description": job_description[:2400],
        "summary": summary or None,
        "bullets": [
            {
                "original": item.get("original", "")[:1600],
                "current_suggestion": item.get("improved", "")[:1600],
            }
            for item in bullets[:8]
        ],
    }
    # Cache identity uses the full selections locally. Only the bounded
    # request_data above is sent to NVIDIA; truncated prefixes can otherwise
    # return another selection's original text from the cache.
    cache_identity = {"request": request_data, "bullets": bullets}
    cache_key = hashlib.sha256(
        f"{NVIDIA_MODEL}:{json.dumps(cache_identity, sort_keys=True)}".encode("utf-8")
    ).hexdigest()
    cached = get_cached(cache_key)
    if cached is not None:
        cached["cached"] = True
        cached["latency_ms"] = 0
        return cached

    prompt = (
        "Apply the candidate's instruction only to the supplied selected resume changes. "
        "Return JSON with keys summary and bullets. summary must be a string or null. "
        "bullets must be an array in the same order, each with improved and reason strings. "
        "Keep every statement concise, ATS-readable, and truthful. Never invent employers, "
        "degrees, certifications, tools, responsibilities, dates, or numeric results. "
        "Do not add a metric unless it already appears in the supplied content.\n\n"
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
        "reasoning_effort": "low",
    }
    started = time.perf_counter()
    try:
        response = _session.post(
            NVIDIA_API_URL,
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=NVIDIA_TIMEOUT_SECONDS,
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
        raise NvidiaServiceError(message) from exc
    except ValueError as exc:
        raise NvidiaServiceError("NVIDIA returned an unreadable response.") from exc

    content = extract_message_content(response_payload)
    parsed = parse_json_object(content)
    result = normalize_refinement(parsed, summary, bullets)
    result.update({
        "provider": NVIDIA_MODEL,
        "cached": False,
        "latency_ms": int((time.perf_counter() - started) * 1000),
    })
    set_cached(cache_key, result)
    return result


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
    return value


def normalize_refinement(parsed: Dict, summary: str | None, bullets: List[Dict[str, str]]) -> Dict:
    refined_summary = parsed.get("summary") if summary else None
    if summary and (not isinstance(refined_summary, str) or not refined_summary.strip()):
        refined_summary = summary

    returned_bullets = parsed.get("bullets") if isinstance(parsed.get("bullets"), list) else []
    normalized_bullets = []
    for index, source in enumerate(bullets[:8]):
        candidate = returned_bullets[index] if index < len(returned_bullets) else {}
        if not isinstance(candidate, dict):
            candidate = {}
        improved = str(candidate.get("improved") or source.get("improved") or "").strip()
        reason = str(candidate.get("reason") or "Refined from the selected suggestion.").strip()
        normalized_bullets.append({
            "original": source.get("original", ""),
            "improved": improved[:2000],
            "reason": reason[:800],
        })

    return {
        "summary": str(refined_summary).strip()[:4000] if refined_summary else None,
        "bullets": normalized_bullets,
    }


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
