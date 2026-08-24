// ============================================================
// analyze.js — منطق صفحة "تحليل جديد" المستقلة
// ============================================================
let CURRENT_USER = null;

(async function init() {
  CURRENT_USER = await requireAuth();
  if (!CURRENT_USER) return;
  await loadGoals();
  await prefillSavedProfile();
  await refreshGithubStatus();
  await refreshLinkedinStatus();
})();

// ---------------- Goals ----------------
async function loadGoals() {
  const select = document.getElementById("f-goal");
  select.innerHTML = `<option value="">...</option>`;
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
    } catch (e) { /* غير حرج */ }

    let optionsHtml = goals.map(g => `<option value="${g.key}">${bi(g, "name_ar", "name_en")}</option>`).join("");
    if (myCustomGoals.length > 0) {
      const label = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Your previous custom goals" : "أهدافك المخصصة السابقة";
      optionsHtml += `<optgroup label="${label}">` +
        myCustomGoals.map(g => `<option value="${g.key}">${bi(g, "name_ar", "name_en")}</option>`).join("") +
        `</optgroup>`;
    }
    select.innerHTML = optionsHtml;

    document.getElementById("custom-goal-box").style.display = aiStatus.enabled ? "block" : "none";
  } catch (err) {
    select.innerHTML = `<option value="">error</option>`;
    console.error(err);
  }
}

document.getElementById("btn-generate-goal").addEventListener("click", async () => {
  const input = document.getElementById("custom-goal-text");
  const statusEl = document.getElementById("custom-goal-status");
  const goalText = input.value.trim();
  if (!goalText) {
    statusEl.textContent = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Write your goal first" : "اكتبي هدفك أولًا";
    return;
  }

  const btn = document.getElementById("btn-generate-goal");
  btn.disabled = true;
  btn.textContent = "...";
  statusEl.textContent = "";

  try {
    const res = await fetch(`${API_BASE}/goals/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ goal_text: goalText }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "error");

    const select = document.getElementById("f-goal");
    const opt = document.createElement("option");
    opt.value = data.key;
    opt.textContent = `${bi(data, "name_ar", "name_en")} ✨`;
    opt.selected = true;
    select.appendChild(opt);

    statusEl.textContent = `✅ ${bi(data, "name_ar", "name_en")}`;
    input.value = "";
  } catch (err) {
    statusEl.textContent = "❌ " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = t("btn_analyze_goal");
  }
});

// ---------------- Prefill saved profile ----------------
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

    if (data.last_goal_key) document.getElementById("f-goal").value = data.last_goal_key;

    if (!data.skills || data.skills.length === 0) addRepeatItem("skill");
    if (!data.projects || data.projects.length === 0) addRepeatItem("project");
  } catch (err) {
    addRepeatItem("skill");
    addRepeatItem("project");
  }
}

// ---------------- Repeatable fields ----------------
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

function parseTags(value) {
  return value.split(",").map(t => t.trim().toLowerCase().replace(/\s+/g, "_")).filter(Boolean);
}

function collectProfile() {
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

  return { name: CURRENT_USER ? CURRENT_USER.name : "", skills, projects, experiences: [], certificates };
}

// ---------------- Submit ----------------
document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.textContent = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Analyzing..." : "جارِ التحليل...";

  const profile = collectProfile();
  const goalKey = document.getElementById("f-goal").value;

  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ profile, goal_key: goalKey }),
    });
    if (res.status === 401) { clearToken(); window.location.href = "index.html"; return; }
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || ("Error: " + res.status));
    }
    // بعد التحليل، ترجعين مباشرة للصفحة الرئيسية (Home) — لا تُجبرين على شاشة معيّنة
    window.location.href = "home.html";
  } catch (err) {
    alert(err.message);
    btn.disabled = false;
    btn.textContent = t("btn_analyze");
  }
});

// ---------------- GitHub / LinkedIn ----------------
document.getElementById("btn-connect-github").addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/github/connect`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "error");
    window.location.href = data.authorize_url;
  } catch (err) { alert(err.message); }
});

document.getElementById("btn-connect-linkedin").addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/linkedin/connect`, { headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "error");
    window.location.href = data.authorize_url;
  } catch (err) { alert(err.message); }
});

async function refreshGithubStatus() {
  try {
    const res = await fetch(`${API_BASE}/github/status`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const textEl = document.getElementById("github-status-text");
    const btnEl = document.getElementById("btn-connect-github");
    if (data.connected) {
      textEl.textContent = `✓ @${data.github_username}`;
      textEl.classList.add("connected");
      btnEl.textContent = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Re-sync Projects" : "إعادة مزامنة المشاريع";
      btnEl.onclick = syncGithubProjects;
    }
  } catch (err) { /* صامت */ }
}

async function syncGithubProjects(e) {
  if (e) e.preventDefault();
  const btn = document.getElementById("btn-connect-github");
  const original = btn.textContent;
  btn.textContent = "...";
  try {
    const res = await fetch(`${API_BASE}/github/sync`, { method: "POST", headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "error");
    alert(`✅ ${data.count}`);
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
      textEl.textContent = `✓ ${data.linkedin_name || ""}`;
      textEl.classList.add("connected");
      btnEl.textContent = (typeof CURRENT_LANG !== "undefined" && CURRENT_LANG === "en") ? "Verified" : "تم التأكيد";
      btnEl.disabled = true;
    }
  } catch (err) { /* صامت */ }
}

// معالجة الرجوع من GitHub/LinkedIn بعد الموافقة
(function handleOAuthRedirectParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("github_connected")) alert("✅ GitHub connected");
  else if (params.get("github_error")) alert("❌ GitHub connection failed");
  if (params.get("linkedin_connected")) alert("✅ LinkedIn verified");
  else if (params.get("linkedin_error")) alert("❌ LinkedIn connection failed");
  if (params.toString()) window.history.replaceState({}, document.title, window.location.pathname);
})();
