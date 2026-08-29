@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ===================================================
echo   Пакетная обработка видео (batch_process.py)
echo ===================================================
echo.
echo   Исходные видео: input\
echo   Результат:      output\
echo.

python batch_process.py
echo.
pause
