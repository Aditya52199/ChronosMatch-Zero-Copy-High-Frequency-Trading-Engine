
import struct
from dataclasses import dataclass


# Fixed-size binary record:
# order_id, side, price_ticks, quantity, timestamp_ns
ORDER_FORMAT = "!QBQIQ"
ORDER_SIZE = struct.calcsize(ORDER_FORMAT)

BUY = 0
SELL = 1


@dataclass(frozen=True)
class Order:
    order_id: int
    side: int
    price_ticks: int
    quantity: int
    timestamp_ns: int


def validate_order(order: Order) -> None:
    if not 0 <= order.order_id <= 2**64 - 1:
        raise ValueError("order_id must fit in an unsigned 64-bit integer")

    if order.side not in (BUY, SELL):
        raise ValueError("side must be BUY (0) or SELL (1)")

    if not 0 <= order.price_ticks <= 2**64 - 1:
        raise ValueError("price_ticks must fit in an unsigned 64-bit integer")

    if not 1 <= order.quantity <= 2**32 - 1:
        raise ValueError("quantity must be a positive unsigned 32-bit integer")

    if not 0 <= order.timestamp_ns <= 2**64 - 1:
        raise ValueError("timestamp_ns must fit in an unsigned 64-bit integer")


def pack_order(order: Order) -> bytes:
    validate_order(order)

    return struct.pack(
        ORDER_FORMAT,
        order.order_id,
        order.side,
        order.price_ticks,
        order.quantity,
        order.timestamp_ns,
    )


def unpack_order(data: bytes) -> Order:
    if len(data) != ORDER_SIZE:
        raise ValueError(
            f"Expected exactly {ORDER_SIZE} bytes, received {len(data)}"
        )

    order_id, side, price_ticks, quantity, timestamp_ns = (
        struct.unpack(ORDER_FORMAT, data)
    )

    order = Order(
        order_id=order_id,
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )

    validate_order(order)
    return order
