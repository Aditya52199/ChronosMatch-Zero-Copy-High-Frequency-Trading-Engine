#include "engine.hpp"
#include "match.hpp"
#include <iostream>
void MatchingEngine::submit(const Order& incoming) {
  if (incoming.quantity <= 0) { std::cerr << "Rejected: quantity must be positive\n"; return; }
  double remaining = incoming.quantity;
  for (auto it = orders_.begin(); it != orders_.end() && remaining > 0;) {
    if (crosses(incoming, *it)) {
      const double traded = std::min(remaining, it->quantity);
      remaining -= traded;
      it->quantity -= traded;
      std::cout << "TRADE " << incoming.symbol << " qty=" << traded
                << " price=" << it->limit_price << "\n";
      if (it->quantity <= 1e-9) it = orders_.erase(it); else ++it;
    } else ++it;
  }
  if (remaining > 1e-9 && incoming.type == OrderType::Limit) {
    Order resting = incoming; resting.quantity = remaining; orders_.push_back(resting);
    std::cout << "RESTING order id=" << resting.id << " qty=" << remaining << "\n";
  } else if (remaining > 1e-9) {
    std::cout << "MARKET remainder cancelled qty=" << remaining << "\n";
  }
}
