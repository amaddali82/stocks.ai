#!/usr/bin/env pwsh
Write-Host "`n=== Fixing and Restarting Stock.AI Services ===`n" -ForegroundColor Cyan

Set-Location c:\stocks.ai

Write-Host "1. Stopping services..." -ForegroundColor Yellow
docker compose down

Write-Host "`n2. Rebuilding options-api with ML fix..." -ForegroundColor Yellow
docker compose build --no-cache options-api

Write-Host "`n3. Rebuilding UI..." -ForegroundColor Yellow
docker compose build --no-cache ui

Write-Host "`n4. Starting all services..." -ForegroundColor Yellow
docker compose up -d

Write-Host "`n5. Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "`n6. Checking service status..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-Object -First 10

Write-Host "`n7. Testing Options API..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
try {
    $health = Invoke-RestMethod "http://localhost:8004/health" -TimeoutSec 5
    Write-Host "✓ Options API: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "✗ Options API: Offline" -ForegroundColor Red
}

Write-Host "`n8. Testing UI..." -ForegroundColor Yellow
try {
    $ui = Invoke-WebRequest "http://localhost:3001" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ UI: Online (Status $($ui.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ UI: Offline" -ForegroundColor Red
}

Write-Host "`n=== Services Ready! ===`n" -ForegroundColor Cyan
Write-Host "Access your application at: http://localhost:3001" -ForegroundColor White
Write-Host "`nTo view logs:"
Write-Host "  docker logs options-api --tail 50" -ForegroundColor Gray
Write-Host "  docker logs stocks-ai-ui --tail 50" -ForegroundColor Gray
