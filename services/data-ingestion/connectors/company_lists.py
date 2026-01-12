"""
Company lists for top 500 companies in USA and India
"""

import requests
import pandas as pd
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def get_sp500_companies() -> List[Dict]:
    """Get S&P 500 company list from Wikipedia"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # Add headers to avoid 403
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        tables = pd.read_html(req)
        df = tables[0]
        
        companies = []
        for _, row in df.iterrows():
            companies.append({
                'symbol': row['Symbol'].replace('.', '-'),  # Fix for Yahoo Finance
                'company': row['Security'],
                'sector': row['GICS Sector'],
                'industry': row['GICS Sub-Industry'],
                'market': 'US',
                'index': 'S&P500'
            })
        
        logger.info(f"Loaded {len(companies)} S&P 500 companies")
        return companies
    except Exception as e:
        logger.error(f"Error loading S&P 500: {e}")
        return get_fallback_us_companies()


def get_nasdaq100_companies() -> List[Dict]:
    """Get NASDAQ 100 company list"""
    try:
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        tables = pd.read_html(url)
        df = tables[4]  # The main table
        
        companies = []
        for _, row in df.iterrows():
            companies.append({
                'symbol': row['Ticker'],
                'company': row['Company'],
                'sector': row.get('GICS Sector', 'Technology'),
                'industry': row.get('GICS Sub-Industry', ''),
                'market': 'US',
                'index': 'NASDAQ100'
            })
        
        logger.info(f"Loaded {len(companies)} NASDAQ 100 companies")
        return companies
    except Exception as e:
        logger.error(f"Error loading NASDAQ 100: {e}")
        return []


def get_russell1000_companies() -> List[Dict]:
    """Get Russell 1000 companies (fallback list)"""
    # Since Russell 1000 isn't easily accessible, we'll use a curated list
    # of major US companies not in S&P 500
    companies = [
        {'symbol': 'TSLA', 'company': 'Tesla Inc', 'sector': 'Consumer Discretionary', 'industry': 'Automobiles'},
        {'symbol': 'BRK.B', 'company': 'Berkshire Hathaway', 'sector': 'Financials', 'industry': 'Insurance'},
        {'symbol': 'V', 'company': 'Visa Inc', 'sector': 'Financials', 'industry': 'Payments'},
        {'symbol': 'MA', 'company': 'Mastercard', 'sector': 'Financials', 'industry': 'Payments'},
        {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
        # Add more companies as needed
    ]
    
    for company in companies:
        company['market'] = 'US'
        company['index'] = 'RUSSELL1000'
    
    return companies


def get_fallback_us_companies() -> List[Dict]:
    """Comprehensive fallback list of major US companies"""
    companies_list = [
        # Tech Giants
        {'symbol': 'AAPL', 'company': 'Apple Inc', 'sector': 'Technology', 'industry': 'Consumer Electronics'},
        {'symbol': 'MSFT', 'company': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Software'},
        {'symbol': 'GOOGL', 'company': 'Alphabet Inc Class A', 'sector': 'Technology', 'industry': 'Internet'},
        {'symbol': 'GOOG', 'company': 'Alphabet Inc Class C', 'sector': 'Technology', 'industry': 'Internet'},
        {'symbol': 'AMZN', 'company': 'Amazon.com Inc', 'sector': 'Consumer Discretionary', 'industry': 'E-commerce'},
        {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'META', 'company': 'Meta Platforms Inc', 'sector': 'Technology', 'industry': 'Social Media'},
        {'symbol': 'TSLA', 'company': 'Tesla Inc', 'sector': 'Consumer Discretionary', 'industry': 'Automobiles'},
        {'symbol': 'AVGO', 'company': 'Broadcom Inc', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'ORCL', 'company': 'Oracle Corporation', 'sector': 'Technology', 'industry': 'Software'},
        {'symbol': 'ADBE', 'company': 'Adobe Inc', 'sector': 'Technology', 'industry': 'Software'},
        {'symbol': 'CRM', 'company': 'Salesforce Inc', 'sector': 'Technology', 'industry': 'Software'},
        {'symbol': 'NFLX', 'company': 'Netflix Inc', 'sector': 'Communication Services', 'industry': 'Streaming'},
        {'symbol': 'CSCO', 'company': 'Cisco Systems Inc', 'sector': 'Technology', 'industry': 'Networking'},
        {'symbol': 'INTC', 'company': 'Intel Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'AMD', 'company': 'Advanced Micro Devices Inc', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'QCOM', 'company': 'QUALCOMM Inc', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'TXN', 'company': 'Texas Instruments Inc', 'sector': 'Technology', 'industry': 'Semiconductors'},
        {'symbol': 'IBM', 'company': 'International Business Machines', 'sector': 'Technology', 'industry': 'IT Services'},
        {'symbol': 'NOW', 'company': 'ServiceNow Inc', 'sector': 'Technology', 'industry': 'Software'},
        
        # Financials
        {'symbol': 'JPM', 'company': 'JPMorgan Chase & Co', 'sector': 'Financials', 'industry': 'Banking'},
        {'symbol': 'V', 'company': 'Visa Inc', 'sector': 'Financials', 'industry': 'Payments'},
        {'symbol': 'MA', 'company': 'Mastercard Inc', 'sector': 'Financials', 'industry': 'Payments'},
        {'symbol': 'BAC', 'company': 'Bank of America Corp', 'sector': 'Financials', 'industry': 'Banking'},
        {'symbol': 'WFC', 'company': 'Wells Fargo & Co', 'sector': 'Financials', 'industry': 'Banking'},
        {'symbol': 'GS', 'company': 'Goldman Sachs Group Inc', 'sector': 'Financials', 'industry': 'Investment Banking'},
        {'symbol': 'MS', 'company': 'Morgan Stanley', 'sector': 'Financials', 'industry': 'Investment Banking'},
        {'symbol': 'BLK', 'company': 'BlackRock Inc', 'sector': 'Financials', 'industry': 'Asset Management'},
        {'symbol': 'C', 'company': 'Citigroup Inc', 'sector': 'Financials', 'industry': 'Banking'},
        {'symbol': 'BRK.B', 'company': 'Berkshire Hathaway Inc', 'sector': 'Financials', 'industry': 'Insurance'},
        {'symbol': 'AXP', 'company': 'American Express Co', 'sector': 'Financials', 'industry': 'Credit Services'},
        {'symbol': 'SCHW', 'company': 'Charles Schwab Corp', 'sector': 'Financials', 'industry': 'Brokerage'},
        {'symbol': 'USB', 'company': 'U.S. Bancorp', 'sector': 'Financials', 'industry': 'Banking'},
        {'symbol': 'PNC', 'company': 'PNC Financial Services', 'sector': 'Financials', 'industry': 'Banking'},
        
        # Healthcare
        {'symbol': 'UNH', 'company': 'UnitedHealth Group Inc', 'sector': 'Healthcare', 'industry': 'Health Insurance'},
        {'symbol': 'JNJ', 'company': 'Johnson & Johnson', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
        {'symbol': 'LLY', 'company': 'Eli Lilly and Co', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
        {'symbol': 'ABBV', 'company': 'AbbVie Inc', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
        {'symbol': 'MRK', 'company': 'Merck & Co Inc', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
        {'symbol': 'PFE', 'company': 'Pfizer Inc', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
        {'symbol': 'TMO', 'company': 'Thermo Fisher Scientific', 'sector': 'Healthcare', 'industry': 'Life Sciences'},
        {'symbol': 'ABT', 'company': 'Abbott Laboratories', 'sector': 'Healthcare', 'industry': 'Medical Devices'},
        {'symbol': 'DHR', 'company': 'Danaher Corporation', 'sector': 'Healthcare', 'industry': 'Medical Equipment'},
        {'symbol': 'CVS', 'company': 'CVS Health Corporation', 'sector': 'Healthcare', 'industry': 'Pharmacy'},
        
        # Consumer
        {'symbol': 'WMT', 'company': 'Walmart Inc', 'sector': 'Consumer Staples', 'industry': 'Retail'},
        {'symbol': 'PG', 'company': 'Procter & Gamble Co', 'sector': 'Consumer Staples', 'industry': 'Personal Products'},
        {'symbol': 'KO', 'company': 'Coca-Cola Co', 'sector': 'Consumer Staples', 'industry': 'Beverages'},
        {'symbol': 'PEP', 'company': 'PepsiCo Inc', 'sector': 'Consumer Staples', 'industry': 'Beverages'},
        {'symbol': 'COST', 'company': 'Costco Wholesale Corp', 'sector': 'Consumer Staples', 'industry': 'Retail'},
        {'symbol': 'HD', 'company': 'Home Depot Inc', 'sector': 'Consumer Discretionary', 'industry': 'Home Improvement'},
        {'symbol': 'MCD', 'company': 'McDonald\'s Corp', 'sector': 'Consumer Discretionary', 'industry': 'Restaurants'},
        {'symbol': 'DIS', 'company': 'Walt Disney Co', 'sector': 'Communication Services', 'industry': 'Entertainment'},
        {'symbol': 'NKE', 'company': 'Nike Inc', 'sector': 'Consumer Discretionary', 'industry': 'Apparel'},
        {'symbol': 'SBUX', 'company': 'Starbucks Corp', 'sector': 'Consumer Discretionary', 'industry': 'Restaurants'},
        
        # Energy
        {'symbol': 'XOM', 'company': 'Exxon Mobil Corp', 'sector': 'Energy', 'industry': 'Oil & Gas'},
        {'symbol': 'CVX', 'company': 'Chevron Corp', 'sector': 'Energy', 'industry': 'Oil & Gas'},
        {'symbol': 'COP', 'company': 'ConocoPhillips', 'sector': 'Energy', 'industry': 'Oil & Gas'},
        {'symbol': 'SLB', 'company': 'Schlumberger NV', 'sector': 'Energy', 'industry': 'Oil Services'},
        
        # Industrial
        {'symbol': 'CAT', 'company': 'Caterpillar Inc', 'sector': 'Industrials', 'industry': 'Machinery'},
        {'symbol': 'BA', 'company': 'Boeing Co', 'sector': 'Industrials', 'industry': 'Aerospace'},
        {'symbol': 'GE', 'company': 'General Electric Co', 'sector': 'Industrials', 'industry': 'Conglomerate'},
        {'symbol': 'HON', 'company': 'Honeywell International', 'sector': 'Industrials', 'industry': 'Conglomerate'},
        {'symbol': 'UPS', 'company': 'United Parcel Service', 'sector': 'Industrials', 'industry': 'Logistics'},
        
        # Communication Services
        {'symbol': 'GOOGL', 'company': 'Alphabet Inc', 'sector': 'Communication Services', 'industry': 'Internet'},
        {'symbol': 'META', 'company': 'Meta Platforms', 'sector': 'Communication Services', 'industry': 'Social Media'},
        {'symbol': 'T', 'company': 'AT&T Inc', 'sector': 'Communication Services', 'industry': 'Telecom'},
        {'symbol': 'VZ', 'company': 'Verizon Communications', 'sector': 'Communication Services', 'industry': 'Telecom'},
        
        # Utilities
        {'symbol': 'NEE', 'company': 'NextEra Energy Inc', 'sector': 'Utilities', 'industry': 'Electric Utilities'},
        {'symbol': 'DUK', 'company': 'Duke Energy Corp', 'sector': 'Utilities', 'industry': 'Electric Utilities'},
        
        # Real Estate
        {'symbol': 'AMT', 'company': 'American Tower Corp', 'sector': 'Real Estate', 'industry': 'REITs'},
        {'symbol': 'PLD', 'company': 'Prologis Inc', 'sector': 'Real Estate', 'industry': 'REITs'},
        
        # Materials
        {'symbol': 'LIN', 'company': 'Linde PLC', 'sector': 'Materials', 'industry': 'Chemicals'},
        {'symbol': 'APD', 'company': 'Air Products and Chemicals', 'sector': 'Materials', 'industry': 'Chemicals'},
        
        # ETFs and Indices
        {'symbol': 'SPY', 'company': 'SPDR S&P 500 ETF', 'sector': 'ETF', 'industry': 'Index Fund'},
        {'symbol': 'QQQ', 'company': 'Invesco QQQ Trust', 'sector': 'ETF', 'industry': 'Index Fund'},
        {'symbol': 'IWM', 'company': 'iShares Russell 2000 ETF', 'sector': 'ETF', 'industry': 'Index Fund'},
        {'symbol': 'DIA', 'company': 'SPDR Dow Jones Industrial Average ETF', 'sector': 'ETF', 'industry': 'Index Fund'},
        {'symbol': 'VTI', 'company': 'Vanguard Total Stock Market ETF', 'sector': 'ETF', 'industry': 'Index Fund'},
    ]
    
    for company in companies_list:
        company['market'] = 'US'
        company['index'] = 'TOP_US'
    
    logger.info(f"Using fallback list with {len(companies_list)} US companies")
    return companies_list


def get_top_us_companies() -> List[Dict]:
    """Get top 500+ US companies combining multiple indices"""
    companies = []
    
    # Get S&P 500
    sp500 = get_sp500_companies()
    companies.extend(sp500)
    
    # Get NASDAQ 100 (may have overlap with S&P 500)
    nasdaq100 = get_nasdaq100_companies()
    
    # Remove duplicates
    existing_symbols = {c['symbol'] for c in companies}
    for company in nasdaq100:
        if company['symbol'] not in existing_symbols:
            companies.append(company)
            existing_symbols.add(company['symbol'])
    
    # Add Russell 1000 companies
    russell = get_russell1000_companies()
    for company in russell:
        if company['symbol'] not in existing_symbols:
            companies.append(company)
            existing_symbols.add(company['symbol'])
    
    logger.info(f"Total US companies: {len(companies)}")
    return companies[:500]  # Return top 500


def get_nifty500_companies() -> List[Dict]:
    """Get NIFTY 500 company list"""
    try:
        # NIFTY 500 companies - using a curated list
        # In production, fetch from NSE API or data provider
        url = 'https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv'
        df = pd.read_csv(url)
        
        companies = []
        for _, row in df.iterrows():
            companies.append({
                'symbol': row['Symbol'],
                'company': row['Company Name'],
                'sector': row.get('Industry', ''),
                'industry': row.get('Industry', ''),
                'market': 'INDIA',
                'index': 'NIFTY500'
            })
        
        logger.info(f"Loaded {len(companies)} NIFTY 500 companies")
        return companies
    except Exception as e:
        logger.error(f"Error loading NIFTY 500: {e}")
        # Fallback to major Indian companies
        return get_fallback_india_companies()


def get_fallback_india_companies() -> List[Dict]:
    """Fallback list of major Indian companies"""
    companies_list = [
        {'symbol': 'RELIANCE', 'company': 'Reliance Industries Ltd', 'sector': 'Energy', 'industry': 'Oil & Gas'},
        {'symbol': 'TCS', 'company': 'Tata Consultancy Services Ltd', 'sector': 'IT', 'industry': 'IT Services'},
        {'symbol': 'HDFCBANK', 'company': 'HDFC Bank Ltd', 'sector': 'Financial', 'industry': 'Banking'},
        {'symbol': 'INFY', 'company': 'Infosys Ltd', 'sector': 'IT', 'industry': 'IT Services'},
        {'symbol': 'ICICIBANK', 'company': 'ICICI Bank Ltd', 'sector': 'Financial', 'industry': 'Banking'},
        {'symbol': 'HINDUNILVR', 'company': 'Hindustan Unilever Ltd', 'sector': 'FMCG', 'industry': 'Consumer Goods'},
        {'symbol': 'BHARTIARTL', 'company': 'Bharti Airtel Ltd', 'sector': 'Telecom', 'industry': 'Telecommunications'},
        {'symbol': 'ITC', 'company': 'ITC Ltd', 'sector': 'FMCG', 'industry': 'Consumer Goods'},
        {'symbol': 'KOTAKBANK', 'company': 'Kotak Mahindra Bank Ltd', 'sector': 'Financial', 'industry': 'Banking'},
        {'symbol': 'LT', 'company': 'Larsen & Toubro Ltd', 'sector': 'Infrastructure', 'industry': 'Construction'},
        {'symbol': 'SBIN', 'company': 'State Bank of India', 'sector': 'Financial', 'industry': 'Banking'},
        {'symbol': 'AXISBANK', 'company': 'Axis Bank Ltd', 'sector': 'Financial', 'industry': 'Banking'},
        {'symbol': 'ASIANPAINT', 'company': 'Asian Paints Ltd', 'sector': 'Consumer Durables', 'industry': 'Paints'},
        {'symbol': 'MARUTI', 'company': 'Maruti Suzuki India Ltd', 'sector': 'Automobile', 'industry': 'Automobiles'},
        {'symbol': 'TITAN', 'company': 'Titan Company Ltd', 'sector': 'Consumer Durables', 'industry': 'Jewelry'},
        {'symbol': 'WIPRO', 'company': 'Wipro Ltd', 'sector': 'IT', 'industry': 'IT Services'},
        {'symbol': 'HCLTECH', 'company': 'HCL Technologies Ltd', 'sector': 'IT', 'industry': 'IT Services'},
        {'symbol': 'ULTRACEMCO', 'company': 'UltraTech Cement Ltd', 'sector': 'Cement', 'industry': 'Cement'},
        {'symbol': 'SUNPHARMA', 'company': 'Sun Pharmaceutical Industries Ltd', 'sector': 'Pharma', 'industry': 'Pharmaceuticals'},
        {'symbol': 'BAJFINANCE', 'company': 'Bajaj Finance Ltd', 'sector': 'Financial', 'industry': 'NBFC'},
        {'symbol': 'NESTLEIND', 'company': 'Nestle India Ltd', 'sector': 'FMCG', 'industry': 'Food Products'},
        {'symbol': 'TATAMOTORS', 'company': 'Tata Motors Ltd', 'sector': 'Automobile', 'industry': 'Automobiles'},
        {'symbol': 'TATASTEEL', 'company': 'Tata Steel Ltd', 'sector': 'Metals', 'industry': 'Steel'},
        {'symbol': 'ADANIPORTS', 'company': 'Adani Ports and SEZ Ltd', 'sector': 'Infrastructure', 'industry': 'Ports'},
        {'symbol': 'ONGC', 'company': 'Oil and Natural Gas Corporation Ltd', 'sector': 'Energy', 'industry': 'Oil & Gas'},
        # Add more companies to reach 500
    ]
    
    for company in companies_list:
        company['market'] = 'INDIA'
        company['index'] = 'NIFTY500'
    
    logger.info(f"Using fallback list with {len(companies_list)} Indian companies")
    return companies_list


def get_all_companies() -> Dict[str, List[Dict]]:
    """Get all companies from both markets"""
    return {
        'US': get_top_us_companies(),
        'INDIA': get_nifty500_companies()
    }


if __name__ == "__main__":
    # Test the functions
    logging.basicConfig(level=logging.INFO)
    
    us_companies = get_top_us_companies()
    print(f"\nUS Companies: {len(us_companies)}")
    print(us_companies[:5])
    
    india_companies = get_nifty500_companies()
    print(f"\nIndia Companies: {len(india_companies)}")
    print(india_companies[:5])
