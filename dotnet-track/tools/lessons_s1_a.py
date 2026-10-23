"""Stage 1, Module 1 — full authored lesson content (lessons 1-4).

Written in Python (not raw JSON) so C# code blocks stay readable: triple-quoted
raw strings, no quote escaping. tools/build_lessons.py dumps these to
content/lessons/<id>.json.
"""

TODAY = "2026-10-22"

LESSONS_S1_A = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s1-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
**SOLID** مش خمسة ملصقات تحفظها — دي خمس طرق تسأل بيها سؤال واحد: *مين مسؤول عن إيه، ومين بيعرف عن مين؟*
في مشروع ASP.NET Core حقيقي، المبادئ دي بتظهر في قرارات يومية: هل الـService دي بتعمل حاجتين؟ هل إضافة
وسيلة دفع جديدة هتعدّل كود موجود؟ هل أقدر أختبر الـLogic من غير قاعدة بيانات؟

إحنا هنا مش هنشرح التعريفات — هنشوف كود **قبل وبعد**، ونربط كل مبدأ بعلامة تحذير تشوفها في Code Review.
"""},
            {"type": "terms", "title": "مصطلحات الدرس", "items": [
                {"term": "SRP — Single Responsibility", "def": "الكلاس له سبب واحد للتغيير. مش معناه «دالة واحدة»، معناه **مسؤولية واحدة قدام جهة واحدة**."},
                {"term": "OCP — Open/Closed", "def": "مفتوح للامتداد، مقفول للتعديل: إضافة سلوك جديد بدون تعديل الكود الموجود (بالـpolymorphism مش بالـif)."},
                {"term": "LSP — Liskov Substitution", "def": "أي نوع مشتق لازم يقدر يحل محل الأساسي من غير ما يكسر توقعات المستخدم."},
                {"term": "ISP — Interface Segregation", "def": "لا تجبر عميلًا على الاعتماد على أعضاء هو مش محتاجها — واجهات صغيرة أفضل من واجهة ضخمة."},
                {"term": "DIP — Dependency Inversion", "def": "التبعيات تكون على **تجريدات** (interfaces) مش على تفاصيل التنفيذ. السياسة العليا ما تعتمدش على التفاصيل الواطية."},
                {"term": "Cohesion / Coupling", "def": "التماسك: قد إيه أجزاء الكلاس بتخدم هدف واحد. الاقتران: قد إيه تغيير هنا يجبر تغيير هناك."},
            ]},
            {"type": "heading", "level": 2, "text": "قبل: كلاس له خمسة أسباب للتغيير"},
            {"type": "text", "md": """
ده الشكل اللي بنلاقيه في مشاريع كتير — وكل سطر فيه بيكسر مبدأ مختلف:
"""},
            {"type": "code", "lang": "csharp", "filename": "OrderService.cs", "title": "قبل التعديل — God Service", "code": r'''
public class OrderService
{
    // SRP: حفظ + حساب + إشعار + فاتورة + تسعير = 5 أسباب للتغيير
    public async Task Place(Order order)
    {
        await using var db = new AppDbContext("Server=.;Database=Shop;Trusted_Connection=True"); // DIP: تفاصيل الاتصال هنا
        order.Total = order.Lines.Sum(l => l.Price * l.Qty);

        if (order.Customer.Country == "EG") order.Total *= 1.14m;        // OCP: أي دولة جديدة = تعديل هنا
        else if (order.Customer.Country == "SA") order.Total *= 1.15m;
        else if (order.Customer.Country == "AE") order.Total *= 1.05m;

        db.Orders.Add(order);
        await db.SaveChangesAsync();

        // ISP: نفس الكلاس بيعرف عن SMTP وعن PDF
        using var smtp = new SmtpClient("smtp.mailgun.org", 587);
        await smtp.SendMailAsync("no-reply@shop.com", order.Customer.Email, "تم استلام طلبك", order.Id.ToString());

        File.WriteAllBytes($"invoices/{order.Id}.pdf", InvoicePdf.Render(order)); // تفاصيل تنفيذ ثابتة
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "أعراض بتقول إن الكود ده هيتعبك",
             "md": """
- عشان تختبر حساب الإجمالي لازم قاعدة بيانات وSMTP شغالين.
- إضافة دولة جديدة معناها تعديل ملف موجود (خطر regression).
- أي تغيير في طريقة إرسال الإيميل بيعدّل نفس الكلاس.
- الـconnection string مكتوب جوه الكود = مستحيل تغييره لكل بيئة.
"""},
            {"type": "heading", "level": 2, "text": "بعد: مسؤوليات مفصولة وتبعيات معكوسة"},
            {"type": "code", "lang": "csharp", "filename": "Domain/Orders", "title": "الـDomain: قواعد العمل من غير أي تفاصيل تقنية", "code": r'''
public interface ITaxPolicy           // DIP: التجريد في الـDomain
{
    decimal Apply(Order order);
}

public interface IOrderStore
{
    Task SaveAsync(Order order, CancellationToken ct = default);
}

public interface IOrderNotifier
{
    Task NotifyAsync(Order order, CancellationToken ct = default);
}

public sealed class Order
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public required Customer Customer { get; init; }
    public required IReadOnlyList<OrderLine> Lines { get; init; }
    public decimal SubTotal => Lines.Sum(l => l.Price * l.Quantity);
    public decimal Total { get; private set; }

    // SRP: الكيان مسؤول عن حالته وقواعد عمله فقط
    public void ApplyTax(ITaxPolicy policy) =>
        Total = policy.Apply(this);
}

public sealed class OrderPlacementService   // التنسيق فقط
{
    private readonly IOrderStore _store;
    private readonly IOrderNotifier _notifier;
    private readonly ITaxPolicy _tax;

    public OrderPlacementService(IOrderStore store, IOrderNotifier notifier, ITaxPolicy tax)
        => (_store, _notifier, _tax) = (store, notifier, tax);

    public async Task PlaceAsync(Order order, CancellationToken ct = default)
    {
        order.ApplyTax(_tax);
        await _store.SaveAsync(order, ct);
        await _notifier.NotifyAsync(order, ct);
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Tax/EgyptTaxPolicy.cs", "title": "OCP: دولة جديدة = كلاس جديد، من غير تعديل موجود", "code": r'''
public sealed class EgyptTaxPolicy : ITaxPolicy
{
    private const decimal Vat = 0.14m;
    public decimal Apply(Order order) =>
        order.Customer.Country == "EG" ? order.SubTotal * (1 + Vat) : order.SubTotal;
}

// اختيار السياسة من الإعداد (Composition Root) — مش جوه الـDomain
public static class TaxPolicyResolver
{
    public static ITaxPolicy Resolve(string country) => country switch
    {
        "EG" => new EgyptTaxPolicy(),
        "SA" => new SaudiTaxPolicy(),
        "AE" => new EmiratesTaxPolicy(),
        _    => new NoTaxPolicy(),
    };
}
'''},
            {"type": "text", "md": """
لاحظ الفرق: في النسخة الأولى كان `switch` البلدان **جوّه** منطق الطلب، فأي بلد جديد بيعدّل كود موجود.
في النسخة التانية، الـswitch بقى في **مكان واحد مسؤول عن الاختيار** (Composition Root / DI)، والـDomain
ما بيعرفش حاجة عن الضرائب المحلية.

وكمان: `OrderPlacementService` بقى قابل للاختبار بثواني، لأن كل تبعياته تجريدات:
"""},
            {"type": "code", "lang": "csharp", "filename": "OrderPlacementServiceTests.cs", "title": "DIP بيمكّنك تختبر من غير قاعدة بيانات ولا SMTP", "code": r'''
public sealed class OrderPlacementServiceTests
{
    private sealed class FakeStore : IOrderStore
    {
        public List<Order> Saved { get; } = [];
        public Task SaveAsync(Order order, CancellationToken ct = default)
        {
            Saved.Add(order);
            return Task.CompletedTask;
        }
    }

    private sealed class FakeNotifier : IOrderNotifier
    {
        public int Calls;
        public Task NotifyAsync(Order order, CancellationToken ct = default)
        {
            Interlocked.Increment(ref Calls);
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task Place_applies_tax_then_saves_then_notifies()
    {
        var store = new FakeStore();
        var notifier = new FakeNotifier();
        var sut = new OrderPlacementService(store, notifier, new EgyptTaxPolicy());

        var order = new Order
        {
            Customer = new Customer { Country = "EG" },
            Lines = [new OrderLine { Price = 100m, Quantity = 2 }],
        };

        await sut.PlaceAsync(order);

        order.Total.Should().Be(228m);          // 200 + 14%
        store.Saved.Should().ContainSingle();
        notifier.Calls.Should().Be(1);
    }
}
'''},
            {"type": "table", "head": ["المبدأ", "يعني إيه عمليًا في ASP.NET Core", "علامة إنك كسرته"], "rows": [
                ["SRP", "كل كلاس له سبب واحد للتغيير، والـControllers بتنسّق مش بتنّفذ", "الكلاس عنده 300+ سطر أو بيشتغل مع SMTP وEF في نفس الوقت"],
                ["OCP", "الامتداد بالـinterfaces/الـstrategies، مش بـif/else متنامية", "إضافة نوع جديد بتعدّل switch موجود في أكثر من ملف"],
                ["LSP", "المشتق بيحترم عقد الأساسي (يرجع نفس الضمانات)", "مشتق بيرمي NotImplementedException أو بيتجاهل معاملة مهمة"],
                ["ISP", "واجهات صغيرة حسب استخدام العميل", "تنفيذ بيضطر يكتب أعضاء فاضية أو يرمي استثناء"],
                ["DIP", "الطبقات العليا تعتمد على تجريدات مسجّلة في DI", "new AppDbContext() أو new SmtpClient() جوه كلاس عمل"],
            ]},
            {"type": "callout", "kind": "warn", "title": "Over-engineering: إمتى SOLID بيضر",
             "md": """
مش كل كلاس محتاج interface. قاعدة عملية:
اعمل abstraction لما **(1)** فيه أكثر من تنفيذ متوقع، أو **(2)** محتاج seam للاختبار، أو **(3)** ده حدّ وحدة/موديول.
غير كده، كلاس واحد مباشر أسهل في القراءة وأرخص في الصيانة.
وكمان: **متعملش Repository فوق EF Core** لمجرد «النظافة» — `DbContext` نفسه Unit of Work وRepository،
والطبقة الزايدة غالبًا بتسرّب LINQ على أي حال.
"""},
            {"type": "checkpoints", "items": [
                "أقدر أحدد سبب التغيير لكل كلاس في مشروعي، وأقول لو فيه كلاس له أكثر من سبب.",
                "أقدر أحوّل if/else متنامية إلى Strategy مسجّلة في DI.",
                "أقدر أكتب اختبار Unit لمنطق عمل من غير قاعدة بيانات ولا شبكة.",
                "أعرف الفرق بين «كود نظيف» و«كود فيه تجريدات بلا داعي».",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "كل ما العميل يطلب وسيلة دفع جديدة (فيزا/فودافون كاش/تقسيط) إنت بتعدّل نفس `switch` في `PaymentService`. أنهي مبدأ بيتكسر أساسًا؟",
                 "options": ["SRP", "OCP", "LSP", "ISP"], "answer": 1,
                 "explain": "المشكلة إن الكود **مقفول للامتداد**: كل إضافة بتعدّل كود قائم. الحل: `IPaymentMethod` مع تنفيذ لكل وسيلة وتسجيلها في DI (Strategy)."},
                {"q": "`public class ReadOnlyOrderStore : IOrderStore { public Task SaveAsync(...) => throw new NotImplementedException(); }` — ده خرق لأنهي مبدأ؟",
                 "options": ["DIP", "ISP (وLSP كمان)", "SRP", "OCP"], "answer": 1,
                 "explain": "العميل اتجبر يعتمد على عضو هو مش محتاجه (ISP)، والمشتق ما يقدرش يحل محل الأساسي (LSP). الحل: فصل `IOrderReader` عن `IOrderWriter`."},
                {"q": "أنهي تعديل يحقق DIP فعليًا؟",
                 "options": [
                     "نقل الـconnection string لملف appsettings",
                     "استقبال `IOrderStore` في الـconstructor بدل `new AppDbContext()` جوه الدالة",
                     "تقسيم الدالة الطويلة لدالتين",
                     "إضافة try/catch حول الحفظ",
                 ], "answer": 1,
                 "explain": "DIP يعني الاعتماد على تجريد يُحقن من بره. نقل الـconnection string تحسين إعدادات، مش عكس اتجاه الاعتماد."},
                {"q": "إمتى **ما** تعملش interface لخدمة عندك؟",
                 "options": [
                     "لما يكون فيها منطق عايز تختبره بمعزل",
                     "لما تتوقع تنفيذين مختلفين (مثلًا provider محلي وcloud)",
                     "لما تكون خدمة داخلية بتنفيذ واحد ومش محتاج seam للاختبار",
                     "لما تكون حدّ بين وحدتين (modules)",
                 ], "answer": 2,
                 "explain": "تجريد بلا سبب = ضوضاء. لو تنفيذ واحد ومش محتاج تستبدله في الاختبار، الكلاس المباشر أوضح."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "intro": "اعمل المهام دي على مشروعك الحقيقي لو ممكن — التعلم بيثبت لما تعدّل كود إنت كاتبه.", "items": [
                {"id": "t1", "title": "فكّك God Service",
                 "md": "خد أكبر Service في مشروعك (أو استخدم `OrderService` فوق)، وفصلها لـ3 مسؤوليات على الأقل مع حقن التبعيات من الـconstructor.",
                 "criteria": [
                     "مفيش `new` لأي تبعية خارجية (DB/SMTP/HTTP) جوه كلاس العمل",
                     "كل مسؤولية في كلاس مستقل باسم يشرحها",
                     "الـController/Endpoint بقى بينادي خدمة تنسيق واحدة",
                     "الكود بيترجم من غير تحذيرات جديدة",
                 ],
                 "hint": "ابدأ بسؤال: «لو اتغيرت طريقة إرسال الإيميل، أنهي ملف بيتعدّل؟» — الملف ده لازم يبقى `EmailOrderNotifier` بس.",
                 "solution": "الشكل النهائي: `IOrderStore` (EF implementation)، `IOrderNotifier` (Email/SMS implementations)، `ITaxPolicy` (policies)، و`OrderPlacementService` بتنسّق. سجلهم في `Program.cs` بـ`AddScoped`/`AddSingleton` حسب الطبيعة."},
                {"id": "t2", "title": "اختبار يثبت الـDIP",
                 "md": "اكتب اختبار xUnit واحد لـ`OrderPlacementService` باستخدام fakes (مش mocking library) يثبت إن: الضريبة اتحسبت، الطلب اتحفظ، والإشعار اتبعت — بالترتيب.",
                 "criteria": [
                     "الاختبار بيشتغل من غير قاعدة بيانات ولا شبكة",
                     "بيفشل لو شلت `await _store.SaveAsync(...)`",
                     "الـassertions على السلوك (Saved/Calls/Total) مش على تفاصيل داخلية",
                 ],
                 "hint": "لو لسه ما ثبّتّش مكتبة assertions، استخدم `Assert.Equal` العادية — الفكرة في الـfakes.",
                 "solution": [
                     {"type": "code", "lang": "bash", "title": "إنشاء مشروع الاختبار", "code": "dotnet new xunit -n Shop.Tests\ndotnet add Shop.Tests reference Shop.Core\ndotnet test"},
                     {"type": "text", "md": "الكود الكامل للاختبار موجود في مثال `OrderPlacementServiceTests` فوق — انسخه وشغّله، وبعدين اكسره عمدًا (شيل سطر الحفظ) واتأكد إنه fail."},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Microsoft — Architectural principles", "url": "https://learn.microsoft.com/dotnet/architecture/"},
                {"label": "Refactoring Guru — Design patterns", "url": "https://refactoring.guru/design-patterns"},
                {"label": "Clean Architecture sample (ardalis)", "url": "https://github.com/ardalis/CleanArchitecture"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s1-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الـ**Dependency Injection** في ASP.NET Core مش ميزة إضافية — دي الطريقة اللي بيتبني بيها التطبيق. وأهم قرار بتاخده
لكل خدمة هو **الـlifetime**: مين بيمتلك النسخة دي، وإمتى بتتعمل، وإمتى بتموت؟

الغلطة الأشهر (واللي بتظهر في الإنتاج مش في التطوير) هي **captive dependency**: خدمة Singleton تمسك خدمة Scoped،
فتقعد تعيش أكتر من الـRequest اللي عملها — ومع `DbContext` معناها بيانات متداخلة وتسريبات ذاكرة.
"""},
            {"type": "terms", "items": [
                {"term": "Transient", "def": "نسخة جديدة **كل مرة** تطلبها. خفيفة وبلا حالة (stateless)."},
                {"term": "Scoped", "def": "نسخة واحدة **لكل scope** — في الويب: لكل HTTP Request. ده الافتراضي للخدمات المرتبطة بالطلب زي `DbContext`."},
                {"term": "Singleton", "def": "نسخة واحدة **طوال عمر التطبيق**. لازم تكون thread-safe وبلا حالة مرتبطة بمستخدم."},
                {"term": "Captive dependency", "def": "خدمة طويلة العمر (Singleton) تعتمد على أقصر عمرًا (Scoped/Transient بحالة) — ASP.NET Core بيرفضها في Development."},
                {"term": "IServiceScopeFactory", "def": "الطريقة الشرعية لإنشاء scope جوه Singleton (زي BackgroundService) عشان تستهلك خدمات Scoped بأمان."},
                {"term": "Keyed services", "def": "من .NET 8: تسجيل أكثر من تنفيذ لنفس الـinterface بمفتاح، وحقنه بـ`[FromKeyedServices]`."},
            ]},
            {"type": "table", "head": ["Lifetime", "نسخة لكل", "استخدام نموذجي", "خطر رئيسي"], "rows": [
                ["Singleton", "التطبيق كله", "كاش، إعدادات ثابتة، `IHttpClientFactory`, clocks", "حالة مشتركة بين المستخدمين + captive dependency"],
                ["Scoped", "HTTP Request", "`DbContext`، Unit of Work، خدمات المستخدم الحالي", "استهلاكها من Singleton"],
                ["Transient", "كل حقن", "خدمات خفيفة بلا حالة، مappers", "إنشاؤها كتير لو ثقيلة، وموتها مع من حقنها"],
            ]},
            {"type": "heading", "level": 2, "text": "التسجيل والحقن"},
            {"type": "code", "lang": "csharp", "filename": "Program.cs", "title": "Composition Root — المكان الوحيد اللي بيتقرر فيه الـlifetimes", "code": r'''
var builder = WebApplication.CreateBuilder(args);

// Scoped: نسخة لكل request — مناسب للـDbContext
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseNpgsql(builder.Configuration.GetConnectionString("Shop")));

builder.Services.AddScoped<IOrderStore, EfOrderStore>();
builder.Services.AddScoped<ICurrentUser, HttpCurrentUser>();

// Transient: خفيفة وبلا حالة
builder.Services.AddTransient<OrderTotalCalculator>();

// Singleton: لازم تكون thread-safe وما تمسكش Scoped
builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddSingleton<ITaxPolicy, EgyptTaxPolicy>();

// Keyed services (.NET 8+): أكثر من تنفيذ لنفس العقد
builder.Services.AddKeyedSingleton<INotifier, EmailNotifier>("email");
builder.Services.AddKeyedSingleton<INotifier, SmsNotifier>("sms");

builder.Services.AddScoped<OrderPlacementService>(sp => new OrderPlacementService(
    sp.GetRequiredService<IOrderStore>(),
    sp.GetRequiredKeyedService<INotifier>("email"),
    sp.GetRequiredService<ITaxPolicy>()));

var app = builder.Build();
'''},
            {"type": "heading", "level": 2, "text": "الغلطة: Singleton يمسك Scoped"},
            {"type": "code", "lang": "csharp", "filename": "BrokenCache.cs", "title": "كود يبدو سليمًا… ويفشل في الإنتاج", "code": r'''
// ✗ خطأ: Singleton بيمسك IOrderStore (Scoped) وDbContext معه
public sealed class RecentOrdersCache
{
    private readonly IOrderStore _store;              // captive dependency
    private readonly List<Order> _items = [];

    public RecentOrdersCache(IOrderStore store) => _store = store;

    public async Task<IReadOnlyList<Order>> GetAsync()
    {
        if (_items.Count == 0)
            _items.AddRange(await _store.RecentAsync());   // أي مستخدم؟ أي request؟
        return _items;                                      // حالة مشتركة بين كل المستخدمين!
    }
}

builder.Services.AddSingleton<RecentOrdersCache>();
// في Development: InvalidOperationException
// "Cannot consume scoped service 'IOrderStore' from singleton 'RecentOrdersCache'."
// في Production (لو ValidateScopes متقفل): DbContext عايش للأبد + بيانات مستخدمين متداخلة
'''},
            {"type": "callout", "kind": "note", "title": "ليه بتشوف الخطأ في Development بس؟",
             "md": """
`builder.Host.UseDefaultServiceProvider(o => { o.ValidateScopes = true; o.ValidateOnBuild = true; })`
مفعّل افتراضيًا في بيئة Development. في Production بيتقفل لأسباب أداء، فالخطأ بيتحول لتسريب صامت.
خليك صريح وفعّلها في الاختبارات كمان:
"""},
            {"type": "code", "lang": "csharp", "title": "تفعيل التحقق في كل البيئات (مع إبقاء الإنتاج سريعًا)", "code": r'''
builder.Host.UseDefaultServiceProvider(options =>
{
    options.ValidateScopes = builder.Environment.IsDevelopment() || IsTestRun();
    options.ValidateOnBuild = builder.Environment.IsDevelopment();
});

static bool IsTestRun() =>
    Environment.GetEnvironmentVariable("DOTNET_ENVIRONMENT") == "Testing";
'''},
            {"type": "heading", "level": 2, "text": "الإصلاح: scope صريح أو lifetime مناسب"},
            {"type": "code", "lang": "csharp", "filename": "FixedCache.cs", "title": "الحل 1: إنشاء scope لكل عملية داخل Singleton", "code": r'''
public sealed class RecentOrdersCache(TimeProvider time, IServiceScopeFactory scopes)
{
    private readonly TimeSpan _ttl = TimeSpan.FromSeconds(30);
    private IReadOnlyList<Order> _items = [];
    private DateTimeOffset _expiresAt = DateTimeOffset.MinValue;
    private readonly SemaphoreSlim _gate = new(1, 1);

    public async Task<IReadOnlyList<Order>> GetAsync(CancellationToken ct = default)
    {
        if (time.GetUtcNow() < _expiresAt) return _items;

        await _gate.WaitAsync(ct);
        try
        {
            if (time.GetUtcNow() < _expiresAt) return _items;

            await using var scope = scopes.CreateAsyncScope();   // ✓ scope صريح
            var store = scope.ServiceProvider.GetRequiredService<IOrderStore>();
            _items = await store.RecentAsync(ct);
            _expiresAt = time.GetUtcNow().Add(_ttl);
            return _items;
        }
        finally { _gate.Release(); }
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Worker.cs", "title": "الحل 2: BackgroundService — نفس القاعدة بالضبط", "code": r'''
public sealed class OrderCleanupWorker(IServiceScopeFactory scopes, ILogger<OrderCleanupWorker> log)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromMinutes(5));
        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                var removed = await db.Orders
                    .Where(o => o.Status == OrderStatus.Abandoned && o.CreatedAt < DateTime.UtcNow.AddHours(-2))
                    .ExecuteDeleteAsync(stoppingToken);
                log.LogInformation("cleaned {Count} abandoned orders", removed);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                log.LogError(ex, "cleanup iteration failed");   // بلا catch = الـworker يموت بصمت
            }
        }
    }
}
'''},
            {"type": "callout", "kind": "tip", "title": "قواعد سريعة تحفظك",
             "md": """
- **الافتراضي Scoped** لأي خدمة مرتبطة بطلب. حوّلها Singleton بس لما تثبت إنها thread-safe وبلا حالة.
- **مفيش حالة مستخدم في Singleton** — ولا كاش مشترك من غير `SemaphoreSlim`/`ConcurrentDictionary`.
- **Transient جوه Singleton** بيبقى عمليًا singleton (بيتحقن مرة واحدة) — لو له حالة، ده باج.
- **BackgroundService = Singleton**: استخدم `IServiceScopeFactory` دايمًا.
- فعّل `ValidateScopes`/`ValidateOnBuild` في Development والاختبارات.
"""},
            {"type": "checkpoints", "items": [
                "أشرح الفرق بين الثلاثة lifetimes بمثال من مشروعي.",
                "أكتشف captive dependency من رسالة الخطأ أو من قراءة التسجيلات.",
                "أستخدم `IServiceScopeFactory` في خدمة Singleton أو BackgroundService.",
                "أسجّل تنفيذين لنفس العقد بـkeyed services وأختار بينهم.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`DbContext` مسجّل بـ`AddDbContext` (Scoped). أنهي تسجيل هيثير captive dependency؟",
                 "options": [
                     "`builder.Services.AddScoped<IOrderService, OrderService>()`",
                     "`builder.Services.AddSingleton<IReportService, ReportService>()` و`ReportService` بياخد `AppDbContext` في الـconstructor",
                     "`builder.Services.AddTransient<OrderMapper>()`",
                     "`builder.Services.AddSingleton(TimeProvider.System)`",
                 ], "answer": 1,
                 "explain": "Singleton بيستهلك Scoped. الصح: تخلي `ReportService` Scoped، أو تستخدم `IServiceScopeFactory` جوه Singleton."},
                {"q": "خدمة Transient اتحقنت جوه Singleton. إيه اللي بيحصل فعليًا؟",
                 "options": [
                     "بيتعمل نسخة جديدة مع كل استخدام",
                     "بيتعمل نسخة واحدة وقت إنشاء الـSingleton وتفضل معاه",
                     "بيرمي استثناء دايمًا",
                     "بيتحوّل تلقائيًا لـScoped",
                 ], "answer": 1,
                 "explain": "الـTransient بيتحل مرة واحدة وقت بناء الـSingleton، فبياخد عمره. لو الخدمة دي بحالة (stateful) ده مصدر باجات."},
                {"q": "في `BackgroundService` محتاج تقرأ من قاعدة البيانات كل دقيقة. إيه الصح؟",
                 "options": [
                     "تحقن `AppDbContext` في الـconstructor وتستخدمه كل مرة",
                     "تعمل `CreateAsyncScope()` جوه كل دورة وتحل الـDbContext منها",
                     "تسجّل الـBackgroundService كـScoped",
                     "تستخدم static DbContext مشترك",
                 ], "answer": 1,
                 "explain": "الـHosted services singletons. الـscope المؤقت بيديك `DbContext` بعمر دورة واحدة ويتخلص منها بشكل صحيح."},
                {"q": "عايز تنفيذين لـ`INotifier` (email وsms) وتختار بينهم وقت الحقن. أفضل حل حديث؟",
                 "options": [
                     "`IEnumerable<INotifier>` واختيار بالـindex",
                     "Keyed services مع `[FromKeyedServices(\"email\")]` أو `GetRequiredKeyedService`",
                     "classين بأسماء مختلفة من غير interface مشترك",
                     "Singleton بيقرأ setting في كل نداء",
                 ], "answer": 1,
                 "explain": "Keyed services (‎.NET 8+) بتحل المشكلة دي مباشرة وبشكل مصرّح به في مكان الحقن."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "اصنع الباج وبعدين اصلحه",
                 "md": "في مشروع تجريبي: سجّل `DbContext` كـScoped وخدمة Singleton بتستهلكه. شغّل في Development، وثّق رسالة الخطأ، ثم أصلحها بطريقتين: مرة بتغيير الـlifetime، ومرة بـ`IServiceScopeFactory`.",
                 "criteria": [
                     "شفت `InvalidOperationException: Cannot consume scoped service ...` بنفسك",
                     "الإصلاح الأول: الخدمة بقت Scoped والطلب شغال",
                     "الإصلاح التاني: Singleton مع scope صريح وشغال",
                     "كتبت في ملاحظاتك إمتى تختار كل إصلاح",
                 ],
                 "hint": "لو الرسالة مش ظاهرة، تأكد إن `ValidateScopes = true` (وهو الافتراضي في Development) وإنك بتحل الخدمة فعلًا وقت البناء أو في أول طلب."},
                {"id": "t2", "title": "Worker آمن",
                 "md": "اكتب `BackgroundService` بـ`PeriodicTimer` كل 10 ثواني ينشئ scope، يعدّ الطلبات الجديدة، ويسجّل الرقم — مع معالجة الاستثناءات بحيث الـworker ما يموتش.",
                 "criteria": [
                     "بيستخدم `IServiceScopeFactory` مش حقن مباشر",
                     "فيه `try/catch` حول الدورة مع logging",
                     "بيحترم `stoppingToken` ويقفل بنظافة",
                     "السجل بيظهر رقم متزايد كل 10 ثواني",
                 ],
                 "solution": "راجع `OrderCleanupWorker` في الشرح — نفس الهيكل مع `PeriodicTimer` و`CreateAsyncScope` و`log.LogError` جوه catch."},
            ]},
            {"type": "resources", "items": [
                {"label": "Dependency injection in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/dependency-injection"},
                {"label": "Hosted services / BackgroundService", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/host/hosted-services"},
                {"label": "Keyed DI services", "url": "https://learn.microsoft.com/dotnet/core/extensions/dependency-injection-usage"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l3
    {
        "id": "s1-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الإعدادات (Configuration) أكتر مكان بيتكتب فيه كود سريع وبينفجر لاحقًا: connection strings في الـrepo،
`IConfiguration["..."]` منتشر في كل ملف، وإعداد بيتغير في الإنتاج من غير ما حد ياخد باله.

الحل في .NET بسيط وموجود من زمان: **Options Pattern** — كائنات strongly-typed، متحقَّق منها عند الإقلاع،
ومحقونة بالـDI. والأسرار بره الكود تمامًا: User Secrets محليًا، وKey Vault/متغيرات بيئة في السحابة.
"""},
            {"type": "terms", "items": [
                {"term": "IConfiguration", "def": "قراءة قيم مباشرة بمفتاح نصي. مرن لكنه stringly-typed — استخدمه في الـComposition Root فقط."},
                {"term": "IOptions<T>", "def": "كائن إعدادات مُحقن، **Singleton**، بيتحسب مرة واحدة ولا يتغير بعد الإقلاع."},
                {"term": "IOptionsSnapshot<T>", "def": "**Scoped** — بيتعاد حسابه لكل request، فبيلتقط التغيير في الملفات أثناء التشغيل."},
                {"term": "IOptionsMonitor<T>", "def": "**Singleton** مع إشعار تغيير (`OnChange`) — مناسب للخدمات الطويلة العمر."},
                {"term": "User Secrets", "def": "أسرار التطوير مخزّنة بره مجلد المشروع (وبره git) ومرتبطة بـ`UserSecretsId`."},
                {"term": "ValidateOnStart", "def": "التحقق من صحة الإعدادات عند الإقلاع — يفشل التطبيق بدري بدل ما يفشل أول طلب."},
            ]},
            {"type": "code", "lang": "json", "filename": "appsettings.json", "title": "أقسام واضحة، ولا سر هنا", "code": r'''
{
  "ConnectionStrings": {
    "Shop": ""
  },
  "Payments": {
    "Provider": "stripe",
    "TimeoutSeconds": 10,
    "RetryCount": 3,
    "WebhookPath": "/hooks/payments"
  },
  "Email": {
    "From": "no-reply@shop.example",
    "Host": "smtp.example",
    "Port": 587
  },
  "Serilog": {
    "MinimumLevel": { "Default": "Information" }
  }
}
'''},
            {"type": "code", "lang": "bash", "title": "الأسرار: User Secrets محليًا (وبره git)", "code": r'''
# مرة واحدة لكل مشروع
dotnet user-secrets init

# القيم الحساسة
dotnet user-secrets set "ConnectionStrings:Shop" "Host=localhost;Database=shop;Username=dev;Password=dev-only"
dotnet user-secrets set "Payments:ApiKey" "sk_test_..."
dotnet user-secrets set "Email:Password" "..."

# مكان التخزين (بره مجلد المشروع):
#   Linux/macOS: ~/.microsoft/usersecrets/<UserSecretsId>/secrets.json
#   Windows:     %APPDATA%\Microsoft\UserSecrets\<UserSecretsId>\secrets.json
dotnet user-secrets list
'''},
            {"type": "callout", "kind": "warn", "title": "ترتيب المصادر (الأخير يكسب)",
             "md": """
`appsettings.json` ← `appsettings.{Environment}.json` ← **User Secrets** (Development) ← متغيرات البيئة ← سطر الأوامر.
يعني متغير البيئة `ConnectionStrings__Shop` بيتجاوز كل حاجة — وده بالظبط اللي تستخدمه في Docker/Kubernetes/Azure.
**ما تحطش أسرار في `appsettings.Production.json`** — ده ملف في الـrepo.
"""},
            {"type": "heading", "level": 2, "text": "Options قوية الأنواع + تحقق عند الإقلاع"},
            {"type": "code", "lang": "csharp", "filename": "Configuration/PaymentOptions.cs", "title": "كلاس الإعدادات مع DataAnnotations", "code": r'''
using System.ComponentModel.DataAnnotations;

namespace Shop.Configuration;

[OptionsName]
public sealed class PaymentOptions
{
    public const string SectionName = "Payments";

    [Required]
    public string Provider { get; init; } = "stripe";

    [Range(1, 120)]
    public int TimeoutSeconds { get; init; } = 10;

    [Range(0, 10)]
    public int RetryCount { get; init; } = 3;

    public Uri WebhookUrl { get; init; } = new("https://localhost/hooks/payments");

    // السر نفسه: يُحقن من البيئة/Key Vault، ومش بيتسجل في اللوج أبدًا
    public string ApiKey { get; init; } = "";
}

public sealed class EmailOptions
{
    public const string SectionName = "Email";
    [Required, EmailAddress] public string From { get; init; } = "";
    [Required] public string Host { get; init; } = "";
    [Range(1, 65535)] public int Port { get; init; } = 587;
}

// Attribute اختياري للتوثيق الذاتي
[AttributeUsage(AttributeTargets.Class)]
public sealed class OptionsNameAttribute : Attribute;
'''},
            {"type": "code", "lang": "csharp", "filename": "Program.cs", "title": "الربط + التحقق + الفشل المبكر", "code": r'''
using Shop.Configuration;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddOptions<PaymentOptions>()
    .Bind(builder.Configuration.GetSection(PaymentOptions.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();                       // ✓ يفشل عند الإقلاع مش وقت أول طلب

builder.Services
    .AddOptions<EmailOptions>()
    .Bind(builder.Configuration.GetSection(EmailOptions.SectionName))
    .ValidateDataAnnotations()
    .Validate(o => o.Port is > 0 and < 65536, "Port out of range")
    .ValidateOnStart();

// تحقق مخصص أعقد
builder.Services
    .AddOptions<PaymentOptions>()
    .Validate(o => !string.IsNullOrWhiteSpace(o.ApiKey) || builder.Environment.IsDevelopment(),
              "Payments:ApiKey is required outside Development");

builder.Services.AddScoped<PaymentGateway>();
var app = builder.Build();
'''},
            {"type": "code", "lang": "csharp", "filename": "Payments/PaymentGateway.cs", "title": "الاستهلاك: حقن IOptions<T>", "code": r'''
public sealed class PaymentGateway(
    IOptions<PaymentOptions> options,
    IHttpClientFactory httpFactory,
    ILogger<PaymentGateway> log)
{
    private readonly PaymentOptions _options = options.Value;
    private readonly HttpClient _http = httpFactory.CreateClient("payments");

    public async Task<ChargeResult> ChargeAsync(ChargeRequest request, CancellationToken ct)
    {
        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        cts.CancelAfter(TimeSpan.FromSeconds(_options.TimeoutSeconds));

        using var msg = new HttpRequestMessage(HttpMethod.Post, "/v1/charges");
        msg.Headers.Authorization = new("Bearer", _options.ApiKey);   // السر من Environment/Key Vault
        msg.Content = JsonContent.Create(request);

        try
        {
            var res = await _http.SendAsync(msg, cts.Token);
            res.EnsureSuccessStatusCode();
            return await res.Content.ReadFromJsonAsync<ChargeResult>(cts.Token)
                   ?? throw new InvalidOperationException("empty charge response");
        }
        catch (Exception ex)
        {
            // ⚠ لا تسجلApiKey أو الترويسة — سجل السياق الآمن فقط
            log.LogError(ex, "charge failed for {OrderId} via {Provider}", request.OrderId, _options.Provider);
            throw;
        }
    }
}
'''},
            {"type": "table", "head": ["الواجهة", "Lifetime", "بتتحدث؟", "إمتى تستخدمها"], "rows": [
                ["`IOptions<T>`", "Singleton", "لا", "الافتراضي: إعداد ثابت طول عمر التطبيق"],
                ["`IOptionsSnapshot<T>`", "Scoped", "نعم (كل request)", "عايز تغيير الملف ينعكس بدون إعادة تشغيل — في خدمات مرتبطة بطلب"],
                ["`IOptionsMonitor<T>`", "Singleton", "نعم (+OnChange)", "خدمات طويلة العمر (Worker/Kestrel) محتاجة تعرف بالتغيير"],
            ]},
            {"type": "callout", "kind": "tip", "title": "لما تنتقل للسحابة",
             "md": """
في Azure استخدم **Managed Identity + Key Vault** (من غير أسرار في الكود أو في الـCI)، وفي Kubernetes استخدم
**Secrets** مع `envFrom`، وفي Docker استخدم متغيرات البيئة. كود التطبيق ما بيتغيرش — بيقرأ من `IConfiguration`
اللي بيوصل له القيم من المصدر المناسب. وده بالظبط مكسب الـOptions Pattern.
"""},
            {"type": "checkpoints", "items": [
                "أقدر أحوّل أي `IConfiguration[\"...\"]` منتشر إلى كلاس Options قوي الأنواع.",
                "أخلي التطبيق يفشل عند الإقلاع لو إعداد ناقص أو غلط.",
                "أخزّن أسرار التطوير خارج المستودع وأضبط الإنتاج بمتغيرات بيئة/Key Vault.",
                "أختار بين IOptions وIOptionsSnapshot وIOptionsMonitor بمبرر.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "خدمة Singleton طويلة العمر محتاجة تعرف لو ملف الإعداد اتغير وقت التشغيل. تستخدم إيه؟",
                 "options": ["IOptions<T>", "IOptionsSnapshot<T>", "IOptionsMonitor<T>", "IConfiguration مباشرة"], "answer": 2,
                 "explain": "`IOptionsSnapshot` Scoped (مش هيشتغل في Singleton)، بينما `IOptionsMonitor` Singleton وبيدعم `OnChange`."},
                {"q": "إيه فايدة `ValidateOnStart()`؟",
                 "options": [
                     "بيسرّع الإقلاع",
                     "بيفشل التطبيق بدري لو إعداد غلط، بدل فشل وقت أول طلب",
                     "بيمنع تغيير الإعدادات",
                     "بيشفّر الأسرار",
                 ], "answer": 1,
                 "explain": "فشل مبكر وواضح = نشر سيء ما يوصلش الإنتاج. من غيره، الخطأ يظهر كـ500 لأول مستخدم."},
                {"q": "أفضل مكان لـconnection string الخاص بـProduction في تطبيق منشور على Azure؟",
                 "options": [
                     "appsettings.Production.json في المستودع",
                     "متغير بيئة / Key Vault مع Managed Identity",
                     "مكتوب في Program.cs",
                     "في ملف .env داخل صورة Docker",
                 ], "answer": 1,
                 "explain": "الأسرار بره الكود وبره المستودع وبره الصورة. Key Vault + Managed Identity يلغي الحاجة لأي سر مخزّن."},
                {"q": "ترتيب المصادر في .NET: أنهي بيتجاوز التاني؟",
                 "options": [
                     "appsettings.json يتجاوز متغيرات البيئة",
                     "متغيرات البيئة تتجاوز appsettings.json",
                     "User Secrets تتجاوز متغيرات البيئة في الإنتاج",
                     "الترتيب أبجدي",
                 ], "answer": 1,
                 "explain": "المصادر اللاحقة تكسب: appsettings ← appsettings.{Env} ← User Secrets (Development) ← Environment ← CLI."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "حوّل إعدادات مشروعك لـOptions",
                 "md": "اختار قسم إعدادات حقيقي في مشروعك (Email/Payments/Jwt/Storage) وحوّله لكلاس Options مع DataAnnotations و`ValidateOnStart`، وامسح كل استخدام مباشر لـ`IConfiguration` برا الـComposition Root.",
                 "criteria": [
                     "كلاس Options واحد لكل قسم مع `const string SectionName`",
                     "تحقق DataAnnotations + قاعدة مخصصة واحدة على الأقل",
                     "مفيش `IConfiguration[\"key\"]` في خدمات العمل",
                     "التطبيق يفشل عند الإقلاع لو حذفت قيمة مطلوبة (جرّب)",
                 ],
                 "hint": "ابدأ بـ`builder.Services.AddOptions<T>().Bind(section).ValidateDataAnnotations().ValidateOnStart();` وبعدين حقن `IOptions<T>` في الخدمة."},
                {"id": "t2", "title": "أسرار نظيفة",
                 "md": "أخرج كل الأسرار من المستودع إلى User Secrets، وأضف `.gitignore` للتأكد، واكتب في README كيف يضبط مطور جديد أسراره المحلية.",
                 "criteria": [
                     "`dotnet user-secrets list` يعرض القيم والتطبيق يشتغل",
                     "لا يوجد سر في أي ملف متتبع بـgit (تحقق بـ`git grep -i password`)",
                     "README فيه خطوة `dotnet user-secrets set ...` جاهزة للنسخ",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Options pattern in .NET", "url": "https://learn.microsoft.com/dotnet/core/extensions/options"},
                {"label": "Configuration in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/configuration/"},
                {"label": "Safe storage of app secrets in development", "url": "https://learn.microsoft.com/aspnet/core/security/app-secrets"},
                {"label": "Azure Key Vault", "url": "https://learn.microsoft.com/azure/key-vault/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s1-m1-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
كل طلب بيدخل نظامك هو **مدخل غير موثوق**. لو التحقق من المدخلات متناثر في الـServices، هتلاقي نفسك
بتتحقق من نفس الحاجة في تلات أماكن وتنسى الرابع.

النمط المطلوب: قواعد التحقق في **كلاس Validator مستقل**، يشتغل أوتوماتيك قبل الوصول لمنطق العمل،
ويرجع استجابة أخطاء **موحّدة** تقدر الواجهة تعرضها مباشرة. ده بالظبط اللي بتوفره FluentValidation.
"""},
            {"type": "terms", "items": [
                {"term": "AbstractValidator<T>", "def": "الكلاس اللي بيحتوي قواعد التحقق لنوع معين (DTO أو command)."},
                {"term": "RuleFor / RuleForEach", "def": "بداية كل قاعدة: حدد الخاصية، ثم سلسل القيود (`NotEmpty`, `MaximumLength`, `Matches`…)."},
                {"term": "Must / Custom", "def": "قاعدة مخصصة بدالة — للتحقق المعتمد على أكثر من خاصية أو على خدمة خارجية."},
                {"term": "ValidationFailure / Result", "def": "نتيجة التحقق: قائمة أخطاء لكل واحدة `PropertyName` و`ErrorMessage` و`ErrorCode`."},
                {"term": "Fail-fast (CascadeMode.Stop)", "def": "التوقف عند أول خطأ في القاعدة بدل إنتاج قائمة طويلة."},
                {"term": "Severity", "def": "تمييز الأخطاء عن التحذيرات (Warning) داخل نفس النتيجة."},
            ]},
            {"type": "heading", "level": 2, "text": "الـDTO والـValidator"},
            {"type": "code", "lang": "csharp", "filename": "Orders/CreateOrderRequest.cs", "title": "عقد الطلب (ما تخلطهوش بالـEntity)", "code": r'''
public sealed record CreateOrderRequest(
    Guid CustomerId,
    IReadOnlyList<CreateOrderLine> Lines,
    string? CouponCode,
    string? Note);

public sealed record CreateOrderLine(Guid ProductId, int Quantity, decimal UnitPrice);
'''},
            {"type": "code", "lang": "csharp", "filename": "Orders/CreateOrderValidator.cs", "title": "قواعد واضحة وقابلة للقراءة والاختبار", "code": r'''
using FluentValidation;

public sealed class CreateOrderValidator : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderValidator()
    {
        RuleFor(x => x.CustomerId)
            .NotEmpty().WithMessage("معرّف العميل مطلوب");

        RuleFor(x => x.Lines)
            .NotEmpty().WithMessage("الطلب لازم يحتوي على صنف واحد على الأقل")
            .Must(lines => lines!.Count <= 100).WithMessage("الحد الأقصى 100 صنف في الطلب")
            .ForEach(line => line.SetValidator(new OrderLineValidator()));

        RuleFor(x => x.CouponCode)
            .MaximumLength(32)
            .Matches("^[A-Z0-9-]+$").When(x => x.CouponCode is not null)
            .WithMessage("كود الكوبون غير صالح");

        RuleFor(x => x.Note)
            .MaximumLength(500);

        // قاعدة عبر أكثر من خاصية
        RuleFor(x => x)
            .Must(x => x.Lines?.Sum(l => l.Quantity) <= 1000)
            .WithMessage("إجمالي الكميات لا يتجاوز 1000")
            .WithErrorCode("ORDER_QTY_LIMIT");
    }
}

public sealed class OrderLineValidator : AbstractValidator<CreateOrderLine>
{
    public OrderLineValidator()
    {
        RuleFor(l => l.ProductId).NotEmpty();
        RuleFor(l => l.Quantity).InclusiveBetween(1, 500);
        RuleFor(l => l.UnitPrice).InclusiveBetween(0.01m, 1_000_000m)
            .WithMessage("السعر خارج النطاق المسموح");
    }
}
'''},
            {"type": "heading", "level": 2, "text": "التشغيل التلقائي في الـEndpoints"},
            {"type": "code", "lang": "csharp", "filename": "Program.cs", "title": "تسجيل + Endpoint Filter يشغّل التحقق قبل منطق العمل", "code": r'''
using FluentValidation;

var builder = WebApplication.CreateBuilder(args);

// تسجيل كل الـValidators في الـassembly مرة واحدة
builder.Services.AddValidatorsFromAssemblyContaining<CreateOrderValidator>(ServiceLifetime.Scoped);
builder.Services.AddScoped<IValidationRunner, ValidationRunner>();

var app = builder.Build();

app.MapPost("/api/orders", async (
    CreateOrderRequest request,
    IValidationRunner validator,
    OrderPlacementService orders,
    CancellationToken ct) =>
{
    var failures = await validator.ValidateAsync(request, ct);
    if (failures.Count > 0)
        return Results.ValidationProblem(
            failures.GroupBy(f => f.PropertyName)
                    .ToDictionary(g => g.Key, g => g.Select(f => f.ErrorMessage).ToArray()));

    var id = await orders.PlaceAsync(request, ct);
    return Results.Created($"/api/orders/{id}", new { id });
})
.WithName("CreateOrder")
.WithOpenApi();

app.Run();
'''},
            {"type": "code", "lang": "csharp", "filename": "Validation/ValidationRunner.cs", "title": "تشغيل عام لأي DTO (يصلح للـEndpoints كلها)", "code": r'''
using FluentValidation;

public interface IValidationRunner
{
    Task<IReadOnlyList<ValidationFailure>> ValidateAsync<T>(T instance, CancellationToken ct = default);
}

public sealed class ValidationRunner(IEnumerable<IValidator> validators) : IValidationRunner
{
    public async Task<IReadOnlyList<ValidationFailure>> ValidateAsync<T>(T instance, CancellationToken ct = default)
    {
        var failures = new List<ValidationFailure>();
        foreach (var validator in validators.OfType<IValidator<T>>())
        {
            var result = await validator.ValidateAsync(new ValidationContext<T>(instance), ct);
            if (!result.IsValid) failures.AddRange(result.Errors);
        }
        return failures;
    }
}
'''},
            {"type": "callout", "kind": "note", "title": "الرد الموحد: ValidationProblemDetails",
             "md": """
`Results.ValidationProblem(...)` بيرجع **400** بجسم `application/problem+json` بالشكل ده —
والواجهة تقدر تعرضه مباشرة بدون parsing مخصص:
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "errors": {
    "Lines[0].Quantity": ["الكمية يجب أن تكون بين 1 و500"],
    "CouponCode": ["كود الكوبون غير صالح"]
  },
  "traceId": "00-8f2c...-01"
}
```
"""},
            {"type": "callout", "kind": "tip", "title": "في .NET 10 فيه Validation مدمج للـMinimal APIs",
             "md": """
ASP.NET Core 10 أضاف دعم التحقق (DataAnnotations) داخل Minimal APIs بشكل مدمج، وده يغطي الحالات البسيطة.
اختيار عملي شائع: **DataAnnotations للعقود البسيطة + FluentValidation للقواعد المعقدة** (عبر أكثر من خاصية،
تحقق غير متزامن، رسائل معرّفة). راجع التوثيق للتفعيل واختر أسلوبًا واحدًا لكل المشروع عشان الرسائل تفضل موحّدة.
"""},
            {"type": "heading", "level": 2, "text": "اختبار الـValidator (بلا API)"},
            {"type": "code", "lang": "csharp", "filename": "CreateOrderValidatorTests.cs", "title": "اختبارات سريعة ومباشرة", "code": r'''
public sealed class CreateOrderValidatorTests
{
    private readonly CreateOrderValidator _sut = new();

    [Fact]
    public async Task Empty_lines_is_rejected()
    {
        var request = new CreateOrderRequest(Guid.NewGuid(), [], null, null);

        var result = await _sut.ValidateAsync(request);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyName == "Lines");
    }

    [Fact]
    public async Task Quantity_above_500_is_rejected_with_property_path()
    {
        var request = new CreateOrderRequest(
            Guid.NewGuid(),
            [new CreateOrderLine(Guid.NewGuid(), 900, 10m)],
            null, null);

        var result = await _sut.ValidateAsync(request);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyName.Contains("Quantity"));
    }

    [Theory]
    [InlineData("SAVE-10")]
    [InlineData("A1")]
    public async Task Valid_coupon_shapes_pass(string code)
    {
        var request = new CreateOrderRequest(
            Guid.NewGuid(),
            [new CreateOrderLine(Guid.NewGuid(), 1, 10m)],
            code, null);

        (await _sut.ValidateAsync(request)).IsValid.Should().BeTrue();
    }
}
'''},
            {"type": "table", "head": ["المكان", "نوع التحقق", "مثال"], "rows": [
                ["الـValidator (FluentValidation)", "شكل المدخل وقواعده", "مطلوب، طول، نطاق، regex، قاعدة عبر خصائص"],
                ["الـDomain (الكيان)", "قواعد العمل", "«الطلب الملغي لا يُعدَّل»، «الرصيد لا يقل عن صفر»"],
                ["قاعدة البيانات", "السلامة النهائية", "Unique/FK/Check constraints — آخر خط دفاع"],
            ], "caption": "التحقق مش طبقة واحدة: الشكل عند الحافة، والقواعد في الـDomain، والسلامة في قاعدة البيانات."},
            {"type": "checkpoints", "items": [
                "أكتب Validator لقواعد معقدة (عبر خصائص، قوائم، غير متزامن).",
                "أشغّل التحقق تلقائيًا قبل منطق العمل وأرجع 400 موحّد.",
                "أختبر الـValidator كوحدة مستقلة بدون API.",
                "أفرّق بين تحقق الشكل (edge) وقواعد العمل (domain) وقيود قاعدة البيانات.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "القاعدة «تاريخ النهاية لازم يكون بعد تاريخ البداية» مكانها الأنسب؟",
                 "options": ["DataAnnotations على كل خاصية لوحدها", "`RuleFor(x => x).Must(...)` في الـValidator", "جوه الـController", "في قاعدة البيانات فقط"], "answer": 1,
                 "explain": "قاعدة عبر أكثر من خاصية تُكتب على الكائن كله (`RuleFor(x => x)`) أو بـ`Must` مرتبطة بخاصية مع `WithMessage`."},
                {"q": "ليه الأفضل إن الـValidator يرجع 400 بـValidationProblemDetails بدل رسالة نصية؟",
                 "options": [
                     "أسرع في الأداء",
                     "عقد موحّد (RFC 9457) تقدر الواجهة تعرضه مباشرة لكل الأخطاء",
                     "بيشفّر البيانات",
                     "بيتجنب الحاجة للـlogging",
                 ], "answer": 1,
                 "explain": "التوحيد هو المكسب: كل أخطاء التحقق في مشروعك بشكل واحد، فالعميل يكتب معالجة مرة واحدة."},
                {"q": "أنهي حالة **ما** ينفعش تتحل بـFluentValidation لوحدها وتحتاج قيد في قاعدة البيانات؟",
                 "options": [
                     "طول الاسم الأقصى 100 حرف",
                     "أن البريد الإلكتروني فريد بين كل المستخدمين",
                     "أن الكمية أكبر من صفر",
                     "أن الكود يتكون من حروف كبيرة",
                 ], "answer": 1,
                 "explain": "التفرد عبر كل الصفوف يحتاج قيد Unique (وحتى مع تحقق غير متزامن، فيه سباق زمني). القاعدة الأخيرة في قاعدة البيانات."},
                {"q": "إمتى تستخدم `CascadeMode.Stop`؟",
                 "options": [
                     "لما عايز كل الأخطاء دفعة واحدة للواجهة",
                     "لما التحقق التالي مالوش معنى بعد فشل الأول (زي ما يكون الحقل فاضي)",
                     "لما التحقق غير متزامن",
                     "دايمًا في كل validator",
                 ], "answer": 1,
                 "explain": "Fail-fast بيقلل الضوضاء: بعد `NotEmpty` فشل، مالوش لازمة تشتكي من الـregex."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "Validator كامل لـendpoint حقيقي",
                 "md": "اختار endpoint في مشروعك (أو `CreateOrderRequest` فوق) واكتب له Validator كامل مع قواعد عبر الخصائص، وشغّله تلقائيًا، وارجع `ValidationProblem`.",
                 "criteria": [
                     "5 قواعد على الأقل، منها واحدة عبر أكثر من خاصية",
                     "رسائل بالعربي و`ErrorCode` ثابت للأخطاء المهمة",
                     "الاستجابة 400 بشكل problem+json",
                     "3 اختبارات على الأقل للـValidator (نجاح + فشلين)",
                 ],
                 "hint": "استخدم `WithErrorCode` عشان الواجهة تتصرف بحسب الكود مش النص (النص ممكن يُترجم)."},
                {"id": "t2", "title": "منع التحقق المكرر",
                 "md": "ابحث في مشروعك عن كل أماكن التحقق اليدوي (`if (string.IsNullOrWhite...` في الخدمات) وانقلها للـValidators، وسيب في الـDomain قواعد العمل فقط.",
                 "criteria": [
                     "قائمة بالمواضع اللي شلتها (في ملاحظات الدرس)",
                     "الـDomain بقى بيتحقق من القواعد مش من الشكل",
                     "الاختبارات كلها لسه ناجحة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "FluentValidation documentation", "url": "https://docs.fluentvalidation.net/"},
                {"label": "Minimal APIs in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis"},
                {"label": "What's new in ASP.NET Core (validation in Minimal APIs)", "url": "https://learn.microsoft.com/aspnet/core/what-is-new/"},
                {"label": "RFC 9457 — Problem Details for HTTP APIs", "url": "https://www.rfc-editor.org/rfc/rfc9457"},
            ]},
        ],
    },
]
