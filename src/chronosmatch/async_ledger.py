
"""Asynchronous, batched SQLite persistence for executed trades."""

import asyncio
import sqlite3
from pathlib import Path

from .matching_engine import Trade


class AsyncTradeLedger:
    """Queue trades and persist them in batches on a background task.

    SQLite writes run in a worker thread so they do not block the asyncio
    event loop. Call close() or use the async context manager to flush
    queued trades before shutting down.
    """

    def __init__(
        self,
        path: str | Path,
        batch_size: int = 256,
        queue_capacity: int = 8192,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if queue_capacity <= 0:
            raise ValueError("queue_capacity must be positive")

        self.path = str(path)
        self.batch_size = batch_size
        self._queue = asyncio.Queue(maxsize=queue_capacity)
        self._connection = None
        self._worker_task = None
        self._closed = False
        self._worker_error = None

    async def __aenter__(self):
        if self._worker_task is not None:
            raise RuntimeError("Ledger has already been started")
        if self._closed:
            raise RuntimeError("Ledger is closed")

        self._connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
        )
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buy_order_id INTEGER NOT NULL,
                sell_order_id INTEGER NOT NULL,
                price_ticks INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL
            )
        """)
        self._connection.commit()

        self._worker_task = asyncio.create_task(self._run_worker())
        return self

    async def record_trades(self, trades: list[Trade]) -> None:
        """Queue executed trades without waiting for SQLite commits."""
        if self._closed or self._worker_task is None:
            raise RuntimeError("Ledger is not running")

        if self._worker_error is not None:
            raise RuntimeError("Ledger worker failed") from self._worker_error

        for trade in trades:
            await self._queue.put(trade)

    def _write_batch(self, trades: list[Trade]) -> None:
        """Write one batch. Called only by the background worker."""
        self._connection.executemany(
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
        self._connection.commit()

    async def _run_worker(self) -> None:
        try:
            stopping = False

            while not stopping:
                first = await self._queue.get()

                if first is None:
                    self._queue.task_done()
                    break

                batch = [first]

                while len(batch) < self.batch_size:
                    try:
                        item = self._queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    if item is None:
                        self._queue.task_done()
                        stopping = True
                        break

                    batch.append(item)

                try:
                    await asyncio.to_thread(self._write_batch, batch)
                finally:
                    for _ in batch:
                        self._queue.task_done()

        except BaseException as exc:
            self._worker_error = exc
            raise

    async def flush(self) -> None:
        """Wait until all currently queued trades have been persisted."""
        if self._worker_task is None:
            raise RuntimeError("Ledger is not running")

        await self._queue.join()

        if self._worker_error is not None:
            raise RuntimeError("Ledger worker failed") from self._worker_error

    async def close(self) -> None:
        """Flush pending trades and stop the background writer."""
        if self._closed:
            return

        self._closed = True

        try:
            if self._worker_task is not None:
                await self._queue.put(None)
                await self._worker_task
        finally:
            if self._connection is not None:
                await asyncio.to_thread(self._connection.close)
                self._connection = None

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
        return False
