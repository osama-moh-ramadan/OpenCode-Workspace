"""Stage 5, Module 2 — Messaging & reliability (lessons 1-2 of 5)."""

TODAY = "2026-10-22"

LESSONS_S5_C = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s5-m2-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لحد دلوقتي الأحداث كانت بتتنقل **داخل العملية** (MediatR notifications) أو عبر **outbox** لجدول في نفس القاعدة.
الخطوة التالية: وسيط رسائل حقيقي بين الخدمات — وده بيغيّر ضماناتك: التسليم بقى at-least-once،
الترتيب بقى محليًا، والفشل بقى جزئيًا.

الاختيار الأشهر في أنظمة .NET: **RabbitMQ** (وسيط رسائ عام، قوي في التوجيه والاعتمادية)
+ **MassTransit** (تجريد فوقه بيديك consumers وretry وsagas وoutbox واختبارات جاهزة).

الدرس ده بيمشي من الصفر: مفاهيم AMQP اللي بتحدد سلوكك فعلًا (exchanges، queues، acks، prefetch، DLX)،
ثم MassTransit بإعداد إنتاجي (retry، redelivery، outbox، صحة، مراقبة)، ثم اختبارات بلا وسيط حقيقي.
"""},
            {"type": "terms", "items": [
                {"term": "Exchange", "def": "نقطة استقبال الرسائل من الناشر وتوجيهها لقوائم بحسب قواعد (bindings). الأنواع: `direct`, `topic`, `fanout`, `headers`."},
                {"term": "Binding / Routing Key", "def": "قاعدة الربط بين exchange وqueue. في `topic`: نمط مثل `order.*.created` أو `order.#`."},
                {"term": "Queue", "def": "مخزن الرسائل لمستهلك واحد أو مجموعة (competing consumers). **قائمة لكل مجموعة مستهلكين**، مش قائمة مشتركة لكل الأنواع."},
                {"term": "Publish مقابل Send", "def": "Publish = حدث لمستهلكين غير معروفين (fan-out). Send = أمر لمستقبل محدد (queue واحدة)."},
                {"term": "ACK / NACK", "def": "تأكيد المستهلك بالاستلام/المعالجة. **manual ack بعد النجاح** هو النمط الآمن."},
                {"term": "Prefetch (QoS)", "def": "كم رسالة تُسلَّم للمستهلك قبل التأكيد — يحدد التوازن بين الإنتاجية والتوزيع العادل."},
                {"term": "Durability", "def": "queue دائمة + رسائل persistent = بقاء بعد إعادة تشغيل الوسيط. بلاها: فقد رسائل عند أي restart."},
                {"term": "Publisher Confirms", "def": "تأكيد الوسيط للناشر إن الرسالة استُلمت وحُفظت — بدونه النشر «best effort»."},
                {"term": "DLX (Dead Letter Exchange)", "def": "مصير الرسائل المرفوضة/المنتهية/الزائدة عن حد القائمة — ضروري للتشغيل."},
                {"term": "Quorum Queue", "def": "قائمة مبنية على Raft (نسخ متماثل قوي) — الموصى بها بدل classic mirrored في RabbitMQ الحديث."},
                {"term": "Poison Message", "def": "رسالة تفشل كل مرة (بيانات غلط/bug) — لازم تروح لـDLQ بدل ما توقف القائمة."},
                {"term": "Consumer Group (MassTransit endpoint)", "def": "كل `IConsumer<T>` له receive endpoint؛ النوع الواحد في أكتر من endpoint = نسخ متعددة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الوسيط: تشغيل ومفاهيم بتحدد سلوكك"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "تشغيل RabbitMQ + أدوات الفحص", "code": r'''
# ✓ صورة رسمية مع لوحة الإدارة (15672) وquorum queues
docker run -d --name shop-rabbit -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=shop -e RABBITMQ_DEFAULT_PASS=shop-dev-pass \
  rabbitmq:4-management-alpine

# فحص سريع من سطر الأوامر
docker exec shop-rabbit rabbitmqctl list_queues name messages consumers message_bytes
docker exec shop-rabbit rabbitmqctl list_exchanges name type
docker exec shop-rabbit rabbitmqctl list_bindings
docker exec shop-rabbit rabbitmq-diagnostics check_running check_local_alarms

# ⚠ أهم إنذارين في التشغيل:
#   • طول قائمة > 0 باستمرار  → المستهلك أبطأ من الناشر (أو واقع)
#   • ذاكرة/قرص alarm         → الوسيط بيحجب النشر (block)
'''},
            {"type": "code", "lang": "xml", "filename": "docker-compose.yml", "title": "إعداد إنتاجي مصغّر في compose", "code": r'''
services:
  rabbitmq:
    image: rabbitmq:4-management-alpine
    hostname: shop-rabbit                     # ★ مهم: الاسم يحدد هوية العقدة في الـcluster
    environment:
      RABBITMQ_DEFAULT_USER: shop
      RABBITMQ_DEFAULT_PASS: ${RABBIT_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: /shop
      RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: >
        -rabbit max_memory 512MB
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
      - ./infra/rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro   # ★ بنية معلنة ككود
    ports: ["5672:5672", "15672:15672"]
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
    deploy:
      resources: { limits: { memory: 768M, cpus: "1.0" } }

  orders-api:
    build: ./src/Services/Orders
    depends_on:
      rabbitmq: { condition: service_healthy }
      postgres:  { condition: service_healthy }
    environment:
      ConnectionStrings__RabbitMq: amqp://shop:${RABBIT_PASSWORD}@rabbitmq:5672/shop

volumes: { rabbitmq-data: {} }
'''},
            {"type": "table", "head": ["نوع Exchange", "التوجيه", "الحالة النموذجية", "مثال"], "rows": [
                ["`direct`", "routing key مطابق تمامًا", "أحداث بنوع واحد محدد", "`order.created` → قائمة الفوترة"],
                ["`topic`", "نمط (`order.*.created`, `order.#`)", "★ الأشهر: اشتراك مرن بحسب المجال/النوع", "`shipping.#` لكل أحداث الشحن"],
                ["`fanout`", "لكل القوائم المرتبطة (بلا مفتاح)", "بث لعدة أنظمة", "إشعار تغيير سعر لكل المستهلكين"],
                ["`headers`", "مطابقة رؤوس الرسالة", "نادر (أبطأ وأقل وضوحًا)", "—"],
                ["`(default/AMQP default)`", "اسم القائمة كـrouting key", "أوامر مباشرة لقائمة محددة", "MassTransit `Send`"],
            ]},
            {"type": "callout", "kind": "warn", "title": "قرارات RabbitMQ اللي بتحدد الموثوقية (اكتبها في ADR)",
             "md": """
1. **قوائم quorum** (مش classic mirrored): نسخ متماثل قوي بـRaft، وموصى به في الإصدارات الحديثة.
2. **دوام كامل**: queue durable + messages persistent (`delivery_mode=2`) → بقاء بعد إعادة تشغيل.
3. **Publisher confirms** مفعّلة على الناشر → تعرف إن الرسالة وصلت فعلًا (MassTransit بيدعمها).
4. **manual ack بعد المعالجة الناجحة** → لا `auto-ack` لعمل حرج (فقد عند الانهيار).
5. **`prefetch` محدود** (مثلاً 10-50 لكل مستهلك): بلا حدود، مستهلك واحد ياخد كل الرسائل والقوائم التانية تجوع.
6. **DLX + DLQ لكل قائمة عمل**: الرسائل المرفوضة بعد المحاولات تروح لمكان تُفحص فيه.
7. **قائمة لكل مجموعة مستهلكين** (مش قائمة مشتركة لأنواع مختلفة) → وإلا خدمة تانية هتاخد رسائلك.
8. **TTL للرسائل والقوائم** حيث يناسب (مثلاً: طلب تصدير قديم بلا قيمة).
9. **مراقبة إلزامية**: طول القائمة، معدل الاستهلاك، الذاكرة/القرص، عدد الاتصالات، وحالات unacked.
10. **حدود حجم الرسالة**: رسائل كبيرة → **claim check** (خزّن الحمولة في blob/S3 ومرّر المرجع).
"""},
            {"type": "heading", "level": 2, "text": "2) MassTransit: إعداد إنتاجي"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add src/Services/Orders package MassTransit
dotnet add src/Services/Orders package MassTransit.RabbitMQ
dotnet add src/Services/Orders package MassTransit.EntityFrameworkCore   # outbox/saga persistence
dotnet add src/Services/Orders package Microsoft.Extensions.Diagnostics.HealthChecks
dotnet add tests/Shop.Orders.Tests package MassTransit.Testing
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Messaging/BusRegistration.cs", "title": "التهيئة الكاملة: retry، redelivery، outbox، صحة، مراقبة", "code": r'''
using MassTransit;

public static class BusRegistration
{
    public static IServiceCollection AddOrderMessaging(this IServiceCollection services, IConfiguration config)
    {
        services.AddMassTransit(x =>
        {
            // ① المستهلكون من نفس التجميع + تسجيل endpoints تلقائيًا بأسماء kebab-case
            x.AddConsumers(typeof(OrderPlacedConsumer).Assembly);
            x.AddSagaStateMachines(typeof(OrderFulfillmentStateMachine).Assembly);

            // ★ ② Outbox مدمج مع EF Core: الرسالة تُكتب في معاملة البيانات (درس 4.2.3)
            x.AddEntityFrameworkOutbox<AppDbContext>(o =>
            {
                o.UsePostgres();                    // أو UseSqlServer/UseSqlite
                o.UseBusOutbox();                   // ✓ الناشر يكتب في outbox لا للوسيط مباشرة
                o.QueryDelay = TimeSpan.FromSeconds(1);
                o.DisableInboxCleanupInterval = TimeSpan.FromMinutes(5);
            });

            // ✓ ③ Inbox (إلغاء تكرار على جانب المستهلك) مدمج مع EF outbox نفسه —
            //   بلا حاجة لفلتر يدوي: `UseBusOutbox` بيخزن الرسائل الواردة المعالَجة ويمنع إعادة التنفيذ.

            x.UsingRabbitMq((context, cfg) =>
            {
                cfg.Host(new Uri(config["RabbitMq:Host"]!), h =>
                {
                    h.Username(config["RabbitMq:Username"]!);
                    h.Password(config["RabbitMq:Password"]!);
                    h.Heartbeat(TimeSpan.FromSeconds(30));           // ✓ كشف الاتصال الميت
                });

                cfg.UseTimeout(t => t.Timeout = TimeSpan.FromSeconds(30));

                // ★ ④ إعادة المحاولة: فوري (لأخطاء عابرة) ثم redelivery (لفشل أطول)
                cfg.UseMessageRetry(r =>
                {
                    r.Interval(3, TimeSpan.FromSeconds(1));          // 3 محاولات فورية
                    r.Ignore<ValidationException>();                 // ✗ لا تُعد محاولة خطأ بيانات
                    r.Ignore<NotFoundException>();                   // ✗ ولا حالة غير موجودة
                    r.Handle<HttpRequestException>();                // ✓ أخطاء اعتماديات خارجية
                    r.Handle<RabbitMqConnectionException>();
                });

                cfg.UseDelayedRedelivery(r => r.Intervals(
                    TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(5), TimeSpan.FromMinutes(15)));

                // ⑤ ترتيب المعالجة داخل consumer واحد (لو محتاج تسلسلًا صارمًا)
                // cfg.UseInMemoryOutbox();   // ← فقط لو لسه ما استخدمتش EF outbox

                // ⑥ مراقبة: OpenTelemetry + مقاييس + health
                cfg.UseOpenTelemetry(otel => otel
                    .SetServiceName("orders-bus")
                    .AddSource("MassTransit"));

                // ⑦ حدود عامة تُطبق على كل endpoints (ولكل consumer إعدادات أدق إن لزم)
                cfg.PrefetchCount = 16;                    // ✓ لا unlimited (توزيع عادل بين المستهلكين)
                cfg.ConcurrentMessageLimit = 8;            // حد التوازي داخل المستهلك الواحد

                // ⑧ endpoints تلقائية بأسماء kebab-case (endpoint لكل نوع رسالة)
                cfg.ConfigureEndpoints(context, new KebabCaseEndpointNameFormatter("orders", false));

                // ✓ قوائم الأخطاء تلقائية في MassTransit: `<endpoint>_error` للرسائل الفاشلة
                //   و`<endpoint>_skipped` للرسائل غير القابلة للتوجيه — راقب طولهما وأنشئ إنذارًا.
            });
        });

        // ✓ فحص صحة الوسيط (لـreadiness probe) — AddMassTransit يسجّل فحصًا تلقائيًا كمان
        services.AddHealthChecks().AddMassTransitBusCheck();

        return services;
    }
}

// استثناءات مخصصة تستخدمها سياسات إعادة المحاولة والاستهلاك:
public sealed class PoisonMessageException(string reason, Exception? inner = null)
    : Exception($"رسالة غير قابلة للمعالجة: {reason}", inner);

/// <summary>فحص صحة مخصص للوسيط (يُستخدم في readiness probe).</summary>
public sealed class MessagingHealthCheck(IEventPublisher publisher) : IHealthCheck
{
    public Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct = default) =>
        Task.FromResult(HealthCheckResult.Healthy("messaging provider registered"));
}

/// <summary>للتطوير المحلي: outbox يُكتب لكن بلا وسيط (بلا رسائل طائرة في بيئتك).</summary>
public sealed class NoopPublisher(ILogger<NoopPublisher> log) : IEventPublisher
{
    public Task PublishAsync<TEvent>(string topic, string partitionKey, TEvent evt, CancellationToken ct)
        where TEvent : IIntegrationEvent
    {
        log.LogDebug("outbox-only mode: {Type} → {Topic} (لم يُنشر)", typeof(TEvent).Name, topic);
        return Task.CompletedTask;
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Messaging/Contracts.cs", "title": "عقود الرسائل: records في مشروع مشترك", "code": r'''
// ★ الرسائل في مشروع `Shop.Contracts` مستقل — لا في خدمة واحدة (المستهلكون يحتاجونها)
namespace Shop.Contracts.Orders;

/// <summary>
/// حدث ماضٍ، غير قابل للتعديل، ذاتي الاحتواء.
/// ⚠ قواعد العقد: إضافة حقل اختياري = آمن. حذف/تغيير اسم أو دلالة = كاسر (درس 5.1.2).
/// </summary>
public sealed record OrderPlaced(
    Guid OrderId,
    Guid CustomerId,
    decimal TotalMinorUnits,          // ★ minor units (لا decimal عبر بعض الوسائط، ولا double أبدًا)
    string Currency,
    string Country,
    int LineCount,                    // ✓ بيانات كافية للتوجيه (لا كيان كامل — claim check للأحمال الكبيرة)
    DateTimeOffset OccurredAt,
    int SchemaVersion = 2);           // ✓ إصدار المخطط داخل الرسالة

public sealed record OrderCancelled(Guid OrderId, string Reason, DateTimeOffset OccurredAt, int SchemaVersion = 1);
public sealed record OrderShipped(Guid OrderId, DateTimeOffset OccurredAt, int SchemaVersion = 1);

/// <summary>أمر (Send، مش Publish): مستقبل محدد ومسؤولية واحدة.</summary>
public sealed record ReserveStock(Guid OrderId, IReadOnlyList<StockLine> Lines, Guid IdempotencyKey);
public sealed record StockLine(Guid ProductId, int Quantity);

/// <summary>رد على أمر (request/response).</summary>
public sealed record StockReserved(Guid OrderId, Guid ReservationId, DateTimeOffset ExpiresAt);
public sealed record StockReservationFailed(Guid OrderId, string Reason, IReadOnlyList<Guid> UnavailableProducts);

/// <summary>حدث تكاملي من موديول تاني (يُستهلك لتحديث نسخة محلية).</summary>
public sealed record ProductPriceChanged(Guid ProductId, decimal PriceMinorUnits, string Currency, DateTimeOffset OccurredAt);
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Shipping/Consumers/OrderPlacedConsumer.cs", "title": "مستهلك إنتاجي: idempotent، نطاق DI، فشل صريح", "code": r'''
using MassTransit;

/// <summary>
/// ✓ كل مستهلك = نطاق DI خاص (scoped) — MassTransit بيحل الاعتماديات لكل رسالة.
/// ✓ الاستثناء = إعادة محاولة (بحسب السياسة). بلا استثناء = ack تلقائي.
/// </summary>
public sealed class OrderPlacedConsumer(
    ShippingDbContext db, IShipmentScheduler scheduler, ILogger<OrderPlacedConsumer> log)
    : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        var message = context.Message;

        // ① idempotency طبيعية: إعادة التسليم لا تُنشئ شحنة مكررة (درس 4.2.3)
        if (await db.Shipments.AnyAsync(s => s.OrderId == message.OrderId, context.CancellationToken))
        {
            log.LogInformation("shipment already exists for {OrderId} — duplicate delivery", message.OrderId);
            return;                                    // ✓ ack بلا أثر
        }

        // ② تجاهل صريح للرسائل القديمة جدًا (لا شغل بلا قيمة)
        if (message.OccurredAt < DateTimeOffset.UtcNow.AddDays(-7))
        {
            log.LogWarning("discarding stale order.placed for {OrderId}", message.OrderId);
            return;
        }

        // ③ العمل في معاملة واحدة مع سجل الـinbox
        await using var tx = await db.Database.BeginTransactionAsync(context.CancellationToken);

        var shipment = await scheduler.ScheduleAsync(
            orderId: message.OrderId,
            country: message.Country,
            weightHint: message.LineCount,
            ct: context.CancellationToken);

        db.Shipments.Add(shipment);
        await db.SaveChangesAsync(context.CancellationToken);

        // ④ حدث تابع (يُنشر عبر outbox لو مفعّل — وإلا بعد الالتزام)
        await context.Publish(new ShipmentScheduled(shipment.Id, message.OrderId, shipment.Carrier, DateTimeOffset.UtcNow),
                              context.CancellationToken);

        await tx.CommitAsync(context.CancellationToken);

        log.LogInformation("shipment {ShipmentId} scheduled for {OrderId}", shipment.Id, message.OrderId);
    }
}

/// <summary>
/// مستهلك لأمر (Send): يردّ بـRespond — نمط request/response.
/// </summary>
public sealed class ReserveStockConsumer(IStockService stock, ILogger<ReserveStockConsumer> log)
    : IConsumer<ReserveStock>
{
    public async Task Consume(ConsumeContext<ReserveStock> context)
    {
        var result = await stock.TryReserveAsync(context.Message.OrderId, context.Message.Lines,
                                                 context.Message.IdempotencyKey, context.CancellationToken);

        if (result.Success)
            await context.RespondAsync(new StockReserved(context.Message.OrderId, result.ReservationId, result.ExpiresAt));
        else
            await context.RespondAsync(new StockReservationFailed(context.Message.OrderId, result.Reason, result.Missing));
            // ✓ الرد بفشل صريح أفضل من رمي استثناء (الاستثناء = إعادة محاولة بلا فائدة)
    }
}

/// <summary>الناشر من مسار الكتابة — عبر IPublishEndpoint (بيكتب في outbox لو مفعّل).</summary>
public sealed class OrderEventPublisher(IPublishEndpoint publishEndpoint) : IOrderEventPublisher
{
    public Task PublishPlacedAsync(Order order, CancellationToken ct) =>
        publishEndpoint.Publish(new OrderPlaced(
            order.Id, order.CustomerId,
            (long)Math.Round(order.Total.Amount * 100m), order.Total.Currency,
            order.ShippingAddress.Country, order.CreatedAt), ct);
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Clients/StockClient.cs", "title": "request/response بمهلة، وفحص الصحة والمراقبة", "code": r'''
// ═══ ① طلب/رد مع مهلة صريحة (بلاها: نداء متعلّق للأبد) ═══
public sealed class StockClient(IBus bus, ILogger<StockClient> log) : IStockClient
{
    private static readonly TimeSpan RequestTimeout = TimeSpan.FromSeconds(5);

    public async Task<StockReservation> ReserveAsync(Guid orderId, IReadOnlyList<StockLine> lines, CancellationToken ct)
    {
        var client = bus.CreateRequestClient<ReserveStock>(RequestTimeout);

        try
        {
            var response = await client.GetResponse<StockReserved, StockReservationFailed>(
                new ReserveStock(orderId, lines, IdempotencyKey: orderId), ct);

            // ✓ MassTransit بيرجع أي نوع من الاثنين — فحص أيهما وصل
            if (response.TryGetMessage(out Response<StockReserved> reserved))
                return StockReservation.Ok(reserved.Message.ReservationId, reserved.Message.ExpiresAt);

            if (response.TryGetMessage(out Response<StockReservationFailed> failed))
                return StockReservation.Rejected(failed.Message.Reason, failed.Message.UnavailableProducts);

            throw new InvalidOperationException("رد غير متوقع من خدمة المخزون");
        }
        catch (RequestTimeoutException ex)
        {
            log.LogWarning(ex, "stock service timed out for {OrderId}", orderId);
            throw new DependencyUnavailableException("stock");       // → 503 (لا تخمين)
        }
    }
}

// ═══ ② فحص صحة مخصص: هل الوسيط متصل **ويستهلك فعلًا**؟ ═══
public sealed class RabbitHealthCheck(IBusControl bus, IConfiguration config) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct = default)
    {
        if (bus.ConnectStatus != BusConnectStatus.Connected)
            return HealthCheckResult.Unhealthy("RabbitMQ غير متصل",
                data: new Dictionary<string, object> { ["status"] = bus.ConnectStatus.ToString() });

        // ✓ جاهزية مش بس اتصال: هل فيه receive endpoints نشطة؟
        var endpoints = bus.GetReceiveEndpoints().Count();
        return endpoints > 0
            ? HealthCheckResult.Healthy($"متصل بـ{endpoints} endpoint")
            : HealthCheckResult.Degraded("متصل لكن بلا receive endpoints");
    }
}

// ═══ ③ مقاييس تشغيلية مهمة (انشرها في Grafana) ═══
// من لوحة RabbitMQ (prometheus plugin):
//   rabbitmq_queue_messages                 ← طول القائمة (الأهم: إنذار لو > حد لفترة)
//   rabbitmq_queue_messages_unacknowledged ← رسائل مسلَّمة بلا تأكيد (مستهلك عالق)
//   rabbitmq_queue_messages_ready          ← منتظرة (ضغط استهلاك)
//   rabbitmq_connections / channels        ← تسريب اتصالات
//   rabbitmq_channel_messages_published_total / delivered_total  ← معدل النشر مقابل الاستهلاك
'''},
            {"type": "heading", "level": 2, "text": "3) الاختبارات: بلا وسيط حقيقي وبوسيط حقيقي"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Orders.Tests/Messaging/ConsumerTests.cs", "title": "TestHarness (in-memory) + Testcontainers (تكامل)", "code": r'''
// ═══ ① اختبار مستهلك معزول (الأسرع — للمنطق) ═══
public class OrderPlacedConsumerTests
{
    [Fact]
    public async Task Duplicate_delivery_creates_single_shipment()
    {
        await using var provider = new ServiceCollection()
            .AddDbContext<ShippingDbContext>(o => o.UseNpgsql(TestDb.ConnectionString))
            .AddMassTransitTestHarness(x => x.AddConsumer<OrderPlacedConsumer>())
            .BuildServiceProvider(true);

        var harness = provider.GetRequiredService<ITestHarness>();
        await harness.Start();

        var message = new OrderPlaced(Guid.NewGuid(), Guid.NewGuid(), 25050, "EGP", "EG", 2, DateTimeOffset.UtcNow);

        await harness.Bus.Publish(message);          // ★ النشر 3 مرات = إعادة تسليم
        await harness.Bus.Publish(message);
        await harness.Bus.Publish(message);

        Assert.True(await harness.Consumed.Any<OrderPlaced>(x => x.Context.Message.OrderId == message.OrderId,
                                                            TimeSpan.FromSeconds(10)));

        var db = provider.GetRequiredService<ShippingDbContext>();
        (await db.Shipments.CountAsync(s => s.OrderId == message.OrderId)).Should().Be(1, "idempotent");

        await harness.Stop();
    }

    [Fact]
    public async Task Validation_failure_is_not_retried_and_faults_once()
    {
        await using var provider = new ServiceCollection()
            .AddMassTransitTestHarness(x =>
            {
                x.AddConsumer<ThrowingConsumer>(c => c.UseMessageRetry(r => r.Ignore<ValidationException>()));
            })
            .BuildServiceProvider(true);

        var harness = provider.GetRequiredService<ITestHarness>();
        await harness.Start();

        await harness.Bus.Publish(new OrderCancelled(Guid.NewGuid(), "", DateTimeOffset.UtcNow));

        // ✓ الخطأ المتجاهل لا يُعاد → fault واحد فقط
        Assert.True(await harness.Consumed.Any<Fault<OrderCancelled>>(TimeSpan.FromSeconds(5)));
        ThrowingConsumer.Attempts.Should().Be(1);

        await harness.Stop();
    }
}

// ═══ ② اختبار تكامل على RabbitMQ حقيقي (Testcontainers) — للتوجيه والـretry والـDLQ ═══
public class RabbitIntegrationTests : IAsyncLifetime
{
    private readonly RabbitMqContainer _rabbit = new RabbitMqBuilder()
        .WithImage("rabbitmq:4-management-alpine")
        .WithUsername("shop").WithPassword("test-pass")
        .Build();

    // helper محلي: RabbitMQ Management HTTP API على منفذ 15672 (list_queues)

    public async ValueTask InitializeAsync() => await _rabbit.StartAsync();
    public async ValueTask DisposeAsync() => await _rabbit.DisposeAsync();

    [Fact]
    public async Task Poison_message_lands_in_error_queue_after_retries()
    {
        var services = new ServiceCollection()
            .AddMassTransit(x =>
            {
                x.AddConsumer<AlwaysFailingConsumer>();
                x.UsingRabbitMq((ctx, cfg) =>
                {
                    cfg.Host(_rabbit.GetConnectionString());
                    cfg.UseMessageRetry(r => r.Immediate(2));       // محاولتان ثم فشل
                    cfg.ConfigureEndpoints(ctx);
                });
            });

        await using var provider = services.BuildServiceProvider(true);
        var bus = provider.GetRequiredService<IBusControl>();
        await bus.StartAsync();

        await bus.Publish(new PoisonMessage(Guid.NewGuid()));
        await Task.Delay(TimeSpan.FromSeconds(5));                  // انتظر المحاولات

        // ✓ التحقق من قائمة الأخطاء عبر API الإدارة
        var errorCount = await RabbitManagement.GetQueueLengthAsync(_rabbit, "always-failing_error");
        errorCount.Should().Be(1, "الرسالة السامة وصلت لـerror queue بدل ما توقف القائمة");

        AlwaysFailingConsumer.Attempts.Should().Be(3);              // 1 + محاولتان
        await bus.StopAsync();
    }

    [Fact]
    public async Task Messages_survive_broker_restart_when_durable()
    {
        // انشر → أوقف الحاوية → شغّلها → تحقق إن الرسالة لسه موجودة (durable + persistent)
        // ★ ده الاختبار اللي بيثبت إن إعدادات الدوام مش مجرد كلام
    }
}
'''},
            {"type": "heading", "level": 2, "text": "4) أخطاء بتكلّفك رسائل ضائعة أو نظام واقع"},
            {"type": "table", "head": ["الخطأ", "النتيجة", "الإصلاح"], "rows": [
                ["النشر قبل/خارج معاملة الحفظ", "رسالة شبحية أو ضائعة", "**outbox** في نفس المعاملة (MassTransit EF outbox)"],
                ["إعادة محاولة كل الاستثناءات", "رسالة بيانات غلط تدور للأبد وتوقف القائمة", "`Ignore<ValidationException>`/`NotFoundException` + DLQ"],
                ["بلا idempotency في المستهلك", "أثر مضاعف عند أي إعادة تسليم", "inbox أو idempotency طبيعية (فحص وجود)"],
                ["`prefetch` بلا حد", "مستهلك واحد يحتكر الرسائل والآخرون يجوعون", "16-64 + `ConcurrentMessageLimit`"],
                ["قائمة مشتركة لأنواع مختلفة", "رسائل تروح لمستهلك غلط وتُفقد", "endpoint لكل نوع رسالة (MassTransit بيعمله تلقائيًا)"],
                ["`Send` بدل `Publish` للأحداث", "اقتران بمستقبل محدد وبلا fan-out", "أحداث → `Publish`؛ أوامر → `Send`"],
                ["اتصال/قناة جديدة لكل رسالة", "استنزاف موارد وبطء شديد", "اتصال واحد (IBus singleton) — MassTransit بيديره"],
                ["تجاهل `_error`/`_skipped` queues", "رسائل فاشلة تتراكم بلا حد يلاحظ", "مراقبة + إنذار + أداة إعادة تشغيل"],
                ["رسائل ضخمة (> 100KB)", "ضغط على الذاكرة وشبكة وبطء عام", "claim check: الحمولة في blob والمرجع في الرسالة"],
                ["بلا مهلة في request/response", "طلب متعلّق لحد ما ينفد الـpool", "`CreateRequestClient<T>(timeout)` صريح"],
                ["الاعتماد على ترتيب القوائم العام", "ترتيب غير مضمون مع مستهلكين متعددين", "رتّب منطقيًا (إصدار/تاريخ في الرسالة) أو استخدم قائمة واحدة بمستهلك واحد"],
                ["إعادة تشغيل الوسيط بلا قوائم دائمة", "فقد كل الرسائل", "durable queues + persistent messages + confirms"],
            ]},
            {"type": "checkpoints", "items": [
                "أشغّل RabbitMQ بإعداد معلن ككود (definitions.json) وأعرف قرارات الموثوقية العشرة.",
                "أضبط MassTransit بإعداد إنتاجي: retry + delayed redelivery + استثناءات متجاهلة + EF outbox + prefetch.",
                "أفرّق بين `Publish` (حدث) و`Send` (أمر) وأصمم عقود الرسائل كـrecords بإصدار مخطط.",
                "أكتب مستهلكين idempotent بنطاق DI لكل رسالة، وأختبر بالـTestHarness وعلى حاوية حقيقية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "الفرق بين `Publish` و`Send` في MassTransit؟",
                 "options": [
                     "لا فرق",
                     "Publish = حدث يُوجَّه لكل المستهلكين المهتمين (fan-out عبر exchange)؛ Send = أمر لقائمة/مستقبل محدد واحد",
                     "Send أسرع",
                     "Publish للأوامر",
                 ], "answer": 1,
                 "explain": "القاعدة الدلالية: حدث (ماضي، «حصل كذا») → Publish. أمر (مستقبلي، «اعمل كذا») → Send."},
                {"q": "ليه `Ignore<ValidationException>` في سياسة إعادة المحاولة؟",
                 "options": [
                     "للأداء",
                     "لأن خطأ البيانات لن يُصلح نفسه بإعادة المحاولة — الرسائل دي لازم تروح لـDLQ بدل ما تستهلك المحاولات وتوقف القائمة",
                     "مطلب MassTransit",
                     "لتقليل اللوجات",
                 ], "answer": 1,
                 "explain": "أعد المحاولة للأخطاء العابرة (شبكة، timeout، 503). الأخطاء الدائمة (تحقق، غير موجود، حالة غير صالحة) → فشل صريح + DLQ."},
                {"q": "رسالة وصلت لمستهلكين مختلفين مرتين. إيه المطلوب؟",
                 "options": [
                     "إيقاف الوسيط",
                     "لا شيء على مستوى الوسيط (at-least-once متوقع) — المطلوب idempotency في المستهلك",
                     "تقليل prefetch",
                     "استخدام fanout",
                 ], "answer": 1,
                 "explain": "التكرار جزء من العقد. الحل: فحص وجود الأثر، أو inbox بمعرّف الرسالة، أو قيد فريد في قاعدة المستهلك."},
                {"q": "طول قائمة RabbitMQ بي زاد باستمرار. أول تشخيص؟",
                 "options": [
                     "الوسيط بطيء",
                     "هل المستهلكون يعملون؟ (عدد المستهلكين، رسائل unacknowledged، أخطاء في اللوج) ثم: هل معدل الإنتاج زاد فعليًا؟",
                     "زد الذاكرة",
                     "احذف الرسائل",
                 ], "answer": 1,
                 "explain": "قائمة بتزيد = مستهلك ميت/بطيء أو إنتاج ارتفع. `messages_unacknowledged` عالي معناه مستهلك عالق في معالجة طويلة."},
                {"q": "ليه outbox مهم حتى مع وسيط موثوق؟",
                 "options": [
                     "للأداء",
                     "لأن المشكلة في **الذرّية بين القاعدة والوسيط**: الوسيط لا يحل dual write — الالتزام ثم النشر قد يفشل في المنتصف",
                     "مطلب MassTransit",
                     "لتقليل الرسائل",
                 ], "answer": 1,
                 "explain": "`AddEntityFrameworkOutbox` بيكتب الرسالة في معاملة البيانات نفسها، فالمُرسِل بيضمن النشر لاحقًا."},
                {"q": "رسالة 5MB فيها تفاصيل طلب كاملة. الحكم؟",
                 "options": [
                     "عادي",
                     "claim check: خزّن الحمولة في blob/object storage ومرّر المعرّف + الحقول الأساسية فقط في الرسالة",
                     "قسمها لـ10 رسائل",
                     "اضغطها بـgzip",
                 ], "answer": 1,
                 "explain": "الرسائل الكبيرة تضغط ذاكرة الوسيط وتبطئ الجميع. الرسالة المثالية: معرّفات + بيانات كافية للتوجيه (< 10KB)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "حدث حقيقي بين موديولين/خدمتين",
                 "md": "شغّل RabbitMQ في compose، وانشر حدثًا من خدمة (outbox عبر EF Core) واستهلكه في خدمة تانية بمستهلك idempotent. أضف retry باستثناءات متجاهلة، DLQ، وhealth check. اختبر الحالات الحرجة.",
                 "criteria": [
                     "مشروع `Contracts` مشترك للرسائل (records + `SchemaVersion` + minor units للمال)",
                     "النشر عبر outbox (اختبار: rollback يلغي الرسالة، وانهيار محاكى بعد الالتزام → الرسالة تُنشر لاحقًا)",
                     "مستهلك idempotent (اختبار نشر مكرر ×3 → أثر واحد)",
                     "`UseMessageRetry` مع `Ignore` لخطأين دائمين على الأقل + delayed redelivery",
                     "رسالة سامة تصل لقائمة الأخطاء (اختبار على حاوية حقيقية)",
                     "health check للوسيط في readiness + 4 مقاييس مراقبة موثقة (طول القائمة، unacked، معدل النشر/الاستهلاك)",
                     "README يشرح إزاي تشغّل كل حاجة بأمر واحد",
                 ],
                 "hint": "لو الاختبارات بتستنى كتير: استخدم `harness.Consumed.Any<T>(timeout)` بدل `Task.Delay` ثابت، وشغّل الوسيط مرة واحدة لكل fixture (IAsyncLifetime)."},
                {"id": "t2", "title": "request/response + مراقبة",
                 "md": "أضف مسار request/response (مثل حجز مخزون قبل تأكيد الطلب) بمهلة صريحة وردّين محتملين (نجاح/رفض)، واربط لوحة مراقبة محلية (Prometheus + Grafana) بمقاييس الوسيط والـbus.",
                 "criteria": [
                     "`CreateRequestClient<T>(timeout)` صريح + معالجة `RequestTimeoutException` → 503 (لا تخمين)",
                     "ردّان محتملان (`GetResponse<TSuccess, TFailure>`) مع معالجة الاثنين",
                     "idempotency key في الأمر (لا حجز مضاعف عند إعادة الطلب)",
                     "compose فيه Prometheus + Grafana مع dashboard محفوظ في الـrepo (JSON)",
                     "إنذاران موثقان: طول قائمة > حد لمدة دقيقتين، وارتفاع unacknowledged",
                     "اختبار: مهلة منتهية → استجابة 503 ورسالة سجل واضحة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "MassTransit documentation", "url": "https://masstransit.io/documentation"},
                {"label": "MassTransit — RabbitMQ configuration", "url": "https://masstransit.io/documentation/configuration/transports/rabbitmq"},
                {"label": "MassTransit — Entity Framework Outbox", "url": "https://masstransit.io/documentation/configuration/outbox"},
                {"label": "RabbitMQ documentation", "url": "https://www.rabbitmq.com/docs"},
                {"label": "RabbitMQ — Quorum queues", "url": "https://www.rabbitmq.com/docs/quorum-queues"},
                {"label": "AMQP 0-9-1 model explained", "url": "https://www.rabbitmq.com/tutorials/amqp-concepts"},
                {"label": "Testcontainers for .NET — RabbitMQ", "url": "https://testcontainers.com/modules/rabbitmq/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s5-m2-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
«نستخدم Kafka لأنه أسرع» — جملة بتبان كتير وبتكون غلط في أغلب الحالات، لأن **Kafka مش وسيط رسائل**،
ده **سجل أحداث موزّع** (distributed log). الفرق جوهري: في RabbitMQ/Service Bus الرسالة بتُستهلك وتُحذف،
في Kafka الرسالة بتفضل في الـlog والمستهلك بيتتبع موقعه (offset) — وده بيديك إعادة تشغيل (replay) وترتيب لكل partition.

الدرس ده بيعقد المقارنة صح: Kafka مقابل Azure Service Bus مقابل RabbitMQ،
بنماذج البيانات والضمانات والتكلفة التشغيلية — وبيعلّمك **تجريد الناشر** عشان تغيير الوسيط يبقى إعدادات مش إعادة كتابة.
"""},
            {"type": "terms", "items": [
                {"term": "Topic / Partition", "def": "في Kafka: الموضوع يُقسَّم لأقسام متوازية. **الترتيب مضمون داخل الـpartition فقط** — ومفتاح الرسالة يحدد القسم."},
                {"term": "Offset", "def": "موقع المستهلك في الـpartition. الالتزام به بعد المعالجة = أساس at-least-once."},
                {"term": "Consumer Group", "def": "مجموعة مستهلكين يتقاسمون الـpartitions (كل partition لمستهلك واحد داخل المجموعة). مجموعة مختلفة = قراءة مستقلة لكل البيانات."},
                {"term": "Rebalance", "def": "إعادة توزيع الـpartitions عند انضمام/خروج مستهلك — فترة توقف قصيرة، وأحد مصادر الألم."},
                {"term": "Retention / Compaction", "def": "حفظ الأحداث لمدة/حجم (retention) أو الاحتفاظ بآخر قيمة لكل مفتاح (log compaction)."},
                {"term": "Idempotent Producer", "def": "منع التكرار من الناشر نفسه (مع `acks=all`) — أساس exactly-once داخل Kafka."},
                {"term": "Schema Registry", "def": "مخزن مخططات (Avro/Protobuf/JSON Schema) مع قواعد توافق — يمنع كسر المستهلكين."},
                {"term": "Queue / Topic-Subscription (Service Bus)", "def": "طابور لمستقبل واحد، أو موضوع باشتراكات متعددة (كل اشتراك ينسخ الرسائل)."},
                {"term": "Peek-Lock مقابل Receive-Delete", "def": "في Service Bus: قفل الرسالة حتى التأكيد (آمن) مقابل حذفها فور الاستلام (بلا ضمان)."},
                {"term": "Sessions", "def": "ميزة Service Bus لترتيب صارم لكل مفتاح جلسة + معالجة حصرية — مفيدة لسلاسل عمليات."},
                {"term": "Claim Check", "def": "نمط: الحمولة الكبيرة في تخزين خارجي، والرسالة تحمل المرجع فقط."},
            ]},
            {"type": "heading", "level": 2, "text": "1) المقارنة الأساسية"},
            {"type": "table", "head": ["المعيار", "RabbitMQ", "**Kafka**", "Azure Service Bus"], "rows": [
                ["النموذج", "وسيط رسائل (queue/exchange)", "**سجل أحداث موزّع (log)**", "وسيط رسائل سحابي مُدار"],
                ["مصير الرسالة", "تُحذف بعد التأكيد", "**تبقى** حسب retention (تُعاد قراءتها)", "تُحذف بعد التأكيد (مع dead-letter)"],
                ["إعادة التشغيل (replay)", "✗", "**✓ أساس التصميم**", "✗ (إلا بنسخ احتياطي/تصدير)"],
                ["الترتيب", "داخل قائمة بمستهلك واحد", "**داخل partition (بحسب المفتاح)**", "داخل queue أو session"],
                ["نمط الاستهلاك", "push (من الوسيط)", "**pull (المستهلك يتحكم)**", "push/pull (processor)"],
                ["الإنتاجية", "عشرات الآلاف/ث", "**مئات الآلاف–ملايين/ث**", "عشرات الآلاف/ث (بحسب الطبقة)"],
                ["الزمن (latency)", "منخفض جدًا (ms)", "منخفض–متوسط (يعتمد batch)", "منخفض (ms–عشرات ms)"],
                ["التوجيه المرن", "**✓ exchanges/bindings قوية**", "△ (topic + header عبر كود)", "✓ (filters SQL92 على الاشتراكات)"],
                ["request/response", "✓ طبيعي", "✗ غير مناسب", "✓ (sessions/reply queue)"],
                ["معاملات", "△ (publisher confirms)", "**✓ معاملات Kafka (داخل Kafka)**", "✓ (ضمن كيان/جلسة)"],
                ["الرسائل المؤجلة/المجدولة", "△ (plugin/TTL+DLX)", "✗ (يدوي)", "**✓ مدمج** (ScheduledEnqueueTimeUtc)"],
                ["كشف التكرار", "✗ (يدوي)", "△ (idempotent producer)", "**✓ مدمج** (DuplicateDetection)"],
                ["DLQ", "✓ (DLX)", "△ (topic مخصص)", "✓ مدمج"],
                ["التشغيل الذاتي", "سهل نسبيًا", "**صعب** (partitions، KRaft/ZooKeeper، tuning)", "✗ مُدار (بلا عمليات)"],
                ["التكلفة", "منخفضة", "متوسطة–عالية (قرص/عقد)", "بحسب الرسائل/الطبقة"],
                ["أنسب حالة", "أوامر، مهام، توجيه مرن، request/response", "**event streaming، تدقيق، replay، تحليلات، CDC**", "أنظمة Azure، مهام مجدولة، جلسات، بلا فرق تشغيل"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قاعدة الاختيار في 3 أسئلة",
             "md": """
**① هل تحتاج إعادة تشغيل الأحداث (replay) أو بناء read models منها لاحقًا؟**
   → نعم: **Kafka** (أو EventStoreDB لو event sourcing). لأ: كمّل.

**② هل تحتاج توجيهًا مرنًا، أوامر مباشرة، request/response، أو رسائل مجدولة؟**
   → نعم: **RabbitMQ** (توجيه/مرونة) أو **Service Bus** (مجدولة/جلسات/مُدار).

**③ هل عندك فريق تشغيل يملك خبرة Kafka (أو ميزانية Confluent Cloud)؟**
   → لأ: **لا تستخدم Kafka**. وسيط رسائل أبسط هيخدمك أحسن بسنة صيانة أقل.

**الحالة الشائعة في الواقع:** RabbitMQ/Service Bus لرسائل التطبيق،
وKafka (أو CDC من Postgres لـwarehouse) لتحليلات وتدفقات البيانات. **الاتنين مش بديلين.**
"""},
            {"type": "heading", "level": 2, "text": "2) Kafka من .NET"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "تشغيل محلي + الحزم", "code": r'''
# Kafka بلا ZooKeeper (KRaft) للتطوير المحلي
docker run -d --name shop-kafka -p 9092:9092 \
  -e KAFKA_CFG_NODE_ID=1 -e KAFKA_CFG_PROCESS_ROLES=broker,controller \
  -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka:9093 \
  -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE=false \
  bitnami/kafka:3.9

docker run -d --name kafka-ui -p 8080:8080 \
  -e KAFKA_CLUSTERS_0_NAME=local -e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092 \
  provectuslabs/kafka-ui:latest

dotnet add src/Services/Orders package Confluent.Kafka
dotnet add src/Services/Orders package Confluent.SchemaRegistry.Serdes.Protobuf   # لو تستخدم schema registry
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/Kafka/KafkaPublisher.cs", "title": "ناشر: idempotent + acks=all + مفتاح للتقسيم", "code": r'''
using Confluent.Kafka;

public sealed class KafkaPublisher : IEventPublisher, IAsyncDisposable
{
    private readonly IProducer<string, string> _producer;
    private readonly ILogger<KafkaPublisher> _log;

    public KafkaPublisher(IConfiguration config, ILogger<KafkaPublisher> log)
    {
        _log = log;
        _producer = new ProducerBuilder<string, string>(new ProducerConfig
        {
            BootstrapServers = config["Kafka:BootstrapServers"],

            // ★ الموثوقية: كل النسخ تؤكد + منع تكرار من الناشر
            Acks = Acks.All,
            EnableIdempotence = true,                 // ✓ ترتيب + عدم تكرار داخل الناشر
            MaxInFlightRequestsPerConnection = 5,      // الحد المسموح مع idempotence

            // ✓ الإنتاجية: دفعات (مع زمن انتظار صغير)
            LingerMs = 20,
            BatchSize = 64 * 1024,
            CompressionType = CompressionType.Lz4,

            // ★ إعادة المحاولة للأخطاء العابرة فقط
            MessageSendMaxRetries = 3,
            RetryBackoffMs = 200,
            RequestTimeoutMs = 10_000,

            ClientId = $"orders-{Environment.MachineName}",
            EnableDeliveryReports = true,
        }).Build();
    }

    /// <summary>
    /// ★ المفتاح = معرّف الـaggregate: يضمن إن كل أحداث نفس الكيان تروح لنفس الـpartition
    /// وبالتالي **ترتيبها محفوظ**. بلا مفتاح → توزيع عشوائي → ترتيب مفقود.
    /// </summary>
    public async Task PublishAsync<TEvent>(string topic, string partitionKey, TEvent evt, CancellationToken ct)
        where TEvent : IIntegrationEvent
    {
        var message = new Message<string, string>
        {
            Key = partitionKey,                                     // ← يحدد الـpartition
            Value = JsonSerializer.Serialize(evt, AppJson.Options),
            Headers = new Headers
            {
                { "event-type",   System.Text.Encoding.UTF8.GetBytes(typeof(TEvent).Name) },
                { "schema-version", System.Text.Encoding.UTF8.GetBytes(evt.SchemaVersion.ToString()) },
                { "correlation-id", System.Text.Encoding.UTF8.GetBytes(evt.CorrelationId?.ToString() ?? string.Empty) },
                { "occurred-at",  System.Text.Encoding.UTF8.GetBytes(evt.OccurredAt.ToString("O")) },
            },
        };

        try
        {
            var result = await _producer.ProduceAsync(topic, message, ct);

            _log.LogDebug("published {Event} to {Topic}[{Partition}]@{Offset}",
                typeof(TEvent).Name, result.TopicPartition, result.Partition.Value, result.Offset.Value);

            KafkaMetrics.Published.Add(1, new("topic", topic));
        }
        catch (ProduceException<string, string> ex)
        {
            KafkaMetrics.Errors.Add(1, new("topic", topic), new("code", ex.Error.Code.ToString()));

            // ✗ لا تُعد المحاولة على أخطاء دائمة
            if (ex.Error.Code is ErrorCode.MsgSizeTooLarge or ErrorCode.TopicAuthorizationFailed
                                 or ErrorCode.InvalidRequiredAck)
            {
                _log.LogError(ex, "permanent kafka error for {Topic}", topic);
                throw;
            }

            throw;      // الأخطاء العابرة تُعالج في طبقة المرونة (درس 5.2.4) أو الـoutbox
        }
    }

    public ValueTask DisposeAsync()
    {
        _producer.Flush(TimeSpan.FromSeconds(5));      // ★ تأكيد إرسال كل ما في الـbuffer قبل الإغلاق
        _producer.Dispose();
        return ValueTask.CompletedTask;
    }
}

public static class KafkaMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Infrastructure.kafka", "1.0.0");
    public static readonly Counter<long> Published = Meter.CreateCounter<long>("kafka.published");
    public static readonly Counter<long> Errors = Meter.CreateCounter<long>("kafka.errors");
    public static readonly Counter<long> Consumed = Meter.CreateCounter<long>("kafka.consumed");
    public static readonly Histogram<double> Lag = Meter.CreateHistogram<double>("kafka.consumer.lag", unit: "messages");
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Reporting/Infrastructure/Kafka/OrderEventConsumer.cs", "title": "مستهلك: التزام offset **بعد** المعالجة + معالجة rebalance", "code": r'''
public sealed class OrderEventConsumer(
    IServiceScopeFactory scopes, IConfiguration config, ILogger<OrderEventConsumer> log) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var consumerConfig = new ConsumerConfig
        {
            BootstrapServers = config["Kafka:BootstrapServers"],
            GroupId = config["Kafka:GroupId"] ?? "reporting",   // ★ مجموعة مختلفة = قراءة مستقلة
            ClientId = $"reporting-{Environment.MachineName}",

            // ✓ ابدأ من البداية لمجموعة جديدة (لأحداث قديمة) أو من الأحدث
            AutoOffsetReset = AutoOffsetReset.Earliest,

            // ★ الأهم: لا التزام تلقائي — نلتزم بعد نجاح المعالجة (at-least-once)
            EnableAutoCommit = false,
            EnableAutoOffsetStore = false,

            SessionTimeoutMs = 30_000,
            MaxPollIntervalMs = 300_000,          // ✓ لو المعالجة بطيئة، ارفعها (وإلا rebalance متكرر)
            PartitionAssignmentStrategy = PartitionAssignmentStrategy.CooperativeSticky,  // ✓ rebalance أقل إزعاجًا
            FetchMinBytes = 1,
            FetchWaitMaxMs = 500,
        };

        using var consumer = new ConsumerBuilder<string, string>(consumerConfig)
            .SetPartitionsRevokedHandler((c, partitions) =>
            {
                // ★ عند سحب الـpartitions: التزم بما عولج (وإلا هيتكرر كتير)
                try { c.Commit(); } catch (KafkaException ex) { log.LogWarning(ex, "commit on revoke failed"); }
                log.LogInformation("partitions revoked: {Partitions}", string.Join(",", partitions.Select(p => p.Partition.Value)));
            })
            .SetErrorHandler((_, error) =>
            {
                if (error.IsFatal) log.LogError("fatal kafka error: {Reason}", error.Reason);
                else log.LogWarning("kafka error: {Reason}", error.Reason);
            })
            .Build();

        consumer.Subscribe(config["Kafka:Topics:Orders"] ?? "shop.orders.events");

        while (!stoppingToken.IsCancellationRequested)
        {
            ConsumeResult<string, string> result;
            try { result = consumer.Consume(TimeSpan.FromSeconds(1)); }
            catch (ConsumeException ex)
            {
                log.LogError(ex, "consume error ({Code})", ex.Error.Code);
                await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);
                continue;
            }

            if (result is null) continue;

            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var handler = scope.ServiceProvider.GetRequiredService<IOrderEventHandler>();
                await handler.HandleAsync(result.Message.Headers, result.Message.Value, stoppingToken);

                // ✓ الالتزام **بعد** النجاح فقط (وإلا فقد رسائل عند الانهيار)
                consumer.StoreOffset(result);
                consumer.Commit(result);
                KafkaMetrics.Consumed.Add(1);
            }
            catch (PoisonMessageException ex)
            {
                // ★ رسالة لن تُعالج أبدًا → انقلها لموضوع DLQ والتزم (لا توقف الـpartition)
                await PublishToDeadLetterAsync(result, ex, stoppingToken);
                consumer.StoreOffset(result);
                consumer.Commit(result);
                log.LogError(ex, "poison message sent to DLQ: {Key}@{Offset}", result.Message.Key, result.Offset);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                log.LogError(ex, "processing failed at {Offset}; will be redelivered", result.Offset);
                await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);   // backoff قبل إعادة القراءة
            }
        }

        consumer.Close();          // ✓ يغادر المجموعة بشكل نظيف (يسرّع الـrebalance)
    }

    private Task PublishToDeadLetterAsync(ConsumeResult<string, string> r, Exception ex, CancellationToken ct) =>
        Task.CompletedTask;        // نشر لموضوع shop.orders.events.dlq مع رؤوس الخطأ
}
'''},
            {"type": "heading", "level": 2, "text": "3) Azure Service Bus"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/ServiceBus/ServiceBusPublisherAndProcessor.cs", "title": "الناشر + المعالج بـpeek-lock", "code": r'''
using Azure.Messaging.ServiceBus;

// ═══ ① التسجيل: client واحد (singleton) + sender لكل موضوع ═══
public static class ServiceBusRegistration
{
    public static IServiceCollection AddServiceBusMessaging(this IServiceCollection services, IConfiguration config)
    {
        services.AddSingleton(_ => new ServiceBusClient(
            config["ServiceBus:ConnectionString"],
            new ServiceBusClientOptions
            {
                TransportType = ServiceBusTransportType.Amqp,           // ✓ AMQP (أفضل من HTTP)
                RetryOptions = new ServiceBusRetryOptions
                {
                    Mode = ServiceBusRetryMode.Exponential,
                    MaxRetries = 3,
                    Delay = TimeSpan.FromSeconds(1),
                    MaxDelay = TimeSpan.FromSeconds(15),
                    TryTimeout = TimeSpan.FromSeconds(20),
                },
            }));

        services.AddSingleton(sp => sp.GetRequiredService<ServiceBusClient>()
            .CreateSender("shop-orders"));                               // ✓ sender قابل لإعادة الاستخدام

        services.AddHostedService<OrderEventProcessor>();
        return services;
    }
}

// ═══ ② النشر: دفعات + رسائل مجدولة + كشف تكرار ═══
public sealed class ServiceBusPublisher(ServiceBusSender sender, ILogger<ServiceBusPublisher> log) : IEventPublisher
{
    public async Task PublishAsync<TEvent>(string topic, string partitionKey, TEvent evt, CancellationToken ct)
    {
        var message = new ServiceBusMessage(JsonSerializer.Serialize(evt, AppJson.Options))
        {
            ContentType = "application/json",
            Subject = typeof(TEvent).Name,                               // ← للفلترة في الاشتراكات
            MessageId = evt.MessageId,                                   // ★ لكشف التكرار (مدمج في Service Bus)
            CorrelationId = evt.CorrelationId?.ToString(),
            PartitionKey = partitionKey,                                 // ✓ ترتيب لكل مفتاح (Premium)
            TimeToLive = TimeSpan.FromHours(24),                         // ✓ لا رسائل للأبد
            ScheduledEnqueueTime = evt.DelayUntil,                       // ★ جدولة مدمجة (ميزة مقابل Kafka)
        };

        message.ApplicationProperties["schema-version"] = evt.SchemaVersion;

        await sender.SendMessageAsync(message, ct);
        log.LogDebug("sent {Type} to {Topic}", typeof(TEvent).Name, topic);
    }

    /// <summary>دفعات: أقل round-trips وأعلى إنتاجية (احترم حد الحجم ~256KB/Tier).</summary>
    public async Task PublishBatchAsync<TEvent>(string topic, IReadOnlyList<TEvent> events, CancellationToken ct)
        where TEvent : IIntegrationEvent
    {
        var batch = await sender.CreateMessageBatchAsync(ct);
        try
        {
            foreach (var evt in events)
            {
                var message = new ServiceBusMessage(JsonSerializer.Serialize(evt, AppJson.Options))
                {
                    Subject = typeof(TEvent).Name,
                    MessageId = evt.MessageId,
                    ContentType = "application/json",
                };

                if (!batch.TryAddMessage(message))            // ★ الدفعة امتلأت → أرسلها وابدأ جديدة
                {
                    await sender.SendMessagesAsync(batch, ct);
                    await batch.DisposeAsync();
                    batch = await sender.CreateMessageBatchAsync(ct);

                    if (!batch.TryAddMessage(message))        // رسالة أكبر من حد الدفعة
                        throw new InvalidOperationException($"الرسالة {evt.MessageId} أكبر من حد حجم الدفعة");
                }
            }
            await sender.SendMessagesAsync(batch, ct);
        }
        finally { await batch.DisposeAsync(); }
    }
}

// ═══ ③ المعالج: peek-lock + معالجة أخطاء + dead-letter ═══
public sealed class OrderEventProcessor(
    ServiceBusClient client, IServiceScopeFactory scopes, ILogger<OrderEventProcessor> log) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var options = new ServiceBusProcessorOptions
        {
            MaxConcurrentCalls = 8,                        // ✓ حد التوازي (bulkhead)
            MaxAutoLockRenewalDuration = TimeSpan.FromMinutes(5),   // ★ للمعالجة الطويلة
            PrefetchCount = 20,                            // ✓ يقلل round-trips
            ReceiveMode = ServiceBusReceiveMode.PeekLock,  // ★ لا ReceiveAndDelete للعمل الحرج
            AutoCompleteMessages = false,                  // ✓ نتحكم في التأكيد بأنفسنا
        };

        await using var processor = client.CreateProcessor("shop-orders", "reporting-subscription", options);

        processor.ProcessMessageAsync += async args =>
        {
            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var handler = scope.ServiceProvider.GetRequiredService<IOrderEventHandler>();
                await handler.HandleAsync(args.Message.Subject!, args.Message.Body.ToString(), args.CancellationToken);

                await args.CompleteMessageAsync(args.Message, args.CancellationToken);   // ✓ ack بعد النجاح
            }
            catch (PoisonMessageException ex)
            {
                log.LogError(ex, "dead-lettering {MessageId}", args.Message.MessageId);
                await args.DeadLetterMessageAsync(args.Message,
                    deadLetterReason: "PoisonMessage", deadLetterErrorDescription: ex.Message,
                    cancellationToken: args.CancellationToken);
            }
            catch (Exception ex)
            {
                log.LogError(ex, "abandoning {MessageId} for redelivery", args.Message.MessageId);
                await args.AbandonMessageAsync(args.Message, cancellationToken: args.CancellationToken);
                // ✓ Abandon = ترجع للقائمة فورًا؛ DeliveryCount بيزيد ولما يوصل MaxDeliveryCount → DLQ تلقائيًا
            }
        };

        processor.ProcessErrorAsync += args =>
        {
            log.LogError(args.Exception, "processor error: {Source}", args.ErrorSource);
            return Task.CompletedTask;
        };

        await processor.StartProcessingAsync(stoppingToken);
        stoppingToken.Register(async () => await processor.StopProcessingAsync());
        await Task.Delay(Timeout.Infinite, stoppingToken).ConfigureAwait(ConfigureAwaitOptions.SuppressThrowing);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "4) التجريد: غيّر الوسيط بلا إعادة كتابة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Contracts/Messaging/IEventPublisher.cs", "title": "منفذ محايد + اختيار التنفيذ بالإعدادات", "code": r'''
/// <summary>
/// ★ منفذ واحد في Application/Contracts — الكود ما يعرفش الوسيط.
/// تغيير الوسيط = تنفيذ جديد + سطر تسجيل (مش إعادة كتابة المستهلكين).
/// </summary>
public interface IEventPublisher
{
    Task PublishAsync<TEvent>(string topic, string partitionKey, TEvent evt, CancellationToken ct)
        where TEvent : IIntegrationEvent;
}

/// <summary>كل حدث يحمل ما تحتاجه أي وسيط: معرّف، إصدار، ارتباط، ووقت.</summary>
public interface IIntegrationEvent
{
    string MessageId { get; }
    int SchemaVersion { get; }
    Guid? CorrelationId { get; }
    DateTimeOffset OccurredAt { get; }
    DateTimeOffset? DelayUntil { get; }
}

// ── التسجيل بحسب الإعدادات (وحدات قابلة للتبديل) ──
public static class MessagingRegistration
{
    public static IServiceCollection AddMessaging(this IServiceCollection services, IConfiguration config)
    {
        var provider = config["Messaging:Provider"]?.ToLowerInvariant() ?? "inmemory";

        switch (provider)
        {
            case "rabbitmq":
                services.AddOrderMessaging(config);          // MassTransit + RabbitMQ (الدرس 5.2.1)
                break;

            case "kafka":
                services.AddSingleton<IEventPublisher, KafkaPublisher>();
                break;

            case "servicebus":
                services.AddServiceBusMessaging(config);
                break;

            case "outbox-only":                            // ✓ للتطوير المحلي: outbox بلا وسيط
                services.AddSingleton<IEventPublisher, NoopPublisher>();
                break;

            default:
                services.AddSingleton<IEventPublisher, InMemoryPublisher>();   // للاختبارات
                break;
        }

        services.AddHealthChecks().AddCheck<MessagingHealthCheck>("messaging");
        return services;
    }
}

/// <summary>ناشر للتطوير/الاختبار: يسجل ولا يرسل (يمنع «يعمل عندي» الزائف).</summary>
public sealed class InMemoryPublisher(ILogger<InMemoryPublisher> log) : IEventPublisher
{
    public readonly List<(string Topic, string Type, string Payload)> Published = [];
    public Task PublishAsync<TEvent>(string topic, string partitionKey, TEvent evt, CancellationToken ct)
    {
        Published.Add((topic, typeof(TEvent).Name, JsonSerializer.Serialize(evt)));
        log.LogDebug("in-memory publish {Type} → {Topic}", typeof(TEvent).Name, topic);
        return Task.CompletedTask;
    }
}
'''},
            {"type": "callout", "kind": "danger", "title": "فخاخ بتوقع فرق في الأنظمة الموزعة",
             "md": """
- **«Kafka بيضمن الترتيب»** → الترتيب **داخل partition واحد** فقط. بلا مفتاح صحيح، أحداث نفس الطلب ممكن تتوزع.
  واستهلاك بـconsumer group مع عدة مستهلكين = موازاة (الترتيب بين partitions غير مضمون).
- **«offset يُلتزم تلقائيًا»** → مع `EnableAutoCommit=true` بتفقد رسائل لو انهرت بين الالتزام والمعالجة.
  الالتزام **بعد** المعالجة (at-least-once) هو النمط الصحيح.
- **معالجة بطيئة مع `MaxPollIntervalMs` افتراضي** → المستهلك يُطرد من المجموعة ويعمل rebalance لا نهائي.
- **Rebalance متكرر** = توقف استهلاك. قلّل عدد الـpartitions غير الضروري، واستخدم `CooperativeSticky`،
  وارفع `MaxPollIntervalMs` وقلّل `MaxPollRecords`.
- **Auto-create topics في الإنتاج** → مواضيع بأسماء غلط تتعمل بصمت. عطّله (`auto.create.topics.enable=false`) وأنشئ المواضيع بـIaC.
- **Service Bus بـ`ReceiveAndDelete`** لعمل حرج → فقد عند الانهيار. استخدم `PeekLock`.
- **رسائل بلا TTL** → قوائم ومواضيع تمتلئ برسائل بلا قيمة.
- **اختيار Kafka لـrequest/response** → نمط خاطئ (استخدم RabbitMQ/Service Bus أو gRPC).
- **بلا Schema Registry** في Kafka → أول تغيير في شكل الرسالة يكسر المستهلكين بصمت.
- **نسيان حجم الرسالة الأقصى** (Kafka ~1MB افتراضيًا، Service Bus 256KB/1MB بحسب الطبقة) → `MsgSizeTooLarge`.
"""},
            {"type": "checkpoints", "items": [
                "أفرّق بين وسيط الرسائل وسجل الأحداث، وأختار الوسيط بثلاثة أسئلة (replay؟ توجيه/أوامر؟ خبرة تشغيلية؟).",
                "أضبط Kafka بمفتاح تقسيم صحيح، `acks=all` + idempotent producer، والتزام offset بعد المعالجة.",
                "أضبط Service Bus بـPeekLock وDLQ ومعالجة دفعات ورسائل مجدولة وكشف تكرار.",
                "أجرّد النشر خلف `IEventPublisher` بحيث تغيير الوسيط إعدادات لا إعادة كتابة، وأتعامل مع حدود حجم الرسالة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "الفرق الجوهري بين Kafka وRabbitMQ؟",
                 "options": [
                     "السرعة فقط",
                     "Kafka سجل أحداث (الرسائل تبقى وتُعاد قراءتها بـoffsets) — RabbitMQ وسيط رسائل (تُستهلك وتُحذف)",
                     "اللغة",
                     "الدعم السحابي",
                 ], "answer": 1,
                 "explain": "من الفرق ده بتيجي كل الفروق: replay وترتيب لكل partition وthroughput عالي في Kafka، مقابل توجيه مرن ورسائل مجدولة وrequest/response في وسيط الرسائل."},
                {"q": "ليه مفتاح الرسالة في Kafka مهم؟",
                 "options": [
                     "للأمان",
                     "يحدد الـpartition → يضمن ترتيب أحداث نفس الكيان؛ بلا مفتاح (أو بمفتاح عشوائي) الترتيب يُفقد",
                     "للضغط",
                     "للتشفير",
                 ], "answer": 1,
                 "explain": "استخدم معرّف الـaggregate (مثل OrderId) مفتاحًا، فتبقى كل أحداث الطلب في partition واحد وبترتيب."},
                {"q": "`EnableAutoCommit=true` مع معالجة قد تفشل — النتيجة؟",
                 "options": [
                     "لا أثر",
                     "فقد رسائل: الـoffset يُلتزم قبل/بغض النظر عن نجاح المعالجة، فالانهيار يتخطى رسائل غير معالَجة",
                     "تكرار فقط",
                     "rebalance",
                 ], "answer": 1,
                 "explain": "النمط الصحيح: `EnableAutoCommit=false` و`EnableAutoOffsetStore=false` + `Commit` بعد نجاح المعالجة (at-least-once)."},
                {"q": "أنهي وسيط لرسائل مجدولة (تشغيل بعد 3 ساعات) وكشف تكرار مدمج؟",
                 "options": [
                     "Kafka",
                     "Azure Service Bus (`ScheduledEnqueueTime` + `DuplicateDetection`)",
                     "Redis Pub/Sub",
                     "gRPC",
                 ], "answer": 1,
                 "explain": "في Kafka هتبني الجدولة بنفسك (موضوع تأخير + عامل)، وفي RabbitMQ تحتاج TTL+DLX أو plugin. Service Bus بيدعمها مدمجًا."},
                {"q": "فريق صغير بلا خبرة تشغيل Kafka ومحتاج أوامر وrequest/response. القرار؟",
                 "options": [
                     "Kafka (أقوى)",
                     "RabbitMQ أو Service Bus — Kafka هنا تكلفة تشغيلية بلا فائدة مقابلة",
                     "بلا وسيط",
                     "EventStoreDB",
                 ], "answer": 1,
                 "explain": "لو مش محتاج replay/streaming، وسيط الرسائل أبسط وأرخص تشغيليًا ويخدم الأنماط دي أحسن."},
                {"q": "رسالة أكبر من حد الوسيط. الحل؟",
                 "options": [
                     "ارفع الحد للأبد",
                     "claim check: خزّن الحمولة في blob/object storage ومرّر المرجع + الحقول الأساسية في الرسالة",
                     "اقسمها عشوائيًا",
                     "احذف الحقول",
                 ], "answer": 1,
                 "explain": "رفع الحد بيضغط ذاكرة الوسيط ويقلل الإنتاجية. الرسالة المثالية صغيرة (< 10KB) وتحمل ما يكفي للتوجيه."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تجريد ناشر + وسيطان",
                 "md": "عرّف `IEventPublisher` في مشروع العقود، ونفّذه لوسيطَين (RabbitMQ عبر MassTransit + Kafka أو Service Bus)، مع اختيار بالإعدادات. انقل مسارًا موجودًا للتجريد وأثبت إن التبديل بلا تغيير في كود العمل.",
                 "criteria": [
                     "منفذ واحد في Contracts/Application (لا اعتماد على أنواع الوسيط في كود العمل)",
                     "تنفيذان حقيقيان + `InMemoryPublisher` للاختبارات + `NoopPublisher` للتطوير",
                     "اختبار يبدّل المزوّد بالإعدادات ويمر (نفس اختبارات المستهلك)",
                     "`IIntegrationEvent` يحمل MessageId/SchemaVersion/CorrelationId/OccurredAt",
                     "مفتاح تقسيم/توجيه موثق لكل نوع حدث (ولييه)",
                     "ADR يشرح الوسيط المختار ولماذا، وشروط الانتقال للآخر",
                 ]},
                {"id": "t2", "title": "مستهلك Kafka أو Service Bus بسلوك فشل صحيح",
                 "md": "ابنِ مستهلكًا لإحداثات الطلبات (تقارير/بحث) بالتزام/تأكيد **بعد** المعالجة، DLQ للرسائل السامة، وقياس lag. اختبر: فشل عابر (إعادة تسليم)، رسالة سامة (DLQ)، وانهيار أثناء المعالجة (لا فقد).",
                 "criteria": [
                     "التزام/ack بعد النجاح فقط (اختبار انهيار محاكى → الرسالة تُعاد ولا تُفقد)",
                     "رسالة سامة → DLQ/موضوع dead-letter مع سبب محفوظ، والـpartition/القائمة تستمر",
                     "إعادة تسليم مكررة → idempotent (اختبار)",
                     "مقياس lag (Kafka) أو طول القائمة (Service Bus) منشور + حد إنذار موثق",
                     "إعدادات موثقة: `MaxPollIntervalMs`/`MaxConcurrentCalls` و`PrefetchCount` وليه القيم دي",
                 ],
                 "hint": "لمحاكاة الانهيار: اقتل العملية بين المعالجة والالتزام في اختبار يدوي (أو استخدم flag يرمي استثناء بعد المعالجة وقبل الالتزام) وتحقق إن الرسالة رجعت."},
            ]},
            {"type": "resources", "items": [
                {"label": "Confluent Kafka .NET client", "url": "https://docs.confluent.io/kafka-clients/dotnet/current/overview.html"},
                {"label": "Apache Kafka documentation", "url": "https://kafka.apache.org/documentation/"},
                {"label": "Azure Service Bus documentation", "url": "https://learn.microsoft.com/azure/service-bus-messaging/"},
                {"label": "Azure.Messaging.ServiceBus", "url": "https://learn.microsoft.com/dotnet/api/overview/azure/messaging.servicebus-readme"},
                {"label": "Azure Architecture — Choose a messaging option", "url": "https://learn.microsoft.com/azure/architecture/guide/technology-choices/messaging-overview"},
                {"label": "RabbitMQ vs Kafka (concepts)", "url": "https://www.rabbitmq.com/docs/streams"},
                {"label": "Claim Check pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/claim-check"},
            ]},
        ],
    },
]
