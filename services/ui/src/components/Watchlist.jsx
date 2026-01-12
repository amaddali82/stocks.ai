import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Star, Plus, Minus } from 'lucide-react';

export default function Watchlist({ symbols = [], marketData = {}, onSymbolSelect }) {
  const [watchlistItems, setWatchlistItems] = useState([]);

  useEffect(() => {
    // Create watchlist with unique symbols
    const uniqueSymbols = [...new Set(symbols)];
    const items = uniqueSymbols.map(symbol => ({
      symbol,
      price: marketData[symbol]?.price || 0,
      change: marketData[symbol]?.change || 0,
      starred: false
    }));
    setWatchlistItems(items);
  }, [symbols, marketData]);

  const toggleStar = (symbol) => {
    setWatchlistItems(items =>
      items.map(item =>
        item.symbol === symbol ? { ...item, starred: !item.starred } : item
      )
    );
  };

  return (
    <div className="h-full flex">
      {/* Main Watchlist */}
      <div className="flex-1 border-r border-gray-800 overflow-y-auto">
        <div className="sticky top-0 bg-[#1a1f2e] border-b border-gray-800 p-4 z-10">
          <h2 className="text-lg font-bold text-white">Watchlist</h2>
        </div>
        
        <div className="divide-y divide-gray-800">
          {watchlistItems.map((item) => (
            <div
              key={item.symbol}
              onClick={() => onSymbolSelect(item.symbol)}
              className="p-4 hover:bg-gray-900/50 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleStar(item.symbol);
                    }}
                    className="p-1"
                  >
                    <Star
                      className={`w-4 h-4 ${
                        item.starred ? 'text-yellow-400 fill-yellow-400' : 'text-gray-500'
                      }`}
                    />
                  </button>
                  <div>
                    <p className="font-semibold text-white">{item.symbol}</p>
                    <p className="text-xs text-gray-500">{item.price ? `$${item.price.toFixed(2)}` : '-'}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`flex items-center gap-1 ${
                    item.change >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {item.change >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    <span className="text-sm font-semibold">
                      {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
