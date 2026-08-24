// ============================================================
// common.js — نظام مشترك لكل صفحات الداشبورد المنفصلة
// (المصادقة، الشريط الجانبي، رأس الصفحة، تسجيل الخروج...)
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

const NAV_ITEMS = [
  { key: "home", page: "home.html", labelKey: "nav_home" },
  { key: "skills", page: "skills.html", labelKey: "nav_skills" },
  { key: "bridge", page: "bridge.html", labelKey: "nav_bridge" },
  { key: "connections", page: "connections.html", labelKey: "nav_connections" },
  { key: "opportunities", page: "opportunities.html", labelKey: "nav_opportunities" },
  { key: "competitions", page: "competitions.html", labelKey: "nav_competitions" },
  { key: "messages", page: "messages.html", labelKey: "nav_messages" },
  { key: "contact", page: "contact.html", labelKey: "nav_contact" },
];

/**
 * يتأكد إن المستخدم مسجّل دخوله؛ لو لا، يرجّعه لصفحة تسجيل الدخول.
 * يرجّع بيانات المستخدم (name, username, email, major) عند النجاح.
 */
async function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "index.html";
    return null;
  }
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
    if (!res.ok) {
      clearToken();
      window.location.href = "index.html";
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error("تعذّر التحقق من الجلسة:", err);
    window.location.href = "index.html";
    return null;
  }
}

/**
 * يبني الشريط الجانبي + رأس الصفحة داخل #layout-root، ويحقن main فاضي بمعرّف
 * #page-main يقدر كل ملف صفحة يعبّيه بمحتواه الخاص.
 */
function renderShell(activeKey, user) {
  const root = document.getElementById("layout-root");
  const navHtml = NAV_ITEMS.map(item => `
    <a href="${item.page}" class="nav-item ${item.key === activeKey ? 'active' : ''}">
      <span data-i18n="${item.labelKey}"></span>
      ${item.key === "messages" ? '<span id="unread-badge" class="unread-badge" style="display:none;"></span>' : ''}
    </a>
  `).join("");

  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="sidebar-brand">
          <a href="home.html"><img src="assets/logo.png" alt="اتجاهك" class="brand-logo-img brand-logo-sm"></a>
          <span class="brand-name">اتجاهك</span>
        </div>
        <nav class="sidebar-nav">${navHtml}</nav>
        <button class="btn-ghost btn-block" id="btn-new-analysis" data-i18n="btn_restart"></button>
        <button class="btn-ghost btn-block" id="btn-copy-profile-link" data-i18n="btn_copy_profile_link"></button>
        <button class="btn-ghost btn-block" id="btn-logout" data-i18n="btn_logout"></button>
      </aside>
      <main class="main-content">
        <header class="topbar">
          <button class="lang-toggle">English</button>
          <button class="theme-toggle">🌙</button>
          <div class="topbar-user">
            <span id="user-name-badge">${user ? user.name : "--"}</span>
            <span class="avatar">🙂</span>
          </div>
        </header>
        <div id="page-main"></div>
      </main>
    </div>
  `;

  document.getElementById("btn-new-analysis").addEventListener("click", () => {
    window.location.href = "analyze.html";
  });

  document.getElementById("btn-logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
  });

  document.getElementById("btn-copy-profile-link").addEventListener("click", async () => {
    if (!user || !user.username) return;
    const link = `${window.location.origin}/profile.html?u=${user.username}`;
    const msg = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en")
      ? "Your public profile link was copied ✅\n" : "تم نسخ رابط بروفايلك العام ✅\n";
    try {
      await navigator.clipboard.writeText(link);
      alert(msg + link);
    } catch (err) {
      prompt((typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Copy this link manually:" : "انسخي هذا الرابط يدويًا:", link);
    }
  });

  if (typeof applyTranslations === "function") applyTranslations();
  if (typeof wireThemeToggle === "function") wireThemeToggle();
  loadUnreadBadge();
}

async function loadUnreadBadge() {
  try {
    const res = await fetch(`${API_BASE}/messages/unread-count`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("unread-badge");
    if (!badge) return;
    if (data.unread_count > 0) {
      badge.textContent = data.unread_count;
      badge.style.display = "inline-block";
    } else {
      badge.style.display = "none";
    }
  } catch (err) { /* صامت */ }
}

setInterval(() => { if (getToken()) loadUnreadBadge(); }, 20000);

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function prettify(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// دالة مساعدة: تختار الحقل العربي أو الإنجليزي حسب اللغة الحالية
function bi(obj, arField, enField) {
  if (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en" && obj[enField]) return obj[enField];
  return obj[arField];
}
