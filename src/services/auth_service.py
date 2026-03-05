from __future__ import annotations

import hashlib
from typing import Any

from src.db.database import DatabaseManager


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        query = "SELECT id, full_name, username, role, password_hash FROM users WHERE username = ?"
        with self.db.get_connection() as conn:
            row = conn.execute(query, (username.strip(),)).fetchone()

        if not row:
            return None

        if row["password_hash"] != hash_password(password):
            return None

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "username": row["username"],
            "role": row["role"],
        }
