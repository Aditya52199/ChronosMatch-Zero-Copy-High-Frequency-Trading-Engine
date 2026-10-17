"""Async mock market firehose publishing binary orders to a shared ring."""
from __future__ import annotations

import argparse
import asyncio
import time

from .protocol import SharedOrderRing, SIDE_BUY, SIDE_SELL


async def publish(path: str, count: int, target_rate: int, capacity: int,
                  consumer_timeout: float = 5.0) -> None:
    if count < 0 or target_rate < 0:
        raise ValueError("orders and rate must be non-negative")
    ring = SharedOrderRing(path, capacity)
    start = time.perf_counter_ns()
    published = 0
    full_retries = 0
    last_progress = time.monotonic()
    batch_size = max(1, min(1000, target_rate // 100 if target_rate else 1000))
    try:
        while published < count:
            batch_end = min(count, published + batch_size)
            while published < batch_end:
                i = published
                side = SIDE_BUY if i % 2 == 0 else SIDE_SELL
                # Integer ticks and lots avoid float conversion in the matching core.
                price = 6_700_000 + (i % 21 - 10) * 100
                if ring.try_write_fields(i + 1, price, 1 + i % 4, side):
                    published += 1
                    last_progress = time.monotonic()
                else:
                    full_retries += 1
                    if time.monotonic() - last_progress >= consumer_timeout:
                        raise TimeoutError(
                            f"IPC ring stayed full for {consumer_timeout:g}s; "
                            "start or speed up the matching-engine consumer"
                        )
                    await asyncio.sleep(0.0001)
            if target_rate:
                target_ns = start + published * 1_000_000_000 // target_rate
                remaining_ns = target_ns - time.perf_counter_ns()
                if remaining_ns > 0:
                    await asyncio.sleep(remaining_ns / 1_000_000_000)
            else:
                await asyncio.sleep(0)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000_000
        rate = published / elapsed if elapsed else 0
        print(f"published={published:,} elapsed_s={elapsed:.3f} rate={rate:,.0f} orders/s "
              f"target={target_rate:,} orders/s ring_full_retries={full_retries:,}")
    finally:
        ring.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default="chronosmatch.ring")
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--rate", type=int, default=100_000)
    parser.add_argument("--capacity", type=int, default=65_536)
    parser.add_argument("--consumer-timeout", type=float, default=5.0,
                        help="fail if a full ring makes no progress for this many seconds")
    args = parser.parse_args()
    asyncio.run(publish(args.path, args.orders, args.rate, args.capacity,
                        args.consumer_timeout))


if __name__ == "__main__":
    main()
