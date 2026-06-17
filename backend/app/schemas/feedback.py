from pydantic import BaseModel, Field

from app.schemas.resume import ApiModel


class FeedbackRequest(ApiModel):
    visitor_id: str = Field(..., min_length=8, max_length=128)
    rating: int = Field(..., ge=1, le=5)
    message: str = Field(default="", max_length=2000)
    page: str = Field(default="/", max_length=200)


class FeedbackResponse(BaseModel):
    id: int
    status: str
    created_at: str
