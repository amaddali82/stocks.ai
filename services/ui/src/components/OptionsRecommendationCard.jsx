import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Calendar, Target, Award } from 'lucide-react';

function OptionsRecommendationCard({ option }) {
  const getRecommendationColor = (rec) => {
    if (rec.includes('STRONG BUY')) return 'from-green-500 to-emerald-600';
    if (rec.includes('BUY')) return 'from-green-400 to-green-500';
    if (rec.includes('HOLD')) return 'from-yellow-400 to-yellow-500';
    if (rec.includes('AVOID')) return 'from-red-500 to-red-600';
    return 'from-gray-400 to-gray-500';
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LOW': return 'text-green-400 bg-green-500/20';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/20';
      case 'HIGH': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value) => {
    return (value * 100).toFixed(0) + '%';
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-[1.02]">
      {/* Header */}
      <div className={`bg-gradient-to-r ${getRecommendationColor(option.recommendation)} p-6`}>
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-2xl font-bold text-white">{option.symbol}</h3>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                option.option_type === 'CALL' ? 'bg-green-500/30 text-green-200' : 'bg-red-500/30 text-red-200'
              }`}>
                {option.option_type}
              </span>
            </div>
            <p className="text-white/80 text-sm mt-1">{option.company}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">{formatPercent(option.overall_confidence)}</div>
            <div className="text-white/70 text-xs">Confidence</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-4">
        {/* Recommendation and Risk */}
        <div className="flex gap-3">
          <div className="flex-1 bg-white/5 rounded-xl p-4">
            <div className="text-white/60 text-xs mb-1">Recommendation</div>
            <div className="text-xl font-bold text-white">{option.recommendation}</div>
          </div>
          <div className="flex-1 bg-white/5 rounded-xl p-4">
            <div className="text-white/60 text-xs mb-1">Risk Level</div>
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${getRiskColor(option.risk_level)}`}>
              {option.risk_level}
            </span>
          </div>
        </div>

        {/* Option Details */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-xl p-3">
            <div className="text-white/60 text-xs mb-1">Entry Price</div>
            <div className="text-lg font-bold text-white">{formatCurrency(option.entry_price)}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3">
            <div className="text-white/60 text-xs mb-1">Strike Price</div>
            <div className="text-lg font-bold text-white">{formatCurrency(option.strike_price)}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3">
            <div className="text-white/60 text-xs mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Expiration
            </div>
            <div className="text-sm font-medium text-white">{option.expiration_date}</div>
            <div className="text-xs text-white/50">{option.days_to_expiry} days</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3">
            <div className="text-white/60 text-xs mb-1">Breakeven</div>
            <div className="text-lg font-bold text-white">{formatCurrency(option.breakeven_price)}</div>
          </div>
        </div>

        {/* Price Targets */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-white/70 text-sm font-semibold">
            <Target className="w-4 h-4" />
            Price Targets
          </div>
          
          {/* Target 1 */}
          <div className="bg-gradient-to-r from-green-500/20 to-green-600/10 rounded-xl p-3 border border-green-500/30">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-green-400 text-xs font-semibold">TARGET 1 (Conservative)</div>
                <div className="text-2xl font-bold text-white mt-1">{formatCurrency(option.target1)}</div>
              </div>
              <div className="text-right">
                <div className="text-green-300 text-2xl font-bold">{formatPercent(option.target1_confidence)}</div>
                <div className="text-green-400/70 text-xs">Confidence</div>
              </div>
            </div>
          </div>

          {/* Target 2 */}
          <div className="bg-gradient-to-r from-blue-500/20 to-blue-600/10 rounded-xl p-3 border border-blue-500/30">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-blue-400 text-xs font-semibold">TARGET 2 (Moderate)</div>
                <div className="text-xl font-bold text-white mt-1">{formatCurrency(option.target2)}</div>
              </div>
              <div className="text-right">
                <div className="text-blue-300 text-xl font-bold">{formatPercent(option.target2_confidence)}</div>
                <div className="text-blue-400/70 text-xs">Confidence</div>
              </div>
            </div>
          </div>

          {/* Target 3 */}
          <div className="bg-gradient-to-r from-purple-500/20 to-purple-600/10 rounded-xl p-3 border border-purple-500/30">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-purple-400 text-xs font-semibold">TARGET 3 (Aggressive)</div>
                <div className="text-xl font-bold text-white mt-1">{formatCurrency(option.target3)}</div>
              </div>
              <div className="text-right">
                <div className="text-purple-300 text-xl font-bold">{formatPercent(option.target3_confidence)}</div>
                <div className="text-purple-400/70 text-xs">Confidence</div>
              </div>
            </div>
          </div>
        </div>

        {/* Greeks and Metrics */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10">
          <div className="space-y-2">
            <div className="text-white/60 text-xs">Option Greeks</div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-white/70">Delta:</span>
                <span className="text-white font-medium">{option.delta.toFixed(4)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/70">IV:</span>
                <span className="text-white font-medium">{formatPercent(option.implied_volatility)}</span>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-white/60 text-xs">Market Data</div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-white/70">OI:</span>
                <span className="text-white font-medium">{option.open_interest.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/70">Volume:</span>
                <span className="text-white font-medium">{option.volume.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Max Profit Potential */}
        <div className="bg-gradient-to-r from-amber-500/20 to-orange-600/10 rounded-xl p-4 border border-amber-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-400" />
              <span className="text-amber-400 text-sm font-semibold">Max Profit Potential</span>
            </div>
            <div className="text-3xl font-bold text-amber-300">
              {option.max_profit_potential > 0 ? '+' : ''}{option.max_profit_potential.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OptionsRecommendationCard;
