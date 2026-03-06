"""
Модуль инициализации базы данных.

Этот модуль перенесён в src/db/database_init.py.
Данный файл оставлен для обратной совместимости.
"""

from src.db.database_init import (
    _seed_bookings,
    _seed_clients,
    _seed_tours,
    _seed_users,
    seed_database,
)

__all__ = [
    "_seed_bookings",
    "_seed_clients",
    "_seed_tours",
    "_seed_users",
    "seed_database",
]
