import json
import re
from typing import Dict

from app.services.llm.llm_router import generate_resume_optimization


def extract_resume_json(resume_text: str) -> Dict:
    prompt = f"""
Extract resume information into compact JSON.
Return only JSON with these keys: name, email, phone, skills, education, projects.
Do not invent missing fields.

Resume:
{resume_text[:2500]}
"""
    result = generate_resume_optimization(prompt, max_new_tokens=256)
    if not result["success"]:
        return {"error": result["text"]}

    match = re.search(r"\{.*\}", result["text"], re.DOTALL)
    if not match:
        return {"raw_output": result["text"]}

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"raw_output": result["text"]}
