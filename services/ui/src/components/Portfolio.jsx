import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Activity, X } from 'lucide-react';

export default function Portfolio({ positions = [], onClose }) {
  const [totalPnL, setTotalPnL] = useState(0);
  const [totalValue, setTotalValue] = useState(0);

  useEffect(() => {
    let pnl = 0;
    let value = 0;
    
    positions.forEach(pos => {
      const currentValue = pos.quantity * pos.current_price * 100;
      const costBasis = pos.quantity * pos.entry_price * 100;
      pnl += (currentValue - costBasis);
      value += currentValue;
    });
    
    setTotalPnL(pnl);
    setTotalValue(value);
  }, [positions]);

  const calculatePnL = (position) => {
    const currentValue = position.quantity * position.current_price * 100;
    const costBasis = position.quantity * position.entry_price * 100;
    return currentValue - costBasis;
  };

  const calculatePnLPercent = (position) => {
    const pnl = calculatePnL(position);
    const costBasis = position.quantity * position.entry_price * 100;
    return (pnl / costBasis) * 100;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-[#1a1f2e] border-b border-gray-800 p-6">
        <h2 className="text-2xl font-bold text-white mb-4">Portfolio</h2>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-900/50 rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-1">Total Value</p>
            <p className="text-2xl font-bold text-white">${totalValue.toFixed(2)}</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-1">Total P&L</p>
            <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
            </p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-1">Open Positions</p>
            <p className="text-2xl font-bold text-white">{positions.length}</p>
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="flex-1 overflow-auto">
        {positions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Activity className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg">No open positions</p>
            <p className="text-sm mt-2">Your positions will appear here</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-[#1a1f2e] border-b border-gray-800">
              <tr>
                <th className="text-left p-4 text-xs text-gray-400 font-semibold">Symbol</th>
                <th className="text-left p-4 text-xs text-gray-400 font-semibold">Type</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">Strike</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">Qty</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">Entry</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">Current</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">P&L</th>
                <th className="text-right p-4 text-xs text-gray-400 font-semibold">P&L %</th>
                <th className="text-center p-4 text-xs text-gray-400 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {positions.map((position, idx) => {
                const pnl = calculatePnL(position);
                const pnlPercent = calculatePnLPercent(position);
                
                return (
                  <tr key={idx} className="hover:bg-gray-900/30">
                    <td className="p-4">
                      <div>
                        <p className="font-semibold text-white">{position.symbol}</p>
                        <p className="text-xs text-gray-500">{position.expiry}</p>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        position.option_type === 'call'
                          ? 'bg-blue-900/30 text-blue-400'
                          : 'bg-red-900/30 text-red-400'
                      }`}>
                        {position.option_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4 text-right text-gray-300">${position.strike.toFixed(2)}</td>
                    <td className="p-4 text-right text-gray-300">{position.quantity}</td>
                    <td className="p-4 text-right text-gray-300">${position.entry_price.toFixed(2)}</td>
                    <td className="p-4 text-right font-semibold text-white">
                      ${position.current_price.toFixed(2)}
                    </td>
                    <td className={`p-4 text-right font-semibold ${
                      pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                    </td>
                    <td className={`p-4 text-right font-semibold ${
                      pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      <div className="flex items-center justify-end gap-1">
                        {pnlPercent >= 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => onClose(position)}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Close
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
