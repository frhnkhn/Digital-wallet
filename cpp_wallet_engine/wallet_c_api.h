/**
 * wallet_c_api.h - extern "C" API for Python ctypes integration
 * Language: C++ with C linkage
 *
 * Python uses ctypes to call these functions from libwallet.so.
 * extern "C" prevents C++ name mangling so ctypes can find the symbols.
 */

#ifndef WALLET_C_API_H
#define WALLET_C_API_H

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Wallet operations ---- */

/**
 * wallet_load - Load a wallet into the engine with its current balance.
 * Call this for each user at startup (data comes from SQLite via Python).
 * Returns 1 on success, 0 on failure.
 */
int    wallet_load(const char* wallet_id, double balance, const char* owner_id);

/**
 * wallet_get_balance - Returns the current balance of a wallet.
 * Returns -1.0 if wallet not found.
 */
double wallet_get_balance(const char* wallet_id);

/**
 * wallet_add_money - Credits amount to wallet_id.
 * Returns 1 on success, 0 on failure.
 */
int    wallet_add_money(const char* wallet_id, double amount, const char* description);

/**
 * wallet_transfer - Transfers amount from sender to receiver.
 * Returns codes:
 *   0 = SUCCESS
 *   1 = INSUFFICIENT_FUNDS
 *   2 = SENDER_NOT_FOUND
 *   3 = RECEIVER_NOT_FOUND
 *   4 = SENDER_BLOCKED
 *   5 = RECEIVER_BLOCKED
 *   6 = INVALID_AMOUNT
 */
int    wallet_transfer(const char* from_wallet_id, const char* to_wallet_id,
                       double amount, const char* description);

/**
 * wallet_get_stats_total_money - Returns total money across all loaded wallets.
 */
double wallet_get_stats_total_money(void);

/**
 * wallet_get_stats_total_transactions - Returns total transactions processed.
 */
int    wallet_get_stats_total_transactions(void);

#ifdef __cplusplus
}
#endif

#endif /* WALLET_C_API_H */
