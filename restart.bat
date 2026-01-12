@echo off
echo.
echo === Restarting Stock.AI Services ===
echo.
cd /d c:\stocks.ai
echo 1. Stopping services...
docker compose down
echo.
echo 2. Starting services...
docker compose up -d
echo.
echo 3. Waiting 15 seconds for startup...
timeout /t 15 /nobreak >nul
echo.
echo 4. Service Status:
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr /C:"ui" /C:"api"
echo.
echo === Services Ready! ===
echo.
echo Access: http://localhost:3001
echo.
pause
