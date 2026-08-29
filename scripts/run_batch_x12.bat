@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==========================================================
echo   RUN_BATCH_X12: 12 АККАУНТОВ x 6 РОЛИКОВ (72 ВИДЕО)
echo ==========================================================
echo.
echo   Исходные видео : input\
echo   Результат      : output\account_01 ... account_12\
echo.

python batch_x12.py
echo.
pause
