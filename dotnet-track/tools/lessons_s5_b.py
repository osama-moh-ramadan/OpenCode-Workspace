"""Stage 5, Module 1 — Decomposition & communication (lessons 3-4 of 4): gRPC & YARP gateway."""

TODAY = "2026-10-22"

LESSONS_S5_B = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s5-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
بين الخدمات، JSON/REST بيكلفك: تسلسل أكبر، عقود مكتوبة بإيدك (وبتختلف عن التنفيذ)،
وبلا streaming حقيقي. **gRPC** بيحل التلاتة: عقود `.proto` مولّدة لكود في الطرفين (تغيير العقد = خطأ ترجمة)،
بروتوكول ثنائي أصغر، HTTP/2 (multiplexing، بلا head-of-line بين النداءات)، ومهل (deadlines) وإلغاء مدمجين.

القاعدة العملية في .NET: **gRPC داخليًا بين خدماتك، وREST/OpenAPI خارجيًا للمتصفحين والشركاء**.
الدرس ده: عقود proto صحيحة (وقابلة للتطور)، خادم بـinterceptors، عميل بـdeadline وresilience،
streaming، واختبارات — وأخطاء بتخلّي gRPC أبطأ من REST لو عملتها.
"""},
            {"type": "terms", "items": [
                {"term": "`.proto` / Protocol Buffers", "def": "لغة تعريف العقد: رسائل وخدمات بأرقام حقول. **رقم الحقل هو الهوية** — الاسم للراحة فقط."},
                {"term": "Unary / Streaming RPC", "def": "4 أنماط: نداء واحد/رد واحد، server streaming، client streaming، bidirectional."},
                {"term": "Deadline", "def": "مهلة زمنية يحملها النداء عبر كل الخدمات. انتهت → `DEADLINE_EXCEEDED` تلقائيًا (بديل timeout اليدوي)."},
                {"term": "Channel مقابل Client", "def": "الـ`GrpcChannel` هو الاتصال (مكلف — **singleton**)، والـclient غلاف خفيف يُنشأ لكل نداء."},
                {"term": "Interceptor", "def": "وسيط على الخادم/العميل: logging، auth، تحويل استثناءات، مقاييس — مكان واحد بدل تكراره."},
                {"term": "Status / StatusCode", "def": "حالة النداء (`OK`, `NotFound`, `InvalidArgument`, `Unavailable`, `DeadlineExceeded`…) — تقابل أكواد HTTP دلاليًا."},
                {"term": "Well-known types", "def": "أنواع جاهزة: `Timestamp`, `Duration`, `Empty`, `Any`, `FieldMask` — استخدمها بدل اختراع equivalents."},
                {"term": "Reflection & Health", "def": "خدمتان إضافيتان: `grpcurl` للاستكشاف في التطوير، وفحص صحة gRPC لـload balancers."},
                {"term": "gRPC-Web", "def": "بروتوكول وسيط للمتصفحات (لا يدعم client streaming/bidi) — تحتاجه لو العميل متصفح مباشرة."},
                {"term": "Backward compatibility", "def": "قواعد proto: إضافة حقل جديد آمن؛ حذف/تغيير رقم أو نوع حقل كاسر (استخدم `reserved`)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) العقود: مشروع proto مشترك"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم وتوليد الكود", "code": r'''
# ── مشروع العقود (يُشارك بين الخدمات — بلا أي تنفيذ) ──
dotnet new classlib -n Shop.Contracts.Grpc -o src/Contracts/Shop.Contracts.Grpc
cd src/Contracts/Shop.Contracts.Grpc
dotnet add package Google.Protobuf
dotnet add package Grpc.Tools                 # مولّد الكود وقت البناء
dotnet add package Grpc.Net.Client            # للأنواع الأساسية (ClientBase)
mkdir -p Protos/v1

# ── الخادم (الخدمة المزوِّدة) ──
dotnet add src/Services/Catalog package Grpc.AspNetCore

# ── العميل (الخدمة المستهلكة) ──
dotnet add src/Services/Orders package Grpc.Net.ClientFactory
dotnet add src/Services/Orders package Microsoft.Extensions.Http.Resilience

# ── أدوات التطوير والتشغيل ──
dotnet add src/Services/Catalog package Grpc.AspNetCore.Server.Reflection   # grpcurl
dotnet add src/Services/Catalog package Grpc.HealthCheck                     # فحص صحة gRPC

# ── أداة سطر الأوامر للاختبار اليدوي ──
# grpcurl -plaintext -d '{"sku":"KB-1"}' localhost:5081 shop.catalog.v1.Catalog/GetProduct
'''},
            {"type": "code", "lang": "xml", "filename": "src/Contracts/Shop.Contracts.Grpc/Shop.Contracts.Grpc.csproj", "title": "توليد الكود من الـprotos", "code": r'''
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <!-- ★ مشروع العقود: client + server stubs معًا، عشان أي خدمة تستخدمه -->
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Google.Protobuf" Version="3.*" />
    <PackageReference Include="Grpc.Net.Client" Version="2.*" />
    <PackageReference Include="Grpc.Tools" Version="2.*" PrivateAssets="All" />
  </ItemGroup>

  <ItemGroup>
    <!-- Client: للمستهلكين · Server: للمزوِّدين -->
    <Protobuf Include="Protos\v1\catalog.proto" GrpcServices="Both" />
    <Protobuf Include="Protos\v1\common.proto"  GrpcServices="None" />
  </ItemGroup>
</Project>
'''},
            {"type": "code", "lang": "text", "filename": "src/Contracts/Shop.Contracts.Grpc/Protos/v1/catalog.proto", "title": "عقد proto3: unary + server streaming + قواعد التطور", "code": r'''
syntax = "proto3";

package shop.catalog.v1;                     // ★ إصدار في اسم الحزمة (v1) — مش في اسم الملف فقط

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";
import "protos/v1/common.proto";

option csharp_namespace = "Shop.Contracts.Grpc.Catalog.V1";

service Catalog {
  // ── unary: نداء/رد ──
  rpc GetProduct(GetProductRequest) returns (Product);
  rpc GetProducts(GetProductsRequest) returns (GetProductsResponse);
  rpc CheckStock(CheckStockRequest) returns (CheckStockResponse);

  // ── server streaming: رد متعدد الأجزاء (تصدير/تقدُّم) ──
  rpc StreamPriceChanges(PriceWatchRequest) returns (stream PriceChange);

  // ── client streaming: رفع دفعات ──
  rpc ImportProducts(stream ProductImportItem) returns (ImportSummary);
}

// ═══ الرسائل ═══
message GetProductRequest {
  // ★ حقل واحد من مجموعة بدائل: استخدم oneof بدل حقول اختيارية غامضة
  oneof identifier {
    string sku = 1;
    string product_id = 2;                   // UUID كنص (proto3 بلا نوع uuid أصلي)
  }
  common.ResponseOptions options = 10;        // حقول اختيارية عامة في آخر الرسالة
}

message Product {
  string product_id = 1;
  string sku = 2;
  string title = 3;
  string description = 4;
  common.Money price = 5;                     // ★ لا تستخدم float/double للمال أبدًا
  int32 available_stock = 6;
  ProductStatus status = 7;
  repeated Attribute attributes = 8;
  google.protobuf.Timestamp updated_at = 9;

  // ✓ إضافة حقل جديد = متوافق خلفيًا (رقم غير مستخدم)
  string brand = 10;

  // ✗ ممنوع: إعادة استخدام رقم محذوف — احجزه
  reserved 11, 12;
  reserved "legacy_code", "old_price";        // الأسماء كمان تُحجز (لأدوات JSON)
}

message Attribute {
  string name = 1;
  string value = 2;
}

enum ProductStatus {
  PRODUCT_STATUS_UNSPECIFIED = 0;             // ★ الصفر لازم يكون «غير محدد» — مش قيمة حقيقية
  PRODUCT_STATUS_DRAFT = 1;
  PRODUCT_STATUS_ACTIVE = 2;
  PRODUCT_STATUS_ARCHIVED = 3;
}

message GetProductsRequest {
  repeated string product_ids = 1;            // ✓ دفعات: نداء واحد بدل N نداءات
  string category_id = 2;
  int32 page_size = 3;                        // الخادم يفرض حدًا أقصى (لا تثق بالعميل)
  string page_token = 4;                      // cursor pagination (درس 2.1.3)
}

message GetProductsResponse {
  repeated Product products = 1;
  string next_page_token = 2;                 // فاضي = مفيش المزيد
  int32 total_size = 3;                       // اختياري: تكلفة عالية — وثّق إنّه تقريبي
}

message CheckStockRequest  { repeated string product_ids = 1; int32 quantity = 2; }
message CheckStockResponse { repeated StockLine lines = 1; bool all_available = 2; }
message StockLine { string product_id = 1; int32 available = 2; bool sufficient = 3; }

message PriceWatchRequest { string category_id = 1; int32 max_items = 2; }
message PriceChange {
  string product_id = 1;
  common.Money old_price = 2;
  common.Money new_price = 3;
  google.protobuf.Timestamp changed_at = 4;
}

message ProductImportItem { string sku = 1; string title = 2; common.Money price = 3; }
message ImportSummary { int32 accepted = 1; int32 rejected = 2; repeated string errors = 3; }
'''},
            {"type": "code", "lang": "text", "filename": "src/Contracts/Shop.Contracts.Grpc/Protos/v1/common.proto", "title": "أنواع مشتركة: المال والخيارات", "code": r'''
syntax = "proto3";
package shop.common;
option csharp_namespace = "Shop.Contracts.Grpc.Common";

// ★ المال: أجزاء أصغر (minor units) + رمز العملة — لا float ولا double
message Money {
  int64 minor_units = 1;      // 25050 = 250.50
  string currency_code = 2;   // "EGP" (ISO 4217)
  int32 exponent = 3;         // 2 → القيمة = minor_units / 10^exponent
}

message ResponseOptions {
  repeated string field_mask_paths = 1;   // لو محتاج إسقاط حقول (قلّل حجم الرد)
  string locale = 2;
  bool include_metadata = 3;
}

message ErrorDetail {
  string code = 1;           // رمز خطأ مستقر (مش رسالة)
  string message = 2;        // رسالة للبشر (لا تعتمد عليها برمجيًا)
  repeated string field_names = 3;
}
'''},
            {"type": "callout", "kind": "warn", "title": "قواعد تطوّر عقود proto (الكسر الصامت بيحصل هنا)",
             "md": """
| التغيير | الحكم | الطريقة |
|---|---|---|
| إضافة حقل جديد برقم غير مستخدم | ✓ متوافق | أضف، والعملاء القدامى يتجاهلوه |
| إضافة قيمة جديدة لـenum | ✓ متوافق | العميل **لازم** يعالج `Unrecognized` (لا استثناء) |
| إضافة RPC جديد للخدمة | ✓ متوافق | — |
| حذف حقل | △ | أوقف استخدامه → `reserved <رقم>` و`reserved "<اسم>"` → احذف |
| تغيير رقم حقل | ✗ كاسر |البيانات هتتفسر غلط بصمت. لا تفعلها أبدًا |
| تغيير نوع حقل | ✗ كاسر (غالبًا) | حقل جديد باسم ورقم جديدين + فترة انتقال |
| إعادة تسمية حقل | ✓ متوافق ثنائيًا / ✗ كاسر لـJSON | الاسم مش جزء من الترميز الثنائي، لكن أدوات JSON/التوثيق تتأثر |
| تغيير اسم RPC/الخدمة/الحزمة | ✗ كاسر | إصدار جديد (`v2`) ودعم الاثنين |

**3 قواعد ذهبية:** ① أرقام الحقول للأبد (احجز المحذوف)، ② الصفر في enum = `UNSPECIFIED`،
③ لا `float`/`double` للمال — استخدم minor units.
"""},
            {"type": "heading", "level": 2, "text": "2) الخادم: تنفيذ + interceptors + صحة + reflection"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Catalog/Grpc/CatalogGrpcService.cs", "title": "unary + streaming + أخطاء بصيغتها الصحيحة", "code": r'''
using Grpc.Core;
using Shop.Contracts.Grpc.Catalog.V1;

namespace Shop.Catalog.Grpc;

/// <summary>
/// الخادم يرث من الـbase class المولّدة. ★ لا منطق عمل هنا — تنسيق فقط (الموديول/الـhandler بيقرر).
/// </summary>
public sealed class CatalogGrpcService(
    ICatalogModule catalog, IPublishPriceChanges priceFeed, ILogger<CatalogGrpcService> log)
    : Catalog.CatalogBase
{
    private const int MaxPageSize = 100;

    public override async Task<Product> GetProduct(GetProductRequest request, ServerCallContext context)
    {
        // ✓ الإلغاء/المهلة: context.CancellationToken مرتبطة بالـdeadline تلقائيًا
        context.CancellationToken.ThrowIfCancellationRequested();

        var id = request.IdentifierCase switch
        {
            GetProductRequest.IdentifierOneofCase.Sku =>
                await catalog.FindIdBySkuAsync(request.Sku, context.CancellationToken),
            GetProductRequest.IdentifierOneofCase.ProductId => Guid.Parse(request.ProductId),
            _ => throw new RpcException(new Status(StatusCode.InvalidArgument, "معرّف المنتج مطلوب (sku أو product_id)")),
        };

        if (id is null)
            throw new RpcException(new Status(StatusCode.NotFound, $"product not found"),
                                   CreateTrailers("PRODUCT_NOT_FOUND", request));

        var product = await catalog.GetAsync(id.Value, context.CancellationToken)
                      ?? throw new RpcException(new Status(StatusCode.NotFound, "product not found"));

        return product.ToProto();          // ✓ mapper في مكان واحد (Infrastructure) — لا تسريب Domain
    }

    public override async Task<GetProductsResponse> GetProducts(GetProductsRequest request, ServerCallContext context)
    {
        // ★ لا تثق بحدود العميل: افرض سقفًا
        var size = Math.Clamp(request.PageSize is 0 ? 20 : request.PageSize, 1, MaxPageSize);

        var page = await catalog.ListAsync(
            request.CategoryId is "" ? null : request.CategoryId,
            request.PageToken is "" ? null : request.PageToken, size, context.CancellationToken);

        var response = new GetProductsResponse { NextPageToken = page.NextCursor ?? string.Empty };
        response.Products.AddRange(page.Items.Select(ProductMapper.ToProto));
        return response;
    }

    /// <summary>Server streaming: دفعة تغييرات لحظية (بديل WebSocket داخليًا).</summary>
    public override async Task StreamPriceChanges(
        PriceWatchRequest request, IServerStreamWriter<PriceChange> responseStream, ServerCallContext context)
    {
        var max = request.MaxItems is 0 ? 1_000 : request.MaxItems;
        var sent = 0;

        await foreach (var change in priceFeed.WatchAsync(
                           request.CategoryId is "" ? null : request.CategoryId, context.CancellationToken))
        {
            // ✓ الكتابة على الـstream ليست thread-safe بالتوازي — هنا تسلسلية داخل الحلقة
            await responseStream.WriteAsync(change.ToProto(), context.CancellationToken);
            if (++sent >= max) break;                        // سقف صريح (لا بث لانهائي)
        }

        log.LogInformation("price stream ended after {Sent} items", sent);
    }

    /// <summary>Client streaming: رفع دفعات بلا N نداءات.</summary>
    public override async Task<ImportSummary> ImportProducts(
        IAsyncStreamReader<ProductImportItem> requestStream, ServerCallContext context)
    {
        var summary = new ImportSummary();

        while (await requestStream.MoveNext(context.CancellationToken))
        {
            var item = requestStream.Current;
            try
            {
                await catalog.ImportAsync(item.FromProto(), context.CancellationToken);
                summary.Accepted++;
            }
            catch (ArgumentException ex)
            {
                summary.Rejected++;
                summary.Errors.Add($"{item.Sku}: {ex.Message}");
                if (summary.Errors.Count >= 50) break;        // ✓ لا تجمع أخطاء للأبد
            }
        }

        return summary;
    }

    private static Trailers CreateTrailers(string code, object context) =>
        new() { { "error-code", code } };                     // ★ تفاصيل خطأ منظمة في الـtrailers
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Catalog/Program.cs", "title": "التسجيل: gRPC + interceptors + health + reflection", "code": r'''
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddGrpc(options =>
{
    options.MaxReceiveMessageSize = 4 * 1024 * 1024;      // ★ حدود صريحة (الافتراضي 4MB استقبال)
    options.MaxSendMessageSize = 8 * 1024 * 1024;
    options.EnableDetailedErrors = builder.Environment.IsDevelopment();   // ✓ تفاصيل في الإنتاج = تسريب
    options.Interceptors.Add<ExceptionInterceptor>();     // تحويل استثناءات المجال → Status صحيح
    options.Interceptors.Add<LoggingInterceptor>();
    options.Interceptors.Add<MetricsInterceptor>();
});

builder.Services.AddGrpcHealthChecks()                  // فحص صحة gRPC (للـload balancer)
    .AddCheck("self", () => HealthCheckResult.Healthy());
builder.Services.AddGrpcReflection();                   // لـgrpcurl في التطوير

builder.Services.AddCatalogModule(builder.Configuration);

var app = builder.Build();

app.MapGrpcService<CatalogGrpcService>();
app.MapGrpcHealthChecksService();
if (app.Environment.IsDevelopment()) app.MapGrpcReflectionService();

// ★ لو الخدمة بتستقبل HTTP/JSON كمان: حدد البروتوكولات لكل endpoint
app.MapGet("/", () => "catalog gRPC service").RequireHost("*:5080");

app.Run();
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Catalog/Grpc/Interceptors.cs", "title": "3 interceptors: استثناءات، logging، مقاييس", "code": r'''
using Grpc.Core;
using Grpc.Core.Interceptors;

/// <summary>★ أهم interceptor: يحوّل استثناءات المجال لـStatusCode دلالي (بلا 500/Unknown لكل حاجة).</summary>
public sealed class ExceptionInterceptor(ILogger<ExceptionInterceptor> log) : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request, ServerCallContext context, UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try { return await continuation(request, context); }
        catch (RpcException) { throw; }                       // بالفعل gRPC — مرّرها
        catch (OperationCanceledException) when (context.CancellationToken.IsCancellationRequested)
        {
            throw new RpcException(new Status(StatusCode.Cancelled, "cancelled by client/deadline"));
        }
        catch (NotFoundException ex)
        {
            throw new RpcException(new Status(StatusCode.NotFound, ex.Message));
        }
        catch (ValidationException ex)
        {
            var trailers = new Trailers { { "error-code", "VALIDATION_FAILED" } };
            foreach (var (field, error) in ex.Errors.Take(10)) trailers.Add($"field-{field}", error);
            throw new RpcException(new Status(StatusCode.InvalidArgument, "validation failed"), trailers);
        }
        catch (ConflictException ex)
        {
            throw new RpcException(new Status(StatusCode.FailedPrecondition, ex.Message));
        }
        catch (Exception ex)
        {
            log.LogError(ex, "unhandled error in {Method}", context.Method);
            // ✓ لا تسرّب التفاصيل في الإنتاج
            throw new RpcException(new Status(StatusCode.Internal, "internal error"));
        }
    }
}

/// <summary>Logging مع correlation id القادم من الـmetadata (درس 2.1.7).</summary>
public sealed class LoggingInterceptor(ILogger<LoggingInterceptor> log) : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request, ServerCallContext context, UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var correlation = context.RequestHeaders.GetValue("x-correlation-id") ?? Guid.NewGuid().ToString("N");

        using (log.BeginScope(new Dictionary<string, object>
               { ["correlation_id"] = correlation, ["method"] = context.Method }))
        {
            var sw = Stopwatch.StartNew();
            try
            {
                var response = await continuation(request, context);
                log.LogInformation("grpc ok {Method} {Elapsed}ms", context.Method, sw.ElapsedMilliseconds);
                return response;
            }
            catch (RpcException ex)
            {
                log.LogWarning("grpc {Status} {Method} {Elapsed}ms", ex.StatusCode, context.Method, sw.ElapsedMilliseconds);
                throw;
            }
        }
    }
}

/// <summary>مقاييس لكل method/status — أساس لوحات gRPC.</summary>
public sealed class MetricsInterceptor : Interceptor
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Catalog.grpc", "1.0.0");
    private static readonly Histogram<double> Duration =
        Meter.CreateHistogram<double>("grpc.server.duration", unit: "ms");
    private static readonly Counter<long> Calls = Meter.CreateCounter<long>("grpc.server.calls");

    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request, ServerCallContext context, UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var sw = Stopwatch.StartNew();
        var status = "ok";
        try { return await continuation(request, context); }
        catch (RpcException ex) { status = ex.StatusCode.ToString(); throw; }
        finally
        {
            var tags = new KeyValuePair<string, object?>[]
            {
                new("method", context.Method), new("status", status),
            };
            Duration.Record(sw.Elapsed.TotalMilliseconds, tags);
            Calls.Add(1, tags);
        }
    }
}
'''},
            {"type": "heading", "level": 2, "text": "3) العميل: channel واحد + deadline + resilience"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/CatalogGrpcClient.cs", "title": "التسجيل الصحيح والاستخدام", "code": r'''
using Grpc.Net.Client;
using Shop.Contracts.Grpc.Catalog.V1;

// ═══ التسجيل: channel مُدار عبر HttpClientFactory (singleton فعليًا) ═══
public static class CatalogClientRegistration
{
    public static IServiceCollection AddCatalogGrpcClient(this IServiceCollection services, IConfiguration config)
    {
        var address = config["Services:Catalog:Address"]
                      ?? throw new InvalidOperationException("Services:Catalog:Address مطلوب");

        services.AddGrpcClient<Catalog.CatalogClient>(options =>
        {
            options.Address = new Uri(address);

            // ✗ لا تحدد deadline هنا: القيمة تُحسب مرة واحدة وقت التسجيل!
            //   الـdeadline لازم يُضرب لكل نداء (شوف الغلاف أسفل: deadline: DateTime.UtcNow.AddSeconds(2))
        })
        .ConfigurePrimaryHttpMessageHandler(() => new SocketsHttpHandler
        {
            // ★ الأهم للأداء: اتصال HTTP/2 واحد مُعاد استخدامه (multiplexing)
            PooledConnectionLifetime = TimeSpan.FromMinutes(10),     // يدور الاتصال (لتغيير DNS)
            PooledConnectionIdleTimeout = TimeSpan.FromMinutes(2),
            EnableMultipleHttp2Connections = true,                   // ✓ يتجاوز حد التدفقات المتزامنة
            MaxConnectionsPerServer = 4,
        })
        // ✓ resilience قياسي: retry + circuit breaker + timeout (درس 5.2.4)
        .AddStandardResilienceHandler(options =>
        {
            options.Retry.MaxRetryAttempts = 2;
            options.Retry.UseJitter = true;
            options.Retry.Delay = TimeSpan.FromMilliseconds(200);
            options.CircuitBreaker.FailureRatio = 0.5;
            options.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(5);   // ★ يشمل كل المحاولات
        })
        // ✓ propagation تلقائي للـactivity/trace context (OpenTelemetry)
        .AddCallInvocationsLogger();

        return services;
    }
}

/// <summary>غلاف: يترجم بين نموذجنا وعقد الـproto (ACL — درس 5.1.2).</summary>
public sealed class CatalogGrpcClient(Catalog.CatalogClient client, ILogger<CatalogGrpcClient> log)
    : ICatalogGateway
{
    public async Task<IReadOnlyList<CatalogItemRef>> GetItemsAsync(
        IReadOnlyList<Guid> productIds, CancellationToken ct)
    {
        var request = new GetProductsRequest();
        request.ProductIds.AddRange(productIds.Distinct().Select(id => id.ToString()));
        request.PageSize = Math.Clamp(productIds.Count, 1, 100);

        try
        {
            // ✓ deadline + cancellation من النداء (يتجاوز الافتراضي لو محتاج)
            var response = await client.GetProductsAsync(request,
                deadline: DateTime.UtcNow.AddSeconds(2), cancellationToken: ct);

            return response.Products.Select(p => new CatalogItemRef(
                ProductId: Guid.Parse(p.ProductId),
                DisplayName: p.Title,
                UnitPrice: p.Price.ToMoney(),                     // minor units → Money (VO من 4.2.1)
                AvailableStock: p.AvailableStock,
                IsSellable: p.Status == ProductStatus.Active && p.AvailableStock > 0)).ToList();
        }
        catch (RpcException ex) when (ex.StatusCode is StatusCode.NotFound)
        {
            return [];                                            // ✓ حالة متوقعة → نتيجة فارغة
        }
        catch (RpcException ex) when (ex.StatusCode is StatusCode.Unavailable or StatusCode.DeadlineExceeded)
        {
            log.LogWarning(ex, "catalog gRPC unavailable ({Status})", ex.StatusCode);
            throw new DependencyUnavailableException("catalog");  // → 503 (لا بيانات خاطئة صامتة)
        }
        catch (RpcException ex) when (ex.StatusCode == StatusCode.InvalidArgument)
        {
            // ✓ تفاصيل التحقق في الـtrailers
            var fields = ex.Trailers.Where(t => t.Key.StartsWith("field-")).Select(t => t.Value).ToList();
            throw new ValidationException(fields);
        }
    }
}

/// <summary>تحويل أنواع proto ↔ أنواع المجال في مكان واحد.</summary>
public static class GrpcMoneyExtensions
{
    public static Money ToMoney(this Shop.Contracts.Grpc.Common.Money m)
    {
        var divisor = (decimal)Math.Pow(10, m.Exponent == 0 ? 2 : m.Exponent);
        return new Money(m.MinorUnits / divisor, m.CurrencyCode);
    }

    public static Shop.Contracts.Grpc.Common.Money ToProto(this Money m) => new()
    {
        MinorUnits = (long)Math.Round(m.Amount * 100m, MidpointRounding.AwayFromZero),
        CurrencyCode = m.Currency,
        Exponent = 2,
    };
}
'''},
            {"type": "heading", "level": 2, "text": "4) gRPC مقابل REST داخليًا"},
            {"type": "table", "head": ["المعيار", "gRPC", "REST/JSON", "الحكم"], "rows": [
                ["حجم الحمولة", "ثنائي (أصغر 3-10×)", "نص (أكبر)", "gRPC للمحمولات الكبيرة/النداءات الكثيرة"],
                ["زمن التسلسل", "أقل بوضوح", "أعلى (خاصة مع reflection)", "gRPC"],
                ["العقد", "مولّد من .proto — خطأ ترجمة عند الاختلاف", "OpenAPI + مولّدات (اختياري)", "gRPC أقوى"],
                ["النقل", "HTTP/2 multiplexing + streaming أصيل", "HTTP/1.1 غالبًا (بلا streaming سهل)", "gRPC"],
                ["المتصفحات", "يحتاج gRPC-Web/بروكسي", "✓ مباشر", "REST"],
                ["القابلية للتصحيح", "يحتاج grpcurl/reflection", "✓ curl/متصفح", "REST"],
                ["شركاء خارجيون", "نادر الدعم", "✓ المعيار الفعلي", "REST"],
                ["المهلة/الإلغاء", "deadline مدمج وعابر للخدمات", "يدوي (CancellationToken + timeout)", "gRPC"],
                ["دعم .NET", "ممتاز (Grpc.AspNetCore)", "ممتاز", "تعادل"],
                ["**الخلاصة**", "**داخلي بين خدماتك**", "**خارجي (متصفحات/شركاء)**", "الاتنين معًا في نظام واحد"],
            ]},
            {"type": "callout", "kind": "danger", "title": "أخطاء بتخلي gRPC أبطأ من REST",
             "md": """
- **إنشاء `GrpcChannel` لكل نداء** → تفاوض TLS/اتصال جديد كل مرة (كارثة). القناة **singleton**.
- **نداء في حلقة** (N منتجات = N نداء) → استخدم `repeated` (دفعات) أو streaming. نفس خطأ N+1.
- **بلا deadline** → نداء متعلّق بيشغل خيط/اتصال لحد ما ينفد الـpool.
- **رسائل ضخمة** (> 4MB) → تجاوز الحد أو ضغط الذاكرة؛ استخدم streaming للتصدير.
- **تجاهل `StatusCode.Unavailable`** وإعادة المحاولة بلا jitter → عاصفة إعادة محاولة تسقط الخدمة المستهدفة.
- **HTTP/1.1 proxy في المنتصف** (بعض ingress/موزّعات) → يكسر gRPC. تأكد من `HttpProtocols.Http2`.
- **منطق عمل في الـservice** → طبقة gRPC تسليم فقط (زي الـendpoints).
- **`EnableDetailedErrors = true` في الإنتاج** → تسريب تفاصيل داخلية للعميل.
- **إعادة محاولة نداء غير idempotent** (خصم مبلغ) بلا مفتاح idempotency → أثر مضاعف.
"""},
            {"type": "heading", "level": 2, "text": "5) الاختبار"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Catalog.Tests/Grpc/CatalogGrpcTests.cs", "title": "وحدة (الخادم مباشرة) + تكامل (قناة حقيقية)", "code": r'''
// ═══ ① اختبار وحدة: نداء الخادم مباشرة (بلا شبكة) ═══
public class CatalogGrpcUnitTests
{
    private static ServerCallContext Ctx(CancellationToken ct = default) =>
        new TestServerCallContext(ct);                    // تنفيذ بسيط لـServerCallContext (شائع في الاختبارات)

    [Fact]
    public async Task GetProduct_missing_identifier_throws_InvalidArgument()
    {
        var service = new CatalogGrpcService(Substitute.For<ICatalogModule>(),
                                             Substitute.For<IPublishPriceChanges>(), NullLogger);

        var act = async () => await service.GetProduct(new GetProductRequest(), Ctx());

        var ex = await act.Should().ThrowAsync<RpcException>();
        ex.Which.StatusCode.Should().Be(StatusCode.InvalidArgument);
    }

    [Fact]
    public async Task GetProduct_not_found_maps_to_NotFound_status()
    {
        var catalog = Substitute.For<ICatalogModule>();
        catalog.FindIdBySkuAsync("NOPE", Arg.Any<CancellationToken>()).Returns((Guid?)null);
        var service = new CatalogGrpcService(catalog, Substitute.For<IPublishPriceChanges>(), NullLogger);

        var act = async () => await service.GetProduct(
            new GetProductRequest { Sku = "NOPE" }, Ctx());

        (await act.Should().ThrowAsync<RpcException>()).Which.StatusCode.Should().Be(StatusCode.NotFound);
    }
}

// ═══ ② اختبار تكامل: خادم حقيقي + قناة حقيقية (WebApplicationFactory) ═══
public class CatalogGrpcIntegrationTests(CatalogWebFactory factory) : IClassFixture<CatalogWebFactory>
{
    [Fact]
    public async Task GetProduct_returns_product_over_real_grpc_channel()
    {
        await factory.SeedProductAsync(sku: "KB-1", title: "Keyboard", priceMinor: 25050);

        // ★ القناة لازم تستخدم نفس HttpClient (بشهادته/اتصاله) — مش عنوان خارجي
        var channel = GrpcChannel.ForAddress(factory.Server!.BaseAddress, new GrpcChannelOptions
        {
            HttpClient = factory.CreateClient(),
        });
        var client = new Catalog.CatalogClient(channel);

        var product = await client.GetProductAsync(new GetProductRequest { Sku = "KB-1" });

        product.Title.Should().Be("Keyboard");
        product.Price.MinorUnits.Should().Be(25050);
        product.Price.CurrencyCode.Should().Be("EGP");
    }

    [Fact]
    public async Task Deadline_exceeded_is_surfaced_as_DeadlineExceeded()
    {
        var channel = GrpcChannel.ForAddress(factory.Server!.BaseAddress,
            new GrpcChannelOptions { HttpClient = factory.CreateClient() });
        var client = new Catalog.CatalogClient(channel);

        var act = async () => await client.GetProductAsync(new GetProductRequest { Sku = "SLOW" },
            deadline: DateTime.UtcNow.AddMilliseconds(50));      // ✓ مهلة ضيقة مقصودة

        (await act.Should().ThrowAsync<RpcException>()).Which.StatusCode
            .Should().BeOneOf(StatusCode.DeadlineExceeded, StatusCode.NotFound);
    }

    [Fact]
    public async Task Server_streaming_returns_bounded_items()
    {
        var channel = GrpcChannel.ForAddress(factory.Server!.BaseAddress,
            new GrpcChannelOptions { HttpClient = factory.CreateClient() });
        var client = new Catalog.CatalogClient(channel);

        using var call = client.StreamPriceChanges(new PriceWatchRequest { MaxItems = 3 });
        var received = new List<PriceChange>();
        while (await call.ResponseStream.MoveNext(CancellationToken.None)) received.Add(call.ResponseStream.Current);

        received.Count.Should().BeLessThanOrEqualTo(3);
    }
}

/// <summary>خادم اختباري حقيقي (بلا Kestrel خارجي) — نفس نمط REST لكن بـAllowSynchronousIO بلا حاجة.</summary>
public class CatalogWebFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder) =>
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<ICatalogModule>();
            services.AddSingleton<ICatalogModule, FakeCatalogModule>();   // أو Postgres عبر Testcontainers
        });
}
'''},
            {"type": "checkpoints", "items": [
                "أستخدم gRPC للاتصال الداخلي وREST/OpenAPI للخارجي، وأعرف سبب كل اختيار.",
                "أصمم عقود proto قابلة للتطور (أرقام محفوظة، `UNSPECIFIED` للصفر، minor units للمال، `oneof` للبدائل).",
                "أبني خادمًا بـinterceptors (استثناءات→Status، logging، مقاييس) وحدود رسائل وصحة وreflection في التطوير.",
                "أبني عميلًا بقناة مُدارة (singleton) وdeadline وresilience وACL، وأتعامل مع كل StatusCode بشكل صريح.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه أرقام الحقول في proto أهم من الأسماء؟",
                 "options": [
                     "للترتيب الأبجدي",
                     "الترميز الثنائي يعتمد على الرقم فقط — تغيير الرقم يكسر التوافق بصمت، بينما تغيير الاسم آمن ثنائيًا",
                     "للأداء",
                     "مطلب grpcurl",
                 ], "answer": 1,
                 "explain": "عشان كده القاعدة: احجز الأرقام المحذوفة (`reserved 11; reserved \"old_price\";`) ولا تعِد استخدامها أبدًا."},
                {"q": "قيمة الصفر في enum لازم تكون…",
                 "options": [
                     "أول قيمة حقيقية",
                     "`*_UNSPECIFIED` — لأن القيمة الافتراضية لأي حقل في proto3 هي الصفر، فلو كانت قيمة حقيقية هتتفسر غلط",
                     "محذوفة",
                     "`UNKNOWN_ERROR`",
                 ], "answer": 1,
                 "explain": "بلا `UNSPECIFIED`: عميل ما بعتش الحقل خالص هيظهر كأنه بعت القيمة الأولى الحقيقية — خطأ صامت شائع."},
                {"q": "إزاي تخزن المال في proto؟",
                 "options": [
                     "double",
                     "float",
                     "minor units (int64) + رمز العملة + exponent",
                     "string فقط",
                 ], "answer": 2,
                 "explain": "`float`/`double` لهما أخطاء تقريب — مرفوضان للمال. `string` مقبول لكن أقل كفاءة وأضعف تحققًا."},
                {"q": "إنشاء `GrpcChannel` داخل كل handler — النتيجة؟",
                 "options": [
                     "أفضل عزلًا",
                     "كارثة أداء: تفاوض TLS/اتصال جديد لكل نداء واستنزاف منافذ؛ القناة يجب أن تكون singleton (عبر HttpClientFactory)",
                     "بلا أثر",
                     "أكثر أمانًا",
                 ], "answer": 1,
                 "explain": "الـclient رخيص ويُنشأ لكل نداء؛ الـchannel هو الاتصال ويُشارك. `AddGrpcClient` بيدير ده صح."},
                {"q": "خدمة gRPC رجعت `StatusCode.Unavailable`. أحسن تصرف في العميل؟",
                 "options": [
                     "أعد المحاولة فورًا وبلا حد",
                     "إعادة محاولة محدودة بـbackoff وjitter (لنداء idempotent) + circuit breaker، وإلا فشل صريح 503",
                     "تجاهل الخطأ",
                     "أعد تشغيل الخدمة",
                 ], "answer": 1,
                 "explain": "إعادة المحاولة بلا حدود وjitter بتعمل «عاصفة» تسقط الخدمة المستهدفة أكتر. `AddStandardResilienceHandler` بيعمل ده جاهزًا."},
                {"q": "متى تختار REST بدل gRPC؟",
                 "options": [
                     "دائمًا",
                     "للواجهات العامة/المتصفحات، تكاملات شركاء خارجيين، والمسارات اللي محتاجة تصحيح سهل (curl) — gRPC يبقى داخليًا",
                     "لما البيانات كبيرة",
                     "لما فيه streaming",
                 ], "answer": 1,
                 "explain": "النمط الشائع: BFF/gateway بيقدّم REST/OpenAPI للخارج، وبينادي الخدمات داخليًا بـgRPC."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "خدمة gRPC داخلية بعقد مشترك",
                 "md": "ابنِ مشروع عقود (`.proto`) + خدمة gRPC لموديول (Catalog) + عميل في موديول تاني (Orders) عبر ACL. شغّلها محليًا واختبر unary وحالة خطأ واحدة على الأقل.",
                 "criteria": [
                     "مشروع `Contracts.Grpc` مستقل بلا تنفيذ، والكود مولّد من `.proto` وقت البناء",
                     "proto3 بقواعد صحيحة: `UNSPECIFIED` للصفر، `reserved` بلا أرقام محذوفة، Money بـminor units",
                     "خادم بـ3 interceptors (استثناءات→Status، logging بـcorrelation id، مقاييس)",
                     "عميل بقناة مُدارة عبر `AddGrpcClient` + deadline + resilience",
                     "تعامل صريح مع ≥ 4 حالات Status (OK/NotFound/InvalidArgument/Unavailable)",
                     "اختبار وحدة (الخادم مباشرة) + اختبار تكامل (قناة حقيقية عبر WebApplicationFactory)",
                     "grpcurl يعمل ضد الخدمة في التطوير (reflection مفعّل في Development فقط)",
                 ],
                 "hint": "لو `WebApplicationFactory` مع gRPC بيرفض: تأكد إن القناة مبنية على `factory.CreateClient()` و`factory.Server.BaseAddress` (مش عنوان خارجي)، وإن Kestrel مضبوط على HTTP/2 للاختبار."},
                {"id": "t2", "title": "streaming + قياس مقارنة",
                 "md": "أضف RPC واحد بـserver streaming (تصدير/تقدُّم/تغييرات أسعار) واستخدمه في عميل. ثم قِس الفرق بين مسار gRPC ومسار REST مكافئ لنفس العملية (حجم الحمولة والزمن) بـBenchmarkDotNet أو k6.",
                 "criteria": [
                     "streaming بسقف صريح (`max_items`) وإلغاء عبر CancellationToken (اختبار)",
                     "العميل يقرأ الـstream بشكل تسلسلي ويتعامل مع الإلغاء/الانقطاع",
                     "جدول مقارنة: حجم الحمولة والزمن p50/p95 لـgRPC مقابل JSON لنفس العملية",
                     "استنتاج مكتوب: هل الفرق يبرر التعقيد في حالتك؟",
                     "ملاحظة عن حدود الرسائل (MaxReceive/Send) وليه اخترت القيم دي",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "gRPC for .NET", "url": "https://learn.microsoft.com/aspnet/core/grpc/"},
                {"label": "Protocol Buffers — Language guide (proto3)", "url": "https://protobuf.dev/programming-guides/proto3/"},
                {"label": "Proto best practices (versioning)", "url": "https://protobuf.dev/programming-guides/dos-donts/"},
                {"label": "gRPC — Deadlines & cancellation", "url": "https://learn.microsoft.com/aspnet/core/grpc/deadlines"},
                {"label": "Grpc.Net.ClientFactory", "url": "https://learn.microsoft.com/aspnet/core/grpc/clientfactory"},
                {"label": "grpcurl", "url": "https://github.com/fullstorydev/grpcurl"},
                {"label": "gRPC-Web", "url": "https://github.com/grpc/grpc-web"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s5-m1-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لما الخدمات بتزيد، العميل ما ينفعش يعرف 7 عناوين، ولا يعمل 5 نداءات لتركيب صفحة واحدة،
ولا يتعامل مع TLS ومصادقة ومهل لكل خدمة. هنا بييجي دور **API Gateway**: نقطة دخول واحدة
بتوجّه، بتجمّع، بتطبّق سياسات (auth، rate limiting، timeouts، retries)، وبتقيس كل حاجة.

في .NET الاختيار الطبيعي هو **YARP (Yarp Reverse Proxy)**: مكتبة من مايكروسوفت، قابلة للتخصيص بالكامل،
بتشتغل كـmiddleware داخل ASP.NET Core (مش عملية منفصلة)، وبتدعم HTTP/2 وgRPC وWebSocket.

الدرس ده: إعداد مسارات ومجموعات (routes/clusters) من الإعدادات أو الكود، تحويلات (transforms)،
تجميع (aggregation) مع فشل جزئي، سياسات أمان ومرونة، canary، ومراقبة — وليه الـgateway
**ماينفعش يبقى مكان منطق العمل**.
"""},
            {"type": "terms", "items": [
                {"term": "Reverse Proxy", "def": "وسيط يستقبل طلبات العملاء ويوجّهها لخدمات داخلية — العميل يعرف الـgateway فقط."},
                {"term": "Cluster (YARP)", "def": "مجموعة وجهات (destinations) لخدمة واحدة + سياساتها (توزيع حمل، صحة، affinity، HTTP client)."},
                {"term": "Route (YARP)", "def": "قاعدة مطابقة (path/host/method/header) → cluster + تحويلات + سياسات."},
                {"term": "Transform", "def": "تعديل الطلب/الاستجابة أثناء العبور: إضافة/حذف headers، تغيير path، إعادة كتابة host."},
                {"term": "Load Balancing Policy", "def": "كيف تُختار الوجهة: `FirstAlphabetical`, `Random`, `RoundRobin`, `LeastRequests`, `PowerOfTwoChoices`."},
                {"term": "Active/Passive Health", "def": "فحص دوري للوجهات (active) مقابل استنتاج الصحة من أكواد الاستجابة (passive) → إبعاد الوجهات المريضة."},
                {"term": "Session Affinity", "def": "تثبيت العميل على وجهة محددة (مطلوب لبعض الحالات؛ يقلل مرونة التوسع)."},
                {"term": "API Composition", "def": "جمع نتائج عدة خدمات في استجابة واحدة — في الـgateway أو في BFF."},
                {"term": "BFF (Backend for Frontend)", "def": "gateway مخصص لواجهة واحدة (ويب/موبايل) — شكله من احتياجات الواجهة."},
                {"term": "Canary / Blue-Green", "def": "توجيه نسبة صغيرة (أو بحسب header) لإصدار جديد، مع إمكانية الرجوع الفوري."},
                {"term": "Edge concerns", "def": "ما يخص الحافة: TLS، رؤوس موجهة (Forwarded)، rate limiting، إخفاء داخلي، CORS."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الإعداد: من appsettings (الأسرع)"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم والمشروع", "code": r'''
dotnet new web -n Shop.Gateway -o src/Services/Shop.Gateway
cd src/Services/Shop.Gateway
dotnet add package Yarp.ReverseProxy
dotnet add package Microsoft.Extensions.Http.Resilience
dotnet add package Serilog.AspNetCore
dotnet add package Microsoft.Extensions.ServiceDiscovery.Yarp   # خدمة discovery (Aspire، درس 5.3.1)
'''},
            {"type": "code", "lang": "json", "filename": "src/Services/Shop.Gateway/appsettings.json", "title": "مسارات ومجموعات: config-driven", "code": r'''
{
  "ReverseProxy": {
    "Routes": {
      "catalog-route": {
        "ClusterId": "catalog",
        "Match": { "Path": "/api/catalog/{**catch-all}", "Methods": [ "GET", "POST", "PUT", "PATCH", "DELETE" ] },
        "Transforms": [
          { "PathRemovePrefix": "/api/catalog" },
          { "PathPrefix": "/catalog" },
          { "RequestHeader": "X-Forwarded-Prefix", "Set": "/api/catalog" },
          { "ResponseHeader": "X-Frame-Options", "Append": "DENY" }
        ],
        "Metadata": { "TimeoutMs": "5000" },
        "AuthorizationPolicy": "AuthenticatedUsers",
        "RateLimiterPolicy": "api-default",
        "CorsPolicy": "web-app"
      },

      "orders-route": {
        "ClusterId": "orders",
        "Match": { "Path": "/api/orders/{**catch-all}" },
        "Transforms": [ { "PathRemovePrefix": "/api" } ],
        "AuthorizationPolicy": "AuthenticatedUsers",
        "RateLimiterPolicy": "api-default"
      },

      "orders-canary": {
        "ClusterId": "orders-v2",
        "Match": {
          "Path": "/api/orders/{**catch-all}",
          "Headers": [ { "Name": "X-Canary", "Values": [ "v2" ], "Mode": "ExactHeader" } ]
        },
        "Order": -1,
        "Transforms": [ { "PathRemovePrefix": "/api" } ]
      },

      "health-route": {
        "ClusterId": "orders",
        "Match": { "Path": "/internal/orders/health" },
        "AuthorizationPolicy": "Anonymous",
        "RateLimiterPolicy": "internal"
      }
    },

    "Clusters": {
      "catalog": {
        "LoadBalancingPolicy": "LeastRequests",
        "Destinations": {
          "c1": { "Address": "http://catalog-1:5080/" },
          "c2": { "Address": "http://catalog-2:5080/" }
        },
        "HealthCheck": {
          "Active": {
            "Enabled": "true",
            "Interval": "00:00:10",
            "Timeout": "00:00:02",
            "Policy": "ConsecutiveFailures",
            "Path": "/health/live"
          },
          "Passive": {
            "Enabled": "true",
            "Policy": "TransportFailureRate",
            "ReactivationPeriod": "00:00:30"
          }
        },
        "HttpClient": {
          "DangerousAcceptAnyServerCertificate": "false",
          "MaxConnectionsPerServer": 100,
          "RequestTimeout": "00:00:05"
        },
        "Metadata": { "ServiceVersion": "1.4.2" }
      },

      "orders": {
        "LoadBalancingPolicy": "PowerOfTwoChoices",
        "Destinations": { "o1": { "Address": "http://orders:5081/" } },
        "SessionAffinity": { "Enabled": "false" }
      },

      "orders-v2": {
        "LoadBalancingPolicy": "RoundRobin",
        "Destinations": { "o2": { "Address": "http://orders-v2:5081/" } }
      },

      "catalog-grpc": {
        "Destinations": { "g1": { "Address": "http://catalog-1:5081/" } },
        "HttpClient": { "Http2Only": "true" }
      }
    }
  }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Shop.Gateway/Program.cs", "title": "التركيب: YARP + سياسات الحافة", "code": r'''
var builder = WebApplication.CreateBuilder(args);

// ═══ ① YARP ═══
builder.Services.AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"))
    .AddServiceDiscoveryDestinationResolver()          // ✓ يحل أسماء الخدمات (Aspire/K8s) بدل عناوين ثابتة
    .AddTransforms<CorrelationHeaderTransform>()       // تحويلات مخصصة (ITransformProvider)
    // ✓ retries/circuit breaker لكل cluster — تحقق من توفر الامتداد في إصدارك:
    //   البديل: .ConfigureHttpClient(c => c.AddStandardResilienceHandler()) لكل cluster
    .AddHttpClientResilience();

// ═══ ② سياسات الحافة (تُطبق على المسارات بالاسم) ═══
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AuthenticatedUsers", p => p.RequireAuthenticatedUser());
    options.AddPolicy("InternalOnly", p => p.RequireClaim("scope", "internal.ops"));
});

builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddPolicy("api-default", http => RateLimitPartition.GetSlidingWindowLimiter(
        partitionKey: http.User.Identity?.Name ?? http.Connection.RemoteIpAddress?.ToString() ?? "anon",
        factory: _ => new SlidingWindowRateLimiterOptions
        {
            PermitLimit = 120, Window = TimeSpan.FromMinutes(1), SegmentsPerWindow = 6,
            QueueProcessingOrder = QueueProcessingOrder.OldestFirst, QueueLimit = 0,
        }));
    options.AddFixedWindowLimiter("internal", o => { o.PermitLimit = 30; o.Window = TimeSpan.FromSeconds(10); });
});

builder.Services.AddCors(o => o.AddPolicy("web-app", p => p
    .WithOrigins(builder.Configuration.GetSection("Cors:Origins").Get<string[]>() ?? [])
    .AllowAnyHeader().AllowAnyMethod().AllowCredentials()));

// ✓ المصادقة عند الحافة **و** في كل خدمة (دفاع بالعمق — درس 2.2.x)
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o =>
    {
        o.Authority = builder.Configuration["Auth:Authority"];
        o.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateAudience = true, ValidAudience = "shop.api",
            ValidateIssuer = true, ClockSkew = TimeSpan.FromSeconds(30),
            ValidAlgorithms = [SecurityAlgorithms.RsaSha256],
        };
    });

builder.Services.AddOutputCache();
builder.Services.AddHealthChecks();
builder.Services.AddOpenTelemetry().WithTracing(t => t
    .AddAspNetCoreInstrumentation().AddHttpClientInstrumentation()
    .AddSource("Yarp.ReverseProxy.Forwarder")             // ★ تتبع عبور الـgateway (تحقق من اسم المصدر في إصدارك)
    .AddOtlpExporter());

var app = builder.Build();

// ═══ ③ ترتيب الـmiddleware (الحافة أولًا) ═══
app.UseExceptionHandler("/error");
app.UseForwardedHeaders(new ForwardedHeadersOptions     // ★ قبل كل شيء (وإلا IP/البروتوكول غلط)
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto,
    KnownProxies = { IPAddress.Parse(app.Configuration["Gateway:KnownProxy"] ?? "10.0.0.1") },
});
app.UseSerilogRequestLogging(o => o.EnrichDiagnosticContext = (ctx, http) =>
{
    ctx.SetProperty("RemoteIp", http.Connection.RemoteIpAddress?.ToString());
    ctx.SetProperty("Cluster", http.Items.TryGetValue("ClusterId", out var c) ? c : null);
});
app.UseHsts();
app.UseHttpsRedirection();
app.UseSecurityHeaders();                                 // درس 2.2.3
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.UseRateLimiter();
app.UseOutputCache();

// ═══ ④ المسارات ═══
app.MapHealthChecks("/gateway/health");
app.MapGet("/gateway/clusters", (IProxyStateLookup proxy) =>       // ✓ شفافية تشغيلية
    proxy.GetClusters().Select(c => new
    {
        c.ClusterId,
        c.Model.Config.LoadBalancingPolicy,
        Destinations = c.Destinations.Select(d => new { d.DestinationId, d.Model.Address, Healthy = d.Model.Health.Active }),
    })).RequireAuthorization("InternalOnly");

app.MapPost("/error", (HttpContext ctx) => Results.Problem(       // استجابة موحدة للأخطاء
    statusCode: 500, title: "GatewayError",
    extensions: new Dictionary<string, object?> { ["traceId"] = ctx.TraceIdentifier }));

app.MapReverseProxy(proxyPipeline =>                       // ★ pipeline خاص بالبروكسي
    proxyPipeline.Use(async (ctx, next) =>
    {
        ctx.Response.Headers["X-Gateway"] = "shop-gateway";
        await next();
    }));

app.Run();

/// <summary>
/// تحويل مطبّق على **كل** المسارات: يمرر correlation id مولّدًا ويحذف رؤوسًا داخلية حساسة.
/// (`ITransformProvider` هو الـAPI الذي يقبله `AddTransforms&lt;T&gt;()`.)
/// </summary>
public sealed class CorrelationHeaderTransform : ITransformProvider
{
    public void ValidateRoute(TransformRouteValidationContext context) { }
    public void ValidateCluster(TransformClusterValidationContext context) { }

    public void Apply(TransformBuilderContext context)
    {
        context.AddRequestTransform(transformContext =>
        {
            var correlation = transformContext.HttpContext.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                              ?? Activity.Current?.TraceId.ToString() ?? Guid.NewGuid().ToString("N");

            transformContext.ProxyRequest.Headers.Remove("X-Correlation-Id");   // ✓ لا تثق برأس العميل أعمى
            transformContext.ProxyRequest.Headers.TryAddWithoutValidation("X-Correlation-Id", correlation);

            // ★ احذف رؤوس داخلية حساسة لو العميل حاول حقنها
            foreach (var header in new[] { "X-Internal-Token", "X-Forwarded-Host" })
                transformContext.ProxyRequest.Headers.Remove(header);

            transformContext.HttpContext.Response.Headers["X-Correlation-Id"] = correlation;
            return ValueTask.CompletedTask;
        });
    }
}
'''},
            {"type": "heading", "level": 2, "text": "2) التجميع (API Composition) مع فشل جزئي"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Shop.Gateway/Composition/OrderDetailsAggregator.cs", "title": "نداءات متوازية + مهلة لكل واحد + تدهور مقصود", "code": r'''
/// <summary>
/// BFF-style composition: صفحة تفاصيل الطلب تحتاج (طلب + شحن + دفع + إشعارات).
/// ★ القواعد: توازي، مهلة لكل نداء، فشل جزئي مُعلن (لا فشل كامل)، ولا منطق عمل هنا.
/// </summary>
public sealed class OrderDetailsAggregator(
    OrdersClient orders, ShippingClient shipping, PaymentsClient payments,
    ILogger<OrderDetailsAggregator> log, TimeProvider time)
{
    private static readonly TimeSpan SectionTimeout = TimeSpan.FromSeconds(2);
    private static readonly System.Diagnostics.ActivitySource Source = new("Shop.Gateway.Aggregation");

    public async Task<IResult> GetAsync(Guid orderId, string? accessToken, CancellationToken ct)
    {
        using var scope = Source.StartActivity("aggregate.order_details");
        scope?.SetTag("order.id", orderId);

        // ① النداء الأساسي: لو فشل → فشل كامل (بلا تفاصيل الطلب مفيش صفحة)
        var order = await TryAsync("orders", ct,
            () => orders.GetAsync(orderId, accessToken, ct), required: true);
        if (order is null) return Results.NotFound(new { orderId });

        // ② الأقسام الثانوية بالتوازي — الفشل يُعلن كقسم ناقص (partial)
        var shipmentTask = TryAsync("shipping", ct, () => shipping.GetAsync(orderId, accessToken, ct), required: false);
        var paymentTask  = TryAsync("payments", ct, () => payments.GetAsync(orderId, accessToken, ct), required: false);
        await Task.WhenAll(shipmentTask, paymentTask);

        var shipment = shipmentTask.Result;      // ✓ آمنة: اكتملت بعد WhenAll
        var payment  = paymentTask.Result;

        var degraded = shipment is null || payment is null;
        if (degraded)
        {
            log.LogWarning("partial aggregation for {OrderId}: shipping={S} payments={P}",
                orderId, shipment is not null, payment is not null);
            GatewayMetrics.PartialResponses.Add(1);
        }

        return Results.Ok(new OrderDetailsPage(
            Order: order,
            Shipment: shipment,
            Payment: payment,
            Meta: new PageMeta(Degraded: degraded,
                MissingSections: Missing(shipment, payment),
                GeneratedAt: time.GetUtcNow())));
    }

    private static string[] Missing(ShipmentDto? s, PaymentDto? p) =>
        [.. new[] { s is null ? "shipping" : null, p is null ? "payment" : null }.Where(x => x is not null)!];

    private async Task<T?> TryAsync<T>(string name, CancellationToken ct, Func<Task<T>> call, bool required)
    {
        try
        {
            // ✓ مهلة لكل قسم مستقلًا — قسم بطيء لا يسحب المهلة كلها
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
            timeout.CancelAfter(SectionTimeout);
            return await call().WaitAsync(SectionTimeout, timeout.Token);
        }
        catch (Exception ex) when (ex is TaskCanceledException or TimeoutException or HttpRequestException)
        {
            GatewayMetrics.SectionFailures.Add(1, new("section", name));
            if (required) { log.LogError(ex, "required section {Section} failed", name); throw; }
            log.LogWarning(ex, "optional section {Section} unavailable — degrading", name);
            return default;
        }
    }
}

public sealed record OrderDetailsPage(OrderDto Order, ShipmentDto? Shipment, PaymentDto? Payment, PageMeta Meta);
public sealed record PageMeta(bool Degraded, string[] MissingSections, DateTimeOffset GeneratedAt);

// تسجيل كمسار في الـgateway (بلا تمرير عبر YARP)
public static class CompositionEndpoints
{
    public static void Map(this IEndpointRouteBuilder app) =>
        app.MapGet("/bff/orders/{orderId:guid}/details",
            async (Guid orderId, string? accessToken, OrderDetailsAggregator agg, CancellationToken ct) =>
                await agg.GetAsync(orderId, accessToken, ct))
           .RequireAuthorization()
           .WithTags("BFF")
           .Produces<OrderDetailsPage>();
}
'''},
            {"type": "callout", "kind": "danger", "title": "الـgateway ليس مكان منطق العمل",
             "md": """
أشهر انهيار معماري: الـgateway يبدأ يحتوي قواعد عمل (حساب أسعار، تحقق من مخزون، تحويل DTOs معقدة).
النتيجة: **distributed monolith** — كل الخدمات مقترنة بنشر الـgateway، وهو نقطة فشل واحدة لكل شيء.

**ما يُسمح به في الـgateway:**
توجيه، تحويلات (headers/path)، مصادقة/تفويض عند الحافة، rate limiting، retries/timeouts/circuit breakers،
تجميع عرض **بلا قواعد** (fan-out + دمج)، ضغط/كاش استجابات عامة، مراقبة، canary.

**ما يُمنع:**
قواعد عمل، وصول مباشر لقواعد بيانات الخدمات، معاملات، منطق تسعير/مخزون،
وتحويلات معقدة للـDTOs (دي مسؤولية BFF مخصص أو الخدمة نفسها).

والقاعدة التشغيلية: **شغّل نسختين على الأقل من الـgateway** خلف load balancer — هو نقطة دخول وحيدة،
فلازم ما يكونش نقطة فشل وحيدة.
"""},
            {"type": "heading", "level": 2, "text": "3) YARP مقابل ingress مقابل service mesh"},
            {"type": "table", "head": ["المعيار", "YARP (داخل .NET)", "K8s Ingress / Envoy", "Service Mesh (Istio/Linkerd)"], "rows": [
                ["أين يعمل", "عملية ASP.NET Core (تطبيق)", "على حافة الـcluster", "sidecar بجانب كل خدمة"],
                ["التخصيص بالكود", "✓ كامل (middleware/transforms)", "△ (annotations/CRDs)", "△ (سياسات mesh)"],
                ["مصادقة/تفويض", "✓ ASP.NET Core (JWT/policies)", "△ (plugins/OIDC proxy)", "✓ (mTLS + policies)"],
                ["mTLS بين الخدمات", "△ يدوي", "△", "✓ تلقائي"],
                ["التتبع/المقاييس", "✓ OpenTelemetry", "✓", "✓✓ تلقائي"],
                ["Canary/تقسيم حركة", "✓ (routes/headers/weights)", "✓ (Ingress annotations)", "✓✓ (قوي)"],
                ["تكلفة التشغيل", "منخفضة (تطبيق عادي)", "متوسطة", "**عالية** (تعلم + موارد)"],
                ["مناسب لـ", "فرق .NET، أنظمة متوسطة، BFF", "K8s موجود أصلًا", "منظمات كبيرة بفرق متعددة اللغات ومتطلبات أمان صارمة"],
            ]},
            {"type": "callout", "kind": "tip", "title": "اختيار عملي لفرق .NET",
             "md": """
- **محليًا / خدمة واحدة / بداية التقسيم**: YARP كتطبيق .NET — أسرع طريق وأسهل تصحيح.
- **على Kubernetes**: Ingress (أو Gateway API) للحافة الخارجية + YARP كـBFF داخلي للواجهات.
- **مؤسسة كبيرة متعددة اللغات**: service mesh لـmTLS والسياسات — لكن ادفع تكلفته بوعي (مش افتراضي).
- **لا تجمع الثلاث طبقات بلا سبب**: كل طبقة بتضيف زمن وتقلل وضوح تتبع الطلب.
"""},
            {"type": "heading", "level": 2, "text": "4) الاختبار والتشغيل"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Gateway.Tests/RoutingTests.cs", "title": "اختبارات التوجيه والتحويلات (على خدمات وهمية)", "code": r'''
public class GatewayRoutingTests : IAsyncLifetime
{
    private WebApplicationFactory<Program> _gateway = default!;
    private StubServer _catalog = default!;                 // خدمة وهمية (HttpListener/Kestrel اختباري)

    public async ValueTask InitializeAsync()
    {
        _catalog = await StubServer.StartAsync();            // يرد بـ200 + جسم معروف ويسجل الرؤوس
        _gateway = new WebApplicationFactory<Program>().WithWebHostBuilder(b =>
            b.UseSetting("ReverseProxy:Clusters:catalog:Destinations:c1:Address", _catalog.BaseUrl));
    }
    public ValueTask DisposeAsync() { _gateway.Dispose(); _catalog.Dispose(); return ValueTask.CompletedTask; }

    [Fact]
    public async Task Route_strips_prefix_and_forwards_to_cluster()
    {
        var client = _gateway.CreateClient();
        var response = await client.GetAsync("/api/catalog/products/KB-1");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        _catalog.LastRequestPath.Should().Be("/catalog/products/KB-1", "PathRemovePrefix + PathPrefix طُبّقا");
    }

    [Fact]
    public async Task Correlation_id_is_generated_and_forwarded_not_trusted()
    {
        var client = _gateway.CreateClient();
        var request = new HttpRequestMessage(HttpMethod.Get, "/api/catalog/products/KB-1");
        request.Headers.Add("X-Correlation-Id", "attacker-controlled");       // ★ محاولة حقن
        request.Headers.Add("X-Internal-Token", "secret");                    // ★ رأس داخلي

        await client.SendAsync(request);

        _catalog.LastHeaders.Should().NotContainKey("X-Internal-Token", "الرؤوس الداخلية تُحذف عند الحافة");
        _catalog.LastHeaders.Should().ContainKey("X-Correlation-Id");
    }

    [Fact]
    public async Task Unauthenticated_request_is_rejected_at_edge()
    {
        var client = _gateway.CreateClient();
        var response = await client.GetAsync("/api/orders/1");

        response.StatusCode.Should().BeOneOf(HttpStatusCode.Unauthorized, HttpStatusCode.Forbidden);
        _catalog.RequestCount.Should().Be(0, "الطلب لم يصل للخدمة أصلًا");
    }

    [Fact]
    public async Task Canary_header_routes_to_v2_cluster()
    {
        var client = _gateway.CreateClient();
        var request = new HttpRequestMessage(HttpMethod.Get, "/api/orders/1");
        request.Headers.Add("X-Canary", "v2");

        await client.SendAsync(request);

        _gateway.Services.GetRequiredService<IProxyStateLookup>()
            .GetClusters().Should().Contain(c => c.ClusterId == "orders-v2");
    }

    [Fact]
    public async Task Unhealthy_destination_is_excluded_by_passive_health()
    {
        _catalog.FailNext(3);                                // 3 أخطاء 502/503
        var client = _gateway.CreateClient();

        for (var i = 0; i < 3; i++) await client.GetAsync("/api/catalog/products/1");

        var cluster = _gateway.Services.GetRequiredService<IProxyStateLookup>()
            .GetClusters().Single(c => c.ClusterId == "catalog");

        cluster.Destinations.Values.Should()
            .Contain(d => d.Model.Health.Passive == DestinationHealth.Unhealthy);
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أعرف ما يُسمح به في الـgateway (توجيه/سياسات/تجميع بلا قواعد) وما يُمنع، وأشغّل نسختين على الأقل.",
                "أضبط YARP بمسارات ومجموعات من الإعدادات أو الكود، مع تحويلات وحدود ومهل وسياسات مفروضة بالاسم.",
                "أطبق سياسات الحافة بالترتيب الصحيح (ForwardedHeaders → logging → security → auth → rate limit → proxy).",
                "أجمّع الاستجابات بتوازي ومهلة لكل قسم وتدهور مُعلن، وأختبر التوجيه والتحويلات وحذف الرؤوس الحساسة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `UseForwardedHeaders` لازم يكون مبكرًا وبـ`KnownProxies` صريح؟",
                 "options": [
                     "للأداء",
                     "لأن الـgateway/الـLB بيضيف رؤوس X-Forwarded؛ من غير تحديد proxies موثوقة، عميل يقدر ينتحل IP وبروتوكول (ويكسر rate limiting وHTTPS detection)",
                     "مطلب YARP",
                     "لتحسين اللوجات فقط",
                 ], "answer": 1,
                 "explain": "قاعدة أمان: لا تثق برؤوس قادمة من عميل. حدّد `KnownProxies`/`KnownNetworks` وامسح الرؤوس الواردة عند الحافة."},
                {"q": "قسم ثانوي (شحن) فشل أثناء تجميع صفحة تفاصيل الطلب. التصرف؟",
                 "options": [
                     "500 للصفحة كلها",
                     "تدهور مقصود: أرجع الصفحة مع `Meta.Degraded=true` وقائمة الأقسام الناقصة + مقياس وتنبيه",
                     "أعد المحاولة للأبد",
                     "ارجع بيانات وهمية",
                 ], "answer": 1,
                 "explain": "الأقسام الثانوية لا يجب أن تسقط الصفحة. لكن **أعلن** التدهور (لا بيانات وهمية صامتة) وقسّه."},
                {"q": "إمتى تحتاج Session Affinity في YARP؟",
                 "options": [
                     "دائمًا",
                     "نادراً: لو الخدمة تحتفظ بحالة في الذاكرة (WebSocket غير مدعوم عبر النسخ، أو تخزين محلي) — والأفضل إصلاح الخدمة لتبقى stateless",
                     "للأداء",
                     "للأمان",
                 ], "answer": 1,
                 "explain": "الـaffinity بتقلل مرونة التوسع وبتعمل hotspots. Services stateless + Redis backplane للحالات المشتركة (درس 2.3.1) هو الحل."},
                {"q": "canary بـ10% من الحركة — أنظف طريقة في YARP؟",
                 "options": [
                     "نسخ الكود لخدمة تانية",
                     "route إضافي بترتيب أسبق (`Order`) يطابق header أو وزن، يوجّه لـcluster الإصدار الجديد، مع إمكانية إزالة الـroute فورًا للرجوع",
                     "DNS",
                     "middleware مخصص يغيّر العنوان",
                 ], "answer": 1,
                 "explain": "الأوزان/Header-based routing في الإعدادات = تغيير بلا نشر كود. رجوع فوري بحذف المسار أو تعديل الوزن."},
                {"q": "الـgateway بقى فيه منطق تسعير وتحقق مخزون. الحكم؟",
                 "options": [
                     "تحسين (نداءات أقل)",
                     "distributed monolith: اقتران نشر لكل الخدمات + نقطة فشل واحدة — انقل المنطق للخدمات وخلّي الـgateway يوجّه ويجمّع فقط",
                     "مقبول لو موثق",
                     "يحتاج كاش",
                 ], "answer": 1,
                 "explain": "اختبار سريع: لو تغيير في خدمة بيحتاج نشر الـgateway → الحدود انكسرت."},
                {"q": "بروكسي gRPC عبر YARP — إيه المطلوب؟",
                 "options": [
                     "لا شيء",
                     "HTTP/2 على الطرفين (`Http2Only` للـcluster) وبلا buffering للاستجابات الـstreaming، وتحقق إن أي proxy وسيط بيدعم HTTP/2",
                     "تحويل لـJSON",
                     "gRPC-Web دائمًا",
                 ], "answer": 1,
                 "explain": "HTTP/1.1 في المنتصف بيكسر gRPC (خصوصًا streaming). تأكد من `HttpProtocols.Http2` و`Http2Only` في الإعدادات."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "gateway يعمل لمشروعك",
                 "md": "ابنِ gateway بـYARP أمام خدمتين/موديولين من مشروعك: مسارات بـtransforms، مصادقة عند الحافة، rate limiting لكل مسار، health checks نشطة وسلبية للوجهات، ومقاييس/تتبع. شغّله بـcompose مع الخدمات.",
                 "criteria": [
                     "≥ 3 مسارات (واحد بـcanary بالـheader، واحد داخلي بسياسة مختلفة)",
                     "تحويلات: إزالة/إضافة prefix، correlation id مولّد (غير موثوق من العميل)، وحذف رؤوس داخلية",
                     "مصادقة JWT عند الحافة **+** في الخدمة (دفاع بالعمق) مع اختبار يثبت رفض غير المصادق",
                     "rate limiter مفروض بالاسم على المسارات مع 429 و`Retry-After`",
                     "active + passive health checks مع إبعاد وجهة مريضة (اختبار)",
                     "تتبع OpenTelemetry يشمل `Yarp.ReverseProxy.Forwarder` ومقياس لكل cluster",
                     "`docker compose` يشغّل gateway + خدمتين + قاعدة، ويثبت التوجيه بـcurl",
                 ],
                 "hint": "لو الاختبارات بتشتكي من `WebApplicationFactory` مع إعدادات YARP: استخدم `UseSetting(\"ReverseProxy:Clusters:…\")` لتغيير الوجهات وقت الاختبار بدل تعديل appsettings."},
                {"id": "t2", "title": "تجميع BFF بفشل جزئي",
                 "md": "أضف endpoint تجميع (BFF) يجمع 3 أقسام من خدمات مختلفة بتوازي، مع مهلة لكل قسم وتدهور مُعلن، واختبر الفشل الجزئي والتجاوز الزمني.",
                 "criteria": [
                     "نداءات متوازية (لا تسلسلية) — مثبت بقياس زمن (≈ أبطأ قسم، مش مجموعها)",
                     "مهلة مستقلة لكل قسم + `WaitAsync`/linked CTS",
                     "قسم أساسي يفشل → 404/503؛ قسم ثانوي يفشل → 200 مع `Meta.Degraded` وقائمة الناقص",
                     "مقاييس: `partial_responses` و`section_failures` بوسم القسم",
                     "لا منطق عمل في المجمع (مراجعة: لا قواعد، لا وصول لقواعد بيانات)",
                     "اختباران: فشل قسم ثانوي، وتجاوز مهلة قسم",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "YARP documentation", "url": "https://yarp.dev/"},
                {"label": "YARP — Config & transforms", "url": "https://yarp.dev/current/docs/config-files"},
                {"label": "Gateway Aggregation (Azure Architecture)", "url": "https://learn.microsoft.com/azure/architecture/patterns/gateway-aggregation"},
                {"label": "Backends for Frontends", "url": "https://learn.microsoft.com/azure/architecture/patterns/backends-for-frontends"},
                {"label": "Kubernetes Gateway API", "url": "https://gateway-api.sigs.k8s.io/"},
                {"label": "HTTP Resilience (Microsoft.Extensions.Http.Resilience)", "url": "https://learn.microsoft.com/dotnet/core/resilience/http-resilience"},
            ]},
        ],
    },
]
