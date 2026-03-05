from __future__ import annotations

import sqlite3
from typing import Any

from src.db.database import DatabaseManager
from src.utils.validators import required, valid_email, valid_phone


class ClientsService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def list_clients(self, search: str = "") -> list[dict[str, Any]]:
        sql = """
            SELECT id, full_name, phone, email, document, birth_date
            FROM clients
            WHERE (? = '' OR full_name LIKE ? OR phone LIKE ?)
            ORDER BY id DESC
        """
        term = f"%{search.strip()}%"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (search.strip(), term, term)).fetchall()
        return [dict(row) for row in rows]

    def list_client_choices(self) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, full_name, phone FROM clients ORDER BY full_name"
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM clients").fetchone()
        return int(row["total"])

    def create_client(self, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        sql = """
            INSERT INTO clients (full_name, phone, email, document, birth_date)
            VALUES (?, ?, ?, ?, ?)
        """
        args = (
            payload["full_name"].strip(),
            payload["phone"].strip(),
            payload["email"].strip() or None,
            payload["document"].strip(),
            payload.get("birth_date") or None,
        )
        try:
            with self.db.get_connection() as conn:
                conn.execute(sql, args)
                conn.commit()
        except sqlite3.IntegrityError as exc:
            if "clients.phone" in str(exc):
                raise ValueError("Клиент с таким телефоном уже существует.") from exc
            raise ValueError("Не удалось сохранить клиента.") from exc

    def update_client(self, client_id: int, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        sql = """
            UPDATE clients
            SET full_name = ?, phone = ?, email = ?, document = ?, birth_date = ?
            WHERE id = ?
        """
        args = (
            payload["full_name"].strip(),
            payload["phone"].strip(),
            payload["email"].strip() or None,
            payload["document"].strip(),
            payload.get("birth_date") or None,
            client_id,
        )
        try:
            with self.db.get_connection() as conn:
                conn.execute(sql, args)
                conn.commit()
        except sqlite3.IntegrityError as exc:
            if "clients.phone" in str(exc):
                raise ValueError("Клиент с таким телефоном уже существует.") from exc
            raise ValueError("Не удалось обновить клиента.") from exc

    def delete_client(self, client_id: int) -> None:
        try:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Нельзя удалить клиента, у него есть бронирования.") from exc

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        if not required(payload.get("full_name", "")):
            raise ValueError("Поле 'ФИО' обязательно.")
        if not required(payload.get("phone", "")):
            raise ValueError("Поле 'Телефон' обязательно.")
        if not valid_phone(payload["phone"]):
            raise ValueError("Телефон должен быть в формате +79991234567.")
        if not valid_email(payload.get("email", "")):
            raise ValueError("Некорректный email.")
        if not required(payload.get("document", "")):
            raise ValueError("Поле 'Документ' обязательно.")
