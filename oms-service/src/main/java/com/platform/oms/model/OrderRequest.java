package com.platform.oms.model;
public record OrderRequest(String symbol, String side, double quantity, String type, Double limitPrice) {}
