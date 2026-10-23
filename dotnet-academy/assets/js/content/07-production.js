/* الوحدة 8 — الأداء والإنتاج: التخزين المؤقت، الذاكرة، والنشر. */
Academy.addModule({
  id: "production",
  title: "الأداء والإنتاج",
  tagline: "الكود الذي يعمل على جهازك ليس بالضرورة جاهزًا للإنتاج. هنا نصنع الفرق في الزمن والذاكرة والتشغيل.",
  icon: "▲",
  color: "#a3e635",
  lessons: [
    {
      id: "caching",
      title: "Caching: OutputCache + HybridCache والإبطال",
      duration: 26,
      level: "متقدم",
      summary:
        "التخزين المؤقت أسرع تحسين وأخطر عيب. سنفهم ماذا نcache، وكيف نُبطل بأمان، ولماذا Invalidation أهم من TTL.",
      keywords: ["OutputCache", "HybridCache", "Redis", "invalidation", "stampede", "TTL"],
      objectives: [
        "تميّز بين Response وOutput وDistributed وHybrid Cache.",
        "تضبط سياسة Output Cache مع Vary وTags.",
        "تُبطل الكاش عند الكتابة بدقة.",
        "تتجنب تسريب بيانات مستخدم أو Cache Stampede.",
      ],
      concept: `
        <p>هناك طبقات تخزين مؤقت مختلفة، وخلطها يسبب أخطاء غريبة:</p>
        <ul>
          <li><strong>Response Caching</strong>: ترويسات HTTP (<code>Cache-Control</code>) التي يفهمها المتصفح وCDN. لا يخزّن الخادم شيئًا بالضرورة.</li>
          <li><strong>Output Caching</strong>: Middleware داخل ASP.NET Core يخزّن الاستجابة كاملة على الخادم أو في مخزن موزّع، ويُعيدها دون تنفيذ الـ endpoint.</li>
          <li><strong>In-Memory Cache</strong>: <code>IMemoryCache</code> لتخزين كائنات داخل العملية.</li>
          <li><strong>Distributed Cache</strong>: Redis/SQL لتخزين مشترك بين نسخ التطبيق.</li>
          <li><strong>HybridCache</strong>: طبقة L1 في الذاكرة + L2 موزّعة، مع حماية من التسابق ووسوم للإبطال (متاحة في .NET 9+).</li>
        </ul>
        <h3>ماذا نcache؟</h3>
        <p>البيانات المقروءة كثيرًا والمتغيّرة قليلًا: قائمة تصنيفات، تفاصيل منتج، إعدادات عامة. لا تcache: استجابات مخصصة لمستخدم دون Vary صحيح، ولا نتائج بحث حساسة، ولا أخطاء عابرة.</p>
        <h3>TTL ليس استراتيجية</h3>
        <p>اختيار «60 ثانية» عشوائيًا يعني إما بيانات قديمة أو كاش بلا فائدة. الاستراتيجية الحقيقية:</p>
        <ol>
          <li>حدّد مفتاحًا دقيقًا (المسار + query + اللغة + المستخدم عند اللزوم).</li>
          <li>حدّد مدة قصوى (TTL) كشبكة أمان.</li>
          <li>أبطل عند الكتابة باستخدام <strong>Tags</strong>، لا بالاعتماد على انتهاء المدة.</li>
        </ol>
        <h3>Cache Stampede</h3>
        <p>عند انتهاء مفتاح ساخن، تحاول مئات الطلبات إعادة بنائه في آن واحد، فتنهار قاعدة البيانات. الحلول: قفل موزّع (Single Flight)، أو <code>HybridCache</code> الذي يوفّر حماية مدمجة، أو إضافة jitter للمدة. لا تفترض أن TTL يحل المشكلة.</p>
      `,
      compare: {
        intro: `<p>الطريقة اليدوية تكرّر منطق الكاش في كل خدمة وتنسى الإبطال. سياسة OutputCache تجمع كل ذلك في تعريف واحد.</p>`,
        before: {
          label: "MemoryCache يدوي",
          lang: "csharp",
          title: "ProductsService.cs",
          code: `public async Task<List<ProductDto>> ListAsync(CancellationToken ct)
{
    if (_cache.TryGetValue("products", out List<ProductDto>? cached))
        return cached!;

    var items = await _db.Products
        .AsNoTracking()
        .Select(p => new ProductDto(p.Id, p.Name, p.Price))
        .ToListAsync(ct);

    _cache.Set("products", items, TimeSpan.FromMinutes(5));
    return items;
}

public async Task CreateAsync(CreateProductRequest request, CancellationToken ct)
{
    // ... إضافة المنتج
    await _db.SaveChangesAsync(ct);

    // نسيان إبطال الكاش = بيانات قديمة
}`,
          points: [
            "مفتاح واحد لكل الصفحات والحالات.",
            "الإبطال مسؤولية منسية في كل عملية كتابة.",
            "لا حماية من التسابق بين النسخ.",
          ],
        },
        after: {
          label: "OutputCache + Tags",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services.AddOutputCache(options =>
{
    options.AddPolicy("products:list", policy => policy
        .Expire(TimeSpan.FromSeconds(60))
        .SetVaryByQuery("page", "size", "categoryId")
        .Tag("products"));
});

var app = builder.Build();
app.UseOutputCache();

var products = app.MapGroup("/api/v1/products");

products.MapGet("/", async (
    int page, int size, IProductReadService service, CancellationToken ct) =>
        TypedResults.Ok(await service.ListAsync(page, size, ct)))
    .CacheOutput("products:list");

products.MapPost("/", async (
    CreateProductRequest request,
    IProductService service,
    IOutputCacheStore cache,
    CancellationToken ct) =>
{
    var created = await service.CreateAsync(request, ct);
    await cache.EvictByTagAsync("products", ct); // إبطال دقيق
    return TypedResults.Created($"/api/v1/products/{created.Id}", created);
});`,
          points: [
            "سياسة واحدة تُطبَّق على كل الطلبات المطابقة.",
            "VaryByQuery يمنع خلط الصفحات.",
            "إبطال بالوسم عند الكتابة.",
          ],
        },
        verdict: `<p>الـ Output Cache يخزّن <em>الاستجابة</em> لا الكائن. هذا يعني أنه يتجاوز تنفيذ الـ endpoint والاستعلام كليهما. لكنه أيضًا يخزّن الأخطاء إذا لم تُضبط السياسة، ويسرّب البيانات إذا نسيت <code>VaryByHeader</code> أو المصادقة. راجع السياسة قبل النشر.</p>`,
      },
      walkthrough: [
        {
          title: "Output Cache",
          code: `builder.Services.AddOutputCache(options =>\n{\n    options.AddBasePolicy(b => b.Expire(TimeSpan.FromSeconds(30)));\n});\n\napp.UseOutputCache();\n\ngroup.MapGet("/products", GetProducts)\n    .CacheOutput("products");`,
          lang: "csharp",
          body: `<p>Output Cache يخزن الاستجابة كاملة. مناسب للكتالوج العام. لا تستخدمه لبيانات مستخدم دون مفتاح صحيح. حدد مدة قصيرة. أضف سياسة باسم واضح. اختبر أن التحديث يظهر بعد الإبطال/الانتهاء.</p>`
        },
        {
          title: "سياسة مخصصة",
          code: `options.AddPolicy("products", policy => policy\n    .Expire(TimeSpan.FromSeconds(60))\n    .SetVaryByQuery("page", "search")\n    .Tag("catalog"));`,
          lang: "csharp",
          body: `<p><code>VaryByQuery</code> يمنع خلط الصفحات. <code>Tag</code> يسمح بالإبطال الجماعي. لا تنسَ headers مثل اللغة/العملة. اختبر مفاتيح مختلفة. لا تخزن استجابة بناءً على Authorization دون Vary صحيح.</p>`
        },
        {
          title: "Hybrid Cache",
          code: `var product = await cache.GetOrCreateAsync(\n    $"product:{id}",\n    async ct => await db.Products.AsNoTracking()\n        .Select(p => new ProductDto(p.Id, p.Name, p.Price.Amount))\n        .SingleOrDefaultAsync(p => p.Id == id, ct),\n    cancellationToken: ct);`,
          lang: "csharp",
          body: `<p>HybridCache يجمع ذاكرة محلية + توزيع. المفتاح يجب أن يشمل الإصدار/اللغة. القيمة DTO صغيرة. لا تخزن <code>DbContext</code>. تعامل مع null. أضف مدة. لا تجعل الكاش مصدر الحقيقة.</p>`
        },
        {
          title: "تصميم المفتاح",
          code: `catalog:v1:product:{id}:currency:SAR\norders:user:{userId}:page:{page}\n// لا: "products" فقط`,
          lang: "text",
          body: `<p>المفتاح يحدد التجزئة. أضف الإصدار والعملة/اللغة وأي بُعد يغيّر النتيجة. مفتاح عام لبيانات مستخدم = تسريب. لا تضع PII في المفتاح إن ظهر في logs. وثّق المفاتيح.</p>`
        },
        {
          title: "الإبطال",
          code: `await cache.RemoveAsync($"product:{id}", ct);\nawait outputCache.EvictByTagAsync("catalog", ct);`,
          lang: "csharp",
          body: `<p>الإبطال أصعب من التخزين. أبطِل عند التعديل. استخدم tags للمجموعات. لا تعتمد على TTL فقط لبيانات حساسة. اختبر التحديث. في التوزيع، تأكد أن الإبطال يصل للنسخ. لا تنسَ النسخ الاحتياطية/الطبقات.</p>`
        },
        {
          title: "Stampede",
          code: `// استخدم قفلًا/دمجًا لمنع عشرات الحسابات المتزامنة لنفس المفتاح\nvar value = await cache.GetOrCreateAsync(key, factory,\n    new HybridCacheEntryOptions { Expiration = TimeSpan.FromMinutes(5) });`,
          lang: "csharp",
          body: `<p>عند انتهاء مفتاح ساخن، قد تحاول طلبات كثيرة إعادة حسابه. HybridCache/قفل موزع يقلل ذلك. أضف jitter للمدة. لا تضع قفلًا عالميًا يوقف كل الطلبات. راقب cache miss.</p>`
        },
        {
          title: "لا تخزّن الخاص",
          code: `// خطأ\napp.MapGet("/me/orders", GetMyOrders).CacheOutput();\n\n// صحيح: مفتاح/سياسة خاصة أو بلا كاش\napp.MapGet("/me/orders", GetMyOrders).CacheOutput(p => p\n    .SetVaryByHeader("Authorization"));`,
          lang: "csharp",
          body: `<p>الاستجابة الخاصة لا تُخزّن في كاش عام. <code>VaryByHeader</code> قد ينفع لكنه قد يخزن نسخة لكل توكن. الأفضل كاش على مستوى بيانات المستخدم بمفتاح userId. لا تخلط مستخدمين. اختبر مستخدمين.</p>`
        },
        {
          title: "قِس",
          code: `# راقب hit rate وp95 وذاكرة الكاش\n# قارن قبل/بعد\n# اختبر إبطال ونشر`,
          lang: "bash",
          body: `<p>الكاش ليس نجاحًا تلقائيًا. قِس hit rate والزمن والذاكرة. إذا كانت الإصابة منخفضة، راجع المفاتيح/المدة. الإبطال الخاطئ أسوأ من عدم الكاش. اختبر سيناريو تحديث. لا تخزن بيانات لا تتغير؟ وثّق.</p>`
        }
      ],
      internals: `
        <p><code>OutputCacheMiddleware</code> يبني مفتاحًا من: المسار، الـ query المحدد، الهيدرات المحددة، واسم السياسة. عند وجود إصابة (Hit)، يكتب الاستجابة المخزّنة ويعيدها. عند الغياب (Miss)، يلتقط الاستجابة في <code>MemoryStream</code> أو مخزن، ثم يخزّنها بعد اكتمالها. هذا يعني أن الاستجابات الكبيرة تستهلك ذاكرة إضافية أثناء الالتقاط.</p>
        <p><code>IOutputCacheStore</code> هو تجريد المخزن. الافتراضي في الذاكرة، ويمكن استبداله بـ Redis عبر حزمة <code>Microsoft.AspNetCore.OutputCaching.StackExchangeRedis</code>. الوسوم (Tags) تُخزَّن كعلاقة بين المفتاح والوسم، و<code>EvictByTagAsync</code> يمسح كل المفاتيح المرتبطة.</p>
        <p><strong>HybridCache</strong> يختلف: يخزّن <em>قيمًا</em> لا استجابات، ويجمع L1 (ذاكرة العملية) وL2 (موزّع). يستخدم <code>GetOrCreateAsync</code> مع قفل داخلي يمنع عشرات الطلبات من إعادة بناء نفس القيمة، ويوفّر وسومًا للإبطال. مناسب للاستعلامات المكلفة داخل الخدمات.</p>
        <p>الإبطال الموزّع ليس فوريًا في كل الحالات: L1 في نسخة أخرى قد تحتفظ بالقيمة حتى انتهاء <code>LocalCacheExpiration</code> أو وصول إشعار. اختر مدة L1 قصيرة (ثوانٍ) إذا كانت حداثة البيانات حرجة.</p>
      `,
      internalsTable: {
        head: ["النوع", "يخزّن", "يُشارَك بين النسخ؟"],
        rows: [
          ["Response Cache", "ترويسات للعميل/CDN", "نعم عبر CDN"],
          ["Output Cache (memory)", "استجابة كاملة", "لا"],
          ["Output Cache (Redis)", "استجابة كاملة", "نعم"],
          ["IMemoryCache", "كائنات", "لا"],
          ["HybridCache", "قيم + L1/L2", "نعم عبر L2"],
        ],
      },
      tips: [
        {
          title: "لا تcache استجابات مصادقة",
          body: "إن كان المسار يعيد بيانات المستخدم، لا تخزّنه على مستوى مشترك. استخدم VaryByHeader على Authorization أو تجنّب الكاش كليًا.",
        },
        {
          title: "أبطل بالوسم لا بالوقت",
          body: "عند إنشاء/تعديل/حذف منتج، استدعِ <code>EvictByTagAsync(\"products\")</code>. TTL يبقى شبكة أمان، لا آلية تحديث.",
        },
        {
          title: "أضف jitter",
          body: "إن انتهت كل المفاتيح في نفس اللحظة، سيتزامن الحمل. أضف عشوائية صغيرة للمدة أو استخدم HybridCache.",
        },
        {
          title: "راقب نسبة الإصابة",
          body: "Cache Hit Ratio منخفض يعني ذاكرة مهدورة. راقب <code>dotnet-counters</code> أو مقاييس Redis قبل توسيع الكاش.",
        },
      ],
      quiz: [
        {
          q: "ما الفرق الأساسي بين OutputCache وHybridCache؟",
          options: [
            "لا فرق.",
            "OutputCache يخزّن الاستجابة كاملة، وHybridCache يخزّن قيمًا مع L1/L2.",
            "HybridCache للمتصفح فقط.",
            "OutputCache لا يدعم الإبطال.",
          ],
          answer: 1,
          explain:
            "OutputCache يعمل على مستوى HTTP ويختصر الطلب، وHybridCache يخزّن نتائج داخل الخدمة مع طبقتين.",
        },
        {
          q: "كيف تُبطل OutputCache عند تعديل البيانات؟",
          options: [
            "أعد تشغيل التطبيق.",
            "استخدم Tag على السياسة و<code>EvictByTagAsync</code> عند الكتابة.",
            "انتظر TTL دائمًا.",
            "احذف ملفات bin.",
          ],
          answer: 1,
          explain:
            "الوسوم تربط المفاتيح بمجموعة منطقية، فتمسحها دفعة واحدة عند تغيّر البيانات.",
        },
        {
          q: "ما هو Cache Stampede؟",
          options: [
            "زيادة حجم الكاش.",
            "تزامن طلبات كثيرة لإعادة بناء مفتاح منتهٍ في نفس اللحظة.",
            "فشل Redis.",
            "نوع من الضغط.",
          ],
          answer: 1,
          explain:
            "عند انتهاء مفتاح ساخن، تحاول طلبات متزامنة إعادة حسابه، فتُحمّل قاعدة البيانات. الحل قفل/Single Flight أو HybridCache.",
        },
      ],
      capstone: {
        title: "كاش قائمة المنتجات",
        goal: "نضيف Output Cache لقائمة المنتجات مع إبطال دقيق عند الكتابة، ونقيس الفرق في زمن الاستجابة.",
        tasks: [
          "أضف <code>AddOutputCache</code> و<code>UseOutputCache</code>.",
          "عرّف سياسة <code>products:list</code> مع VaryByQuery وTag.",
          "طبّق <code>CacheOutput</code> على GET فقط.",
          "أبطل الوسم في POST وPUT وDELETE.",
          "قِس زمن أول طلب وثاني طلب وسجّل الفرق.",
        ],
        code: {
          lang: "csharp",
          title: "سياسة الكاش",
          code: `builder.Services.AddOutputCache(options =>
{
    options.AddPolicy("products:list", policy => policy
        .Expire(TimeSpan.FromSeconds(60))
        .SetVaryByQuery("page", "size")
        .Tag("products"));
});

app.UseOutputCache();

products.MapGet("/", ListProducts)
    .CacheOutput("products:list");`,
        },
      },
    },
    {
      id: "memory-performance",
      title: "GC والذاكرة وJSON: أين يذهب الأداء؟",
      duration: 28,
      level: "متقدم",
      summary:
        "كل تخصيص (allocation) له ثمن. سنفهم أجيال GC، ونقلل ضغط الذاكرة عبر Span وArrayPool، ونسرّع JSON بـ source generation.",
      keywords: ["GC", "Gen0", "LOH", "Span", "ArrayPool", "source generation", "ValueTask", "BenchmarkDotNet"],
      objectives: [
        "تفسّر عمل GC وأجياله وأثر LOH.",
        "تقلل التخصيصات في المسارات الساخنة.",
        "تستخدم JSON source generation لخفض زمن البدء والذاكرة.",
        "تقيس بـ dotnet-counters وBenchmarkDotNet بدل التخمين.",
      ],
      concept: `
        <p>CLR يدير الذاكرة تلقائيًا، لكن «تلقائي» لا يعني «مجاني». كل <code>new</code> يخصّص على managed heap. عندما يمتلئ Gen0، يبدأ GC بجمع الكائنات الميتة وإبقاء الحيّة. الجمع نفسه يستهلك وقتًا، وقد يوقف خيوط التطبيق لحظيًا.</p>
        <p>الأجيال:</p>
        <ul>
          <li><strong>Gen0</strong>: كائنات قصيرة العمر (معظم كائنات الطلب). جمعه سريع.</li>
          <li><strong>Gen1</strong>: منطقة انتقالية للكائنات التي نجت من Gen0.</li>
          <li><strong>Gen2</strong>: كائنات طويلة العمر. جمعه مكلف وقد يستغرق أجزاء من الثانية.</li>
          <li><strong>LOH</strong>: كائنات أكبر من 85 كيلوبايت تقريبًا. تُجمع مع Gen2، وتجزئتها مؤلمة.</li>
        </ul>
        <p>في ASP.NET Core، الذاكرة المثالية هي: تخصيصات صغيرة كثيرة في Gen0 تُجمع بسرعة، بلا كائنات كبيرة متكررة. المشكلة تظهر عند بناء نصوص ضخمة أو مصفوفات كبيرة لكل طلب، أو تخزين نتائج في <code>static</code> بلا حد.</p>
        <h3>Span وArrayPool</h3>
        <p><code>Span&lt;T&gt;</code> و<code>Memory&lt;T&gt;</code> يمثلان نافذة على ذاكرة موجودة دون نسخ. <code>stackalloc</code> يخصص على المكدس (محدود الحجم). <code>ArrayPool&lt;T&gt;.Shared.Rent(n)</code> يعيد استخدام مصفوفات بدل تخصيص جديدة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>var buffer = ArrayPool&lt;byte&gt;.Shared.Rent(4096);
try { /* استخدم buffer */ }
finally { ArrayPool&lt;byte&gt;.Shared.Return(buffer); }</code></pre>
        <p>هذه الأدوات ليست للاستخدام العشوائي. استخدمها حيث أثبت القياس أن التخصيص هو العنق.</p>
        <h3>JSON Source Generation</h3>
        <p><code>System.Text.Json</code> التقليدي يستخدم Reflection لبناء المسلسِل، ما يكلّف وقت بدء وذاكرة. مع <code>JsonSerializerContext</code> يُولَّد الكود وقت الترجمة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(List&lt;ProductDto&gt;))]
internal partial class AppJsonContext : JsonSerializerContext { }</code></pre>
        <p>الفائدة الأكبر في AOT/trimming، لكن حتى في JIT العادي يقلّل زمن أول طلب.</p>
      `,
      compare: {
        intro: `<p>دالة صغيرة تُظهر الفرق: بناء نص داخل حلقة، ثم تسلسل JSON بالانعكاس. النسختان تعطيان نفس الناتج، بتكلفة مختلفة.</p>`,
        before: {
          label: "تخصيصات متكررة",
          lang: "csharp",
          title: "Report.cs",
          code: `public string BuildCsv(List<Product> products)
{
    var csv = "";
    foreach (var p in products)
    {
        // كل += ينشئ string جديدًا (O(n^2) نسخ)
        csv += p.Id + "," + p.Name + "," + p.Price + "\\n";
    }
    return csv;
}

public string ToJson(ProductDto dto) =>
    JsonSerializer.Serialize(dto); // Reflection + تخصيصات

public async Task<ProductDto?> GetAsync(int id)
{
    // تخصيص مصفوفة لكل طلب
    var buffer = new byte[8192];
    return await ReadAsync(id, buffer);
}`,
          points: [
            "نسخ نص متكرر وضغط على Gen0.",
            "Reflection في كل تسلسل (خصوصًا أول مرة).",
            "مصفوفة كبيرة لكل طلب تضغط LOH.",
          ],
        },
        after: {
          label: "أدوات أقل تخصيصًا",
          lang: "csharp",
          title: "Report.cs",
          code: `public string BuildCsv(List<Product> products)
{
    var sb = new StringBuilder(products.Count * 32);
    foreach (var p in products)
    {
        sb.Append(p.Id).Append(',')
          .Append(p.Name).Append(',')
          .Append(p.Price).Append('\\n');
    }
    return sb.ToString();
}

[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(List<ProductDto>))]
internal partial class AppJsonContext : JsonSerializerContext { }

public string ToJson(ProductDto dto) =>
    JsonSerializer.Serialize(dto, AppJsonContext.Default.ProductDto);

public async Task<ProductDto?> GetAsync(int id)
{
    var buffer = ArrayPool<byte>.Shared.Rent(8192);
    try { return await ReadAsync(id, buffer); }
    finally { ArrayPool<byte>.Shared.Return(buffer); }
}`,
          points: [
            "StringBuilder يقلّل النسخ.",
            "Source generation يزيل Reflection.",
            "ArrayPool يعيد استخدام الذاكرة.",
          ],
        },
        verdict: `<p>هذه التحسينات لا تُطبَّق «لأنها أسرع». تُطبَّق بعد قياس: هل GC Time مرتفع؟ هل LOH ينمو؟ هل أول طلب بطيء؟ ابدأ بالقياس، ثم غيّر نقطة واحدة، ثم قِس مرة أخرى. التحسين الأعمى يضيف تعقيدًا بلا دليل.</p>`,
      },
      walkthrough: [
        {
          title: "قِس التخصيصات",
          code: `dotnet-counters monitor --process-id <pid> \\\n  System.Runtime[gc-heap-size,alloc-rate,gen-0-gc-count]\n\n# أو BenchmarkDotNet مع MemoryDiagnoser`,
          lang: "bash",
          body: `<p>لا تحسّن الذاكرة بالحدس. <code>alloc-rate</code> و<code>gc-heap-size</code> وعدد GC. BenchmarkDotNet يعطي allocations/op. ابدأ بالقياس. لا تضع <code>GC.Collect</code> في الإنتاج. ركّز على المسار الحرج.</p>`
        },
        {
          title: "تقليل التخصيص",
          code: `// قبل: string + LINQ في حلقة ساخنة\nvar text = "order:" + id.ToString() + ":" + status;\n\n// بعد: StringBuilder مع capacity أو Span\nvar builder = new StringBuilder(64);\nbuilder.Append("order:").Append(id).Append(':').Append(status);`,
          lang: "csharp",
          body: `<p>كل string جديد يخصص. في الحلقة الساخنة، التخصيصات تتراكم. استخدم <code>StringBuilder</code> أو <code>string.Create</code>. لا تفرط في التحسين قبل القياس. اجعل الكود واضحًا أولًا. اختبر الفرق.</p>`
        },
        {
          title: "Span<T>",
          code: `ReadOnlySpan<char> span = line.AsSpan();\nvar colon = span.IndexOf(':');\nvar key = span[..colon];\nvar value = span[(colon + 1)..];`,
          lang: "csharp",
          body: `<p><code>Span</code> يعمل على ذاكرة موجودة بلا نسخ. مناسب لتحليل النصوص/البروتوكولات. لا تحتفظ به بعد انتهاء الذاكرة الأصلية. لا تستخدمه مع async. وازن بين الوضوح والأداء.</p>`
        },
        {
          title: "ArrayPool",
          code: `var buffer = ArrayPool<byte>.Shared.Rent(4096);\ntry\n{\n    var read = await stream.ReadAsync(buffer, ct);\n    Process(buffer.AsSpan(0, read));\n}\nfinally\n{\n    ArrayPool<byte>.Shared.Return(buffer);\n}`,
          lang: "csharp",
          body: `<p>المخازن المؤقتة الكبيرة المتكررة تضغط GC. <code>ArrayPool</code> يعيد استخدامها. أعدها دائمًا في <code>finally</code>. لا تفترض أنها مصفّرة. استخدم الطول المقروء فقط. لا تشاركها بين عمليات متزامنة.</p>`
        },
        {
          title: "JSON Source Generation",
          code: `[JsonSerializable(typeof(ProductDto))]\ninternal partial class AppJsonContext : JsonSerializerContext { }\n\noptions.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonContext.Default);`,
          lang: "csharp",
          body: `<p>Source generation يقلل الانعكاس/التخصيص ويسرّع البدء. مناسب لـAOT/حالات معروفة. أضف كل نوع. لا تخلط resolver خاطئ. اختبر serialization. قد لا يدعم كل الميزات. قِس قبل/بعد.</p>`
        },
        {
          title: "LOH",
          code: `// تجنب إنشاء مصفوفات/strings ضخمة متكررة (>85KB)\n// استخدم streaming أو pooled buffers\nawait foreach (var item in source.WithCancellation(ct))\n    await writer.WriteAsync(item);`,
          lang: "csharp",
          body: `<p>الأجسام الكبيرة تذهب إلى LOH وتُجمع بتكلفة. لا تجمع استجابة ضخمة في string. استخدم streaming. لا تخصص مصفوفة ضخمة لكل طلب. راقب LOH. أعد استخدام المخازن. وازن مع التعقيد.</p>`
        },
        {
          title: "GC Generations",
          code: `Gen0: قصيرة العمر\nGen1: متوسطة\nGen2: طويلة العمر\nLOH: كبيرة`,
          lang: "text",
          body: `<p>معظم الكائنات تموت صغيرة. لا تحتفظ بذاكرة طويلة بلا سبب. caches بلا حدود ترفع Gen2. Singleton يحتفظ بكل شيء. راقب GC pause. لا تفرض <code>GCSettings.LatencyMode</code> بلا فهم. القياس أولًا.</p>`
        },
        {
          title: "قاعدة عملية",
          code: `1. قِس\n2. حسّن المسار الساخن\n3. أعد القياس\n4. تحقق من الوضوح\n5. راقب الإنتاج`,
          lang: "text",
          body: `<p>الأداء ليس سباق micro-optimizations. ابدأ بالخوارزمية/الاستعلامات/الشبكة. ثم التخصيصات. لا تضحّ بالصيانة مقابل 2%. استخدم نتائج قابلة للتكرار. راقب بعد النشر.</p>`
        }
      ],
      internals: `
        <p>GC في .NET يعمل بـ <strong>Mark-and-Sweep</strong> مع Compaction اختياري. Gen0 صغير (بضع مئات كيلوبايت إلى عدة ميغابايت) ويُجمع عندما يمتلئ. الكائنات التي تنجو تُرقّى إلى Gen1 ثم Gen2. هذا الترقية تجعل العمر الافتراضي للكائنات القصيرة قصيرًا والطويلة مستقرة.</p>
        <p><strong>Server GC</strong> (الافتراضي في ASP.NET Core على أنظمة متعددة النوى) ينشئ heap لكل نواة ويجمع بالتوازي. يزيد الإنتاجية لكنه يستهلك ذاكرة أكبر. في حاويات ذات حد ذاكرة منخفض، قد تحتاج <code>DOTNET_gcServer=0</code> أو ضبط <code>GCHeapHardLimit</code> لتجنب OOM.</p>
        <p><strong>LOH</strong> لا يُضغط افتراضيًا (يمكن تفعيل الضغط). إذا كنت تخصص سلاسل أو مصفوفات كبيرة متكررة، فقد تتجزأ الذاكرة ويزيد Working Set. الحل: تجنّب الكائنات الكبيرة في المسار الساخن، أو استخدم <code>RecyclableMemoryStream</code> أو <code>ArrayPool</code>.</p>
        <p><strong>ValueTask</strong> يقلل التخصيص عندما تكون النتيجة متاحة غالبًا بشكل متزامن (مثل cache hit)، لكنه لا يجوز انتظاره مرتين أو استخدامه بتوازٍ. إن لم تكن متأكدًا، استخدم <code>Task</code>. التعقيد الخاطئ أسوأ من تخصيص صغير.</p>
      `,
      internalsTable: {
        head: ["المؤشر", "معناه", "أداة"],
        rows: [
          ["Gen0 GC Count", "ضغط تخصيصات قصيرة", "dotnet-counters"],
          ["LOH Size", "كائنات كبيرة/تجزئة", "dotnet-gcdump"],
          ["Allocation Rate", "بايت/ثانية لكل طلب", "dotnet-trace"],
          ["P99 Latency", "تأثير الجمع على الطلبات", "OpenTelemetry"],
        ],
      },
      tips: [
        {
          title: "قِس أولًا",
          body: "استخدم <code>dotnet-counters monitor</code> و<code>dotnet-trace</code> وBenchmarkDotNet. لا تضف Span وArrayPool قبل أن ترى مشكلة حقيقية.",
        },
        {
          title: "احذر LOH",
          body: "سلاسل JSON الضخمة والمصفوفات الكبيرة تذهب إلى LOH. استخدم streaming أو <code>PipeWriter</code> للاستجابات الضخمة بدل بناء نص كامل.",
        },
        {
          title: "JSON source-gen في الإنتاج",
          body: "أضف <code>JsonSerializerContext</code> واربطه بـ <code>ConfigureHttpJsonOptions</code>. يفيد البدء وAOT ويقلل الذاكرة.",
        },
        {
          title: "لا تحسّن مسارًا باردًا",
          body: "تحسين endpoint يُستدعى مرة يوميًا بلا قيمة. رتّب حسب الأثر: عدد الطلبات × التكلفة.",
        },
      ],
      quiz: [
        {
          q: "أين تُخصص الكائنات الأكبر من 85KB تقريبًا؟",
          options: ["Gen0", "Gen1", "LOH", "Stack"],
          answer: 2,
          explain:
            "Large Object Heap للأحجام الكبيرة. جمعها مرتبط بـ Gen2 وتجزئتها قد ترفع الذاكرة.",
        },
        {
          q: "ما فائدة JsonSerializerContext؟",
          options: [
            "يشفّر JSON.",
            "يولّد كود التسلسل وقت الترجمة بدل Reflection.",
            "يزيد حجم الاستجابة.",
            "يستبدل قاعدة البيانات.",
          ],
          answer: 1,
          explain:
            "Source generation يزيل الحاجة للانعكاس، فيحسّن البدء والذاكرة ويدعم AOT.",
        },
        {
          q: "متى تستخدم ArrayPool؟",
          options: [
            "لكل مصفوفة صغيرة.",
            "بعد قياس يثبت أن تخصيص المصفوفات المتكررة يمثل ضغطًا.",
            "بدل قاعدة البيانات.",
            "فقط مع Controllers.",
          ],
          answer: 1,
          explain:
            "هو تحسين موجه؛ استخدامه بلا قياس يضيف تعقيدًا ومخاطر إعادة استخدام خاطئة.",
        },
      ],
      capstone: {
        title: "تحسين JSON وذاكرة Souq.NET",
        goal: "نقلل تخصيصات التسلسل ونقيس الأثر بأدوات .NET، دون تغيير عقد الـ API.",
        tasks: [
          "أضف <code>AppJsonContext</code> مع <code>[JsonSerializable]</code> لأنواع الاستجابة.",
          "اربطه بـ <code>ConfigureHttpJsonOptions</code> عبر <code>TypeInfoResolverChain</code>.",
          "شغّل <code>dotnet-counters monitor</code> وسجّل Allocation Rate وGen0 قبل التغيير.",
          "أعد القياس بعد التغيير وقارن.",
          "أضف اختبارًا يتأكد أن الاستجابة ما زالت بنفس الشكل.",
        ],
        code: {
          lang: "csharp",
          title: "ربط source generation",
          code: `[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(List<ProductDto>))]
[JsonSerializable(typeof(ProblemDetails))]
internal partial class AppJsonContext : JsonSerializerContext { }

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain.Insert(
        0, AppJsonContext.Default);
});`,
        },
      },
    },
    {
      id: "docker-deploy",
      title: "Docker والنشر الإنتاجي",
      duration: 28,
      level: "متقدم",
      summary:
        "صورة صغيرة، مستخدم غير جذري، فحص صحة، وإيقاف لطيف. سنحوّل التطبيق إلى حاوية جاهزة مع قائمة تحقق إنتاجية.",
      keywords: ["Docker", "multi-stage", "non-root", "healthcheck", "compose", "graceful shutdown", "CI/CD"],
      objectives: [
        "تكتب Dockerfile متعدد المراحل لـ .NET 10.",
        "تشغّل الحاوية بمستخدم غير جذري وبحدود واضحة.",
        "تضيف Health Checks وتفرّق بين Liveness وReadiness.",
        "تخطط للترحيلات والإعدادات والأسرار في النشر.",
      ],
      concept: `
        <p>صورة .NET الإنتاجية لا تحتاج SDK. افصل بين مرحلتين:</p>
        <ol>
          <li><strong>build</strong>: صورة SDK كاملة، تنسخ csproj، تستعيد الحزم، تنسخ الكود، تنشر إلى مجلد.</li>
          <li><strong>runtime</strong>: صورة <code>aspnet</code> أصغر، تنسخ مجلد النشر فقط، وتشغّل التطبيق.</li>
        </ol>
        <p>هذا يقلل الحجم وسطح الهجوم. لا تنسخ <code>bin/obj</code> من جهازك؛ ابنِ داخل الصورة لضمان التطابق. واستخدم <code>.dockerignore</code> لاستبعاد <code>bin</code> و<code>obj</code> و<code>.git</code> و<code>node_modules</code>.</p>
        <h3>مستخدم غير جذري</h3>
        <p>صور .NET الحديثة تتضمن مستخدم <code>app</code> (UID 1654) يمكنك التبديل إليه بـ <code>USER $APP_UID</code>. لا تشغّل التطبيق كـ root: أي ثغرة في الكود تعني صلاحيات كاملة داخل الحاوية. واقرأ نظام الملفات للقراءة فقط إن أمكن.</p>
        <h3>المنفذ والإعداد</h3>
        <p>في .NET 8+ الصورة الافتراضية تستمع على 8080. اضبط <code>ASPNETCORE_URLS=http://+:8080</code> صراحة، و<code>ASPNETCORE_ENVIRONMENT=Production</code>. لا تضع أسرارًا في الصورة أو ملف compose داخل Git؛ استخدم متغيرات بيئة من مدير أسرار، أو Docker secrets.</p>
        <h3>الصحة والإيقاف</h3>
        <p><strong>Liveness</strong>: هل العملية حيّة؟ لا تعتمد على قاعدة البيانات، وإلا أعدت Kubernetes تشغيل التطبيق بسبب انقطاع خارجي. <strong>Readiness</strong>: هل جاهز لاستقبال الترافيك؟ يمكنه فحص قاعدة البيانات والكاش. أضف <code>/health/live</code> و<code>/health/ready</code>.</p>
        <p>عند إيقاف الحاوية، يُرسل SIGTERM. ASP.NET Core يبدأ <strong>Graceful Shutdown</strong>: يتوقف عن القبول، وينتظر الطلبات الجارية حتى <code>ShutdownTimeout</code>. تأكد أن مدة الانتظار في المنصة أطول من مدة التطبيق، وإلا قُطعت الطلبات.</p>
      `,
      compare: {
        intro: `<p>النشر اليدوي يعتمد على الجهاز والإعدادات المحلية. الحاوية تجعل كل شيء جزءًا من المستودع وقابلًا للتكرار.</p>`,
        before: {
          label: "نشر يدوي على VM",
          lang: "bash",
          title: "خطوات يدوية",
          code: `# على الخادم:
dotnet publish -c Release
scp -r bin/Release/net10.0/publish/ user@server:/var/www/souq
ssh user@server
sudo systemctl restart souq
# إذا فشل: لا سجل موحد، ولا نسخة سابقة واضحة`,
          points: [
            "البيئة تختلف بين الجهاز والخادم.",
            "التراجع يدوي وغير مضمون.",
            "الأسرار تُنسخ يدويًا.",
          ],
        },
        after: {
          label: "Dockerfile متعدد المراحل",
          lang: "dockerfile",
          title: "Dockerfile",
          code: `FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/Souq.Api/Souq.Api.csproj", "src/Souq.Api/"]
COPY ["src/Souq.Application/Souq.Application.csproj", "src/Souq.Application/"]
COPY ["src/Souq.Domain/Souq.Domain.csproj", "src/Souq.Domain/"]
COPY ["src/Souq.Infrastructure/Souq.Infrastructure.csproj", "src/Souq.Infrastructure/"]
RUN dotnet restore "src/Souq.Api/Souq.Api.csproj"
COPY . .
RUN dotnet publish "src/Souq.Api/Souq.Api.csproj" \\
    -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
ENV ASPNETCORE_URLS=http://+:8080 \\
    ASPNETCORE_ENVIRONMENT=Production \\
    DOTNET_RUNNING_IN_CONTAINER=true
COPY --from=build /app/publish .
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["dotnet", "Souq.Api.dll"]`,
          points: [
            "بناء متطابق في أي بيئة.",
            "صورة نهائية صغيرة بلا SDK.",
            "جاهزة للتراجع عبر وسم الإصدار.",
          ],
        },
        verdict: `<p>الحاوية ليست ضمانًا للأمان أو الأداء، لكنها تجعل <strong>البيئة جزءًا من الكود</strong>. نفس الصورة التي اختبرتها في staging هي التي تعمل في الإنتاج، وهذا يقلل مفاجآت النشر أكثر من أي أداة أخرى.</p>`,
      },
      walkthrough: [
        {
          title: "Dockerfile multi-stage",
          code: `FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build\nWORKDIR /src\nCOPY . .\nRUN dotnet publish src/Souq.Api/Souq.Api.csproj -c Release -o /app/publish\n\nFROM mcr.microsoft.com/dotnet/aspnet:10.0\nWORKDIR /app\nCOPY --from=build /app/publish .\nUSER $APP_UID\nEXPOSE 8080\nENTRYPOINT ["dotnet", "Souq.Api.dll"]`,
          lang: "dockerfile",
          body: `<p>SDK للبناء فقط. runtime للتشغيل. <code>publish</code> Release. مستخدم غير root. لا تنسخ الأسرار. استخدم <code>.dockerignore</code>. ثبّت الإصدار. الصورة النهائية أصغر وأ safer. اختبر تشغيلها محليًا.</p>`
        },
        {
          title: "Compose",
          code: `services:\n  api:\n    build: .\n    env_file: .env\n    depends_on:\n      db:\n        condition: service_healthy\n    ports: ["8080:8080"]\n  db:\n    image: postgres:16-alpine\n    volumes: ["pgdata:/var/lib/postgresql/data"]\nvolumes:\n  pgdata:`,
          lang: "yaml",
          body: `<p>شبكة داخلية. API ينتظر صحة DB. البيانات في volume. لا تنشر 5432 للخارج. أضف proxy/redis/collector. استخدم healthchecks. لا تضع الأسرار في YAML. اختبر من clone نظيف.</p>`
        },
        {
          title: "الإعدادات والأسرار",
          code: `ASPNETCORE_ENVIRONMENT=Production\nConnectionStrings__Souq=Host=db;Database=souq;Username=souq\nJwt__SigningKey_FILE=/run/secrets/jwt_key`,
          lang: "text",
          body: `<p>متغيرات بأسماء هرمية. <code>_FILE</code> للأسرار. لا تضع المفتاح في appsettings/الصورة. تحقق من الإعداد عند البدء. لا تسجّل القيم. افصل البيئات. استخدم خزنة في الإنتاج.</p>`
        },
        {
          title: "Migration job",
          code: `migrate:\n  build: .\n  command: ["dotnet", "ef", "database", "update", "--no-build"]\n  env_file: .env\n  depends_on:\n    db:\n      condition: service_healthy\n  restart: "no"`,
          lang: "yaml",
          body: `<p>خدمة واحدة تنتهي. لا تشغّل migrations في كل replica. اختبر من قاعدة فارغة/قديمة. خذ backup قبل التغيير الخطير. استخدم expand/contract للنشر المتداخل. <code>restart: "no"</code> يمنع الحلقة.</p>`
        },
        {
          title: "Health checks",
          code: `healthcheck:\n  test: ["CMD", "curl", "-f", "http://localhost:8080/health/ready"]\n  interval: 10s\n  timeout: 3s\n  retries: 5`,
          lang: "yaml",
          body: `<p>readiness يفحص DB/Outbox. liveness منفصل. لا تضع فحص DB في liveness. اختبر عند إيقاف DB. لا تجعل الفحص بطيئًا. راقب restart loops. أضف health للـproxy أيضًا.</p>`
        },
        {
          title: "HTTPS وProxy",
          code: `api.souq.example {\n  reverse_proxy api:8080\n  encode gzip\n}`,
          lang: "text",
          body: `<p>TLS عند proxy. HSTS في الإنتاج. Forwarded headers موثوقة. لا تعرض API مباشرة. اختبر redirect من HTTP. لا تضع شهادة خاصة في الصورة. راقب انتهاء الشهادة.</p>`
        },
        {
          title: "غير root",
          code: `USER $APP_UID\n# أو مستخدم مخصص بصلاحيات محدودة\n# لا تكتب ملفات داخل الحاوية`,
          lang: "dockerfile",
          body: `<p>الحاوية ليست VM. لا تشغّل root. اجعل الملفات للقراءة فقط. استخدم volume للبيانات. اضبط capabilities/read-only حيث ممكن. لا تخزّن logs في الحاوية. راقب الصلاحيات.</p>`
        },
        {
          title: "Smoke/Runbook",
          code: `docker compose up -d\ndocker compose run --rm migrate\ncurl -f https://api.souq.example/health/ready\ncurl -f https://api.souq.example/api/v1/products`,
          lang: "bash",
          body: `<p>بعد النشر نفّذ smoke. اختبر شراء في staging. إذا فشل، راجع logs/health. وثّق rollback/backup/RPO/RTO. اختبر restore. Runbook قصير وقابل للتنفيذ. المشروع ليس جاهزًا حتى يعمل من صورة نظيفة.</p>`
        }
      ],
      internals: `
        <p>كل سطر في Dockerfile يُنشئ طبقة (Layer) مخزّنة. نسخ csproj أولًا ثم restore ثم نسخ الكود يستغل الكاش: تغيير ملف C# لا يعيد استعادة الحزم. هذا يقلص زمن البناء كثيرًا في CI.</p>
        <p>صورة <code>aspnet</code> تحتوي runtime + ASP.NET Core، بينما <code>runtime</code> لا تحتوي ASP.NET. اختيار الصورة الخاطئة يعطي خطأ «framework missing». ثبت الإصدار الكامل (<code>10.0.1</code>) بدل <code>latest</code> لضمان بناء قابل للتكرار، وحدّث بوعي.</p>
        <p>داخل الحاوية، <code>DOTNET_RUNNING_IN_CONTAINER=true</code> يجعل بعض الإعدادات تتكيف. حد الذاكرة (cgroup) يؤثر على GC؛ .NET يقرأه عادة، لكن في بيئات معينة تحتاج <code>DOTNET_GCHeapHardLimit</code>. راقب <code>Working Set</code> وOOMKilled في المنصة.</p>
        <p>لا تشغّل التطبيق كعملية PID 1 إن كنت تعتمد على إشارات؛ استخدم <code>ENTRYPOINT</code> بصيغة exec (المصفوفة) ليمر SIGTERM مباشرة. تجنّب صيغة shell التي تبتلع الإشارة. هذا الفرق يحدد هل الإيقاف لطيف أم قاطع.</p>
      `,
      internalsTable: {
        head: ["العنصر", "الخطأ الشائع", "الصحيح"],
        rows: [
          ["صورة التشغيل", "استخدام sdk في النهائي", "aspnet:10.0"],
          ["المستخدم", "root افتراضيًا", "USER $APP_UID"],
          ["المنفذ", "localhost داخل الحاوية", "http://+:8080"],
          ["الأسرار", "ENV في Dockerfile", "secrets/مدير أسرار"],
          ["الترحيلات", "EnsureCreated عند الإقلاع", "خطوة نشر منفصلة"],
        ],
      },
      tips: [
        {
          title: "استخدم .dockerignore",
          body: "استبعد <code>bin</code> و<code>obj</code> و<code>.git</code> و<code>tests</code> و<code>*.user</code>. هذا يسرّع البناء ويمنع تسريب ملفات محلية.",
        },
        {
          title: "افصل الترحيلات عن الإقلاع",
          body: "شغّل <code>dotnet ef database update</code> أو bundle كـ Job قبل النشر. تشغيلها في كل نسخة مع التوسع الأفقي يسبب سباقات وأقفالًا.",
        },
        {
          title: "Health Checks واقعية",
          body: "Liveness لا يفحص قاعدة البيانات. Readiness يفحصها ويكون أخف من طلب كامل. اضبط <code>timeout</code> و<code>period</code> بحسب زمن الاستجابة.",
        },
        {
          title: "راقب بعد النشر",
          body: "سجلات JSON، معدل الأخطاء، P95/P99، وذاكرة الحاوية. النشر لا ينتهي عند <code>docker push</code>; ينتهي عندما تثبت Observability أن الخدمة سليمة.",
        },
      ],
      quiz: [
        {
          q: "لماذا نستخدم multi-stage build؟",
          options: [
            "لزيادة حجم الصورة.",
            "لفصل SDK الثقيل عن صورة التشغيل الصغيرة وتقليل سطح الهجوم.",
            "لتشغيل الاختبارات تلقائيًا.",
            "لأن Docker يطلب ذلك.",
          ],
          answer: 1,
          explain:
            "المرحلة الأولى تبني، والثانية تنسخ الناتج فقط. النتيجة صورة أصغر وأكثر أمانًا.",
        },
        {
          q: "ماذا يجب أن يفحص Liveness probe؟",
          options: [
            "قاعدة البيانات والكاش.",
            "حيوية العملية نفسها فقط، دون تبعيات خارجية.",
            "توفر جميع الخدمات.",
            "سرعة الشبكة.",
          ],
          answer: 1,
          explain:
            "لو فحص قاعدة بيانات خارجية، فقد تُعاد الحاوية بلا داعٍ عند انقطاع مؤقت. Readiness هو مكان فحص التبعيات.",
        },
        {
          q: "أين تُخزَّن أسرار الإنتاج؟",
          options: [
            "في Dockerfile كـ ENV.",
            "في appsettings.json داخل الصورة.",
            "في مدير أسرار/متغيرات بيئة تُحقن وقت التشغيل.",
            "في README.",
          ],
          answer: 2,
          explain:
            "أي سر داخل الصورة أو المستودع يُعتبر مكشوفًا. الحقن وقت التشغيل يسمح بالتدوير وعدم التسريب.",
        },
      ],
      capstone: {
        title: "حاوية Souq.NET الجاهزة",
        goal: "ننشر التطبيق في حاوية مع PostgreSQL، بفحص صحة وإعدادات إنتاج، ونتأكد من الإيقاف اللطيف.",
        tasks: [
          "أضف Dockerfile متعدد المراحل بمستخدم غير جذري.",
          "أضف <code>.dockerignore</code> يستبعد bin وobj و.git.",
          "أضف Health Checks: <code>/health/live</code> و<code>/health/ready</code>.",
          "أنشئ <code>compose.yaml</code> فيه api وpostgres مع healthcheck وvolume.",
          "شغّل <code>docker compose up --build</code> وتأكد من عمل التطبيق.",
          "أرسل SIGTERM أثناء طلب طويل وتحقق من عدم قطعه.",
        ],
        code: {
          lang: "yaml",
          title: "compose.yaml",
          code: `services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      ASPNETCORE_ENVIRONMENT: Production
      ConnectionStrings__Default: Host=db;Database=souq;Username=app;Password=$DB_PASSWORD
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17
    environment:
      POSTGRES_DB: souq
      POSTGRES_USER: app
      POSTGRES_PASSWORD: $DB_PASSWORD
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d souq"]
      interval: 5s
      retries: 10

volumes:
  pgdata:`,
        },
      },
    },
    {
      id: "observability",
      title: "Observability: Logs وMetrics وTraces",
      duration: 32,
      level: "متقدم",
      summary:
        "لا تسأل «هل يعمل؟» بل «كيف أعرف أين تعطّل ولماذا؟». سنبني ثلاث إشارات مترابطة، وربطها بـSLO وتنبيهات قابلة للتنفيذ.",
      keywords: ["OpenTelemetry", "Serilog", "traces", "metrics", "logs", "health checks", "SLO", "OTLP", "correlation"],
      objectives: [
        "تفرّق بين logs وmetrics وtraces.",
        "تربط السجلات بالـtrace عبر Correlation/TraceId.",
        "تصدّر traces وmetrics عبر OpenTelemetry.",
        "تضبط liveness وreadiness بشكل صحيح.",
        "تبني تنبيهات مبنية على SLO لا على ضجيج."
      ],
      concept: `
        <p><strong>Observability</strong> قدرة النظام على الإجابة عن أسئلة لم تتوقعها مسبقًا: لماذا p99 ارتفع؟ أي طلب بطيء؟ أي مستخدم تأثر؟ ثلاث إشارات أساسية:</p>
        <ul>
          <li><strong>Logs</strong>: أحداث منفصلة بتفاصيل سياقية. جيدة للتحقيق، سيئة كأساس وحيد للقياس.</li>
          <li><strong>Metrics</strong>: أرقام مجمعة عبر الزمن (counters/histograms). رخيصة للتنبيه والاتجاهات.</li>
          <li><strong>Traces</strong>: مسار طلب عبر الخدمات والاستعلامات، مع spans وأزمنة.</li>
        </ul>
        <p>الثلاثة معًا: metric يقول «هناك مشكلة»، trace يقول «أين»، log يقول «لماذا/بمن». بدون ربطها بـTraceId، تتحول إلى ثلاث جزر.</p>
        <h3>السجلات المنظمة</h3>
        <p>لا تكتب <code>"Order created " + id</code>. استخدم قالبًا وحقولًا: <code>logger.LogInformation("Order {OrderId} created", id)</code>. هذا ينتج JSON قابلًا للبحث. لا تسجّل التوكنات أو كلمات المرور أو جسم الطلب كاملًا. أضف <code>TraceId</code> و<code>SpanId</code> تلقائيًا من OpenTelemetry. اجعل مستوى المعلومات افتراضيًا، والتفاصيل عند الحاجة.</p>
        <h3>Metrics</h3>
        <p>Counter يزيد فقط (عدد الطلبات/الأخطاء). Histogram يوزّع القيم (زمن الاستجابة). Gauge قيمة لحظية (اتصالات نشطة). استخدم أبعادًا منخفضة الكاردينالية: method، status class، route template. لا تضع <code>userId</code> أو <code>orderId</code> كـlabel؛ ستفجّر نظام القياس. احسب p95/p99 من histogram، لا متوسطًا فقط.</p>
        <h3>Traces</h3>
        <p>كل طلب له trace، وداخله spans: ASP.NET Core، HttpClient، EF Core، وbroker. W3C Trace Context يمرر <code>traceparent</code> بين الخدمات. أضف resource attributes مثل service.name وversion. استخدم sampling ذكيًا: 100% في التطوير، نسبة في الإنتاج مع الاحتفاظ بالأخطاء. لا تنسَ أن التتبع نفسه له تكلفة.</p>
        <h3>Health Checks</h3>
        <p><strong>Liveness</strong> يجيب: هل العملية حية؟ لا تفحص قاعدة البيانات فيه، وإلا أعادت orchestrator تشغيل التطبيق عند عطل قاعدة بيانات. <strong>Readiness</strong> يجيب: هل جاهز لاستقبال الحركة؟ افحص الاتصال والاعتماديات الأساسية. ميّز بينهما؛ الخلط يسبب إعادة تشغيل لا تحل المشكلة.</p>
        <h3>SLO والتنبيهات</h3>
        <p>لا تنبّه على كل خطأ 500 منفرد. استخدم معدل الأخطاء ضمن نافذة، p95/p99، وعمر Outbox. كل تنبيه يجب أن يكون قابلًا للتنفيذ: من يستجيب؟ ماذا يفحص؟ ما rollback؟ أضف Runbook. التنبيهات الكثيرة تجعل الفريق يتجاهلها، وهذا أسوأ من قلة التنبيه.</p>
        <h3>الخصوصية والتكلفة</h3>
        <p>لا تجمع PII في traces أو logs. انقّح الحقول الحساسة. اضبط مدة الاحتفاظ. عيّن العينات. راقب حجم البيانات نفسها؛ observability نظام إنتاجي وله ميزانية. ابدأ بالإشارات التي تجيب عن SLO، لا بجمع كل شيء.</p>
      `,
      walkthrough: [
        {
          title: "عرّف SLO",
          code: `SLO:\n- availability: 99.9% شهريًا\n- p95 latency: < 300ms\n- p99 latency: < 800ms\n- error rate: < 1%\n- outbox lag: < 60s`,
          lang: "text",
          body: `<p>ابدأ بالأهداف. بدون SLO، لا تعرف ما الذي يستحق تنبيهًا. اختر مؤشرات مرتبطة بتجربة المستخدم والعمليات. اكتب نافذة القياس (شهريًا/أسبوعيًا) ومصدر البيانات. SLO ليس وعدًا تسويقيًا؛ هو أداة قرار.</p>`
        },
        {
          title: "سجلات JSON منظمة",
          code: `builder.Host.UseSerilog((context, config) =>\n{\n    config.ReadFrom.Configuration(context.Configuration)\n          .Enrich.FromLogContext()\n          .WriteTo.Console(new JsonFormatter());\n});`,
          lang: "csharp",
          body: `<p><code>UseSerilog</code> يستبدل logging الافتراضي. <code>ReadFrom.Configuration</code> يجعل المستويات قابلة للضبط. <code>JsonFormatter</code> ينتج سجلات قابلة للفهرسة. لا تضع connection strings أو tokens في القالب. استخدم enrichers لإضافة environment/service/version.</p>`
        },
        {
          title: "اربط السجل بالـtrace",
          code: `app.Use(async (context, next) =>\n{\n    var traceId = Activity.Current?.TraceId.ToString()\n        ?? context.TraceIdentifier;\n\n    using (logger.BeginScope(new Dictionary<string, object>\n    {\n        ["TraceId"] = traceId\n    }))\n    {\n        await next();\n    }\n});`,
          lang: "csharp",
          body: `<p><code>Activity.Current</code> يأتي من OpenTelemetry/ASP.NET Core. <code>BeginScope</code> يضيف TraceId لكل سجل داخل الطلب. لا تسجّل معرف الجلسة أو التوكن. يمكنك استخدام <code>TraceIdentifier</code> كبديل عند غياب Activity. هذا الرابط يجعل البحث من metric إلى trace إلى log ممكنًا.</p>`
        },
        {
          title: "فعّل OpenTelemetry",
          code: `builder.Services.AddOpenTelemetry()\n    .ConfigureResource(r => r.AddService("Souq.Api"))\n    .WithTracing(t => t\n        .AddAspNetCoreInstrumentation()\n        .AddHttpClientInstrumentation()\n        .AddOtlpExporter())\n    .WithMetrics(m => m\n        .AddAspNetCoreInstrumentation()\n        .AddRuntimeInstrumentation()\n        .AddOtlpExporter());`,
          lang: "csharp",
          body: `<p>هذا يجمع traces من ASP.NET Core وHttpClient، وmetrics من runtime. <code>AddOtlpExporter</code> يرسل إلى Collector (Jaeger/Tempo/OTel). أضف <code>AddEntityFrameworkCoreInstrumentation</code> لرؤية SQL. لا تصدّر مباشرة إلى عدة أنظمة من التطبيق؛ اجعل Collector نقطة تجميع.</p>`
        },
        {
          title: "أنشئ metrics للأعمال",
          code: `private static readonly Meter Meter = new("Souq.Orders");\nprivate static readonly Counter<long> OrdersCreated =\n    Meter.CreateCounter<long>("orders.created");\nprivate static readonly Histogram<double> OrderValue =\n    Meter.CreateHistogram<double>("orders.value", "EGP");\n\nOrdersCreated.Add(1, new KeyValuePair<string, object?>("status", "placed"));\nOrderValue.Record(order.Total.Amount);`,
          lang: "csharp",
          body: `<p>Metrics الأعمال تكمل metrics البنية. احذر الكاردينالية: status محدود، لا userId. استخدم أسماء ثابتة ووحدات واضحة. سجّل بعد نجاح العملية، لا قبلها. إذا أردت قياس الفشل، أضف counter/بُعدًا منفصلًا. لا تضع قيمًا عالية التنوع في labels.</p>`
        },
        {
          title: "Health Checks منفصلة",
          code: `builder.Services.AddHealthChecks()\n    .AddNpgSql(connectionString, name: "db")\n    .AddCheck<OutboxLagHealthCheck>("outbox");\n\napp.MapHealthChecks("/health/live", new HealthCheckOptions\n{\n    Predicate = _ => false\n});\napp.MapHealthChecks("/health/ready");`,
          lang: "csharp",
          body: `<p><code>/health/live</code> لا يفحص أي اعتمادية؛ فقط العملية. <code>/health/ready</code> يفحص DB وOutbox. إذا فشل readiness، لا ترسل الحركة، لكن لا تعِد تشغيل التطبيق. إذا فشل liveness، قد يكون التعليق بحاجة restart. اضبط timeouts قصيرة حتى لا يتعلق الفحص.</p>`
        },
        {
          title: "أضف TraceId إلى الأخطاء",
          code: `return TypedResults.Problem(\n    title: "Unexpected error",\n    statusCode: 500,\n    extensions: new Dictionary<string, object?>\n    {\n        ["traceId"] = Activity.Current?.TraceId.ToString()\n    });`,
          lang: "csharp",
          body: `<p>traceId في ProblemDetails يسمح للدعم بربط شكوى المستخدم بالـtrace. لا ترجع stack trace أو SQL. أضف traceId أيضًا في السجلات. إذا لم يكن هناك Activity، استخدم معرفًا بديلًا. هذا الحقل يجب أن يكون ضمن عقد الأخطاء.</p>`
        },
        {
          title: "اضبط sampling",
          code: `t.SetSampler(new TraceIdRatioBasedSampler(0.1))\n .AddOtlpExporter();`,
          lang: "csharp",
          body: `<p>10% في الإنتاج يقلل التكلفة. لكن لا تفقد traces الأخطاء؛ استخدم sampler مخصصًا يحتفظ بها. في التطوير 100%. وثّق نسبة العينات عند تفسير الأرقام. لا تقارن عدد traces بعدد الطلبات دون مراعاة sampling.</p>`
        },
        {
          title: "أنشئ لوحة وتنبيهات",
          code: `Dashboard:\n- RPS / error rate / p95 / p99\n- CPU / GC / thread pool\n- DB connections / query time\n- Outbox lag / dead letters\n\nAlerts:\n- error rate > 2% لمدة 5 دقائق\n- p95 > 300ms لمدة 10 دقائق\n- outbox lag > 60s`,
          lang: "text",
          body: `<p>كل لوحة تخدم سؤالًا. ابدأ بـSLO. التنبيهات على أعراض المستخدم (latency/errors) وعلى تراكم Outbox. لا تنبّه على CPU منفردًا إلا إذا كان سببًا معروفًا. اربط كل تنبيه بـRunbook: ماذا تفحص، من تتصل، كيف تعيد الحالة.</p>`
        },
        {
          title: "اختبر المراقبة",
          code: `// أنشئ خطأً متعمدًا وتحقّق:\n// - log يحتوي TraceId\n// - trace يظهر الطلب والاستثناء\n// - metric error rate يزيد\n// - alert يصل للقناة الصحيحة`,
          lang: "text",
          body: `<p>المراقبة التي لا تُختبر تفشل وقت الحاجة. أضف تمرينًا: أوقف DB، أطلق خطأً، أبطئ استعلامًا، وتأكد من الإشارات والتنبيه. اختبر Runbook مع فريق. لا تنتظر حادثة حقيقية لاكتشاف أن dashboard فارغ.</p>`
        }
      ],
      compare: {
        intro: `<p>السجل النصي يخبرك أن شيئًا حدث؛ الإشارات المترابطة تخبرك أين ولماذا.</p>`,
        before: {
          label: "Console بلا سياق",
          lang: "csharp",
          title: "قبل",
          code: `Console.WriteLine("Order created " + order.Id);\n// 500 error: Something failed`,
          points: [
            "لا TraceId يربط الطلب بالسجل.",
            "لا metrics للاتجاه أو التنبيه.",
            "لا spans لمعرفة أين تأخر.",
            "رسالة الخطأ بلا سياق."
          ]
        },
        after: {
          label: "إشارات مترابطة",
          lang: "csharp",
          title: "بعد",
          code: `logger.LogInformation("Order {OrderId} created", order.Id);\nOrdersCreated.Add(1);\n// OpenTelemetry يضيف TraceId/SpanId تلقائيًا\n// ProblemDetails يحتوي traceId`,
          points: [
            "سجل منظم قابل للبحث.",
            "metric لعدد الطلبات/الأخطاء.",
            "trace يربط HTTP/DB/Outbox.",
            "traceId يربط شكوى المستخدم."
          ]
        },
        verdict: `<p>اجمع الإشارات الثلاث، واربطها بمعرف واحد. لا تجمع بيانات أكثر مما تستطيع استخدامه أو تأمينه.</p>`
      },
      internals: `
        <p>OpenTelemetry يبني <code>Activity</code> لكل عملية. Trace هو شجرة Activities، وSpan قطعة واحدة. W3C <code>traceparent</code> يمرر السياق عبر HTTP. ASP.NET Core وHttpClient وEF تنشئ spans تلقائيًا عند تفعيل instrumentation. الـCollector يستقبل OTLP ويصدّر للخلفيات.</p>
        <p>Metrics لها أنواع: Counter (تراكمي)، Histogram (توزيع)، Gauge (لحظي). الكاردينالية هي عدد التوليفات الفريدة للأبعاد. كل label جديد يضاعف الاحتمالات. لا تضع معرفات مستخدم/طلب. استخدم route template لا URL كاملًا.</p>
        <h3>Health Checks</h3>
        <p>Liveness يفشل يعني أعد التشغيل. Readiness يفشل يعني لا ترسل حركة. لا تضع فحص DB في liveness. اضبط timeout وفشلًا متسلسلًا. إذا كان الفحص بطيئًا، سيصبح هو المشكلة. اختبره عند إيقاف الاعتمادية.</p>
        <h3>التكلفة والخصوصية</h3>
        <p>Logs وtraces قد تحتوي PII. استخدم redaction وsampling وretention. لا تسجّل body كاملًا. راقب حجم البيانات. Observability الجيدة ليست «كل شيء»، بل الإشارات الصحيحة بأقل تكلفة. ابدأ بـSLO ثم أضف.</p>
      `,
      internalsTable: {
        head: ["الإشارة", "تجيب عن", "التكلفة"],
        rows: [
          ["Logs", "ماذا حدث ولماذا", "حجم كبير/PII"],
          ["Metrics", "هل هناك اتجاه/مشكلة", "كاردينالية"],
          ["Traces", "أين تأخر الطلب", "حجم/عينات"],
          ["Health", "هل نرسل حركة؟", "timeouts"],
          ["Alert", "من يستجيب الآن؟", "ضجيج إن زاد"]
        ]
      },
      tips: [
        {
          title: "اربط بالـTraceId",
          body: "اجعل logs وerrors تحمل TraceId. بدون الرابط، التحقيق يصبح تخمينًا."
        },
        {
          title: "راقب الأعراض",
          body: "ابدأ بـerror rate وp95/p99 وlag. لا تنبّه على كل مورد منفرد."
        },
        {
          title: "افصل liveness/readiness",
          body: "لا تفحص DB في liveness. readiness هي التي تقرر إرسال الحركة."
        },
        {
          title: "اختبر المراقبة",
          body: "أطلق خطأً متعمدًا وتحقق من السجل والـtrace والتنبيه. Runbook غير المختبَر وهم."
        }
      ],
      quiz: [
        {
          q: "ما الفرق بين liveness وreadiness؟",
          options: [
            "لا فرق.",
            "liveness: هل العملية حية؛ readiness: هل جاهزة لاستقبال الحركة.",
            "liveness يفحص قاعدة البيانات فقط.",
            "readiness يعيد تشغيل التطبيق."
          ],
          answer: 1,
          explain: "liveness يفشل -> restart. readiness يفشل -> لا ترسل حركة. لا تخلط فحص DB في liveness."
        },
        {
          q: "لماذا لا نضع userId كـmetric label؟",
          options: [
            "لأنه غير مفيد.",
            "لأنه يزيد الكاردينالية بشكل انفجاري.",
            "لأن Metrics لا تدعم النصوص.",
            "لأنه يبطئ JWT."
          ],
          answer: 1,
          explain: "كل قيمة فريدة تضاعف التوليفات. استخدم أبعادًا محدودة مثل status/route."
        },
        {
          q: "ما وظيفة Trace؟",
          options: [
            "قياس CPU فقط.",
            "تتبع مسار طلب عبر الخدمات/الاستعلامات وأزمنة spans.",
            "تخزين كلمات المرور.",
            "استبدال قاعدة البيانات."
          ],
          answer: 1,
          explain: "Trace يجمع spans لطلب واحد، فيظهر أين ذهب الوقت وأي خدمة أبطأت."
        }
      ],
      capstone: {
        title: "مراقبة Souq في الإنتاج",
        goal: "أضف logs/traces/metrics وhealth checks ولوحة SLO، واختبر الحالة الفاشلة.",
        tasks: [
          "اضبط Serilog JSON مع enrichers للبيئة والخدمة.",
          "أضف OpenTelemetry traces لـASP.NET Core وHttpClient وEF Core.",
          "أضف metrics لعدد الطلبات ومعدل الأخطاء وزمن الاستجابة.",
          "أضف <code>/health/live</code> و<code>/health/ready</code> مع فحص DB/Outbox.",
          "أطلق خطأً متعمدًا وتأكد من TraceId في السجل وProblemDetails والتنبيه."
        ],
        code: {
          lang: "csharp",
          title: "OTel",
          code: `builder.Services.AddOpenTelemetry()\n    .ConfigureResource(r => r.AddService("Souq.Api"))\n    .WithTracing(t => t.AddAspNetCoreInstrumentation()\n        .AddHttpClientInstrumentation().AddOtlpExporter());`,
        },
      },
    },
    {
      id: "ci-cd-cloud",
      title: "CI/CD: من Commit إلى نشر آمن",
      duration: 30,
      level: "متقدم",
      summary:
        "النشر اليدوي ليس عملية؛ هو حادثة تنتظر الحدوث. سنبني خط أنابيب يبني مرة، يختبر، يفحص، ينشر تدريجيًا، ويتيح rollback.",
      keywords: ["CI/CD", "GitHub Actions", "OIDC", "Docker", "artifact", "smoke test", "zero downtime", "rollback", "SBOM"],
      objectives: [
        "تبني pipeline من PR إلى الإنتاج.",
        "تبني artifact مرة واحدة وتنشره في كل بيئة.",
        "تفصل الهوية والأسرار عن المستودع.",
        "تنشر migrations وAPI دون توقف.",
        "تخطط rollback وSmoke Tests."
      ],
      concept: `
        <p><strong>CI</strong> يدمج التغييرات ويتحقق منها: build، analyzers، tests، فحص أمني. <strong>CD</strong> ينشر الناتج عبر بيئات. الهدف ليس «زر نشر» فقط؛ هو تقليل المخاطرة وتكرار العملية. النشر اليدوي يعتمد على ذاكرة شخص، والذاكرة تفشل تحت الضغط.</p>
        <h3>ابنِ مرة واحدة</h3>
        <p>ابنِ artifact/container مرة في CI ومرّره إلى staging/production. لا تعِد البناء لكل بيئة؛ قد تحصل على ناتج مختلف. استخدم صورة/حزمة بتاج ثابت (commit SHA)، لا <code>latest</code>. هذا يجعل ما اختبرته هو ما تنشره بالضبط. احتفظ بـchecksums/SBOM.</p>
        <h3>الأسرار والهوية</h3>
        <p>لا تضع مفاتيح النشر في GitHub Secrets طويلة العمر إن أمكن. استخدم OIDC لهوية قصيرة العمر مع السحابة. لا تطبع الأسرار في السجلات. فصل الصلاحيات: pipeline النشر لا يحتاج قراءة كل البيانات. دوّر المفاتيح. أي سر ظهر في commit اعتبره مسربًا حتى لو حذفته.</p>
        <h3>البيئات والبوابات</h3>
        <p>PR: build/test سريع. main: artifact + نشر staging تلقائي. Production: موافقة/بوابة، ثم نشر تدريجي. لا تجعل production بيئة اختبار. أضف smoke tests بعد النشر. إذا فشلت، أوقف الترويج. البيئات يجب أن تتشابه في الصورة والإعداد، وتختلف في القيم.</p>
        <h3>Migrations صفر توقف</h3>
        <p>لا تشغّل migrations من كل replica. استخدم job نشر واحد. اجعل التغيير متوافقًا: أضف عمودًا nullable، انشر الكود الذي يكتب/يقرأ، ثم املأ البيانات، ثم أضف NOT NULL في خطوة لاحقة. لا تحذف عمودًا يستخدمه الإصدار القديم قبل انتهاء rolling. اختبر migrations على نسخة تشبه الإنتاج.</p>
        <h3>Zero-downtime</h3>
        <p>Rolling أو Blue/Green. تأكد من readiness قبل استقبال الحركة. لا تقطع الاتصالات القائمة فجأة؛ اسمح بـdraining. استخدم إصدارات API متوافقة. اختبر سلوك الإصدارين معًا أثناء الانتقال. قاعدة البيانات هي غالبًا أصعب جزء، وليس الحاوية.</p>
        <h3>Rollback</h3>
        <p>خطة rollback ليست «أعد نشر القديم» فقط. هل المخطط متوافق مع القديم؟ هل البيانات الجديدة مفهومة؟ هل الرسائل/الأحداث متوافقة؟ اختبر rollback في staging. احتفظ بالإصدار السابق جاهزًا. راقب الأخطاء بعد النشر، وحدد معايير التراجع مسبقًا.</p>
      `,
      walkthrough: [
        {
          title: "CI للـPR",
          code: `on:\n  pull_request:\n    branches: [main]\n\njobs:\n  ci:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-dotnet@v4\n        with: { dotnet-version: "10.0.x" }\n      - run: dotnet restore\n      - run: dotnet build --no-restore -warnaserror\n      - run: dotnet test --no-build`,
          lang: "yaml",
          body: `<p>CI على PR يعطي تغذية راجعة قبل الدمج. <code>--no-restore</code> و<code>--no-build</code> يمنعان تكرار العمل. شغّل analyzers وtests. أضف cache للحزم لتسريع. لا تنشر من PR. إذا كان build بطيئًا، افصل jobs لكن لا تتخلَّ عن البوابة.</p>`
        },
        {
          title: "ابنِ صورة Docker",
          code: `- run: docker build -t souq-api:\${{ github.sha }} .\n- run: docker push ghcr.io/org/souq-api:\${{ github.sha }}`,
          lang: "yaml",
          body: `<p>استخدم commit SHA كتاج ثابت. لا تستخدم <code>latest</code> للإنتاج. ابنِ multi-stage لتقليل حجم الصورة. ثبّت الإصدارات. ادفع إلى registry آمن. نفس الصورة تُنشر في staging وproduction. لا تعِد بناءها هناك.</p>`
        },
        {
          title: "افحص الصورة",
          code: `- run: trivy image --exit-code 1 \\\n    --severity HIGH,CRITICAL souq-api:\${{ github.sha }}`,
          lang: "yaml",
          body: `<p>فحص الثغرات جزء من CI. <code>--exit-code 1</code> يوقف البناء عند ثغرة عالية. لا تفحص فقط الحزم؛ افحص الصورة النهائية. أنشئ SBOM. راجع النتائج بدل تجاهلها. بعض الثغرات تحتاج ترقية أساس أو استثناءًا موثقًا.</p>`
        },
        {
          title: "انشر staging",
          code: `- name: Deploy staging\n  run: ./deploy.sh staging \${{ github.sha }}\n  env:\n    CLOUD_TOKEN: \${{ secrets.CLOUD_TOKEN }}`,
          lang: "yaml",
          body: `<p>staging تلقائي من main بعد نجاح CI. استخدم نفس الصورة. مرّر التاج لا المصدر. لا تضع الأسرار في السجل. الأفضل OIDC بدل token طويل العمر. تأكد من أن staging تشبه production في الإعداد والاعتماديات.</p>`
        },
        {
          title: "Smoke Tests",
          code: `- run: ./scripts/smoke.sh https://staging.souq.example\n# GET /health/ready -> 200\n# GET /api/v1/products -> 200\n# POST /api/v1/orders -> 201`,
          lang: "yaml",
          body: `<p>Smoke tests تتحقق من المسارات الحرجة بعد النشر. ليست بديلًا عن اختبارات التكامل، لكنها تكشف فشل النشر/الإعداد. اختبر health وreadiness وطلبًا حقيقيًا آمنًا. إذا فشلت، أوقف الترويج. لا تنشئ بيانات حقيقية خطيرة.</p>`
        },
        {
          title: "بوابة الإنتاج",
          code: `environment:\n  name: production\n  url: https://api.souq.example\n# يتطلب مراجعة/موافقة قبل التنفيذ`,
          lang: "yaml",
          body: `<p>استخدم GitHub Environments لحماية production. الموافقة ليست بيروقراطية؛ هي نقطة وعي. أضف قائمة تحقق: migrations، feature flags، مراقبة، rollback. لا تجعل النشر التلقائي الكامل هو الافتراضي لنظام مالي حساس.</p>`
        },
        {
          title: "Migration Job منفصل",
          code: `- name: Migrate\n  run: dotnet ef database update \\\n    --project src/Souq.Api --no-build\n  env:\n    ConnectionStrings__Souq: \${{ secrets.PROD_DB }}`,
          lang: "yaml",
          body: `<p>شغّل migration مرة واحدة قبل/أثناء النشر حسب التوافق. لا تجعل كل replica تشغّلها. اختبر على staging. استخدم connection محدود الصلاحيات. خذ نسخة احتياطية عند التغييرات الخطيرة. لا تطبّق migration حذفية قبل التأكد من توافق الإصدار القديم.</p>`
        },
        {
          title: "نشر تدريجي",
          code: `kubectl set image deployment/souq-api \\\n  api=ghcr.io/org/souq-api:\${SHA}\nkubectl rollout status deployment/souq-api`,
          lang: "bash",
          body: `<p>Rolling يحدّث replicas تدريجيًا. <code>rollout status</code> ينتظر النتيجة. readiness تمنع حركة قبل الجاهزية. استخدم maxUnavailable/maxSurge مناسبًا. راقب error rate وp95 أثناء النشر. إذا ارتفعت، أوقف/ارجع.</p>`
        },
        {
          title: "Rollback محسوب",
          code: `kubectl rollout undo deployment/souq-api\nkubectl rollout status deployment/souq-api`,
          lang: "bash",
          body: `<p>الرجوع للمانيفست السابق سريع، لكنه لا يعيد schema/data. تأكد أن migration الجديدة متوافقة مع القديم. اختبر rollback. وثّق متى تتراجع: error rate، p95، health. لا تنتظر ساعة لتقرر.</p>`
        },
        {
          title: "راقب وأغلق الحلقة",
          code: `# بعد النشر:\n# - error rate < 1%\n# - p95 < 300ms\n# - readiness 200\n# - outbox lag < 60s\n# - لا زيادة في 5xx`,
          lang: "text",
          body: `<p>النشر لا ينتهي عند نجاح الأمر. راقب SLO لمدة كافية. اربط الحوادث بالـtrace. أضف ما تعلمته إلى Runbook. كل فشل نشر يجب أن ينتج تحسينًا في pipeline، لا لومًا. الأتمتة الجيدة تقلل التغيير البشري.</p>`
        }
      ],
      compare: {
        intro: `<p>النشر اليدوي يعتمد على الذاكرة؛ pipeline يعتمد على خطوات قابلة للتكرار.</p>`,
        before: {
          label: "نشر يدوي",
          lang: "bash",
          title: "قبل",
          code: `dotnet publish -c Release\nscp -r publish/ server:/app\nssh server "systemctl restart souq"`,
          points: [
            "بناء مختلف لكل بيئة.",
            "لا اختبارات/فحص أمني.",
            "لا rollback واضح.",
            "الأسرار على الجهاز."
          ]
        },
        after: {
          label: "Pipeline",
          lang: "yaml",
          title: "بعد",
          code: `- run: dotnet build -warnaserror\n- run: dotnet test\n- run: docker build -t api:\${{ github.sha }} .\n- run: ./deploy.sh staging \${{ github.sha }}\n- run: ./scripts/smoke.sh https://staging.souq.example`,
          points: [
            "نفس artifact لكل بيئة.",
            "بوابات جودة وأمان.",
            "Smoke tests بعد النشر.",
            "تاج ثابت وrollback."
          ]
        },
        verdict: `<p>CI/CD ليست رفاهية للفرق الكبيرة. حتى مشروع فردي يستفيد من تكرار النشر وتقليل الخطأ اليدوي.</p>`
      },
      internals: `
        <p>CI runner يبدأ بيئة نظيفة، يستعيد الكود، يبني، يختبر، ثم ينتج artifact. الـartifact يجب أن يكون immutable وقابلًا للتتبع بـcommit SHA. CD يروّج نفس الـartifact عبر البيئات. لا تعِد البناء في production.</p>
        <h3>OIDC</h3>
        <p>بدل تخزين مفتاح سحابي دائم، يطلب runner token قصير العمر من مزود الهوية، ويتبادله مع السحابة. تقلل خطر تسرب المفتاح. اضبط شروط المستودع/الفرع. لا تمنح صلاحية نشر لكل PR.</p>
        <h3>Zero-downtime</h3>
        <p>Rolling يعتمد على readiness وconnection draining. Blue/Green يبدّل الحركة بين بيئتين. Canary يوجّه نسبة صغيرة. كلها تحتاج توافق API/DB. لا تفترض أن الحاوية الجديدة وحدها تكفي إذا كانت migration كاسرة.</p>
        <h3>Rollback</h3>
        <p>الرجوع للكود لا يعيد البيانات. اجعل migrations متوافقة مع الإصدار السابق (expand/contract). اختبر rollback مع بيانات. احتفظ بالإصدار السابق. راقب مؤشرات القرار. Runbook يحدد من ينفذ ومتى.</p>
      `,
      internalsTable: {
        head: ["المرحلة", "الهدف", "الخطر"],
        rows: [
          ["Build", "artifact واحد", "بناء مختلف لكل بيئة"],
          ["Test", "منع الانحدار", "اختبارات بطيئة/غير حاسمة"],
          ["Scan", "ثغرات الحزم/الصورة", "تجاهل النتائج"],
          ["Staging", "بيئة مشابهة", "اختلاف الإعداد"],
          ["Migration", "مخطط متوافق", "توقف/فقد بيانات"],
          ["Rollback", "عودة سريعة", "عدم توافق schema"]
        ]
      },
      tips: [
        {
          title: "ابنِ مرة واحدة",
          body: "مرّر نفس الصورة/الحزمة عبر البيئات. التاج commit SHA، لا latest."
        },
        {
          title: "أمن pipeline",
          body: "OIDC وأسرار قصيرة العمر. لا تطبع الأسرار. افحص الصورة وأنشئ SBOM."
        },
        {
          title: "Migrations متوافقة",
          body: "Expand/contract. لا تحذف عمودًا قبل توقف الإصدار القديم. اختبر على staging."
        },
        {
          title: "Rollback مختبَر",
          body: "الكود وحده لا يكفي. خطط للبيانات والتوافق، واختبر الرجوع فعليًا."
        }
      ],
      quiz: [
        {
          q: "لماذا نبني artifact مرة واحدة؟",
          options: [
            "لتقليل عدد الملفات.",
            "لضمان أن ما اختُبر هو ما يُنشر في كل بيئة.",
            "لأن Docker يمنع البناء المتعدد.",
            "لإلغاء الاختبارات."
          ],
          answer: 1,
          explain: "البناء لكل بيئة قد ينتج ناتجًا مختلفًا. نفس الصورة/الحزمة تضمن التطابق."
        },
        {
          q: "ما فائدة OIDC في CI/CD؟",
          options: [
            "يسرّع Docker.",
            "هوية قصيرة العمر بدل مفاتيح سحابية دائمة.",
            "يخفي أخطاء الاختبار.",
            "ينشر تلقائيًا بلا مراجعة."
          ],
          answer: 1,
          explain: "OIDC يتبادل token قصير العمر، ويقلل خطر تسرب مفاتيح النشر."
        },
        {
          q: "ما شرط zero-downtime مع migrations؟",
          options: [
            "حذف الجدول مباشرة.",
            "تغيير متوافق مع الإصدار القديم والجديد (expand/contract).",
            "تشغيل migration من كل replica.",
            "إيقاف قاعدة البيانات."
          ],
          answer: 1,
          explain: "أثناء rolling تعمل النسختان. يجب أن يكون المخطط متوافقًا معهما."
        }
      ],
      capstone: {
        title: "Pipeline نشر Souq",
        goal: "أنشئ CI/CD يبني ويختبر وينشر staging ثم production ببوابة وrollback.",
        tasks: [
          "أضف GitHub Actions للـPR: restore/build/test/analyzers.",
          "ابنِ صورة Docker بتاج commit SHA وافحصها أمنيًا.",
          "انشر staging تلقائيًا ونفّذ smoke tests.",
          "أضف job migration منفصلًا قبل النشر مع اختبار توافق.",
          "أضف بوابة production واختبر rollback ومراقبة SLO بعد النشر."
        ],
        code: {
          lang: "yaml",
          title: "CI",
          code: `- run: dotnet build --no-restore -warnaserror\n- run: dotnet test --no-build\n- run: docker build -t souq-api:\${{ github.sha }} .`,
        },
      },
    },
  ],
});
