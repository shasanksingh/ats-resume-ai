from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from app.core.files import safe_pdf_name, unique_pdf_path

router = APIRouter(prefix="/upload", tags=["Upload"])
CHUNK_SIZE = 1024 * 1024
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}


@router.post("/resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        safe_pdf_name(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    if file.content_type and file.content_type.lower() not in PDF_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="The selected file must be a PDF")

    target_path = unique_pdf_path(file.filename)
    temp_path = UPLOAD_DIR / f".upload-{uuid4().hex}.tmp"
    size_bytes = 0
    header = b""

    try:
        with temp_path.open("wb") as destination:
            while chunk := await file.read(CHUNK_SIZE):
                if not header:
                    header = chunk[:5]
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Resume PDF must be smaller than {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
                    )
                destination.write(chunk)

        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if header != b"%PDF-":
            raise HTTPException(status_code=415, detail="The selected file is not a valid PDF")

        temp_path.replace(target_path)
    except HTTPException:
        temp_path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="The resume could not be saved") from exc
    finally:
        await file.close()

    return {
        "filename": target_path.name,
        "original_filename": file.filename,
        "status": "uploaded successfully",
        "size_bytes": size_bytes,
    }
