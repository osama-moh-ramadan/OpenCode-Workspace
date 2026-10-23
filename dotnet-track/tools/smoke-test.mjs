/**
 * jsdom smoke test — boots the real app modules, drives the router, clicks a
 * quiz answer and a completion tick, and verifies persistence end to end.
 *
 *   npm i -D jsdom
 *   npm test
 */
import { JSDOM } from "jsdom";
import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
let failures = 0;
const ok = (label, cond, extra = "") => {
  if (cond) console.log(`  ✓ ${label}`);
  else { failures += 1; console.log(`  ✗ ${label} ${extra}`); }
};

const html = await readFile(path.join(ROOT, "index.html"), "utf8");
const dom = new JSDOM(html, { url: "http://127.0.0.1:8123/#/", pretendToBeVisual: true });
const { window } = dom;

const posts = [];

// Every real lesson is authored, so the "content still being written" panel is
// covered by one synthetic, un-authored lesson appended to the last module.
const FIXTURE_ID = "s99-m1-l1";
const diskCurriculum = JSON.parse(await readFile(path.join(ROOT, "content/curriculum.json"), "utf8"));
const REAL_TOTAL = diskCurriculum.stages.flatMap((st) => st.modules.flatMap((mo) => mo.lessons)).length;
const TOTAL = REAL_TOTAL + 1;   // + synthetic fixture

// --- fake same-origin fetch backed by the real files -------------------------
globalThis.fetch = async (input, init = {}) => {
  const url = new URL(String(input), "http://127.0.0.1:8123");
  if (url.pathname.startsWith("/api/progress")) {
    if ((init.method || "GET").toUpperCase() === "POST") {
      posts.push(JSON.parse(init.body));
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    return new Response(JSON.stringify({ version: 2, lessons: {}, notes: {}, bookmarks: [], activity: [] }),
      { status: 200, headers: { "Content-Type": "application/json" } });
  }
  const rel = decodeURIComponent(url.pathname).replace(/^\/+/, "") || "index.html";
  if (rel === "content/curriculum.json") {
    const cur = JSON.parse(await readFile(path.join(ROOT, rel), "utf8"));
    cur.stages[cur.stages.length - 1].modules.at(-1).lessons.push({
      id: FIXTURE_ID,
      title: "درس تجريبي بلا محتوى",
      titleEn: "Synthetic scaffolded lesson",
      summary: "تركيبة اختبار للوحة «المحتوى بيتكتب».",
      minutes: 20,
      kind: "lesson",
      objectives: ["هدف تجريبي أول", "هدف تجريبي ثانٍ", "هدف تجريبي ثالث"],
      resources: [{ label: "مصدر تجريبي", url: "https://learn.microsoft.com/dotnet/" }],
      hasContent: false,
    });
    return new Response(JSON.stringify(cur), { status: 200, headers: { "Content-Type": "application/json" } });
  }
  if (rel === `content/lessons/${FIXTURE_ID}.json`) return new Response("not found", { status: 404 });
  const full = path.join(ROOT, rel);
  if (!existsSync(full) || full.includes("..")) return new Response("not found", { status: 404 });
  const body = await readFile(full, "utf8");
  const type = full.endsWith(".json") ? "application/json" : full.endsWith(".js") ? "text/javascript" : "text/plain";
  return new Response(body, { status: 200, headers: { "Content-Type": type } });
};

// --- globals the app modules expect -----------------------------------------
globalThis.window = window;
globalThis.document = window.document;
globalThis.localStorage = window.localStorage;
globalThis.navigator = window.navigator;
globalThis.location = window.location;
globalThis.HTMLElement = window.HTMLElement;
globalThis.Blob = window.Blob;
window.scrollTo = () => {};
globalThis.scrollTo = () => {};
window.URL.createObjectURL = () => "blob:stub";
window.confirm = () => true;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

console.log("\n== boot (#/) ==");
await import(pathToFileURL(path.join(ROOT, "assets/js/app.js")).href);
await sleep(600);

const view = window.document.getElementById("view");
ok("home rendered", view.children.length > 0, `children=${view.children.length}`);
ok("hero present", !!view.querySelector(".hero"));
ok("stage cards rendered", view.querySelectorAll(".stage-card").length === 10,
  `found ${view.querySelectorAll(".stage-card").length}`);
ok(`stats show ${TOTAL} lessons`, view.textContent.includes(String(TOTAL)), view.textContent.slice(0, 120));
ok("footer stats filled", window.document.getElementById("footerStats").textContent.includes(`/${TOTAL}`),
  window.document.getElementById("footerStats").textContent);
ok("ring label initialised", window.document.getElementById("ringLabel").textContent === "0%");

console.log("\n== stage view (#/stage/s1) ==");
window.location.hash = "#/stage/s1";
await sleep(400);
ok("stage hero", view.textContent.includes("الكود المحترف والاختبار"));
ok("lesson rows", view.querySelectorAll(".lesson-row").length === 14,
  `found ${view.querySelectorAll(".lesson-row").length}`);
ok("capstone styled", !!view.querySelector(".lesson-row.is-capstone"));

console.log("\n== authored lesson (#/lesson/s1-m1-l1) ==");
window.location.hash = "#/lesson/s1-m1-l1";
await sleep(700);
ok("lesson title", view.querySelector("h1")?.textContent.includes("SOLID"));
ok("code blocks rendered", view.querySelectorAll(".code").length >= 3, `found ${view.querySelectorAll(".code").length}`);
ok("csharp highlighted", !!view.querySelector(".tok-kw") && !!view.querySelector(".tok-type"));
ok("terms rendered", view.querySelectorAll(".term").length >= 5);
ok("table rendered", !!view.querySelector("table.tbl"));
ok("quiz questions", view.querySelectorAll(".q").length === 4, `found ${view.querySelectorAll(".q").length}`);
ok("tasks rendered", view.querySelectorAll(".task").length === 2);
ok("resources links", view.querySelectorAll("ul.res a").length >= 3);
ok("objectives listed", view.querySelectorAll(".objectives li").length >= 4);
ok("no raw markdown leaked", !view.textContent.includes("**") && !view.textContent.includes("```"));
ok("aside module nav", view.querySelectorAll(".lesson-aside .chip").length >= 5);

console.log("\n== quiz interaction ==");
const radios = view.querySelectorAll(".q__opts input[type=radio]");
ok("radio count = 4 questions x 4 options", radios.length === 16, `found ${radios.length}`);
radios[1].checked = true;
radios[1].dispatchEvent(new window.Event("change", { bubbles: true }));
await sleep(80);
ok("correct option marked", view.querySelectorAll(".q .opt.is-right").length === 1);
ok("explanation shown", !view.querySelector(".q__why").hidden && view.querySelector(".q__why").textContent.length > 10);
ok("score updated", view.querySelector(".score").textContent.includes("1 / 4"), view.querySelector(".score").textContent);

console.log("\n== completion + notes + persistence ==");
const doneBtn = [...view.querySelectorAll("button.btn")].find((b) => b.textContent.includes("علّم الدرس كمكتمل"));
ok("complete button found", !!doneBtn);
doneBtn?.click();
await sleep(80);
const stored = JSON.parse(localStorage.getItem("dotnet-track.progress.v2"));
ok("localStorage lesson marked done", stored.lessons["s1-m1-l1"]?.status === "done");
ok("quiz answers persisted", Object.keys(stored.lessons["s1-m1-l1"].quiz.answers).length === 1);
ok("activity day recorded", (stored.activity || []).length === 1);
ok("ring updated to 1%", window.document.getElementById("ringLabel").textContent === "1%",
  window.document.getElementById("ringLabel").textContent);

const noteArea = view.querySelector(".notes textarea");
ok("notes area present", !!noteArea);
noteArea.value = "ملاحظة تجريبية";
noteArea.dispatchEvent(new window.Event("input", { bubbles: true }));
await sleep(1800); // 700ms input debounce + 600ms save debounce + POST
ok("note saved to server payload", posts.some((p) => p.notes?.["s1-m1-l1"]?.text === "ملاحظة تجريبية"),
  `posts=${posts.length}`);

console.log("\n== search ==");
window.location.hash = "#/search";
await sleep(300);
const input = view.querySelector("input[type=search]");
ok("search input", !!input);
input.value = "CQRS";
input.dispatchEvent(new window.Event("input", { bubbles: true }));
await sleep(350);
ok("CQRS hits", view.querySelectorAll(".hit").length >= 2, `found ${view.querySelectorAll(".hit").length}`);
input.value = "مقابله";   // intentional spelling variant (taa marbuta normalization)
input.dispatchEvent(new window.Event("input", { bubbles: true }));
await sleep(350);
ok("Arabic normalization search works", view.querySelectorAll(".hit").length >= 1,
  `found ${view.querySelectorAll(".hit").length}`);

console.log("\n== progress screen ==");
window.location.hash = "#/progress";
await sleep(400);
ok("progress screen rendered", view.textContent.includes("تقدّمي"));
ok("stage table rows = 10", view.querySelectorAll("table.tbl tbody tr").length === 10);
ok("bookmarks section", view.textContent.includes("المفضلة"));
ok("export/import/reset buttons", view.querySelectorAll("button.btn").length >= 3);

console.log("\n== theme toggle ==");
window.document.getElementById("themeBtn").click();
ok("theme switched to light", window.document.documentElement.dataset.theme === "light");
window.document.getElementById("themeBtn").click();
ok("theme back to dark", window.document.documentElement.dataset.theme === "dark");

console.log("\n== 404 route ==");
window.location.hash = "#/lesson/nope-999";
await sleep(300);
ok("not found rendered", view.textContent.includes("مش موجود"));


console.log("\n== every authored lesson renders cleanly ==");
const curriculum = JSON.parse(await readFile(path.join(ROOT, "content/curriculum.json"), "utf8"));
const authored = [];
for (const stage of curriculum.stages)
  for (const mod of stage.modules)
    for (const lesson of mod.lessons)
      if (lesson.hasContent) authored.push(lesson);

const lessonFiles = (await readdir(path.join(ROOT, "content/lessons"))).filter((f) => f.endsWith(".json"));
ok("authored lessons match files on disk", authored.length === lessonFiles.length,
   `curriculum=${authored.length} files=${lessonFiles.length}`);
ok("at least stage 1 fully authored", authored.length >= 14, `found ${authored.length}`);

for (const lesson of authored) {
  window.location.hash = `#/lesson/${lesson.id}`;
  await sleep(260);

  const src = JSON.parse(await readFile(path.join(ROOT, `content/lessons/${lesson.id}.json`), "utf8"));
  const codeBlocks = src.blocks.filter((b) => b.type === "code").length;
  const fenced = (JSON.stringify(src.blocks).match(/```/g) || []).length / 2;
  const quizQs = src.blocks.filter((b) => b.type === "quiz").flatMap((b) => b.questions || []);
  const expectedOptions = quizQs.reduce((n, q) => n + (q.options || []).length, 0);

  // Prose only: code blocks legitimately contain ** (glob patterns like TestResults/**/coverage.xml)
  const prose = view.cloneNode(true);
  prose.querySelectorAll(".code").forEach((e) => e.remove());
  const text = prose.textContent;
  const checks = {
    rendered: view.querySelectorAll(".block").length >= 3,
    noRawMarkdown: !text.includes("**") && !text.includes("```") && !text.includes("\u0000"),
    code: view.querySelectorAll(".code").length >= codeBlocks + Math.floor(fenced),
    highlighted: view.querySelectorAll(".code .tok-kw, .code .tok-type, .code .tok-str, .code .tok-prop").length > 0,
    options: view.querySelectorAll(".q__opts input[type=radio]").length === expectedOptions,
    tasks: view.querySelectorAll(".task").length ===
      src.blocks.filter((b) => b.type === "tasks").flatMap((b) => b.items || []).length,
    resources: view.querySelectorAll("ul.res a").length > 0,
  };
  const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k);
  const leakAt = text.search(/\*\*|```|\u0000/);
  const leak = leakAt < 0 ? "" : ` → "${text.slice(Math.max(0, leakAt - 70), leakAt + 70).replace(/\s+/g, " ")}"`;
  ok(`${lesson.id}`, failed.length === 0, failed.join(",") + leak);
}

console.log("\n== fenced code inside callout markdown ==");
window.location.hash = "#/lesson/s1-m2-l5";
await sleep(300);
ok("callout contains a rendered code block", !!view.querySelector(".callout .code"));
ok("yaml block highlighted", view.querySelectorAll(".tok-prop, .tok-kw").length > 0);

console.log("\n== stage 1 fully authored ==");
window.location.hash = "#/stage/s1";
await sleep(300);
const readyChips = [...view.querySelectorAll(".lesson-row")].filter((r) => r.textContent.includes("محتوى جاهز"));
ok("all 14 stage-1 rows show 'محتوى جاهز'", readyChips.length === 14, `found ${readyChips.length}`);

console.log("\n== scaffolded lesson (no content yet) ==");
// the curriculum is fully authored; simulate a lesson whose content isn't written
// yet by 404-ing its JSON. s1-m1-l2 is untouched by earlier checks (no cache).
const pendingId = FIXTURE_ID;
const realPending = diskCurriculum.stages
  .flatMap((st) => st.modules.flatMap((mo) => mo.lessons)).filter((l) => !l.hasContent).length;
ok("every real lesson is authored", realPending === 0, `still scaffolded: ${realPending}`);
window.location.hash = `#/lesson/${pendingId}`;
await sleep(500);
ok("pending panel shown", !!view.querySelector(".pending"));
ok("objectives still rendered", view.querySelectorAll(".objectives li").length >= 3);
ok("resources for self-study", view.querySelectorAll("ul.res a").length >= 1);
ok("complete button works on scaffolded lesson",
  !![...view.querySelectorAll("button.btn")].find((b) => b.textContent.includes("مكتمل")));
ok("scaffold fixture does not leak into real counts", TOTAL === REAL_TOTAL + 1);

console.log(failures === 0 ? "\nALL CHECKS PASSED ✅" : `\n${failures} CHECK(S) FAILED ❌`);
process.exit(failures === 0 ? 0 : 1);
