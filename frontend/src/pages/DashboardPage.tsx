import { Panel } from '../components/Panel';
export function DashboardPage() {
  return <Panel title="Account snapshot"><div className="stats-grid">
    <div><span>Paper balance</span><strong>$25,000.00</strong><small>Starting demo equity</small></div>
    <div><span>Open positions</span><strong>0</strong><small>No positions opened</small></div>
    <div><span>Today's P&amp;L</span><strong className="positive">$0.00</strong><small>Simulated account</small></div>
  </div></Panel>;
}
