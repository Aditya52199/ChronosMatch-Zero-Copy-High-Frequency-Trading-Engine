
"""Behavioral parity tests for the Python and Cython matching engines."""

import pytest

from chronosmatch.order_format import Order, BUY, SELL
from chronosmatch.matching_engine import OrderBook
from chronosmatch.matching_engine_cy import CythonOrderBook


ENGINE_TYPES = [OrderBook, CythonOrderBook]


def make_order(order_id, side, price, quantity, timestamp):
    return Order(
        order_id=order_id,
        side=side,
        price_ticks=price,
        quantity=quantity,
        timestamp_ns=timestamp,
    )


def normalize_trades(trades):
    return [
        (
            t.buy_order_id,
            t.sell_order_id,
            t.price_ticks,
            t.quantity,
            t.timestamp_ns,
        )
        for t in trades
    ]


def normalize_book(book):
    return {
        "best_bid": book.best_bid,
        "best_ask": book.best_ask,
        "resting_order_count": book.resting_order_count,
        "resting_orders": book.resting_orders,
    }


@pytest.mark.parametrize("engine_type", ENGINE_TYPES)
def test_partial_fill_preserves_remainder(engine_type):
    book = engine_type()

    book.submit_order(make_order(1, SELL, 100, 10, 1))
    trades = book.submit_order(make_order(2, BUY, 100, 4, 2))

    assert [
        (t.buy_order_id, t.sell_order_id, t.price_ticks, t.quantity)
        for t in trades
    ] == [(2, 1, 100, 4)]

    assert book.resting_order_count == 1
    assert book.resting_orders[0]["remaining_quantity"] == 6


@pytest.mark.parametrize("engine_type", ENGINE_TYPES)
def test_whale_sweeps_multiple_ask_levels(engine_type):
    book = engine_type()

    for i, price in enumerate((100, 101, 102, 103), start=1):
        book.submit_order(
            make_order(i, SELL, price, 2, i)
        )

    trades = book.submit_order(
        make_order(10, BUY, 103, 8, 20)
    )

    assert [
        (t.sell_order_id, t.price_ticks, t.quantity)
        for t in trades
    ] == [
        (1, 100, 2),
        (2, 101, 2),
        (3, 102, 2),
        (4, 103, 2),
    ]

    assert book.resting_order_count == 0
    assert book.best_ask is None


@pytest.mark.parametrize("engine_type", ENGINE_TYPES)
def test_same_price_uses_time_priority(engine_type):
    book = engine_type()

    book.submit_order(make_order(1, SELL, 100, 2, 10))
    book.submit_order(make_order(2, SELL, 100, 2, 20))

    trades = book.submit_order(make_order(3, BUY, 100, 3, 30))

    assert [
        (t.sell_order_id, t.quantity)
        for t in trades
    ] == [(1, 2), (2, 1)]

    assert book.resting_order_count == 1
    assert book.resting_orders[0]["order_id"] == 2
    assert book.resting_orders[0]["remaining_quantity"] == 1


def test_python_and_cython_engines_produce_identical_results():
    python_book = OrderBook()
    cython_book = CythonOrderBook()

    orders = [
        make_order(1, SELL, 103, 4, 1),
        make_order(2, SELL, 101, 3, 2),
        make_order(3, SELL, 101, 2, 3),
        make_order(4, BUY, 100, 5, 4),
        make_order(5, BUY, 103, 6, 5),
        make_order(6, BUY, 104, 4, 6),
        make_order(7, SELL, 99, 3, 7),
    ]

    for order in orders:
        python_trades = python_book.submit_order(order)
        cython_trades = cython_book.submit_order(order)

        assert normalize_trades(python_trades) == normalize_trades(
            cython_trades
        )
        assert normalize_book(python_book) == normalize_book(cython_book)


def test_both_engines_reject_duplicate_order_ids():
    for engine_type in ENGINE_TYPES:
        book = engine_type()
        book.submit_order(make_order(1, BUY, 100, 2, 1))

        with pytest.raises(ValueError, match="Duplicate order ID"):
            book.submit_order(make_order(1, SELL, 100, 2, 2))
