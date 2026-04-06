/**
 * Transaction.h - Transaction class for wallet operations
 * Language: C++
 * OOP Concepts: Encapsulation, enum class
 */

#ifndef TRANSACTION_H
#define TRANSACTION_H

#include "Entity.h"
#include <string>
#include <ctime>

/* Transaction type */
enum class TransactionType {
    CREDIT,   /* Money received */
    DEBIT     /* Money sent */
};

/**
 * Transaction - Represents a single wallet transaction.
 * Stores amount, parties, type, and timestamp.
 */
class Transaction : public Entity {
private:
    std::string   fromWalletId;
    std::string   toWalletId;
    double        amount;
    TransactionType type;
    std::string   description;
    time_t        timestamp;
    std::string   status; /* "SUCCESS", "FAILED" */

public:
    Transaction(const std::string& txnId,
                const std::string& fromId,
                const std::string& toId,
                double amount,
                TransactionType type,
                const std::string& description = "");

    /* Getters */
    const std::string&  getFromWalletId()  const { return fromWalletId; }
    const std::string&  getToWalletId()    const { return toWalletId; }
    double              getAmount()         const { return amount; }
    TransactionType     getType()           const { return type; }
    const std::string&  getDescription()   const { return description; }
    time_t              getTimestamp()      const { return timestamp; }
    const std::string&  getStatus()        const { return status; }
    std::string         getTypeString()    const;
    std::string         getTimestampString() const;

    void setStatus(const std::string& s) { status = s; }

    /* Polymorphic: serialize to string */
    std::string toString() const override;
};

#endif /* TRANSACTION_H */
