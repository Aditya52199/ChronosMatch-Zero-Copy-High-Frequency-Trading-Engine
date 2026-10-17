#pragma once
#include <cstdint>
#include <string>
enum class Side { Buy, Sell };
enum class OrderType { Market, Limit };
struct Order {
  std::uint64_t id{};
  std::string symbol;
  Side side{Side::Buy};
  OrderType type{OrderType::Limit};
  double quantity{};
  double limit_price{};
};
