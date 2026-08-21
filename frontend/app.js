// اتجاهك — Frontend Logic
// إذا شغّلتِ الـ Backend على منفذ مختلف، عدّلي API_BASE فقط.
const API_BASE = "http://127.0.0.1:8000";

function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

document.getElementById("btn-start").addEventListener("click", () => {
  showView("view-onboarding");
  loadGoals();
});

document.getElementById("btn-restart").addEventListener("click", () => {
  showView("view-landing");
});

async function loadGoals() {
  const select = document.getElementById("f-goal");
  if (select.dataset.loaded === "1") return;
  select.innerHTML = `<option value="">جارِ التحميل...</option>`;
  try {
    const res = await fetch(`${API_BASE}/goals`);
    const goals = await res.json();
    select.innerHTML = goals.map(g => `<option value="${g.key}">${g.name_ar}</option>`).join("");
    select.dataset.loaded = "1";
  } catch (err) {
    select.innerHTML = `<option value="">تعذّر الاتصال بالخادم — تأكدي أن الـBackend يعمل</option>`;
    console.error(err);
  }
}

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

["skill", "project"].forEach(addRepeatItem);

function parseTags(value) {
  return value.split(",").map(t => t.trim().toLowerCase().replace(/\s+/g, "_")).filter(Boolean);
}

function collectProfile() {
  const name = document.getElementById("f-name").value.trim();
  const major = document.getElementById("f-major").value.trim();

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

  return { name, major, skills, projects, experiences: [], certificates };
}

document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.textContent = "جارِ التحليل...";

  const profile = collectProfile();
  const goalKey = document.getElementById("f-goal").value;

  try {
    const analyzeRes = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, goal_key: goalKey }),
    });
    if (!analyzeRes.ok) throw new Error("فشل التحليل: " + analyzeRes.status);
    const analysis = await analyzeRes.json();

    const oppRes = await fetch(`${API_BASE}/opportunities`);
    const opportunities = oppRes.ok ? await oppRes.json() : [];

    renderDashboard(profile, analysis, opportunities);
    showView("view-dashboard");
  } catch (err) {
    alert("حدث خطأ في الاتصال بالخادم. تأكدي أن الـBackend يعمل على " + API_BASE + "\n\n" + err.message);
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = "حلّل قدراتي وابنِ الجسر 🌉";
  }
});

function renderDashboard(profile, analysis, opportunities) {
  document.getElementById("user-name-badge").textContent = profile.name || "مستخدم";
  document.getElementById("greet-name").textContent = profile.name || "بك";
  document.getElementById("greet-goal").textContent = analysis.goal_name_ar;
  document.getElementById("sum-goal").textContent = analysis.goal_name_ar;
  document.getElementById("sum-gaps").textContent = analysis.gaps.length + " فجوة";

  const readiness = analysis.overall_readiness;
  document.getElementById("readiness-value").textContent = readiness + "%";
  const circumference = 326.7;
  const offset = circumference - (circumference * readiness) / 100;
  document.getElementById("ring-fg").style.strokeDashoffset = offset;

  const capWrap = document.getElementById("capabilities-list");
  capWrap.innerHTML = analysis.capabilities.length === 0
    ? `<div class="empty-hint">لا توجد مهارات كافية بعد — أضيفي مهارات أو مشاريع في ملفك.</div>`
    : analysis.capabilities.map(c => `
      <div class="bar-row">
        <div class="bar-top"><span>${prettify(c.skill)}</span><span>${c.score}%</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${c.score}%"></div></div>
        ${c.evidence.length ? `<div class="bar-evidence">✓ ${c.evidence.join(" · ")}</div>` : ""}
      </div>`).join("");

  const gapsWrap = document.getElementById("gaps-list");
  gapsWrap.innerHTML = analysis.gaps.length === 0
    ? `<div class="empty-hint">🎉 لا توجد فجوات كبيرة — أنت قريب جدًا من هدفك!</div>`
    : analysis.gaps.map(g => `
      <div class="gap-chip">
        <span>${g.label_ar} <span class="muted">(${g.current_score}% / ${g.required_score}%)</span></span>
        <span class="gap-type ${g.gap_type}">${g.gap_type === "network" ? "فجوة شبكة" : "قدرة/دليل"}</span>
      </div>`).join("");

  document.getElementById("bridge-list").innerHTML = analysis.bridge.map(step => `
    <li>
      <div class="step-num">${step.order}</div>
      <div class="step-body">
        <strong>${step.title_ar}</strong>
        <span>${step.description_ar}</span>
      </div>
    </li>`).join("");

  const connWrap = document.getElementById("connections-list");
  connWrap.innerHTML = analysis.connections.length === 0
    ? `<div class="empty-hint">أضيفي مزيدًا من المشاريع لنقترح أشخاصًا مناسبين للتواصل.</div>`
    : analysis.connections.map(c => `
      <div class="person-card">
        <div class="person-icon">${c.icon}</div>
        <div class="person-body">
          <strong>${c.name_ar}</strong>
          <span class="role">${c.role_ar}</span>
          <span class="reason">${c.reason_ar}</span>
        </div>
        <div class="match-badge">${c.match_score}%</div>
      </div>`).join("");

  const oppWrap = document.getElementById("opportunities-list");
  oppWrap.innerHTML = (!opportunities || opportunities.length === 0)
    ? `<div class="empty-hint">لا توجد فرص متاحة حاليًا.</div>`
    : opportunities.map(o => `
      <div class="opp-card">
        <div class="opp-icon">${o.icon}</div>
        <div class="opp-body">
          <strong>${o.name_ar}</strong>
          <span class="type">${o.type}</span>
          <div class="reason">${o.reason_ar}</div>
        </div>
        <div class="opp-match">${o.match_score}%</div>
      </div>`).join("");
}

function prettify(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    item.classList.add("active");
    const targetMap = {
      overview: "section-capabilities", capabilities: "section-capabilities",
      bridge: "section-bridge", connections: "section-connections", opportunities: "section-opportunities",
    };
    const target = document.getElementById(targetMap[item.dataset.section]);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});