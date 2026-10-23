/* الوحدة 3 — Dependency Injection، والوحدة 4 — Middleware Pipeline. */
Academy.addModule({
  id: "di",
  title: "Dependency Injection",
  tagline: "الحاوية ليست صندوقًا سحريًا: هي دورة حياة ونطاقات وقرارات تصميم. أتقنها أو ستطارد أخطاء لا تُنسى.",
  icon: "◉",
  color: "#a78bfa",
  lessons: [
    {
      id: "di-lifetimes",
      title: "Dependency Injection: Transient / Scoped / Singleton",
      duration: 24,
      level: "متوسط",
      summary:
        "لماذا لا نكتب new داخل كل نقطة نهاية؟ وكيف تقرر الحاوية متى تنشئ الكائن ومتى تعيد استخدامه؟ سنفهم النطاقات من الجذر إلى الطلب، ونربطها بـ DbContext.",
      keywords: ["Dependency Injection", "IoC", "Transient", "Scoped", "Singleton", "IServiceScope", "DbContext"],
      objectives: [
        "تشرح كيف تحلّ الحاوية التبعيات عبر constructor injection.",
        "تميّز بين الأنماط الثلاثة وتختار النمط الصحيح لكل خدمة.",
        "تفهم الفرق بين Root Provider وRequest Scope.",
        "تعرف لماذا DbContext يجب أن يكون Scoped.",
      ],
      concept: `
        <p><strong>Dependency Injection</strong> ليست مكتبة؛ إنها نمط تصميم: الكائن لا يصنع تبعياته بنفسه، بل يطلبها في مُنشئه. الحاوية مسؤولة عن إنشاء الشجرة كاملة. الفائدة ليست «كودًا أقل» بل <strong>حدودًا قابلة للاستبدال</strong>: يمكنك استبدال تنفيذ قاعدة البيانات بآخر وهمي في الاختبار، دون لمس منطق العمل.</p>
        <p>في ASP.NET Core الحاوية مدمجة: <code>IServiceCollection</code> للتسجيل، و<code>IServiceProvider</code> للحل. عند كتابة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>app.MapGet("/products", (IProductService service) => service.GetAll());</code></pre>
        <p>فأنت لا تستدعي الحاوية يدويًا. إطار العمل Minimal API يقرأ توقيع الدالة، يرى <code>IProductService</code>، فيطلبه من نطاق الطلب الحالي ويمرّره.</p>
        <h3>الأنماط الثلاثة</h3>
        <ul>
          <li><strong>Transient</strong>: كائن جديد في كل مرة يُطلب فيها. مناسب للخدمات الخفيفة عديمة الحالة (مثل <code>IEmailSender</code> أو <code>IValidator</code>).</li>
          <li><strong>Scoped</strong>: كائن واحد لكل <em>نطاق</em>. في ASP.NET Core النطاق = طلب HTTP واحد. مناسب لـ <code>DbContext</code> والخدمات التي تحمل حالة الطلب.</li>
          <li><strong>Singleton</strong>: كائن واحد لعمر التطبيق كله. مناسب للذاكرة المؤقتة والإعدادات الثابتة وعملاء HTTP المُعاد استخدامهم. يجب أن يكون آمنًا للخيوط (thread-safe).</li>
        </ul>
        <p>الخطأ الأخطر هو <strong>Captive Dependency</strong>: خدمة Singleton تحتفظ بخدمة Scoped. عندها يبقى كائن الطلب الأول حيًّا إلى الأبد، ويخدم كل الطلبات اللاحقة — وكأنك أعطيت كل زائر نفس المفتاح. الحاوية في التطوير قد ترمي استثناءً عند حلّ Scoped من الجذر، لكنها لا تلتقط كل الحالات. القاعدة: <em>لا تحقن Scoped في Singleton أبدًا</em>.</p>
        <h3>لماذا DbContext بالذات Scoped؟</h3>
        <p><code>DbContext</code> ليس اتصالًا واحدًا؛ هو <strong>وحدة عمل</strong> (Unit of Work) تحمل <em>Change Tracker</em> لكل الكائنات التي قرأتها أو عدّلتها. لو كان Singleton، لتراكمت الكائنات في الذاكرة، واختلطت تغييرات الطلبات، وفسدت سلامة البيانات. لهذا <code>AddDbContext</code> يسجّله Scoped افتراضيًا، ولهذا لا يجوز استخدامه في خدمة Singleton أو في BackgroundService مباشرة.</p>
      `,
      compare: {
        intro: `<p>المقارنة ليست «new مقابل DI» فقط؛ إنها الفرق بين كود يعرف كيف تُبنى تبعياته وكود يعرف فقط ما يحتاجه.</p>`,
        before: {
          label: "إنشاء يدوي داخل كل endpoint",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapGet("/api/products", () =>
{
    // كل طلب ينشئ اتصالاً ومُرسِل بريد وخدمة من الصفر
    using var db = new SouqDbContext();
    var email = new SmtpEmailSender("smtp.example.com");
    var service = new ProductService(db, email);

    return Results.Ok(service.GetAll());
});

app.MapPost("/api/products", (CreateProductRequest request) =>
{
    using var db = new SouqDbContext();          // تكرار
    var email = new SmtpEmailSender("smtp...");   // إعداد مكرر
    var service = new ProductService(db, email);
    service.Create(request);
    return Results.Created();
});`,
          points: [
            "إعدادات مكررة في كل نقطة نهاية.",
            "استبدال التنفيذ في الاختبار صعب.",
            "نسيان Dispose أو استخدام اتصال خاطئ وارد جدًا.",
          ],
        },
        after: {
          label: "تسجيل في الحاوية",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services.AddScoped<SouqDbContext>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddSingleton<IClock, SystemClock>();
builder.Services.AddTransient<IEmailSender, SmtpEmailSender>();

var app = builder.Build();

app.MapGet("/api/products", async (IProductService service, CancellationToken ct) =>
    TypedResults.Ok(await service.GetAllAsync(ct)));

app.MapPost("/api/products", async (
    CreateProductRequest request,
    IProductService service,
    CancellationToken ct) =>
{
    var id = await service.CreateAsync(request, ct);
    return TypedResults.Created($"/api/products/{id}", id);
});`,
          points: [
            "كل نقطة نهاية تعلن احتياجها فقط.",
            "الحاوية تدير العمر والـ Dispose.",
            "الاستبدال في الاختبار سطر واحد.",
          ],
        },
        verdict: `<p>DI لا يجعل الكود أقصر دائمًا، لكنه يجعل <strong>الحدود</strong> واضحة. عندما يصبح <code>IProductService</code> واجهة، يمكنك اختبار الـ endpoint بخدمة وهمية دون قاعدة بيانات، وتغيير التنفيذ دون إعادة كتابة نقاط النهاية.</p>`,
      },
      walkthrough: [
        {
          title: "سجّل الخدمات",
          code: `builder.Services.AddTransient<IEmailSender, SmtpEmailSender>();\nbuilder.Services.AddScoped<IProductService, ProductService>();\nbuilder.Services.AddDbContext<SouqDbContext>(o =>\n    o.UseNpgsql(connectionString));\nbuilder.Services.AddSingleton<IClock, SystemClock>();`,
          lang: "csharp",
          body: `<p>كل سطر يحدد عمر الخدمة. <code>Transient</code> لكائن جديد كل طلب، <code>Scoped</code> لواحد لكل طلب HTTP، و<code>Singleton</code> لواحد للتطبيق. <code>AddDbContext</code> يسجّل الـcontext Scoped افتراضيًا. لا تسجّل <code>DbContext</code> Singleton.</p>`
        },
        {
          title: "اطلب التبعية في المُنشئ",
          code: `public sealed class ProductService(\n    SouqDbContext db,\n    IEmailSender email,\n    IClock clock) : IProductService\n{\n    public async Task<Product> CreateAsync(CreateProduct request)\n    {\n        var product = Product.Create(request.Name, request.Price, clock.UtcNow);\n        db.Products.Add(product);\n        await db.SaveChangesAsync();\n        await email.SendAsync(request.OwnerEmail, "Product created");\n        return product;\n    }\n}`,
          lang: "csharp",
          body: `<p>الحاوية تمرّر التبعيات. لا تستدعي <code>new SouqDbContext()</code> داخل الخدمة. <code>IClock</code> يجعل الوقت قابلًا للاختبار. <code>IEmailSender</code> يسمح باستبداله بـfake. لاحظ أن كل التبعيات تُحل من نطاق الطلب الحالي.</p>`
        },
        {
          title: "Transient: كائن لكل طلب",
          code: `public sealed class PriceFormatter : IPriceFormatter\n{\n    private readonly StringBuilder _buffer = new();\n\n    public string Format(decimal amount) =>\n        _buffer.Clear().Append(amount.ToString("0.00")).ToString();\n}`,
          lang: "csharp",
          body: `<p>Transient مناسب للكائنات الخفيفة عديمة الحالة. لكن هذا المثال يحمل <code>StringBuilder</code> كحالة؛ إذا سُجّل Singleton، ستتداخل الطلبات. حتى Transient ليس آمنًا إذا احتُجز في Singleton. القاعدة: الحالة الخاصة بالطلب تبقى Scoped/Transient.</p>`
        },
        {
          title: "Scoped: وحدة عمل للطلب",
          code: `app.MapPost("/api/products", async (\n    CreateProduct request,\n    IProductService service) =>\n{\n    var product = await service.CreateAsync(request);\n    return TypedResults.Created($"/api/products/{product.Id}", product.Id);\n});`,
          lang: "csharp",
          body: `<p>كل طلب HTTP يحصل على نطاقه الخاص. <code>ProductService</code> و<code>DbContext</code> يشاركان النطاق، فالتغييرات تُحفظ مرة واحدة. لا تمرّر <code>DbContext</code> إلى مهمة خلفية تعيش بعد الطلب. أنشئ نطاقًا جديدًا هناك.</p>`
        },
        {
          title: "Singleton: حالة مشتركة وآمنة",
          code: `public sealed class InMemoryCatalogCache : ICatalogCache\n{\n    private readonly ConcurrentDictionary<Guid, ProductDto> _items = new();\n\n    public bool TryGet(Guid id, out ProductDto? product) =>\n        _items.TryGetValue(id, out product);\n\n    public void Set(ProductDto product) =>\n        _items[product.Id] = product;\n}`,
          lang: "csharp",
          body: `<p>Singleton يعيش مع التطبيق. استخدم بنية thread-safe مثل <code>ConcurrentDictionary</code>. لا تحتفظ بـ<code>DbContext</code> أو <code>HttpContext</code> هنا. إذا احتجت بيانات طلب، مرّرها كوسيط. اختبر التزامن. الذاكرة تنمو بلا حد؛ أضف سياسة إخلاء.</p>`
        },
        {
          title: "نطاق جديد في BackgroundService",
          code: `public sealed class OutboxWorker(\n    IServiceScopeFactory scopeFactory,\n    ILogger<OutboxWorker> logger) : BackgroundService\n{\n    protected override async Task ExecuteAsync(CancellationToken ct)\n    {\n        while (!ct.IsCancellationRequested)\n        {\n            using var scope = scopeFactory.CreateScope();\n            var db = scope.ServiceProvider.GetRequiredService<SouqDbContext>();\n            await PublishPendingAsync(db, ct);\n            await Task.Delay(TimeSpan.FromSeconds(5), ct);\n        }\n    }\n}`,
          lang: "csharp",
          body: `<p>الخدمة الخلفية Singleton بطبيعتها. لا تحقن <code>DbContext</code> مباشرة. استخدم <code>IServiceScopeFactory</code> وأنشئ نطاقًا لكل دورة عمل. لا تنسَ cancellation. لا تمسك النطاق طوال عمر التطبيق. هذا يمنع Captive Dependency وتسريب الحالة.</p>`
        },
        {
          title: "Captive Dependency",
          code: `// خطأ: Singleton يحتفظ بخدمة Scoped\nbuilder.Services.AddSingleton<ReportService>();\nbuilder.Services.AddScoped<SouqDbContext>();\n\npublic sealed class ReportService(SouqDbContext db) { }`,
          lang: "csharp",
          body: `<p>هذه أخطر مصيدة. <code>ReportService</code> Singleton سيحتفظ بأول <code>DbContext</code> إلى الأبد، فيخدم كل الطلبات بنفس الحالة. الحل: اجعل الخدمة Scoped، أو استخدم <code>IServiceScopeFactory</code> عند الحاجة. فعّل التحقق من النطاقات في التطوير.</p>`
        },
        {
          title: "تحقق عند البناء",
          code: `builder.Host.UseDefaultServiceProvider(options =>\n{\n    options.ValidateScopes = true;\n    options.ValidateOnBuild = true;\n});`,
          lang: "csharp",
          body: `<p><code>ValidateScopes</code> يكتشف حل Scoped من الجذر. <code>ValidateOnBuild</code> يفشل مبكرًا إذا كانت تبعية غير مسجلة. استخدمهما في التطوير/الاختبار. لا تعتمد على اكتشاف الخطأ في الإنتاج. راجع التسجيلات عند كل خدمة جديدة.</p>`
        }
      ],
      internals: `
        <p>عند التسجيل، تُخزَّن <code>ServiceDescriptor</code>: نوع الخدمة، نوع التنفيذ، والعمر. عند أول طلب، تبني الحاوية <strong>Call Site</strong> وتُجمّعه إلى تعبير (expression) قابل للتنفيذ، ثم تخزّنه. لهذا حلّ خدمة للمرة الثانية أسرع من الأولى؛ لا يوجد Reflection في كل طلب.</p>
        <p><strong>النطاق</strong> هو <code>IServiceScope</code> يحمل <code>IServiceProvider</code> فرعيًا. في ASP.NET Core، كل طلب HTTP ينشئ نطاقًا، وفي نهايته تُستدعى <code>Dispose</code> على كل الخدمات Scoped التي تنفّذ <code>IDisposable</code>. هذا هو المكان الذي يُغلق فيه اتصال DbContext ويعود إلى البركة.</p>
        <p><strong>Singleton</strong> يُنشأ كسولًا (lazy) عند أول طلب، والحاوية تضمن إنشاء نسخة واحدة حتى مع طلبات متزامنة عبر قفل داخلي. لكنها لا تضمن أن الكود داخله آمن للخيوط. إذا كان Singleton يعدّل <code>Dictionary</code> بلا قفل، فأنت أمام حالة سباق (race condition) لا يكتشفها المترجم.</p>
        <p>في التطوير، ASP.NET Core يفعّل <code>ValidateScopes</code> و<code>ValidateOnBuild</code>. الأول يرمي إذا حللت Scoped من الجذر، والثاني يتحقق من إمكانية بناء كل التسجيلات عند الإقلاع. في الإنتاج يُعطَّلان للأداء، لذا لا تعتمد على اكتشاف الخطأ هناك.</p>
      `,
      internalsTable: {
        head: ["العمر", "متى يُنشأ؟", "متى يُدمَّر؟", "أمثلة"],
        rows: [
          ["Transient", "كل طلب حل", "مع نهاية النطاق الحاوي", "Validators, EmailSender"],
          ["Scoped", "مرة لكل نطاق/طلب", "نهاية الطلب", "DbContext, UnitOfWork, CurrentUser"],
          ["Singleton", "مرة لكل تطبيق", "إيقاف التطبيق", "Cache, Clock, HttpClientFactory"],
        ],
      },
      tips: [
        {
          title: "لا تستخدم Service Locator",
          body: "استدعاء <code>provider.GetService&lt;T&gt;()</code> داخل منطق العمل يخفي التبعيات ويكسر الاختبار. اطلبها في المُنشئ أو في توقيع الـ endpoint.",
        },
        {
          title: "لا تحقن IServiceProvider",
          body: "حقن الحاوية نفسها يعني أنك ستحلّ خدمات عشوائيًا لاحقًا. استثناء مشروع: مكتبات البناء مثل MediatR تحتاجها داخليًا، لا كودك.",
        },
        {
          title: "اجعل Singleton بلا حالة",
          body: "أي حقل قابل للتغيير في Singleton يُشارَك بين كل المستخدمين. استخدم <code>ConcurrentDictionary</code> أو <code>IMemoryCache</code> بدلًا من Dictionary عادي.",
        },
        {
          title: "استخدم AddHttpClient",
          body: "لا تنشئ <code>new HttpClient()</code> لكل طلب (استنزاف sockets) ولا Singleton واحد (DNS قديم). <code>AddHttpClient&lt;T&gt;()</code> يدير البركة ودورة حياة المقبس.",
        },
      ],
      quiz: [
        {
          q: "أي عمر مناسب لـ DbContext في Web API؟",
          options: ["Singleton", "Scoped (لكل طلب)", "Transient لكل استعلام", "Static"],
          answer: 1,
          explain:
            "DbContext وحدة عمل تحمل Change Tracker. Scoped يضمن نطاقًا نظيفًا لكل طلب وتدميرًا صحيحًا في نهايته.",
        },
        {
          q: "ماذا يحدث إذا حقنت خدمة Scoped داخل Singleton؟",
          options: [
            "تعمل الحاوية على تجديدها تلقائيًا كل طلب.",
            "تُحتجَز نسخة الطلب الأول وتُستخدم لكل الطلبات (Captive Dependency).",
            "يتحول Singleton إلى Scoped تلقائيًا.",
            "لا يعمل التطبيق إطلاقًا في كل الحالات.",
          ],
          answer: 1,
          explain:
            "Singleton يُنشأ مرة واحدة، فتبقى تبعيته Scoped حيّة معه. هذا يسبب تسريب حالة بين الطلبات وأخطاء يصعب تتبعها.",
        },
        {
          q: "ما الذي يضمنه تسجيل خدمة كـ Singleton؟",
          options: [
            "أنها آمنة للخيوط تلقائيًا.",
            "أنها تُنشأ مرة واحدة لعمر التطبيق، دون ضمان سلامة الخيوط.",
            "أنها تُدمَّر بعد كل طلب.",
            "أنها أسرع من Scoped دائمًا.",
          ],
          answer: 1,
          explain:
            "الحاوية تضمن نسخة واحدة فقط. أما سلامة الخيوط فمسؤوليتك أنت في تصميم الخدمة.",
        },
      ],
      capstone: {
        title: "تسجيل خدمات Souq.NET",
        goal: "نبدأ طبقة التطبيق: واجهة خدمة منتجات وتنفيذها، مع تسجيل صحيح للعمر، ونقطة نهاية تثبت أن الحقن يعمل.",
        tasks: [
          "أنشئ <code>IProductService</code> و<code>ProductService</code>.",
          "سجّل <code>ProductService</code> كـ Scoped و<code>IClock</code> كـ Singleton.",
          "أضف <code>GET /api/di-check</code> تحقن الخدمتين وتعيد <code>HashCode</code> لكل منهما.",
          "أرسل طلبين متتاليين: يجب أن يتغيّر HashCode للـ Scoped ويثبت للـ Singleton.",
          "أضف تعليقًا في الكود يوضح سبب اختيار كل عمر.",
        ],
        code: {
          lang: "csharp",
          title: "التحقق من الأنماط",
          code: `app.MapGet("/api/di-check", (IProductService scoped, IClock singleton) =>
    Results.Ok(new
    {
        scoped = scoped.GetHashCode(),
        singleton = singleton.GetHashCode(),
        note = "أرسل الطلب مرتين: scoped يتغير، singleton يثبت"
    }));

public interface IClock { DateTimeOffset UtcNow { get; } }
public sealed class SystemClock : IClock
{
    public DateTimeOffset UtcNow => DateTimeOffset.UtcNow;
}`,
        },
      },
    },
    {
      id: "di-pitfalls",
      title: "مصائد DI: Captive Dependencies وإعداد Options",
      duration: 23,
      level: "متقدم",
      summary:
        "الحاوية لا تحمي نفسها من كل خطأ. سنرى كيف تتسرّب الخدمات، وكيف نربط الإعداد بأنواع مع تحقق عند البدء، ونستخدم Keyed Services بذكاء.",
      keywords: ["IOptions", "IOptionsSnapshot", "IOptionsMonitor", "ValidateOnStart", "Keyed Services", "captive dependency"],
      objectives: [
        "تكتشف Captive Dependency وتصلحها.",
        "تختار بين IOptions وIOptionsSnapshot وIOptionsMonitor.",
        "تفعّل التحقق من الإعداد عند بدء التطبيق.",
        "تستخدم Keyed Services لاختيار تنفيذ حسب المفتاح.",
      ],
      concept: `
        <p>الخطأ الكلاسيكي لا يظهر في الترجمة: خدمة <code>Singleton</code> تحقن <code>DbContext</code>، فيعمل التطبيق في البداية ثم يبدأ بإرجاع بيانات قديمة أو يرمي «A second operation started on this context». السبب ليس EF Core، بل أنك أعطيت كل الطلبات نفس الـ Context.</p>
        <p>الحل ليس دائمًا «غيّر Singleton إلى Scoped». أحيانًا تحتاج Singleton فعلًا، لكنه يحتاج Scoped لكل عملية. هنا تستخدم <strong><code>IServiceScopeFactory</code></strong>:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>using var scope = _scopeFactory.CreateScope();
var db = scope.ServiceProvider.GetRequiredService&lt;SouqDbContext&gt;();</code></pre>
        <p>هذا هو النمط الصحيح داخل <code>BackgroundService</code>: الخدمة الخلفية Singleton، لكنها تفتح نطاقًا لكل دورة عمل.</p>
        <h3>Options: لا تقرأ النص مباشرة</h3>
        <p>قراءة <code>Configuration[\"Jwt:Key\"]</code> في كل مكان تجعل الإعداد نصًا سحريًا بلا نوع ولا تحقق. الأنماط الثلاثة:</p>
        <ul>
          <li><code>IOptions&lt;T&gt;</code>: Singleton، تُحسب مرة واحدة. مناسبة للإعدادات الثابتة.</li>
          <li><code>IOptionsSnapshot&lt;T&gt;</code>: Scoped، تُعاد قراءتها كل طلب. مناسبة للقيم التي تتغيّر دون إعادة تشغيل، لكنها تكلّف قليلًا.</li>
          <li><code>IOptionsMonitor&lt;T&gt;</code>: Singleton مع إشعارات تغيير عبر <code>OnChange</code>. مناسبة للخدمات طويلة العمر مثل Singleton يريد معرفة التحديث.</li>
        </ul>
        <p>والأهم: <strong>التحقق</strong>. أضف <code>ValidateDataAnnotations()</code> و<code>ValidateOnStart()</code>، فيفشل التطبيق عند الإقلاع إذا كان المفتاح ناقصًا أو الرابط خاطئًا. الفشل المبكر أرحم من فشل عند أول طلب حقيقي في الإنتاج.</p>
        <h3>Keyed Services</h3>
        <p>أحيانًا تحتاج أكثر من تنفيذ لنفس الواجهة: مزوّد دفع محلي وآخر دولي، أو مخزنان. بدلًا من مصنع يدوي، سجّل بمفتاح:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>builder.Services.AddKeyedScoped&lt;IPaymentGateway, StripeGateway&gt;("stripe");
builder.Services.AddKeyedScoped&lt;IPaymentGateway, PaymobGateway&gt;("paymob");</code></pre>
        <p>ثم اطلبها بـ <code>[FromKeyedServices(\"stripe\")]</code> أو <code>GetRequiredKeyedService</code>. هذا يحافظ على حدود واضحة بدل شجرة <code>if</code> في المصنع.</p>
      `,
      compare: {
        intro: `<p>الفرق بين إعداد مبعثر وإعداد مُصنّف يظهر عند أول قيمة ناقصة في الإنتاج.</p>`,
        before: {
          label: "قراءة نصية متكررة",
          lang: "csharp",
          title: "Program.cs",
          code: `var key = builder.Configuration["Jwt:Key"];      // قد تكون null
var issuer = builder.Configuration["Jwt:Issuer"]; // نص بلا تحقق
var minutes = int.Parse(
    builder.Configuration["Jwt:ExpiryMinutes"] ?? "60");

builder.Services.AddAuthentication().AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidIssuer = issuer,       // قد تكون null
        IssuerSigningKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(key!)) // انفجار وقت الطلب
    };
});`,
          points: [
            "لا تحقق عند البدء؛ الخطأ يظهر متأخرًا.",
            "التكرار في كل ملف يزيد فرص الاختلاف.",
            "القيم الرقمية تُحوَّل يدويًا وقد تفشل.",
          ],
        },
        after: {
          label: "Options مُصنّفة ومتحققة",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services.AddOptions<JwtOptions>()
    .Bind(builder.Configuration.GetSection("Jwt"))
    .ValidateDataAnnotations()
    .Validate(o => o.Key.Length >= 32,
        "Jwt:Key يجب أن يكون 32 حرفًا على الأقل.")
    .ValidateOnStart();

builder.Services.AddAuthentication().AddJwtBearer();
builder.Services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<IOptions<JwtOptions>>((bearer, jwt) =>
    {
        var o = jwt.Value;
        bearer.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = o.Issuer,
            ValidAudience = o.Audience,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(o.Key))
        };
    });

public sealed class JwtOptions
{
    [Required, MinLength(32)] public string Key { get; init; } = "";
    [Required] public string Issuer { get; init; } = "";
    [Required] public string Audience { get; init; } = "";
    [Range(5, 1440)] public int ExpiryMinutes { get; init; } = 60;
}`,
          points: [
            "خطأ واضح عند الإقلاع لا عند أول مستخدم.",
            "نوع واحد موثّق ومُختبَر.",
            "قابل للتوسّع والاختبار بسهولة.",
          ],
        },
        verdict: `<p>التحقق عند البدء (Fail Fast) مبدأ إنتاجي: الأفضل أن تفشل الحاوية في النشر بدل أن تبدأ وتُعيد 500 لكل طلب. راقب سجلات الإقلاع في CI؛ رسالة «OptionsValidationException» هي نجاح للتحقق لا فشل للنظام.</p>`,
      },
      walkthrough: [
        {
          title: "المصيدة الأولى: Captive Dependency",
          code: `builder.Services.AddSingleton<ICatalogCache, CatalogCache>();\nbuilder.Services.AddScoped<SouqDbContext>();\n\npublic sealed class CatalogCache(SouqDbContext db) : ICatalogCache\n{\n    // db هنا سيعيش مع التطبيق كله!\n}`,
          lang: "csharp",
          body: `<p>Singleton لا يجوز أن يحقن Scoped. <code>DbContext</code> هنا سيُلتقط من أول نطاق ويبقى. الأعراض: بيانات قديمة، أخطاء تزامن، تسريب ذاكرة. الحل: اجعل الخدمة Scoped، أو استخدم مصنع نطاق عند الحاجة الفعلية.</p>`
        },
        {
          title: "Service Locator",
          code: `// خطأ\npublic sealed class OrderService(IServiceProvider provider)\n{\n    public Task PayAsync(Guid id)\n    {\n        var db = provider.GetRequiredService<SouqDbContext>();\n        var mail = provider.GetRequiredService<IEmailSender>();\n        return Task.CompletedTask;\n    }\n}`,
          lang: "csharp",
          body: `<p>طلب التبعيات من <code>IServiceProvider</code> يخفي الاعتماديات ويصعّب الاختبار. اطلبها في المُنشئ. إذا كان عددها كبيرًا، فقد تحتاج تقسيم الخدمة. لا تستخدم الحاوية كـglobal state. الاستثناء: إطار عمل/مصنع يحتاج إنشاء كائنات ديناميكيًا.</p>`
        },
        {
          title: "HttpContext في Singleton",
          code: `// خطأ: احتجاز سياق الطلب\npublic sealed class CurrentUserService\n{\n    private readonly HttpContext _context;\n    public CurrentUserService(IHttpContextAccessor accessor)\n        => _context = accessor.HttpContext!;\n}`,
          lang: "csharp",
          body: `<p><code>HttpContext</code> خاص بالطلب. لا تحتفظ به في Singleton. استخدم <code>IHttpContextAccessor</code> وقت الحاجة، أو مرّر <code>userId</code> كوسيط. الاحتجاز قد يسبب تسريب بيانات مستخدم لطلب آخر. اختبر التزامن.</p>`
        },
        {
          title: "Options بدل الإعدادات المتناثرة",
          code: `public sealed class JwtOptions\n{\n    public required string Issuer { get; init; }\n    public required string Audience { get; init; }\n    public required string SigningKey { get; init; }\n}\n\nbuilder.Services.AddOptions<JwtOptions>()\n    .Bind(builder.Configuration.GetSection("Jwt"))\n    .ValidateDataAnnotations()\n    .ValidateOnStart();`,
          lang: "csharp",
          body: `<p>لا تقرأ <code>IConfiguration</code> في كل مكان. اربط section بكائن. <code>ValidateOnStart</code> يفشل مبكرًا إذا كان المفتاح ناقصًا. لا تسجّل القيمة. افصل الإعدادات الحساسة عن العامة.</p>`
        },
        {
          title: "IOptions vs IOptionsMonitor",
          code: `public sealed class EmailSender(IOptions<EmailOptions> options)\n{\n    private readonly EmailOptions _options = options.Value;\n}\n\npublic sealed class FeatureGate(IOptionsMonitor<Features> monitor)\n{\n    public bool Enabled => monitor.CurrentValue.NewCheckout;\n}`,
          lang: "csharp",
          body: `<p><code>IOptions</code> قيمة ثابتة عند البدء. <code>IOptionsMonitor</code> يقرأ التغييرات، و<code>IOptionsSnapshot</code> لكل طلب. اختر حسب الحاجة. لا تحقن <code>IOptionsSnapshot</code> في Singleton. راقب إعادة التحميل.</p>`
        },
        {
          title: "Scoped داخل BackgroundService",
          code: `using var scope = _scopeFactory.CreateScope();\nvar db = scope.ServiceProvider.GetRequiredService<SouqDbContext>();\nvar jobs = scope.ServiceProvider.GetRequiredService<IJobService>();\nawait jobs.RunAsync(stoppingToken);`,
          lang: "csharp",
          body: `<p>الخدمة الخلفية تعيش طويلًا. أنشئ نطاقًا لكل وحدة عمل. لا تحفظ <code>db</code> خارج النطاق. استخدم cancellation. لا تشغّل عملًا متوازيًا على نفس <code>DbContext</code>. هذا النمط يمنع Captive Dependency.</p>`
        },
        {
          title: "اختبار قابل للاستبدال",
          code: `var email = new FakeEmailSender();\nvar clock = new FakeClock(DateTimeOffset.Parse("2026-01-01"));\nvar service = new OrderService(db, email, clock);\n\nawait service.PlaceAsync(orderId);\nAssert.Single(email.Sent);\nAssert.Equal(expected, order.CreatedAt);`,
          lang: "csharp",
          body: `<p>Constructor Injection يجعل الاختبار بسيطًا. استبدل التبعيات الخارجية بـfake. لا تحتاج حاوية كاملة لاختبار وحدة. اختبر السلوك، لا تسلسل الاستدعاءات. هذا أحد أكبر أسباب استخدام DI.</p>`
        },
        {
          title: "قاعدة عملية",
          code: `Scoped -> Scoped       ✅\nSingleton -> Singleton ✅\nSingleton -> Scoped    ❌\nTransient -> Scoped    ✅ (إذا لم يُحتجز)\nScoped -> Singleton    ✅`,
          lang: "text",
          body: `<p>الاتجاه من الأطول عمرًا إلى الأقصر هو الخطر. Singleton لا يعتمد على Scoped. Scoped يمكنه الاعتماد على Singleton. Transient يمكنه الاعتماد على أي شيء، لكن احذر احتجازه. راجع التسجيلات عند كل إضافة.</p>`
        }
      ],
      internals: `
        <p><code>IOptions&lt;T&gt;</code> يُخزَّن Singleton ويُبنى مرة واحدة عند أول وصول. <code>IOptionsSnapshot&lt;T&gt;</code> يُسجَّل Scoped ويعيد بناء القيمة لكل نطاق، ولهذا لا يجب حقنه في Singleton. <code>IOptionsMonitor&lt;T&gt;</code> يحتفظ بذاكرة داخلية للقيم الحالية، ويستخدم <code>IOptionsChangeTokenSource</code> للاستماع لتغيّر ملفات الإعداد وإطلاق <code>OnChange</code>.</p>
        <p>ملاحظة دقيقة: إعادة تحميل appsettings لا تعني أن كل شيء يتحدّث. مزوّد ملف JSON يدعم <code>reloadOnChange</code>، لكن متغيرات البيئة ليست كذلك. وأي خدمة تحتفظ بنسخة من القيمة (بدل قراءة <code>CurrentValue</code>) لن ترى التغيير.</p>
        <p>أما <code>ValidateOnStart</code> فينفّذ التحقق أثناء بدء المضيف عبر <code>IStartupValidator</code>. إن فشل، تتوقف العملية ولا يستمع Kestrel. هذا مفيد في Kubernetes: تفشل الحاوية سريعًا وتظهر في السجلات بدل أن تبدو «جاهزة» وهي معطوبة.</p>
        <p>بخصوص <strong>Keyed Services</strong>، المفتاح يمكن أن يكون أي كائن، لكن استخدم <code>string</code> أو <code>enum</code> لتفادي مفاجآت المقارنة. الحاوية تخزّن الخدمات في خريطة مفاتيح، والحلّ المفتاحي يكلّف بحثًا إضافيًا بسيطًا. لا تستخدمه لإخفاء تصميم متردد؛ استخدمه عندما يكون الاختيار جزءًا من المجال.</p>
      `,
      tips: [
        {
          title: "لا تستدع BuildServiceProvider",
          body: "استدعاء <code>services.BuildServiceProvider()</code> داخل التكوين ينشئ حاوية ثانية، فتتضاعف Singletons وتضيع إعدادات. استخدم <code>AddOptions&lt;T&gt;().Configure&lt;TDependency&gt;()</code>.",
        },
        {
          title: "اختبر الإعداد بالاختبارات",
          body: "اكتب اختبارًا يحمّل <code>appsettings.json</code> ويتحقق من نجاح <code>ValidateOnStart</code>. هذا يمنع نشر ملف ناقص إلى الإنتاج.",
        },
        {
          title: "Scoped داخل BackgroundService",
          body: "استخدم <code>IServiceScopeFactory</code> لكل دورة عمل. لا تحقن DbContext مباشرة في الخدمة الخلفية مهما بدا الأمر بسيطًا.",
        },
        {
          title: "مفاتيح التوقيع ليست إعدادًا عاديًا",
          body: "لا تضعها في appsettings ولا في صورة Docker. استخدم Secret Manager أو متغير بيئة يُحقن وقت التشغيل، ودوّر المفاتيح دوريًا.",
        },
      ],
      quiz: [
        {
          q: "أي واجهة Options مناسبة لخدمة Singleton تريد معرفة تغيّر الإعداد فورًا؟",
          options: ["IOptions<T>", "IOptionsSnapshot<T>", "IOptionsMonitor<T>", "IConfigurationRoot فقط"],
          answer: 2,
          explain:
            "IOptionsMonitor Singleton ويوفّر CurrentValue وOnChange. IOptionsSnapshot Scoped ولا يصلح داخل Singleton.",
        },
        {
          q: "ما فائدة ValidateOnStart؟",
          options: [
            "يعيد تشغيل التطبيق عند تغيير الملف.",
            "يفشل بدء التطبيق مبكرًا إذا كان الإعداد غير صالح.",
            "يزيد سرعة الاستجابة.",
            "يشفّر مفاتيح الإعداد.",
          ],
          answer: 1,
          explain:
            "هو Fail Fast: يكشف الإعداد الناقص عند الإقلاع بدل ظهوره كخطأ 500 لاحقًا.",
        },
        {
          q: "كيف تصلح Singleton يحتاج DbContext؟",
          options: [
            "تحوّل DbContext إلى Singleton.",
            "تستخدم IServiceScopeFactory لإنشاء نطاق لكل عملية.",
            "تحذف DbContext.",
            "تستخدم static Context.",
          ],
          answer: 1,
          explain:
            "الخدمة تبقى Singleton، لكنها تفتح نطاقًا قصير العمر لكل وحدة عمل وتحل DbContext داخله.",
        },
      ],
      capstone: {
        title: "إعداد JWT آمن في Souq.NET",
        goal: "نضيف نوع إعداد JwtOptions مع تحقق كامل، ونسجّله بطريقة تفشل مبكرًا عند نقص المفتاح.",
        tasks: [
          "أنشئ <code>JwtOptions</code> بخصائص Key وIssuer وAudience وExpiryMinutes مع سمات التحقق.",
          "سجّل الإعداد مع <code>Bind</code> و<code>ValidateDataAnnotations</code> و<code>ValidateOnStart</code>.",
          "أضف مفتاحًا محليًا عبر <code>dotnet user-secrets</code> بطول 32 حرفًا على الأقل.",
          "احذف المفتاح مؤقتًا وتأكد أن التطبيق يفشل عند الإقلاع برسالة واضحة.",
          "أعد المفتاح وتأكد من نجاح التشغيل.",
        ],
        code: {
          lang: "bash",
          title: "مفتاح تطوير محلي",
          code: `dotnet user-secrets init --project src/Souq.Api
dotnet user-secrets set "Jwt:Key" "dev-only-super-long-signing-key-32+" --project src/Souq.Api
dotnet user-secrets set "Jwt:Issuer" "souq.local" --project src/Souq.Api
dotnet run --project src/Souq.Api`,
        },
      },
    },
  ],
});

Academy.addModule({
  id: "pipeline",
  title: "Middleware Pipeline",
  tagline: "كل طلب يعبر سلسلة قرارات. افهم الترتيب والاختصار، أو ستدفع الثمن في الأمان والأداء.",
  icon: "⇄",
  color: "#38bdf8",
  lessons: [
    {
      id: "middleware-mechanics",
      title: "تشريح Middleware: الطبقات والترتيب والاختصار",
      duration: 22,
      level: "متوسط",
      summary:
        "خط الأنابيب ليس قائمة أوامر متتابعة؛ هو دوال متداخلة. سنفهم RequestDelegate، ومتى تُختصر الاستجابة، ولماذا ترتيب المصادقة قبل التوجيه خطأ.",
      keywords: ["Middleware", "RequestDelegate", "Use", "Run", "Map", "short-circuit", "pipeline order"],
      objectives: [
        "تشرح كيف يتحول Use إلى دوال متداخلة.",
        "تفرّق بين Use وRun وMap وMapWhen.",
        "ترتّب المكوّنات الوسيطة ترتيبًا إنتاجيًا وتفسّره.",
        "تعرف متى تختصر الطلب ومتى تستدعي next.",
      ],
      concept: `
        <p><strong>Middleware</strong> مكوّن يعالج طلب HTTP أو يستدعي المكوّن التالي. توقيعه دالة واحدة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>public delegate Task RequestDelegate(HttpContext context);</code></pre>
        <p>عندما تكتب <code>app.Use(async (ctx, next) =&gt; { ... await next(); ... })</code>، فأنت تُنشئ طبقة تغلّف الطبقة التالية. التنفيذ يشبه استدعاء دوال متداخلة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>await A(ctx, () => B(ctx, () => C(ctx, () => D(ctx))));</code></pre>
        <p>لهذا الكود قبل <code>await next()</code> يعمل في الذهاب، والكود بعده يعمل في العودة. هذه الخاصية هي أساس التسجيل الزمني، وقياس الأداء، والتعديل على الاستجابة.</p>
        <h3>Use وRun وMap</h3>
        <ul>
          <li><code>Use</code>: يضيف طبقة تستدعي التالية (أو لا تستدعيها).</li>
          <li><code>Run</code>: طبقة نهائية لا تستدعي شيئًا؛ تنهِ السلسلة. تُستخدم لاختصار الطلب أو لإرجاع 404 مخصص.</li>
          <li><code>Map</code>: يفرّع حسب بادئة المسار. <code>Map(\"/api\", api =&gt; ...)</code> يعطي خط أنابيب فرعيًا.</li>
          <li><code>MapWhen</code>: يفرّع حسب شرط على <code>HttpContext</code>.</li>
        </ul>
        <h3>الترتيب ليس تجميليًا</h3>
        <p>الترتيب الإنتاجي الشائع:</p>
        <ol>
          <li><strong>Exception Handler</strong> أولًا ليلتقط أخطاء كل ما بعده.</li>
          <li><strong>HSTS / HTTPS Redirection</strong>.</li>
          <li><strong>Static Files</strong> قبل التوجيه (لا داعي لمرور الأصول عبر Routing).</li>
          <li><strong>Routing</strong> (يُضاف تلقائيًا في Minimal Hosting عند الحاجة).</li>
          <li><strong>CORS</strong> قبل المصادقة لمعالجة preflight.</li>
          <li><strong>Rate Limiter</strong> قبل العمل الثقيل.</li>
          <li><strong>Authentication</strong> ثم <strong>Authorization</strong>.</li>
          <li><strong>Endpoint</strong> التنفيذ النهائي.</li>
        </ol>
        <p>لو قدّمت <code>UseAuthorization</code> على <code>UseAuthentication</code>، فستُقيَّم السياسات على مستخدم غير مُعرَّف. ولو وضعت <code>UseCors</code> بعد المصادقة، فقد يُرفض طلب <code>OPTIONS</code> قبل أن يصل. الإطار لا يصحّح لك الترتيب.</p>
        <h3>الاختصار (Short-circuit)</h3>
        <p>عندما لا تستدعي <code>next</code>، يتوقف الطلب عندك. هذا صحيح لـ: رفض غير مصرّح، إرجاع من الذاكرة المؤقتة، أو التحقق من مفتاح API. لكنه خطر إذا نسيت كتابة استجابة: العميل سيبقى ينتظر أو يحصل على 200 فارغ. القاعدة: كل اختصار يجب أن يكتب Status Code وجسمًا واضحًا.</p>
      `,
      walkthrough: [
        {
          title: "شكل الـ Middleware",
          code: `app.Use(async (context, next) =>
{
    // قبل
    await next(context);
    // بعد
});`,
          lang: "csharp",
          body: `<p><code>Use</code> يضيف دالة إلى الأنبوب. <code>next</code> هو <code>RequestDelegate</code> يمثل بقية السلسلة. الكود قبل <code>await next</code> يعمل في اتجاه الطلب، والكود بعده يعمل في اتجاه الاستجابة. هذا هو الفرق الجوهري بين «قائمة أوامر» و«دوال متداخلة»: كل middleware يغلّف ما بعده.</p>`
        },
        {
          title: "استدعِ next مرة واحدة فقط",
          code: `await next(context);`,
          lang: "csharp",
          body: `<p>استدعاء <code>next</code> مرتين يعني تنفيذ بقية الأنبوب مرتين، وقد تكتب الاستجابة مرتين أو تفتح استعلامين. لا تفعل ذلك إلا لسبب مقصود ونادر. بعد استدعاء <code>next</code> تحقّق من <code>context.Response.HasStarted</code> قبل تعديل الترويسات؛ إذا بدأ إرسال الجسم فلا يمكنك تغيير الحالة أو الترويسات.</p>`
        },
        {
          title: "أضف Correlation ID قبل downstream",
          code: `context.Response.Headers["X-Correlation-Id"] =
    context.TraceIdentifier;`,
          lang: "csharp",
          body: `<p><code>TraceIdentifier</code> معرف فريد للطلب داخل ASP.NET Core. إضافته إلى الاستجابة تساعد الدعم والعميل على ربط المشكلة بسجل الخادم. يجب أن تُضاف <strong>قبل</strong> أن يبدأ الـ response؛ بعد <code>HasStarted</code> لا يمكن. في الإنتاج، انقل نفس المعرف إلى logs وtraces وردود الأخطاء، ولا تعتمد على عنوان IP وحده.</p>`
        },
        {
          title: "حوّل الاستثناء إلى استجابة",
          code: `try
{
    await next(context);
}
catch (Exception ex)
{
    logger.LogError(ex, "Unhandled request failure");
    throw;
}`,
          lang: "csharp",
          body: `<p>التقاط الاستثناء هنا يسمح بالتسجيل، لكن <code>throw;</code> يعيد رفعه ليصل إلى <code>UseExceptionHandler</code> أو <code>IExceptionHandler</code> الذي ينتج Problem Details. لا تكتب استجابة 500 يدويًا في كل middleware. ولا تبتلع الاستثناء بـ<code>catch { }</code>؛ سيرى العميل نجاحًا كاذبًا وتفقد أثر الخطأ.</p>`
        },
        {
          title: "اختصار الطلب عند رفضه",
          code: `if (!context.User.Identity?.IsAuthenticated ?? true)
{
    context.Response.StatusCode = StatusCodes.Status401Unauthorized;
    return;
}

await next(context);`,
          lang: "csharp",
          body: `<p>عدم استدعاء <code>next</code> يوقف السلسلة. هذا صحيح للرفض أو الرد من cache. لكن يجب أن تكتب حالة واضحة، وإلا قد يحصل العميل على 200 فارغ. لا تضع فحصًا أمنيًا في middleware عشوائي بدل <code>UseAuthorization</code>؛ استخدم الأدوات القياسية أولًا، واكتب middleware مخصصًا فقط لحالة لا تغطيها.</p>`
        },
        {
          title: "رتّب معالجة الأخطاء أولًا",
          code: `app.UseExceptionHandler();
app.UseHsts();
app.UseHttpsRedirection();
app.UseCors("web");
app.UseAuthentication();
app.UseAuthorization();`,
          lang: "csharp",
          body: `<p>الترتيب يحدد من يرى ماذا. معالج الاستثناء يجب أن يكون قريبًا من بداية الأنبوب ليغلّف كل ما بعده. <code>UseCors</code> قبل المصادقة كي تُضاف ترويسات CORS حتى للطلبات المرفوضة. <code>UseAuthentication</code> يبني <code>User</code>، ثم <code>UseAuthorization</code> يقرر. عكس المصادقة والتفويض يجعل السياسات ترى هوية فارغة.</p>`
        },
        {
          title: "تفرّع بمسار منفصل",
          code: `app.Map("/ops", ops =>
{
    ops.Run(async context =>
        await context.Response.WriteAsync("ops"));
});`,
          lang: "csharp",
          body: `<p><code>Map</code> يفرع الأنبوب حسب بادئة المسار. الطلبات التي لا تطابق <code>/ops</code> تكمل في الأنبوب الرئيسي. <code>Run</code> هنا ينهي الفرع لأنه لا يستدعي next. استخدم <code>MapWhen</code> لشرط غير المسار، مثل ترويسة أو بيئة. لا تفرّع بلا سبب؛ كل فرع إضافي يعقّد الترتيب والاختبار.</p>`
        },
        {
          title: "Middleware كصنف قابل للحقن",
          code: `public sealed class RequestTimingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestTimingMiddleware(RequestDelegate next)
        => _next = next;

    public async Task InvokeAsync(
        HttpContext context,
        ILogger<RequestTimingMiddleware> logger)
    {
        var started = Stopwatch.GetTimestamp();
        await _next(context);
        logger.LogInformation("Request took {Ms} ms",
            Stopwatch.GetElapsedTime(started).TotalMilliseconds);
    }
}`,
          lang: "csharp",
          body: `<p>الصنف يُنشأ مرة واحدة تقريبًا (singleton)، لذلك لا تحقن <code>DbContext</code> أو خدمة scoped في constructor. حقن التبعيات يكون في معاملات <code>InvokeAsync</code>، فتُحل لكل طلب. <code>RequestDelegate next</code> يُمرر تلقائيًا. سجّل القياس بعد <code>await _next</code> ليشمل بقية الأنبوب، وتذكّر أن الاستجابة قد تكون بدأت.</p>`
        },
        {
          title: "سجّل الـ middleware في المكان الصحيح",
          code: `app.UseMiddleware<RequestTimingMiddleware>();`,
          lang: "csharp",
          body: `<p><code>UseMiddleware</code> يضيف الصنف إلى الأنبوب عند موضعه. إن سجّلته بعد <code>UseAuthorization</code> فلن يقيس قرارات التفويض. إن أردت أن يعمل قبل كل شيء، ضعه بعد معالج الاستثناء وقبل الباقي. اختبر الترتيب بطلبين: واحد ناجح وآخر مرفوض، وتأكد من وجود الترويسة والقياس في الحالتين.</p>`
        }
      ],
      compare: {
        intro: `<p>بدون Middleware، تتكرر نفس الفحوصات في كل نقطة نهاية. ومع Middleware، تصبح سياسة واحدة تحمي كل المسارات — بشرط الترتيب الصحيح.</p>`,
        before: {
          label: "فحص مكرر داخل كل endpoint",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapGet("/api/products", (HttpContext ctx) =>
{
    if (!ctx.Request.Headers.TryGetValue("X-Api-Key", out var key) ||
        key != "secret")
        return Results.Unauthorized();

    return Results.Ok(products);
});

app.MapPost("/api/products", (HttpContext ctx, ProductDto dto) =>
{
    if (!ctx.Request.Headers.TryGetValue("X-Api-Key", out var key) ||
        key != "secret")
        return Results.Unauthorized();

    // ... نفس الفحص مرة أخرى
    return Results.Created();
});`,
          points: [
            "نسيان الفحص في نقطة واحدة = ثغرة.",
            "منطق مشترك مبعثر في كل مكان.",
            "صعب تغيير السياسة لاحقًا.",
          ],
        },
        after: {
          label: "Middleware واحد",
          lang: "csharp",
          title: "Program.cs",
          code: `app.Use(async (context, next) =>
{
    if (context.Request.Path.StartsWithSegments("/api") &&
        !context.Request.Headers.ContainsKey("X-Api-Key"))
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new
        {
            error = "missing_api_key"
        });
        return; // اختصار مقصود
    }

    await next(context);
});

app.MapGet("/api/products", () => Results.Ok(products));
app.MapPost("/api/products", (ProductDto dto) => Results.Created());`,
          points: [
            "سياسة واحدة لكل المسارات.",
            "الاختصار واضح ومكتوب.",
            "تغيير القاعدة يحدث في مكان واحد.",
          ],
        },
        verdict: `<p>الـ Middleware يحرّك السياسات من «كل نقطة نهاية» إلى «حدود التطبيق». لكنه ليس سلة مهملات: المنطق الخاص بمجال واحد يبقى في الخدمة أو الـ endpoint، والـ Middleware للهموم العرضية (Cross-cutting): الهوية، السجلات، الوقت، الحدود.</p>`,
      },
      internals: `
        <p><code>ApplicationBuilder</code> يحتفظ بقائمة من <code>Func&lt;RequestDelegate, RequestDelegate&gt;</code>. عند البناء، يبدأ من <code>RequestDelegate</code> نهائي (عادة 404) ويطبّق الدوال بالعكس، فينتج دالة واحدة. هذا يعني أن تكلفة تركيب السلسلة تحدث مرة واحدة عند الإقلاع، وليست لكل طلب.</p>
        <p>كل <code>Use</code> يضيف <strong>closure</strong> يحمل المتغيرات الملتقطة. Closure صغير لا مشكلة، لكن middleware يلتقط كائنات كبيرة أو يخصّص مصفوفات لكل طلب قد يزيد ضغط GC. الأفضل أن يكون الالتقاط لإعدادات ثابتة فقط.</p>
        <p><strong>Endpoint Routing</strong> يعمل على مرحلتين: <code>UseRouting</code> يطابق المسار ويضع <code>Endpoint</code> في ميزات الـ Context، ثم <code>UseEndpoints</code> ينفّذ الـ Endpoint المختار. في Minimal Hosting يُضاف التوجيه تلقائيًا عند أول <code>Map</code>، لكن ترتيب <code>UseAuthentication</code> يبقى مهمًا: يجب أن يأتي بعد Routing حتى تعرف سياسة الـ endpoint، وقبل Authorization.</p>
        <p>عند كتابة الاستجابة، تذكّر أن الهيدرات لا تُرسل حتى أول كتابة للجسم أو نهاية الطلب. إذا عدّلت هيدرًا بعد <code>Response.HasStarted</code> فسيرمي استثناءً. هذا سبب فشل middleware يحاول إضافة هيدر بعد أن كتب endpoint الاستجابة.</p>
      `,
      internalsTable: {
        head: ["Middleware", "ماذا يحدث لو تأخّر؟"],
        rows: [
          ["Exception Handler", "أخطاء ما قبله لن تُلتقط كـ ProblemDetails"],
          ["HTTPS Redirection", "طلبات HTTP تصل للتطبيق بلا تشفير"],
          ["CORS", "طلبات preflight تُرفض قبل الوصول"],
          ["Authentication", "Authorization يرى مستخدمًا مجهولًا"],
          ["Rate Limiter", "العمل الثقيل يُنفَّذ قبل الرفض"],
        ],
      },
      tips: [
        {
          title: "ارسم السلسلة قبل الكتابة",
          body: "اكتب أسماء الطبقات بالترتيب على ورقة. معظم أخطاء 401/404/CORS سببها ترتيب طبقة، لا منطق خاطئ.",
        },
        {
          title: "لا تكتب استجابة ثم تستدعي next",
          body: "بعد <code>WriteAsJsonAsync</code> لا تستدعِ <code>next</code>؛ ستحاول الطبقة التالية الكتابة فوق استجابة بدأت. استخدم <code>return</code>.",
        },
        {
          title: "استخدم UseWhen للفروع",
          body: "<code>UseWhen</code> يفرّع دون استنساخ كامل للإعداد، ويُعيد الدمج. مناسب لسياسات تخص مسارًا مثل <code>/api</code>.",
        },
        {
          title: "اختبر الترتيب باختبار تكامل",
          body: "اختبار يطلب مسارًا محميًا ويتوقع 401 يكشف ترتيب Authentication/Authorization. لا تعتمد على المراجعة البصرية.",
        },
      ],
      quiz: [
        {
          q: "ماذا يحدث إذا لم يستدعِ Middleware الدالة next؟",
          options: [
            "يكمل الإطار تلقائيًا إلى النهاية.",
            "يتوقف الطلب عند هذه الطبقة (Short-circuit) ويجب كتابة استجابة.",
            "يُعاد الطلب من البداية.",
            "يُغلَق التطبيق.",
          ],
          answer: 1,
          explain:
            "عدم استدعاء next ينهي السلسلة. إن لم تكتب Status/Response، قد يحصل العميل على استجابة فارغة أو غير متوقعة.",
        },
        {
          q: "أين يجب أن يأتي UseAuthentication؟",
          options: [
            "قبل UseRouting.",
            "بعد UseRouting وقبل UseAuthorization.",
            "بعد MapGet.",
            "لا يهم.",
          ],
          answer: 1,
          explain:
            "Routing يحدد الـ endpoint وسياسته، ثم Authentication يبني الهوية، ثم Authorization يقيّمها قبل التنفيذ.",
        },
        {
          q: "ما الفرق بين Use وRun؟",
          options: [
            "لا فرق.",
            "Use تضيف طبقة تستدعي next، وRun طبقة نهائية لا تستدعي شيئًا.",
            "Run أسرع دائمًا.",
            "Use للـ HTTPS فقط.",
          ],
          answer: 1,
          explain:
            "Run تُنهي السلسلة (terminal middleware). Use تسمح بالمرور إلى الطبقة التالية.",
        },
      ],
      capstone: {
        title: "ترتيب خط أنابيب Souq.NET",
        goal: "نبني خط الأنابيب الإنتاجي كاملًا بالترتيب الصحيح، مع مسار API محمي بسيط يثبت أن الطبقات تعمل معًا.",
        tasks: [
          "أضف <code>UseExceptionHandler</code> و<code>UseStatusCodePages</code> في البداية.",
          "أضف <code>UseHttpsRedirection</code> ثم <code>UseCors</code>.",
          "أضف <code>UseAuthentication</code> ثم <code>UseAuthorization</code>.",
          "أضف <code>MapGroup(\"/api\")</code> وضع فيه نقطة عامة وأخرى تتطلب سياسة مؤقتة.",
          "اكتب اختبارًا يدويًا: اطلب المسار المحمي بلا Token وتأكد أن الاستجابة 401 وليست 404.",
        ],
        code: {
          lang: "csharp",
          title: "ترتيب Pipeline",
          code: `var app = builder.Build();

app.UseExceptionHandler();
app.UseStatusCodePages();

if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseCors("web");

app.UseAuthentication();
app.UseAuthorization();

var api = app.MapGroup("/api");
api.MapGet("/public", () => Results.Ok("public"));
api.MapGet("/private", () => Results.Ok("private"))
   .RequireAuthorization();

app.Run();`,
        },
      },
    },
    {
      id: "custom-middleware",
      title: "كتابة Middleware مخصص: من Lambda إلى Class",
      duration: 22,
      level: "متقدم",
      summary:
        "متى تكفي Lambda ومتى تحتاج class؟ سنكتب Middleware قابلًا للاختبار، ونفهم حقن التبعيات فيه، ومعالجة الأخطاء دون كسر السلسلة.",
      keywords: ["IMiddleware", "UseMiddleware", "InvokeAsync", "correlation id", "timing", "DI in middleware"],
      objectives: [
        "تفرّق بين Middleware inline وclass-based.",
        "تعرف لماذا Middleware singleton ولا يجوز حقن Scoped في مُنشئه.",
        "تكتب Middleware يضيف هيدرًا ويقيس الزمن بأمان.",
        "تختبر Middleware بمعزل عن التطبيق.",
      ],
      concept: `
        <p>الـ Lambda مناسب لسطرين أو ثلاثة. لكن عندما يكبر المنطق أو تحتاج حقن تبعيات أو اختبارًا مستقلًا، استخدم كلاس:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>public sealed class CorrelationMiddleware
{
    private readonly RequestDelegate _next;
    public CorrelationMiddleware(RequestDelegate next) =&gt; _next = next;

    public async Task InvokeAsync(HttpContext context)
    {
        var id = context.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                 ?? Guid.NewGuid().ToString("N");
        context.Items["correlation-id"] = id;
        context.Response.Headers["X-Correlation-Id"] = id;
        await _next(context);
    }
}</code></pre>
        <p>ثم <code>app.UseMiddleware&lt;CorrelationMiddleware&gt;()</code>. الإطار ينشئ المكوّن <strong>مرة واحدة</strong> عند الإقلاع (Singleton)، ويستدعي <code>InvokeAsync</code> لكل طلب. ولهذا لا تحقن خدمة Scoped في المُنشئ؛ ستُحتجز. الحل: أضفها كمعامل في <code>InvokeAsync</code>، فيحقنها الإطار من نطاق الطلب:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>public async Task InvokeAsync(HttpContext context, ILogger&lt;CorrelationMiddleware&gt; logger)</code></pre>
        <h3>البديل: IMiddleware</h3>
        <p>إذا أردت أن يُنشأ المكوّن من الحاوية (Factory-based) ويمكن تسجيله Scoped/Transient، نفّذ <code>IMiddleware</code>:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>public sealed class AuditMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
        =&gt; await next(context);
}
builder.Services.AddScoped&lt;AuditMiddleware&gt;();
app.UseMiddleware&lt;AuditMiddleware&gt;();</code></pre>
        <h3>التعديل على الاستجابة</h3>
        <p>الهيدرات تُرسل مع أول بايت من الجسم. إذا أردت إضافة هيدر بعد تنفيذ الـ endpoint، استخدم <code>context.Response.OnStarting</code> أو أضفه <strong>قبل</strong> <code>await next()</code>. لا تحاول التعديل بعد <code>HasStarted</code>.</p>
        <p>وقاعدة ذهبية: <strong>لا تبتلع الاستثناءات</strong>. إن أردت التسجيل، سجّل ثم أعد الرمي (<code>throw;</code>) ليتولّى <code>IExceptionHandler</code> تحويلها إلى ProblemDetails. ابتلاعها هنا يعني أن العميل سيرى 200 كاذبًا.</p>
      `,
      walkthrough: [
        {
          title: "متى تكفي Lambda؟",
          code: `app.Use(async (context, next) =>
{
    context.Response.Headers["X-Api-Version"] = "1";
    await next(context);
});`,
          lang: "csharp",
          body: `<p>الـ lambda مناسبة لسلوك صغير لا يحتاج تبعيات أو اختبارًا مستقلًا. هنا تضيف ترويسة ثم تكمل. لكنها تصبح صعبة عندما تحتاج <code>ILogger</code> أو <code>IOptions</code> أو <code>DbContext</code>، أو عندما تريد اختبارها بمعزل عن التطبيق. عندها انتقل إلى class بدل تكديس الكود داخل <code>Program.cs</code>.</p>`
        },
        {
          title: "الصنف التقليدي",
          code: `public sealed class RequestTimingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestTimingMiddleware(RequestDelegate next)
        => _next = next;

    public async Task InvokeAsync(HttpContext context)
    {
        var started = Stopwatch.GetTimestamp();
        await _next(context);
        var ms = Stopwatch.GetElapsedTime(started).TotalMilliseconds;
        context.Response.Headers["X-Elapsed-Ms"] = ms.ToString("F0");
    }
}`,
          lang: "csharp",
          body: `<p>الـ constructor يستقبل <code>RequestDelegate</code>؛ هذا هو الـ next. الصنف يُنشأ مرة واحدة تقريبًا، لذلك لا تضع فيه حالة خاصة بطلب. <code>InvokeAsync</code> يُنفّذ لكل طلب. إضافة الترويسة بعد <code>_next</code> تعمل فقط إذا لم تبدأ الاستجابة؛ إن كانت قد بدأت فسيفشل التعديل. راجع <code>HasStarted</code> في الإنتاج.</p>`
        },
        {
          title: "حقن التبعيات في InvokeAsync",
          code: `public async Task InvokeAsync(
    HttpContext context,
    ILogger<RequestTimingMiddleware> logger,
    IOptions<RequestTimingOptions> options)
{
    var started = Stopwatch.GetTimestamp();
    await _next(context);
    logger.LogInformation("elapsed={Ms}ms threshold={Threshold}",
        Stopwatch.GetElapsedTime(started).TotalMilliseconds,
        options.Value.SlowThresholdMs);
}`,
          lang: "csharp",
          body: `<p>معاملات <code>InvokeAsync</code> تُحقن من حاوية DI لكل طلب. هذا هو المكان الصحيح للخدمات scoped. <code>ILogger</code> و<code>IOptions</code> آمنان أيضًا، لكن لا تحقن <code>DbContext</code> في constructor الـ middleware. تذكّر أن <code>IOptions</code> يُقرأ عند الاستخدام؛ لا تعتمد على تعديل الإعداد أثناء الطلب.</p>`
        },
        {
          title: "IMiddleware للتبعيات scoped",
          code: `public sealed class ApiKeyMiddleware : IMiddleware
{
    private readonly IApiKeyValidator _validator;

    public ApiKeyMiddleware(IApiKeyValidator validator)
        => _validator = validator;

    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        if (!context.Request.Headers.TryGetValue("X-Api-Key", out var key)
            || !await _validator.IsValidAsync(key!, context.RequestAborted))
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            return;
        }

        await next(context);
    }
}`,
          lang: "csharp",
          body: `<p><code>IMiddleware</code> يُنشأ عبر <code>IMiddlewareFactory</code> لكل طلب، لذلك يمكنه حقن خدمات scoped في constructor. سجّله بـ<code>AddScoped&lt;ApiKeyMiddleware&gt;()</code> ثم <code>UseMiddleware&lt;ApiKeyMiddleware&gt;()</code>. لا تخلط بين النمطين: الصنف التقليدي singleton تقريبًا، و<code>IMiddleware</code> per-request. اختر حسب احتياج التبعيات.</p>`
        },
        {
          title: "أعد رمي الاستثناء",
          code: `try
{
    await _next(context);
}
catch (Exception ex) when (ex is not OperationCanceledException)
{
    logger.LogError(ex, "Middleware failure");
    throw;
}`,
          lang: "csharp",
          body: `<p>سجّل ثم <code>throw;</code> ليتولى معالج الأخطاء المركزي الاستجابة. لا تبتلع الاستثناء ولا ترسل 200. استثناء <code>OperationCanceledException</code> عند إلغاء العميل ليس خطأ خادمًا؛ لا تحوّله إلى 500. الفلتر <code>when</code> يوضح النية ويمنع تسجيل الإلغاء كخطأ.</p>`
        },
        {
          title: "افحص HasStarted قبل الكتابة",
          code: `if (!context.Response.HasStarted)
{
    context.Response.Headers["X-Correlation-Id"] = context.TraceIdentifier;
}
else
{
    logger.LogWarning("Response already started; header skipped");
}`,
          lang: "csharp",
          body: `<p>بعد بدء إرسال الجسم لا يمكن تغيير الحالة أو الترويسات. المحاولة قد ترمي <code>InvalidOperationException</code>. افحص <code>HasStarted</code> قبل أي تعديل متأخر. الأفضل أن تضيف الترويسات قبل <code>_next</code>، لكن بعض القياسات لا تُعرف إلا بعده؛ لهذا تحتاج الحماية.</p>`
        },
        {
          title: "مرّر السياق بين الطبقات",
          code: `context.Items["CorrelationId"] = context.TraceIdentifier;`,
          lang: "csharp",
          body: `<p><code>HttpContext.Items</code> قاموس لكل طلب، مناسب لتمرير قيمة صغيرة بين middleware وendpoint دون تغيير التوقيعات. لا تستخدمه لتخزين حالة أعمال طويلة أو كائنات كبيرة. في الإنتاج، اربط نفس المعرف بـ logs وtraces وProblem Details حتى تستطيع تتبع الطلب من البداية للنهاية.</p>`
        },
        {
          title: "مهلة مرتبطة بإلغاء العميل",
          code: `using var cts = CancellationTokenSource
    .CreateLinkedTokenSource(context.RequestAborted);
cts.CancelAfter(TimeSpan.FromSeconds(5));
await _next(context);`,
          lang: "csharp",
          body: `<p><code>RequestAborted</code> يُلغى عند انقطاع العميل. الربط بمهلة إضافية يمنع عملية بطيئة من البقاء للأبد. مرّر <code>cts.Token</code> إلى الخدمات التي تدعمه. لا تكتب استجابة 504 بعد أن تكون الاستجابة بدأت؛ افحص <code>HasStarted</code>. الإلغاء ليس خطأً دائمًا، لكنه يحتاج تسجيلًا منضبطًا.</p>`
        },
        {
          title: "اختبره بمعزل عن الشبكة",
          code: `var context = new DefaultHttpContext();
context.Response.Body = new MemoryStream();
var middleware = new RequestTimingMiddleware(
    _ => Task.CompletedTask);

await middleware.InvokeAsync(context);`,
          lang: "csharp",
          body: `<p><code>DefaultHttpContext</code> يتيح اختبار الـ middleware دون تشغيل Kestrel. استخدم <code>RequestDelegate</code> بسيطًا يحاكي ما بعده، وتحقق من الحالة والترويسات والجسم. غطِّ الحالات: طلب ناجح، استثناء، إلغاء، واستجابة بدأت. الاختبار السريع هنا أرخص من integration test كامل لكل تغيير.</p>`
        }
      ],
      compare: {
        intro: `<p>نفس الوظيفة مرتين: Lambda قصيرة لا تُختبر، وكلاس مستقل يمكن اختباره وحقن السجلات فيه.</p>`,
        before: {
          label: "Lambda داخل Program.cs",
          lang: "csharp",
          title: "Program.cs",
          code: `app.Use(async (context, next) =>
{
    var sw = Stopwatch.StartNew();
    try
    {
        await next(context);
    }
    finally
    {
        sw.Stop();
        var logger = context.RequestServices
            .GetRequiredService<ILogger<Program>>();
        logger.LogInformation("Path {Path} took {Ms} ms",
            context.Request.Path, sw.ElapsedMilliseconds);
    }
});`,
          points: [
            "منطق مدفون داخل ملف الإقلاع.",
            "استخدام Service Locator داخل الطلب.",
            "لا يمكن اختباره مباشرة بسهولة.",
          ],
        },
        after: {
          label: "Class Middleware",
          lang: "csharp",
          title: "Middleware/RequestTimingMiddleware.cs",
          code: `public sealed class RequestTimingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestTimingMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(
        HttpContext context,
        ILogger<RequestTimingMiddleware> logger)
    {
        var sw = Stopwatch.StartNew();
        try
        {
            await _next(context);
        }
        finally
        {
            sw.Stop();
            context.Response.Headers["X-Elapsed-Ms"] =
                sw.ElapsedMilliseconds.ToString();

            logger.LogInformation(
                "HTTP {Method} {Path} responded {Status} in {Elapsed} ms",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                sw.ElapsedMilliseconds);
        }
    }
}

// Program.cs
app.UseMiddleware<RequestTimingMiddleware>();`,
          points: [
            "تبعية Scoped تُحقن في InvokeAsync لا في المُنشئ.",
            "اختبار مستقل عبر DefaultHttpContext.",
            "إعادة استخدام في كل المشاريع.",
          ],
        },
        verdict: `<p>الكلاس ليس «أفضل» دائمًا؛ Lambda أوضح لسطرين. لكن عندما يصبح الهمّ متكررًا أو يحتاج تبعيات أو اختبارًا، الكلاس هو الاستثمار الصحيح. القاعدة: كلما زاد احتمال إعادة الاستخدام، زادت قيمة الفصل.</p>`,
      },
      internals: `
        <p><code>UseMiddleware&lt;T&gt;</code> يفحص نوع T بالـ Reflection مرة واحدة عند البناء، ويبني دالة تُنشئ نسخة واحدة. يبحث عن مُنشئ يقبل <code>RequestDelegate</code> وأي خدمات Singleton مسجّلة، ثم يبحث عن <code>InvokeAsync</code> أو <code>Invoke</code>.</p>
        <p>المعاملات الإضافية في <code>InvokeAsync</code> تُحلّ من <strong>نطاق الطلب</strong> في كل استدعاء. هذا تصميم ذكي: يمنع Captive Dependencies دون منع استخدام الخدمات Scoped.</p>
        <p>تكلفة الاستدعاء نفسها منخفضة، لكن الانتباه للأداء يظل مطلوبًا: لا تُسجّل كل طلب بمستوى Information في تطبيق عالي الحركة دون عيّنة أو مستوى مناسب. السجلات أيضًا تخصّص ذاكرة وتكتب I/O؛ استخدم <code>LoggerMessage</code> المولّد لتقليل التخصيص.</p>
        <p>أما <code>IMiddleware</code> فيُسجَّل في الحاوية ويُنشأ لكل طلب وفق عمره، ويُنفّذ عبر <code>MiddlewareFactory</code>. مناسب إذا كان لديك حالة لكل طلب أو تريد حقن Scoped في المُنشئ بوعي.</p>
      `,
      tips: [
        {
          title: "استخدم InvokeAsync للتبعيات Scoped",
          body: "لا تحقن <code>DbContext</code> أو <code>IProductService</code> في مُنشئ Middleware التقليدي. أضفها كمعاملات InvokeAsync.",
        },
        {
          title: "لا تكتب استجابة داخل finally",
          body: "إذا بدأ الـ endpoint الاستجابة، لا تحاول كتابة جسم في finally. الهيدرات فقط، وقبل HasStarted عند الحاجة.",
        },
        {
          title: "أعد رمي الاستثناء",
          body: "Middleware التسجيل يجب أن يستخدم <code>try/finally</code> أو <code>catch { log; throw; }</code>. لا تحوّل الخطأ إلى 200.",
        },
        {
          title: "احترس من Middleware يقرأ الجسم",
          body: "قراءة <code>Request.Body</code> تستهلكه. إن احتجت قراءته، فعّل <code>EnableBuffering</code> وأعد الموضع إلى الصفر، أو استخدم <code>HttpRequest.ReadFormAsync</code> بحذر.",
        },
      ],
      quiz: [
        {
          q: "لماذا لا يجوز حقن خدمة Scoped في مُنشئ Middleware تقليدي؟",
          options: [
            "لأن Middleware لا يدعم DI.",
            "لأن نسخة Middleware تُنشأ مرة واحدة، فتُحتجز الخدمة Scoped لعمر التطبيق.",
            "لأن Scoped أبطأ.",
            "لأنه يمنع التشغيل.",
          ],
          answer: 1,
          explain:
            "المكوّن Singleton بطبيعته. حقن Scoped في المُنشئ يجعله Captive. استخدم معاملات InvokeAsync.",
        },
        {
          q: "ما الطريقة الصحيحة لإضافة هيدر بعد تنفيذ endpoint؟",
          options: [
            "اكتبه بعد await next مباشرة دائمًا.",
            "استخدم Response.OnStarting أو أضفه قبل await next.",
            "عدّل Response.Headers بعد HasStarted.",
            "أعد تشغيل الطلب.",
          ],
          answer: 1,
          explain:
            "بعد بدء الاستجابة لا يمكن تعديل الهيدرات. OnStarting يسمح بذلك قبل الإرسال الفعلي.",
        },
        {
          q: "ماذا يجب أن يفعل Middleware عند التقاط استثناء؟",
          options: [
            "يعيد 200 لتجنب الإزعاج.",
            "يسجّل ثم يعيد رمي الاستثناء ليعالجه المعالج العام.",
            "يغلّف التطبيق.",
            "يحذف الاستثناء.",
          ],
          answer: 1,
          explain:
            "الابتلاع يخفي الخطأ ويكسر ProblemDetails. سجّل ثم أعد الرمي ليتولى المعالج المركزي الاستجابة.",
        },
      ],
      capstone: {
        title: "Correlation وTiming في Souq.NET",
        goal: "نضيف هوية للطلب وتوقيتًا قابلًا للقياس، ونتأكد أن القيم تظهر في الهيدر والسجل دون كسر السلسلة.",
        tasks: [
          "أنشئ <code>CorrelationIdMiddleware</code> يقرأ <code>X-Correlation-Id</code> أو يولّد GUID.",
          "خزّن المعرف في <code>HttpContext.Items</code> وأضفه إلى هيدر الاستجابة.",
          "أنشئ <code>RequestTimingMiddleware</code> يسجّل المدة والحالة.",
          "سجّل الميدلويرين قبل <code>UseAuthentication</code>.",
          "أرسل طلبين وتحقق من اختلاف Correlation ID وثبات صحة القياس.",
        ],
        code: {
          lang: "csharp",
          title: "ربط المعرف بالسجل",
          code: `using var scope = logger.BeginScope(new Dictionary<string, object>
{
    ["correlation_id"] = context.Items["correlation-id"]!
});

logger.LogInformation(
    "HTTP {Method} {Path} -> {Status} in {Elapsed}ms",
    context.Request.Method,
    context.Request.Path,
    context.Response.StatusCode,
    sw.ElapsedMilliseconds);`,
        },
      },
    },
  ],
});
