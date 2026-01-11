"""
India Market Data Connector
Streams real-time data from Zerodha Kite, Upstox, and NSE/BSE
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import json

from kiteconnect import KiteConnect, KiteTicker

logger = logging.getLogger(__name__)


class IndiaMarketConnector:
    """Connector for India market data (NSE, BSE, F&O)"""
    
    def __init__(self, zerodha_api_key: str, zerodha_api_secret: str,
                 zerodha_access_token: str, kafka_producer, redis_cache):
        self.api_key = zerodha_api_key
        self.api_secret = zerodha_api_secret
        self.access_token = zerodha_access_token
        self.kafka_producer = kafka_producer
        self.redis_cache = redis_cache
        
        # Initialize Zerodha Kite
        if self.api_key and self.access_token:
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            
            # Initialize ticker for WebSocket
            self.ticker = KiteTicker(self.api_key, self.access_token)
            
            # Set up callbacks
            self.ticker.on_ticks = self.on_ticks
            self.ticker.on_connect = self.on_connect
            self.ticker.on_close = self.on_close
            self.ticker.on_error = self.on_error
        else:
            self.kite = None
            self.ticker = None
            logger.warning("No Zerodha credentials - India market disabled")
        
        # Load instruments
        self.instruments = []
        self.stock_tokens = []
        self.option_tokens = []
        
        logger.info("India Market Connector initialized")
    
    async def initialize_instruments(self):
        """Load and cache NSE/BSE instruments"""
        if not self.kite:
            return
        
        try:
            # Fetch all instruments
            instruments = self.kite.instruments("NSE")
            instruments.extend(self.kite.instruments("NFO"))  # F&O segment
            
            self.instruments = instruments
            
            # Filter stocks and options
            self.stock_tokens = [
                inst['instrument_token'] 
                for inst in instruments 
                if inst['segment'] == 'NSE' and inst['instrument_type'] == 'EQ'
            ][:100]  # Top 100 stocks
            
            self.option_tokens = [
                inst['instrument_token']
                for inst in instruments
                if inst['segment'] == 'NFO' and inst['instrument_type'] in ['CE', 'PE']
            ][:500]  # Top 500 options
            
            logger.info(f"Loaded {len(self.stock_tokens)} stocks and {len(self.option_tokens)} options")
            
        except Exception as e:
            logger.error(f"Error loading instruments: {e}")
    
    def on_ticks(self, ws, ticks):
        """Handle incoming tick data"""
        for tick in ticks:
            try:
                # Find instrument details
                instrument = next(
                    (inst for inst in self.instruments 
                     if inst['instrument_token'] == tick['instrument_token']),
                    None
                )
                
                if not instrument:
                    continue
                
                # Determine asset type
                is_option = instrument['instrument_type'] in ['CE', 'PE']
                
                data = {
                    'symbol': instrument['tradingsymbol'],
                    'exchange': instrument['exchange'],
                    'price': tick.get('last_price'),
                    'volume': tick.get('volume'),
                    'oi': tick.get('oi', 0) if is_option else None,
                    'timestamp': datetime.now().isoformat(),
                    'market': 'INDIA',
                    'asset_type': 'option' if is_option else 'stock',
                    'bid': tick.get('depth', {}).get('buy', [{}])[0].get('price'),
                    'ask': tick.get('depth', {}).get('sell', [{}])[0].get('price'),
                    'high': tick.get('ohlc', {}).get('high'),
                    'low': tick.get('ohlc', {}).get('low'),
                    'open': tick.get('ohlc', {}).get('open'),
                    'close': tick.get('ohlc', {}).get('close')
                }
                
                # Send to appropriate Kafka topic
                topic = 'market.india.options.realtime' if is_option else 'market.india.stocks.realtime'
                
                self.kafka_producer.send_message(
                    topic=topic,
                    key=instrument['tradingsymbol'],
                    value=data
                )
                
                # Cache in Redis
                cache_key = f"price:india:{instrument['tradingsymbol']}"
                self.redis_cache.set(cache_key, json.dumps(data), expiry=300)
                
            except Exception as e:
                logger.error(f"Error processing tick: {e}")
    
    def on_connect(self, ws, response):
        """Handle WebSocket connection"""
        logger.info("Connected to Zerodha WebSocket")
        
        # Subscribe to instruments
        all_tokens = self.stock_tokens + self.option_tokens
        if all_tokens:
            ws.subscribe(all_tokens)
            ws.set_mode(ws.MODE_FULL, all_tokens)
            logger.info(f"Subscribed to {len(all_tokens)} instruments")
    
    def on_close(self, ws, code, reason):
        """Handle WebSocket disconnection"""
        logger.warning(f"WebSocket closed: {code} - {reason}")
    
    def on_error(self, ws, code, reason):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {code} - {reason}")
    
    async def stream_stocks_realtime(self):
        """Start real-time stock stream"""
        if not self.ticker:
            logger.warning("No Zerodha ticker - skipping India stock stream")
            return
        
        logger.info("Starting India stock stream...")
        
        # Initialize instruments first
        await self.initialize_instruments()
        
        # Start WebSocket in background thread
        def run_ticker():
            self.ticker.connect(threaded=True)
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_ticker)
        
        # Keep running
        while True:
            await asyncio.sleep(60)
    
    async def stream_options_realtime(self):
        """Stream real-time options data (handled by stock stream)"""
        # Options are handled in the same stream as stocks
        logger.info("Options streaming is combined with stocks stream")
        await asyncio.sleep(1)
    
    async def fetch_open_interest(self):
        """Periodically fetch options open interest"""
        if not self.kite:
            return
        
        logger.info("Starting India open interest fetcher...")
        
        while True:
            try:
                # Fetch F&O instruments
                instruments = self.kite.instruments("NFO")
                
                # Group by underlying
                underlyings = set(inst['name'] for inst in instruments)
                
                for underlying in list(underlyings)[:50]:  # Top 50 underlyings
                    # Filter options for this underlying
                    options = [
                        inst for inst in instruments
                        if inst['name'] == underlying and 
                        inst['instrument_type'] in ['CE', 'PE']
                    ]
                    
                    # Fetch OI data
                    tokens = [opt['instrument_token'] for opt in options]
                    
                    if not tokens:
                        continue
                    
                    # Get quotes (includes OI)
                    quotes = self.kite.quote([f"NFO:{opt['tradingsymbol']}" for opt in options[:100]])
                    
                    for symbol, quote in quotes.items():
                        data = {
                            'symbol': symbol.split(':')[1],
                            'exchange': 'NFO',
                            'open_interest': quote.get('oi', 0),
                            'volume': quote.get('volume', 0),
                            'last_price': quote.get('last_price', 0),
                            'timestamp': datetime.now().isoformat(),
                            'market': 'INDIA',
                            'asset_type': 'option'
                        }
                        
                        self.kafka_producer.send_message(
                            topic='market.india.options.openinterest',
                            key=symbol,
                            value=data
                        )
                    
                    await asyncio.sleep(1)  # Rate limiting
                
                logger.info(f"Fetched OI for {len(underlyings)} underlyings")
                
                # Wait 15 minutes
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Error fetching India OI: {e}")
                await asyncio.sleep(60)
    
    async def close(self):
        """Close all connections"""
        logger.info("Closing India Market Connector...")
        if self.ticker:
            self.ticker.close()
