import React from 'react';

const RecommendationCard = ({ recommendation, index }) => {
  const { symbol, action, confidence, targetPrice, currentPrice, prediction, 
          modelSignals, technicalIndicators, reasoning, riskLevel, timeHorizon } = recommendation;

  const getActionColor = (action) => {
    switch (action.toUpperCase()) {
      case 'BUY': return 'bg-green-100 text-green-800 border-green-300';
      case 'SELL': return 'bg-red-100 text-red-800 border-red-300';
      case 'HOLD': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getActionIcon = (action) => {
    switch (action.toUpperCase()) {
      case 'BUY': return '📈';
      case 'SELL': return '📉';
      case 'HOLD': return '⏸️';
      default: return '❓';
    }
  };

  const getRiskColor = (level) => {
    if (level.includes('low')) return 'text-green-600';
    if (level.includes('high')) return 'text-red-600';
    return 'text-yellow-600';
  };

  const priceChange = ((targetPrice - currentPrice) / currentPrice * 100).toFixed(2);

  return (
    <div 
      className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 animate-slide-in transform hover:-translate-y-1"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
            {symbol.charAt(0)}
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-800">{symbol}</h3>
            <p className="text-sm text-gray-500">{timeHorizon}</p>
          </div>
        </div>
        <div className={`px-4 py-2 rounded-full font-bold text-sm border-2 ${getActionColor(action)} flex items-center space-x-2`}>
          <span>{getActionIcon(action)}</span>
          <span>{action}</span>
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600 font-medium">Confidence</span>
          <span className="text-sm font-bold text-gray-800">{(confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${confidence * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
        <div>
          <div className="text-xs text-gray-500 mb-1">Current Price</div>
          <div className="text-lg font-bold text-gray-800">${currentPrice.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Target Price</div>
          <div className={`text-lg font-bold ${priceChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${targetPrice.toFixed(2)}
            <span className="text-sm ml-1">({priceChange > 0 ? '+' : ''}{priceChange}%)</span>
          </div>
        </div>
      </div>

      {/* Model Signals */}
      <div className="mb-4">
        <div className="text-sm font-semibold text-gray-700 mb-2">Model Signals</div>
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">LSTM</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-blue-500 h-1.5 rounded-full"
                  style={{ width: `${modelSignals.lstm * 100}%` }}
                ></div>
              </div>
              <span className="text-gray-800 font-medium w-10 text-right">{(modelSignals.lstm * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">Transformer</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-purple-500 h-1.5 rounded-full"
                  style={{ width: `${modelSignals.transformer * 100}%` }}
                ></div>
              </div>
              <span className="text-gray-800 font-medium w-10 text-right">{(modelSignals.transformer * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">Sentiment</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-green-500 h-1.5 rounded-full"
                  style={{ width: `${modelSignals.sentiment * 100}%` }}
                ></div>
              </div>
              <span className="text-gray-800 font-medium w-10 text-right">{(modelSignals.sentiment * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Technical Indicators */}
      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <div className="text-xs font-semibold text-gray-700 mb-2">Technical Indicators</div>
        <div className="flex justify-between text-xs">
          <div>
            <span className="text-gray-500">RSI: </span>
            <span className="font-medium text-gray-800">{technicalIndicators.rsi}</span>
          </div>
          <div>
            <span className="text-gray-500">MACD: </span>
            <span className="font-medium text-gray-800">{technicalIndicators.macd}</span>
          </div>
          <div>
            <span className="text-gray-500">Vol: </span>
            <span className="font-medium text-gray-800">{technicalIndicators.volume}</span>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-gray-700 mb-1">Analysis</div>
        <p className="text-xs text-gray-600 leading-relaxed">{reasoning}</p>
      </div>

      {/* Risk Level */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="text-xs text-gray-500">Risk Level</span>
        </div>
        <span className={`text-xs font-bold ${getRiskColor(riskLevel)} uppercase`}>
          {riskLevel}
        </span>
      </div>
    </div>
  );
};

export default RecommendationCard;
