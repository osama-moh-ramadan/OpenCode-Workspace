"""Stage 2, Module 1 — Modern API design (lessons 4-6 of 6)."""

TODAY = "2026-10-22"

LESSONS_S2_G = [
    # ------------------------------------------------------------------ l4
    {
        "id": "s2-m1-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
كل طلب في ASP.NET Core بيمرّ في **سلسلة middleware** قبل ما يوصل للـendpoint وبعدها في طريق الرجوع.
فهم السلسلة دي مش «نظرية» — ده اللي بيحدد: أنهي middleware يقدر يمسك الاستثناء، مين بيضيف رؤوس،
ومين بيشوف الهوية. ومين بيشتغل **على كل طلب** (فالغلط هنا بيتضاعف في كل استجابة).

الدرس ده: تكتب middleware مخصص بأداء مقبول، تفهم الترتيب وأثره على الأخطاء، وتعرف إمتى تستخدم
Endpoint Filter بدل الـmiddleware.
"""},
            {"type": "terms", "items": [
                {"term": "Pipeline", "def": "سلسلة middleware: كل واحدة تنادي `next()` للتي بعدها، وترجع الاستجابة في طريق العودة."},
                {"term": "Terminal middleware", "def": "آخر نقطة في السلسلة (الـendpoints) — ما بتناديش `next`."},
                {"term": "Conventional middleware", "def": "كلاس بـconstructor ياخد `RequestDelegate next` — **يُنشأ مرة واحدة** (singleton)."},
                {"term": "Factory-based (`IMiddleware`)", "def": "يُحلّ من DI **لكل طلب** — يقبل خدمات scoped، بتكلفة حلّ بسيطة."},
                {"term": "`RequestDelegate`", "def": "`Func<HttpContext, Task>` — توقيع الـpipeline كله."},
                {"term": "`Response.HasStarted`", "def": "لما تبدأ الاستجابة في الإرسال، ما تقدرش تغيّر الحالة/الرؤوس ولا تتعامل مع الخطأ."},
                {"term": "`Response.OnStarting`", "def": "callback قبل إرسال أول بايت — المكان الآمن لإضافة رؤوس."},
                {"term": "`EnableBuffering`", "def": "يخلي جسم الطلب/الاستجابة قابلًا لإعادة القراءة — بتكلفة ذاكرة وأداء."},
            ]},
            {"type": "heading", "level": 2, "text": "الترتيب: ده مش تفصيلة"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "الترتيب الموثّق — وأي تبديل له أثر ملموس", "code": r'''
var app = builder.Build();

// 1) معالج الأخطاء أولًا: عشان يقدر يمسك استثناءات كل ما بعده
app.UseExceptionHandler(string.Empty);          // + IExceptionHandler المسجّل في DI
app.UseProblemDetails();

// 2) أمان النقل (إنتاج فقط)
if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
    app.UseHttpsRedirection();
}

// 3) رؤوس الأمان المخصصة (قبل أي استجابة ممكن تخرج)
app.UseSecurityHeaders();

// 4) ملفات ثابتة (لو فيه) — قبل الـrouting عشان ما تدفعش تكلفة التوجيه
app.UseStaticFiles();

// 5) correlation id والتسجيل — بعد رؤوس الأمان، وقبل المصادقة عشان تسجّل الهوية كمان
app.UseCorrelationId();
app.UseSerilogRequestLogging();

// 6) التوجيه (ضمني في Minimal APIs، صريح مع Controllers)
app.UseRouting();

// 7) CORS بعد الـrouting (يعرف المسار) وقبل المصادقة (يرفض الطلبات غير المسموحة مبكرًا)
app.UseCors("spa");

// 8) المصادقة ثم التفويض — بالترتيب ده دائمًا
app.UseAuthentication();
app.UseAuthorization();

// 9) حدود الاستهلاك — بعد المصادقة عشان تقدر تقسّم بحسب المستخدم
app.UseRateLimiter();

// 10) الكاش عند الخروج — بعد التفويض (لا تخزّن استجابة مستخدم لآخر)
app.UseOutputCache();

// 11) الـendpoints (terminal)
app.MapOrdersApi();
app.MapCatalogApi();
app.MapHealthEndpoints();

app.Run();
'''},
            {"type": "table", "head": ["لو حطيت…", "الأثر"], "rows": [
                ["`UseExceptionHandler` بعد `UseRouting`", "أخطاء التوجيه/الـmiddleware المبكرة ما بتتلحقش → استجابة خام أو اتصال مقطوع"],
                ["`UseAuthorization` قبل `UseAuthentication`", "كل الطلبات مجهولة → 401/403 غلط"],
                ["`UseCors` قبل `UseRouting`", "الـpreflight ممكن ما يتعرفش صح، والسياسات المعتمدة على المسار تفشل"],
                ["`UseRateLimiter` قبل `UseAuthentication`", "ما تعرفش المستخدم → تقسيم بـIP فقط (وورا الـproxy كل المستخدمين واحد)"],
                ["`UseOutputCache` قبل `UseAuthorization`", "خطر تسريب: تخزين استجابة مستخدم وتقديمها لآخر"],
                ["`UseHttpsRedirection` قبل `UseExceptionHandler`", "أخطاء التحويل ما بتتلحقش"],
                ["تسجيل جسم الطلب في middleware مبكر", "تكلفة `EnableBuffering` على **كل** طلب، وتسريب بيانات حساسة في اللوجات"],
            ]},
            {"type": "heading", "level": 2, "text": "middleware مخصص: مثالان حقيقيان"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Middleware/CorrelationIdMiddleware.cs", "title": "Conventional (singleton) — الأسرع، وبلا خدمات scoped", "code": r'''
/// <summary>
/// ربط الطلب بسياق واحد عبر الخدمات والـlogs والعميل.
/// ★ conventional middleware: يُنشأ مرة واحدة → لا تحقن فيه DbContext أو أي scoped.
/// </summary>
public sealed class CorrelationIdMiddleware(RequestDelegate next, ILogger<CorrelationIdMiddleware> log)
{
    private const string Header = "X-Correlation-Id";
    private static readonly string[] AcceptedPrefixes = ["0HM", "00-", "|"];   // أمثلة لتنقية المدخل

    public async Task InvokeAsync(HttpContext context)
    {
        var correlationId = GetOrGenerate(context);

        // ✓ أضف الرأس للاستجابة قبل ما تبدأ (بعد البدء مستحيل)
        context.Response.OnStarting(() =>
        {
            context.Response.Headers[Header] = correlationId;
            return Task.CompletedTask;
        });

        // ✓ وسّع نطاق اللوجات: أي log داخل هذا الطلب يحمل المعرّف تلقائيًا
        using (Serilog.Context.LogContext.PushProperty("CorrelationId", correlationId))
        {
            await next(context);
        }
    }

    private string GetOrGenerate(HttpContext context)
    {
        var incoming = context.Request.Headers[Header].FirstOrDefault();

        // لا تثق في رأس من العميل بلا تنقية: طول معقول + أحرف آمنة فقط
        if (!string.IsNullOrWhiteSpace(incoming)
            && incoming.Length is >= 8 and <= 64
            && incoming.All(c => char.IsAsciiLetterOrDigit(c) || c is '-' or '.'))
            return incoming;

        if (!string.IsNullOrWhiteSpace(incoming))
            log.LogWarning("rejected malformed correlation id header");

        return context.TraceIdentifier;
    }
}

public static class CorrelationIdExtensions
{
    public static IApplicationBuilder UseCorrelationId(this IApplicationBuilder app) =>
        app.UseMiddleware<CorrelationIdMiddleware>();
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Middleware/RequestMetricsMiddleware.cs", "title": "قياس زمن الطلب + تسجيل الاستثناءات المتأخرة", "code": r'''
using System.Diagnostics;

public static class RequestMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Api", "1.0.0");

    public static readonly Histogram<double> Duration =
        Meter.CreateHistogram<double>("http.server.request.duration", unit: "s",
            description: "زمن معالجة الطلب");
    public static readonly Counter<long> Rejections =
        Meter.CreateCounter<long>("http.server.rejections", description: "4xx/5xx counts");
}

public sealed class RequestMetricsMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        // ✓ Activity موجودة أصلًا من ASP.NET Core — نثريها بدل إنشاء واحدة جديدة
        var activity = Activity.Current;
        var started = Stopwatch.GetTimestamp();

        try
        {
            await next(context);
        }
        finally
        {
            var elapsed = Stopwatch.GetElapsedTime(started);
            var tags = new TagList
            {
                { "http.request.method", context.Request.Method },
                { "url.path", context.Request.Path.Value },
                { "http.response.status_code", context.Response.StatusCode },
            };

            RequestMetrics.Duration.Record(elapsed.TotalSeconds, tags);

            if (context.Response.StatusCode >= 400)
                RequestMetrics.Rejections.Add(1, tags);

            if (activity is not null && elapsed.TotalSeconds > 1)
                activity.SetTag("slow_request", true);      // يظهر في التتبع الموزع
        }
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Middleware/TenantMiddleware.cs", "title": "IMiddleware (factory-based) — لما تحتاج خدمة scoped", "code": r'''
/// <summary>
/// IMiddleware يُحلّ من DI لكل طلب → تقدر تحقن خدمات scoped.
/// التكلفة: حلّ اعتمادية لكل طلب (صغيرة، لكنها ليست صفرًا).
/// </summary>
public sealed class TenantMiddleware(ITenantStore tenants) : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        var host = context.Request.Host.Host;
        var tenant = await tenants.ResolveAsync(host, context.RequestAborted);

        if (tenant is null)
        {
            // ✓ ارفض مبكرًا — لا تكمل السلسلة بحالة غير معروفة
            context.Response.StatusCode = StatusCodes.Status404NotFound;
            await context.Response.WriteAsJsonAsync(new ProblemDetails
            {
                Status = 404, Title = "نطاق غير معروف",
                Extensions = { ["traceId"] = context.TraceIdentifier },
            }, context.RequestAborted);
            return;
        }

        context.Items["tenant"] = tenant;
        using (Serilog.Context.LogContext.PushProperty("TenantId", tenant.Id))
            await next(context);
    }
}

// التسجيل: النوع نفسه يُسجَّل في DI (IMiddleware يُحلّ من الحاوية)
builder.Services.AddScoped<TenantMiddleware>();
app.UseMiddleware<TenantMiddleware>();
'''},
            {"type": "callout", "kind": "warn", "title": "أداء الـmiddleware: كل سطر بيتنفذ على كل طلب",
             "md": """
- **conventional = singleton**: لا تحقن scoped (هترمي أو تستخدم كائن مغلق). لو محتاج scoped → `IMiddleware` أو `CreateAsyncScope`.
- **تجنّب التخصيص في المسار الساخن**: `string.Concat` لكل طلب، `ToList()`، closures، و`new JsonSerializerOptions` (ده الأخير كارثة — أنشئه مرة واحدة).
- **لا تقرأ جسم الطلب** إلا لو لازم فعلًا: `EnableBuffering()` = نسخ للذاكرة (وللملف لو كبير).
- **لا تعمل sync-over-async** (`.Result`/`.Wait()`) → تجويع thread pool.
- **اخرج مبكرًا**: لو Middleware يخص مسارًا معينًا، افحص `context.Request.Path.StartsWithSegments(...)` أول سطر و`return next(context)` فورًا.
- **`Response.OnStarting` مش داخل الـtry/finally بعد `next`**: بعد بدء الاستجابة تغيير الرؤوس بيرمي.
"""},
            {"type": "heading", "level": 2, "text": "الأخطاء: مين بيمسكها فعلًا؟"},
            {"type": "code", "lang": "text", "title": "القاعدة: الماسك لازم يكون *قبل* مصدر الخطأ في السلسلة", "code": r'''
طلب  ↓
 ┌─ UseExceptionHandler        ← يمسك أي استثناء من كل ما تحته
 │   UseSecurityHeaders
 │   UseCorrelationId
 │   UseRouting
 │   UseAuthentication          ← استثناء هنا: يُمسَك (ExceptionHandler فوقه)
 │   UseAuthorization
 │   Endpoint filters           ← استثناء هنا: يُمسَك أيضًا
 │   Endpoint handler           ← استثناء هنا: IExceptionHandler يتولاه
 └─ الاستجابة ↑ (تُبنى في طريق العودة — أول من يضيف رأسًا هو الأقرب للعميل)

★ لكن: لو الاستجابة **بدأت** (HasStarted = true) — مثلًا داخل streaming أو بعد كتابة جسم —
  لا يمكن تغيير الحالة ولا تحويل الخطأ لـproblem+json. الحل: افشل قبل الكتابة، أو استخدم
  قناة/طابور للأعمال الطويلة وأعد 202 مع مسار تقدم (درس SSE).
'''},
            {"type": "table", "head": ["الأداة", "النطاق", "أنسب استخدام"], "rows": [
                ["`IExceptionHandler`", "استثناءات غير معالجة في كل الـpipeline", "ترجمة استثناءات الـdomain لحالات HTTP + problem+json"],
                ["`UseExceptionHandler` + صفحة/مسار", "نفسه، بصيغة أقدم", "تطبيقات MVC/HTML أو معالجة مخصصة"],
                ["Endpoint filter `try/catch`", "endpoint أو مجموعة واحدة", "أخطاء متوقعة في مسار معين (validation, conflict)"],
                ["Middleware مخصص", "كل الطلبات أو مسارات مختارة", "سلوك غير مرتبط بالاستثناء (correlation, metrics, tenant)"],
                ["`Results.Problem`/TypedResults", "داخل الـhandler", "الحالات المتوقعة — الأفضل: لا ترمي استثناء أصلًا"],
                ["Polly / resilience", "حول استدعاءات خارجية", "timeout/retry/circuit breaker للتبعيات"],
            ]},
            {"type": "heading", "level": 2, "text": "Endpoint Filters: التركيب والترتيب"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Filters/IdempotencyFilter.cs", "title": "Filter حقيقي القيمة: منع التنفيذ المزدوج للكتابات", "code": r'''
/// <summary>
/// العميل يبعت `Idempotency-Key`؛ أول تنفيذ يُخزَّن ويُعاد نفس الرد للمفتاح نفسه.
/// مهم جدًا لعمليات الدفع/الإنشاء عند إعادة المحاولة من العميل أو الشبكة.
/// </summary>
public sealed class IdempotencyFilter(IIdempotencyStore store, TimeProvider time) : IEndpointFilter
{
    private static readonly TimeSpan Ttl = TimeSpan.FromHours(24);

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
    {
        var http = ctx.HttpContext;
        var key = http.Request.Headers["Idempotency-Key"].FirstOrDefault();

        // بلا مفتاح: نفّذ عادي (اجعل المفتاح إلزاميًا في endpoints محددة فقط)
        if (string.IsNullOrWhiteSpace(key) || key.Length > 128)
            return await next(ctx);

        var route = $"{http.Request.Method}:{http.Request.Path}";
        var scopeKey = $"{route}:{key}";

        // ✓ لو اتنفذ قبل كده: أعد نفس الاستجابة بدون تنفيذ المنطق مرة تانية
        if (await store.TryGetAsync(scopeKey, http.RequestAborted) is { } cached)
        {
            http.Response.Headers["Idempotency-Replayed"] = "true";
            return cached.Result;
        }

        // حجز المفتاح: لو طلب متوازٍ بنفس المفتاح → 409 بدل تنفيذين
        if (!await store.TryReserveAsync(scopeKey, time.GetUtcNow().Add(Ttl), http.RequestAborted))
            return TypedResults.Conflict(new ProblemDetails
            {
                Status = 409, Title = "طلب مماثل قيد المعالجة",
                Detail = "أعد المحاولة بعد لحظات بنفس Idempotency-Key.",
            });

        var result = await next(ctx);

        // خزّن النتيجة للطلبات اللاحقة (2xx فقط — لا تخزن فشلًا مؤقتًا)
        if (result is IStatusCodeHttpResult { StatusCode: >= 200 and < 300 } ok)
            await store.SaveAsync(scopeKey, ok, time.GetUtcNow().Add(Ttl), http.RequestAborted);
        else
            await store.ReleaseAsync(scopeKey, http.RequestAborted);

        return result;
    }
}

// التركيب: الترتيب = ترتيب الإضافة (الأول هو الخارجي)
var group = app.MapGroup("/api/orders")
    .AddEndpointFilter<TimingEndpointFilter>()          // 1) خارجي: يقيس الكل
    .AddEndpointFilter<ValidationEndpointFilter<CreateOrderRequest>>()   // 2) يرفض مبكرًا
    .AddEndpointFilter<IdempotencyFilter>();            // 3) داخل: ينفذ أو يعيد الرد
'''},
            {"type": "callout", "kind": "tip", "title": "قاعدة القرار: filter ولا middleware؟",
             "md": """
اسأل: **«هل السلوك ده يخص endpoint معين/مجموعة، ولا كل الطلبات؟»**
- يخص endpoint (validation، idempotency، authorization إضافي، تحويل نتيجة) → **Endpoint Filter** (أرخص، أوضح، قابل للتركيب).
- يخص كل الطلبات (correlation id، رؤوس أمان، metrics، tenant) → **Middleware**.
- يخص استثناءات من أي مكان → **`IExceptionHandler`**.

وفلتر واحد بيعمل حاجة واحدة. ثلاثة فلاتر صغيرة أوضح من فلتر واحد فيه 3 مسؤوليات —
لأن ترتيبهم هو اللي بيحدد السلوك.
"""},
            {"type": "checkpoints", "items": [
                "أرتب الـpipeline عن فهم وأعرف أثر كل تبديل على الأخطاء والأمان.",
                "أكتب conventional middleware (singleton) و`IMiddleware` (scoped) وأختار الصح بحسب الحاجة.",
                "أتجنب أخطاء الأداء: بلا قراءة جسم الطلب، بلا تخصيص في المسار الساخن، وخروج مبكر للمسارات غير المعنية.",
                "أستخدم Endpoint Filters للسلوك الخاص بالـendpoints وأركّبها بترتيب مقصود.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "conventional middleware بياخد `AppDbContext` في الـconstructor. إيه المشكلة؟",
                 "options": [
                     "بطء",
                     "الـmiddleware singleton والـDbContext scoped → استثناء عند الإقلاع أو سياق مغلق/مشترك",
                     "لا مشكلة",
                     "يفقد الترتيب",
                 ], "answer": 1,
                 "explain": "الحل: `IMiddleware` (يُحلّ لكل طلب) أو `IServiceScopeFactory` و`CreateAsyncScope()` داخل `InvokeAsync`."},
                {"q": "استثناء حصل بعد ما الاستجابة بدأت (`HasStarted = true`). إيه اللي هيحصل؟",
                 "options": [
                     "`IExceptionHandler` بيحوّله لـproblem+json عادي",
                     "ما يمكنش تغيير الحالة/الرؤوس؛ الاتصال بيتقطع أو بيكمل بجزء ناقص — لذا افشل قبل الكتابة أو استخدم 202 + مسار تقدّم",
                     "يُسجَّل فقط",
                     "يعيد المحاولة",
                 ], "answer": 1,
                 "explain": "ده سبب مهم لتصميم streaming/exports كـ202 Accepted + SSE بدل محاولة إرسال كل شيء في استجابة واحدة."},
                {"q": "`UseRateLimiter` قبل `UseAuthentication` — إيه الأثر؟",
                 "options": [
                     "لا أثر",
                     "ما تعرفش هوية المستخدم، فالتقسيم يبقى بـIP فقط — وورا proxy كل العملاء يبدون IP واحد",
                     "يرفض كل الطلبات",
                     "يبطئ المصادقة",
                 ], "answer": 1,
                 "explain": "الحد العادل يحتاج هوية. الترتيب الصحيح: مصادقة → تفويض → rate limiting → output cache → endpoints."},
                {"q": "ليه `new JsonSerializerOptions(...)` داخل middleware خطأ أداء؟",
                 "options": [
                     "يرمي استثناء",
                     "بناء cache التسلسل في كل طلب (تخصيص + إعادة حساب metadata) — أنشئه مرة واحدة static",
                     "يغيّر الترميز",
                     "لا خطأ",
                 ], "answer": 1,
                 "explain": "نفس القاعدة لأي كائن ثقيل: `RegexOptions.Compiled` regex، caches، pools. الـmiddleware بيتنفذ لكل طلب."},
                {"q": "idempotency + validation على نفس المجموعة — أنهي ترتيب صح؟",
                 "options": [
                     "idempotency أولًا ثم validation",
                     "validation أولًا (يرفض الطلبات الباطلة بلا حجز مفتاح)، ثم idempotency، ثم التنفيذ",
                     "لا فرق",
                     "لا يُركّبان معًا",
                 ], "answer": 1,
                 "explain": "لو idempotency بره: كل طلب باطل هيحجز مفتاحًا ويلوث المخزن. رتّب الفلاتر بحيث الأرخص والأكثر رفضًا في الخارج."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "correlation id من الطرف للطرف",
                 "md": "نفّذ `CorrelationIdMiddleware` بتنقية الرأس، وأضفه لكل الاستجابات ولـproblem+json (`traceId`/`correlationId`) وللسجلات (Serilog `LogContext`). تأكّد إنه بيظهر في اختبارات الـintegration من المرحلة 1.",
                 "criteria": [
                     "كل استجابة فيها `X-Correlation-Id` (حتى 404 و500)",
                     "رأس وارد صالح (16 حرفًا مثلًا) بيُعاد كما هو، وتالف بيُستبدل (اختباران)",
                     "أي سطر log داخل الطلب يحمل المعرّف",
                     "زمن الوسيط < 1ms في المسار الساخن (قِس بـStopwatch أو من الـmetrics)",
                 ],
                 "hint": "لو الرأس مش بيظهر في الاستجابات: استخدم `Response.OnStarting` بدل تعيينه بعد `next(context)` — بعد بدء الاستجابة التعديل بيرمي."},
                {"id": "t2", "title": "Idempotency للكتابات",
                 "md": "أضف `IdempotencyFilter` على `POST /api/orders` بمخزن في Redis أو جدول في القاعدة، بحيث إعادة نفس المفتاح ترجع نفس الاستجابة بلا تنفيذ ثانٍ، وطلبات متوازية بنفس المفتاح ترجع 409.",
                 "criteria": [
                     "طلب مكرر بنفس المفتاح → نفس الاستجابة + رأس `Idempotency-Replayed` (اختبار)",
                     "طلبان متوازيان بنفس المفتاح → واحد 201 والآخر 409 أو إعادة (اختبار)",
                     "فشل التنفيذ (500/400) لا يخزَّن كمفتاح مستهلَك",
                     "TTL واضح ومخزّن (مش في الذاكرة فقط) أو قرار موثق ليه في الذاكرة كافٍ",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "ASP.NET Core middleware", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/middleware/"},
                {"label": "Factory-based middleware (IMiddleware)", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/middleware/extensibility"},
                {"label": "Endpoint filters", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/filters"},
                {"label": "Error handling & IExceptionHandler", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/error-handling"},
                {"label": "High-performance logging with LoggerMessage", "url": "https://learn.microsoft.com/dotnet/core/extensions/high-performance-logging"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l5
    {
        "id": "s2-m1-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
من غير حدود، الـAPI بتاعك مفتوح لـ: تخمين كلمات السر، سحب بيانات بالجملة، هجمات استنزاف،
و«عميل واحد بوظ الخدمة للكل». الـRate Limiting المدمج في ASP.NET Core بيديك أربع استراتيجيات
وتقسيم (partitioning) بحسب المستخدم/المفتاح/IP — بس أغلب المشاكل العملية بتيجي من **مكان التطبيق**
ومن **مصدر الـIP ورا proxy**.

الدرس ده: استراتيجيات محددة، تقسيم عادل، 429 مع `Retry-After` صحيح، وحدود خاصة بالمصادقة.
"""},
            {"type": "terms", "items": [
                {"term": "Fixed Window", "def": "نافذة ثابتة (مثال: 100 طلب/دقيقة) مع عدّاد يُصفّر. بسيط لكن فيه «حدّ مزدوج» عند التقاء نافذتين."},
                {"term": "Sliding Window", "def": "نافذة منزلقة مجزّأة — أنعم من الثابتة، بتكلفة ذاكرة أعلى قليلًا."},
                {"term": "Token Bucket", "def": "دلو رموز: يسمح بانفجار (burst) ثم معدل ثابت — الأنسب لسلوك مستخدم حقيقي."},
                {"term": "Concurrency Limiter", "def": "يحدّ عدد الطلبات **المتزامنة** (مش المعدل) — حماية من استنزاف الموارد في عمليات بطيئة."},
                {"term": "Partitioning", "def": "تقسيم الحدود بمفتاح (user id، API key، IP) — عشان مستخدم ما يعاقبش الكل."},
                {"term": "Global limiter", "def": "حد افتراضي على كل الطلبات، مع استثناءات لمسارات محددة."},
                {"term": "429 + `Retry-After`", "def": "الاستجابة الصحيحة: حالة 429 ورأس يقول للعميل إمتى يرجع (ثوانٍ أو تاريخ HTTP)."},
                {"term": "`X-Forwarded-For`", "def": "الرأس اللي بيحمله الـproxy عن IP العميل الحقيقي — لازم تُفعّل `ForwardedHeaders` وإلا كل العملاء عنوانهم واحد."},
            ]},
            {"type": "table", "head": ["الاستراتيجية", "السلوك", "أنسب حالة"], "rows": [
                ["Fixed Window", "100 طلب في كل دقيقة تقويمية، يُصفّر", "حدود عامة بسيطة على API key"],
                ["Sliding Window", "100 طلب في آخر 60 ثانية (متزحلقة)", "عدالة أفضل، بلا «قفزة» عند حدود النافذة"],
                ["Token Bucket", "سعة 50 + تعبئة 10/ثانية", "تصفح مستخدم حقيقي: انفجار قصير ثم معدل ثابت"],
                ["Concurrency", "≤ 20 طلبًا متزامنًا", "تقارير/تصدير/استعلامات ثقيلة — حماية الموارد"],
                ["مزيج", "token bucket للمستخدم + concurrency للمسار", "الوضع الواقعي للإنتاج"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/RateLimiting/RateLimitSetup.cs", "title": "سياسات + تقسيم عالمي بحسب المستخدم ثم IP", "code": r'''
using System.Threading.RateLimiting;

public static class RateLimitSetup
{
    public static IServiceCollection AddApiRateLimiting(this IServiceCollection services, IConfiguration config)
    {
        var limits = config.GetSection("RateLimits").Get<RateLimitOptions>() ?? new RateLimitOptions();

        services.AddRateLimiter(options =>
        {
            options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

            // ── استجابة الرفض: 429 + Retry-After + problem+json (مش جسم فاضي)
            options.OnRejected = async (context, ct) =>
            {
                var response = context.HttpContext.Response;
                response.StatusCode = StatusCodes.Status429TooManyRequests;
                response.ContentType = "application/problem+json";

                // ✓ Retry-After من بيانات النافذة الحقيقية لما تتوفر
                if (context.Lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
                    response.Headers.RetryAfter =
                        ((int)Math.Ceiling(retryAfter.TotalSeconds)).ToString();
                else
                    response.Headers.RetryAfter = "30";

                // ✓ وسم بالـendpoint (مش بمسار خام) عشان القياس ما ينفجرش cardinality
                Metrics.RateLimitRejections.Add(1, new(
                    "endpoint", context.HttpContext.GetEndpoint()?.DisplayName ?? "unknown"));

                await response.WriteAsJsonAsync(new ProblemDetails
                {
                    Status = 429,
                    Title = "عدد الطلبات تجاوز الحد المسموح",
                    Detail = "قلّل معدل الطلبات أو استخدم الترقيم بالصفحات لتقليل عدد النداءات.",
                    Extensions =
                    {
                        ["traceId"] = context.HttpContext.TraceIdentifier,
                        ["retryAfterSeconds"] = response.Headers.RetryAfter.ToString(),
                    },
                }, ct);
            };

            // ── حد عام مقسّم: المستخدم المصادق أولًا، وإلا IP (مع مراعاة الـproxy)
            options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(http =>
            {
                // المسارات المستثناة: health العام والـstatic
                if (http.Request.Path.StartsWithSegments("/health/live"))
                    return RateLimitPartition.GetNoLimiter("health");

                var partitionKey = PartitionKeyFor(http);

                return RateLimitPartition.GetTokenBucketLimiter(partitionKey, _ => new TokenBucketRateLimiterOptions
                {
                    TokenLimit = limits.General.TokenLimit,          // 50
                    TokensPerPeriod = limits.General.ReplenishmentPeriod == default
                        ? 10 : limits.General.TokensPerPeriod,        // 10
                    ReplenishmentPeriod = limits.General.ReplenishmentPeriod, // 1 ثانية
                    QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                    QueueLimit = 0,                                     // لا طابور: ارفض فورًا
                    AutoReplenishment = true,
                });
            });

            // ── سياسات مسماة للـendpoints الحساسة
            options.AddPolicy("auth", http => RateLimitPartition.GetFixedWindowLimiter(
                PartitionKeyFor(http), _ => new FixedWindowRateLimiterOptions
                {
                    PermitLimit = limits.Auth.PermitLimit,            // 5
                    Window = TimeSpan.FromMinutes(5),
                    QueueLimit = 0,
                }));

            options.AddPolicy("orders-write", http => RateLimitPartition.GetSlidingWindowLimiter(
                PartitionKeyFor(http), _ => new SlidingWindowRateLimiterOptions
                {
                    PermitLimit = limits.Write.PermitLimit,           // 30
                    Window = TimeSpan.FromMinutes(1),
                    SegmentsPerWindow = 6,                            // دقة أعلى = أنعم
                    QueueLimit = 0,
                }));

            // ── حد تزامن للتقارير/التصدير (حماية موارد، مش معدل)
            options.AddPolicy("heavy", _ => RateLimitPartition.GetConcurrencyLimiter(
                "heavy-reports", _ => new ConcurrencyLimiterOptions
                {
                    PermitLimit = limits.Heavy.Concurrency,           // 20
                    QueueLimit = 5,
                    QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                }));
        });

        return services;
    }

    /// <summary>
    /// أولوية مفتاح التقسيم: مستخدم مصادق > API key > IP.
    /// ★ IP وحده ورا proxy = كل عملائك في حد واحد → ظلم أو ثغرة تجاوز.
    /// </summary>
    private static string PartitionKeyFor(HttpContext http)
    {
        var userId = http.User.FindFirst(JwtRegisteredClaimNames.Sub)?.Value
                  ?? http.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (!string.IsNullOrEmpty(userId)) return $"user:{userId}";

        var apiKey = http.Request.Headers["X-Api-Key"].FirstOrDefault();
        if (!string.IsNullOrEmpty(apiKey) && apiKey.Length <= 128) return $"key:{apiKey}";

        var ip = http.Connection.RemoteIpAddress?.ToString() ?? "unknown";
        return $"ip:{ip}";
    }
}

public sealed class RateLimitOptions
{
    public Bucket General { get; init; } = new() { TokenLimit = 50, TokensPerPeriod = 10, ReplenishmentPeriod = TimeSpan.FromSeconds(1) };
    public Window Auth { get; init; } = new() { PermitLimit = 5 };
    public Window Write { get; init; } = new() { PermitLimit = 30 };
    public Heavy Heavy { get; init; } = new() { Concurrency = 20 };

    public sealed class Bucket { public int TokenLimit { get; init; } public int TokensPerPeriod { get; init; } public TimeSpan ReplenishmentPeriod { get; init; } }
    public sealed class Window { public int PermitLimit { get; init; } }
    public sealed class Heavy { public int Concurrency { get; init; } }
}

public static class Metrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Api", "1.0.0");
    public static readonly Counter<long> RateLimitRejections =
        Meter.CreateCounter<long>("ratelimit.rejections", description: "عدد الـ429");
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "رؤوس التحويل: بلا ضبطها، الـIP غلط ورا الـproxy", "code": r'''
// ✓ قبل UseRateLimiter (وقبل تسجيل الطلبات) — عشان RemoteIpAddress يبقى العميل الحقيقي
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;

    // ★ أمان: ثق فقط في الـproxies بتاعتك — وإلا أي عميل يزوّر X-Forwarded-For
    //   ويتجاوز الحدود (أو يخفي عنوانه)
    options.KnownProxies.Add(IPAddress.Parse(config["Infrastructure:ProxyIp"]!));
    // أو للشبكات الداخلية: options.KnownNetworks.Add(new IPNetwork(...));

    options.ForwardLimit = 2;                       // حد لعدد القفزات الموثوقة
});

var app = builder.Build();
app.UseForwardedHeaders();
// ... المصادقة والتفويض
app.UseRateLimiter();                               // ← بعد المصادقة عشان التقسيم بالمستخدم
app.UseOutputCache();
'''},
            {"type": "callout", "kind": "danger", "title": "ثغرتان في الـrate limiting بيعملهم الناس بالغلط",
             "md": """
**① الثقة في `X-Forwarded-For` من أي مصدر**: لو `KnownProxies` فاضية/مفتوحة، العميل يبعت
`X-Forwarded-For: 1.2.3.4` عشوائي في كل طلب → مفتاح تقسيم جديد كل مرة → **بلا حدود فعلية**.
الحل: حدد الـproxies الموثوقة صراحة، أو استخدم العنوان من الاتصال مباشرة لو مفيش proxy.

**② الاعتماد على الـrate limiting وحده ضد تخمين كلمات السر**: الحد بـIP ما يوقفش مهاجم بشبكة
بوتات. لازم معاه: **lockout على الحساب** (درس Identity)، وCAPTCHA/OTP بعد N فشل،
ومراقبة أنماط (نفس الحساب من IPs كتير)، وحد على **الحساب** كمان مش على المصدر فقط.
"""},
            {"type": "heading", "level": 2, "text": "تطبيق الحدود على الـendpoints"},
            {"type": "code", "lang": "csharp", "title": "سياسات على مجموعات وendpoints محددة", "code": r'''
// مجموعة كلها تحت سياسة الكتابة
var orders = app.MapGroup("/api/orders")
    .RequireAuthorization(Policies.CustomerOrAdmin)
    .RequireRateLimiting("orders-write");

// endpoint واحد أثقل → سياسة مختلفة (بتتجاوز سياسة المجموعة)
orders.MapGet("/export", ExportOrders)
    .RequireRateLimiting("heavy")
    .RequireAuthorization(Policies.AdminOnly);

// مسار عام بلا حد (أو بحد مختلف)
app.MapGet("/api/catalog/products", ListProducts)
    .DisableRateLimiting();          // ← قرار صريح وموثق، مش نسيان

// المصادقة: أشد الحدود + تفاعل مع lockout
var auth = app.MapGroup("/api/auth").RequireRateLimiting("auth");
auth.MapPost("/login", Login).AllowAnonymous();
auth.MapPost("/password/forgot", Forgot).AllowAnonymous();

// Controllers: بنفس الأسماء
[EnableRateLimiting("orders-write")]
public sealed class OrdersController : ControllerBase { }

[DisableRateLimiting]
public IActionResult Health() => Ok();
'''},
            {"type": "heading", "level": 2, "text": "حدود المصادقة: الطبقات مع بعض"},
            {"type": "table", "head": ["الطبقة", "الحد", "الهدف"], "rows": [
                ["Rate limit على المصدر (IP/API key)", "5 محاولات/5 دقائق", "إبطاء الهجوم الآلي"],
                ["Lockout على الحساب (Identity)", "5 فشل → 15 دقيقة قفل", "حماية حساب محدد من التخمين"],
                ["حد على (الحساب + المصدر) معًا", "3 فشل → CAPTCHA/OTP", "كشف credential stuffing"],
                ["حد عالمي على `/api/auth/*`", "مثال: 100/دقيقة لكل النسخ", "حماية من هجمات كثيفة"],
                ["تأخير متدرج (tarpit)", "200ms → 1s بعد فشل", "رفع تكلفة الهجوم بلا أثر على المستخدم الشرعي"],
                ["مراقبة وتنبيه", "تنبيه عند 401 متكررة لنفس الحساب", "كشف قبل الضرر"],
            ]},
            {"type": "callout", "kind": "warn", "title": "حدود الموزّع: المحدد في الذاكرة لكل نسخة",
             "md": """
`AddRateLimiter` الافتراضي **في ذاكرة العملية**: مع 4 نسخ، الحد الفعلي = 4× المحدد (والتوزيع غير متساوٍ).

الخيارات:
1. **اقبلها واعكسها في الأرقام**: اضبط الحد للنسخة (مثال: 25 بدل 100) — بسيط لكن غير دقيق مع توزيع غير متساوٍ.
2. **حد مركزي في Redis**: `PartitionedRateLimiter` مخصص بيعدّ في Redis (Lua script للذرية) — أدق، بتكلفة شبكة لكل طلب.
3. **الحد عند الحافة**: API Gateway (YARP/Kong/Envoy) أو خدمة إدارة API — الأفضل تشغيليًا للأنظمة الكبيرة.

وفي كل الحالات: **الـ429 لازم يكون متسقًا** — لا خلي العميل يشوف حدود مختلفة بحسب النسخة اللي وصلها.
"""},
            {"type": "code", "lang": "csharp", "title": "جانب العميل: احترم 429 بدل ما تكسر الخدمة", "code": r'''
// Polly: انتظار مع backoff أسي + jitter، واحترام Retry-After
builder.Services.AddHttpClient("partner", client =>
{
    client.Timeout = TimeSpan.FromSeconds(10);
})
.AddTransientHttpErrorPolicy(p => p
    .WaitAndRetryAsync(
        retryCount: 3,
        sleepDurationProvider: (attempt, response, ctx) =>
        {
            // ✓ لو الخادم قال إمتى نرجع — اسمعه (بدل تخمين عشوائي)
            if (response?.Headers.RetryAfter?.Delta is { } delta) return delta;
            if (response?.Headers.RetryAfter?.Date is { } date) return date - DateTimeOffset.UtcNow;

            var baseDelay = TimeSpan.FromSeconds(Math.Pow(2, attempt));
            var jitter = TimeSpan.FromMilliseconds(Random.Shared.Next(0, 500));
            return baseDelay + jitter;
        },
        onRetryAsync: (outcome, delay, attempt, ctx) =>
        {
            Log.Warning("retry {Attempt} after {Delay} (status={Status})",
                attempt, delay, outcome.Result?.StatusCode);
            return Task.CompletedTask;
        }));
'''},
            {"type": "checkpoints", "items": [
                "أختار الاستراتيجية (fixed/sliding/token bucket/concurrency) بحسب السلوك المطلوب.",
                "أقسّم الحدود بالمستخدم ثم المفتاح ثم IP، وأضبط `ForwardedHeaders` بـproxies موثوقة فقط.",
                "أرجّع 429 مع `Retry-After` وproblem+json وقياس للرفض.",
                "أطبق حدودًا متعددة الطبقات على المصادقة، وأفهم حدود المحدد في الذاكرة مع تعدد النسخ.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `UseRateLimiter()` بعد `UseAuthentication()`؟",
                 "options": [
                     "متطلب الإطار",
                     "عشان مفتاح التقسيم يبقى المستخدم الحقيقي (أعدل وأصعب تجاوزًا من IP)",
                     "لتقليل الـ429",
                     "لا علاقة",
                 ], "answer": 1,
                 "explain": "قبل المصادقة ما تعرفش مين المستخدم، فالتقسيم كله بـIP — وورا proxy/NAT ده معناه ظلم جماعي."},
                {"q": "الفرق بين Token Bucket وFixed Window؟",
                 "options": [
                     "لا فرق",
                     "Bucket يسمح بانفجار قصير ثم معدل ثابت؛ Fixed Window بيصفّر العدّاد فيسمح بضعف الحد عند التقاء نافذتين",
                     "Bucket أبطأ",
                     "Fixed Window أدق دائمًا",
                 ], "answer": 1,
                 "explain": "مشكلة «الحد المزدوج» في النوافذ الثابتة معروفة: 100 في آخر ثانية من نافذة + 100 في أول ثانية من التالية."},
                {"q": "`X-Forwarded-For` من عميل غير موثوق — الخطر؟",
                 "options": [
                     "بطء",
                     "تزوير مفتاح التقسيم كل طلب → تجاوز كامل للحدود (أو إخفاء المصدر)",
                     "401",
                     "تسريب بيانات",
                 ], "answer": 1,
                 "explain": "`KnownProxies`/`KnownNetworks` صريحة + `ForwardLimit` هي الحماية. غير كده أي حد يبدّل IP."},
                {"q": "Concurrency limiter بيحمي من إيه بالتحديد؟",
                 "options": [
                     "عدد الطلبات في الدقيقة",
                     "عدد الطلبات **المتزامنة** — استنزاف الموارد بعمليات بطيئة (تقارير/تصدير)",
                     "حجم الجسم",
                     "التخمين",
                 ], "answer": 1,
                 "explain": "20 طلب تصدير بطيء في نفس اللحظة ممكن ياكل كل الـconnections والذاكرة، رغم إن المعدل في الدقيقة منخفض."},
                {"q": "4 نسخ والحد 100/دقيقة في الذاكرة لكل نسخة. الحد الفعلي؟",
                 "options": [
                     "100",
                     "حتى 400 (وغير متساوٍ) — اضبط الحد لكل نسخة أو استخدم مخزنًا مركزيًا/بوابة",
                     "25",
                     "لا يتغير",
                 ], "answer": 1,
                 "explain": "قرار معماري: دقة الحد مقابل تكلفة/تعقيد. الأنظمة الكبيرة بتحط الحدود عند الحافة (gateway)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "حدود مطبقة ومختبرة",
                 "md": "أضف 3 سياسات على مشروعك: `auth` (ثابت صارم)، `orders-write` (منزلق)، `heavy` (تزامن للتصدير). اضبط `OnRejected` بـproblem+json و`Retry-After`، وطبّق `ForwardedHeaders` بـproxy موثوق. اكتب اختبارات تتجاوز كل حد.",
                 "criteria": [
                     "اختبار يتجاوز حد `auth` ويؤكد 429 + `Retry-After` + `application/problem+json`",
                     "اختبار يثبت إن مستخدمين مختلفين لهم حدود مستقلة (واحد وصل الحد والتاني لسه 200)",
                     "مسار `/health/live` مستثنى ولا يتأثر",
                     "قياس `ratelimit.rejections` يظهر في الـmetrics",
                     "رأس `X-Forwarded-For` من مصدر غير موثوق **لا** يغيّر مفتاح التقسيم (اختبار)",
                 ],
                 "hint": "في اختبارات الـintegration، استخدم `factory.CreateAuthenticatedClient(...)` بحسابين مختلفين، و`WithWebHostBuilder` لضبط حدود صغيرة (مثال: 2 طلبات/دقيقة) عشان الاختبار يبقى سريعًا."},
                {"id": "t2", "title": "دفاع متعدد الطبقات على تسجيل الدخول",
                 "md": "ارسم وطبّق الدفاع على `/api/auth/login`: rate limit على المصدر + lockout على الحساب + تأخير متدرج بعد الفشل + تنبيه عند تكرار 401. وثّق القرار في `CAPSTONE.md`/ADR.",
                 "criteria": [
                     "5 محاولات فاشلة → 429 أو 423 (محدد ومختبر)",
                     "الحساب بيتقفل 15 دقيقة بعد 5 فشل (من درس Identity) ومختبر",
                     "لا رسالة تكشف هل الحساب موجود",
                     "حدث سجل/تنبيه عند نمط تخمين (نفس الحساب من مصادر متعددة)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Rate limiting in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/rate-limit"},
                {"label": "Forwarded Headers middleware", "url": "https://learn.microsoft.com/aspnet/core/host-and-deploy/proxy-load-balancer"},
                {"label": "System.Threading.RateLimiting", "url": "https://learn.microsoft.com/dotnet/api/system.threading.ratelimiting"},
                {"label": "RFC 6585 — 429 Too Many Requests", "url": "https://www.rfc-editor.org/rfc/rfc6585"},
                {"label": "Polly", "url": "https://www.pollydocs.org/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l6
    {
        "id": "s2-m1-l6",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الكاش أسرع تحسين أداء متاح — وهو أسرع طريق لباج «البيانات القديمة» لو اتعمل بلا استراتيجية إبطال.
المشكلة إن الناس بتقول «هنعمل كاش» كأنها قرار واحد، بينما فيه **خمس طبقات** مختلفة المكان والتكلفة والدقة:
من المتصفح والـCDN، لـoutput cache في الخادم، لـ`IMemoryCache`، لـdistributed cache،
و**HybridCache** (اللي بيجمع الطبقتين مع حماية من stampede).

الدرس ده: تختار الطبقة الصح، تضبط الإبطال بشكل مقصود، وتقيس الأثر الفعلي بالأرقام.
"""},
            {"type": "terms", "items": [
                {"term": "Client/CDN cache", "def": "`Cache-Control`, `ETag`, `Last-Modified` — أقرب طبقة للمستخدم وأرخصها (الطلب ما يوصلش لخادمك)."},
                {"term": "Response Caching", "def": "كاش خادمي يحترم توجيهات العميل (`Cache-Control`) — يعمل كـcache وسيط متوافق."},
                {"term": "Output Caching", "def": "كاش خادمي **بقراراتك أنت** (سياسات، وسوم، إبطال) — بيتجاهل توجيهات العميل لما تريد."},
                {"term": "`IMemoryCache`", "def": "كاش داخل العملية. الأسرع، لكنه لكل نسخة، ولا يتشارك، وبيرجع **نفس مرجع الكائن**."},
                {"term": "`IDistributedCache`", "def": "كاش مشترك (Redis غالبًا) بقيم مُسلسلة — أبطأ من الذاكرة لكنه متسق بين النسخ."},
                {"term": "`IHybridCache`", "def": ".NET 9+: L1 في الذاكرة + L2 موزّع + **حماية من stampede** + إبطال بوسوم."},
                {"term": "Cache Stampede", "def": "لحظة انتهاء صلاحية مفتاح ساخن: مئات الطلبات المتزامنة كلها بتعيد الحساب على المصدر."},
                {"term": "Tag-based invalidation", "def": "إبطال مجموعة مفاتيح بوسم (`catalog`, `orders:{id}`) بدل تتبع كل مفتاح."},
            ]},
            {"type": "table", "head": ["الطبقة", "المكان", "الإبطال", "التكلفة", "أنسب حالة"], "rows": [
                ["Client/CDN", "المتصفح/الحافة", "`Cache-Control`/`ETag`/purge", "الأرخص", "أصول ثابتة، بيانات عامة قليلة التغير"],
                ["Output Cache", "خادمك (أو Redis في .NET 8+)", "وسوم + TTL + `EvictByTag`", "رخيصة", "استجابات endpoints كاملة (قوائم، كتالوج)"],
                ["Response Cache", "خادمك", "يوجيهات العميل", "رخيصة", "APIs عامة تحترم `Cache-Control`"],
                ["`IMemoryCache`", "ذاكرة العملية", "TTL/حجم/يدوي", "الأسرع", "بيانات مرجعية صغيرة، إعدادات، lookups"],
                ["`IDistributedCache`", "Redis", "TTL/حذف مفتاح", "شبكة لكل طلب", "جلسات، بيانات مشتركة بين النسخ"],
                ["`IHybridCache`", "ذاكرة + Redis", "مفتاح/وسم + TTL", "متوازنة", "★ الافتراضي الجديد: بيانات محسوبة غالية + تعدد نسخ"],
            ]},
            {"type": "heading", "level": 2, "text": "HybridCache: الاختيار الافتراضي في .NET 9/10"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Microsoft.Extensions.Caching.Hybrid
dotnet add Shop.Api package Microsoft.Extensions.Caching.StackExchangeRedis   # للـL2
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Caching/CachingSetup.cs", "title": "L1 + L2 + وسوم + إبطال مقصود", "code": r'''
using Microsoft.Extensions.Caching.Hybrid;

public static class CachingSetup
{
    public static IServiceCollection AddAppCaching(this IServiceCollection services, IConfiguration config)
    {
        // L2: Redis مشترك بين النسخ
        services.AddStackExchangeRedisCache(options =>
        {
            options.Configuration = config.GetConnectionString("Redis");
            options.InstanceName = "shop:";                        // عزل منطقي لو Redis مشترك
        });

        // L1 + L2 مع حماية من stampede
        services.AddHybridCache(options =>
        {
            options.DefaultEntryOptions = new HybridCacheEntryOptions
            {
                Expiration = TimeSpan.FromMinutes(10),             // صلاحية إجمالية (L2)
                LocalCacheExpiration = TimeSpan.FromSeconds(30),   // صلاحية الذاكرة (L1) — أقصر عمدًا
            };
            options.MaximumPayloadBytes = 1024 * 512;              // ✓ ارفض القيم الضخمة (512KB)
            options.MaximumKeyLength = 256;
        });

        // Output cache للـendpoints الكاملة (أرخص من حساب أي شيء)
        services.AddOutputCache(options =>
        {
            options.AddBasePolicy(p => p.Expire(TimeSpan.FromMinutes(1)));

            options.AddPolicy("catalog", p => p
                .Expire(TimeSpan.FromMinutes(10))
                .Tag("catalog")
                .SetVaryByQuery("page", "size", "sort", "country"));   // ★ لا تخزّن كل المتغيرات كمفتاح واحد

            options.AddPolicy("reports", p => p
                .Expire(TimeSpan.FromHours(1))
                .Tag("reports")
                .SetVaryByAuthorizedUser());                            // ✓ بيانات المستخدم لا تُخلط
        });

        return services;
    }
}

/// <summary>
/// مثال الاستخدام: حساب غالي (تجميع مبيعات) محمي من stampede وبوسوم للإبطال.
/// </summary>
public sealed class SalesReportService(IHybridCache cache, AppDbContext db, TimeProvider time)
{
    public Task<DailySales> GetDailyAsync(DateOnly day, CancellationToken ct) =>
        cache.GetOrCreateAsync(
            key: $"sales:daily:{day:yyyy-MM-dd}",
            factory: async token => await ComputeAsync(day, token),
            options: new HybridCacheEntryOptions
            {
                Expiration = day < DateOnly.FromDateTime(time.GetUtcNow().UtcDateTime)
                    ? TimeSpan.FromHours(6)          // يوم ماضٍ: لا يتغير → صلاحية أطول
                    : TimeSpan.FromMinutes(2),       // اليوم الجاري: يتغير باستمرار
                LocalCacheExpiration = TimeSpan.FromSeconds(20),
            },
            tags: ["sales", $"sales:{day:yyyy-MM-dd}"],
            cancellationToken: ct);

    /// <summary>الإبطال المقصود بعد أي كتابة تؤثر على التقرير.</summary>
    public async Task InvalidateAsync(DateOnly day, CancellationToken ct)
    {
        await cache.RemoveByTagAsync($"sales:{day:yyyy-MM-dd}", ct);
        await cache.RemoveByTagAsync("sales", ct);      // وسوم مجمّعة لو فيه تقارير مشتقة
    }

    private async Task<DailySales> ComputeAsync(DateOnly day, CancellationToken ct)
    {
        var from = day.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var to = from.AddDays(1);

        var rows = await db.Orders
            .AsNoTracking()
            .Where(o => o.CreatedAt >= from && o.CreatedAt < to && o.Status != OrderStatus.Cancelled)
            .GroupBy(o => o.Customer.Country)
            .Select(g => new CountrySales(g.Key, g.Count(), g.Sum(o => o.Total)))
            .ToListAsync(ct);

        return new DailySales(day, rows, rows.Sum(r => r.Total), rows.Sum(r => r.Count));
    }
}

public sealed record CountrySales(string Country, int Orders, decimal Total);
public sealed record DailySales(DateOnly Day, IReadOnlyList<CountrySales> ByCountry, decimal Total, int Orders);
'''},
            {"type": "callout", "kind": "tip", "title": "ليه `LocalCacheExpiration` أقصر من `Expiration`؟",
             "md": """
دي أهم ضبط في HybridCache:
- **L2 (Redis)** = مصدر الحقيقة المشترك، صلاحيته أطول.
- **L1 (الذاكرة)** = نسخة محلية سريعة لكل نسخة من التطبيق — صلاحياتها أقصر عشان الإبطال ما يتأخرش.

إبطال بوسم بينسخ الـL2 وبيبلّغ النسخ، لكن لو عندك نشر/إعادة تشغيل أو شبكة Pub/Sub معطّلة،
الـL1 القصير بيضمن إن أقدم نسخة خاطئة عمرها ≤ 30 ثانية. قرّر الرقم بحسب **أقصى قدر مقبول من القدم**
(staleness) لبياناتك — مش بحسب الأداء.
"""},
            {"type": "heading", "level": 2, "text": "Output Cache + إبطال بعد الكتابة"},
            {"type": "code", "lang": "csharp", "title": "كاش للاستجابة كاملة، وإبطال عند أي تغيير في الكتالوج", "code": r'''
// ── القراءة: سياسة "catalog"
catalog.MapGet("/products", ListProducts)
    .CacheOutput("catalog")
    .Produces<PagedResult<ProductSummary>>();

// ★ Output cache بيتنوّع تلقائيًا بحسب الـURL (path + query) — فـ/products/{id}
//   بيتخزّن لكل id على حدة. الوسم المشترك "catalog" كافٍ للإبطال الجماعي.
catalog.MapGet("/products/{id:guid}", GetProduct)
    .CacheOutput("catalog");

// ── الكتابة: إبطال مقصود بعد نجاح الحفظ
catalog.MapPut("/products/{id:guid}", async (
    Guid id, UpdateProductRequest request, AppDbContext db,
    IOutputCacheStore outputCache, IHybridCache hybrid, CancellationToken ct) =>
{
    var product = await db.Products.FirstOrDefaultAsync(p => p.Id == id, ct)
                  ?? throw new NotFoundException("Product", id);

    product.Name = request.Name;
    product.Price = request.Price;
    await db.SaveChangesAsync(ct);                       // ✓ احفظ أولًا

    await outputCache.EvictByTagAsync("catalog", ct);    // ← كل قوائم وتفاصيل الكتالوج
    await hybrid.RemoveByTagAsync("catalog", ct);        // ← البيانات المحسوبة في HybridCache

    return TypedResults.NoContent();
}).RequireAuthorization(Policies.AdminOnly);
'''},
            {"type": "heading", "level": 2, "text": "ETag وconditional GET: توفير حتى مع كاش الخادم"},
            {"type": "code", "lang": "csharp", "title": "304 Not Modified — ASP.NET Core لا يفعلها تلقائيًا", "code": r'''
catalog.MapGet("/products/{id:guid}", async (
    Guid id, AppDbContext db, HttpContext http, CancellationToken ct) =>
{
    var product = await db.Products.AsNoTracking()
        .Where(p => p.Id == id)
        .Select(p => new { p.Id, p.Name, p.Price, p.UpdatedAt, p.RowVersion })
        .FirstOrDefaultAsync(ct);

    if (product is null) throw new NotFoundException("Product", id);

    // ✓ ETag من عمود إصدار حقيقي (RowVersion) — أقوى من hash للمحتوى
    var etag = new EntityTagHeaderValue($"\"{Convert.ToHexString(product.RowVersion)}\"");

    if (http.Request.Headers.IfNoneMatch.ToString() is { Length: > 0 } match
        && match.Trim('"') == etag.Tag.Trim('"'))
    {
        http.Response.StatusCode = StatusCodes.Status304NotModified;
        http.Response.Headers.ETag = etag.Tag;
        return Results.Empty;                            // بلا جسم — توفير شبكة حقيقي
    }

    http.Response.Headers.ETag = etag.Tag;
    http.Response.Headers.CacheControl = "private, max-age=30, must-revalidate";
    return TypedResults.Ok(new ProductResponse(product.Id, product.Name, product.Price));
});
'''},
            {"type": "callout", "kind": "danger", "title": "5 طرق يخرّب بيها الكاش مشروعك",
             "md": """
1. **`IMemoryCache` بيرجع نفس المرجع**: لو خزّنت كائنًا قابلًا للتعديل، أي طلب بيعدّل فيه بيأثر على **كل** الطلبات. خزّن records/قيم غير قابلة للتغيير، أو نسخة.
2. **كاش لبيانات خاصة على مفتاح عام**: `products:list` مخزّن لمستخدم فيه أسعاره الخاصة → تسريب. استخدم `SetVaryByAuthorizedUser()` أو ضمّن معرّف المستخدم في المفتاح.
3. **بلا إبطال**: TTL وحده معناه «بيانات قديمة لمدة TTL». أي كتابة تؤثر على القراءة لازم تبطل الكاش (أو تخلي المفتاح بإصدار: `key:v2:`).
4. **stampede**: مفتاح ساخن بينتهي → 500 طلب بيحسبوا نفس الشيء على القاعدة. HybridCache بيحلها (نداء واحد للمصنع)، ولو استخدمت `IMemoryCache` احمِها بـ`SemaphoreSlim` لكل مفتاح.
5. **كاش كحل لاستعلام بطيء**: الكاش بيخفي المشكلة ويخليها تظهر فجأة. أصلح الاستعلام/الفهرس أولًا، وبعدين اعمل كاش لو لسه مستحق.
"""},
            {"type": "heading", "level": 2, "text": "قياس الأثر: بلا أرقام الكاش تخمين"},
            {"type": "code", "lang": "csharp", "title": "عدّادات hit/miss — بدونها ما تعرفش هل الكاش بيشتغل أصلًا", "code": r'''
public static class CacheMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Api.cache", "1.0.0");

    public static readonly Counter<long> Hits =
        Meter.CreateCounter<long>("cache.hits", description: "ضربات الكاش");
    public static readonly Counter<long> Misses =
        Meter.CreateCounter<long>("cache.misses", description: "إخفاقات الكاش");
    public static readonly Histogram<double> LoadDuration =
        Meter.CreateHistogram<double>("cache.load.duration", unit: "s");
    public static readonly Counter<long> Evictions =
        Meter.CreateCounter<long>("cache.evictions", description: "عمليات الإبطال");
}

/// <summary>لفّ حول أي حساب عشان تقيس نسبة الإصابة وتكلفة التحميل.</summary>
public sealed class MeasuredCache(IHybridCache inner)
{
    public async Task<T> GetAsync<T>(string key, Func<CancellationToken, ValueTask<T>> factory,
        IEnumerable<string>? tags, CancellationToken ct)
    {
        var hit = true;
        var result = await inner.GetOrCreateAsync(key, async token =>
        {
            hit = false;                                  // المصنع بيشتغل = miss
            var started = TimeProvider.System.GetTimestamp();
            var value = await factory(token);
            CacheMetrics.LoadDuration.Record(
                TimeProvider.System.GetElapsedTime(started).TotalSeconds, new("key", key));
            return value;
        }, tags: tags, cancellationToken: ct);

        if (hit) CacheMetrics.Hits.Add(1, new("key", key));
        else CacheMetrics.Misses.Add(1, new("key", key));

        return result;
    }
}
'''},
            {"type": "table", "head": ["القياس", "قبل الكاش", "بعد الكاش", "الهدف"], "rows": [
                ["p50 لزمن الاستجابة", "—", "—", "تحسّن واضح على المسار الساخن"],
                ["p95 لزمن الاستجابة", "—", "—", "الأهم: الذيل هو اللي بيكسر UX"],
                ["نسبة الإصابة (hits/total)", "0%", "—", "> 70% للمسارات العامة"],
                ["عدد الاستعلامات لكل طلب", "—", "—", "انخفاض ملموس"],
                ["حمل القاعدة (CPU/connections)", "—", "—", "انخفاض تحت نفس الـRPS"],
                ["RPS قصوى مستقرة", "—", "—", "زيادة قبل بدء التدهور"],
                ["تكلفة التسلسل/الشبكة للـL2", "—", "—", "أقل من تكلفة الحساب وإلا الكاش خسارة"],
            ]},
            {"type": "callout", "kind": "note", "title": "إمتى الكاش **مش** الحل",
             "md": """
- بيانات لازم تكون محدثة فورًا (رصيد، مخزون أثناء الشراء) → استخدم حجز/transaction بدل الكاش.
- استعلام بطيء بسبب غياب فهرس → الفهرس حل أرخص وأدق.
- استجابة مختلفة لكل مستخدم → الكاش قليل القيمة (أو يحتاج vary by user بتكلفة ذاكرة).
- نسبة إصابة < 20% → أنت بتدفع تكلفة تسلسل وشبكة بلا عائد؛ راجع المفاتيح وTTL.
- مشكلة استقرار (spikes/tail latency) سببها GC أو استنزاف thread pool → الكاش بيخفيها ولا يحلها.
"""},
            {"type": "checkpoints", "items": [
                "أختار طبقة الكاش المناسبة (CDN/OutputCache/HybridCache/IMemoryCache) بحسب المكان والتكلفة ودقة الإبطال.",
                "أضبط `HybridCache` بوسوم و`LocalCacheExpiration` أقصر وأحمي من stampede.",
                "أبطل الكاش بعد كل كتابة مؤثرة وأتعامل مع ETag/304.",
                "أقيس نسبة الإصابة وزمن الاستجابة قبل/بعد، وأعرف متى الكاش ليس الحل.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه الفرق الجوهري بين Response Caching وOutput Caching؟",
                 "options": [
                     "لا فرق",
                     "Response Caching بيحترم توجيهات العميل (`Cache-Control`) كوسيط؛ Output Caching قرار خادمي بسياسات ووسوم وإبطال تحت سيطرتك",
                     "Output Caching أقدم",
                     "Response Caching أسرع دائمًا",
                 ], "answer": 1,
                 "explain": "للـAPIs اللي بتتحكم فيها، Output Caching أقوى: وسوم، إبطال بعد الكتابة، vary by query/user."},
                {"q": "خزّنت `List<Product>` في `IMemoryCache` وطلب عدّل عنصر فيها. إيه اللي حصل؟",
                 "options": [
                     "لا شيء — نسخة مستقلة",
                     "الكاش بيرجع نفس المرجع → التعديل أثر على كل الطلبات اللاحقة (باج بيانات مشترك)",
                     "استثناء",
                     "إبطال تلقائي",
                 ], "answer": 1,
                 "explain": "خزّن أنواع غير قابلة للتغيير (records/collections ثابتة) أو نسخة دفاعية. ده من أشهر مصائب `IMemoryCache`."},
                {"q": "Cache stampede بيحصل إمتى و`IHybridCache` بيحلها إزاي؟",
                 "options": [
                     "عند بدء التشغيل فقط — بحلها بالـwarm-up",
                     "عند انتهاء صلاحية مفتاح ساخن: طلبات متزامنة كتير تحسب نفس الشيء؛ HybridCache بيخلي نداء واحد فقط ينفّذ المصنع والباقي يستنى",
                     "عند حذف Redis",
                     "لا تحلها المكتبة",
                 ], "answer": 1,
                 "explain": "مع `IMemoryCache` العادي لازم تنفذ الحماية بنفسك (`SemaphoreSlim`/`Lazy<T>` لكل مفتاح)."},
                {"q": "endpoint مخزّن بـOutput Cache ومطلوب مصادقة وبيحتوي بيانات المستخدم. الخطر؟",
                 "options": [
                     "بطء",
                     "تقديم استجابة مستخدم لمستقبل مختلف → تسريب بيانات. الحل: `SetVaryByAuthorizedUser()` أو ضمّن الهوية في المفتاح أو لا تخزّن",
                     "401",
                     "فشل الإبطال",
                 ], "answer": 1,
                 "explain": "الكاش ما يعرفش «لمين» الاستجابة تلقائيًا. أي تخزين لبيانات خاصة لازم يتنوع بحسب الهوية."},
                {"q": "نسبة إصابة الكاش 12% وزمن الاستجابة ما اتحسنش. أنهي استنتاج سليم؟",
                 "options": [
                     "زِد TTL وخليه كده",
                     "المفاتيح/TTL غير مناسبة أو البيانات شديدة التخصيص — الكاش بيكلف (تسلسل/شبكة) بلا عائد؛ راجع التصميم أو أصلح الاستعلام",
                     "احذف Redis",
                     "زد حجم الذاكرة",
                 ], "answer": 1,
                 "explain": "الكاش قرار اقتصادي: عائد (حساب متجنب) مقابل تكلفة (تسلسل + شبكة + تعقيد إبطال). 12% عادةً خسارة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "طبقتان بكاش مع إبطال صحيح",
                 "md": "طبّق Output Cache على مسار قراءة عام، وHybridCache على حساب غالي (تقرير/تجميع) بوسوم. أضف إبطالًا بعد كل كتابة مؤثرة، وعدّادات hit/miss. قِس p50/p95 قبل وبعد بحمل k6 من درس الـcapstone.",
                 "criteria": [
                     "اختبار يثبت إن الكتابة تبطل الكاش (القراءة بعد الكتابة ترجع القيمة الجديدة)",
                     "نسبة إصابة مسجلة > 50% تحت حمل متكرر لنفس المسار",
                     "جدول قبل/بعد فيه p50 وp95 وأرقام حقيقية",
                     "`LocalCacheExpiration` أقصر من `Expiration` مع تبرير الرقم",
                     "لا كاش لبيانات خاصة على مفتاح عام (مراجعة المفاتيح)",
                 ],
                 "hint": "لو الاختبار «الكتابة تبطل الكاش» بيفشل عشوائيًا: غالبًا فيه نسخة L1 في عملية الاختبار ما اتبطلتش — تأكد إنك بتبطل الوسوم في **الطبقتين** (OutputCache store + HybridCache) وبنفس الترتيب بعد `SaveChangesAsync`."},
                {"id": "t2", "title": "ETag و304",
                 "md": "أضف ETag مبني على `RowVersion`/`UpdatedAt` لمسار قراءة واحد، وردّ 304 عند `If-None-Match` مطابق. اكتب اختبارين: طلب أول 200 مع ETag، وطلب ثانٍ بنفس الـETag يرجع 304 بلا جسم.",
                 "criteria": [
                     "304 بلا جسم ورأس ETag موجود",
                     "تعديل المورد يغيّر الـETag (اختبار)",
                     "`Cache-Control` مضبوط بعمر مقصود (مش max-age ضخم بالخطأ)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "HybridCache (.NET 9+)", "url": "https://learn.microsoft.com/dotnet/core/extensions/hybrid-cache"},
                {"label": "Output caching in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/output"},
                {"label": "Response caching", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/response"},
                {"label": "In-memory cache", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/memory"},
                {"label": "Distributed caching (Redis)", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/distributed"},
                {"label": "HTTP caching (MDN)", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching"},
            ]},
        ],
    },
]
