# -*- coding: utf-8 -*-
"""Stage 7 module 2 (part F): s7-m2-l3 (قائمة فحص أمان إنتاجية)."""

TODAY = "2026-10-22"

_L3 = {
    "id": "s7-m2-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "في المرحلة 2 (2.2.5) قسّينا التطبيق من جوه. الدرس ده **قائمة فحص ما قبل النشر** — اللي بيفصل بين «التطبيق مؤمّن نظريًا» و«التطبيق مؤمّن في الإنتاج فعلًا ومُثبت بأمر». بنمشي على **OWASP Top 10:2025** (اللي صدر في نوفمبر 2025 وغيّر الترتيب تغييرًا جوهريًا: الإعدادات الخاطئة طلعت رقم 2، وسلسلة التوريد بقت فئة كاملة رقم 3)، وبعدين أربعة أعمدة عملية: **الترويسات وTLS** · **أقل الصلاحيات** · **سجل تدقيق للعمليات الحساسة** · **خطة استجابة للاختراق**. وفي الآخر سكربت بيفحص كل ده ويخرج تقريرًا — عشان قائمة الفحص اللي بتتنفذ بإيد بتتنسى، واللي بتتنفذ بأمر بتفضل."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "OWASP Top 10:2025", "def": "أخطر عشر فئات خطر في تطبيقات الويب. الجديد: **A03 Software Supply Chain Failures** و**A10 Mishandling of Exceptional Conditions**، و**SSRF اتدمجت في A01**، و**A02 Security Misconfiguration** طلعت من الخامس للثاني."},
            {"term": "A02 Misconfiguration", "def": "أكتر فئة انتشارًا في البيانات: سلوك التطبيق بقى معرّفًا بالإعدادات أكتر من الكود (Cloud + IaC). أمثلة: صفحة استثناءات المطور في الإنتاج · CORS مفتوح · مستند OpenAPI مكشوف · حساب افتراضي."},
            {"term": "A10 Mishandling of Exceptional Conditions", "def": "فئة جديدة: الفشل في **منع أو اكتشاف أو الاستجابة** للحالات غير الطبيعية — الـfail-open، المعاملات الجزئية، معالجة أخطاء خاطئة. العلاج: fail-closed + rollback + حصص موارد + handler عالمي كشبكة أمان مش كاستراتيجية أساسية."},
            {"term": "Defense in depth", "def": "طبقات متعددة مستقلة: الترويسة في التطبيق **و**في الـingress · الصلاحيات في Azure **و**في K8s RBAC · التحقق في الكود **و**في قاعدة البيانات. طبقة واحدة بتفشل = الطبقة التانية بتمسك."},
            {"term": "Least privilege", "def": "كل هوية (خدمة · مستخدم · pipeline) عندها **أقل صلاحية تكفي لمهمتها** وفي **أضيق نطاق ممكن** (vault واحد، namespace واحد، جدول واحد) — وبتتدور/بتُراجع."},
            {"term": "CSP (Content-Security-Policy)", "def": "ترويسة بتقول للمتصفح إيه المصادر المسموح تحميلها/تنفيذها. **nonce-based** (قيمة عشوائية لكل استجابة) أفضل بكتير من `unsafe-inline` اللي بتلغي معظم قيمة الـCSP."},
            {"term": "HSTS", "def": "`Strict-Transport-Security`: بتقول للمتصفح «كلمني HTTPS فقط لمدة سنة» — بتمنع هجمات الـSSL-stripping. `includeSubDomains` + `preload` = التزام أوسع، فاختبر قبل ما تفعّلها."},
            {"term": "Audit log (سجل تدقيق)", "def": "سجل **من عمل إيه على إيه وإمتى ومن أين** للعمليات الحساسة. صفاته: append-only · ما يقدرش يعدّله حتى الأدمن · محفوظ لفترة محددة · ومحمي من التسرب (فيه بيانات شخصية → 7.2.5)."},
            {"term": "Fail closed", "def": "عند الخطأ: ارفض/ارجع المعاملة — مش «كمل على الأساس». عكس الـfail-open اللي بيفتح الباب وقت الأعطال (مثال: تفويض بيرجع allow لو خدمة الهوية وقعت)."},
            {"term": "Secret rotation", "def": "تدوير دوري للأسرار (مفاتيح · شهادات · connection strings) + تدوير فوري عند الاشتباه. في السحابة: Managed Identity بتلغي الحاجة للسر أصلًا (6.2.3)."},
            {"term": "Breach (خرق بيانات)", "def": "وصول غير مصرح به لبيانات شخصية أو تسربها. بيبدأ ساعة قانونية (إخطار الجهة الرقابية/الأفراد) — فالتأخير في الاكتشاف أغلى من التأخير في الإصلاح."},
            {"term": "ASVS", "def": "**OWASP Application Security Verification Standard**: مستويات تحقق مفصّلة (تصميم/كود/نشر). استخدمه لما تحتاج متطلبات قابلة للاختبار بدل قائمة عامة."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① OWASP Top 10:2025 — وإزاي تقفل كل فئة في ASP.NET Core 10"},
        {"type": "table", "caption": "الفئة × التغيير عن 2021 × مثال واقعي في shop × الإجراء",
         "head": ["الفئة", "التغيير", "مثال في نظام shop", "الإجراء في ASP.NET Core 10"],
         "rows": [
             ["**A01 Broken Access Control** (تشمل SSRF)", "ثابت في المركز الأول · **SSRF اتدمجت فيه**",
              "`GET /orders/{id}` من غير فحص ملكية → IDOR · مسار بيجيب URL من المستخدم ويطلبه داخليًا",
              "authorization policies + فحص الملكية في كل endpoint · `RequireAuthorization()` افتراضي · منع النداء لعناوين داخلية/metadata (allowlist للمخرَج)"],
             ["**A02 Security Misconfiguration**", "طلع من **الخامس للثاني**",
              "صفحة استثناءات المطور في الإنتاج · CORS `AllowAnyOrigin` · Scalar مكشوف · حساب DB بصلاحيات owner",
              "`ASPNETCORE_ENVIRONMENT=Production` · `IExceptionHandler` مخصص · CORS allowlist · حماية `/scalar` · مستخدم DB بصلاحيات محددة · فحص إعدادات في CI"],
             ["**A03 Software Supply Chain Failures**", "**فئة جديدة** (توسيع «التبعيات القديمة»)",
              "حزمة NuGet ملوثة · صورة أساس بثغرة · action غير مثبّت",
              "الدرس 7.2.2 بالكامل: lockfile + NuGetAudit + SBOM + توقيع + admission policy + تثبيت بالـSHA"],
             ["**A04 Cryptographic Failures**", "نزل من الثاني للرابع",
              "كلمات مرور بـMD5 · بيانات شخصية بلا تشفير · مفاتيح في الكود",
              "Identity hashing (PBKDF2) · Data Protection API بمفاتيح في Key Vault · تشفير حقلي (7.2.5) · TLS 1.2+ · HSTS"],
             ["**A05 Injection**", "نزل من الثالث للخامس",
              "SQL مبني بدمج نصوص · `FromSqlRaw` بمتغير · أمر shell بمُدخل مستخدم",
              "EF Core/LINQ المعلمة · `FromSqlInterpolated` · تحقق من المدخلات بـFluentValidation (1.1.4) · encoding في المخرجات"],
             ["**A06 Insecure Design**", "نزل من الرابع للسادس",
              "خصم يُحسب في العميل · إعادة محاولة بلا حدود · flow بلا تحقق من الحالة",
              "threat modeling (7.2.4) · حدود معدلات (2.2.5) · idempotency (5.2.5) · تحقق من الحالة في الخادم دائمًا"],
             ["**A07 Authentication Failures**", "نفس المركز · الاسم اتقصّر",
              "جلسات طويلة · بلا MFA للأدمن · رسائل تكشف وجود الحساب · credential stuffing",
              "Identity + OIDC (2.2.7/2.2.8) · MFA للأدوار الحساسة · رسالة واحدة موحّدة للفشل · rate limit على /login · قفل تدريجي"],
             ["**A08 Software or Data Integrity Failures**", "ثابت تقريبًا",
              "تحديث ذاتي من مصدر غير موقّع · deserialization لمدخل خارجي · CI بلا حماية",
              "توقيع وprovenance (7.2.2) · تجنب deserialization غير آمن · حماية فرع + أقل صلاحيات للـpipeline"],
             ["**A09 Security Logging and Alerting Failures**", "الاتسمية اتغيرت: Monitoring → **Alerting**",
              "سجلات بلا تنبيه · محاولات دخول فاشلة مش متجمعة · تنبيهات بلا runbook",
              "7.1.3–7.1.5: لوجنج مركزي + تدقيق (الأسفل) + تنبيهات على الأعراض + runbook (7.2.1)"],
             ["**A10 Mishandling of Exceptional Conditions**", "**فئة جديدة**",
              "تفويض بيرجع allow لو خدمة الهوية وقعت · معاملة نصفها اتكتب · retry بلا حدود بيسحب الـpool",
              "fail-closed في التفويض · `IExceptionHandler` + rollback · حصص موارد وtimeouts (5.2.4) · circuit breaker"],
         ]},
        {"type": "callout", "kind": "note", "title": "الـTop 10 مش قائمة قبول",
         "md": "OWASP بتقولها صراحة: الـTop 10 **تصنيف مخاطر وأداة توعية**، مش قائمة متطلبات ولا معيار تدقيق — عشر فئات ما بتغطيش كل المتطلبات الأمنية، وكل فئة تحتها مجموعة CWEs من غير معيار نجاح/فشل لكل بند. عشان كده:\n\n• **استخدمه للتواصل والأولويات** (إيه اللي نبدأ بيه) — مش كشهادة امتثال.\n• **للمتطلبات القابلة للاختبار**: استخدم **OWASP ASVS** (مستويات L1/L2/L3) أو متطلبات threat model الخاصة بيك (7.2.4).\n• **للإثبات في الإنتاج**: استخدم سكربت الفحص أدناه — كل بند له أمر ونتيجة متوقعة."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② الترويسات وTLS — والطبقة الصحيحة لكل واحدة"},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Api/Security/SecurityHeaders.cs — ترويسات كتوسيط قابل للاختبار", "filename": "src/Orders.Api/Security/SecurityHeaders.cs", "code": r'''using System.Security.Cryptography;
using Microsoft.AspNetCore.Http;

namespace Shop.Security;

/// <summary>
/// ترويسات أمان الاستجابة. القواعد:
///   • تُضبط في التطبيق حتى لو الـingress بيضبطها كمان (defense in depth) — لكن اتفق على طبقة واحدة
///     لكل ترويسة حتى لا تتعارض القيم (بعض الـproxies بتضيف ولا تستبدل).
///   • الـCSP بـnonce لكل استجابة، لا unsafe-inline.
///   • Append لا Add: Add بترمي لو الترويسة موجودة (من الـingress مثلًا).
/// </summary>
public sealed class SecurityHeadersMiddleware(RequestDelegate next, ICspNonceProvider nonces)
{
    public async Task InvokeAsync(HttpContext context)
    {
        // nonce لكل طلب — يُحقن في الـ<script nonce="...">
        var nonce = nonces.GetOrCreate(context);
        var headers = context.Response.Headers;

        headers.Append("X-Content-Type-Options", "nosniff");
        headers.Append("Referrer-Policy", "strict-origin-when-cross-origin");
        headers.Append("Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()");
        headers.Append("X-Frame-Options", "DENY");
        headers.Append("Cross-Origin-Opener-Policy", "same-origin");
        headers.Append("Cross-Origin-Resource-Policy", "same-origin");
        // CSP: افتراضي self، والسكربتات بـnonce فقط (بلا unsafe-inline)
        headers.Append("Content-Security-Policy",
            $"default-src 'self'; " +
            $"script-src 'self' 'nonce-{nonce}'; " +
            $"style-src 'self' 'nonce-{nonce}'; " +
            $"img-src 'self' data: https://cdn.shop.local; " +
            $"connect-src 'self' https://api.shop.local; " +
            $"frame-ancestors 'none'; base-uri 'self'; form-action 'self'; " +
            "object-src 'none'; upgrade-insecure-requests");

        // منع التخزين المؤقت للاستجابات الحساسة (لا تطبقها على الأصول الثابتة)
        var path = context.Request.Path.Value ?? string.Empty;
        if (!path.StartsWith("/assets", StringComparison.OrdinalIgnoreCase))
        {
            headers.Append("Cache-Control", "no-store");
            headers.Append("Pragma", "no-cache");
        }

        await next(context);
    }
}

/// <summary>يولّد nonce واحدًا لكل طلب ويخزنه في HttpContext.Items.</summary>
public interface ICspNonceProvider
{
    string GetOrCreate(HttpContext context);
}

public sealed class CspNonceProvider : ICspNonceProvider
{
    private const string Key = "__csp_nonce";

    public string GetOrCreate(HttpContext context)
    {
        if (context.Items.TryGetValue(Key, out var existing) && existing is string cached)
        {
            return cached;
        }

        // 16 بايت = 128 بت عشوائية، بترميز base64 صالح للـheader
        Span<byte> buffer = stackalloc byte[16];
        RandomNumberGenerator.Fill(buffer);
        var nonce = Convert.ToBase64String(buffer);
        context.Items[Key] = nonce;
        return nonce;
    }
}

public static class SecurityHeadersExtensions
{
    public static IServiceCollection AddSecurityHeaders(this IServiceCollection services)
        => services.AddSingleton<ICspNonceProvider, CspNonceProvider>();

    public static IApplicationBuilder UseSecurityHeaders(this IApplicationBuilder app)
        => app.UseMiddleware<SecurityHeadersMiddleware>();
}
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — التوصيل والقيود (مقتطف الإنتاج)", "filename": "src/Orders.Api/Program.cs", "code": r'''// usings المطلوبة للمقتطف:
// using System.Net; using Microsoft.AspNetCore.Http;
// using Microsoft.AspNetCore.Builder; using Microsoft.AspNetCore.HttpOverrides;
// using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// ── 1) البيئة والصلاحيات ─────────────────────────────────────────────
// ASPNETCORE_ENVIRONMENT=Production يُضبط من المنصة (6.1.5) — لا من الكود.
builder.Services.AddSecurityHeaders();

builder.Services.AddHsts(o =>
{
    o.MaxAge = TimeSpan.FromDays(365);
    o.IncludeSubDomains = true;
    o.Preload = false;   // فعّلها فقط بعد التأكد من كل النطاقات الفرعية على HTTPS
});

builder.Services.Configure<ForwardedHeadersOptions>(o =>
{
    // ثق فقط بالـproxy المعروف — وإلا المستخدم يقدر يزوّر X-Forwarded-For/Scheme
    o.KnownProxies.Add(IPAddress.Parse(builder.Configuration["Infra:TrustedProxy"]!));
    o.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
});

// ── 2) CORS: allowlist صريح، ولا أي أصل ───────────────────────────────
builder.Services.AddCors(o => o.AddPolicy("shop", p => p
    .WithOrigins(builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()!)
    .WithMethods("GET", "POST", "PUT", "PATCH", "DELETE")
    .WithHeaders("Authorization", "Content-Type", "X-Correlation-Id")
    .AllowCredentials()
    .SetPreflightCacheTimeout(TimeSpan.FromMinutes(10))));

// ── 3) قيود Kestrel: حصص موارد ضد A10 (ظروف استثنائية) ────────────────
builder.WebHost.ConfigureKestrel(k =>
{
    k.Limits.MaxRequestBodySize = 1_048_576;          // 1 MB
    k.Limits.MaxConcurrentConnections = 5_000;
    k.Limits.MaxConcurrentUpgradedConnections = 500;
    k.Limits.KeepAliveTimeout = TimeSpan.FromMinutes(2);
    k.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);
    k.AddServerHeader = false;                        // لا تكشف اسم/إصدار الخادم
});

// ── 4) الكوكيز: HttpOnly + Secure + SameSite ─────────────────────────
builder.Services.ConfigureApplicationCookie(o =>
{
    o.Cookie.HttpOnly = true;
    o.Cookie.SecurePolicy = CookieSecurePolicy.Always;
    o.Cookie.SameSite = SameSiteMode.Strict;   // Lax لو عندك تدفقات دخول خارجي (OAuth redirects)
    o.ExpireTimeSpan = TimeSpan.FromMinutes(30);
    o.SlidingExpiration = true;
});

var app = builder.Build();

// ── 5) ترتيب الوسائط مهم: Forwarded قبل Hsts/HttpsRedirection ─────────
app.UseForwardedHeaders();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();   // في التطوير فقط — ممنوع في الإنتاج
}
else
{
    app.UseExceptionHandler("/error"); // IExceptionHandler من 2.2.3 → ProblemDetails بلا stack trace
    app.UseHsts();
    app.UseHttpsRedirection();
}

app.UseSecurityHeaders();
app.UseCors("shop");
app.UseAuthentication();
app.UseAuthorization();
app.UseRateLimiter();                  // 2.2.5: حدود على /login و/auth و/export
app.MapControllers();

// مستند OpenAPI/Scalar محمي أو معطّل في الإنتاج (A02)
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

app.MapDefaultEndpoints();             // /health و/alive — بلا تفاصيل في الإنتاج (2.2.9)
app.Run();
'''},
        {"type": "table", "caption": "الترويسة × القيمة × بتحمي من إيه × الطبقة الأنسب",
         "head": ["الترويسة", "القيمة الموصى بها", "بتحمي من", "أين تُضبط"],
         "rows": [
             ["`Strict-Transport-Security`", "`max-age=31536000; includeSubDomains`", "SSL-stripping · الوصول بـHTTP", "`app.UseHsts()` (التطبيق) أو الـingress — طبقة واحدة تكفي"],
             ["`Content-Security-Policy`", "nonce-based · `frame-ancestors 'none'` · `object-src 'none'`", "XSS · حقن سكربت · clickjacking", "التطبيق (لأن الـnonce لكل استجابة)"],
             ["`X-Content-Type-Options`", "`nosniff`", "تخمين نوع المحتوى (MIME sniffing)", "التطبيق أو الـingress"],
             ["`X-Frame-Options`", "`DENY` (أو `SAMEORIGIN` لو محتاج)", "تأطير الصفحة (clickjacking)", "التطبيق — مكررًا مع `frame-ancestors` للتوافق"],
             ["`Referrer-Policy`", "`strict-origin-when-cross-origin`", "تسرب مسارات/معرّفات في الـReferer", "التطبيق"],
             ["`Permissions-Policy`", "`geolocation=(), camera=(), microphone=(), payment=()`", "استخدام صلاحيات متصفح مش محتاجها", "التطبيق"],
             ["`Cross-Origin-Opener-Policy`", "`same-origin`", "هجمات عبر النوافذ (Spectro-like/leaks)", "التطبيق أو الـingress"],
             ["`Cross-Origin-Resource-Policy`", "`same-origin` (أو `cross-origin` للأصول العامة)", "قراءة الأصول من مصادر أخرى", "التطبيق"],
             ["`Cache-Control`", "`no-store` للاستجابات الحساسة · `public,max-age` للأصول", "تخزين بيانات شخصية في كاش وسيط/متصفح", "التطبيق (مسار-مشروط)"],
             ["`Server` / ترويسات الإصدار", "محذوفة", "بصمات تساعد المهاجم", "`AddServerHeader=false` + إعداد الـproxy"],
         ]},
        {"type": "callout", "kind": "warn", "title": "أربعة أخطاء بتخلي الترويسات تختفي في الإنتاج",
         "md": "**① ترتيب الوسائط**: `UseForwardedHeaders` لازم **قبل** `UseHsts`/`UseHttpsRedirection` — وإلا المخطط اللي يوصل للتطبيق HTTP والتحويل بيلف.\n**② طبقتان بتتعارضان**: الـingress بيضيف `Content-Security-Policy` والتطبيق بيضيف واحدة تانية → المتصفح بياخد **القيود الأشد** (الاتنين بيتطبقوا)، وده ممكن يكسر الموقع من غير رسالة خطأ واضحة. اختار طبقة واحدة ووثّقها.\n**③ `unsafe-inline`**: بيخلي الـCSP شبه بلا قيمة ضد XSS. استخدم nonce (كما في الكود) أو hash.\n**④ ما اختبرتش في الإنتاج**: اختبر بالأمر ده على **الرابط المنشور** مش localhost:"},
        {"type": "code", "lang": "bash", "title": "تحقق حي من الترويسات وTLS (نفّذه على الإنتاج)", "filename": "scripts/check-headers.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
URL="${1:?استخدم: check-headers.sh https://api.example.com/health}"

echo "== الترويسات =="
curl -sSIL "$URL" | grep -iE 'strict-transport|content-security|x-content-type|x-frame|referrer-policy|permissions-policy|cross-origin|cache-control|server' || echo "(لا توجد ترويسات أمان!)"

echo "== HTTP -> HTTPS =="
HTTP_URL="${URL/https:/http:}"
CODE=$(curl -s -o /dev/null -w '%{http_code}' -I "$HTTP_URL" || true)
echo "رمز الاستجابة على HTTP: $CODE (المتوقع 301/308)"

echo "== إصدار TLS والشهادات =="
HOST=$(printf '%s' "$URL" | sed -E 's#https://([^/]+).*#\1#')
echo | openssl s_client -connect "${HOST}:443" -servername "${HOST}" 2>/dev/null \
  | grep -E 'Protocol|Cipher|subject=|issuer=|Verify return code' || echo "تعذر الفحص"

echo "== رفض TLS قديم (لازم يفشل) =="
openssl s_client -connect "${HOST}:443" -tls1_1 </dev/null >/dev/null 2>&1 \
  && echo "✗ TLS 1.1 مقبول — أغلقه" \
  || echo "✓ TLS 1.1 مرفوض"

echo "== صفحة الخطأ لا تكشف تفاصيل =="
curl -sS -o /dev/null -w 'status=%{http_code}\n' "$URL/not-found-path"
curl -sS "$URL/not-found-path" | grep -qiE 'stack ?trace|at Shop\.|Microsoft\.AspNetCore' \
  && echo "✗ الاستجابة تكشف stack trace" \
  || echo "✓ لا تسرب تفاصيل داخلية"
'''},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ أقل الصلاحيات: لكل هوية، في كل طبقة"},
        {"type": "table", "caption": "الهوية × الصلاحية الدنيا × النطاق × كيف تراجعه",
         "head": ["الهوية", "الصلاحيات الدنيا", "النطاق (أضيق ممكن)", "أداة المراجعة"],
         "rows": [
             ["خدمة `orders-api` (Managed Identity)", "قراءة الأسرار · سحب الصورة · كتابة على طابورها", "Key Vault واحد · ACR واحد · namespace واحد", "`az keyvault role assignment list --scope <vault>`"],
             ["خدمة `payments-worker`", "قراءة/كتابة جداولها فقط · نشر لـtopic واحد", "جداول محددة · topic محدد · بلا وصول لمفاتيح التشفير", "K8s Role + مراجعة Service Bus/Event permissions"],
             ["pipeline النشر (OIDC federated credential)", "Contributor على **مجموعة موارد الإنتاج فقط** + AcrPush", "مجموعة موارد واحدة · بيئة GitHub `production` بمراجعين (6.3.5)", "`az ad sp show --id <client-id>` + قائمة federated credentials"],
             ["مهندس on-call", "قراءة السجلات والمقاييس · تنفيذ runbook · **لا حذف**", "namespace/اشتراك محدد · وصول مؤقت (JIT)", "سجلات Activity Log + مراجعة ربع سنوية"],
             ["مستخدم قاعدة البيانات للتطبيق", "`SELECT/INSERT/UPDATE/DELETE` على مخططاته · **بلا DDL**", "قاعدة واحدة · مخطط واحد · بلا `db_owner`/`sa`", "`GRANT` scripts في الريبو + تدقيق صلاحيات DB"],
             ["التطبيق نفسه داخل الـPod", "non-root (UID 1654 في chiseled) · read-only filesystem · `automountServiceAccountToken: false`", "الـPod · namespace", "`kubectl get pod -o yaml` + `trivy image --scanners misconfig`"],
         ]},
        {"type": "code", "lang": "yaml", "title": "deploy/k8s/rbac.yaml — هوية لكل خدمة وصلاحيات محدودة", "filename": "deploy/k8s/rbac.yaml", "code": r'''# لكل خدمة: ServiceAccount خاص + Role محدودة + RoleBinding.
# لا تستخدم default SA، ولا تعطِ ClusterRole لتطبيق.
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-api
  namespace: shop
  # Workload Identity (6.2.3): الربط بهوية Azure يتم بالـannotation
  annotations:
    azure.workload.identity/client-id: "00000000-0000-0000-0000-000000000000"
automountServiceAccountToken: false   # التطبيق لا يحتاج Kubernetes API → لا تركّب التوكن
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: orders-api-minimal
  namespace: shop
rules:
  # المثال الوحيد المشروع هنا: قراءة ConfigMap خاص بالتطبيق (لو محتاج فعلًا)
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["orders-api-featureflags"]   # محدد بالاسم — لا wildcard
    verbs: ["get"]
  # لا delete · لا create · لا secrets · لا pods
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: orders-api-minimal
  namespace: shop
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: orders-api-minimal
subjects:
  - kind: ServiceAccount
    name: orders-api
    namespace: shop
'''},
        {"type": "code", "lang": "bash", "title": "scripts/least-privilege.sh — طبّق وراجع الصلاحيات على Azure", "filename": "scripts/least-privilege.sh", "code": r'''#!/usr/bin/env bash
# يمنح أقل الصلاحيات لهويات الخدمات ويراجع ما هو موجود.
# يتطلب: az CLI مسجل الدخول بصلاحيات تعيين أدوار على النطاقات المحددة.
set -euo pipefail

RG="${RG:-shop-rg}"
SUB_ID="$(az account show --query id -o tsv)"
VAULT_NAME="${VAULT_NAME:-shop-kv}"
ACR_NAME="${ACR_NAME:-shopacr}"

VAULT_ID="/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.KeyVault/vaults/${VAULT_NAME}"
ACR_ID="/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}"

# ── 1) اقرأ object id لهوية الخدمة (لا تستخدم app/client id في الدور) ──
MI_PRINCIPAL_ID="$(az containerapp show -n orders-api -g "$RG" \
  --query identity.principalId -o tsv)"
echo "Managed Identity principalId: $MI_PRINCIPAL_ID"

# ── 2) قراءة الأسرار فقط، وعلى هذا الـvault فقط ───────────────────────
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee-object-id "$MI_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --scope "$VAULT_ID"

# ── 3) سحب الصور فقط (لا دفع) ─────────────────────────────────────────
az role assignment create \
  --role "AcrPull" \
  --assignee-object-id "$MI_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --scope "$ACR_ID"

# ── 4) مراجعة: كل التعيينات على هذا النطاق ────────────────────────────
echo "== الأدوار على الـKey Vault =="
az role assignment list --scope "$VAULT_ID" \
  --query "[].{principal:principalName,role:roleDefinitionName,type:principalType}" -o table

echo "== الأدوار على الـACR =="
az role assignment list --scope "$ACR_ID" \
  --query "[].{principal:principalName,role:roleDefinitionName,type:principalType}" -o table

# ── 5) مخالفات شائعة تُفحص يدويًا ─────────────────────────────────────
echo "== فحوصات يجب أن ترجع فارغة =="
echo "- ACR admin enabled (لازم false — السحب بهوية):"
az acr show -n "$ACR_NAME" --query adminEnabled -o tsv
echo "- أي هوية خدمة بدور Contributor أو أعلى على مستوى مجموعة الموارد:"
az role assignment list --resource-group "$RG" \
  --query "[?principalType=='ServicePrincipal' && roleDefinitionName=='Contributor'].{p:principalName,scope:scope}" -o table
echo "- Key Vaults تستخدم سياسة الوصول القديمة بدل RBAC:"
az keyvault list -g "$RG" --query "[].{name:name,rbac:properties.enableRbacAuthorization}" -o table
'''},
        {"type": "callout", "kind": "danger", "title": "ثلاثة «تساهلات» بتتحول لخرق",
         "md": "**① `--admin-enabled true` على ACR**: كلمة مرور ثابتة بصلاحيات واسعة، بتنتشر في الـmanifests والـlogs — عندنا السحب بهوية (6.2.3).\n**② Contributor على مستوى الاشتراك للـpipeline**: اختراق الـCI = سيطرة على كل مواردك. اعطِ الدور على **مجموعة موارد الإنتاج** فقط، واستخدم federated credential مقيدة بـ`environment:production` (6.3.1).\n**③ connection string واحدة لكل الخدمات**: ما تعرفش مين قرأ إيه، والتدوير بيكسر كل حاجة في نفس الوقت. هوية لكل خدمة + أسرار مقسّمة (زي `PrefixSecretManager` في 6.2.3)."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ سجل التدقيق: من عمل إيه، على إيه، إمتى"},
        {"type": "text", "md": "الـlogs (7.1.3) بتقول **إيه اللي حصل تقنيًا**. الـaudit بيقول **مين غيّر إيه في أي كيان** — وده اللي محتاجه في تحقيق خرق، وفي إثبات الامتثال (7.2.5)، وفي الرد على سؤال «مين غيّر السعر ده؟». التنفيذ الأنضف في .NET: **interceptor على `SaveChanges`** — فأي تغيير عبر EF Core بيتسجل تلقائيًا، من غير ما تعتمد على إن كل مطور يفتكر ينادي دالة."},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Infrastructure/Audit/AuditEntry.cs + AuditSaveChangesInterceptor.cs", "filename": "src/Orders.Infrastructure/Audit/AuditSaveChangesInterceptor.cs", "code": r'''using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace Shop.Infrastructure.Audit;

/// <summary>
/// صف تدقيق append-only. القواعد:
///   • لا Update ولا Delete عبر التطبيق (لا DbSet.Update/Delete على هذا النوع).
///   • Before/After مخزنة كـJSON مع إخفاء الحقول الحساسة (7.2.5).
///   • Actor من الهوية المصادَقة، لا من مدخلات الطلب.
/// </summary>
public sealed class AuditEntry
{
    public long Id { get; set; }
    public DateTimeOffset OccurredAtUtc { get; set; }
    public string Action { get; set; } = "";        // Created / Updated / Deleted / Exported / Erased
    public string EntityType { get; set; } = "";    // Order / Customer / PriceRule
    public string EntityId { get; set; } = "";
    public string? ActorId { get; set; }            // sub من التوكن — null = مجهول (يُسجَّل كـanonymous)
    public string? ActorType { get; set; }          // user / service / system
    public string? CorrelationId { get; set; }      // يربط بالسجلات والتتبع (7.1.3)
    public string? SourceIp { get; set; }
    public string? UserAgent { get; set; }
    public string? BeforeJson { get; set; }
    public string? AfterJson { get; set; }
    public string[] ChangedFields { get; set; } = [];
    public string Reason { get; set; } = "";        // "api" / "admin-ui" / "job:outbox-dispatcher"
}

/// <summary>سياق التدقيق: من وين؟ من أين؟ — يُملأ من HttpContext أو من خلفية المهام.</summary>
public interface IAuditContext
{
    string? ActorId { get; }
    string? ActorType { get; }
    string? CorrelationId { get; }
    string? SourceIp { get; }
    string? UserAgent { get; }
    string Reason { get; }
}

public sealed class HttpAuditContext(IHttpContextAccessor accessor) : IAuditContext
{
    private HttpContext? Ctx => accessor.HttpContext;

    public string? ActorId => Ctx?.User?.FindFirst("sub")?.Value
                              ?? Ctx?.User?.Identity?.Name;
    public string? ActorType => Ctx is null ? "system" : (Ctx.User.Identity?.IsAuthenticated == true ? "user" : "anonymous");
    public string? CorrelationId => Ctx?.TraceIdentifier;
    public string? SourceIp => Ctx?.Connection.RemoteIpAddress?.ToString();
    public string? UserAgent => Ctx?.Request.Headers.UserAgent.ToString();
    public string Reason => Ctx is null ? "background" : "api";
}

public sealed class AuditSaveChangesInterceptor(
    IAuditContext auditContext,
    IAuditClock clock,
    AuditRedactor redactor)
    : SaveChangesInterceptor
{
    public override async ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken cancellationToken = default)
    {
        var context = eventData.Context;
        if (context is null)
        {
            return await base.SavingChangesAsync(eventData, result, cancellationToken);
        }

        var entries = context.ChangeTracker.Entries()
            .Where(e => e.State is EntityState.Added or EntityState.Modified or EntityState.Deleted
                        && e.Entity is not AuditEntry)     // لا ندقق صفوف التدقيق نفسها
            .ToList();

        if (entries.Count == 0)
        {
            return await base.SavingChangesAsync(eventData, result, cancellationToken);
        }

        var now = clock.UtcNow;   // قابل للاختبار — لا DateTime.UtcNow مباشرة هنا
        var rows = new List<AuditEntry>(entries.Count);

        foreach (var entry in entries)
        {
            rows.Add(new AuditEntry
            {
                OccurredAtUtc = now,
                Action = Map(entry.State),
                EntityType = entry.Metadata.ClrType.Name,
                EntityId = GetPrimaryKey(entry) ?? "(new)",
                ActorId = auditContext.ActorId,
                ActorType = auditContext.ActorType,
                CorrelationId = auditContext.CorrelationId,
                SourceIp = auditContext.SourceIp,
                UserAgent = Truncate(auditContext.UserAgent, 256),
                Reason = auditContext.Reason,
                BeforeJson = entry.State is EntityState.Added ? null : Snapshot(entry, useOriginal: true),
                AfterJson = entry.State is EntityState.Deleted ? null : Snapshot(entry, useOriginal: false),
                ChangedFields = Changed(entry),
            });
        }

        context.Set<AuditEntry>().AddRange(rows);
        return await base.SavingChangesAsync(eventData, result, cancellationToken);
    }

    private static string Map(EntityState s) => s switch
    {
        EntityState.Added => "Created",
        EntityState.Modified => "Updated",
        EntityState.Deleted => "Deleted",
        _ => "Unknown",
    };

    private static string[] Changed(EntityEntry entry)
        => entry.State == EntityState.Modified
            ? entry.Properties.Where(p => p.IsModified).Select(p => p.Metadata.Name).ToArray()
            : [];

    private static string? GetPrimaryKey(EntityEntry entry)
    {
        var key = entry.Metadata.FindPrimaryKey();
        if (key is null) return null;
        var values = key.Properties.Select(p => entry.Property(p.Name).CurrentValue);
        return string.Join("|", values.Select(v => v?.ToString() ?? "null"));
    }

    private string Snapshot(EntityEntry entry, bool useOriginal)
    {
        var values = entry.Properties.ToDictionary(
            p => p.Metadata.Name,
            p => useOriginal
                ? (p.OriginalValue ?? p.CurrentValue)
                : p.CurrentValue);

        var redacted = redactor.Redact(entry.Metadata.ClrType.Name, values);
        return JsonSerializer.Serialize(redacted, new JsonSerializerOptions { WriteIndented = false });
    }

    private static string? Truncate(string? value, int max)
        => value is null ? null : (value.Length <= max ? value : value[..max]);
}

/// <summary>
/// يخفي الحقول الحساسة قبل تخزينها في BeforeJson/AfterJson:
/// سجل التدقيق نفسه بيانات شخصية (7.2.5)، فلا نضاعف الخطر.
/// </summary>
public sealed class AuditRedactor
{
    // أسماء الحقول التي تُخفى كليًا — تُدار من الإعدادات في مشروع حقيقي
    private static readonly HashSet<string> FullRedaction = new(StringComparer.OrdinalIgnoreCase)
    {
        "PasswordHash", "CardNumber", "Cvv", "NationalId", "SecurityStamp",
        "RefreshToken", "ApiKey", "Secret", "PrivateKey",
    };

    // حقول تُقنّع جزئيًا (تُبقي آخر 4 أرقام للمطابقة)
    private static readonly HashSet<string> Mask = new(StringComparer.OrdinalIgnoreCase)
    {
        "PhoneNumber", "Email", "Iban", "MobileNumber",
    };

    public Dictionary<string, object?> Redact(string entityType, IDictionary<string, object?> values)
    {
        var result = new Dictionary<string, object?>(values.Count);
        foreach (var (name, value) in values)
        {
            if (FullRedaction.Contains(name))
            {
                result[name] = "[REDACTED]";
            }
            else if (Mask.Contains(name) && value is string text && text.Length > 4)
            {
                result[name] = new string('*', text.Length - 4) + text[^4..];
            }
            else
            {
                result[name] = value;
            }
        }

        return result;
    }
}

/// <summary>مصدر زمن قابل للاستبدال في الاختبارات (1.2.1).</summary>
public interface IAuditClock { DateTimeOffset UtcNow { get; } }
public sealed class SystemAuditClock(TimeProvider tp) : IAuditClock
{
    public DateTimeOffset UtcNow => tp.GetUtcNow();
}
'''},
        {"type": "table", "caption": "عشرة أحداث لازم تُدقَّق (بخلاف تغييرات الكيانات التلقائية)",
         "head": ["#", "الحدث", "الحقول المطلوبة", "الاحتفاظ", "من يقرأه"],
         "rows": [
             ["1", "تسجيل دخول ناجح/فاشل", "المستخدم · IP · User-Agent · السبب · CorrelationId", "12 شهرًا", "الأمن + الدعم"],
             ["2", "تغيير دور/صلاحية", "من · لمن · من إيه لإيه · السبب · موافقة", "7 سنوات", "الأمن + الامتثال"],
             ["3", "قراءة بيانات شخصية بكمية (تصدير/تقرير)", "من · نطاق البيانات · عدد السجلات · السبب", "7 سنوات", "الامتثال (7.2.5)"],
             ["4", "حذف/إخفاء هوية بيانات شخصية", "من · المعرّف · النطاق · الأساس القانوني", "دائمًا (إثبات الحذف)", "الامتثال"],
             ["5", "تغيير سعر/خصم/حد ائتماني", "من · الكيان · قبل/بعد · التذكرة", "7 سنوات", "المالية + الأمن"],
             ["6", "وصول/تدوير سر أو مفتاح", "من · أي سر · العملية · النتيجة", "3 سنوات", "الأمن"],
             ["7", "تغيير إعدادات أمان (CORS/CSP/rate limit)", "من · المفتاح · قبل/بعد · النشر", "3 سنوات", "الأمن"],
             ["8", "عمليات إدارية على الإنتاج (exec/scale/rollback)", "من · الأمر · الهدف · النتيجة", "3 سنوات", "الأمن + SRE"],
             ["9", "محاولات رفض متكررة (403/401/429)", "المستخدم/IP · العدد · الفترة", "6 أشهر", "الأمن (تنبيه)"],
             ["10", "استدعاءات طرف ثالث تُرسل لها بيانات شخصية", "الجهة · الغرض · حجم البيانات", "3 سنوات", "الامتثال"],
         ]},
        {"type": "callout", "kind": "tip", "title": "خصائص سجل التدقيق اللي ما تتنازلش عنها",
         "md": "**Append-only**: مفيش UPDATE/DELETE من التطبيق — ولو على DB، امنع الصلاحيات (`DENY UPDATE,DELETE ON audit_entries`) وخزّن في جدول منفصل أو storage بتأمين WORM.\n**لا يعتمد على مُدخلات الطلب**: الـActorId من التوكن المصادَق، مش من body.\n**محمي من التسرب**: سجل التدقيق نفسه يحتوي بيانات شخصية → إخفاء الحقول الحساسة (`AuditRedactor`) + نفس قواعد التشفير والاحتفاظ (7.2.5).\n**مربوط بالتتبع**: `CorrelationId` بيخليك تقفز من صف التدقيق للسجلات والتتبع في ثانية (7.1.3).\n**منبّه عليه**: «5 محاولات رفض من نفس IP خلال دقيقة» و«تصدير أكثر من N سجل» = تنبيهات أمنية (A09).\n**مُختبر**: اختبار تكاملي يثبت إن التغيير بيتسجل فعلًا — لأن interceptor مش متسجل بيصمت بهدوء."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ قائمة الفحص قبل النشر — بأوامر"},
        {"type": "code", "lang": "bash", "title": "scripts/pre-release-security-check.sh — تقرير PASS/FAIL لكل بند", "filename": "scripts/pre-release-security-check.sh", "code": r'''#!/usr/bin/env bash
# يفحص قائمة الأمان على بيئة منشورة + الكود. اكتب النتيجة في ملف تقرير.
# الاستخدام: BASE_URL=https://api.example.com ./scripts/pre-release-security-check.sh
set -uo pipefail

BASE_URL="${BASE_URL:?عيّن BASE_URL}"
REPORT="${REPORT:-artifacts/security/pre-release-check.md}"
mkdir -p "$(dirname "$REPORT")"
pass=0; fail=0

check() {  # check "البند" "النتيجة المتوقعة" "القيمة الفعلية"
  local item="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    printf '| ✅ | %s | %s |\n' "$item" "$actual" >> "$REPORT"
    pass=$((pass+1))
  else
    printf '| ❌ | %s | متوقع: %s · فعلي: %s |\n' "$item" "$expected" "$actual" >> "$REPORT"
    fail=$((fail+1))
  fi
}

{
  echo "# تقرير الفحص الأمني قبل النشر"
  echo "- البيئة: $BASE_URL"
  echo "- التاريخ: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "| الحالة | البند | التفاصيل |"
  echo "|---|---|---|"
} > "$REPORT"

HEADERS=$(curl -sSIL "$BASE_URL/health" 2>/dev/null || true)

# A02: الترويسات
check "HSTS" "yes" "$(grep -qi 'strict-transport-security' <<<"$HEADERS" && echo yes || echo no)"
check "CSP" "yes" "$(grep -qi 'content-security-policy' <<<"$HEADERS" && echo yes || echo no)"
check "nosniff" "yes" "$(grep -qi 'x-content-type-options: *nosniff' <<<"$HEADERS" && echo yes || echo no)"
check "frame options" "yes" "$(grep -qiE 'x-frame-options|frame-ancestors' <<<"$HEADERS" && echo yes || echo no)"
check "بلا ترويسة Server كاشفة" "yes" "$(grep -qi '^server:' <<<"$HEADERS" && echo no || echo yes)"

# A02: HTTPS والتحويل
check "تحويل HTTP إلى HTTPS" "301" "$(curl -s -o /dev/null -w '%{http_code}' -I "${BASE_URL/https:/http:}/health" 2>/dev/null || echo 000)"

# A02: صفحة الخطأ لا تكشف تفاصيل
ERRBODY=$(curl -sS "$BASE_URL/definitely-not-a-route" 2>/dev/null || true)
check "صفحة الخطأ بلا stack trace" "yes" \
  "$(grep -qiE 'stack ?trace|at Shop\.|Microsoft\.AspNetCore\.' <<<"$ERRBODY" && echo no || echo yes)"
check "صفحة الخطأ ترجع ProblemDetails" "yes" \
  "$(grep -qi 'application/problem+json' <<<"$(curl -sSI "$BASE_URL/definitely-not-a-route" 2>/dev/null)" && echo yes || echo no)"

# A02: أدوات المطور غير مكشوفة
for path in "/scalar" "/scalar/v1" "/openapi/v1.json" "/swagger" "/health/detail" "/metrics"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL$path" 2>/dev/null || echo 000)
  if [[ "$code" == "404" || "$code" == "401" || "$code" == "403" ]]; then
    check "$path غير مكشوف" "yes" "yes ($code)"
  else
    check "$path غير مكشوف" "yes" "no ($code)"
  fi
done

# A01/A06: endpoint بلا مصادقة لازم يرجع 401
check "/orders محمي" "401" "$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/orders" 2>/dev/null || echo 000)"

# A07: حدود المعدل على تسجيل الدخول (429 بعد تجاوز الحد)
codes=""
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  codes+=$(curl -s -o /dev/null -w '%{http_code} ' -X POST "$BASE_URL/login" \
    -H 'Content-Type: application/json' -d '{}' 2>/dev/null || echo "000 ")
done
check "rate limiting على /login" "yes" "$(grep -q '429' <<<"$codes" && echo yes || echo no)"

# A05: الاستعلامات معلمة (فحص ثابت على الكود)
if [[ -d "src" ]]; then
  RAW_SQL=$(grep -rn --include='*.cs' -E 'FromSqlRaw|ExecuteSqlRaw|CommandText *=' src | grep -vE 'FromSqlInterpolated|Test' | wc -l | tr -d ' ')
  check "بلا SQL خام غير معلم" "0" "$RAW_SQL"
  STRING_CONCAT_SQL=$(grep -rn --include='*.cs' -E '(\$".*(SELECT|INSERT|UPDATE|DELETE).*\{)' src | wc -l | tr -d ' ')
  check "بلا SQL مبني بـstring interpolation" "0" "$STRING_CONCAT_SQL"
fi

# A03/A04: أسرار في الكود
TMP="$(mktemp -d)"
if command -v gitleaks >/dev/null 2>&1; then
  # gitleaks بيرجع كود خروج 1 لو لقى تسريبات — فلا نوقف السكربت
  gitleaks detect --no-banner --redact --report-format json \
    --report-path "$TMP/gitleaks.json" >/dev/null 2>&1 || true
  LEAKS=$(jq 'length' "$TMP/gitleaks.json" 2>/dev/null || echo 0)
  check "gitleaks: لا أسرار" "0" "$LEAKS"
else
  check "gitleaks مثبت" "yes" "no"
fi

# A03: التبعيات
if command -v trivy >/dev/null 2>&1; then
  FIXABLE=$(trivy fs . --scanners vuln --severity HIGH,CRITICAL --format json 2>/dev/null \
    | jq '[.Results[]?.Vulnerabilities[]? | select(.FixedVersion != null and .FixedVersion != "")] | length' 2>/dev/null || echo 0)
  check "لا ثغرات عالية قابلة للإصلاح" "0" "$FIXABLE"
fi

# A04/A07: الكوكيز (نفحص لو المسار بيرجّع كوكي فعلًا)
COOKIE_HDR=$(curl -sS -D - -o /dev/null -X POST "$BASE_URL/login" \
  -H 'Content-Type: application/json' -d '{}' 2>/dev/null | grep -i '^set-cookie' || true)
if [[ -z "$COOKIE_HDR" ]]; then
  printf '| ⚪ | كوكيز الجلسة | المسار لا يرجع كوكي — فحص يدوي على مسار الدخول الحقيقي |\n' >> "$REPORT"
else
  check "الكوكيز HttpOnly" "yes" "$(grep -qi 'httponly' <<<"$COOKIE_HDR" && echo yes || echo no)"
  check "الكوكيز Secure" "yes" "$(grep -qi 'secure' <<<"$COOKIE_HDR" && echo yes || echo no)"
  check "الكوكيز SameSite" "yes" "$(grep -qi 'samesite' <<<"$COOKIE_HDR" && echo yes || echo no)"
fi

# A10: الصحة لا تكشف تفاصيل التبعية
HEALTH=$(curl -sS "$BASE_URL/health" 2>/dev/null || true)
check "health بلا تفاصيل داخلية" "yes" \
  "$(grep -qiE 'connectionstring|Server=|Password=' <<<"$HEALTH" && echo no || echo yes)"

echo "" >> "$REPORT"
echo "**النتيجة: $pass ناجح · $fail فاشل**" >> "$REPORT"
echo "راجع التقرير: $REPORT"
if (( fail > 0 )); then
  echo "✗ توجد بنود فاشلة — لا تنشر قبل معالجتها أو توثيق استثناء بمالك وتاريخ."
  exit 1
fi
echo "✓ قائمة الفحص مكتملة."
'''},
        {"type": "callout", "kind": "note", "title": "إزاي تستخدم القائمة من غير ما تتحول لطقس فارغ",
         "md": "**① اربطها بالـpipeline**: شغّلها كـjob في بيئة `staging` قبل `production`، وبوابة `fail` تمنع الترقية (6.3.5).\n**② الاستثناءات مكتوبة**: بند فاشل مع سبب + مالك + تاريخ انتهاء — مش تجاهل صامت.\n**③ راجع البنود ربع سنويًا**: أضف بندًا لكل حادثة/ثغرة حقيقية حصلت (من الـpostmortem في 7.2.1). دي أرخص طريقة تخلي القائمة حية.\n**④ لا تخلط الطبقات**: بنود تفحص **من بره** (curl على URL منشور) وبنود تفحص **الكود** (grep/gitleaks) — الاتنين مطلوب لأن واحد ممكن يخفي عيب التاني (الترويسة في الـingress والتطبيق مكشوف)."},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ خطة الاستجابة للاختراق: الساعات الأولى بتحدد الخسائر"},
        {"type": "steps", "title": "سبع خطوات — بالترتيب (لا تعكسها)", "items": [
            {"title": "أعلن وسمِّ الأدوار (دقيقة 0–10)",
             "md": "SEV1 فورًا حسب 7.2.1 + بلّغ مسؤول الأمن والقانوني. **الخرق مش حادثة موثوقية**: فيه ساعات قانونية بتبدأ من لحظة العلم بالخرق، فالتأخير في الإعلان أغلى من أي حاجة تانية."},
            {"title": "احفظ الأدلة قبل أي تنظيف (دقيقة 5–40)",
             "md": "لقطة للسجلات · snapshot للقرص/الحاوية · تصدير سجل التدقيق · لقطة لقوائم الصلاحيات · سجل الـActivity في السحابة. **لا تعيد تشغيل ولا تحذف**: إعادة التشغيل بتمسح الذاكرة والأثر.",
             "code": r'''# أدلة سريعة (نفّذها قبل أي تدخل)
mkdir -p evidence/$(date -u +%Y%m%dT%H%M)
EV=evidence/$(date -u +%Y%m%dT%H%M)
kubectl -n shop get pods -o wide > "$EV/pods.txt"
kubectl -n shop logs -l app=orders-api --since=6h --tail=20000 > "$EV/app-logs.txt"
az monitor activity-log list --namespace Microsoft.KeyVault -o json > "$EV/keyvault-activity.json"
az role assignment list --resource-group shop-rg -o json > "$EV/rbac.json"
az keyvault list -g shop-rg --query "[].{name:name,rbac:properties.enableRbacAuthorization}" -o json > "$EV/kv-config.json" || true
# سجلات الدخول (Entra ID) بتتصدر من البوابة أو Graph API — مش من az CLI مباشرة
# صدّر سجل التدقيق (append-only) من قاعدة البيانات إلى ملف محمي
psql "$AUDIT_DSN" -c "\copy (SELECT * FROM audit_entries WHERE occurred_at_utc > now() - interval '48 hours') TO '$EV/audit.csv' CSV HEADER"'''},
            {"title": "احصر الأثر (دقيقة 30–120)",
             "md": "ثلاثة أسئلة: **إيه اللي اتأثر؟** (أنظمة · بيانات · هويات) · **مين اللي يقدر يوصل؟** (الصلاحيات المسروقة) · **إمتى بدأ؟** (من أقدم سجل غير طبيعي). الأثر بيحدد هل فيه إخطار قانوني ولا لأ."},
            {"title": "احتوِ — دوّر كل الأسرار المتأثرة (دقيقة 30+)",
             "md": "تدوير فوري: مفاتيح Key Vault · شهادات · connection strings · tokens · مفاتيح التوقيع · PATs. ابطال الجلسات النشطة. عزل المكوّن المخترق (مش حذفه). لو هوية خدمة مسروقة → عطّلها وامنح هوية جديدة.",
             "code": r'''# تدوير وإبطال (أمثلة — طبّقها حسب منصتك)
az keyvault secret set --vault-name shop-kv --name ConnectionStrings--ShopDb --value "$NEW_VALUE"
az ad app credential delete --id "$APP_ID" --key-id "$KEY_ID"
az containerapp identity remove -n orders-api -g shop-rg --system-assigned   # ثم أعد الربط بهوية جديدة
# تدوير مفاتيح Data Protection: عطّل/استبدل المفتاح المتأثر فقط —
# حذف كل المفاتيح يُبطل كل الكوكيز والتوكنات دفعة واحدة ويكسر الجلسات السليمة.
az keyvault key list --vault-name shop-kv --query "[].{name:name,enabled:attributes.enabled}" -o table'''},
            {"title": "استعد الخدمة بأمان (بعد الاحتواء)",
             "md": "انشر من build **مؤكَّد المصدر** (7.2.2: تحقق من التوقيع والـprovenance) — مش من صورة قديمة مجهولة النسب. لو الشك في سلسلة البناء، ابنِ من commit معروف ووقّعه."},
            {"title": "أخطِر قانونيًا في الموعد",
             "md": "**GDPR**: إخطار الجهة الرقابية **خلال 72 ساعة** من العلم بالخرق (مادة 33)، وإخطار الأفراد **بدون تأخير غير مبرر** لو الخطر عالٍ (مادة 34).\n**مصر (قانون 151/2020 ولائحته التنفيذية بالقرار 816/2025)**: فيه التزام إخطار **مركز حماية البيانات الشخصية** وصاحب البيانات عند الخرق — **راجع النص الحالي مع مستشار قانوني**؛ المواعيد والإجراءات التفصيلية في اللائحة اللي دخلت حيز النفاذ في نوفمبر 2025 (فترة توفيق الأوضاع تنتهي في 31 أكتوبر 2026).\nجهّز مسبقًا: قالب الإخطار · بيانات مسؤول حماية البيانات · سجل المعالجة (7.2.5)."},
            {"title": "اكتب التقرير وغيّر النظام (خلال 48 ساعة)",
             "md": "postmortem بلا لوم (7.2.1) + **إجراءات بمالك وتاريخ**. أضف بندًا في قائمة الفحص أعلاه لكل ثغرة استُغلت، وتنبيهًا جديدًا لكل نمط اكتشاف تأخر."},
        ]},
        {"type": "code", "lang": "text", "title": "docs/breach-response.md — قالب جاهز للتعبئة أثناء الحدث", "filename": "docs/breach-response.md", "code": r'''# تقرير خرق بيانات — [رقم الحدث]
> حالة: مسودة/نهائي · IC: <اسم> · مسؤول أمن: <اسم> · قانوني: <اسم>
> **بلا لوم**: الوثيقة دي للتعلم والامتثال، مش للمحاسبة الفردية.

## 1) الاكتشاف
- الوقت (UTC) الذي عُلم فيه بالخرق: 
- كيف اكتُشف: (تنبيه / بلاغ خارجي / فحص / طرف ثالث)
- الزمن من بدء النشاط غير الطبيعي للاكتشاف: 

## 2) ما الذي حدث (وقائع مثبتة بالأدلة فقط)
- النوع: (وصول غير مصرح / تسرب / تعديل / فقد توفر / انتحال هوية)
- الناقل الأولي (إن عُرف): (اعتمادات مسروقة / ثغرة تطبيق / تبعية / إعداد خاطئ / هندسة اجتماعية)
- الدليل: (روابط السجلات · لقطات · معرفات الطلبات · CorrelationIds)

## 3) الأثر
| البند | التفاصيل |
|---|---|
| الأنظمة المتأثرة | |
| الفئات المتأثرة (عملاء/موظفون/موردون) | |
| أنواع البيانات | (اسم · اتصال · هوية وطنية · دفع · صحية · أطفال) |
| عدد السجلات/الأفراد (تقديري ومصدر التقدير) | |
| هل البيانات مشفرة/مخفية الهوية؟ | (نعم/لا — وأين) |
| هل خرجت البيانات خارج حدود السيطرة؟ | |

## 4) الخط الزمني
| الوقت (UTC) | الحدث | من | الدليل |
|---|---|---|---|
| | | | |

## 5) الاحتواء والإجراءات المتخذة
- [ ] الأسرار المدوّرة (قائمة كاملة بالمسمّيات)
- [ ] الجلسات المبطلة
- [ ] الهويات المعطّلة/المستبدلة
- [ ] المكوّنات المعزولة
- [ ] الأدلة المحفوظة (المسار/المكان)

## 6) الإخطار القانوني
| الجهة | السند | الموعد | الحالة |
|---|---|---|---|
| الجهة الرقابية (GDPR إن انطبق) | المادة 33 | خلال 72 ساعة من العلم | |
| الأفراد المتأثرون | المادة 34 (خطر عالٍ) | دون تأخير غير مبرر | |
| مركز حماية البيانات الشخصية (مصر) | القانون 151/2020 والقرار 816/2025 | راجع النص مع القانوني | |
| جهات تعاقدية/عملاء | بند في العقد | | |

## 7) الأسباب المساهمة (النظام، لا الأشخاص)
1. 
2. 
3. 

## 8) إجراءات المتابعة
| # | الإجراء | المالك | الأولوية | التاريخ | التذكرة |
|---|---|---|---|---|---|
| 1 | | | | | |

## 9) الدروس في قائمة الفحص
- بند جديد في scripts/pre-release-security-check.sh: 
- تنبيه جديد في slo-rules/security-rules.yml: 
- تحديث runbook: 
'''},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف فئات **OWASP Top 10:2025** العشر وأقدر أسمّي الفئتين الجديدتين والتغييرات في الترتيب.",
            "أعرف إن الـTop 10 **تصنيف مخاطر** مش قائمة قبول، وأستخدم ASVS للمتطلبات القابلة للاختبار.",
            "أضبط الترويسات في الطبقة الصح، وأستخدم **nonce-based CSP**، وأتحقق منها بأمر على الإنتاج.",
            "أعرف ترتيب الوسائط الحرج (Forwarded قبل Hsts/HttpsRedirection) وأثره.",
            "أمنح **أقل الصلاحيات** لكل هوية في Azure وK8s، وأراجعها بأمر، وأرفض `admin-enabled` وContributor الواسع.",
            "أنفّذ **audit log** عبر `SaveChangesInterceptor` بخصائص append-only وactor من التوكن وربط بالـCorrelationId.",
            "أعرف الأحداث العشرة اللي لازم تُدقَّق وفترة الاحتفاظ لكل واحد.",
            "أشغّل **قائمة فحص بأوامر** في الـpipeline كبوابة، وأوثّق الاستثناءات بمالك وتاريخ.",
            "أعرف ترتيب خطوات الاستجابة للخرق: أدلة → أثر → احتواء → استعادة → إخطار → تقرير.",
            "أعرف الساعات القانونية (72 ساعة في GDPR · والتزام الإخطار في القانون المصري 151/2020) وإن التفاصيل بتحتاج مراجعة قانونية.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على قائمة الفحص والأمان الإنتاجي.",
         "questions": [
             {"q": "في OWASP Top 10:2025، إيه الفئتان الجديدتان؟",
              "options": ["Injection وCryptographic Failures",
                          "Software Supply Chain Failures وMishandling of Exceptional Conditions",
                          "SSRF وInsecure Design",
                          "Authentication Failures وLogging Failures"],
              "answer": 1,
              "explain": "A03 Supply Chain Failures (توسيع لفئة التبعيات القديمة، وأعلى إجماع بين الخبراء) وA10 Mishandling of Exceptional Conditions (fail-open والمعاملات الجزئية). وSSRF اتدمجت في A01، وMisconfiguration طلعت للمركز الثاني."},
             {"q": "إيه الاستخدام الصحيح للـTop 10؟",
              "options": ["بند تعاقدي: «يجب الامتثال لـOWASP Top 10»",
                          "شهادة امتثال تُمنح بعد تدقيق",
                          "تصنيف مخاطر وأولويات — والمتطلبات القابلة للاختبار من ASVS أو threat model",
                          "قائمة فحص نهائية تكفي وحدها"],
              "answer": 2,
              "explain": "OWASP بتقول صراحة إنه أداة توعية وتصنيف، مش معيار قبول: عشر فئات ما بتغطيش كل المتطلبات ومفيش معيار نجاح لكل بند. للمتطلبات استخدم ASVS أو مخرجات threat modeling."},
             {"q": "CSP فيها `script-src 'self' 'unsafe-inline'`. ما التقييم؟",
              "options": ["مقبولة لأنها تمنع التحميل من مصادر خارجية",
                          "تقريبًا بلا قيمة ضد XSS: أي سكربت محقون في الصفحة هيتنفذ",
                          "أقوى من nonce لأنها أشمل",
                          "ممنوعة في المتصفحات الحديثة"],
              "answer": 1,
              "explain": "`unsafe-inline` بتسمح بأي سكربت مضمّن، وXSS بالذات بيشتغل بسكربت مضمّن أو event handler. البديل: nonce لكل استجابة (كما في الكود) أو hash ثابت. كمان ضيف `frame-ancestors 'none'` و`object-src 'none'`."},
             {"q": "وضعت `app.UseHsts()` و`app.UseHttpsRedirection()` قبل `app.UseForwardedHeaders()`. ما الخطر؟",
              "options": ["لا خطر، الترتيب غير مؤثر",
                          "خلف proxy، التطبيق يشاهد المخطط HTTP فيعيد التحويل في حلقة أو يولّد روابط غير صحيحة",
                          "HSTS يتوقف عن العمل نهائيًا",
                          "يزيد زمن الاستجابة فقط"],
              "answer": 1,
              "explain": "الـproxy بينهي TLS فالتطبيق بيشوف HTTP. `UseForwardedHeaders` بيحوّل `X-Forwarded-Proto` لمخطط الطلب — ولازم يشتغل **قبل** أي منطق معتمد على المخطط. وضيف `KnownProxies` عشان المستخدم ما يزوّرش الترويسة."},
             {"q": "الـpipeline عنده دور Contributor على مستوى **الاشتراك**. ليه ده خطر كبير؟",
              "options": ["لأنه يبطئ النشر",
                          "لأن اختراق الـCI يمنح المهاجم سيطرة على كل موارد الاشتراك (يشمل قراءة أسرار وتعديل الشبكات)",
                          "لأن Contributor لا يسمح بالنشر",
                          "لأنه يتطلب MFA"],
              "answer": 1,
              "explain": "المبدأ: أضيق نطاق ممكن. الدور لازم يكون على **مجموعة موارد الإنتاج** فقط (أو موارد محددة)، مع federated credential مقيدة بـ`environment:production` ومراجعين (6.3.1/6.3.5). وراجع دوريًا بـ`az role assignment list`."},
             {"q": "سجل تدقيقك بياخد الـActorId من حقل `userId` في جسم الطلب. ما المشكلة؟",
              "options": ["بطيء",
                          "قابل للتزوير بالكامل — لازم يؤخذ من الهوية المصادَقة (sub في التوكن)",
                          "يخالف GDPR",
                          "يحتاج تشفير"],
              "answer": 1,
              "explain": "أي مدخل من العميل قابل للتزوير، فسجل التدقيق يبقى بلا قيمة إثباتية (وممكن يُستخدم لتوريط مستخدم آخر). خد الـactor من `User.FindFirst(\"sub\")` وسجّل `ActorType` (user/service/anonymous) — والمجهول يُسجَّل كـanonymous بدل ما يُختلق."},
             {"q": "اكتشفت اشتباه اختراق. إيه أول إجراء تقني؟",
              "options": ["إعادة تشغيل كل الخدمات لمسح الأثر",
                          "حذف الحاويات المخترقة فورًا",
                          "حفظ الأدلة (سجلات/لقطات/تدقيق/صلاحيات) ثم الاحتواء بتدوير الأسرار والعزل",
                          "إيقاف الخدمة بالكامل حتى انتهاء التحقيق"],
              "answer": 2,
              "explain": "إعادة التشغيل/الحذف بيمسح الذاكرة والأثر ويصعّب تحديد الأثر — وده بيأثر على التزامك القانوني (مش هتعرف تُخطِر بدقة). العزل (مش الحذف) + تدوير الأسرار + إبطال الجلسات هو الاحتواء الصحيح."},
             {"q": "بند في قائمة الفحص فشل (Scalar مكشوف على الإنتاج). الفريق محتاج ينشر الليلة. التصرف الأنسب؟",
              "options": ["احذف البند من السكربت مؤقتًا",
                          "انشر وسجّل الاستثناء بمالك وتاريخ انتهاء وإجراء مؤقت (حماية بـauth أو تعطيل في الإنتاج)",
                          "أجّل النشر لأجل غير مسمى",
                          "اعتبره غير مهم لأنه توثيق فقط"],
              "answer": 1,
              "explain": "الاستثناءات جزء من العملية شرط تكون **مكتوبة ومؤقتة بمالك وتاريخ**. حذف البند بيكسر القائمة للأبد، والتأجيل المطلق بيوقف التسليم. ومستند OpenAPI مكشوف = خريطة كاملة لهجومك (A02) فالحل سريع: `MapScalarApiReference()` في التطوير فقط أو حماية بمصادقة."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "قائمة فحص شغالة + سجل تدقيق فعلي.",
         "items": [
            {"id": "s7-m2-l3-t1",
             "title": "مهمة 1: قائمة فحص أمان تعمل كبوابة نشر",
             "md": "طبّق `pre-release-security-check.sh` على بيئة منشورة حقيقية عندك (staging/production أو compose محلي معكوس للـinternet عبر نفق). عدّل البنود لتناسب مشروعك، وأضف 3 بنود من عندك (من threat model أو من حادثة حصلت). اربطها بالـCI كـjob قبل النشر، ووثّق أي استثناء.",
             "criteria": [
                 "السكربت يشتغل من غير تدخل ويخرج تقرير Markdown فيه حالة كل بند (✅/❌) وملخص العدد.",
                 "**≥ 18 بندًا** مغطى، على الأقل: 5 ترويسات · تحويل HTTPS · صفحة الخطأ بلا تسرب · 4 مسارات مطورين غير مكشوفة · حماية endpoint · rate limiting على /login · فحصان ثابتان على SQL · gitleaks · فحص ثغرات · health بلا تفاصيل.",
                 "3 بنود جديدة من تصميمك مع سبب مكتوب (من threat model أو حادثة أو بند OWASP ما اتغطاش).",
                 "**نتيجة فعلية**: تقرير من بيئة منشورة + جدول بالبنود الفاشلة وكيف أصلحتها (أو الاستثناء بمالك وتاريخ).",
                 "ربط في الـCI: job يفشل لو فيه بند فاشل (أو gate مع allowlist للاستثناءات الموثقة).",
                 "ملاحظة عن الحدود: إيه اللي السكربت **ما يقدرش** يفحصه (منطق التفويض · IDOR · ثغرات الكود) وإزاي تغطيه (اختبارات + threat model + فحص خارجي).",
             ],
             "hint": "لو ما عندك بيئة منشورة: استخدم `docker compose` من 6.1.2 واعكسها بـ`cloudflared tunnel` أو `ngrok`، أو نفّذ الفحص على `http://localhost:8080` واذكر إن بنود TLS هتفشل محليًا (وده صحيح — وثّقه كاستثناء بيئة). وخلي بالك من `set -euo pipefail` مع `curl` على مسار بيرجع 404: استخدم `|| true` أو `set -uo pipefail` (زي في السكربت) عشان الفحص ما يتوقفش عند أول بند.",
             "solution": "النتائج النموذجية: أول تشغيل بيفشل في 4–7 بنود — المعتاد: ترويسة `Server` كاشفة (حل: `AddServerHeader=false` + إعداد الـproxy)، `/metrics` مكشوف (حل: محدد بشبكة داخلي أو مصادقة)، rate limiting على `/login` مش مفعّل (2.2.5)، و`/health` بيرجع تفاصيل التبعية (2.2.9). البنود اللي السكربت ما يقدرش يغطيها فعلًا: **IDOR** (محتاج اختبار تكاملي بيطلب مورد مستخدم تاني ويتوقع 403 — اكتبه في اختباراتك)، **تفويض fail-open** (محتاج اختبار بيوقف خدمة الهوية ويتوقع رفض)، و**CSP الفعّالة** (الترويسة موجودة بس ممكن تكون مش مطبقة على HTML الحقيقي — اختبر بمتصفح/أداة خارجية). أهم مخرَج: كل حادثة مستقبلية تضيف بندًا — وبعد ربع سنة القائمة بتبقى أقوى من أي قالب عام.",
             "resources": [
                 "https://cheatsheetseries.owasp.org/",
                 "https://top10.owasp.org/2025/",
                 "https://owasp.org/www-project-application-security-verification-standard/",
                 "https://learn.microsoft.com/aspnet/core/security/",
                 "https://learn.microsoft.com/azure/security/fundamentals/",
             ]},
            {"id": "s7-m2-l3-t2",
             "title": "مهمة 2: سجل تدقيق append-only + تنبيهات أمنية",
             "md": "نفّذ `AuditSaveChangesInterceptor` مع `IAuditContext` و`AuditRedactor`، وسجّل الأحداث العشرة (أو 6 منها على الأقل) في جدول `audit_entries`. امنع التعديل/الحذف من التطبيق والصلاحيات، وأضف اختبارين تكامليين يثبتوا التسجيل، وتنبيهين أمنيين (محاولات رفض متكررة · تصدير كبير).",
             "criteria": [
                 "`AuditEntry` بالحقول: وقت UTC · فعل · نوع/معرّف الكيان · **ActorId من التوكن** · ActorType · CorrelationId · SourceIp · Before/After JSON · ChangedFields · Reason.",
                 "الـinterceptor مسجّل (`AddInterceptors`) وبيشتغل على Added/Modified/Deleted، ومستثنى `AuditEntry` نفسه (بلا تكرار لا نهائي).",
                 "**إخفاء الحقول الحساسة** قبل التخزين (بطاقة/هوية/هاتف) مع اختبار يثبت إن القيمة ما بتظهرش في `BeforeJson`.",
                 "منع التعديل/الحذف: لا `Update/Delete` في الكود على `audit_entries` + `DENY UPDATE,DELETE` على مستوى قاعدة البيانات (أو جدول منفصل بصلاحيات مختلفة) + إثبات بأمر.",
                 "**3 أحداث يدوية** مضافة صراحةً: تسجيل دخول فاشل · تصدير بيانات شخصية · تغيير صلاحية/دور.",
                 "اختباران تكامليان (WebApplicationFactory + Testcontainers): الأول يثبت إن تعديل كيان ينتج صف تدقيق بالحقول الصح · الثاني يثبت إن `ActorId` مجهول يسجَّل anonymous وما يفشلش.",
                 "تنبيهان: ≥ 10 رفض (401/403/429) من نفس IP خلال 5 دقائق · تصدير أكثر من N سجل في طلب — مع runbook لكل واحد (7.2.1).",
                 "قرار الاحتفاظ مكتوب: كم شهرًا/سنة لكل نوع حدث، وكيف يُرحَّل/يُحذف (يرتبط بـ7.2.5).",
             ],
             "hint": "في الاختبارات التكاملية، `IHttpContextAccessor` بيشتغل تلقائيًا مع `WebApplicationFactory`، بس الـ`sub` claim ممكن ما يكونش موجود لو مستخدم اختبار بلا مصادقة — فاختبر الحالتين (مصادَق ومجهول). ولـ`DENY UPDATE,DELETE`: اعمل مستخدم DB منفصل للتطبيق وامنعه صراحةً، ثم جرّب `UPDATE audit_entries …` بهوية التطبيق وتتوقع فشل. ولتنبيه الـIP: سجل `SourceIp` في كل رفض (middleware) وصدره كمقياس بسمات محدودة (`status_class`, `route`) — **لا تصدر الـIP كسمة مقياس** (cardinality + بيانات شخصية): استخدم السجلات للتنبيه بدل المقاييس لو محتاج IP.",
             "solution": "الأخطاء النموذجية: (1) الـinterceptor بيتسجل بعد `AddDbContext` بدون تمرير الـoptions فيتجاهل — الحل `options.AddInterceptors(...)` داخل `AddDbContext`. (2) `BeforeJson` بيطلع فاضي لأن `OriginalValues` مش محمّلة لما الكيان `Detached`/من query بلا tracking — تأكد إن التغييرات جاية من tracked entities. (3) تكرار صفوف التدقيق في المعاملات الكبيرة: الصفوف بتُكتب في نفس المعاملة مع التغيير، فلو المعاملة تراجعت التدقيق كمان بيتراجع — وده **الصحيح** (ما تسجلش تغيير ما حصلش)؛ لو محتاج سجلًا حتى للفشل، اكتبه في معاملة منفصلة. (4) أهم اكتشاف: **سجل التدقيق نفسه بيانات شخصية** — فالحذف (7.2.5) بيتعارض مع الاحتفاظ القانوني؛ الحل المعتاد: إخفاء هوية الـActorId بعد انتهاء فترة الاحتفاظ بدل حذف الصف، مع توثيق الأساس القانوني للاحتفاظ.",
             "resources": [
                 "https://learn.microsoft.com/ef/core/logging-events-diagnostics/interceptors",
                 "https://learn.microsoft.com/aspnet/core/security/authorization/",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html",
                 "https://learn.microsoft.com/dotnet/standard/security/",
                 "https://csrc.nist.gov/pubs/sp/800/92/final",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "OWASP Top 10:2025", "url": "https://top10.owasp.org/2025/"},
            {"label": "OWASP Cheat Sheet Series", "url": "https://cheatsheetseries.owasp.org/"},
            {"label": "OWASP ASVS", "url": "https://owasp.org/www-project-application-security-verification-standard/"},
            {"label": "ASP.NET Core: الأمان", "url": "https://learn.microsoft.com/aspnet/core/security/"},
            {"label": "EF Core: Interceptors", "url": "https://learn.microsoft.com/ef/core/logging-events-diagnostics/interceptors"},
            {"label": "Azure Security Fundamentals", "url": "https://learn.microsoft.com/azure/security/fundamentals/"},
            {"label": "NIST SP 800-61: إدارة حوادث أمن المعلومات", "url": "https://csrc.nist.gov/pubs/sp/800/61"},
            {"label": "Microsoft Learn: حماية البيانات في .NET", "url": "https://learn.microsoft.com/dotnet/standard/security/"},
        ]},
    ],
}

LESSONS_S7_F = [_L3]
