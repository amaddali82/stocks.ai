"""
Options data repository for database operations
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from .db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class OptionRepository:
    """Repository for options data operations"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def upsert_option(self, option_data: Dict) -> bool:
        """Insert or update option master data"""
        query = """
        INSERT INTO options 
        (symbol, company_name, market, option_type, strike_price, entry_price, 
         expiration_date, days_to_expiry, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (symbol, option_type, strike_price, expiration_date)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            entry_price = EXCLUDED.entry_price,
            days_to_expiry = EXCLUDED.days_to_expiry,
            last_updated = NOW()
        """
        
        try:
            # Parse expiration date if it's a string
            exp_date = option_data['expiration_date']
            if isinstance(exp_date, str):
                exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
            
            self.db.execute_insert(query, (
                option_data['symbol'],
                option_data['company'],
                option_data['market'],
                option_data['option_type'],
                option_data['strike_price'],
                option_data['entry_price'],
                exp_date,
                option_data.get('days_to_expiry', 0)
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting option for {option_data['symbol']}: {e}")
            return False
    
    def insert_option_prediction(self, prediction: Dict) -> bool:
        """Insert option prediction data"""
        query = """
        INSERT INTO option_predictions
        (time, symbol, option_type, strike_price, expiration_date,
         target1, target1_confidence, target2, target2_confidence,
         target3, target3_confidence, recommendation, overall_confidence,
         risk_level, implied_volatility, delta, open_interest, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (time, symbol, option_type, strike_price, expiration_date)
        DO UPDATE SET
            target1 = EXCLUDED.target1,
            target1_confidence = EXCLUDED.target1_confidence,
            target2 = EXCLUDED.target2,
            target2_confidence = EXCLUDED.target2_confidence,
            target3 = EXCLUDED.target3,
            target3_confidence = EXCLUDED.target3_confidence,
            recommendation = EXCLUDED.recommendation,
            overall_confidence = EXCLUDED.overall_confidence,
            risk_level = EXCLUDED.risk_level,
            implied_volatility = EXCLUDED.implied_volatility,
            delta = EXCLUDED.delta,
            open_interest = EXCLUDED.open_interest,
            volume = EXCLUDED.volume
        """
        
        try:
            # Parse expiration date
            exp_date = prediction['expiration_date']
            if isinstance(exp_date, str):
                exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
            
            self.db.execute_insert(query, (
                prediction.get('time', datetime.now()),
                prediction['symbol'],
                prediction['option_type'],
                prediction['strike_price'],
                exp_date,
                prediction['target1'],
                prediction['target1_confidence'],
                prediction['target2'],
                prediction['target2_confidence'],
                prediction['target3'],
                prediction['target3_confidence'],
                prediction['recommendation'],
                prediction['overall_confidence'],
                prediction['risk_level'],
                prediction.get('implied_volatility', 0),
                prediction.get('delta', 0),
                prediction.get('open_interest', 0),
                prediction.get('volume', 0)
            ))
            return True
        except Exception as e:
            logger.error(f"Error inserting option prediction for {prediction['symbol']}: {e}")
            return False
    
    def get_latest_predictions(
        self, 
        market: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Dict]:
        """Get latest option predictions"""
        query = """
        SELECT DISTINCT ON (op.symbol, op.option_type, op.strike_price, op.expiration_date)
            op.symbol, o.company_name, o.market, op.option_type,
            op.strike_price, o.entry_price, op.expiration_date, o.days_to_expiry,
            op.target1, op.target1_confidence, op.target2, op.target2_confidence,
            op.target3, op.target3_confidence, op.recommendation, op.overall_confidence,
            op.risk_level, op.implied_volatility, op.delta, op.open_interest, op.volume,
            op.time as last_updated
        FROM option_predictions op
        JOIN options o ON 
            op.symbol = o.symbol AND 
            op.option_type = o.option_type AND
            op.strike_price = o.strike_price AND
            op.expiration_date = o.expiration_date
        WHERE op.time >= NOW() - INTERVAL '1 day'
          AND op.overall_confidence >= %s
        """
        
        params = [min_confidence]
        
        if market:
            query += " AND o.market = %s"
            params.append(market)
        
        query += " ORDER BY op.symbol, op.option_type, op.strike_price, op.expiration_date, op.time DESC LIMIT %s"
        params.append(limit)
        
        try:
            rows = self.db.execute_query(query, tuple(params))
            return [
                {
                    'symbol': row[0],
                    'company': row[1],
                    'market': row[2],
                    'option_type': row[3],
                    'strike_price': float(row[4]),
                    'entry_price': float(row[5]) if row[5] else 0,
                    'expiration_date': row[6].strftime('%Y-%m-%d'),
                    'days_to_expiry': int(row[7]) if row[7] else 0,
                    'target1': float(row[8]),
                    'target1_confidence': float(row[9]),
                    'target2': float(row[10]),
                    'target2_confidence': float(row[11]),
                    'target3': float(row[12]),
                    'target3_confidence': float(row[13]),
                    'recommendation': row[14],
                    'overall_confidence': float(row[15]),
                    'risk_level': row[16],
                    'implied_volatility': float(row[17]) if row[17] else 0,
                    'delta': float(row[18]) if row[18] else 0,
                    'open_interest': int(row[19]) if row[19] else 0,
                    'volume': int(row[20]) if row[20] else 0,
                    'max_profit_potential': 0,  # Calculate if needed
                    'breakeven_price': float(row[4]) + float(row[5]) if row[5] else float(row[4])
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting latest predictions: {e}")
            return []
    
    def bulk_upsert_options(self, options: List[Dict]) -> int:
        """Bulk upsert multiple options"""
        success_count = 0
        for option in options:
            if self.upsert_option(option):
                success_count += 1
        return success_count
    
    def bulk_insert_predictions(self, predictions: List[Dict]) -> int:
        """Bulk insert option predictions"""
        success_count = 0
        for prediction in predictions:
            if self.insert_option_prediction(prediction):
                success_count += 1
        return success_count
    
    def insert_nse_option_chain(self, chain_data: Dict) -> int:
        """Insert NSE option chain data"""
        query = """
        INSERT INTO nse_option_chain
        (time, symbol, asset_type, expiry_date, strike_price, option_type,
         last_price, change, percent_change, volume, open_interest, oi_change,
         implied_volatility, bid_price, ask_price, underlying_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (time, symbol, expiry_date, strike_price, option_type)
        DO UPDATE SET
            last_price = EXCLUDED.last_price,
            change = EXCLUDED.change,
            percent_change = EXCLUDED.percent_change,
            volume = EXCLUDED.volume,
            open_interest = EXCLUDED.open_interest,
            oi_change = EXCLUDED.oi_change,
            implied_volatility = EXCLUDED.implied_volatility,
            bid_price = EXCLUDED.bid_price,
            ask_price = EXCLUDED.ask_price,
            underlying_value = EXCLUDED.underlying_value
        """
        
        success_count = 0
        current_time = datetime.now()
        
        try:
            # Parse expiry date
            expiry_str = chain_data.get('expiry_date', '')
            if expiry_str:
                # Try DD-MMM-YYYY format (e.g., "27-Jan-2026")
                try:
                    expiry_date = datetime.strptime(expiry_str, '%d-%b-%Y').date()
                except:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            else:
                expiry_date = (datetime.now() + timedelta(days=30)).date()
            
            # Insert calls
            for call in chain_data.get('calls', []):
                try:
                    self.db.execute_insert(query, (
                        current_time,
                        chain_data['symbol'],
                        chain_data['asset_type'],
                        expiry_date,
                        call['strike_price'],
                        call['option_type'],
                        call.get('last_price', 0),
                        call.get('change', 0),
                        call.get('percent_change', 0),
                        call.get('volume', 0),
                        call.get('open_interest', 0),
                        call.get('oi_change', 0),
                        call.get('implied_volatility', 0),
                        call.get('bid_price', 0),
                        call.get('ask_price', 0),
                        chain_data.get('underlying_value', 0)
                    ))
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error inserting call option: {e}")
            
            # Insert puts
            for put in chain_data.get('puts', []):
                try:
                    self.db.execute_insert(query, (
                        current_time,
                        chain_data['symbol'],
                        chain_data['asset_type'],
                        expiry_date,
                        put['strike_price'],
                        put['option_type'],
                        put.get('last_price', 0),
                        put.get('change', 0),
                        put.get('percent_change', 0),
                        put.get('volume', 0),
                        put.get('open_interest', 0),
                        put.get('oi_change', 0),
                        put.get('implied_volatility', 0),
                        put.get('bid_price', 0),
                        put.get('ask_price', 0),
                        chain_data.get('underlying_value', 0)
                    ))
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error inserting put option: {e}")
            
            logger.info(f"Inserted {success_count} NSE options for {chain_data['symbol']}")
            return success_count
        except Exception as e:
            logger.error(f"Error inserting NSE option chain: {e}")
            return 0
