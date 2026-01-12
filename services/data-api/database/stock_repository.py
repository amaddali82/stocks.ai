"""
Stock data repository for database operations
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class StockRepository:
    """Repository for stock data operations"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def upsert_stock(self, stock_data: Dict) -> bool:
        """Insert or update stock master data"""
        query = """
        INSERT INTO stocks (symbol, company_name, market, sector, index_name, last_updated)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (symbol) 
        DO UPDATE SET 
            company_name = EXCLUDED.company_name,
            market = EXCLUDED.market,
            sector = EXCLUDED.sector,
            index_name = EXCLUDED.index_name,
            last_updated = NOW()
        """
        
        try:
            self.db.execute_insert(query, (
                stock_data['symbol'],
                stock_data['company'],
                stock_data['market'],
                stock_data.get('sector', 'N/A'),
                stock_data.get('index', 'N/A')
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting stock {stock_data['symbol']}: {e}")
            return False
    
    def insert_stock_price(self, price_data: Dict) -> bool:
        """Insert stock price data"""
        query = """
        INSERT INTO stock_prices 
        (time, symbol, market, current_price, change_percent, volume, market_cap, pe_ratio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (time, symbol, market) DO UPDATE SET
            current_price = EXCLUDED.current_price,
            change_percent = EXCLUDED.change_percent,
            volume = EXCLUDED.volume,
            market_cap = EXCLUDED.market_cap,
            pe_ratio = EXCLUDED.pe_ratio
        """
        
        try:
            self.db.execute_insert(query, (
                price_data.get('time', datetime.now()),
                price_data['symbol'],
                price_data['market'],
                price_data['current_price'],
                price_data.get('change_percent', 0),
                price_data.get('volume', 0),
                price_data.get('market_cap'),
                price_data.get('pe_ratio')
            ))
            return True
        except Exception as e:
            logger.error(f"Error inserting stock price for {price_data['symbol']}: {e}")
            return False
    
    def get_latest_stocks(self, market: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get latest stock data"""
        query = """
        SELECT DISTINCT ON (s.symbol) 
            s.symbol, s.company_name, s.market, s.sector, s.index_name,
            sp.current_price, sp.change_percent, sp.volume, sp.market_cap, sp.pe_ratio,
            sp.time as last_updated
        FROM stocks s
        LEFT JOIN stock_prices sp ON s.symbol = sp.symbol
        WHERE sp.time >= NOW() - INTERVAL '1 day'
        """
        
        params = []
        if market:
            query += " AND s.market = %s"
            params.append(market)
        
        query += " ORDER BY s.symbol, sp.time DESC LIMIT %s"
        params.append(limit)
        
        try:
            rows = self.db.execute_query(query, tuple(params))
            return [
                {
                    'symbol': row[0],
                    'company': row[1],
                    'market': row[2],
                    'sector': row[3],
                    'index': row[4],
                    'current_price': float(row[5]) if row[5] else 0,
                    'change_percent': float(row[6]) if row[6] else 0,
                    'volume': int(row[7]) if row[7] else 0,
                    'market_cap': int(row[8]) if row[8] else None,
                    'pe_ratio': float(row[9]) if row[9] else None,
                    'last_updated': row[10]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting latest stocks: {e}")
            return []
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get stock data by symbol"""
        query = """
        SELECT s.symbol, s.company_name, s.market, s.sector, s.index_name,
               sp.current_price, sp.change_percent, sp.volume, sp.market_cap, sp.pe_ratio,
               sp.time as last_updated
        FROM stocks s
        LEFT JOIN stock_prices sp ON s.symbol = sp.symbol
        WHERE s.symbol = %s
        ORDER BY sp.time DESC
        LIMIT 1
        """
        
        try:
            rows = self.db.execute_query(query, (symbol,))
            if rows:
                row = rows[0]
                return {
                    'symbol': row[0],
                    'company': row[1],
                    'market': row[2],
                    'sector': row[3],
                    'index': row[4],
                    'current_price': float(row[5]) if row[5] else 0,
                    'change_percent': float(row[6]) if row[6] else 0,
                    'volume': int(row[7]) if row[7] else 0,
                    'market_cap': int(row[8]) if row[8] else None,
                    'pe_ratio': float(row[9]) if row[9] else None,
                    'last_updated': row[10]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting stock {symbol}: {e}")
            return None
    
    def bulk_upsert_stocks(self, stocks: List[Dict]) -> int:
        """Bulk upsert multiple stocks"""
        success_count = 0
        for stock in stocks:
            if self.upsert_stock(stock):
                success_count += 1
        return success_count
    
    def bulk_insert_prices(self, prices: List[Dict]) -> int:
        """Bulk insert stock prices"""
        success_count = 0
        for price in prices:
            if self.insert_stock_price(price):
                success_count += 1
        return success_count
