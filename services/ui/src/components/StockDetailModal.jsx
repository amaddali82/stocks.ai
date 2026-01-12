import React from 'react';

function StockDetailModal({ stock, onClose, onViewOptions }) {
  if (!stock) return null;

  const getActionColor = (action) => {
    switch (action?.toUpperCase()) {
      case 'BUY': return 'text-green-400 bg-green-500/20 border-green-500/50';
      case 'SELL': return 'text-red-400 bg-red-500/20 border-red-500/50';
      case 'HOLD': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
    }
  };

  const priceChange = ((stock.targetPrice - stock.currentPrice) / stock.currentPrice * 100).toFixed(2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-white/10 animate-scale-in">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600/90 to-purple-600/90 backdrop-blur-xl px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-3xl font-bold text-white">{stock.symbol}</div>
            <span className={`px-4 py-2 rounded-lg text-lg font-bold border-2 ${getActionColor(stock.action)}`}>
              {stock.action}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Price Information */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="text-sm text-white/60 mb-1">Current Price</div>
              <div className="text-3xl font-bold text-white">${stock.currentPrice?.toFixed(2)}</div>
            </div>
            <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="text-sm text-white/60 mb-1">Target Price</div>
              <div className="text-3xl font-bold text-blue-400">${stock.targetPrice?.toFixed(2)}</div>
            </div>
            <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="text-sm text-white/60 mb-1">Expected Change</div>
              <div className={`text-3xl font-bold ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {priceChange >= 0 ? '+' : ''}{priceChange}%
              </div>
            </div>
          </div>

          {/* Confidence & Risk */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="text-sm text-white/60 mb-2">Confidence Level</div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl font-bold text-white">{(stock.confidence * 100).toFixed(0)}%</span>
                <span className="text-sm text-white/60">{stock.timeHorizon}</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${stock.confidence * 100}%` }}
                />
              </div>
            </div>
            <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
              <div className="text-sm text-white/60 mb-2">Risk Assessment</div>
              <div className="text-2xl font-bold text-white capitalize mb-2">{stock.riskLevel}</div>
              <div className="text-sm text-white/70">{stock.prediction}</div>
            </div>
          </div>

          {/* Model Signals */}
          <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
            <div className="text-lg font-semibold text-white mb-4">AI Model Signals</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white/70">LSTM Model</span>
                  <span className="text-lg font-bold text-white">{(stock.modelSignals?.lstm * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                    style={{ width: `${stock.modelSignals?.lstm * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white/70">Transformer</span>
                  <span className="text-lg font-bold text-white">{(stock.modelSignals?.transformer * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                    style={{ width: `${stock.modelSignals?.transformer * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white/70">Sentiment</span>
                  <span className="text-lg font-bold text-white">{(stock.modelSignals?.sentiment * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                    style={{ width: `${stock.modelSignals?.sentiment * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
            <div className="text-lg font-semibold text-white mb-4">Technical Indicators</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-sm text-white/60 mb-1">RSI</div>
                <div className={`text-2xl font-bold ${
                  stock.technicalIndicators?.rsi > 70 ? 'text-red-400' :
                  stock.technicalIndicators?.rsi < 30 ? 'text-green-400' :
                  'text-yellow-400'
                }`}>
                  {stock.technicalIndicators?.rsi?.toFixed(1)}
                </div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-sm text-white/60 mb-1">MACD</div>
                <div className={`text-xl font-bold capitalize ${
                  stock.technicalIndicators?.macd?.includes('bullish') ? 'text-green-400' :
                  stock.technicalIndicators?.macd?.includes('bearish') ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {stock.technicalIndicators?.macd}
                </div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-sm text-white/60 mb-1">Volume</div>
                <div className="text-xl font-bold text-white capitalize">
                  {stock.technicalIndicators?.volume}
                </div>
              </div>
            </div>
          </div>

          {/* Reasoning */}
          <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
            <div className="text-lg font-semibold text-white mb-2">Analysis & Reasoning</div>
            <p className="text-white/80 leading-relaxed">{stock.reasoning}</p>
          </div>

          {/* Last Update */}
          {stock.lastUpdate && (
            <div className="text-center text-sm text-white/50">
              Last updated: {new Date(stock.lastUpdate).toLocaleString()}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4">
            <button
              onClick={() => onViewOptions(stock.symbol)}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              View Options Chain
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-white/10 hover:bg-white/20 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 border border-white/20"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StockDetailModal;
