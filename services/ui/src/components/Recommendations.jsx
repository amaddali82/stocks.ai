import React, { useState } from 'react';
import { Calendar, DollarSign, Target, X, BarChart3, TrendingUp, AlertCircle } from 'lucide-react';

export default function Recommendations({ highConfidence, mediumConfidence, loading, onSymbolSelect, onRefresh }) {
  const [activeTab, setActiveTab] = useState('high');
  const [sortBy, setSortBy] = useState('confidence');
  const [selectedOption, setSelectedOption] = useState(null);

  // Calculate profit metrics for each option
  const calculateProfitMetrics = (option) => {
    const entryPrice = option.entry_price || option.current_price || 0;
    const target1 = option.target_price_1 || option.target1 || 0;
    const target2 = option.target_price_2 || option.target2 || 0;
    const target3 = option.target_price_3 || option.target3 || 0;
    
    // Profit per contract (100 shares)
    const profit1 = (target1 - entryPrice) * 100;
    const profit2 = (target2 - entryPrice) * 100;
    const profit3 = (target3 - entryPrice) * 100;
    
    // Risk-reward ratio (Target 1)
    const riskReward = entryPrice > 0 ? (target1 - entryPrice) / entryPrice : 0;
    
    // Capital required (per contract)
    const capitalRequired = entryPrice * 100;
    
    // Expected value (probability-weighted profit for Target 1)
    const target1Confidence = option.target_1_confidence || option.target1_confidence || 0;
    const expectedValue = profit1 * target1Confidence;
    
    return {
      profit1, profit2, profit3,
      riskReward,
      capitalRequired,
      expectedValue,
      entryPrice,
      isLowCapital: entryPrice <= 5.0
    };
  };

  const allOptions = [...highConfidence, ...mediumConfidence].map(opt => ({
    ...opt,
    metrics: calculateProfitMetrics(opt)
  }));
  
  const displayOptions = activeTab === 'high' 
    ? allOptions.filter(opt => (opt.overall_confidence || 0) >= 0.8)
    : activeTab === 'medium' 
    ? allOptions.filter(opt => (opt.overall_confidence || 0) >= 0.6 && (opt.overall_confidence || 0) < 0.8)
    : allOptions;

  const sortedOptions = [...displayOptions].sort((a, b) => {
    if (sortBy === 'confidence') return b.overall_confidence - a.overall_confidence;
    if (sortBy === 'expiry') return new Date(a.expiry) - new Date(b.expiry);
    if (sortBy === 'profit') return b.metrics.expectedValue - a.metrics.expectedValue;
    if (sortBy === 'capital') return a.metrics.capitalRequired - b.metrics.capitalRequired;
    return 0;
  });

  const handleRowClick = (option) => {
    setSelectedOption(option);
  };

  const closeModal = () => {
    setSelectedOption(null);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading recommendations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-6 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Options Recommendations</h2>
            <p className="text-sm text-gray-600 mt-1">AI-powered trading recommendations with confidence scores</p>
          </div>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Tabs and Sort */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('high')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'high'
                  ? 'bg-white text-blue-600 shadow-md'
                  : 'text-gray-600 hover:bg-white/50'
              }`}
            >
              High Confidence ({highConfidence.length})
            </button>
            <button
              onClick={() => setActiveTab('medium')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'medium'
                  ? 'bg-white text-blue-600 shadow-md'
                  : 'text-gray-600 hover:bg-white/50'
              }`}
            >
              Medium ({mediumConfidence.length})
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'all'
                  ? 'bg-white text-blue-600 shadow-md'
                  : 'text-gray-600 hover:bg-white/50'
              }`}
            >
              All ({allOptions.length})
            </button>
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option value="confidence">Sort by Confidence</option>
            <option value="expiry">Sort by Expiry</option>
            <option value="profit">Sort by Expected Profit</option>
            <option value="capital">Sort by Capital Required (Low to High)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {sortedOptions.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No recommendations available</p>
            </div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left p-4 text-xs font-semibold text-gray-600">Symbol</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-600">Type</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Strike</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Entry Price</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Target 1</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Target 2</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Target 3</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Capital Needed</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Target 1 Profit</th>
                <th className="text-center p-4 text-xs font-semibold text-gray-600">Risk:Reward</th>
                <th className="text-center p-4 text-xs font-semibold text-gray-600">Win Probability</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-600">Days to Expiry</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-600">Expected Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedOptions.map((option, index) => (
                <tr
                  key={index}
                  onClick={() => handleRowClick(option)}
                  className="hover:bg-blue-50 cursor-pointer transition-colors"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div>
                        <p className="font-semibold text-gray-900">{option.symbol}</p>
                        <p className="text-xs text-gray-500">{option.company || 'N/A'}</p>
                      </div>
                      {option.metrics.isLowCapital && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
                          Low Capital
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      option.option_type === 'CALL'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {option.option_type || 'CALL'}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-bold text-gray-900">${(option.strike_price || option.strike || 0).toFixed(2)}</p>
                    <p className="text-xs text-gray-500">strike</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-bold text-gray-900">${option.metrics.entryPrice.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">per share</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-semibold text-green-600">${(option.target_price_1 || option.target1 || 0).toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{((option.target_1_confidence || option.target1_confidence || 0) * 100).toFixed(0)}%</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-semibold text-green-600">${(option.target_price_2 || option.target2 || 0).toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{((option.target_2_confidence || option.target2_confidence || 0) * 100).toFixed(0)}%</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-semibold text-green-600">${(option.target_price_3 || option.target3 || 0).toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{((option.target_3_confidence || option.target3_confidence || 0) * 100).toFixed(0)}%</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-semibold text-blue-600">${option.metrics.capitalRequired.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">per contract</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-bold text-green-600">${option.metrics.profit1.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">
                      {option.metrics.profit1 > 0 ? `+${((option.metrics.profit1 / option.metrics.capitalRequired) * 100).toFixed(0)}%` : '0%'}
                    </p>
                  </td>
                  <td className="p-4 text-center">
                    <div className={`px-3 py-1 rounded-full text-xs font-bold inline-block ${
                      option.metrics.riskReward >= 2
                        ? 'bg-green-100 text-green-700'
                        : option.metrics.riskReward >= 1
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      1:{option.metrics.riskReward.toFixed(1)}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center justify-center">
                      <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                        (option.overall_confidence || 0) >= 0.8
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {((option.overall_confidence || 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="text-gray-700">{option.days_to_expiry || 'N/A'} days</p>
                    <p className="text-xs text-gray-500">{option.expiry || 'N/A'}</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-bold text-purple-600">${option.metrics.expectedValue.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">probability-weighted</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Card View Modal */}
      {selectedOption && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-2xl font-bold">{selectedOption.symbol}</h3>
                    <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                      selectedOption.option_type === 'CALL'
                        ? 'bg-blue-400 text-white'
                        : 'bg-red-400 text-white'
                    }`}>
                      {selectedOption.option_type || 'CALL'}
                    </span>
                  </div>
                  <p className="text-blue-100">{selectedOption.company || 'Company Name'}</p>
                </div>
                <button
                  onClick={closeModal}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Capital & Profit Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <DollarSign className="w-6 h-6 text-blue-600" />
                    <p className="text-sm text-gray-600 font-medium">Capital Required</p>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">
                    ${selectedOption.metrics.capitalRequired.toFixed(0)}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">per contract (100 shares)</p>
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <p className="text-xs text-gray-600">Entry: ${selectedOption.metrics.entryPrice.toFixed(2)} × 100</p>
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                    <p className="text-sm text-gray-600 font-medium">Expected Profit (T1)</p>
                  </div>
                  <p className="text-3xl font-bold text-green-700">
                    ${selectedOption.metrics.profit1.toFixed(0)}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    +{((selectedOption.metrics.profit1 / selectedOption.metrics.capitalRequired) * 100).toFixed(0)}% return
                  </p>
                  <div className="mt-3 pt-3 border-t border-green-200">
                    <p className="text-xs text-gray-600">
                      {((selectedOption.target_1_confidence || selectedOption.target1_confidence || 0) * 100).toFixed(0)}% probability in {selectedOption.days_to_expiry || 'N/A'} days
                    </p>
                  </div>
                </div>
              </div>

              {/* Risk-Reward Ratio */}
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-2 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      Risk-Reward Ratio
                    </p>
                    <p className="text-4xl font-bold text-gray-900">
                      1:{selectedOption.metrics.riskReward.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600 mb-2">Expected Value</p>
                    <p className="text-2xl font-bold text-purple-600">
                      ${selectedOption.metrics.expectedValue.toFixed(0)}
                    </p>
                    <p className="text-xs text-gray-500">probability-weighted</p>
                  </div>
                </div>
              </div>

              {/* Confidence Score */}
              <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Overall Win Probability</p>
                  <p className="text-5xl font-bold text-gray-900">
                    {((selectedOption.overall_confidence || 0) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-2">chance to hit Target 1 in {selectedOption.days_to_expiry || 'N/A'} days</p>
                </div>
              </div>

              {/* Price Information */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Strike Price</p>
                  <p className="text-xl font-bold text-gray-900">${selectedOption.strike?.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Entry Price</p>
                  <p className="text-xl font-bold text-blue-600">${selectedOption.entry_price?.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Current Price</p>
                  <p className="text-xl font-bold text-gray-900">${selectedOption.current_price?.toFixed(2)}</p>
                </div>
              </div>

              {/* Target Prices with Profit */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  Profit Targets
                </h4>
                <div className="space-y-3">
                  <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-700">Target 1</span>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        ((selectedOption.target_1_confidence || selectedOption.target1_confidence || 0) >= 0.8)
                          ? 'bg-green-200 text-green-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {((selectedOption.target_1_confidence || selectedOption.target1_confidence || 0) * 100).toFixed(0)}% probability
                      </span>
                    </div>
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-2xl font-bold text-green-700">${selectedOption.metrics.profit1.toFixed(0)}</p>
                        <p className="text-xs text-gray-600">profit per contract</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-900">${selectedOption.target_price_1?.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">target price</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-700">Target 2</span>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        ((selectedOption.target_2_confidence || selectedOption.target2_confidence || 0) >= 0.8)
                          ? 'bg-green-200 text-green-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {((selectedOption.target_2_confidence || selectedOption.target2_confidence || 0) * 100).toFixed(0)}% probability
                      </span>
                    </div>
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-2xl font-bold text-green-700">${selectedOption.metrics.profit2.toFixed(0)}</p>
                        <p className="text-xs text-gray-600">profit per contract</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-900">${selectedOption.target_price_2?.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">target price</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-700">Target 3</span>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        ((selectedOption.target_3_confidence || selectedOption.target3_confidence || 0) >= 0.8)
                          ? 'bg-green-200 text-green-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {((selectedOption.target_3_confidence || selectedOption.target3_confidence || 0) * 100).toFixed(0)}% probability
                      </span>
                    </div>
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-2xl font-bold text-green-700">${selectedOption.metrics.profit3.toFixed(0)}</p>
                        <p className="text-xs text-gray-600">profit per contract</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-900">${selectedOption.target_price_3?.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">target price</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Calendar className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="text-xs text-gray-600">Expiry Date</p>
                    <p className="text-sm font-semibold text-gray-900">{selectedOption.expiry}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <DollarSign className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="text-xs text-gray-600">Data Source</p>
                    <p className="text-sm font-semibold text-gray-900">{selectedOption.data_source || 'Verified'}</p>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => {
                  onSymbolSelect(selectedOption.symbol);
                  closeModal();
                }}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
              >
                View Options Chain
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
