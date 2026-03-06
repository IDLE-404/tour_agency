from __future__ import annotations

import sqlite3
from pathlib import Path

from src.utils.paths import data_dir


class DatabaseManager:
    def __init__(self, db_path: Path | None = None) -> None:
        default_path = data_dir() / "tour_agency.db"
        self.db_path = db_path or default_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin'
                        CHECK(role IN ('admin', 'manager', 'seller', 'guest')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    email TEXT,
                    document TEXT NOT NULL,
                    birth_date TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    date_from TEXT NOT NULL,
                    date_to TEXT NOT NULL,
                    price REAL NOT NULL CHECK(price >= 0),
                    seats INTEGER NOT NULL CHECK(seats >= 0),
                    description TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    tour_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('новое', 'оплачено', 'отменено')),
                    amount REAL NOT NULL CHECK(amount >= 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT,
                    FOREIGN KEY(tour_id) REFERENCES tours(id) ON DELETE RESTRICT
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_clients_phone
                ON clients(phone)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tours_country
                ON tours(country)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_status_date
                ON bookings(status, booking_date)
                """
            )
            conn.commit()
