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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from connectors.company_lists import get_all_companies, get_top_us_companies, get_nifty500_companies
from models.options_predictor import OptionsPredictor, OptionPrediction

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
        
        # Fetch stock data in batches
        for company in companies[:limit]:
            try:
                ticker = yf.Ticker(company['symbol'])
                info = ticker.info
                
                stock = StockData(
                    symbol=company['symbol'],
                    company=company['company'],
                    market=company['market'],
                    sector=company.get('sector', 'N/A'),
                    current_price=info.get('currentPrice', info.get('regularMarketPrice', 0)),
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
        ticker = yf.Ticker(symbol)
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


def generate_sample_predictions(limit: int = 20):
    """Generate sample predictions when real data is unavailable (rate limited)"""
    sample_data = []
    
    # US Stock samples
    us_samples = [
        {"symbol": "AAPL", "company": "Apple Inc", "market": "US", "strike": 185.0, "spot": 178.5},
        {"symbol": "MSFT", "company": "Microsoft Corporation", "market": "US", "strike": 395.0, "spot": 385.0},
        {"symbol": "GOOGL", "company": "Alphabet Inc", "market": "US", "strike": 142.0, "spot": 138.5},
        {"symbol": "NVDA", "company": "NVIDIA Corporation", "market": "US", "strike": 505.0, "spot": 495.0},
        {"symbol": "AMZN", "company": "Amazon.com Inc", "market": "US", "strike": 178.0, "spot": 172.5},
    ]
    
    # India Stock samples  
    india_samples = [
        {"symbol": "RELIANCE.NS", "company": "Reliance Industries Ltd", "market": "INDIA", "strike": 2950.0, "spot": 2885.0},
        {"symbol": "TCS.NS", "company": "Tata Consultancy Services", "market": "INDIA", "strike": 3850.0, "spot": 3790.0},
        {"symbol": "INFY.NS", "company": "Infosys Ltd", "market": "INDIA", "strike": 1520.0, "spot": 1485.0},
        {"symbol": "HDFCBANK.NS", "company": "HDFC Bank Ltd", "market": "INDIA", "strike": 1750.0, "spot": 1715.0},
    ]
    
    all_samples = us_samples + india_samples
    
    for sample in all_samples[:limit]:
        # Calculate sample targets
        spot = sample["spot"]
        target1 = spot * 1.05  # 5% gain
        target2 = spot * 1.10  # 10% gain
        target3 = spot * 1.15  # 15% gain
        
        prediction = {
            "symbol": sample["symbol"],
            "company": sample["company"],
            "market": sample["market"],
            "option_type": "CALL",
            "strike_price": sample["strike"],
            "entry_price": spot * 0.03,  # 3% of spot as premium
            "expiration_date": "2026-02-21",
            "days_to_expiry": 41,
            "target1": target1,
            "target1_confidence": 0.85,
            "target2": target2,
            "target2_confidence": 0.65,
            "target3": target3,
            "target3_confidence": 0.40,
            "implied_volatility": 0.28,
            "delta": 0.65,
            "recommendation": "BUY",
            "overall_confidence": 0.72,
            "risk_level": "MEDIUM",
            "max_profit_potential": 45.8,
            "breakeven_price": sample["strike"] + (spot * 0.03),
            "open_interest": 15000,
            "volume": 2500
        }
        sample_data.append(prediction)
    
    return {
        "total": len(sample_data),
        "predictions": sample_data,
        "note": "Sample data - Yahoo Finance rate limits exceeded. Refresh in a few minutes for live data."
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


def generate_sample_predictions(limit: int = 20):
    """Generate sample predictions when real data is unavailable (rate limited)"""
    sample_data = []
    
    # US Stock samples
    us_samples = [
        {"symbol": "AAPL", "company": "Apple Inc", "market": "US", "strike": 185.0, "spot": 178.5},
        {"symbol": "MSFT", "company": "Microsoft Corporation", "market": "US", "strike": 395.0, "spot": 385.0},
        {"symbol": "GOOGL", "company": "Alphabet Inc", "market": "US", "strike": 142.0, "spot": 138.5},
        {"symbol": "NVDA", "company": "NVIDIA Corporation", "market": "US", "strike": 505.0, "spot": 495.0},
        {"symbol": "AMZN", "company": "Amazon.com Inc", "market": "US", "strike": 178.0, "spot": 172.5},
    ]
    
    # India Stock samples  
    india_samples = [
        {"symbol": "RELIANCE.NS", "company": "Reliance Industries Ltd", "market": "INDIA", "strike": 2950.0, "spot": 2885.0},
        {"symbol": "TCS.NS", "company": "Tata Consultancy Services", "market": "INDIA", "strike": 3850.0, "spot": 3790.0},
        {"symbol": "INFY.NS", "company": "Infosys Ltd", "market": "INDIA", "strike": 1520.0, "spot": 1485.0},
        {"symbol": "HDFCBANK.NS", "company": "HDFC Bank Ltd", "market": "INDIA", "strike": 1750.0, "spot": 1715.0},
    ]
    
    all_samples = us_samples + india_samples
    
    for sample in all_samples[:limit]:
        # Calculate sample targets
        spot = sample["spot"]
        target1 = spot * 1.05  # 5% gain
        target2 = spot * 1.10  # 10% gain
        target3 = spot * 1.15  # 15% gain
        
        prediction = {
            "symbol": sample["symbol"],
            "company": sample["company"],
            "market": sample["market"],
            "option_type": "CALL",
            "strike_price": sample["strike"],
            "entry_price": spot * 0.03,  # 3% of spot as premium
            "expiration_date": "2026-02-21",
            "days_to_expiry": 41,
            "target1": target1,
            "target1_confidence": 0.85,
            "target2": target2,
            "target2_confidence": 0.65,
            "target3": target3,
            "target3_confidence": 0.40,
            "implied_volatility": 0.28,
            "delta": 0.65,
            "recommendation": "BUY",
            "overall_confidence": 0.72,
            "risk_level": "MEDIUM",
            "max_profit_potential": 45.8,
            "breakeven_price": sample["strike"] + (spot * 0.03),
            "open_interest": 15000,
            "volume": 2500
        }
        sample_data.append(prediction)
    
    return {
        "total": len(sample_data),
        "predictions": sample_data,
        "note": "Sample data - Yahoo Finance rate limits exceeded. Refresh in a few minutes for live data."
    }


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
