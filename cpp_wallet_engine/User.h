/**
 * User.h - User class (base user)
 * Language: C++
 * OOP Concepts: Encapsulation, inheritance from Entity
 */

#ifndef USER_H
#define USER_H

#include "Entity.h"
#include "Wallet.h"
#include <string>

/**
 * User - Represents a registered wallet user.
 * Inherits from Entity (has an ID).
 * Composed with a Wallet.
 */
class User : public Entity {
protected:
    std::string username;
    std::string email;
    std::string walletId;
    bool        isBlocked;
    std::string createdAt;

public:
    User(const std::string& userId,
         const std::string& username,
         const std::string& email,
         const std::string& walletId);

    /* Getters */
    const std::string& getUsername()  const { return username; }
    const std::string& getEmail()     const { return email; }
    const std::string& getWalletId()  const { return walletId; }
    bool               getIsBlocked() const { return isBlocked; }
    const std::string& getCreatedAt() const { return createdAt; }

    /* Setters */
    void setBlocked(bool blocked) { isBlocked = blocked; }
    void setEmail(const std::string& e) { email = e; }

    /* Virtual so AdminUser can override */
    virtual bool isAdmin() const { return false; }
    virtual std::string getRole() const { return "user"; }

    /* Polymorphic */
    std::string toString() const override;
};

#endif /* USER_H */
