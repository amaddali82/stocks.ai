"""
Zerodha Kite Broker Integration
"""

import logging
from typing import Dict, List, Optional
from kiteconnect import KiteConnect

logger = logging.getLogger(__name__)


class ZerodhaBroker:
    """Zerodha Kite broker integration"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.kite = None
        
        logger.info("Zerodha broker initialized")
    
    async def initialize(self):
        """Initialize Kite connection"""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                logger.info("Zerodha Kite connected successfully")
            else:
                logger.warning("No access token provided for Zerodha")
        except Exception as e:
            logger.error(f"Failed to initialize Zerodha: {e}")
    
    async def place_order(self, symbol: str, exchange: str, action: str, quantity: int,
                         order_type: str, price: Optional[float] = None,
                         trigger_price: Optional[float] = None,
                         product: str = "MIS") -> Dict:
        """Place order on Zerodha"""
        try:
            # Map order types
            variety = "regular"
            transaction_type = self.kite.TRANSACTION_TYPE_BUY if action == "BUY" else self.kite.TRANSACTION_TYPE_SELL
            
            order_type_map = {
                "MARKET": self.kite.ORDER_TYPE_MARKET,
                "LIMIT": self.kite.ORDER_TYPE_LIMIT,
                "STOP_LOSS": self.kite.ORDER_TYPE_SL,
                "STOP_LOSS_MARKET": self.kite.ORDER_TYPE_SLM
            }
            
            product_map = {
                "MIS": self.kite.PRODUCT_MIS,
                "CNC": self.kite.PRODUCT_CNC,
                "NRML": self.kite.PRODUCT_NRML
            }
            
            # Place order
            order_id = self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type_map.get(order_type, self.kite.ORDER_TYPE_MARKET),
                product=product_map.get(product, self.kite.PRODUCT_MIS),
                price=price,
                trigger_price=trigger_price
            )
            
            logger.info(f"Order placed successfully: {order_id}")
            
            return {
                'order_id': order_id,
                'status': 'OPEN',
                'filled_quantity': 0,
                'average_price': 0.0,
                'message': 'Order placed successfully'
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        try:
            orders = self.kite.orders()
            order = next((o for o in orders if o['order_id'] == order_id), None)
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            return {
                'order_id': order_id,
                'status': order['status'],
                'filled_quantity': order['filled_quantity'],
                'average_price': order['average_price'],
                'symbol': order['tradingsymbol']
            }
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        try:
            self.kite.cancel_order(variety="regular", order_id=order_id)
            logger.info(f"Order {order_id} cancelled")
            return {'status': 'success'}
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        try:
            positions = self.kite.positions()
            return positions.get('day', []) + positions.get('net', [])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise
    
    async def get_portfolio(self) -> Dict:
        """Get portfolio summary"""
        try:
            positions = await self.get_positions()
            
            total_pnl = sum(p.get('pnl', 0) for p in positions)
            total_value = sum(p.get('value', 0) for p in positions)
            
            return {
                'total_pnl': total_pnl,
                'total_value': total_value,
                'positions_count': len(positions)
            }
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            raise
    
    async def get_holdings(self) -> List[Dict]:
        """Get holdings"""
        try:
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            raise
    
    async def get_funds(self) -> Dict:
        """Get available funds"""
        try:
            return self.kite.margins()
        except Exception as e:
            logger.error(f"Error fetching funds: {e}")
            raise
