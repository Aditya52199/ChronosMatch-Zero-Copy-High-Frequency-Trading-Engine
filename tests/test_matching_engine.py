import pytest

from chronosmatch.order_format import BUY, SELL, Order
from chronosmatch.matching_engine import OrderBook


def make_order(order_id, side, price, quantity, timestamp):
    return Order(order_id, side, price, quantity, timestamp)


def test_non_crossing_orders_rest_on_book():
    book = OrderBook()
    assert book.submit_order(make_order(1, BUY, 100, 5, 1)) == []
    assert book.submit_order(make_order(2, SELL, 105, 5, 2)) == []
    assert book.best_bid == 100
    assert book.best_ask == 105


def test_crossing_orders_generate_trade():
    book = OrderBook()
    book.submit_order(make_order(1, BUY, 105, 4, 1))
    trades = book.submit_order(make_order(2, SELL, 100, 4, 2))

    assert len(trades) == 1
    assert trades[0].buy_order_id == 1
    assert trades[0].sell_order_id == 2
    assert trades[0].price_ticks == 105
    assert trades[0].quantity == 4
    assert book.resting_order_count == 0


def test_partial_fill_leaves_remainder():
    book = OrderBook()
    book.submit_order(make_order(1, BUY, 100, 10, 1))
    trades = book.submit_order(make_order(2, SELL, 100, 4, 2))

    assert trades[0].quantity == 4
    assert book.resting_order_count == 1
    assert book.best_bid == 100


def test_price_priority_selects_best_ask():
    book = OrderBook()
    book.submit_order(make_order(1, SELL, 105, 2, 1))
    book.submit_order(make_order(2, SELL, 101, 2, 2))

    trades = book.submit_order(make_order(3, BUY, 110, 2, 3))
    assert trades[0].sell_order_id == 2
    assert trades[0].price_ticks == 101


def test_time_priority_at_same_price():
    book = OrderBook()
    book.submit_order(make_order(1, SELL, 100, 2, 1))
    book.submit_order(make_order(2, SELL, 100, 2, 2))

    trades = book.submit_order(make_order(3, BUY, 100, 1, 3))
    assert trades[0].sell_order_id == 1


def test_duplicate_order_id_is_rejected():
    book = OrderBook()
    book.submit_order(make_order(1, BUY, 100, 1, 1))

    with pytest.raises(ValueError, match="Duplicate order ID"):
        book.submit_order(make_order(1, SELL, 100, 1, 2))