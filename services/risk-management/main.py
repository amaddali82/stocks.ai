"""
Risk Management Service
Monitors and enforces risk limits for trading
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import redis
import pandas as pd

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
    title="Risk Management Service",
    description="Real-time risk monitoring and compliance",
    version="1.0.0"
)

# Initialize Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Risk parameters
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 100000))
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', 10000))
MAX_PORTFOLIO_RISK = float(os.getenv('MAX_PORTFOLIO_RISK', 0.05))
MAX_LEVERAGE = float(os.getenv('MAX_LEVERAGE', 2.0))


class RiskCheckRequest(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    price: float
    broker: str


class RiskCheckResponse(BaseModel):
    approved: bool
    reason: Optional[str] = None
    risk_metrics: Dict


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Risk Management Service...")
    logger.info(f"Risk Limits: Position=${MAX_POSITION_SIZE:,.0f}, Daily Loss=${MAX_DAILY_LOSS:,.0f}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Risk Management",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    redis_healthy = redis_client.ping()
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/check", response_model=RiskCheckResponse)
async def check_risk(request: RiskCheckRequest):
    """
    Check if an order passes risk limits
    
    Args:
        request: Order details to check
    
    Returns:
        Risk check result with approval status
    """
    try:
        logger.info(f"Risk check: {request.action} {request.quantity} {request.symbol} @ ${request.price}")
        
        # Calculate order value
        order_value = request.quantity * request.price
        
        # Check 1: Position size limit
        if order_value > MAX_POSITION_SIZE:
            return RiskCheckResponse(
                approved=False,
                reason=f"Order value ${order_value:,.0f} exceeds max position size ${MAX_POSITION_SIZE:,.0f}",
                risk_metrics={"order_value": order_value, "max_allowed": MAX_POSITION_SIZE}
            )
        
        # Check 2: Daily loss limit
        daily_pnl = await get_daily_pnl(request.broker)
        if daily_pnl < -MAX_DAILY_LOSS:
            return RiskCheckResponse(
                approved=False,
                reason=f"Daily loss ${abs(daily_pnl):,.0f} exceeds limit ${MAX_DAILY_LOSS:,.0f}",
                risk_metrics={"daily_pnl": daily_pnl, "max_loss": MAX_DAILY_LOSS}
            )
        
        # Check 3: Portfolio concentration
        total_portfolio_value = await get_portfolio_value(request.broker)
        if total_portfolio_value > 0:
            concentration = order_value / total_portfolio_value
            if concentration > MAX_PORTFOLIO_RISK:
                return RiskCheckResponse(
                    approved=False,
                    reason=f"Position would be {concentration:.1%} of portfolio, max allowed {MAX_PORTFOLIO_RISK:.1%}",
                    risk_metrics={"concentration": concentration, "max_concentration": MAX_PORTFOLIO_RISK}
                )
        
        # Check 4: Available funds (simplified check)
        available_funds = await get_available_funds(request.broker)
        if request.action == "BUY" and order_value > available_funds:
            return RiskCheckResponse(
                approved=False,
                reason=f"Insufficient funds. Need ${order_value:,.0f}, available ${available_funds:,.0f}",
                risk_metrics={"required": order_value, "available": available_funds}
            )
        
        # All checks passed
        return RiskCheckResponse(
            approved=True,
            reason="All risk checks passed",
            risk_metrics={
                "order_value": order_value,
                "daily_pnl": daily_pnl,
                "portfolio_value": total_portfolio_value,
                "available_funds": available_funds
            }
        )
        
    except Exception as e:
        logger.error(f"Risk check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_risk_metrics(broker: str):
    """
    Get current risk metrics
    
    Args:
        broker: Broker name
    
    Returns:
        Current risk metrics
    """
    try:
        daily_pnl = await get_daily_pnl(broker)
        portfolio_value = await get_portfolio_value(broker)
        available_funds = await get_available_funds(broker)
        
        # Calculate Value at Risk (simplified)
        var_95 = portfolio_value * 0.02  # 2% VaR estimate
        
        return {
            "daily_pnl": daily_pnl,
            "portfolio_value": portfolio_value,
            "available_funds": available_funds,
            "var_95": var_95,
            "max_daily_loss": MAX_DAILY_LOSS,
            "max_position_size": MAX_POSITION_SIZE,
            "risk_utilization": abs(daily_pnl) / MAX_DAILY_LOSS if daily_pnl < 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/limits")
async def get_risk_limits():
    """Get configured risk limits"""
    return {
        "max_position_size": MAX_POSITION_SIZE,
        "max_daily_loss": MAX_DAILY_LOSS,
        "max_portfolio_risk": MAX_PORTFOLIO_RISK,
        "max_leverage": MAX_LEVERAGE
    }


# Helper functions
async def get_daily_pnl(broker: str) -> float:
    """Get daily P&L from Redis cache"""
    try:
        key = f"daily_pnl:{broker}:{datetime.now().date()}"
        pnl = redis_client.get(key)
        return float(pnl) if pnl else 0.0
    except Exception as e:
        logger.error(f"Error fetching daily P&L: {e}")
        return 0.0


async def get_portfolio_value(broker: str) -> float:
    """Get total portfolio value from Redis cache"""
    try:
        key = f"portfolio_value:{broker}"
        value = redis_client.get(key)
        return float(value) if value else 100000.0  # Default $100k
    except Exception as e:
        logger.error(f"Error fetching portfolio value: {e}")
        return 100000.0


async def get_available_funds(broker: str) -> float:
    """Get available funds from Redis cache"""
    try:
        key = f"available_funds:{broker}"
        funds = redis_client.get(key)
        return float(funds) if funds else 50000.0  # Default $50k
    except Exception as e:
        logger.error(f"Error fetching available funds: {e}")
        return 50000.0


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )
