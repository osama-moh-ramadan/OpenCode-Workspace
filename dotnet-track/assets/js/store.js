/**
 * Progress store: localStorage first, with an optional local file mirror
 * (progress.json) written through the bundled dev server.
 *
 * Nothing leaves the machine: there is no account, no analytics, no network
 * call other than the same-origin /api/progress endpoint.
 */

const KEY = "dotnet-track.progress.v2";
const ENDPOINT = "api/progress";

const emptyState = () => ({
  version: 2,
  updatedAt: null,
  lessons: {},      // id -> { status, completedAt, updatedAt, quiz: {answers:{i:idx}, score, total}, tasks: {taskId:true}, minutes }
  notes: {},        // id -> { text, updatedAt }
  bookmarks: [],    // [lessonId]
  activity: [],     // ["YYYY-MM-DD"] distinct days with any progress
  settings: { theme: "dark" },
});

const listeners = new Set();
const notify = () => listeners.forEach((fn) => { try { fn(state); } catch (e) { console.error(e); } });

let state = emptyState();
let serverAvailable = false;
let saveTimer = null;

/* ------------------------------------------------------------------ helpers */

const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

const isBrowser = () => typeof window !== "undefined" && typeof localStorage !== "undefined";

const clone = (v) => JSON.parse(JSON.stringify(v));

const touchActivity = () => {
  const day = todayStr();
  if (!state.activity.includes(day)) {
    state.activity.push(day);
    if (state.activity.length > 400) state.activity = state.activity.slice(-400);
  }
};

/* --------------------------------------------------------------- persistence */

const readLocal = () => {
  if (!isBrowser()) return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return { ...emptyState(), ...parsed, settings: { ...emptyState().settings, ...(parsed.settings || {}) } };
  } catch (err) {
    console.warn("progress: unreadable localStorage entry", err);
    return null;
  }
};

const writeLocal = () => {
  if (!isBrowser()) return;
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch (err) {
    console.warn("progress: localStorage write failed", err);
  }
};

/** Merge another state into the current one, newest per-entry wins. */
export const mergeState = (incoming) => {
  if (!incoming || typeof incoming !== "object") return false;
  const base = { ...emptyState(), ...incoming };
  const newer = (a, b) => new Date(a?.updatedAt || 0) >= new Date(b?.updatedAt || 0) ? a : b;
  let changed = false;

  for (const [id, entry] of Object.entries(base.lessons || {})) {
    const mine = state.lessons[id];
    const winner = newer(mine, entry);
    if (winner === entry && JSON.stringify(mine) !== JSON.stringify(entry)) changed = true;
    state.lessons[id] = winner || entry;
  }
  for (const [id, note] of Object.entries(base.notes || {})) {
    const mine = state.notes[id];
    const winner = newer(mine, note);
    if (winner === note && (mine?.text || "") !== (note?.text || "")) changed = true;
    state.notes[id] = winner || note;
  }
  const marks = new Set(state.bookmarks);
  for (const id of base.bookmarks || []) {
    if (!marks.has(id)) { marks.add(id); changed = true; }
  }
  state.bookmarks = [...marks];

  const days = new Set(state.activity);
  for (const day of base.activity || []) if (!days.has(day)) { days.add(day); changed = true; }
  state.activity = [...days].sort();

  if (base.settings?.theme && base.settings.theme !== state.settings.theme && !state.updatedAt) {
    state.settings.theme = base.settings.theme;
    changed = true;
  }
  return changed;
};

const pushToServer = async () => {
  if (!serverAvailable) return false;
  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    return res.ok;
  } catch {
    serverAvailable = false;
    return false;
  }
};

const pullFromServer = async () => {
  try {
    const res = await fetch(ENDPOINT, { headers: { Accept: "application/json" } });
    if (!res.ok) return false;
    serverAvailable = true;
    const data = await res.json();
    if (data && data.version) return mergeState(data);
    return false;
  } catch {
    serverAvailable = false;
    return false;
  }
};

/** Debounced save: always local, mirrored to progress.json when a server runs. */
export const save = ({ immediate = false } = {}) => {
  state.updatedAt = new Date().toISOString();
  writeLocal();
  clearTimeout(saveTimer);
  const doPush = () => { void pushToServer(); };
  if (immediate) doPush();
  else saveTimer = setTimeout(doPush, 600);
};

/* -------------------------------------------------------------- initial load */

export const initStore = async () => {
  state = readLocal() || emptyState();
  const merged = await pullFromServer();
  if (merged) { save(); notify(); }
  return { state, serverAvailable };
};

/* ------------------------------------------------------------------ selectors */

export const getState = () => state;
export const isServerMode = () => serverAvailable;

export const lessonState = (id) => state.lessons[id] || null;

export const isDone = (id) => state.lessons[id]?.status === "done";

export const doneCount = (ids) => ids.filter(isDone).length;

export const stats = (allLessonIds) => {
  const total = allLessonIds.length;
  const done = doneCount(allLessonIds);
  const minutesDone = allLessonIds.reduce((sum, id) => sum + (isDone(id) ? (state.lessons[id]?.minutes || 0) : 0), 0);
  return { total, done, remaining: total - done, pct: total ? Math.round((done / total) * 100) : 0, minutesDone };
};

export const streak = () => {
  const days = new Set(state.activity);
  if (!days.size) return { current: 0, longest: 0, todayActive: false };
  const sorted = [...days].sort();
  let longest = 1;
  let run = 1;
  for (let i = 1; i < sorted.length; i += 1) {
    const prev = new Date(sorted[i - 1] + "T00:00:00");
    const cur = new Date(sorted[i] + "T00:00:00");
    const diff = Math.round((cur - prev) / 86400000);
    if (diff === 1) { run += 1; longest = Math.max(longest, run); }
    else if (diff > 1) run = 1;
  }
  const today = todayStr();
  const yesterday = (() => {
    const d = new Date(); d.setDate(d.getDate() - 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  })();
  let current = 0;
  if (days.has(today) || days.has(yesterday)) {
    let cursor = days.has(today) ? new Date(today + "T00:00:00") : new Date(yesterday + "T00:00:00");
    for (;;) {
      const key = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`;
      if (!days.has(key)) break;
      current += 1;
      cursor.setDate(cursor.getDate() - 1);
    }
  }
  return { current, longest, todayActive: days.has(today) };
};

/** Next lesson to work on: first not-done lesson in curriculum order. */
export const nextLessonId = (orderedIds) => orderedIds.find((id) => !isDone(id)) || orderedIds[0] || null;

/* ------------------------------------------------------------------- mutators */

const ensureLesson = (id, minutes = 0) => {
  if (!state.lessons[id]) state.lessons[id] = { status: "todo", updatedAt: null, minutes };
  if (minutes && !state.lessons[id].minutes) state.lessons[id].minutes = minutes;
  return state.lessons[id];
};

export const setLessonDone = (id, done, minutes = 0) => {
  const entry = ensureLesson(id, minutes);
  entry.status = done ? "done" : "todo";
  entry.completedAt = done ? new Date().toISOString() : null;
  entry.updatedAt = new Date().toISOString();
  if (done) touchActivity();
  save();
  notify();
  return entry;
};

export const setQuizResult = (id, { answers, score, total }) => {
  const entry = ensureLesson(id);
  entry.quiz = { answers, score, total, updatedAt: new Date().toISOString() };
  entry.updatedAt = new Date().toISOString();
  touchActivity();
  save();
  notify();
};

export const setTaskDone = (id, taskKey, done) => {
  const entry = ensureLesson(id);
  entry.tasks = { ...(entry.tasks || {}), [taskKey]: !!done };
  entry.updatedAt = new Date().toISOString();
  if (done) touchActivity();
  save();
  notify();
};

export const setNote = (id, text) => {
  if (!text) delete state.notes[id];
  else state.notes[id] = { text, updatedAt: new Date().toISOString() };
  state.updatedAt = new Date().toISOString();
  save();
};

export const toggleBookmark = (id) => {
  const set = new Set(state.bookmarks);
  if (set.has(id)) set.delete(id); else set.add(id);
  state.bookmarks = [...set];
  save();
  notify();
  return set.has(id);
};

export const setTheme = (theme) => {
  state.settings.theme = theme;
  save();
};

export const resetAll = () => {
  const theme = state.settings.theme;
  state = emptyState();
  state.settings.theme = theme;
  save({ immediate: true });
  notify();
};

export const importState = (json) => {
  const data = typeof json === "string" ? JSON.parse(json) : json;
  if (!data || typeof data !== "object") throw new Error("ملف غير صالح");
  const merged = mergeState(data);
  save({ immediate: true });
  notify();
  return merged;
};

export const exportState = () => clone(state);

export const subscribe = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
