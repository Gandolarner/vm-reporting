@echo off
cd /d C:\Users\clausm\vm-reporting

echo Starte Entwicklungsumgebung fuer vm-reporting...
echo.

call .venv\Scripts\activate.bat

echo Virtuelle Umgebung wurde aktiviert.
echo Projektordner: %CD%
echo.

python -m app.main --help

echo.
echo Du kannst jetzt mit dem Projekt weiterarbeiten.
echo Beispiele:
echo   python -m app.main collect
echo   python -m app.main aggregate 2026-05
echo   python -m app.main report 2026-05
echo.

cmd /k