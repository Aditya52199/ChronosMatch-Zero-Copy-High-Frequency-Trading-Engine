import { useAppState } from '../context/AppContext';
import { Panel } from '../components/Panel';
import { Clock, CheckCircle2, ArrowDownRight, ArrowUpRight, ExternalLink } from 'lucide-react';

export function OrdersPage() {
  const { orders, setActiveTab, setSelectedSymbol } = useAppState();

  return (
    <div className="orders-page-container">
      <Panel 
        title="Paper Order History &amp; Executions" 
        action={
          <span className="panel-tag">{orders.length} Total Orders</span>
        }
      >
        {orders.length === 0 ? (
          <div className="empty-ledger">
            <Clock size={32} className="muted" />
            <h3>No Orders Placed Yet</h3>
            <p className="muted">
              Place your first market or limit paper order from the Trading Terminal.
            </p>
            <button 
              type="button" 
              className="action-btn buy" 
              onClick={() => setActiveTab('terminal')}
            >
              Go to Trading Terminal <ExternalLink size={13} />
            </button>
          </div>
        ) : (
          <div className="holdings-table-wrap">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Side</th>
                  <th>Pair</th>
                  <th>Type</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Quantity</th>
                  <th className="text-right">Total (USD)</th>
                  <th className="text-right">Time</th>
                  <th className="text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => {
                  const isBuy = order.side === 'buy';
                  return (
                    <tr key={order.id}>
                      <td className="tabular-nums muted">{order.id}</td>
                      <td>
                        <span className={`tx-type-badge ${order.side}`}>
                          {isBuy ? <ArrowDownRight size={12} /> : <ArrowUpRight size={12} />}
                          {order.side.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <button 
                          type="button"
                          className="symbol-link-btn"
                          onClick={() => {
                            setSelectedSymbol(order.symbol);
                            setActiveTab('terminal');
                          }}
                        >
                          <strong>{order.symbol}</strong>
                        </button>
                      </td>
                      <td>
                        <span className="type-pill">{order.type.toUpperCase()}</span>
                      </td>
                      <td className="text-right tabular-nums">
                        ${order.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="text-right tabular-nums font-semibold">
                        {order.quantity}
                      </td>
                      <td className="text-right tabular-nums">
                        <strong className={isBuy ? 'text-red' : 'text-green'}>
                          ${order.total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </strong>
                      </td>
                      <td className="text-right muted text-xs tabular-nums">
                        {new Date(order.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="text-center">
                        <span className="status-pill-filled">
                          <CheckCircle2 size={12} /> FILLED
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
