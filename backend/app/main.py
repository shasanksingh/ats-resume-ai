import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analyze, auth, feedback, jd, optimize, rag, recommend, upload
from app.core.config import CLEANUP_INTERVAL_SECONDS, CORS_ORIGINS, UPLOAD_DIR
from app.core.retention import cleanup_expired_files
from app.services.auth import initialize_auth_db


async def periodic_file_cleanup():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        await asyncio.to_thread(cleanup_expired_files)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_auth_db()
    await asyncio.to_thread(cleanup_expired_files)
    cleanup_task = asyncio.create_task(periodic_file_cleanup())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(title="ATS Resume Studio", version="0.4.0", lifespan=lifespan)

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


@app.get("/health")
def health():
    return {"status": "ok"}
