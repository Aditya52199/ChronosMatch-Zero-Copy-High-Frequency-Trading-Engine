from collections import defaultdict
from dataclasses import dataclass
@dataclass
class Candle:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
class CandleAggregator:
    def __init__(self):
        self._prices = defaultdict(list)
    def add(self, symbol: str, price: float) -> None:
        if price <= 0:
            raise ValueError("price must be positive")
        self._prices[symbol].append(price)
    def snapshot(self) -> list[Candle]:
        result = []
        for symbol, values in self._prices.items():
            result.append(Candle(symbol, values[0], max(values), min(values), values[-1], float(len(values))))
        return result
