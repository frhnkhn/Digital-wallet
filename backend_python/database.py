"""
database.py - SQLite database setup and helper functions
for the Smart Digital Wallet System.

Tables:
  - users        : account credentials and profile
  - wallets      : wallet ID, balance per user
  - transactions : all debit/credit records
"""

import sqlite3
import os

# Path to the database file
_DB_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
DB_PATH  = os.path.join(_DB_DIR, "wallet.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory for dict-like rows."""
    os.makedirs(_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Create all tables if they don't exist. Called once on app startup."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users table ─────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            pin_hash    TEXT,
            pin_salt    TEXT,
            wallet_id   TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'user',
            is_blocked  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ── Wallets table ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id          TEXT PRIMARY KEY,
            owner_id    TEXT NOT NULL,
            balance     REAL NOT NULL DEFAULT 0.0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)

    # ── Transactions table ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              TEXT PRIMARY KEY,
            from_wallet_id  TEXT NOT NULL,
            to_wallet_id    TEXT NOT NULL,
            amount          REAL NOT NULL,
            type            TEXT NOT NULL,   -- 'CREDIT' or 'DEBIT'
            description     TEXT,
            status          TEXT NOT NULL DEFAULT 'SUCCESS',
            created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()
    conn.close()


# ── User helpers ──────────────────────────────────────────────────────────────

def get_user_by_id(user_id: str) -> sqlite3.Row | None:
    conn  = get_connection()
    row   = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_username(username: str) -> sqlite3.Row | None:
    conn = get_connection()
    row  = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email: str) -> sqlite3.Row | None:
    conn = get_connection()
    row  = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def create_user(user_id: str, username: str, email: str,
                password_hash: str, password_salt: str,
                wallet_id: str, role: str = "user") -> bool:
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO users (id, username, email, password_hash, password_salt,
                               wallet_id, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, email, password_hash, password_salt, wallet_id, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_all_users() -> list:
    conn  = get_connection()
    rows  = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_user_blocked(user_id: str, blocked: bool) -> bool:
    conn = get_connection()
    conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?",
                 (1 if blocked else 0, user_id))
    conn.commit()
    conn.close()
    return True


def update_pin(user_id: str, pin_hash: str, pin_salt: str) -> bool:
    conn = get_connection()
    conn.execute("UPDATE users SET pin_hash = ?, pin_salt = ? WHERE id = ?",
                 (pin_hash, pin_salt, user_id))
    conn.commit()
    conn.close()
    return True


# ── Wallet helpers ────────────────────────────────────────────────────────────

def create_wallet_record(wallet_id: str, owner_id: str, balance: float = 0.0) -> bool:
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO wallets (id, owner_id, balance)
            VALUES (?, ?, ?)
        """, (wallet_id, owner_id, balance))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_wallet(wallet_id: str) -> sqlite3.Row | None:
    conn = get_connection()
    row  = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
    conn.close()
    return row


def get_wallet_by_owner(owner_id: str) -> sqlite3.Row | None:
    conn = get_connection()
    row  = conn.execute("SELECT * FROM wallets WHERE owner_id = ?", (owner_id,)).fetchone()
    conn.close()
    return row


def update_wallet_balance(wallet_id: str, new_balance: float) -> bool:
    conn = get_connection()
    conn.execute("UPDATE wallets SET balance = ? WHERE id = ?",
                 (new_balance, wallet_id))
    conn.commit()
    conn.close()
    return True


def get_all_wallets() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM wallets").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Transaction helpers ────────────────────────────────────────────────────────

def record_transaction(txn_id: str, from_wallet: str, to_wallet: str,
                       amount: float, txn_type: str,
                       description: str = "", status: str = "SUCCESS") -> bool:
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO transactions
                (id, from_wallet_id, to_wallet_id, amount, type, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (txn_id, from_wallet, to_wallet, amount, txn_type, description, status))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_transactions_for_wallet(wallet_id: str, limit: int = 50) -> list:
    """Get all transactions where this wallet is sender OR receiver."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM transactions
        WHERE from_wallet_id = ? OR to_wallet_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (wallet_id, wallet_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_transactions(limit: int = 200) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_db_stats() -> dict:
    """Aggregate statistics from the database."""
    conn = get_connection()
    total_users  = conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_txns   = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    blocked      = conn.execute("SELECT COUNT(*) FROM users WHERE is_blocked=1").fetchone()[0]
    total_money  = conn.execute("SELECT COALESCE(SUM(balance),0) FROM wallets").fetchone()[0]
    total_volume = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions").fetchone()[0]
    conn.close()
    return {
        "total_users":       total_users,
        "total_transactions": total_txns,
        "blocked_users":     blocked,
        "total_money":       round(total_money, 2),
        "total_volume":      round(total_volume, 2),
    }
