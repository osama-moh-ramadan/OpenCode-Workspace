/** Screen renderers: home, curriculum, stage, lesson, search, progress. */
import {
  meta, stages, getStage, getModule, getLesson, flatLessons, allLessonIds,
  neighbors, stageLessons, loadLessonContent, search, totalsFor,
} from "./curriculum.js";
import {
  isDone, setLessonDone, setNote, toggleBookmark, lessonState, stats, streak,
  nextLessonId, exportState, importState, resetAll, isServerMode, getState,
} from "./store.js";
import { renderBlocks, resources } from "./blocks.js";
import { esc, h, humanMinutes, humanHours, percent, toast, formatDate, debounce, normalizeAr } from "./util.js";

/* ------------------------------------------------------------------ shared */

const TICK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';

const KIND_LABEL = { lesson: "درس", lab: "معمل", quiz: "اختبار", capstone: "مشروع المرحلة" };

const tickButton = (lesson) => {
  const btn = h("button.tick", {
    type: "button",
    title: isDone(lesson.id) ? "إلغاء الإنجاز" : "علّم كمكتمل",
    "aria-pressed": isDone(lesson.id) ? "true" : "false",
    "aria-label": `إنجاز: ${lesson.title}`,
    html: TICK_SVG,
  });
  btn.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const next = btn.getAttribute("aria-pressed") !== "true";
    setLessonDone(lesson.id, next, lesson.minutes);
    btn.setAttribute("aria-pressed", next ? "true" : "false");
    btn.title = next ? "إلغاء الإنجاز" : "علّم كمكتمل";
    const row = btn.closest(".lesson-row");
    if (row) row.classList.toggle("is-done", next);
    toast(next ? `أكملت: ${lesson.title}` : "اتلغى تعليم الإنجاز", next ? "ok" : "warn");
  });
  return btn;
};

const progressBar = (done, total, extraClass = "") =>
  h("div.bar", { class: extraClass || null }, h("i", { style: `width:${percent(done, total)}%` }));

const lessonRow = (lesson, { showStage = false, showObjectives = false } = {}) => {
  const row = h(`div.lesson-row${isDone(lesson.id) ? " is-done" : ""}${lesson.kind === "capstone" ? " is-capstone" : ""}`);
  row.append(tickButton(lesson));
  row.append(h("span.kind-dot", { dataset: { kind: lesson.kind }, title: KIND_LABEL[lesson.kind] || lesson.kind }));

  const link = h("a.title", { href: `#/lesson/${lesson.id}` }, [
    h("span", { text: lesson.title }),
    showStage ? h("span.dim.tiny", { text: ` · ${lesson.stage.title}` }) : null,
  ]);
  row.append(h("div", { style: "flex:1;min-width:0" }, [
    link,
    showObjectives ? h("div.dim.tiny", { text: lesson.summary }) : null,
  ]));

  const meta = h("div.lesson-row__meta", {}, [
    lesson.hasContent
      ? h("span.chip.chip--accent", { text: "محتوى جاهز" })
      : h("span.chip", { text: "قريبًا" }),
    lesson.kind !== "lesson" ? h(`span.chip.chip--kind-${lesson.kind}`, { text: KIND_LABEL[lesson.kind] }) : null,
    h("span.dim.tiny.mono", { text: humanMinutes(lesson.minutes) }),
  ]);
  row.append(meta);
  return row;
};

const stageCard = (stage) => {
  const lessons = stageLessons(stage.id);
  const done = lessons.filter((l) => isDone(l.id)).length;
  const card = h("article.card.card--hover.stage-card");
  card.append(
    h("div.stage-card__head", {}, [
      h("div.stage-num", { text: String(stage.index).padStart(2, "0") }),
      h("div", {}, [
        h("h3", {}, [
          h("a", { href: `#/stage/${stage.id}`, text: stage.title }),
        ]),
        h("span.stage-card__en", { text: stage.titleEn }),
      ]),
    ]),
    h("p.stage-card__sum", { text: stage.summary }),
    h("div.row", { style: "gap:6px" }, [
      h("span.chip", { text: stage.level }),
      h("span.chip", { text: stage.weeks }),
      h("span.chip", { text: `${lessons.length} درس` }),
      h("span.chip", { text: humanHours(stage.hours) }),
      done ? h("span.chip.chip--done", { text: `${done} مكتمل` }) : null,
    ]),
    h("div.stage-card__foot", {}, [
      progressBar(done, lessons.length),
      h("span.pct", { text: `${percent(done, lessons.length)}%` }),
      h("a.btn.btn--ghost.btn--sm", { href: `#/stage/${stage.id}`, text: done === lessons.length ? "مراجعة" : "ابدأ" }),
    ]),
  );
  return card;
};

const sectionTitle = (title, sub) =>
  h("div.spread", { style: "align-items:flex-end;margin-bottom:16px" }, [
    h("div", {}, [h("h2", { text: title, style: "margin:0" }), sub ? h("p.dim", { text: sub, style: "margin:0" }) : null]),
  ]);

/* -------------------------------------------------------------------- home */

export const renderHome = () => {
  const root = h("div");
  const m = meta();
  const ids = allLessonIds();
  const s = stats(ids);
  const st = streak();
  const lessons = flatLessons();
  const next = nextLessonId(ids);
  const nextLesson = next ? getLesson(next) : null;

  root.append(h("section.hero", {}, [
    h("span.hero__eyebrow", {}, [
      h("span", { text: "● " }),
      h("span.mono", { text: m.target || "" }),
    ]),
    h("h1", { text: m.title || "مسار .NET" }),
    h("p.hero__sub", { text: m.tagline || "" }),
    h("div.hero__actions", {}, [
      nextLesson
        ? h("a.btn.btn--primary", { href: `#/lesson/${nextLesson.id}` }, [
            h("span", { text: s.done ? "كمّل من حيث وقفت" : "ابدأ المسار" }),
            h("span.chip", { text: humanMinutes(nextLesson.minutes), style: "background:rgba(0,0,0,.15);color:inherit;border:0" }),
          ])
        : h("a.btn.btn--primary", { href: "#/curriculum", text: "تصفح المراحل" }),
      h("a.btn.btn--ghost", { href: "#/curriculum", text: "كل المراحل" }),
      h("a.btn.btn--quiet", { href: "#/progress", text: "تقدّمي وإحصائياتي" }),
    ]),
    h("div.hero__meta", {}, [
      h("span", {}, [h("b", { text: `${m.stats?.stages ?? stages().length}` }), " مراحل"]),
      h("span", {}, [h("b", { text: `${m.stats?.modules ?? 0}` }), " موديول"]),
      h("span", {}, [h("b", { text: `${s.total}` }), " درس ومهمة"]),
      h("span", {}, [h("b", { text: humanHours((m.stats?.minutes || 0) / 60) }), " محتوى"]),
      h("span", {}, [h("b", { text: `${m.stats?.capstones ?? 0}` }), " مشروع مرحلة"]),
    ]),
  ]));

  root.append(h("div.grid.grid--4.mt-5", {}, [
    h("div.card.card--tight", {}, [
      h("div.stat", {}, [h("span.stat__v", { text: `${s.pct}%` }), h("span.stat__l", { text: `الإنجاز الكلي (${s.done}/${s.total})` })]),
      progressBar(s.done, s.total, "mt-2"),
    ]),
    h("div.card.card--tight", {}, [
      h("div.stat", {}, [h("span.stat__v", { text: humanHours(s.minutesDone / 60) }), h("span.stat__l", { text: "وقت تعلّم مكتمل" })]),
      h("p.dim.tiny", { text: `المتبقي تقريبًا ${humanHours(((m.stats?.minutes || 0) - s.minutesDone) / 60)}`, style: "margin:6px 0 0" }),
    ]),
    h("div.card.card--tight", {}, [
      h("div.stat", {}, [h("span.stat__v", { text: `${st.current}` }), h("span.stat__l", { text: "أيام متتالية (streak)" })]),
      h("p.dim.tiny", { text: `أطول سلسلة: ${st.longest} يوم`, style: "margin:6px 0 0" }),
    ]),
    h("div.card.card--tight", {}, [
      h("div.stat", {}, [h("span.stat__v", { text: `${m.stats?.authoredLessons ?? lessons.filter((l) => l.hasContent).length}` }), h("span.stat__l", { text: "درس بمحتوى كامل" })]),
      h("p.dim.tiny", { text: "باقي الدروس مسجّلة بالأهداف والمصادر والمحتوى بيتكتب على دفعات", style: "margin:6px 0 0" }),
    ]),
  ]));

  if (!isServerMode()) {
    root.append(h("div.callout.callout--note.mt-4", {}, [
      h("div.callout__ico", { text: "i" }),
      h("div.callout__body", {
        html: `<div class="callout__title">التقدّم محفوظ في المتصفح</div>
        <p class="muted" style="margin:0">شغّال الآن من غير سيرفر محلي، فالإنجاز بيتحفظ في <code>localStorage</code>.
        لو عايز نسخة ملف على جهازك (<code>progress.json</code>) شغّل <code>python3 server.py</code> أو <code>node server.mjs</code> وافتح التطبيق من نفس العنوان.</p>`,
      }),
    ]));
  }

  root.append(h("div.mt-6"));
  root.append(sectionTitle("مراحل المسار", "من بعد EF Core لحد ما تمضي عقد"));
  root.append(h("div.grid.grid--2", {}, stages().map(stageCard)));

  root.append(h("div.card.mt-6", {}, [
    h("h2", { text: "المسار مبني على إيه؟" }),
    h("p.muted", { text: `نقطة البداية المفترضة: ${m.entryPoint || ""}` }),
    h("ul.objectives", {}, (m.prerequisites || []).map((p) => h("li", { text: p }))),
    m.sources?.length ? resources({ title: "المصادر اللي اتبنى عليها الرودماب", items: m.sources }) : null,
  ]));

  return root;
};

/* -------------------------------------------------------------- curriculum */

export const renderCurriculum = () => {
  const root = h("div");
  root.append(h("h1", { text: "المراحل العشرة" }));
  root.append(h("p.muted", { text: "كل مرحلة فيها موديولات، وكل موديول فيه دروس ومهام، وفي الآخر مشروع مرحلة (Capstone) بمعايير قبول." }));

  for (const stage of stages()) {
    const lessons = stageLessons(stage.id);
    const done = lessons.filter((l) => isDone(l.id)).length;
    const card = h("section.card.mt-5");
    card.append(h("div.spread", {}, [
      h("div.row", {}, [
        h("div.stage-num", { text: String(stage.index).padStart(2, "0") }),
        h("div", {}, [
          h("h2", { style: "margin:0" }, h("a", { href: `#/stage/${stage.id}`, text: stage.title })),
          h("span.stage-card__en", { text: stage.titleEn }),
        ]),
      ]),
      h("div.row", {}, [
        h("span.chip", { text: `${done}/${lessons.length}` }),
        h("span.chip", { text: humanHours(stage.hours) }),
        h("span.chip", { text: stage.weeks }),
      ]),
    ]));
    card.append(progressBar(done, lessons.length, "mt-4"));
    card.append(h("p.muted.mt-4", { text: stage.summary }));

    for (const mod of stage.modules) {
      const mLessons = lessons.filter((l) => l.module.id === mod.id);
      const mDone = mLessons.filter((l) => isDone(l.id)).length;
      const box = h("div.module.mt-5");
      box.append(h("div.module__head", {}, [
        h("h3", { text: mod.title }),
        h("span.stage-card__en", { text: mod.titleEn }),
        h("span.chip", { text: `${mDone}/${mLessons.length}` }),
        h("span.dim.tiny.mono", { text: humanMinutes(mod.minutes) }),
      ]));
      box.append(h("p.dim.tiny", { text: mod.summary }));
      for (const lesson of mLessons) box.append(lessonRow(lesson));
      card.append(box);
    }
    root.append(card);
  }
  return root;
};

/* ------------------------------------------------------------------- stage */

export const renderStage = (stageId) => {
  const stage = getStage(stageId);
  if (!stage) return notFound(`المرحلة ${stageId} مش موجودة`);

  const lessons = stageLessons(stage.id);
  const done = lessons.filter((l) => isDone(l.id)).length;
  const root = h("div");

  root.append(h("nav.crumbs", {}, [
    h("a", { href: "#/", text: "الرئيسية" }),
    h("span.sep", { text: "›" }),
    h("a", { href: "#/curriculum", text: "المراحل" }),
    h("span.sep", { text: "›" }),
    h("span", { text: stage.title }),
  ]));

  root.append(h("section.hero", {}, [
    h("span.hero__eyebrow", {}, [h("span", { text: `المرحلة ${String(stage.index).padStart(2, "0")} · ${stage.level} · ${stage.weeks}` })]),
    h("h1", { text: stage.title }),
    h("span.lesson-head__en", { text: stage.titleEn }),
    h("p.hero__sub.mt-2", { text: stage.summary }),
    h("div.callout.callout--goal.mt-4", { style: "margin-bottom:0" }, [
      h("div.callout__ico", { text: "◎" }),
      h("div.callout__body", {}, [
        h("div.callout__title", { text: "لو خلصت المرحلة دي هتقدر:" }),
        h("p.muted", { text: stage.outcome, style: "margin:0" }),
      ]),
    ]),
    h("div.hero__actions", {}, [
      (() => {
        const nxt = lessons.find((l) => !isDone(l.id)) || lessons[0];
        return nxt ? h("a.btn.btn--primary", { href: `#/lesson/${nxt.id}`, text: nxt.title }) : null;
      })(),
      h("span.chip.chip--done", { text: `${done} / ${lessons.length} مكتمل` }),
      h("span.chip", { text: humanHours(stage.hours) }),
    ]),
    progressBar(done, lessons.length, "mt-4"),
  ]));

  for (const mod of stage.modules) {
    const mLessons = lessons.filter((l) => l.module.id === mod.id);
    const mDone = mLessons.filter((l) => isDone(l.id)).length;
    const box = h("section.card.mt-5");
    box.append(h("div.spread", {}, [
      h("div", {}, [
        h("h2", { style: "margin:0", text: mod.title }),
        h("span.stage-card__en", { text: mod.titleEn }),
      ]),
      h("div.row", {}, [h("span.chip", { text: `${mDone}/${mLessons.length}` }), h("span.chip", { text: humanMinutes(mod.minutes) })]),
    ]));
    box.append(h("p.muted.mt-2", { text: mod.summary }));
    for (const lesson of mLessons) box.append(lessonRow(lesson, { showObjectives: true }));
    root.append(box);
  }

  const nextStage = stages().find((s) => s.index === stage.index + 1);
  root.append(h("div.pager", {}, [
    stage.index > 1
      ? h("a.btn.btn--ghost", { href: `#/stage/s${stage.index - 1}`, text: `‹ المرحلة ${stage.index - 1}` })
      : h("a.btn.btn--ghost", { href: "#/curriculum", text: "‹ كل المراحل" }),
    nextStage ? h("a.btn.btn--primary", { href: `#/stage/${nextStage.id}`, text: `المرحلة ${nextStage.index}: ${nextStage.title} ›` }) : h("span"),
  ]));

  return root;
};

/* ------------------------------------------------------------------ lesson */

export const renderLesson = async (lessonId) => {
  const lesson = getLesson(lessonId);
  if (!lesson) return notFound(`الدرس ${lessonId} مش موجود`);

  const content = await loadLessonContent(lessonId);
  const { prev, next } = neighbors(lessonId);
  const mod = getModule(lesson.module.id);

  const root = h("div");
  root.append(h("nav.crumbs", {}, [
    h("a", { href: "#/", text: "الرئيسية" }), h("span.sep", { text: "›" }),
    h("a", { href: `#/stage/${lesson.stage.id}`, text: lesson.stage.title }), h("span.sep", { text: "›" }),
    h("a", { href: `#/stage/${lesson.stage.id}#${lesson.module.id}`, text: mod?.title || lesson.module.title }), h("span.sep", { text: "›" }),
    h("span", { text: lesson.title }),
  ]));

  root.append(h("header.lesson-head", {}, [
    h("div.row", { style: "gap:8px;margin-bottom:10px" }, [
      h(`span.chip.chip--kind-${lesson.kind}`, { text: KIND_LABEL[lesson.kind] || lesson.kind }),
      h("span.chip", { text: humanMinutes(lesson.minutes) }),
      lesson.hasContent ? h("span.chip.chip--accent", { text: "محتوى كامل" }) : h("span.chip.chip--warn", { text: "المحتوى بيتكتب" }),
      h("span.chip", { text: `المرحلة ${lesson.stage.index}` }),
    ]),
    h("h1", { text: lesson.title }),
    h("span.lesson-head__en", { text: lesson.titleEn }),
    h("p.muted.mt-2", { text: lesson.summary }),
  ]));

  const layout = h("div.lesson-layout");
  const article = h("article");
  const aside = h("aside.lesson-aside");

  /* --- objectives --- */
  if (lesson.objectives?.length) {
    article.append(h("section.card.card--tight.mb-5", {}, [
      h("h3", { text: "في نهاية الدرس هتكون قادر على:" }),
      h("ul.objectives", {}, lesson.objectives.map((o) => h("li", { text: o }))),
    ]));
  }

  /* --- content or pending panel --- */
  if (content?.blocks?.length) {
    if (content.title && content.title !== lesson.title) article.append(h("h2", { text: content.title }));
    article.append(renderBlocks(content.blocks, { lessonId: lesson.id, lesson }));
  } else {
    article.append(h("section.pending", {}, [
      h("h3", { text: "محتوى الدرس ده لسه بيتكتب" }),
      h("p.muted", {
        text: "الدرس مسجّل في المنهج بالأهداف والمصادر، والمحتوى الكامل (شرح + كود + Quiz + مهام) بيتضاف على دفعات. تقدر تبدأ بالأهداف والمصادر دلوقتي، وتعلّم الدرس كمكتمل لما تذاكره.",
      }),
      h("div.row.mt-2", {}, [
        h("span.chip.mono", { text: lesson.id }),
        h("span.chip", { text: "ابعتلي المعرف ده عشان أكتب محتواه" }),
      ]),
      lesson.objectives?.length ? h("div.mt-4", {}, [
        h("h4", { text: "الأهداف" }),
        h("ul.objectives", {}, lesson.objectives.map((o) => h("li", { text: o }))),
      ]) : null,
    ]));
    if (lesson.resources?.length) article.append(h("div.mt-5", {}, resources({ title: "مصادر للبدء فورًا", items: lesson.resources })));
  }

  /* --- notes --- */
  const savedNote = getState().notes[lesson.id]?.text || "";
  const noteArea = h("textarea", { placeholder: "اكتب ملاحظاتك هنا… بتتحفظ تلقائيًا على جهازك", spellcheck: "false" });
  noteArea.value = savedNote;
  const saveNote = debounce(() => { setNote(lesson.id, noteArea.value.trim()); toast("الملاحظات اتحفظت"); }, 700);
  noteArea.addEventListener("input", saveNote);
  article.append(h("section.card.notes.mt-6", {}, [
    h("h3", { text: "ملاحظاتي على الدرس" }),
    noteArea,
    h("div.row.mt-2", {}, [
      h("span.dim.tiny", { text: "محفوظة محليًا — بتظهر تاني لما ترجع للدرس" }),
    ]),
  ]));

  /* --- complete button + pager --- */
  const doneBtn = h("button.btn.btn--primary.btn--wide", {
    type: "button",
    text: isDone(lesson.id) ? "✓ مكتمل — اضغط للإلغاء" : "علّم الدرس كمكتمل",
  });
  const syncDoneBtn = () => {
    const done = isDone(lesson.id);
    doneBtn.textContent = done ? "✓ مكتمل — اضغط للإلغاء" : "علّم الدرس كمكتمل";
    doneBtn.className = `btn btn--wide ${done ? "btn--ghost" : "btn--primary"}`;
  };
  doneBtn.addEventListener("click", () => {
    setLessonDone(lesson.id, !isDone(lesson.id), lesson.minutes);
    syncDoneBtn();
    toast(isDone(lesson.id) ? "تمام، اتسجّل الإنجاز 👌" : "اتلغى الإنجاز", isDone(lesson.id) ? "ok" : "warn");
  });
  article.append(h("div.mt-5", {}, doneBtn));

  article.append(h("nav.pager", {}, [
    prev ? h("a.btn.btn--ghost", { href: `#/lesson/${prev.id}` }, [h("small", { text: "الدرس السابق" }), h("span", { text: `› ${prev.title}` })]) : h("span"),
    next ? h("a.btn.btn--ghost", { href: `#/lesson/${next.id}` }, [h("small", { text: "الدرس التالي" }), h("span", { text: `${next.title} ‹` })]) : h("span"),
  ]));

  /* --- aside --- */
  const bookmarked = getState().bookmarks.includes(lesson.id);
  const bookmarkBtn = h("button.btn.btn--ghost.btn--sm", {
    type: "button", text: bookmarked ? "★ محفوظ" : "☆ احفظ في المفضلة",
  });
  bookmarkBtn.addEventListener("click", () => {
    const on = toggleBookmark(lesson.id);
    bookmarkBtn.textContent = on ? "★ محفوظ" : "☆ احفظ في المفضلة";
    toast(on ? "اتضاف للمفضلة" : "اتشال من المفضلة", "warn");
  });

  const ls = lessonState(lesson.id);
  aside.append(h("section.card.card--tight", {}, [
    h("h4", { text: "حالتك في الدرس" }),
    h("div.stack", { style: "gap:8px" }, [
      h("div.row", {}, [h("span.chip", { text: isDone(lesson.id) ? "مكتمل" : "لم يكتمل" })]),
      ls?.quiz ? h("span.dim.tiny", { text: `Quiz: ${ls.quiz.score}/${ls.quiz.total}` }) : h("span.dim.tiny", { text: "لسه ما حلّتش الـQuiz" }),
      ls?.completedAt ? h("span.dim.tiny", { text: `اتكمل: ${formatDate(ls.completedAt)}` }) : null,
      bookmarkBtn,
    ]),
  ]));

  aside.append(h("section.card.card--tight", {}, [
    h("h4", { text: `باقي دروس «${mod?.title || lesson.module.title}»` }),
    h("div.stack", { style: "gap:6px" },
      mod.lessons.map((l) => h("a", {
        href: `#/lesson/${l.id}`,
        class: l.id === lesson.id ? "chip chip--accent" : `chip${isDone(l.id) ? " chip--done" : ""}`,
        style: "justify-content:flex-start;width:100%",
        text: `${isDone(l.id) ? "✓ " : ""}${l.title}`,
      }))),
  ]));

  if (content?.blocks?.length) {
    aside.append(h("section.card.card--tight", {}, [
      h("h4", { text: "محتويات الدرس" }),
      h("div.stack", { style: "gap:6px" },
        content.blocks
          .filter((b) => b.type === "heading" || (b.title && ["quiz", "tasks", "steps", "terms", "resources", "checkpoints"].includes(b.type)))
          .map((b) => h("span.dim.tiny", { text: b.text || b.title }))),
    ]));
  }

  if (lesson.resources?.length && content?.blocks?.length) {
    aside.append(h("section.card.card--tight", {}, resources({ title: "مصادر", items: lesson.resources })));
  }

  layout.append(article, aside);
  root.append(layout);
  syncDoneBtn();
  return root;
};

/* ------------------------------------------------------------------ search */

export const renderSearch = (initial = "") => {
  const root = h("div");
  root.append(h("h1", { text: "ابحث في المنهج" }));
  root.append(h("p.muted", { text: "ابحث بالعربي أو الإنجليزي أو بمعرّف الدرس (مثال: s3-m2-l1)." }));

  const input = h("input", { type: "search", placeholder: "مثال: CQRS، Docker، async، مقابلة، s10…", value: initial });
  const box = h("div.searchbar", {}, [
    h("span.dim", { text: "🔎" }),
    input,
    h("span.chip.mono", { text: `${flatLessons().length} عنصر` }),
  ]);
  const results = h("div.search-hits");
  const counter = h("p.dim.tiny.mt-2");

  const run = () => {
    const q = input.value.trim();
    results.replaceChildren();
    if (!q) { counter.textContent = "اكتب كلمة للبحث."; return; }
    const hits = search(q);
    counter.textContent = hits.length ? `${hits.length} نتيجة` : "مفيش نتائج — جرّب كلمة أقصر أو بالإنجليزي.";
    for (const { lesson } of hits) {
      results.append(h("a.hit", { href: `#/lesson/${lesson.id}` }, [
        h("div.row", { style: "gap:8px" }, [
          h("span.kind-dot", { dataset: { kind: lesson.kind } }),
          h("strong", { text: lesson.title }),
          lesson.hasContent ? h("span.chip.chip--accent.tiny", { text: "جاهز" }) : null,
          isDone(lesson.id) ? h("span.chip.chip--done.tiny", { text: "مكتمل" }) : null,
        ]),
        h("span.dim.tiny", { text: `${lesson.stage.title} › ${lesson.module.title}` }),
        h("br"),
        h("small", { text: lesson.id }),
        h("p.dim.tiny", { text: lesson.summary, style: "margin:4px 0 0" }),
      ]));
    }
  };

  input.addEventListener("input", debounce(run, 180));
  root.append(box, counter, results);
  setTimeout(() => { input.focus(); run(); }, 30);
  return root;
};

/* ---------------------------------------------------------------- progress */

export const renderProgress = () => {
  const root = h("div");
  const ids = allLessonIds();
  const s = stats(ids);
  const st = streak();
  const m = meta();

  root.append(h("h1", { text: "تقدّمي" }));
  root.append(h("p.muted", { text: "كل البيانات على جهازك. تقدر تصدّرها نسخة احتياطية أو تستوردها على جهاز تاني." }));

  root.append(h("div.grid.grid--4", {}, [
    h("div.card.card--tight", {}, [h("div.stat", {}, [h("span.stat__v", { text: `${s.pct}%` }), h("span.stat__l", { text: "الإنجاز الكلي" })]), progressBar(s.done, s.total, "mt-2")]),
    h("div.card.card--tight", {}, [h("div.stat", {}, [h("span.stat__v", { text: `${s.done}/${s.total}` }), h("span.stat__l", { text: "دروس مكتملة" })])]),
    h("div.card.card--tight", {}, [h("div.stat", {}, [h("span.stat__v", { text: `${st.current}` }), h("span.stat__l", { text: "أيام متتالية" })])]),
    h("div.card.card--tight", {}, [h("div.stat", {}, [h("span.stat__v", { text: humanHours(s.minutesDone / 60) }), h("span.stat__l", { text: "ساعات مكتملة" })])]),
  ]));

  /* activity strip */
  const days = new Set(getState().activity);
  const strip = h("div.row.mt-5", { style: "gap:5px;flex-wrap:wrap" });
  for (let i = 27; i >= 0; i -= 1) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    strip.append(h("span", {
      title: key,
      style: `width:14px;height:14px;border-radius:4px;display:inline-block;background:${days.has(key) ? "var(--accent)" : "var(--surface-3)"}`,
    }));
  }
  root.append(h("section.card.mt-5", {}, [h("h3", { text: "آخر 28 يوم" }), strip]));

  /* per stage */
  const tableWrap = h("section.card.mt-5", {}, h("h3", { text: "التفصيل حسب المرحلة" }));
  const tbl = h("table.tbl");
  tbl.append(h("thead", {}, h("tr", {}, ["المرحلة", "الدروس", "المكتمل", "النسبة", "الوقت", ""].map((t) => h("th", { text: t })))));
  const body = h("tbody");
  for (const stage of stages()) {
    const lessons = stageLessons(stage.id);
    const done = lessons.filter((l) => isDone(l.id)).length;
    body.append(h("tr", {}, [
      h("td", {}, h("a", { href: `#/stage/${stage.id}`, text: `${stage.index}. ${stage.title}` })),
      h("td.mono", { text: String(lessons.length) }),
      h("td.mono", { text: String(done) }),
      h("td", { style: "min-width:120px" }, progressBar(done, lessons.length)),
      h("td.mono", { text: humanHours(stage.hours) }),
      h("td", {}, h("a.btn.btn--ghost.btn--sm", { href: `#/stage/${stage.id}`, text: "افتح" })),
    ]));
  }
  tbl.append(body);
  tableWrap.append(h("div", { style: "overflow-x:auto" }, tbl));
  root.append(tableWrap);

  /* bookmarks */
  const marks = getState().bookmarks.map(getLesson).filter(Boolean);
  root.append(h("section.card.mt-5", {}, [
    h("h3", { text: `المفضلة (${marks.length})` }),
    marks.length
      ? h("div.stack", { style: "gap:6px" }, marks.map((l) => lessonRow(l, { showStage: true })))
      : h("p.dim", { text: "لسه مفيش دروس محفوظة — اضغط ☆ في أي درس." }),
  ]));

  /* data management */
  const exportBtn = h("button.btn.btn--ghost", { type: "button", text: "تصدير نسخة احتياطية (JSON)" });
  exportBtn.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(exportState(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = h("a", { href: url, download: `dotnet-track-progress-${new Date().toISOString().slice(0, 10)}.json` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast("اتصدّرت النسخة الاحتياطية");
  });

  const importInput = h("input", { type: "file", accept: "application/json", style: "display:none" });
  importInput.addEventListener("change", async () => {
    const file = importInput.files?.[0];
    if (!file) return;
    try {
      importState(await file.text());
      toast("اتستورد التقدّم وانددمج مع الحالي");
      setTimeout(() => { location.hash = "#/progress"; location.reload(); }, 600);
    } catch (err) {
      toast(`فشل الاستيراد: ${err.message}`, "warn", 4000);
    }
  });
  const importBtn = h("button.btn.btn--ghost", { type: "button", text: "استيراد نسخة" });
  importBtn.addEventListener("click", () => importInput.click());

  const resetBtn = h("button.btn.btn--ghost", { type: "button", text: "تصفير كل التقدّم", style: "color:var(--danger);border-color:rgba(255,107,107,.4)" });
  resetBtn.addEventListener("click", () => {
    if (!confirm("متأكد؟ هيمسح كل الإنجاز والملاحظات والمفضلة من الجهاز.")) return;
    resetAll();
    toast("اتصفّر التقدّم", "warn");
    setTimeout(() => location.reload(), 500);
  });

  root.append(h("section.card.mt-5", {}, [
    h("h3", { text: "بياناتك" }),
    h("p.muted", {
      text: isServerMode()
        ? "التقدّم بيتحفظ في المتصفح وكمان في progress.json على جهازك (السيرفر المحلي شغال)."
        : "التقدّم بيتحفظ في المتصفح (localStorage). شغّل السيرفر المحلي لو عايز ملف progress.json كمان.",
    }),
    h("p.dim.tiny.mono", { text: `آخر تحديث: ${getState().updatedAt || "—"}` }),
    h("div.row.mt-4", {}, [exportBtn, importBtn, importInput, resetBtn]),
  ]));

  root.append(h("p.dim.tiny.mt-5", { text: `المنهج: ${m.title} · إصدار ${m.version || "1.0"} · حُدّث ${m.updatedAt || ""}` }));
  return root;
};

/* ---------------------------------------------------------------- not found */

export const notFound = (message) =>
  h("div.empty", {}, [
    h("h2", { text: "مش موجود" }),
    h("p.muted", { text: message || "الرابط ده مش موجود في المسار." }),
    h("a.btn.btn--primary", { href: "#/", text: "ارجع للرئيسية" }),
  ]);

export { normalizeAr };
