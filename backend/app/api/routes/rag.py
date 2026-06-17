from fastapi import APIRouter, HTTPException

from app.schemas.resume import RagSearchRequest
from app.services.rag.rag_engine import create_vector_db, search_rag_detailed

router = APIRouter(prefix="/rag", tags=["Role Guidance"])


@router.post("/build")
def build_rag():
    try:
        create_vector_db()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local role guidance index could not be built") from exc
    return {"message": "Local role guidance index created successfully"}


@router.post("/search")
def rag_search(payload: RagSearchRequest):
    try:
        detailed = search_rag_detailed(payload.query, payload.k)
        return {
            "results": [item["content"] for item in detailed],
            "sources": [
                {
                    "source": item["source"],
                    "retrieval": item["retrieval"],
                }
                for item in detailed
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local role guidance search is unavailable") from exc
