@echo off
cd /d "%~dp0"
python -c "import lameenc, soundfile, numpy, tkinterdnd2" 2>nul
if errorlevel 1 (
    echo Installing required packages (first run only)...
    python -m pip install --upgrade lameenc soundfile numpy tkinterdnd2
    if errorlevel 1 (
        echo.
        echo [ERROR] Python not found or install failed.
        echo Install Python from https://www.python.org/downloads/ ^(check "Add python.exe to PATH"^)
        pause
        exit /b 1
    )
)
start "" pythonw "%~dp0wav2mp3.py" %*
