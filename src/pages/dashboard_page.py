from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from src.services.bookings_service import BookingsService
from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.ui.widgets import StatCard
from src.utils.formatters import format_money


class DashboardPage(QWidget):
    supports_add = False
    search_placeholder = "Поиск недоступен на панели"

    def __init__(
        self,
        clients_service: ClientsService,
        tours_service: ToursService,
        bookings_service: BookingsService,
        mode: str = "admin",
    ) -> None:
        super().__init__()
        self.clients_service = clients_service
        self.tours_service = tours_service
        self.bookings_service = bookings_service
        self.mode = mode

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(14)
        cards_layout.setVerticalSpacing(14)

        if self.mode == "manager":
            self.clients_card = StatCard("Бронирований за день", "purple")
            self.tours_card = StatCard("Оплачено за день", "cyan")
            self.bookings_card = StatCard("Отменено за день", "purple")
            self.revenue_card = StatCard("Выручка за день", "cyan")
        else:
            self.clients_card = StatCard("Клиентов", "purple")
            self.tours_card = StatCard("Туров", "cyan")
            self.bookings_card = StatCard("Бронирований", "purple")
            self.revenue_card = StatCard("Выручка (оплачено)", "cyan")

        cards_layout.addWidget(self.clients_card, 0, 0)
        cards_layout.addWidget(self.tours_card, 0, 1)
        cards_layout.addWidget(self.bookings_card, 1, 0)
        cards_layout.addWidget(self.revenue_card, 1, 1)

        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setObjectName("DataTable")
        if self.mode == "manager":
            self.recent_table.setHorizontalHeaderLabels(["Тур", "Направление", "Бронирований", "Оплачено", "Выручка"])
        else:
            self.recent_table.setHorizontalHeaderLabels(["Дата", "Клиент", "Тур", "Статус", "Сумма"])
        self.recent_table.setCornerButtonEnabled(False)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setAlternatingRowColors(False)
        self.recent_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.setMinimumHeight(260)

        layout.addLayout(cards_layout)
        layout.addWidget(self.recent_table)

        self.refresh()

    def refresh(self) -> None:
        if self.mode == "manager":
            day = date.today().isoformat()
            summary = self.bookings_service.daily_summary(day)
            self.clients_card.set_value(str(summary["total_count"]))
            self.tours_card.set_value(str(summary["paid_count"]))
            self.bookings_card.set_value(str(summary["canceled_count"]))
            self.revenue_card.set_value(format_money(float(summary["paid_revenue"])))
            rows = self.bookings_service.daily_popular_tours(day, limit=5)
        else:
            self.clients_card.set_value(str(self.clients_service.count()))
            self.tours_card.set_value(str(self.tours_service.count()))
            self.bookings_card.set_value(str(self.bookings_service.count()))
            self.revenue_card.set_value(format_money(self.bookings_service.paid_revenue()))
            rows = self.bookings_service.last_bookings(limit=5)

        self.recent_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            if self.mode == "manager":
                values = [
                    row["tour_name"],
                    row["destination"],
                    str(row["bookings_count"]),
                    str(row["paid_count"]),
                    format_money(float(row["paid_revenue"])),
                ]
            else:
                values = [
                    row["booking_date"],
                    row["client_name"],
                    row["tour_name"],
                    row["status"],
                    format_money(float(row["amount"])),
                ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if self.mode == "manager" and col_idx >= 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.recent_table.setItem(row_idx, col_idx, item)

    def apply_global_search(self, _: str) -> None:
        return

    def handle_add(self) -> None:
        return
