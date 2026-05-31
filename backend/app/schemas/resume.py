from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    filename: str = Field(..., description="Uploaded resume PDF filename")
    job_description: Optional[str] = ""


class MatchRequest(BaseModel):
    resume_text: Optional[str] = ""
    filename: Optional[str] = None
    job_description: str


class OptimizeRequest(BaseModel):
    filename: str
    job_description: str


class RagSearchRequest(BaseModel):
    query: str
    k: int = 4


class RebuildRequest(BaseModel):
    filename: str
    job_description: str
    output_format: str = "docx"


class BulletRewrite(BaseModel):
    original: str
    improved: str
    reason: str


class OptimizationResult(BaseModel):
    improved_summary: str
    improved_bullets: List[BulletRewrite]
    keyword_suggestions: List[str]
    warnings: List[str]
