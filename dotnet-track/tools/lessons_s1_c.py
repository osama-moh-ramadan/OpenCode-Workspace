"""Stage 1, Module 2 — Testing (lessons 1-3 of 6)."""

TODAY = "2026-10-22"

LESSONS_S1_C = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s1-m2-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
أكتر غلطتين في الاختبارات: **(1)** كتابة 300 اختبار Unit كلها بتعيد اختبار الـframework، و**(2)** مفيش ولا اختبار
Integration واحد — فأول باج حقيقي يظهر بعد النشر. الاختبارات مش «عدد»، دي **توزيع مخاطر**: كل مستوى بيجاوب
على سؤال مختلف، وبتكلفة مختلفة.

في الدرس ده هنبني الخريطة: إيه اللي يُختبر فين، إزاي توزّع مجهودك على مشروع .NET حقيقي، وإمتى الاختبار
بيبقى **كاذب** (ناجح دايمًا ومش بيكشف حاجة).
"""},
            {"type": "terms", "title": "مصطلحات الدرس", "items": [
                {"term": "Unit test", "def": "بيختبر وحدة واحدة (دالة/كلاس) بمعزل عن التبعيات — ملي ثانية، وآلاف منه مقبول."},
                {"term": "Integration test", "def": "بيختبر تعاون مكونات حقيقية معًا (HTTP pipeline + EF + قاعدة بيانات) — ثواني، وعشرات منه كافية."},
                {"term": "Contract test", "def": "بيأكد إن مزوّد الخدمة والمستهلك متفقين على الشكل — مهم بين الميكروسيرفيسز."},
                {"term": "E2E test", "def": "سيناريو كامل من الواجهة لقاعدة البيانات — بطيء وهش، استخدمه لأهم 3-5 مسارات فقط."},
                {"term": "Determinism", "def": "نفس المدخلات → نفس النتيجة دائمًا. أي اعتماد على الوقت/الشبكة/الترتيب = اختبار flaky."},
                {"term": "Test doubles", "def": "بدائل التبعيات: Fake (تنفيذ مبسّط حقيقي)، Stub (قيم جاهزة)، Spy/Mock (يراقب التفاعل)."},
            ]},
            {"type": "table", "head": ["المستوى", "بياكد إيه", "السرعة", "التكلفة", "مثال في مشروع .NET", "العدد المعقول"], "rows": [
                ["Unit", "منطق العمل والقواعد", "ملي ثانية", "منخفضة", "حساب إجمالي الطلب، سياسة الضريبة، validator", "70-80% من الاختبارات"],
                ["Integration", "التعاون الحقيقي + العقد", "ثواني", "متوسطة", "`POST /api/orders` بـWebApplicationFactory + Postgres حقيقي", "15-25%"],
                ["Contract", "توافق الخدمات", "ثواني", "متوسطة", "مستهلك RabbitMQ يتفق مع شكل الحدث المنشور", "لكل حد بين خدمتين"],
                ["E2E", "تجربة المستخدم الكاملة", "دقائق", "عالية", "سيناريو Playwright: تسجيل → طلب → دفع", "3-5 مسارات حرجة"],
            ], "caption": "التوزيع ده تقريبي — المهم إن كل مستوى موجود، مش النسبة نفسها."},
            {"type": "heading", "level": 2, "text": "نفس القاعدة تُختبر في مستويين مختلفين"},
            {"type": "code", "lang": "csharp", "filename": "Unit: OrderTests.cs", "title": "Unit — منطق الـDomain بمعزل عن كل حاجة", "code": r'''
public sealed class OrderTotalTests
{
    [Theory]
    [InlineData("EG", 200, 228)]     // 14% VAT
    [InlineData("SA", 200, 230)]     // 15% VAT
    [InlineData("US", 200, 200)]     // لا ضريبة
    public void ApplyTax_uses_country_policy(string country, decimal subTotal, decimal expected)
    {
        var order = AnOrder.WithCountry(country).WithLines(1, subTotal);

        order.ApplyTax(TaxPolicyResolver.Resolve(country));

        order.Total.Should().Be(expected);
    }

    [Fact]
    public void Cancelled_order_cannot_be_modified()
    {
        var order = AnOrder.Cancelled();

        var act = () => order.AddLine(new OrderLine(Guid.NewGuid(), 1, 10m));

        act.Should().Throw<OrderAlreadyCancelledException>();
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Integration: OrdersApiTests.cs", "title": "Integration — نفس القاعدة عبر الـpipeline الحقيقي", "code": r'''
public sealed class OrdersApiTests(CustomWebApplicationFactory factory)
    : IClassFixture<CustomWebApplicationFactory>
{
    [Fact]
    public async Task Create_order_returns_201_and_persists_it()
    {
        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/orders", new
        {
            customerId = factory.SeededCustomer.Id,
            lines = new[] { new { productId = factory.SeededProduct.Id, quantity = 2, unitPrice = 100m } },
        });

        response.StatusCode.Should().Be(HttpStatusCode.Created);

        var created = await response.Content.ReadFromJsonAsync<OrderCreatedResponse>();
        created!.Id.Should().NotBeEmpty();

        // التحقق من الأثر الحقيقي — مش من الاستجابة فقط
        var stored = await factory.GetOrderAsync(created.Id);
        stored.Total.Should().Be(228m);
        stored.Lines.Should().HaveCount(1);
    }

    [Fact]
    public async Task Create_order_with_zero_quantity_returns_400_problem_json()
    {
        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/orders", new
        {
            customerId = factory.SeededCustomer.Id,
            lines = new[] { new { productId = factory.SeededProduct.Id, quantity = 0, unitPrice = 100m } },
        });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/problem+json");

        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemDetails>();
        problem!.Errors.Keys.Should().Contain(k => k.Contains("Quantity"));
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "اختبارات كاذبة — أخطر من مفيش اختبارات",
             "md": """
- **`InMemory` provider بدل قاعدة حقيقية**: بيختلف عن SQL Server/Postgres في الـtransactions، والـraw SQL،
  والـconstraints، والـclient-evaluation. اختبارك هينجح والإنتاج هيفشل.
- **Mock لكل حاجة بما فيها الكلاس المُختبَر نفسه**: بتختبر إعدادات الـmock مش الكود.
- **Assertion على رسالة اللوج أو على ترتيب نداءات داخلية**: أي refactor بريء يكسره (brittle).
- **اختبار بلا assert**: بينفّذ الكود بس — التغطية بتزيد والثقة صفر.
- **Ice-cream cone**: 500 اختبار E2E و20 Unit — بطء، هشاشة، وتكلفة تشغيل عالية.
"""},
            {"type": "steps", "title": "إزاي توزّع مجهودك على مشروعك (خطة 5 خطوات)", "items": [
                {"title": "ابدأ من المخاطر مش من الملفات",
                 "md": "اكتب قائمة بـ5 قواعد عمل لو اتكسرت هتكلّف فلوس/ثقة (ضريبة، خصم، منع تجاوز المخزون، صلاحيات، حساب الفاتورة). دي أول ما يُختبر Unit."},
                {"title": "غطّ كل endpoint باختبار Integration واحد على الأقل",
                 "md": "مسار نجاح + مسار فشل لكل endpoint عام. ده بيختبر routing وauth وvalidation وserialization وEF دفعة واحدة."},
                {"title": "اعزل الاختبارات البطيئة بـTraits",
                 "md": "`[Trait(\"Category\",\"Integration\")]` وشغّل الـUnit في كل commit والـIntegration في كل PR — سرعة استجابة في التطوير وأمان قبل الدمج."},
                {"title": "ثبّت الحدود بين الخدمات بـContract tests",
                 "md": "لو فيه رسالة/حدث بين خدمتين، اختبر شكله من الطرفين. أرخص بكتير من اكتشاف الكسر في الإنتاج."},
                {"title": "قِس واحذف",
                 "md": "شوف التغطية **على الـDomain** (مش المشروع كله)، واحذف أي اختبار مش بيكشف عطل حقيقي. الاختبار السيئ له تكلفة صيانة دائمة."},
            ]},
            {"type": "callout", "kind": "tip", "title": "قاعدة عملية للاختيار",
             "md": """
اسأل: **«لو غيّرت تنفيذ التفاصيل دي، الاختبار ده لازم يفشل؟»**
لو الإجابة لأ → الاختبار بيقيّد التصميم من غير فايدة (احذفه أو أعد كتابته على السلوك).
ولو السلوك اللي بتختبره ممكن يتكسر بتغيير في قاعدة البيانات → مكانه Integration مش Unit.
"""},
            {"type": "checkpoints", "items": [
                "أصنّف أي اختبار عندي على المستوى الصحيح وأبرر السبب.",
                "أحدّد المخاطر الخمس الأهم في مشروعي وأتأكد إنها مغطاة Unit.",
                "أكتب اختبار Integration لكل endpoint يغطي نجاح وفشل.",
                "أكتشف الاختبار الكاذب/الهش وأعيد كتابته على السلوك.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "قاعدتك «لا يمكن إلغاء طلب تم شحنه». أنهي توزيع اختبار صحيح؟",
                 "options": [
                     "اختبار Unit على الكيان + اختبار Integration على endpoint الإلغاء",
                     "اختبار E2E بـPlaywright فقط",
                     "50 اختبار Unit يغطوا كل فروع الكود",
                     "مفيش اختبار — القاعدة واضحة في الكود",
                 ], "answer": 0,
                 "explain": "القاعدة نفسها Unit (سريعة وشاملة للحالات)، وطريقها عبر الـAPI Integration (بيأكد إن الحد بيستخدم القاعدة فعلًا وإن الرد 409)."},
                {"q": "ليه `InMemory` provider في اختبار EF Core خطر؟",
                 "options": [
                     "بطيء",
                     "بيتصرف differently عن مزوّد SQL حقيقي (transactions/constraints/raw SQL) فبيدي ثقة كاذبة",
                     "مش مدعوم من Microsoft",
                     "محتاج Docker",
                 ], "answer": 1,
                 "explain": "الاختبار بيعدي والإنتاج بيفشل. البديل: SQLite في ملف/ذاكرة بحذر، أو الأفضل Testcontainers بقاعدة حقيقية."},
                {"q": "أي تغيير يحوّل الاختبار لـ«هش» (brittle)؟",
                 "options": [
                     "التحقق من إن `POST /api/orders` بيرجع 201 والطلب اتخزن",
                     "التحقق من إن `_store.SaveAsync` اتنادت مرة بالظبط بترتيب محدد",
                     "التحقق من إن إجمالي الطلب = 228",
                     "التحقق من إن الاستجابة 400 فيها خطأ على Quantity",
                 ], "answer": 1,
                 "explain": "التحقق من تفاعل داخلي (مين نده مين وبأي ترتيب) بيكسر مع أي refactor بريء. اختبر الأثر/السلوك الظاهر."},
                {"q": "عندك 20 دقيقة تضيف فيها اختبارات لمشروع مفيهوش أي اختبار. تبدأ بإيه؟",
                 "options": [
                     "اختبارات E2E لأهم 3 سيناريوهات",
                     "Unit لأهم قاعدة عمل + Integration لمسار نجاح واحد على أهم endpoint",
                     "تغطية 100% للـControllers",
                     "اختبارات للـDTOs والـmappers",
                 ], "answer": 1,
                 "explain": "أعلى عائد/دقيقة: قاعدة عمل حرجة + مسار حقيقي واحد يثبت إن الـpipeline شغال. الباقي يتبني تدريجيًا."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "خريطة اختبار لمشروعك",
                 "md": "اكتب جدول من 3 أعمدة: (1) أهم 5 قواعد عمل عندك، (2) المستوى المناسب لكل واحدة، (3) هل مغطاة حاليًا؟ وبعدين اكتب الاختبارات الناقصة للأولوية الأولى.",
                 "criteria": [
                     "5 قواعد عمل محددة بالاسم (مش «الـCRUD»)",
                     "لكل قاعدة مستوى مبرر (Unit/Integration/Contract)",
                     "3 اختبارات جديدة مكتوبة وناجحة على الأقل",
                     "كل اختبار جديد بيكشف عطل حقيقي (جرّب تكسر الكود وتأكد إنه fail)",
                 ],
                 "hint": "اختبار ما بيفشلش لما تكسر الكود = اختبار بلا قيمة. ده أهم فحص جودة للاختبارات نفسها."},
                {"id": "t2", "title": "تصنيف ما هو موجود",
                 "md": "لو عندك اختبارات بالفعل: صنّفها (Unit/Integration/E2E) واحسب النسب، وحدد أيها هش وأيها كاذب، واحذف أو أعد كتابة أسوأ 3.",
                 "criteria": [
                     "جدول بالنسب الحالية مقابل الهدف",
                     "قائمة بالاختبارات الهشة مع سبب الهشاشة",
                     "حذف/إعادة كتابة 3 اختبارات على الأقل",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Testing in .NET (Microsoft Learn)", "url": "https://learn.microsoft.com/dotnet/core/testing/"},
                {"label": "Integration tests in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/test/integration-tests"},
                {"label": "EF Core testing providers", "url": "https://learn.microsoft.com/ef/core/testing/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s1-m2-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
**xUnit** هو الاختيار الافتراضي في سوق .NET (ومعظم مشاريع Microsoft نفسها بتستخدمه). ومن **xUnit v3** بقى
مبنيًا على **Microsoft.Testing.Platform (MTP)** — runner جديد بيحل محل VSTest، أسرع في الـCI، وبيسمح إن مشروع
الاختبارات نفسه يتبني كـ**executable** تشتغله مباشرة.

الدرس ده عملي: مشروع اختبارات منظم، `Fact` مقابل `Theory`، مشاركة الإعداد بالـ**fixtures**، تصنيف
الاختبارات بـ**Traits**، وإعدادات التشغيل في `xunit.runner.json` — وبعدين تشغيل كل ده في CI.
"""},
            {"type": "terms", "items": [
                {"term": "[Fact]", "def": "اختبار بلا مدخلات: حالة واحدة ثابتة."},
                {"term": "[Theory]", "def": "اختبار بمجموعة حالات: `InlineData` / `MemberData` / `ClassData` — كل حالة بتظهر كنتيجة مستقلة."},
                {"term": "IClassFixture<T>", "def": "إعداد مشترك يُنشأ مرة واحدة لكل كلاس اختبار (مثال: قاعدة بيانات) ويُتخلص منه في النهاية."},
                {"term": "ICollectionFixture<T>", "def": "نفس الفكرة لكن على مستوى collection — مشاركة أوسع مع تحكم في التوازي."},
                {"term": "Trait", "def": "وسم للاختبار (`Category=Integration`) تستخدمه في الفلترة بـ`dotnet test --filter`."},
                {"term": "Microsoft.Testing.Platform", "def": "runner الجديد (بديل VSTest): أسرع، قابل للتوسيع، ومشروع الاختبار بيبقى تطبيق قائم بذاته."},
                {"term": "xunit.runner.json", "def": "ملف إعدادات التشغيل: التوازي، عدد الـthreads، شكل أسماء الاختبارات، وshadow copy."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "إنشاء مشروع الاختبارات وربطه", "code": r'''
# مشروع اختبارات xUnit (القالب الحالي في .NET 10 SDK)
dotnet new xunit -n Shop.Tests
dotnet sln Shop.sln add Shop.Tests

# ربط المشروعات تحت الاختبار
dotnet add Shop.Tests reference Shop.Domain Shop.Api Shop.Infrastructure

# الحزم الأساسية
dotnet add Shop.Tests package xunit.v3                       # xUnit v3 (MTP)
dotnet add Shop.Tests package NSubstitute                    # doubles
dotnet add Shop.Tests package Shouldly                       # assertions (بديل مفتوح)
dotnet add Shop.Tests package coverlet.collector             # التغطية
dotnet add Shop.Tests package Microsoft.AspNetCore.Mvc.Testing   # WebApplicationFactory

# تشغيل
dotnet test Shop.Tests
dotnet test Shop.Tests --filter "Category=Unit"
dotnet test Shop.Tests --logger "console;verbosity=detailed"
dotnet test Shop.Tests --collect:"XPlat Code Coverage"
'''},
            {"type": "callout", "kind": "note", "title": "ملاحظة على مكتبات الـassertions",
             "md": """
`FluentAssertions` من الإصدار 8 بقى بترخيص تجاري للشركات، فكتير من الفرق انتقلت لبدائل مفتوحة:
**`Shouldly`** (أسلوب `x.ShouldBe(5)`) أو **AwesomeAssertions** (fork مجتمعي بنفس أسلوب `.Should()`).
أمثلة الدرس بتستخدم أسلوب `.Should()` — لو اخترت Shouldly، الاستبدال ميكانيكي:
`result.IsValid.Should().BeFalse()` ← `result.IsValid.ShouldBeFalse()`.
المهم: **مكتبة واحدة في المشروع كله** عشان رسائل الفشل تفضل متسقة.
"""},
            {"type": "heading", "level": 2, "text": "Fact وTheory: حالات مش نسخ"},
            {"type": "code", "lang": "csharp", "filename": "Domain/TaxPolicyTests.cs", "title": "InlineData / MemberData / ClassData", "code": r'''
public sealed class TaxPolicyTests
{
    [Fact]
    public void Egypt_applies_14_percent_vat()
    {
        var order = AnOrder.WithSubTotal(100m).WithCountry("EG");

        order.ApplyTax(new EgyptTaxPolicy());

        order.Total.Should().Be(114m);
    }

    [Theory]
    [InlineData("EG", 100, 114)]
    [InlineData("SA", 100, 115)]
    [InlineData("AE", 100, 105)]
    [InlineData("US", 100, 100)]
    public void Tax_by_country(string country, decimal subTotal, decimal expected)
    {
        var order = AnOrder.WithSubTotal(subTotal).WithCountry(country);

        order.ApplyTax(TaxPolicyResolver.Resolve(country));

        order.Total.Should().Be(expected);
    }

    // حالات معقّدة: MemberData بترجع IEnumerable<object[]>
    public static TheoryData<string, decimal[]> DiscountMatrix => new()
    {
        { "GOLD_1Y",   [200m, 170m] },     // 15%
        { "SILVER",    [200m, 186m] },     // 7%
        { "NONE",      [200m, 200m] },
    };

    [Theory]
    [MemberData(nameof(DiscountMatrix))]
    public void Discount_tiers(string tier, decimal[] amounts)
    {
        var order = AnOrder.WithTier(tier).WithSubTotal(amounts[0]);

        order.ApplyDiscount();

        order.Total.Should().Be(amounts[1]);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "Fixtures: إعداد ثقيل مرة واحدة"},
            {"type": "code", "lang": "csharp", "filename": "Infrastructure/DatabaseFixture.cs", "title": "IAsyncLifetime + fixture مشترك للكلاس", "code": r'''
public sealed class DatabaseFixture : IAsyncLifetime
{
    private NpgsqlDataSource? _dataSource;

    public string ConnectionString { get; private set; } = "";

    public async ValueTask InitializeAsync()
    {
        // في الواقع: Testcontainers (الدرس الجاي). هنا الشكل العام.
        var container = new PostgreSqlBuilder()
            .WithImage("postgres:17-alpine")
            .WithDatabase("shop_tests")
            .Build();
        await container.StartAsync();

        ConnectionString = container.GetConnectionString();
        _dataSource = NpgsqlDataSource.Create(ConnectionString);
        await using var db = new AppDbContext(new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql(ConnectionString).Options);
        await db.Database.MigrateAsync();          // ✓ نفس مسار الإنتاج
    }

    public async ValueTask DisposeAsync()
    {
        if (_dataSource is not null) await _dataSource.DisposeAsync();
    }

    /// <summary>سياق جديد لكل استخدام — الاختبارات ما تشاركش DbContext.</summary>
    public AppDbContext CreateContext() =>
        new(new DbContextOptionsBuilder<AppDbContext>().UseNpgsql(ConnectionString).Options);
}

public sealed class OrderPersistenceTests(DatabaseFixture db) : IClassFixture<DatabaseFixture>
{
    [Fact]
    public async Task Saved_order_can_be_read_back()
    {
        var id = Guid.NewGuid();
        await using (var ctx = db.CreateContext())
        {
            ctx.Orders.Add(AnOrder.WithId(id).WithTotal(228m).Build());
            await ctx.SaveChangesAsync();
        }

        await using var verify = db.CreateContext();
        var loaded = await verify.Orders.SingleAsync(o => o.Id == id);

        loaded.Total.Should().Be(228m);
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "قواعد الـfixtures",
             "md": """
- الـfixture بيتشارك **الحالة** — فالاختبارات اللي بتستخدمه لازم تكون مستقلة البيانات (معرّفات فريدة لكل اختبار).
- xUnit بيشغّل الاختبارات **داخل الكلاس الواحد بالتسلسل**، لكن الكلاسات المختلفة **بالتوازي**. fixture مشارك بين
  كلاسات (CollectionFixture) + توازي = تعارض. استخدم `[Collection("Database")]` لضبط التوازي.
- **ما تشاركش `DbContext` بين اختبارين** — التغييرات المتتبعة هتتلوث. اعمل context جديد لكل عملية.
"""},
            {"type": "heading", "level": 2, "text": "التصنيف والفلترة والتوازي"},
            {"type": "code", "lang": "csharp", "filename": "Traits.cs", "title": "وسوم ثابتة بدل السلاسل المكتوبة بإيدك", "code": r'''
public static class Categories
{
    public const string Unit = "Unit";
    public const string Integration = "Integration";
    public const string Slow = "Slow";
}

[Trait("Category", Categories.Unit)]
public sealed class OrderTotalTests { /* ... */ }

[Trait("Category", Categories.Integration)]
[Trait("Category", Categories.Slow)]
public sealed class OrdersApiTests(CustomWebApplicationFactory f) : IClassFixture<CustomWebApplicationFactory> { /* ... */ }

// تجميع الكلاسات اللي بتشارك fixture + إلغاء التوازي بينها
[CollectionDefinition("Database", DisableParallelization = true)]
public sealed class DatabaseCollection : ICollectionFixture<DatabaseFixture>;

[Collection("Database")]
public sealed class OrderPersistenceTests { /* ... */ }
'''},
            {"type": "code", "lang": "json", "filename": "Shop.Tests/xunit.runner.json", "title": "إعدادات التشغيل (انسخه لمجلد الإخراج)", "code": r'''
{
  "$schema": "https://xunit.net/schema/current/xunit.runner.schema.json",
  "parallelizeAssembly": false,
  "parallelizeTestCollections": true,
  "maxParallelThreads": 4,
  "methodDisplay": "method",
  "methodDisplayOptions": "replaceUnderscoreWithSpace",
  "diagnosticMessages": false,
  "shadowCopy": false
}
'''},
            {"type": "code", "lang": "xml", "filename": "Shop.Tests/Shop.Tests.csproj", "title": "نسخ ملف الإعداد + تفعيل MTP", "code": r'''
<ItemGroup>
  <None Update="xunit.runner.json" CopyToOutputDirectory="PreserveNewest" />
</ItemGroup>

<!-- xUnit v3 بيشتغل على Microsoft.Testing.Platform.
     لما تفعّل وضع MTP، مشروع الاختبارات بيتبني كتطبيق مستقل تشتغله مباشرة
     (أسرع في الـCI من طبقة dotnet test). راجع التوثيق للتفاصيل والضبط. -->
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <Nullable>enable</Nullable>
  <ImplicitUsings>enable</ImplicitUsings>
  <IsPackable>false</IsPackable>
</PropertyGroup>
'''},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الفلترة في التطوير والـCI", "code": r'''
# سريع أثناء التطوير: Unit فقط
dotnet test --filter "Category=Unit"

# قبل الدمج: كل حاجة
dotnet test

# استبعاد البطيء مؤقتًا
dotnet test --filter "Category!=Slow"

# فلترة بالاسم
dotnet test --filter "FullyQualifiedName~OrdersApiTests"

# إعادة تشغيل الفاشل فقط (xUnit v3 / MTP)
dotnet test -- --report-trx
'''},
            {"type": "code", "lang": "yaml", "filename": ".github/workflows/ci.yml", "title": "تشغيل الاختبارات في CI مع تغطية", "code": r'''
name: ci
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'

      - name: Restore
        run: dotnet restore

      - name: Build (warnings as errors)
        run: dotnet build --no-restore -warnaserror

      - name: Unit tests (fast)
        run: dotnet test --no-build --filter "Category=Unit"

      - name: Integration tests
        run: dotnet test --no-build --filter "Category=Integration" --collect:"XPlat Code Coverage"

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: '**/coverage.cobertura.xml'
'''},
            {"type": "table", "head": ["الاحتياج", "الأداة", "ملاحظة"], "rows": [
                ["اختبار حالة واحدة", "`[Fact]`", "بلا مدخلات"],
                ["اختبار عدة حالات", "`[Theory]` + `InlineData`", "كل حالة نتيجة مستقلة في التقرير"],
                ["حالات معقدة/مولّدة", "`MemberData`/`ClassData`", "`TheoryData<T>` أقوى أنواعًا"],
                ["إعداد ثقيل مشترك", "`IClassFixture<T>`", "مرة واحدة لكل كلاس"],
                ["مشاركة أوسع + تحكم توازي", "`ICollectionFixture<T>` + `[Collection]`", "`DisableParallelization` عند اللزوم"],
                ["إعداد لكل اختبار", "`IAsyncLifetime` على الكلاس نفسه", "أبطأ لكن معزول تمامًا"],
                ["فلترة في CI", "`[Trait]` + `--filter`", "وسوم ثابتة في كلاس `Categories`"],
            ]},
            {"type": "checkpoints", "items": [
                "أنشئ مشروع اختبارات xUnit v3 مرتبط بالمشروعات الصحيحة والحزم المطلوبة.",
                "أحوّل الاختبارات المكررة إلى `[Theory]` بحالات واضحة.",
                "أستخدم fixtures للإعداد الثقيل مع الحفاظ على استقلالية البيانات.",
                "أصنّف الاختبارات بـTraits وأشغّل الفئات المختلفة في أوقات مختلفة (محليًا وفي CI).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "عندك 6 حالات لسعر الشحن حسب المنطقة. أفضل كتابة؟",
                 "options": [
                     "6 دوال `[Fact]` بأسماء مختلفة",
                     "`[Theory]` واحدة بـ6 `InlineData`",
                     "حلقة `foreach` جوه `[Fact]` واحد",
                     "اختبار واحد بأول حالة بس",
                 ], "answer": 1,
                 "explain": "`[Theory]` بتظهر كل حالة كنتيجة مستقلة في التقرير (فشل حالة ما يخفيش الباقي)، وبتقلل التكرار. الـforeach جوه Fact بتفشل الكل عند أول حالة."},
                {"q": "إيه الفرق الجوهري بين `IClassFixture` و`IAsyncLifetime` على كلاس الاختبار؟",
                 "options": [
                     "لا فرق",
                     "الـfixture يُنشأ مرة للكلاس كله، و`IAsyncLifetime` على الكلاس بيشتغل قبل/بعد كل اختبار",
                     "الـfixture أبطأ",
                     "`IAsyncLifetime` للتوازي فقط",
                 ], "answer": 1,
                 "explain": "الـfixture = إعداد مشترك مرة واحدة (أرخص). `IAsyncLifetime` على كلاس الاختبار نفسه = إعداد/تنظيف لكل اختبار (أعزل وأغلى). (ملاحظة: الـfixture نفسه ممكن ينفّذ IAsyncLifetime لبدء/إنهاء غير متزامن.)"},
                {"q": "كلاسات اختبارات مختلفة بتشارك قاعدة بيانات واحدة والاختبارات بتفشل عشوائيًا. السبب الأرجح؟",
                 "options": [
                     "xUnit مش بيدعم التوازي",
                     "التوازي بين الكلاسات + بيانات غير معزولة → تعارض",
                     "قاعدة البيانات بطيئة",
                     "الـfixtures مش شغالة",
                 ], "answer": 1,
                 "explain": "xUnit بيشغّل collections بالتوازي. الحل: `[CollectionDefinition(..., DisableParallelization = true)]` أو عزل البيانات بمعرّفات فريدة لكل اختبار."},
                {"q": "عايز تشغّل الاختبارات السريعة في كل commit والبطيئة قبل الدمج. تستخدم إيه؟",
                 "options": [
                     "مشروعين اختبار منفصلين دائمًا",
                     "`[Trait(\"Category\", ...)]` + `dotnet test --filter`",
                     "تعطيل التوازي",
                     "`xunit.runner.json` بـ`parallelizeAssembly:false`",
                 ], "answer": 1,
                 "explain": "التصنيف بـTraits هو الأداة المصممة للفلترة الانتقائية، محليًا وفي الـCI."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "بنية اختبارات نظيفة",
                 "md": "أنشئ مشروع `Shop.Tests` (أو في مشروعك) بالحزم المذكورة، وحوّل 3 اختبارات مكررة إلى `[Theory]`، وأضف fixture واحدًا لإعداد مشترك، وصنّف كل الاختبارات بـ`Category`.",
                 "criteria": [
                     "`dotnet test --filter \"Category=Unit\"` يشغّل مجموعة فرعية فعلًا",
                     "فيه `[Theory]` واحدة بـ3 حالات على الأقل",
                     "فيه fixture واحد (`IClassFixture` أو `ICollectionFixture`) مستخدم في اختبارين على الأقل",
                     "`xunit.runner.json` منسوخ لمجلد الإخراج",
                     "ملف CI يشغّل Unit ثم Integration كخطوتين",
                 ],
                 "hint": "لو `--filter` ما أثرش، تأكد إن الـ`[Trait]` على مستوى الكلاس أو الدالة (مش جوه الـfixture) وإن الاسم مطابق حرفيًا."},
                {"id": "t2", "title": "اجعل الفشل مقروءًا",
                 "md": "شغّل `dotnet test --logger \"console;verbosity=detailed\"` بعد كسر متعمد في الكود، وحسّن أسماء الاختبارات ورسائل الـassertions لحد ما تعرف سبب الفشل من الرسالة وحدها.",
                 "criteria": [
                     "أسماء الاختبارات تصف السلوك (مش `Test1`)",
                     "رسالة الفشل توضح المتوقع مقابل الفعلي",
                     "وثّقت في ملاحظاتك قاعدة تسمية فريقك",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "xUnit.net", "url": "https://xunit.net/"},
                {"label": "Microsoft.Testing.Platform", "url": "https://learn.microsoft.com/dotnet/core/testing/unit-testing-platform"},
                {"label": "Unit testing in .NET", "url": "https://learn.microsoft.com/dotnet/core/testing/unit-testing-best-practices"},
                {"label": "Shouldly", "url": "https://docs.shouldly.io/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l3
    {
        "id": "s1-m2-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الـmocking أداة مفيدة وخطيرة: مفيدة لعزل التبعيات الخارجية، وخطيرة لأنها بتسهّل إنك تكتب اختبارات
بتؤكد على **تفاصيل التنفيذ** بدل السلوك — فتنكسر مع كل refactor وتديك ثقة وهمية.

القاعدة اللي هنمشي عليها: **Fake > Stub > Mock**. لو تقدر تكتب تنفيذ مبسّط حقيقي (Fake)، اعمله.
استخدم الـsubstitute للتحقق من تفاعل **مهم فعلًا** (إرسال إشعار، استدعاء بوابة دفع) — مش لكل تبعية.
"""},
            {"type": "terms", "items": [
                {"term": "SUT", "def": "System Under Test — الكائن اللي بتختبره. كل ما زادت تبعياته، صعب الاختبار."},
                {"term": "Dummy", "def": "مُمرَّر عشان الإمضاء يتحقق بس — مش بيُستخدم."},
                {"term": "Stub", "def": "بيرجع قيم محددة مسبقًا (state). مثال: `clock` بيرجع تاريخ ثابت."},
                {"term": "Spy / Mock", "def": "بيسجّل كيف اتُستخدم (interaction). مثال: التأكد إن `notifier.NotifyAsync` اتنادت مرة."},
                {"term": "Fake", "def": "تنفيذ مبسّط لكنه حقيقي السلوك. مثال: `InMemoryOrderStore` بقائمة. **الأفضل للاختبار**."},
                {"term": "AAA", "def": "Arrange / Act / Assert — بنية اختبار مقروءة: إعداد، تنفيذ، تأكيد (وفراغ بين كل جزء)."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Tests package NSubstitute
# اختياري: توليد doubles تلقائيًا مع AutoFixture
dotnet add Shop.Tests package AutoFixture
dotnet add Shop.Tests package AutoFixture.AutoNSubstitute
'''},
            {"type": "heading", "level": 2, "text": "الأولوية الأولى: Fake بدل Mock"},
            {"type": "code", "lang": "csharp", "filename": "Testing/Fakes.cs", "title": "fakes صغيرة وواضحة — بتختبر سلوك حقيقي", "code": r'''
public sealed class InMemoryOrderStore : IOrderStore
{
    private readonly List<Order> _orders = [];

    public IReadOnlyList<Order> Saved => _orders;
    public int SaveCalls { get; private set; }

    public void Seed(params Order[] orders) => _orders.AddRange(orders);
    public bool FailNextSave { get; set; }          // للتحكم في سيناريو الفشل

    public Task SaveAsync(Order order, CancellationToken ct = default)
    {
        SaveCalls++;
        if (FailNextSave) throw new DbUpdateException("simulated failure");
        _orders.Add(order);
        return Task.CompletedTask;
    }
}

public sealed class RecordingNotifier : IOrderNotifier
{
    public List<Order> Notified { get; } = [];
    public Task NotifyAsync(Order order, CancellationToken ct = default)
    {
        Notified.Add(order);
        return Task.CompletedTask;
    }
}

public sealed class FixedClock(DateTimeOffset now) : TimeProvider
{
    public override DateTimeOffset GetUtcNow() => now;
}

/// <summary>Object Mother: قيم افتراضية سليمة + تعديل ما تحتاجه فقط.</summary>
public static class AnOrder
{
    public static OrderBuilder Default() => new();

    public sealed class OrderBuilder
    {
        private Guid _id = Guid.NewGuid();
        private string _country = "EG";
        private decimal _subTotal = 200m;

        public OrderBuilder WithId(Guid id) { _id = id; return this; }
        public OrderBuilder WithCountry(string c) { _country = c; return this; }
        public OrderBuilder WithSubTotal(decimal v) { _subTotal = v; return this; }
        public Order Build() => new()
        {
            Id = _id,
            Customer = new Customer { Id = Guid.NewGuid(), Country = _country },
            Lines = [new OrderLine(Guid.NewGuid(), 1, _subTotal)],
        };
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "OrderPlacementServiceTests.cs", "title": "اختبار على السلوك باستخدام fakes", "code": r'''
public sealed class OrderPlacementServiceTests
{
    private readonly InMemoryOrderStore _store = new();
    private readonly RecordingNotifier _notifier = new();
    private readonly FixedClock _clock = new(new DateTimeOffset(2026, 1, 15, 10, 0, 0, TimeSpan.Zero));

    private OrderPlacementService CreateSut() =>
        new(_store, _notifier, new EgyptTaxPolicy(), _clock);

    [Fact]
    public async Task Place_saves_order_with_tax_and_notifies_customer()
    {
        var sut = CreateSut();
        var order = AnOrder.Default().WithCountry("EG").WithSubTotal(200m).Build();

        await sut.PlaceAsync(order);

        order.Total.Should().Be(228m);                 // السلوك: الضريبة اتحسبت
        _store.Saved.Should().ContainSingle(o => o.Id == order.Id);
        _notifier.Notified.Should().ContainSingle(o => o.Id == order.Id);
    }

    [Fact]
    public async Task Place_when_store_fails_does_not_notify()
    {
        _store.FailNextSave = true;
        var sut = CreateSut();
        var order = AnOrder.Default().Build();

        await Assert.ThrowsAsync<DbUpdateException>(() => sut.PlaceAsync(order));

        _notifier.Notified.Should().BeEmpty();          // ✓ سلوك مهم: مفيش إشعار لطلب مش محفوظ
    }
}
'''},
            {"type": "heading", "level": 2, "text": "لما تحتاج substitute فعلًا: NSubstitute"},
            {"type": "code", "lang": "csharp", "filename": "PaymentGatewayTests.cs", "title": "الأساسيات: Returns، Arg.Is، Received، الاستثناءات", "code": r'''
using NSubstitute;
using NSubstitute.ExceptionExtensions;

public sealed class PaymentServiceTests
{
    private static readonly Guid orderId = Guid.NewGuid();

    [Fact]
    public async Task Charge_success_marks_order_paid()
    {
        // Arrange
        var gateway = Substitute.For<IPaymentGateway>();
        gateway.ChargeAsync(Arg.Any<ChargeRequest>(), Arg.Any<CancellationToken>())
               .Returns(new ChargeResult(true, "ch_123", 228m));
        var store = new InMemoryOrderStore();
        var sut = new PaymentService(gateway, store, Substitute.For<ILogger<PaymentService>>());

        // Act
        await sut.PayOrderAsync(orderId, 228m);

        // Assert — السلوك أولًا
        var order = store.Saved.Single(o => o.Id == orderId);
        order.Status.Should().Be(OrderStatus.Paid);

        // والتفاعل المهم ثانيًا (المبلغ الصح اتبعت)
        await gateway.Received(1).ChargeAsync(
            Arg.Is<ChargeRequest>(r => r.OrderId == orderId && r.Amount == 228m),
            Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task Charge_failure_leaves_order_unpaid_and_logs()
    {
        var gateway = Substitute.For<IPaymentGateway>();
        gateway.ChargeAsync(Arg.Any<ChargeRequest>(), Arg.Any<CancellationToken>())
               .ThrowsAsync(new PaymentDeclinedException("card_declined"));
        var log = Substitute.For<ILogger<PaymentService>>();
        var store = new InMemoryOrderStore();
        store.Seed(AnOrder.WithId(orderId).Build());
        var sut = new PaymentService(gateway, store, log);

        await sut.PayOrderAsync(orderId, 228m);

        store.Saved.Single().Status.Should().Be(OrderStatus.PaymentFailed);
        log.Received(1).Log(
            LogLevel.Warning,
            Arg.Any<EventId>(),
            Arg.Is<object>(o => o.ToString()!.Contains("card_declined")),
            Arg.Any<Exception>(),
            Arg.Any<Func<object, Exception?, string>>());
    }

    [Fact]
    public async Task Does_not_charge_twice_for_same_order()
    {
        var gateway = Substitute.For<IPaymentGateway>();
        gateway.ChargeAsync(Arg.Any<ChargeRequest>(), Arg.Any<CancellationToken>())
               .Returns(new ChargeResult(true, "ch_1", 228m));
        var sut = new PaymentService(gateway, new InMemoryOrderStore(), Substitute.For<ILogger<PaymentService>>());

        await sut.PayOrderAsync(orderId, 228m);
        await sut.PayOrderAsync(orderId, 228m);          // إعادة (idempotency)

        await gateway.Received(1).ChargeAsync(Arg.Any<ChargeRequest>(), Arg.Any<CancellationToken>());
    }
}
'''},
            {"type": "table", "head": ["الموقف", "استخدم", "مثال NSubstitute"], "rows": [
                ["تحتاج قيم مرجعة ثابتة", "Stub", "`clock.GetUtcNow().Returns(fixedDate)`"],
                ["تحتاج تأكيد إن تفاعل مهم حصل", "Mock/Spy", "`await notifier.Received(1).NotifyAsync(...)`"],
                ["تحتاج تأكيد إنه **ما** حصلش", "Spy", "`await gateway.DidNotReceive().ChargeAsync(...)`"],
                ["تحتاج سلوك حقيقي مبسّط", "Fake", "`InMemoryOrderStore` بقائمة"],
                ["تحتاج محاكاة فشل تبعية", "Stub بيرمي", "`.ThrowsAsync(new TimeoutException())`"],
                ["التبعية معقدة/خارجية (SDK)", "لفّها في interface بتاعك ثم Fake", "`IEmailClient` بدل `SmtpClient`"],
            ]},
            {"type": "callout", "kind": "warn", "title": "حاجات ما تعملهاش",
             "md": """
- **ما تعملش Mock لـ`DbContext`/`DbSet`**: EF معقد داخليًا، والـmock هيكذب. استخدم SQLite أو Testcontainers.
- **ما تعملش Mock لنوع إنت ما تملكه** (SDK خارجي): لفّه في interface بتاعك (Anti-Corruption Layer) واختبر الـwrapper.
- **ما تعملش Mock لـvalue objects/DTOs**: اعملها حقيقية — أرخص وأصدق.
- **ما تتحققش من نداءات داخلية** بين مكونات الكلاس المُختبر: ده بيقفل التصميم.
- **ما تستخدمش `Arg.Any` في كل حاجة**: لما تتحقق من تفاعل، حدد `Arg.Is<T>(x => …)` عشان الاختبار يبقى له معنى.
"""},
            {"type": "heading", "level": 2, "text": "اختبار هش مقابل اختبار صامد"},
            {"type": "code", "lang": "csharp", "title": "قبل / بعد", "code": r'''
// ✗ هش: بيتحقق من تفاصيل التنفيذ — أي refactor يكسره
[Fact]
public async Task Calls_helpers_in_order()
{
    var sut = new OrderService(store, notifier, tax, validator, mapper, logger);
    await sut.PlaceAsync(request);

    Received.InOrder(async () =>
    {
        validator.Validate(request);
        mapper.Map(request);
        tax.Apply(Arg.Any<Order>());
        await store.SaveAsync(Arg.Any<Order>());
        await notifier.NotifyAsync(Arg.Any<Order>());
        logger.LogInfo(Arg.Any<string>());
    });
}

// ✓ صامد: بيتحقق من الأثر — التعديل الداخلي الحر مسموح
[Fact]
public async Task Invalid_request_is_rejected_before_anything_is_saved()
{
    var store = new InMemoryOrderStore();
    var sut = new OrderPlacementService(store, new RecordingNotifier(), new EgyptTaxPolicy());

    var act = () => sut.PlaceAsync(AnOrder.Default().WithSubTotal(-5m).Build());

    await act.Should().ThrowAsync<ValidationException>();
    store.Saved.Should().BeEmpty();
}
'''},
            {"type": "callout", "kind": "tip", "title": "AutoFixture: لما الإعداد نفسه يطول",
             "md": """
`AutoFixture` بيولّد كائنات ببيانات معقولة تلقائيًا، و`AutoNSubstitute` بيملأ التبعيات بـsubstitutes:
```csharp
var fixture = new Fixture().Customize(new AutoNSubstituteCustomization());
var sut = fixture.Create<OrderPlacementService>();     // التبعيات اتحلّت تلقائيًا
var order = fixture.Build<Order>().With(o => o.Total, 0m).Create();
```
مفيد للاختبارات اللي الإعداد فيها بيغطي على الفكرة. **احذر**: لو الكائنات المولّدة غامضة،
الاختبار بقى صعب القراءة — للـDomain الحساس استخدم builders صريحة زي `AnOrder`.
"""},
            {"type": "checkpoints", "items": [
                "أفرّق بين Fake وStub وMock وأختار الأنسب لكل تبعية.",
                "أكتب fakes صغيرة قابلة لإعادة الاستخدام في كل الاختبارات.",
                "أستخدم NSubstitute للتحقق من تفاعل مهم فقط، مع `Arg.Is` محددة.",
                "أتجنب الـMocking لـDbContext وللأنواع الخارجية وأميّز الاختبار الهش.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "عندك `TimeProvider` في خدمة بت حساب تاريخ الاستحقاق. أفضل بديل في الاختبار؟",
                 "options": [
                     "Mock بـNSubstitute مع `Received()`",
                     "Fake/Stub: `FixedClock` يرجع تاريخًا ثابتًا",
                     "`DateTime.UtcNow` مع تسامح ±2 ثانية",
                     "تعطيل الاختبار وقت نهاية اليوم",
                 ], "answer": 1,
                 "explain": "تاريخ ثابت = اختبار deterministic. التسامح الزمني مصدر flakiness كلاسيكي، والـMock هنا مبالغة لأن المطلوب قيمة مش تفاعل."},
                {"q": "ليه ما تعملش `Substitute.For<DbSet<Order>>()`؟",
                 "options": [
                     "DbSet sealed",
                     "سلوك EF الداخلي (tracking/translation/transactions) معقد والـmock هيدي نتائج كاذبة",
                     "NSubstitute لا يدعم async",
                     "أداء سيئ",
                 ], "answer": 1,
                 "explain": "الاختبار هينجح بينما الاستعلام الحقيقي يفشل. استخدم SQLite أو Testcontainers (درس قادم) لاختبارات EF."},
                {"q": "أنهي تأكيد يعتبر «اختبار تفاعل» مشروع؟",
                 "options": [
                     "`await notifier.Received(1).NotifyAsync(Arg.Is<Order>(o => o.Id == id))`",
                     "`mapper.Received(1).Map(request)`",
                     "`logger.Received(3).LogInfo(Arg.Any<string>())`",
                     "`service.Received(1).PrivateHelper()`",
                 ], "answer": 0,
                 "explain": "إرسال الإشعار أثر خارجي له قيمة عمل (والعدد مهم: إشعار مكرر = باج). التفاصيل الداخلية (mapper/logger بعدد) بتقفل التصميم."},
                {"q": "خدمة بتستخدم SDK خارجي (مثال: مكتبة بوابة دفع). إزاي تختبرها؟",
                 "options": [
                     "Mock الـSDK مباشرة",
                     "لفّه في interface بتاعك (Anti-Corruption Layer) واختبر كودك مع Fake له",
                     "ما تختبرهاش — مسؤولية المزوّد",
                     "اختبار E2E فقط",
                 ], "answer": 1,
                 "explain": "الـwrapper بيحميك من تغييرات المزوّد وبيديك نقطة عزل قابلة للاختبار. والقاعدة: «ما تعملش mock لحاجة إنت ما تملكهاش»."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "طقم Fakes لمشروعك",
                 "md": "اكتب Fakes لكل تبعيات خدمة واحدة عندك (store، notifier، clock، logger إن لزم) واستبدل كل الـmocks الحالية بيها في اختبارات الخدمة دي.",
                 "criteria": [
                     "Fake واحد على الأقل بيسمح بمحاكاة الفشل (flag أو queue)",
                     "كل الاختبارات نجحت بدون أي `Substitute.For<DbContext>`",
                     "حجم الكود في كل اختبار قلّ (قِس الأسطر قبل/بعد)",
                     "مفيش تأكيد على ترتيب نداءات داخلية",
                 ],
                 "hint": "لو الـFake كبر عن ~40 سطر، غالبًا الـinterface عام جدًا — قسّمه (ISP)."},
                {"id": "t2", "title": "اختبار idempotency",
                 "md": "اكتب اختبارًا ينفّذ نفس العملية مرتين ويتأكد إن الأثر حصل مرة واحدة (دفع، إشعار، إنشاء مورد) — باستخدام `Received(1)` أو عدّاد في الـFake.",
                 "criteria": [
                     "الاختبار يفشل لو شلت فحص التكرار من الكود",
                     "الاسم يوضح السلوك (`Does_not_charge_twice_for_same_order`)",
                     "وثّقت في الملاحظات مفتاح الـidempotency المستخدم",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "NSubstitute documentation", "url": "https://nsubstitute.github.io/"},
                {"label": "Unit testing best practices (.NET)", "url": "https://learn.microsoft.com/dotnet/core/testing/unit-testing-best-practices"},
                {"label": "AutoFixture", "url": "https://github.com/AutoFixture/AutoFixture"},
                {"label": "Shouldly", "url": "https://docs.shouldly.io/"},
            ]},
        ],
    },
]
