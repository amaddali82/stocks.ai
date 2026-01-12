"""
Multi-Provider Stock Data Fetcher with Fallback Mechanism
Supports: Yahoo Finance, Alpha Vantage, Finnhub, and other free providers
"""

import os
import requests
import yfinance as yf
import logging
from typing import Optional, Dict, List
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# API Keys from environment (optional - will work without them for some providers)
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
FINNHUB_KEY = os.getenv('FINNHUB_KEY', '')
TWELVEDATA_KEY = os.getenv('TWELVEDATA_KEY', '')

class MultiProviderDataFetcher:
    """Fetches stock data from multiple providers with automatic fallback"""
    
    def __init__(self):
        self.providers = [
            self._fetch_from_yahoo,
            self._fetch_from_finnhub,
            self._fetch_from_alpha_vantage,
            self._fetch_from_twelvedata,
        ]
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
    
    @lru_cache(maxsize=1000)
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """
        Get current price from multiple providers with fallback
        Returns: {'price': float, 'change': float, 'change_percent': float, 'source': str}
        """
        # Check cache first
        cache_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                logger.debug(f"Cache hit for {symbol} from {cached_data['data']['source']}")
                return cached_data['data']
        
        # Try each provider in order
        for provider_func in self.providers:
            try:
                result = provider_func(symbol)
                if result and result.get('price') and result['price'] > 0:
                    # Cache the successful result
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': datetime.now()
                    }
                    logger.info(f"✓ Got price for {symbol} from {result['source']}: ${result['price']}")
                    return result
            except Exception as e:
                logger.debug(f"Provider {provider_func.__name__} failed for {symbol}: {e}")
                continue
        
        logger.error(f"All providers failed for {symbol}")
        return None
    
    def _fetch_from_yahoo(self, symbol: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance (free, no API key)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            change = info.get('regularMarketChange', 0)
            change_pct = info.get('regularMarketChangePercent', 0)
            
            if price and price > 0:
                return {
                    'price': float(price),
                    'change': float(change),
                    'change_percent': float(change_pct),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap'),
                    'source': 'Yahoo Finance'
                }
        except Exception as e:
            logger.debug(f"Yahoo Finance failed: {e}")
        return None
    
    def _fetch_from_finnhub(self, symbol: str) -> Optional[Dict]:
        """Fetch from Finnhub.io (free tier: 60 calls/minute)"""
        if not FINNHUB_KEY:
            return None
        
        try:
            # Convert .NS symbols to NSE:SYMBOL format
            if symbol.endswith('.NS'):
                symbol = f"NSE:{symbol.replace('.NS', '')}"
            
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('c')  # Current price
                change = data.get('d')    # Change
                change_pct = data.get('dp') # Change percent
                
                if current and current > 0:
                    return {
                        'price': float(current),
                        'change': float(change or 0),
                        'change_percent': float(change_pct or 0),
                        'volume': 0,
                        'market_cap': None,
                        'source': 'Finnhub.io'
                    }
        except Exception as e:
            logger.debug(f"Finnhub failed: {e}")
        return None
    
    def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage (free tier: 5 calls/minute, 500/day)"""
        if ALPHA_VANTAGE_KEY == 'demo':
            return None  # Skip if using demo key
        
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                price = quote.get('05. price')
                change = quote.get('09. change')
                change_pct = quote.get('10. change percent', '0%').replace('%', '')
                
                if price:
                    return {
                        'price': float(price),
                        'change': float(change or 0),
                        'change_percent': float(change_pct or 0),
                        'volume': int(quote.get('06. volume', 0)),
                        'market_cap': None,
                        'source': 'Alpha Vantage'
                    }
        except Exception as e:
            logger.debug(f"Alpha Vantage failed: {e}")
        return None
    
    def _fetch_from_twelvedata(self, symbol: str) -> Optional[Dict]:
        """Fetch from Twelve Data (free tier: 8 calls/minute, 800/day)"""
        if not TWELVEDATA_KEY:
            return None
        
        try:
            url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVEDATA_KEY}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get('price')
                
                if price:
                    return {
                        'price': float(price),
                        'change': 0,
                        'change_percent': 0,
                        'volume': 0,
                        'market_cap': None,
                        'source': 'Twelve Data'
                    }
        except Exception as e:
            logger.debug(f"Twelve Data failed: {e}")
        return None
    
    def get_batch_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch prices for multiple symbols efficiently"""
        results = {}
        for symbol in symbols:
            price_data = self.get_current_price(symbol)
            if price_data:
                results[symbol] = price_data
        return results
    
    def clear_cache(self):
        """Clear the price cache"""
        self.cache.clear()
        self.get_current_price.cache_clear()
        logger.info("Price cache cleared")


# Global instance
_fetcher = None

def get_price_fetcher() -> MultiProviderDataFetcher:
    """Get or create the global price fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MultiProviderDataFetcher()
    return _fetcher
