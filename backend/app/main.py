from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analyze, jd, optimize, rag, recommend, upload
from app.core.config import UPLOAD_DIR

app = FastAPI(title="ATS Resume AI", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(jd.router)
app.include_router(rag.router)
app.include_router(recommend.router)
app.include_router(optimize.router)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")


@app.get("/")
def home():
    return {"message": "ATS Resume AI Backend Running"}
