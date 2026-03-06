"""
Главное окно приложения Tour Agency AIS.

Это основное окно программы, которое видит пользователь после входа.
Здесь есть:
- Боковое меню (сайдбар) с кнопками навигации
- Переключение между страницами (Клиенты, Туры, Бронирования и т.д.)
- Поиск и кнопки действий на каждой странице

Каждая роль (Админ, Менеджер, Продавец, Гость) видит свой набор страниц.
"""

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

from src.config import (
    PageIndex,
    get_allowed_indexes,
    get_default_page_index,
    get_page_config,
)
from src.db.database import DatabaseManager
from src.pages.bookings_page import BookingsPage
from src.pages.consultations_page import ConsultationsPage
from src.pages.clients_page import ClientsPage
from src.pages.dashboard_page import DashboardPage
from src.pages.manager_page import ManagerPage
from src.pages.reports_page import ReportsPage
from src.pages.tours_page import ToursPage
from src.pages.users_page import UsersPage
from src.services.bookings_service import BookingsService
from src.services.clients_service import ClientsService
from src.services.tours_service import ToursService
from src.services.users_service import UsersService
from src.ui.widgets import SidebarButton
from src.utils.roles import (
    ROLE_ADMIN,
    ROLE_GUEST,
    ROLE_MANAGER,
    ROLE_SELLER,
    normalize_role,
)


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    
    Простыми словами: это "основной экран" программы, где пользователь работает.
    Слева — меню с кнопками, справа — содержимое выбранной страницы.
    """

    def __init__(self, db: DatabaseManager, user: dict[str, Any]) -> None:
        super().__init__()
        self.setWindowTitle("Автоматизированная информационная система Турфирмы")
        self.setMinimumSize(1000, 650)

        self.db = db
        self.user = user
        # Определяем роль пользователя — от этого зависит, какие страницы будут доступны
        self.role = self._determine_role(user)

        # Сервисы для работы с данными (база данных)
        self.clients_service = ClientsService(db)
        self.tours_service = ToursService(db)
        self.bookings_service = BookingsService(db)
        self.users_service = UsersService(db)

        # Навигация: какие страницы доступны этой роли
        self.allowed_indexes = get_allowed_indexes(self.role)
        self.current_page_index = get_default_page_index(self.role)

        # UI компоненты (будут созданы ниже)
        self.stack: QStackedWidget | None = None
        self.page_title: QLabel | None = None
        self.search_input: QLineEdit | None = None
        self.add_btn: QPushButton | None = None
        self.nav_buttons: list[QPushButton] = []

        # Словарь для хранения созданных страниц
        self._pages: dict[str, QWidget] = {}

        # Создаём интерфейс, настраиваем навигацию и показываем первую страницу
        self._init_ui()
        self._setup_navigation()
        self._apply_role_navigation()
        self.switch_page(self.current_page_index)

    def _determine_role(self, user: dict[str, Any]) -> str:
        """Определить роль пользователя."""
        role = normalize_role(str(user.get("role", "")))
        username = str(user.get("username", "")).strip().lower()
        role_map = {
            "admin": ROLE_ADMIN,
            "manager": ROLE_MANAGER,
            "seller": ROLE_SELLER,
            "guest": ROLE_GUEST,
        }
        return role_map.get(username, role)

    def _init_ui(self) -> None:
        """
        Создать основной интерфейс окна.
        
        Структура:
        - Слева: боковая панель (сайдбар) с кнопками
        - Справа: рабочая область с контентом
        """
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # Создаём левую панель (меню) и правую часть (контент)
        sidebar = self._build_sidebar()
        content = self._build_content()

        root.addWidget(sidebar)
        root.addWidget(content)

    def _build_sidebar(self) -> QWidget:
        """
        Создать боковую панель меню.
        
        Здесь размещаются:
        - Логотип "TOUR CRM"
        - Кнопки навигации по страницам
        """
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(8)

        # Логотип вверху
        logo = QLabel("TOUR CRM")
        logo.setObjectName("SidebarLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Кнопки навигации — их набор зависит от роли пользователя
        button_labels = ["Панель", "Клиенты", "Туры", "Консультации", "Регистрация продаж", "Пользователи", "Отчеты"]
        self.nav_buttons = [SidebarButton(label) for label in button_labels]

        layout.addWidget(logo)
        layout.addSpacing(10)
        for btn in self.nav_buttons:
            layout.addWidget(btn)
        layout.addStretch()

        return sidebar

    def _build_content(self) -> QWidget:
        """
        Создать правую часть окна — здесь будет контент страниц.
        
        Состоит из:
        - Верхняя панель: заголовок, поиск, кнопки действий
        - Стек страниц: переключение между разделами
        """
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Верхняя панель (TopBar)
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

        self.logout_btn = QPushButton("Выход")
        self.logout_btn.setObjectName("DangerButton")
        self.logout_btn.clicked.connect(self._on_logout_clicked)

        top_layout.addWidget(self.page_title)
        top_layout.addStretch()
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.logout_btn)

        # Стек страниц
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")
        self._create_pages()

        layout.addWidget(topbar)
        layout.addWidget(self.stack)

        return wrapper

    def _create_pages(self) -> None:
        """Создать страницы приложения."""
        # Страница для менеджера отличается от остальных
        if self.role == ROLE_MANAGER:
            self.manager_page = ManagerPage(
                bookings_service=self.bookings_service,
                clients_service=self.clients_service,
                tours_service=self.tours_service,
                can_create=True,
            )
            self.stack.addWidget(self.manager_page)
            self._pages["manager"] = self.manager_page
        else:
            self.dashboard_page = DashboardPage(
                clients_service=self.clients_service,
                tours_service=self.tours_service,
                bookings_service=self.bookings_service,
                mode="admin",
            )
            self.stack.addWidget(self.dashboard_page)
            self._pages["dashboard"] = self.dashboard_page

        # Общие страницы
        self.clients_page = ClientsPage(
            self.clients_service,
            can_create=self._can("clients.create"),
            can_edit=self._can("clients.edit"),
            can_delete=self._can("clients.delete"),
        )
        self.stack.addWidget(self.clients_page)
        self._pages["clients"] = self.clients_page

        self.tours_page = ToursPage(
            self.tours_service,
            clients_service=self.clients_service,
            can_create=self._can("tours.create"),
            can_edit=self._can("tours.edit"),
            can_delete=self._can("tours.delete"),
            can_consult=self._can("consultations.view"),
            can_register_sale=self._can("bookings.create"),
        )
        self.stack.addWidget(self.tours_page)
        self._pages["tours"] = self.tours_page

        self.consultations_page = ConsultationsPage(
            clients_service=self.clients_service,
            tours_service=self.tours_service,
            can_register_sale=self._can("bookings.create"),
        )
        self.stack.addWidget(self.consultations_page)
        self._pages["consultations"] = self.consultations_page

        # Страницы только для админа
        if self.role == ROLE_ADMIN:
            self.bookings_page = BookingsPage(
                bookings_service=self.bookings_service,
                clients_service=self.clients_service,
                tours_service=self.tours_service,
                can_create=True,
                can_edit=True,
                can_delete=True,
                can_export=True,
            )
            self.stack.addWidget(self.bookings_page)
            self._pages["bookings"] = self.bookings_page

            self.users_page = UsersPage(
                service=self.users_service,
                current_user_id=int(self.user["id"]),
                can_create=True,
                can_edit=True,
                can_delete=True,
            )
            self.stack.addWidget(self.users_page)
            self._pages["users"] = self.users_page

            self.reports_page = ReportsPage(bookings_service=self.bookings_service)
            self.stack.addWidget(self.reports_page)
            self._pages["reports"] = self.reports_page

        # Подключение сигналов
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Подключить сигналы между страницами."""
        if self.role == ROLE_MANAGER:
            self.manager_page.data_changed.connect(self._refresh_all_pages)
            self.consultations_page.register_sale_requested.connect(self._open_sale_registration_from_tour)
            self.tours_page.register_sale_requested.connect(self._open_sale_registration_from_tour)
        else:
            self.clients_page.data_changed.connect(self.dashboard_page.refresh)
            self.tours_page.data_changed.connect(self.dashboard_page.refresh)
            self.consultations_page.register_sale_requested.connect(self._open_sale_registration_from_tour)
            self.tours_page.register_sale_requested.connect(self._open_sale_registration_from_tour)

            # Страницы только для админа
            if hasattr(self, "bookings_page"):
                self.bookings_page.data_changed.connect(self.dashboard_page.refresh)
                self.bookings_page.data_changed.connect(self.reports_page.refresh)
            if hasattr(self, "reports_page"):
                self.tours_page.data_changed.connect(self.reports_page.refresh)

    def _can(self, permission: str) -> bool:
        """Проверить наличие разрешения у роли."""
        from src.utils.roles import has_permission

        return has_permission(self.role, permission)

    def _setup_navigation(self) -> None:
        """Настроить навигацию по кнопкам."""
        for idx, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))

    def _apply_role_navigation(self) -> None:
        """Применить видимость кнопок согласно роли."""
        for idx, button in enumerate(self.nav_buttons):
            visible = idx in self.allowed_indexes
            button.setVisible(visible)

    def switch_page(self, index: int) -> None:
        """
        Переключиться на страницу по индексу.
        
        Что происходит:
        1. Проверяем, разрешена ли эта страница для текущей роли
        2. Переключаем стек на нужную страницу
        3. Подсвечиваем активную кнопку в меню
        4. Обновляем заголовок и настройки верхней панели
        5. Обновляем данные на странице
        6. Запускаем анимацию появления
        
        Args:
            index: Индекс страницы (0 = Панель, 1 = Клиенты, и т.д.)
        """
        # Проверяем, есть ли у пользователя доступ к этой странице
        if index not in self.allowed_indexes:
            return

        self.current_page_index = index
        self.stack.setCurrentIndex(index)

        # Подсвечиваем нажатую кнопку
        for idx, button in enumerate(self.nav_buttons):
            button.setChecked(idx == index)

        # Получаем настройки страницы (заголовок, поиск, кнопки)
        page = self.stack.currentWidget()
        config = get_page_config(self.role, index)

        if config:
            self.page_title.setText(config.title)
            self.search_input.setPlaceholderText(config.search_placeholder)
            self.add_btn.setVisible(config.supports_add)
            self.search_input.setEnabled(config.search_enabled)
        else:
            self.page_title.setText("Раздел")
            self.search_input.setPlaceholderText("Поиск...")
            self.add_btn.setVisible(False)
            self.search_input.setEnabled(False)

        # Очищаем строку поиска при переключении
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        # Обновляем данные на странице
        if hasattr(page, "refresh"):
            page.refresh()

        # Красивое появление страницы (анимация)
        self._animate_page(page)

    def _refresh_all_pages(self) -> None:
        """
        Обновить все страницы после изменения данных.
        
        Вызывается, когда пользователь добавил/изменил данные
        на одной из страниц — чтобы остальные страницы тоже обновились.
        """
        for i in range(self.stack.count()):
            page = self.stack.widget(i)
            if hasattr(page, "refresh"):
                page.refresh()

    def _animate_page(self, page: QWidget) -> None:
        """
        Добавить анимацию плавного появления страницы.
        
        Делает интерфейс более приятным — страница не просто появляется,
        а плавно "проявляется" за 220 мс.
        """
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
        """
        Обработать ввод текста в строке поиска.
        
        Передаёт поисковый запрос на текущую страницу.
        """
        page = self.stack.currentWidget()
        if hasattr(page, "apply_global_search"):
            page.apply_global_search(text)

    def _on_add_clicked(self) -> None:
        """Обработать клик по кнопке добавления."""
        page = self.stack.currentWidget()
        if hasattr(page, "handle_add"):
            page.handle_add()

    def _on_logout_clicked(self) -> None:
        """Обработать клик по кнопке выхода."""
        from src.ui.login_window import LoginWindow

        login_window = LoginWindow(self.db)
        if login_window.exec() != LoginWindow.Accepted:
            self.close()
            return

        user = login_window.authenticated_user
        if not user:
            self.close()
            return

        new_window = MainWindow(self.db, user)
        new_window.show()
        self._next_window = new_window
        self.close()

    def _open_sale_registration_from_tour(self, tour_id: int, client_id: int) -> None:
        """
        Открыть регистрацию продажи из консультации.

        Args:
            tour_id: ID тура
            client_id: ID клиента
        """
        if self.role == ROLE_MANAGER:
            self.switch_page(PageIndex.DASHBOARD)
        else:
            if PageIndex.BOOKINGS in self.allowed_indexes:
                self.switch_page(PageIndex.BOOKINGS)
                selected_client_id = client_id if client_id > 0 else None
                self.bookings_page.handle_add(
                    preselected_tour_id=tour_id,
                    preselected_client_id=selected_client_id,
                )
