@echo off
REM Cambia a la carpeta del programa sin depender de la ubicación de cada PC.
cd /d "%~dp0autopark"

REM Inicia la aplicación usando el Python instalado en Windows.
python main.py

REM Si ocurre un error, mantiene la ventana abierta para poder leerlo.
if errorlevel 1 pause
