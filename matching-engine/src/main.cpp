#include "engine.hpp"
#include <iostream>
int main() {
  MatchingEngine engine;
  engine.submit({1, "BTC-USD", Side::Sell, OrderType::Limit, 0.50, 67000.0});
  engine.submit({2, "BTC-USD", Side::Buy, OrderType::Limit, 0.20, 67100.0});
  engine.submit({3, "BTC-USD", Side::Buy, OrderType::Market, 0.10, 0.0});
  std::cout << "Demo complete. Resting orders: " << engine.resting_orders().size() << "\n";
  return 0;
}
