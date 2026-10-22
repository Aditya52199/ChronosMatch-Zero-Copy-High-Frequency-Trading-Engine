"""Fixed-size mmap-backed binary ring buffer.

This MVP supports one producer and one consumer without concurrent access.
It uses fixed-size binary records and does not serialize through JSON or Pickle.
"""

import mmap
import struct
from pathlib import Path

from .order_format import ORDER_SIZE, Order, pack_order, unpack_order


_HEADER = struct.Struct("!QQ")
_HEADER_SIZE = _HEADER.size


class MmapRingBuffer:
    """File-backed circular buffer for fixed-size order records."""

    def __init__(self, path: str | Path, capacity: int = 1024):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")

        self.capacity = capacity
        self.path = Path(path)
        self._file = self.path.open("w+b")
        self._file.truncate(_HEADER_SIZE + capacity * ORDER_SIZE)
        self._map = mmap.mmap(self._file.fileno(), 0)

        # Header stores monotonically increasing write and read counters.
        _HEADER.pack_into(self._map, 0, 0, 0)
        self._closed = False

    def put(self, order: Order) -> None:
        """Write an order or raise BufferError when the buffer is full."""
        self._ensure_open()
        data = pack_order(order)

        write_pos, read_pos = _HEADER.unpack_from(self._map, 0)
        if write_pos - read_pos >= self.capacity:
            raise BufferError("Ring buffer is full")

        slot = write_pos % self.capacity
        offset = _HEADER_SIZE + slot * ORDER_SIZE
        self._map[offset : offset + ORDER_SIZE] = data

        _HEADER.pack_into(self._map, 0, write_pos + 1, read_pos)

    def get(self) -> Order | None:
        """Read the next order, or return None when the buffer is empty."""
        self._ensure_open()

        write_pos, read_pos = _HEADER.unpack_from(self._map, 0)
        if read_pos == write_pos:
            return None

        slot = read_pos % self.capacity
        offset = _HEADER_SIZE + slot * ORDER_SIZE
        data = self._map[offset : offset + ORDER_SIZE]
        order = unpack_order(data)

        _HEADER.pack_into(self._map, 0, write_pos, read_pos + 1)
        return order

    def _ensure_open(self) -> None:
        if self._closed:
            raise ValueError("Ring buffer is closed")

    def close(self) -> None:
        if not self._closed:
            self._map.close()
            self._file.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()