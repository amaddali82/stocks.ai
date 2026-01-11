"""
E*TRADE Broker Integration
"""

import logging
from typing import Dict, List, Optional
import requests
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)


class ETradeBroker:
    """E*TRADE broker integration"""
    
    def __init__(self, consumer_key: str, consumer_secret: str, 
                 access_token: str, access_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_secret = access_secret
        
        self.base_url = "https://api.etrade.com"
        self.sandbox_url = "https://etwssandbox.etrade.com"
        
        # OAuth1 session
        self.auth = OAuth1(
            consumer_key,
            consumer_secret,
            access_token,
            access_secret
        )
        
        logger.info("E*TRADE broker initialized")
    
    async def initialize(self):
        """Initialize E*TRADE connection"""
        try:
            # Verify connection by fetching account list
            response = requests.get(
                f"{self.base_url}/v1/accounts/list",
                auth=self.auth
            )
            
            if response.status_code == 200:
                self.accounts = response.json().get('AccountListResponse', {}).get('Accounts', {}).get('Account', [])
                logger.info(f"E*TRADE connected successfully. Found {len(self.accounts)} accounts")
            else:
                logger.error(f"E*TRADE connection failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to initialize E*TRADE: {e}")
    
    async def place_order(self, symbol: str, exchange: str, action: str, quantity: int,
                         order_type: str, price: Optional[float] = None,
                         trigger_price: Optional[float] = None,
                         product: str = None) -> Dict:
        """Place order on E*TRADE"""
        try:
            # Get first account ID
            if not hasattr(self, 'accounts') or not self.accounts:
                raise ValueError("No E*TRADE accounts found")
            
            account_id = self.accounts[0]['accountId']
            
            # Build order payload
            order_payload = {
                "PlaceOrderRequest": {
                    "orderType": order_type,
                    "clientOrderId": f"OMS_{symbol}_{int(datetime.now().timestamp())}",
                    "Order": [{
                        "Instrument": [{
                            "Product": {
                                "symbol": symbol,
                                "securityType": "EQ"
                            },
                            "orderAction": action,
                            "quantityType": "QUANTITY",
                            "quantity": quantity
                        }],
                        "priceType": "MARKET" if order_type == "MARKET" else "LIMIT",
                        "limitPrice": price if price else None,
                        "stopPrice": trigger_price if trigger_price else None,
                        "allOrNone": False
                    }]
                }
            }
            
            # Place order
            response = requests.post(
                f"{self.base_url}/v1/accounts/{account_id}/orders/place",
                json=order_payload,
                auth=self.auth
            )
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('PlaceOrderResponse', {}).get('OrderIds', [{}])[0].get('orderId')
                
                logger.info(f"E*TRADE order placed: {order_id}")
                
                return {
                    'order_id': str(order_id),
                    'status': 'OPEN',
                    'filled_quantity': 0,
                    'average_price': 0.0,
                    'message': 'Order placed successfully'
                }
            else:
                raise ValueError(f"Order placement failed: {response.text}")
                
        except Exception as e:
            logger.error(f"E*TRADE order placement failed: {e}")
            raise
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        try:
            account_id = self.accounts[0]['accountId']
            
            response = requests.get(
                f"{self.base_url}/v1/accounts/{account_id}/orders/{order_id}",
                auth=self.auth
            )
            
            if response.status_code == 200:
                order = response.json().get('OrderResponse', {})
                return {
                    'order_id': order_id,
                    'status': order.get('status', 'UNKNOWN'),
                    'filled_quantity': order.get('filledQuantity', 0),
                    'average_price': order.get('averageExecutionPrice', 0.0)
                }
            else:
                raise ValueError(f"Failed to fetch order: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching E*TRADE order status: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        try:
            account_id = self.accounts[0]['accountId']
            
            response = requests.put(
                f"{self.base_url}/v1/accounts/{account_id}/orders/cancel",
                json={"CancelOrderRequest": {"orderId": order_id}},
                auth=self.auth
            )
            
            if response.status_code == 200:
                logger.info(f"E*TRADE order {order_id} cancelled")
                return {'status': 'success'}
            else:
                raise ValueError(f"Cancellation failed: {response.text}")
        except Exception as e:
            logger.error(f"Error cancelling E*TRADE order: {e}")
            raise
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        try:
            account_id = self.accounts[0]['accountId']
            
            response = requests.get(
                f"{self.base_url}/v1/accounts/{account_id}/portfolio",
                auth=self.auth
            )
            
            if response.status_code == 200:
                portfolio = response.json().get('PortfolioResponse', {})
                positions = portfolio.get('AccountPortfolio', [{}])[0].get('Position', [])
                return positions
            else:
                return []
        except Exception as e:
            logger.error(f"Error fetching E*TRADE positions: {e}")
            raise
    
    async def get_portfolio(self) -> Dict:
        """Get portfolio summary"""
        try:
            positions = await self.get_positions()
            
            total_value = sum(p.get('marketValue', 0) for p in positions)
            total_gain_loss = sum(p.get('totalGainLoss', 0) for p in positions)
            
            return {
                'total_value': total_value,
                'total_pnl': total_gain_loss,
                'positions_count': len(positions)
            }
        except Exception as e:
            logger.error(f"Error fetching E*TRADE portfolio: {e}")
            raise
    
    async def get_holdings(self) -> List[Dict]:
        """Get holdings (same as positions for E*TRADE)"""
        return await self.get_positions()
    
    async def get_funds(self) -> Dict:
        """Get available funds"""
        try:
            account_id = self.accounts[0]['accountId']
            
            response = requests.get(
                f"{self.base_url}/v1/accounts/{account_id}/balance",
                auth=self.auth
            )
            
            if response.status_code == 200:
                balance = response.json().get('BalanceResponse', {})
                return {
                    'cash_available': balance.get('cashAvailableForInvestment', 0),
                    'buying_power': balance.get('cashBuyingPower', 0)
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error fetching E*TRADE funds: {e}")
            raise


from datetime import datetime
