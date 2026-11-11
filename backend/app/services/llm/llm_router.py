from functools import lru_cache
from pathlib import Path
from typing import Dict

from app.core.config import LOCAL_LLM_MODEL, MODEL_LOCAL_FILES_ONLY


@lru_cache(maxsize=1)
def get_local_generator():
    if MODEL_LOCAL_FILES_ONLY and not Path(LOCAL_LLM_MODEL).is_dir():
        from huggingface_hub import try_to_load_from_cache

        if not isinstance(try_to_load_from_cache(LOCAL_LLM_MODEL, "config.json"), str):
            raise RuntimeError("The optional local generation model is not cached.")
    from transformers import pipeline

    return pipeline(
        "text2text-generation",
        model=LOCAL_LLM_MODEL,
        model_kwargs={"local_files_only": MODEL_LOCAL_FILES_ONLY},
        device=-1,
    )


def generate_resume_optimization(prompt: str, max_new_tokens: int = 220) -> Dict:
    try:
        generator = get_local_generator()
        result = generator(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
        return {
            "success": True,
            "provider": LOCAL_LLM_MODEL,
            "text": result[0]["generated_text"].strip(),
        }
    except Exception as exc:
        return {
            "success": False,
            "provider": "local-model",
            "text": local_model_error_message(exc),
        }


def local_model_error_message(exc: Exception) -> str:
    if MODEL_LOCAL_FILES_ONLY:
        return (
            f"Local model '{LOCAL_LLM_MODEL}' is not available in this deployment cache. "
            "Deterministic resume optimization was used instead."
        )
    return str(exc)
