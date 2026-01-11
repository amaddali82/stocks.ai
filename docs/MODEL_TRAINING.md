# Model Training Guide

## Overview

This guide covers training, evaluating, and deploying machine learning models in the Stocks.AI system.

## Supported Models

1. **LSTM Networks** - Time series prediction
2. **Transformer Models** - Multi-horizon forecasting
3. **Graph Neural Networks** - Cross-asset dependencies
4. **Ensemble Models** - Combined predictions
5. **FinGPT-RAG** - LLM-powered analysis

## Data Preparation

### 1. Collect Training Data

```python
from data.data_loader import DataLoader

# Initialize data loader
loader = DataLoader()

# Fetch historical data
data = loader.fetch_historical_data(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2025-12-31',
    market='US'
)

# Add technical features
data_with_features = loader.add_technical_indicators(data)

# Add sentiment data
data_complete = loader.add_sentiment_scores(data_with_features)

# Save prepared dataset
data_complete.to_parquet('data/training/prepared_dataset.parquet')
```

### 2. Create Labels

```python
from data.labeling import create_labels

# Create trading signals (BUY=2, HOLD=1, SELL=0)
labels = create_labels(
    data_complete,
    method='returns',  # or 'sharpe', 'drawdown'
    horizon='1d',
    threshold=0.02  # 2% return threshold
)

data_complete['label'] = labels
```

## Training Models

### LSTM Model

```python
from models.lstm_model import LSTMPredictor
import mlflow

# Initialize MLflow
mlflow.set_tracking_uri('http://localhost:5000')
mlflow.set_experiment('lstm_stock_prediction')

# Start training run
with mlflow.start_run(run_name='lstm_v1'):
    # Initialize model
    model = LSTMPredictor()
    
    # Prepare data
    X_train, X_val, y_train, y_val = model.prepare_training_data(
        data_complete,
        train_split=0.8
    )
    
    # Train model
    history = model.train(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=32
    )
    
    # Log parameters
    mlflow.log_params({
        'model_type': 'LSTM',
        'hidden_size': 128,
        'num_layers': 2,
        'dropout': 0.2,
        'sequence_length': 60
    })
    
    # Evaluate
    val_accuracy = model.evaluate(X_val, y_val)
    mlflow.log_metric('val_accuracy', val_accuracy)
    
    # Save model
    model.save('models/lstm_v1.pth')
    mlflow.pytorch.log_model(model, 'model')
    
    print(f"Training complete. Accuracy: {val_accuracy:.4f}")
```

### Transformer Model

```python
from models.transformer_model import TransformerPredictor

with mlflow.start_run(run_name='transformer_v1'):
    model = TransformerPredictor(
        d_model=128,
        nhead=8,
        num_layers=4,
        dropout=0.1
    )
    
    # Train
    model.train(X_train, y_train, epochs=50)
    
    # Evaluate
    accuracy = model.evaluate(X_val, y_val)
    
    # Log to MLflow
    mlflow.log_params(model.get_config())
    mlflow.log_metric('val_accuracy', accuracy)
    mlflow.pytorch.log_model(model, 'model')
```

### Ensemble Model

```python
from models.ensemble_model import EnsemblePredictor

# Load individual models
lstm_model = LSTMPredictor.load('models/lstm_v1.pth')
transformer_model = TransformerPredictor.load('models/transformer_v1.pth')

# Create ensemble
ensemble = EnsemblePredictor(
    models=[lstm_model, transformer_model],
    weights=[0.6, 0.4]  # LSTM gets 60%, Transformer 40%
)

# Evaluate ensemble
ensemble_accuracy = ensemble.evaluate(X_val, y_val)
print(f"Ensemble accuracy: {ensemble_accuracy:.4f}")

# Save ensemble
ensemble.save('models/ensemble_v1.pkl')
```

## Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV
from models.model_wrapper import ModelWrapper

# Define parameter grid
param_grid = {
    'hidden_size': [64, 128, 256],
    'num_layers': [2, 3, 4],
    'dropout': [0.1, 0.2, 0.3],
    'learning_rate': [0.001, 0.0001]
}

# Grid search
grid_search = GridSearchCV(
    ModelWrapper(LSTMPredictor),
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best accuracy: {grid_search.best_score_:.4f}")
```

## Backtesting

```python
from backtesting.backtest_engine import BacktestEngine
import backtrader as bt

# Initialize backtest
engine = BacktestEngine()

# Load model
model = LSTMPredictor.load('models/lstm_v1.pth')

# Run backtest
results = engine.run_backtest(
    model=model,
    data=data_complete,
    start_date='2024-01-01',
    end_date='2025-12-31',
    initial_capital=100000,
    commission=0.001  # 0.1%
)

# Print results
print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Total Trades: {results['total_trades']}")

# Plot equity curve
results['equity_curve'].plot(title='Backtest Equity Curve')
```

## Model Evaluation Metrics

```python
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Get predictions
y_pred = model.predict(X_val)

# Classification report
print(classification_report(y_val, y_pred, target_names=['SELL', 'HOLD', 'BUY']))

# Confusion matrix
cm = confusion_matrix(y_val, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['SELL', 'HOLD', 'BUY'],
            yticklabels=['SELL', 'HOLD', 'BUY'])
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.show()

# Custom trading metrics
def calculate_trading_metrics(y_true, y_pred, prices):
    """Calculate trading-specific metrics"""
    # Implement profit/loss calculation
    # Implement Sharpe ratio
    # Implement maximum drawdown
    pass
```

## Model Deployment

### 1. Register Model in MLflow

```python
import mlflow

# Register best model
model_uri = "runs:/abc123/model"
mlflow.register_model(model_uri, "stock_predictor")

# Transition to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="stock_predictor",
    version=1,
    stage="Production"
)
```

### 2. Deploy to Prediction Engine

```python
# Copy model to prediction engine
import shutil
shutil.copy('models/lstm_v1.pth', '/app/models/production/lstm_v1.pth')

# Restart prediction service
import subprocess
subprocess.run(['docker-compose', 'restart', 'prediction-engine'])
```

### 3. A/B Testing

```python
# Deploy new model alongside existing one
from deployment.ab_testing import ABTestManager

ab_test = ABTestManager()

# Route 20% traffic to new model
ab_test.create_test(
    model_a='lstm_v1',
    model_b='lstm_v2',
    traffic_split=0.2,  # 20% to model B
    duration_days=7
)

# Monitor performance
ab_test.monitor_test()

# Promote winner
winner = ab_test.get_winner()
print(f"Winner: {winner}")
```

## Continuous Training

### Setup Automated Retraining

```python
# airflow/dags/model_retraining.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def retrain_model():
    """Retrain model with latest data"""
    # Fetch latest data
    # Retrain model
    # Evaluate performance
    # Deploy if better
    pass

dag = DAG(
    'model_retraining',
    schedule_interval='0 0 * * 0',  # Weekly on Sunday
    start_date=datetime(2026, 1, 1),
    catchup=False
)

retrain_task = PythonOperator(
    task_id='retrain_model',
    python_callable=retrain_model,
    dag=dag
)
```

## Best Practices

1. **Version Control**: Track all model versions in MLflow
2. **Data Versioning**: Use DVC or similar for dataset versioning
3. **Cross-Validation**: Use time-series cross-validation
4. **Feature Engineering**: Experiment with different features
5. **Ensemble Methods**: Combine multiple models for better accuracy
6. **Regular Retraining**: Retrain models weekly or monthly
7. **Monitor Drift**: Track model performance degradation
8. **Backtest Thoroughly**: Test on multiple time periods
9. **Risk Management**: Always validate with risk checks
10. **Document Everything**: Keep training notebooks and logs

## Troubleshooting

### Model Not Converging

- Reduce learning rate
- Increase training epochs
- Add more training data
- Check for data leakage

### Overfitting

- Increase dropout rate
- Add L2 regularization
- Use early stopping
- Reduce model complexity

### Poor Performance

- Check data quality
- Verify feature engineering
- Try different architectures
- Increase model capacity

## Further Reading

- [Deep Learning for Time Series](https://arxiv.org/abs/2004.13408)
- [Financial Machine Learning](https://www.quantresearch.org/)
- [Backtrader Documentation](https://www.backtrader.com/docu/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
