"""Stage 2, Module 1 — Modern API design (lessons 1-3 of 6)."""

TODAY = "2026-10-22"

LESSONS_S2_A = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s2-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
في .NET 10 مفيش سؤال «Minimal APIs ولا Controllers؟» كسؤال ديني — فيه سؤال: **أنهي أسلوب يديك أقل كود
وأوضح عقد لنهاية (endpoint) معينة؟** الـMinimal APIs بقت ناضجة: groups، endpoint filters، OpenAPI metadata،
validation، وTypedResults. والـControllers لسه أفضل لما عندك تراث كبير أو بتحتاج action filters/model binders معقدة.

الدرس ده: تبني API بـMinimal APIs **منظّم بـfeatures** (مش Program.cs بـ2000 سطر)، وتكتب قرار الاختيار بمعايير.
"""},
            {"type": "terms", "items": [
                {"term": "Endpoint", "def": "وحدة التنفيذ: مسار + HTTP method + delegate. Minimal APIs بتعرّفها مباشرة على الـrouter."},
                {"term": "Route Group", "def": "`MapGroup(\"/api/orders\")` — prefix + إعدادات مشتركة (auth، rate limit، tags، filters) لكل endpoints المجموعة."},
                {"term": "TypedResults", "def": "نسخة من `Results` بأنواع إرجاع صريحة (`ValidationProblem`، `NotFound<T>`) → metadata أدق في OpenAPI."},
                {"term": "Endpoint Filter", "def": "كود cross-cutting يدور حول endpoint واحد أو مجموعة (validation، logging، authorization إضافي) بدون middleware عام."},
                {"term": "IEndpointRouteBuilder", "def": "الواجهة اللي بتمدها extension methods عشان تسجّل endpoints من أي مكان في الكود."},
                {"term": "Feature folder", "def": "تنظيم حسب القدرة (`Orders/`, `Catalog/`) بدل الطبقات (`Controllers/`, `Models/`) — أساس الـvertical slice."},
            ]},
            {"type": "heading", "level": 2, "text": "القرار: معايير مش تفضيلات"},
            {"type": "table", "head": ["المعيار", "Minimal APIs", "Controllers"], "rows": [
                ["حجم الكود لـendpoint بسيط", "أقل (delegate + typed result)", "أكثر (class + attributes + action)"],
                ["OpenAPI metadata", "ممتاز مع `TypedResults` و`Produces<T>()`", "ممتاز مع `ApiController` و`ProducesResponseType`"],
                ["Filters", "Endpoint filters (بسيطة، قابلة للتركيب)", "Action/Result/Exception filters (أغنى)"],
                ["Model binding معقّد", "جيد؛ أقل مرونة في custom binders", "أقوى (custom model binders, form files)"],
                ["إرث موجود", "إعادة كتابة مكلفة", "الأفضل لو عندك مئات الـactions"],
                ["فريق كبير ومنظم", "يحتاج انضباط في التنظيم", "الـconvention واضح تلقائيًا"],
                ["الأداء", "أقل overhead (بدون pipeline الـMVC)", "overhead أعلى قليلًا"],
            ], "caption": "الخلاصة العملية: مشروع جديد → Minimal APIs. مشروع MVC قائم → ما تهاجرش لمجرد الموضة."},
            {"type": "heading", "level": 2, "text": "التنظيم: feature folder + extension methods"},
            {"type": "code", "lang": "text", "title": "شكل المشروع", "code": r'''
Shop.Api/
  Program.cs                     ← 20-40 سطر بس: build الـhost وربط الـfeatures
  Infrastructure/
    ExceptionHandling/GlobalExceptionHandler.cs
    Filters/ValidationEndpointFilter.cs
  Features/
    Orders/
      OrdersEndpoints.cs         ← MapOrdersApi(this IEndpointRouteBuilder)
      OrdersHandlers.cs
      OrderDtos.cs
      CreateOrderValidator.cs
    Catalog/
      CatalogEndpoints.cs
      ...
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "Program.cs يبقى صغيرًا — كل feature بتسجّل نفسها", "code": r'''
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails();
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddOpenApi();
builder.Services.AddApplicationServices(builder.Configuration);   // DI لكل الـfeatures

var app = builder.Build();

app.UseExceptionHandler(string.Empty);
app.UseSerilogRequestLogging();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();                 // → /openapi/v1.json
    app.MapScalarApiReference();      // → /scalar/v1
}

app.UseAuthentication();
app.UseAuthorization();

app.MapOrdersApi();                   // ← كل feature بتضيف endpoints الخاصة بيها
app.MapCatalogApi();
app.MapHealthChecks("/health/live");

app.Run();

public partial class Program;         // للاختبارات (WebApplicationFactory<Program>)
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/OrdersEndpoints.cs", "title": "Group + filters + metadata صريحة", "code": r'''
using Microsoft.AspNetCore.Http.HttpResults;

public static class OrdersEndpoints
{
    public static IEndpointRouteBuilder MapOrdersApi(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orders")
            .WithTags("Orders")
            .RequireAuthorization("CustomerOrAdmin")
            .AddEndpointFilter<ValidationEndpointFilter<CreateOrderRequest>>()
            .RequireRateLimiting("orders-write");

        group.MapPost("/", CreateOrder)
            .WithName("CreateOrder")
            .Produces<Created<OrderCreatedResponse>>(StatusCodes.Status201Created)
            .ProducesValidationProblem()
            .ProducesProblem(StatusCodes.Status404NotFound);

        group.MapGet("/{id:guid}", GetOrder)
            .WithName("GetOrder")
            .Produces<OrderResponse>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status404NotFound);

        group.MapGet("/", ListOrders)
            .WithName("ListOrders")
            .RequireAuthorization()
            .Produces<PagedResult<OrderSummary>>(StatusCodes.Status200OK);

        group.MapPost("/{id:guid}/cancel", CancelOrder)
            .WithName("CancelOrder")
            .RequireAuthorization("AdminOnly")
            .Produces<NoContent>(StatusCodes.Status204NoContent)
            .ProducesProblem(StatusCodes.Status409Conflict);

        return app;
    }

    // الـhandler نفسه: دالة ساكنة نقية — سهلة الاختبار وقابلة للـsource generation
    private static async Task<Results<Created<OrderCreatedResponse>, ValidationProblem>> CreateOrder(
        CreateOrderRequest request,
        IOrderService orders,
        CancellationToken ct)
    {
        var order = await orders.CreateAsync(request, ct);
        return TypedResults.Created($"/api/orders/{order.Id}", new OrderCreatedResponse(order.Id, order.Total));
    }

    private static async Task<Results<Ok<OrderResponse>, NotFound<ProblemDetails>>> GetOrder(
        Guid id, IOrderService orders, CancellationToken ct) =>
        await orders.GetAsync(id, ct) is { } order
            ? TypedResults.Ok(OrderResponse.From(order))
            : TypedResults.NotFound(ProblemDetailsFactory.ForNotFound(id));

    private static async Task<Ok<PagedResult<OrderSummary>>> ListOrders(
        [AsParameters] OrderListQuery query, IOrderService orders, CancellationToken ct) =>
        TypedResults.Ok(await orders.ListAsync(query, ct));

    private static async Task<Results<NoContent, Conflict<ProblemDetails>>> CancelOrder(
        Guid id, IOrderService orders, CancellationToken ct) =>
        await orders.CancelAsync(id, ct)
            ? TypedResults.NoContent()
            : TypedResults.Conflict(ProblemDetailsFactory.ForConflict("Order", id, "لا يمكن إلغاء طلب مدفوع"));
}
'''},
            {"type": "callout", "kind": "tip", "title": "ليه `Results<A, B>` مش `IActionResult`",
             "md": """
الـunion type ده **هو** مصدر الـmetadata: لما تكتب `Results<Created<T>, ValidationProblem>`
الـOpenAPI generator يعرف تلقائيًا إن فيه 201 و400، و`TypedResults` بيرجّع أنواع صريحة.
لو رجّعت `IResult` عام، هتحتاج `Produces<T>()` يدويًا لكل حالة — وناسيين كتير بينسوها.
القاعدة: **اكتب كل حالات الفشل في التوقيع**، حتى لو حسيتها تطويل.
"""},
            {"type": "heading", "level": 2, "text": "Endpoint Filters: المكان الصح للـcross-cutting"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Filters/ValidationEndpointFilter.cs", "title": "FluentValidation كـendpoint filter قابل لإعادة الاستخدام", "code": r'''
using FluentValidation;

/// <summary>
/// Filter عام: يلاقي الـvalidator المناسب لنوع TRequest وينفّذه قبل الـhandler.
/// .NET 10 فيه دعم validation مدمج في Minimal APIs — راجع الرابط في المصادر،
/// لكن الـfilter ده بيشتغل على أي إصدار وبيديك تحكم كامل في شكل الاستجابة.
/// </summary>
public sealed class ValidationEndpointFilter<TRequest>(IValidator<TRequest> validator) : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
    {
        var request = ctx.Arguments.OfType<TRequest>().FirstOrDefault();
        if (request is null) return await next(ctx);

        var result = await validator.ValidateAsync(request, ctx.HttpContext.RequestAborted);
        if (result.IsValid) return await next(ctx);

        var errors = result.Errors
            .GroupBy(e => e.PropertyName)
            .ToDictionary(g => g.Key, g => g.Select(e => e.ErrorMessage).ToArray());

        return TypedResults.ValidationProblem(errors);
    }
}

/// <summary>Filter بسيط: تسجيل زمن التنفيذ لكل endpoint (بديل مصغر عن APM).</summary>
public sealed class TimingEndpointFilter(ILogger<TimingEndpointFilter> log) : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
    {
        var started = TimeProvider.System.GetTimestamp();
        try { return await next(ctx); }
        finally
        {
            var elapsed = TimeProvider.System.GetElapsedTime(started);
            if (elapsed > TimeSpan.FromMilliseconds(300))
                log.LogWarning("slow endpoint {Endpoint} took {Elapsed}ms",
                    ctx.HttpContext.GetEndpoint()?.DisplayName, elapsed.TotalMilliseconds);
        }
    }
}
'''},
            {"type": "table", "head": ["الموقف", "استخدم"], "rows": [
                ["منطق يخص endpoint/مجموعة endpoints (validation، authorization إضافي)", "Endpoint filter"],
                ["منطق يخص كل الطلبات (logging، correlation id، handling الأخطاء)", "Middleware / `UseExceptionHandler`"],
                ["منطق يخص الاستجابة نفسها (كاش، ضغط، رؤوس)", "Middleware مخصص أو Output caching"],
                ["تحويل استثناء لحالة HTTP موحدة", "`IExceptionHandler`"],
                ["قياس/تتبع (metrics, tracing)", "Middleware + OpenTelemetry"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/ExceptionHandling/GlobalExceptionHandler.cs", "title": "استثناء واحد → problem+json واحد", "code": r'''
using Microsoft.AspNetCore.Diagnostics;

public sealed class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> log) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext ctx, Exception ex, CancellationToken ct)
    {
        var traceId = ctx.TraceIdentifier;
        var (status, title) = ex switch
        {
            NotFoundException       => (StatusCodes.Status404NotFound,    "المورد غير موجود"),
            ConflictException       => (StatusCodes.Status409Conflict,      "تعارض مع الحالة الحالية"),
            InsufficientStockException => (StatusCodes.Status422UnprocessableEntity, "المخزون غير كافٍ"),
            TimeoutException        => (StatusCodes.Status504GatewayTimeout,"تعذّر إتمام العملية"),
            _                       => (StatusCodes.Status500InternalServerError, "خطأ غير متوقع"),
        };

        // 5xx يُسجَّل بالكامل؛ 4xx خطأ عميل فلا يلوث السجلات بمستوى Error
        if (status >= 500) log.LogError(ex, "unhandled error on {Path} trace={TraceId}", ctx.Request.Path, traceId);
        else               log.LogInformation("{Type} on {Path}: {Message}", ex.GetType().Name, ctx.Request.Path, ex.Message);

        ctx.Response.StatusCode = status;
        await ctx.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Status = status,
            Title = title,
            Detail = status >= 500 ? null : ex.Message,   // لا تسرّب تفاصيل داخلية
            Instance = ctx.Request.Path,
            Extensions = { ["traceId"] = traceId },
        }, cancellationToken: ct);

        return true;
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء شائعة في Minimal APIs",
             "md": """
- **Program.cs بيكبر لـ1500 سطر** → الحل في extension methods لكل feature (`MapOrdersApi`).
- **رجوع `IResult` بدل `Results<A,B>`** → OpenAPI ناقص والمستهلك ما يعرفش حالات الفشل.
- **نسيان `CancellationToken`** → طلبات ملغاة بتكمل شغلها في الخلفية (تسريب موارد).
- **`app.MapPost("/", async (MyDto dto) => ...)` بدون `[FromBody]` في حالة ambiguous** → لو عندك أكثر من مصدر (route + body)، وضّح بـ`[AsParameters]` أو أنواع صريحة.
- **تسجيل الـhandlers كـservices** مش ضروري — لكن لو الـhandler بياخد 8 تبعيات، دي إشارة إن المنطق لازم يكون في service وراه handler رفيع.
"""},
            {"type": "checkpoints", "items": [
                "أبرر اختيار Minimal APIs أو Controllers بمعايير (مش بتفضيل).",
                "أنظم endpoints في feature folders مع `MapGroup` وextension methods.",
                "أرجّع `Results<A,B>` صريحة عشان OpenAPI يعكس كل حالات الفشل.",
                "أكتب endpoint filter وأعرف الفرق بينه وبين الـmiddleware.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "أهم فائدة عملية لـ`Results<Created<T>, ValidationProblem>` في التوقيع؟",
                 "options": [
                     "أسرع في التنفيذ",
                     "الـOpenAPI metadata بيولّد حالات الاستجابة تلقائيًا بدون `Produces` يدوي",
                     "يمنع الأخطاء في وقت الترجمة",
                     "بيختصر عدد الأسطر",
                 ], "answer": 1,
                 "explain": "الأنواع الصريحة هي مصدر الحقيقة للعقد. من غيرها لازم تفتكر تضيف `Produces`/`ProducesValidationProblem` لكل حالة."},
                {"q": "validation خاص بـCreateOrderRequest — أنهي أداة أنسب؟",
                 "options": ["Middleware عام", "Endpoint filter على مجموعة orders", "Background service", "Health check"],
                 "answer": 1,
                 "explain": "الـfilter بيتنفذ حول الـendpoint المعني بس، فبيبقى أرخص وأوضح من middleware يمر على كل الطلبات."},
                {"q": "ليه `Program.cs` المفروض يفضل صغير؟",
                 "options": [
                     "متطلب تشغيلي",
                     "عشان التسجيل والتوجيه يبقوا مركزيين وواضحين، والمنطق يتوزع على features قابلة للاختبار",
                     "عشان الأداء",
                     "عشان الـDI",
                 ], "answer": 1,
                 "explain": "Program.cs هو مكان **التكوين**. لما يتحول لمكان **التنفيذ**، الاختبار وإعادة الاستخدام بيصبحوا صعبين."},
                {"q": "نسيان تمرير `CancellationToken` للـhandler يسبب إيه؟",
                 "options": [
                     "مفيش أثر",
                     "شغل بيكمل بعد إلغاء العميل: استهلاك اتصال قاعدة بيانات وموارد بلا فائدة",
                     "فشل الترجمة",
                     "401",
                 ], "answer": 1,
                 "explain": "الـtoken بيوصل من `HttpContext.RequestAborted`. بدونه، الإلغاء ما بينتشرش لـEF Core أو HttpClient."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "إعادة تنظيم API موجود (أو بناء جديد)",
                 "md": "حوّل endpoints لمشروعك إلى feature folders مع `MapGroup` و`MapXxxApi` extension methods، واجعل Program.cs أقل من 50 سطرًا. رجّع `Results<A,B>` صريحة في 3 endpoints على الأقل.",
                 "criteria": [
                     "Program.cs ≤ 50 سطر وكل feature بتسجّل نفسها",
                     "3 endpoints على الأقل بتستخدم union types صريحة",
                     "OpenAPI document يعرض حالات 200/201/400/404/409 بشكل صحيح",
                     "اختبارات الـIntegration من المرحلة 1 لسه ناجحة",
                 ],
                 "hint": "ابدأ بنقل endpoints لمجلد feature واحد وتأكد إن الاختبارات عايزة، ثم كرر. النقل الجماعي مرة واحدة بيصعّب التشخيص."},
                {"id": "t2", "title": "قرار مكتوب",
                 "md": "اكتب ADR قصير (نصف صفحة): أنهي أسلوب اخترت لمشروعك، المعايير اللي حكمتك، وإمتى هتعيد النظر. احفظه في ملاحظات الدرس.",
                 "criteria": [
                     "يذكر 3 معايير على الأقل من جدول الدرس",
                     "يحدد شرطًا قابلًا للقياس لإعادة النظر",
                     "لا يعتمد على «أشهر» أو «أحدث» كسبب وحيد",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Minimal APIs overview", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis"},
                {"label": "Minimal APIs — parameter binding", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/parameter-binding"},
                {"label": "Endpoint filters", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/filters"},
                {"label": "TypedResults", "url": "https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.http.typedresults"},
                {"label": "Handle errors with IExceptionHandler", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/error-handling"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s2-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الـAPI من غير وثيقة حيّة = دعم لا نهائي في الشات. في .NET 10 الـOpenAPI document **بيتولّد من الكود نفسه**
(مش ملف YAML تكتبه بإيدك ويتقادم)، وواجهة **Scalar** بتعرضه بشكل أسرع وأدق من Swagger UI التقليدي.

الدرس ده: توليد المستند، إثراؤه بالأوصاف والأمثلة، تجميعه حسب الإصدارات، وعرضه — وضمان إنه ما يكذبش.
"""},
            {"type": "terms", "items": [
                {"term": "OpenAPI 3.1", "def": "مواصفة وصف الـAPI (مسارات، معاملات، مخططات، أمان). .NET 10 بيولّد 3.1 بدل 3.0."},
                {"term": "`AddOpenApi` / `MapOpenApi`", "def": "توليد المستند وعرضه على `/openapi/v1.json` — مدمج في ASP.NET Core (بدون Swashbuckle)."},
                {"term": "Scalar", "def": "واجهة تفاعلية حديثة (`Scalar.AspNetCore`) تعرض المستند مع أمثلة وrequests جاهزة."},
                {"term": "`IOpenApiDocumentTransformer`", "def": "خطوة تعديل على المستند النهائي (أمان، معلومات، وسوم، مسارات)."},
                {"term": "`IOpenApiOperationTransformer`", "def": "تعديل عملية (endpoint) واحدة: وصف، أمثلة، رؤوس."},
                {"term": "Schema examples", "def": "أمثلة على المخططات والاستجابات — أكتر حاجة بتقلل أسئلة المستهلكين."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
# توليد OpenAPI مدمج في ASP.NET Core 10 — لا حزمة إضافية
dotnet add Shop.Api package Scalar.AspNetCore      # الواجهة التفاعلية
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "التوليد والعرض", "code": r'''
builder.Services.AddOpenApi(options =>
{
    // إخفاء رؤوس التشخيص الداخلية من المستند
    options.AddDocumentTransformer<SecuritySchemeTransformer>();
    options.AddDocumentTransformer<ApiInfoTransformer>();
    options.AddOperationTransformer<ExamplesOperationTransformer>();
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();                                  // GET /openapi/v1.json
    app.MapScalarApiReference(options =>
    {
        options.Title = "Shop API";
        options.DefaultHttpClient = new(ScalarTarget.Http, ScalarClient.Curl);
        options.AddPreferredSecuritySchemes("Bearer");
    });                                                // GET /scalar/v1
}
'''},
            {"type": "callout", "kind": "warn", "title": "لا تعرض المستند في الإنتاج هكذا",
             "md": """
`app.MapOpenApi()` في الإنتاج = خريطة كاملة لهجومك. الاختيارات:
1. **الأفضل**: ولّد المستند وقت البناء واحفظه كملف (`dotnet run -- --openapi out.json` أو MSBuild target) ووزعه على مستهلكين محددين.
2. اعرضه خلف مصادقة/شبكة داخلية فقط.
3. لو لازم عام: `RequireAuthorization()` على `MapOpenApi()` و`MapScalarApiReference()`.
"""},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/OpenApi/Transformers.cs", "title": "إثراء المستند: معلومات، أمان، أمثلة", "code": r'''
using Microsoft.AspNetCore.OpenApi;
using Microsoft.OpenApi;

public sealed class ApiInfoTransformer : IOpenApiDocumentTransformer
{
    public Task TransformAsync(OpenApiDocument document, OpenApiDocumentTransformerContext ctx, CancellationToken ct)
    {
        document.Info = new OpenApiInfo
        {
            Title = "Shop API",
            Version = "v1",
            Description = """
                API للمتجر. كل الأخطاء تُرجَع بصيغة `application/problem+json` (RFC 9457)
                مع `traceId` يربط الاستجابة بالسجلات.
                """,
            Contact = new OpenApiContact { Name = "Platform Team", Email = "api@example.com" },
        };

        document.Components ??= new OpenApiComponents();
        document.Components.SecuritySchemes["Bearer"] = new OpenApiSecurityScheme
        {
            Type = SecuritySchemeType.Http,
            Scheme = "bearer",
            BearerFormat = "JWT",
            Description = "ضع access token هنا (بدون كلمة Bearer).",
        };
        document.SecurityRequirements.Add(new OpenApiSecurityRequirement
        {
            [new OpenApiSecurityScheme { Reference = new OpenApiReference { Id = "Bearer", Type = ReferenceType.SecurityScheme } }] = [],
        });

        return Task.CompletedTask;
    }
}

/// <summary>أمثلة للاستجابات — أعلى قيمة للمستهلك.</summary>
public sealed class ExamplesOperationTransformer : IOpenApiOperationTransformer
{
    public Task TransformAsync(OpenApiOperation operation, OpenApiOperationTransformerContext ctx, CancellationToken ct)
    {
        if (ctx.Description.RelativePath == "/api/orders" && ctx.Description.HttpMethod == "POST")
        {
            operation.Summary = "إنشاء طلب جديد";
            operation.Description = "يتحقق من المخزون ويحسب الخصم حسب الدولة. يحتاج دور `customer` أو `admin`.";

            AddExample(operation, StatusCodes.Status201Created, """
                { "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "total": 228.00, "currency": "EGP" }
                """);
            AddExample(operation, StatusCodes.Status400BadRequest, """
                {
                  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.1",
                  "title": "One or more validation errors occurred.",
                  "status": 400,
                  "errors": { "Lines[0].Quantity": ["الكمية يجب أن تكون أكبر من صفر"] },
                  "traceId": "0HMV1..."
                }
                """);
        }
        return Task.CompletedTask;
    }

    private static void AddExample(OpenApiOperation op, int status, string json)
    {
        if (!op.Responses.TryGetValue(status.ToString(), out var response)) return;
        response.Content["application/json"] ??= new OpenApiMediaType();
        response.Content["application/json"].Example = new OpenApiString(json);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "أهم 6 قواعد لوثيقة ما تكذبش"},
            {"type": "steps", "title": "قائمة الفحص", "items": [
                {"title": "كل endpoint له `WithName` و`WithTags`",
                 "md": "الاسم بيولّد operationId ثابت (المستهلكين بيعتمدوا عليه في توليد الكود)، والوسم بيجمّع المسارات في الواجهة."},
                {"title": "كل حالات الفشل معلنة",
                 "md": "`Results<A,B>` أو `ProducesProblem(404)`. حالة مش معلنة = مفاجأة في الإنتاج.",
                 "code": {"lang": "csharp", "title": "إعلان صريح", "code": "group.MapGet(\"/{id:guid}\", GetOrder)\n    .Produces<OrderResponse>(200)\n    .ProducesProblem(404)\n    .ProducesProblem(401);"}},
                {"title": "problem+json موثق كنمط عام",
                 "md": "اعمل schema مشترك لـ`ProblemDetails` و`ValidationProblemDetails` وارجع له (`$ref`) في كل استجابات الأخطاء."},
                {"title": "أمثلة حقيقية على الطلب والاستجابة",
                 "md": "مثال واحد دقيق بيوفر ساعات شرح. استخدم قيم واقعية (EGP، تواريخ بصيغة ISO 8601)."},
                {"title": "الأمان معلن",
                 "md": "security scheme + أنهي endpoint محتاج أنهي دور. من غيره المستهلك هيجرب ويحصل على 401 مش مفهومة."},
                {"title": "تحقق تلقائي في CI",
                 "md": "قارن المستند المولّد بالنسخة المعتمدة (golden file) — أي تغيير في العقد يظهر في الـPR.",
                 "code": {"lang": "bash", "title": "فحص العقد في CI", "code": "# ولّد المستند\ndotnet run --project Shop.Api -- --dump-openapi openapi.json\n# قارن بالنسخة المعتمدة (فشل لو العقد اتغير بدون تحديث متعمد)\ngit diff --exit-code --no-index docs/openapi.approved.json openapi.json"}},
            ]},
            {"type": "callout", "kind": "note", "title": "OpenAPI 3.1 — إيه الجديد اللي يهمك؟",
             "md": """
3.1 متوافقة مع JSON Schema 2020-12: `nullable` بقى `type: [\"string\", \"null\"]`، و`exclusiveMinimum` رقم مش boolean،
ودعم `webhooks`. الأثر العملي عليك: **أدوات توليد كود قديمة** (مبنية على 3.0) ممكن تفشل في قراءة المستند.
جرّب مولّد العميل بتاعك على المستند قبل ما تسلّمه لفريق تاني.
"""},
            {"type": "table", "head": ["الأداة", "الدور", "متى"], "rows": [
                ["`AddOpenApi` (مدمج)", "توليد المستند من الكود", "الافتراضي في .NET 10"],
                ["Scalar", "واجهة تفاعلية للمستهلك", "داخليًا وللمطورين"],
                ["NSwag / openapi-generator", "توليد عميل C#/TS من المستند", "لما يكون عندك frontend منفصل"],
                ["Stoplight / Postman", "مشاركة وتجميع واختبار يدوي", "مع فرق خارجية"],
                ["golden file diff في CI", "كشف تغييرات العقد غير المقصودة", "كل PR"],
            ]},
            {"type": "checkpoints", "items": [
                "أولّد OpenAPI 3.1 من الكود وأعبر عنه في Scalar.",
                "أثري المستند بـtransformers (معلومات، أمان، أمثلة).",
                "أعلن كل حالات الفشل والأدوار المطلوبة لكل endpoint.",
                "أحمي العقد بـgolden file diff في الـCI، ولا أعرض المستند في الإنتاج بلا حماية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه التوليد من الكود أفضل من كتابة YAML بإيدك؟",
                 "options": [
                     "أسرع في التشغيل",
                     "ما يتقادمش: المستند مشتق من التوقيعات والأنواع الحقيقية",
                     "أصغر حجمًا",
                     "بيدعم GraphQL",
                 ], "answer": 1,
                 "explain": "الوثيقة اليدوية بتكذب بعد أول تعديل على الكود. التوليد بيخلي المستند ناتج بناء."},
                {"q": "أخطر خطأ في نشر الـOpenAPI في الإنتاج؟",
                 "options": [
                     "الحجم الكبير",
                     "عرض المستند والواجهة بلا مصادقة = خريطة كاملة لسطح الهجوم",
                     "بطء Scalar",
                     "عدم دعم 3.1",
                 ], "answer": 1,
                 "explain": "الحل: ولّد وقت البناء ووزّع على مستهلكين محددين، أو اعرضه خلف auth/شبكة داخلية."},
                {"q": "`WithName(\"CreateOrder\")` — فايدته الأساسية؟",
                 "options": [
                     "تسريع التوجيه",
                     "توليد operationId ثابت يستخدمه مولّدو كود العميل، وربط الـlinks بين العمليات",
                     "الأمان",
                     "الكاش",
                 ], "answer": 1,
                 "explain": "من غيره الأسماء بتتولد تلقائيًا وبتتغير مع أي تعديل، فينكسر كود العميل المولّد."},
                {"q": "golden file diff للمستند في CI بيحميك من إيه؟",
                 "options": [
                     "الأخطاء الإملائية",
                     "تغييرات غير مقصودة في العقد (كسر للمستهلكين) تعدي في الـPR بدون انتباه",
                     "بطء البناء",
                     "تسريب الأسرار",
                 ], "answer": 1,
                 "explain": "العقد ده واجهة عامة. أي تغيير فيه لازم يكون متعمدًا ومراجَعًا — مش أثرًا جانبيًا لتعديل DTO."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "وثيقة كاملة لـAPI عندك",
                 "md": "فعّل `AddOpenApi` + `MapOpenApi` + Scalar، وأضف transformers للمعلومات والأمان (Bearer) والأمثلة. تأكد إن كل endpoint له tags وname وكل حالات الفشل معلنة.",
                 "criteria": [
                     "`/openapi/v1.json` يرجع مستند 3.1 صالح و`/scalar/v1` يفتحه",
                     "كل endpoint له `WithTags` و`WithName`",
                     "استجابات 400/401/404/409 معلنة مع مثال problem+json واحد على الأقل",
                     "security scheme باسم Bearer مطبّق على الـendpoints المحمية",
                 ],
                 "hint": "لو المستند فاضي: تأكد إن `MapOpenApi()` بيتنادى **بعد** تسجيل الـendpoints في الـpipeline، وإن المجموعة مش معزولة عن `app`."},
                {"id": "t2", "title": "حارس العقد في CI",
                 "md": "أضف خطوة في الـworkflow تولّد المستند وتقارنه بنسخة معتمدة في الـrepo، وتفشل لو اختلفت. وثّق في README إزاي تحدّث النسخة المعتمدة عمدًا.",
                 "criteria": [
                     "الـCI يفشل عند تغيير عقد غير مقصود (جرّب بتعديل DTO)",
                     "تحديث النسخة المعتمدة إجراء موثق بسطر واحد",
                     "المستند لا يُعرض في الإنتاج بلا حماية",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "OpenAPI in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/openapi"},
                {"label": "Customize OpenAPI documents with transformers", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/openapi/customize-openapi"},
                {"label": "Scalar", "url": "https://scalar.com/"},
                {"label": "OpenAPI 3.1 specification", "url": "https://spec.openapis.org/oas/v3.1.0"},
                {"label": "RFC 9457 — Problem Details", "url": "https://www.rfc-editor.org/rfc/rfc9457"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l3
    {
        "id": "s2-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
تلات حاجات بتفرق بين API هاوي وAPI إنتاجي: **الإصدارات** (تغيّر العقد بدون كسر العملاء)،
**الترقيم** (offset بيبقى بطيء ومؤلم مع نمو البيانات — cursor بيحلها)،
و**الفلترة والفرز** (عقد موحّد بدل endpoint لكل حالة).

الدرس ده بيبني التلاتة بكود جاهز للنسخ والتعديل، مع الحدود اللي لازم تعرفها.
"""},
            {"type": "terms", "items": [
                {"term": "API Versioning", "def": "تشغيل أكثر من إصدار من العقد في نفس الوقت مع خطة تقاعد معلنة."},
                {"term": "URL segment vs Header vs Query", "def": "طرق حمل رقم الإصدار: `/api/v1/…` (الواضح والكاش-صديق)، رأس `api-version`، أو query string."},
                {"term": "Offset pagination", "def": "`skip/take` — بسيط لكن `OFFSET 100000` بيكلف مسح كل الصفوف السابقة."},
                {"term": "Cursor (keyset) pagination", "def": "ترقيم بمفتاح مرتب (وقت + id): `WHERE (created_at, id) > (cursor)` — أداء ثابت مهما كان العمق."},
                {"term": "Stable sort key", "def": "مفتاح ترتيب فريد وثابت. بدون `Id` كمكسّر تعادل، الصفوف بتتكرر أو بتضيع بين الصفحات."},
                {"term": "Filter contract", "def": "قواعد موحدة للفلترة (`status=paid&country=EG&min=100`) بدل endpoints مكررة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الإصدارات: ابدأ بسيطًا"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/OrdersEndpoints.cs", "title": "خيار أ: مجموعات إصدار صريحة (بلا حزم — الأنسب للبداية)", "code": r'''
public static IEndpointRouteBuilder MapOrdersApi(this IEndpointRouteBuilder app)
{
    // v1: العقد القديم — مجمّد إلا لإصلاح أمني
    var v1 = app.MapGroup("/api/v1/orders").WithTags("Orders v1");
    v1.MapGet("/{id:guid}", GetOrderV1).Produces<OrderResponseV1>();

    // v2: العقد الحالي
    var v2 = app.MapGroup("/api/v2/orders").WithTags("Orders v2");
    v2.MapGet("/{id:guid}", GetOrderV2).Produces<OrderResponseV2>();

    return app;
}

// الـDTOs منفصلة — لا تعدل V1 لإضافة حقل V2
public sealed record OrderResponseV1(Guid Id, decimal Total, string Status);
public sealed record OrderResponseV2(
    Guid Id,
    Money Total,                       // بنية { amount, currency } بدل decimal غامض
    OrderStatus Status,
    IReadOnlyList<OrderLineDto> Lines,
    DateTimeOffset CreatedAt);
'''},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "خيار ب: حزمة الإصدارات الرسمية (لما الإصدارات كتير)", "code": r'''
dotnet add Shop.Api package Asp.Versioning.Http
'''},
            {"type": "code", "lang": "csharp", "title": "Asp.Versioning.Http مع Minimal APIs", "code": r'''
using Asp.Versioning;

builder.Services.AddProblemDetails();
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;                        // رؤوس api-supported-versions / api-deprecated-versions
    options.ApiVersionReader = ApiVersionReader.Combine(
        new UrlSegmentApiVersionReader(),
        new HeaderApiVersionReader("api-version"));
    options.UnsupportedApiVersionStatusCode = StatusCodes.Status400BadRequest;
}).AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";                        // مستند OpenAPI لكل إصدار
    options.SubstituteApiVersionInUrl = true;
});

// في الـpipeline
var versionSet = app.NewApiVersionSet()
    .WithApiVersion(1, 0)
    .WithApiVersion(2, 0)
    .ReportApiVersions()
    .Build();

app.MapGroup("/api/v{version:apiVersion}/orders")
   .WithApiVersionSet(versionSet)
   .MapGet("/{id:guid}", GetOrder)
   .MapToApiVersion(2, 0);                                    // الـendpoint ده موجود في v2 بس
'''},
            {"type": "callout", "kind": "warn", "title": "قواعد الإصدارات اللي بتحميك",
             "md": """
- **إضافة حقل جديد للاستجابة ≠ إصدار جديد** (العملاء بيتجاهلوا الحقول الزائدة). الحذف/إعادة التسمية/تغيير النوع = **كسر** = إصدار جديد.
- **لا تعمل إصدار لكل تعديل صغير**: كل إصدار = عبء صيانة مضاعف (اختبارات، وثائق، مراقبة).
- **أعلن التقاعد**: رأس `Deprecation` + `Sunset` + تاريخ في الوثيقة، ومراقبة استخدام الإصدار القديم قبل حذفه.
- **قيس الاستخدام**: metric لكل إصدار — لو v1 بيستخدمه 2% من الطلبات، جدول تقاعده.
- راجع تفاصيل الحزمة في مستودعها الرسمي قبل الاعتماد عليها (الأسماء أعلاه من الوثائق الحالية).
"""},
            {"type": "heading", "level": 2, "text": "2) Cursor pagination: أداء ثابت عند أي عمق"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Common/Paging.cs", "title": "مفتاح مركّب (CreatedAt, Id) + ترميز آمن للرابط", "code": r'''
public sealed record PageRequest(int Size, string? Cursor)
{
    public int ClampedSize => Math.Clamp(Size is 0 ? 20 : Size, 1, 100);   // حد أعلى: حماية من طلب 100k صف
}

public sealed record PagedResult<T>(IReadOnlyList<T> Items, string? NextCursor, int Size);

public static class CursorCodec
{
    // Cursor = (CreatedAt ticks, Id) → base64url. معتِم بما يكفي للرابط، مش للتشفير.
    public static string Encode(DateTimeOffset createdAt, Guid id)
    {
        var raw = $"{createdAt.UtcTicks}:{id:N}";
        return Convert.ToHexString(Encoding.UTF8.GetBytes(raw)).ToLowerInvariant();
    }

    public static (DateTimeOffset CreatedAt, Guid Id)? Decode(string? cursor)
    {
        if (string.IsNullOrWhiteSpace(cursor)) return null;
        try
        {
            var raw = Encoding.UTF8.GetString(Convert.FromHexString(cursor));
            var parts = raw.Split(':', 2);
            return (new DateTimeOffset(long.Parse(parts[0]), TimeSpan.Zero), Guid.ParseExact(parts[1], "N"));
        }
        catch (Exception) { return null; }        // cursor تالف → ابدأ من الأول بدل 500
    }
}

public static class PagingExtensions
{
    /// <summary>
    /// Keyset pagination على (CreatedAt DESC, Id DESC).
    /// الشرط المركّب ده هو اللي بيمنع تكرار/فقدان الصفوف عند تساوي التواريخ.
    /// </summary>
    public static async Task<PagedResult<OrderSummary>> PageOrdersAsync(
        this AppDbContext db, PageRequest page, OrderFilter filter, CancellationToken ct)
    {
        var query = db.Orders.AsNoTracking().ApplyFilter(filter).AsQueryable();

        if (CursorCodec.Decode(page.Cursor) is { } cursor)
        {
            // (CreatedAt, Id) < (cursorTime, cursorId)  — ترتيب تنازلي
            query = query.Where(o => o.CreatedAt < cursor.CreatedAt
                                  || (o.CreatedAt == cursor.CreatedAt && o.Id.CompareTo(cursor.Id) < 0));
        }

        var rows = await query
            .OrderByDescending(o => o.CreatedAt)
            .ThenByDescending(o => o.Id)          // ← مكسّر التعادل: بدونه الترقيم غير مستقر
            .Take(page.ClampedSize + 1)           // ← صف زيادة عشان نعرف هل فيه صفحة تانية
            .Select(o => OrderSummary.From(o))
            .ToListAsync(ct);

        var hasMore = rows.Count > page.ClampedSize;
        if (hasMore) rows.RemoveAt(rows.Count - 1);

        var last = rows.LastOrDefault();
        var next = hasMore && last is not null ? CursorCodec.Encode(last.CreatedAt, last.Id) : null;

        return new PagedResult<OrderSummary>(rows, next, rows.Count);
    }
}
'''},
            {"type": "table", "head": ["المعيار", "Offset (`skip/take`)", "Cursor (keyset)"], "rows": [
                ["الأداء عند العمق", "يتدهور: `OFFSET 100000` بيمسح 100 ألف صف", "ثابت: فهرس على مفتاح الترتيب"],
                ["القفز لصفحة رقم N", "مدعوم", "غير مدعوم (تنقل تسلسلي فقط)"],
                ["الاستقرار مع إدراجات جديدة", "صفوف بتتكرر/تضيع", "مستقر (المفتاح ثابت)"],
                ["العدد الكلي للصفحات", "سهل (`COUNT(*)`)", "مكلف — غالبًا ما تُرجعه"],
                ["متطلبات", "ترتيب ثابت", "ترتيب **فريد** + فهرس مناسب"],
                ["أنسب حالة", "واجهات إدارية صغيرة", "Feeds، سجلات، تصدير، API عام"],
            ]},
            {"type": "code", "lang": "sql", "title": "الفهرس اللي بيخلي الـcursor سريعًا", "code": r'''
CREATE INDEX ix_orders_createdat_id
    ON orders (created_at DESC, id DESC)
    INCLUDE (status, total, currency);   -- covered index: الاستعلام ما يلمسش الجدول
'''},
            {"type": "heading", "level": 2, "text": "3) الفلترة والفرز: عقد واحد"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/OrderListQuery.cs", "title": "`[AsParameters]` + whitelist صريح (لا تسمح بفرز حر)", "code": r'''
public sealed record OrderListQuery
{
    public int Size { get; init; } = 20;
    public string? Cursor { get; init; }
    public string? Status { get; init; }
    public string? Country { get; init; }
    public decimal? MinTotal { get; init; }
    public decimal? MaxTotal { get; init; }
    public DateTimeOffset? From { get; init; }
    public DateTimeOffset? To { get; init; }
    public string? Sort { get; init; }          // "total_desc" | "created_desc" | "created_asc"
}

public sealed record OrderFilter(OrderStatus? Status, string? Country,
                                 decimal? MinTotal, decimal? MaxTotal,
                                 DateTimeOffset? From, DateTimeOffset? To, OrderSort Sort);

public enum OrderSort { CreatedDesc, CreatedAsc, TotalDesc }

public static class OrderQueryMapper
{
    /// <summary>whitelist: أي قيمة sort غير معروفة ترجع للافتراضي بدل ما توصل للـSQL.</summary>
    public static OrderFilter ToFilter(this OrderListQuery q) => new(
        Status: Enum.TryParse<OrderStatus>(q.Status, true, out var s) ? s : null,
        Country: q.Country?.Trim().ToUpperInvariant() is { Length: 2 } c ? c : null,
        MinTotal: q.MinTotal,
        MaxTotal: q.MaxTotal,
        From: q.From,
        To: q.To,
        Sort: q.Sort?.ToLowerInvariant() switch
        {
            "total_desc"   => OrderSort.TotalDesc,
            "created_asc"  => OrderSort.CreatedAsc,
            _              => OrderSort.CreatedDesc,
        });
}

public static IQueryable<Order> ApplyFilter(this IQueryable<Order> q, OrderFilter f)
{
    if (f.Status is { } s)     q = q.Where(o => o.Status == s);
    if (f.Country is { } c)    q = q.Where(o => o.Customer.Country == c);
    if (f.MinTotal is { } min) q = q.Where(o => o.Total >= min);
    if (f.MaxTotal is { } max) q = q.Where(o => o.Total <= max);
    if (f.From is { } from)    q = q.Where(o => o.CreatedAt >= from);
    if (f.To is { } to)        q = q.Where(o => o.CreatedAt < to);

    return f.Sort switch
    {
        OrderSort.TotalDesc  => q.OrderByDescending(o => o.Total).ThenByDescending(o => o.Id),
        OrderSort.CreatedAsc => q.OrderBy(o => o.CreatedAt).ThenBy(o => o.Id),
        _                    => q.OrderByDescending(o => o.CreatedAt).ThenByDescending(o => o.Id),
    };
}
'''},
            {"type": "callout", "kind": "danger", "title": "لا تنفّذ فرزًا حرًا من العميل",
             "md": """
أنماط زي `?orderBy=Total desc, Customer.Email` بتتحوّل لـ**بناء تعبيرات ديناميكية** — ومكتبات زي
`System.Linq.Dynamic.Core` بتسمح بحقن أسماء أعمدة: تسريب بيانات (فرز على عمود حساس يكشف معلومات)،
أو استعلامات بلا فهرس تدمّر قاعدة البيانات.

القاعدة: **whitelist صريح** لكل حقل فرز وفلترة. لو العميل محتاج مرونة حقيقية، اعمل endpoint تقارير منفصل
بصلاحيات وحدود مختلفة.
"""},
            {"type": "code", "lang": "csharp", "title": "الاستجابة الكاملة: روابط تنقل ذاتية الوصف", "code": r'''
group.MapGet("/", async (
    [AsParameters] OrderListQuery query,
    AppDbContext db,
    CancellationToken ct) =>
{
    var page = await db.PageOrdersAsync(query.ToPageRequest(), query.ToFilter(), ct);

    return TypedResults.Ok(new OrdersPageResponse(
        Items: page.Items,
        Size: page.Size,
        Next: page.NextCursor is null ? null : $"/api/v2/orders?size={page.Size}&cursor={page.NextCursor}",
        // ملاحظة: مفيش total/count — COUNT(*) على جدول كبير مكلف. لو لازم، ارجعه تقريبيًا أو مخبأ.
    ));
}).Produces<OrdersPageResponse>();

public sealed record OrdersPageResponse(
    IReadOnlyList<OrderSummary> Items, int Size, string? Next);
'''},
            {"type": "checkpoints", "items": [
                "أقرر بين مجموعات إصدار يدوية وحزمة الإصدارات، وأعرف إيه اللي يستحق إصدار جديد فعلًا.",
                "أنفّذ cursor pagination بمفتاح مركّب وفهرس مناسب وصف زيادة.",
                "أبني عقد فلترة/فرز واحد بـwhitelist صريح.",
                "أتجنب `COUNT(*)` و`OFFSET` العميق في المسارات السخنة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه التغيير اللي يستوجب إصدار API جديد؟",
                 "options": [
                     "إضافة حقل جديد للاستجابة",
                     "تغيير نوع `total` من `decimal` إلى كائن `{amount, currency}`",
                     "إضافة مثال في الوثيقة",
                     "تحسين أداء استعلام داخلي",
                 ], "answer": 1,
                 "explain": "تغيير النوع/الحذف/إعادة التسمية كسر للعميل. الإضافة للاستجابة عادةً متوافقة رجعيًا لأن العملاء بيتجاهلوا الحقول غير المعروفة."},
                {"q": "ليه `Take(size + 1)` في cursor pagination؟",
                 "options": [
                     "لتحسين الأداء",
                     "لمعرفة هل فيه صفحة تالية بدون تنفيذ `COUNT(*)`",
                     "لتجنب الأخطاء",
                     "لتكرار الصف الأخير",
                 ], "answer": 1,
                 "explain": "لو رجّعنا أكثر من `size`، فيه المزيد → نبني `NextCursor`. ولو لا، `Next = null`. التكلفة صف واحد بدل عدّ الجدول كله."},
                {"q": "ليه `ThenByDescending(o => o.Id)` ضروري؟",
                 "options": [
                     "متطلب EF Core",
                     "بدون مكسّر تعادل فريد، الصفوف المتساوية في `CreatedAt` ممكن تتكرر أو تضيع بين الصفحات",
                     "للأمان",
                     "لتقليل حجم الاستجابة",
                 ], "answer": 1,
                 "explain": "الترتيب لازم يكون **كليًا** (total order). `CreatedAt` وحده مش فريد؛ `Id` بيكسر التعادل ويخلي الـcursor مستقرًا."},
                {"q": "عميل بعت `?sort=Customer.Email;DROP` — أنهي سلوك صح؟",
                 "options": [
                     "تمريره لـEF Core",
                     "whitelist: القيمة غير معروفة → ترجع للفرز الافتراضي (أو 400 صريح)",
                     "تجاهل كل الفلاتر",
                     "500",
                 ], "answer": 1,
                 "explain": "EF Core بيمرّر قيم معطاة كـparameters فالحقن المباشر مش سهل، لكن المشكلة الحقيقية هي **الفرز على أعمدة غير مقصودة** وتسريب المعلومات. الـwhitelist بيمنع ده."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "cursor pagination كامل",
                 "md": "نفّذ ترقيم cursor على أكبر جدول عندك مع فهرس مناسب، وصف زيادة، و`NextCursor` في الاستجابة. قِس الفرق مقابل `skip/take` عند العمق 10,000 (EXPLAIN ANALYZE أو stopwatch).",
                 "criteria": [
                     "فهرس مركّب على (created_at, id) موجود ومُستخدم فعليًا (شوف خطة التنفيذ)",
                     "التنقل عبر 5 صفحات متتالية بلا صفوف مكررة أو مفقودة (اختبار آلي)",
                     "قياس مسجل: زمن offset مقابل cursor عند العمق",
                     "`size` محدود بـ100 كحد أقصى",
                 ],
                 "hint": "لو الاختبار كشف تكرار: تأكد إن الـcursor بيحتوي **الاتنين** (الوقت والمعرّف) وإن شرط `WHERE` بيغطي حالة التعادل."},
                {"id": "t2", "title": "عقد فلترة موحّد",
                 "md": "ابنِ `OrderListQuery` بـ`[AsParameters]` وwhitelist للفرز، وطبّقه على endpoint قائمة. أضف اختبار integration يغطي: فلتر حالة + نطاق تاريخ + فرز غير معروف يرجع افتراضي.",
                 "criteria": [
                     "endpoint واحد يغطي كل حالات الفلترة (مش endpoint لكل حالة)",
                     "قيم الفرز المسموحة موثقة في OpenAPI",
                     "3 اختبارات على الأقل ناجحة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "ASP.NET Core API versioning", "url": "https://github.com/dotnet/aspnet-api-versioning"},
                {"label": "Pagination guidance", "url": "https://learn.microsoft.com/azure/architecture/best-practices/api-design"},
                {"label": "EF Core — query performance & indexes", "url": "https://learn.microsoft.com/ef/core/performance/"},
                {"label": "PostgreSQL EXPLAIN", "url": "https://www.postgresql.org/docs/current/using-explain.html"},
            ]},
        ],
    },
]
