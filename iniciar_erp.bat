@echo off
REM Inicia el ERP Restaurant
REM Coloca este archivo en la carpeta del proyecto o crea un acceso directo

cd /d "%~dp0"
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo No se encontro el entorno virtual. Ejecuta setup.ps1 primero.
    pause
    exit /b 1
)
echo Iniciando ERP en http://127.0.0.1:5000/
echo Presiona Ctrl+C para detener.
echo.
python app.py
pause
