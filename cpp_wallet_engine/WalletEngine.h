/**
 * WalletEngine.h - Core orchestration engine
 * Language: C++
 * OOP Concepts: Singleton pattern, composition, polymorphism
 */

#ifndef WALLETENGINE_H
#define WALLETENGINE_H

#include "User.h"
#include "AdminUser.h"
#include "Wallet.h"
#include "Transaction.h"
#include <string>
#include <unordered_map>
#include <vector>

/* Transfer result codes */
enum class TransferResult {
    SUCCESS         = 0,
    INSUFFICIENT_FUNDS = 1,
    SENDER_NOT_FOUND   = 2,
    RECEIVER_NOT_FOUND = 3,
    SENDER_BLOCKED     = 4,
    RECEIVER_BLOCKED   = 5,
    INVALID_AMOUNT     = 6
};

/* System-wide statistics */
struct WalletStats {
    int    totalUsers;
    int    totalTransactions;
    double totalMoneyInSystem;
    double totalTransactionVolume;
    int    blockedUsers;
};

/**
 * WalletEngine - Singleton orchestrator for all wallet operations.
 * Uses composition: holds maps of Users and Wallets.
 */
class WalletEngine {
private:
    /* Singleton instance */
    static WalletEngine* instance;

    /* In-memory stores (source of truth is the SQLite DB) */
    std::unordered_map<std::string, Wallet>      wallets;      /* walletId -> Wallet */
    std::vector<Transaction>                      allTransactions;
    int                                            txnCounter;

    WalletEngine();  /* Private constructor for singleton */

    /* Generate a unique transaction ID */
    std::string generateTxnId();

public:
    /* Singleton access */
    static WalletEngine* getInstance();

    /* Wallet lifecycle */
    Wallet  createWallet(const std::string& ownerId, const std::string& walletId);
    bool    loadWallet(const std::string& walletId, double balance, const std::string& ownerId);

    /* Money operations */
    bool           addMoney(const std::string& walletId, double amount, const std::string& desc = "");
    TransferResult transfer(const std::string& fromWalletId,
                            const std::string& toWalletId,
                            double amount,
                            const std::string& desc = "");

    /* Query */
    double getBalance(const std::string& walletId) const;
    std::vector<Transaction> getTransactions(const std::string& walletId) const;
    WalletStats getStats() const;

    /* Prevent copying (Singleton) */
    WalletEngine(const WalletEngine&)            = delete;
    WalletEngine& operator=(const WalletEngine&) = delete;
    ~WalletEngine() = default;
};

#endif /* WALLETENGINE_H */
