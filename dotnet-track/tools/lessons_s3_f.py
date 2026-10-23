"""Stage 3, Module 4 — Capstone project: from 800ms to 80ms with evidence."""

TODAY = "2026-10-22"

LESSONS_S3_F = [
    {
        "id": "s3-m4-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "callout", "kind": "goal", "title": "هدف المرحلة",
             "md": """
خد مسارًا واحدًا بطيئًا في مشروعك (قائمة طلبات، تقرير، صفحة كتالوج) وحوّله من
**~800ms p95 إلى ≤ 120ms p95** — أو حقّق تحسّنًا ≥ 5× — **بدليل قابل للتكرار**:
بيئة ثابتة، بيانات ثابتة، قياس بعد كل تغيير، وتقرير يشرح **ليه** التحسّن حصل مش بس **إنه** حصل.

**المدة المتوقعة: 16-22 ساعة عمل.** المعيار مش السرعة النهائية؛ المعيار **المنهجية**:
أي مطور تاني يقدر يكرر قياسك ويصدّق أرقامك.
"""},
            {"type": "text", "md": """
ليه المشروع ده بالذات مهم؟ لأن «حسّنت الأداء» جملة بلا قيمة في مقابلة أو في مراجعة تقنية.
الجملة اللي لها قيمة: **«p95 نزل من 812ms إلى 96ms على 50 مستخدمًا متزامنًا، 68% من التحسّن من فهرس مركّب
غطّى شرط الحالة والترتيب، و21% من استبدال N+1 بـprojection، والبقي من NoTracking والكاش — والقياسات محفوظة هنا.»**

القاعدة الحاكمة للمشروع: **تغيير واحد في المرة، وقياس بعد كل تغيير.** لو غيّرت حاجة تانية في نفس الوقت،
الأرقام بقت بلا معنى (ومش هتعرف مين سبب التحسن).
"""},
            {"type": "heading", "level": 2, "text": "قبل ما تبدأ: حدّد الهدف والخط الأساسي"},
            {"type": "steps", "title": "الخطوة صفر (لا تتخطاها)", "items": [
                {"title": "اختر مسارًا واحدًا",
                 "md": "endpoint واحد أو عملية واحدة. لا تحاول تحسين النظام كله — العمق هنا أهم من العرض. سجّل: المسار، حجم البيانات، والحمل المستهدف."},
                {"title": "اكتب هدفًا رقميًا وقابلًا للقياس",
                 "md": "مثال: `p95 ≤ 120ms و p99 ≤ 300ms و معدل أخطاء < 0.1% عند 50 VUs`. هدف بلا رقم = مشروع بلا نهاية.",
                 "code": {"lang": "text", "title": "PERF_GOALS.md", "code": "المسار: GET /api/orders?size=20\nالبيانات: 1,000,000 طلب · 40,000 عميل · 120,000 سطر طلب\nالبيئة: docker compose (api: 2 vCPU/2GB, postgres: 2 vCPU/4GB)\nالحمل: 50 VUs · 3 دقائق · k6 ramping-vus\n\nالخط الأساسي (قبل أي تغيير):\n  p50 = 431 ms · p95 = 812 ms · p99 = 1,940 ms\n  RPS = 61 · http_req_failed = 0.4%\n  استعلامات/طلب = 22 · استعلامات القاعدة في الثانية = 1,340\n\nالهدف:\n  p95 ≤ 120 ms · p99 ≤ 300 ms · أخطاء < 0.1% · استعلامات/طلب ≤ 3"}},
                {"title": "ثبّت البيئة والبيانات",
                 "md": "docker compose بموارد محددة، سكربت بذر بيانات بحجم واقعي (مش 100 صف)، وإيقاف أي حاجة تانية على الجهاز. **القياس على جهاز التطوير العشوائي لا يُقارن بشيء.**"},
                {"title": "شغّل الخط الأساسي 3 مرات",
                 "md": "احسب الوسيط من 3 تشغيلات (التباين الطبيعي موجود). لو التباين > 15% بين التشغيلات، بيئتك غير مستقرة — اصلحها قبل البدء."},
                {"title": "التقط التشخيص الأولي",
                 "md": "`pg_stat_statements` (أعلى calls وtotal_time)، `EXPLAIN ANALYZE` للاستعلام الرئيسي، `dotnet-counters` أثناء الحمل، وعدد الاستعلامات لكل طلب (interceptor من الدرس 3.2.1)."},
            ]},
            {"type": "heading", "level": 2, "text": "طبقات التحسين (بالترتيب المرجّح للأثر)"},
            {"type": "table", "head": ["#", "الطبقة", "التغييرات المتوقعة", "الأثر النموذجي", "الدرس"], "rows": [
                ["1", "**SQL والفهارس**", "فهرس مركّب يغطي الشرط والترتيب، `INCLUDE` للأعمدة المقروءة، فهرس جزئي للصفوف الحية، إزالة فرز غير مدعوم بفهرس", "★★★ الأكبر غالبًا (2-20×)", "3.1.1"],
                ["2", "**شكل الاستعلام**", "إسقاط أعمدة غير مستخدمة، `LIMIT` صارم، استعلام واحد بدل N+1، تحويل فرز/فلترة للقاعدة", "★★★ (2-10×)", "3.1.1 / 3.2.1"],
                ["3", "**N+1 → projection**", "`Select` لـDTO بدل `Include` لكيانات كاملة، أو `AsSplitQuery` عند الحاجة للكيانات", "★★ (2-5×)", "3.2.1"],
                ["4", "**Tracking**", "`AsNoTracking` لكل مسارات القراءة + سلوك افتراضي NoTracking", "★ (1.3-2×) + ذاكرة أقل كثيرًا", "3.2.1"],
                ["5", "**حجم الحمولة**", "DTO أصغر، ضغط الاستجابة (Brotli)، ترقيم cursor بحد أقصى، إزالة حقول لا تُعرض", "★★ (خصوصًا p99 والشبكة)", "2.1.3"],
                ["6", "**الكاش**", "HybridCache للنتائج المحسوبة، Output cache للقوائم العامة، Redis للبيانات المشتركة، إبطال بعد الكتابة", "★★★ للمسارات الساخنة (3-50×)", "2.1.6 / 3.3.1"],
                ["7", "**الاتصال بالقاعدة**", "حجم pool مناسب، `CommandTimeout`، اتصال واحد مشترك، تقليل round-trips (`QueryMultiple`)", "★ (ثبات الذيل)", "3.1.3"],
                ["8", "**async وthread pool**", "إزالة `.Result`/`.Wait()`، تمرير `CancellationToken`، توازي بحدود", "★★ تحت الحمل (الذيل)", "3.3.4"],
                ["9", "**التخصيصات/GC**", "`Span`/`ArrayPool` في التحليل والتسلسل، تقليل كائنات وسيطة", "★ (Gen2/p99)", "3.3.4"],
                ["10", "**البنية**", "read model متخصص (Redis/Mongo/OpenSearch)، نقل تجميعات لمهمة مجدولة، تخزين نتيجة التقرير", "★★★ لكن بتعقيد تشغيلي", "3.3.2"],
            ]},
            {"type": "callout", "kind": "warn", "title": "ترتيب العمل: الأكبر أثرًا والأقل خطرًا أولًا",
             "md": """
ابدأ بالطبقات 1-4 (SQL/شكل الاستعلام/N+1/tracking): **أعلى عائد وأقل تعقيد تشغيلي**.
ثم 5-7، وبعدها 8-9. الطبقة 10 (read model/بنية) **آخر حاجة** — لأنها بتضيف تعقيد تشغيلي
(مزامنة، اتساق eventual، مراقبة إضافية) ولازم تكون مبررة بأرقام بعد استنفاد الأسهل.

⚠️ **لا تبدأ بالكاش**: الكاش بيخفي الاستعلام البطيء ويؤجل المشكلة، وبيضيف تعقيد إبطال.
لما تصلح الاستعلام الأول، الكاش ممكن يبقى مش ضروري أصلًا — أو يبقى أكثر فعالية بكتير.
"""},
            {"type": "heading", "level": 2, "text": "بروتوكول القياس (لكل تغيير)"},
            {"type": "code", "lang": "bash", "filename": "perf/measure.sh", "title": "سكربت واحد يضمن إن كل قياس بنفس الظروف", "code": r'''
#!/usr/bin/env bash
# الاستخدام: ./perf/measure.sh <label>   مثال: ./perf/measure.sh 03-add-composite-index
set -euo pipefail

LABEL="${1:?label مطلوب (مثال: 02-after-index)}"
RUNS="${RUNS:-3}"
OUT="results/$LABEL"
mkdir -p "$OUT"

echo "── 0) تحقق من ثبات البيئة"
docker compose ps --format json > "$OUT/containers.json"
psql "$DATABASE_URL" -c "SELECT count(*) AS orders FROM orders;"        | tee "$OUT/data-size.txt"
psql "$DATABASE_URL" -c "SELECT version();"                             | tee -a "$OUT/data-size.txt"
dotnet --version                                                        | tee -a "$OUT/data-size.txt"

echo "── 1) إعادة بناء نظيفة (Release)"
dotnet build -c Release --no-incremental > "$OUT/build.log" 2>&1

echo "── 2) إحماء (warm-up) — تشغيل واحد يُهمل"
BASE_URL="$BASE_URL" k6 run load/scenarios.js --vus 10 --duration 30s > "$OUT/warmup.txt" 2>&1 || true

echo "── 3) القياس ($RUNS تشغيلات)"
for i in $(seq 1 "$RUNS"); do
  echo "   run $i/$RUNS"
  BASE_URL="$BASE_URL" k6 run load/scenarios.js --summary-export="$OUT/run-$i.json" \
       > "$OUT/run-$i.log" 2>&1
  sleep 10                                                    # اترك النظام يستقر
done

echo "── 4) لقطة عدادات الخادم أثناء التشغيل الأخير"
( dotnet-counters monitor -p "$API_PID" --counters System.Runtime,Npgsql \
    > "$OUT/counters.txt" 2>&1 & COUNTERS_PID=$! ; sleep 60 ; kill $COUNTERS_PID ) || true

echo "── 5) حالة القاعدة"
psql "$DATABASE_URL" -c "
  SELECT calls, round(mean_exec_time::numeric,2) AS mean_ms,
         round(total_exec_time::numeric,1) AS total_ms, left(query,90) AS query
  FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;" | tee "$OUT/pg-statements.txt"

psql "$DATABASE_URL" -c "EXPLAIN (ANALYZE, BUFFERS) $MAIN_QUERY" | tee "$OUT/explain.txt"

echo "── 6) ملخص"
python3 perf/summarize.py "$OUT" | tee "$OUT/summary.txt"
echo "✓ محفوظ في $OUT"
'''},
            {"type": "code", "lang": "text", "filename": "results/PERF_REPORT.md", "title": "قالب التقرير — املأه بعد كل تغيير", "code": r'''
# تقرير أداء: GET /api/orders

الهدف: p95 ≤ 120ms · p99 ≤ 300ms · أخطاء < 0.1% @ 50 VUs
البيئة: docker compose · api 2vCPU/2GB · postgres 2vCPU/4GB · .NET 10.0.x · Postgres 17
البيانات: 1,000,000 طلب · 40,000 عميل · بذر ثابت (seed.sql)

| # | التغيير | p50 | p95 | p99 | RPS | أخطاء | استعلامات/طلب | Δ p95 |
|---|---------|-----|-----|-----|-----|-------|----------------|-------|
| 0 | الخط الأساسي | 431 | 812 | 1940 | 61 | 0.4% | 22 | — |
| 1 | فهرس مركّب (status, created_at DESC, id DESC) INCLUDE (total, customer_id) | 118 | 214 | 486 | 178 | 0.1% | 22 | **-74%** |
| 2 | projection بدل Include + DTO مصغّر | 74 | 131 | 268 | 262 | 0.0% | 22 | -39% |
| 3 | القضاء على N+1 (استعلام واحد + JOIN) | 41 | 63 | 118 | 486 | 0.0% | **3** | -52% |
| 4 | AsNoTracking افتراضيًا | 39 | 58 | 104 | 512 | 0.0% | 3 | -8% |
| 5 | HybridCache على الصفحة الأولى (TTL 30s + إبطال بعد الكتابة) | 12 | 24 | 46 | 1,240 | 0.0% | 0.4 (متوسط) | -59% |
| **الإجمالي** | | **12** | **24** | **46** | **1,240** | **0.0%** | **0.4** | **-97%** |

## التحليل: من وين جه التحسّن؟
1. **الفهرس المركّب (−74%)**: قبله كانت الخطة `Index Scan` على created_at مع
   `Rows Removed by Filter: 3912` — أي 95% من الصفوف تُقرأ ثم تُرفض. بعد الفهرس: `Index Only Scan`.
2. **القضاء على N+1 (−52%)**: 22 استعلامًا لكل طلب → 3. الدليل: `pg_stat_statements` كان يُظهر
   استعلام `SELECT … FROM order_lines WHERE order_id = $1` بـ1,340 نداء/ثانية.
3. **projection (−39%)**: حجم الصف المنقول من 1.2KB إلى 180B؛ `Buffers: shared hit` انخفض من 290 إلى 41.
4. **الكاش (−59%)**: نسبة إصابة 82% على 50 VUs. لاحظ: **بعد** إصلاح الاستعلامات،
   فالتكلفة المخزنة أقل والإبطال أبسط.

## ما لم يعمل (مهم بنفس القدر)
- `Span<T>` في مسار التسلسل: تحسّن 3ms في micro-benchmark، **بلا أثر مقيس** على p95 → لم يُعتمد.
- رفع `max_parallel_workers_per_gather`: تحسّن غير ثابت (تباين 22%) → رُفض.
- Output cache على endpoint مفوّض: رفض لأسباب أمنية (تسريب بين المستخدمين) → استُخدم HybridCache بمفتاح لكل مستخدم.

## القرارات والتكاليف
- ADR-011: الفهرس المركّب — تكلفة: +18% مساحة، +4ms على INSERT (مقيس) → مقبول.
- ADR-012: الكاش بـTTL 30s + إبطال بالوسوم — تكلفة: عدم اتساق ≤ 30s على L1 → مقبول تجاريًا وموثق.
- حارس الانحدار: اختبار أداء في CI يفشل لو p95 > 150ms على بيئة معيارية.

## إعادة الإنتاج
    docker compose up -d && ./perf/seed.sh && ./perf/measure.sh 05-final
النتائج الخام في results/<label>/ (k6 JSON + counters + EXPLAIN).
'''},
            {"type": "heading", "level": 2, "text": "حارس ضد الانحدار (Regression guard)"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/Performance/OrdersListPerformanceTests.cs", "title": "اختبار أداء في CI — باتجاه وميزانية، لا برقم مطلق هش", "code": r'''
[Collection("Postgres")]
[Trait("Category", "Performance")]              // يُشغَّل في job منفصل (بطيء ويحتاج بيئة ثابتة)
public sealed class OrdersListPerformanceTests(PostgresFixture db) : IAsyncLifetime
{
    private const int SeedOrders = 50_000;      // حجم معياري ثابت (مش 1M في CI)
    private const int Runs = 20;                // عدد جولات القياس
    private static readonly TimeSpan Budget = TimeSpan.FromMilliseconds(150);

    public async ValueTask InitializeAsync()
    {
        await db.ResetAsync();
        await using var ctx = db.CreateContext();
        if (await ctx.Orders.CountAsync() < SeedOrders)
        {
            ctx.Orders.AddRange(TestData.ManyOrders(SeedOrders));
            await ctx.SaveChangesAsync();
            await ctx.Database.ExecuteSqlRawAsync("ANALYZE orders;");   // ★ إحصائيات حديثة
        }
    }
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;

    [Fact]
    public async Task List_orders_stays_within_budget_and_query_count()
    {
        await using var ctx = db.CreateContext();
        var interceptor = new QueryCounter();      // DbCommandInterceptor محلي
        ctx.Database.AddInterceptor(interceptor);

        // إحماء (JIT/خطة/كاش)
        for (var i = 0; i < 3; i++) await RunAsync(ctx);

        // ★ قياس تسلسلي: DbContext ليس thread-safe، فلا تشغّل استعلامات متزامنة عليه
        var times = new List<TimeSpan>(Runs);
        for (var i = 0; i < Runs; i++)
        {
            var sw = Stopwatch.StartNew();
            await RunAsync(ctx);
            times.Add(sw.Elapsed);
        }

        times.Sort();
        var p95 = times[(int)(times.Length * 0.95)];

        TestContext.WriteLine($"p50={times[times.Length / 2]:F1} p95={p95:F1} queries={interceptor.Count}");

        // ✓ ميزانية اتجاهية (تعمل على أجهزة مختلفة) + حد ثابت لعدد الاستعلامات (لا يتغير بالجهاز)
        interceptor.Count.Should().BeLessThanOrEqualTo(3, "N+1 انحدار: عدد الاستعلامات لكل طلب زاد");
        p95.Should().BeLessThan(Budget, "انحدار أداء في مسار القائمة");
    }

    /// <summary>عدّاد استعلامات (نفس فكرة interceptor الدرس 3.2.1 لكن بنطاق محلي للاختبار).</summary>
    private sealed class QueryCounter : DbCommandInterceptor
    {
        public int Count;
        public override DbDataReader ReaderExecuting(DbCommand command, CommandEventData e, DbDataReader result)
        { Count++; return result; }
        public override Task<DbDataReader> ReaderExecutingAsync(DbCommand command, CommandEventData e,
            DbDataReader result, CancellationToken ct = default)
        { Count++; return Task.FromResult(result); }
    }

    private static Task<List<OrderSummary>> RunAsync(AppDbContext ctx) =>
        ctx.Orders.AsNoTracking()
            .OrderByDescending(o => o.CreatedAt).ThenByDescending(o => o.Id)
            .Take(20)
            .Select(o => new OrderSummary(o.Id, o.CreatedAt, o.Status, o.Lines.Count, o.Total, o.Customer.Country))
            .ToListAsync();
}
'''},
            {"type": "callout", "kind": "danger", "title": "أخطاء بتبوظ المشروع ده (وكلها حصلت فعلًا لفرق حقيقية)",
             "md": """
- **تغيير أكثر من حاجة بين قياسين** → الأرقام بلا معنى، ومش هتعرف السبب. تغيير واحد، قياس، سجل.
- **القياس على جهاز التطوير مع متصفح وIDE وDocker** → تباين 30%+ يبتلع أي تحسّن حقيقي. استخدم بيئة معزولة بموارد محددة.
- **بيانات صغيرة (100 صف)** → خطة التنفيذ مختلفة تمامًا عن الإنتاج، والفهرس «ما يعملش فرق». بذّر بحجم واقعي.
- **نسيان `ANALYZE`** بعد تغيير الفهارس/البيانات → المخطط بيشتغل بإحصائيات قديمة والنتائج مضللة.
- **الكاش أول حاجة** → تحسّن ضخم مؤقت، والمشكلة الأساسية مخفية، وتعقيد إبطال للأبد.
- **مقارنة تشغيلات في أوقات مختلفة** (أو بعد إعادة تشغيل) بدون warm-up → أول تشغيل دايمًا أبطأ.
- **الاعتماد على المتوسط** → p95/p99 هو اللي بيمثل تجربة المستخدم والـSLA.
- **عدم تسجيل «ما لم يعمل»** → أغلى معلومات للفريق؛ بدونها حد هيجرّب نفس الحاجة الفاشلة بعد شهر.
- **تجاهل تكلفة التحسين** → كل فهرس بيكلف في الكتابة، وكل كاش بيكلف في الاتساق. سجّل التكلفة جنب العائد.
"""},
            {"type": "tasks", "title": "مهام المشروع", "items": [
                {"id": "t1", "title": "التحسين الكامل مع دليل",
                 "md": "نفّذ بروتوكول القياس: خط أساسي (3 تشغيلات) ثم تحسينات طبقية (واحدة في المرة) حتى تحقق الهدف أو تثبت أن الباقي غير مجدٍ اقتصاديًا. احفظ كل النتائج الخام في `results/<label>/`.",
                 "criteria": [
                     "هدف رقمي مكتوب **قبل** البدء (p95/p99/أخطاء/استعلامات لكل طلب)",
                     "خط أساسي من 3 تشغيلات بتباين < 15% (موثق)",
                     "5 تغييرات على الأقل، كل واحد بقياس مستقل وملف نتائج خاص",
                     "تحسّن إجمالي ≥ 5× في p95 (أو بلوغ الهدف المعلن)",
                     "عدد الاستعلامات لكل طلب ≤ 3 في المسار المختار",
                     "تقرير `PERF_REPORT.md` فيه الجدول + تحليل السبب لكل تغيير + قسم «ما لم يعمل»",
                     "كل EXPLAIN ANALYZE قبل/بعد محفوظ كنص",
                 ],
                 "hint": "لو التحسّن أقل من المتوقع: ارجع لـ`pg_stat_statements` — غالبًا الاستعلام الأبطأ مش الاستعلام اللي افترضته. ولو p95 تحسن وp99 لأ: المشكلة ذيل (GC/thread pool/lock) مش في SQL."},
                {"id": "t2", "title": "بيئة قياس قابلة للتكرار",
                 "md": "ابنِ `docker compose` بموارد محددة + سكربت بذر بيانات بحجم واقعي + سكربت قياس واحد (`measure.sh`) + سكربت تلخيص. أي شخص (أو CI) يقدر يكرر أرقامك بأمر واحد.",
                 "criteria": [
                     "`docker compose up && ./perf/seed.sh && ./perf/measure.sh baseline` يعمل من clone نظيف",
                     "حدود CPU/ذاكرة معلنة في compose (ومطبقة)",
                     "البذر ثابت وقابل للتكرار (نفس الأرقام في كل تشغيل)",
                     "الملفات محفوظة في الـrepo مع README يشرح الاستخدام",
                 ]},
                {"id": "t3", "title": "حارس الانحدار + القرارات",
                 "md": "أضف اختبار أداء في CI (ميزانية زمنية + حد ثابت لعدد الاستعلامات لكل طلب)، واكتب ADRs للقرارات المكلفة (فهرس جديد، كاش بـTTL، read model) بتكلفتها وعائدها.",
                 "criteria": [
                     "اختبار أداء يُشغَّل في job منفصل (Category=Performance) ولا يبطئ الـCI العادي",
                     "الاختبار يفشل عند انحدار مفتعل (جرّب: احذف الفهرس وشوف)",
                     "حد ثابت لعدد الاستعلامات لكل طلب (لا يتأثر بسرعة الجهاز)",
                     "ADR لكل تحسين مكلف: السياق، القرار، التكلفة المقاسة، العائد المقاس",
                     "ملاحظة في README عن كيفية تحديث الميزانية عند تغيير البيئة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "EF Core — Performance", "url": "https://learn.microsoft.com/ef/core/performance/"},
                {"label": "ASP.NET Core — Performance best practices", "url": "https://learn.microsoft.com/aspnet/core/performance/performance-best-practices"},
                {"label": "PostgreSQL — EXPLAIN", "url": "https://www.postgresql.org/docs/current/using-explain.html"},
                {"label": "BenchmarkDotNet", "url": "https://benchmarkdotnet.org/"},
                {"label": "k6 — Running distributed tests & thresholds", "url": "https://grafana.com/docs/k6/"},
                {"label": ".NET diagnostics tools", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/"},
                {"label": "Systems Performance (Brendan Gregg)", "url": "https://www.brendangregg.com/systems-performance-2nd-edition-book.html"},
            ]},
        ],
    },
]
