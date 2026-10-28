import { useMemo } from 'react';
import { useAppState } from '../../context/AppContext';
import { Panel } from '../../components/Panel';
import { Layers } from 'lucide-react';

export function OrderBook() {
  const { currentMarket } = useAppState();
  const price = currentMarket.price;
  const asset = currentMarket.asset;

  // Generate real-time synthetic order book levels anchored to current live price
  const { asks, bids, spread, spreadPercent } = useMemo(() => {
    const askLevels = [];
    const bidLevels = [];
    let cumAsk = 0;
    let cumBid = 0;

    // 5 ask levels above price
    for (let i = 5; i >= 1; i--) {
      const step = (price * 0.00035 * i);
      const levelPrice = price + step;
      const qty = Number(((Math.sin(levelPrice * 13) * 0.4 + 0.6) * (asset === 'BTC' ? 0.35 : asset === 'ETH' ? 2.5 : 18)).toFixed(3));
      cumAsk += qty;
      askLevels.push({
        price: levelPrice,
        qty,
        total: cumAsk,
        pct: Math.min(100, Math.max(15, (qty / (asset === 'BTC' ? 1.5 : 20)) * 100)),
      });
    }

    // 5 bid levels below price
    for (let i = 1; i <= 5; i++) {
      const step = (price * 0.00035 * i);
      const levelPrice = price - step;
      const qty = Number(((Math.cos(levelPrice * 17) * 0.4 + 0.6) * (asset === 'BTC' ? 0.35 : asset === 'ETH' ? 2.5 : 18)).toFixed(3));
      cumBid += qty;
      bidLevels.push({
        price: levelPrice,
        qty,
        total: cumBid,
        pct: Math.min(100, Math.max(15, (qty / (asset === 'BTC' ? 1.5 : 20)) * 100)),
      });
    }

    const bestAsk = askLevels[askLevels.length - 1]?.price || price * 1.0002;
    const bestBid = bidLevels[0]?.price || price * 0.9998;
    const spreadVal = Math.max(0.01, bestAsk - bestBid);
    const spreadPct = (spreadVal / price) * 100;

    return {
      asks: askLevels,
      bids: bidLevels,
      spread: spreadVal,
      spreadPercent: spreadPct,
    };
  }, [price, asset]);

  return (
    <Panel
      title="Live Zero-Copy Order Book"
      action={
        <div className="book-action-badge">
          <Layers size={13} />
          <span>{currentMarket.symbol} · L2 DEPTH</span>
        </div>
      }
    >
      <div className="book">
        <div className="book-head">
          <span>Price (USD)</span>
          <span className="text-right">Size ({asset})</span>
          <span className="text-right">Total</span>
        </div>

        {/* Asks (Sells) */}
        <div className="book-list asks-list">
          {asks.map((x, i) => (
            <div className="book-row ask" key={`ask-${i}`}>
              <div className="depth-bar ask-bar" style={{ width: `${x.pct}%` }} />
              <span className="price-col text-red">${x.price.toFixed(2)}</span>
              <span className="qty-col text-right">{x.qty.toFixed(3)}</span>
              <span className="total-col text-right muted">{x.total.toFixed(3)}</span>
            </div>
          ))}
        </div>

        {/* Current Mid Spread */}
        <div className="spread-bar">
          <div className="spread-price">
            <strong>${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
            <span className="spread-tag">
              Spread: ${spread.toFixed(2)} ({spreadPercent.toFixed(3)}%)
            </span>
          </div>
          <span className="live-pill">
            <span className="pulse-dot" /> LIVE TICK
          </span>
        </div>

        {/* Bids (Buys) */}
        <div className="book-list bids-list">
          {bids.map((x, i) => (
            <div className="book-row bid" key={`bid-${i}`}>
              <div className="depth-bar bid-bar" style={{ width: `${x.pct}%` }} />
              <span className="price-col text-green">${x.price.toFixed(2)}</span>
              <span className="qty-col text-right">{x.qty.toFixed(3)}</span>
              <span className="total-col text-right muted">{x.total.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
