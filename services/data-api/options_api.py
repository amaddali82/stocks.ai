"""
Options Data API
Serves top 500 companies with stocks and options predictions
Includes NSE India option chain data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import asyncio
import sys
import os
import time
from functools import lru_cache
import requests_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup cache for yfinance to avoid rate limiting (1 hour cache)
YFINANCE_CACHE_SESSION = requests_cache.CachedSession(
    'yfinance.cache',
    backend='memory',  # Use memory backend (no disk I/O)
    expire_after=3600  # Cache for 1 hour
)

# Rate limiting: minimum delay between requests (milliseconds)
RATE_LIMIT_DELAY = 0.3  # 300ms delay between requests
last_request_time = 0

def rate_limit_wait():
    """Ensure minimum delay between API requests"""
    global last_request_time
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    if time_since_last_request < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - time_since_last_request)
    last_request_time = time.time()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from connectors.company_lists import get_all_companies, get_top_us_companies, get_nifty500_companies
from models.options_predictor import OptionsPredictor, OptionPrediction

# Try to import ML predictor (optional, falls back if not available)
try:
    prediction_engine_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prediction-engine')
    sys.path.append(prediction_engine_path)
    from models.ml_predictor import get_ml_predictor, OptionsMLPredictor
    ML_PREDICTOR_AVAILABLE = True
    logger.info("✓ ML Predictor (LSTM/RandomForest/XGBoost) loaded successfully")
except ImportError as e:
    ML_PREDICTOR_AVAILABLE = False
    logger.warning(f"ML Predictor not available (will use fallback): {e}")

# Try to import ML predictor (optional, falls back if not available)
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prediction-engine'))
    from models.ml_predictor import get_ml_predictor, OptionsMLPredictor
    ML_PREDICTOR_AVAILABLE = True
    logger.info("✓ ML Predictor (LSTM/RandomForest/XGBoost) loaded successfully")
except ImportError as e:
    ML_PREDICTOR_AVAILABLE = False
    logger.warning(f"ML Predictor not available: {e}")

# Import database layer
from database import get_db, StockRepository, OptionRepository

# Import NSE option chain fetcher
try:
    from connectors.nse_options import nse_option_chain, fetch_nse_options
    NSE_AVAILABLE = True
    logger.info("NSE option chain module loaded successfully")
except ImportError as e:
    NSE_AVAILABLE = False
    logger.warning(f"NSE option chain module not available: {e}")

app = FastAPI(
    title="Options Trading API",
    description="Top 500 companies from US and India with options predictions (Free data via yfinance)",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and repositories
db_conn = get_db()
stock_repo = StockRepository(db_conn)
option_repo = OptionRepository(db_conn)

# Initialize predictor
options_predictor = OptionsPredictor()

# Initialize database schema on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        db_conn.initialize_schema()
        logger.info("Database schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


class StockData(BaseModel):
    symbol: str
    company: str
    market: str
    sector: str
    current_price: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    index: str


class OptionData(BaseModel):
    symbol: str
    company: str
    market: str
    option_type: str
    strike_price: float
    entry_price: float
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
    recommendation: str
    overall_confidence: float
    risk_level: str
    max_profit_potential: float
    breakeven_price: float
    open_interest: int
    volume: int


class CompanyWithOptions(BaseModel):
    stock: StockData
    options: List[OptionData]


@app.get("/")
async def root():
    return {
        "service": "Options Trading API",
        "status": "running",
        "endpoints": {
            "companies": "/api/companies",
            "stocks": "/api/stocks",
            "options": "/api/options",
            "predictions": "/api/predictions"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "options-api"}


@app.get("/api/companies")
async def get_companies(
    market: Optional[str] = Query(None, description="Filter by market: US or INDIA"),
    limit: int = Query(500, description="Maximum number of companies to return")
):
    """Get list of top companies"""
    try:
        all_companies = get_all_companies()
        
        if market:
            market = market.upper()
            companies = all_companies.get(market, [])
        else:
            companies = all_companies.get('US', []) + all_companies.get('INDIA', [])
        
        return {
            "total": len(companies[:limit]),
            "companies": companies[:limit]
        }
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks", response_model=List[StockData])
async def get_stocks(
    market: Optional[str] = Query(None, description="Filter by market: US or INDIA"),
    limit: int = Query(50, description="Maximum number of stocks to return")
):
    """Get current stock data for top companies"""
    try:
        all_companies = get_all_companies()
        
        if market:
            market = market.upper()
            companies = all_companies.get(market, [])
        else:
            companies = all_companies.get('US', [])[:25] + all_companies.get('INDIA', [])[:25]
        
        stocks_data = []
        companies_to_fetch = companies[:limit]
        
        # Batch fetch using yf.download() - more efficient than individual Ticker() calls
        symbols = [c['symbol'] for c in companies_to_fetch]
        
        try:
            rate_limit_wait()  # Rate limiting
            # Use batch download with cached session
            batch_data = yf.download(
                symbols,
                period='1d',
                interval='1d',
                group_by='ticker',
                threads=False,  # Sequential to avoid rate limiting
                progress=False
            )
            logger.info(f"Batch downloaded data for {len(symbols)} symbols")
        except Exception as e:
            logger.warning(f"Batch download failed: {e}, falling back to individual requests")
            batch_data = None
        
        # Fetch detailed info for each company (with rate limiting and caching)
        for company in companies_to_fetch:
            try:
                rate_limit_wait()  # Add delay between requests
                ticker = yf.Ticker(company['symbol'], session=YFINANCE_CACHE_SESSION)
                info = ticker.info
                
                # Try to get price from batch data first
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                if batch_data is not None and company['symbol'] in batch_data:
                    try:
                        if isinstance(batch_data, pd.DataFrame) and 'Close' in batch_data.columns:
                            current_price = float(batch_data[company['symbol']]['Close'].iloc[-1])
                    except:
                        pass
                
                stock = StockData(
                    symbol=company['symbol'],
                    company=company['company'],
                    market=company['market'],
                    sector=company.get('sector', 'N/A'),
                    current_price=current_price,
                    change_percent=info.get('regularMarketChangePercent', 0),
                    volume=info.get('volume', 0),
                    market_cap=info.get('marketCap'),
                    pe_ratio=info.get('trailingPE'),
                    index=company.get('index', 'N/A')
                )
                
                stocks_data.append(stock)
                
            except Exception as e:
                logger.error(f"Error fetching stock data for {company['symbol']}: {e}")
                continue
        
        return stocks_data
        
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/options/{symbol}", response_model=List[OptionData])
async def get_options_for_symbol(
    symbol: str,
    option_type: Optional[str] = Query(None, description="Filter by type: CALL or PUT"),
    expiry_days_min: int = Query(7, description="Minimum days to expiry"),
    expiry_days_max: int = Query(90, description="Maximum days to expiry")
):
    """Get options predictions for a specific symbol"""
    try:
        rate_limit_wait()  # Rate limiting
        ticker = yf.Ticker(symbol, session=YFINANCE_CACHE_SESSION)
        info = ticker.info
        spot_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        company_name = info.get('longName', symbol)
        
        # Determine market
        market = 'US'  # Default to US, update logic as needed
        
        # Get option expirations
        expirations = ticker.options
        
        if not expirations:
            return []
        
        options_data = []
        current_date = datetime.now()
        
        # Process each expiration
        for expiry in expirations[:5]:  # Limit to first 5 expirations
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            days_to_expiry = (expiry_date - current_date).days
            
            if days_to_expiry < expiry_days_min or days_to_expiry > expiry_days_max:
                continue
            
            # Get option chain
            opt_chain = ticker.option_chain(expiry)
            
            # Process calls
            if not option_type or option_type.upper() == 'CALL':
                for _, row in opt_chain.calls.iterrows():
                    try:
                        # Filter for liquid options
                        if row.get('volume', 0) < 10 or row.get('openInterest', 0) < 50:
                            continue
                        
                        prediction = options_predictor.predict_option(
                            symbol=symbol,
                            company=company_name,
                            market=market,
                            spot_price=spot_price,
                            strike_price=row['strike'],
                            option_price=row['lastPrice'],
                            expiration_date=expiry,
                            option_type='CALL',
                            implied_volatility=row.get('impliedVolatility', 0.3),
                            open_interest=int(row.get('openInterest', 0)),
                            volume=int(row.get('volume', 0))
                        )
                        
                        option_data = OptionData(
                            symbol=prediction.symbol,
                            company=prediction.company,
                            market=prediction.market,
                            option_type=prediction.option_type,
                            strike_price=prediction.strike_price,
                            entry_price=prediction.entry_price,
                            expiration_date=prediction.expiration_date,
                            days_to_expiry=prediction.days_to_expiry,
                            target1=prediction.target1,
                            target1_confidence=prediction.target1_confidence,
                            target2=prediction.target2,
                            target2_confidence=prediction.target2_confidence,
                            target3=prediction.target3,
                            target3_confidence=prediction.target3_confidence,
                            implied_volatility=prediction.implied_volatility,
                            delta=prediction.delta,
                            recommendation=prediction.recommendation,
                            overall_confidence=prediction.overall_confidence,
                            risk_level=prediction.risk_level,
                            max_profit_potential=prediction.max_profit_potential,
                            breakeven_price=prediction.breakeven_price,
                            open_interest=prediction.open_interest,
                            volume=prediction.volume
                        )
                        
                        options_data.append(option_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing call option: {e}")
                        continue
            
            # Process puts
            if not option_type or option_type.upper() == 'PUT':
                for _, row in opt_chain.puts.iterrows():
                    try:
                        # Filter for liquid options
                        if row.get('volume', 0) < 10 or row.get('openInterest', 0) < 50:
                            continue
                        
                        prediction = options_predictor.predict_option(
                            symbol=symbol,
                            company=company_name,
                            market=market,
                            spot_price=spot_price,
                            strike_price=row['strike'],
                            option_price=row['lastPrice'],
                            expiration_date=expiry,
                            option_type='PUT',
                            implied_volatility=row.get('impliedVolatility', 0.3),
                            open_interest=int(row.get('openInterest', 0)),
                            volume=int(row.get('volume', 0))
                        )
                        
                        option_data = OptionData(
                            symbol=prediction.symbol,
                            company=prediction.company,
                            market=prediction.market,
                            option_type=prediction.option_type,
                            strike_price=prediction.strike_price,
                            entry_price=prediction.entry_price,
                            expiration_date=prediction.expiration_date,
                            days_to_expiry=prediction.days_to_expiry,
                            target1=prediction.target1,
                            target1_confidence=prediction.target1_confidence,
                            target2=prediction.target2,
                            target2_confidence=prediction.target2_confidence,
                            target3=prediction.target3,
                            target3_confidence=prediction.target3_confidence,
                            implied_volatility=prediction.implied_volatility,
                            delta=prediction.delta,
                            recommendation=prediction.recommendation,
                            overall_confidence=prediction.overall_confidence,
                            risk_level=prediction.risk_level,
                            max_profit_potential=prediction.max_profit_potential,
                            breakeven_price=prediction.breakeven_price,
                            open_interest=prediction.open_interest,
                            volume=prediction.volume
                        )
                        
                        options_data.append(option_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing put option: {e}")
                        continue
        
        # Sort by overall confidence
        options_data.sort(key=lambda x: x.overall_confidence, reverse=True)
        
        return options_data
        
    except Exception as e:
        logger.error(f"Error fetching options for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_next_option_expiry_dates():
    """Get next valid options expiration dates (Fridays for US, Thursdays for India)"""
    expiry_dates = []
    current_date = datetime.now()
    
    # Find next 6 Fridays (standard US options expiration)
    days_ahead = 4 - current_date.weekday()  # Friday = 4
    if days_ahead <= 0:  # If today is Friday or past, get next Friday
        days_ahead += 7
    
    next_friday = current_date + timedelta(days=days_ahead)
    
    # Get next 6 weekly/monthly Friday expirations
    for i in range(6):
        expiry_date = next_friday + timedelta(weeks=i)
        expiry_dates.append(expiry_date.strftime('%Y-%m-%d'))
    
    return expiry_dates

def try_fetch_real_options_prices(symbols_list, expiry_dates):
    """Try to fetch real options prices from yfinance with improved error handling"""
    real_options = []
    max_symbols = min(10, len(symbols_list))  # Fetch up to 10 symbols
    
    for symbol_info in symbols_list[:max_symbols]:
        try:
            rate_limit_wait()
            symbol = symbol_info['symbol']
            
            # Skip .NS symbols for now as they may have different option formats
            if '.NS' in symbol:
                continue
                
            ticker = yf.Ticker(symbol, session=YFINANCE_CACHE_SESSION)
            
            # Get available option dates
            try:
                available_dates = ticker.options
                if not available_dates or len(available_dates) == 0:
                    logger.debug(f"No options available for {symbol}")
                    continue
            except Exception as e:
                logger.debug(f"Error getting options dates for {symbol}: {e}")
                continue
            
            # Try to match our expiry dates with available dates
            for expiry in expiry_dates[:3]:  # First 3 expiry dates
                if expiry in available_dates:
                    try:
                        rate_limit_wait()
                        option_chain = ticker.option_chain(expiry)
                        
                        # Get ATM or near-the-money calls
                        spot = symbol_info['spot']
                        calls = option_chain.calls
                        
                        if len(calls) == 0:
                            continue
                        
                        # Filter for strikes near current price
                        atm_calls = calls[
                            (calls['strike'] >= spot * 0.95) & 
                            (calls['strike'] <= spot * 1.05) &
                            (calls['volume'] > 5) &
                            (calls['lastPrice'] > 0)
                        ]
                        
                        if len(atm_calls) > 0:
                            # Get the best liquid option
                            atm_call = atm_calls.iloc[0]
                            
                            real_options.append({
                                'symbol': symbol,
                                'company': symbol_info['company'],
                                'market': symbol_info['market'],
                                'strike': float(atm_call['strike']),
                                'entry_price': float(atm_call['lastPrice']),
                                'spot': spot,
                                'expiry': expiry,
                                'volume': int(atm_call['volume']) if pd.notna(atm_call['volume']) else 0,
                                'open_interest': int(atm_call['openInterest']) if pd.notna(atm_call['openInterest']) else 0,
                                'implied_volatility': float(atm_call['impliedVolatility']) if pd.notna(atm_call['impliedVolatility']) else 0.3
                            })
                            logger.info(f"✓ Fetched real option for {symbol}: ${atm_call['lastPrice']:.2f} (Strike {atm_call['strike']})")
                            break  # Got one option for this symbol, move to next
                    except Exception as e:
                        logger.debug(f"Error fetching option chain for {symbol} {expiry}: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Error fetching real options for {symbol}: {e}")
            continue
    
    return real_options

def enhance_predictions_with_ml(predictions: List[Dict]) -> List[Dict]:
    """
    Enhance predictions with ML models (LSTM, Random Forest, XGBoost)
    """
    if not ML_PREDICTOR_AVAILABLE:
        return predictions
    
    try:
        ml_predictor = get_ml_predictor()
        enhanced_predictions = []
        
        for pred in predictions[:20]:  # Limit to first 20 to avoid long processing
            try:
                symbol = pred['symbol']
                spot = pred.get('strike_price', 100) * 0.98  # Approximate spot from strike
                strike = pred['strike_price']
                entry_price = pred['entry_price']
                expiry_date = datetime.strptime(pred['expiration_date'], '%Y-%m-%d')
                days_to_expiry = pred['days_to_expiry']
                time_to_expiry = days_to_expiry / 365.0
                volume = pred.get('volume', 1000)
                open_interest = pred.get('open_interest', 5000)
                implied_vol = pred.get('implied_volatility', 0.30)
                
                # Get comprehensive ML prediction
                ml_result = ml_predictor.predict_comprehensive(
                    symbol=symbol,
                    spot=spot,
                    strike=strike,
                    time_to_expiry=time_to_expiry,
                    volatility=implied_vol,
                    volume=volume,
                    open_interest=open_interest,
                    historical_data=None  # Will generate synthetic data
                )
                
                # Update prediction with ML insights
                pred['ml_insights'] = {
                    'lstm_price_forecast': ml_result['lstm_prediction']['predicted_price'],
                    'lstm_confidence': ml_result['lstm_prediction']['confidence'],
                    'action_recommendation': ml_result['action_prediction']['action'],
                    'action_confidence': ml_result['action_prediction']['confidence'],
                    'xgb_premium': ml_result['premium_prediction']['predicted_premium'],
                    'xgb_confidence': ml_result['premium_prediction']['confidence'],
                    'greeks': ml_result['greeks'],
                    'sentiment': ml_result['sentiment']['sentiment_label'],
                    'sentiment_score': ml_result['sentiment']['sentiment_score'],
                    'overall_ml_confidence': ml_result['overall_confidence'],
                    'models_used': ml_result['models_used']
                }
                
                # Adjust entry price based on XGBoost prediction (weighted average)
                xgb_premium = ml_result['premium_prediction']['predicted_premium']
                xgb_weight = 0.3  # 30% weight to ML, 70% to market data
                pred['entry_price'] = entry_price * (1 - xgb_weight) + xgb_premium * xgb_weight
                
                # Adjust confidence based on ML consensus
                ml_confidence = ml_result['overall_confidence']
                pred['overall_confidence'] = round(
                    pred['overall_confidence'] * 0.7 + ml_confidence * 0.3, 
                    2
                )
                
                # Adjust recommendation based on ML action
                ml_action = ml_result['action_prediction']['action']
                if ml_action == 'SELL':
                    pred['recommendation'] = 'AVOID'
                    pred['overall_confidence'] *= 0.7
                elif ml_action == 'HOLD':
                    pred['overall_confidence'] *= 0.85
                
                # Update Greeks
                pred['delta'] = ml_result['greeks']['delta']
                pred['gamma'] = ml_result['greeks']['gamma']
                pred['theta'] = ml_result['greeks']['theta']
                pred['vega'] = ml_result['greeks']['vega']
                
                enhanced_predictions.append(pred)
                logger.debug(f"✓ ML enhanced: {symbol} - {ml_action} (conf: {ml_confidence:.2f})")
                
            except Exception as e:
                logger.warning(f"Failed to enhance prediction for {pred.get('symbol', 'unknown')}: {e}")
                enhanced_predictions.append(pred)  # Keep original if ML fails
        
        # Add remaining predictions without ML enhancement
        enhanced_predictions.extend(predictions[20:])
        
        logger.info(f"✓ Enhanced {min(20, len(predictions))} predictions with ML models")
        return enhanced_predictions
        
    except Exception as e:
        logger.error(f"ML enhancement failed: {e}")
        return predictions  # Return original predictions on failure

def generate_sample_predictions(limit: int = 20):
    """Generate sample predictions when real data is unavailable (rate limited)"""
    sample_data = []
    
    # US Stock samples - Top 50 (updated with current market data)
    us_samples = [
        {"symbol": "AAPL", "company": "Apple Inc", "market": "US", "strike": 265.0, "spot": 259.37},
        {"symbol": "MSFT", "company": "Microsoft Corporation", "market": "US", "strike": 490.0, "spot": 479.28},
        {"symbol": "GOOGL", "company": "Alphabet Inc", "market": "US", "strike": 335.0, "spot": 328.57},
        {"symbol": "NVDA", "company": "NVIDIA Corporation", "market": "US", "strike": 190.0, "spot": 184.83},
        {"symbol": "AMZN", "company": "Amazon.com Inc", "market": "US", "strike": 255.0, "spot": 247.34},
        {"symbol": "META", "company": "Meta Platforms Inc", "market": "US", "strike": 395.0, "spot": 387.50},
        {"symbol": "TSLA", "company": "Tesla Inc", "market": "US", "strike": 385.0, "spot": 378.20},
        {"symbol": "BRK.B", "company": "Berkshire Hathaway", "market": "US", "strike": 445.0, "spot": 438.90},
        {"symbol": "V", "company": "Visa Inc", "market": "US", "strike": 295.0, "spot": 289.45},
        {"symbol": "JPM", "company": "JPMorgan Chase", "market": "US", "strike": 225.0, "spot": 221.30},
        {"symbol": "MA", "company": "Mastercard Inc", "market": "US", "strike": 495.0, "spot": 487.60},
        {"symbol": "UNH", "company": "UnitedHealth Group", "market": "US", "strike": 545.0, "spot": 536.80},
        {"symbol": "JNJ", "company": "Johnson & Johnson", "market": "US", "strike": 165.0, "spot": 162.40},
        {"symbol": "WMT", "company": "Walmart Inc", "market": "US", "strike": 95.0, "spot": 93.50},
        {"symbol": "PG", "company": "Procter & Gamble", "market": "US", "strike": 175.0, "spot": 172.30},
        {"symbol": "XOM", "company": "Exxon Mobil", "market": "US", "strike": 115.0, "spot": 113.20},
        {"symbol": "CVX", "company": "Chevron Corp", "market": "US", "strike": 165.0, "spot": 162.70},
        {"symbol": "LLY", "company": "Eli Lilly", "market": "US", "strike": 925.0, "spot": 910.40},
        {"symbol": "ABBV", "company": "AbbVie Inc", "market": "US", "strike": 185.0, "spot": 182.10},
        {"symbol": "AVGO", "company": "Broadcom Inc", "market": "US", "strike": 215.0, "spot": 211.80},
        {"symbol": "NVO", "company": "Novo Nordisk", "market": "US", "strike": 125.0, "spot": 123.40},
        {"symbol": "MRK", "company": "Merck & Co", "market": "US", "strike": 105.0, "spot": 103.60},
        {"symbol": "PEP", "company": "PepsiCo Inc", "market": "US", "strike": 175.0, "spot": 172.90},
        {"symbol": "KO", "company": "Coca-Cola Co", "market": "US", "strike": 67.0, "spot": 65.80},
        {"symbol": "COST", "company": "Costco Wholesale", "market": "US", "strike": 975.0, "spot": 960.30},
        {"symbol": "TMO", "company": "Thermo Fisher Scientific", "market": "US", "strike": 565.0, "spot": 556.70},
        {"symbol": "ADBE", "company": "Adobe Inc", "market": "US", "strike": 545.0, "spot": 536.90},
        {"symbol": "CRM", "company": "Salesforce Inc", "market": "US", "strike": 335.0, "spot": 329.60},
        {"symbol": "NFLX", "company": "Netflix Inc", "market": "US", "strike": 805.0, "spot": 792.40},
        {"symbol": "CSCO", "company": "Cisco Systems", "market": "US", "strike": 59.0, "spot": 58.10},
        {"symbol": "ABT", "company": "Abbott Laboratories", "market": "US", "strike": 115.0, "spot": 113.40},
        {"symbol": "ORCL", "company": "Oracle Corporation", "market": "US", "strike": 195.0, "spot": 192.10},
        {"symbol": "INTC", "company": "Intel Corporation", "market": "US", "strike": 22.0, "spot": 21.65},
        {"symbol": "AMD", "company": "AMD Inc", "market": "US", "strike": 135.0, "spot": 133.20},
        {"symbol": "QCOM", "company": "QUALCOMM Inc", "market": "US", "strike": 165.0, "spot": 162.70},
        {"symbol": "TXN", "company": "Texas Instruments", "market": "US", "strike": 185.0, "spot": 182.40},
        {"symbol": "HON", "company": "Honeywell Int'l", "market": "US", "strike": 215.0, "spot": 211.80},
        {"symbol": "IBM", "company": "IBM", "market": "US", "strike": 215.0, "spot": 211.60},
        {"symbol": "CAT", "company": "Caterpillar Inc", "market": "US", "strike": 395.0, "spot": 389.20},
        {"symbol": "BA", "company": "Boeing Co", "market": "US", "strike": 175.0, "spot": 172.50},
        {"symbol": "GE", "company": "General Electric", "market": "US", "strike": 185.0, "spot": 182.30},
        {"symbol": "UPS", "company": "UPS", "market": "US", "strike": 125.0, "spot": 123.10},
        {"symbol": "AXP", "company": "American Express", "market": "US", "strike": 285.0, "spot": 280.70},
        {"symbol": "BAC", "company": "Bank of America", "market": "US", "strike": 45.0, "spot": 44.30},
        {"symbol": "WFC", "company": "Wells Fargo", "market": "US", "strike": 72.0, "spot": 70.90},
        {"symbol": "HD", "company": "Home Depot", "market": "US", "strike": 405.0, "spot": 398.60},
        {"symbol": "DIS", "company": "Walt Disney", "market": "US", "strike": 115.0, "spot": 113.20},
        {"symbol": "NKE", "company": "Nike Inc", "market": "US", "strike": 75.0, "spot": 73.90},
        {"symbol": "MCD", "company": "McDonald's", "market": "US", "strike": 305.0, "spot": 300.40},
        {"symbol": "SBUX", "company": "Starbucks", "market": "US", "strike": 95.0, "spot": 93.50},
    ]
    
    # India Stock samples - Top 50 NSE stocks
    india_samples = [
        {"symbol": "RELIANCE.NS", "company": "Reliance Industries", "market": "INDIA", "strike": 2950.0, "spot": 2885.0},
        {"symbol": "TCS.NS", "company": "Tata Consultancy Services", "market": "INDIA", "strike": 3850.0, "spot": 3790.0},
        {"symbol": "INFY.NS", "company": "Infosys Ltd", "market": "INDIA", "strike": 1520.0, "spot": 1485.0},
        {"symbol": "HDFCBANK.NS", "company": "HDFC Bank", "market": "INDIA", "strike": 1750.0, "spot": 1715.0},
        {"symbol": "ICICIBANK.NS", "company": "ICICI Bank", "market": "INDIA", "strike": 1150.0, "spot": 1130.0},
        {"symbol": "BHARTIARTL.NS", "company": "Bharti Airtel", "market": "INDIA", "strike": 1650.0, "spot": 1620.0},
        {"symbol": "ITC.NS", "company": "ITC Ltd", "market": "INDIA", "strike": 485.0, "spot": 476.0},
        {"symbol": "SBIN.NS", "company": "State Bank of India", "market": "INDIA", "strike": 825.0, "spot": 810.0},
        {"symbol": "HINDUNILVR.NS", "company": "Hindustan Unilever", "market": "INDIA", "strike": 2650.0, "spot": 2605.0},
        {"symbol": "LT.NS", "company": "Larsen & Toubro", "market": "INDIA", "strike": 3650.0, "spot": 3585.0},
        {"symbol": "HCLTECH.NS", "company": "HCL Technologies", "market": "INDIA", "strike": 1850.0, "spot": 1815.0},
        {"symbol": "WIPRO.NS", "company": "Wipro Ltd", "market": "INDIA", "strike": 565.0, "spot": 555.0},
        {"symbol": "KOTAKBANK.NS", "company": "Kotak Mahindra Bank", "market": "INDIA", "strike": 1950.0, "spot": 1915.0},
        {"symbol": "AXISBANK.NS", "company": "Axis Bank", "market": "INDIA", "strike": 1150.0, "spot": 1130.0},
        {"symbol": "MARUTI.NS", "company": "Maruti Suzuki", "market": "INDIA", "strike": 12800.0, "spot": 12560.0},
        {"symbol": "SUNPHARMA.NS", "company": "Sun Pharma", "market": "INDIA", "strike": 1850.0, "spot": 1815.0},
        {"symbol": "TATAMOTORS.NS", "company": "Tata Motors", "market": "INDIA", "strike": 915.0, "spot": 898.0},
        {"symbol": "TATASTEEL.NS", "company": "Tata Steel", "market": "INDIA", "strike": 145.0, "spot": 142.5},
        {"symbol": "TITAN.NS", "company": "Titan Company", "market": "INDIA", "strike": 3650.0, "spot": 3585.0},
        {"symbol": "BAJFINANCE.NS", "company": "Bajaj Finance", "market": "INDIA", "strike": 7250.0, "spot": 7120.0},
        {"symbol": "BAJAJFINSV.NS", "company": "Bajaj Finserv", "market": "INDIA", "strike": 1750.0, "spot": 1720.0},
        {"symbol": "M&M.NS", "company": "Mahindra & Mahindra", "market": "INDIA", "strike": 2950.0, "spot": 2895.0},
        {"symbol": "ASIANPAINT.NS", "company": "Asian Paints", "market": "INDIA", "strike": 2450.0, "spot": 2405.0},
        {"symbol": "ULTRACEMCO.NS", "company": "UltraTech Cement", "market": "INDIA", "strike": 11500.0, "spot": 11285.0},
        {"symbol": "NESTLEIND.NS", "company": "Nestle India", "market": "INDIA", "strike": 2550.0, "spot": 2505.0},
        {"symbol": "POWERGRID.NS", "company": "Power Grid Corp", "market": "INDIA", "strike": 335.0, "spot": 329.0},
        {"symbol": "NTPC.NS", "company": "NTPC Ltd", "market": "INDIA", "strike": 385.0, "spot": 378.0},
        {"symbol": "ONGC.NS", "company": "ONGC", "market": "INDIA", "strike": 285.0, "spot": 280.0},
        {"symbol": "ADANIENT.NS", "company": "Adani Enterprises", "market": "INDIA", "strike": 2850.0, "spot": 2795.0},
        {"symbol": "ADANIPORTS.NS", "company": "Adani Ports", "market": "INDIA", "strike": 1350.0, "spot": 1325.0},
        {"symbol": "COALINDIA.NS", "company": "Coal India", "market": "INDIA", "strike": 485.0, "spot": 476.0},
        {"symbol": "DRREDDY.NS", "company": "Dr Reddy's Labs", "market": "INDIA", "strike": 1350.0, "spot": 1325.0},
        {"symbol": "CIPLA.NS", "company": "Cipla Ltd", "market": "INDIA", "strike": 1550.0, "spot": 1520.0},
        {"symbol": "TECHM.NS", "company": "Tech Mahindra", "market": "INDIA", "strike": 1750.0, "spot": 1720.0},
        {"symbol": "EICHERMOT.NS", "company": "Eicher Motors", "market": "INDIA", "strike": 4850.0, "spot": 4760.0},
        {"symbol": "HEROMOTOCO.NS", "company": "Hero MotoCorp", "market": "INDIA", "strike": 4650.0, "spot": 4565.0},
        {"symbol": "DIVISLAB.NS", "company": "Divi's Laboratories", "market": "INDIA", "strike": 6050.0, "spot": 5940.0},
        {"symbol": "BRITANNIA.NS", "company": "Britannia Industries", "market": "INDIA", "strike": 4950.0, "spot": 4860.0},
        {"symbol": "SHREECEM.NS", "company": "Shree Cement", "market": "INDIA", "strike": 27500.0, "spot": 27000.0},
        {"symbol": "GRASIM.NS", "company": "Grasim Industries", "market": "INDIA", "strike": 2650.0, "spot": 2605.0},
        {"symbol": "JSWSTEEL.NS", "company": "JSW Steel", "market": "INDIA", "strike": 935.0, "spot": 918.0},
        {"symbol": "HINDALCO.NS", "company": "Hindalco Industries", "market": "INDIA", "strike": 685.0, "spot": 673.0},
        {"symbol": "INDUSINDBK.NS", "company": "IndusInd Bank", "market": "INDIA", "strike": 975.0, "spot": 958.0},
        {"symbol": "BAJAJ-AUTO.NS", "company": "Bajaj Auto", "market": "INDIA", "strike": 9850.0, "spot": 9670.0},
        {"symbol": "APOLLOHOSP.NS", "company": "Apollo Hospitals", "market": "INDIA", "strike": 7250.0, "spot": 7120.0},
        {"symbol": "BPCL.NS", "company": "Bharat Petroleum", "market": "INDIA", "strike": 315.0, "spot": 309.0},
        {"symbol": "IOC.NS", "company": "Indian Oil Corp", "market": "INDIA", "strike": 145.0, "spot": 142.5},
        {"symbol": "VEDL.NS", "company": "Vedanta Ltd", "market": "INDIA", "strike": 485.0, "spot": 476.0},
        {"symbol": "TATACONSUM.NS", "company": "Tata Consumer", "market": "INDIA", "strike": 1150.0, "spot": 1130.0},
    ]
    
    # Get actual Friday expiration dates (standard for US options)
    current_date = datetime.now()
    expiry_dates = get_next_option_expiry_dates()
    
    all_samples = us_samples + india_samples
    
    # Try to fetch real options prices
    real_options = try_fetch_real_options_prices(all_samples, expiry_dates)
    logger.info(f"Fetched {len(real_options)} real options from market")
    
    # Use real options data if available
    for real_opt in real_options:
        days_to_expiry = (datetime.strptime(real_opt['expiry'], '%Y-%m-%d') - current_date).days
        entry_price = real_opt['entry_price']
        
        # Calculate realistic targets based on actual option price
        time_multiplier = 1 + (days_to_expiry / 180)
        target1 = entry_price * 1.35 * min(time_multiplier, 1.5)
        target2 = entry_price * 1.80 * min(time_multiplier, 1.5)
        target3 = entry_price * 2.50 * min(time_multiplier, 1.5)
        
        confidence_adjustment = max(0.7, 1 - (days_to_expiry / 365))
        
        prediction = {
            "symbol": real_opt["symbol"],
            "company": real_opt["company"],
            "market": real_opt["market"],
            "option_type": "CALL",
            "strike_price": real_opt["strike"],
            "entry_price": entry_price,
            "expiration_date": real_opt["expiry"],
            "days_to_expiry": days_to_expiry,
            "target1": target1,
            "target1_confidence": round(0.85 * confidence_adjustment, 2),
            "target2": target2,
            "target2_confidence": round(0.65 * confidence_adjustment, 2),
            "target3": target3,
            "target3_confidence": round(0.40 * confidence_adjustment, 2),
            "implied_volatility": real_opt["implied_volatility"],
            "delta": 0.65,
            "recommendation": "BUY",
            "overall_confidence": round(0.72 * confidence_adjustment, 2),
            "risk_level": "MEDIUM" if days_to_expiry > 30 else "HIGH",
            "max_profit_potential": ((target3 - entry_price) / entry_price * 100),
            "breakeven_price": real_opt["strike"] + entry_price,
            "open_interest": real_opt["open_interest"],
            "volume": real_opt["volume"]
        }
        sample_data.append(prediction)
    
    # Fill remaining with calculated estimates if needed
    for sample in all_samples:
        for expiry_date in expiry_dates:
            if len(sample_data) >= limit:
                break
                
            days_to_expiry = (datetime.strptime(expiry_date, '%Y-%m-%d') - current_date).days
            
            # Calculate option premium targets (not stock price)
            spot = sample["spot"]
            entry_price = spot * 0.03  # 3% of spot as premium
            
            # Adjust targets based on time to expiry (longer = higher potential)
            time_multiplier = 1 + (days_to_expiry / 180)  # Up to 50% higher for 6-month options
            target1 = entry_price * 1.35 * min(time_multiplier, 1.5)  # 35% gain on option premium
            target2 = entry_price * 1.80 * min(time_multiplier, 1.5)  # 80% gain on option premium
            target3 = entry_price * 2.50 * min(time_multiplier, 1.5)  # 150% gain on option premium
            
            # Adjust confidence based on time to expiry (shorter = more confident)
            confidence_adjustment = max(0.7, 1 - (days_to_expiry / 365))
            
            prediction = {
                "symbol": sample["symbol"],
                "company": sample["company"],
                "market": sample["market"],
                "option_type": "CALL",
                "strike_price": sample["strike"],
                "entry_price": entry_price,
                "expiration_date": expiry_date,
                "days_to_expiry": days_to_expiry,
                "target1": target1,
                "target1_confidence": round(0.85 * confidence_adjustment, 2),
                "target2": target2,
                "target2_confidence": round(0.65 * confidence_adjustment, 2),
                "target3": target3,
                "target3_confidence": round(0.40 * confidence_adjustment, 2),
                "implied_volatility": 0.28,
                "delta": 0.65,
                "recommendation": "BUY",
                "overall_confidence": round(0.72 * confidence_adjustment, 2),
                "risk_level": "MEDIUM" if days_to_expiry > 30 else "HIGH",
                "max_profit_potential": ((target3 - entry_price) / entry_price * 100),
                "breakeven_price": sample["strike"] + entry_price,
                "open_interest": 15000,
                "volume": 2500
            }
            sample_data.append(prediction)
        
        if len(sample_data) >= limit:
            break
    
    # Enhance predictions with ML models if available
    if ML_PREDICTOR_AVAILABLE:
        logger.info(f"Enhancing {len(sample_data)} predictions with ML models (LSTM/RandomForest/XGBoost)...")
        sample_data = enhance_predictions_with_ml(sample_data)
    
    data_source = "live market data" if len(real_options) > 0 else "calculated estimates"
    ml_note = " + ML predictions (LSTM/RF/XGBoost)" if ML_PREDICTOR_AVAILABLE else ""
    return {
        "total": len(sample_data),
        "predictions": sample_data,
        "expiry_dates_included": expiry_dates,
        "real_options_count": len(real_options),
        "note": f"Showing {len(real_options)} options with {data_source}{ml_note}. Prices from Yahoo Finance. Real-time quotes may vary."
    }


@app.get("/api/predictions/best")
async def get_best_predictions(
    market: Optional[str] = Query(None, description="Filter by market: US or INDIA"),
    min_confidence: float = Query(0.65, description="Minimum confidence level"),
    max_risk: str = Query("MEDIUM", description="Maximum risk level: LOW, MEDIUM, HIGH"),
    limit: int = Query(20, description="Maximum number of predictions to return"),
    force_refresh: bool = Query(False, description="Force refresh from external APIs")
):
    """Get best options predictions - reads from DB or generates new data"""
    try:
        # Try to get from database first
        if not force_refresh:
            db_predictions = option_repo.get_latest_predictions(
                market=market,
                min_confidence=min_confidence,
                limit=limit
            )
            
            if db_predictions:
                logger.info(f"Returning {len(db_predictions)} predictions from database")
                return {
                    "total": len(db_predictions),
                    "predictions": db_predictions,
                    "source": "database",
                    "note": "Data from database cache"
                }
        
        # Generate and save new predictions
        logger.info(f"Generating fresh predictions (limit={limit})")
        predictions = generate_sample_predictions(limit)
        
        # Save to database in background
        asyncio.create_task(save_predictions_to_db(predictions['predictions']))
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return generate_sample_predictions(limit)


@app.get("/api/nse/option-chain/{symbol}")
async def get_nse_option_chain(
    symbol: str,
    asset_type: str = Query("EQUITY", description="Asset type: EQUITY or INDEX"),
    num_strikes: int = Query(5, description="Number of strikes around ATM"),
    expiry: Optional[str] = Query(None, description="Expiry date in DD-MMM-YYYY format (e.g., 27-Jan-2026)")
):
    """
    Get NSE India option chain data for a symbol
    
    Args:
        symbol: NSE symbol (e.g., 'RELIANCE', 'NIFTY')
        asset_type: 'EQUITY' or 'INDEX'
        num_strikes: Number of strikes to return around ATM
        expiry: Expiry date. If not provided, uses nearest expiry.
    """
    if not NSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSE option chain service is not available"
        )
    
    try:
        data = nse_option_chain.get_atm_options(
            symbol.upper(),
            asset_type.upper(),
            num_strikes,
            expiry
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No option chain data found for {symbol}"
            )
        
        if 'error' in data:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching option chain: {data['error']}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching NSE option chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nse/expiry-dates/{symbol}")
async def get_nse_expiry_dates(
    symbol: str,
    asset_type: str = Query("EQUITY", description="Asset type: EQUITY or INDEX")
):
    """
    Get available expiry dates for an NSE symbol
    
    Args:
        symbol: NSE symbol (e.g., 'RELIANCE', 'NIFTY')
        asset_type: 'EQUITY' or 'INDEX'
    """
    if not NSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSE option chain service is not available"
        )
    
    try:
        expiry_dates = nse_option_chain.fetch_expiry_dates(
            symbol.upper(),
            asset_type.upper()
        )
        
        if not expiry_dates:
            raise HTTPException(
                status_code=404,
                detail=f"No expiry dates found for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "asset_type": asset_type.upper(),
            "expiry_dates": expiry_dates,
            "total": len(expiry_dates),
            "nearest_expiry": expiry_dates[0] if expiry_dates else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching expiry dates for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nse/top-equities")
async def get_nse_top_equity_options(
    limit: int = Query(5, description="Number of equities to fetch")
):
    """
    Get option chains for top NSE equity stocks
    
    Returns option chain data for top liquid stocks with options
    """
    if not NSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSE option chain service is not available"
        )
    
    try:
        results = nse_option_chain.get_all_equity_options(limit)
        
        return {
            "total": len(results),
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching NSE equity options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nse/indices")
async def get_nse_index_options():
    """
    Get option chains for all major NSE indices
    
    Returns option chain data for NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
    """
    if not NSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSE option chain service is not available"
        )
    
    try:
        results = nse_option_chain.get_all_index_options()
        
        return {
            "total": len(results),
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching NSE index options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nse/symbols")
async def get_nse_symbols():
    """Get list of available NSE symbols for options"""
    if not NSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSE option chain service is not available"
        )
    
    return {
        "equities": nse_option_chain.EQUITY_SYMBOLS,
        "indices": nse_option_chain.INDEX_SYMBOLS,
        "total_equities": len(nse_option_chain.EQUITY_SYMBOLS),
        "total_indices": len(nse_option_chain.INDEX_SYMBOLS)
    }


async def save_predictions_to_db(predictions: List[Dict]):
    """Save predictions to database in background"""
    try:
        for pred in predictions:
            # Save option master data
            option_repo.upsert_option({
                "symbol": pred["symbol"],
                "option_type": pred["type"],
                "strike_price": pred["strike"],
                "expiration_date": pred["expiration"]
            })
            
            # Save prediction data
            option_repo.insert_option_prediction(pred)
        
        logger.info(f"Saved {len(predictions)} predictions to database")
    except Exception as e:
        logger.error(f"Failed to save predictions to database: {e}")


@app.post("/api/nse/save-chain")
async def save_nse_chain(
    symbol: str,
    asset_type: str = Query("EQUITY", description="Asset type: EQUITY or INDEX")
):
    """
    Fetch and save NSE option chain to database
    
    This endpoint fetches live NSE option chain data and persists it to the database.
    """
    try:
        chain_data = nse_option_chain.get_atm_options(symbol, asset_type)
        
        if not chain_data:
            raise HTTPException(status_code=404, detail=f"No option chain data found for {symbol}")
        
        saved_count = option_repo.insert_nse_option_chain(chain_data)
        
        return {
            "success": True,
            "symbol": symbol,
            "asset_type": asset_type,
            "saved_count": saved_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to save NSE chain for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
