from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class AnalyzeRequest(ApiModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Uploaded resume PDF filename")
    job_description: Optional[str] = Field(default="", max_length=50000)


class MatchRequest(ApiModel):
    resume_text: Optional[str] = ""
    filename: Optional[str] = Field(default=None, max_length=255)
    job_description: str = Field(..., min_length=1, max_length=50000)


class OptimizeRequest(ApiModel):
    filename: str = Field(..., min_length=1, max_length=255)
    job_description: str = Field(..., min_length=1, max_length=50000)
    confirmed_keywords: List[str] = Field(default_factory=list, max_length=20)
    use_ai: bool = False


class RagSearchRequest(ApiModel):
    query: str = Field(..., min_length=1, max_length=5000)
    k: int = Field(default=4, ge=1, le=10)


class SelectedBullet(ApiModel):
    original: str = Field(..., min_length=1, max_length=2000)
    improved: str = Field(..., min_length=1, max_length=2000)
    reason: str = Field(default="", max_length=800)


class LatexRequest(ApiModel):
    filename: str = Field(..., min_length=1, max_length=255)
    job_description: str = Field(..., min_length=1, max_length=50000)
    template: Literal["jakes"] = "jakes"
    confirmed_keywords: List[str] = Field(default_factory=list, max_length=20)
    selected_summary: Optional[str] = Field(default=None, max_length=4000)
    selected_bullets: List[SelectedBullet] = Field(default_factory=list, max_length=8)


class RebuildRequest(LatexRequest):
    output_format: Literal["docx", "pdf"] = "docx"


class RefinementRequest(ApiModel):
    job_description: str = Field(..., min_length=1, max_length=50000)
    instruction: str = Field(..., min_length=3, max_length=2000)
    summary: Optional[str] = Field(default=None, max_length=4000)
    bullets: List[SelectedBullet] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def require_selected_change(self):
        if not self.summary and not self.bullets:
            raise ValueError("Select at least one summary or bullet change to refine.")
        return self


class BulletRewrite(BaseModel):
    original: str
    improved: str
    reason: str


class OptimizationResult(BaseModel):
    improved_summary: str
    improved_bullets: List[BulletRewrite]
    keyword_suggestions: List[str]
    warnings: List[str]
