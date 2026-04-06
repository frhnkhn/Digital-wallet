/**
 * AdminUser.h - Admin user class (inherits User)
 * Language: C++
 * OOP Concepts: Inheritance, polymorphism, method overriding
 */

#ifndef ADMINUSER_H
#define ADMINUSER_H

#include "User.h"
#include <string>

/**
 * AdminUser - Extends User with administrator privileges.
 * Demonstrates inheritance and polymorphism:
 *   AdminUser IS-A User (substitution principle)
 */
class AdminUser : public User {
private:
    std::string adminLevel; /* e.g. "SUPER", "STANDARD" */

public:
    AdminUser(const std::string& userId,
              const std::string& username,
              const std::string& email,
              const std::string& walletId,
              const std::string& adminLevel = "STANDARD");

    /* Override virtual methods to demonstrate polymorphism */
    bool isAdmin() const override { return true; }
    std::string getRole() const override { return "admin"; }
    const std::string& getAdminLevel() const { return adminLevel; }

    /* Override toString */
    std::string toString() const override;
};

#endif /* ADMINUSER_H */
