import { useEffect, useState } from 'react';
import { fetchHealth } from './api/client';
import { useAppState, AppProvider } from './context/AppContext';
import { OrderBook } from './features/orderbook/OrderBook';
import { TradeForm } from './features/trading/TradeForm';
import { PriceChart } from './features/charting/PriceChart';
import { DashboardPage } from './pages/DashboardPage';
import { WalletPage } from './pages/WalletPage';
import { OrdersPage } from './pages/OrdersPage';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Activity, 
  BarChart3, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Info,
  X
} from 'lucide-react';
import type { MarketSymbol } from './types/trading';

function MainShell() {
  const { 
    activeTab, 
    setActiveTab, 
    selectedSymbol, 
    setSelectedSymbol, 
    markets, 
    marketList, 
    cashBalance, 
    toasts, 
    removeToast,
    isRealTimeActive
  } = useAppState();

  const [apiHealth, setApiHealth] = useState<'online' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    fetchHealth()
      .then(() => setApiHealth('online'))
      .catch(() => setApiHealth('offline'));
  }, []);

  return (
    <main className="shell">
      {/* Toast Notification Stack */}
      <div className="toast-container" aria-live="polite">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast-card ${toast.type}`}>
            <div className="toast-icon">
              {toast.type === 'success' && <CheckCircle2 size={18} />}
              {toast.type === 'error' && <AlertCircle size={18} />}
              {toast.type === 'info' && <Info size={18} />}
              {toast.type === 'warning' && <AlertCircle size={18} />}
            </div>
            <div className="toast-content">
              <strong>{toast.title}</strong>
              <p>{toast.description}</p>
            </div>
            <button 
              type="button" 
              className="toast-close" 
              onClick={() => removeToast(toast.id)}
              aria-label="Close notification"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Top Navigation Bar */}
      <header className="topbar">
        <div className="topbar-left">
          <div className="brand" onClick={() => setActiveTab('terminal')} style={{ cursor: 'pointer' }}>
            <span className="brand-mark">⚡</span>
            <div>
              <strong>ChronosMatch</strong>
              <small>Zero-Copy High-Frequency Trading Engine</small>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="tab-nav">
            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'terminal' ? 'active' : ''}`}
              onClick={() => setActiveTab('terminal')}
            >
              <BarChart3 size={15} />
              <span>Trading Terminal</span>
            </button>

            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'wallet' ? 'active' : ''}`}
              onClick={() => setActiveTab('wallet')}
            >
              <Wallet size={15} />
              <span>Wallet &amp; Portfolio</span>
              <span className="cash-tab-pill">
                ${cashBalance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </button>

            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
              onClick={() => setActiveTab('orders')}
            >
              <Clock size={15} />
              <span>Orders</span>
            </button>
          </nav>
        </div>

        {/* Topbar Right Telemetry & Quick Balance */}
        <div className="topbar-right">
          <button 
            type="button" 
            className="quick-wallet-badge" 
            onClick={() => setActiveTab('wallet')}
            title="Click to open Paper Wallet"
          >
            <div className="wallet-mini-icon">
              <Wallet size={14} />
            </div>
            <div className="wallet-mini-details">
              <span className="mini-label">PAPER CASH</span>
              <strong className="mini-cash">
                ${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </strong>
            </div>
          </button>

          <div className="status-indicators">
            <div className="status-item" title="Engine tick loop simulation">
              <span className={`dot ${isRealTimeActive ? 'green' : 'amber'}`} />
              <span>REAL-TIME ENGINE</span>
            </div>
            <div className="status-item" title="Gateway HTTP connection">
              <span className={`dot ${apiHealth === 'online' ? 'green' : 'dim'}`} />
              <span>GATEWAY {apiHealth}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      {activeTab === 'terminal' && (
        <>
          {/* Section Intro */}
          <section className="intro">
            <div>
              <p className="eyebrow">HIGH FREQUENCY TRADING / LIVE EXECUTION</p>
              <h1>Real-Time Trading Terminal</h1>
              <p className="muted">
                Zero-copy simulated matching engine. Trade paper funds with instant real-time cash balance updates.
              </p>
            </div>
            <div className="intro-badges">
              <span className="pill pulse-border">
                <Activity size={12} className="pulse-icon" /> ZERO-COPY ENGINE: ACTIVE
              </span>
              <span className="pill paper-pill">SIMULATED PAPER MONEY</span>
            </div>
          </section>

          {/* Interactive Market Strip */}
          <section className="market-strip">
            {marketList.map(m => {
              const isSelected = selectedSymbol === m.symbol;
              const isPositive = m.change >= 0;
              return (
                <article 
                  className={`market-card interactive ${isSelected ? 'selected' : ''}`} 
                  key={m.symbol}
                  onClick={() => setSelectedSymbol(m.symbol as MarketSymbol)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="market-card-head">
                    <div className="market-symbol-box">
                      <strong>{m.symbol}</strong>
                      <span className="market-name">{m.name}</span>
                    </div>
                    {isSelected && <span className="active-pair-badge">ACTIVE</span>}
                  </div>

                  <div className="market-card-price">
                    <strong className="live-ticker-price">
                      ${m.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </strong>
                    <em className={isPositive ? 'positive' : 'negative'}>
                      {isPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                      {isPositive ? '+' : ''}{m.change}%
                    </em>
                  </div>

                  <div className="market-card-meta">
                    <span>Vol: {m.volume24h.toLocaleString(undefined, { maximumFractionDigits: 0 })} {m.asset}</span>
                    <span>High: ${m.high24h.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                  </div>
                </article>
              );
            })}
          </section>

          {/* Workspace Grid */}
          <section className="workspace">
            <div className="main-column">
              <DashboardPage />
              <PriceChart />
              <OrderBook />
            </div>
            <aside>
              <TradeForm />
            </aside>
          </section>
        </>
      )}

      {activeTab === 'wallet' && <WalletPage />}

      {activeTab === 'orders' && <OrdersPage />}

      <footer>
        ChronosMatch Zero-Copy HFT Engine · Real-Time Paper Trading Mode · Cash balance increases when selling and decreases when buying.
      </footer>
    </main>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainShell />
    </AppProvider>
  );
}
