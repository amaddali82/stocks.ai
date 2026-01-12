import React, { useState } from 'react';
import { 
  TrendingUp, TrendingDown, Star, Filter, RefreshCw, 
  AlertCircle, Target, Award, Clock, Shield 
} from 'lucide-react';

export default function Recommendations({ highConfidence, mediumConfidence, loading, onSymbolSelect, onRefresh }) {
  const [activeTab, setActiveTab] = useState('high'); // high, medium, all
  const [sortBy, setSortBy] = useState('confidence'); // confidence, expiry, profit

  const getDisplayOptions = () => {
    switch (activeTab) {
      case 'high':
        return highConfidence;
      case 'medium':
        return mediumConfidence;
      default:
        return [...highConfidence, ...mediumConfidence];
    }
  };

  const getSortedOptions = (options) => {
    const sorted = [...options];
    switch (sortBy) {
      case 'confidence':
        return sorted.sort((a, b) => b.overall_confidence - a.overall_confidence);
      case 'expiry':
        return sorted.sort((a, b) => a.days_to_expiry - b.days_to_expiry);
      case 'profit':
        return sorted.sort((a, b) => b.max_profit_potential - a.max_profit_potential);
      default:
        return sorted;
    }
  };

  const displayOptions = getSortedOptions(getDisplayOptions());

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.85) return 'text-emerald-400';
    if (confidence >= 0.80) return 'text-green-400';
    if (confidence >= 0.70) return 'text-yellow-400';
    return 'text-orange-400';
  };

  const getRecommendationColor = (rec) => {
    switch (rec) {
      case 'STRONG BUY':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'BUY':
        return 'bg-green-500/10 text-green-400 border-green-500/30';
      case 'HOLD':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0f1419]">
      {/* Header Section */}
      <div className="border-b border-gray-800 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Options Recommendations</h1>
            <p className="text-sm text-gray-400">AI-powered options trading recommendations with verified market data</p>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Tabs and Filters */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('high')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'high'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4" />
                High Confidence ({highConfidence.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('medium')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'medium'
                  ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Medium Confidence ({mediumConfidence.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'all'
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              All ({highConfidence.length + mediumConfidence.length})
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
            >
              <option value="confidence">Sort by Confidence</option>
              <option value="expiry">Sort by Expiry</option>
              <option value="profit">Sort by Profit Potential</option>
            </select>
          </div>
        </div>
      </div>

      {/* Options Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-400">Loading recommendations...</p>
            </div>
          </div>
        ) : displayOptions.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400">No recommendations available</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {displayOptions.map((option, index) => (
              <div
                key={index}
                onClick={() => onSymbolSelect(option.symbol)}
                className="bg-[#1a1f2e] border border-gray-800 rounded-xl p-5 hover:border-blue-500/50 transition-all cursor-pointer group"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-xl font-bold text-white">{option.symbol}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getRecommendationColor(option.recommendation)}`}>
                        {option.recommendation}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{option.company}</p>
                  </div>
                  <button className="p-1.5 hover:bg-gray-800 rounded-lg transition-colors">
                    <Star className="w-4 h-4 text-gray-500 hover:text-yellow-400" />
                  </button>
                </div>

                {/* Price Info */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">Current Price</p>
                    <p className="text-lg font-bold text-white">${option.current_price}</p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">Strike Price</p>
                    <p className="text-lg font-bold text-white">${option.strike_price}</p>
                  </div>
                </div>

                {/* Entry & Confidence */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Entry Price</p>
                    <p className="text-lg font-bold text-emerald-400">${option.entry_price}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-1">Confidence</p>
                    <p className={`text-lg font-bold ${getConfidenceColor(option.overall_confidence)}`}>
                      {(option.overall_confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Targets */}
                <div className="border-t border-gray-800 pt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Target 1 ({(option.target1_confidence * 100).toFixed(0)}%)</span>
                    <span className="text-green-400 font-semibold">${option.target1}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Target 2 ({(option.target2_confidence * 100).toFixed(0)}%)</span>
                    <span className="text-green-400 font-semibold">${option.target2}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Target 3 ({(option.target3_confidence * 100).toFixed(0)}%)</span>
                    <span className="text-green-400 font-semibold">${option.target3}</span>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-800 text-xs">
                  <div className="flex items-center gap-1 text-gray-400">
                    <Clock className="w-3 h-3" />
                    <span>{option.days_to_expiry}d to expiry</span>
                  </div>
                  <div className="flex items-center gap-1 text-gray-400">
                    <Shield className="w-3 h-3" />
                    <span>{option.data_source?.split(' ')[0]}</span>
                  </div>
                </div>

                {/* Profit Potential Badge */}
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Max Profit</span>
                    <span className="text-sm font-bold text-purple-400">
                      +{option.max_profit_potential?.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
