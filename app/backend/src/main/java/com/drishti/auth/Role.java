package com.drishti.auth;

/**
 * OPERATOR runs inspections and reads the dashboard. OWNER additionally tunes
 * thresholds and triggers recomputation — the shop-floor/shop-owner split the
 * project is built around.
 */
public enum Role {
    OPERATOR,
    OWNER
}
