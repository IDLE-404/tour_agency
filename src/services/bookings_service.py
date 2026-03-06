from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

from src.db.database import DatabaseManager


ALLOWED_STATUSES = ("новое", "оплачено", "отменено")


class BookingsService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def list_bookings(
        self,
        search: str = "",
        status: str = "",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                b.id,
                b.client_id,
                b.tour_id,
                b.booking_date,
                b.status,
                b.amount,
                c.full_name AS client_name,
                c.phone AS client_phone,
                t.name AS tour_name,
                t.country || ', ' || t.city AS destination
            FROM bookings b
            JOIN clients c ON c.id = b.client_id
            JOIN tours t ON t.id = b.tour_id
            WHERE (? = '' OR c.full_name LIKE ? OR c.phone LIKE ? OR t.name LIKE ?)
              AND (? = '' OR b.status = ?)
              AND (? IS NULL OR b.booking_date >= ?)
              AND (? IS NULL OR b.booking_date <= ?)
            ORDER BY b.booking_date DESC, b.id DESC
        """
        term = f"%{search.strip()}%"
        with self.db.get_connection() as conn:
            rows = conn.execute(
                sql,
                (
                    search.strip(),
                    term,
                    term,
                    term,
                    status.strip(),
                    status.strip(),
                    date_from,
                    date_from,
                    date_to,
                    date_to,
                ),
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM bookings").fetchone()
        return int(row["total"])

    def paid_revenue(self) -> float:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM bookings WHERE status = 'оплачено'"
            ).fetchone()
        return float(row["total"])

    def last_bookings(self, limit: int = 5) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    b.booking_date,
                    c.full_name AS client_name,
                    t.name AS tour_name,
                    b.status,
                    b.amount
                FROM bookings b
                JOIN clients c ON c.id = b.client_id
                JOIN tours t ON t.id = b.tour_id
                ORDER BY b.booking_date DESC, b.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def daily_summary(self, day: str) -> dict[str, Any]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_count,
                    COALESCE(SUM(CASE WHEN status = 'оплачено' THEN 1 ELSE 0 END), 0) AS paid_count,
                    COALESCE(SUM(CASE WHEN status = 'отменено' THEN 1 ELSE 0 END), 0) AS canceled_count,
                    COALESCE(SUM(CASE WHEN status = 'оплачено' THEN amount ELSE 0 END), 0) AS paid_revenue
                FROM bookings
                WHERE booking_date = ?
                """,
                (day,),
            ).fetchone()

        return {
            "total_count": int(row["total_count"]) if row else 0,
            "paid_count": int(row["paid_count"]) if row else 0,
            "canceled_count": int(row["canceled_count"]) if row else 0,
            "paid_revenue": float(row["paid_revenue"]) if row else 0.0,
        }

    def daily_popular_tours(self, day: str, limit: int = 10) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.name AS tour_name,
                    t.country || ', ' || t.city AS destination,
                    COUNT(*) AS bookings_count,
                    COALESCE(SUM(CASE WHEN b.status = 'оплачено' THEN 1 ELSE 0 END), 0) AS paid_count,
                    COALESCE(SUM(CASE WHEN b.status = 'оплачено' THEN b.amount ELSE 0 END), 0) AS paid_revenue
                FROM bookings b
                JOIN tours t ON t.id = b.tour_id
                WHERE b.booking_date = ?
                GROUP BY b.tour_id, t.name, t.country, t.city
                ORDER BY bookings_count DESC, paid_revenue DESC, t.name ASC
                LIMIT ?
                """,
                (day, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_booking(self, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        if payload["status"] != "отменено":
            self._ensure_available_seat(int(payload["tour_id"]))
        sql = """
            INSERT INTO bookings (client_id, tour_id, booking_date, status, amount)
            VALUES (?, ?, ?, ?, ?)
        """
        args = (
            int(payload["client_id"]),
            int(payload["tour_id"]),
            payload["booking_date"],
            payload["status"],
            float(payload["amount"]),
        )
        with self.db.get_connection() as conn:
            conn.execute(sql, args)
            conn.commit()

    def update_booking(self, booking_id: int, payload: dict[str, Any]) -> None:
        self._validate_payload(payload)
        if payload["status"] != "отменено":
            self._ensure_available_seat(int(payload["tour_id"]), exclude_booking_id=booking_id)
        sql = """
            UPDATE bookings
            SET client_id = ?, tour_id = ?, booking_date = ?, status = ?, amount = ?
            WHERE id = ?
        """
        args = (
            int(payload["client_id"]),
            int(payload["tour_id"]),
            payload["booking_date"],
            payload["status"],
            float(payload["amount"]),
            booking_id,
        )
        with self.db.get_connection() as conn:
            conn.execute(sql, args)
            conn.commit()

    def delete_booking(self, booking_id: int) -> None:
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            conn.commit()

    def export_to_csv(self, file_path: str | Path, rows: list[dict[str, Any]]) -> None:
        file_path = Path(file_path)
        with file_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                [
                    "ID",
                    "Клиент",
                    "Телефон",
                    "Тур",
                    "Направление",
                    "Дата бронирования",
                    "Статус",
                    "Сумма",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["client_name"],
                        row["client_phone"],
                        row["tour_name"],
                        row["destination"],
                        row["booking_date"],
                        row["status"],
                        f"{row['amount']:.2f}",
                    ]
                )

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        if not payload.get("client_id"):
            raise ValueError("Выберите клиента.")
        if not payload.get("tour_id"):
            raise ValueError("Выберите тур.")
        if payload.get("status") not in ALLOWED_STATUSES:
            raise ValueError("Некорректный статус бронирования.")
        if float(payload.get("amount", 0)) < 0:
            raise ValueError("Сумма не может быть отрицательной.")

    def tour_price(self, tour_id: int) -> float:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT price FROM tours WHERE id = ?", (tour_id,)).fetchone()
        if not row:
            return 0.0
        return float(row["price"])

    def available_seats(self, tour_id: int, exclude_booking_id: int | None = None) -> int:
        sql = """
            SELECT
                t.seats AS total_seats,
                COALESCE(SUM(CASE WHEN b.status != 'отменено' THEN 1 ELSE 0 END), 0) AS booked_seats
            FROM tours t
            LEFT JOIN bookings b ON b.tour_id = t.id AND (? IS NULL OR b.id != ?)
            WHERE t.id = ?
            GROUP BY t.id
        """
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (exclude_booking_id, exclude_booking_id, tour_id)).fetchone()

        if not row:
            return 0
        return max(int(row["total_seats"]) - int(row["booked_seats"]), 0)

    def _ensure_available_seat(self, tour_id: int, exclude_booking_id: int | None = None) -> None:
        if self.available_seats(tour_id, exclude_booking_id=exclude_booking_id) <= 0:
            raise ValueError("Свободных мест по выбранному туру нет.")
