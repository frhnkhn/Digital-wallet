"""
admin_routes.py - Admin operations Blueprint
Routes: /api/admin/users, /api/admin/transactions,
        /api/admin/block-user, /api/admin/stats, /api/admin/unblock-user
"""

from flask import Blueprint, request, jsonify, session
from database import (get_all_users, get_all_transactions,
                      set_user_blocked, get_db_stats)
from cpp_bridge import engine_get_total_money, engine_get_total_transactions

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    """Returns True if the current session has admin role."""
    return session.get("role") == "admin"


@admin_bp.route("/api/admin/users", methods=["GET"])
def admin_users():
    """List all registered users (admin only)."""
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    users = get_all_users()
    # Remove sensitive fields before returning
    safe_users = []
    for u in users:
        safe_users.append({
            "id":         u["id"],
            "username":   u["username"],
            "email":      u["email"],
            "wallet_id":  u["wallet_id"],
            "role":       u["role"],
            "is_blocked": bool(u["is_blocked"]),
            "created_at": u["created_at"],
        })
    return jsonify({"users": safe_users}), 200


@admin_bp.route("/api/admin/transactions", methods=["GET"])
def admin_transactions():
    """List all transactions (admin only)."""
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    txns = get_all_transactions(limit=200)
    return jsonify({"transactions": txns}), 200


@admin_bp.route("/api/admin/block-user", methods=["POST"])
def block_user():
    """Block a user by user_id (admin only)."""
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data    = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    if user_id == session.get("user_id"):
        return jsonify({"error": "Cannot block yourself"}), 400

    set_user_blocked(user_id, True)
    return jsonify({"message": "User blocked successfully"}), 200


@admin_bp.route("/api/admin/unblock-user", methods=["POST"])
def unblock_user():
    """Unblock a user by user_id (admin only)."""
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data    = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    set_user_blocked(user_id, False)
    return jsonify({"message": "User unblocked successfully"}), 200


@admin_bp.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Get system-wide wallet statistics (admin only)."""
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403

    db_stats = get_db_stats()

    # Enrich with C++ engine live data where available
    engine_money = engine_get_total_money()
    engine_txns  = engine_get_total_transactions()

    return jsonify({
        **db_stats,
        "engine_total_money":        round(engine_money, 2) if engine_money > 0 else db_stats["total_money"],
        "engine_total_transactions": engine_txns if engine_txns > 0 else db_stats["total_transactions"],
    }), 200
