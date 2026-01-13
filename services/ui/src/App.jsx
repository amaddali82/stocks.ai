import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TradingLayout from './components/TradingLayout';
import Watchlist from './components/Watchlist';
import OptionsChain from './components/OptionsChain';
import OrderPanel from './components/OrderPanel';
import Recommendations from './components/Recommendations';
import MarketOverview from './components/MarketOverview';
import Portfolio from './components/Portfolio';

function App() {
  const [activeView, setActiveView] = useState('recommendations');
  const [options, setOptions] = useState([]);
  const [highConfidenceOptions, setHighConfidenceOptions] = useState([]);
  const [mediumConfidenceOptions, setMediumConfidenceOptions] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [showOrderPanel, setShowOrderPanel] = useState(false);
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState({});
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [portfolio, setPortfolio] = useState([]);

  useEffect(() => {
    loadRecommendations();
    loadMarketData();
    // Verification check disabled - endpoint not available
    
    const interval = setInterval(() => {
      loadRecommendations();
      loadMarketData();
    }, 300000); // Reload every 5 minutes

    return () => clearInterval(interval);
  }, []);

  const transformOption = (opt) => ({
    ...opt,
    strike: opt.strike_price,
    expiry: opt.expiration_date,
    current_price: opt.entry_price,
    target_price_1: opt.target1,
    target_price_2: opt.target2,
    target_price_3: opt.target3,
    target_1_confidence: opt.target1_confidence,
    target_2_confidence: opt.target2_confidence,
    target_3_confidence: opt.target3_confidence,
    data_source: opt.source || 'Verified'
  });

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      
      const highConfResponse = await axios.get('/api/predictions/high-confidence', {
        params: { limit: 50 },
        timeout: 15000
      });
      
      const mediumConfResponse = await axios.get('/api/predictions/medium-confidence', {
        params: { limit: 100 },
        timeout: 15000
      });
      
      const allResponse = await axios.get('/api/predictions/best', {
        params: { limit: 30 },
        timeout: 15000
      });
      
      const transformedHigh = (highConfResponse.data.predictions || []).map(transformOption);
      const transformedMedium = (mediumConfResponse.data.predictions || []).map(transformOption);
      const transformedAll = (allResponse.data.predictions || []).map(transformOption);
      
      setHighConfidenceOptions(transformedHigh);
      setMediumConfidenceOptions(transformedMedium);
      setOptions(transformedAll);
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading recommendations:', error);
      setLoading(false);
    }
  };

  const loadMarketData = async () => {
    try {
      const response = await axios.get('/api/predictions/best', {
        params: { limit: 10 },
        timeout: 10000
      });
      
      if (response.data.predictions) {
        const data = {};
        response.data.predictions.forEach(opt => {
          data[opt.symbol] = {
            price: opt.current_price,
            change: opt.change_percent || 0
          };
        });
        setMarketData(data);
      }
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  const checkVerification = async () => {
    try {
      const response = await axios.get('/api/verify/status', {
        timeout: 5000
      });
      setVerificationStatus(response.data);
    } catch (error) {
      console.error('Error checking verification:', error);
    }
  };

  const handleSymbolSelect = (symbol) => {
    setSelectedSymbol(symbol);
    setActiveView('options');
  };

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    setShowOrderPanel(true);
  };

  const handleOrderSubmit = (order) => {
    console.log('Order submitted:', order);
    setShowOrderPanel(false);
    setSelectedOption(null);
  };

  const handleClosePosition = (position) => {
    console.log('Closing position:', position);
    setPortfolio(portfolio.filter(p => p !== position));
  };

  return (
    <TradingLayout
      activeView={activeView}
      onViewChange={setActiveView}
      verificationStatus={verificationStatus}
    >
      {activeView === 'recommendations' && (
        <Recommendations
          highConfidence={highConfidenceOptions}
          mediumConfidence={mediumConfidenceOptions}
          loading={loading}
          onSymbolSelect={handleSymbolSelect}
          onRefresh={loadRecommendations}
        />
      )}
      
      {activeView === 'watchlist' && (
        <Watchlist
          symbols={options.map(o => o.symbol)}
          marketData={marketData}
          onSymbolSelect={handleSymbolSelect}
        />
      )}
      
      {activeView === 'options' && (
        <OptionsChain
          symbol={selectedSymbol}
          onSelectOption={handleOptionSelect}
        />
      )}
      
      {activeView === 'portfolio' && (
        <Portfolio
          positions={portfolio}
          onClose={handleClosePosition}
        />
      )}
      
      {activeView === 'market' && (
        <MarketOverview />
      )}
      
      {showOrderPanel && selectedOption && (
        <OrderPanel
          option={selectedOption}
          onClose={() => {
            setShowOrderPanel(false);
            setSelectedOption(null);
          }}
          onSubmit={handleOrderSubmit}
        />
      )}
    </TradingLayout>
  );
}

export default App;
