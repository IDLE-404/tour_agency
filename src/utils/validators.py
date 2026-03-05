from __future__ import annotations

import re


PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def required(value: str) -> bool:
    return bool(value and value.strip())


def valid_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone.strip()))


def valid_email(email: str) -> bool:
    if not email.strip():
        return True
    return bool(EMAIL_PATTERN.match(email.strip()))


def non_negative_number(value: float) -> bool:
    return value >= 0
