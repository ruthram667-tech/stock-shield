package com.stockshield.model;

/**
 * Stock level classification based on current weight relative to full weight.
 */
public enum StockLevel {
    FULL,       // > 80%
    ADEQUATE,   // 40–80%
    LOW,        // 20–40%
    CRITICAL,   // 5–20%
    EMPTY       // < 5%
}
