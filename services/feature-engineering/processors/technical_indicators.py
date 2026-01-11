"""
Technical Indicator Processor
Computes indicators using TA-Lib and pandas-ta
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np
import talib
import pandas_ta as ta

logger = logging.getLogger(__name__)


class TechnicalIndicatorProcessor:
    """Process market data and compute technical indicators"""
    
    def __init__(self, db_writer, redis_cache):
        self.db_writer = db_writer
        self.redis_cache = redis_cache
        
        # Window sizes for indicators
        self.sma_windows = [5, 10, 20, 50, 200]
        self.ema_windows = [9, 12, 26, 50]
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        logger.info("Technical Indicator Processor initialized")
    
    async def process_market_data(self, data: Dict):
        """Process incoming market data and compute indicators"""
        try:
            symbol = data.get('symbol')
            market = data.get('market')
            
            # Fetch recent historical data
            df = await self.db_writer.fetch_recent_ohlcv(symbol, market, limit=250)
            
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Compute indicators
            features = self._compute_all_indicators(df)
            
            # Add metadata
            features['symbol'] = symbol
            features['market'] = market
            features['timestamp'] = data.get('timestamp')
            
            # Write to database
            await self.db_writer.write_features('technical_features', features)
            
            # Cache latest features
            self.redis_cache.cache_features(symbol, features)
            
            logger.debug(f"Computed features for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing technical indicators: {e}")
    
    def _compute_all_indicators(self, df: pd.DataFrame) -> Dict:
        """Compute all technical indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        features = {}
        
        # Price and volume
        features['price'] = close[-1]
        features['volume'] = volume[-1]
        features['avg_volume_20'] = np.mean(volume[-20:])
        
        # Moving Averages
        for window in self.sma_windows:
            if len(close) >= window:
                features[f'sma_{window}'] = talib.SMA(close, timeperiod=window)[-1]
        
        for window in self.ema_windows:
            if len(close) >= window:
                features[f'ema_{window}'] = talib.EMA(close, timeperiod=window)[-1]
        
        # RSI
        if len(close) >= self.rsi_period:
            features['rsi'] = talib.RSI(close, timeperiod=self.rsi_period)[-1]
        
        # MACD
        if len(close) >= self.macd_slow:
            macd, macd_signal, macd_hist = talib.MACD(
                close,
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            features['macd'] = macd[-1]
            features['macd_signal'] = macd_signal[-1]
            features['macd_hist'] = macd_hist[-1]
        
        # Bollinger Bands
        if len(close) >= 20:
            upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            features['bb_upper'] = upper[-1]
            features['bb_middle'] = middle[-1]
            features['bb_lower'] = lower[-1]
            features['bb_width'] = (upper[-1] - lower[-1]) / middle[-1]
        
        # ATR (Average True Range)
        if len(close) >= 14:
            features['atr'] = talib.ATR(high, low, close, timeperiod=14)[-1]
        
        # Stochastic Oscillator
        if len(close) >= 14:
            slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            features['stoch_k'] = slowk[-1]
            features['stoch_d'] = slowd[-1]
        
        # ADX (Average Directional Index)
        if len(close) >= 14:
            features['adx'] = talib.ADX(high, low, close, timeperiod=14)[-1]
        
        # CCI (Commodity Channel Index)
        if len(close) >= 14:
            features['cci'] = talib.CCI(high, low, close, timeperiod=14)[-1]
        
        # Williams %R
        if len(close) >= 14:
            features['willr'] = talib.WILLR(high, low, close, timeperiod=14)[-1]
        
        # OBV (On-Balance Volume)
        features['obv'] = talib.OBV(close, volume)[-1]
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (high + low + close) / 3
        features['vwap'] = np.sum(typical_price[-20:] * volume[-20:]) / np.sum(volume[-20:])
        
        # Momentum
        if len(close) >= 10:
            features['momentum'] = talib.MOM(close, timeperiod=10)[-1]
        
        # Rate of Change
        if len(close) >= 10:
            features['roc'] = talib.ROC(close, timeperiod=10)[-1]
        
        # Price changes
        features['price_change_1d'] = (close[-1] - close[-2]) / close[-2] if len(close) >= 2 else 0
        features['price_change_5d'] = (close[-1] - close[-6]) / close[-6] if len(close) >= 6 else 0
        features['price_change_20d'] = (close[-1] - close[-21]) / close[-21] if len(close) >= 21 else 0
        
        # Volatility
        if len(close) >= 20:
            returns = np.diff(np.log(close[-20:]))
            features['volatility_20d'] = np.std(returns) * np.sqrt(252)  # Annualized
        
        return features
