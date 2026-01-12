import React, { useState, useMemo } from 'react';
import { TrendingUp, DollarSign, Target, Calendar, Filter } from 'lucide-react';

function OptionsTable({ options, onRowClick }) {
  const [filters, setFilters] = useState({
    symbol: '',
    type: 'ALL',
    expiry: 'ALL',
    risk: 'ALL',
    minConfidence: 0
  });
  const [showFilters, setShowFilters] = useState(false);

  // Get unique values for filters
  const uniqueSymbols = useMemo(() => {
    return [...new Set(options.map(o => o.symbol))].sort();
  }, [options]);

  const uniqueExpiries = useMemo(() => {
    return [...new Set(options.map(o => o.expiration_date))].sort();
  }, [options]);

  // Filter options based on selected filters
  const filteredOptions = useMemo(() => {
    return options.filter(option => {
      if (filters.symbol && option.symbol !== filters.symbol) return false;
      if (filters.type !== 'ALL' && option.option_type !== filters.type) return false;
      if (filters.expiry !== 'ALL' && option.expiration_date !== filters.expiry) return false;
      if (filters.risk !== 'ALL' && option.risk_level !== filters.risk) return false;
      if (option.overall_confidence < filters.minConfidence) return false;
      return true;
    });
  }, [options, filters]);

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
      {/* Filter Controls */}
      <div className="border-b border-white/10 p-4">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-white/70 hover:text-white transition-colors"
        >
          <Filter size={18} />
          <span className="text-sm font-semibold">
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </span>
          {filteredOptions.length !== options.length && (
            <span className="ml-2 px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded-full">
              {filteredOptions.length} of {options.length}
            </span>
          )}
        </button>

        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Symbol Filter */}
            <div>
              <label className="block text-xs text-white/50 mb-1">Symbol</label>
              <select
                value={filters.symbol}
                onChange={(e) => setFilters({ ...filters, symbol: e.target.value })}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ color: 'white' }}
              >
                <option value="" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>All Symbols</option>
                {uniqueSymbols.map(sym => (
                  <option key={sym} value={sym} style={{ backgroundColor: '#1a1a2e', color: 'white' }}>{sym}</option>
                ))}
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-xs text-white/50 mb-1">Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ color: 'white' }}
              >
                <option value="ALL" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>All Types</option>
                <option value="CALL" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>CALL</option>
                <option value="PUT" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>PUT</option>
              </select>
            </div>

            {/* Expiry Filter */}
            <div>
              <label className="block text-xs text-white/50 mb-1">Expiry Date</label>
              <select
                value={filters.expiry}
                onChange={(e) => setFilters({ ...filters, expiry: e.target.value })}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ color: 'white' }}
              >
                <option value="ALL" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>All Dates</option>
                {uniqueExpiries.map(exp => (
                  <option key={exp} value={exp} style={{ backgroundColor: '#1a1a2e', color: 'white' }}>{exp}</option>
                ))}
              </select>
            </div>

            {/* Risk Filter */}
            <div>
              <label className="block text-xs text-white/50 mb-1">Risk Level</label>
              <select
                value={filters.risk}
                onChange={(e) => setFilters({ ...filters, risk: e.target.value })}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ color: 'white' }}
              >
                <option value="ALL" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>All Risks</option>
                <option value="LOW" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>LOW</option>
                <option value="MEDIUM" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>MEDIUM</option>
                <option value="HIGH" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>HIGH</option>
              </select>
            </div>

            {/* Confidence Filter */}
            <div>
              <label className="block text-xs text-white/50 mb-1">Min Confidence</label>
              <select
                value={filters.minConfidence}
                onChange={(e) => setFilters({ ...filters, minConfidence: parseFloat(e.target.value) })}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ color: 'white' }}
              >
                <option value="0" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>Any</option>
                <option value="0.5" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>≥50%</option>
                <option value="0.6" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>≥60%</option>
                <option value="0.7" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>≥70%</option>
                <option value="0.8" style={{ backgroundColor: '#1a1a2e', color: 'white' }}>≥80%</option>
              </select>
            </div>
          </div>
        )}
      </div>

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
            {filteredOptions.map((option, index) => (
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

      {filteredOptions.length === 0 && options.length > 0 && (
        <div className="text-center py-12">
          <div className="text-white/50 text-lg">No options match the selected filters</div>
          <div className="text-white/30 text-sm mt-2">Try adjusting your filter criteria</div>
        </div>
      )}
      
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
