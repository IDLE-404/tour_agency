from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.db.database import DatabaseManager
from src.pages.bookings_page import BookingsPage
from src.pages.clients_page import ClientsPage
from src.pages.dashboard_page import DashboardPage
from src.pages.tours_page import ToursPage
from src.services.bookings_service import BookingsService
from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.ui.widgets import SidebarButton


class SettingsPage(QWidget):
    supports_add = False
    search_placeholder = "Поиск недоступен"

    def __init__(self, user: dict[str, Any]) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        title = QLabel("Настройки")
        title.setObjectName("PageTitle")

        user_info = QLabel(
            f"Текущий пользователь: <b>{user['full_name']}</b><br>"
            f"Логин: {user['username']}<br>"
            f"Роль: {user['role']}"
        )
        user_info.setObjectName("MutedText")

        hint = QLabel("Для MVP настройки сведены к информации о профиле.")
        hint.setObjectName("MutedText")

        card_layout.addWidget(title)
        card_layout.addWidget(user_info)
        card_layout.addWidget(hint)
        card_layout.addStretch()

        layout.addWidget(card)

    def apply_global_search(self, _: str) -> None:
        return

    def handle_add(self) -> None:
        return


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager, user: dict[str, Any]) -> None:
        super().__init__()
        self.setWindowTitle("Автоматизированная информационная система Турфирмы")
        self.setMinimumSize(1000, 650)

        self.clients_service = ClientsService(db)
        self.tours_service = ToursService(db)
        self.bookings_service = BookingsService(db)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        sidebar = self._build_sidebar()
        content = self._build_content(user)

        root.addWidget(sidebar)
        root.addWidget(content)

        self._setup_navigation()
        self.switch_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(8)

        logo = QLabel("TOUR CRM")
        logo.setObjectName("SidebarLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.btn_dashboard = SidebarButton("Панель")
        self.btn_clients = SidebarButton("Клиенты")
        self.btn_tours = SidebarButton("Туры")
        self.btn_bookings = SidebarButton("Бронирования")
        self.btn_settings = SidebarButton("Настройки")

        layout.addWidget(logo)
        layout.addSpacing(10)
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_clients)
        layout.addWidget(self.btn_tours)
        layout.addWidget(self.btn_bookings)
        layout.addWidget(self.btn_settings)
        layout.addStretch()

        return sidebar

    def _build_content(self, user: dict[str, Any]) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        topbar = QFrame()
        topbar.setObjectName("TopBar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(10)

        self.page_title = QLabel("Панель")
        self.page_title.setObjectName("TopBarTitle")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("GlobalSearch")
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self._on_search_changed)

        self.add_btn = QPushButton("Добавить")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(self._on_add_clicked)

        top_layout.addWidget(self.page_title)
        top_layout.addStretch()
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.add_btn)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")

        self.dashboard_page = DashboardPage(
            clients_service=self.clients_service,
            tours_service=self.tours_service,
            bookings_service=self.bookings_service,
        )
        self.clients_page = ClientsPage(self.clients_service)
        self.tours_page = ToursPage(self.tours_service)
        self.bookings_page = BookingsPage(
            bookings_service=self.bookings_service,
            clients_service=self.clients_service,
            tours_service=self.tours_service,
        )
        self.settings_page = SettingsPage(user)

        self.clients_page.data_changed.connect(self.dashboard_page.refresh)
        self.tours_page.data_changed.connect(self.dashboard_page.refresh)
        self.bookings_page.data_changed.connect(self.dashboard_page.refresh)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.clients_page)
        self.stack.addWidget(self.tours_page)
        self.stack.addWidget(self.bookings_page)
        self.stack.addWidget(self.settings_page)

        layout.addWidget(topbar)
        layout.addWidget(self.stack)

        return wrapper

    def _setup_navigation(self) -> None:
        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_clients,
            self.btn_tours,
            self.btn_bookings,
            self.btn_settings,
        ]

        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_clients.clicked.connect(lambda: self.switch_page(1))
        self.btn_tours.clicked.connect(lambda: self.switch_page(2))
        self.btn_bookings.clicked.connect(lambda: self.switch_page(3))
        self.btn_settings.clicked.connect(lambda: self.switch_page(4))

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for idx, button in enumerate(self.nav_buttons):
            button.setChecked(idx == index)

        page = self.stack.currentWidget()
        title = ["Панель", "Клиенты", "Туры", "Бронирования", "Настройки"][index]
        self.page_title.setText(title)

        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        self.search_input.setPlaceholderText(getattr(page, "search_placeholder", "Поиск..."))
        supports_add = bool(getattr(page, "supports_add", False))
        self.add_btn.setVisible(supports_add)
        self.search_input.setEnabled(index in {1, 2, 3})

        if hasattr(page, "refresh"):
            page.refresh()

        self._animate_page(page)

    def _animate_page(self, page: QWidget) -> None:
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        self._current_animation = animation

    def _on_search_changed(self, text: str) -> None:
        page = self.stack.currentWidget()
        if hasattr(page, "apply_global_search"):
            page.apply_global_search(text)

    def _on_add_clicked(self) -> None:
        page = self.stack.currentWidget()
        if hasattr(page, "handle_add"):
            page.handle_add()
