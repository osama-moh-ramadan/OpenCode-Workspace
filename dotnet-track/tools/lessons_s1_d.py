"""Stage 1, Module 2 — Testing (lessons 4-6 of 6): integration harness, Testcontainers, data & coverage."""

TODAY = "2026-10-22"

LESSONS_S1_D = [
    # ------------------------------------------------------------------ l4
    {
        "id": "s1-m2-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
اختبارات الـUnit بتأكد إن **منطقك** صح. لكنها ما بتأكدش إن: الـrouting وصل للـendpoint الصح،
الـvalidation اشتغل، الـauthorization رفض الطلب، الـmodel binding فكّ الـJSON، الـEF ترجم الاستعلام،
والـserialization رجّع الشكل المتفق عليه. كل دول بيحصلوا في **الـpipeline الحقيقي** — وده بالظبط
اللي `WebApplicationFactory` بيشغّله في الذاكرة: تطبيقك كامل، بدون نشر، مع `HttpClient` حقيقي.

الدرس ده: تبني harness واحد نظيف، تبدّل فيه التبعيات (قاعدة البيانات، المصادقة، الخدمات الخارجية)،
وتكتب اختبارات تغطي النجاح والفشل والصلاحيات.
"""},
            {"type": "terms", "items": [
                {"term": "WebApplicationFactory<TEntryPoint>", "def": "بيشغّل تطبيقك (Kestrel في الذاكرة/test server) ويعطيك `HttpClient` مربوط بيه."},
                {"term": "ConfigureTestServices", "def": "آخر تسجيل في DI — عشان كده بيتجاوز تسجيلات التطبيق الحقيقية (مهم جدًا)."},
                {"term": "RemoveAll<T>", "def": "يمسح كل التسجيلات لنوع معين قبل ما تسجل بديلك (مثال: DbContextOptions)."},
                {"term": "WithWebHostBuilder", "def": "ينسخ الـfactory بإعدادات مختلفة لاختبار معين (بدون تلويث الباقي)."},
                {"term": "TestAuthHandler", "def": "مخطط مصادقة للاختبارات يتحكم في الهوية والـclaims — عشان تختبر 401/403/200 بمزاجك."},
                {"term": "IAsyncLifetime", "def": "بدء/إنهاء غير متزامن للـfixture (تشغيل container، ترحيل قاعدة، بذر بيانات)."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزمة المطلوبة", "code": r'''
dotnet add Shop.Tests package Microsoft.AspNetCore.Mvc.Testing
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs (آخر الملف)", "title": "خطوة صغيرة ضرورية: اجعل Program مرئيًا للاختبارات", "code": r'''
// top-level statements بتولّد كلاس Program داخلي (internal).
// أضف السطر ده في آخر Program.cs عشان WebApplicationFactory<Program> تشتغل:
public partial class Program;
'''},
            {"type": "heading", "level": 2, "text": "الـHarness: factory واحد لكل الاختبارات"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/CustomWebApplicationFactory.cs", "title": "بيئة Testing + استبدال قاعدة البيانات + المصادقة", "code": r'''
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

public sealed class CustomWebApplicationFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    // SQLite في الذاكرة محتاج اتصال مفتوح طول عمر الـfactory
    private SqliteConnection? _connection;

    public Guid SeededCustomerId { get; private set; }
    public Guid SeededProductId { get; private set; }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");          // ← appsettings.Testing.json لو موجود

        builder.ConfigureTestServices(services =>
        {
            // 1) امسح تسجيلات قاعدة البيانات الحقيقية
            services.RemoveAll(typeof(DbContextOptions<AppDbContext>));
            services.RemoveAll<AppDbContext>();

            _connection = new SqliteConnection("DataSource=:memory:");
            _connection.Open();
            services.AddDbContext<AppDbContext>(o => o.UseSqlite(_connection));

            // 2) أي خدمة خارجية → fake (لا شبكة في الاختبارات)
            services.RemoveAll<IPaymentGateway>();
            services.AddSingleton<IPaymentGateway, FakePaymentGateway>();

            services.RemoveAll<IOrderNotifier>();
            services.AddSingleton<IOrderNotifier, RecordingNotifier>();

            // 3) المصادقة: مخطط اختباري نتحكم في هويته
            services.AddAuthentication("Test")
                    .AddScheme<AuthenticationSchemeOptions, TestAuthHandler>("Test", _ => { });
            services.AddAuthorization();           // السياسات الحقيقية تفضل شغالة

            // 4) إبطال أي BackgroundService بيستهلك موارد أو بيلخبط البيانات
            services.RemoveAll<IHostedService>();
        });
    }

    public async ValueTask InitializeAsync()
    {
        await using var scope = Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        await db.Database.MigrateAsync();           // ✓ نفس مسار الإنتاج

        // بيانات أساسية ثابتة لكل الاختبارات
        var customer = new Customer { Id = Guid.NewGuid(), Email = "seed@example.com", Country = "EG" };
        var product = new Product { Id = Guid.NewGuid(), Name = "Widget", Price = 100m, Stock = 50 };
        db.Customers.Add(customer);
        db.Products.Add(product);
        await db.SaveChangesAsync();

        SeededCustomerId = customer.Id;
        SeededProductId = product.Id;
    }

    public async ValueTask DisposeAsync()
    {
        if (_connection is not null) await _connection.DisposeAsync();
    }

    /// <summary>عميل بإعدادات صريحة: بدون redirect تلقائي عشان نقرأ 302/401 بصدق.</summary>
    public HttpClient CreateAuthenticatedClient(params string[] roles)
    {
        TestAuthHandler.NextUser = new TestUser("test-user", roles);
        return CreateClient(new WebApplicationFactoryClientOptions
        {
            AllowAutoRedirect = false,
            HandleCookies = true,
        });
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/TestAuthHandler.cs", "title": "مصادقة اختبارية قابلة للتحكم (مش إلغاء للأمان)", "code": r'''
using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

public sealed record TestUser(string Id, IReadOnlyList<string> Roles);

public sealed class TestAuthHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder)
    : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    /// <summary>null = مستخدم مجهول (يُنتج 401).</summary>
    public static TestUser? NextUser { get; set; }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (NextUser is null) return Task.FromResult(AuthenticateResult.NoResult());

        var claims = new List<Claim> { new(ClaimTypes.NameIdentifier, NextUser.Id) };
        claims.AddRange(NextUser.Roles.Select(r => new Claim(ClaimTypes.Role, r)));

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var principal = new ClaimsPrincipal(identity);
        return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(principal, Scheme.Name)));
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "خلي بالك",
             "md": """
- `ConfigureTestServices` بيتنفّذ **بعد** تسجيلات التطبيق، فبيكسب. لو استخدمت `ConfigureServices` عادي ممكن ترتيبك يتلخبط.
- **لا تختبر على قاعدة الإنتاج**. أبدًا. الـfactory لازم يبدّل الـconnection string.
- `services.RemoveAll<IHostedService>()` مهم: أي worker بيشتغل وقت الاختبارات بيلخبط البيانات وبيبطّئ.
- اختبارات الـAPI **بتشارك حالة** قاعدة البيانات — استخدم معرّفات فريدة لكل اختبار، أو عطّل التوازي (`[Collection]`).
- الـ`TestAuthHandler` بيحاكي الهوية بس؛ **السياسات (`[Authorize(Policy=…)]`) تفضل مُطبَّقة**، وده المقصود.
"""},
            {"type": "heading", "level": 2, "text": "الاختبارات نفسها"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/OrdersApiTests.cs", "title": "نجاح + تحقق + مجهول + ممنوع", "code": r'''
[Collection("Api")]                                  // مشاركة factory واحدة بلا توازي
public sealed class OrdersApiTests(CustomWebApplicationFactory factory)
{
    [Fact]
    public async Task POST_orders_as_customer_returns_201_and_persists()
    {
        var client = factory.CreateAuthenticatedClient("customer");

        var response = await client.PostAsJsonAsync("/api/orders", new
        {
            customerId = factory.SeededCustomerId,
            lines = new[] { new { productId = factory.SeededProductId, quantity = 2, unitPrice = 100m } },
        });

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<OrderCreatedResponse>();
        body!.Id.Should().NotBeEmpty();

        // الأثر في قاعدة البيانات — مش بس الاستجابة
        await using var scope = factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var order = await db.Orders.Include(o => o.Lines).SingleAsync(o => o.Id == body.Id);
        order.Total.Should().Be(228m);
        order.Lines.Should().HaveCount(1);
    }

    [Fact]
    public async Task POST_orders_with_invalid_quantity_returns_400_problem_json()
    {
        var client = factory.CreateAuthenticatedClient("customer");

        var response = await client.PostAsJsonAsync("/api/orders", new
        {
            customerId = factory.SeededCustomerId,
            lines = new[] { new { productId = factory.SeededProductId, quantity = 0, unitPrice = 100m } },
        });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/problem+json");

        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemDetails>();
        problem!.Errors.Should().ContainKey(k => k.Contains("Quantity"));
        response.Headers.GetValues("X-Correlation-Id").Single().Should().NotBeNullOrWhiteSpace();
    }

    [Fact]
    public async Task POST_orders_anonymously_returns_401()
    {
        var client = factory.CreateClient();          // TestAuthHandler.NextUser = null

        var response = await client.PostAsJsonAsync("/api/orders", new { customerId = factory.SeededCustomerId });

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task DELETE_order_as_customer_returns_403()
    {
        var client = factory.CreateAuthenticatedClient("customer");   // الدور المطلوب: admin

        var response = await client.DeleteAsync("/api/orders/" + Guid.NewGuid());

        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }

    [Fact]
    public async Task GET_unknown_order_returns_404_with_traceId()
    {
        var client = factory.CreateAuthenticatedClient("customer");

        var response = await client.GetAsync($"/api/orders/{Guid.NewGuid()}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Extensions.Should().ContainKey("traceId");
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/PerTestOverrides.cs", "title": "إعداد مختلف لاختبار واحد بدون تلويث الباقي", "code": r'''
public sealed class TimeoutBehaviourTests(CustomWebApplicationFactory factory)
{
    [Fact]
    public async Task Payment_gateway_timeout_returns_504_problem()
    {
        var client = factory.WithWebHostBuilder(builder => builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<IPaymentGateway>();
            services.AddSingleton<IPaymentGateway, HangingPaymentGateway>();   // بيرمي TimeoutException
        })).CreateAuthenticatedClient("customer");

        var response = await client.PostAsJsonAsync($"/api/orders/{Guid.NewGuid()}/pay", new { amount = 100m });

        response.StatusCode.Should().Be(HttpStatusCode.GatewayTimeout);
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Title.Should().Be("تعذّر إتمام الدفع");
    }
}
'''},
            {"type": "table", "head": ["عايز تختبر", "التقنية"], "rows": [
                ["مسار نجاح عبر الـpipeline", "`factory.CreateClient()` + POST/GET حقيقي"],
                ["عقد الأخطاء (problem+json)", "اقرأ `ProblemDetails`/`ValidationProblemDetails` من الجسم"],
                ["الصلاحيات (401/403)", "`TestAuthHandler` بأدوار مختلفة"],
                ["سلوك تحت فشل تبعية", "`WithWebHostBuilder` + fake بيرمي الاستثناء المطلوب"],
                ["الأثر على البيانات", "scope من `factory.Services` واقرأ من `DbContext`"],
                ["رؤوس/كاش/حدود", "`WebApplicationFactoryClientOptions` + فحص `response.Headers`"],
            ]},
            {"type": "checkpoints", "items": [
                "أبني `CustomWebApplicationFactory` يبدّل قاعدة البيانات والمصادقة والخدمات الخارجية.",
                "أكتب اختبارات تغطي 201 و400 و401 و403 و404 على endpoint واحد.",
                "أستخدم `WithWebHostBuilder` لاختبار سلوك فشل تبعية معينة.",
                "أتحقق من الأثر في قاعدة البيانات مش من الاستجابة فقط.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `ConfigureTestServices` مش `ConfigureServices` في الـfactory؟",
                 "options": [
                     "أسرع",
                     "بيتسجّل بعد خدمات التطبيق فيكسب الاستبدال",
                     "بيدعم SQLite فقط",
                     "بيتجاهل المصادقة تلقائيًا",
                 ], "answer": 1,
                 "explain": "ترتيب التسجيل بيحدد الفائز للخدمات من نفس النوع. `ConfigureTestServices` هو آخر خطوة في بناء الحاوية."},
                {"q": "SQLite in-memory مع EF Core: إيه الشرط اللي الناس بتنساه؟",
                 "options": [
                     "لازم تشغّل `Migrate` مرتين",
                     "لازم تفضل `SqliteConnection` مفتوحة طول عمر الاختبارات، وإلا القاعدة بتختفي",
                     "لازم تستخدم `EnsureCreated` فقط",
                     "لازم تعمل Docker",
                 ], "answer": 1,
                 "explain": "قاعدة `:memory:` موجودة طالما الاتصال مفتوح. لو قفل، اختفت البيانات — عشان كده الـconnection يعيش في الـfixture."},
                {"q": "اختبارك نجح محليًا بيفشل في CI بشكل متقطع. أرجح سبب؟",
                 "options": [
                     "CI أبطأ",
                     "اختبارات بتشارك قاعدة بيانات واحدة بالتوازي وبتلخبط بيانات بعض",
                     "الإصدارات مختلفة",
                     "الحزم ناقصة",
                 ], "answer": 1,
                 "explain": "xUnit بيشغّل collections بالتوازي. استخدم `[Collection(\"Api\")]` لكل الكلاسات المشتركة في factory، أو `DisableParallelization`، أو اعزل البيانات بمعرّفات فريدة."},
                {"q": "إيه الفائدة من `AllowAutoRedirect = false` في `CreateClient`؟",
                 "options": [
                     "تسريع الاختبارات",
                     "تشوف 301/302 الحقيقية بدل ما العميل يتبعها وتخفي النتيجة",
                     "تعطيل الكوكيز",
                     "تجاوز HTTPS",
                 ], "answer": 1,
                 "explain": "الافتراضي يتبع التحويلات، فاختبار «HTTP يتحول لـHTTPS» مثلًا هيفقد معناه."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "Harness كامل لـAPI عندك",
                 "md": "ابنِ `CustomWebApplicationFactory` لمشروعك مع: SQLite/Testcontainers، استبدال الخدمات الخارجية بـfakes، `TestAuthHandler`، وإبطال الـhosted services. وبعدين اكتب 5 اختبارات: نجاح، 400، 401، 403، 404.",
                 "criteria": [
                     "مفيش أي طلب شبكة أو خدمة خارجية أثناء الاختبارات (افصل النت وجرّب)",
                     "الاختبارات الخمسة ناجحة ومتكررة (شغّلها 3 مرات)",
                     "اختبار واحد على الأقل بيتحقق من الأثر في قاعدة البيانات",
                     "اختبار واحد بيتحقق من `application/problem+json` و`traceId`",
                 ],
                 "hint": "لو ظهر خطأ `Unable to find type Program` أضف `public partial class Program;` في آخر Program.cs، ولو `InvalidOperationException: No service for type` راجع `RemoveAll` قبل `Add`."},
                {"id": "t2", "title": "اختبار فشل تبعية",
                 "md": "باستخدام `WithWebHostBuilder`، اجعل بوابة الدفع ترمي `TimeoutException` وأكد إن الـAPI بيرجع 504 (مش 500) مع problem+json.",
                 "criteria": [
                     "الكود بيتعامل مع الاستثناء ويترجمه لـ504",
                     "الاختبار يفشل لو رجّعت الحالة لـ500",
                     "ما أثّرتش على بقية الاختبارات (التجاوز محلي)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Integration tests in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/test/integration-tests"},
                {"label": "WebApplicationFactory API", "url": "https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.mvc.testing.webapplicationfactory-1"},
                {"label": "Testing authorization", "url": "https://learn.microsoft.com/aspnet/core/security/authorization/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l5
    {
        "id": "s1-m2-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
اختبارات EF Core على `InMemory` provider بتكذب عليك: مفيش transactions حقيقية، مفيش قيود (unique/FK/check)،
الـraw SQL ما بيشتغلش، وترجمة LINQ بتختلف. وSQLite أقرب — لكنها لسه مش Postgres/SQL Server
(الفهارس، أنواع JSON، السلوك تحت التزامن).

**Testcontainers** بيحل المسألة دي: يشغّل قاعدة بيانات **حقيقية** في Docker، ويعطيك connection string،
وينضّف وراها. نفس الفكرة لـRedis وRabbitMQ وKafka — أي تبعية كانت بتخليك تكتب mocks كاذبة.
"""},
            {"type": "terms", "items": [
                {"term": "Testcontainers", "def": "مكتبة تبني وتشغّل حاويات مُدارة من داخل الاختبارات (Docker API مباشرة، بلا docker-compose)."},
                {"term": "PostgreSqlBuilder", "def": "وحدة جاهزة لحاوية Postgres مع ضبط الصورة وقاعدة البيانات والمستخدم."},
                {"term": "Ryuk", "def": "حاوية جانبية تنظّف الحاويات المتبقية لو الاختبارات اتقتلت فجأة."},
                {"term": "Resource reuse", "def": "`WithReuse(true)` لإعادة استخدام نفس الحاوية بين تشغيلات — أسرع تطويرًا (انتبه للبيانات المتبقية)."},
                {"term": "Respawn", "def": "مكتبة تصفّر جداول قاعدة البيانات بين الاختبارات بسرعة (بدل إعادة إنشاء الحاوية)."},
                {"term": "IAsyncLifetime", "def": "بدء/إنهاء غير متزامن — المكان الطبيعي لتشغيل الحاوية وإيقافها."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم والمتطلبات", "code": r'''
# المتطلب: Docker شغال (Docker Desktop على Windows/macOS، أو Docker Engine على Linux)
docker info

# الحزم
dotnet add Shop.Tests package Testcontainers.PostgreSql
dotnet add Shop.Tests package Testcontainers.Redis        # اختياري
dotnet add Shop.Tests package Testcontainers.RabbitMq     # اختياري
dotnet add Shop.Tests package Respawn                     # اختياري: تصفير سريع
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/PostgresFixture.cs", "title": "حاوية حقيقية + ترحيل EF + تصفير بين الاختبارات", "code": r'''
using Respawn;
using Testcontainers.PostgreSql;

public sealed class PostgresFixture : IAsyncLifetime
{
    private readonly PostgreSqlContainer _db = new PostgreSqlBuilder()
        .WithImage("postgres:17-alpine")
        .WithDatabase("shop_tests")
        .WithUsername("test")
        .WithPassword("test")
        .WithCleanUp(true)            // Ryuk ينظّف لو العملية اتقتلت
        .Build();

    private Respawner? _respawner;

    public string ConnectionString => _db.GetConnectionString();

    public async ValueTask InitializeAsync()
    {
        await _db.StartAsync();

        await using var ctx = CreateContext();
        await ctx.Database.MigrateAsync();          // ✓ نفس migrations الإنتاج

        _respawner = await Respawner.CreateAsync(ConnectionString, new RespawnerOptions
        {
            DbAdapter = DbAdapter.Postgres,
            SchemasToInclude = ["public"],
        });
    }

    public async ValueTask DisposeAsync() => await _db.DisposeAsync();

    public AppDbContext CreateContext() =>
        new(new DbContextOptionsBuilder<AppDbContext>().UseNpgsql(ConnectionString).Options);

    /// <summary>نادِ عليها في بداية كل اختبار: قاعدة نظيفة بأقل تكلفة.</summary>
    public async Task ResetAsync()
    {
        if (_respawner is not null) await _respawner.ResetAsync(ConnectionString);
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/OrderQueryTests.cs", "title": "اختبارات تعتمد على سلوك Postgres الحقيقي", "code": r'''
[Collection("Postgres")]
public sealed class OrderQueryTests(PostgresFixture db) : IAsyncLifetime
{
    public ValueTask InitializeAsync() => new(db.ResetAsync().AsTask());
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;

    [Fact]
    public async Task Unique_email_constraint_is_enforced()
    {
        // ده اختبار مستحيل على InMemory provider: قيد فريد في قاعدة البيانات
        await using (var ctx = db.CreateContext())
        {
            ctx.Customers.Add(new Customer { Id = Guid.NewGuid(), Email = "dup@example.com" });
            await ctx.SaveChangesAsync();
        }

        await using var second = db.CreateContext();
        second.Customers.Add(new Customer { Id = Guid.NewGuid(), Email = "dup@example.com" });

        var act = () => second.SaveChangesAsync();

        await act.Should().ThrowAsync<DbUpdateException>();
    }

    [Fact]
    public async Task Projection_translates_to_sql_and_returns_only_needed_columns()
    {
        await using var ctx = db.CreateContext();
        ctx.Orders.AddRange(
            AnOrder.WithCountry("EG").WithTotal(228m).Build(),
            AnOrder.WithCountry("SA").WithTotal(230m).Build());
        await ctx.SaveChangesAsync();

        var totals = await ctx.Orders
            .GroupBy(o => o.Customer.Country)
            .Select(g => new { Country = g.Key, Sum = g.Sum(o => o.Total) })
            .OrderByDescending(x => x.Sum)
            .ToListAsync();

        totals.Should().HaveCount(2);
        totals[0].Sum.Should().Be(230m);
    }

    [Fact]
    public async Task ExecuteUpdateAsync_updates_rows_without_loading_them()
    {
        await using var ctx = db.CreateContext();
        ctx.Orders.AddRange([..Enumerable.Range(0, 5).Select(_ => AnOrder.WithStatus(OrderStatus.Abandoned).Build())]);
        await ctx.SaveChangesAsync();

        var affected = await ctx.Orders
            .Where(o => o.Status == OrderStatus.Abandoned)
            .ExecuteUpdateAsync(s => s.SetProperty(o => o.Status, OrderStatus.Cancelled));

        affected.Should().Be(5);
    }
}
'''},
            {"type": "callout", "kind": "note", "title": "ربط الحاوية بـWebApplicationFactory",
             "md": """
بدل SQLite في درس الـIntegration، بدّل التسجيل في `CustomWebApplicationFactory` لـPostgres:
```csharp
public sealed class CustomWebApplicationFactory(PostgresFixture db)
    : WebApplicationFactory<Program>, IAsyncLifetime
{
    protected override void ConfigureWebHost(IWebHostBuilder builder) =>
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll(typeof(DbContextOptions<AppDbContext>));
            services.AddDbContext<AppDbContext>(o => o.UseNpgsql(db.ConnectionString));
        });

    public ValueTask InitializeAsync() => new(db.ResetAsync().AsTask());
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;
}
```
والأفضل: حاوية واحدة لكل مجموعة الاختبارات (assembly fixture) عشان ما تدفعش تكلفة الإقلاع لكل كلاس.
"""},
            {"type": "heading", "level": 2, "text": "تبعيات تانية: Redis وRabbitMQ"},
            {"type": "code", "lang": "csharp", "title": "حاويات جاهزة لأي تبعية", "code": r'''
// Redis: اختبار IDistributedCache / rate limiting / distributed lock حقيقيًا
var redis = new RedisBuilder().WithImage("redis:7-alpine").Build();
await redis.StartAsync();
services.AddSingleton<IConnectionMultiplexer>(ConnectionMultiplexer.Connect(redis.GetConnectionString()));

// RabbitMQ: اختبار نشر/استهلاك حدث حقيقي (MassTransit in-memory بديل أبسط للاختبارات السريعة)
var rabbit = new RabbitMqBuilder().WithImage("rabbitmq:3-management-alpine").Build();
await rabbit.StartAsync();
var amqp = rabbit.GetConnectionString();      // amqp://guest:guest@localhost:<port>
'''},
            {"type": "table", "head": ["المزوّد", "السرعة", "الدقة", "إمتى تستخدمه"], "rows": [
                ["EF InMemory", "الأعلى", "منخفضة — مفيش transactions/قيود/SQL", "اختبارات منطق صرف لا تلمس SQL (نادراً)"],
                ["SQLite (ملف/ذاكرة)", "عالية", "متوسطة — SQL حقيقي لكن ليس مزوّدك", "تطوير سريع واختبارات CRUD بسيطة"],
                ["Testcontainers (Postgres/SQL Server)", "متوسطة (ثوانٍ للإقلاع)", "عالية — نفس محرك الإنتاج", "أي اختبار يعتمد على SQL/قيود/أداء/ترحيلات"],
            ]},
            {"type": "callout", "kind": "warn", "title": "تكلفة وأداء",
             "md": """
- **أول تشغيل بيسحب الصور** (مئات الميجابايت): اسحبها مسبقًا في الـCI (`docker pull postgres:17-alpine`) وخبّئها (cache).
- **حاوية واحدة لكل الـassembly** (assembly fixture) بدل حاوية لكل كلاس — الفرق ثواني × عدد الكلاسات.
- `WithReuse(true)` بيسرّع التطوير المحلي، لكنه **بيسيب بيانات من التشغيل السابق**: لا تستخدمه مع اختبارات حساسة للبيانات.
- **لا تشغّل اختبارات بالتوازي على نفس الحاوية** من غير عزل (Respawn قبل كل اختبار + معرّفات فريدة).
- علّمها `[Trait(\"Category\",\"Integration\")]` عشان تتفادى تشغيلها في كل حفظ.
"""},
            {"type": "checkpoints", "items": [
                "أشغّل Postgres حقيقي في اختباراتي بـTestcontainers مع `MigrateAsync`.",
                "أستخدم Respawn لتصفير البيانات بين الاختبارات بدل إعادة إنشاء الحاوية.",
                "أختبر سلوكًا يعتمد على قاعدة البيانات فعلًا (قيود، ترجمة LINQ، ExecuteUpdate).",
                "أربط الحاوية بـWebApplicationFactory وأتحكم في التوازي والتكلفة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "أنهي اختبار **يستحيل** ينجح بشكل صحيح على EF InMemory provider؟",
                 "options": [
                     "حفظ كيان وقراءته",
                     "التحقق من إن قيد Unique على Email بيسبب `DbUpdateException`",
                     "اختبار سياسة خصم على كيان",
                     "اختبار validator",
                 ], "answer": 1,
                 "explain": "InMemory ما بتطبقش قيود قاعدة البيانات. ده بالظبط نوع الباج اللي بيظهر في الإنتاج بس."},
                {"q": "إيه وظيفة Ryuk في Testcontainers؟",
                 "options": [
                     "يسرّع الاستعلامات",
                     "ينظّف الحاويات المتبقية لو عملية الاختبار اتقتلت فجأة",
                     "يشفّر الاتصال",
                     "يدير الـmigrations",
                 ], "answer": 1,
                 "explain": "حاوية جانبية بتتبع الموارد اللي أنشأتها المكتبة وتوقفها لو العملية الأم اختفت — عشان ما تفضلش حاويات تأكل موارد جهازك."},
                {"q": "الاختبارات بقت بطيئة (30 ثانية). أنهي إصلاح له أكبر أثر؟",
                 "options": [
                     "زيادة `maxParallelThreads` مع قاعدة مشتركة",
                     "حاوية واحدة لكل الـassembly + Respawn بين الاختبارات بدل حاوية لكل كلاس",
                     "حذف الاختبارات",
                     "استخدام InMemory لكل حاجة",
                 ], "answer": 1,
                 "explain": "تكلفة إقلاع الحاوية هي الغالبة. مشاركتها + تصفير سريع للبيانات بيوفر أغلب الوقت. (زيادة التوازي على قاعدة مشتركة بيسبب تعارض.)"},
                {"q": "`WithReuse(true)` — إمتى يكون خطر؟",
                 "options": [
                     "في الـCI",
                     "لما الاختبارات بتفترض قاعدة فاضية والحاوية محتفظة ببيانات من تشغيل سابق",
                     "مع Redis",
                     "لما الصور كبيرة",
                 ], "answer": 1,
                 "explain": "إعادة الاستخدام بتسيب الحالة. لو محتاجها للسرعة، اضمن تصفير البيانات (Respawn) في بداية كل اختبار."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "استبدال SQLite بـPostgres حقيقي",
                 "md": "حوّل الـfactory من درس الـIntegration لتشتغل على Postgres بـTestcontainers، وأضف 3 اختبارات تعتمد على سلوك قاعدة البيانات: قيد فريد، ترجمة استعلام مجمّع (GroupBy/Sum)، و`ExecuteUpdateAsync`.",
                 "criteria": [
                     "الاختبارات الثلاثة تفشل لو رجّعت لـInMemory provider (جرّب وتأكد)",
                     "حاوية واحدة مشتركة (assembly/collection fixture)",
                     "Respawn أو ما يعادله بين الاختبارات",
                     "زمن التشغيل الكلي أقل من 60 ثانية على جهازك",
                 ],
                 "hint": "لو `docker` مش متاح في البيئة، الاختبار يفشل بسرعة وواضح: أضف فحصًا في `InitializeAsync` يرمي رسالة مفهومة («Docker مطلوب») بدل stack trace غامض."},
                {"id": "t2", "title": "حاوية لتبعية تانية",
                 "md": "شغّل Redis أو RabbitMQ في اختبار واحد حقيقي: إما كاش موزع تثبت إن القيمة اتخزنت واتقرأت، أو حدث منشور ومستهلَك.",
                 "criteria": [
                     "الاختبار بيتصل بالحاوية الحقيقية (مش in-memory fake)",
                     "بيؤكد على الأثر (القيمة موجودة / الرسالة اتستهلكت)",
                     "الحاوية بتتنضّف بعد الاختبار",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Testcontainers", "url": "https://testcontainers.com/"},
                {"label": "EF Core testing providers", "url": "https://learn.microsoft.com/ef/core/testing/"},
                {"label": "Respawn", "url": "https://github.com/jbogard/Respawn"},
                {"label": "Npgsql EF Core provider", "url": "https://www.npgsql.org/efcore/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l6
    {
        "id": "s1-m2-l6",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
نص صعوبة الاختبار مش في الـassertions — دي في **الإعداد**: بناء كائنات صالحة، وتوليد بيانات واقعية،
والحفاظ على الثبات (determinism). النص التاني في **قياس** الاختبارات نفسها: التغطية رقم مفيد للتشخيص،
وخادع جدًا لو بقى هدفًا.

في الدرس ده: Test Data Builders وObject Mother، توليد بيانات بـBogus ببذرة ثابتة، ملفات ذهبية (golden/approval)
بـVerify، وقياس التغطية بـcoverlet + ReportGenerator مع حدود في الـCI — وأخيرًا لمحة عن mutation testing.
"""},
            {"type": "terms", "items": [
                {"term": "Object Mother", "def": "مصنع مركزي لكائنات اختبار جاهزة: `AnOrder.Cancelled()` — قيم افتراضية سليمة."},
                {"term": "Test Data Builder", "def": "نمط fluent لتعديل ما تحتاجه فقط: `AnOrder.Default().WithCountry(\"SA\").Build()`."},
                {"term": "Bogus", "def": "توليد بيانات واقعية (أسماء، إيميلات، عناوين، تواريخ) — مع بذرة ثابتة للتكرار."},
                {"term": "AutoFixture", "def": "توليد تلقائي للكائنات وملء التبعيات — سريع لكن أحيانًا غامض."},
                {"term": "Golden / Approval files", "def": "تخزين المخرَج المتوقع في ملف ومراجعته عند التغيير (Verify) — ممتاز للـserializers والـSQL المُولَّد."},
                {"term": "Line vs Branch coverage", "def": "تغطية الأسطر مقابل تغطية الفروع. الفرعية أدق: `if` بسطر واحد ممكن تغطي السطر وتترك الفرع."},
                {"term": "Mutation testing", "def": "أداة تغيّر كودك عمدًا وتتأكد إن اختباراتك بتكتشف التغيير — مقياس جودة الاختبارات نفسها."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Tests package Bogus
dotnet add Shop.Tests package AutoFixture
dotnet add Shop.Tests package Verify.Xunit
dotnet add Shop.Tests package coverlet.collector

# تقارير التغطية
dotnet tool install -g dotnet-reportgenerator-globaltool
'''},
            {"type": "heading", "level": 2, "text": "Builders: إعداد مقروء وقابل لإعادة الاستخدام"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/Builders/OrderBuilder.cs", "title": "قيم افتراضية سليمة + تعديل ما يهم الاختبار فقط", "code": r'''
public sealed class OrderBuilder
{
    private Guid _id = Guid.NewGuid();
    private Guid _customerId = Guid.NewGuid();
    private string _country = "EG";
    private OrderStatus _status = OrderStatus.New;
    private DateTimeOffset _createdAt = new(2026, 1, 15, 10, 0, 0, TimeSpan.Zero);
    private List<OrderLine> _lines = [new(Guid.NewGuid(), 2, 100m)];

    public static OrderBuilder AnOrder() => new();

    public OrderBuilder WithId(Guid id) { _id = id; return this; }
    public OrderBuilder WithCountry(string c) { _country = c; return this; }
    public OrderBuilder WithStatus(OrderStatus s) { _status = s; return this; }
    public OrderBuilder WithLines(params (int qty, decimal price)[] lines)
    {
        _lines = lines.Select(l => new OrderLine(Guid.NewGuid(), l.qty, l.price)).ToList();
        return this;
    }
    public OrderBuilder CreatedAt(DateTimeOffset at) { _createdAt = at; return this; }
    public OrderBuilder Cancelled() => WithStatus(OrderStatus.Cancelled);

    public Order Build() => new()
    {
        Id = _id,
        Customer = new Customer { Id = _customerId, Country = _country },
        Status = _status,
        CreatedAt = _createdAt,
        Lines = _lines,
    };
}

// الاستخدام في الاختبار — القارئ يعرف بالظبط إيه اللي متغيّر
var order = AnOrder().Cancelled().Build();
var egyptianOrder = AnOrder().WithCountry("EG").WithLines((2, 100m)).Build();
'''},
            {"type": "heading", "level": 2, "text": "Bogus: بيانات واقعية ببذرة ثابتة"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/Data/CustomerFaker.cs", "title": "Determinism هو الشرط — بلا بذرة، الاختبارات flaky", "code": r'''
using Bogus;

public static class TestData
{
    // ✓ بذرة ثابتة: نفس البيانات في كل تشغيل، على كل جهاز وفي الـCI
    static TestData() => Randomizer.Seed = new Random(20260115);

    public static Faker<Customer> Customers(string country = "EG") =>
        new Faker<Customer>()
            .RuleFor(c => c.Id, f => f.Random.Guid())
            .RuleFor(c => c.Email, f => f.Internet.Email())
            .RuleFor(c => c.FullName, f => f.Name.FullName())
            .RuleFor(c => c.Country, _ => country)
            .RuleFor(c => c.Joined, f => f.Date.Past(2));

    public static Faker<Order> Orders(int lineCount = 3) =>
        new Faker<Order>()
            .RuleFor(o => o.Id, f => f.Random.Guid())
            .RuleFor(o => o.Customer, f => Customers().Generate())
            .RuleFor(o => o.Status, f => f.PickRandom<OrderStatus>())
            .RuleFor(o => o.Lines, f => Enumerable.Range(0, lineCount)
                .Select(_ => new OrderLine(f.Random.Guid(), f.Random.Int(1, 5), f.Commerce.Price(10, 500)))
                .ToList());

    /// <summary>كمية كبيرة لاختبار الأداء/الترقيم — لسه ثابتة.</summary>
    public static List<Order> ManyOrders(int count = 500) => Orders().Generate(count);
}

public sealed class OrderListQueryTests
{
    [Fact]
    public void Pagination_returns_requested_page_size_only()
    {
        var orders = TestData.ManyOrders(50);

        var page = OrderListQuery.Page(orders, page: 2, size: 10);

        page.Items.Should().HaveCount(10);
        page.TotalPages.Should().Be(5);
        page.Items[0].Id.Should().Be(orders[10].Id);
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء بيانات الاختبار الكلاسيكية",
             "md": """
- **بلا بذرة** → بيانات مختلفة كل تشغيل → اختبار ناجح مرة وفاشل مرة (flaky). ثبّت `Randomizer.Seed`.
- **بيانات غير صالحة تجاريًا** (سعر سالب، تاريخ ميلاد في المستقبل) → الاختبار بيعدي على حالة مستحيلة.
- **مشاركة كائن واحد قابل للتعديل بين اختبارين** → تعديل في اختبار بيكسر التاني. ابنِ نسخة جديدة كل مرة.
- **`DateTime.Now` في التوقعات** → فشل عند منتصف الليل. حقن `TimeProvider` واستخدم وقتًا ثابتًا.
- **AutoFixture لكل حاجة** → إعداد غامض؛ للـDomain الحساس استخدم builders صريحة.
"""},
            {"type": "heading", "level": 2, "text": "ملفات ذهبية: قارن المخرَج بملف معتمد"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Tests/SerializationApprovalTests.cs", "title": "Verify: أي تغيير في العقد بيظهر كـdiff واضح", "code": r'''
[UsesVerify]
public sealed class SerializationApprovalTests
{
    [Fact]
    public async Task OrderDto_contract_is_stable()
    {
        var dto = new OrderDto(
            Id: Guid.Parse("11111111-1111-1111-1111-111111111111"),
            Total: 228m,
            Currency: "EGP",
            Status: "paid",
            Lines: [new OrderLineDto(Guid.Empty, "Widget", 2, 100m)]);

        await Verify(dto)
            .UseParameters("v1")
            .ScrubMember(nameof(OrderDto.Id));       // إخفاء القيم المتغيرة
    }

    [Fact]
    public async Task Generated_sql_for_top_orders_is_stable()
    {
        // مفيد جدًا: أي تغيير في الاستعلام يظهر قبل ما يوصل الإنتاج
        var sql = OrderQueries.TopOrdersByRevenueSql();

        await Verify(sql).UseExtension("sql");
    }
}
// أول تشغيل بينشئ *.received.txt؛ تقبله فيتحول لـ*.verified.txt ويتضاف للـrepo.
// بعد كده، أي فرق = فشل مع diff واضح للمراجعة.
'''},
            {"type": "heading", "level": 2, "text": "التغطية: قياس صادق، مش رقم مستهدف"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "جمع التغطية وتوليد تقرير", "code": r'''
# جمع (coverlet.collector بيكتب cobertura.xml)
dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults

# تقرير HTML مقروء
reportgenerator \
  -reports:"TestResults/**/coverage.cobertura.xml" \
  -targetdir:"TestResults/report" \
  -reporttypes:Html \
  -assemblyfilters:"-*.Tests;-xunit.*"

# افتح TestResults/report/index.html
'''},
            {"type": "code", "lang": "yaml", "filename": ".github/workflows/coverage-gate.yml", "title": "حد أدنى في الـCI (على assemblies مهمة فقط)", "code": r'''
- name: Test with coverage
  run: dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults

- name: Coverage gate (Domain >= 85%)
  run: |
    reportgenerator -reports:"TestResults/**/coverage.cobertura.xml" \
                    -targetdir:"coverage-report" -reporttypes:Xml
    threshold=85
    actual=$(python3 - <<'PY'
    import xml.etree.ElementTree as ET
    root = ET.parse("coverage-report/Cobertura.xml").getroot()
    for cls in root.iter("class"):
        pass
    pkgs = root.find("packages")
    total, covered = 0, 0
    for line in pkgs.iter("line"):
        total += 1
        covered += int(line.get("hits", "0")) > 0
    print(round(100 * covered / max(total, 1)))
    PY
    )
    echo "coverage=${actual}% (threshold=${threshold}%)"
    test "$actual" -ge "$threshold"
'''},
            {"type": "table", "head": ["المنطقة", "الهدف المعقول للتغطية", "ليه"], "rows": [
                ["Domain / قواعد العمل", "85-100%", "أغلى مكان للباج، وأسهل مكان للاختبار"],
                ["Application services (handlers)", "70-90%", "منطق تنسيق له حالات فشل مهمة"],
                ["API endpoints (Integration)", "كل endpoint عام", "الاختبار الواحد بيغطي طبقات كتير"],
                ["Infrastructure (EF, clients)", "الحالات الحرجة فقط", "اختبارها الحقيقي = Testcontainers، ومكلف"],
                ["DTOs / Mappers / Models", "منخفض", "كود بلا منطق — التغطية هنا وهمية"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قياس جودة الاختبارات نفسها: Mutation Testing",
             "md": """
**Stryker.NET** بيعدّل كودك عمدًا (يقلب `>` إلى `<`، يبدّل `+` بـ`-`، يحذف شرط) ويشوف هل اختباراتك بتكتشف
التغيير. التعديلات اللي **ما بتكتشفهاش** = فجوات حقيقية في اختباراتك — أدق من التغطية بكتير.
```bash
dotnet tool install -g dotnet-stryker
dotnet stryker --project Shop.Domain/Shop.Domain.csproj
```
شغّله على الـDomain مرة كل فترة (مش في كل CI — بطيء).
"""},
            {"type": "checkpoints", "items": [
                "أبني Object Mother/Builders لبيانات الاختبار وأستخدمها في كل الاختبارات.",
                "أولّد بيانات واقعية بـBogus مع بذرة ثابتة (بلا flakiness).",
                "أستخدم ملفات ذهبية (Verify) لحماية العقود والـSQL المُولَّد.",
                "أقيس التغطية على المناطق المهمة وأفسّر الرقم بصدق (وأعرف حدوده).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "اختبار بيفشل مرة كل أسبوعين بدون تغيير في الكود. أول حاجة تفحصها؟",
                 "options": [
                     "سرعة الجهاز",
                     "الاعتماد على الوقت/العشوائية: `DateTime.Now` أو بيانات Bogus بلا بذرة",
                     "عدد الاختبارات",
                     "إصدار xUnit",
                 ], "answer": 1,
                 "explain": "الـflakiness سببه غالبًا nondeterminism: وقت حقيقي، عشوائية بلا بذرة، ترتيب غير مضمون، أو حالة مشتركة."},
                {"q": "تغطية 95% ومش لاقيين باجات بتتكشف. إيه التفسير الأرجح؟",
                 "options": [
                     "الكود ممتاز",
                     "اختبارات بتنفّذ الكود بدون assertions ذات معنى (تغطية ≠ صحة)",
                     "أداة التغطية غلط",
                     "محتاج اختبارات E2E",
                 ], "answer": 1,
                 "explain": "التغطية تقيس **التنفيذ** مش **التحقق**. الحل: راجع قوة الـassertions، وشغّل mutation testing لكشف الفجوات الحقيقية."},
                {"q": "أنهي منطقة تستحق أعلى تغطية؟",
                 "options": ["DTOs وrecords", "قواعد العمل في الـDomain", "الـmappers", "ملفات الإعدادات"], "answer": 1,
                 "explain": "أغلى الباجات وأرخص الاختبارات في الـDomain. الباقي كود بلا منطق غالبًا."},
                {"q": "فايدة الملفات الذهبية (Verify/approval)؟",
                 "options": [
                     "تسريع الاختبارات",
                     "إظهار أي تغيير في مخرَج معقّد (عقد JSON، SQL مولَّد) كـdiff يحتاج مراجعة واعية",
                     "استبدال الاختبارات",
                     "تقليل التغطية",
                 ], "answer": 1,
                 "explain": "بتحوّل «اتغير حاجة في العقد» من باج صامت في الإنتاج إلى مراجعة صريحة في الـPR."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "بنية بيانات اختبار",
                 "md": "أنشئ Builders لكل كيان Domain عندك + Faker ببذرة ثابتة لبيانات واقعية، واستبدل كل إعداد يدوي مكرر في الاختبارات بيهم.",
                 "criteria": [
                     "Builder لكل كيان رئيسي بقيم افتراضية صالحة",
                     "`Randomizer.Seed` ثابتة وموثقة",
                     "متوسط أسطر الإعداد في كل اختبار قلّ (قِس قبل/بعد)",
                     "تشغيل الاختبارات 5 مرات متتالية بنفس النتيجة (بلا flakiness)",
                 ],
                 "hint": "لو builder كبر، غالبًا الكيان نفسه كبير — دي إشارة معمارية مفيدة، مش مشكلة اختبار."},
                {"id": "t2", "title": "تقرير تغطية وحد أدنى",
                 "md": "شغّل التغطية، ولّد تقرير HTML، وحدد النسبة الحالية للـDomain، وأضف حدًا أدنى في الـCI (85% للـDomain مثلًا). ولو الوقت سمح: شغّل Stryker على مشروع الـDomain وسجّل 3 فجوات كشفها.",
                 "criteria": [
                     "تقرير HTML متولّد والنسب مسجلة في ملاحظات الدرس",
                     "gate في workflow يفشل لو النسبة نزلت",
                     "الاستثناءات مبررة (مجلدات مستبعدة من القياس)",
                     "(اختياري) 3 فجوات mutation مكتوبة مع اختبار يعالجها",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Bogus", "url": "https://github.com/bchavez/Bogus"},
                {"label": "Verify (approval testing)", "url": "https://github.com/VerifyTests/Verify"},
                {"label": "coverlet", "url": "https://github.com/coverlet-coverage/coverlet"},
                {"label": "ReportGenerator", "url": "https://github.com/danielpalme/ReportGenerator"},
                {"label": "Stryker.NET (mutation testing)", "url": "https://stryker-mutator.io/"},
            ]},
        ],
    },
]
