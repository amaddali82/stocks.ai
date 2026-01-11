"""
Order Management System - Main API
Handles trade execution with broker integrations
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from brokers.zerodha_broker import ZerodhaBroker
from brokers.etrade_broker import ETradeBroker
from risk.risk_checker import RiskChecker

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
    title="Order Management System",
    description="Trade execution and order management for multiple brokers",
    version="1.0.0"
)


# Enums
class OrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class BrokerType(str, Enum):
    ZERODHA = "zerodha"
    ETRADE = "etrade"


# Request/Response models
class OrderRequest(BaseModel):
    symbol: str
    exchange: str  # NSE, BSE, NYSE, NASDAQ
    action: OrderAction
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    broker: BrokerType
    product: Optional[str] = "MIS"  # MIS, CNC, NRML for Zerodha


class OrderResponse(BaseModel):
    order_id: str
    status: OrderStatus
    symbol: str
    action: OrderAction
    quantity: int
    filled_quantity: int
    average_price: float
    timestamp: str
    broker: str
    message: str


class PositionInfo(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    broker: str


# Initialize brokers
zerodha_broker = ZerodhaBroker(
    api_key=os.getenv('ZERODHA_API_KEY'),
    api_secret=os.getenv('ZERODHA_API_SECRET'),
    access_token=os.getenv('ZERODHA_ACCESS_TOKEN')
) if os.getenv('ZERODHA_API_KEY') else None

etrade_broker = ETradeBroker(
    consumer_key=os.getenv('ETRADE_CONSUMER_KEY'),
    consumer_secret=os.getenv('ETRADE_CONSUMER_SECRET'),
    access_token=os.getenv('ETRADE_ACCESS_TOKEN'),
    access_secret=os.getenv('ETRADE_ACCESS_SECRET')
) if os.getenv('ETRADE_CONSUMER_KEY') else None

# Initialize risk checker
risk_checker = RiskChecker()


def get_broker(broker_type: BrokerType):
    """Get broker instance"""
    if broker_type == BrokerType.ZERODHA:
        if not zerodha_broker:
            raise HTTPException(status_code=400, detail="Zerodha broker not configured")
        return zerodha_broker
    elif broker_type == BrokerType.ETRADE:
        if not etrade_broker:
            raise HTTPException(status_code=400, detail="E*TRADE broker not configured")
        return etrade_broker
    else:
        raise HTTPException(status_code=400, detail="Invalid broker type")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Order Management System...")
    
    # Initialize brokers
    if zerodha_broker:
        await zerodha_broker.initialize()
    if etrade_broker:
        await etrade_broker.initialize()
    
    logger.info("Order Management System ready")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Order Management System",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/orders", response_model=OrderResponse)
async def place_order(order: OrderRequest):
    """
    Place a new order
    
    Args:
        order: Order details
    
    Returns:
        Order confirmation with order ID and status
    """
    try:
        logger.info(f"Placing order: {order.action} {order.quantity} {order.symbol} via {order.broker}")
        
        # Get broker instance
        broker = get_broker(order.broker)
        
        # Check risk limits
        risk_check = await risk_checker.check_order(order)
        if not risk_check['approved']:
            raise HTTPException(status_code=400, detail=f"Risk check failed: {risk_check['reason']}")
        
        # Place order with broker
        result = await broker.place_order(
            symbol=order.symbol,
            exchange=order.exchange,
            action=order.action.value,
            quantity=order.quantity,
            order_type=order.order_type.value,
            price=order.price,
            trigger_price=order.trigger_price,
            product=order.product
        )
        
        return OrderResponse(
            order_id=result['order_id'],
            status=OrderStatus(result['status']),
            symbol=order.symbol,
            action=order.action,
            quantity=order.quantity,
            filled_quantity=result.get('filled_quantity', 0),
            average_price=result.get('average_price', 0.0),
            timestamp=datetime.now().isoformat(),
            broker=order.broker.value,
            message=result.get('message', 'Order placed successfully')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{order_id}")
async def get_order_status(order_id: str, broker: BrokerType):
    """
    Get order status
    
    Args:
        order_id: Order ID
        broker: Broker type
    
    Returns:
        Order status and details
    """
    try:
        broker_instance = get_broker(broker)
        order_details = await broker_instance.get_order_status(order_id)
        return order_details
    except Exception as e:
        logger.error(f"Error fetching order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str, broker: BrokerType):
    """
    Cancel an order
    
    Args:
        order_id: Order ID to cancel
        broker: Broker type
    
    Returns:
        Cancellation confirmation
    """
    try:
        logger.info(f"Cancelling order {order_id} on {broker}")
        
        broker_instance = get_broker(broker)
        result = await broker_instance.cancel_order(order_id)
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": "Order cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Order cancellation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions", response_model=List[PositionInfo])
async def get_positions(broker: BrokerType):
    """
    Get all open positions
    
    Args:
        broker: Broker type
    
    Returns:
        List of open positions
    """
    try:
        broker_instance = get_broker(broker)
        positions = await broker_instance.get_positions()
        return positions
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio")
async def get_portfolio(broker: BrokerType):
    """
    Get portfolio summary
    
    Args:
        broker: Broker type
    
    Returns:
        Portfolio details with P&L
    """
    try:
        broker_instance = get_broker(broker)
        portfolio = await broker_instance.get_portfolio()
        return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/holdings")
async def get_holdings(broker: BrokerType):
    """
    Get long-term holdings
    
    Args:
        broker: Broker type
    
    Returns:
        List of holdings
    """
    try:
        broker_instance = get_broker(broker)
        holdings = await broker_instance.get_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Error fetching holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/funds")
async def get_funds(broker: BrokerType):
    """
    Get available funds
    
    Args:
        broker: Broker type
    
    Returns:
        Available funds and margins
    """
    try:
        broker_instance = get_broker(broker)
        funds = await broker_instance.get_funds()
        return funds
    except Exception as e:
        logger.error(f"Error fetching funds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
