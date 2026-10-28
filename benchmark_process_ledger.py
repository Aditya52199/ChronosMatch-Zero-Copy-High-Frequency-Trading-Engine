
import argparse
import tempfile
from pathlib import Path

from chronosmatch.order_format import BUY, SELL, Order
from chronosmatch.process_ledger import run_process_ledger_simulation


def make_orders(levels: int, sweeps: int) -> list[Order]:
    orders = []

    for i in range(levels):
        orders.append(
            Order(
                order_id=i,
                side=SELL,
                price_ticks=10_000 + i,
                quantity=10,
                timestamp_ns=i + 1,
            )
        )

    # Each buy crosses the full ask range. Unique IDs are required.
    for i in range(sweeps):
        orders.append(
            Order(
                order_id=levels + i,
                side=BUY,
                price_ticks=10_000 + levels,
                quantity=levels * 10,
                timestamp_ns=levels + i + 1,
            )
        )

    return orders


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", type=int, default=64)
    parser.add_argument("--sweeps", type=int, default=20)
    parser.add_argument("--capacity", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    if args.levels < 1 or args.sweeps < 1:
        parser.error("--levels and --sweeps must be positive")

    orders = make_orders(args.levels, args.sweeps)

    with tempfile.TemporaryDirectory(prefix="chronosmatch_bench_") as temp:
        root = Path(temp)
        result = run_process_ledger_simulation(
            db_path=root / "trades.db",
            ring_path=root / "trades.ring",
            orders=orders,
            capacity=args.capacity,
            batch_size=args.batch_size,
        )

    print("\n=== Separate-Process Ledger Benchmark ===")
    print(f"Orders processed:          {result['orders_processed']:,}")
    print(f"Trades executed:           {result['trades_executed']:,}")
    print(f"Trades persisted:          {result['trades_stored']:,}")
    print(f"Matching mean:             {result['latency_mean_ns']:,} ns")
    print(f"Matching maximum:          {result['latency_max_ns']:,} ns")
    print(f"End-to-end elapsed:        {result['elapsed_ns'] / 1e9:.6f} s")
    print(
        "End-to-end throughput:     "
        f"{result['end_to_end_orders_per_second']:,.0f} orders/s"
    )
    print(f"Ledger process exit code:  {result['ledger_process_exitcode']}")


if __name__ == "__main__":
    main()
