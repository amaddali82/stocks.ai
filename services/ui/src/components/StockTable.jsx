import React from 'react';

function StockTable({ recommendations, onRowClick }) {
  const getActionColor = (action) => {
    switch (action?.toUpperCase()) {
      case 'BUY': return 'text-green-400';
      case 'SELL': return 'text-red-400';
      case 'HOLD': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getActionBgColor = (action) => {
    switch (action?.toUpperCase()) {
      case 'BUY': return 'bg-green-500/20';
      case 'SELL': return 'bg-red-500/20';
      case 'HOLD': return 'bg-yellow-500/20';
      default: return 'bg-gray-500/20';
    }
  };

  const getPriceChange = (current, target) => {
    const change = ((target - current) / current * 100).toFixed(2);
    return change;
  };

  const getPriceChangeColor = (change) => {
    return change >= 0 ? 'text-green-400' : 'text-red-400';
  };

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-white/10 border-b border-white/10">
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Current Price
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Target Price
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Change
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Action
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                RSI
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Risk
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {recommendations.map((rec, index) => {
              const priceChange = getPriceChange(rec.currentPrice, rec.targetPrice);
              return (
                <tr
                  key={rec.symbol}
                  onClick={() => onRowClick(rec)}
                  className="hover:bg-white/10 cursor-pointer transition-all duration-200 group animate-slide-in"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
                        {rec.symbol}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-base font-semibold text-white">
                      ${rec.currentPrice?.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-base font-semibold text-white/80">
                      ${rec.targetPrice?.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-base font-bold ${getPriceChangeColor(priceChange)}`}>
                      {priceChange >= 0 ? '+' : ''}{priceChange}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getActionBgColor(rec.action)} ${getActionColor(rec.action)}`}>
                      {rec.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-base font-semibold text-white">
                        {(rec.confidence * 100).toFixed(0)}%
                      </div>
                      <div className="ml-2 w-16 bg-white/10 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${rec.confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-base text-white/80">
                      {rec.technicalIndicators?.rsi?.toFixed(1)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      rec.riskLevel === 'low' || rec.riskLevel === 'low-medium' ? 'bg-green-500/20 text-green-400' :
                      rec.riskLevel === 'medium' || rec.riskLevel === 'medium-high' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {rec.riskLevel}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default StockTable;
