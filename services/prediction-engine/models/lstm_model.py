"""
LSTM Model for Time Series Prediction
"""

import logging
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    """LSTM Neural Network for price prediction"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 3)  # 3 classes: BUY, HOLD, SELL
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        """Forward pass"""
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # Take output from last time step
        last_output = lstm_out[:, -1, :]
        
        # Fully connected layers
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        out = self.softmax(out)
        
        return out


class LSTMPredictor:
    """LSTM-based trading signal predictor"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 60  # 60 time steps
        self.feature_columns = []
        
        if model_path:
            self.load_model(model_path)
        
        logger.info("LSTM Predictor initialized")
    
    def load_model(self, model_path: str):
        """Load pre-trained model"""
        try:
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            
            input_size = checkpoint['input_size']
            self.model = LSTMModel(input_size=input_size)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            self.scaler = checkpoint.get('scaler', self.scaler)
            self.feature_columns = checkpoint.get('feature_columns', [])
            
            logger.info(f"LSTM model loaded from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load LSTM model: {e}")
    
    async def predict(self, features: pd.DataFrame) -> Dict:
        """
        Generate prediction from features
        
        Args:
            features: DataFrame with technical indicators and features
        
        Returns:
            Dictionary with prediction, confidence, etc.
        """
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Prepare input sequence
            X = self._prepare_input(features)
            
            # Make prediction
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X).unsqueeze(0)  # Add batch dimension
                output = self.model(X_tensor)
                probabilities = output.numpy()[0]
            
            # Interpret results
            signal_idx = np.argmax(probabilities)
            signals = ['SELL', 'HOLD', 'BUY']
            
            signal = signals[signal_idx]
            confidence = float(probabilities[signal_idx])
            
            # Calculate expected return based on historical patterns
            expected_return = self._calculate_expected_return(features, signal)
            
            # Calculate risk score
            risk_score = self._calculate_risk(features)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'expected_return': expected_return,
                'risk_score': risk_score,
                'probabilities': {
                    'buy': float(probabilities[2]),
                    'hold': float(probabilities[1]),
                    'sell': float(probabilities[0])
                },
                'model': 'LSTM'
            }
            
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            raise
    
    def _prepare_input(self, features: pd.DataFrame) -> np.ndarray:
        """Prepare input sequence for model"""
        # Select relevant features
        if self.feature_columns:
            feature_df = features[self.feature_columns].tail(self.sequence_length)
        else:
            # Use all numeric columns
            feature_df = features.select_dtypes(include=[np.number]).tail(self.sequence_length)
        
        # Handle missing values
        feature_df = feature_df.fillna(method='ffill').fillna(0)
        
        # Scale features
        scaled = self.scaler.fit_transform(feature_df)
        
        # Pad if sequence is too short
        if len(scaled) < self.sequence_length:
            padding = np.zeros((self.sequence_length - len(scaled), scaled.shape[1]))
            scaled = np.vstack([padding, scaled])
        
        return scaled
    
    def _calculate_expected_return(self, features: pd.DataFrame, signal: str) -> float:
        """Calculate expected return based on historical patterns"""
        try:
            # Get recent returns
            if 'price_change_1d' in features.columns:
                recent_returns = features['price_change_1d'].tail(20).mean()
            else:
                recent_returns = 0
            
            # Adjust based on signal
            multipliers = {'BUY': 1.5, 'HOLD': 1.0, 'SELL': -1.5}
            expected = recent_returns * multipliers.get(signal, 1.0)
            
            return float(expected)
            
        except Exception as e:
            logger.error(f"Error calculating expected return: {e}")
            return 0.0
    
    def _calculate_risk(self, features: pd.DataFrame) -> float:
        """Calculate risk score from volatility and other factors"""
        try:
            risk_score = 0.5  # Default medium risk
            
            # Volatility factor
            if 'volatility_20d' in features.columns:
                vol = features['volatility_20d'].iloc[-1]
                risk_score = min(1.0, vol / 0.5)  # Normalize to 0-1
            
            # ATR factor
            if 'atr' in features.columns and 'price' in features.columns:
                atr = features['atr'].iloc[-1]
                price = features['price'].iloc[-1]
                atr_pct = atr / price
                risk_score = (risk_score + min(1.0, atr_pct * 10)) / 2
            
            return float(risk_score)
            
        except Exception as e:
            logger.error(f"Error calculating risk: {e}")
            return 0.5
    
    def train(self, train_data: pd.DataFrame, labels: np.ndarray, epochs: int = 50):
        """Train the LSTM model"""
        try:
            # Prepare training data
            X_train, y_train = self._prepare_training_data(train_data, labels)
            
            # Initialize model if not exists
            if self.model is None:
                input_size = X_train.shape[2]
                self.model = LSTMModel(input_size=input_size)
            
            # Training setup
            criterion = nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            # Training loop
            self.model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                
                outputs = self.model(torch.FloatTensor(X_train))
                loss = criterion(outputs, torch.LongTensor(y_train))
                
                loss.backward()
                optimizer.step()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
            
            logger.info("LSTM training completed")
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            raise
    
    def _prepare_training_data(self, data: pd.DataFrame, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for training"""
        # Implementation for creating sequences from data
        # This is a simplified version
        sequences = []
        sequence_labels = []
        
        # Select numeric features
        feature_df = data.select_dtypes(include=[np.number])
        scaled_data = self.scaler.fit_transform(feature_df)
        
        # Create sequences
        for i in range(len(scaled_data) - self.sequence_length):
            sequences.append(scaled_data[i:i + self.sequence_length])
            sequence_labels.append(labels[i + self.sequence_length])
        
        return np.array(sequences), np.array(sequence_labels)
