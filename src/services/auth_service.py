"""
Сервис аутентификации.

Обрабатывает вход пользователей:
- Хеширование паролей (PBKDF2)
- Проверка паролей
- Автоматическое обновление хешей
"""

from __future__ import annotations

import binascii
import hmac
import hashlib
import os
from typing import Any

from src.db.database import DatabaseManager
from src.utils.roles import ROLE_ADMIN, ROLE_GUEST, ROLE_MANAGER, ROLE_SELLER, normalize_role


PBKDF2_ITERATIONS: int = 260_000
PBKDF2_SALT_BYTES: int = 16
PBKDF2_PREFIX: str = "pbkdf2_sha256"

DEMO_ROLE_BY_USERNAME: dict[str, str] = {
    "admin": ROLE_ADMIN,
    "manager": ROLE_MANAGER,
    "seller": ROLE_SELLER,
    "guest": ROLE_GUEST,
}


def hash_password(password: str) -> str:
    """
    Хешировать пароль с помощью PBKDF2.

    Args:
        password: Пароль в открытом виде

    Returns:
        Хешированный пароль в формате prefix$iterations$salt$hash
    """
    salt = os.urandom(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"{PBKDF2_PREFIX}${PBKDF2_ITERATIONS}$"
        f"{binascii.hexlify(salt).decode('ascii')}$"
        f"{binascii.hexlify(digest).decode('ascii')}"
    )


def _is_legacy_sha256_hash(stored_hash: str) -> bool:
    """
    Проверить, является ли хеш устаревшим SHA256.

    Args:
        stored_hash: Сохранённый хеш пароля

    Returns:
        True если это legacy хеш
    """
    if len(stored_hash) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in stored_hash.lower())


def verify_password(stored_hash: str, password: str) -> tuple[bool, bool]:
    """
    Проверить пароль against сохранённого хеша.

    Args:
        stored_hash: Сохранённый хеш пароля
        password: Пароль для проверки

    Returns:
        Кортеж (пароль верен, требуется обновление хеша)
    """
    if not stored_hash:
        return False, False

    if stored_hash.startswith(f"{PBKDF2_PREFIX}$"):
        parts = stored_hash.split("$", maxsplit=3)
        if len(parts) != 4:
            return False, False
        _, iterations_str, salt_hex, digest_hex = parts
        try:
            iterations = int(iterations_str)
            salt = binascii.unhexlify(salt_hex.encode("ascii"))
            expected = binascii.unhexlify(digest_hex.encode("ascii"))
        except (ValueError, binascii.Error):
            return False, False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected), False

    if _is_legacy_sha256_hash(stored_hash):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        is_valid = hmac.compare_digest(legacy, stored_hash)
        return is_valid, is_valid

    return False, False


class AuthService:
    """Сервис для аутентификации пользователей."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        """
        Аутентифицировать пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Данные пользователя или None
        """
        normalized_username = username.strip()
        query = "SELECT id, full_name, username, role, password_hash FROM users WHERE username = ?"
        with self.db.get_connection() as conn:
            row = conn.execute(query, (normalized_username,)).fetchone()

        if not row:
            return None

        is_valid, needs_upgrade = verify_password(row["password_hash"], password)
        if not is_valid:
            return None

        if needs_upgrade:
            self._upgrade_password_hash(int(row["id"]), password)

        row_username = str(row["username"]).strip().lower()
        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "username": row["username"],
            "role": DEMO_ROLE_BY_USERNAME.get(row_username, normalize_role(str(row["role"]))),
        }

    def _upgrade_password_hash(self, user_id: int, password: str) -> None:
        """
        Обновить хеш пароля пользователя.

        Args:
            user_id: ID пользователя
            password: Пароль в открытом виде
        """
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(password), user_id),
            )
            conn.commit()
