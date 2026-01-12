"""
Ensemble Model - Combines multiple models for robust predictions
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """Ensemble predictor combining multiple ML models"""
    
    def __init__(self, models: Optional[List[str]] = None):
        """
        Initialize ensemble predictor
        
        Args:
            models: List of model names to include in ensemble
        """
        self.models = models or ['lstm', 'transformer', 'gradient_boost']
        self.weights = [0.4, 0.35, 0.25]  # Model weights for ensemble
        self.version = '1.0.0'
        
        logger.info(f"EnsemblePredictor initialized with models: {self.models}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make ensemble prediction by combining multiple models
        
        Args:
            features: Input features for prediction
            
        Returns:
            Ensemble prediction with individual model contributions
        """
        try:
            symbol = features.get('symbol', 'UNKNOWN')
            current_price = features.get('current_price', 100.0)
            
            # Simulate predictions from different models
            predictions = []
            
            for i, model_name in enumerate(self.models):
                # Each model gives slightly different predictions
                direction_prob = np.random.uniform(0.4, 0.9)
                direction = 'bullish' if direction_prob > 0.5 else 'bearish'
                
                if direction == 'bullish':
                    price_change = np.random.uniform(0.005, 0.04)
                else:
                    price_change = np.random.uniform(-0.04, -0.005)
                
                predictions.append({
                    'model': model_name,
                    'price_change': price_change,
                    'confidence': float(np.random.uniform(0.65, 0.85)),
                    'weight': self.weights[i]
                })
            
            # Calculate weighted ensemble prediction
            weighted_change = sum(p['price_change'] * p['weight'] for p in predictions)
            ensemble_confidence = sum(p['confidence'] * p['weight'] for p in predictions)
            
            predicted_price = current_price * (1 + weighted_change)
            direction = 'bullish' if weighted_change > 0 else 'bearish'
            
            return {
                'symbol': symbol,
                'model': 'ensemble',
                'predicted_price': round(predicted_price, 2),
                'current_price': current_price,
                'price_change_pct': round(weighted_change * 100, 2),
                'direction': direction,
                'confidence': round(ensemble_confidence, 3),
                'individual_predictions': predictions,
                'ensemble_weights': dict(zip(self.models, self.weights)),
                'horizon': '1d',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            raise
    
    def update_weights(self, performance_metrics: Dict[str, float]) -> None:
        """
        Update ensemble weights based on model performance
        
        Args:
            performance_metrics: Dict of model_name -> performance_score
        """
        # Normalize weights based on performance
        total_performance = sum(performance_metrics.values())
        self.weights = [
            performance_metrics.get(model, 0.33) / total_performance 
            for model in self.models
        ]
        logger.info(f"Updated ensemble weights: {dict(zip(self.models, self.weights))}")
    
    def get_model_contributions(self, prediction: Dict[str, Any]) -> Dict[str, float]:
        """Get individual model contributions to final prediction"""
        return {
            pred['model']: pred['price_change'] * pred['weight']
            for pred in prediction.get('individual_predictions', [])
        }
