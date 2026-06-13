@echo off
title Repartition des menages - Motel Panoramique

echo ============================================
echo    Repartition des menages - Demarrage
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n est pas installe ou pas dans le PATH.
    echo.
    echo Telecharger Python : https://www.python.org/downloads/
    echo IMPORTANT : Cocher "Add Python to PATH" a l installation.
    echo.
    pause
    exit /b 1
)

echo Installation des dependances (premiere fois seulement)...
pip install -r "%~dp0requirements.txt" --quiet >nul 2>&1
echo OK.
echo.
echo Ouverture de l application dans sa fenetre...

start "" pythonw "%~dp0desktop_app.py"
exit /b 0
