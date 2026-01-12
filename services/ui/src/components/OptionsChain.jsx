import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';
import axios from 'axios';

export default function OptionsChain({ symbol, onSelectOption }) {
  const [optionsData, setOptionsData] = useState([]);
  const [selectedExpiry, setSelectedExpiry] = useState('');
  const [loading, setLoading] = useState(false);
  const [expiryDates, setExpiryDates] = useState([]);

  useEffect(() => {
    if (symbol) {
      loadOptionsChain();
    }
  }, [symbol]);

  const loadOptionsChain = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/options/chain/${symbol}`);
      const data = response.data;
      
      // Extract unique expiry dates
      const expiries = [...new Set(data.map(opt => opt.expiry))].sort();
      setExpiryDates(expiries);
      setSelectedExpiry(expiries[0] || '');
      setOptionsData(data);
    } catch (error) {
      console.error('Error loading options chain:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOptions = optionsData.filter(
    opt => opt.expiry === selectedExpiry
  );

  const strikes = [...new Set(filteredOptions.map(opt => opt.strike))].sort((a, b) => a - b);

  const getOptionByType = (strike, type) => {
    return filteredOptions.find(opt => opt.strike === strike && opt.option_type === type);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-[#1a1f2e] border-b border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">{symbol} Options Chain</h2>
            <p className="text-sm text-gray-400 mt-1">Select strike and type to trade</p>
          </div>
          
          <select
            value={selectedExpiry}
            onChange={(e) => setSelectedExpiry(e.target.value)}
            className="bg-gray-900 border border-gray-700 text-white rounded-lg px-4 py-2"
          >
            {expiryDates.map(date => (
              <option key={date} value={date}>{date}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Options Chain Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading options chain...</div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-[#1a1f2e] border-b border-gray-800">
              <tr>
                {/* Calls Header */}
                <th className="text-left p-3 text-xs text-gray-400 font-semibold">OI</th>
                <th className="text-left p-3 text-xs text-gray-400 font-semibold">Volume</th>
                <th className="text-left p-3 text-xs text-gray-400 font-semibold">LTP</th>
                <th className="text-left p-3 text-xs text-gray-400 font-semibold">Change</th>
                
                {/* Strike */}
                <th className="text-center p-3 text-xs text-white font-bold bg-gray-800">STRIKE</th>
                
                {/* Puts Header */}
                <th className="text-right p-3 text-xs text-gray-400 font-semibold">Change</th>
                <th className="text-right p-3 text-xs text-gray-400 font-semibold">LTP</th>
                <th className="text-right p-3 text-xs text-gray-400 font-semibold">Volume</th>
                <th className="text-right p-3 text-xs text-gray-400 font-semibold">OI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {strikes.map((strike) => {
                const callOption = getOptionByType(strike, 'call');
                const putOption = getOptionByType(strike, 'put');
                
                return (
                  <tr key={strike} className="hover:bg-gray-900/30">
                    {/* Call Side */}
                    <td
                      onClick={() => callOption && onSelectOption(callOption)}
                      className="p-3 text-sm text-gray-300 cursor-pointer hover:bg-blue-900/20"
                    >
                      {callOption?.open_interest || '-'}
                    </td>
                    <td className="p-3 text-sm text-gray-300">
                      {callOption?.volume || '-'}
                    </td>
                    <td className="p-3 text-sm font-semibold text-white">
                      {callOption?.entry_price ? `$${callOption.entry_price.toFixed(2)}` : '-'}
                    </td>
                    <td className={`p-3 text-sm ${
                      (callOption?.change || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {callOption?.change ? `${callOption.change >= 0 ? '+' : ''}${callOption.change.toFixed(2)}%` : '-'}
                    </td>
                    
                    {/* Strike Price */}
                    <td className="p-3 text-center text-sm font-bold text-white bg-gray-800/50">
                      ${strike.toFixed(2)}
                    </td>
                    
                    {/* Put Side */}
                    <td className={`p-3 text-sm text-right ${
                      (putOption?.change || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {putOption?.change ? `${putOption.change >= 0 ? '+' : ''}${putOption.change.toFixed(2)}%` : '-'}
                    </td>
                    <td className="p-3 text-sm font-semibold text-white text-right">
                      {putOption?.entry_price ? `$${putOption.entry_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="p-3 text-sm text-gray-300 text-right">
                      {putOption?.volume || '-'}
                    </td>
                    <td
                      onClick={() => putOption && onSelectOption(putOption)}
                      className="p-3 text-sm text-gray-300 text-right cursor-pointer hover:bg-red-900/20"
                    >
                      {putOption?.open_interest || '-'}
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
