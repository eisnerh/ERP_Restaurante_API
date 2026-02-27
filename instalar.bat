@echo off
REM Instalador ERP Raul Castano - Doble clic para instalar
cd /d "%~dp0"
echo.
echo Ejecutando instalador...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0instalador.ps1"
pause
