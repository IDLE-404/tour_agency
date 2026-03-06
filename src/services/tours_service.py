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
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                t.id,
                t.name,
                t.country,
                t.city,
                t.date_from,
                t.date_to,
                t.price,
                t.seats,
                t.description,
                COALESCE(b.booked_count, 0) AS booked_seats,
                MAX(t.seats - COALESCE(b.booked_count, 0), 0) AS free_seats
            FROM tours t
            LEFT JOIN (
                SELECT tour_id, COUNT(*) AS booked_count
                FROM bookings
                WHERE status != 'отменено'
                GROUP BY tour_id
            ) b ON b.tour_id = t.id
            WHERE (? = '' OR t.name LIKE ? OR t.city LIKE ?)
              AND (? = '' OR t.country LIKE ?)
              AND (? IS NULL OR t.price >= ?)
              AND (? IS NULL OR t.price <= ?)
              AND (? IS NULL OR t.date_from >= ?)
              AND (? IS NULL OR t.date_to <= ?)
            ORDER BY t.date_from ASC
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
                    date_from,
                    date_from,
                    date_to,
                    date_to,
                ),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_tour_choices(self) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.id,
                    t.name,
                    t.country,
                    t.city,
                    t.price,
                    t.seats,
                    COALESCE(b.booked_count, 0) AS booked_seats,
                    MAX(t.seats - COALESCE(b.booked_count, 0), 0) AS free_seats
                FROM tours t
                LEFT JOIN (
                    SELECT tour_id, COUNT(*) AS booked_count
                    FROM bookings
                    WHERE status != 'отменено'
                    GROUP BY tour_id
                ) b ON b.tour_id = t.id
                ORDER BY t.date_from
                """
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
