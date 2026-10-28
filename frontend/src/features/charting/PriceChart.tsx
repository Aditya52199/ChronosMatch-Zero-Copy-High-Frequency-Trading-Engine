import { useState } from 'react';
import { useAppState } from '../../context/AppContext';
import { Panel } from '../../components/Panel';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';

export function PriceChart() {
  const { currentMarket } = useAppState();
  const [timeframe, setTimeframe] = useState<'1m' | '5m' | '15m' | '1H'>('1m');

  const history = currentMarket.history;
  const isPositive = currentMarket.change >= 0;
  const strokeColor = isPositive ? '#42d6a0' : '#ff7186';
  const gradientId = isPositive ? 'chart-gradient-green' : 'chart-gradient-red';

  // Compute SVG coordinates from real-time history
  const minVal = Math.min(...history);
  const maxVal = Math.max(...history);
  const range = Math.max(0.01, maxVal - minVal);
  const width = 580;
  const height = 150;
  const paddingY = 16;
  const plotHeight = height - paddingY * 2;

  const points = history.map((val, idx) => {
    const x = (idx / Math.max(1, history.length - 1)) * width;
    const y = paddingY + plotHeight - ((val - minVal) / range) * plotHeight;
    return { x, y, val };
  });

  const pathD = points
    .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  const areaD = `${pathD} L ${width} ${height} L 0 ${height} Z`;
  const lastPoint = points[points.length - 1] || { x: width, y: height / 2, val: currentMarket.price };

  return (
    <Panel
      title={`${currentMarket.symbol} · Real-Time Price Stream`}
      action={
        <div className="chart-header-actions">
          <div className="timeframe-buttons">
            {(['1m', '5m', '15m', '1H'] as const).map(tf => (
              <button
                key={tf}
                type="button"
                className={`tf-btn ${timeframe === tf ? 'active' : ''}`}
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
          <span className="live-stream-badge">
            <Activity size={12} /> STREAMING
          </span>
        </div>
      }
    >
      <div className="chart-meta-row">
        <div className="meta-item">
          <span className="muted">Live Price</span>
          <strong className="text-xl">
            ${currentMarket.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </strong>
        </div>
        <div className="meta-item">
          <span className="muted">24h Change</span>
          <strong className={`flex-center gap-1 ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {isPositive ? '+' : ''}{currentMarket.change}% (${currentMarket.changeAmount > 0 ? '+' : ''}{currentMarket.changeAmount})
          </strong>
        </div>
        <div className="meta-item">
          <span className="muted">24h High</span>
          <strong>${currentMarket.high24h.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
        </div>
        <div className="meta-item">
          <span className="muted">24h Low</span>
          <strong>${currentMarket.low24h.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
        </div>
        <div className="meta-item">
          <span className="muted">24h Volume</span>
          <strong>{currentMarket.volume24h.toLocaleString(undefined, { maximumFractionDigits: 0 })} {currentMarket.asset}</strong>
        </div>
      </div>

      <div className="chart-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="chart-gradient-green" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#42d6a0" stopOpacity="0.32" />
              <stop offset="100%" stopColor="#42d6a0" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="chart-gradient-red" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff7186" stopOpacity="0.32" />
              <stop offset="100%" stopColor="#ff7186" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((ratio, i) => (
            <line
              key={i}
              x1="0"
              x2={width}
              y1={height * ratio}
              y2={height * ratio}
              stroke="var(--line)"
              strokeDasharray="4 4"
              opacity="0.6"
            />
          ))}

          {/* Area Fill */}
          <path d={areaD} fill={`url(#${gradientId})`} />

          {/* Stroke Line */}
          <path
            d={pathD}
            fill="none"
            stroke={strokeColor}
            strokeWidth="2.4"
            vectorEffect="non-scaling-stroke"
          />

          {/* Pulse marker on current live point */}
          <circle cx={lastPoint.x} cy={lastPoint.y} r="5" fill={strokeColor} />
          <circle cx={lastPoint.x} cy={lastPoint.y} r="9" fill={strokeColor} opacity="0.3" className="pulse-circle" />
        </svg>
      </div>

      <div className="chart-labels">
        <span>-30s</span>
        <span>-20s</span>
        <span>-10s</span>
        <span className="positive">Now (Live)</span>
      </div>
    </Panel>
  );
}
