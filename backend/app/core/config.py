import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
RAG_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "rag-data"))
CHROMA_PATH = os.getenv("CHROMA_PATH", str(BASE_DIR / "vector_db"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "ats_resume.db"))
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "google/flan-t5-base")
MODEL_LOCAL_FILES_ONLY = os.getenv("MODEL_LOCAL_FILES_ONLY", "1") == "1"
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
