import { useState } from 'react';
import { submitPaperOrder } from '../../api/client';
import { Panel } from '../../components/Panel';
export function TradeForm() {
  const [side,setSide] = useState<'buy'|'sell'>('buy');
  const [symbol,setSymbol] = useState('BTC-USD');
  const [quantity,setQuantity] = useState('0.01');
  const [type,setType] = useState<'market'|'limit'>('market');
  const [limitPrice,setLimitPrice] = useState('67250');
  const [message,setMessage] = useState('');
  const [busy,setBusy] = useState(false);
  async function submit(e:React.FormEvent) {
    e.preventDefault();
    const q = Number(quantity);
    if (!Number.isFinite(q) || q <= 0) { setMessage('Enter a quantity greater than zero.'); return; }
    setBusy(true); setMessage('');
    try {
      const result = await submitPaperOrder({symbol,side,quantity:q,type,...(type==='limit'?{limitPrice:Number(limitPrice)}:{})});
      setMessage(`Paper order accepted: ${result.id ?? 'demo order'}`);
    } catch {
      setMessage('Gateway unavailable. Start gateway-service to submit a paper order.');
    } finally { setBusy(false); }
  }
  return <Panel title="Place paper order"><form className="trade-form" onSubmit={submit}>
    <div className="side-toggle"><button type="button" className={side==='buy'?'active buy':''} onClick={()=>setSide('buy')}>Buy</button><button type="button" className={side==='sell'?'active sell':''} onClick={()=>setSide('sell')}>Sell</button></div>
    <label>Market<select value={symbol} onChange={e=>setSymbol(e.target.value)}><option>BTC-USD</option><option>ETH-USD</option><option>SOL-USD</option></select></label>
    <label>Order type<select value={type} onChange={e=>setType(e.target.value as 'market'|'limit')}><option value="market">Market</option><option value="limit">Limit</option></select></label>
    {type==='limit' && <label>Limit price (USD)<input type="number" min="0.01" step="0.01" value={limitPrice} onChange={e=>setLimitPrice(e.target.value)} required /></label>}
    <label>Quantity<input type="number" min="0.000001" step="any" value={quantity} onChange={e=>setQuantity(e.target.value)} required /></label>
    <div className="estimate"><span>Estimated total</span><strong>Calculated by gateway</strong></div>
    <button className={`submit-order ${side}`} disabled={busy}>{busy?'Submitting…':`Place ${side} paper order`}</button>
    {message && <p className="form-message" role="status">{message}</p>}
    <p className="fine-print">Paper trading only. This demo does not execute real trades.</p>
  </form></Panel>;
}
