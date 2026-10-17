"""Curses terminal monitor; use --plain on terminals without curses support."""
from __future__ import annotations

import argparse
import time
from collections import deque
try:
    import curses
except ImportError:  # Windows uses the optional windows-curses package.
    curses = None

from .protocol import SharedOrderRing

try:
    from .engine import Book
except ImportError as exc:
    raise SystemExit(
        "ChronosMatch Cython engine is not built. From the matching-engine "
        "directory, run: python setup.py build_ext --inplace"
    ) from exc


def run(stdscr, path: str, capacity: int, price_scale: int, quantity_scale: int) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    ring = SharedOrderRing(path, capacity)
    book = Book()
    latencies = deque(maxlen=120)
    processed = 0
    try:
        while True:
            key = stdscr.getch()
            if key in (ord("q"), 27):
                break
            for _ in range(5000):
                order = ring.try_read()
                if order is None:
                    break
                started = time.perf_counter_ns()
                book.submit(order.order_id, order.price_ticks, order.quantity_lots,
                            order.side, order.order_type)
                latencies.append((time.perf_counter_ns() - started) / 1000)
                processed += 1
            snapshot = book.snapshot()
            avg = sum(latencies) / len(latencies) if latencies else 0
            p99 = sorted(latencies)[int((len(latencies) - 1) * .99)] if latencies else 0
            stdscr.erase()
            rows, cols = stdscr.getmaxyx()
            lines = [
                "ChronosMatch | shared memory -> Cython matching engine",
                f"Orders matched: {processed:,}",
                f"Best bid: {snapshot['best_bid'] / price_scale:.4f}" if snapshot["best_bid"] else "Best bid: —",
                f"Best ask: {snapshot['best_ask'] / price_scale:.4f}" if snapshot["best_ask"] else "Best ask: —",
                f"Spread: {(snapshot['best_ask'] - snapshot['best_bid']) / price_scale:.4f}" if snapshot["best_bid"] and snapshot["best_ask"] else "Spread: —",
                f"Resting orders: {snapshot['resting_orders']:,}    Trades: {snapshot['trades']:,}",
                f"Matching latency (μs): avg {avg:.2f}    p99 {p99:.2f}    max {max(latencies, default=0):.2f}",
                "Recent latency (μs):",
            ]
            for row, line in enumerate(lines[:max(0, rows - 2)]):
                stdscr.addnstr(row, 0, line, max(0, cols - 1))
            if rows > 9 and cols > 10 and latencies:
                width = min(cols - 2, len(latencies))
                values = list(latencies)[-width:]
                ceiling = max(max(values), 1.0)
                graph_y = 9
                graph_h = rows - graph_y - 2
                for x, value in enumerate(values):
                    height = min(graph_h, int(value / ceiling * graph_h))
                    for dy in range(height):
                        y = rows - 2 - dy
                        try:
                            stdscr.addch(y, x, "#")
                        except curses.error:
                            pass
            stdscr.addnstr(rows - 1, 0, "Press q to quit", max(0, cols - 1))
            stdscr.refresh()
            time.sleep(.05)
    finally:
        ring.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default="chronosmatch.ring")
    parser.add_argument("--capacity", type=int, default=65_536)
    parser.add_argument("--price-scale", type=int, default=100)
    parser.add_argument("--quantity-scale", type=int, default=1000)
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()

    def consume(stdscr) -> None:
        run(stdscr, args.path, args.capacity, args.price_scale, args.quantity_scale)

    if args.plain or curses is None:
        # Plain fallback keeps the same IPC/engine path, with periodic summaries.
        ring = SharedOrderRing(args.path, args.capacity)
        book = Book()
        processed = 0
        try:
            while True:
                order = ring.wait_read()
                if order:
                    book.submit(order.order_id, order.price_ticks, order.quantity_lots,
                                order.side, order.order_type)
                    processed += 1
                if processed and processed % 10_000 == 0:
                    print({"processed": processed, **book.snapshot()})
        except KeyboardInterrupt:
            print({"processed": processed, **book.snapshot()})
        finally:
            ring.close()
    else:
        curses.wrapper(consume)


if __name__ == "__main__":
    main()
