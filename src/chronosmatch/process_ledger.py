
"""Separate-process SQLite writer using a binary mmap trade ring.

Trade records travel through mmap, not multiprocessing.Queue or pickle.
A process-shared lock protects ring metadata and record access.
SQLite writes and commits happen only in the ledger process.
"""

from __future__ import annotations

import mmap
import multiprocessing as mp
import os
import queue
import sqlite3
import struct
import tempfile
import time
from pathlib import Path

from .matching_engine import OrderBook, Trade
from .order_format import BUY, SELL, Order


_HEADER = struct.Struct("!QQ")
_HEADER_SIZE = _HEADER.size

# buy_order_id, sell_order_id, price_ticks, quantity, timestamp_ns
_TRADE_RECORD = struct.Struct("!QQQIQ")
TRADE_RECORD_SIZE = _TRADE_RECORD.size


def _initialize_trade_file(path: str, capacity: int) -> None:
    with open(path, "w+b") as file:
        file.truncate(_HEADER_SIZE + capacity * TRADE_RECORD_SIZE)
        with mmap.mmap(file.fileno(), 0) as mapped:
            _HEADER.pack_into(mapped, 0, 0, 0)
            mapped.flush()


class MmapTradeRingBuffer:
    """Single-producer/single-consumer ring with externally shared locking."""

    def __init__(
        self,
        path: str | Path,
        capacity: int,
        lock,
        *,
        initialize: bool = False,
    ):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")

        self.path = str(path)
        self.capacity = capacity
        self.lock = lock

        if initialize:
            _initialize_trade_file(self.path, capacity)

        self._file = open(self.path, "r+b")
        self._map = mmap.mmap(self._file.fileno(), 0)
        self._closed = False

    def put(self, trade: Trade, consumer_process=None) -> None:
        """Block when full, while detecting a failed consumer process."""
        record = _TRADE_RECORD.pack(
            trade.buy_order_id,
            trade.sell_order_id,
            trade.price_ticks,
            trade.quantity,
            trade.timestamp_ns,
        )

        while True:
            with self.lock:
                write_pos, read_pos = _HEADER.unpack_from(self._map, 0)

                if write_pos - read_pos < self.capacity:
                    slot = write_pos % self.capacity
                    offset = _HEADER_SIZE + slot * TRADE_RECORD_SIZE
                    self._map[offset : offset + TRADE_RECORD_SIZE] = record
                    _HEADER.pack_into(
                        self._map, 0, write_pos + 1, read_pos
                    )
                    return

            if consumer_process is not None and not consumer_process.is_alive():
                raise RuntimeError(
                    "Ledger process exited while the trade ring was full"
                )

            time.sleep(0.0001)

    def get(self) -> Trade | None:
        """Read one record; return None if no record is currently available."""
        with self.lock:
            write_pos, read_pos = _HEADER.unpack_from(self._map, 0)

            if read_pos == write_pos:
                return None

            slot = read_pos % self.capacity
            offset = _HEADER_SIZE + slot * TRADE_RECORD_SIZE
            values = _TRADE_RECORD.unpack_from(self._map, offset)

            _HEADER.pack_into(
                self._map, 0, write_pos, read_pos + 1
            )

        return Trade(
            buy_order_id=values[0],
            sell_order_id=values[1],
            price_ticks=values[2],
            quantity=values[3],
            timestamp_ns=values[4],
        )

    def close(self) -> None:
        if not self._closed:
            self._map.close()
            self._file.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def _ledger_process(
    ring_path: str,
    capacity: int,
    lock,
    producer_done,
    result_queue,
    db_path: str,
    batch_size: int,
) -> None:
    """Child-process entry point. SQLite is owned by this process."""
    connection = None

    try:
        connection = sqlite3.connect(db_path)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buy_order_id INTEGER NOT NULL,
                sell_order_id INTEGER NOT NULL,
                price_ticks INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL
            )
        """)
        connection.commit()

        persisted = 0
        batch = []

        with MmapTradeRingBuffer(ring_path, capacity, lock) as ring:
            while True:
                trade = ring.get()

                if trade is None:
                    if producer_done.is_set():
                        break
                    time.sleep(0.0001)
                    continue

                batch.append(trade)

                if len(batch) >= batch_size:
                    connection.executemany(
                        """
                        INSERT INTO trades (
                            buy_order_id, sell_order_id, price_ticks,
                            quantity, timestamp_ns
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                item.buy_order_id,
                                item.sell_order_id,
                                item.price_ticks,
                                item.quantity,
                                item.timestamp_ns,
                            )
                            for item in batch
                        ],
                    )
                    connection.commit()
                    persisted += len(batch)
                    batch.clear()

        if batch:
            connection.executemany(
                """
                INSERT INTO trades (
                    buy_order_id, sell_order_id, price_ticks,
                    quantity, timestamp_ns
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.buy_order_id,
                        item.sell_order_id,
                        item.price_ticks,
                        item.quantity,
                        item.timestamp_ns,
                    )
                    for item in batch
                ],
            )
            connection.commit()
            persisted += len(batch)

        result_queue.put(("ok", persisted))

    except BaseException as exc:
        if connection is not None:
            connection.rollback()
        result_queue.put(("error", repr(exc)))
        raise

    finally:
        if connection is not None:
            connection.close()


def run_process_ledger_simulation(
    db_path: str | Path,
    ring_path: str | Path | None = None,
    orders: list[Order] | None = None,
    *,
    capacity: int = 1024,
    batch_size: int = 256,
    join_timeout_seconds: float = 60.0,
) -> dict:
    """Match orders in the caller and persist trades in a separate process.

    The returned latency measurements cover only OrderBook.submit_order().
    End-to-end elapsed time includes process startup and ledger persistence.
    """
    if capacity < 1:
        raise ValueError("capacity must be at least 1")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if join_timeout_seconds <= 0:
        raise ValueError("join_timeout_seconds must be positive")

    if orders is None:
        orders = [
            Order(1, BUY, 101, 5, 1_000),
            Order(2, SELL, 100, 3, 2_000),
            Order(3, SELL, 101, 4, 3_000),
        ]

    db_path = str(db_path)
    owned_ring_path = ring_path is None

    if owned_ring_path:
        fd, ring_path = tempfile.mkstemp(
            prefix="chronosmatch_trade_", suffix=".ring"
        )
        os.close(fd)

    ring_path = str(ring_path)
    ctx = mp.get_context("spawn")
    lock = ctx.Lock()
    producer_done = ctx.Event()
    result_queue = ctx.Queue()
    process = None
    started_ns = time.perf_counter_ns()
    latencies_ns = []
    executed_trades = 0
    processed_orders = 0

    try:
        with MmapTradeRingBuffer(
            ring_path, capacity, lock, initialize=True
        ) as ring:
            process = ctx.Process(
                target=_ledger_process,
                args=(
                    ring_path,
                    capacity,
                    lock,
                    producer_done,
                    result_queue,
                    db_path,
                    batch_size,
                ),
                name="chronosmatch-sqlite-ledger",
            )
            process.start()

            book = OrderBook()

            for order in orders:
                start_ns = time.perf_counter_ns()
                trades = book.submit_order(order)
                latencies_ns.append(time.perf_counter_ns() - start_ns)
                processed_orders += 1
                executed_trades += len(trades)

                for trade in trades:
                    ring.put(trade, consumer_process=process)

            # The child drains all remaining records before exiting.
            producer_done.set()
            process.join(timeout=join_timeout_seconds)

            if process.is_alive():
                process.terminate()
                process.join()
                raise TimeoutError(
                    "Ledger process did not finish before the timeout"
                )

            try:
                status, value = result_queue.get(timeout=5)
            except queue.Empty as exc:
                raise RuntimeError(
                    f"Ledger process returned no result "
                    f"(exit code {process.exitcode})"
                ) from exc

            if process.exitcode != 0 or status != "ok":
                raise RuntimeError(f"Ledger process failed: {value}")

            persisted_trades = value

        elapsed_ns = time.perf_counter_ns() - started_ns

        if persisted_trades != executed_trades:
            raise RuntimeError(
                f"Trade persistence mismatch: executed={executed_trades}, "
                f"persisted={persisted_trades}"
            )

        return {
            "orders_processed": processed_orders,
            "trades_executed": executed_trades,
            "trades_stored": persisted_trades,
            "best_bid": book.best_bid,
            "best_ask": book.best_ask,
            "resting_order_count": book.resting_order_count,
            "resting_orders": book.resting_orders,
            "latency_samples_ns": latencies_ns,
            "latency_mean_ns": (
                round(sum(latencies_ns) / len(latencies_ns))
                if latencies_ns else 0
            ),
            "latency_max_ns": max(latencies_ns, default=0),
            "elapsed_ns": elapsed_ns,
            "end_to_end_orders_per_second": (
                processed_orders / (elapsed_ns / 1_000_000_000)
                if elapsed_ns else 0
            ),
            "ledger_process_exitcode": process.exitcode,
        }

    finally:
        producer_done.set()

        if process is not None and process.is_alive():
            process.terminate()
            process.join()

        result_queue.close()
        result_queue.join_thread()

        if owned_ring_path:
            Path(ring_path).unlink(missing_ok=True)
