/* =========================================================================
   Souq Academy — core.js
   سجلّ المنهج + التخزين المحلي + أدوات مساعدة.
   لا يعتمد على أي مكتبة خارجية، ويعمل عبر file:// بدون خادم.
   ========================================================================= */
(function () {
  "use strict";

  /* ----------------------------- سجلّ المنهج ----------------------------- */

  const modules = [];
  const lessons = new Map();

  function addModule(mod) {
    if (!mod || !mod.id || !Array.isArray(mod.lessons)) {
      throw new Error("addModule: وحدة غير صالحة");
    }
    const moduleIndex = modules.length;
    const normalized = {
      ...mod,
      index: moduleIndex,
      lessons: mod.lessons.map((lesson, lessonIndex) => {
        const full = {
          ...lesson,
          moduleId: mod.id,
          moduleTitle: mod.title,
          moduleColor: mod.color || "var(--accent)",
          moduleIndex,
          lessonIndex,
          order: 0,
        };
        lessons.set(full.id, full);
        return full;
      }),
    };
    modules.push(normalized);
    reindex();
    return normalized;
  }

  function reindex() {
    let order = 0;
    for (const mod of modules) {
      for (const lesson of mod.lessons) lesson.order = order++;
    }
  }

  function getLesson(id) {
    return lessons.get(id) || null;
  }

  function getModules() {
    return modules;
  }

  function getLessons() {
    return Array.from(lessons.values()).sort((a, b) => a.order - b.order);
  }

  function getModule(id) {
    return modules.find((m) => m.id === id) || null;
  }

  function getNeighbors(id) {
    const all = getLessons();
    const i = all.findIndex((l) => l.id === id);
    return { prev: i > 0 ? all[i - 1] : null, next: i >= 0 && i < all.length - 1 ? all[i + 1] : null };
  }

  /* ------------------------------ التخزين ------------------------------- */

  const STORAGE_KEY = "souq-academy.dotnet.v1";

  const defaultState = () => ({
    version: 1,
    theme: "light",
    visits: [],
    lastLesson: null,
    lessons: {},
    startedAt: new Date().toISOString(),
  });

  let state = loadState();

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      return {
        ...defaultState(),
        ...parsed,
        lessons: parsed && typeof parsed.lessons === "object" && parsed.lessons ? parsed.lessons : {},
        visits: Array.isArray(parsed?.visits) ? parsed.visits : [],
      };
    } catch (error) {
      console.warn("تعذّر قراءة التقدم المحفوظ، سيتم البدء من جديد.", error);
      return defaultState();
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch (error) {
      console.warn("تعذّر حفظ التقدم في localStorage.", error);
      return false;
    }
  }

  function getState() {
    return state;
  }

  function lessonState(id) {
    if (!state.lessons[id]) {
      state.lessons[id] = { completed: false, quiz: {}, tasks: {}, updatedAt: null };
    }
    const entry = state.lessons[id];
    entry.quiz = entry.quiz || {};
    entry.tasks = entry.tasks || {};
    return entry;
  }

  function isComplete(id) {
    return Boolean(state.lessons[id]?.completed);
  }

  function markComplete(id, value = true) {
    const entry = lessonState(id);
    entry.completed = Boolean(value);
    entry.completedAt = value ? new Date().toISOString() : null;
    entry.updatedAt = new Date().toISOString();
    saveState();
    return entry.completed;
  }

  function toggleComplete(id) {
    return markComplete(id, !isComplete(id));
  }

  function setQuizAnswer(id, questionIndex, pickedIndex, correct) {
    const entry = lessonState(id);
    entry.quiz[questionIndex] = { picked: pickedIndex, correct: Boolean(correct) };
    entry.updatedAt = new Date().toISOString();
    const lesson = getLesson(id);
    if (lesson && lesson.quiz && lesson.quiz.length) {
      const allCorrect = lesson.quiz.every((_, i) => entry.quiz[i] && entry.quiz[i].correct);
      if (allCorrect) {
        entry.completed = true;
        entry.completedAt = entry.completedAt || new Date().toISOString();
      }
    }
    saveState();
    return entry.quiz[questionIndex];
  }

  function setTask(id, taskIndex, done) {
    const entry = lessonState(id);
    entry.tasks[taskIndex] = Boolean(done);
    entry.updatedAt = new Date().toISOString();
    saveState();
  }

  function setLastLesson(id) {
    state.lastLesson = id;
    saveState();
  }

  function setTheme(theme) {
    state.theme = theme;
    saveState();
  }

  function registerVisit() {
    const today = new Date();
    const key = dateKey(today);
    if (!state.visits.includes(key)) {
      state.visits.push(key);
      if (state.visits.length > 400) state.visits = state.visits.slice(-400);
      saveState();
    }
  }

  function dateKey(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function streak() {
    const set = new Set(state.visits);
    let count = 0;
    const cursor = new Date();
    // إذا لم تُسجَّل زيارة اليوم بعد، ابدأ العدّ من أمس.
    if (!set.has(dateKey(cursor))) cursor.setDate(cursor.getDate() - 1);
    while (set.has(dateKey(cursor))) {
      count += 1;
      cursor.setDate(cursor.getDate() - 1);
    }
    return count;
  }

  function totals() {
    const all = getLessons();
    let completed = 0;
    let correct = 0;
    let quizTotal = 0;
    let tasksDone = 0;
    let tasksTotal = 0;

    for (const lesson of all) {
      const entry = state.lessons[lesson.id];
      if (entry?.completed) completed += 1;
      const quiz = lesson.quiz || [];
      quizTotal += quiz.length;
      if (entry?.quiz) {
        for (const value of Object.values(entry.quiz)) if (value && value.correct) correct += 1;
      }
      const capTasks = lesson.capstone?.tasks || [];
      tasksTotal += capTasks.length;
      if (entry?.tasks) {
        for (const value of Object.values(entry.tasks)) if (value) tasksDone += 1;
      }
    }

    const percent = all.length ? Math.round((completed / all.length) * 100) : 0;
    return {
      lessons: all.length,
      completed,
      percent,
      correct,
      quizTotal,
      tasksDone,
      tasksTotal,
      xp: completed * 50 + correct * 10,
    };
  }

  function moduleProgress(moduleId) {
    const mod = getModule(moduleId);
    if (!mod) return { completed: 0, total: 0, percent: 0 };
    const total = mod.lessons.length;
    const completed = mod.lessons.filter((l) => isComplete(l.id)).length;
    return { completed, total, percent: total ? Math.round((completed / total) * 100) : 0 };
  }

  function resetProgress() {
    const theme = state.theme;
    state = defaultState();
    state.theme = theme;
    registerVisit();
    saveState();
  }

  function exportProgress() {
    return JSON.stringify(
      {
        app: "Souq Academy",
        course: "dotnet-backend",
        exportedAt: new Date().toISOString(),
        state,
      },
      null,
      2
    );
  }

  function importProgress(text) {
    const parsed = JSON.parse(text);
    const incoming = parsed && parsed.state ? parsed.state : parsed;
    if (!incoming || typeof incoming !== "object" || typeof incoming.lessons !== "object") {
      throw new Error("الملف لا يحتوي على بيانات تقدم صالحة.");
    }
    state = {
      ...defaultState(),
      ...incoming,
      lessons: incoming.lessons || {},
      visits: Array.isArray(incoming.visits) ? incoming.visits : [],
    };
    saveState();
  }

  /* --------------------------- أدوات النصوص ---------------------------- */

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  const KEYWORDS = {
    csharp:
      "abstract|as|async|await|base|bool|break|byte|case|catch|char|checked|class|const|continue|decimal|default|delegate|do|double|else|enum|event|explicit|extern|false|finally|fixed|float|for|foreach|get|global|goto|if|implicit|in|init|int|interface|internal|is|lock|long|namespace|new|null|object|operator|out|override|params|private|protected|public|readonly|record|ref|required|return|sealed|set|short|sizeof|stackalloc|static|string|struct|switch|this|throw|true|try|typeof|uint|ulong|unchecked|unsafe|ushort|using|var|virtual|void|volatile|when|where|while|yield|with|nameof|typeof",
    bash:
      "dotnet|npm|npx|docker|git|cd|export|echo|curl|sudo|aspnet|run|build|new|add|restore|publish|test|exec|compose",
    json: "true|false|null",
    http: "GET|POST|PUT|PATCH|DELETE|HTTP|Authorization|Content-Type|Bearer",
  };

  function highlight(code, lang) {
    const escaped = escapeHtml(code);
    const keywords = KEYWORDS[lang] || KEYWORDS.csharp;
    const commentPattern =
      lang === "bash" || lang === "dockerfile" || lang === "yaml" ? "#[^\\n]*" : "\\/\\/[^\\n]*|\\/\\*[\\s\\S]*?\\*\\/";

    const pattern = new RegExp(
      `(${commentPattern})|("(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*')|\\b(${keywords})\\b|\\b(\\d+(?:\\.\\d+)?[fmdL]?)\\b|\\b([A-Z][A-Za-z0-9_]*)\\b`,
      "g"
    );

    return escaped.replace(pattern, (match, comment, str, keyword, number, type) => {
      if (comment) return `<span class="tok-comment">${comment}</span>`;
      if (str) return `<span class="tok-string">${str}</span>`;
      if (keyword) return `<span class="tok-keyword">${keyword}</span>`;
      if (number) return `<span class="tok-number">${number}</span>`;
      if (type) return `<span class="tok-type">${type}</span>`;
      return match;
    });
  }

  function slug(value) {
    return String(value)
      .trim()
      .toLowerCase()
      .replace(/[^\p{L}\p{N}]+/gu, "-")
      .replace(/^-+|-+$/g, "");
  }

  function pluralAr(n, one, two, many) {
    if (n === 1) return one;
    if (n === 2) return two;
    return many;
  }

  /* ------------------------------ التصدير ------------------------------- */

  window.Academy = {
    addModule,
    getModules,
    getModule,
    getLessons,
    getLesson,
    getNeighbors,
    getState,
    lessonState,
    isComplete,
    markComplete,
    toggleComplete,
    setQuizAnswer,
    setTask,
    setLastLesson,
    setTheme,
    registerVisit,
    streak,
    totals,
    moduleProgress,
    resetProgress,
    exportProgress,
    importProgress,
    saveState,
    escapeHtml,
    highlight,
    slug,
    pluralAr,
  };
})();
