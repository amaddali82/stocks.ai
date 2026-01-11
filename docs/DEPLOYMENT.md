# Deployment Guide

## Prerequisites

Before deploying the Stocks.AI Trading System, ensure you have:

- Docker Desktop (Windows) or Docker Engine + Docker Compose
- At least 16GB RAM
- 50GB free disk space
- Internet connection for pulling Docker images
- API keys for data providers (Polygon, Alpha Vantage, Finnhub, etc.)
- Broker credentials (Zerodha and/or E*TRADE)

## Local Development Deployment

### 1. Clone and Setup

```powershell
cd c:\stocks.ai
cp .env.example .env
```

Edit `.env` and add your API keys and credentials.

### 2. Build Docker Images

```powershell
docker-compose build
```

This will build all microservices. First build may take 15-30 minutes.

### 3. Start Services

```powershell
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f prediction-engine
```

### 4. Initialize Databases

```powershell
# Create database schemas
docker exec -it timescaledb psql -U trading_user -d trading_db <<EOF
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
    ema_12 DOUBLE PRECISION,
    PRIMARY KEY (time, symbol, market)
);

SELECT create_hypertable('technical_features', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    broker TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
EOF

# Initialize MLflow database
docker exec -it timescaledb psql -U trading_user -d trading_db -c "CREATE DATABASE mlflow_db;"
docker exec -it timescaledb psql -U trading_user -d trading_db -c "CREATE DATABASE airflow_db;"

# Initialize Airflow
docker exec -it airflow-webserver airflow db init
docker exec -it airflow-webserver airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 5. Verify Deployment

Access the services:

- Grafana: http://localhost:3000 (admin/admin)
- MLflow: http://localhost:5000
- Airflow: http://localhost:8080 (admin/admin)
- Prediction API: http://localhost:8001/docs
- Order Management API: http://localhost:8002/docs

### 6. Test the System

```powershell
# Test prediction endpoint
curl -X POST http://localhost:8001/predict `
  -H "Content-Type: application/json" `
  -d '{"symbol":"AAPL","market":"US","asset_type":"stock","horizon":"1d"}'

# Check service health
docker-compose ps
docker-compose logs --tail=50 data-ingestion
```

## Production Deployment (Kubernetes)

### 1. Setup Kubernetes Cluster

```powershell
# Install kubectl
choco install kubernetes-cli

# Verify cluster connection
kubectl cluster-info
kubectl get nodes
```

### 2. Create Kubernetes Resources

```powershell
# Create namespace
kubectl create namespace trading-system

# Create secrets
kubectl create secret generic trading-secrets \
  --from-env-file=.env \
  -n trading-system

# Deploy services
kubectl apply -f k8s/ -n trading-system
```

### 3. Configure Persistent Storage

```yaml
# k8s/persistent-volumes.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: timescaledb-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mlflow-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

### 4. Deploy with Helm

```powershell
# Install Helm
choco install kubernetes-helm

# Add chart repository
helm repo add trading-system ./helm

# Install chart
helm install trading-system ./helm/trading-system \
  --namespace trading-system \
  --values helm/values-production.yaml
```

## Cloud Deployment (AWS)

### 1. Setup AWS Infrastructure

```powershell
# Install AWS CLI
choco install awscli

# Configure credentials
aws configure

# Create EKS cluster
aws eks create-cluster \
  --name trading-system-cluster \
  --region us-east-1 \
  --kubernetes-version 1.28 \
  --role-arn arn:aws:iam::YOUR_ACCOUNT:role/eks-service-role
```

### 2. Deploy to EKS

```powershell
# Update kubeconfig
aws eks update-kubeconfig \
  --name trading-system-cluster \
  --region us-east-1

# Deploy application
kubectl apply -f k8s/ -n trading-system

# Setup ingress
kubectl apply -f k8s/ingress.yaml
```

### 3. Configure Auto-Scaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prediction-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prediction-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring Setup

### 1. Configure Prometheus

```powershell
# Deploy Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Create ServiceMonitors
kubectl apply -f k8s/monitoring/
```

### 2. Setup Grafana Dashboards

```powershell
# Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n trading-system

# Import dashboards from config/grafana/dashboards/
```

## Backup and Recovery

### Database Backup

```powershell
# Backup TimescaleDB
docker exec timescaledb pg_dump -U trading_user trading_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i timescaledb psql -U trading_user trading_db < backup_20260111.sql
```

### Model Backup

```powershell
# Backup ML models
docker cp prediction-engine:/models ./models_backup_$(date +%Y%m%d)

# Restore
docker cp ./models_backup_20260111 prediction-engine:/models
```

## Performance Tuning

### 1. Database Optimization

```sql
-- Create indexes for faster queries
CREATE INDEX CONCURRENTLY idx_market_data_symbol_time ON market_data(symbol, time DESC);
CREATE INDEX CONCURRENTLY idx_features_symbol_time ON technical_features(symbol, time DESC);

-- Set compression
ALTER TABLE market_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'symbol, market'
);

SELECT add_compression_policy('market_data', INTERVAL '7 days');
```

### 2. Kafka Tuning

```yaml
# docker-compose.yml (Kafka section)
environment:
  KAFKA_NUM_PARTITIONS: 10
  KAFKA_DEFAULT_REPLICATION_FACTOR: 3
  KAFKA_LOG_RETENTION_HOURS: 168
  KAFKA_LOG_SEGMENT_BYTES: 1073741824
```

### 3. Redis Configuration

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 300
```

## Troubleshooting

### Service Won't Start

```powershell
# Check logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name

# Rebuild if needed
docker-compose up -d --build service-name
```

### Database Connection Issues

```powershell
# Check database is running
docker-compose ps timescaledb

# Test connection
docker exec -it timescaledb psql -U trading_user -d trading_db -c "SELECT 1;"

# Check environment variables
docker-compose exec prediction-engine env | grep DB
```

### High Memory Usage

```powershell
# Check resource usage
docker stats

# Restart services with memory limits
docker-compose down
docker-compose up -d
```

## Security Best Practices

1. **Use environment variables** for all secrets
2. **Enable SSL/TLS** for all external communications
3. **Implement rate limiting** on APIs
4. **Regular security updates** for Docker images
5. **Use separate databases** for different environments
6. **Enable audit logging** for all trades
7. **Implement IP whitelisting** for broker APIs

## Maintenance

### Daily Tasks
- Monitor system health via Grafana
- Check for failed orders
- Review prediction accuracy

### Weekly Tasks
- Backup databases and models
- Review and rotate logs
- Update API keys if needed

### Monthly Tasks
- Retrain ML models
- Review and optimize database queries
- Update dependencies and Docker images
- Conduct security audits
