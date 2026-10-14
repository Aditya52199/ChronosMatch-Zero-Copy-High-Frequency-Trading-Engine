import json
import time
from processor.aggregator import CandleAggregator

def main():
    # Simulated feed; replace with a documented exchange API/WebSocket connector.
    aggregator = CandleAggregator()
    demo_ticks = [("BTC-USD", 67250.12), ("ETH-USD", 3520.42), ("BTC-USD", 67260.50)]
    for symbol, price in demo_ticks:
        aggregator.add(symbol, price)
    payload = {"timestamp": time.time(), "candles": [c.__dict__ for c in aggregator.snapshot()]}
    print(json.dumps(payload, indent=2))
    print("Demo publisher finished; no live exchange feed is connected.")

if __name__ == "__main__":
    main()
