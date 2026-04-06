"""
seed_data.py - Create sample users for testing the Digital Wallet System.

Sample accounts created:
  - alice   / alice123   (regular user, ₹1500 balance, PIN: 1234)
  - bob     / bob123     (regular user, ₹800 balance)
  - charlie / charlie123 (regular user, ₹250 balance)
  - admin   / admin123   (admin account, ₹0 balance)

Run this once before starting the app:
  cd backend_python
  python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import uuid
from database import (init_db, get_user_by_username, create_user,
                      create_wallet_record, update_wallet_balance,
                      record_transaction, update_pin, get_connection)
from cpp_bridge import (generate_salt, hash_password, hash_pin,
                        generate_wallet_id)


SAMPLE_USERS = [
    {
        "username": "alice",
        "email":    "alice@wallet.com",
        "password": "alice123",
        "balance":  1500.00,
        "pin":      "1234",
        "role":     "user",
    },
    {
        "username": "bob",
        "email":    "bob@wallet.com",
        "password": "bob123",
        "balance":  800.00,
        "pin":      None,
        "role":     "user",
    },
    {
        "username": "charlie",
        "email":    "charlie@wallet.com",
        "password": "charlie123",
        "balance":  250.00,
        "pin":      None,
        "role":     "user",
    },
    {
        "username": "admin",
        "email":    "admin@wallet.com",
        "password": "admin123",
        "balance":  0.00,
        "pin":      None,
        "role":     "admin",
    },
]

SAMPLE_TRANSACTIONS = []  # will be built after wallets are created


def seed():
    init_db()

    created_wallets = {}

    for u in SAMPLE_USERS:
        if get_user_by_username(u["username"]):
            print(f"  ⚠️  User '{u['username']}' already exists, skipping.")
            continue

        user_id   = str(uuid.uuid4())
        wallet_id = generate_wallet_id()
        salt      = generate_salt()
        pw_hash   = hash_password(u["password"], salt)

        create_user(user_id, u["username"], u["email"],
                    pw_hash, salt, wallet_id, u["role"])
        create_wallet_record(wallet_id, user_id, u["balance"])

        if u["pin"]:
            p_salt   = generate_salt()
            p_hash   = hash_pin(u["pin"], p_salt)
            update_pin(user_id, p_hash, p_salt)

        created_wallets[u["username"]] = wallet_id
        print(f"  ✅ Created user '{u['username']}'  wallet_id={wallet_id}  balance=₹{u['balance']}")

    # ── Sample transactions between alice and bob ─────────────────────────────
    if "alice" in created_wallets and "bob" in created_wallets:
        alice_wid = created_wallets["alice"]
        bob_wid   = created_wallets["bob"]

        sample_txns = [
            ("TXN000001", "SYSTEM",    alice_wid, 1500.00, "CREDIT", "Initial deposit"),
            ("TXN000002", "SYSTEM",    bob_wid,    800.00, "CREDIT", "Initial deposit"),
            ("TXN000003", "SYSTEM",    created_wallets.get("charlie", ""), 250.00, "CREDIT", "Initial deposit"),
            ("TXN000004", alice_wid,   bob_wid,    200.00, "DEBIT",  "Transfer to Bob"),
            ("TXN000005", alice_wid,   bob_wid,     50.00, "DEBIT",  "Coffee money"),
        ]
        for txn in sample_txns:
            txn_id, frm, to, amt, typ, desc = txn
            if frm and to:
                record_transaction(txn_id, frm, to, amt, typ, desc)

    print("\n✅ Seed complete! You can now run: python app.py")
    print("\nSample login credentials:")
    print("  alice   / alice123   (user, PIN: 1234)")
    print("  bob     / bob123     (user)")
    print("  charlie / charlie123 (user)")
    print("  admin   / admin123   (admin)")


if __name__ == "__main__":
    print("🌱 Seeding sample data...\n")
    seed()
