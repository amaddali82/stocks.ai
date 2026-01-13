import React from 'react';
import { 
  Home, TrendingUp, List, Package, BarChart2, Settings, 
  User, Bell, Search, Activity, Shield, CheckCircle 
} from 'lucide-react';

export default function TradingLayout({ children, activeView, onViewChange, verificationStatus }) {
  const navItems = [
    { id: 'recommendations', label: 'Recommendations', icon: TrendingUp },
    { id: 'watchlist', label: 'Watchlist', icon: List },
    { id: 'options', label: 'Options Chain', icon: Activity },
    { id: 'portfolio', label: 'Portfolio', icon: Package },
    { id: 'market', label: 'Market', icon: BarChart2 },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Header - Zerodha/E*TRADE style */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Stocks.AI</span>
            </div>
            
            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    activeView === item.id
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Right side - Search and User */}
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search symbols..."
                className="bg-gray-50 border border-gray-300 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:border-blue-500 w-64"
              />
            </div>

            {/* Verification Status */}
            {verificationStatus && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-xs text-green-700">Data Verified</span>
              </div>
            )}

            {/* Notifications */}
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative">
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User */}
            <button className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 rounded-lg transition-colors">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-700">Account</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>

      {/* Bottom Status Bar */}
      <footer className="bg-white border-t border-gray-200 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Market Open</span>
            </div>
            <div>NSE: 19,847.45 (+0.34%)</div>
            <div>NIFTY: 23,644.80 (+0.52%)</div>
          </div>
          <div className="flex items-center gap-4">
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
            <div className="flex items-center gap-1">
              <Shield className="w-3 h-3 text-green-600" />
              <span className="text-green-600">Secure Connection</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
