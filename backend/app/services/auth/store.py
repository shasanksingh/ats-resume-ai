import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import DATABASE_PATH

PBKDF2_ITERATIONS = 210_000


class AuthError(ValueError):
    pass


def initialize_auth_db(db_path: Path | None = None) -> None:
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                visitor_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                message TEXT NOT NULL,
                page TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )


def create_user(name: str | None, email: str, password: str) -> dict:
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise AuthError("Enter a valid email address.")

    display_name = (name or normalized_email.split("@", 1)[0]).strip()[:120]
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    created_at = timestamp()

    initialize_auth_db()
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (display_name, normalized_email, password_hash, salt, created_at),
            )
            user = {
                "id": int(cursor.lastrowid),
                "name": display_name,
                "email": normalized_email,
                "created_at": created_at,
            }
    except sqlite3.IntegrityError as exc:
        raise AuthError("An account with this email already exists.") from exc

    return {"token": create_session(user["id"]), "user": user}


def login_user(email: str, password: str) -> dict:
    initialize_auth_db()
    normalized_email = normalize_email(email)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, name, email, password_hash, salt, created_at FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()

    if row is None or not verify_password(password, row["salt"], row["password_hash"]):
        raise AuthError("Invalid email or password.")

    user = row_to_user(row)
    return {"token": create_session(user["id"]), "user": user}


def get_user_by_token(token: str | None) -> dict | None:
    if not token:
        return None
    initialize_auth_db()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT users.id, users.name, users.email, users.created_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    return row_to_user(row) if row else None


def revoke_session(token: str | None) -> None:
    if not token:
        return
    initialize_auth_db()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DELETE FROM sessions WHERE token = ?", (token,))


def create_feedback(
    visitor_id: str,
    rating: int,
    message: str,
    page: str,
    token: str | None = None,
) -> dict:
    initialize_auth_db()
    user = get_user_by_token(token)
    created_at = timestamp()
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback (user_id, visitor_id, rating, message, page, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"] if user else None,
                visitor_id[:128],
                rating,
                message[:2000],
                page[:200],
                created_at,
            ),
        )
        feedback_id = int(cursor.lastrowid)
    return {
        "id": feedback_id,
        "status": "saved",
        "created_at": created_at,
    }


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, timestamp()),
        )
    return token


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt), expected_hash)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        return ""
    return normalized


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_user(row: sqlite3.Row) -> dict:
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }
