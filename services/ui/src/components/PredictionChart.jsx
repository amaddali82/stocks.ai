import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const PredictionChart = ({ recommendations }) => {
  const chartData = recommendations.map(rec => ({
    symbol: rec.symbol,
    confidence: (rec.confidence * 100).toFixed(0),
    action: rec.action
  }));

  const getBarColor = (action) => {
    switch (action.toUpperCase()) {
      case 'BUY': return '#10B981';
      case 'SELL': return '#EF4444';
      case 'HOLD': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-6 animate-slide-in">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <svg className="w-6 h-6 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Confidence Levels
      </h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="symbol" stroke="#6b7280" />
          <YAxis stroke="#6b7280" domain={[0, 100]} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            formatter={(value) => [`${value}%`, 'Confidence']}
          />
          <Legend />
          <Bar dataKey="confidence" name="Confidence" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.action)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PredictionChart;
