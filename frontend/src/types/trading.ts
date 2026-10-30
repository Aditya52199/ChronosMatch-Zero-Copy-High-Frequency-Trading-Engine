export type MarketSymbol = 'BTC-USD' | 'ETH-USD' | 'SOL-USD';

export interface MarketInfo {
  symbol: MarketSymbol;
  name: string;
  asset: string;
  price: number;
  prevPrice: number;
  change: number;
  changeAmount: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  history: number[];
}

export interface HoldingPosition {
  asset: string;
  symbol: MarketSymbol;
  quantity: number;
  avgCost: number;
  totalCost: number;
}

export type OrderSide = 'buy' | 'sell';
export type OrderType = 'market' | 'limit';
export type OrderStatus = 'filled' | 'pending' | 'cancelled';

export interface PaperOrder {
  id: string;
  symbol: MarketSymbol;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price: number;
  total: number;
  timestamp: number;
  status: OrderStatus;
  note?: string;
}

export interface Transaction {
  id: string;
  timestamp: number;
  type: 'BUY' | 'SELL' | 'DEPOSIT' | 'RESET';
  symbol?: MarketSymbol;
  asset?: string;
  quantity?: number;
  price?: number;
  total: number;
  fee: number;
  realizedPnL?: number;
  note?: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  description: string;
  timestamp: number;
}
