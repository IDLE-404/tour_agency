"""
Диалоги для работы с турами.

Содержит классы:
- TourDialog: создание/редактирование тура
- TourDetailsDialog: просмотр деталей тура
- ConsultationDialog: консультация клиента по туру
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets import DateSelect
from src.utils.formatters import format_money


class TourDialog(QDialog):
    """Диалог создания/редактирования тура."""

    def __init__(
        self,
        parent: QWidget | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Тур")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.country_input = QLineEdit()
        self.city_input = QLineEdit()
        self.date_from_input = DateSelect(QDate.currentDate(), width=None)
        self.date_to_input = DateSelect(QDate.currentDate().addDays(7), width=None)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10_000_000)
        self.price_input.setSingleStep(1000)
        self.price_input.setSuffix(" ₽")

        self.seats_input = QSpinBox()
        self.seats_input.setRange(0, 10000)

        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(100)

        form.addRow("Название *", self.name_input)
        form.addRow("Страна *", self.country_input)
        form.addRow("Город *", self.city_input)
        form.addRow("Дата с *", self.date_from_input)
        form.addRow("Дата по *", self.date_to_input)
        form.addRow("Цена *", self.price_input)
        form.addRow("Мест *", self.seats_input)
        form.addRow("Описание", self.description_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("PrimaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        root.addLayout(form)
        root.addLayout(btn_layout)

        if data:
            self._populate_data(data)

    def _populate_data(self, data: dict[str, Any]) -> None:
        """Заполнить форму данными тура."""
        self.name_input.setText(data.get("name", ""))
        self.country_input.setText(data.get("country", ""))
        self.city_input.setText(data.get("city", ""))
        self.date_from_input.setDate(QDate.fromString(data["date_from"], "yyyy-MM-dd"))
        self.date_to_input.setDate(QDate.fromString(data["date_to"], "yyyy-MM-dd"))
        self.price_input.setValue(float(data.get("price", 0)))
        self.seats_input.setValue(int(data.get("seats", 0)))
        self.description_input.setText(data.get("description") or "")

    def payload(self) -> dict[str, Any]:
        """Получить данные тура из формы."""
        return {
            "name": self.name_input.text(),
            "country": self.country_input.text(),
            "city": self.city_input.text(),
            "date_from": self.date_from_input.date().toString("yyyy-MM-dd"),
            "date_to": self.date_to_input.date().toString("yyyy-MM-dd"),
            "price": self.price_input.value(),
            "seats": self.seats_input.value(),
            "description": self.description_input.toPlainText(),
        }


class TourDetailsDialog(QDialog):
    """Диалог просмотра деталей тура."""

    def __init__(
        self,
        parent: QWidget | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Карточка тура")
        self.setMinimumWidth(540)

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        details = data or {}
        destination = f"{details.get('country', '')}, {details.get('city', '')}".strip(", ")

        form.addRow("Название", QLabel(details.get("name", "—")))
        form.addRow("Направление", QLabel(destination or "—"))
        form.addRow("Период", QLabel(f"{details.get('date_from', '—')} — {details.get('date_to', '—')}"))
        form.addRow("Стоимость", QLabel(format_money(float(details.get("price", 0)))))
        form.addRow("Всего мест", QLabel(str(details.get("seats", 0))))
        form.addRow("Свободно мест", QLabel(str(details.get("free_seats", 0))))

        description = QTextEdit()
        description.setReadOnly(True)
        description.setFixedHeight(130)
        description.setPlainText(details.get("description") or "Описание тура не заполнено.")

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("PrimaryButton")
        close_btn.clicked.connect(self.accept)

        root.addLayout(form)
        root.addWidget(QLabel("Описание"))
        root.addWidget(description)
        root.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


class ConsultationDialog(QDialog):
    """Диалог консультации клиента по туру."""

    def __init__(
        self,
        parent: QWidget | None,
        tour_data: dict[str, Any],
        clients: list[dict[str, Any]],
        can_register_sale: bool,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Консультация клиента")
        self.setMinimumWidth(520)
        self.register_requested = False

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self._populate_tour_info(form, tour_data)
        self._populate_clients(form, clients)
        self._create_buttons(form, can_register_sale)

    def _populate_tour_info(self, form: QFormLayout, tour_data: dict[str, Any]) -> None:
        """Заполнить информацию о туре."""
        destination = f"{tour_data.get('country', '')}, {tour_data.get('city', '')}".strip(", ")
        form.addRow("Тур", QLabel(tour_data.get("name", "—")))
        form.addRow("Направление", QLabel(destination or "—"))
        form.addRow("Период", QLabel(f"{tour_data.get('date_from', '—')} — {tour_data.get('date_to', '—')}"))
        form.addRow("Стоимость", QLabel(format_money(float(tour_data.get("price", 0)))))
        form.addRow("Свободно мест", QLabel(str(tour_data.get("free_seats", 0))))

    def _populate_clients(self, form: QFormLayout, clients: list[dict[str, Any]]) -> None:
        """Заполнить комбобокс клиентами."""
        self.client_combo = QComboBox()
        for client in clients:
            label = f"{client['full_name']} ({client['phone']})"
            self.client_combo.addItem(label, int(client["id"]))
        form.addRow("Клиент *", self.client_combo)

    def _create_buttons(self, form: QFormLayout, can_register_sale: bool) -> None:
        """Создать кнопки диалога."""
        buttons = QHBoxLayout()
        buttons.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)

        if can_register_sale:
            sale_btn = QPushButton("К регистрации продажи")
            sale_btn.setObjectName("PrimaryButton")
            sale_btn.clicked.connect(self._open_sale)
            buttons.addWidget(sale_btn)

        form.addRow(buttons)

    def _open_sale(self) -> None:
        """Открыть регистрацию продажи."""
        self.register_requested = True
        self.accept()

    def selected_client_id(self) -> int | None:
        """Получить ID выбранного клиента."""
        value = self.client_combo.currentData()
        return int(value) if value is not None else None
