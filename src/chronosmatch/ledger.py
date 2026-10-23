"""SQLite persistence for executed trades."""

import sqlite3
from pathlib import Path

from .matching_engine import Trade


class TradeLedger:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(str(path))
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buy_order_id INTEGER NOT NULL,
                sell_order_id INTEGER NOT NULL,
                price_ticks INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL
            )
        """)
        self.connection.commit()

    def record_trades(self, trades: list[Trade]) -> None:
        self.connection.executemany(
            """
            INSERT INTO trades (
                buy_order_id, sell_order_id, price_ticks,
                quantity, timestamp_ns
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    trade.buy_order_id,
                    trade.sell_order_id,
                    trade.price_ticks,
                    trade.quantity,
                    trade.timestamp_ns,
                )
                for trade in trades
            ],
        )
        self.connection.commit()

    def get_trades(self) -> list[tuple]:
        cursor = self.connection.execute("""
            SELECT buy_order_id, sell_order_id, price_ticks,
                   quantity, timestamp_ns
            FROM trades ORDER BY id
        """)
        return cursor.fetchall()

    def count_trades(self) -> int:
        return self.connection.execute(
            "SELECT COUNT(*) FROM trades"
        ).fetchone()[0]

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()