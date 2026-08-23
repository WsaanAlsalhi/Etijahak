// ============================================================
// اتجاهك — Frontend Logic (نسخة الإنتاج: تسجيل دخول + قاعدة بيانات)
// عدّلي API_BASE فقط إذا غيّرتِ عنوان الـ Backend (مثلاً بعد النشر).
// ============================================================
const API_BASE = window.ETIJAHAK_API_BASE || "http://127.0.0.1:8000";
const TOKEN_KEY = "etijahak_token";

// ---------------- Token helpers ----------------
function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }

function authHeaders() {
  const token = getToken();
  return token ? { "Authorization": "Bearer " + token } : {};
}

// ---------------- View switching ----------------
function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

// ---------------- Navigation between landing/signup/login ----------------
document.getElementById("btn-start").addEventListener("click", () => showView("view-signup"));
document.getElementById("btn-goto-login").addEventListener("click", () => showView("view-login"));
document.getElementById("link-goto-login").addEventListener("click", (e) => { e.preventDefault(); showView("view-login"); });
document.getElementById("link-goto-signup").addEventListener("click", (e) => { e.preventDefault(); showView("view-signup"); });

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
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Failed to create account" : "فشل إنشاء الحساب"));

    setToken(data.access_token);
    await afterAuthSuccess(data.user_name, data.username);
    await handleComposeParam();
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
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Failed to log in" : "فشل تسجيل الدخول"));

    setToken(data.access_token);
    await afterAuthSuccess(data.user_name, data.username);
    await handleComposeParam();
  } catch (err) {
    errBox.textContent = err.message;
  }
});

// ---------------- Logout ----------------
document.getElementById("btn-logout").addEventListener("click", () => {
  clearToken();
  showView("view-landing");
});

document.getElementById("btn-restart").addEventListener("click", () => {
  showView("view-onboarding");
});

// ---------------- After successful auth: load goals + saved profile, go to onboarding ----------------
let currentUsername = null;

async function afterAuthSuccess(userName, username) {
  document.getElementById("user-name-badge").textContent = userName || (CURRENT_LANG === "en" ? "User" : "مستخدم");
  currentUsername = username || null;
  await loadGoals();
  await prefillSavedProfile();
  await refreshGithubStatus();
  await refreshLinkedinStatus();
  loadUnreadBadge();
  showView("view-onboarding");
}

// تحديث دوري لعدد الرسائل غير المقروءة كل 20 ثانية بغض النظر عن الشاشة الحالية
setInterval(() => { if (getToken()) loadUnreadBadge(); }, 20000);

document.getElementById("btn-copy-profile-link").addEventListener("click", async () => {
  if (!currentUsername) {
    alert(CURRENT_LANG === "en" ? "Couldn\u2019t determine your profile link. Try logging in again." : "تعذّر تحديد رابط بروفايلك حاليًا، حاولي تسجيل الدخول من جديد.");
    return;
  }
  const link = `${window.location.origin}/profile.html?u=${currentUsername}`;
  try {
    await navigator.clipboard.writeText(link);
    alert((CURRENT_LANG === "en" ? "Your public profile link was copied ✅\n" : "تم نسخ رابط بروفايلك العام ✅\n") + link);
  } catch (err) {
    prompt(CURRENT_LANG === "en" ? "Copy this link manually:" : "انسخي هذا الرابط يدويًا:", link);
  }
});

// عند تحميل الصفحة، تحققي إن كنا راجعين من GitHub/LinkedIn بعد الموافقة
handleOAuthRedirectParams();

// إذا كان فيه توكن محفوظ من قبل (المستخدم مسجّل دخوله سابقًا)، ادخليه مباشرة
(async function tryAutoLogin() {
  const token = getToken();
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
    if (!res.ok) { clearToken(); return; }
    const user = await res.json();
    await afterAuthSuccess(user.name, user.username);
    await handleComposeParam();
  } catch (err) {
    console.warn("Auto-login failed:", err);
  }
})();

// ---------------- Load goals dropdown ----------------
async function loadGoals() {
  const select = document.getElementById("f-goal");
  select.innerHTML = `<option value="">جارِ التحميل...</option>`;
  try {
    const [goalsRes, aiStatusRes] = await Promise.all([
      fetch(`${API_BASE}/goals`),
      fetch(`${API_BASE}/goals/ai-status`),
    ]);
    const goals = await goalsRes.json();
    const aiStatus = aiStatusRes.ok ? await aiStatusRes.json() : { enabled: false };

    let myCustomGoals = [];
    try {
      const mineRes = await fetch(`${API_BASE}/goals/mine`, { headers: authHeaders() });
      if (mineRes.ok) myCustomGoals = await mineRes.json();
    } catch (e) { /* تجاهل، ليست حرجة */ }

    let optionsHtml = goals.map(g => `<option value="${g.key}">${bi(g, "name_ar", "name_en")}</option>`).join("");
    if (myCustomGoals.length > 0) {
      optionsHtml += `<optgroup label="${CURRENT_LANG === 'en' ? 'Your previous custom goals' : 'أهدافك المخصصة السابقة'}">` +
        myCustomGoals.map(g => `<option value="${g.key}">${bi(g, "name_ar", "name_en")}</option>`).join("") +
        `</optgroup>`;
    }
    select.innerHTML = optionsHtml;

    const customBox = document.getElementById("custom-goal-box");
    if (aiStatus.enabled) {
      customBox.style.display = "block";
    } else {
      customBox.style.display = "none";
    }
  } catch (err) {
    select.innerHTML = `<option value="">تعذّر الاتصال بالخادم</option>`;
    console.error(err);
  }
}

document.getElementById("btn-generate-goal").addEventListener("click", async () => {
  const input = document.getElementById("custom-goal-text");
  const statusEl = document.getElementById("custom-goal-status");
  const goalText = input.value.trim();
  if (!goalText) {
    statusEl.textContent = CURRENT_LANG === "en" ? "Write your goal first" : "اكتبي هدفك أولًا";
    return;
  }

  const btn = document.getElementById("btn-generate-goal");
  btn.disabled = true;
  btn.textContent = CURRENT_LANG === "en" ? "Analyzing..." : "جارِ التحليل...";
  statusEl.textContent = "";

  try {
    const res = await fetch(`${API_BASE}/goals/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ goal_text: goalText }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Couldn\u2019t analyze this goal" : "تعذّر تحليل هذا الهدف"));

    const select = document.getElementById("f-goal");
    const opt = document.createElement("option");
    opt.value = data.key;
    opt.textContent = `${data.name_ar} (مخصص جديد)`;
    opt.selected = true;
    select.appendChild(opt);

    statusEl.textContent = `✅ تم تحليل الهدف وإضافته: ${data.name_ar}`;
    input.value = "";
  } catch (err) {
    statusEl.textContent = "❌ " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "🤖 حلّليه";
  }
});

// ---------------- Prefill form with previously saved profile ----------------
async function prefillSavedProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("skills-list").innerHTML = "";
    document.getElementById("projects-list").innerHTML = "";
    document.getElementById("certificates-list").innerHTML = "";

    (data.skills || []).forEach(s => {
      addRepeatItem("skill");
      const row = document.getElementById("skills-list").lastElementChild;
      row.querySelector(".skill-name").value = s.name;
      row.querySelector(".skill-level").value = s.level;
    });
    (data.projects || []).forEach(p => {
      addRepeatItem("project");
      const row = document.getElementById("projects-list").lastElementChild;
      row.querySelector(".project-title").value = p.title;
      row.querySelector(".project-tags").value = (p.tags || []).join(", ");
      row.querySelector(".project-repo").checked = !!p.has_repo;
    });
    (data.certificates || []).forEach(c => {
      addRepeatItem("certificate");
      const row = document.getElementById("certificates-list").lastElementChild;
      row.querySelector(".cert-title").value = c.title;
      row.querySelector(".cert-tags").value = (c.tags || []).join(", ");
    });

    if (data.last_goal_key) {
      document.getElementById("f-goal").value = data.last_goal_key;
    }

    if (!data.skills || data.skills.length === 0) addRepeatItem("skill");
    if (!data.projects || data.projects.length === 0) addRepeatItem("project");
  } catch (err) {
    console.warn("تعذّر تحميل الملف المحفوظ:", err);
    addRepeatItem("skill");
    addRepeatItem("project");
  }
}

// ---------------- Repeatable fields (skills/projects/certificates) ----------------
function addRepeatItem(kind) {
  const map = {
    skill: { list: "skills-list", tpl: "tpl-skill" },
    project: { list: "projects-list", tpl: "tpl-project" },
    certificate: { list: "certificates-list", tpl: "tpl-certificate" },
  };
  const { list, tpl } = map[kind];
  const listEl = document.getElementById(list);
  const template = document.getElementById(tpl);
  const clone = template.content.cloneNode(true);
  clone.querySelector(".btn-remove").addEventListener("click", (e) => {
    e.target.closest(".repeat-item").remove();
  });
  listEl.appendChild(clone);
}

document.querySelectorAll("[data-add]").forEach(btn => {
  btn.addEventListener("click", () => addRepeatItem(btn.dataset.add));
});

// ---------------- Collect form data ----------------
function parseTags(value) {
  return value.split(",").map(t => t.trim().toLowerCase().replace(/\s+/g, "_")).filter(Boolean);
}

function collectProfile() {
  const name = document.getElementById("f-name") ? document.getElementById("f-name").value.trim() : "";
  const skills = Array.from(document.querySelectorAll("#skills-list .repeat-item")).map(row => ({
    name: row.querySelector(".skill-name").value.trim().toLowerCase().replace(/\s+/g, "_"),
    level: parseInt(row.querySelector(".skill-level").value, 10),
  })).filter(s => s.name);

  const projects = Array.from(document.querySelectorAll("#projects-list .repeat-item")).map(row => ({
    title: row.querySelector(".project-title").value.trim(),
    tags: parseTags(row.querySelector(".project-tags").value),
    has_repo: row.querySelector(".project-repo").checked,
  })).filter(p => p.title);

  const certificates = Array.from(document.querySelectorAll("#certificates-list .repeat-item")).map(row => ({
    title: row.querySelector(".cert-title").value.trim(),
    tags: parseTags(row.querySelector(".cert-tags").value),
  })).filter(c => c.title);

  return { name: name || document.getElementById("user-name-badge").textContent, skills, projects, experiences: [], certificates };
}

// ---------------- Submit -> /analyze then /opportunities ----------------
document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.textContent = CURRENT_LANG === "en" ? "Analyzing..." : "جارِ التحليل...";

  const profile = collectProfile();
  const goalKey = document.getElementById("f-goal").value;

  try {
    const analyzeRes = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ profile, goal_key: goalKey }),
    });
    if (analyzeRes.status === 401) { clearToken(); showView("view-login"); throw new Error(CURRENT_LANG === "en" ? "Session expired, please log in again" : "انتهت الجلسة، سجّلي الدخول مجددًا"); }
    if (!analyzeRes.ok) {
      const errData = await analyzeRes.json().catch(() => ({}));
      throw new Error(errData.detail || ("فشل التحليل: " + analyzeRes.status));
    }
    const analysis = await analyzeRes.json();

    const oppRes = await fetch(`${API_BASE}/opportunities`, { headers: authHeaders() });
    const opportunities = oppRes.ok ? await oppRes.json() : [];

    const profileRes = await fetch(`${API_BASE}/profile`, { headers: authHeaders() });
    const profileData = profileRes.ok ? await profileRes.json() : {};

    renderDashboard(profile, analysis, opportunities, profileData.github_projects || []);
    showView("view-dashboard");

    // نجلب المسابقات بعد التحليل مباشرة (تعتمد على قدرات المستخدم المحفوظة تلقائيًا)
    loadCompetitions();
  } catch (err) {
    alert(err.message);
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = t("btn_analyze");
  }
});

// ---------------- Render dashboard ----------------
// دالة مساعدة: تختار الحقل العربي أو الإنجليزي حسب اللغة الحالية
function bi(obj, arField, enField) {
  if (CURRENT_LANG === "en" && obj[enField]) return obj[enField];
  return obj[arField];
}

let lastAnalysis = null, lastOpportunities = null, lastGithubProjects = null, lastProfile = null;

// تُستدعى تلقائيًا عند تبديل اللغة لإعادة رسم أي محتوى ديناميكي معروض حاليًا
window.rerenderDynamicContent = function () {
  if (lastAnalysis) renderDashboard(lastProfile, lastAnalysis, lastOpportunities, lastGithubProjects);
  if (document.getElementById("competitions-list") && document.getElementById("competitions-list").dataset.loaded) {
    loadCompetitions();
  }
};

function renderDashboard(profile, analysis, opportunities, githubProjects) {
  lastProfile = profile; lastAnalysis = analysis; lastOpportunities = opportunities; lastGithubProjects = githubProjects;

  const goalName = bi(analysis, "goal_name_ar", "goal_name_en");
  document.getElementById("greet-name").textContent = profile.name || (CURRENT_LANG === "en" ? "you" : "بك");
  document.getElementById("greet-goal").textContent = goalName;
  document.getElementById("sum-goal").textContent = goalName;
  document.getElementById("sum-gaps").textContent = analysis.gaps.length + (CURRENT_LANG === "en" ? " gaps" : " فجوة");

  const readiness = analysis.overall_readiness;
  document.getElementById("readiness-value").textContent = readiness + "%";
  const circumference = 326.7;
  const offset = circumference - (circumference * readiness) / 100;
  document.getElementById("ring-fg").style.strokeDashoffset = offset;

  const emptyCap = CURRENT_LANG === "en" ? "No skills yet — add skills or projects to your profile." : "لا توجد مهارات كافية بعد — أضيفي مهارات أو مشاريع في ملفك.";
  const capWrap = document.getElementById("capabilities-list");
  capWrap.innerHTML = analysis.capabilities.length === 0
    ? `<div class="empty-hint">${emptyCap}</div>`
    : analysis.capabilities.map(c => `
      <div class="bar-row">
        <div class="bar-top"><span>${prettify(c.skill)}</span><span>${c.score}%</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${c.score}%"></div></div>
        ${c.evidence.length ? `<div class="bar-evidence">✓ ${c.evidence.join(" · ")}</div>` : ""}
      </div>`).join("");

  const emptyGaps = CURRENT_LANG === "en" ? "🎉 No major gaps — you're very close to your goal!" : "🎉 لا توجد فجوات كبيرة — أنت قريب جدًا من هدفك!";
  const gapsWrap = document.getElementById("gaps-list");
  gapsWrap.innerHTML = analysis.gaps.length === 0
    ? `<div class="empty-hint">${emptyGaps}</div>`
    : analysis.gaps.map(g => `
      <div class="gap-chip">
        <span>${bi(g, "label_ar", "label_en")} <span class="muted">(${g.current_score}% / ${g.required_score}%)</span></span>
        <span class="gap-type ${g.gap_type}">${g.gap_type === "network" ? (CURRENT_LANG === "en" ? "Network Gap" : "فجوة شبكة") : (CURRENT_LANG === "en" ? "Skill/Evidence" : "قدرة/دليل")}</span>
      </div>`).join("");

  document.getElementById("bridge-list").innerHTML = analysis.bridge.map(step => `
    <li>
      <div class="step-num">${step.order}</div>
      <div class="step-body">
        <strong>${bi(step, "title_ar", "title_en")}</strong>
        <span>${bi(step, "description_ar", "description_en")}</span>
      </div>
    </li>`).join("");

  const emptyConn = CURRENT_LANG === "en" ? "Add more projects so we can suggest relevant people to connect with." : "أضيفي مزيدًا من المشاريع لنقترح أشخاصًا مناسبين للتواصل.";
  const connWrap = document.getElementById("connections-list");
  connWrap.innerHTML = analysis.connections.length === 0
    ? `<div class="empty-hint">${emptyConn}</div>`
    : analysis.connections.map(c => `
      <div class="person-card">
        <div class="person-icon">${c.icon}</div>
        <div class="person-body">
          <strong>${bi(c, "name_ar", "name_en")}</strong>
          <span class="role">${bi(c, "role_ar", "role_en")}</span>
          <span class="reason">${bi(c, "reason_ar", "reason_en")}</span>
        </div>
        <div class="match-badge">${c.match_score}%</div>
      </div>`).join("");

  const emptyOpp = CURRENT_LANG === "en" ? "No opportunities available right now." : "لا توجد فرص متاحة حاليًا.";
  const oppWrap = document.getElementById("opportunities-list");
  oppWrap.innerHTML = (!opportunities || opportunities.length === 0)
    ? `<div class="empty-hint">${emptyOpp}</div>`
    : opportunities.map(o => `
      <div class="opp-card">
        <div class="opp-icon">${o.icon}</div>
        <div class="opp-body">
          <strong>${bi(o, "name_ar", "name_en")}</strong>
          <span class="type">${o.type}</span>
          <div class="reason">${bi(o, "reason_ar", "reason_en")}</div>
        </div>
        <div class="opp-match">${o.match_score}%</div>
      </div>`).join("");

  // مشاريع GitHub
  const noDesc = CURRENT_LANG === "en" ? "No description" : "بدون وصف";
  const ghSection = document.getElementById("section-github-projects");
  const ghWrap = document.getElementById("github-projects-list");
  if (githubProjects && githubProjects.length > 0) {
    ghSection.style.display = "block";
    ghWrap.innerHTML = githubProjects.map(p => `
      <div class="opp-card">
        <div class="opp-icon">🐙</div>
        <div class="opp-body">
          <strong><a href="${p.url}" target="_blank" rel="noopener">${p.title}</a></strong>
          <span class="type">${(p.tags || []).join(", ")}</span>
          <div class="reason">${p.description || noDesc}</div>
        </div>
        <div class="opp-match">⭐ ${p.stars || 0}</div>
      </div>`).join("");
  } else {
    ghSection.style.display = "none";
  }
}

function prettify(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ---------------- GitHub / LinkedIn Connection ----------------
document.getElementById("btn-connect-github").addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/github/connect`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Failed to start GitHub connection" : "فشل بدء ربط GitHub"));
    window.location.href = data.authorize_url; // يوجّه المتصفح فعليًا لصفحة GitHub
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("btn-connect-linkedin").addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/linkedin/connect`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Failed to start LinkedIn sign-in" : "فشل بدء تسجيل الدخول عبر LinkedIn"));
    window.location.href = data.authorize_url;
  } catch (err) {
    alert(err.message);
  }
});

async function refreshGithubStatus() {
  try {
    const res = await fetch(`${API_BASE}/github/status`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const textEl = document.getElementById("github-status-text");
    const btnEl = document.getElementById("btn-connect-github");
    if (data.connected) {
      textEl.textContent = `مربوط ✓ (@${data.github_username})`;
      textEl.classList.add("connected");
      btnEl.textContent = CURRENT_LANG === "en" ? "Re-sync Projects" : "إعادة مزامنة المشاريع";
      btnEl.onclick = syncGithubProjects;
    }
  } catch (err) {
    console.warn("تعذّر جلب حالة GitHub:", err);
  }
}

async function syncGithubProjects(e) {
  if (e) e.preventDefault();
  const btn = document.getElementById("btn-connect-github");
  const original = btn.textContent;
  btn.textContent = CURRENT_LANG === "en" ? "Syncing..." : "جارِ المزامنة...";
  try {
    const res = await fetch(`${API_BASE}/github/sync`, { method: "POST", headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || (CURRENT_LANG === "en" ? "Sync failed" : "فشلت المزامنة"));
    alert(`تمت مزامنة ${data.count} مشروع من GitHub بنجاح ✅`);
  } catch (err) {
    alert(err.message);
  } finally {
    btn.textContent = original;
  }
}

async function refreshLinkedinStatus() {
  try {
    const res = await fetch(`${API_BASE}/linkedin/status`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const textEl = document.getElementById("linkedin-status-text");
    const btnEl = document.getElementById("btn-connect-linkedin");
    if (data.verified) {
      textEl.textContent = `مؤكّد ✓ (${data.linkedin_name || ""})`;
      textEl.classList.add("connected");
      btnEl.textContent = CURRENT_LANG === "en" ? "Verified" : "تم التأكيد";
      btnEl.disabled = true;
    }
  } catch (err) {
    console.warn("تعذّر جلب حالة LinkedIn:", err);
  }
}

// يعالج الرجوع من GitHub/LinkedIn (عبر query params بالرابط بعد إعادة التوجيه)
function handleOAuthRedirectParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("github_connected")) {
    alert(CURRENT_LANG === "en" ? "GitHub connected successfully ✅ Click 'Re-sync Projects' to pull your repos." : "تم ربط GitHub بنجاح ✅ اضغطي 'إعادة مزامنة المشاريع' لسحب مستودعاتك.");
  } else if (params.get("github_error")) {
    alert(CURRENT_LANG === "en" ? "Couldn\u2019t connect GitHub, please try again." : "تعذّر ربط GitHub، حاولي مجددًا.");
  }
  if (params.get("linkedin_connected")) {
    alert(CURRENT_LANG === "en" ? "LinkedIn account verified successfully ✅" : "تم تأكيد حساب LinkedIn بنجاح ✅");
  } else if (params.get("linkedin_error")) {
    alert(CURRENT_LANG === "en" ? "Couldn\u2019t sign in with LinkedIn, please try again." : "تعذّر تسجيل الدخول عبر LinkedIn، حاولي مجددًا.");
  }
  if (params.toString()) {
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

// ---------------- Competitions / Hackathons ----------------
async function loadCompetitions() {
  const wrap = document.getElementById("competitions-list");
  wrap.innerHTML = `<div class="empty-hint">جارِ جلب المسابقات الحقيقية من Devpost...</div>`;
  try {
    const res = await fetch(`${API_BASE}/competitions`, { headers: authHeaders() });
    if (!res.ok) throw new Error(CURRENT_LANG === "en" ? "Couldn\u2019t load competitions" : "تعذّر جلب المسابقات");
    const competitions = await res.json();
    renderCompetitions(competitions);
  } catch (err) {
    const errMsg = CURRENT_LANG === "en" ? "Couldn't load competitions. Try again later." : "تعذّر جلب المسابقات حاليًا. حاولي لاحقًا.";
    wrap.innerHTML = `<div class="empty-hint">${errMsg}</div>`;
    console.error(err);
  }
}

function renderCompetitions(competitions) {
  const wrap = document.getElementById("competitions-list");
  wrap.dataset.loaded = "1";
  if (!competitions || competitions.length === 0) {
    const noComp = CURRENT_LANG === "en" ? "No open competitions right now." : "لا توجد مسابقات مفتوحة حاليًا.";
    wrap.innerHTML = `<div class="empty-hint">${noComp}</div>`;
    return;
  }

  const isEn = CURRENT_LANG === "en";
  const labels = isEn
    ? { match: "Match", registered: "Registered", participated: "Participated Before", organizer: "Organizer", clear: "Clear", people: "registered" }
    : { match: "تطابق", registered: "مسجّل", participated: "شاركت سابقًا", organizer: "مشرف/منظّم", clear: "إلغاء التعليم", people: "مسجّل" };

  wrap.innerHTML = competitions.map(c => `
    <div class="comp-card" data-comp-id="${c.id}" data-comp-title="${escapeHtml(c.title)}">
      <div class="comp-top">
        <div>
          <div class="comp-title"><a href="${c.url}" target="_blank" rel="noopener">${c.title}</a></div>
          <div class="comp-org">${c.organizer} · ${c.location}</div>
        </div>
        ${c.match_score > 0 ? `<div class="comp-match-badge">${labels.match} ${c.match_score}%</div>` : ""}
      </div>
      <div class="comp-meta">
        <span>📅 <strong>${c.dates}</strong></span>
        <span>⏳ ${c.time_left}</span>
        <span>💰 <strong>${c.prize}</strong></span>
        <span>👥 ${c.registrations_count} ${labels.people}</span>
      </div>
      <div class="comp-actions">
        <button type="button" class="status-btn ${c.my_status === 'registered' ? 'active-registered' : ''}" data-status="registered">${labels.registered}</button>
        <button type="button" class="status-btn ${c.my_status === 'participated' ? 'active-participated' : ''}" data-status="participated">${labels.participated}</button>
        <button type="button" class="status-btn ${c.my_status === 'organizer' ? 'active-organizer' : ''}" data-status="organizer">${labels.organizer}</button>
        ${c.my_status ? `<button type="button" class="status-clear" data-status="null">${labels.clear}</button>` : ""}
      </div>
    </div>
  `).join("");

  wrap.querySelectorAll(".status-btn, .status-clear").forEach(btn => {
    btn.addEventListener("click", () => updateCompetitionStatus(btn));
  });
}

async function updateCompetitionStatus(btnEl) {
  const card = btnEl.closest(".comp-card");
  const competitionId = card.dataset.compId;
  const competitionTitle = card.dataset.compTitle;
  const newStatus = btnEl.dataset.status === "null" ? null : btnEl.dataset.status;

  try {
    const res = await fetch(`${API_BASE}/competitions/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ competition_id: competitionId, competition_title: competitionTitle, status: newStatus }),
    });
    if (!res.ok) throw new Error(CURRENT_LANG === "en" ? "Failed to save status" : "فشل حفظ الحالة");
    const data = await res.json();

    // تحديث الواجهة فورًا بدون أي إعادة تحميل للصفحة
    card.querySelectorAll(".status-btn").forEach(b => {
      b.classList.remove("active-registered", "active-participated", "active-organizer");
      if (data.status && b.dataset.status === data.status) {
        b.classList.add(`active-${data.status}`);
      }
    });
    let clearBtn = card.querySelector(".status-clear");
    if (data.status && !clearBtn) {
      clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.className = "status-clear";
      clearBtn.dataset.status = "null";
      clearBtn.textContent = CURRENT_LANG === "en" ? "Clear" : "إلغاء التعليم";
      clearBtn.addEventListener("click", () => updateCompetitionStatus(clearBtn));
      card.querySelector(".comp-actions").appendChild(clearBtn);
    } else if (!data.status && clearBtn) {
      clearBtn.remove();
    }
  } catch (err) {
    alert(err.message);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------- Messaging ----------------
let activeConversationUsername = null;
let messagesPollInterval = null;

async function loadUnreadBadge() {
  try {
    const res = await fetch(`${API_BASE}/messages/unread-count`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("unread-badge");
    if (data.unread_count > 0) {
      badge.textContent = data.unread_count;
      badge.style.display = "inline-block";
    } else {
      badge.style.display = "none";
    }
  } catch (err) { /* صامت، ليست حرجة */ }
}

async function loadConversations() {
  try {
    const res = await fetch(`${API_BASE}/messages/conversations`, { headers: authHeaders() });
    if (!res.ok) return;
    const conversations = await res.json();
    const wrap = document.getElementById("conversations-list");
    wrap.innerHTML = conversations.length === 0
      ? `<div class="empty-hint" style="font-size:12px;">${CURRENT_LANG === "en" ? "No conversations yet" : "لا توجد محادثات بعد"}</div>`
      : conversations.map(c => `
        <div class="conv-item ${c.username === activeConversationUsername ? 'active' : ''}" data-username="${c.username}">
          <div>
            <strong>${c.name}</strong>
            <span class="preview">${c.last_message}</span>
          </div>
          ${c.unread > 0 ? `<span class="conv-unread">${c.unread}</span>` : ""}
        </div>
      `).join("");

    wrap.querySelectorAll(".conv-item").forEach(item => {
      item.addEventListener("click", () => openConversation(item.dataset.username, item.querySelector("strong").textContent));
    });
  } catch (err) {
    console.warn("تعذّر تحميل المحادثات:", err);
  }
}

document.getElementById("user-search-input").addEventListener("input", async (e) => {
  const q = e.target.value.trim();
  const resultsBox = document.getElementById("user-search-results");
  if (q.length < 2) { resultsBox.innerHTML = ""; return; }

  try {
    const res = await fetch(`${API_BASE}/users/search?q=${encodeURIComponent(q)}`, { headers: authHeaders() });
    if (!res.ok) return;
    const users = await res.json();
    resultsBox.innerHTML = users.length === 0
      ? `<div class="search-result-item muted">${CURRENT_LANG === "en" ? "No results" : "لا نتائج"}</div>`
      : users.map(u => `<div class="search-result-item" data-username="${u.username}" data-name="${u.name}">${u.name} <span class="muted">(@${u.username})</span></div>`).join("");

    resultsBox.querySelectorAll(".search-result-item[data-username]").forEach(item => {
      item.addEventListener("click", () => {
        openConversation(item.dataset.username, item.dataset.name);
        document.getElementById("user-search-input").value = "";
        resultsBox.innerHTML = "";
      });
    });
  } catch (err) { console.warn(err); }
});

async function openConversation(username, name) {
  activeConversationUsername = username;
  document.getElementById("chat-empty").style.display = "none";
  document.getElementById("chat-thread").style.display = "flex";
  document.getElementById("chat-thread").style.flexDirection = "column";
  document.getElementById("chat-header").textContent = name;

  await refreshThread();
  loadConversations();
  loadUnreadBadge();

  if (messagesPollInterval) clearInterval(messagesPollInterval);
  messagesPollInterval = setInterval(refreshThread, 8000); // تحديث تلقائي كل 8 ثوانٍ
}

async function refreshThread() {
  if (!activeConversationUsername) return;
  try {
    const res = await fetch(`${API_BASE}/messages/with/${activeConversationUsername}`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const wrap = document.getElementById("chat-messages");
    wrap.innerHTML = data.messages.map(m => `
      <div class="chat-bubble ${m.from_me ? 'mine' : 'theirs'}">${escapeHtml(m.content)}</div>
    `).join("");
    wrap.scrollTop = wrap.scrollHeight;
    loadUnreadBadge();
  } catch (err) { console.warn("تعذّر تحديث المحادثة:", err); }
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const content = input.value.trim();
  if (!content || !activeConversationUsername) return;

  input.value = "";
  try {
    const res = await fetch(`${API_BASE}/messages/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ to_username: activeConversationUsername, content }),
    });
    if (!res.ok) throw new Error(CURRENT_LANG === "en" ? "Failed to send message" : "فشل إرسال الرسالة");
    await refreshThread();
    loadConversations();
  } catch (err) {
    alert(err.message);
  }
});

// يعالج الدخول من رابط "تواصل معي" بصفحة بروفايل شخص آخر
async function handleComposeParam() {
  const params = new URLSearchParams(window.location.search);
  const composeWith = params.get("compose");
  if (!composeWith) return;

  window.history.replaceState({}, document.title, window.location.pathname);
  showView("view-dashboard");
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  document.querySelector('[data-section="messages"]').classList.add("active");
  await loadConversations();

  try {
    const res = await fetch(`${API_BASE}/users/search?q=${encodeURIComponent(composeWith)}`, { headers: authHeaders() });
    const users = res.ok ? await res.json() : [];
    const match = users.find(u => u.username === composeWith) || { username: composeWith, name: composeWith };
    openConversation(match.username, match.name);
  } catch (err) {
    openConversation(composeWith, composeWith);
  }
}

// ---------------- Sidebar nav smooth-scroll ----------------
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    item.classList.add("active");
    const targetMap = {
      overview: "section-capabilities", capabilities: "section-capabilities",
      bridge: "section-bridge", connections: "section-connections", opportunities: "section-opportunities",
      competitions: "section-competitions", messages: "section-messages",
    };
    if (item.dataset.section === "messages") {
      loadConversations();
      loadUnreadBadge();
    }
    const target = document.getElementById(targetMap[item.dataset.section]);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
