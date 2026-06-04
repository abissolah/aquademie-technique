@echo off
setlocal

cd /d "%~dp0aquademie-technique"
if errorlevel 1 (
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 (
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    exit /b 1
)

python manage.py runserver 0.0.0.0:8000

endlocal
