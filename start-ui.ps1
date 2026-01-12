# Start Options API and UI Services
Write-Host "=== Starting Options API and UI ===" -ForegroundColor Cyan

# Navigate to project directory
Set-Location c:\stocks.ai

# Build and start the services
Write-Host "`nBuilding and starting options-api service..." -ForegroundColor Yellow
docker-compose up -d --build options-api

Start-Sleep -Seconds 5

Write-Host "`nBuilding and starting ui service..." -ForegroundColor Yellow
docker-compose up -d --build ui

Start-Sleep -Seconds 3

# Show container status
Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "options-api|ui|stocks"

# Check Options API logs
Write-Host "`n=== Options API Logs (last 15 lines) ===" -ForegroundColor Cyan
docker logs options-api --tail 15

# Check UI logs
Write-Host "`n=== UI Logs (last 15 lines) ===" -ForegroundColor Cyan
docker logs stocks-ai-ui --tail 15

Write-Host "`n=== Services Started ===" -ForegroundColor Green
Write-Host "Options API: http://localhost:8004" -ForegroundColor White
Write-Host "UI: http://localhost:3001" -ForegroundColor White
Write-Host "`nUse 'docker logs <container-name>' to view logs" -ForegroundColor Gray
