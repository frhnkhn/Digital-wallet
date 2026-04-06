/**
 * Wallet.h - Wallet class for managing user balance
 * Language: C++
 * OOP Concepts: Encapsulation, composition
 */

#ifndef WALLET_H
#define WALLET_H

#include "Entity.h"
#include "Transaction.h"
#include <string>
#include <vector>

/**
 * Wallet - Holds a user's balance and transaction history.
 * Composed inside a User object.
 */
class Wallet : public Entity {
private:
    std::string ownerId;
    double      balance;
    std::vector<Transaction> transactions;

public:
    Wallet() : Entity(""), balance(0.0) {}
    Wallet(const std::string& walletId, const std::string& ownerId,
           double initialBalance = 0.0);

    /* Balance operations */
    bool   credit(double amount, const std::string& fromId,
                  const std::string& txnId, const std::string& desc = "");
    bool   debit (double amount, const std::string& toId,
                  const std::string& txnId, const std::string& desc = "");

    /* Getters */
    double              getBalance()         const { return balance; }
    const std::string&  getOwnerId()         const { return ownerId; }
    const std::vector<Transaction>& getTransactions() const { return transactions; }

    void setBalance(double b) { balance = b; }
    void addTransaction(const Transaction& t) { transactions.push_back(t); }

    /* Polymorphic */
    std::string toString() const override;
};

#endif /* WALLET_H */
