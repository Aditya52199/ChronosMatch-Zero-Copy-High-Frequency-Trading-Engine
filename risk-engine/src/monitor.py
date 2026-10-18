from margin import calculate_margin

def monitor_position(quantity: float, mark_price: float, leverage: float, equity: float) -> dict:
    result = calculate_margin(quantity, mark_price, leverage)
    return {
        "notional": round(result.notional, 2),
        "initial_margin": round(result.initial_margin, 2),
        "maintenance_margin": round(result.maintenance_margin, 2),
        "equity": round(equity, 2),
        "warning": equity <= result.maintenance_margin,
        "note": "Illustrative calculation only; not a liquidation engine."
    }

if __name__ == "__main__":
    print(monitor_position(0.1, 67250, 2, 5000))
