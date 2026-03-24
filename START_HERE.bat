@echo off
title GenAI SQL Assistant
color 0B
echo.
echo  GenAI SQL Assistant  ^|  Starting...
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Install from https://python.org ^(tick Add to PATH^)
    pause
    exit /b 1
)
python "%~dp0launcher.py"
if errorlevel 1 pause
