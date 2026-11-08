bat_content = """@echo off
TITLE AeroHydro-Twin Launcher
COLOR 0A

echo ===================================================
echo     AeroHydro-Twin: Flood Management Console
echo ===================================================
echo Starting local Flask backend server...
echo.

:: Navigate to current directory
cd /d "%~dp0"

:: Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.x and check "Add Python to PATH".
    pause
    exit /b
)

:: Launch app.py
echo Server launching on http://127.0.0.1:5000 ...
echo Press Ctrl+C in this window to stop the server.
echo.

python app.py

pause
"""

file_path = "run_aerohydro_twin.bat"
with open(file_path, "w") as f:
    f.write(bat_content)

print(f"Generated {file_path}")