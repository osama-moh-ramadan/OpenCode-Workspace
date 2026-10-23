(function () {
  "use strict";

  const A = window.Academy;

  /* ------------------------------- عناصر الصفحة ------------------------------- */

  const main = document.getElementById("main");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const nav = document.getElementById("moduleNav");
  const crumbs = document.getElementById("crumbs");
  const searchInput = document.getElementById("searchInput");
  const searchResults = document.getElementById("searchResults");
  const toastEl = document.getElementById("toast");
  const themeToggle = document.getElementById("themeToggle");

  let currentLessonId = null;
  let currentPage = "home";
  let toastTimer = null;

  /* -------------------------------- المظهر -------------------------------- */

  function applyTheme(theme) {
    const value = theme === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = value;
    document.documentElement.style.colorScheme = value;
    if (themeToggle) {
      const dark = value === "dark";
      themeToggle.setAttribute("aria-pressed", String(dark));
      themeToggle.setAttribute("aria-label", dark ? "تفعيل الوضع الفاتح" : "تفعيل الوضع الداكن");
      themeToggle.title = dark ? "الوضع الفاتح" : "الوضع الداكن";
    }
  }

  /* -------------------------------- أيقونات -------------------------------- */

  const svg = (paths, extra = "") =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${extra} aria-hidden="true">${paths}</svg>`;

  const ICONS = {
    check: svg('<path d="M20 6 9 17l-5-5"/>'),
    clock: svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    book: svg('<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/>'),
    target: svg('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>'),
    project: svg('<path d="M4 7h16v13H4z"/><path d="M8 7V4h8v3M8 12h8M8 16h5"/>'),
    arrow: svg('<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>'),
    copy: svg('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>'),
    external: svg('<path d="M14 3h7v7M21 3l-9 9"/><path d="M10 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/>'),
    chevron: svg('<path d="m6 9 6 6 6-6"/>'),
    layers: svg('<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>'),
    code: svg('<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 4l-4 16"/>'),
    spark: svg('<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>'),
  };

  /* -------------------------------- أدوات -------------------------------- */

  const esc = (value) => A.escapeHtml(value);

  function norm(value) {
    return String(value)
      .toLowerCase()
      .replace(/[\u064B-\u0652\u0670]/g, "")
      .replace(/[أإآ]/g, "ا")
      .replace(/ى/g, "ي")
      .replace(/ة/g, "ه");
  }

  function toast(message, kind = "ok") {
    toastEl.textContent = message;
    toastEl.dataset.kind = kind;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3000);
  }

  function langLabel(lang) {
    return (
      {
        csharp: "C#",
        bash: "Terminal",
        json: "JSON",
        http: "HTTP",
        xml: "XML",
        yaml: "YAML",
        dockerfile: "Dockerfile",
        sql: "SQL",
        text: "Text",
      }[lang] || lang
    );
  }

  function codeBlock(sample) {
    if (!sample || !sample.code) return "";
    const lang = sample.lang || "csharp";
    return `<figure class="code-block">
      <figcaption class="code-head">
        <span class="code-lang">${langLabel(lang)}</span>
        ${sample.title ? `<span class="code-title">${esc(sample.title)}</span>` : ""}
        <button class="copy-btn" type="button" data-copy>${ICONS.copy}<span>نسخ</span></button>
      </figcaption>
      <pre dir="ltr" tabindex="0"><code class="language-${lang}">${A.highlight(String(sample.code).trim(), lang)}</code></pre>
    </figure>`;
  }

  function lenHours(lessons) {
    const minutes = lessons.reduce((sum, lesson) => sum + (Number(lesson.duration) || 0), 0);
    const hours = Math.round((minutes / 60) * 10) / 10;
    return hours;
  }

  function statusOf(lesson) {
    const entry = A.lessonState(lesson.id);
    const quiz = lesson.quiz || [];
    const correct = quiz.filter((_, i) => entry.quiz[i] && entry.quiz[i].correct).length;
    const tasks = lesson.capstone?.tasks || [];
    const tasksDone = tasks.filter((_, i) => entry.tasks[i]).length;
    return { entry, correct, quizTotal: quiz.length, tasksDone, tasksTotal: tasks.length };
  }

  function setCrumbs(parts) {
    crumbs.innerHTML = parts
      .map((part, index) => {
        const label = esc(part.label);
        const node = part.href ? `<a href="${part.href}">${label}</a>` : `<span class="crumb-current">${label}</span>`;
        return index < parts.length - 1 ? `${node}<span class="crumb-sep">/</span>` : node;
      })
      .join("");
  }

  function setActiveNav(page) {
    document.querySelectorAll("[data-nav]").forEach((link) => {
      link.classList.toggle("active", link.dataset.nav === page);
    });
  }

  /* ------------------------------ شريط التقدم ------------------------------ */

  function updateProgressUI() {
    const totals = A.totals();
    const percent = totals.percent || 0;
    const header = document.getElementById("headerProgress");
    if (header) {
      header.textContent = `${percent}%`;
      header.title = `${totals.completed} من ${totals.lessons} درسًا مكتملًا`;
    }

    const pct = document.getElementById("overallPct");
    const bar = document.getElementById("overallBar");
    const sub = document.getElementById("overallSub");
    const title = document.getElementById("overallTitle");
    const xp = document.getElementById("xpBadge");
    if (pct) pct.textContent = `${percent}%`;
    if (bar) bar.style.width = `${percent}%`;
    if (sub) sub.textContent = `${totals.completed} من ${totals.lessons} درسًا`;
    if (title) {
      title.textContent =
        percent === 0 ? "لنبدأ المسار" : percent < 35 ? "بداية جيدة" : percent < 75 ? "منتصف المسار" : percent < 100 ? "اقتربت من النهاية" : "أكملت المسار";
    }
    if (xp) xp.textContent = `${totals.xp.toLocaleString("en-US")} XP`;
  }

  /* ------------------------------ الشريط الجانبي ------------------------------ */

  function renderNav() {
    const modules = A.getModules();
    nav.innerHTML = modules
      .map((mod, index) => {
        const progress = A.moduleProgress(mod.id);
        const containsActive = mod.lessons.some((lesson) => lesson.id === currentLessonId);
        const lessons = mod.lessons
          .map((lesson) => {
            const done = A.isComplete(lesson.id);
            const active = lesson.id === currentLessonId;
            return `<a class="nav-lesson ${done ? "done" : ""} ${active ? "active" : ""}"
              href="#/lesson/${encodeURIComponent(lesson.id)}" ${active ? 'aria-current="page"' : ""}>
              <span class="nav-check">${done ? ICONS.check : `<span class="nav-num">${lesson.lessonIndex + 1}</span>`}</span>
              <span class="nav-title">${esc(lesson.title)}</span>
              <span class="nav-time">${lesson.duration}<small>د</small></span>
            </a>`;
          })
          .join("");
        return `<details class="nav-module" ${containsActive ? "open" : ""}>
          <summary class="nav-module-head">
            <span>${String(index + 1).padStart(2, "0")} · ${esc(mod.title)}</span>
            <span class="nav-module-count">${progress.completed}/${mod.lessons.length}</span>
            ${ICONS.chevron}
          </summary>
          <div class="nav-lessons">${lessons}</div>
        </details>`;
      })
      .join("");
  }

  function openSidebar() {
    sidebar.classList.add("open");
    backdrop.hidden = false;
    document.body.classList.add("no-scroll");
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    backdrop.hidden = true;
    document.body.classList.remove("no-scroll");
  }

  /* -------------------------------- البحث -------------------------------- */

  function hideSearchResults() {
    searchResults.hidden = true;
    searchInput.setAttribute("aria-expanded", "false");
  }

  function renderSearchResults(query) {
    const q = norm(query.trim());
    if (!q) {
      hideSearchResults();
      return;
    }
    const matches = A.getLessons()
      .filter((lesson) =>
        norm(`${lesson.title} ${lesson.summary} ${(lesson.keywords || []).join(" ")} ${lesson.moduleTitle}`).includes(q)
      )
      .slice(0, 8);

    searchResults.innerHTML = matches.length
      ? matches
          .map(
            (lesson) => `<a class="search-result" href="#/lesson/${encodeURIComponent(lesson.id)}">
              <strong>${esc(lesson.title)}</strong>
              <span>${esc(lesson.moduleTitle)} · ${lesson.duration} دقيقة</span>
            </a>`
          )
          .join("")
      : `<div class="search-empty">لا توجد دروس تطابق «${esc(query.trim())}».</div>`;
    searchResults.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
  }

  /* -------------------------------- الرئيسية -------------------------------- */

  function renderHome() {
    currentPage = "home";
    currentLessonId = null;
    document.body.classList.remove("with-sidebar");
    setActiveNav("home");

    const totals = A.totals();
    const modules = A.getModules();
    const lessons = A.getLessons();
    const state = A.getState();
    const last = state.lastLesson ? A.getLesson(state.lastLesson) : null;
    const allDone = totals.lessons > 0 && totals.completed === totals.lessons;
    let next = last || lessons[0];
    if (allDone) next = lessons[0];
    else if (last && A.isComplete(last.id)) {
      const neighbors = A.getNeighbors(last.id);
      next = neighbors.next || last;
    }
    const hours = lenHours(lessons);

    document.title = "Souq Academy — مسار .NET Backend من الصفر إلى الإنتاج";
    setCrumbs([{ label: "المسار" }]);
    renderNav();
    updateProgressUI();

    main.innerHTML = `<div class="home">
      <section class="course-hero">
        <div class="hero-copy">
          <span class="eyebrow">مسار .NET Backend</span>
          <h1 class="hero-title">من أول سطر <code>C#</code> إلى API جاهز للإنتاج.</h1>
          <p class="hero-lead">
            مرجع واحد متكامل: يشرح الفكرة من الصفر، يفكّك كل سطر كود، ويبني معك
            مشروع <strong>Souq.NET</strong> للتجارة الإلكترونية خطوة بخطوة — حتى تصبح قادرًا
            على بناء API حقيقي والدفاع عنه في مقابلة عمل.
          </p>
          <div class="hero-meta">
            <span>${ICONS.target} من المبتدئ إلى المحترف</span>
            <span>${ICONS.layers} ${modules.length} وحدات</span>
            <span>${ICONS.book} ${lessons.length} درسًا</span>
            <span>${ICONS.clock} نحو ${hours} ساعة</span>
          </div>
          <div class="hero-actions">
            <a class="btn primary" href="#/lesson/${next.id}">
              ${totals.completed ? (allDone ? "راجع أول درس" : "أكمل من حيث توقفت") : "ابدأ الدرس الأول"}
              ${ICONS.arrow}
            </a>
            <a class="btn secondary" href="#/project">${ICONS.project} مشروع المسار</a>
          </div>
          ${
            totals.completed
              ? `<div class="hero-progress">
                  <div class="progress-track"><i style="width:${totals.percent}%"></i></div>
                  <p>أكملت ${totals.completed} من ${totals.lessons} درسًا — تقدمك محفوظ على جهازك.</p>
                </div>`
              : ""
          }
        </div>

        <aside class="course-includes">
          <h2>هذا المسار يضم</h2>
          <ul class="includes-list">
            <li>${ICONS.check}<span>شرح تدريجي من أول سطر، بدون افتراض معرفة سابقة.</span></li>
            <li>${ICONS.code}<span>تفكيك الكود سطرًا بسطر: ماذا ينفّذ، وماذا يحدث في الخلفية.</span></li>
            <li>${ICONS.target}<span>اختبارات فورية وتطبيق عملي بعد كل مفهوم.</span></li>
            <li>${ICONS.project}<span>مشروع E-Commerce واحد يكبر معك حتى النشر.</span></li>
          </ul>
          <p class="includes-note">بدون تسجيل دخول، وبدون فيديوهات. كل شيء نص وكود قابل للنسخ.</p>
        </aside>
      </section>

      <section class="stat-strip" aria-label="ملخص المسار">
        <div class="stat-item">${ICONS.target}<div><span>المستوى</span><strong>مبتدئ → متقدم</strong></div></div>
        <div class="stat-item">${ICONS.clock}<div><span>الوقت التقديري</span><strong>${hours} ساعة</strong></div></div>
        <div class="stat-item">${ICONS.book}<div><span>الدروس</span><strong>${lessons.length} درسًا</strong></div></div>
        <div class="stat-item">${ICONS.project}<div><span>المشروع</span><strong>${totals.tasksTotal} خطوة</strong></div></div>
      </section>

      <section class="section-block" id="curriculum">
        <div class="section-heading">
          <div>
            <h2>خطة المسار</h2>
            <p>كل وحدة تبني على التي قبلها. ابدأ من الأعلى وتقدّم بالترتيب.</p>
          </div>
          <div class="heading-progress">
            <span>${totals.completed} / ${totals.lessons}</span>
            <div class="progress-track"><i style="width:${totals.percent}%"></i></div>
          </div>
        </div>

        ${modules
          .map((mod, index) => {
            const progress = A.moduleProgress(mod.id);
            const moduleLessons = mod.lessons
              .map((lesson) => {
                const done = A.isComplete(lesson.id);
                return `<li>
                  <a class="lesson-row ${done ? "done" : ""}" href="#/lesson/${encodeURIComponent(lesson.id)}">
                    <span class="lesson-row-index">${done ? ICONS.check : String(lesson.lessonIndex + 1).padStart(2, "0")}</span>
                    <span class="lesson-row-title">${esc(lesson.title)}</span>
                    <span class="lesson-row-meta">${lesson.duration} د</span>
                    <span class="lesson-status ${done ? "done" : ""}">${done ? "مكتمل" : "ابدأ"}</span>
                  </a>
                </li>`;
              })
              .join("");
            return `<details class="module-panel" open>
              <summary class="module-summary">
                <span class="module-number">${String(index + 1).padStart(2, "0")}</span>
                <div class="module-summary-copy">
                  <h3>${esc(mod.title)}</h3>
                  <p>${esc(mod.tagline)}</p>
                </div>
                <div class="module-meta">
                  <span>${mod.lessons.length} دروس · ${lenHours(mod.lessons)} ساعة</span>
                  <div class="module-bar"><i style="width:${progress.percent}%"></i></div>
                </div>
                ${svg('<path d="m6 9 6 6 6-6"/>', 'class="module-chevron"')}
              </summary>
              <ol class="lesson-list">${moduleLessons}</ol>
            </details>`;
          })
          .join("")}
      </section>

      <section class="project-banner">
        <div>
          <h2>المشروع: Souq.NET E-Commerce API</h2>
          <p>
            لن نبقى في أمثلة منفصلة. كل درس يضيف طبقة حقيقية إلى متجر إلكتروني:
            منتجات، سلة، طلبات، مصادقة، دفع، كاش، اختبارات، ونشر. المشروع هو
            مساحة التطبيق التي تربط كل ما تتعلمه.
          </p>
        </div>
        <div class="project-banner-actions">
          <a class="btn primary" href="#/project">${ICONS.project} افتح صفحة المشروع</a>
        </div>
      </section>
    </div>`;

    closeSidebar();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  /* --------------------------------- الدرس --------------------------------- */

  function renderLesson(id) {
    const lesson = A.getLesson(id);
    if (!lesson) return renderNotFound();

    currentPage = "lesson";
    currentLessonId = id;
    A.setLastLesson(id);
    document.body.classList.add("with-sidebar");
    setActiveNav("home");

    const status = statusOf(lesson);
    const neighbors = A.getNeighbors(id);
    const total = A.getLessons().length;

    document.title = `${lesson.title} — Souq Academy`;
    setCrumbs([
      { label: "المسار", href: "#/home" },
      { label: lesson.moduleTitle, href: "#/home" },
      { label: lesson.title },
    ]);
    renderNav();
    updateProgressUI();

    const hasWalkthrough = Array.isArray(lesson.walkthrough) && lesson.walkthrough.length > 0;
    const sections = [
      ["s-concept", "الشرح"],
      ...(hasWalkthrough ? [["s-walkthrough", "سطرًا بسطر"]] : []),
      ["s-compare", "قبل / بعد"],
      ["s-internals", "تحت الغطاء"],
      ["s-tips", "نصائح"],
      ["s-quiz", "اختبار"],
      ["s-capstone", "المشروع"],
    ];
    let sectionNumber = 0;
    const nConcept = String(++sectionNumber).padStart(2, "0");
    const nWalk = hasWalkthrough ? String(++sectionNumber).padStart(2, "0") : null;
    const nCompare = String(++sectionNumber).padStart(2, "0");
    const nInternals = String(++sectionNumber).padStart(2, "0");
    const nTips = String(++sectionNumber).padStart(2, "0");
    const nQuiz = String(++sectionNumber).padStart(2, "0");
    const nCapstone = String(++sectionNumber).padStart(2, "0");

    const internalsTable = lesson.internalsTable
      ? `<div class="table-wrap"><table>
          <thead><tr>${lesson.internalsTable.head.map((head) => `<th>${head}</th>`).join("")}</tr></thead>
          <tbody>${lesson.internalsTable.rows
            .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
            .join("")}</tbody>
        </table></div>`
      : "";

    const walkthrough = hasWalkthrough
      ? `<section class="lesson-section" id="s-walkthrough">
          <div class="section-head">
            <span class="section-num">${nWalk}</span>
            <div><h2>الكود سطرًا بسطر</h2><p>كل جزء من الكود: ما وظيفته، وما الذي يحدث في الخلفية عند تنفيذه.</p></div>
          </div>
          <div class="section-body">
            <div class="walkthrough">
              ${lesson.walkthrough
                .map(
                  (step, index) => `<div class="walk-step">
                    <div class="walk-step-head"><span class="walk-num">${index + 1}</span><strong>${esc(step.title)}</strong></div>
                    <pre class="walk-code" dir="ltr"><code>${A.highlight(String(step.code).trim(), step.lang || "csharp")}</code></pre>
                    <div class="walk-copy">${step.body}</div>
                  </div>`
                )
                .join("")}
            </div>
          </div>
        </section>`
      : "";

    const compare = lesson.compare || {};
    const compareSection = `<section class="lesson-section" id="s-compare">
      <div class="section-head">
        <span class="section-num">${nCompare}</span>
        <div><h2>قبل وبعد</h2><p>نفس المشكلة مرتين: النمط القديم، ثم الطريقة التي تُكتب بها في .NET الحديثة.</p></div>
      </div>
      <div class="section-body">
        ${compare.intro ? `<div class="prose">${compare.intro}</div>` : ""}
        <div class="compare">
          <div class="compare-card before">
            <div class="compare-head"><span class="compare-label">قبل</span><h3>${esc(compare.before?.label || "الطريقة التقليدية")}</h3></div>
            ${codeBlock(compare.before)}
            ${
              compare.before?.points?.length
                ? `<ul class="compare-points bad">${compare.before.points.map((point) => `<li>${point}</li>`).join("")}</ul>`
                : ""
            }
          </div>
          <div class="compare-card after">
            <div class="compare-head"><span class="compare-label">بعد</span><h3>${esc(compare.after?.label || "الطريقة الحديثة")}</h3></div>
            ${codeBlock(compare.after)}
            ${
              compare.after?.points?.length
                ? `<ul class="compare-points good">${compare.after.points.map((point) => `<li>${point}</li>`).join("")}</ul>`
                : ""
            }
          </div>
        </div>
        ${
          compare.verdict
            ? `<div class="verdict"><strong>لماذا هذا أفضل؟</strong>${compare.verdict}</div>`
            : ""
        }
      </div>
    </section>`;

    main.innerHTML = `<article class="lesson-article">
      <header class="lesson-header">
        <div class="lesson-top">
          <span class="module-label">${esc(lesson.moduleTitle)}</span>
          <span>·</span>
          <span>الدرس ${lesson.order + 1} من ${total}</span>
          ${A.isComplete(id) ? `<span class="done-pill">${ICONS.check} مكتمل</span>` : ""}
        </div>
        <h1 class="lesson-title">${esc(lesson.title)}</h1>
        <p class="lesson-summary">${lesson.summary}</p>
        <div class="lesson-meta">
          <span>${ICONS.clock} ${lesson.duration} دقيقة</span>
          <span>${ICONS.target} ${esc(lesson.level)}</span>
          <span>${ICONS.book} ${status.quizTotal} أسئلة · ${status.tasksTotal} خطوة عملية</span>
        </div>
        <div class="objectives">
          <strong>بنهاية الدرس ستكون قادرًا على</strong>
          <ul>${(lesson.objectives || []).map((objective) => `<li>${objective}</li>`).join("")}</ul>
        </div>
      </header>

      <nav class="lesson-toc" aria-label="أقسام الدرس">
        ${sections.map(([target, label]) => `<button type="button" data-scroll="${target}">${label}</button>`).join("")}
      </nav>

      <section class="lesson-section" id="s-concept">
        <div class="section-head">
          <span class="section-num">${nConcept}</span>
          <div><h2>الشرح من الصفر</h2><p>الفكرة كما لو أنك تسمعها لأول مرة، ثم نبني عليها بقية الدرس.</p></div>
        </div>
        <div class="section-body prose">${lesson.concept}</div>
      </section>

      ${walkthrough}
      ${compareSection}

      <section class="lesson-section" id="s-internals">
        <div class="section-head">
          <span class="section-num">${nInternals}</span>
          <div><h2>تحت الغطاء والأداء</h2><p>ماذا يفعل CLR أو Kestrel أو GC فعلًا؟ وأين تظهر التكلفة في الإنتاج؟</p></div>
        </div>
        <div class="section-body prose">${lesson.internals}${internalsTable}</div>
      </section>

      <section class="lesson-section" id="s-tips">
        <div class="section-head">
          <span class="section-num">${nTips}</span>
          <div><h2>أخطاء شائعة ونصائح مهنية</h2><p>قواعد قصيرة تفصل بين كود يعمل وكود يمكن أن يعيش في الإنتاج.</p></div>
        </div>
        <div class="section-body">
          <div class="tips">
            ${(lesson.tips || [])
              .map(
                (tip, index) => `<div class="tip">
                  <span class="tip-num">${String(index + 1).padStart(2, "0")}</span>
                  <div><h3>${esc(tip.title)}</h3><div>${tip.body}</div></div>
                </div>`
              )
              .join("")}
          </div>
        </div>
      </section>

      <section class="lesson-section" id="s-quiz">
        <div class="section-head">
          <span class="section-num">${nQuiz}</span>
          <div><h2>اختبر فهمك</h2><p>الإجابة تُصحَّح محليًا مع تفسير فوري. أجب على الكل لإكمال الدرس تلقائيًا.</p></div>
        </div>
        <div class="section-body">
          <div class="quiz" id="quizRoot">${renderQuiz(lesson)}</div>
        </div>
      </section>

      <section class="lesson-section" id="s-capstone">
        <div class="section-head">
          <span class="section-num">${nCapstone}</span>
          <div><h2>خطوة المشروع: Souq.NET</h2><p>كل درس يضيف جزءًا حقيقيًا إلى الـ API. علّم الخطوات عندما تنجزها.</p></div>
        </div>
        <div class="section-body">
          <div class="project-step">
            <div class="project-step-head">
              <div>
                <h3>${esc(lesson.capstone?.title || "خطوة المشروع")}</h3>
                <p>${lesson.capstone?.goal || ""}</p>
              </div>
              <div class="project-step-score">
                <strong id="capstoneScore">${status.tasksDone}/${status.tasksTotal}</strong>
                <span>خطوات</span>
              </div>
            </div>
            <div class="progress-track"><i id="capstoneBar" style="width:${status.tasksTotal ? (status.tasksDone / status.tasksTotal) * 100 : 0}%"></i></div>
            <ul class="task-list">
              ${(lesson.capstone?.tasks || [])
                .map(
                  (task, index) => `<li>
                    <label class="task">
                      <input type="checkbox" data-task data-lesson="${id}" data-task-index="${index}" ${status.entry.tasks[index] ? "checked" : ""} />
                      <span class="task-box">${ICONS.check}</span>
                      <span class="task-text">${task}</span>
                    </label>
                  </li>`
                )
                .join("")}
            </ul>
            ${lesson.capstone?.code ? codeBlock(lesson.capstone.code) : ""}
          </div>
        </div>
      </section>

      <section class="completion" id="completionPanel">${renderCompletion(lesson)}</section>

      <nav class="lesson-pager" aria-label="التنقل بين الدروس">
        ${
          neighbors.prev
            ? `<a class="pager-link prev" href="#/lesson/${encodeURIComponent(neighbors.prev.id)}"><span>الدرس السابق</span><strong>${esc(neighbors.prev.title)}</strong></a>`
            : `<span class="pager-link disabled"></span>`
        }
        ${
          neighbors.next
            ? `<a class="pager-link next" href="#/lesson/${encodeURIComponent(neighbors.next.id)}"><span>الدرس التالي</span><strong>${esc(neighbors.next.title)}</strong></a>`
            : `<a class="pager-link next" href="#/home"><span>نهاية المسار الحالي</span><strong>ارجع إلى خريطة الدروس</strong></a>`
        }
      </nav>
    </article>`;

    closeSidebar();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function renderCompletion(lesson) {
    const entry = A.lessonState(lesson.id);
    const done = Boolean(entry.completed);
    return `<div class="completion-inner ${done ? "is-done" : ""}">
      <div class="completion-icon">${done ? ICONS.check : ICONS.target}</div>
      <div class="completion-copy">
        <h3>${done ? "أحسنت — هذا الدرس مكتمل" : "جاهز لإغلاق هذا الدرس؟"}</h3>
        <p>${done ? "تقدمك محفوظ محليًا. يمكنك مراجعة الاختبار أو الانتقال للدرس التالي." : "أكمل الاختبارات، أو علّم الدرس يدويًا إذا كنت تريد المتابعة."}</p>
      </div>
      <button class="btn ${done ? "secondary" : "primary"}" type="button" data-complete data-lesson="${lesson.id}">
        ${done ? "إلغاء الإكمال" : "تحديد كمكتمل"} ${done ? "" : ICONS.check}
      </button>
    </div>`;
  }

  /* --------------------------------- الاختبار --------------------------------- */

  function renderQuiz(lesson) {
    const entry = A.lessonState(lesson.id);
    const quiz = lesson.quiz || [];
    const answeredCount = quiz.filter((_, index) => entry.quiz[index]).length;
    const correctCount = quiz.filter((_, index) => entry.quiz[index]?.correct).length;

    return (
      quiz
        .map((question, questionIndex) => {
          const saved = entry.quiz[questionIndex];
          const answered = Boolean(saved);
          const options = question.options
            .map((option, optionIndex) => {
              let className = "";
              let mark = "";
              if (answered) {
                if (optionIndex === question.answer) {
                  className = "correct";
                  mark = ICONS.check;
                } else if (saved.picked === optionIndex) {
                  className = "wrong";
                  mark = "×";
                }
              }
              return `<button type="button" class="quiz-option ${className}"
                data-quiz-option data-lesson="${lesson.id}" data-q="${questionIndex}" data-opt="${optionIndex}"
                ${answered ? "disabled" : ""}>
                <span class="opt-key">${String.fromCharCode(65 + optionIndex)}</span>
                <span class="opt-text">${option}</span>
                <span class="opt-mark">${mark}</span>
              </button>`;
            })
            .join("");

          const feedback = answered
            ? `<div class="quiz-feedback ${saved.correct ? "ok" : "bad"}">
                <strong>${saved.correct ? "إجابة صحيحة." : `ليست صحيحة — الإجابة الصحيحة هي (${String.fromCharCode(65 + question.answer)}).`}</strong>
                <p>${question.explain}</p>
                ${saved.correct ? "" : `<button type="button" class="retry-btn" data-retry data-lesson="${lesson.id}" data-q="${questionIndex}">حاول مرة أخرى</button>`}
              </div>`
            : "";

          return `<div class="quiz-question ${answered ? "answered" : ""}" data-question="${questionIndex}">
            <div class="quiz-q-head"><span class="q-index">س${questionIndex + 1}</span><h3>${question.q}</h3></div>
            <div class="quiz-options">${options}</div>
            ${feedback}
          </div>`;
        })
        .join("") +
      `<div class="quiz-summary">
        <span>${ICONS.target} النتيجة: <strong>${correctCount}/${quiz.length}</strong></span>
        <div class="progress-track"><i style="width:${quiz.length ? (correctCount / quiz.length) * 100 : 0}%"></i></div>
        <small>${
          answeredCount === quiz.length
            ? correctCount === quiz.length
              ? "ممتاز — أتممت الاختبار بالكامل."
              : "راجع التفسيرات وأعد المحاولة للسؤال الخاطئ."
            : "أجب على جميع الأسئلة."
        }</small>
      </div>`
    );
  }

  function refreshQuiz(lesson) {
    const root = document.getElementById("quizRoot");
    if (root) root.innerHTML = renderQuiz(lesson);
    refreshDynamic(lesson);
  }

  function refreshDynamic(lesson) {
    const panel = document.getElementById("completionPanel");
    if (panel) panel.innerHTML = renderCompletion(lesson);
    const status = statusOf(lesson);
    const score = document.getElementById("capstoneScore");
    const bar = document.getElementById("capstoneBar");
    if (score) score.textContent = `${status.tasksDone}/${status.tasksTotal}`;
    if (bar) bar.style.width = `${status.tasksTotal ? (status.tasksDone / status.tasksTotal) * 100 : 0}%`;

    const donePill = document.querySelector(".lesson-top .done-pill");
    const complete = A.isComplete(lesson.id);
    if (complete && !donePill) {
      const top = document.querySelector(".lesson-top");
      if (top) {
        const pill = document.createElement("span");
        pill.className = "done-pill";
        pill.innerHTML = `${ICONS.check} مكتمل`;
        top.appendChild(pill);
      }
    } else if (!complete && donePill) {
      donePill.remove();
    }
    updateProgressUI();
    renderNav();
  }

  /* -------------------------------- المشروع -------------------------------- */

  function projectStats() {
    const lessons = A.getLessons();
    const allTasks = lessons.reduce((sum, lesson) => sum + (lesson.capstone?.tasks?.length || 0), 0);
    const doneTasks = lessons.reduce((sum, lesson) => {
      const entry = A.lessonState(lesson.id);
      return sum + (lesson.capstone?.tasks || []).filter((_, index) => entry.tasks[index]).length;
    }, 0);
    return { lessons, allTasks, doneTasks, percent: allTasks ? Math.round((doneTasks / allTasks) * 100) : 0 };
  }

  function projectTaskCount(module) {
    let total = 0;
    let done = 0;
    for (const lesson of module.lessons) {
      const tasks = lesson.capstone?.tasks || [];
      const entry = A.lessonState(lesson.id);
      total += tasks.length;
      done += tasks.filter((_, index) => entry.tasks[index]).length;
    }
    return { total, done };
  }

  function updateProjectProgressUI() {
    const stats = projectStats();
    const score = document.getElementById("projectScore");
    const done = document.getElementById("projectDone");
    const bar = document.getElementById("projectBar");
    const pct = document.getElementById("projectPct");
    if (score) score.textContent = `${stats.doneTasks}/${stats.allTasks}`;
    if (done) done.textContent = `${stats.doneTasks} من ${stats.allTasks} خطوة`;
    if (bar) bar.style.width = `${stats.percent}%`;
    if (pct) pct.textContent = `${stats.percent}%`;
    document.querySelectorAll("[data-milestone-count]").forEach((node) => {
      const module = A.getModule(node.dataset.milestoneCount);
      if (!module) return;
      const count = projectTaskCount(module);
      node.textContent = `${count.done}/${count.total}`;
    });
  }

  function renderProject() {
    currentPage = "project";
    currentLessonId = null;
    document.body.classList.remove("with-sidebar");
    setActiveNav("project");
    const stats = projectStats();
    const modules = A.getModules();

    document.title = "مشروع Souq.NET — Souq Academy";
    setCrumbs([{ label: "المسار", href: "#/home" }, { label: "المشروع" }]);
    updateProgressUI();

    const endpoints = [
      ["GET", "/api/products", "قائمة المنتجات مع بحث وترقيم صفحات"],
      ["GET", "/api/products/{id}", "تفاصيل منتج واحد"],
      ["POST", "/api/products", "إنشاء منتج — يتطلب صلاحية Admin"],
      ["PUT", "/api/products/{id}", "تحديث منتج — يتطلب صلاحية Admin"],
      ["DELETE", "/api/products/{id}", "حذف ناعم لمنتج — يتطلب صلاحية Admin"],
      ["POST", "/api/auth/login", "إصدار JWT بعد التحقق من بيانات المستخدم"],
      ["GET", "/api/cart", "سلة المستخدم الحالي"],
      ["POST", "/api/orders", "إنشاء طلب من السلة بشكل Idempotent"],
      ["GET", "/api/orders/{id}", "تفاصيل طلب يملكه المستخدم"],
      ["GET", "/health/live", "فحص سريع لبقاء العملية"],
    ];

    main.innerHTML = `<div class="project-page">
      <header class="project-hero">
        <div>
          <span class="eyebrow">المشروع التطبيقي</span>
          <h1>Souq.NET — متجر إلكتروني كامل</h1>
          <p>
            مشروع واحد يكبر مع المسار. تبدأ بمشروع Web API فارغ، ثم تضيف المنتجات،
            المصادقة، السلة، الطلبات، قاعدة البيانات، الكاش، الاختبارات، والنشر.
            كل خطوة مرتبطة بدرس، ومربوطة بمهمة تستطيع تنفيذها والتحقق منها.
          </p>
        </div>
        <aside class="project-score">
          <strong id="projectScore">${stats.doneTasks}/${stats.allTasks}</strong>
          <span id="projectDone">${stats.doneTasks} من ${stats.allTasks} خطوة</span>
          <div class="progress-track"><i id="projectBar" style="width:${stats.percent}%"></i></div>
          <span id="projectPct" style="margin-top:6px;direction:ltr">${stats.percent}%</span>
        </aside>
      </header>

      <div class="project-grid">
        <section>
          <h2>ماذا ستبني فعليًا؟</h2>
          <ul>
            <li>API لمنتجات مع CRUD، تحقق، أخطاء موحّدة، وترقيم صفحات.</li>
            <li>مصادقة JWT وصلاحيات مبنية على الأدوار والسياسات.</li>
            <li>سلة وطلبات مع معاملات (Transactions) ومنع التكرار.</li>
            <li>EF Core مع علاقات، ترحيلات، استعلامات محسّنة، واختبارات تكامل.</li>
            <li>كاش، مراقبة، Docker، ونشر قابل للتشغيل في الإنتاج.</li>
          </ul>
        </section>
        <section>
          <h2>شكل النظام</h2>
          <div class="architecture" aria-label="مخطط معماري مبسط">
            <div class="arch-row">
              <div class="arch-box">Client<small>Web / Mobile</small></div>
              <span class="arch-arrow">←</span>
              <div class="arch-box">ASP.NET Core API<small>Kestrel + Middleware</small></div>
            </div>
            <div class="arch-row">
              <div class="arch-box">Application<small>Use Cases / DTOs</small></div>
              <span class="arch-arrow">←</span>
              <div class="arch-box">Domain<small>Entities / Rules</small></div>
            </div>
            <div class="arch-row">
              <div class="arch-box">Infrastructure<small>EF Core / JWT / Cache</small></div>
              <span class="arch-arrow">←</span>
              <div class="arch-box">PostgreSQL<small>+ Redis</small></div>
            </div>
          </div>
        </section>
      </div>

      <section class="section-block">
        <div class="section-heading"><div><h2>واجهات الـ API المستهدفة</h2><p>هذه هي الصورة النهائية التي تبني إليها خلال المسار.</p></div></div>
        <div class="table-wrap endpoint-table">
          <table>
            <thead><tr><th>Method</th><th>المسار</th><th>الوظيفة</th></tr></thead>
            <tbody>${endpoints
              .map(([method, path, description]) => `<tr><td><code>${method}</code></td><td><code>${path}</code></td><td>${description}</td></tr>`)
              .join("")}</tbody>
          </table>
        </div>
      </section>

      <section class="milestones">
        <h2>خطوات المشروع</h2>
        <p>علّم كل مهمة أنجزتها. التقدم هنا هو نفسه المحفوظ داخل الدروس.</p>
        ${modules
          .map((mod, index) => {
            const count = projectTaskCount(mod);
            const lessons = mod.lessons.filter((lesson) => lesson.capstone?.tasks?.length);
            if (!lessons.length) return "";
            return `<details class="milestone" ${index === 0 ? "open" : ""}>
              <summary>
                <span class="milestone-index">${String(index + 1).padStart(2, "0")}</span>
                <span class="milestone-title">${esc(mod.title)}<small>${esc(mod.tagline)}</small></span>
                <span class="milestone-count" data-milestone-count="${mod.id}">${count.done}/${count.total}</span>
                ${ICONS.chevron}
              </summary>
              <div class="milestone-body">
                ${lessons
                  .map((lesson) => {
                    const entry = A.lessonState(lesson.id);
                    return `<div class="project-step" style="border:0;border-radius:0;padding:10px 0">
                      <div class="project-step-head">
                        <div>
                          <h3 style="font-size:14px">${esc(lesson.capstone.title)}</h3>
                          <p>${lesson.capstone.goal || ""}</p>
                        </div>
                        <a href="#/lesson/${encodeURIComponent(lesson.id)}">افتح الدرس</a>
                      </div>
                      <ul class="task-list">
                        ${(lesson.capstone.tasks || [])
                          .map(
                            (task, taskIndex) => `<li>
                              <label class="task">
                                <input type="checkbox" data-task data-lesson="${lesson.id}" data-task-index="${taskIndex}" ${entry.tasks[taskIndex] ? "checked" : ""} />
                                <span class="task-box">${ICONS.check}</span>
                                <span class="task-text">${task}</span>
                              </label>
                            </li>`
                          )
                          .join("")}
                      </ul>
                    </div>`;
                  })
                  .join("")}
              </div>
            </details>`;
          })
          .join("")}
      </section>
    </div>`;
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  /* -------------------------------- المصادر -------------------------------- */

  function renderSources() {
    currentPage = "sources";
    currentLessonId = null;
    document.body.classList.remove("with-sidebar");
    setActiveNav("sources");
    document.title = "المراجع — Souq Academy";
    setCrumbs([{ label: "المسار", href: "#/home" }, { label: "المراجع" }]);
    updateProgressUI();

    const groups = [
      {
        title: "Microsoft Learn — ASP.NET Core و.NET",
        items: [
          ["ASP.NET Core documentation", "https://learn.microsoft.com/aspnet/core/"],
          ["Minimal APIs", "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/"],
          ["Middleware", "https://learn.microsoft.com/aspnet/core/fundamentals/middleware/"],
          ["Dependency injection", "https://learn.microsoft.com/aspnet/core/fundamentals/dependency-injection/"],
          ["Configuration", "https://learn.microsoft.com/aspnet/core/fundamentals/configuration/"],
          [".NET 10 — What's new", "https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/overview"],
        ],
      },
      {
        title: "البيانات والوصول إلى قواعد البيانات",
        items: [
          ["Entity Framework Core", "https://learn.microsoft.com/ef/core/"],
          ["EF Core performance", "https://learn.microsoft.com/ef/core/performance/"],
          ["Migrations", "https://learn.microsoft.com/ef/core/managing-schemas/migrations/"],
          ["Transactions", "https://learn.microsoft.com/ef/core/saving/transactions/"],
        ],
      },
      {
        title: "الأمان والجودة",
        items: [
          ["ASP.NET Core security", "https://learn.microsoft.com/aspnet/core/security/"],
          ["JWT bearer authentication", "https://learn.microsoft.com/aspnet/core/security/authentication/configure-jwt-bearer-authentication/"],
          ["Integration tests", "https://learn.microsoft.com/aspnet/core/test/integration-tests/"],
          ["OWASP API Security Top 10", "https://owasp.org/API-Security/editions/2023/en/0x00-header/"],
          ["Twelve-Factor App", "https://12factor.net/"],
        ],
      },
      {
        title: "الأداء والنشر",
        items: [
          ["ASP.NET Core performance", "https://learn.microsoft.com/aspnet/core/performance/"],
          ["Output caching", "https://learn.microsoft.com/aspnet/core/performance/caching/output/"],
          ["Host and deploy", "https://learn.microsoft.com/aspnet/core/host-and-deploy/"],
          ["Docker images for ASP.NET Core", "https://learn.microsoft.com/aspnet/core/host-and-deploy/docker/building-net-docker-images/"],
          [".NET architecture guides", "https://learn.microsoft.com/dotnet/architecture/"],
        ],
      },
      {
        title: "خرائط الطريق",
        items: [
          ["roadmap.sh — ASP.NET Core", "https://roadmap.sh/aspnet-core"],
          ["roadmap.sh — Backend", "https://roadmap.sh/backend"],
          ["roadmap.sh — Docker", "https://roadmap.sh/docker"],
          ["roadmap.sh — SQL", "https://roadmap.sh/sql"],
        ],
      },
    ];

    main.innerHTML = `<div class="sources-page">
      <span class="eyebrow">المراجع</span>
      <h1>مصادر بُنيت عليها الخريطة</h1>
      <p class="sources-intro">
        المحتوى في هذه الأكاديمية مكتوب خصيصًا لها، لكن تسلسل الموضوعات مبني على
        وثائق Microsoft الرسمية وخرائط roadmap.sh. هذه ليست قراءة إضافية واجبة؛
        هي مراجع للتحقق والتوسّع عندما تريد الرجوع إلى المصدر الأصلي.
      </p>
      ${groups
        .map(
          (group) => `<section class="source-group">
            <h2>${group.title}</h2>
            <ul class="source-list">
              ${group.items
                .map(
                  ([label, href]) => `<li><a href="${href}" target="_blank" rel="noopener noreferrer"><span>${label}</span><small>${new URL(href).hostname.replace("www.", "")}</small>${ICONS.external}</a></li>`
                )
                .join("")}
            </ul>
          </section>`
        )
        .join("")}
    </div>`;
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  /* -------------------------------- غير موجود -------------------------------- */

  function renderNotFound() {
    currentPage = "notfound";
    currentLessonId = null;
    document.body.classList.remove("with-sidebar");
    setActiveNav("");
    document.title = "الصفحة غير موجودة — Souq Academy";
    setCrumbs([{ label: "المسار", href: "#/home" }, { label: "غير موجود" }]);
    updateProgressUI();
    main.innerHTML = `<section class="notfound">
      <span class="eyebrow">404</span>
      <h1>هذه الصفحة أو الدرس غير موجود</h1>
      <p>ربما تغيّر الرابط أو أن الرابط من نسخة أقدم من الأكاديمية.</p>
      <a class="btn primary" href="#/home">العودة إلى خريطة المسار</a>
    </section>`;
    closeSidebar();
  }

  /* --------------------------------- الراوتر --------------------------------- */

  function route() {
    const raw = window.location.hash.replace(/^#\/?/, "");
    const [head, tail] = raw.split("/");
    closeSidebar();

    if (!raw || head === "home") return renderHome();
    if (head === "lesson" && tail) return renderLesson(decodeURIComponent(tail));
    if (head === "project") return renderProject();
    if (head === "sources") return renderSources();
    return renderNotFound();
  }

  /* --------------------------------- الأحداث --------------------------------- */

  function askConfirm(title, body, onConfirm) {
    const dialog = document.getElementById("confirmDialog");
    document.getElementById("dialogTitle").textContent = title;
    document.getElementById("dialogBody").textContent = body;
    dialog._onConfirm = onConfirm;
    dialog.showModal();
  }

  function wireEvents() {
    window.addEventListener("hashchange", route);

    document.addEventListener("click", (event) => {
      if (event.target.closest("#themeToggle")) {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        A.setTheme(next);
        applyTheme(next);
        toast(next === "dark" ? "تم تفعيل الوضع الداكن." : "تم تفعيل الوضع الفاتح.");
        return;
      }

      const navLesson = event.target.closest(".nav-lesson");
      if (navLesson) {
        closeSidebar();
        return;
      }

      const copy = event.target.closest("[data-copy]");
      if (copy) {
        const figure = copy.closest(".code-block");
        const code = figure?.querySelector("code");
        if (code) {
          const text = code.textContent;
          const done = () => {
            const label = copy.querySelector("span");
            if (label) label.textContent = "تم النسخ";
            setTimeout(() => {
              if (label) label.textContent = "نسخ";
            }, 1500);
          };
          if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(text).then(done).catch(() => toast("تعذّر النسخ التلقائي — حدّد الكود يدويًا.", "warn"));
          } else {
            toast("تعذّر النسخ التلقائي — حدّد الكود يدويًا.", "warn");
          }
        }
        return;
      }

      const quizButton = event.target.closest("[data-quiz-option]");
      if (quizButton) {
        const lesson = A.getLesson(quizButton.dataset.lesson);
        if (!lesson) return;
        const questionIndex = Number(quizButton.dataset.q);
        const optionIndex = Number(quizButton.dataset.opt);
        const correct = optionIndex === lesson.quiz[questionIndex].answer;
        A.setQuizAnswer(lesson.id, questionIndex, optionIndex, correct);
        refreshQuiz(lesson);
        toast(correct ? "إجابة صحيحة. +10 XP" : "إجابة غير صحيحة — اقرأ التفسير بالأسفل.", correct ? "ok" : "warn");
        return;
      }

      const retry = event.target.closest("[data-retry]");
      if (retry) {
        const lesson = A.getLesson(retry.dataset.lesson);
        if (!lesson) return;
        const entry = A.lessonState(lesson.id);
        delete entry.quiz[Number(retry.dataset.q)];
        A.saveState();
        refreshQuiz(lesson);
        return;
      }

      const complete = event.target.closest("[data-complete]");
      if (complete) {
        const lesson = A.getLesson(complete.dataset.lesson);
        if (!lesson) return;
        const nowDone = A.toggleComplete(lesson.id);
        refreshDynamic(lesson);
        toast(nowDone ? "تم إكمال الدرس — تقدمك محفوظ." : "تم إلغاء تحديد الدرس.", nowDone ? "ok" : "warn");
        return;
      }

      const scrollButton = event.target.closest("[data-scroll]");
      if (scrollButton) {
        const target = document.getElementById(scrollButton.dataset.scroll);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }

      if (event.target.closest("#menuBtn")) {
        openSidebar();
        return;
      }
      if (event.target.closest("#sidebarClose") || event.target === backdrop) {
        closeSidebar();
        return;
      }
      if (event.target.closest("#resetBtn")) {
        askConfirm("تصفير كل التقدم؟", "سيتم حذف الدروس المكتملة، نتائج الاختبارات، وخطوات المشروع. لا يمكن التراجع.", () => {
          A.resetProgress();
          route();
          toast("تم تصفير التقدم. بداية جديدة.", "warn");
        });
        return;
      }
      if (event.target.closest("#exportBtn")) {
        const blob = new Blob([A.exportProgress()], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "souq-academy-progress.json";
        anchor.click();
        URL.revokeObjectURL(url);
        toast("تم تصدير ملف التقدم.");
        return;
      }
      if (event.target.closest("#importBtn")) {
        document.getElementById("importFile").click();
        return;
      }
    });

    document.addEventListener("change", (event) => {
      const task = event.target.closest("[data-task]");
      if (task) {
        const lesson = A.getLesson(task.dataset.lesson);
        if (!lesson) return;
        A.setTask(lesson.id, Number(task.dataset.taskIndex), task.checked);
        if (currentPage === "project") {
          updateProgressUI();
          updateProjectProgressUI();
        } else {
          refreshDynamic(lesson);
        }
        if (task.checked) toast("خطوة مشروع مكتملة.");
        return;
      }

      if (event.target.id === "importFile") {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          try {
            A.importProgress(String(reader.result));
            applyTheme(A.getState().theme);
            route();
            toast("تم استيراد التقدم بنجاح.");
          } catch (error) {
            toast("ملف غير صالح: " + error.message, "warn");
          }
        };
        reader.readAsText(file);
        event.target.value = "";
      }
    });

    searchInput.addEventListener("input", () => renderSearchResults(searchInput.value));
    searchInput.addEventListener("focus", () => {
      if (searchInput.value.trim()) renderSearchResults(searchInput.value);
    });
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        searchInput.value = "";
        hideSearchResults();
        searchInput.blur();
      }
      if (event.key === "Enter") {
        const first = searchResults.querySelector("a");
        if (first) {
          first.click();
          searchInput.value = "";
          hideSearchResults();
        }
      }
    });
    searchResults.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        searchInput.value = "";
        hideSearchResults();
      }
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".search-box")) hideSearchResults();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && document.activeElement !== searchInput && !/input|textarea|select/i.test(document.activeElement.tagName)) {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
      if (event.key === "Escape") closeSidebar();
    });

    const dialog = document.getElementById("confirmDialog");
    dialog.addEventListener("close", () => {
      if (dialog.returnValue === "confirm" && dialog._onConfirm) dialog._onConfirm();
      dialog._onConfirm = null;
    });
  }

  /* --------------------------------- التشغيل --------------------------------- */

  applyTheme(A.getState().theme);
  A.registerVisit();
  wireEvents();
  route();
  updateProgressUI();
})();
