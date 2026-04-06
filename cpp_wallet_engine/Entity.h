/**
 * Entity.h - Abstract base class for all entities in the wallet system
 * Language: C++
 * OOP Concepts: Abstract class, pure virtual functions
 */

#ifndef ENTITY_H
#define ENTITY_H

#include <string>

/**
 * Entity - Abstract base class providing a common ID interface.
 * Demonstrates: abstraction, encapsulation.
 */
class Entity {
protected:
    std::string id;

public:
    explicit Entity(const std::string& id) : id(id) {}
    virtual ~Entity() = default;

    /* Pure virtual: every entity must be serializable to a string */
    virtual std::string toString() const = 0;

    const std::string& getId() const { return id; }
};

#endif /* ENTITY_H */
