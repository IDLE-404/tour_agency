"""
Модуль управления ролями и разрешениями.

Определяет роли пользователей и их права доступа к функциям приложения.

Роли:
    - Admin: полный доступ ко всем функциям
    - Manager: управление клиентами, турами и бронированиями
    - Seller: просмотр туров и регистрация продаж
    - Guest: только просмотр туров
"""

from __future__ import annotations

from typing import Final


ROLE_ADMIN: Final[str] = "admin"
ROLE_MANAGER: Final[str] = "manager"
ROLE_SELLER: Final[str] = "seller"
ROLE_GUEST: Final[str] = "guest"

ROLE_CHOICES: Final[tuple[str, ...]] = (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_SELLER,
    ROLE_GUEST,
)

ROLE_LABELS: Final[dict[str, str]] = {
    ROLE_ADMIN: "Администратор",
    ROLE_MANAGER: "Менеджер",
    ROLE_SELLER: "Продавец",
    ROLE_GUEST: "Гость",
}

_ROLE_PERMISSIONS: Final[dict[str, set[str]]] = {
    ROLE_ADMIN: {
        "dashboard.view",
        "clients.view",
        "clients.create",
        "clients.edit",
        "clients.delete",
        "tours.view",
        "tours.create",
        "tours.edit",
        "tours.delete",
        "consultations.view",
        "manager_bookings.view",
        "manager_bookings.create",
        "bookings.view",
        "bookings.create",
        "bookings.edit",
        "bookings.delete",
        "bookings.export",
        "users.view",
        "users.create",
        "users.edit",
        "users.delete",
        "reports.view",
    },
    ROLE_MANAGER: {
        "dashboard.view",
        "clients.view",
        "clients.create",
        "clients.edit",
        "tours.view",
        "tours.edit",
        "consultations.view",
        "manager_bookings.view",
        "manager_bookings.create",
    },
    ROLE_SELLER: {
        "tours.view",
        "consultations.view",
        "bookings.view",
        "bookings.create",
        "bookings.edit",
    },
    ROLE_GUEST: {
        "tours.view",
    },
}


def normalize_role(role: str) -> str:
    """
    Нормализовать роль пользователя.

    Args:
        role: Исходная строка роли

    Returns:
        Нормализованная роль или ROLE_GUEST
    """
    role = role.strip().lower()
    return role if role in ROLE_CHOICES else ROLE_GUEST


def role_label(role: str) -> str:
    """
    Получить человеко-читаемое название роли.

    Args:
        role: Роль пользователя

    Returns:
        Название роли на русском языке
    """
    return ROLE_LABELS.get(normalize_role(role), "Гость")


def has_permission(role: str, permission: str) -> bool:
    """
    Проверить наличие разрешения у роли.

    Args:
        role: Роль пользователя
        permission: Имя разрешения (например, "clients.create")

    Returns:
        True если разрешение есть, False иначе
    """
    current_role = normalize_role(role)
    return permission in _ROLE_PERMISSIONS.get(current_role, set())
