import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from app.core.config import UPLOAD_DIR, UPLOAD_RETENTION_HOURS


RETENTION_SUFFIXES = {".pdf", ".docx", ".tex", ".tmp"}


def expires_at_iso(created_at: datetime | None = None) -> str:
    created = created_at or datetime.now(timezone.utc)
    return (created + timedelta(hours=UPLOAD_RETENTION_HOURS)).isoformat()


def cleanup_expired_files(now: float | None = None) -> Dict[str, int]:
    """Remove only generated/uploaded resume artifacts older than the retention window."""
    root = UPLOAD_DIR.resolve()
    if not root.exists() or root.parent == root or len(root.parts) < 3:
        return {"removed": 0, "errors": 0}

    cutoff = (now if now is not None else time.time()) - (UPLOAD_RETENTION_HOURS * 3600)
    removed = 0
    errors = 0

    for candidate in root.rglob("*"):
        try:
            if not candidate.is_file() or candidate.suffix.lower() not in RETENTION_SUFFIXES:
                continue
            resolved = candidate.resolve()
            if not resolved.is_relative_to(root) or resolved.stat().st_mtime > cutoff:
                continue
            resolved.unlink()
            removed += 1
        except (FileNotFoundError, OSError):
            errors += 1

    return {"removed": removed, "errors": errors}
