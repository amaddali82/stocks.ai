"""
Test script to run the options API and fetch top companies with predictions
"""

import requests
import json
from tabulate import tabulate

API_BASE_URL = "http://localhost:8004"


def test_companies():
    """Test getting company lists"""
    print("\n" + "="*100)
    print("TESTING: Get Top Companies")
    print("="*100)
    
    # Get US companies
    response = requests.get(f"{API_BASE_URL}/api/companies?market=US&limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"\nUS Companies (showing 10 of {data['total']}):")
        companies = data['companies'][:5]
        for c in companies:
            print(f"  • {c['symbol']:8s} - {c['company'][:50]:50s} | {c['sector'][:20]:20s}")
    
    # Get India companies
    response = requests.get(f"{API_BASE_URL}/api/companies?market=INDIA&limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"\nIndia Companies (showing 10 of {data['total']}):")
        companies = data['companies'][:5]
        for c in companies:
            print(f"  • {c['symbol']:15s} - {c['company'][:50]:50s} | {c['sector'][:20]:20s}")


def test_stocks():
    """Test getting stock data"""
    print("\n" + "="*100)
    print("TESTING: Get Stock Data")
    print("="*100)
    
    response = requests.get(f"{API_BASE_URL}/api/stocks?market=US&limit=5")
    if response.status_code == 200:
        stocks = response.json()
        print(f"\nFetched {len(stocks)} stocks:")
        
        table_data = []
        for stock in stocks:
            table_data.append([
                stock['symbol'],
                stock['company'][:30],
                f"${stock['current_price']:.2f}",
                f"{stock['change_percent']:.2f}%",
                f"{stock['volume']:,}",
                stock['sector'][:20]
            ])
        
        print(tabulate(table_data, 
                      headers=['Symbol', 'Company', 'Price', 'Change%', 'Volume', 'Sector'],
                      tablefmt='grid'))


def test_options_for_symbol(symbol='AAPL'):
    """Test getting options for a specific symbol"""
    print("\n" + "="*100)
    print(f"TESTING: Get Options Predictions for {symbol}")
    print("="*100)
    
    response = requests.get(f"{API_BASE_URL}/api/options/{symbol}?expiry_days_min=14&expiry_days_max=60")
    if response.status_code == 200:
        options = response.json()
        print(f"\nFound {len(options)} options for {symbol}")
        
        # Show top 5 options
        table_data = []
        for opt in options[:5]:
            table_data.append([
                opt['option_type'],
                f"${opt['strike_price']:.2f}",
                f"${opt['entry_price']:.2f}",
                opt['expiration_date'],
                opt['days_to_expiry'],
                f"${opt['target1']:.2f} ({opt['target1_confidence']*100:.0f}%)",
                f"${opt['target2']:.2f} ({opt['target2_confidence']*100:.0f}%)",
                f"${opt['target3']:.2f} ({opt['target3_confidence']*100:.0f}%)",
                opt['recommendation'],
                f"{opt['overall_confidence']*100:.0f}%",
                opt['risk_level']
            ])
        
        print(tabulate(table_data,
                      headers=['Type', 'Strike', 'Entry', 'Expiry', 'Days', 'Target 1', 'Target 2', 'Target 3', 'Rec', 'Conf', 'Risk'],
                      tablefmt='grid'))


def test_best_predictions():
    """Test getting best predictions across all companies"""
    print("\n" + "="*100)
    print("TESTING: Get Best Options Predictions")
    print("="*100)
    
    response = requests.get(f"{API_BASE_URL}/api/predictions/best?min_confidence=0.60&max_risk=MEDIUM&limit=10")
    if response.status_code == 200:
        data = response.json()
        predictions = data['predictions']
        print(f"\nTop {len(predictions)} Options Predictions:")
        
        table_data = []
        for pred in predictions:
            table_data.append([
                pred['symbol'],
                pred['company'][:25],
                pred['option_type'],
                f"${pred['strike_price']:.2f}",
                f"${pred['entry_price']:.2f}",
                pred['expiration_date'],
                f"${pred['target1']:.2f}",
                f"{pred['target1_confidence']*100:.0f}%",
                f"${pred['target2']:.2f}",
                f"{pred['target2_confidence']*100:.0f}%",
                f"${pred['target3']:.2f}",
                f"{pred['target3_confidence']*100:.0f}%",
                pred['recommendation'],
                f"{pred['overall_confidence']*100:.0f}%",
                pred['risk_level'],
                f"{pred['max_profit_potential']:.1f}%"
            ])
        
        print(tabulate(table_data,
                      headers=['Symbol', 'Company', 'Type', 'Strike', 'Entry', 'Expiry', 
                              'T1', 'C1', 'T2', 'C2', 'T3', 'C3', 'Rec', 'Conf', 'Risk', 'MaxProfit'],
                      tablefmt='grid'))
        
        # Show detailed view of best prediction
        if predictions:
            best = predictions[0]
            print(f"\n{'='*100}")
            print(f"BEST OPPORTUNITY: {best['symbol']} - {best['company']}")
            print(f"{'='*100}")
            print(f"Option Type:        {best['option_type']}")
            print(f"Strike Price:       ${best['strike_price']:.2f}")
            print(f"Entry Price:        ${best['entry_price']:.2f}")
            print(f"Expiration:         {best['expiration_date']} ({best['days_to_expiry']} days)")
            print(f"\nPRICE TARGETS:")
            print(f"  Target 1:         ${best['target1']:.2f}  (Confidence: {best['target1_confidence']*100:.1f}%)")
            print(f"  Target 2:         ${best['target2']:.2f}  (Confidence: {best['target2_confidence']*100:.1f}%)")
            print(f"  Target 3:         ${best['target3']:.2f}  (Confidence: {best['target3_confidence']*100:.1f}%)")
            print(f"\nANALYSIS:")
            print(f"  Recommendation:   {best['recommendation']}")
            print(f"  Overall Confidence: {best['overall_confidence']*100:.1f}%")
            print(f"  Risk Level:       {best['risk_level']}")
            print(f"  Delta:            {best['delta']:.4f}")
            print(f"  Implied Vol:      {best['implied_volatility']:.2%}")
            print(f"  Breakeven:        ${best['breakeven_price']:.2f}")
            print(f"  Max Profit:       {best['max_profit_potential']:.1f}%")
            print(f"  Open Interest:    {best['open_interest']:,}")
            print(f"  Volume:           {best['volume']:,}")
            print(f"{'='*100}")


def main():
    """Run all tests"""
    print("\n" + "="*100)
    print("OPTIONS TRADING API - COMPREHENSIVE TEST")
    print("Testing Top 500 Companies with Options Predictions")
    print("="*100)
    
    try:
        # Test 1: Get companies
        test_companies()
        
        # Test 2: Get stock data
        test_stocks()
        
        # Test 3: Get options for specific symbols
        test_options_for_symbol('AAPL')
        
        # Test 4: Get best predictions
        test_best_predictions()
        
        print("\n" + "="*100)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*100)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure the API is running on http://localhost:8004")


if __name__ == "__main__":
    main()
