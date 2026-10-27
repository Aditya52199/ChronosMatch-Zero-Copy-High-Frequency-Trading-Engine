
"""Asyncio binary-order firehose benchmark.

Measures in-process asynchronous queue throughput. This is not an
end-to-end cross-process IPC benchmark.
"""

import argparse
import asyncio
import struct
import time

# order_id: uint64, side: uint8, price_ticks: uint64,
# quantity: uint32, timestamp_ns: uint64 = 29 bytes.
ORDER_STRUCT = struct.Struct("!QBQIQ")
TARGET_ORDERS_PER_SEC = 100_000
SENTINEL = None


async def producer(queue, count):
    """Generate binary order records and enqueue them."""
    for order_id in range(1, count + 1):
        side = order_id % 2
        price_ticks = 10_000 + (order_id % 100)
        quantity = 1 + (order_id % 10)
        timestamp_ns = time.perf_counter_ns()

        record = ORDER_STRUCT.pack(
            order_id,
            side,
            price_ticks,
            quantity,
            timestamp_ns,
        )
        await queue.put(record)

    await queue.put(SENTINEL)


async def consumer(queue, expected_count):
    """Decode records and verify order sequence and checksums."""
    received = 0
    id_checksum = 0
    quantity_checksum = 0

    while True:
        record = await queue.get()

        try:
            if record is SENTINEL:
                break

            if len(record) != ORDER_STRUCT.size:
                raise ValueError(
                    f"Invalid record size: {len(record)}"
                )

            order_id, side, price, quantity, timestamp_ns = (
                ORDER_STRUCT.unpack(record)
            )

            expected_id = received + 1
            if order_id != expected_id:
                raise ValueError(
                    f"FIFO mismatch: expected ID {expected_id}, "
                    f"received {order_id}"
                )

            if side not in (0, 1):
                raise ValueError(f"Invalid side: {side}")

            if price <= 0 or quantity <= 0 or timestamp_ns <= 0:
                raise ValueError("Invalid order field")

            received += 1
            id_checksum += order_id
            quantity_checksum += quantity
        finally:
            queue.task_done()

    if received != expected_count:
        raise ValueError(
            f"Expected {expected_count} records, received {received}"
        )

    return received, id_checksum, quantity_checksum


async def run_firehose(count, capacity):
    if count <= 0:
        raise ValueError("count must be positive")
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    queue = asyncio.Queue(maxsize=capacity)

    # Start timing after setup, before the producer and consumer run.
    start_ns = time.perf_counter_ns()

    consumer_task = asyncio.create_task(consumer(queue, count))
    producer_task = asyncio.create_task(producer(queue, count))

    await producer_task
    received, id_checksum, quantity_checksum = await consumer_task

    elapsed_ns = time.perf_counter_ns() - start_ns
    elapsed_seconds = elapsed_ns / 1_000_000_000
    throughput = received / elapsed_seconds
    expected_id_checksum = count * (count + 1) // 2

    print("\n=== ChronosMatch Asyncio Firehose ===")
    print(f"Orders generated:       {count:,}")
    print(f"Orders consumed:        {received:,}")
    print(f"Binary record size:     {ORDER_STRUCT.size} bytes")
    print(f"Queue capacity:         {capacity:,}")
    print(f"Expected ID checksum:   {expected_id_checksum:,}")
    print(f"Actual ID checksum:     {id_checksum:,}")
    print(f"Quantity checksum:      {quantity_checksum:,}")
    print(f"Elapsed time:           {elapsed_seconds:.3f} s")
    print(f"Throughput:             {throughput:,.0f} orders/sec")
    print(f"Target:                 {TARGET_ORDERS_PER_SEC:,} orders/sec")
    print(
        "Target achieved:        "
        + ("YES" if throughput >= TARGET_ORDERS_PER_SEC else "NOT YET")
    )
    print(
        "Sequence/checksum:      "
        + (
            "PASS"
            if received == count and id_checksum == expected_id_checksum
            else "FAIL"
        )
    )
    print("Transport:              asyncio.Queue, binary records")
    print("Scope:                  single process; not IPC throughput")

    if received != count or id_checksum != expected_id_checksum:
        raise RuntimeError("Firehose integrity check failed")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark asynchronous binary order throughput."
    )
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--capacity", type=int, default=8192)
    args = parser.parse_args()

    asyncio.run(run_firehose(args.count, args.capacity))


if __name__ == "__main__":
    main()
