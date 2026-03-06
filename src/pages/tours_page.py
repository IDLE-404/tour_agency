"""
Страница управления турами.

Отображает список туров с фильтрами, позволяет создавать,
редактировать, удалять туры и консультировать клиентов.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.ui.widgets import DateSelect
from src.utils.formatters import ask_confirmation, format_money, show_error, show_info
from src.pages.tours_dialogs import TourDialog, TourDetailsDialog, ConsultationDialog


class ToursPage(QWidget):
    """Страница просмотра и управления турами."""

    data_changed = Signal()
    register_sale_requested = Signal(int, int)
    supports_add = True
    search_placeholder = "Поиск туров по названию/городу..."

    def __init__(
        self,
        service: ToursService,
        clients_service: ClientsService | None = None,
        can_create: bool = True,
        can_edit: bool = True,
        can_delete: bool = True,
        can_consult: bool = False,
        can_register_sale: bool = False,
    ) -> None:
        super().__init__()
        self.service = service
        self.clients_service = clients_service
        self.can_create = can_create
        self.can_edit = can_edit
        self.can_delete = can_delete
        self.can_consult = can_consult
        self.can_register_sale = can_register_sale
        self.supports_add = self.can_create
        self._search_text = ""
        self._rows: list[dict[str, Any]] = []

        self.country_filter_value = ""
        self.min_price_value: float | None = None
        self.max_price_value: float | None = None
        self.date_from_value: str | None = None
        self.date_to_value: str | None = None

        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        """Инициализировать пользовательский интерфейс."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Заголовок и подсказка
        title = QLabel("Туры и свободные места")
        title.setObjectName("PageTitle")
        hint_text = "Двойной клик по туру открывает карточку."
        if self.can_consult:
            hint_text = "Выберите тур и нажмите 'Консультация' или откройте карточку двойным кликом."
        hint = QLabel(hint_text)
        hint.setObjectName("MutedText")
        root.addWidget(title)
        root.addWidget(hint)

        # Кнопки действий
        actions_bar = self._create_actions_bar()
        root.addWidget(actions_bar)

        # Фильтры
        filters = self._create_filters()
        root.addWidget(filters)

        # Таблица
        self.table = self._create_table()
        root.addWidget(self.table)

    def _create_actions_bar(self) -> QFrame:
        """Создать панель действий."""
        actions_bar = QFrame()
        actions_bar.setObjectName("FilterBar")
        actions_layout = QHBoxLayout(actions_bar)
        actions_layout.setContentsMargins(12, 10, 12, 10)
        actions_layout.setSpacing(8)

        self.consult_btn = QPushButton("Консультация")
        self.consult_btn.setObjectName("GhostButton")
        self.consult_btn.setVisible(self.can_consult)
        self.consult_btn.clicked.connect(self._consult_selected_tour)

        self.register_sale_btn = QPushButton("Регистрация продажи")
        self.register_sale_btn.setObjectName("PrimaryButton")
        self.register_sale_btn.setVisible(self.can_register_sale)
        self.register_sale_btn.clicked.connect(self._register_sale_for_selected_tour)

        actions_layout.addWidget(self.consult_btn)
        actions_layout.addWidget(self.register_sale_btn)
        actions_layout.addStretch()

        return actions_bar

    def _create_filters(self) -> QFrame:
        """Создать панель фильтров."""
        filters = QFrame()
        filters.setObjectName("FilterBar")
        self.filters_layout = QVBoxLayout(filters)
        self.filters_layout.setContentsMargins(12, 10, 12, 10)
        self.filters_layout.setSpacing(8)
        self.filters_top_row = QHBoxLayout()
        self.filters_top_row.setSpacing(8)
        self.filters_bottom_row = QHBoxLayout()
        self.filters_bottom_row.setSpacing(8)

        self.country_filter = QLineEdit()
        self.country_filter.setPlaceholderText("Поиск по стране")
        self.country_filter.setMinimumWidth(180)
        self.country_filter.setClearButtonEnabled(True)

        self.use_date_from = QCheckBox("Дата с")
        self.date_from_filter = DateSelect(QDate.currentDate())
        self.date_from_filter.setEnabled(False)
        self.use_date_from.toggled.connect(self.date_from_filter.setEnabled)

        self.use_date_to = QCheckBox("Дата по")
        self.date_to_filter = DateSelect(QDate.currentDate().addMonths(1))
        self.date_to_filter.setEnabled(False)
        self.use_date_to.toggled.connect(self.date_to_filter.setEnabled)

        price_validator = QDoubleValidator(0.0, 10_000_000.0, 2, self)
        price_validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        self.min_price_filter = QLineEdit()
        self.min_price_filter.setPlaceholderText("Цена от")
        self.min_price_filter.setValidator(price_validator)
        self.min_price_filter.setFixedWidth(120)
        self.min_price_filter.setClearButtonEnabled(True)

        self.max_price_filter = QLineEdit()
        self.max_price_filter.setPlaceholderText("Цена до")
        self.max_price_filter.setValidator(price_validator)
        self.max_price_filter.setFixedWidth(120)
        self.max_price_filter.setClearButtonEnabled(True)

        self.apply_btn = QPushButton("Применить")
        self.apply_btn.setObjectName("GhostButton")
        self.reset_btn = QPushButton("Сброс")
        self.reset_btn.setObjectName("GhostButton")

        self.apply_btn.clicked.connect(self.apply_filters)
        self.reset_btn.clicked.connect(self.reset_filters)

        self.date_from_group = QWidget()
        date_from_group_layout = QHBoxLayout(self.date_from_group)
        date_from_group_layout.setContentsMargins(0, 0, 0, 0)
        date_from_group_layout.setSpacing(8)
        date_from_group_layout.addWidget(self.use_date_from)
        date_from_group_layout.addWidget(self.date_from_filter)

        self.date_to_group = QWidget()
        date_to_group_layout = QHBoxLayout(self.date_to_group)
        date_to_group_layout.setContentsMargins(0, 0, 0, 0)
        date_to_group_layout.setSpacing(8)
        date_to_group_layout.addWidget(self.use_date_to)
        date_to_group_layout.addWidget(self.date_to_filter)

        self.filters_layout.addLayout(self.filters_top_row)
        self.filters_layout.addLayout(self.filters_bottom_row)
        self._is_compact_filters: bool | None = None
        self._arrange_filters(self.width())

        return filters

    def _create_table(self) -> QTableWidget:
        """Создать таблицу туров."""
        table = QTableWidget(0, 10)
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels([
            "ID", "Название", "Страна", "Город", "С", "По", "Цена", "Мест", "Свободные места", "Действия"
        ])
        table.verticalHeader().setVisible(False)
        table.setColumnHidden(0, True)
        table.setCornerButtonEnabled(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        if not (self.can_edit or self.can_delete):
            table.setColumnHidden(9, True)
        table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        return table

    def _clear_layout(self, layout: QHBoxLayout) -> None:
        """Очистить layout."""
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count():
                    child_layout.takeAt(0)

    def _arrange_filters(self, width: int) -> None:
        """Расположить фильтры в зависимости от ширины."""
        compact_mode = width < 1180
        if compact_mode == self._is_compact_filters:
            return

        self._is_compact_filters = compact_mode
        self._clear_layout(self.filters_top_row)
        self._clear_layout(self.filters_bottom_row)

        self.filters_top_row.addWidget(self.country_filter, 1)
        self.filters_top_row.addWidget(self.date_from_group)
        self.filters_top_row.addWidget(self.date_to_group)

        if compact_mode:
            self.filters_bottom_row.addWidget(self.min_price_filter)
            self.filters_bottom_row.addWidget(self.max_price_filter)
            self.filters_bottom_row.addWidget(self.apply_btn)
            self.filters_bottom_row.addWidget(self.reset_btn)
            self.filters_bottom_row.addStretch()
        else:
            self.filters_top_row.addWidget(self.min_price_filter)
            self.filters_top_row.addWidget(self.max_price_filter)
            self.filters_top_row.addWidget(self.apply_btn)
            self.filters_top_row.addWidget(self.reset_btn)
            self.filters_top_row.addStretch()
            self.filters_bottom_row.addStretch()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._arrange_filters(self.width())

    def apply_filters(self) -> None:
        """Применить фильтры."""
        self.country_filter_value = self.country_filter.text().strip()
        self.date_from_value = (
            self.date_from_filter.date().toString("yyyy-MM-dd") if self.use_date_from.isChecked() else None
        )
        self.date_to_value = (
            self.date_to_filter.date().toString("yyyy-MM-dd") if self.use_date_to.isChecked() else None
        )
        self.min_price_value = self._parse_price(self.min_price_filter.text())
        self.max_price_value = self._parse_price(self.max_price_filter.text())
        self.refresh()

    def reset_filters(self) -> None:
        """Сбросить фильтры."""
        self.country_filter.clear()
        self.use_date_from.setChecked(False)
        self.use_date_to.setChecked(False)
        self.min_price_filter.clear()
        self.max_price_filter.clear()
        self.country_filter_value = ""
        self.date_from_value = None
        self.date_to_value = None
        self.min_price_value = None
        self.max_price_value = None
        self.refresh()

    def refresh(self) -> None:
        """Обновить таблицу туров."""
        rows = self.service.list_tours(
            search=self._search_text,
            country=self.country_filter_value,
            min_price=self.min_price_value,
            max_price=self.max_price_value,
            date_from=self.date_from_value,
            date_to=self.date_to_value,
        )
        self._rows = rows
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
            self.table.setItem(row_idx, 8, QTableWidgetItem(str(row.get("free_seats", 0))))
            if self.can_edit or self.can_delete:
                self.table.setCellWidget(row_idx, 9, self._actions_widget(row))
            self.table.setRowHeight(row_idx, 52)

    def apply_global_search(self, text: str) -> None:
        """Обработать глобальный поиск."""
        self._search_text = text
        self.country_filter_value = ""
        self.country_filter.setText("")
        self.refresh()

    def _actions_widget(self, row: dict[str, Any]) -> QWidget:
        """Создать виджет действий для строки."""
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
            edit_btn.clicked.connect(lambda: self._edit_tour(row))
            layout.addWidget(edit_btn)

        if self.can_delete:
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("DangerButton")
            delete_btn.setMinimumWidth(86)
            delete_btn.setFixedHeight(28)
            delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            delete_btn.clicked.connect(lambda: self._delete_tour(row["id"]))
            layout.addWidget(delete_btn)
        return container

    def _on_cell_double_clicked(self, row_idx: int, _: int) -> None:
        """Обработать двойной клик по ячейке."""
        if row_idx < 0 or row_idx >= len(self._rows):
            return
        self._view_tour_details(self._rows[row_idx])

    def _selected_row(self) -> dict[str, Any] | None:
        """Получить выбранную строку."""
        row_idx = self.table.currentRow()
        if row_idx < 0 or row_idx >= len(self._rows):
            return None
        return self._rows[row_idx]

    def _consult_selected_tour(self) -> None:
        """Консультировать клиента по выбранному туру."""
        if not self.can_consult:
            return
        row = self._selected_row()
        if not row:
            show_error(self, "Консультация", "Выберите тур в таблице для консультации.")
            return
        if not self.clients_service:
            self._view_tour_details(row)
            return

        clients = self.clients_service.list_client_choices()
        if not clients:
            show_error(self, "Консультация", "Нет клиентов. Сначала добавьте клиента.")
            return

        dialog = ConsultationDialog(
            parent=self,
            tour_data=row,
            clients=clients,
            can_register_sale=self.can_register_sale,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if dialog.register_requested:
            client_id = dialog.selected_client_id()
            if not client_id:
                show_error(self, "Продажа", "Выберите клиента для регистрации продажи.")
                return
            self.register_sale_requested.emit(int(row["id"]), int(client_id))
            return

        self._view_tour_details(row)

    def _register_sale_for_selected_tour(self) -> None:
        """Зарегистрировать продажу для выбранного тура."""
        if not self.can_register_sale:
            return
        row = self._selected_row()
        if not row:
            show_error(self, "Продажа", "Выберите тур, чтобы зарегистрировать продажу.")
            return
        self.register_sale_requested.emit(int(row["id"]), 0)

    def _view_tour_details(self, row: dict[str, Any]) -> None:
        """Показать детали тура."""
        dialog = TourDetailsDialog(self, row)
        dialog.exec()

    @staticmethod
    def _parse_price(text: str) -> float | None:
        """Разобрать цену из строки."""
        normalized = text.strip().replace(" ", "").replace(",", ".")
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None

    def _delete_tour(self, tour_id: int) -> None:
        """Удалить тур."""
        if not self.can_delete:
            return
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
        """Редактировать тур."""
        if not self.can_edit:
            return
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
        """Добавить новый тур."""
        if not self.can_create:
            return
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
