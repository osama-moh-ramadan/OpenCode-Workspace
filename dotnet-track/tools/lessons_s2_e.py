"""Stage 2, Module 3 — Realtime & background work (lessons 3-4 of 4)."""

TODAY = "2026-10-22"

LESSONS_S2_E = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s2-m3-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
«شغل في الخلفية» حاجة و«جدولة» حاجة تانية. الجدولة محتاجة أربع حاجات الـ`BackgroundService`
ما بيديهاش لوحده: **دوام** (المهمة تتنفذ حتى لو التطبيق اتعاد تشغيله)، **رؤية** (لوحة تقولك إيه اللي فشل وإمتى)،
**إعادة محاولة** (retry/backoff/dead-letter)، و**منع التكرار** (نسخ متعددة ما تنفذهاش مرتين).

الدرس ده: مقارنة عملية بين Hangfire وQuartz.NET والقناة الداخلية وK8s CronJob،
وتنفيذ cron job قابل للمراقبة و**idempotent** — لأن التسليم «مرة واحدة بالظبط» وهم؛ الواقع at-least-once.
"""},
            {"type": "terms", "items": [
                {"term": "Cron expression", "def": "صيغة جدولة: `*/5 * * * *` (كل 5 دقائق)، `0 2 * * *` (2:00 يوميًا). راجع ترتيب الحقول — يختلف بين الأدوات."},
                {"term": "Recurring Job", "def": "مهمة متكررة محفوظة في مخزن دائم (Hangfire) أو مجدولة بمشغّل (Quartz)."},
                {"term": "Persistent Store", "def": "قاعدة بيانات تحفظ المهام وحالتها → تنجو من إعادة التشغيل وتمكّن الـclustering."},
                {"term": "Misfire", "def": "الموعد فات والخادم كان واقع. السياسة: نفّذ فورًا، تجاهل، أو نفّذ مرة واحدة — قرار لازم يتاخد صراحة."},
                {"term": "At-least-once", "def": "المهمة ممكن تتنفذ أكتر من مرة. المقابل: معالج idempotent."},
                {"term": "Idempotency Key", "def": "مفتاح فريد للتنفيذ (اسم المهمة + وقت الجدولة) بـunique index يمنع التكرار."},
                {"term": "`[DisableConcurrentExecution]` / `[DisallowConcurrentExecution]`", "def": "منع تداخل تشغيلين لنفس المهمة (Hangfire / Quartz)."},
                {"term": "Dead Letter", "def": "مكان المهام اللي فشلت بعد كل المحاولات — للمراجعة اليدوية بدل الضياع الصامت."},
            ]},
            {"type": "table", "head": ["المعيار", "Channel + BackgroundService", "Hangfire", "Quartz.NET", "Queue (MassTransit)", "K8s CronJob"], "rows": [
                ["الدوام بعد إعادة التشغيل", "✗ (في الذاكرة)", "✓ قاعدة بيانات", "✓ (persistent store)", "✓ الوسيط", "✓ (خارج التطبيق)"],
                ["لوحة تحكم/رؤية", "✗", "✓ Dashboard ممتاز", "جزئي (تحتاج أدوات)", "✓ إدارة الوسيط", "kubectl/logs"],
                ["إعادة المحاولة/Backoff", "يدوي", "✓ مدمج + DLQ", "يدوي/مكتبات", "✓ مدمج قوي", "restart policy"],
                ["Cron", "✗ (دوري بسيط)", "✓", "✓ + مناطق زمنية + misfire", "✗ (مش دوره)", "✓"],
                ["Clustering / منع التكرار", "✗", "✓ (خوادم متعددة)", "✓ (JDBC store)", "✓ (منافسة مستهلكين)", "✓ (تشغيل واحد)"],
                ["فصل الموارد عن الـAPI", "✗", "✗/✓ (خادم منفصل ممكن)", "✗", "✓", "✓"],
                ["التكلفة التشغيلية", "الأقل", "منخفضة (جدول DB)", "متوسطة", "أعلى (وسيط)", "متوسطة"],
                ["أنسب حالة", "شغل ناتج عن طلب، غير حرج", "مهام دورية داخل تطبيق .NET مع رؤية", "جدولة معقدة/مناطق زمنية/مجموعات", "رسائل وأحداث بين الخدمات", "مهام ثقيلة ليلية/تقارير"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قاعدة الاختيار",
             "md": """
- مهام دورية **داخل تطبيقك** ومحتاجة لوحة تحكم وإعادة محاولة → **Hangfire** (أسرع طريق لقيمة حقيقية).
- جدولة معقدة: مناطق زمنية، تقويمات، misfire policies، مجموعات مهام → **Quartz.NET**.
- أحداث ورسائل **بين الخدمات** وتحميل متغيّر → **MassTransit + RabbitMQ/Service Bus**.
- مهمة ثقيلة/نادرة وماينفعش تنافس الـAPI على الموارد → **K8s CronJob** أو خدمة منفصلة.
- شغل ناتج عن طلب وغير حرج وقابل لإعادة التوليد → **Channel** من الدرس السابق (بلا بنية إضافية).
"""},
            {"type": "heading", "level": 2, "text": "Hangfire: أسرع طريق لمهام دورية مرئية"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Hangfire.AspNetCore
dotnet add Shop.Api package Hangfire.PostgreSql        # أو Hangfire.SqlServer
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Jobs/HangfireSetup.cs", "title": "الإعداد + Dashboard محمي + مهام متكررة", "code": r'''
using Hangfire;
using Hangfire.PostgreSql;

public static class HangfireSetup
{
    public static IServiceCollection AddJobScheduler(
        this IServiceCollection services, IConfiguration config, IWebHostEnvironment env)
    {
        services.AddHangfire(options => options
            .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
            .UseSimpleAssemblyNameTypeSerializer()
            .UseRecommendedSerializerSettings()
            .UsePostgreSqlStorage(c => c.UseNpgsqlConnection(config.GetConnectionString("Hangfire")!))
            // ✓ إعادة المحاولة: عدد محاولات + backoff أسي
            // ✗ لا تبتلع الفشل بعد استنفاد المحاولات — AttemptsExceededAction.Fail يخليه ظاهر في اللوحة
            .UseFilter(new AutomaticRetryAttribute
            {
                Attempts = 3,
                BackoffStrategy = BackoffStrategy.Exponential,
                OnAttemptsExceeded = AttemptsExceededAction.Fail,
            }));

        services.AddHangfireServer(options =>
        {
            options.WorkerCount = Environment.ProcessorCount * 2;
            options.Queues = ["default", "reports"];               // طوابير بأولويات مختلفة
        });

        return services;
    }

    public static IApplicationBuilder UseJobDashboard(this IApplicationBuilder app, IWebHostEnvironment env)
    {
        // ★ لوحة Hangfire فيها أسماء المهام والبيانات — لا تعرضها عامًا أبدًا
        app.UseHangfireDashboard("/hangfire", new DashboardOptions
        {
            Authorization = [new AdminOnlyDashboardFilter()],
            DisplayStorageConnectionString = false,               // لا تسرّب connection string
            StatsPollingInterval = 10_000,
        });
        return app;
    }
}

public sealed class AdminOnlyDashboardFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var http = context.GetHttpContext();
        // ✓ مصادقة حقيقية: سياسة admin، وشبكة داخلية في الإنتاج
        return http.User.Identity?.IsAuthenticated == true
            && http.User.IsInRole(Roles.Admin)
            && !context.GetHttpContext().Request.Headers.ContainsKey("X-Forwarded-For");
    }
}

/// <summary>المهام فئات عادية — تُختبر كأي كلاس، وتستدعي الـApplication layer.</summary>
public sealed class AbandonedOrdersJob(IOrderService orders, ILogger<AbandonedOrdersJob> log)
{
    // ★ منع التداخل: لو دورة أخدت أطول من 5 دقائق، الدورة الجاية تنتظر ولا تتداخل
    [DisableConcurrentExecution(timeoutInSeconds: 120)]
    public async Task RunAsync(CancellationToken ct)
    {
        var result = await orders.SweepAbandonedAsync(batchSize: 100, ct);
        log.LogInformation("abandoned sweep: {Cancelled} cancelled", result.Cancelled);
    }
}

public sealed class NightlyReportJob(ISender sender, ILogger<NightlyReportJob> log)
{
    /// <summary>
    /// ★ المهمة «مجدول» فقط؛ المنطق في handler MediatR — نفس الكود اللي بيخدم الـAPI،
    /// وبنفس الاختبارات. ده معنى «MediatR jobs»: الجدولة توصيل، والمنطق مكانه في الـhandlers.
    /// </summary>
    public async Task RunAsync(DateOnly day, CancellationToken ct)
    {
        await sender.Send(new GenerateDailySalesReportCommand(day), ct);
        log.LogInformation("daily sales report queued for {Day}", day);
    }
}

// التسجيل (مرة واحدة عند الإقلاع — AddOrUpdate idempotent بحسب الاسم)
public static class JobRegistration
{
    public static void RegisterRecurringJobs()
    {
        RecurringJob.AddOrUpdate<AbandonedOrdersJob>(
            "sweep-abandoned-orders",
            job => job.RunAsync(CancellationToken.None),
            "*/5 * * * *",                                     // كل 5 دقائق
            new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc, MisfireHandling = MisfireHandlingMode.FireAndForget });

        RecurringJob.AddOrUpdate<NightlyReportJob>(
            "nightly-sales-report",
            job => job.RunAsync(DateOnly.FromDateTime(DateTime.UtcNow.AddDays(-1)), CancellationToken.None),
            "0 2 * * *",                                       // 02:00 UTC يوميًا
            new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc, Queue = "reports" });
    }
}
// تُنادى بعد app.Build() — أو من hosted service صغير للتسجيل الآمن
'''},
            {"type": "heading", "level": 2, "text": "Quartz.NET: جدولة معقدة ومناطق زمنية"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Quartz.Extensions.Hosting
dotnet add Shop.Api package Quartz.Extensions.DependencyInjection
dotnet add Shop.Api package Quartz.Serialization.SystemTextJson
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Jobs/QuartzSetup.cs", "title": "Persistent store + misfire policy + منطقة زمنية", "code": r'''
using Quartz;

public sealed class DailyReportJob(ISender sender) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        var day = DateOnly.FromDateTime(context.FireTimeUtc.AddDays(-1).UtcDateTime);
        await sender.Send(new GenerateDailySalesReportCommand(day), context.CancellationToken);
    }
}

public static IServiceCollection AddQuartzScheduler(this IServiceCollection services, IConfiguration config)
{
    services.AddQuartz(q =>
    {
        // للتطوير المحلي فقط: q.UseInMemoryStore();
        q.UsePersistentStore(s =>                    // ★ الدوام = نجاة من إعادة التشغيل + clustering
        {
            s.UseProperties = true;
            s.UsePostgres(o => o.ConnectionString = config.GetConnectionString("Quartz")!);
            s.UseJsonSerializer();
            s.UseClustering(c =>                     // نسخ متعددة: واحدة فقط تنفّذ المهمة
            {
                c.CheckinMisfireThreshold = TimeSpan.FromSeconds(20);
                c.CheckinInterval = TimeSpan.FromSeconds(10);
            });
        });

        var tz = TimeZoneInfo.FindSystemZoneById("Africa/Cairo");   // ✓ صريح: لا تعتمد على منطقة الخادم

        q.ScheduleJob<DailyReportJob>(trigger => trigger
            .WithIdentity("daily-report")
            .WithCronSchedule("0 2 * * *", s => s
                .InTimeZone(tz)
                // ★ السياسة: لو الموعد فات والخادم واقع — تجاهل ولا تنفّذ متأخرًا بلا حدود
                .WithMisfireHandlingInstructionDoNothing())
            .StartNow());
    });

    services.AddQuartzHostedService(options =>
    {
        options.WaitForJobsToComplete = true;        // ✓ إيقاف لطيف: كمّل الشغل الجاري
        options.AwaitStartup = true;
    });

    return services;
}

/// <summary>منع تداخل تشغيلين لنفس المهمة — ضروري لو التنفيذ أطول من الفترة.</summary>
[DisallowConcurrentExecution]
[PersistJobDataAfterExecution]
public sealed class StockSyncJob(IProductCatalog catalog) : IJob
{
    public async Task Execute(IJobExecutionContext context) =>
        await catalog.SyncStockAsync(context.CancellationToken);
}
'''},
            {"type": "callout", "kind": "warn", "title": "منطقة زمنية وDST: الباج اللي بيظهر مرتين في السنة",
             "md": """
- **خزّن الجدولة بمنطقة زمنية صريحة** (`InTimeZone(tz)` / `RecurringJobOptions.TimeZone`). الاعتماد على منطقة الخادم = سلوك مختلف بين جهازك والإنتاج.
- **تغيير التوقيت الصيفي**: مهمة «2:30 صباحًا» قد **لا تُنفَّذ** (الساعة قفزت) أو **تُنفَّذ مرتين** (الساعة رجعت). حدد سياسة misfire واختبرها.
- **مناطق زمنية غير مثبتة في الحاوية**: صور Alpine/Linux النحيفة أحيانًا بلا قاعدة بيانات tz. الحل: `tzdata` في الصورة، أو خزّن UTC وحول في التطبيق.
- **أعمدة التواريخ**: خزّن `timestamptz`/UTC دائمًا، وحوّل للعرض فقط.
"""},
            {"type": "heading", "level": 2, "text": "Idempotency: لأن التنفيذ هيتكرر"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Jobs/JobExecutionLog.cs", "title": "مفتاح تنفيذ فريد يمنع التكرار حتى مع at-least-once", "code": r'''
public sealed class JobExecutionLog
{
    public Guid Id { get; init; } = Guid.NewGuid();
    /// <summary>«nightly-sales-report|2026-10-21» — مفتاح منطقي للتنفيذ المقصود.</summary>
    public required string ExecutionKey { get; init; }
    public required DateTimeOffset StartedAt { get; init; }
    public DateTimeOffset? CompletedAt { get; init; }
    public required string Status { get; init; }          // running | done | failed
    public string? Error { get; init; }
}

public sealed class IdempotentJobRunner(AppDbContext db, ILogger<IdempotentJobRunner> log)
{
    /// <summary>
    /// يحجز التنفيذ بـunique index: لو حد تاني حجزه، نخرج بهدوء.
    /// ده بيحل التكرار من: نسختين، إعادة محاولة بعد timeout، أو misfire.
    /// </summary>
    public async Task<bool> RunOnceAsync(string executionKey, Func<CancellationToken, Task> work, CancellationToken ct)
    {
        var attempt = new JobExecutionLog
        {
            ExecutionKey = executionKey,
            StartedAt = DateTimeOffset.UtcNow,
            Status = "running",
        };

        try { db.JobExecutionLogs.Add(attempt); await db.SaveChangesAsync(ct); }
        catch (DbUpdateException)                       // unique violation → تنفيذ تاني سبقنا
        {
            log.LogInformation("job {Key} already claimed by another run", executionKey);
            return false;
        }

        try
        {
            await work(ct);
            attempt.CompletedAt = DateTimeOffset.UtcNow;
            attempt.Status = "done";
        }
        catch (Exception ex)
        {
            attempt.Status = "failed";
            attempt.Error = ex.Message;                 // موجز — التفاصيل في اللوجات
            await db.SaveChangesAsync(ct);
            throw;                                      // خلّي المجدول يعيد المحاولة بحسب سياسته
        }

        await db.SaveChangesAsync(ct);
        return true;
    }
}

// الاستخدام داخل المهمة
public async Task RunAsync(DateOnly day, CancellationToken ct)
{
    var key = $"nightly-sales-report|{day:yyyy-MM-dd}";
    await runner.RunOnceAsync(key, token => sender.Send(new GenerateDailySalesReportCommand(day), token), ct);
}
'''},
            {"type": "code", "lang": "sql", "title": "الـunique index اللي بيخلي الحجز فعالًا", "code": r'''
CREATE UNIQUE INDEX ux_job_execution_key ON job_execution_logs (execution_key);
CREATE INDEX ix_job_executions_started ON job_execution_logs (started_at DESC);
'''},
            {"type": "heading", "level": 2, "text": "المراقبة: مهمة من غير قياس = مهمة ميتة بصمت"},
            {"type": "code", "lang": "csharp", "title": "قياس + health check «المهمة اشتغلت من وقت قريب»", "code": r'''
public static class JobMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter =
        new("Shop.Api.jobs", version: "1.0.0");

    public static readonly UpDownCounter<int> Running =
        Meter.CreateUpDownCounter<int>("jobs.running", description: "المهام الجارية");
    public static readonly Counter<int> Completed =
        Meter.CreateCounter<int>("jobs.completed", description: "المهام المنتهية");
    public static readonly Counter<int> Failed =
        Meter.CreateCounter<int>("jobs.failed", description: "المهام الفاشلة");
    public static readonly Histogram<double> Duration =
        Meter.CreateHistogram<double>("jobs.duration", unit: "s");
}

/// <summary>
/// فحص «المهمة اشتغلت بنجاح خلال النافذة المتوقعة» — أهم من فحص «المهمة موجودة».
/// مهمّة بتفشل بصمت أسبوع = باج إنتاجي لا يكتشفه أحد.
/// </summary>
public sealed class JobFreshnessHealthCheck(AppDbContext db) : IHealthCheck
{
    private static readonly Dictionary<string, TimeSpan> Expectations = new()
    {
        ["sweep-abandoned-orders"] = TimeSpan.FromMinutes(20),      // 4 أضعاف الفترة
        ["nightly-sales-report"] = TimeSpan.FromHours(30),
    };

    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct)
    {
        var now = DateTimeOffset.UtcNow;
        var stale = new List<string>();

        foreach (var (key, window) in Expectations)
        {
            var last = await db.JobExecutionLogs
                .Where(l => l.ExecutionKey.StartsWith(key) && l.Status == "done")
                .OrderByDescending(l => l.CompletedAt)
                .Select(l => l.CompletedAt)
                .FirstOrDefaultAsync(ct);

            if (last is null || now - last.Value > window) stale.Add(key);
        }

        return stale.Count == 0
            ? HealthCheckResult.Healthy("كل المهام الدورية اشتغلت في نافذتها")
            : HealthCheckResult.Unhealthy($"مهام متأخرة أو متوقفة: {string.Join(", ", stale)}");
    }
}
'''},
            {"type": "callout", "kind": "danger", "title": "أخطاء الجدولة الشائعة",
             "md": """
- **مهمة أطول من الفترة بدون `[DisallowConcurrentExecution]`** → تداخل وتعارضات على نفس الصفوف.
- **ابتلاع الاستثناء داخل المهمة** → المجدول يفتكر إنها نجحت، ومفيش إعادة محاولة ولا تنبيه. سجّل وارمِ.
- **مهمة بتشتغل على كل الصفوف بلا حدود** → قفل جداول وتأثير على الإنتاج. خد دفعات (`Take(100)`) وحلقة.
- **Dashboard مكشوف** → أسماء مهام وبيانات وأحيانًا connection strings. خلف admin + شبكة داخلية.
- **الاعتماد على «once» من غير مفتاح تنفيذ** → أي إعادة تشغيل/إعادة محاولة = تنفيذ مكرر (شحن مرتين، تقريرين).
- **منطقة زمنية الخادم** → سلوك مختلف بين البيئات. حدد tz صراحة.
"""},
            {"type": "checkpoints", "items": [
                "أختار أداة الجدولة بمعيار الدوام والرؤية وإعادة المحاولة ومنع التكرار.",
                "أنفّذ cron job بمخزن دائم وmisfire policy ومنطقة زمنية صريحة ومنع تداخل.",
                "أجعل التنفيذ idempotent بمفتاح تنفيذ فريد (at-least-once + معالج آمن).",
                "أقيس المهام وأضيف health check لحداثها، وأحمي لوحة التحكم.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "«exactly-once delivery» في الجدولة — إيه الحقيقة العملية؟",
                 "options": [
                     "متاح لو استخدمت Hangfire",
                     "وهم عمليًا: التسليم at-least-once + معالج idempotent هو الحل الصحيح",
                     "متاح في Quartz",
                     "يحتاج Kafka فقط",
                 ], "answer": 1,
                 "explain": "أي نظام موزع ممكن يكرر التنفيذ (timeout، إعادة محاولة، misfire، نسختين). الحماية في المعالج: مفتاح تنفيذ فريد."},
                {"q": "مهمة بتاخد 7 دقائق ومجدولة كل 5 دقائق. إيه اللي لازم تعمله؟",
                 "options": [
                     "تقلل الفترة",
                     "تمنع التداخل (`DisableConcurrentExecution`/`[DisallowConcurrentExecution]`) وتعيد النظر في الفترة أو تنقلها لطابور",
                     "تزيد عدد العمال",
                     "تحذف المهمة",
                 ], "answer": 1,
                 "explain": "بدون منع التداخل هيحصل تضارب على نفس البيانات. وبعدها اسأل: هل الفترة منطقية أصلًا؟"},
                {"q": "إيه فايدة `WithMisfireHandlingInstructionDoNothing()`؟",
                 "options": [
                     "تسريع الجدولة",
                     "تحديد صريح للسلوك لما الموعد يفوت والخادم واقع (تجاهل بدل تنفيذ متأخر غير مقصود)",
                     "إلغاء المهمة",
                     "منع التكرار",
                 ], "answer": 1,
                 "explain": "من غير سياسة misfire، بعض الإعدادات بتنفّذ كل المواعيد الفائتة مرة واحدة — كارثة لمهمة زي «إرسال فواتير»."},
                {"q": "أهم health check لمهمة دورية؟",
                 "options": [
                     "إن الكلاس موجود",
                     "إن آخر تنفيذ ناجح كان داخل النافذة المتوقعة (freshness)",
                     "إن cron صحيح",
                     "إن الطابور فاضي",
                 ], "answer": 1,
                 "explain": "مهمة بتفشل بصمت لأسبوع لا يكتشفها أحد غير فحص الحداثة. ده أعلى قيمة مراقبة بتكلفة بسيطة."},
                {"q": "مهمة ليلية تقيلة بتأثر على زمن استجابة الـAPI. أفضل حل؟",
                 "options": [
                     "تقليل حجم الدفعة",
                     "نقلها لطابور/خادم منفصل أو K8s CronJob لعزل الموارد عن خدمة الـAPI",
                     "تشغيلها في وقت الذروة",
                     "إلغاؤها",
                 ], "answer": 1,
                 "explain": "عزل الموارد قرار معماري: الـAPI محتاج latency مستقر، والمهمة محتاجة throughput. لا يتنافسوا في نفس العملية."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "cron job إنتاجي",
                 "md": "اختار أداة (Hangfire أو Quartz) ونفّذ مهمتين: واحدة كل 5 دقائق والأخرى يومية بوقت محدد بمنطقة زمنية صريحة. أضف مخزنًا دائمًا، منع تداخل، إعادة محاولة، و`ExecutionKey` idempotent.",
                 "criteria": [
                     "إعادة تشغيل التطبيق لا تفقد الجدولة (المهام محفوظة في المخزن)",
                     "تشغيل المهمة يدويًا مرتين بنفس المفتاح → تنفيذ واحد فعلي (اختبار)",
                     "لوحة التحكم محمية بدور admin ولا تعرض connection string",
                     "قياسات (duration/success/failure) منشورة",
                     "health check «freshness» يفشل لو عطّلت المهمة (جرّب)",
                 ],
                 "hint": "لو المهمة بتتنفذ مرتين عند الإقلاع: راجع سياسة الـmisfire، وتأكد إن `AddOrUpdate` بيستخدم نفس الاسم الثابت في كل تشغيل."},
                {"id": "t2", "title": "مهمة عبر MediatR بدل كود مكرر",
                 "md": "حوّل منطق موجود (تقرير/مزامنة) إلى command/handler واحد يستخدمه الـAPI والمجدول، بحيث المهمة بقت «توصيل» فقط. واكتب اختبارًا للـhandler بلا أي مجدول.",
                 "criteria": [
                     "لا تكرار للمنطق بين endpoint والمهمة",
                     "اختبار handler مستقل عن أداة الجدولة",
                     "المهمة بتنادي `ISender.Send` بس (أقل من 10 أسطر)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Hangfire documentation", "url": "https://docs.hangfire.io/"},
                {"label": "Quartz.NET documentation", "url": "https://www.quartz-scheduler.net/"},
                {"label": "Quartz.NET tutorials (persistent store & clustering)", "url": "https://www.quartz-scheduler.net/documentation/quartz-3.x/tutorial/"},
                {"label": "MediatR", "url": "https://github.com/jbogard/MediatR"},
                {"label": "Enterprise Integration Patterns — Idempotent Receiver", "url": "https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s2-m3-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لما تطبيقك بينشر في Kubernetes أو behind load balancer، فيه سؤالان بسيطان بيحددا استقرار النظام:
**«هل العملية حية؟»** (liveness) و**«هل تقدر تستقبل شغل دلوقتي؟»** (readiness).

الخلط بينهم كارثة عملية: لو فحص الـliveness بيفحص قاعدة البيانات، أي بطء في القاعدة = إعادة تشغيل
لكل النسخ في نفس الوقت = **restart storm** وانقطاع كامل. الدرس ده بيعلمك الفصل الصحيح، والفحوصات
المفيدة، وإزاي تعرض الحالة بأمان.
"""},
            {"type": "terms", "items": [
                {"term": "Liveness", "def": "«العملية حية وغير معلّقة». فحص **رخيص وذاتي** — لا تبعيات خارجية. فشله = إعادة تشغيل."},
                {"term": "Readiness", "def": "«جاهز لاستقبال طلبات». يفحص التبعيات الحرجة. فشله = إزالة من الـload balancer (بدون إعادة تشغيل)."},
                {"term": "Startup", "def": "«خلص إقلاع؟» للمهام البطيئة (migrations، تحميل كاش). يحمي الفحصين التانيين أثناء البدء."},
                {"term": "`HealthCheckResult`", "def": "`Healthy` / `Degraded` (شغال بجودة أقل) / `Unhealthy` (لا يصلح للاستخدام)."},
                {"term": "Tags / Predicate", "def": "تحديد أنهي فحوصات تدخل في أنهي endpoint (`live`, `ready`, `db`, `external`)."},
                {"term": "`HealthCheckOptions.ResponseWriter`", "def": "كتابة الاستجابة بنفسك (JSON منظم بدل نص خام)."},
                {"term": "Probe", "def": "فحص دوري من المنصة (K8s/load balancer) لمسار الـhealth."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore
dotnet add Shop.Api package AspNetCore.HealthChecks.NpgSql
dotnet add Shop.Api package AspNetCore.HealthChecks.Redis
dotnet add Shop.Api package AspNetCore.HealthChecks.Rabbitmq
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Health/HealthSetup.cs", "title": "فحوصات مصنّفة بوسوم (المفتاح كله هنا)", "code": r'''
using Microsoft.Extensions.Diagnostics.HealthChecks;

public static class HealthSetup
{
    public static IServiceCollection AddAppHealth(this IServiceCollection services, IConfiguration config)
    {
        services.AddHealthChecks()
            // ── LIVENESS: ذاتي ورخيص. ✗ لا تبعيات خارجية — وإلا كل بطء = إعادة تشغيل
            .AddCheck("self", () => HealthCheckResult.Healthy("process alive"), tags: ["live"])
            .AddCheck<ThreadPoolStarvationCheck>("threadpool", tags: ["live"])

            // ── READINESS: التبعيات اللي من غيرها الخدمة لا تنفع
            .AddNpgSql(
                config.GetConnectionString("Default")!,
                name: "postgres",
                healthQuery: "SELECT 1;",
                timeout: TimeSpan.FromSeconds(2),          // ✓ لا تترك فحصًا بلا سقف
                tags: ["ready", "db"])
            .AddDbContextCheck<AppDbContext>("dbcontext", tags: ["ready", "db"])
            .AddRedis(
                config.GetConnectionString("Redis")!,
                name: "redis",
                timeout: TimeSpan.FromSeconds(2),
                tags: ["ready", "cache"])

            // ── تبعيات خارجية: Degraded مش Unhealthy (الخدمة لسه تنفع لقراءات من الكاش)
            .AddCheck<PaymentGatewayHealthCheck>("payment-gateway", tags: ["external", "payments"])

            // ── حداثة المهام الدورية (من درس الجدولة)
            .AddCheck<JobFreshnessHealthCheck>("jobs-freshness", tags: ["ready", "jobs"]);

        return services;
    }

    public static IEndpointRouteBuilder MapHealthEndpoints(this IEndpointRouteBuilder app)
    {
        // ✓ عام ورخيص: المنصة تسأله كل ثوانٍ
        app.MapHealthChecks("/health/live", new HealthCheckOptions
        {
            Predicate = reg => reg.Tags.Contains("live"),
            ResponseWriter = HealthWriter.Json,
            ResultStatusCodes =
            {
                [HealthStatus.Healthy] = StatusCodes.Status200OK,
                [HealthStatus.Degraded] = StatusCodes.Status200OK,     // لسه حي
                [HealthStatus.Unhealthy] = StatusCodes.Status503ServiceUnavailable,
            },
        }).AllowAnonymous().WithTags("Health").ExcludeFromDescription();

        // ★ داخلي فقط: يكشف أسماء التبعيات — لا تعرضه للإنترنت
        app.MapHealthChecks("/health/ready", new HealthCheckOptions
        {
            Predicate = reg => reg.Tags.Contains("ready"),
            ResponseWriter = HealthWriter.Json,
            ResultStatusCodes =
            {
                [HealthStatus.Healthy] = StatusCodes.Status200OK,
                [HealthStatus.Degraded] = StatusCodes.Status200OK,
                [HealthStatus.Unhealthy] = StatusCodes.Status503ServiceUnavailable,
            },
        }).RequireAuthorization(Policies.AdminOnly).WithTags("Health");

        // تفاصيل كاملة للتشخيص (دعم/تحقيق) — خلف مصادقة ودون تخزين
        app.MapHealthChecks("/health/detail", new HealthCheckOptions
        {
            Predicate = _ => true,
            ResponseWriter = HealthWriter.DetailedJson,
        }).RequireAuthorization(Policies.AdminOnly).WithTags("Health");

        return app;
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Health/HealthWriter.cs", "title": "استجابة JSON منظمة + تنقية الأسرار", "code": r'''
using System.Text.Json;
using Microsoft.Extensions.Diagnostics.HealthChecks;

public static class HealthWriter
{
    private static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web);

    /// <summary>ملخص بلا تفاصيل — آمن نسبيًا ويكفي للمنصة والمراقبة.</summary>
    public static Task Json(HttpContext ctx, HealthReport report) => Write(ctx, report, detailed: false);

    /// <summary>تفاصيل لكل فحص — للتشخيص فقط وخلف مصادقة.</summary>
    public static Task DetailedJson(HttpContext ctx, HealthReport report) => Write(ctx, report, detailed: true);

    private static async Task Write(HttpContext ctx, HealthReport report, bool detailed)
    {
        ctx.Response.ContentType = "application/json; charset=utf-8";
        ctx.Response.Headers.CacheControl = "no-store";

        var payload = new
        {
            status = report.Status.ToString(),
            totalDurationMs = Math.Round(report.TotalDuration.TotalMilliseconds, 1),
            timestamp = DateTimeOffset.UtcNow,
            checks = detailed
                ? report.Entries.Select(e => new
                {
                    name = e.Key,
                    status = e.Value.Status.ToString(),
                    description = e.Value.Description,
                    durationMs = Math.Round(e.Value.Duration.TotalMilliseconds, 1),
                    tags = e.Value.Tags,
                    // ★ لا تُرجع Data كما هي: قد تحتوي connection strings أو تفاصيل داخلية
                    data = Sanitize(e.Value.Data),
                })
                : report.Entries
                    .Where(e => e.Value.Status != HealthStatus.Healthy)     // المشاكل فقط
                    .Select(e => new { name = e.Key, status = e.Value.Status.ToString(), description = e.Value.Description }),
        };

        await ctx.Response.WriteAsync(JsonSerializer.Serialize(payload, Options));
    }

    private static Dictionary<string, object?> Sanitize(IReadOnlyDictionary<string, object> data)
    {
        string[] blocked = ["connectionstring", "connection", "password", "secret", "token", "host", "uri", "query"];
        return data
            .Where(kv => !blocked.Any(b => kv.Key.Contains(b, StringComparison.OrdinalIgnoreCase)))
            .ToDictionary(kv => kv.Key, kv => (object?)kv.Value);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "فحوصات مخصصة: اللي بيكشف المشاكل فعلًا"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Health/CustomChecks.cs", "title": "timeout صريح + كاش + Degraded بدل Unhealthy", "code": r'''
/// <summary>
/// استنزاف الـthread pool = تطبيق «حي» لكنه ما بيردش. فحص بيكشفه مبكرًا.
/// </summary>
public sealed class ThreadPoolStarvationCheck : IHealthCheck
{
    public Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct)
    {
        ThreadPool.GetAvailableThreads(out var worker, out _);
        ThreadPool.GetMaxThreads(out var maxWorker, out _);
        var usedRatio = 1.0 - (double)worker / maxWorker;

        var data = new Dictionary<string, object>
        {
            ["availableWorkerThreads"] = worker,
            ["maxWorkerThreads"] = maxWorker,
            ["usedRatio"] = Math.Round(usedRatio, 3),
        };

        var result = usedRatio > 0.95 ? HealthCheckResult.Unhealthy("استنزاف thread pool", data: data)
                   : usedRatio > 0.80 ? HealthCheckResult.Degraded("ضغط على thread pool", data: data)
                   : HealthCheckResult.Healthy(data: data);

        return Task.FromResult(result);
    }
}

/// <summary>
/// تبعية خارجية: فحص بطيء = فحص يضر. كاش النتيجة + timeout صريح.
/// ★ الإطار نفسه لا يفرض timeout عامًا على الفحوصات. بعض حزم المجتمع بتوفر
    ///   معامل `timeout` (مثل AddRedis/AddNpgSql) — حدده دائمًا، وإلا لفّ الفحص بنفسك كما هنا.
/// </summary>
public sealed class PaymentGatewayHealthCheck(IHttpClientFactory http, IMemoryCache cache) : IHealthCheck
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromSeconds(30);
    private static readonly TimeSpan Timeout = TimeSpan.FromSeconds(2);

    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct)
    {
        var cached = await cache.GetOrCreateAsync("health:payment-gateway", async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = CacheTtl;
            return await ProbeAsync(ct);
        });

        return cached ?? HealthCheckResult.Degraded("لا توجد نتيجة فحص");
    }

    private async Task<HealthCheckResult> ProbeAsync(CancellationToken ct)
    {
        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
            timeout.CancelAfter(Timeout);                                  // ✓ timeout صريح

            using var client = http.CreateClient("payment-gateway");
            var started = TimeProvider.System.GetTimestamp();
            using var response = await client.GetAsync("/health", timeout.Token);
            var elapsed = TimeProvider.System.GetElapsedTime(started);

            return response.IsSuccessStatusCode
                ? HealthCheckResult.Healthy($"gateway reachable in {elapsed.TotalMilliseconds:F0}ms")
                : HealthCheckResult.Degraded($"gateway returned {(int)response.StatusCode}");
                // ✓ Degraded مش Unhealthy: خدمة الدفع واقعة ≠ خدمتي كلها غير صالحة
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            return HealthCheckResult.Degraded("gateway غير متاح", exception: ex);
        }
    }
}
'''},
            {"type": "callout", "kind": "danger", "title": "restart storm: أشهر خطأ في الـhealth checks",
             "md": """
لو `/health/live` بيفحص قاعدة البيانات، فأي انقطاع/بطء في القاعدة بيعمل:
كل النسخ تفشل في الـliveness → المنصة **تعيد تشغيلها كلها في نفس اللحظة** →
النسخ بتحاول الاتصال بالقاعدة أثناء الإقلاع (migrations/kاش) → فشل أطول → إعادة تشغيل تانية.
النتيجة: انقطاع كامل من مشكلة جزئية.

القاعدة الذهبية:
- **liveness = ذاتي فقط** (العملية بتشتغل، thread pool مش مستنزف).
- **readiness = التبعيات** (قاعدة، كاش، طابور). فشله بيشيل النسخة من التوزيع **بدون** إعادة تشغيل.
- التبعيات الخارجية غير الحرجة = **Degraded**.
"""},
            {"type": "code", "lang": "yaml", "filename": "deploy/shop-api.yaml", "title": "ربط المسارات بالـprobes في Kubernetes", "code": r'''
livenessProbe:
  httpGet: { path: /health/live, port: 8080 }
  initialDelaySeconds: 10
  periodSeconds: 15
  timeoutSeconds: 2          # ← أقل من أي فحص بطيء محتمل
  failureThreshold: 3        # 3 إخفاقات = إعادة تشغيل (لا تعيد التشغيل من أول فشل)

readinessProbe:
  httpGet: { path: /health/ready, port: 8080 }
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 2        # إزالة سريعة من التوزيع
  successThreshold: 1

startupProbe:                # ★ يحمي التطبيق البطيء في الإقلاع (migrations, warm cache)
  httpGet: { path: /health/live, port: 8080 }
  periodSeconds: 5
  failureThreshold: 30       # حتى 150 ثانية للإقلاع
'''},
            {"type": "table", "head": ["المسار", "الفحوصات", "من يسأله", "عند الفشل"], "rows": [
                ["/health/live", "ذاتية فقط (`self`, `threadpool`)", "liveness probe", "إعادة تشغيل النسخة"],
                ["/health/ready", "التبعيات الحرجة (`db`, `cache`, `jobs`)", "readiness probe / load balancer", "إزالة من التوزيع (بلا إعادة تشغيل)"],
                ["/health/startup", "ذاتي", "startup probe", "يؤخر الفحصين الآخرين حتى اكتمال الإقلاع"],
                ["/health/detail", "كل الفحوصات + بياناتها", "الدعم/التحقيق (خلف admin)", "لا شيء — للتشخيص"],
            ]},
            {"type": "callout", "kind": "warn", "title": "أخطاء عملية",
             "md": """
- **فحص بطيء بلا timeout** → الـprobe بيتعلّق ويحكم على النسخة بالموت وهي شغالة. حدد timeout أقل من timeout الـprobe.
- **فحص بيتنفذ كل 10 ثواني على كل نسخة وبيضرب خدمة خارجية** → حمل بلا معنى. كاش النتيجة 30 ثانية.
- **تسريب تفاصيل** → `HealthReport.Data` ممكن يحتوي connection string. نقّيه (زي `Sanitize` أعلاه) واحمِ المسارات التفصيلية.
- **`ExcludeFromDescription` منسي** → مسارات الـhealth تظهر في OpenAPI العام (ضجيج + كشف بنية).
- **لا مراقبة** → حوّل النتيجة لـmetric (`health.check.status` بوسوم) وأنذِر على سلسلة Degraded، مش على أول فشل.
"""},
            {"type": "checkpoints", "items": [
                "أفرّق بين liveness وreadiness وstartup وأعرف أثر كل فشل على المنصة.",
                "أصنّف الفحوصات بوسوم وأربط كل مسار بمجموعة الفحوصات المناسبة.",
                "أكتب فحوصات مخصصة بـtimeout صريح وكاش و`Degraded` للتبعيات غير الحرجة.",
                "أعرض JSON منظمًا بلا تسريب أسرار، وأحمي المسارات التفصيلية، وأحوّل الحالة لـmetric.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `/health/live` ما يفحصش قاعدة البيانات؟",
                 "options": [
                     "عشان الأداء فقط",
                     "لأن فشل القاعدة هيسبب إعادة تشغيل كل النسخ معًا (restart storm) بدل عزل المشكلة",
                     "لأن المنصة لا تدعمه",
                     "لأن القاعدة ليست مهمة",
                 ], "answer": 1,
                 "explain": "liveness معناه «العملية محتاجة إعادة تشغيل؟». بطء تبعية خارجية مش سبب لإعادة تشغيل تطبيقك."},
                {"q": "فشل `/health/ready` بيعمل إيه في Kubernetes؟",
                 "options": [
                     "إعادة تشغيل الـpod",
                     "إزالة الـpod من الـService endpoints (لا يصله ترافيك) حتى ينجح الفحص",
                     "حذف الـpod",
                     "لا شيء",
                 ], "answer": 1,
                 "explain": "ده بالظبط اللي عايزينه: النسخة تبقى حية وتعالج مشكلتها، بس ما تستقبلش طلبات."},
                {"q": "خدمة الدفع واقعة. أنهي حالة أنسب للفحص؟",
                 "options": [
                     "Unhealthy",
                     "Degraded — الخدمة لسه تقدر تخدم القراءات/الطلبات غير المعتمدة على الدفع",
                     "Healthy",
                     "حذف الفحص",
                 ], "answer": 1,
                 "explain": "`Unhealthy` في readiness هيشيلك من التوزيع بالكامل. `Degraded` بيعكس الحقيقة ويسمح باستمرار الخدمة الجزئية."},
                {"q": "ليه الـcaching مهم في فحص تبعية خارجية؟",
                 "options": [
                     "لتقليل حجم الاستجابة",
                     "الـprobes بتسأل كل نسخ كل ثوانٍ — بلا كاش هتعمل هجوم DoS على التبعية بنفسك",
                     "لتسريع الإقلاع",
                     "لتقليل الـmetrics",
                 ], "answer": 1,
                 "explain": "10 نسخ × كل 10 ثواني = طلب/ثانية على خدمة خارجية لمجرد الفحص. كاش 30 ثانية بيقللها 30 مرة."},
                {"q": "إيه فائدة `startupProbe`؟",
                 "options": [
                     "يسرّع الإقلاع",
                     "يحمي تطبيقًا بطيء البدء (migrations/warm cache) من القتل بفحص liveness مبكر",
                     "يستبدل readiness",
                     "يفحص قاعدة البيانات",
                 ], "answer": 1,
                 "explain": "بينجح أول مرة، الفحصين التانيين يبدأوا. من غيره `initialDelaySeconds` تخمين هش."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "فحوصات صحية صحيحة",
                 "md": "نفّذ `/health/live` (ذاتي فقط)، `/health/ready` (قاعدة + كاش + حداثة المهام)، و`/health/detail` (خلف admin) مع JSON منظم وتنقية للأسرار. أضف فحصًا مخصصًا واحدًا على الأقل (thread pool أو تبعية خارجية بـtimeout وكاش).",
                 "criteria": [
                     "وقف قاعدة البيانات → `/health/live` يرجع 200 و`/health/ready` يرجع 503 (اختبره فعلًا)",
                     "`/health/detail` يتطلب دور admin ولا يظهر connection strings (افحص الاستجابة)",
                     "كل فحص خارجي له timeout ≤ 3 ثوانٍ وكاش للنتيجة",
                     "المسارات مستثناة من OpenAPI (`ExcludeFromDescription`)",
                     "زمن استجابة `/health/live` أقل من 20ms",
                 ],
                 "hint": "لاختبار «وقف القاعدة»: لو بتستخدم Testcontainers من المرحلة 1، `await container.StopAsync()` في اختبار integration هو أسهل طريقة لإثبات سلوك readiness."},
                {"id": "t2", "title": "مراقبة قابلة للتنبيه",
                 "md": "حوّل نتائج الفحوصات لـmetric بوسوم (`health.check.status{name, status}`) واكتب قاعدة تنبيه واحدة مفيدة (مثال: readiness فاشل في ≥50% من النسخ لمدة دقيقتين). وثّق أنهي مسار يستخدمه أي probe في نشرتك.",
                 "criteria": [
                     "metric منشور ويمكن قراءته محليًا (Prometheus/OTel)",
                     "قاعدة تنبيه مكتوبة مع سبب واضح وإجراء مطلوب",
                     "خرائط الـprobes موثقة (مسار/فترة/failureThreshold)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Health checks in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/host-and-deploy/health-checks"},
                {"label": "Kubernetes — liveness/readiness/startup probes", "url": "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"},
                {"label": "AspNetCore.Diagnostics.HealthChecks", "url": "https://github.com/Xabaril/AspNetCore.Diagnostics.HealthChecks"},
                {"label": ".NET metrics with System.Diagnostics.Metrics", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/metrics-instrumentation"},
            ]},
        ],
    },
]
