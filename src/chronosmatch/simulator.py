"""End-to-end ChronosMatch demonstration pipeline."""

import statistics
import time
from pathlib import Path

from .ledger import TradeLedger
from .matching_engine import OrderBook
from .order_format import BUY, SELL, Order
from .ring_buffer import MmapRingBuffer


def sample_orders() -> list[Order]:
    """A deterministic scenario with two executions."""
    return [
        Order(1, BUY, 101, 5, 1_000),
        Order(2, SELL, 100, 3, 2_000),
        Order(3, SELL, 101, 4, 3_000),
    ]


def run_simulation(
    db_path: str | Path,
    ring_path: str | Path,
    orders: list[Order] | None = None,
) -> dict:
    orders = sample_orders() if orders is None else orders
    book = OrderBook()
    latencies_ns: list[int] = []
    executed_trades = 0

    with TradeLedger(db_path) as ledger:
        with MmapRingBuffer(ring_path, capacity=max(2, len(orders))) as ring:
            # Producer: place fixed-size binary records into the ring.
            for order in orders:
                ring.put(order)

            # Consumer: decode records, match orders, persist executions.
            while True:
                order = ring.get()
                if order is None:
                    break

                start_ns = time.perf_counter_ns()
                trades = book.submit_order(order)
                elapsed_ns = time.perf_counter_ns() - start_ns

                latencies_ns.append(elapsed_ns)
                ledger.record_trades(trades)
                executed_trades += len(trades)

        stored_trades = ledger.count_trades()

    return {
        "orders_processed": len(orders),
        "trades_executed": executed_trades,
        "trades_stored": stored_trades,
        "best_bid": book.best_bid,
        "best_ask": book.best_ask,
        "latency_mean_ns": (
            round(statistics.mean(latencies_ns)) if latencies_ns else 0
        ),
        "latency_max_ns": max(latencies_ns, default=0),
        "latency_samples_ns": latencies_ns,
        "resting_order_count": book.resting_order_count,
        "resting_orders": book.resting_orders,
    }