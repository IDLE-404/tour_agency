"""
Окно входа в систему.

Здесь пользователь:
- Вводит логин и пароль для входа
- Может зарегистрироваться как новый пользователь (с ролью "Гость")
"""

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
from src.services.auth_service import AuthService, hash_password
from src.utils.formatters import show_error, show_info
from src.utils.roles import ROLE_GUEST


class RegisterDialog(QDialog):
    """
    Окно регистрации нового пользователя.
    
    Простыми словами: здесь человек создаёт себе учётную запись.
    Все новые пользователи создаются с ролью "Гость" (только просмотр).
    """

    def __init__(self, parent: LoginWindow | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Регистрация пользователя")
        self.setMinimumWidth(400)

        # Основная раскладка окна
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        # Поля ввода: ФИО, логин, пароль, подтверждение пароля
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("login")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setPlaceholderText("Повторите пароль")

        # Добавляем поля на форму
        form.addRow("ФИО *", self.full_name_input)
        form.addRow("Логин *", self.username_input)
        form.addRow("Пароль *", self.password_input)
        form.addRow("Подтверждение *", self.password_confirm_input)

        # Кнопки: Отмена и Зарегистрировать
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Отмена")
        register_btn = QPushButton("Зарегистрировать")
        register_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        register_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(register_btn)

        layout.addLayout(form)
        layout.addLayout(buttons)

    def payload(self) -> dict:
        """Вернуть данные из формы регистрации."""
        return {
            "full_name": self.full_name_input.text().strip(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
            "password_confirm": self.password_confirm_input.text(),
        }


class LoginWindow(QDialog):
    """
    Главное окно входа в систему.
    
    Что здесь можно сделать:
    - Войти под существующим аккаунтом (admin/admin, manager/manager, и т.д.)
    - Зарегистрировать нового пользователя (будет с ролью "Гость")
    """
    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setMinimumSize(520, 360)
        self.db = db
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

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Логин *", self.username_input)
        form.addRow("Пароль *", self.password_input)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.clicked.connect(self.handle_login)

        self.register_btn = QPushButton("Регистрация")
        self.register_btn.setObjectName("GhostButton")
        self.register_btn.clicked.connect(self.handle_register)

        actions = QHBoxLayout()
        actions.addWidget(self.login_btn)
        actions.addWidget(self.register_btn)

        hint = QLabel("Демо: admin/admin, manager/manager, seller/seller, guest/guest")
        hint.setObjectName("MutedText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(title)
        container_layout.addWidget(subtitle)
        container_layout.addLayout(form)
        container_layout.addLayout(actions)
        container_layout.addWidget(hint)

        root_layout.addStretch()
        root_layout.addWidget(container)
        root_layout.addStretch()

        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.setFocus()

    def handle_login(self) -> None:
        """
        Обработать вход пользователя.
        
        Проверяет:
        - Введён ли логин и пароль
        - Существует ли пользователь с такими данными
        """
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            show_error(self, "Ошибка", "Введите логин и пароль.")
            return

        # Пытаемся аутентифицировать пользователя
        user = self.auth_service.authenticate(username, password)
        if not user:
            show_error(self, "Ошибка", "Неверный логин или пароль.")
            return

        # Успешный вход — сохраняем пользователя и закрываем окно
        self.authenticated_user = user
        self.accept()

    def handle_register(self) -> None:
        """
        Обработать регистрацию нового пользователя.
        
        Что происходит:
        1. Открывается окно регистрации
        2. Проверяются введённые данные (ФИО, логин, пароль)
        3. Если логин свободен — создаётся новый пользователь с ролью "Гость"
        """
        dialog = RegisterDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.payload()

        # Проверяем, что все поля заполнены
        if not data["full_name"]:
            show_error(self, "Ошибка", "Введите ФИО.")
            return
        if not data["username"]:
            show_error(self, "Ошибка", "Введите логин.")
            return
        if not data["password"]:
            show_error(self, "Ошибка", "Введите пароль.")
            return
        if data["password"] != data["password_confirm"]:
            show_error(self, "Ошибка", "Пароли не совпадают.")
            return

        # Регистрируем в базе данных
        try:
            with self.db.get_connection() as conn:
                # Проверяем, не занят ли логин
                exists = conn.execute(
                    "SELECT 1 FROM users WHERE username = ?",
                    (data["username"],),
                ).fetchone()
                if exists:
                    show_error(self, "Ошибка", "Пользователь с таким логином уже существует.")
                    return

                # Создаём нового пользователя с ролью "guest"
                conn.execute(
                    """
                    INSERT INTO users (full_name, username, password_hash, role)
                    VALUES (?, ?, ?, 'guest')
                    """,
                    (
                        data["full_name"],
                        data["username"],
                        hash_password(data["password"]),
                    ),
                )
                conn.commit()

            show_info(self, "Успешно", f"Пользователь {data['username']} зарегистрирован.\nТеперь войдите.")
        except Exception as e:
            show_error(self, "Ошибка", f"Не удалось зарегистрировать: {e}")
