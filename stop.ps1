# Stop Script for Stocks.AI Trading System

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Stopping Stocks.AI Trading System" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping all services..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All services stopped" -ForegroundColor Green
} else {
    Write-Host "✗ Error stopping services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "To completely remove all data (including databases):" -ForegroundColor Yellow
Write-Host "  docker-compose down -v" -ForegroundColor Gray
Write-Host ""
Write-Host "To start again, run: .\start.ps1" -ForegroundColor Cyan
Write-Host ""
