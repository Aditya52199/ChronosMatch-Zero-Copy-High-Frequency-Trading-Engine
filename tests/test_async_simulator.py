
import asyncio
import sqlite3

from chronosmatch.simulator import (
    run_async_simulation,
    sample_orders,
)


def test_async_simulation_persists_all_trades(tmp_path):
    db_path = tmp_path / "async_simulation.db"
    ring_path = tmp_path / "async_simulation.ring"

    result = asyncio.run(
        run_async_simulation(
            db_path=db_path,
            ring_path=ring_path,
            orders=sample_orders(),
            batch_size=2,
            queue_capacity=8,
        )
    )

    assert result["orders_processed"] == 3
    assert result["trades_executed"] == 2
    assert result["trades_stored"] == 2

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT buy_order_id, sell_order_id, price_ticks, quantity
            FROM trades
            ORDER BY id
            """
        ).fetchall()

    assert len(rows) == 2
    assert all(row[3] > 0 for row in rows)


def test_async_simulation_handles_no_orders(tmp_path):
    result = asyncio.run(
        run_async_simulation(
            db_path=tmp_path / "empty.db",
            ring_path=tmp_path / "empty.ring",
            orders=[],
        )
    )

    assert result["orders_processed"] == 0
    assert result["trades_executed"] == 0
    assert result["trades_stored"] == 0
