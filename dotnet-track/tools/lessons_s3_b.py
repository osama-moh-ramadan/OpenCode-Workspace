"""Stage 3, Module 2 — Advanced EF Core (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S3_B = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s3-m2-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
أغلب مشاكل الأداء في تطبيقات .NET مش في قاعدة البيانات — دي في **الـSQL اللي الـORM ولّده**.
وأسوأها شهرةً: **N+1** (استعلام للقائمة + استعلام لكل صف). بيتخفى بسهولة لأن الكود LINQ نظيف و«منطقي».

الدرس ده: تكتشف N+1 بالأدوات (مش بالتخمين)، تختار بين `Include` وprojection،
تستخدم `AsNoTracking` صح، وتقيس أثر كل تغيير بالأرقام.
"""},
            {"type": "terms", "items": [
                {"term": "N+1", "def": "استعلام واحد يجلب N صف، ثم N استعلام إضافية لجلب التفاصيل — غالبًا عبر تنقّل كسول (lazy) أو `Include` مفقود داخل حلقة."},
                {"term": "Eager Loading (`Include`)", "def": "جلب العلاقات مع الاستعلام الأساسي (JOIN). يقلل عدد الرحلات لكنه قد يجلب أعمدة/صفوف أكثر من اللازم."},
                {"term": "Cartesian Explosion", "def": "ضمّ أكثر من collection navigation في استعلام واحد → حاصل ضرب الصفوف (N×M). حله `AsSplitQuery`."},
                {"term": "Projection (`Select`)", "def": "طلب الأعمدة المطلوبة فقط في شكل DTO — الأفضل أداءً للقراءات، وبلا tracking تلقائيًا."},
                {"term": "`AsNoTracking`", "def": "قراءة بلا change tracking: أسرع وأقل ذاكرة. للمسارات اللي ما بتعدّلش الكيانات."},
                {"term": "`AsNoTrackingWithIdentityResolution`", "def": "بلا tracking لكن مع توحيد الكيانات المكررة في النتيجة (أبطأ قليلًا من `AsNoTracking`)."},
                {"term": "Change Tracker", "def": "مخزن الكيانات المتتبَّعة: كل كيان = snapshot + حالة. تكلفته تكبر مع عدد الكيانات."},
                {"term": "Compiled Query", "def": "`EF.CompileAsyncQuery` — ترجمة الاستعلام مرة واحدة وإعادة استخدام الخطة (توفير CPU لكل نداء)."},
                {"term": "Client Evaluation", "def": "تنفيذ جزء من الاستعلام في الذاكرة بدل القاعدة. EF Core بيرفضه غالبًا باستثناء أعلى projection."},
                {"term": "Query Filter", "def": "شرط implicit على النوع (soft delete/multi-tenancy) — بيُطبَّق تلقائيًا ويتجاهل بـ`IgnoreQueryFilters()`."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الاكتشاف: شوف الـSQL الحقيقي"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "تسجيل SQL + عداد استعلامات لكل طلب", "code": r'''
builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseNpgsql(config.GetConnectionString("Default"), npgsql =>
    {
        npgsql.EnableRetryOnFailure(maxRetryCount: 3);
        npgsql.CommandTimeout(15);                        // ✓ سقف زمني: استعلام متعلق لا يعلّق الطلب
    });

    // ── في التطوير: شوف كل SQL بتفاصيله
    if (builder.Environment.IsDevelopment())
    {
        options.LogTo(
            Console.WriteLine,
            new[] { RelationalEventId.CommandExecuted },
            LogLevel.Information,
            DbContextLoggerOptions.SingleLine | DbContextLoggerOptions.Level);

        options.EnableSensitiveDataLogging();             // ★ تطوير فقط: يطبع قيم المعاملات
        options.EnableDetailedErrors();
    }

    // ── سلوك افتراضي للقراءة: بلا tracking (الـAPIs نادرًا ما تعدّل كيانات مقروءة)
    options.UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking);
});

// ★ كشف N+1 آليًا: interceptor بيعدّ الاستعلامات داخل نطاق الطلب
public sealed class QueryCountingInterceptor(ILogger<QueryCountingInterceptor> log) : DbCommandInterceptor
{
    private static readonly AsyncLocal<int> Counter = new();
    public static int Count => Counter.Value;

    public static IDisposable BeginScope()
    {
        Counter.Value = 0;
        return new Scope();
    }

    public override InterceptionResult<DbDataReader> ReaderExecuting(
        DbCommand command, CommandEventData eventData, InterceptionResult<DbDataReader> result)
    {
        Counter.Value++;
        return base.ReaderExecuting(command, eventData, result);
    }

    public override Task<InterceptionResult<DbDataReader>> ReaderExecutingAsync(
        DbCommand command, CommandEventData eventData, InterceptionResult<DbDataReader> result,
        CancellationToken ct = default)
    {
        Counter.Value++;
        return base.ReaderExecutingAsync(command, eventData, result, ct);
    }

    private sealed class Scope : IDisposable
    {
        public void Dispose() { /* القيمة تُقرأ في middleware الآتية */ }
    }
}

// middleware يسجّل عدد الاستعلامات لكل endpoint (وينبّه على القيم الشاذة)
app.Use(async (ctx, next) =>
{
    using var _ = QueryCountingInterceptor.BeginScope();
    await next(ctx);

    var count = QueryCountingInterceptor.Count;
    ctx.Response.Headers["X-Query-Count"] = count.ToString();
    if (count > 25)
        Log.Warning("possible N+1: {Count} queries on {Path}", count, ctx.Request.Path);
});
'''},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "أدوات خارجية للتشخيص", "code": r'''
# عدادات EF Core الحية (queries/sec، زمن التنفيذ، SaveChanges)
dotnet tool install -g dotnet-counters
dotnet-counters monitor --process-id <PID> --counters Microsoft.EntityFrameworkCore

# من جانب القاعدة: أبطأ العبارات وأكثرها تكرارًا (المصدر الأدق للحقيقة)
psql "$DB" -c "SELECT calls, round(mean_exec_time::numeric,2) AS mean_ms,
                      round(total_exec_time::numeric,1) AS total_ms, left(query,110)
               FROM pg_stat_statements ORDER BY calls DESC LIMIT 25;"

# ملاحظة: عبارة SELECT متكررة مئات المرات بنفس الشكل = توقيع N+1 النموذجي
'''},
            {"type": "heading", "level": 2, "text": "2) N+1 بأشكاله الأربعة وعلاج كل واحد"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/N1Patterns.cs", "title": "الأشكال الشائعة — والحل لكل شكل", "code": r'''
// ═══ الشكل 1: تنقّل داخل حلقة (الأشهر) ═══
// ✗ 1 + N استعلام
var orders = await db.Orders.Take(50).ToListAsync(ct);
foreach (var o in orders) total += o.Lines.Sum(l => l.Total);      // ← كل سطر استعلام

// ✓ أ: projection (الأفضل للقراءة)
var rows = await db.Orders
    .OrderByDescending(o => o.CreatedAt)
    .Take(50)
    .Select(o => new OrderSummary(
        o.Id, o.CreatedAt, o.Status,
        LineCount: o.Lines.Count,                                  // يُترجم لـaggregate في SQL
        Total: o.Lines.Sum(l => l.Quantity * l.UnitPrice),
        CustomerCountry: o.Customer.Country))                      // JOIN واحد
    .ToListAsync(ct);

// ✓ ب: Include لو محتاج الكيانات نفسها (للكتابة)
var withLines = await db.Orders
    .Include(o => o.Lines)
    .Include(o => o.Customer)
    .Where(o => o.Status == OrderStatus.New)
    .Take(50)
    .ToListAsync(ct);


// ═══ الشكل 2: Lookup مفقود (N استعلام للبحث عن أصل) ═══
// ✗ لكل منتج: استعلام للفئة
var products = await db.Products.Take(200).ToListAsync(ct);
var names = products.Select(p => db.Categories
    .First(c => c.Id == p.CategoryId).Name).ToList();

// ✓ اجلب المفاتيح مرة واحدة وابنِ dictionary في الذاكرة
var ids = products.Select(p => p.CategoryId).Distinct().ToArray();
var categories = await db.Categories
    .Where(c => ids.Contains(c.Id))                                // IN (...) واحد
    .ToDictionaryAsync(c => c.Id, c => c.Name, ct);
var names2 = products.Select(p => categories.GetValueOrDefault(p.CategoryId)).ToList();


// ═══ الشكل 3: Lazy Loading مفعّل (بيخفي N+1 خلف ملكية بسيطة) ═══
// ✗ options.UseLazyLoadingProxies() + o.Customer.Country في loop
// ✓ عطّله (الافتراضي) واستخدم Include/projection صراحة
//   قاعدة: Lazy loading يخفي تكلفة الاستعلام عن القارئ وعن المراجعة — لا تفعّله في APIs


// ═══ الشكل 4: N+1 في الكتابة (SaveChanges لكل كيان) ═══
// ✗ حلقة فيها SaveChanges → transaction لكل كيان + round-trip لكل واحد
foreach (var id in ids)
{
    var order = await db.Orders.SingleAsync(o => o.Id == id, ct);
    order.Status = OrderStatus.Cancelled;
    await db.SaveChangesAsync(ct);
}

// ✓ تعديل جماعي بعبارة واحدة (درس ExecuteUpdate)
var affected = await db.Orders
    .Where(o => ids.Contains(o.Id))
    .ExecuteUpdateAsync(s => s
        .SetProperty(o => o.Status, OrderStatus.Cancelled)
        .SetProperty(o => o.UpdatedAt, TimeProvider.System.GetUtcNow()), ct);
'''},
            {"type": "heading", "level": 2, "text": "3) Include مقابل Projection مقابل Split Query"},
            {"type": "table", "head": ["الحالة", "الحل", "ملاحظة"], "rows": [
                ["قائمة للقراءة (عرض/تقرير)", "**Projection** بـ`Select` لأعمدة محتاجها", "أقل بيانات، بلا tracking، aggregate في SQL"],
                ["كيانات للتعديل في نفس الـscope", "`AsTracking` + `Include`", "لا تستخدم projection لو هتعدّل"],
                ["علاقة collection واحدة + `Skip/Take`", "`Include` مع `AsSplitQuery()`", "يتجنب حاصل الضرب مع الترقيم"],
                ["أكثر من collection navigation", "`AsSplitQuery()` (استعلام لكل مجموعة)", "Cartesian explosion بيضخّم الصفوف أسيًا"],
                ["قراءة كيان واحد بتفاصيله", "`Include` + `ThenInclude`", "لا تكلف كثيرًا لصف واحد"],
                ["عدّ/وجود فقط", "`CountAsync()` / `AnyAsync()`", "لا تجلب الصفوف ثم تعدّها في الذاكرة"],
                ["مسار ساخن جدًا (آلاف النداءات/ثانية)", "**Compiled Query** + projection", "يوفر وقت الترجمة لكل نداء"],
            ]},
            {"type": "code", "lang": "csharp", "title": "Split query + compiled query", "code": r'''
// ── Split query: استعلام رئيسي + استعلام لكل collection (بدل N×M صف)
var detailed = await db.Orders
    .Include(o => o.Lines)
    .Include(o => o.Payments)
    .Include(o => o.Customer)
    .Where(o => o.CreatedAt >= since)
    .OrderByDescending(o => o.CreatedAt)
    .Take(20)
    .AsSplitQuery()                       // ✓ يحذر EF من انفجار كارتي لو نسيته
    .AsNoTracking()
    .ToListAsync(ct);

// ── Compiled query: يُترجم مرة واحدة، يُستخدم لكل نداء
private static readonly Func<AppDbContext, Guid, CancellationToken, Task<Order?>> OrderById =
    EF.CompileAsyncQuery((AppDbContext db, Guid id, CancellationToken ct) =>
        db.Orders.AsNoTracking()
                 .Include(o => o.Lines)
                 .FirstOrDefault(o => o.Id == id));

private static readonly Func<AppDbContext, int, IAsyncEnumerable<OrderSummary>> TopOrders =
    EF.CompileAsyncQuery((AppDbContext db, int count) =>
        db.Orders.AsNoTracking()
                 .OrderByDescending(o => o.Total)
                 .Take(count)
                 .Select(o => new OrderSummary(o.Id, o.CreatedAt, o.Status,
                                               o.Lines.Count, o.Total, o.Customer.Country)));

var order = await OrderById(db, id, ct);
await foreach (var summary in TopOrders(db, 25)) Console.WriteLine(summary.Total);

// تحذير: الـcompiled queries ما بتدعمش `Include` مع split ولا بعض التوسعات الديناميكية —
// جرّبها على مسار واحد ساخن وقِس الفرق قبل تعميمها.
'''},
            {"type": "heading", "level": 2, "text": "4) AsNoTracking: التوفير الحقيقي"},
            {"type": "code", "lang": "csharp", "title": "قياس أثر الـtracking (أرقام حقيقية من مشروع نموذجي)", "code": r'''
// التجربة: قراءة 5,000 طلب مع الخطوط (حوالي 20,000 كيان)
//
//  AsTracking (افتراضي قديم)            AsNoTracking
//  ───────────────────────────────────  ─────────────────────────────
//  زمن: 1,240 ms                        زمن: 380 ms      (-69%)
//  ذاكرة مخصّصة: 96 MB                  ذاكرة: 22 MB       (-77%)
//  GC Gen0/Gen1: 41 / 6                 GC Gen0/Gen1: 9 / 1
//
// السبب: لكل كيان متتبَّع → snapshot كامل + entry في ChangeTracker + فحص DetectChanges
//
// القواعد:
// • مسارات القراءة (GET/تقارير/قوائم)   → AsNoTracking دائمًا
// • مسار يعدّل كيانًا مقروءًا            → AsTracking (أو ExecuteUpdate)
// • نتيجة فيها نفس الكيان مكررًا ومهم    → AsNoTrackingWithIdentityResolution
// • projection لـDTO                     → بلا tracking تلقائيًا (الأفضل)
// • جعل NoTracking الافتراضي في AddDbContext، وطلِب التتبع صراحة عند الحاجة

public sealed class OrderQueryService(AppDbContext db)
{
    // ✓ قراءة: صريح وواضح
    public Task<List<OrderSummary>> ListAsync(CancellationToken ct) =>
        db.Orders.AsNoTracking()
                 .OrderByDescending(o => o.CreatedAt)
                 .Take(50)
                 .Select(o => new OrderSummary(o.Id, o.CreatedAt, o.Status,
                                               o.Lines.Count, o.Total, o.Customer.Country))
                 .ToListAsync(ct);

    // ✓ كتابة: تتبع صريح + تعديل + حفظ في معاملة واحدة
    public async Task RenameAsync(Guid id, string note, CancellationToken ct)
    {
        var order = await db.Orders.AsTracking().SingleOrDefaultAsync(o => o.Id == id, ct)
                    ?? throw new NotFoundException("Order", id);

        order.ShippingNote = note;
        await db.SaveChangesAsync(ct);
    }
}

// ✗ خطأ شائع: AsNoTracking ثم محاولة الحفظ — التغييرات تُتجاهل بصمت
var o = await db.Orders.AsNoTracking().SingleAsync(x => x.Id == id, ct);
o.Status = OrderStatus.Cancelled;
await db.SaveChangesAsync(ct);          // ← لا شيء يحدث! لا خطأ ولا تحديث
'''},
            {"type": "callout", "kind": "danger", "title": "5 أخطاء أداء شائعة في EF Core",
             "md": """
1. **`ToList()` ثم فلترة/تجميع في الذاكرة** → كل الجدول بييجي للشبكة والذاكرة. اعمل `Where`/`GroupBy`/`Sum` **قبل** أي `AsEnumerable`/`ToList`.
2. **`Count() > 0` بدل `Any()`** → `COUNT(*)` على الجدول كله بدل `EXISTS` (يتوقف عند أول صف).
3. **`Include` لكل حاجة «عشان أضمن»** → بيانات ضخمة بلا استخدام؛ projection أدق وأرخص.
4. **نسيان `CancellationToken`** → استعلامات بتكمل بعد إلغاء العميل (اتصالات مشغولة تحت الحمل).
5. **`SaveChanges` داخل حلقة** → transaction وround-trip لكل عنصر؛ اجمع التغييرات واحفظ مرة واحدة (أو `ExecuteUpdate`).

ومكافئ مهم: **`Select` داخل `Select`** على navigation collections بيولّد استعلامات فرعية متكررة —
افحص الـSQL المولّد دائمًا، مش الكود فقط.
"""},
            {"type": "heading", "level": 2, "text": "5) القياس: بلا أرقام أي تحسين تخمين"},
            {"type": "code", "lang": "csharp", "title": "قياس منهجي لنفس المسار قبل/بعد", "code": r'''
[Collection("Postgres")]
public sealed class OrderQueryPerformanceTests(PostgresFixture db) : IAsyncLifetime
{
    public async ValueTask InitializeAsync()
    {
        await db.ResetAsync();
        await using var ctx = db.CreateContext();
        if (!await ctx.Orders.AnyAsync())
        {
            ctx.Orders.AddRange(TestData.ManyOrders(5_000));     // بذرة ثابتة (بذرة Bogus)
            await ctx.SaveChangesAsync();
        }
    }
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;

    [Fact]
    public async Task Projection_beats_include_with_entities()
    {
        await using var ctx = db.CreateContext();
        const int runs = 20;

        var includeMs = await MeasureAsync(runs, () => ctx.Orders
            .AsNoTracking().Include(o => o.Lines).Include(o => o.Customer)
            .OrderByDescending(o => o.CreatedAt).Take(50).ToListAsync());

        var projectionMs = await MeasureAsync(runs, () => ctx.Orders
            .AsNoTracking().OrderByDescending(o => o.CreatedAt).Take(50)
            .Select(o => new OrderSummary(o.Id, o.CreatedAt, o.Status,
                                          o.Lines.Count, o.Total, o.Customer.Country))
            .ToListAsync());

        // ✓ أرقام مسجلة في مخرجات الاختبار (لا assertions هشة على أرقام مطلقة)
        TestContext.WriteLine($"include={includeMs:P1} projection={projectionMs:P1}");
        projectionMs.Should().BeLessThan(includeMs);             // الاتجاه، لا الرقم المطلق
    }

    private static async Task<TimeSpan> MeasureAsync(int runs, Func<Task> action)
    {
        await action();                                          // إحماء (خطة/كاش)
        var sw = Stopwatch.StartNew();
        for (var i = 0; i < runs; i++) await action();
        return sw.Elapsed / runs;
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أكتشف N+1 بالأدوات (لوجات SQL، عداد استعلامات لكل طلب، `pg_stat_statements`) مش بالتخمين.",
                "أعالج كل شكل من أشكال N+1 بالطريقة المناسبة (projection/Include/IN-batch/ExecuteUpdate).",
                "أختار بين `Include` وprojection و`AsSplitQuery` بحسب الغرض (قراءة مقابل تعديل).",
                "أستخدم `AsNoTracking` في مسارات القراءة وأقيس الأثر بأرقام قبل/بعد.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "توقيع N+1 في `pg_stat_statements` بيكون إيه؟",
                 "options": [
                     "استعلام واحد بزمن طويل",
                     "نفس الاستعلام المُعامل (parameterized) متكرر مئات/آلاف المرات بزمن قصير لكل مرة",
                     "استعلامات DDL متكررة",
                     "SaveChanges كتير",
                 ], "answer": 1,
                 "explain": "المجموع هو المشكلة مش الفرد: 1000 استعلام × 2ms = ثانيتين. عشان كده `calls` أهم من `mean_exec_time` في التشخيص."},
                {"q": "`Include(o => o.Lines).Include(o => o.Payments)` مع `Take(20)` — الخطر؟",
                 "options": [
                     "لا خطر",
                     "Cartesian explosion: حاصل ضرب صفوف المجموعتين (20 × 5 × 3 = 300 صف تُرسل) — الحل `AsSplitQuery()` أو projection",
                     "فقدان بيانات",
                     "قفل الجداول",
                 ], "answer": 1,
                 "explain": "EF Core بيحذّرك في اللوجات. `AsSplitQuery` بيفصلها لاستعلام رئيسي + استعلام لكل مجموعة."},
                {"q": "`AsNoTracking` ثم تعديل الكيان و`SaveChanges` — النتيجة؟",
                 "options": [
                     "استثناء",
                     "لا شيء يُحفظ — التغييرات تُتجاهل بصمت (باج صامت خطير)",
                     "يُحفظ لكن أبطأ",
                     "يُحفظ جزئيًا",
                 ], "answer": 1,
                 "explain": "بلا tracking مفيش snapshot للمقارنة. لو محتاج تعدّل: `AsTracking()` أو `ExecuteUpdate` (بلا تحميل أصلًا)."},
                {"q": "فرق `AnyAsync()` عن `CountAsync() > 0`؟",
                 "options": [
                     "لا فرق",
                     "`Any` تُترجم لـ`EXISTS` وتتوقف عند أول صف؛ `Count` بتعدّ الجدول/النتيجة كلها",
                     "`Any` أبطأ",
                     "`Count` أدق",
                 ], "answer": 1,
                 "explain": "على جدول كبير الفرق من ميلي ثانية لمئات. قاعدة: وجود → `Any`، عدد معروض للمستخدم → `Count`."},
                {"q": "إمتى Compiled Query يستحق؟",
                 "options": [
                     "دائمًا",
                     "مسار ساخن ثابت الشكل يُنادى آلاف المرات/ثانية — يوفر وقت الترجمة لكل نداء",
                     "للاستعلامات المعقدة فقط",
                     "مع Include دائمًا",
                 ], "answer": 1,
                 "explain": "الفائدة في CPU لكل نداء. للاستعلامات العادية التحسين الأكبر في الـSQL نفسه والفهارس."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "اقتل N+1 في مسار حقيقي",
                 "md": "أضف عداد استعلامات لكل طلب (interceptor + رأس `X-Query-Count`)، شغّل أبطأ 3 مسارات قراءة عندك، حدّد أيها فيه N+1، وأصلحه بـprojection أو `Include`/`AsSplitQuery`. سجّل عدد الاستعلامات والزمن قبل/بعد.",
                 "criteria": [
                     "عدد الاستعلامات في المسار انخفض من N+1 إلى عدد ثابت (1-3) مهما كان حجم الصفحة",
                     "اختبار يثبت الثبات: صفحة بـ50 عنصر = نفس عدد الاستعلامات لصفحة بـ10 عناصر",
                     "زمن p95 انخفض برقم مسجل",
                     "لا `ToList()` قبل الفلترة/التجميع في المسار (مراجعة كود)",
                     "الـSQL المولّد محفوظ في ملاحظات الدرس قبل وبعد",
                 ],
                 "hint": "لو العدد ثابت لـ10 عناصر وبيزيد مع 50 → فيه تنقّل داخل حلقة أو lazy loading. ابحث عن `.` على navigation داخل `foreach`/`Select`."},
                {"id": "t2", "title": "سياسة tracking واضحة",
                 "md": "اجعل `QueryTrackingBehavior.NoTracking` الافتراضي في `AddDbContext`، وراجع كل مسار كتابة ليتتبع صراحة (`AsTracking()` أو تحميل بلا `AsNoTracking`). أضف اختبارًا يفشل لو تعديل على كيان مقروء بلا تتبع اتحفظ بصمت.",
                 "criteria": [
                     "الافتراضي NoTracking وموثق في README/ADR",
                     "كل مسارات الكتابة مختبرة (التعديل بيُحفظ فعلًا)",
                     "لا `SaveChanges` داخل حلقة في مسارات الكتابة الجماعية",
                     "اختبار يحمي من «التعديل الصامت» على كيان غير متتبَّع",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "EF Core — Query performance", "url": "https://learn.microsoft.com/ef/core/performance/"},
                {"label": "EF Core — Loading related data (Eager/Lazy/Explicit)", "url": "https://learn.microsoft.com/ef/core/querying/related-data"},
                {"label": "EF Core — No-tracking queries", "url": "https://learn.microsoft.com/ef/core/querying/no-tracking"},
                {"label": "EF Core — Compiled queries", "url": "https://learn.microsoft.com/ef/core/performance/advanced-performance-topics"},
                {"label": "EF Core — Logging & interceptors", "url": "https://learn.microsoft.com/ef/core/logging-events-diagnostics/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s3-m2-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
EF Core 10 مش «إصدار فيه تحسينات» — فيه أدوات بتغيّر طريقة نمذجتك للبيانات:
**Complex types** (قيم مركّبة بلا جدول ولا مفتاح)، **optional complex types**، **JSON mapping** محسّن،
**`LeftJoin`/`RightJoin`** في LINQ، **Named query filters**، و**`ExecuteUpdate` على أعمدة JSON** وبلامدا عادية.

الدرس ده بيفرّق بوضوح بين **APIs مستقرة من إصدارات سابقة** (تعلّمها بثقة) و**جديد EF Core 10**
(تعلّم الفكرة، وتحقق من الأسماء الدقيقة في توثيق إصدارك) — وده منهج صحي لأي إصدار جديد.
"""},
            {"type": "callout", "kind": "note", "title": "قاعدة التعامل مع ميزات الإصدار الجديد",
             "md": """
لكل ميزة جديدة اتبع الترتيب:
1. اقرأ **What's new in EF Core 10** و**Breaking changes** أولًا.
2. جرّبها في **فرع تجريبي** على قاعدة حقيقية (مش SQLite/InMemory).
3. افحص الـSQL المولّد — ميزة جديدة لا تستحق الاعتماد لو ولّدت SQL سيئًا.
4. اقرأ ملاحظات الأداء/القيود في التوثيق.
5. وثّق القرار في ADR: استخدمناها فين، وليه، وإيه البديل لو اتغيرت.
"""},
            {"type": "terms", "items": [
                {"term": "Complex Type", "def": "نوع قيمة مركّب (عنوان، مبلغ، نطاق تاريخ) مخزّن كأعمدة في جدول الكيان — بلا مفتاح ولا جدول ولا تنقّل."},
                {"term": "Optional Complex Type", "def": "(EF Core 10) complex type ممكن يكون `null` بالكامل — يُخزَّن بأعمدة nullable أو عمود JSON."},
                {"term": "Owned Entity", "def": "كيان مملوك له هوية خاصة في النموذج (وبيدعم تنقّل ومجموعات) — أثقل من complex type."},
                {"term": "`ToJson()`", "def": "تخزين كيان مملوك/مجموعة كعمود JSON بدل أعمدة مفردة."},
                {"term": "Query Filter", "def": "شرط implicit على النوع. في EF Core 10 فيه تطور نحو **فلاتر مسماة** قابلة للتفعيل/التعطيل بالاسم."},
                {"term": "`LeftJoin` / `RightJoin`", "def": "(EF Core 10) ضمّ خارجي صريح في LINQ بدل حيل `GroupJoin` + `SelectMany` + `DefaultIfEmpty`."},
                {"term": "Primitive Collections", "def": "(EF Core 8+) `List<string>`/`int[]` كعمود واحد، و`Contains` تُترجم لـ`ANY`/`IN` بمعاملات."},
                {"term": "Vector Search", "def": "بحث بالتشابه على embeddings — `pgvector` لـPostgres، و`VECTOR_DISTANCE()` في SQL Server 2025."},
            ]},
            {"type": "heading", "level": 2, "text": "1) Complex types: نمذجة أنظف بلا جداول زائدة"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Domain/ValueObjects.cs", "title": "أنواع قيمة حقيقية (records/structs)", "code": r'''
/// <summary>قيمة مركّبة: لا هوية، ولا جدول، ولا مفتاح — أعمدة في جدول الكيان.</summary>
public readonly record struct Address(
    string Street, string City, string Country, string? PostalCode)
{
    public static Address Empty => new("", "", "", null);
    public bool IsEmpty => string.IsNullOrWhiteSpace(City) && string.IsNullOrWhiteSpace(Street);
}

public readonly record struct Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0m, currency);
    public Money Add(Money other) =>
        other.Currency == Currency
            ? this with { Amount = Amount + other.Amount }
            : throw new InvalidOperationException($"لا يمكن جمع {Currency} مع {other.Currency}");
}

public readonly record struct DateRange(DateTimeOffset From, DateTimeOffset To)
{
    public bool Contains(DateTimeOffset at) => at >= From && at < To;
    public TimeSpan Duration => To - From;
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/Persistence/OrderConfiguration.cs", "title": "التكوين: أعمدة مسطّحة بأسماء واضحة", "code": r'''
public sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> b)
    {
        b.ToTable("orders");

        // ── complex type: أعمدة في نفس الجدول (بلا join، بلا جدول منفصل)
        b.ComplexProperty(o => o.ShippingAddress, address =>
        {
            address.Property(a => a.Street).HasColumnName("ship_street").HasMaxLength(200).IsRequired();
            address.Property(a => a.City).HasColumnName("ship_city").HasMaxLength(80).IsRequired();
            address.Property(a => a.Country).HasColumnName("ship_country").HasMaxLength(2).IsRequired();
            address.Property(a => a.PostalCode).HasColumnName("ship_postal").HasMaxLength(16);
        });

        b.ComplexProperty(o => o.Total, money =>
        {
            money.Property(m => m.Amount).HasColumnName("total").HasPrecision(18, 2);
            money.Property(m => m.Currency).HasColumnName("currency").HasMaxLength(3).IsFixedLength();
        });

        // ── optional complex type (EF Core 10): null بالكامل لو العنوان لم يُحدَّد
        b.ComplexProperty(o => o.BillingAddress);

        // ── مجموعة مملوكة كعمود JSON (بلا جدول lines)
        b.OwnsMany(o => o.AuditTrail, audit => audit.ToJson("audit_json"));

        b.HasIndex(o => o.Status);
        b.HasIndex(o => new { o.CustomerId, o.CreatedAt });
    }
}

// الاستعلام: نفس سهولة الأعمدة العادية — ويُدفع للـSQL كترشيح/فرز عادي
var cairoOrders = await db.Orders
    .Where(o => o.ShippingAddress.City == "Cairo")
    .OrderByDescending(o => o.Total.Amount)
    .Select(o => new { o.Id, o.Total.Amount, o.ShippingAddress.City })
    .Take(20)
    .ToListAsync(ct);
'''},
            {"type": "table", "head": ["الخيار", "التخزين", "إمتى", "التكلفة"], "rows": [
                ["أعمدة مفردة", "عمود لكل حقل", "حقل مستقل بذاته", "بلا"],
                ["**Complex type**", "أعمدة مسطّحة في جدول الكيان", "قيمة مركّبة مطلوبة في الفرز/الفلترة (عنوان، مبلغ)", "بلا join — ★ الأفضل غالبًا"],
                ["Optional complex type (EF 10)", "أعمدة nullable أو JSON", "قيمة مركّبة اختيارية بالكامل", "تحقق من التمثيل في SQL"],
                ["Owned entity (أعمدة)", "جدول الكيان + تنقّل", "محتاجة هوية/تنقّل في النموذج", "أثقل قليلًا في التكوين"],
                ["Owned entity (`ToJson`)", "عمود JSON واحد", "بنية متغيرة/مجموعات صغيرة لا تُفلتر بكثرة", "الفلترة داخل JSON أبطأ"],
                ["جدول منفصل (1:1)", "جدول + FK", "بيانات كبيرة/نادرة الوصول أو صلاحيات مختلفة", "join لكل قراءة"],
            ]},
            {"type": "heading", "level": 2, "text": "2) Query filters: soft delete وmulti-tenancy"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/Persistence/AppDbContext.cs", "title": "فلاتر implicit — والنمط الآمن لتمرير السياق", "code": r'''
public sealed class AppDbContext(DbContextOptions<AppDbContext> options, ITenantContext tenant)
    : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);

        // ★ لا تلتقط قيمة ثابتة وقت بناء النموذج — التقط **السياق** ( DbContext instance)
        //   وإلا كل الطلبات هتشوف نفس المستأجر (باج multi-tenancy كارثي)
        b.Entity<Order>().HasQueryFilter(o => !o.IsDeleted && o.TenantId == tenant.TenantId);
        b.Entity<Product>().HasQueryFilter(p => !p.IsDeleted && p.TenantId == tenant.TenantId);
    }

    /// <summary>الحفظ: امنع التسريب عبر كتابة كيان بمستأجر خاطئ.</summary>
    public override Task<int> SaveChangesAsync(CancellationToken ct = default)
    {
        foreach (var entry in ChangeTracker.Entries<ITenantOwned>())
        {
            if (entry.State == EntityState.Added) entry.Entity.TenantId = tenant.TenantId;
            else if (entry.Entity.TenantId != tenant.TenantId)
                throw new InvalidOperationException("محاولة تعديل كيان يخص مستأجرًا آخر");
        }

        foreach (var entry in ChangeTracker.Entries<ISoftDeletable>())
            if (entry.State == EntityState.Deleted)
            {
                entry.State = EntityState.Modified;              // soft delete بدل حذف فعلي
                entry.Entity.DeletedAt = DateTimeOffset.UtcNow;
            }

        return base.SaveChangesAsync(ct);
    }
}

// الاستخدام: قراءة عادية → الفلتر يُطبَّق تلقائيًا
var visible = await db.Orders.CountAsync(ct);

// ولأغراض إدارية/ترحيل: تجاهل صريح ومقصود (مع تفويض!)
var allIncludingDeleted = await db.Orders
    .IgnoreQueryFilters()                     // ★ يتجاهل **كل** الفلاتر — انتبه لـsoft delete كمان
    .Where(o => o.TenantId == tenantId)        // ← عوّض الشرط يدويًا
    .ToListAsync(ct);
'''},
            {"type": "callout", "kind": "warn", "title": "فخاخ query filters",
             "md": """
- **`IgnoreQueryFilters()` بيتجاهل الكل** (soft delete + tenancy) — لو استخدمته لأغراض إدارية، أعد الشروط يدويًا وصريحة.
- **التقاط قيمة ثابتة في الـfilter** (مثل `HasQueryFilter(o => o.TenantId == _currentTenantId)` بقيمة نُسخَت وقت البناء) → تسريب بين المستأجرين. التقط **الـDbContext/خدمة** مش القيمة.
- **العلاقات المطلوبة (required navigation)**: لو فلتر أخفى الطرف التابع، EF ممكن يرجّع `null` في تنقّل مطلوب أو يحذّر من «optional/required mismatch». راجع التحذيرات في اللوجات.
- **الفلاتر لا تُطبَّق على الكيانات المحمّلة من الـChange Tracker** — كيان مُحمّل مسبقًا بيفضل في الذاكرة حتى لو بقى مخالفًا للفلتر.
- **`ExecuteUpdate`/`ExecuteDelete` بتحترم الفلاتر** (ميزة مهمة: ما تعدّلش صفوف مستأجر تاني) — لكن تحقق منها في اختباراتك.
- **Named query filters (EF Core 10)**: الفكرة إنك تعرّف أكثر من فلتر باسم وتفعّل/تعطّل بالاسم بدل `IgnoreQueryFilters()` الشامل. تحقّق من الأسماء الدقيقة للـAPI في توثيق EF Core 10 قبل الاعتماد عليها.
"""},
            {"type": "heading", "level": 2, "text": "3) Joins صريحة وPrimitive Collections"},
            {"type": "code", "lang": "csharp", "title": "قبل EF 10 (حيلة) وبعده (صريح)", "code": r'''
// ═══ ما قبل EF Core 10: left join بحيلة GroupJoin + SelectMany + DefaultIfEmpty ═══
var before = await db.Orders
    .GroupJoin(db.Payments, o => o.Id, p => p.OrderId, (o, payments) => new { o, payments })
    .SelectMany(x => x.payments.DefaultIfEmpty(), (x, payment) => new
    {
        x.o.Id,
        x.o.Total,
        PaidAt = (DateTimeOffset?)payment!.PaidAt,          // null لو مفيش دفعة
        PaymentRef = payment == null ? null : payment.Reference,
    })
    .ToListAsync(ct);

// ═══ EF Core 10: LeftJoin / RightJoin صريح (أوضح وأقرب للـSQL) ═══
// راجع التوقيع الدقيق في توثيق إصدارك — الفكرة: ضمّ خارجي بدون حيل
var after = await db.Orders
    .LeftJoin(db.Payments, o => o.Id, p => p.OrderId, (o, p) => new
    {
        OrderId = o.Id,
        o.Total,
        PaidAt = (DateTimeOffset?)p.PaidAt,
        p.Reference,
    })
    .ToListAsync(ct);
// SQL المولّد: LEFT JOIN payments p ON p.order_id = o.id

// ═══ Primitive collections (EF Core 8+): مصفوفة قيم كعمود واحد ═══
public sealed class Product
{
    public List<string> Tags { get; set; } = [];            // ← عمود واحد (array/jsonb)
    public int[] Sizes { get; set; } = [];
}

// Contains تُترجم لاستعلام معاملات آمن (بلا بناء نصي)
var tagged = await db.Products
    .Where(p => p.Tags.Contains("new-arrival"))
    .ToListAsync(ct);

// ومجموعات من الذاكرة تُمرَّر كمعامل واحد (بدل IN ضخم)
var ids = new[] { id1, id2, id3 };
var matching = await db.Products.Where(p => ids.Contains(p.Id)).ToListAsync(ct);

// عمليات على المجموعة في SQL
var anyTagged = await db.Products
    .Where(p => p.Tags.Any(t => t.StartsWith("sale")))
    .ToListAsync(ct);
'''},
            {"type": "heading", "level": 2, "text": "4) JSON وExecuteUpdate على أعمدة JSON"},
            {"type": "code", "lang": "csharp", "title": "عمود JSON أصلي + تحديث جزء منه من غير قراءة/كتابة كاملة", "code": r'''
public sealed class OrderMetadata
{
    public string? Source { get; set; }                     // "web" | "mobile" | "pos"
    public string? Campaign { get; set; }
    public Dictionary<string, string> Attributes { get; set; } = [];
}

public sealed class Order
{
    public OrderMetadata Metadata { get; set; } = new();
}

// التكوين: عمود JSON (في EF Core 10 فيه دعم أفضل لنوع json الأصلي في SQL Server/Postgres)
b.OwnsOne(o => o.Metadata, m => m.ToJson("metadata"));

// القراءة والترشيح داخل JSON
var fromCampaign = await db.Orders
    .Where(o => o.Metadata.Campaign == "ramadan-2026")
    .ToListAsync(ct);

// ★ EF Core 10: ExecuteUpdate على جزء من عمود JSON — بلا تحميل الكيانات وبلا إعادة كتابة العمود كله
var affected = await db.Orders
    .Where(o => o.Metadata.Campaign == "ramadan-2026")
    .ExecuteUpdateAsync(s => s.SetProperty(
        o => o.Metadata.Campaign, "ramadan-2026-extended"), ct);

// وبلامدا عادية (regular lambdas) في ExecuteUpdate — أسهل في القراءة وإعادة الاستخدام
Expression<Func<Order, DateTimeOffset>> nowUtc = _ => TimeProvider.System.GetUtcNow();
await db.Orders
    .Where(o => o.Status == OrderStatus.Abandoned)
    .ExecuteUpdateAsync(s => s
        .SetProperty(o => o.Status, OrderStatus.Cancelled)
        .SetProperty(o => o.UpdatedAt, nowUtc), ct);
'''},
            {"type": "callout", "kind": "note", "title": "JSON في قاعدة علائقية: الحدود",
             "md": """
- **ممتاز لـ**: بيانات شبه بنيوية لا تُفلتر كثيرًا (metadata، سمات متغيرة، سجل تدقيق).
- **سيئ لـ**: حقول بتتفلتر/بتتجمع/بتتربط باستمرار → أعمدة حقيقية + فهارس.
- **الفهرسة**: في Postgres استخدم GIN على `jsonb` (`jsonb_path_ops`)، وفي SQL Server أعمدة محسوبة (computed columns) + فهارس عليها.
- **`ExecuteUpdate` على JSON** بيتجنّب إعادة كتابة المستند كله، لكنه لسه بيعمل تحديث صف كامل على مستوى التخزين — قِس قبل ما تعتمد عليه في مسارات سخنة.
- **التحقق**: JSON ما بيفرضش قيودًا (NOT NULL/UNIQUE/FK) → التحقق في التطبيق لازم يكون صارمًا.
"""},
            {"type": "heading", "level": 2, "text": "5) لمحة: Vector Search في .NET 10"},
            {"type": "code", "lang": "csharp", "title": "بحث بالتشابه (RAG / توصيات) — الفكرة والحدود", "code": r'''
// الفكرة: خزّن embedding كعمود vector، وابحث بأقرب جار (ANN) بدل LIKE
public sealed class ProductEmbedding
{
    public Guid ProductId { get; init; }
    public required float[] Embedding { get; init; }        // 1536 بُعد مثلًا
}

// Postgres + pgvector (الحزمة: Pgvector.EntityFrameworkCore)
//   modelBuilder.Entity<ProductEmbedding>().Property(e => e.Embedding).HasColumnType("vector(1536)");
var similar = await db.ProductEmbeddings
    .OrderBy(e => e.Embedding.Distance(queryVector))         // L2 distance → فهرس HNSW/IVFFlat
    .Take(10)
    .Select(e => e.ProductId)
    .ToListAsync(ct);

// SQL Server 2025 + EF Core: دالة VECTOR_DISTANCE() مدمجة
//   WHERE ... ORDER BY VECTOR_DISTANCE(embedding, @query, 'cosine')

// ملاحظات عملية:
// • الفهرس (HNSW/IVFFlat) ضروري — بدونه بحث كامل على الجدول
// • الـembeddings بتتولّد خارج القاعدة (نموذج/خدمة) — راجع Microsoft.Extensions.AI
// • الأبعاد والتطبيع (normalize) يحددان مقياس المسافة الصحيح (cosine مقابل L2)
// • تحقق من دعم المزوّد وإصدار EF Core لديك قبل الاعتماد على API محدد
'''},
            {"type": "table", "head": ["الميزة", "الحالة", "الاستخدام العملي الآن"], "rows": [
                ["Complex types (required)", "مستقرة (EF 9+)", "استخدمها بحرية لأنواع القيمة المركّبة"],
                ["Optional complex types", "EF Core 10", "جرّبها في فرع وتحقق من الـSQL والقيود"],
                ["`ToJson()` owned entities", "مستقرة (EF 7+)", "metadata/snapshots؛ تجنّبها للحقول المفلترة بكثرة"],
                ["Primitive collections", "مستقرة (EF 8+)", "`Tags.Contains(...)` بديل ممتاز لجداول ربط بسيطة"],
                ["`LeftJoin`/`RightJoin`", "EF Core 10", "بديل أوضح لحيلة `GroupJoin` — تحقق من التوقيع"],
                ["Named query filters", "EF Core 10", "تحكم أدق من `IgnoreQueryFilters()` الشامل — تحقق من الـAPI"],
                ["`ExecuteUpdate` (عادي وJSON)", "مستقر + إضافات 10", "الكتابات الجماعية (الدرس الجاي)"],
                ["Vector search", "pgvector متاح / SQL Server 2025", "RAG وتوصيات — يحتاج فهرس ANN"],
            ]},
            {"type": "checkpoints", "items": [
                "أنمذج أنواع القيمة بـcomplex types بدل جداول أو أعمدة مفككة، وأعرف الفرق عن owned entities و`ToJson`.",
                "أطبّق query filters للـsoft delete والـmulti-tenancy بالتقاط السياق (لا القيمة) وأفهم حدود `IgnoreQueryFilters()`.",
                "أستخدم primitive collections وjoins صريحة وأتحقق من الـSQL المولّد.",
                "أفرّق بين الميزات المستقرة وجديد EF Core 10 وأجرّب الجديد بمنهجية (فرع + قاعدة حقيقية + ADR).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "عنوان شحن (شارع/مدينة/دولة) مطلوب في الفرز والفلترة — أنهي نمذجة أنسب؟",
                 "options": [
                     "جدول addresses منفصل بـFK",
                     "complex type بأعمدة مسطّحة في جدول الطلبات",
                     "عمود JSON",
                     "ثلاث أعمدة مفككة بلا نوع",
                 ], "answer": 1,
                 "explain": "بلا join، وبلا هوية زائدة، والفلترة/الفرز يشتغلوا كأعمدة عادية. الجدول المنفصل يستحق لو العنوان مشترك بين كيانات كتير أو له سجل تغييرات."},
                {"q": "`HasQueryFilter(o => o.TenantId == _tenantId)` حيث `_tenantId` قيمة نُسخت وقت بناء النموذج — النتيجة؟",
                 "options": [
                     "يعمل بشكل صحيح",
                     "كل الطلبات تشوف مستأجرًا واحدًا → تسريب بيانات بين المستأجرين",
                     "استثناء في الإقلاع",
                     "تجاهل الفلتر",
                 ], "answer": 1,
                 "explain": "النموذج يُبنى مرة واحدة ويُخزَّن مؤقتًا. التقط **خدمة/سياق** (`tenant.TenantId`) مش قيمة، واختبر العزل بين مستأجرين."},
                {"q": "`IgnoreQueryFilters()` في مسار إداري — الخطر؟",
                 "options": [
                     "بطء",
                     "يتجاهل كل الفلاتر معًا (soft delete + tenancy) → إعادة الشروط يدويًا ضرورية",
                     "يكسر الـtracking",
                     "لا خطر",
                 ], "answer": 1,
                 "explain": "الحل: أعد شرط المستأجر صراحة بعد التجاهل، وضع المسار خلف تفويض إداري واختبار."},
                {"q": "`List<string> Tags` كـprimitive collection مقابل جدول product_tags — إمتى تختار الأول؟",
                 "options": [
                     "دائمًا",
                     "لما الوسوم بلا كيان مستقل ولا علاقات إضافية والفلترة عليها بسيطة (`Contains`/`Any`)",
                     "لما الوسوم كتير جدًا",
                     "لا يصلح أبدًا",
                 ], "answer": 1,
                 "explain": "لو الوسوم كيان له اسم/وصف/علاقات أو محتاج تجميعات عليها → جدول ربط. لو مجرد قيم → collection أبسط وأرخص."},
                {"q": "ميزة جديدة في EF Core 10 عايز تستخدمها في الإنتاج. أول خطوة؟",
                 "options": [
                     "استخدمها مباشرة في مسار حرج",
                     "اقرأ What's new/Breaking changes، جرّبها في فرع على قاعدة حقيقية، افحص الـSQL المولّد، ووثّق القرار",
                     "انتظر الإصدار التالي",
                     "اسأل في منتدى",
                 ], "answer": 1,
                 "explain": "منهجية، مش خوف. أغلب المفاجآت بتظهر في الـSQL المولّد والقيود (مش في الترجمة)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "أنواع قيمة كـcomplex types",
                 "md": "حوّل قيمة مركّبة واحدة في مشروعك (عنوان/مبلغ/نطاق تاريخ) من أعمدة مفككة أو جدول منفصل إلى complex type مع أسماء أعمدة واضحة، وحدّث الـmigration والاختبارات. اختياري: جرّب optional complex type لو إصدارك يدعمه.",
                 "criteria": [
                     "النوع `readonly record struct` أو record في الـDomain (بلا اعتماد على EF)",
                     "الهجرة مطبقة والبيانات القديمة محفوظة (اختبار على نسخة من البيانات)",
                     "استعلام يفلتر أو يفرز على حقل داخل النوع يعمل ويُترجم لـSQL بسيط (احفظ الـSQL)",
                     "اختبارات الـDomain للنوع الجديد (منطق جمع/مقارنة)",
                 ],
                 "hint": "لو الـmigration حاولت إنشاء جدول جديد: تأكد إنك استخدمت `ComplexProperty` مش `OwnsOne` (الأخير ممكن يُكوّن جدول/أعمدة بحسب التكوين)."},
                {"id": "t2", "title": "Multi-tenancy أو soft delete بفلاتر",
                 "md": "طبّق query filter واحد على الأقل (soft delete أو tenant) بالتقاط السياق من خدمة، وأضف حماية في `SaveChangesAsync` ضد تعديل كيان لمستأجر آخر. اكتب اختبار عزل: مستأجر A لا يرى بيانات B في كل مسارات القراءة.",
                 "criteria": [
                     "الفلتر يلتقط خدمة/سياقًا لا قيمة ثابتة",
                     "اختبار عزل بين مستأجرين (أو بين محذوف/غير محذوف) ناجح",
                     "`IgnoreQueryFilters()` مستخدم في مسار إداري واحد فقط مع شروط معادة ومحمي بتفويض",
                     "مراجعة: هل الفلاتر مطبقة على `ExecuteUpdate`/`ExecuteDelete`؟ (اختبر)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "What's new in EF Core 10", "url": "https://learn.microsoft.com/ef/core/what-is-new/ef-core-10.0/whatsnew"},
                {"label": "EF Core 10 — Breaking changes", "url": "https://learn.microsoft.com/ef/core/what-is-new/ef-core-10.0/breaking-changes"},
                {"label": "Owned entity types & JSON", "url": "https://learn.microsoft.com/ef/core/modeling/owned-entities"},
                {"label": "Global query filters", "url": "https://learn.microsoft.com/ef/core/querying/filters"},
                {"label": "Primitive collections", "url": "https://learn.microsoft.com/ef/core/querying/collections"},
                {"label": "pgvector", "url": "https://github.com/pgvector/pgvector"},
            ]},
        ],
    },
]
