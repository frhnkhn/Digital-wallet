/**
 * app.js - Smart Digital Wallet System Frontend JavaScript
 * 
 * Handles:
 *   - API calls to Flask backend
 *   - Toast notifications
 *   - Session state management
 *   - Dynamic UI updates (balance, transactions)
 *   - Form validation
 */

const API_BASE = "";   // same origin (Flask serves both)

/* ══════════════════════════════════════════════════════
   TOAST NOTIFICATION SYSTEM
═══════════════════════════════════════════════════════ */
(function () {
  const container = document.createElement("div");
  container.id = "toast-container";
  document.body.appendChild(container);

  window.showToast = function (message, type = "info", duration = 3500) {
    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || "ℹ️"}</span>
      <span class="toast-msg">${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = "toastIn 0.3s ease-out reverse";
      setTimeout(() => toast.remove(), 300);
    }, duration);
  };
})();

/* ══════════════════════════════════════════════════════
   API HELPER
═══════════════════════════════════════════════════════ */
async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      ...options,
    });
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 0, data: { error: "Network error" } };
  }
}

/* ══════════════════════════════════════════════════════
   AUTH STATE
═══════════════════════════════════════════════════════ */
async function getMe() {
  const { ok, data } = await apiFetch("/api/me");
  return ok ? data : null;
}

/** Redirect to login if not authenticated */
async function requireAuth() {
  const me = await getMe();
  if (!me) {
    window.location.href = "/login.html";
    return null;
  }
  return me;
}

/** Redirect to dashboard if already authenticated */
async function redirectIfAuth() {
  const me = await getMe();
  if (me) window.location.href = "/dashboard.html";
}

/* ══════════════════════════════════════════════════════
   LOGOUT
═══════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-logout]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await apiFetch("/api/logout", { method: "POST" });
      window.location.href = "/login.html";
    });
  });
});

/* ══════════════════════════════════════════════════════
   SET ACTIVE NAV ITEM
═══════════════════════════════════════════════════════ */
function setActiveNav(page) {
  document.querySelectorAll(".nav-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.page === page);
  });
}

/* ══════════════════════════════════════════════════════
   CURRENCY FORMATTER
═══════════════════════════════════════════════════════ */
function formatCurrency(amount) {
  return "₹" + parseFloat(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/* ══════════════════════════════════════════════════════
   FORMAT DATE
═══════════════════════════════════════════════════════ */
function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/* ══════════════════════════════════════════════════════
   RENDER TRANSACTION ITEM (reusable)
═══════════════════════════════════════════════════════ */
function renderTxn(t, walletId) {
  const isIn     = (t.to_wallet_id === walletId && t.type === "CREDIT") ||
                   (t.direction === "IN");
  const isSystem = t.from_wallet_id === "SYSTEM";
  let iconClass, iconEmoji, amountClass, sign;

  if (isSystem) {
    iconClass = "sys"; iconEmoji = "🏦";
    amountClass = "in"; sign = "+";
  } else if (isIn) {
    iconClass = "in"; iconEmoji = "⬇️";
    amountClass = "in"; sign = "+";
  } else {
    iconClass = "out"; iconEmoji = "⬆️";
    amountClass = "out"; sign = "-";
  }

  return `
    <div class="txn-item fade-in">
      <div class="txn-icon ${iconClass}">${iconEmoji}</div>
      <div class="txn-details">
        <div class="txn-desc">${t.description || "Transaction"}</div>
        <div class="txn-date">${formatDate(t.created_at)}</div>
        <div class="txn-id-text">ID: ${t.id}</div>
      </div>
      <div class="txn-amount ${amountClass}">
        ${sign}${formatCurrency(t.amount)}
      </div>
    </div>
  `;
}

/* ══════════════════════════════════════════════════════
   BUTTON LOADING STATE
═══════════════════════════════════════════════════════ */
function btnLoading(btn, loading, label = "") {
  if (loading) {
    btn.disabled = true;
    btn._originalContent = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn._originalContent || label;
  }
}

/* ══════════════════════════════════════════════════════
   UPDATE SIDEBAR USER INFO
═══════════════════════════════════════════════════════ */
async function populateSidebar() {
  const me = await getMe();
  if (!me) return;
  const el = document.getElementById("sidebar-username");
  if (el) el.textContent = me.username;
  const role = document.getElementById("sidebar-role");
  if (role) role.textContent = me.role === "admin" ? "Administrator" : "Personal Wallet";
  const wid = document.getElementById("sidebar-wallet-id");
  if (wid) wid.textContent = me.wallet_id;

  // Show admin nav if admin
  if (me.role === "admin") {
    document.querySelectorAll(".admin-only").forEach((el) => el.style.display = "flex");
  }
}

/* ══════════════════════════════════════════════════════
   COUNTER ANIMATION
═══════════════════════════════════════════════════════ */
function animateNumber(el, target, prefix = "₹", duration = 800) {
  const start = 0;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed  = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease     = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    const current  = start + (target - start) * ease;
    el.textContent = prefix + current.toLocaleString("en-IN", {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

/* ══════════════════════════════════════════════════════
   EXPOSE TO GLOBAL SCOPE
═══════════════════════════════════════════════════════ */
window.Wallet = {
  apiFetch, getMe, requireAuth, redirectIfAuth,
  formatCurrency, formatDate, renderTxn,
  btnLoading, setActiveNav, populateSidebar,
  animateNumber, showToast,
};
