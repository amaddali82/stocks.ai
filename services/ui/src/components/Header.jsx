import React from 'react';

const Header = ({ lastUpdate }) => {
  return (
    <div className="mb-8 animate-slide-in">
      <div className="bg-white rounded-2xl shadow-2xl p-8 backdrop-blur-lg bg-opacity-95">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Stocks.AI
              </span>
              <span className="ml-3 text-2xl">🚀</span>
            </h1>
            <p className="text-gray-600 text-lg">
              AI-Powered Trading Recommendations
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500 mb-1">Last Updated</div>
            <div className="text-lg font-semibold text-gray-700">
              {lastUpdate ? lastUpdate.toLocaleTimeString() : '--:--:--'}
            </div>
            <div className="flex items-center justify-end mt-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
              <span className="text-xs text-gray-600">Live</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
