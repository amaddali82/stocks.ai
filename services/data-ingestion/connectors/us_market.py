"""
US Market Data Connector
Streams real-time data from Polygon.io, Alpha Vantage, and other US market sources
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import json

import requests
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import WebSocketMessage, EquityTrade, EquityQuote
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


class USMarketConnector:
    """Connector for US market data (stocks, options, futures)"""
    
    def __init__(self, polygon_api_key: str, alpha_vantage_key: str, 
                 kafka_producer, redis_cache):
        self.polygon_api_key = polygon_api_key
        self.alpha_vantage_key = alpha_vantage_key
        self.kafka_producer = kafka_producer
        self.redis_cache = redis_cache
        
        # Initialize Polygon REST client
        self.polygon_rest = RESTClient(api_key=polygon_api_key) if polygon_api_key else None
        
        # WebSocket connections
        self.ws_stocks = None
        self.ws_options = None
        
        # Symbols to track
        self.stock_symbols = self._load_stock_symbols()
        self.option_symbols = []
        
        logger.info(f"US Market Connector initialized with {len(self.stock_symbols)} stocks")
    
    def _load_stock_symbols(self) -> List[str]:
        """Load list of stocks to track (S&P 500, NASDAQ 100, etc.)"""
        # Default symbols - should be loaded from config
        symbols = [
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO',
            # Indices
            'SPY', 'QQQ', 'DIA', 'IWM', 'VTI'
        ]
        return symbols
    
    async def stream_stocks_realtime(self):
        """Stream real-time stock prices via WebSocket"""
        if not self.polygon_api_key:
            logger.warning("No Polygon API key - skipping stock stream")
            return
        
        logger.info("Starting real-time stock stream...")
        
        async def handle_msg(msgs: List[WebSocketMessage]):
            """Handle incoming WebSocket messages"""
            for msg in msgs:
                try:
                    data = {
                        'symbol': msg.symbol,
                        'price': msg.price if hasattr(msg, 'price') else None,
                        'volume': msg.size if hasattr(msg, 'size') else None,
                        'timestamp': msg.timestamp if hasattr(msg, 'timestamp') else datetime.now().isoformat(),
                        'exchange': msg.exchange if hasattr(msg, 'exchange') else None,
                        'market': 'US',
                        'asset_type': 'stock'
                    }
                    
                    # Send to Kafka
                    self.kafka_producer.send_message(
                        topic='market.us.stocks.realtime',
                        key=msg.symbol,
                        value=data
                    )
                    
                    # Cache latest price in Redis
                    self.redis_cache.set(
                        f"price:us:{msg.symbol}",
                        json.dumps(data),
                        expiry=300  # 5 minutes
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing stock message: {e}")
        
        # Create WebSocket client
        ws_client = WebSocketClient(
            api_key=self.polygon_api_key,
            feed='stocks',
            market='stocks'
        )
        
        # Subscribe to stock symbols
        ws_client.subscribe(*[f"T.{symbol}" for symbol in self.stock_symbols])
        ws_client.subscribe(*[f"Q.{symbol}" for symbol in self.stock_symbols])
        
        # Run WebSocket
        try:
            await ws_client.connect(handle_msg)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await asyncio.sleep(5)
            # Retry connection
            await self.stream_stocks_realtime()
    
    async def stream_options_realtime(self):
        """Stream real-time options data"""
        if not self.polygon_api_key:
            logger.warning("No Polygon API key - skipping options stream")
            return
        
        logger.info("Starting real-time options stream...")
        
        async def handle_options_msg(msgs: List[WebSocketMessage]):
            """Handle options messages"""
            for msg in msgs:
                try:
                    data = {
                        'symbol': msg.symbol,
                        'strike': getattr(msg, 'strike_price', None),
                        'expiry': getattr(msg, 'expiration_date', None),
                        'option_type': getattr(msg, 'option_type', None),
                        'price': getattr(msg, 'price', None),
                        'volume': getattr(msg, 'size', None),
                        'open_interest': getattr(msg, 'open_interest', None),
                        'implied_volatility': getattr(msg, 'implied_volatility', None),
                        'timestamp': datetime.now().isoformat(),
                        'market': 'US',
                        'asset_type': 'option'
                    }
                    
                    # Send to Kafka
                    self.kafka_producer.send_message(
                        topic='market.us.options.realtime',
                        key=msg.symbol,
                        value=data
                    )
                    
                    # Cache in Redis
                    self.redis_cache.set(
                        f"option:us:{msg.symbol}",
                        json.dumps(data),
                        expiry=300
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing options message: {e}")
        
        # Create options WebSocket
        ws_client = WebSocketClient(
            api_key=self.polygon_api_key,
            feed='options',
            market='options'
        )
        
        # Subscribe to options for tracked stocks
        # This is a simplified version - real implementation would need option chains
        try:
            await ws_client.connect(handle_options_msg)
        except Exception as e:
            logger.error(f"Options WebSocket error: {e}")
            await asyncio.sleep(5)
    
    async def fetch_open_interest(self):
        """Periodically fetch options open interest data"""
        logger.info("Starting open interest fetcher...")
        
        while True:
            try:
                for symbol in self.stock_symbols:
                    # Fetch option chain with open interest
                    ticker = yf.Ticker(symbol)
                    
                    # Get all expiration dates
                    expirations = ticker.options
                    
                    for expiry in expirations[:3]:  # Fetch next 3 expiries
                        # Get calls and puts
                        opt_chain = ticker.option_chain(expiry)
                        
                        # Process calls
                        for _, row in opt_chain.calls.iterrows():
                            data = {
                                'symbol': symbol,
                                'strike': row['strike'],
                                'expiry': expiry,
                                'option_type': 'call',
                                'open_interest': row['openInterest'],
                                'volume': row['volume'],
                                'implied_volatility': row['impliedVolatility'],
                                'last_price': row['lastPrice'],
                                'timestamp': datetime.now().isoformat(),
                                'market': 'US',
                                'asset_type': 'option'
                            }
                            
                            self.kafka_producer.send_message(
                                topic='market.us.options.openinterest',
                                key=f"{symbol}_{expiry}_{row['strike']}_C",
                                value=data
                            )
                        
                        # Process puts
                        for _, row in opt_chain.puts.iterrows():
                            data = {
                                'symbol': symbol,
                                'strike': row['strike'],
                                'expiry': expiry,
                                'option_type': 'put',
                                'open_interest': row['openInterest'],
                                'volume': row['volume'],
                                'implied_volatility': row['impliedVolatility'],
                                'last_price': row['lastPrice'],
                                'timestamp': datetime.now().isoformat(),
                                'market': 'US',
                                'asset_type': 'option'
                            }
                            
                            self.kafka_producer.send_message(
                                topic='market.us.options.openinterest',
                                key=f"{symbol}_{expiry}_{row['strike']}_P",
                                value=data
                            )
                        
                        await asyncio.sleep(1)  # Rate limiting
                
                logger.info(f"Fetched open interest for {len(self.stock_symbols)} symbols")
                
                # Wait 15 minutes before next fetch
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Error fetching open interest: {e}")
                await asyncio.sleep(60)
    
    async def close(self):
        """Close all connections"""
        logger.info("Closing US Market Connector...")
        # Close WebSocket connections if open
        if self.ws_stocks:
            await self.ws_stocks.close()
        if self.ws_options:
            await self.ws_options.close()
