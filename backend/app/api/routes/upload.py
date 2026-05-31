from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import UPLOAD_DIR

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    safe_name = Path(file.filename).name.replace(" ", "_")
    file_path = UPLOAD_DIR / safe_name
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_path.write_bytes(content)

    return {
        "filename": safe_name,
        "status": "uploaded successfully",
        "size_bytes": len(content),
    }
