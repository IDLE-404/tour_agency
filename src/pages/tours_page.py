from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.tours_service import ToursService
from src.utils.formatters import ask_confirmation, format_money, show_error, show_info


class TourDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, data: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Тур")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.country_input = QLineEdit()
        self.city_input = QLineEdit()

        self.date_from_input = QDateEdit()
        self.date_from_input.setCalendarPopup(True)
        self.date_from_input.setDisplayFormat("yyyy-MM-dd")
        self.date_from_input.setDate(QDate.currentDate())

        self.date_to_input = QDateEdit()
        self.date_to_input.setCalendarPopup(True)
        self.date_to_input.setDisplayFormat("yyyy-MM-dd")
        self.date_to_input.setDate(QDate.currentDate().addDays(7))

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10_000_000)
        self.price_input.setSingleStep(1000)
        self.price_input.setSuffix(" ₽")

        self.seats_input = QSpinBox()
        self.seats_input.setRange(0, 10000)

        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(100)

        form.addRow("Название *", self.name_input)
        form.addRow("Страна *", self.country_input)
        form.addRow("Город *", self.city_input)
        form.addRow("Дата с *", self.date_from_input)
        form.addRow("Дата по *", self.date_to_input)
        form.addRow("Цена *", self.price_input)
        form.addRow("Мест *", self.seats_input)
        form.addRow("Описание", self.description_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        root.addLayout(form)
        root.addLayout(btn_layout)

        if data:
            self.name_input.setText(data.get("name", ""))
            self.country_input.setText(data.get("country", ""))
            self.city_input.setText(data.get("city", ""))
            self.date_from_input.setDate(QDate.fromString(data["date_from"], "yyyy-MM-dd"))
            self.date_to_input.setDate(QDate.fromString(data["date_to"], "yyyy-MM-dd"))
            self.price_input.setValue(float(data.get("price", 0)))
            self.seats_input.setValue(int(data.get("seats", 0)))
            self.description_input.setText(data.get("description") or "")

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name_input.text(),
            "country": self.country_input.text(),
            "city": self.city_input.text(),
            "date_from": self.date_from_input.date().toString("yyyy-MM-dd"),
            "date_to": self.date_to_input.date().toString("yyyy-MM-dd"),
            "price": self.price_input.value(),
            "seats": self.seats_input.value(),
            "description": self.description_input.toPlainText(),
        }


class ToursPage(QWidget):
    data_changed = Signal()
    supports_add = True
    search_placeholder = "Поиск туров по названию/городу..."

    def __init__(self, service: ToursService) -> None:
        super().__init__()
        self.service = service
        self._search_text = ""

        self.country_filter_value = ""
        self.min_price_value: float | None = None
        self.max_price_value: float | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Каталог туров")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        filters = QFrame()
        filters.setObjectName("FilterBar")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(12, 10, 12, 10)
        filters_layout.setSpacing(8)

        self.country_filter = QLineEdit()
        self.country_filter.setPlaceholderText("Страна")

        self.min_price_filter = QDoubleSpinBox()
        self.min_price_filter.setRange(0, 10_000_000)
        self.min_price_filter.setPrefix("от ")
        self.min_price_filter.setSuffix(" ₽")
        self.min_price_filter.setSpecialValueText("от: любая")

        self.max_price_filter = QDoubleSpinBox()
        self.max_price_filter.setRange(0, 10_000_000)
        self.max_price_filter.setPrefix("до ")
        self.max_price_filter.setSuffix(" ₽")
        self.max_price_filter.setSpecialValueText("до: любая")

        apply_btn = QPushButton("Применить")
        apply_btn.setObjectName("GhostButton")
        reset_btn = QPushButton("Сброс")
        reset_btn.setObjectName("GhostButton")

        apply_btn.clicked.connect(self.apply_filters)
        reset_btn.clicked.connect(self.reset_filters)

        filters_layout.addWidget(self.country_filter)
        filters_layout.addWidget(self.min_price_filter)
        filters_layout.addWidget(self.max_price_filter)
        filters_layout.addWidget(apply_btn)
        filters_layout.addWidget(reset_btn)
        filters_layout.addStretch()

        self.table = QTableWidget(0, 9)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название", "Страна", "Город", "С", "По", "Цена", "Мест", "Действия"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(filters)
        root.addWidget(self.table)

        self.refresh()

    def apply_filters(self) -> None:
        self.country_filter_value = self.country_filter.text().strip()
        self.min_price_value = self.min_price_filter.value() if self.min_price_filter.value() > 0 else None
        self.max_price_value = self.max_price_filter.value() if self.max_price_filter.value() > 0 else None
        self.refresh()

    def reset_filters(self) -> None:
        self.country_filter.clear()
        self.min_price_filter.setValue(0)
        self.max_price_filter.setValue(0)
        self.country_filter_value = ""
        self.min_price_value = None
        self.max_price_value = None
        self.refresh()

    def refresh(self) -> None:
        rows = self.service.list_tours(
            search=self._search_text,
            country=self.country_filter_value,
            min_price=self.min_price_value,
            max_price=self.max_price_value,
        )
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["country"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["city"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["date_from"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["date_to"]))
            self.table.setItem(row_idx, 6, QTableWidgetItem(format_money(float(row["price"]))))
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(row["seats"])))
            self.table.setCellWidget(row_idx, 8, self._actions_widget(row))
            self.table.setRowHeight(row_idx, 40)

    def _actions_widget(self, row: dict[str, Any]) -> QWidget:
        container = QFrame()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        edit_btn = QPushButton("Изменить")
        edit_btn.setObjectName("GhostButton")
        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("DangerButton")

        edit_btn.clicked.connect(lambda: self._edit_tour(row))
        delete_btn.clicked.connect(lambda: self._delete_tour(row["id"]))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        return container

    def _delete_tour(self, tour_id: int) -> None:
        if not ask_confirmation(self, "Подтверждение", "Удалить выбранный тур?"):
            return
        try:
            self.service.delete_tour(tour_id)
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Удалено", "Тур удален.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def _edit_tour(self, row: dict[str, Any]) -> None:
        dialog = TourDialog(self, row)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.update_tour(row["id"], dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Сохранено", "Тур обновлен.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def handle_add(self) -> None:
        dialog = TourDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.service.create_tour(dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Готово", "Тур добавлен.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self.refresh()
