# -*- coding: utf-8 -*-
"""Stage 8 module 1 (part B): s8-m1-l2 (استهلاك API من العميل: auth وأخطاء)."""

TODAY = "2026-10-22"

_L2 = {
    "id": "s8-m1-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "أي حد يقدر يكتب `fetch('/api/orders')`. الفرق بين «واجهة بتشتغل» و«واجهة إنتاجية» في أربعة حاجات: **إزاي بتصادق من غير ما تسرّب توكنات** · **إزاي بتحوّل 401/403/409/429/500 لقرار واضح للمستخدم** · **إمتى تعيد المحاولة وإمتى لأ** · **وإزاي تلغي الطلبات القديمة**. الدرس ده مبني على التوصيات الحالية: **RFC 9700** (أفضل ممارسات أمان OAuth 2.0) و**RFC 10017** (OAuth 2.0 لتطبيقات المتصفح) وتحذير OWASP الصريح من تخزين التوكنات في `localStorage` — ومع تنفيذ عملي بنمط **BFF** في ASP.NET Core 10 (وهو النمط اللي أنت كمطور .NET في أفضل وضع لتنفيذه، لأنك بتملك الخادم)."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Public client مقابل Confidential client", "def": "**Public** = ما يقدرش يحفظ سر (SPA/موبايل) — فمفيش client secret وبيعتمد على PKCE. **Confidential** = عنده سر محفوظ في الخادم (تطبيق ASP.NET Core/BFF). التوصية الحالية: خلي المتصفح public client بأقل ما يمكن، أو **ما تخليش التوكنات توصله أصلًا**."},
            {"term": "PKCE", "def": "**Proof Key for Code Exchange**: المتصفح/العميل بيولّد `code_verifier` عشوائي ويبعت hash منه (`code_challenge`) في طلب التفويض، ثم الـverifier نفسه في تبادل الكود. بيمنع استخدام كود اعتراض. **RFC 9700 بيخليه إلزاميًا لكل منح authorization code** (وألغى implicit تمامًا)."},
            {"term": "BFF (Backend For Frontend)", "def": "خادم وسيط (عادة نفس تطبيق ASP.NET Core بتاعك) بيبقى هو **الـconfidential client**: بيعمل تبادل الكود، بيخزن التوكنات في الخادم، وبيدي المتصفح **كوكي جلسة HttpOnly** فقط، وبيوكّل الطلبات للـAPI مع حقن التوكن. النمط الأول في توصيات RFC 10017."},
            {"term": "Token-mediating backend", "def": "بديل أبسط من BFF: الخادم مش عميل OAuth كامل، بس بيخزن الـrefresh token وبيدير الجلسة — المتصفح بياخد access token قصير في الذاكرة. أقل أمانًا من BFF وأسهل."},
            {"term": "Access token مقابل Refresh token", "def": "**Access**: قصير العمر (عادة 5–15 دقيقة) وبيُستخدم في كل طلب. **Refresh**: أطول وبيُستخدم لجلب access جديد. القاعدة: الـrefresh هو **السر الحقيقي** — ولو وصل للمتصفح، لازم يدور (rotate) مع كل استخدام."},
            {"term": "Refresh token rotation", "def": "إصدار refresh جديد مع كل استخدام وإبطال القديم. RFC 10017 بيخليه **إلزامي** للعملاء العموميين (أو sender-constrained بدلها)، مع حد أقصى للعمر أو انتهاء عند الخمول، و**التدوير ما يمددش العمر المطلق**، وكشف إعادة استخدام التوكن القديم = حدث أمني يستوجب الإبطال."},
            {"term": "كوكي `__Host-`", "def": "بادئة اسم كوكي بتفرض: `Secure` + `Path=/` + بلا `Domain` — فبيتقفل على النطاق الحالي عبر HTTPS فقط. مع `HttpOnly` و`SameSite` بتبقى الثلاثية الأساسية لكوكيز الجلسة."},
            {"term": "CSRF", "def": "**Cross-Site Request Forgery**: موقع تاني بيخلي متصفحك يبعت طلب باسمك لأن الكوكي بتتُرسل تلقائيًا. بيظهر كـ**مقايضة** لنمط الكوكيز (بينما نمط Bearer token مش معرض له). العلاج: `SameSite=Strict/Lax` + ترويسة مخصصة/توكن مضاد للتزوير."},
            {"term": "CORS وpreflight", "def": "آلية المتصفح للسماح بطلبات عبر الأصول. الطلب «غير البسيط» (ترويسة مخصصة/PUT/DELETE) بيبدأ بـ**OPTIONS preflight**. لو الواجهة والخادم على نفس الأصل (نمط BFF) فمفيش CORS أصلًا — وده أحد مكاسبه."},
            {"term": "ProblemDetails (RFC 9457)", "def": "صيغة خطأ موحّدة: `type` · `title` · `status` · `detail` · `instance` + امتدادات (وفي ASP.NET Core: `errors` لأخطاء التحقق و`traceId`). العميل الذكي بيقرأها بدل ما يخمّن من نص الرسالة (2.2.3)."},
            {"term": "Idempotency key", "def": "ترويسة فريدة لكل عملية إنشاء (`Idempotency-Key: <uuid>`) بتخلي إعادة المحاولة آمنة: الخادم بيعرف إنه نفس الطلب (5.2.5). من غيرها، إعادة محاولة POST ممكن تعمل طلبين."},
            {"term": "Backoff مع jitter", "def": "إعادة المحاولة بمهلة متزايدة أسّيًا + عشوائية — العشوائية (jitter) بتمنع إن كل العملاء يرجعوا في نفس اللحظة بعد عطل (thundering herd)."},
            {"term": "Single-flight refresh", "def": "لما 5 طلبات تفشل بـ401 في نفس الوقت، **تجديد واحد بس** يحصل والباقي ينتظره — وإلا هتعمل 5 طلبات تجديد وتبطل 4 توكنات مدوّرة (وبسبب الدوران ممكن تسجّل المستخدم خروج)."},
            {"term": "Optimistic UI + rollback", "def": "تحديث الواجهة قبل تأكيد الخادم (تجربة أسرع)، مع **خطة تراجع** لو الخادم رفض. بيصلح للعمليات منخفضة الخطورة (إعجاب/نقل عنصر) وبيمنع للعمليات المالية (5.1.3)."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① أول قرار: فين تعيش التوكنات؟ (ترتيب من الأقوى للأضعف)"},
        {"type": "table", "caption": "أربعة أنماط — من توصيات RFC 10017 وOWASP",
         "head": ["النمط", "المتصفح بيحتفظ بإيه", "JS يقدر يقراه؟", "مخاطر أساسية", "التعقيد", "إمتى تستخدمه"],
         "rows": [
             ["**① BFF (الأقوى)**", "كوكي جلسة `HttpOnly` فقط — **صفر توكنات**", "لا", "CSRF (يُعالج بـSameSite + ترويسة مخصصة)", "متوسط (proxy + جلسة)", "**الافتراضي لأي منتج جاد** — خصوصًا وأنت بتملك الخادم بالفعل"],
             ["**② AT في الذاكرة + RT في كوكي `HttpOnly`**", "access token في متغير JS + refresh في كوكي", "الـaccess فقط (قصير)", "XSS يقدر يستخدم الـaccess طول صلاحيتها · CSRF على endpoint التجديد", "متوسط", "SPA بلا BFF (مثلًا API مشترك بين عدة عملاء)"],
             ["**③ التوكنان في كوكيز `HttpOnly`**", "access + refresh في كوكيز", "لا", "CSRF (مطلوب دفاع جاد) · حجم الكوكي · الإلغاء أصعب", "منخفض", "لو الـAPI بيقرأ الكوكيز مباشرة وتقبل مخاطرة CSRF"],
             ["**④ `localStorage`/`sessionStorage`**", "التوكنات في storage", "**نعم — أي سكربت**", "XSS واحد = سرقة كاملة ودائمة (الـrefresh كمان)", "منخفض جدًا", "**لا** — OWASP بتحذر صراحة: «لا تخزن توكنات أو معرّفات جلسات في localStorage»"],
         ]},
        {"type": "callout", "kind": "danger", "title": "قواعد إلزامية (من RFC 9700 وRFC 10017 — مش اختيارات)",
         "md": "**① Implicit grant ميت**: استخدم **Authorization Code + PKCE** دائمًا.\n**② لا توكنات في `localStorage`/`sessionStorage`**: أي XSS بيسرق كل حاجة، وأي مكتبة/إضافة/ويدجت طرف ثالث في الصفحة بيقدر يقرا.\n**③ لو المتصفح بيستلم refresh token**: لازم **يدور مع كل استخدام** (أو يكون sender-constrained) + **حد أقصى للعمر أو انتهاء بالخمول** + التدوير **ما يمددش العمر المطلق** + كشف إعادة استخدام التوكن القديم = **إبطال + حدث أمني**.\n**④ access token قصير** (5–15 دقيقة) ومقصور على جمهور محدد (audience) وأقل scopes.\n**⑤ لا أسرار في الـfrontend أبدًا**: أي client secret أو مفتاح API في الحزمة = مكشوف للعالم (6.2.3).\n**⑥ سجل الخروج**: اربط عمر الجلسة بعمر الـrefresh token، ونفّذ RP-initiated logout عشان الخروج من عندك يخرج من مزود الهوية كمان.\n**⑦ لا تسجل التوكنات**: لا في السجلات (7.1.3) ولا في URLs ولا في localStorage — تسرب التوكن في السجلات من أشهر حوادث التسريب."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② BFF في ASP.NET Core 10 — الكود الكامل"},
        {"type": "code", "lang": "csharp", "title": "src/Shop.Bff/Program.cs — جلسة كوكي للمتصفح + توكنات في الخادم + proxy", "filename": "src/Shop.Bff/Program.cs", "code": r'''using System.Globalization;
using System.Net;
using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;

var builder = WebApplication.CreateBuilder(args);

// ── 1) المصادقة: كوكي للمتصفح + OIDC للخادم (confidential client) ──────
builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
        options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    })
    .AddCookie(options =>
    {
        // بادئة __Host- تفرض: Secure + Path=/ + بلا Domain
        options.Cookie.Name = "__Host-shopbff";
        options.Cookie.HttpOnly = true;
        options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
        options.Cookie.SameSite = SameSiteMode.Strict;   // دفاع CSRF الأساسي
        options.SlidingExpiration = true;
        options.ExpireTimeSpan = TimeSpan.FromHours(8);
        options.Events.OnRedirectToLogin = ctx =>
        {
            // لطلبات API: 401 بدل تحويل HTML (العميل بيقرر يعيد التوجيه)
            if (IsApiRequest(ctx.Request))
            {
                ctx.Response.StatusCode = StatusCodes.Status401Unauthorized;
                return Task.CompletedTask;
            }

            ctx.Response.Redirect(ctx.RedirectUri);
            return Task.CompletedTask;
        };
    })
    .AddOpenIdConnect(options =>
    {
        options.Authority = builder.Configuration["Oidc:Authority"];
        options.ClientId = builder.Configuration["Oidc:ClientId"];
        options.ClientSecret = builder.Configuration["Oidc:ClientSecret"];  // في Key Vault (6.2.3)
        options.ResponseType = OpenIdConnectResponseType.Code;   // لا implicit (RFC 9700)
        options.UsePkce = true;                                  // PKCE إلزامي
        options.SaveTokens = true;                               // عشان الـproxy يحقنها
        options.GetClaimsFromUserInfoEndpoint = true;
        options.Scope.Clear();
        options.Scope.Add("openid");
        options.Scope.Add("profile");
        options.Scope.Add("shop.api");        // أقل scopes ممكنة
        options.Scope.Add("offline_access");  // مطلوب للـrefresh token
        options.TokenValidationParameters = new Microsoft.IdentityModel.Tokens.TokenValidationParameters
        {
            NameClaimType = "name",
            RoleClaimType = "role",
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("ApiUser", p => p.RequireAuthenticatedUser());
});

// ── 2) الـproxy: HttpClient مُسمّى (ولو عايز YARP كامل: AddReverseProxy + MapReverseProxy)
builder.Services.AddHttpClient("shop-api", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Api:BaseUrl"]!);
    client.Timeout = TimeSpan.FromSeconds(15);
});

var app = builder.Build();

app.UseForwardedHeaders();
app.UseHttpsRedirection();
app.UseSecurityHeaders();            // الامتداد من 7.2.3 (HSTS/CSP/nosniff/…)

// ── 3) دفاع CSRF: أي طلب مُعدِّل لازم يحمل ترويسة مخصصة ─────────────────
// (الكوكي SameSite=Strict كفاية في أغلب الحالات؛ الترويسة طبقة إضافية للـAPI)
app.Use(async (ctx, next) =>
{
    if (HttpMethods.IsPost(ctx.Request.Method)
        || HttpMethods.IsPut(ctx.Request.Method)
        || HttpMethods.IsPatch(ctx.Request.Method)
        || HttpMethods.IsDelete(ctx.Request.Method))
    {
        if (!ctx.Request.Headers.TryGetValue("X-Csrf", out var value) || value != "1")
        {
            ctx.Response.StatusCode = StatusCodes.Status403Forbidden;
            await ctx.Response.WriteAsJsonAsync(new
            {
                title = "طلب مرفوض",
                detail = "الترويسة X-Csrf مطلوبة للطلبات المُعدِّلة.",
            });
            return;
        }
    }

    await next();
});

app.UseAuthentication();
app.UseAuthorization();

// ── 4) نقاط BFF: من أنا؟ / تسجيل الدخول / الخروج ────────────────────────
app.MapGet("/bff/user", (ClaimsPrincipal user) => user.Identity?.IsAuthenticated == true
    ? Results.Ok(new
    {
        isAuthenticated = true,
        name = user.FindFirst("name")?.Value ?? user.Identity?.Name,
        roles = user.FindAll("role").Select(c => c.Value).ToArray(),
        // لا نرسل أي توكن للمتصفح — هذه هي الفكرة كلها
    })
    : Results.Json(new { isAuthenticated = false }, statusCode: 401))
    .AllowAnonymous();

app.MapGet("/bff/login", (string? returnUrl) =>
{
    // منع open redirect: مسارات نسبية فقط (لا URLs خارجية)
    var target = !string.IsNullOrEmpty(returnUrl)
                 && Uri.IsWellFormedUriString(returnUrl, UriKind.Relative)
                 && returnUrl.StartsWith('/')
        ? returnUrl
        : "/";

    return Results.Challenge(
        new AuthenticationProperties { RedirectUri = target },
        [OpenIdConnectDefaults.AuthenticationScheme]);
});

app.MapPost("/bff/logout", async (HttpContext ctx) =>
{
    await ctx.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    // RP-initiated logout: الخروج من مزود الهوية كمان (وإلا الجلسة هناك تفضل)
    await ctx.SignOutAsync(OpenIdConnectDefaults.AuthenticationScheme,
        new AuthenticationProperties { RedirectUri = "/" });
    return Results.Ok(new { loggedOut = true });
}).RequireAuthorization("ApiUser");

// ── 5) الـproxy: حقن access token من الجلسة (وتجديده لو انتهى) ──────────
app.Map("/api/{**catch-all}", async (HttpContext ctx, IHttpClientFactory factory, ILogger<Program> log) =>
{
    if (ctx.User.Identity?.IsAuthenticated != true)
    {
        return Results.StatusCode(StatusCodes.Status401Unauthorized);
    }

    // GetTokenAsync بيقرأ التوكن المحفوظ بـSaveTokens.
    // ملاحظة مهمة: ASP.NET Core ما يجددش التوكن تلقائيًا — لو منتهي،
    // استخدم Microsoft.Identity.Web (ITokenAcquisition) أو Duende.Bff/TokenManagement.
    var accessToken = await ctx.GetTokenAsync("access_token");
    var expires = await ctx.GetTokenAsync("expires_at");

    if (string.IsNullOrEmpty(accessToken) || IsExpired(expires, log))
    {
        // 401 مع سبب واضح — العميل بيعمل redirect لـ/bff/login
        return Results.Json(
            new { title = "انتهت صلاحية الجلسة", detail = "أعد تسجيل الدخول." },
            statusCode: StatusCodes.Status401Unauthorized);
    }

    var client = factory.CreateClient("shop-api");
    using var request = new HttpRequestMessage(
        new HttpMethod(ctx.Request.Method), ctx.Request.Path + ctx.Request.QueryString);

    request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);
    // تمرير CorrelationId للربط بالسجلات (7.1.3)
    if (ctx.Request.Headers.TryGetValue("X-Correlation-Id", out var cid))
    {
        request.Headers.TryAddWithoutValidation("X-Correlation-Id", cid.ToString());
    }

    if (ctx.Request.ContentLength > 0 || HttpMethods.IsPost(ctx.Request.Method))
    {
        request.Content = new StreamContent(ctx.Request.Body);
        request.Content.Headers.ContentType =
            System.Net.Http.Headers.MediaTypeHeaderValue.Parse(
                ctx.Request.ContentType ?? "application/json");
    }

    try
    {
        using var response = await client.SendAsync(request, ctx.RequestAborted);
        var body = await response.Content.ReadAsByteArrayAsync(ctx.RequestAborted);

        // ترويسات يديرها Kestrel/الاتصال نفسه — نسخها بيرمي أو بيكسر الاستجابة
        string[] skip = ["Transfer-Encoding", "Connection", "Content-Length", "Keep-Alive"];
        foreach (var header in response.Headers)
        {
            if (skip.Contains(header.Key, StringComparer.OrdinalIgnoreCase)) continue;
            ctx.Response.Headers[header.Key] = header.Value.ToArray();
        }

        return Results.Bytes(body, response.Content.Headers.ContentType?.ToString(),
            statusCode: (int)response.StatusCode);
    }
    catch (HttpRequestException ex)
    {
        log.LogError(ex, "فشل الاتصال بالـAPI");
        return Results.Json(
            new { title = "تعذر الوصول إلى الخدمة", detail = "حاول مرة أخرى بعد قليل." },
            statusCode: StatusCodes.Status502BadGateway);
    }
    catch (TaskCanceledException) when (ctx.RequestAborted.IsCancellationRequested)
    {
        return Results.StatusCode(499);   // العميل ألغى (499 اصطلاح شائع، غير قياسي)
    }
}).RequireAuthorization("ApiUser");

// ── 6) الملفات الثابتة للواجهة (SPA fallback) ───────────────────────────
app.UseDefaultFiles();
app.UseStaticFiles();
app.MapFallbackToFile("index.html");

app.Run();

static bool IsApiRequest(HttpRequest request)
    => request.Path.StartsWithSegments("/api")
       || string.Equals(request.Headers["Accept"], "application/json", StringComparison.Ordinal);

static bool IsExpired(string? expiresAt, ILogger log)
{
    if (string.IsNullOrEmpty(expiresAt))
    {
        return false;   // بلا معلومات انتهاء — نفترض الصلاحية ونراقب 401 من الخادم
    }

    if (!DateTimeOffset.TryParse(
            expiresAt,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
            out var exp))
    {
        log.LogWarning("قيمة expires_at غير مفهومة: {Value}", expiresAt);
        return false;
    }

    // هامش أمان 60 ثانية قبل الانتهاء الفعلي
    return exp <= DateTimeOffset.UtcNow.AddSeconds(60);
}

internal static class UriHelper
{
    public static string GetDisplayUrl(HttpRequest request, bool forceHttps)
        => $"{(forceHttps ? "https" : request.Scheme)}://{request.Host}{request.PathBase}{request.Path}";
}
'''},
        {"type": "callout", "kind": "warn", "title": "ثلاث حاجات لازم تعرفها عن تجديد التوكن في .NET",
         "md": "**① ASP.NET Core ما يجددش access token تلقائيًا** لما تستخدم `SaveTokens` + `GetTokenAsync` — بتاخد اللي محفوظ بس. لو التوكن انتهى، الجلسة بتفضل صالحة لكن النداء للـAPI هيفشل.\n**② الحلول الجاهزة**: `Microsoft.Identity.Web` (لـEntra ID) بيديك `ITokenAcquisition.GetAccessTokenForUserAsync(scopes)` مع **تجديد تلقائي** وتخزين · أو **Duende.Bff / Duende.AccessTokenManagement** لأي مزود OIDC (بيدير التجديد والتدوير والتخزين).\n**③ التخزين في جلسة موزعة**: لو عندك أكتر من نسخة، الجلسة/التوكنات لازم تكون في مخزن مشترك (Redis) — وإلا تسجيل الدخول على نسخة والتجديد على التانية هيفشل. وده مثال حقيقي على نمط من 2.2.12 و3.4.\n\nوالقاعدة المعمارية: **المتصفح ما يشوفش توكن أبدًا** — فأي XSS بيسرق جلسة كوكي (محدودة وقابلة للإبطال) مش توكنات طويلة العمر."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ العميل: معالجة 401 وre-auth وتجديد واحد (single-flight)"},
        {"type": "code", "lang": "javascript", "title": "src/api/client.ts — طلب + أخطاء + إعادة محاولة + إلغاء", "filename": "src/api/client.ts", "code": r'''import type { ApiError } from "./types";

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
  /** مفتاح idempotency للطلبات المنشئة (5.2.5) — لازم لإعادة المحاولة الآمنة */
  idempotencyKey?: string;
  /** إعادة المحاولة التلقائية: للطلبات الآمنة فقط */
  retry?: { attempts?: number; baseMs?: number } | false;
  /** لا تعالج 401 (لنداءات التجديد نفسها) */
  skipAuthHandling?: boolean;
}

const DEFAULT_TIMEOUT = 8_000;
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

/**
 * عميل واحد لكل الطلبات:
 *   • نمط BFF: credentials include (كوكي جلسة) — لا توكنات في JS.
 *   • 401 → محاولة إعادة مصادقة واحدة (single-flight) ثم إعادة الطلب مرة واحدة.
 *   • 429/5xx → إعادة محاولة بـbackoff + jitter للطلبات الآمنة فقط
 *     (أو POST معه Idempotency-Key).
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    signal,
    timeoutMs = DEFAULT_TIMEOUT,
    idempotencyKey,
    retry = { attempts: 2, baseMs: 250 },
    skipAuthHandling = false,
  } = options;

  const attempt = async (allowReauth: boolean, attemptNo = 0): Promise<T> => {
    let res: Response;
    try {
      res = await fetch(path, {
        method,
        credentials: "include",                       // كوكي BFF (لا Bearer في JS)
        headers: buildHeaders(method, body, idempotencyKey),
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: signal
          ? AbortSignal.any([signal, AbortSignal.timeout(timeoutMs)])
          : AbortSignal.timeout(timeoutMs),
      });
    } catch (err) {
      throw networkError(err);
    }

    // 401 → أعد المصادقة مرة واحدة، ثم أعد الطلب
    if (res.status === 401 && !skipAuthHandling && allowReauth) {
      const ok = await reauthenticateOnce();
      if (ok) return attempt(false);
      throw await toApiError(res);
    }

    if (!res.ok) {
      const apiError = await toApiError(res);
      if (shouldRetry(method, res.status, idempotencyKey, retry) && attemptNo < maxAttempts(retry)) {
        await sleep(backoffMs(retry, attemptNo, apiError.retryAfterSeconds));
        return attempt(allowReauth, attemptNo + 1);
      }

      throw apiError;
    }

    if (res.status === 204) return undefined as T;
    const text = await res.text();
    if (!text) return undefined as T;
    return JSON.parse(text) as T;      // تحقّق من الشكل عند الحدود في الطبقة الأعلى (8.1.1)
  };

  return attempt(true);
}

function buildHeaders(method: string, body: unknown, idempotencyKey?: string): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    // دفاع CSRF الإضافي مع كوكي الجلسة (8.1.2 ②)
    "X-Csrf": "1",
  };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  if (!SAFE_METHODS.has(method)) headers["Cache-Control"] = "no-store";
  return headers;
}

/**
 * single-flight: مهما كان عدد الطلبات اللي فشلت بـ401،
 * محاولة إعادة المصادقة بتحصل مرة واحدة فقط.
 */
let reauthInFlight: Promise<boolean> | null = null;

async function reauthenticateOnce(): Promise<boolean> {
  reauthInFlight ??= (async () => {
    try {
      const res = await fetch("/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "X-Csrf": "1" },
        signal: AbortSignal.timeout(10_000),
      });
      if (res.ok) return true;
      // الجلسة انتهت فعلًا → وجّه المستخدم لتسجيل الدخول (BFF)
      redirectToLogin();
      return false;
    } catch {
      redirectToLogin();
      return false;
    }
  })();

  try {
    return await reauthInFlight;
  } finally {
    // نظّف بعد الاستقرار عشان محاولة مستقبلية تقدر تشتغل
    setTimeout(() => { reauthInFlight = null; }, 0);
  }
}

function redirectToLogin(): void {
  const back = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.assign(`/bff/login?returnUrl=${back}`);
}

/** ما نعيدش المحاولة إلا لو الطلب آمن (أو POST بمفتاح idempotency). */
function shouldRetry(
  method: string,
  status: number,
  idempotencyKey: string | undefined,
  retry: RequestOptions["retry"],
): boolean {
  if (!retry) return false;
  const retryableStatus = status === 429 || status === 502 || status === 503 || status === 504;
  const safe = SAFE_METHODS.has(method) || idempotencyKey !== undefined;
  return retryableStatus && safe;
}

/** الحد الأقصى للمحاولات الإضافية (لا حلقة لا نهائية). */
function maxAttempts(retry: RequestOptions["retry"]): number {
  return typeof retry === "object" && retry !== null ? (retry.attempts ?? 2) : 0;
}

/** backoff أسّي + jitter، مع احترام Retry-After لو موجود. */
function backoffMs(retry: RequestOptions["retry"], attemptNo: number, retryAfterSeconds?: number): number {
  const base = typeof retry === "object" && retry?.baseMs ? retry.baseMs : 250;
  const exponential = base * 2 ** Math.min(4, attemptNo);   // 250 → 500 → 1000 → 2000 …
  const jitter = Math.random() * base;                      // يمنع thundering herd
  const fromHeader = retryAfterSeconds ? retryAfterSeconds * 1000 : 0;
  return Math.min(15_000, Math.max(exponential + jitter, fromHeader));
}

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

async function toApiError(res: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = undefined;
  }

  const pd = (typeof body === "object" && body !== null ? body : {}) as Record<string, unknown>;
  const str = (k: string) => (typeof pd[k] === "string" ? (pd[k] as string) : undefined);
  const retryAfter = res.headers.get("Retry-After");

  return {
    status: res.status,
    title: str("title") ?? defaultTitle(res.status),
    detail: str("detail"),
    type: str("type"),
    instance: str("instance"),
    correlationId: str("traceId") ?? res.headers.get("X-Correlation-Id") ?? undefined,
    fieldErrors: extractFieldErrors(pd.errors),
    retryAfterSeconds: retryAfter ? Number.parseInt(retryAfter, 10) || undefined : undefined,
  };
}

function extractFieldErrors(errors: unknown): Record<string, readonly string[]> | undefined {
  if (typeof errors !== "object" || errors === null) return undefined;
  const out: Record<string, string[]> = {};
  for (const [field, messages] of Object.entries(errors as Record<string, unknown>)) {
    out[field] = Array.isArray(messages) ? messages.filter((m): m is string => typeof m === "string") : [];
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

function networkError(err: unknown): ApiError {
  const dom = err instanceof DOMException ? err.name : "";
  return {
    status: 0,
    title: dom === "AbortError" ? "أُلغي الطلب"
      : dom === "TimeoutError" ? "انتهت مهلة الاتصال"
      : "تعذر الوصول إلى الخادم",
    detail: dom ? undefined : "تحقق من الاتصال ثم أعد المحاولة.",
  };
}

function defaultTitle(status: number): string {
  if (status === 403) return "ليست لديك صلاحية لهذا الإجراء";
  if (status === 404) return "العنصر غير موجود";
  if (status === 409) return "تعارض مع حالة أحدث — حدّث البيانات";
  if (status === 422) return "البيانات غير صالحة";
  if (status === 429) return "طلبات كثيرة — حاول بعد قليل";
  if (status >= 500) return "خطأ في الخادم";
  return `طلب غير ناجح (${status})`;
}
'''},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ كل حالة HTTP → قرار واضح في الواجهة"},
        {"type": "table", "caption": "جدول القرار (الصقه جنب الكود — ده اللي بيفرّق المحترف عن المبتدئ)",
         "head": ["الحالة", "المعنى من خادمك (2.2.3)", "رد الفعل في الواجهة", "إعادة محاولة؟"],
         "rows": [
             ["**400**", "جسم الطلب غير صالح (قواعد عامة)", "اعرض رسالة عامة + احتفظ بمدخلات النموذج", "لا — صحّح المدخلات أولًا"],
             ["**422 / 400 مع `errors`**", "أخطاء تحقق لكل حقل (FluentValidation)", "اربط كل خطأ بالحقل (`aria-describedby`) + لفّ لأول خطأ", "لا"],
             ["**401**", "بلا جلسة/منتهية", "إعادة مصادقة **مرة واحدة** (single-flight) ثم إعادة الطلب؛ لو فشلت → `/bff/login` مع `returnUrl`", "نعم، مرة واحدة بعد إعادة المصادقة"],
             ["**403**", "مصادَق لكن بلا صلاحية", "رسالة واضحة + لا تخفي الزر فقط (اخفه أو عطّله حسب الدور) + **لا** تعد المحاولة", "لا"],
             ["**404**", "المورد غير موجود (أو محذوف)", "اعرض حالة «غير موجود» + رابط رجوع — لا صفحة خطأ عامة", "لا"],
             ["**409**", "تعارض (تعديل متزامن/حالة قديمة — 3.2.2)", "أعد جلب البيانات واعرض الفرق/الإصدار الحالي واطلب تأكيد", "لا — بعد إعادة الجلب"],
             ["**412**", "شرط مسبق فشل (`If-Match`/ETag)", "زي 409: حدّث واعرض التعارض", "لا"],
             ["**422**", "صالح بنيويًا لكن مرفوض عملًا", "رسالة العمل (مثل «الرصيد غير كافٍ») بلغة المستخدم", "لا"],
             ["**429**", "حد المعدل (2.2.5)", "احترم `Retry-After` + عطّل الزر + عدّاد تنازلي", "نعم، بعد `Retry-After`"],
             ["**500**", "خطأ خادم غير متوقع", "رسالة عامة + **اعرض CorrelationId** مع زر «نسخ التفاصيل» + شجّع إعادة المحاولة لاحقًا", "نعم (1–2) للطلبات الآمنة"],
             ["**502/503/504**", "وسيط/خدمة غير متاحة (نشر/عطل)", "حالة «الخدمة مؤقتًا غير متاحة» + backoff مع jitter", "نعم (backoff) للآمنة أو POST بمفتاح"],
             ["**شبكة (status 0)**", "انقطاع/مهلة/DNS", "«تعذر الوصول» + فحص `navigator.onLine` + زر إعادة محاولة يدوي", "يدويًا (لا تلقائي بلا حدود)"],
             ["**AbortError**", "إلغاء مقصود (تغيير صفحة/مكوّن)", "**لا شيء** — لا رسالة خطأ ولا سجل حادث", "لا"],
         ]},
        {"type": "callout", "kind": "tip", "title": "ثلاثة تفاصيل بتخلي التجربة احترافية",
         "md": "**① اعرض `correlationId` في رسالة الخطأ** مع زر نسخ — الدعم هيشكرك، وأنت هتلاقي الحادثة في السجلات في ثانية (7.1.3).\n**② احتفظ بمدخلات النموذج عند الفشل** — مسح 20 حقلًا بعد خطأ شبكة من أكتر الحاجات اللي بتضايق المستخدمين.\n**③ لا تخفي الخطأ برسالة عامة دايمًا**: 403 و409 و429 ليهم رسائل مختلفة ومفيدة. الرسالة العامة الوحيدة المناسبة هي 500 (لأن التفاصيل الداخلية ما تنفعش تُكشف — 7.2.3)."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ الكاش والحالة: ما تعيدش اختراع العجلة"},
        {"type": "table", "caption": "الخيارات الثلاثة لإدارة بيانات الخادم في الواجهة",
         "head": ["الخيار", "بيحل إيه", "المفاهيم الأساسية", "إمتى تختاره"],
         "rows": [
             ["**TanStack Query**", "كاش + إعادة جلب + تحميل/خطأ + تحسين + إلغاء (مستقل عن إطار الحالة)", "`queryKey` · `staleTime` · `gcTime` · `invalidateQueries` · `useMutation` · optimistic updates", "الافتراضي لمعظم التطبيقات (React/Vue/Svelte/Angular)"],
             ["**RTK Query**", "نفس الدور داخل Redux Toolkit + توليد endpoints من OpenAPI", "`createApi` · `endpoints` · tags للتصحيح · `useQuery` hooks", "لو فريقك بالفعل على Redux أو عايز codegen من OpenAPI"],
             ["**يدوي (مثل كود هذا الدرس)**", "التحكم الكامل — بس بتكتب الكاش والإلغاء وإعادة المحاولة بنفسك", "`Remote<T>` state machine + store بسيط", "لوحة إدارية صغيرة · أو للتعلم قبل ما تعتمد على مكتبة"],
         ]},
        {"type": "callout", "kind": "note", "title": "قواعد كاش تمنع 90% من أخطاء الواجهة",
         "md": "**① مفتاح الكاش يشمل كل المدخلات**: `['orders', { cursor, status }]` — مفتاح ناقص = بيانات غلط لمستخدم تاني.\n**② `staleTime` مقابل `gcTime`**: الأول «قد إيه البيانات طازجة» (ما تعيدش الجلب خلالها) والتاني «إمتى تتحذف من الذاكرة». البيانات الحساسة (رصيد/مخزون): `staleTime` قصير.\n**③ الإبطال بعد الطفرة**: أي `POST/PUT/DELETE` ناجح → أبطل مفاتيح القائمة والتفاصيل المتعلقة. نسيان ده = «الواجهة مش بتتحدث».\n**④ إلغاء الطلبات عند تغيير المفتاح**: من غير إلغاء، استجابة قديمة ممكن توصل بعد الجديدة وتكتب فوقها (race).\n**⑤ لا تكاش بيانات حساسة على القرص**: الكاش في الذاكرة فقط — وخصوصًا مع بيانات شخصية (7.2.5).\n**⑥ optimistic UI للعمليات المنخفضة الخطورة فقط** ومع rollback واضح + إظهار حالة «جارٍ الحفظ». للعمليات المالية: انتظر التأكيد (5.1.3)."},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ CORS — وإزاي تتجنبه أصلًا"},
        {"type": "code", "lang": "csharp", "title": "إعداد CORS في الخادم (لو الواجهة على أصل مختلف)", "filename": "src/Shop.Api/Program.cs (مقتطف CORS)", "code": r'''// القاعدة: allowlist صريح بأصول معروفة — ولا AllowAnyOrigin مع AllowCredentials
// (التركيب ده مرفوض أصلًا في ASP.NET Core لأنه غير آمن).
var allowedOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>() ?? throw new InvalidOperationException("عيّن Cors:AllowedOrigins");

builder.Services.AddCors(options => options.AddPolicy("shop-web", policy => policy
    .WithOrigins(allowedOrigins)          // مثلًا https://admin.shop.example.com
    .WithMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    .WithHeaders("Content-Type", "Authorization", "X-Csrf", "X-Correlation-Id", "Idempotency-Key")
    .ExposeHeaders("X-Correlation-Id", "Retry-After", "Location")   // ما ينفعش العميل يقراها من غيرها
    .AllowCredentials()                   // مطلوب لنمط الكوكيز (BFF/refresh cookie)
    .SetPreflightCacheTimeout(TimeSpan.FromMinutes(10))));

var app = builder.Build();
// الترتيب مهم: UseCors قبل MapEndpoints وبعد UseRouting (وضمن UseAuthorization)
app.UseCors("shop-web");
'''},
        {"type": "table", "caption": "أسئلة CORS اللي بتضيّع ساعات — وإجاباتها",
         "head": ["السؤال", "الإجابة"],
         "rows": [
             ["إمتى يحصل preflight؟", "لأي طلب «غير بسيط»: طريقة غير GET/HEAD/POST · أو ترويسة مخصصة (`X-Csrf`, `Authorization`, `Idempotency-Key`) · أو `Content-Type: application/json`"],
             ["الواجهة والخادم على نفس النطاق بس منافذ مختلفة (5173 مقابل 8080) — فيه CORS؟", "**نعم** — الأصل = scheme + host + **port**. الحل في التطوير: proxy في `vite.config.ts` (8.1.1)"],
             ["`AllowAnyOrigin` مع `AllowCredentials`؟", "**مرفوض/غير آمن**: ASP.NET Core بترمي استثناء. ولو عدّيت بـ`SetIsOriginAllowed(_ => true)` فأنت فتحت الباب لأي موقع"],
             ["أصل الخطأ: «No 'Access-Control-Allow-Origin' header» رغم إن الطلب نجح", "غالبًا الاستجابة جاية من وسيط/بوابة (401/502) من غير ترويسات CORS — المشكلة في المصادقة مش في CORS"],
             ["إزاي أتجنب CORS بالكامل؟", "قدّم الواجهة من **نفس الأصل** (BFF يقدّم الملفات الثابتة + يوكّل `/api`) — زي ما في كود 8.1.2 ②"],
             ["`ExposeHeaders` لماذا؟", "المتصفح ما يكشفش ترويسات الاستجابة غير البسيطة للـJS من غيرها — فـ`X-Correlation-Id` و`Retry-After` لازم تُدرج"],
         ]},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ عميل مكتوب من OpenAPI — بلا أخطاء كتابة يدوية"},
        {"type": "callout", "kind": "goal", "title": "من 2.1.1 إلى الواجهة: الأنواع مولّدة لا مكتوبة",
         "md": "عندك مستند OpenAPI 3.1 من ASP.NET Core 10 (2.1.1). استغله:\n\n• **`openapi-typescript`** بيولّد أنواع TS من المستند (`npx openapi-typescript http://localhost:8080/openapi/v1.json -o src/api/schema.d.ts`) — فأي تغيير في الـAPI بيظهر كخطأ ترجمة في الواجهة.\n• **`openapi-fetch`** بيستخدم الأنواع دي لنداءات typed بلا codegen للدوال.\n• **RTK Query codegen** أو **Scalar client** أو **NSwag** لو عايز hooks/دوال مولّدة.\n• **الأهم**: اجعل التوليد **خطوة في CI** تفشل لو المستند تغير والأنواع ما اتحدثتش — ده العقد الحي بين الخادم والواجهة (ونفس فكرة contract tests من 5.3.2 بس للأنواع).\n\nومع ذلك: **الأنواع المولّدة ما تلغيش التحقق وقت التشغيل** للبيانات الحرجة (8.1.1 ③)."},

        {"type": "callout", "kind": "danger", "title": "سبع حاجات لا تعملها أبدًا في عميل الواجهة",
         "md": "**① توكن في `localStorage`** (OWASP صريحة).\n**② client secret أو مفتاح API في الحزمة** — أي حاجة في الـfrontend مكشوفة.\n**③ إعادة محاولة POST بلا `Idempotency-Key`** — هتعمل طلبين (5.2.5).\n**④ تسجيل التوكنات/الكوكيز في console أو analytics** — تسرب مباشر.\n**⑤ تفويض في الواجهة فقط** (إخفاء زر) — الإخفاء UX مش أمان؛ التفويض في الخادم دايمًا (2.2.1/7.2.3).\n**⑥ access token طويل العمر «عشان ما نعملش refresh»** — العكس: قصير + تجديد في الخادم.\n**⑦ تجاهل `Retry-After` وإعادة المحاولة بقوة** — بتزيد العطل وبتدخل في حظر الحد."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أرتّب أنماط تخزين التوكنات الأربعة وأعرف ليه BFF هو الأقوى ولماذا `localStorage` مرفوض.",
            "أعرف إن **Authorization Code + PKCE** هو المطلوب (وimplicit ميت حسب RFC 9700).",
            "أعرف قواعد refresh token للعميل العام: تدوير مع كل استخدام · عمر أقصى · التدوير ما يمددش العمر المطلق · كشف إعادة الاستخدام = حدث أمني.",
            "أبني BFF في ASP.NET Core: كوكي `__Host-` بـHttpOnly/Secure/SameSite + OIDC بـ`UsePkce`/`SaveTokens` + proxy يحقن التوكن + دفاع CSRF بترويسة.",
            "أعرف إن `GetTokenAsync` ما يجددش تلقائيًا، وأعرف الحلول (`Microsoft.Identity.Web` / Duende) ومشكلة الجلسة الموزعة.",
            "أعالج كل حالة HTTP بقرار واضح: 401 single-flight · 403 بلا إعادة · 409 إعادة جلب · 429 احترام `Retry-After` · 500 بـcorrelationId.",
            "أعيد المحاولة **للطلبات الآمنة فقط** (أو POST بمفتاح idempotency) بـbackoff + jitter.",
            "أستخدم `AbortSignal` للإلغاء وأفرّق `AbortError` (مقصود) عن أخطاء الشبكة.",
            "أعرف قواعد الكاش: مفتاح كامل · staleTime مقابل gcTime · إبطال بعد الطفرة · إلغاء عند تغيير المفتاح.",
            "أفهم CORS/preflight وأعرف إن نفس الأصل (BFF) بيتجنبه، ولماذا `AllowAnyOrigin` مع credentials مرفوض.",
            "أولّد أنواع TS من OpenAPI وأخلي التوليد خطوة CI — مع الاستمرار في التحقق وقت التشغيل.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على مصادقة وأخطاء العميل.",
         "questions": [
             {"q": "أفضل نمط لتطبيق SPA عندك فيه خادم ASP.NET Core؟",
              "options": ["توكنات في localStorage لبساطتها",
                          "BFF: الخادم عميل سري، والتوكنات في الخادم، والمتصفح ياخد كوكي جلسة HttpOnly فقط",
                          "implicit flow لأنه أسرع",
                          "access token في كوكي غير HttpOnly عشان JS يقدر يقراه"],
              "answer": 1,
              "explain": "RFC 10017 بيرتب BFF كأقوى نمط: المتصفح ما يشوفش توكن أبدًا، فأي XSS بيسرق كوكي جلسة (قابلة للإبطال وقصيرة) مش توكنات. وimplicit ملغى حسب RFC 9700، وlocalStorage مرفوض صراحة من OWASP."},
             {"q": "خمس طلبات فشلت بـ401 في نفس اللحظة. السلوك الصحيح؟",
              "options": ["كل طلب يجدد التوكن لنفسه",
                          "تجديد واحد (single-flight) والباقي ينتظره ثم يعيد طلبه مرة واحدة",
                          "إعادة توجيه فورية لصفحة الدخول من كل طلب",
                          "تجاهل الأخطاء"],
              "answer": 1,
              "explain": "مع تدوير الـrefresh token، خمسة تجديدات متوازية هتبطل أربعة توكنات — وممكن تسجّل المستخدم خروج عشوائيًا. single-flight بيضمن محاولة واحدة، وبعدها إعادة الطلب **مرة واحدة** (بلا حلقة لا نهائية)."},
             {"q": "إمتى إعادة المحاولة التلقائية مقبولة؟",
              "options": ["لأي طلب فشل",
                          "للطلبات الآمنة (GET/HEAD) أو POST يحمل Idempotency-Key، وعلى 429/502/503/504 فقط، مع backoff وجitter واحترام Retry-After",
                          "لـ400 و422 لأنها أخطاء مؤقتة",
                          "دائمًا بحد أقصى 10 محاولات"],
              "answer": 1,
              "explain": "400/422 أخطاء في الطلب نفسه — إعادة المحاولة هتفشل بنفس الطريقة وتزيد الحمل. وPOST بلا مفتاح idempotency ممكن ينشئ سجلين. و`Retry-After` لازم يُحترم وإلا هتدخل حظر الحد."},
             {"q": "كوكي الجلسة في BFF لازم يكون؟",
              "options": ["HttpOnly فقط",
                          "HttpOnly + Secure + SameSite=Strict/Lax، ويفضل بادئة __Host-",
                          "قابل للقراءة من JS عشان التجديد",
                          "بلا قيود لتسهيل التطوير"],
              "answer": 1,
              "explain": "`HttpOnly` بتمنع قراءة JS · `Secure` بتقصرها على HTTPS · `SameSite` بتقلل CSRF · وبادئة `__Host-` بتفرض الثلاثية دي + `Path=/` + بلا `Domain` (فلا تُرسل لنطاقات فرعية)."},
             {"q": "رد 409 (Conflict) على تحديث طلب. أفضل استجابة في الواجهة؟",
              "options": ["رسالة «خطأ في الخادم» وإعادة محاولة",
                          "إعادة جلب البيانات وعرض الحالة الحالية/التعارض ثم طلب تأكيد من المستخدم",
                          "تجاهل الرد والاحتفاظ بالتعديلات",
                          "تسجيل الخروج"],
              "answer": 1,
              "explain": "409 معناها حالتك قديمة (تعديل متزامن — 3.2.2 أو ETag/If-Match). الصح: أعد الجلب، اعرض الفرق، واطلب تأكيدًا — وحافظ على مدخلات المستخدم. إعادة المحاولة العمياء هترجع نفس 409."},
             {"q": "`GetTokenAsync(\"access_token\")` في ASP.NET Core بيعمل إيه لو التوكن انتهى؟",
              "options": ["يجدده تلقائيًا",
                          "يرجع التوكن المنتهي (أو null) — التجديد التلقائي محتاج Microsoft.Identity.Web (ITokenAcquisition) أو Duende TokenManagement",
                          "يرمي استثناء",
                          "يسجل خروج المستخدم"],
              "answer": 1,
              "explain": "`SaveTokens` بيخزن التوكنات في خصائص المصادقة، و`GetTokenAsync` بيقرأها **من غير تجديد**. عشان كده في كود الـBFF فحصنا `expires_at` بهامش 60 ثانية ورجعنا 401 واضح — والحل الإنتاجي مكتبة تدير التجديد والتخزين (ومخزن مشترك لو أكتر من نسخة)."},
             {"q": "واجهة على 5173 وAPI على 8080 (نفس المضيف). فيه CORS؟",
              "options": ["لا، نفس المضيف يكفي",
                          "نعم — الأصل يشمل المنفذ، فمطلوب CORS أو proxy في التطوير",
                          "لا، لأن الطلبات JSON",
                          "نعم لكن فقط لـPOST"],
              "answer": 1,
              "explain": "الأصل = scheme + host + **port**. في التطوير: proxy في `vite.config.ts` (بلا CORS). في الإنتاج: نفس الأصل عبر BFF (الأنضف) أو allowlist صريح مع `AllowCredentials` و`ExposeHeaders` للترويسات اللي العميل محتاج يقراها."},
             {"q": "أنواع TS مولّدة من OpenAPI — هل تغني عن التحقق وقت التشغيل؟",
              "options": ["نعم، المترجم يضمن الصحة",
                          "لا — الأنواع تُمسح وقت التشغيل، فالتحقق عند الحدود لازم للبيانات الحرجة",
                          "نعم لو فعّلت strict",
                          "لا حاجة للأنواع المولدة أصلًا"],
              "answer": 1,
              "explain": "الأنواع المولدة قيمة كبيرة (اكتشاف تغيير العقد في CI) لكنها **ادعاء وقت التشغيل**: الخادم ممكن يرجع حاجة مختلفة (إصدار قديم · وسيط · خطأ). للبيانات الحرجة تحقق فعلي (zod/valibot أو دوال parse) — نفس مبدأ «لا تثق في المدخلات»."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "BFF شغال + عميل يتعامل مع كل الحالات.",
         "items": [
            {"id": "s8-m1-l2-t1",
             "title": "مهمة 1: BFF في ASP.NET Core 10 بيوصل لمزود OIDC",
             "md": "ابنِ `Shop.Bff` كتطبيق ASP.NET Core: مصادقة بكوكي جلسة + OIDC (Authorization Code + PKCE) ضد مزود حقيقي أو محلي (Keycloak في compose من 2.2.8 · أو Entra ID dev tenant)، وproxy يوكّل `/api/*` لتطبيقك مع حقن التوكن، ونقاط `/bff/user` و`/bff/login` و`/bff/logout`. وقدّم ملفات الواجهة الثابتة من نفس التطبيق (نفس الأصل → بلا CORS).",
             "criteria": [
                 "كوكي الجلسة: اسم ببادئة `__Host-` + `HttpOnly` + `Secure=Always` + `SameSite=Strict` + `SlidingExpiration` بمدة معقولة.",
                 "OIDC: `ResponseType=Code` + `UsePkce=true` + `SaveTokens=true` + `offline_access` + **أقل scopes** + `TokenValidationParameters` بـNameClaimType/RoleClaimType.",
                 "دفاع CSRF: طلب مُعدِّل بدون `X-Csrf` → 403 بجسم ProblemDetails.",
                 "Proxy: حقن `Authorization: Bearer` من `GetTokenAsync` + تمرير `X-Correlation-Id` + `ctx.RequestAborted` للإلغاء + معالجة انتهاء الصلاحية (فحص `expires_at` بهامش) بـ401 واضح.",
                 "`/bff/user` بيرجع `isAuthenticated/name/roles` **وبلا أي توكن** + `/bff/login` و`/bff/logout` (RP-initiated logout).",
                 "`OnRedirectToLogin` بيرجع 401 لطلبات الـAPI بدل تحويل HTML.",
                 "الـclient secret من Key Vault/Managed Identity (6.2.3) — **مش** في `appsettings.json` الملتزم.",
                 "صفحة قرار مكتوبة: النمط المختار (BFF) · كيف يُدار التجديد (Microsoft.Identity.Web/Duende/يدوي) · أين تُخزن الجلسة لو ≥ 2 نسخة (Redis) · كيف يُختبر الخروج والإلغاء.",
                 "اختبار تكاملي واحد على الأقل: طلب `/api/…` بلا جلسة → 401 · ومع جلسة (توكن اختباري) → الترويسة `Authorization` وصلت للـAPI (استخدم mock/echo endpoint).",
             ],
             "hint": "أسرع مزود محلي: Keycloak أو Zitadel بـ`docker compose` (زي ما عملنا في 2.2.8). عرّف client بـ`Confidential` + `Authorization Code Flow` + `Valid redirect URIs = https://localhost:5001/signin-oidc` + `Web origins` فاضي (لأن المتصفح ما بيكلمش المزود مباشرة في BFF). ولو عايز تجرب من غير مزود: `dotnet user-jwts` (2.2.7) بيولّد توكنات اختبار — بس ده يغطي الـAPI مش الـBFF flow. ولو `GetTokenAsync` بيرجع null: تأكد إن `SaveTokens=true` وإن الـscope فيه `offline_access`.",
             "solution": "المشاكل النموذجية: (1) `SameSite=Strict` بيكسر الرجوع من مزود الهوية (لأنها navigation عبر موقع) — الحل: مسار `/bff/login` بيعمل challenge من نفس الأصل، فمشكلة الـStrict ما تظهرش؛ لو ظهرت، استخدم `Lax` ووثّق المقايضة. (2) الكوكي ببادئة `__Host-` بيفشل في `http://localhost` لأنه بيطلب `Secure` — استخدم HTTPS في التطوير (`dotnet dev-certs https --trust`) أو اسم كوكي مختلف في Development مع شرط بيئي. (3) انتهاء التوكن: أول نسخة هتنجح لحد ما التوكن تنتهي (دقائق) وبعدها كل الطلبات 401 — هنا لازم تقرر: تجديد يدوي بـrefresh_token (اكتبه) أو مكتبة. (4) أكتر من نسخة: الجلسة في كوكي مشفرة فبتشتغل، بس **التوكنات** في خصائص المصادقة جوه الكوكي → حجم الكوكي ممكن يعدي 4KB؛ الحل تخزين التوكنات في Redis بمعرّف جلسة (وده بالظبط سبب وجود المكتبات الجاهزة). (5) أهم مكسب: الواجهة بقت على نفس الأصل فاختفت كل مشاكل CORS.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/security/authentication/",
                 "https://learn.microsoft.com/entra/identity-platform/v2-protocols-oidc",
                 "https://datatracker.ietf.org/doc/html/rfc9700",
                 "https://oauth.net/2/browser-based-apps/",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
                 "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/",
             ]},
            {"id": "s8-m1-l2-t2",
             "title": "مهمة 2: عميل يتعامل مع كل الحالات + اختبارات",
             "md": "على المشروع من 8.1.1: طوّر الـclient ليشمل 401 single-flight · إعادة محاولة آمنة بـbackoff وجitter · احترام `Retry-After` · `Idempotency-Key` لـPOST · إلغاء بـ`AbortController` عند فك الارتباط/تغيير الشاشة · وربط كل خطأ بحالة واجهة (`Remote<T>`). واكتب ≥ 6 اختبارات بـVitest تغطي الحالات الحرجة.",
             "criteria": [
                 "`request<T>()` واحد لكل النداءات: ترويسات موحدة (`Accept` · `X-Csrf` · `Content-Type` عند الحاجة · `Idempotency-Key`) · `credentials: 'include'` · مهلة افتراضية + `AbortSignal.any` للدمج.",
                 "401 → **محاولة إعادة مصادقة واحدة** (shared promise) ثم إعادة الطلب مرة واحدة؛ عند الفشل توجيه لـ`/bff/login?returnUrl=…`.",
                 "إعادة المحاولة: فقط 429/502/503/504 + (GET/HEAD/OPTIONS أو POST بمفتاح) + backoff أسّي + jitter + احترام `Retry-After` + حد أقصى للمحاولات + سقف زمني.",
                 "تحويل كل استجابة فاشلة لـ`ApiError` من ProblemDetails (بما فيها `traceId`/`X-Correlation-Id` و`errors` لكل حقل) + `networkError` بتمييز timeout/abort/offline.",
                 "**جدول ربط**: `ApiError.status` → حالة واجهة ورسالة وإجراء (استخدم جدول الدرس) — مع `correlationId` ظاهر وزر نسخ + احتفاظ بمدخلات النموذج.",
                 "إلغاء: `AbortController` لكل شاشة/مكوّن، وإلغاء الطلب السابق عند تغيير المعاملات (cursor/بحث)، و`AbortError` لا يُعرض كخطأ.",
                 "≥ 6 اختبارات Vitest: 401→refresh→retry مرة واحدة (وتثبيت إن التجديد حصل **مرة** رغم 3 طلبات متوازية) · 429 يحترم Retry-After · POST بلا مفتاح لا يُعاد · 409 لا يُعاد · network error → status 0 · AbortError بلا رسالة خطأ.",
                 "ملف قرار: هل تستخدم TanStack Query/RTK Query فوق العميل ده؟ وليه (staleTime/gcTime/إبطال/إلغاء) — ولو يدوي: كيف تمنع الـraces.",
             ],
             "hint": "لاختبار single-flight: ابدأ 3 طلبات متوازية مع mock بيرجع 401 في الأول و200 بعد التجديد، واثبت إن `/auth/refresh` اتنادت **مرة واحدة** (`expect(refreshMock).toHaveBeenCalledTimes(1)`). ولاختبار backoff: استخدم `vi.useFakeTimers()` و`vi.advanceTimersByTimeAsync()` — وإلا الاختبار هيستنى فعليًا. وخلي بالك من `setTimeout(() => reauthInFlight = null, 0)` في finally: مع fake timers محتاج تتقدم بالزمن عشان تتنظف.",
             "solution": "الأخطاء النموذجية: (1) حلقة لا نهائية: 401 → refresh → retry → 401 → refresh… — الحل علم `allowReauth=false` في المحاولة المعادة (موجود في الكود). (2) إعادة محاولة POST بتعمل طلبين — لأن الناس بتضيف retry عام من غير فحص `Idempotency-Key`. (3) jitter بـ`Math.random()` فقط بدون سقف → محاولات متأخرة جدًا؛ حدد سقفًا (15 ثانية في الكود). (4) `Retry-After` ممكن يكون تاريخ HTTP مش ثوانٍ — الكود بيتعامل مع الثواني؛ لو الخادم بيبعت تاريخ، أضف تحويلًا (`Date.parse`). (5) في الاختبارات: `Response.json()` بتستهلك الجسم مرة واحدة — فلو حاولت تقرا Body مرتين في الاختبار هتفشل؛ استخدم `res.clone()`. النتيجة المتوقعة: ~200 سطر عميل + 6–8 اختبارات تعدي، وأهم مكسب: **كل حالة فشل عندها سلوك محدد ومُختبر** بدل «رسالة خطأ عامة».",
             "resources": [
                 "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API",
                 "https://developer.mozilla.org/en-US/docs/Web/API/AbortController",
                 "https://tanstack.com/query/latest",
                 "https://redux-toolkit.js.org/rtk-query/overview",
                 "https://www.rfc-editor.org/rfc/rfc9457.html",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "RFC 10017: OAuth 2.0 لتطبيقات المتصفح", "url": "https://oauth.net/2/browser-based-apps/"},
            {"label": "RFC 9700: أفضل ممارسات أمان OAuth 2.0", "url": "https://datatracker.ietf.org/doc/html/rfc9700"},
            {"label": "OWASP: Session Management Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"},
            {"label": "OWASP: Authentication Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"},
            {"label": "ASP.NET Core: المصادقة والتفويض", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/"},
            {"label": "MDN: Fetch API", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API"},
            {"label": "MDN: CORS", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS"},
            {"label": "RFC 9457: Problem Details", "url": "https://www.rfc-editor.org/rfc/rfc9457.html"},
            {"label": "TanStack Query", "url": "https://tanstack.com/query/latest"},
        ]},
    ],
}

LESSONS_S8_B = [_L2]
