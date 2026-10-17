"""Fixed-width SPSC shared-memory ring protocol (little-endian, version 2)."""
from __future__ import annotations

import mmap
import os
import struct
import time
from dataclasses import dataclass

MAGIC = b"CHRM"
VERSION = 2
HEADER = struct.Struct("<4sIIIIQQ")
# Each raw order record contains exactly: uint64 order ID, int64 price ticks,
# int64 quantity lots. Direction and type are encoded in the ID's high bits.
ORDER = struct.Struct("<Qqq")
HEADER_SIZE = HEADER.size
RECORD_SIZE = ORDER.size
DEFAULT_CAPACITY = 65_536
SIDE_BUY = 0
SIDE_SELL = 1
TYPE_LIMIT = 0
TYPE_MARKET = 1
_ID_MASK = (1 << 62) - 1
_SIDE_SHIFT = 62
_TYPE_SHIFT = 63


@dataclass(frozen=True, slots=True)
class Order:
    order_id: int
    price_ticks: int
    quantity_lots: int
    side: int
    order_type: int = TYPE_LIMIT


class SharedOrderRing:
    """Single-producer/single-consumer ring; exactly one writer and reader."""

    def __init__(self, path: str, capacity: int = DEFAULT_CAPACITY, *, create: bool = False):
        if capacity < 2:
            raise ValueError("capacity must be at least two")
        self.path = path
        self.capacity = capacity
        self._file = open(path, "r+b" if not create else "w+b", buffering=0)
        size = HEADER_SIZE + capacity * RECORD_SIZE
        if create:
            self._file.truncate(size)
        elif os.fstat(self._file.fileno()).st_size != size:
            self._file.close()
            raise ValueError("ring file size does not match capacity")
        self._map = mmap.mmap(self._file.fileno(), size, access=mmap.ACCESS_WRITE)
        if create:
            HEADER.pack_into(self._map, 0, MAGIC, VERSION, capacity, RECORD_SIZE, 0, 0, 0)
        else:
            magic, version, stored_capacity, record_size, _, _, _ = HEADER.unpack_from(self._map)
            if (magic, version, stored_capacity, record_size) != (MAGIC, VERSION, capacity, RECORD_SIZE):
                self.close()
                raise ValueError("incompatible ring header")

    def _indexes(self) -> tuple[int, int]:
        return HEADER.unpack_from(self._map)[-2:]

    def try_write(self, order: Order) -> bool:
        return self.try_write_fields(order.order_id, order.price_ticks, order.quantity_lots,
                                     order.side, order.order_type)

    def try_write_fields(self, order_id: int, price_ticks: int, quantity_lots: int,
                         side: int, order_type: int = TYPE_LIMIT) -> bool:
        """Write primitive fields directly, avoiding a per-order Python object."""
        if not 0 <= order_id <= _ID_MASK:
            raise ValueError("order_id must fit in 62 bits")
        if price_ticks < 0 or quantity_lots <= 0:
            raise ValueError("price must be non-negative and quantity must be positive")
        if side not in (SIDE_BUY, SIDE_SELL) or order_type not in (TYPE_LIMIT, TYPE_MARKET):
            raise ValueError("invalid side or order type")
        head, tail = self._indexes()
        if head - tail >= self.capacity:
            return False
        offset = HEADER_SIZE + (head % self.capacity) * RECORD_SIZE
        encoded_id = order_id | (side << _SIDE_SHIFT) | (order_type << _TYPE_SHIFT)
        ORDER.pack_into(self._map, offset, encoded_id, price_ticks, quantity_lots)
        struct.pack_into("<Q", self._map, 20, head + 1)
        return True

    def try_read(self) -> Order | None:
        head, tail = self._indexes()
        if tail == head:
            return None
        offset = HEADER_SIZE + (tail % self.capacity) * RECORD_SIZE
        encoded_id, price_ticks, quantity_lots = ORDER.unpack_from(self._map, offset)
        struct.pack_into("<Q", self._map, 28, tail + 1)
        return Order(encoded_id & _ID_MASK, price_ticks, quantity_lots,
                     (encoded_id >> _SIDE_SHIFT) & 1,
                     (encoded_id >> _TYPE_SHIFT) & 1)

    def wait_read(self, timeout: float = 0.05) -> Order | None:
        deadline = time.monotonic() + timeout
        while True:
            order = self.try_read()
            if order is not None or time.monotonic() >= deadline:
                return order
            time.sleep(0)

    def close(self) -> None:
        if getattr(self, "_map", None) is not None:
            self._map.close()
            self._map = None
        if getattr(self, "_file", None) is not None:
            self._file.close()
            self._file = None

    def __enter__(self) -> "SharedOrderRing":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
