import { Panel } from '../../components/Panel';
const points = [32,36,34,42,39,48,45,53,50,58,55,64,60,68,66,74,71,79];
export function PriceChart() {
  const path = points.map((p,i)=>`${i===0?'M':'L'} ${i*20} ${110-p}`).join(' ');
  return <Panel title="BTC-USD · Price overview" action={<span className="muted small">1D · SIMULATED</span>}>
    <div className="chart-wrap"><svg viewBox="0 0 340 120" role="img" aria-label="Illustrative upward price chart" preserveAspectRatio="none">
      <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4f8cff" stopOpacity=".3"/><stop offset="100%" stopColor="#4f8cff" stopOpacity="0"/></linearGradient></defs>
      {[25,50,75,100].map(y=><line key={y} x1="0" x2="340" y1={y} y2={y} stroke="var(--line)" strokeDasharray="4 5"/> )}
      <path d={`${path} L 340 120 L 0 120 Z`} fill="url(#area)"/><path d={path} fill="none" stroke="#4f8cff" strokeWidth="2.5" vectorEffect="non-scaling-stroke"/>
    </svg></div><div className="chart-labels"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span></div>
  </Panel>;
}
