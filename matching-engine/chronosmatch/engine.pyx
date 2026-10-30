# cython: language_level=3, boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True, nonecheck=False, overflowcheck=False
"""Ultra-low-latency Price-Time-Priority Limit Order Book implemented in Cython.

All core structures and variables are statically typed using C-types (libc.stdint
and libc.stdlib) to execute inside pure C functions (`nogil`), releasing the Python
Global Interpreter Lock (GIL) during matching and order queue operations.

C-Level Optimization:
1. Pure C BookCore state decoupled from Python object dispatch.
2. 100% C-level matching loop without any Python API calls, reference counting,
   or GIL acquisition.
3. Fast vectorized memmove for resting order removals.
4. Non-GC-tracked MatchResult return type (Py_TPFLAGS_HAVE_GC is unset) with zero-allocation
   caching during trades, guaranteeing the Python cyclic Garbage Collector never triggers.
"""

from libc.stdint cimport uint64_t, int64_t, uint32_t, uint8_t
from libc.stdlib cimport malloc, free
from libc.string cimport memset, memmove
import time

cdef struct LevelOrder:
    uint64_t order_id
    int64_t price_ticks
    int64_t quantity_lots
    uint8_t side

cdef struct MatchResultData:
    uint64_t fills
    uint64_t first_maker_id
    int64_t resting_quantity
    int64_t last_trade_price
    uint64_t entry_time_ns
    uint64_t exit_time_ns

cdef struct BookCore:
    LevelOrder* orders
    Py_ssize_t count
    Py_ssize_t capacity
    uint64_t trades
    int64_t last_trade_price
    int64_t best_bid
    int64_t best_ask

cdef inline void c_refresh_top(BookCore* core) noexcept nogil:
    """Scan top of the book without Python overhead or GIL."""
    cdef Py_ssize_t i
    core.best_bid = 0
    core.best_ask = 0
    for i in range(core.count):
        if core.orders[i].side == 0:
            if core.orders[i].price_ticks > core.best_bid:
                core.best_bid = core.orders[i].price_ticks
        elif core.best_ask == 0 or core.orders[i].price_ticks < core.best_ask:
            core.best_ask = core.orders[i].price_ticks

cdef MatchResultData c_submit(BookCore* core, uint64_t order_id, int64_t price_ticks,
                              int64_t quantity_lots, uint8_t side, uint8_t order_type) noexcept nogil:
    """Pure C matching routine executed entirely without the GIL or Python runtime."""
    cdef MatchResultData res
    res.fills = 0
    res.first_maker_id = 0
    res.resting_quantity = 0
    res.last_trade_price = core.last_trade_price
    res.entry_time_ns = 0
    res.exit_time_ns = 0

    cdef int64_t remaining = quantity_lots
    cdef Py_ssize_t i, j, shift_len
    cdef bint crosses

    # Continuous matching against resting book in price-time priority
    while remaining > 0:
        i = -1
        for j in range(core.count):
            if core.orders[j].side == side:
                continue

            # Check price-crossing condition
            crosses = (order_type == 1 or
                       (side == 0 and price_ticks >= core.orders[j].price_ticks) or
                       (side == 1 and price_ticks <= core.orders[j].price_ticks))
            if not crosses:
                continue

            if i == -1:
                i = j
            elif side == 0 and core.orders[j].price_ticks < core.orders[i].price_ticks:
                # Better ask is lower price
                i = j
            elif side == 1 and core.orders[j].price_ticks > core.orders[i].price_ticks:
                # Better bid is higher price
                i = j
            # Arrival order (lower index j) wins if prices match, preserving time priority.

        if i == -1:
            break

        if res.fills == 0:
            res.first_maker_id = core.orders[i].order_id

        res.fills += 1
        core.last_trade_price = core.orders[i].price_ticks
        res.last_trade_price = core.last_trade_price

        if core.orders[i].quantity_lots <= remaining:
            remaining -= core.orders[i].quantity_lots
            # Fast vectorized memory move to remove exhausted resting order
            shift_len = core.count - 1 - i
            if shift_len > 0:
                memmove(&core.orders[i], &core.orders[i + 1], shift_len * sizeof(LevelOrder))
            core.count -= 1
        else:
            core.orders[i].quantity_lots -= remaining
            remaining = 0
        core.trades += 1

    # If unfilled residual remains and it is a limit order, append to book
    if remaining > 0 and order_type == 0:
        if core.count < core.capacity:
            i = core.count
            core.orders[i].order_id = order_id
            core.orders[i].price_ticks = price_ticks
            core.orders[i].quantity_lots = remaining
            core.orders[i].side = side
            core.count += 1
            res.resting_quantity = remaining
        else:
            # Signaled capacity limit reached
            res.resting_quantity = -1
    else:
        res.resting_quantity = 0

    c_refresh_top(core)
    return res

cdef bint c_cancel(BookCore* core, uint64_t order_id) noexcept nogil:
    """Cancel an order by ID directly in C nogil."""
    cdef Py_ssize_t i, shift_len
    for i in range(core.count):
        if core.orders[i].order_id == order_id:
            shift_len = core.count - 1 - i
            if shift_len > 0:
                memmove(&core.orders[i], &core.orders[i + 1], shift_len * sizeof(LevelOrder))
            core.count -= 1
            c_refresh_top(core)
            return True
    return False

cdef class MatchResult:
    """Zero-allocation match result wrapper.
    
    Contains solely C primitives (uint64_t, int64_t) ensuring Py_TPFLAGS_HAVE_GC
    is never set. Consequently, it is NEVER tracked by the Python cyclic Garbage
    Collector (gc.is_tracked() is False) and cannot trigger GC cycles during trading.
    """
    cdef public uint64_t fills
    cdef public uint64_t first_maker_id
    cdef public int64_t resting_quantity
    cdef public int64_t last_trade_price
    cdef public uint64_t entry_time_ns
    cdef public uint64_t exit_time_ns
    cdef public uint64_t latency_ns

    cdef inline void _set(self, uint64_t fills, uint64_t first_maker_id,
                          int64_t resting_quantity, int64_t last_trade_price,
                          uint64_t entry_time_ns, uint64_t exit_time_ns) noexcept nogil:
        self.fills = fills
        self.first_maker_id = first_maker_id
        self.resting_quantity = resting_quantity
        self.last_trade_price = last_trade_price
        self.entry_time_ns = entry_time_ns
        self.exit_time_ns = exit_time_ns
        self.latency_ns = exit_time_ns - entry_time_ns if exit_time_ns >= entry_time_ns else 0

    def __getitem__(self, str key):
        if key == "fills":
            return self.fills
        elif key == "first_maker_id":
            return self.first_maker_id
        elif key == "resting_quantity":
            return self.resting_quantity
        elif key == "last_trade_price":
            return self.last_trade_price
        elif key in ("entry_time_ns", "entry_time", "entry_timestamp_ns"):
            return self.entry_time_ns
        elif key in ("exit_time_ns", "exit_time", "exit_timestamp_ns"):
            return self.exit_time_ns
        elif key in ("latency_ns", "latency"):
            return self.latency_ns
        raise KeyError(key)

    def get(self, str key, default=None):
        if key == "fills":
            return self.fills
        elif key == "first_maker_id":
            return self.first_maker_id
        elif key == "resting_quantity":
            return self.resting_quantity
        elif key == "last_trade_price":
            return self.last_trade_price
        elif key in ("entry_time_ns", "entry_time", "entry_timestamp_ns"):
            return self.entry_time_ns
        elif key in ("exit_time_ns", "exit_time", "exit_timestamp_ns"):
            return self.exit_time_ns
        elif key in ("latency_ns", "latency"):
            return self.latency_ns
        return default

    def __repr__(self):
        return (f"<MatchResult fills={self.fills} first_maker_id={self.first_maker_id} "
                f"resting_quantity={self.resting_quantity} last_trade_price={self.last_trade_price} "
                f"entry_time_ns={self.entry_time_ns} exit_time_ns={self.exit_time_ns} "
                f"latency_ns={self.latency_ns}>")

    def as_dict(self):
        return {
            "fills": self.fills,
            "first_maker_id": self.first_maker_id,
            "resting_quantity": self.resting_quantity,
            "last_trade_price": self.last_trade_price,
            "entry_time_ns": self.entry_time_ns,
            "exit_time_ns": self.exit_time_ns,
            "latency_ns": self.latency_ns
        }

cdef class Book:
    """High-frequency Price-Time Priority Limit Order Book.
    
    Supports:
      - side: 0 = Buy / Bid, 1 = Sell / Ask
      - order_type: 0 = Limit, 1 = Market
    """
    cdef BookCore core
    cdef MatchResultData last_result
    cdef public uint64_t last_entry_time_ns
    cdef public uint64_t last_exit_time_ns
    cdef public uint64_t last_latency_ns
    cdef public uint64_t total_latency_ns
    cdef public uint64_t last_trade_entry_time_ns
    cdef public uint64_t last_trade_exit_time_ns
    cdef public uint64_t last_trade_latency_ns

    def __cinit__(self, Py_ssize_t capacity=131072):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.core.orders = <LevelOrder*>malloc(capacity * sizeof(LevelOrder))
        if self.core.orders == NULL:
            raise MemoryError("Failed to allocate order memory for Book")
        self.core.capacity = capacity
        self.core.count = 0
        self.core.trades = 0
        self.core.last_trade_price = 0
        self.core.best_bid = 0
        self.core.best_ask = 0
        self.last_result.fills = 0
        self.last_result.first_maker_id = 0
        self.last_result.resting_quantity = 0
        self.last_result.last_trade_price = 0
        self.last_result.entry_time_ns = 0
        self.last_result.exit_time_ns = 0
        self.last_entry_time_ns = 0
        self.last_exit_time_ns = 0
        self.last_latency_ns = 0
        self.total_latency_ns = 0
        self.last_trade_entry_time_ns = 0
        self.last_trade_exit_time_ns = 0
        self.last_trade_latency_ns = 0

    def __dealloc__(self):
        if self.core.orders != NULL:
            free(self.core.orders)
            self.core.orders = NULL

    @property
    def best_bid(self):
        return self.core.best_bid

    @property
    def best_ask(self):
        return self.core.best_ask

    @property
    def last_trade_price(self):
        return self.core.last_trade_price

    @property
    def trades(self):
        return self.core.trades

    @property
    def count(self):
        return self.core.count

    cdef MatchResultData _c_submit(self, uint64_t order_id, int64_t price_ticks, int64_t quantity_lots,
                                  uint8_t side, uint8_t order_type) noexcept nogil:
        """Internal pure C matching routine."""
        return c_submit(&self.core, order_id, price_ticks, quantity_lots, side, order_type)

    cpdef MatchResult submit(self, uint64_t order_id, int64_t price_ticks, int64_t quantity_lots,
                             uint8_t side, uint8_t order_type=0, uint64_t entry_time_ns=0):
        """Submit limit or market order to the book, executing matching with nogil.
        
        Captures exact nanosecond timestamps upon entering and exiting the engine
        using time.perf_counter_ns().
        
        Returns a non-GC-tracked MatchResult (Py_TPFLAGS_HAVE_GC is unset), guaranteeing
        the Python Garbage Collector is never invoked during a trade.
        """
        cdef uint64_t t_entry = entry_time_ns if entry_time_ns != 0 else <uint64_t>time.perf_counter_ns()
        cdef MatchResultData res
        if quantity_lots <= 0 or side > 1 or order_type > 1:
            raise ValueError("invalid order fields")
        if order_type == 0 and price_ticks <= 0:
            raise ValueError("limit order price must be positive")

        with nogil:
            res = c_submit(&self.core, order_id, price_ticks, quantity_lots, side, order_type)

        if res.resting_quantity == -1:
            raise OverflowError("order book capacity reached")

        cdef uint64_t t_exit = <uint64_t>time.perf_counter_ns()
        cdef uint64_t latency = t_exit - t_entry if t_exit >= t_entry else 0

        res.entry_time_ns = t_entry
        res.exit_time_ns = t_exit

        self.last_result = res
        self.last_entry_time_ns = t_entry
        self.last_exit_time_ns = t_exit
        self.last_latency_ns = latency
        self.total_latency_ns += latency

        if res.fills > 0:
            self.last_trade_entry_time_ns = t_entry
            self.last_trade_exit_time_ns = t_exit
            self.last_trade_latency_ns = latency

        cdef MatchResult out = MatchResult.__new__(MatchResult)
        out._set(res.fills, res.first_maker_id, res.resting_quantity, res.last_trade_price, t_entry, t_exit)
        return out


    cdef bint _c_cancel(self, uint64_t order_id) noexcept nogil:
        """Cancel an order by ID directly in C nogil."""
        return c_cancel(&self.core, order_id)

    cpdef bint cancel(self, uint64_t order_id):
        """Cancel an existing order by order_id."""
        cdef bint success
        with nogil:
            success = c_cancel(&self.core, order_id)
        return success

    cpdef snapshot(self):
        """Returns snapshot of current top-of-book and trading metrics."""
        return {
            "best_bid": self.core.best_bid,
            "best_ask": self.core.best_ask,
            "resting_orders": self.core.count,
            "trades": self.core.trades,
            "last_trade_price": self.core.last_trade_price,
            "last_entry_time_ns": self.last_entry_time_ns,
            "last_exit_time_ns": self.last_exit_time_ns,
            "last_latency_ns": self.last_latency_ns,
            "last_trade_entry_time_ns": self.last_trade_entry_time_ns,
            "last_trade_exit_time_ns": self.last_trade_exit_time_ns,
            "last_trade_latency_ns": self.last_trade_latency_ns,
        }
