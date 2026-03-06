"""
Tour Agency AIS — Автоматизированная информационная система Турфирмы.

Простыми словами: это программа для управления туристическим агентством.
В ней можно:
- Вести базу клиентов и туров
- Оформлять бронирования и продажи
- Смотреть отчёты по продажам
- Работать под разными ролями (Админ, Менеджер, Продавец, Гость)
"""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.db.database import DatabaseManager
from src.db.database_init import seed_database
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow
from src.utils.paths import resource_path


def load_stylesheet() -> str:
    """
    Загрузить красивый внешний вид программы (цвета, шрифты, кнопки).
    
    Returns:
        Содержимое файла styles.qss или пустая строка, если файл не найден
    """
    styles_path = resource_path("assets", "styles.qss")
    if styles_path.exists():
        return styles_path.read_text(encoding="utf-8")
    return ""


def main() -> None:
    """
    Главная точка входа — отсюда начинается запуск программы.
    
    Что происходит по шагам:
    1. Создаём приложение Qt
    2. Настраиваем шрифт и стили
    3. Инициализируем базу данных
    4. Показываем окно входа
    5. После успешного входа — показываем главное окно
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Tour Agency AIS")
    app.setFont(QFont("Inter", 10))

    # Применяем красивый стиль, если файл стилей найден
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # Создаём и инициализируем базу данных
    db = DatabaseManager()
    db.initialize()
    seed_database(db)

    # Показываем окно входа — пока пользователь не войдёт, программа не пустится дальше
    login_window = LoginWindow(db)
    if login_window.exec() != LoginWindow.Accepted:
        sys.exit(0)

    # После успешного входа открываем главное окно программы
    user = login_window.authenticated_user
    window = MainWindow(db, user)
    window.show()

    # Запускаем главный цикл приложения
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
