from fastapi import APIRouter

from app.schemas.resume import RagSearchRequest
from app.services.rag.rag_engine import create_vector_db, search_rag

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/build")
def build_rag():
    create_vector_db()
    return {"message": "Vector DB created successfully"}


@router.post("/search")
def rag_search(payload: RagSearchRequest):
    return {"results": search_rag(payload.query, payload.k)}
