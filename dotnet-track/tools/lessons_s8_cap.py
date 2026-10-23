# -*- coding: utf-8 -*-
"""Stage 8 — module 3: s8-m3-l1 (Capstone: full-stack بمصادقة ومراقبة)."""

TODAY = "2026-10-22"

_CAP = {
    "id": "s8-m3-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الـCapstone بتاع المرحلة 8 هو **الامتحان النهائي على كل حاجة قبل كده**: API من المرحلة 2 · قاعدة بيانات وفهارس من 3 · معمارية من 4 · رسائل من 5 · حاويات ونشر من 6 · مراقبة وأمان من 7 · وواجهة من 8.\n\n**الهدف:** تطبيق **يعمل end-to-end** — مستخدم بيسجّل دخول، بيشوف بياناته، بيعدّلها، وكل حاجة متتبَّعة بـtrace واحد من المتصفح للقاعدة، ومنشورة على Azure بـCI/CD. **6 ساعات موزّعة على 8 جلسات.** لو خلّصته، عندك مشروع واحد يغطّي 80% من كلام السيرة الذاتية."},

        # ①
        {"type": "heading", "level": 2, "text": "① النطاق: اللي مطلوب واللي ممنوع"},
        {"type": "table", "caption": "حدود المشروع — التزم بها حرفيًا (النطاق المفتوح = مشروع مش بيخلص)",
         "head": ["مطلوب ✅", "ممنوع ❌ (في هذا الـCapstone)"],
         "rows": [
             ["**كيان واحد رئيس** + كيان تابع (مثال: `Order` + `OrderLine`)", "ميكروسيرفيسز متعددة — مشروع واحد بـmodular monolith كافٍ"],
             ["5–7 endpoints REST مع OpenAPI 3.1", "أي شاشة إدارة كاملة لكل كيان"],
             ["مصادقة **OIDC** بواجهة (BFF أو SPA) + سياسة تفويض واحدة على الأقل", "نظام صلاحيات كامل (RBAC متعدد المستويات)"],
             ["EF Core 10 + PostgreSQL + migrations + فهرسين مبرّرين", "أي NoSQL/بحث/كاش موزّع (إلا لو عندك سبب مقاس)"],
             ["واجهة واحدة (Blazor **أو** React): 3 صفحات (دخول · قائمة · تفاصيل/تعديل)", "تصميم UI متقدم — استخدم Tailwind/Bootstrap جاهز"],
             ["OpenTelemetry (traces + metrics + logs) + Serilog JSON + `/health` + `/alive`", "لوحات Grafana كاملة — يكفي trace واحد مترابط + 3 استعلامات"],
             ["اختبارات: 15+ وحدة · 4 تكامل · اختبار مصادقة واحد", "اختبارات E2E كاملة للمتصفح"],
             ["Docker multi-stage + صورة chiseled + نشر على ACA + GitHub Actions بـOIDC", "Kubernetes · Terraform · Bicep **والاثنان معًا**"],
             ["README + ADR واحد + مخطط معمارية", "توثيق شامل لكل ملف"],
         ]},

        # ②
        {"type": "heading", "level": 2, "text": "② المعمارية: 5 مكوّنات فقط"},
        {"type": "code", "lang": "text", "title": "خريطة المكوّنات", "filename": "docs/architecture.txt", "code": r'''
   ┌─────────────────┐   HTTPS    ┌──────────────────────────────┐
   │  المتصفح        │ ─────────► │  App (ACA)                    │
   │  Blazor/React   │            │  ├─ BFF: /bff/login /bff/user │
   └─────────────────┘            │  ├─ API: /api/orders …        │
                                  │  ├─ /health /alive            │
     ┌──────────────┐             │  └─ OTel → OTLP               │
     │  Entra ID    │ ◄── OIDC ───┤                               │
     │  (المزوّد)   │  PKCE/Code  └──────────────┬───────────────┘
     └──────────────┘                             │ EF Core 10
                                                  ▼
                                       ┌────────────────────┐
                                       │ PostgreSQL (ACA)   │
                                       │ + migrations + bk  │
                                       └────────────────────┘

  Observability: OTLP → (Aspire Dashboard محليًا) / Application Insights أو
  أي OTLP backend في السحابة. serilog → stdout JSON (Container Apps logs).
'''},
        {"type": "code", "lang": "bash", "title": "هيكل الحل + أوامر الإنشاء", "filename": "docs/setup.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

# 1) الحل: 4 مشاريع فقط
dotnet new sln -n Shop
dotnet new webapi   -n Shop.Api        -o src/Shop.Api
dotnet new blazor   -n Shop.Web        -o src/Shop.Web      # أو npm create vite@latest web -- --template react-ts
dotnet new xunit3   -n Shop.Api.Tests  -o tests/Shop.Api.Tests
dotnet new classlib -n Shop.Domain     -o src/Shop.Domain

dotnet sln add src/Shop.Api src/Shop.Web src/Shop.Domain tests/Shop.Api.Tests

# 2) الحزم الأساسية
dotnet add src/Shop.Api package Microsoft.EntityFrameworkCore.Npgsql
dotnet add src/Shop.Api package Microsoft.AspNetCore.Authentication.OpenIdConnect
dotnet add src/Shop.Api package Serilog.AspNetCore
dotnet add src/Shop.Api package Serilog.Formatting.Compact
dotnet add src/Shop.Api package Serilog.Sinks.OpenTelemetry
dotnet add src/Shop.Api package Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore
dotnet add src/Shop.Api package OpenTelemetry.Extensions.Hosting
dotnet add src/Shop.Api package OpenTelemetry.Instrumentation.AspNetCore
dotnet add src/Shop.Api package OpenTelemetry.Instrumentation.Http
dotnet add src/Shop.Api package OpenTelemetry.Instrumentation.Runtime
dotnet add src/Shop.Api package OpenTelemetry.Exporter.OpenTelemetryProtocol
dotnet add tests/Shop.Api.Tests package Testcontainers.PostgreSql
dotnet add tests/Shop.Api.Tests package NSubstitute
dotnet add tests/Shop.Api.Tests package Shouldly

# 3) قاعدة بيانات محلية (6.2: compose للتطوير)
cat > compose.yaml <<'EOF'
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD: dev-only-password
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop -d shop"]
      interval: 5s
      retries: 10
EOF
docker compose up -d db

# 4) أول migration
dotnet ef migrations add Initial -p src/Shop.Api
dotnet ef database update -p src/Shop.Api

echo "شغّل: dotnet run --project src/Shop.Api"
echo "الـAPI: http://localhost:5080  ·  OpenAPI: /openapi/v1.json"
'''},

        # ③
        {"type": "heading", "level": 2, "text": "③ المصادقة: BFF + سياسة تفويض"},
        {"type": "code", "lang": "csharp", "title": "Shop.Api/Program.cs — OIDC (code+PKCE) + كوكي + سياسات + حماية CSRF", "filename": "src/Shop.Api/Program.cs", "code": r'''using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// ── قاعدة البيانات ────────────────────────────────────────────────
builder.Services.AddDbContext<ShopDbContext>(o =>
    o.UseNpgsql(builder.Configuration.GetConnectionString("Db")));

// ── BFF: OIDC على الخادم، المتصفح يشوف كوكي فقط (8.1.2) ──────────
builder.Services
    .AddAuthentication(o =>
    {
        o.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
        o.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
    })
    .AddCookie(o =>
    {
        o.Cookie.Name = "__Host-shop";        // يفرض Secure + Path=/ + بلا Domain
        o.Cookie.HttpOnly = true;
        o.Cookie.SameSite = SameSiteMode.Lax; // كافٍ مع ترويسة CSRF للطلبات المعدّلة
        o.Cookie.SecurePolicy = CookieSecurePolicy.Always;
        o.SlidingExpiration = false;
        o.ExpireTimeSpan = TimeSpan.FromHours(8);
        o.Events.OnValidatePrincipal = SessionValidator.ValidateAsync; // جلسة ملغاة؟
    })
    .AddOpenIdConnect(o =>
    {
        o.Authority = builder.Configuration["Oidc:Authority"];
        o.ClientId = builder.Configuration["Oidc:ClientId"];
        o.ClientSecret = builder.Configuration["Oidc:ClientSecret"]; // confidential: في Key Vault
        o.ResponseType = "code";
        o.UsePkce = true;                     // إلزامي (RFC 9700)
        o.SaveTokens = true;                  // التوكنات في الخادم لا في المتصفح
        o.GetClaimsFromUserInfoEndpoint = true;
        o.Scope.Clear();
        o.Scope.Add("openid"); o.Scope.Add("profile"); o.Scope.Add("shop.api");
        o.TokenValidationParameters.NameClaimType = "name";
        o.MapInboundClaims = false;
        o.Events.OnTokenValidated = ClaimsMapper.MapAsync;  // دور التطبيق من الأدوار
    });

// ── التفويض: سياسة واحدة على الأقل ────────────────────────────────
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("CanManageOrders", p => p
        .RequireAuthenticatedUser()
        .RequireClaim("role", "orders.write"));

// ── مراقبة (7.1) ─────────────────────────────────────────────────
builder.Services.AddObservability(builder.Configuration, builder.Environment);

// ── API ──────────────────────────────────────────────────────────
builder.Services.AddProblemDetails();
builder.Services.AddOpenApi();
builder.Services.AddAntiforgery();        // للطلبات المعدّلة من الواجهة

var app = builder.Build();

app.UseExceptionHandler();                // → ProblemDetails موحّد (2.2.3)
app.UseSecurityHeaders();                 // CSP · HSTS · X-Content-Type-Options (7.2.3)
app.UseSerilogRequestLogging();
app.UseAuthentication();
app.UseAuthorization();
app.UseAntiforgery();

app.MapOpenApi();
app.MapObservabilityEndpoints();          // /health /alive /metrics

// ── نقاط الـBFF ──────────────────────────────────────────────────
app.MapGet("/bff/user", (HttpContext ctx) => ctx.User.Identity?.IsAuthenticated == true
    ? Results.Ok(new
    {
        isAuthenticated = true,
        name = ctx.User.Identity!.Name,
        roles = ctx.User.FindAll("role").Select(c => c.Value).ToArray(),
    })
    : Results.Ok(new { isAuthenticated = false, name = (string?)null, roles = Array.Empty<string>() }))
   .AllowAnonymous();

app.MapGet("/bff/login", (string? returnUrl, HttpContext ctx) =>
{
    // ✅ منع open redirect: مسارات نسبية فقط (8.1.2)
    var target = IsSafeLocal(returnUrl) ? returnUrl! : "/";
    return Results.Challenge(new AuthenticationProperties { RedirectUri = target },
        [OpenIdConnectDefaults.AuthenticationScheme]);
});

app.MapPost("/bff/logout", async (HttpContext ctx) =>
{
    await ctx.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    await ctx.SignOutAsync(OpenIdConnectDefaults.AuthenticationScheme, new AuthenticationProperties
    {
        RedirectUri = "/",
    });
});

// ── نقاط الـAPI (محمية) ──────────────────────────────────────────
app.MapOrdersEndpoints();

app.Run();

static bool IsSafeLocal(string? url) =>
    !string.IsNullOrWhiteSpace(url) && url.StartsWith('/') && !url.StartsWith("//");
'''},
        {"type": "callout", "kind": "warn", "title": "4 تفاصيل مصادقة تُغفَل وتكلّف ساعات",
         "md": "**① `__Host-` prefix** يحتاج `Secure` + `Path=/` + **بلا `Domain`** — لو حددت Domain، الكوكي بيُرفض.\n**② `MapInboundClaims = false`** يمنعك من رؤية `http://schemas.microsoft.com/...` كأسماء مطوّلة؛ بس لازم تقرأ الـclaims بأسمائها الأصلية.\n**③ الـlogout يحتاج جلسة RP-initiated** — تسجيل خروج من الكوكي بس يخلّي جلسة المزوّد مفتوحة، فالدخول التالي بيمرّ بلا كلمة سر.\n**④ `SameSite=Lax` + ترويسة CSRF** — كفيل عادةً، لكن أي endpoint معدّل لازم `app.UseAntiforgery()` وإرسال `RequestVerificationToken`."},

        # ④
        {"type": "heading", "level": 2, "text": "④ الـAPI: نقطة واحدة كاملة كمرجع (BFF موثّق بكل طبقاته)"},
        {"type": "code", "lang": "csharp", "title": "Endpoints/OrdersEndpoints.cs — تفويض + idempotency + cursor + مشكلة موحّدة", "filename": "src/Shop.Api/Endpoints/OrdersEndpoints.cs", "code": r'''using System.Security.Claims;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

public static class OrdersEndpoints
{
    public static void MapOrdersEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orders").RequireAuthorization();

        group.MapGet("/", async (ShopDbContext db, ClaimsPrincipal user,
            [FromQuery] string? cursor, [FromQuery] int? limit, CancellationToken ct) =>
        {
            var take = Math.Clamp(limit ?? 20, 1, 100);
            var ownerId = user.GetSubjectId();

            var query = db.Orders
                .AsNoTracking()
                .Where(o => o.OwnerId == ownerId);

            // ترقيم بالمفاتيح: لا OFFSET (3.3) — cursor = CreatedAt|Id
            if (Cursor.TryDecode(cursor, out var after))
            {
                query = query.Where(o => o.CreatedAt < after.CreatedAt
                    || (o.CreatedAt == after.CreatedAt && o.Id.CompareTo(after.Id) < 0));
            }

            var rows = await query
                .OrderByDescending(o => o.CreatedAt).ThenByDescending(o => o.Id)
                .Take(take + 1)
                .Select(o => new OrderSummary(o.Id, o.Status, o.Total, o.Currency, o.CreatedAt))
                .ToListAsync(ct);

            var hasMore = rows.Count > take;
            var page = rows.Take(take).ToList();
            var next = hasMore ? Cursor.Encode(page[^1].CreatedAt, page[^1].Id) : null;

            return TypedResults.Ok(new PageDto<OrderSummary>(page, next));
        });

        group.MapGet("/{id}", async Task<Results<Ok<OrderDto>, NotFound, ForbidHttpResult>> (
            string id, ShopDbContext db, ClaimsPrincipal user, CancellationToken ct) =>
        {
            var row = await db.Orders.AsNoTracking()
                .Where(o => o.Id == id)
                .Select(o => new
                {
                    o.OwnerId,
                    Dto = new OrderDto(o.Id, o.Status, o.Total, o.Currency, o.CreatedAt,
                        o.Lines.Select(l => new LineDto(l.Sku, l.Qty, l.UnitPrice)).ToList()),
                })
                .FirstOrDefaultAsync(ct);

            if (row is null) return TypedResults.NotFound();

            // ✅ فحص الملكية في الخادم (لا يكفي إخفاء الزر في الواجهة)
            var canReadAll = user.HasClaim("role", "orders.read.all");
            if (row.OwnerId != user.GetSubjectId() && !canReadAll) return TypedResults.Forbid();
            return TypedResults.Ok(row.Dto);
        });

        // ✅ كتابة: سياسة + idempotency + تحقق + نتيجة واضحة
        group.MapPost("/", async Task<Results<Created<OrderDto>, ValidationProblem, Conflict<string>>> (
            CreateOrderRequest req, ShopDbContext db, ClaimsPrincipal user,
            [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey, CancellationToken ct) =>
        {
            if (Validate(req) is { Count: > 0 } errors)
                return TypedResults.ValidationProblem(errors);

            if (string.IsNullOrWhiteSpace(idempotencyKey) || idempotencyKey.Length > 64)
                return TypedResults.Conflict("Idempotency-Key مطلوب (≤64 حرفًا)");

            // ① نفس المفتاح لمستخدم آخر = مرفوض
            var existing = await db.IdempotencyRecords
                .FirstOrDefaultAsync(r => r.Key == idempotencyKey && r.UserId == user.GetSubjectId(), ct);
            if (existing is not null)
                return TypedResults.Created($"/api/orders/{existing.OrderId}",
                    await LoadDtoAsync(db, existing.OrderId, ct));

            // ② إنشاء + تسجيل المفتاح في **نفس** الترانزاكشن
            var order = Order.Create(user.GetSubjectId(), req.Lines);
            db.Orders.Add(order);
            db.IdempotencyRecords.Add(new IdempotencyRecord(idempotencyKey, user.GetSubjectId(), order.Id,
                DateTimeOffset.UtcNow));

            try { await db.SaveChangesAsync(ct); }
            catch (DbUpdateException ex) when (ex.IsUniqueViolation())
            {
                // ③ سباق: طلب متزامن بنفس المفتاح → أعِد النتيجة بدل خطأ
                var winner = await db.IdempotencyRecords
                    .FirstAsync(r => r.Key == idempotencyKey, ct);
                return TypedResults.Created($"/api/orders/{winner.OrderId}",
                    await LoadDtoAsync(db, winner.OrderId, ct));
            }

            return TypedResults.Created($"/api/orders/{order.Id}",
                await LoadDtoAsync(db, order.Id, ct));
        }).RequireAuthorization("CanManageOrders");

        group.MapPost("/{id}/cancel", async Task<Results<NoContent, NotFound, ProblemHttpResult>> (
            string id, ShopDbContext db, ClaimsPrincipal user, CancellationToken ct) =>
        {
            var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == id, ct);
            if (order is null) return TypedResults.NotFound();

            var result = order.Cancel(user.GetSubjectId());   // منطق النطاق (4.x)
            if (!result.IsSuccess)
                return TypedResults.Problem(result.Error, statusCode: StatusCodes.Status409Conflict);

            await db.SaveChangesAsync(ct);
            return TypedResults.NoContent();
        });
    }

    private static Dictionary<string, string[]> Validate(CreateOrderRequest r) => new()
    {
        ["lines"] = r.Lines.Count == 0 ? ["سطر واحد على الأقل"] : [],
        ["lines[].qty"] = r.Lines.Any(l => l.Qty <= 0) ? ["الكمية يجب أن تكون موجبة"] : [],
        ["lines[].sku"] = r.Lines.Any(l => string.IsNullOrWhiteSpace(l.Sku)) ? ["SKU مطلوب"] : [],
    };
}
'''},
        {"type": "code", "lang": "csharp", "title": "Pagination/Cursor.cs — ترميز/فك المؤشر (bounded، بلا Offset)", "filename": "src/Shop.Api/Pagination/Cursor.cs", "code": r'''using System.Buffers.Text;
using System.Globalization;
using System.Text;

/// <summary>
/// مؤشر ترقيم شفاف: "ticks|id" مُرمّز Base64Url.
/// لا يحتوي أي سر ولا حالة خادم — وله سقف طول لمنع الإساءة.
/// </summary>
public readonly record struct Cursor(DateTimeOffset CreatedAt, string Id)
{
    public static string Encode(DateTimeOffset createdAt, string id) =>
        Base64Url.EncodeToString(Encoding.UTF8.GetBytes(string.Create(
            CultureInfo.InvariantCulture,
            $"{createdAt.UtcTicks}|{id}")));

    public static bool TryDecode(string? value, out Cursor cursor)
    {
        cursor = default;
        if (string.IsNullOrEmpty(value) || value.Length > 200) return false;

        try
        {
            var raw = Encoding.UTF8.GetString(Base64Url.DecodeFromChars(value));
            var sep = raw.IndexOf('|');
            if (sep <= 0) return false;

            if (!long.TryParse(raw[..sep], NumberStyles.None, CultureInfo.InvariantCulture, out var ticks))
                return false;

            var id = raw[(sep + 1)..];
            if (id.Length is 0 or > 64) return false;

            cursor = new Cursor(new DateTimeOffset(ticks, TimeSpan.Zero), id);
            return true;
        }
        catch (FormatException)
        {
            return false;   // مؤشر تالف → ابدأ من البداية بدل 500
        }
    }
}
'''},
        {"type": "callout", "kind": "note", "title": "لماذا هذه النقطة تحديدًا هي «المرجع»",
         "md": "لأنها تجمع **كل قرارات المراحل السابقة في مكان واحد**: ترقيم بالمفاتيح (3.3) · `AsNoTracking` للقراءة · تصفية بالمالك + سياسة (2.2.1) · تحقق قبل القاعدة (2.2.2) · `ProblemDetails`/`ValidationProblem` (2.2.3) · **idempotency** في نفس الترانزاكشن (5.2.5) · منطق نطاق في الكيان لا في الـendpoint (4.x) · و`CancellationToken` في كل استدعاء.\nلو مش فاهم سطر منها، ارجع للدرس المذكور — الـCapstone بيختبر التوليف، مش بيعلّم من جديد."},

        # ⑤
        {"type": "heading", "level": 2, "text": "⑤ الواجهة: 3 صفحات فقط (Blazor أو React)"},
        {"type": "code", "lang": "csharp", "title": "Shop.Web/Pages/Orders.razor — Blazor InteractiveServer + حالة + تحقق", "filename": "src/Shop.Web/Pages/Orders.razor", "code": r'''@page "/orders"
@using Microsoft.AspNetCore.Authorization
@rendermode InteractiveServer
@attribute [Authorize]
@inject IOrdersClient Api
@inject NavigationManager Nav

<PageTitle>الطلبات</PageTitle>

<h1 class="text-xl font-semibold">الطلبات</h1>

@if (_state == UiState.Loading)
{
    <div class="grid gap-2" aria-busy="true">
        @for (var i = 0; i < 3; i++) { <div class="h-14 animate-pulse rounded bg-gray-100"></div> }
    </div>
}
else if (_state == UiState.Error)
{
    <div class="rounded border border-red-300 bg-red-50 p-4" role="alert">
        <p class="font-medium text-red-700">@_error</p>
        <button class="mt-2 rounded border px-3 py-1.5" @onclick="LoadAsync">إعادة المحاولة</button>
    </div>
}
else if (_orders.Count == 0)
{
    <div class="rounded border p-8 text-center text-gray-600">لا طلبات بعد.</div>
}
else
{
    <ul class="grid gap-2">
        @foreach (var o in _orders)
        {
            <li class="flex items-center justify-between rounded border p-3" @key="o.Id">
                <span dir="ltr" class="font-mono text-sm">@o.Id</span>
                <span>@StatusText(o.Status)</span>
                <span dir="ltr" class="tabular-nums">@o.Total.ToString("N2") @o.Currency</span>
                <button class="rounded border px-3 py-1 text-sm"
                        disabled="@(o.Status == "cancelled" || _busyId == o.Id)"
                        @onclick="() => CancelAsync(o.Id)">
                    @(_busyId == o.Id ? "جارٍ الإلغاء…" : "إلغاء")
                </button>
            </li>
        }
    </ul>

    @if (_nextCursor is not null)
    {
        <button class="mt-3 rounded border px-3 py-2 text-sm" disabled="@_loadingMore"
                @onclick="LoadMoreAsync">@(_loadingMore ? "جارٍ التحميل…" : "تحميل المزيد")</button>
    }
}

<p class="mt-6">
    <a href="/orders/new" class="rounded bg-blue-600 px-3 py-2 text-white">طلب جديد</a>
</p>

@code {
    private enum UiState { Loading, Ready, Error }

    private UiState _state = UiState.Loading;
    private List<OrderSummary> _orders = [];
    private string? _nextCursor;
    private string? _error;
    private string? _busyId;
    private bool _loadingMore;

    protected override Task OnInitializedAsync() => LoadAsync();

    private async Task LoadAsync()
    {
        _state = UiState.Loading;
        _error = null;
        try
        {
            var page = await Api.GetOrdersAsync(cursor: null);
            _orders = page.Items.ToList();
            _nextCursor = page.NextCursor;
            _state = UiState.Ready;
        }
        catch (ApiException ex)
        {
            _error = ex.StatusCode == 401 ? "انتهت الجلسة — سجّل الدخول مرة أخرى."
                                         : "تعذّر تحميل الطلبات.";
            _state = UiState.Error;
        }
    }

    private async Task LoadMoreAsync()
    {
        if (_nextCursor is null) return;
        _loadingMore = true;
        try
        {
            var page = await Api.GetOrdersAsync(_nextCursor);
            _orders.AddRange(page.Items);
            _nextCursor = page.NextCursor;
        }
        finally { _loadingMore = false; }
    }

    private async Task CancelAsync(string id)
    {
        _busyId = id;
        var snapshot = _orders.ToList();
        // تحديث متفائل (8.1.4)
        _orders = _orders.Select(o => o.Id == id ? o with { Status = "cancelled" } : o).ToList();
        try
        {
            await Api.CancelAsync(id);
        }
        catch (ApiException)
        {
            _orders = snapshot;                 // تراجع
            _error = "تعذّر إلغاء الطلب.";
        }
        finally { _busyId = null; }
    }

    private static string StatusText(string status) => status switch
    {
        "paid" => "مدفوع",
        "pending" => "قيد الدفع",
        "cancelled" => "ملغى",
        _ => status,
    };
}
'''},

        # ⑥
        {"type": "heading", "level": 2, "text": "⑥ المراقبة: trace واحد يربط المتصفح بالقاعدة"},
        {"type": "code", "lang": "csharp", "title": "Observability/ServiceCollectionExtensions.cs — OTel + Serilog + health", "filename": "src/Shop.Api/Observability/ServiceCollectionExtensions.cs", "code": r'''using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;
using Serilog.Formatting.Compact;

public static class ObservabilityExtensions
{
    public static IServiceCollection AddObservability(
        this IServiceCollection services, IConfiguration config, IHostEnvironment env)
    {
        // ── Serilog: JSON مضغوط + scrubbing للحقول الحساسة (7.1.3) ──
        services.AddSerilog((sp, lc) => lc
            .ReadFrom.Configuration(config)
            .Enrich.FromLogContext()
            .Enrich.WithProperty("service.name", "shop-api")
            .Enrich.WithProperty("deployment.environment", env.EnvironmentName)
            .WriteTo.Console(new CompactJsonFormatter())
            .WriteTo.OpenTelemetry(o =>
            {
                o.Endpoint = config["Otlp:Endpoint"] ?? "http://localhost:18889";
                o.Protocol = Serilog.Sinks.OpenTelemetry.OtlpProtocol.Grpc;
            }));

        // ── OpenTelemetry: traces + metrics + runtime ──
        services.AddOpenTelemetry()
            .ConfigureResource(r => r
                .AddService(serviceName: "shop-api", serviceVersion: "1.0.0")
                .AddAttributes(new Dictionary<string, object>
                {
                    ["deployment.environment"] = env.EnvironmentName,
                }))
            .WithTracing(t => t
                .AddAspNetCoreInstrumentation(o => o.RecordException = true)
                .AddHttpClientInstrumentation()
                .AddEntityFrameworkCoreInstrumentation(o => o.SetDbStatementForText = false)
                .AddOtlpExporter())        // ⚠️ لا تجمعها مع UseOtlpExporter
            .WithMetrics(m => m
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation()
                .AddRuntimeInstrumentation()
                .AddMeter("Shop.Orders")   // عدّادات الأعمال
                .AddOtlpExporter());

        services.AddSingleton<OrdersMetrics>();
        services.AddHealthChecks()
            .AddDbContextCheck<ShopDbContext>("db")
            .AddCheck("self", () => HealthCheckResult.Healthy());

        return services;
    }

    public static void MapObservabilityEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapHealthChecks("/health");                       // جاهز للحركة
        app.MapHealthChecks("/alive", new()
        {
            Predicate = r => r.Name == "self",                // liveness: بلا قاعدة
        });
        // ملاحظة: مُصدّر Prometheus في OTel .NET ما زال beta (7.1.2) —
        // في الإنتاج فضّل OTLP إلى backend، واستخدم Prometheus فقط لو عندك مكدّس جاهز.
        // app.MapPrometheusScrapingEndpoint();               // يتطلب OpenTelemetry.Exporter.Prometheus.AspNetCore
    }
}

/// <summary>عدّادات أعمال بسيطة — قابلة للإنذار (7.1.4).</summary>
public sealed class OrdersMetrics
{
    public Counter<long> Created { get; }
    public Counter<long> Cancelled { get; }
    public Histogram<double> TotalValue { get; }

    public OrdersMetrics(IMeterFactory factory)
    {
        var meter = factory.Create("Shop.Orders");
        Created   = meter.CreateCounter<long>("orders.created");
        Cancelled = meter.CreateCounter<long>("orders.cancelled");
        TotalValue = meter.CreateHistogram<double>("orders.total_value", unit: "EGP");
    }
}
'''},
        {"type": "code", "lang": "bash", "title": "إثبات الترابط: trace واحد + استعلامان + SLO", "filename": "docs/evidence/observability.md", "code": r'''# إثبات المراقبة (يُرفَق مع التسليم)

## 1) trace واحد end-to-end
# طلب: POST /api/orders  → شوف trace-id في الرد (traceparent) وفي اللوج
curl -s -D - -X POST https://shop.example.com/api/orders \
  -H "Content-Type: application/json" -H "Idempotency-Key: $(uuidgen)" \
  --cookie "__Host-shop=..." -d '{"lines":[{"sku":"A-1","qty":2}]}' | tee /tmp/resp.txt
TRACE=$(grep -i traceparent /tmp/resp.txt | cut -d'-' -f2)
echo "trace=$TRACE"

# في اللوحة: ابحث بالـtrace-id — لازم تشوف:
#   HTTP POST /api/orders (server) → SELECT orders (db) → INSERT orders (db)
#   + أي خروج HTTP (إن وُجد) بنفس الـtrace-id. عدد spans ≥ 4.

## 2) استعلامان يُجابان في < 30 ثانية
# (أ) كم طلبًا فشل في آخر ساعة؟
count_over_time({service_name="shop-api"} |= "status=500" [1h])
# (ب) p95 لزمن الـAPI آخر 6 ساعات
histogram_quantile(0.95, sum(rate(http_server_request_duration_seconds_bucket[6h])) by (le))

## 3) SLO + إنذار
# الهدف: 99.5% نجاح على /api/* خلال 30 يومًا (7.1.5)
# إنذار: p95 > 800ms لمدة 5 دقائق  → ticket (burn 1×)
# إنذار: نسبة خطأ > 2% لمدة 10 دقائق → page (burn 6×)
'''},

        # ⑦
        {"type": "heading", "level": 2, "text": "⑦ النشر: ACA + GH Actions بـOIDC (بلا أسرار)"},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/deploy.yml — build → test → صورة chiseled → ACA", "filename": ".github/workflows/deploy.yml", "code": r'''name: deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write        # OIDC إلى Azure
  contents: read

env:
  ACR: ${{ vars.ACR_NAME }}
  APP: ${{ vars.ACA_APP }}
  RG: ${{ vars.AZURE_RG }}
  IMAGE: ${{ vars.ACR_NAME }}.azurecr.io/shop-api

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "10.0.x"
          cache: true                  # ⚠️ يحتاج packages.lock.json
      - run: dotnet restore --locked-mode
      - run: dotnet build -c Release --no-restore
      - run: dotnet test -c Release --no-build --logger "trx;LogFileName=test.trx"
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: test-results, path: "**/*.trx" }

  deploy:
    needs: build-test
    runs-on: ubuntu-latest
    environment: production             # ← subject: repo:org/repo:environment:production
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.ACR }}.azurecr.io
          username: ${{ secrets.ACR_USER }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build & push (chiseled, non-root UID 1654)
        run: |
          docker build -f src/Shop.Api/Dockerfile \
            -t "$IMAGE:${{ github.sha }}" -t "$IMAGE:latest" .
          docker push "$IMAGE:${{ github.sha }}"
          docker push "$IMAGE:latest"

      - name: Deploy to Container Apps
        run: |
          az containerapp update -n "$APP" -g "$RG" \
            --image "$IMAGE:${{ github.sha }}" \
            --set-env-vars "Otlp__Endpoint=${{ vars.OTLP_ENDPOINT }}" \
            --revision-suffix "r$(git rev-parse --short HEAD)"

      - name: Smoke (health + 401 على API محمي)
        run: |
          FQDN=$(az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
          curl -fsS "https://$FQDN/alive" -o /dev/null || exit 1
          curl -fsS "https://$FQDN/health" -o /dev/null || exit 1
          code=$(curl -s -o /dev/null -w "%{http_code}" "https://$FQDN/api/orders")
          test "$code" = "401" || { echo "الأمان: توقع 401 ووُجد $code"; exit 1; }
'''},
        {"type": "code", "lang": "dockerfile", "title": "src/Shop.Api/Dockerfile — multi-stage + chiseled (6.1)", "filename": "src/Shop.Api/Dockerfile", "code": r'''# ── build ───────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/sdk:10.0-noble AS build
WORKDIR /src
COPY Directory.Packages.props* packages.lock.json* ./
COPY src/Shop.Api/*.csproj src/Shop.Api/
RUN dotnet restore src/Shop.Api/Shop.Api.csproj --locked-mode
COPY src/ src/
RUN dotnet publish src/Shop.Api/Shop.Api.csproj -c Release -o /app/publish \
    --no-restore /p:UseAppHost=false

# ── runtime: chiseled (بلا shell/package manager — سطح هجوم أقل) ──
FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS final
WORKDIR /app
ENV ASPNETCORE_HTTP_PORTS=8080 \
    DOTNET_GCServer=1 \
    DOTNET_TieredPGO=1
COPY --from=build /app/publish .
USER 1654                              # non-root (المستخدم المدمج في chiseled)
EXPOSE 8080
ENTRYPOINT ["dotnet", "Shop.Api.dll"]
'''},

        # ⑧
        {"type": "heading", "level": 2, "text": "⑧ خطة الجلسات الثمانية (6 ساعات)"},
        {"type": "steps", "title": "نفّذ بالترتيب — كل جلسة لها «ناتج» يُثبت",
         "items": [
            {"title": "الجلسة 1 — (45 د) الهيكل والقاعدة", "md": "أنشئ الحل والمشاريع · EF Core + PostgreSQL (compose) · كيانان + migration · seed بيانات تجريبية.\n**الناتج:** `dotnet ef database update` ينجح، و`GET /api/orders` (مؤقتًا بلا مصادقة) يرجّع 20 صفًا."},
            {"title": "الجلسة 2 — (60 د) الـAPI الكامل", "md": "انقل النقاط لـ`MapGroup` محمي · ترقيم cursor · تحقق · `ProblemDetails` · `Idempotency-Key` في نفس الترانزاكشن · سياسة `CanManageOrders`.\n**الناتج:** مجموعة `requests.http` (أو curl) تغطي 8 حالات: نجاح · 400 · 401 · 403 · 404 · 409 · idempotent-replay · cursor."},
            {"title": "الجلسة 3 — (60 د) المصادقة", "md": "OIDC على الخادم (code+PKCE) · كوكي `__Host-` · `/bff/user` · `/bff/login` بمصفاة `returnUrl` · logout RP-initiated · `UseAntiforgery`.\n**الناتج:** تسجيل لقطة/سجل يوضح: زائر → 401 · دخول → 200 · `returnUrl=https://evil.com` → يُتجاهل."},
            {"title": "الجلسة 4 — (60 د) الواجهة", "md": "3 صفحات (قائمة · جديد · تفاصيل/إلغاء) · حالات 4 · تحديث متفائل · ربط `/bff/user` لإظهار الاسم/الأدوار.\n**الناتج:** فيديو 60 ثانية: تصفح، إنشاء طلب، إلغاء، خطأ متعمد (خادم مغلق) وإعادة محاولة."},
            {"title": "الجلسة 5 — (45 د) المراقبة", "md": "Serilog JSON + OTLP · OTel (AspNetCore/HttpClient/EFCore/Runtime) · عدّادات `orders.created` · `/health` و`/alive` بشكل صحيح (liveness بلا قاعدة).\n**الناتج:** trace واحد بـ≥4 spans من المتصفح للـINSERT + صورة اللوحة."},
            {"title": "الجلسة 6 — (60 د) الحاوية والنشر", "md": "Dockerfile multi-stage + chiseled/non-root · تشغيل محلي `docker run` · ACR + ACA (min-scale 0) · متغيرات البيئة والأسرار في Key Vault/RBAC.\n**الناتج:** URL عام يعمل + `docker images` يوضح الحجم (`docker history`)."},
            {"title": "الجلسة 7 — (60 د) CI/CD والاختبارات", "md": "15+ اختبار وحدة · 4 تكامل (Testcontainers) · اختبار مصادقة · GH Actions بـOIDC · smoke test يتحقق من 401.\n**الناتج:** تشغيل أخضر (رابط Run) + لقطة من فشل متعمد (اختبار مكسور) ثم إصلاحه."},
            {"title": "الجلسة 8 — (30 د) التغليف والتوثيق", "md": "README (لقطات · تشغيل بأمرين · قرارات) · ADR واحد · `CAPSTONE.md` بالروابط والأدلة · مراجعة «ماذا لو» مع مقابلة تجريبية لنفسك.\n**الناتج:** مستودع نظيف + `CAPSTONE.md` مكتمل."},
         ]},

        # ⑨
        {"type": "heading", "level": 2, "text": "⑨ الأدلة العشرون (هي اللي هتتقاس)"},
        {"type": "table", "caption": "كل بند = دليل قابل للفحص في 30 ثانية",
         "head": ["#", "الدليل", "أين يوجد", "معيار القبول"],
         "rows": [
             ["1", "`GET /openapi/v1.json` يرجع OpenAPI 3.1", "URL عام", "يظهر في المتصفح + عدد المسارات ≥7"],
             ["2", "زائر → `/api/orders` = **401**", "curl في README", "مخرَج الطلب مرفق"],
             ["3", "مستخدم بلا دور → **403**", "سجل/لقطة", "نفس المستخدم بعد إضافة الدور → 200"],
             ["4", "`returnUrl` خبيث مرفوض", "اختبار وحدة/سجل", "`//evil.com` و`https://evil.com` → `/`"],
             ["5", "idempotency: نفس المفتاح مرتين = **طلب واحد**", "اختبار تكامل", "عدّ الصفوف في القاعدة = 1"],
             ["6", "ترقيم cursor يعمل مع 25 صفًا", "طلبين متتاليين", "لا تكرار ولا فقد بين الصفحتين"],
             ["7", "تحقق: كمية 0 → **400** + `errors`", "طلب/اختبار", "شكل `ValidationProblemDetails`"],
             ["8", "سياسة CSRF: POST بلا ترويسة → 400", "اختبار", "مع الترويسة → 201"],
             ["9", "trace واحد ≥4 spans", "لقطة لوحة", "HTTP → db → db (+ خروج إن وُجد)"],
             ["10", "لوج JSON بلا PII", "عيّنة 20 سطرًا", "لا بريد/اسم/توكن؛ `traceId` موجود"],
             ["11", "`/health` و`/alive` مختلفان", "docker stop db", "`/alive` 200 و`/health` 503"],
             ["12", "مقياس أعمال `orders.created`", "استعلام", "يزداد بعد كل إنشاء"],
             ["13", "صورة chiseled غير جذرية", "`docker inspect`", "`User=1654` · الحجم ≤ 130MB"],
             ["14", "ملف compose للتطوير", "`compose.yaml`", "`docker compose up` يعمل بلا تعديل"],
             ["15", "15+ اختبار وحدة", "`dotnet test`", "أخضر · تغطية منطق النطاق ≥70%"],
             ["16", "4 اختبارات تكامل Testcontainers", "مجلد tests", "تشتغل بلا قاعدة خارجية"],
             ["17", "CI أخضر + Smoke", "رابط workflow", "يفشل عند كسر 401 (إثبات)"],
             ["18", "نشر ACA + دومين", "URL", "HTTPS فقط · HSTS · CSP"],
             ["19", "ADR واحد", "`docs/adr/0001-*.md`", "سياق/بدائل/قرار/عواقب"],
             ["20", "`CAPSTONE.md`", "جذر المستودع", "روابط كل الأدلة أعلاه"],
         ]},

        # ⑩
        {"type": "heading", "level": 2, "text": "⑩ سيناريوهات فشل تختبرها بنفسك"},
        {"type": "table", "caption": "5 تجارب — كل واحدة 3 دقائق",
         "head": ["التجربة", "ما تفعله", "ما يجب أن يحدث", "الخطأ الشائع إذا فشلت"],
         "rows": [
             ["قاعدة متوقفة", "`docker stop` للـdb ثم `GET /api/orders`", "`/alive` 200 · `/health` 503 · الـAPI 503 بـProblemDetails · لا stack trace للمستخدم", "liveness يفشل أيضًا → ACA يعيد تشغيل التطبيق بلا داعٍ"],
             ["طلب مكرر", "نفس `Idempotency-Key` 5 مرات متوازية", "طلب واحد + 4 إجابات 201 بنفس الـid", "5 صفوف في القاعدة (خطأ كارثي في الدفع)"],
             ["جلسة ملغاة", "احذف المستخدم في المزوّد ثم اطلب", "401 + تحويل للدخول (لا 500)", "استعلام كل طلب على المزوّد في المسار الحرج"],
             ["بطء قاعدة", "`pg_sleep` في سيناريو أو قيد اتصال", "p95 يتجاوز SLO → إنذار ticket (وليس page) للمرة الأولى", "إنذار عند كل ارتفاع لحظي (إنذارات آلية متعبة)"],
             ["سر في الصورة", "`docker history` + `grep` على المتغيرات", "لا أسرار: كلها من Key Vault/بيئة ACA", "سلسلة اتصال مكتوبة في `appsettings.Production.json`"],
         ]},
        {"type": "callout", "kind": "danger", "title": "أشهر 6 أخطاء تُفشل الـCapstone",
         "md": "**① تأجيل المصادقة لآخر الجلسات** — بتحوّل كل الاختبارات والـUI لاحقًا؛ اعمل «مستخدم وهمي» في الجلسة 1 واستبدله بـOIDC في 3.\n**② نطاق مفتوح** — كل ميزة إضافية تأخذ ساعتين من اللي محتاجه الأدلة (20 بند). لو زادت عن 3 ساعات: **أعِدها للـbacklog**.\n**③ liveness بيفحص القاعدة** → إعادة تشغيل لا نهائية عند انقطاعها (افصل `/alive`).\n**④ idempotency خارج الترانزاكشن** → طلبان متزامنان = صفان (اختبر 5 متوازية!).\n**⑤ سجلات فيها PII** — تُرفض فورًا في المراجعة؛ استخدم redactor (7.1.3).\n**⑥ نشر بلا smoke** — 401 المتوقع لا يُفحص، فتشحن فتحًا أمنيًا بلا ملاحظة."},

        {"type": "checkpoints", "title": "قائمة التسليم النهائية (DoD)", "items": [
            "المستودع يبني من نسخة نظيفة (`git clone` → `dotnet build` → `docker build`) بلا خطوات سرية مكتوبة.",
            "7 مسارات API على الأقل، منها مسار كتابة محمي بسياسة، ومسارات `/bff/*`.",
            "كل الأخطاء تأتي بـ`application/problem+json` + `traceId` — لا استثناءات مكشوفة.",
            "المصادقة BFF بكوكي `__Host-` + PKCE + تحقق `returnUrl` + logout RP-initiated.",
            "البيانات تُفلتَر بالمالك في الاستعلام، وليس في الواجهة فقط.",
            "كل كتابة تأخذ `Idempotency-Key` مع فحص فريد داخل ترانزاكشن.",
            "القراءات `AsNoTracking`، والتعدادات ذات فهارس مبررة، وترقيم بالمفاتيح لا OFFSET.",
            "trace واحد يربط HTTP → EF Core → أي خروج، ومقاييس أعمال مُصدّرة.",
            "`/alive` مستقل عن القاعدة، `/health` يشمل القاعدة، والاستجابة للفشل مُختبرة.",
            "صورة chiseled، تعمل كـnon-root، حجمها معروف، وبلا أسرار.",
            "CI: build + test + docker + نشر + smoke يتحقق من 401.",
            "15+ وحدة · 4 تكامل · اختبار مصادقة واحد على الأقل — كلها خضراء.",
            "README + ADR + `CAPSTONE.md` بالأدلة العشرين.",
            "قرار مكتوب: ما الذي أقصرته عن قصد، ولماذا (الوقت مقابل القيمة).",
        ]},

        {"type": "tasks", "title": "التسليم", "intro": "مخرج واحد نهائي.",
         "items": [
            {"id": "s8-m3-l1-t1",
             "title": "سلّم Capstone المرحلة 8",
             "md": "طبّق الجلسات الثماني واملأ `CAPSTONE.md` بالأدلة العشرين وروابطها. المراجعة: جرّب كل بند على نسخة نظيفة من المستودع بمفردك ثم مع شخص آخر (أو سجّل فيديو 5 دقائق).",
             "criteria": [
                 "كل بنود DoD أعلاه محققة أو موثّق سبب التقصير.",
                 "الأدلة العشرون كلها موجودة وقابلة للفتح برابط/أمر واحد.",
                 "تشغيل نظيف من الصفر: `git clone` → 3 أوامر → التطبيق يعمل محليًا.",
                 "3 مشاكل حقيقية واجهتها + كيف حللتها (مكتوبة في `docs/lessons-learned.md`).",
                 "تسجيل 5 دقائق: عرض كامل (دخول → إنشاء → إلغاء → trace → نشر).",
                 "مراجعة أمنية سريعة من قائمة 7.2.3: 10 بنود على الأقلين تم فحصها.",
                 "تكلفة شهرية تقديرية مكتوبة (ACA + PostgreSQL + Log Analytics).",
             ],
             "hint": "لو الوقت ضاق: قلّل عدد الصفحات إلى 2 وعدد النقاط إلى 5 — لكن **لا تقلّل الأدلة**: (401 · 403 · idempotency · trace · نشر). أربع ساعات بدون مصادقة أو بدون نشر = مشروع غير صالح للبورتفوليو. وابدأ الجلسة 6 (النشر) مبكرًا لو تقدر — النشر بيكشف مشاكل بيئة لا تظهر محليًا.",
             "solution": "المخرج النموذجي: ~2,500 سطر عبر API + واجهة + اختبارات، وصورة ~110MB تعمل على ACA بـscale-to-zero، وtrace من 6 spans، وREADME بلقطتين. أكبر مكسب تعليمي بيحصل في الجلسة 6 (النشر): مشاكل البيئة/الأسرار/`localhost`/CORS/الشهادات — وهي اللي بتفرّق بين «يعمل عندي» و«يعمل». ثاني مكسب: كتابة `CAPSTONE.md` بأدلة قابلة للفحص — وهي نفسها اللي هتتكلم عنها في المقابلة (s10).",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/openapi",
                 "https://learn.microsoft.com/azure/container-apps/overview",
                 "https://learn.microsoft.com/azure/container-apps/scale-app",
                 "https://opentelemetry.io/docs/languages/dotnet/",
                 "https://learn.microsoft.com/aspnet/core/security/authentication/",
                 "https://learn.microsoft.com/dotnet/core/docker/container-images",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Minimal APIs + OpenAPI 3.1", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/openapi"},
            {"label": "Azure Container Apps", "url": "https://learn.microsoft.com/azure/container-apps/overview"},
            {"label": "قواعد scale في ACA", "url": "https://learn.microsoft.com/azure/container-apps/scale-app"},
            {"label": "OpenTelemetry .NET", "url": "https://opentelemetry.io/docs/languages/dotnet/"},
            {"label": "صور .NET المحسّنة (chiseled)", "url": "https://learn.microsoft.com/dotnet/core/docker/container-images"},
            {"label": "GitHub Actions: OIDC إلى Azure", "url": "https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure"},
            {"label": "OWASP ASVS (مراجعة أمنية)", "url": "https://owasp.org/www-project-application-security-verification-standard/"},
        ]},
    ],
}

LESSONS_S8_CAP = [_CAP]
