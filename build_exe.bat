@echo off
cd /d "%~dp0"
echo Building WAV2MP3.exe ...
python -m pip install --upgrade pyinstaller -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name WAV2MP3 ^
  --icon icon.ico --add-data "icon.ico;." ^
  --collect-all tkinterdnd2 --collect-all soundfile --collect-all lameenc ^
  wav2mp3.py
echo.
echo Done. EXE is in the "dist" folder: dist\WAV2MP3.exe
pause