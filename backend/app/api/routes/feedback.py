from fastapi import APIRouter, Header

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.auth import create_feedback

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest, x_session_token: str | None = Header(default=None)):
    return create_feedback(
        visitor_id=payload.visitor_id,
        rating=payload.rating,
        message=payload.message,
        page=payload.page,
        token=x_session_token,
    )
