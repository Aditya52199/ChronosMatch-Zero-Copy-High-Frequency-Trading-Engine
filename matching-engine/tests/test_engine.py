"""Tests for Price-Time-Priority Cython engine."""
import unittest
import sys
from pathlib import Path

# Add the matching_engine directory to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))
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

    def test_zero_gc_collection_during_trades(self):
        import gc
        book = Book(capacity=20000)
        self.assertFalse(gc.is_tracked(book), "Book instance must not be tracked by Python GC")

        res = book.submit(order_id=1, price_ticks=100, quantity_lots=10, side=0, order_type=0)
        self.assertFalse(gc.is_tracked(res), "MatchResult must not be tracked by Python GC")

        # Force a collection to settle GC generation baselines
        gc.collect()
        stats_before = gc.get_stats()[0]["collections"]

        # Submit 5,000 orders/trades
        for i in range(2, 5002):
            book.submit(order_id=i, price_ticks=100, quantity_lots=1, side=1 if i % 2 == 0 else 0, order_type=0)

        stats_after = gc.get_stats()[0]["collections"]
        self.assertEqual(stats_before, stats_after, "Garbage collector must never trigger during trades")



if __name__ == "__main__":
    unittest.main()


def test_instant_match_buy_sell():
    book = Book(capacity=1024)
    res_buy = book.submit(order_id=100, price_ticks=120, quantity_lots=10, side=0, order_type=0)
    assert res_buy["fills"] == 0
    res_sell = book.submit(order_id=101, price_ticks=120, quantity_lots=10, side=1, order_type=0)
    assert res_sell["fills"] == 1
    assert res_sell["resting_quantity"] == 0
    assert res_sell["last_trade_price"] == 120
