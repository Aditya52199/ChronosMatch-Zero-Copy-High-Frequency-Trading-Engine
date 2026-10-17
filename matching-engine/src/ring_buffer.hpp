#pragma once
#include <array>
#include <atomic>
#include <cstddef>
// Single-producer/single-consumer demonstration queue; not a general MPMC queue.
template <typename T, std::size_t Capacity>
class RingBuffer {
  static_assert(Capacity > 1, "Capacity must be > 1");
 public:
  bool push(const T& value) {
    const auto head = head_.load(std::memory_order_relaxed);
    const auto next = (head + 1) % Capacity;
    if (next == tail_.load(std::memory_order_acquire)) return false;
    data_[head] = value;
    head_.store(next, std::memory_order_release);
    return true;
  }
  bool pop(T& value) {
    const auto tail = tail_.load(std::memory_order_relaxed);
    if (tail == head_.load(std::memory_order_acquire)) return false;
    value = data_[tail];
    tail_.store((tail + 1) % Capacity, std::memory_order_release);
    return true;
  }
 private:
  std::array<T, Capacity> data_{};
  std::atomic<std::size_t> head_{0}, tail_{0};
};
