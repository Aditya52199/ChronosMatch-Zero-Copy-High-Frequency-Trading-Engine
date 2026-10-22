"""Tests for Price-Time-Priority Cython engine."""
import unittest
from chronosmatch.engine import Book


class TestLimitOrderBook(unittest.TestCase):
    def setUp(self):
        self.book = Book(capacity=1024)

    def test_limit_order_bids_asks_and_priority(self):
        # Insert Bid 1: Price 100, Qty 10 (order_id 1)
        res = self.book.submit(order_id=1, price_ticks=100, quantity_lots=10, side=0, order_type=0)
        self.assertEqual(res["fills"], 0)
        self.assertEqual(res["resting_quantity"], 10)

        # Insert Bid 2: Price 100, Qty 15 (order_id 2) - same price, later time
        res = self.book.submit(order_id=2, price_ticks=100, quantity_lots=15, side=0, order_type=0)
        self.assertEqual(res["fills"], 0)

        # Insert Bid 3: Price 101, Qty 5 (order_id 3) - higher price (better priority)
        self.book.submit(order_id=3, price_ticks=101, quantity_lots=5, side=0, order_type=0)

        snap = self.book.snapshot()
        self.assertEqual(snap["best_bid"], 101)
        self.assertEqual(snap["resting_orders"], 3)

        # Incoming Sell limit order at 100 with qty 8
        # Should match Bid 3 (qty 5 @ 101) first due to price priority,
        # then match Bid 1 (qty 3 @ 100) due to time priority over Bid 2.
        res = self.book.submit(order_id=4, price_ticks=100, quantity_lots=8, side=1, order_type=0)
        self.assertEqual(res["fills"], 2)
        self.assertEqual(res["first_maker_id"], 3)
        self.assertEqual(res["resting_quantity"], 0)
        self.assertEqual(res["last_trade_price"], 100)

        snap = self.book.snapshot()
        self.assertEqual(snap["best_bid"], 100)
        self.assertEqual(snap["trades"], 2)

    def test_cancel_order(self):
        self.book.submit(order_id=10, price_ticks=50, quantity_lots=20, side=0, order_type=0)
        self.assertEqual(self.book.snapshot()["best_bid"], 50)
        self.assertTrue(self.book.cancel(10))
        self.assertEqual(self.book.snapshot()["best_bid"], 0)
        self.assertFalse(self.book.cancel(10))


if __name__ == "__main__":
    unittest.main()
