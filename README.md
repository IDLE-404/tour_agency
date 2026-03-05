# Автоматизированная информационная система Турфирмы (MVP)

Desktop MVP на `Python 3.11+`, `PySide6`, `SQLite`.

## Что реализовано
- Авторизация (`admin/admin` по умолчанию).
- Dashboard с KPI-карточками и последними 5 бронированиями.
- CRUD-справочники:
  - Клиенты
  - Туры
  - Бронирования
- Поиск/фильтры:
  - Клиенты: по ФИО/телефону
  - Туры: по стране и диапазону цены
  - Бронирования: по статусу и диапазону дат
- Экспорт бронирований в CSV.
- Валидация обязательных полей, подтверждение удаления, защита от дубля телефона.
- Демоданные при первом запуске (клиенты, туры, бронирования).

## Стек
- Python 3.11+
- PySide6 (Qt Widgets + QSS)
- SQLite (`sqlite3`)
- Простая MVC-подобная структура: `ui/pages` + `services` + `db`

## Структура
```text
tour_agency_ais/
  app.py
  requirements.txt
  README.md
  assets/
    styles.qss
    icons/
  src/
    ui/
      main_window.py
      login_window.py
      widgets.py
    pages/
      dashboard_page.py
      clients_page.py
      tours_page.py
      bookings_page.py
    db/
      database.py
      models.py
      seed.py
    services/
      auth_service.py
      clients_service.py
      tours_service.py
      bookings_service.py
    utils/
      validators.py
      formatters.py
```

## Установка и запуск
1. Перейдите в директорию проекта:
   ```bash
   cd tour_agency_ais
   ```
2. Создайте и активируйте виртуальное окружение (опционально, но рекомендуется).
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите приложение:
   ```bash
   python app.py
   ```

## Сборка `.exe` (Windows)
1. Откройте `cmd` в корне проекта.
2. Запустите:
   ```bat
   build_exe.bat
   ```
3. Готовый файл:
   ```text
   dist\TourAgencyAIS\TourAgencyAIS.exe
   ```

Если собираете вручную:
```bat
pyinstaller --noconfirm --clean --windowed --name TourAgencyAIS --add-data "assets;assets" app.py
```

Если `dist` не появился:
- проверьте, что в выводе нет `Build failed`
- проверьте наличие интернета (для установки `PyInstaller` и `PySide6`)
- попробуйте ручную сборку:
  ```bat
  py -3 -m venv .venv
  .venv\Scripts\activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements-dev.txt
  python -m PyInstaller --noconfirm --clean --windowed --name TourAgencyAIS --add-data "assets;assets" app.py
  ```

## Логин по умолчанию
- `admin`
- `admin`

## Примечания
- База создается автоматически:
  - в режиме разработки: `data/tour_agency.db`
  - в `.exe`-режиме: `%USERPROFILE%\\.tour_agency_ais\\tour_agency.db`
- Экспорт в PDF оставлен как optional и не входит в текущий MVP.
