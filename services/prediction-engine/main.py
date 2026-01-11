"""
Prediction Engine - Main API
Serves ML models for trading predictions
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from models.model_manager import ModelManager
from models.lstm_model import LSTMPredictor
from models.transformer_model import TransformerPredictor
from models.ensemble_model import EnsemblePredictor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Trading Prediction Engine",
    description="ML-powered trading predictions for stocks, options, and futures",
    version="1.0.0"
)

# Initialize model manager
model_manager = ModelManager(
    mlflow_uri=os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000'),
    model_path=os.getenv('MODEL_PATH', '/models')
)


# Request/Response models
class PredictionRequest(BaseModel):
    symbol: str
    market: str  # US or INDIA
    asset_type: str  # stock, option, future
    horizon: str  # 1d, 5d, 1h, etc.
    model_type: Optional[str] = "ensemble"  # lstm, transformer, ensemble


class PredictionResponse(BaseModel):
    symbol: str
    prediction: str  # BUY, SELL, HOLD
    confidence: float
    target_price: Optional[float]
    expected_return: float
    risk_score: float
    features_used: Dict
    model_used: str
    timestamp: str


class ModelInfo(BaseModel):
    name: str
    version: str
    accuracy: float
    last_trained: str
    status: str


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting Prediction Engine API...")
    await model_manager.load_models()
    logger.info("Models loaded successfully")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Prediction Engine",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "models_loaded": model_manager.get_loaded_models(),
        "timestamp": datetime.now().isoformat()
    }
    return health_status


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Generate trading prediction for a symbol
    
    Args:
        request: Prediction request with symbol, market, asset type, etc.
    
    Returns:
        Prediction response with signal, confidence, target price, etc.
    """
    try:
        logger.info(f"Prediction request for {request.symbol} ({request.market})")
        
        # Get prediction from model manager
        prediction = await model_manager.predict(
            symbol=request.symbol,
            market=request.market,
            asset_type=request.asset_type,
            horizon=request.horizon,
            model_type=request.model_type
        )
        
        return prediction
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
async def predict_batch(symbols: List[str], market: str = "US"):
    """
    Batch prediction for multiple symbols
    
    Args:
        symbols: List of symbols to predict
        market: Market (US or INDIA)
    
    Returns:
        List of predictions
    """
    try:
        predictions = []
        
        for symbol in symbols:
            pred = await model_manager.predict(
                symbol=symbol,
                market=market,
                asset_type="stock",
                horizon="1d",
                model_type="ensemble"
            )
            predictions.append(pred)
        
        return {"predictions": predictions}
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """
    List all available models and their status
    
    Returns:
        List of model information
    """
    try:
        models = await model_manager.list_models()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/{model_name}/train")
async def train_model(model_name: str):
    """
    Trigger model training/retraining
    
    Args:
        model_name: Name of the model to train
    
    Returns:
        Training status
    """
    try:
        logger.info(f"Starting training for {model_name}")
        
        result = await model_manager.train_model(model_name)
        
        return {
            "status": "success",
            "model": model_name,
            "message": f"Training started for {model_name}",
            "job_id": result.get("job_id")
        }
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/features/{symbol}")
async def get_features(symbol: str, market: str = "US"):
    """
    Get latest features for a symbol
    
    Args:
        symbol: Stock/option symbol
        market: Market (US or INDIA)
    
    Returns:
        Latest features used for prediction
    """
    try:
        features = await model_manager.get_features(symbol, market)
        return {
            "symbol": symbol,
            "market": market,
            "features": features,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/{model_name}")
async def backtest_model(
    model_name: str,
    start_date: str,
    end_date: str,
    symbols: Optional[List[str]] = None
):
    """
    Run backtest for a model
    
    Args:
        model_name: Name of model to backtest
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        symbols: Optional list of symbols
    
    Returns:
        Backtest results
    """
    try:
        logger.info(f"Running backtest for {model_name}")
        
        results = await model_manager.backtest(
            model_name=model_name,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get model performance metrics"""
    try:
        metrics = await model_manager.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
