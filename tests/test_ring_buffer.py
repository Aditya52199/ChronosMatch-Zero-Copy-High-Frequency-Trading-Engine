import pytest

from chronosmatch.order_format import BUY, SELL, Order
from chronosmatch.ring_buffer import MmapRingBuffer


def make_order(order_id, side=BUY):
    return Order(order_id, side, 100, 2, order_id * 10)


def test_empty_buffer_returns_none(tmp_path):
    with MmapRingBuffer(tmp_path / "ring.bin", capacity=2) as ring:
        assert ring.get() is None


def test_round_trip_order(tmp_path):
    expected = make_order(1, SELL)

    with MmapRingBuffer(tmp_path / "ring.bin", capacity=2) as ring:
        ring.put(expected)
        assert ring.get() == expected


def test_full_buffer_raises(tmp_path):
    with MmapRingBuffer(tmp_path / "ring.bin", capacity=2) as ring:
        ring.put(make_order(1))
        ring.put(make_order(2))

        with pytest.raises(BufferError, match="full"):
            ring.put(make_order(3))


def test_wraparound_preserves_fifo_order(tmp_path):
    with MmapRingBuffer(tmp_path / "ring.bin", capacity=2) as ring:
        ring.put(make_order(1))
        ring.put(make_order(2))
        assert ring.get() == make_order(1)

        ring.put(make_order(3))
        assert ring.get() == make_order(2)
        assert ring.get() == make_order(3)
        assert ring.get() is None


def test_invalid_capacity_rejected(tmp_path):
    with pytest.raises(ValueError, match="capacity"):
        MmapRingBuffer(tmp_path / "ring.bin", capacity=0)


def test_closed_buffer_rejects_operations(tmp_path):
    ring = MmapRingBuffer(tmp_path / "ring.bin", capacity=1)
    ring.close()

    with pytest.raises(ValueError, match="closed"):
        ring.get()