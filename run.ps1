Set-Location -Path $PSScriptRoot
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting PeakCut Server..." -ForegroundColor Cyan
Write-Host "Open http://127.0.0.1:8765 in your browser" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m studio.server
