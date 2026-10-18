package com.platform.oms.service;
import com.platform.oms.model.OrderRequest;
import com.platform.oms.model.OrderResponse;
import org.springframework.stereotype.Service;
import java.util.UUID;
@Service
public class OrderService {
 public OrderResponse accept(OrderRequest r) {
  if (r == null || r.symbol() == null || r.symbol().isBlank() ||
      !("buy".equals(r.side()) || "sell".equals(r.side())) ||
      r.quantity() <= 0 || !("market".equals(r.type()) || "limit".equals(r.type()))) {
    throw new IllegalArgumentException("Invalid order fields");
  }
  if ("limit".equals(r.type()) && (r.limitPrice() == null || r.limitPrice() <= 0)) throw new IllegalArgumentException("Invalid limit price");
  return new OrderResponse("oms-" + UUID.randomUUID(), "ACCEPTED", "Demo acknowledgement only; no execution performed.");
 }
}
