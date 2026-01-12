"""
Quick Options Demo - Shows predictions for top companies
"""

import yfinance as yf
from datetime import datetime
import sys
import os

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'data-ingestion'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'prediction-engine'))

from models.options_predictor import OptionsPredictor

# Top companies to analyze
TOP_COMPANIES = [
    {'symbol': 'AAPL', 'company': 'Apple Inc', 'market': 'US'},
    {'symbol': 'MSFT', 'company': 'Microsoft Corporation', 'market': 'US'},
    {'symbol': 'GOOGL', 'company': 'Alphabet Inc', 'market': 'US'},
    {'symbol': 'AMZN', 'company': 'Amazon.com Inc', 'market': 'US'},
    {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'market': 'US'},
    {'symbol': 'TSLA', 'company': 'Tesla Inc', 'market': 'US'},
    {'symbol': 'META', 'company': 'Meta Platforms Inc', 'market': 'US'},
    {'symbol': 'JPM', 'company': 'JPMorgan Chase & Co', 'market': 'US'},
    {'symbol': 'V', 'company': 'Visa Inc', 'market': 'US'},
    {'symbol': 'WMT', 'company': 'Walmart Inc', 'market': 'US'},
]

def main():
    print("\n" + "="*120)
    print("OPTIONS TRADING PREDICTIONS - TOP US COMPANIES")
    print("="*120 + "\n")
    
    predictor = OptionsPredictor()
    results = []
    
    for idx, company in enumerate(TOP_COMPANIES, 1):
        print(f"[{idx}/{len(TOP_COMPANIES)}] Analyzing {company['symbol']} - {company['company']}...")
        
        try:
            ticker = yf.Ticker(company['symbol'])
            info = ticker.info
            spot_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if spot_price == 0:
                print(f"  ✗ No price data\n")
                continue
            
            print(f"  Stock Price: ${spot_price:.2f}")
            
            expirations = ticker.options
            if not expirations:
                print(f"  ✗ No options available\n")
                continue
            
            # Get first expiration
            target_expiry = expirations[0]
            expiry_date = datetime.strptime(target_expiry, '%Y-%m-%d')
            days_to_expiry = (expiry_date - datetime.now()).days
            
            print(f"  Analyzing options expiring: {target_expiry} ({days_to_expiry} days)")
            
            opt_chain = ticker.option_chain(target_expiry)
            
            # Find ATM call
            calls_df = opt_chain.calls
            calls_df = calls_df[(calls_df['openInterest'] > 50) & (calls_df['volume'] > 10)].copy()
            
            if len(calls_df) == 0:
                print(f"  ✗ No liquid options\n")
                continue
            
            calls_df['moneyness'] = abs(calls_df['strike'] - spot_price) / spot_price
            atm_call = calls_df.nsmallest(1, 'moneyness').iloc[0]
            
            # Generate prediction
            prediction = predictor.predict_option(
                symbol=company['symbol'],
                company=company['company'],
                market=company['market'],
                spot_price=spot_price,
                strike_price=atm_call['strike'],
                option_price=atm_call['lastPrice'],
                expiration_date=target_expiry,
                option_type='CALL',
                implied_volatility=atm_call.get('impliedVolatility', 0.3),
                open_interest=int(atm_call.get('openInterest', 0)),
                volume=int(atm_call.get('volume', 0))
            )
            
            results.append(prediction)
            
            print(f"  ✓ PREDICTION:")
            print(f"    Recommendation: {prediction.recommendation}")
            print(f"    Confidence: {prediction.overall_confidence*100:.1f}%")
            print(f"    Risk Level: {prediction.risk_level}")
            print(f"    Entry Price: ${prediction.entry_price:.2f}")
            print(f"    Strike: ${prediction.strike_price:.2f}")
            print(f"    Target 1: ${prediction.target1:.2f} (Confidence: {prediction.target1_confidence*100:.0f}%)")
            print(f"    Target 2: ${prediction.target2:.2f} (Confidence: {prediction.target2_confidence*100:.0f}%)")
            print(f"    Target 3: ${prediction.target3:.2f} (Confidence: {prediction.target3_confidence*100:.0f}%)")
            print(f"    Max Profit Potential: {prediction.max_profit_potential:.1f}%")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            continue
    
    # Show summary
    print("\n" + "="*120)
    print(f"SUMMARY - OPTIONS PREDICTIONS FOR {len(results)} COMPANIES")
    print("="*120 + "\n")
    
    # Sort by confidence
    results.sort(key=lambda x: x.overall_confidence, reverse=True)
    
    print(f"{'Symbol':<8} {'Company':<30} {'Entry':<10} {'Expiry':<12} {'Target 1':<15} {'Target 2':<15} {'Target 3':<15} {'Rec':<12} {'Conf':<8} {'Risk':<8}")
    print("-" * 120)
    
    for r in results:
        print(f"{r.symbol:<8} {r.company[:28]:<30} ${r.entry_price:<9.2f} {r.expiration_date:<12} "
              f"${r.target1:<5.2f} ({r.target1_confidence*100:.0f}%) {' ':<4} "
              f"${r.target2:<5.2f} ({r.target2_confidence*100:.0f}%) {' ':<4} "
              f"${r.target3:<5.2f} ({r.target3_confidence*100:.0f}%) {' ':<4} "
              f"{r.recommendation:<12} {r.overall_confidence*100:<7.1f}% {r.risk_level:<8}")
    
    # Show best opportunity
    if results:
        print("\n" + "="*120)
        print("BEST OPPORTUNITY")
        print("="*120)
        best = results[0]
        print(f"\nSymbol:           {best.symbol}")
        print(f"Company:          {best.company}")
        print(f"Option Type:      {best.option_type}")
        print(f"Stock Price:      ${best.current_price:.2f}")
        print(f"Strike Price:     ${best.strike_price:.2f}")
        print(f"Entry Price:      ${best.entry_price:.2f}")
        print(f"Expiration:       {best.expiration_date} ({best.days_to_expiry} days)")
        print(f"\nPRICE TARGETS:")
        print(f"  Target 1:       ${best.target1:.2f}  (Confidence: {best.target1_confidence*100:.1f}%)")
        print(f"  Target 2:       ${best.target2:.2f}  (Confidence: {best.target2_confidence*100:.1f}%)")
        print(f"  Target 3:       ${best.target3:.2f}  (Confidence: {best.target3_confidence*100:.1f}%)")
        print(f"\nANALYSIS:")
        print(f"  Recommendation:   {best.recommendation}")
        print(f"  Confidence:       {best.overall_confidence*100:.1f}%")
        print(f"  Risk Level:       {best.risk_level}")
        print(f"  Delta:            {best.delta:.4f}")
        print(f"  Implied Vol:      {best.implied_volatility:.2%}")
        print(f"  Breakeven:        ${best.breakeven_price:.2f}")
        print(f"  Max Profit:       {best.max_profit_potential:.1f}%")
        print(f"  Open Interest:    {best.open_interest:,}")
        print(f"  Volume:           {best.volume:,}")
        print("="*120 + "\n")

if __name__ == "__main__":
    main()
