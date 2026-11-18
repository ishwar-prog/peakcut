@echo off
setlocal
echo ===================================================
echo  Setting up PeakCut on Windows
echo ===================================================

where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] ffmpeg not in current PATH. Checking WinGet/Scoop...
    echo If needed, run: winget install Gyan.FFmpeg
) else (
    echo [✓] ffmpeg found
)

if not exist ".venv" (
    echo --> Creating virtual environment...
    py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || python -m venv .venv
)

call .venv\Scripts\activate.bat
echo --> Installing Python dependencies...
pip install -r requirements.txt

echo --> Checking speech model...
python -m studio.fetch_model

echo ===================================================
echo  [✓] PeakCut Setup complete!
echo  - To start Web Dashboard: run.bat
echo  - To clip directly: python clip.py ^<video_url_or_file^>
echo ===================================================
pause
