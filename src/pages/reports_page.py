from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.bookings_service import BookingsService
from src.ui.widgets import DateSelect, StatCard
from src.utils.formatters import format_money


class ReportsPage(QWidget):
    supports_add = False
    search_placeholder = "Поиск недоступен в отчетах"

    def __init__(self, bookings_service: BookingsService) -> None:
        super().__init__()
        self.bookings_service = bookings_service

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Отчеты по бронированиям")
        title.setObjectName("PageTitle")

        filter_bar = QFrame()
        filter_bar.setObjectName("FilterBar")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        day_label = QLabel("Дата отчета")
        day_label.setObjectName("MutedText")

        self.day_input = DateSelect(QDate.currentDate())

        refresh_btn = QPushButton("Сформировать")
        refresh_btn.setObjectName("GhostButton")
        refresh_btn.clicked.connect(self.refresh)

        self.day_hint = QLabel()
        self.day_hint.setObjectName("MutedText")

        filter_layout.addWidget(day_label)
        filter_layout.addWidget(self.day_input)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()
        filter_layout.addWidget(self.day_hint)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(10)
        cards_layout.setVerticalSpacing(10)

        self.total_card = StatCard("Бронирований за день", "purple")
        self.paid_card = StatCard("Оплачено", "cyan")
        self.canceled_card = StatCard("Отменено", "purple")
        self.revenue_card = StatCard("Выручка за день", "cyan")

        cards_layout.addWidget(self.total_card, 0, 0)
        cards_layout.addWidget(self.paid_card, 0, 1)
        cards_layout.addWidget(self.canceled_card, 1, 0)
        cards_layout.addWidget(self.revenue_card, 1, 1)

        self.popular_table = QTableWidget(0, 5)
        self.popular_table.setObjectName("DataTable")
        self.popular_table.setHorizontalHeaderLabels(
            ["Тур", "Направление", "Бронирований", "Оплачено", "Выручка"]
        )
        self.popular_table.setCornerButtonEnabled(False)
        self.popular_table.verticalHeader().setVisible(False)
        self.popular_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.popular_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.popular_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.popular_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.popular_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.popular_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.popular_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.popular_table.setMinimumHeight(260)

        root.addWidget(title)
        root.addWidget(filter_bar)
        root.addLayout(cards_layout)
        root.addWidget(self.popular_table)

        self.day_input.dateChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        day = self.day_input.date().toString("yyyy-MM-dd")
        self.day_hint.setText(f"Статистика за: {day}")

        summary = self.bookings_service.daily_summary(day)
        self.total_card.set_value(str(summary["total_count"]))
        self.paid_card.set_value(str(summary["paid_count"]))
        self.canceled_card.set_value(str(summary["canceled_count"]))
        self.revenue_card.set_value(format_money(float(summary["paid_revenue"])))

        rows = self.bookings_service.daily_popular_tours(day, limit=10)
        self.popular_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            values = [
                row["tour_name"],
                row["destination"],
                str(row["bookings_count"]),
                str(row["paid_count"]),
                format_money(float(row["paid_revenue"])),
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_idx >= 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.popular_table.setItem(row_idx, col_idx, item)

            self.popular_table.setRowHeight(row_idx, 42)

    def apply_global_search(self, _: str) -> None:
        return

    def handle_add(self) -> None:
        return
