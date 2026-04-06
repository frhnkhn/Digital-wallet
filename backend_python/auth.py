"""
auth.py - Authentication Blueprint
Routes: /register, /login, /logout, /api/me
"""

import uuid
from flask import Blueprint, request, jsonify, session
from database import (get_user_by_username, get_user_by_email,
                      create_user, create_wallet_record,
                      get_wallet_by_owner)
from cpp_bridge import (generate_salt, hash_password, verify_password,
                        generate_wallet_id, engine_load_wallet)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "").strip()

    # ── Validation ────────────────────────────────────────────────────────────
    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Invalid email address"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if get_user_by_username(username):
        return jsonify({"error": "Username already taken"}), 409
    if get_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    # ── Hash password via C security module ──────────────────────────────────
    salt          = generate_salt()
    password_hash = hash_password(password, salt)
    user_id       = str(uuid.uuid4())
    wallet_id     = generate_wallet_id()

    # ── Persist to SQLite ────────────────────────────────────────────────────
    if not create_user(user_id, username, email, password_hash, salt, wallet_id):
        return jsonify({"error": "Registration failed. Try again."}), 500
    create_wallet_record(wallet_id, user_id, 0.0)

    # ── Load wallet into C++ engine ──────────────────────────────────────────
    engine_load_wallet(wallet_id, 0.0, user_id)

    return jsonify({
        "message":   "Account created successfully!",
        "wallet_id": wallet_id
    }), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    """Authenticate user and start a session."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401
    if user["is_blocked"]:
        return jsonify({"error": "Your account has been blocked. Contact admin."}), 403
    if not verify_password(password, user["password_salt"], user["password_hash"]):
        return jsonify({"error": "Invalid username or password"}), 401

    # ── Load wallet into C++ engine (in case server restarted) ───────────────
    wallet = get_wallet_by_owner(user["id"])
    if wallet:
        engine_load_wallet(wallet["id"], wallet["balance"], user["id"])

    # ── Set session ──────────────────────────────────────────────────────────
    session["user_id"]   = user["id"]
    session["username"]  = user["username"]
    session["role"]      = user["role"]
    session["wallet_id"] = user["wallet_id"]
    session.permanent    = True

    return jsonify({
        "message":  "Login successful",
        "username": user["username"],
        "role":     user["role"],
        "wallet_id": user["wallet_id"]
    }), 200


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    """Clear user session."""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/me", methods=["GET"])
def me():
    """Return currently logged-in user info."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({
        "user_id":  session["user_id"],
        "username": session["username"],
        "role":     session["role"],
        "wallet_id": session["wallet_id"]
    }), 200
