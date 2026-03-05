from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def show_info(parent: QWidget, title: str, message: str) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_error(parent: QWidget, title: str, message: str) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def ask_confirmation(parent: QWidget, title: str, message: str) -> bool:
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes
