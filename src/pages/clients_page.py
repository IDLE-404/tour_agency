from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.clients_service import ClientsService
from src.utils.formatters import ask_confirmation, show_error, show_info


class ClientDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, data: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.full_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+79991234567")
        self.email_input = QLineEdit()
        self.document_input = QLineEdit()

        self.birth_toggle = QCheckBox("Указать дату рождения")
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDisplayFormat("yyyy-MM-dd")
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate())
        self.birth_date_input.setEnabled(False)
        self.birth_toggle.toggled.connect(self.birth_date_input.setEnabled)

        form.addRow("ФИО *", self.full_name_input)
        form.addRow("Телефон *", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Документ *", self.document_input)

        birth_layout = QVBoxLayout()
        birth_layout.setContentsMargins(0, 0, 0, 0)
        birth_layout.addWidget(self.birth_toggle)
        birth_layout.addWidget(self.birth_date_input)
        form.addRow("Дата рождения", birth_layout)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addLayout(form)
        layout.addLayout(buttons)

        if data:
            self.full_name_input.setText(data.get("full_name", ""))
            self.phone_input.setText(data.get("phone", ""))
            self.email_input.setText(data.get("email") or "")
            self.document_input.setText(data.get("document", ""))
            if data.get("birth_date"):
                self.birth_toggle.setChecked(True)
                self.birth_date_input.setDate(QDate.fromString(data["birth_date"], "yyyy-MM-dd"))

    def payload(self) -> dict[str, Any]:
        birth_date = self.birth_date_input.date().toString("yyyy-MM-dd") if self.birth_toggle.isChecked() else None
        return {
            "full_name": self.full_name_input.text(),
            "phone": self.phone_input.text(),
            "email": self.email_input.text(),
            "document": self.document_input.text(),
            "birth_date": birth_date,
        }


class ClientsPage(QWidget):
    data_changed = Signal()
    supports_add = True
    search_placeholder = "Поиск клиентов по ФИО или телефону..."

    def __init__(self, service: ClientsService) -> None:
        super().__init__()
        self.service = service
        self._search_text = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.caption = QLabel("Справочник клиентов")
        self.caption.setObjectName("PageTitle")

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Телефон", "Email", "Документ", "Дата рождения", "Действия"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.caption)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        rows = self.service.list_clients(self._search_text)
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["full_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["phone"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row.get("email") or "—"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["document"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(row.get("birth_date") or "—"))
            self.table.setCellWidget(row_idx, 6, self._actions_widget(row))
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

        edit_btn.clicked.connect(lambda: self._edit_client(row))
        delete_btn.clicked.connect(lambda: self._delete_client(row["id"]))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        return container

    def _delete_client(self, client_id: int) -> None:
        if not ask_confirmation(self, "Подтверждение", "Удалить выбранного клиента?"):
            return
        try:
            self.service.delete_client(client_id)
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Удалено", "Клиент удален.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def _edit_client(self, row: dict[str, Any]) -> None:
        dialog = ClientDialog(self, row)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.service.update_client(row["id"], dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Сохранено", "Данные клиента обновлены.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def handle_add(self) -> None:
        dialog = ClientDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.service.create_client(dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Готово", "Клиент добавлен.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self.refresh()
