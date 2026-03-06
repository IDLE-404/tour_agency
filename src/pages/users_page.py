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
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.services.users_service import UsersService
from src.utils.formatters import ask_confirmation, show_error, show_info
from src.utils.roles import ROLE_CHOICES, role_label


class UserDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, data: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Пользователь")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.full_name_input = QLineEdit()
        self.username_input = QLineEdit()

        self.role_input = QComboBox()
        for role in ROLE_CHOICES:
            self.role_input.addItem(role_label(role), role)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Минимум 4 символа")

        self.password_hint = QLabel("Пароль обязателен при создании.")
        self.password_hint.setObjectName("MutedText")

        form.addRow("ФИО *", self.full_name_input)
        form.addRow("Логин *", self.username_input)
        form.addRow("Роль *", self.role_input)
        form.addRow("Пароль", self.password_input)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        layout.addLayout(form)
        layout.addWidget(self.password_hint)
        layout.addLayout(btns)

        if data:
            self.full_name_input.setText(data.get("full_name", ""))
            self.username_input.setText(data.get("username", ""))
            idx = self.role_input.findData(data.get("role"))
            if idx >= 0:
                self.role_input.setCurrentIndex(idx)
            self.password_hint.setText("Оставьте пароль пустым, чтобы не менять.")
        else:
            self.password_input.setPlaceholderText("Обязательно")

    def payload(self) -> dict[str, Any]:
        return {
            "full_name": self.full_name_input.text(),
            "username": self.username_input.text(),
            "role": self.role_input.currentData(),
            "password": self.password_input.text(),
        }


class UsersPage(QWidget):
    data_changed = Signal()
    supports_add = True
    search_placeholder = "Поиск пользователей по ФИО или логину..."

    def __init__(
        self,
        service: UsersService,
        current_user_id: int,
        can_create: bool = True,
        can_edit: bool = True,
        can_delete: bool = True,
    ) -> None:
        super().__init__()
        self.service = service
        self.current_user_id = current_user_id
        self.can_create = can_create
        self.can_edit = can_edit
        self.can_delete = can_delete
        self.supports_add = self.can_create
        self._search_text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("Управление пользователями")
        title.setObjectName("PageTitle")

        self.table = QTableWidget(0, 6)
        self.table.setObjectName("DataTable")
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Логин", "Роль", "Создан", "Действия"])
        self.table.setColumnHidden(0, True)
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        if not (self.can_edit or self.can_delete):
            self.table.setColumnHidden(5, True)

        root.addWidget(title)
        root.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        rows = self.service.list_users(self._search_text)
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["full_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["username"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(role_label(row["role"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["created_at"]))
            if self.can_edit or self.can_delete:
                self.table.setCellWidget(row_idx, 5, self._actions_widget(row))
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
            edit_btn.clicked.connect(lambda: self._edit_user(row))
            layout.addWidget(edit_btn)

        if self.can_delete:
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("DangerButton")
            delete_btn.setMinimumWidth(86)
            delete_btn.setFixedHeight(28)
            delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            delete_btn.clicked.connect(lambda: self._delete_user(row))
            layout.addWidget(delete_btn)

        return container

    def _edit_user(self, row: dict[str, Any]) -> None:
        dialog = UserDialog(self, row)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.service.update_user(row["id"], dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Сохранено", "Пользователь обновлен.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def _delete_user(self, row: dict[str, Any]) -> None:
        if row["id"] == self.current_user_id:
            show_error(self, "Ошибка", "Нельзя удалить текущего пользователя.")
            return
        if not ask_confirmation(self, "Подтверждение", "Удалить выбранного пользователя?"):
            return
        try:
            self.service.delete_user(row["id"])
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Удалено", "Пользователь удален.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def handle_add(self) -> None:
        dialog = UserDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.create_user(dialog.payload())
            self.refresh()
            self.data_changed.emit()
            show_info(self, "Готово", "Пользователь добавлен.")
        except ValueError as exc:
            show_error(self, "Ошибка", str(exc))

    def apply_global_search(self, text: str) -> None:
        self._search_text = text
        self.refresh()
