"""
Модуль валидации данных.

Функции для проверки:
- Обязательных полей
- Телефонов и email
- Числовых значений
"""

from __future__ import annotations

import re

PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def required(value: str) -> bool:
    """
    Проверить, что поле заполнено.

    Args:
        value: Проверяемое значение

    Returns:
        True если значение не пустое
    """
    return bool(value and value.strip())


def valid_phone(phone: str) -> bool:
    """
    Проверить корректность номера телефона.

    Args:
        phone: Номер телефона

    Returns:
        True если номер валиден
    """
    return bool(PHONE_PATTERN.match(phone.strip()))


def valid_email(email: str) -> bool:
    """
    Проверить корректность email.

    Args:
        email: Email адрес

    Returns:
        True если email валиден или пуст
    """
    if not email.strip():
        return True
    return bool(EMAIL_PATTERN.match(email.strip()))


def non_negative_number(value: float) -> bool:
    """
    Проверить, что число неотрицательное.

    Args:
        value: Число для проверки

    Returns:
        True если число >= 0
    """
    return value >= 0
