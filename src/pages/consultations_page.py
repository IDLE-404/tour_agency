from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.utils.formatters import format_money, show_error


class ConsultationCardDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        client_label: str,
        tour: dict[str, Any],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Карточка консультации")
        self.setMinimumWidth(520)

        destination = f"{tour.get('country', '')}, {tour.get('city', '')}".strip(", ")

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Клиент", QLabel(client_label))
        form.addRow("Тур", QLabel(tour.get("name", "—")))
        form.addRow("Направление", QLabel(destination or "—"))
        form.addRow("Период", QLabel(f"{tour.get('date_from', '—')} — {tour.get('date_to', '—')}"))
        form.addRow("Стоимость", QLabel(format_money(float(tour.get("price", 0)))))
        form.addRow("Свободно мест", QLabel(str(tour.get("free_seats", 0))))
        form.addRow("Описание", QLabel(tour.get("description") or "Описание не заполнено."))

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("PrimaryButton")
        close_btn.clicked.connect(self.accept)

        root.addLayout(form)
        root.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


class ConsultationsPage(QWidget):
    register_sale_requested = Signal(int, int)
    supports_add = False
    search_placeholder = "Поиск туров для консультации..."

    def __init__(
        self,
        clients_service: ClientsService,
        tours_service: ToursService,
        can_register_sale: bool = True,
    ) -> None:
        super().__init__()
        self.clients_service = clients_service
        self.tours_service = tours_service
        self.can_register_sale = can_register_sale
        self._search_text = ""
        self._rows: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Консультации клиентов")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Выберите клиента и тур, затем откройте карточку консультации или регистрацию продажи.")
        subtitle.setObjectName("MutedText")

        bar = QFrame()
        bar.setObjectName("FilterBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 10, 12, 10)
        bar_layout.setSpacing(8)

        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(340)

        refresh_clients_btn = QPushButton("Обновить клиентов")
        refresh_clients_btn.setObjectName("GhostButton")
        refresh_clients_btn.clicked.connect(self._reload_clients)

        self.consult_btn = QPushButton("Открыть консультацию")
        self.consult_btn.setObjectName("GhostButton")
        self.consult_btn.clicked.connect(self._open_consultation_card)

        self.register_sale_btn = QPushButton("Регистрация продажи")
        self.register_sale_btn.setObjectName("PrimaryButton")
        self.register_sale_btn.setVisible(self.can_register_sale)
        self.register_sale_btn.clicked.connect(self._register_sale)

        bar_layout.addWidget(QLabel("Клиент"))
        bar_layout.addWidget(self.client_combo, 1)
        bar_layout.addWidget(refresh_clients_btn)
        bar_layout.addWidget(self.consult_btn)
        bar_layout.addWidget(self.register_sale_btn)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Тур", "Страна", "Город", "С", "По", "Цена", "Свободно"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setCornerButtonEnabled(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(lambda *_: self._open_consultation_card())

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(bar)
        root.addWidget(self.table)

        self.refresh()

    def _reload_clients(self) -> None:
        selected_client_id = self.client_combo.currentData()
        self.client_combo.blockSignals(True)
        self.client_combo.clear()

        clients = self.clients_service.list_client_choices()
        for client in clients:
            label = f"{client['full_name']} ({client['phone']})"
            self.client_combo.addItem(label, int(client["id"]))

        if self.client_combo.count() == 0:
            self.client_combo.addItem("Нет клиентов", 0)

        if selected_client_id is not None:
            idx = self.client_combo.findData(selected_client_id)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)

        self.client_combo.blockSignals(False)

    def _selected_tour(self) -> dict[str, Any] | None:
        row_idx = self.table.currentRow()
        if row_idx < 0 or row_idx >= len(self._rows):
            return None
        return self._rows[row_idx]

    def _selected_client(self) -> tuple[int, str] | None:
        client_id = self.client_combo.currentData()
        if not client_id:
            return None
        return int(client_id), self.client_combo.currentText()

    def _open_consultation_card(self) -> None:
        selected_client = self._selected_client()
        if not selected_client:
            show_error(self, "Консультация", "Сначала выберите клиента.")
            return

        tour = self._selected_tour()
        if not tour:
            show_error(self, "Консультация", "Сначала выберите тур.")
            return

        _, client_label = selected_client
        dialog = ConsultationCardDialog(self, client_label=client_label, tour=tour)
        dialog.exec()

    def _register_sale(self) -> None:
        if not self.can_register_sale:
            return

        selected_client = self._selected_client()
        if not selected_client:
            show_error(self, "Продажа", "Сначала выберите клиента.")
            return
        client_id, _ = selected_client

        tour = self._selected_tour()
        if not tour:
            show_error(self, "Продажа", "Сначала выберите тур.")
            return

        self.register_sale_requested.emit(int(tour["id"]), client_id)

    def refresh(self) -> None:
        self._reload_clients()

        rows = self.tours_service.list_tours(search=self._search_text)
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
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(row.get("free_seats", 0))))
            self.table.setRowHeight(row_idx, 46)

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self.refresh()

    def handle_add(self) -> None:
        return
