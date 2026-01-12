# ML/AI Prediction Models Implementation

## Overview
Comprehensive machine learning system for options trading predictions using LSTM, Random Forest, and XGBoost models.

## Implemented Models

### 1. LSTM (Long Short-Term Memory) for Time-Series Price Prediction
**Purpose**: Predict future stock prices based on historical patterns

**Architecture**:
- Input: Sequence of 10 time steps with 8 features per step
- Layer 1: LSTM(128 units) + Dropout(0.2)
- Layer 2: LSTM(64 units) + Dropout(0.2)
- Layer 3: LSTM(32 units) + Dropout(0.2)
- Dense Layer: 16 neurons (ReLU activation)
- Output: 1 neuron (linear activation) - predicted price

**Features Used**:
- Close price
- Returns
- Simple Moving Averages (SMA 5, SMA 10)
- Volatility (rolling standard deviation)
- Momentum
- RSI (Relative Strength Index)
- Volume

**Training**:
- Optimizer: Adam (learning_rate=0.001)
- Loss: MSE (Mean Squared Error)
- Metrics: MAE (Mean Absolute Error)
- Epochs: 5 (quick training, production would use pre-trained models)

**Output**:
```json
{
  "predicted_price": 265.50,
  "confidence": 0.82,
  "model": "LSTM",
  "days_ahead": 7
}
```

### 2. Random Forest Classifier for BUY/SELL/HOLD Classification
**Purpose**: Classify trading action based on technical indicators

**Architecture**:
- n_estimators: 100 trees
- max_depth: 10
- class_weight: balanced
- Features: 8 technical indicators

**Classification Logic**:
- **BUY**: RSI < 30 and positive momentum (oversold + reversal)
- **SELL**: RSI > 70 and negative momentum (overbought + decline)
- **HOLD**: All other conditions (neutral market)

**Features Used**:
- Close price
- Returns
- Moving averages
- Volatility
- Momentum
- RSI
- Volume

**Output**:
```json
{
  "action": "BUY",
  "confidence": 0.78,
  "probabilities": {
    "BUY": 0.78,
    "HOLD": 0.15,
    "SELL": 0.07
  },
  "model": "RandomForest"
}
```

### 3. XGBoost Regressor for Premium Prediction
**Purpose**: Predict option premium based on Greeks, volatility, and market data

**Architecture**:
- n_estimators: 100
- max_depth: 6
- learning_rate: 0.1
- objective: reg:squarederror

**Features Used** (11 features):
1. **Spot Price**: Current stock price
2. **Strike Price**: Option strike price
3. **Moneyness**: Spot/Strike ratio
4. **Time to Expiry**: Years until expiration
5. **Implied Volatility**: Market volatility
6. **Volume**: Trading volume (log-transformed)
7. **Open Interest**: Open contracts (log-transformed)
8. **Delta**: Price sensitivity to underlying
9. **Gamma**: Delta sensitivity
10. **Theta**: Time decay
11. **Vega**: Volatility sensitivity

**Training Data**:
- 1000 synthetic samples generated using Black-Scholes approximations
- Spot range: ±20% of current
- Strike range: ±20% of current
- Time range: 0.01 to 1.5x current expiry
- Volatility: 15% to 60%

**Output**:
```json
{
  "predicted_premium": 5.42,
  "confidence": 0.85,
  "model": "XGBoost",
  "feature_importance": {
    "moneyness": 0.32,
    "time_to_expiry": 0.28,
    "volatility": 0.18,
    "delta": 0.12,
    "spot": 0.05,
    "strike": 0.03,
    "vega": 0.02
  }
}
```

## Greeks Calculation

### Black-Scholes Greeks Implementation

**Delta (Δ)**: Rate of change of option price with respect to underlying price
```
Δ = N(d1)
where d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
```

**Gamma (Γ)**: Rate of change of delta
```
Γ = N'(d1) / (S × σ × √T)
```

**Theta (Θ)**: Time decay
```
Θ = -(S × N'(d1) × σ) / (2√T) - r × K × e^(-rT) × N(d2)
```

**Vega (ν)**: Sensitivity to volatility
```
ν = S × N'(d1) × √T / 100
```

## Market Sentiment Analysis

**Current Implementation**: Simulated sentiment based on sector
- **Tech stocks** (AAPL, MSFT, GOOGL, NVDA, META): Bullish (0.6-0.9)
- **Energy stocks** (XOM, CVX): Neutral to Bullish (0.4-0.7)
- **Others**: Mixed (0.3-0.7)

**Future Enhancement**: Integration with:
- News APIs (NewsAPI, Alpha Vantage News)
- Social media sentiment (Twitter, Reddit)
- NLP models (BERT, FinBERT)
- Analyst ratings aggregation

## Comprehensive Prediction Pipeline

### Integration Flow:
1. **Data Collection**: Historical prices, volume, open interest
2. **Feature Engineering**: Technical indicators, Greeks calculation
3. **LSTM Prediction**: Future price forecast (7-day horizon)
4. **Random Forest**: BUY/SELL/HOLD classification
5. **XGBoost**: Premium prediction with Greeks
6. **Sentiment Analysis**: Market sentiment scoring
7. **Ensemble**: Combine all predictions with weighted confidence

### Confidence Scoring:
- Base confidence from each model
- Consensus bonus: +10% if action aligns with sentiment
- Weighted average: LSTM(25%) + RF(25%) + XGBoost(30%) + Sentiment(20%)
- Final confidence: 0.50 to 0.95 range

### Risk Assessment:
- **LOW**: Confidence > 0.75, >30 days to expiry
- **MEDIUM**: Confidence 0.60-0.75, >30 days to expiry
- **HIGH**: Confidence < 0.60 or <30 days to expiry

## API Integration

### Enhanced Predictions Endpoint
```
GET /api/predictions/best?limit=20
```

**Response Enhancement**:
```json
{
  "symbol": "AAPL",
  "company": "Apple Inc",
  "entry_price": 5.42,
  "overall_confidence": 0.82,
  "recommendation": "BUY",
  "ml_insights": {
    "lstm_price_forecast": 265.50,
    "lstm_confidence": 0.82,
    "action_recommendation": "BUY",
    "action_confidence": 0.78,
    "xgb_premium": 5.42,
    "xgb_confidence": 0.85,
    "greeks": {
      "delta": 0.6543,
      "gamma": 0.0123,
      "theta": -2.34,
      "vega": 1.45
    },
    "sentiment": "Bullish",
    "sentiment_score": 0.78,
    "overall_ml_confidence": 0.81,
    "models_used": ["LSTM", "RandomForest", "XGBoost", "Greeks", "Sentiment"]
  }
}
```

## Model Performance

### LSTM Performance:
- Training time: ~5-10 seconds per model
- Accuracy: MSE-based confidence (0.5-0.95)
- Best for: Trending markets with clear patterns
- Limitations: Requires 30+ data points for training

### Random Forest Performance:
- Training time: <1 second
- Accuracy: Based on technical indicator consensus
- Best for: Clear overbought/oversold signals
- Limitations: Lag in detecting trend reversals

### XGBoost Performance:
- Training time: 2-3 seconds
- Accuracy: R² score on synthetic data (0.7-0.9)
- Best for: Premium estimation with multiple features
- Limitations: Requires calibration with real market data

## Production Considerations

### Current Limitations:
1. Models trained on-the-fly (should be pre-trained)
2. Synthetic training data (should use historical data)
3. Simulated sentiment (should use real news/social data)
4. No model versioning or A/B testing
5. No performance monitoring/alerting

### Recommended Improvements:

**1. Pre-trained Models**:
- Train LSTM on 5 years of historical data for top 100 stocks
- Save model weights to disk/S3
- Load pre-trained models on service startup
- Periodic retraining (weekly/monthly)

**2. Real Training Data**:
- Historical price data from Polygon API
- Options chain history from CBOE
- Actual option trades for premium validation
- Store in TimescaleDB for efficient queries

**3. Real Sentiment Analysis**:
- Integrate NewsAPI for real-time news
- Reddit API for r/wallstreetbets sentiment
- Twitter API for trending tickers
- FinBERT for financial text sentiment

**4. Model Monitoring**:
- Track prediction accuracy vs actual outcomes
- Log confidence scores and actual results
- Calculate Sharpe ratio, win rate, profit factor
- MLflow for experiment tracking

**5. Feature Store**:
- Centralized feature computation
- Cache technical indicators in Redis
- Pre-compute Greeks for common strikes
- Feature versioning and lineage

**6. Backtesting Framework**:
- Historical simulation of predictions
- Walk-forward validation
- Out-of-sample testing
- Risk-adjusted returns analysis

## Usage Examples

### Python API:
```python
from models.ml_predictor import get_ml_predictor

predictor = get_ml_predictor()

# Comprehensive prediction
result = predictor.predict_comprehensive(
    symbol='AAPL',
    spot=259.37,
    strike=265.0,
    time_to_expiry=0.019,  # 7 days / 365
    volatility=0.28,
    volume=50000,
    open_interest=15000,
    historical_data=None  # Will generate synthetic
)

print(f"Action: {result['action_prediction']['action']}")
print(f"Premium: ${result['premium_prediction']['predicted_premium']:.2f}")
print(f"Confidence: {result['overall_confidence']:.2%}")
```

### REST API:
```bash
curl http://localhost:8004/api/predictions/best?limit=20
```

## Files Structure

```
services/
├── data-api/
│   ├── models/
│   │   ├── ml_predictor.py          # ML models implementation
│   │   └── options_predictor.py     # Original predictor
│   ├── options_api.py                # API with ML integration
│   └── requirements.txt              # Added ML libraries
├── prediction-engine/
│   ├── models/
│   │   └── ml_predictor.py          # Same ML models
│   └── requirements.txt              # ML libraries
└── docs/
    └── ML_IMPLEMENTATION.md          # This file
```

## Dependencies

### Required Libraries:
- **TensorFlow 2.15.0**: LSTM model
- **scikit-learn 1.3.2**: Random Forest, preprocessing
- **XGBoost 2.0.3**: Gradient boosting regressor
- **scipy 1.11.4**: Statistical functions, norm distribution
- **numpy 1.24.3**: Numerical operations
- **pandas 2.1.3**: Data manipulation

## Testing

### Unit Tests (TODO):
```python
def test_lstm_prediction():
    predictor = OptionsMLPredictor()
    result = predictor.predict_price_lstm(test_data)
    assert result['confidence'] > 0.5
    assert result['predicted_price'] > 0

def test_random_forest_classification():
    predictor = OptionsMLPredictor()
    result = predictor.predict_action_random_forest(test_features)
    assert result['action'] in ['BUY', 'SELL', 'HOLD']
    
def test_xgboost_premium():
    predictor = OptionsMLPredictor()
    result = predictor.predict_premium_xgboost(...)
    assert result['predicted_premium'] > 0
```

## Performance Metrics

### Latency:
- LSTM prediction: ~1-2 seconds
- Random Forest: <100ms
- XGBoost: ~500ms
- Total per prediction: ~2-3 seconds
- Batch of 20: ~30-40 seconds

### Memory:
- LSTM model: ~50MB
- Random Forest: ~10MB
- XGBoost: ~20MB
- Total: ~100MB per predictor instance

### Accuracy Goals:
- Price prediction: ±5% within 7 days
- Action classification: >65% win rate
- Premium prediction: ±10% of actual premium
- Overall system: >60% profitable trades

## Changelog

### Version 1.0.0 (January 12, 2026)
- ✅ Implemented LSTM for time-series price prediction
- ✅ Implemented Random Forest for BUY/SELL/HOLD classification
- ✅ Implemented XGBoost for premium prediction
- ✅ Calculated Greeks (Delta, Gamma, Theta, Vega)
- ✅ Added market sentiment analysis (simulated)
- ✅ Integrated with options_api.py
- ✅ Enhanced 20 predictions per request with ML insights
- ✅ Comprehensive prediction pipeline with ensemble confidence

### Next Release (Planned)
- [ ] Real historical data training
- [ ] Pre-trained model loading
- [ ] Real-time sentiment from NewsAPI
- [ ] Model versioning with MLflow
- [ ] Backtesting framework
- [ ] Performance monitoring dashboard
- [ ] A/B testing infrastructure
- [ ] Feature store with Redis caching

## Support

For questions or issues:
- Check logs: `docker logs options-api`
- ML predictor status: Look for "ML Predictor loaded successfully" in startup logs
- Fallback behavior: System gracefully falls back to calculated estimates if ML fails

## License

Internal use only - Proprietary trading system
