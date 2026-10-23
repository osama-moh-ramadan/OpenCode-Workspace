"""Stage 5, Module 3 — Orchestration with .NET Aspire (lessons 1 & 2)."""

TODAY = "2026-10-22"

LESSONS_S5_F = [
    # ══════════════════════════════════════════════════════════════════
    # s5-m3-l1 — .NET Aspire: AppHost وService Discovery
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s5-m3-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لحد دلوقتي النظام اللي بنيناه محتاج: Postgres + Redis + RabbitMQ + 4 خدمات + gateway،
وكل واحد بيتشغّل بأمر مختلف، بترتيب مختلف، بمنافذ مكتوبة يدويًا في `appsettings.Development.json`.
**ده ثمن الميكروسيرفيسز الحقيقي**: المطور الجديد بياخد يوم عشان يشغّل النظام محليًا.

**.NET Aspire** بيحل المشكلة دي بثلاث حاجات:
1. **AppHost** — برنامج واحد بيوصف النظام كله ككود (موارد، تبعيات، ترتيب إقلاع، أسرار) وبيشغّله بأمر واحد.
2. **Service Discovery** — الخدمات تنادي بعضها بـ**الاسم** (`https+http://catalog`) بدل URL ثابت،
   والمنافذ العشوائية محليًا بتتحل تلقائيًا.
3. **ServiceDefaults + Dashboard** — telemetry وhealth checks وresilience موحدة في كل خدمة (الدرس الجاي).

المهم تفهمه من الأول: **Aspire أداة تطوير وتنسيق محلي**، مش بديل Kubernetes في الإنتاج
(رغم إنه بيولّد مخططات نشر لـK8s/ACA/Compose).
"""},
            {"type": "terms", "items": [
                {"term": "AppHost", "def": "مشروع تنفيذي (`Aspire.AppHost.Sdk`) بيوصف النظام: موارد، تبعيات، أسرار. `DistributedApplication.CreateBuilder(args)` ← `builder.Build().Run()`."},
                {"term": "Resource", "def": "أي حاجة في النموذج: مشروع .NET، container، قاعدة بيانات، cache، وسيط رسائل، ملف تنفيذي. كل مورد له اسم فريد."},
                {"term": "IResourceBuilder<T>", "def": "الـfluent API لتكوين المورد: `WithReference`, `WaitFor`, `WithHttpHealthCheck`, `WithEnvironment`, `WithDataVolume`, `WithBindMount`."},
                {"term": "Integration", "def": "حزمة `Aspire.Hosting.*` بتضيف مورد جاهز (`AddPostgres`, `AddRedis`, `AddRabbitMQ`) + حزمة `Aspire.*` في الخدمة بتقرأ الـconnection string (`AddNpgsqlDbContext`)."},
                {"term": "Service Discovery", "def": "حل اسم الخدمة لعنوان فعلي وقت التشغيل. محليًا: Aspire يحقن `services__catalog__https__0`. في K8s: DNS."},
                {"term": "ServiceDefaults", "def": "مشروع مكتبة مشترك فيه `AddServiceDefaults()`: OTel + health checks + discovery + resilience لكل الخدمات."},
                {"term": "DCP (Developer Control Plane)", "def": "المحرك اللي بيدير دورة حياة الموارد محليًا وبيوزع المنافذ عشوائيًا (عشان تشغّل نسختين مع بعض)."},
                {"term": "Parameter", "def": "قيمة تكوين/سر من بره الكود: `builder.AddParameter(\"pg-password\", secret: true)` ← من user-secrets أو environment."},
                {"term": "WaitFor / WaitForCompletion", "def": "ترتيب إقلاع: المورد ما يبدأش إلا لما الاعتماد يبقى **صحي** (مش بس شغال) — أو لحد ما مهمة تنتهي (seeder)."},
                {"term": "Aspire CLI", "def": "`aspire run` · `aspire add` · `aspire restore` · `aspire init` · `aspire dashboard run` — و`aspire.config.json` لاكتشاف الـAppHost."},
            ]},
            {"type": "heading", "level": 2, "text": "1) شكل المشاريع: 3 أنواع"},
            {"type": "code", "lang": "xml", "filename": "src/Shop.AppHost/Shop.AppHost.csproj", "title": "AppHost (صيغة Aspire 13) — الـSDK في سطر المشروع نفسه", "code": r'''
<!--
  ★ تغيّر في Aspire 13: الـSDK بيتحدد مباشرة في وسم <Project> بالإصدار.
  الـSDK بيشمل Aspire.Hosting.AppHost تلقائيًا — بلا PackageReference إضافية،
  وبلا <Sdk Name="Aspire.AppHost.Sdk" .../> ولا Microsoft.NET.Sdk كقاعدة (الصيغة القديمة 9.x).
-->
<Project Sdk="Aspire.AppHost.Sdk/13.6.0">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <!-- ✓ قوالب 13.5+ بتفعّلها: الـAppHost بيحل نسخة CLI محلية (dotnet run == aspire run) -->
    <AspireUseCliBundle>true</AspireUseCliBundle>
    <UserSecretsId>9f2c1a7e-shop-apphost</UserSecretsId>
  </PropertyGroup>

  <ItemGroup>
    <!-- كل مورد من حزمة hosting خاصة به -->
    <PackageReference Include="Aspire.Hosting.PostgreSQL" Version="13.6.0" />
    <PackageReference Include="Aspire.Hosting.Redis"      Version="13.6.0" />
    <PackageReference Include="Aspire.Hosting.RabbitMQ"   Version="13.6.0" />
  </ItemGroup>

  <ItemGroup>
    <!-- ✓ ProjectReference هي اللي بتولّد أنواع `Projects.Shop_Orders` المستخدمة في AppHost.cs -->
    <ProjectReference Include="..\Shop.Catalog\Shop.Catalog.csproj" />
    <ProjectReference Include="..\Shop.Orders\Shop.Orders.csproj" />
    <ProjectReference Include="..\Shop.Payments\Shop.Payments.csproj" />
    <ProjectReference Include="..\Shop.Notifications\Shop.Notifications.csproj" />
    <ProjectReference Include="..\Shop.Gateway\Shop.Gateway.csproj" />
    <ProjectReference Include="..\Shop.Seed\Shop.Seed.csproj" />
  </ItemGroup>

</Project>
'''},
            {"type": "code", "lang": "xml", "filename": "src/Shop.ServiceDefaults/Shop.ServiceDefaults.csproj", "title": "ServiceDefaults — مشروع مشترك (لا يُنشر كخدمة)", "code": r'''
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <!-- ★ بيعلّم أدوات Aspire إن ده المشروع المشترك اللي يتضاف تلقائيًا لأي خدمة جديدة -->
    <IsAspireSharedProject>true</IsAspireSharedProject>
  </PropertyGroup>

  <ItemGroup>
    <FrameworkReference Include="Microsoft.AspNetCore.App" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Extensions.Http.Resilience"            Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.ServiceDiscovery"          Version="10.0.0" />
    <PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol"   Version="1.12.0" />
    <PackageReference Include="OpenTelemetry.Extensions.Hosting"               Version="1.12.0" />
    <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore"       Version="1.12.0" />
    <PackageReference Include="OpenTelemetry.Instrumentation.Http"             Version="1.12.0" />
    <PackageReference Include="OpenTelemetry.Instrumentation.Runtime"          Version="1.12.0" />
  </ItemGroup>

</Project>

<!--
  لو بتستخدم file-based AppHost (apphost.cs بلا csproj) المشروع ده مش بيتولد تلقائيًا:
      dotnet new aspire-servicedefaults -n Shop.ServiceDefaults
-->
'''},
            {"type": "code", "lang": "bash", "title": "أوامر التجهيز والتشغيل", "code": r'''
# ═══ 1) إضافة Aspire لحل قائم (بدل إنشاء مشروع جديد) ═══
dotnet new install Aspire.ProjectTemplates
dotnet new aspire-apphost       -n Shop.AppHost        -o src/Shop.AppHost
dotnet new aspire-servicedefaults -n Shop.ServiceDefaults -o src/Shop.ServiceDefaults

# أو من CLI (13.x) — يكتشف/ينشئ الـAppHost ويضيف موارد
dotnet tool install --global aspire.cli      # مرة واحدة
aspire init                                  # في جذر المستودع
aspire add aspire.hosting.postgresql         # يضيف الحزمة + سطر المورد
aspire add aspire.hosting.rabbitmq
aspire restore                               # يستعيد الحزم (ويعيد توليد SDKs للغات تانية)

# ═══ 2) التشغيل: أمر واحد لكل النظام ═══
cd src/Shop.AppHost
dotnet run                                   # يفتح لوحة Aspire + يشغّل كل الموارد
# أو
aspire run                                   # نفس الحاجة عبر CLI (يدعم launch profiles)

# ═══ 3) الأسرار: user-secrets (لا أسرار في الكود ولا في git) ═══
cd src/Shop.AppHost
dotnet user-secrets set "Parameters:pg-password"     "local-dev-only"
dotnet user-secrets set "Parameters:rabbit-password" "local-dev-only"

# ═══ 4) اللوحة لوحدها (لخدمات مش تحت AppHost) — الدرس الجاي ═══
aspire dashboard run                         # UI على 18888، OTLP على 4317/4318

# ═══ 5) file-based AppHost (بديل خفيف لمستودع متعدد اللغات) ═══
#   apphost.cs يبدأ بـ:
#     #:sdk Aspire.AppHost.Sdk@13.6.0
#     #:package Aspire.Hosting.Redis@13.6.0
#   ⚠ الـAppHost الملفّي **لا يمكن** اختباره بـDistributedApplicationTestingBuilder (درس 5.3.3)
'''},
            {"type": "heading", "level": 2, "text": "2) AppHost الكامل: موارد + تبعيات + ترتيب إقلاع"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.AppHost/AppHost.cs", "title": "النظام كله ككود", "code": r'''
// requires: using Aspire.Hosting;
var builder = DistributedApplication.CreateBuilder(args);

// ═══ 1) بارامترات وأسرار (من user-secrets / environment — بلا قيم في الكود) ═══
var pgPassword     = builder.AddParameter("pg-password",     secret: true);
var rabbitPassword = builder.AddParameter("rabbit-password", secret: true);

// ═══ 2) البنية التحتية ═══
var postgres = builder.AddPostgres("postgres", password: pgPassword)   // ✓ تحقق من ترتيب الوسائط في إصدارك
    .WithDataVolume("shop-pg-data")
    .WithLifetime(ContainerLifetime.Persistent)     // ★ البيانات تبقى بين التشغيلات (وإلا كل مرة DB فاضية)
    .WithPgAdmin();                                 // أداة إدارة (في إصدارات أحدث: PgWeb — تحقق)

var shopdb = postgres.AddDatabase("shopdb");        // ← الاسم ده هو مفتاح الـconnection string

var cache = builder.AddRedis("cache")
    .WithDataVolume("shop-redis-data");

var rabbit = builder.AddRabbitMQ("rabbit", password: rabbitPassword)
    .WithDataVolume("shop-rabbit-data")
    .WithManagementPlugin()                         // لوحة 15672 (إصدارات أحدث: sidecar — تحقق)
    // ★ بنية الوسيط المعلنة ككود (درس 5.2.1): exchanges/queues/bindings/policies
    .WithBindMount("../infra/rabbitmq/rabbitmq.conf",     "/etc/rabbitmq/rabbitmq.conf",     isReadOnly: true)
    .WithBindMount("../infra/rabbitmq/definitions.json",  "/etc/rabbitmq/definitions.json",  isReadOnly: true);

// ═══ 3) مهمة تجهيز البيانات: الباقي ينتظر **انتهاءها** ═══
var seed = builder.AddProject<Projects.Shop_Seed>("seed")
    .WithReference(shopdb)
    .WaitFor(shopdb);

// ═══ 4) الخدمات ═══
var catalog = builder.AddProject<Projects.Shop_Catalog>("catalog")
    .WithHttpHealthCheck("/health")                 // ✓ يتطلب MapDefaultEndpoints في الخدمة (تحت)
    .WithReference(shopdb).WaitFor(shopdb)          // → يحقن ConnectionStrings__shopdb
    .WithReference(cache).WaitFor(cache)            // → يحقن ConnectionStrings__cache
    .WaitForCompletion(seed);                       // ★ ما تبدأش قبل ما البيانات تتزرع

var orders = builder.AddProject<Projects.Shop_Orders>("orders")
    .WithHttpHealthCheck("/health")
    .WithReference(shopdb).WaitFor(shopdb)
    .WithReference(rabbit).WaitFor(rabbit)          // → يحقن ConnectionStrings__rabbit
    .WithReference(catalog).WaitFor(catalog);       // → يحقن services__catalog__https__0 (discovery!)

var payments = builder.AddProject<Projects.Shop_Payments>("payments")
    .WithHttpHealthCheck("/health")
    .WithReference(rabbit).WaitFor(rabbit);         // worker: بلا endpoint خارجي

var notifications = builder.AddProject<Projects.Shop_Notifications>("notifications")
    .WithReference(rabbit).WaitFor(rabbit);

var gateway = builder.AddProject<Projects.Shop_Gateway>("gateway")
    .WithExternalHttpEndpoints()                    // ★ يُعلن للمتصفح/الخارج (وإلا الرابط مش هيظهر)
    .WithHttpHealthCheck("/health")
    .WithReference(orders).WaitFor(orders)
    .WithReference(catalog).WaitFor(catalog);

// ═══ 5) أمثلة تكوين إضافية (مش مستخدمة كلها هنا) ═══
// .WithEnvironment("Orders__FeatureFlags__NewPricing", "true")   // تكوين لكل تشغيل
// .WithReplicas(2)                                               // نسختين محليًا (اختبار discovery/load)
// .WithArgs("--verbose")
// .WithHttpEndpoint(port: 5100, targetPort: 8080, name: "api")   // تثبيت منفذ (يفضّل تركه عشوائيًا)
// .WithEndpoint("api", e => e.UriScheme = "https")               // تعديل endpoint موجود

builder.Build().Run();

// ══════════════════════════════════════════════════════════════════
// ما الذي يحدث فعلًا عند Run()؟
// ① DCP يبني نموذج الموارد ويحسب ترتيب الإقلاع من WaitFor
// ② يشغّل containers (postgres/redis/rabbit) وينتظر صحتها
// ③ يشغّل مشاريع .NET كعمليات محلية بمنافذ **عشوائية**
// ④ يحقن لكل عملية: ConnectionStrings__* + services__<name>__<scheme>__0 + OTEL_* للوحة
// ⑤ يفتح لوحة Aspire (الدرس الجاي) ويعرض الحالة واللوغات والـtraces
// ══════════════════════════════════════════════════════════════════
'''},
            {"type": "table", "head": ["المورد", "الحزمة", "المتغير المحقون في الخدمة", "ملاحظة"], "rows": [
                ["`AddPostgres(\"postgres\").AddDatabase(\"shopdb\")`", "Aspire.Hosting.PostgreSQL", "`ConnectionStrings__shopdb`", "اسم **قاعدة البيانات** هو المفتاح، مش اسم الخادم"],
                ["`AddRedis(\"cache\")`", "Aspire.Hosting.Redis", "`ConnectionStrings__cache`", "منفذ عشوائي — `IDatabase` واحد مشترك (درس 3.3.5)"],
                ["`AddRabbitMQ(\"rabbit\")`", "Aspire.Hosting.RabbitMQ", "`ConnectionStrings__rabbit`", "بصيغة `amqp://user:pass@host:port`"],
                ["`AddProject<Projects.Shop_Catalog>(\"catalog\")`", "—", "`services__catalog__https__0`", "★ discovery: استخدم الاسم في `BaseAddress`"],
                ["`AddParameter(\"x\", secret: true)`", "—", "بالحقن الصريح (`WithEnvironment`/`WithReference`)", "من user-secrets أو environment"],
                ["`AddContainer(\"otel\", \"…\")`", "—", "حسب الـendpoints", "لأدوات جانبية (Jaeger/Collector)"],
                ["`AddExecutable(\"node\", …)`", "—", "`services__web__http__0`", "لواجهات غير .NET (polyglot)"],
            ]},
            {"type": "callout", "kind": "tip", "title": "الـAppHost كود — يتراجع في الـPR زي أي كود",
             "md": """
**قواعد نطبقها في الفريق:**
1. **بلا أسرار في AppHost** — `AddParameter(secret: true)` دائمًا، والقيم في user-secrets/key-vault.
2. **بلا منطق أعمال** — AppHost يصف **التوبولوجيا** بس. لو لقيت نفسك بتعمل حسابات/قراءة ملفات تكوين خدمات،
   ده مكانه الخدمة نفسها.
3. **أسماء الموارد = أسماء الخدمات في discovery** — ثبّتها في مستند (`docs/services.md`) لأن كل `BaseAddress` بيعتمد عليها.
4. **`WaitFor` لكل اعتماد** — بلا ترتيب، الخدمة تبدأ وتفشل في أول طلب (وتعيد المحاولة بصخب).
5. **`WithHttpHealthCheck` لكل خدمة HTTP** — هو اللي يخلي `WaitFor` يعني «صحي» مش «العملية اشتغلت».
6. **مراجعة الـAppHost في الـPR** إلزامية: إضافة مورد = تغيير في توبولوجيا النظام.
7. **AppHost نفسه لا يُنشر** كخدمة؛ يُستخدم لتوليد مخطط النشر (`aspire publish`/`PublishAs*` APIs).
"""},
            {"type": "heading", "level": 2, "text": "3) Service Discovery: من URL ثابت لاسم خدمة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.ServiceDefaults/Extensions.cs", "title": "الملف الكامل اللي كل خدمة بتستخدمه", "code": r'''
// requires: using Microsoft.AspNetCore.Builder; using Microsoft.AspNetCore.Diagnostics.HealthChecks;
//           using Microsoft.Extensions.DependencyInjection; using Microsoft.Extensions.Diagnostics.HealthChecks;
//           using Microsoft.Extensions.Hosting; using Microsoft.Extensions.Logging;
//           using OpenTelemetry; using OpenTelemetry.Metrics; using OpenTelemetry.Trace;

public static class ServiceDefaultsExtensions
{
    /// <summary>السطر الوحيد اللي كل خدمة بتناديه في Program.cs.</summary>
    public static TBuilder AddServiceDefaults<TBuilder>(this TBuilder builder)
        where TBuilder : IHostApplicationBuilder
    {
        builder.ConfigureOpenTelemetry();
        builder.AddDefaultHealthChecks();

        builder.Services.AddServiceDiscovery();          // ✓ يحل أسماء الخدمات لعناوين

        builder.Services.ConfigureHttpClientDefaults(http =>
        {
            http.AddStandardResilienceHandler();         // ✓ resilience افتراضي لكل HttpClient (درس 5.2.4)
            http.AddServiceDiscovery();                  // ✓ discovery افتراضي لكل HttpClient
            // (في إصدارات أقدم كان الاسم: http.UseServiceDiscovery())
        });

        // اختياري: قصر discovery على https في البيئات المشفرة
        // builder.Services.Configure<ServiceDiscoveryOptions>(o => o.AllowedSchemes = ["https"]);

        return builder;
    }

    private static TBuilder ConfigureOpenTelemetry<TBuilder>(this TBuilder builder)
        where TBuilder : IHostApplicationBuilder
    {
        builder.Services.AddOpenTelemetry()
            .WithMetrics(metrics => metrics
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation()
                .AddRuntimeInstrumentation())
            .WithTracing(tracing => tracing
                .AddSource(builder.Environment.ApplicationName)     // ★ مصادرنا المخصصة (الدرس الجاي)
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation());
                // .AddGrpcClientInstrumentation()  ← يحتاج OpenTelemetry.Instrumentation.GrpcNetClient

        builder.AddOpenTelemetryExporters();
        return builder;
    }

    private static TBuilder AddOpenTelemetryExporters<TBuilder>(this TBuilder builder)
        where TBuilder : IHostApplicationBuilder
    {
        // ✓ لو فيه OTLP endpoint (لوحة Aspire بتحطه تلقائيًا) → صدّر له
        var useOtlp = !string.IsNullOrWhiteSpace(builder.Configuration["OTEL_EXPORTER_OTLP_ENDPOINT"]);
        if (useOtlp)
        {
            builder.Services.AddOpenTelemetry().UseOtlpExporter();
        }

        // للإنتاج: Azure Monitor / Grafana / Prometheus (المرحلة 6)
        return builder;
    }

    private static TBuilder AddDefaultHealthChecks<TBuilder>(this TBuilder builder)
        where TBuilder : IHostApplicationBuilder
    {
        builder.Services.AddHealthChecks()
            .AddCheck("self", () => HealthCheckResult.Healthy(), ["live"]);   // ✓ liveness رخيص
        return builder;
    }

    /// <summary>يُنادى في نهاية Program.cs لكل خدمة HTTP.</summary>
    public static WebApplication MapDefaultEndpoints(this WebApplication app)
    {
        // ⚠ في الإنتاج قيّد الوصول لهذه المسارات (شبكة داخلية/مصادقة) — فيها معلومات حساسة
        app.MapHealthChecks("/health");                          // readiness: كل الفحوصات

        app.MapHealthChecks("/alive", new HealthCheckOptions     // liveness: التطبيق بيرد بس
        {
            Predicate = r => r.Tags.Contains("live"),
        });

        return app;
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Program.cs", "title": "خدمة تستهلك الاسم بدل العنوان + تكاملات Aspire", "code": r'''
// requires: using Shop.ServiceDefaults;
var builder = WebApplication.CreateBuilder(args);

// ★ 1) السطر اللي يربط الخدمة بكل defaults (OTel + health + discovery + resilience)
builder.AddServiceDefaults();

// 2) قاعدة البيانات: التكامل بيقرأ ConnectionStrings:shopdb اللي حقنه الـAppHost
builder.AddNpgsqlDbContext<OrdersDbContext>("shopdb");      // حزمة Aspire.Npgsql.EntityFrameworkCore.PostgreSQL

// 3) Redis بنفس الطريقة
builder.AddRedisDistributedCache("cache");                  // حزمة Aspire.StackExchange.Redis

// 4) ★ الوسيط: connection string من discovery — بدل RabbitMq:Host الثابت في درس 5.2.1
builder.Services.AddMassTransit(x =>
{
    x.AddConsumer<OrderPlacedConsumer>();
    x.AddEntityFrameworkOutbox<OrdersDbContext>(o => o.UsePostgres().UseBusOutbox());

    x.UsingRabbitMq((context, cfg) =>
    {
        // ✓ Aspire يحقن ConnectionStrings__rabbit = amqp://shop:****@localhost:52341
        cfg.Host(new Uri(builder.Configuration.GetConnectionString("rabbit")!));
        cfg.ConfigureEndpoints(context);
    });
});

// 5) ★ عميل HTTP لخدمة تانية **بالاسم** — بلا أرقام منافذ
builder.Services.AddHttpClient<CatalogClient>(client =>
{
    // https+http:// ← «فضّل https، ولو مش متاح استخدم http» (محلل الـschemes)
    client.BaseAddress = new Uri("https+http://catalog");
    client.Timeout = TimeSpan.FromSeconds(5);               // ✓ ميزانية المهلة (درس 5.2.4)
});
// الشكل المختصر: BaseAddress = new Uri("http://catalog")
// endpoint مُسمّى:  BaseAddress = new Uri("https://catalog.api")   ← اسم المورد.اسم الـendpoint

var app = builder.Build();

app.MapDefaultEndpoints();                                  // /health + /alive
app.MapPost("/api/orders", OrdersApi.PlaceOrder);
// …
app.Run();

// ═══ العميل نفسه (بلا أي كود discovery — بيشتغل بالاسم) ═══
public sealed class CatalogClient(HttpClient http, ILogger<CatalogClient> log)
{
    public async Task<ProductSnapshot?> GetAsync(Guid productId, CancellationToken ct)
    {
        try
        {
            // ✓ resilience handler + discovery اتضافوا افتراضيًا عبر ConfigureHttpClientDefaults
            return await http.GetFromJsonAsync<ProductSnapshot>($"/api/products/{productId}", ct);
        }
        catch (HttpRequestException ex)
        {
            log.LogError(ex, "catalog lookup failed for {ProductId} — degrading", productId);
            return null;                                     // fallback مُعلَن (درس 5.2.4)
        }
    }
}

public sealed record ProductSnapshot(Guid Id, string Name, long PriceMinor, string Currency, int Stock);
'''},
            {"type": "callout", "kind": "note", "title": "إزاي الاسم بيتحل فعلًا (بلا سحر)",
             "md": """
**محليًا (Aspire):** الـAppHost بيحقن لكل خدمة متغيرات بيئة بالشكل ده (من 13.2 الاسم = **الـscheme**):
```bash
services__catalog__https__0 = https://localhost:53211
services__catalog__http__0  = http://localhost:53210
ConnectionStrings__shopdb   = Host=localhost;Port=54321;Database=shopdb;Username=postgres;Password=****
ConnectionStrings__rabbit   = amqp://shop:****@localhost:52341
```
`AddServiceDiscovery()` بيقرأ المتغيرات دي ويحل `https+http://catalog` لأول عنوان مطابق بالترتيب المطلوب.
المنافذ عشوائية عن قصد → تقدر تشغّل نسختين من النظام في نفس الوقت بلا تصادم.

**في Kubernetes:** نفس الاسم بيتحل بـDNS (`catalog.namespace.svc.cluster.local`) — **الكود ما بيتغيرش**.
ده جوهر discovery: الكود بيتعامل مع اسم منطقي، وآلية الحل بتختلف حسب البيئة.

**لغات تانية (Go/Python/TS/Java):** اقرأ المتغير مباشرة:
```bash
CATALOG_URL="${services__catalog__https__0}"
```

**لـYARP (درس 5.1.4):** `AddServiceDiscoveryDestinationResolver()` + clusters بـ`"https://orders"` بدل عناوين ثابتة.
"""},
            {"type": "table", "head": ["المشكلة قبل Aspire", "الحل بعده", "الأثر على الفريق"], "rows": [
                ["5 أوامر تشغيل + ترتيب يدوي", "`dotnet run` في AppHost", "onboarding من يوم لـ5 دقايق"],
                ["منافذ ثابتة في appsettings → تصادم", "منافذ عشوائية + discovery بالاسم", "نسختين من النظام جنب بعض"],
                ["`localhost:5432` مكتوب في كل خدمة", "`ConnectionStrings__shopdb` محقون", "نقل البيئة بلا تعديل كود"],
                ["الخدمة تبدأ قبل ما DB تجهز → crash loop", "`WaitFor(shopdb)` + health check", "تشغيل حتمي (deterministic)"],
                ["كل خدمة بتكوّن OTel لوحدها", "`AddServiceDefaults()` سطر واحد", "تتبّع موحّد عبر الخدمات"],
                ["كل خدمة بتكوّن resilience لوحدها", "`AddStandardResilienceHandler()` افتراضيًا", "لا خدمة «نسيت» retry/timeout"],
                ["أسرار في appsettings.Development.json", "`AddParameter(secret: true)` + user-secrets", "لا تسريب في git"],
                ["`docker-compose` للبنية و`launchSettings` للخدمات (مصدرين)", "نموذج واحد ككود", "مراجعة التوبولوجيا في PR واحد"],
            ]},
            {"type": "callout", "kind": "warn", "title": "حدود Aspire — افهمها قبل ما تعتمد عليه",
             "md": """
- **أداة تطوير وتنسيق محلي** في الأساس. النشر للإنتاج بيتم عبر targets (`Kubernetes`, `Azure Container Apps`,
  `Docker Compose` publish mode) — **تعلّم K8s نفسه** (المرحلة 7) ولا تعتمد على Aspire إنه «يفهمك» الإنتاج.
- **حزم `Aspire.Hosting.*` لا تُشحن مع خدماتك** — هي للـAppHost بس. اللي بيتشحن مع الخدمة:
  `Aspire.*` client integrations + `Microsoft.Extensions.ServiceDiscovery`.
- **المنافذ العشوائية** بتكسر أي حاجة بتفترض منفذ ثابت: اختبارات بتربط بـ`localhost:5000`،
  قواعد CORS ثابتة، أدوات خارجية. استخدم `CreateHttpClient("name")` في الاختبارات (درس 5.3.3).
- **`WithHttpHealthCheck` يتطلب endpoint فعّال** — لو الخدمة مش بتعمل map لـ`/health`،
  المورد هيفضل «غير صحي» وكل المعتمدين عليه هيعلقوا في `WaitFor`.
- **التكاملات المجتمعية** (مثل `Aspire.MassTransit.RabbitMQ`) مش من Microsoft —
  قيّم الجودة والدعم قبل الاعتماد؛ الكود اليدوي اللي فوق بيشتغل بلا أي تكامل إضافي.
- **الإصدارات بتتحرك بسرعة** (13.0 → 13.6 في سنة): ثبّت الإصدار في كل الحزم،
  وراجع release notes عند الترقية — فيه تغييرات أسماء (مثل `services__x__<endpoint>` → `services__x__<scheme>`).
"""},
            {"type": "steps", "title": "أضف Aspire لحل قائم في 7 خطوات", "items": [
                {"title": "أنشئ AppHost + ServiceDefaults", "md": "`dotnet new aspire-apphost` و`dotnet new aspire-servicedefaults`، وأضف ProjectReferences للخدمات في AppHost.csproj.", "code": "dotnet new aspire-apphost -n Shop.AppHost -o src/Shop.AppHost\ndotnet new aspire-servicedefaults -n Shop.ServiceDefaults -o src/Shop.ServiceDefaults"},
                {"title": "ارفع كل خدمة لـServiceDefaults", "md": "في كل خدمة: ProjectReference لـServiceDefaults + `builder.AddServiceDefaults();` + `app.MapDefaultEndpoints();`. احذف تكوين OTel المكرر.", "code": "builder.AddServiceDefaults();\n// …\napp.MapDefaultEndpoints();"},
                {"title": "انقل البنية التحتية لموارد", "md": "بدّل `docker-compose` بـ`AddPostgres`/`AddRedis`/`AddRabbitMQ` مع `WithDataVolume` و`WithLifetime(ContainerLifetime.Persistent)`.", "code": "var postgres = builder.AddPostgres(\"postgres\", password: pgPassword).WithDataVolume();\nvar shopdb = postgres.AddDatabase(\"shopdb\");"},
                {"title": "استبدل الـconnection strings الثابتة", "md": "احذف `ConnectionStrings` من `appsettings.Development.json` واعتمد على `WithReference` — مع fallback لقيمة محلية لو الخدمة شغالة بره AppHost.", "code": "// ✓ fallback آمن للتشغيل المنفرد\nvar cs = builder.Configuration.GetConnectionString(\"shopdb\")\n         ?? \"Host=localhost;Port=5432;Database=shopdb;Username=postgres;Password=local\";"},
                {"title": "حوّل النداءات بين الخدمات لـdiscovery", "md": "أي `BaseAddress` فيه `localhost:port` → اسم المورد. وأضف `WithReference(otherService)` في AppHost عشان يحقن العنوان.", "code": "client.BaseAddress = new Uri(\"https+http://catalog\");"},
                {"title": "رتّب الإقلاع بالصحة", "md": "`WithHttpHealthCheck(\"/health\")` لكل خدمة + `WaitFor` لكل اعتماد + `WaitForCompletion(seeder)`.", "code": "var orders = builder.AddProject<Projects.Shop_Orders>(\"orders\")\n    .WithHttpHealthCheck(\"/health\")\n    .WithReference(shopdb).WaitFor(shopdb);"},
                {"title": "وثّق وشغّل", "md": "حدّث README بأمر تشغيل واحد، وثبّت إصدارات الحزم، وراجع `docs/services.md` (أسماء الموارد = أسماء discovery).", "code": "# التشغيل المحلي\ndotnet run --project src/Shop.AppHost"}]},
            {"type": "checkpoints", "items": [
                "أكتب AppHost يصف البنية التحتية والخدمات والتبعيات والأسرار ككود، وأشغّل النظام بأمر واحد.",
                "أستخدم `WithReference` + `WaitFor` + `WithHttpHealthCheck` لترتيب إقلاع حتمي بناءً على الصحة.",
                "أستبدل URLs الثابتة بـservice discovery (`https+http://catalog`) وأفهم المتغيرات المحقونة (`services__*`, `ConnectionStrings__*`).",
                "أرفع الخدمات لـServiceDefaults (OTel + health + discovery + resilience) بسطر واحد في كل خدمة.",
                "أعرف حدود Aspire: أداة تطوير، مش بديل منصة الإنتاج، ومش بيُشحن مع الخدمات.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "في Aspire 13، إزاي يتحدد SDK للـAppHost؟",
                 "options": [
                     "`<Project Sdk=\"Microsoft.NET.Sdk\">` + `<Sdk Name=\"Aspire.AppHost.Sdk\" />`",
                     "مباشرة في وسم المشروع: `<Project Sdk=\"Aspire.AppHost.Sdk/13.6.0\">` — والـSDK بيشمل `Aspire.Hosting.AppHost` تلقائيًا",
                     "PackageReference لـ`Aspire.Hosting`",
                     "global tool فقط",
                 ], "answer": 1,
                 "explain": "دي صيغة 13.x الجديدة (الصيغة الأولى هي 9.x القديمة). حزم `Aspire.Hosting.*` للموارد (Postgres/Redis/RabbitMQ) لسه محتاجة PackageReference."},
                {"q": "خدمة بتنادي `https+http://catalog`. إيه اللي بيحصل؟",
                 "options": [
                     "DNS عادي",
                     "service discovery بيحل الاسم لعنوان فعلي من متغيرات البيئة المحقونة (`services__catalog__https__0`) مع تفضيل https",
                     "يقرأ appsettings",
                     "يفشل لو المنفذ مش ثابت",
                 ], "answer": 1,
                 "explain": "الصيغة `https+http://` = محلل schemes: جرّب https الأول، ولو مش متاح استخدم http. محليًا Aspire بيحقن العناوين؛ في K8s بيتحل بـDNS."},
                {"q": "فرق `WaitFor(x)` عن مجرد إضافة `x` قبل الخدمة في الكود؟",
                 "options": [
                     "مفيش فرق",
                     "`WaitFor` بيأجل بدء الخدمة لحد ما `x` يبقى **صحي** (health check عدى) — مش بس إن العملية اشتغلت",
                     "بيعمل restart",
                     "بيمنع `x` من التوقف",
                 ], "answer": 1,
                 "explain": "بلا health check + WaitFor، الخدمة تبدأ وتحاول توصيل لـDB لسه بتتهيّأ → فشل وصخب وإعادة محاولة. الترتيب في الكود مالوش أي أثر."},
                {"q": "متغير البيئة اللي بيحقنه `WithReference(shopdb)`؟",
                 "options": [
                     "`ConnectionStrings__postgres`",
                     "`ConnectionStrings__shopdb` — اسم **قاعدة البيانات** (المورد اللي عملته بـ`AddDatabase`) هو المفتاح",
                     "`services__shopdb__https__0`",
                     "`Database__shopdb`",
                 ], "answer": 1,
                 "explain": "`AddPostgres(\"postgres\").AddDatabase(\"shopdb\")` بيعمل موردين؛ الـconnection string بيتحقن باسم قاعدة البيانات. وده اللي بيقراه `AddNpgsqlDbContext<>(\"shopdb\")`."},
                {"q": "إيه اللي **ما ينفعش** تحطه في AppHost؟",
                 "options": [
                     "`AddParameter(secret: true)`",
                     "منطق أعمال وقراءة تكوين الخدمات وحسابات — AppHost يصف التوبولوجيا فقط",
                     "`WithBindMount`",
                     "`WithReplicas(2)`",
                 ], "answer": 1,
                 "explain": "AppHost = وصف النظام (موارد/تبعيات/أسرار/منافذ). أي منطق يخص سلوك الخدمة مكانه جوه الخدمة نفسها."},
                {"q": "خدمة HTTP في AppHost مع `WithHttpHealthCheck(\"/health\")` لكنها ما بتعملش map للمسار. النتيجة؟",
                 "options": [
                     "كله عادي",
                     "المورد يفضل غير صحي، وأي خدمة معتمدة عليه بـ`WaitFor` تعلق في الانتظار (timeout في النهاية)",
                     "404 وفقط",
                     "اللوحة تتعطل",
                 ], "answer": 1,
                 "explain": "لهذا `MapDefaultEndpoints()` جزء إلزامي من رفع كل خدمة لـServiceDefaults: `/health` و`/alive`."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "AppHost يشغّل نظامك بأمر واحد",
                 "md": "أنشئ `Shop.AppHost` + `Shop.ServiceDefaults` لمشروعك الحالي، وانقل كل البنية التحتية (DB/cache/وسيط) لموارد Aspire، وارفع كل الخدمات لـServiceDefaults مع health checks وترتيب إقلاع. احذف `docker-compose` من مسار التطوير (خليه للنشر/CI) واحذف الـURLs الثابتة.",
                 "criteria": [
                     "`dotnet run --project src/Shop.AppHost` يشغّل النظام كاملًا بلا أي أمر إضافي",
                     "كل مورد بنية تحتية بـ`WithDataVolume` + `WithLifetime(ContainerLifetime.Persistent)` (البيانات تبقى بين التشغيلات)",
                     "كل الأسرار عبر `AddParameter(secret: true)` — `git grep` مفيهوش كلمة سر",
                     "كل خدمة HTTP: `AddServiceDefaults()` + `MapDefaultEndpoints()` + `WithHttpHealthCheck(\"/health\")` في AppHost",
                     "كل اعتماد عليه `WaitFor` (و`WaitForCompletion` لو فيه seeder)",
                     "مفيش `localhost:<port>` ثابت في أي `BaseAddress` — كل النداءات بين الخدمات بأسماء الموارد",
                     "`docs/services.md` فيه جدول: اسم المورد × النوع × الاعتمادات × الـenv المحقون",
                 ],
                 "hint": "لو خدمة لازم تشتغل بره AppHost (اختبار وحدة/CI سريع)، خلي قراءة الـconnection string بـfallback: `GetConnectionString(\"shopdb\") ?? \"Host=localhost;…\"`.",
                 "solution": "",
                 "resources": [
                     {"label": "Aspire: Build your first app", "url": "https://aspire.dev/get-started/first-app/"},
                     {"label": "Add Aspire to an existing app", "url": "https://aspire.dev/get-started/add-aspire-existing-app/"},
                     {"label": "Migrate from Docker Compose to Aspire", "url": "https://aspire.dev/app-host/migrate-from-docker-compose/"},
                 ]},
                {"id": "t2", "title": "discovery + resilience في نداء بين خدمتين",
                 "md": "خلّي خدمة تنادي خدمة تانية بالاسم عبر `HttpClient` مُسجَّل بـ`AddHttpClient<T>` مع discovery وstandard resilience، وطبّق fallback مُعلَن عند الفشل، وأثبت بـAspire إنك تقدر توقف الخدمة المعتمدة عليها والنظام يفضل يرد (بـdegradation).",
                 "criteria": [
                     "`BaseAddress` بصيغة `https+http://<resource>` (بلا منفذ)",
                     "`WithReference(target).WaitFor(target)` في AppHost",
                     "resilience مطبّق (افتراضيًا عبر ServiceDefaults أو pipeline مسمّى من درس 5.2.4)",
                     "fallback مُعلَن: header `X-Degraded` + مقياس + لوج — بلا استثناء يطير للمستخدم",
                     "إثبات عملي: أوقف الخدمة المعتمدة (من اللوحة) → الخدمة الأولى بترد 200 مع degraded، وبتتعافى لما ترجع",
                     "توثيق ميزانية المهلة: timeout العميل < timeout الطرف الأمامي (جدول من `docs/timeout-budget.md`)",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Aspire service discovery", "url": "https://aspire.dev/fundamentals/service-discovery/"},
                     {"label": "Scheme selectors (aka.ms/dotnet/sdschemes)", "url": "https://aka.ms/dotnet/sdschemes"},
                     {"label": "C# Service Defaults", "url": "https://aspire.dev/get-started/csharp-service-defaults/"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET Aspire docs", "url": "https://aspire.dev/"},
                {"label": "Aspire health checks and readiness gates", "url": "https://aspire.dev/fundamentals/health-checks/"},
                {"label": "Console & worker apps in Aspire", "url": "https://aspire.dev/app-host/console-apps/"},
                {"label": ".NET Aspire on Microsoft Learn", "url": "https://learn.microsoft.com/dotnet/aspire/"},
                {"label": "HTTP resilience in .NET", "url": "https://learn.microsoft.com/dotnet/core/resilience/http-resilience"},
                {"label": "eShop sample (Aspire + microservices)", "url": "https://github.com/dotnet-architecture/eShop"},
            ]},
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # s5-m3-l2 — لوحة Aspire والتشخيص المحلي
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s5-m3-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الدرس اللي فات شغّلنا النظام بأمر واحد. دلوقتي السؤال الأصعب:
**طلب فشل — فين المشكلة؟** في gateway؟ في orders؟ في نداء catalog؟ في مستهلك RabbitMQ؟ في DB؟

من غير تتبع موزّع، الإجابة بتيجي من `Console.WriteLine` في 5 نوافذ طرفية ومحاولة مطابقة التوقيتات يدويًا.
**لوحة Aspire** بتجمع الإشارات التلاتة — **logs · metrics · traces** — من كل الموارد (بما فيها الـcontainers)
في مكان واحد، وبتربط اللوج بالـtrace تلقائيًا. ومن Aspire 13.6 اللوحة بتخزن في **SQLite**
فتقدر ترجع لـ**تشغيلات سابقة** (run history) وتقارن بينها.

الهدف مش «أشوف لوحة حلوة» — الهدف **مهارة تشخيص**: منهجية ثابتة توصلك لسبب فشل عبر سلسلة خدمات في دقايق.
"""},
            {"type": "terms", "items": [
                {"term": "OTLP", "def": "OpenTelemetry Protocol — الطريقة الموحدة لإرسال traces/metrics/logs. اللوحة عندها مستقبل gRPC (4317/18889) وHTTP (4318/18890)."},
                {"term": "Trace / Span", "def": "الـtrace = رحلة طلب واحد. الـspan = وحدة عمل جواه (نداء HTTP، استعلام DB، معالجة رسالة) بمدته وسماته وحالته."},
                {"term": "Trace Context Propagation", "def": "تمرير `traceparent` عبر HTTP/الوسيط — هو اللي يخلي spans من خدمات مختلفة تتجمع في trace واحد."},
                {"term": "Structured Logs", "def": "لوجات بقوالب وحقول (`{OrderId}`) مش نصوص — قابلة للبحث والربط بالـtrace في اللوحة."},
                {"term": "Log–Trace Correlation", "def": "ربط كل سطر لوج بالـ`TraceId` الحالي — تفتح الـtrace فتلاقي لوجاته جنبه."},
                {"term": "Resource Service", "def": "القناة اللي اللوحة بتعرف منها الموارد وحالتها ومنافذها ولوجات الـconsole (بتشتغل تلقائيًا مع AppHost)."},
                {"term": "Run / Run History", "def": "تشغيل واحد للـAppHost. من 13.6 اللوحة بتحتفظ لحد **10 تشغيلات** لكل تطبيق (read-only) مع run selector وتثبيت (pin)."},
                {"term": "API Key / Login Token", "def": "اللوحة مؤمّنة افتراضيًا: token للمتصفح و`x-otlp-api-key` لـOTLP ingest. `--allow-anonymous` للتطوير المحلي فقط."},
                {"term": "Telemetry Limits", "def": "`DASHBOARD__TELEMETRYLIMITS__MAX{LOG,TRACE}COUNT` (100,000 افتراضيًا) و`MAXMETRICSCOUNT` (50,000 لكل بُعد) — اللوحة للتطوير مش تخزين دائم."},
                {"term": "Cardinality", "def": "عدد القيم المختلفة لـtag. لو حطيت `OrderId` كـtag في مقياس → آلاف السلاسل الزمنية وانهيار الذاكرة. (درس 2.3.5)"},
            ]},
            {"type": "heading", "level": 2, "text": "1) تشغيل اللوحة: 3 طرق"},
            {"type": "code", "lang": "bash", "title": "مع AppHost · standalone container · CLI", "code": r'''
# ═══ ① تلقائيًا مع AppHost (الأشهر في التطوير) ═══
dotnet run --project src/Shop.AppHost
#   → اللوحة بتفتح في المتصفح، وكل مورد بيبعت OTLP تلقائيًا
#   → الـAppHost بيحقن للخدمات: OTEL_EXPORTER_OTLP_ENDPOINT + OTEL_EXPORTER_OTLP_HEADERS (api key) + OTEL_SERVICE_NAME

# ═══ ② standalone: لخدمة/لغة مش تحت AppHost (Java/Go/Python أو خدمة قديمة) ═══
docker run --rm -d --name aspire-dashboard \
  -p 127.0.0.1:18888:18888 \
  -p 127.0.0.1:4317:18889 \
  -p 127.0.0.1:4318:18890 \
  mcr.microsoft.com/aspire/dashboard:latest      # اسم بديل مكافئ: mcr.microsoft.com/dotnet/aspire-dashboard:13
#   18888 = واجهة اللوحة · 4317→18889 = OTLP/gRPC · 4318→18890 = OTLP/HTTP
#   ★ اربط على 127.0.0.1 فقط — اللوحة بتشوف لوجاتك وأسرارك المحتملة

# مع تسجيل دخول معطّل (تطوير محلي فقط، بلا أي بيانات حقيقية):
docker run --rm -d --name aspire-dashboard \
  -p 127.0.0.1:18888:18888 -p 127.0.0.1:4317:18889 -p 127.0.0.1:4318:18890 \
  -e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true \
  mcr.microsoft.com/aspire/dashboard:latest

# ★ الاحتفاظ بالبيانات بين إعادات التشغيل (13.6):
docker run --rm -d --name aspire-dashboard \
  -p 127.0.0.1:18888:18888 -p 127.0.0.1:4317:18889 -p 127.0.0.1:4318:18890 \
  -e ASPIRE_DASHBOARD_PERSISTENCE_MODE=Resume \
  -e ASPIRE_DASHBOARD_APPLICATION_NAME=shop-local \
  -e ASPIRE_DASHBOARD_DATA_DIRECTORY=/data \
  -v aspire-dashboard-data:/data \
  mcr.microsoft.com/aspire/dashboard:latest

# ═══ ③ عبر Aspire CLI (بلا docker) ═══
aspire dashboard run                                   # افتراضي: UI 18888، gRPC 4317، HTTP 4318
aspire dashboard run --allow-anonymous                 # تطوير محلي فقط
aspire dashboard run --otlp-grpc-url http://localhost:4317

# ═══ ⑤ توصيل تطبيق خارجي باللوحة ═══
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_EXPORTER_OTLP_HEADERS="x-otlp-api-key=<key-from-dashboard-output>"
export OTEL_SERVICE_NAME="orders-api"
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=dev"

# ⚠ token المتصفح بيتغيّر مع كل تشغيل — اطبعه من مخرجات `docker run` (رابط /login?t=…)
'''},
            {"type": "table", "head": ["المتغير / الخيار", "الافتراضي", "الاستخدام"], "rows": [
                ["`ASPNETCORE_URLS`", "`http://localhost:18888`", "منفذ واجهة اللوحة"],
                ["`ASPIRE_DASHBOARD_OTLP_ENDPOINT_URL`", "`http://localhost:18889` (داخل الـcontainer)", "OTLP/gRPC — التطبيقات بتبعت له"],
                ["`ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL`", "`http://localhost:18890`", "OTLP/HTTP (`POST /v1/traces|/v1/metrics|/v1/logs`)"],
                ["`ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS`", "غير مفعّل", "يلغي token المتصفح وapi key — **تطوير محلي فقط**"],
                ["`x-otlp-api-key` (header)", "مولّد تلقائيًا", "تأمين OTLP ingest في الوضع standalone"],
                ["`ASPIRE_DASHBOARD_PERSISTENCE_MODE`", "`None` (standalone) / `Run` (مع AppHost)", "`Resume` = الاحتفاظ بنفس الـrun بين إعادات التشغيل"],
                ["`ASPIRE_DASHBOARD_APPLICATION_NAME`", "—", "اسم التطبيق (بيفصل البيانات المخزنة)"],
                ["`ASPIRE_DASHBOARD_DATA_DIRECTORY`", "مؤقت", "مسار قاعدة SQLite"],
                ["`DASHBOARD__TELEMETRYLIMITS__MAXLOGCOUNT` / `MAXTRACECOUNT`", "100,000", "حدود التخزين — اللوحة مش تخزين دائم"],
                ["`DASHBOARD__TELEMETRYLIMITS__MAXMETRICSCOUNT`", "50,000 لكل بُعد", "حماية من cardinality عالية"],
            ]},
            {"type": "heading", "level": 2, "text": "2) إزاي الخدمة بتبعت إشارات مفيدة (مش افتراضية بس)"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Diagnostics/Instrumentation.cs", "title": "مصدر Activity مخصص + مقاييس + ربط اللوج بالـtrace", "code": r'''
// requires: using System.Diagnostics; using System.Diagnostics.Metrics;

/// <summary>
/// ★ `AddSource(builder.Environment.ApplicationName)` في ServiceDefaults هو اللي بيخلي المصدر ده يظهر في اللوحة.
/// الاسم مهم: لو اسم الـActivitySource مختلف عن اسم التطبيق، أضفه صراحةً بـAddSource("Shop.Orders").
/// </summary>
public static class OrderInstrumentation
{
    public static readonly ActivitySource Activities = new("Shop.Orders", "1.0.0");
    private static readonly Meter Meter = new("Shop.Orders", "1.0.0");

    public static readonly Counter<long> OrdersPlaced   = Meter.CreateCounter<long>("shop.orders.placed");
    public static readonly Counter<long> OrdersFailed   = Meter.CreateCounter<long>("shop.orders.failed");
    public static readonly Histogram<double> PlaceOrderDuration =
        Meter.CreateHistogram<double>("shop.orders.place_order.duration", "ms", "مدة إنشاء الطلب");

    /// <summary>span لعملية أعمال واحدة — بسمات منخفضة cardinality.</summary>
    public static Activity? StartPlaceOrder(Guid orderId)
    {
        var activity = Activities.StartActivity("orders.place", ActivityKind.Internal);
        if (activity is null) return null;

        activity.SetTag("order.id", orderId.ToString());            // ✓ معرّف = مفيد للتتبع (مش مقياس)
        activity.SetTag("order.channel", "web");                    // ✓ cardinality منخفضة
        // ⚠ ممنوع: activity.SetTag("order.total", total) لو هيتحوّل لمقياس — استخدمه كـevent/لوج
        return activity;
    }
}

// ═══ الاستخدام في الـhandler ═══
public static class OrdersApi
{
    public static async Task<IResult> PlaceOrder(PlaceOrderRequest req, OrdersDbContext db,
                                                 ILogger<Program> log, CancellationToken ct)
    {
        using var activity = OrderInstrumentation.StartPlaceOrder(req.OrderId);
        var sw = Stopwatch.StartNew();

        try
        {
            // درس 4.2.1: الـDomain بياخد خطوط بقيمة مطلقة (minor units)
            var order = Order.Place(req.OrderId,
                req.Lines.Select(l => new OrderLine(l.ProductId, l.Quantity, l.UnitPriceMinor)).ToList());
            db.Orders.Add(order);
            await db.SaveChangesAsync(ct);                          // ✓ Outbox بيتكتب في نفس المعاملة (4.2.3)

            OrderInstrumentation.OrdersPlaced.Add(1, new("channel", "web"));

            // ★ لوج منظّم بحقول — بيربط نفسه بالـTraceId الحالي تلقائيًا
            log.LogInformation("Order {OrderId} placed with {LineCount} lines in {Elapsed}ms",
                order.Id, order.Lines.Count, sw.ElapsedMilliseconds);

            // ✓ event على الـspan (بدل tag لو القيمة متغيرة/كبيرة)
            activity?.AddEvent(new ActivityEvent("placed",
                tags: new ActivityTagsCollection { ["lines"] = order.Lines.Count }));

            return Results.Created($"/api/orders/{order.Id}", new { order.Id });
        }
        catch (Exception ex)
        {
            OrderInstrumentation.OrdersFailed.Add(1, new("reason", ex.GetType().Name));   // ✓ cardinality منخفضة
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.AddTag("exception.type", ex.GetType().FullName);
            log.LogError(ex, "Failed to place order {OrderId}", req.OrderId);
            throw;                                                  // IExceptionHandler يتعامل معه (درس 2.1.4)
        }
        finally
        {
            OrderInstrumentation.PlaceOrderDuration.Record(sw.Elapsed.TotalMilliseconds);
        }
    }
}

public sealed record PlaceOrderRequest(Guid OrderId, IReadOnlyList<OrderLineDto> Lines);
public sealed record OrderLineDto(Guid ProductId, int Quantity, long UnitPriceMinor);
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Program.cs", "title": "لوجات موحّدة: Serilog + correlation عبر HTTP والوسيط", "code": r'''
// requires: using Serilog; using Serilog.Context; using Serilog.Core; using Serilog.Events;
// packages:  Serilog.AspNetCore · Serilog.Sinks.OpenTelemetry · Serilog.Enrichers.Environment

builder.Host.UseSerilog((ctx, services, cfg) => cfg
    .ReadFrom.Configuration(ctx.Configuration)
    .Enrich.FromLogContext()
    // ★ الحقول دي هي اللي بتخلي اللوج قابل للبحث والربط في اللوحة
    .Enrich.WithProperty("service", "orders")
    .Enrich.WithProperty("version", typeof(Program).Assembly.GetName().Version?.ToString() ?? "0.0.0")
    .Enrich.With<TraceIdEnricher>()
    .WriteTo.Console(outputTemplate:
        "[{Timestamp:HH:mm:ss} {Level:u3}] [{TraceId}] {Message:lj}{NewLine}{Exception}")
    .WriteTo.OpenTelemetry(options =>                       // ✓ تصدير اللوجات كـOTLP (حزمة Serilog.Sinks.OpenTelemetry)
    {
        // الـendpoint والـheaders بيجوا من OTEL_* اللي حقنها الـAppHost
        options.ResourceAttributes = new Dictionary<string, object> { ["service.name"] = "orders" };
    }));

// ★ middleware: correlation id واحد عبر الطلب كله (ومروره للخارج)
app.Use(async (context, next) =>
{
    var correlationId = context.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                        ?? Activity.Current?.TraceId.ToString()
                        ?? Guid.NewGuid().ToString("N");

    context.Response.Headers["X-Correlation-Id"] = correlationId;
    using (LogContext.PushProperty("CorrelationId", correlationId))
    {
        await next();
    }
});

// وفي مستهلك MassTransit: خد الـtrace من رؤوس الرسالة (الوسيط بينقل traceparent تلقائيًا مع OTel)
public sealed class OrderPlacedConsumer(ILogger<OrderPlacedConsumer> log) : IConsumer<OrderPlaced>
{
    public Task Consume(ConsumeContext<OrderPlaced> context)
    {
        // ✓ MassTransit + OTel: الـspan بيتربط بالـtrace الأصلي للطلب تلقائيًا (درس 5.2.1 فعّل AddMassTransitOpenTelemetry)
        log.LogInformation("Consumed {MessageId} for order {OrderId}", context.MessageId, context.Message.OrderId);
        return Task.CompletedTask;
    }
}

/// <summary>يضيف TraceId لكل سطر لوج — الربط الأساسي بين اللوجات والـtraces.</summary>
internal sealed class TraceIdEnricher : ILogEventEnricher
{
    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory factory) =>
        logEvent.AddPropertyIfAbsent(factory.CreateProperty(
            "TraceId", Activity.Current?.TraceId.ToString() ?? "-", destructureObjects: false));
}
'''},
            {"type": "callout", "kind": "tip", "title": "الربط اللي بيوفر ساعات: log ↔ trace ↔ metric",
             "md": """
**الثلاثة لازم يشتركوا في معرّفات واحدة:**
- **TraceId** في كل سطر لوج (enricher أو `Serilog` + OTel logs exporter) → في اللوحة تفتح الـtrace وتلاقي لوجاته.
- **CorrelationId** في الرؤوس (`X-Correlation-Id`) ويمر للخدمات التالية **ولرسائل الوسيط** → تتبع تدفق أعمال عبر أحداث غير متزامنة.
- **سمات منخفضة cardinality** في المقاييس (`channel`, `reason`, `endpoint`) → تقدر تجمّع وتنذر؛ المعرّفات (OrderId) مكانها الـtags واللوجات مش المقاييس.

**قواعد عملية:**
1. **بلا لوجات نصية** — `log.LogInformation("Order {OrderId} placed", id)` مش `$"Order {id} placed"` (المنظّمة بتبقى قابلة للبحث).
2. **بلا أسرار في اللوجات أو الـtags** — ولا connection strings، ولا tokens، ولا PAN. افحص قبل ما ترفع اللوحة لفريق.
3. **`SetStatus(ActivityStatusCode.Error)`** على الـspan عند الفشل — اللوحة بتلوّن الـtrace أحمر وتقدر تفلتر عليه.
4. **event على الـspan بدل tag** للقيم الكبيرة/المتغيرة (تجنب تضخيم الـspans).
5. **لا تقيس ما لا تنذر عليه** — كل مقياس بيكلّف ذاكرة في اللوحة وفي الخلفية الإنتاجية.
"""},
            {"type": "heading", "level": 2, "text": "3) منهجية تشخيص فشل عبر سلسلة خدمات"},
            {"type": "steps", "title": "6 خطوات ثابتة (جرّبها على فشل حقيقي)", "items": [
                {"title": "ابدأ من الطلب، مش من اللوجات", "md": "في تبويب **Traces**: فلتر بالخدمة (gateway) + الحالة (Error) أو بمدة > 1s. اختار الطلب الفاشل. لو معاك `X-Correlation-Id` من العميل، ابحث بيه في **Structured logs**.", "code": "# من الطرفية بدل اللوحة (13.6+؛ الأوامر موجودة لكن الوسائط بتتطور — شوف المساعدة)\naspire otel --help\naspire otel traces\naspire otel logs"},
                {"title": "اقرأ الـwaterfall: فين الوقت راح؟", "md": "أكبر span بياخد الوقت هو المشتبه الأول. قارن: `POST /api/orders` (gateway) → `orders.place` → `HTTP GET catalog` → ` Npgsql command`. لو span الوسيط (publish) موجود بس مفيش consume → المشكلة عند المستهلك مش الناشر.", "code": ""},
                {"title": "افتح اللوجات المرتبطة بالـtrace", "md": "من صفحة الـtrace: **Logs** → هتشوف لوجات كل الخدمات لنفس الـTraceId بالترتيب. ابحث عن أول `Error`/`Warning` — أول خطأ في الزمن هو السبب غالبًا، والباقي توابع.", "code": ""},
                {"title": "افحص الحالة والاعتمادات", "md": "تبويب **Resources**: هل مورد غير صحي؟ (health check فاشل = `WaitFor` علق المعتمدين). افتح `/health` بتاع الخدمة وشوف **أي** فحص فشل (db؟ redis؟ rabbit؟) — درس 2.3.7.", "code": "curl -s http://localhost:<port>/health | jq\n# أو من اللوحة: endpoint المورد → /health"},
                {"title": "قارن بالمقاييس (مش بالحدس)", "md": "تبويب **Metrics**: `shop.orders.failed` بـ`reason` → نوع الفشل. `http.server.request.duration` p95 → بطء ولا خطأ؟ `shop.orders.place_order.duration` → فين الجزء البطيء. لو مقياس اختفى فجأة = الخدمة وقفت تبعت (مش إن المشكلة اختفت).", "code": ""},
                {"title": "أعد الإنتاج ثم صلح", "md": "من 13.6: لو التشغيل انتهى، افتح الـ**run selector** وادخل على الـrun السابق (read-only) — أو **ثبّت (pin)** الـrun اللي فيه العطل عشان ما يتحذفش. بعدين أعد السيناريو محليًا بنفس البيانات، وحوّله لاختبار تكامل (درس 5.3.3) عشان ما يرجعش.", "code": "# الـrun history بتتحفظ لحد 10 تشغيلات لكل تطبيق\n# ثبّت الـrun المهم من الـrun selector في رأس اللوحة"}]},
            {"type": "table", "head": ["العَرَض", "أول مكان تبص فيه", "السبب الشائع", "الإصلاح"], "rows": [
                ["الطلب بيرجع 504 من الـgateway", "أطول span في الـwaterfall", "خدمة تابعة بطيئة/معلّقة ومفيش timeout كفاية", "ميزانية مهلة (5.2.4) + hedging للقراءات"],
                ["span فيه `HTTP GET catalog` بحالة Error وبعده retry×2", "attributes بتاعة الـspan (`http.response.status_code`)", "circuit breaker فتح أو الخدمة واقعـة", "شوف `shop.orders.failed{reason=BrokenCircuitException}` + صحة catalog"],
                ["الحدث اتنشر بس مفيش span للاستهلاك", "تبويب Resources → مستهلك الرسائل", "المستهلك مش شغال / مفيش consumer على الطابور", "`rabbitmqctl list_queues name messages consumers` (درس 5.2.1)"],
                ["الرسائل بتتكرر والمستهلك بيعالجها مرتين", "Structured logs بـ`MessageId`", "إعادة تسليم بلا idempotency", "درس 5.2.5: dedup + قيد فريد"],
                ["الخدمة بتبدأ وتفشل في أول طلب", "لوجات الـstartup + حالة المورد", "بدأت قبل ما DB تجهز (بلا `WaitFor`)", "`WaitFor(db)` + `EnableRetryOnFailure`"],
                ["p95 عالي بس p50 طبيعي", "Metrics → histogram", "tail latency: GC، pool connections صغير، استعلام بلا فهرس", "درس 3.3.1/3.4.1 (EXPLAIN) + فحص GC"],
                ["اللوحة مفيهاش traces لخدمة واحدة", "لوجات الـstartup للخدمة + `OTEL_EXPORTER_OTLP_ENDPOINT`", "الخدمة مش بتنادي `AddServiceDefaults()` أو اسم الـActivitySource مختلف", "أضف `AddSource(\"<اسم المصدر>\")` صراحةً"],
                ["المقاييس اختفت فجأة", "حالة المورد + حدود اللوحة", "وصلت لحد `MAXMETRICSCOUNT` (cardinality عالية) أو الخدمة وقفت", "قلّل السمات + افحص tag فيه معرّفات"],
            ]},
            {"type": "callout", "kind": "danger", "title": "اللوحة أداة تطوير — مش backend للـobservability في الإنتاج",
             "md": """
- **التخزين محدود ومؤقت**: افتراضيًا standalone بيحذف قاعدة البيانات عند الإيقاف (`PERSISTENCE_MODE=None`)،
  ومع AppHost بيحتفظ لحد **10 تشغيلات**. الحدود: 100,000 لوج/trace و50,000 نقطة مقياس لكل بُعد.
- **البيانات بتضيع** عند إعادة التشغيل/الحذف — أي حاجة تحتاج **احتفاظ** أو **إنذار** لازم تروح لخلفية حقيقية
  (Grafana + Prometheus + Loki/Tempo، أو Azure Monitor/App Insights، أو أي OTLP backend) — ده موضوع المرحلة 6.
- **الأمان**: اللوحة بتشوف لوجات وtraces فيها بيانات حساسة محتملة.
  اربط على `127.0.0.1`، ولا تستخدم `--allow-anonymous` إلا محليًا وبلا بيانات حقيقية، ولا تشارك اللوحة على الشبكة العامة.
- **exponential histograms وsummaries مش مدعومة** في اللوحة — استخدم histograms صريحة.
- **OTLP/HTTP** بيقبل `application/x-protobuf` أو `application/json` (غير كده → 415).
- **لا تخلط environments**: بلا لوحة واحدة تستقبل telemetry من dev وstaging مع بعض بلا فصل بـ`OTEL_RESOURCE_ATTRIBUTES`.

✅ **القاعدة**: استخدم اللوحة للتشخيص المحلي السريع، وصدّر نفس الإشارات لخلفية إنتاجية **بنفس الكود**
(الفرق الوحيد هو `OTEL_EXPORTER_OTLP_ENDPOINT`). ده معنى «telemetry قابل للنقل».
"""},
            {"type": "code", "lang": "json", "filename": "src/Shop.Orders/appsettings.Development.json", "title": "تشغيل خدمة منفصلة نحو لوحة standalone", "code": r'''
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft.AspNetCore": "Warning",
        "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
        "System.Net.Http.HttpClient": "Warning"
      }
    }
  },

  "//": "OTEL_* ممكن تتحط كمتغيرات بيئة بدل appsettings (الـAppHost بيحقنها تلقائيًا)",
  "OTEL_SERVICE_NAME": "orders",
  "OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=dev,service.version=1.4.0",
  "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
  "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
  "OTEL_TRACES_SAMPLER": "parentbased_traceidratio",
  "OTEL_TRACES_SAMPLER_ARG": "1.0",

  "//sampling": "★ محليًا 1.0 (كل الطلبات). في الإنتاج: نسبة أو ذيلي (tail-based) — عيّن كل الأخطاء والبطيء"
}
'''},
            {"type": "checkpoints", "items": [
                "أشغّل لوحة Aspire بثلاث طرق (مع AppHost، container standalone، CLI) وأفهم المنافذ والأمان والحدود.",
                "أصدّر traces/metrics/logs من خدمتي بإشارات مفيدة: ActivitySource مخصص، سمات منخفضة cardinality، لوجات منظمة مربوطة بـTraceId.",
                "أربط log ↔ trace ↔ metric بمعرّفات مشتركة (TraceId + CorrelationId) عبر HTTP والوسيط.",
                "أتبع منهجية 6 خطوات لتشخيص فشل عبر سلسلة خدمات (waterfall → لوجات مرتبطة → صحة الموارد → مقاييس → إعادة إنتاج).",
                "أعرف إن اللوحة للتطوير، وأنقل نفس الإشارات لخلفية إنتاجية بتغيير الـendpoint فقط.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه المنافذ الثلاثة للوحة standalone؟",
                 "options": [
                     "18888 UI · 4317 OTLP/gRPC · 4318 OTLP/HTTP (محوّلة من 18889/18890 داخل الـcontainer)",
                     "8080/9090/5000",
                     "18888 بس",
                     "4317 UI و18888 OTLP",
                 ], "answer": 0,
                 "explain": "`-p 18888:18888 -p 4317:18889 -p 4318:18890`. واجهة اللوحة 18888، ومستقبلات OTLP على 4317 (gRPC) و4318 (HTTP) من ناحية المضيف."},
                {"q": "ليه `AddSource(builder.Environment.ApplicationName)` مهم في tracing؟",
                 "options": [
                     "شكلي",
                     "لأن OTel بيسجّل بس من الـActivitySources المعلنة — لو اسم مصدرك المخصص مختلف عن اسم التطبيق، الـspans بتاعتك مش هتظهر",
                     "بيسرّع التصدير",
                     "مطلوب للـmetrics بس",
                 ], "answer": 1,
                 "explain": "الحل: إما تسمّي `ActivitySource` باسم التطبيق، أو تضيف `AddSource(\"Shop.Orders\")` صراحةً في ConfigureOpenTelemetry."},
                {"q": "tag فيه `OrderId` على مقياس (Counter). المشكلة؟",
                 "options": [
                     "مفيش مشكلة",
                     "cardinality عالية: كل طلب = سلسلة زمنية جديدة → انفجار ذاكرة ووصول لحد اللوحة (50,000 لكل بُعد)",
                     "بيبطّأ التصدير شوية",
                     "بيتعارض مع الـtraces",
                 ], "answer": 1,
                 "explain": "المعرّفات مكانها اللوجات وtags الـspans/events. المقاييس بتاخد سمات محدودة القيم: `channel`, `reason`, `endpoint`, `status`."},
                {"q": "أول خطوة في تشخيص طلب فشل عبر 4 خدمات؟",
                 "options": [
                     "قراءة لوجات كل خدمة بالترتيب",
                     "افتح الـtrace بتاع الطلب وشوف الـwaterfall: أكبر span وأول span بحالة Error",
                     "إعادة تشغيل الخدمات",
                     "زيادة الـtimeout",
                 ], "answer": 1,
                 "explain": "الـwaterfall بيحدد **مكان** المشكلة في ثواني (زمن/خطأ)، وبعدين اللوجات المرتبطة بنفس الـTraceId بتديك **السبب**. العكس بيضيع وقت."},
                {"q": "الحدث اتنشر (فيه span للنشر) بس مفيش span للاستهلاك. تشخّص إزاي؟",
                 "options": [
                     "أعيد النشر",
                     "أفحص المستهلك: هل هو شغال وصحي؟ وهل فيه consumer متصل بالطابور؟ (`rabbitmqctl list_queues name messages consumers`) + هل الرسائل بتتكدس في `_error`؟",
                     "أزيد الـprefetch",
                     "أغيّر الـexchange",
                 ], "answer": 1,
                 "explain": "التتبع بيوقف عند حد العملية. النشر نجح = المشكلة في الطرف التاني: مستهلك مش شغال، binding غلط، أو الرسالة راحت لطابور الأخطاء (درس 5.2.1)."},
                {"q": "ممكن تعتمد على لوحة Aspire كخلفية observability للإنتاج؟",
                 "options": [
                     "نعم، بتخزن في SQLite",
                     "لا — التخزين محدود ومؤقت (10 تشغيلات، 100k trace/log، 50k مقياس/بُعد) ومفيش إنذارات/احتفاظ. صدّر OTLP لخلفية إنتاجية (Grafana/Prometheus/Azure Monitor)",
                     "نعم لو فعّلت Resume",
                     "نعم للـtraces فقط",
                 ], "answer": 1,
                 "explain": "`Resume` بيخلي الـrun يعيش بين إعادات التشغيل — مفيد للتطوير والتحقيق، مش بديل عن الاحتفاظ والإنذار في الإنتاج. الكود نفسه بيتنقل: غيّر `OTEL_EXPORTER_OTLP_ENDPOINT`."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تشخيص فشل مُفتعل بمنهجية 6 خطوات",
                 "md": "افتعل 3 أعطال مختلفة في نظامك (أوقف خدمة معتمدة، خلي فحص صحة يفشل، ارمِ استثناء في مستهلك رسائل)، وشخّص كل واحد **من اللوحة فقط** باستخدام الخطوات الست. اكتب تقرير تشخيص لكل عطل: العَرَض، أول span/لوج دلّك، السبب الجذري، الإصلاح، وإزاي تمنعه (اختبار/إنذار).",
                 "criteria": [
                     "3 أعطال مختلفة الأنواع (HTTP تابع · صحة مورد · مستهلك رسائل) — كل واحد متوثق",
                     "لكل عطل: لقطة/وصف للـwaterfall + أول سطر لوج مرتبط بالـTraceId + المقياس اللي أثبت الحالة",
                     "السبب الجذري مذكور بدقة (مش «فيه مشكلة في الشبكة»)",
                     "الإصلاح مطبّق بكود، + إجراء وقائي (اختبار تكامل أو إنذار) لكل عطل",
                     "مفيش `Console.WriteLine` في مسار التشخيص — لوجات منظمة فقط",
                     "الوقت المستغرق لكل تشخيص مسجّل (قارن بعد التمرين الثاني)",
                 ],
                 "hint": "خلي الأعطال قابلة للتفعيل بمفتاح تكوين (`Orders__FaultInjection__CatalogTimeout=true`) عشان تقدر تعيد السيناريو بدقة وتحوله لاختبار.",
                 "solution": "",
                 "resources": [
                     {"label": "Aspire dashboard — standalone", "url": "https://aspire.dev/dashboard/standalone/"},
                     {"label": "Aspire dashboard — configuration reference", "url": "https://aspire.dev/dashboard/configuration/"},
                 ]},
                {"id": "t2", "title": "إشارات مخصصة: trace + metric + log مربوطين",
                 "md": "أضف لتدفق أعمال واحد في مشروعك (إنشاء طلب مثلًا): span مخصص بسمات منخفضة cardinality، مقياسَين (counter + histogram)، لوجات منظمة مربوطة بـTraceId، و`CorrelationId` يمر عبر HTTP والوسيط. أثبت في اللوحة إنك تقدر تبدأ من مقياس مرتفع وتوصل للـtrace ثم للوج السبب.",
                 "criteria": [
                     "`ActivitySource` مخصص ومسجّل في `ConfigureOpenTelemetry` (يظهر فعلًا في اللوحة)",
                     "الـspan فيه `SetStatus(Error)` + `exception.type` عند الفشل — والـtrace بيتلوّن أحمر",
                     "counter + histogram بسمات منخفضة cardinality فقط (مفيش معرّفات في المقاييس)",
                     "كل سطر لوج فيه TraceId (enricher) + اللوجات بتظهر مرتبطة بالـtrace في اللوحة",
                     "`X-Correlation-Id` بيتولّد/بيمرر في الرد وفي الرسائل — وتقدر تبحث بيه في اللوجات",
                     "لقطة تشرح المسار: مقياس → trace → لوج → سبب",
                     "لا أسرار/بيانات حساسة في اللوجات أو الـtags (افحص يدويًا واذكر إزاي تأكدت)",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "OpenTelemetry with OTLP and the Aspire Dashboard", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/observability-otlp-example"},
                     {"label": "OpenTelemetry .NET", "url": "https://opentelemetry.io/docs/languages/dotnet/"},
                     {"label": "Serilog", "url": "https://serilog.net/"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Aspire dashboard — standalone", "url": "https://aspire.dev/dashboard/standalone/"},
                {"label": "Aspire dashboard — configuration", "url": "https://aspire.dev/dashboard/configuration/"},
                {"label": "Aspire 13.6: dashboard persistence & run history", "url": "https://devblogs.microsoft.com/aspire/whats-new-aspire-13-6/"},
                {"label": "Dashboard security considerations", "url": "https://learn.microsoft.com/dotnet/aspire/fundamentals/dashboard/security-considerations"},
                {"label": "Observability with OpenTelemetry in .NET", "url": "https://learn.microsoft.com/dotnet/core/diagnostics/observability-with-otel"},
                {"label": "OpenTelemetry Protocol (OTLP) spec", "url": "https://opentelemetry.io/docs/specs/otlp/"},
            ]},
        ],
    },
]
