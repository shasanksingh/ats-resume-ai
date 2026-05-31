import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
RAG_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "rag-data"))
CHROMA_PATH = os.getenv("CHROMA_PATH", str(BASE_DIR / "vector_db"))
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "google/flan-t5-base")
MODEL_LOCAL_FILES_ONLY = os.getenv("MODEL_LOCAL_FILES_ONLY", "1") == "1"


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
