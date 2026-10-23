/** Renders authored lesson content blocks and wires their interactions. */
import { md, mdInline } from "./md.js";
import { highlight, langLabel } from "./highlight.js";
import { h, copyText, toast } from "./util.js";
import { lessonState, setQuizResult, setTaskDone } from "./store.js";

/* --------------------------------------------------------------- code block */

export const codeBlock = ({ lang = "csharp", title = "", filename = "", code = "" }) => {
  const wrap = h("div.code");
  const head = h("div.code__head");
  const left = h("div.code__title", {}, [
    filename ? h("span.mono", { text: filename }) : null,
    title ? h("span", { html: mdInline(title) }) : null,
    h("span.code__lang", { text: langLabel(lang) }),
  ]);
  const copy = h("button.code__copy", { type: "button", text: "نسخ" });
  copy.addEventListener("click", async () => {
    const ok = await copyText(code);
    copy.textContent = ok ? "تم النسخ ✓" : "تعذّر النسخ";
    setTimeout(() => { copy.textContent = "نسخ"; }, 1600);
  });
  head.append(left, copy);
  const pre = h("pre", { html: `<code>${highlight(code, lang)}</code>` });
  wrap.append(head, pre);
  return wrap;
};

/* ------------------------------------------------------------------ callout */

const CALLOUT_ICON = { tip: "✦", warn: "!", note: "i", goal: "◎", danger: "×" };

const callout = ({ kind = "note", title = "", md: body = "" }) =>
  h(`div.callout.callout--${kind}`, {}, [
    h("div.callout__ico", { text: CALLOUT_ICON[kind] || "i" }),
    h("div.callout__body", {
      html: (title ? `<div class="callout__title">${mdInline(title)}</div>` : "") + md(body),
    }),
  ]);

/* -------------------------------------------------------------------- table */

const table = ({ head = [], rows = [], caption = "" }) => {
  const wrap = h("div", { style: "overflow-x:auto" });
  const tbl = h("table.tbl");
  if (head.length) {
    tbl.append(h("thead", {}, h("tr", {}, head.map((c) => h("th", { html: md(c) })))));
  }
  tbl.append(h("tbody", {}, rows.map((r) => h("tr", {}, (Array.isArray(r) ? r : [r]).map((c) => h("td", { html: md(String(c)) }))))));
  wrap.append(tbl);
  if (caption) wrap.append(h("p.dim.tiny.center", { html: mdInline(caption) }));
  return wrap;
};

/* -------------------------------------------------------------------- steps */

const steps = ({ title = "", items = [] }) => {
  const wrap = h("div");
  if (title) wrap.append(h("h3", { html: mdInline(title) }));
  const list = h("ol.steps");
  for (const item of items) {
    const li = h("li");
    if (item.title) li.append(h("strong", { html: mdInline(item.title) }));
    if (item.md) li.append(h("div", { html: md(item.md) }));
    if (item.code) li.append(codeBlock(item.code));
    list.append(li);
  }
  wrap.append(list);
  return wrap;
};

/* ------------------------------------------------------------------- terms */

const terms = ({ title = "", items = [] }) => {
  const wrap = h("div");
  if (title) wrap.append(h("h3", { html: mdInline(title) }));
  const grid = h("div.terms");
  for (const t of items) grid.append(h("div.term", {}, [h("b", { html: mdInline(t.term) }), h("span", { html: md(t.def) })]));
  wrap.append(grid);
  return wrap;
};

/* --------------------------------------------------------------- resources */

export const resources = ({ title = "مصادر", items = [] }) => {
  if (!items?.length) return null;
  const wrap = h("div");
  wrap.append(h("h3", { html: mdInline(title) }));
  const ul = h("ul.res");
  for (const r of items) {
    const a = h("a", { href: r.url, target: "_blank", rel: "noopener noreferrer" }, [
      h("span", { text: r.label }),
      h("span.ext.mono", { text: new URL(r.url, location.href).hostname.replace(/^www\./, "") }),
    ]);
    ul.append(h("li", {}, a));
  }
  wrap.append(ul);
  return wrap;
};

/* ------------------------------------------------------------------ quiz */

const quiz = (block, ctx) => {
  const questions = block.questions || [];
  const wrap = h("div.block.quiz");
  if (block.title) wrap.append(h("h2", { html: mdInline(block.title) }));
  if (block.intro) wrap.append(h("div.prose", { html: md(block.intro) }));

  const saved = lessonState(ctx.lessonId)?.quiz || { answers: {} };
  const bar = h("div.quiz__bar");
  const scoreEl = h("span.score");
  const retry = h("button.btn.btn--ghost.btn--sm", { type: "button", text: "إعادة المحاولة" });
  bar.append(scoreEl, retry);
  wrap.append(bar);

  const state = { answers: { ...(saved.answers || {}) } };

  const recompute = () => {
    let score = 0;
    let answered = 0;
    questions.forEach((q, i) => {
      const pick = state.answers[i];
      if (pick === undefined || pick === null) return;
      answered += 1;
      if (Number(pick) === Number(q.answer)) score += 1;
    });
    const total = questions.length;
    scoreEl.textContent = answered ? `النتيجة: ${score} / ${total}` : `الأسئلة: ${total}`;
    scoreEl.style.color = answered === total ? (score === total ? "var(--ok)" : score >= total / 2 ? "var(--warn)" : "var(--danger)") : "";
    setQuizResult(ctx.lessonId, { answers: state.answers, score, total });
    return { score, answered, total };
  };

  questions.forEach((q, qi) => {
    const card = h("div.q");
    card.append(h("div.q__head", {}, [
      h("div.q__n", { text: String(qi + 1) }),
      h("div.q__text", { html: md(q.q) }),
    ]));

    const opts = h("div.q__opts");
    const why = h("div.q__why", { hidden: true });
    const name = `q-${ctx.lessonId}-${qi}`;

    const applyState = () => {
      const pick = state.answers[qi];
      [...opts.children].forEach((label, oi) => {
        const input = label.querySelector("input");
        label.classList.remove("is-right", "is-wrong", "is-locked");
        input.checked = Number(pick) === oi;
        if (pick === undefined || pick === null) return;
        label.classList.add("is-locked");
        if (oi === Number(q.answer)) label.classList.add("is-right");
        else if (oi === Number(pick)) label.classList.add("is-wrong");
      });
      if (pick !== undefined && pick !== null && q.explain) {
        why.hidden = false;
        why.innerHTML = `<span class="tag">${Number(pick) === Number(q.answer) ? "إجابة صحيحة — " : "الإجابة الصحيحة هي " + (Number(q.answer) + 1) + " — "}</span>${md(q.explain)}`;
      } else {
        why.hidden = true;
      }
    };

    (q.options || []).forEach((optionText, oi) => {
      const input = h("input", { type: "radio", name, value: String(oi) });
      const label = h("label.opt", {}, [input, h("span", { html: md(optionText) })]);
      input.addEventListener("change", () => {
        state.answers[qi] = oi;
        applyState();
        recompute();
      });
      opts.append(label);
    });

    card.append(opts, why);
    wrap.append(card);
    applyState();
  });

  retry.addEventListener("click", () => {
    state.answers = {};
    wrap.querySelectorAll(".opt input").forEach((input) => { input.checked = false; });
    wrap.querySelectorAll(".opt").forEach((label) => label.classList.remove("is-right", "is-wrong", "is-locked"));
    wrap.querySelectorAll(".q__why").forEach((node) => { node.hidden = true; });
    recompute();
    toast("تم مسح الإجابات — جرّب تاني", "warn");
  });

  recompute();
  return wrap;
};

/* ------------------------------------------------------------------ tasks */

const tasks = (block, ctx) => {
  const items = block.items || [];
  const wrap = h("div.block");
  if (block.title) wrap.append(h("h2", { html: mdInline(block.title) }));
  if (block.intro) wrap.append(h("div.prose", { html: md(block.intro) }));

  const saved = lessonState(ctx.lessonId)?.tasks || {};

  items.forEach((task, i) => {
    const key = task.id || `t${i + 1}`;
    const node = h("div.task");
    const tick = h("button.tick", {
      type: "button",
      title: "علّم المهمة كمنجزة",
      "aria-pressed": saved[key] ? "true" : "false",
      html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    });
    const head = h("div.task__head", {}, [
      tick,
      h("div", { html: `<strong>${mdInline(task.title || `مهمة ${i + 1}`)}</strong>` + (task.md ? md(task.md) : "") }),
    ]);
    node.append(head);

    const body = h("div.task__body");
    if (task.criteria?.length) {
      body.append(h("ul.criteria", {}, task.criteria.map((c) => h("li", { html: md(c) }))));
    }
    if (task.hint) {
      const d = h("details.reveal", {}, [h("summary", { text: "تلميح" }), h("div.prose", { html: md(task.hint) })]);
      body.append(d);
    }
    if (task.solution) {
      const d = h("details.reveal", {}, [h("summary", { text: "الحل المرجعي" })]);
      const inner = h("div");
      if (typeof task.solution === "string") inner.append(h("div.prose", { html: md(task.solution) }));
      else if (Array.isArray(task.solution)) task.solution.forEach((part) => inner.append(renderBlock(part, ctx)));
      else inner.append(renderBlock(task.solution, ctx));
      d.append(inner);
      body.append(d);
    }
    if (task.resources?.length) body.append(resources({ title: "مصادر المهمة", items: task.resources }));
    node.append(body);

    if (saved[key]) node.classList.add("is-done");
    tick.addEventListener("click", () => {
      const next = tick.getAttribute("aria-pressed") !== "true";
      tick.setAttribute("aria-pressed", next ? "true" : "false");
      node.classList.toggle("is-done", next);
      setTaskDone(ctx.lessonId, key, next);
      if (next) toast("تم إنجاز المهمة 👌");
    });

    wrap.append(node);
  });
  return wrap;
};

/* ------------------------------------------------------------- checkpoints */

const checkpoints = ({ title = "نقاط تحقق — لو معرفتهاش ارجع للشرح", items = [] }) => {
  const wrap = h("div.block");
  wrap.append(h("h3", { html: mdInline(title) }));
  wrap.append(h("ul.objectives", {}, items.map((c) => h("li", { html: md(c) }))));
  return wrap;
};

/* ------------------------------------------------------------ block router */

export const renderBlock = (block, ctx) => {
  if (!block) return null;
  switch (block.type) {
    case "text":
    case "md":
    case "markdown":
      return h("div.block.prose", { html: md(block.md || block.text || "") });
    case "heading":
      return h(`h${block.level === 3 ? 3 : 2}`, { html: mdInline(block.text || "") });
    case "code":
      return h("div.block", {}, codeBlock(block));
    case "callout":
      return h("div.block", {}, callout(block));
    case "table":
      return h("div.block", {}, table(block));
    case "steps":
      return h("div.block", {}, steps(block));
    case "terms":
      return h("div.block", {}, terms(block));
    case "quiz":
      return quiz(block, ctx);
    case "tasks":
      return tasks(block, ctx);
    case "checkpoints":
      return h("div.block", {}, checkpoints(block));
    case "resources":
      return h("div.block", {}, resources(block));
    default: {
      const fallback = h("div.block.prose", { html: md(block.md || JSON.stringify(block, null, 2)) });
      console.warn("unknown block type:", block.type);
      return fallback;
    }
  }
};

export const renderBlocks = (blocks, ctx) => {
  const frag = document.createDocumentFragment();
  for (const block of blocks || []) {
    const node = renderBlock(block, ctx);
    if (node) frag.append(node);
  }
  return frag;
};
