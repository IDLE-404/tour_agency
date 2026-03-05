@echo off
setlocal EnableExtensions

cd /d %~dp0

echo [1/5] Detecting Python...
set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PY_CMD=python"
  )
)

if "%PY_CMD%"=="" (
  echo ERROR: Python not found in PATH.
  goto :fail
)

echo Using: %PY_CMD%

echo [2/5] Creating virtual env...
if not exist .venv (
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :fail
)

echo [3/5] Installing dependencies...
call .venv\Scripts\activate
if errorlevel 1 goto :fail

python -m pip install --upgrade pip
if errorlevel 1 goto :fail

python -m pip install -r requirements-dev.txt
if errorlevel 1 goto :fail

echo [4/5] Building EXE with PyInstaller...
python -m PyInstaller --noconfirm --clean --windowed --name TourAgencyAIS --add-data "assets;assets" app.py
if errorlevel 1 goto :fail

echo [5/5] Done.
if exist dist\TourAgencyAIS\TourAgencyAIS.exe (
  echo EXE path: dist\TourAgencyAIS\TourAgencyAIS.exe
  goto :ok
)

echo ERROR: Build finished but EXE not found.
goto :fail

:ok
pause
exit /b 0

:fail
echo Build failed. Read errors above.
pause
exit /b 1
