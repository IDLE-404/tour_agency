from __future__ import annotations

import sqlite3
from typing import Any

from src.db.database import DatabaseManager
from src.services.auth_service import hash_password
from src.utils.roles import ROLE_ADMIN, ROLE_CHOICES


class UsersService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def list_users(self, search: str = "") -> list[dict[str, Any]]:
        sql = """
            SELECT id, full_name, username, role, created_at
            FROM users
            WHERE (? = '' OR full_name LIKE ? OR username LIKE ?)
            ORDER BY id DESC
        """
        term = f"%{search.strip()}%"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (search.strip(), term, term)).fetchall()
        return [dict(row) for row in rows]

    def create_user(self, payload: dict[str, Any]) -> None:
        full_name = payload.get("full_name", "").strip()
        username = payload.get("username", "").strip()
        password = payload.get("password", "")
        role = str(payload.get("role", "")).strip().lower()

        if not full_name:
            raise ValueError("Поле 'ФИО' обязательно.")
        if not username:
            raise ValueError("Поле 'Логин' обязательно.")
        if len(username) < 3:
            raise ValueError("Логин должен содержать минимум 3 символа.")
        if len(password) < 4:
            raise ValueError("Пароль должен содержать минимум 4 символа.")
        if role not in ROLE_CHOICES:
            raise ValueError("Некорректная роль пользователя.")

        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (full_name, username, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (full_name, username, hash_password(password), role),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Пользователь с таким логином уже существует.") from exc

    def update_user(self, user_id: int, payload: dict[str, Any]) -> None:
        full_name = payload.get("full_name", "").strip()
        username = payload.get("username", "").strip()
        password = payload.get("password", "")
        role = str(payload.get("role", "")).strip().lower()

        if not full_name:
            raise ValueError("Поле 'ФИО' обязательно.")
        if not username:
            raise ValueError("Поле 'Логин' обязательно.")
        if len(username) < 3:
            raise ValueError("Логин должен содержать минимум 3 символа.")
        if role not in ROLE_CHOICES:
            raise ValueError("Некорректная роль пользователя.")

        with self.db.get_connection() as conn:
            current = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
            if not current:
                raise ValueError("Пользователь не найден.")

            if current["role"] == ROLE_ADMIN and role != ROLE_ADMIN and self.admin_count() <= 1:
                raise ValueError("В системе должен оставаться хотя бы один администратор.")

            try:
                if password:
                    if len(password) < 4:
                        raise ValueError("Пароль должен содержать минимум 4 символа.")
                    conn.execute(
                        """
                        UPDATE users
                        SET full_name = ?, username = ?, role = ?, password_hash = ?
                        WHERE id = ?
                        """,
                        (full_name, username, role, hash_password(password), user_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE users
                        SET full_name = ?, username = ?, role = ?
                        WHERE id = ?
                        """,
                        (full_name, username, role, user_id),
                    )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("Пользователь с таким логином уже существует.") from exc

    def delete_user(self, user_id: int) -> None:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("Пользователь не найден.")

            if row["role"] == ROLE_ADMIN and self.admin_count() <= 1:
                raise ValueError("Нельзя удалить последнего администратора.")

            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    def admin_count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM users WHERE role = ?", (ROLE_ADMIN,)).fetchone()
        return int(row["total"])
