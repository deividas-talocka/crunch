@echo off
rem Starts Crunch and opens it in the browser. Closing this window stops Crunch.
cd /d "%~dp0"
title Crunch

rem Already running: just open it.
netstat -ano | findstr /r /c:":5000 .*LISTENING" >nul
if %errorlevel%==0 (
    start "" http://localhost:5000
    exit /b
)

.venv\Scripts\python.exe --version >nul 2>&1
if errorlevel 1 (
    echo Crunch can't start because Python is missing or has moved.
    echo Install Python 3.12, then try again. See README.md for setup steps.
    pause
    exit /b 1
)

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" http://localhost:5000"
.venv\Scripts\python.exe app.py
