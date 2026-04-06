"""
wallet_routes.py - Wallet operations Blueprint
Routes: /api/balance, /api/add-money, /api/send-money, /api/transactions, /api/profile
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database import (get_wallet_by_owner, get_wallet,
                      update_wallet_balance, record_transaction,
                      get_transactions_for_wallet, get_user_by_id,
                      update_pin)
from cpp_bridge import (engine_get_balance, engine_add_money,
                        engine_transfer, engine_load_wallet,
                        generate_salt, hash_pin, verify_pin)

wallet_bp = Blueprint("wallet", __name__)


def _require_login():
    """Returns (user_id, wallet_id) if logged in, else raises error dict."""
    if "user_id" not in session:
        return None, None
    return session["user_id"], session["wallet_id"]


def _gen_txn_id() -> str:
    return "TXN" + uuid.uuid4().hex[:12].upper()


@wallet_bp.route("/api/balance", methods=["GET"])
def get_balance():
    """Return current wallet balance."""
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    # Get from DB (source of truth persisted)
    wallet = get_wallet_by_owner(uid)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    # Also sync with C++ engine balance
    engine_balance = engine_get_balance(wid)
    balance = wallet["balance"] if engine_balance < 0 else engine_balance

    return jsonify({
        "wallet_id": wid,
        "balance":   round(balance, 2)
    }), 200


@wallet_bp.route("/api/add-money", methods=["POST"])
def add_money():
    """Add money to the user's own wallet."""
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data   = request.get_json(silent=True) or {}
    amount = data.get("amount", 0)
    desc   = data.get("description", "Wallet top-up")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0 or amount > 100000:
        return jsonify({"error": "Amount must be between 0 and 100,000"}), 400

    wallet = get_wallet_by_owner(uid)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    # ── C++ engine: credit the wallet ────────────────────────────────────────
    engine_load_wallet(wid, wallet["balance"], uid)
    ok = engine_add_money(wid, amount, desc)
    if not ok:
        return jsonify({"error": "Failed to add money"}), 500

    # ── Update SQLite balance ─────────────────────────────────────────────────
    new_balance = wallet["balance"] + amount
    update_wallet_balance(wid, new_balance)

    # ── Record transaction ────────────────────────────────────────────────────
    txn_id = _gen_txn_id()
    record_transaction(txn_id, "SYSTEM", wid, amount, "CREDIT", desc)

    return jsonify({
        "message":     f"₹{amount:.2f} added successfully!",
        "new_balance": round(new_balance, 2),
        "txn_id":      txn_id
    }), 200


@wallet_bp.route("/api/send-money", methods=["POST"])
def send_money():
    """Transfer money to another user by username or wallet ID."""
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data        = request.get_json(silent=True) or {}
    amount      = data.get("amount", 0)
    recipient   = data.get("recipient", "").strip()   # username or wallet_id
    desc        = data.get("description", "Money transfer")
    pin_input   = data.get("pin", "")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400
    if not recipient:
        return jsonify({"error": "Recipient is required"}), 400

    # ── Find sender wallet ────────────────────────────────────────────────────
    sender_wallet = get_wallet_by_owner(uid)
    if not sender_wallet:
        return jsonify({"error": "Sender wallet not found"}), 404
    if sender_wallet["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    # ── PIN verification (if PIN is set) ──────────────────────────────────────
    sender_user = get_user_by_id(uid)
    if sender_user and sender_user["pin_hash"]:
        if not pin_input:
            return jsonify({"error": "PIN required for transfers"}), 400
        if not verify_pin(str(pin_input), sender_user["pin_salt"],
                          sender_user["pin_hash"]):
            return jsonify({"error": "Incorrect PIN"}), 403

    # ── Find recipient ────────────────────────────────────────────────────────
    from database import get_user_by_username, get_wallet
    recv_user   = get_user_by_username(recipient)
    recv_wallet = None

    if recv_user:
        recv_wallet = get_wallet_by_owner(recv_user["id"])
    else:
        # Try as wallet ID
        recv_wallet = get_wallet(recipient)
        if recv_wallet:
            recv_user = get_user_by_id(recv_wallet["owner_id"])

    if not recv_wallet:
        return jsonify({"error": "Recipient not found"}), 404
    if recv_wallet["id"] == wid:
        return jsonify({"error": "Cannot send money to yourself"}), 400
    if recv_user and recv_user["is_blocked"]:
        return jsonify({"error": "Recipient account is blocked"}), 403

    # ── Load both wallets into C++ engine ─────────────────────────────────────
    engine_load_wallet(wid,              sender_wallet["balance"], uid)
    engine_load_wallet(recv_wallet["id"], recv_wallet["balance"], recv_wallet["owner_id"])

    # ── Execute C++ transfer ──────────────────────────────────────────────────
    result = engine_transfer(wid, recv_wallet["id"], amount, desc)
    if result["code"] != 0:
        messages = {
            1: "Insufficient funds",
            2: "Sender wallet error",
            3: "Receiver wallet not found",
            4: "Your account is blocked",
            5: "Recipient account is blocked",
            6: "Invalid amount",
        }
        return jsonify({"error": messages.get(result["code"], "Transfer failed")}), 400

    # ── Persist updated balances ──────────────────────────────────────────────
    new_sender_balance   = sender_wallet["balance"]   - amount
    new_receiver_balance = recv_wallet["balance"] + amount
    update_wallet_balance(wid,              new_sender_balance)
    update_wallet_balance(recv_wallet["id"], new_receiver_balance)

    # ── Record transactions ───────────────────────────────────────────────────
    txn_id = _gen_txn_id()
    record_transaction(txn_id, wid, recv_wallet["id"], amount, "DEBIT",  desc)
    record_transaction(txn_id, wid, recv_wallet["id"], amount, "CREDIT", desc)

    return jsonify({
        "message":     f"₹{amount:.2f} sent to {recv_user['username'] if recv_user else recipient}!",
        "new_balance": round(new_sender_balance, 2),
        "txn_id":      txn_id,
        "recipient":   recv_user["username"] if recv_user else recipient
    }), 200


@wallet_bp.route("/api/transactions", methods=["GET"])
def transactions():
    """Get transaction history for the current user's wallet."""
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    txns = get_transactions_for_wallet(wid, limit=50)

    # Annotate each transaction with direction relative to this wallet
    result = []
    for t in txns:
        t_copy = dict(t)
        if t["to_wallet_id"] == wid and t["type"] == "CREDIT":
            t_copy["direction"] = "IN"
        else:
            t_copy["direction"] = "OUT"
        result.append(t_copy)

    return jsonify({"transactions": result, "wallet_id": wid}), 200


@wallet_bp.route("/api/profile", methods=["GET"])
def profile():
    """Return the logged-in user's profile."""
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    user   = get_user_by_id(uid)
    wallet = get_wallet_by_owner(uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id":   user["id"],
        "username":  user["username"],
        "email":     user["email"],
        "wallet_id": user["wallet_id"],
        "balance":   round(wallet["balance"] if wallet else 0.0, 2),
        "role":      user["role"],
        "is_blocked": bool(user["is_blocked"]),
        "created_at": user["created_at"],
        "has_pin":   bool(user["pin_hash"]),
    }), 200


@wallet_bp.route("/api/set-pin", methods=["POST"])
def set_pin():
    """Set or update the wallet PIN."""
    uid, _ = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    pin  = str(data.get("pin", "")).strip()

    if not pin.isdigit() or len(pin) != 4:
        return jsonify({"error": "PIN must be exactly 4 digits"}), 400

    salt     = generate_salt()
    pin_hash = hash_pin(pin, salt)
    update_pin(uid, pin_hash, salt)

    return jsonify({"message": "PIN set successfully"}), 200
