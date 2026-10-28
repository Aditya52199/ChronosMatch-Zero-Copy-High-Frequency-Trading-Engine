import { useState } from 'react';
import { useAppState } from '../context/AppContext';
import { Panel } from '../components/Panel';
import { 
  Wallet, 
  ArrowUpRight, 
  ArrowDownRight, 
  PlusCircle, 
  RotateCcw, 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  ShieldCheck, 
  Clock,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import type { MarketSymbol } from '../types/trading';

export function WalletPage() {
  const { 
    cashBalance, 
    holdings, 
    markets, 
    transactions, 
    portfolioTotalValue, 
    totalUnrealizedPnL, 
    totalUnrealizedPnLPercent, 
    totalRealizedPnL, 
    totalInvested,
    depositPaperCash, 
    resetPaperWallet,
    executePaperOrder,
    setSelectedSymbol,
    setActiveTab
  } = useAppState();

  const [depositAmount, setDepositAmount] = useState<string>('5000');
  const [filterType, setFilterType] = useState<'ALL' | 'BUY' | 'SELL' | 'DEPOSIT'>('ALL');
  const [sellingAsset, setSellingAsset] = useState<string | null>(null);

  const handleDeposit = (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(depositAmount);
    if (!isNaN(val) && val > 0) {
      depositPaperCash(val);
      setDepositAmount('5000');
    }
  };

  const handleQuickSell = async (symbol: MarketSymbol, percent: number) => {
    const market = markets[symbol];
    if (!market) return;
    const holding = holdings[market.asset];
    if (!holding || holding.quantity <= 0) return;

    const qtyToSell = percent === 100 
      ? holding.quantity 
      : Number((holding.quantity * (percent / 100)).toFixed(6));

    setSellingAsset(market.asset);
    try {
      await executePaperOrder({
        symbol,
        side: 'sell',
        type: 'market',
        quantity: qtyToSell
      });
    } catch {
      // Handled via toast
    } finally {
      setSellingAsset(null);
    }
  };

  const filteredTransactions = transactions.filter(tx => {
    if (filterType === 'ALL') return true;
    return tx.type === filterType;
  });

  return (
    <div className="wallet-container">
      {/* Portfolio Top Highlights */}
      <section className="wallet-hero-grid">
        <article className="wallet-stat-card primary-gradient">
          <div className="stat-header">
            <span className="stat-label">Total Portfolio Net Worth</span>
            <span className="badge live-badge">
              <span className="live-dot" /> LIVE VALUATION
            </span>
          </div>
          <div className="stat-value-large">
            ${portfolioTotalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="stat-footer">
            <span className={`pnl-badge ${totalUnrealizedPnL >= 0 ? 'positive' : 'negative'}`}>
              {totalUnrealizedPnL >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {totalUnrealizedPnL >= 0 ? '+' : ''}${totalUnrealizedPnL.toLocaleString(undefined, { minimumFractionDigits: 2 })} ({totalUnrealizedPnL >= 0 ? '+' : ''}{totalUnrealizedPnLPercent}%)
            </span>
            <span className="stat-caption">Unrealized P&amp;L</span>
          </div>
        </article>

        <article className="wallet-stat-card">
          <div className="stat-header">
            <span className="stat-label">Available Paper Cash</span>
            <div className="wallet-icon-wrap green">
              <DollarSign size={18} />
            </div>
          </div>
          <div className="stat-value-large green-text">
            ${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="stat-footer">
            <span className="cash-indicator">
              <span className="pulse-dot" /> Ready for immediate paper orders
            </span>
          </div>
        </article>

        <article className="wallet-stat-card">
          <div className="stat-header">
            <span className="stat-label">Active Capital in Assets</span>
            <div className="wallet-icon-wrap blue">
              <Sparkles size={18} />
            </div>
          </div>
          <div className="stat-value-large">
            ${(portfolioTotalValue - cashBalance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="stat-footer">
            <span className="stat-subtext">Original Cost Basis: ${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          </div>
        </article>

        <article className="wallet-stat-card">
          <div className="stat-header">
            <span className="stat-label">Realized Trading P&amp;L</span>
            <div className={`wallet-icon-wrap ${totalRealizedPnL >= 0 ? 'green' : 'red'}`}>
              {totalRealizedPnL >= 0 ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
            </div>
          </div>
          <div className={`stat-value-large ${totalRealizedPnL >= 0 ? 'green-text' : 'red-text'}`}>
            {totalRealizedPnL >= 0 ? '+' : ''}${totalRealizedPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="stat-footer">
            <span className="stat-subtext">Profit/Loss locked in from sells</span>
          </div>
        </article>
      </section>

      {/* Paper Cash Management Tool */}
      <section className="paper-manager-panel">
        <div className="manager-intro">
          <div className="badge-paper">
            <ShieldCheck size={14} /> Paper Trading Simulator
          </div>
          <h3>Paper Money Controls</h3>
          <p>
            Experience simulated high-frequency order execution. When you <strong>BUY</strong>, paper cash <em>decreases</em> and your asset holdings increase. When you <strong>SELL</strong>, your asset holdings decrease and paper cash <em>increases</em> in real time.
          </p>
        </div>

        <div className="manager-actions">
          <div className="quick-deposit-group">
            <span className="action-hint">Quick Deposit:</span>
            <button type="button" className="quick-btn" onClick={() => depositPaperCash(1000)}>+$1,000</button>
            <button type="button" className="quick-btn" onClick={() => depositPaperCash(5000)}>+$5,000</button>
            <button type="button" className="quick-btn" onClick={() => depositPaperCash(10000)}>+$10,000</button>
            <button type="button" className="quick-btn" onClick={() => depositPaperCash(25000)}>+$25,000</button>
          </div>

          <form onSubmit={handleDeposit} className="custom-deposit-form">
            <div className="input-with-symbol">
              <span className="prefix">$</span>
              <input 
                type="number" 
                min="1" 
                step="100" 
                value={depositAmount} 
                onChange={e => setDepositAmount(e.target.value)} 
                placeholder="Amount"
              />
            </div>
            <button type="submit" className="deposit-btn">
              <PlusCircle size={15} /> Add Funds
            </button>
          </form>

          <button 
            type="button" 
            className="reset-btn" 
            onClick={() => {
              if (window.confirm('Reset your paper wallet back to starting $25,000.00 cash? All holdings will be cleared.')) {
                resetPaperWallet();
              }
            }}
            title="Reset wallet to default starting condition"
          >
            <RotateCcw size={14} /> Reset to $25k
          </button>
        </div>
      </section>

      {/* Asset Holdings Breakdown */}
      <Panel 
        title="Asset Holdings &amp; Positions" 
        action={
          <span className="panel-tag">
            {Object.values(holdings).filter(h => h.quantity > 0).length} Open Positions
          </span>
        }
      >
        <div className="holdings-table-wrap">
          <table className="modern-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th className="text-right">Quantity Held</th>
                <th className="text-right">Avg Buy Price</th>
                <th className="text-right">Live Price</th>
                <th className="text-right">Market Value</th>
                <th className="text-right">Unrealized P&amp;L</th>
                <th className="text-center">Paper Actions</th>
              </tr>
            </thead>
            <tbody>
              {(['BTC-USD', 'ETH-USD', 'SOL-USD'] as MarketSymbol[]).map(symbol => {
                const market = markets[symbol];
                const asset = market.asset;
                const holding = holdings[asset] || { asset, symbol, quantity: 0, avgCost: 0, totalCost: 0 };
                const marketPrice = market.price;
                const currentValue = holding.quantity * marketPrice;
                const pnl = holding.quantity > 0 ? currentValue - holding.totalCost : 0;
                const pnlPercent = holding.totalCost > 0 ? (pnl / holding.totalCost) * 100 : 0;
                const hasPosition = holding.quantity > 0.000001;

                return (
                  <tr key={symbol} className={hasPosition ? 'active-row' : 'inactive-row'}>
                    <td>
                      <div className="asset-cell">
                        <span className={`asset-circle ${asset.toLowerCase()}`}>
                          {asset.substring(0, 3)}
                        </span>
                        <div>
                          <strong>{market.name}</strong>
                          <small className="muted">{symbol}</small>
                        </div>
                      </div>
                    </td>
                    <td className="text-right tabular-nums">
                      <strong>{holding.quantity.toFixed(4)}</strong> <span className="muted">{asset}</span>
                    </td>
                    <td className="text-right tabular-nums">
                      {hasPosition ? `$${holding.avgCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="text-right tabular-nums">
                      <span className="live-ticker-price">
                        ${marketPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="text-right tabular-nums">
                      <strong>${currentValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                    </td>
                    <td className="text-right tabular-nums">
                      {hasPosition ? (
                        <span className={`badge-inline ${pnl >= 0 ? 'positive' : 'negative'}`}>
                          {pnl >= 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          <small>({pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)</small>
                        </span>
                      ) : (
                        <span className="muted">$0.00</span>
                      )}
                    </td>
                    <td className="text-center">
                      <div className="row-actions">
                        <button
                          type="button"
                          className="action-btn buy"
                          onClick={() => {
                            setSelectedSymbol(symbol);
                            setActiveTab('terminal');
                          }}
                        >
                          Trade <ExternalLink size={12} />
                        </button>
                        {hasPosition && (
                          <>
                            <button
                              type="button"
                              className="action-btn sell-half"
                              disabled={sellingAsset === asset}
                              onClick={() => handleQuickSell(symbol, 50)}
                              title="Sell 50% of holding for instant paper cash"
                            >
                              Sell 50%
                            </button>
                            <button
                              type="button"
                              className="action-btn sell-all"
                              disabled={sellingAsset === asset}
                              onClick={() => handleQuickSell(symbol, 100)}
                              title="Sell 100% of holding for instant paper cash"
                            >
                              Sell 100%
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Transaction & Order Ledger */}
      <Panel
        title="Paper Money Transaction Ledger"
        action={
          <div className="filter-pill-group">
            {(['ALL', 'BUY', 'SELL', 'DEPOSIT'] as const).map(type => (
              <button
                key={type}
                type="button"
                className={`filter-pill ${filterType === type ? 'active' : ''}`}
                onClick={() => setFilterType(type)}
              >
                {type}
              </button>
            ))}
          </div>
        }
      >
        <div className="ledger-wrap">
          {filteredTransactions.length === 0 ? (
            <div className="empty-ledger">
              <Clock size={28} className="muted" />
              <p>No transactions found for filter "{filterType}".</p>
              <button 
                type="button" 
                className="action-btn buy" 
                onClick={() => setActiveTab('terminal')}
              >
                Go to Terminal to Trade
              </button>
            </div>
          ) : (
            <table className="modern-table ledger-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Description</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Quantity</th>
                  <th className="text-right">Cash Impact</th>
                  <th className="text-right">Realized P&amp;L</th>
                  <th className="text-right">Time</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map(tx => {
                  const isBuy = tx.type === 'BUY';
                  const isSell = tx.type === 'SELL';
                  const isDeposit = tx.type === 'DEPOSIT';
                  const isReset = tx.type === 'RESET';

                  return (
                    <tr key={tx.id}>
                      <td>
                        <span className={`tx-type-badge ${tx.type.toLowerCase()}`}>
                          {isBuy && <ArrowDownRight size={12} />}
                          {isSell && <ArrowUpRight size={12} />}
                          {isDeposit && <PlusCircle size={12} />}
                          {isReset && <RotateCcw size={12} />}
                          {tx.type}
                        </span>
                      </td>
                      <td>
                        <strong>{tx.note || (tx.symbol ? `${tx.type} ${tx.symbol}` : 'Cash Adjustment')}</strong>
                      </td>
                      <td className="text-right tabular-nums">
                        {tx.price ? `$${tx.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}
                      </td>
                      <td className="text-right tabular-nums">
                        {tx.quantity ? `${tx.quantity} ${tx.asset}` : '—'}
                      </td>
                      <td className="text-right tabular-nums">
                        <strong className={`cash-impact ${isBuy ? 'deduct' : 'credit'}`}>
                          {isBuy ? '-' : '+'}${tx.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </strong>
                      </td>
                      <td className="text-right tabular-nums">
                        {tx.realizedPnL !== undefined ? (
                          <span className={`badge-inline ${tx.realizedPnL >= 0 ? 'positive' : 'negative'}`}>
                            {tx.realizedPnL >= 0 ? '+' : ''}${tx.realizedPnL.toFixed(2)}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="text-right muted text-xs tabular-nums">
                        {new Date(tx.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Panel>
    </div>
  );
}
