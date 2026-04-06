/**
 * WalletEngine.cpp - Singleton orchestration engine implementation
 */

#include "WalletEngine.h"
#include <sstream>
#include <iomanip>
#include <ctime>
#include <algorithm>

/* Initialize static singleton pointer */
WalletEngine* WalletEngine::instance = nullptr;

WalletEngine::WalletEngine() : txnCounter(0) {}

WalletEngine* WalletEngine::getInstance() {
    if (!instance) {
        instance = new WalletEngine();
    }
    return instance;
}

std::string WalletEngine::generateTxnId() {
    /* TXN-<timestamp>-<counter> */
    std::ostringstream oss;
    oss << "TXN" << time(nullptr) << std::setw(4) << std::setfill('0') << (++txnCounter);
    return oss.str();
}

Wallet WalletEngine::createWallet(const std::string& ownerId,
                                   const std::string& walletId) {
    Wallet w(walletId, ownerId, 0.0);
    wallets.emplace(walletId, w);
    return w;
}

bool WalletEngine::loadWallet(const std::string& walletId, double balance,
                               const std::string& ownerId) {
    Wallet w(walletId, ownerId, balance);
    wallets[walletId] = w;
    return true;
}

bool WalletEngine::addMoney(const std::string& walletId, double amount,
                             const std::string& desc) {
    if (amount <= 0.0) return false;
    auto it = wallets.find(walletId);
    if (it == wallets.end()) return false;

    std::string txnId = generateTxnId();
    bool ok = it->second.credit(amount, "SYSTEM", txnId,
                                 desc.empty() ? "Wallet top-up" : desc);
    if (ok) {
        /* Also record in global list */
        Transaction t(txnId, "SYSTEM", walletId, amount,
                       TransactionType::CREDIT, desc.empty() ? "Wallet top-up" : desc);
        allTransactions.push_back(t);
    }
    return ok;
}

TransferResult WalletEngine::transfer(const std::string& fromWalletId,
                                       const std::string& toWalletId,
                                       double amount,
                                       const std::string& desc) {
    if (amount <= 0.0)
        return TransferResult::INVALID_AMOUNT;

    auto fromIt = wallets.find(fromWalletId);
    if (fromIt == wallets.end())
        return TransferResult::SENDER_NOT_FOUND;

    auto toIt = wallets.find(toWalletId);
    if (toIt == wallets.end())
        return TransferResult::RECEIVER_NOT_FOUND;

    if (fromIt->second.getBalance() < amount)
        return TransferResult::INSUFFICIENT_FUNDS;

    std::string txnId = generateTxnId();
    std::string note  = desc.empty() ? "Money transfer" : desc;

    /* Debit sender */
    fromIt->second.debit(amount, toWalletId, txnId, note);
    /* Credit receiver */
    toIt->second.credit(amount, fromWalletId, txnId, note);

    /* Record in global list */
    Transaction t(txnId, fromWalletId, toWalletId, amount,
                   TransactionType::DEBIT, note);
    allTransactions.push_back(t);

    return TransferResult::SUCCESS;
}

double WalletEngine::getBalance(const std::string& walletId) const {
    auto it = wallets.find(walletId);
    if (it == wallets.end()) return -1.0;
    return it->second.getBalance();
}

std::vector<Transaction> WalletEngine::getTransactions(
        const std::string& walletId) const {
    auto it = wallets.find(walletId);
    if (it == wallets.end()) return {};
    return it->second.getTransactions();
}

WalletStats WalletEngine::getStats() const {
    WalletStats stats{};
    stats.totalUsers        = (int)wallets.size();
    stats.totalTransactions = (int)allTransactions.size();
    stats.blockedUsers      = 0; /* Managed in Python layer */

    double total = 0.0, volume = 0.0;
    for (auto& kv : wallets)
        total += kv.second.getBalance();
    for (auto& t : allTransactions)
        volume += t.getAmount();

    stats.totalMoneyInSystem     = total;
    stats.totalTransactionVolume = volume;
    return stats;
}
