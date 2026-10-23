/**
 * Markdown-lite renderer used for lesson prose.
 * Supports: headings, paragraphs, lists (one nesting level), ordered lists,
 * blockquotes, tables, horizontal rules, and inline bold/italic/code/links.
 * Everything is escaped first, so lesson JSON can never inject HTML.
 */
import { esc } from "./util.js";
import { highlight, langLabel } from "./highlight.js";

const inline = (text) => {
  let out = "";
  let rest = String(text ?? "");

  // Protect inline code spans first so their content is never reformatted.
  const codes = [];
  rest = rest.replace(/`([^`]+)`/g, (_, body) => {
    codes.push(body);
    return `\u0000${codes.length - 1}\u0000`;
  });

  out = esc(rest);

  // links [label](url) — url must be http(s), mailto or a relative path
  out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, label, url) => {
    const safe = /^(https?:|mailto:|\/|#)/i.test(url) ? url : "#";
    const external = /^https?:/i.test(url);
    return `<a href="${safe}"${external ? ' target="_blank" rel="noopener noreferrer"' : ""}>${label}</a>`;
  });

  out = out
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>")
    .replace(/&lt;([A-Za-z][\w.&lt;&gt;]*)&gt;/g, "<code>&lt;$1&gt;</code>");

  // Restore inline code.
  out = out.replace(/\u0000(\d+)\u0000/g, (_, idx) => `<code>${esc(codes[Number(idx)])}</code>`);
  return out;
};

const isTableSeparator = (line) => /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(line) && line.includes("-");

const splitRow = (line) =>
  line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

/** Render a markdown-lite string to HTML. */
export const md = (source) => {
  const lines = String(source ?? "").replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;

  const flushList = (items, ordered) => {
    if (!items.length) return;
    const tag = ordered ? "ol" : "ul";
    out.push(`<${tag}>` + items.map((it) => `<li>${inline(it)}</li>`).join("") + `</${tag}>`);
    items.length = 0;
  };

  let bullets = [];
  let numbers = [];

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) { flushList(bullets, false); flushList(numbers, true); i += 1; continue; }

    // fenced code block ```lang ... ```
    const fence = /^\s*```([\w+#.-]*)\s*$/.exec(line);
    if (fence) {
      flushList(bullets, false); flushList(numbers, true);
      const lang = fence[1] || "";
      const buf = [];
      i += 1;
      while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) { buf.push(lines[i]); i += 1; }
      i += 1; // consume the closing fence (or end of input)
      out.push(
        `<div class="code"><div class="code__head"><div class="code__title">` +
        `<span class="code__lang">${esc(langLabel(lang))}</span></div></div>` +
        `<pre><code>${highlight(buf.join("\n"), lang)}</code></pre></div>`,
      );
      continue;
    }

    // horizontal rule
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushList(bullets, false); flushList(numbers, true);
      out.push("<hr />"); i += 1; continue;
    }

    // heading
    const heading = /^(#{1,6})\s+(.*)$/.exec(trimmed);
    if (heading) {
      flushList(bullets, false); flushList(numbers, true);
      const level = Math.min(6, Math.max(2, heading[1].length));
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      i += 1; continue;
    }

    // table
    if (trimmed.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      flushList(bullets, false); flushList(numbers, true);
      const head = splitRow(trimmed);
      const rows = [];
      i += 2;
      while (i < lines.length && lines[i].trim().includes("|")) { rows.push(splitRow(lines[i])); i += 1; }
      out.push(
        "<div style='overflow-x:auto'><table class='tbl'><thead><tr>" +
        head.map((c) => `<th>${inline(c)}</th>`).join("") +
        "</tr></thead><tbody>" +
        rows.map((r) => "<tr>" + r.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>").join("") +
        "</tbody></table></div>",
      );
      continue;
    }

    // blockquote
    if (trimmed.startsWith(">")) {
      flushList(bullets, false); flushList(numbers, true);
      const buf = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        buf.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      out.push(`<blockquote>${inline(buf.join(" "))}</blockquote>`);
      continue;
    }

    // ordered list
    const ordered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (ordered) { flushList(bullets, false); numbers.push(ordered[1]); i += 1; continue; }

    // unordered list (with one nesting level rendered as a sub-list marker)
    const bullet = /^\s*[-*+]\s+(.*)$/.exec(line);
    if (bullet) {
      flushList(numbers, true);
      const indent = line.match(/^\s*/)[0].length;
      bullets.push(indent >= 2 ? `↳ ${bullet[1]}` : bullet[1]);
      i += 1; continue;
    }

    // paragraph (gather consecutive plain lines)
    flushList(bullets, false); flushList(numbers, true);
    const para = [trimmed];
    i += 1;
    while (i < lines.length) {
      const next = lines[i].trim();
      if (!next || next.startsWith("```") || /^(#{1,6}\s|>|[-*+]\s|\d+[.)]\s|(-{3,})$)/.test(next) || (next.includes("|") && isTableSeparator(lines[i + 1] || ""))) break;
      para.push(next);
      i += 1;
    }
    out.push(`<p>${inline(para.join(" "))}</p>`);
  }

  flushList(bullets, false);
  flushList(numbers, true);
  return out.join("\n");
};

export { inline as mdInline };
