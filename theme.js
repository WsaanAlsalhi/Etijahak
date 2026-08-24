// ============================================================
// theme.js — الوضع الليلي/النهاري (مشترك بكل الصفحات)
// ============================================================
const THEME_KEY = "etijahak_theme";

function getSavedTheme() {
  return localStorage.getItem(THEME_KEY) || "light";
}

function applyTheme(theme) {
  document.body.classList.toggle("dark-mode", theme === "dark");
  localStorage.setItem(THEME_KEY, theme);
  document.querySelectorAll(".theme-toggle").forEach(btn => {
    btn.textContent = theme === "dark" ? "☀️" : "🌙";
  });
}

function toggleTheme() {
  applyTheme(getSavedTheme() === "dark" ? "light" : "dark");
}

// تُستدعى بعد أي إضافة ديناميكية لزر .theme-toggle (مثل renderShell بصفحات الداشبورد)
function wireThemeToggle() {
  document.querySelectorAll(".theme-toggle").forEach(btn => {
    if (btn.dataset.wired) return;
    btn.dataset.wired = "1";
    btn.addEventListener("click", toggleTheme);
  });
  applyTheme(getSavedTheme());
}
window.wireThemeToggle = wireThemeToggle;

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(getSavedTheme());
  wireThemeToggle();
});
