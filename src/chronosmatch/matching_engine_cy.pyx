
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

"""Cython-compiled price-time-priority matching engine."""

from chronosmatch.order_format import BUY, SELL, validate_order
from chronosmatch.matching_engine import Trade, _RestingOrder


class CythonOrderBook:
    """Order book with one sort per incoming order, not per fill."""

    def __init__(self):
        self._bids = []
        self._asks = []
        self._sequence = 0
        self._seen_order_ids = set()

    def submit_order(self, order):
        validate_order(order)

        if order.order_id in self._seen_order_ids:
            raise ValueError(f"Duplicate order ID: {order.order_id}")

        self._seen_order_ids.add(order.order_id)

        cdef unsigned long long incoming_quantity = order.quantity
        cdef unsigned long long incoming_price = order.price_ticks
        cdef unsigned long long resting_price
        cdef unsigned long long resting_quantity
        cdef unsigned long long fill_quantity
        cdef unsigned long long incoming_timestamp = order.timestamp_ns
        cdef unsigned long long resting_timestamp
        cdef bint crosses
        cdef object opposite
        cdef object resting
        cdef object trades = []

        opposite = self._asks if order.side == BUY else self._bids

        # Python's built-in sort executes in optimized native code.
        # Preserve price priority, then timestamp and insertion sequence.
        if order.side == BUY:
            opposite.sort(
                key=lambda item: (
                    item.order.price_ticks,
                    item.order.timestamp_ns,
                    item.sequence,
                )
            )
        else:
            opposite.sort(
                key=lambda item: (
                    -item.order.price_ticks,
                    item.order.timestamp_ns,
                    item.sequence,
                )
            )

        # The best order is now always at index zero.
        while incoming_quantity > 0 and opposite:
            resting = opposite[0]
            resting_price = resting.order.price_ticks

            if order.side == BUY:
                crosses = incoming_price >= resting_price
            else:
                crosses = incoming_price <= resting_price

            if not crosses:
                break

            resting_quantity = resting.remaining_quantity

            if incoming_quantity < resting_quantity:
                fill_quantity = incoming_quantity
            else:
                fill_quantity = resting_quantity

            if order.side == BUY:
                buy_id = order.order_id
                sell_id = resting.order.order_id
            else:
                buy_id = resting.order.order_id
                sell_id = order.order_id

            if incoming_timestamp > resting.order.timestamp_ns:
                resting_timestamp = incoming_timestamp
            else:
                resting_timestamp = resting.order.timestamp_ns

            trades.append(
                Trade(
                    buy_order_id=buy_id,
                    sell_order_id=sell_id,
                    price_ticks=resting_price,
                    quantity=fill_quantity,
                    timestamp_ns=resting_timestamp,
                )
            )

            incoming_quantity -= fill_quantity
            resting.remaining_quantity -= fill_quantity

            if resting.remaining_quantity == 0:
                opposite.pop(0)

        if incoming_quantity > 0:
            self._sequence += 1
            resting_order = _RestingOrder(
                order=order,
                remaining_quantity=incoming_quantity,
                sequence=self._sequence,
            )
            own_side = self._bids if order.side == BUY else self._asks
            own_side.append(resting_order)

        return trades

    @property
    def best_bid(self):
        cdef Py_ssize_t i
        cdef unsigned long long price
        cdef unsigned long long best_price = 0

        if not self._bids:
            return None

        for i in range(len(self._bids)):
            price = self._bids[i].order.price_ticks
            if i == 0 or price > best_price:
                best_price = price

        return best_price

    @property
    def best_ask(self):
        cdef Py_ssize_t i
        cdef unsigned long long price
        cdef unsigned long long best_price = 0

        if not self._asks:
            return None

        for i in range(len(self._asks)):
            price = self._asks[i].order.price_ticks
            if i == 0 or price < best_price:
                best_price = price

        return best_price

    @property
    def resting_order_count(self):
        return len(self._bids) + len(self._asks)

    @property
    def resting_orders(self):
        orders = []

        for item in self._bids:
            orders.append({
                "side": "BUY",
                "order_id": item.order.order_id,
                "price_ticks": item.order.price_ticks,
                "remaining_quantity": item.remaining_quantity,
                "timestamp_ns": item.order.timestamp_ns,
            })

        for item in self._asks:
            orders.append({
                "side": "SELL",
                "order_id": item.order.order_id,
                "price_ticks": item.order.price_ticks,
                "remaining_quantity": item.remaining_quantity,
                "timestamp_ns": item.order.timestamp_ns,
            })

        return sorted(
            orders,
            key=lambda order: (
                0 if order["side"] == "BUY" else 1,
                -order["price_ticks"]
                if order["side"] == "BUY"
                else order["price_ticks"],
                order["timestamp_ns"],
            ),
        )
