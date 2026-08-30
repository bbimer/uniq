@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==========================================================
echo   ГЕНЕРАЦИЯ: 6 УНИКОВ RU + 12 УНИКОВ ENG (18 РОЛИКОВ)
echo ==========================================================
echo.
echo   Исходники : input\RU.mp4 и input\ENG.mp4
echo   Результат : output\RU\ и output\ENG\
echo.

python batch_run_ru_eng.py
echo.
pause
