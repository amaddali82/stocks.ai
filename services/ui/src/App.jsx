import React, { useState, useEffect } from 'react';
import axios from 'axios';
import RecommendationCard from './components/RecommendationCard';
import Header from './components/Header';
import SystemStatus from './components/SystemStatus';
import PredictionChart from './components/PredictionChart';

function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    prediction: 'checking',
    risk: 'checking',
    data: 'checking'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Mock data for demonstration
  const mockRecommendations = [
    {
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.87,
      targetPrice: 185.50,
      currentPrice: 178.20,
      prediction: 'strong_bullish',
      modelSignals: {
        lstm: 0.85,
        transformer: 0.89,
        sentiment: 0.82
      },
      technicalIndicators: {
        rsi: 62.5,
        macd: 'bullish',
        volume: 'above_average'
      },
      reasoning: 'Strong technical momentum, positive sentiment analysis, and favorable market conditions',
      riskLevel: 'medium',
      timeHorizon: '5-7 days'
    },
    {
      symbol: 'TSLA',
      action: 'HOLD',
      confidence: 0.65,
      targetPrice: 245.80,
      currentPrice: 242.10,
      prediction: 'neutral',
      modelSignals: {
        lstm: 0.62,
        transformer: 0.68,
        sentiment: 0.55
      },
      technicalIndicators: {
        rsi: 48.3,
        macd: 'neutral',
        volume: 'average'
      },
      reasoning: 'Mixed signals from technical indicators, moderate sentiment, awaiting clearer trend',
      riskLevel: 'medium',
      timeHorizon: '3-5 days'
    },
    {
      symbol: 'NVDA',
      action: 'BUY',
      confidence: 0.92,
      targetPrice: 195.00,
      currentPrice: 184.00,
      prediction: 'very_bullish',
      modelSignals: {
        lstm: 0.91,
        transformer: 0.94,
        sentiment: 0.88
      },
      technicalIndicators: {
        rsi: 68.2,
        macd: 'strong_bullish',
        volume: 'high'
      },
      reasoning: 'Exceptional AI sector momentum, strong institutional buying, positive earnings outlook',
      riskLevel: 'medium-high',
      timeHorizon: '7-10 days'
    },
    {
      symbol: 'GOOGL',
      action: 'SELL',
      confidence: 0.73,
      targetPrice: 128.50,
      currentPrice: 138.90,
      prediction: 'bearish',
      modelSignals: {
        lstm: 0.71,
        transformer: 0.75,
        sentiment: 0.42
      },
      technicalIndicators: {
        rsi: 38.7,
        macd: 'bearish',
        volume: 'below_average'
      },
      reasoning: 'Weakening technicals, negative sentiment shift, regulatory concerns',
      riskLevel: 'medium',
      timeHorizon: '5-7 days'
    },
    {
      symbol: 'MSFT',
      action: 'BUY',
      confidence: 0.81,
      targetPrice: 395.00,
      currentPrice: 378.50,
      prediction: 'bullish',
      modelSignals: {
        lstm: 0.79,
        transformer: 0.83,
        sentiment: 0.76
      },
      technicalIndicators: {
        rsi: 59.4,
        macd: 'bullish',
        volume: 'above_average'
      },
      reasoning: 'Cloud growth acceleration, AI integration driving upside, strong fundamentals',
      riskLevel: 'low-medium',
      timeHorizon: '7-14 days'
    },
    {
      symbol: 'META',
      action: 'HOLD',
      confidence: 0.58,
      targetPrice: 352.00,
      currentPrice: 348.20,
      prediction: 'slightly_bullish',
      modelSignals: {
        lstm: 0.56,
        transformer: 0.60,
        sentiment: 0.52
      },
      technicalIndicators: {
        rsi: 52.1,
        macd: 'neutral',
        volume: 'average'
      },
      reasoning: 'Consolidating after recent rally, monitoring key support levels',
      riskLevel: 'medium',
      timeHorizon: '3-5 days'
    }
  ];

  useEffect(() => {
    // Check system status
    checkSystemStatus();
    
    // Load recommendations
    loadRecommendations();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      checkSystemStatus();
      loadRecommendations();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const checkSystemStatus = async () => {
    const status = {
      prediction: 'offline',
      risk: 'offline',
      data: 'offline'
    };

    try {
      await axios.get('http://localhost:8001/health', { timeout: 2000 });
      status.prediction = 'online';
    } catch (e) {
      status.prediction = 'offline';
    }

    try {
      await axios.get('http://localhost:8003/health', { timeout: 2000 });
      status.risk = 'online';
    } catch (e) {
      status.risk = 'offline';
    }

    // Assume data service is running if container is up
    status.data = 'online';

    setSystemStatus(status);
  };

  const loadRecommendations = async () => {
    try {
      // Try to fetch from API
      try {
        const response = await axios.get('http://localhost:8001/api/predictions', { timeout: 5000 });
        setRecommendations(response.data);
        setError(null);
      } catch (apiError) {
        // Use mock data if API is not available
        setRecommendations(mockRecommendations);
        setError('Using demo data - API services are starting up');
      }
      
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      setRecommendations(mockRecommendations);
      setError('Using demo data - API services are starting up');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        <Header lastUpdate={lastUpdate} />
        
        <SystemStatus status={systemStatus} />

        {error && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-lg animate-slide-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-pulse-custom">
              <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          </div>
        ) : (
          <>
            <PredictionChart recommendations={recommendations} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
              {recommendations.map((rec, index) => (
                <RecommendationCard 
                  key={rec.symbol} 
                  recommendation={rec}
                  index={index}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
