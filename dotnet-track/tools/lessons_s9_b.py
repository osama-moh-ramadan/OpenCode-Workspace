# -*- coding: utf-8 -*-
"""Stage 9 — module 1 (part B): s9-m1-l2 (تصميم: مُقصّر روابط)."""

TODAY = "2026-10-22"

_L2 = {
    "id": "s9-m1-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "أشهر سؤال System Design وأكثرها فائدة: **مُقصّر روابط** (URL shortener). سؤال بسيط ظاهريًا، لكنه بيجبرك على: حساب أحجام · مولّد مفاتيح بلا تعارض · فهرسة · كاش · ترقيم · تحليلات بدون تعطيل الـredirect · وتوسع للقراءة الثقيلة.\n\nطريقة العمل في الدرس: **نتكلم كأننا في مقابلة** — متطلبات → أرقام → مخطط بيانات → مسار الكتابة → مسار القراءة → التوسع → الأعطال. والكود بـASP.NET Core 10 + PostgreSQL."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Back-of-envelope", "def": "حساب تقديري سريع (RPS · حجم · عدد صفوف) قبل التصميم — يحدد إن كنت تحتاج توزيعًا أصلًا."},
            {"term": "Base62", "def": "ترميز بـ`0-9a-zA-Z` (62 رمزًا). 7 رموز = 62⁷ ≈ 3.5 تريليون قيمة — تكفي لعقود."},
            {"term": "Key generation", "def": "توليد المعرّف: عدّاد مركزي (`SEQUENCE`) · UUID ثم اختصار · عشوائي مع فحص تعارض · Hash للرابط (نفس الرابط → نفس الاختصار)."},
            {"term": "Collision handling", "def": "عند التوليد العشوائي: فهرس فريد + إعادة محاولة محدودة (2–3) ثم خطأ صريح — لا حلقة لا نهائية."},
            {"term": "301 vs 302", "def": "301 دائم (المتصفح يكاشه → أسرع وأقل حمل، لكن التحليلات تفقد زيارات) · 302 مؤقت (كل زيارة تصل لك → تحليلات دقيقة)."},
            {"term": "Snowflake-like", "def": "معرّف 64-bit = وقت + ماكينة + تسلسل: فريد عالميًا، مرتّب زمنيًا تقريبًا، بلا تنسيق مركزي."},
            {"term": "Hot key", "def": "مفتاح واحد يحمل نسبة كبيرة من الطلبات (رابط منتشر) — قد يسبب اختناقًا في نسخة كاش واحدة."},
            {"term": "Negative caching", "def": "كاش «غير موجود» لفترة قصيرة حتى لا يضرب الطلبُ الوهمي القاعدةَ مليون مرة."},
        ]},

        # ①
        {"type": "heading", "level": 2, "text": "① المتطلبات ثم الأرقام (قبل أي كود)"},
        {"type": "table", "caption": "متطلبات وظيفية وغير وظيفية",
         "head": ["النوع", "البند", "القرار"],
         "rows": [
             ["وظيفي", "إنشاء اختصار لرابط", "`POST /api/links` → `{code, shortUrl, expiresAt}`"],
             ["وظيفي", "فتح الرابط", "`GET /{code}` → 302 + `Location`"],
             ["وظيفي", "روابط مخصصة (custom alias) وصيانتها", "اختياري — مع فحص توفر"],
             ["وظيفي", "انتهاء صلاحية", "عمود `ExpiresAt` + رفض عند الفتح"],
             ["غير وظيفي", "زمن الفتح p95", "**≤ 50ms** من الكاش · ≤ 120ms من القاعدة"],
             ["غير وظيفي", "التوفر", "99.95% للفتح (أهم من الإنشاء)"],
             ["غير وظيفي", "عدم فقد الروابط", "لا حذف فعلي للمستخدم — soft delete"],
             ["خارج النطاق", "لوحة تحليلات كاملة", "نكتفي بعدّادات غير متزامنة (⑤)"],
         ]},
        {"type": "code", "lang": "text", "title": "الحساب: 3 أرقام تحدد المعمارية", "filename": "docs/numbers.txt", "code": r'''
الافتراضات (واقعية لمشروع متوسط، لا «مليار مستخدم»):
  إنشاء: 100 رابط/ثانية ذروة (≈ 8.6M رابط/يوم)
  قراءة: نسبة 20:1 → 2,000 فتح/ثانية ذروة
  حجم السجل: 500B (رابط طويل + كود + مالك + وقت) → 4.3GB/يوم ≈ 1.6TB/سنة
  احتفاظ: أبدي (soft delete فقط)

الاستنتاجات:
  ① القراءة ثقيلة ⇒ كاش أولًا، ثم replica للقراءة.
  ② 2,000 RPS للفتح ⇒ نسختان للتطبيق + كاش مشترك؛ كل 1%miss = 20 استعلام/ث.
  ③ 1.6TB/سنة ⇒ مرشّح قوي لـ**تقسيم** بالكود (hash) أو أرشيف بارد بعد سنتين.
  ④ زمن الفتح يحدده الكاش: 50ms مستهدَفة تعني قراءة ذاكرة لا قاعدة في الحالة الشائعة.
  ⑤ العدّادات لا تُكتب في مسار الفتح (وإلا 2,000 كتابة/ث = 10× عمل الكتابة).
'''},
        {"type": "callout", "kind": "tip", "title": "لو الحساب صغير، التصميم يبقى صغيرًا",
         "md": "لو مشروعك 10 روابط/ثانية، فـ**جدول واحد + فهرس فريد + كاش في الذاكرة + PostgreSQL** كافٍ، وأي حديث عن Sharding وSnowflake هو **تعقيد مضاد**. في المقابلة قُل ذلك صريحًا: «بهذه الأرقام، أحتاج X فقط؛ وسننتقل إلى Y عندما يتجاوز الحمل Z» — ده اللي يفرّقك."},

        # ②
        {"type": "heading", "level": 2, "text": "② مخطط البيانات ومعرّف الاختصار"},
        {"type": "table", "caption": "جدولان فقط",
         "head": ["العمود", "النوع", "الغرض", "الفهرس"],
         "rows": [
             ["`Code`", "`varchar(12)`", "المعرّف العام (Base62 أو alias)", "**PK / فريد**"],
             ["`TargetUrl`", "`text`", "الرابط الأصلي", "—"],
             ["`OwnerId`", "`varchar(64)`", "من أنشأه (null للزوّار)", "فهرس مركّب `(OwnerId, CreatedAt)`"],
             ["`CreatedAt`", "`timestamptz`", "الوقت", "داخل الفهرس المركّب"],
             ["`ExpiresAt`", "`timestamptz NULL`", "انتهاء الصلاحية", "فهرس جزئي للتنظيف"],
             ["`IsDeleted`", "`boolean`", "soft delete", "فهرس جزئي `WHERE IsDeleted = false`"],
             ["`Version`", "`int`", "تفاؤلي (concurrency)", "—"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Links/CodeGenerator.cs — عدّاد + Base62 (بلا تعارض، بلا تنسيق معقّد)", "filename": "src/Shop.Api/Links/CodeGenerator.cs", "code": r'''using System.Buffers.Text;   // Base64Url للإسقاط إن لزم
using Microsoft.EntityFrameworkCore;

/// <summary>
/// مولّد أكواد بلا تعارض:
///   • عدّاد في القاعدة (SEQUENCE) → كل قيمة فريدة، لا فحص تعارض.
///   • Base62 يقلّل الطول (7 رموز تكفي لعقود).
///   • توزيع الأكواد: نضرب في مُعامل فردي كبير ونعيد الترتيب
///     حتى لا تكون الأكواد المتتالية قابلة للتخمين (تعداد).
/// </summary>
public sealed class CodeGenerator(ShopDbContext db)
{
    private const string Alphabet =
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private const long Multiplier = 6_364_136_223_846_793_005; // فردي (Knuth)

    public async Task<string> NextAsync(CancellationToken ct)
    {
        // SELECT nextval('link_code_seq') — ذرّي وسريع
        var next = await db.Database
            .SqlQuery<long>($"SELECT nextval('link_code_seq') AS \"Value\"")
            .SingleAsync(ct);

        // تشويش ترتيبي: n → (n × فردي) mod 62^7 (تبديل تقريبي)
        var mixed = (next * Multiplier) % 3_521_614_606_207;   // 62^7 - 1
        return ToBase62(mixed);
    }

    public static string ToBase62(long value)
    {
        if (value == 0) return "0";
        Span<char> buffer = stackalloc char[11];   // 62^11 > long.MaxValue
        var i = buffer.Length;
        while (value > 0)
        {
            buffer[--i] = Alphabet[(int)(value % 62)];
            value /= 62;
        }
        return new string(buffer[i..]);
    }

    /// <summary>للروابط المخصصة: تحقق من الصيغة قبل الوصول للقاعدة.</summary>
    public static bool IsValidAlias(string alias) =>
        alias.Length is >= 3 and <= 12 &&
        alias.All(c => char.IsAsciiLetterOrDigit(c) || c is '-' or '_') &&
        !Reserved.Contains(alias, StringComparer.OrdinalIgnoreCase);

    private static readonly string[] Reserved =
        ["api", "admin", "login", "health", "static", "assets", "bff"];
}
'''},
        {"type": "callout", "kind": "note", "title": "لماذا لا UUID عشوائي؟",
         "md": "**UUID v4**: فريد بلا تنسيق، لكن 36 حرفًا (أو 22 بـBase64) — طويل على الروابط، وعشوائي تمامًا = لا ترتيب زمني (يسيء للفهرسة).\n**UUID v7** (مرتّب زمنيًا) خيار ممتاز لو تحتاج فريدًا بلا قاعدة.\n**Hash للرابط** (MD5/SHA → 7 رموز): يعطي **نفس الاختصار لنفس الرابط** (ميزة)، لكنه يحتاج فحص تعارض (احتمال تصادم صغير)، ويكشف أحيانًا أن الرابط موجود سابقًا — وقد يُساء استخدامه للاستعلام.\n**الدرس:** ليس هناك «أفضل مولّد» — بل: هل تحتاج ترتيبًا؟ هل تقبل تصادمًا؟ هل تريد عدم التخمين؟"},

        # ③
        {"type": "heading", "level": 2, "text": "③ مسار الكتابة والقراءة (كود كامل)"},
        {"type": "code", "lang": "csharp", "title": "Links/LinkEndpoints.cs — إنشاء + فتح + كاش + تحليلات غير متزامنة", "filename": "src/Shop.Api/Links/LinkEndpoints.cs", "code": r'''using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Hybrid;

public static class LinkEndpoints
{
    public static void MapLinkEndpoints(this IEndpointRouteBuilder app)
    {
        // ── إنشاء ────────────────────────────────────────────────
        app.MapPost("/api/links", async Task<Results<Created<LinkDto>, ValidationProblem>> (
            CreateLinkRequest req, ShopDbContext db, CodeGenerator gen,
            TimeProvider clock, CancellationToken ct) =>
        {
            if (!Uri.TryCreate(req.Url, UriKind.Absolute, out var uri) ||
                (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
                return TypedResults.ValidationProblem(new Dictionary<string, string[]>
                    { ["url"] = ["رابط http/https صالح مطلوب"] });

            if (req.Alias is { } alias && !CodeGenerator.IsValidAlias(alias))
                return TypedResults.ValidationProblem(new Dictionary<string, string[]>
                    { ["alias"] = ["3–12 حرفًا/رقمًا؛ وليس كلمة محجوزة"] });

            var code = req.Alias ?? await gen.NextAsync(ct);
            var link = Link.Create(code, uri.ToString(), req.OwnerId,
                req.ExpiresAt is { } e ? clock.GetUtcNow().Add(e) : null);

            db.Links.Add(link);
            try { await db.SaveChangesAsync(ct); }
            catch (DbUpdateException ex) when (ex.IsUniqueViolation())
            {
                // alias مستخدم أو (نادرًا) تعارض كود — استجابة واضحة لا 500
                return TypedResults.ValidationProblem(new Dictionary<string, string[]>
                    { ["alias"] = ["هذا الاختصار مستخدم بالفعل"] });
            }

            return TypedResults.Created($"/api/links/{code}",
                new LinkDto(code, $"{req.BaseUrl}/{code}", link.ExpiresAt));
        });

        // ── فتح الرابط: المسار الساخن ────────────────────────────
        app.MapGet("/{code}", async (
            string code, ShopDbContext db, HybridCache cache,
            LinkAnalytics analytics, TimeProvider clock, HttpContext http, CancellationToken ct) =>
        {
            // ① تحقق شكلي قبل الوصول لأي طبقة
            if (code.Length is < 3 or > 12) return Results.NotFound();

            // ② الكاش: القيمة = (TargetUrl, ExpiresAt)
            var target = await cache.GetOrCreateAsync(
                key: $"v1:link:{code}",
                factory: async token => await db.Links.AsNoTracking()
                    .Where(l => l.Code == code && !l.IsDeleted)
                    .Select(l => new CachedLink(l.TargetUrl, l.ExpiresAt, l.Version))
                    .FirstOrDefaultAsync(token),
                options: new HybridCacheEntryOptions
                {
                    Expiration = TimeSpan.FromHours(6),
                    LocalCacheExpiration = TimeSpan.FromMinutes(5),
                },
                cancellationToken: ct);

            if (target is null) return Results.NotFound();

            if (target.ExpiresAt is { } exp && exp <= clock.GetUtcNow())
                return Results.StatusCode(StatusCodes.Status410Gone);

            // ③ التحليلات: لا تُعطّل الفتح أبدًا (fire-and-forget)
            analytics.Track(code, http);

            // ④ 302 للمؤقت (تحليلات دقيقة)، 301 للدائم (كاش المتصفح)
            return Results.Redirect(target.TargetUrl, permanent: false, preserveMethod: false);
        });
    }
}

/// <summary>يجمع أحداث الفتح في الذاكرة ويُفرّغها دوريًا — لا كتابة في مسار الطلب.</summary>
public sealed class LinkAnalytics(Channel<LinkHit> channel, ILogger<LinkAnalytics> log)
{
    public void Track(string code, HttpContext http) =>
        // TryWrite لا يحجب أبدًا؛ لو الممتد ممتلئ نُسقط الحدث (التحليلات ليست معاملات)
        channel.Writer.TryWrite(new LinkHit(
            code,
            Hash(http.Connection.RemoteIpAddress?.ToString()),   // لا تخزّن IP خامًا (7.2.5)
            http.Request.Headers.Referer.ToString(),
            http.Request.Headers.UserAgent.ToString()[..Math.Min(200, http.Request.Headers.UserAgent.ToString().Length)],
            DateTimeOffset.UtcNow));

    private static string Hash(string? ip) =>
        string.IsNullOrEmpty(ip) ? "unknown"
            : Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(
                System.Text.Encoding.UTF8.GetBytes(ip)))[..16];
}
'''},
        {"type": "table", "caption": "قرارات مسار الفتح — كل واحد له سبب",
         "head": ["القرار", "السبب", "الثمن"],
         "rows": [
             ["كاش قبل القاعدة", "2,000 RPS على القاعدة = عنق زجاجة وتكلفة", "بيانات قديمة حتى TTL عند الحذف — نبطل عند الحذف"],
             ["302 لا 301 (افتراضيًا)", "التحليلات تُفقد مع 301 لأن المتصفح لا يسأل", "زمن أعلى قليلًا (كل زيارة تصل لك)"],
             ["410 للرابط المنتهي", "دلالة صحيحة (Gone) تفيد الـSEO والمستخدم", "لا شيء"],
             ["التحليلات fire-and-forget", "لا يجوز أن يفشل فتح الرابط بسبب عدّاد", "قد تُفقد نسبة صغيرة من الأحداث"],
             ["IP مُهشَّر", "خصوصية (7.2.5): لا حفظ بيانات شخصية خامة", "لا يمكن تحليل جغرافي دقيق لاحقًا"],
             ["`Version` في الكاش", "يتيح إبطالًا انتقائيًا عند تعديل الهدف", "عمود إضافي"],
         ]},

        # ④
        {"type": "heading", "level": 2, "text": "④ التوسع والأعطال: أين ينكسر التصميم؟"},
        {"type": "table", "caption": "5 أعطال وردّك عليها",
         "head": ["العطل", "الأثر", "الحل", "ما لا تفعله"],
         "rows": [
             ["رابط منتشر (hot key)", "نسخة كاش واحدة تختنق", "L1 محلي + نسخ L2 + `singleflight` + حد معدل", "لا تعيد التوزيع بتغيير المفتاح (يكسر الكاش)"],
             ["كاش بارد بعد نشر", "كل الطلبات تقع على القاعدة دفعة واحدة", "warm-up للمفاتيح الشائعة + تأخير إزالة النسخ القديمة", "لا تنشر كل النسخ في اللحظة نفسها"],
             ["تعارض alias", "500 للمستخدم", "فهرس فريد + إعادة رسالة 400 واضحة", "لا تلفّ الاستثناء وترجّعه 500"],
             ["العدّاد المركزي بطيء", "تأخر الإنشاء", "تخصيص نطاقات (blocks) لكل نسخة + بلا تنسيق لكل طلب", "لا تجعل كل نسخة تنادي القاعدة لكل كود"],
             ["قاعدة القراءة متأخرة", "رابط أُنشئ للتو لا يفتح", "**read-your-writes**: اقرأ من الأساسي بعد الكتابة (أو مرّر الكود في الرد)", "لا تعتمد على replica فورًا بعد الكتابة"],
         ]},
        {"type": "code", "lang": "text", "title": "متى نُقسّم (Sharding)؟", "filename": "docs/sharding.txt", "code": r'''
الترتيب الصحيح قبل التقسيم:
  1) فهرس صحيح (Code فريد · OwnerId+CreatedAt)           ← يغطي 90% من البطء
  2) كاش + replica للقراءة
  3) أرشفة الروابط الخاملة (> سنتين) إلى جدول بارد/ZSTD
  4) تقسيم أفقي فقط عند تجاوز ~1–2TB أو كتابة > 5k/ث

لو وصلت للتقسيم:
  shard key = hash(Code) % N   ← توزيع متساوٍ، والفتح يحدد القطعة مباشرة
  مشكلة: الاستعلام «كل روابط المستخدم» يحتاج جولة على كل القطع.
  الحل: جدول مرجعي UserId → shard، أو تقسيم ثانوي بالمالك.
  إعادة التوازن: انقل القطع تدريجيًا + اقبل قراءة من القديم مؤقتًا (dual-read).
'''},

        # ⑤
        {"type": "heading", "level": 2, "text": "⑤ التحليلات: قيمة بلا كسر الأداء"},
        {"type": "table", "caption": "ثلاث طبقات للعدّ",
         "head": ["الطبقة", "ماذا تفعل", "التأثير", "الدقة"],
         "rows": [
             ["في الذاكرة (Counter)", "عدّ لكل كود في العملية", "صفر تقريبًا", "تُفقد عند إعادة التشغيل"],
             ["قناة + دفعات", "تجميع أحداث ثم كتابة كل 5 ثوانٍ", "منخفض جدًا", "فقدان نادر عند الامتلاء"],
             ["جدول أحداث", "سجل كامل لكل زيارة", "كتابة = 2,000/ث", "كاملة — لكن مكلفة"],
         ]},
        {"type": "callout", "kind": "warn", "title": "خصوصية التحليلات",
         "md": "أي «تحليل زيارة» يحتوي بيانات قد تكون شخصية: IP · User-Agent · Referer. في مصر، قانون **PDPL 151/2020** (نافذ مع انتهاء سماح ~نوفمبر 2026) يفرض أساسًا قانونيًا وتقليل البيانات.\n**الحد الأدنى المقبول:** هشّر IP بـsalt دوري · خزّن UA مختصرًا · لا تخزّن referer كاملًا إن كان يحتوي معرّفات · احتفظ بالأحداث ≤ 90 يومًا · وفّر تصدير/حذف للمستخدم (7.2.5)."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تحسب RPS للإنشاء والفتح وحجم البيانات قبل التصميم.",
            "تختار مولّد أكواد حسب احتياجك (عدّاد · UUIDv7 · hash) وتشرح ثمن كل واحد.",
            "تعرف سعة Base62 (7 رموز ≈ 3.5 تريليون) وتستخدمها في قرار الطول.",
            "تصمّم جدولًا بفهرسين على الأكثر وتبرّرهما.",
            "تفصل مسار القراءة الساخن عن أي عمل ثقيل (تحليلات/كتابة).",
            "تفرّق بين 301 و302 وتشرح أثر كل واحد على التحليلات.",
            "تستخدم `GetOrCreateAsync` + TTL + إبطال عند الحذف.",
            "تتعامل مع hot key وcold cache وread-your-writes بخطط محددة.",
            "تقرر **لا** تقسّم حتى تصل للحدود، وتذكر حدود إعادة النظر.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "7 أسئلة على تصميم حقيقي.",
         "questions": [
             {"q": "7 رموز Base62 — كم قيمة ممكنة تقريبًا؟",
              "options": ["62 ألف", "3.5 تريليون", "7 ملايين", "62 مليون"],
              "answer": 1,
              "explain": "62⁷ = 3,521,614,606,208 (≈3.5 تريليون). لذلك 7 رموز كافية لعقود دون زيادة الطول — وهذا حساب back-of-envelope نموذجي."},
             {"q": "لماذا نستخدم عدّادًا + تشويش ترتيبي بدل عشوائي كامل؟",
              "options": ["لأن العشوائي لا يعمل في PostgreSQL",
                          "لأن العدّاد يضمن عدم التعارض بلا فحص، والتشويش يمنع تخمين الأكواد المتتالية (تعداد)",
                          "لتقليل حجم الروابط", "لتحسين الـSEO"],
              "answer": 1,
              "explain": "العدّاد يعطي تفردًا مضمونًا بأداء عالٍ، لكن الأكواد المتتالية قابلة للتخمين (مستخدم يجرّب `a1, a2, a3`). ضرب في مُعامل فردي mod 62⁷ يعطي توزيعًا غير متسلسل ظاهريًا مع بقاء التفرد."},
             {"q": "أي رد redirect يحافظ على دقة التحليلات؟",
              "options": ["301", "302", "308", "بدون redirect"],
              "answer": 1,
              "explain": "301 يجعله المتصفح يذهب مباشرة في المرات التالية فلا تصل زيارات. 302 يضمن وصول كل نقرة (مع ثمن زمن إضافي). بعض الأنظمة تستخدم 302 افتراضيًا وتسمح بـ301 للمالك إن أراد الأداء."},
             {"q": "بعد إنشاء رابط، المستخدم يفتحه فورًا ولا يعمل. السبب الأرجح؟",
              "options": ["الكاش", "قراءة من replica متأخرة (replication lag) — الحل read-your-writes أو تمرير الكود في الرد",
                          "الفهرس", "302"],
              "answer": 1,
              "explain": "الكتابة تذهب للأساسي والقراءة للنسخة المتابعة قد تكون متأخرة أجزاء من الثانية. الحلول: قراءة من الأساسي بعد الكتابة، أو service-level: نمرر الكود ونعرضه دون قراءة، أو انتظار LSN. التصميم الجيد يعالج هذه الحالة صراحة."},
             {"q": "ما أخطر أثر للـhot key؟",
              "options": ["زيادة حجم القاعدة", "اختناق نسخة كاش واحدة/اتصال واحد + ارتفاع p99 رغم صحة النظام عمومًا",
                          "فقدان البيانات", "تعارض الأكواد"],
              "answer": 1,
              "explain": "مفتاح واحد يحمل نسبة كبيرة من الحمل يضرب نفس العقدة. الحلول: L1 محلي في كل نسخة (توزيع طبيعي)، نسخ خوانية للـL2، `singleflight`، وحد معدل — مع مراقبة حمل المفاتيح الساخنة."},
             {"q": "التحليلات في مسار الفتح: ما القرار الصحيح؟",
              "options": ["كتابة متزامنة قبل الرد", "قناة/ذاكرة + تفريغ دوري، مع إسقاط الأحداث عند الامتلاء (لا تُفشل الفتح)",
                          "حذف التحليلات", "كتابة في نفس ترانزاكشن الرابط"],
              "answer": 1,
              "explain": "فتح الرابط أهم من التحليلات؛ أي كتابة متزامنة تضاعف زمن الاستجابة وتضيف نقطة فشل. القناة + التفريغ تعطي زمنًا شبه صفري وتحمّل الذروة، وفقدان نسبة صغيرة مقبول."},
             {"q": "متى يكون التقسيم (Sharding) قرارًا صحيحًا؟",
              "options": ["من البداية دائمًا", "بعد استنفاد الفهرس والكاش وreplica والأرشفة، ووصول حجم/كتابة يتجاوز قدرة عقدة واحدة",
                          "عند 1000 رابط", "عند وجود فهرس فريد"],
              "answer": 1,
              "explain": "التقسيم يضيف تعقيدًا كبيرًا (استعلامات موزعة، إعادة توازن، معاملات). الترتيب: فهرس → كاش → replica → أرشفة → تقسيم. وفي المقابلة اذكر حدًا رقميًا لإعادة النظر."},
         ]},

        {"type": "tasks", "title": "مهمة واحدة", "intro": "تصميم من صفحتين + كود مسار الفتح.",
         "items": [
            {"id": "s9-m1-l2-t1",
             "title": "صمّم مُقصّر روابط بأرقامك",
             "md": "اكتب تصميمًا من صفحتين (متطلبات · أرقام · مخطط بيانات · مسار كتابة · مسار قراءة · توسع · أعطال)، ونفّذ مسار الفتح بـASP.NET Core + PostgreSQL مع كاش وتحقّق.",
             "criteria": [
                 "قسم أرقام: RPS ذروة للإنشاء والفتح · حجم سجل · حجم سنة · نسبة إصابة كاش مستهدفة — بافتراضات مكتوبة.",
                 "مخطط جدول واحد على الأقل بفهرسين مبرّرين + سياسة soft delete + انتهاء صلاحية.",
                 "مولّد أكواد مكتوب (Base62) مع خطة تعارض (فهرس فريد + رسالة واضحة).",
                 "مسار الفتح: كاش → قاعدة → 302 · مع `404` للكود غير الموجود و`410` للمنتهي.",
                 "مفتاح كاش يحتوي نسخة (`v1:`) + TTL + إبطال عند الحذف موثّق.",
                 "التحليلات خارج مسار الطلب (قناة/دفعة) مع إسقاط عند الامتلاء وIP مهشّر.",
                 "قسم أعطال: hot key · cold cache · lag · alias مكرر · عدّاد بطيء — بخطة لكل منها.",
                 "سطر «لا نُقسّم قبل…» بحد رقمي + ما يتغير عنده التصميم.",
                 "3 اختبارات على الأقل: فتح صحيح · كود غير موجود · رابط منتهي (410).",
             ],
             "hint": "ابدأ بالجدول والمسار واشتغل على «فتح الرابط» فقط في الكود — الباقي ورقي. لو عندك وقت ضيق، نفّذ النسخة البسيطة (بلا Kesh موزّع): `IMemoryCache` + فهرس فريد تُظهر كل المفاهيم. ولاحظ أن `HybridCache` يحتاج تسجيل L2 (Redis) لتستفيد من الاتساق بين النسخ — وفي مشروع محلي، L1 وحده مقبول مع توثيق الفرق.",
             "solution": "التصميم النموذجي: جدول `Links` (Code PK · TargetUrl · OwnerId · CreatedAt · ExpiresAt · IsDeleted · Version) + فهرسان · عدّاد Sequence + Base62 بـ7 رموز · مسار فتح من الكاش (TTL 6س · L1 5د) → 302 · تحليلات بدفعات · حدود إعادة النظر (RPS > 5k أو 1.5TB → sharding بـhash(code)). من أهم نقاط التقييم: هل تعرف **لماذا** كل قرار، وما ثمنه — لا عدد الأدوات.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/performance/caching/hybrid",
                 "https://learn.microsoft.com/ef/core/modeling/indexes",
                 "https://www.postgresql.org/docs/current/sql-sequences.html",
                 "https://learn.microsoft.com/azure/architecture/patterns/cache-aside",
                 "https://learn.microsoft.com/azure/architecture/best-practices/api-design",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "HybridCache", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/hybrid"},
            {"label": "فهارس EF Core", "url": "https://learn.microsoft.com/ef/core/modeling/indexes"},
            {"label": "PostgreSQL SEQUENCE", "url": "https://www.postgresql.org/docs/current/sql-sequences.html"},
            {"label": "Cache-Aside", "url": "https://learn.microsoft.com/azure/architecture/patterns/cache-aside"},
            {"label": "تصميم الـAPIs", "url": "https://learn.microsoft.com/azure/architecture/best-practices/api-design"},
        ]},
    ],
}

LESSONS_S9_B = [_L2]
