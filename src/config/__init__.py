"""Конфигурация приложения."""

from src.config.navigation import (
    ADMIN_PAGES,
    GUEST_PAGES,
    MANAGER_PAGES,
    SELLER_PAGES,
    PageConfig,
    PageIndex,
    get_allowed_indexes,
    get_default_page_index,
    get_page_config,
)

__all__ = [
    "ADMIN_PAGES",
    "GUEST_PAGES",
    "MANAGER_PAGES",
    "SELLER_PAGES",
    "PageConfig",
    "PageIndex",
    "get_allowed_indexes",
    "get_default_page_index",
    "get_page_config",
]
