"""Stage 5, Module 2 — Messaging & reliability (lesson 5 of 5): Idempotency."""

TODAY = "2026-10-22"

LESSONS_S5_E = [
    {
        "id": "s5-m2-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
في الأنظمة الموزعة، **التكرار هو القاعدة مش الاستثناء**: العميل بيعيد المحاولة بعد timeout،
الـgateway بيعيد المحاولة، الوسيط بيعيد التسليم (at-least-once)، الـsaga بيعوّض ويعيد،
وأسوأ حالة: **مش عارف هل العملية تمت ولا لأ** (النداء انقطع بعد التنفيذ وقبل الرد).

الحل الوحيد العملي: خلّي العمليات **idempotent** — تنفيذها مرة أو عشر مرات له نفس الأثر.
الدرس ده بيغطي المستويين: **idempotency طبيعية** في المنطق (الأفضل والأرخص)،
و**مفاتيح idempotency** للعمليات اللي مستحيل تكون طبيعية (خصم مبلغ، إنشاء كيان).
"""},
            {"type": "terms", "items": [
                {"term": "Idempotent Operation", "def": "عملية تنفيذها N مرة له نفس أثر تنفيذها مرة واحدة. `PUT /orders/1 {status:'cancelled'}` idempotent؛ `POST /orders` لأ."},
                {"term": "Idempotency-Key", "def": "معرّف يولّده **العميل** لكل عملية منطقية، والخادم يخزنه مع النتيجة — التكرار يرجع نفس الاستجابة بلا تنفيذ."},
                {"term": "Request Fingerprint (hash)", "def": "بصمة جسم الطلب المخزنة مع المفتاح: لو نفس المفتاح وصل بجسم مختلف → 409 (استخدام خاطئ للمفتاح)."},
                {"term": "Dedup Window", "def": "المدة اللي بنحتفظ فيها بالمفاتيح. لازم تغطي أقصى فترة إعادة تسليم/محاولة (وإلا التكرار المتأخر ينفذ تاني)."},
                {"term": "Natural Idempotency", "def": "العملية نفسها لا تتأثر بالتكرار (upsert، تحديث شرطي، انتقال حالة مرفوض لو تم) — ★ الأفضل: بلا جداول إضافية."},
                {"term": "Conditional Update", "def": "`UPDATE … WHERE version = @v` أو `WHERE status = 'placed'` → التكرار يؤثر في 0 صفوف (يمكن اكتشافه)."},
                {"term": "Inbox Pattern", "def": "جدول عند المستهلك يسجل معرّفات الرسائل المعالَجة — إلغاء تكرار على مستوى الرسائل (درس 4.2.3)."},
                {"term": "In-Flight Request", "def": "مفتاح مُسجَّل لكن العملية لسه بتتنفذ → التكرار المتزامن لازم ينتظر أو ياخد 409 (لا تنفيذ موازٍ)."},
                {"term": "Poison Retry", "def": "إعادة محاولة عملية نجحت فعلًا لأن الرد ضاع — سبب أشهر مشاكل الدفع والمخزون."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الدلالات: أنهي عملية idempotent بطبيعتها؟"},
            {"type": "table", "head": ["العملية", "idempotent؟", "السبب / إزاي تخليها"], "rows": [
                ["`GET`", "✓", "قراءة بلا أثر"],
                ["`PUT /orders/{id}` (المورد كامل)", "✓", "استبدال الحالة — التكرار يوصل لنفس النتيجة"],
                ["`DELETE /orders/{id}`", "✓ (دلاليًا)", "الحالة النهائية واحدة؛ لكن ارجع 404 أو 204 consistently (وثّق الاختيار)"],
                ["`PATCH` (تعديل جزئي ثابت)", "✓", "`{status:'cancelled'}` نعم · `{quantity: '+1'}` ✗ (تراكمي!)"],
                ["`POST /orders` (إنشاء)", "✗", "يحتاج idempotency key أو مفتاح عمل فريد (مثل `reference`)"],
                ["خصم مبلغ / تحصيل", "✗", "idempotency key + البوابة غالبًا بتدعمها (Stripe: `Idempotency-Key`)"],
                ["نقص مخزون بكمية", "✗ (تراكمي)", "اجعله مطلقًا (`SET stock = 8 WHERE stock = 10`) أو بمعرّف عملية"],
                ["إرسال إيميل/إشعار", "✗", "معرّف رسالة فريد + جدول تسليم (أو قبول التكرار كـ«أثر جانبي مقبول»)"],
                ["نشر حدث", "△", "الحدث نفسه يتكرر — المستهلك لازم يكون idempotent"],
                ["`UPDATE … SET status='cancelled' WHERE id=@id`", "✓", "تحديث مطلق (مش `status = status + 1`)"],
                ["`INSERT … ON CONFLICT DO NOTHING`", "✓", "upsert بمفتاح فريد — ★ الأنسب للمستهلكين"],
                ["زيادة عدّاد (`+1`)", "✗", "استخدم مفتاح حدث: `INSERT … ON CONFLICT DO NOTHING` ثم عدّ"],
            ]},
            {"type": "callout", "kind": "tip", "title": "القاعدة الأولى: ابحث عن idempotency طبيعية قبل ما تبني جدول مفاتيح",
             "md": """
**3 أسئلة تحسم أغلب الحالات:**
1. هل الأثر **مطلق** ولا **تراكمي**؟ (`SET total = 100` مقابل `total = total + 100`) — المطلق idempotent.
2. هل فيه **قيد فريد طبيعي** يمكن الاعتماد عليه؟ (`OrderId` في جدول الشحنات، `InvoiceNumber`، `(TenantId, Email)`) —
   `ON CONFLICT DO NOTHING` بيحل التكرار في عبارة واحدة.
3. هل **انتقال الحالة** مرفوض لو تم؟ (`Cancel()` على طلب ملغى = لا أثر) — ده idempotency من الـDomain (درس 4.2.1).

لو الإجابة «نعم» لأي واحدة → استخدمها. جدول المفاتيح حل للعمليات اللي **مالهاش مفتاح طبيعي** (مدفوعات، إنشاء موارد).
"""},
            {"type": "heading", "level": 2, "text": "2) idempotency طبيعية بكود"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Shipping/IdempotentOperations.cs", "title": "3 طرق عملية (بلا جدول مفاتيح)", "code": r'''
// ═══ ① قيد فريد + upsert (الأبسط والأقوى) ═══
public sealed class ShipmentScheduler(ShippingDbContext db)
{
    public async Task<Guid> ScheduleAsync(Guid orderId, Address address, CancellationToken ct)
    {
        // ★ التكرار مستحيل بنيويًا: (order_id) فريد في جدول الشحنات
        // (Shipment كيان بسيط: Id/OrderId/Address/Status — من درس 4.2.1)
        var shipment = Shipment.Schedule(orderId, address);

        await db.Database.ExecuteSqlInterpolatedAsync($"""
            INSERT INTO shipping.shipments (id, order_id, address_json, status, created_at)
            VALUES ({shipment.Id}, {orderId}, {JsonSerializer.Serialize(address)}::jsonb, 'Scheduled', now())
            ON CONFLICT (order_id) DO NOTHING
            """, ct);

        // ✓ ارجع المعرّف الفعلي (الموجود أو الجديد) — لا تفترض إن INSERT نجح
        var existingId = await db.Shipments.Where(s => s.OrderId == orderId)
                                           .Select(s => s.Id).FirstOrDefaultAsync(ct);
        return existingId;
    }
}

// ═══ ② تحديث شرطي (conditional update) — يكتشف التكرار بعدد الصفوف ═══
public sealed class StockService(CatalogDbContext db)
{
    /// <summary>خصم **مطلق** بشرط الحالة — التكرار يؤثر في 0 صفوف.</summary>
    public async Task<bool> DeductAsync(Guid productId, int fromQuantity, int toQuantity, CancellationToken ct)
    {
        var affected = await db.Database.ExecuteSqlInterpolatedAsync($"""
            UPDATE catalog.stock
            SET quantity = {toQuantity}, updated_at = now()
            WHERE product_id = {productId} AND quantity = {fromQuantity}
            """, ct);

        return affected == 1;      // ✓ 0 = حد تاني سبقك أو العملية تمت فعلًا (تحقق من الحالة)
    }

    /// <summary>إلغاء حجز بمعرّف الحجز (idempotent: إلغاء غير الموجود = نجاح).</summary>
    public async Task ReleaseAsync(Guid reservationId, CancellationToken ct)
    {
        var affected = await db.Database.ExecuteSqlInterpolatedAsync($"""
            UPDATE catalog.reservations SET status = 'Released', released_at = now()
            WHERE id = {reservationId} AND status = 'Held'
            """, ct);

        if (affected == 0)
            Log.Debug("reservation {ReservationId} already released — idempotent no-op", reservationId);
    }
}

// ═══ ③ حارس انتقال الحالة في الـDomain (درس 4.2.1) ═══
public partial class Order
{
    public void Cancel(string reason, IClock clock)
    {
        if (Status == OrderStatus.Cancelled) return;         // ✓ تكرار = لا أثر (بدل استثناء)
        if (Status is OrderStatus.Shipped or OrderStatus.Delivered)
            throw new OrderCannotBeCancelledException(Id, Status);
        // … باقي المنطق
    }
}

// ═══ ④ إلغاء تكرار الرسائل في Redis (للمستهلكين بلا جدول inbox) ═══
// requires: using StackExchange.Redis;
public sealed class RedisDeduplicator(IConnectionMultiplexer mux)
{
    /// <summary>
    /// SET NX EX: ذرّي — يرجع true لأول مرة فقط خلال نافذة إلغاء التكرار.
    /// ★ النافذة لازم تغطي أقصى فترة إعادة تسليم (وإلا تكرار متأخر ينفذ).
    /// </summary>
    public Task<bool> TryClaimAsync(string messageId, TimeSpan window) =>
        mux.GetDatabase().StringSetAsync($"dedup:{messageId}", "1", window, When.NotExists);

    public Task ReleaseAsync(string messageId) =>
        mux.GetDatabase().KeyDeleteAsync($"dedup:{messageId}");
}

// ── الاستخدام في مستهلك MassTransit ──
public sealed class OrderPlacedConsumer(RedisDeduplicator dedup, ILogger<OrderPlacedConsumer> log)
    : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        var messageId = context.MessageId?.ToString() ?? context.Message.OrderId.ToString();
        var ct = context.CancellationToken;

        if (!await dedup.TryClaimAsync(messageId, TimeSpan.FromHours(24)))
        {
            log.LogInformation("duplicate {MessageId} — acked without processing", messageId);
            return;                                          // ✓ ack بلا أثر
        }

        try
        {
            await HandleAsync(context.Message, ct);
        }
        catch
        {
            // ⚠ حرّر المفتاح بعد الفشل — وإلا إعادة التسليم لن تعالج الرسالة أبدًا
            await dedup.ReleaseAsync(messageId);
            throw;
        }
    }

    private Task HandleAsync(OrderPlaced message, CancellationToken ct) => Task.CompletedTask;   // منطقك
}
'''},
            {"type": "heading", "level": 2, "text": "3) مفاتيح idempotency (للعمليات اللي ملهاش مفتاح طبيعي)"},
            {"type": "code", "lang": "sql", "filename": "db/030_idempotency_keys.sql", "title": "الجدول والقيود", "code": r'''
CREATE TABLE IF NOT EXISTS orders.idempotency_keys (
    idempotency_key text        NOT NULL,
    tenant_id       uuid        NOT NULL,           -- ★ عزل المستأجرين (مفتاح واحد من مستأجرين مختلفين!)
    endpoint        text        NOT NULL,           -- يمنع استخدام نفس المفتاح على مسار مختلف
    request_hash    text        NOT NULL,           -- بصمة الجسم (كشف إعادة استخدام المفتاح بجسم مختلف)
    status          text        NOT NULL DEFAULT 'in_progress',   -- in_progress | completed | failed
    status_code     int         NULL,
    response_body   jsonb       NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    completed_at    timestamptz NULL,
    expires_at      timestamptz NOT NULL,           -- ★ نافذة إلغاء التكرار

    PRIMARY KEY (tenant_id, endpoint, idempotency_key)
);

-- التنظيف الدوري
CREATE INDEX ix_idempotency_expires ON orders.idempotency_keys (expires_at);

-- ⚠ ملاحظات تصميم:
-- ① المفتاح **يولّده العميل** (UUID) — لو ولّده الخادم، كل إعادة محاولة تاخد مفتاح جديد (بلا فائدة)
-- ② `expires_at` لازم يغطي أقصى فترة إعادة محاولة (عادة 24 ساعة للمدفوعات)
-- ③ `request_hash` يمنع: نفس المفتاح بجسم مختلف → 409 (خطأ عميل، مش تكرار)
-- ④ لا تخزن أسرار/بيانات حساسة في request_hash أو response_body بلا تشفير
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/IdempotencyFilter.cs", "title": "endpoint filter كامل: حجز → تنفيذ → تخزين الرد → إعادة تشغيل", "code": r'''
public static class IdempotencyEndpointFilter
{
    private const string HeaderName = "Idempotency-Key";
    private static readonly TimeSpan Window = TimeSpan.FromHours(24);

    /// <summary>
    /// يُستخدم على المسارات غير idempotent: `.AddEndpointFilter(IdempotencyEndpointFilter.Create())`
    /// </summary>
    public static IEndpointFilter Create(string endpointName) => new Filter(endpointName);

    private sealed class Filter(string endpointName) : IEndpointFilter
    {
        public async ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
        {
            var http = ctx.HttpContext;
            var ct = http.RequestAborted;
            var db = ctx.HttpContext.RequestServices.GetRequiredService<AppDbContext>();
            var log = ctx.HttpContext.RequestServices.GetRequiredService<ILogger<Filter>>();

            // ① المفتاح اختياري لكن موصى به بشدة — لو مفقود، نفّذ عادي (وسجّل)
            if (!http.Request.Headers.TryGetValue(HeaderName, out var keyValues) ||
                string.IsNullOrWhiteSpace(keyValues.FirstOrDefault()))
            {
                log.LogDebug("no idempotency key for {Endpoint}", endpointName);
                return await next(ctx);
            }

            var key = keyValues.First()!.Trim();
            if (key.Length is < 8 or > 128)
                return Results.Problem(statusCode: 400, title: "InvalidIdempotencyKey",
                                       detail: "طول المفتاح يجب أن يكون بين 8 و128 حرفًا");

            var tenantId = http.User.FindFirst("tenant_id")?.Value ?? "anonymous";
            var body = await ReadBodyAsync(http.Request, ct);
            var requestHash = ComputeHash(body);

            // ② هل المفتاح موجود؟
            var existing = await db.IdempotencyKeys.FirstOrDefaultAsync(
                k => k.TenantId == tenantId && k.Endpoint == endpointName && k.Key == key, ct);

            if (existing is not null)
            {
                // ③ نفس المفتاح بجسم مختلف → استخدام خاطئ (لا تخمين!)
                if (existing.RequestHash != requestHash)
                    return Results.Json(new
                    {
                        error = "idempotency_key_reused_with_different_body",
                        detail = "استخدم مفتاحًا جديدًا لكل عملية منطقية مختلفة",
                    }, statusCode: StatusCodes.Status409Conflict);

                // ④ لسه بتتنفذ → طلب متزامن (لا تنفيذ موازٍ)
                if (existing.Status == "in_progress")
                    return Results.Problem(statusCode: StatusCodes.Status409Conflict,
                        title: "RequestInProgress",
                        detail: "الطلب الأصلي لسه بيتنفذ — أعد المحاولة بعد قليل",
                        extensions: new Dictionary<string, object?> { ["retryAfterSeconds"] = 2 });

                // ⑤ ★ اكتملت قبل كده → أرجع **نفس الاستجابة** بلا تنفيذ
                if (existing.Status == "completed" && existing.ResponseBody is not null)
                {
                    log.LogInformation("idempotent replay for {Key}", key);
                    IdempotencyMetrics.Replays.Add(1, new("endpoint", endpointName));

                    // ✓ نكتب الاستجابة المخزنة حرفيًا — بلا تنفيذ للمنطق
                    http.Response.StatusCode = existing.StatusCode ?? 200;
                    http.Response.ContentType ??= "application/json; charset=utf-8";
                    await http.Response.WriteAsync(existing.ResponseBody, ct);
                    return Results.Empty;
                }

                // ⑥ فشلت قبل كده → اسمح بإعادة التنفيذ (لا نخزن الفشل للأبد)
                await db.IdempotencyKeys.Where(k => k.Key == key && k.TenantId == tenantId)
                                        .ExecuteDeleteAsync(ct);
            }

            // ⑦ احجز المفتاح **قبل** التنفيذ (قيد فريد يمنع التنفيذ المتوازي)
            try
            {
                db.IdempotencyKeys.Add(new IdempotencyKeyEntity(tenantId, endpointName, key, requestHash,
                    "in_progress", DateTimeOffset.UtcNow + Window));
                await db.SaveChangesAsync(ct);
            }
            catch (DbUpdateException ex) when (IsUniqueViolation(ex))
            {
                // ★ طلب متزامن سبقنا → 409 (لا تنفيذ مرتين)
                return Results.Problem(statusCode: StatusCodes.Status409Conflict,
                    title: "ConcurrentDuplicate", detail: "طلب مطابق قيد التنفيذ");
            }

            // ⑧ نفّذ العملية الفعلية
            object? result;
            try
            {
                result = await next(ctx);
            }
            catch (Exception ex)
            {
                await MarkFailedAsync(db, tenantId, endpointName, key, ct);
                log.LogError(ex, "idempotent operation failed for {Key}", key);
                throw;
            }

            // ⑨ التقط الاستجابة الفعلية (لأي نوع IHttpResult) ثم خزّنها واكتبها
            var (statusCode, body) = await CaptureResponseAsync(result, http, ct);
            await StoreResponseAsync(db, tenantId, endpointName, key, statusCode, body, ct);
            IdempotencyMetrics.Executions.Add(1, new("endpoint", endpointName));

            http.Response.StatusCode = statusCode;
            http.Response.ContentType ??= "application/json; charset=utf-8";
            await http.Response.WriteAsync(body, ct);
            return Results.Empty;
        }

        private static async Task<string> ReadBodyAsync(HttpRequest request, CancellationToken ct)
        {
            request.EnableBuffering();                                  // ✓ عشان نقدر نقرأ ونمرّر
            using var reader = new StreamReader(request.Body, leaveOpen: true);
            var body = await reader.ReadToEndAsync(ct);
            request.Body.Position = 0;
            return body;
        }

        private static string ComputeHash(string body) =>
            Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(body)));

        private static bool IsUniqueViolation(DbUpdateException ex) =>
            ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation };

        private static Task MarkFailedAsync(AppDbContext db, string tenant, string endpoint, string key, CancellationToken ct) =>
            db.IdempotencyKeys.Where(k => k.TenantId == tenant && k.Endpoint == endpoint && k.Key == key)
              .ExecuteUpdateAsync(s => s.SetProperty(k => k.Status, "failed")
                                        .SetProperty(k => k.CompletedAt, DateTimeOffset.UtcNow), ct);

        /// <summary>
        /// ★ يشغّل الـIHttpResult داخل buffer لالتقاط **نفس** البايتات وكود الحالة
        /// اللي كان العميل هيشوفهم — صحيح لكل الأنواع (Ok/Created/NoContent/Json/Problem).
        /// </summary>
        private static async Task<(int StatusCode, string Body)> CaptureResponseAsync(
            object? result, HttpContext http, CancellationToken ct)
        {
            if (result is not IHttpResult httpResult)
                return (StatusCodes.Status200OK, "{}");

            var originalBody = http.Response.Body;
            using var buffer = new MemoryStream();
            http.Response.Body = buffer;
            try
            {
                await httpResult.ExecuteAsync(http);          // ✓ يكتب في الـbuffer ويضبط StatusCode/ContentType
            }
            finally
            {
                http.Response.Body = originalBody;
            }

            return (http.Response.StatusCode, Encoding.UTF8.GetString(buffer.ToArray()));
        }

        private static Task StoreResponseAsync(AppDbContext db, string tenant, string endpoint, string key,
                                               int statusCode, string body, CancellationToken ct) =>
            db.IdempotencyKeys
              .Where(k => k.TenantId == tenant && k.Endpoint == endpoint && k.Key == key)
              .ExecuteUpdateAsync(s => s
                  .SetProperty(k => k.Status, "completed")
                  .SetProperty(k => k.StatusCode, statusCode)
                  .SetProperty(k => k.ResponseBody, body)
                  .SetProperty(k => k.CompletedAt, DateTimeOffset.UtcNow), ct);
    }
}

public static class IdempotencyMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Orders.idempotency", "1.0.0");
    public static readonly Counter<long> Replays = Meter.CreateCounter<long>("idempotency.replays");
    public static readonly Counter<long> Executions = Meter.CreateCounter<long>("idempotency.executions");
    public static readonly Counter<long> KeyConflicts = Meter.CreateCounter<long>("idempotency.key_conflicts");
}

// ── الكيان ──
// requires: using Microsoft.EntityFrameworkCore; using Npgsql; using System.Security.Cryptography;
//           using System.Text;
public class IdempotencyKeyEntity
{
    public IdempotencyKeyEntity(string tenantId, string endpoint, string key, string requestHash,
                                string status, DateTimeOffset expiresAt)
    {
        TenantId = tenantId;
        Endpoint = endpoint;
        Key = key;
        RequestHash = requestHash;
        Status = status;
        ExpiresAt = expiresAt;
        CreatedAt = DateTimeOffset.UtcNow;
    }

    public string TenantId { get; private set; }
    public string Endpoint { get; private set; }
    public string Key { get; private set; }
    public string RequestHash { get; private set; }
    public string Status { get; set; }
    public int? StatusCode { get; set; }
    public string? ResponseBody { get; set; }
    public DateTimeOffset CreatedAt { get; private set; }
    public DateTimeOffset? CompletedAt { get; set; }
    public DateTimeOffset ExpiresAt { get; private set; }
}

// وفي DbContext:
//   public DbSet<IdempotencyKeyEntity> IdempotencyKeys => Set<IdempotencyKeyEntity>();
//   modelBuilder.Entity<IdempotencyKeyEntity>(b => {
//       b.ToTable("idempotency_keys", "orders");
//       b.HasKey(k => new { k.TenantId, k.Endpoint, k.Key });          // ✓ مفتاح مركّب
//       b.Property(k => k.ResponseBody).HasColumnType("jsonb");
//       b.HasIndex(k => k.ExpiresAt);
//   });

// ── التنظيف الدوري (درس 2.3.6) ──
public sealed class IdempotencyCleanup(IServiceScopeFactory scopes, ILogger<IdempotencyCleanup> log)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromHours(1));
        while (await timer.WaitForNextTickAsync(ct))
        {
            await using var scope = scopes.CreateAsyncScope();
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var deleted = await db.IdempotencyKeys
                .Where(k => k.ExpiresAt < DateTimeOffset.UtcNow)
                .ExecuteDeleteAsync(ct);
            if (deleted > 0) log.LogInformation("purged {Count} expired idempotency keys", deleted);
        }
    }
}

// ── الاستخدام ──
// app.MapPost("/api/payments/capture", CaptureHandler)
//    .AddEndpointFilter(IdempotencyEndpointFilter.Create("payments.capture"))
//    .RequireAuthorization("Payments.Write");
'''},
            {"type": "callout", "kind": "danger", "title": "7 تفاصيل بتخلي idempotency تشتغل أو تنهار",
             "md": """
1. **المفتاح من العميل، لا الخادم** — لو الخادم ولّده، كل إعادة محاولة تاخد مفتاحًا جديدًا (صفر فائدة).
   وثّق ده في العقد (OpenAPI: header مطلوب/موصى به + مثال).
2. **نطاق المفتاح = عملية منطقية، مش طلب HTTP** — نفس المفتاح لعمليتين مختلفتين = 409.
   ولا تعيد استخدام مفتاح بعد نجاح العملية لطلب جديد.
3. **النافذة (TTL) لازم تغطي أقصى فترة إعادة محاولة** — لو العميل يعيد المحاولة لمدة ساعة وTTL 5 دقائق،
   التكرار المتأخر هيتنفذ. للمدفوعات: 24 ساعة عادةً.
4. **لا تخزن الفشل كاستجابة نهائية** — اسمح بإعادة التنفيذ بعد فشل (وإلا خطأ عابر يبقى دائمًا).
5. **عزل المستأجرين في المفتاح** — `(tenant_id, endpoint, key)` مش `key` لوحده (وإلا تصادم بين مستأجرين).
6. **التنفيذ المتزامن** — القيد الفريد + 409 (لا تنفيذين متوازيين). `SELECT` ثم `INSERT` بلا قيد = سباق.
7. **التنظيف** — مهمة دورية تحذف المفاتيح المنتهية (وإلا الجدول بيكبر بلا حدود).

⚠ **idempotency ≠ exactly-once delivery**: التسليم هيتكرر دايمًا؛ الأثر بس اللي بقى مرة واحدة.
ومتخليش idempotency يخفي bug: لو `Replays` مرتفع جدًا، فيه عميل بيعيد المحاولة بشكل مريض — حقق.
"""},
            {"type": "heading", "level": 2, "text": "4) الاختبارات (الحالات اللي بتظهر في الإنتاج)"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Orders.Tests/IdempotencyTests.cs", "title": "5 حالات حرجة", "code": r'''
public class IdempotencyTests(PostgresFixture db) : IClassFixture<PostgresFixture>
{
    private static string NewKey() => Guid.NewGuid().ToString("N");
    private static object Payload(decimal amount = 1000) =>
        new { order_id = Guid.NewGuid(), amount_minor = amount, currency = "EGP" };

    /// <summary>
    /// ★ HttpClient مفيهوش PostAsync(url, content, HttpRequestMessage) —
    /// نبني الطلب ونرسله بـSendAsync عشان نضيف الهيدر.
    /// </summary>
    private static Task<HttpResponseMessage> PostAsync(HttpClient client, string? key, object body)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/api/payments/capture")
        {
            Content = JsonContent.Create(body),
        };
        if (key is not null) request.Headers.Add("Idempotency-Key", key);
        return client.SendAsync(request);
    }

    // PostgresFixture من درس 5.2.1 (Testcontainers) + مساعدَين للاختبار:
    //   db.CreateWebApplication()   → WebApplicationFactory مع قاعدة حقيقية
    //   db.CountChargesAsync()      → عدد التحصيلات الفعلية (الأثر الحقيقي)
    //   db.FailNextCapture          → يحفّز فشل بوابة الدفع مرة واحدة

    [Fact]
    public async Task Duplicate_post_executes_once_and_replays_same_response()
    {
        await using var app = db.CreateWebApplication();
        var client = app.CreateClient();
        var key = NewKey();

        var first = await PostAsync(client, key, Payload());
        var second = await PostAsync(client, key, Payload());
        var third = await PostAsync(client, key, Payload());

        first.StatusCode.Should().Be(HttpStatusCode.OK);
        second.StatusCode.Should().Be(first.StatusCode);
        third.StatusCode.Should().Be(first.StatusCode);

        var firstBody = await first.Content.ReadAsStringAsync();
        (await second.Content.ReadAsStringAsync()).Should().Be(firstBody);
        (await third.Content.ReadAsStringAsync()).Should().Be(firstBody);

        // ★ الأثر الحقيقي: تحصيل واحد فقط
        (await db.CountChargesAsync()).Should().Be(1);
    }

    [Fact]
    public async Task Same_key_with_different_body_is_rejected_409()
    {
        await using var app = db.CreateWebApplication();
        var client = app.CreateClient();
        var key = NewKey();

        await PostAsync(client, key, Payload(amount: 1000));
        var second = await PostAsync(client, key, Payload(amount: 5000));

        second.StatusCode.Should().Be(HttpStatusCode.Conflict);
        (await second.Content.ReadAsStringAsync())
            .Should().Contain("idempotency_key_reused_with_different_body");
    }

    [Fact]
    public async Task Concurrent_duplicates_result_in_single_execution()
    {
        await using var app = db.CreateWebApplication();
        var client = app.CreateClient();
        var key = NewKey();

        // ★ 5 طلبات متزامنة بنفس المفتاح (سيناريو العميل العصبي / إعادة محاولة الشبكة)
        var responses = await Task.WhenAll(
            Enumerable.Range(0, 5).Select(_ => PostAsync(client, key, Payload())));

        responses.Count(r => r.StatusCode == HttpStatusCode.OK).Should().Be(1);
        responses.Count(r => r.StatusCode == HttpStatusCode.Conflict).Should().Be(4);
        (await db.CountChargesAsync()).Should().Be(1, "التنفيذ المتوازي ممنوع بالقيد الفريد");
    }

    [Fact]
    public async Task Failed_operation_can_be_retried_with_same_key()
    {
        await using var app = db.CreateWebApplication();
        var client = app.CreateClient();
        var key = NewKey();
        db.FailNextCapture = true;                            // ✓ فشل عابر من البوابة

        var failed = await PostAsync(client, key, Payload());
        failed.StatusCode.Should().Be(HttpStatusCode.BadGateway);

        // ★ الفشل لا يُخزن كاستجابة نهائية → إعادة التنفيذ مسموحة
        var retried = await PostAsync(client, key, Payload());
        retried.StatusCode.Should().Be(HttpStatusCode.OK);
        (await db.CountChargesAsync()).Should().Be(1);
    }

    [Fact]
    public async Task Request_without_key_is_not_protected()
    {
        await using var app = db.CreateWebApplication();
        var client = app.CreateClient();

        await PostAsync(client, key: null, Payload());
        await PostAsync(client, key: null, Payload());

        (await db.CountChargesAsync()).Should().Be(2, "بلا مفتاح = بلا حماية (ولهذا نوثّقه في OpenAPI)");
    }
}
'''},
            {"type": "callout", "kind": "note", "title": "وثّق الـidempotency في العقد (OpenAPI)",
             "md": """
idempotency بلا توثيق = عملاء ما يستخدموها. أضف في OpenAPI:
- **اسم الهيدر** ووصفه («UUID يولّده العميل لكل عملية منطقية»).
- **هل هو مطلوب أم موصى به**، وماذا يحدث بدونه.
- **نافذة إلغاء التكرار** (24 ساعة).
- **الاستجابات**: 200 (أول مرة)، 200 (إعادة تشغيل — نفس الجسم)، 409 (مفتاح مستخدم بجسم مختلف / طلب قيد التنفيذ).
- **مثال كامل** بـcurl.

وللاستهلاك الداخلي (خدمات تنادي بعضها): مرّر المفتاح تلقائيًا في `HttpClient` handler
(من `Activity.Current?.Id` أو معرّف العملية) — ولا تعتمد على كل مطور يفتكر.
"""},
            {"type": "checkpoints", "items": [
                "أفرّق بين idempotency طبيعية (الأفضل) ومفاتيح idempotency (للعمليات بلا مفتاح طبيعي).",
                "أصمم عمليات مطلقة (لا تراكمية) وأستخدم قيودًا فريدة وتحديثات شرطية لكشف التكرار.",
                "أنفّذ مفتاح idempotency بحجز قبل التنفيذ + بصمة للجسم + تخزين الاستجابة + عزل مستأجرين + تنظيف.",
                "أختبر الحالات الخمس: تكرار، جسم مختلف، تزامن، فشل ثم إعادة، وبلا مفتاح — وأوثق السلوك في OpenAPI.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`PATCH {\"quantity\": \"+1\"}` — idempotent؟",
                 "options": [
                     "نعم (PATCH idempotent)",
                     "لا — التعديل تراكمي: التكرار يزود الكمية كل مرة. اجعله مطلقًا (`{\"quantity\": 5}`) أو بمعرّف عملية",
                     "يعتمد على الخادم",
                     "نعم لو PUT",
                 ], "answer": 1,
                 "explain": "دلالية HTTP بتقول PATCH مش idempotent بطبيعته. الأهم من الدلالية: هل الأثر تراكمي ولا مطلق؟"},
                {"q": "مين يولّد الـidempotency key؟",
                 "options": [
                     "الخادم",
                     "العميل — لأنه الوحيد اللي يعرف إن الطلبين هما نفس العملية المنطقية (خصوصًا بعد timeout)",
                     "الوسيط",
                     "قاعدة البيانات",
                 ], "answer": 1,
                 "explain": "لو الخادم ولّده، كل إعادة محاولة تاخد مفتاحًا جديدًا والتكرار يتنفذ. القاعدة: العميل يولّد UUID ويعيد استخدامه في الإعادة."},
                {"q": "نفس المفتاح وصل بجسم مختلف. الرد؟",
                 "options": [
                     "نفّذ الطلب الجديد",
                     "409 مع خطأ واضح — ده استخدام خاطئ للمفتاح، والتنفيذ أو التخمين هيخفي bug عند العميل",
                     "أرجع الاستجابة القديمة",
                     "400",
                 ], "answer": 1,
                 "explain": "البصمة (request_hash) موجودة لكشف ده بالظبط. 409 = تعارض مفهوم وقابل للتصحيح من العميل."},
                {"q": "العملية فشلت (502 من بوابة الدفع) والمفتاح محفوظ. العميل أعاد بنفس المفتاح — التصرف؟",
                 "options": [
                     "أرجع الـ502 المخزنة",
                     "احذف/تجاهل السجل الفاشل ونفّذ من جديد — الفشل العابر لا يجب أن يصبح دائمًا",
                     "409",
                     "اطلب مفتاحًا جديدًا",
                 ], "answer": 1,
                 "explain": "خزّن الاستجابات **الناجحة** فقط (أو خزّن الفشل بـTTL قصير جدًا). وإلا خطأ شبكة عابر يمنع العملية للأبد."},
                {"q": "نافذة إلغاء التكرار 5 دقائق والعميل يعيد المحاولة لمدة ساعة. النتيجة؟",
                 "options": [
                     "لا مشكلة",
                     "التكرار المتأخر يُنفَّذ من جديد (المفتاح انتهت صلاحيته) — النافذة لازم تغطي أقصى فترة إعادة محاولة (24h للمدفوعات)",
                     "409",
                     "فشل دائم",
                 ], "answer": 1,
                 "explain": "حدّد النافذة من سلوك عملائك الفعلي (أقصى retry window) + أقصى redelivery في الوسيط، وخد الأكبر."},
                {"q": "مستهلك رسائل بيخصم مخزون. أحسن طريقة للـidempotency؟",
                 "options": [
                     "جدول مفاتيح في كل مستهلك",
                     "قيد فريد طبيعي (مثل `order_id` في الشحنات) + `ON CONFLICT DO NOTHING`، أو تحديث شرطي — أرخص وأقوى من جدول مفاتيح",
                     "تجاهل (at-least-once مقبول)",
                     "Redis فقط",
                 ], "answer": 1,
                 "explain": "ابدأ دائمًا بالـidempotency الطبيعية. جدول المفاتيح/الـinbox لما مفيش مفتاح عمل فريد (زي العمليات الخارجية)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "اجعل 5 عمليات idempotent",
                 "md": "جرّد العمليات غير idempotent في مشروعك (إنشاء، خصم، إشعار، نشر) وطبّق لكل واحدة أفضل آلية: طبيعية (قيد فريد/تحديث شرطي/حارس حالة) أو مفتاح idempotency. وثّق الاختيار لكل واحدة.",
                 "criteria": [
                     "جدول بالعمليات (≥ 5) × الآلية المختارة × السبب",
                     "3 عمليات على الأقل بـidempotency طبيعية (بلا جدول مفاتيح)",
                     "اختبار لكل عملية: تنفيذ مرتين → أثر واحد",
                     "لا عمليات تراكمية (`+1`) بلا مفتاح عملية",
                     "الـDomain بيرفض الانتقالات المكررة بلا استثناء (return مبكر) حيث يناسب",
                 ],
                 "hint": "لو عملية إشعار/إيميل: استخدم معرّف رسالة فريد + جدول تسليم بقيد فريد — التكرار يبقى «تم التسليم فعلًا» بدل إرسال مزدوج."},
                {"id": "t2", "title": "مفتاح idempotency كامل + توثيق",
                 "md": "نفّذ مفتاح idempotency لمسار كتابة حساس (دفع/إنشاء طلب) بالجدول والفلتر الكامل (حجز، بصمة، تخزين الاستجابة، عزل مستأجرين، تنظيف)، ووثّقه في OpenAPI، واختبر الحالات الخمس.",
                 "criteria": [
                     "جدول بـPK `(tenant_id, endpoint, key)` + `request_hash` + `expires_at` + فهرس للتنظيف",
                     "الحجز قبل التنفيذ (قيد فريد) + 409 عند التزامن (اختبار 5 طلبات متزامنة)",
                     "إعادة التشغيل ترجع **نفس** الاستجابة وكود الحالة (اختبار)",
                     "409 عند نفس المفتاح بجسم مختلف (اختبار)",
                     "الفشل لا يُخزن كاستجابة نهائية (اختبار إعادة بعد فشل)",
                     "مهمة تنظيف دورية + مقياس `Replays`/`Executions`/`KeyConflicts` مع إنذار لو Replays مرتفع",
                     "OpenAPI يوثق الهيدر والنافذة والاستجابات مع مثال curl",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Idempotent Receiver pattern", "url": "https://microservices.io/patterns/communication-style/idempotent-receiver.html"},
                {"label": "The Idempotency-Key HTTP header (IETF draft)", "url": "https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/"},
                {"label": "HTTP semantics — idempotent methods (RFC 9110)", "url": "https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods"},
                {"label": "Stripe — Idempotent requests", "url": "https://docs.stripe.com/api/idempotent_requests"},
                {"label": "Designing data-intensive applications (ch. 12)", "url": "https://dataintensive.net/"},
                {"label": "Minimal APIs — Endpoint filters", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/endpoint-filters"},
            ]},
        ],
    },
]
