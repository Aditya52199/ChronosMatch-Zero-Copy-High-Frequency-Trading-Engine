# cython: language_level=3, boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True
"""Ultra-low-latency Price-Time-Priority Limit Order Book implemented in Cython.

All core structures and variables are statically typed using C-types (libc.stdint
and libc.stdlib) to execute inside pure C functions (`nogil`), releasing the Python
Global Interpreter Lock (GIL) during matching and order queue operations.
"""

from libc.stdint cimport uint64_t, int64_t, uint32_t, uint8_t
from libc.stdlib cimport malloc, free, realloc
from libc.string cimport memset

cdef struct MatchResult:
    uint64_t fills
    uint64_t first_maker_id
    int64_t resting_quantity
    int64_t last_trade_price

cdef struct LevelOrder:
    uint64_t order_id
    int64_t price_ticks
    int64_t quantity_lots
    uint8_t side

cdef class Book:
    """High-frequency Price-Time Priority Limit Order Book.
    
    Supports:
      - side: 0 = Buy / Bid, 1 = Sell / Ask
      - order_type: 0 = Limit, 1 = Market
    """
    cdef LevelOrder* orders
    cdef Py_ssize_t count
    cdef Py_ssize_t capacity
    cdef uint64_t trades
    cdef int64_t last_trade_price
    cdef int64_t best_bid
    cdef int64_t best_ask

    def __cinit__(self, Py_ssize_t capacity=131072):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.orders = <LevelOrder*>malloc(capacity * sizeof(LevelOrder))
        if self.orders == NULL:
            raise MemoryError("Failed to allocate order memory for Book")
        self.capacity = capacity
        self.count = 0
        self.trades = 0
        self.last_trade_price = 0
        self.best_bid = 0
        self.best_ask = 0

    def __dealloc__(self):
        if self.orders != NULL:
            free(self.orders)
            self.orders = NULL

    cdef MatchResult _c_submit(self, uint64_t order_id, int64_t price_ticks, int64_t quantity_lots,
                               uint8_t side, uint8_t order_type) noexcept nogil:
        """Internal pure C matching routine executed entirely without the GIL."""
        cdef MatchResult res
        res.fills = 0
        res.first_maker_id = 0
        res.resting_quantity = 0
        res.last_trade_price = self.last_trade_price

        cdef int64_t remaining = quantity_lots
        cdef Py_ssize_t i, j
        cdef bint crosses

        # Continuous matching against resting book in price-time priority
        while remaining > 0:
            i = -1
            for j in range(self.count):
                if self.orders[j].side == side:
                    continue
                
                # Check price-crossing condition
                crosses = (order_type == 1 or
                           (side == 0 and price_ticks >= self.orders[j].price_ticks) or
                           (side == 1 and price_ticks <= self.orders[j].price_ticks))
                if not crosses:
                    continue

                if i == -1:
                    i = j
                elif side == 0 and self.orders[j].price_ticks < self.orders[i].price_ticks:
                    # Better ask is lower price
                    i = j
                elif side == 1 and self.orders[j].price_ticks > self.orders[i].price_ticks:
                    # Better bid is higher price
                    i = j
                # If prices are equal, arrival order (lower index j) wins, preserving time priority.

            if i == -1:
                break

            if res.fills == 0:
                res.first_maker_id = self.orders[i].order_id

            res.fills += 1
            self.last_trade_price = self.orders[i].price_ticks
            res.last_trade_price = self.last_trade_price

            if self.orders[i].quantity_lots <= remaining:
                remaining -= self.orders[i].quantity_lots
                # Remove exhausted resting order by shifting
                for j in range(i, self.count - 1):
                    self.orders[j] = self.orders[j + 1]
                self.count -= 1
            else:
                self.orders[i].quantity_lots -= remaining
                remaining = 0
            self.trades += 1

        # If unfilled residual remains and it is a limit order, append to book
        if remaining > 0 and order_type == 0:
            if self.count < self.capacity:
                i = self.count
                self.orders[i].order_id = order_id
                self.orders[i].price_ticks = price_ticks
                self.orders[i].quantity_lots = remaining
                self.orders[i].side = side
                self.count += 1
                res.resting_quantity = remaining
            else:
                # Signaled capacity limit reached
                res.resting_quantity = -1
        else:
            res.resting_quantity = 0

        self._c_refresh_top()
        return res

    cdef void _c_refresh_top(self) noexcept nogil:
        """Scan top of the book without Python overhead or GIL."""
        cdef Py_ssize_t i
        self.best_bid = 0
        self.best_ask = 0
        for i in range(self.count):
            if self.orders[i].side == 0:
                if self.orders[i].price_ticks > self.best_bid:
                    self.best_bid = self.orders[i].price_ticks
            elif self.best_ask == 0 or self.orders[i].price_ticks < self.best_ask:
                self.best_ask = self.orders[i].price_ticks

    cpdef submit(self, uint64_t order_id, int64_t price_ticks, int64_t quantity_lots,
                 uint8_t side, uint8_t order_type=0):
        """Submit limit or market order to the book, executing matching with nogil."""
        cdef MatchResult res
        if quantity_lots <= 0 or side > 1 or order_type > 1:
            raise ValueError("invalid order fields")
        if order_type == 0 and price_ticks <= 0:
            raise ValueError("limit order price must be positive")

        with nogil:
            res = self._c_submit(order_id, price_ticks, quantity_lots, side, order_type)

        if res.resting_quantity == -1:
            raise OverflowError("order book capacity reached")

        return {
            "fills": res.fills,
            "first_maker_id": res.first_maker_id,
            "resting_quantity": res.resting_quantity,
            "last_trade_price": res.last_trade_price
        }

    cdef bint _c_cancel(self, uint64_t order_id) noexcept nogil:
        """Cancel an order by ID directly in C nogil."""
        cdef Py_ssize_t i, j
        for i in range(self.count):
            if self.orders[i].order_id == order_id:
                for j in range(i, self.count - 1):
                    self.orders[j] = self.orders[j + 1]
                self.count -= 1
                self._c_refresh_top()
                return True
        return False

    cpdef bint cancel(self, uint64_t order_id):
        """Cancel an existing order by order_id."""
        cdef bint success
        with nogil:
            success = self._c_cancel(order_id)
        return success

    cpdef snapshot(self):
        """Returns snapshot of current top-of-book and trading metrics."""
        return {
            "best_bid": self.best_bid,
            "best_ask": self.best_ask,
            "resting_orders": self.count,
            "trades": self.trades,
            "last_trade_price": self.last_trade_price
        }
