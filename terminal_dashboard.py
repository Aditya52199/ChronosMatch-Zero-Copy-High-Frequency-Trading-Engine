
"""Interactive curses order-book dashboard for ChronosMatch.

Run from the project root: python terminal_dashboard.py

Controls:
    Space / Enter / Right Arrow = next order
    A = toggle automatic playback
    R = restart demo
    Q / Esc = quit

Windows dependency:
    python -m pip install windows-curses
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from typing import Any

try:
    import curses
except ImportError:
    curses = None  # type: ignore[assignment]

from chronosmatch.matching_engine import OrderBook
from chronosmatch.order_format import BUY, SELL, Order


TICK_DELAY_SECONDS = 0.8
BOOK_DEPTH = 5
RECENT_TRADE_DEPTH = 6


def build_demo_orders() -> list[Order]:
    """Create demo orders where a whale buy sweeps three ask levels."""
    now = time.perf_counter_ns()

    return [
        Order(1, SELL, 101, 3, now),
        Order(2, SELL, 102, 4, now + 1),
        Order(3, SELL, 103, 2, now + 2),
        Order(4, SELL, 104, 5, now + 3),
        Order(5, BUY, 98, 6, now + 4),
        Order(6, BUY, 103, 11, now + 5),
        Order(7, BUY, 100, 2, now + 6),
        Order(8, SELL, 99, 3, now + 7),
    ]


def aggregate_depth(
    resting_orders: list[dict[str, Any]],
) -> tuple[dict[int, int], dict[int, int]]:
    """Aggregate remaining order quantities by side and price."""
    bids: dict[int, int] = defaultdict(int)
    asks: dict[int, int] = defaultdict(int)

    for order in resting_orders:
        side = order.get("side")
        price = order.get("price_ticks")
        quantity = order.get(
            "remaining_quantity",
            order.get("quantity", 0),
        )

        if price is None:
            continue

        if side in (BUY, "BUY", "buy"):
            bids[int(price)] += int(quantity)
        elif side in (SELL, "SELL", "sell"):
            asks[int(price)] += int(quantity)

    return bids, asks


def _safe_addstr(
    window: Any,
    y: int,
    x: int,
    text: str,
    attr: int = 0,
) -> None:
    """Write clipped text and tolerate small terminals or resize errors."""
    height, width = window.getmaxyx()

    if y < 0 or y >= height or x >= width or width <= 0:
        return

    try:
        clipped = str(text)[: max(0, width - x - 1)]
        window.addstr(y, x, clipped, attr)
    except Exception:
        # curses can raise when the terminal is resized or a cell is invalid.
        pass


def _draw(
    window: Any,
    book: OrderBook,
    recent_trades: list[Any],
    event: str,
    order_number: int,
    total_orders: int,
    auto_play: bool,
    finished: bool,
) -> None:
    """Render the order book, spread, executions, and controls."""
    window.erase()
    height, width = window.getmaxyx()

    bold = curses.A_BOLD if curses is not None else 0

    _safe_addstr(window, 0, 0, "=" * max(1, width - 1))
    _safe_addstr(
        window,
        1,
        2,
        "CHRONOSMATCH | ZERO-COPY HIGH-FREQUENCY TRADING ENGINE",
        bold,
    )
    _safe_addstr(window, 2, 0, "=" * max(1, width - 1))

    bid = book.best_bid
    ask = book.best_ask
    spread = ask - bid if bid is not None and ask is not None else None

    _safe_addstr(window, 4, 2, f"Event: {event}")
    _safe_addstr(
        window,
        5,
        2,
        f"Progress: {order_number}/{total_orders}    "
        f"Mode: {'AUTO' if auto_play else 'MANUAL'}",
    )
    _safe_addstr(
        window,
        6,
        2,
        f"Best bid: {bid if bid is not None else '—'}    "
        f"Best ask: {ask if ask is not None else '—'}    "
        f"Spread: {spread if spread is not None else 'N/A'}    "
        f"Resting orders: {book.resting_order_count}",
    )

    bids, asks = aggregate_depth(book.resting_orders)

    _safe_addstr(
        window,
        8,
        2,
        f"{'BID QTY':>10} {'BID PRICE':>10}  |  "
        f"{'ASK PRICE':>10} {'ASK QTY':>10}",
        bold,
    )
    _safe_addstr(
        window,
        9,
        2,
        "-" * min(max(width - 4, 0), 55),
    )

    bid_prices = sorted(bids, reverse=True)[:BOOK_DEPTH]
    ask_prices = sorted(asks)[:BOOK_DEPTH]

    for i in range(max(len(bid_prices), len(ask_prices), 1)):
        bp = bid_prices[i] if i < len(bid_prices) else ""
        ap = ask_prices[i] if i < len(ask_prices) else ""

        bq = bids[bp] if bp != "" else ""
        aq = asks[ap] if ap != "" else ""

        _safe_addstr(
            window,
            10 + i,
            2,
            f"{str(bq):>10} {str(bp):>10}  |  "
            f"{str(ap):>10} {str(aq):>10}",
        )

    heading = 17 if height >= 24 else max(11, height - 8)

    _safe_addstr(window, heading, 2, "RECENT EXECUTIONS", bold)
    _safe_addstr(
        window,
        heading + 1,
        2,
        "-" * min(max(width - 4, 0), 55),
    )

    if not recent_trades:
        _safe_addstr(
            window,
            heading + 2,
            2,
            "No trades executed yet.",
        )
    else:
        for i, trade in enumerate(
            recent_trades[-RECENT_TRADE_DEPTH:]
        ):
            _safe_addstr(
                window,
                heading + 2 + i,
                2,
                f"Buy #{trade.buy_order_id}  "
                f"Sell #{trade.sell_order_id}  "
                f"Price {trade.price_ticks}  "
                f"Qty {trade.quantity}",
            )

    if finished:
        help_text = "Demo complete | R: restart  Q: quit"
    else:
        help_text = (
            "Space/Enter/Right: next  "
            "A: auto-play  R: restart  Q/Esc: quit"
        )

    _safe_addstr(
        window,
        max(0, height - 2),
        2,
        help_text,
        bold,
    )

    window.refresh()


def _run_curses(window: Any) -> None:
    """Run the interactive terminal dashboard."""
    curses.curs_set(0)
    window.keypad(True)
    window.timeout(100)

    orders = build_demo_orders()
    book = OrderBook()
    trades: list[Any] = []

    index = 0
    event = "READY"
    auto_play = False
    finished = False
    last_step = time.monotonic()

    while True:
        _draw(
            window,
            book,
            trades,
            event,
            index,
            len(orders),
            auto_play,
            finished,
        )

        key = window.getch()
        now = time.monotonic()

        if key in (ord("q"), ord("Q"), 27):
            break

        if key in (ord("r"), ord("R")):
            orders = build_demo_orders()
            book = OrderBook()
            trades = []
            index = 0
            event = "READY"
            finished = False
            last_step = now
            continue

        if key in (ord("a"), ord("A")):
            auto_play = not auto_play
            last_step = now

        step = key in (
            ord(" "),
            10,
            13,
            curses.KEY_ENTER,
            curses.KEY_RIGHT,
        )

        if (
            auto_play
            and not finished
            and now - last_step >= TICK_DELAY_SECONDS
        ):
            step = True

        if step and not finished:
            order = orders[index]
            trades.extend(book.submit_order(order))

            side = "BUY" if order.side == BUY else "SELL"

            if order.order_id == 6:
                event = (
                    f"WHALE BUY #{order.order_id} - "
                    "swept multiple ask levels"
                )
            else:
                event = f"{side} #{order.order_id}"

            index += 1
            finished = index >= len(orders)
            last_step = now


def main() -> int:
    """Start the dashboard."""
    if curses is None:
        print(
            "curses is unavailable. On Windows, run:\n"
            "python -m pip install windows-curses",
            file=sys.stderr,
        )
        return 1

    try:
        curses.wrapper(_run_curses)
    except KeyboardInterrupt:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
