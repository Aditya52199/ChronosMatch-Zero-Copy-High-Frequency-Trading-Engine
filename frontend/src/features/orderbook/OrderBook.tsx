import { Panel } from '../../components/Panel';
const asks = [{p:'67,281.40',q:'0.184'},{p:'67,278.10',q:'0.420'},{p:'67,274.90',q:'0.095'},{p:'67,270.00',q:'0.735'}];
const bids = [{p:'67,250.20',q:'0.510'},{p:'67,246.80',q:'0.240'},{p:'67,241.10',q:'0.680'},{p:'67,238.60',q:'0.125'}];
export function OrderBook() {
  return <Panel title="Order book" action={<span className="muted small">BTC-USD</span>}><div className="book">
    <div className="book-head"><span>Price (USD)</span><span>Amount (BTC)</span></div>
    {asks.map((x,i)=><div className="book-row ask" key={i}><span>{x.p}</span><span>{x.q}</span></div>)}
    <div className="spread">$67,265.30 <small>Spread · 0.046%</small></div>
    {bids.map((x,i)=><div className="book-row bid" key={i}><span>{x.p}</span><span>{x.q}</span></div>)}
  </div></Panel>;
}
