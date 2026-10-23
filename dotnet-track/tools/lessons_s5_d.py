"""Stage 5, Module 2 — Messaging & reliability (lessons 3-4 of 5): Sagas & Resilience."""

TODAY = "2026-10-22"

LESSONS_S5_D = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s5-m2-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
في درس 5.1.2 كتبنا Saga يدويًا (منسّق + حالة محفوظة + تعويضات). الكود كان واضح، لكن فيه حاجات
لازم تكتبها بنفسك: الحفظ والاستئناف بعد الانهيار، المهلات المجدولة، منع تكرار الانتقالات، والمراقبة.

**MassTransit** بيديك كل ده كـ**state machine دائم**: حالات وأحداث وانتقالات معلنة، حفظ تلقائي في قاعدة البيانات،
مهلات (schedules) بتعيش بعد إعادة التشغيل، واختبارات بـtest harness.

الدرس ده: تصميم saga صحيح، تنفيذه بـMassTransit، حفظه في EF Core، التعويض والمهلات،
و**المراقبة** (اللي أغلب الفرق بتنساه لحد ما يلاقي 400 saga عالق من شهر).
"""},
            {"type": "terms", "items": [
                {"term": "Saga / Process Manager", "def": "حالة طويلة العمر لعملية عمل عبر خدمات: خطوات، انتقالات، وتعويضات. Saga (مصطلح DDD) بلا حالة عمل؛ Process Manager بيحتفظ بحالة — عمليًا الاسمَين بيتستخدموا لنفس الحاجة."},
                {"term": "State Machine", "def": "تعريف معلن: حالات (`State`)، أحداث (`Event<T>`)، وانتقالات (`Initially`/`During`/`Finally`)."},
                {"term": "CorrelationId", "def": "المفتاح اللي بيربط كل الرسائل بنفس نسخة الـsaga (عادةً `OrderId`) — بيضمن idempotency تلقائيًا."},
                {"term": "Compensating Event", "def": "حدث/أمر يعكس أثر خطوة تمت (`ReleaseStock`, `RefundPayment`)."},
                {"term": "Schedule / Timeout", "def": "مهلة مجدولة محفوظة في القاعدة: لو خطوة ما ردّتتش خلال M دقائق → حدث مهلة يعوّض."},
                {"term": "Saga Repository", "def": "مكان حفظ الحالة (EF Core/Postgres، Redis، Marten…). بلا حفظ → الـsaga بيموت مع العملية."},
                {"term": "Optimistic Concurrency (saga)", "def": "نسختان من نفس الـsaga تعالجان حدثين في نفس اللحظة → تعارض يُحل بإعادة المحاولة."},
                {"term": "Stuck Saga", "def": "نسخة في حالة وسيطة من غير تقدم (مهلة مفقودة/مستهلك واقع) — أخطر مشكلة تشغيلية، وتحتاج إنذارًا."},
                {"term": "Choreography", "def": "بلا منسّق: كل خدمة تستمع وتنفذ وتنشر. التدفق مشتت — أصعب في التتبع والاختبار."},
            ]},
            {"type": "heading", "level": 2, "text": "1) صمّم العملية أولًا (قبل الكود)"},
            {"type": "code", "lang": "text", "filename": "docs/sagas/order-fulfillment.md", "title": "رسم الحالات والانتقالات — الوثيقة اللي تمنع 80% من الأخطاء", "code": r'''
# Saga: تنفيذ الطلب (Order Fulfillment)

CorrelationId = OrderId · المهلة الكلية = 15 دقيقة · التعويض = عكس الترتيب

## الحالات
  Pending            → ابتدائية (اتسجلت بعد OrderPlaced)
  StockReserved      → المخزون محجوز (expires في 10 دقائق)
  PaymentCaptured    → الدفع محصّل
  Completed          → ★ نهائية (شحن مُجدول، طلب مؤكَّد)
  StockReservationFailed → نهائية (لا تعويض لازم)
  PaymentFailed      → نهائية بعد تعويض (تحرير الحجز)
  Faulted / NeedsManual → نهائية (تعويض فشل → تدخل بشري)

## الانتقالات
  (start)            --OrderPlaced----------------------> Pending            [أنشئ + جدوله StockTimeout]
  Pending            --StockReserved---------------------> StockReserved      [جدوله PaymentTimeout]
  Pending            --StockReservationFailed------------> StockReservationFailed
  Pending            --StockTimeoutExpired---------------> Pending            [أعد المحاولة مرة واحدة ثم فشل]
  StockReserved      --PaymentCaptured-------------------> Completed          [أرسل ScheduleShipment]
  StockReserved      --PaymentFailed---------------------> PaymentFailed      [أرسل ReleaseStock]
  StockReserved      --PaymentTimeoutExpired-------------> PaymentFailed      [أرسل ReleaseStock]
  PaymentFailed      --StockReleased---------------------> PaymentFailed (نهائية)
  أي حالة            --CancelRequested-------------------> Compensating…      [عكس ما تم]

## التعويضات (بالترتيب العكسي)
  1. CancelShipment  (لو الشحنة جُدولت — idempotent: إلغاء غير موجود = نجاح)
  2. RefundPayment   (لو الدفع تحصّل — الأهم: لا تحصيل بلا طلب)
  3. ReleaseStock    (لو الحجز تم)

## المهلات
  StockTimeout   = 5 دقائق  (حجز المخزون ما ردّش)
  PaymentTimeout = 10 دقائق (الدفع ما ردّش — يشمل بوابة خارجية بطيئة)
  SagaTimeout    = 15 دقيقة (الحالة الكلية — آخر شبكة أمان → NeedsManual)

## قواعد
  • كل خطوة idempotent (إعادة التسليم/إعادة المحاولة لا تكرر الأثر)
  • فشل التعويض ≠ فشل الـsaga: حالة NeedsManual + تنبيه حرج
  • لا منطق عمل داخل الـsaga (تنسيق فقط؛ القواعد في الخدمات)
  • كل الانتقالات تُسجَّل (audit) مع السبب والرسالة المسببة
'''},
            {"type": "heading", "level": 2, "text": "2) العقود: أوامر وأحداث لكل خطوة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Contracts/Orders/Fulfillment.cs", "title": "كل رسالة تحمل CorrelationId = OrderId", "code": r'''
namespace Shop.Contracts.Orders;

// ═══ مدخلات الـsaga ═══
public sealed record OrderPlaced(Guid OrderId, Guid CustomerId, decimal TotalMinorUnits, string Currency,
                                 IReadOnlyList<StockLine> Lines, DateTimeOffset OccurredAt) : CorrelatedBy(Guid OrderId);

// ═══ أوامر (Send) للخدمات ═══
public sealed record ReserveStock(Guid OrderId, IReadOnlyList<StockLine> Lines) : CorrelatedBy(Guid OrderId);
public sealed record CapturePayment(Guid OrderId, Guid CustomerId, decimal AmountMinorUnits, string Currency)
    : CorrelatedBy(Guid OrderId);
public sealed record ScheduleShipment(Guid OrderId, Guid CustomerId) : CorrelatedBy(Guid OrderId);

// ═══ تعويضات (Send) ═══
public sealed record ReleaseStock(Guid OrderId, Guid ReservationId) : CorrelatedBy(Guid OrderId);
public sealed record RefundPayment(Guid OrderId, Guid ChargeId, string Reason) : CorrelatedBy(Guid OrderId);
public sealed record CancelShipment(Guid OrderId, string Reason) : CorrelatedBy(Guid OrderId);

// ═══ ردود (أحداث) من الخدمات ═══
public sealed record StockReserved(Guid OrderId, Guid ReservationId, DateTimeOffset ExpiresAt) : CorrelatedBy(Guid OrderId);
public sealed record StockReservationFailed(Guid OrderId, string Reason, IReadOnlyList<Guid> MissingProducts)
    : CorrelatedBy(Guid OrderId);
public sealed record PaymentCaptured(Guid OrderId, Guid ChargeId) : CorrelatedBy(Guid OrderId);
public sealed record PaymentFailed(Guid OrderId, string Reason, bool Retryable) : CorrelatedBy(Guid OrderId);
public sealed record ShipmentScheduled(Guid OrderId, Guid ShipmentId, string Carrier) : CorrelatedBy(Guid OrderId);
public sealed record StockReleased(Guid OrderId) : CorrelatedBy(Guid OrderId);
public sealed record PaymentRefunded(Guid OrderId, Guid RefundId) : CorrelatedBy(Guid OrderId);

// ═══ أحداث انتهاء (للمستهلكين الخارجيين: إشعارات، تقارير) ═══
public sealed record OrderFulfillmentCompleted(Guid OrderId, DateTimeOffset CompletedAt) : CorrelatedBy(Guid OrderId);
public sealed record OrderFulfillmentFailed(Guid OrderId, string Reason, string FailedStep, DateTimeOffset At)
    : CorrelatedBy(Guid OrderId);

/// <summary>كل الرسائل بتُربط بنفس المفتاح → نسخة saga واحدة لكل طلب (idempotency تلقائية).</summary>
public interface CorrelatedBy<out T> where T : notnull { T OrderId { get; } }
'''},
            {"type": "heading", "level": 2, "text": "3) الـState Machine"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Sagas/OrderFulfillmentStateMachine.cs", "title": "الحالات والانتقالات والمهلات والتعويض", "code": r'''
using MassTransit;

/// <summary>الحالة المحفوظة — ★ حقول قليلة (لا كيانات كاملة)، وقابلة للتسلسل.</summary>
public sealed class OrderFulfillmentState : SagaStateMachineInstance, ISagaVersion
{
    public Guid CorrelationId { get; set; }              // = OrderId
    public string CurrentState { get; set; } = default!; // ★ اسم الحالة (يُحفظ كنص)
    public int Version { get; set; }                     // تنافس أمثل

    public Guid CustomerId { get; set; }
    public decimal TotalMinorUnits { get; set; }
    public string Currency { get; set; } = "EGP";
    public Guid? ReservationId { get; set; }
    public Guid? ChargeId { get; set; }
    public Guid? ShipmentId { get; set; }
    public int StockAttempts { get; set; }
    public string? FailureReason { get; set; }
    public DateTimeOffset StartedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }

    // ★ معرّفات المهلات المجدولة (MassTransit بيحفظها ويلغيها عند الانتقال)
    public Guid? StockTimeoutId { get; set; }
    public Guid? PaymentTimeoutId { get; set; }
    public Guid? SagaTimeoutId { get; set; }
}

public sealed class OrderFulfillmentStateMachine : MassTransitStateMachine<OrderFulfillmentState>
{
    // ── الحالات ──
    public State Pending { get; private set; } = null!;
    public State StockReserved { get; private set; } = null!;
    public State AwaitingShipment { get; private set; } = null!;
    public State Compensating { get; private set; } = null!;
    public State NeedsManual { get; private set; } = null!;
    // الحالات النهائية تُعلن كذلك عشان الـsaga تُحذف/تُؤرشف
    public State Completed { get; private set; } = null!;
    public State Failed { get; private set; } = null!;

    // ── الأحداث ──
    public Event<OrderPlaced> OrderPlacedEvent { get; private set; } = null!;
    public Event<StockReserved> StockReservedEvent { get; private set; } = null!;
    public Event<StockReservationFailed> StockFailedEvent { get; private set; } = null!;
    public Event<PaymentCaptured> PaymentCapturedEvent { get; private set; } = null!;
    public Event<PaymentFailed> PaymentFailedEvent { get; private set; } = null!;
    public Event<ShipmentScheduled> ShipmentScheduledEvent { get; private set; } = null!;

    // ── المهلات (أحداث داخلية مجدولة) ──
    public Event<StockTimeoutExpired> StockTimeoutEvent { get; private set; } = null!;
    public Event<PaymentTimeoutExpired> PaymentTimeoutEvent { get; private set; } = null!;
    public Event<SagaTimeoutExpired> SagaTimeoutEvent { get; private set; } = null!;

    public Schedule<OrderFulfillmentState, StockTimeoutExpired> StockTimeout { get; private set; } = null!;
    public Schedule<OrderFulfillmentState, PaymentTimeoutExpired> PaymentTimeout { get; private set; } = null!;
    public Schedule<OrderFulfillmentState, SagaTimeoutExpired> SagaTimeout { get; private set; } = null!;

    public OrderFulfillmentStateMachine()
    {
        // ① الحالة تُخزن كنص (أوضح في القاعدة والتقارير من رقم)
        InstanceState(x => x.CurrentState);

        // ② الربط: كل الأحداث ترتبط بنسخة saga عبر OrderId
        // ★ ملاحظة: لو الرسالة بتنفّذ CorrelatedBy<Guid> (بخاصية اسمها CorrelationId) الربط تلقائي.
        //   هنا نربط صراحة لأن اسم الحقل OrderId أوضح في لغة المجال (درس 4.2.1).
        Event(() => OrderPlacedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockReservedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockFailedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentCapturedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentFailedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => ShipmentScheduledEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockReleased, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentRefundedEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => CompensationFailed, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockTimeoutEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentTimeoutEvent, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => SagaTimeoutEvent, x => x.CorrelateById(m => m.Message.OrderId));

        // ★ ③ المهلات المجدولة (توقيع Schedule بيختلف قليلًا بين إصدارات MassTransit — راجع توثيق إصدارك)
        Schedule(() => StockTimeout, x => x.StockTimeoutId, s =>
        {
            s.Delay = TimeSpan.FromMinutes(5);
            s.Received = r => r.Any();               // لو وصل حدث المهلة متأخر → يُعالج (لا يُهمل)
        });
        Schedule(() => PaymentTimeout, x => x.PaymentTimeoutId, s => s.Delay = TimeSpan.FromMinutes(10));
        Schedule(() => SagaTimeout, x => x.SagaTimeoutId, s => s.Delay = TimeSpan.FromMinutes(15));

        // ④ عند الانتهاء: انشر حدثًا للمستهلكين الخارجيين
        SetCompletedWhenFinalized();

        // ═══ البداية ═══
        Initially(
            When(OrderPlacedEvent)
                .Then(ctx =>
                {
                    var m = ctx.Message;
                    ctx.Saga.CustomerId = m.CustomerId;
                    ctx.Saga.TotalMinorUnits = m.TotalMinorUnits;
                    ctx.Saga.Currency = m.Currency;
                    ctx.Saga.StartedAt = m.OccurredAt;
                    ctx.Saga.UpdatedAt = DateTimeOffset.UtcNow;
                })
                .Schedule(StockTimeout, ctx => new StockTimeoutExpired(ctx.Saga.CorrelationId))
                .Schedule(SagaTimeout, ctx => new SagaTimeoutExpired(ctx.Saga.CorrelationId))
                // ★ ابدأ بأرخص/أسهل خطوة قابلة للتراجع (الحجز) قبل الدفع
                .Send(ctx => new Uri("queue:stock-service"),
                      ctx => new ReserveStock(ctx.Message.OrderId, ctx.Message.Lines))
                .TransitionTo(Pending));

        // ═══Pending ═══
        During(Pending,
            When(StockReservedEvent)
                .Then(ctx => { ctx.Saga.ReservationId = ctx.Message.ReservationId; Touch(ctx.Saga); })
                .Unschedule(StockTimeout)
                .Schedule(PaymentTimeout, ctx => new PaymentTimeoutExpired(ctx.Saga.CorrelationId))
                .Send(ctx => new Uri("queue:payments-service"), ctx => new CapturePayment(
                    ctx.Saga.CorrelationId, ctx.Saga.CustomerId, ctx.Saga.TotalMinorUnits, ctx.Saga.Currency))
                .TransitionTo(StockReserved),

            When(StockFailedEvent)
                .Then(ctx => { ctx.Saga.FailureReason = ctx.Message.Reason; Touch(ctx.Saga); })
                .Unschedule(StockTimeout).Unschedule(SagaTimeout)
                .PublishAsync(ctx => ctx.Init<OrderFulfillmentFailed>(new
                 {
                     OrderId = ctx.Saga.CorrelationId, Reason = ctx.Message.Reason,
                     FailedStep = "ReserveStock", At = DateTimeOffset.UtcNow,
                 }))
                .Finalize(),

            // ✓ مهلة الحجز: أعد المحاولة **مرة واحدة** ثم فشل (لا دوران لانهائي)
            When(StockTimeoutEvent)
                .IfElse(ctx => ctx.Saga.StockAttempts < 1,        // ✓ إعادة محاولة واحدة فقط
                    retry => retry
                        .Then(ctx => { ctx.Saga.StockAttempts++; Touch(ctx.Saga); })
                        .Schedule(StockTimeout, ctx => new StockTimeoutExpired(ctx.Saga.CorrelationId))
                        .Send(ctx => new Uri("queue:stock-service"), ctx => new ReserveStock(ctx.Saga.CorrelationId, []))),
                    giveUp => giveUp
                        .Then(ctx => { ctx.Saga.FailureReason = "stock reservation timeout"; Touch(ctx.Saga); })
                        .Unschedule(SagaTimeout)
                        .PublishAsync(ctx => ctx.Init<OrderFulfillmentFailed>(new
                        {
                            OrderId = ctx.Saga.CorrelationId, Reason = "stock timeout",
                            FailedStep = "ReserveStock", At = DateTimeOffset.UtcNow,
                        }))
                        .Finalize()));

        // ═══ StockReserved ═══
        During(StockReserved,
            When(PaymentCapturedEvent)
                .Then(ctx => { ctx.Saga.ChargeId = ctx.Message.ChargeId; Touch(ctx.Saga); })
                .Unschedule(PaymentTimeout)
                .Send(ctx => new Uri("queue:shipping-service"), ctx => new ScheduleShipment(
                    ctx.Saga.CorrelationId, ctx.Saga.CustomerId))
                .TransitionTo(AwaitingShipment),                 // ★ حالة وسيطة حتى يؤكد الشحن
            // ✓ فشل الدفع → تعويض (تحرير الحجز)
            When(PaymentFailedEvent)
                .Then(ctx => { ctx.Saga.FailureReason = ctx.Message.Reason; Touch(ctx.Saga); })
                .Unschedule(PaymentTimeout)
                .Send(ctx => new Uri("queue:stock-service"), ctx =>
                    new ReleaseStock(ctx.Saga.CorrelationId, ctx.Saga.ReservationId!.Value))
                .TransitionTo(Compensating),

            // ✓ مهلة الدفع → نفس مسار التعويض
            When(PaymentTimeoutEvent)
                .Then(ctx => { ctx.Saga.FailureReason = "payment timeout"; Touch(ctx.Saga); })
                .Send(ctx => new Uri("queue:stock-service"), ctx =>
                    new ReleaseStock(ctx.Saga.CorrelationId, ctx.Saga.ReservationId!.Value))
                .TransitionTo(Compensating));

        // ═══ AwaitingShipment: آخر خطوة (لا تعويض لها غالبًا — إلغاء الشحنة idempotent) ═══
        During(AwaitingShipment,
            When(ShipmentScheduledEvent)
                .Then(ctx => { ctx.Saga.ShipmentId = ctx.Message.ShipmentId; Touch(ctx.Saga); })
                .Unschedule(SagaTimeout)
                .PublishAsync(ctx => ctx.Init<OrderFulfillmentCompleted>(new
                 {
                     OrderId = ctx.Saga.CorrelationId, CompletedAt = DateTimeOffset.UtcNow,
                 }))
                .TransitionTo(Completed)
                .Finalize(),

            When(SagaTimeoutEvent)
                .Then(ctx => { ctx.Saga.FailureReason = "shipment not confirmed"; Touch(ctx.Saga); })
                .Send(ctx => new Uri("queue:shipping-service"), ctx => new CancelShipment(
                    ctx.Saga.CorrelationId, "saga timeout"))
                .TransitionTo(NeedsManual)
                .PublishAsync(ctx => ctx.Init<SagaNeedsManualIntervention>(new
                 {
                     ctx.Saga.CorrelationId, State = ctx.Saga.CurrentState, Reason = ctx.Saga.FailureReason,
                 })));

        // ═══ Compensating: انتظر تأكيد التعويض ثم انهِ ═══
        During(Compensating,
            When(StockReleased)
                .Then(ctx => { ctx.Saga.ReservationId = null; Touch(ctx.Saga); })
                .Unschedule(SagaTimeout)
                .PublishAsync(ctx => ctx.Init<OrderFulfillmentFailed>(new
                 {
                     OrderId = ctx.Saga.CorrelationId, Reason = ctx.Saga.FailureReason ?? "compensated",
                     FailedStep = "CapturePayment", At = DateTimeOffset.UtcNow,
                 }))
                .TransitionTo(Failed)
                .Finalize(),

            // ★ التعويض نفسه فشل → حالة تحتاج تدخل بشري (لا تبتلعها!)
            When(CompensationFailed)
                .Then(ctx => { ctx.Saga.FailureReason = $"compensation failed: {ctx.Message.Reason}"; Touch(ctx.Saga); })
                .TransitionTo(NeedsManual)
                .PublishAsync(ctx => ctx.Init<SagaNeedsManualIntervention>(new
                 {
                     ctx.Saga.CorrelationId, State = ctx.Saga.CurrentState, Reason = ctx.Saga.FailureReason,
                 })),

            // ✓ شبكة الأمان الأخيرة: المهلة الكلية
            When(SagaTimeoutEvent)
                .Then(ctx => { ctx.Saga.FailureReason = "saga overall timeout"; Touch(ctx.Saga); })
                .TransitionTo(NeedsManual)
                .PublishAsync(ctx => ctx.Init<SagaNeedsManualIntervention>(new
                 {
                     ctx.Saga.CorrelationId, State = ctx.Saga.CurrentState, Reason = ctx.Saga.FailureReason,
                 })));

        // ── أي حدث غير متوقع في أي حالة: سجّله ولا تفشل بصمت ──
        DuringAny(
            When(StockReleased).Then(ctx => Touch(ctx.Saga)),
            When(PaymentRefundedEvent).Then(ctx => { ctx.Saga.ChargeId = null; Touch(ctx.Saga); }));
    }

    private static void Touch(OrderFulfillmentState s) => s.UpdatedAt = DateTimeOffset.UtcNow;

    // ★ الأحداث المتبقية مُعلنة هنا (الترتيب في C# لا يهم — الـconstructor بيستخدمها)
    public Event<StockReleased> StockReleased { get; private set; } = null!;
    public Event<PaymentRefunded> PaymentRefundedEvent { get; private set; } = null!;
    public Event<CompensationFailed> CompensationFailed { get; private set; } = null!;
}

// أحداث المهلات والداخلية
public sealed record StockTimeoutExpired(Guid OrderId);
public sealed record PaymentTimeoutExpired(Guid OrderId);
public sealed record SagaTimeoutExpired(Guid OrderId);
public sealed record CompensationFailed(Guid OrderId, string Reason);
public sealed record PaymentRefunded(Guid OrderId, Guid RefundId);
public sealed record SagaNeedsManualIntervention(Guid OrderId, string? State, string? Reason);
'''},
            {"type": "heading", "level": 2, "text": "4) الحفظ في EF Core + التسجيل"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Persistence/SagaMap.cs", "title": "تخطيط الحالة + تسجيل الـsaga", "code": r'''
// ═══ تخطيط EF (جدول واحد لكل saga) ═══
public sealed class OrderFulfillmentStateMap : IEntityTypeConfiguration<OrderFulfillmentState>
{
    public void Configure(EntityTypeBuilder<OrderFulfillmentState> b)
    {
        b.ToTable("order_fulfillment_sagas", "orders");
        b.HasKey(x => x.CorrelationId);
        b.Property(x => x.CurrentState).HasMaxLength(64).IsRequired();
        b.Property(x => x.Currency).HasMaxLength(3);
        b.Property(x => x.TotalMinorUnits).HasPrecision(18, 2);
        b.Property(x => x.FailureReason).HasMaxLength(2000);
        b.Property(x => x.Version).IsConcurrencyToken();     // ★ تنافس أمثل (نسخ متزامنة)

        // فهرس للمراقبة: الحالات العالقة
        b.HasIndex(x => new { x.CurrentState, x.UpdatedAt })
         .HasDatabaseName("ix_sagas_state_updated");
    }
}

// ═══ التسجيل ═══
public static class SagaRegistration
{
    public static IServiceCollection AddOrderFulfillmentSaga(this IServiceCollection services, IConfiguration config)
    {
        services.AddMassTransit(x =>
        {
            x.AddSagaStateMachine<OrderFulfillmentStateMachine, OrderFulfillmentState>()
             .EntityFrameworkRepository(r =>
             {
                 r.ConcurrencyMode = ConcurrencyMode.Optimistic;   // ★ أساسي مع مستهلكين متوازيين
                 r.AddDbContext<DbContext, AppDbContext>((provider, builder) =>
                     builder.UseNpgsql(config.GetConnectionString("Orders"),
                         npgsql => npgsql.MigrationsHistoryTable("__migrations", "orders")));
             });

            x.AddConsumers(typeof(OrderFulfillmentStateMachine).Assembly);

            x.UsingRabbitMq((context, cfg) =>
            {
                cfg.Host(new Uri(config["RabbitMq:Host"]!));
                cfg.UseMessageRetry(r => r.Interval(3, TimeSpan.FromSeconds(2)));
                cfg.UseDelayedRedelivery(r => r.Intervals(
                    TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(5)));
                cfg.ConfigureEndpoints(context);
            });
        });

        return services;
    }
}
'''},
            {"type": "heading", "level": 2, "text": "5) المراقبة: الـsagas العالقة"},
            {"type": "code", "lang": "sql", "filename": "db/saga-monitoring.sql", "title": "استعلامات الإنذار (شغّلها كل دقيقة)", "code": r'''
-- ① توزيع الحالات (لوحة): كم نسخة في كل حالة؟
SELECT current_state, count(*) AS sagas,
       min(updated_at) AS oldest, max(updated_at) AS newest
FROM orders.order_fulfillment_sagas
GROUP BY current_state ORDER BY count(*) DESC;

-- ② ★ sagas عالقة: في حالة غير نهائية بلا تحديث منذ 20 دقيقة
SELECT correlation_id, current_state, failure_reason,
       now() - updated_at AS stuck_for, stock_attempts
FROM orders.order_fulfillment_sagas
WHERE current_state NOT IN ('Completed', 'Failed', 'StockReservationFailed')
  AND updated_at < now() - interval '20 minutes'
ORDER BY updated_at;
-- أي صف = إنذار (page on-call)

-- ③ حالات NeedsManual (تحتاج تدخل بشري)
SELECT correlation_id, failure_reason, updated_at
FROM orders.order_fulfillment_sagas
WHERE current_state = 'NeedsManual'
ORDER BY updated_at DESC;

-- ④ زمن التنفيذ (p50/p95 من البداية للنهاية)
SELECT percentile_cont(0.5)  WITHIN GROUP (ORDER BY extract(epoch FROM updated_at - started_at)) AS p50_s,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM updated_at - started_at)) AS p95_s,
       count(*) FILTER (WHERE current_state = 'Completed') AS completed,
       count(*) FILTER (WHERE current_state IN ('Failed','NeedsManual')) AS failed
FROM orders.order_fulfillment_sagas
WHERE started_at > now() - interval '24 hours';

-- ⑤ أرشفة المنتهية (بلا تنظيف، الجدول بيكبر للأبد)
-- DELETE FROM orders.order_fulfillment_sagas
-- WHERE current_state IN ('Completed','Failed') AND updated_at < now() - interval '30 days';
'''},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Orders.Tests/Sagas/OrderFulfillmentSagaTests.cs", "title": "اختبار الـsaga: المسار السعيد، التعويض، المهلة، التكرار", "code": r'''
public class OrderFulfillmentSagaTests
{
    private static readonly Guid OrderId = Guid.NewGuid();

    private static async Task<(ITestHarness Harness, ISagaStateMachineTestHarness<OrderFulfillmentStateMachine, OrderFulfillmentState> Saga)>
        StartAsync()
    {
        await using var provider = new ServiceCollection()
            .AddMassTransitTestHarness(x =>
            {
                // ★ في الاختبارات: الحالة في الذاكرة (بلا EF) — أسرع وأبسط
                x.AddSagaStateMachine<OrderFulfillmentStateMachine, OrderFulfillmentState>()
                 .InMemoryInstance();
            })
            .BuildServiceProvider(true);

        var harness = provider.GetRequiredService<ITestHarness>();
        await harness.Start();
        var saga = harness.GetSagaHarness<OrderFulfillmentStateMachine, OrderFulfillmentState>();
        return (harness, saga);
    }

    [Fact]
    public async Task Happy_path_reaches_Completed()
    {
        var (harness, saga) = await StartAsync();

        await harness.Bus.Publish(new OrderPlaced(OrderId, Guid.NewGuid(), 25050, "EGP",
                                                  [new StockLine(Guid.NewGuid(), 2)], DateTimeOffset.UtcNow));
        await saga.Consumed.Any<StockReserved>(x => x.Context.Message.OrderId == OrderId);

        await harness.Bus.Publish(new StockReserved(OrderId, Guid.NewGuid(), DateTimeOffset.UtcNow.AddMinutes(10)));
        await saga.Consumed.Any<PaymentCaptured>(x => x.Context.Message.OrderId == OrderId);

        await harness.Bus.Publish(new PaymentCaptured(OrderId, Guid.NewGuid()));
        await harness.Bus.Publish(new ShipmentScheduled(OrderId, Guid.NewGuid(), "aramex"));

        // ★ الحالة النهائية
        Assert.True(await saga.Consumed.Any<ShipmentScheduled>(
            x => x.Context.Message.OrderId == OrderId, TimeSpan.FromSeconds(10)));
        var instance = await saga.Created.Any(x => x.CorrelationId == OrderId);
        instance!.CurrentState.Should().Be("Completed");

        // ✓ حدث الانتهاء نُشر للمستهلكين الخارجيين
        Assert.True(await harness.Published.Any<OrderFulfillmentCompleted>(TimeSpan.FromSeconds(5)));
        await harness.Stop();
    }

    [Fact]
    public async Task Payment_failure_compensates_by_releasing_stock()
    {
        var (harness, saga) = await StartAsync();

        await harness.Bus.Publish(new OrderPlaced(OrderId, Guid.NewGuid(), 1000, "EGP", [], DateTimeOffset.UtcNow));
        await harness.Bus.Publish(new StockReserved(OrderId, Guid.NewGuid(), DateTimeOffset.UtcNow.AddMinutes(10)));
        await harness.Bus.Publish(new PaymentFailed(OrderId, "card declined", Retryable: false));

        // ✓ التعويض أُرسل
        Assert.True(await harness.Sent.Any<ReleaseStock>(TimeSpan.FromSeconds(10)));
        var instance = await saga.Created.Any(x => x.CorrelationId == OrderId);
        instance!.CurrentState.Should().BeOneOf("Compensating", "Failed");

        await harness.Bus.Publish(new StockReleased(OrderId));
        Assert.True(await harness.Published.Any<OrderFulfillmentFailed>(TimeSpan.FromSeconds(10)));
        await harness.Stop();
    }

    [Fact]
    public async Task Duplicate_events_do_not_duplicate_transitions()
    {
        var (harness, saga) = await StartAsync();
        var placed = new OrderPlaced(OrderId, Guid.NewGuid(), 1000, "EGP", [], DateTimeOffset.UtcNow);

        await harness.Bus.Publish(placed);
        await harness.Bus.Publish(placed);          // ★ إعادة تسليم
        await harness.Bus.Publish(placed);

        var sent = await harness.Sent.Select<ReserveStock>().ToListAsync();
        sent.Should().HaveCount(1, "correlation id واحد = نسخة saga واحدة = انتقال واحد");

        await harness.Stop();
    }

    [Fact]
    public async Task Stock_timeout_retries_once_then_fails()
    {
        var (harness, saga) = await StartAsync();

        await harness.Bus.Publish(new OrderPlaced(OrderId, Guid.NewGuid(), 1000, "EGP", [], DateTimeOffset.UtcNow));
        // في الاختبارات: يمكن إطلاق المهلة يدويًا بدل الانتظار 5 دقائق
        await harness.Bus.Publish(new StockTimeoutExpired(OrderId));
        await harness.Bus.Publish(new StockTimeoutExpired(OrderId));

        var instance = await saga.Created.Any(x => x.CorrelationId == OrderId);
        instance!.StockAttempts.Should().Be(1);
        instance.CurrentState.Should().Be("StockReservationFailed");
        Assert.True(await harness.Published.Any<OrderFulfillmentFailed>(TimeSpan.FromSeconds(5)));

        await harness.Stop();
    }
}
'''},
            {"type": "table", "head": ["الحالة", "استخدم", "لييه"], "rows": [
                ["عملية عمل طويلة عبر ≥ 3 خدمات مع تعويضات", "**Saga (orchestration)**", "الحالة والانتقالات معلنة، والتتبع والاختبار أسهل"],
                ["خطوتان بلا تعويض معقد (إشعار بعد كتابة)", "**حدث عبر outbox**", "saga هنا تعقيد بلا فائدة"],
                ["قراءة لحظية من خدمة تانية", "**نداء متزامن (gRPC/REST)**", "لا حالة طويلة، ولا تعويض"],
                ["تدفق بسيط 2-3 خطوات وفرق مستقلة تمامًا", "Choreography", "اقتران أقل — لكن التدفق بيصير صعب التتبع"],
                ["عملية تحتاج تدخل بشري/موافقة (أيام)", "Saga + مهلات طويلة + حالة `AwaitingApproval`", "الحالة الدائمة ضرورية"],
                ["مزامنة بيانات مستمرة (CDC)", "Projection/عامل، لا saga", "بلا حالات عمل"],
            ]},
            {"type": "callout", "kind": "danger", "title": "7 قواعد Saga بتفرق بين نظام شغال وكارثة",
             "md": """
1. **ابدأ بأرخص خطوة قابلة للتراجع** (حجز مخزون) واختم بالأصعب (تحصيل مالي) — التعويض يبقى نادرًا.
2. **الحالة صغيرة**: معرّفات وأرقام وحالات — لا كيانات كاملة ولا payloads ضخمة (كل انتقال بيحفظها).
3. **مهلة لكل خطوة + مهلة كلية** — بلا مهلة، saga بيتعلّق للأبد ويحجز موارد.
4. **كل خطوة idempotent** — المنسّق هيعيد المحاولة، والوسيط هيعيد التسليم.
5. **فشل التعويض = `NeedsManual` + تنبيه حرج** (مش log وتحريك): ده معناه فلوس/مخزون في حالة مجهولة.
6. **لا منطق عمل في الـsaga** — تنسيق فقط. القواعد في الخدمات (وإلا بقى monolith مخفي).
7. **راقب الحالات العالقة من اليوم الأول** — استعلام `updated_at` + إنذار. أغلب كوارث الـsagas
   هي نُسَخ عالقة اكتُشفت بعد أسابيع.
"""},
            {"type": "checkpoints", "items": [
                "أصمم العملية أولًا (حالات، انتقالات، تعويضات، مهلات) كوثيقة قبل الكود.",
                "أنفّذها بـMassTransit state machine محفوظة في EF Core بتنافس أمثل وcorrelation id.",
                "أضع مهلة لكل خطوة ومهلة كلية، وأعيد المحاولة عددًا محدودًا ثم أفشل صراحة.",
                "أراقب الحالات العالقة وNeedsManual باستعلامات وإنذارات، وأختبر المسار السعيد والتعويض والتكرار والمهلة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه اللي بيضمن إن حدث مكرر ما يعملش انتقالين في الـsaga؟",
                 "options": [
                     "الوسيط بيمنع التكرار",
                     "correlation id: كل الأحداث بترتبط بنفس نسخة الـsaga، والانتقال في حالة غير متوقعة لا يُنفَّذ",
                     "قاعدة البيانات",
                     "idempotency key في الرسالة",
                 ], "answer": 1,
                 "explain": "ده أحد أكبر مكاسب الـsaga: idempotency بنيوية. كمان الحالة (CurrentState) بتمنع تكرار انتقال تم فعلًا."},
                {"q": "ليه الحفظ في قاعدة البيانات مش اختياري؟",
                 "options": [
                     "للأداء",
                     "لأن العملية بتعيش دقائق/أيام: بلا حفظ، أي إعادة نشر أو انهيار بيمسح الحالة ويترك آثارًا بلا منسّق",
                     "مطلب MassTransit",
                     "للتقارير فقط",
                 ], "answer": 1,
                 "explain": "كمان المهلات المجدولة بتُحفظ، فبتشتغل بعد إعادة التشغيل — وده اللي بيخلي `NeedsManual` مش حالة نظرية."},
                {"q": "خطوة التعويض (رد المبلغ) فشلت. التصرف؟",
                 "options": [
                     "سجّل warning وأكمل",
                     "انتقل لحالة `NeedsManual` + انشر حدث إنذار + تنبيه on-call — الأموال في حالة مجهولة ويجب تدخل بشري",
                     "أعد المحاولة للأبد",
                     "احذف الـsaga",
                 ], "answer": 1,
                 "explain": "فشل التعويض أخطر من فشل الخطوة الأصلية. لازم يبقى مرئيًا (استعلام SQL + إنذار + أداة معالجة)."},
                {"q": "ليه تبدأ saga بحجز المخزون قبل تحصيل الدفع؟",
                 "options": [
                     "أسرع",
                     "لأن الحجز أرخص وأسهل في التراجع — فالتعويض (اللي هو أصعب وأخطر جزء) بيصير نادرًا",
                     "ترتيب إجباري",
                     "لأن الدفع يحتاج موافقة",
                 ], "answer": 1,
                 "explain": "القاعدة العامة: رتّب الخطوات من الأسهل تراجعًا للأصعب. لو الدفع الأول، كل فشل مخزون يعني رد أموال."},
                {"q": "متى تكفي outbox بلا saga؟",
                 "options": [
                     "دائمًا",
                     "لما الأثر الجانبي خطوة واحدة بلا تعويض معقد (إشعار/تسجيل) أو لما التعويض غير مطلوب",
                     "لما فيه 5 خدمات",
                     "أبدًا",
                 ], "answer": 1,
                 "explain": "saga بيضيف حالة ومهلات ومراقبة — تكلفة حقيقية. استخدمه لما فيه ≥ 3 خطوات وتعويضات."},
                {"q": "400 نسخة saga في حالة `StockReserved` من 3 أيام. التشخيص الأول؟",
                 "options": [
                     "احذفهم",
                     "هل خدمة الدفع واقفة/بطيئة؟ هل `PaymentTimeout` مجدول فعلًا (ومُخزَّن)؟ هل المستهلك بيستهلك قائمة الدفع؟",
                     "زد عدد المستهلكين",
                     "أعد تشغيل الوسيط",
                 ], "answer": 1,
                 "explain": "ده بالظبط سيناريو «sagas عالقة». المهلة الكلية + استعلام المراقبة بيحوّلوه من كارثة صامتة لإنذار خلال دقائق."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "saga كامل بـMassTransit",
                 "md": "نفّذ saga لعملية عمل حقيقية في مشروعك (تنفيذ طلب، استرجاع، تفعيل اشتراك) بـ3 خطوات على الأقل وتعويض ومهلات، محفوظ في EF Core. اختبر المسارات الأربعة.",
                 "criteria": [
                     "وثيقة تصميم أولًا (حالات/انتقالات/تعويضات/مهلات) في `docs/sagas/`",
                     "حالة محفوظة في جدول مع `Version` كـconcurrency token وفهرس `(current_state, updated_at)`",
                     "مهلة لكل خطوة + مهلة كلية → `NeedsManual` عند تجاوزها",
                     "إعادة محاولة محدودة لخطوة واحدة ثم فشل صريح (لا دوران لانهائي)",
                     "4 اختبارات: المسار السعيد، التعويض، حدث مكرر، مهلة",
                     "حدث انتهاء يُنشر للمستهلكين الخارجيين (إشعارات/تقارير)",
                 ],
                 "hint": "لو اختبار المهلات بطيء: اجعل التأخيرات قابلة للضبط من الإعدادات (ثوانٍ في الاختبار، دقائق في الإنتاج) أو أطلق حدث المهلة يدويًا كما في المثال."},
                {"id": "t2", "title": "مراقبة ومعالجة الحالات العالقة",
                 "md": "أضف استعلامات المراقبة (توزيع الحالات، العالقة، NeedsManual، زمن التنفيذ) كمهمة مجدولة تنشر مقاييس وتنبّه، وأداة إدارية (endpoint داخلي) لإعادة دفع saga عالق أو إنهائه يدويًا.",
                 "criteria": [
                     "4 استعلامات مراقبة موثقة + مقياس منشور لكل واحد",
                     "إنذار: أي saga في حالة غير نهائية بلا تحديث > 20 دقيقة (مع اختبار يثبت الاكتشاف)",
                     "endpoint إداري (خلف تفويض داخلي) يعرض حالة saga ويعيد دفعه أو ينهيه مع سبب مسجّل",
                     "أرشفة/حذف المنتهية أقدم من N يومًا (مهمة دورية)",
                     "توثيق «إزاي تعالج saga عالق» بخطوات تشغيلية (runbook)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "MassTransit — Sagas (state machines)", "url": "https://masstransit.io/documentation/concepts/sagas"},
                {"label": "MassTransit — Scheduling", "url": "https://masstransit.io/documentation/concepts/scheduling"},
                {"label": "MassTransit — EF Core saga persistence", "url": "https://masstransit.io/documentation/concepts/sagas/persistence"},
                {"label": "Saga pattern (microservices.io)", "url": "https://microservices.io/patterns/data/saga.html"},
                {"label": "Life beyond distributed transactions", "url": "https://learn.microsoft.com/azure/architecture/microservices/design/patterns"},
                {"label": "MassTransit Testing", "url": "https://masstransit.io/documentation/configuration/testing"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s5-m2-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
في الأنظمة الموزعة، الاعتماد على خدمة تانية **هيفشل** — مش «ممكن يفشل». الشبكة بتقطع، الخدمات بتتعطل،
والمهلات بتنتهي. السؤال مش «هل هنواجه فشل» لكن «إيه اللي هيعمله كودنا لما يحصل».

.NET الحديث بيديك **Microsoft.Extensions.Resilience** (مبني على **Polly v8**): خطوط أنابيب مرونة معلنة
(retry، circuit breaker، timeout، rate limiter، fallback، hedging) بتتطبق على `HttpClient` أو أي نداء.

الدرس ده بيعلّمك: أنهي استراتيجية لأي نوع فشل، **ترتيب الـpipeline** (اللي بيغلط فيه أغلب الناس)،
إزاي تتجنب عاصفة إعادة المحاولة، وتوزيع المهلات عبر الخدمات، وإمتى **ما** تستخدمش مرونة خالص.
"""},
            {"type": "terms", "items": [
                {"term": "Transient Failure", "def": "فشل عابر (timeout، 503، reset اتصال) — إعادة المحاولة ممكن تنجح."},
                {"term": "Permanent Failure", "def": "فشل دائم (400، 401، 404، قيد قاعدة) — إعادة المحاولة **مضيعة** وبتزيد الحمل."},
                {"term": "Retry + Backoff + Jitter", "def": "إعادة محاولة بفترات متزايدة وعشوائية — Jitter يمنع تزامن كل العملاء (thundering herd)."},
                {"term": "Circuit Breaker", "def": "بعد N فشل في فترة M: «يفتح» ويرفض النداءات فورًا (بلا انتظار) لفترة، ثم يجرب (half-open). بيحمي الاعتماد المتعافي."},
                {"term": "Bulkhead", "def": "عزل: حد أقصى للنداءات المتزامنة لكل اعتماد — فشل اعتماد لا يستهلك كل خيوط/اتصالات خدمتك."},
                {"term": "Timeout", "def": "سقف زمني للنداء. بلا مهلة: خيوط محجوزة ولاتنتهي."},
                {"term": "Fallback", "def": "سلوك بديل عند الفشل (قيمة مخزنة، كاش قديم، تدهور معلَن) — لازم يكون **مُعلنًا** لا صامتًا."},
                {"term": "Hedging", "def": "إرسال نفس النداء لأكثر من نسخة بعد تأخير وأخذ أول رد — للقراءات idempotent فقط."},
                {"term": "Resilience Pipeline", "def": "سلسلة استراتيجيات بترتيب محدد. **الترتيب يغير السلوك جذريًا**."},
                {"term": "Load Shedding", "def": "رفض حمل زائد عمدًا (429/503) لحماية النظام من الانهيار الكامل."},
                {"term": "Retry Storm", "def": "إعادة محاولة متزامنة من كل العملاء/الطبقات → تضخيم الحمل على خدمة بتحاول تتعافى."},
            ]},
            {"type": "heading", "level": 2, "text": "1) أنهي استراتيجية لأي فشل؟"},
            {"type": "table", "head": ["نوع الفشل", "الاستراتيجية", "المعاملات المهمة", "تحذير"], "rows": [
                ["timeout / 502/503/504 / reset اتصال", "**Retry** (exponential + jitter)", "MaxRetryAttempts 2-3، Delay 200ms-1s، BaseDelay/MaxDelay", "النداء لازم يكون idempotent"],
                ["فشل متكرر من اعتماد واحد", "**Circuit Breaker**", "FailureRatio 0.5، SamplingDuration 10-30s، MinimumThroughput 10، BreakDuration 15-60s", "بلا MinimumThroughput → يفتح من فشلين"],
                ["نداء بطيء/معلّق", "**Timeout**", "كل طبقة أقصر من اللي فوقها", "مهلة أطول من مهلة المُنادي = بلا قيمة"],
                ["اعتماد بيسحب كل الموارد", "**Bulkhead** (concurrency limit)", "حد لكل اعتماد (مثلاً 10-20 متزامن)", "حد صغير جدًا = طوابير؛ كبير = بلا عزل"],
                ["حمل زائد على خدمتك", "**Rate Limiter / Load Shedding**", "429 + `Retry-After` (درس 2.1.5)", "رفض صريح أفضل من بطء عام"],
                ["قراءة غير حرجة فشلت", "**Fallback** (كاش قديم/قيمة افتراضية)", "أعلن التدهور (header/metric/log)", "لا fallback صامت لبيانات مالية"],
                ["قراءة idempotent بطيئة في الذيل", "**Hedging**", "نسخة تانية بعد p95", "يضاعف الحمل — للقراءات فقط"],
                ["400/401/403/404/409", "**لا إعادة محاولة**", "فشل فوري + استثناء/نتيجة واضحة", "إعادة المحاولة بتخفي bug"],
                ["قيد قاعدة / تحقق من بيانات", "**لا إعادة محاولة**", "صحّح المدخلات", "—"],
                ["كتابة غير idempotent فشلت", "**لا إعادة محاولة تلقائية**", "idempotency key أولًا (درس 5.2.5)", "خطر أثر مضاعف"],
                ["الوسيط واقع (RabbitMQ/Kafka)", "**Outbox + إعادة تسليم مؤجلة**", "delayed redelivery بمراحل", "لا retry فوري بلا حدود"],
            ]},
            {"type": "heading", "level": 2, "text": "2) الـpipeline: الترتيب يغيّر كل شيء"},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/ResiliencePipelines.cs", "title": "خط أنابيب مسمى + الاستخدام", "code": r'''
using Microsoft.Extensions.Resilience;
using Polly;

public static class ResiliencePipelines
{
    public const string ExternalPayment = "external-payment";
    public const string InternalRead = "internal-read";

    public static IServiceCollection AddResilience(this IServiceCollection services)
    {
        // ═══ ① pipeline لكتابة خارجية غير idempotent نسبيًا (بوابة دفع) ═══
        services.AddResiliencePipeline(ExternalPayment, builder =>
        {
            // ★ الترتيب من **الخارج للداخل**: أول strategy تُضاف هي الأبعد عن النداء الفعلي
            builder.AddTimeout(new TimeoutStrategyOptions
            {
                Timeout = TimeSpan.FromSeconds(20),                    // 1. سقف كلي (يشمل كل المحاولات)
                OnTimeout = args => { Metrics.Timeouts.Add(1, new("pipeline", ExternalPayment));
                                      return ValueTask.CompletedTask; },
            });

            builder.AddCircuitBreaker(new CircuitBreakerStrategyOptions
            {
                FailureRatio = 0.5,                                    // 2. لو 50% فشلوا…
                MinimumThroughput = 10,                                //    …من 10 نداءات على الأقل
                SamplingDuration = TimeSpan.FromSeconds(30),           //    …خلال 30 ثانية
                BreakDuration = TimeSpan.FromSeconds(30),              // 3. اقطع 30 ثانية (ثم half-open)
                ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
                    .Handle<HttpRequestException>()
                    .Handle<TimeoutRejectedException>()
                    .HandleResult(r => (int)r.StatusCode >= 500),      // ✓ 5xx فقط (لا 4xx)
                OnOpened = args => { Log.Warning("circuit OPENED for payments"); return ValueTask.CompletedTask; },
                OnClosed = args => { Log.Information("circuit closed for payments"); return ValueTask.CompletedTask; },
            });

            builder.AddRetry(new RetryStrategyOptions<HttpResponseMessage>
            {
                MaxRetryAttempts = 2,                                  // 4. محاولتان إضافيتان
                BackoffType = DelayBackoffType.Exponential,
                Delay = TimeSpan.FromMilliseconds(500),
                MaxDelay = TimeSpan.FromSeconds(5),
                UseJitter = true,                                      // ★ jitter: يمنع التزامن
                ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
                    .Handle<HttpRequestException>()
                    .Handle<TimeoutRejectedException>()
                    .HandleResult(r => (int)r.StatusCode >= 500
                                    || r.StatusCode is HttpStatusCode.RequestTimeout
                                                  or HttpStatusCode.TooManyRequests),
                DelayGenerator = args =>                              // ✓ احترم Retry-After لو موجود
                {
                    if (args.Outcome.Result?.Headers.RetryAfter?.Delta is { } delta && delta <= TimeSpan.FromSeconds(10))
                        return ValueTask.FromResult<TimeSpan?>(delta);
                    return ValueTask.FromResult<TimeSpan?>(null);
                },
                OnRetry = args =>
                {
                    Log.Warning("retry {Attempt} after {Delay}ms (status={Status})",
                        args.AttemptNumber, args.RetryDelay.TotalMilliseconds,
                        args.Outcome.Result?.StatusCode);
                    Metrics.Retries.Add(1, new("pipeline", ExternalPayment));
                    return ValueTask.CompletedTask;
                },
            });

            builder.AddConcurrencyLimiter(new ConcurrencyLimiterOptions    // 5. عزل (bulkhead)
            {
                PermitLimit = 12, QueueLimit = 24, QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
            });
        });

        // ═══ ② pipeline لقراءة داخلية (أسرع، مع fallback معلن) ═══
        services.AddResiliencePipeline<HttpResponseMessage>(InternalRead, builder => builder
            .AddTimeout(TimeSpan.FromSeconds(3))
            .AddRetry(new RetryStrategyOptions<HttpResponseMessage>
            {
                MaxRetryAttempts = 3, Delay = TimeSpan.FromMilliseconds(100),
                BackoffType = DelayBackoffType.Exponential, UseJitter = true,
            })
            .AddHedging(new HedgingStrategyOptions<HttpResponseMessage>     // ✓ قراءة idempotent فقط
            {
                MaxHedgedAttempts = 1,
                Delay = TimeSpan.FromMilliseconds(400),                     // بعد p95 المحلي
            })
            .AddFallback(new FallbackStrategyOptions<HttpResponseMessage>
            {
                ShouldHandle = new PredicateBuilder<HttpResponseMessage>().Handle<Exception>(),
                FallbackAction = _ => Outcome.FromResultAsValueTask(        // ★ تدهور **معلن**
                    new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
                    {
                        Content = new StringContent("""{"degraded":true,"source":"fallback"}"""),
                        Headers = { { "X-Degraded", "true" } },
                    }),
            }));

        return services;
    }
}

/// <summary>الاستخدام: حلّ الـpipeline بالاسم ونفّذ داخله.</summary>
public sealed class PaymentGateway(
    ResiliencePipelineProvider<string> pipelines, HttpClient http, ILogger<PaymentGateway> log) : IPaymentGateway
{
    public async Task<ChargeResult> CaptureAsync(Guid orderId, Money amount, string idempotencyKey, CancellationToken ct)
    {
        var pipeline = pipelines.GetPipeline(ResiliencePipelines.ExternalPayment);

        try
        {
            return await pipeline.ExecuteAsync(async token =>
            {
                // ★ مفتاح idempotency = إعادة المحاولة آمنة (درس 5.2.5)
                using var request = new HttpRequestMessage(HttpMethod.Post, "/v1/charges")
                {
                    Content = JsonContent.Create(new { order_id = orderId, amount_minor = amount.MinorUnits,
                                                       currency = amount.Currency }),
                };
                request.Headers.Add("Idempotency-Key", idempotencyKey);

                var response = await http.SendAsync(request, token);
                response.EnsureSuccessStatusCode();
                return await response.Content.ReadFromJsonAsync<ChargeResult>(cancellationToken: token)
                       ?? throw new InvalidOperationException("رد فارغ من بوابة الدفع");
            }, ct);
        }
        catch (BrokenCircuitException ex)                       // ✓ الدائرة مفتوحة: فشل سريع صريح
        {
            log.LogWarning(ex, "payments circuit open — shedding request for {OrderId}", orderId);
            Metrics.ShedRequests.Add(1, new("dependency", "payments"));
            throw new DependencyUnavailableException("payments");       // → 503 + Retry-After
        }
        catch (OperationCanceledException) when (!ct.IsCancellationRequested)
        {
            throw new DependencyTimeoutException("payments");           // → 504 (لا انتظار أبدي)
        }
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "ترتيب الـpipeline: القاعدة اللي بيغلط فيها أغلب الناس",
             "md": """
**الاستراتيجيات تُنفَّذ من الخارج للداخل**، وأول واحدة تُضاف هي الأبعد عن النداء الفعلي:

```
Timeout (كلي) → Circuit Breaker → Retry → Bulkhead → Timeout (لكل محاولة) → النداء
```

- **Timeout الكلي بره الـretry**: عشان يحد **مجموع** المحاولات. لو جوه، كل محاولة لها مهلة لكن المجموع بلا سقف.
- **Circuit Breaker بره الـretry**: الدائرة بتحسب **النتيجة النهائية** للنداء. لو جوه الـretry،
  كل محاولة فاشلة هتُحسب كتير والدائرة هتفتح بسرعة مبالغ فيها.
- **Bulkhead (حد التوازي) جوه**: بيحمي الاعتماد نفسه من فيضان المحاولات.
- **Retry جوه الـtimeout الكلي**: وإلا المحاولات هتتقطع في النص عشوائيًا.

⚠ **`AddStandardResilienceHandler`** (لـHttpClient) بيستخدم ترتيب جاهز مدروس:
`TotalRequestTimeout → Retry → CircuitBreaker → PerTryTimeout → Bulkhead`. استخدمه كافتراضي،
وخصّص pipeline مخصص لما تحتاج سلوكًا مختلفًا.
"""},
            {"type": "heading", "level": 2, "text": "3) توزيع المهلات عبر الخدمات"},
            {"type": "code", "lang": "text", "filename": "docs/timeout-budget.md", "title": "ميزانية المهلات: كل طبقة أقصر من اللي فوقها", "code": r'''
العميل (متصفح/موبايل)          30s
  └─ Gateway / YARP            10s   ← RequestTimeout لكل مسار
       └─ BFF aggregation       8s   ← إجمالي التجميع
            ├─ Orders gRPC      3s   ← deadline لكل نداء
            │    └─ DB query    2s   ← CommandTimeout
            ├─ Catalog gRPC     2s
            └─ Shipping gRPC    2s

القواعد:
① كل طبقة **أقصر** من اللي فوقها (وإلا الطبقة العليا هتقطع قبل السفلية تخلص — شغل ضائع).
② اترك هامشًا للشبكة والتسلسل (~10-20%) — مش مساواة بالضبط.
③ مجموع المهلات المتوازية = أبطأ واحدة (مش المجموع) — ده سبب التجميع المتوازي.
④ المهلات المتسلسلة لازم تُجمع: 3s + 2s + 2s = 7s → لازم تكون أقل من مهلة الطبقة العليا (8s ✓).
⑤ مرّر الـdeadline عبر الخدمات (gRPC deadline / CancellationToken) — عشان الخدمة الداخلية تلغي شغلها
   لما المُنادي يلغي (بلا شغل ضائع وبلا استنزاف).
⑥ سجل كل مهلة منتهية كـmetric بوسم (الخدمة، الاعتماد) — المهلات المتزايدة أول علامة على تشبع.
'''},
            {"type": "code", "lang": "csharp", "title": "مرونة في أماكن تانية (مش HttpClient بس)", "code": r'''
// ═══ ① قاعدة البيانات: EF Core لديه إعادة محاولة مدمجة ═══
services.AddDbContext<AppDbContext>(o => o.UseNpgsql(cs, npgsql =>
{
    npgsql.EnableRetryOnFailure(
        maxRetryCount: 3,
        maxRetryDelay: TimeSpan.FromSeconds(2),
        errorCodesToAdd: ["40P01"]);          // ★ deadlock كمان (درس 3.1.2)
}));
// ⚠ مع معاملة يدوية: لازم تلفّها في execution strategy — وإلا إعادة المحاولة تفشل

// ═══ ② الرسائل: MassTransit retry + delayed redelivery (درس 5.2.1) ═══
cfg.UseMessageRetry(r => { r.Interval(3, TimeSpan.FromSeconds(1)); r.Ignore<ValidationException>(); });
cfg.UseDelayedRedelivery(r => r.Intervals(TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(5)));

// ═══ ③ gRPC: deadline لكل نداء (مش pipeline كامل) ═══
var response = await client.GetProductsAsync(request,
    deadline: DateTime.UtcNow.AddSeconds(2), cancellationToken: ct);

// ═══ ④ Redis: فشل مفتوح (fail-open) بدل pipeline (درس 3.3.1) ═══
try { return await cache.GetAsync(key); }
catch (RedisException) { return await LoadFromSourceAsync(); }        // ✓ تدهور مقصود

// ═══ ⑤ pipeline لنداء غير HTTP (أي كود) ═══
var pipeline = new ResiliencePipelineBuilder()
    .AddRetry(new RetryStrategyOptions { MaxRetryAttempts = 2, UseJitter = true })
    .AddTimeout(TimeSpan.FromSeconds(4))
    .Build();

await pipeline.ExecuteAsync(async ct => await fileStorage.UploadAsync(blob, ct), stoppingToken);

// ═══ ⑥ حماية من عاصفة إعادة المحاولة: حدود على مستوى التطبيق كمان ═══
builder.Services.AddRateLimiter(o => o.AddPolicy("per-tenant", http =>
    RateLimitPartition.GetTokenBucketLimiter(http.User.FindFirst("tenant_id")?.Value ?? "anon",
        _ => new TokenBucketRateLimiterOptions { TokenLimit = 100, ReplenishmentPeriod = TimeSpan.FromSeconds(1),
                                                   TokensPerPeriod = 20, QueueLimit = 0 })));
'''},
            {"type": "heading", "level": 2, "text": "4) الاختبار: إثبات إن المرونة شغالة"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Orders.Tests/ResilienceTests.cs", "title": "FakeTimeProvider (بلا انتظار حقيقي) + خادم يفشل", "code": r'''
// يتطلب: Microsoft.Extensions.TimeProvider.Testing (FakeTimeProvider) + Microsoft.Extensions.Resilience
public class ResilienceTests
{
    [Fact]
    public async Task Retries_twice_with_backoff_then_succeeds()
    {
        var handler = new FlakyHandler(failuresBeforeSuccess: 2);
        using var http = new HttpClient(handler);
        var pipeline = new ResiliencePipelineBuilder<HttpResponseMessage>()
            .AddRetry(new() { MaxRetryAttempts = 2, Delay = TimeSpan.FromSeconds(1),
                              BackoffType = DelayBackoffType.Constant, UseJitter = false })
            .Build();

        var response = await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/orders", ct), CancellationToken.None);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        handler.Attempts.Should().Be(3, "محاولتان فشلتا ثم نجاح");
    }

    [Fact]
    public async Task Does_not_retry_on_400()
    {
        var handler = new FlakyHandler(failuresBeforeSuccess: 99, statusCode: HttpStatusCode.BadRequest);
        using var http = new HttpClient(handler);
        var pipeline = new ResiliencePipelineBuilder<HttpResponseMessage>()
            .AddRetry(new() { MaxRetryAttempts = 3, Delay = TimeSpan.FromMilliseconds(1),
                              ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
                                  .HandleResult(r => (int)r.StatusCode >= 500) })   // ★ 5xx فقط
            .Build();

        var response = await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/orders", ct), CancellationToken.None);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        handler.Attempts.Should().Be(1, "الخطأ الدائم لا يُعاد");
    }

    [Fact]
    public async Task Circuit_opens_after_threshold_and_fails_fast()
    {
        // ★ FakeTimeProvider: نتحكم في الزمن بلا انتظار 30 ثانية حقيقية
        var time = new FakeTimeProvider();
        var handler = new FlakyHandler(failuresBeforeSuccess: 999, statusCode: HttpStatusCode.ServiceUnavailable);
        using var http = new HttpClient(handler);

        var pipeline = new ResiliencePipelineBuilder<HttpResponseMessage>()
            .AddCircuitBreaker(new()
            {
                FailureRatio = 0.5, MinimumThroughput = 4,
                SamplingDuration = TimeSpan.FromSeconds(10), BreakDuration = TimeSpan.FromSeconds(30),
                ShouldHandle = new PredicateBuilder<HttpResponseMessage>().HandleResult(r => (int)r.StatusCode >= 500),
                TimeProvider = time,                              // ✓ حقن الزمن الافتراضي
            })
            .Build();

        for (var i = 0; i < 4; i++)
            await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/x", ct), CancellationToken.None);

        var attemptsBefore = handler.Attempts;

        // ✓ الدائرة مفتوحة: النداءات تُرفض فورًا (بلا وصول للخادم)
        await Assert.ThrowsAsync<BrokenCircuitException>(async () =>
            await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/x", ct), CancellationToken.None));
        handler.Attempts.Should().Be(attemptsBefore, "لا نداءات فعلية والدائرة مفتوحة");

        // ✓ بعد مدة القطع: تجربة واحدة (half-open)
        time.Advance(TimeSpan.FromSeconds(31));
        await Assert.ThrowsAnyAsync<Exception>(async () =>
            await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/x", ct), CancellationToken.None));
        handler.Attempts.Should().Be(attemptsBefore + 1, "half-open يسمح بنداء تجريبي واحد");
    }

    [Fact]
    public async Task Timeout_cancels_the_call()
    {
        var handler = new SlowHandler(TimeSpan.FromSeconds(5));
        using var http = new HttpClient(handler);
        var pipeline = new ResiliencePipelineBuilder<HttpResponseMessage>()
            .AddTimeout(TimeSpan.FromMilliseconds(100)).Build();

        var act = async () => await pipeline.ExecuteAsync(ct => http.GetAsync("http://svc/x", ct), CancellationToken.None);

        await act.Should().ThrowAsync<TimeoutRejectedException>();
        handler.WasCancelled.Should().BeTrue("الـCancellationToken اتمرر للنداء الفعلي");
    }

    [Fact]
    public async Task Bulkhead_queues_beyond_limit()
    {
        var pipeline = new ResiliencePipelineBuilder()
            .AddConcurrencyLimiter(new ConcurrencyLimiterOptions { PermitLimit = 2, QueueLimit = 0 }).Build();

        var started = new SemaphoreSlim(0);
        var release = new TaskCompletionSource();

        var task1 = pipeline.ExecuteAsync(async ct => { started.Release(); await release.Task; }, CancellationToken.None);
        var task2 = pipeline.ExecuteAsync(async ct => { started.Release(); await release.Task; }, CancellationToken.None);
        await Task.WhenAll(started.WaitAsync(), started.WaitAsync());

        // ✓ الثالث يُرفض فورًا (QueueLimit = 0)
        var act = async () => await pipeline.ExecuteAsync(_ => ValueTask.CompletedTask, CancellationToken.None);
        await act.Should().ThrowAsync<RateLimitRejectedException>();

        release.SetResult();
        await Task.WhenAll(task1, task2);
    }

    private sealed class FlakyHandler(int failuresBeforeSuccess, HttpStatusCode statusCode = HttpStatusCode.ServiceUnavailable)
        : HttpMessageHandler
    {
        public int Attempts;
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct) =>
            Task.FromResult(++Attempts <= failuresBeforeSuccess
                ? new HttpResponseMessage(statusCode)
                : new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{}") });
    }

    private sealed class SlowHandler(TimeSpan delay) : HttpMessageHandler
    {
        public bool WasCancelled;
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct)
        {
            try { await Task.Delay(delay, ct); } catch (OperationCanceledException) { WasCancelled = true; throw; }
            return new HttpResponseMessage(HttpStatusCode.OK);
        }
    }
}
'''},
            {"type": "callout", "kind": "danger", "title": "9 أخطاء مرونة بتسبب أعطال أكبر من اللي بتحله",
             "md": """
1. **إعادة محاولة نداءات غير idempotent** (POST خصم مبلغ) → أثر مضاعف. الحل: idempotency key (درس 5.2.5).
2. **إعادة محاولة 4xx** → مضيعة وقت + تضخيم حمل على خدمة بتقول «طلبك غلط».
3. **retry متداخل في طبقتين** (client 3 × gateway 3 = 9 محاولات) → تضخيم أُسّي. حدد **مسؤولية واحدة** لكل طبقة.
4. **بلا jitter** → كل العملاء يعيدون المحاولة في نفس اللحظة (thundering herd).
5. **Circuit breaker بلا `MinimumThroughput`** → يفتح بعد فشلين في حركة منخفضة ويعطل الخدمة بلا سبب.
6. **مهلة أطول من مهلة المُنادي** → شغل ضائع (المُنادي قطع أصلًا).
7. **Fallback صامت** → المستخدم يشوف بيانات قديمة/صفر وهو فاكر إنها حقيقية. أعلن التدهور (header/metric/log).
8. **بلا مقاييس** (retries، breaker state، timeouts) → ما تعرفش إن المرونة شغالة أو بتخفي مشكلة.
9. **مرونة على كل حاجة** (حتى قواعد البيانات المحلية والكاش) → تعقيد بلا فائدة. طبّقها على **الاعتمادات الخارجية والشبكة**.
"""},
            {"type": "checkpoints", "items": [
                "أصنّف الفشل (عابر/دائم) وأختار الاستراتيجية المناسبة — ولا أعيد محاولة 4xx أو كتابات غير idempotent.",
                "أرتب الـpipeline صح (timeout كلي → breaker → retry → bulkhead) وأعرف أثر الترتيب.",
                "أوزع المهلات عبر الطبقات (كل طبقة أقصر من اللي فوقها) وأمرر الإلغاء/deadline.",
                "أختبر المرونة بـ`FakeTimeProvider` وhandlers تفشل/تتباطأ، وأنشر مقاييس لكل استراتيجية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه Circuit Breaker يُضاف **قبل** (خارج) Retry في الـpipeline؟",
                 "options": [
                     "للأداء",
                     "عشان يحسب النتيجة النهائية للنداء؛ لو كان داخل الـretry، كل محاولة فاشلة تُحسب منفصلة والدائرة تفتح أسرع من اللازم",
                     "مطلب Polly",
                     "بلا فرق",
                 ], "answer": 1,
                 "explain": "الترتيب: Timeout كلي → Breaker → Retry → Bulkhead → Timeout لكل محاولة → النداء. تغيير الترتيب يغير السلوك جذريًا."},
                {"q": "خدمة رجعت 409 Conflict. تعمل retry؟",
                 "options": [
                     "نعم (خطأ خادم)",
                     "لا — خطأ دائم/منطقي: إعادة المحاولة لن تغير النتيجة وتزيد الحمل",
                     "نعم مع jitter",
                     "يعتمد على الوسيط",
                 ], "answer": 1,
                 "explain": "أعد المحاولة للأخطاء العابرة فقط: timeouts، 408، 429 (مع احترام Retry-After)، و5xx."},
                {"q": "`MinimumThroughput = 10` في إعدادات الـbreaker معناها…",
                 "options": [
                     "حد أدنى للطلبات في الخدمة",
                     "لا يُحسب FailureRatio إلا بعد 10 نداءات على الأقل في فترة العينة — يمنع الفتح من فشلين في حركة منخفضة",
                     "10 محاولات إعادة",
                     "حد التوازي",
                 ], "answer": 1,
                 "explain": "بلا الحد الأدنى: حركة خفيفة + فشلين = دائرة مفتوحة وخدمة معطلة بلا سبب حقيقي."},
                {"q": "ليه jitter مهم في الـbackoff؟",
                 "options": [
                     "للأمان",
                     "بلاه، كل العملاء اللى فشلوا في نفس اللحظة يعيدون المحاولة معًا → عاصفة تضرب الخدمة وهي بتحاول تتعافى",
                     "يقلل عدد المحاولات",
                     "مطلب HTTP",
                 ], "answer": 1,
                 "explain": "jitter بيفرق لحظات إعادة المحاولة. `UseJitter = true` في Polly v8 بيعمله جاهزًا."},
                {"q": "عندك retry في HttpClient وretry في الـgateway. المشكلة؟",
                 "options": [
                     "لا مشكلة",
                     "تضخيم أُسّي (3 × 3 = 9 محاولات) وزمن استجابة أطول من مهلة العميل — حدد مسؤولية المرونة لطبقة واحدة",
                     "أداء أفضل",
                     "تعقيد كود فقط",
                 ], "answer": 1,
                 "explain": "القاعدة: المرونة أقرب ما يمكن للاعتماد (العميل)، والطبقات الأعلى تكتفي بمهلة كلية وfallback."},
                {"q": "Fallback رجّع بيانات كاش عمرها 10 دقائق. التصرف الصحيح؟",
                 "options": [
                     "عادي، المستخدم مش هيلاحظ",
                     "أعلن التدهور صراحة (header/metric/log، وعلامة في الواجهة لو مؤثرة) — خاصة لو البيانات مالية أو حرجة",
                     "امنع الـfallback",
                     "زد الـTTL",
                 ], "answer": 1,
                 "explain": "التدهور الصامت بيخلي المستخدمين ياخدوا قرارات على بيانات غلط، وبيخلي الفريق يفتكر إن كل شيء سليم."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "pipelines مرونة لثلاثة اعتمادات",
                 "md": "عرّف 3 خطوط مرونة مختلفة لـ3 اعتمادات في مشروعك (خدمة خارجية للكتابة، خدمة داخلية للقراءة، تخزين/وسيط) — كل واحد باستراتيجيات ومعاملات مبررة، وطبّقها على الـtyped clients.",
                 "criteria": [
                     "3 pipelines بأسماء مسجلة (named) + مبرر مكتوب لكل معامل (عدد المحاولات، النسب، المهلات)",
                     "ترتيب صحيح (timeout كلي → breaker → retry → bulkhead) مع تعليق يشرح الترتيب",
                     "`ShouldHandle` يستثني 4xx صراحة (اختبار يثبت عدم إعادة المحاولة)",
                     "مفتاح idempotency في أي pipeline لكتابة غير idempotent",
                     "مقاييس: عدد المحاولات، حالات الدائرة، المهلات المنتهية، الطلبات المرفوضة",
                     "≥ 5 اختبارات بـ`FakeTimeProvider` وhandlers تفشل/تتباطأ",
                 ],
                 "hint": "لو اختبار الدائرة بطيء: حقن `TimeProvider = fakeTime` في `CircuitBreakerStrategyOptions` و`time.Advance(...)` بدل `Task.Delay`."},
                {"id": "t2", "title": "ميزانية مهلات + اختبار تشبع",
                 "md": "ارسم ميزانية المهلات لنظامك (من العميل للقاعدة) وتحقق إن كل طبقة أقصر من اللي فوقها، ثم شغّل اختبار تشبع يثبت إن النظام يفشل «بأدب» (503/429 سريعة) بدل ما يعلّق.",
                 "criteria": [
                     "جدول ميزانية المهلات (6 طبقات على الأقل) مع الهوامش مبررة",
                     "لا مهلة أطول من مهلة مناديها (فحص موثق)",
                     "deadline/CancellationToken يُمرر عبر الخدمات (بلا شغل ضائع — اختبار إلغاء)",
                     "اختبار تشبع: عند فشل الاعتماد، الاستجابة 503/504 خلال مهلة محددة (مش تعليق)",
                     "توثيق سلوك التدهور: أنهي الأقسام بتُعلن تدهور وأنهي بتفشل",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET Resilience (Microsoft.Extensions.Resilience)", "url": "https://learn.microsoft.com/dotnet/core/resilience/"},
                {"label": "HTTP resilience with Standard Resilience Handler", "url": "https://learn.microsoft.com/dotnet/core/resilience/http-resilience"},
                {"label": "Polly v8 documentation", "url": "https://www.pollydocs.org/"},
                {"label": "Circuit Breaker pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker"},
                {"label": "Bulkhead pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/bulkhead"},
                {"label": "Throttling & Load shedding", "url": "https://learn.microsoft.com/azure/architecture/patterns/throttling"},
                {"label": "Testing with FakeTimeProvider", "url": "https://learn.microsoft.com/dotnet/core/testing/time-abstraction"},
            ]},
        ],
    },
]
