import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import './i18n';
import './App.css';

// Icons
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Settings, 
  User, 
  LogOut, 
  Play, 
  Pause,
  Wallet,
  BarChart3,
  Globe,
  Shield,
  Menu,
  X
} from 'lucide-react';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Axios configuration
axios.defaults.baseURL = API_BASE_URL;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get('/api/user/profile');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      toast.success('Login successful!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
      return false;
    }
  };

  const register = async (name, email, password) => {
    try {
      const response = await axios.post('/api/register', { name, email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      toast.success('Registration successful!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Logged out successfully');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// WebSocket Hook
const useWebSocket = (url) => {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!url) return;

    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [url]);

  return { data, isConnected };
};

// Components
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
  </div>
);

const Navbar = ({ onLanguageToggle, currentLang }) => {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-8 w-8 text-yellow-400" />
            <span className="text-xl font-bold text-white">TradingBot</span>
            <span className="text-sm text-gray-400">v0.1</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <button
              onClick={onLanguageToggle}
              className="flex items-center space-x-1 px-3 py-2 text-gray-300 hover:text-yellow-400 transition-colors"
            >
              <Globe className="h-4 w-4" />
              <span>{currentLang === 'tr' ? 'EN' : 'TR'}</span>
            </button>
            
            {user && (
              <>
                <div className="flex items-center space-x-2 text-gray-300">
                  <User className="h-4 w-4" />
                  <span>{user.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center space-x-1 px-3 py-2 text-gray-300 hover:text-red-400 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>{t('logout')}</span>
                </button>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-300 hover:text-yellow-400 transition-colors"
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-800">
            <div className="space-y-4">
              <button
                onClick={onLanguageToggle}
                className="flex items-center space-x-2 px-3 py-2 text-gray-300 hover:text-yellow-400 transition-colors w-full text-left"
              >
                <Globe className="h-4 w-4" />
                <span>{currentLang === 'tr' ? 'English' : 'Türkçe'}</span>
              </button>
              
              {user && (
                <>
                  <div className="flex items-center space-x-2 px-3 py-2 text-gray-300">
                    <User className="h-4 w-4" />
                    <span>{user.name}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center space-x-2 px-3 py-2 text-gray-300 hover:text-red-400 transition-colors w-full text-left"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>{t('logout')}</span>
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

const CoinHeatmap = ({ coins }) => {
  const { t } = useTranslation();

  const getColorByChange = (change) => {
    if (change > 5) return 'bg-green-500';
    if (change > 0) return 'bg-green-400';
    if (change > -5) return 'bg-red-400';
    return 'bg-red-500';
  };

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'STRONG_BUY': return 'text-green-400';
      case 'BUY': return 'text-green-300';
      case 'STRONG_SELL': return 'text-red-400';
      case 'SELL': return 'text-red-300';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h3 className="text-xl font-semibold text-white mb-6 flex items-center space-x-2">
        <Activity className="h-6 w-6 text-yellow-400" />
        <span>{t('liveMarketData')}</span>
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {coins?.map((coin) => (
          <div
            key={coin.symbol}
            className={`${getColorByChange(coin.change_24h)} bg-opacity-20 border border-gray-700 rounded-lg p-4 hover:bg-opacity-30 transition-all`}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-white">{coin.symbol}</h4>
              <div className={`text-sm font-medium ${coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h}%
              </div>
            </div>
            
            <div className="text-lg font-bold text-white mb-2">
              ${coin.price.toLocaleString()}
            </div>
            
            <div className="text-xs text-gray-400 space-y-1">
              <div>EMA9: {coin.ema9?.toFixed(4)}</div>
              <div>EMA21: {coin.ema21?.toFixed(4)}</div>
              <div className={`font-semibold ${getSignalColor(coin.signal)}`}>
                {coin.signal}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const BotControlPanel = ({ botConfig, onConfigUpdate, onStart, onStop }) => {
  const { t } = useTranslation();
  const [config, setConfig] = useState(botConfig);

  const handleSaveConfig = async () => {
    await onConfigUpdate(config);
    toast.success(t('configUpdated'));
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h3 className="text-xl font-semibold text-white mb-6 flex items-center space-x-2">
        <Settings className="h-6 w-6 text-yellow-400" />
        <span>{t('botControl')}</span>
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('tradingPair')}
          </label>
          <select
            value={config.symbol}
            onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          >
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="ETHUSDT">ETHUSDT</option>
            <option value="BNBUSDT">BNBUSDT</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('timeframe')}
          </label>
          <select
            value={config.timeframe}
            onChange={(e) => setConfig({ ...config, timeframe: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          >
            <option value="1m">1m</option>
            <option value="3m">3m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('leverage')}
          </label>
          <input
            type="number"
            min="1"
            max="125"
            value={config.leverage}
            onChange={(e) => setConfig({ ...config, leverage: parseInt(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('takeProfit')} (%)
          </label>
          <input
            type="number"
            step="0.1"
            value={config.take_profit}
            onChange={(e) => setConfig({ ...config, take_profit: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('stopLoss')} (%)
          </label>
          <input
            type="number"
            step="0.1"
            value={config.stop_loss}
            onChange={(e) => setConfig({ ...config, stop_loss: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t('positionSize')} ($)
          </label>
          <input
            type="number"
            step="1"
            value={config.position_size}
            onChange={(e) => setConfig({ ...config, position_size: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
        </div>
      </div>

      <div className="flex space-x-4">
        <button
          onClick={handleSaveConfig}
          className="px-4 py-2 bg-yellow-500 text-gray-900 rounded-md hover:bg-yellow-400 transition-colors font-medium"
        >
          {t('saveConfig')}
        </button>
        
        <button
          onClick={onStart}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-500 transition-colors"
        >
          <Play className="h-4 w-4" />
          <span>{t('startBot')}</span>
        </button>
        
        <button
          onClick={onStop}
          className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500 transition-colors"
        >
          <Pause className="h-4 w-4" />
          <span>{t('stopBot')}</span>
        </button>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [coins, setCoins] = useState([]);
  const [botConfig, setBotConfig] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  // WebSocket connection
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/ws`;
  const { data: wsData } = useWebSocket(wsUrl);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (wsData?.type === 'coins_update') {
      setCoins(wsData.data);
    }
  }, [wsData]);

  const fetchInitialData = async () => {
    try {
      const [coinsResponse, configResponse] = await Promise.all([
        axios.get('/api/coins'),
        axios.get('/api/bot/config')
      ]);

      setCoins(coinsResponse.data.coins);
      setBotConfig(configResponse.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigUpdate = async (newConfig) => {
    try {
      await axios.put('/api/bot/config', newConfig);
      setBotConfig(newConfig);
    } catch (error) {
      toast.error('Failed to update configuration');
    }
  };

  const handleStartBot = async () => {
    try {
      await axios.post('/api/bot/start');
      toast.success(t('botStarted'));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start bot');
    }
  };

  const handleStopBot = async () => {
    try {
      await axios.post('/api/bot/stop');
      toast.success(t('botStopped'));
    } catch (error) {
      toast.error('Failed to stop bot');
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="min-h-screen bg-gray-900 p-4 space-y-6">
      {/* Welcome Section */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-2xl font-bold text-white mb-2">
          {t('welcome')}, {user?.name}!
        </h2>
        <p className="text-gray-300">
          {t('dashboardDescription')}
        </p>
      </div>

      {/* Market Heatmap */}
      <CoinHeatmap coins={coins} />

      {/* Bot Control Panel */}
      <BotControlPanel 
        botConfig={botConfig}
        onConfigUpdate={handleConfigUpdate}
        onStart={handleStartBot}
        onStop={handleStopBot}
      />
    </div>
  );
};

const AuthPage = () => {
  const { t } = useTranslation();
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.name, formData.email, formData.password);
      }
    } catch (error) {
      // Error handling is done in auth context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="flex justify-center items-center space-x-2 mb-4">
            <BarChart3 className="h-10 w-10 text-yellow-400" />
            <span className="text-2xl font-bold text-white">TradingBot</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-300">
            {isLogin ? t('login') : t('register')}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('name')}
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                placeholder={t('enterName')}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('email')}
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400"
              placeholder={t('enterEmail')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('password')}
            </label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400"
              placeholder={t('enterPassword')}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-yellow-500 text-gray-900 py-2 px-4 rounded-md font-medium hover:bg-yellow-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 disabled:opacity-50 transition-colors"
          >
            {isLoading ? t('processing') : (isLogin ? t('login') : t('register'))}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-yellow-400 hover:text-yellow-300 transition-colors"
          >
            {isLogin ? t('needAccount') : t('haveAccount')}
          </button>
        </div>
      </div>
    </div>
  );
};

const Footer = () => {
  const { t } = useTranslation();
  
  return (
    <footer className="bg-gray-900 border-t border-gray-800 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <BarChart3 className="h-6 w-6 text-yellow-400" />
              <span className="text-lg font-bold text-white">TradingBot</span>
            </div>
            <p className="text-gray-400">
              {t('footerDescription')}
            </p>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">{t('features')}</h4>
            <ul className="space-y-2 text-gray-400">
              <li className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-yellow-400" />
                <span>{t('realTimeData')}</span>
              </li>
              <li className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-yellow-400" />
                <span>{t('emaStrategy')}</span>
              </li>
              <li className="flex items-center space-x-2">
                <Shield className="h-4 w-4 text-yellow-400" />
                <span>{t('secureTrading')}</span>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">{t('support')}</h4>
            <div className="space-y-2">
              <a href="#" className="block text-gray-400 hover:text-yellow-400 transition-colors">
                {t('documentation')}
              </a>
              <a href="#" className="block text-gray-400 hover:text-yellow-400 transition-colors">
                {t('support')}
              </a>
              <a href="#" className="block text-gray-400 hover:text-yellow-400 transition-colors">
                {t('contact')}
              </a>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2024 TradingBot v0.1 - MVP. {t('allRightsReserved')}</p>
        </div>
      </div>
    </footer>
  );
};

const App = () => {
  const { user, loading } = useAuth();
  const { i18n } = useTranslation();
  const [currentLang, setCurrentLang] = useState(i18n.language);

  const handleLanguageToggle = () => {
    const newLang = currentLang === 'tr' ? 'en' : 'tr';
    i18n.changeLanguage(newLang);
    setCurrentLang(newLang);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar onLanguageToggle={handleLanguageToggle} currentLang={currentLang} />
      
      <main className="flex-1">
        {user ? <Dashboard /> : <AuthPage />}
      </main>
      
      <Footer />
      
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#374151',
            color: '#ffffff',
            border: '1px solid #4B5563'
          }
        }}
      />
    </div>
  );
};

const AppWithAuth = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default AppWithAuth;