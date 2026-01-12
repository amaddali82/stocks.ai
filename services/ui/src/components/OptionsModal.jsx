import React, { useState, useEffect } from 'react';
import axios from 'axios';

function OptionsModal({ symbol, onClose }) {
  const [optionsData, setOptionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('calls');

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/options/${symbol}`, { timeout: 10000 });
        setOptionsData(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching options:', error);
        setLoading(false);
      }
    };

    fetchOptions();
  }, [symbol]);

  if (!symbol) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto border border-white/10 animate-scale-in">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-green-600/90 to-blue-600/90 backdrop-blur-xl px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-3xl font-bold text-white">{symbol} Options</div>
            {optionsData && (
              <div className="text-sm text-white/80">
                Current Price: ${optionsData.currentPrice}
              </div>
            )}
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
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-pulse-custom">
                <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
          ) : optionsData ? (
            <>
              {/* Info Bar */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
                  <div className="text-sm text-white/60">Current Price</div>
                  <div className="text-2xl font-bold text-white">${optionsData.currentPrice}</div>
                </div>
                <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
                  <div className="text-sm text-white/60">Expiration Date</div>
                  <div className="text-2xl font-bold text-white">{optionsData.expirationDate}</div>
                </div>
                <div className="bg-white/5 backdrop-blur-xl rounded-xl p-4 border border-white/10">
                  <div className="text-sm text-white/60">Available Expirations</div>
                  <div className="text-2xl font-bold text-white">{optionsData.totalExpirations}</div>
                </div>
              </div>

              {optionsData.dataSource === 'synthetic' && (
                <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 mb-4">
                  <p className="text-sm text-yellow-200">
                    📊 Showing synthetic options data based on current market prices
                  </p>
                </div>
              )}

              {/* Tabs */}
              <div className="flex space-x-2 mb-6 bg-white/5 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('calls')}
                  className={`flex-1 py-2 px-4 rounded-lg font-semibold transition-all duration-200 ${
                    activeTab === 'calls'
                      ? 'bg-green-600 text-white shadow-lg'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                >
                  Calls ({optionsData.calls?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('puts')}
                  className={`flex-1 py-2 px-4 rounded-lg font-semibold transition-all duration-200 ${
                    activeTab === 'puts'
                      ? 'bg-red-600 text-white shadow-lg'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                >
                  Puts ({optionsData.puts?.length || 0})
                </button>
              </div>

              {/* Options Table */}
              <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-white/10 border-b border-white/10">
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">Strike</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">Last</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">Bid</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">Ask</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">Volume</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">OI</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-white/70 uppercase">IV</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {(activeTab === 'calls' ? optionsData.calls : optionsData.puts)?.map((option, index) => (
                        <tr
                          key={index}
                          className={`hover:bg-white/10 transition-colors ${
                            Math.abs(option.strike - optionsData.currentPrice) < optionsData.currentPrice * 0.02
                              ? 'bg-blue-500/10'
                              : ''
                          }`}
                        >
                          <td className="px-4 py-3 font-bold text-white">${option.strike?.toFixed(2)}</td>
                          <td className="px-4 py-3 text-white">${option.lastPrice?.toFixed(2)}</td>
                          <td className="px-4 py-3 text-green-400">${option.bid?.toFixed(2)}</td>
                          <td className="px-4 py-3 text-red-400">${option.ask?.toFixed(2)}</td>
                          <td className="px-4 py-3 text-white/80">{option.volume?.toLocaleString()}</td>
                          <td className="px-4 py-3 text-white/80">{option.openInterest?.toLocaleString()}</td>
                          <td className="px-4 py-3 text-white/80">{(option.impliedVolatility * 100)?.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 text-sm text-white/50 text-center">
                OI = Open Interest | IV = Implied Volatility
              </div>
            </>
          ) : (
            <div className="text-center text-white/60 py-8">
              No options data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OptionsModal;
