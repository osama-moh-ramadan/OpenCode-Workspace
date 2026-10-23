"""Stage 4, Module 2 — DDD & CQRS (lessons 3-4 of 4): Outbox/Inbox & Event Sourcing."""

TODAY = "2026-10-22"

LESSONS_S4_D = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s4-m2-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
فيه مشكلة بتحصل في كل نظام بيكتب في قاعدة بيانات وبينشر رسالة — وغالبًا بتبان بعد شهر في الإنتاج:
**مشكلة الكتابة المزدوجة (dual write)**. مفيش طريقة تعمل «احفظ في القاعدة وانشر للوسيط» كعملية ذرّية واحدة،
لأنهم نظامين مختلفين. النتيجة: رسائل ضائعة (التزام ثم انهيار قبل النشر) أو رسائل شبحية (نشر ثم rollback).

الحل عملي وممل ومضمون: **Outbox** — اكتب الرسالة في جدول داخل نفس قاعدة البيانات ونفس المعاملة،
ومُرسِل مستقل يقرأ الجدول وينشر. التسليم يبقى **at-least-once**، وده بيفرض على المستهلك **Inbox/idempotency**.

الدرس ده: التصميم الكامل (جداول، مُرسِل، إعادة محاولة، DLQ)، ومقارنة بالحلول الجاهزة (MassTransit)،
والحقيقة عن «exactly-once».
"""},
            {"type": "terms", "items": [
                {"term": "Dual Write Problem", "def": "تعديل قاعدة البيانات ونشر رسالة لا يمكن أن يكونا ذرّيين → فقد أو تكرار عند الفشل في المنتصف."},
                {"term": "Outbox", "def": "جدول في نفس قاعدة البيانات تُكتب فيه الرسائل **داخل معاملة البيانات**. مُرسِل مستقل ينشرها لاحقًا."},
                {"term": "Inbox / Deduplication", "def": "جدول/منطق عند المستهلك يسجّل معرّفات الرسائل المعالَجة — يحمي من أثر إعادة التسليم."},
                {"term": "At-most-once", "def": "قد تُفقد الرسالة ولا تُكرر (نشر بلا تأكيد). نادرًا مقبول."},
                {"term": "At-least-once", "def": "لا تُفقد، لكن قد تُكرر. ★ النمط الواقعي لكل الأنظمة الموثوقة — ويتطلب idempotency."},
                {"term": "Exactly-once", "def": "**شبه مستحيل عبر نظامين**. الموجود فعلًا: تسليم مكرر + معالجة idempotent = «effectively once»."},
                {"term": "MessageId / CorrelationId", "def": "معرّف فريد للرسالة (لإلغاء التكرار) ومعرف يربط العملية عبر الخدمات (للتتبع)."},
                {"term": "DLQ (Dead Letter Queue)", "def": "مصير الرسائل اللي فشلت بعد كل المحاولات — مع تنبيه وأداة إعادة تشغيل."},
                {"term": "Polling مقابل CDC", "def": "استطلاع الجدول دوريًا (بسيط) مقابل قراءة سجل المعاملات مثل Debezium (أدق وأقل تأخير، وأعقد تشغيليًا)."},
                {"term": "Backoff", "def": "زيادة فترة إعادة المحاولة تدريجيًا (مثلاً 1s, 5s, 25s…) مع jitter لمنع التزامن."},
                {"term": "Visibility Timeout", "def": "مدة «يختفي» فيها العمل عن بقية النسخ أثناء معالجته (بديل `SKIP LOCKED`)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) السيناريوهان اللي بيكسروا النظام"},
            {"type": "code", "lang": "text", "title": "الفشل قبل/بعد النشر", "code": r'''
// ═══ النمط الساذج ═══
await db.SaveChangesAsync(ct);                    // ① الالتزام
await bus.PublishAsync(new OrderPlaced(order), ct); // ② النشر

// السيناريو أ: انهيار/انقطاع شبكة بين ① و ②
//   → الطلب محفوظ في القاعدة، **والشحن لم يُجدول أبدًا**.
//   → العميل دفع والطلب اختفى من النظام. (أصعب نوع bugs: بلا سجل وبلا أثر)

// ═══ النمط الساذج المعكوس ═══
await bus.PublishAsync(new OrderPlaced(order), ct); // ① النشر
await db.SaveChangesAsync(ct);                    // ② الالتزام (فشل!)

// السيناريو ب: النشر نجح ثم فشل الالتزام (قيد/تعارض/مهلة)
//   → **رسالة شبحية**: المستهلكين عالجوا طلبًا غير موجود.
//   → مخزون نقص، إشعار اتبعت، وفاتورة اتعملت — لطلب وهمي.

// ═══ الحل: Outbox (ذرّي بحكم كونه في نفس القاعدة) ═══
await using var tx = await db.Database.BeginTransactionAsync(ct);
db.Orders.Add(order);                              // البيانات
db.OutboxMessages.Add(OutboxMessage.Of(order));    // الرسالة **في نفس المعاملة**
await db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);                          // ★ إما الاثنين أو لا شيء
// ثم: مُرسِل مستقل يقرأ الجدول وينشر (at-least-once)
'''},
            {"type": "heading", "level": 2, "text": "2) الجداول والفهارس"},
            {"type": "code", "lang": "sql", "filename": "db/012_outbox_inbox.sql", "title": "outbox عند المنتج + inbox عند المستهلك", "code": r'''
-- ═══ OUTBOX (في قاعدة المنتج) ═══
CREATE TABLE IF NOT EXISTS messaging.outbox (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id    uuid         NOT NULL UNIQUE,          -- ★ لإلغاء التكرار عند المستهلك
    correlation_id uuid        NULL,                     -- تتبع العملية عبر الخدمات
    type          text         NOT NULL,                 -- "order.placed"
    payload       jsonb        NOT NULL,
    headers       jsonb        NOT NULL DEFAULT '{}',
    created_at    timestamptz  NOT NULL DEFAULT now(),
    available_at  timestamptz  NOT NULL DEFAULT now(),   -- ★ للـbackoff (لا تنشر قبل كده)
    attempts      int          NOT NULL DEFAULT 0,
    sent_at       timestamptz  NULL,
    last_error    text         NULL
);

-- فهرس المُرسِل: «أقدم الرسائل المتاحة غير المرسلة»
CREATE INDEX ix_outbox_pending ON messaging.outbox (available_at, id)
    WHERE sent_at IS NULL;                                -- ★ فهرس جزئي: صغير وسريع

-- فهرس التنظيف
CREATE INDEX ix_outbox_sent ON messaging.outbox (sent_at) WHERE sent_at IS NOT NULL;

-- ═══ INBOX (في قاعدة المستهلك) — سجل ما عولج ═══
CREATE TABLE IF NOT EXISTS messaging.inbox (
    message_id    uuid PRIMARY KEY,
    type          text NOT NULL,
    processed_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_inbox_processed ON messaging.inbox (processed_at);

-- ═══ DLQ: ما فشل بعد كل المحاولات ═══
CREATE TABLE IF NOT EXISTS messaging.dead_letter (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id   uuid NOT NULL,
    type         text NOT NULL,
    payload      jsonb NOT NULL,
    attempts     int NOT NULL,
    last_error   text NOT NULL,
    failed_at    timestamptz NOT NULL DEFAULT now(),
    resolved_at  timestamptz NULL                          -- ★ يُملأ عند إعادة التشغيل الناجحة
);
CREATE INDEX ix_dlq_open ON messaging.dead_letter (failed_at) WHERE resolved_at IS NULL;

-- ═══ المراقبة: عمر أقدم رسالة (أهم رقم تشغيلي) ═══
-- SELECT extract(epoch FROM now() - min(created_at)) AS outbox_lag_seconds
-- FROM messaging.outbox WHERE sent_at IS NULL;
'''},
            {"type": "heading", "level": 3, "text": "3) المُرسِل: آمن مع عدة نسخ"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/Messaging/OutboxDispatcher.cs", "title": "SKIP LOCKED + backoff + محاولات + DLQ", "code": r'''
public sealed class OutboxDispatcher(
    IServiceScopeFactory scopes, IMessageBus bus, ILogger<OutboxDispatcher> log, TimeProvider time)
    : BackgroundService
{
    private const int BatchSize = 50;
    private const int MaxAttempts = 8;
    private static readonly TimeSpan Idle = TimeSpan.FromMilliseconds(400);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        log.LogInformation("outbox dispatcher started");

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var processed = await RunBatchAsync(stoppingToken);
                if (processed == 0) await Task.Delay(Idle, stoppingToken);   // لا تدوير ساخن
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                log.LogError(ex, "outbox batch failed; backing off");
                OutboxMetrics.Errors.Add(1);
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
        }
    }

    private async Task<int> RunBatchAsync(CancellationToken ct)
    {
        await using var scope = scopes.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        await using var connection = await db.Database.OpenConnectionAsync(ct);

        // ① احجز دفعة **بلا تنافس بين النسخ**: FOR UPDATE SKIP LOCKED (درس 2.3.x)
        // ② UPDATE … RETURNING في عبارة واحدة = حجز + تحديث ذرّي
        const string Sql = """
            UPDATE messaging.outbox
            SET attempts = attempts + 1
            WHERE id IN (
                SELECT id FROM messaging.outbox
                WHERE sent_at IS NULL AND available_at <= now()
                ORDER BY available_at, id
                LIMIT @Batch
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, message_id, correlation_id, type, payload, headers, attempts;
            """;

        var batch = (await connection.QueryAsync<OutboxRow>(
            new CommandDefinition(Sql, new { Batch = BatchSize }, commandTimeout: 10, cancellationToken: ct))).ToList();

        if (batch.Count == 0) return 0;

        foreach (var row in batch)
        {
            try
            {
                await bus.PublishAsync(
                    new OutgoingMessage(row.MessageId, row.CorrelationId, row.Type, row.Payload, row.Headers), ct);

                // ★ مع Dapper، الـCancellationToken يمر عبر CommandDefinition
                await connection.ExecuteAsync(new CommandDefinition(
                    "UPDATE messaging.outbox SET sent_at = now(), last_error = NULL WHERE id = @Id",
                    new { row.Id }, cancellationToken: ct));

                OutboxMetrics.Published.Add(1, new("type", row.Type));
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                await HandleFailureAsync(connection, row, ex, ct);
            }
        }

        OutboxMetrics.Lag.Record(batch.Count, new("phase", "batch"));
        return batch.Count;
    }

    private async Task HandleFailureAsync(
        IDbConnection connection, OutboxRow row, Exception ex, CancellationToken ct)
    {
        OutboxMetrics.Errors.Add(1, new("type", row.Type));

        if (row.Attempts >= MaxAttempts)
        {
            // ★ بعد كل المحاولات: DLQ + تنبيه (لا دوران لانهائي)
            const string dlqSql = """
                INSERT INTO messaging.dead_letter (message_id, type, payload, attempts, last_error)
                VALUES (@MessageId, @Type, @Payload::jsonb, @Attempts, @Error)
                ON CONFLICT DO NOTHING;
                UPDATE messaging.outbox SET sent_at = now(), last_error = @Error WHERE id = @Id;
                """;
            await connection.ExecuteAsync(new CommandDefinition(dlqSql,
                new { row.MessageId, row.Type, row.Payload, row.Attempts, Error = Truncate(ex.Message), row.Id },
                cancellationToken: ct));

            log.LogError(ex, "message {MessageId} ({Type}) moved to DLQ after {Attempts} attempts",
                row.MessageId, row.Type, row.Attempts);
            return;
        }

        // ✓ backoff أُسّي + jitter: 1s, 2s, 4s… (ويمنع تزامن كل النسخ)
        var delay = TimeSpan.FromSeconds(Math.Pow(2, row.Attempts - 1))
                    + TimeSpan.FromMilliseconds(Random.Shared.Next(0, 500));

        await connection.ExecuteAsync(new CommandDefinition(
            "UPDATE messaging.outbox SET available_at = now() + @Delay, last_error = @Error WHERE id = @Id",
            new { Delay = delay, Error = Truncate(ex.Message), row.Id }, cancellationToken: ct));

        log.LogWarning(ex, "publish failed for {MessageId}; retry {Attempt}/{Max} in {Delay}",
            row.MessageId, row.Attempts, MaxAttempts, delay);
    }

    private static string Truncate(string s) => s.Length <= 2000 ? s : s[..2000];
    private sealed record OutboxRow(long Id, Guid MessageId, Guid? CorrelationId, string Type,
                                    string Payload, string Headers, int Attempts);
}

public static class OutboxMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Infrastructure.outbox", "1.0.0");
    public static readonly Counter<long> Published = Meter.CreateCounter<long>("outbox.published");
    public static readonly Counter<long> Errors = Meter.CreateCounter<long>("outbox.errors");
    public static readonly Histogram<long> Lag = Meter.CreateHistogram<long>("outbox.batch.size", unit: "messages");
    public static readonly ObservableGauge<double> OldestAgeSeconds =
        Meter.CreateObservableGauge("outbox.oldest_age_seconds", () => 0d, unit: "s",
            description: "عمر أقدم رسالة غير مرسلة — أهم مؤشر صحة (يُحسب من القاعدة)");
}
'''},
            {"type": "callout", "kind": "warn", "title": "تفاصيل صغيرة بتحدد نجاح التصميم",
             "md": """
- **فهرس جزئي** `WHERE sent_at IS NULL` — وإلا المُرسِل بيمسح ملايين الصفوف المرسلة كل دورة.
- **التنظيف**: مهمة دورية تحذف/أرشف الرسائل المرسلة (مثلاً أقدم من 7 أيام) + `VACUUM`.
  من غيرها الجدول بيكبر والأداء بينهار (وده أشهر سبب لتدهور outbox في الإنتاج).
- **`FOR UPDATE SKIP LOCKED`** ضروري لو عندك أكتر من نسخة — وإلا هتنشر نفس الرسالة مرات.
- **لا تنشر داخل المعاملة**: النشر بعد الالتزام (زي ما هنا). لو نشرت جوه المعاملة،
  المعاملة هتطول على زمن الشبكة (أقفال أطول) ولو فشلت المعاملة بعد النشر → رسالة شبحية.
- **الترتيب**: outbox بيضمن ترتيب الإرسال داخل الجدول (بالـid). لو محتاج ترتيبًا صارمًا لكل stream،
  اجعل المُرسِل أحادي الخيط لكل مفتاح (partition by aggregate id) أو استخدم وسيطًا يدعم الترتيب.
- **راقب `oldest_age_seconds`** مش عدد الرسائل: رقم واحد يقولك «فيه حاجة واقفة».
"""},
            {"type": "heading", "level": 2, "text": "4) المستهلك: Inbox وidempotency"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Shipping/Messaging/InboxConsumer.cs", "title": "إلغاء تكرار + معالجة ذرّية مع تغيير البيانات", "code": r'''
public sealed class InboxConsumer(ShippingDbContext db, IMessageBus bus, ILogger<InboxConsumer> log)
{
    /// <summary>
    /// ★ القاعدتان معًا:
    ///   ① إلغاء التكرار في **نفس معاملة** تغيير البيانات (وإلا سقطت بين الخطوتين)
    ///   ② لو الرسالة سبق معالجتها → أكّد التسليم (ack) ولا تُعد التنفيذ
    /// </summary>
    public async Task HandleAsync(IncomingMessage message, CancellationToken ct)
    {
        await using var tx = await db.Database.BeginTransactionAsync(ct);

        // ① هل سبق معالجتها؟ (INSERT ذرّي: لو اتكرر المعرّف → المعاملة تفشل بصراع فريد)
        var inserted = await db.Database.ExecuteSqlInterpolatedAsync($"""
            INSERT INTO messaging.inbox (message_id, type) VALUES ({message.MessageId}, {message.Type})
            ON CONFLICT (message_id) DO NOTHING
            """, ct);

        if (inserted == 0)
        {
            log.LogInformation("duplicate {MessageId} ({Type}) — skipped", message.MessageId, message.Type);
            await tx.CommitAsync(ct);
            await bus.AcknowledgeAsync(message, ct);            // ✓ أكّد عشان ما تفضل تتكرر
            MessagingMetrics.Duplicates.Add(1, new("type", message.Type));
            return;
        }

        // ② نفّذ الأثر (idempotent بطبيعته كمان — دفاع مزدوج)
        switch (message.Type)
        {
            case "order.placed":
                var placed = message.Deserialize<OrderPlaced>();
                await ScheduleShipmentAsync(placed, ct);
                break;

            case "order.cancelled":
                await CancelShipmentAsync(message.Deserialize<OrderCancelled>(), ct);
                break;

            default:
                log.LogDebug("unknown type {Type} — ignored", message.Type);
                break;                                          // ✓ تجاهل صريح (لا فشل) للأنواع الجديدة
        }

        await db.SaveChangesAsync(ct);
        await tx.CommitAsync(ct);
        await bus.AcknowledgeAsync(message, ct);
    }

    /// <summary>idempotent حتى بلا inbox: لو الشحنة موجودة → لا تفعل شيئًا.</summary>
    private async Task ScheduleShipmentAsync(OrderPlaced e, CancellationToken ct)
    {
        if (await db.Shipments.AnyAsync(s => s.OrderId == e.OrderId, ct)) return;

        db.Shipments.Add(Shipment.Schedule(e.OrderId, e.ShippingAddress, e.Total));
        MessagingMetrics.Handled.Add(1, new("type", "order.placed"));
    }

    private async Task CancelShipmentAsync(OrderCancelled e, CancellationToken ct)
    {
        var shipment = await db.Shipments.FirstOrDefaultAsync(s => s.OrderId == e.OrderId, ct);
        if (shipment is null || shipment.Status == ShipmentStatus.Cancelled) return;   // ✓ idempotent
        shipment.Cancel(e.Reason);
    }
}

public static class MessagingMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Infrastructure.messaging", "1.0.0");
    public static readonly Counter<long> Handled = Meter.CreateCounter<long>("messages.handled");
    public static readonly Counter<long> Duplicates = Meter.CreateCounter<long>("messages.duplicates");
    public static readonly Counter<long> Failed = Meter.CreateCounter<long>("messages.failed");
}
'''},
            {"type": "table", "head": ["التنفيذ", "الجهد", "المزايا", "القيود", "إمتى"], "rows": [
                ["**يدوي** (زي أعلاه)", "متوسط (~300 سطر)", "تحكم كامل، بلا اعتماديات، سهل الفهم", "بتكتب الصيانة (تنظيف، DLQ، مراقبة) بنفسك", "لو عندك جدول outbox واحد ووسيط واحد"],
                ["**MassTransit Outbox**", "منخفض", "مدمج مع EF Core، retries/DLQ/مقاييس جاهزة، مدعوم", "يربطك بنموذج MassTransit (consumers/sagas)", "★ الخيار الأسرع قيمة لو بتستخدم MassTransit أصلًا"],
                ["**CDC (Debezium)**", "عالي", "بلا استطلاع (تأخير أقل)، بلا تحميل على القاعدة، يلتقط أي تغيير", "بنية تحتية إضافية (Kafka/Connect) وخبرة تشغيلية", "أنظمة كبيرة، تدفقات بيانات، عدد جداول كبير"],
                ["**وسيط بمعاملات (Kafka transactions)**", "عالي", "ذرّية عبر قواعد ووسائط محددة", "قيود قوية، وتعقيد تشغيلي", "نادرًا يستحق لتطبيق واحد"],
                ["**بلا outbox (نشر مباشر)**", "صفر", "بسيط", "✗ رسائل ضائعة/شبحية عند أي فشل", "نموذج أولي فقط، أو لو الفقد مقبول صراحة"],
            ]},
            {"type": "callout", "kind": "note", "title": "الحقيقة عن «exactly-once»",
             "md": """
مفيش تسليم exactly-once عبر نظامين مستقلين (دي نتيجة نظرية مش قصور أدوات):
أي تأكيد تسليم ممكن يُفقد، فيُعاد الإرسال.

اللي موجود عمليًا: **at-least-once delivery + idempotent processing = effectively-once effect**.

**3 طرق لعمل المعالجة idempotent:**
1. **Inbox** (جدول معرّفات) — الأشمل، ويحتاج تنظيفًا دوريًا (احتفظ بفترة ≥ أقصى مدة إعادة تسليم).
2. **Idempotency طبيعية** — العملية نفسها لا تتأثر بالتكرار (`UPDATE … SET status='cancelled' WHERE id=@id`).
   ★ الأفضل لو ممكن: بلا جداول إضافية وبلا تنظيف.
3. **مفتاح عمل فريد** — قيد فريد على (`OrderId`, `Type`) في جدول الأثر؛ التكرار يفشل بصراع ويُبتلع.

استخدم 2 أو 3 لما ينطبقوا، و1 لما الأثر معقد (نداء خارجي، حساب مبلغ، إنشاء كيان).
"""},
            {"type": "code", "lang": "csharp", "title": "اختبارات الموثوقية (اللي بتثبت التصميم فعلًا)", "code": r'''
public class OutboxReliabilityTests(PostgresFixture db) : IClassFixture<PostgresFixture>
{
    [Fact]
    public async Task Message_is_written_atomically_with_data()
    {
        await using var ctx = db.CreateContext();
        var order = TestData.NewOrder();

        await ctx.Database.CreateExecutionStrategy().ExecuteAsync(async () =>
        {
            await using var tx = await ctx.Database.BeginTransactionAsync();
            ctx.Orders.Add(order);
            ctx.Outbox.Add(OutboxMessage.Of("order.placed", order));
            await ctx.SaveChangesAsync();
            await tx.CommitAsync();
        });

        var messages = await ctx.Outbox.Where(m => m.Type == "order.placed").ToListAsync();
        messages.Should().ContainSingle();
        messages[0].SentAt.Should().BeNull("المُرسِل لسه ما اشتغلش");
    }

    [Fact]
    public async Task Rollback_removes_both_data_and_message()
    {
        await using var ctx = db.CreateContext();
        try
        {
            await using var tx = await ctx.Database.BeginTransactionAsync();
            ctx.Orders.Add(TestData.NewOrder());
            ctx.Outbox.Add(OutboxMessage.Of("order.placed", TestData.NewOrder()));
            await ctx.SaveChangesAsync();
            throw new InvalidOperationException("فشل مفتعل بعد الحفظ");
        }
        catch (InvalidOperationException) { /* متوقع */ }

        (await ctx.Outbox.CountAsync()).Should().Be(0, "لا رسالة شبحية بعد rollback");
    }

    [Fact]
    public async Task Dispatcher_does_not_deliver_same_message_to_two_workers()
    {
        await db.SeedOutboxAsync(count: 20);

        // ★ نسختان تعملان بالتوازي — نفس السيناريو في الإنتاج
        var (a, b) = (new List<Guid>(), new List<Guid>());
        await Task.WhenAll(
            CollectAsync(a), CollectAsync(b));

        a.Concat(b).Should().HaveCount(20, "كل رسالة تُحجز مرة واحدة فقط");
        a.Intersect(b).Should().BeEmpty("لا تكرار بين النسختين (SKIP LOCKED)");
    }

    [Fact]
    public async Task Failed_message_is_retried_with_backoff_then_goes_to_dlq()
    {
        await db.SeedOutboxAsync(count: 1);
        var bus = new FailingBus();                       // يفشل دائمًا

        for (var i = 0; i < 9; i++) await new OutboxDispatcher(db.Scopes, bus, NullLogger, db.Time)
            .RunSingleBatchForTestAsync();                // نقطة اختبار داخلية

        var dlq = await db.GetDeadLettersAsync();
        dlq.Should().ContainSingle();
        dlq[0].Attempts.Should().BeGreaterThanOrEqualTo(8);
        bus.PublishCount.Should().BeGreaterThan(1, "أُعيدت المحاولة فعلًا");
    }

    [Fact]
    public async Task Duplicate_delivery_is_processed_once()
    {
        await using var ctx = db.CreateContext();
        var message = IncomingMessage.Of("order.placed", TestData.OrderPlacedPayload());
        var consumer = new InboxConsumer(ctx, new RecordingBus(), NullLogger);

        await consumer.HandleAsync(message, CancellationToken.None);
        await consumer.HandleAsync(message, CancellationToken.None);      // ★ إعادة تسليم
        await consumer.HandleAsync(message, CancellationToken.None);

        (await ctx.Shipments.CountAsync()).Should().Be(1, "الشحن جُدول مرة واحدة رغم 3 تسليمات");
    }

    private Task CollectAsync(List<Guid> sink) => Task.CompletedTask;    // يجمع ما حجزه عامل واحد
}
'''},
            {"type": "checkpoints", "items": [
                "أفهم مشكلة الكتابة المزدوجة وأكتب الرسائل في outbox داخل نفس معاملة البيانات.",
                "أبني مُرسِلًا آمنًا مع عدة نسخ (`SKIP LOCKED`) بـbackoff وحد محاولات وDLQ وتنظيف دوري.",
                "أجعل المستهلك idempotent (inbox أو منطق طبيعي أو قيد فريد) مع ack بعد الالتزام.",
                "أختبر الموثوقية: ذرّية، rollback، تكرار تسليم، فشل ونسخة احتياطية، وقياس عمر أقدم رسالة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "انهيار بعد `SaveChanges` وقبل `Publish` — النتيجة بلا outbox؟",
                 "options": [
                     "لا شيء",
                     "البيانات محفوظة والرسالة ضائعة للأبد → آثار جانبية لم تحدث (شحن/إشعار) وبلا أثر في السجل",
                     "تُعاد الرسالة تلقائيًا",
                     "البيانات تُرجع",
                 ], "answer": 1,
                 "explain": "أصعب نوع أعطال: صامت. Outbox يخلي الرسالة جزءًا من المعاملة، فالمُرسِل هيلاقيها بعد إعادة التشغيل."},
                {"q": "ليه النشر لازم يكون **بعد** الالتزام مش جوه المعاملة؟",
                 "options": [
                     "أسرع",
                     "النشر جوه المعاملة يطيل الأقفال على زمن الشبكة، ولو فشل الالتزام بعد النشر تنتج رسالة شبحية",
                     "الوسيط لا يدعم المعاملات",
                     "ممنوع تقنيًا",
                 ], "answer": 1,
                 "explain": "القاعدة: غيّر البيانات + اكتب الرسالة ذرّيًا، ثم انشر. لو النشر فشل، الرسالة لسه في الجدول وهتُعاد."},
                {"q": "at-least-once معناه…",
                 "options": [
                     "لا تكرار",
                     "لا فقد، لكن التكرار متوقع → المستهلك لازم يكون idempotent",
                     "ترتيب مضمون",
                     "تسليم فوري",
                 ], "answer": 1,
                 "explain": "ده العقد الواقعي لكل الأنظمة الموثوقة (RabbitMQ/Kafka/Service Bus). صمّم على إن التكرار هيحصل."},
                {"q": "جدول outbox فيه 40 مليون صف (كلها مرسلة) والمُرسِل بقى بطيء. السبب؟",
                 "options": [
                     "Postgres بطيء",
                     "مفيش تنظيف + الفهرس مش جزئيًا → كل دورة تمسح/تفهرس صفوفًا ميتة؛ الحل: فهرس `WHERE sent_at IS NULL` + أرشفة/حذف دوري",
                     "الحجم الطبيعي للوسيط",
                     "لازم Redis",
                 ], "answer": 1,
                 "explain": "outbox من غير تنظيف بيتدهور ببطء لحد ما يبقى أزمة. أضف مهمة دورية (حذف/أرشفة أقدم من N أيام) من اليوم الأول."},
                {"q": "inbox consumer: الرسالة اتعالجت قبل كده. التصرف؟",
                 "options": [
                     "نفّذها تاني (idempotent على أي حال)",
                     "اعترف بالتسليم (ack) وتخطَّ التنفيذ، وسجّل مقياس duplicates — وإلا الرسالة هتفضل ترجع",
                     "ارمي استثناء",
                     "احذفها من الوسيط يدويًا",
                 ], "answer": 1,
                 "explain": "لو ما عملتش ack، الوسيط هيعيد تسليمها للأبد. التخطي + الاعتراف هو المسار الصحيح، مع مقياس يوريك حجم التكرار."},
                {"q": "نظام فيه outbox + inbox — ده exactly-once؟",
                 "options": [
                     "نعم",
                     "لا: التسليم at-least-once (قد يتكرر) لكن **الأثر** مرة واحدة — «effectively once»",
                     "at-most-once",
                     "بلا ضمان",
                 ], "answer": 1,
                 "explain": "الفرق مهم في المقابلات: exactly-once delivery شبه مستحيل عبر نظامين؛ exactly-once processing (effect) ممكن."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "outbox كامل بموثوقية مثبتة",
                 "md": "طبّق outbox في مشروعك: جدول بفهرس جزئي، كتابة في معاملة البيانات، مُرسِل بـ`SKIP LOCKED` وbackoff وDLQ، تنظيف دوري، و3 مقاييس (published/errors/oldest_age). أثبت السلوك باختبارات.",
                 "criteria": [
                     "اختبار: البيانات والرسالة يُحفظان معًا أو لا يُحفظان (rollback)",
                     "اختبار: عاملان متوازيان لا يسلمان نفس الرسالة مرتين",
                     "اختبار: فشل متكرر → DLQ بعد حد المحاولات مع رسالة خطأ محفوظة",
                     "مهمة تنظيف (حذف/أرشفة المرسلة أقدم من N أيام) + `VACUUM`/تحليل",
                     "مقياس `oldest_age_seconds` + تنبيه لو تجاوز حدًا (مثلًا 30s)",
                     "لا نشر داخل المعاملة (مراجعة كود)",
                 ],
                 "hint": "لو المُرسِل بياخد رسائل قديمة بالغلط: تأكد إن `available_at` بيُحدَّث في الـbackoff، وإن الفهرس على `(available_at, id) WHERE sent_at IS NULL`."},
                {"id": "t2", "title": "مستهلك idempotent بحالة فشل واقعية",
                 "md": "ابنِ مستهلكًا لحدث من موديول/خدمة تانية مع inbox (أو idempotency طبيعية)، واختبر: إعادة تسليم 3 مرات، تسليم قديم بعد تسليم أحدث (ترتيب معكوس)، ورسالة بنوع غير معروف.",
                 "criteria": [
                     "إعادة التسليم 3 مرات → أثر واحد (اختبار يثبت عدد الصفوف)",
                     "ack بعد الالتزام (لا ack قبل نجاح المعالجة)",
                     "ترتيب معكوس لا يُفسد الحالة (إصدار/تاريخ في الحدث + شرط في UPDATE)",
                     "نوع غير معروف → تجاهل + سجل debug (لا فشل ولا DLQ)",
                     "قرار مكتوب: inbox ولا idempotency طبيعية ولا قيد فريد — وليه",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Outbox pattern — microservices.io", "url": "https://microservices.io/patterns/data/transactional-outbox.html"},
                {"label": "Idempotent receiver", "url": "https://microservices.io/patterns/communication-style/idempotent-receiver.html"},
                {"label": "MassTransit — Outbox", "url": "https://masstransit.io/documentation/configuration/outbox"},
                {"label": "Debezium — Outbox event router", "url": "https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html"},
                {"label": "PostgreSQL — SELECT FOR UPDATE SKIP LOCKED", "url": "https://www.postgresql.org/docs/current/sql-select.html"},
                {"label": "Azure Architecture — Scheduler Agent Supervisor", "url": "https://learn.microsoft.com/azure/architecture/patterns/scheduler-agent-supervisor"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s4-m2-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
Event Sourcing بيقلب نموذج التخزين: بدل ما تخزّن **الحالة الحالية** (صف فيه `status='shipped'`)،
بتخزّن **تسلسل الأحداث** اللي وصلتها (`OrderPlaced`, `PaymentCaptured`, `OrderShipped`) —
والحالة بتتحسب بتطبيق الأحداث بالترتيب (fold).

ده بيديك تدقيق كامل، time travel، وإعادة بناء أي projection من الصفر. وبيكلفك:
اتساق eventual في كل حتة، إصدارات أحداث للأبد، snapshots، وصعوبة في الاستعلامات،
وتعارض مع متطلبات حذف البيانات الشخصية.

الهدف هنا مش إقناعك تستخدمه — الهدف إنك **تفهمه كفاية عشان تقرر بوعي**،
وتعرف إن أغلب الفرق محتاجة **audit log + domain events + outbox** (الدرس السابق) مش event sourcing كامل.
"""},
            {"type": "terms", "items": [
                {"term": "Event Store", "def": "مخزن append-only للأحداث: لا تعديل ولا حذف، فقط إضافة."},
                {"term": "Stream", "def": "تسلسل أحداث لكيان واحد (عادةً aggregate) بمعرّف stream وترتيب (version)."},
                {"term": "Version / Optimistic Concurrency", "def": "رقم إصدار الـstream. الإضافة تتوقع إصدارًا محددًا → لو اتغير، تعارض (بديل `RowVersion`)."},
                {"term": "Fold / Replay", "def": "تطبيق الأحداث بالترتيب لبناء الحالة. نفس الأحداث = نفس الحالة (شرط: الأحداث حتمية)."},
                {"term": "Snapshot", "def": "لقطة حالة عند إصدار معين — لتقليل زمن التحميل للـstreams الطويلة."},
                {"term": "Projection", "def": "read model مبني من الأحداث (جدول/view/فهرس بحث) — قابل لإعادة البناء دائمًا."},
                {"term": "Upcasting", "def": "تحويل حدث قديم (v1) لصيغته الحالية (v2) وقت القراءة — الحل الوحيد لعدم كسر الـstreams القديمة."},
                {"term": "Event Versioning", "def": "إصدار نوع الحدث نفسه (`OrderPlaced@2`) مع قواعد تحويل موثقة."},
                {"term": "Time Travel", "def": "حساب الحالة عند لحظة ماضية بتطبيق الأحداث حتى تاريخ معين."},
                {"term": "Immutable Log vs GDPR", "def": "السجل غير قابل للحذف يتعارض مع «حق المسح» → الحل: تشفير البيانات الشخصية + حذف المفتاح (crypto-shredding)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) المقارنة الصريحة (قبل أي كود)"},
            {"type": "table", "head": ["المعيار", "CRUD + Domain Events (outbox)", "**Audit Log** (جدول سجل)", "**Event Sourcing**"], "rows": [
                ["مصدر الحقيقة", "جدول الحالة", "جدول الحالة + سجل للقراءة", "**الأحداث** (الحالة محسوبة)"],
                ["تدقيق كامل للتغييرات", "جزئي (بحسب الأحداث)", "✓ كامل", "✓ كامل + قابل لإعادة التشغيل"],
                ["«ليه وصلنا لكده؟»", "صعب", "سهل (سجل)", "✓ سهل جدًا (fold)"],
                ["الحالة عند تاريخ ماضي", "✗", "△ (يحتاج إعادة بناء يدوي)", "✓ time travel أصيل"],
                ["إعادة بناء read models", "✗", "△", "✓ replay كامل"],
                ["استعلام الحالة الحالية", "✓ مباشر وسهل", "✓ مباشر", "✗ يحتاج projection لكل استعلام"],
                ["الاتساق", "قوي (ACID)", "قوي", "eventual في كل القراءات المشتقة"],
                ["إصدارات المخطط", "migrations عادية", "بسيطة", "**معقدة للأبد** (upcasting)"],
                ["حذف بيانات شخصية", "✓ سهل", "△ (السجل كمان)", "✗ يحتاج crypto-shredding"],
                ["تعقيد الفريق", "منخفض", "منخفض", "**عالي** (منحنى تعلم حاد)"],
                ["تكلفة التخزين", "منخفضة", "متوسطة", "تنمو بلا حدود (أحداث + snapshots)"],
                ["مناسب لـ", "★ أغلب الأنظمة", "★ أغلب الأنظمة اللي تحتاج تدقيق", "مالي/حجوزات/أنظمة بتدقيق صارم"],
            ]},
            {"type": "callout", "kind": "goal", "title": "القرار الواقعي لأغلب الفرق",
             "md": """
**احتياجاتك غالبًا:** «عايز أعرف مين غيّر إيه وإمتى وليه» + «عايز أنظمة تانية تعرف بالتغييرات».

ده بيتحقق بـ**CRUD + Domain Events (outbox) + جدول audit** — بلا event sourcing:
- جدول `audit_log (entity, entity_id, action, actor, changes jsonb, at)` يُكتب في نفس المعاملة.
- أحداث outbox للموديولات/الخدمات الأخرى.
- الحالة الحالية في جداول عادية → استعلامات بسيطة وأداء معروف.

**استخدم Event Sourcing فقط لو 2+ من دول صحيحين:**
1. التدقيق الكامل **متطلب تنظيمي** وكل حالة قابلة لإعادة البناء منه.
2. الحالة نفسها سلسلة انتقالات معقدة (حجوزات، مطالبات تأمين، ledger) والاستعلامات التاريخية جزء من المنتج.
3. محتاج تعيد بناء read models من الصفر بشكل متكرر (تغيير نموذج العمل).
4. الفريق عنده خبرة سابقة بيه وميزانية صيانة للأحداث المُصدَّرة.

ولو احتجته: **طبّقه على bounded context واحد** (مثل `Billing`) مش على النظام كله.
"""},
            {"type": "heading", "level": 2, "text": "2) تنفيذ على Postgres (بلا اعتماد خارجي)"},
            {"type": "code", "lang": "sql", "filename": "db/020_event_store.sql", "title": "جداول events وsnapshots وcheckpoints", "code": r'''
CREATE SCHEMA IF NOT EXISTS events;

CREATE TABLE events.streams (
    stream_id    uuid PRIMARY KEY,
    stream_type  text NOT NULL,
    version      bigint NOT NULL DEFAULT 0,              -- ★ آخر إصدار (للتنافس الأمثل)
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE events.events (
    stream_id    uuid NOT NULL REFERENCES events.streams(stream_id) ON DELETE CASCADE,
    version      bigint NOT NULL,
    type         text NOT NULL,
    schema_ver   int  NOT NULL DEFAULT 1,                -- ★ إصدار نوع الحدث (للـupcasting)
    payload      jsonb NOT NULL,
    metadata     jsonb NOT NULL DEFAULT '{}',            -- actor, correlation_id, causation_id
    occurred_at  timestamptz NOT NULL DEFAULT now(),
    global_pos   bigint GENERATED ALWAYS AS IDENTITY,    -- ★ ترتيب عالمي للـprojections
    PRIMARY KEY (stream_id, version)                     -- ★ يمنع تكرار إصدار في نفس الـstream
);

CREATE INDEX ix_events_global ON events.events (global_pos);
CREATE INDEX ix_events_type_time ON events.events (type, occurred_at DESC);
CREATE INDEX ix_events_payload_gin ON events.events USING GIN (payload jsonb_path_ops);   -- استعلامات ad-hoc

CREATE TABLE events.snapshots (
    stream_id    uuid NOT NULL REFERENCES events.streams(stream_id) ON DELETE CASCADE,
    version      bigint NOT NULL,
    state        jsonb NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (stream_id, version)
);

CREATE TABLE events.projection_checkpoints (
    projection   text PRIMARY KEY,
    global_pos   bigint NOT NULL,
    updated_at   timestamptz NOT NULL DEFAULT now()
);

-- أمثلة استعلامات مفيدة:
-- كل أحداث stream:      SELECT * FROM events.events WHERE stream_id = @id ORDER BY version;
-- التدقيق لمستخدم:      SELECT * FROM events.events WHERE metadata->>'actor_id' = @actor ORDER BY global_pos;
-- الحالة عند تاريخ:    SELECT * FROM events.events WHERE stream_id = @id AND occurred_at <= @at ORDER BY version;
-- streams نشطة اليوم:  SELECT DISTINCT stream_id FROM events.events WHERE occurred_at >= now() - interval '1 day';
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/EventStore/PostgresEventStore.cs", "title": "إضافة بتنافس أمثل + تحميل بـsnapshot + fold", "code": r'''
public interface IEventSerializer
{
    /// <summary>يرجع (نوع الحدث، إصدار المخطط، payload JSON).</summary>
    (string Type, int SchemaVersion, string Payload) Serialize(IDomainEvent domainEvent);
    IDomainEvent DeserializeAndUpcast(string type, int schemaVersion, string payload);
    string SerializeState<TState>(TState state);
    TState DeserializeState<TState>(string json);
}

public static class EventStoreMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Infrastructure.eventstore", "1.0.0");
    public static readonly Counter<long> Appended = Meter.CreateCounter<long>("eventstore.appended");
    public static readonly Histogram<long> LoadDuration =
        Meter.CreateHistogram<long>("eventstore.load.applied_events", unit: "events");
}

public interface IEventStore
{
    Task<long> AppendAsync(Guid streamId, string streamType, long expectedVersion,
                           IReadOnlyList<IDomainEvent> events, EventMetadata metadata, CancellationToken ct);
    Task<EventStream> LoadAsync<TState>(Guid streamId, CancellationToken ct)
        where TState : IEventSourcedState, new();
}

public sealed record EventMetadata(Guid? CorrelationId, Guid? CausationId, string? ActorId);
public sealed record StoredEvent(Guid StreamId, long Version, string Type, int SchemaVersion,
                                 string Payload, EventMetadata Metadata, DateTimeOffset OccurredAt, long GlobalPos);
public sealed record EventStream(Guid StreamId, long Version, object State);

public sealed class PostgresEventStore(AppDbContext db, IEventSerializer serializer, ILogger<PostgresEventStore> log)
    : IEventStore
{
    private const int SnapshotEvery = 50;

    /// <summary>إضافة ذرّية مع تنافس أمثل: لو الـstream اتقدم من حد تاني → استثناء تعارض.</summary>
    public async Task<long> AppendAsync(
        Guid streamId, string streamType, long expectedVersion,
        IReadOnlyList<IDomainEvent> events, EventMetadata metadata, CancellationToken ct)
    {
        if (events.Count == 0) return expectedVersion;
        var connection = db.Database.GetDbConnection();
        if (connection.State != ConnectionState.Open) await connection.OpenAsync(ct);   // ✓ (درس 3.1.3)

        await using var tx = await connection.BeginTransactionAsync(ct);

        // ① أنشئ الـstream لو جديد (بلا فشل لو موجود)
        const string ensureStreamSql = """
            INSERT INTO events.streams (stream_id, stream_type, version)
            VALUES (@StreamId, @StreamType, 0) ON CONFLICT (stream_id) DO NOTHING
            """;
        await connection.ExecuteAsync(new CommandDefinition(ensureStreamSql,
            new { StreamId = streamId, StreamType = streamType }, tx, cancellationToken: ct));

        // ② ★ التنافس الأمثل: UPDATE بشرط الإصدار المتوقع
        const string advanceSql = """
            UPDATE events.streams SET version = @NewVersion
            WHERE stream_id = @StreamId AND version = @ExpectedVersion
            """;
        var advanced = await connection.ExecuteAsync(new CommandDefinition(advanceSql,
            new { StreamId = streamId, NewVersion = expectedVersion + events.Count, ExpectedVersion = expectedVersion },
            tx, cancellationToken: ct));

        if (advanced == 0)
        {
            await tx.RollbackAsync(ct);
            var actual = await connection.ExecuteScalarAsync<long>(new CommandDefinition(
                "SELECT version FROM events.streams WHERE stream_id = @StreamId", new { StreamId = streamId },
                cancellationToken: ct));
            throw new EventStoreConcurrencyException(streamId, expectedVersion, actual);
        }

        // ③ أدخل الأحداث بإصدارات متتابعة (PK يمنع التكرار كمان)
        var version = expectedVersion;
        foreach (var domainEvent in events)
        {
            version++;
            var (type, schemaVersion, payload) = serializer.Serialize(domainEvent);
            const string insertEventSql = """
                INSERT INTO events.events (stream_id, version, type, schema_ver, payload, metadata, occurred_at)
                VALUES (@StreamId, @Version, @Type, @SchemaVer, @Payload::jsonb, @Metadata::jsonb, @OccurredAt)
                """;
            await connection.ExecuteAsync(new CommandDefinition(insertEventSql,
                new
                {
                    StreamId = streamId, Version = version, Type = type, SchemaVer = schemaVersion,
                    Payload = payload,
                    Metadata = JsonSerializer.Serialize(new { metadata.CorrelationId, metadata.CausationId, metadata.ActorId }),
                    OccurredAt = domainEvent.OccurredAt,
                }, tx, cancellationToken: ct));
        }

        await tx.CommitAsync(ct);
        EventStoreMetrics.Appended.Add(events.Count, new("type", streamType));
        return version;
    }

    /// <summary>تحميل: أحدث snapshot + الأحداث بعده، ثم fold + upcasting.</summary>
    public async Task<EventStream> LoadAsync<TState>(Guid streamId, CancellationToken ct)
        where TState : IEventSourcedState, new()
    {
        var connection = db.Database.GetDbConnection();

        var snapshot = await connection.QuerySingleOrDefaultAsync<SnapshotRow?>(new CommandDefinition(
            "SELECT version, state FROM events.snapshots WHERE stream_id = @StreamId ORDER BY version DESC LIMIT 1",
            new { StreamId = streamId }, cancellationToken: ct));

        var state = new TState();
        var fromVersion = 0L;
        if (snapshot is not null)
        {
            state = serializer.DeserializeState<TState>(snapshot.State);
            fromVersion = snapshot.Version;
        }

        const string loadSql = """
            SELECT version, type, schema_ver, payload, metadata, occurred_at
            FROM events.events WHERE stream_id = @StreamId AND version > @FromVersion ORDER BY version
            """;
        var rows = await connection.QueryAsync<EventRow>(new CommandDefinition(
            loadSql, new { StreamId = streamId, FromVersion = fromVersion }, cancellationToken: ct));

        var applied = 0;
        foreach (var row in rows)
        {
            var domainEvent = serializer.DeserializeAndUpcast(row.Type, row.SchemaVersion, row.Payload);  // ★ upcasting
            state = state.Apply(domainEvent);
            applied++;
        }

        var currentVersion = fromVersion + applied;

        // ✓ snapshot دوري — وإلا الـstreams الطويلة بتبطئ التحميل بشكل خطي
        if (applied >= SnapshotEvery)
        {
            const string snapshotSql = """
                INSERT INTO events.snapshots (stream_id, version, state) VALUES (@StreamId, @Version, @State::jsonb)
                ON CONFLICT (stream_id, version) DO NOTHING
                """;
            await connection.ExecuteAsync(new CommandDefinition(snapshotSql,
                new { StreamId = streamId, Version = currentVersion, State = serializer.SerializeState(state) },
                cancellationToken: ct));
        }

        EventStoreMetrics.LoadDuration.Record(applied, new("snapshot", snapshot is not null));
        return new EventStream(streamId, currentVersion, state);
    }

    private sealed record SnapshotRow(long Version, string State);
    private sealed record EventRow(long Version, string Type, int SchemaVersion, string Payload,
                                   string Metadata, DateTimeOffset OccurredAt);
}

public sealed class EventStoreConcurrencyException(Guid streamId, long expected, long actual)
    : Exception($"تعارض في الـstream {streamId}: توقعنا الإصدار {expected} والفعلية {actual}");

public interface IEventSourcedState
{
    /// <summary>تطبيق حدث واحد على الحالة (لا I/O، لا منطق غير حتمي — وإلا الـreplay يتغير).</summary>
    IEventSourcedState Apply(IDomainEvent domainEvent);
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Billing/Domain/InvoiceStream.cs", "title": "aggregate مُصدَّر بالحدث: Apply بدل setters", "code": r'''
namespace Shop.Billing.Domain;

/// <summary>
/// الحالة محسوبة من الأحداث: مفيش setter، ومفيش حفظ مباشر.
/// ★ كل `Apply` لازم يكون **حتميًا**: نفس الأحداث → نفس الحالة (بلا `DateTime.Now` ولا عشوائية).
/// </summary>
public sealed class InvoiceStream : IEventSourcedState
{
    public Guid Id { get; private init; }
    public Guid CustomerId { get; private init; }
    public InvoiceStatus Status { get; private set; } = InvoiceStatus.Draft;
    public Money Amount { get; private set; }
    public DateTimeOffset IssuedAt { get; private set; }
    public DateTimeOffset? PaidAt { get; private set; }
    public IReadOnlyList<InvoiceLine> Lines => _lines;
    /// <summary>★ يُحددها الـevent store عند التحميل — مش جزء من الـfold (وإلا بقى غير حتمي).</summary>
    public long Version { get; internal set; }
    private readonly List<InvoiceLine> _lines = [];

    IEventSourcedState IEventSourcedState.Apply(IDomainEvent e) { Apply(e); return this; }

    public void Apply(IDomainEvent e)
    {
        switch (e)
        {
            case InvoiceIssued issued:
                Id = issued.InvoiceId; CustomerId = issued.CustomerId; Amount = issued.Amount;
                IssuedAt = issued.OccurredAt; Status = InvoiceStatus.Issued;
                _lines.AddRange(issued.Lines);
                break;

            case InvoiceLineAdjusted adj:
                var line = _lines.Find(l => l.ProductId == adj.ProductId);
                if (line is not null) line.AdjustQuantity(adj.NewQuantity);
                Amount = adj.NewAmount;                 // ★ المبلغ الجديد من الحدث (مش محسوب الآن)
                break;

            case PaymentCaptured paid:
                if (Status == InvoiceStatus.Issued) { Status = InvoiceStatus.Paid; PaidAt = paid.OccurredAt; }
                break;                                  // ✓ idempotent: تكرار الحدث لا يكسر الحالة

            case InvoiceVoided voided:
                Status = InvoiceStatus.Voided;
                break;

            default:
                // ★ حدث جديد/غير معروف: تجاهله (لا تفشل) — عشان الـstreams القديمة تفضل تُقرأ
                break;
        }
    }

    // ── الأوامر: تتحقق ثم تُنتج أحداثًا (لا تعدّل الحالة مباشرة) ──
    public static (InvoiceStream State, IReadOnlyList<IDomainEvent> Events) Issue(
        Guid invoiceId, Guid customerId, Money amount, IReadOnlyList<InvoiceLine> lines, IClock clock)
    {
        if (amount.IsZero) throw new InvalidOperationException("لا يمكن إصدار فاتورة بمبلغ صفر");
        if (lines.Count == 0) throw new InvalidOperationException("الفاتورة تحتاج سطرًا واحدًا على الأقل");

        var evt = new InvoiceIssued(invoiceId, customerId, amount, lines, clock.UtcNow);
        var state = new InvoiceStream();
        state.Apply(evt);
        return (state, [evt]);
    }

    public IReadOnlyList<IDomainEvent> CapturePayment(Money amount, IClock clock)
    {
        if (Status != InvoiceStatus.Issued)
            throw new InvalidOperationException($"لا يمكن تحصيل فاتورة بحالة {Status}");
        if (amount != Amount)
            throw new InvalidOperationException($"المبلغ المحصّل {amount} لا يطابق المستحق {Amount}");

        return [new PaymentCaptured(Id, amount, clock.UtcNow)];
    }

    public IReadOnlyList<IDomainEvent> Void(string reason, IClock clock)
    {
        if (Status == InvoiceStatus.Paid)
            throw new InvalidOperationException("الفاتورة المدفوعة لا تُلغى — أصدر فاتورة دائنة (credit note)");

        return [new InvoiceVoided(Id, reason, clock.UtcNow)];
    }
}

public sealed record InvoiceIssued(Guid InvoiceId, Guid CustomerId, Money Amount,
    IReadOnlyList<InvoiceLine> Lines, DateTimeOffset OccurredAt) : IDomainEvent;
public sealed record InvoiceLineAdjusted(Guid InvoiceId, Guid ProductId, int NewQuantity,
    Money NewAmount, DateTimeOffset OccurredAt) : IDomainEvent;
public sealed record PaymentCaptured(Guid InvoiceId, Money Amount, DateTimeOffset OccurredAt) : IDomainEvent;
public sealed record InvoiceVoided(Guid InvoiceId, string Reason, DateTimeOffset OccurredAt) : IDomainEvent;

public sealed class InvoiceLine
{
    public Guid ProductId { get; init; }
    public string Name { get; init; } = string.Empty;
    public int Quantity { get; private set; }
    public Money UnitPrice { get; init; }
    public Money Subtotal => UnitPrice.Multiply(Quantity);
    public void AdjustQuantity(int q) { if (q < 0) throw new ArgumentOutOfRangeException(nameof(q)); Quantity = q; }
}

public enum InvoiceStatus { Draft, Issued, Paid, Voided }
'''},
            {"type": "heading", "level": 2, "text": "3) Upcasting: التكلفة اللي بتفضل معاك للأبد"},
            {"type": "code", "lang": "csharp", "title": "تحويل الأحداث القديمة للصيغة الحالية وقت القراءة", "code": r'''
/// <summary>
/// لما يتغير شكل الحدث، **ممنوع** تعديل الأحداث المخزنة (السجل غير قابل للتغيير).
/// الحل: upcaster يحوّل النسخة القديمة للجديدة وقت القراءة، ومُسجَّل لكل إصدار.
/// </summary>
public interface IEventUpcaster
{
    string Type { get; }
    int FromVersion { get; }
    JsonNode Upcast(JsonNode payload);
}

/// <summary>مثال حقيقي: `InvoiceIssued@1` كان فيه `total` بدل `amount` + `currency` منفصلين.</summary>
public sealed class InvoiceIssuedV1ToV2 : IEventUpcaster
{
    public string Type => "invoice.issued";
    public int FromVersion => 1;

    public JsonNode Upcast(JsonNode payload)
    {
        var obj = payload.AsObject();
        if (obj["amount"] is not null) return obj;                     // ✓ بالفعل بالصيغة الجديدة

        var total = obj["total"]?.GetValue<decimal>()
                    ?? throw new InvalidDataException("invoice.issued@1 بلا total");
        var currency = obj["currency"]?.GetValue<string>() ?? "EGP";   // ✓ قيمة افتراضية موثقة

        obj["amount"] = new JsonObject { ["amount"] = total, ["currency"] = currency };
        obj.Remove("total");
        obj.Remove("currency");
        return obj;
    }
}

/// <summary>سلسلة الـupcasting: v1 → v2 → v3 (ترتيب مهم).</summary>
public sealed class EventSerializer(IEnumerable<IEventUpcaster> upcasters) : IEventSerializer
{
    private readonly Dictionary<(string Type, int Version), IEventUpcaster> _map =
        upcasters.ToDictionary(u => (u.Type, u.FromVersion));

    public IDomainEvent DeserializeAndUpcast(string type, int schemaVersion, string payload)
    {
        var node = JsonNode.Parse(payload) ?? throw new InvalidDataException($"payload فارغ لـ{type}");
        var version = schemaVersion;

        // ★ اصعد إصدارًا بإصدار حتى الأحدث
        while (_map.TryGetValue((type, version), out var upcaster))
        {
            node = upcaster.Upcast(node);
            version++;
        }

        return MapToDomainEvent(type, node);                            // type → النوع الحالي في الكود
    }

    private static IDomainEvent MapToDomainEvent(string type, JsonNode node) => type switch
    {
        "invoice.issued"     => node.Deserialize<InvoiceIssued>()!,
        "invoice.voided"     => node.Deserialize<InvoiceVoided>()!,
        "payment.captured"   => node.Deserialize<PaymentCaptured>()!,
        "invoice.line_adjusted" => node.Deserialize<InvoiceLineAdjusted>()!,
        _ => new UnknownEvent(type, node),      // ✓ لا تفشل على حدث من إصدار أحدث (توافق أمامي)
    };
}

public sealed record UnknownEvent(string Type, JsonNode Payload) : IDomainEvent
{
    public DateTimeOffset OccurredAt => DateTimeOffset.MinValue;
}

// قواعد إصدار الأحداث (اكتبها في CONTRIBUTING):
// ① إضافة حقل اختياري بقيمة افتراضية → **لا** يحتاج إصدارًا جديدًا (توافق خلفي)
// ② إعادة تسمية/حذف/تغيير نوع حقل → إصدار جديد + upcaster + اختبار على بيانات قديمة
// ③ ممنوع حذف upcaster قديم ما دام فيه stream بهذا الإصدار (فحص: SELECT DISTINCT schema_ver)
// ④ كل upcaster له اختبار على payload حقيقي من الإنتاج (مش مثال مختلق)
'''},
            {"type": "heading", "level": 2, "text": "4) الأدوات الجاهزة في .NET"},
            {"type": "table", "head": ["الأداة", "التخزين", "المزايا", "اعتبارات"], "rows": [
                ["**Marten**", "PostgreSQL", "event store + projections + document DB في مكتبة واحدة، بلا بنية إضافية", "يربطك بـPostgres؛ افحص أداء الـprojections لحملك"],
                ["**EventStoreDB**", "مخصص (gRPC)", "مصمم للأحداث: اشتراكات، projections مدمجة، أداء عالي", "خدمة إضافية تشغّلها وتراقبها وتؤمنها"],
                ["**Wolfgang / Wolverine**", "Postgres", "مراسلة + أحداث في إطار واحد", "أصغر مجتمعًا من MassTransit"],
                ["**EF Core + outbox (MassTransit)**", "Postgres/SQL Server", "بلا event sourcing لكن بموثوقية رسائل", "★ الخيار الكافي لأغلب الفرق"],
                ["يدوي على Postgres (كما أعلاه)", "PostgreSQL", "بلا اعتماديات، تحكم كامل، سهل الفهم", "بتكتب snapshots/ projections/ upcasting بنفسك"],
            ]},
            {"type": "callout", "kind": "note", "title": "ملاحظة على APIs المكتبات الجاهزة",
             "md": """
المكتبات دي بتتطور بسرعة وتواقيعها بتتغير بين الإصدارات (Marten مثلًا غيّر API الـaggregations أكتر من مرة).
استخدم الكود اليدوي أعلاه لفهم **المفاهيم** (streams، version، fold، snapshots، upcasting) —
ولما تختار مكتبة، اقرأ توثيق إصدارك المحدد وابدأ بـspike صغير على بياناتك قبل الالتزام.

مهما كانت الأداة، الأسئلة اللي لازم تجاوبها بنفسك: **إزاي هتعمل migration لأحداث قديمة؟
إزاي هتحذف بيانات شخصية؟ وإزاي هتستعلم عن الحالة الحالية بسرعة؟**
"""},
            {"type": "heading", "level": 2, "text": "5) المشاكل التشغيلية (اللي بتظهر بعد 6 شهور)"},
            {"type": "table", "head": ["المشكلة", "ليه بتحصل", "الحل"], "rows": [
                ["الاستعلامات البسيطة بقت صعبة", "الحالة مش مخزنة — كل عرض يحتاج projection", "ابنِ projection لكل حالة عرض من البداية (وقِس تكلفة إعادة البناء)"],
                ["إصدار جديد من حدث قديم كسر الـreplay", "تغيير شكل الحدث بلا upcaster", "قواعد إصدار صارمة + اختبارات على payloads قديمة حقيقية"],
                ["حذف بيانات مستخدم (GDPR)", "السجل غير قابل للحذف", "شفّر الحقول الشخصية بمفتاح لكل مستخدم واحذف المفتاح (crypto-shredding)، أو خزن معرّف بدل البيانات"],
                ["stream بطول 200k حدث → تحميل بطيء", "بلا snapshots أو snapshot كل N كبير", "snapshot دوري (كل 50-100 حدث) + قيّم ضغط الـstream (stream per فترة)"],
                ["الـprojection تأخرت بعد إعادة بناء", "replay لملايين الأحداث", "خطة إعادة بناء متوازية + نسخة جديدة من الجدول + تبديل (shadow table)"],
                ["الأحداث صارت «API» غير مقصود", "كل مستهلك يعتمد على حقول الحدث", "عقود موثقة + إصدار + اختبار توافق"],
                ["التخزين بيكبر بلا حدود", "append-only بطبيعته", "أرشفة الـstreams المغلقة (cold storage) + احتفظ بـsnapshot نهائي"],
                ["صعوبة onboarding", "نموذج غير مألوف", "توثيق + مثال مرجعي + مراجعة صارمة لـApply (لا I/O ولا عدم حتمية)"],
            ]},
            {"type": "code", "lang": "csharp", "title": "اختبارات event sourcing (مختلفة عن اختبارات CRUD)", "code": r'''
public class InvoiceStreamTests
{
    private static readonly FixedClock Clock = new(new DateTimeOffset(2026, 10, 22, 9, 0, 0, TimeSpan.Zero));

    [Fact]
    public void Fold_produces_same_state_regardless_of_chunking()
    {
        var events = new List<IDomainEvent>
        {
            new InvoiceIssued(Guid.NewGuid(), Guid.NewGuid(), new Money(1000m, "EGP"), TestData.Lines(2), Clock.UtcNow),
        };

        var state = new InvoiceStream();
        foreach (var e in events) state.Apply(e);

        // ★ إعادة التطبيق (تكرار) لا تغيّر الحالة — idempotent fold
        foreach (var e in events) state.Apply(e);

        state.Status.Should().Be(InvoiceStatus.Issued);
        state.Lines.Should().HaveCount(2);
        state.Amount.Should().Be(new Money(1000m, "EGP"));
    }

    [Fact]
    public async Task Concurrent_append_on_same_stream_yields_conflict()
    {
        await using var store = new TestEventStore();          // Postgres حقيقي (Testcontainers)
        var streamId = Guid.NewGuid();
        await store.AppendAsync(streamId, "invoice", 0, [Issued()], Meta(), CancellationToken.None);

        // نسختان قرأتا الإصدار 1 وحاولتا الإضافة
        await store.AppendAsync(streamId, "invoice", 1, [Paid()], Meta(), CancellationToken.None);
        var second = () => store.AppendAsync(streamId, "invoice", 1, [Voided()], Meta(), CancellationToken.None);

        await second.Should().ThrowAsync<EventStoreConcurrencyException>()
            .Where(e => e.Message.Contains("توقعنا الإصدار 1"));
    }

    [Fact]
    public async Task Upcaster_migrates_v1_payload_to_current_shape()
    {
        const string V1Payload = """{"invoiceId":"...","customerId":"...","total":1000,"currency":"EGP","lines":[]}""";
        var serializer = new EventSerializer([new InvoiceIssuedV1ToV2()]);

        var e = serializer.DeserializeAndUpcast("invoice.issued", schemaVersion: 1, V1Payload);

        e.Should().BeOfType<InvoiceIssued>().Which.Amount.Should().Be(new Money(1000m, "EGP"));
    }

    [Fact]
    public async Task Unknown_future_event_is_ignored_not_fatal()
    {
        var serializer = new EventSerializer([]);
        var e = serializer.DeserializeAndUpcast("invoice.new_feature_from_v3", 1, "{}");

        e.Should().BeOfType<UnknownEvent>();
        var state = new InvoiceStream();
        var act = () => state.Apply(e);
        act.Should().NotThrow("التوافق الأمامي: حدث من إصدار أحدث لا يكسر القراءة");
    }

    [Fact]
    public async Task Snapshot_plus_tail_equals_full_fold()
    {
        await using var store = new TestEventStore();
        var streamId = Guid.NewGuid();
        // 120 حدثًا → يُلتقط snapshot بعد 50
        await store.AppendManyAsync(streamId, "invoice", Enumerable.Range(0, 120).Select(Adjust).ToList());

        var withSnapshot = await store.LoadAsync<InvoiceStream>(streamId, CancellationToken.None);
        var fromScratch = FoldManually(await store.ReadAllAsync(streamId, CancellationToken.None));

        withSnapshot.Version.Should().Be(120);
        JsonSerializer.Serialize(withSnapshot.State).Should().Be(JsonSerializer.Serialize(fromScratch),
            "التحميل من snapshot + الذيل لازم يساوي fold كامل");
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أفرّق بين Event Sourcing وaudit log وCRUD+events وأختار بأدلة (مش بحماس).",
                "أفهم streams/version/fold/snapshots وأعرف إن `Apply` لازم يكون حتميًا وبلا I/O.",
                "أتعامل مع إصدارات الأحداث عبر upcasting وقواعد تغيير صارمة واختبارات على بيانات قديمة.",
                "أعرف المشاكل التشغيلية (GDPR، نمو التخزين، صعوبة الاستعلام، إعادة البناء) وخطة كل واحدة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "في Event Sourcing، مصدر الحقيقة هو…",
                 "options": [
                     "جدول الحالة",
                     "تسلسل الأحداث (الحالة الحالية نتيجة fold عليها)",
                     "الـprojection",
                     "الـsnapshot",
                 ], "answer": 1,
                 "explain": "الجداول الأخرى كلها مشتقة وقابلة لإعادة البناء. ده اللي بيديك time travel وإعادة تشغيل."},
                {"q": "ليه `Apply` لازم يكون حتميًا (بلا `DateTime.Now` ولا عشوائية)؟",
                 "options": [
                     "للأداء",
                     "لأن إعادة تشغيل نفس الأحداث لازم تنتج نفس الحالة — وإلا الـreplay والـsnapshots بتدي نتائج مختلفة",
                     "مطلب المترجم",
                     "لتقليل الذاكرة",
                 ], "answer": 1,
                 "explain": "الزمن/القيم العشوائية تجيء من الحدث نفسه (occurred_at) أو من الـmetadata — مش من لحظة الـfold."},
                {"q": "غيرت شكل حدث موجود في 3 مليون صف قديم. التصرف؟",
                 "options": [
                     "UPDATE للأحداث القديمة",
                     "اكتب upcaster يحوّل v1→v2 وقت القراءة، وسجّل إصدار النوع، واختبره على payload حقيقي قديم",
                     "احذف الأحداث القديمة",
                     "أنشئ stream جديدة",
                 ], "answer": 1,
                 "explain": "تعديل السجل بيكسر مبدأ immutability والتدقيق. الـupcasting هو الآلية الوحيدة المقبولة (مع سلسلة إصدارات)."},
                {"q": "مستخدم طلب حذف بياناته (GDPR) والسجل غير قابل للحذف. الحل؟",
                 "options": [
                     "احذف الأحداث",
                     "crypto-shredding: شفّر الحقول الشخصية بمفتاح لكل مستخدم واحذف المفتاح، أو خزن معرّفات بدل البيانات الحساسة",
                     "تجاهل الطلب",
                     "احذف قاعدة البيانات",
                 ], "answer": 1,
                 "explain": "بعد حذف المفتاح، البيانات المشفرة تصير غير قابلة للقراءة = مسح فعلي. لازم تخطط لها من التصميم الأول."},
                {"q": "stream فيه 200,000 حدث والتحميل بقى بطيء. الحل؟",
                 "options": [
                     "احذف أحداث قديمة",
                     "snapshots دورية (كل 50-100 حدث) + تحميل من أحدث snapshot ثم الذيل فقط، وقياس زمن التحميل",
                     "زِد الـtimeout",
                     "لا تخزن أحداث",
                 ], "answer": 1,
                 "explain": "التحميل خطي في عدد الأحداث بلا snapshot. كمان قيّم تصميم الـstream (stream لكل فترة/دورة حياة) بدل stream واحد أبدي."},
                {"q": "أغلب الفرق محتاجة «نعرف مين غيّر إيه وليه». أنسب حل؟",
                 "options": [
                     "Event Sourcing كامل",
                     "CRUD + domain events عبر outbox + جدول audit_log في نفس المعاملة",
                     "لا شيء",
                     "طباعة اللوجات",
                 ], "answer": 1,
                 "explain": "بيديك التدقيق والتكامل بلا تكلفة ES (إصدارات أحداث للأبد، projections لكل استعلام، اتساق eventual)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "قرار event sourcing موثق",
                 "md": "اكتب ADR يقيّم Event Sourcing مقابل audit log مقابل CRUD+events لنظامك: جدول معايير، تقييم لكل خيار، القرار، وشروط إعادة النظر. لو قررت audit log: صمّم الجدول واكتبه في معاملة.",
                 "criteria": [
                     "جدول ≥ 8 معايير (تدقيق، time travel، استعلامات، اتساق، إصدارات، GDPR، تكلفة فريق، تخزين)",
                     "قرار صريح بدليل من متطلباتك (مش تفضيل عام)",
                     "لو audit log: الجدول يُكتب في نفس معاملة التغيير + اختبار يثبت تطابق السجل مع التغيير",
                     "معالجة صريحة لمتطلب حذف البيانات الشخصية (أيًا كان القرار)",
                     "شروط إعادة نظر مقاسة",
                 ]},
                {"id": "t2", "title": "نموذج event sourcing مصغّر (لو اخترت التجربة)",
                 "md": "نفّذ stream واحدة (فاتورة/حجز) على Postgres: جداول events/snapshots/checkpoints، append بتنافس أمثل، fold، snapshot كل 50 حدث، وprojection واحدة. اختبر الحالات الحرجة.",
                 "criteria": [
                     "append ذرّي مع تنافس أمثل (اختبار تعارض بين نسختين)",
                     "fold حتمي (اختبار: التطبيق المزدوج لا يغيّر الحالة)",
                     "snapshots: تحميل من snapshot + الذيل يساوي fold كامل (اختبار)",
                     "projection واحدة بـcheckpoint قابل لإعادة البناء (truncate + replay)",
                     "مثال upcaster واحد مع اختبار على payload قديم",
                     "قياس: زمن التحميل لـstream بـ100 و1000 و10000 حدث (جدول)",
                 ],
                 "hint": "خلي الـaggregate صغير (كيان واحد). لو لقيت نفسك بتطبق أحداث من aggregates تانية داخل الـfold → الحدود غلط."},
            ]},
            {"type": "resources", "items": [
                {"label": "Event Sourcing pattern (MS Learn)", "url": "https://learn.microsoft.com/azure/architecture/patterns/event-sourcing"},
                {"label": "Marten — Event store", "url": "https://martendb.io/events/"},
                {"label": "EventStoreDB documentation", "url": "https://www.eventstore.com/docs"},
                {"label": "Event versioning & upcasting", "url": "https://learn.microsoft.com/azure/architecture/patterns/event-sourcing#event-versioning"},
                {"label": "CQRS + Event Sourcing guidance", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/cqrs-microservice-reads"},
                {"label": "Crypto-shredding & GDPR", "url": "https://gdpr-info.eu/art-17-gdpr/"},
            ]},
        ],
    },
]
