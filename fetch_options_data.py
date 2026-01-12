"""
Standalone Options Data Fetcher
Fetches top 500 companies from US and India with options predictions
Can be run directly without Docker
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'data-ingestion'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'prediction-engine'))

from connectors.company_lists import get_all_companies
from models.options_predictor import OptionsPredictor


def fetch_options_data(symbols_list, market_name, max_companies=10):
    """Fetch options data with predictions for multiple companies"""
    
    print(f"\n{'='*120}")
    print(f"FETCHING OPTIONS DATA FOR TOP {market_name} COMPANIES")
    print(f"{'='*120}\n")
    
    predictor = OptionsPredictor()
    all_results = []
    
    for idx, company in enumerate(symbols_list[:max_companies], 1):
        symbol = company['symbol']
        company_name = company['company']
        
        print(f"[{idx}/{max_companies}] Processing {symbol} - {company_name}...")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            spot_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            if spot_price == 0:
                print(f"  ⚠ No price data available for {symbol}")
                continue
            
            # Get option expirations
            expirations = ticker.options
            if not expirations:
                print(f"  ⚠ No options available for {symbol}")
                continue
            
            # Find expiration between 2-8 weeks out
            target_expiry = None
            for expiry in expirations:
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                days_to_expiry = (expiry_date - datetime.now()).days
                if 14 <= days_to_expiry <= 60:
                    target_expiry = expiry
                    break
            
            if not target_expiry:
                target_expiry = expirations[0]
            
            # Get option chain
            opt_chain = ticker.option_chain(target_expiry)
            
            # Process calls - find ATM options with good liquidity
            calls_df = opt_chain.calls
            calls_df = calls_df[
                (calls_df['openInterest'] > 100) & 
                (calls_df['volume'] > 20)
            ].copy()
            
            if len(calls_df) > 0:
                # Find ATM call
                calls_df['moneyness'] = abs(calls_df['strike'] - spot_price) / spot_price
                atm_call = calls_df.nsmallest(1, 'moneyness').iloc[0]
                
                try:
                    prediction = predictor.predict_option(
                        symbol=symbol,
                        company=company_name,
                        market=market_name,
                        spot_price=spot_price,
                        strike_price=atm_call['strike'],
                        option_price=atm_call['lastPrice'],
                        expiration_date=target_expiry,
                        option_type='CALL',
                        implied_volatility=atm_call.get('impliedVolatility', 0.3),
                        open_interest=int(atm_call.get('openInterest', 0)),
                        volume=int(atm_call.get('volume', 0))
                    )
                    
                    all_results.append({
                        'symbol': prediction.symbol,
                        'company': prediction.company,
                        'market': prediction.market,
                        'option_type': prediction.option_type,
                        'entry_price': prediction.entry_price,
                        'strike': prediction.strike_price,
                        'spot_price': spot_price,
                        'expiration_date': prediction.expiration_date,
                        'days_to_expiry': prediction.days_to_expiry,
                        'target1': prediction.target1,
                        'target1_conf': prediction.target1_confidence,
                        'target2': prediction.target2,
                        'target2_conf': prediction.target2_confidence,
                        'target3': prediction.target3,
                        'target3_conf': prediction.target3_confidence,
                        'recommendation': prediction.recommendation,
                        'confidence': prediction.overall_confidence,
                        'risk_level': prediction.risk_level,
                        'max_profit': prediction.max_profit_potential,
                        'delta': prediction.delta,
                        'iv': prediction.implied_volatility,
                        'oi': prediction.open_interest,
                        'volume': prediction.volume
                    })
                    
                    print(f"  ✓ {prediction.recommendation} - Confidence: {prediction.overall_confidence*100:.0f}% - Risk: {prediction.risk_level}")
                    
                except Exception as e:
                    print(f"  ✗ Error predicting: {e}")
            
        except Exception as e:
            print(f"  ✗ Error fetching data: {e}")
            continue
    
    return all_results


def display_results(results, market_name):
    """Display results in formatted tables"""
    
    if not results:
        print(f"\nNo results available for {market_name}")
        return
    
    print(f"\n{'='*120}")
    print(f"{market_name} OPTIONS PREDICTIONS - SUMMARY")
    print(f"{'='*120}\n")
    
    # Create summary table
    table_data = []
    for r in results:
        table_data.append([
            r['symbol'],
            r['company'][:25],
            r['option_type'],
            f"${r['spot_price']:.2f}",
            f"${r['strike']:.2f}",
            f"${r['entry_price']:.2f}",
            r['expiration_date'],
            r['days_to_expiry'],
            f"${r['target1']:.2f}",
            f"{r['target1_conf']*100:.0f}%",
            f"${r['target2']:.2f}",
            f"{r['target2_conf']*100:.0f}%",
            f"${r['target3']:.2f}",
            f"{r['target3_conf']*100:.0f}%",
            r['recommendation'][:10],
            f"{r['confidence']*100:.0f}%",
            r['risk_level']
        ])
    
    print(tabulate(table_data,
                  headers=['Symbol', 'Company', 'Type', 'Spot', 'Strike', 'Entry', 
                          'Expiry', 'Days', 'Target1', 'Conf1', 'Target2', 'Conf2', 
                          'Target3', 'Conf3', 'Rec', 'Conf', 'Risk'],
                  tablefmt='grid'))
    
    # Show top 3 best opportunities
    sorted_results = sorted(results, key=lambda x: x['confidence'], reverse=True)
    
    print(f"\n{'='*120}")
    print(f"TOP 3 OPPORTUNITIES - {market_name}")
    print(f"{'='*120}\n")
    
    for idx, best in enumerate(sorted_results[:3], 1):
        print(f"\n{'─'*120}")
        print(f"#{idx}: {best['symbol']} - {best['company']}")
        print(f"{'─'*120}")
        print(f"  Market:           {best['market']}")
        print(f"  Option Type:      {best['option_type']}")
        print(f"  Stock Price:      ${best['spot_price']:.2f}")
        print(f"  Strike Price:     ${best['strike']:.2f}")
        print(f"  Entry Price:      ${best['entry_price']:.2f}")
        print(f"  Expiration:       {best['expiration_date']} ({best['days_to_expiry']} days)")
        print(f"\n  PRICE TARGETS:")
        print(f"    Target 1:       ${best['target1']:.2f}  (Confidence: {best['target1_conf']*100:.1f}%)")
        print(f"    Target 2:       ${best['target2']:.2f}  (Confidence: {best['target2_conf']*100:.1f}%)")
        print(f"    Target 3:       ${best['target3']:.2f}  (Confidence: {best['target3_conf']*100:.1f}%)")
        print(f"\n  ANALYSIS:")
        print(f"    Recommendation: {best['recommendation']}")
        print(f"    Confidence:     {best['confidence']*100:.1f}%")
        print(f"    Risk Level:     {best['risk_level']}")
        print(f"    Delta:          {best['delta']:.4f}")
        print(f"    Implied Vol:    {best['iv']:.2%}")
        print(f"    Max Profit:     {best['max_profit']:.1f}%")
        print(f"    Open Interest:  {best['oi']:,}")
        print(f"    Volume:         {best['volume']:,}")


def main():
    """Main function to fetch and display options data"""
    
    print("\n" + "="*120)
    print("OPTIONS TRADING ANALYSIS - TOP 500 COMPANIES (USA & INDIA)")
    print("Fetching stocks and options data with AI predictions")
    print("="*120)
    
    # Get all companies
    print("\nLoading company lists...")
    all_companies = get_all_companies()
    
    us_companies = all_companies['US']
    india_companies = all_companies['INDIA']
    
    print(f"✓ Loaded {len(us_companies)} US companies")
    print(f"✓ Loaded {len(india_companies)} India companies")
    
    # Fetch US options data
    print("\n" + "="*120)
    print("PART 1: ANALYZING US MARKET OPTIONS")
    print("="*120)
    us_results = fetch_options_data(us_companies, 'US', max_companies=15)
    display_results(us_results, 'US MARKET')
    
    # Fetch India options data (if available)
    print("\n" + "="*120)
    print("PART 2: ANALYZING INDIA MARKET OPTIONS")
    print("="*120)
    india_results = fetch_options_data(india_companies, 'INDIA', max_companies=10)
    display_results(india_results, 'INDIA MARKET')
    
    # Combined best opportunities
    all_results = us_results + india_results
    if all_results:
        sorted_all = sorted(all_results, key=lambda x: x['confidence'], reverse=True)
        
        print(f"\n{'='*120}")
        print("OVERALL TOP 5 BEST OPTIONS OPPORTUNITIES (ALL MARKETS)")
        print(f"{'='*120}\n")
        
        table_data = []
        for r in sorted_all[:5]:
            table_data.append([
                r['market'],
                r['symbol'],
                r['company'][:30],
                r['option_type'],
                f"${r['entry_price']:.2f}",
                r['expiration_date'],
                f"${r['target1']:.2f} ({r['target1_conf']*100:.0f}%)",
                f"${r['target2']:.2f} ({r['target2_conf']*100:.0f}%)",
                f"${r['target3']:.2f} ({r['target3_conf']*100:.0f}%)",
                r['recommendation'],
                f"{r['confidence']*100:.0f}%",
                r['risk_level'],
                f"{r['max_profit']:.1f}%"
            ])
        
        print(tabulate(table_data,
                      headers=['Market', 'Symbol', 'Company', 'Type', 'Entry', 'Expiry',
                              'Target 1', 'Target 2', 'Target 3', 'Rec', 'Conf', 'Risk', 'Max Profit'],
                      tablefmt='grid'))
    
    print(f"\n{'='*120}")
    print("ANALYSIS COMPLETE!")
    print(f"Total companies analyzed: {len(us_results) + len(india_results)}")
    print(f"{'='*120}\n")
    
    # Save to CSV
    if all_results:
        df = pd.DataFrame(all_results)
        filename = f"options_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"✓ Results saved to: {filename}\n")


if __name__ == "__main__":
    main()
