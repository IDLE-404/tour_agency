from __future__ import annotations

import sqlite3
from typing import Any

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
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

from src.services.bookings_service import ALLOWED_STATUSES, BookingsService
from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.ui.widgets import DateSelect
from src.utils.formatters import ask_confirmation, format_money, show_error, show_info


class BookingDialog(QDialog):
    def __init__(
        self,
        clients_service: ClientsService,
        tours_service: ToursService,
        bookings_service: BookingsService,
        parent: QWidget | None = None,
        data: dict[str, Any] | None = None,
        preselected_tour_id: int | None = None,
        preselected_client_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редактирование продажи" if data else "Регистрация продажи")
        self.setMinimumWidth(460)

        self.clients_service = clients_service
        self.tours_service = tours_service
        self.bookings_service = bookings_service

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.client_combo = QComboBox()
        self.tour_combo = QComboBox()
        self.booking_date = DateSelect(QDate.currentDate(), width=None)

        self.status_combo = QComboBox()
        self.status_combo.addItems(ALLOWED_STATUSES)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 10_000_000)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setSingleStep(500)

        clients = self.clients_service.list_client_choices()
        for client in clients:
            label = f"{client['full_name']} ({client['phone']})"
            self.client_combo.addItem(label, client["id"])

        tours = self.tours_service.list_tour_choices()
        for tour in tours:
            label = (
                f"{tour['name']} - {tour['country']}, {tour['city']} "
                f"(свободно: {tour.get('free_seats', 0)})"
            )
            self.tour_combo.addItem(label, tour["id"])

        self.tour_combo.currentIndexChanged.connect(self._sync_amount_with_tour)

        form.addRow("Клиент *", self.client_combo)
        form.addRow("Тур *", self.tour_combo)
        form.addRow("Дата *", self.booking_date)
        form.addRow("Статус *", self.status_combo)
        form.addRow("Сумма *", self.amount_input)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        root.addLayout(form)
        root.addLayout(btns)

        if self.tour_combo.count() > 0:
            self._sync_amount_with_tour()

        if data:
            self._apply_data(data)
        else:
            if preselected_tour_id is not None:
                tour_index = self.tour_combo.findData(preselected_tour_id)
                if tour_index >= 0:
                    self.tour_combo.setCurrentIndex(tour_index)
            if preselected_client_id is not None:
                client_index = self.client_combo.findData(preselected_client_id)
                if client_index >= 0:
                    self.client_combo.setCurrentIndex(client_index)

    def _apply_data(self, data: dict[str, Any]) -> None:
        client_index = self.client_combo.findData(data.get("client_id"))
        if client_index >= 0:
            self.client_combo.setCurrentIndex(client_index)

        tour_index = self.tour_combo.findData(data.get("tour_id"))
        if tour_index >= 0:
            self.tour_combo.setCurrentIndex(tour_index)

        self.booking_date.setDate(QDate.fromString(data["booking_date"], "yyyy-MM-dd"))

        status_index = self.status_combo.findText(data["status"])
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

        self.amount_input.setValue(float(data.get("amount", 0)))

    def _sync_amount_with_tour(self) -> None:
        tour_id = self.tour_combo.currentData()
        if not tour_id:
            return
        price = self.bookings_service.tour_price(int(tour_id))
        self.amount_input.setValue(price)

    def payload(self) -> dict[str, Any]:
        return {
            "client_id": self.client_combo.currentData(),
            "tour_id": self.tour_combo.currentData(),
            "booking_date": self.booking_date.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "amount": self.amount_input.value(),
        }


class BookingsPage(QWidget):
    data_changed = Signal()
    supports_add = False
    search_placeholder = "Поиск продаж по клиенту, телефону или туру..."

    def __init__(
        self,
        bookings_service: BookingsService,
        clients_service: ClientsService,
        tours_service: ToursService,
        can_create: bool = True,
        can_edit: bool = True,
        can_delete: bool = True,
        can_export: bool = True,
    ) -> None:
        super().__init__()
        self.bookings_service = bookings_service
        self.clients_service = clients_service
        self.tours_service = tours_service
        self.can_create = can_create
        self.can_edit = can_edit
        self.can_delete = can_delete
        self.can_export = can_export
        self.supports_add = False

        self._search_text = ""

        self.status_filter_value = ""
        self.date_from_value: str | None = None
        self.date_to_value: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Регистрация продаж")
        title.setObjectName("PageTitle")

        filter_bar = QFrame()
        filter_bar.setObjectName("FilterBar")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(8)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", "")
        for status in ALLOWED_STATUSES:
            self.status_filter.addItem(status, status)

        self.use_date_from = QCheckBox("Дата с")
        self.date_from = DateSelect(QDate.currentDate().addMonths(-1))
        self.date_from.setEnabled(False)
        self.use_date_from.toggled.connect(self.date_from.setEnabled)

        self.use_date_to = QCheckBox("Дата по")
        self.date_to = DateSelect(QDate.currentDate())
        self.date_to.setEnabled(False)
        self.use_date_to.toggled.connect(self.date_to.setEnabled)

        apply_btn = QPushButton("Применить")
        apply_btn.setObjectName("GhostButton")
        reset_btn = QPushButton("Сброс")
        reset_btn.setObjectName("GhostButton")
        register_sale_btn = QPushButton("Регистрация продажи")
        register_sale_btn.setObjectName("PrimaryButton")
        register_sale_btn.setVisible(self.can_create)
        export_btn = QPushButton("Экспорт CSV")
        export_btn.setObjectName("GhostButton")
        export_btn.setVisible(self.can_export)

        apply_btn.clicked.connect(self.apply_filters)
        reset_btn.clicked.connect(self.reset_filters)
        register_sale_btn.clicked.connect(self.handle_add)
        export_btn.clicked.connect(self.export_csv)

        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.use_date_from)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.use_date_to)
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(apply_btn)
        filter_layout.addWidget(reset_btn)
        filter_layout.addStretch()
        filter_layout.addWidget(register_sale_btn)
        filter_layout.addWidget(export_btn)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Клиент", "Тур", "Направление", "Дата", "Статус", "Сумма", "Действия"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setCornerButtonEnabled(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        if not (self.can_edit or self.can_delete):
            self.table.setColumnHidden(7, True)

        root.addWidget(title)
        root.addWidget(filter_bar)
        root.addWidget(self.table)

        self.refresh()

    def apply_filters(self) -> None:
        self.status_filter_value = self.status_filter.currentData() or ""
        self.date_from_value = (
            self.date_from.date().toString("yyyy-MM-dd") if self.use_date_from.isChecked() else None
        )
        self.date_to_value = self.date_to.date().toString("yyyy-MM-dd") if self.use_date_to.isChecked() else None
        self.refresh()

    def reset_filters(self) -> None:
        self.status_filter.setCurrentIndex(0)
        self.use_date_from.setChecked(False)
        self.use_date_to.setChecked(False)
        self.status_filter_value = ""
        self.date_from_value = None
        self.date_to_value = None
        self.refresh()

    def refresh(self) -> None:
        rows = self.bookings_service.list_bookings(
            search=self._search_text,
            status=self.status_filter_value,
            date_from=self.date_from_value,
            date_to=self.date_to_value,
        )
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["client_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tour_name"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["destination"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["booking_date"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["status"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(format_money(float(row["amount"]))))
            if self.can_edit or self.can_delete:
                self.table.setCellWidget(row_idx, 7, self._actions_widget(row))
            self.table.setRowHeight(row_idx, 52)

    def _actions_widget(self, row: dict[str, Any]) -> QWidget:
        container = QWidget()
        container.setObjectName("ActionCell")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.can_edit:
            edit_btn = QPushButton("Изменить")
            edit_btn.setObjectName("GhostButton")
            edit_btn.setMinimumWidth(86)
            edit_btn.setFixedHeight(28)
            edit_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            edit_btn.clicked.connect(lambda: self._edit_booking(row))
            layout.addWidget(edit_btn)

        if self.can_delete:
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("DangerButton")
            delete_btn.setMinimumWidth(86)
            delete_btn.setFixedHeight(28)
            delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            delete_btn.clicked.connect(lambda: self._delete_booking(row["id"]))
            layout.addWidget(delete_btn)
        return container

    def _edit_booking(self, row: dict[str, Any]) -> None:
        if not self.can_edit:
            return
        dialog = BookingDialog(
            clients_service=self.clients_service,
            tours_service=self.tours_service,
            bookings_service=self.bookings_service,
            parent=self,
            data=row,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.bookings_service.update_booking(row["id"], dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Сохранено", "Бронирование обновлено.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def _delete_booking(self, booking_id: int) -> None:
        if not self.can_delete:
            return
        if not ask_confirmation(self, "Подтверждение", "Удалить выбранное бронирование?"):
            return

        self.bookings_service.delete_booking(booking_id)
        self.refresh()
        self.data_changed.emit()
        show_info(self, "Удалено", "Бронирование удалено.")

    def handle_add(
        self,
        preselected_tour_id: int | None = None,
        preselected_client_id: int | None = None,
    ) -> None:
        if not self.can_create:
            return
        if not self.clients_service.list_client_choices() or not self.tours_service.list_tour_choices():
            show_error(self, "Недостаточно данных", "Сначала добавьте хотя бы одного клиента и тур.")
            return

        dialog = BookingDialog(
            clients_service=self.clients_service,
            tours_service=self.tours_service,
            bookings_service=self.bookings_service,
            parent=self,
            preselected_tour_id=preselected_tour_id,
            preselected_client_id=preselected_client_id,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.bookings_service.create_booking(dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Готово", "Продажа зарегистрирована.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            show_error(self, "Ошибка", str(exc))

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self.refresh()

    def export_csv(self) -> None:
        if not self.can_export:
            return
        rows = self.bookings_service.list_bookings(
            search=self._search_text,
            status=self.status_filter_value,
            date_from=self.date_from_value,
            date_to=self.date_to_value,
        )
        if not rows:
            show_info(self, "Экспорт", "Нет данных для экспорта.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            "bookings_export.csv",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        self.bookings_service.export_to_csv(file_path, rows)
        show_info(self, "Экспорт", "CSV-файл успешно сохранен.")
