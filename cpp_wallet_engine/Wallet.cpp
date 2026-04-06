/**
 * Wallet.cpp - Implementation of Wallet class
 */

#include "Wallet.h"
#include <sstream>
#include <iomanip>

Wallet::Wallet(const std::string& walletId, const std::string& ownerId,
               double initialBalance)
    : Entity(walletId), ownerId(ownerId), balance(initialBalance)
{}

bool Wallet::credit(double amount, const std::string& fromId,
                    const std::string& txnId, const std::string& desc) {
    if (amount <= 0.0) return false;
    balance += amount;
    Transaction t(txnId, fromId, id, amount, TransactionType::CREDIT,
                  desc.empty() ? "Money received" : desc);
    transactions.push_back(t);
    return true;
}

bool Wallet::debit(double amount, const std::string& toId,
                   const std::string& txnId, const std::string& desc) {
    if (amount <= 0.0 || amount > balance) return false;
    balance -= amount;
    Transaction t(txnId, id, toId, amount, TransactionType::DEBIT,
                  desc.empty() ? "Money sent" : desc);
    transactions.push_back(t);
    return true;
}

std::string Wallet::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    oss << "[Wallet:" << id << "] "
        << "Owner:" << ownerId
        << " Balance:" << balance
        << " Transactions:" << transactions.size();
    return oss.str();
}
