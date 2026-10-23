"""Stage 2, Module 2 — Authentication & Authorization (lessons 4-5 of 5)."""

TODAY = "2026-10-22"

LESSONS_S2_C = [
    # ------------------------------------------------------------------ l4
    {
        "id": "s2-m2-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
«تسجيل دخول بـGoogle» مش feature — ده **تفويض لجهة خارجية بإثبات هوية مستخدمي لك** (OpenID Connect)،
ومعاه أسئلة حقيقية: أنهي flow يصلح لأنهي عميل؟ فين تخزن التوكنات؟ إزاي تجدد؟ وإزاي تلغي الربط بأمان؟

قبل الكود: فرق مهم كثيرًا ما يُخلط —
**① الـAPI بتاعك بيتحقق من توكنات IdP خارجي** (Entra ID / Auth0 / Keycloak) — ده درس الـJWT السابق.
**② تطبيقك بيعمل تسجيل دخول خارجي ويدير هوية محلية** — ده درس النهارده.
"""},
            {"type": "terms", "items": [
                {"term": "IdP / RP", "def": "Identity Provider (Google، Entra ID، Keycloak) وRelying Party (تطبيقك اللي بيثق فيه)."},
                {"term": "Authorization Code + PKCE", "def": "الـflow الصحيح لكل العملاء اللي فيهم مستخدم (ويب، SPA، موبايل). الكود بيتبدّل بتوكنات على الـbackend، وPKCE بيمنع اعتراضه."},
                {"term": "Client Credentials", "def": "خدمة إلى خدمة، بلا مستخدم. `client_id` + `client_secret` (أو شهادة) → access token."},
                {"term": "Device Code", "def": "جهاز بلا متصفح مريح (CLI، TV): المستخدم يكتب كودًا على جهاز تاني."},
                {"term": "Implicit / Hybrid", "def": "أنماط قديمة. Implicit مرفوض في OAuth 2.1؛ Hybrid باقٍ لحالات نادرة (سيرفر-side + توكن فوري)."},
                {"term": "id_token مقابل access_token", "def": "`id_token` = إثبات هوية (اقرأه للـclaims). `access_token` = تصريح وصول للـAPI (ابعته، ولا تفسر محتواه)."},
                {"term": "state / nonce", "def": "قيم عشوائية تمنع CSRF (state) وربط التوكن بالجلسة (nonce). الـmiddleware بيتحقق منهم — لا تعطّلهم."},
                {"term": "Redirect URI allowlist", "def": "قائمة عناوين العودة المسجلة عند الـIdP. أي تجاوز = ثغرة open redirect / سرقة كود."},
            ]},
            {"type": "heading", "level": 2, "text": "① اختيار الـflow حسب نوع العميل"},
            {"type": "table", "head": ["العميل", "الـflow", "أسرار", "ملاحظات"], "rows": [
                ["تطبيق ويب server-side (ASP.NET Core MVC/Razor)", "Authorization Code (+ `offline_access` للتجديد)", "client secret على الخادم", "الجلسة في كوكي HttpOnly — الأسهل والأأمن"],
                ["SPA (React/Vue/Angular)", "Authorization Code + PKCE **مع BFF**", "لا secret في المتصفح", "BFF بيخفي التوكنات في كوكي؛ بدونه التوكنات مكشوفة لـJS"],
                ["Mobile / MAUI", "Authorization Code + PKCE", "بلا secret (أو client assertion)", "خزّن التوكنات في Keychain/Keystore"],
                ["CLI / أداة سطر أوامر", "Device Code", "بلا secret", "تجربة مستخدم جيدة بلا متصفح مدمج"],
                ["خدمة → خدمة (background job)", "Client Credentials", "secret/certificate من Key Vault", "مفيش مستخدم؛ الصلاحيات scopes للتطبيق"],
                ["IoT/TV", "Device Code", "—", "شاشات محدودة"],
                ["أي عميل حديث", "✗ Implicit", "—", "مرفوض في OAuth 2.1 — لا تستخدمه حتى لو SDK قديم يقترحه"],
            ]},
            {"type": "heading", "level": 2, "text": "② تطبيق ويب server-side: الكود الكامل"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Web package Microsoft.AspNetCore.Authentication.OpenIdConnect
dotnet add Shop.Web package Microsoft.AspNetCore.Authentication.Cookies
# لو الـIdP هو Microsoft Entra ID:
dotnet add Shop.Api package Microsoft.Identity.Web
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Web/Program.cs", "title": "كوكي محلي + OIDC خارجي (Code + PKCE)", "code": r'''
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;

var builder = WebApplication.CreateBuilder(args);
var auth = builder.Configuration.GetSection("Oidc").Get<OidcOptions>()!;

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
        options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    })
    .AddCookie(options =>
    {
        options.Cookie.Name = "shop.session";
        options.Cookie.HttpOnly = true;
        options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
        options.Cookie.SameSite = SameSiteMode.Lax;          // Lax مطلوب لسير العودة من الـIdP
        options.SlidingExpiration = true;
        options.ExpireTimeSpan = TimeSpan.FromHours(8);
        options.AccessDeniedPath = "/access-denied";
        options.Events.OnRedirectToLogin = ctx =>             // API-ish endpoints: 401 بدل redirect
        {
            if (ctx.Request.Path.StartsWithSegments("/api"))
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
        options.Authority = auth.Authority;                  // مثال: https://accounts.google.com
        options.ClientId = auth.ClientId;
        options.ClientSecret = auth.ClientSecret;            // من Key Vault / user-secrets — ليس من الـrepo

        options.ResponseType = OpenIdConnectResponseType.Code;   // ✓ Code فقط
        options.UsePkce = true;                                   // ✓ إلزامي عمليًا
        options.RequireHttpsMetadata = true;

        options.Scope.Clear();
        options.Scope.Add("openid");
        options.Scope.Add("profile");
        options.Scope.Add("email");
        options.Scope.Add("offline_access");                  // ← عشان نطلب refresh_token

        options.SaveTokens = true;                            // نحفظ التوكنات مع الكوكي للتجديد ونداء APIs
        options.GetClaimsFromUserInfoEndpoint = true;         // claims أغنى من id_token لوحده
        options.MapInboundClaims = false;                     // أسماء claims زي ما الـIdP بيبعتها

        options.TokenValidationParameters = new TokenValidationParameters
        {
            NameClaimType = "name",
            RoleClaimType = "role",
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
        };

        options.Events = new OpenIdConnectEvents
        {
            OnRedirectToIdentityProvider = ctx =>
            {
                // مرّر سياق إضافي بأمان (مثال: صفحة العودة بعد التسجيل)
                if (ctx.Properties.Items.TryGetValue("returnTo", out var to) && to is not null)
                    ctx.ProtocolMessage.State = Uri.EscapeDataString(to);
                return Task.CompletedTask;
            },
            OnTokenValidated = ctx =>
            {
                // ✓ طبّق تفويضك المحلي على الهوية الخارجية (لا تثق في claims الـIdP مباشرةً للأدوار)
                var email = ctx.Principal?.FindFirst("email")?.Value;
                // مثال: اربط بمستخدم محلي أو أنشئ حسابًا وسجّل حدث التدقيق
                return Task.CompletedTask;
            },
            OnRemoteFailure = ctx =>
            {
                // المستخدم ألغى أو الـIdP رفض: ارجع لصفحة مفهومة بدل خطأ خام
                ctx.Response.Redirect("/login?error=external");
                ctx.HandleResponse();
                return Task.CompletedTask;
            },
            OnAccessDenied = ctx =>
            {
                ctx.Response.Redirect("/access-denied");
                ctx.HandleResponse();
                return Task.CompletedTask;
            },
        };
    });

builder.Services.AddAuthorizationBuilder();
var app = builder.Build();

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/login", (HttpContext ctx, string? returnUrl) =>
    Results.Challenge(new AuthenticationProperties
    {
        RedirectUri = string.IsNullOrWhiteSpace(returnUrl) ? "/" : returnUrl,   // ✓ whitelist للـreturnUrl!
        Items = { ["returnTo"] = returnUrl ?? "/" },
    }));

app.MapGet("/logout", (HttpContext ctx) => Results.SignOut(
    new AuthenticationProperties { RedirectUri = "/" },
    [CookieAuthenticationDefaults.AuthenticationScheme, OpenIdConnectDefaults.AuthenticationScheme]));

app.Run();

public sealed record OidcOptions
{
    public required string Authority { get; init; }
    public required string ClientId { get; init; }
    public required string ClientSecret { get; init; }
}
'''},
            {"type": "callout", "kind": "danger", "title": "open redirect: `returnUrl` غير مفحوص",
             "md": """
`RedirectUri = returnUrl` من العميل = المهاجم يبعت
`/login?returnUrl=https://evil.example/steal` فيسرق الكود/الجلسة بعد الدخول.

```csharp
private static bool IsLocalReturn(string? url) =>
    !string.IsNullOrEmpty(url) && Uri.IsWellFormedUriString(url, UriKind.Relative) && url.StartsWith('/');

// الاستخدام
RedirectUri = IsLocalReturn(returnUrl) ? returnUrl : "/"
```
القاعدة: **أي URL من العميل يُعامل كمصدر خطر** — whitelist للمسارات المحلية أو لنطاقات مسجلة.
"""},
            {"type": "heading", "level": 2, "text": "③ ربط حساب خارجي بـIdentity المحلي"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Auth/ExternalLoginEndpoints.cs", "title": "Challenge → callback → ربط أو إنشاء", "code": r'''
public static IEndpointRouteBuilder MapExternalLoginApi(this IEndpointRouteBuilder app)
{
    var group = app.MapGroup("/api/auth/external").WithTags("Auth");

    // 1) ابدأ: ارجع للـIdP (الـmiddleware هيدير state/PKCE/correlation cookie)
    group.MapGet("/challenge/{provider}", (string provider, HttpContext http, string? returnUrl) =>
    {
        var props = new AuthenticationProperties
        {
            RedirectUri = IsLocalReturn(returnUrl) ? returnUrl : "/auth/callback",
        };
        return Results.Challenge(props, [provider]);           // "google" | "github" | "entra"
    }).AllowAnonymous();

    // 2) العودة: سجّل الدخول أو اربط الحساب
    group.MapGet("/callback", async (
        HttpContext http, SignInManager<ApplicationUser> signIn, UserManager<ApplicationUser> users,
        TokenRotationService tokens, CancellationToken ct) =>
    {
        var info = await signIn.GetExternalLoginInfoAsync();
        if (info is null) return Results.Redirect("/login?error=external");

        // أ) المستخدم موجود وربطه سابقًا → دخول مباشر
        var result = await signIn.ExternalLoginSignInAsync(
            info.LoginProvider, info.ProviderKey, isPersistent: false, bypassTwoFactor: false);

        if (result.IsLockedOut)
            return Results.Json(new ProblemDetails { Status = 423, Title = "الحساب مقفل مؤقتًا" }, statusCode: 423);

        ApplicationUser user;
        if (result.Succeeded)
        {
            user = (await users.FindByLoginAsync(info.LoginProvider, info.ProviderKey))!;
        }
        else
        {
            // ب) أول مرة: ابحث بإيميل موثّق من الـIdP، وإلا اطلب تأكيدًا
            var email = info.Principal.FindFirstValue(ClaimTypes.Email)
                     ?? info.Principal.FindFirstValue("email");

            var emailVerified = info.Principal.HasClaim("email_verified", "true")
                             || info.Principal.HasClaim("email_verified", "True");

            if (email is null || !emailVerified)
                return Results.Redirect("/login?error=email_required");

            user = await users.FindByEmailAsync(email)
                   ?? new ApplicationUser
                   {
                       UserName = email,
                       Email = email,
                       EmailConfirmed = true,
                       FullName = info.Principal.FindFirstValue("name"),
                       CreatedAt = DateTimeOffset.UtcNow,
                   };

            if (user.Id == Guid.Empty)
            {
                var created = await users.CreateAsync(user);          // بلا كلمة سر محلية
                if (!created.Succeeded)
                    return Results.Json(new ProblemDetails { Status = 400, Title = "تعذّر إنشاء الحساب" },
                                        statusCode: 400);
                await users.AddToRoleAsync(user, Roles.Customer);
            }

            // ✓ اربط المزوّد بالحساب (لو مش مربوط)
            var alreadyLinked = await users.FindByLoginAsync(info.LoginProvider, info.ProviderKey);
            if (alreadyLinked is null)
                await users.AddLoginAsync(user, info);

            await users.UpdateSecurityStampAsync(user);
            result = await signIn.ExternalLoginSignInAsync(info.LoginProvider, info.ProviderKey, false);
            if (!result.Succeeded)
                return Results.Redirect("/login?error=external");
        }

        // ج) أصدر توكناتنا الخاصة (العميل بيتعامل مع عقدنا، مش مع توكنات Google)
        var pair = await tokens.IssueAsync(user,
            http.Connection.RemoteIpAddress?.ToString() ?? "?", http.Request.Headers.UserAgent, ct);

        SetRefreshCookie(http, pair.RefreshToken, pair.RefreshExpiresIn);
        return Results.Redirect($"/auth/done#access_token={pair.AccessToken}");
        // (للـSPA: الأفضل تسليم الـaccess token عبر استدعاء /refresh بدل وضعه في الرابط)
    }).AllowAnonymous();

    // 3) إلغاء الربط — بأمان
    group.MapPost("/unlink/{provider}", async (
        string provider, UserManager<ApplicationUser> users, ICurrentUser me,
        TokenRotationService tokens, CancellationToken ct) =>
    {
        if (me.UserId is not { } id) return Results.Unauthorized();
        var user = await users.FindByIdAsync(id.ToString());
        if (user is null) return Results.NotFound();

        var logins = await users.GetLoginsAsync(user);
        var hasPassword = await users.HasPasswordAsync(user);

        // ★ لا تترك الحساب بلا أي وسيلة دخول
        if (logins.Count <= 1 && !hasPassword)
            return Results.Json(new ProblemDetails
            {
                Status = 409,
                Title = "لا يمكن إلغاء الربط",
                Detail = "أضف كلمة سر أو مزوّدًا آخر أولًا حتى لا تفقد الوصول لحسابك.",
            }, statusCode: 409);

        var login = logins.FirstOrDefault(l => l.LoginProvider == provider);
        if (login is null) return Results.NotFound();

        await users.RemoveLoginAsync(user, login.LoginProvider, login.ProviderKey);
        await users.UpdateSecurityStampAsync(user);                    // يبطل الجلسات القديمة
        await tokens.RevokeAllForUserAsync(id, "unlinked", ct);        // يبطل refresh tokens

        return Results.NoContent();
    }).RequireAuthorization();

    return app;
}

private static bool IsLocalReturn(string? url) =>
    !string.IsNullOrEmpty(url) && Uri.IsWellFormedUriString(url, UriKind.Relative) && url.StartsWith('/');
'''},
            {"type": "callout", "kind": "warn", "title": "حاجات بتلسع في External login",
             "md": """
- **الإيميل غير موثّق** من الـIdP → لو ربطت تلقائيًا، مهاجم ينشئ حساب Google بإيميل الضحية ويختطف حسابه. اشترط `email_verified`.
- **`account takeover` بالربط الأعمى**: لو المستخدم مسجّل بإيميل ومزوّد خارجي رجّع نفس الإيميل، اربط **فقط** بعد إثبات ملكية (أو اطلب كلمة السر).
- **الأدوار من الـIdP**: claims زي `role`/`groups` من Entra ID ممكن تتضخّم. طبّق خرائط محلية صريحة ولا تفوّض مباشرة من claims خارجية.
- **تضخّم الكوكي**: كل الـclaims في الكوكي → رأس أكبر من 8KB وفشل صامت. خزّن معرّف المستخدم بس، وحمّل الباقي عند الحاجة (أو استخدم `ITicketStore`).
- **تسجيل التوكنات في اللوجات**: `SaveTokens=true` بيخليها متاحة — لا تسجّل `HttpContext.GetTokenAsync(...)` أبدًا.
- **`SameSite=None` بلا `Secure`** → المتصفح يرفض الكوكي ويسقط سير العودة.
"""},
            {"type": "heading", "level": 2, "text": "④ التجديد ونداء APIs خارجية"},
            {"type": "code", "lang": "csharp", "title": "تجديد يدوي + استدعاء خدمة خارجية بالتوكن", "code": r'''
/// <summary>
/// ASP.NET Core لا يجدد توكنات OIDC تلقائيًا. إما تستخدم مكتبة إدارة توكنات
/// (Microsoft.Identity.Web أو Duende.AccessTokenManagement) أو تجددها بنفسك كما هنا.
/// </summary>
public sealed class OidcTokenRefresher(IHttpClientFactory http, OidcOptions options, TimeProvider time)
{
    public async Task<string?> GetAccessTokenAsync(HttpContext ctx, string resource, CancellationToken ct)
    {
        var auth = await ctx.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        if (!auth.Succeeded) return null;

        var expires = auth.Properties.GetTokenValue("expires_at");
        var accessToken = auth.Properties.GetTokenValue("access_token");
        var refreshToken = auth.Properties.GetTokenValue("refresh_token");

        // لسه صالح لأكثر من دقيقة → استخدمه مباشرة
        if (expires is not null && DateTimeOffset.TryParse(expires, out var at)
            && at > time.GetUtcNow().AddMinutes(1))
            return accessToken;

        if (refreshToken is null) return null;                 // يحتاج إعادة challenge

        var response = await http.CreateClient("oidc").PostFormAsync($"{options.Authority}/token", new()
        {
            ["grant_type"] = "refresh_token",
            ["refresh_token"] = refreshToken,
            ["client_id"] = options.ClientId,
            ["client_secret"] = options.ClientSecret,
            ["scope"] = resource,
        }, ct);

        if (!response.IsSuccessStatusCode) return null;

        var tokens = await response.Content.ReadFromJsonAsync<TokenResponse>(cancellationToken: ct);
        if (tokens is null) return null;

        // ✓ احفظ التوكنات الجديدة في الكوكي (وإلا هتجدد في كل طلب)
        auth.Properties.UpdateTokenValue("access_token", tokens.AccessToken);
        auth.Properties.UpdateTokenValue("refresh_token", tokens.RefreshToken ?? refreshToken);
        auth.Properties.UpdateTokenValue("expires_at",
            time.GetUtcNow().AddSeconds(tokens.ExpiresIn).ToString("o"));
        await ctx.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, auth.Principal!, auth.Properties);

        return tokens.AccessToken;
    }
}

internal sealed record TokenResponse
{
    public string AccessToken { get; init; } = "";
    public string? RefreshToken { get; init; }
    public int ExpiresIn { get; init; }
}
'''},
            {"type": "table", "head": ["السيناريو", "الحل", "ملاحظة"], "rows": [
                ["SPA + IdP خارجي", "BFF (ASP.NET Core + YARP/Duende.Bff)", "التوكنات في كوكي HttpOnly والمتصفح ما يشوفهاش"],
                ["API بتحقق توكنات Entra ID", "`Microsoft.Identity.Web` → `AddMicrosoftIdentityWebApi`", "يدعم JWKS وتدوير المفاتيح وscopes"],
                ["خدمة داخلية تنادي خدمة تانية", "Client Credentials", "بلا مستخدم؛ صلاحيات على مستوى التطبيق"],
                ["نيابة عن المستخدم (on-behalf-of)", "OAuth2 On-Behalf-Of flow", "سلسلة خدمات مع الحفاظ على هوية المستخدم"],
                ["تجديد تلقائي في تطبيق ويب", "`ITicketStore` + مكتبة إدارة توكنات", "التجديد اليدوي بيتكرر في كل مشروع — استخدم مكتبة"],
            ]},
            {"type": "checkpoints", "items": [
                "أختار الـflow الصحيح لكل نوع عميل (Code+PKCE، Client Credentials، Device Code).",
                "أضبط OIDC بكوكي آمن وأتحكم في الـclaims والـevents.",
                "أربط/ألغي ربط حسابات خارجية بأمان (email_verified + وسيلة دخول بديلة + إبطال الجلسات).",
                "أجدد التوكنات وأنادي خدمات خارجية بدون تسريبها في اللوجات أو الروابط.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "SPA بيتصل بـIdP خارجي مباشرة. أنهي نمط موصى به؟",
                 "options": [
                     "Implicit flow عشان أسرع",
                     "BFF: الـbackend يعمل Code+PKCE ويخفي التوكنات في كوكي HttpOnly",
                     "تخزين التوكن في localStorage",
                     "وضع client secret في الـSPA",
                 ], "answer": 1,
                 "explain": "Implicit مرفوض في OAuth 2.1، وأي secret في المتصفح مكشوف. BFF بيخلي التوكنات بعيدة عن JavaScript خالص."},
                {"q": "الفرق بين `id_token` و`access_token`؟",
                 "options": [
                     "لا فرق",
                     "`id_token` إثبات هوية تقرأه؛ `access_token` تصريح وصول تبعته للـAPI ولا تفسر محتواه",
                     "`access_token` أقصر",
                     "`id_token` للتجديد",
                 ], "answer": 1,
                 "explain": "خلطهم سبب أخطاء شهيرة: استخدام access_token كدليل هوية (جمهوره الـAPI مش تطبيقك) أو إرسال id_token للـAPI."},
                {"q": "مستخدم سجّل بـGoogle بإيميل `victim@example.com` غير موثّق. لو ربطت تلقائيًا بحساب موجود؟",
                 "options": [
                     "تجربة مستخدم أفضل",
                     "اختطاف حساب (account takeover) — لازم تشترط email_verified أو إثبات ملكية",
                     "مفيش خطر",
                     "يحتاج 2FA فقط",
                 ], "answer": 1,
                 "explain": "الإيميل غير الموثّق عند الـIdP مش دليل ملكية. الربط الأعمى من أشهر ثغرات OAuth العملية."},
                {"q": "`RefreshToken` اختفى بعد إعادة تشغيل الجلسة. أرجح سبب؟",
                 "options": [
                     "الـIdP ما بيدعمش التجديد",
                     "ما طلبتش scope `offline_access` (أو ما فعّلتش `SaveTokens`)",
                     "PKCE معطل",
                     "الكوكي كبير",
                 ], "answer": 1,
                 "explain": "`offline_access` هو اللي بيخلي الـIdP يصدر refresh token. و`SaveTokens=true` لازم عشان يتخزن مع الكوكي."},
                {"q": "إلغاء ربط المزوّد الوحيد لحساب بلا كلمة سر — أنهي تصرف؟",
                 "options": [
                     "نفّذ الإلغاء",
                     "ارفض بـ409 واطلب إضافة وسيلة دخول بديلة أولًا",
                     "احذف الحساب",
                     "أنشئ كلمة سر عشوائية",
                 ], "answer": 1,
                 "explain": "منع فقدان الوصول أهم من المرونة. (وكمان: أبطل الجلسات والـrefresh tokens بعد أي تغيير في وسائل الدخول.)"},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تسجيل دخول خارجي كامل",
                 "md": "أضف مزوّدًا واحدًا (Google أو Keycloak محلي أو Entra ID تجريبي) لمشروعك: challenge → callback → ربط بحساب Identity → إصدار توكناتك الخاصة. وطبّق كل شروط الأمان من الدرس.",
                 "criteria": [
                     "`email_verified` مطلوب قبل أي ربط تلقائي بحساب موجود",
                     "`returnUrl`/`RedirectUri` بفحص `IsLocalReturn` (اختبار يرفض `https://evil.example`)",
                     "كوكي الجلسة HttpOnly + Secure + SameSite=Lax",
                     "logout يبطل الكوكي المحلي ويسجّل الخروج من الـIdP",
                     "لا توجد توكنات في اللوجات أو في الروابط (راجع سجل الطلبات)",
                 ],
                 "hint": "للتجربة بلا حساب سحابي: شغّل Keycloak بـTestcontainers (من درس المرحلة 1) وأضفه كمزوّد OIDC — بيئة كاملة تحت سيطرتك."},
                {"id": "t2", "title": "إلغاء ربط + إبطال الجلسات",
                 "md": "نفّذ `/unlink/{provider}` مع رفض 409 لو هيفقد المستخدم كل وسائل الدخول، وإبطال refresh tokens وSecurity Stamp. اكتب اختبارين: نجاح الإلغاء مع وجود كلمة سر، ورفض 409 بدونها.",
                 "criteria": [
                     "حالة 409 مختبرة",
                     "بعد الإلغاء الناجح: التوكنات القديمة مرفوضة",
                     "الحساب لسه ممكن يدخل بكلمة السر أو مزوّد آخر",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "OpenID Connect on ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/signin-with-oidc"},
                {"label": "External login providers setup", "url": "https://learn.microsoft.com/aspnet/core/security/authentication/social/"},
                {"label": "Microsoft.Identity.Web", "url": "https://learn.microsoft.com/entra/identity-platform/microsoft-identity-web"},
                {"label": "OpenID Connect Core 1.0", "url": "https://openid.net/specs/openid-connect-core-1_0.html"},
                {"label": "OAuth 2.1 draft", "url": "https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1"},
                {"label": "OWASP ASVS", "url": "https://owasp.org/www-project-application-security-verification-standard/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l5
    {
        "id": "s2-m2-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
تأمين الـAPI مش ميزة إضافية — ده مجموعة إعدادات صغيرة، **مقصودة**، ومختبرة. أغلب الاختراقات اللي بتحصل
لأنظمة حقيقية مش ثغرات غامضة: إعدادات افتراضية، أسرار في الـrepo، CORS مفتوح، رسائل خطأ كاشفة،
ومسارات تطوير منسية في الإنتاج.

الدرس ده: رؤوس الأمان، CORS، HTTPS/HSTS، إدارة الأسرار، وقائمة OWASP API Top 10 بتطبيقاتها العملية في ASP.NET Core.
"""},
            {"type": "terms", "items": [
                {"term": "Security Headers", "def": "رؤوس استجابة توجّه المتصفح: CSP، nosniff، frame-ancestors، referrer-policy، permissions-policy."},
                {"term": "HSTS", "def": "`Strict-Transport-Security`: يخلي المتصفح يرفض HTTP عادي للنطاق لمدة محددة."},
                {"term": "CORS", "def": "آلية المتصفح للسماح بطلبات من أصل مختلف. **ليست حماية للخادم** — أي عميل غير متصفح يتجاهلها."},
                {"term": "Preflight", "def": "طلب `OPTIONS` مسبق للطلبات «غير البسيطة». نتيجته قابلة للكاش."},
                {"term": "Managed Identity", "def": "هوية مُدارة في Azure — بلا secret ولا connection string في الكود."},
                {"term": "User Secrets", "def": "تخزين أسرار التطوير خارج الـrepo (`~/.microsoft/usersecrets/`)."},
                {"term": "BOLA / BFLA", "def": "كسر تفويض مستوى الكائن (مورد مش بتاعك) ومستوى الوظيفة (عملية مش من دورك)."},
                {"term": "SSRF", "def": "خداع خادمك ليجلب عنوانًا يختاره المهاجم (شبكات داخلية، metadata endpoints)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) رؤوس الأمان + HTTPS"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Security/SecurityHeaders.cs", "title": "Middleware صغير، أثر كبير", "code": r'''
public static class SecurityHeaders
{
    /// <summary>
    /// رؤوس لـJSON API. لو بتقدّم HTML من نفس النطاق، الـCSP يحتاج تضييقًا مختلفًا
    /// (واستثنِ مسارات الواجهة التفاعلية في التطوير).
    /// </summary>
    public static IApplicationBuilder UseSecurityHeaders(this IApplicationBuilder app) =>
        app.Use(async (ctx, next) =>
        {
            var headers = ctx.Response.Headers;

            headers["X-Content-Type-Options"] = "nosniff";                  // لا تخمين لنوع المحتوى
            headers["X-Frame-Options"] = "DENY";                            // منع clickjacking
            headers["Referrer-Policy"] = "no-referrer";                     // لا تسريب لمسارات في Referer
            headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()";
            headers["Cross-Origin-Resource-Policy"] = "same-origin";
            headers["Cross-Origin-Opener-Policy"] = "same-origin";
            headers["Cache-Control"] = "no-store";                          // استجابات API فيها بيانات مستخدم
            headers["Pragma"] = "no-cache";

            // CSP لـAPI: لا مصادر خارجية ولا تنفيذ سكربتات
            headers["Content-Security-Policy"] =
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

            await next();
        });

    /// <summary>إخفاء بصمة الخادم (لا تفيد المهاجم بمعلومة إصدار).</summary>
    public static IWebHostBuilder HideServerHeader(this IWebHostBuilder host) =>
        host.ConfigureKestrel(options => options.AddServerHeader = false);
}

// Program.cs
builder.WebHost.HideServerHeader();

builder.Services.AddHsts(options =>
{
    options.MaxAge = TimeSpan.FromDays(365);
    options.IncludeSubDomains = true;
    options.Preload = true;                    // أضف النطاق لقائمة preload بعد التأكد من HTTPS لكل شيء
});
builder.Services.AddHttpsRedirection(options => options.HttpsPort = 443);

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseHsts();                              // ✓ إنتاج فقط: في التطوير بيلخبط localhost
    app.UseHttpsRedirection();
}
app.UseSecurityHeaders();
app.UseExceptionHandler(string.Empty);         // لا stack traces للعميل
'''},
            {"type": "callout", "kind": "note", "title": "TLS: الإعدادات الدنيا المقبولة",
             "md": """
- اقبل **TLS 1.2 و1.3 فقط** (عطّل 1.0/1.1). على Kestrel: `options.ConfigureHttpsDefaults(h => h.SslProtocols = SslProtocols.Tls12 | SslProtocols.Tls13)`.
- الشهادات من Let's Encrypt / Key Vault / خدمة الشهادات المُدارة، مع **تجديد تلقائي**.
- افحص من الخارج بعد النشر: [SSL Labs](https://www.ssllabs.com/ssltest/) أو `nmap --script ssl-enum-ciphers`.
- `RequireHttpsMetadata = true` في JwtBearer/OIDC — لا تعطّلها إلا في تطوير محلي موثّق ومؤقت.
"""},
            {"type": "heading", "level": 2, "text": "2) CORS: مقصود وضيّق"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Security/CorsSetup.cs", "title": "أصول صريحة من الإعدادات — لا `AllowAnyOrigin` أبدًا", "code": r'''
public static IServiceCollection AddApiCors(this IServiceCollection services, IConfiguration config)
{
    var origins = config.GetSection("Cors:Origins").Get<string[]>() ?? [];
    if (origins.Length == 0)
        throw new InvalidOperationException("Cors:Origins فاضي — حدّد الأصول المسموحة صراحةً");

    services.AddCors(options =>
    {
        options.AddPolicy("spa", policy => policy
            .WithOrigins(origins)                              // ✓ قائمة صريحة
            .WithMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
            .WithHeaders("Authorization", "Content-Type", "X-Correlation-Id", "Idempotency-Key")
            .WithExposedHeaders("X-Correlation-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining",
                                "X-RateLimit-Reset", "Retry-After", "Location", "Deprecation", "Sunset")
            .AllowCredentials());                              // ✓ مسموح لأن الأصول صريحة

        // لو محتاج subdomains موثوقة: اكتب الأصل بصيغة wildcard واستخدم
        // .WithOrigins("https://*.example.com").SetIsOriginAllowedToAllowWildcardSubdomains()
        // (بلا wildcards السطر ده ما لهوش أثر — خلي القائمة صريحة ما أمكن)
    });

    return services;
}

// Program.cs — الترتيب مهم: بعد الـrouting وقبل الـauthorization
app.UseCors("spa");
'''},
            {"type": "code", "lang": "json", "filename": "appsettings.Production.json", "title": "الأصول من الإعدادات (لا من الكود)", "code": r'''
{
  "Cors": {
    "Origins": [
      "https://app.example.com",
      "https://admin.example.com"
    ]
  }
}
'''},
            {"type": "callout", "kind": "danger", "title": "التركيب القاتل: `AllowAnyOrigin` + `AllowCredentials`",
             "md": """
أي موقع على الإنترنت يقدر ينادي الـAPI بتاعك **بكوكيز المستخدم**. المتصفح هيقبل لو الـAPI رجّع
`Access-Control-Allow-Origin: <origin الطالب>` مع `Allow-Credentials: true` — وده بالظبط اللي بيعمله
الانعكاس الديناميكي للأصول.

القواعد:
1. **أصول صريحة من الإعدادات** — لا `AllowAnyOrigin()` مع credentials، ولا انعكاس لرأس `Origin` بدون whitelist.
2. لو الـAPI عام بلا بيانات مستخدم (مثال: بيانات أسعار) → `AllowAnyOrigin()` **بدون** credentials.
3. **CORS مش أمان للخادم**: أي أداة (curl، خدمة خلفية) بتتجاهله. التفويض الحقيقي في التوكن والسياسات.
"""},
            {"type": "heading", "level": 2, "text": "3) الأسرار: لا شيء في الـrepo"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الترتيب حسب البيئة", "code": r'''
# ── تطوير محلي: user-secrets (خارج الـrepo)
dotnet user-secrets init --project Shop.Api
dotnet user-secrets set "ConnectionStrings:Default" "Host=localhost;Database=shop_dev;Username=dev;Password=dev" --project Shop.Api
dotnet user-secrets set "AuthToken:PrivateKeyPem" "$(cat ./dev-key.pem)" --project Shop.Api

# ── CI: GitHub Actions secrets (مش متغيرات مكشوفة)
#   Repository → Settings → Secrets and variables → Actions

# ── إنتاج Azure: Key Vault + Managed Identity (بلا أي secret في الكود)
az keyvault secret set --vault-name shop-kv --name ConnectionStrings--Default --value "$CONN"

# ── فحص تسريب الأسرار (محليًا وفي CI)
grep -rEn "(password|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}" --include="*.json" --include="*.cs" --include="*.yml" . \
  || echo "clean ✅"
dotnet list package --vulnerable --include-transitive
dotnet list package --deprecated
'''},
            {"type": "code", "lang": "csharp", "title": "تحميل الأسرار من Key Vault في الإنتاج", "code": r'''
using Azure.Identity;
using Azure.Extensions.AspNetCore.Configuration.Secrets;

var builder = WebApplication.CreateBuilder(args);

if (builder.Environment.IsProduction())
{
    var vaultUrl = builder.Configuration["KeyVault:Url"]
        ?? throw new InvalidOperationException("KeyVault:Url مطلوب في الإنتاج");

    // DefaultAzureCredential → Managed Identity في Azure، وبلا أسرار في الكود أو الإعدادات
    builder.Configuration.AddAzureKeyVault(new Uri(vaultUrl), new DefaultAzureCredential());
}

// تحقق مبكر عند الإقلاع: فشل واضح بدل سلوك غريب وقت التشغيل
builder.Services.AddOptions<AuthTokenOptions>()
    .Bind(builder.Configuration.GetSection("AuthToken"))
    .Validate(o => !string.IsNullOrWhiteSpace(o.PrivateKeyPem), "AuthToken:PrivateKeyPem مفقود")
    .Validate(o => o.AccessTokenLifetime <= TimeSpan.FromMinutes(30), "عمر access token طويل جدًا")
    .ValidateOnStart();                                    // ← يفشل النشر فورًا لو فيه خطأ إعداد
'''},
            {"type": "heading", "level": 2, "text": "4) OWASP API Security Top 10 → تنفيذ عملي"},
            {"type": "table", "head": ["الخطر (2023)", "مظهره", "التنفيذ في ASP.NET Core"], "rows": [
                ["API1: BOLA", "`/orders/123` يرجّع طلب مستخدم آخر", "resource-based authorization على المورد المحمّل + `ICurrentUser` بدل معرّف من الطلب"],
                ["API2: Broken Authentication", "تخمين كلمات السر، توكنات طويلة العمر، endpoints مصادقة بلا حدود", "lockout + rate limiting على `/login` + access token 5-15 دقيقة + refresh rotation"],
                ["API3: Object Property Authorization", "mass assignment: العميل يبعت `role: admin` أو `isVerified: true`", "DTOs صريحة للكتابة منفصلة عن القراءة — لا تربط كيانات EF مباشرة"],
                ["API4: Unrestricted Resource Consumption", "طلبات ضخمة/متكررة تستهلك القاعدة", "rate limiting + `size ≤ 100` + `MaxRequestBodySize` + timeout على HttpClient + فهارس"],
                ["API5: BFLA", "مستخدم عادي ينادي `/admin/users`", "سياسات تفويض على **كل** endpoint (مش بس الواجهة)، واختبارات 403"],
                ["API6: Sensitive Business Flows", "شراء/تسجيل/استرجاع بلا حدود → bots", "حدود تدفق + تحقق من النوايا (captcha/OTP) + مراقبة أنماط"],
                ["API7: SSRF", "endpoint بيجيب URL من العميل", "whitelist للنطاقات + منع IP الخاصة/metadata + `IHttpClientFactory` بسياسات"],
                ["API8: Security Misconfiguration", "CORS مفتوح، رؤوس افتراضية، رسائل خطأ كاشفة، مسار dev في الإنتاج", "قائمة الفحص أدناه + `UseSecurityHeaders` + `IExceptionHandler` + فحص بيئات"],
                ["API9: Improper Inventory Management", "إصدارات قديمة شغالة، endpoints منسية، بيئة staging مكشوفة", "versioning + `Deprecation`/`Sunset` + مراجعة المسارات + عزل البيئات"],
                ["API10: Unsafe Consumption of APIs", "ثقة عمياء في رد خدمة خارجية", "تحقق من المخطط + timeouts + circuit breaker (Polly) + عزل الأخطاء"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Security/SsrfGuard.cs", "title": "مثال API7: منع SSRF عند جلب URL من العميل", "code": r'''
public static class UrlGuard
{
    private static readonly string[] AllowedHosts = ["cdn.example.com", "images.partner.example"];

    /// <summary>
    /// يرفض: نطاقات غير مسجلة، IP مباشرة، عناوين خاصة/محلية، ومسارات الـmetadata السحابية.
    /// </summary>
    public static bool IsAllowedFetch(string? url)
    {
        if (!Uri.TryCreate(url, UriKind.Absolute, out var uri)) return false;
        if (uri.Scheme != Uri.UriSchemeHttps) return false;

        // ✓ whitelist للنطاق — لا فحص "ليس محليًا" فقط (الهجمات كتيرة بالـDNS rebind)
        if (!AllowedHosts.Contains(uri.Host, StringComparer.OrdinalIgnoreCase)) return false;

        return !System.Net.IPAddress.TryParse(uri.Host, out var ip) || !IsBlockedIp(ip);
    }

    private static bool IsBlockedIp(System.Net.IPAddress ip)
    {
        if (System.Net.IPAddress.IsLoopback(ip)) return true;
        var bytes = ip.GetAddressBytes();
        return bytes.Length switch
        {
            4 => bytes[0] is 10 or 127
              || (bytes[0] == 172 && bytes[1] is >= 16 and <= 31)
              || (bytes[0] == 192 && bytes[1] == 168)
              || (bytes[0] == 169 && bytes[1] == 254),          // ← عنوان metadata السحابي
            6 => bytes[0] == 0xfc || bytes[0] == 0xfd || bytes[0] == 0xfe,
            _ => false,
        };
    }
}

// الاستخدام
group.MapPost("/webhooks/fetch", async (FetchRequest request, IHttpClientFactory http, CancellationToken ct) =>
{
    if (!UrlGuard.IsAllowedFetch(request.Url))
        return TypedResults.BadRequest(new ProblemDetails { Status = 400, Title = "العنوان غير مسموح" });

    using var client = http.CreateClient("external");           // timeout + Polly من إعداد الـclient
    var bytes = await client.GetByteArrayAsync(request.Url, ct);
    return TypedResults.Ok(new FetchResponse(bytes.Length));
});
'''},
            {"type": "code", "lang": "csharp", "title": "API3: DTO منفصل للكتابة (منع mass assignment)", "code": r'''
// ✗ خطر: ربط كيان EF مباشرة — العميل يقدر يبعت IsAdmin/CreatedAt/Total
group.MapPut("/{id:guid}", async (Guid id, Order entity, AppDbContext db) => { /* ... */ });

// ✓ آمن: حقول مقصودة فقط، والباقي من الهوية والحالة الحالية
public sealed record UpdateOrderRequest(string? ShippingNote, DateTimeOffset? PreferredDate);

group.MapPut("/{id:guid}", async (Guid id, UpdateOrderRequest request, AppDbContext db,
                                  ICurrentUser user, CancellationToken ct) =>
{
    var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == id, ct)
                ?? throw new NotFoundException("Order", id);

    if (order.CustomerId != user.UserId && !user.Roles.Contains(Roles.Admin))
        throw new ForbiddenException("Order", id);

    order.ShippingNote = request.ShippingNote;              // تعديل صريح لحقل مسموح
    order.PreferredDate = request.PreferredDate;
    await db.SaveChangesAsync(ct);
    return TypedResults.NoContent();
});
'''},
            {"type": "heading", "level": 2, "text": "5) قائمة فحص ما قبل الإطلاق"},
            {"type": "steps", "title": "راجعها بندًا بندًا على مشروعك", "items": [
                {"title": "لا أسرار في الـrepo",
                 "md": "user-secrets/Key Vault/env vars فقط. شغّل فحص تسريب وأضف `.gitignore` للملفات المحلية. لو سر اتسرب: **دوّره فورًا** (مش بس احذفه من git history)."},
                {"title": "كل endpoint محمي عمدًا",
                 "md": "قائمة بكل المسارات وحالتها (عام/مصادَق/دور). `AllowAnonymous()` لازم يكون قرارًا موثقًا، مش نسيانًا."},
                {"title": "فحص ملكية الموارد",
                 "md": "لكل مسار بيقرأ/يعدّل موردًا مملوكًا: اختبار يثبت إن مستخدم تاني ياخد 403/404."},
                {"title": "حدود على الاستهلاك",
                 "md": "rate limiting على المصادقة والكتابة، `size ≤ 100` في الترقيم، `MaxRequestBodySize`، وtimeouts على كل HttpClient."},
                {"title": "رؤوس وأخطاء آمنة",
                 "md": "لا stack traces، لا تفاصيل داخلية في 500، `problem+json` موحّد مع `traceId`، ورؤوس الأمان مطبقة."},
                {"title": "CORS ضيق ومقصود",
                 "md": "أصول صريحة من الإعدادات، بلا `AllowAnyOrigin` + credentials، وpreflight متوقع."},
                {"title": "HTTPS إجباري",
                 "md": "`UseHttpsRedirection` + HSTS في الإنتاج + TLS 1.2/1.3 فقط + شهادة تتجدد تلقائيًا."},
                {"title": "المسارات الحساسة غير مكشوفة",
                 "md": "`/openapi`، `/scalar`، `/health` التفصيلي، dashboards: خلف مصادقة أو شبكة داخلية. `/health/live` عام، `/health/ready` داخلي."},
                {"title": "الاعتماديات محدثة ومفحوصة",
                 "md": "`dotnet list package --vulnerable --include-transitive` في الـCI + Dependabot/Renovate + سياسة ترقيات."},
                {"title": "تسجيل ومراقبة الأحداث الأمنية",
                 "md": "دخول فاشل، lockout، 403 متكررة، reuse لـrefresh token، تغيير صلاحيات — كلها events بمعرّفات قابلة للربط (correlation id)."},
            ]},
            {"type": "callout", "kind": "tip", "title": "اجعل الأمان قابلًا للاختبار",
             "md": """
كل بند في القائمة أعلاه يقدر يبقى **اختبار آلي** — وده اللي بيخليه يفضل مطبّق بعد سنة:
```csharp
[Fact]
public async Task Responses_include_security_headers()
{
    var client = factory.CreateAuthenticatedClient("customer");
    var response = await client.GetAsync("/api/orders");

    response.Headers.GetValues("X-Content-Type-Options").Should().Contain("nosniff");
    response.Headers.Should().NotContainKey("Server");
}

[Fact]
public async Task Cors_rejects_unknown_origin()
{
    var client = factory.CreateClient();
    client.DefaultRequestHeaders.Add("Origin", "https://evil.example");

    var response = await client.GetAsync("/api/orders");

    response.Headers.TryGetValues("Access-Control-Allow-Origin", out _).Should().BeFalse();
}
```
"""},
            {"type": "checkpoints", "items": [
                "أطبّق رؤوس الأمان وHSTS وTLS الحديث وأخفي بصمة الخادم.",
                "أضبط CORS بأصول صريحة من الإعدادات وأفهم إنه مش حماية للخادم.",
                "أدير الأسرار بـuser-secrets/Key Vault/Managed Identity مع تحقق `ValidateOnStart`.",
                "أراجع OWASP API Top 10 على مشروعي وأحوّل كل بند لاختبار آلي.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه اللي CORS **ما بيعملوش**؟",
                 "options": [
                     "يسمح للمتصفح بقراءة استجابة من أصل آخر",
                     "يمنع عميلًا غير متصفح (curl/خدمة خلفية) من نداء الـAPI",
                     "يتحكم في الـpreflight",
                     "يكشف الرؤوس المسموحة",
                 ], "answer": 1,
                 "explain": "CORS سياسة **متصفح**. الحماية الحقيقية على الخادم هي المصادقة والتفويض والـrate limiting."},
                {"q": "مسار `/scalar` منشور في الإنتاج بلا مصادقة. الخطر؟",
                 "options": [
                     "بطء الصفحة",
                     "كشف كامل لسطح الـAPI (مسارات، معاملات، أدوار) يسهّل الاستطلاع والهجوم",
                     "تعارض CORS",
                     "لا خطر",
                 ], "answer": 1,
                 "explain": "الحل: ولّد المستند وقت البناء ووزّعه، أو اعرضه خلف مصادقة/شبكة داخلية، أو عطّله في الإنتاج تمامًا."},
                {"q": "mass assignment بيحصل إزاي في Minimal APIs؟",
                 "options": [
                     "من ربط كيان Domain/EF مباشرة كمعامل في الـendpoint (العميل يبعت حقولًا ما قصدتهاش)",
                     "من استخدام DTOs",
                     "من JSON كبير",
                     "من CORS",
                 ], "answer": 0,
                 "explain": "الحل: DTO منفصل للكتابة بحقول مقصودة فقط، والتعديل الصريح على الحقول المسموحة."},
                {"q": "سر اتسرب في commit قديم وحذفته من الكود. كفاية؟",
                 "options": [
                     "أيوه بعد `git filter-repo`",
                     "لأ: السر لسه في التاريخ وممكن يكون اتنسخ — لازم **تدوير السر** فورًا مع الحذف",
                     "أيوه لو الـrepo خاص",
                     "أيوه بعد إعادة النشر",
                 ], "answer": 1,
                 "explain": "افترض إن السر اتسرب واستُخدم. التدوير هو الإجراء الحاسم؛ التنظيف من التاريخ إجراء تكميلي."},
                {"q": "ليه `ValidateOnStart()` مفيدة أمنيًا؟",
                 "options": [
                     "تسرّع الإقلاع",
                     "تفشل النشر فورًا لو إعداد أمني ناقص (مفتاح، عمر توكن) بدل ما تشتغل بوضع ضعيف صامت",
                     "تمنع الطلبات",
                     "تولد المفاتيح",
                 ], "answer": 1,
                 "explain": "الإعداد الخاطئ اللي يعدي بصمت = ثغرة شغالة لأسابيع. الفشل المبكر في الـdeployment أفضل بكتير."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تقوية مشروعك",
                 "md": "طبّق `UseSecurityHeaders` + `HideServerHeader` + HSTS/HTTPS (إنتاج) + CORS بأصول من الإعدادات + نقل كل الأسرار لـuser-secrets/Key Vault مع `ValidateOnStart`. وحوّل 4 بنود على الأقل لاختبارات آلية.",
                 "criteria": [
                     "اختبار يؤكد وجود الرؤوس الأمنية وغياب رأس `Server`",
                     "اختبار يرفض أصلًا غير معروف في CORS",
                     "`grep` على الـrepo لا يجد أي سر (والتحقق مسجل في الملاحظات)",
                     "`ValidateOnStart` يفشل الإقلاع لو مفتاح التوقيع ناقص (جرّبه)",
                     "لا توجد stack traces في أي استجابة 500",
                 ],
                 "hint": "لو HSTS بيعطّل localhost عندك: خلي `UseHsts()` داخل `if (!IsDevelopment())` — وده بالظبط ما عملناه في الكود."},
                {"id": "t2", "title": "تدقيق OWASP API Top 10",
                 "md": "املأ جدول تدقيق للعشرة مخاطر على مشروعك: لكل بند اكتب الحالة (محمي/جزئي/مكشوف)، الدليل (اختبار أو كود)، وخطة الإصلاح. ركّز على API1/API3/API4/API5 لأنها الأكثر حدوثًا.",
                 "criteria": [
                     "10 بنود بحالة ودليل لكل بند",
                     "اختبار آلي واحد على الأقل لكل من BOLA وBFLA",
                     "حد أقصى لحجم الطلب والترقيم مطبق ومختبر",
                     "خطة إصلاح بترتيب أولوية (الأخطر أولًا) مع تواريخ",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "OWASP API Security Top 10", "url": "https://owasp.org/www-project-api-security/"},
                {"label": "Enforce HTTPS in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/security/enforcing-ssl"},
                {"label": "Enable CORS in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/security/cors"},
                {"label": "Safe storage of app secrets in development", "url": "https://learn.microsoft.com/aspnet/core/security/app-secrets"},
                {"label": "MDN — HTTP security headers", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security"},
                {"label": "OWASP Cheat Sheets", "url": "https://cheatsheetseries.owasp.org/"},
            ]},
        ],
    },
]
