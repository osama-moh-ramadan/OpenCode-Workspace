/** App bootstrap + hash router. */
import { loadCurriculum, flatLessons, allLessonIds, meta } from "./curriculum.js";
import { initStore, subscribe, stats, setTheme, getState } from "./store.js";
import { renderHome, renderCurriculum, renderStage, renderLesson, renderSearch, renderProgress, notFound } from "./views.js";
import { h, percent, toast } from "./util.js";

const view = document.getElementById("view");
const ringFg = document.getElementById("ringFg");
const ringLabel = document.getElementById("ringLabel");
const RING_LEN = 97.4; // 2 * PI * r(15.5)

/* ------------------------------------------------------------------- chrome */

const applyTheme = (theme) => {
  document.documentElement.dataset.theme = theme === "light" ? "light" : "dark";
};

const updateRing = () => {
  const s = stats(allLessonIds());
  const p = percent(s.done, s.total);
  if (ringFg) ringFg.style.strokeDashoffset = String(RING_LEN - (RING_LEN * p) / 100);
  if (ringLabel) ringLabel.textContent = `${p}%`;
  const footerStats = document.getElementById("footerStats");
  if (footerStats) footerStats.textContent = `${s.done}/${s.total} درس مكتمل`;
  const footerTarget = document.getElementById("footerTarget");
  if (footerTarget && meta().target) footerTarget.textContent = meta().target;
};

const markActiveNav = (route) => {
  document.querySelectorAll(".nav a").forEach((a) => {
    a.classList.toggle("is-active", a.dataset.route === route);
  });
};

const setLoading = () => {
  view.replaceChildren(h("div.stack", { style: "gap:12px" }, [
    h("div.skeleton", { style: "height:120px" }),
    h("div.skeleton", { style: "height:18px;width:60%" }),
    h("div.skeleton", { style: "height:18px;width:40%" }),
    h("div.grid.grid--2.mt-4", {}, [h("div.skeleton", { style: "height:150px" }), h("div.skeleton", { style: "height:150px" })]),
  ]));
};

/* ------------------------------------------------------------------- router */

const parseHash = () => {
  const raw = (location.hash || "#/").replace(/^#/, "");
  const [pathPart, queryPart] = raw.split("?");
  const parts = pathPart.split("/").filter(Boolean);
  const query = new URLSearchParams(queryPart || "");
  return { parts, query, raw };
};

const navigate = async () => {
  const { parts, query } = parseHash();
  const [head, param] = parts;

  markActiveNav(head || "home");
  setLoading();

  try {
    let node;
    switch (head) {
      case undefined:
      case "":
        markActiveNav("home");
        node = renderHome();
        break;
      case "curriculum":
        node = renderCurriculum();
        break;
      case "stage":
        node = renderStage(param || "");
        break;
      case "lesson":
        node = await renderLesson(param || "");
        break;
      case "search":
        markActiveNav("search");
        node = renderSearch(query.get("q") || decodeURIComponent(param || ""));
        break;
      case "progress":
        node = renderProgress();
        break;
      default:
        node = notFound(`المسار «${head}» غير معروف`);
    }
    view.replaceChildren(node);
    updateRing();

    // Keep stage anchors (#/stage/s3#s3-m2) usable.
    const anchor = location.hash.split("#")[2];
    if (anchor) {
      const el = document.getElementById(anchor);
      if (el) { el.scrollIntoView({ block: "start" }); return; }
    }
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  } catch (err) {
    console.error(err);
    view.replaceChildren(h("div.empty", {}, [
      h("h2", { text: "حصل خطأ" }),
      h("p.muted", { text: String(err?.message || err) }),
      h("p.dim.tiny", { text: "تأكد إنك فاتح التطبيق من خلال سيرفر (python3 server.py) مش من ملف مباشرة، لو المنهج مش ظاهر." }),
      h("a.btn.btn--primary", { href: "#/", text: "حاول تاني" }),
    ]));
  }
};

/* ------------------------------------------------------------------ boot */

const boot = async () => {
  applyTheme(getState().settings?.theme || "dark");

  document.getElementById("themeBtn")?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
    setTheme(next);
  });

  subscribe(updateRing);

  try {
    await initStore();
    applyTheme(getState().settings?.theme || "dark");
    await loadCurriculum();
  } catch (err) {
    console.error(err);
    view.replaceChildren(h("div.empty", {}, [
      h("h2", { text: "تعذّر تحميل المنهج" }),
      h("p.muted", { text: String(err?.message || err) }),
      h("p.dim.tiny", { text: "لازم التطبيق يشتغل من سيرفر: python3 server.py (أو node server.mjs) ثم افتح العنوان اللي يطبعه." }),
    ]));
    return;
  }

  if (!flatLessons().length) {
    toast("المنهج فاضي — شغّل python3 tools/build.py", "warn", 5000);
  }

  window.addEventListener("hashchange", navigate);
  await navigate();

  const s = stats(allLessonIds());
  console.info(`[dotnet-track] ${flatLessons().length} درس · ${s.done} مكتمل (${s.pct}%)`);
};

void boot();
