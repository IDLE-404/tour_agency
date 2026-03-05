import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.db.database import DatabaseManager
from src.db.seed import seed_database
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow
from src.utils.paths import resource_path


def load_stylesheet() -> str:
    styles_path = resource_path("assets", "styles.qss")
    if styles_path.exists():
        return styles_path.read_text(encoding="utf-8")
    return ""


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Tour Agency AIS")
    app.setFont(QFont("Inter", 10))

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    db = DatabaseManager()
    db.initialize()
    seed_database(db)

    login_window = LoginWindow(db)
    if login_window.exec() != LoginWindow.Accepted:
        sys.exit(0)

    user = login_window.authenticated_user
    window = MainWindow(db, user)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
