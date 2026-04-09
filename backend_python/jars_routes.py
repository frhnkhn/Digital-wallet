"""
jars_routes.py - Smart Money Jars Blueprint
Routes: /api/jars (GET/POST), /api/jars/<id>/topup, /api/jars/<id>/break, /api/jars/<id>
"""

import uuid
from flask import Blueprint, request, jsonify, session
from database import (
    get_wallet_by_owner, update_wallet_balance,
    record_transaction, get_user_by_id,
    create_jar, get_jars_for_user, get_jar,
    update_jar_balance, delete_jar, get_total_jars_saved
)

jars_bp = Blueprint("jars", __name__)

VALID_THEMES = ["purple", "emerald", "amber", "rose", "sky", "orange", "pink", "teal"]
VALID_FREQUENCIES = ["none", "daily", "weekly", "monthly"]


def _require_login():
    if "user_id" not in session:
        return None, None
    return session["user_id"], session["wallet_id"]


def _jar_id():
    return "JAR" + uuid.uuid4().hex[:10].upper()


def _txn_id():
    return "TXN" + uuid.uuid4().hex[:12].upper()


def _jar_to_dict(jar) -> dict:
    j = dict(jar)
    j["progress_pct"] = round(
        min(100.0, (j["saved_amount"] / j["goal_amount"]) * 100), 1
    ) if j["goal_amount"] > 0 else 0
    j["remaining"] = max(0.0, round(j["goal_amount"] - j["saved_amount"], 2))
    j["is_complete"] = bool(j["is_complete"])
    return j


# ── List all jars ──────────────────────────────────────────────────────────────

@jars_bp.route("/api/jars", methods=["GET"])
def list_jars():
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    jars = get_jars_for_user(uid)
    total_saved = get_total_jars_saved(uid)

    wallet = get_wallet_by_owner(uid)
    spendable = round(wallet["balance"], 2) if wallet else 0.0

    return jsonify({
        "jars":        [_jar_to_dict(j) for j in jars],
        "total_saved": total_saved,
        "spendable":   spendable,
        "jar_count":   len(jars),
    }), 200


# ── Create a new jar ───────────────────────────────────────────────────────────

@jars_bp.route("/api/jars", methods=["POST"])
def create_new_jar():
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name              = data.get("name", "").strip()
    emoji             = data.get("emoji", "🫙").strip()
    goal_amount       = data.get("goal_amount", 0)
    initial_deposit   = data.get("initial_deposit", 0)
    color_theme       = data.get("color_theme", "purple")
    auto_save_amount  = data.get("auto_save_amount", 0)
    auto_save_freq    = data.get("auto_save_frequency", "none")

    # Validations
    if not name:
        return jsonify({"error": "Jar name is required"}), 400
    if len(name) > 40:
        return jsonify({"error": "Jar name too long (max 40 chars)"}), 400

    try:
        goal_amount     = float(goal_amount)
        initial_deposit = float(initial_deposit)
        auto_save_amount = float(auto_save_amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount values"}), 400

    if goal_amount <= 0 or goal_amount > 10_000_000:
        return jsonify({"error": "Goal amount must be between ₹1 and ₹1,00,00,000"}), 400
    if initial_deposit < 0:
        return jsonify({"error": "Initial deposit cannot be negative"}), 400
    if initial_deposit > goal_amount:
        return jsonify({"error": "Initial deposit cannot exceed goal amount"}), 400
    if color_theme not in VALID_THEMES:
        color_theme = "purple"
    if auto_save_freq not in VALID_FREQUENCIES:
        auto_save_freq = "none"

    # Check wallet balance for initial deposit
    wallet = get_wallet_by_owner(uid)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    if initial_deposit > 0 and wallet["balance"] < initial_deposit:
        return jsonify({"error": "Insufficient wallet balance for initial deposit"}), 400

    # Deduct initial deposit from wallet
    if initial_deposit > 0:
        new_balance = wallet["balance"] - initial_deposit
        update_wallet_balance(wid, new_balance)
        txn_id = _txn_id()
        record_transaction(txn_id, wid, "JARS", initial_deposit, "DEBIT",
                           f"Savings: {name} jar created")

    jar_id = _jar_id()
    ok = create_jar(jar_id, uid, wid, name, emoji, goal_amount,
                    initial_deposit, color_theme, auto_save_amount, auto_save_freq)

    if not ok:
        # Rollback wallet if jar creation failed
        if initial_deposit > 0:
            update_wallet_balance(wid, wallet["balance"])
        return jsonify({"error": "Failed to create jar"}), 500

    jar = get_jar(jar_id)
    return jsonify({
        "message":    f"🫙 Jar \"{name}\" created!",
        "jar":        _jar_to_dict(jar),
        "new_wallet_balance": round(wallet["balance"] - initial_deposit, 2) if initial_deposit > 0 else round(wallet["balance"], 2)
    }), 201


# ── Top up a jar ───────────────────────────────────────────────────────────────

@jars_bp.route("/api/jars/<jar_id>/topup", methods=["POST"])
def topup_jar(jar_id: str):
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data   = request.get_json(silent=True) or {}
    amount = data.get("amount", 0)

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    jar = get_jar(jar_id)
    if not jar or jar["owner_id"] != uid:
        return jsonify({"error": "Jar not found"}), 404
    if jar["is_complete"]:
        return jsonify({"error": "Jar is already complete 🎉"}), 400

    remaining = jar["goal_amount"] - jar["saved_amount"]
    if amount > remaining:
        amount = remaining  # Cap at remaining goal

    wallet = get_wallet_by_owner(uid)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    if wallet["balance"] < amount:
        return jsonify({"error": "Insufficient wallet balance"}), 400

    # Deduct from wallet
    new_wallet_balance = wallet["balance"] - amount
    update_wallet_balance(wid, new_wallet_balance)

    # Credit jar
    new_saved = round(jar["saved_amount"] + amount, 2)
    update_jar_balance(jar_id, new_saved)

    txn_id = _txn_id()
    record_transaction(txn_id, wid, "JARS", amount, "DEBIT",
                       f"Savings top-up: {jar['name']}")

    # Re-fetch jar for updated state
    updated_jar = get_jar(jar_id)
    jar_data    = _jar_to_dict(updated_jar)

    msg = f"₹{amount:.0f} added to {jar['name']}!"
    if jar_data["is_complete"]:
        msg = f"🎉 Goal achieved! {jar['name']} is complete!"

    return jsonify({
        "message":            msg,
        "jar":                jar_data,
        "new_wallet_balance": round(new_wallet_balance, 2),
    }), 200


# ── Break a jar (return money) ─────────────────────────────────────────────────

@jars_bp.route("/api/jars/<jar_id>/break", methods=["POST"])
def break_jar(jar_id: str):
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    jar = get_jar(jar_id)
    if not jar or jar["owner_id"] != uid:
        return jsonify({"error": "Jar not found"}), 404

    saved_amount    = jar["saved_amount"]
    goal_amount     = jar["goal_amount"]
    penalty_applied = False
    returned_amount = saved_amount

    # If goal not met: 2% break penalty (as a teaching moment, not a real fee)
    if not jar["is_complete"] and saved_amount > 0:
        penalty      = round(saved_amount * 0.02, 2)
        returned_amount = round(saved_amount - penalty, 2)
        penalty_applied = True

    # Return money to wallet
    if returned_amount > 0:
        wallet = get_wallet_by_owner(uid)
        if wallet:
            new_balance = wallet["balance"] + returned_amount
            update_wallet_balance(wid, new_balance)
            txn_id = _txn_id()
            record_transaction(txn_id, "JARS", wid, returned_amount, "CREDIT",
                               f"Jar broken: {jar['name']}")

    # Delete jar
    delete_jar(jar_id)

    wallet = get_wallet_by_owner(uid)
    msg = (
        f"💔 Jar broken early. ₹{returned_amount:.2f} returned (2% early-break fee applied)."
        if penalty_applied
        else f"🎉 Congratulations! ₹{returned_amount:.2f} returned to your wallet!"
    )

    return jsonify({
        "message":            msg,
        "returned_amount":    returned_amount,
        "penalty_applied":    penalty_applied,
        "goal_was_met":       bool(jar["is_complete"]),
        "new_wallet_balance": round(wallet["balance"], 2) if wallet else 0.0,
    }), 200


# ── Delete an empty jar ────────────────────────────────────────────────────────

@jars_bp.route("/api/jars/<jar_id>", methods=["DELETE"])
def remove_jar(jar_id: str):
    uid, _ = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    jar = get_jar(jar_id)
    if not jar or jar["owner_id"] != uid:
        return jsonify({"error": "Jar not found"}), 404

    delete_jar(jar_id)
    return jsonify({"message": "Jar removed"}), 200
