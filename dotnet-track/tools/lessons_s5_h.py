"""Stage 5, Module 4 — Capstone: 3 services + RabbitMQ + Aspire."""

TODAY = "2026-10-22"

LESSONS_S5_H = [
    {
        "id": "s5-m4-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "callout", "kind": "goal", "title": "مشروع المرحلة 5 — نظام طلبات موزّع (6 ساعات)",
             "md": """
**المطلوب**: نظام من **3 خدمات + gateway** تتواصل بالأحداث عبر RabbitMQ، منسّقة بـ**.NET Aspire**،
مع **Outbox** و**Saga** و**Resilience** و**Idempotency** — والأهم: **تثبت بالأدلة إن الأحداث ما بتضيعش
لما خدمة تقع**، وتوثّق مخطط النظام وتدفق الأحداث.

**المعيار الحقيقي للنجاح** مش إن النظام يشتغل وهو سعيد — بل إن **سلوكه تحت الفشل معروف ومُثبت ومُقاس**.
كل جلسة ليها **دليل** (كود/مخرجات/لقطة/مقياس). بلا دليل = الجلسة ما اتعملتش.
"""},
            {"type": "text", "md": """
المشروع ده بيجمع كل حاجة من المرحلة 5 (ودروس من 2 و3 و4):
تقسيم الخدمات وعقودها (5.1) · الأحداث والوسيط (5.2.1) · Sagas والاتساق النهائي (5.2.3) ·
Resilience وميزانية المهلة (5.2.4) · Idempotency (5.2.5) · Aspire وdiscovery (5.3.1) ·
التشخيص باللوحة (5.3.2) · اختبار موزّع وعقود (5.3.3) · الأنماط (5.3.4) — كلها في نظام واحد قابل للتشغيل.
"""},
            {"type": "heading", "level": 2, "text": "1) النظام المطلوب (المخطط وتدفق الأحداث)"},
            {"type": "code", "lang": "text", "filename": "docs/system-map.md", "title": "المخطط اللي لازم ترسمه وتشرحه بصوتك في 3 دقايق", "code": r'''
                          ┌──────────────────────────────┐
       متصفح/عميل  ──────▶ │  Shop.Gateway (YARP + BFF)   │  ◀── rate limit لكل مستأجر
                          │  · routes/clusters بالاسم     │      (per-tenant + burst + global)
                          │  · timeout budget             │
                          └───────┬───────────────┬──────┘
                     https+http://orders     https+http://catalog
                                  │               │
              ┌───────────────────▼───┐       ┌───▼─────────────────────┐
              │  Shop.Orders (API)     │       │  Shop.Catalog (API)     │
              │  · POST /api/orders    │       │  · GET /api/products/{id}│
              │  · Order aggregate     │       │  · stock                │
              │  · EF Core + Outbox    │       │  · cache-aside (Hybrid) │
              │  · Saga (state machine)│       └───────────┬─────────────┘
              └───────┬───────────────────────┬────────────┘
                      │ ConnectionStrings__shopdb        │ ConnectionStrings__rabbit
             ┌────────▼─────────┐                        │
             │  PostgreSQL      │              ┌─────────▼──────────────────────────────┐
             │  · orders.orders │              │  RabbitMQ (definitions.json as code)    │
             │  · orders.outbox │              │  · shop.events (topic)                  │
             │  · payments.*    │              │  · order-placed / payment-captured      │
             │  · *_sagas       │              │  · *_error (DLQ) + policies (quorum,TTL)│
             └────────▲─────────┘              └────┬───────────────────┬────────────────┘
                      │                             │                   │
         ┌────────────┴──────────────┐   ┌──────────▼─────────┐  ┌──────▼──────────────────┐
         │  Shop.Payments (worker)   │   │ Shop.Notifications │  │  Redis (cache)          │
         │  · consumes order-placed  │   │ · consumes         │  │  · catalog L2           │
         │  · idempotent capture     │   │   payment-captured │  │  · dedup keys           │
         │  · publishes result       │   │ · sends (fake)     │  └─────────────────────────┘
         └───────────────────────────┘   └────────────────────┘

  كل الخدمات: Shop.ServiceDefaults (OTel → لوحة Aspire · /health + /alive · discovery · resilience)
  التدفق: POST /api/orders → (معاملة واحدة: Order + Outbox) → dispatcher → RabbitMQ
          → Payments (capture) → payment-captured → Saga → Notifications
          → (فشل الدفع) → payment-failed → Saga: CancelShipment/ReleaseStock → order-cancelled

  ★ قواعد النظام (لا تتجاوزها):
   ① لا نداء متزامن بين الخدمات داخل تدفق الكتابة — الأحداث فقط (النداء المتزامن مسموح للقراءة: orders→catalog)
   ② كل كتابة لأحداث داخل معاملة DB واحدة مع Outbox
   ③ كل مستهلك idempotent (قيد فريد أو inbox)
   ④ كل timeout في النظام موجود في docs/timeout-budget.md
   ⑤ كل قرار معماري له ADR
'''},
            {"type": "table", "head": ["داخل نطاق المشروع", "بره النطاق (وليه)"], "rows": [
                ["3 خدمات + gateway + worker إشعارات", "أكثر من 5 خدمات — هتغرق في التنسيق بدل التعلم"],
                ["RabbitMQ + MassTransit + Outbox + Saga", "Kafka/Service Bus (درس 5.2.2 غطاهم نظريًا + abstraction)"],
                ["Aspire AppHost + لوحة للتشخيص", "Kubernetes/Namespace (المرحلة 7)"],
                ["Resilience + bulkhead + throttling", "Service mesh/Istio — تعقيد بلا حاجة في نطاق المشروع"],
                ["اختبار موزّع (Aspire) + عقود (Pact أو snapshot)", "اختبار حمل كامل/أداء (المرحلة 6)"],
                ["Postgres + EF Core + Redis للـcache", "قواعد NoSQL إضافية (درس 3.3.6)"],
                ["مصادقة بسيطة (JWT) لو محتاجها gateway", "Identity كامل/SSO (المرحلة 2)"],
                ["توثيق: مخطط + تدفق أحداث + ADRs + CAPSTONE.md", "واجهة أمامية غنية — API فقط + صفحة فحص بسيطة"],
            ]},
            {"type": "heading", "level": 2, "text": "2) الجلسات السبع (كل واحدة بدليل)"},
            {"type": "steps", "title": "360 دقيقة = 7 جلسات · نفّذ بالترتيب", "items": [
                {"title": "جلسة 1 (45د): الهيكل يشتغل — AppHost + 4 موارد صحية",
                 "md": "أنشئ `Shop.AppHost` + `Shop.ServiceDefaults`، وأضف Postgres (`shopdb`) وRedis (`cache`) وRabbitMQ (`rabbit` بـ`definitions.json`)، و4 مشاريع (catalog/orders/payments/notifications) + gateway. كل خدمة: `AddServiceDefaults()` + `MapDefaultEndpoints()` + `WithHttpHealthCheck(\"/health\")` في AppHost + `WaitFor` لكل اعتماد. **الدليل**: أمر واحد يشغّل الكل، واللوحة بتعرض كل الموارد **Healthy**، و`curl /health` بيرد 200 من كل خدمة.",
                 "code": "# أمر واحد — وكل الموارد خضرا في اللوحة\ndotnet run --project src/Shop.AppHost\n\n# الدليل: صحة كل خدمة — المنفذ من لوحة Aspire (تبويب Resources → endpoint المورد)\n# (المنافذ عشوائية محليًا عن قصد؛ خدها من اللوحة أو من services__<name>__https__0)\ncurl -s -o /dev/null -w 'catalog       %{http_code}\\n' http://localhost:<PORT>/health\ncurl -s -o /dev/null -w 'orders        %{http_code}\\n' http://localhost:<PORT>/health\ncurl -s -o /dev/null -w 'gateway       %{http_code}\\n' http://localhost:<PORT>/health\ncurl -s -o /dev/null -w 'notifications %{http_code}\\n' http://localhost:<PORT>/alive\n\n# الدليل: الوسيط جاهز بالبنية المعلنة ككود\ndocker exec shop-rabbit rabbitmqctl list_exchanges name type | grep shop.events\ndocker exec shop-rabbit rabbitmqctl list_queues name type messages consumers"},
                {"title": "جلسة 2 (50د): العقود + Orders API + Outbox",
                 "md": "عرّف الأحداث/الأوامر في `Shop.Contracts` (records + `SchemaVersion` + مبالغ بـminor units). في Orders: `Order` aggregate بقواعد (درس 4.2.1)، `POST /api/orders` بيكتب **الطلب + رسالة Outbox في معاملة واحدة**، وdispatcher بيفرغ الـOutbox (درس 4.2.3). **الدليل**: اختبار slice بيثبت إن فشل الوسيط **ما بيمنعش** إنشاء الطلب، وصف في `orders.outbox_messages` بحالة `Pending` ثم `Dispatched`، ولقطة من اللوحة للـtrace بتاع الطلب.",
                 "code": "-- الدليل: الحدث اتكتب في نفس معاملة الطلب (بلا نشر مباشر)\nSELECT id, event_type, status, retry_count, available_at, created_at, dispatched_at\nFROM orders.outbox_messages\nORDER BY created_at DESC LIMIT 10;\n\n-- الدليل: مفيش أحداث ضايعة (العدد = عدد الطلبات)\nSELECT (SELECT COUNT(*) FROM orders.orders)  AS orders_count,\n       (SELECT COUNT(*) FROM orders.outbox_messages WHERE event_type = 'order-placed') AS events_count;"},
                {"title": "جلسة 3 (50د): Payments worker — استهلاك idempotent ونشر النتيجة",
                 "md": "مستهلك `OrderPlaced` في Payments: يتحقق من الـinbox/قيد فريد (درس 5.2.5)، ينفّذ `Capture` (محاكاة بوابة خارجية مع `ResiliencePipeline` مسمّى)، يكتب `payments.charges`، وينشر `PaymentCaptured` أو `PaymentFailed` عبر Outbox بتاعه. **الدليل**: اختبار Aspire موزّع بيثبت التدفق من HTTP لصف في `payments.charges` خلال 30 ثانية بـpolling، واختبار تكرار الرسالة **مرتين** بينتج charge **واحد**.",
                 "code": "-- الدليل: charge واحد لكل طلب حتى مع تكرار التسليم\nSELECT order_id, COUNT(*) AS charges\nFROM payments.charges GROUP BY order_id HAVING COUNT(*) > 1;   -- ← لازم يرجع 0 صفوف\n\n-- الدليل: الـinbox شغال\nSELECT message_id, consumed_at FROM payments.inbox_messages ORDER BY consumed_at DESC LIMIT 5;\n\n-- الدليل: الطوابير بتفضى (مفيش تكدس)\ndocker exec shop-rabbit rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers"},
                {"title": "جلسة 4 (50د): Saga + Notifications — التناسق النهائي والتعويض",
                 "md": "نفّذ `OrderFulfillmentStateMachine` (درس 5.2.3) في Orders: `AwaitingPayment → AwaitingShipment → Completed`، ومع `PaymentFailed` → `Compensating` → `OrderCancelled` (+ `ReleaseStock` عند Catalog). وNotifications يستهلك `PaymentCaptured`/`OrderCancelled` ويبعت إشعار (محاكاة). **الدليل**: استعلامات `db/saga-monitoring.sql` بتوضح توزيع الحالات، واختبار **مسار التعويض** بيثبت إن فشل الدفع بينتهي بـ`Cancelled` + release، واختبار timeout بيثبت إن saga علق > 15 دقيقة بيتحوّل `NeedsManual`.",
                 "code": "-- الدليل: حالات الـsagas (ما فيش saga عالق بلا سبب)\nSELECT current_state, COUNT(*) FROM orders.order_fulfillment_sagas GROUP BY current_state;\n\n-- الدليل: التعويض تم بالترتيب الصحيح (من اللوجات + الـtrace)\nSELECT s.order_id, s.current_state, s.updated_at, o.status\nFROM orders.order_fulfillment_sagas s JOIN orders.orders o ON o.id = s.order_id\nWHERE s.current_state IN ('Compensating','NeedsManual','Cancelled');"},
                {"title": "جلسة 5 (45د): Gateway (YARP) + Resilience + Bulkhead/Throttling",
                 "md": "YARP بـclusters **بالأسماء** عبر `AddServiceDiscoveryDestinationResolver()` + transforms (correlation id) + health checks للـclusters (درس 5.1.4). أضف throttling لكل مستأجر (429 + `Retry-After`)، وbulkhead لكل مستأجر، وpipelines resilience لكل تابع خارجي مع fallback مُعلَن (`X-Degraded`)، وطبّق `docs/timeout-budget.md` على كل الطبقات. **الدليل**: طلب عبر الـgateway بيرد 201، وطلب بلا مفتاح مستأجر بيتقاسم الحد، و**إثبات عملي**: إيقاف catalog → orders/gateway بيردوا 200 مع `X-Degraded` (مش 5xx).",
                 "code": "# الدليل: 429 مع Retry-After عند تجاوز المعدل\nfor i in $(seq 1 140); do\n  curl -s -o /dev/null -w '%{http_code} ' -H 'X-Tenant-Id: t1' http://localhost:8080/api/catalog/products\ndone; echo\ncurl -s -D - -H 'X-Tenant-Id: t1' http://localhost:8080/api/catalog/products | grep -iE 'HTTP/|retry-after|problem'\n\n# الدليل: degradation مُعلن عند وقوع التابع (أوقف catalog من اللوحة ثم):\ncurl -s -D - http://localhost:8080/api/orders/availability/42 | grep -iE 'HTTP/|x-degraded'"},
                {"title": "جلسة 6 (60د): ★ إثبات المتانة — 8 سيناريوهات فشل",
                 "md": "دي أهم جلسة. لكل سيناريو: توقّع مكتوب **قبل** التنفيذ، تنفيذ، ملاحظة (مخرجات/لقطة/مقياس)، ثم **حكم**: نجح/فشل + السبب + الإصلاح. السيناريوهات في الجدول تحت. نفّذ 5 منها آليًا (اختبارات Aspire/slice) و3 يدويًا (docker stop / حقن عطل) — وسجّل كل حاجة في `docs/reliability-evidence.md`.",
                 "code": "# ① إيقاف مستهلك (payments) ثم إنشاء طلب ثم إعادة التشغيل\ndocker stop shop-payments           # أو أوقف المورد من لوحة Aspire\ncurl -s -X POST http://localhost:8080/api/orders -H 'content-type: application/json' -d @order.json\nSELECT status FROM orders.outbox_messages ORDER BY created_at DESC LIMIT 1;   -- ← Pending/Dispatched، الطلب اتعمل\ndocker start shop-payments\n#   التوقّع: بعد الإقلاع، الرسالة تتعالج (retry/redelivery) → charge واحد، saga → Completed\n\n# ② رسالة سامة (payload غلط) → الطابور الميت\ndocker exec shop-rabbit rabbitmqctl list_queues name messages | grep _error\n\n# ③ قطع الوسيط تمامًا أثناء النشر → Outbox بيحتفظ والـdispatcher بيعيد\niptables -A OUTPUT -p tcp --dport 5672 -j DROP   # (أو أوقف container الـrabbit)\n#   التوقّع: إنشاء الطلب يفشل بوضوح **أو** ينجح مع رسالة Pending — المهم: بلا فقدان صامت"},
                {"title": "جلسة 7 (60د): التوثيق والتسليم",
                 "md": "أكمل `docs/system-map.md` (المخطط + تدفق الأحداث)، `docs/events.md` (جدول الأحداث: الناشر × المستهلكين × الحقول × التوافق)، `docs/timeout-budget.md`، 5 ADRs على الأقل، `docs/reliability-evidence.md` (جدول السيناريوهات)، و`CAPSTONE.md`. أضف CI بـ3 jobs (fast/contracts/integration) واشتغله مرة أخضر. سجّل **مقطع 3 دقايق** تشرح فيه النظام وتدفق الأحداث وسلوك الفشل (ده اللي هتقوله في المقابلة).",
                 "code": "# الدليل الأخير: كل حاجة خضرا من الصفر\ngit clean -xdf && dotnet restore && dotnet build -c Release /warnaserror\ndotnet test --filter \"Category=Unit|Category=Slice\"          # سريع\ndotnet test --filter \"Category=Contract\"                     # عقود\ndotnet test tests/Shop.SystemTests --filter \"Category=Integration\"   # موزّع (Docker)\n\n# وعدد الأدلة المُجمعة\ngrep -c '^| ' docs/reliability-evidence.md\nls docs/adr/ | wc -l     # ≥ 5"}]},
            {"type": "heading", "level": 2, "text": "3) ★ إثبات عدم فقدان الأحداث (الهدف الأساسي)"},
            {"type": "table", "head": ["#", "السيناريو", "التوقّع (اكتبه قبل التنفيذ)", "الدليل المقاس", "آلي/يدوي"], "rows": [
                ["1", "مستهلك Payments واقع وقت النشر", "الطلب يُنشأ، والحدث يفضل في Outbox/الطابور، ويُعالَج بعد الإقلاع — **charge واحد**", "صف Outbox + عدد charges = 1 + saga = Completed", "يدوي (`docker stop`) + آلي (fault flag)"],
                ["2", "الوسيط (RabbitMQ) واقع وقت النشر", "إما إنشاء الطلب يفشل بوضوح (503) أو ينجح مع رسالة `Pending` يُعاد إرسالها — **بلا فقدان صامت**", "حالة Outbox + استجابة HTTP + لوج الـdispatcher", "يدوي (stop container)"],
                ["3", "تسليم مكرر (redelivery) لحدث `order-placed`", "المستهلك يعالج مرة واحدة (inbox/قيد فريد) — **charge واحد**", "استعلام `HAVING COUNT(*) > 1` يرجع 0 صفوف", "آلي (اختبار)"],
                ["4", "رسالة سامة (JSON غلط/حقل ناقص)", "بعد محاولات محدودة → طابور `_error` + مقياس + **بلا إعادة لا نهائية** وبلا تعطيل الطابور", "`list_queues` فيه `_error` + `messages.failed` counter", "آلي (TestHarness)"],
                ["5", "فشل بوابة الدفع (500/timeout)", "`PaymentFailed` → Saga → تعويض (ReleaseStock + OrderCancelled) — **حالة نهائية متناسقة**", "حالة الـsaga + حالة الطلب + لوج التعويض بالترتيب", "آلي (اختبار)"],
                ["6", "فشل خطوة التعويض نفسها", "Saga → `NeedsManual` + إنذار + **بلا حلقة تعويض لا نهائية**", "صف NeedsManual + مقياس + (اختياري) إيميل/لوج Error", "آلي (اختبار)"],
                ["7", "timeout: لا رد من الدفع خلال 10 دقايق", "الـsaga timeout بيطلق `CancelShipment`/إلغاء — **بلا saga عالق للأبد**", "حالة بعد تقدم الوقت (`FakeTimeProvider`) أو انتظار حقيقي مُقلَّص", "آلي (اختبار)"],
                ["8", "تجاوز مستأجر للمعدل/التزامن", "429 + `Retry-After` للمستأجر المسيء، **وباقي المستأجرين غير متأثرين** (p95 ثابت)", "مقياس rejections + p95 لمستأجر تاني أثناء الهجوم", "آلي (k6/50 طلب متزامن)"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.SystemTests/NoEventLossTests.cs", "title": "أهم 3 اختبارات في المشروع (اكتبهم قبل السيناريوهات اليدوية)", "code": r'''
[Collection("ShopSystem")]
[Trait("Category", Categories.Integration)]
public class NoEventLossTests(ShopAppFixture app, ITestOutputHelper output)
{
    private static readonly Guid ProductId = Guid.Parse("11111111-1111-1111-1111-111111111111");

    /// <summary>
    /// ★ السيناريو 1 و3 معًا: المستهلك معطّل في أول محاولتين (fault injection)،
    /// والحدث يُسلَّم أكثر من مرة. النتيجة المطلوبة: charge **واحد** وحالة نهائية صحيحة.
    /// </summary>
    [Fact]
    public async Task When_payments_consumer_fails_then_event_is_not_lost_and_processed_once()
    {
        var orderId = Guid.NewGuid();

        // ✓ حقن العطل عبر تكوين الخدمة (Development/test only) — أول محاولتين يفشلوا
        await app.Payments.PostAsJsonAsync("/api/test/faults/fail-next-captures", new { count = 2 });

        var placed = await app.Orders.PostAsJsonAsync("/api/orders", new
        {
            order_id = orderId,
            lines = new[] { new { product_id = ProductId, quantity = 1, unit_price_minor = 2500L } },
        });
        placed.StatusCode.ShouldBe(HttpStatusCode.Created);

        // ★ polling حتى الأثر — لا Task.Delay ثابت
        var charge = await WaitUntilAsync(() => GetChargeCountAsync(orderId), c => c == 1,
            timeout: TimeSpan.FromSeconds(60), poll: TimeSpan.FromMilliseconds(300));

        charge.ShouldBe(1, "الحدث ما ضاعش رغم فشل المعالج — واتعالج **مرة واحدة** رغم إعادة التسليم");

        var sagaState = await GetSagaStateAsync(orderId);
        sagaState.ShouldBe("Completed");

        // ✓ وبعد 10 ثواني إضافية: مفيش charge تاني ظهر (إثبات idempotency على المدى الأطول)
        await Task.Delay(TimeSpan.FromSeconds(10));
        (await GetChargeCountAsync(orderId)).ShouldBe(1);
    }

    /// <summary>★ السيناريو 5: فشل الدفع → تعويض → حالة نهائية متناسقة.</summary>
    [Fact]
    public async Task When_payment_fails_permanently_then_saga_compensates_and_order_is_cancelled()
    {
        var orderId = Guid.NewGuid();

        // ✓ المحاولة الوحيدة تفشل فشلًا دائمًا (بطاقة مرفوضة — بلا retry)
        await app.Payments.PostAsJsonAsync("/api/test/faults/decline-order", new { order_id = orderId });

        // ★ التقط خط الأساس **قبل** الطلب — وإلا المقارنة بتقارن قيمة بنفسها (اختبار فاضي)
        var baselineStock = await GetStockAsync(ProductId);

        var placed = await app.Orders.PostAsJsonAsync("/api/orders", new
        {
            order_id = orderId,
            lines = new[] { new { product_id = ProductId, quantity = 2, unit_price_minor = 900L } },
        });
        placed.StatusCode.ShouldBe(HttpStatusCode.Created);

        (await WaitUntilAsync(() => GetSagaStateAsync(orderId), s => s is "Cancelled" or "NeedsManual",
             timeout: TimeSpan.FromSeconds(60), poll: TimeSpan.FromMilliseconds(300)))
            .ShouldBe("Cancelled");

        // ✓ التعويض شمل المخزون (ReleaseStock) — الدليل من Catalog مش من اللوجات
        (await GetStockAsync(ProductId)).ShouldBe(baselineStock, "المخزون رجع لحالته بعد التعويض");

        // ✓ ولا charge اتسجلت
        (await GetChargeCountAsync(orderId)).ShouldBe(0);
    }

    /// <summary>★ السيناريو 8: مستأجر مسيء ما يأثرش على باقي المستأجرين (bulkhead + throttling).</summary>
    [Fact]
    public async Task When_one_tenant_floods_then_other_tenants_stay_fast()
    {
        // خط الأساس: مستأجر هادئ
        var before = await MeasureP95Async("tenant-calm", requests: 20);

        // هجوم: مستأجر تاني بيبعت 200 طلب متزامن
        var flood = Enumerable.Range(0, 200).Select(_ => PostOrderAsTenantAsync(NewOrder(), "tenant-abuse"));
        var responses = await Task.WhenAll(flood);

        // ✓ جزء مرفوض بوضوح (429) — مش timeouts غامضة
        responses.Count(r => r.StatusCode == HttpStatusCode.TooManyRequests).ShouldBeGreaterThan(0);

        // والأهم: المستأجر الهادئ لسه سريع
        var during = await MeasureP95Async("tenant-calm", requests: 20);
        during.ShouldBeLessThan(before * 3, "العزل منع تعدّي الضرر (bulkhead/throttling لكل مستأجر)");

        output.WriteLine($"p95 before={before.TotalMilliseconds:F0}ms during={during.TotalMilliseconds:F0}ms");
    }

    // ── مساعدات (اتعرفت في درس 5.3.3) ──
    private static async Task<T> WaitUntilAsync<T>(Func<Task<T>> probe, Func<T, bool> predicate,
                                                   TimeSpan timeout, TimeSpan poll)
    {
        var deadline = DateTime.UtcNow + timeout;
        T last = default!;
        while (DateTime.UtcNow < deadline)
        {
            last = await probe();
            if (predicate(last)) return last;
            await Task.Delay(poll);
        }
        throw new TimeoutException($"الشرط لم يتحقق خلال {timeout}. آخر قيمة: {last}");
    }

    private async Task<int> GetChargeCountAsync(Guid orderId)
    {
        await using var conn = await OpenAsync();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT COUNT(*) FROM payments.charges WHERE order_id = @orderId", new { orderId });
    }

    private async Task<string?> GetSagaStateAsync(Guid orderId)
    {
        await using var conn = await OpenAsync();
        return await conn.ExecuteScalarAsync<string?>(
            "SELECT current_state FROM orders.order_fulfillment_sagas WHERE order_id = @orderId", new { orderId });
    }

    private async Task<int> GetStockAsync(Guid productId)
    {
        await using var conn = await OpenAsync();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT quantity FROM catalog.stock WHERE product_id = @productId", new { productId });
    }

    private async Task<TimeSpan> MeasureP95Async(string tenantId, int requests)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var durations = new List<double>();
        for (var i = 0; i < requests; i++)
        {
            var one = System.Diagnostics.Stopwatch.StartNew();
            await GetAsTenantAsync("/api/catalog/products", tenantId);
            durations.Add(one.Elapsed.TotalMilliseconds);
        }
        sw.Stop();
        durations.Sort();
        return TimeSpan.FromMilliseconds(durations[(int)(durations.Count * 0.95)]);
    }

    private async Task<Npgsql.NpgsqlConnection> OpenAsync()
    {
        var cs = await app.GetConnectionStringAsync("shopdb");
        var conn = new Npgsql.NpgsqlConnection(cs);
        await conn.OpenAsync();
        return conn;
    }

    private static object NewOrder() => new
    {
        order_id = Guid.NewGuid(),
        lines = new[] { new { product_id = ProductId, quantity = 1, unit_price_minor = 500L } },
    };

    // ★ HttpClient مفيهوش PostAsJsonAsync/GetAsync بتاخد HttpRequestMessage → نبني الطلب ونرسله بـSendAsync
    private Task<HttpResponseMessage> GetAsTenantAsync(string path, string tenantId)
    {
        var request = new HttpRequestMessage(HttpMethod.Get, path);
        request.Headers.Add("X-Tenant-Id", tenantId);
        return app.Gateway.SendAsync(request);
    }

    private Task<HttpResponseMessage> PostOrderAsTenantAsync(object order, string tenantId)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/api/orders")
        {
            Content = JsonContent.Create(order),
        };
        request.Headers.Add("X-Tenant-Id", tenantId);
        return app.Gateway.SendAsync(request);
    }
}

// ⚠ ملاحظات تنفيذ:
// ① مسارات `/api/test/faults/*` لازم تكون مقصورة على Development/Testing (درس 5.3.3) — ممنوع في الإنتاج.
// ② `X-Tenant-Id` هنا مبسّط للتجربة؛ في الإنتاج المستأجر بييجي من التوكن (claim) مش من رأس قابل للتزوير.
// ③ خط الأساس (baselineStock) يُلتقط **قبل** أول طلب في الاختبار — مش وقت الـassertion.
// ④ Dapper: `ExecuteScalarAsync<int>` يحتاج `using Dapper;`
// ⑤ لو عدة اختبارات بتشارك حالة بيانات: التقط خطوط الأساس في `InitializeAsync` (درس 5.3.3).
'''},
            {"type": "heading", "level": 2, "text": "4) تعريف «خلصت» — 22 بندًا بدليل"},
            {"type": "table", "head": ["#", "البند", "الدليل المقبول"], "rows": [
                ["1", "أمر واحد يشغّل النظام كله (بلا docker-compose يدوي)", "`dotnet run --project src/Shop.AppHost` + لقطة اللوحة وكل الموارد Healthy"],
                ["2", "4 خدمات + gateway كلها `AddServiceDefaults()` + `/health` + `/alive`", "`curl` لكل خدمة + لقطة تبويب Resources"],
                ["3", "كل النداءات بين الخدمات بالاسم (discovery) — مفيش `localhost:port`", "`git grep -n \"localhost:[0-9]\" src/` يرجع نتائج صفر (عدا fallback موثق)"],
                ["4", "RabbitMQ ببنية معلنة ككود (exchanges/queues/policies)", "`definitions.json` + مخرجات `rabbitmqctl list_exchanges/list_queues/list_bindings`"],
                ["5", "العقود في مشروع مشترك (records + `SchemaVersion` + minor units)", "كود `Shop.Contracts` + جدول في `docs/events.md`"],
                ["6", "كل كتابة أحداث داخل معاملة DB مع Outbox", "كود + استعلام يثبت العدد (orders = events) + اختبار slice لفشل الوسيط"],
                ["7", "كل مستهلك idempotent (inbox أو قيد فريد)", "اختبار تكرار التسليم + استعلام `HAVING COUNT(*) > 1` = 0 صفوف"],
                ["8", "Saga بحالات وانتقالات وتعويض و3 timeouts", "`OrderFulfillmentStateMachine` + `db/saga-monitoring.sql` + نتائج الاستعلامات"],
                ["9", "مسار التعويض يشتغل (فشل دفع → إلغاء + ReleaseStock)", "اختبار `When_payment_fails_permanently…` أخضر"],
                ["10", "فشل التعويض → `NeedsManual` + إنذار (بلا حلقة لا نهائية)", "اختبار + مقياس + لوج Error"],
                ["11", "Resilience pipeline لكل تابع خارجي (retry+breaker+timeout+bulkhead)", "الكود + 5 اختبارات بـ`FakeTimeProvider` (درس 5.2.4)"],
                ["12", "`docs/timeout-budget.md` يغطي كل الطبقات (client→gateway→service→DB→broker)", "ملف + جدول + تحقق إن كل رقم موجود في الكود"],
                ["13", "Throttling لكل مستأجر + 429 + `Retry-After` + problem+json", "مخرجات curl (رؤوس) + اختبار"],
                ["14", "Bulkhead لكل مستأجر + رفض سريع", "اختبار `When_one_tenant_floods…` أخضر بأرقام p95"],
                ["15", "Cache-aside في Catalog (وسوم إبطال + TTL+jitter + fail-open)", "اختبار: أوقف Redis → الخدمة ترد (أبطأ) + مقياس hit/miss"],
                ["16", "Gateway بـYARP: routes/clusters/health/transforms + BFF aggregator", "`appsettings.json` + اختبار عبر الـgateway + `X-Correlation-Id` في الرد"],
                ["17", "5 سيناريوهات فشل على الأقل مثبتة (جدول الأدلة)", "`docs/reliability-evidence.md` بمخرجات/لقطات لكل سيناريو"],
                ["18", "اختبارات: unit + slice + contract + distributed integration (Aspire)", "مخرجات `dotnet test` لكل فئة + عدد الاختبارات"],
                ["19", "CI بـ3 jobs (fast/contracts/integration) أخضر", "رابط/لقطة من GitHub Actions + `timeout-minutes` ظاهر"],
                ["20", "5 ADRs على الأقل (قرارات حقيقية ببدائل مرفوضة)", "`ls docs/adr/` + محتوى كل ملف فيه سياق رقمي"],
                ["21", "`CAPSTONE.md` + مخطط النظام + جدول الأحداث", "الملف + `docs/system-map.md` + `docs/events.md`"],
                ["22", "مقطع/سكريبت 3 دقايق تشرح النظام والفشل", "سكريبت مكتوب (ومقطع اختياري) + تدريب مرة بصوت عالي"],
            ]},
            {"type": "callout", "kind": "danger", "title": "10 طرق بتفشل بيها مشاريع المرحلة دي",
             "md": """
1. **البدء بالـgateway أو بالواجهة** — ابدأ بتدفق واحد من طرف لطرف (orders → outbox → rabbit → payments)،
   وبعدين زوّد. «كل حاجة ناقصة شوية» = مفيش حاجة خلصت.
2. **نشر مباشر بلا Outbox** — أول ما تقفل DB أو الوسيط هتفقد أحداث، ومش هتعرف. (الهدف الأساسي من المشروع!)
3. **مستهلك بلا idempotency** — الاختبارات خضرا، وفي الإنتاج كل إعادة تسليم تعمل charge تاني.
4. **Saga بلا timeouts** — هتوصل لحالات «عالقة للأبد» ومش هتعرف تفرق بينها وبين اللي لسه شغالة.
5. **Timeouts عشوائية** — timeout العميل أكبر من timeout الخادم = العميل يستنى بعد ما الخادم استسلم.
   اكتب `timeout-budget.md` **قبل** الكود.
6. **retry في كل طبقة** — retry في العميل + في الـHttpClient + في MassTransit + في EF = 27 محاولة فعلية.
   حدّد طبقة واحدة للمحاولة (درس 5.2.4).
7. **اختبارات بتعتمد على `Task.Delay` واللوجات** — flaky من اليوم الأول، وبعد أسبوع محدش بيثق فيها.
8. **مفيش أدلة** — «النظام شغال» مش دليل. كل بند في جدول الـDoD محتاج مخرجات/لقطة/مقياس.
9. **نطاق أكبر من 6 ساعات** — K8s + Kafka + 8 خدمات + واجهة React = مش هتخلص. التزم بالجدول.
10. **توثيق في الآخر كله مرة واحدة** — ADR بعد ما تنسى السياق بيبقى بلا قيمة. اكتبه مع القرار.

⚠ **لو ضاع الوقت**: احذف Notifications وخلي النظام خدمتين + gateway. إثبات المتانة (جلسة 6) أهم من عدد الخدمات.
"""},
            {"type": "heading", "level": 2, "text": "5) التقييم الذاتي (سجّل درجتك بصراحة)"},
            {"type": "table", "head": ["المحور", "0 — ما اتعملش", "1 — جزئي", "2 — مكتمل بدليل", "3 — مكتمل + مُقاس + موثق", "درجتي"], "rows": [
                ["التشغيل والتنسيق (Aspire)", "أوامر يدوية متعددة", "AppHost شغال بس بلا health/WaitFor", "أمر واحد + كل الموارد Healthy + discovery", "+ `WithLifetime`/volumes + توثيق أسماء الموارد في `docs/services.md`", "___ /3"],
                ["الأحداث والوسيط", "نشر مباشر", "Outbox بلا dispatcher/مقاييس", "Outbox + dispatcher + DLQ + سياسات معلنة ككود", "+ مقاييس عمق الطابور/التأخير + إنذار + اختبار فقدان وسيط", "___ /3"],
                ["الاتساق النهائي (Saga)", "بلا saga", "saga بلا تعويض/بلا timeouts", "حالات + تعويض + 3 timeouts + تخزين EF بـconcurrency", "+ `saga-monitoring.sql` + NeedsManual + إنذار + اختبار لكل مسار", "___ /3"],
                ["الاعتمادية (Resilience)", "بلا", "retry بسيط", "pipelines لكل تابع + breaker + bulkhead + fallback مُعلَن", "+ ميزانية مهلة موثقة + اختبارات `FakeTimeProvider` + أرقام قبل/بعد", "___ /3"],
                ["Idempotency والحماية", "بلا", "dedup في مستهلك واحد", "inbox/قيود فريدة + مفاتيح idempotency + throttling لكل مستأجر", "+ اختبارات التزامن/التكرار + 429 مع `Retry-After` + عزل مثبت بأرقام", "___ /3"],
                ["الاختبار والتشخيص", "بلا اختبارات", "اختبارات وحدة فقط", "slice + contract + Aspire integration + CI", "+ لوحة/مقاييس مستخدمة فعلًا في تشخيص عطل مُفتعل + run history", "___ /3"],
                ["التوثيق والقرارات", "بلا", "README", "مخطط + جدول أحداث + 5 ADRs + CAPSTONE.md", "+ سكريبت مقابلة 3 دقايق + أدلة رقمية لكل قرار", "___ /3"],
            ]},
            {"type": "code", "lang": "text", "filename": "CAPSTONE.md", "title": "ملف التسليم (انسخ الهيكل واملأه)", "code": r'''
# Capstone المرحلة 5 — نظام طلبات موزّع (Orders · Payments · Notifications · Gateway)

## 1) الخلاصة في 5 سطور
- نظام من 4 خدمات + gateway، تتواصل بالأحداث عبر RabbitMQ، منسّقة بـ.NET Aspire 13.
- الكتابة: Order + Outbox في معاملة واحدة → dispatcher → RabbitMQ → Payments → Saga → Notifications.
- الاتساق: نهائي (eventual) عبر Saga بحالات وتعويض و3 timeouts.
- الاعتمادية: resilience pipelines لكل تابع + bulkhead/throttling لكل مستأجر + idempotency في كل مستهلك.
- النتيجة المُقاسة: 8 سيناريوهات فشل، 0 حدث ضائع، 0 معالجة مكررة، p95 ثابت أثناء هجوم مستأجر.

## 2) التشغيل (أمر واحد)
```
dotnet user-secrets set "Parameters:pg-password" "..." --project src/Shop.AppHost
dotnet run --project src/Shop.AppHost        # → لوحة Aspire + كل الموارد
```
المتطلبات: .NET 10 SDK · Docker · 8GB RAM حرة.

## 3) المخطط
(الصورة/الرسم من docs/system-map.md — ضعه هنا)

## 4) جدول الأحداث
| الحدث | الناشر | المستهلكون | الحقول الأساسية | التوافق |
|---|---|---|---|---|
| order-placed | Orders | Payments, Saga | order_id, lines[], total_minor, currency, schema_version | إضافة حقل اختياري فقط |
| payment-captured | Payments | Orders (Saga), Notifications | order_id, charge_id, amount_minor | … |
| payment-failed | Payments | Orders (Saga) | order_id, reason_code | … |
| order-cancelled | Orders | Notifications, Catalog | order_id, reason | … |

## 5) الأدلة (كل بند بمخرجات)
| البند | الدليل | الرابط/المسار |
|---|---|---|
| عدم فقدان الأحداث | `NoEventLossTests` أخضر + استعلامات SQL | docs/reliability-evidence.md#1 |
| عدم التكرار | charge واحد رغم تسليم مزدوج | docs/reliability-evidence.md#3 |
| التعويض | saga → Cancelled + المخزون رجع | docs/reliability-evidence.md#5 |
| العزل | p95 قبل/أثناء الهجوم | docs/reliability-evidence.md#8 |
| CI | 3 jobs خضرا | (رابط run) |

## 6) القرارات (ADRs)
| ADR | القرار | البدائل المرفوضة |
|---|---|---|
| 0001 | RabbitMQ + MassTransit بدل Kafka | … |
| 0002 | Outbox في EF بدل CDC | … |
| 0003 | Saga orchestration بدل choreography | … |
| 0004 | Aspire بدل docker-compose للتطوير | … |
| 0005 | bulkhead+throttling لكل مستأجر | … |

## 7) الأرقام
| المقياس | قبل | بعد |
|---|---|---|
| p95 إنشاء طلب | ___ ms | ___ ms |
| p95 أثناء هجوم مستأجر (مستأجر هادئ) | ___ ms | ___ ms |
| أحداث ضائعة (8 سيناريوهات) | — | 0 |
| معالجة مكررة | — | 0 |
| زمن CI (fast/contracts/integration) | — | ___ / ___ / ___ دقيقة |

## 8) المعروف إنه ناقص (بصراحة)
- مفيش مصادقة كاملة (JWT مبسّط) · مفيش مراقبة إنتاجية (المرحلة 6) · مفيش K8s (المرحلة 7)
- الإشعارات محاكاة (بلا SMTP/SMS حقيقي) · مفيش اختبار حمل طويل

## 9) إيه اللي اتعلمته (3 نقاط صادقة)
1. …
2. …
3. …
'''},
            {"type": "callout", "kind": "tip", "title": "إزاي تحكي المشروع ده في مقابلة (3 دقايق)",
             "md": """
**الثانية 0–20 (النظام):** «بنيت نظام طلبات موزّع بـ.NET 10: 4 خدمات وgateway، منسّقين بـAspire،
بيتواصلوا بالأحداث عبر RabbitMQ بـMassTransit. الكتابة بتتم في معاملة واحدة مع Outbox،
والتناسق النهائي عبر Saga بحالات وتعويض وtimeouts.»

**الثانية 20–70 (القرار الصعب):** «أهم قرار كان **Orchestration مقابل Choreography** في الـSaga:
اخترت state machine مركزية لأن مسار التعويض فيه 3 خطوات وترتيبها مهم، وكنت محتاج **مراقبة**
لحالات الـsagas — كتبت استعلامات SQL بتوضحلي توزيع الحالات واللي عالق منها أكتر من 20 دقيقة.
البديل (choreography) كان أبسط بس هيصعّب تتبع الفشل.»

**الثانية 70–130 (الدليل):** «اللي فخور بيه إني **أثبتّ** المتانة مش ادعيتها: 8 سيناريوهات فشل —
إيقاف المستهلك، قطع الوسيط، تسليم مكرر، رسالة سامة، فشل الدفع، فشل التعويض، timeout، وهجوم مستأجر.
النتيجة: صفر حدث ضائع، صفر معالجة مكررة، وp95 لمستأجر هادئ فضل ثابت أثناء هجوم مستأجر تاني
بسبب bulkhead وthrottling لكل مستأجر. كل ده اختبارات آلية في CI بـAspire، مش تجارب يدوية.»

**الثانية 130–180 (الدرس + السؤال):** «أكتر حاجة اتعلمتها إن **الـtimeout budget** لازم يُكتب قبل الكود:
أول نسخة كانت فيها retry في 4 طبقات، فالطلب الواحد كان بياخد 40 ثانية قبل ما يفشل.
لما كتبت الميزانية في جدول وحددت طبقة واحدة للمحاولة، بقى الفشل واضح في 6 ثواني.»
ثم اسأل: «أنتم بتتعاملوا إزاي مع الأحداث الضائعة/المكررة في نظامكم؟»

**أسئلة متوقعة وجهّز إجابتها:** ليه RabbitMQ مش Kafka؟ · إزاي بتضمن عدم التكرار؟ ·
إيه اللي يحصل لو الـsaga علق؟ · إزاي بتعمل deploy لخدمة بتغير عقد حدث؟ · فين الـDLQ وبتعمل إيه بيه؟
"""},
            {"type": "tasks", "title": "مهام التسليم", "items": [
                {"id": "t1", "title": "البناء الكامل (7 جلسات)",
                 "md": "نفّذ الجلسات السبع بالترتيب، وكل جلسة بتسليمها ودليلها. لا تنتقل لجلسة قبل ما دليل السابقة موجود.",
                 "criteria": [
                     "أمر واحد يشغّل النظام كله وكل الموارد Healthy في اللوحة (لقطة)",
                     "4 خدمات + gateway بـServiceDefaults وdiscovery — `git grep localhost:[0-9] src/` صفر نتائج",
                     "تدفق واحد يعمل من طرف لطرف: POST /api/orders → charge → saga Completed → إشعار",
                     "Outbox في كل خدمة بتكتب أحداث + dispatcher + DLQ + بنية RabbitMQ معلنة ككود",
                     "Saga بحالات وتعويض و3 timeouts + `saga-monitoring.sql` بنتائج فعلية",
                     "Gateway (YARP) بـclusters بالاسم + correlation id + 429/Retry-After + bulkhead لكل مستأجر",
                     "جدول الـDoD (22 بند) — كل بند عليه دليل أو مكتوب جنبه «ناقص وليه»",
                 ],
                 "hint": "ابدأ بتدفق واحد (orders → payments) وخليه أخضر من طرف لطرف قبل ما تضيف Notifications أو الـSaga. الإحساس بالتقدم بيمنع الاستسلام.",
                 "resources": [
                     {"label": "eShop — عينة Microsoft لميكروسيرفيسز بـAspire", "url": "https://github.com/dotnet-architecture/eShop"},
                     {"label": "Aspire: build your first app", "url": "https://aspire.dev/get-started/first-app/"},
                 ]},
                {"id": "t2", "title": "إثبات المتانة (الأهم — 8 سيناريوهات)",
                 "md": "نفّذ سيناريوهات الفشل الثمانية: 5 آليًا (اختبارات Aspire/slice) و3 يدويًا (docker stop / حقن عطل / هجوم معدل). لكل سيناريو اكتب التوقّع **قبل** التنفيذ، ثم المخرجات، ثم الحكم والإصلاح لو فشل.",
                 "criteria": [
                     "`docs/reliability-evidence.md` فيه 8 صفوف: السيناريو × التوقّع × الملاحظة (مخرجات/لقطة/مقياس) × الحكم",
                     "3 اختبارات آلية على الأقل في `NoEventLossTests` خضرا في CI (فشل مستهلك · فشل دفع وتعويض · هجوم مستأجر)",
                     "إثبات SQL: صفر أحداث ضايعة (orders = events) وصفر تكرار (`HAVING COUNT(*) > 1` = 0 صفوف)",
                     "سيناريو يدوي بقطع الوسيط مع مخرجات قبل/أثناء/بعد + تفسير السلوك",
                     "رسالة سامة → `_error` queue + مقياس + بلا إعادة لا نهائية (مخرجات `rabbitmqctl`)",
                     "أرقام p95 قبل/أثناء هجوم مستأجر (جدول) + تفسير سبب الثبات",
                     "كل حقن عطل عبر مفاتيح تكوين مقصورة على Development/test (كود + تعليق)",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Aspire testing overview", "url": "https://aspire.dev/testing/overview/"},
                     {"label": "Outbox pattern (MassTransit)", "url": "https://masstransit.io/documentation/configuration/outbox"},
                     {"label": "RabbitMQ CLI tools", "url": "https://www.rabbitmq.com/docs/cli"},
                 ]},
                {"id": "t3", "title": "التوثيق والقرارات والعرض",
                 "md": "أكمل التوثيق: مخطط النظام، جدول الأحداث والتوافق، ميزانية المهلة، 5 ADRs، `CAPSTONE.md`، CI بـ3 jobs، وسكريبت المقابلة (3 دقايق) — ودرّب عليه مرة بصوت عالي وسجّل وقتك.",
                 "criteria": [
                     "`docs/system-map.md` فيه مخطط + تدفق الأحداث + قواعد النظام الخمس",
                     "`docs/events.md`: كل حدث × الناشر × المستهلكون × الحقول × قاعدة التوافق (إضافة اختيارية فقط)",
                     "`docs/timeout-budget.md`: كل الطبقات، وكل رقم فيه مقابل في الكود (اذكر الملف والسطر)",
                     "5 ADRs بالقالب: سياق **بأرقام** · قرار · بدائل مرفوضة · نتائج · مراجعة",
                     "`CAPSTONE.md` مملوء بالأرقام الحقيقية (مش `___`) + قسم «المعروف إنه ناقص»",
                     "CI: 3 jobs (fast/contracts/integration) بـ`timeout-minutes` وartifacts — وتشغيل أخضر مرفق",
                     "سكريبت 3 دقايق + وقت مسجّل + إجابات لـ5 أسئلة متوقعة",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Architectural Decision Records", "url": "https://adr.github.io/"},
                     {"label": "Azure Architecture Center — patterns", "url": "https://learn.microsoft.com/azure/architecture/patterns/"},
                     {"label": "GitHub Actions", "url": "https://docs.github.com/en/actions"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET Aspire docs", "url": "https://aspire.dev/"},
                {"label": "eShop — microservices reference sample", "url": "https://github.com/dotnet-architecture/eShop"},
                {"label": "MassTransit — Sagas", "url": "https://masstransit.io/documentation/usage/sagas"},
                {"label": "MassTransit — Outbox", "url": "https://masstransit.io/documentation/configuration/outbox"},
                {"label": "RabbitMQ documentation", "url": "https://www.rabbitmq.com/docs"},
                {"label": "Microservices.io — Saga / Outbox / Idempotent Receiver", "url": "https://microservices.io/patterns/"},
                {"label": "Azure Architecture Center — design patterns", "url": "https://learn.microsoft.com/azure/architecture/patterns/"},
                {"label": "Google SRE Book", "url": "https://sre.google/sre-book/table-of-contents/"},
            ]},
        ],
    },
]
