# System Architecture

## Overview

Stocks.AI is a microservices-based trading prediction system designed for high performance, scalability, and reliability.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                         External Data Sources                        │
│  Polygon.io │ Alpha Vantage │ Finnhub │ Zerodha │ E*TRADE │ NSE/BSE │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Data Ingestion Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ US Market    │  │ India Market │  │ News & Sentiment         │ │
│  │ Connector    │  │ Connector    │  │ Connector                │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────────────┘ │
└─────────┼──────────────────┼───────────────────┼───────────────────┘
          │                  │                   │
          └──────────────────┴───────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                   Message Broker & Streaming                        │
│  ┌──────────────────────────┐  ┌────────────────────────────────┐ │
│  │ Apache Kafka             │  │ Redis Streams                  │ │
│  │ - market.us.stocks       │  │ - Real-time cache              │ │
│  │ - market.india.stocks    │  │ - Session storage              │ │
│  │ - news.company           │  │ - Feature cache                │ │
│  │ - sentiment.scores       │  │                                │ │
│  └──────────────────────────┘  └────────────────────────────────┘ │
└──────────────┬──────────────────────────┬──────────────────────────┘
               │                          │
    ┌──────────┴──────────┐      ┌───────┴──────────┐
    │                     │      │                  │
    ▼                     ▼      ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Feature       │  │   Prediction    │  │ Order Mgmt &    │
│  Engineering    │  │    Engine       │  │ Risk Mgmt       │
│                 │  │                 │  │                 │
│ - TA-Lib        │  │ - LSTM Models   │  │ - Zerodha API   │
│ - pandas-ta     │  │ - Transformers  │  │ - E*TRADE API   │
│ - FinBERT       │  │ - GNN Models    │  │ - Risk Checks   │
│ - VADER         │  │ - Ensemble      │  │ - Compliance    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         └────────────────────┴─────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Persistence Layer                              │
│  ┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ TimescaleDB      │  │ Redis        │  │ MLflow Registry    │   │
│  │ - Time series    │  │ - Cache      │  │ - Model versions   │   │
│  │ - Market data    │  │ - Sessions   │  │ - Experiments      │   │
│  │ - Features       │  │ - Real-time  │  │ - Artifacts        │   │
│  └──────────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                  Monitoring & Orchestration                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Prometheus   │  │ Grafana      │  │ Apache Airflow           │ │
│  │ - Metrics    │  │ - Dashboards │  │ - Workflow automation    │ │
│  │ - Alerts     │  │ - Alerts     │  │ - Scheduled retraining   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Ingestion Layer

**Purpose**: Collect real-time and historical data from multiple sources

**Components**:
- **US Market Connector**: Polygon.io, Alpha Vantage for US stocks/options
- **India Market Connector**: Zerodha Kite, NSE/BSE for Indian markets
- **News Sentiment Connector**: Finnhub, NewsAPI for news and sentiment

**Technologies**: Python, WebSockets, REST APIs, asyncio

**Key Features**:
- Real-time WebSocket streaming
- Rate limiting and retry logic
- Data validation and normalization
- Multi-source aggregation

### 2. Message Broker

**Purpose**: Decouple services and enable scalable data streaming

**Components**:
- **Apache Kafka**: Persistent message streaming
- **Redis Streams**: Real-time caching and pub/sub

**Topics**:
- `market.us.stocks.realtime`: US stock prices
- `market.india.stocks.realtime`: Indian stock prices
- `market.*.options.openinterest`: Options OI data
- `news.company`: Company-specific news
- `sentiment.scores`: Sentiment analysis results

### 3. Feature Engineering Service

**Purpose**: Compute technical indicators and sentiment features

**Features Generated**:
- **Technical**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
- **Volume**: OBV, VWAP, volume ratios
- **Sentiment**: VADER scores, FinBERT predictions
- **Events**: M&A, earnings, macro indicators

**Technologies**: pandas, TA-Lib, pandas-ta, FinBERT, VADER

### 4. Prediction Engine

**Purpose**: Generate trading signals using ML models

**Models**:
1. **LSTM Networks**: Sequence-based time series prediction
2. **Transformers**: Multi-horizon attention-based forecasting
3. **GNNs**: Cross-asset correlation modeling
4. **Ensemble**: Weighted combination of models

**APIs**:
- `POST /predict`: Single symbol prediction
- `POST /predict/batch`: Multiple symbols
- `GET /models`: List available models
- `POST /models/{name}/train`: Trigger retraining

**Technologies**: PyTorch, TensorFlow, scikit-learn, MLflow

### 5. Order Management System

**Purpose**: Execute trades with broker integration

**Features**:
- Order placement (market, limit, stop-loss)
- Order status tracking
- Position management
- Portfolio monitoring

**Broker Integrations**:
- **Zerodha Kite Connect**: Indian markets (NSE, BSE, F&O)
- **E*TRADE API**: US markets (NYSE, NASDAQ)

**APIs**:
- `POST /orders`: Place order
- `GET /orders/{id}`: Get order status
- `GET /positions`: List positions
- `GET /portfolio`: Portfolio summary

### 6. Risk Management Service

**Purpose**: Monitor risk and enforce compliance

**Checks**:
- Position size limits
- Daily loss limits
- Portfolio concentration
- Margin requirements
- Regulatory compliance

**Metrics**:
- Value at Risk (VaR)
- Maximum drawdown
- Portfolio beta
- Sharpe ratio

### 7. Monitoring Stack

**Components**:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Real-time dashboards and visualization
- **Apache Airflow**: Workflow orchestration and scheduling

**Dashboards**:
1. Trading Performance (P&L, Sharpe, win rate)
2. Model Performance (accuracy, precision, recall)
3. System Health (CPU, memory, latency)
4. Risk Metrics (VaR, drawdown, exposure)

## Data Flow

### Real-time Trading Flow

```
1. Market Data → Kafka → Feature Engineering
2. Feature Engineering → Redis Cache + TimescaleDB
3. Feature Engineering → Kafka → Prediction Engine
4. Prediction Engine → Risk Management → Order Management
5. Order Management → Broker API → Order Execution
6. All Services → Prometheus → Grafana
```

### Batch Training Flow

```
1. Airflow triggers data collection
2. Historical data fetched from TimescaleDB
3. Features computed in batch
4. Model training with MLflow tracking
5. Model evaluation and registration
6. A/B testing deployment
7. Promotion to production if successful
```

## Scalability

### Horizontal Scaling

- **Kafka**: Add partitions and consumers
- **Prediction Engine**: Add replicas with load balancer
- **TimescaleDB**: Sharding by symbol/market
- **Kubernetes**: Auto-scaling based on CPU/memory

### Performance Optimization

- **Redis Caching**: Sub-millisecond feature retrieval
- **Kafka Batching**: Reduce network overhead
- **Model Quantization**: Faster inference
- **Connection Pooling**: Reduce broker API latency

## High Availability

### Redundancy

- **Kafka**: 3-node cluster with replication
- **Redis**: Redis Sentinel for failover
- **TimescaleDB**: Streaming replication
- **Services**: Multiple replicas with health checks

### Disaster Recovery

- **Automated Backups**: Daily database backups
- **Model Versioning**: All models versioned in MLflow
- **Configuration as Code**: Infrastructure in Git
- **Multi-region Deployment**: Active-passive setup

## Security

### Authentication & Authorization

- API key authentication for all services
- OAuth2 for broker integrations
- Role-based access control (RBAC)
- JWT tokens for service-to-service communication

### Data Security

- Encryption at rest (database)
- TLS/SSL for all communications
- Secrets management with environment variables
- Audit logging for all trades

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| Data Ingestion | Python, asyncio, WebSockets | Real-time data streaming |
| Message Broker | Kafka, Redis | Decoupled communication |
| Feature Engineering | pandas, TA-Lib, FinBERT | Feature computation |
| ML/AI | PyTorch, TensorFlow, MLflow | Model training & inference |
| Storage | TimescaleDB, Redis | Time-series & caching |
| Orchestration | Docker, Kubernetes, Airflow | Deployment & automation |
| Monitoring | Prometheus, Grafana | Observability |
| Trading | Zerodha, E*TRADE APIs | Order execution |

## Design Principles

1. **Microservices**: Independent, loosely-coupled services
2. **Event-Driven**: Asynchronous communication via Kafka
3. **Scalability**: Horizontal scaling for all components
4. **Fault Tolerance**: Graceful degradation and retry logic
5. **Observability**: Comprehensive metrics and logging
6. **Security**: Defense in depth, least privilege
7. **Testability**: Unit, integration, and end-to-end tests
8. **Reproducibility**: Containerized, version-controlled

## Future Enhancements

1. **GraphQL API**: Flexible data querying
2. **Reinforcement Learning**: Deep Q-Networks for trading
3. **Multi-cloud Deployment**: AWS, Azure, GCP support
4. **Mobile App**: Real-time monitoring on mobile
5. **Advanced NLP**: FinGPT integration for news analysis
6. **Social Media Integration**: Twitter sentiment analysis
7. **Options Pricing**: Black-Scholes and Greeks calculations
8. **Portfolio Optimization**: Modern Portfolio Theory integration
