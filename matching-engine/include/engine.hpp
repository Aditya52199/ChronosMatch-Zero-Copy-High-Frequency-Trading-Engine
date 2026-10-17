#pragma once
#include "order.hpp"
#include <vector>
class MatchingEngine {
 public:
  void submit(const Order& order);
  const std::vector<Order>& resting_orders() const { return orders_; }
 private:
  std::vector<Order> orders_;
};
