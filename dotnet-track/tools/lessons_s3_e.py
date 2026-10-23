"""Stage 3, Module 3 — Caching, alternative storage & measurement (lessons 3-4 of 4)."""

TODAY = "2026-10-22"

LESSONS_S3_E = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s3-m3-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
«حسّيت إنه أسرع» مش قياس. و`Stopwatch` حول كود صغير **بيكذب** بشكل منهجي: JIT بيسخّن، الكود الميت بيتحذف،
الـGC بيشتغل في وقت عشوائي، والـCPU بيغيّر تردده.

الدرس ده بيعلمك ثلاث أدوات لمستويات مختلفة: **BenchmarkDotNet** لكود محدد، **k6** لسلوك النظام تحت حمل،
و**dotnet-counters/dotnet-trace/dotnet-dump** لتشخيص الإنتاج — وإزاي تقرأ p95/p99 بدل المتوسط اللي بيخفي كل حاجة.
"""},
            {"type": "terms", "items": [
                {"term": "Micro-benchmark", "def": "قياس وحدة كود صغيرة بمعزل. صحيح فقط بأداة تتحكم في JIT/GC/التسخين (BenchmarkDotNet)."},
                {"term": "Macro/Load test", "def": "قياس النظام كله تحت حمل حقيقي (k6) — الأقرب لتجربة المستخدم."},
                {"term": "Profiling", "def": "أخذ عينات من العملية الجارية لمعرفة أين يُستهلك CPU/الذاكرة فعلًا (dotnet-trace)."},
                {"term": "Dead Code Elimination", "def": "المحرك يحذف حسابًا نتيجته غير مستخدمة → benchmark يقيس صفرًا. الحل: استهلك النتيجة."},
                {"term": "Tiered Compilation / Dynamic PGO", "def": ".NET بيترجم على مرحلتين ويحسّن بحسب الاستخدام الفعلي — سبب إضافي لعدم الثقة في أول تشغيل."},
                {"term": "p50 / p95 / p99", "def": "الوسيط والنسب المئوية للزمن. المتوسط بيخفي الذيل؛ p99 هو تجربة أسوأ المستخدمين."},
                {"term": "Little's Law", "def": "التزامن ≈ الإنتاجية × الزمن. أساس الربط بين VUs وRPS وlatency."},
                {"term": "Saturation / Knee", "def": "النقطة اللي بعدها زيادة الحمل ترفع الزمن وتنزل الإنتاجية — سعة النظام الحقيقية."},
                {"term": "Allocation / Gen0", "def": "الذاكرة المخصّصة لكل تشغيل وجمعيات GC الناتجة — مؤشر أداء رئيسي في .NET."},
                {"term": "Thread Pool Starvation", "def": "كل خيوط الـpool مشغولة بانتظار (sync-over-async) → طابور يطول وزمن يرتفع فجأة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) BenchmarkDotNet: قياس كود بطريقة صحيحة"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الإعداد والتشغيل", "code": r'''
dotnet new console -n Shop.Benchmarks && cd Shop.Benchmarks
dotnet add package BenchmarkDotNet

# ★ Release دائمًا، وبلا debugger، وعلى جهاز هادئ
dotnet run -c Release -- --filter '*OrderPricing*'
dotnet run -c Release -- --filter '*' --job short          # دورة سريعة أثناء التطوير
dotnet run -c Release -- --runtimes net10.0 --exporters json html
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Benchmarks/PricingBenchmarks.cs", "title": "قياس مقارن: قبل/بعد تحسين حقيقي", "code": r'''
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Jobs;

[MemoryDiagnoser]                                  // ★ يعرض Gen0/Gen1/Allocated — الأهم في .NET
[GroupBenchmarksBy(BenchmarkLogicalGroupRule.ByParams)]
[SimpleJob(RuntimeMoniker.Net10_0, warmupCount: 3, iterationCount: 10)]
public class OrderPricingBenchmarks
{
    private Order[] _orders = default!;

    [Params(100, 10_000)]                          // أحجام مختلفة: التحسين قد يختلف بحسب الحجم
    public int Count;

    [GlobalSetup]
    public void Setup()
    {
        _orders = TestData.ManyOrders(Count).ToArray();     // بيانات واقعية وثابتة البذرة
    }

    [Benchmark(Baseline = true)]                   // ★ الأساس: كل نتيجة تُقاس كنسبة منه
    public decimal Linq_SumWithAllocation()
    {
        // النمط الشائع: مجموعات وسيطة + إغلاق (closure) لكل عميل
        return _orders
            .GroupBy(o => o.Customer.Country)
            .Select(g => new { Country = g.Key, Total = g.Sum(o => o.Total) })
            .Where(x => x.Total > 1000m)
            .Sum(x => x.Total);
    }

    [Benchmark]
    public decimal SinglePass_Span()
    {
        Span<decimal> totals = stackalloc decimal[Countries.Count];   // ✓ بلا تخصيص على الكومة
        for (var i = 0; i < _orders.Length; i++)
        {
            var idx = Countries.IndexOf(_orders[i].Customer.Country);
            if (idx >= 0) totals[idx] += _orders[i].Total;
        }

        var result = 0m;
        foreach (var t in totals) if (t > 1000m) result += t;
        return result;                               // ★ استهلك النتيجة (منع Dead Code Elimination)
    }

    [Benchmark]
    public decimal ForeachWithDictionary()
    {
        var map = new Dictionary<string, decimal>(8);
        foreach (var o in _orders)
            map[o.Customer.Country] = map.GetValueOrDefault(o.Customer.Country) + o.Total;

        var result = 0m;
        foreach (var kv in map) if (kv.Value > 1000m) result += kv.Value;
        return result;
    }
}

// مثال مخرجات (اتجاهي — أرقامك هتختلف):
// | Method                | Count  | Mean      | Ratio | Gen0    | Allocated |
// |---------------------- |------- |---------- |------ |-------- |---------- |
// | Linq_SumWithAllocation| 10000  | 412.3 μs  |  1.00 | 38.0859 | 320.5 KB  |
// | SinglePass_Span       | 10000  |  58.1 μs  |  0.14 |       - |      1 KB |
// | ForeachWithDictionary | 10000  | 121.7 μs  |  0.30 |  3.9063 |  33.2 KB  |
//
// القراءة: Ratio < 1 = أسرع من الأساس؛ Allocated = التخصيص لكل تشغيل (المحرك الحقيقي لـGC).
'''},
            {"type": "callout", "kind": "warn", "title": "قواعد benchmark لا تُكسر",
             "md": """
1. **Release فقط** — Debug بلا تحسينات، والنتائج بلا معنى.
2. **استهلك النتيجة** (`return` أو حقل) — وإلا JIT يحذف الحساب وتقيس صفرًا.
3. **بيانات واقعية وثابتة** — بيانات عشوائية لكل تشغيل = تباين لا يُفسَّر.
4. **لا تقيس I/O كمicro-benchmark** — شبكة/قرص متغيرة؛ استخدم load test أو محاكاة.
5. **سجّل البيئة** (CPU، RAM، إصدار .NET، OS) — benchmark بلا سياق غير قابل للمقارنة.
6. **اهتم بـAllocated مثل Mean** — في خدمات عالية الحمل، التخصيص هو سبب الذيل (GC pauses).
7. **كرر وشوف التباين** — `Error`/`StdDev` عاليين يعني البيئة مش هادية (VM/noisy neighbor).
8. **لا تحسّن بلا macro** — micro-benchmark على كود مش في المسار الساخن = مضيعة وقت.
"""},
            {"type": "heading", "level": 2, "text": "2) k6: قياس النظام تحت حمل"},
            {"type": "code", "lang": "javascript", "filename": "load/scenarios.js", "title": "4 سيناريوهات: smoke / load / stress / soak", "code": r'''
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

// مقاييس مخصصة تُظهر في الملخص مع المدمجة
const listOrders = new Trend("list_orders_duration", true);
const authFailures = new Rate("auth_failures");

export const options = {
  scenarios: {
    // ① smoke: يعمل كل شيء؟ (قبل أي حمل جاد)
    smoke: { executor: "per-vu-iterations", vus: 3, iterations: 5, exec: "browse", tags: { phase: "smoke" } },

    // ② load: الحمل المتوقع
    load: {
      executor: "ramping-vus", startVUs: 0, startTime: "10s",
      stages: [
        { duration: "1m", target: 20 },
        { duration: "3m", target: 50 },
        { duration: "1m", target: 0 },
      ],
      exec: "browse",
    },

    // ③ stress: أين نقطة الانهيار؟ (نُشغَّل منفصلًا)
    // stress: { executor: "ramping-arrival-rate", startRate: 50,
    //           stages: [{ duration: "2m", target: 200 }, { duration: "2m", target: 800 }],
    //           preAllocatedVUs: 200, maxVUs: 1000, exec: "browse" },

    // ④ soak: تسريب ذاكرة/تدهور؟ (ساعات)
    // soak: { executor: "constant-vus", vus: 30, duration: "2h", exec: "browse" },
  },

  thresholds: {
    http_req_failed: ["rate<0.01"],                       // أقل من 1% أخطاء
    http_req_duration: ["p(95)<300", "p(99)<800"],        // ★ نسب مئوية، لا متوسط
    list_orders_duration: ["p(95)<250"],
    auth_failures: ["rate<0.005"],
    checks: ["rate>0.99"],
  },
};

const BASE = __ENV.BASE_URL ?? "http://localhost:8123";

export function setup() {
  const res = http.post(`${BASE}/api/auth/login`, JSON.stringify({
    email: __ENV.EMAIL, password: __ENV.PASSWORD,
  }), { headers: { "Content-Type": "application/json" } });

  if (res.status !== 200) throw new Error(`login failed: ${res.status} ${res.body}`);
  return { token: res.json("accessToken") };
}

export function browse(data) {
  const headers = { Authorization: `Bearer ${data.token}` };

  const list = http.get(`${BASE}/api/orders?size=20`, { headers, tags: { name: "listOrders" } });
  listOrders.add(list.timings.duration);
  check(list, { "list 200": (r) => r.status === 200, "has items": (r) => r.json("items").length >= 0 });

  const id = list.status === 200 ? list.json("items[0].id") : null;
  if (id) {
    const detail = http.get(`${BASE}/api/orders/${id}`, { headers, tags: { name: "getOrder" } });
    check(detail, { "detail 200": (r) => r.status === 200 });
  }

  sleep(1);                                               // ★ فكّر كمستخدم، لا كآلة ضغط
}

// ملخص قابل للحفظ والمقارنة (بدل الاعتماد على مخرجات الطرفية)
export function handleSummary(data) {
  return {
    "results/summary.json": JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
  };
}
function textSummary(data, opts) { return JSON.stringify(data.metrics.http_req_duration?.values ?? {}); }
'''},
            {"type": "table", "head": ["الرقم", "معناه", "إمتى تقلق"], "rows": [
                ["p50 (الوسيط)", "تجربة المستخدم النموذجي", "ارتفاعه = تدهور عام"],
                ["p95", "تجربة 5% الأبطأ — غالبًا هدف الـSLA", "ارتفاعه قبل p50 = ذيل يبدأ (GC/قفل/استعلام)"],
                ["p99", "أسوأ 1% — يكشف المشاكل المتقطعة", "قفزات = stop-the-world GC، thread starvation، أو lock contention"],
                ["`http_req_failed`", "نسبة الأخطاء", "أي ارتفاع تحت الحمل = سعة/خطأ تصميم، مش «حظ»"],
                ["RPS (throughput)", "العمليات المنجزة/ثانية", "يتسطح رغم زيادة VUs = نقطة التشبع"],
                ["VUs (concurrency)", "المستخدمون المتزامنون", "زيادتها مع ثبات RPS = زمن يرتفع فقط"],
                ["`iteration_duration`", "زمن السيناريو كاملًا", "أدق لتجربة المستخدم من زمن طلب واحد"],
            ]},
            {"type": "callout", "kind": "tip", "title": "اقرأ منحنى السعة (لا رقم واحد)",
             "md": """
شغّل `ramping-arrival-rate` من 10 إلى 1000 طلب/ثانية وارسم العلاقة:
- **منطقة خطية**: RPS يزيد والزمن ثابت تقريبًا → النظام تحت السعة.
- **الركبة (knee)**: الزمن يبدأ يرتفع أسرع من الحمل → **دي سعة النظام الحقيقية**، خطط عليها.
- **الانهيار**: RPS ينزل والأخطاء ترتفع → تشبع (اتصالات قاعدة، thread pool، ذاكرة).

الهدف العملي: شغّل الإنتاج عند **60-70% من سعة الركبة** عشان تمتص الذ spikes والنشر المتدرج.
ولا تعمل load test على الإنتاج الحقيقي (استخدم نسخة معزولة ببيانات مشابهة في الحجم).
"""},
            {"type": "heading", "level": 2, "text": "3) التشخيص الحي: counters وtrace وdump"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الأدوات الثلاث", "code": r'''
dotnet tool install -g dotnet-counters dotnet-trace dotnet-dump dotnet-gcdump

# ① عدادات حية (أول خطوة دائمًا — أرخص وأسرع إجابة)
dotnet-counters monitor --process-id <PID> \
  --counters System.Runtime,Microsoft.AspNetCore.Hosting,Microsoft.EntityFrameworkCore,Npgsql

# ② تتبع CPU/GC (لما counters تقول «CPU عالي» أو «GC كتير»)
dotnet-trace collect --process-id <PID> --profile cpu-sampling --duration 00:00:30 --output cpu.nettrace
dotnet-trace collect --process-id <PID> --profile gc-verbose --duration 00:00:20 --output gc.nettrace
# افتح الملف في PerfView (Windows) أو حوّله لـspeedscope:
dotnet-trace convert cpu.nettrace --format Speedscope

# ③ ذاكرة (لما النمو مستمر = تسريب محتمل)
dotnet-gcdump collect --process-id <PID> --output heap.gcdump
dotnet-dump collect --process-id <PID> --output core.dump
dotnet-dump analyze core.dump
> dumpheap -stat            # أكثر الأنواع استهلاكًا للذاكرة
> gcroot -all 0x7f...       # من يمسك هذا الكائن (جذر التسريب)
'''},
            {"type": "table", "head": ["العدّاد", "القيمة الصحية", "لو مرتفعة → السبب المرجح"], "rows": [
                ["`cpu-usage`", "< 70% تحت الحمل المتوقع", "كود غير كفء، GC مفرط، أو حمل زائد"],
                ["`time-in-gc`", "< 5%", "تخصيصات كثيفة → راجع `Allocated` في الـbenchmarks"],
                ["`gen-0-gc-count` / `gen-2`", "Gen0 كثيرة مقبول؛ **Gen2 نادرة**", "Gen2 متكررة = كائنات طويلة العمر/تسريب أو LOH"],
                ["`gc-heap-size`", "مستقر (نمو ثم انخفاض دوري)", "نمو مستمر بلا انخفاض = تسريب"],
                ["`threadpool-thread-count`", "قريب من عدد الأنوية", "ارتفاع مستمر = starvation (blocking/sync-over-async)"],
                ["`monitor-lock-contention-count`", "منخفض", "أقفال متنازع عليها → قلّل نطاق القفل أو غيّر التصميم"],
                ["`exception-count`", "قريب من صفر", "استثناءات في المسار الساخن (تكلفة + منطق خاطئ)"],
                ["ASP.NET `current-requests` / `failed-requests`", "ثابت/منخفض", "تراكم = تشبع في مورد (اتصالات/خيوط)"],
                ["EF/`Npgsql` active connections", "أقل من حد الـpool", "الاقتراب من الحد = pool صغير أو معاملات طويلة"],
            ]},
            {"type": "callout", "kind": "note", "title": "منهجية التشخيص: من العرض للأداة",
             "md": """
| العرض | أول أداة | ما تبحث عنه |
|---|---|---|
| زمن مرتفع تحت حمل معين | k6 + `dotnet-counters` | نقطة التشبع، `threadpool-queue-length`، `time-in-gc` |
| CPU عالي بلا حمل | `dotnet-trace --profile cpu-sampling` | الدوال الأعلى في flame graph (حلقة، regex، تسلسل) |
| ذاكرة تنمو مع الوقت | `dotnet-counters` ثم `dotnet-gcdump`/`dump` | أنواع مهيمنة + `gcroot` لمعرفة من يمسكها |
| توقفات دورية قصيرة (p99) | `dotnet-trace --profile gc-verbose` | Gen2 / LOH allocations / pause reasons |
| استعلام بطيء | `pg_stat_statements` + `EXPLAIN ANALYZE` | (درس الفهارس) |
| أخطاء متقطعة تحت الحمل | لوجات + metrics بالتوقيت نفسه | timeout، pool exhausted، deadlock، 429 |
| بطء في الإقلاع فقط | `dotnet-trace` أثناء البدء + Startup probe | migrations، warm cache، JIT (فكّر في R2R/AOT) |

القاعدة: **عدّادات أولًا** (رخيصة وتحدد الاتجاه)، ثم تتبع/ذاكرة على المسار المحدد.
"""},
            {"type": "heading", "level": 2, "text": "4) إعدادات GC والتجميع (ضبط على مستوى المشروع)"},
            {"type": "code", "lang": "xml", "filename": "Shop.Api.csproj", "title": "إعدادات runtime مؤثرة فعلًا", "code": r'''
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>

  <!-- Server GC: أكثر خيوط جمع → إنتاجية أعلى للخوادم (على حساب ذاكرة أكبر) -->
  <ServerGarbageCollection>true</ServerGarbageCollection>
  <ConcurrentGarbageCollection>true</ConcurrentGarbageCollection>

  <!-- DATAS (.NET 9+): يضبط حجم الكومة ديناميًا بحسب الحمل — مفيد للكثافة/الحاويات -->
  <GarbageCollectionAdaptationMode>1</GarbageCollectionAdaptationMode>

  <!-- تقليل زمن الإقلاع والذاكرة (ثمن: حجم نشر أكبر) -->
  <TieredCompilation>true</TieredCompilation>
  <TieredPGO>true</TieredPGO>
  <PublishReadyToRun Condition="'$(Configuration)' == 'Release'">true</PublishReadyToRun>

  <!-- في حاويات: احترم حدود الذاكرة/الـCPU (وإلا GC يحسب سعة الجهاز المضيف) -->
  <InvariantGlobalization>false</InvariantGlobalization>
</PropertyGroup>
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء قياس بتضيّع أيام",
             "md": """
- **قياس على Debug أو مع debugger موصول** → أرقام بلا معنى.
- **الاعتماد على المتوسط** → tail latency هو اللي بيكسر تجربة المستخدم والـSLA.
- **قياس في بيئة مختلفة عن الإنتاج** (جهاز تطوير مقابل حاوية بـ2 vCPU) → الاستنتاجات ما تنتقلش.
- **تحسين بلا قياس للحالة الأصلية** → ما تعرفش هل التحسن من تغييرك ولا من ظروف التشغيل.
- **تغيير أكثر من متغير في المرة** → قياس غير قابل للتفسير.
- **نسيان قاعدة البيانات** → 70% من زمن الاستجابة غالبًا في SQL/الشبكة، والكود مش هو الزجاجة.
- **load test بلا بيانات بحجم الإنتاج** → حجم الجدول بيغير خطة التنفيذ والسلوك بالكامل.
- **مقارنة أرقام من أجهزة مختلفة** → قارِن **النسب** (Ratio) على نفس الجهاز، لا القيم المطلقة.
"""},
            {"type": "checkpoints", "items": [
                "أقيس كودًا حساسًا بـBenchmarkDotNet (Release، نتيجة مستهلَكة، بيانات واقعية، `MemoryDiagnoser`).",
                "أشغّل اختبار حمل بـk6 بسيناريوهات وthresholds وأقرأ p95/p99 ونقطة التشبع.",
                "أشخّص بـ`dotnet-counters` أولًا ثم `dotnet-trace`/`dotnet-gcdump` بحسب العرض.",
                "أضبط إعدادات GC/التجميع عن وعي وأقيس أثرها، ولا أحسّن بلا قياس أساسي.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "benchmark رجّع 0.01 ns لعملية معقدة. السبب الأرجح؟",
                 "options": [
                     "الجهاز سريع",
                     "Dead Code Elimination: النتيجة غير مستهلَكة فحذف JIT الحساب",
                     "BenchmarkDotNet مخطئ",
                     "JIT سخّن الكود",
                 ], "answer": 1,
                 "explain": "الحل: `return` النتيجة أو خزنها في حقل `[ThreadStatic]`. قاعدة ذهبية: أي benchmark بلا استهلاك للنتيجة مش موثوق."},
                {"q": "p50 = 40ms لكن p99 = 1800ms. إيه التفسير الأرجح؟",
                 "options": [
                     "القياس غلط",
                     "مشكلة ذيل: Gen2 GC، thread pool starvation، lock contention، أو استعلام بطيء في حالات نادرة",
                     "الشبكة بطيئة",
                     "الحمل منخفض",
                 ], "answer": 1,
                 "explain": "ذيل طويل مع وسيط جيد = حدث متقطع. `dotnet-counters` (time-in-gc, thread-count) ثم `dotnet-trace` يحددوه."},
                {"q": "RPS توقف عند 400 رغم زيادة VUs لـ500 والزمن يرتفع. معنى ده؟",
                 "options": [
                     "k6 محدود",
                     "وصلت نقطة التشبع (السعة ≈ 400 RPS) — حدد المورد المختنق (اتصالات قاعدة/خيوط/CPU)",
                     "الخادم سريع",
                     "البيانات قليلة",
                 ], "answer": 1,
                 "explain": "منحنى السعة: بعد الركبة، زيادة الحمل ترفع الزمن فقط. شخّص المورد المختنق بالـcounters."},
                {"q": "Gen2 GC كل 30 ثانية في خدمة ويب — إيه أول ما تفحصه؟",
                 "options": [
                     "زيادة الـheap",
                     "تخصيصات كائنات طويلة العمر أو كبيرة (LOH) — مثل تحميل جداول كاملة أو buffers بلا ArrayPool",
                     "تغيير GC لـWorkstation",
                     "إعادة التشغيل الدوري",
                 ], "answer": 1,
                 "explain": "Gen2 = stop-the-world غالبًا. استخدم `dotnet-gcdump`/`gc-verbose` لمعرفة الأنواع والأحجام المسيطرة."},
                {"q": "تحسين جعل الكود أسرع 3 مرات في الـmicro-benchmark، لكن p95 في k6 ما اتغيرش. الاستنتاج؟",
                 "options": [
                     "k6 غير دقيق",
                     "الكود ليس في المسار الساخن (الزمن في SQL/الشبكة/التسلسل) — ارجع للـprofiling ووزّع الجهد صح",
                     "التحسين وهمي",
                     "يلزم حمل أعلى",
                 ], "answer": 1,
                 "explain": "قانون أمدهل (Amdahl) عمليًا: حسّن ما يستهلك الزمن فعلًا. `dotnet-trace` flame graph يوريك النسب الحقيقية."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "بنشمارك لتحسين حقيقي",
                 "md": "اختار عملية حسابية/معالجة بيانات في مشروعك (تسعير، تجميع، تسلسل) واكتب benchmark يقارن التنفيذ الحالي بتنفيذ محسّن (Span/ArrayPool/single-pass). سجّل الجدول الناتج في ملف الأداء.",
                 "criteria": [
                     "`[MemoryDiagnoser]` مفعّل والجدول يحتوي Mean/Ratio/Gen0/Allocated",
                     "النتيجة مستهلَكة (لا DCE) والبيانات واقعية ببذرة ثابتة",
                     "`[Params]` بحجمين على الأقل (صغير/كبير) والنتائج مفسّرة",
                     "تشغيل في Release على جهاز هادئ، مع تسجيل البيئة (CPU/RAM/إصدار .NET)",
                     "استنتاج: هل التحسين يستحق التعقيد؟ (قرار مكتوب)",
                 ],
                 "hint": "لو النسبة قريبة من 1 رغم تحسين واضح: غالبًا البيانات صغيرة جدًا بحيث التخصيص لا يظهر — جرّب حجمًا أكبر أو شوف عمود Allocated."},
                {"id": "t2", "title": "اختبار حمل + تقرير تشخيص",
                 "md": "شغّل k6 بسيناريو `ramping-arrival-rate` على مسارين من API عندك حتى نقطة التشبع. في نفس الوقت راقب `dotnet-counters`. اكتب تقريرًا: السعة، p50/p95/p99، معدل الأخطاء، المورد المختنق، وتوصيتين.",
                 "criteria": [
                     "منحنى/جدول يوضح نقطة الركبة (سعة RPS)",
                     "thresholds معرّفة وممررة أو فشل موثق بسببه",
                     "لقطات من `dotnet-counters` (CPU، time-in-gc، threadpool-queue، connections) أثناء الحمل",
                     "تحديد المورد المختنق بدليل (مش تخمين)",
                     "توصيتان قابلتان للتنفيذ مع الأثر المتوقع",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "BenchmarkDotNet", "url": "https://benchmarkdotnet.org/"},
                {"label": "k6 documentation", "url": "https://grafana.com/docs/k6/"},
                {"label": ".NET diagnostics tools (counters/trace/dump)", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/"},
                {"label": "Runtime metrics — System.Runtime counters", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/available-counters"},
                {"label": "Garbage collection & DATAS", "url": "https://learn.microsoft.com/dotnet/core/runtime-config/garbage-collector"},
                {"label": "ASP.NET Core metrics", "url": "https://learn.microsoft.com/aspnet/core/log-mon/metrics/metrics"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s3-m3-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
كل مرشح بيقول إنه يعرف async. الفرق بين «بعرف أكتب `await`» و«فاهم» بيظهر في الإنتاج:
طلبات بتعلّق تحت الحمل، `Task` بيتسرب، ذاكرة بتزيد بلا سبب، وdeadlock غامض في تطبيق Desktop.

الدرس ده بيشرح **state machine** اللي بيولّدها المترجم، وإزاي thread pool بيتعامل معاها،
وليه `.Result` كارثة، وبعدين ينتقل لتقليل التخصيصات بـ`Span<T>`/`ArrayPool`، وينتهي بـNativeAOT: إمتى يستحق وإمتى لا.
"""},
            {"type": "terms", "items": [
                {"term": "Async State Machine", "def": "بنية يولّدها المترجم لكل دالة async: حالة لكل `await` + `MoveNext()` تستأنف التنفيذ. async ≠ خيط جديد."},
                {"term": "Continuation", "def": "الجزء المتبقي من الدالة بعد `await` — يُجدول على thread pool (أو على SynchronizationContext لو موجود)."},
                {"term": "SynchronizationContext", "def": "آلية إرجاع الاستكمال لسياق واحد (UI thread / ASP.NET القديم). **غير موجود في ASP.NET Core** — وده يغير قواعد `ConfigureAwait`."},
                {"term": "Thread Pool Starvation", "def": "كل الخيوط مشغولة بالانتظار (blocking) → طابور مهام يطول وزمن يرتفع فجأة."},
                {"term": "Sync-over-Async", "def": "`.Result`/`.Wait()`/`.GetAwaiter().GetResult()` على مهمة غير مكتملة — أشهر سبب للاختناق والـdeadlock."},
                {"term": "`ValueTask`", "def": "بديل `Task` لتقليل التخصيص في المسارات الساخنة اللي بتكمل غالبًا بشكل متزامن — بشروط استخدام صارمة."},
                {"term": "`Span<T>` / `Memory<T>`", "def": "عرض لجزء من ذاكرة (مصفوفة/stackalloc/string) بلا نسخ. `Span` نوع stack فقط — **لا يعبر `await`**."},
                {"term": "`ArrayPool<T>`", "def": "إعادة استخدام buffers لتقليل التخصيص وضغط GC — مع تأجير/إرجاع منضبط."},
                {"term": "NativeAOT", "def": "ترجمة كاملة لملف تنفيذي أصلي: إقلاع فوري وذاكرة أقل — مقابل قيود على reflection/dynamic ودعم EF Core."},
                {"term": "Trimming warnings (IL2xxx/IL3xxx)", "def": "تحذيرات المترجم عن كود يعتمد على metadata غير مضمون بعد القص — لازم تُعالج قبل AOT."},
            ]},
            {"type": "heading", "level": 2, "text": "1) اللي بيحصل فعلًا خلف `await`"},
            {"type": "code", "lang": "csharp", "title": "الكود اللي بتكتبه مقابل ما يولّده المترجم (مبسّط)", "code": r'''
// ── ما تكتبه ──
public async Task<decimal> GetTotalAsync(Guid id, CancellationToken ct)
{
    var order = await db.Orders.FindAsync([id], ct);        // نقطة تعليق 1
    if (order is null) return 0m;
    var rate = await rates.GetAsync(order.Currency, ct);    // نقطة تعليق 2
    return order.Total * rate;
}

// ── ما يولّده المترجم (مبسّط جدًا) ──
// [CompilerGenerated] struct <GetTotalAsync>d__12 : IAsyncStateMachine
// {
//     public int <>1__state;               // 0 = قبل await الأول، 1 = بعده، -1 = منتهي
//     public TaskAwaiter<Order?> <>u__1;
//     public TaskAwaiter<decimal> <>u__2;
//     public Order? order; public decimal rate;   // المتغيرات المحلية تُرفع لحقول
//
//     public void MoveNext()
//     {
//         switch (<>1__state) {
//           case 0: goto RESUME_1;
//           case 1: goto RESUME_2;
//         }
//         // ... بدء: أول await
//         var awaiter = db.Orders.FindAsync(...).GetAwaiter();
//         if (!awaiter.IsCompleted) {            // ★ لو اكتملت متزامنًا: لا تعليق إطلاقًا
//             <>1__state = 0; <>u__1 = awaiter;
//             builder.AwaitUnsafeOnCompleted(ref awaiter, ref this);
//             return;                            // ← الخيط يتحرر هنا (بلا blocking!)
//         }
//       RESUME_1:
//         order = <>u__1.GetResult();            // الاستكمال على thread pool
//         // ... await الثاني بنفس النمط
//       RESUME_2:
//         result = order.Total * rate;
//         builder.SetResult(result);
//     }
// }

// الخلاصات العملية:
// ① async لا ينشئ خيطًا — await يحرّر الخيط الحالي ويستأنف لاحقًا (على خيط آخر غالبًا)
// ② لو المهمة اكتملت متزامنًا، الدالة تعمل بلا أي تعليق (ولهذا ValueTask مفيدة)
// ③ المتغيرات المحلية تصير حقولًا في بنية → تخصيص على الكومة لو الدالة «هربت»
// ④ الاستثناءات تُلتقط داخل الـTask (لا تضيع) → await يعيد رميها، .Result يلفها في AggregateException
'''},
            {"type": "heading", "level": 2, "text": "2) `.Result` وthread pool starvation"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Pricing/PricingService.cs", "title": "الأشكال الخطرة وبدائلها", "code": r'''
// ═══ ✗ أشكال sync-over-async ═══
public decimal GetTotalSync(Guid id)
{
    return GetTotalAsync(id, CancellationToken.None).Result;        // ① يلف الاستثناء في AggregateException
}
public decimal GetTotalSync2(Guid id)
{
    return GetTotalAsync(id, CancellationToken.None).GetAwaiter().GetResult();  // ② استثناء أنظف لكن نفس الحجب
}
public decimal GetTotalSync3(Guid id)
{
    return Task.Run(() => GetTotalAsync(id, CancellationToken.None)).Result;    // ③ أسوأ: خيطين محجوبين
}

// لماذا كارثة؟ كل نداء يحجز خيطًا من thread pool في **انتظار** (لا عمل).
// تحت الحمل: الـpool يستهلك خيوطه، ثم يحقن خيوطًا جديدة بمعدل بطيء (~1/ثانية بعد الحد الأدنى)
// → طابور المهام يطول، والزمن يقفز من 50ms إلى ثوانٍ، وقد تصل لفشل كامل.
// التشخيص: `dotnet-counters` → threadpool-queue-length مرتفع + thread-count يصعد ببطء.

// ═══ ✓ الحلول ═══
// ① الأفضل: اجعل المسار كاملًا async (من الـendpoint للقاعدة)
public Task<decimal> GetTotalAsync(Guid id, CancellationToken ct) => /* ... */ Task.FromResult(0m);

// ② لو مضطر لواجهة متزامنة (حدث مكتبة قديمة): اعزل في خيط مخصص ولا تحجب thread pool
public decimal GetTotalLegacy(Guid id)
{
    return Task.Run(async () => await GetTotalAsync(id, CancellationToken.None))
               .GetAwaiter().GetResult();          // مقبول **فقط** في مسار نادر/خارج الطلب
}

// ③ مكتبات: لا تستخدم ConfigureAwait(false) كحل للحجب — بل وفّر واجهة متزامنة أصلًا إن لزم
//    (في ASP.NET Core لا يوجد SynchronizationContext، فـConfigureAwait(false) غالبًا بلا أثر)

// ═══ ✗ deadlock الكلاسيكي (يحدث مع SynchronizationContext) ═══
// في WPF/WinForms/ASP.NET القديم:
private void Button_Click(object sender, EventArgs e)
{
    var data = LoadAsync().Result;          // UI thread محجوب
}
private async Task<string> LoadAsync()
{
    await Task.Delay(100);                  // الاستكمال يريد العودة لـUI thread… وهو محجوب → deadlock
    return "data";
}
// في ASP.NET Core: لا SynchronizationContext → لا deadlock بهذا الشكل، لكن الحجب والاستنزاف قائمان.
'''},
            {"type": "table", "head": ["النمط", "الحكم", "البديل/التصحيح"], "rows": [
                ["`.Result` / `.Wait()` على I/O", "✗ ممنوع في مسار الطلب", "اجعل المسار async بالكامل"],
                ["`async void`", "✗ إلا في معالجات الأحداث", "`async Task` — الاستثناء في async void يقتل العملية"],
                ["fire-and-forget (`_ = DoAsync()`)", "✗ استثناءات غير مراقبة", "Channel + BackgroundService، أو `Task.Run` مع try/catch وسجل"],
                ["`Task.Run` داخل ASP.NET لمجرد «توازي»", "✗ يستهلك خيطًا بلا فائدة", "نادِ الدالة async مباشرة"],
                ["`Task.WhenAll` بلا `await` في نفس الـscope", "△ استثناءات مفقودة", "`await Task.WhenAll(...)` داخل try، وافحص `Task.Exception`"],
                ["حلقة `await` متسلسلة على عناصر مستقلة", "△ بطيء (تسلسل بلا داعٍ)", "`Parallel.ForEachAsync` بحد توازي أو WhenAll بدفعات"],
                ["`ValueTask` مخزّنة/منتظرة مرتين", "✗ سلوك غير معرّف", "استخدم `Task` إلا لو قِست فائدة حقيقية"],
                ["`CancellationToken` غير مُمرَّر", "✗ تسريب موارد بعد الإلغاء", "مرّره في كل نداء I/O"],
                ["`new CancellationTokenSource()` بلا dispose", "△ تسريب مقبض", "`using`/`await using` دائمًا"],
            ]},
            {"type": "heading", "level": 2, "text": "3) التوازي والإلغاء الصحيحان"},
            {"type": "code", "lang": "csharp", "title": "WhenAll، حدود التوازي، وtimeouts", "code": r'''
// ═══ WhenAll: استثناءات متعددة، أول واحد فقط يُرمى ═══
public async Task<EnrichedOrder> EnrichAsync(Guid orderId, CancellationToken ct)
{
    var orderTask = orders.GetAsync(orderId, ct);
    var customerTask = customers.GetAsync(orderId, ct);
    var ratesTask = rates.GetTableAsync(ct);

    try { await Task.WhenAll(orderTask, customerTask, ratesTask); }
    catch (Exception)
    {
        // ✓ سجل كل الاستثناءات، لا الأول فقط
        foreach (var t in new[] { orderTask, customerTask, ratesTask })
            if (t.IsFaulted) log.LogError(t.Exception, "sub-task failed");
        throw;
    }

    return new EnrichedOrder(orderTask.Result, customerTask.Result, ratesTask.Result);
    // ✓ .Result هنا آمنة: المهام اكتملت بعد WhenAll (لا حجب)
}

// ═══ حدود التوازي: لا تفتح 10,000 نداء متزامن ═══
public async Task<IReadOnlyList<Product>> FetchAllAsync(IReadOnlyList<Guid> ids, CancellationToken ct)
{
    var results = new Product[ids.Count];

    await Parallel.ForEachAsync(ids.Select((id, i) => (id, i)),
        new ParallelOptions { MaxDegreeOfParallelism = 8, CancellationToken = ct },
        async (item, token) => results[item.i] = await catalog.GetAsync(item.id, token));

    return results;
}

// ═══ timeout مستقل عن الإلغاء الخارجي ═══
public async Task<Price?> TryGetPriceAsync(string sku, CancellationToken ct)
{
    using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
    timeout.CancelAfter(TimeSpan.FromSeconds(2));       // ✓ سقف زمني محلي

    try { return await pricing.GetAsync(sku, timeout.Token); }
    catch (OperationCanceledException) when (!ct.IsCancellationRequested)
    {
        log.LogWarning("pricing timed out for {Sku}; using fallback", sku);
        Metrics.Timeouts.Add(1, new("dependency", "pricing"));
        return null;                                     // ← تدهور مقصود، لا فشل
    }
}

// ═══ .NET 6+: WaitAsync (أنظف من linked CTS للمهام البسيطة) ═══
var result = await longRunning.GetAsync(ct).WaitAsync(TimeSpan.FromSeconds(5));

// ═══ fire-and-forget الصحيح (لو مضطر) ═══
_ = Task.Run(async () =>
{
    try { await notifier.SendAsync(message, appLifetime.ApplicationStopping); }
    catch (Exception ex) { log.LogError(ex, "background notification failed"); }   // ★ لا تبتلع بصمت
}, CancellationToken.None);
// الأفضل معماريًا: Channel + BackgroundService (درس المرحلة 2) — بلا فقد وبلا استثناءات طائرة
'''},
            {"type": "heading", "level": 2, "text": "4) تقليل التخصيصات: Span وArrayPool"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Parsing/CsvParser.cs", "title": "قبل/بعد مع أرقام توجيهية", "code": r'''
// ═══ ✗ النمط المعتاد: تخصيصات لكل سطر ═══
public static OrderLine ParseNaive(string line)
{
    var parts = line.Split(',');                          // ① مصفوفة جديدة
    var sku = parts[0].Trim();                            // ② string جديد (Trim)
    var qty = int.Parse(parts[1].Trim());                 // ③ string جديد + parse
    var price = decimal.Parse(parts[2].Trim());           // ④ نفس الشيء
    return new OrderLine(Guid.Empty, sku, qty, price);
}

// ═══ ✓ Span: صفر تخصيص (للسطور القصيرة) ═══
public static OrderLine ParseSpan(ReadOnlySpan<char> line)
{
    var rest = line;
    var sku = NextField(ref rest);                        // slice = عرض، لا نسخة
    var qty = int.Parse(NextField(ref rest));             // ★ int.Parse(ReadOnlySpan<char>) موجود
    var price = decimal.Parse(NextField(ref rest), NumberStyles.Number, CultureInfo.InvariantCulture);

    return new OrderLine(Guid.Empty, sku.ToString(), qty, price);   // ToString فقط لما يلزم string
}

private static ReadOnlySpan<char> NextField(ref ReadOnlySpan<char> rest)
{
    var idx = rest.IndexOf(',');
    if (idx < 0) { var last = rest.Trim(); rest = default; return last; }

    var field = rest[..idx].Trim();                       // ✓ slicing بلا تخصيص
    rest = rest[(idx + 1)..];
    return field;
}

// ═══ ✓ ArrayPool للـbuffers الكبيرة/المتكررة ═══
public static async Task<byte[]> ReadUpToAsync(Stream stream, int maxBytes, CancellationToken ct)
{
    var buffer = ArrayPool<byte>.Shared.Rent(maxBytes);   // ✓ استأجر بدل new
    try
    {
        var read = await stream.ReadAsync(buffer.AsMemory(0, maxBytes), ct);
        return buffer.AsSpan(0, read).ToArray();          // انسخ فقط الحجم المقروء
    }
    finally
    {
        ArrayPool<byte>.Shared.Return(buffer);            // ★ أرجعه دائمًا (في finally)
    }
}

// ═══ ✓ string.Create لتكوين نص بلا StringBuilder (لحالات ثابتة الشكل) ═══
public static string FormatOrderRef(Guid id, int year) =>
    string.Create(12, (id, year), (chars, state) =>
    {
        var hex = state.id.ToString("N");
        hex.AsSpan(0, 8).CopyTo(chars);
        chars[8] = '-';
        state.year.TryFormat(chars[9..], out _, "D3");
    });

// أرقام توجيهية (BenchmarkDotNet، سطر CSV نموذجي، 100k سطر):
//   ParseNaive : ~ 24 ms   Gen0: 3.9 MB allocated
//   ParseSpan  : ~  9 ms   Gen0: 0.4 MB allocated   (التخصيص من ToString النهائي فقط)
// ★ قِس في مشروعك: التحسين يستحق فقط لو المسار ساخن فعلًا.
'''},
            {"type": "callout", "kind": "danger", "title": "قواعد `Span<T>` التي لا تُكسر",
             "md": """
- **`Span` نوع `ref struct`** → يعيش على الـstack فقط: لا يُخزَّن في حقل كلاس، لا يُصندَق (boxing)،
  و**لا يعبر `await`/`yield`**. لو محتاج تحتفظ به عبر تعليق → استخدم `Memory<T>`.
- **لا تُرجع Span لبيانات مؤقتة** (مثل `stackalloc` أو buffer مُستأجر رُجّع) → dangling/قراءة ذاكرة محررة.
- **`ArrayPool.Rent` يرجع مصفوفة أكبر من المطلوب** → تابع الطول بنفسك (`AsSpan(0, length)`).
- **`Return` في `finally` دائمًا** — وإلا تسريب من الـpool (وفقدان الفائدة).
- **لا تكتب فوق بيانات مُؤجَّرة مشتركة** (إلا لو `clearArray: true` مهمًا لك) — البيانات القديمة ممكن تُقرأ.
- **`stackalloc` بحدود**: مساحات كبيرة على الـstack → `StackOverflowException`. القاعدة: ≤ 1KB تقريبًا، وإلا استخدم pool.
"""},
            {"type": "heading", "level": 2, "text": "5) NativeAOT: إمتى يستحق"},
            {"type": "table", "head": ["المعيار", "JIT (الافتراضي)", "ReadyToRun", "NativeAOT"], "rows": [
                ["زمن الإقلاع", "متوسط (تسخين JIT)", "أسرع", "**فوري** (بلا JIT)"],
                ["استهلاك الذاكرة", "متوسط", "متوسط", "أقل بوضوح"],
                ["حجم الملف", "صغير", "أكبر", "أكبر (ملف أصلي واحد)"],
                ["ذروة الأداء (throughput)", "الأفضل عادة (Dynamic PGO)", "قريب", "أقل قليلًا (بلا PGO زمني)"],
                ["Reflection/dynamic", "كامل", "كامل", "**محدود** — يحتاج source generation/annotations"],
                ["EF Core", "مدعوم", "مدعوم", "**غير مدعوم عمليًا** (يعتمد على proxies/reflection)"],
                ["System.Text.Json", "كامل", "كامل", "يحتاج `JsonSerializerContext` (source gen)"],
                ["أنسب حالة", "خدمات ويب/تطبيقات EF", "تقليل إقلاع مع دعم كامل", "CLI tools، serverless، sidecars، كثافة عالية"],
            ]},
            {"type": "code", "lang": "xml", "filename": "Shop.Worker.csproj", "title": "تفعيل AOT + التعامل مع التحذيرات", "code": r'''
<Project Sdk="Microsoft.NET.Sdk.Worker">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <PublishAot>true</PublishAot>

    <!-- ★ اجعل تحذيرات القص/AOT أخطاء في CI — وإلا تكتشفها وقت النشر فقط -->
    <TrimmerSingleWarn>false</TrimmerSingleWarn>
    <EnableTrimAnalyzer>true</EnableTrimAnalyzer>
    <EnableAotAnalyzer>true</EnableAotAnalyzer>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>

    <IlcOptimizationPreference>Speed</IlcOptimizationPreference>
    <InvariantGlobalization>true</InvariantGlobalization>
  </PropertyGroup>
</Project>
'''},
            {"type": "code", "lang": "csharp", "title": "التسلسل مع source generation (شرط AOT) + annotations", "code": r'''
// ✓ سياق تسلسل مولّد — يعمل في AOT بلا reflection
[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull)]
[JsonSerializable(typeof(WorkItem))]
[JsonSerializable(typeof(IReadOnlyList<WorkItem>))]
internal partial class AppJsonContext : JsonSerializerContext;

var json = JsonSerializer.Serialize(item, AppJsonContext.Default.WorkItem);
var back = JsonSerializer.Deserialize(json, AppJsonContext.Default.WorkItem);

// ✓ لو مكتبتك تحتاج أنواعًا غير معروفة وقت الترجمة: وثّق المتطلب بالـannotations
[RequiresUnreferencedCode("يعتمد على reflection لتحديد الخصائص")]
[RequiresDynamicCode("يولّد كودًا في وقت التشغيل")]
public static object MapDynamic(Type targetType, IDictionary<string, object?> source) => /* ... */ null!;

// ✓ بديل متوافق مع AOT: اعتماد على types معروفة + generics
public static T Map<T>(IDictionary<string, object?> source) where T : class, new() => /* ... */ new T();

// النشر والقياس
//   dotnet publish -c Release -r linux-x64
//   قبل/بعد: قِس زمن الإقلاع (من أول سطر لـ"listening") والذاكرة (RSS بعد الاستقرار)
//   وجرّب **كل** المسارات: AOT يكشف مشاكله وقت التشغيل (reflection ناقص) لا وقت الترجمة
'''},
            {"type": "callout", "kind": "note", "title": "ConfigureAwait(false): الحقيقة في .NET الحديث",
             "md": """
- **ASP.NET Core**: لا يوجد `SynchronizationContext` → `ConfigureAwait(false)` **بلا أثر عملي** في كود التطبيق.
- **مكتبات عامة** (NuGet يستهلكها WPF/WinForms/أدوات): ضعها كعادة دفاعية، أو الأفضل استخدم
  `ConfigureAwait(ConfigureAwaitOptions.ForceYielding)` (.NET 8+) لما تريد تحرير الخيط صراحة.
- **لا تستخدمها كحل لمشكلة حجب** (`.Result`) — هي لا تمنع starvation.
- الأهم من كل ده: **لا تخلط async مع sync** في مسار الطلب.
"""},
            {"type": "code", "lang": "csharp", "title": "ValueTask: إمتى تستحق وشروطها", "code": r'''
// ✓ تستحق: مسار ساخن يكمل متزامنًا في أغلب المرات (كاش ذاكرة، قراءة buffer)
public ValueTask<Product?> GetCachedAsync(Guid id, CancellationToken ct)
{
    if (_cache.TryGetValue(id, out var product))
        return ValueTask.FromResult(product);              // صفر تخصيص (بدل Task allocation)

    return new ValueTask<Product?>(LoadFromDbAsync(id, ct));
}

// قواعد صارمة:
// ① انتظرها مرة واحدة فقط (`await` واحد) — لا تخزنها ولا تعد انتظارها
// ② لا تستخدم `.Result`/`.GetAwaiter()` قبل التأكد من الاكتمال
// ③ لا ترجع ValueTask لو المسار دايما غير متزامن (لا فائدة، وتعقيد إضافي)
// ④ في الواجهات العامة: `Task` أوضح للمستهلك إلا لو الفائدة مقيسة

// ✗ خطأ شائع
var vt = GetCachedAsync(id, ct);
var a = await vt;
var b = await vt;      // ← سلوك غير معرّف (قد يرمي أو يعطي نتيجة خاطئة)
'''},
            {"type": "checkpoints", "items": [
                "أشرح ما يولّده المترجم لـasync (state machine/continuations) وأعرف إن `await` لا يحجز خيطًا.",
                "أتجنب sync-over-async وأشخّص thread pool starvation بالـcounters وأعرف بدائل كل نمط.",
                "أدير التوازي والإلغاء والمهل بشكل صحيح (`WhenAll` بحدود، linked CTS، `WaitAsync`).",
                "أقلل التخصيصات بـ`Span<T>`/`ArrayPool` في المسارات الساخنة، وأقيّم NativeAOT بمعيار واضح.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`await` بيعمل إيه بالخيط الحالي؟",
                 "options": [
                     "يحجبه حتى تكتمل المهمة",
                     "يحرّره ليعمل في شيء آخر، ويستأنف الدالة كـcontinuation على thread pool عند الاكتمال",
                     "ينشئ خيطًا جديدًا دائمًا",
                     "ينقل التنفيذ لخيط UI",
                 ], "answer": 1,
                 "explain": "ده جوهر async: لا حجز خيوط أثناء الانتظار. ولو المهمة اكتملت متزامنًا، الاستمرار فوري بلا تعليق."},
                {"q": "`.Result` في ASP.NET Core — إيه الخطر الحقيقي؟",
                 "options": [
                     "deadlock بسبب SynchronizationContext",
                     "thread pool starvation (حجز خيوط في الانتظار) + بطء حقن الخيوط → قفزات زمن وفشل تحت الحمل",
                     "استثناءات مفقودة",
                     "لا خطر",
                 ], "answer": 1,
                 "explain": "الـdeadlock الكلاسيكي يحتاج SynchronizationContext (غير موجود هنا)، لكن الاستنزاف قائم وأخطر لأنه يظهر فقط تحت الحمل."},
                {"q": "`async void` ليه خطر؟",
                 "options": [
                     "أبطأ",
                     "الاستثناء يهرب للـSynchronizationContext وينهي العملية — ولا يمكن انتظاره",
                     "لا يعمل مع CancellationToken",
                     "يستهلك ذاكرة",
                 ], "answer": 1,
                 "explain": "استخدمه فقط في معالجات الأحداث. أي شيء آخر: `async Task` (أو `ValueTask`)."},
                {"q": "`Span<T>` لا يمكن استخدامه عبر `await` — ليه والبديل؟",
                 "options": [
                     "قياس أداء؛ البديل `Memory<T>`",
                     "لأنه `ref struct` (stack-only) والدالة async تُرفع حالتها لكائن على الكومة؛ البديل `Memory<T>`/`ReadOnlyMemory<T>`",
                     "خطأ ترجمة؛ البديل `byte[]`",
                     "لا سبب؛ البديل `Task`",
                 ], "answer": 1,
                 "explain": "حالة الدالة async تُخزَّن في state machine على الكومة، و`Span` لا يُخزَّن هناك. `Memory<T>` هو النسخة الآمنة للـheap."},
                {"q": "متى NativeAOT قرار صحيح؟",
                 "options": [
                     "دائمًا — أسرع",
                     "أدوات CLI/serverless/sidecars تحتاج إقلاعًا فوريًا وذاكرة أقل، ولا تعتمد على reflection/EF Core",
                     "لأي API مع EF Core",
                     "لتقليل حجم الـrepo",
                 ], "answer": 1,
                 "explain": "المقايضة: إقلاع/كثافة أفضل مقابل قيود على reflection وديناميكية، ودعم EF Core غير عملي. خدمة ويب كاملة بـEF → ابقَ على JIT (+R2R لو الإقلاع يهمك)."},
                {"q": "`ValueTask` تستحق إمتى؟",
                 "options": [
                     "دائمًا بدل Task",
                     "مسار ساخن يكتمل متزامنًا غالبًا (كاش ذاكرة) مع الالتزام بانتظارها مرة واحدة فقط",
                     "للدوال الطويلة",
                     "في الواجهات العامة دائمًا",
                 ], "answer": 1,
                 "explain": "الفائدة: تجنب تخصيص Task. الثمن: قواعد استخدام صارمة. بلا قياس، `Task` أوضح وأأمن."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تطهير sync-over-async",
                 "md": "ابحث في مشروعك عن كل `.Result`/`.Wait()`/`GetAwaiter().GetResult()` و`async void` (خارج معالجات الأحداث)، وأصلحها بجعل المسارات async بالكامل. أضف قاعدة تحليل (`.editorconfig`/analyzer) تمنع عودتها.",
                 "criteria": [
                     "`grep -rn \"\\.Result\\b\\|\\.Wait()\\|GetAwaiter().GetResult()\"` يرجع صفر نتائج في مسار الطلب (أو موثقة بمبرر)",
                     "لا `async void` إلا في معالجات أحداث",
                     "قاعدة analyzer/.editorconfig تمنع الأنماط دي في CI",
                     "اختبار حمل بعد التغيير يُظهر `threadpool-queue-length` مستقرًا تحت نفس الحمل",
                 ],
                 "hint": "لو فيه مكتبة قديمة تفرض واجهة متزامنة: وفّر مسارًا async موازيًا في كودك، واستخدم العزل (خيط مخصص) في المسار النادر فقط — مش في مسار الطلب."},
                {"id": "t2", "title": "تقليل تخصيصات في مسار ساخن",
                 "md": "اختار مسار معالجة نصوص/بايتات ساخن (parsing، تسلسل، قراءة ملف) وأعد كتابته بـ`Span<T>`/`ArrayPool`. قِس بـBenchmarkDotNet (Mean + Allocated) وسجّل الفرق، ثم تحقق إن p95 في اختبار الحمل تحسّن.",
                 "criteria": [
                     "benchmark بـ`[MemoryDiagnoser]` يظهر انخفاض Allocated بنسبة مسجلة",
                     "لا `Span` مخزّن في حقل ولا عابر لـ`await` (مراجعة)",
                     "`ArrayPool.Return` داخل `finally`",
                     "اختبارات الوحدة تغطي الحالات الحدّية (مدخلات ناقصة/فارغة/بلا فواصل)",
                     "قرار: هل التحسين يستحق التعقيد؟ (مكتوب)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Async programming in .NET", "url": "https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/"},
                {"label": "Task asynchronous programming model", "url": "https://learn.microsoft.com/dotnet/csharp/programming-guide/concepts/async/task-asynchronous-programming-model"},
                {"label": "ConfigureAwait FAQ / .NET 8 options", "url": "https://learn.microsoft.com/dotnet/api/system.threading.tasks.configureawaitoptions"},
                {"label": "Span<T> and Memory<T>", "url": "https://learn.microsoft.com/dotnet/standard/memory-and-spans/"},
                {"label": "ArrayPool<T>", "url": "https://learn.microsoft.com/dotnet/api/system.buffers.arraypool-1"},
                {"label": "NativeAOT deployment", "url": "https://learn.microsoft.com/dotnet/core/deploying/native-aot/"},
                {"label": "ValueTask guidance", "url": "https://learn.microsoft.com/dotnet/api/system.threading.tasks.valuetask-1"},
            ]},
        ],
    },
]
