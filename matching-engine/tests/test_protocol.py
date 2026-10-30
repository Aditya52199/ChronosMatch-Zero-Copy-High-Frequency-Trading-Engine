"""Tests for SharedOrderRing binary protocol using mmap and struct."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the matching_engine directory to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

from chronosmatch.protocol import (
    DEFAULT_CAPACITY,
    MAGIC,
    ORDER,
    RECORD_SIZE,
    SIDE_BUY,
    SIDE_SELL,
    TYPE_LIMIT,
    TYPE_MARKET,
    Order,
    SharedOrderRing,
)


class TestSharedOrderRing(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ring")
        self.temp_file.close()
        self.ring_path = self.temp_file.name

    def tearDown(self):
        if os.path.exists(self.ring_path):
            try:
                os.remove(self.ring_path)
            except OSError:
                pass

    def test_create_and_read_write(self):
        capacity = 8
        with SharedOrderRing(self.ring_path, capacity=capacity, create=True) as ring:
            self.assertEqual(ring.capacity, capacity)
            # Empty initially
            self.assertIsNone(ring.try_read())

            # Write single order
            order = Order(order_id=101, price_ticks=55000, quantity_lots=15, side=SIDE_BUY, order_type=TYPE_LIMIT)
            self.assertTrue(ring.try_write(order))

            # Read back order
            read_order = ring.try_read()
            self.assertIsNotNone(read_order)
            self.assertEqual(read_order.order_id, 101)
            self.assertEqual(read_order.price_ticks, 55000)
            self.assertEqual(read_order.quantity_lots, 15)
            self.assertEqual(read_order.side, SIDE_BUY)
            self.assertEqual(read_order.order_type, TYPE_LIMIT)

            # Ring is now empty again
            self.assertIsNone(ring.try_read())

    def test_write_fields_zero_copy_primitive(self):
        capacity = 4
        with SharedOrderRing(self.ring_path, capacity=capacity, create=True) as ring:
            self.assertTrue(ring.try_write_fields(order_id=999, price_ticks=12345, quantity_lots=50, side=SIDE_SELL, order_type=TYPE_MARKET))
            read_order = ring.try_read()
            self.assertIsNotNone(read_order)
            self.assertEqual(read_order.order_id, 999)
            self.assertEqual(read_order.price_ticks, 12345)
            self.assertEqual(read_order.quantity_lots, 50)
            self.assertEqual(read_order.side, SIDE_SELL)
            self.assertEqual(read_order.order_type, TYPE_MARKET)

    def test_ring_buffer_capacity_and_wrap_around(self):
        capacity = 4
        with SharedOrderRing(self.ring_path, capacity=capacity, create=True) as ring:
            # Fill buffer to capacity
            for i in range(capacity):
                self.assertTrue(ring.try_write_fields(order_id=i + 1, price_ticks=100 + i, quantity_lots=10, side=SIDE_BUY))

            # Next write must fail (ring is full)
            self.assertFalse(ring.try_write_fields(order_id=99, price_ticks=200, quantity_lots=10, side=SIDE_BUY))

            # Consume 2 items
            item1 = ring.try_read()
            item2 = ring.try_read()
            self.assertEqual(item1.order_id, 1)
            self.assertEqual(item2.order_id, 2)

            # Now we can write 2 more items (wrap-around)
            self.assertTrue(ring.try_write_fields(order_id=10, price_ticks=500, quantity_lots=1, side=SIDE_SELL))
            self.assertTrue(ring.try_write_fields(order_id=11, price_ticks=501, quantity_lots=2, side=SIDE_SELL))
            self.assertFalse(ring.try_write_fields(order_id=12, price_ticks=502, quantity_lots=3, side=SIDE_SELL))

            # Consume remaining items
            remaining_ids = []
            while True:
                item = ring.try_read()
                if item is None:
                    break
                remaining_ids.append(item.order_id)
            self.assertEqual(remaining_ids, [3, 4, 10, 11])

    def test_validation_errors(self):
        with SharedOrderRing(self.ring_path, capacity=4, create=True) as ring:
            with self.assertRaises(ValueError):
                # Negative price
                ring.try_write_fields(order_id=1, price_ticks=-1, quantity_lots=10, side=SIDE_BUY)

            with self.assertRaises(ValueError):
                # Zero quantity
                ring.try_write_fields(order_id=1, price_ticks=100, quantity_lots=0, side=SIDE_BUY)

            with self.assertRaises(ValueError):
                # Order ID > 62 bits
                ring.try_write_fields(order_id=1 << 62, price_ticks=100, quantity_lots=10, side=SIDE_BUY)


if __name__ == "__main__":
    unittest.main()
