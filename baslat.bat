@echo off
title Accura Finance
cd /d "%~dp0"
echo Accura Finance baslatiliyor...
python main.py
if errorlevel 1 (
    echo.
    echo Bir hata olustu!
    pause
)
