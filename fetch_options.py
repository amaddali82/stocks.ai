import yfinance as yf
from datetime import datetime

symbols = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'MSFT', 'META']
print('Fetching options data...\n')

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        
        # Get current stock price
        hist = ticker.history(period="1d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f'\n{symbol}: ${current_price:.2f}')
        
        # Get available expiration dates
        expirations = ticker.options
        if expirations:
            print(f'  Available option expirations: {len(expirations)} dates')
            print(f'  Nearest: {expirations[0]}, Furthest: {expirations[-1]}')
            
            # Get options for nearest expiration
            opt_chain = ticker.option_chain(expirations[0])
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            print(f'  Calls available: {len(calls)} contracts')
            print(f'  Puts available: {len(puts)} contracts')
            
            # Show some ATM options
            atm_calls = calls[calls['strike'].between(current_price * 0.95, current_price * 1.05)]
            atm_puts = puts[puts['strike'].between(current_price * 0.95, current_price * 1.05)]
            
            if not atm_calls.empty:
                print(f'  ATM Call example: Strike ${atm_calls.iloc[0]["strike"]:.2f}, Last ${atm_calls.iloc[0]["lastPrice"]:.2f}')
            if not atm_puts.empty:
                print(f'  ATM Put example: Strike ${atm_puts.iloc[0]["strike"]:.2f}, Last ${atm_puts.iloc[0]["lastPrice"]:.2f}')
        else:
            print(f'  No options data available')
            
    except Exception as e:
        print(f'{symbol}: Error - {str(e)[:100]}')

# Index options
print('\n\nIndex Options (SPY, QQQ, DIA):')
for symbol in ['SPY', 'QQQ', 'DIA']:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f'\n{symbol}: ${current_price:.2f}')
        
        expirations = ticker.options
        if expirations:
            print(f'  Available expirations: {len(expirations)} dates')
            opt_chain = ticker.option_chain(expirations[0])
            print(f'  Calls: {len(opt_chain.calls)}, Puts: {len(opt_chain.puts)}')
    except Exception as e:
        print(f'{symbol}: Error - {str(e)[:100]}')
