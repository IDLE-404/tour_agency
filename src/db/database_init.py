"""
Инициализация базы данных.

Создаёт структуру таблиц и базовых пользователей (если их нет).
Остальные данные заполняются вручную через интерфейс программы.
"""

from __future__ import annotations

from src.db.database import DatabaseManager
from src.services.auth_service import hash_password
from src.utils.roles import ROLE_ADMIN, ROLE_GUEST, ROLE_MANAGER, ROLE_SELLER


def _create_default_users(db: DatabaseManager) -> None:
    """
    Создать пользователей по умолчанию, если их ещё нет.
    
    Пользователи создаются только при первом запуске (когда таблица пустая).
    """
    users = [
        ("Administrator", "admin", "admin", ROLE_ADMIN),
        ("Марина Менеджер", "manager", "manager", ROLE_MANAGER),
        ("Павел Продавец", "seller", "seller", ROLE_SELLER),
        ("Гость системы", "guest", "guest", ROLE_GUEST),
    ]

    with db.get_connection() as conn:
        # Проверяем, есть ли уже пользователи
        exists = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if exists:
            # Пользователи уже есть — ничего не делаем
            return

        # Создаём пользователей по умолчанию
        conn.executemany(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            [(name, username, hash_password(password), role) for name, username, password, role in users],
        )
        conn.commit()


def seed_database(db: DatabaseManager) -> None:
    """
    Инициализировать базу данных.
    
    Таблицы создаются в database.py, здесь добавляем пользователей по умолчанию.
    
    Args:
        db: Менеджер базы данных
    """
    # Создаём пользователей по умолчанию (admin, manager, seller, guest)
    _create_default_users(db)
