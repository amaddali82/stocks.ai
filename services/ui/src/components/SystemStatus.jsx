import React from 'react';

const SystemStatus = ({ status }) => {
  const getStatusColor = (state) => {
    switch (state) {
      case 'online': return 'bg-green-500';
      case 'offline': return 'bg-red-500';
      default: return 'bg-yellow-500 animate-pulse';
    }
  };

  const getStatusText = (state) => {
    switch (state) {
      case 'online': return 'Online';
      case 'offline': return 'Offline';
      default: return 'Checking...';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-6 animate-slide-in">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        System Status
      </h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(status.prediction)}`}></div>
          <div>
            <div className="text-xs text-gray-500">Prediction Engine</div>
            <div className="text-sm font-medium">{getStatusText(status.prediction)}</div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(status.risk)}`}></div>
          <div>
            <div className="text-xs text-gray-500">Risk Management</div>
            <div className="text-sm font-medium">{getStatusText(status.risk)}</div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(status.data)}`}></div>
          <div>
            <div className="text-xs text-gray-500">Data Ingestion</div>
            <div className="text-sm font-medium">{getStatusText(status.data)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
