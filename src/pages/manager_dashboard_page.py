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


class ManagerDashboardPage(QWidget):
    supports_add = False
    search_placeholder = "Поиск недоступен на панели менеджера"

    def __init__(self, bookings_service: BookingsService) -> None:
        super().__init__()
        self.bookings_service = bookings_service

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Панель менеджера")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Оперативная сводка за выбранную дату и активность по бронированиям.")
        subtitle.setObjectName("MutedText")

        filter_bar = QFrame()
        filter_bar.setObjectName("FilterBar")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        self.day_input = DateSelect(QDate.currentDate())
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setObjectName("GhostButton")
        refresh_btn.clicked.connect(self.refresh)

        self.day_hint = QLabel()
        self.day_hint.setObjectName("MutedText")

        filter_layout.addWidget(QLabel("Рабочая дата"))
        filter_layout.addWidget(self.day_input)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()
        filter_layout.addWidget(self.day_hint)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(10)
        cards_layout.setVerticalSpacing(10)

        self.total_card = StatCard("Бронирований за день", "purple")
        self.paid_card = StatCard("Оплачено за день", "cyan")
        self.conversion_card = StatCard("Конверсия оплат", "purple")
        self.revenue_card = StatCard("Выручка за день", "cyan")

        cards_layout.addWidget(self.total_card, 0, 0)
        cards_layout.addWidget(self.paid_card, 0, 1)
        cards_layout.addWidget(self.conversion_card, 1, 0)
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
        self.popular_table.setMinimumHeight(220)

        self.activity_table = QTableWidget(0, 5)
        self.activity_table.setObjectName("DataTable")
        self.activity_table.setHorizontalHeaderLabels(["Дата", "Клиент", "Тур", "Статус", "Сумма"])
        self.activity_table.setCornerButtonEnabled(False)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.activity_table.setMinimumHeight(220)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(filter_bar)
        root.addLayout(cards_layout)
        root.addWidget(QLabel("Популярные туры за день"))
        root.addWidget(self.popular_table)
        root.addWidget(QLabel("Последние бронирования за день"))
        root.addWidget(self.activity_table)

        self.day_input.dateChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        day = self.day_input.date().toString("yyyy-MM-dd")
        self.day_hint.setText(f"Дата: {day}")

        summary = self.bookings_service.daily_summary(day)
        total_count = int(summary["total_count"])
        paid_count = int(summary["paid_count"])

        self.total_card.set_value(str(total_count))
        self.paid_card.set_value(str(paid_count))
        if total_count > 0:
            conversion = f"{(paid_count / total_count) * 100:.1f}%"
        else:
            conversion = "0.0%"
        self.conversion_card.set_value(conversion)
        self.revenue_card.set_value(format_money(float(summary["paid_revenue"])))

        popular_rows = self.bookings_service.daily_popular_tours(day, limit=7)
        self.popular_table.setRowCount(len(popular_rows))
        if not popular_rows:
            self.popular_table.setRowCount(1)
            self.popular_table.setSpan(0, 0, 1, 5)
            empty_label = QLabel("Нет данных за выбранную дату")
            empty_label.setObjectName("EmptySubtitle")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.popular_table.setCellWidget(0, 0, empty_label)
        else:
            for row_idx, row in enumerate(popular_rows):
                values = [
                    row["tour_name"],
                    row["destination"],
                    str(row["bookings_count"]),
                    str(row["paid_count"]),
                    format_money(float(row["paid_revenue"])),
                ]
                for col_idx, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if col_idx >= 2:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.popular_table.setItem(row_idx, col_idx, item)

        activity_rows = self.bookings_service.list_bookings(date_from=day, date_to=day)[:7]
        self.activity_table.setRowCount(len(activity_rows))
        if not activity_rows:
            self.activity_table.setRowCount(1)
            self.activity_table.setSpan(0, 0, 1, 5)
            empty_label = QLabel("Бронирований за выбранную дату нет")
            empty_label.setObjectName("EmptySubtitle")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_table.setCellWidget(0, 0, empty_label)
        else:
            for row_idx, row in enumerate(activity_rows):
                values = [
                    row["booking_date"],
                    row["client_name"],
                    row["tour_name"],
                    row["status"],
                    format_money(float(row["amount"])),
                ]
                for col_idx, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if col_idx == 4:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.activity_table.setItem(row_idx, col_idx, item)

    def apply_global_search(self, _: str) -> None:
        return

    def handle_add(self) -> None:
        return
