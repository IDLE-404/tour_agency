"""
Утилиты форматирования и отображения сообщений.

Функции для:
- Форматирования денежных значений
- Показа информационных и ошибочных сообщений
- Запроса подтверждения действий
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def format_money(value: float) -> str:
    """
    Отформатировать денежное значение.

    Args:
        value: Числовое значение

    Returns:
        Строка вида "1 234 ₽"
    """
    return f"{value:,.0f} ₽".replace(",", " ")


def show_info(parent: QWidget, title: str, message: str) -> None:
    """
    Показать информационное сообщение.

    Args:
        parent: Родительское окно
        title: Заголовок сообщения
        message: Текст сообщения
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_error(parent: QWidget, title: str, message: str) -> None:
    """
    Показать сообщение об ошибке.

    Args:
        parent: Родительское окно
        title: Заголовок сообщения
        message: Текст ошибки
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def ask_confirmation(parent: QWidget, title: str, message: str) -> bool:
    """
    Запросить подтверждение действия.

    Args:
        parent: Родительское окно
        title: Заголовок диалога
        message: Текст подтверждения

    Returns:
        True если пользователь подтвердил, False иначе
    """
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes
