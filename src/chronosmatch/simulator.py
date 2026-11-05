
import random
from .order_format import BUY, SELL, Order
"""End-to-end ChronosMatch demonstration pipeline."""

import statistics
import time
from pathlib import Path
import asyncio

from .async_ledger import AsyncTradeLedger
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


def generate_random_orders(
    count: int = 100,
    seed: int | None = None,
    base_price: int = 100,
) -> list[Order]:
    """Generate a varied order flow for interactive demonstrations.

    Supply a seed to reproduce a specific order sequence.
    Leave seed as None for a different sequence on each run.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    if base_price < 6:
        raise ValueError("base_price must be at least 6")

    rng = random.Random(seed)
    orders = []

    for order_id in range(1, count + 1):
        side = rng.choice([BUY, SELL])
        price = base_price + rng.randint(-5, 5)
        quantity = rng.randint(1, 10)
        timestamp = order_id * 1_000

        orders.append(
            Order(
                order_id,
                side,
                price,
                quantity,
                timestamp,
            )
        )

    return orders

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


async def run_async_simulation(
    db_path: str | Path,
    ring_path: str | Path,
    orders=None,
    batch_size: int = 256,
    queue_capacity: int = 8192,
) -> dict:
    """Run matching with asynchronously batched SQLite persistence.

    Matching is performed in the current asyncio task. Completed trades
    are queued for a background writer thread; SQLite commits do not run
    inside the matching loop.
    """
    orders = sample_orders() if orders is None else orders

    book = OrderBook()
    latencies_ns = []
    executed_trades = 0

    async with AsyncTradeLedger(
        db_path,
        batch_size=batch_size,
        queue_capacity=queue_capacity,
    ) as ledger:
        with MmapRingBuffer(
            ring_path,
            capacity=max(2, len(orders)),
        ) as ring:
            for order in orders:
                ring.put(order)

            while True:
                order = ring.get()
                if order is None:
                    break

                start_ns = time.perf_counter_ns()
                trades = book.submit_order(order)
                elapsed_ns = time.perf_counter_ns() - start_ns

                latencies_ns.append(elapsed_ns)
                executed_trades += len(trades)

                if trades:
                    await ledger.record_trades(trades)

        # Ensure queued trades have been committed before reading results.
        await ledger.flush()

    # Open the database after the async ledger has closed its connection.
    with TradeLedger(db_path) as read_ledger:
        stored_trades = read_ledger.count_trades()

    return {
        "orders_processed": len(orders),
        "trades_executed": executed_trades,
        "trades_stored": stored_trades,
        "best_bid": book.best_bid,
        "best_ask": book.best_ask,
        "latency_mean_ns": (
            int(statistics.mean(latencies_ns)) if latencies_ns else 0
        ),
        "latency_max_ns": max(latencies_ns, default=0),
        "latency_samples_ns": latencies_ns,
        "resting_order_count": book.resting_order_count,
        "resting_orders": book.resting_orders,
    }
