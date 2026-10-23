"""Stage 2, Module 4 — Capstone project."""

TODAY = "2026-10-22"

LESSONS_S2_F = [
    {
        "id": "s2-m4-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "callout", "kind": "goal", "title": "هدف المرحلة",
             "md": """
مش هتتعلم تقنية جديدة هنا — هتجمّع **المرحلة 1 + المرحلة 2** في API واحد يُعتبر «جاهز للإنتاج»
بمعايير 2026: منظّم، مختبَر، موثّق بـOpenAPI، مؤمّن عمداً (مش بالافتراضيات)، فيه realtime وbackground work
وصحة معلنة — ومقاس بأرقام مش بانطباعات.

**المدة المتوقعة: 20-26 ساعة عمل** موزعة على أيام. المعيار مش «اشتغل على جهازي»؛
المعيار إن مطورًا تاني يقدر يستنسخه ويشغّله ويثق في سلوكه.
"""},
            {"type": "text", "md": """
اشتغل على نفس مشروع المرحلة 1 (المتجر/الطلبات) وطوّره — **لا تبدأ من الصفر**.
القيمة الحقيقية في المشروع ده هي *التحويل التدريجي* لكود موجود إلى كود إنتاجي:
ده بالظبط اللي بيحصل في الشغل الحقيقي، وهو أقوى حاجة تتكلم عنها في المقابلات.

القاعدة الحاكمة: **كل عنصر في القائمة لازم يكون له دليل** — اختبار، قياس، أو قرار مكتوب (ADR).
عنصر بلا دليل = عنصر غير منفَّذ مهما كان رأيك فيه.
"""},
            {"type": "heading", "level": 2, "text": "القائمة الكاملة (كل بند مربوط بدرس)"},
            {"type": "table", "head": ["#", "البند", "الدليل المطلوب", "الدرس"], "rows": [
                ["1", "Domain نظيف + Application services + DTOs منفصلة للقراءة/الكتابة", "اختبارات Domain ≥ 85% تغطية + مخطط اعتماد (اتجاه للداخل)", "1.1-1.4"],
                ["2", "Minimal APIs منظمة بـfeature folders و`Results<A,B>` صريحة", "`Program.cs` ≤ 50 سطر + حالات 200/201/400/401/403/404/409 في OpenAPI", "2.1.1"],
                ["3", "عقد أخطاء موحّد `application/problem+json` + `traceId` + `X-Correlation-Id`", "اختبار لكل حالة خطأ يتحقق من الشكل والرؤوس", "1.6 / 2.1.1"],
                ["4", "OpenAPI 3.1 + Scalar + golden diff في CI", "ملف مستند معتمد + workflow يفشل عند تغيير عقد غير مقصود", "2.1.2"],
                ["5", "Cursor pagination + فلترة/فرز بـwhitelist", "اختبار تنقل 5 صفحات بلا تكرار + قياس مقابل offset عند عمق 10k", "2.1.3"],
                ["6", "Rate limiting على المصادقة والكتابة + 429 مع `Retry-After`", "اختبار يتجاوز الحد ويؤكد الاستجابة والرؤوس", "2.1.5"],
                ["7", "كاش (HybridCache/Output cache) مع إبطال مقصود", "قياس p95 قبل/بعد + اختبار إبطال بعد الكتابة", "2.1.6"],
                ["8", "سياسات تفويض مركزية + resource-based authorization (BOLA)", "اختبارات 401/403/200 لكل endpoint محمي + اختبار ملكية المورد", "2.2.1"],
                ["9", "JWT (Authority/JWKS أو إصدار ذاتي بمفتاح RSA) + refresh rotation + كشف إعادة استخدام", "اختبار دورة التوكنات كاملة + إبطال العائلة", "2.2.2"],
                ["10", "Identity: تسجيل، lockout، سياسة كلمة سر، 2FA + recovery codes", "اختبار قفل بعد 5 محاولات + تفعيل 2FA وإبطال الجلسات", "2.2.3"],
                ["11", "رؤوس أمان + HTTPS/HSTS + CORS بأصول صريحة + أسرار خارج الـrepo", "اختبارات رؤوس/CORS + `grep` نظيف + `ValidateOnStart`", "2.2.5"],
                ["12", "تدقيق OWASP API Top 10 بحالة ودليل لكل بند", "جدول 10 بنود + أولويات إصلاح", "2.2.5"],
                ["13", "Realtime: SignalR لمجموعات مستخدمين أو SSE لتقدّم مهمة", "اختبار منطق بـmock + تحقق يدوي من عدم تسريب أحداث بين مستخدمين", "2.3.1"],
                ["14", "BackgroundService آمن (scope/try-catch/stoppingToken) + قناة idempotent", "اختبار فشل دورة لا يوقف التطبيق + إيقاف < 5 ثوانٍ", "2.3.2"],
                ["15", "مهمة دورية بمخزن دائم + مفتاح تنفيذ idempotent + حداثة مُقاسة", "تشغيل يدوي مزدوج → تنفيذ واحد + health check freshness", "2.3.3"],
                ["16", "Health: `/live` ذاتي، `/ready` تبعيات، `/detail` محمي", "وقف القاعدة → live=200 وready=503", "2.3.4"],
                ["17", "اختبارات: Unit + Integration (WebApplicationFactory + Testcontainers) في CI", "workflow أخضر + زمن تشغيل مسجل + فئات مفصولة (Unit/Integration)", "1.2.1-1.2.5"],
                ["18", "قياس تحميل p50/p95/p99 قبل وبعد الكاش/الفهرس", "أرقام محفوظة في الملف مع منهجية القياس", "2.4"],
                ["19", "Docker + docker-compose للتبعيات (Postgres/Redis)", "تشغيل بأمر واحد من clone نظيف", "3.x (مقدمة)"],
                ["20", "قرارات موثقة: 3-5 ADRs + README تشغيل", "ملفات ADR + README يُتبع حرفيًا", "1.1.7"],
            ]},
            {"type": "heading", "level": 2, "text": "خطة التنفيذ على 6 جلسات"},
            {"type": "steps", "title": "لا تعمل كل حاجة مرة واحدة — رتّبها كده", "items": [
                {"title": "الجلسة 1 (3-4 ساعات): الأساس المعماري والاختبارات",
                 "md": "راجع بنية المرحلة 1: طبقات، DTOs منفصلة، عقد أخطاء موحّد. تأكد إن CI أخضر وفيه Unit + Integration على Testcontainers. من غير الأساس ده، باقي البنود هتتراكم فوق رمل.",
                 "code": {"lang": "bash", "title": "تحقق قبل البدء", "code": "dotnet build --warnaserror\ndotnet test --filter Category=Unit\ndotnet test --filter Category=Integration\ngit log --oneline -5   # تأكد إنك على فرع feature مش main"}},
                {"title": "الجلسة 2 (3-4 ساعات): الـAPI الحديث",
                 "md": "Minimal APIs بـfeature folders + `Results<A,B>` + OpenAPI/Scalar + golden diff + cursor pagination + فلترة whitelist. اختتمها بقياس قبل الكاش (نقطة أساس للأرقام)."},
                {"title": "الجلسة 3 (4-5 ساعات): الأمان",
                 "md": "سياسات تفويض + BOLA + JWT/refresh rotation + Identity (lockout/2FA) + rate limiting + رؤوس/CORS/أسرار + تدقيق OWASP. دي أطول جلسة؛ لو ضاق الوقت قسمها على يومين."},
                {"title": "الجلسة 4 (3-4 ساعات): الكاش والأداء",
                 "md": "HybridCache أو Output cache بإبطال مقصود، فهارس للـcursor، ثم **قياس بعد**. قارن p50/p95/p99 واكتب الفرق بالمللي ثانية والنسبة."},
                {"title": "الجلسة 5 (3-4 ساعات): Realtime والخلفية",
                 "md": "SignalR/SSE لحدث واحد حقيقي في مشروعك (تغيّر حالة طلب) + BackgroundService آمن + قناة idempotent + مهمة دورية بمخزن دائم وhealth check لحداثتها."},
                {"title": "الجلسة 6 (3-4 ساعات): التشغيل والتوثيق",
                 "md": "Health endpoints + Docker/compose + ADRs + README تشغيل يُتبع حرفيًا + مراجعة القائمة بندًا بندًا مع الأدلة. أي بند ناقص: وثّق **لييه** وخطتك ليه (قرار صريح أفضل من تجاهل صامت)."},
            ]},
            {"type": "heading", "level": 2, "text": "القياس: أرقام مش انطباعات"},
            {"type": "code", "lang": "javascript", "filename": "load/list-orders.js", "title": "k6: سيناريو صغير يكفي لأرقام موثوقة", "code": r'''
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    ramp: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 10 },     // إحماء
        { duration: "2m", target: 50 },      // حمل ثابت
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],          // أقل من 1% أخطاء
    http_req_duration: ["p(95)<300"],        // p95 أقل من 300ms
  },
};

const BASE = __ENV.BASE_URL ?? "http://localhost:8123";
const TOKEN = __ENV.TOKEN;

export default function () {
  const res = http.get(`${BASE}/api/orders?size=20`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  check(res, {
    "status 200": (r) => r.status === 200,
    "has items": (r) => JSON.parse(r.body).items.length > 0,
  });
}
'''},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "منهجية القياس (نفس الظروف مرتين)", "code": r'''
# 1) ثبّت الظروف: نفس البيانات (عدد صفوف)، نفس الجهاز، بلا عمليات تانية
psql "$DB" -c "SELECT count(*) FROM orders;"      # سجّل العدد
docker stats --no-stream                          # تأكد من موارد مستقرة

# 2) قبل التغيير
k6 run load/list-orders.js | tee results/before.txt

# 3) التغيير (كاش / فهرس) ثم نفس الأمر تمامًا
k6 run load/list-orders.js | tee results/after.txt

# 4) قارن الأرقام المسجلة (p50/p95/p99 + معدل الأخطاء + RPS) واكتبها في ملف المشروع
grep -E "http_req_duration|http_req_failed|iterations" results/before.txt results/after.txt

# 5) SQL: تأكد إن الفهرس مستخدم فعلًا (مش مجرد تحسّن عشوائي)
psql "$DB" -c "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT 21;"
'''},
            {"type": "table", "head": ["القياس", "قبل", "بعد", "ملاحظة"], "rows": [
                ["GET /api/orders p50", "—", "—", "املأها من نتائج k6"],
                ["GET /api/orders p95", "—", "—", "الأهم لاتفاق مستوى الخدمة"],
                ["GET /api/orders p99", "—", "—", "يكشف الذيل (GC/قفل/استعلام بطيء)"],
                ["معدل الأخطاء", "—", "—", "لا تقبل تحسّن زمن مع ارتفاع أخطاء"],
                ["RPS قصوى مستقرة", "—", "—", "متى يبدأ التدهور؟"],
                ["حجم/زمن أبطأ استعلام (EXPLAIN)", "—", "—", "دليل إن الفهرس استُخدم"],
            ]},
            {"type": "callout", "kind": "warn", "title": "أخطاء بتضيع وقت المشروع",
             "md": """
- **البدء من الصفر** بدل تطوير مشروع المرحلة 1 → هتقضي الوقت في الـscaffolding مش في المهارات المطلوبة.
- **العمل بالعرض** (كل حاجة شوية) → الأفضل بالعمود: أتم بندًا بدليله قبل ما تنتقل للي بعده.
- **تأجيل الاختبارات للآخر** → هتعيد كتابة كود كتير. كل بند + اختباره في نفس الجلسة.
- **كاش قبل القياس** → مش هتعرف هل التحسن من الكاش ولا من ظروف التشغيل. قِس أولًا.
- **إهمال الأمان لأنه «مش هيظهر في الديمو»** → هو بالظبط اللي بيتسأل عنه في المقابلات وأول حاجة بتفشل في الإنتاج.
- **محاولة إضافة Aspire/K8s/microservices دلوقتي** → دي المرحلة 3 و5. خلّي النطاق مضبوطًا.
"""},
            {"type": "callout", "kind": "note", "title": "إزاي تستخدم المشروع ده في البحث عن وظيفة (المرحلة 10)",
             "md": """
مشروع واحد عميق بـ20 بند موثق بأدلة أقوى من 5 مشاريع tutorial. لما توصل لمرحلة الوظيفة:
- حط **README** فيه: مشكلة النظام، قراران معماريان بسببهم، الأرقام (p95 قبل/بعد)، وإزاي تشغّله بأمر واحد.
- سجّل **3 دقائق** فيديو/ GIF لمسار واحد حقيقي (إنشاء طلب → حدث realtime → تقرير مجدول).
- جهّز **قصتين**: باج صعب شخّصته بأدوات القياس، وقرار أمني رفضت فيه الحل الأسهل.
- خلي الـrepo عام (أو خاص مع لقطات) والـCI badge شغال.
"""},
            {"type": "tasks", "title": "مهام المشروع", "items": [
                {"id": "t1", "title": "القائمة الكاملة: 20 بندًا بأدلة",
                 "md": "نفّذ البنود الـ20 في الجدول على مشروع المرحلة 1. لكل بند: دليل (اختبار/قياس/قرار مكتوب) وعلّم حالته في ملف `CAPSTONE.md` داخل المشروع (منفَّذ / جزئي / مؤجَّل + السبب).",
                 "criteria": [
                     "17 بندًا على الأقل منفَّذ بدليل، والباقي مؤجَّل بسبب مكتوب صراحة",
                     "CI أخضر: Unit + Integration مفصولة بفئات وزمنها مسجل",
                     "تشغيل من clone نظيف بأمرين أو أقل (docker compose + dotnet run)",
                     "لا أسرار في الـrepo (`grep` نظيف + user-secrets/Key Vault)",
                     "OpenAPI منشور داخليًا ومستند معتمد + golden diff في CI",
                     "كل endpoint محمي: اختبارات 401/403 وBOLA على مورد واحد على الأقل",
                     "دورة توكنات كاملة مع كشف إعادة الاستخدام (اختبار يثبت إبطال العائلة)",
                     "وقف قاعدة البيانات → `/health/live`=200 و`/health/ready`=503",
                 ],
                 "hint": "اعمل `CAPSTONE.md` بأعمدة: البند | الحالة | الدليل (رابط ملف/اختبار) | ملاحظة. حدّثه بعد كل جلسة — هو أداة التخطيط والتقييم في نفس الوقت."},
                {"id": "t2", "title": "قياس وتحسين موثّق",
                 "md": "قِس مسارًا ساخنًا واحدًا (`GET /api/orders`) بـk6 قبل وبعد تحسين واحد (كاش أو فهرس). سجّل p50/p95/p99 ومعدل الأخطاء وRPS، وأثبت بـ`EXPLAIN ANALYZE` إن الفهرس استُخدم.",
                 "criteria": [
                     "منهجية مكتوبة: حجم البيانات، الظروف، عدد الجولات",
                     "جدول قبل/بعد مملوء بأرقام حقيقية (مش تقديرية)",
                     "p95 تحسّن بنسبة مسجلة، ومعدل الأخطاء ما ارتفعش",
                     "مخرَج `EXPLAIN` محفوظ ويظهر استخدام الفهرس",
                     "استنتاج من سطر: إيه اللي سبب التحسن فعلًا",
                 ]},
                {"id": "t3", "title": "القرارات والتوثيق",
                 "md": "اكتب 3-5 ADRs للقرارات المؤثرة (Minimal APIs، أداة الجدولة، نمط التوكنات، استراتيجية الكاش، اختبار التبعيات) وREADME تشغيل يُتبع حرفيًا من clone نظيف.",
                 "criteria": [
                     "كل ADR فيه: السياق، القرار، البدائل المرفوضة وسبب رفضها، والعواقب",
                     "README فيه: المتطلبات، أوامر التشغيل، أوامر الاختبار، المسارات المهمة، والمتغيرات البيئية",
                     "شخص تاني (أو أنت بعد شهر) يقدر يشغّل المشروع من README وحده",
                 ],
                 "solution": "قالب ADR مختصر:\n```\n# ADR-007: أداة الجدولة\nالحالة: مقبول (2026-10-22)\nالسياق: محتاجين مهمتين دوريتين مع رؤية وإعادة محاولة.\nالقرار: Hangfire مع مخزن Postgres.\nالبدائل: BackgroundService (بلا دوام/رؤية) — Quartz (أثقل من الاحتياج) — K8s CronJob (يستلزم نشر منفصل).\nالعواقب: جداول إضافية في القاعدة + لوحة تحكم تحتاج حماية؛ إعادة المحاولة مدمجة.\n```"},
            ]},
            {"type": "resources", "items": [
                {"label": "k6 documentation", "url": "https://grafana.com/docs/k6/"},
                {"label": "ADR — Architectural Decision Records", "url": "https://adr.github.io/"},
                {"label": "ASP.NET Core production checklist", "url": "https://learn.microsoft.com/aspnet/core/host-and-deploy/"},
                {"label": "OWASP API Security Top 10", "url": "https://owasp.org/www-project-api-security/"},
                {"label": "Docker Compose", "url": "https://docs.docker.com/compose/"},
                {"label": "eShop reference architecture", "url": "https://github.com/dotnet-architecture/eShop"},
            ]},
        ],
    },
]
