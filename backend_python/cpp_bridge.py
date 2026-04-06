"""
cpp_bridge.py - ctypes bridge connecting Python to C and C++ shared libraries.

This module loads:
  - libsecurity.so  (C security module: hashing, salt, wallet ID)
  - libwallet.so    (C++ wallet engine: balance, add money, transfer)

Python calls the extern "C" API functions via ctypes.
"""

import ctypes
import os
import sys

# ── Library paths ──────────────────────────────────────────────────────────────
_BASE = os.path.abspath(os.path.dirname(__file__))
_ROOT = os.path.abspath(os.path.join(_BASE, ".."))

LIB_SECURITY = os.path.join(_ROOT, "c_security",        "libsecurity.so")
LIB_WALLET   = os.path.join(_ROOT, "cpp_wallet_engine", "libwallet.so")


def _load_lib(path: str, name: str) -> ctypes.CDLL:
    """Load a shared library, raising a descriptive error if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"❌ {name} not found at {path}\n"
            f"   Run 'make' inside the corresponding directory first."
        )
    return ctypes.CDLL(path)


# ── Load both libraries ────────────────────────────────────────────────────────
try:
    _sec = _load_lib(LIB_SECURITY, "libsecurity.so")
    _wal = _load_lib(LIB_WALLET,   "libwallet.so")
    _LIBS_LOADED = True
except FileNotFoundError as e:
    print(f"[cpp_bridge] WARNING: {e}", file=sys.stderr)
    _LIBS_LOADED = False
    _sec = None
    _wal = None


# ── Security library function signatures ──────────────────────────────────────
if _sec:
    # void generate_salt(char out_salt[33])
    _sec.generate_salt.argtypes  = [ctypes.c_char_p]
    _sec.generate_salt.restype   = None

    # void hash_password(const char *pw, const char *salt, char out[65])
    _sec.hash_password.argtypes  = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    _sec.hash_password.restype   = None

    # void hash_pin(const char *pin, const char *salt, char out[65])
    _sec.hash_pin.argtypes       = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    _sec.hash_pin.restype        = None

    # int verify_password(const char *input, const char *salt, const char *stored)
    _sec.verify_password.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    _sec.verify_password.restype  = ctypes.c_int

    # int verify_pin(const char *pin, const char *salt, const char *stored)
    _sec.verify_pin.argtypes     = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    _sec.verify_pin.restype      = ctypes.c_int

    # void generate_wallet_id(char out[17])
    _sec.generate_wallet_id.argtypes = [ctypes.c_char_p]
    _sec.generate_wallet_id.restype  = None


# ── Wallet library function signatures ────────────────────────────────────────
if _wal:
    # int wallet_load(const char *wallet_id, double balance, const char *owner_id)
    _wal.wallet_load.argtypes  = [ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p]
    _wal.wallet_load.restype   = ctypes.c_int

    # double wallet_get_balance(const char *wallet_id)
    _wal.wallet_get_balance.argtypes = [ctypes.c_char_p]
    _wal.wallet_get_balance.restype  = ctypes.c_double

    # int wallet_add_money(const char *wallet_id, double amount, const char *desc)
    _wal.wallet_add_money.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p]
    _wal.wallet_add_money.restype  = ctypes.c_int

    # int wallet_transfer(const char *from, const char *to, double amount, const char *desc)
    _wal.wallet_transfer.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                                      ctypes.c_double, ctypes.c_char_p]
    _wal.wallet_transfer.restype  = ctypes.c_int

    # double wallet_get_stats_total_money(void)
    _wal.wallet_get_stats_total_money.argtypes = []
    _wal.wallet_get_stats_total_money.restype  = ctypes.c_double

    # int wallet_get_stats_total_transactions(void)
    _wal.wallet_get_stats_total_transactions.argtypes = []
    _wal.wallet_get_stats_total_transactions.restype  = ctypes.c_int


# ── Python-friendly wrappers ───────────────────────────────────────────────────

def _buf(size: int) -> ctypes.Array:
    """Create a mutable char buffer of given size."""
    return ctypes.create_string_buffer(size)


def generate_salt() -> str:
    """Returns a 32-character hex random salt."""
    if not _sec:
        import secrets
        return secrets.token_hex(16)
    buf = _buf(34)
    _sec.generate_salt(buf)
    return buf.value.decode()


def hash_password(password: str, salt: str) -> str:
    """Returns SHA-256(password + salt) as a 64-char hex string."""
    if not _sec:
        import hashlib
        return hashlib.sha256((password + salt).encode()).hexdigest()
    buf = _buf(65)
    _sec.hash_password(password.encode(), salt.encode(), buf)
    return buf.value.decode()


def hash_pin(pin: str, salt: str) -> str:
    """Returns SHA-256(pin + salt) as a 64-char hex string."""
    if not _sec:
        import hashlib
        return hashlib.sha256((pin + salt).encode()).hexdigest()
    buf = _buf(65)
    _sec.hash_pin(pin.encode(), salt.encode(), buf)
    return buf.value.decode()


def verify_password(input_pw: str, salt: str, stored_hash: str) -> bool:
    """Returns True if hash_password(input, salt) matches stored_hash."""
    if not _sec:
        return hash_password(input_pw, salt) == stored_hash
    result = _sec.verify_password(input_pw.encode(), salt.encode(), stored_hash.encode())
    return result == 1


def verify_pin(input_pin: str, salt: str, stored_hash: str) -> bool:
    """Returns True if hash_pin(input, salt) matches stored_hash."""
    if not _sec:
        return hash_pin(input_pin, salt) == stored_hash
    result = _sec.verify_pin(input_pin.encode(), salt.encode(), stored_hash.encode())
    return result == 1


def generate_wallet_id() -> str:
    """Returns a unique 16-char hex wallet ID."""
    if not _sec:
        import secrets
        return secrets.token_hex(8)
    buf = _buf(18)
    _sec.generate_wallet_id(buf)
    return buf.value.decode()


# ── Wallet engine wrappers ─────────────────────────────────────────────────────

TRANSFER_CODES = {
    0: "SUCCESS",
    1: "INSUFFICIENT_FUNDS",
    2: "SENDER_NOT_FOUND",
    3: "RECEIVER_NOT_FOUND",
    4: "SENDER_BLOCKED",
    5: "RECEIVER_BLOCKED",
    6: "INVALID_AMOUNT",
}


def engine_load_wallet(wallet_id: str, balance: float, owner_id: str) -> bool:
    """Load a wallet into the C++ engine (call at startup per user)."""
    if not _wal:
        return True  # fallback: Python-only mode
    return _wal.wallet_load(wallet_id.encode(), balance, owner_id.encode()) == 1


def engine_get_balance(wallet_id: str) -> float:
    """Get live balance from C++ engine. Returns -1 if not found."""
    if not _wal:
        return -1.0
    return float(_wal.wallet_get_balance(wallet_id.encode()))


def engine_add_money(wallet_id: str, amount: float, description: str = "") -> bool:
    """Credit amount to wallet in C++ engine."""
    if not _wal:
        return True
    return _wal.wallet_add_money(
        wallet_id.encode(), amount, description.encode()
    ) == 1


def engine_transfer(from_wallet: str, to_wallet: str,
                    amount: float, description: str = "") -> dict:
    """Transfer money between wallets via C++ engine."""
    if not _wal:
        return {"code": 0, "status": "SUCCESS"}
    code = _wal.wallet_transfer(
        from_wallet.encode(), to_wallet.encode(),
        amount, description.encode()
    )
    return {"code": code, "status": TRANSFER_CODES.get(code, "UNKNOWN")}


def engine_get_total_money() -> float:
    """Total money across all loaded wallets (C++ engine stats)."""
    if not _wal:
        return 0.0
    return float(_wal.wallet_get_stats_total_money())


def engine_get_total_transactions() -> int:
    """Total transactions processed by C++ engine."""
    if not _wal:
        return 0
    return int(_wal.wallet_get_stats_total_transactions())


def libs_loaded() -> bool:
    """Returns True if both shared libraries are loaded."""
    return _LIBS_LOADED
