/**
 * wallet_c_api.cpp - Implementation of the C-compatible API
 * Bridges ctypes (Python) → C API → WalletEngine (C++) 
 */

#include "wallet_c_api.h"
#include "WalletEngine.h"
#include <cstring>

/* Helper to get the singleton engine */
static WalletEngine* engine() {
    return WalletEngine::getInstance();
}

int wallet_load(const char* wallet_id, double balance, const char* owner_id) {
    if (!wallet_id || !owner_id) return 0;
    return engine()->loadWallet(std::string(wallet_id), balance,
                                 std::string(owner_id)) ? 1 : 0;
}

double wallet_get_balance(const char* wallet_id) {
    if (!wallet_id) return -1.0;
    return engine()->getBalance(std::string(wallet_id));
}

int wallet_add_money(const char* wallet_id, double amount, const char* description) {
    if (!wallet_id) return 0;
    std::string desc = description ? std::string(description) : "";
    return engine()->addMoney(std::string(wallet_id), amount, desc) ? 1 : 0;
}

int wallet_transfer(const char* from_wallet_id, const char* to_wallet_id,
                    double amount, const char* description) {
    if (!from_wallet_id || !to_wallet_id) return 2; /* SENDER_NOT_FOUND */
    std::string desc = description ? std::string(description) : "";
    TransferResult result = engine()->transfer(
        std::string(from_wallet_id),
        std::string(to_wallet_id),
        amount, desc
    );
    return static_cast<int>(result);
}

double wallet_get_stats_total_money(void) {
    return engine()->getStats().totalMoneyInSystem;
}

int wallet_get_stats_total_transactions(void) {
    return engine()->getStats().totalTransactions;
}
