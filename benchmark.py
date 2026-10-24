
"""Microbenchmark for a single resting order matched by an incoming order."""

import argparse
import statistics
import time

from chronosmatch.matching_engine import OrderBook
from chronosmatch.order_format import BUY, SELL, Order


def run_benchmark(iterations: int = 10_000) -> dict:
    if iterations < 1:
        raise ValueError("iterations must be at least 1")

    latencies = []

    for i in range(iterations):
        book = OrderBook()
        base_id = i * 2

        # Prepare the book outside the measured matching call.
        book.submit_order(
            Order(base_id + 1, SELL, 100, 1, base_id + 1)
        )
        incoming = Order(base_id + 2, BUY, 100, 1, base_id + 2)

        start = time.perf_counter_ns()
        trades = book.submit_order(incoming)
        elapsed = time.perf_counter_ns() - start

        if len(trades) != 1 or trades[0].quantity != 1:
            raise RuntimeError("Expected exactly one fully executed trade")

        latencies.append(elapsed)

    ordered = sorted(latencies)

    def percentile(p: float) -> int:
        index = min(len(ordered) - 1, int((len(ordered) - 1) * p))
        return ordered[index]

    return {
        "iterations": iterations,
        "mean_ns": round(statistics.mean(latencies)),
        "median_ns": percentile(0.50),
        "p95_ns": percentile(0.95),
        "p99_ns": percentile(0.99),
        "max_ns": max(latencies),
    }


def main():
    parser = argparse.ArgumentParser(description="ChronosMatch microbenchmark")
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()

    results = run_benchmark(args.iterations)

    print("\n=== ChronosMatch Microbenchmark ===")
    print(f"Measured matches: {results['iterations']:,}")
    print(f"Mean latency:     {results['mean_ns']:,} ns")
    print(f"Median latency:   {results['median_ns']:,} ns")
    print(f"P95 latency:      {results['p95_ns']:,} ns")
    print(f"P99 latency:      {results['p99_ns']:,} ns")
    print(f"Maximum latency:  {results['max_ns']:,} ns")
    print("\nSynthetic single-order-book workload; results depend on your machine.")


if __name__ == "__main__":
    main()
