"""Stage 2, Module 2 — Authentication & Authorization (lessons 1-3 of 5)."""

TODAY = "2026-10-22"

LESSONS_S2_B = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s2-m2-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
أكتر خطأ بيتكرر في مشاريع .NET إن الناس بتبدأ بالكود (JWT، Identity) قبل المفاهيم. النتيجة:
`[Authorize(Roles="admin")]` متناثرة في كل ملف، فحص ملكية المورد منسي (BOLA)، و401/403 مش متسقة.

الدرس ده **مفاهيم أولًا**: أنهي حاجة المصادقة وأنهي التفويض، إزاي ASP.NET Core بيمثّل الهوية
(`ClaimsPrincipal`)، وإزاي تبني **Policies** مركزية بدل فحوصات الأدوار المتناثرة — وبعدين فحص ملكية
المورد، وهو أكتر ثغرة عملية هتقابلك.
"""},
            {"type": "terms", "items": [
                {"term": "Authentication", "def": "مين إنت؟ إثبات الهوية (توكن، كوكي، مفتاح) وإنتاج `ClaimsPrincipal`."},
                {"term": "Authorization", "def": "ينفع تعمل كده؟ قرار مبني على الهوية + المورد + السياسة."},
                {"term": "Authentication Scheme", "def": "اسم آلية مصادقة (`Bearer`, `Cookies`, `Test`) وكل آلية لها Handler بيترجم الطلب لهوية."},
                {"term": "Claim", "def": "زوج (نوع، قيمة) عن المستخدم: `sub`, `email`, `role`, `country`."},
                {"term": "ClaimsPrincipal / ClaimsIdentity", "def": "الهوية النهائية على `HttpContext.User`. `Principal` ممكن يحتوي أكثر من `Identity`."},
                {"term": "Policy", "def": "قاعدة تفويض مسماة (`RequireRole`, `RequireClaim`, `RequireAssertion`, requirements مخصصة)."},
                {"term": "Resource-based authorization", "def": "قرار يعتمد على **المورد نفسه** (هل ده طلبي أنا؟) — مش بس على المستخدم."},
                {"term": "401 مقابل 403", "def": "401 = الهوية ناقصة/باطلة. 403 = الهوية معروفة لكن مفيش صلاحية."},
            ]},
            {"type": "heading", "level": 2, "text": "الـpipeline: الترتيب مش تفصيلة"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "الترتيب الصحيح — وأي خطأ فيه يسبب سلوكًا غامضًا", "code": r'''
var builder = WebApplication.CreateBuilder(args);

// 1) المصادقة: تسجيل الـhandlers
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer();                                   // التفاصيل في الدرس الجاي

// 2) التفويض: سياسات مركزية (مش فحوصات متناثرة)
builder.Services.AddAuthorizationBuilder()
    .AddPolicy(Policies.CustomerOrAdmin, p => p.RequireRole(Roles.Customer, Roles.Admin))
    .AddPolicy(Policies.AdminOnly,     p => p.RequireRole(Roles.Admin))
    .AddPolicy(Policies.SameCountry,   p => p.RequireClaim("country").RequireAuthenticatedUser())
    .AddPolicy(Policies.Support,       p => p.RequireAssertion(ctx =>
        ctx.User.HasClaim("department", "support") || ctx.User.IsInRole(Roles.Admin)));

builder.Services.AddHttpContextAccessor();             // لو محتاج CurrentUser abstraction
builder.Services.AddScoped<IAuthorizationHandler, OrderOwnerHandler>();

var app = builder.Build();

app.UseExceptionHandler(string.Empty);
app.UseSerilogRequestLogging();

app.UseAuthentication();      // ← يبني HttpContext.User من التوكن
app.UseAuthorization();       // ← يقيّم السياسات على الـendpoint المختار
// (في Minimal APIs التوجيه ضمني ويُستدعى أولًا تلقائيًا؛ لو استخدمت Controllers
//  فاكتب UseRouting() قبل الاثنين.)

app.MapOrdersApi();

app.Run();

public static class Policies
{
    public const string CustomerOrAdmin = "CustomerOrAdmin";
    public const string AdminOnly = "AdminOnly";
    public const string SameCountry = "SameCountry";
    public const string Support = "Support";
}

public static class Roles
{
    public const string Admin = "admin";
    public const string Customer = "customer";
    public const string Support = "support";
}
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء الترتيب الشائعة",
             "md": """
- `UseAuthorization()` **قبل** `UseAuthentication()` → كل الطلبات بتبقى مجهولة والسياسات تفشل بشكل محيّر.
- نسيان `UseAuthorization()` خالص → `[Authorize]` و`RequireAuthorization()` **ما بتتنفذش** (مفيش خطأ، مفيش حماية).
- استخدام `[Authorize(Roles = "admin")]` متناثر → تغيير دور واحد يتطلب بحث في كل الـrepo. السياسة المركزية اسم واحد.
- فحص الصلاحية **قبل** معرفة المورد (مثال: السماح بالقراءة ثم اكتشاف إن الطلب لعميل تاني) → BOLA.
"""},
            {"type": "heading", "level": 2, "text": "قراءة ClaimsPrincipal بشكل صحيح"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/CurrentUser.cs", "title": "تجريد واحد للهوية — الـDomain ما يعرفش Claims", "code": r'''
using System.Security.Claims;

/// <summary>اللي الـApplication layer محتاج معرفته عن المستخدم الحالي.</summary>
public interface ICurrentUser
{
    bool IsAuthenticated { get; }
    Guid? UserId { get; }
    string? Email { get; }
    string? Country { get; }
    IReadOnlyList<string> Roles { get; }
    bool HasPermission(string permission);
}

public sealed class CurrentUser(IHttpContextAccessor accessor) : ICurrentUser
{
    private ClaimsPrincipal User => accessor.HttpContext?.User ?? new ClaimsPrincipal();

    public bool IsAuthenticated => User.Identity?.IsAuthenticated == true;

    // ✗ الخطأ الشائع: ClaimTypes.NameIdentifier ثابتًا — الـIdP قد يرجّع "sub"
    // ✓ الحل: جرّب النوعين، وفشل بوضوح لو الاتنين غايبين
    public Guid? UserId =>
        TryGuid(JwtRegisteredClaimNames.Sub) ?? TryGuid(ClaimTypes.NameIdentifier);

    public string? Email => User.FindFirstValue(JwtRegisteredClaimNames.Email)
                         ?? User.FindFirstValue(ClaimTypes.Email);

    public string? Country => User.FindFirstValue("country");

    public IReadOnlyList<string> Roles =>
        User.FindAll(ClaimTypes.Role).Select(c => c.Value)
            .Concat(User.FindAll("role").Select(c => c.Value))
            .Distinct().ToArray();

    public bool HasPermission(string permission) =>
        User.HasClaim("permissions", permission);

    private Guid? TryGuid(string type) =>
        Guid.TryParse(User.FindFirstValue(type), out var id) ? id : null;
}

// الاستخدام في handler — نظيف، قابل للاختبار، بلا اعتماد على Claims في الـDomain
public sealed class OrderService(ICurrentUser user, IOrderRepository orders)
{
    public async Task<Order> GetAsync(Guid id, CancellationToken ct)
    {
        var order = await orders.GetAsync(id, ct) ?? throw new NotFoundException("Order", id);

        // ✓ فحص الملكية في مكان واحد، مش في كل endpoint
        if (order.CustomerId != user.UserId && !user.Roles.Contains(Roles.Admin))
            throw new ForbiddenException("Order", id);

        return order;
    }
}
'''},
            {"type": "heading", "level": 2, "text": "Resource-based authorization: سد ثغرة BOLA"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/OrderOwnerHandler.cs", "title": "سياسة بتفهم المورد نفسه", "code": r'''
using Microsoft.AspNetCore.Authorization;

public sealed record OrderOwnershipRequirement : IAuthorizationRequirement;

public sealed class OrderOwnerHandler(ICurrentUser user)
    : AuthorizationHandler<OrderOwnershipRequirement, Order>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context, OrderOwnershipRequirement requirement, Order order)
    {
        if (user.Roles.Contains(Roles.Admin))
        {
            context.Succeed(requirement);
            return Task.CompletedTask;
        }

        if (order.CustomerId == user.UserId)
            context.Succeed(requirement);
        else
            context.Fail();            // ✓ Fail صريح: يمنع handlers تانية من النجاح بالغلط

        return Task.CompletedTask;
    }
}

// في الـendpoint: الـresource authorization ما بيحصلش تلقائيًا في Minimal APIs
group.MapGet("/{id:guid}", async (Guid id, AppDbContext db, IAuthorizationService auth,
                                  HttpContext http, CancellationToken ct) =>
{
    var order = await db.Orders.AsNoTracking().SingleOrDefaultAsync(o => o.Id == id, ct);
    if (order is null) return TypedResults.NotFound(ProblemDetailsFactory.ForNotFound(id));

    // ← المورد نفسه بيدخل في القرار (مش بس الـclaims)
    var decision = await auth.AuthorizeAsync(http.User, order, "OrderOwner");
    if (!decision.Succeeded)
        return TypedResults.Json(ProblemDetailsFactory.ForForbidden(id), statusCode: 403);

    return TypedResults.Ok(OrderResponse.From(order));
}).RequireAuthorization(Policies.CustomerOrAdmin);   // الطبقة الأولى: دور صالح
'''},
            {"type": "callout", "kind": "danger", "title": "BOLA: الثغرة رقم 1 في APIs",
             "md": """
`GET /api/orders/123` بترجع الطلب 123 لأي مستخدم مسجّل — لأن الكود فحص **إن فيه مستخدم**،
مش **إن المورد بتاعه**. الاسم الرسمي: Broken Object Level Authorization.

القاعدة: **المعرّف اللي في الـbody أو الـquery ما يحددش الصلاحية**. هوية المستخدم من التوكن،
وفحص الملكية على **المورد المحمّل من قاعدة البيانات** (زي المثال أعلاه).
ولو عندك `customerId` في الطلب، تجاهله واعتمد على `user.UserId` — أو ارفض لو اختلفوا.
"""},
            {"type": "heading", "level": 2, "text": "إثراء الـClaims (بحدود)"},
            {"type": "code", "lang": "csharp", "title": "IClaimsTransformation — بيشتغل على كل طلب، فالكاش مش رفاهية", "code": r'''
public sealed class PermissionsClaimsTransformation(
    IPermissionStore permissions, TimeProvider time, IMemoryCache cache) : IClaimsTransformation
{
    public async Task<ClaimsPrincipal> TransformAsync(ClaimsPrincipal principal)
    {
        var id = principal.FindFirstValue(JwtRegisteredClaimNames.Sub);
        if (id is null) return principal;

        // ✓ بدوّن كاش: استعلام قاعدة بيانات لكل طلب (بما فيها الصور والـhealth checks)
        var list = await cache.GetOrCreateAsync($"perms:{id}", async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
            return await permissions.GetForUserAsync(Guid.Parse(id));
        }) ?? [];

        var identity = new ClaimsIdentity(list.Select(p => new Claim("permissions", p)), "Permissions");
        principal.AddIdentity(identity);
        return principal;
    }
}
'''},
            {"type": "table", "head": ["الطريقة", "الميزة", "التكلفة"], "rows": [
                ["Permissions داخل التوكن", "بلا استعلام وقت الطلب", "التوكن يكبر، والتغيير يتأخر لحد انتهاء صلاحيته"],
                ["`IClaimsTransformation` + كاش", "تحديث أسرع، توكن صغير", "استعلام/كاش لكل طلب — لازم تضبط الكاش"],
                ["فحص في الـservice من القاعدة مباشرة", "أدق وأحدث", "استعلام لكل عملية، وصعب توحيده"],
                ["نظام خارجي (OPA/Cerbos)", "سياسات مركزية عبر الخدمات", "تعقيد تشغيلي — للمشاريع الكبيرة فقط"],
            ]},
            {"type": "code", "lang": "csharp", "title": "401/403 بصيغة problem+json بدل الاستجابة الفاضية", "code": r'''
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        // ... إعدادات التحقق في الدرس القادم
        options.Events = new JwtBearerEvents
        {
            OnChallenge = ctx =>
            {
                ctx.HandleResponse();                       // أوقف الاستجابة الافتراضية الفاضية
                ctx.Response.StatusCode = StatusCodes.Status401Unauthorized;
                ctx.Response.ContentType = "application/problem+json";
                return ctx.Response.WriteAsJsonAsync(new ProblemDetails
                {
                    Status = 401,
                    Title = "غير مُصادَق",
                    Detail = string.IsNullOrEmpty(ctx.Error) ? "توكن ناقص أو منتهي أو غير صالح"
                                                             : $"{ctx.Error}: {ctx.ErrorDescription}",
                    Extensions = { ["traceId"] = ctx.HttpContext.TraceIdentifier },
                });
            },
            OnForbidden = ctx =>
            {
                ctx.Response.StatusCode = StatusCodes.Status403Forbidden;
                ctx.Response.ContentType = "application/problem+json";
                return ctx.Response.WriteAsJsonAsync(new ProblemDetails
                {
                    Status = 403,
                    Title = "ممنوع",
                    Detail = "هويتك معروفة، لكن الصلاحية غير كافية لهذا المورد.",
                    Extensions = { ["traceId"] = ctx.HttpContext.TraceIdentifier },
                });
            },
        };
    });
'''},
            {"type": "checkpoints", "items": [
                "أفرّق بين المصادقة والتفويض وأعرف مكان كل واحدة في الـpipeline.",
                "أقرأ `ClaimsPrincipal` عبر تجريد (`ICurrentUser`) وأتعامل مع اختلاف أنواع الـclaims.",
                "أعرّف سياسات مركزية بأسماء ثابتة بدل فحوصات أدوار متناثرة.",
                "أطبّق resource-based authorization لسد BOLA وأرجّع 401/403 بصيغة problem+json.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه الفرق الجوهري بين المصادقة والتفويض؟",
                 "options": [
                     "المصادقة للـAPIs والتفويض للويب",
                     "المصادقة تثبت الهوية، والتفويض يقرر الصلاحية بناءً عليها وعلى المورد",
                     "المصادقة أسرع",
                     "التفويض يحتاج قاعدة بيانات",
                 ], "answer": 1,
                 "explain": "ترتيبهم ثابت: مصادقة أولًا (مين إنت؟) ثم تفويض (ينفع؟). الخلط بينهم هو سبب أغلب فحوصات الصلاحية الناقصة."},
                {"q": "`UseAuthorization()` من غير `UseAuthentication()` — إيه النتيجة؟",
                 "options": [
                     "خطأ ترجمة",
                     "كل الطلبات تُعامَل كمجهولة والسياسات تفشل (401) حتى بتوكن صالح",
                     "الـAPI يشتغل بلا حماية",
                     "لا شيء",
                 ], "answer": 1,
                 "explain": "من غير handler يبني `HttpContext.User`، التفويض ما يلاقيش هوية. والعكس (بلا `UseAuthorization`) أخطر: الحماية ما بتتنفذش أصلًا."},
                {"q": "ليه `customerId` في جسم الطلب مصدر خطر؟",
                 "options": [
                     "بيكبر حجم الطلب",
                     "العميل يقدر يغيّره → BOLA؛ الصلاحية لازم تُشتق من التوكن وفحص ملكية المورد",
                     "بيبطئ الـbinding",
                     "بيكسر OpenAPI",
                 ], "answer": 1,
                 "explain": "أي بيانات صلاحية بيجيبها العميل قابلة للتزوير. اعتمد على `sub` في التوكن + فحص على المورد المحمّل."},
                {"q": "إمتى تستخدم `context.Fail()` بدل ترك القرار فاضي؟",
                 "options": [
                     "دائمًا",
                     "لما handler عندك متأكد من الرفض — عشان يمنع handlers تانية في نفس السياسة من النجاح",
                     "لما المستخدم admin",
                     "في الـmiddleware",
                 ], "answer": 1,
                 "explain": "`Fail()` قرار قاطع. من غيره، لو فيه أكثر من handler، واحد ممكن ينجح الطلب رغم رفضك."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "سياسات مركزية",
                 "md": "استبدل كل `[Authorize(Roles=…)]` / `RequireAuthorization(\"admin\")` المتناثرة بسياسات مسماة في `AddAuthorizationBuilder`، وطبّقها على الـendpoints. اكتب اختبار integration يثبت 401 (مجهول) و403 (دور ناقص) و200 (دور صالح) لكل endpoint محمي.",
                 "criteria": [
                     "لا يوجد فحص أدوار حرفي (`\"admin\"`) خارج ملف السياسات",
                     "3 اختبارات على الأقل (401/403/200) ناجحة لكل endpoint محمي رئيسي",
                     "الاستجابات بصيغة `application/problem+json` مع `traceId`",
                 ],
                 "hint": "لو الاختبارات بترجع 200 بدل 403: تأكد من `UseAuthorization()` موجود، ومن إن `TestAuthHandler` بيضيف الأدوار بـ`ClaimTypes.Role` **و**نفس الاسم اللي السياسة بتطلبه."},
                {"id": "t2", "title": "سد BOLA في مسار واحد",
                 "md": "اختار endpoint بيرجّع موردًا مملوكًا لمستخدم، وأضف فحص ملكية (resource-based). أثبت باختبار إن مستخدم A لا يقرأ مورد مستخدم B (403)، بينما admin يقرأه.",
                 "criteria": [
                     "الفحص على المورد المحمّل من القاعدة، مش على معرّف من الطلب",
                     "اختبار 403 لمستخدم تاني + اختبار 200 لـadmin",
                     "لا تسريب لوجود المورد: قرّر عمدًا بين 403 و404 ووثّق القرار",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Overview of ASP.NET Core authentication", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/"},
                {"label": "Authorization in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/security/authorization/introduction"},
                {"label": "Resource-based authorization", "url": "https://learn.microsoft.com/aspnet/core/security/authorization/resourcebased"},
                {"label": "Custom authorization handler", "url": "https://learn.microsoft.com/aspnet/core/security/authorization/policies"},
                {"label": "OWASP API Security Top 10", "url": "https://owasp.org/www-project-api-security/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s2-m2-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
JWT مش «طريقة تسجيل دخول» — ده **حامل claims موقّع** بصلاحيات قصيرة. أغلب الثغرات اللي بنشوفها في
تدقيقات الأمان مش في التشفير، دي في: مفاتيح متسربة، توكنات صلاحيتها طويلة، وrefresh tokens بلا تدوير
أو بلا كشف إعادة استخدام.

الدرس ده: إصدار وتحقق JWT بشكل سليم (مفاتيح غير متماثلة + تدوير تلقائي)، وrefresh token rotation
مع **كشف السرقة**، وتخزين المفاتيح بأمان.
"""},
            {"type": "terms", "items": [
                {"term": "Access Token", "def": "JWT قصير العمر (5-15 دقيقة) يحمل الهوية والصلاحيات. لا يمكن إبطاله قبل انتهاء صلاحيته."},
                {"term": "Refresh Token", "def": "سر طويل العمر (أيام/أسابيع) عشوائي ومعتم، يُستخدم لإصدار access token جديد."},
                {"term": "Token Rotation", "def": "كل استخدام لـrefresh token يُصدر بديلًا ويُبطِل القديم — فيتحول أي تسريب إلى نافذة صغيرة."},
                {"term": "Reuse Detection", "def": "لو قُدِّم refresh token مُستبدَل مرة تانية → سرقة محتملة → إبطال العائلة كلها."},
                {"term": "Token Family", "def": "سلسلة الإصدارات المتعاقبة من أول تسجيل دخول. إبطالها يقطع الطريق على المهاجم."},
                {"term": "JWKS", "def": "endpoint للمفاتيح العامة (`/.well-known/jwks.json`) — يخلي التحقق يدوّر المفاتيح تلقائيًا."},
                {"term": "Clock Skew", "def": "سماحية الفرق في الساعة. الافتراضي 5 دقائق — قلّلها لثوانٍ."},
                {"term": "Asymmetric Signing", "def": "RSA/ECDSA: المصدر يوقّع بالخاص، والمستهلكون يتحققون بالعام فقط (أأمن بكثير من المفتاح المشترك)."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Microsoft.AspNetCore.Authentication.JwtBearer
# لو إنت الـIdP وتحتاج إصدار التوكنات:
dotnet add Shop.Api package Microsoft.IdentityModel.JsonWebTokens
'''},
            {"type": "heading", "level": 2, "text": "1) التحقق: دع المكتبة تجلب المفاتيح وتدوّرها"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/JwtSetup.cs", "title": "الحالة الموصى بها: Authority + JWKS (تدوير مفاتيح تلقائي)", "code": r'''
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

public static class JwtSetup
{
    public static IServiceCollection AddJwtAuth(this IServiceCollection services, IConfiguration config)
    {
        var auth = config.GetSection("Auth").Get<AuthOptions>()
                   ?? throw new InvalidOperationException("قسم Auth ناقص في الإعدادات");

        services
            .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                // ✓ Authority: يجلب مستند OIDC + JWKS، ويحدّث المفاتيح عند التدوير بدون إعادة نشر
                options.Authority = auth.Authority;             // مثال: https://login.example.com/tenant
                options.Audience  = auth.Audience;              // مثال: shop-api
                options.RequireHttpsMetadata = true;            // لا تعطّلها إلا في تطوير محلي موثق

                // ✗ لا تضع MapInboundClaims = true (الافتراضي في بعض القوالب):
                //   بيعيد تسمية الـclaims ويخفي الشكل الحقيقي القادم من الـIdP
                options.MapInboundClaims = false;

                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer           = true,
                    ValidIssuer              = auth.Issuer,
                    ValidateAudience         = true,
                    ValidAudience            = auth.Audience,
                    ValidateLifetime         = true,
                    ValidateIssuerSigningKey = true,
                    ClockSkew                = TimeSpan.FromSeconds(30),   // ← مش 5 دقائق
                    NameClaimType            = "name",
                    RoleClaimType            = "role",
                };

                // لا تقبل إلا خوارزميات موقعة غير متماثلة
                options.TokenValidationParameters.ValidAlgorithms =
                    [SecurityAlgorithms.RsaSha256, SecurityAlgorithms.RsaSha384, SecurityAlgorithms.EcdsaSha256];

                options.Events = new JwtBearerEvents
                {
                    OnTokenValidated = ctx =>
                    {
                        // فرصة أخيرة لرفض توكن «صالح توقيعيًا» لكنه من عميل غير مرغوب
                        var azp = ctx.Principal?.FindFirstValue("azp");
                        if (azp is not null && !auth.AllowedClients.Contains(azp))
                        {
                            ctx.Fail($"client '{azp}' غير مسموح له");
                            return Task.CompletedTask;
                        }
                        return Task.CompletedTask;
                    },
                    OnAuthenticationFailed = ctx =>
                    {
                        // سجّل السبب الحقيقي (منتهي/توقيع/جمهور) — بيوفر ساعات تشخيص
                        ctx.HttpContext.Items["authError"] = ctx.Exception.GetType().Name;
                        return Task.CompletedTask;
                    },
                };
            });

        services.AddAuthorizationBuilder();
        return services;
    }
}

public sealed record AuthOptions
{
    public required string Authority { get; init; }
    public required string Audience { get; init; }
    public required string Issuer { get; init; }
    public IReadOnlySet<string> AllowedClients { get; init; } = new HashSet<string>();
}
'''},
            {"type": "callout", "kind": "danger", "title": "لو إنت بتصدر التوكنات بنفسك: أخطاء قاتلة",
             "md": """
- `ValidateIssuerSigningKey = false` → **أي مفتاح يُقبل**. ده أشهر خطأ في الأكواد المنسوخة.
- مفتاح متماثل (HMAC) في `appsettings.json` داخل الـrepo → أي قارئ للكود يقدر يزوّر توكنات للأبد.
- مفتاح أقصر من 256 بت → رفض/ضعف. لو HMAC فلازم ≥ 32 بايت عشوائية (وليس كلمة سر).
- `ValidateAudience = false` → توكن مصدور لخدمة تانية يشتغل عندك (token replay بين الخدمات).
- `ClockSkew` كبيرة + `Expires` طويل → نافذة إبطال معدومة.
- الاعتماد على `alg` من التوكن نفسه → ثبّت قائمة خوارزميات مقبولة صراحةً (زي الكود أعلاه).
"""},
            {"type": "heading", "level": 2, "text": "2) الإصدار: JsonWebTokenHandler + مفتاح غير متماثل"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/AccessTokenFactory.cs", "title": "إصدار توكن قصير العمر بمحتوى مقصود", "code": r'''
using System.Security.Cryptography;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;

public sealed class AccessTokenFactory(AuthTokenOptions options, TimeProvider time)
{
    private static readonly JsonWebTokenHandler Handler = new();   // الأحدث والأسرع من JwtSecurityTokenHandler
    private readonly RsaSecurityKey _signingKey = CreateSigningKey(options);

    public string Create(ApplicationUser user, IReadOnlyList<string> roles, IReadOnlyList<string> permissions)
    {
        var now = time.GetUtcNow();
        var subject = new ClaimsIdentity(
        [
            new Claim(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString("N")),  // معرّف فريد للإبطال/التدقيق
            new Claim(JwtRegisteredClaimNames.Email, user.Email ?? string.Empty),
            new Claim("name", user.FullName ?? string.Empty),
            new Claim("country", user.Country ?? string.Empty),
            .. roles.Select(r => new Claim("role", r)),
            .. permissions.Select(p => new Claim("permissions", p)),
        ]);

        var descriptor = new SecurityTokenDescriptor
        {
            Issuer = options.Issuer,
            Audience = options.Audience,
            Subject = subject,
            IssuedAt = now.UtcDateTime,
            NotBefore = now.UtcDateTime,
            Expires = now.Add(options.AccessTokenLifetime).UtcDateTime,   // 5-15 دقيقة
            SigningCredentials = new SigningCredentials(_signingKey, SecurityAlgorithms.RsaSha256),
        };

        return Handler.CreateToken(descriptor);
    }

    private static RsaSecurityKey CreateSigningKey(AuthTokenOptions options)
    {
        var rsa = RSA.Create();
        // المفتاح الخاص من Key Vault / user-secrets — ليس من ملف في الـrepo
        rsa.ImportFromPem(options.PrivateKeyPem);
        return new RsaSecurityKey(rsa) { KeyId = options.KeyId };   // KeyId يظهر في JWKS ورأس kid
    }
}

public sealed record AuthTokenOptions
{
    public required string Issuer { get; init; }
    public required string Audience { get; init; }
    public required string KeyId { get; init; }
    public required string PrivateKeyPem { get; init; }
    public TimeSpan AccessTokenLifetime { get; init; } = TimeSpan.FromMinutes(10);
}
'''},
            {"type": "callout", "kind": "warn", "title": "لا تضع أسرارًا في التوكن",
             "md": """
الـJWT **مشفّر بترميز base64url، مش مُعمّى** — أي حد بياخده يقدر يفكّه ويقرأ كل الـclaims.
حط فيه: معرّفات، أدوار، صلاحيات، بلد. **لا تحط**: كلمة سر، رقم بطاقة، عنوان تفصيلي، بيانات صحية،
أو أي حاجة تخالف GDPR/خصوصية. وقلّل الحجم: كل claim بيتبعت في **كل** طلب.
"""},
            {"type": "heading", "level": 2, "text": "3) Refresh Token Rotation مع كشف إعادة الاستخدام"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/RefreshToken.cs", "title": "النموذج: hash فقط + family + علامة استبدال", "code": r'''
public sealed class RefreshToken
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public required Guid UserId { get; init; }

    /// <summary>سلسلة الإصدارات: كل تدوير يحتفظ بنفس الـfamily — أساس كشف السرقة.</summary>
    public required Guid FamilyId { get; init; }

    /// <summary>SHA-256 للتوكن. ✗ لا تخزن التوكن الخام — لو القاعدة اتسربت، الجلسات اتسرقت.</summary>
    public required string TokenHash { get; init; }

    public required DateTimeOffset CreatedAt { get; init; }
    public required DateTimeOffset ExpiresAt { get; init; }

    /// <summary>null = التوكن الحالي صالح. غير null = استُبدل (استخدامه تاني = سرقة محتملة).</summary>
    public Guid? ReplacedById { get; init; }
    public string? RevokedReason { get; init; }

    public string? CreatedByIp { get; init; }
    public string? UserAgent { get; init; }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Auth/TokenRotationService.cs", "title": "التدوير + كشف إعادة الاستخدام + إبطال العائلة", "code": r'''
using System.Security.Cryptography;

public sealed class TokenRotationService(
    AppDbContext db, AccessTokenFactory accessTokens, UserManager<ApplicationUser> users,
    TimeProvider time, ILogger<TokenRotationService> log, AuthOptions options)
{
    private static readonly TimeSpan RefreshLifetime = TimeSpan.FromDays(14);
    private static readonly TimeSpan AbsoluteSessionLimit = TimeSpan.FromDays(30);

    /// <summary>أول إصدار بعد تسجيل الدخول: يبدأ عائلة جديدة.</summary>
    public async Task<TokenPair> IssueAsync(ApplicationUser user, string ip, string? agent, CancellationToken ct)
    {
        var family = Guid.NewGuid();
        return await CreatePairAsync(user, family, previous: null, ip, agent, ct);
    }

    public async Task<TokenPairResult> RotateAsync(string presented, string ip, CancellationToken ct)
    {
        var hash = Hash(presented);
        var now = time.GetUtcNow();

        var stored = await db.RefreshTokens.AsTracking()
            .SingleOrDefaultAsync(t => t.TokenHash == hash, ct);

        if (stored is null)
            return TokenPairResult.Fail("invalid_grant", "توكن غير معروف");

        if (stored.RevokedReason is not null)
            return TokenPairResult.Fail("invalid_grant", "توكن مُبطَل");

        // ★ الحالة الأخطر: توكن استُبدل بالفعل وبيتقدّم تاني
        if (stored.ReplacedById is not null)
        {
            log.LogWarning(
                "refresh token reuse detected user={UserId} family={Family} ip={Ip} — revoking family",
                stored.UserId, stored.FamilyId, ip);

            await RevokeFamilyAsync(stored.FamilyId, "reuse_detected", ct);
            return TokenPairResult.Fail("invalid_grant", "تم رصد استخدام غير طبيعي؛ أعد تسجيل الدخول");
        }

        if (stored.ExpiresAt <= now)
            return TokenPairResult.Fail("invalid_grant", "توكن منتهي");

        var user = await users.FindByIdAsync(stored.UserId.ToString());
        if (user is null || await users.IsLockedOutAsync(user))
            return TokenPairResult.Fail("invalid_grant", "الحساب غير متاح");

        // حد جلسة مطلق: منعيدش التدوير للأبد
        if (now - stored.CreatedAt > AbsoluteSessionLimit)
            return TokenPairResult.Fail("invalid_grant", "انتهت مدة الجلسة القصوى");

        var pair = await CreatePairAsync(user, stored.FamilyId, stored, ip, stored.UserAgent, ct);
        return TokenPairResult.Ok(pair);
    }

    private async Task<TokenPair> CreatePairAsync(
        ApplicationUser user, Guid family, RefreshToken? previous,
        string ip, string? agent, CancellationToken ct)
    {
        var raw = Convert.ToHexString(RandomNumberGenerator.GetBytes(48));   // عشوائي قوي، مش JWT

        var next = new RefreshToken
        {
            UserId = user.Id,
            FamilyId = family,
            TokenHash = Hash(raw),
            CreatedAt = time.GetUtcNow(),
            ExpiresAt = time.GetUtcNow().Add(RefreshLifetime),
            CreatedByIp = ip,
            UserAgent = agent,
        };

        db.RefreshTokens.Add(next);
        if (previous is not null)
            db.Entry(previous).CurrentValues[nameof(RefreshToken.ReplacedById)] = next.Id;

        await db.SaveChangesAsync(ct);

        var roles = await users.GetRolesAsync(user);
        var access = accessTokens.Create(user, [.. roles], await Permissions.ForAsync(user.Id, ct));

        return new TokenPair(access, raw, (int)TimeSpan.FromMinutes(10).TotalSeconds,
                             (int)RefreshLifetime.TotalSeconds);
    }

    public async Task RevokeFamilyAsync(Guid family, string reason, CancellationToken ct)
    {
        await db.RefreshTokens
            .Where(t => t.FamilyId == family && t.RevokedReason == null)
            .ExecuteUpdateAsync(s => s.SetProperty(t => t.RevokedReason, reason), ct);
    }

    public async Task RevokeAllForUserAsync(Guid userId, string reason, CancellationToken ct) =>
        await db.RefreshTokens
            .Where(t => t.UserId == userId && t.RevokedReason == null)
            .ExecuteUpdateAsync(s => s.SetProperty(t => t.RevokedReason, reason), ct);

    private static string Hash(string raw) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(raw)));
}

public sealed record TokenPair(string AccessToken, string RefreshToken, int ExpiresIn, int RefreshExpiresIn);
public sealed record TokenPairResult(bool Succeeded, TokenPair? Pair, string? Error, string? Description)
{
    public static TokenPairResult Ok(TokenPair p) => new(true, p, null, null);
    public static TokenPairResult Fail(string e, string d) => new(false, null, e, d);
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Auth/AuthEndpoints.cs", "title": "الـendpoints: refresh ككوكي HttpOnly (الخيار الآمن للويب)", "code": r'''
public static IEndpointRouteBuilder MapAuthApi(this IEndpointRouteBuilder app)
{
    var group = app.MapGroup("/api/auth").WithTags("Auth");

    group.MapPost("/login", async (
        LoginRequest request, HttpContext http, SignInManager<ApplicationUser> signIn,
        TokenRotationService tokens, CancellationToken ct) =>
    {
        var user = await signIn.UserManager.FindByEmailAsync(request.Email);
        var result = user is null
            ? SignInResult.Failed                                   // لا تكشف إن الإيميل موجود
            : await signIn.CheckPasswordSignInAsync(user, request.Password, lockoutOnFailure: true);

        if (!result.Succeeded)
            return TypedResults.Json(new ProblemDetails
            {
                Status = 401, Title = "بيانات الدخول غير صحيحة",
                Extensions = { ["traceId"] = http.TraceIdentifier },
            }, statusCode: 401);

        if (result.IsLockedOut)
            return TypedResults.Json(new ProblemDetails
            {
                Status = 423, Title = "الحساب مقفل مؤقتًا",
                Detail = "جرّب بعد دقائق أو استخدم استعادة الوصول.",
            }, statusCode: 423);

        var pair = await tokens.IssueAsync(user!, http.Connection.RemoteIpAddress?.ToString() ?? "?",
                                           http.Request.Headers.UserAgent, ct);

        SetRefreshCookie(http, pair.RefreshToken, pair.RefreshExpiresIn);
        return TypedResults.Ok(new LoginResponse(pair.AccessToken, pair.ExpiresIn));
    }).RequireRateLimiting("auth");                                 // ← مهم: منع تخمين كلمات السر

    group.MapPost("/refresh", async (HttpContext http, TokenRotationService tokens, CancellationToken ct) =>
    {
        var presented = http.Request.Cookies["refresh_token"];
        if (string.IsNullOrEmpty(presented))
            return TypedResults.Unauthorized();

        var result = await tokens.RotateAsync(presented,
            http.Connection.RemoteIpAddress?.ToString() ?? "?", ct);

        if (!result.Succeeded)
        {
            http.Response.Cookies.Delete("refresh_token", CookieOptions());   // نظّف الكوكي
            return TypedResults.Json(new ProblemDetails
            {
                Status = 401, Title = "تعذّر تجديد الجلسة", Detail = result.Description,
            }, statusCode: 401);
        }

        SetRefreshCookie(http, result.Pair!.RefreshToken, result.Pair.RefreshExpiresIn);
        return TypedResults.Ok(new LoginResponse(result.Pair.AccessToken, result.Pair.ExpiresIn));
    }).RequireRateLimiting("auth");

    group.MapPost("/logout", async (HttpContext http, TokenRotationService tokens,
                                    ICurrentUser user, CancellationToken ct) =>
    {
        if (user.UserId is { } id)
            await tokens.RevokeAllForUserAsync(id, "logout", ct);
        http.Response.Cookies.Delete("refresh_token", CookieOptions());
        return TypedResults.NoContent();
    }).RequireAuthorization();

    return app;
}

private static void SetRefreshCookie(HttpContext http, string token, int maxAge) =>
    http.Response.Cookies.Append("refresh_token", token, new CookieOptions
    {
        HttpOnly = true,                       // ← JavaScript ما يقدرش يقرأه (حماية من XSS)
        Secure = true,                         // HTTPS فقط
        SameSite = SameSiteMode.Strict,        // حماية من CSRF
        Path = "/api/auth",                    // ← يُرسل لمسارات المصادقة فقط
        MaxAge = TimeSpan.FromSeconds(maxAge),
    });

private static CookieOptions CookieOptions() => new() { Path = "/api/auth", Secure = true, HttpOnly = true };
'''},
            {"type": "heading", "level": 2, "text": "4) تخزين المفاتيح والتوكنات على العميل"},
            {"type": "table", "head": ["نوع العميل", "أفضل نمط", "ليه"], "rows": [
                ["SPA (React/Angular) مع API", "BFF: كوكي HttpOnly للـrefresh + الـaccess token في الذاكرة", "لا يصل JS لأي توكن طويل العمر → XSS ما يسرقش الجلسة"],
                ["SPA بدون BFF", "access token في الذاكرة فقط + refresh في كوكي HttpOnly", "حل وسط مقبول؛ تجنّب localStorage إطلاقًا"],
                ["Mobile (MAUI/native)", "Keychain/Keystore عبر مكتبة آمنة", "تخزين مشفّر من النظام"],
                ["CLI / أداة سطر أوامر", "Device Code flow + تخزين في credential manager", "بلا متصفح مدمج وبلا secret في الكود"],
                ["خدمة إلى خدمة", "Client Credentials (OAuth2) — بلا refresh token", "مفيش مستخدم أصلًا"],
                ["تخزين في localStorage", "✗ لا", "أي XSS = سرقة كاملة للجلسة"],
            ]},
            {"type": "code", "lang": "csharp", "title": "المفاتيح: من Key Vault بـManaged Identity (بلا سر في الكود)", "code": r'''
// Program.cs
var config = builder.Configuration;

if (builder.Environment.IsProduction())
{
    var vaultUrl = config["KeyVault:Url"]
        ?? throw new InvalidOperationException("KeyVault:Url مطلوب في الإنتاج");
    // Managed Identity: لا يوجد client secret ولا connection string في الكود أو الإعدادات
    config.AddAzureKeyVault(new Uri(vaultUrl), new DefaultAzureCredential());
}

builder.Services.Configure<AuthTokenOptions>(config.GetSection("AuthToken"));
// AuthToken:PrivateKeyPem و AuthToken:KeyId يجيئان من Key Vault
'''},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "التطوير المحلي: user-secrets (مش appsettings.json)", "code": r'''
dotnet user-secrets init --project Shop.Api
dotnet user-secrets set "AuthToken:KeyId" "dev-key-2026-10" --project Shop.Api
dotnet user-secrets set "AuthToken:PrivateKeyPem" "$(cat ./dev-key.pem)" --project Shop.Api

# تأكد إن الملف مش في الـrepo
grep -rn "PRIVATE KEY" --include="*.json" --include="*.cs" . || echo "clean ✅"
'''},
            {"type": "callout", "kind": "note", "title": "تدوير المفاتيح بدون downtime",
             "md": """
1. أنشئ مفتاحًا جديدًا بـ`KeyId` مختلف وانشره في JWKS (المفتاحان موجودان معًا).
2. ابدأ التوقيع بالمفتاح الجديد. التوكنات القديمة لسه بتتحقق بالقديم (عن طريق `kid`).
3. بعد انتهاء عمر أقصى توكن مصدر + سماحية، احذف القديم من JWKS.

مع `options.Authority` في الـJwtBearer، الخطوات دي بتحصل **تلقائيًا** على جانب المستهلك —
وده أقوى حجة لعدم إدارة المفاتيح يدويًا في كل خدمة.
"""},
            {"type": "checkpoints", "items": [
                "أضبط JwtBearer بـAuthority/JWKS وأفعّل كل عناصر التحقق مع ClockSkew صغير.",
                "أصدر access token قصير العمر بمفتاح غير متماثل وclaims مقصودة.",
                "أنفّذ refresh token rotation مع hash للتخزين وكشف إعادة الاستخدام وإبطال العائلة.",
                "أخزن المفاتيح في Key Vault/user-secrets وأختار نمط تخزين توكنات مناسب لكل عميل.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه access token ما ينفعش يُبطَل مباشرة؟ وإيه الحل العملي؟",
                 "options": [
                     "يُبطَل بحذفه من قاعدة البيانات",
                     "لأنه stateless وموقّع؛ الحل: عمر قصير + إبطال الـrefresh tokens + deny-list للحالات الطارئة",
                     "يُبطَل بإعادة إصداره",
                     "يُبطَل بتغيير الجمهور",
                 ], "answer": 1,
                 "explain": "التوكن صالح حتى انتهاء صلاحيته عند أي خدمة تتحقق منه. تقصير العمر (5-15 دقيقة) هو الآلية الأساسية، وإبطال الـrefresh بيقطع التجديد."},
                {"q": "توكن refresh مُستبدَل اتقدّم تاني. أنهي تصرف صح؟",
                 "options": [
                     "أصدر زوجًا جديدًا عادي",
                     "ارفض واعتبرها سرقة محتملة: أبطل العائلة كلها وسجّل تحذيرًا",
                     "أرجع 500",
                     "أجدد الـexpires",
                 ], "answer": 1,
                 "explain": "ده بالظبط هدف rotation: التوكن المسروق إما يُستخدم من المهاجم أو من المستخدم الشرعي — التاني هيظهر كـreuse فتنكشف السرقة."},
                {"q": "ليه نخزن hash للـrefresh token مش التوكن نفسه؟",
                 "options": [
                     "لتقليل الحجم",
                     "لو قاعدة البيانات اتسربت، المهاجم ما يحصلش على توكنات صالحة للاستخدام",
                     "لأن الـhash أسرع في البحث",
                     "متطلب من ASP.NET Core",
                 ], "answer": 1,
                 "explain": "نفس منطق عدم تخزين كلمات السر. البحث بـhash محسوب من التوكن المقدَّم — سريع وآمن."},
                {"q": "SPA بيخزن الـaccess token في localStorage. إيه الخطر؟",
                 "options": [
                     "بطء القراءة",
                     "أي ثغرة XSS تقرأ التوكن وتبعته لأي مكان — الجلسة بتتسرق بالكامل",
                     "مشكلة في CSRF",
                     "تعارض مع CORS",
                 ], "answer": 1,
                 "explain": "الحل: BFF بكوكي HttpOnly للـrefresh، والـaccess token في الذاكرة فقط (يُفقد عند إعادة التحميل ويُستعاد بـ/refresh)."},
                {"q": "مفتاح HMAC مشترك بين 6 خدمات. إيه المشكلة؟",
                 "options": [
                     "أبطأ",
                     "أي خدمة مخترقة تقدر تزوّر توكنات لكل الخدمات؛ مع RSA/ECDSA المستهلك يحتاج المفتاح العام فقط",
                     "التوكن أكبر",
                     "لا توجد مشكلة",
                 ], "answer": 1,
                 "explain": "المفتاح المتماثل سر مشترك = سطح هجوم مشترك. غير المتماثل بيفصل القدرة على الإصدار عن القدرة على التحقق."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "دورة توكنات كاملة",
                 "md": "نفّذ `/api/auth/login` و`/refresh` و`/logout` مع rotation وhash للعائلة وكشف إعادة الاستخدام، والـrefresh في كوكي HttpOnly بـ`Path=/api/auth`. اكتب اختبارات integration للدورة كلها.",
                 "criteria": [
                     "login ناجح → access token + كوكي refresh، وفاشل → 401 problem+json بلا كشف لوجود الحساب",
                     "refresh يستبدل التوكن ويبطل السابق",
                     "إعادة استخدام توكن مستبدل → 401 + إبطال كل توكنات العائلة (اختبار يثبت إن توكن تالت من نفس العائلة بقى مرفوض)",
                     "logout يبطل كل توكنات المستخدم",
                     "لا يوجد توكن خام مخزن في القاعدة (تحقق بفحص العمود)",
                 ],
                 "hint": "لو اختبار الـreuse بيفشل: تأكد إنك بتحمّل الـtoken بـ`AsTracking()` وبتحفظ `ReplacedById` في نفس `SaveChanges`، وإن الـendpoints بتقرأ الكوكي من `Path=/api/auth` (كوكي بمسار تاني مش هيتبعت)."},
                {"id": "t2", "title": "تدقيق إعدادات التحقق",
                 "md": "راجع `TokenValidationParameters` في مشروعك وسجّل في ملاحظات الدرس: حالة كل `Validate*`، قيمة `ClockSkew`، الخوارزميات المقبولة، ومصدر المفتاح. أصلح أي بند ضعيف وأضف اختبارًا يفشل لو اتغير.",
                 "criteria": [
                     "كل عناصر التحقق مفعّلة وموثقة",
                     "`ClockSkew` ≤ 60 ثانية",
                     "قائمة خوارزميات مقبولة صريحة (لا `none` ولا خوارزميات متماثلة غير مقصودة)",
                     "اختبار يرفض توكن منتهي + توكن بجمهور خاطئ + توكن بتوقيع خاطئ",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "JWT Bearer authentication", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/jwt"},
                {"label": "TokenValidationParameters", "url": "https://learn.microsoft.com/dotnet/api/microsoft.identitymodel.tokens.tokenvalidationparameters"},
                {"label": "OAuth 2.0 Security BCP (RFC 9700)", "url": "https://www.rfc-editor.org/rfc/rfc9700"},
                {"label": "OAuth 2.1 draft (PKCE إلزامي)", "url": "https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1"},
                {"label": "Key Vault configuration provider", "url": "https://learn.microsoft.com/azure/key-vault/general/configuration-provider"},
                {"label": "OWASP Authentication Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l3
    {
        "id": "s2-m2-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
ASP.NET Core Identity بتحل مشكلات ماينفعش ترتجل فيها: تخزين كلمة السر (PBKDF2/Argon2)،
lockout بعد محاولات فاشلة، 2FA بـTOTP، تأكيد الإيميل، recovery codes. الخطأ الشائع إنك إما
تعيد اختراعها (خطر أمني) أو تسيبها تتسرب لجوالة الـDomain (تشابك معماري).

الدرس ده: دمج Identity مع API وEF Core، ضبط السياسات (كلمات السر، القفل، 2FA)، وفصلها عن الـDomain.
"""},
            {"type": "terms", "items": [
                {"term": "`AddIdentityCore<TUser>`", "def": "النسخة المخصصة للـAPIs: بلا كوكيز ولا صفحات — أنت تتحكم في الاستجابات."},
                {"term": "`SignInManager<TUser>`", "def": "إدارة جلسات الدخول (كوكيز/توكنات) والتحقق من كلمة السر مع lockout."},
                {"term": "`UserManager<TUser>`", "def": "CRUD للمستخدمين + الأدوار + التوكنات الخاصة (تأكيد إيميل، 2FA، تغيير كلمة السر)."},
                {"term": "Password Hasher", "def": "خوارزمية اشتقاق مفتاح مبطّئة عمدًا (PBKDF2 افتراضيًا) مع salt لكل مستخدم وترقية تلقائية للصيغة."},
                {"term": "Lockout", "def": "قفل مؤقت بعد N محاولات فاشلة — أهم دفاع ضد تخمين كلمات السر."},
                {"term": "TOTP 2FA", "def": "كلمة سر لمرة واحدة كل 30 ثانية من تطبيق authenticator (Google/Microsoft Authenticator)."},
                {"term": "Recovery Codes", "def": "رموز بديلة لمرة واحدة لو فقد المستخدم جهاز الـ2FA."},
                {"term": "Security Stamp", "def": "قيمة تتغير عند أحداث حساسة → إبطال كل الجلسات/التوكنات القديمة."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Microsoft.AspNetCore.Identity.EntityFrameworkCore
dotnet add Shop.Api package Microsoft.Extensions.Identity.Stores
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Identity/ApplicationUser.cs", "title": "المستخدم + DbContext الخاص بالـIdentity", "code": r'''
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;

/// <summary>Guid بدل string: فهارس أصغر وعلاقات أوضح.</summary>
public sealed class ApplicationUser : IdentityUser<Guid>
{
    public string? FullName { get; set; }
    public string? Country { get; set; }
    public DateTimeOffset CreatedAt { get; set; }

    /// <summary>ربط صريح بمفهوم الـDomain — الـDomain لا يعرف ApplicationUser.</summary>
    public Guid? CustomerId { get; set; }
}

public sealed class AppIdentityDbContext(DbContextOptions<AppIdentityDbContext> options)
    : IdentityDbContext<ApplicationUser, IdentityRole<Guid>, Guid>(options)
{
    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        builder.Entity<ApplicationUser>(e =>
        {
            e.ToTable("identity_users");
            e.HasIndex(u => u.Country);
            e.HasIndex(u => u.CustomerId).IsUnique();
            e.Property(u => u.FullName).HasMaxLength(200);
        });
        builder.Entity<IdentityRole<Guid>>().ToTable("identity_roles");
        // بقية جداول Identity (logins, tokens, claims, role claims) — سمّها بـprefix واضح
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Identity/IdentitySetup.cs", "title": "الإعداد: سياسات صريحة بدل الافتراضيات", "code": r'''
public static IServiceCollection AddIdentityForApi(
    this IServiceCollection services, IConfiguration config)
{
    services.AddDbContext<AppIdentityDbContext>(o =>
        o.UseNpgsql(config.GetConnectionString("Identity"), npgsql => npgsql.EnableRetryOnFailure()));

    services
        .AddIdentityCore<ApplicationUser>(options =>
        {
            // ── كلمة السر: الطول أهم من التعقيد (توصية NIST 800-63B)
            options.Password.RequiredLength = 12;
            options.Password.RequireDigit = false;
            options.Password.RequireLowercase = false;
            options.Password.RequireUppercase = false;
            options.Password.RequireNonAlphanumeric = false;
            options.Password.RequiredUniqueChars = 4;

            // ── القفل: أهم دفاع ضد التخمين
            options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
            options.Lockout.MaxFailedAccessAttempts = 5;
            options.Lockout.AllowedForNewUsers = true;

            // ── المستخدم
            options.User.RequireUniqueEmail = true;
            options.User.AllowedUserNameCharacters =
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-";

            // ── 2FA
            options.SignIn.RequireConfirmedEmail = false;     // فعّلها لو عندك بريد موثوق
            options.Tokens.AuthenticatorTokenProvider = TokenOptions.DefaultAuthenticatorProvider;
            options.Tokens.PasswordResetTokenProvider = TokenOptions.DefaultEmailProvider;
        })
        .AddRoles<IdentityRole<Guid>>()
        .AddEntityFrameworkStores<AppIdentityDbContext>()
        .AddSignInManager()
        .AddTokenProvider<DataProtectorTokenProvider<ApplicationUser>>(TokenOptions.DefaultProvider)
        .AddDefaultTokenProviders();

    // مدقق كلمة السر المخصص: ارفض الكلمات المسربة والشائعة
    services.AddScoped<IPasswordValidator<ApplicationUser>, BreachedPasswordValidator>();
    services.AddScoped<IUserValidator<ApplicationUser>, NormalizedEmailValidator>();

    // توزيع صلاحيات الـIdentity: لا تمنح UserManager لـController/endpoint مباشرة
    services.AddScoped<IUserAccounts, IdentityUserAccounts>();

    return services;
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Identity/BreachedPasswordValidator.cs", "title": "مدقق مخصص: كلمات السر الشائعة/المسربة", "code": r'''
using Microsoft.AspNetCore.Identity;

/// <summary>
/// يفحص كلمة السر مقابل قائمة كلمات شائعة (ويفضل خدمة k-anonymity مثل HIBP في الإنتاج).
/// قائمة الـ10k الأكثر شيوعًا تمنع أغلب الهجمات الحقيقية بتكلفة صفر.
/// </summary>
public sealed class BreachedPasswordValidator(ICommonPasswordStore passwords)
    : IPasswordValidator<ApplicationUser>
{
    public async Task<IdentityResult> ValidateAsync(
        UserManager<ApplicationUser> manager, ApplicationUser user, string? password)
    {
        if (string.IsNullOrWhiteSpace(password))
            return IdentityResult.Failed(new IdentityError { Code = "EmptyPassword", Description = "كلمة السر مطلوبة" });

        if (password.Length < 12)
            return IdentityResult.Failed(new IdentityError
            {
                Code = "PasswordTooShort", Description = "كلمة السر يجب ألا تقل عن 12 حرفًا",
            });

        if (await passwords.IsCommonAsync(password))
            return IdentityResult.Failed(new IdentityError
            {
                Code = "PasswordCommon", Description = "كلمة السر مستخدمة بكثرة؛ اختر عبارة مرور أطول",
            });

        // لا تسمح بأن تكون مشتقة من بيانات الحساب (إيميل/اسم)
        var email = user.Email ?? string.Empty;
        if (email.Length > 3 && password.Contains(email.Split('@')[0], StringComparison.OrdinalIgnoreCase))
            return IdentityResult.Failed(new IdentityError
            {
                Code = "PasswordContainsEmail", Description = "لا تستخدم جزءًا من بريدك في كلمة السر",
            });

        return IdentityResult.Success;
    }
}
'''},
            {"type": "heading", "level": 2, "text": "APIs فوق Identity: اترجم الأخطاء لعقدك"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Auth/AccountsEndpoints.cs", "title": "تسجيل + أخطاء problem+json موحدة", "code": r'''
public static IEndpointRouteBuilder MapAccountsApi(this IEndpointRouteBuilder app)
{
    var group = app.MapGroup("/api/accounts").WithTags("Accounts");

    group.MapPost("/register", async (
        RegisterRequest request, IUserAccounts accounts, HttpContext http, CancellationToken ct) =>
    {
        var result = await accounts.RegisterAsync(request, ct);

        if (!result.Succeeded)
            return TypedResults.Json(new ValidationProblemDetails(result.ErrorsByField)
            {
                Status = 400, Title = "تعذّر إنشاء الحساب",
                Extensions = { ["traceId"] = http.TraceIdentifier },
            }, statusCode: 400);

        return TypedResults.Created($"/api/accounts/{result.UserId}", new AccountCreatedResponse(result.UserId));
    }).RequireRateLimiting("auth").AllowAnonymous();

    group.MapPost("/{id:guid}/email/confirm", async (
        Guid id, ConfirmEmailRequest request, IUserAccounts accounts, CancellationToken ct) =>
        await accounts.ConfirmEmailAsync(id, request.Token, ct)
            ? TypedResults.NoContent()
            : TypedResults.BadRequest(new ProblemDetails { Status = 400, Title = "رابط التأكيد غير صالح" }));

    group.MapPost("/password/forgot", async (ForgotPasswordRequest r, IUserAccounts accounts, CancellationToken ct) =>
    {
        // ✓ استجابة واحدة مهما كانت النتيجة: لا تكشف إن الإيميل مسجل
        await accounts.SendPasswordResetAsync(r.Email, ct);
        return TypedResults.Accepted();
    }).RequireRateLimiting("auth").AllowAnonymous();

    return app;
}

/// <summary>غلاف فوق UserManager: يترجم أخطاء Identity لعقدنا ويمنع تسريبها للطبقات العليا.</summary>
public sealed class IdentityUserAccounts(
    UserManager<ApplicationUser> users, RoleManager<IdentityRole<Guid>> roles,
    ILogger<IdentityUserAccounts> log) : IUserAccounts
{
    public async Task<AccountResult> RegisterAsync(RegisterRequest request, CancellationToken ct)
    {
        var user = new ApplicationUser
        {
            UserName = request.Email,           // Identity يتطلب UserName
            Email = request.Email,
            FullName = request.FullName,
            Country = request.Country,
            CreatedAt = DateTimeOffset.UtcNow,
        };

        var result = await users.CreateAsync(user, request.Password);
        if (!result.Succeeded)
            return AccountResult.Failed(MapErrors(result));

        await users.AddToRoleAsync(user, Roles.Customer);
        log.LogInformation("account created user={UserId}", user.Id);

        return AccountResult.Ok(user.Id);
    }

    /// <summary>ترجمة رموز Identity لرسائل مفهومة ومجمّعة حسب الحقل.</summary>
    private static Dictionary<string, string[]> MapErrors(IdentityResult result)
    {
        var map = new Dictionary<string, List<string>>();
        foreach (var e in result.Errors)
        {
            var field = e.Code switch
            {
                "PasswordTooShort" or "PasswordRequiresUniqueChars" or "PasswordCommon" => "password",
                "InvalidEmail" or "DuplicateEmail" => "email",
                "DuplicateUserName" => "email",
                _ => "",
            };
            if (!map.TryGetValue(field, out var list)) map[field] = list = [];
            list.Add(Describe(e));
        }
        return map.ToDictionary(kv => kv.Key, kv => kv.Value.ToArray());
    }

    private static string Describe(IdentityError e) => e.Code switch
    {
        "PasswordTooShort" => "كلمة السر قصيرة جدًا (12 حرفًا على الأقل)",
        "PasswordRequiresUniqueChars" => "كلمة السر تحتاج أحرفًا مختلفة أكثر",
        "DuplicateEmail" => "البريد مسجل بالفعل",
        "InvalidEmail" => "صيغة البريد غير صحيحة",
        _ => "تعذّر إتمام العملية",                       // لا تسرّب تفاصيل داخلية
    };
}
'''},
            {"type": "heading", "level": 2, "text": "2FA بـTOTP + recovery codes"},
            {"type": "code", "lang": "csharp", "title": "مسار التفعيل الكامل", "code": r'''
public static IEndpointRouteBuilder MapTwoFactorApi(this IEndpointRouteBuilder app)
{
    var group = app.MapGroup("/api/accounts/2fa")
        .WithTags("Accounts")
        .RequireAuthorization();

    // 1) ابدأ التفعيل: رجّع المفتاح المشترك + رابط otpauth:// للتطبيق
    group.MapPost("/setup", async (UserManager<ApplicationUser> users, ICurrentUser me, CancellationToken ct) =>
    {
        var user = await RequireUserAsync(users, me);
        await users.SetTwoFactorEnabledAsync(user, true);
        await users.ResetAuthenticatorKeyAsync(user);              // يبطل أي مفتاح سابق

        var key = await users.GetAuthenticatorKeyAsync(user);
        return TypedResults.Ok(new TwoFactorSetupResponse(
            SharedKey: FormatKey(key!),
            AuthenticatorUri: $"otpauth://totp/Shop:{Uri.EscapeDataString(user.Email!)}" +
                              $"?secret={key}&issuer=Shop&digits=6&period=30"));
    });

    // 2) أكّد التفعيل برمز من التطبيق + سلّم recovery codes (مرة واحدة)
    group.MapPost("/verify", async (
        VerifyTwoFactorRequest request, UserManager<ApplicationUser> users,
        ICurrentUser me, CancellationToken ct) =>
    {
        var user = await RequireUserAsync(users, me);
        var code = request.Code.Replace(" ", string.Empty).Replace("-", string.Empty);

        var valid = await users.VerifyTwoFactorTokenAsync(
            user, TokenOptions.DefaultAuthenticatorProvider, code);

        if (!valid)
        {
            // صدّ التخمين: كل محاولة فاشلة تُحتسب نحو lockout
            await users.AccessFailedAsync(user);
            return TypedResults.Json(new ProblemDetails
            {
                Status = 400, Title = "رمز التحقق غير صحيح",
                Detail = "تأكد من تزامن ساعة جهازك (الرموز تتغير كل 30 ثانية).",
            }, statusCode: 400);
        }

        var recoveryCodes = await users.GenerateNewTwoFactorRecoveryCodesAsync(user, 10);
        await users.UpdateSecurityStampAsync(user);                 // ← يبطل الجلسات القديمة

        return TypedResults.Ok(new TwoFactorEnabledResponse([.. recoveryCodes!]));
    });

    // 3) تعطيل (يتطلب رمزًا حاليًا — لا تسمح بتعطيل بلا إثبات)
    group.MapPost("/disable", async (
        VerifyTwoFactorRequest request, UserManager<ApplicationUser> users, ICurrentUser me, CancellationToken ct) =>
    {
        var user = await RequireUserAsync(users, me);
        var ok = await users.VerifyTwoFactorTokenAsync(
            user, TokenOptions.DefaultAuthenticatorProvider, request.Code);
        if (!ok) return TypedResults.BadRequest(new ProblemDetails { Status = 400, Title = "رمز غير صحيح" });

        await users.SetTwoFactorEnabledAsync(user, false);
        await users.UpdateSecurityStampAsync(user);
        return TypedResults.NoContent();
    });

    return app;
}

private static async Task<ApplicationUser> RequireUserAsync(UserManager<ApplicationUser> users, ICurrentUser me) =>
    me.UserId is { } id
        ? await users.FindByIdAsync(id.ToString()) ?? throw new NotFoundException("User", id)
        : throw new UnauthorizedException();

private static string FormatKey(string key) =>
    string.Join(" ", key.Chunk(4).Select(chunk => new string(chunk)));
'''},
            {"type": "callout", "kind": "warn", "title": "Security Stamp: الزر السحري لإبطال الجلسات",
             "md": """
`UpdateSecurityStampAsync(user)` بيغيّر طابع الأمان، فأي توكن/جلسة قديمة **بتبطل**.
استخدمه بعد: تغيير كلمة السر، تفعيل/تعطيل 2FA، الاشتباه في اختراق، تغيير البريد.

لو بتصدر JWT بنفسك: حط `security_stamp` كـclaim، وفي `OnTokenValidated` قارنه بالقيمة الحالية
(مع كاش قصير) — ده بيدّيك **قدرة إبطال** على توكنات الـstateless، وبيحل أكبر ضعف في JWT.
"""},
            {"type": "heading", "level": 2, "text": "فصل Identity عن الـDomain"},
            {"type": "table", "head": ["الطبقة", "مسموح", "ممنوع"], "rows": [
                ["Domain", "مفاهيم العمل (`Customer`, `Order`)", "أي إشارة لـ`ApplicationUser`/`IdentityUser`"],
                ["Application", "`ICurrentUser`, `IUserAccounts` (تجريدات)", "`UserManager` مباشرة"],
                ["Infrastructure", "Identity + EF stores + `IdentityUserAccounts`", "منطق عمل"],
                ["API", "endpoints المصادقة وDTOs", "`UserManager` في الـendpoints (غلاف فقط)"],
            ]},
            {"type": "code", "lang": "csharp", "title": "خريطتان نظيفتان بين العالمين", "code": r'''
// 1) عند إنشاء الحساب: ApplicationUser ← Customer (مفهوم العمل)
public async Task<Guid> RegisterAsync(RegisterRequest request, CancellationToken ct)
{
    var identityResult = await accounts.RegisterAsync(request, ct);
    if (!identityResult.Succeeded) throw new ValidationException(identityResult.ErrorsByField);

    // الـDomain لا يعرف شيئًا عن Identity: بنمرر قيمًا بسيطة
    var customer = await customers.CreateAsync(
        new CreateCustomerCommand(identityResult.UserId, request.Email, request.Country), ct);

    await accounts.LinkCustomerAsync(identityResult.UserId, customer.Id, ct);   // ApplicationUser.CustomerId
    return customer.Id;
}

// 2) عند تنفيذ عملية: ICurrentUser ← معرّف المستخدم فقط
public sealed record CreateOrderRequest(Guid CustomerId, IReadOnlyList<OrderLineInput> Lines);

// في الـservice: تجاهل CustomerId من الطلب واعتمد على الهوية (منع BOLA)
var customerId = user.UserId ?? throw new UnauthorizedException();
if (request.CustomerId != customerId && !user.Roles.Contains(Roles.Admin))
    throw new ForbiddenException("Order", request.CustomerId);
'''},
            {"type": "callout", "kind": "note", "title": "`MapIdentityApi<TUser>()` — نقاط جاهزة",
             "md": """
.NET 8+ بيوفّر `app.MapIdentityApi<ApplicationUser>()` اللي بيعمل `/register` و`/login` و`/refresh`
و`/confirmEmail` و`/2fa` و`/manage/info` جاهزة. مفيدة جدًا للبداية أو الـprototypes،
لكنك غالبًا هتحتاج تتحكم في: شكل الاستجابة (عقدك مش شكلها الافتراضي)، سياسات الـrate limiting،
ربط الحساب بـ`Customer`، وتسجيل الأحداث.

القرار: ابدأ بيها لو مستعجل، وانتقل لنقاطك الخاصة أول ما تحتاج تخصيصًا — ولا تسيب الاثنين شغالين معًا
(سطحان للمصادقة = ضعفان).
"""},
            {"type": "checkpoints", "items": [
                "أدمج Identity بـ`AddIdentityCore` في API مع DbContext مخصص وتسمية جداول واضحة.",
                "أضبط سياسات كلمة السر (طول > تعقيد) وlockout ومدقق كلمات مسربة.",
                "أنفّذ 2FA بـTOTP مع recovery codes وأستخدم Security Stamp لإبطال الجلسات.",
                "أفصل Identity عن الـDomain بتجريدات (`ICurrentUser`, `IUserAccounts`).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه الطول أهم من اشتراط رموز وأرقام؟",
                 "options": [
                     "أسهل على المستخدم فقط",
                     "الإنتروبيا بتيجي من الطول؛ القيود المفروضة تقلل مساحة التخمين وتشجع أنماطًا متوقعة (NIST 800-63B)",
                     "لأن الـhash أسرع",
                     "لا فرق",
                 ], "answer": 1,
                 "explain": "`password123!` بيحقق كل قيود التعقيد ومع ذلك ضعيف. «عبارة مرور» من 4 كلمات عشوائية أطول وأقوى بكثير."},
                {"q": "إيه فائدة الـSecurity Stamp؟",
                 "options": [
                     "تشفير كلمة السر",
                     "إبطال الجلسات والتوكنات القديمة بعد حدث حساس (تغيير كلمة السر/2FA/اختراق مشتبه)",
                     "تسريع الدخول",
                     "تخزين الأدوار",
                 ], "answer": 1,
                 "explain": "بدونه، تغيير كلمة السر ما بيوقفش توكن مسروق. ده أهم تعويض عن طبيعة JWT الـstateless."},
                {"q": "`/password/forgot` لإيميل غير مسجل — أنهي استجابة؟",
                 "options": [
                     "404 «الإيميل غير موجود»",
                     "202 Accepted بنفس الاستجابة والشكل، بلا كشف لوجود الحساب",
                     "400",
                     "500",
                 ], "answer": 1,
                 "explain": "كشف وجود الحساب = تسريب لقائمة مستخدميك (enumeration). الاستجابة الموحدة + rate limiting هو الحل."},
                {"q": "ليه `AddIdentityCore` بدل `AddIdentity` في مشروع API؟",
                 "options": [
                     "أسرع",
                     "`AddIdentity` بتضيف كوكيز وredirects وسلوك صفحات — أنت عايز تتحكم في الاستجابات بنفسك",
                     "`AddIdentityCore` بيدعم 2FA فقط",
                     "لا فرق",
                 ], "answer": 1,
                 "explain": "`AddIdentity` مصممة لتطبيقات MVC بصفحات. في API، `AddIdentityCore` + `AddSignInManager` بيدّيك التحكم الكامل."},
                {"q": "الـDomain layer بيعتمد على `UserManager<ApplicationUser>`. إيه المشكلة؟",
                 "options": [
                     "الأداء",
                     "تشابك مع إطار العمل: قواعد العمل بقت مرتبطة بالـIdentity، والاختبار بقى يحتاج stores حقيقية",
                     "لا مشكلة",
                     "حجم التوكن",
                 ], "answer": 1,
                 "explain": "مرّر تجريدًا (`ICurrentUser` / معرّفات بسيطة) للـApplication والـDomain، وسيب التكيف مع Identity في Infrastructure."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "Identity مضبوطة في مشروعك",
                 "md": "دمج `AddIdentityCore` مع DbContext مخصص، سياسات كلمة سر (12+ حرف، 4 أحرف مختلفة)، lockout (5 محاولات/15 دقيقة)، `BreachedPasswordValidator` بقائمة كلمات شائعة، و`/register` يرجع problem+json موحّد.",
                 "criteria": [
                     "تسجيل ناجح ينشئ المستخدم ويعطيه دور customer ويربطه بـCustomer في الـDomain",
                     "كلمة سر شائعة (مثل `password12345`) مرفوضة برسالة واضحة",
                     "5 محاولات دخول فاشلة → 423/lockout (اختبار يثبت القفل)",
                     "`/password/forgot` بيرجع نفس الاستجابة لإيميل موجود وغير موجود",
                     "الـDomain لا يحتوي أي `using Microsoft.AspNetCore.Identity`",
                 ],
                 "hint": "لو `DuplicateUserName` بيظهر رغم إن الإيميل جديد: `UserManager` بيطبّع الـUserName. اضبط `UserName = Email` consistently واستخدم `FindByEmailAsync`."},
                {"id": "t2", "title": "2FA كامل مع إبطال الجلسات",
                 "md": "نفّذ `/2fa/setup` و`/2fa/verify` و`/2fa/disable`، وأظهر recovery codes مرة واحدة، ونفّذ إبطال الجلسات بعد التفعيل عبر Security Stamp (ولو بتصدر JWT: قارن الـstamp في `OnTokenValidated`).",
                 "criteria": [
                     "otpauth URI صحيح ويفتح في تطبيق authenticator حقيقي",
                     "رمز خاطئ مرفوض ومحسوب نحو lockout",
                     "recovery codes بتُعرض مرة واحدة ومخزنة بـhash (مش نص صريح)",
                     "توكن قديم مرفوض بعد تغيير الـSecurity Stamp (اختبار)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "ASP.NET Core Identity overview", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/identity"},
                {"label": "Custom Identity with API", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/customize-identity-model"},
                {"label": "Enable 2FA", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/identity-enable-qrcodes"},
                {"label": "NIST 800-63B (digital identity)", "url": "https://pages.nist.gov/800-63-3/sp800-63b.html"},
                {"label": "OWASP Credential Stuffing", "url": "https://owasp.org/www-community/attacks/Credential_stuffing"},
            ]},
        ],
    },
]
