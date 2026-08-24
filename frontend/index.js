// ============================================================
// index.js — منطق صفحة الترحيب/تسجيل الدخول/إنشاء الحساب
// ============================================================
const API_BASE = window.ETIJAHAK_API_BASE || "http://127.0.0.1:8000";
const TOKEN_KEY = "etijahak_token";

function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }
function authHeaders() {
  const token = getToken();
  return token ? { "Authorization": "Bearer " + token } : {};
}

function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

document.getElementById("btn-start").addEventListener("click", () => showView("view-signup"));
document.getElementById("btn-goto-login").addEventListener("click", () => showView("view-login"));
document.getElementById("link-goto-login").addEventListener("click", (e) => { e.preventDefault(); showView("view-login"); });
document.getElementById("link-goto-signup").addEventListener("click", (e) => { e.preventDefault(); showView("view-signup"); });

// لو المستخدم مسجّل دخوله من قبل (توكن محفوظ صالح)، ودّيه مباشرة لصفحة الرئيسية
(async function tryAutoLogin() {
  const token = getToken();
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
    if (!res.ok) { clearToken(); return; }
    goAfterAuth();
  } catch (err) {
    console.warn("Auto-login check failed:", err);
  }
})();

function goAfterAuth() {
  const params = new URLSearchParams(window.location.search);
  const composeWith = params.get("compose");
  if (composeWith) {
    window.location.href = `messages.html?compose=${encodeURIComponent(composeWith)}`;
  } else {
    window.location.href = "home.html";
  }
}

// ---------------- Signup ----------------
document.getElementById("signup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errBox = document.getElementById("signup-error");
  errBox.textContent = "";

  const body = {
    name: document.getElementById("su-name").value.trim(),
    email: document.getElementById("su-email").value.trim(),
    major: document.getElementById("su-major").value.trim(),
    password: document.getElementById("su-password").value,
  };

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Signup failed");

    setToken(data.access_token);
    goAfterAuth();
  } catch (err) {
    errBox.textContent = err.message;
  }
});

// ---------------- Login ----------------
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errBox = document.getElementById("login-error");
  errBox.textContent = "";

  const body = {
    email: document.getElementById("li-email").value.trim(),
    password: document.getElementById("li-password").value,
  };

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");

    setToken(data.access_token);
    goAfterAuth();
  } catch (err) {
    errBox.textContent = err.message;
  }
});
