@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ===================================================
echo   Запуск графического интерфейса (GUI)
echo ===================================================
echo.

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] Приложение завершилось с кодом ошибки %ERRORLEVEL%.
    pause
)
