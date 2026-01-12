import React, { useState } from 'react';
import { X, TrendingUp, TrendingDown, DollarSign, Calculator } from 'lucide-react';

export default function OrderPanel({ option, onClose, onSubmit }) {
  const [orderType, setOrderType] = useState('buy'); // buy or sell
  const [quantity, setQuantity] = useState(1);
  const [price, setPrice] = useState(option?.entry_price || 0);
  const [orderMode, setOrderMode] = useState('market'); // market or limit

  if (!option) return null;

  const calculateTotal = () => {
    return (price * quantity * 100).toFixed(2); // Options contracts are typically 100 shares
  };

  const handleSubmit = () => {
    const order = {
      symbol: option.symbol,
      strike: option.strike,
      expiry: option.expiry,
      option_type: option.option_type,
      order_type: orderType,
      quantity,
      price: orderMode === 'market' ? option.entry_price : price,
      order_mode: orderMode,
      total: calculateTotal()
    };
    onSubmit(order);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-[#1a1f2e] border border-gray-800 rounded-xl w-full max-w-lg m-4 shadow-2xl">
        {/* Header */}
        <div className="border-b border-gray-800 p-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Place Order</h3>
            <p className="text-sm text-gray-400 mt-1">
              {option.symbol} ${option.strike} {option.option_type.toUpperCase()} - {option.expiry}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Buy/Sell Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setOrderType('buy')}
              className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
                orderType === 'buy'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              BUY
            </button>
            <button
              onClick={() => setOrderType('sell')}
              className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
                orderType === 'sell'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <TrendingDown className="w-4 h-4 inline mr-2" />
              SELL
            </button>
          </div>

          {/* Market/Limit Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setOrderMode('market')}
              className={`flex-1 py-2 rounded-lg font-medium text-sm transition-colors ${
                orderMode === 'market'
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Market
            </button>
            <button
              onClick={() => setOrderMode('limit')}
              className={`flex-1 py-2 rounded-lg font-medium text-sm transition-colors ${
                orderMode === 'limit'
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Limit
            </button>
          </div>

          {/* Quantity Input */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Quantity (Contracts)
            </label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Price Input (for limit orders) */}
          {orderMode === 'limit' && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Limit Price
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-3.5 w-5 h-5 text-gray-500" />
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={price}
                  onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                  className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {/* Order Summary */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Market Price:</span>
              <span className="text-white font-semibold">${option.entry_price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Quantity:</span>
              <span className="text-white font-semibold">{quantity} contracts</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Price per Contract:</span>
              <span className="text-white font-semibold">
                ${(orderMode === 'market' ? option.entry_price : price).toFixed(2)}
              </span>
            </div>
            <div className="border-t border-gray-800 pt-2 mt-2">
              <div className="flex justify-between">
                <span className="text-gray-300 font-semibold">Total:</span>
                <span className="text-white font-bold text-lg">${calculateTotal()}</span>
              </div>
            </div>
          </div>

          {/* Confidence Display */}
          {option.overall_confidence && (
            <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-400 text-sm">
                <Calculator className="w-4 h-4" />
                <span>AI Confidence: {(option.overall_confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-800 p-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
              orderType === 'buy'
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            {orderType === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
          </button>
        </div>
      </div>
    </div>
  );
}
