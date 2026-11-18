@echo off
title PeakCut Server
cd /d "%~dp0"
echo ===================================================
echo Starting PeakCut Server...
echo Open http://127.0.0.1:8765 in your browser
echo Press Ctrl+C in this window to stop the server
echo ===================================================
".venv\Scripts\python.exe" -m studio.server
pause
