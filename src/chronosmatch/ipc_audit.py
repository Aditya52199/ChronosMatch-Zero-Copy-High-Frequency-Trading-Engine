
"""Cross-process mmap IPC audit for ChronosMatch.

The order data path uses fixed-size binary records, not pickle.
A multiprocessing lock protects the shared ring-buffer header and slots.
"""

from __future__ import annotations

import argparse
import mmap
import multiprocessing as mp
import os
import struct
import tempfile
import time
from pathlib import Path

from .order_format import ORDER_SIZE, BUY, SELL, Order, pack_order, unpack_order

_HEADER = struct.Struct("!QQ")
_HEADER_SIZE = _HEADER.size


def _initialize_file(path: str, capacity: int) -> None:
    """Initialize the mmap file once, before either worker starts."""
    with open(path, "w+b") as file:
        file.truncate(_HEADER_SIZE + capacity * ORDER_SIZE)
        with mmap.mmap(file.fileno(), 0) as mapped:
            _HEADER.pack_into(mapped, 0, 0, 0)
            mapped.flush()


def _producer(
    path: str,
    capacity: int,
    count: int,
    lock,
) -> None:
    """Write sequentially numbered binary orders into the shared ring."""
    with open(path, "r+b") as file:
        with mmap.mmap(file.fileno(), 0) as mapped:
            for order_id in range(count):
                order = Order(
                    order_id=order_id,
                    side=BUY if order_id % 2 == 0 else SELL,
                    price_ticks=10_000 + order_id % 100,
                    quantity=1 + order_id % 10,
                    timestamp_ns=time.perf_counter_ns(),
                )
                record = pack_order(order)

                while True:
                    with lock:
                        write_pos, read_pos = _HEADER.unpack_from(mapped, 0)

                        if write_pos - read_pos < capacity:
                            slot = write_pos % capacity
                            offset = _HEADER_SIZE + slot * ORDER_SIZE

                            mapped[offset : offset + ORDER_SIZE] = record
                            _HEADER.pack_into(
                                mapped, 0, write_pos + 1, read_pos
                            )
                            break

                    # Give the consumer a chance to free a slot.
                    time.sleep(0)


def _consumer(
    path: str,
    capacity: int,
    count: int,
    lock,
    results,
) -> None:
    """Read and validate every order, including FIFO sequence."""
    checksum = 0
    quantity_checksum = 0

    with open(path, "r+b") as file:
        with mmap.mmap(file.fileno(), 0) as mapped:
            received = 0

            while received < count:
                order = None

                with lock:
                    write_pos, read_pos = _HEADER.unpack_from(mapped, 0)

                    if read_pos < write_pos:
                        slot = read_pos % capacity
                        offset = _HEADER_SIZE + slot * ORDER_SIZE
                        record = mapped[offset : offset + ORDER_SIZE]

                        order = unpack_order(record)
                        _HEADER.pack_into(
                            mapped, 0, write_pos, read_pos + 1
                        )

                if order is None:
                    time.sleep(0)
                    continue

                if order.order_id != received:
                    raise RuntimeError(
                        f"FIFO/loss/duplicate check failed: expected "
                        f"order ID {received}, got {order.order_id}"
                    )

                checksum += order.order_id
                quantity_checksum += order.quantity
                received += 1

    results.put(
        {
            "received": received,
            "id_checksum": checksum,
            "quantity_checksum": quantity_checksum,
        }
    )


def run_audit(count: int = 1_000_000, capacity: int = 8192) -> None:
    """Run producer and consumer in separate OS processes."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if capacity < 1:
        raise ValueError("capacity must be at least 1")

    fd, path = tempfile.mkstemp(prefix="chronosmatch_ipc_", suffix=".ring")
    os.close(fd)

    ctx = mp.get_context("spawn")
    lock = ctx.Lock()
    results = ctx.Queue()

    producer = None
    consumer = None

    try:
        _initialize_file(path, capacity)

        consumer = ctx.Process(
            target=_consumer,
            args=(path, capacity, count, lock, results),
            name="chronosmatch-consumer",
        )
        producer = ctx.Process(
            target=_producer,
            args=(path, capacity, count, lock),
            name="chronosmatch-producer",
        )

        start_ns = time.perf_counter_ns()
        consumer.start()
        producer.start()

        producer.join()
        consumer.join()

        elapsed_ns = time.perf_counter_ns() - start_ns

        if producer.exitcode != 0:
            raise RuntimeError(
                f"Producer failed with exit code {producer.exitcode}"
            )
        if consumer.exitcode != 0:
            raise RuntimeError(
                f"Consumer failed with exit code {consumer.exitcode}"
            )

        report = results.get(timeout=5)
        expected_checksum = count * (count - 1) // 2

        if report["received"] != count:
            raise RuntimeError(f"Incorrect received count: {report}")
        if report["id_checksum"] != expected_checksum:
            raise RuntimeError(f"Order ID checksum mismatch: {report}")

        elapsed_seconds = elapsed_ns / 1_000_000_000
        throughput = count / elapsed_seconds

        print("\n=== ChronosMatch Cross-Process IPC Audit ===")
        print("Producer processes:       1")
        print("Consumer processes:       1")
        print(f"Orders sent:              {count:,}")
        print(f"Orders received:          {report['received']:,}")
        print(f"Expected ID checksum:     {expected_checksum:,}")
        print(f"Actual ID checksum:       {report['id_checksum']:,}")
        print(f"Quantity checksum:        {report['quantity_checksum']:,}")
        print(f"Elapsed time:             {elapsed_seconds:.3f} s")
        print(f"End-to-end throughput:    {throughput:,.0f} orders/s")
        print(f"Target:                   100,000 orders/s")
        print(
            "Target achieved:          "
            f"{'YES' if throughput >= 100_000 else 'NOT YET'}"
        )
        print("FIFO sequence verified:   YES")
        print("Missing/duplicate IDs:    NONE DETECTED")
        print("Order transport:          mmap binary records")
        print("Order-path pickle:        NOT USED")

    finally:
        for process in (producer, consumer):
            if process is not None and process.is_alive():
                process.terminate()
                process.join()

        results.close()
        results.join_thread()

        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            print(f"Warning: temporary mmap file remains at {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ChronosMatch two-process mmap IPC audit"
    )
    parser.add_argument(
        "--count", type=int, default=1_000_000,
        help="Number of orders to transfer (default: 1,000,000)",
    )
    parser.add_argument(
        "--capacity", type=int, default=8192,
        help="Ring-buffer capacity (default: 8192)",
    )
    args = parser.parse_args()
    run_audit(args.count, args.capacity)


if __name__ == "__main__":
    mp.freeze_support()
    main()
