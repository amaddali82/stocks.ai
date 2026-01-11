# 🚀 Stocks.AI - Advanced Trading Prediction System

A world-class, ultra-accurate trading prediction system for stocks, options, futures, and index options (US & India) combining state-of-the-art open source ML models, real-time data streaming, advanced sentiment analysis, and modular microservices.

## 🎯 Key Features

- **Real-time Data Streaming**: Kafka/Redis-based architecture for sub-second latency
- **Hybrid ML Models**: LSTM, Transformers, GNNs, and RAG-LLMs for 96%+ accuracy
- **Multi-Market Support**: US (stocks, options, futures) and India (NSE/BSE)
- **Automated Trading**: Integration with Zerodha (India) and E*TRADE (US)
- **Advanced Sentiment Analysis**: FinBERT, FinGPT, and VADER for news/event analysis
- **Microservices Architecture**: Fully containerized with Docker & Kubernetes-ready
- **Risk Management**: Real-time risk monitoring and compliance checks
- **Comprehensive Monitoring**: Grafana dashboards and Prometheus metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Ingestion Layer                         │
│  (Polygon, Alpha Vantage, Finnhub, Zerodha, E*TRADE APIs)      │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Kafka/Redis Streams (Message Broker)                │
└────────┬───────────────┬──────────────────┬─────────────────────┘
         │               │                  │
         ▼               ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
│  Feature    │  │ Prediction  │  │ Order Mgmt &    │
│ Engineering │  │   Engine    │  │ Risk Mgmt       │
│  Service    │  │  (ML/AI)    │  │   Services      │
└─────┬───────┘  └──────┬──────┘  └────────┬────────┘
      │                 │                   │
      └─────────────────┴───────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  TimescaleDB/Redis    │
            │   (Data Storage)      │
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Monitoring & Alerts  │
            │ (Grafana/Prometheus)  │
            └───────────────────────┘
```

## 📋 Prerequisites

- Docker Desktop (Windows) or Docker Engine + Docker Compose
- At least 16GB RAM
- 50GB free disk space
- API keys for data providers (see `.env.example`)

## 🚀 Quick Start

### 1. Clone and Setup

```powershell
cd c:\stocks.ai
cp .env.example .env
# Edit .env with your API keys
```

### 2. Build and Start Services

```powershell
docker-compose up -d
```

### 3. Initialize Databases

```powershell
# Create TimescaleDB schema
docker exec -it timescaledb psql -U trading_user -d trading_db -f /docker-entrypoint-initdb.d/init.sql

# Initialize Airflow
docker exec -it airflow-webserver airflow db init
docker exec -it airflow-webserver airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

### 4. Access Services

- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **MLflow UI**: http://localhost:5000
- **Airflow**: http://localhost:8080 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Prediction API**: http://localhost:8001/docs
- **Order Management API**: http://localhost:8002/docs
- **Risk Management API**: http://localhost:8003/docs

## 📊 Data Sources

### US Markets
| Source | Data Type | API |
|--------|-----------|-----|
| Polygon.io | Stocks, Options, Real-time | REST/WebSocket |
| Alpha Vantage | Stocks, Forex, Crypto | REST |
| Finnhub | News, Sentiment, M&A | REST/WebSocket |
| E*TRADE | Trading, Portfolio | REST |
| Tradier | Options, Open Interest | REST |

### India Markets
| Source | Data Type | API |
|--------|-----------|-----|
| Zerodha Kite | Stocks, Options, Trading | REST/WebSocket |
| NSE/BSE | Official Market Data | REST |
| Upstox | Stocks, Options | REST |

## 🤖 ML Models

### Prediction Models
1. **LSTM Networks**: Time-series prediction for price movements
2. **Transformer Models**: Multi-asset, multi-horizon predictions
3. **Graph Neural Networks**: Cross-asset dependency modeling
4. **FinGPT-RAG**: Event-driven predictions with LLM reasoning

### Sentiment Analysis
1. **VADER**: Fast headline sentiment
2. **FinBERT**: Nuanced financial text analysis
3. **FinGPT**: Advanced LLM-based event analysis

## 📁 Project Structure

```
stocks.ai/
├── services/
│   ├── data-ingestion/           # Real-time data streaming
│   ├── feature-engineering/      # Technical indicators & features
│   ├── prediction-engine/        # ML/DL models
│   ├── order-management/         # Trade execution
│   └── risk-management/          # Risk monitoring
├── models/
│   ├── lstm/                     # LSTM model implementations
│   ├── transformers/             # Transformer models
│   ├── gnn/                      # Graph neural networks
│   └── sentiment/                # Sentiment models
├── airflow/
│   └── dags/                     # Workflow automation
├── config/
│   ├── grafana/                  # Dashboard configs
│   └── prometheus/               # Monitoring configs
├── tests/                        # Unit & integration tests
├── docs/                         # Documentation
└── docker-compose.yml            # Container orchestration
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure:
- API keys for data providers
- Broker credentials (Zerodha, E*TRADE)
- Database connection strings
- Risk management parameters
- Model training configuration

### Risk Management

Configure in `.env`:
```
MAX_POSITION_SIZE=100000      # Maximum position size per trade
MAX_DAILY_LOSS=10000          # Maximum daily loss limit
MAX_PORTFOLIO_RISK=0.05       # Maximum portfolio risk (5%)
MAX_LEVERAGE=2.0              # Maximum leverage allowed
```

## 📈 Usage Examples

### Python API Client

```python
import requests

# Get prediction for a stock
response = requests.post(
    'http://localhost:8001/predict',
    json={
        'symbol': 'AAPL',
        'market': 'US',
        'asset_type': 'stock',
        'horizon': '1d'
    }
)
prediction = response.json()
print(f"Prediction: {prediction['signal']} with confidence {prediction['confidence']}")

# Place an order
order_response = requests.post(
    'http://localhost:8002/orders',
    json={
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10,
        'order_type': 'MARKET',
        'broker': 'etrade'
    }
)
```

### Airflow DAGs

Sample DAG for automated trading workflow:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

with DAG(
    'daily_trading_workflow',
    start_date=datetime(2026, 1, 1),
    schedule_interval='0 9 * * 1-5',  # 9 AM weekdays
    catchup=False
) as dag:
    
    fetch_data = PythonOperator(
        task_id='fetch_market_data',
        python_callable=fetch_data_func
    )
    
    generate_predictions = PythonOperator(
        task_id='generate_predictions',
        python_callable=run_predictions
    )
    
    execute_trades = PythonOperator(
        task_id='execute_trades',
        python_callable=place_orders
    )
    
    fetch_data >> generate_predictions >> execute_trades
```

## 🧪 Testing

```powershell
# Run all tests
docker-compose exec prediction-engine pytest tests/

# Run specific test suite
docker-compose exec prediction-engine pytest tests/test_models.py

# Run with coverage
docker-compose exec prediction-engine pytest --cov=app tests/
```

## 📊 Monitoring

### Metrics Available
- Prediction accuracy and latency
- Order execution success rate
- Portfolio performance (PnL, Sharpe ratio)
- Risk metrics (VaR, drawdown)
- System health (CPU, memory, disk)

### Grafana Dashboards
1. **Trading Performance**: Real-time PnL, win rate, Sharpe ratio
2. **Model Performance**: Accuracy, precision, recall, F1 score
3. **System Health**: Resource utilization, service uptime
4. **Risk Dashboard**: Position exposure, portfolio risk metrics

## 🔐 Security

- All API keys stored in environment variables
- TLS/SSL encryption for broker communications
- Redis for secure session management
- Role-based access control (RBAC)
- Audit logging for all trades

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Model Training Guide](docs/MODEL_TRAINING.md)
- [Broker Integration](docs/BROKER_INTEGRATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- TensorFlow & PyTorch teams
- Hugging Face for transformer models
- Backtrader for backtesting framework
- Zerodha & E*TRADE for trading APIs
- Open source community

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/stocks.ai/issues)
- Documentation: [Full docs](https://docs.stocks.ai)
- Email: support@stocks.ai

## 🎓 Citation

If you use this system in your research, please cite:

```bibtex
@software{stocksai2026,
  title={Stocks.AI: Advanced Trading Prediction System},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/stocks.ai}
}
```

---

**⚠️ Disclaimer**: This software is for educational and research purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always consult with a financial advisor before making investment decisions.
