#pragma once
#include "order.hpp"
#include <algorithm>
inline bool crosses(const Order& incoming, const Order& resting) {
  if (incoming.symbol != resting.symbol || incoming.side == resting.side) return false;
  if (incoming.type == OrderType::Market) return true;
  return incoming.side == Side::Buy
    ? incoming.limit_price >= resting.limit_price
    : incoming.limit_price <= resting.limit_price;
}
