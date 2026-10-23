#!/usr/bin/env node
/**
 * Local server for the .NET track app — zero dependencies (Node 18+).
 *
 *   node server.mjs            # http://127.0.0.1:8123
 *   PORT=9000 node server.mjs
 *
 * Serves the static app and mirrors progress to progress.json.
 */
import { createServer } from "node:http";
import { readFile, writeFile, rename, stat } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)));
const PROGRESS_PATH = join(ROOT, "progress.json");
const PORT = Number(process.env.PORT || process.argv[2] || 8123);
const HOST = process.env.HOST || "0.0.0.0";
const MAX_BODY = 4 * 1024 * 1024;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
};

const send = (res, status, body, type = "application/json; charset=utf-8") => {
  res.writeHead(status, {
    "Content-Type": type,
    "Cache-Control": "no-store, must-revalidate",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
};

const sendJson = (res, status, payload) => send(res, status, JSON.stringify(payload));

/** Resolve a URL path to a file inside ROOT, refusing traversal. */
const safePath = (urlPath) => {
  const decoded = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  const relative = normalize(decoded).replace(/^(\.\.[/\\])+/, "").replace(/^[/\\]+/, "");
  const full = join(ROOT, relative);
  if (full !== ROOT && !full.startsWith(ROOT + sep)) return null;
  return full;
};

const readBody = (req) =>
  new Promise((resolveBody, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) { reject(new Error("payload too large")); req.destroy(); return; }
      chunks.push(chunk);
    });
    req.on("end", () => resolveBody(Buffer.concat(chunks)));
    req.on("error", reject);
  });

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  // ---- progress API ---------------------------------------------------
  if (url.pathname.replace(/\/+$/, "") === "/api/progress") {
    if (req.method === "GET") {
      try {
        const raw = await readFile(PROGRESS_PATH, "utf8");
        send(res, 200, raw);
      } catch {
        sendJson(res, 200, { version: 2, lessons: {}, notes: {}, bookmarks: [], activity: [] });
      }
      return;
    }
    if (req.method === "POST") {
      try {
        const raw = await readBody(req);
        const data = JSON.parse(raw.toString("utf8"));
        if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("progress must be a JSON object");
        const tmp = `${PROGRESS_PATH}.tmp`;
        await writeFile(tmp, `${JSON.stringify(data, null, 2)}\n`, "utf8");
        await rename(tmp, PROGRESS_PATH);
        const lessons = Object.keys(data.lessons || {}).length;
        const done = Object.values(data.lessons || {}).filter((l) => l?.status === "done").length;
        sendJson(res, 200, { ok: true, file: "progress.json", lessons, done });
      } catch (err) {
        sendJson(res, 400, { ok: false, error: String(err?.message || err) });
      }
      return;
    }
    if (req.method === "OPTIONS") {
      res.writeHead(204, { Allow: "GET, POST, OPTIONS" });
      res.end();
      return;
    }
    sendJson(res, 405, { ok: false, error: "method not allowed" });
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    sendJson(res, 405, { ok: false, error: "method not allowed" });
    return;
  }

  // ---- static files ---------------------------------------------------
  let filePath = safePath(url.pathname);
  if (!filePath) { sendJson(res, 403, { ok: false, error: "forbidden" }); return; }

  try {
    const info = await stat(filePath);
    if (info.isDirectory()) filePath = join(filePath, "index.html");
  } catch {
    filePath = join(ROOT, "index.html"); // SPA-style fallback
  }

  try {
    const buf = await readFile(filePath);
    const type = MIME[extname(filePath).toLowerCase()] || "application/octet-stream";
    send(res, 200, buf, type);
  } catch {
    send(res, 404, "Not Found", "text/plain; charset=utf-8");
  }
});

server.listen(PORT, HOST, () => {
  const shown = HOST === "0.0.0.0" || HOST === "::" ? "127.0.0.1" : HOST;
  console.log(`مسار .NET — التطبيق شغال على  http://${shown}:${PORT}`);
  console.log(`  الجذر: ${ROOT}`);
  console.log(`  التقدّم: ${PROGRESS_PATH}`);
  console.log("  اضغط Ctrl+C للإيقاف");
});
