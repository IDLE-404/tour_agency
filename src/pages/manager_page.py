"""
Страница бронирований менеджера.

Предоставляет интерфейс для оформления бронирований туров клиентами.
"""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
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


class ManagerBookingsTab(QWidget):
    """Вкладка бронирования туров для менеджера."""

    data_changed = Signal()

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

        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """Инициализировать пользовательский интерфейс."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # Заголовок
        title = QLabel("Бронирование туров")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Выберите клиента и тур для оформления бронирования")
        subtitle.setObjectName("MutedText")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Форма бронирования
        form_bar = self._create_form_bar()
        root.addWidget(form_bar)

        # Таблица бронирований
        self.table = self._create_table()
        root.addWidget(self.table)

    def _create_form_bar(self) -> QFrame:
        """Создать панель формы бронирования."""
        form_bar = QFrame()
        form_bar.setObjectName("FilterBar")
        form_layout = QGridLayout(form_bar)
        form_layout.setContentsMargins(14, 12, 14, 12)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        # Клиент
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(250)
        self.client_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Тур
        self.tour_combo = QComboBox()
        self.tour_combo.setMinimumWidth(300)
        self.tour_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tour_combo.currentIndexChanged.connect(self._sync_amount_from_tour)

        # Дата
        self.booking_date = DateSelect(QDate.currentDate())
        self.booking_date.setFixedWidth(140)

        # Сумма
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 10_000_000)
        self.amount_input.setSingleStep(500)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setFixedWidth(150)

        # Кнопки
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setObjectName("GhostButton")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.setToolTip("Обновить списки")

        self.create_btn = QPushButton("Оформить бронирование")
        self.create_btn.setObjectName("PrimaryButton")
        self.create_btn.setEnabled(self.can_create)

        # Row 1
        form_layout.addWidget(QLabel("Клиент *"), 0, 0)
        form_layout.addWidget(self.client_combo, 0, 1)
        form_layout.addWidget(QLabel("Тур *"), 0, 2)
        form_layout.addWidget(self.tour_combo, 0, 3)

        # Row 2
        form_layout.addWidget(QLabel("Дата *"), 1, 0)
        form_layout.addWidget(self.booking_date, 1, 1)
        form_layout.addWidget(QLabel("Сумма *"), 1, 2)
        form_layout.addWidget(self.amount_input, 1, 3)
        form_layout.addWidget(self.refresh_btn, 1, 4)
        form_layout.addWidget(self.create_btn, 1, 5)

        form_layout.setColumnStretch(1, 3)
        form_layout.setColumnStretch(3, 4)

        self.refresh_btn.clicked.connect(self._reload_selectors)
        self.create_btn.clicked.connect(self._create_booking)

        return form_bar

    def _create_table(self) -> QTableWidget:
        """Создать таблицу бронирований."""
        table = QTableWidget(0, 7)
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels([
            "ID", "Клиент", "Тур", "Направление", "Дата", "Статус", "Сумма"
        ])
        table.setColumnHidden(0, True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setCornerButtonEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        table.setMinimumHeight(300)
        return table

    def _reload_selectors(self) -> None:
        """Обновить списки клиентов и туров."""
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
            free = tour.get("free_seats", 0)
            label = f"{tour['name']} — {tour['country']}, {tour['city']} (свободно: {free})"
            self.tour_combo.addItem(label, int(tour["id"]))
        if selected_tour is not None:
            idx = self.tour_combo.findData(selected_tour)
            if idx >= 0:
                self.tour_combo.setCurrentIndex(idx)
        self.tour_combo.blockSignals(False)
        self._sync_amount_from_tour()

    def _sync_amount_from_tour(self) -> None:
        """Синхронизировать сумму с ценой тура."""
        tour_id = self.tour_combo.currentData()
        if not tour_id:
            self.amount_input.setValue(0.0)
            return
        self.amount_input.setValue(self.bookings_service.tour_price(int(tour_id)))

    def _create_booking(self) -> None:
        """Создать бронирование."""
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
        """Обновить таблицу бронирований."""
        rows = self.bookings_service.list_bookings(search=self._search_text)
        self.table.setRowCount(max(len(rows), 1) if not rows else len(rows))

        if not rows:
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            empty = QLabel("Бронирований пока нет")
            empty.setObjectName("EmptySubtitle")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(0, 0, empty)
            return

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["client_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tour_name"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["destination"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["booking_date"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["status"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(format_money(float(row["amount"]))))
            self.table.setRowHeight(row_idx, 44)

    def refresh(self) -> None:
        """Обновить страницу."""
        self._reload_selectors()
        self._refresh_table()

    def apply_global_search(self, text: str) -> None:
        """Обработать глобальный поиск."""
        self._search_text = text
        self._refresh_table()


class ManagerPage(QWidget):
    """Единая страница менеджера с бронированиями."""

    data_changed = Signal()
    supports_add = False
    search_placeholder = "Поиск по бронированиям..."

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

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        self.bookings_tab = ManagerBookingsTab(
            bookings_service, clients_service, tours_service, can_create
        )

        root.addWidget(self.bookings_tab)

        self.bookings_tab.data_changed.connect(self.data_changed.emit)
        self.bookings_tab.refresh()

    def refresh(self) -> None:
        """Обновить страницу."""
        self.bookings_tab.refresh()

    def apply_global_search(self, text: str) -> None:
        """Обработать глобальный поиск."""
        self.bookings_tab.apply_global_search(text)

    def handle_add(self) -> None:
        """Обработать добавление (не используется)."""
        pass
