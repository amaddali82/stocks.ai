# API Documentation

## Overview

The Stocks.AI Trading Prediction System provides RESTful APIs for all major services:

- **Prediction Engine** (Port 8001): ML-powered trading predictions
- **Order Management** (Port 8002): Trade execution and broker integration
- **Risk Management** (Port 8003): Risk monitoring and compliance

## Authentication

All API endpoints support authentication via API keys (to be configured):

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8001/predict
```

---

## Prediction Engine API

Base URL: `http://localhost:8001`

### POST /predict

Generate trading prediction for a symbol.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "market": "US",
  "asset_type": "stock",
  "horizon": "1d",
  "model_type": "ensemble"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "prediction": "BUY",
  "confidence": 0.87,
  "target_price": 185.50,
  "expected_return": 0.035,
  "risk_score": 0.42,
  "features_used": {...},
  "model_used": "ensemble",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

### POST /predict/batch

Batch predictions for multiple symbols.

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "market": "US"
}
```

### GET /models

List all available models and their performance metrics.

**Response:**
```json
{
  "models": [
    {
      "name": "lstm_v1",
      "version": "1.0.0",
      "accuracy": 0.89,
      "last_trained": "2026-01-10T00:00:00Z",
      "status": "active"
    }
  ]
}
```

---

## Order Management API

Base URL: `http://localhost:8002`

### POST /orders

Place a new order.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "exchange": "NASDAQ",
  "action": "BUY",
  "quantity": 10,
  "order_type": "MARKET",
  "broker": "etrade"
}
```

**Response:**
```json
{
  "order_id": "ORD123456",
  "status": "OPEN",
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "filled_quantity": 0,
  "average_price": 0.0,
  "timestamp": "2026-01-11T10:30:00Z",
  "broker": "etrade",
  "message": "Order placed successfully"
}
```

### GET /orders/{order_id}

Get order status.

**Parameters:**
- `order_id`: Order ID
- `broker`: Broker type (zerodha or etrade)

### GET /positions

Get all open positions.

**Parameters:**
- `broker`: Broker type

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "quantity": 10,
    "average_price": 180.00,
    "current_price": 182.50,
    "pnl": 25.00,
    "pnl_percent": 1.39,
    "broker": "etrade"
  }
]
```

### GET /portfolio

Get portfolio summary with total P&L.

### GET /holdings

Get long-term holdings.

### GET /funds

Get available funds and buying power.

---

## Usage Examples

### Python

```python
import requests

# Get prediction
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
print(f"Signal: {prediction['prediction']}, Confidence: {prediction['confidence']}")

# Place order
if prediction['confidence'] > 0.75 and prediction['prediction'] == 'BUY':
    order_response = requests.post(
        'http://localhost:8002/orders',
        json={
            'symbol': 'AAPL',
            'exchange': 'NASDAQ',
            'action': 'BUY',
            'quantity': 10,
            'order_type': 'MARKET',
            'broker': 'etrade'
        }
    )
    print(f"Order placed: {order_response.json()['order_id']}")
```

### cURL

```bash
# Get prediction
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","market":"US","asset_type":"stock","horizon":"1d"}'

# Place order
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","exchange":"NASDAQ","action":"BUY","quantity":10,"order_type":"MARKET","broker":"etrade"}'

# Get positions
curl "http://localhost:8002/positions?broker=etrade"
```

---

## Rate Limits

- **Prediction API**: 100 requests/minute
- **Order API**: 50 requests/minute
- **Batch endpoints**: 10 requests/minute

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Service down |

## Webhooks

Configure webhooks for real-time notifications:

```python
{
  "event": "order.filled",
  "data": {
    "order_id": "ORD123456",
    "symbol": "AAPL",
    "filled_quantity": 10,
    "average_price": 182.50
  },
  "timestamp": "2026-01-11T10:35:00Z"
}
```

Supported events:
- `order.placed`
- `order.filled`
- `order.cancelled`
- `position.opened`
- `position.closed`
- `risk.alert`
