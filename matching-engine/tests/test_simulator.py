"""Tests for the asyncio market firehose simulator."""
import asyncio
import os
import tempfile
import unittest
import sys
from pathlib import Path

# Add the matching_engine directory to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

from chronosmatch.protocol import SharedOrderRing
from chronosmatch.simulator import publish


class TestSimulator(unittest.TestCase):
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

    def test_firehose_small_burst(self):
        capacity = 1024
        count = 500
        # Create empty ring
        SharedOrderRing(self.ring_path, capacity=capacity, create=True).close()

        # Run publisher to write count orders
        asyncio.run(publish(self.ring_path, count=count, target_rate=100_000, capacity=capacity))

        # Verify consumer can read all orders
        ring = SharedOrderRing(self.ring_path, capacity=capacity)
        read_orders = []
        for _ in range(count):
            order = ring.try_read()
            self.assertIsNotNone(order)
            read_orders.append(order)

        self.assertEqual(len(read_orders), count)
        # Verify first order and last order sequence
        self.assertEqual(read_orders[0].order_id, 1)
        self.assertEqual(read_orders[-1].order_id, count)
        # Ring should now be empty
        self.assertIsNone(ring.try_read())
        ring.close()

    def test_firehose_backpressure_timeout_when_full(self):
        capacity = 16
        # Create small ring
        SharedOrderRing(self.ring_path, capacity=capacity, create=True).close()

        # Trying to publish more than capacity with no consumer should hit TimeoutError
        with self.assertRaises(TimeoutError):
            asyncio.run(publish(self.ring_path, count=32, target_rate=0, capacity=capacity, consumer_timeout=0.2))


if __name__ == "__main__":
    unittest.main()
