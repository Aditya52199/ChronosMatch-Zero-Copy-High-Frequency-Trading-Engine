
import pytest

from chronosmatch.order_format import (
    BUY,
    SELL,
    ORDER_SIZE,
    Order,
    pack_order,
    unpack_order,
)


def test_order_binary_round_trip():
    original = Order(
        order_id=1001,
        side=BUY,
        price_ticks=25050,
        quantity=10,
        timestamp_ns=123456789,
    )

    binary_data = pack_order(original)
    restored = unpack_order(binary_data)

    assert len(binary_data) == 29
    assert restored == original


def test_sell_order_round_trip():
    original = Order(1002, SELL, 25100, 5, 123456790)

    assert unpack_order(pack_order(original)) == original


def test_invalid_side_is_rejected():
    order = Order(1003, 5, 25000, 10, 123456791)

    with pytest.raises(ValueError):
        pack_order(order)


def test_invalid_quantity_is_rejected():
    order = Order(1004, BUY, 25000, 0, 123456792)

    with pytest.raises(ValueError):
        pack_order(order)


def test_wrong_binary_size_is_rejected():
    with pytest.raises(ValueError):
        unpack_order(b"\x00\x01")


def test_record_size_is_fixed():
    assert ORDER_SIZE == 29
