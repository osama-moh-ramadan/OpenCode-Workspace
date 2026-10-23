# -*- coding: utf-8 -*-
"""Stage 8 module 1 (part C): s8-m1-l3 (CSS عمليًا + Tailwind v4)."""

TODAY = "2026-10-22"

_L3 = {
    "id": "s8-m1-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "مش محتاج تبقى مصمم عشان تبني واجهة نظيفة — محتاج **نموذجًا عقليًا** لأربع حاجات: صندوق (box model) · تخطيط (Flexbox مقابل Grid) · توكنات تصميم (ألوان ومسافات كمتغيرات) · واستجابة (breakpoints + container queries). الدرس ده بيديك الحد ده بالظبط، ومعاه **Tailwind CSS v4** — اللي اتغير تغييرًا جوهريًا في 2025: الإعداد بقى **CSS-first** (`@theme` بدل `tailwind.config.js`)، والمحرك بقى Rust (Oxide)، والكشف عن الملفات بقى تلقائيًا، والاستعلامات الحاوية (container queries) بقت مدمجة. وهنغطي كمان حاجة أغلب الكورسات بتتجاهلها وهي مهمة جدًا ليك: **الدعم الكامل للاتجاه من اليمين لليسار (RTL)** بالخصائص المنطقية."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Box model", "def": "كل عنصر صندوق من أربع طبقات: **content → padding → border → margin**. مع `box-sizing: border-box` (الافتراضي في Tailwind/Preflight) الـwidth بيشمل padding وborder — وده بيخلي الحسابات منطقية."},
            {"term": "Flow مقابل Flex مقابل Grid", "def": "**Flow** (الافتراضي): عناصر بتتكدس رأسيًا/أفقيًا. **Flexbox**: توزيع في **محور واحد** (صف أو عمود) — مثالي لشريط أدوات أو بطاقة. **Grid**: **محوران** معًا — مثالي لتخطيط الصفحة أو شبكة بطاقات."},
            {"term": "Specificity (الخصوصية)", "def": "ترتيب يحسم التعارض: inline > #id > .class/attribute/pseudo-class > element. ولو اتساوت، **الآخر في الملف بيكسب**. أغلب حروب CSS بتيجي من هنا — وTailwind بيتجنبها لأن كل utility طبقة واحدة."},
            {"term": "Cascade layers", "def": "`@layer` بيحدد أولوية مجموعات القواعد **بغض النظر عن الخصوصية**: الطبقة الأخيرة تكسب. Tailwind v4 بيستخدم layers (theme · base · components · utilities) — عشان كده الـutilities بتتغلب على أنماطك المخصصة."},
            {"term": "Custom properties (متغيرات CSS)", "def": "`--color-brand: #6366f1` ثم `var(--color-brand)`. دي **design tokens** الحقيقية: بتتغير وقت التشغيل (ثيم داكن/فاتح) وبتتوارث. في Tailwind v4 كل توكن في `@theme` هو متغير CSS."},
            {"term": "`rem` مقابل `em` مقابل `px`", "def": "**`rem`** نسبة لجذر المستند (16px افتراضيًا) — الأفضل للمسافات والخطوط لأنه بيحترم تكبير المستخدم. **`em`** نسبة للعنصر الأب (بيتضاعف في التعشيش). **`px`** ثابت — استخدمه للحدود الرفيعة فقط."},
            {"term": "Mobile-first", "def": "تكتب الأنماط الأساسية للشاشة الصغيرة، وتضيف `md:` / `lg:` للأكبر. عكسه (desktop-first بـ`max-width`) بيؤدي لتعارضات أكتر."},
            {"term": "Container queries", "def": "استجابة **لحجم الحاوية** مش حجم الشاشة (`@container` + `@md:`). بتحل مشكلة المكوّن اللي بيتعرض في عمود ضيق وفي صفحة عريضة — مدمجة في Tailwind v4 بلا plugin."},
            {"term": "Utility-first", "def": "أنماط صغيرة ذات غرض واحد في الـHTML (`p-4`, `text-sm`, `grid-cols-3`) بدل classes مخصصة. المكسب: مفيش تنقل بين الملفات ولا أسماء جديدة ولا CSS ميت. الثمن: HTML مزدحم — يُحل بـ`@utility` للمكونات المتكررة."},
            {"term": "Preflight", "def": "إعادة تعيين أساسية بيجيبها Tailwind (margin صفر · `border-box` · حدود بـ`currentColor` · صور block). لازم تعرفها عشان ما تتفاجأش إن عناصر HTML العادية شكلها مختلف."},
            {"term": "الخصائص المنطقية (RTL)", "def": "خصائص بتشتغل بالاتجاه مش بالجهة: `margin-inline-start` بدل `margin-left` · وفي Tailwind: `ms-`/`me-` (margin start/end) · `ps-`/`pe-` · `start-`/`end-` · `text-start` · `border-s` · `rounded-e`. **دي اللي تخلي RTL مجانيًا**."},
            {"term": "`oklch` وP3", "def": "نموذج لوني حديث: `oklch(62% 0.18 250)` أقرب لإدراك العين (نفس الإضاءة = نفس السطوع المُدرك) ويدعم نطاق ألوان أوسع (P3). Tailwind v4 بيستخدمه افتراضيًا في لوحة الألوان."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① الأساس: الصندوق والعرض والخصوصية"},
        {"type": "table", "caption": "خصائص بتحل 80% من مشاكل التخطيط",
         "head": ["الخاصية", "القيم الشائعة", "متى تستخدمها", "الفخّ"],
         "rows": [
             ["`display`", "`block` · `inline` · `inline-block` · `flex` · `grid` · `none`", "تحدد نمط التخطيط للعنصر وأولاده", "`inline` بيتجاهل width/height العمودي — استخدم `inline-block` أو `flex`"],
             ["`box-sizing`", "`border-box` (المطلوب)", "دايمًا — Preflight بيضبطها", "بـ`content-box` إضافة padding بتوسّع العنصر وتكسر التخطيط"],
             ["`position`", "`static` · `relative` · `absolute` · `fixed` · `sticky`", "`relative` كمرجع لـ`absolute` · `sticky` لرأس جدول/شريط", "`absolute` بلا أب `relative` بيتثبت بالمستند كله"],
             ["`gap`", "`gap-4` (1rem)", "مسافة بين عناصر flex/grid — **بدل margins على الأولاد**", "margins على الأولاد بتضيف مسافة زيادة على الحواف"],
             ["`overflow`", "`hidden` · `auto` · `scroll` · `clip`", "حاويات قابلة للتمرير · منع تجاوز", "`overflow: hidden` بيكسر `position: sticky` جواه"],
             ["`width`/`max-width`", "`max-w-md`, `w-full`", "قيّد عرض النص للقراءة المريحة (~65–75 حرفًا)", "`w-full` بلا `max-w` بيخلي الأسطر طويلة جدًا على شاشة كبيرة"],
             ["`aspect-ratio`", "`aspect-video`, `aspect-square`", "صور/بطاقات بأبعاد ثابتة بلا حسابات", "بلا `object-cover` الصورة هتتمدد"],
             ["`z-index`", "`z-10`, `z-50`", "ترتيب الطبقات للعناصر المتمركزة", "بلا `position` ≠ static ما يشتغلش · وتصعيد z-index (1000!) بيضيع النظام"],
         ]},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② Flexbox مقابل Grid — القرار في سطرين"},
        {"type": "callout", "kind": "tip", "title": "القاعدة",
         "md": "**محتوى بيحدد الحجم → Flexbox** (شريط أدوات · قائمة عناصر · أزرار · بطاقة: صورة + نص).\n**حاوية بتحدد الحجم → Grid** (تخطيط الصفحة · شبكة بطاقات · نموذج بحقول وصفوف · لوحة مؤشرات).\n\nولو محتاج الاتنين: **Grid للتخطيط العام وFlex داخل كل خلية** — ده أشهر تركيب في الواجهات الحديثة."},
        {"type": "code", "lang": "text", "title": "Flexbox مقابل Grid — نفس البيانات، أسلوبان", "filename": "docs/css-layout.md", "code": r'''## Flexbox: محور واحد (شريط أدوات + بطاقة)

~~~html
<!-- شريط أدوات: عناصر متباعدة، وزر ثابت في النهاية -->
<div class="flex items-center justify-between gap-3 border-b border-gray-200 p-4">
  <h1 class="text-lg font-semibold">الطلبات</h1>
  <div class="flex items-center gap-2">
    <button class="rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50">تصدير</button>
    <button class="rounded-md bg-brand-600 px-3 py-1.5 text-sm text-white hover:bg-brand-700">
      طلب جديد
    </button>
  </div>
</div>

<!-- بطاقة: صورة + محتوى (اتجاه صف على الشاشات الكبيرة) -->
<article class="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row">
  <img src="…" alt="" class="h-24 w-24 shrink-0 rounded-md object-cover" />
  <div class="flex min-w-0 flex-col gap-1">   <!-- min-w-0 يمنع تجاوز النص -->
    <h2 class="truncate text-base font-medium">اسم المنتج</h2>
    <p class="line-clamp-2 text-sm text-gray-600">وصف قصير…</p>
    <span class="mt-auto text-sm font-semibold">199.99 ج.م</span>
  </div>
</article>
~~~

**خصائص flex الأساسية**: `flex-row/-col` (المحور) · `items-*` (المحاذاة العرضية)
· `justify-*` (المحاذاة على المحور) · `gap-*` · `flex-1` (املأ المتاح)
· `shrink-0` (لا تتقلص) · `flex-wrap` (انزل لسطر جديد).

**فخّ شائع**: عنصر نصي داخل flex بيتجاوز العرض → أضف `min-w-0` على الحاوي
و`truncate` على النص.

## Grid: محوران (تخطيط صفحة + شبكة بطاقات + نموذج)

~~~html
<!-- تخطيط لوحة إدارية: شريط جانبي + محتوى -->
<div class="grid min-h-screen grid-cols-1 md:grid-cols-[16rem_1fr]">
  <aside class="border-e bg-gray-50 p-4">…</aside>   <!-- border-e = منطقي (RTL-safe) -->
  <main class="p-6">…</main>
</div>

<!-- شبكة بطاقات: عدد الأعمدة يستجيب للعرض تلقائيًا -->
<section class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  <!-- بطاقات -->
</section>

<!-- أعمدة «تعبئة تلقائية» بلا breakpoints (أقوى حيلة في Grid) -->
<section class="grid grid-cols-[repeat(auto-fill,minmax(16rem,1fr))] gap-4">…</section>

<!-- نموذج: تسمية + حقل في صفين، وزر يمتد عليهما -->
<form class="grid grid-cols-1 gap-4 sm:grid-cols-2">
  <label class="grid gap-1">
    <span class="text-sm font-medium">الاسم</span>
    <input class="rounded-md border px-3 py-2" name="name" />
  </label>
  <label class="grid gap-1">
    <span class="text-sm font-medium">الهاتف</span>
    <input class="rounded-md border px-3 py-2" name="phone" dir="ltr" />
  </label>
  <button class="rounded-md bg-brand-600 px-4 py-2 text-white sm:col-span-2">حفظ</button>
</form>
~~~

**خصائص grid الأساسية**: `grid-cols-N` / `grid-rows-N` · `col-span-N` / `row-span-N`
· `gap-*` · `grid-cols-[…]` (قيم مخصصة) · `place-items-*` · `auto-rows-*`.

## متى تختار إيه؟
| الحاجة | الاختيار |
|---|---|
| عناصر في صف/عمود بأحجام مختلفة | Flexbox |
| توزيع مساحة بين عنصرين (اسم + زر) | Flexbox (`justify-between`) |
| شبكة بطاقات متساوية | Grid |
| تخطيط صفحة (شريط جانبي + محتوى) | Grid |
| نموذج بتسميات وحقول في أعمدة | Grid |
| محاذاة نص وأيقونة | Flexbox (`items-center gap-2`) |
| عدد أعمدة يعتمد على **عرض المكوّن** | Grid + container query (أسفل) |
'''},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ توكنات التصميم: `@theme` في Tailwind v4"},
        {"type": "code", "lang": "css", "title": "src/styles/app.css — ملف CSS واحد فيه كل الإعداد (v4: CSS-first)", "filename": "src/styles/app.css", "code": r'''/* v4: سطر واحد بدل @tailwind base/components/utilities — ولازم يكون أول شيء */
@import "tailwindcss";

/* مصدر الملفات: v4 بيكشف تلقائيًا، وأضف مسارات صريحة عند الحاجة */
@source "../**/*.{html,ts,tsx,razor}";

/* الوضع الداكن بـdata-attribute بدل prefers-color-scheme (قرار تصميم) */
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

/* ── توكنات التصميم: كل واحد متغير CSS يُستخدم في كل المشروع ───────── */
@theme {
  /* الألوان: الاسم بيولّد utilities (bg-brand-600 · text-brand-600 · border-brand-600) */
  --color-brand-50:  oklch(97% 0.02 250);
  --color-brand-100: oklch(94% 0.04 250);
  --color-brand-300: oklch(82% 0.09 250);
  --color-brand-500: oklch(62% 0.18 250);
  --color-brand-600: oklch(55% 0.19 250);
  --color-brand-700: oklch(47% 0.17 250);
  --color-brand-900: oklch(30% 0.10 250);

  /* ألوان دلالية (semantic) — لا تسميها blue/red بل بالوظيفة */
  --color-surface: #ffffff;
  --color-surface-raised: #f8fafc;
  --color-ink: #0f172a;
  --color-ink-muted: #475569;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-danger: #dc2626;

  /* الخطوط */
  --font-sans: "Inter", "Noto Sans Arabic", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  /* أساس المسافات: v4 بيشتق كل قيم p-/m-/gap- من المتغير ده */
  --spacing: 0.25rem;

  /* الحدود والانحناء */
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;

  /* نقاط توقف إضافية (الافتراضية: sm 40rem · md 48rem · lg 64rem · xl 80rem · 2xl 96rem) */
  --breakpoint-3xl: 120rem;

  /* حركة */
  --ease-snap: cubic-bezier(0.2, 0, 0, 1);
  --animate-fade-in: fade-in 160ms var(--ease-snap);
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: none; }
}

/* ── ثيم داكن: نفس أسماء التوكنات، قيم مختلفة ─────────────────────────── */
[data-theme="dark"] {
  --color-surface: #0b1220;
  --color-surface-raised: #111a2e;
  --color-ink: #e2e8f0;
  --color-ink-muted: #94a3b8;
}

/* ── طبقة أساسية: سلوك عام للعناصر ───────────────────────────────────── */
@layer base {
  html {
    /* دعم RTL/LTR: الاتجاه يُضبط على <html dir="rtl" lang="ar"> */
    -webkit-text-size-adjust: 100%;
  }

  body {
    background-color: var(--color-surface);
    color: var(--color-ink);
    font-family: var(--font-sans);
  }

  /* حلقة تركيز واضحة دائمًا — لا تحذفها أبدًا (a11y) */
  :focus-visible {
    outline: 2px solid var(--color-brand-600);
    outline-offset: 2px;
  }

  /* احترام تفضيل تقليل الحركة */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
}

/* ── مكونات متكررة: @utility في v4 (بدل plugin JS) ───────────────────── */
@utility card {
  border-radius: var(--radius-lg);
  border: 1px solid color-mix(in oklab, var(--color-ink) 12%, transparent);
  background-color: var(--color-surface-raised);
  padding: calc(var(--spacing) * 4);
}

@utility btn-primary {
  display: inline-flex;
  align-items: center;
  gap: calc(var(--spacing) * 2);
  border-radius: var(--radius-md);
  background-color: var(--color-brand-600);
  padding: calc(var(--spacing) * 2) calc(var(--spacing) * 4);
  font-size: var(--text-sm);
  color: white;
  &:hover { background-color: var(--color-brand-700); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

/* لو محتاج @apply في ملف/SFC منفصل (Vue/Svelte) أضف أولًا:
   @reference "../styles/app.css";   — وإلا التوكنات ما تُعرفش */
'''},
        {"type": "table", "caption": "لماذا توكنات بدل قيم ثابتة (المكسب الحقيقي)",
         "head": ["بدون توكنات", "مع توكنات"],
         "rows": [
             ["`#3b82f6` في 40 مكانًا — تغيير العلامة التجارية = بحث واستبدال", "`--color-brand-600` مرة واحدة"],
             ["الوضع الداكن = ملف CSS تاني كامل", "استبدال قيم التوكنات تحت `[data-theme=\"dark\"]`"],
             ["`margin: 16px` و`18px` و`15px` في صفحات مختلفة (فوضى بصرية)", "مقياس مسافات واحد مشتق من `--spacing`"],
             ["ثلاث درجات «رمادي» عشوائية", "`--color-ink` و`--color-ink-muted` بأسماء وظيفية"],
             ["صعوبة مراجعة التصميم", "مراجعة قائمة توكنات واحدة (وتمكن مقارنتها مع Figma/التصميم)"],
         ]},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ Tailwind v4: التثبيت والتغييرات عن v3"},
        {"type": "code", "lang": "bash", "title": "تثبيت Tailwind v4 مع Vite (بلا PostCSS ولا tailwind.config.js)", "filename": "terminal/tailwind-v4.sh", "code": r'''# 1) الحزم: tailwindcss وإضافة Vite
npm install tailwindcss @tailwindcss/vite

# 2) أضف الـplugin لـvite.config.ts
cat > vite.config.ts <<'EOF'
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss()],
  server: { port: 5173, proxy: { "/api": { target: "http://localhost:8080", changeOrigin: true } } },
  build: { target: "es2023", sourcemap: true },
});
EOF

# 3) ملف CSS واحد (بلا @tailwind directives وبلا content array)
mkdir -p src/styles
cat > src/styles/app.css <<'EOF'
@import "tailwindcss";
@theme {
  --color-brand-600: oklch(55% 0.19 250);
  --font-sans: "Inter", "Noto Sans Arabic", system-ui, sans-serif;
}
EOF

# 4) اربطه بنقطة الدخول
#    في main.ts:  import "./styles/app.css";
#    أو في index.html:  <link rel="stylesheet" href="/src/styles/app.css" />

# 5) تحقق
npm run dev          # غيّر class في HTML وشوف التحديث الفوري
npx @tailwindcss/cli --input src/styles/app.css --output /tmp/out.css --minify
wc -c /tmp/out.css   # الناتج لازم يكون صغيرًا (v4 بيولّد المستخدم فقط)

# 6) لو مشروع v3 قائم: أداة الترقية الرسمية (على branch نظيف وراجع الفرق يدويًا)
# npx @tailwindcss/upgrade

# ملاحظة الحزم في v4:
#   Vite      -> @tailwindcss/vite
#   Next.js   -> @tailwindcss/postcss
#   CLI فقط   -> @tailwindcss/cli
#   autoprefixer مش مطلوب (Lightning CSS مدمج)
'''},
        {"type": "table", "caption": "v3 → v4: التغييرات اللي هتقابلك (الحالي 4.3.x في 2026)",
         "head": ["الجانب", "v3", "v4", "ملاحظة عملية"],
         "rows": [
             ["الإعداد", "`tailwind.config.js` (مطلوب)", "`@theme` في CSS (بلا ملف JS افتراضيًا)", "تقدر تحمّل إعداد JS قديم بـ`@config \"./tailwind.config.js\"`"],
             ["نقطة الدخول", "`@tailwind base; @tailwind components; @tailwind utilities;`", "`@import \"tailwindcss\";`", "لازم `@import` **قبل** أي قواعد تانية"],
             ["كشف الملفات", "`content: [...]` يدوي", "**تلقائي** + `@source` لمسارات إضافية", "استخدم `@source` لمجلدات خارج الجذر أو لتوسيع/تضييق المسح"],
             ["البناء", "PostCSS بـJS", "**Oxide (Rust)** + Lightning CSS مدمج", "أسرع بكثير؛ `autoprefixer` و`postcss` مش مطلوبين"],
             ["الإضافات", "`plugins: [require(…)]` في JS", "`@plugin \"@tailwindcss/typography\";` في CSS", "الـAPI القديم للإضافات اتغير — راجع إضافة كل plugin"],
             ["utilities مخصصة", "plugin JS أو `@layer components`", "**`@utility name { … }`**", "بتشتغل مع المتغيرات (`@md:card`) عكس `@apply` في class"],
             ["الوضع الداكن", "`darkMode: 'class'`", "`@custom-variant dark (&:where([data-theme=dark], …))`", "الافتراضي لسه `prefers-color-scheme`"],
             ["لون الحدود الافتراضي", "`gray-200`", "**`currentColor`**", "أشهر كسر بصري عند الترقية: أضف `border-gray-200` صراحة"],
             ["`outline-none`", "شفاف مع fallback", "`outline-style: none` فعلًا", "للوصلية استخدم **`outline-hidden`** (بتحتفظ بالـoutline في forced-colors)"],
             ["عرض `ring` الافتراضي", "3px", "**1px**", "لو عايز الشكل القديم: `ring-3`"],
             ["التدرجات", "`bg-gradient-to-r`", "`bg-linear-to-r` (و`bg-radial`/`bg-conic`)", "الأسماء القديمة لسه شغالة لكن الأفضل الجديد"],
             ["أسماء `*-sm`", "`shadow-sm`, `rounded-sm`", "`shadow-xs`, `rounded-xs` (و`-sm` بقت قيمة أصغر)", "أداة الترقية بتعدلها — راجع بصريًا"],
             ["Container queries", "plugin منفصل", "**مدمجة**: `@container` + `@sm:`/`@md:`", "مثالية للمكوّنات المعاد استخدامها"],
             ["الحد الأدنى للمتصفحات", "أقدم", "**Safari 16.4+ · Chrome 111+ · Firefox 128+**", "لو جمهورك أقدم، اثبت على 3.4 ووثّق القرار"],
             ["المسافات", "قيم ثابتة (p-1…p-96)", "**مشتقة من `--spacing`** (فـ`p-13` و`w-17` شغالين)", "أي مضاعف لـ0.25rem متاح"],
         ]},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ الاستجابة: breakpoints + container queries"},
        {"type": "table", "caption": "القيم الافتراضية في v4 (mobile-first: اللاحقة تعني «من هذا العرض فأعلى»)",
         "head": ["اللاحقة", "العرض", "الاستخدام النموذجي"],
         "rows": [
             ["(بلا لاحقة)", "كل الأحجام", "التخطيط الأساسي للموبايل — اكتبه أولًا"],
             ["`sm:`", "40rem (640px)", "هواتف كبيرة/تابلت صغير: عمودان خفيفان"],
             ["`md:`", "48rem (768px)", "تابلت: شريط جانبي يظهر · 2–3 أعمدة"],
             ["`lg:`", "64rem (1024px)", "لابتوب: 3–4 أعمدة · هوامش أكبر"],
             ["`xl:`", "80rem (1280px)", "شاشات كبيرة: 4 أعمدة"],
             ["`2xl:`", "96rem (1536px)", "شاشات ضخمة · قيّد المحتوى بـ`max-w-7xl` بدل التمدد"],
             ["`@sm:`/`@md:` …", "**حجم الحاوية**", "مكوّن يتغير حسب مكانه (عمود ضيق مقابل صفحة عريضة)"],
         ]},
        {"type": "code", "lang": "text", "title": "استجابة عملية: container query + RTL + تكبير الخط", "filename": "docs/css-responsive.md", "code": r'''## 1) container query: مكوّن واحد يشتغل في مكانين

~~~html
<!-- الحاوية تُعلَّم بـ@container -->
<div class="@container">
  <!-- البطاقة تتغير حسب عرض الحاوية، لا عرض الشاشة -->
  <article class="card flex flex-col gap-3 @md:flex-row @md:items-center">
    <img src="…" alt="" class="h-20 w-20 rounded-md object-cover" />
    <div class="min-w-0">
      <h3 class="truncate font-medium">طلب رقم 1042</h3>
      <p class="text-sm text-ink-muted">منذ ساعتين</p>
    </div>
    <span class="@md:ms-auto rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-700">
      مدفوع
    </span>
  </article>
</div>
~~~

**لماذا**: نفس المكوّن في الشريط الجانبي (عرض 300px) وفي الصفحة الرئيسية
(عرض 900px). بـbreakpoints عادية هتضبط حسب **الشاشة** فتخطئ في الحالتين.

## 2) RTL بلا إعادة كتابة: الخصائص المنطقية

| بدل (مادي) | استخدم (منطقي) | في Tailwind |
|---|---|---|
| `margin-left/right` | `margin-inline-start/end` | `ms-*` / `me-*` |
| `padding-left/right` | `padding-inline-start/end` | `ps-*` / `pe-*` |
| `left/right` | `inset-inline-start/end` | `start-*` / `end-*` |
| `text-align: left` | `text-align: start` | `text-start` / `text-end` |
| `border-left` | `border-inline-start` | `border-s` / `border-e` |
| `border-radius: 8px 0 0 8px` | منطقي | `rounded-s-lg` / `rounded-e-lg` |

~~~html
<html lang="ar" dir="rtl">
  <body>
    <!-- الأرقام/الأكواد/البريد تبقى LTR داخل صفحة RTL -->
    <p>رقم الطلب: <span dir="ltr">ORD-2026-1042</span></p>
    <pre dir="ltr" class="overflow-x-auto"><code>dotnet run</code></pre>
    <input dir="ltr" class="text-start" placeholder="+20 10 1234 5678" />
  </body>
</html>
~~~

**قواعد RTL العملية**:
- اضبط `dir="rtl"` على `<html>` (مش على عناصر متفرقة).
- استخدم الأيقونات المتماثلة فقط، أو اعكس ما يحتاج (`scale-x-[-1]` للأسهم).
- الأرقام: `font-variant-numeric: tabular-nums` (`tabular-nums` في Tailwind)
  عشان الجداول تتحاذي — ومهم في العربية لأن الأرقام العربية (٠١٢٣) عرضها مختلف.
- الاختبار: شغّل الصفحة في الاتجاهين — أي عنصر «لاصق» في جهة هيبان فورًا.

## 3) تكبير الخط والوصولية
- استخدم `rem` للنص والمسافات: المستخدم اللي بيكبّر لـ200% هيشوف تخطيطك يتمدد صح.
- اختبر بعرض 320px (أصغر هاتف شائع): أي overflow أفقي = مشكلة.
- `text-balance` للعناوين و`text-pretty` للفقرات يحسّنان التقسيم بصريًا.
- لا تخفِ محتوى على الموبايل بـ`hidden md:block` لو هو **وظيفة** — أخفِ التكرار فقط.
'''},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ صفحة كاملة: من tokens إلى واجهة إدارية"},
        {"type": "code", "lang": "text", "title": "src/pages/orders.html — صفحة إدارية (RTL) بكل الحالات", "filename": "src/pages/orders.html", "code": r'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>الطلبات — لوحة shop</title>
  <link rel="stylesheet" href="/src/styles/app.css" />
</head>
<body class="bg-surface text-ink">
  <!-- رابط تخطي للمحتوى (a11y) -->
  <a href="#main"
     class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:start-2 focus:z-50
            focus:rounded-md focus:bg-brand-600 focus:px-3 focus:py-2 focus:text-white">
    تخطي إلى المحتوى
  </a>

  <div class="grid min-h-screen grid-cols-1 md:grid-cols-[16rem_1fr]">
    <!-- الشريط الجانبي -->
    <aside class="border-e border-gray-200 bg-surface-raised p-4 md:sticky md:top-0 md:h-screen">
      <p class="mb-4 text-sm font-semibold text-ink-muted">shop</p>
      <nav aria-label="التنقل الرئيسي">
        <ul class="grid gap-1 text-sm">
          <li><a href="#" aria-current="page"
                 class="block rounded-md bg-brand-50 px-3 py-2 font-medium text-brand-700">الطلبات</a></li>
          <li><a href="#" class="block rounded-md px-3 py-2 hover:bg-gray-100">العملاء</a></li>
          <li><a href="#" class="block rounded-md px-3 py-2 hover:bg-gray-100">التقارير</a></li>
        </ul>
      </nav>
    </aside>

    <!-- المحتوى -->
    <main id="main" class="grid gap-6 p-4 sm:p-6">
      <!-- رأس الصفحة: عنوان + إجراءات -->
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-xl font-semibold text-balance">الطلبات</h1>
          <p class="text-sm text-ink-muted">1,248 طلبًا · آخر تحديث منذ دقيقتين</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button type="button" class="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50">
            تصدير
          </button>
          <button type="button" class="btn-primary">طلب جديد</button>
        </div>
      </header>

      <!-- مؤشرات: أعمدة تتكيف تلقائيًا -->
      <section aria-label="مؤشرات" class="grid grid-cols-[repeat(auto-fill,minmax(14rem,1fr))] gap-4">
        <article class="card">
          <p class="text-sm text-ink-muted">طلبات اليوم</p>
          <p class="mt-1 text-2xl font-semibold tabular-nums">312</p>
          <p class="mt-1 text-xs text-success">▲ 8% عن أمس</p>
        </article>
        <article class="card">
          <p class="text-sm text-ink-muted">معدل الفشل</p>
          <p class="mt-1 text-2xl font-semibold tabular-nums">0.4%</p>
          <p class="mt-1 text-xs text-ink-muted">ضمن الميزانية (7.1.5)</p>
        </article>
        <article class="card">
          <p class="text-sm text-ink-muted">قيمة السلة</p>
          <p class="mt-1 text-2xl font-semibold tabular-nums" dir="ltr">EGP 486.20</p>
        </article>
      </section>

      <!-- أدوات الجدول: بحث + مرشحات -->
      <section class="card grid gap-3 sm:grid-cols-[1fr_auto]">
        <label class="grid gap-1">
          <span class="text-sm font-medium">بحث</span>
          <input type="search" name="q" placeholder="رقم الطلب أو اسم العميل"
                 class="rounded-md border border-gray-300 px-3 py-2 text-sm
                        focus-visible:outline-2 focus-visible:outline-brand-600" />
        </label>
        <div class="flex items-end gap-2">
          <select name="status" class="rounded-md border border-gray-300 px-3 py-2 text-sm">
            <option value="">كل الحالات</option>
            <option value="placed">تم الطلب</option>
            <option value="paid">مدفوع</option>
            <option value="cancelled">ملغي</option>
          </select>
        </div>
      </section>

      <!-- الجدول: قابل للتمرير أفقيًا على الموبايل -->
      <section class="card overflow-x-auto p-0">
        <table class="w-full min-w-[40rem] text-sm">
          <caption class="sr-only">قائمة الطلبات مع الحالة والقيمة</caption>
          <thead class="border-b bg-surface-raised text-start text-ink-muted">
            <tr>
              <th scope="col" class="px-4 py-3 text-start font-medium">الطلب</th>
              <th scope="col" class="px-4 py-3 text-start font-medium">العميل</th>
              <th scope="col" class="px-4 py-3 text-end font-medium">القيمة</th>
              <th scope="col" class="px-4 py-3 text-start font-medium">الحالة</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr class="hover:bg-surface-raised">
              <th scope="row" class="px-4 py-3 font-medium" dir="ltr">ORD-1042</th>
              <td class="px-4 py-3">منى إبراهيم</td>
              <td class="px-4 py-3 text-end tabular-nums" dir="ltr">EGP 486.20</td>
              <td class="px-4 py-3">
                <span class="rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">مدفوع</span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ترقيم -->
      <nav aria-label="ترقيم الصفحات" class="flex items-center justify-between text-sm">
        <p class="text-ink-muted">صفحة 1 من 63</p>
        <div class="flex gap-2">
          <button type="button" disabled class="rounded-md border px-3 py-1.5 disabled:opacity-50">السابق</button>
          <button type="button" class="rounded-md border px-3 py-1.5 hover:bg-gray-50">التالي</button>
        </div>
      </nav>
    </main>
  </div>
</body>
</html>
'''},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ CSS والوصولية (a11y) — ما تفرطش فيها"},
        {"type": "table", "caption": "عشرة قواعد وصولية في CSS/HTML تكفي لمعظم المنتجات",
         "head": ["#", "القاعدة", "التنفيذ في Tailwind", "لماذا"],
         "rows": [
             ["1", "لا تحذف حلقة التركيز", "`focus-visible:outline-2 focus-visible:outline-brand-600` — ولا `outline-none` أبدًا", "مستخدمو لوحة المفاتيح بيضيعوا من غير مؤشر"],
             ["2", "تباين كافٍ", "نص عادي ≥ 4.5:1 · كبير ≥ 3:1 (تحقق بأداة تباين)", "ضعف البصر والإضاءة الخارجية"],
             ["3", "هدف لمس ≥ 44×44 بكسل", "`min-h-11 min-w-11` للأزرار والروابط", "الموبايل والرعشة"],
             ["4", "لا تعتمد على اللون وحده", "شارة حالة بنص + أيقونة (`مدفوع` + نقطة)", "عمى الألوان"],
             ["5", "احترم تقليل الحركة", "`@media (prefers-reduced-motion: reduce)` (في ملف CSS أعلاه)", "دوار الحركة/الصداع"],
             ["6", "لا تخفِ المحتوى بـ`hidden` لو وظيفة", "استخدم `sr-only` للمحتوى المخصص لقارئ الشاشة", "قارئ الشاشة والتصفح بلوحة المفاتيح"],
             ["7", "HTML دلالي أولًا", "`button` للأفعال · `a` للتنقل · `nav`/`main`/`table` مع `caption` و`scope`", "التقنيات المساعدة بتفهم البنية"],
             ["8", "لا تغير ترتيب التركيز بـtabindex موجب", "رتب الـDOM منطقيًا بدل `tabindex=\"1\"`", "ترتيب مفاجئ = مستخدم تائه"],
             ["9", "حجم خط قابل للتكبير", "`rem` للنص والمسافات + بلا `overflow: hidden` قاتل", "تكبير المتصفح لـ200%"],
             ["10", "لغة واتجاه صحيحان", "`<html lang=\"ar\" dir=\"rtl\">` + `dir=\"ltr\"` للأرقام/الأكواد", "نطق صحيح ومحاذاة صحيحة"],
         ]},

        # ───────────────────────────────────────────── ⑧
        {"type": "heading", "level": 2, "text": "⑧ عشرة أخطاء بتخلي الواجهة شكلها هاوي"},
        {"type": "table", "caption": "الخطأ × الأثر × الإصلاح",
         "head": ["#", "الخطأ", "الأثر", "الإصلاح"],
         "rows": [
             ["1", "مسافات عشوائية (13px · 18px · 15px)", "فوضى بصرية بدون سبب واضح", "مقياس واحد من `--spacing` (مضاعفات 4)"],
             ["2", "خمس درجات رمادي مختلفة", "الصفحة باهتة/متسخة", "توكنان: `--color-ink` و`--color-ink-muted` + حدود بلون واحد"],
             ["3", "خطوط بأحجام غير متسلسلة", "لا هرم بصري", "مقياس: 12/14/16/20/24/30 — وبلا أحجام بينها"],
             ["4", "`px` للنص والمسافات", "التكبير بيكسر التخطيط", "`rem` (و`em` للنص النسبي داخل مكوّن)"],
             ["5", "margins على أولاد flex/grid", "مسافة زيادة على الحواف", "`gap-*` على الحاوي"],
             ["6", "`overflow-x` غير مقصود", "تمرير أفقي على الموبايل (أسوأ عيب بصري)", "اختبر على 320px + `min-w-0` لعناصر flex النصية"],
             ["7", "الوضع الداكن كفكرة لاحقة", "تباين مكسور وألوان غير مقروءة", "توكنات دلالية من اليوم الأول (`surface`/`ink`)"],
             ["8", "z-index تصاعدي (999!)", "طبقات فوق بعضها بلا نظام", "مقياس محدد (10/20/30/40/50) موثق"],
             ["9", "class soup بلا مكونات", "HTML غير مقروء وتكرار", "`@utility` للمكونات المتكررة (card/btn-primary) أو مكوّن في إطارك"],
             ["10", "الاعتماد على الخصائص المادية (`ms-` غائبة)", "RTL مكسور تمامًا", "خصائص منطقية دايمًا (الجدول في ⑤)"],
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أشرح box model وأعرف ليه `border-box` هو المطلوب.",
            "أختار بين Flexbox وGrid بقاعدة واضحة (محتوى بيحدد الحجم مقابل حاوية بتحدد الحجم) وأركب الاتنين.",
            "أعرف Specificity وcascade layers وأفسر ليه الـutilities بتكسب.",
            "أعرّف توكنات تصميم في `@theme` (ألوان دلالية · خطوط · مسافات · حدود · حركة) وأستخدمها لثيم داكن.",
            "أعرف إعداد Tailwind v4: `@import \"tailwindcss\"` + `@tailwindcss/vite` + كشف تلقائي + `@source` + `@plugin` + `@utility`.",
            "أعرف أهم كسرين عند الترقية من v3: لون الحدود الافتراضي `currentColor` · و`outline-none` مقابل `outline-hidden`.",
            "أبني استجابة mobile-first بالـbreakpoints الافتراضية، وأستخدم container queries للمكوّنات.",
            "أبني واجهة RTL صحيحة بالخصائص المنطقية (`ms-/me-/ps-/pe-/start-/end-/border-s`) مع `dir=\"ltr\"` للأرقام والأكواد.",
            "أطبّق 10 قواعد وصولية في CSS (حلقة تركيز · تباين · هدف لمس · تقليل حركة · HTML دلالي).",
            "أتجنب الأخطاء العشرة: مسافات عشوائية · px · margins بدل gap · overflow أفقي · z-index تصاعدي.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على CSS وTailwind v4.",
         "questions": [
             {"q": "في Tailwind v4، كيف تُعرّف الإعداد (ألوان مخصصة)؟",
              "options": ["`tailwind.config.js` إلزامي",
                          "بكتلة `@theme` في ملف CSS بعد `@import \"tailwindcss\"`",
                          "في `package.json`",
                          "بملف JSON منفصل"],
              "answer": 1,
              "explain": "v4 أصبح CSS-first: التوكنات متغيرات CSS في `@theme` فتولّد utilities (مثلًا `--color-brand-600` → `bg-brand-600`). ولازم `@import \"tailwindcss\"` يبقى أول قاعدة. إعداد JS القديم ممكن يتحمّل بـ`@config` عند الترقية."},
             {"q": "أشهر كسر بصري عند الترقية من v3 إلى v4؟",
              "options": ["اختفاء الـgrid",
                          "لون الحدود الافتراضي اتغير من gray-200 إلى currentColor، و`ring` بقى 1px بدل 3px",
                          "منع استخدام rem",
                          "إلغاء الوضع الداكن"],
              "answer": 1,
              "explain": "أي `border` بلا لون صريح هياخد لون النص — ف الحدود بتبقى أغمق بكتير. أضف `border-gray-200` (أو توكن) صراحة، واستخدم `ring-3` لو عايز سماكة الـring القديمة. أداة `@tailwindcss/upgrade` بتعدل معظم الأسماء لكن راجع بصريًا."},
             {"q": "متى تستخدم container query بدل breakpoint عادي؟",
              "options": ["دائمًا",
                          "عندما يعتمد شكل المكوّن على عرض حاويته (يُعرض في شريط جانبي ضيق وفي صفحة عريضة)",
                          "عندما تكون الصفحة ثابتة العرض",
                          "لا فرق بينهما"],
              "answer": 1,
              "explain": "breakpoints بتقيس **الشاشة** فبتخطئ للمكوّنات المعاد استخدامها في أماكن مختلفة. v4 دمجت container queries (`@container` على الحاوي + `@md:` على المكوّن) بلا plugin."},
             {"q": "لتطبيق يدعم العربية والإنجليزية، ما الأسلوب الصحيح؟",
              "options": ["ملف CSS لكل اتجاه مع `left/right`",
                          "خصائص منطقية: `ms-/me-` · `ps-/pe-` · `start-/end-` · `text-start` · `border-s` مع `dir` على `<html>`",
                          "تدوير العناصر بـ`rotate-180`",
                          "استخدام flexbox فقط"],
              "answer": 1,
              "explain": "الخصائص المنطقية بتتبع اتجاه الكتابة، فتبديل `dir=\"rtl\"` بـ`dir=\"ltr\"` بيقلب التخطيط كاملًا بدون تعديل أنماط. وأضف `dir=\"ltr\"` على الأرقام والأكواد والبريد داخل صفحة RTL."},
             {"q": "لماذا `gap` أفضل من margins بين عناصر flex؟",
              "options": ["أسرع في الأداء",
                          "لا يضيف مسافة على الحواف الخارجية ولا يحتاج إلغاء آخر عنصر",
                          "يعمل مع grid فقط",
                          "يقلل حجم CSS"],
              "answer": 1,
              "explain": "margins على الأولاد بتسيب مسافة زيادة عند الحواف وبتحتاج حيل (`:last-child`) لإلغائها. `gap` بتضبط المسافة **بين** العناصر فقط في flex وgrid."},
             {"q": "`outline-none` في v4 — ما البديل الصحيح للوصولية؟",
              "options": ["لا بديل، الحلقة غير ضرورية",
                          "`outline-hidden` (يخفيها بصريًا لكن يحتفظ بها في forced-colors) أو نمط `focus-visible` واضح",
                          "`ring-0`",
                          "`border-none`"],
              "answer": 1,
              "explain": "في v4 `outline-none` يعني `outline-style: none` فعلًا (مش hack الشفافية القديم). حذف مؤشر التركيز بيضيع مستخدم لوحة المفاتيح — الأفضل نمط واضح: `focus-visible:outline-2 focus-visible:outline-brand-600`."},
             {"q": "عنصر نصي داخل `flex` بيتجاوز عرض الحاوي. الإصلاح؟",
              "options": ["`overflow-hidden` على الصفحة",
                          "`min-w-0` على عنصر flex الحاوي + `truncate` على النص",
                          "تقليل حجم الخط",
                          "`position: absolute`"],
              "answer": 1,
              "explain": "عناصر flex الافتراضي `min-width: auto` فمش بتتقلص أقل من حجم محتواها — عشان كده النص الطويل بيكسر العرض. `min-w-0` بيسمح بالتقلص، و`truncate` بيقص مع نقاط."},
             {"q": "لماذا التوكنات بأسماء وظيفية (`--color-surface`) أفضل من أسماء الألوان (`--color-blue-500`)؟",
              "options": ["أقصر في الكتابة",
                          "تسمح بثيم داكن/تغيير علامة تجارية بتبديل القيم فقط، وتمنع استخدامًا عشوائيًا",
                          "أسرع في البناء",
                          "مدعومة فقط في v4"],
              "answer": 1,
              "explain": "الاسم الوظيفي بيربط القيمة بالدور: في الوضع الداكن تبدّل `--color-surface` من أبيض لأزرق داكن **من غير ما تلمس أي مكوّن**. أما `blue-500` فبيتحوّل لـ«أي أزرق في أي مكان» وبيصعب التدوير."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "نظام توكنات + صفحة إدارية متجاوبة وRTL.",
         "items": [
            {"id": "s8-m1-l3-t1",
             "title": "مهمة 1: نظام توكنات وTailwind v4 مضبوط",
             "md": "في مشروع الواجهة (من 8.1.1): ثبّت Tailwind v4 مع `@tailwindcss/vite`، وابنِ `app.css` فيه توكنات كاملة (ألوان دلالية + خطوط + مسافات + انحناء + حركة) + ثيم داكن + `@utility` لمكونين متكررين (card/btn-primary) + قواعد base للوصولية (حلقة تركيز · تقليل حركة).",
             "criteria": [
                 "`package.json` فيه `tailwindcss` و`@tailwindcss/vite` · و`vite.config.ts` فيه الـplugin · **بلا `tailwind.config.js` وبلا `postcss.config.js`** (أو مع سبب مكتوب لبقائهما).",
                 "`app.css` يبدأ بـ`@import \"tailwindcss\"` ثم `@source` (لو محتاج) ثم `@custom-variant dark` ثم `@theme`.",
                 "**≥ 6 توكنات ألوان دلالية** (`surface` · `surface-raised` · `ink` · `ink-muted` · `brand-*` · `success/warning/danger`) — بلا أسماء ألوان مباشرة في المكونات.",
                 "ثيم داكن بتبديل قيم التوكنات تحت `[data-theme=\"dark\"]` + زر تبديل في الصفحة (يحفظ الاختيار في `localStorage` — مسموح هنا لأنه تفضيل مش توكن أمان).",
                 "**`@utility` واحد على الأقل** (card أو btn-primary) مستخدم في ≥ 3 أماكن.",
                 "قواعد base: `:focus-visible` واضح · `prefers-reduced-motion` · `body` يستخدم التوكنات · `box-sizing` من Preflight متحقق.",
                 "`npm run build` ينتج CSS **أصغر من 30KB مضغوطًا** (v4 بيولّد المستخدم فقط) — اذكر الحجم الفعلي.",
                 "قرار مكتوب: هل استخدمت `oklch` أم hex، ولماذا (P3/إدراك لوني/توافق).",
             ],
             "hint": "لو الـCSS الناتج كبير: غالبًا `@source` بيمسح مجلدات فيها ملفات مولّدة (dist/coverage) — ضيّق المسار أو استبعد بـ`@import \"tailwindcss\" source(none)` + `@source` محددة. ولو الـutilities ما ظهرتش: تأكد إن ملف CSS مستورد في نقطة الدخول (`import \"./styles/app.css\"`) وإن الإضافة مسجلة في مصفوفة `plugins` داخل `vite.config.ts`. وللاختبار السريع: `npx @tailwindcss/cli --input … --output /tmp/out.css` ثم ابحث عن اسم الـutility في الناتج.",
             "solution": "النتائج النموذجية: حجم CSS الناتج لمشروع صغير 8–20KB مضغوطًا (مقابل 3MB+ لو ولّدت كل الـutilities). التوكنات الدلالية بتكشف فورًا أي ألوان عشوائية في الكود (grep عن `#` في ملفات المكوّنات لازم يرجع فاضي تقريبًا). الثيم الداكن أول مرة بيطلع 3–5 أماكن فيها ألوان مثبتة (غالبًا حدود وظلال) — حوّلها لـ`color-mix(in oklab, var(--color-ink) 12%, transparent)` أو توكن. و`@utility` مقابل `@layer components`: الأول بيشتغل مع المتغيرات (يعني `@md:card` شغالة) وبيُنتج CSS عند الاستخدام فقط — عشان كده هو المفضل في v4.",
             "resources": [
                 "https://tailwindcss.com/docs/installation/using-vite",
                 "https://tailwindcss.com/docs/theme",
                 "https://tailwindcss.com/docs/dark-mode",
                 "https://tailwindcss.com/docs/upgrade-guide",
                 "https://tailwindcss.com/docs/adding-custom-styles",
             ]},
            {"id": "s8-m1-l3-t2",
             "title": "مهمة 2: صفحة إدارية متجاوبة RTL/LTR",
             "md": "ابنِ صفحة «الطلبات» (مثل صفحة الدرس) بتخطيط Grid (شريط جانبي + محتوى) + شبكة مؤشرات + جدول قابل للتمرير + أدوات بحث/ترشيح + ترقيم. اشتغل mobile-first، واستخدم الخصائص المنطقية فقط، واختبر الاتجاهين (rtl/ltr) وثلاثة عروض (320/768/1440).",
             "criteria": [
                 "HTML دلالي: `header`/`nav`/`main`/`aside`/`section`/`table` مع `caption` و`scope` · `button` للأفعال و`a` للتنقل · رابط تخطي (`sr-only focus:not-sr-only`).",
                 "تخطيط Grid للصفحة (`md:grid-cols-[16rem_1fr]`) + Grid لشبكة المؤشرات (`auto-fill,minmax`) + Flex داخل البطاقات.",
                 "**صفر خصائص مادية** في الأنماط: كل المسافات والحدود منطقية (`ms-/me-/ps-/pe-/border-s/text-start/rounded-s`) — واثبت ذلك بأمر بحث.",
                 "يعمل في الاتجاهين: `<html dir=\"rtl\" lang=\"ar\">` ومبدّل للاتجاه، والأرقام/الأكواد بـ`dir=\"ltr\"` و`tabular-nums`.",
                 "استجابة: بلا overflow أفقي عند 320px · الجدول قابل للتمرير داخل حاويته فقط · الأدوات بتتنقل لصف واحد على الموبايل.",
                 "وصولية: تباين ≥ 4.5:1 للنص الأساسي (اذكر القيم المحسوبة) · أهداف لمس ≥ 44px · حلقة تركيز واضحة · حالة `disabled` و`aria-current=\"page\"`.",
                 "**لقطات/مخرجات** للثلاثة عروض × الاتجاهين (6 حالات) مع ملاحظة على أي مشكلة لقيتها وأصلحتها.",
                 "فحص بأداة آلية: `axe-core` (أو Lighthouse) — صفر أخطاء حرجة، مع قائمة النتائج.",
             ],
             "hint": "لإثبات «صفر خصائص مادية»: `grep -rnE '\\b(ml-|mr-|pl-|pr-|left-|right-|text-left|text-right|border-l|border-r)\\b' src` لازم يرجع فاضي (عدا حالات موثقة). وللاختبار السريع على 320px: أدوات المطور → device toolbar → 320×568. ولو الجدول بيكسر العرض: لفّه في حاوي `overflow-x-auto` + `min-w-[40rem]` على الجدول نفسه (مش على الحاوي). ولـaxe-core: إضافة المتصفح أو `@axe-core/cli` على الصفحة.",
             "solution": "المشاكل النموذجية: (1) `truncate` بلا `min-w-0` في flex → النص بيتجاوز، وده بيظهر أول ما تضيق الشاشة. (2) الأيقونات السهمية ما بتنعكسش في RTL — تحتاج `scale-x-[-1]` أو أيقونات متماثلة. (3) `tabular-nums` ناقصة فالأرقام في الجدول مش متحاذية (واضحة أكتر في العربية). (4) الشريط الجانبي `sticky` مع `overflow-x: hidden` على أب → الـsticky بيكسر (قاعدة: `overflow` غير `visible` على السلسلة بيوقف sticky). (5) Lighthouse بيطلع عادة: تباين النص الرمادي الفاتح (استخدم `--color-ink-muted` أغمق) · أزرار بلا اسم متاح (أضف `aria-label` للأيقونات فقط). النتيجة المتوقعة: 6 لقطات متسقة، وصفر أخطاء axe حرجة، وCSS أقل من 20KB.",
             "resources": [
                 "https://tailwindcss.com/docs/responsive-design",
                 "https://tailwindcss.com/docs/container-queries",
                 "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout",
                 "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout",
                 "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values",
                 "https://web.dev/learn/accessibility/",
                 "https://github.com/dequelabs/axe-core",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Tailwind CSS: التوثيق", "url": "https://tailwindcss.com/docs"},
            {"label": "Tailwind v4: تثبيت مع Vite", "url": "https://tailwindcss.com/docs/installation/using-vite"},
            {"label": "Tailwind v4: دليل الترقية من v3", "url": "https://tailwindcss.com/docs/upgrade-guide"},
            {"label": "MDN: CSS", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS"},
            {"label": "MDN: الخصائص المنطقية", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values"},
            {"label": "MDN: Container queries", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_queries"},
            {"label": "web.dev: تعلّم الوصولية", "url": "https://web.dev/learn/accessibility/"},
            {"label": "MDN: Flexbox", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout"},
        ]},
    ],
}

LESSONS_S8_C = [_L3]
