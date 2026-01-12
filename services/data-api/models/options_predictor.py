"""
Options Prediction Model with Multiple Targets and Confidence Levels
Predicts entry price, expiration date, and multiple price targets with confidence levels
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptionPrediction:
    """Options prediction with multiple targets"""
    symbol: str
    company: str
    market: str
    option_type: str  # CALL or PUT
    entry_price: float
    current_price: float
    strike_price: float
    expiration_date: str
    days_to_expiry: int
    target1: float
    target1_confidence: float
    target2: float
    target2_confidence: float
    target3: float
    target3_confidence: float
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    open_interest: int
    volume: int
    recommendation: str  # BUY, SELL, HOLD
    overall_confidence: float
    risk_level: str  # LOW, MEDIUM, HIGH
    max_profit_potential: float
    max_loss_potential: float
    breakeven_price: float
    timestamp: str


class OptionsPredictor:
    """Advanced options prediction with ML and technical analysis"""
    
    def __init__(self):
        self.models = {}
        self.historical_accuracy = {}
        
    def calculate_greeks(self, 
                        spot_price: float,
                        strike_price: float,
                        time_to_expiry: float,
                        volatility: float,
                        risk_free_rate: float = 0.05,
                        option_type: str = 'call') -> Dict[str, float]:
        """
        Calculate option Greeks (simplified Black-Scholes)
        
        Returns: Dict with delta, gamma, theta, vega, rho
        """
        from scipy.stats import norm
        
        try:
            # Time in years
            T = time_to_expiry / 365.0
            
            if T <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
            # d1 and d2 from Black-Scholes
            d1 = (np.log(spot_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * T) / (volatility * np.sqrt(T))
            d2 = d1 - volatility * np.sqrt(T)
            
            if option_type.upper() == 'CALL':
                delta = norm.cdf(d1)
                theta = (-(spot_price * norm.pdf(d1) * volatility) / (2 * np.sqrt(T)) -
                        risk_free_rate * strike_price * np.exp(-risk_free_rate * T) * norm.cdf(d2))
            else:  # PUT
                delta = -norm.cdf(-d1)
                theta = (-(spot_price * norm.pdf(d1) * volatility) / (2 * np.sqrt(T)) +
                        risk_free_rate * strike_price * np.exp(-risk_free_rate * T) * norm.cdf(-d2))
            
            # Gamma is same for calls and puts
            gamma = norm.pdf(d1) / (spot_price * volatility * np.sqrt(T))
            
            # Vega is same for calls and puts
            vega = spot_price * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for percentage change
            
            # Rho
            if option_type.upper() == 'CALL':
                rho = strike_price * T * np.exp(-risk_free_rate * T) * norm.cdf(d2) / 100
            else:
                rho = -strike_price * T * np.exp(-risk_free_rate * T) * norm.cdf(-d2) / 100
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'theta': round(theta / 365, 4),  # Per day
                'vega': round(vega, 4),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    def calculate_multiple_targets(self,
                                   current_price: float,
                                   volatility: float,
                                   days_to_expiry: int,
                                   option_type: str,
                                   spot_price: float,
                                   strike_price: float) -> Tuple[List[float], List[float]]:
        """
        Calculate three price targets with confidence levels
        
        Returns: (targets, confidences)
        """
        # Calculate expected moves based on volatility
        annual_vol = volatility
        days_vol = annual_vol * np.sqrt(days_to_expiry / 365.0)
        
        # Conservative target (1 standard deviation)
        conservative_move = current_price * days_vol * 0.5
        target1 = current_price + conservative_move
        confidence1 = 0.85  # High confidence for conservative target
        
        # Moderate target (1.5 standard deviations)
        moderate_move = current_price * days_vol * 0.75
        target2 = current_price + moderate_move
        confidence2 = 0.65  # Medium confidence
        
        # Aggressive target (2+ standard deviations)
        aggressive_move = current_price * days_vol * 1.2
        target3 = current_price + aggressive_move
        confidence3 = 0.40  # Lower confidence for aggressive target
        
        # Adjust confidence based on time to expiry
        time_factor = min(1.0, days_to_expiry / 30.0)  # Reduce confidence for near-term expiry
        confidence1 *= time_factor
        confidence2 *= time_factor
        confidence3 *= time_factor
        
        # Adjust confidence based on moneyness
        moneyness = spot_price / strike_price
        if option_type.upper() == 'CALL':
            if moneyness > 1.05:  # ITM call
                confidence1 *= 1.1
                confidence2 *= 1.05
            elif moneyness < 0.95:  # OTM call
                confidence1 *= 0.9
                confidence2 *= 0.85
                confidence3 *= 0.80
        else:  # PUT
            if moneyness < 0.95:  # ITM put
                confidence1 *= 1.1
                confidence2 *= 1.05
            elif moneyness > 1.05:  # OTM put
                confidence1 *= 0.9
                confidence2 *= 0.85
                confidence3 *= 0.80
        
        # Cap confidence at 95%
        confidence1 = min(0.95, confidence1)
        confidence2 = min(0.90, confidence2)
        confidence3 = min(0.85, confidence3)
        
        targets = [round(target1, 2), round(target2, 2), round(target3, 2)]
        confidences = [round(confidence1, 2), round(confidence2, 2), round(confidence3, 2)]
        
        return targets, confidences
    
    def determine_recommendation(self,
                                delta: float,
                                days_to_expiry: int,
                                implied_vol: float,
                                open_interest: int,
                                volume: int,
                                moneyness: float) -> Tuple[str, float, str]:
        """
        Determine recommendation (BUY/SELL/HOLD) with confidence and risk level
        
        Returns: (recommendation, confidence, risk_level)
        """
        score = 0
        factors = []
        
        # Factor 1: Delta (momentum indicator)
        if abs(delta) > 0.7:
            score += 2
            factors.append("Strong delta")
        elif abs(delta) > 0.4:
            score += 1
            factors.append("Moderate delta")
        
        # Factor 2: Time to expiry
        if days_to_expiry > 30:
            score += 2
            factors.append("Good time cushion")
        elif days_to_expiry > 15:
            score += 1
            factors.append("Adequate time")
        else:
            score -= 1
            factors.append("Limited time")
        
        # Factor 3: Liquidity (OI and volume)
        if open_interest > 1000 and volume > 500:
            score += 2
            factors.append("High liquidity")
        elif open_interest > 100 and volume > 50:
            score += 1
            factors.append("Moderate liquidity")
        else:
            score -= 1
            factors.append("Low liquidity")
        
        # Factor 4: Implied volatility
        if 0.2 < implied_vol < 0.6:
            score += 1
            factors.append("Normal volatility")
        elif implied_vol > 0.8:
            score -= 1
            factors.append("High volatility")
        
        # Factor 5: Moneyness
        if 0.95 < moneyness < 1.05:
            score += 2
            factors.append("Near ATM")
        elif 0.90 < moneyness < 1.10:
            score += 1
            factors.append("Moderate moneyness")
        
        # Determine recommendation
        if score >= 6:
            recommendation = "STRONG BUY"
            confidence = 0.85
        elif score >= 4:
            recommendation = "BUY"
            confidence = 0.70
        elif score >= 2:
            recommendation = "HOLD"
            confidence = 0.60
        elif score >= 0:
            recommendation = "WEAK HOLD"
            confidence = 0.45
        else:
            recommendation = "AVOID"
            confidence = 0.30
        
        # Determine risk level
        risk_score = 0
        if days_to_expiry < 7:
            risk_score += 2
        elif days_to_expiry < 15:
            risk_score += 1
        
        if implied_vol > 0.7:
            risk_score += 2
        elif implied_vol > 0.5:
            risk_score += 1
        
        if open_interest < 100 or volume < 50:
            risk_score += 2
        elif open_interest < 500 or volume < 200:
            risk_score += 1
        
        if risk_score >= 4:
            risk_level = "HIGH"
        elif risk_score >= 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        logger.info(f"Recommendation: {recommendation} (confidence: {confidence}, risk: {risk_level}) - {', '.join(factors)}")
        
        return recommendation, confidence, risk_level
    
    def predict_option(self,
                      symbol: str,
                      company: str,
                      market: str,
                      spot_price: float,
                      strike_price: float,
                      option_price: float,
                      expiration_date: str,
                      option_type: str,
                      implied_volatility: float,
                      open_interest: int,
                      volume: int) -> OptionPrediction:
        """
        Generate complete option prediction with multiple targets
        
        Args:
            symbol: Stock symbol
            company: Company name
            market: US or INDIA
            spot_price: Current stock price
            strike_price: Option strike price
            option_price: Current option price
            expiration_date: Expiration date (YYYY-MM-DD)
            option_type: CALL or PUT
            implied_volatility: Implied volatility (decimal)
            open_interest: Open interest
            volume: Trading volume
        
        Returns:
            OptionPrediction object
        """
        try:
            # Calculate days to expiry
            expiry_dt = datetime.strptime(expiration_date, '%Y-%m-%d')
            days_to_expiry = (expiry_dt - datetime.now()).days
            
            if days_to_expiry < 0:
                raise ValueError("Option has already expired")
            
            # Calculate Greeks
            greeks = self.calculate_greeks(
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=days_to_expiry,
                volatility=implied_volatility,
                option_type=option_type
            )
            
            # Calculate multiple targets
            targets, confidences = self.calculate_multiple_targets(
                current_price=option_price,
                volatility=implied_volatility,
                days_to_expiry=days_to_expiry,
                option_type=option_type,
                spot_price=spot_price,
                strike_price=strike_price
            )
            
            # Calculate moneyness
            moneyness = spot_price / strike_price
            
            # Determine recommendation
            recommendation, overall_confidence, risk_level = self.determine_recommendation(
                delta=greeks['delta'],
                days_to_expiry=days_to_expiry,
                implied_vol=implied_volatility,
                open_interest=open_interest,
                volume=volume,
                moneyness=moneyness
            )
            
            # Calculate profit/loss potential
            if option_type.upper() == 'CALL':
                max_profit_potential = (targets[2] - option_price) / option_price * 100
                max_loss_potential = -100  # Premium paid
                breakeven_price = strike_price + option_price
            else:  # PUT
                max_profit_potential = (targets[2] - option_price) / option_price * 100
                max_loss_potential = -100  # Premium paid
                breakeven_price = strike_price - option_price
            
            # Create prediction object
            prediction = OptionPrediction(
                symbol=symbol,
                company=company,
                market=market,
                option_type=option_type.upper(),
                entry_price=option_price,
                current_price=option_price,
                strike_price=strike_price,
                expiration_date=expiration_date,
                days_to_expiry=days_to_expiry,
                target1=targets[0],
                target1_confidence=confidences[0],
                target2=targets[1],
                target2_confidence=confidences[1],
                target3=targets[2],
                target3_confidence=confidences[2],
                implied_volatility=implied_volatility,
                delta=greeks['delta'],
                gamma=greeks['gamma'],
                theta=greeks['theta'],
                vega=greeks['vega'],
                open_interest=open_interest,
                volume=volume,
                recommendation=recommendation,
                overall_confidence=overall_confidence,
                risk_level=risk_level,
                max_profit_potential=round(max_profit_potential, 2),
                max_loss_potential=round(max_loss_potential, 2),
                breakeven_price=round(breakeven_price, 2),
                timestamp=datetime.now().isoformat()
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating option prediction for {symbol}: {e}")
            raise
    
    def batch_predict_options(self, options_data: List[Dict]) -> List[OptionPrediction]:
        """
        Generate predictions for multiple options
        
        Args:
            options_data: List of option data dictionaries
        
        Returns:
            List of OptionPrediction objects
        """
        predictions = []
        
        for option_data in options_data:
            try:
                prediction = self.predict_option(**option_data)
                predictions.append(prediction)
            except Exception as e:
                logger.error(f"Error in batch prediction: {e}")
                continue
        
        return predictions
    
    def filter_best_opportunities(self, 
                                 predictions: List[OptionPrediction],
                                 min_confidence: float = 0.65,
                                 max_risk: str = "MEDIUM") -> List[OptionPrediction]:
        """
        Filter options to show only the best opportunities
        
        Args:
            predictions: List of predictions
            min_confidence: Minimum confidence level
            max_risk: Maximum acceptable risk level
        
        Returns:
            Filtered list of best opportunities
        """
        risk_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        max_risk_level = risk_levels.get(max_risk, 2)
        
        filtered = [
            pred for pred in predictions
            if pred.overall_confidence >= min_confidence
            and risk_levels.get(pred.risk_level, 3) <= max_risk_level
            and pred.recommendation in ["BUY", "STRONG BUY"]
        ]
        
        # Sort by confidence
        filtered.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return filtered


if __name__ == "__main__":
    # Test the predictor
    logging.basicConfig(level=logging.INFO)
    
    predictor = OptionsPredictor()
    
    # Example prediction
    prediction = predictor.predict_option(
        symbol="AAPL",
        company="Apple Inc",
        market="US",
        spot_price=185.50,
        strike_price=190.00,
        option_price=3.50,
        expiration_date="2026-02-21",
        option_type="CALL",
        implied_volatility=0.35,
        open_interest=5000,
        volume=1200
    )
    
    print(f"\n{'='*80}")
    print(f"Option Prediction for {prediction.symbol}")
    print(f"{'='*80}")
    print(f"Company: {prediction.company}")
    print(f"Type: {prediction.option_type}")
    print(f"Strike: ${prediction.strike_price}")
    print(f"Entry Price: ${prediction.entry_price}")
    print(f"Expiration: {prediction.expiration_date} ({prediction.days_to_expiry} days)")
    print(f"\nTargets:")
    print(f"  Target 1: ${prediction.target1} (Confidence: {prediction.target1_confidence*100:.1f}%)")
    print(f"  Target 2: ${prediction.target2} (Confidence: {prediction.target2_confidence*100:.1f}%)")
    print(f"  Target 3: ${prediction.target3} (Confidence: {prediction.target3_confidence*100:.1f}%)")
    print(f"\nGreeks:")
    print(f"  Delta: {prediction.delta}")
    print(f"  Gamma: {prediction.gamma}")
    print(f"  Theta: {prediction.theta}")
    print(f"  Vega: {prediction.vega}")
    print(f"\nRecommendation: {prediction.recommendation}")
    print(f"Confidence: {prediction.overall_confidence*100:.1f}%")
    print(f"Risk Level: {prediction.risk_level}")
    print(f"Max Profit Potential: {prediction.max_profit_potential:.1f}%")
    print(f"Breakeven: ${prediction.breakeven_price}")
    print(f"{'='*80}")
