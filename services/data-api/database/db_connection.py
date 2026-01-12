"""
Database Connection Manager for TimescaleDB/PostgreSQL
"""

import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import ThreadedConnectionPool
import logging
import os
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL/TimescaleDB connections"""
    
    def __init__(
        self,
        host: str = "timescaledb",
        port: int = 5432,
        user: str = "trading_user",
        password: str = "trading_pass",
        database: str = "trading_db",
        min_conn: int = 1,
        max_conn: int = 10
    ):
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        
        try:
            self.pool = ThreadedConnectionPool(
                min_conn,
                max_conn,
                **self.connection_params
            )
            logger.info(f"Database connection pool created: {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            self.pool = None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            if self.pool:
                conn = self.pool.getconn()
                yield conn
            else:
                # Fallback to direct connection
                conn = psycopg2.connect(**self.connection_params)
                yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                if self.pool:
                    self.pool.putconn(conn)
                else:
                    conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Get a cursor with automatic commit/rollback"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database query error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a SELECT query and return results"""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT query and return affected rows"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_batch(self, query: str, data: List[tuple]) -> int:
        """Execute batch INSERT with multiple rows"""
        with self.get_cursor(commit=True) as cursor:
            execute_values(cursor, query, data)
            return cursor.rowcount
    
    def initialize_schema(self):
        """Initialize database schema"""
        schema_sql = """
        -- Enable TimescaleDB extension
        CREATE EXTENSION IF NOT EXISTS timescaledb;
        
        -- Stock master table
        CREATE TABLE IF NOT EXISTS stocks (
            symbol VARCHAR(20) PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            market VARCHAR(20) NOT NULL,
            sector VARCHAR(100),
            index_name VARCHAR(100),
            last_updated TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Stock prices time-series
        CREATE TABLE IF NOT EXISTS stock_prices (
            time TIMESTAMPTZ NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            market VARCHAR(20) NOT NULL,
            current_price DOUBLE PRECISION,
            change_percent DOUBLE PRECISION,
            volume BIGINT,
            market_cap BIGINT,
            pe_ratio DOUBLE PRECISION,
            PRIMARY KEY (time, symbol, market)
        );
        
        -- Convert to hypertable if not already
        SELECT create_hypertable('stock_prices', 'time', if_not_exists => TRUE);
        
        -- Options master table
        CREATE TABLE IF NOT EXISTS options (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            market VARCHAR(20) NOT NULL,
            option_type VARCHAR(10) NOT NULL,
            strike_price DOUBLE PRECISION NOT NULL,
            entry_price DOUBLE PRECISION,
            expiration_date DATE NOT NULL,
            days_to_expiry INTEGER,
            last_updated TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(symbol, option_type, strike_price, expiration_date)
        );
        
        -- Options predictions time-series
        CREATE TABLE IF NOT EXISTS option_predictions (
            time TIMESTAMPTZ NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            option_type VARCHAR(10) NOT NULL,
            strike_price DOUBLE PRECISION NOT NULL,
            expiration_date DATE NOT NULL,
            target1 DOUBLE PRECISION,
            target1_confidence DOUBLE PRECISION,
            target2 DOUBLE PRECISION,
            target2_confidence DOUBLE PRECISION,
            target3 DOUBLE PRECISION,
            target3_confidence DOUBLE PRECISION,
            recommendation VARCHAR(10),
            overall_confidence DOUBLE PRECISION,
            risk_level VARCHAR(20),
            implied_volatility DOUBLE PRECISION,
            delta DOUBLE PRECISION,
            open_interest INTEGER,
            volume INTEGER,
            PRIMARY KEY (time, symbol, option_type, strike_price, expiration_date)
        );
        
        SELECT create_hypertable('option_predictions', 'time', if_not_exists => TRUE);
        
        -- NSE option chain data
        CREATE TABLE IF NOT EXISTS nse_option_chain (
            time TIMESTAMPTZ NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            asset_type VARCHAR(20) NOT NULL,
            expiry_date DATE NOT NULL,
            strike_price DOUBLE PRECISION NOT NULL,
            option_type VARCHAR(10) NOT NULL,
            last_price DOUBLE PRECISION,
            change DOUBLE PRECISION,
            percent_change DOUBLE PRECISION,
            volume INTEGER,
            open_interest INTEGER,
            oi_change INTEGER,
            implied_volatility DOUBLE PRECISION,
            bid_price DOUBLE PRECISION,
            ask_price DOUBLE PRECISION,
            underlying_value DOUBLE PRECISION,
            PRIMARY KEY (time, symbol, expiry_date, strike_price, option_type)
        );
        
        SELECT create_hypertable('nse_option_chain', 'time', if_not_exists => TRUE);
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);
        CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);
        CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices(symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_options_symbol ON options(symbol);
        CREATE INDEX IF NOT EXISTS idx_options_expiry ON options(expiration_date);
        CREATE INDEX IF NOT EXISTS idx_option_predictions_symbol ON option_predictions(symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_nse_option_chain_symbol ON nse_option_chain(symbol, time DESC);
        """
        
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute(schema_sql)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Global database instance
db = None

def get_db() -> DatabaseConnection:
    """Get or create database connection"""
    global db
    if db is None:
        db = DatabaseConnection(
            host=os.getenv('TIMESCALEDB_HOST', 'timescaledb'),
            port=int(os.getenv('TIMESCALEDB_PORT', 5432)),
            user=os.getenv('TIMESCALEDB_USER', 'trading_user'),
            password=os.getenv('TIMESCALEDB_PASSWORD', 'trading_pass'),
            database=os.getenv('TIMESCALEDB_DB', 'trading_db')
        )
    return db
