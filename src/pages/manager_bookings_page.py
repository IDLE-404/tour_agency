from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.bookings_service import BookingsService
from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.ui.widgets import DateSelect
from src.utils.formatters import format_money, show_error, show_info


class ManagerBookingsPage(QWidget):
    data_changed = Signal()
    supports_add = False
    search_placeholder = "Поиск бронирований по клиенту, туру или телефону..."

    def __init__(
        self,
        bookings_service: BookingsService,
        clients_service: ClientsService,
        tours_service: ToursService,
        can_create: bool = True,
    ) -> None:
        super().__init__()
        self.bookings_service = bookings_service
        self.clients_service = clients_service
        self.tours_service = tours_service
        self.can_create = can_create
        self._search_text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Бронирование туров для клиентов")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Отдельный рабочий экран менеджера: клиент -> тур -> оформление бронирования.")
        subtitle.setObjectName("MutedText")

        form_bar = QFrame()
        form_bar.setObjectName("FilterBar")
        form_layout = QGridLayout(form_bar)
        form_layout.setContentsMargins(12, 10, 12, 10)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(8)

        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(220)

        self.tour_combo = QComboBox()
        self.tour_combo.setMinimumWidth(280)
        self.tour_combo.currentIndexChanged.connect(self._sync_amount_from_tour)

        self.booking_date = DateSelect(QDate.currentDate())

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 10_000_000)
        self.amount_input.setSingleStep(500)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setFixedWidth(140)

        refresh_btn = QPushButton("Обновить списки")
        refresh_btn.setObjectName("GhostButton")
        refresh_btn.clicked.connect(self._reload_selectors)

        create_btn = QPushButton("Оформить бронирование")
        create_btn.setObjectName("PrimaryButton")
        create_btn.setEnabled(self.can_create)
        create_btn.clicked.connect(self._create_booking)

        # Row 1: client + tour selectors
        form_layout.addWidget(QLabel("Клиент"), 0, 0)
        form_layout.addWidget(self.client_combo, 0, 1)
        form_layout.addWidget(QLabel("Тур"), 0, 2)
        form_layout.addWidget(self.tour_combo, 0, 3)

        # Row 2: date + amount + actions
        form_layout.addWidget(QLabel("Дата"), 1, 0)
        form_layout.addWidget(self.booking_date, 1, 1)
        form_layout.addWidget(QLabel("Сумма"), 1, 2)
        form_layout.addWidget(self.amount_input, 1, 3)
        form_layout.addWidget(refresh_btn, 1, 4)
        form_layout.addWidget(create_btn, 1, 5)

        form_layout.setColumnStretch(1, 2)
        form_layout.setColumnStretch(3, 3)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Клиент", "Тур", "Направление", "Дата", "Статус", "Сумма"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(form_bar)
        root.addWidget(self.table)

        self.refresh()

    def _reload_selectors(self) -> None:
        selected_client = self.client_combo.currentData()
        selected_tour = self.tour_combo.currentData()

        self.client_combo.blockSignals(True)
        self.client_combo.clear()
        for client in self.clients_service.list_client_choices():
            label = f"{client['full_name']} ({client['phone']})"
            self.client_combo.addItem(label, int(client["id"]))
        if selected_client is not None:
            idx = self.client_combo.findData(selected_client)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)
        self.client_combo.blockSignals(False)

        self.tour_combo.blockSignals(True)
        self.tour_combo.clear()
        for tour in self.tours_service.list_tour_choices():
            label = (
                f"{tour['name']} - {tour['country']}, {tour['city']} "
                f"(свободно: {tour.get('free_seats', 0)})"
            )
            self.tour_combo.addItem(label, int(tour["id"]))
        if selected_tour is not None:
            idx = self.tour_combo.findData(selected_tour)
            if idx >= 0:
                self.tour_combo.setCurrentIndex(idx)
        self.tour_combo.blockSignals(False)
        self._sync_amount_from_tour()

    def _sync_amount_from_tour(self) -> None:
        tour_id = self.tour_combo.currentData()
        if not tour_id:
            self.amount_input.setValue(0.0)
            return
        self.amount_input.setValue(self.bookings_service.tour_price(int(tour_id)))

    def _create_booking(self) -> None:
        if not self.can_create:
            return
        client_id = self.client_combo.currentData()
        tour_id = self.tour_combo.currentData()
        if not client_id:
            show_error(self, "Бронирование", "Выберите клиента.")
            return
        if not tour_id:
            show_error(self, "Бронирование", "Выберите тур.")
            return

        payload = {
            "client_id": int(client_id),
            "tour_id": int(tour_id),
            "booking_date": self.booking_date.date().toString("yyyy-MM-dd"),
            "status": "новое",
            "amount": float(self.amount_input.value()),
        }
        try:
            self.bookings_service.create_booking(payload)
            self._reload_selectors()
            self._refresh_table()
            self.data_changed.emit()
            show_info(self, "Готово", "Бронирование успешно оформлено.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def _refresh_table(self) -> None:
        rows = self.bookings_service.list_bookings(search=self._search_text)
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["client_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tour_name"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["destination"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["booking_date"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["status"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(format_money(float(row["amount"]))))
            self.table.setRowHeight(row_idx, 46)

    def refresh(self) -> None:
        self._reload_selectors()
        self._refresh_table()

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self._refresh_table()

    def handle_add(self) -> None:
        return
