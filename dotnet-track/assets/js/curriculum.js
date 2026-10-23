/** Curriculum loading + lookup helpers (pure data, no rendering). */
import { normalizeAr } from "./util.js";

const CURRICULUM_URL = "content/curriculum.json";
const LESSON_URL = (id) => `content/lessons/${id}.json`;

let curriculum = null;
let flat = [];
let byId = new Map();
const contentCache = new Map();

/** Load the curriculum once. */
export const loadCurriculum = async () => {
  if (curriculum) return curriculum;
  const res = await fetch(CURRICULUM_URL, { cache: "no-cache" });
  if (!res.ok) throw new Error(`تعذّر تحميل المنهج: HTTP ${res.status}`);
  curriculum = await res.json();

  flat = [];
  byId = new Map();
  for (const stage of curriculum.stages) {
    for (const mod of stage.modules) {
      for (const lesson of mod.lessons) {
        const entry = { ...lesson, stage, module: mod };
        flat.push(entry);
        byId.set(lesson.id, entry);
      }
    }
  }
  return curriculum;
};

export const getCurriculum = () => curriculum;
export const meta = () => curriculum?.meta || {};
export const stages = () => curriculum?.stages || [];
export const flatLessons = () => flat;
export const allLessonIds = () => flat.map((l) => l.id);
export const getLesson = (id) => byId.get(id) || null;
export const getStage = (id) => stages().find((s) => s.id === id) || null;
export const getModule = (id) => {
  for (const s of stages()) {
    const m = s.modules.find((x) => x.id === id);
    if (m) return { ...m, stage: s };
  }
  return null;
};

export const stageLessons = (stageId) => flat.filter((l) => l.stage.id === stageId);
export const moduleLessons = (moduleId) => flat.filter((l) => l.module.id === moduleId);

/** Previous/next lesson in curriculum order. */
export const neighbors = (id) => {
  const idx = flat.findIndex((l) => l.id === id);
  return { prev: idx > 0 ? flat[idx - 1] : null, next: idx >= 0 && idx < flat.length - 1 ? flat[idx + 1] : null, index: idx };
};

/** Load authored lesson content; null when the lesson is still scaffolded. */
export const loadLessonContent = async (id) => {
  if (contentCache.has(id)) return contentCache.get(id);
  try {
    const res = await fetch(LESSON_URL(id), { cache: "no-cache" });
    if (!res.ok) { contentCache.set(id, null); return null; }
    const data = await res.json();
    contentCache.set(id, data);
    return data;
  } catch (err) {
    console.warn("lesson content unavailable:", id, err);
    contentCache.set(id, null);
    return null;
  }
};

/** Client-side search across titles, English titles, summaries and objectives. */
export const search = (query, limit = 40) => {
  const q = normalizeAr(query);
  if (!q) return [];
  const raw = query.trim().toLowerCase();
  const scored = [];

  for (const lesson of flat) {
    const titleN = normalizeAr(lesson.title);
    const titleEn = (lesson.titleEn || "").toLowerCase();
    const summaryN = normalizeAr(lesson.summary);
    const objectives = lesson.objectives.map(normalizeAr).join(" ");
    const stageN = normalizeAr(lesson.stage.title);

    let score = 0;
    if (titleN.includes(q)) score += 12;
    if (titleEn.includes(raw)) score += 12;
    if (lesson.id.includes(raw)) score += 14;
    if (summaryN.includes(q)) score += 6;
    if (objectives.includes(q)) score += 4;
    if (stageN.includes(q)) score += 2;
    if (lesson.kind === "capstone" && q.length > 2) score += 1;
    if (!score) continue;

    scored.push({ lesson, score });
  }

  return scored
    .sort((a, b) => b.score - a.score || a.lesson.id.localeCompare(b.lesson.id))
    .slice(0, limit);
};

/** Aggregate progress numbers for any list of lessons. */
export const totalsFor = (lessons) => ({
  count: lessons.length,
  minutes: lessons.reduce((sum, l) => sum + (l.minutes || 0), 0),
  hours: Math.round((lessons.reduce((sum, l) => sum + (l.minutes || 0), 0) / 60) * 10) / 10,
  authored: lessons.filter((l) => l.hasContent).length,
});
