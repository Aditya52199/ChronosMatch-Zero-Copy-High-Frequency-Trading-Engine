from dataclasses import dataclass
@dataclass
class MarginResult:
    notional: float
    initial_margin: float
    maintenance_margin: float
    liquidation_buffer: float
def calculate_margin(quantity: float, mark_price: float, leverage: float,
                     maintenance_rate: float = 0.005) -> MarginResult:
    if quantity < 0 or mark_price <= 0 or leverage < 1 or not 0 < maintenance_rate < 1:
        raise ValueError("Invalid margin inputs")
    notional = quantity * mark_price
    initial = notional / leverage
    maintenance = notional * maintenance_rate
    return MarginResult(notional, initial, maintenance, max(0.0, initial - maintenance))
if __name__ == "__main__":
    print(calculate_margin(quantity=0.1, mark_price=67250, leverage=2))
