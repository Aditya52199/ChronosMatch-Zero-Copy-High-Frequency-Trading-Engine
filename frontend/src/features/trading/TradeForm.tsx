import { useState, useMemo } from 'react';
import { useAppState } from '../../context/AppContext';
import { Panel } from '../../components/Panel';
import { DollarSign, Wallet, ArrowDownRight, ArrowUpRight, CheckCircle2, AlertCircle } from 'lucide-react';
import type { MarketSymbol } from '../../types/trading';

export function TradeForm() {
  const { 
    selectedSymbol, 
    setSelectedSymbol, 
    currentMarket, 
    markets, 
    cashBalance, 
    holdings, 
    executePaperOrder 
  } = useAppState();

  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('0.05');
  const [type, setType] = useState<'market' | 'limit'>('market');
  const [limitPrice, setLimitPrice] = useState(currentMarket.price.toFixed(2));
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Update limit price when symbol changes if user hasn't heavily modified it
  const marketPrice = currentMarket.price;
  const asset = currentMarket.asset;
  const currentHolding = holdings[asset] || { asset, symbol: selectedSymbol, quantity: 0, avgCost: 0, totalCost: 0 };

  const parsedQty = parseFloat(quantity) || 0;
  const effectivePrice = type === 'limit' ? (parseFloat(limitPrice) || marketPrice) : marketPrice;
  const estimatedTotal = Number((parsedQty * effectivePrice).toFixed(2));

  // Max calculations
  const maxBuyQuantity = useMemo(() => {
    if (effectivePrice <= 0) return 0;
    return Number((cashBalance / effectivePrice).toFixed(6));
  }, [cashBalance, effectivePrice]);

  const maxSellQuantity = useMemo(() => {
    return Number(currentHolding.quantity.toFixed(6));
  }, [currentHolding.quantity]);

  // Handle Quick Percentage
  const handlePercentage = (pct: number) => {
    setErrorMsg('');
    setSuccessMsg('');
    if (side === 'buy') {
      if (effectivePrice <= 0) return;
      const budget = (cashBalance * (pct / 100));
      const calcQty = Number((budget / effectivePrice).toFixed(4));
      setQuantity(calcQty.toString());
    } else {
      const calcQty = Number((currentHolding.quantity * (pct / 100)).toFixed(4));
      setQuantity(calcQty.toString());
    }
  };

  const remainingCashIfBuy = Math.max(0, cashBalance - estimatedTotal);
  const newCashIfSell = cashBalance + estimatedTotal;

  const isInsufficientBuyFunds = side === 'buy' && estimatedTotal > cashBalance;
  const isInsufficientSellBalance = side === 'sell' && parsedQty > currentHolding.quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (parsedQty <= 0) {
      setErrorMsg('Please specify a quantity greater than zero.');
      return;
    }

    if (side === 'buy' && estimatedTotal > cashBalance) {
      setErrorMsg(`Insufficient paper cash! Total is $${estimatedTotal.toLocaleString()} but available is $${cashBalance.toLocaleString()}.`);
      return;
    }

    if (side === 'sell' && parsedQty > currentHolding.quantity) {
      setErrorMsg(`Insufficient ${asset}! You only own ${currentHolding.quantity.toFixed(4)} ${asset}.`);
      return;
    }

    setBusy(true);
    try {
      const result = await executePaperOrder({
        symbol: selectedSymbol,
        side,
        type,
        quantity: parsedQty,
        ...(type === 'limit' ? { limitPrice: parseFloat(limitPrice) } : {}),
      });

      setSuccessMsg(result.message);
      // If sold out or small residual, reset quantity gently
      if (side === 'sell' && parsedQty >= currentHolding.quantity) {
        setQuantity('0.01');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit order');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel 
      title="Execute Paper Order" 
      action={
        <span className="live-pulse-badge">
          <span className="pulse-dot" /> Real-Time Engine
        </span>
      }
    >
      <form className="trade-form" onSubmit={handleSubmit}>
        {/* Side Toggle */}
        <div className="side-toggle">
          <button 
            type="button" 
            className={side === 'buy' ? 'active buy' : ''} 
            onClick={() => { setSide('buy'); setErrorMsg(''); setSuccessMsg(''); }}
          >
            <ArrowDownRight size={15} /> Buy / Long
          </button>
          <button 
            type="button" 
            className={side === 'sell' ? 'active sell' : ''} 
            onClick={() => { setSide('sell'); setErrorMsg(''); setSuccessMsg(''); }}
          >
            <ArrowUpRight size={15} /> Sell / Short
          </button>
        </div>

        {/* Market Selector */}
        <div className="form-group">
          <label>Trading Pair</label>
          <div className="market-select-wrap">
            <select 
              value={selectedSymbol} 
              onChange={e => {
                const s = e.target.value as MarketSymbol;
                setSelectedSymbol(s);
                if (markets[s]) setLimitPrice(markets[s].price.toFixed(2));
              }}
            >
              <option value="BTC-USD">BTC-USD · Bitcoin (${markets['BTC-USD']?.price.toLocaleString()})</option>
              <option value="ETH-USD">ETH-USD · Ethereum (${markets['ETH-USD']?.price.toLocaleString()})</option>
              <option value="SOL-USD">SOL-USD · Solana (${markets['SOL-USD']?.price.toLocaleString()})</option>
            </select>
          </div>
        </div>

        {/* Order Type & Price */}
        <div className="form-row-2">
          <div className="form-group">
            <label>Order Type</label>
            <select value={type} onChange={e => setType(e.target.value as 'market' | 'limit')}>
              <option value="market">Market (Instant Fill)</option>
              <option value="limit">Limit Order</option>
            </select>
          </div>

          <div className="form-group">
            <label>{type === 'limit' ? 'Limit Price (USD)' : 'Market Price (USD)'}</label>
            {type === 'limit' ? (
              <div className="input-with-symbol">
                <span className="prefix">$</span>
                <input 
                  type="number" 
                  step="0.01" 
                  min="0.01" 
                  value={limitPrice} 
                  onChange={e => setLimitPrice(e.target.value)} 
                  required 
                />
              </div>
            ) : (
              <div className="static-field">
                ${marketPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            )}
          </div>
        </div>

        {/* Available Paper Balance Display */}
        <div className="balance-info-strip">
          <div className="balance-info-left">
            <Wallet size={14} className="muted" />
            <span className="muted">
              {side === 'buy' ? 'Available Paper Cash:' : `Available ${asset}:`}
            </span>
          </div>
          <strong className={side === 'buy' ? 'green-text' : 'blue-text'}>
            {side === 'buy' 
              ? `$${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}` 
              : `${currentHolding.quantity.toFixed(4)} ${asset}`
            }
          </strong>
        </div>

        {/* Quantity Field */}
        <div className="form-group">
          <div className="label-with-action">
            <label>Quantity ({asset})</label>
            <span className="tiny-label muted">
              {side === 'buy' 
                ? `Max affordable: ${maxBuyQuantity.toFixed(4)} ${asset}` 
                : `Holding: ${maxSellQuantity.toFixed(4)} ${asset}`
              }
            </span>
          </div>
          <input 
            type="number" 
            min="0.000001" 
            step="any" 
            value={quantity} 
            onChange={e => {
              setQuantity(e.target.value);
              setErrorMsg('');
              setSuccessMsg('');
            }} 
            required 
          />
        </div>

        {/* Quick Percent Buttons */}
        <div className="pct-buttons">
          <button type="button" onClick={() => handlePercentage(25)}>25%</button>
          <button type="button" onClick={() => handlePercentage(50)}>50%</button>
          <button type="button" onClick={() => handlePercentage(75)}>75%</button>
          <button type="button" onClick={() => handlePercentage(100)}>100% (MAX)</button>
        </div>

        {/* Real-Time Cost & Cash Impact Preview */}
        <div className="order-summary-box">
          <div className="summary-line">
            <span>Estimated Total:</span>
            <strong>${estimatedTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
          </div>
          <div className="summary-line">
            <span>Trading Fee (Paper):</span>
            <span className="free-badge">FREE (0.00%)</span>
          </div>
          <div className="summary-line highlight">
            <span>{side === 'buy' ? 'Paper Cash After Buy:' : 'Paper Cash After Sell:'}</span>
            <strong className={side === 'buy' ? (isInsufficientBuyFunds ? 'red-text' : '') : 'green-text'}>
              ${(side === 'buy' ? remainingCashIfBuy : newCashIfSell).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </strong>
          </div>
        </div>

        {/* Error or Success feedback */}
        {errorMsg && (
          <div className="form-alert error" role="alert">
            <AlertCircle size={15} />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="form-alert success" role="status">
            <CheckCircle2 size={15} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Action Button */}
        <button 
          type="submit" 
          className={`submit-order ${side}`} 
          disabled={busy || isInsufficientBuyFunds || isInsufficientSellBalance || parsedQty <= 0}
        >
          {busy 
            ? 'Executing zero-copy match…' 
            : isInsufficientBuyFunds 
              ? 'Insufficient Paper Cash' 
              : isInsufficientSellBalance 
                ? `Insufficient ${asset} Balance` 
                : `Place ${side.toUpperCase()} Paper Order`
          }
        </button>

        <p className="fine-print">
          Paper Trading Execution: Instant zero-copy matching simulation. Paper money and portfolio balances update live.
        </p>
      </form>
    </Panel>
  );
}
