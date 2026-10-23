"""Stage 5, Module 3 — Orchestration with .NET Aspire (lessons 3 & 4)."""

TODAY = "2026-10-22"

LESSONS_S5_G = [
    # ══════════════════════════════════════════════════════════════════
    # s5-m3-l3 — اختبار الأنظمة الموزعة وContract tests
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s5-m3-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
اختبار نظام موزّع مش «نفس اختبارات الوحدة لكن أكثر». فيه **3 أنواع فشل جديدة** ما كانتش موجودة في المونوليث:
1. **العقد اتكسر**: خدمة غيّرت شكل الرد/الحدث فخدمة تانية اتكسرت في الإنتاج (وكل اختباراتها الخضرا).
2. **التفاعل**: كل خدمة صحيحة لوحدها، بس **مع بعض** بيفشلوا (ترتيب، توقيت، timeout، رسالة ضايعة).
3. **البيئة**: الاختبار بيتكلم مع DB/وسيط حقيقي → بطء وعدم استقرار (flakiness).

الحل: **هرم اختبار خاص بالأنظمة الموزعة**، مش الهرم الكلاسيكي بس. الدرس ده بيغطي المستويين الجديدين:
**contract tests** (رخيصة، بتكشف كسر العقد في ثواني) و**اختبارات تكامل عبر النظام** بـAspire
(بتشغّل النظام الحقيقي وتختبر التفاعل). ومعاهم: بيئات ephemeral، وCI، ومحاربة الـflakiness.
"""},
            {"type": "terms", "items": [
                {"term": "Distributed Integration Test", "def": "اختبار يشغّل **النظام الحقيقي** (خدمات + containers) ويتحقق من تفاعلها — في Aspire عبر `DistributedApplicationTestingBuilder`."},
                {"term": "Ephemeral Environment", "def": "بيئة تُبنى عند الطلب وتُهدم بعد الاختبار (containers/موارد مؤقتة) — لا حالة مشتركة بين الاختبارات."},
                {"term": "Consumer-Driven Contract", "def": "**المستهلك** يعلن ما يحتاجه فعلًا من المزود، والمزود بيثبت إنه بيلتزم بيه. العقد من تحت لفوق (مش من التوثيق)."},
                {"term": "Pact File", "def": "ملف JSON يولّده اختبار المستهلك ويصف التفاعلات المتوقعة (طلب/رد) — هو اللي بيتحقق منه المزود."},
                {"term": "Provider State", "def": "حالة البيانات اللي المزود لازم يجهزها قبل تنفيذ تفاعل معيّن («يوجد منتج بمعرّف 42»)."},
                {"term": "Pact Broker", "def": "خادم يخزن العقود ويربطها بإصدارات الخدمات — مصدر الحقيقة لـ«مين يعتمد على إيه»."},
                {"term": "Pending / WIP Pacts", "def": "عقود جديدة ما تكسرش بناء المزود (pending) أو لسه بتتطور (WIP) — بتفصل «العقد اتكسر» عن «البناء احمر من عقد لسه ما اتنفذش»."},
                {"term": "Flaky Test", "def": "اختبار بينجح ويفشل من غير تغيير في الكود. ★ أخطر حاجة في الاختبارات الموزعة: بيقتل الثقة في الأحمر."},
                {"term": "Polling Assertion", "def": "بدل `Task.Delay(3000)`: حلقة بتتحقق من الشرط كل 100ms لحد deadline — أسرع وأقل flakiness."},
                {"term": "Fault Injection", "def": "تعمّد إحداث فشل (إيقاف خدمة، تأخير، رسالة سامة) والتحقق من سلوك النظام — بيثبت إن الـresilience شغال فعلًا."},
            ]},
            {"type": "table", "head": ["المستوى", "بيغطي إيه", "السرعة", "الاعتمادات", "أشهر فشل بيكشفه"], "rows": [
                ["**Unit** (xUnit + NSubstitute)", "منطق Domain/خدمات معزولة", "ملّي ثانية", "ولا حاجة", "خطأ في قاعدة/حساب"],
                ["**Slice** (`WebApplicationFactory` + Respawn)", "مسار HTTP كامل داخل خدمة واحدة (middleware/DI/validation)", "ثانية", "DB اختبار أو container", "تكوين/تسلسل middleware خاطئ"],
                ["**Contract** (Pact)", "توافق عقد بين مستهلك ومزود", "ثواني", "mock server محلي (بلا بيئة)", "★ كسر عقد بعد تغيير في مزود"],
                ["**Distributed integration** (Aspire)", "تفاعل خدمتين+ عبر HTTP/وسيط مع بنية حقيقية", "10–60 ثانية للإقلاع، بعدها ثواني", "Docker + AppHost", "ترتيب إقلاع، timeout، رسائل ضايعة/مكررة"],
                ["**E2E في staging**", "سيناريو مستخدم كامل بعد النشر", "دقائق", "بيئة منشورة", "تكوين/أسرار/شبكة في البيئة الحقيقية"],
                ["**Fault injection / chaos**", "السلوك تحت فشل (إيقاف/تأخير/رسالة سامة)", "دقائق", "بيئة معزولة", "circuit breaker/تعويض/idempotency ما بيشتغلوش"],
                ["**Performance** (k6/BenchmarkDotNet)", "زمن الاستجابة والقدرة الاستيعابية", "دقائق", "بيئة مشابهة للإنتاج", "انحدار p95، تسريب موارد"],
            ]},
            {"type": "callout", "kind": "goal", "title": "قاعدة التوزيع: 70% contract + slice، 25% distributed integration، 5% E2E",
             "md": """
**الهرم الكلاسيكي بينقلب** في الأنظمة الموزعة: اختبارات E2E الكاملة (تشغيل النظام كله لكل حالة) بطيئة وهشّة،
فلو بنيت عليها هتوصل لـCI بياخد 30 دقيقة واختبارات flaky.

**الترتيب الصحيح للاستثمار:**
1. **عقودك مضبوطة** (Pact لكل زوج مستهلك/مزود + لكل حدث في `Shop.Contracts`) → أرخص حماية من الكسر.
2. **شريحة لكل خدمة** (`WebApplicationFactory` + Respawn) → معظم الأخطاء المنطقية/التكوينية.
3. **عدد قليل من اختبارات التكامل الموزعة** (5–15) بتغطي **التدفقات الحرجة** فقط: إنشاء طلب → دفع → إشعار، وفشل كل خطوة.
4. **E2E في staging** بعد النشر (smoke tests): 3–5 سيناريوهات.

⚠ مش معناه إن اختبارات Aspire قليلة القيمة — معناه إن كل اختبار فيها لازم **يغطي تفاعلًا** مش منطقًا
(المنطق مكانه slice/unit).
"""},
            {"type": "heading", "level": 2, "text": "1) اختبار تكامل عبر النظام كله بـAspire"},
            {"type": "code", "lang": "bash", "title": "تجهيز مشروع الاختبار", "code": r'''
# حزمة الاختبار + مرجع للـAppHost نفسه (ده اللي بيولّد نوع Projects.Shop_AppHost)
cd tests/Shop.SystemTests
dotnet add package Aspire.Hosting.Testing
dotnet add package xunit.v3
dotnet add package NSubstitute
dotnet add package Shouldly          # (أو Awesome Assertions — راجع درس 1.4.1: FluentAssertions مدفوعة من v8)
dotnet add reference ../../src/Shop.AppHost/Shop.AppHost.csproj

# ⚠ المتطلبات على جهاز المطور وCI:
#   • Docker شغال ( containers للبنيـة التحتية)
#   • مساحة/ذاكرة كافية — النظام كله بيشتغل داخل عملية الاختبار
#   • ملفّي AppHost (apphost.cs بلا csproj) **لا يمكن** اختباره بالطريقة دي: محتاج ProjectReference
'''},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.SystemTests/ShopAppFixture.cs", "title": "fixture يشغّل النظام مرة ويشاركه بين الاختبارات", "code": r'''
// requires: using Aspire.Hosting; using Aspire.Hosting.Testing; using Microsoft.Extensions.DependencyInjection;

/// <summary>
/// ★ يشغّل النظام الحقيقي (خدمات + containers) **مرة واحدة** لكل مجموعة اختبارات.
/// xUnit v3: `IAsyncLifetime` بيرجع `ValueTask`.
/// </summary>
public sealed class ShopAppFixture : IAsyncLifetime, IAsyncDisposable
{
    private static readonly TimeSpan StartupTimeout = TimeSpan.FromMinutes(5);
    private DistributedApplication? _app;

    public DistributedApplication App =>
        _app ?? throw new InvalidOperationException("التطبيق لم يبدأ — تحقق من InitializeAsync");

    public HttpClient Orders      => App.CreateHttpClient("orders");       // ✓ discovery: بالاسم، بلا منافذ ثابتة
    public HttpClient Catalog     => App.CreateHttpClient("catalog");
    public HttpClient Gateway     => App.CreateHttpClient("gateway");

    public async ValueTask InitializeAsync()
    {
        using var cts = new CancellationTokenSource(StartupTimeout);
        var ct = cts.Token;

        // ✓ وسيطات اختيارية: تعطيل عشوائية المنافذ لو اختبار محتاج منفذ ثابت (نادر)
        var appHost = await DistributedApplicationTestingBuilder
            .CreateAsync<Projects.Shop_AppHost>(ct);
            // .CreateAsync<Projects.Shop_AppHost>(["DcpPublisher:RandomizePorts=false"], ct);

        // الاختبارات بتنادي خدمات حقيقية → خلّي العميل صبورًا ومقاومًا للأخطاء العابرة
        appHost.Services.ConfigureHttpClientDefaults(http =>
        {
            http.AddStandardResilienceHandler();
        });

        // ★ حدود زمنية صريحة: بلا WaitAsync، أي تعليق هيبقى اختبار معلق للأبد
        _app = await appHost.BuildAsync(ct).WaitAsync(StartupTimeout, ct);
        await _app.StartAsync(ct).WaitAsync(StartupTimeout, ct);

        // ✓ انتظر **الصحة** مش مجرد البدء — وإلا أول اختبار هيفشل عشوائيًا
        var notifications = _app.ResourceNotifications;
        await notifications.WaitForResourceHealthyAsync("postgres", ct).WaitAsync(StartupTimeout, ct);
        await notifications.WaitForResourceHealthyAsync("shopdb",   ct).WaitAsync(StartupTimeout, ct);
        await notifications.WaitForResourceHealthyAsync("rabbit",   ct).WaitAsync(StartupTimeout, ct);
        await notifications.WaitForResourceHealthyAsync("catalog",  ct).WaitAsync(StartupTimeout, ct);
        await notifications.WaitForResourceHealthyAsync("orders",   ct).WaitAsync(StartupTimeout, ct);
        await notifications.WaitForResourceHealthyAsync("payments", ct).WaitAsync(StartupTimeout, ct);
    }

    public async ValueTask DisposeAsync()
    {
        if (_app is not null) await _app.DisposeAsync();     // ✓ يوقف العمليات والـcontainers
    }

    // ── مساعدات ──
    /// <summary>connection string لمورد (للتحقق من حالة البيانات مباشرة).</summary>
    public Task<string?> GetConnectionStringAsync(string resourceName) =>
        App.GetConnectionStringAsync(resourceName);          // ✓ تحقق من الاسم في إصدارك (GetConnectionString/…Async)

    // ✓ تحقق من التوقيع في إصدارك: GetEndpoint(name, endpointName) / GetEndpoint(name)
    public Uri Endpoint(string resourceName, string endpointName = "https") =>
        App.GetEndpoint(resourceName, endpointName)
           ?? throw new InvalidOperationException($"endpoint غير موجود: {resourceName}/{endpointName}");
}

// ✓ مشاركة الـfixture بين كل اختبارات التكامل (إقلاع النظام مرة واحدة بس)
[CollectionDefinition("ShopSystem")]
public sealed class ShopSystemCollection : ICollectionFixture<ShopAppFixture> { }

// وفي كل كلاس اختبار:
//   [Collection("ShopSystem")]
//   public class OrderFlowTests(ShopAppFixture app) { … }
'''},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.SystemTests/OrderFlowTests.cs", "title": "3 اختبارات: تدفق HTTP · تدفق أحداث عبر الوسيط · فشل مُفتعل", "code": r'''
// requires: using System.Net.Http.Json; using Npgsql; using Dapper; using System.Net;

[Collection("ShopSystem")]
[Trait("Category", Categories.Integration)]
public class OrderFlowTests(ShopAppFixture app, ITestOutputHelper output)
{
    private static readonly Guid ProductId = Guid.Parse("11111111-1111-1111-1111-111111111111");

    // ═══ 1) تدفق متزامن عبر gateway → orders → catalog (discovery + صحة) ═══
    [Fact]
    public async Task PlaceOrder_through_gateway_succeeds_and_reads_catalog()
    {
        var orderId = Guid.NewGuid();
        var payload = new
        {
            order_id = orderId,
            lines = new[] { new { product_id = ProductId, quantity = 2, unit_price_minor = 1500L } },
        };

        var response = await app.Gateway.PostAsJsonAsync("/api/orders", payload);

        response.StatusCode.ShouldNotBe(HttpStatusCode.BadGateway, "الـgateway لقى orders بالاسم");
        response.StatusCode.ShouldBe(HttpStatusCode.Created);

        // ✓ التحقق من الأثر في قاعدة البيانات الحقيقية (مش من الرد بس)
        var cs = await app.GetConnectionStringAsync("shopdb");
        cs.ShouldNotBeNullOrEmpty();
        await using var conn = new NpgsqlConnection(cs);
        await conn.OpenAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT status FROM orders.orders WHERE id = @id";
        cmd.Parameters.AddWithValue("id", orderId);
        var status = (string?)await cmd.ExecuteScalarAsync();

        status.ShouldBe("Placed");
    }

    // ═══ 2) تدفق أحداث: orders → outbox → RabbitMQ → payments → notifications ═══
    [Fact]
    public async Task PlacedOrder_publishes_event_and_is_consumed_by_payments()
    {
        var orderId = Guid.NewGuid();

        var placed = await app.Orders.PostAsJsonAsync("/api/orders", new
        {
            order_id = orderId,
            lines = new[] { new { product_id = ProductId, quantity = 1, unit_price_minor = 900L } },
        });
        placed.StatusCode.ShouldBe(HttpStatusCode.Created);

        // ★ التدفق غير متزامن → انتظر النتيجة بـpolling بدل Task.Delay ثابت
        var charge = await WaitUntilAsync(
            () => GetChargeAsync(orderId),
            c => c is not null,
            timeout: TimeSpan.FromSeconds(30),
            poll: TimeSpan.FromMilliseconds(200));

        charge.ShouldNotBeNull("المستهلك عالج الحدث خلال 30 ثانية (outbox → rabbit → payments)");
        charge!.Status.ShouldBe("Captured");
        charge.AmountMinor.ShouldBe(900L);
    }

    // ═══ 3) فشل مُفتعل: catalog واقع → orders يرد degraded (بلا 5xx) ═══
    [Fact]
    public async Task When_catalog_is_down_orders_degrades_instead_of_failing()
    {
        // ✓ تفعيل حقن العطل عبر تكوين الخدمة (مفتاح مخصص — بلا إيقاف container يدويًا)
        await app.Orders.PostAsJsonAsync("/api/test/faults/catalog-timeout", new { enabled = true });

        try
        {
            var response = await app.Orders.GetAsync($"/api/products/{ProductId}/availability");

            response.StatusCode.ShouldBe(HttpStatusCode.OK);
            response.Headers.Contains("X-Degraded").ShouldBeTrue("الـfallback مُعلَن (درس 5.2.4)");

            var body = await response.Content.ReadFromJsonAsync<AvailabilityResponse>();
            body!.Source.ShouldBe("cache-or-default");
        }
        finally
        {
            await app.Orders.PostAsJsonAsync("/api/test/faults/catalog-timeout", new { enabled = false });
        }
    }

    // ── مساعدات ──
    /// <summary>★ بديل `Task.Delay` الثابت: يحاول لحد deadline — أسرع وأقل flakiness.</summary>
    private static async Task<T> WaitUntilAsync<T>(Func<Task<T>> probe, Func<T, bool> predicate,
                                                   TimeSpan timeout, TimeSpan poll)
    {
        var deadline = DateTime.UtcNow + timeout;
        T last = default!;
        while (DateTime.UtcNow < deadline)
        {
            last = await probe();
            if (predicate(last)) return last;
            await Task.Delay(poll);
        }
        throw new TimeoutException($"الشرط لم يتحقق خلال {timeout}. آخر قيمة: {last}");
    }

    private async Task<ChargeRow?> GetChargeAsync(Guid orderId)
    {
        var cs = await app.GetConnectionStringAsync("shopdb");
        await using var conn = new NpgsqlConnection(cs);
        await conn.OpenAsync();
        return await conn.QueryFirstOrDefaultAsync<ChargeRow>(
            "SELECT status, amount_minor FROM payments.charges WHERE order_id = @orderId", new { orderId });
    }

    private sealed record ChargeRow(string Status, long AmountMinor);
    private sealed record AvailabilityResponse(string Source, int Stock);
}
'''},
            {"type": "callout", "kind": "warn", "title": "10 قواعد تمنع flakiness في اختبارات Aspire",
             "md": """
1. **`WaitForResourceHealthyAsync` لكل اعتماد** قبل أول assertion — الإقلاع مش فوري.
2. **بلا `Task.Delay` ثابت**: استخدم polling مع deadline (زي `WaitUntilAsync` فوق).
3. **حدود زمنية على `BuildAsync`/`StartAsync`** بـ`WaitAsync` — الاختبار المعلق أسوأ من الفاشل.
4. **fixture واحد مشترك** (`ICollectionFixture`) — إقلاع النظام لكل اختبار = CI بياخد ساعة.
5. **بلا منافذ ثابتة**: استخدم `app.CreateHttpClient("name")` — Aspire بيوزع المنافذ عشوائيًا.
6. **عزل حالة البيانات**: كل اختبار يستخدم معرّفات جديدة (GUID) أو `Respawn` بين الاختبارات (درس 1.4.2).
7. **لا تعتمد على ترتيب الاختبارات** — xUnit بيشغّل الكلاسات بالتوازي.
8. **بلا assertions على الزمن المطلق** (`elapsed.ShouldBeLessThan(200)`) → استخدم `FakeTimeProvider` أو حدود واسعة.
9. **الأحداث غير المتزامنة**: انتظر **الأثر في قاعدة البيانات**، مش اللوج (اللوغات ترتيبها مش مضمون).
10. **احجر (quarantine) الاختبار flaky فورًا** بـ`[Trait("Category", "Quarantine")]` + issue — وأصلحه أو احذفه خلال أيام.
    اختبار أحمر بيتجاهله الفريق = صفر قيمة.

⚠ **CI**: اختبارات Aspire محتاجة Docker + ذاكرة. شغّلها في job منفصل (مش مع كل PR سريع)،
وحطّ `timeout-minutes` — وإلا runner هيفضل معلق لحد ما يخلص الـquota.
"""},
            {"type": "heading", "level": 2, "text": "2) Contract tests بـPact (consumer-driven)"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Orders.ContractTests/CatalogContractTests.cs", "title": "المستهلك: يعلن ما يحتاجه فعلًا ويولّد الـpact", "code": r'''
// packages: PactNet (4.x/5.x) · xunit.v3 · Shouldly
// requires: using PactNet; using PactNet.Infrastructure;
// ★ الـmatchers (`Match.String/Integer/Regex`) من حزمة PactNet — تحقق من الاسم/المكان في إصدارك

/// <summary>
/// ★ المستهلك هو اللي بيكتب العقد: «أنا (Orders) محتاج من Catalog رد فيه الحقول دي بالتحديد».
/// الاختبار بيشغّل mock server، بينفّذ كود العميل الحقيقي ضده، وبيولّد ملف pact.
/// </summary>
public sealed class CatalogContractTests : IDisposable
{
    private readonly IPactBuilderV3 _pact;
    private readonly string _pactDir;

    public CatalogContractTests()
    {
        _pactDir = Path.Combine(Path.GetTempPath(), "shop-pacts");   // في CI: مسار artifact
        Directory.CreateDirectory(_pactDir);

        IPactV3 pact = Pact.V3("Orders API", "Catalog API", new PactConfig { PactDir = _pactDir });
        _pact = pact.WithHttpInteractions();
    }

    [Fact]
    public async Task GetProduct_returns_snapshot_orders_depends_on()
    {
        var productId = Guid.Parse("42424242-4242-4242-4242-424242424242");
        var expected = new
        {
            id = productId,
            name = "Widget",
            price_minor = 1500,
            currency = "EGP",
            stock = 7,
        };

        // ✓ ترتيب الـDSL كما في توثيق PactNet — تحقق من إصدارك (Given/UponReceiving)
        _pact
            .Given($"A product with id '{productId}' exists")
            .UponReceiving("a request for that product")
                .WithRequest(HttpMethod.Get, $"/api/products/{productId}")
                .WithHeader("Accept", "application/json")
            .WillRespond()
                .WithStatus(HttpStatusCode.OK)
                .WithHeader("Content-Type", "application/json; charset=utf-8")
                .WithJsonBody(new
                {
                    id = productId,
                    // ★ matchers: «مهم إن الحقل موجود بالنوع ده» مش «القيمة دي بالظبط»
                    name = Match.String("Widget"),
                    price_minor = Match.Integer(1500),
                    currency = Match.Regex("^[A-Z]{3}$"),
                    stock = Match.Integer(7),
                });

        await _pact.VerifyAsync(async ctx =>
        {
            // ✓ كل النداءات **لازم** تحصل جوه الـlambda باستخدام عنوان الـmock server
            var client = new CatalogClient(new HttpClient { BaseAddress = ctx.MockServerUri });
            var snapshot = await client.GetAsync(productId, CancellationToken.None);

            snapshot.ShouldNotBeNull();
            snapshot!.Id.ShouldBe(productId);
            snapshot.PriceMinor.ShouldBe(1500);
            snapshot.Currency.ShouldBe("EGP");
        });
    }

    [Fact]
    public async Task GetProduct_returns_404_when_missing()
    {
        var missing = Guid.NewGuid();

        _pact
            .Given("No product with that id exists")
            .UponReceiving("a request for a missing product")
                .WithRequest(HttpMethod.Get, $"/api/products/{missing}")
                .WithHeader("Accept", "application/json")
            .WillRespond()
                .WithStatus(HttpStatusCode.NotFound)
                .WithHeader("Content-Type", "application/problem+json")
                .WithJsonBody(new { title = "NotFound", status = 404 });

        await _pact.VerifyAsync(async ctx =>
        {
            var client = new CatalogClient(new HttpClient { BaseAddress = ctx.MockServerUri });
            var snapshot = await client.GetAsync(missing, CancellationToken.None);
            snapshot.ShouldBeNull("404 يتحول إلى null في عميل الـACL (درس 5.1.2)");
        });
    }

    public void Dispose()
    {
        // ملفات الـpact اتكتبت في _pactDir → تُرفع كـartifact وتُنشر للـbroker
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Catalog.ContractTests/CatalogProviderVerification.cs", "title": "المزود: يثبت إنه بيلتزم بالعقد + endpoint لحالات المزود", "code": r'''
// requires: using PactNet; using PactNet.Infrastructure; using PactNet.Infrastructure.Outputters;
//           using Microsoft.AspNetCore.Mvc.Testing;

/// <summary>
/// ★ المزود بيشغّل نفسه (WebApplicationFactory) وبيلفّ على كل تفاعل في ملفات الـpact
/// ويتحقق إن رده الفعلي بيطابق المتوقع. كسر العقد = اختبار أحمر **عند المزود**.
/// </summary>
public sealed class CatalogProviderVerification : IAsyncLifetime
{
    // ✓ نفس الاصطلاح المستخدم في باقي الدروس: WebApplicationFactory<Program>
    //   (الخدمة بتعلن `public partial class Program { }` في آخر Program.cs)
    private readonly WebApplicationFactory<Program> _factory = new();
    private Uri _serverUri = null!;

    public async ValueTask InitializeAsync()
    {
        var server = _factory.Server;                       // ✓ Kestrel in-memory
        _serverUri = server.BaseAddress;
        await Task.CompletedTask;
    }

    public ValueTask DisposeAsync()
    {
        _factory.Dispose();
        return ValueTask.CompletedTask;
    }

    [Fact]
    public void Catalog_honours_the_orders_pact()
    {
        var config = new PactVerifierConfig
        {
            Outputters = [new ConsoleOutput()],             // ✓ من PactNet.Infrastructure.Outputters
            LogLevel = PactLogLevel.Information,
        };

        var pactPath = new FileInfo(Path.Combine("..", "..", "..", "..", "..",
                                                 "pacts", "Orders API-Catalog API.json"));
        pactPath.Exists.ShouldBeTrue($"ملف العقد لازم يتشارك بين المشروعين (أو يجي من الـbroker): {pactPath.FullName}");

        using var verifier = new PactVerifier("Catalog API", config);

        verifier
            .WithHttpEndpoint(_serverUri)
            .WithFileSource(pactPath)
            .WithProviderStateUrl(new Uri(_serverUri, "/provider-states"))   // ✓ المزود يجهّز البيانات
            // .WithPactBrokerSource(brokerUri, options)   // ← من broker بدل ملف (pending/WIP pacts)
            .Verify();
    }

}

// ═══ endpoint لحالات المزود — ★ للاختبارات فقط، ممنوع في الإنتاج ═══
// في Program.cs (Development فقط):
//   if (app.Environment.IsDevelopment()) app.MapProviderStates();
public static class ProviderStatesEndpoints
{
    public static IEndpointRouteBuilder MapProviderStates(this IEndpointRouteBuilder app)
    {
        app.MapPost("/provider-states", async (ProviderStateRequest req, CatalogDbContext db, CancellationToken ct) =>
        {
            switch (req.State)
            {
                case var s when s is not null && s.StartsWith("A product with id '"):
                    var id = Guid.Parse(s[(s.IndexOf('\'') + 1)..s.LastIndexOf('\'')]);
                    await db.SeedProductAsync(id, "Widget", 1500, "EGP", 7, ct);      // ✓ idempotent
                    break;

                case "No product with that id exists":
                    await db.ResetAsync(ct);                                            // ✓ حالة نظيفة
                    break;

                default:
                    // ⚠ حالة غير معروفة = فشل صريح، مش تجاهل (وإلا العقد بيتحقق على بيانات غلط)
                    throw new InvalidOperationException($"Unknown provider state: {req.State}");
            }

            return Results.Ok();
        });

        return app;
    }
}

public sealed record ProviderStateRequest(string? State, IDictionary<string, object?>? Params);
'''},
            {"type": "code", "lang": "json", "filename": "pacts/Orders API-Catalog API.json", "title": "شكل ملف العقد (مختصر) — ده اللي بيتبادل", "code": r'''
{
  "consumer": { "name": "Orders API" },
  "provider": { "name": "Catalog API" },
  "interactions": [
    {
      "description": "a request for that product",
      "providerStates": [ { "name": "A product with id '42424242-4242-4242-4242-424242424242' exists" } ],
      "request": {
        "method": "GET",
        "path": "/api/products/42424242-4242-4242-4242-424242424242",
        "headers": { "Accept": "application/json" }
      },
      "response": {
        "status": 200,
        "headers": { "Content-Type": "application/json; charset=utf-8" },
        "body": {
          "id": "42424242-4242-4242-4242-424242424242",
          "name": "Widget",
          "price_minor": 1500,
          "currency": "EGP",
          "stock": 7
        },
        "matchingRules": {
          "body": {
            "$.name":        { "match": "type" },
            "$.price_minor": { "match": "integer" },
            "$.currency":    { "match": "regex", "regex": "^[A-Z]{3}$" },
            "$.stock":       { "match": "integer" }
          }
        }
      }
    }
  ],
  "metadata": {
    "pactSpecification": { "version": "3.0.0" },
    "consumerVersion": "1.4.0+sha.9f2c1a7"
  }
}
'''},
            {"type": "table", "head": ["", "Contract tests (Pact)", "Distributed integration (Aspire)"], "rows": [
                ["السؤال اللي بيجاوبه", "هل العقد **لسه متوافق**؟", "هل النظام **شغال مع بعضه**؟"],
                ["البيئة", "mock server محلي — بلا Docker", "النظام الحقيقي كله (containers)"],
                ["الزمن", "ثواني (يشغّل مع كل PR)", "دقيقة+ للإقلاع (job منفصل)"],
                ["بيكشف", "حقل اتشال/اتغيّر نوعه/حالة جديدة", "ترتيب إقلاع، timeout، رسالة ضايعة، إعدادات شبكة"],
                ["مش بيكشف", "مشاكل التفاعل/التوقيت/الأداء", "— (بيكشف أكتر بس أبطأ وأثقل)"],
                ["مين بيكتبه", "**المستهلك** (ويشارك العقد)", "فريق المنصة/صاحب التدفق"],
                ["عدد الاختبارات", "لكل تفاعل مهم (عشرات)", "للتدفقات الحرجة (5–15)"],
                ["في CI", "كل PR — gate على المزود والمستهلك", "كل PR (job منفصل) أو كل merge"],
            ]},
            {"type": "callout", "kind": "note", "title": "عقود الأحداث (Events) — النصف المنسي",
             "md": """
Pact بين خدمات HTTP واضح، بس في نظامنا **أغلب العقود أحداث** في `Shop.Contracts` (درس 5.1.2). طبّق نفس المبدأ:

1. **عقد مكتوب ككود**: الـrecords في مشروع مشترك + `SchemaVersion` + اختبارات snapshot للـJSON
   (`Verify` — درس 1.4.4) عشان أي تغيير في الشكل يكسر اختبارًا.
2. **اختبار توافق من الطرفين**:
   - **الناشر**: يختبر إن الحدث اللي بينشره بيتسلسل بالشكل المتفق عليه (snapshot).
   - **المستهلك**: يختبر إنه يقدر يفك **نسخ قديمة** من الحدث (upcasting — درس 4.2.4).
3. **قاعدة التوافق**: إضافة حقل **اختياري** = آمن · حذف/إعادة تسمية/تغيير نوع = **كسر** → يحتاج إصدار جديد
   وتشغيل النسختين بالتوازي (جدول الـ9 قواعد في درس 5.1.2).
4. **Pact message contracts**: Pact بيدعم عقود الرسائل (message interactions) برضه —
   لو عندك broker، استخدمه بدل ما تبني حل خاص (راجع توثيق PactNet للـmessage DSL في إصدارك).

⚠ أشهر فشل حقيقي: خدمة أضافت حقل `required` لحدث → المستهلكين القدام كسروا في الإنتاج،
وكل الاختبارات كانت خضرا لأن **مفيش اختبار بيغطي العقد بين الخدمتين**. ده بالظبط اللي contract tests بيمنعه.
"""},
            {"type": "heading", "level": 2, "text": "3) CI: تشغيل الكل بثبات"},
            {"type": "code", "lang": "yaml", "filename": ".github/workflows/tests.yml", "title": "3 jobs: سريعة · عقود · تكامل موزّع", "code": r'''
name: tests

on:
  pull_request:
  push: { branches: [main] }

env:
  DOTNET_VERSION: "10.0.x"
  DOTNET_NOLOGO: true
  DOTNET_SKIP_FIRST_TIME_EXPERIENCE: true

jobs:
  # ═══ 1) سريعة: وحدة + شرائح (كل PR، دقيقتين) ═══
  fast:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: "${{ env.DOTNET_VERSION }}" }
      - run: dotnet restore
      - run: dotnet build --no-restore -c Release /warnaserror
      - run: >
          dotnet test --no-build -c Release
          --filter "Category=Unit|Category=Slice"
          --logger "trx;LogFileName=fast.trx"
          --collect:"XPlat Code Coverage"
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: fast-results, path: "**/*.trx" }

  # ═══ 2) العقود: المستهلك يولّد، المزود يتحقق، والنشر للـbroker ═══
  contracts:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: "${{ env.DOTNET_VERSION }}" }
      - run: dotnet restore

      # 2.1 اختبارات المستهلك → توليد ملفات pact
      - name: Consumer contract tests
        run: dotnet test tests/Shop.Orders.ContractTests -c Release --filter "Category=Contract"

      # 2.2 رفع العقود كـartifacts (للمراجعة عند الفشل)
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: pacts, path: pacts/ }

      # 2.3 النشر للـbroker (can-i-deploy يعتمد عليه)
      - name: Publish pacts
        if: github.ref == 'refs/heads/main'
        run: |
          npx --yes pact-broker publish ./pacts \
            --consumer-app-version="${GITHUB_SHA}" \
            --branch="${GITHUB_HEAD_REF:-main}" \
            --broker-base-url="${{ secrets.PACT_BROKER_URL }}" \
            --broker-token="${{ secrets.PACT_BROKER_TOKEN }}"

      # 2.4 اختبارات المزود (بتستهلك نفس الملفات محليًا، أو من الـbroker)
      - name: Provider verification
        run: dotnet test tests/Shop.Catalog.ContractTests -c Release --filter "Category=Contract"

      # 2.5 ★ البوابة: هل النسخة دي آمنة للنشر بالنسبة لمستهلكيها؟
      - name: can-i-deploy
        if: github.ref == 'refs/heads/main'
        run: |
          npx --yes pact-broker can-i-deploy \
            --pacticipant "Catalog API" \
            --version "${GITHUB_SHA}" \
            --to-environment production \
            --retry-while-unknown 6 \
            --broker-base-url="${{ secrets.PACT_BROKER_URL }}" \
            --broker-token="${{ secrets.PACT_BROKER_TOKEN }}"

  # ═══ 3) تكامل موزّع: Aspire (Docker + ذاكرة) — job منفصل ═══
  integration:
    runs-on: ubuntu-latest        # Docker متاح مسبقًا
    timeout-minutes: 30           # ★ إلزامي: الاختبارات الموزعة ممكن تعلق
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: "${{ env.DOTNET_VERSION }}" }
      - run: dotnet restore
      - name: Pre-pull infrastructure images
        run: |
          docker pull postgres:18-alpine
          docker pull redis:8-alpine
          docker pull rabbitmq:4-management-alpine
      - name: Distributed integration tests
        run: >
          dotnet test tests/Shop.SystemTests -c Release
          --filter "Category=Integration"
          --logger "trx;LogFileName=integration.trx"
      # ✓ عند الفشل: ارفع كل حاجة تساعدك تشخّص من غير ما تعيد التشغيل
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: integration-diagnostics
          path: |
            **/*.trx
            **/TestResults/**
            logs/**
      - name: Dump container state on failure
        if: failure()
        run: |
          docker ps -a
          docker logs shop-rabbit 2>&1 | tail -n 200 || true
'''},
            {"type": "callout", "kind": "danger", "title": "أخطاء بتخلي الاختبارات الموزعة عديمة القيمة",
             "md": """
1. **اختبار التكامل بيكرر اختبار الوحدة** (بيختبر حساب خصم) — بطيء وهش وبلا قيمة إضافية.
   اختبارات Aspire بتغطي **التفاعل** فقط.
2. **مفيش حدود زمنية**: `StartAsync` بلا `WaitAsync` + `Task.Delay(60_000)` = CI معلق لحد الـtimeout.
3. **assertion على اللوجات**: اللوجات مش عقد. تحقق من **الأثر** (صف في DB، رد HTTP، رسالة في طابور).
4. **مشاركة حالة بين الاختبارات** (كل الاختبارات بتستخدم نفس `orderId`) → فشل متسلسل غير مفهوم.
5. **`provider-states` endpoint منشور للإنتاج** = ثغرة (أي حد يقدر يزرع/يمسح بيانات). Development فقط + شبكة داخلية.
6. **عقود بلا gate**: توليد pact بدون تحقق المزود (أو العكس) = مفيش حماية. لازم **الاتنين** في CI.
7. **عقد over-specified**: كل الحقول بقيم ثابتة → كل تغيير شكلي يكسر العقد. استخدم matchers
   وحدد **بس** الحقول اللي المستهلك بيعتمد عليها فعلًا.
8. **تجاهل الأحمر flaky** بدل إصلاحه: بعد أسبوعين محدش بيثق في CI.
9. **بيئة اختبار ≠ بيئة إنتاج في الإعدادات الأساسية** (إصدار DB مختلف، وسيط مختلف) → «نجح عندنا».
10. **E2E لكل حاجة**: 200 اختبار بيشغّلوا النظام كله = CI ساعة + فشل عشوائي يومي.

✅ **المقياس**: لو CI بتاعك > 15 دقيقة أو الاختبارات الحمراء بتتجاهل، الهرم مقلوب — استثمر في العقود والشرائح.
"""},
            {"type": "checkpoints", "items": [
                "أبني هرم اختبار للأنظمة الموزعة: unit · slice · contract · distributed integration · E2E · fault injection · performance.",
                "أكتب fixture يشغّل نظام Aspire مرة واحدة، بانتظار الصحة وحدود زمنية و`CreateHttpClient` بالاسم.",
                "أختبر تدفقًا غير متزامن بـpolling حتى الأثر في قاعدة البيانات (بلا `Task.Delay` ثابت).",
                "أطبّق consumer-driven contracts بـPact: مستهلك يولّد العقد بمatchers، مزود يتحقق مع provider states، وبوابة `can-i-deploy`.",
                "أغطي عقود **الأحداث** (snapshot للنشر + upcasting للاستهلاك) وأضع 3 jobs في CI بلا flakiness.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "خدمة غيّرت اسم حقل في الرد من `priceMinor` لـ`price_minor`. كل الاختبارات خضرا. مين اللي كان لازم يكشف ده؟",
                 "options": [
                     "اختبارات الوحدة للمزود",
                     "**Contract test عند المستهلك** (Pact) + تحقق المزود من العقد — دي الحالة اللي العقد بيتكسر فيها والاختبارات الداخلية ما تشوفهاش",
                     "اختبار E2E في staging",
                     "مراجعة الكود فقط",
                 ], "answer": 1,
                 "explain": "اختبارات المزود بتختبر سلوكه الجديد (صحيح بالنسبة له)، واختبارات المستهلك بتشتغل ضد mock — فالعقد وحده هو اللي بيربط الطرفين. E2E هيكشفه لكن متأخر وببطء."},
                {"q": "ليه ننتظر `WaitForResourceHealthyAsync` بدل ما نبدأ الاختبار فورًا بعد `StartAsync`؟",
                 "options": [
                     "أداء أفضل",
                     "`StartAsync` بينتهي لما العمليات تبدأ، مش لما الاعتمادات تبقى جاهزة — أول اختبار هيفشل عشوائيًا (flaky)",
                     "مطلوب من xUnit",
                     "عشان اللوحة تظهر",
                 ], "answer": 1,
                 "explain": "الصحة (health check عدى) هي الضمان إن DB/الوسيط/الخدمة جاهزة تستقبل. بلاها الاختبارات بتنجح «أحيانًا»."},
                {"q": "التدفق غير متزامن (حدث → مستهلك → صف في DB). إزاي تختبره؟",
                 "options": [
                     "`await Task.Delay(5000)` ثم تحقق",
                     "Polling مع deadline: تحقق من **الأثر في DB** كل 200ms لحد 30 ثانية — أسرع وأقل هشاشة",
                     "تحقق من اللوجات",
                     "ما تختبروش (غير متزامن = غير قابل للاختبار)",
                 ], "answer": 1,
                 "explain": "الـdelay الثابت بطيء (5 ثواني حتى لو النتيجة جاهزت في 300ms) وهش (لو الجهاز أبطأ يفشل). الـpolling على الأثر هو النمط الصحيح."},
                {"q": "مين بيكتب الـpact file؟",
                 "options": [
                     "المزود",
                     "**المستهلك** — لأنه الوحيد اللي يعرف الحقول اللي بيعتمد عليها فعلًا؛ والمزود بيتحقق منه",
                     "فريق المنصة",
                     "يتولد تلقائيًا من OpenAPI",
                 ], "answer": 1,
                 "explain": "ده معنى «consumer-driven»: العقود من تحت لفوق (من الاحتياج الفعلي)، مش من فوق (من التوثيق). OpenAPI ممكن يساعد لكنه مش بديل."},
                {"q": "provider state «يوجد منتج بمعرّف 42» — ليه المزود محتاجها؟",
                 "options": [
                     "عشان الأداء",
                     "لأن تحقق العقد لازم يشتغل على **حالة بيانات معروفة وقابلة للتكرار** — وإلا الرد هيتغير حسب محتوى DB وقت التشغيل",
                     "مطلوب من Pact broker",
                     "عشان الـmatchers",
                 ], "answer": 1,
                 "explain": "المزود بيفتح endpoint (`/provider-states`) يجهّز الحالة قبل كل تفاعل — **في الاختبارات فقط**، ممنوع في الإنتاج."},
                {"q": "إمتى تشغّل اختبارات Aspire الموزعة في CI؟",
                 "options": [
                     "مع كل اختبار وحدة",
                     "job منفصل بـ`timeout-minutes`، مع العقود والشرائح في jobs أسرع — عشان Docker/الذاكرة والزمن",
                     "يدويًا فقط",
                     "بعد النشر",
                 ], "answer": 1,
                 "explain": "الفصل بيخلي الـfeedback السريع (دقايق) منفصل عن الثقيل (دقايق طويلة)، وبلا `timeout-minutes` الـrunner ممكن يعلق."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "عقد Pact بين خدمتين + gate في CI",
                 "md": "اختار زوج مستهلك/مزود حقيقي في مشروعك (أو حدثًا بين ناشر ومستهلك)، واكتب contract tests بالمستهلك (matchers لا قيم ثابتة) وتحقق المزود (provider states)، واربطهم في CI ببوابة تمنع الدمج عند كسر العقد.",
                 "criteria": [
                     "اختبار مستهلك بيولّد pact file بـ**matchers** (مش كل القيم ثابتة) ويغطي الحالة الناجحة + حالة خطأ واحدة",
                     "اختبار مزود بيتحقق من نفس الملف مع `WithProviderStateUrl` وحالات مزود معرّفة (وحالة غير معروفة → فشل صريح)",
                     "`provider-states` endpoint مقصور على Development (كود + تعليق يوضح الخطورة)",
                     "كسر مقصود (حذف حقل من رد المزود) بيخلي اختبار المزود يفشل — **أثبت ده بلقطة/مخرجات** ثم ارجعه",
                     "CI job للعقود (consumer → artifacts → provider verification) + `timeout-minutes`",
                     "لكل عقد أحداث: snapshot test للنشر + اختبار upcasting لنسخة قديمة (لو applicable)",
                     "جدول في `docs/contracts.md`: المستهلك × المزود × التفاعل × حالة التوافق",
                 ],
                 "hint": "ابدأ بـ**تفاعل واحد فقط** (الأهم) وخليه أخضر في CI، بعدين زوّد. محاولة تغطية كل العقود مرة واحدة بتفشل.",
                 "solution": "",
                 "resources": [
                     {"label": "PactNet README (consumer + provider)", "url": "https://github.com/pact-foundation/pact-net"},
                     {"label": "Pact .NET implementation guide", "url": "https://docs.pact.io/implementation_guides/net/readme"},
                     {"label": "Consumer-driven contracts", "url": "https://docs.pact.io/"},
                 ]},
                {"id": "t2", "title": "اختبار تكامل موزّع بـAspire لتدفق حرج + فشل مُفتعل",
                 "md": "اكتب 3–5 اختبارات تكامل بـAspire تغطي تدفق أعمال حرج واحد عبر خدمتين+ (متزامن وغير متزامن)، واختبارَي فشل مُفتعل (خدمة تابعة واقعة، رسالة مكررة/سامة)، وخليهم يشتغلوا في CI بثبات (3 تشغيلات متتالية خضرا).",
                 "criteria": [
                     "`ShopAppFixture` بـ`IAsyncLifetime` + `ICollectionFixture`: إقلاع واحد لكل الاختبارات",
                     "`WaitForResourceHealthyAsync` لكل اعتماد + `WaitAsync` بحدود زمنية على `BuildAsync`/`StartAsync`",
                     "اختبار تدفق متزامن (HTTP عبر ≥2 خدمة) بيتحقق من الرد **ومن الأثر في DB**",
                     "اختبار تدفق غير متزامن بـpolling (بلا `Task.Delay` ثابت) بيتحقق من أثر المعالجة",
                     "اختبارَا فشل مُفتعل: fallback مُعلَن عند وقوع تابع، وidempotency عند رسالة مكررة (درس 5.2.5)",
                     "كل الاختبارات بـ`[Trait(\"Category\", Categories.Integration)]` + job CI منفصل بـ`timeout-minutes` + artifacts عند الفشل",
                     "إثبات استقرار: 3 تشغيلات متتالية خضرا محليًا + تشغيل واحد في CI (مخرجات مرفقة)",
                     "مفيش حالة مشتركة بين الاختبارات (معرّفات جديدة/Respawn) — اذكر إزاي حققت العزل",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Aspire testing — overview", "url": "https://aspire.dev/testing/overview/"},
                     {"label": "Aspire testing — manage the AppHost lifecycle", "url": "https://aspire.dev/testing/manage-app-host/"},
                     {"label": "Aspire testing in CI/CD", "url": "https://aspire.dev/testing/testing-in-ci/"},
                     {"label": "Aspire testing — advanced scenarios", "url": "https://aspire.dev/testing/advanced-scenarios/"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Aspire integration testing overview", "url": "https://aspire.dev/testing/overview/"},
                {"label": "Write your first Aspire integration test", "url": "https://aspire.dev/testing/write-your-first-test/"},
                {"label": "PactNet", "url": "https://github.com/pact-foundation/pact-net"},
                {"label": "Pact docs — .NET guide", "url": "https://docs.pact.io/implementation_guides/net/readme"},
                {"label": "GitHub Actions workflows", "url": "https://docs.github.com/en/actions"},
                {"label": "Testcontainers for .NET", "url": "https://testcontainers.com/"},
            ]},
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # s5-m3-l4 — أنماط جاهزة: Cache-aside وCircuit breaker وBulkhead وThrottling
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s5-m3-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
دلوقتي عندك خدمات، وسيط رسائل، وresilience. السؤال اللي بيفرّق بين junior وsenior مش
«تعرف أنماط إيه؟» — بل **«لأي مشكلة استخدمت أي نمط، وإيه اللي رفضته وليه؟»**.

الدرس ده جولة مركزة في أهم الأنماط من **Azure Architecture Center** (المرجع الأشهر للأنماط السحابية)
بتنفيذها في .NET: **Cache-aside**، **Circuit Breaker**، **Bulkhead**، **Throttling**، و**Queue-Based Load Leveling**،
مع جدول اختيار، وأخطاء شائعة لكل نمط، وقالب **ADR** يخلي قرارك موثقًا (درس 4.1.4).

القاعدة الحاكمة: **النمط تكلفة** (كود + تعقيد + فشل جديد محتمل). طبّقه لما المشكلة موجودة فعلًا ومقاسة،
مش لأن مقال قال إن كل الأنظمة الكبيرة بتستخدمه.
"""},
            {"type": "terms", "items": [
                {"term": "Cache-Aside", "def": "التطبيق بيقرأ من الكاش؛ لو مش موجود يجيب من المصدر ويملأ الكاش. الكتابة بتبطل الكاش (مش بتحدّثه)."},
                {"term": "Cache Stampede", "def": "لحظة انتهاء صلاحية مفتاح ساخن: 500 طلب يروحوا للمصدر في نفس اللحظة. الحل: قفل/`GetOrCreate` ذرّي (HybridCache بيعملها)."},
                {"term": "Bulkhead", "def": "عزل الموارد (اتصالات/خيوط/طلبات) في أقسام، عشان فشل جزء ما يستهلكش موارد الكل ويغرق النظام."},
                {"term": "Throttling / Rate Limiting", "def": "تحديد معدل الطلبات المسموح (لكل عميل/مستأجر/مسار) ورفض الزائد بـ429 + `Retry-After`."},
                {"term": "Queue-Based Load Leveling", "def": "طابور بين المنتج والمستهلك يمتص الذروة: الإنتاج يتقبل فورًا، والمعالجة بمعدل ثابت — بدل الانهيار تحت الحمل."},
                {"term": "Circuit Breaker", "def": "يقطع النداءات لتابع فاشل لفترة، مع اختبار دوري (half-open) للتعافي — بيمنع استنزاف المهلات والموارد (درس 5.2.4)."},
                {"term": "Backpressure", "def": "إشارة للمنتج إنه يبطّئ (رفض/انتظار/429/طابور ممتلئ) — بلاها النظام بياخد شغل أكتر من قدرته."},
                {"term": "Fail-Open / Fail-Closed", "def": "سلوك المكوّن عند فشله: الكاش fail-open (كمل من المصدر)، والمصادقة/الـrate limiter غالبًا fail-closed (ارفض)."},
                {"term": "Claim Check", "def": "الرسالة الكبيرة تتخزن في blob والحدث بيشيل **مرجع** لها — يحافظ على حجم الرسائل وسرعة الوسيط."},
                {"term": "ADR", "def": "Architecture Decision Record: وثيقة قصيرة تسجل القرار والسياق والبدائل والنتائج (درس 4.1.4)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) جدول الاختيار: المشكلة ← النمط ← التنفيذ في .NET"},
            {"type": "table", "head": ["المشكلة المقاسة", "النمط", "التنفيذ في .NET", "الفخ الأشهر", "الدرس"], "rows": [
                ["قراءة متكررة غالية (DB/خارجي) وبيانات تتحمل تأخير", "**Cache-Aside**", "`IHybridCache` (L1+L2+stampede) أو Output Cache", "الكاش يبقى مصدر حقيقة والإبطال ينسى", "2.1.6"],
                ["تابع بيفشل/بيبطّئ وبيستهلك مهلات وموارد", "**Circuit Breaker**", "`CircuitBreakerStrategy` لكل تابع", "breaker واحد لكل التبعيات → تابع واحد يعطّل الكل", "5.2.4"],
                ["تابع بطيء ممكن ياكل كل اتصالات/خيوط الخدمة", "**Bulkhead**", "`ConcurrencyLimiterStrategy` / `SemaphoreSlim` لكل تابع أو مستأجر", "بلا timeout على الانتظار → طوابير لانهائية", "تحت ↓"],
                ["عميل/مستأجر بيبعت طلبات أكتر من المتفق", "**Throttling**", "`AddRateLimiter` (sliding window/token bucket مقسّم)", "429 بلا `Retry-After` → العملاء بيدوّروا على الفور", "2.1.5"],
                ["ذروة حمل مؤقتة بتوقع المعالجة", "**Queue-Based Load Leveling**", "وسيط رسائل (MassTransit) أو `Channel` محدود + `BackgroundService`", "طابور بلا حد أقصى → استهلاك ذاكرة بلا نهاية", "5.2.1"],
                ["عملية أعمال عبر خدمات بلا معاملات موزعة", "**Compensating Transaction (Saga)**", "MassTransit state machine + تعويض", "تعويض بلا idempotency ولا timeout", "5.2.3"],
                ["حدث لازم ما يضيعش رغم فشل الوسيط", "**Outbox**", "EF Outbox / outbox يدوي + dispatcher", "نشر خارج المعاملة (ضائع عند الفشل)", "4.2.3"],
                ["استقبال حدث مكرر", "**Idempotent Receiver**", "قيد فريد / تحديث شرطي / مفاتيح idempotency", "جدول مفاتيح بلا نافذة صحيحة", "5.2.5"],
                ["رسائل كبيرة بتبطّئ الوسيط", "**Claim Check**", "Blob storage + مرجع في الحدث", "مرجع بلا TTL/صلاحيات → رسالة ميتة", "—"],
                ["محاولة ثانية بعد فشل عابر", "**Retry (backoff + jitter)**", "`RetryStrategy` مع `DelayGenerator`", "retry بلا jitter → موجات متزامنة (thundering herd)", "5.2.4"],
                ["معرفة هل التابع سليم قبل ما تقرر readiness", "**Health Endpoint Monitoring**", "`AddHealthChecks` + فحوصات تابعة", "`/health` بيتحقق من كل حاجة → liveness فاشل يعيد تشغيل سليم", "2.3.4"],
                ["قراءة من نسخة طبقية لتقليل الحمل", "**CQRS / Materialized View**", "قراءة من projector/قاعدة قراءة (درس 4.2.2)", "view من غير آلية تحديث/تأخير مُعلن", "4.2.2"],
            ]},
            {"type": "heading", "level": 2, "text": "2) Cache-Aside: التنفيذ الكامل (مع الإبطال والحماية)"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Catalog/Read/ProductCatalogReader.cs", "title": "HybridCache + وسوم إبطال + fail-open + مقاييس", "code": r'''
// packages: Microsoft.Extensions.Caching.Hybrid (.NET 9+)
// requires: using Microsoft.Extensions.Caching.Hybrid;

/// <summary>
/// ★ Cache-Aside: اقرأ من الكاش → لو مفقود اجلب من المصدر واملأ الكاش.
/// `IHybridCache` بيديك: L1 (ذاكرة) + L2 (Redis) + **حماية من stampede** + إبطال بوسوم.
/// (شرح الطبقات والمقارنة في درس 2.1.6 — هنا التركيز على النمط في سياق خدمات متعددة.)
/// </summary>
public sealed class ProductCatalogReader(
    IHybridCache cache,
    CatalogDbContext db,
    CatalogMetrics metrics,
    ILogger<ProductCatalogReader> log)
{
    private static readonly HybridCacheEntryOptions Options = new()
    {
        Expiration = TimeSpan.FromMinutes(5) + TimeSpan.FromSeconds(Random.Shared.Next(0, 60)),  // ★ jitter ضد انتهاء جماعي
        LocalCacheExpiration = TimeSpan.FromSeconds(30),                                          // L1 قصير (تعدد النسخ)
    };

    public async Task<ProductView?> GetAsync(Guid productId, CancellationToken ct)
    {
        var key = $"catalog:product:{productId}";

        try
        {
            // ✓ ذرّي: لو 500 طلب وصلوا في نفس اللحظة، واحد فقط بيروح للـDB (stampede protection)
            return await cache.GetOrCreateAsync(
                key,
                async token => await LoadFromDbAsync(productId, token),
                Options,
                tags: [$"product:{productId}", "catalog:products"],   // ★ وسوم للإبطال الدقيق
                cancellationToken: ct);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            // ✓ fail-open: الكاش واقع → اكمل من المصدر (بلا تعطيل الخدمة)
            metrics.CacheFailures.Add(1);
            log.LogWarning(ex, "cache unavailable for {Key} — falling back to database", key);
            return await LoadFromDbAsync(productId, ct);
        }
    }

    /// <summary>★ الكتابة تُبطل الكاش — لا تحاول تحديثه (سباق + تعقيد بلا فائدة).</summary>
    public async Task InvalidateAsync(Guid productId, CancellationToken ct)
    {
        try
        {
            await cache.RemoveByTagAsync($"product:{productId}", ct);
            metrics.CacheInvalidations.Add(1, new("reason", "write"));
        }
        catch (Exception ex)
        {
            // ⚠ فشل الإبطال = بيانات قديمة تُخدم. سجل + قِس + أنذر (ولا تبتلع الخطأ بصمت)
            metrics.CacheInvalidationFailures.Add(1);
            log.LogError(ex, "failed to invalidate cache for product {ProductId} — serving stale until TTL", productId);
        }
    }

    private async Task<ProductView?> LoadFromDbAsync(Guid productId, CancellationToken ct)
    {
        metrics.CacheLoads.Add(1);
        var product = await db.Products
            .Where(p => p.Id == productId)
            .Select(p => new ProductView(p.Id, p.Name, p.PriceMinor, p.Currency, p.Stock))
            .FirstOrDefaultAsync(ct);

        if (product is null)
        {
            // ★ حماية من cache penetration: خزّن «غير موجود» بـTTL قصير (وإلا كل طلب لمعرّف غلط يضرب DB)
            log.LogDebug("product {ProductId} not found — caching negative result briefly", productId);
        }

        return product;
    }
}

public sealed record ProductView(Guid Id, string Name, long PriceMinor, string Currency, int Stock);

public sealed class CatalogMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Catalog", "1.0.0");
    public Counter<long> CacheLoads              = Meter.CreateCounter<long>("catalog.cache.loads");
    public Counter<long> CacheInvalidations      = Meter.CreateCounter<long>("catalog.cache.invalidations");
    public Counter<long> CacheInvalidationFailures = Meter.CreateCounter<long>("catalog.cache.invalidation_failures");
    public Counter<long> CacheFailures           = Meter.CreateCounter<long>("catalog.cache.failures");
}

// ── التسجيل ──
// builder.Services.AddHybridCache(o =>
// {
//     o.DefaultEntryOptions = new HybridCacheEntryOptions
//     {
//         Expiration = TimeSpan.FromMinutes(5),
//         LocalCacheExpiration = TimeSpan.FromSeconds(30),
//     };
//     o.MaximumPayloadBytes = 1024 * 1024;          // ✓ حد أقصى لحجم العنصر (حماية ذاكرة)
// });
// ✓ الطبقة الثانية (L2): سجّل IDistributedCache عبر تكامل Aspire، وHybridCache بيستخدمه تلقائيًا
// builder.AddRedisDistributedCache("cache");        // حزمة Aspire.StackExchange.Redis (درس 5.3.1)
// builder.Services.AddHybridCache(o => { /* DefaultEntryOptions/MaximumPayloadBytes */ });
'''},
            {"type": "callout", "kind": "note", "title": "Cache-aside مقابل البدائل — اختار بوعي",
             "md": """
| النمط | الكتابة | القراءة | إمتى |
|---|---|---|---|
| **Cache-Aside** | التطبيق يكتب للمصدر **ويُبطل** الكاش | من الكاش، ولو مفقود من المصدر | ★ الافتراضي: بيانات تُحسب غالية وتتحمل ثواني تأخير |
| **Write-Through** | التطبيق يكتب للكاش **والمصدر** معًا | من الكاش (دائمًا موجود) | قراءة كثيفة جدًا وتأخير كتابة مقبول |
| **Write-Behind** | للكاش فقط، والتخزين لاحقًا | من الكاش | أداء كتابة أقصى — **خطر فقدان بيانات** |
| **Refresh-Ahead** | — | الكاش بيتحدّث قبل الانتهاء | مفاتيح ساخنة جدًا (يقلل stampede) |

**3 قواعد لا تتفاوض عليها في cache-aside:**
1. **الإبطال عند الكتابة، مش التحديث** — التحديث المتزامن من نسختين = بيانات قديمة بشكل دائم.
2. **TTL + jitter دائمًا** — بلا jitter كل المفاتيح بتنتهي في نفس اللحظة (ذروة على DB).
3. **الكاش ليس مصدر حقيقة** — لو الكاش ضاع، النظام لازم يفضل شغال (أبطأ). اختبر ده (أوقف Redis).
"""},
            {"type": "heading", "level": 2, "text": "3) Bulkhead: عزل الموارد حتى لا يغرق الكل"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Infrastructure/Bulkheads.cs", "title": "عزل لكل تابع + لكل مستأجر (بـtimeout ورفض صريح)", "code": r'''
// packages: Microsoft.Extensions.Resilience
// requires: using Microsoft.Extensions.DependencyInjection; using Microsoft.Extensions.Resilience;
//           using Polly.Concurrency; using System.Threading.RateLimiting;   // ← QueueProcessingOrder

/// <summary>
/// ★ Bulkhead = حد أقصى للتزامن + طابور محدود + **رفض صريح** عند الامتلاء.
/// الهدف: تابع بطيء (مدفوعات) ما يستهلكش كل اتصالات/خيوط الخدمة فيعطّل حتى القراءات السريعة.
/// </summary>
public static class BulkheadRegistration
{
    public static IServiceCollection AddOrderBulkheads(this IServiceCollection services)
    {
        // ① لكل **تابع خارجي** pipeline خاص (مش pipeline واحد مشترك)
        services.AddResiliencePipeline("ExternalPayment", builder => builder
            .AddConcurrencyLimiter(new ConcurrencyLimiterOptions
            {
                PermitLimit = 12,          // ★ أقصى 12 نداء متزامن للبوابة
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit = 24,           // ✓ طابور محدود: الزيادة تُرفض فورًا (backpressure)
            })
            .AddTimeout(TimeSpan.FromSeconds(20)));   // ← من ميزانية المهلة (درس 5.2.4)

        services.AddResiliencePipeline("ExternalShipping", builder => builder
            .AddConcurrencyLimiter(new ConcurrencyLimiterOptions { PermitLimit = 6, QueueLimit = 12 })
            .AddTimeout(TimeSpan.FromSeconds(15)));

        services.AddResiliencePipeline("InternalRead", builder => builder
            .AddConcurrencyLimiter(new ConcurrencyLimiterOptions { PermitLimit = 64, QueueLimit = 128 })
            .AddTimeout(TimeSpan.FromSeconds(3)));

        // ② عزل **لكل مستأجر**: مستأجر واحد مسيء ما يحرقش حصة الباقين
        services.AddSingleton<TenantBulkheadRegistry>();

        return services;
    }
}

/// <summary>bulkhead لكل مستأجر، مع timeout على الانتظار ورفض صريح (429).</summary>
public sealed class TenantBulkheadRegistry(TenantBulkheadOptions options)
{
    private readonly System.Collections.Concurrent.ConcurrentDictionary<string, SemaphoreSlim> _gates = new();

    public async Task<T> ExecuteAsync<T>(string tenantId, Func<CancellationToken, Task<T>> action, CancellationToken ct)
    {
        var gate = _gates.GetOrAdd(tenantId, _ => new SemaphoreSlim(options.MaxConcurrencyPerTenant,
                                                                     options.MaxConcurrencyPerTenant));

        // ✓ الانتظار **محدود بزمن** — بلا timeout الطابور بيكبر لانهائيًا
        if (!await gate.WaitAsync(options.AcquireTimeout, ct))
        {
            BulkheadMetrics.Rejections.Add(1, new("tenant", tenantId, "reason", "saturated"));
            throw new TenantRateLimitedException(tenantId, options.AcquireTimeout);   // ← يتحوّل لـ429
        }

        try
        {
            BulkheadMetrics.InFlight.Add(1, new("tenant", tenantId));
            return await action(ct);
        }
        finally
        {
            BulkheadMetrics.InFlight.Add(-1, new("tenant", tenantId));
            gate.Release();
        }
    }
}

public sealed class TenantBulkheadOptions
{
    public int MaxConcurrencyPerTenant { get; init; } = 8;
    public TimeSpan AcquireTimeout { get; init; } = TimeSpan.FromSeconds(2);   // ★ قصير: ارفض بسرعة
}

public sealed class TenantRateLimitedException(string tenantId, TimeSpan waited)
    : Exception($"المستأجر {tenantId} تجاوز حد التزامن بعد انتظار {waited.TotalSeconds}s");

public static class BulkheadMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Bulkhead", "1.0.0");
    public Counter<long> Rejections = Meter.CreateCounter<long>("bulkhead.rejections");
    public ObservableGauge<int> InFlight = Meter.CreateObservableGauge("bulkhead.inflight", () => 0);   // ✓ اربطه بقيمة حقيقية
}

// ── الاستخدام في endpoint ──
// app.MapPost("/api/orders", async (PlaceOrderRequest req, TenantBulkheadRegistry bulkheads,
//                                   OrderService orders, HttpContext http) =>
// {
//     var tenantId = http.User.FindFirst("tenant_id")?.Value ?? "anonymous";
//     try
//     {
//         return await bulkheads.ExecuteAsync(tenantId, ct => orders.PlaceAsync(req, ct), http.RequestAborted);
//     }
//     catch (TenantRateLimitedException)
//     {
//         // ✓ ارفض بسرعة وبوضوح (بلا طوابير لانهائية)
//         return Results.Problem(statusCode: StatusCodes.Status429TooManyRequests,
//             title: "TooManyRequests", detail: "تجاوزت حد التزامن لمستأجرك — أعد المحاولة بعد قليل",
//             extensions: new Dictionary<string, object?> { ["retryAfterSeconds"] = 2 });
//     }
// });
'''},
            {"type": "table", "head": ["بُعد العزل", "مثال", "الحد النموذجي", "عند الامتلاء"], "rows": [
                ["لكل **تابع خارجي**", "بوابة الدفع، الشحن، SMS", "6–20 متزامن + طابور ≤ 2×", "رفض/503 مع fallback لو متاح"],
                ["لكل **مستأجر/عميل**", "طلبات مستأجر واحد", "4–16 متزامن", "429 + `Retry-After`"],
                ["لكل **مسار/عملية**", "التقارير الثقيلة مقابل القراءات", "pool منفصل (اتصالات/خيوط)", "طابور محدود أو رفض"],
                ["لكل **قاعدة بيانات**", "اتصالات Npgsql لكل خدمة", "`Max Pool Size` (درس 3.4.2)", "timeout على الفتح → 503"],
                ["لكل **مستهلك رسائل**", "مستهلك الأحداث مقابل مستهلك التقارير", "`PrefetchCount`/`ConcurrentMessageLimit`", "الرسائل تنتظر في الطابور (مقبول)"],
                ["لكل **نسخة/منطقة**", "خدمة في منطقة مقابل تانية", "routing + weights", "تحويل للحمل المتبقي"],
            ]},
            {"type": "heading", "level": 2, "text": "4) Throttling: احمِ نفسك قبل ما تحمي عملاءك"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Gateway/RateLimiting.cs", "title": "مقسّم حسب المستأجر + عام + token bucket للانفجارات", "code": r'''
// requires: using System.Globalization;               // ← NumberFormatInfo
//           using System.Threading.RateLimiting;      // ← limiters + MetadataName
//           using Microsoft.AspNetCore.RateLimiting;

public static class GatewayRateLimiting
{
    public static IServiceCollection AddGatewayRateLimiting(this IServiceCollection services)
    {
        services.AddRateLimiter(options =>
        {
            // ✓ الرفض لازم يكون مفهومًا: 429 + Retry-After + جسم problem+json (درس 2.1.4)
            options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
            options.OnRejected = async (context, ct) =>
            {
                var lease = context.Lease;
                if (lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
                {
                    context.HttpContext.Response.Headers.RetryAfter =
                        ((int)retryAfter.TotalSeconds).ToString(NumberFormatInfo.InvariantInfo);
                }

                ThrottleMetrics.Rejections.Add(1, new(
                    "policy", context.HttpContext.GetEndpoint()?.DisplayName ?? "unknown",
                    "tenant", context.HttpContext.User.FindFirst("tenant_id")?.Value ?? "anonymous"));

                context.HttpContext.Response.ContentType = "application/problem+json";
                await context.HttpContext.Response.WriteAsJsonAsync(new
                {
                    type = "https://tools.ietf.org/html/rfc6585#section-4",
                    title = "Too Many Requests",
                    status = 429,
                    detail = "تجاوزت الحد المسموح — راجع ترويسة Retry-After",
                }, ct);
            };

            // ① سياسة لكل مستأجر: نافذة منزلقة (أعدل من الثابتة عند الحدود)
            options.AddPolicy("per-tenant", httpContext =>
            {
                var tenantId = httpContext.User.FindFirst("tenant_id")?.Value
                               ?? httpContext.Connection.RemoteIpAddress?.ToString()
                               ?? "anonymous";

                return RateLimitPartition.GetSlidingWindowLimiter(tenantId, _ => new SlidingWindowRateLimiterOptions
                {
                    PermitLimit = 120,                              // 120 طلب
                    Window = TimeSpan.FromMinutes(1),               // في الدقيقة
                    SegmentsPerWindow = 6,                          // ★ دقة أعلى = عدل أكثر
                    QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                    QueueLimit = 0,                                 // ✓ بلا طابور: ارفض فورًا (backpressure)
                });
            });

            // ② سياسة للانفجارات: token bucket يسمح بدفعة ثم يهدّئ
            options.AddPolicy("burst", httpContext =>
                RateLimitPartition.GetTokenBucketLimiter(
                    httpContext.User.FindFirst("tenant_id")?.Value ?? "anonymous",
                    _ => new TokenBucketRateLimiterOptions
                    {
                        TokenLimit = 50,
                        TokensPerPeriod = 10,
                        ReplenishmentPeriod = TimeSpan.FromSeconds(1),
                        QueueLimit = 0,
                        AutoReplenishment = true,
                    }));

            // ③ حد عام لكل الخدمة (حماية أخيرة من DDoS خفيف/خطأ في عميل)
            options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(httpContext =>
                RateLimitPartition.GetFixedWindowLimiter("global", _ => new FixedWindowRateLimiterOptions
                {
                    PermitLimit = 5_000,
                    Window = TimeSpan.FromSeconds(1),
                    QueueLimit = 0,
                }));
        });

        return services;
    }
}

public static class ThrottleMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Gateway", "1.0.0");
    public Counter<long> Rejections = Meter.CreateCounter<long>("gateway.rate_limit.rejections");
}

// ── الاستخدام ──
// var app = builder.Build();
// app.UseRateLimiter();                              // ★ بعد المصادقة (عشان تقسّم بالمستأجر) وقبل الـendpoints
// app.MapGet("/api/catalog/products", Handler).RequireRateLimiting("per-tenant");
// app.MapPost("/api/orders",        Handler).RequireRateLimiting("burst");
// app.MapPost("/api/reports",       Handler).RequireRateLimiting("per-tenant");   // ← المسارات الغالية أولًا
'''},
            {"type": "callout", "kind": "tip", "title": "Throttling: 6 قرارات لا تتجاهلها",
             "md": """
1. **ارفض بوضوح**: `429` + `Retry-After` + `application/problem+json`. عميل بلا `Retry-After` بيعيد فورًا = ذروة تانية.
2. **التقسيم بالمستأجر/العميل، مش بالمنفذ العام فقط** — حد عام بس معناه إن مستأجر واحد مسيء يعطّل الكل.
3. **الترتيب مهم**: `UseAuthentication` → `UseRateLimiter` → endpoints (وإلا هتقسّم بـ«anonymous» للجميع).
4. **احمي المسارات الغالية أولًا** (تقارير، بحث، تصدير) — مش كل المسارات بنفس الحد.
5. **ثبّت الحدود بقياس**: من p95 للحمل الحقيقي × هامش، مش رقم من مقال. وراجعها كل فترة.
6. **لا تعاقب عملاءك بإعادة محاولة أعمى**: في **جهة العميل** احترم `Retry-After` عبر `DelayGenerator`
   (درس 5.2.4) — وقلّل المعدل محليًا (client-side throttling) بدل ما تغرق الشبكة.

⚠ **فرّق بين throttling وbulkhead**: الـthrottling بيحدّ **معدل** الطلبات (لكل فترة)،
والـbulkhead بيحدّ **التزامن** (كم طلب شغال دلوقتي). الاتنين مطلوبين لحماية مختلفة:
معدل عالي بتزامن منخفض = طوابير، وتزامن عالي بمعدل منخفض = انفجار لحظي.
"""},
            {"type": "heading", "level": 2, "text": "5) Queue-Based Load Leveling: امتصاص الذروة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Ingest/IngestionQueue.cs", "title": "Channel محدود + backpressure + مقاييس", "code": r'''
// requires: using System.Threading.Channels;

/// <summary>
/// ★ النمط: قبول العمل فورًا في طابور **محدود**، ومعالجته بمعدل ثابت — بدل الانهيار تحت الذروة.
/// استخدم وسيط رسائل (RabbitMQ/Kafka) لما تحتاج توزيعًا/تكرارًا/تسليمًا موثوقًا (درس 5.2.1)،
/// و`Channel` في الذاكرة لما الطابور داخلي لعملية واحدة ولازم يكون رخيصًا.
/// </summary>
public sealed class IngestionQueue(IngestionOptions options, IngestionMetrics metrics, ILogger<IngestionQueue> log)
{
    // ✓ BoundedChannelOptions.FullMode.Wait = backpressure: المنتج ينتظر بدل ما يملأ الذاكرة
    private readonly Channel<IngestItem> _channel = Channel.CreateBounded<IngestItem>(
        new BoundedChannelOptions(options.Capacity)
        {
            FullMode = BoundedChannelFullMode.Wait,
            SingleReader = false,
            SingleWriter = false,
        });

    public async ValueTask EnqueueAsync(IngestItem item, CancellationToken ct)
    {
        // ⚠ لو الطابور ممتلئ: `WriteAsync` هينتظر. لو الانتظار أطول من الميزانية → ارفض (429/503)
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeout.CancelAfter(options.EnqueueTimeout);

        try
        {
            await _channel.Writer.WriteAsync(item, timeout.Token);
            metrics.EnqueueDepth.Add(1);
        }
        catch (OperationCanceledException) when (!ct.IsCancellationRequested)
        {
            metrics.Rejections.Add(1, new("reason", "queue_full"));
            log.LogWarning("ingestion queue full (capacity {Capacity}) — rejecting item", options.Capacity);
            throw new QueueFullException(options.Capacity);     // ← يتحوّل لـ429/503 في الـendpoint
        }
    }

    /// <summary>المعالجة بمعدل ثابت (مستهلك واحد أو أكثر) — ★ لا تطلق مهام بلا حدود.</summary>
    public async Task ProcessAsync(Func<IngestItem, CancellationToken, Task> handler, CancellationToken ct)
    {
        await foreach (var item in _channel.Reader.ReadAllAsync(ct))
        {
            metrics.EnqueueDepth.Add(-1);
            try
            {
                await handler(item, ct);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                // ✓ فشل عنصر لا يوقف الطابور: سجل + عدّاد + (اختياري) طابور ميت
                metrics.Failures.Add(1, new("reason", ex.GetType().Name));
                log.LogError(ex, "failed to process ingestion item {ItemId}", item.Id);
            }
        }
    }
}

public sealed record IngestItem(Guid Id, string Kind, string PayloadJson, DateTimeOffset ReceivedAt);

public sealed class IngestionOptions
{
    public int Capacity { get; init; } = 10_000;                      // ★ محدود دائمًا
    public TimeSpan EnqueueTimeout { get; init; } = TimeSpan.FromMilliseconds(500);
    public int Workers { get; init; } = 4;                            // ← bulkhead ضمني على المعالجة
}

public sealed class QueueFullException(int capacity)
    : Exception($"طابور الاستيعاب ممتلئ ({capacity})");

public sealed class IngestionMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Ingest", "1.0.0");
    public Counter<long> Rejections = Meter.CreateCounter<long>("ingest.rejections");
    public Counter<long> Failures   = Meter.CreateCounter<long>("ingest.failures");
    public Counter<long> EnqueueDepth = Meter.CreateCounter<long>("ingest.depth_delta");   // ✓ عمق الطابور (delta)
}

// ── التشغيل كـBackgroundService (درس 2.3.2) ──
public sealed class IngestionWorker(IngestionQueue queue, IngestionOptions options, IngestHandler handler)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        // ★ عدد عمال ثابت = bulkhead على المعالجة (بلا Task.Run لكل عنصر)
        var workers = Enumerable.Range(0, options.Workers)
            .Select(_ => queue.ProcessAsync(handler.HandleAsync, ct))
            .ToArray();

        await Task.WhenAll(workers);
    }
}
'''},
            {"type": "table", "head": ["إعداد وسيط الرسائل", "أثره", "متى تزوّده"], "rows": [
                ["`PrefetchCount` (MassTransit/RabbitMQ)", "كم رسالة محجوزة عند المستهلك قبل المعالجة", "الحمل عالي والعناصر قصيرة → زوّد؛ العناصر ثقيلة/ذاكرة محدودة → قلّل"],
                ["`ConcurrentMessageLimit`", "أقصى معالجة متزامنة **لكل** مستهلك", "التابع بطيء/محدود (bulkhead) → قلّله"],
                ["عدد المستهلكين (instances)", "القدرة الكلية على المعالجة", "عمق الطابور بيكسر باستمرار → زوّد النسخ (HPA في K8s)"],
                ["`QueueLimit` / `Capacity`", "حد الطابور قبل الرفض", "دائمًا محدود — بلا حدود = OOM"],
                ["TTL على الطابور/الرسالة", "رمي الرسائل القديمة بدل معالجتها متأخرة", "أحداث لها صلاحية (أسعار، إشعارات فورية)"],
                ["Dead-letter + إعادة تسليم", "مصير الرسائل الفاشلة", "دائمًا (درس 5.2.1) — بلاها الرسائل بتضيع بصمت"],
            ]},
            {"type": "heading", "level": 2, "text": "6) وثّق القرار: ADR للنمط المختار"},
            {"type": "code", "lang": "text", "filename": "docs/adr/0007-bulkhead-per-tenant.md", "title": "قالب ADR لنمط (قصير، قابل للمراجعة)", "code": r'''
# ADR-0007: عزل التزامن لكل مستأجر (Bulkhead) في Orders API

- الحالة: مقبول
- التاريخ: 2026-10-22
- أصحاب القرار: فريق Orders + فريق المنصة

## السياق (بأرقام، مش بإحساس)
في 2026-10-14 بين 09:10 و09:25، مستأجر واحد (`tenant-77`) بعت 1,900 طلب إنشاء طلب
(مقابل متوسط 60/دقيقة لباقي المستأجرين). النتيجة المقاسة من لوحة Aspire وPrometheus:
- p95 لإنشاء الطلب عبر **كل** المستأجرين: 240ms → 6.8s
- 412 طلب فشلوا بـ504 من الـgateway
- استهلاك pool اتصالات Postgres: 100% (Max Pool Size=100) لمدة 9 دقايق
السبب: مفيش حد على التزامن لكل مستأجر → الطلبات البطيئة احتلت كل الاتصالات.

## القرار
نطبق **Bulkhead** لكل مستأجر بحد 8 عمليات متزامنة و`AcquireTimeout` = 2 ثانية،
والرفض يرجع `429` + `Retry-After: 2` + `application/problem+json`.
بالإضافة لـ**Throttling** لكل مستأجر: 120 طلب/دقيقة (نافذة منزلقة، 6 قطع).

## البدائل المرفوضة
1. **حد عام لكل الخدمة فقط**: ما بيمنعش مستأجر واحد من استهلاك الحصة كلها (وده اللي حصل).
2. **طابور غير متزامن لكل الطلبات**: بيغير عقد الـAPI (متزامن → غير متزامن) ويأثر على كل العملاء.
3. **رفع `Max Pool Size`**: بيأجل المشكلة وينقلها لـDB (درس 3.4.2) — بلا عزل السبب الجذري.
4. **throttling فقط بلا bulkhead**: المعدل ممكن يبقى ضمن الحد لكن بالتزامن الكامل (طلبات طويلة).

## النتائج
**إيجابية:**
- فشل مستأجر واحد ما يعديش لباقي المستأجرين (يُثبت باختبار فشل مُفتعل — درس 5.3.3).
- رفض سريع وواضح (429) بدل timeouts غامضة.

**سلبية / تكلفة:**
- عميل شرعي بيعمل دفعة كبيرة هياخد 429 → محتاج توثيق + دعم `Retry-After` في SDK العميل.
- إعداد إضافي لكل مستأجر (الحدود) → بدأنا بقيمة واحدة وبعدين per-tenant overrides.
- مقياس جديد للمراقبة (`bulkhead.rejections`, `bulkhead.inflight`) وإنذار عند رفض > 1%.

## التحقق (مقاس بعد التطبيق)
- p95 أثناء إعادة تمثيل الحادث: 6.8s → 310ms (باقي المستأجرين غير متأثرين)
- `tenant-77`: 429s واضحة بدل 504s
- الاختبار: `When_tenant_exceeds_concurrency_other_tenants_are_unaffected` (أخضر في CI)

## مراجعة
تُراجع الحدود كل ربع سنة مقابل الحمل الفعلي، أو فورًا لو `bulkhead.rejections` > 1% من الطلبات.
'''},
            {"type": "callout", "kind": "danger", "title": "8 أخطاء في تطبيق الأنماط (بتحوّل الحل لمشكلة)",
             "md": """
1. **الكاش كمصدر حقيقة**: لو فقدان الكاش بيعطّل الخدمة، ده مش كاش — ده قاعدة بيانات بلا متانة. اختبر fail-open.
2. **Bulkhead بلا timeout على الانتظار**: الطابور بيكبر لحد استهلاك الذاكرة. الرفض السريع أفضل من الانتظار الطويل.
3. **Circuit breaker واحد لكل التبعيات**: تابع واحد بطيء بيفتح الدايرة على الكل. breaker **لكل تابع** (درس 5.2.4).
4. **Throttling بلا `Retry-After`**: العملاء بيعيدوا المحاولة فورًا → الذروة بتتكرر.
5. **طابور بلا حد أقصى**: بلا `Capacity`/`QueueLimit`، الذروة بتتحول لـOOM بدل رفض واضح.
6. **نمط بلا مقياس**: لو مش بتقيس hit rate / rejections / breaker state، مش هتعرف إنه شغال أو إنه بيضر.
7. **أنماط متراكمة بلا حاجة**: retry + breaker + bulkhead + hedging + fallback على نداء داخلي بسيط =
   تعقيد وأعطال جديدة (زي «retry داخل retry» في درس 5.2.4). طبّق النمط لما **القياس** يثبت المشكلة.
8. **نسخ كود من مقال بلا فهم الوسائط**: `PermitLimit=12` من أين؟ من قياس p95 وقدرة التابع — مش رقم سحري.

✅ **اختبار سريع لأي نمط طبقته**: «لو المكوّن ده فشل/امتلى، إيه اللي بيحصل للمستخدم؟» —
لو الإجابة «مش عارف»، النمط ناقص (مقياس/رفض واضح/fallback/توثيق).
"""},
            {"type": "checkpoints", "items": [
                "أختار النمط من مشكلة **مقاسة** (جدول الاختيار)، وأعرف تكلفة كل نمط وأرفض ما لا أحتاجه.",
                "أنفّذ Cache-aside بـ`IHybridCache`: وسوم إبطال، TTL + jitter، حماية stampede، fail-open، وحماية penetration.",
                "أنفّذ Bulkhead لكل تابع ولكل مستأجر بحدود تزامن وطوابير محدودة وtimeout ورفض صريح (429).",
                "أنفّذ Throttling مقسّمًا بالمستأجر (نافذة منزلقة + token bucket + حد عام) مع `Retry-After` وproblem+json.",
                "أنفّذ Queue-based load leveling بطابور محدود + backpressure + عمال ثابتين + مقاييس عمق الطابور.",
                "أوثّق كل نمط في ADR بأرقام من السياق وبدائل مرفوضة ونتائج مُقاسة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "في Cache-aside، عند الكتابة بنعمل إيه؟",
                 "options": [
                     "نحدّث الكاش ثم المصدر",
                     "نكتب للمصدر ثم **نبطل** مدخلات الكاش (invalidate) — التحديث المتزامن من نسختين بيسبب بيانات قديمة دائمة",
                     "نكتب للكاش فقط",
                     "ما نلمسش الكاش ونسيب TTL",
                 ], "answer": 1,
                 "explain": "الإبطال أبسط وآمن. وسيب TTL كحد أقصى لعمر البيانات القديمة، مع jitter عشان المفاتيح ما تنتهيش كلها في نفس اللحظة."},
                {"q": "فرق Throttling عن Bulkhead؟",
                 "options": [
                     "مفيش فرق",
                     "Throttling بيحدّ **المعدل** (طلبات/فترة) · Bulkhead بيحدّ **التزامن** (كم عملية شغالة دلوقتي) — والاتنين مطلوبين",
                     "Bulkhead للشبكة فقط",
                     "Throttling للتبعيات الخارجية فقط",
                 ], "answer": 1,
                 "explain": "معدل ضمن الحد بتزامن كامل = طوابير/استهلاك موارد. وتزامن منخفض بمعدل عالي = رفض كتير. الحماية الكاملة تحتاج الاتنين."},
                {"q": "ليه `BoundedChannelOptions.FullMode.Wait` + `EnqueueTimeout` بدل طابور غير محدود؟",
                 "options": [
                     "أداء أفضل",
                     "الطابور غير المحدود بيحوّل الذروة لاستهلاك ذاكرة بلا نهاية (OOM)؛ المحدود + timeout بيدي **backpressure** واضح (رفض 429/503)",
                     "مطلوب من Channel",
                     "عشان المقاييس",
                 ], "answer": 1,
                 "explain": "الرفض السريع والواضح أفضل من الانهيار البطيء. وبلّغ العميل بـ429 + `Retry-After` عشان يعدّل معدله."},
                {"q": "مستأجر واحد بعت 30 ضعف المعدل الطبيعي. حد عام واحد (global limiter) كفاية؟",
                 "options": [
                     "نعم، ده الغرض منه",
                     "لا — لازم تقسيم لكل مستأجر/عميل (partitioned)، وإلا المستأجر المسيء هيستهلك الحصة العامة ويحرم الباقي (bulkhead + throttling لكل مستأجر)",
                     "كفاية لو زاد الحد",
                     "كفاية مع retry",
                 ], "answer": 1,
                 "explain": "الحد العام حماية أخيرة. الحماية الحقيقية بتقسيم الموارد/المعدلات لكل مستأجر — وده اللي بيثبته الـADR في الدرس."},
                {"q": "Circuit breaker واحد مشترك لكل التبعيات الخارجية. المشكلة؟",
                 "options": [
                     "مفيش مشكلة (أبسط)",
                     "تابع واحد فاشل بيفتح الدايرة على **كل** التبعيات → نداءات صحية بتُرفض. breaker لكل تابع بإعداداته الخاصة",
                     "بيستهلك ذاكرة",
                     "ما بيشتغلش مع retry",
                 ], "answer": 1,
                 "explain": "كل تابع له ميزانية مهلة وحد فشل مختلف (درس 5.2.4). العزل ده هو نفسه فكرة الـbulkhead مطبقة على الفشل."},
                {"q": "طبقت 4 أنماط (retry + breaker + bulkhead + hedging) على نداء داخلي سريع. التقييم؟",
                 "options": [
                     "ممتاز — حماية قصوى",
                     "over-engineering: كل نمط تكلفة وتعقيد وفشل جديد محتمل. طبّق النمط لما **قياس** يثبت المشكلة",
                     "ينقصه fallback",
                     "ينقصه timeout",
                 ], "answer": 1,
                 "explain": "القاعدة: نمط واحد لكل مشكلة مقاسة. تكديس الأنماط بيولد تفاعلات غريبة (مثل retry داخل retry) وبيصعّب التشخيص."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "3 أنماط مطبقة ومقاسة + ADR لكل واحد",
                 "md": "اختار 3 أنماط من الجدول (منها Cache-aside وBulkhead أو Throttling إلزاميًا) وطبّقهم في مشروعك على مشكلة **مقاسة فعلًا**، واكتب ADR لكل نمط بالسياق الرقمي والبدائل المرفوضة والنتائج بعد التطبيق.",
                 "criteria": [
                     "لكل نمط: دليل رقمي على المشكلة **قبل** التطبيق (لقطة/مقياس/لوج من اللوحة أو Prometheus)",
                     "تنفيذ كامل بالكود: Cache-aside (إبطال بوسوم + TTL+jitter + fail-open) · Bulkhead (حد + طابور محدود + timeout + 429) · Throttling (تقسيم مستأجر + `Retry-After` + problem+json)",
                     "مقياس لكل نمط (`cache.hit/miss`, `bulkhead.rejections/inflight`, `gateway.rate_limit.rejections`) معروض في اللوحة",
                     "اختبار لكل نمط: فقدان الكاش → الخدمة ترد (أبطأ) · تجاوز التزامن لمستأجر → مستأجر تاني غير متأثر · تجاوز المعدل → 429 مع `Retry-After`",
                     "3 ملفات ADR بالقالب (سياق بأرقام · قرار · بدائل مرفوضة · نتائج · مراجعة)",
                     "الوسائط مبررة (من أين جاء `PermitLimit=8`؟) — مش أرقام منسوخة",
                     "جدول «الأنماط المرفوضة»: نمط × سبب الرفض (دليل إنك اخترت بوعي)",
                 ],
                 "hint": "ابدأ بالقياس: شغّل k6 أو 50 طلب متزامن وشوف p95 ومقاييسك، وبعدين طبّق النمط وقِس تاني. الفرق الرقمي هو محتوى الـADR.",
                 "solution": "",
                 "resources": [
                     {"label": "Azure Architecture Center — Cloud design patterns", "url": "https://learn.microsoft.com/azure/architecture/patterns/"},
                     {"label": "Cache-Aside pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/cache-aside"},
                     {"label": "Bulkhead pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/bulkhead"},
                 ]},
                {"id": "t2", "title": "اختبار فشل مُفتعل يثبت إن الأنماط شغالة",
                 "md": "ابنِ سيناريو اختبار (في Aspire أو slice) يفتعل حملًا/فشلًا ويثبت إن كل نمط بيشتغل زي ما هو موثق: امتلاء الطابور، تشبع الـbulkhead، فتح الـbreaker، إبطال الكاش بعد الكتابة، ورفض المعدل. كل سيناريو بيتحقق من **سلوك المستخدم** (كود الحالة/الجسم/الرؤوس) مش من اللوجات فقط.",
                 "criteria": [
                     "5 سيناريوهات: queue full · tenant saturation · breaker open · cache invalidation بعد الكتابة · rate limit exceeded",
                     "كل سيناريو بيتحقق من كود الحالة + `Retry-After`/`X-Degraded` + جسم problem+json (حيث ينطبق)",
                     "كل سيناريو بيتحقق من **عدم تعدّي الضرر**: مستأجر/تابع تاني غير متأثر (assertion صريح)",
                     "حقن العطل عبر مفاتيح تكوين (Development/test فقط) — بلا تعديل كود الإنتاج وقت الاختبار",
                     "المقاييس بتتغير كما هو متوقع (assert على العدادات حيث ممكن)",
                     "الاختبارات مستقرة: 3 تشغيلات متتالية خضرا (بلا `Task.Delay` ثابت)",
                     "فقرة في `docs/patterns.md`: لكل نمط — إزاي أتأكد إنه شغال في الإنتاج (مقياس + إنذار)",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Circuit Breaker pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker"},
                     {"label": "Throttling pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/throttling"},
                     {"label": "Queue-Based Load Leveling pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Azure Architecture Center — design patterns", "url": "https://learn.microsoft.com/azure/architecture/patterns/"},
                {"label": "Cache-Aside pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/cache-aside"},
                {"label": "Bulkhead pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/bulkhead"},
                {"label": "Circuit Breaker pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker"},
                {"label": "Throttling pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/throttling"},
                {"label": "Queue-Based Load Leveling pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling"},
                {"label": "Rate limiting in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/rate-limit"},
                {"label": "HybridCache in .NET", "url": "https://learn.microsoft.com/dotnet/core/extensions/hybridcache"},
            ]},
        ],
    },
]
