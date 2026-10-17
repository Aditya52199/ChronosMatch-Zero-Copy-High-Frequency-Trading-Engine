# cython: language_level=3, boundscheck=False, wraparound=False, initializedcheck=False
"""Cython price-time-priority book. Prices/quantities use integer ticks/lots."""
from libc.stdint cimport uint64_t, int64_t
from libc.stdlib cimport malloc, free

ctypedef struct LevelOrder:
    uint64_t order_id
    int64_t price_ticks
    int64_t quantity_lots
    unsigned char side

cdef class Book:
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
            raise MemoryError()
        self.capacity = capacity
        self.count = 0
        self.trades = 0
        self.last_trade_price = 0
        self.best_bid = 0
        self.best_ask = 0

    def __dealloc__(self):
        if self.orders != NULL:
            free(self.orders)

    cpdef submit(self, uint64_t order_id, int64_t price_ticks, int64_t quantity_lots,
                 unsigned char side, unsigned char order_type=0):
        cdef int64_t remaining = quantity_lots
        cdef Py_ssize_t i, j
        cdef bint crosses
        cdef uint64_t fill_count = 0
        cdef uint64_t first_fill_id = 0
        if quantity_lots <= 0 or side > 1 or order_type > 1:
            raise ValueError("invalid order fields")
        if order_type == 0 and price_ticks <= 0:
            raise ValueError("limit order price must be positive")

        # Book is maintained in arrival order; scan for the best crossing order,
        # resolving equal prices by earliest timestamp.
        while remaining > 0:
            i = -1
            for j in range(self.count):
                if self.orders[j].side == side:
                    continue
                crosses = (order_type == 1 or
                           (side == 0 and price_ticks >= self.orders[j].price_ticks) or
                           (side == 1 and price_ticks <= self.orders[j].price_ticks))
                if not crosses:
                    continue
                if i == -1:
                    i = j
                elif side == 0 and self.orders[j].price_ticks < self.orders[i].price_ticks:
                    i = j
                elif side == 1 and self.orders[j].price_ticks > self.orders[i].price_ticks:
                    i = j
            if i == -1:
                break
            if fill_count == 0:
                first_fill_id = self.orders[i].order_id
            fill_count += 1
            self.last_trade_price = self.orders[i].price_ticks
            if self.orders[i].quantity_lots <= remaining:
                remaining -= self.orders[i].quantity_lots
                for j in range(i, self.count - 1):
                    self.orders[j] = self.orders[j + 1]
                self.count -= 1
            else:
                self.orders[i].quantity_lots -= remaining
                remaining = 0
            self.trades += 1

        if remaining > 0 and order_type == 0:
            if self.count == self.capacity:
                raise OverflowError("order book capacity reached")
            i = self.count
            self.orders[i].order_id = order_id
            self.orders[i].price_ticks = price_ticks
            self.orders[i].quantity_lots = remaining
            self.orders[i].side = side
            self.count += 1
        self._refresh_top()
        return {"fills": fill_count, "first_maker_id": first_fill_id,
                "resting_quantity": remaining if order_type == 0 else 0,
                "last_trade_price": self.last_trade_price}

    cdef void _refresh_top(self) noexcept:
        cdef Py_ssize_t i
        self.best_bid = 0
        self.best_ask = 0
        for i in range(self.count):
            if self.orders[i].side == 0:
                if self.orders[i].price_ticks > self.best_bid:
                    self.best_bid = self.orders[i].price_ticks
            elif self.best_ask == 0 or self.orders[i].price_ticks < self.best_ask:
                self.best_ask = self.orders[i].price_ticks

    cpdef snapshot(self):
        return {"best_bid": self.best_bid, "best_ask": self.best_ask,
                "resting_orders": self.count, "trades": self.trades,
                "last_trade_price": self.last_trade_price}
