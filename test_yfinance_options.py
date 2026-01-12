import yfinance as yf
import time

print("Testing yfinance options data...")
symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

for symbol in symbols:
    try:
        time.sleep(1)  # Rate limit
        ticker = yf.Ticker(symbol)
        opts = ticker.options
        if opts and len(opts) > 0:
            print(f"✓ {symbol}: {len(opts)} expiry dates available")
            # Try to get first option chain
            time.sleep(1)
            chain = ticker.option_chain(opts[0])
            print(f"  - {opts[0]}: {len(chain.calls)} calls available")
            if len(chain.calls) > 0:
                best_call = chain.calls.iloc[0]
                print(f"  - Strike: {best_call['strike']}, Last: ${best_call['lastPrice']}")
        else:
            print(f"✗ {symbol}: No options available")
    except Exception as e:
        print(f"✗ {symbol}: Error - {str(e)[:80]}")

print("\nDone!")
