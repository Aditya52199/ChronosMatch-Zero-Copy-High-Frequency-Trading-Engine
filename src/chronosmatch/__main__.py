"""Run the ChronosMatch demo with: python -m chronosmatch"""

import argparse
from pathlib import Path

from .simulator import run_simulation


def main():
    parser = argparse.ArgumentParser(description="ChronosMatch demo")
    parser.add_argument("--db", default="chronosmatch.db", help="SQLite path")
    parser.add_argument(
        "--ring", default="chronosmatch.ring", help="Ring-buffer file path"
    )
    args = parser.parse_args()

    # Start each demo with a fresh database and ring file.
    for filename in (args.db, args.ring):
        path = Path(filename)
        if path.exists():
            path.unlink()

    result = run_simulation(args.db, args.ring)

    print("\n=== ChronosMatch Demo ===")
    print(f"Orders processed: {result['orders_processed']}")
    print(f"Trades executed:  {result['trades_executed']}")
    print(f"Trades stored:    {result['trades_stored']}")
    print(f"Best bid:         {result['best_bid']}")
    print(f"Best ask:         {result['best_ask']}")
    print(f"Mean match time:  {result['latency_mean_ns']} ns")
    print(f"Max match time:   {result['latency_max_ns']} ns")
    print("\nNote: timing measures matching only, not end-to-end transport.")


if __name__ == "__main__":
    main()