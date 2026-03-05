from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.db.database import DatabaseManager
from src.services.auth_service import AuthService
from src.utils.formatters import show_error


class LoginWindow(QDialog):
    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setMinimumSize(520, 360)
        self.auth_service = AuthService(db)
        self.authenticated_user: dict | None = None

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(40, 30, 40, 30)

        container = QFrame()
        container.setObjectName("LoginCard")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 28, 30, 24)
        container_layout.setSpacing(16)

        title = QLabel("Tour Agency AIS")
        title.setObjectName("LoginTitle")
        subtitle = QLabel("Вход в систему")
        subtitle.setObjectName("LoginSubtitle")

        form = QFormLayout()
        form.setContentsMargins(0, 8, 0, 0)
        form.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setText("admin")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText("admin")

        form.addRow("Логин *", self.username_input)
        form.addRow("Пароль *", self.password_input)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.clicked.connect(self.handle_login)

        hint = QLabel("Демо-доступ: admin / admin")
        hint.setObjectName("MutedText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(title)
        container_layout.addWidget(subtitle)
        container_layout.addLayout(form)
        container_layout.addWidget(self.login_btn)
        container_layout.addWidget(hint)

        root_layout.addStretch()
        root_layout.addWidget(container)
        root_layout.addStretch()

        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            show_error(self, "Ошибка", "Введите логин и пароль.")
            return

        user = self.auth_service.authenticate(username, password)
        if not user:
            show_error(self, "Ошибка", "Неверный логин или пароль.")
            return

        self.authenticated_user = user
        self.accept()
