Write-Host "Restarting Options API..." -ForegroundColor Cyan
Set-Location c:\stocks.ai
docker compose restart options-api
Start-Sleep -Seconds 10
Write-Host "`nChecking service status..." -ForegroundColor Yellow
docker ps | Select-String "options-api"
Write-Host "`nRecent logs:" -ForegroundColor Yellow
docker logs options-api --tail 20
Write-Host "`nTesting API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod "http://localhost:8004/health" -TimeoutSec 5
    Write-Host "✓ API is online!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor White
} catch {
    Write-Host "✗ API health check failed" -ForegroundColor Red
}
