CREATE TABLE IF NOT EXISTS wallets (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  asset TEXT NOT NULL,
  available NUMERIC(28, 10) NOT NULL DEFAULT 0 CHECK (available >= 0),
  locked NUMERIC(28, 10) NOT NULL DEFAULT 0 CHECK (locked >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, asset)
);
