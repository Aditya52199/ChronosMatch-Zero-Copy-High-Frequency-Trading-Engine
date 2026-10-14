from dataclasses import dataclass
from typing import Protocol
@dataclass
class Tick:
    symbol: str
    price: float
    timestamp: float
class FeedConnector(Protocol):
    def latest_ticks(self) -> list[Tick]: ...
