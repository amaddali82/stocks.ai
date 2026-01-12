import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3 } from 'lucide-react';

export default function MarketOverview() {
  const [marketData, setMarketData] = useState({
    indices: [
      { name: 'S&P 500', value: 4783.45, change: 0.85, changePercent: 1.2 },
      { name: 'NASDAQ', value: 15849.46, change: -45.23, changePercent: -0.28 },
      { name: 'DOW JONES', value: 37305.16, change: 157.06, changePercent: 0.42 }
    ],
    topGainers: [],
    topLosers: [],
    mostActive: []
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* Page Title */}
        <div>
          <h2 className="text-2xl font-bold text-white">Market Overview</h2>
          <p className="text-sm text-gray-400 mt-1">Real-time market data and insights</p>
        </div>

        {/* Major Indices */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Major Indices</h3>
          <div className="grid grid-cols-3 gap-4">
            {marketData.indices.map((index, idx) => (
              <div key={idx} className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5">
                <p className="text-sm text-gray-400 mb-2">{index.name}</p>
                <p className="text-2xl font-bold text-white mb-2">
                  {index.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
                <div className={`flex items-center gap-2 ${
                  index.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {index.changePercent >= 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  <span className="font-semibold">
                    {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)} ({index.changePercent >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Movers */}
        <div className="grid grid-cols-2 gap-6">
          {/* Top Gainers */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Top Gainers
            </h3>
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl overflow-hidden">
              {marketData.topGainers.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {marketData.topGainers.map((stock, idx) => (
                    <div key={idx} className="p-4 flex items-center justify-between hover:bg-gray-900/30">
                      <div>
                        <p className="font-semibold text-white">{stock.symbol}</p>
                        <p className="text-sm text-gray-400">${stock.price}</p>
                      </div>
                      <div className="text-right text-green-400">
                        <p className="font-semibold">+{stock.changePercent}%</p>
                        <p className="text-sm">+${stock.change}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Top Losers */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-red-400" />
              Top Losers
            </h3>
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl overflow-hidden">
              {marketData.topLosers.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No data available</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {marketData.topLosers.map((stock, idx) => (
                    <div key={idx} className="p-4 flex items-center justify-between hover:bg-gray-900/30">
                      <div>
                        <p className="font-semibold text-white">{stock.symbol}</p>
                        <p className="text-sm text-gray-400">${stock.price}</p>
                      </div>
                      <div className="text-right text-red-400">
                        <p className="font-semibold">{stock.changePercent}%</p>
                        <p className="text-sm">${stock.change}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Most Active Options */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            Most Active Options
          </h3>
          <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl overflow-hidden">
            {marketData.mostActive.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No data available</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-900/50 border-b border-gray-800">
                  <tr>
                    <th className="text-left p-4 text-xs text-gray-400 font-semibold">Symbol</th>
                    <th className="text-left p-4 text-xs text-gray-400 font-semibold">Type</th>
                    <th className="text-right p-4 text-xs text-gray-400 font-semibold">Strike</th>
                    <th className="text-right p-4 text-xs text-gray-400 font-semibold">Price</th>
                    <th className="text-right p-4 text-xs text-gray-400 font-semibold">Volume</th>
                    <th className="text-right p-4 text-xs text-gray-400 font-semibold">Change</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {marketData.mostActive.map((option, idx) => (
                    <tr key={idx} className="hover:bg-gray-900/30">
                      <td className="p-4 font-semibold text-white">{option.symbol}</td>
                      <td className="p-4">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                          option.type === 'call'
                            ? 'bg-blue-900/30 text-blue-400'
                            : 'bg-red-900/30 text-red-400'
                        }`}>
                          {option.type.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-4 text-right text-gray-300">${option.strike}</td>
                      <td className="p-4 text-right text-white">${option.price}</td>
                      <td className="p-4 text-right text-gray-300">{option.volume}</td>
                      <td className={`p-4 text-right font-semibold ${
                        option.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {option.changePercent >= 0 ? '+' : ''}{option.changePercent}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Market Sentiment */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-yellow-400" />
            Market Sentiment
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5 text-center">
              <p className="text-sm text-gray-400 mb-2">VIX</p>
              <p className="text-2xl font-bold text-yellow-400">14.32</p>
              <p className="text-xs text-gray-500 mt-1">Volatility Index</p>
            </div>
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5 text-center">
              <p className="text-sm text-gray-400 mb-2">Put/Call Ratio</p>
              <p className="text-2xl font-bold text-white">0.87</p>
              <p className="text-xs text-gray-500 mt-1">Market Direction</p>
            </div>
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5 text-center">
              <p className="text-sm text-gray-400 mb-2">Advances</p>
              <p className="text-2xl font-bold text-green-400">2,345</p>
              <p className="text-xs text-gray-500 mt-1">Stocks Up</p>
            </div>
            <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5 text-center">
              <p className="text-sm text-gray-400 mb-2">Declines</p>
              <p className="text-2xl font-bold text-red-400">1,876</p>
              <p className="text-xs text-gray-500 mt-1">Stocks Down</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
