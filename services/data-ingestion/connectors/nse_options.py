"""
NSE India Option Chain Data Fetcher
Fetches real-time option chain data from NSE India
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time
from functools import lru_cache

logger = logging.getLogger(__name__)


class NSEOptionChain:
    """Fetches option chain data from NSE India"""
    
    BASE_URL = "https://www.nseindia.com"
    OPTION_CHAIN_URL = f"{BASE_URL}/api/option-chain-equities"
    OPTION_CHAIN_INDEX_URL = f"{BASE_URL}/api/option-chain-indices"
    
    # Common NSE stocks with options
    EQUITY_SYMBOLS = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
        'ICICIBANK', 'KOTAKBANK', 'BHARTIARTL', 'ITC', 'SBIN',
        'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH', 'AXISBANK',
        'LT', 'ULTRACEMCO', 'TITAN', 'SUNPHARMA', 'WIPRO',
        'TECHM', 'NESTLEIND', 'TATAMOTORS', 'BAJAJFINSV', 'POWERGRID',
        'NTPC', 'M&M', 'ONGC', 'JSWSTEEL', 'TATASTEEL'
    ]
    
    # NSE Indices with options
    INDEX_SYMBOLS = [
        'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/option-chain',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self._initialize_session()
        logger.info("NSE Option Chain fetcher initialized")
    
    def _initialize_session(self):
        """Initialize session by visiting NSE homepage to get cookies"""
        try:
            response = self.session.get(
                self.BASE_URL,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("NSE session initialized successfully")
            else:
                logger.warning(f"NSE session init returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Error initializing NSE session: {e}")
    
    def _refresh_session(self):
        """Refresh session if cookies expired"""
        logger.info("Refreshing NSE session...")
        self.session.cookies.clear()
        self._initialize_session()
        time.sleep(1)  # Rate limiting
    
    def fetch_equity_option_chain(self, symbol: str) -> Optional[Dict]:
        """
        Fetch option chain for an equity symbol
        
        Args:
            symbol: NSE equity symbol (e.g., 'RELIANCE', 'TCS')
            
        Returns:
            Option chain data dict or None if error
        """
        try:
            url = f"{self.OPTION_CHAIN_URL}?symbol={symbol.upper()}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 401 or response.status_code == 403:
                # Session expired, refresh and retry
                self._refresh_session()
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_option_chain(data, symbol, 'EQUITY')
            else:
                logger.error(f"NSE API returned status {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return None
    
    def fetch_index_option_chain(self, symbol: str) -> Optional[Dict]:
        """
        Fetch option chain for an index symbol
        
        Args:
            symbol: NSE index symbol (e.g., 'NIFTY', 'BANKNIFTY')
            
        Returns:
            Option chain data dict or None if error
        """
        try:
            url = f"{self.OPTION_CHAIN_INDEX_URL}?symbol={symbol.upper()}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 401 or response.status_code == 403:
                # Session expired, refresh and retry
                self._refresh_session()
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_option_chain(data, symbol, 'INDEX')
            else:
                logger.error(f"NSE API returned status {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return None
    
    def _parse_option_chain(self, raw_data: Dict, symbol: str, asset_type: str) -> Dict:
        """Parse raw NSE option chain response into standardized format"""
        try:
            records = raw_data.get('records', {})
            underlying_value = records.get('underlyingValue', 0)
            timestamp = records.get('timestamp', '')
            
            option_data = records.get('data', [])
            
            calls = []
            puts = []
            
            for record in option_data:
                strike_price = record.get('strikePrice', 0)
                expiry_date = record.get('expiryDate', '')
                
                # Parse CE (Call Option)
                if 'CE' in record:
                    ce = record['CE']
                    calls.append({
                        'strike_price': strike_price,
                        'expiry_date': expiry_date,
                        'option_type': 'CALL',
                        'last_price': ce.get('lastPrice', 0),
                        'change': ce.get('change', 0),
                        'percent_change': ce.get('pChange', 0),
                        'volume': ce.get('totalTradedVolume', 0),
                        'open_interest': ce.get('openInterest', 0),
                        'oi_change': ce.get('changeinOpenInterest', 0),
                        'implied_volatility': ce.get('impliedVolatility', 0),
                        'bid_price': ce.get('bidprice', 0),
                        'bid_qty': ce.get('bidQty', 0),
                        'ask_price': ce.get('askPrice', 0),
                        'ask_qty': ce.get('askQty', 0),
                    })
                
                # Parse PE (Put Option)
                if 'PE' in record:
                    pe = record['PE']
                    puts.append({
                        'strike_price': strike_price,
                        'expiry_date': expiry_date,
                        'option_type': 'PUT',
                        'last_price': pe.get('lastPrice', 0),
                        'change': pe.get('change', 0),
                        'percent_change': pe.get('pChange', 0),
                        'volume': pe.get('totalTradedVolume', 0),
                        'open_interest': pe.get('openInterest', 0),
                        'oi_change': pe.get('changeinOpenInterest', 0),
                        'implied_volatility': pe.get('impliedVolatility', 0),
                        'bid_price': pe.get('bidprice', 0),
                        'bid_qty': pe.get('bidQty', 0),
                        'ask_price': pe.get('askPrice', 0),
                        'ask_qty': pe.get('askQty', 0),
                    })
            
            return {
                'symbol': symbol,
                'asset_type': asset_type,
                'underlying_value': underlying_value,
                'timestamp': timestamp,
                'total_call_oi': sum(c['open_interest'] for c in calls),
                'total_put_oi': sum(p['open_interest'] for p in puts),
                'pcr_oi': sum(p['open_interest'] for p in puts) / sum(c['open_interest'] for c in calls) if sum(c['open_interest'] for c in calls) > 0 else 0,
                'pcr_volume': sum(p['volume'] for p in puts) / sum(c['volume'] for c in calls) if sum(c['volume'] for c in calls) > 0 else 0,
                'calls': calls,
                'puts': puts,
                'total_calls': len(calls),
                'total_puts': len(puts)
            }
            
        except Exception as e:
            logger.error(f"Error parsing option chain data: {e}")
            return {
                'symbol': symbol,
                'asset_type': asset_type,
                'error': str(e),
                'calls': [],
                'puts': []
            }
    
    def get_atm_options(self, symbol: str, asset_type: str = 'EQUITY', num_strikes: int = 5) -> Dict:
        """
        Get at-the-money (ATM) options with strikes around current price
        
        Args:
            symbol: Stock/Index symbol
            asset_type: 'EQUITY' or 'INDEX'
            num_strikes: Number of strikes above and below ATM to return
            
        Returns:
            ATM option chain data
        """
        if asset_type == 'INDEX':
            data = self.fetch_index_option_chain(symbol)
        else:
            data = self.fetch_equity_option_chain(symbol)
        
        if not data or 'error' in data:
            return data
        
        # Filter to ATM strikes
        underlying_value = data['underlying_value']
        all_calls = data['calls']
        all_puts = data['puts']
        
        # Find strikes closest to underlying value
        strikes = sorted(set(c['strike_price'] for c in all_calls))
        atm_strike = min(strikes, key=lambda x: abs(x - underlying_value))
        atm_idx = strikes.index(atm_strike)
        
        # Get strikes around ATM
        start_idx = max(0, atm_idx - num_strikes)
        end_idx = min(len(strikes), atm_idx + num_strikes + 1)
        atm_strikes = strikes[start_idx:end_idx]
        
        # Filter options to ATM strikes
        atm_calls = [c for c in all_calls if c['strike_price'] in atm_strikes]
        atm_puts = [p for p in all_puts if p['strike_price'] in atm_strikes]
        
        data['calls'] = atm_calls
        data['puts'] = atm_puts
        data['atm_strike'] = atm_strike
        data['strikes_range'] = atm_strikes
        
        return data
    
    def get_all_equity_options(self, limit: int = 10) -> List[Dict]:
        """
        Fetch option chains for multiple equity symbols
        
        Args:
            limit: Maximum number of symbols to fetch
            
        Returns:
            List of option chain data
        """
        results = []
        
        for symbol in self.EQUITY_SYMBOLS[:limit]:
            logger.info(f"Fetching options for {symbol}...")
            data = self.get_atm_options(symbol, 'EQUITY', num_strikes=3)
            
            if data and 'error' not in data:
                results.append(data)
            
            # Rate limiting - NSE blocks aggressive requests
            time.sleep(1)
        
        return results
    
    def get_all_index_options(self) -> List[Dict]:
        """
        Fetch option chains for all major indices
        
        Returns:
            List of index option chain data
        """
        results = []
        
        for symbol in self.INDEX_SYMBOLS:
            logger.info(f"Fetching options for {symbol}...")
            data = self.get_atm_options(symbol, 'INDEX', num_strikes=5)
            
            if data and 'error' not in data:
                results.append(data)
            
            # Rate limiting
            time.sleep(1)
        
        return results


# Global instance
nse_option_chain = NSEOptionChain()


def fetch_nse_options(symbol: str, asset_type: str = 'EQUITY') -> Optional[Dict]:
    """
    Convenience function to fetch NSE options
    
    Args:
        symbol: NSE symbol
        asset_type: 'EQUITY' or 'INDEX'
        
    Returns:
        Option chain data or None
    """
    return nse_option_chain.get_atm_options(symbol, asset_type)


if __name__ == "__main__":
    # Test the fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== Testing NSE Option Chain Fetcher ===\n")
    
    # Test equity options
    print("Fetching RELIANCE options...")
    reliance = fetch_nse_options('RELIANCE', 'EQUITY')
    if reliance:
        print(f"✓ RELIANCE: {len(reliance['calls'])} calls, {len(reliance['puts'])} puts")
        print(f"  Underlying: ₹{reliance['underlying_value']}")
        print(f"  ATM Strike: ₹{reliance.get('atm_strike', 'N/A')}")
        print(f"  PCR (OI): {reliance['pcr_oi']:.2f}")
    
    time.sleep(2)
    
    # Test index options
    print("\nFetching NIFTY options...")
    nifty = fetch_nse_options('NIFTY', 'INDEX')
    if nifty:
        print(f"✓ NIFTY: {len(nifty['calls'])} calls, {len(nifty['puts'])} puts")
        print(f"  Underlying: {nifty['underlying_value']}")
        print(f"  ATM Strike: {nifty.get('atm_strike', 'N/A')}")
        print(f"  PCR (OI): {nifty['pcr_oi']:.2f}")
