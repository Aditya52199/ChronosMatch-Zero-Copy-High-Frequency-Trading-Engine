import { useEffect, useState } from 'react';
import { fetchHealth, fetchMarkets } from './api/client';
import { OrderBook } from './features/orderbook/OrderBook';
import { TradeForm } from './features/trading/TradeForm';
import { PriceChart } from './features/charting/PriceChart';
import { DashboardPage } from './pages/DashboardPage';

export default function App() {
  const [health, setHealth] = useState('checking');
  const [markets, setMarkets] = useState<{symbol:string; price:number; change:number}[]>([]);
  useEffect(() => {
    fetchHealth().then(() => setHealth('online')).catch(() => setHealth('offline'));
    fetchMarkets().then(setMarkets).catch(() => setMarkets([
      {symbol:'BTC-USD', price:67250.12, change:1.8},
      {symbol:'ETH-USD', price:3520.42, change:-0.6},
      {symbol:'SOL-USD', price:148.30, change:2.4},
    ]));
  }, []);
  return <main className="shell">
    <header className="topbar"><div className="brand"><span className="brand-mark"></span><div><strong>ChronosMatch</strong><small>Zero-Copy High-Frequency Trading
Engine</small></div></div>
      <div className="status"><span className={health === 'online' ? 'dot green' : 'dot'} /> API {health}</div>
    </header>
    <section className="intro"><div><p className="eyebrow">OVERVIEW / MARKETS</p><h1>Market dashboard</h1><p className="muted">A starter trading interface with simulated market data.</p></div><span className="pill">PAPER TRADING</span></section>
    <section className="market-strip">{markets.map(m => <article className="market-card" key={m.symbol}><span>{m.symbol}</span><strong>${m.price.toLocaleString(undefined,{maximumFractionDigits:2})}</strong><em className={m.change >= 0 ? 'positive' : 'negative'}>{m.change >= 0 ? '+' : ''}{m.change}%</em></article>)}</section>
    <section className="workspace"><div className="main-column"><DashboardPage /><PriceChart /><OrderBook /></div><aside><TradeForm /></aside></section>
    <footer>Demo interface only · No real orders are sent.</footer>
  </main>;
}
