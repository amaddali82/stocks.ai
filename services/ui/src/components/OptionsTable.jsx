import React from 'react';
import { TrendingUp, DollarSign, Target, Calendar } from 'lucide-react';

function OptionsTable({ options, onRowClick }) {
  const getRecommendationColor = (rec) => {
    if (rec.includes('STRONG BUY')) return 'text-green-400 bg-green-500/20';
    if (rec.includes('BUY')) return 'text-green-300 bg-green-500/10';
    if (rec.includes('HOLD')) return 'text-yellow-300 bg-yellow-500/10';
    if (rec.includes('AVOID')) return 'text-red-400 bg-red-500/20';
    return 'text-gray-400 bg-gray-500/10';
  };

  const getRiskBadgeColor = (risk) => {
    switch (risk) {
      case 'LOW': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'HIGH': return 'bg-red-500/20 text-red-300 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const formatCurrency = (value) => {
    return '$' + value.toFixed(2);
  };

  const formatPercent = (value) => {
    return (value * 100).toFixed(0) + '%';
  };

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-white/10 border-b border-white/10">
              <th className="px-4 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-4 py-4 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-white/70 uppercase tracking-wider">
                Entry
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-white/70 uppercase tracking-wider">
                Strike
              </th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-white/70 uppercase tracking-wider">
                Expiry
              </th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-white/70 uppercase tracking-wider">
                Targets
              </th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-white/70 uppercase tracking-wider">
                Recommendation
              </th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-white/70 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-white/70 uppercase tracking-wider">
                Risk
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-white/70 uppercase tracking-wider">
                Max Profit
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {options.map((option, index) => (
              <tr
                key={index}
                onClick={() => onRowClick && onRowClick(option)}
                className="hover:bg-white/5 cursor-pointer transition-colors duration-150"
              >
                <td className="px-4 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-bold text-white">{option.symbol}</div>
                    <div className="text-xs text-white/50 truncate max-w-[150px]">{option.company}</div>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    option.option_type === 'CALL' 
                      ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                      : 'bg-red-500/20 text-red-300 border border-red-500/30'
                  }`}>
                    {option.option_type}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <div className="text-sm font-semibold text-white">{formatCurrency(option.entry_price)}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <div className="text-sm font-medium text-white/80">{formatCurrency(option.strike_price)}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-center">
                  <div className="text-xs text-white/70">{option.expiration_date}</div>
                  <div className="text-xs text-white/50">{option.days_to_expiry}d</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-green-400">{formatCurrency(option.target1)}</span>
                      <span className="text-green-400/60">{formatPercent(option.target1_confidence)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-blue-400">{formatCurrency(option.target2)}</span>
                      <span className="text-blue-400/60">{formatPercent(option.target2_confidence)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-purple-400">{formatCurrency(option.target3)}</span>
                      <span className="text-purple-400/60">{formatPercent(option.target3_confidence)}</span>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-center">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRecommendationColor(option.recommendation)}`}>
                    {option.recommendation}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-center">
                  <div className="text-lg font-bold text-white">{formatPercent(option.overall_confidence)}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-center">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold border ${getRiskBadgeColor(option.risk_level)}`}>
                    {option.risk_level}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <div className={`text-sm font-bold ${
                    option.max_profit_potential > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {option.max_profit_potential > 0 ? '+' : ''}{option.max_profit_potential.toFixed(1)}%
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {options.length === 0 && (
        <div className="text-center py-12">
          <div className="text-white/50 text-lg">No options data available</div>
          <div className="text-white/30 text-sm mt-2">Loading recommendations...</div>
        </div>
      )}
    </div>
  );
}

export default OptionsTable;
