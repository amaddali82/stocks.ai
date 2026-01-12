"""
Price Verification Module
Verifies option prices against multiple data sources
"""

import logging
import time
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OptionPriceVerifier:
    """Verify option prices from multiple sources"""
    
    def __init__(self):
        self.verification_cache = {}
        
    def verify_option_price(
        self, 
        symbol: str, 
        strike: float, 
        expiry: str, 
        option_type: str = 'CALL',
        expected_price: float = None
    ) -> Dict:
        """
        Verify option price against live market data
        Returns: {
            'verified': bool,
            'live_price': float,
            'expected_price': float,
            'difference': float,
            'difference_pct': float,
            'source': str,
            'timestamp': str
        }
        """
        cache_key = f"{symbol}_{strike}_{expiry}_{option_type}"
        
        # Check cache (5 minute expiry)
        if cache_key in self.verification_cache:
            cached = self.verification_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < 300:
                return cached['data']
        
        result = {
            'verified': False,
            'live_price': None,
            'expected_price': expected_price,
            'difference': None,
            'difference_pct': None,
            'source': None,
            'timestamp': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            # Try Yahoo Finance
            ticker = yf.Ticker(symbol)
            
            # Get available option dates
            available_dates = ticker.options
            if not available_dates or expiry not in available_dates:
                result['error'] = f"Expiry {expiry} not available. Available: {list(available_dates)[:3] if available_dates else 'None'}"
                logger.warning(f"Expiry {expiry} not in available dates for {symbol}")
                return result
            
            # Get option chain
            chain = ticker.option_chain(expiry)
            
            # Select calls or puts
            options_df = chain.calls if option_type.upper() == 'CALL' else chain.puts
            
            # Find matching strike
            matching = options_df[options_df['strike'] == strike]
            
            if len(matching) == 0:
                # Try approximate match (within $1)
                matching = options_df[
                    (options_df['strike'] >= strike - 1) & 
                    (options_df['strike'] <= strike + 1)
                ]
                
            if len(matching) > 0:
                live_option = matching.iloc[0]
                live_price = float(live_option['lastPrice'])
                
                result['verified'] = True
                result['live_price'] = live_price
                result['source'] = 'Yahoo Finance'
                
                if expected_price:
                    result['difference'] = live_price - expected_price
                    result['difference_pct'] = (result['difference'] / expected_price * 100) if expected_price > 0 else 0
                    
                    # Consider verified if within 5% tolerance
                    if abs(result['difference_pct']) > 5:
                        logger.warning(
                            f"⚠️ Price mismatch for {symbol} ${strike} {option_type}: "
                            f"Expected ${expected_price:.2f}, Live ${live_price:.2f} "
                            f"({result['difference_pct']:.1f}% diff)"
                        )
                    else:
                        logger.info(
                            f"✓ Verified {symbol} ${strike} {option_type}: "
                            f"${live_price:.2f} (within 5% tolerance)"
                        )
            else:
                result['error'] = f"Strike ${strike} not found in option chain"
                logger.warning(f"Strike {strike} not found for {symbol} {expiry}")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error verifying {symbol} ${strike} {option_type}: {e}")
        
        # Cache result
        self.verification_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        return result
    
    def verify_multiple_options(self, options: List[Dict]) -> List[Dict]:
        """
        Verify multiple options
        Returns list of verification results
        """
        results = []
        
        for opt in options:
            time.sleep(0.5)  # Rate limiting
            
            verification = self.verify_option_price(
                symbol=opt['symbol'],
                strike=opt['strike'],
                expiry=opt['expiry'],
                option_type=opt.get('option_type', 'CALL'),
                expected_price=opt.get('entry_price')
            )
            
            results.append({
                'option': opt,
                'verification': verification
            })
        
        return results
    
    def get_verification_summary(self, results: List[Dict]) -> Dict:
        """Generate verification summary"""
        total = len(results)
        verified = sum(1 for r in results if r['verification']['verified'])
        failed = total - verified
        
        mismatches = [
            r for r in results 
            if r['verification']['verified'] and 
            r['verification'].get('difference_pct') and 
            abs(r['verification']['difference_pct']) > 5
        ]
        
        return {
            'total_checked': total,
            'verified': verified,
            'failed': failed,
            'verification_rate': (verified / total * 100) if total > 0 else 0,
            'price_mismatches': len(mismatches),
            'mismatch_details': [
                {
                    'symbol': r['option']['symbol'],
                    'strike': r['option']['strike'],
                    'expected': r['verification']['expected_price'],
                    'live': r['verification']['live_price'],
                    'difference_pct': r['verification']['difference_pct']
                }
                for r in mismatches
            ]
        }


# Singleton instance
_verifier = None

def get_price_verifier() -> OptionPriceVerifier:
    """Get singleton price verifier instance"""
    global _verifier
    if _verifier is None:
        _verifier = OptionPriceVerifier()
    return _verifier
