
"""Compare Python and Cython matching latency on a multi-level sweep."""

import statistics
import time

from chronosmatch.order_format import Order, BUY, SELL
from chronosmatch.matching_engine import OrderBook
from chronosmatch.matching_engine_cy import CythonOrderBook


LEVELS = 64
ROUNDS = 200


def measure(book_type, rounds=ROUNDS):
    samples = []

    for _ in range(rounds):
        book = book_type()

        # Prepare 64 ask levels outside the timed matching operation.
        for i in range(LEVELS):
            book.submit_order(
                Order(
                    order_id=i + 1,
                    side=SELL,
                    price_ticks=100 + i,
                    quantity=1,
                    timestamp_ns=i + 1,
                )
            )

        whale = Order(
            order_id=LEVELS + 1,
            side=BUY,
            price_ticks=100 + LEVELS - 1,
            quantity=LEVELS,
            timestamp_ns=LEVELS + 100,
        )

        start = time.perf_counter_ns()
        trades = book.submit_order(whale)
        elapsed = time.perf_counter_ns() - start

        assert len(trades) == LEVELS
        assert sum(t.quantity for t in trades) == LEVELS
        assert book.resting_order_count == 0

        samples.append(elapsed)

    samples.sort()
    return {
        "mean": statistics.mean(samples),
        "median": statistics.median(samples),
        "p95": samples[int(0.95 * (len(samples) - 1))],
        "max": samples[-1],
    }


def main():
    # Warm up both implementations before collecting measurements.
    measure(OrderBook, rounds=10)
    measure(CythonOrderBook, rounds=10)

    results = {
        "Python": measure(OrderBook),
        "Cython": measure(CythonOrderBook),
    }

    print("\n=== ChronosMatch Matching Benchmark ===")
    print(f"Workload: whale sweep across {LEVELS} ask levels")
    print(f"Measured rounds per engine: {ROUNDS}")
    print("Timing: matching call only; book setup excluded")
    print("Units: nanoseconds per incoming order\n")

    for name, result in results.items():
        print(f"{name} engine")
        print(f"  Mean:   {result['mean']:,.0f} ns")
        print(f"  Median: {result['median']:,.0f} ns")
        print(f"  P95:    {result['p95']:,.0f} ns")
        print(f"  Max:    {result['max']:,.0f} ns")

    python_mean = results["Python"]["mean"]
    cython_mean = results["Cython"]["mean"]

    if cython_mean < python_mean:
        print(f"\nMean latency improvement: "
              f"{(1 - cython_mean / python_mean) * 100:.1f}%")
    elif cython_mean > python_mean:
        print(f"\nCython mean latency was "
              f"{(cython_mean / python_mean - 1) * 100:.1f}% higher.")
    else:
        print("\nMean latency was equal in this run.")


if __name__ == "__main__":
    main()
