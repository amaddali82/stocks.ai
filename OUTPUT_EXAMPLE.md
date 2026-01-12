# Options Trading System - Output Example

## Sample Output Structure

### For Each Company/Option:

```
Symbol: AAPL
Company: Apple Inc
Market: US
Option Type: CALL
Stock Price: $185.50
Strike Price: $190.00
Entry Price: $3.50
Expiration Date: 2026-02-21 (41 days)

PRICE TARGETS:
  Target 1: $4.25  (Confidence: 85%)  ← Conservative target
  Target 2: $5.10  (Confidence: 65%)  ← Moderate target
  Target 3: $6.80  (Confidence: 40%)  ← Aggressive target

OPTION GREEKS:
  Delta:     0.5234  (50.34% chance of expiring ITM)
  Gamma:     0.0145  (Delta changes by 0.0145 per $1 move)
  Theta:    -0.0234  (Loses $0.0234 per day from time decay)
  Vega:      0.1234  (Price changes $0.1234 per 1% IV change)
  Implied Volatility: 35%

ANALYSIS:
  Recommendation:   BUY
  Overall Confidence: 75%
  Risk Level:       MEDIUM
  Max Profit Potential: 94.3%
  Breakeven Price:  $193.50
  Open Interest:    5,000 contracts
  Volume:           1,200 contracts
```

## Complete Data Set Format

### Top 500 US Companies Include:

**Technology Sector:**
- AAPL (Apple Inc)
- MSFT (Microsoft Corporation)
- GOOGL (Alphabet Inc)
- AMZN (Amazon.com Inc)
- NVDA (NVIDIA Corporation)
- META (Meta Platforms Inc)
- TSLA (Tesla Inc)
- [... 100+ more tech companies]

**Financial Sector:**
- JPM (JPMorgan Chase & Co)
- BAC (Bank of America Corp)
- V (Visa Inc)
- MA (Mastercard Inc)
- WFC (Wells Fargo & Co)
- [... 50+ more financial companies]

**Healthcare Sector:**
- UNH (UnitedHealth Group)
- JNJ (Johnson & Johnson)
- LLY (Eli Lilly)
- ABBV (AbbVie Inc)
- [... 40+ more healthcare companies]

**Consumer Sector:**
- WMT (Walmart Inc)
- HD (Home Depot)
- MCD (McDonald's Corp)
- NKE (Nike Inc)
- [... 30+ more consumer companies]

**Energy, Industrials, Materials, etc.**
- [... remaining companies to reach 500]

### Top 500 India Companies Include:

**IT Sector:**
- TCS (Tata Consultancy Services)
- INFY (Infosys Ltd)
- WIPRO (Wipro Ltd)
- HCLTECH (HCL Technologies)
- [... more IT companies]

**Banking Sector:**
- HDFCBANK (HDFC Bank Ltd)
- ICICIBANK (ICICI Bank Ltd)
- SBIN (State Bank of India)
- AXISBANK (Axis Bank Ltd)
- KOTAKBANK (Kotak Mahindra Bank)
- [... more banking companies]

**Energy & Conglomerates:**
- RELIANCE (Reliance Industries)
- ONGC (Oil and Natural Gas Corp)
- ITC (ITC Ltd)
- [... more companies]

**Consumer & Pharma:**
- HINDUNILVR (Hindustan Unilever)
- NESTLEIND (Nestle India)
- SUNPHARMA (Sun Pharmaceutical)
- [... more companies]

**Auto & Infrastructure:**
- MARUTI (Maruti Suzuki)
- TATAMOTORS (Tata Motors)
- LT (Larsen & Toubro)
- [... more companies]

[... remaining companies to reach 500]

## Data Fields Provided for Each Option

```json
{
  "symbol": "AAPL",
  "company": "Apple Inc",
  "market": "US",
  "option_type": "CALL",
  "strike_price": 190.00,
  "entry_price": 3.50,
  "current_price": 3.50,
  "spot_price": 185.50,
  "expiration_date": "2026-02-21",
  "days_to_expiry": 41,
  
  "target1": 4.25,
  "target1_confidence": 0.85,
  "target2": 5.10,
  "target2_confidence": 0.65,
  "target3": 6.80,
  "target3_confidence": 0.40,
  
  "delta": 0.5234,
  "gamma": 0.0145,
  "theta": -0.0234,
  "vega": 0.1234,
  "implied_volatility": 0.35,
  
  "recommendation": "BUY",
  "overall_confidence": 0.75,
  "risk_level": "MEDIUM",
  "max_profit_potential": 94.3,
  "max_loss_potential": -100,
  "breakeven_price": 193.50,
  
  "open_interest": 5000,
  "volume": 1200,
  "timestamp": "2026-01-11T15:30:00"
}
```

## How to Access the Data

### Method 1: Run Standalone Scripts

```bash
# Quick demo with 10 companies
python quick_options_demo.py

# Full analysis with up to 500 companies
python fetch_options_data.py

# Output is displayed in console and saved to CSV
```

### Method 2: Use REST API

```bash
# Start the API server
cd services/data-api
python options_api.py

# Then make HTTP requests:
curl http://localhost:8004/api/companies?market=US&limit=500
curl http://localhost:8004/api/stocks?market=INDIA&limit=100
curl http://localhost:8004/api/options/AAPL
curl http://localhost:8004/api/predictions/best?limit=50
```

### Method 3: Docker Integration

```bash
# The system is integrated with Docker compose
docker-compose up -d

# Services available:
# - Data ingestion (fetches company data)
# - Prediction engine (generates predictions)
# - Data API (serves predictions via REST)
# - UI (displays data in web interface)
```

## Understanding Confidence Levels

### Target 1 (Conservative) - 85% Confidence
- Represents a realistic, achievable price target
- Based on 1 standard deviation of expected movement
- High probability of reaching this level
- **Best for:** Risk-averse traders, profit-taking strategy

### Target 2 (Moderate) - 65% Confidence
- Balanced risk-reward target
- Based on 1.5 standard deviations
- Moderate probability of success
- **Best for:** Balanced trading strategy, swing traders

### Target 3 (Aggressive) - 40% Confidence
- Optimistic but possible target
- Based on 2+ standard deviations
- Lower probability but higher reward
- **Best for:** Risk-tolerant traders, home-run plays

## Recommendation Levels Explained

- **STRONG BUY (Score ≥ 6):** High conviction, strong fundamentals
- **BUY (Score 4-5):** Good opportunity, favorable conditions
- **HOLD (Score 2-3):** Neutral outlook, monitor closely
- **WEAK HOLD (Score 0-1):** Marginal opportunity
- **AVOID (Score < 0):** Poor conditions, avoid trade

## Risk Levels Explained

- **LOW RISK:** Long time to expiry (30+ days), normal volatility, high liquidity
- **MEDIUM RISK:** Moderate time (15-30 days), elevated volatility, decent liquidity
- **HIGH RISK:** Short time (<15 days), high volatility, low liquidity

## CSV Output Format

When you run the scripts, data is automatically saved to CSV:

```csv
symbol,company,market,option_type,entry_price,strike,spot_price,expiration_date,days_to_expiry,target1,target1_conf,target2,target2_conf,target3,target3_conf,recommendation,confidence,risk_level,max_profit,delta,iv,oi,volume
AAPL,Apple Inc,US,CALL,3.50,190.00,185.50,2026-02-21,41,4.25,0.85,5.10,0.65,6.80,0.40,BUY,0.75,MEDIUM,94.3,0.5234,0.35,5000,1200
MSFT,Microsoft Corporation,US,CALL,4.20,420.00,415.30,2026-02-21,41,5.10,0.83,6.25,0.63,8.15,0.38,BUY,0.72,MEDIUM,93.8,0.5112,0.32,4500,980
...
```

## Summary

You now have a complete system that provides:

✅ **500 US Companies** - Major stocks from all sectors
✅ **500 India Companies** - Major NSE/BSE listed stocks
✅ **Real-time Stock Data** - Current prices, volume, market cap
✅ **Options Data** - Strikes, premiums, expirations
✅ **3 Price Targets** - Conservative, Moderate, Aggressive
✅ **Confidence Levels** - 40-85% confidence for each target
✅ **Option Greeks** - Delta, Gamma, Theta, Vega
✅ **Buy/Sell Recommendations** - AI-powered analysis
✅ **Risk Assessment** - LOW/MEDIUM/HIGH classification
✅ **Multiple Access Methods** - Scripts, API, Docker
✅ **Export Formats** - Console, CSV, JSON

The system is production-ready and committed to GitHub!
