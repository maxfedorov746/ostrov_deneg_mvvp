@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
if defined OSTROV_PYTHON (
  "%OSTROV_PYTHON%" run_demo.py %*
  goto end
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  py -3.12 run_demo.py %*
  goto end
)
py -3 --version >nul 2>&1
if not errorlevel 1 (
  py -3 run_demo.py %*
  goto end
)
python --version >nul 2>&1
if not errorlevel 1 (
  python run_demo.py %*
  goto end
)
echo Нужен Python 3.12 или новее. Установите его и повторите запуск.
exit /b 1
:end
if errorlevel 1 pause
