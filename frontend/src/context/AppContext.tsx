import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { MarketInfo, MarketSymbol, HoldingPosition, PaperOrder, Transaction, ToastMessage, OrderSide, OrderType } from '../types/trading';
import { submitPaperOrder } from '../api/client';

const STORAGE_KEY = 'chronos_paper_trading_state_v2';
const INITIAL_CASH = 25000.00;

const INITIAL_MARKETS: Record<MarketSymbol, MarketInfo> = {
  'BTC-USD': {
    symbol: 'BTC-USD',
    name: 'Bitcoin',
    asset: 'BTC',
    price: 67250.25,
    prevPrice: 67250.25,
    change: 1.84,
    changeAmount: 1215.40,
    high24h: 68140.00,
    low24h: 65920.00,
    volume24h: 28412.50,
    history: [66800, 66920, 66850, 67010, 67150, 67080, 67220, 67190, 67310, 67250.25],
  },
  'ETH-USD': {
    symbol: 'ETH-USD',
    name: 'Ethereum',
    asset: 'ETH',
    price: 3520.45,
    prevPrice: 3520.45,
    change: -0.62,
    changeAmount: -22.10,
    high24h: 3590.00,
    low24h: 3480.00,
    volume24h: 142850.00,
    history: [3560, 3545, 3550, 3530, 3515, 3525, 3510, 3518, 3522, 3520.45],
  },
  'SOL-USD': {
    symbol: 'SOL-USD',
    name: 'Solana',
    asset: 'SOL',
    price: 148.60,
    prevPrice: 148.60,
    change: 2.75,
    changeAmount: 3.98,
    high24h: 152.40,
    low24h: 142.10,
    volume24h: 624100.00,
    history: [144.2, 145.1, 144.8, 146.3, 147.0, 146.5, 147.8, 148.2, 148.4, 148.60],
  },
};

export type ActiveTab = 'terminal' | 'wallet' | 'orders';

interface AppContextType {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  selectedSymbol: MarketSymbol;
  setSelectedSymbol: (symbol: MarketSymbol) => void;
  markets: Record<MarketSymbol, MarketInfo>;
  marketList: MarketInfo[];
  currentMarket: MarketInfo;
  
  // Paper Wallet & Portfolio
  cashBalance: number;
  holdings: Record<string, HoldingPosition>;
  transactions: Transaction[];
  orders: PaperOrder[];
  toasts: ToastMessage[];
  removeToast: (id: string) => void;
  
  // Computed Portfolio Metrics
  portfolioTotalValue: number;
  totalUnrealizedPnL: number;
  totalUnrealizedPnLPercent: number;
  totalRealizedPnL: number;
  totalInvested: number;
  
  // Actions
  executePaperOrder: (params: {
    symbol: MarketSymbol;
    side: OrderSide;
    type: OrderType;
    quantity: number;
    limitPrice?: number;
  }) => Promise<{ order: PaperOrder; message: string }>;
  
  depositPaperCash: (amount: number) => void;
  resetPaperWallet: () => void;
  isRealTimeActive: boolean;
  setIsRealTimeActive: (active: boolean) => void;
  lastTickTime: number;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('terminal');
  const [selectedSymbol, setSelectedSymbol] = useState<MarketSymbol>('BTC-USD');
  const [markets, setMarkets] = useState<Record<MarketSymbol, MarketInfo>>(INITIAL_MARKETS);
  const [isRealTimeActive, setIsRealTimeActive] = useState<boolean>(true);
  const [lastTickTime, setLastTickTime] = useState<number>(Date.now());
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Load persistent wallet state
  const [cashBalance, setCashBalance] = useState<number>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (typeof parsed.cashBalance === 'number' && !isNaN(parsed.cashBalance)) {
          return parsed.cashBalance;
        }
      }
    } catch {}
    return INITIAL_CASH;
  });

  const [holdings, setHoldings] = useState<Record<string, HoldingPosition>>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.holdings) return parsed.holdings;
      }
    } catch {}
    return {
      BTC: { asset: 'BTC', symbol: 'BTC-USD', quantity: 0, avgCost: 0, totalCost: 0 },
      ETH: { asset: 'ETH', symbol: 'ETH-USD', quantity: 0, avgCost: 0, totalCost: 0 },
      SOL: { asset: 'SOL', symbol: 'SOL-USD', quantity: 0, avgCost: 0, totalCost: 0 },
    };
  });

  const [transactions, setTransactions] = useState<Transaction[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed.transactions)) return parsed.transactions;
      }
    } catch {}
    return [
      {
        id: 'tx-init',
        timestamp: Date.now() - 3600000,
        type: 'DEPOSIT',
        total: INITIAL_CASH,
        fee: 0,
        note: 'Initial paper trading simulation grant',
      },
    ];
  });

  const [orders, setOrders] = useState<PaperOrder[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed.orders)) return parsed.orders;
      }
    } catch {}
    return [];
  });

  // Save wallet state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        cashBalance,
        holdings,
        transactions,
        orders,
      }));
    } catch (e) {
      console.warn('Failed to persist paper trading state', e);
    }
  }, [cashBalance, holdings, transactions, orders]);

  // Toast Helper
  const addToast = (type: ToastMessage['type'], title: string, description: string) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    const newToast: ToastMessage = { id, type, title, description, timestamp: Date.now() };
    setToasts(prev => [newToast, ...prev.slice(0, 4)]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  // Real-Time Market Price Generator (Micro-ticks simulation)
  useEffect(() => {
    if (!isRealTimeActive) return;

    const interval = setInterval(() => {
      setMarkets(prev => {
        const next: Record<MarketSymbol, MarketInfo> = { ...prev };
        const symbols: MarketSymbol[] = ['BTC-USD', 'ETH-USD', 'SOL-USD'];

        symbols.forEach(sym => {
          const current = prev[sym];
          // Volatility scale proportional to price
          const vol = sym === 'BTC-USD' ? 14 : sym === 'ETH-USD' ? 1.2 : 0.12;
          const randomDelta = (Math.random() - 0.495) * vol;
          const newPrice = Math.max(1, Number((current.price + randomDelta).toFixed(sym === 'SOL-USD' ? 2 : 2)));
          
          const changeAmount = newPrice - (current.price - current.changeAmount);
          const changePercent = Number(((changeAmount / (newPrice - changeAmount)) * 100).toFixed(2));
          const high24h = Math.max(current.high24h, newPrice);
          const low24h = Math.min(current.low24h, newPrice);
          const volumeDelta = Math.random() * (sym === 'BTC-USD' ? 0.4 : sym === 'ETH-USD' ? 2 : 8);

          const updatedHistory = [...current.history.slice(-35), newPrice];

          next[sym] = {
            ...current,
            prevPrice: current.price,
            price: newPrice,
            change: changePercent,
            changeAmount: Number(changeAmount.toFixed(2)),
            high24h,
            low24h,
            volume24h: Number((current.volume24h + volumeDelta).toFixed(2)),
            history: updatedHistory,
          };
        });

        return next;
      });
      setLastTickTime(Date.now());
    }, 900);

    return () => clearInterval(interval);
  }, [isRealTimeActive]);

  // Derived metrics
  const marketList = useMemo(() => Object.values(markets), [markets]);
  const currentMarket = markets[selectedSymbol] || markets['BTC-USD'];

  // Portfolio calculation in real time
  const { portfolioTotalValue, totalUnrealizedPnL, totalUnrealizedPnLPercent, totalRealizedPnL, totalInvested } = useMemo(() => {
    let investedValue = 0;
    let currentMarketAssetsValue = 0;
    let totalCostBasis = 0;

    Object.values(holdings).forEach(h => {
      if (h.quantity > 0) {
        const currentPrice = markets[h.symbol]?.price ?? 0;
        const assetValue = h.quantity * currentPrice;
        currentMarketAssetsValue += assetValue;
        investedValue += h.totalCost;
        totalCostBasis += h.totalCost;
      }
    });

    const unrealized = currentMarketAssetsValue - totalCostBasis;
    const unrealizedPct = totalCostBasis > 0 ? (unrealized / totalCostBasis) * 100 : 0;
    const totalPortfolio = cashBalance + currentMarketAssetsValue;

    // Calculate realized P&L from transactions
    let realized = 0;
    transactions.forEach(t => {
      if (t.realizedPnL) {
        realized += t.realizedPnL;
      }
    });

    return {
      portfolioTotalValue: Number(totalPortfolio.toFixed(2)),
      totalUnrealizedPnL: Number(unrealized.toFixed(2)),
      totalUnrealizedPnLPercent: Number(unrealizedPct.toFixed(2)),
      totalRealizedPnL: Number(realized.toFixed(2)),
      totalInvested: Number(investedValue.toFixed(2)),
    };
  }, [cashBalance, holdings, markets, transactions]);

  // Execute Paper Order (Buy / Sell)
  const executePaperOrder = async ({
    symbol,
    side,
    type,
    quantity,
    limitPrice,
  }: {
    symbol: MarketSymbol;
    side: OrderSide;
    type: OrderType;
    quantity: number;
    limitPrice?: number;
  }) => {
    const market = markets[symbol];
    if (!market) throw new Error(`Market ${symbol} not recognized.`);
    if (quantity <= 0 || !Number.isFinite(quantity)) {
      throw new Error('Please enter a valid positive quantity.');
    }

    const executionPrice = type === 'limit' && limitPrice && limitPrice > 0 ? limitPrice : market.price;
    const grossTotal = Number((quantity * executionPrice).toFixed(2));
    const asset = market.asset;

    if (side === 'buy') {
      // Check if user has sufficient paper cash
      if (cashBalance < grossTotal) {
        const needed = grossTotal - cashBalance;
        const msg = `Insufficient paper funds! You need $${grossTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })} but only have $${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })} (Short by $${needed.toLocaleString(undefined, { minimumFractionDigits: 2 })}).`;
        addToast('error', 'Buy Order Rejected', msg);
        throw new Error(msg);
      }

      // Deduct paper money
      const nextCash = Number((cashBalance - grossTotal).toFixed(2));
      setCashBalance(nextCash);

      // Add to asset holdings
      const currentHolding = holdings[asset] || { asset, symbol, quantity: 0, avgCost: 0, totalCost: 0 };
      const newQuantity = Number((currentHolding.quantity + quantity).toFixed(6));
      const newTotalCost = Number((currentHolding.totalCost + grossTotal).toFixed(2));
      const newAvgCost = Number((newTotalCost / newQuantity).toFixed(2));

      setHoldings(prev => ({
        ...prev,
        [asset]: {
          asset,
          symbol,
          quantity: newQuantity,
          avgCost: newAvgCost,
          totalCost: newTotalCost,
        },
      }));

      // Record Order and Transaction
      const orderId = `PO-${Date.now().toString().slice(-6)}`;
      const newOrder: PaperOrder = {
        id: orderId,
        symbol,
        side: 'buy',
        type,
        quantity,
        price: executionPrice,
        total: grossTotal,
        timestamp: Date.now(),
        status: 'filled',
        note: `Paper Buy: -${grossTotal.toFixed(2)} USD, +${quantity} ${asset}`,
      };

      const newTx: Transaction = {
        id: `tx-${Date.now()}`,
        timestamp: Date.now(),
        type: 'BUY',
        symbol,
        asset,
        quantity,
        price: executionPrice,
        total: grossTotal,
        fee: 0,
        note: `Bought ${quantity} ${asset} at $${executionPrice.toLocaleString()} (-$${grossTotal.toFixed(2)} Paper Cash)`,
      };

      setOrders(prev => [newOrder, ...prev]);
      setTransactions(prev => [newTx, ...prev]);

      // Trigger Gateway sync in background if available
      submitPaperOrder({
        symbol,
        side,
        quantity,
        type,
        ...(type === 'limit' ? { limitPrice: executionPrice } : {}),
      }).catch(() => {
        // Gateway offline is completely expected in demo mode, engine maintains client simulation
      });

      const successMsg = `Purchased ${quantity} ${asset} for $${grossTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}. Paper Cash decreased to $${nextCash.toLocaleString(undefined, { minimumFractionDigits: 2 })}.`;
      addToast('success', 'Paper Order Filled', successMsg);
      return { order: newOrder, message: successMsg };
    } else {
      // SELL ORDER
      const currentHolding = holdings[asset] || { asset, symbol, quantity: 0, avgCost: 0, totalCost: 0 };
      if (currentHolding.quantity < quantity || currentHolding.quantity <= 0) {
        const msg = `Insufficient ${asset} balance! You only hold ${currentHolding.quantity.toFixed(4)} ${asset}, but tried to sell ${quantity} ${asset}.`;
        addToast('error', 'Sell Order Rejected', msg);
        throw new Error(msg);
      }

      // Add proceeds to paper cash
      const nextCash = Number((cashBalance + grossTotal).toFixed(2));
      setCashBalance(nextCash);

      // Calculate realized P&L on the sold portion
      const costOfSoldShare = currentHolding.avgCost * quantity;
      const realizedPnL = Number((grossTotal - costOfSoldShare).toFixed(2));

      // Reduce holding
      const newQuantity = Number(Math.max(0, currentHolding.quantity - quantity).toFixed(6));
      const newTotalCost = newQuantity > 0 ? Number((newQuantity * currentHolding.avgCost).toFixed(2)) : 0;
      const newAvgCost = newQuantity > 0 ? currentHolding.avgCost : 0;

      setHoldings(prev => ({
        ...prev,
        [asset]: {
          asset,
          symbol,
          quantity: newQuantity,
          avgCost: newAvgCost,
          totalCost: newTotalCost,
        },
      }));

      // Record Order & Transaction
      const orderId = `PO-${Date.now().toString().slice(-6)}`;
      const newOrder: PaperOrder = {
        id: orderId,
        symbol,
        side: 'sell',
        type,
        quantity,
        price: executionPrice,
        total: grossTotal,
        timestamp: Date.now(),
        status: 'filled',
        note: `Paper Sell: +${grossTotal.toFixed(2)} USD, -${quantity} ${asset}`,
      };

      const pnlSign = realizedPnL >= 0 ? `+$${realizedPnL.toFixed(2)}` : `-$${Math.abs(realizedPnL).toFixed(2)}`;
      const newTx: Transaction = {
        id: `tx-${Date.now()}`,
        timestamp: Date.now(),
        type: 'SELL',
        symbol,
        asset,
        quantity,
        price: executionPrice,
        total: grossTotal,
        fee: 0,
        realizedPnL,
        note: `Sold ${quantity} ${asset} at $${executionPrice.toLocaleString()} (+$${grossTotal.toFixed(2)} Paper Cash, Realized P&L: ${pnlSign})`,
      };

      setOrders(prev => [newOrder, ...prev]);
      setTransactions(prev => [newTx, ...prev]);

      // Gateway sync
      submitPaperOrder({
        symbol,
        side,
        quantity,
        type,
        ...(type === 'limit' ? { limitPrice: executionPrice } : {}),
      }).catch(() => {});

      const successMsg = `Sold ${quantity} ${asset} for $${grossTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}. Paper Cash increased to $${nextCash.toLocaleString(undefined, { minimumFractionDigits: 2 })}.`;
      addToast('success', 'Paper Order Filled', successMsg);
      return { order: newOrder, message: successMsg };
    }
  };

  // Deposit Paper Cash
  const depositPaperCash = (amount: number) => {
    if (amount <= 0 || !Number.isFinite(amount)) return;
    const nextCash = Number((cashBalance + amount).toFixed(2));
    setCashBalance(nextCash);

    const tx: Transaction = {
      id: `tx-${Date.now()}`,
      timestamp: Date.now(),
      type: 'DEPOSIT',
      total: amount,
      fee: 0,
      note: `Deposited $${amount.toLocaleString()} paper cash funds`,
    };
    setTransactions(prev => [tx, ...prev]);
    addToast('success', 'Paper Funds Deposited', `+$${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} added. New Balance: $${nextCash.toLocaleString(undefined, { minimumFractionDigits: 2 })}.`);
  };

  // Reset Paper Wallet
  const resetPaperWallet = () => {
    setCashBalance(INITIAL_CASH);
    setHoldings({
      BTC: { asset: 'BTC', symbol: 'BTC-USD', quantity: 0, avgCost: 0, totalCost: 0 },
      ETH: { asset: 'ETH', symbol: 'ETH-USD', quantity: 0, avgCost: 0, totalCost: 0 },
      SOL: { asset: 'SOL', symbol: 'SOL-USD', quantity: 0, avgCost: 0, totalCost: 0 },
    });
    setOrders([]);
    const resetTx: Transaction = {
      id: `tx-${Date.now()}`,
      timestamp: Date.now(),
      type: 'RESET',
      total: INITIAL_CASH,
      fee: 0,
      note: 'Reset paper wallet to initial $25,000.00 cash',
    };
    setTransactions([resetTx]);
    addToast('info', 'Paper Wallet Reset', 'Account reset to initial $25,000.00 paper cash and clean portfolio.');
  };

  const value = useMemo(
    () => ({
      activeTab,
      setActiveTab,
      selectedSymbol,
      setSelectedSymbol,
      markets,
      marketList,
      currentMarket,
      cashBalance,
      holdings,
      transactions,
      orders,
      toasts,
      removeToast,
      portfolioTotalValue,
      totalUnrealizedPnL,
      totalUnrealizedPnLPercent,
      totalRealizedPnL,
      totalInvested,
      executePaperOrder,
      depositPaperCash,
      resetPaperWallet,
      isRealTimeActive,
      setIsRealTimeActive,
      lastTickTime,
    }),
    [
      activeTab,
      selectedSymbol,
      markets,
      marketList,
      currentMarket,
      cashBalance,
      holdings,
      transactions,
      orders,
      toasts,
      portfolioTotalValue,
      totalUnrealizedPnL,
      totalUnrealizedPnLPercent,
      totalRealizedPnL,
      totalInvested,
      isRealTimeActive,
      lastTickTime,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used inside an AppProvider');
  }
  return context;
}
