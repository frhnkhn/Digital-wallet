# Smart Digital Wallet System 💳
> Powered by **C++** (OOP Wallet Engine) · **Python Flask** (REST API) · **C** (Security) · SQLite

## Table of Contents

1. [Project Structure](#project-structure)  
2. [Architecture](#architecture)  
3. [Setup Guide](#setup-guide)  
4. [How C++ Connects to Python](#how-c-connects-to-python)  
5. [Sample Users](#sample-users)  
6. [Pages & Features](#pages--features)

---

## Project Structure

```
Wallet/
├── frontend/               # HTML, CSS, JavaScript (8 pages)
│   ├── css/style.css
│   ├── js/app.js
│   ├── index.html          # Home / Landing page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html      # Balance card, quick actions
│   ├── add_money.html
│   ├── send_money.html
│   ├── transactions.html
│   ├── profile.html        # PIN management
│   └── admin.html          # Admin panel
│
├── backend_python/         # Flask REST API
│   ├── app.py              # Entry point
│   ├── auth.py             # Register / Login / Logout
│   ├── wallet_routes.py    # Balance / Add / Send / History
│   ├── admin_routes.py     # Admin: users, block, stats
│   ├── database.py         # SQLite helpers
│   ├── cpp_bridge.py       # ctypes bridge → libwallet.so + libsecurity.so
│   ├── seed_data.py        # Sample users seeder
│   └── requirements.txt
│
├── cpp_wallet_engine/      # C++ OOP Wallet Engine → libwallet.so
│   ├── Entity.h            # Abstract base class
│   ├── User.h / .cpp       # User class (inherits Entity)
│   ├── AdminUser.h / .cpp  # AdminUser (inherits User, polymorphism)
│   ├── Wallet.h / .cpp     # Wallet class
│   ├── Transaction.h / .cpp# Transaction class with timestamps
│   ├── WalletEngine.h / .cpp # Singleton orchestrator
│   ├── wallet_c_api.h / .cpp # extern "C" Python ctypes API
│   └── Makefile
│
├── c_security/             # C Security Module → libsecurity.so
│   ├── security.h
│   ├── security.c          # Pure-C SHA-256, salt, hashing
│   └── Makefile
│
└── database/
    └── wallet.db           # SQLite database (auto-created)
```

---

## Architecture

```
Browser (HTML/CSS/JS)
       │  HTTP (fetch API)
       ▼
 Python Flask (app.py)
       │  Blueprints: auth, wallet, admin
       ├──► database.py   (SQLite: users, wallets, transactions)
       │
       ├──► cpp_bridge.py ──ctypes──► libwallet.so   (C++ Engine)
       │                              ├── WalletEngine (Singleton)
       │                              ├── Wallet (balance, debit, credit)
       │                              ├── User / AdminUser (polymorphism)
       │                              └── Transaction (timestamped records)
       │
       └──► cpp_bridge.py ──ctypes──► libsecurity.so (C Module)
                                      ├── generate_salt()
                                      ├── hash_password()
                                      ├── hash_pin()
                                      └── verify_password() / verify_pin()
```

---

## Setup Guide

### Step 1 — Install prerequisites (Mac)

```bash
# Install Xcode Command Line Tools (provides gcc/g++)
xcode-select --install

# Install Python 3 (if not installed)
brew install python
```

### Step 2 — Compile C Security Module

```bash
cd /Users/frhnkhn/Codes/Projects/Wallet/c_security
make
# Expected output: ✅ Built libsecurity.so successfully
```

### Step 3 — Compile C++ Wallet Engine

```bash
cd /Users/frhnkhn/Codes/Projects/Wallet/cpp_wallet_engine
make
# Expected output: ✅ Built libwallet.so successfully
```

### Step 4 — Install Python dependencies

```bash
cd /Users/frhnkhn/Codes/Projects/Wallet/backend_python
pip3 install -r requirements.txt
```

### Step 5 — Seed sample users (first time only)

```bash
cd /Users/frhnkhn/Codes/Projects/Wallet/backend_python
python3 seed_data.py
```

### Step 6 — Start the Flask server

```bash
cd /Users/frhnkhn/Codes/Projects/Wallet/backend_python
python3 app.py
```

Open: **http://127.0.0.1:5000**

> **Note:** If `libwallet.so` / `libsecurity.so` are not compiled, the system automatically falls back to Python-only mode (SHA-256 via `hashlib`, balance managed in DB only). All features still work.

---

## How C++ Connects to Python

### 1. C++ Exports a C API (`wallet_c_api.cpp`)

```cpp
extern "C" {
    double wallet_get_balance(const char* wallet_id);
    int    wallet_transfer(const char*, const char*, double, const char*);
    // ...
}
```

The `extern "C"` prevents C++ name mangling so Python can find the symbols.

### 2. Makefile compiles to shared library

```bash
g++ -fPIC -shared -o libwallet.so *.cpp
```

### 3. Python loads it via ctypes (`cpp_bridge.py`)

```python
import ctypes
lib = ctypes.CDLL("../cpp_wallet_engine/libwallet.so")
lib.wallet_get_balance.argtypes = [ctypes.c_char_p]
lib.wallet_get_balance.restype  = ctypes.c_double

balance = lib.wallet_get_balance(b"abc123wallet")
```

### 4. Python bridges to Flask routes

```python
# wallet_routes.py
from cpp_bridge import engine_transfer
result = engine_transfer(from_wid, to_wid, amount, description)
```

The same pattern is used for `libsecurity.so` (C module).

---

## Sample Users

| Username | Password   | Role  | PIN  | Balance  |
|----------|------------|-------|------|----------|
| `alice`  | `alice123` | User  | 1234 | ₹1,500   |
| `bob`    | `bob123`   | User  | —    | ₹800     |
| `charlie`| `charlie123`| User | —    | ₹250     |
| `admin`  | `admin123` | Admin | —    | ₹0       |

---

## Pages & Features

| Page               | URL                    | Features |
|--------------------|------------------------|----------|
| Home               | `/`                    | Landing, feature overview |
| Login              | `/login.html`          | Auth via C security hashing |
| Register           | `/register.html`       | Account + wallet ID creation |
| Dashboard          | `/dashboard.html`      | Balance card, quick actions, recent transactions |
| Add Money          | `/add_money.html`      | Credit wallet via C++ engine |
| Send Money         | `/send_money.html`     | Transfer via C++ WalletEngine, PIN verify via C |
| Transaction History| `/transactions.html`   | Filter: All / In / Out, summary stats |
| Profile            | `/profile.html`        | User info, set/update PIN |
| Admin Panel        | `/admin.html`          | All users, block/unblock, system stats |

---

## OOP Class Hierarchy (C++)

```
Entity (abstract)
├── User (username, email, walletId, isBlocked)
│   └── AdminUser (adminLevel) ← overrides isAdmin(), getRole()
└── Wallet (balance, transactions[])
Transaction (type: CREDIT/DEBIT, amount, timestamp, parties)
WalletEngine (Singleton, orchestrates all operations)
```

Demonstrates: **abstraction, encapsulation, inheritance, polymorphism**.
