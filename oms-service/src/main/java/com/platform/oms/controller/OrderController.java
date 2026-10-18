package com.platform.oms.controller;
import com.platform.oms.model.OrderRequest;
import com.platform.oms.model.OrderResponse;
import com.platform.oms.service.OrderService;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/oms/orders")
public class OrderController {
 private final OrderService service;
 public OrderController(OrderService service) { this.service = service; }
 @PostMapping public OrderResponse create(@RequestBody OrderRequest request) { return service.accept(request); }
}
