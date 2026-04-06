"""
app.py - Flask Application Entry Point
Smart Digital Wallet System

Architecture:
  - Flask serves the frontend HTML pages (as static files)
  - Flask REST API connects frontend JS to Python business logic
  - Python calls C++ wallet engine via ctypes (cpp_bridge.py)
  - Python calls C security module via ctypes (cpp_bridge.py)
  - SQLite persists all data (database.py)

How to run:
  cd backend_python
  pip install -r requirements.txt
  python seed_data.py     # create sample users (first time)
  python app.py           # starts server on http://127.0.0.1:5000
"""

import os
import sys
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ── Bootstrap ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
app.secret_key = "smart-wallet-secret-key-2024-change-in-production"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000",
                                               "http://localhost:5000"])

# ── Database init ─────────────────────────────────────────────────────────────
from database import init_db, get_all_wallets
from cpp_bridge import engine_load_wallet, libs_loaded
init_db()

# Load all existing wallets into C++ engine at startup
_wallets = get_all_wallets()
for _w in _wallets:
    engine_load_wallet(_w["id"], _w["balance"], _w["owner_id"])

print(f"[app] Loaded {len(_wallets)} wallets into C++ engine")
if libs_loaded():
    print("[app] ✅ C and C++ shared libraries loaded")
else:
    print("[app] ⚠️  Shared libs not found – running in Python-only mode (compile .so files for full features)")

# ── Register Blueprints (API Routes) ─────────────────────────────────────────
from auth         import auth_bp
from wallet_routes import wallet_bp
from admin_routes  import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(admin_bp)

# ── Serve Frontend HTML pages ─────────────────────────────────────────────────
_FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


@app.route("/")
def home():
    return send_from_directory(_FRONTEND, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """Serve all static frontend files (HTML, CSS, JS)."""
    full_path = os.path.join(_FRONTEND, filename)
    if os.path.isfile(full_path):
        return send_from_directory(_FRONTEND, filename)
    # Try subdirectory
    return send_from_directory(_FRONTEND, filename)


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "status":     "ok",
        "libs_loaded": libs_loaded(),
        "wallets_loaded": len(_wallets)
    }), 200


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Smart Digital Wallet System running at http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=True)
