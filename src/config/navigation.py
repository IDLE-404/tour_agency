"""
Конфигурация навигации и страниц приложения.

Определяет индексы страниц, заголовки и настройки для каждой роли.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from src.utils.roles import ROLE_ADMIN, ROLE_GUEST, ROLE_MANAGER, ROLE_SELLER


@dataclass(frozen=True)
class PageConfig:
    """Конфигурация страницы приложения."""

    index: int
    title: str
    search_placeholder: str
    supports_add: bool
    search_enabled: bool


class PageIndex:
    """Индексы страниц приложения."""

    DASHBOARD: Final[int] = 0
    CLIENTS: Final[int] = 1
    TOURS: Final[int] = 2
    CONSULTATIONS: Final[int] = 3
    BOOKINGS: Final[int] = 4
    USERS: Final[int] = 5
    REPORTS: Final[int] = 6


# Конфигурация страниц для администратора
ADMIN_PAGES: Final[dict[int, PageConfig]] = {
    PageIndex.DASHBOARD: PageConfig(
        index=PageIndex.DASHBOARD,
        title="Панель",
        search_placeholder="Поиск недоступен на панели",
        supports_add=False,
        search_enabled=False,
    ),
    PageIndex.CLIENTS: PageConfig(
        index=PageIndex.CLIENTS,
        title="Клиенты",
        search_placeholder="Поиск клиентов по ФИО или телефону...",
        supports_add=True,
        search_enabled=True,
    ),
    PageIndex.TOURS: PageConfig(
        index=PageIndex.TOURS,
        title="Туры",
        search_placeholder="Поиск туров по названию/городу...",
        supports_add=True,
        search_enabled=True,
    ),
    PageIndex.CONSULTATIONS: PageConfig(
        index=PageIndex.CONSULTATIONS,
        title="Консультации",
        search_placeholder="Поиск консультаций...",
        supports_add=False,
        search_enabled=True,
    ),
    PageIndex.BOOKINGS: PageConfig(
        index=PageIndex.BOOKINGS,
        title="Регистрация продаж",
        search_placeholder="Поиск бронирований по клиенту, туру или телефону...",
        supports_add=False,
        search_enabled=True,
    ),
    PageIndex.USERS: PageConfig(
        index=PageIndex.USERS,
        title="Пользователи",
        search_placeholder="Поиск пользователей...",
        supports_add=True,
        search_enabled=True,
    ),
    PageIndex.REPORTS: PageConfig(
        index=PageIndex.REPORTS,
        title="Отчеты",
        search_placeholder="Поиск недоступен в отчетах",
        supports_add=False,
        search_enabled=False,
    ),
}

# Конфигурация страниц для менеджера
MANAGER_PAGES: Final[dict[int, PageConfig]] = {
    PageIndex.DASHBOARD: PageConfig(
        index=PageIndex.DASHBOARD,
        title="Бронирования",
        search_placeholder="Поиск по бронированиям...",
        supports_add=False,
        search_enabled=True,
    ),
    PageIndex.CLIENTS: PageConfig(
        index=PageIndex.CLIENTS,
        title="Клиенты",
        search_placeholder="Поиск клиентов по ФИО или телефону...",
        supports_add=True,
        search_enabled=True,
    ),
    PageIndex.TOURS: PageConfig(
        index=PageIndex.TOURS,
        title="Туры",
        search_placeholder="Поиск туров по названию/городу...",
        supports_add=True,
        search_enabled=True,
    ),
    PageIndex.CONSULTATIONS: PageConfig(
        index=PageIndex.CONSULTATIONS,
        title="Консультации",
        search_placeholder="Поиск консультаций...",
        supports_add=False,
        search_enabled=True,
    ),
}

# Конфигурация страниц для продавца
SELLER_PAGES: Final[dict[int, PageConfig]] = {
    PageIndex.TOURS: PageConfig(
        index=PageIndex.TOURS,
        title="Туры",
        search_placeholder="Поиск туров по названию/городу...",
        supports_add=False,
        search_enabled=True,
    ),
    PageIndex.CONSULTATIONS: PageConfig(
        index=PageIndex.CONSULTATIONS,
        title="Консультации",
        search_placeholder="Поиск консультаций...",
        supports_add=False,
        search_enabled=True,
    ),
    PageIndex.BOOKINGS: PageConfig(
        index=PageIndex.BOOKINGS,
        title="Регистрация продаж",
        search_placeholder="Поиск бронирований по клиенту, туру или телефону...",
        supports_add=False,
        search_enabled=True,
    ),
}

# Конфигурация страниц для гостя
GUEST_PAGES: Final[dict[int, PageConfig]] = {
    PageIndex.TOURS: PageConfig(
        index=PageIndex.TOURS,
        title="Туры",
        search_placeholder="Поиск туров по названию/городу...",
        supports_add=False,
        search_enabled=True,
    ),
}

# Видимые кнопки сайдбара для каждой роли
SIDEBAR_BUTTONS: Final[dict[str, list[str]]] = {
    ROLE_ADMIN: ["Панель", "Клиенты", "Туры", "Консультации", "Регистрация продаж", "Пользователи", "Отчеты"],
    ROLE_MANAGER: ["Бронирования", "Клиенты", "Туры", "Консультации"],
    ROLE_SELLER: ["Туры", "Консультации", "Регистрация продаж"],
    ROLE_GUEST: ["Туры"],
}


def get_page_config(role: str, index: int) -> PageConfig | None:
    """
    Получить конфигурацию страницы для роли и индекса.

    Args:
        role: Роль пользователя
        index: Индекс страницы

    Returns:
        Конфигурация страницы или None
    """
    pages_map = {
        ROLE_ADMIN: ADMIN_PAGES,
        ROLE_MANAGER: MANAGER_PAGES,
        ROLE_SELLER: SELLER_PAGES,
        ROLE_GUEST: GUEST_PAGES,
    }
    pages = pages_map.get(role, GUEST_PAGES)
    return pages.get(index)


def get_allowed_indexes(role: str) -> list[int]:
    """
    Получить список разрешённых индексов для роли.

    Args:
        role: Роль пользователя

    Returns:
        Список разрешённых индексов
    """
    pages_map = {
        ROLE_ADMIN: ADMIN_PAGES,
        ROLE_MANAGER: MANAGER_PAGES,
        ROLE_SELLER: SELLER_PAGES,
        ROLE_GUEST: GUEST_PAGES,
    }
    pages = pages_map.get(role, GUEST_PAGES)
    return sorted(pages.keys())


def get_default_page_index(role: str) -> int:
    """
    Получить индекс страницы по умолчанию для роли.

    Args:
        role: Роль пользователя

    Returns:
        Индекс страницы по умолчанию
    """
    allowed = get_allowed_indexes(role)
    return allowed[0] if allowed else PageIndex.TOURS
