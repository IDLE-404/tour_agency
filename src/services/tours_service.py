from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from src.db.database import DatabaseManager
from src.utils.validators import required


class ToursService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def list_tours(
        self,
        search: str = "",
        country: str = "",
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT id, name, country, city, date_from, date_to, price, seats, description
            FROM tours
            WHERE (? = '' OR name LIKE ? OR city LIKE ?)
              AND (? = '' OR country LIKE ?)
              AND (? IS NULL OR price >= ?)
              AND (? IS NULL OR price <= ?)
            ORDER BY date_from ASC
        """
        search_term = f"%{search.strip()}%"
        country_term = f"%{country.strip()}%"
        with self.db.get_connection() as conn:
            rows = conn.execute(
                sql,
                (
                    search.strip(),
                    search_term,
                    search_term,
                    country.strip(),
                    country_term,
                    min_price,
                    min_price,
                    max_price,
                    max_price,
                ),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_tour_choices(self) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, country, city, price FROM tours ORDER BY date_from"
            ).fetchall()
        return [dict(row) for row in rows]

    def list_countries(self) -> list[str]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT DISTINCT country FROM tours ORDER BY country").fetchall()
        return [row["country"] for row in rows]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM tours").fetchone()
        return int(row["total"])

    def create_tour(self, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        sql = """
            INSERT INTO tours (name, country, city, date_from, date_to, price, seats, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        args = (
            payload["name"].strip(),
            payload["country"].strip(),
            payload["city"].strip(),
            payload["date_from"],
            payload["date_to"],
            float(payload["price"]),
            int(payload["seats"]),
            payload.get("description", "").strip() or None,
        )
        with self.db.get_connection() as conn:
            conn.execute(sql, args)
            conn.commit()

    def update_tour(self, tour_id: int, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        sql = """
            UPDATE tours
            SET name = ?, country = ?, city = ?, date_from = ?, date_to = ?,
                price = ?, seats = ?, description = ?
            WHERE id = ?
        """
        args = (
            payload["name"].strip(),
            payload["country"].strip(),
            payload["city"].strip(),
            payload["date_from"],
            payload["date_to"],
            float(payload["price"]),
            int(payload["seats"]),
            payload.get("description", "").strip() or None,
            tour_id,
        )
        with self.db.get_connection() as conn:
            conn.execute(sql, args)
            conn.commit()

    def delete_tour(self, tour_id: int) -> None:
        with self.db.get_connection() as conn:
            try:
                conn.execute("DELETE FROM tours WHERE id = ?", (tour_id,))
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("Нельзя удалить тур, у него есть бронирования.") from exc

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        required_fields = {
            "name": "Название тура",
            "country": "Страна",
            "city": "Город",
        }
        for field, title in required_fields.items():
            if not required(payload.get(field, "")):
                raise ValueError(f"Поле '{title}' обязательно.")

        if float(payload.get("price", 0)) < 0:
            raise ValueError("Цена не может быть отрицательной.")

        if int(payload.get("seats", 0)) < 0:
            raise ValueError("Количество мест не может быть отрицательным.")

        start = datetime.strptime(payload["date_from"], "%Y-%m-%d")
        end = datetime.strptime(payload["date_to"], "%Y-%m-%d")
        if end < start:
            raise ValueError("Дата окончания не может быть раньше даты начала.")
