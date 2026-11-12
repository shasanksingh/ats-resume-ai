import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://ats-resume-ai-alpha.vercel.app",
)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
RAG_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "rag-data"))
CHROMA_PATH = os.getenv("CHROMA_PATH", str(BASE_DIR / "vector_db"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "ats_resume.db"))
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "google/flan-t5-base")
MODEL_LOCAL_FILES_ONLY = os.getenv("MODEL_LOCAL_FILES_ONLY", "1") == "1"
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
UPLOAD_RETENTION_HOURS = max(1, int(os.getenv("UPLOAD_RETENTION_HOURS", "24")))
CLEANUP_INTERVAL_SECONDS = max(300, int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600")))
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_API_URL = os.getenv(
    "NVIDIA_API_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
).strip()
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "mistralai/mistral-large-4-1t-a52b").strip()
NVIDIA_FALLBACK_MODEL = os.getenv("NVIDIA_FALLBACK_MODEL", "nvidia/nemotron-3.5-super-vl-120b-a12b").strip()
NVIDIA_TIMEOUT_SECONDS = max(5, min(120, int(os.getenv("NVIDIA_TIMEOUT_SECONDS", "120"))))
NVIDIA_MAX_TOKENS = max(512, min(8192, int(os.getenv("NVIDIA_MAX_TOKENS", "4096"))))


def parse_cors_origins() -> list[str]:
    configured = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    return list(dict.fromkeys([*DEFAULT_CORS_ORIGINS, *configured]))


CORS_ORIGINS = parse_cors_origins()


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
