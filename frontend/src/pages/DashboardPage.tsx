import { useAppState } from '../context/AppContext';
import { Panel } from '../components/Panel';
import { Wallet, TrendingUp, TrendingDown, ArrowRight, ShieldCheck } from 'lucide-react';

export function DashboardPage() {
  const { 
    cashBalance, 
    portfolioTotalValue, 
    holdings, 
    totalUnrealizedPnL, 
    totalUnrealizedPnLPercent, 
    totalRealizedPnL,
    setActiveTab 
  } = useAppState();

  const openPositionsCount = Object.values(holdings).filter(h => h.quantity > 0.000001).length;
  const netPnL = totalUnrealizedPnL + totalRealizedPnL;
  const isPositive = netPnL >= 0;

  return (
    <Panel 
      title="Live Paper Account Snapshot"
      action={
        <button 
          type="button" 
          className="link-tab-btn" 
          onClick={() => setActiveTab('wallet')}
        >
          <span>View Full Wallet</span>
          <ArrowRight size={13} />
        </button>
      }
    >
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-box-title">
            <Wallet size={14} className="muted" />
            <span>Paper Cash Balance</span>
          </div>
          <strong className="green-text">
            ${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </strong>
          <small>Available paper trading capital</small>
        </div>

        <div className="stat-box">
          <div className="stat-box-title">
            <ShieldCheck size={14} className="muted" />
            <span>Portfolio Net Worth</span>
          </div>
          <strong>
            ${portfolioTotalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </strong>
          <small>{openPositionsCount} active {openPositionsCount === 1 ? 'position' : 'positions'}</small>
        </div>

        <div className="stat-box">
          <div className="stat-box-title">
            {isPositive ? <TrendingUp size={14} className="positive" /> : <TrendingDown size={14} className="negative" />}
            <span>Combined P&amp;L</span>
          </div>
          <strong className={isPositive ? 'positive' : 'negative'}>
            {isPositive ? '+' : ''}${netPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </strong>
          <small>
            Unrealized: {totalUnrealizedPnL >= 0 ? '+' : ''}${totalUnrealizedPnL.toFixed(2)} ({totalUnrealizedPnLPercent}%)
          </small>
        </div>
      </div>
    </Panel>
  );
}
