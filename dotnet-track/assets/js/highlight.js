/**
 * Tiny dependency-free syntax highlighter.
 * Supports the languages this course actually uses: C#, JSON, bash, yaml,
 * XML/csproj, SQL, Dockerfile, HTTP and generic JS/TS. Unknown languages are
 * returned escaped only — never broken.
 */
import { esc } from "./util.js";

const CSHARP_KEYWORDS =
  "abstract as async await base break case catch checked class const continue default delegate do else enum event explicit extern finally fixed for foreach goto if implicit in interface internal is lock namespace new operator out override params private protected public readonly record ref required return sealed sizeof stackalloc static struct switch this throw try typeof unchecked unsafe using var virtual volatile while yield global partial get set init add remove value where not null when nameof field extension";

const CSHARP_TYPES =
  "bool byte char decimal double dynamic float int long nint nuint object sbyte short string uint ulong ushort void Task ValueTask List Dictionary HashSet IEnumerable IQueryable ICollection IServiceProvider DbContext DbSet Guid DateTime DateTimeOffset TimeSpan CancellationToken Exception ArgumentException InvalidOperationException HttpClient ILogger Thread Span Memory ReadOnlySpan Array Func Action StringComparer StringSplitOptions JsonSerializer NumberStyles IHost IApplicationBuilder IServiceCollection WebApplication IOptions";

const JS_KEYWORDS =
  "const let var function return if else for while of in new class extends import export from default async await try catch finally throw typeof instanceof delete yield this null undefined true false switch case break continue do static get set";

const SQL_KEYWORDS =
  "select from where insert into values update set delete create table alter drop index view on join inner left right full outer cross group by order having limit offset distinct as and or not null primary key foreign references unique constraint default check with union all case when then else end begin commit rollback transaction isolation level read committed serializable repeatable desc asc count sum avg min max over partition exists";

const YAML_KEYWORDS = "true false null yes no on off";


/** Turn a space-separated keyword list into a regex alternation. */
const words = (list) => list.trim().split(/\s+/).join("|");

/** Rule tables: [tokenClass, regex]. The regex must be sticky-friendly (no ^ anchors). */
const RULES = {
  csharp: [
    ["com", /\/\/[^\n]*|\/\*[\s\S]*?\*\//y],
    ["str", /\$?@?"(?:[^"\\\n]|\\.|"")*"|'(?:[^'\\\n]|\\.)'/y],
    ["attr", /\[[A-Za-z_][\w.]*(?:\([^\]]*\))?\]/y],
    ["kw", new RegExp(`\\b(?:${words(CSHARP_KEYWORDS)})\\b`, "y")],
    ["type", new RegExp(`\\b(?:${words(CSHARP_TYPES)})\\b`, "y")],
    ["num", /\b\d[\d_]*(?:\.\d+)?(?:[fFdDmMuUlL]{1,2})?\b/y],
    ["fn", /\b[A-Za-z_]\w*(?=\s*\()/y],
    ["pun", /[{}()[\];,.:?]/y],
  ],
  json: [
    ["prop", /"(?:[^"\\]|\\.)*"(?=\s*:)/y],
    ["str", /"(?:[^"\\]|\\.)*"/y],
    ["kw", /\b(?:true|false|null)\b/y],
    ["num", /-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b/y],
    ["pun", /[{}[\],:]/y],
  ],
  bash: [
    ["com", /#[^\n]*/y],
    ["str", /"(?:[^"\\]|\\.)*"|'[^']*'/y],
    ["kw", /\b(?:if|then|else|elif|fi|for|while|do|done|case|esac|function|return|in|export|local|set|shift|trap|sudo)\b/y],
    ["fn", /\b(?:dotnet|docker|kubectl|git|curl|cd|echo|npm|npx|az|helm|psql|redis-cli|make|chmod|mkdir|rm|cp|mv|cat|grep|sed|awk|export|source|apt|brew|ssh|scp|tar|unzip)\b/y],
    ["attr", /\s-{1,2}[A-Za-z][\w-]*/y],
    ["num", /\b\d+\b/y],
    ["type", /\$[A-Za-z_][\w]*|\$\{[^}]*\}/y],
  ],
  yaml: [
    ["com", /#[^\n]*/y],
    ["prop", /^[ \t]*-?[ \t]*[A-Za-z_][\w.-]*(?=\s*:)/my],
    ["str", /"(?:[^"\\]|\\.)*"|'[^']*'/y],
    ["kw", new RegExp(`\\b(?:${words(YAML_KEYWORDS)})\\b`, "y")],
    ["num", /-?\b\d+(?:\.\d+)?\b/y],
    ["type", /\$\{\{[^}]*\}\}|\$[A-Za-z_][\w.]*/y],
    ["pun", /[:\-|>*&]/y],
  ],
  xml: [
    ["com", /<!--[\s\S]*?-->/y],
    ["str", /"(?:[^"\\]|\\.)*"|'[^']*'/y],
    ["attr", /\b[A-Za-z_][\w.:-]*(?==)/y],
    ["kw", /<\/?[A-Za-z_][\w.:-]*|\/?>/y],
    ["pun", /[=]/y],
  ],
  sql: [
    ["com", /--[^\n]*|\/\*[\s\S]*?\*\//y],
    ["str", /'(?:[^']|'')*'/y],
    ["kw", new RegExp(`\\b(?:${words(SQL_KEYWORDS)})\\b`, "yi")],
    ["type", /\b(?:int|bigint|smallint|tinyint|decimal|numeric|float|real|money|bit|char|varchar|nvarchar|text|date|datetime|datetime2|datetimeoffset|time|timestamp|uniqueidentifier|json|jsonb|uuid|bytea|serial|boolean|xml)\b/yi],
    ["fn", /\b[A-Za-z_]\w*(?=\s*\()/y],
    ["num", /\b\d+(?:\.\d+)?\b/y],
    ["pun", /[(),;.*=<>]/y],
  ],
  dockerfile: [
    ["com", /#[^\n]*/y],
    ["kw", /^\s*(?:FROM|RUN|CMD|LABEL|EXPOSE|ENV|ADD|COPY|ENTRYPOINT|VOLUME|USER|WORKDIR|ARG|ONBUILD|STOPSIGNAL|HEALTHCHECK|SHELL)\b/my],
    ["str", /"(?:[^"\\]|\\.)*"|'[^']*'/y],
    ["attr", /\s-{1,2}[A-Za-z][\w-]*/y],
    ["type", /\$[A-Za-z_][\w]*|\$\{[^}]*\}/y],
    ["num", /\b\d+\b/y],
  ],
  http: [
    ["kw", /^\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|HTTP\/[\d.]+)\b/my],
    ["prop", /^[A-Za-z][\w-]*(?=\s*:)/my],
    ["str", /"(?:[^"\\]|\\.)*"/y],
    ["num", /\b\d{3}\b|\b\d+\b/y],
    ["type", /https?:\/\/[^\s"]+/y],
  ],
  css: [
    ["com", /\/\*[\s\S]*?\*\//y],
    ["str", /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/y],
    ["kw", /@[a-z-]+/y],
    ["type", /--[A-Za-z0-9_-]+/y],
    ["prop", /[A-Za-z-]+(?=\s*:)/y],
    ["fn", /\b[a-z-]+(?=\()/y],
    ["num", /-?\b\d+(?:\.\d+)?(?:rem|em|px|%|s|ms|deg|fr|vh|vw)?\b/y],
    ["pun", /[{}();:,]/y],
  ],
  python: [
    ["com", /#[^\n]*/y],
    ["str", /"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'/y],
    ["attr", /@[A-Za-z_][\w.]*/y],
    ["kw", /\b(?:import|from|as|def|class|return|if|elif|else|for|while|break|continue|pass|try|except|finally|raise|with|yield|lambda|and|or|not|in|is|global|nonlocal|assert|del|async|await|True|False|None|self)\b/y],
    ["type", /\b(?:str|int|float|bool|bytes|list|dict|set|tuple|object|Exception|ValueError|TypeError)\b/y],
    ["fn", /\b[A-Za-z_]\w*(?=\s*\()/y],
    ["num", /\b\d[\d_]*(?:\.\d+)?\b/y],
    ["pun", /[{}()\[\];,.:=?]/y],
  ],
  javascript: [
    ["com", /\/\/[^\n]*|\/\*[\s\S]*?\*\//y],
    ["str", /"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`/y],
    ["kw", new RegExp(`\\b(?:${words(JS_KEYWORDS)})\\b`, "y")],
    ["num", /\b\d+(?:\.\d+)?\b/y],
    ["fn", /\b[A-Za-z_$][\w$]*(?=\s*\()/y],
    ["pun", /[{}()[\];,.:?]/y],
  ],
};

RULES.py = RULES.python;
RULES.scss = RULES.css;
RULES.ts = RULES.javascript;
RULES.js = RULES.javascript;
RULES.cs = RULES.csharp;
RULES.csharp_ = RULES.csharp;
RULES["csproj"] = RULES.xml;
RULES.sh = RULES.bash;
RULES.shell = RULES.bash;
RULES.powershell = RULES.bash;
RULES.ps1 = RULES.bash;
RULES.yml = RULES.yaml;
RULES.html = RULES.xml;

const CLASS = {
  com: "tok-com", str: "tok-str", kw: "tok-kw", type: "tok-type",
  num: "tok-num", fn: "tok-fn", attr: "tok-attr", pun: "tok-pun", prop: "tok-prop",
};

/** Highlight `code` and return an HTML string (already escaped). */
export const highlight = (code, lang = "") => {
  const src = String(code ?? "");
  const key = String(lang || "").toLowerCase().trim();
  const rules = RULES[key] || RULES[key.replace(/^lang-/, "")];
  if (!rules) return esc(src);

  let out = "";
  let buf = "";
  let i = 0;
  const flush = () => {
    if (buf) { out += esc(buf); buf = ""; }
  };
  while (i < src.length) {
    let matched = false;
    for (const [cls, re] of rules) {
      re.lastIndex = i;
      const m = re.exec(src);
      if (m && m[0].length > 0) {
        flush();
        out += `<span class="${CLASS[cls]}">${esc(m[0])}</span>`;
        i += m[0].length;
        matched = true;
        break;
      }
    }
    if (!matched) { buf += src[i]; i += 1; }
  }
  flush();
  return out;
};

/** Language label shown in the code header. */
export const langLabel = (lang = "") => {
  const map = {
    csharp: "C#", cs: "C#", json: "JSON", bash: "Bash", sh: "Shell", yaml: "YAML",
    yml: "YAML", xml: "XML", csproj: "csproj", sql: "SQL", dockerfile: "Dockerfile",
    http: "HTTP", javascript: "JavaScript", js: "JavaScript", ts: "TypeScript",
    python: "Python", py: "Python", css: "CSS", scss: "SCSS", markdown: "Markdown", md: "Markdown", text: "text",
  };
  return map[String(lang).toLowerCase()] || lang || "text";
};
