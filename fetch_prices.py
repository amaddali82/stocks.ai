import yfinance as yf
import sys

symbols = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'MSFT', 'META', 'SPY', 'QQQ', 'DIA']
print('Fetching current market prices...\n')

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            print(f'{symbol}: ${price:.2f}')
        else:
            print(f'{symbol}: No data available')
    except Exception as e:
        print(f'{symbol}: Error - {e}')
