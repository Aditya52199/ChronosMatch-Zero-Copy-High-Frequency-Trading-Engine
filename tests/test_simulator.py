import sqlite3

from chronosmatch.simulator import run_simulation


def test_simulation_processes_and_persists_trades(tmp_path):
    db_path = tmp_path / "trades.db"
    ring_path = tmp_path / "ring.bin"

    result = run_simulation(db_path, ring_path)

    assert result["orders_processed"] == 3
    assert result["trades_executed"] == 2
    assert result["trades_stored"] == 2
    assert result["latency_mean_ns"] > 0
    assert result["latency_max_ns"] > 0

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT buy_order_id, sell_order_id, price_ticks, quantity "
            "FROM trades ORDER BY id"
        ).fetchall()

    assert rows == [
        (1, 2, 101, 3),
        (1, 3, 101, 2),
    ]