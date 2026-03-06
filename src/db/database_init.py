"""
Инициализация базы данных демо-данными.

Создаёт тестовых пользователей, клиентов, туры и бронирования
при первом запуске приложения.
"""

from __future__ import annotations

from src.db.database import DatabaseManager
from src.services.auth_service import hash_password
from src.utils.roles import ROLE_ADMIN, ROLE_GUEST, ROLE_MANAGER, ROLE_SELLER


def _seed_users(db: DatabaseManager) -> None:
    """Создать демо-пользователей."""
    users = [
        ("Administrator", "admin", "admin", ROLE_ADMIN),
        ("Марина Менеджер", "manager", "manager", ROLE_MANAGER),
        ("Павел Продавец", "seller", "seller", ROLE_SELLER),
        ("Гость системы", "guest", "guest", ROLE_GUEST),
    ]

    with db.get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            [(name, username, hash_password(password), role) for name, username, password, role in users],
        )
        # Фиксируем пароли демо-аккаунтов даже при старых/грязных данных БД.
        demo_passwords = {
            "admin": "admin",
            "manager": "manager",
            "seller": "seller",
            "guest": "guest",
        }
        for username, password in demo_passwords.items():
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE LOWER(username) = ?
                """,
                (hash_password(password), username),
            )
        conn.commit()


def _seed_clients(db: DatabaseManager) -> None:
    """Создать демо-клиентов."""
    clients = [
        ("Иван Петров", "+79991112233", "ivan@mail.ru", "4500 123456", "1988-05-14"),
        ("Мария Смирнова", "+79991112234", "maria@mail.ru", "4501 987654", "1992-11-02"),
        ("Алексей Орлов", "+79991112235", "alex@mail.ru", "4510 443322", "1985-01-27"),
        ("Екатерина Волкова", "+79991112236", "katya@mail.ru", "4502 556677", "1996-09-18"),
        ("Николай Соколов", "+79991112237", "n.sokolov@mail.ru", "4505 009988", "1990-07-21"),
        ("Ольга Кузнецова", "+79991112238", "olga.k@mail.ru", "4507 222111", "1994-03-08"),
        ("Дмитрий Федоров", "+79991112239", "d.fedorov@mail.ru", "4512 100200", "1987-12-30"),
    ]

    with db.get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM clients LIMIT 1").fetchone()
        if exists:
            return

        conn.executemany(
            """
            INSERT INTO clients (full_name, phone, email, document, birth_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            clients,
        )
        conn.commit()


def _seed_tours(db: DatabaseManager) -> None:
    """Создать демо-туры."""
    tours = [
        ("Огни Стамбула", "Турция", "Стамбул", "2026-04-10", "2026-04-16", 72000, 20, "Городской тур с экскурсиями."),
        ("Римские каникулы", "Италия", "Рим", "2026-05-05", "2026-05-12", 98000, 14, "История и гастрономия."),
        ("Париж и музеи", "Франция", "Париж", "2026-06-01", "2026-06-07", 110000, 12, "Культурная программа + свободное время."),
        ("Бали релакс", "Индонезия", "Денпасар", "2026-07-18", "2026-07-28", 145000, 10, "Пляжный отдых и SPA."),
        ("Дубай Шоппинг", "ОАЭ", "Дубай", "2026-04-25", "2026-04-30", 85000, 18, "Отели 4* и шоппинг-туры."),
        ("Грузинский уикенд", "Грузия", "Тбилиси", "2026-03-20", "2026-03-24", 56000, 16, "Вино, кухня и горные виды."),
        ("Прага комфорт", "Чехия", "Прага", "2026-05-15", "2026-05-21", 76000, 15, "Старый город и замки."),
    ]

    with db.get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM tours LIMIT 1").fetchone()
        if exists:
            return

        conn.executemany(
            """
            INSERT INTO tours (name, country, city, date_from, date_to, price, seats, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tours,
        )
        conn.commit()


def _seed_bookings(db: DatabaseManager) -> None:
    """Создать демо-бронирования."""
    with db.get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM bookings LIMIT 1").fetchone()
        if exists:
            return

        clients = conn.execute("SELECT id FROM clients ORDER BY id LIMIT 5").fetchall()
        tours = conn.execute("SELECT id, price FROM tours ORDER BY id LIMIT 5").fetchall()
        if not clients or not tours:
            return

        bookings = [
            (clients[0]["id"], tours[0]["id"], "2026-03-02", "новое", tours[0]["price"]),
            (clients[1]["id"], tours[1]["id"], "2026-03-01", "оплачено", tours[1]["price"]),
            (clients[2]["id"], tours[2]["id"], "2026-02-28", "оплачено", tours[2]["price"]),
            (clients[3]["id"], tours[3]["id"], "2026-02-27", "отменено", tours[3]["price"]),
            (clients[4]["id"], tours[4]["id"], "2026-02-26", "новое", tours[4]["price"]),
        ]

        conn.executemany(
            """
            INSERT INTO bookings (client_id, tour_id, booking_date, status, amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            bookings,
        )
        conn.commit()


def seed_database(db: DatabaseManager) -> None:
    """
    Инициализировать базу данных демо-данными.

    Args:
        db: Менеджер базы данных
    """
    _seed_users(db)
    _seed_clients(db)
    _seed_tours(db)
    _seed_bookings(db)
