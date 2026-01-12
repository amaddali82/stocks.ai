"""
NSE India Option Chain Data Fetcher using API v3
Fetches real-time option chain data from NSE India
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class NSEOptionChain:
    """Fetches option chain data from NSE India using v3 API"""
    
    BASE_URL = "https://www.nseindia.com"
    OPTION_CHAIN_V3_URL = f"{BASE_URL}/api/option-chain-v3"
    EXPIRY_DATES_URL = f"{BASE_URL}/api/option-chain-expiry-dates"
    
    # Common NSE stocks with options
    EQUITY_SYMBOLS = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
        'ICICIBANK', 'KOTAKBANK', 'BHARTIARTL', 'ITC', 'SBIN',
        'BAJ FINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH', 'AXISBANK',
        'LT', 'ULTRACEMCO', 'TITAN', 'SUNPHARMA', 'WIPRO',
        'TECHM', 'NESTLEIND', 'TATAMOTORS', 'BAJAJFINSV', 'POWERGRID',
        'NTPC', 'M&M', 'ONGC', 'JSWSTEEL', 'TATASTEEL', 'BEL'
    ]
    
    # NSE Indices with options
    INDEX_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
    
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
            response = self.session.get(self.BASE_URL, timeout=10)
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
        time.sleep(1)
    
    def fetch_expiry_dates(self, symbol: str, asset_type: str = 'EQUITY') -> Optional[List[str]]:
        """
        Fetch available expiry dates for a symbol
        
        Args:
            symbol: NSE symbol
            asset_type: 'EQUITY' or 'INDEX'
            
        Returns:
            List of expiry dates in DD-MMM-YYYY format or None
        """
        try:
            url = f"{self.EXPIRY_DATES_URL}?type={asset_type.capitalize()}&symbol={symbol.upper()}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code in [401, 403]:
                self._refresh_session()
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expiries = data.get('expiryDates', [])
                logger.info(f"Found {len(expiries)} expiry dates for {symbol}")
                return expiries
            else:
                logger.error(f"NSE API returned status {response.status_code} for expiry dates")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching expiry dates for {symbol}: {e}")
            return None
    
    def fetch_option_chain(self, symbol: str, asset_type: str = 'EQUITY', expiry: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch option chain for a symbol
        
        Args:
            symbol: NSE symbol
            asset_type: 'EQUITY' or 'INDEX'
            expiry: Expiry date in DD-MMM-YYYY format (e.g., '27-Jan-2026'). If None, fetches nearest expiry.
            
        Returns:
            Option chain data dict or None if error
        """
        try:
            # Get expiry dates if not provided
            if not expiry:
                expiries = self.fetch_expiry_dates(symbol, asset_type)
                if expiries and len(expiries) > 0:
                    expiry = expiries[0]
                    logger.info(f"Using nearest expiry: {expiry}")
                else:
                    logger.error(f"No expiry dates found for {symbol}")
                    return None
            
            # Build URL for option chain v3
            type_param = "Index" if asset_type.upper() == 'INDEX' else "Equity"
            url = f"{self.OPTION_CHAIN_V3_URL}?type={type_param}&symbol={symbol.upper()}&expiry={expiry}"
            
            logger.info(f"Fetching option chain: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code in [401, 403]:
                self._refresh_session()
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_option_chain(data, symbol, asset_type, expiry)
            else:
                logger.error(f"NSE API returned status {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return None
    
    def _parse_option_chain(self, raw_data: Dict, symbol: str, asset_type: str, expiry: str) -> Dict:
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
                        'ask_price': ce.get('askPrice', 0),
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
                        'ask_price': pe.get('askPrice', 0),
                    })
            
            # Calculate PCR
            total_call_oi = sum(c['open_interest'] for c in calls) if calls else 0
            total_put_oi = sum(p['open_interest'] for p in puts) if puts else 0
            total_call_vol = sum(c['volume'] for c in calls) if calls else 0
            total_put_vol = sum(p['volume'] for p in puts) if puts else 0
            
            return {
                'symbol': symbol,
                'asset_type': asset_type,
                'expiry_date': expiry,
                'underlying_value': underlying_value,
                'timestamp': timestamp,
                'total_call_oi': total_call_oi,
                'total_put_oi': total_put_oi,
                'pcr_oi': total_put_oi / total_call_oi if total_call_oi > 0 else 0,
                'pcr_volume': total_put_vol / total_call_vol if total_call_vol > 0 else 0,
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
    
    def get_atm_options(self, symbol: str, asset_type: str = 'EQUITY', num_strikes: int = 5, expiry: Optional[str] = None) -> Dict:
        """
        Get at-the-money (ATM) options with strikes around current price
        
        Args:
            symbol: Stock/Index symbol
            asset_type: 'EQUITY' or 'INDEX'
            num_strikes: Number of strikes above and below ATM to return
            expiry: Expiry date in DD-MMM-YYYY format. If None, uses nearest expiry.
            
        Returns:
            ATM option chain data
        """
        data = self.fetch_option_chain(symbol, asset_type, expiry)
        
        if not data or 'error' in data:
            return data
        
        # Check if we have option data
        all_calls = data.get('calls', [])
        all_puts = data.get('puts', [])
        
        if not all_calls or not all_puts:
            logger.warning(f"No option data found for {symbol}")
            return data
        
        # Filter to ATM strikes
        underlying_value = data.get('underlying_value', 0)
        if underlying_value == 0:
            logger.warning(f"No underlying value found for {symbol}")
            return data
        
        # Find strikes closest to underlying value
        strikes = sorted(set(c['strike_price'] for c in all_calls))
        
        if not strikes:
            logger.warning(f"No strikes found for {symbol}")
            return data
        
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


# Global instance
nse_option_chain = NSEOptionChain()


def fetch_nse_options(symbol: str, asset_type: str = 'EQUITY', expiry: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to fetch NSE options
    
    Args:
        symbol: NSE symbol
        asset_type: 'EQUITY' or 'INDEX'
        expiry: Expiry date in DD-MMM-YYYY format
        
    Returns:
        Option chain data or None
    """
    return nse_option_chain.get_atm_options(symbol, asset_type, expiry=expiry)
