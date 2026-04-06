/**
 * User.cpp - Implementation of User class
 */

#include "User.h"
#include <sstream>
#include <ctime>

User::User(const std::string& userId, const std::string& username,
           const std::string& email, const std::string& walletId)
    : Entity(userId), username(username), email(email),
      walletId(walletId), isBlocked(false)
{
    /* Store creation timestamp */
    char buf[32];
    time_t now = time(nullptr);
    struct tm* tm_info = localtime(&now);
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", tm_info);
    createdAt = std::string(buf);
}

std::string User::toString() const {
    std::ostringstream oss;
    oss << "[User:" << id << "] "
        << username
        << " <" << email << ">"
        << " Wallet:" << walletId
        << " Role:" << getRole()
        << " Blocked:" << (isBlocked ? "yes" : "no");
    return oss.str();
}
