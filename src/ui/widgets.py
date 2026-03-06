"""
Виджеты общего назначения.

Содержит переиспользуемые UI компоненты:
- SidebarButton: кнопка навигации в сайдбаре
- DateSelect: выбор даты с календарём
- StatCard: карточка статистики
"""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SidebarButton(QPushButton):
    """Кнопка навигации в боковой панели."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)


class DateSelect(QDateEdit):
    """Поле выбора даты с всплывающим календарём."""

    def __init__(
        self,
        date: QDate | None = None,
        width: int | None = 138,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setDate(date or QDate.currentDate())
        if width is not None:
            self.setFixedWidth(width)


class StatCard(QFrame):
    """Карточка для отображения статистики."""

    def __init__(self, title: str, accent: str = "purple", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setProperty("accent", accent)
        self.setMinimumSize(200, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatCardTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("StatCardValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        """Установить значение статистики."""
        self.value_label.setText(value)
