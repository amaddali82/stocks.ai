import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import SystemStatus from './components/SystemStatus';
import OptionsRecommendationCard from './components/OptionsRecommendationCard';
import OptionsTable from './components/OptionsTable';
import { TrendingUp, Target, BarChart3, Grid3x3 } from 'lucide-react';

function App() {
  const [options, setOptions] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    prediction: 'checking',
    risk: 'checking',
    data: 'checking',
    options: 'checking'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'cards'
  const [selectedOption, setSelectedOption] = useState(null);

  useEffect(() => {
    // Check system status
    checkSystemStatus();
    
    // Load options recommendations
    loadOptionsRecommendations();
    
    // Refresh every 60 seconds
    const interval = setInterval(() => {
      checkSystemStatus();
      loadOptionsRecommendations();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const checkSystemStatus = async () => {
    const status = {
      prediction: 'offline',
      risk: 'offline',
      data: 'offline',
      options: 'offline'
    };

    try {
      await axios.get('/api/data-api/health', { timeout: 2000 });
      status.data = 'online';
    } catch (e) {
      status.data = 'offline';
    }

    try {
      await axios.get('/api/risk/health', { timeout: 2000 });
      status.risk = 'online';
    } catch (e) {
      status.risk = 'offline';
    }

    try {
      await axios.get('/api/prediction/health', { timeout: 2000 });
      status.prediction = 'online';
    } catch (e) {
      status.prediction = 'offline';
    }

    try {
      await axios.get('/api/options/health', { timeout: 2000 });
      status.options = 'online';
    } catch (e) {
      status.options = 'offline';
    }

    setSystemStatus(status);
  };

  const loadOptionsRecommendations = async () => {
    try {
      setLoading(true);
      
      // Fetch all options recommendations using proxy
      const response = await axios.get('/api/options/api/predictions/best', { 
        timeout: 15000,
        params: { limit: 20 }
      });
      
      // Handle both array and object with predictions array
      const optionsData = response.data.predictions || response.data;
      
      setOptions(optionsData);
      setError(null);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (apiError) {
      console.error('Error fetching options data:', apiError);
      setError('Unable to load options data - Please ensure the options API service is running');
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadOptionsRecommendations();
    checkSystemStatus();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                <Target className="w-10 h-10 text-blue-400" />
                Options Recommendations
              </h1>
              <p className="text-white/60">
                AI-powered options predictions with multi-target analysis and confidence scoring
              </p>
            </div>
            <div className="flex items-center gap-4">
              {lastUpdate && (
                <div className="text-sm text-white/60">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
              )}
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Refresh Data
              </button>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className={`bg-white/5 backdrop-blur-xl rounded-xl p-4 border ${
            systemStatus.data === 'online' ? 'border-green-500/30' : 'border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-white/70 text-sm">Data API</span>
              <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                systemStatus.data === 'online' 
                  ? 'bg-green-500/20 text-green-300' 
                  : 'bg-red-500/20 text-red-300'
              }`}>
                {systemStatus.data}
              </span>
            </div>
          </div>
          
          <div className={`bg-white/5 backdrop-blur-xl rounded-xl p-4 border ${
            systemStatus.prediction === 'online' ? 'border-green-500/30' : 'border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-white/70 text-sm">Prediction Engine</span>
              <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                systemStatus.prediction === 'online' 
                  ? 'bg-green-500/20 text-green-300' 
                  : 'bg-red-500/20 text-red-300'
              }`}>
                {systemStatus.prediction}
              </span>
            </div>
          </div>
          
          <div className={`bg-white/5 backdrop-blur-xl rounded-xl p-4 border ${
            systemStatus.risk === 'online' ? 'border-green-500/30' : 'border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-white/70 text-sm">Risk Management</span>
              <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                systemStatus.risk === 'online' 
                  ? 'bg-green-500/20 text-green-300' 
                  : 'bg-red-500/20 text-red-300'
              }`}>
                {systemStatus.risk}
              </span>
            </div>
          </div>
          
          <div className={`bg-white/5 backdrop-blur-xl rounded-xl p-4 border ${
            systemStatus.options === 'online' ? 'border-green-500/30' : 'border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-white/70 text-sm">Options API</span>
              <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                systemStatus.options === 'online' 
                  ? 'bg-green-500/20 text-green-300' 
                  : 'bg-red-500/20 text-red-300'
              }`}>
                {systemStatus.options}
              </span>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500/30 backdrop-blur-xl p-4 mb-6 rounded-xl animate-slide-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* View Mode Toggle and Stats */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <div className="text-white/70">
              <span className="font-semibold text-white">{options.length}</span> recommendations available
            </div>
          </div>
          
          <div className="bg-white/5 backdrop-blur-xl rounded-lg p-1 border border-white/10">
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 flex items-center gap-2 ${
                viewMode === 'table'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-white/60 hover:text-white hover:bg-white/10'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Table View
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 flex items-center gap-2 ${
                viewMode === 'cards'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-white/60 hover:text-white hover:bg-white/10'
              }`}
            >
              <Grid3x3 className="w-4 h-4" />
              Card View
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin">
              <Target className="w-16 h-16 text-blue-400" />
            </div>
          </div>
        ) : (
          <>
            {viewMode === 'table' ? (
              <OptionsTable 
                options={options}
                onRowClick={(option) => setSelectedOption(option)}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {options.map((option, index) => (
                  <OptionsRecommendationCard 
                    key={`${option.symbol}-${index}`}
                    option={option}
                  />
                ))}
              </div>
            )}

            {options.length === 0 && !loading && (
              <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-12 text-center">
                <Target className="w-16 h-16 text-white/30 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Options Available</h3>
                <p className="text-white/60">
                  No options recommendations available at this time.
                </p>
                <button
                  onClick={handleRefresh}
                  className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all duration-200"
                >
                  Refresh Data
                </button>
              </div>
            )}
          </>
        )}

        {/* Statistics Footer */}
        {!loading && options.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-green-500/20 to-green-600/10 backdrop-blur-xl rounded-xl p-4 border border-green-500/30">
              <div className="text-green-400 text-sm font-semibold mb-1">High Confidence</div>
              <div className="text-3xl font-bold text-white">
                {options.filter(opt => opt.overall_confidence > 0.7).length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 backdrop-blur-xl rounded-xl p-4 border border-blue-500/30">
              <div className="text-blue-400 text-sm font-semibold mb-1">CALL Options</div>
              <div className="text-3xl font-bold text-white">
                {options.filter(opt => opt.option_type === 'CALL').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 backdrop-blur-xl rounded-xl p-4 border border-red-500/30">
              <div className="text-red-400 text-sm font-semibold mb-1">PUT Options</div>
              <div className="text-3xl font-bold text-white">
                {options.filter(opt => opt.option_type === 'PUT').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 backdrop-blur-xl rounded-xl p-4 border border-amber-500/30">
              <div className="text-amber-400 text-sm font-semibold mb-1">Avg Confidence</div>
              <div className="text-3xl font-bold text-white">
                {(options.reduce((sum, opt) => sum + opt.overall_confidence, 0) / options.length * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
