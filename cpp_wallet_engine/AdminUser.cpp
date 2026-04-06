/**
 * AdminUser.cpp - Implementation of AdminUser class
 * Demonstrates polymorphism: overrides User's virtual methods
 */

#include "AdminUser.h"
#include <sstream>

AdminUser::AdminUser(const std::string& userId, const std::string& username,
                     const std::string& email, const std::string& walletId,
                     const std::string& adminLevel)
    : User(userId, username, email, walletId), adminLevel(adminLevel)
{}

std::string AdminUser::toString() const {
    std::ostringstream oss;
    oss << "[AdminUser:" << getId() << "] "
        << getUsername()
        << " <" << getEmail() << ">"
        << " Wallet:" << getWalletId()
        << " Level:" << adminLevel
        << " Blocked:" << (getIsBlocked() ? "yes" : "no");
    return oss.str();
}
