/** Small DOM + formatting helpers shared by the app. No dependencies. */

/** Escape text for safe HTML insertion. */
export const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);

/** Create an element from an HTML string (single root recommended). */
export const fromHTML = (html) => {
  const tpl = document.createElement("template");
  tpl.innerHTML = html.trim();
  return tpl.content.firstElementChild;
};

/** `h("div.card", {...attrs}, [...children])` — tiny hyperscript helper. */
export const h = (spec, attrs = {}, children = []) => {
  const [tagSpec, ...classSpecs] = String(spec).split(".");
  const [tag, ...tagExtras] = tagSpec.split(/\s+/);
  const el = document.createElement(tag || "div");
  // Tolerate both "div.a.b" and "div.a b" style specs.
  const classes = [...tagExtras, ...classSpecs.flatMap((c) => c.split(/\s+/))].filter(Boolean);
  if (classes.length) el.classList.add(...classes);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") el.className = [el.className, value].filter(Boolean).join(" ");
    else if (key === "html") el.innerHTML = value;
    else if (key === "text") el.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2), value);
    else if (key === "dataset") Object.assign(el.dataset, value);
    else el.setAttribute(key, value === true ? "" : value);
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return el;
};

/** Toast notification. */
export const toast = (message, kind = "ok", ms = 2600) => {
  const stack = document.getElementById("toasts");
  if (!stack) return;
  const node = h(`div.toast.toast--${kind}`, { text: message });
  stack.append(node);
  setTimeout(() => {
    node.style.transition = "opacity .3s, transform .3s";
    node.style.opacity = "0";
    node.style.transform = "translateY(6px)";
    setTimeout(() => node.remove(), 320);
  }, ms);
};

/** Minutes → "1س 20د" / "45د". */
export const humanMinutes = (minutes) => {
  const m = Number(minutes) || 0;
  if (m < 60) return `${m}د`;
  const hrs = Math.floor(m / 60);
  const rest = m % 60;
  return rest ? `${hrs}س ${rest}د` : `${hrs}س`;
};

/** Hours with one decimal, Arabic-friendly. */
export const humanHours = (hours) => `${Math.round(Number(hours) * 10) / 10} ساعة`;

export const percent = (done, total) => (total ? Math.round((done / total) * 100) : 0);

/** ISO date (YYYY-MM-DD) in local time. */
export const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export const formatDate = (iso) => {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("ar-EG", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return String(iso).slice(0, 10);
  }
};

export const debounce = (fn, wait = 220) => {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
};

/** Copy text to clipboard with a legacy fallback (file:// contexts). */
export const copyText = async (text) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch { /* fall through */ }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.append(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  } catch {
    return false;
  }
};

export const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

/** Normalise Arabic text for tolerant search (hamza, taa marbuta, diacritics). */
export const normalizeAr = (s) =>
  String(s ?? "")
    .replace(/[\u064B-\u0652\u0670]/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
