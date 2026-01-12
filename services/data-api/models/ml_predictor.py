"""
ML/AI Prediction Models for Options Trading
Implements LSTM, Random Forest, and XGBoost models
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    MODELS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not fully available: {e}")
    MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)

class OptionsMLPredictor:
    """
    Comprehensive ML predictor combining LSTM, Random Forest, and XGBoost
    """
    
    def __init__(self):
        self.lstm_model = None
        self.rf_classifier = None
        self.xgb_regressor = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def calculate_greeks(self, spot: float, strike: float, time_to_expiry: float, 
                        volatility: float, risk_free_rate: float = 0.05) -> Dict[str, float]:
        """
        Calculate option Greeks using Black-Scholes approximations
        """
        from math import sqrt, exp, log
        from scipy.stats import norm
        
        # Avoid division by zero
        if time_to_expiry <= 0:
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
        
        # Black-Scholes d1 and d2
        d1 = (log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * sqrt(time_to_expiry))
        d2 = d1 - volatility * sqrt(time_to_expiry)
        
        # Greeks calculations
        delta = norm.cdf(d1)
        gamma = norm.pdf(d1) / (spot * volatility * sqrt(time_to_expiry))
        theta = (-spot * norm.pdf(d1) * volatility / (2 * sqrt(time_to_expiry)) 
                 - risk_free_rate * strike * exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
        vega = spot * norm.pdf(d1) * sqrt(time_to_expiry) / 100  # Divided by 100 for percentage
        
        return {
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta, 4),
            'vega': round(vega, 4)
        }
    
    def create_lstm_model(self, sequence_length: int = 10, n_features: int = 8) -> Sequential:
        """
        Create LSTM model for time-series price prediction
        """
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(sequence_length, n_features)),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')  # Price prediction
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def prepare_lstm_sequences(self, prices: List[float], features: pd.DataFrame, 
                               sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training
        """
        X, y = [], []
        
        for i in range(len(prices) - sequence_length):
            X.append(features.iloc[i:i+sequence_length].values)
            y.append(prices[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def predict_price_lstm(self, historical_data: pd.DataFrame, days_ahead: int = 7) -> Dict[str, float]:
        """
        Predict future price using LSTM model
        """
        try:
            # Generate synthetic historical data if not enough data
            if len(historical_data) < 30:
                historical_data = self._generate_synthetic_history(historical_data, 30)
            
            # Prepare features
            features = self._extract_features(historical_data)
            prices = historical_data['close'].values
            
            # Create and train LSTM model (in production, load pre-trained model)
            sequence_length = min(10, len(prices) - 1)
            self.lstm_model = self.create_lstm_model(sequence_length, features.shape[1])
            
            # Prepare training data
            X, y = self.prepare_lstm_sequences(prices, features, sequence_length)
            
            if len(X) > 0:
                # Quick training (in production, use pre-trained model)
                self.lstm_model.fit(X, y, epochs=5, batch_size=32, verbose=0, validation_split=0.2)
                
                # Predict next prices
                last_sequence = features.iloc[-sequence_length:].values.reshape(1, sequence_length, -1)
                predicted_price = self.lstm_model.predict(last_sequence, verbose=0)[0][0]
                
                # Calculate confidence based on model performance
                predictions = self.lstm_model.predict(X, verbose=0)
                mse = np.mean((predictions.flatten() - y) ** 2)
                confidence = max(0.5, min(0.95, 1.0 - (mse / np.mean(y))))
                
                return {
                    'predicted_price': float(predicted_price),
                    'confidence': float(confidence),
                    'model': 'LSTM',
                    'days_ahead': days_ahead
                }
            else:
                return self._fallback_prediction(prices[-1])
                
        except Exception as e:
            logger.warning(f"LSTM prediction failed: {e}")
            return self._fallback_prediction(historical_data['close'].values[-1])
    
    def predict_action_random_forest(self, features: pd.DataFrame) -> Dict[str, any]:
        """
        Predict BUY/SELL/HOLD using Random Forest classifier
        """
        try:
            # Create synthetic training data based on technical signals
            X_train, y_train = self._create_classification_training_data(features)
            
            # Train Random Forest
            self.rf_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.rf_classifier.fit(X_train, y_train)
            
            # Predict on current features
            X_current = features.iloc[-1:].values
            prediction = self.rf_classifier.predict(X_current)[0]
            probabilities = self.rf_classifier.predict_proba(X_current)[0]
            
            # Handle 2 or 3 class predictions
            n_classes = len(probabilities)
            if n_classes == 2:
                # Only 2 classes predicted (e.g., HOLD and BUY)
                actions = ['HOLD', 'BUY']
                probs_dict = {
                    'BUY': float(probabilities[1]) if len(probabilities) > 1 else 0.33,
                    'HOLD': float(probabilities[0]),
                    'SELL': 0.0
                }
            else:
                # All 3 classes
                actions = ['SELL', 'HOLD', 'BUY']
                probs_dict = {
                    'BUY': float(probabilities[2]) if len(probabilities) > 2 else float(probabilities[-1]),
                    'HOLD': float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0]),
                    'SELL': float(probabilities[0])
                }
            
            confidence = float(max(probabilities))
            
            return {
                'action': actions[min(prediction, len(actions)-1)],
                'confidence': confidence,
                'probabilities': probs_dict,
                'model': 'RandomForest'
            }
            
        except Exception as e:
            logger.warning(f"Random Forest prediction failed: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.5,
                'probabilities': {'BUY': 0.33, 'HOLD': 0.34, 'SELL': 0.33},
                'model': 'Fallback'
            }
    
    def predict_premium_xgboost(self, spot: float, strike: float, time_to_expiry: float,
                                volatility: float, volume: int, open_interest: int,
                                greeks: Dict[str, float]) -> Dict[str, float]:
        """
        Predict option premium using XGBoost regression
        """
        try:
            # Prepare features for XGBoost
            feature_dict = {
                'spot': spot,
                'strike': strike,
                'moneyness': spot / strike,
                'time_to_expiry': time_to_expiry,
                'volatility': volatility,
                'volume': np.log1p(volume),
                'open_interest': np.log1p(open_interest),
                'delta': greeks['delta'],
                'gamma': greeks['gamma'],
                'theta': greeks['theta'],
                'vega': greeks['vega']
            }
            
            # Create synthetic training data
            X_train, y_train = self._create_premium_training_data(feature_dict)
            
            # Train XGBoost
            self.xgb_regressor = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                objective='reg:squarederror'
            )
            self.xgb_regressor.fit(X_train, y_train, verbose=False)
            
            # Predict premium
            X_current = pd.DataFrame([feature_dict])
            predicted_premium = self.xgb_regressor.predict(X_current)[0]
            
            # Ensure premium is positive and reasonable
            predicted_premium = max(0.01, min(predicted_premium, spot * 0.5))
            
            # Feature importance for confidence
            importance = self.xgb_regressor.feature_importances_
            confidence = 0.7 + (np.max(importance) * 0.25)  # 0.7 to 0.95 range
            
            return {
                'predicted_premium': float(predicted_premium),
                'confidence': float(confidence),
                'model': 'XGBoost',
                'feature_importance': {
                    name: float(imp) for name, imp in zip(feature_dict.keys(), importance)
                }
            }
            
        except Exception as e:
            logger.warning(f"XGBoost prediction failed: {e}")
            # Fallback to intrinsic + time value
            intrinsic = max(0, spot - strike)
            time_value = spot * 0.03 * np.sqrt(time_to_expiry)
            return {
                'predicted_premium': float(intrinsic + time_value),
                'confidence': 0.5,
                'model': 'Fallback'
            }
    
    def get_market_sentiment(self, symbol: str, news_data: Optional[List[Dict]] = None) -> Dict[str, float]:
        """
        Calculate market sentiment from news and social media
        (Placeholder - would integrate with sentiment analysis API)
        """
        # Simulated sentiment based on symbol characteristics
        # In production, integrate with news API and sentiment analysis
        
        sentiment_score = 0.0
        
        # Simulate sentiment based on symbol (placeholder logic)
        if symbol in ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META']:
            sentiment_score = np.random.uniform(0.6, 0.9)  # Tech stocks bullish
        elif symbol in ['XOM', 'CVX']:
            sentiment_score = np.random.uniform(0.4, 0.7)  # Energy neutral to bullish
        else:
            sentiment_score = np.random.uniform(0.3, 0.7)  # Others mixed
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': 'Bullish' if sentiment_score > 0.6 else 'Bearish' if sentiment_score < 0.4 else 'Neutral',
            'confidence': 0.7,
            'source': 'Simulated'
        }
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract technical features from historical data
        """
        features = pd.DataFrame()
        
        close = df['close'].values
        
        # Price-based features
        features['close'] = close
        features['returns'] = np.concatenate([[0], np.diff(close)]) / (close + 1e-10)
        
        # Moving averages
        features['sma_5'] = pd.Series(close).rolling(window=5, min_periods=1).mean().values
        features['sma_10'] = pd.Series(close).rolling(window=10, min_periods=1).mean().values
        
        # Volatility
        features['volatility'] = pd.Series(close).rolling(window=5, min_periods=1).std().values
        
        # Momentum
        features['momentum'] = np.concatenate([[0], close[1:] - close[:-1]])
        
        # RSI (simplified)
        gains = np.maximum(features['returns'], 0)
        losses = np.abs(np.minimum(features['returns'], 0))
        avg_gain = pd.Series(gains).rolling(window=14, min_periods=1).mean().values
        avg_loss = pd.Series(losses).rolling(window=14, min_periods=1).mean().values
        rs = avg_gain / (avg_loss + 1e-10)
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume (if available)
        if 'volume' in df.columns:
            features['volume'] = df['volume'].values
        else:
            features['volume'] = np.ones(len(close)) * 1000000
        
        return features.fillna(0)
    
    def _generate_synthetic_history(self, current_data: pd.DataFrame, target_length: int) -> pd.DataFrame:
        """
        Generate synthetic historical data for training
        """
        if len(current_data) == 0:
            return pd.DataFrame()
        
        last_price = current_data['close'].iloc[-1]
        dates = pd.date_range(end=datetime.now(), periods=target_length, freq='D')
        
        # Generate price series with random walk
        returns = np.random.normal(0.0005, 0.02, target_length)
        prices = last_price * np.exp(np.cumsum(returns))
        
        synthetic_df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, target_length)
        })
        
        return synthetic_df
    
    def _create_classification_training_data(self, features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create synthetic training data for classification
        """
        X = features.values
        n_samples = len(X)
        
        # Generate labels based on technical signals
        y = []
        for i in range(n_samples):
            rsi = features['rsi'].iloc[i] if 'rsi' in features.columns else 50
            momentum = features['momentum'].iloc[i] if 'momentum' in features.columns else 0
            
            # Simple rule-based labeling
            if rsi < 30 and momentum > 0:
                y.append(2)  # BUY
            elif rsi > 70 and momentum < 0:
                y.append(0)  # SELL
            else:
                y.append(1)  # HOLD
        
        return X, np.array(y)
    
    def _create_premium_training_data(self, feature_dict: Dict) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Create synthetic training data for premium prediction
        """
        n_samples = 1000
        
        # Generate variations around current values
        spot_range = np.random.uniform(feature_dict['spot'] * 0.8, feature_dict['spot'] * 1.2, n_samples)
        strike_range = np.random.uniform(feature_dict['strike'] * 0.8, feature_dict['strike'] * 1.2, n_samples)
        time_range = np.random.uniform(max(0.01, feature_dict['time_to_expiry'] * 0.5), 
                                      feature_dict['time_to_expiry'] * 1.5, n_samples)
        vol_range = np.random.uniform(0.15, 0.60, n_samples)
        
        X_train = pd.DataFrame({
            'spot': spot_range,
            'strike': strike_range,
            'moneyness': spot_range / strike_range,
            'time_to_expiry': time_range,
            'volatility': vol_range,
            'volume': np.random.uniform(0, 15, n_samples),  # log scale
            'open_interest': np.random.uniform(0, 15, n_samples),
            'delta': np.random.uniform(0.3, 0.8, n_samples),
            'gamma': np.random.uniform(0, 0.1, n_samples),
            'theta': np.random.uniform(-5, 0, n_samples),
            'vega': np.random.uniform(0, 2, n_samples)
        })
        
        # Calculate target premiums using Black-Scholes approximation
        y_train = []
        for i in range(n_samples):
            intrinsic = max(0, X_train['spot'].iloc[i] - X_train['strike'].iloc[i])
            time_value = X_train['spot'].iloc[i] * X_train['volatility'].iloc[i] * np.sqrt(X_train['time_to_expiry'].iloc[i]) / 4
            premium = intrinsic + time_value
            y_train.append(premium)
        
        return X_train, np.array(y_train)
    
    def _fallback_prediction(self, current_price: float) -> Dict[str, float]:
        """
        Fallback prediction when models fail
        """
        return {
            'predicted_price': current_price * 1.02,  # 2% growth assumption
            'confidence': 0.5,
            'model': 'Fallback'
        }
    
    def predict_comprehensive(self, symbol: str, spot: float, strike: float, 
                            time_to_expiry: float, volatility: float, 
                            volume: int, open_interest: int,
                            historical_data: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """
        Comprehensive prediction combining all models
        """
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'models_used': []
        }
        
        # Calculate Greeks
        greeks = self.calculate_greeks(spot, strike, time_to_expiry, volatility)
        results['greeks'] = greeks
        results['models_used'].append('Greeks')
        
        # Generate historical data if not provided
        if historical_data is None or len(historical_data) < 10:
            historical_data = self._generate_synthetic_history(
                pd.DataFrame({'close': [spot], 'volume': [volume]}), 
                30
            )
        
        # LSTM Price Prediction
        lstm_result = self.predict_price_lstm(historical_data, days_ahead=7)
        results['lstm_prediction'] = lstm_result
        results['models_used'].append('LSTM')
        
        # Random Forest Action Classification
        features = self._extract_features(historical_data)
        rf_result = self.predict_action_random_forest(features)
        results['action_prediction'] = rf_result
        results['models_used'].append('RandomForest')
        
        # XGBoost Premium Prediction
        xgb_result = self.predict_premium_xgboost(
            spot, strike, time_to_expiry, volatility, 
            volume, open_interest, greeks
        )
        results['premium_prediction'] = xgb_result
        results['models_used'].append('XGBoost')
        
        # Market Sentiment
        sentiment = self.get_market_sentiment(symbol)
        results['sentiment'] = sentiment
        results['models_used'].append('Sentiment')
        
        # Aggregate confidence
        confidences = [
            lstm_result['confidence'],
            rf_result['confidence'],
            xgb_result['confidence'],
            sentiment['confidence']
        ]
        results['overall_confidence'] = float(np.mean(confidences))
        
        # Final recommendation
        results['recommendation'] = self._generate_recommendation(results)
        
        return results
    
    def _generate_recommendation(self, results: Dict) -> Dict[str, any]:
        """
        Generate final trading recommendation based on all models
        """
        action = results['action_prediction']['action']
        premium = results['premium_prediction']['predicted_premium']
        confidence = results['overall_confidence']
        sentiment = results['sentiment']['sentiment_label']
        
        # Adjust confidence based on consensus
        if action == 'BUY' and sentiment == 'Bullish':
            confidence = min(0.95, confidence * 1.1)
        elif action == 'SELL' and sentiment == 'Bearish':
            confidence = min(0.95, confidence * 1.1)
        elif action != 'HOLD' and sentiment == 'Neutral':
            confidence = confidence * 0.9
        
        return {
            'action': action,
            'entry_price': premium,
            'confidence': round(confidence, 3),
            'risk_level': 'LOW' if confidence > 0.75 else 'MEDIUM' if confidence > 0.6 else 'HIGH',
            'models_consensus': f"{len(results['models_used'])} models",
            'sentiment_aligned': action == 'BUY' and sentiment == 'Bullish' or action == 'SELL' and sentiment == 'Bearish'
        }


# Singleton instance
_predictor_instance = None

def get_ml_predictor() -> OptionsMLPredictor:
    """Get or create ML predictor singleton"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = OptionsMLPredictor()
    return _predictor_instance
