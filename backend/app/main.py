from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analyze, auth, feedback, jd, optimize, rag, recommend, upload
from app.core.config import CORS_ORIGINS, UPLOAD_DIR
from app.services.auth import initialize_auth_db

app = FastAPI(title="ATS Resume Studio", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(feedback.router)
app.include_router(analyze.router)
app.include_router(jd.router)
app.include_router(rag.router)
app.include_router(recommend.router)
app.include_router(optimize.router)
app.mount("/files/optimized", StaticFiles(directory=UPLOAD_DIR / "optimized"), name="optimized-files")


@app.get("/")
def home():
    return {"message": "ATS Resume Studio Backend Running"}


@app.on_event("startup")
def startup():
    initialize_auth_db()


@app.get("/health")
def health():
    return {"status": "ok"}