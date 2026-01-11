# Quick Start Script for Stocks.AI Trading System
# This script sets up and starts the entire trading system

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Stocks.AI Trading System Setup" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✓ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Please edit .env and add your API keys before continuing!" -ForegroundColor Red
    Write-Host "   Required: POLYGON_API_KEY, ALPHA_VANTAGE_API_KEY, FINNHUB_API_KEY" -ForegroundColor Yellow
    Write-Host "   Optional: ZERODHA_API_KEY, ETRADE_CONSUMER_KEY (for trading)" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Press Enter to continue after editing .env, or Ctrl+C to exit"
}

Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Yellow
Write-Host "This may take 15-30 minutes on first run..." -ForegroundColor Gray
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker images built successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Services started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Initializing databases..." -ForegroundColor Yellow

# Initialize TimescaleDB
$sqlScript = @"
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    PRIMARY KEY (time, symbol, market)
);

SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS technical_features (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    rsi DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    sma_20 DOUBLE PRECISION,
    PRIMARY KEY (time, symbol, market)
);

SELECT create_hypertable('technical_features', 'time', if_not_exists => TRUE);
"@

$sqlScript | docker exec -i timescaledb psql -U trading_user -d trading_db

# Create additional databases
docker exec timescaledb psql -U trading_user -d trading_db -c "CREATE DATABASE IF NOT EXISTS mlflow_db;"
docker exec timescaledb psql -U trading_user -d trading_db -c "CREATE DATABASE IF NOT EXISTS airflow_db;"

Write-Host "✓ Databases initialized" -ForegroundColor Green

Write-Host ""
Write-Host "Initializing Airflow..." -ForegroundColor Yellow
docker exec airflow-webserver airflow db init 2>$null
docker exec airflow-webserver airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com 2>$null
Write-Host "✓ Airflow initialized" -ForegroundColor Green

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services are now running:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  📊 Grafana Dashboard:    http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
Write-Host "  🤖 MLflow UI:            http://localhost:5000" -ForegroundColor Cyan
Write-Host "  ⏰ Airflow:              http://localhost:8080 (admin/admin)" -ForegroundColor Cyan
Write-Host "  📈 Prometheus:           http://localhost:9090" -ForegroundColor Cyan
Write-Host "  🔮 Prediction API:       http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "  💼 Order Management API: http://localhost:8002/docs" -ForegroundColor Cyan
Write-Host "  ⚠️  Risk Management API:  http://localhost:8003/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  docker-compose ps              # Check service status" -ForegroundColor Gray
Write-Host "  docker-compose logs -f [service]  # View logs" -ForegroundColor Gray
Write-Host "  docker-compose restart [service]  # Restart a service" -ForegroundColor Gray
Write-Host "  docker-compose down            # Stop all services" -ForegroundColor Gray
Write-Host ""
Write-Host "Test the prediction API:" -ForegroundColor Yellow
Write-Host '  curl -X POST http://localhost:8001/predict -H "Content-Type: application/json" -d "{\"symbol\":\"AAPL\",\"market\":\"US\",\"asset_type\":\"stock\",\"horizon\":\"1d\"}"' -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see README.md and docs/" -ForegroundColor Cyan
Write-Host ""
