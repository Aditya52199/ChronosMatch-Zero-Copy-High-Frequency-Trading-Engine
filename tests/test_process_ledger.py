
import sqlite3

import pytest

from chronosmatch.order_format import BUY, SELL, Order
from chronosmatch.process_ledger import run_process_ledger_simulation


def test_separate_process_persists_all_whale_sweep_trades(tmp_path):
    db_path = tmp_path / "process_ledger.db"
    ring_path = tmp_path / "trades.ring"

    # Two resting sell levels; the incoming buy clears both.
    orders = [
        Order(1, SELL, 101, 2, 1_000),
        Order(2, SELL, 102, 3, 2_000),
        Order(3, BUY, 102, 4, 3_000),
    ]

    result = run_process_ledger_simulation(
        db_path=db_path,
        ring_path=ring_path,
        orders=orders,
        capacity=2,
        batch_size=2,
    )

    assert result["orders_processed"] == 3
    assert result["trades_executed"] == 2
    assert result["trades_stored"] == 2
    assert result["ledger_process_exitcode"] == 0
    assert result["best_ask"] == 102
    assert result["resting_order_count"] == 1

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT buy_order_id, sell_order_id, price_ticks, quantity
            FROM trades ORDER BY id
            """
        ).fetchall()

    assert rows == [
        (3, 1, 101, 2),
        (3, 2, 102, 2),
    ]


def test_separate_process_handles_no_orders(tmp_path):
    result = run_process_ledger_simulation(
        db_path=tmp_path / "empty.db",
        ring_path=tmp_path / "empty.ring",
        orders=[],
        capacity=2,
        batch_size=2,
    )

    assert result["orders_processed"] == 0
    assert result["trades_executed"] == 0
    assert result["trades_stored"] == 0
    assert result["ledger_process_exitcode"] == 0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"capacity": 0}, "capacity"),
        ({"batch_size": 0}, "batch_size"),
        ({"join_timeout_seconds": 0}, "join_timeout"),
    ],
)
def test_rejects_invalid_configuration(tmp_path, kwargs, message):
    with pytest.raises(ValueError, match=message):
        run_process_ledger_simulation(
            db_path=tmp_path / "invalid.db",
            ring_path=tmp_path / "invalid.ring",
            orders=[],
            **kwargs,
        )
