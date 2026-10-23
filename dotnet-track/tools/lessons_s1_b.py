"""Stage 1 — lessons 5-7 of Module 1, plus the Stage 1 capstone brief."""

TODAY = "2026-10-22"

LESSONS_S1_B = [
    # ------------------------------------------------------------------ l5
    {
        "id": "s1-m1-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
إزاي نظامك بيفشل مهم زي إزاي بيشتغل. العميل (واجهة، تطبيق موبايل، خدمة تانية) محتاج **عقد ثابت** للأخطاء:
كود HTTP صحيح، جسم موثّق، ورسالة آمنة للعرض — ومن غير تسريب تفاصيل داخلية.

في .NET الحديث، العقد ده اسمه **ProblemDetails** (RFC 9457)، والآلية الموصى بها لتحويل الاستثناءات
هي **`IExceptionHandler`** (من .NET 8) — بدل middleware مخصص مكتوب بإيدك.
"""},
            {"type": "terms", "items": [
                {"term": "ProblemDetails", "def": "جسم JSON موحّد للأخطاء: `type`, `title`, `status`, `detail`, `instance` + أي امتدادات."},
                {"term": "ValidationProblemDetails", "def": "امتداد يضيف `errors` (قائمة رسائل لكل خاصية) لأخطاء التحقق 400."},
                {"term": "IExceptionHandler", "def": "عقد .NET لتحويل استثناء إلى استجابة. تُسجّل كل المعالجات وتُجرَّب بالترتيب."},
                {"term": "traceId", "def": "معرّف الطلب — أهم حاجة تديها للمستخدم وقت الخطأ عشان تلاقي اللوج."},
                {"term": "Fail fast", "def": "ارفض الطلب بدري وبوضوح (400/404) بدل ما تكمل بحالة غلط."},
            ]},
            {"type": "heading", "level": 2, "text": "استثناءات لها معنى في الـDomain"},
            {"type": "code", "lang": "csharp", "filename": "Domain/Exceptions.cs", "title": "أنواع تعبّر عن نية، مش Exception عامة", "code": r'''
namespace Shop.Domain;

/// <summary>قاعدة عمل اتكسرت — العميل غلطان (400/409).</summary>
public abstract class DomainException(string message) : Exception(message);

public sealed class OrderAlreadyCancelledException(Guid orderId)
    : DomainException($"الطلب {orderId:N} ملغي ولا يمكن تعديله")
{
    public Guid OrderId { get; } = orderId;
}

public sealed class InsufficientStockException(Guid productId, int requested, int available)
    : DomainException($"الكمية المطلوبة ({requested}) أكبر من المتاح ({available}) للمنتج {productId:N}")
{
    public Guid ProductId { get; } = productId;
    public int Requested { get; } = requested;
    public int Available { get; } = available;
}

/// <summary>مورد غير موجود — 404.</summary>
public sealed class NotFoundException(string resource, object id)
    : Exception($"{resource} بمعرّف {id} غير موجود")
{
    public string Resource { get; } = resource;
    public object Id { get; } = id;
}
'''},
            {"type": "heading", "level": 2, "text": "المعالج: من استثناء إلى ProblemDetails"},
            {"type": "code", "lang": "csharp", "filename": "Api/ErrorHandling/GlobalExceptionHandler.cs", "title": "خريطة واحدة لكل أخطاء التطبيق", "code": r'''
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

public sealed class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> log) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        var traceId = httpContext.TraceIdentifier;

        var (status, title, detail, extensions) = exception switch
        {
            NotFoundException nf => (
                StatusCodes.Status404NotFound,
                "المورد غير موجود",
                nf.Message,
                (IReadOnlyDictionary<string, object?>?)null),

            InsufficientStockException stock => (
                StatusCodes.Status409Conflict,
                "الكمية غير متاحة",
                stock.Message,
                new Dictionary<string, object?>
                {
                    ["productId"] = stock.ProductId,
                    ["requested"] = stock.Requested,
                    ["available"] = stock.Available,
                }),

            DomainException domain => (
                StatusCodes.Status400BadRequest,
                "الطلب مرفوض بسبب قاعدة عمل",
                domain.Message,
                null),

            OperationCanceledException when cancellationToken.IsCancellationRequested => (
                StatusCodes.Status499ClientClosedRequest,   // 499: العميل قفل الاتصال
                "أُلغي الطلب",
                "أغلق العميل الاتصال قبل اكتمال العملية.",
                null),

            UnauthorizedAccessException or SecurityTokenException => (
                StatusCodes.Status403Forbidden,
                "غير مسموح",
                "ليس لديك صلاحية لهذا الإجراء.",       // ⚠ بلا تفاصيل داخلية
                null),

            _ => (
                StatusCodes.Status500InternalServerError,
                "خطأ غير متوقع في الخادم",
                "حدث خطأ أثناء معالجة طلبك. احتفظ بمعرّف التتبع وراسل الدعم.",  // ⚠ بلا stack trace
                null),
        };

        // السجل الداخلي كامل — المستخدم يشوف نسخة آمنة فقط
        if (status >= 500)
            log.LogError(exception, "unhandled error for {Method} {Path} (trace {TraceId})",
                httpContext.Request.Method, httpContext.Request.Path, traceId);
        else
            log.LogWarning("{Type} handled as {Status} for {Path} (trace {TraceId})",
                exception.GetType().Name, status, httpContext.Request.Path, traceId);

        var problem = new ProblemDetails
        {
            Status = status,
            Title = title,
            Detail = detail,
            Instance = httpContext.Request.Path,
            Type = $"https://httpstatuses.com/{status}",
        };
        problem.Extensions["traceId"] = traceId;
        if (extensions is not null)
            foreach (var (key, value) in extensions) problem.Extensions[key] = value;

        httpContext.Response.StatusCode = status;
        httpContext.Response.ContentType = "application/problem+json";
        await httpContext.Response.WriteAsJsonAsync(problem, cancellationToken);
        return true;   // اتعاملت معه — لا تُمرّره لمعالج آخر
    }
}

// نوع مساعد للتوثيق فقط
public sealed class SecurityTokenException : Exception;
'''},
            {"type": "code", "lang": "csharp", "filename": "Program.cs", "title": "التسجيل — ترتيب المعالجات مهم", "code": r'''
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails(options =>
{
    // أجسام 4xx/5xx اللي مش من استثناءات (مثل 404 من الراوتر) تبقى problem+json كمان
    options.CustomizeProblemDetails = ctx =>
    {
        ctx.ProblemDetails.Extensions["traceId"] ??= ctx.HttpContext.TraceIdentifier;
        ctx.ProblemDetails.Extensions["instance"] ??= ctx.HttpContext.Request.Path;
    };
});

builder.Services.AddExceptionHandler<GlobalExceptionHandler>();

var app = builder.Build();

app.UseExceptionHandler(_ => { });   // ✓ يفعّل IExceptionHandler pipeline
app.UseStatusCodePages();              // أجسام problem لـ404/405 بدون استثناء
app.UseHttpsRedirection();

// ... endpoints
app.Run();
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء بتظهر في الإنتاج",
             "md": """
- **`app.UseExceptionHandler()` ناقص** → المعالجات المسجّلة مش هتشتغل وهترجع صفحة 500 فاضية.
- **تسريب التفاصيل**: `detail = ex.ToString()` بيبعت stack trace للعميل (معلومة أمنية مجانية للمهاجم).
- **كل حاجة 400**: أخطاء التبعية الخارجية (Timeout من خدمة تانية) المفروض 502/504 مش 400.
- **429 من غير `Retry-After`** → العملاء هيعيدوا المحاولة فورًا ويزوّدوا الحمل.
- **مفيش traceId** → الدعم مش هيعرف يلاقي اللوج.
"""},
            {"type": "table", "head": ["الحالة", "متى", "مثال من نظام طلبات"], "rows": [
                ["400", "الطلب نفسه غلط (شكل/قاعدة عمل)", "كمية سالبة، كوبون منتهي"],
                ["401", "مش معروف مين إنت", "توكن منتهي/ناقص"],
                ["403", "معروف لكن مش مسموح", "مستخدم عادي بيحاول يلغي طلب حد تاني"],
                ["404", "المورد مش موجود", "orderId غلط"],
                ["409", "تعارض مع الحالة الحالية", "تعديل طلب ملغي، نسخة قديمة (concurrency)"],
                ["422", "الشكل سليم لكن الدلالات غلط", "تاريخ تسليم قبل تاريخ الطلب"],
                ["429", "تجاوزت الحد", "أكثر من 100 طلب/دقيقة"],
                ["500", "خطأ عندنا", "استثناء غير متوقع"],
                ["502/504", "تبعية خارجية فشلت/تأخرت", "بوابة الدفع لا تستجيب"],
            ]},
            {"type": "heading", "level": 2, "text": "اختبار مسار الخطأ"},
            {"type": "code", "lang": "csharp", "filename": "ErrorHandlingTests.cs", "title": "WebApplicationFactory: تأكد من العقد مش من الرسالة بس", "code": r'''
public sealed class ErrorHandlingTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task Cancelled_order_returns_400_problem_json_with_traceId()
    {
        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/orders/cancel", new { orderId = Fixtures.CancelledOrderId });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/problem+json");

        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Title.Should().NotBeNullOrWhiteSpace();
        problem.Extensions.Should().ContainKey("traceId");
        problem.Detail.Should().NotContain("System.");   // ما يسرّبش أنواع داخلية
    }

    [Fact]
    public async Task Unknown_order_returns_404()
    {
        var client = factory.CreateClient();
        var response = await client.GetAsync($"/api/orders/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أصمم مجموعة استثناءات Domain معبّرة وأربطها بأكواد HTTP صحيحة.",
                "أسجّل `IExceptionHandler` وأفعّله في الـpipeline وأتأكد إنه شغال.",
                "أرجع problem+json موحّد فيه traceId وامتدادات مفيدة.",
                "أمنع تسريب stack trace أو أسماء أنواع داخلية للعميل.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "خدمة الدفع الخارجية عملت Timeout. أنهي كود HTTP أنسب؟",
                 "options": ["400", "408", "504", "500"], "answer": 2,
                 "explain": "504 Gateway Timeout (أو 502 Bad Gateway لو رجعت استجابة غير صالحة) يوضّح إن المشكلة في التبعية، مش في طلب العميل ولا في كودك الداخلي."},
                {"q": "سجّلت `AddExceptionHandler<T>()` لكن الأخطاء لسه بترجع صفحة فاضية. السبب الأرجح؟",
                 "options": [
                     "المعالج لازم يرجع false",
                     "نسيت `app.UseExceptionHandler(...)` في الـpipeline",
                     "لازم تسجّل المعالج بعد `app.Run()`",
                     "ProblemDetails مش مفعّل",
                 ], "answer": 1,
                 "explain": "المعالجات تشتغل من خلال middleware الـexception handler. من غيره الاستثناء يطلع للخارج ويتصرف فيه Kestrel بشكل افتراضي."},
                {"q": "إمتى ترجع 409 بدل 400؟",
                 "options": [
                     "لما المدخل ناقص حقل مطلوب",
                     "لما الطلب سليم الشكل لكنه يتعارض مع حالة المورد الحالية",
                     "لما المستخدم غير مسجّل",
                     "لما الخادم وقع",
                 ], "answer": 1,
                 "explain": "409 Conflict = تعارض مع الحالة (تعديل ملغي، concurrency token قديم، مورد مقفول). الناقص في الشكل = 400."},
                {"q": "أنهي تفصيلة أهم حاجة تضيفها لجسم الخطأ في الإنتاج؟",
                 "options": ["stack trace", "اسم السيرفر", "traceId", "كلمة السر المشفرة"], "answer": 2,
                 "explain": "traceId بيوصل شكوى المستخدم بسجلاتك مباشرة — من غيره الدعم هيبحث في الظلام."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "عقد أخطاء كامل",
                 "md": "طبّق `IExceptionHandler` في مشروعك مع 4 أنواع استثناء على الأقل، وفعّل `AddProblemDetails`، واكتب اختبار Integration يتأكد من `application/problem+json` ومن وجود `traceId`.",
                 "criteria": [
                     "كل استثناء Domain بيتحول لكود HTTP مبرر (مش 500)",
                     "الاستجابة media type هي application/problem+json",
                     "مفيش stack trace أو أسماء أنواع داخلية في الجسم",
                     "اختبار Integration ناجح يتحقق من العقد",
                 ],
                 "hint": "ابدأ بالخريطة في `switch expression`، وبعدين اختبر كل فرع بحالة — مش بس الفرع الافتراضي."},
                {"id": "t2", "title": "جدول حالات لفريقك",
                 "md": "اكتب جدول (في README أو ADR) يربط كل حالة خطأ في نظامك بكود HTTP والعنوان والامتدادات، عشان الواجهة تعتمد عليه.",
                 "criteria": ["8 حالات على الأقل", "كل حالة فيها مثال جسم JSON", "اتفقت مع «العميل» (لوحدك برضه) على معانيها"]},
            ]},
            {"type": "resources", "items": [
                {"label": "Handle errors in ASP.NET Core web APIs", "url": "https://learn.microsoft.com/aspnet/core/web-api/handle-errors"},
                {"label": "IExceptionHandler (.NET 8+)", "url": "https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.diagnostics.iexceptionhandler"},
                {"label": "RFC 9457 — Problem Details", "url": "https://www.rfc-editor.org/rfc/rfc9457"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l6
    {
        "id": "s1-m1-l6",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
اللوجنج النصي (`$"failed for user {id}"`) بيخلي البحث مستحيل: كل سطر شكله مختلف، فالأدوات ما تقدرش تجمّع
أو تفلتر. **اللوجنج المهيكل** بيكتب الحدث كحقول (`OrderId=…`, `Elapsed=…`) وقالب ثابت — فتقدر تسأل أسئلة:
«كل الأخطاء اللي فيها OrderId=123 في آخر ساعة».

الدرس ده: Serilog من الإعداد لحد CorrelationId، وقواعد تمنع إن اللوج يبقى مصدر تسريب بيانات.
"""},
            {"type": "terms", "items": [
                {"term": "Message template", "def": "قالب فيه أسماء بدل دمج نصوص: `\"order {OrderId} placed\"` — الاسم بيتخزن كحقل."},
                {"term": "Destructuring ({@obj})", "def": "تخزين الكائن كبنية (JSON) بدل `ToString()`."},
                {"term": "Sink", "def": "وجهة الكتابة: Console، File، Seq، OpenTelemetry، Application Insights…"},
                {"term": "Enricher", "def": "يضيف حقول تلقائيًا لكل حدث (MachineName، Environment، CorrelationId، AssemblyVersion)."},
                {"term": "CorrelationId / TraceId", "def": "معرّف يربط كل سجلات الطلب الواحد (وعبر الخدمات في التتبع الموزع)."},
                {"term": "Minimum level / Overrides", "def": "الحد الأدنى للتسجيل، ومستويات مخصصة لكل namespace (مثلًا تخفيض ضوضاء EF)."},
            ]},
            {"type": "code", "lang": "csharp", "filename": "Program.cs", "title": "إعداد Serilog من appsettings + Console/File", "code": r'''
using Serilog;
using Serilog.Events;

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSerilog((context, services, configuration) => configuration
    .ReadFrom.Configuration(context.Configuration)          // المستويات والـsinks من appsettings
    .ReadFrom.Services(services)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithEnvironmentName()
    .Enrich.WithProperty("Application", "Shop.Api")
    .Enrich.WithProperty("Version", typeof(Program).Assembly.GetName().Version?.ToString() ?? "0.0.0")
    .WriteTo.Console(outputTemplate:
        "[{Timestamp:HH:mm:ss} {Level:u3}] {CorrelationId} {Message:lj}{NewLine}{Exception}")
    .WriteTo.File(
        path: "logs/shop-.log",
        rollingInterval: RollingInterval.Day,
        retainedFileCountLimit: 14,
        shared: true,
        outputTemplate:
        "{Timestamp:o} [{Level:u3}] {CorrelationId} {SourceContext}{NewLine}{Message:lj}{NewLine}{Exception}")
    .MinimumLevel.Override("Microsoft.EntityFrameworkCore", LogEventLevel.Warning)
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning));

var app = builder.Build();
'''},
            {"type": "code", "lang": "json", "filename": "appsettings.json (excerpt)", "title": "مستويات لكل بيئة", "code": r'''
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft": "Warning",
        "Microsoft.Hosting.Lifetime": "Information",
        "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
        "Shop": "Debug"
      }
    }
  }
}
'''},
            {"type": "heading", "level": 2, "text": "CorrelationId: اربط سجلات الطلب الواحد"},
            {"type": "code", "lang": "csharp", "filename": "Middleware/CorrelationMiddleware.cs", "title": "استقبل X-Correlation-Id أو ولّده، ومرّره للرد", "code": r'''
using Serilog.Context;

public sealed class CorrelationMiddleware(RequestDelegate next)
{
    private const string Header = "X-Correlation-Id";

    public async Task Invoke(HttpContext context)
    {
        var incoming = context.Request.Headers[Header].FirstOrDefault();
        var correlationId = Guid.TryParse(incoming, out var parsed)
            ? parsed.ToString("N")
            : context.TraceIdentifier;                    // ASP.NET Core بيولّد واحد لكل طلب

        context.Items["CorrelationId"] = correlationId;
        context.Response.Headers[Header] = correlationId;

        using (LogContext.PushProperty("CorrelationId", correlationId))
        {
            await next(context);
        }
    }
}

// التسجيل: قبل أي middleware بيكتب لوج
app.UseMiddleware<CorrelationMiddleware>();
'''},
            {"type": "heading", "level": 2, "text": "الكتابة الصحيحة: حقول مش نصوص"},
            {"type": "code", "lang": "csharp", "filename": "Orders/OrderPlacementService.cs", "title": "قارن السطرين — نفس المعلومة، قيمة مختلفة تمامًا للبحث", "code": r'''
public sealed class OrderPlacementService(
    IOrderStore store, IOrderNotifier notifier, ITaxPolicy tax, ILogger<OrderPlacementService> log)
{
    public async Task<Guid> PlaceAsync(CreateOrderRequest request, CancellationToken ct)
    {
        var started = TimeProvider.System.GetUtcNow();

        // ✗ خطأ: دمج نصي — مفيش حقول، ومفيش فلتره
        // log.LogInformation("Placing order for customer " + request.CustomerId);

        // ✓ صح: قالب + حقول
        log.LogInformation("placing order for {CustomerId} with {LineCount} lines",
            request.CustomerId, request.Lines.Count);

        var order = OrderFactory.From(request);
        order.ApplyTax(tax);

        try
        {
            await store.SaveAsync(order, ct);
            await notifier.NotifyAsync(order, ct);
        }
        catch (Exception ex)
        {
            // ✓ الاستثناء هو المعامل الأول (مش جوه القالب) — بيتسجل كاملاً مع stack
            log.LogError(ex, "order placement failed for {OrderId} ({CustomerId})", order.Id, order.Customer.Id);
            throw;
        }

        var elapsed = TimeProvider.System.GetUtcNow() - started;
        log.LogInformation("order {OrderId} placed: total {Total:C} in {ElapsedMs}ms",
            order.Id, order.Total, elapsed.TotalMilliseconds);

        // ✓ destructuring لكائن صغير ومفيد — بحذر، مش للكائنات الضخمة
        log.LogDebug("order summary {@OrderSummary}",
            new { order.Id, order.Total, Lines = order.Lines.Count });

        return order.Id;
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "ما تسجّلهوش أبدًا",
             "md": """
- **أسرار**: كلمات سر، توكنات، مفاتيح API، connection strings، ترويسات Authorization/Cookie.
- **بيانات شخصية حساسة**: رقم بطاقة، رقم قومي، بيانات صحية — سجل معرّف مش قيمة.
- **أجسام ضخمة**: `@wholeEntity` لقوائم كبيرة هيبطّئ ويملأ التخزين.
- **Stack traces للمستوى Information**: دي للمعلوماتية مش للتشخيص.

استخدم **redaction**: حوّل القيمة لمعرّف أو بصمة. مثال آمن:
`log.LogInformation("auth failed for {EmailHash}", SHA256.HashData(Encoding.UTF8.GetBytes(email)) is { } h ? Convert.ToHexString(h)[..8] : "?")`
"""},
            {"type": "table", "head": ["المستوى", "الاستخدام", "مثال"], "rows": [
                ["Verbose/Debug", "تفاصيل تطوير — مقفول في الإنتاج افتراضيًا", "قيم وسيطة، استعلامات EF"],
                ["Information", "أحداث عمل طبيعية", "طلب اتنفذ، مهمة خلفية خلصت"],
                ["Warning", "حالة غير مثالية لكن النظام كمل", "إعادة محاولة نجحت، إعداد ناقص بقيمة افتراضية"],
                ["Error", "عملية فشلت", "فشل حفظ طلب، فشل اتصال بتبعية"],
                ["Fatal/Critical", "النظام كله في خطر", "فشل الإقلاع، استنفاد اتصالات قاعدة البيانات"],
            ]},
            {"type": "callout", "kind": "tip", "title": "اختبر إن اللوج بيتكتب فعلًا",
             "md": """
`Serilog.Sinks.InMemory` أو `TestSink` بيسمحوا لك تؤكد في الاختبارات إن حدثًا مهمًا اتسجّل بالحقول الصح:
```csharp
Log.Logger = new LoggerConfiguration().WriteTo.InMemory().CreateLogger();
// ... نفّذ العملية
InMemorySink.Instance.LogEvents.Should().Contain(e =>
    e.MessageTemplate.Text.Contains("{OrderId}") && e.Level == LogEventLevel.Error);
```
"""},
            {"type": "checkpoints", "items": [
                "أضبط Serilog من appsettings مع مستويات مختلفة لكل namespace وبيئة.",
                "أكتب قوالب بحقول بدل دمج النصوص، وأضع الاستثناء كمعامل أول.",
                "أربط كل سجلات الطلب بـCorrelationId وأعيده في ترويسة الرد.",
                "أطبق قواعد منع تسجيل الأسرار والبيانات الشخصية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "أنهي سطر مكتوب بشكل صحيح هيكليًا؟",
                 "options": [
                     "`log.LogInformation($\"order {order.Id} total {order.Total}\")`",
                     "`log.LogInformation(\"order {OrderId} total {Total}\", order.Id, order.Total)`",
                     "`log.LogInformation(\"order \" + order.Id)`",
                     "`log.LogInformation(\"order {0} total {1}\", order.Id, order.Total)`",
                 ], "answer": 1,
                 "explain": "القوالب المهيكلة تستخدم **أسماء** (مش فهارس)، والقيم تُمرر كمعاملات منفصلة عشان تتخزن كحقول."},
                {"q": "إيه فايدة `LogContext.PushProperty(\"CorrelationId\", id)`؟",
                 "options": [
                     "يضيف الحقل لكل حدث داخل النطاق بدون تمريره يدويًا",
                     "يمنع كتابة اللوج",
                     "يستبدل مستوى اللوجنج",
                     "يبعت اللوج لسيرفر بعيد",
                 ], "answer": 0,
                 "explain": "الإثراء السياقي (contextual enrichment) بيضيف الحقل تلقائيًا لكل الأحداث داخل الـusing scope."},
                {"q": "ليه تعمل `MinimumLevel.Override(\"Microsoft.EntityFrameworkCore\", Warning)` في الإنتاج؟",
                 "options": [
                     "عشان EF بيكتب أخطاء وهمية",
                     "عشان لوجنج الأوامر SQL ضخم وممكن يسرّب بيانات ويبطّئ التخزين",
                     "عشان EF مش بيدعم اللوجنج",
                     "عشان نقلل استهلاك الشبكة",
                 ], "answer": 1,
                 "explain": "لوجنج `Database.Command` بيكتب SQL والبارامترات: ضجيج + حجم + احتمال تسريب بيانات شخصية. فعّله مؤقتًا للتشخيص بس."},
                {"q": "أنهي حاجة مقبول تسجيلها في Information؟",
                 "options": [
                     "كلمة سر المستخدم بعد التحقق منها",
                     "ترويسة Authorization كاملة",
                     "معرّف الطلب وزمن التنفيذ",
                     "رقم بطاقة العميل",
                 ], "answer": 2,
                 "explain": "القيم التشغيلية (ids، توقيتات، أكواد نتائج) مفيدة وآمنة. الأسرار والبيانات الشخصية ممنوعة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "لوجنج مهيكل لمشروعك",
                 "md": "ثبّت Serilog مع Console + File sinks، واضبط المستويات من appsettings، وأضف CorrelationMiddleware، وحوّل كل `LogInformation` بدمج نصوص إلى قوالب بحقول.",
                 "criteria": [
                     "كل حدث في اللوج فيه CorrelationId",
                     "مفيش `$\"...\"` جوه أي نداء لوجنج (تحقق بـ`grep -rn 'Log.*\\$\"'`)",
                     "ملفات اللوج بتتدور يوميًا وتُحذف بعد 14 يوم",
                     "الاستثناءات بتُسجل كمعامل أول",
                 ],
                 "hint": "`dotnet add package Serilog.AspNetCore Serilog.Enrichers.Environment Serilog.Sinks.File` ثم `builder.Host.UseSerilog(...)`."},
                {"id": "t2", "title": "قائمة منع التسريب",
                 "md": "اكتب سياسة لوجنج لفريقك (أو لنفسك): ممنوعات، قواعد التعتيم (redaction)، ومتى ترفع المستوى لتشخيص مشكلة.",
                 "criteria": ["5 ممنوعات على الأقل", "مثال على redaction بكود", "خطوات «التشخيص المؤقت» مع تحذير من نسيانه"]},
            ]},
            {"type": "resources", "items": [
                {"label": "Serilog", "url": "https://serilog.net/"},
                {"label": "Logging in .NET", "url": "https://learn.microsoft.com/dotnet/core/extensions/logging"},
                {"label": "Structured logging best practices", "url": "https://github.com/serilog/serilog/wiki/Writing-Log-Events"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l7
    {
        "id": "s1-m1-l7",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
فيه ميزات في C# الحديث بقت **افتراضية** في أي Code Review محترم: `record` للـDTOs،
`nullable reference types` لإلغاء فئة كاملة من الباجات، `pattern matching` بدل سلاسل `if`،
و`collection expressions` للقوائم. وفي C# 14 (.NET 10) إضافات بتقلل كود boilerplate فعلًا:
`field` keyword، extension members، و`?.=`.

الدرس ده عملي: لكل ميزة — **قبل/بعد** ومتى **ما** تستخدمهاش.
"""},
            {"type": "heading", "level": 2, "text": "1) records للقيم والـDTOs"},
            {"type": "code", "lang": "csharp", "title": "قبل / بعد", "code": r'''
// قبل: كلاس فيه مساواة يدوية وEquals/GetHashCode
public class MoneyDto
{
    public decimal Amount { get; set; }
    public string Currency { get; set; } = "EGP";
    public override bool Equals(object? o) => o is MoneyDto m && m.Amount == Amount && m.Currency == Currency;
    public override int GetHashCode() => HashCode.Combine(Amount, Currency);
}

// بعد: positional record — مساواة قيمية وDeconstruct وwith expression
public sealed record Money(decimal Amount, string Currency = "EGP")
{
    public Money
    {
        if (Amount < 0) throw new ArgumentOutOfRangeException(nameof(Amount));
        Currency = Currency.ToUpperInvariant();
    }
}

var egp = new Money(250m);
var usd = egp with { Currency = "USD" };      // نسخة معدّلة — الأصل ما اتغيرش
var (amount, currency) = usd;                  // Deconstruct
Console.WriteLine(usd == new Money(250m, "usd"));   // True (مساواة قيمية)
'''},
            {"type": "callout", "kind": "note", "title": "record class مقابل record struct",
             "md": """
`record` = نوع مرجعي بمساواة قيمية (الأنسب للـDTOs). `readonly record struct` = قيمة على الـstack،
ممتازة للأنواع الصغيرة الساخنة (إحداثيات، معرّفات مركّبة) — لكن انتبه لنسخ الكائنات الكبيرة.
**كيانات الـDomain** اللي لها هوية (Order, Customer) خليك مع `class` + معرّف: المساواة بالهوية مش بالقيم.
"""},
            {"type": "heading", "level": 2, "text": "2) Nullable reference types"},
            {"type": "code", "lang": "xml", "filename": "Shop.csproj", "title": "فعّلها على المشروع كله", "code": r'''
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <Nullable>enable</Nullable>
  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  <ImplicitUsings>enable</ImplicitUsings>
  <InvariantGlobalization>false</InvariantGlobalization>
</PropertyGroup>
'''},
            {"type": "code", "lang": "csharp", "title": "الأنماط اللي بتظهر كل يوم", "code": r'''
public sealed class Customer
{
    public required Guid Id { get; init; }              // required: لا يمكن إنشاء الكائن بدونها
    public required string Email { get; init; }
    public string? PhoneNumber { get; init; }           // اختياري صراحةً
    public Address? Address { get; init; }
}

// التعامل مع الاختياري بدون ! (اللي بيخفي الباج)
string dial = customer.PhoneNumber ?? "no-phone";
int? zip = customer.Address?.PostalCode;

// C# 14: null-conditional assignment
customer.Address?.City = "Cairo";          // بدل if (customer.Address is not null) { ... }

// التحذير CS8602/CS8604 مش «ضوضاء» — ده باج محتمل. عالج السبب مش التحذير.
'''},
            {"type": "heading", "level": 2, "text": "3) Pattern matching بدل if المتسلسلة"},
            {"type": "code", "lang": "csharp", "title": "switch expression + أنماط مركّبة", "code": r'''
public static string Describe(PaymentResult result) => result switch
{
    { Status: PaymentStatus.Succeeded, Amount: > 0 } success => $"paid {success.Amount:C}",
    { Status: PaymentStatus.Pending }                 => "waiting for confirmation",
    { Status: PaymentStatus.Failed, Error.Code: "card_declined" } => "card declined",
    { Status: PaymentStatus.Failed, Error: { } err }  => $"failed: {err.Message}",
    null                                              => "no result",
    _                                                 => throw new ArgumentOutOfRangeException(nameof(result)),
};

// list patterns (C# 11)
static string Classify(int[] scores) => scores switch
{
    []                    => "empty",
    [var only]            => $"single: {only}",
    [>= 90, .., >= 90]    => "strong start and end",
    [.., < 50]            => "weak finish",
    _                     => "mixed",
};

// type patterns + relational patterns
static decimal Discount(Customer c, DateTime now) => c switch
{
    { Tier: Tier.Gold, Joined: var d } when (now - d).TotalDays > 365 => 0.15m,
    { Tier: Tier.Silver } => 0.07m,
    { Tier: Tier.Bronze } => 0.03m,
    _ => 0m,
};
'''},
            {"type": "heading", "level": 2, "text": "4) Collection expressions وprimary constructors"},
            {"type": "code", "lang": "csharp", "title": "أقل ضوضاء في التعريف والحقن", "code": r'''
// collection expressions
string[] allowed = ["EG", "SA", "AE"];
List<OrderLine> lines = [new(ProductId, 1, 10m), new(ProductId2, 2, 5m)];
int[] all = [..first, ..second, 99];                   // spread

// primary constructors (C# 12) — الحقن في سطر واحد
public sealed class EfOrderStore(AppDbContext db, ILogger<EfOrderStore> log) : IOrderStore
{
    public async Task SaveAsync(Order order, CancellationToken ct = default)
    {
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        log.LogInformation("saved {OrderId}", order.Id);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "5) C# 14 في .NET 10: field, extensions, partial constructors"},
            {"type": "code", "lang": "csharp", "title": "الميزات الجديدة اللي تقلل الـboilerplate", "code": r'''
// field keyword: خاصية بـgetter/setter مخصص بدون backing field يدوي
public sealed class Registration
{
    public string Email
    {
        get => field;                                   // field = الحقل المُولَّد تلقائيًا
        set => field = Normalize(value);
    }

    private static string Normalize(string v) => v.Trim().ToLowerInvariant();
}

// extension members: إضافة خصائص/دوال لأنواع لا تملكها
public static class EnumerableExtensions
{
    extension<T>(IEnumerable<T> source)
    {
        public bool IsEmpty => !source.Any();
        public IEnumerable<T> WhereNotNull() => source.Where(x => x is not null)!;
    }
}

// null-conditional assignment
order.Shipping?.Phone = phone;

// nameof مع أنواع generic غير مقيّدة
log.LogWarning("unsupported {Type}", nameof(List<>));

// partial constructors/events: توقيع هنا، وتوليد كود في مكان آخر (source generators)
public partial class GeneratedDto
{
    public partial GeneratedDto(string raw);
}
'''},
            {"type": "callout", "kind": "warn", "title": "إمتى ما تستخدمهاش",
             "md": """
- **`record` لكيان Domain له هوية** → المساواة القيمية هتعمل باجات مقارنة (اتنين Order بنفس القيم مش نفس الطلب).
- **`with` على كائن ضخم/فيه مراجع** → نسخ سطحي؛ المراجع الداخلية مشتركة.
- **`!` (null-forgiving)** كحل دائم → إنت بتخفي التحذير مش بتصلح السبب.
- **primary constructor مع منطق معقد في الـctor** → لو محتاج تحقق/تهيئة متعددة الأسطر، اكتب constructor عادي.
- **switch expression بدون `_`** على نوع مفتوح → خطر `MatchLookupException` وقت التشغيل.
"""},
            {"type": "table", "head": ["الميزة", "المكسب", "احذر"], "rows": [
                ["records", "مساواة قيمية + with + deconstruct في سطر", "مش لكيانات لها هوية"],
                ["nullable + required", "إلغاء NullReferenceException عمليًا", "التحذير باج — ما تكتموش"],
                ["pattern matching", "شروط معقدة بتتقرأ بسهولة", "لازم تغطي كل الحالات (`_`)"],
                ["collection expressions", "تعريف مختصر ومنتظم", "الأنواع الكبيرة: انتبه للنسخ"],
                ["primary constructors", "حقن بدون 5 أسطر", "مش بديل للـctors المعقدة"],
                ["C# 14 field/extensions", "خصائص ذكية وامتدادات أقوى", "اقرأ سلوك الـgetter/setter قبل ما تعتمد عليه"],
            ]},
            {"type": "checkpoints", "items": [
                "أستخدم records للـDTOs وأعرف متى أرفضها لكيانات الـDomain.",
                "أفعّل nullable وأصلح التحذيرات بدون `!`.",
                "أستبدل سلاسل if بـswitch expression شاملة لكل الحالات.",
                "أكتب كود C# 14 (field, extension members, ?.=) وأفهم أثره.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "عندك كيان `Order` له `Id` وحالة متغيرة. تستخدم `record`؟",
                 "options": ["نعم — records أحدث", "لا — class بمساواة بالهوية", "نعم مع record struct", "لا — استخدم tuple"], "answer": 1,
                 "explain": "كيانات الـDomain لها هوية: طلبان بنفس القيم ليسا نفس الطلب. المساواة القيمية لـrecords هتعمل مقارنات مضللة."},
                {"q": "`customer.Address.City = x` مع `Address` نوع nullable — التحذير `CS8602`. أفضل إصلاح؟",
                 "options": [
                     "`customer.Address!.City = x`",
                     "`customer.Address?.City = x` (null-conditional assignment في C# 14)",
                     "تعطيل nullable في الملف",
                     "جعل Address غير nullable دائمًا",
                 ], "answer": 1,
                 "explain": "`?.=` بيعبّر عن النية: حدّث لو موجود. `!` بيخفي الباج، وتعطيل nullable بيخسرك حماية المشروع كله."},
                {"q": "`switch expression` على نوع `object` من غير `_ => …`. إيه الخطر؟",
                 "options": [
                     "خطأ ترجمة",
                     "استثناء وقت التشغيل لو الحالة مش مغطاة",
                     "إرجاع null دائمًا",
                     "أداء أبطأ",
                 ], "answer": 1,
                 "explain": "لو مفيش نمط مطابق ولا arm افتراضي، بيرمي استثناء. دايمًا غطي الحالة العامة بـ`_`."},
                {"q": "أنهي استخدام صحيح لـ`with`؟",
                 "options": [
                     "تعديل كائن record بإنشاء نسخة محدّثة",
                     "تعديل كائن class عادي في المكان",
                     "نسخ عميق لأي كائن",
                     "مقارنة كائنين",
                 ], "answer": 0,
                 "explain": "`with` بيعمل نسخة غير قابلة للتغيير مع التعديلات المحددة — وهو نمط records (وstructs). النسخ سطحي: المراجع تُشارك."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تحديث مشروعك لـC# الحديث",
                 "md": "فعّل `<Nullable>enable</Nullable>` و`TreatWarningsAsErrors`، حوّل كل DTOs إلى records، واستبدل 3 سلاسل if بـswitch expressions — وأصلح كل التحذيرات من غير `!`.",
                 "criteria": [
                     "البناء ينجح بصفر تحذيرات (وصفر `!`)",
                     "كل الـDTOs records مع validation في الـcompact constructor",
                     "3 switch expressions على الأقل تغطي كل الحالات مع `_`",
                     "الاختبارات كلها ناجحة",
                 ],
                 "hint": "ابدأ بمشروع واحد (مش الحل كله) وقيس عدد التحذيرات قبل/بعد. لو العدد ضخم، استخدم `<Nullable>annotations</Nullable>` مؤقتًا ثم ارفعها لـenable."},
                {"id": "t2", "title": "بطاقة مرجعية لنفسك",
                 "md": "اكتب صفحة واحدة (في ملاحظات الدرس) فيها 6 أنماط هتستخدمها يوميًا مع مثال سطر واحد لكل نمط.",
                 "criteria": ["6 أنماط", "مثال كود لكل نمط", "سطر «متى لا تستخدمه» لكل نمط"]},
            ]},
            {"type": "resources", "items": [
                {"label": "What's new in C# 14", "url": "https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-14"},
                {"label": "Records (C# reference)", "url": "https://learn.microsoft.com/dotnet/csharp/fundamentals/types/records"},
                {"label": "Nullable reference types", "url": "https://learn.microsoft.com/dotnet/csharp/nullable-references"},
                {"label": "Pattern matching overview", "url": "https://learn.microsoft.com/dotnet/csharp/fundamentals/functional/pattern-matching"},
            ]},
        ],
    },
    # -------------------------------------------------------------- capstone
    {
        "id": "s1-m3-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "callout", "kind": "goal", "title": "المشروع ده هو معيار اجتياز المرحلة الأولى",
             "md": """
مش هتتعلم حاجة جديدة هنا — هتطبّق كل اللي فات على **مشروع واحد حقيقي**.
المعيار مش «الكود يشتغل»؛ المعيار إن أي مطور تاني يقدر يفهمه، يختبره، ويعدّله من غير ما يسألك.
"""},
            {"type": "text", "md": """
## المطلوب

خد Web API موجود — إما مشروعك السابق (CRUD بـEF Core)، أو نسخة من مستودع «فوضوي» — وحوّله لمشروع
إنتاجي. لو مفيش مشروع جاهز، ابدأ من `dotnet new webapi -n Shop.Api` وأضف 3 موارد (Products, Customers, Orders)
بعلاقات حقيقية، وبعدين طبّق القائمة.

المدة المتوقعة: **12-16 ساعة عمل** موزعة على أيام (مش جلسة واحدة).
"""},
            {"type": "steps", "title": "خطوات التنفيذ", "items": [
                {"title": "افصل الطبقات",
                 "md": "أنشئ `Shop.Domain` (كيانات + استثناءات + عقود/interfaces) و`Shop.Infrastructure` (EF Core, Email, HTTP) و`Shop.Api` (endpoints, DTOs, validators) — واتجاه الاعتماد للداخل. الـDomain **ما يعرفش** EF Core ولا ASP.NET.",
                 "code": {"lang": "bash", "title": "الهيكل", "code": "dotnet new sln -n Shop\ndotnet new classlib -n Shop.Domain\ndotnet new classlib -n Shop.Infrastructure\ndotnet new webapi   -n Shop.Api\ndotnet new xunit   -n Shop.Tests\ndotnet sln add ./**/**.csproj\ndotnet add Shop.Infrastructure reference Shop.Domain\ndotnet add Shop.Api reference Shop.Domain Shop.Infrastructure\ndotnet add Shop.Tests reference Shop.Domain Shop.Api"}},
                {"title": "أعد توزيع المسؤوليات (SRP/DIP)",
                 "md": "كل خدمة تعمل حاجة واحدة. الحقن عبر interfaces مسجّلة في `Program.cs`. مفيش `new` لتبعيات خارجية جوه كلاس العمل، ومفيش connection string مكتوب في الكود.",
                 "code": {"lang": "csharp", "title": "فحص الاعتماديات (اختبار معماري بسيط)", "code": "[Fact]\npublic void Domain_does_not_reference_Infrastructure()\n{\n    var domain = typeof(Order).Assembly;\n    var forbidden = domain.GetReferencedAssemblies()\n        .Select(a => a.Name!)\n        .Where(n => n.Contains(\"Infrastructure\") || n.Contains(\"EntityFrameworkCore\"));\n    forbidden.Should().BeEmpty(\"الـDomain ما يعرفش تفاصيل البنية التحتية\");\n}"}},
                {"title": "إعدادات وخيارات",
                 "md": "كل قسم إعدادات في كلاس Options مع `ValidateDataAnnotations().ValidateOnStart()`، والأسرار في User Secrets محليًا ومتغيرات بيئة في Docker.",
                 },
                {"title": "تحقق وأخطاء موحّدة",
                 "md": "Validators لكل DTO، تشغيلها قبل منطق العمل، وردود `ValidationProblem` للأخطاء 400. و`IExceptionHandler` واحد يحوّل استثناءات الـDomain لأكواد HTTP مبررة مع `traceId`.",
                 },
                {"title": "لوجنج مهيكل",
                 "md": "Serilog (Console + File rolling) مع CorrelationId في كل حدث وفي ترويسة الرد. قوالب بحقول، والاستثناء كمعامل أول. صفر أسرار في اللوج.",
                 },
                {"title": "اختبارات",
                 "md": "على الأقل: 8 اختبارات Unit على منطق الـDomain (بـfakes مش mocks قدر الإمكان)، و5 اختبارات Integration بـ`WebApplicationFactory` تغطي مسار نجاح + مسار فشل + عقد الأخطاء. ولو Docker متاح: Testcontainers مع Postgres بدل InMemory.",
                 "code": {"lang": "bash", "title": "تشغيل كل شيء", "code": "dotnet build -warnaserror\ndotnet test --collect:\"XPlat Code Coverage\"\ndotnet run --project Shop.Api"}},
                {"title": "وثّق قراراتك",
                 "md": "ثلاثة ADRs قصيرة في `docs/adr/`: (1) ليه Layered/Clean، (2) ليه FluentValidation مش DataAnnotations، (3) ليه lifetimes دي للخدمات. كل ADR: السياق، القرار، البدائل، العواقب.",
                 },
            ]},
            {"type": "heading", "level": 2, "text": "معايير القبول (قيّم نفسك بصدق)"},
            {"type": "table", "head": ["#", "المعيار", "إزاي تتحقق"], "rows": [
                ["1", "`dotnet build -warnaserror` ينجح", "شغّلها — أي تحذير nullable أو analyzer يكسر البناء"],
                ["2", "صفر `IConfiguration[\"key\"]` خارج Program.cs", "`grep -rn \"IConfiguration\\[\" Shop.Api Shop.Domain Shop.Infrastructure`"],
                ["3", "الـDomain لا يرجّع EF ولا ASP.NET", "اختبار المعمارية في الخطوة 2 ناجح"],
                ["4", "كل endpoint يرجع problem+json عند الخطأ", "اختبار Integration يتحقق من الـmedia type وtraceId"],
                ["5", "تغطية ≥ 70% على منطق الـDomain", "تقرير التغطية (coverlet) — مش على المشروع كله"],
                ["6", "كل حدث لوج فيه CorrelationId", "اعمل طلب وشوف السطر في logs/shop-*.log"],
                ["7", "مفيش سر في المستودع", "`git grep -iE \"password|apikey|secret\" -- ':!*Tests*'` ما يرجعش قيم حقيقية"],
                ["8", "3 ADRs مكتوبة", "ملفات في docs/adr/"],
                ["9", "README يشرح التشغيل في 3 أوامر", "جرّبه على مستنسخ نظيف (clone في مجلد جديد)"],
                ["10", "التطبيق يفشل عند الإقلاع لو إعداد ناقص", "احذف `ConnectionStrings:Shop` وشوف الرسالة"],
            ]},
            {"type": "callout", "kind": "warn", "title": "أخطاء شائعة في المشروع ده",
             "md": """
- **إعادة كتابة كل حاجة من الصفر** بدل التعديل التدريجي — الهدف مهارة التطوير الآمن لكود موجود.
- **مبالعة في التجريد**: interface لكل كلاس، Repository فوق EF Core، طبقات فاضية. لو الطبقة ما بتضيفش قرار، احذفها.
- **اختبارات هشة**: assertion على نص رسالة اللوج أو على ترتيب نداءات mocks بدل السلوك.
- **نسيان مسار الفشل**: كل الاختبارات نجاح — دي مش اختبارات، دي عرض.
"""},
            {"type": "tasks", "title": "التسليم", "items": [
                {"id": "t1", "title": "سلّم المشروع لنفسك بمعايير الفريق",
                 "md": "بعد ما تخلص، اعمل Pull Request (حتى لو على فرع في مستودعك) واكتب وصف يشرح: المشكلة، الحل، القرارات، والمخاطر. وبعدين راجع الـdiff بنفسك كأنك reviewer.",
                 "criteria": [
                     "كل معايير القبول العشرة متحققة وموثقة بلقطة أو أمر",
                     "وصف PR يشرح القرارات لا التعديلات فقط",
                     "مراجعة ذاتية سجلت فيها 3 تحسينات إضافية (حتى لو مؤجلة)",
                 ],
                 "hint": "أفضل طريقة للحكم: اطلب من زميل (أو من نفسك بعد أسبوع) يشغّل المشروع من README بس. لو سأل سؤال، README ناقص."},
                {"id": "t2", "title": "اربطه بالمرحلة التالية",
                 "md": "اكتب قائمة من 5 نقاط «اللي هيتغير في المرحلة 2»: OpenAPI/Scalar، JWT، Rate limiting، Health checks، Background worker — وحدد أنهي ملفات هتتحرك.",
                 "criteria": ["5 بنود محددة بأسماء ملفات/مجلدات", "ترتيب تنفيذ منطقي", "مخاطر لكل بند"]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET architecture guides", "url": "https://learn.microsoft.com/dotnet/architecture/"},
                {"label": "Integration tests in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/test/integration-tests"},
                {"label": "Architecture decision records", "url": "https://adr.github.io/"},
                {"label": "eShop (مرجع لنظام .NET حديث)", "url": "https://github.com/dotnet-architecture/eShop"},
            ]},
        ],
    },
]
