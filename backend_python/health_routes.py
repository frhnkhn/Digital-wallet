"""
health_routes.py - Financial Health Score Blueprint
Route: GET /api/health-score

Score Components (0-100 total):
  - Savings Rate       (30 pts): jar savings vs wallet top-ups in last 30 days
  - Balance Stability  (20 pts): wallet balance staying consistently positive/growing
  - Jar Activity       (20 pts): active jars + completion rate
  - Spending Discipline(20 pts): ratio of small consistent txns vs. erratic large ones
  - Account Activity   (10 pts): engagement — how actively the wallet is used
"""

from flask import Blueprint, jsonify, session
from database import (
    get_wallet_by_owner, get_transactions_for_wallet,
    get_jars_for_user, get_total_jars_saved
)
import math

health_bp = Blueprint("health", __name__)


def _require_login():
    if "user_id" not in session:
        return None, None
    return session["user_id"], session["wallet_id"]


# ─────────────────────────────────────────────────────────────────────────────

def _score_savings_rate(txns, jar_saved_total, wallet_balance):
    """Up to 30 pts. Based on ratio of jar savings to total money added."""
    credits = [t for t in txns if t.get("type") == "CREDIT"
               and t.get("from_wallet_id") == "SYSTEM"]
    total_added = sum(t["amount"] for t in credits) or 1

    # Savings rate = saved in jars / total added in
    rate = min(jar_saved_total / total_added, 1.0)
    pts = round(rate * 30)
    if rate == 0:
        tip = "Start adding money to jars to boost your savings rate."
    elif rate < 0.1:
        tip = "Try saving at least 10% of each top-up into jars."
    elif rate < 0.25:
        tip = "Good start! Aim for 25%+ savings rate for a stronger score."
    else:
        tip = "Excellent savings discipline! Keep it up."
    return pts, round(rate * 100, 1), tip


def _score_balance_stability(txns, current_balance):
    """Up to 20 pts. Consistent non-zero balance; penalise balance approaching 0."""
    if current_balance <= 0:
        return 0, "Your balance is empty. Add money to improve stability.", current_balance

    # Reward higher absolute balance (logarithmic, caps at ₹50,000)
    log_score = min(math.log10(max(current_balance, 1)) / math.log10(50000), 1.0)
    pts = round(log_score * 20)

    # Check for any debit transactions that brought balance very low
    debits = [t for t in txns if t.get("type") == "DEBIT"]
    large_debits = [t for t in debits if t["amount"] > current_balance * 0.6]
    if large_debits:
        pts = max(pts - 5, 0)
        tip = "Avoid very large single withdrawals to stay stable."
    elif pts >= 16:
        tip = "Great! Your balance is healthy and stable."
    elif pts >= 10:
        tip = "Keep adding money regularly to improve stability."
    else:
        tip = "Low balance detected. Top up your wallet to improve this score."

    return pts, tip, current_balance


def _score_jar_activity(jars):
    """Up to 20 pts. Rewards having active jars and completing them."""
    if not jars:
        return 0, 0, "Create your first Money Jar to earn points here."

    active_jars = len(jars)
    completed   = sum(1 for j in jars if j.get("is_complete"))
    in_progress = active_jars - completed
    completion_rate = (completed / active_jars) * 100 if active_jars else 0

    # 5 pts per active jar (max 10 pts) + up to 10 pts for completion rate
    jar_pts    = min(active_jars * 5, 10)
    comp_pts   = round((completion_rate / 100) * 10)
    pts        = jar_pts + comp_pts

    if completed == 0 and active_jars > 0:
        tip = "Keep funding your jars to reach your goals!"
    elif completion_rate == 100:
        tip = "Amazing! All your jars are complete. Create new goals!"
    else:
        tip = f"{completed} jar(s) done, {in_progress} in progress. Build consistency!"

    return pts, round(completion_rate, 1), tip


def _score_spending_discipline(txns):
    """Up to 20 pts. Rewards many small, consistent transactions over erratic large ones."""
    debits = [t for t in txns if t.get("type") == "DEBIT"
              and t.get("from_wallet_id") not in ("SYSTEM", "JARS")]
    if not debits:
        return 10, "No spending history yet. Make some transactions.", 0

    amounts = [t["amount"] for t in debits]
    avg     = sum(amounts) / len(amounts)
    # Standard deviation as volatility measure
    variance = sum((a - avg) ** 2 for a in amounts) / len(amounts)
    std_dev  = math.sqrt(variance)
    cv       = (std_dev / avg) if avg > 0 else 0  # coefficient of variation

    # Low CV = consistent spending = good
    consistency_score = max(0, 1 - min(cv / 2, 1))
    # Frequency bonus: more transactions = more engaged user
    freq_score = min(len(debits) / 20, 1.0)
    pts = round((consistency_score * 14) + (freq_score * 6))

    if cv < 0.3:
        tip = "Very consistent spending habits. Well done!"
    elif cv < 0.8:
        tip = "Moderate consistency. Try to spread spending evenly."
    else:
        tip = "Erratic spending detected. Avoid large one-off splurges."

    return pts, tip, len(debits)


def _score_account_activity(txns, wallet_created_at):
    """Up to 10 pts. Rewards active usage of the account."""
    total_txns = len(txns)
    # 2 pts per 5 transactions, max 10
    pts = min((total_txns // 5) * 2, 10)

    if total_txns == 0:
        tip = "Make your first transaction to earn activity points."
    elif pts >= 8:
        tip = "Very active account. Great engagement!"
    else:
        tip = f"{total_txns} transactions logged. Keep using SmartWallet!"

    return pts, total_txns, tip


def _grade(score):
    if score >= 85:
        return "Excellent", "#10b981", "🏆"
    elif score >= 70:
        return "Good", "#22c55e", "✅"
    elif score >= 50:
        return "Fair", "#f59e0b", "⚠️"
    elif score >= 30:
        return "Poor", "#ef4444", "📉"
    else:
        return "Critical", "#dc2626", "🚨"


# ─────────────────────────────────────────────────────────────────────────────

@health_bp.route("/api/health-score", methods=["GET"])
def get_health_score():
    uid, wid = _require_login()
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    wallet_row = get_wallet_by_owner(uid)
    if not wallet_row:
        return jsonify({"error": "Wallet not found"}), 404

    # Convert sqlite3.Row -> dict so .get() works safely everywhere
    wallet = dict(wallet_row)

    txns    = get_transactions_for_wallet(wid, limit=100)
    jars    = get_jars_for_user(uid)
    jar_saved = get_total_jars_saved(uid)
    balance = wallet["balance"]

    # ── Component scores ──────────────────────────────────────────────────────
    s_pts, savings_rate_pct, s_tip  = _score_savings_rate(txns, jar_saved, balance)
    b_pts, b_tip, _                 = _score_balance_stability(txns, balance)
    j_pts, completion_pct, j_tip    = _score_jar_activity(jars)
    d_pts, d_tip, txn_count         = _score_spending_discipline(txns)
    a_pts, total_txns, a_tip        = _score_account_activity(txns, wallet.get("created_at", ""))

    total = s_pts + b_pts + j_pts + d_pts + a_pts
    grade, color, icon = _grade(total)

    return jsonify({
        "score":  total,
        "grade":  grade,
        "color":  color,
        "icon":   icon,
        "components": [
            {
                "key":     "savings",
                "label":   "Savings Rate",
                "points":  s_pts,
                "max":     30,
                "tip":     s_tip,
                "detail":  f"{savings_rate_pct}% of top-ups saved in jars",
                "icon":    "🫙"
            },
            {
                "key":     "stability",
                "label":   "Balance Stability",
                "points":  b_pts,
                "max":     20,
                "tip":     b_tip,
                "detail":  f"Current balance: ₹{round(balance, 2):,.2f}",
                "icon":    "⚖️"
            },
            {
                "key":     "jars",
                "label":   "Jar Activity",
                "points":  j_pts,
                "max":     20,
                "tip":     j_tip,
                "detail":  f"{len(jars)} jar(s) · {completion_pct}% completion rate",
                "icon":    "🎯"
            },
            {
                "key":     "discipline",
                "label":   "Spending Discipline",
                "points":  d_pts,
                "max":     20,
                "tip":     d_tip,
                "detail":  f"{txn_count} spending transaction(s) analysed",
                "icon":    "🧾"
            },
            {
                "key":     "activity",
                "label":   "Account Activity",
                "points":  a_pts,
                "max":     10,
                "tip":     a_tip,
                "detail":  f"{total_txns} total transaction(s)",
                "icon":    "📊"
            },
        ],
        "meta": {
            "wallet_balance":  round(balance, 2),
            "total_jar_saved": jar_saved,
            "jar_count":       len(jars),
            "total_txns":      total_txns,
        }
    }), 200
