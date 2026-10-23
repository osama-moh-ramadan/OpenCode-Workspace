# -*- coding: utf-8 -*-
"""Stage 7 module 1 (part B): s7-m1-l3 (لوجنج مركزي قابل للبحث), s7-m1-l4 (Prometheus وGrafana)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s7-m1-l3 — لوجنج مركزي قابل للبحث
# ══════════════════════════════════════════════════════════════════════════
_L3 = {
    "id": "s7-m1-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "درس 1.2.2 كان «اكتب لوجنج مهيكَل». الدرس ده: **تجميعه والبحث فيه وحمايته**. هتبني لوجنج مركزي (Serilog → Seq أو Loki أو OTLP) تبحث فيه بثانية عن «كل طلبات `o-123`» أو «كل فشل الدفع آخر ساعة»، مع **CorrelationId** بيمشي عبر الخدمات، و**حجب البيانات الشخصية** ككود مش كنية حسنة، و**مستويات تُغيَّر وقت التشغيل** من غير نشر، وخطة تكلفة (لأن السجلات عادةً أغلى بند مراقبة — 6.2.5)."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "لوجنج مهيكَل", "def": "الرسالة **قالب** + حقول منفصلة: `log.LogInformation(\"Order {OrderId} failed: {Reason}\", id, reason)`. النتيجة: بحث وتجميع وتنبيه على الحقول، مش على نص."},
            {"term": "Message template", "def": "النص اللي فيه أقواس `{FieldName}`. الأسماء دي بتبقى حقول في الخلفية — خليها ثابتة ولا تستخدم أسماء متغيرة (cardinality في اللوج كمان)."},
            {"term": "Sink", "def": "وجهة الكتابة: Console · File (rolling) · Seq · OpenTelemetry · Elasticsearch · Loki · Azure Monitor. ممكن أكتر من sink بنفس الوقت."},
            {"term": "Enricher", "def": "بيضيف حقول ثابتة/سياقية لكل حدث: `FromLogContext` · `WithMachineName` · `WithEnvironmentName` · و**TraceId/SpanId** (من 7.1.2)."},
            {"term": "`LoggingLevelSwitch`", "def": "مفتاح مستوى يُغيَّر **وقت التشغيل** (من إعداد قابل لإعادة التحميل أو endpoint إداري) — بلا إعادة نشر."},
            {"term": "Sub-logger", "def": "فرع في Serilog بفلاتر خاصة: مثلًا كتابة `/health` لملف مختلف أو تجاهلها بالكامل (أكبر مصدر ضجيج)."},
            {"term": "CorrelationId", "def": "معرّف رحلة منطقية (طلب مستخدم أو عملية أعمال) بين الخدمات — **مكمل لـTraceId** (اللي بيربط spans). غالبًا بيكون نفسه أو مشتق منه."},
            {"term": "حجب/تنقية (Redaction)", "def": "منع وصول بيانات حساسة للسجل: حقول كاملة · أنماط (بطاقات/هواتف/بريد) · نصوص SQL · ترويسات مصادقة. **أفضل حماية: ما تسجلهاش أصلًا**."},
            {"term": "Destructuring", "def": "تحويل كائن لحقول: `log.Info(\"{Order}\", order, destructObjects: true)` أو `@Order` للـJSON. خطر: كائن كبير/فيه بيانات حساسة → حدد العمق والخصائص."},
            {"term": "Log-based metric", "def": "تحويل نمط في السجلات لمقياس (عدد مرات ظهور خطأ). مفيد للأحداث النادرة — لكن المقياس الأصلي في التطبيق أفضل وأرخص (7.1.1)."},
            {"term": "الاحتفاظ الطبقي", "def": "ساخن (قابل للبحث فورًا، أيام–أسابيع) ← بارد/أرشيف (أرخص، استرجاع أبطأ). سياسة تلقائية حسب العمر."},
        ]},

        # ── 1) الإعداد
        {"type": "heading", "level": 2, "text": "① الإعداد الكامل: Serilog بفلاتر ومستويات وإثراء"},
        {"type": "table", "caption": "لوجنج مهيكَل مقابل نصي — الفرق يظهر وقت الحادث",
         "head": ["", "نصي (`$\"Order {id} failed\"`)", "مهيكَل (قالب + حقول)"],
         "rows": [
             ["البحث عن طلب محدد", "grep نصي (بطيء وغير دقيق)", "`OrderId = 'o-123'` في ثانية"],
             ["التجميع", "مستحيل تقريبًا", "`count() group by Reason` — أشهر أسباب الفشل"],
             ["التنبيه على نمط", "تنبيه نصي هش", "تنبيه على حقل وقيمة"],
             ["الربط بالتتبع", "يدوي", "حقل `TraceId` → قفزة مباشرة للرحلة"],
             ["حجم التخزين", "مكرر (النص كله)", "الحقول تُضغط/تُفهرس بكفاءة أعلى"],
             ["التكلفة الخفية", "وقت المهندسين في البحث", "cardinality لو أسماء الحقول متغيرة"],
             ["الخطأ الأشهر", "تسريب بيانات داخل النص", "تسجيل كائن كامل فيه بيانات شخصية"],
         ]},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Api/LoggingSetup.cs", "filename": "src/Orders.Api/LoggingSetup.cs", "code": r'''using OpenTelemetry.Resources;
using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Filters;
using Shop.Observability;

namespace Shop.Orders;

public static class LoggingSetup
{
    // مفتاحان للمستوى: يُغيَّران وقت التشغيل من الإعدادات (App Configuration أو endpoint إداري)
    public static readonly LoggingLevelSwitch DefaultSwitch = new(LogEventLevel.Information);
    public static readonly LoggingLevelSwitch MicrosoftSwitch = new(LogEventLevel.Warning);

    public static WebApplicationBuilder AddShopLogging(this WebApplicationBuilder builder)
    {
        var cfg = builder.Configuration;

        Log.Logger = new LoggerConfiguration()
            // ① المستوى العام + تجاوزات لكل مصدر ضجيج (أهم توفير في الفاتورة):
            .MinimumLevel.ControlledBy(DefaultSwitch)
            .MinimumLevel.Override("Microsoft", MicrosoftSwitch)
            .MinimumLevel.Override("Microsoft.EntityFrameworkCore", LogEventLevel.Warning)
            .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
            .MinimumLevel.Override("System.Net.Http.HttpClient", LogEventLevel.Warning)
            .MinimumLevel.Override("MassTransit", LogEventLevel.Warning)

            // ② الإثراء: سياق + بيئة + نسخة + TraceId/SpanId (من 7.1.2)
            .Enrich.FromLogContext()
            .Enrich.WithMachineName()
            .Enrich.WithProperty("service", "orders-api")
            .Enrich.WithProperty("environment", builder.Environment.EnvironmentName)
            .Enrich.WithProperty("version",
                typeof(LoggingSetup).Assembly.GetName().Version?.ToString() ?? "0.0.0")
            .Enrich.WithTraceContext()

            // ③ حماية البيانات: سياسة تحطيم + حجب الأنماط (الكود بالأسفل)
            .Destructure.With<PiiDestructuringPolicy>()
            .Enrich.With<PiiRedactionEnricher>()

            // ④ فرع خاص: تجاهل مسارات الفحص تمامًا (لا تكتبها في أي مكان)
            .Filter.ByExcluding(Matching.FromSource("Microsoft.AspNetCore.Diagnostics.HealthChecks"))
            .WriteTo.Logger(sub => sub
                .Filter.ByExcluding(e =>
                    e.Properties.TryGetValue("RequestPath", out var p) &&
                    (p.ToString().Contains("/health") || p.ToString().Contains("/alive")))
                .WriteTo.Console(outputTemplate:
                    "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} " +
                    "{TraceId}{NewLine}{Exception}"))

            // ⑤ الخلفية المركزية: اختر واحدًا (أو أكتر في مرحلة الانتقال)
            .WriteTo.Seq(cfg["Serilog:SeqUrl"] ?? "http://localhost:5341",
                restrictedToMinimumLevel: LogEventLevel.Information)

            // أو OTLP (لو عندك Collector + Loki/خلفية مُدارة):
            // .WriteTo.OpenTelemetry(o =>
            // {
            //     o.Endpoint = cfg["OTEL_EXPORTER_OTLP_ENDPOINT"] ?? "http://localhost:4317";
            //     o.Protocol = OtlpProtocol.Grpc;
            //     o.ResourceAttributes = new Dictionary<string, object>
            //     {
            //         ["service.name"] = "orders-api",
            //         ["deployment.environment.name"] = builder.Environment.EnvironmentName,
            //     };
            // })

            // ⑥ ملف محلي للاحتياط (لو الخلفية وقعت، ما تفقدش السجلات):
            .WriteTo.File("logs/orders-.log",
                rollingInterval: RollingInterval.Day,
                retainedFileCountLimit: 3,
                fileSizeLimitBytes: 20_000_000,
                restrictedToMinimumLevel: LogEventLevel.Warning)

            .CreateLogger();

        builder.Host.UseSerilog();   // يربط ILogger<T> بـSerilog (بما فيها سجلات الإطار)
        return builder;
    }
}

/// <summary>
/// سياسة تحطيم: تتحكم في **إيه اللي يتسجل من الكائنات** — العمق والخصائص.
/// الهدف: منع تسجيل كائن كامل فيه بيانات شخصية أو حجم ضخم.
/// </summary>
public sealed class PiiDestructuringPolicy : Serilog.Core.IDestructuringPolicy
{
    // أنواع تُسجَّل كمعرّف فقط (لا كل الخصائص):
    private static readonly HashSet<Type> Sensitive =
    [typeof(CustomerInfo), typeof(PaymentDetails), typeof(Address)];

    public bool TryDestructure(object value, Serilog.Core.ILogEventPropertyValueFactory factory,
        out Serilog.Events.LogEventPropertyValue result)
    {
        if (value is CustomerInfo c)
        {
            result = new Serilog.Events.StructureValue(
                [new Serilog.Events.LogEventProperty("CustomerId",
                    factory.CreatePropertyValue(c.CustomerId))],
                typeTag: "CustomerInfo");          // ← بلا اسم ولا بريد ولا هاتف
            return true;
        }

        if (Sensitive.Contains(value.GetType()))
        {
            result = factory.CreatePropertyValue($"[{value.GetType().Name}:redacted]");
            return true;
        }

        result = null!;
        return false;      // باقي الأنواع تُحطَّم بالطريقة العادية
    }
}

/// <summary>
/// حجب الأنماط من الرسالة نفسها (احتياطي أخير لو حد كتب بيانات في النص).
/// ⚠ الأفضل: لا تسجل البيانات أصلًا — الحجب بيقلل الضرر، ما يمنعهش.
/// </summary>
public sealed class PiiRedactionEnricher : ILogEventEnricher
{
    private static readonly (string Name, System.Text.RegularExpressions.Regex Pattern)[] Rules =
    [
        ("email", new(@"[\w\.\-+]+@[\w\.\-]+\.\w{2,}", System.Text.RegularExpressions.RegexOptions.Compiled)),
        ("phone_eg", new(@"\b(?:\+?2)?01[0125]\d{8}\b", System.Text.RegularExpressions.RegexOptions.Compiled)),
        ("card_like", new(@"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", System.Text.RegularExpressions.RegexOptions.Compiled)),
        ("national_id_eg", new(@"\b\d{14}\b", System.Text.RegularExpressions.RegexOptions.Compiled)),
    ];

    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        var msg = logEvent.MessageTemplate.Text;
        foreach (var (name, pattern) in Rules)
        {
            if (pattern.IsMatch(msg))
            {
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty(
                    "pii.detected", name));        // علامة تُنبّهك إن فيه تسريب في الكود
            }
        }
    }
}

public record CustomerInfo(string CustomerId, string FullName, string Email, string Phone);
public record PaymentDetails(string CardToken, string HolderName, string Expiry);
public record Address(string Street, string City, string Country);
'''},

        # ── 2) Correlation
        {"type": "heading", "level": 2, "text": "② CorrelationId: رحلة واحدة عبر كل الخدمات"},
        {"type": "code", "lang": "csharp", "title": "src/ServiceDefaults/CorrelationMiddleware.cs", "filename": "src/ServiceDefaults/CorrelationMiddleware.cs", "code": r'''using System.Diagnostics;
using Serilog.Context;

namespace Shop.Observability;

/// <summary>
/// يضمن إن كل طلب له CorrelationId:
///   ① من ترويسة واردة (من gateway/عميل/خدمة سابقة)
///   ② أو من TraceId الحالي (أفضل اختيار — يربط السجل بالتتبع مباشرة)
///   ③ أو معرّف جديد
/// ويرجعه في الاستجابة + في ProblemDetails (1.1.5) عشان المستخدم يقدر يقتبسه في بلاغه.
/// </summary>
public static class CorrelationMiddlewareExtensions
{
    public const string HeaderName = "X-Correlation-Id";

    public static IApplicationBuilder UseCorrelationId(this IApplicationBuilder app) =>
        app.Use(async (context, next) =>
        {
            var incoming = context.Request.Headers[HeaderName].FirstOrDefault();
            var correlationId =
                !string.IsNullOrWhiteSpace(incoming) ? incoming :
                Activity.Current?.TraceId.ToString() ??
                Guid.NewGuid().ToString("n");

            // ① في سياق Serilog → يظهر في كل سطر لهذا الطلب
            using (LogContext.PushProperty("CorrelationId", correlationId))
            // ② في Baggage → ينتقل للخدمات التالية عبر HTTP
            using (Activity.Current is { } act ? SetBaggage(act, correlationId) : default)
            {
                // ③ في الاستجابة → العميل/الدعم يقتبسه
                context.Response.OnStarting(() =>
                {
                    context.Response.Headers[HeaderName] = correlationId;
                    return Task.CompletedTask;
                });

                await next(context);
            }
        });

    private static IDisposable SetBaggage(Activity activity, string correlationId)
    {
        activity.SetBaggage("correlation.id", correlationId);
        return NoopDisposable.Instance;
    }

    private sealed class NoopDisposable : IDisposable
    {
        public static readonly NoopDisposable Instance = new();
        public void Dispose() { }
    }
}

/// <summary>
/// outgoing: يمرر CorrelationId صراحةً (احتياطي — Baggage بيعدي تلقائيًا مع W3C).
/// </summary>
public sealed class CorrelationHeaderHandler(IHttpContextAccessor http) : DelegatingHandler
{
    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken ct)
    {
        var id = http.HttpContext?.Request.Headers[CorrelationMiddlewareExtensions.HeaderName]
                 .FirstOrDefault()
                 ?? Activity.Current?.GetBaggageItem("correlation.id");

        if (!string.IsNullOrWhiteSpace(id))
            request.Headers.TryAddWithoutValidation(CorrelationMiddlewareExtensions.HeaderName, id);

        return await base.SendAsync(request, ct);
    }
}

/* التسجيل في Program.cs:
   builder.Services.AddHttpContextAccessor();
   builder.Services.AddTransient<CorrelationHeaderHandler>();
   builder.Services.AddHttpClient<PaymentClient>(c => …)
          .AddHttpMessageHandler<CorrelationHeaderHandler>();
   …
   app.UseCorrelationId();          // بعد UseRouting وقبل endpoints
   app.MapDefaultEndpoints();

   وإرجاعه في الأخطاء (ProblemDetails):
   builder.Services.AddProblemDetails(o => o.CustomizeProblemDetails = ctx =>
   {
       ctx.ProblemDetails.Extensions["correlationId"] =
           ctx.HttpContext.TraceIdentifier;       // أو قيمة الـCorrelationId
       ctx.ProblemDetails.Extensions["traceId"] =
           Activity.Current?.TraceId.ToString();
   });
*/
'''},

        # ── 3) حماية البيانات
        {"type": "heading", "level": 2, "text": "③ حماية البيانات في السجلات (البند اللي بيبقى حادث)"},
        {"type": "table", "caption": "أين تتسرب البيانات الشخصية وكيف تمنعها",
         "head": ["نوع البيانات", "أين تتسرب عادةً", "الحماية", "ملاحظة"],
         "rows": [
             ["بريد/هاتف/اسم", "سجلات الطلبات · رسائل الاستثناء · تسجيل كائن كامل (`{@Request}`)",
              "قوالب بلا حقول شخصية · `PiiDestructuringPolicy` · مراجعة كل `{@…}` في الكود",
              "أخطر مصدر: الاستثناء اللي بيطبع جسم الطلب"],
             ["بطاقة/حساب دفع", "سجلات تكامل الدفع · body كامل · نصوص SQL",
              "**لا تسجل جسم الطلب أصلًا** · خزن token مرجعي · حجب أنماط الأرقام",
              "لو محتاج دليل: سجّل آخر 4 أرقام مشفرة بالتجزئة (hash)"],
             ["رقم قومي/معرّف حكومي", "سجلات التحقق (KYC) · ملفات CSV للتصدير",
              "حقل مسموح به صراحةً + حجب (mask) · سجل مرجع بدل القيمة",
              "14 رقمًا في السياق المصري — نمط قابل للكشف آليًا"],
             ["ترويسات مصادقة (Authorization/Cookie)", "`EnrichWithHttpRequest` · سجلات proxy · OTel span attributes",
              "احذف الترويسات في Collector/المعالجة · لا تستخدم enrichers تلتقط كل الترويسات",
              "تسريب توكن = جلسة فعالة مسروقة"],
             ["نصوص SQL", "`SetDbStatementForText = true` · لوج EF Core على Information",
              "`hash` أو `delete` في Collector · مستوى Warning لـEF Core",
              "نص SQL قد يحتوي قيمًا مضمّنة (literals)"],
             ["عناوين IP", "سجلات الوصول · Kestrel · الـgateway",
              "قرّر: هل تحتاجها؟ لو نعم، احتفظ بها فترة قصيرة أو جزّئها",
              "IP = بيانات شخصية في كثير من التشريعات"],
             ["محتوى رسائل الطابور", "سجلات المستهلك · payload كامل",
              "سجّل المعرّفات والأنواع فقط · حجب الحقول الكبيرة",
              "الرسائل بتحتوي نفس بيانات الطلب"],
         ]},
        {"type": "callout", "kind": "danger", "title": "قاعدة الحذف: السجلات ما بتتنسيش لوحدها",
         "md": "لما مستخدم يطلب حذف بياناته (حق الحذف في GDPR وغيره)، السجلات المركزية **مكان آخر لازم تتعامل معه**: (1) لا تسجل البيانات أصلًا — أرخص وأضمن حل (2) لو اتسجلت، لازم يكون عندك مسار حذف/إخفاء هوية في الخلفية (بعض الخلفيات بتدعم حذف حسب حقل) (3) احتفاظ قصير (30 يومًا) بيقلل السطح (4) وثّق في سجل المعالجة (RoPA) إن السجلات تحتوي أي أنواع بيانات ولمدة كم. **والأهم: الحجب بعد الكتابة مش حماية كاملة** — السجل اتنسخ/اتصدّر/اتخزّن في ملف محلي احتياطي."},

        # ── 4) مستويات ديناميكية وتكلفة
        {"type": "heading", "level": 2, "text": "④ مستويات وقت التشغيل + خطة التكلفة"},
        {"type": "code", "lang": "csharp", "title": "DebugLevelEndpoint.cs — تغيير المستوى بلا نشر (بمصادقة صارمة)", "filename": "src/Orders.Api/Endpoints/DiagnosticsEndpoints.cs", "code": r'''using Microsoft.AspNetCore.Http;
using Serilog.Core;
using Serilog.Events;
using Shop.Orders;

namespace Shop.Api.Endpoints;

/// <summary>
/// تغيير مستوى اللوجنج وقت التشغيل — أداة تشخيص قوية وخطرة:
///   • محمية بمصادقة + دور (لا تُترك anonymous)
///   • مؤقتة (تنتهي تلقائيًا) عشان ما تنساش المستوى مفتوحًا → فاتورة وضجيج
///   • مسجّلة (مين فتح Debug وإمتى)
/// </summary>
public static class DiagnosticsEndpoints
{
    // ConcurrentDictionary: الحالة المشتركة بين الطلبات لازم تكون آمنة من التزامن
    private static readonly System.Collections.Concurrent.ConcurrentDictionary<string, DateTime> OpenedUntil = new();

    public static IEndpointRouteBuilder MapDiagnostics(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/admin/logging")
                       .RequireAuthorization("ObservabilityAdmin");   // سياسة/دور (2.2.x)

        group.MapGet("/", () => Results.Ok(new
        {
            @default = LoggingSetup.DefaultSwitch.MinimumLevel.ToString(),
            microsoft = LoggingSetup.MicrosoftSwitch.MinimumLevel.ToString(),
            elevatedUntil = OpenedUntil.TryGetValue(Environment.MachineName, out var t) ? t : null,
        }));

        group.MapPost("/elevate", (ElevateRequest req, ILogger<Program> log, TimeProvider time) =>
        {
            var minutes = Math.Clamp(req.Minutes, 1, 120);      // حد أقصى ساعتان
            var level = Enum.TryParse<LogEventLevel>(req.Level, true, out var parsed)
                ? parsed : LogEventLevel.Debug;

            LoggingSetup.DefaultSwitch.MinimumLevel = level;
            OpenedUntil[Environment.MachineName] = time.GetUtcNow().UtcDateTime.AddMinutes(minutes);

            log.LogWarning("Logging elevated to {Level} for {Minutes}m by {User}",
                level, minutes, "admin");       // سجّل التغيير نفسه دائمًا
            return Results.Ok(new { level = level.ToString(), until = OpenedUntil[Environment.MachineName] });
        });

        group.MapPost("/restore", (ILogger<Program> log) =>
        {
            LoggingSetup.DefaultSwitch.MinimumLevel = LogEventLevel.Information;
            LoggingSetup.MicrosoftSwitch.MinimumLevel = LogEventLevel.Warning;
            OpenedUntil.Remove(Environment.MachineName);
            log.LogInformation("Logging levels restored");
            return Results.NoContent();
        });

        return app;
    }

    /// <summary>
    /// الإنهاء التلقائي: خدمة خلفية بترجع المستويات بعد انتهاء المدة.
    /// (بدونها: حد يفتح Debug وينسى → ضجيج وفاتورة لأسابيع.)
    /// </summary>
    public sealed class LevelWatchdog(TimeProvider time, ILogger<LevelWatchdog> log) : BackgroundService
    {
        protected override async Task ExecuteAsync(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                await Task.Delay(TimeSpan.FromMinutes(1), ct);
                if (OpenedUntil.TryGetValue(Environment.MachineName, out var until)
                    && time.GetUtcNow().UtcDateTime > until)
                {
                    LoggingSetup.DefaultSwitch.MinimumLevel = LogEventLevel.Information;
                    LoggingSetup.MicrosoftSwitch.MinimumLevel = LogEventLevel.Warning;
                    OpenedUntil.Remove(Environment.MachineName);
                    log.LogWarning("Logging levels auto-restored after elevation window");
                }
            }
        }
    }
}

public record ElevateRequest(string Level, int Minutes);

/* البديل المؤسسي (أفضل للإنتاج): المستوى من App Configuration مع ReloadInterval
   → تغيير مركزي لكل النسخ + سجل تغييرات + صلاحيات، بلا endpoint في التطبيق.
   (6.2.3: AddAzureAppConfiguration + ConfigureKeyVault + ReloadInterval)
*/
'''},
        {"type": "table", "caption": "خطة تقليل تكلفة السجلات — مرتبة بالأثر (من 6.2.5)",
         "head": ["الإجراء", "الأثر النموذجي", "الأثر التشخيصي", "كيف تتحقق"],
         "rows": [
             ["`MinimumLevel.Override` لـEF Core وASP.NET وHttpClient على Warning",
              "**−40 إلى −70%** من الحجم", "منخفض (الاستعلامات الفردية بتظهر في الـspans)",
              "قارن GB/يوم قبل وبعد"],
             ["استبعاد `/health` و`/alive` (sub-logger + filter)",
              "−10 إلى −30% (حسب تردد الفحص وعدد النسخ)",
              "صفر (الفحوصات مغطاة بمقاييس)",
              "عدد أسطر الصحة قبل/بعد"],
             ["عدم تسجيل أجسام الطلبات/الاستجابات",
              "−30 إلى −80% للواجهات الثقيلة", "متوسط (استخدم الـspans + معرّفات)",
              "متوسط حجم الحدث"],
             ["sampling للسجلات المتكررة (مثلًا 1 من كل 100)",
              "−50%+ للأنماط المكررة", "منخفض لو مضبوط (احتفظ بالأخطاء 100%)",
              "عدّ النمط مقابل المتوقع"],
             ["الاحتفاظ: 30 يومًا ساخن + أرشيف بارد",
              "−تكلفة التخزين المستمر", "منخفض (الاسترجاع أبطأ)",
              "إعداد الاحتفاظ في الخلفية"],
             ["تحويل الأنماط المهمة لمقاييس (log-based metrics)",
              "تقليل الحاجة للسجلات في التنبيهات", "إيجابي (تنبيه أرخص وأسرع)",
              "عدد التنبيهات المعتمدة على بحث نصي"],
             ["حجب الحقول الكبيرة في Collector (`db.statement`, headers)",
              "−10 إلى −25% + حماية بيانات", "مقبول (hash يكفي للربط)",
              "حجم الـspan/السجل"],
         ]},

        # ── 5) الخلفيات
        {"type": "heading", "level": 2, "text": "⑤ الخلفيات: Seq · Loki · ELK · Azure Monitor"},
        {"type": "table", "caption": "اختيار واقعي لمشروع .NET (الأرقام تقريبية وتتغير)",
         "head": ["", "**Seq**", "**Grafana Loki**", "**ELK/OpenSearch**", "**Azure Monitor Logs**"],
         "rows": [
             ["التنصيب", "حاوية واحدة (أسهل)", "حاوية + Alloy/Promtail", "3+ عقد (الأثقل)", "خدمة مُدارة (بلا تنصيب)"],
             ["لغة الاستعلام", "SQL-like (`select … where OrderId='o-1'`)", "LogQL (فهرسة على labels فقط)", "KQL/Lucene (الأقوى)", "KQL"],
             ["فهرسة", "كاملة (بحث نصي سريع)", "**labels فقط** + بحث في المحتوى عند الطلب", "كاملة", "كاملة"],
             ["التكلفة النموذجية", "رخصة أو مجانية لمطور واحد", "**الأرخص تشغيليًا** (تخزين كائنات)", "الأعلى (فهرسة + JVM)", "لكل GB استيعاب + احتفاظ"],
             ["التكامل مع .NET", "ممتاز (Serilog sink أصلي)", "جيد (sink/OTLP + labels)", "جيد (sink)", "ممتاز (OTel/Azure SDK)"],
             ["الربط بالتتبع", "TraceId كحقل + رابط", "derived fields → Tempo (ممتاز مع Grafana)", "ممكن", "ممتاز (transaction details)"],
             ["الأنسب", "**مشروع فردي/فريق صغير على .NET**", "فرق بتشغّل Grafana أصلًا وحجم كبير", "بحث معقد/امتثال/تحليلات", "كله على Azure وبلا عمليات"],
             ["الحد/الخطر", "حجم البيانات في الرخصة", "labels عالية cardinality = كارثة", "تكلفة وصيانة", "تكلفة الاستيعاب (6.2.5)"],
         ]},
        {"type": "code", "lang": "yaml", "title": "docker-compose.observability.yml — stack محلي كامل", "filename": "docker-compose.observability.yml", "code": r'''# stack مراقبة محلي: Seq + Prometheus + Grafana + Collector
#   docker compose -f docker-compose.observability.yml up -d
services:
  seq:
    image: datalust/seq:latest
    ports: ["5341:80"]                  # UI على 5341 (OTLP/HTTP ingest مدعوم أيضًا)
    environment:
      ACCEPT_EULA: "Y"
    volumes: [seq-data:/data]

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector.yaml"]
    ports:
      - "127.0.0.1:4317:4317"           # OTLP/gRPC — loopback فقط (6.1.2)
      - "127.0.0.1:4318:4318"           # OTLP/HTTP
    volumes:
      - ./otel/collector-config.yaml:/etc/otel-collector.yaml:ro
    depends_on: [prometheus, seq]

  prometheus:
    image: prom/prometheus:latest
    ports: ["127.0.0.1:9090:9090"]
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./observability/rules.yml:/etc/prometheus/rules.yml:ro
      - prom-data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=15d
      - --storage.tsdb.path=/prometheus

  grafana:
    image: grafana/grafana:latest
    ports: ["127.0.0.1:3000:3000"]
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"      # محلي فقط — لا تفعلها في الإنتاج
      GF_AUTH_ANONYMOUS_ORG_ROLE: "Admin"
    volumes:
      - ./observability/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./observability/grafana-provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana

volumes:
  seq-data:
  prom-data:
  grafana-data:

# في تطبيقك:
#   OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
#   Serilog:SeqUrl=http://localhost:5341
'''},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أقدر أعدّ Serilog بمستويات وتجاوزات لكل مصدر ضجيج + إثراء بالسياق والبيئة والنسخة وTraceId.",
            "أعرف أستثني `/health` و`/alive` بـsub-logger وفلاتر، وأقيس الأثر على الحجم.",
            "أقدر أضيف CorrelationId (من الترويسة أو TraceId أو جديد) وأمرره للخدمات التالية وأرجعه في الاستجابة وProblemDetails.",
            "أعرف طبقات حماية البيانات: عدم التسجيل → سياسة تحطيم → حجب أنماط → حجب في Collector.",
            "أقدر أغيّر مستوى اللوجنج وقت التشغيل (LoggingLevelSwitch أو App Configuration) **بإنهاء تلقائي وسجل تغيير**.",
            "أعرف أرتب إجراءات تقليل التكلفة بالأثر وأقيس كل واحد.",
            "أقدر أختار خلفية (Seq/Loki/ELK/Azure Monitor) بمعايير: التنصيب · الاستعلام · التكلفة · الربط بالتتبع.",
            "فاهم إن السجلات مكان لازم يُعالج في طلبات حذف البيانات، وإن الحجب بعد الكتابة مش حماية كاملة.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على اللوجنج المركزي.",
         "questions": [
             {"q": "مستخدم بلّغ عن مشكلة واديته CorrelationId. إيه اللي يخليه مفيد فعلًا؟",
              "options": ["إنه GUID فريد", "**إنه موجود في كل سطر سجل لهذا الطلب + مُمرَّر للخدمات التالية + ظاهر في الاستجابة/ProblemDetails** — يعني بحث واحد يجمع الرحلة كلها", "إنه يُطبع في الكونسول", "إنه مرتبط بـTraceId فقط"],
              "answer": 1,
              "explain": "القيمة في الانتشار والاتساق: gateway → خدمة → طابور → worker. وأفضل مصدر له هو TraceId نفسه، لأنه كمان بيفتح الرحلة في الـtracing."},
             {"q": "أكبر مصدر لحجم السجلات في تطبيق .NET نموذجي؟",
              "options": ["أخطاء التطبيق", "**سجلات الإطار على مستوى Information (خصوصًا EF Core: كل استعلام) + مسارات الفحص كل 10 ثوانٍ**", "stack traces", "سجلات بدء التشغيل"],
              "answer": 1,
              "explain": "عشان كده أول إجراءين: `MinimumLevel.Override` على Microsoft/EF Core لـWarning، واستبعاد `/health` و`/alive` — غالبًا بينزلوا الحجم 50%+ بلا أي خسارة تشخيصية."},
             {"q": "فتحت مستوى Debug للتشخيص. إيه اللي لازم يصاحبه؟",
              "options": ["مفيش — Debug مفيد دايمًا", "**إنهاء تلقائي بعد مدة + تسجيل مَن فتحه ومتى + مصادقة/دور على نقطة التغيير** — وإلا هيفضل مفتوح لأسابيع (ضجيج + فاتورة)", "إعادة تشغيل بعد التصحيح", "تفعيله في كل النسخ"],
              "answer": 1,
              "explain": "الأداة القوية بلا قيد بتبقى حادث مؤجل. الحل: watchdog بيرجع المستويات + سجل للتغيير + صلاحيات. وفي الإنتاج المؤسسي: App Configuration بتغيير مركزي وسجل مراجعة."},
             {"q": "Loki بيحذر من «labels عالية cardinality». ليه؟",
              "options": ["لأنه بيخزن في ذاكرة", "**لأن Loki بيفهرس الـlabels فقط، فكل قيمة label جديدة = فهرس جديد؛ معرّفات زي OrderId كـlabel بتفجر الفهرس** (نفس مشكلة 7.1.1)", "لأنه بطيء في القراءة", "لأنه ما بيدعمش JSON"],
              "answer": 1,
              "explain": "القاعدة في Loki: labels قليلة ومحدودة (service · environment · level)، والمحتوى (OrderId · TraceId) يُبحث فيه نصيًا داخل السجل."},
             {"q": "إيه أفضل حماية لبيانات شخصية في السجلات؟",
              "options": ["حجب بأنماط regex بعد الكتابة", "**عدم تسجيلها أصلًا** (قوالب بلا حقول شخصية + سياسة تحطيم للكائنات) — الحجب طبقة احتياطية مش أساسية", "تشفير السجلات", "احتفاظ أقصر"],
              "answer": 1,
              "explain": "الحجب بيقلل الضرر لكن السجل اتكتب واتنسخ وقد يكون اتصدّر. والتشفير ما بيمنعش الوصول لمن يملك المفتاح (بما فيه من يسجلون). عدم التسجيل + سياسة تحطيم + مراجعة كل `{@…}` هو الحل."},
             {"q": "خلفية السجلات وقعت. إيه اللي يحميك من فقدان السجلات الحرجة؟",
              "options": ["مفيش حل", "**sink احتياطي محلي (ملف بمستوى Warning فأعلى) + دفعات وإعادة محاولة في الـsink المركزي + تنبيه على صحة خط السجلات نفسه**", "زيادة مستوى اللوج", "إعادة تشغيل التطبيق"],
              "answer": 1,
              "explain": "خط السجلات نفسه لازم يكون مرصودًا (مقياس لأحداث التصدير الفاشلة) — لأن فقدان السجلات صامت غالبًا. والملف المحلي بيديك حد أدنى وقت الحادث."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "بحث في ثانية + سجلات بلا بيانات شخصية.",
         "items": [
             {"id": "t1", "title": "مهمة 1: لوجنج مركزي تبحث فيه بثانية",
              "md": "**السياق:** نظام `shop` بيسجل في الكونسول فقط، والتشخيص بيستغرق وقتًا.\n\n**المطلوب:**\n1. `LoggingSetup` كامل: مستويات + تجاوزات (EF Core/ASP.NET/HttpClient على Warning) + إثراء (machine · environment · version · **TraceId/SpanId** · CorrelationId) + sink مركزي (Seq أو OTLP/Loki) + ملف احتياطي محلي بـWarning فأعلى.\n2. استبعاد `/health` و`/alive` بـsub-logger + filter، مع **قياس الحجم قبل وبعد** (عدد الأسطر/الـGB ليوم أو تحت حمل k6).\n3. CorrelationId middleware: من الترويسة أو TraceId أو جديد · في `LogContext` · في Baggage · في ترويسة الاستجابة · في `ProblemDetails`.\n4. `CorrelationHeaderHandler` على `HttpClient` للتأكد من وصوله للخدمات التالية + مستهلك الطابور بيقرأه من الهيدرز.\n5. مستوى قابل للتغيير وقت التشغيل (`LoggingLevelSwitch` + endpoint إداري بمصادقة + **watchdog للإنهاء التلقائي** + سجل للتغيير).\n6. **الدليل**: ثلاثة استعلامات في الخلفية تُرجع نتائج في أقل من ثانيتين: (أ) كل أحداث `OrderId='o-…'` (ب) كل أخطاء الدفع آخر ساعة مجمعة حسب السبب (ج) كل السجلات المرتبطة بـTraceId معين — مع لقطة/مخرج.\n7. `docs/logging.md`: بنية الحقول القياسية (الحقول الإلزامية في كل حدث) + قواعد كتابة السجل (إمتى Information وإمتى Warning) + إزاي تبحث (أمثلة) + خطة الاحتفاظ.",
              "criteria": [
                  "التجاوزات مطبقة والحجم مقيس **قبل/بعد** برقمين.",
                  "كل حدث فيه على الأقل: Timestamp · Level · service · environment · TraceId · CorrelationId · Message template.",
                  "CorrelationId ينتشر عبر HTTP والطابور (دليل: سجل في الـworker بنفس المعرّف).",
                  "ظهوره في ترويسة الاستجابة وفي `ProblemDetails.Extensions`.",
                  "endpoint إداري محمي بمصادقة/دور + إنهاء تلقائي بعد المدة + سجل للتغيير.",
                  "sink احتياطي محلي بمستوى أعلى (Warning) مع rolling واحتفاظ محدود.",
                  "ثلاثة استعلامات موثقة بنتائج (زمن الاستعلام مذكور).",
                  "`docs/logging.md` فيه الحقول القياسية وقواعد المستويات وأمثلة البحث وخطة الاحتفاظ.",
              ],
              "hint": "للقياس قبل/بعد: شغّل حملًا ثابتًا (k6 لمدة دقيقتين) وعدّ الأسطر/الحجم في الحالتين — ده أدق من الاعتماد على يوم كامل متغير. ولو Seq مش متاح، استخدم Console sink مع `docker compose logs | wc -l` كقياس تقريبي، أو OTLP إلى Collector مع exporter `debug` لعدّ الأحداث.",
              "solution": "الترتيب: (1) `LoggingSetup` بالتجاوزات والإثراء (2) استبعاد الفحص (3) Correlation middleware + handler (4) Seq أو Loki (5) endpoint + watchdog. الأرقام النموذجية: استبعاد `/health` + تجاوزات EF/ASPNET بينزلوا الحجم **50–75%** تحت حمل عادي. الاستعلامات الثلاثة: `select * from stream where OrderId = 'o-123' order by @t` (Seq) أو `{service=\"orders-api\"} |= \"o-123\"` (Loki) · تجميع أخطاء الدفع: `select Reason, count(*) from stream where SourceContext like '%Payment%' and Level='Error' group by Reason` · الربط بالتتبع: `where TraceId = '…'`. أهم نتيجة: زمن التشخيص بينزل من «دقائق من البحث النصي» لـ«ثوانٍ بحقل واحد».",
              "resources": [
                  "https://serilog.net/",
                  "https://github.com/serilog/serilog-aspnetcore",
                  "https://docs.datalust.co/docs/the-seq-query-language",
                  "https://grafana.com/docs/loki/latest/query/",
                  "https://learn.microsoft.com/en-us/dotnet/core/extensions/logging",
                  "https://opentelemetry.io/docs/specs/semconv/registry/attributes/",
              ]},
             {"id": "t2", "title": "مهمة 2: سجّل بلا بيانات شخصية (تدقيق + حجب + اختبار)",
              "md": "**السياق:** تطبيقك بيسجل كائنات الطلب والعملاء، ومحتاج تضمن إن مفيش بيانات شخصية بتوصل للخلفية.\n\n**المطلوب:**\n1. **تدقيق**: اكتب `scripts/log-audit.sh` يجمع عينة من السجلات (1000 حدث) ويبحث عن أنماط: بريد · هاتف مصري (01xxxxxxxxx) · 14 رقمًا · أرقام بطاقات · نصوص SQL · ترويسات مصادقة — ويطبع جدول (النمط · العدد · مثال محجوب · المصدر `SourceContext`).\n2. **إصلاح**: لكل مصدر تسريب: إما تغيير قالب السجل · أو `IDestructuringPolicy` · أو حذف enricher · أو حجب في Collector.\n3. **حماية مستمرة**: enricher يضع علامة `pii.detected` لو نمط ظهر في الرسالة، و**تنبيه** لو العلامة ظهرت (لأن معناها تسريب جديد في الكود).\n4. **اختبارات**: (أ) اختبار وحدة على سياسة التحطيم (كائن `CustomerInfo` يُسجَّل كمعرّف فقط) (ب) اختبار يمرر رسالة فيها بريد/هاتف ويتحقق إن المخرجات محجوبة/معلّمة (ج) اختبار يضمن إن مفيش `{@…}` في الكود على أنواع حساسة (فحص نصي بسيط على المصادر).\n5. **حجب في Collector**: قواعد لحجب `db.statement` (hash) و`http.request.header.authorization` (delete) وسمات العملاء (hash) — مطبقة ومُختبَرة.\n6. `docs/logging-privacy.md`: جدول (نوع البيانات · هل يُسجَّل؟ · الشكل المسموح · الاحتفاظ · أساس الحذف) + فقرة عن طلبات حذف البيانات (إيه اللي بتعمله بالسجلات).\n7. أعد تشغيل التدقيق بعد الإصلاح ووثّق الفرق (عدد الاكتشافات قبل/بعد).",
              "criteria": [
                  "سكربت تدقيق يغطي 6 أنماط على الأقل ويطبع المصدر لكل اكتشاف.",
                  "كل مصدر تسريب مُصلح (مش محجوب فقط) مع ذكر الطريقة.",
                  "enricher + تنبيه على `pii.detected` (التسريب الجديد بيظهر فورًا).",
                  "3 اختبارات (سياسة التحطيم · الحجب · فحص `{@…}` على أنواع حساسة).",
                  "قواعد Collector مطبقة ومُختبَرة (قارن مخرجات قبل/بعد على نفس الطلب).",
                  "وثيقة خصوصية فيها جدول البيانات والاحتفاظ ومسار الحذف.",
                  "رقم قبل/بعد من التدقيق (مثال: 47 اكتشافًا → 0).",
                  "ملاحظة صريحة إن الحجب بعد الكتابة ليس حماية كاملة وإيه البدائل.",
              ],
              "hint": "أخطر مصدر غالبًا: `log.LogInformation(\"Request {@Body}\", body)` أو تسجيل `HttpRequest` كامل في middleware. ابحث عن `{@` في الكود: `grep -rn '{@' src/`. وللهاتف المصري: النمط `\\b(?:\\+?2)?01[0125]\\d{8}\\b`. ولو بتستخدم OTel logs بدل Serilog sink، الحجب ممكن في Collector بمعالج `attributes` أو `transform`.",
              "solution": "النتائج النموذجية: التدقيق الأول بيكشف 3 مصادر رئيسية: (1) `{@Request}` في middleware تسجيل الطلبات (2) نص SQL كامل من EF Core على Information (3) بريد العميل في رسالة تأكيد الطلب. الإصلاح: (1) استبدل بـ`log.LogInformation(\"Request {Method} {Path} {OrderId}\", …)` (2) مستوى Warning لـEF + hash لـ`db.statement` في Collector (3) `PiiDestructuringPolicy` تُسجّل `CustomerId` فقط. النتيجة: 47 اكتشافًا → 0، مع انخفاض حجم السجلات ~35% كتأثير جانبي. الاختبارات: سياسة التحطيم بتُرجع `StructureValue` فيه `CustomerId` فقط؛ اختبار الحجب بيأكد إن `pii.detected=email` اتضاف؛ فحص `{@` بيمنع إضافة تسجيل كائنات جديدة بلا مراجعة. وثيقة الخصوصية: بريد/هاتف لا يُسجلان · IP يُسجَّل 7 أيام فقط · `OrderId`/`CustomerId` مسموحان 30 يومًا · عند طلب الحذف: إخفاء هوية الحقول في الخلفية + حذف الملف المحلي الاحتياطي + توثيق في RoPA.",
              "resources": [
                  "https://learn.microsoft.com/en-us/dotnet/core/extensions/logging",
                  "https://opentelemetry.io/docs/collector/transforming-telemetry/",
                  "https://gdpr.eu/right-to-be-forgotten/",
                  "https://serilog.net/",
                  "https://learn.microsoft.com/en-us/aspnet/core/fundamentals/logging/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Serilog", "url": "https://serilog.net/"},
            {"label": "Serilog.AspNetCore", "url": "https://github.com/serilog/serilog-aspnetcore"},
            {"label": "اللوجنج في .NET (Microsoft Learn)", "url": "https://learn.microsoft.com/en-us/dotnet/core/extensions/logging"},
            {"label": "لغة استعلام Seq", "url": "https://docs.datalust.co/docs/the-seq-query-language"},
            {"label": "Grafana Loki واستعلام LogQL", "url": "https://grafana.com/docs/loki/latest/"},
            {"label": "OpenTelemetry Logs (المفاهيم)", "url": "https://opentelemetry.io/docs/concepts/signals/logs/"},
            {"label": "معالجة وحجب البيانات في Collector", "url": "https://opentelemetry.io/docs/collector/transforming-telemetry/"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s7-m1-l4 — Prometheus وGrafana: لوحات تشرح الحالة
# ══════════════════════════════════════════════════════════════════════════
_L4 = {
    "id": "s7-m1-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "لوحة المراقبة مش زينة — هي **أداة تشخيص**: لازم تجاوب في ثانيتين على «هل فيه مشكلة؟ أين؟ ما حجمها؟ هل بتزيد؟». في الدرس ده: بنية Prometheus (scrape مقابل OTLP push) · **PromQL** بالاستعلامات الـ12 اللي هتستخدمهم فعلًا · لوحة RED + USE مصممة على الأسئلة · **recording rules** للسرعة · لوحات runtime لـ.NET (GC · thread pool · exceptions) · وأخطاء الإعداد اللي بتخلي الأرقام غلط (وإنت مصدقها)."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Pull/scrape مقابل Push", "def": "**Pull**: Prometheus بيجيب `/metrics` من كل هدف كل فترة (scrape). **Push**: التطبيق بيبعت OTLP لـCollector أو لـPrometheus OTLP receiver. الاتنين مدعومين؛ الاختيار بيأثر على service discovery والأمان."},
            {"term": "Series (سلسلة زمنية)", "def": "اسم مقياس + مجموعة labels محددة. كل مجموعة قيم جديدة = سلسلة جديدة = ذاكرة وتكلفة (cardinality — 7.1.1)."},
            {"term": "Counter مقابل Gauge مقابل Histogram", "def": "**Counter** يزيد فقط (يُقرأ بـ`rate`) · **Gauge** يزيد وينقص (يُقرأ مباشرة) · **Histogram** يوزع القيم على buckets (يُقرأ بـ`histogram_quantile`)."},
            {"term": "`rate()` و`increase()`", "def": "`rate(m[5m])` = متوسط الزيادة في الثانية (بيتعامل مع إعادة ضبط العدّاد). `increase(m[5m])` = الزيادة الكلية. **لا تستخدم `irate` للوحات** (حساس جدًا ومتقلب)."},
            {"term": "`histogram_quantile`", "def": "يقدّر النسبة المئوية من الـbuckets. الدقة تعتمد على حدود الـbuckets — لو p99 خارج أعلى bucket هترجع قيمة خاطئة."},
            {"term": "Recording rule", "def": "استعلام محسوب مسبقًا يُخزَّن كسلسلة جديدة (`job:http_requests:rate5m`) — بيسرّع اللوحات والتنبيهات ويوحّد التعريفات."},
            {"term": "Alerting rule + Alertmanager", "def": "القاعدة بتقيّم في Prometheus وتبعت تنبيهًا لـAlertmanager اللي بيتولى التجميع (grouping) · الكبت (inhibition) · الصمت (silence) · التوجيه (routing)."},
            {"term": "Annotation على اللوحة", "def": "خط رأسي على الرسم يوضح حدثًا (نشر · تغيير إعداد · حادث) — بدونه بتقرا تغييرًا في الرسم من غير ما تعرف سببه."},
            {"term": "Exemplars", "def": "ربط نقطة في الـhistogram بـ`trace_id` → من اللوحة للرحلة مباشرة (7.1.2)."},
            {"term": "kube-state-metrics / node_exporter", "def": "مصدرا مقاييس جاهزان: حالة موارد Kubernetes (pods/deployments) ومقاييس النظام (CPU/ذاكرة/قرص/شبكة)."},
            {"term": "Managed Prometheus", "def": "خدمة مُدارة (مثلًا Azure Monitor Managed Prometheus) بتستقبل remote write/OTLP وتوفر الاستعلام لـGrafana — بلا تشغيل TSDB بنفسك."},
        ]},

        # ── 1) البنية
        {"type": "heading", "level": 2, "text": "① البنية: من عداد في كودك لرسم على الشاشة"},
        {"type": "code", "lang": "text", "title": "مسار المقاييس + نقاط القرار", "filename": "docs/metrics-pipeline.txt", "code": r'''  التطبيق (.NET)                 الجمع                   التخزين/الاستعلام        العرض/التنبيه
 ┌───────────────────┐   ┌──────────────────────┐   ┌────────────────┐   ┌──────────────────┐
 │ Meter + instruments│  │ MeterProvider         │   │ Prometheus TSDB │   │ Grafana          │
 │  (Counter/Histogram│─▶│  • readers (Periodic) │──▶│  • series + labels│──▶│  • لوحات RED/USE │
 │   /ObservableGauge)│  │  • views (buckets/    │OTLP│  • retention    │   │  • متغيرات       │
 │                    │  │    TagKeys/limits)    │4317│  • recording rules│ │  • annotations   │
 │ ASP.NET Core/Kestrel│ │                       │   └───────┬────────┘   └──────────────────┘
 │ Runtime (.NET)     │  └──────────┬───────────┘           │ rules
 │ SqlClient/HttpClient│            │                        ▼
 └───────────────────┘             │              ┌────────────────────┐
        │                          │              │ Alertmanager       │
        │  (بديل: /metrics pull)   ▼              │ grouping/inhibition │
        └────────────────▶ Prometheus scrape      │ silence/routing    │
                                                   └─────────┬──────────┘
                                                             ▼
                                                    PagerDuty/Slack/Email/Teams

 قرارات:
   ① pull مقابل push(OTLP): pull أبسط للـVMs/service discovery؛ push أفضل خلف NAT/للسيرفرلس ومع Collector.
   ② buckets: لازم تغطي نطاق p95/p99 الحقيقي (وإلا histogram_quantile بيكذب).
   ③ labels: قليلة ومحدودة (service · route · status · instance · version · env).
   ④ recording rules: لكل استعلام مستخدم في ≥2 مكان (لوحة + تنبيه) — تعريف واحد.
'''},
        {"type": "code", "lang": "yaml", "title": "observability/prometheus.yml + rules.yml", "filename": "observability/prometheus.yml", "code": r'''global:
  scrape_interval: 15s          # 15s كفاية لأغلب الاستخدامات؛ 5s يضاعف الحجم
  evaluation_interval: 30s      # تقييم القواعد
  external_labels:
    cluster: local
    environment: dev

# استقبال OTLP من التطبيق/الـCollector (بديلًا عن الـscrape):
otlp:
  # يحتاج تفعيل receiver في الإصدار المثبت (تحقق من توثيق إصدارك):
  #   --web.enable-otlp-receiver   أو قسم otlp في الإعداد
  promote_resource_attributes:
    - service.name
    - service.version
    - deployment.environment.name
  keep_identifying_resource_attributes: true

rule_files:
  - /etc/prometheus/rules.yml

scrape_configs:
  # ① أهداف ثابتة (التطبيقات اللي بتكشف /metrics):
  - job_name: shop-services
    metrics_path: /metrics
    static_configs:
      - targets: ["host.docker.internal:5001"]
        labels: { service: orders-api, environment: dev }
      - targets: ["host.docker.internal:5002"]
        labels: { service: catalog-api, environment: dev }

  # ② Prometheus نفسه (لمراقبة المراقبة):
  - job_name: prometheus
    static_configs: [{ targets: ["localhost:9090"] }]

  # ③ Kubernetes: اكتشاف تلقائي للـpods بتعليمة (لو على cluster):
  # - job_name: kubernetes-pods
  #   kubernetes_sd_configs: [{ role: pod }]
  #   relabel_configs:
  #     - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  #       action: keep
  #       regex: "true"
  #     - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
  #       action: replace
  #       target_label: __metrics_path__

alerting:
  alertmanagers:
    - static_configs: [{ targets: ["alertmanager:9093"] }]
'''},
        {"type": "code", "lang": "yaml", "title": "observability/rules.yml — recording + alerting", "filename": "observability/rules.yml", "code": r'''groups:
  # ── Recording rules: تعريف واحد يُستخدم في اللوحات والتنبيهات ──
  - name: shop-red
    interval: 30s
    rules:
      - record: job:http_requests:rate5m
        expr: sum by (service, http_route) (rate(http_server_request_duration_seconds_count[5m]))

      - record: job:http_errors:ratio_rate5m
        expr: |
          sum by (service, http_route) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[5m]))
          /
          sum by (service, http_route) (rate(http_server_request_duration_seconds_count[5m]))

      - record: job:http_p95_seconds:rate5m
        expr: |
          histogram_quantile(0.95,
            sum by (service, http_route, le) (
              rate(http_server_request_duration_seconds_bucket[5m])))

      - record: job:http_p99_seconds:rate5m
        expr: |
          histogram_quantile(0.99,
            sum by (service, http_route, le) (
              rate(http_server_request_duration_seconds_bucket[5m])))

      # SLI جاهز لـ7.1.5: نسبة الطلبات الناجحة
      - record: job:sli_success:ratio_rate5m
        expr: 1 - job:http_errors:ratio_rate5m

  # ── قواعد تشبع/موارد ──
  - name: shop-use
    interval: 30s
    rules:
      - record: job:queue_oldest_age_seconds:max
        # gauge بوحدات ثوانٍ → الاسم في Prometheus يأخذ _seconds:
        expr: max by (service) (shop_outbox_oldest_age_seconds)

      - record: job:dotnet_gc_heap_bytes:sum
        # الاسم يختلف بين إصدارات instrumentation:
        #   قديم: process_runtime_dotnet_gc_heap_size
        #   حديث: dotnet_gc_heap_size   ← تحقق من مخرجاتك الفعلية
        expr: sum by (service, dotnet_gc_heap_generation) (dotnet_gc_heap_size)

  # ── تنبيهات (الأعراض، لا الأسباب — 7.1.5) ──
  - name: shop-alerts
    rules:
      - alert: ServiceDown
        expr: absent(up{job="shop-services"} == 1)
        for: 2m
        labels: { severity: critical, team: platform }
        annotations:
          summary: "خدمة {{ $labels.service }} لا تُصدر مقاييس"
          description: "لا توجد سلسلة up==1 لمدة دقيقتين — تحقق من النسخ و/أو الـscrape."
          runbook: "docs/runbooks/service-down.md"

      - alert: HighErrorRate
        expr: job:http_errors:ratio_rate5m > 0.01
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "نسبة 5xx أعلى من 1% على {{ $labels.service }}{{ $labels.http_route }}"
          runbook: "docs/runbooks/high-error-rate.md"

      - alert: QueueLagGrowing
        expr: job:queue_oldest_age_seconds:max > 300
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "أقدم رسالة في outbox عمرها > 5 دقائق — الناشر متوقف غالبًا"
          runbook: "docs/runbooks/queue-lag.md"

      - alert: HighLatencyP95
        expr: job:http_p95_seconds:rate5m > 0.5
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "p95 تجاوز 500ms على {{ $labels.service }}"
'''},

        # ── 2) PromQL
        {"type": "heading", "level": 2, "text": "② PromQL: 12 استعلامًا هتستخدمهم فعلًا"},
        {"type": "code", "lang": "text", "title": "observability/promql-cheatsheet.txt", "filename": "observability/promql-cheatsheet.txt", "code": r'''# ملاحظة أسماء (مهمة جدًا — اطبع الأسماء الفعلية أولًا):
#   النقاط → شرطات سفلية:   http.server.request.duration → http_server_request_duration
#   الوحدة بتُلحق بالاسم:    _seconds · _bytes · _ratio
#   الـcounter بياخد _total: shop.orders.placed → shop_orders_placed_total
#   السمة بتبقى label:       http.route → http_route
#   الـhistogram بينتج:      _bucket{le=…} · _sum · _count

# ── RED ──────────────────────────────────────────────────────────────
# 1) Rate: طلب/ثانية لكل مسار
sum by (service, http_route) (rate(http_server_request_duration_seconds_count[5m]))

# 2) Errors: نسبة 5xx
sum by (service) (rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[5m]))
/
sum by (service) (rate(http_server_request_duration_seconds_count[5m]))

# 3) Duration: p95 (لاحظ sum by le — بدونه histogram_quantile بيرجع NaN)
histogram_quantile(0.95,
  sum by (service, http_route, le) (rate(http_server_request_duration_seconds_bucket[5m])))

# 4) متوسط الزمن (احتياطي — الـpercentiles أفضل)
sum by (service) (rate(http_server_request_duration_seconds_sum[5m]))
/
sum by (service) (rate(http_server_request_duration_seconds_count[5m]))

# 5) أبطأ 5 مسارات حاليًا
topk(5,
  histogram_quantile(0.95,
    sum by (service, http_route, le) (rate(http_server_request_duration_seconds_bucket[5m]))))

# 6) مقارنة بالأمس (هل ده طبيعي في هذا الوقت؟)
sum(rate(http_server_request_duration_seconds_count[5m]))
/
sum(rate(http_server_request_duration_seconds_count[5m] offset 1d))

# ── USE / موارد ─────────────────────────────────────────────────────
# 7) تشبع: طلبات نشطة مقابل الحد
sum by (service) (http_server_active_requests)

# 8) طابور thread pool في .NET
max by (service, service_instance_id) (dotnet_thread_pool_queue_length)

# 9) GC: حجم الـheap حسب الجيل + عدد تجميعات الجيل الثاني (الأغلى)
sum by (service, dotnet_gc_heap_generation) (dotnet_gc_heap_size)
increase(dotnet_gc_collection_count{dotnet_gc_generation="gen2"}[15m])

# 10) استثناءات حسب النوع (أشهر أسباب الضجيج)
topk(5, sum by (exception_type) (increase(dotnet_exceptions_count[15m])))

# ── الطوابير والأعمال ───────────────────────────────────────────────
# 11) lag بالعمر (أهم من العدد — 7.1.1) — لاحظ _seconds المضافة من الوحدة
max by (service) (shop_outbox_oldest_age_seconds)

# 12) طلبات أعمال مقابل أمس (كشف انخفاض غير مبرر)
sum(increase(shop_orders_placed_total[1h]))
/
sum(increase(shop_orders_placed_total[1h] offset 1d))

# ── صيانة/تشخيص ─────────────────────────────────────────────────────
# هل الهدف مفقود؟                 absent(up{job="shop-services"} == 1)
# كم سلسلة زمنية نشطة (cardinality)? prometheus_tsdb_head_series
# أعلى المقاييس تكلفة:              topk(10, count by (__name__)({__name__=~".+"}))
# هل فيه churn (سلاسل بتظهر وتختفي)? rate(prometheus_tsdb_head_series_created_total[5m])
'''},

        # ── 3) اللوحة
        {"type": "heading", "level": 2, "text": "③ لوحة تُصمم على الأسئلة (مش على المقاييس المتاحة)"},
        {"type": "table", "caption": "ترتيب اللوحة من الأعلى للأسفل = ترتيب أسئلتك وقت الحادث",
         "head": ["الصف", "السؤال", "اللوحات", "الاستعلام"],
         "rows": [
             ["1", "هل فيه مشكلة الآن؟", "نسبة 5xx · p95 · rate (3 أرقام كبيرة مع عتبات لونية)", "`job:http_errors:ratio_rate5m` · `job:http_p95_seconds:rate5m` · `job:http_requests:rate5m`"],
             ["2", "أين؟ (أي مسار/نسخة)", "تقسيم حسب `http_route` و`service_instance_id` · topk الأبطأ", "`topk(5, …)` + `sum by (http_route)`"],
             ["3", "هل الموارد مشبعة؟", "GC heap · thread pool queue · اتصالات DB المستخدمة · active requests", "استعلامات 7–9 + مقياس اتصالات من الـpool"],
             ["4", "هل الطوابير بتتراكم؟", "عمر أقدم رسالة · عدد الرسائل · DLQ", "`job:queue_oldest_age_seconds:max`"],
             ["5", "هل الأثر على الأعمال؟", "طلبات مكتملة مقابل أمس · فشل حسب السبب", "استعلام 12 + `sum by (shop_failure_kind)`"],
             ["6", "إيه اللي اتغير؟", "**annotations**: نشر · تغيير إعداد · حوادث", "من `deployments.log` أو datasource للأحداث"],
         ]},
        {"type": "code", "lang": "json", "title": "observability/grafana/dashboards/shop-red.json (مختصر)", "filename": "observability/grafana/dashboards/shop-red.json", "code": r'''{
  "title": "Shop — RED & USE",
  "uid": "shop-red",
  "tags": ["shop", "red", "use"],
  "timezone": "browser",
  "refresh": "30s",
  "time": { "from": "now-3h", "to": "now" },
  "templating": {
    "list": [
      {
        "name": "service",
        "type": "query",
        "datasource": { "type": "prometheus", "uid": "prometheus" },
        "query": "label_values(http_server_request_duration_seconds_count, service)",
        "includeAll": true,
        "multi": true,
        "current": { "text": "All", "value": "$__all" }
      },
      {
        "name": "route",
        "type": "query",
        "query": "label_values(http_server_request_duration_seconds_count{service=~\"$service\"}, http_route)",
        "includeAll": true,
        "multi": true
      }
    ]
  },
  "annotations": {
    "list": [
      {
        "name": "Deployments",
        "datasource": { "type": "grafana", "uid": "-- Grafana --" },
        "enable": true,
        "iconColor": "blue",
        "target": {
          "limit": 100,
          "matchAny": false,
          "tags": ["deploy", "shop"],
          "type": "dashboard"
        }
      }
    ]
  },
  "panels": [
    {
      "id": 1, "type": "stat", "title": "نسبة 5xx (الآن)",
      "gridPos": { "h": 5, "w": 6, "x": 0, "y": 0 },
      "fieldConfig": { "defaults": { "unit": "percentunit", "thresholds": {
        "mode": "absolute",
        "steps": [
          { "color": "green", "value": null },
          { "color": "yellow", "value": 0.005 },
          { "color": "red", "value": 0.01 }
        ] } } },
      "targets": [ { "expr":
        "sum(job:http_errors:ratio_rate5m{service=~\"$service\"}) / count(job:http_errors:ratio_rate5m{service=~\"$service\"})",
        "legendFormat": "5xx ratio" } ]
    },
    {
      "id": 2, "type": "timeseries", "title": "Rate — طلب/ثانية لكل مسار",
      "gridPos": { "h": 8, "w": 12, "x": 6, "y": 0 },
      "fieldConfig": { "defaults": { "unit": "reqps" } },
      "targets": [ { "expr":
        "sum by (http_route) (job:http_requests:rate5m{service=~\"$service\", http_route=~\"$route\"})",
        "legendFormat": "{{http_route}}" } ]
    },
    {
      "id": 3, "type": "timeseries", "title": "Duration — p50/p95/p99",
      "gridPos": { "h": 8, "w": 12, "x": 18, "y": 0 },
      "fieldConfig": { "defaults": { "unit": "s" } },
      "targets": [
        { "expr": "histogram_quantile(0.50, sum by (le) (rate(http_server_request_duration_seconds_bucket{service=~\"$service\"}[5m])))", "legendFormat": "p50" },
        { "expr": "job:http_p95_seconds:rate5m{service=~\"$service\"}", "legendFormat": "p95" },
        { "expr": "job:http_p99_seconds:rate5m{service=~\"$service\"}", "legendFormat": "p99" }
      ]
    },
    {
      "id": 4, "type": "timeseries", "title": "USE — GC heap حسب الجيل",
      "gridPos": { "h": 7, "w": 8, "x": 0, "y": 8 },
      "fieldConfig": { "defaults": { "unit": "bytes" } },
      "targets": [ { "expr":
        "sum by (dotnet_gc_heap_generation) (dotnet_gc_heap_size{service=~\"$service\"})",
        "legendFormat": "{{dotnet_gc_heap_generation}}" } ]
    },
    {
      "id": 5, "type": "timeseries", "title": "USE — طابور thread pool",
      "gridPos": { "h": 7, "w": 8, "x": 8, "y": 8 },
      "targets": [ { "expr":
        "max by (service_instance_id) (dotnet_thread_pool_queue_length{service=~\"$service\"})",
        "legendFormat": "{{service_instance_id}}" } ]
    },
    {
      "id": 6, "type": "timeseries", "title": "طابور الأعمال — عمر أقدم رسالة",
      "gridPos": { "h": 7, "w": 8, "x": 16, "y": 8 },
      "fieldConfig": { "defaults": { "unit": "s", "thresholds": { "mode": "absolute",
        "steps": [ { "color": "green", "value": null }, { "color": "red", "value": 300 } ] } } },
      "targets": [ { "expr": "job:queue_oldest_age_seconds:max{service=~\"$service\"}", "legendFormat": "oldest" } ]
    },
    {
      "id": 7, "type": "timeseries", "title": "أعمال — طلبات مقابل أمس",
      "gridPos": { "h": 7, "w": 12, "x": 0, "y": 15 },
      "targets": [
        { "expr": "sum(increase(shop_orders_placed_total{service=~\"$service\"}[1h]))", "legendFormat": "اليوم" },
        { "expr": "sum(increase(shop_orders_placed_total{service=~\"$service\"}[1h] offset 1d))", "legendFormat": "أمس" }
      ]
    },
    {
      "id": 8, "type": "table", "title": "أشهر الاستثناءات (15 دقيقة)",
      "gridPos": { "h": 7, "w": 12, "x": 12, "y": 15 },
      "targets": [ { "expr":
        "topk(5, sum by (exception_type) (increase(dotnet_exceptions_count{service=~\"$service\"}[15m])))",
        "format": "table", "instant": true } ]
    }
  ]
}
'''},

        # ── 4) runtime
        {"type": "heading", "level": 2, "text": "④ مقاييس runtime في .NET: إيه اللي يقيس إيه"},
        {"type": "table", "caption": "الأسماء بتختلف بين إصدارات `OpenTelemetry.Instrumentation.Runtime` — تحقق من مخرجاتك",
         "head": ["المقياس", "معناه", "العتبة العملية", "السؤال اللي بيجاوبه"],
         "rows": [
             ["`dotnet_gc_heap_size` (بـlabel للجيل)", "حجم الـheap لكل جيل",
              "اقتراب من حد الذاكرة (6.1.5) = خطر OOMKill", "هل الذاكرة بتكبر بلا رجوع (تسريب)؟"],
             ["`dotnet_gc_collection_count` (gen0/1/2)", "عدد التجميعات لكل جيل",
              "gen2 متكرر = ضغط ذاكرة/تصميم كائنات", "هل الـGC بياكل CPU؟"],
             ["`dotnet_gc_duration` / `time_in_gc`", "نسبة الوقت في GC",
              "أكثر من ~10% = مشكلة", "هل البطء من GC؟"],
             ["`dotnet_thread_pool_threads_count`", "عدد خيوط الـpool",
              "زيادة مستمرة = حظر خيوط (sync-over-async)", "هل فيه كود متزامن بيخنق التطبيق؟ (3.3)"],
             ["`dotnet_thread_pool_queue_length`", "طول طابور العمل",
              "> 0 باستمرار = تشبع", "هل الطلبات بتستنى قبل ما تبدأ؟"],
             ["`dotnet_monitor_lock_contention_count`", "عدد مرات التنافس على الأقفال",
              "زيادة حادة = اختناق تزامن", "أين الاختناق في الكود المتزامن؟"],
             ["`dotnet_exceptions_count` (بـ`exception_type`)", "عدد الاستثناءات",
              "استثناء واحد مكرر = عطل صامت", "هل فيه أخطاء مش بتظهر كـ5xx؟"],
             ["`dotnet_timer_count`", "عدد المؤقتات",
              "نمو مستمر = تسريب مؤشرات", "هل فيه `Timer`/`CancellationTokenSource` بلا dispose؟"],
             ["`http_server_active_requests`", "الطلبات الجارية الآن",
              "اقتراب من حد الـpool/الاتصالات", "هل التشبع في التطبيق أم في التبعيات؟"],
             ["`db_client_connection_count` / usage", "اتصالات القاعدة المستخدمة",
              "اقتراب من `Max Pool Size` = رفض اتصالات", "هل الـpool هو الاختناق؟ (6.1.5)"],
         ]},
        {"type": "callout", "kind": "warn", "title": "ست أخطاء بتخلي الأرقام غلط وإنت مصدقها",
         "md": "**① `histogram_quantile` بلا `sum by (le)`** → NaN أو قيم غلط (الـ`le` لازم يُحفظ). **② buckets ما بتغطيش النطاق الحقيقي** → p99 مقدّر بأقل من الواقع (لو كل الطلبات فوق أعلى bucket، النتيجة = الحد الأقصى). **③ `rate()` على gauge** → أرقام بلا معنى (الـgauge يُقرأ مباشرة أو بـ`avg_over_time`). **④ `irate` في اللوحات** → رسم متقلب يصعب قراءته (استخدم `rate` بنافذة ≥ 4× فترة الـscrape). **⑤ مقارنة سلاسل مفقودة** (`/` على صفر) → NaN؛ استخدم `clamp_min` أو تحقق من وجود المقام. **⑥ أسماء مقاييس قديمة**: `process_runtime_dotnet_*` في إصدارات أقدم مقابل `dotnet_*` في الحديثة — لو اللوحة فاضية، اطبع الأسماء الفعلية أولًا (`count by (__name__)({__name__=~\"dotnet.+\"})`). **⑦ نسيان ترجمة OTLP إلى Prometheus**: الوحدة بتُلحق بالاسم (`_seconds`/`_bytes`) والـcounter بياخد `_total` — يعني `shop.orders.placed` بتظهر كـ`shop_orders_placed_total`. القاعدة: لا تكتب استعلامًا من مقال؛ اكتبه من أسماء المقاييس الفعلية عندك."},

        # ── 5) التنصيب
        {"type": "heading", "level": 2, "text": "⑤ التنصيب: محلي · Kubernetes · مُدار"},
        {"type": "code", "lang": "bash", "title": "observability/setup.sh — ثلاثة مسارات", "filename": "observability/setup.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

# ═══ المسار أ) محلي بـDocker Compose (الأسرع) ═══
docker compose -f docker-compose.observability.yml up -d
# التطبيق:
#   OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
#   (أو /metrics مع scrape من prometheus.yml)
curl -s http://localhost:9090/-/ready && echo " ✓ Prometheus"
curl -s -o /dev/null -w "Grafana: %{http_code}\n" http://localhost:3000/login

# تحقق إن المقاييس وصلت:
curl -s "http://localhost:9090/api/v1/label/__name__/values" | tr ',' '\n' | grep -c http_server || echo "لا مقاييس HTTP بعد"
# وأشهر الأسماء الفعلية عندك (مهم قبل ما تكتب لوحة):
curl -s "http://localhost:9090/api/v1/label/__name__/values" | tr ',' '\n' | grep -E "dotnet|http_server" | head -n 20

# ═══ المسار ب) Kubernetes (kube-prometheus-stack أو Operator) ═══
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword="$(openssl rand -hex 16)"
# ServiceMonitor لخدماتك:
#   kubectl apply -f observability/k8s/service-monitor.yaml
# وتحقق من الأهداف:  kubectl -n monitoring port-forward svc/monitoring-prometheus 9090

# ═══ المسار ج) مُدار (بلا تشغيل TSDB) ═══
# Azure Monitor Managed Prometheus:
az monitor metrics list --resource "$(az containerapp show -n orders -g rg-shop-prod --query id -o tsv)" \
  --interval PT1M --output table 2>/dev/null || echo "راجع صفحة Metrics في الـPortal"
# الربط بـGrafana: أضف Azure Monitor كـdatasource (Managed Identity — بلا مفاتيح).
# أو remote write لخدمة متوافقة مع Prometheus من الـCollector.

# ═══ فحص صحة المراقبة نفسها (لا تنساه) ═══
curl -s http://localhost:9090/api/v1/targets | python3 -c \
  'import json,sys; d=json.load(sys.stdin); [print(t["labels"].get("job"), t["health"], t.get("lastError","")) for t in d["data"]["activeTargets"]]'
curl -s "http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series" | head -c 300; echo
'''},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق بين pull/scrape وpush/OTLP وإمتى أختار كل واحد.",
            "أقدر أكتب استعلامات RED الثلاثة صح (rate · نسبة الأخطاء · histogram_quantile مع `sum by (le)`).",
            "أعرف أستخدم recording rules لتعريف واحد يُستخدم في اللوحة والتنبيه.",
            "أقدر أصمم لوحة مرتبة على الأسئلة (مشكلة؟ أين؟ موارد؟ طوابير؟ أعمال؟ إيه اتغير؟).",
            "أعرف مقاييس runtime في .NET وأفسر كل واحد (GC · thread pool · exceptions · timer).",
            "أقدر أضيف annotations للنشر من `deployments.log` وأربطها بالرسوم.",
            "أعرف الست أخطاء اللي بتخلي الأرقام غلط وأكتشفها (خصوصًا الأسماء القديمة للـruntime).",
            "أقدر أتحقق من صحة المراقبة نفسها (targets · head_series · churn).",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على PromQL واللوحات.",
         "questions": [
             {"q": "`histogram_quantile(0.95, rate(http_server_request_duration_seconds_bucket[5m]))` بيرجع NaN أو قيم غريبة. السبب الأشهر؟",
              "options": ["النافذة قصيرة", "**ناقصة `sum by (le)`** — الـ`le` (حد الـbucket) لازم يُحفظ في التجميع عشان التقدير يشتغل", "المقياس gauge", "الـscrape interval كبير"],
              "answer": 1,
              "explain": "الصيغة: `histogram_quantile(0.95, sum by (service, http_route, le) (rate(..._bucket[5m])))`. وأي تجميع بيعمل `sum` لازم يحتفظ بـ`le`."},
             {"q": "p99 الحقيقي 4 ثوانٍ لكن اللوحة بتقول 1.2 ثانية. ليه؟",
              "options": ["rate غلط", "**حدود الـbuckets ما بتغطيش النطاق**: أعلى bucket أقل من 4s فالتقدير بيتشبّع عند الحد → اضبط Boundaries (7.1.2)", "الـlabels غلط", "Grafana بيخطئ"],
              "answer": 1,
              "explain": "الـhistogram بيقدّر داخل الـbuckets. لو كل الطلبات البطيئة فوق أعلى bucket، النتيجة هتكون قريبة من الحد الأقصى. الحل: حدود تغطي نطاقك الحقيقي (حتى 10s أو 30s لو فيه عمليات طويلة)."},
             {"q": "ليه `rate()` على counter وليس القيمة الخام؟",
              "options": ["أسرع", "**لأن العدّاد بيتصفّر عند إعادة التشغيل، و`rate` بيتعامل مع إعادة الضبط ويحول المجموع التراكمي لمعدل في الثانية**", "أدق", "بيقلل السلاسل"],
              "answer": 1,
              "explain": "قراءة العدّاد الخام بلا معنى بعد restart. و`rate` تحتاج نافذة ≥ 4× فترة الـscrape (وإلا هترجع NaN بعد restart)."},
             {"q": "لوحة .NET runtime فاضية تمامًا رغم إن المقاييس بتصدر. السبب الأشهر؟",
              "options": ["Grafana", "**أسماء المقاييس اختلفت بين إصدارات instrumentation (`process_runtime_dotnet_*` مقابل `dotnet_*`)**", "الـsampling", "الـCollector"],
              "answer": 1,
              "explain": "اطبع الأسماء الفعلية أولًا: `count by (__name__)({__name__=~\".+\"})` أو من `/api/v1/label/__name__/values`. القاعدة: لا تكتب لوحة من مقال — اكتبها من مخرجاتك."},
             {"q": "إيه فايدة recording rules؟",
              "options": ["تقليل عدد المقاييس", "**تعريف واحد محسوب مسبقًا يُستخدم في اللوحات والتنبيهات: أسرع، وأدق (لا اختلاف بين استعلام اللوحة واستعلام التنبيه)، وأسهل صيانة**", "بديل للـscrape", "تقليل الـcardinality"],
              "answer": 1,
              "explain": "القاعدة الذهبية: أي استعلام مستخدم في مكانين أو أكتر يبقى recording rule (مثلًا `job:http_errors:ratio_rate5m`). وكمان بتقلل الحمل وقت الاستعلام لأنها محسوبة."},
             {"q": "annotations للنشر على اللوحة — ليه مهمة؟",
              "options": ["جمالية", "**بدونها بتشوف تغيرًا في الرسم من غير ما تعرف سببه؛ الربط بين «ارتفاع p95» و«نشر قبل 3 دقائق» بيختصر التشخيص من دقائق لثوانٍ**", "بتقلل التنبيهات", "بتحسن الأداء"],
              "answer": 1,
              "explain": "أغلب التغيرات في الإنتاج سببها تغيير (نشر/إعداد/بنية). سجّل النشر من `deployments.log` (6.3.5) كمصدر للـannotations."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "لوحة تجاوب + تنبيهات تعمل.",
         "items": [
             {"id": "t1", "title": "مهمة 1: لوحة RED + USE لخدمتين (مصممة على الأسئلة)",
              "md": "**السياق:** عندك مقاييس بتصدر (من 7.1.2) ومحتاج لوحة تُستخدم فعلًا وقت الحادث.\n\n**المطلوب:**\n1. `observability/prometheus.yml` + `rules.yml` بـ**recording rules** لـrate وerror ratio وp95/p99 وSLI، وتنبيهين على الأقل (ServiceDown بـ`absent` · QueueLag).\n2. لوحة Grafana (JSON مُصدَّر من الـUI ومرفوع للمستودع) فيها **6 صفوف مرتبة حسب الأسئلة** من جدول الدرس، مع متغيرين (`service`, `route`) ووحدات صحيحة (`percentunit`, `s`, `bytes`, `reqps`).\n3. **annotations للنشر**: مصدر (ملف/ـAPI) يضيف خطًا عند كل نشر من `deployments.log`.\n4. صف runtime لـ.NET: GC heap حسب الجيل · thread pool queue · أشهر 5 استثناءات (جدول).\n5. **تحقق من الأسماء الفعلية أولًا**: اطبع قائمة أسماء المقاييس من Prometheus وأرفقها في `docs/metrics-inventory.md` مع معنى كل واحد ووحدة كل واحد والسمات المسموحة.\n6. **اختبار اللوحة تحت حمل**: شغّل k6 (50 VU / دقيقتين) وأثبت إن اللوحة بتوضح: ارتفاع rate · ارتفاع p95 · تغير GC · (ولو حقنت عطلًا) ارتفاع نسبة 5xx — مع لقطات.\n7. `docs/dashboard-guide.md`: إزاي أقرأ اللوحة في 30 ثانية (ترتيب النظر) + إيه اللي يعمله كل رقم غير طبيعي.",
              "criteria": [
                  "recording rules لأربعة استعلامات على الأقل + تنبيهين بـ`for` و`annotations` فيها رابط runbook.",
                  "اللوحة فيها 6 صفوف مرتبة حسب الأسئلة (مش مقاييس مبعثرة) + متغيرات + وحدات صحيحة.",
                  "كل لوحة p95/p99 بتستخدم `sum by (… , le)` (يُتحقق من الاستعلام).",
                  "annotations للنشر شغالة (خطوط ظاهرة على الرسم مع الإصدار).",
                  "صف runtime بثلاث لوحات على الأقل (GC · thread pool · exceptions).",
                  "`docs/metrics-inventory.md` بأسماء **فعلية** مأخوذة من Prometheus (مش من مقال) + وحدة وسمات لكل مقياس.",
                  "اختبار تحت حمل بلقطات تُظهر التغيرات الأربعة.",
                  "دليل قراءة اللوحة في 30 ثانية (ترتيب النظر + معنى كل شذوذ).",
              ],
              "hint": "أول شيء تعمله بعد ما توصل المقاييس: `curl -s 'http://localhost:9090/api/v1/label/__name__/values'` واقرأ الأسماء الحقيقية — ده بيوفر ساعات من لوحات فاضية. ولو `dotnet_*` مش موجودة، تأكد إن `AddRuntimeInstrumentation()` مُضاف وإن الـMeter مُسجل بـ`AddMeter`. وللـprovisioning التلقائي في Grafana: ملفات `datasources/*.yaml` و`dashboards/*.yaml` في مجلد الـprovisioning.",
              "solution": "الترتيب: (1) اطبع أسماء المقاييس الفعلية (2) اكتب recording rules (3) ابنِ اللوحة من أعلى (الأعراض) لأسفل (التفاصيل) (4) أضف annotations من `deployments.log` (5) اختبر تحت حمل. النتيجة النموذجية: صف 1 بثلاث `stat` panels (نسبة 5xx بلون عند 0.5% و1% · p95 · rate)، صف 2 timeseries مقسمة على المسارات، صف 3 runtime، صف 4 طوابير، صف 5 أعمال مقابل أمس، صف 6 جدول استثناءات. تحت k6 بـ50 VU: rate من ~5 لـ~200 req/s · p95 من 40ms لـ250ms · GC gen0 collections بتزيد · thread pool queue يظهر لحظيًا. أهم درس: اللوحة اللي مبتبدأش بسؤال «هل فيه مشكلة؟» بتبقى أرشيف مش أداة تشخيص.",
              "resources": [
                  "https://prometheus.io/docs/prometheus/latest/querying/basics/",
                  "https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/",
                  "https://grafana.com/docs/grafana/latest/dashboards/",
                  "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/built-in-metrics-runtime",
                  "https://opentelemetry.io/docs/specs/semconv/http/http-metrics/",
                  "https://k6.io/docs/",
              ]},
             {"id": "t2", "title": "مهمة 2: صحة المراقبة نفسها + تقليل cardinality",
              "md": "**السياق:** المراقبة شغالة، بس محتاج تتأكد إنها هتفضل شغالة لما النظام يكبر.\n\n**المطلوب:**\n1. **جرد التكلفة**: كم سلسلة زمنية نشطة (`prometheus_tsdb_head_series`) · أعلى 10 مقاييس بعدد السلاسل · معدل إنشاء السلاسل (churn) · حجم التخزين ومدة الاحتفاظ.\n2. **اكتشف الانفجار**: لو فيه مقياس بأكثر من 1,000 سلسلة، حدد السمة المسؤولة واصلحها (قَوْلبة مسار · إزالة معرّف · `TagKeys`/`CardinalityLimit`) وقِس الفرق.\n3. **راقب المراقبة**: لوحة صغيرة فيها `prometheus_tsdb_head_series` · `rate(prometheus_tsdb_head_series_created_total[5m])` · `prometheus_target_sync_length_seconds` · `otelcol_refused_metric_points` · أهداف بحالة `down` — وتنبيه لو أي واحدة شذّت.\n4. **تنبيهات بلا ضجيج**: راجع كل التنبيهات الحالية وصنّفها (page/ticket/لا) + أضف `for` مناسب + grouping/inhibition في Alertmanager (تنبيه واحد لكل حادث مش 20) + رابط runbook في كل annotation.\n5. **اختبار التنبيه**: حقن عطل متعمد (إيقاف خدمة · رفع معدل أخطاء) وثبّت إن التنبيه وصل بالشكل الصح (مجمّع، فيه runbook، واختفى بعد الإصلاح خلال مدة معقولة).\n6. `docs/alerting-review.md`: جدول التنبيهات (الاسم · الشرط · `for` · severity · page/ticket · runbook · آخر مرة اشتغل) + قرار لكل تنبيه: إبقاء/تعديل/حذف + **عدد التنبيهات قبل وبعد**.",
              "criteria": [
                  "أرقام حقيقية: سلاسل نشطة · أعلى 10 مقاييس · churn · حجم التخزين.",
                  "إصلاح cardinality واحد على الأقل مقيس قبل/بعد (ولو ما كان فيه مشكلة، وثّق الفحص).",
                  "لوحة لصحة المراقبة بخمس مقاييس على الأقل + تنبيه عليها.",
                  "مراجعة تنبيهات بتصنيف page/ticket + `for` + grouping/inhibition في Alertmanager.",
                  "كل تنبيه فيه رابط runbook في الـannotations.",
                  "اختبار تنبيه متعمد: وصل مجمّعًا واختفى بعد الإصلاح (موثق بالأزمنة).",
                  "جدول مراجعة فيه قرار لكل تنبيه (إبقاء/تعديل/حذف) وعدد قبل/بعد.",
                  "ملاحظة عن المقايضة: تقليل cardinality مقابل فقدان تفاصيل، وكيف تعوضها بالسجلات/الـtraces.",
              ],
              "hint": "لإيجاد السمة المسؤولة عن الانفجار: `topk(10, count by (__name__, job) ({__name__=~\".+\"}))` ثم لمقياس معين: `count by (http_route) (http_server_request_duration_seconds_count)` — لو القيم مسارات كاملة بدل قوالب، فالمشكلة في الـrouting match أو في السمة. وللـgrouping في Alertmanager: `group_by: ['alertname','service']` مع `group_wait: 30s` و`group_interval: 5m` و`repeat_interval: 4h`.",
              "solution": "النتائج النموذجية: `head_series` ~5,000–20,000 لمشروع صغير؛ أعلى المقاييس عادةً `http_server_request_duration_seconds_bucket` (لأن كل bucket سلسلة) — وده طبيعي ما دامت المسارات مُقَوْلبة. الإصلاح الأشهر: مسار غير مُقَوْلَب (مثلًا `/orders/123`) بيوصل لآلاف السلاسل → `TagKeys` يسمح فقط بـ`http.route` أو ضبط الـrouting. لوحة صحة المراقبة: `head_series` (نمو) · `created_total` rate (churn) · `otelcol_refused_metric_points` (فقدان) · عدد الأهداف `down` · زمن الاحتفاظ/الحجم. مراجعة التنبيهات نموذجيًا بتقلل العدد من 15–20 لـ5–7 (page: ServiceDown · HighErrorRate/SLO burn · QueueLag · شهادة TLS قاربت الانتهاء؛ ticket: p95 مرتفع · موارد قربت الحد)، مع grouping بيخلي الحادث = تنبيه واحد. اختبار التنبيه: إيقاف الخدمة → `ServiceDown` بعد دقيقتين (`for: 2m`) → إرجاعها → اختفاء خلال ~3 دقائق.",
              "resources": [
                  "https://prometheus.io/docs/prometheus/latest/querying/basics/",
                  "https://prometheus.io/docs/alerting/latest/alertmanager/",
                  "https://prometheus.io/docs/practices/naming/",
                  "https://grafana.com/blog/2020/05/18/when-to-use-recording-rules/",
                  "https://opentelemetry.io/docs/collector/internal-telemetry/",
                  "https://sre.google/workbook/alerting-on-slos/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Prometheus: أساسيات الاستعلام", "url": "https://prometheus.io/docs/prometheus/latest/querying/basics/"},
            {"label": "Prometheus: Histograms والـsummaries", "url": "https://prometheus.io/docs/concepts/metric_types/#histogram"},
            {"label": "Prometheus: recording rules", "url": "https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/"},
            {"label": "Alertmanager: التجميع والكبت", "url": "https://prometheus.io/docs/alerting/latest/alertmanager/"},
            {"label": "مقاييس runtime المدمجة في .NET", "url": "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/built-in-metrics-runtime"},
            {"label": "اتفاقيات OTel لمقاييس HTTP", "url": "https://opentelemetry.io/docs/specs/semconv/http/http-metrics/"},
            {"label": "Grafana: اللوحات والـprovisioning", "url": "https://grafana.com/docs/grafana/latest/dashboards/"},
            {"label": "kube-prometheus-stack", "url": "https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack"},
        ]},
    ],
}

LESSONS_S7_B = [_L3, _L4]
