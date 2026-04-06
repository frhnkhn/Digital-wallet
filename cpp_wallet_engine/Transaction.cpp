/**
 * Transaction.cpp - Implementation of Transaction class
 */

#include "Transaction.h"
#include <sstream>
#include <iomanip>
#include <ctime>

Transaction::Transaction(const std::string& txnId,
                         const std::string& fromId,
                         const std::string& toId,
                         double amount,
                         TransactionType type,
                         const std::string& description)
    : Entity(txnId),
      fromWalletId(fromId),
      toWalletId(toId),
      amount(amount),
      type(type),
      description(description),
      status("SUCCESS")
{
    timestamp = time(nullptr);
}

std::string Transaction::getTypeString() const {
    return (type == TransactionType::CREDIT) ? "CREDIT" : "DEBIT";
}

std::string Transaction::getTimestampString() const {
    char buf[32];
    struct tm* tm_info = localtime(&timestamp);
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", tm_info);
    return std::string(buf);
}

std::string Transaction::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    oss << "[TXN:" << id << "] "
        << getTypeString() << " "
        << amount
        << " | From:" << fromWalletId
        << " To:" << toWalletId
        << " | " << getTimestampString()
        << " | Status:" << status;
    return oss.str();
}
