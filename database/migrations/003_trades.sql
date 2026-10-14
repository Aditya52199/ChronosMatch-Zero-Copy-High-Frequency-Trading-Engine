CREATE TABLE IF NOT EXISTS trades (
  id BIGSERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,
  buy_order_id TEXT NOT NULL,
  sell_order_id TEXT NOT NULL,
  price NUMERIC(28, 10) NOT NULL CHECK (price > 0),
  quantity NUMERIC(28, 10) NOT NULL CHECK (quantity > 0),
  executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
