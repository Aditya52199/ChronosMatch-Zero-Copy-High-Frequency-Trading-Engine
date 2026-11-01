
import asyncio
import sqlite3

import pytest

from chronosmatch.async_ledger import AsyncTradeLedger
from chronosmatch.matching_engine import Trade


def make_trade(i):
    return Trade(
        buy_order_id=i,
        sell_order_id=i + 1000,
        price_ticks=100 + i,
        quantity=2,
        timestamp_ns=1_000_000 + i,
    )


def test_async_ledger_persists_all_trades_on_close(tmp_path):
    db_path = tmp_path / "async_trades.db"

    async def scenario():
        async with AsyncTradeLedger(
            db_path,
            batch_size=16,
            queue_capacity=32,
        ) as ledger:
            await ledger.record_trades([make_trade(i) for i in range(1, 101)])
            await ledger.flush()

    asyncio.run(scenario())

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT buy_order_id, sell_order_id, price_ticks,
                   quantity, timestamp_ns
            FROM trades ORDER BY id
            """
        ).fetchall()

    assert len(rows) == 100
    assert rows[0] == (1, 1001, 101, 2, 1_000_001)
    assert rows[-1] == (100, 1100, 200, 2, 1_000_100)


def test_async_ledger_flushes_before_context_exit(tmp_path):
    db_path = tmp_path / "flush_on_exit.db"

    async def scenario():
        async with AsyncTradeLedger(db_path, batch_size=8) as ledger:
            await ledger.record_trades([make_trade(i) for i in range(1, 6)])

    asyncio.run(scenario())

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM trades"
        ).fetchone()[0]

    assert count == 5


def test_async_ledger_rejects_invalid_batch_size(tmp_path):
    with pytest.raises(ValueError, match="batch_size"):
        AsyncTradeLedger(tmp_path / "invalid.db", batch_size=0)
