"""Stage 4, Module 1 — Project structures (lessons 3-4 of 4)."""

TODAY = "2026-10-22"

LESSONS_S4_B = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s4-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
عندك اختيارين معروفين: **monolith** بيتحوّل لكره طين (كل شيء بينادي كل شيء)،
أو **ميكروسيرفيسز** بتدفع ضريبتها من أول يوم (شبكة، معاملات موزعة، مراقبة، نشر، فرق).

الخيار التالت — والأصح لأغلب الفرق — **Modular Monolith**: حدود موديولات صارمة **وملكية بيانات واضحة**،
مع نشر واحد وتواصل داخل العملية. بتاخد انضباط الميكروسيرفيسز من غير تكلفة الشبكة،
ولو احتجت تفصل موديول لاحقًا، الحدود موجودة أصلًا.

الفرق بين «monolith منظّم» و«modular monolith» هو **فرض الحدود**: موديول ما يقدرش يقرأ جداول موديول تاني،
ولا يستخدم أنواعه الداخلية، ولا يعدّل كياناته. والقاعدة دي مفروضة بالـcompiler وباختبارات — مش بالاتفاق الشفهي.
"""},
            {"type": "terms", "items": [
                {"term": "Module", "def": "وحدة قدرة عمل (capability) لها حدود: كود خاص، بيانات خاصة، وعقد عام. أمثلة: Orders، Catalog، Payments، Shipping."},
                {"term": "Public Contract", "def": "السطح الوحيد المسموح للموديولات التانية: أوامر/استعلامات/أحداث/أنواع DTO. **مفيش كيانات ولا DbContext**."},
                {"term": "Internal", "def": "كل تنفيذ الموديول (handlers، entities، DbContext، migrations) — `internal` ومش مرجعي من بره."},
                {"term": "Data Ownership", "def": "كل موديول يملك جداوله (schema خاص). **لا FK ولا join عبر الموديولات** — معرّفات فقط + اتساق eventual."},
                {"term": "In-Process Event", "def": "إشعار داخل نفس العملية (MediatR notification) — سريع، لكن بلا دوام لو سقطت العملية."},
                {"term": "Outbox Event", "def": "حدث يُكتب في نفس معاملة البيانات ثم يُنشر لاحقًا — دوام واتساق eventual عبر الموديولات."},
                {"term": "Integration Assembly", "def": "مشروع `Module.Integration` بيجمع تركيب الموديولات في عملية واحدة (composition root)."},
                {"term": "Coupling Metric", "def": "قياس عددي للاعتماديات عبر الحدود (عدد المراجع، عدد الاستعلامات المتقاطعة) — يوريك هل الحدود بتتحترم فعلًا."},
                {"term": "Strangler Migration", "def": "نقل الحدود تدريجيًا: كود أولًا، ثم بيانات (schema)، ثم أحداث — بلا إعادة كتابة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الهيكل: عقد عام + تنفيذ داخلي"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "حل modular monolith", "code": r'''
# لكل موديول: مشروعان (عقد عام + تنفيذ) — أقوى فرض ممكن بالـcompiler
for m in Orders Catalog Payments Shipping; do
  dotnet new classlib -n Shop.$m.Contracts -o src/Modules/Shop.$m/Shop.$m.Contracts
  dotnet new classlib -n Shop.$m           -o src/Modules/Shop.$m/Shop.$m
  dotnet add src/Modules/Shop.$m/Shop.$m reference src/Modules/Shop.$m/Shop.$m.Contracts
done

dotnet new web      -n Shop.Host           -o src/Shop.Host              # composition root فقط
dotnet new classlib -n Shop.Kernel         -o src/Shop.Kernel            # مشترك صغير جدًا (Money, IClock, Result)
dotnet new classlib -n Shop.Infrastructure -o src/Shop.Infrastructure    # outbox, messaging, logging (تقني)

# ★ الاتجاه المسموح:
#   Shop.X        → Shop.X.Contracts, Shop.Kernel, Shop.Infrastructure
#   Shop.X        → Shop.Y.Contracts      (عقود الموديولات الأخرى فقط — ممنوع Shop.Y نفسه)
#   Shop.Host     → كل Shop.X (للتركيب)
#   ممنوع تمامًا: Shop.Y → Shop.X (التنفيذ الداخلي لأي موديول آخر)

# مثال: موديول الشحن يعرف عقد الطلبات فقط
dotnet add src/Modules/Shop.Shipping/Shop.Shipping \
    reference src/Modules/Shop.Orders/Shop.Orders.Contracts src/Shop.Kernel

# ملاحظة: الحل البديل (الأبسط): مشروع واحد لكل موديول مع مجلدات Public/ و Internal/
# + [assembly: InternalsVisibleTo("Shop.Orders.Tests")] — فرض أقل لكن أسرع في البداية.
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Modules/Shop.Orders/Shop.Orders.Contracts/OrdersContract.cs", "title": "العقد العام: كل ما يعرفه الآخرون عن الطلبات", "code": r'''
namespace Shop.Orders.Contracts;

// ═══ أنواع عامة (بلا EF، بلا تفاصيل تنفيذ) ═══
public readonly record struct OrderId(Guid Value);
public readonly record struct OrderRef(string Number);

public sealed record OrderSnapshot(
    OrderId Id, OrderRef Ref, Guid CustomerId, string Status,
    Money Total, DateTimeOffset PlacedAt, IReadOnlyList<OrderLineSnapshot> Lines);

public sealed record OrderLineSnapshot(Guid ProductId, string Name, int Quantity, Money UnitPrice, Money Subtotal);

// ═══ عمليات يمكن استدعاؤها (sync, in-process) ═══
public interface IOrdersModule
{
    Task<OrderSnapshot?> GetAsync(OrderId id, CancellationToken ct);
    Task<IReadOnlyList<OrderSnapshot>> ListForCustomerAsync(Guid customerId, int size, CancellationToken ct);
}

// ═══ أحداث ينشرها الموديول (للمستهلكين داخل وخارج العملية) ═══
public sealed record OrderPlaced(
    OrderId OrderId, Guid CustomerId, Money Total, DateTimeOffset OccurredAt) : IIntegrationEvent;

public sealed record OrderCancelled(
    OrderId OrderId, Guid CustomerId, Money Total, string Reason, DateTimeOffset OccurredAt) : IIntegrationEvent;

public sealed record OrderShipped(OrderId OrderId, DateTimeOffset OccurredAt) : IIntegrationEvent;

/// <summary>علامة لكل الأحداث العابرة للحدود (تُسلسل JSON وتُكتب في outbox).</summary>
public interface IIntegrationEvent
{
    DateTimeOffset OccurredAt { get; }
    string EventType => GetType().Name;
}

// ═══ استثناءات العقد (جزء من الواجهة العامة) ═══
public sealed class OrderNotFoundException(OrderId id) : Exception($"الطلب {id.Value} غير موجود");
public sealed class OrderConflictException(OrderId id, string status)
    : Exception($"الطلب {id.Value} بحالة {status} لا تسمح بالعملية");
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Modules/Shop.Shipping/Internal/Handlers/OnOrderPlaced.cs", "title": "مستهلك في موديول تاني: يعرف العقد فقط", "code": r'''
using Shop.Orders.Contracts;

namespace Shop.Shipping.Internal.Handlers;

/// <summary>
/// ✓ يعتمد على `Shop.Orders.Contracts` فقط — لا يعرف Order entity ولا OrdersDbContext.
/// ★ بياناته الخاصة: جدول `shipping.shipments` في schema الموديول (مفيش FK لـorders.orders).
/// </summary>
public sealed class OnOrderPlaced(
    ShippingDbContext db, IOrdersModule orders, ILogger<OnOrderPlaced> log)
    : INotificationHandler<IntegrationEventEnvelope<OrderPlaced>>
{
    public async Task Handle(IntegrationEventEnvelope<OrderPlaced> envelope, CancellationToken ct)
    {
        var e = envelope.Event;

        // ① idempotency: إعادة التسليم لا تنشئ شحنة مكررة
        if (await db.Shipments.AnyAsync(s => s.OrderId == e.OrderId.Value, ct))
        {
            log.LogDebug("shipment already exists for {OrderId}", e.OrderId.Value);
            return;
        }

        // ② لو محتاج تفاصيل أكتر من الحدث: استعلام عبر العقد (مش قراءة جدول الموديول التاني!)
        var snapshot = await orders.GetAsync(e.OrderId, ct)
                       ?? throw new InvalidOperationException($"Order {e.OrderId.Value} اختفى بعد الحدث");

        var shipment = Shipment.Schedule(
            orderId: e.OrderId.Value,                 // ★ معرّف فقط — بلا كيان وبلا FK
            address: snapshot.Lines.Count > 0 ? ResolveAddress(snapshot) : throw new InvalidOperationException("لا أسطر"),
            weight: EstimateWeight(snapshot),
            clock: envelope.Clock);

        db.Shipments.Add(shipment);
        await db.SaveChangesAsync(ct);
    }

    private static Address ResolveAddress(OrderSnapshot o) => /* ... */ default!;
    private static decimal EstimateWeight(OrderSnapshot o) => o.Lines.Sum(l => l.Quantity * 0.5m);
}

/// <summary>غلاف يحمل الحدث + بيانات التشغيل (ساعة، معرف تسليم) — يُعرَّف في Kernel.</summary>
public sealed record IntegrationEventEnvelope<TEvent>(TEvent Event, IClock Clock, string MessageId)
    where TEvent : IIntegrationEvent;
'''},
            {"type": "heading", "level": 2, "text": "2) قواعد الحدود (العشرة)"},
            {"type": "table", "head": ["#", "القاعدة", "السبب", "إزاي تفرضها"], "rows": [
                ["1", "موديول يستدعي موديولًا آخر **عبر العقد فقط**", "تغيير التنفيذ لا يكسر الآخرين", "مراجع مشاريع + اختبار معماري"],
                ["2", "لا كيانات ولا `DbContext` في العقد العام", "التنفيذ يبقى حرًا في التغيير", "اختبار: أنواع العقود يجب أن تكون records/interfaces"],
                ["3", "**كل موديول يملك schema بياناته**", "ملكية البيانات = جوهر الحدود", "سياق EF لكل موديول + schemas منفصلة"],
                ["4", "لا FK ولا JOIN عبر الموديولات", "FK = اقتران نشر ويمنع فصل الموديول", "مراجعة migrations + اختبار على `pg_constraint`"],
                ["5", "التواصل غير المتزامن عبر أحداث + **outbox**", "بلا فقد رسائل، بلا معاملات موزعة", "`IIntegrationEvent` + اختبار على جدول outbox"],
                ["6", "idempotency في كل مستهلك حدث", "at-least-once = تكرار متوقع", "اختبار إعادة تسليم لنفس المعرف"],
                ["7", "لا حالة مشتركة قابلة للتعديل بين الموديولات", "تسابق وصعوبة تتبع", "اختبار معماري على أنواع `static` عامة"],
                ["8", "Kernel صغير ومراقب", "Kernel ضخم = طبقة مخفية يقترن بها الكل", "حد أقصى للأنواع + مراجعة كل إضافة"],
                ["9", "عقود مُصدَّرة versioned (لا تغيير كاسر صامت)", "مستهلكون خارجيون/مستقبليون", "اختبار توافق (snapshot للعقد)"],
                ["10", "اختبارات تكامل **لكل موديول** + عقدية بين الموديولات", "الأول يحمي السلوك، الثاني يحمي الحدود", "CI jobs منفصلة"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.ArchTests/ModuleBoundaryTests.cs", "title": "فرض الحدود آليًا (ده اللي بيخليها حقيقية)", "code": r'''
public class ModuleBoundaryTests
{
    private static readonly string[] Modules = ["Orders", "Catalog", "Payments", "Shipping"];

    public static TheoryData<string, string> CrossModulePairs()
    {
        var data = new TheoryData<string, string>();
        foreach (var a in Modules) foreach (var b in Modules) if (a != b) data.Add(a, b);
        return data;
    }

    [Theory]
    [MemberData(nameof(CrossModulePairs))]
    public void Module_does_not_reference_another_modules_internals(string from, string to)
    {
        var assembly = Assembly.Load($"Shop.{from}");

        var result = Types.InAssembly(assembly)
            .ShouldNot()
            .HaveDependencyOn($"Shop.{to}.Internal")        // ✓ العقود مسموحة، التنفيذ ممنوع
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            $"{from} يعتمد على تنفيذ {to}: {string.Join(", ", result.FailingTypeNames?.Take(10) ?? [])}");
    }

    [Theory]
    [InlineData("Orders"), InlineData("Catalog"), InlineData("Payments"), InlineData("Shipping")]
    public void Contracts_contain_no_infrastructure_types(string module)
    {
        var contracts = Assembly.Load($"Shop.{module}.Contracts");

        var result = Types.InAssembly(contracts)
            .ShouldNot()
            .HaveDependencyOnAny("Microsoft.EntityFrameworkCore", "Npgsql", "System.Text.Json.Serialization",
                                 "Microsoft.AspNetCore", "StackExchange.Redis")
            .GetResult();

        result.IsSuccessful.Should().BeTrue("العقد العام يجب أن يبقى تقنيًا محايدًا");
    }

    [Fact]
    public void Each_module_has_exactly_one_DbContext()
    {
        foreach (var module in Modules)
        {
            var contexts = Types.InAssembly(Assembly.Load($"Shop.{module}"))
                .That().Inherit(typeof(DbContext)).GetTypes();

            contexts.Should().HaveCount(1, $"{module} لازم يملك سياق بيانات واحد (ملكية واضحة)");
        }
    }

    [Fact]
    public void Integration_events_are_records_and_immutable()
    {
        var events = Modules
            .SelectMany(m => Types.InAssembly(Assembly.Load($"Shop.{m}.Contracts")).GetTypes())
            .Where(t => t.GetInterfaces().Any(i => i.Name == "IIntegrationEvent"))
            .ToList();

        events.Should().NotBeEmpty();
        foreach (var e in events)
        {
            e.IsSealed.Should().BeTrue($"{e.Name} لازم يكون sealed");
            e.GetProperties().Should().OnlyHave(p => p.SetMethod is null,
                $"{e.Name}: أحداث غير قابلة للتعديل (لا setters عامة)");
        }
    }
}
'''},
            {"type": "code", "lang": "sql", "filename": "db/module-ownership.sql", "title": "ملكية البيانات على مستوى القاعدة (schema لكل موديول)", "code": r'''
-- ① schema لكل موديول + مستخدم تطبيق بصلاحيات محدودة
CREATE SCHEMA IF NOT EXISTS orders   AUTHORIZATION shop;
CREATE SCHEMA IF NOT EXISTS catalog  AUTHORIZATION shop;
CREATE SCHEMA IF NOT EXISTS payments AUTHORIZATION shop;
CREATE SCHEMA IF NOT EXISTS shipping AUTHORIZATION shop;

-- ② كل موديول يعمل migrations على schema الخاص به فقط (EF: HasDefaultSchema في سياق الموديول)

-- ③ اختبار ملكية: لا FK عبر الـschemas (ده اللي بيمنع اقتران النشر)
SELECT con.conname, nsp.nspname AS from_schema, ref.nspname AS to_schema
FROM pg_constraint con
JOIN pg_class      tbl ON tbl.oid = con.conrelid
JOIN pg_namespace  nsp ON nsp.oid = tbl.relnamespace
JOIN pg_class      rt  ON rt.oid  = con.confrelid
JOIN pg_namespace  ref ON ref.oid = rt.relnamespace
WHERE con.contype = 'f' AND nsp.nspname <> ref.nspname;
-- ★ الصفوف = انتهاكات. الصفر = الحدود محفوظة على مستوى البيانات.

-- ④ قياس الاقتران في الاستعلامات: أي join عبر schemas؟
SELECT schemaname, count(*) AS queries, round(mean(mean_exec_time)::numeric, 2) AS mean_ms
FROM pg_stat_statements
WHERE query ILIKE '%orders.%' AND query ILIKE '%catalog.%' AND query ILIKE '%join%'
GROUP BY schemaname;

-- ⑤ منع الكتابة المتقاطعة (لو محتاج حماية أقوى في الإنتاج)
-- REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA orders FROM shipping_app;
'''},
            {"type": "heading", "level": 2, "text": "3) التواصل بين الموديولات: 4 خيارات"},
            {"type": "table", "head": ["الآلية", "الزمن", "الاتساق", "عند الفشل", "استخدمها لما"], "rows": [
                ["نداء مباشر عبر `IOrdersModule`", "nanoseconds", "قوي (نفس المعاملة لو شاركت DbContext… لا تشارك!)", "استثناء فوري", "قراءة بيانات لازمة فورًا (snapshot)"],
                ["**In-process event** (MediatR notification)", "nanoseconds", "قوي داخل نفس الطلب", "استثناء يُفشل الطلب", "تنسيق داخلي سريع، بلا حاجة للدوام"],
                ["**Outbox event** (دائم)", "ms–s", "eventual", "إعادة تسليم + DLQ", "★ عبر الموديولات لأي أثر جانبي (شحن، إشعار، نقاط)"],
                ["وسيط رسائل خارجي (RabbitMQ)", "ms–10s", "eventual", "إعادة تسليم + DLQ", "لما فيه عمليات/خدمات مستقلة أو مستهلكون خارج النظام"],
            ]},
            {"type": "callout", "kind": "danger", "title": "الخطأ القاتل: معاملة عبر موديولين",
             "md": """
```csharp
// ✗ مرفوض: موديول الشحن بيكتب في DbContext موديول الطلبات داخل نفس المعاملة
await using var tx = await ordersDb.Database.BeginTransactionAsync(ct);
ordersDb.Orders.Update(order);
shippingDb.Shipments.Add(shipment);
await tx.CommitAsync(ct);          // ← مستحيل: سياقان/اتصالان مختلفان
```

**ليه ممنوع؟** لأن ده بيحوّل الحدود لوهم: الموديولات بقت كيان واحد، وأي فصل مستحيل.
وكمان لو فرضت اتصالًا واحدًا، رجعت للاقتران الكامل.

**البديل الصحيح:** `OrderPlaced` يُكتب في outbox موديول الطلبات **في نفس معاملته**،
وموديول الشحن يستهلكه لاحقًا (at-least-once + idempotent). النتيجة: اتساق eventual **بضمان عدم الفقد** —
وده بالظبط نفس المقايضة اللي هتواجهها لو فصلت الموديولات لخدمات. بتدفعها دلوقتي بأدوات بسيطة بدل ما تدفعها لاحقًا بشبكة.
"""},
            {"type": "heading", "level": 2, "text": "4) monolith ولا modular ولا ميكروسيرفيسز؟"},
            {"type": "table", "head": ["المعيار", "Monolith عادي", "**Modular Monolith**", "Microservices"], "rows": [
                ["حدود الكود", "ضعيفة/عرفية", "**قوية ومفروضة آليًا**", "قوية (عمليات منفصلة)"],
                ["ملكية البيانات", "مشاركة (قاعدة واحدة)", "**schema لكل موديول**", "قاعدة لكل خدمة"],
                ["تكلفة النشر", "منخفضة", "منخفضة", "عالية (CI/CD لكل خدمة)"],
                ["الاتصال", "نداء دالة", "نداء/حدث داخل العملية (ns)", "شبكة + timeouts + retries"],
                ["معاملات", "بسيطة (ACID)", "داخل الموديول ACID، وعبره outbox", "موزعة (Sagas/outbox) — معقدة"],
                ["المراقبة", "بسيطة", "متوسطة (تتبع عبر الموديولات)", "معقدة (tracing إلزامي)"],
                ["توسع الحمل", "رأسي (أسهل)", "رأسي + أفقي لكل النسخ", "أفقي لكل خدمة بشكل مستقل"],
                ["فرق متعددة", "صراع على الكود", "**حدود ملكية واضحة**", "استقلال كامل"],
                ["تكلفة البداية", "الأقل", "متوسطة", "**الأعلى بكتير**"],
                ["عند الفشل الجزئي", "العملية كلها", "العملية كلها", "الخدمة المعنية فقط (لو صُممت صح)"],
                ["مناسب لـ", "نموذج أولي/أداة", "★ أغلب الفرق (2-30 مطورًا)", "فرق كبيرة، حاجات توسع/امتثال مختلفة فعلًا"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قائمة فحص: هل فعلاً تحتاج ميكروسيرفيسز؟",
             "md": """
افصل خدمة فقط لو **3 أو أكتر** من دول صحيحة **ومقاسة**:
1. فريق مستقل بينشر أسبوعيًا على الأقل وبيُعطَّل بسبب جدول النشر المشترك.
2. موديول له ملف توسّع مختلف بوضوح (مثال: البحث 10× حمل الطلبات) والتوسع الرأسي بقى مكلف.
3. متطلبات امتثال/أمان تفرض عزلًا فيزيائيًا (بيانات دفع، بيانات صحية).
4. احتياج تقني مختلف فعلًا (GPU، لغة تانية، تخزين متخصص كخدمة مستقلة).
5. الموديول مستقر عقديًا (عقد نادر التغيير) وحجمه يبرر عملية مستقلة.
6. عندك مراقبة موزعة ونشر متدرج جاهزين **قبل** الفصل (مش بعده).

لو مفيش 3 → **Modular Monolith**. وهتوفر شهور عمل، ولو احتجت تفصل بعدين، الحدود جاهزة.
"""},
            {"type": "heading", "level": 2, "text": "5) المسار من monolith موجود (بلا إعادة كتابة)"},
            {"type": "steps", "title": "6 خطوات تدريجية (Strangler)", "items": [
                {"title": "ارسم الموديولات بالقدرة العمل، لا بالطبقة",
                 "md": "قائمة بالقدرات: Orders، Catalog، Payments، Shipping، Identity، Notifications. المعيار: **بيانات + قواعد مشتركة** تتغير معًا. مش «Services» ولا «Controllers»."},
                {"title": "قيس الاقتران الحالي",
                 "md": "سكربت يعدّ المراجع المتقاطعة بين المجلدات، والاستعلامات اللي بتلمس جداول أكتر من مجال. ابدأ بالموديول الأقل اقترانًا."},
                {"title": "اعزل الكود أولًا (بلا تغيير بيانات)",
                 "md": "حرّك أنواع الموديول لمجلد/مشروع، أنشئ `Contracts`، وحوّل النداءات المباشرة لاستخدام العقد. اختبارات المعمارية تبدأ حمراء وتفضل حمراء لحد ما تخلص."},
                {"title": "انقل البيانات لـschema الموديول",
                 "md": "`ALTER TABLE … SET SCHEMA orders` (عملية سريعة في Postgres) + تحديث الـmappings. احذف FKs المتقاطعة واستبدلها بمعرّفات + فحص تكاملي دوري."},
                {"title": "حوّل الآثار الجانبية لأحداث + outbox",
                 "md": "كل نداء مباشر «اعمل حاجة بعد كده» يصير حدثًا. المستهلكين idempotent. اختبر إعادة التسليم."},
                {"title": "أضف الحراسة المستمرة",
                 "md": "اختبارات حدود في CI، قياس اقتران دوري (لو زاد → إنذار)، ومراجعة أي إضافة للـKernel."},
            ]},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Host/Program.cs", "title": "Composition root: تركيب الموديولات في عملية واحدة", "code": r'''
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddShopKernel(builder.Configuration);            // clock, logging, health

// ★ كل موديول بيسجّل نفسه — المضيف لا يعرف تفاصيله الداخلية
builder.Services.AddOrdersModule(builder.Configuration);          // DbContext + handlers + IOrdersModule
builder.Services.AddCatalogModule(builder.Configuration);
builder.Services.AddPaymentsModule(builder.Configuration);
builder.Services.AddShippingModule(builder.Configuration);

builder.Services.AddOutbox(builder.Configuration);                // بنية تحتية مشتركة (جدول outbox + dispatcher)
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblies(ModuleRegistry.Assemblies));

var app = builder.Build();

app.UseExceptionHandler().UseSerilogRequestLogging();
foreach (var module in ModuleRegistry.All) module.MapEndpoints(app);   // كل موديول بيعرّف مساراته

app.MapHealthChecks("/health/live");
app.MapGet("/modules", () => ModuleRegistry.All.Select(m => new { m.Name, m.Version }));  // ✓ شفافية
app.Run();

// ── داخل كل موديول ──
public static IServiceCollection AddOrdersModule(this IServiceCollection s, IConfiguration cfg)
{
    s.AddDbContext<OrdersDbContext>(o =>
        o.UseNpgsql(cfg.GetConnectionString("Orders"), npgsql => npgsql.MigrationsHistoryTable("__migrations", "orders")));
    s.AddScoped<IOrdersModule, OrdersModuleFacade>();     // ← الواجهة العامة الوحيدة
    s.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<OrdersModuleFacade>());
    return s;
}

internal sealed class OrdersModuleFacade(OrdersDbContext db) : IOrdersModule
{
    public Task<OrderSnapshot?> GetAsync(OrderId id, CancellationToken ct) =>
        db.Orders.AsNoTracking().Where(o => o.Id == id.Value)
          .Select(o => o.ToSnapshot())                    // ✓ تحويل لـDTO من العقد — لا تسريب كيان
          .FirstOrDefaultAsync(ct);

    public Task<IReadOnlyList<OrderSnapshot>> ListForCustomerAsync(Guid customerId, int size, CancellationToken ct) =>
        db.Orders.AsNoTracking().Where(o => o.CustomerId == customerId)
          .OrderByDescending(o => o.PlacedAt).Take(Math.Clamp(size, 1, 100))
          .Select(o => o.ToSnapshot()).ToListAsync(ct);
}
'''},
            {"type": "checkpoints", "items": [
                "أختار Modular Monolith بمعيار (حجم الفريق، الحاجة للتوسع المستقل، الامتثال) وأسجّل القرار في ADR.",
                "أبني حدودًا حقيقية: عقد عام + تنفيذ `internal` + schema بيانات لكل موديول.",
                "أفرض الحدود آليًا (مراجع مشاريع + اختبارات معمارية + استعلام ملكية FK على القاعدة).",
                "أتواصل بين الموديولات بأحداث + outbox وidempotency، ولا أفتح معاملة عبر موديولين أبدًا.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه الفرق الجوهري بين monolith منظّم وmodular monolith؟",
                 "options": [
                     "عدد الملفات",
                     "فرض الحدود آليًا: ملكية بيانات (schema لكل موديول) + عقود عامة فقط + اختبارات تمنع الاعتماد على التنفيذ الداخلي",
                     "استخدام MediatR",
                     "عدد المشاريع",
                 ], "answer": 1,
                 "explain": "بلا ملكية بيانات وبلا فرض آلي، الموديولات بتتآكل من أول feature مستعجلة — وده اللي بيحصل في أغلب المحاولات."},
                {"q": "ليه FK بين `shipping.shipments.order_id` و`orders.orders.id` ممنوع؟",
                 "options": [
                     "أداء فقط",
                     "بيخلق اقتران نشر ومخطط: أي تغيير في جدول الطلبات بيكسر الشحن، وبيمنع فصل الموديول لخدمة مستقلة",
                     "Postgres لا يدعمه",
                     "مسموح عادي",
                 ], "answer": 1,
                 "explain": "البديل: معرّف + فحص تكامل (اختبار/مهمة دورية) أو حدث outbox يضمن وجود الطلب. التكلفة: اتساق eventual — وهي نفس تكلفة الميكروسيرفيسز."},
                {"q": "مستهلك حدث شحن فشل بعد 5 محاولات. التصرف الصحيح؟",
                 "options": [
                     "احذف الرسالة",
                     "انقلها لـDLQ مع تنبيه، واستمر في معالجة الباقي، وأضف idempotency لإعادتها يدويًا لاحقًا",
                     "أوقف الطابور كله",
                     "أعد المحاولة للأبد",
                 ], "answer": 1,
                 "explain": "الدوران اللانهائي بيوقف كل الرسائل. DLQ + تنبيه + أداة إعادة تشغيل = تشغيل صحي."},
                {"q": "مدير: «نحول لميكروسيرفيسز عشان نتوسع». أحسن رد؟",
                 "options": [
                     "موافق فورًا",
                     "اطلب دليلًا مقاسًا: هل فيه فرق بيُعطَّل بالنشر المشترك؟ هل ملف التوسع مختلف فعلاً؟ هل المراقبة الموزعة جاهزة؟ لو لأ → Modular Monolith",
                     "ارفض دائمًا",
                     "اقترح serverless",
                 ], "answer": 1,
                 "explain": "الميكروسيرفيسز حل لمشاكل تنظيم/توسع محددة، مش هدف. أغلب الفرق بتدفع تكلفتها من غير ما تقابل مشاكلها."},
                {"q": "Kernel (المشروع المشترك) بدأ يكبر — 40 نوعًا ومنطق تسعير. الحكم؟",
                 "options": [
                     "ممتاز، إعادة استخدام",
                     "خطر: بقى موديولًا خفيًا يقترن به الكل — منطق التسعير يجب أن يصير موديول Pricing بعقده الخاص",
                     "احذفه",
                     "انقله لـInfrastructure",
                 ], "answer": 1,
                 "explain": "Kernel الصحي = أنواع قيمة وأدوات صغيرة (Money، IClock، Result، pagination). أي منطق عمل يدخله لازم يبقى موديولًا."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "استخرج موديولين بحدود مفروضة",
                 "md": "من مشروعك الحالي، استخرج موديولين (مثل Orders وCatalog) كـ`Contracts` + `Internal`، مع schema بيانات لكل واحد، وتواصل عبر عقد/أحداث. أضف اختبارات حدود تفشل لو حد كسر القاعدة.",
                 "criteria": [
                     "مشروعان لكل موديول (Contracts/Internal) ومراجع صحيحة الاتجاه",
                     "اختبار معماري يرفض أي اعتماد على `*.Internal` لموديول آخر (مثبت بفشل مفتعل)",
                     "schema منفصل لكل موديول + استعلام يثبت صفر FK عبر الـschemas",
                     "حدث واحد على الأقل بين الموديولين عبر outbox مع اختبار idempotency",
                     "لا `DbContext` ولا كيانات في العقود العامة",
                     "ADR يشرح اختيار الحدود وليه الموديولين دول بالذات",
                 ],
                 "hint": "ابدأ بالزوج الأقل اقترانًا (استخدم قياس المراجع المتقاطعة). ولو لقيت FK متقاطع يصعب حذفه: احذفه وسجّل فحص تكامل دوري — وقيس كم مرة الفحص لقى مشكلة فعلًا."},
                {"id": "t2", "title": "قياس اقتران + قرار الفصل",
                 "md": "اكتب سكربت/اختبار يقيس الاقتران بين الموديولات (مراجع أنواع، عدد أحداث، استعلامات متقاطعة)، وارسم مصفوفة. بناءً عليها اكتب تقييمًا: أي موديول (لو فيه) يستحق الانفصال لخدمة مستقلة، وبأي شروط.",
                 "criteria": [
                     "مصفوفة اقتران قابلة للتوليد آليًا (CSV/markdown) مع تعريف كل مقياس",
                     "قائمة فحص الفصل (6 معايير) مقيّمة لكل موديول بدليل",
                     "قرار صريح: فصل/عدم فصل + الشروط اللي لو حصلت يتغير القرار",
                     "خطة لو اتقرر الفصل: الترتيب، ما الذي يحتاج شبكة/مراقبة أولًا",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Modular Monolith (Kamil Grzybek)", "url": "https://github.com/kgrzybek/modular-monolith-with-ddd"},
                {"label": ".NET architecture — Monolith vs microservices", "url": "https://learn.microsoft.com/dotnet/architecture/cloud-native/choosing-between-monolith-and-microservices"},
                {"label": "eShop — modular sample", "url": "https://github.com/dotnet-architecture/eShop"},
                {"label": "Domain-Driven Design — Bounded Contexts", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice"},
                {"label": "ArchUnitNET", "url": "https://github.com/TNG/ArchUnitNET"},
                {"label": "System design primer — scale", "url": "https://github.com/donnemartin/system-design-primer"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s4-m1-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
بعد 8 شهور، حد من الفريق (أو أنت) هيسأل: «ليه استخدمنا Redis مش كاش محلي؟» و«ليه منعملناش ميكروسيرفيسز؟».
من غير سجل، الإجابة هتبقى «مش فاكر» — فبيعملوا التجربة تاني، أو بيكسروا القرار من غير ما يفهموا سببه.

**ADR (Architecture Decision Record)** وثيقة قصيرة (نص صفحة – صفحة) بتسجّل: السياق، القرار، البدائل، والتبعات.
مش بيروقراطية — ده أرخص أداة لنقل التفكير الهندسي، وأقوى دليل على «seniority» في مقابلة:
بتقدر تقول «اخترنا X بدل Y لأن Z، والتكلفة اللي قبلناها هي W، وهنراجع القرار لو حصل V».
"""},
            {"type": "terms", "items": [
                {"term": "ADR", "def": "سجل قرار معماري: ملف markdown مرقّم، غير قابل للتعديل بعد القبول، يُستبدل (superseded) ولا يُمسح."},
                {"term": "Status", "def": "حالة القرار: `Proposed` → `Accepted` / `Rejected` → `Superseded by ADR-012` / `Deprecated`."},
                {"term": "Context", "def": "الظروف والقيود اللي فرضت القرار (حجم، فريق، متطلبات، تكلفة) — أهم قسم؛ بدونه القرار بلا معنى."},
                {"term": "Consequences", "def": "التبعات: الإيجابية **والسلبية** بصدق. ADR بلا تكاليف = إعلان مش قرار."},
                {"term": "One-way door", "def": "قرار صعب الرجوع (اختيار قاعدة بيانات، نمط تخزين، حدود موديولات) → يستحق ADR ومراجعة أعمق."},
                {"term": "Two-way door", "def": "قرار سهل الرجوع (اسم متغير، حجم pool، TTL كاش) → ما يستاهلش ADR؛ قرار سريع وقياس."},
                {"term": "Alternatives Considered", "def": "الخيارات اللي اتدرست وليه اترفضت — بيمنع إعادة النقاش من الصفر."},
                {"term": "Re-evaluation Trigger", "def": "شرط مقاس يفتح المراجعة (مثلًا: «لو p95 > 300ms» أو «لو بقى فيه فريقان بينشروا بشكل مستقل»)."},
                {"term": "MADR", "def": "قالب ADR خفيف ومنتشر (Markdown Any/Architecture Decision Records) — الأساس اللي بنستخدمه هنا."},
            ]},
            {"type": "heading", "level": 2, "text": "1) القالب (انسخه كما هو)"},
            {"type": "code", "lang": "text", "filename": "docs/adr/0000-template.md", "title": "القالب: 7 أقسام، نص صفحة", "code": r'''
# ADR-NNNN: عنوان القرار (جملة فعلية قصيرة)

- **الحالة**: Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- **التاريخ**: 2026-10-22
- **أصحاب القرار**: @alice (tech lead), @bob (backend)
- **قابل للتراجع؟**: one-way door | two-way door

## السياق (Context)
ما الذي نواجهه بالأرقام والقيود؟ (حجم البيانات، معدل الطلبات، حجم الفريق، المتطلبات، المواعيد، التكلفة الحالية)
لا تكتب الحل هنا — اكتب المشكلة والقيود فقط.

## القرار (Decision)
جملة واحدة واضحة: «سنفعل X». ثم 2-5 نقاط تنفيذية محددة (ما الذي يتغير فعلًا في الكود/التشغيل).

## البدائل المدروسة (Alternatives Considered)
| البديل | لماذا لم نختاره |
|---|---|
| Y | سبب محدد (تكلفة/تعقيد/عدم توافق مع قيد) |
| Z | سبب محدد |

## التبعات (Consequences)
**إيجابية:**
- ...
**سلبية / التكاليف المقبولة:**          ← القسم الأهم والأكثر تجاهلًا
- ...
**مخاطر وتخفيفها:**
- خطر: ... → تخفيف: ...

## شروط إعادة النظر (Re-evaluation Triggers)
- مقياس محدد: «لو X تجاوز Y لمدة أسبوعين»
- حدث: «لو انضم فريق ثالث» / «لو تطلب الامتثال عزل البيانات»

## مراجع
- روابط للتوثيق، القياسات، ADRs ذات صلة، نتائج اختبارات.
'''},
            {"type": "heading", "level": 2, "text": "2) ثلاث ADRs حقيقية (من قرارات المراحل السابقة)"},
            {"type": "code", "lang": "text", "filename": "docs/adr/0007-modular-monolith-over-microservices.md", "title": "ADR-0007: modular monolith بدل ميكروسيرفيسز", "code": r'''
# ADR-0007: نبني النظام كـModular Monolith بدل Microservices

- **الحالة**: Accepted
- **التاريخ**: 2026-10-22
- **أصحاب القرار**: @lead, @backend-1, @backend-2
- **قابل للتراجع؟**: one-way door (الحدود والبيانات) — لكن التخفيف: الحدود تُصمَّم قابلة للفصل

## السياق
فريق 4 مطورين، منتج واحد، 3 مجالات (طلبات/كتالوج/شحن). الحمل الحالي 120 RPS
وقياسنا (k6، درس 3.3.3) أظهر سعة ≈ 640 RPS على نسخة واحدة بموارد 2vCPU/2GB.
لا يوجد الآن CI/CD متعدد الخدمات ولا مراقبة موزعة (tracing) جاهزة.
نحتاج تسليمًا أسبوعيًا، وأي تأخير نشر مشترك يكلفنا أقل من ساعة شهريًا (مقاس من سجل النشر).

## القرار
نبني **Modular Monolith**: موديول لكل قدرة عمل بمشروعَي `Contracts`/`Internal`،
schema بيانات لكل موديول، وتواصل عبر عقد مباشر للقراءات وأحداث outbox للآثار الجانبية.
نشر واحد (حاوية واحدة) مع قابلية فصل أي موديول لاحقًا بلا إعادة تصميم بيانات.

## البدائل المدروسة
| البديل | لماذا لم نختاره |
|---|---|
| Microservices من البداية | 3 خدمات × (CI/CD + tracing + عقود + نشر متدرج) ≈ 6-8 أسابيع بنية تحتية قبل أي ميزة؛ ولا مشكلة توسع مقاسة |
| Monolith تقليدي (بلا حدود) | تاريخيًا انتهى باقتران كامل؛ تغيير في الكتالوج كسر الشحن مرتين الشهر الماضي |
| Serverless لكل ميزة | cold starts + صعوبة المعاملات + تكلفة تشغيل غير متوقعة لحملنا الحالي |

## التبعات
**إيجابية:**
- وقت تسليم الميزة أقل (بلا شبكة/عقود خارجية)، وتصحيح محلي بسيط (debugger واحد)
- معاملات ACID داخل الموديول بدل Sagas
- تكلفة تشغيل واحدة (حاوية) ومراقبة بسيطة

**سلبية / التكاليف المقبولة:**
- فشل في موديول واحد قد يسقط العملية كلها → تخفيف: health checks، circuit breakers، حدود ذاكرة/CPU، timeouts داخلية
- لا توسع مستقل لكل موديول → مقبول حاليًا (الحمل 19% من السعة المقاسة)
- انضباط مطلوب من الفريق (اختبارات معمارية في CI إلزامية)

## شروط إعادة النظر
- لو فريق ≥ 8 مطورين **و** تأخير النشر المشترك > 4 ساعات/أسبوع (مقاس)
- لو موديول واحد يحتاج ≥ 3× موارد الآخرين (دليل من القياس، مش تقدير)
- لو متطلبات امتثال تفرض عزل بيانات الدفع فيزيائيًا
- لو السعة المطلوبة > 4× السعة الحالية ولم يعد التوسع الرأسي ممكنًا

## مراجع
- ADR-0003 (اختيار PostgreSQL) · قياس السعة في `results/baseline/summary.txt` · درس 4.1.3
'''},
            {"type": "code", "lang": "text", "filename": "docs/adr/0011-hybridcache-ttl-30s.md", "title": "ADR-0011: كاش بـTTL 30 ثانية مع إبطال بالوسوم", "code": r'''
# ADR-0011: HybridCache لصفحات القوائم بـTTL 30s + إبطال بالوسوم بعد الكتابة

- **الحالة**: Accepted
- **التاريخ**: 2026-10-22
- **قابل للتراجع؟**: two-way door (القيم قابلة للضبط بلا تغيير بنية)

## السياق
`GET /api/orders` كان p95 = 812ms و22 استعلامًا لكل طلب (قياس 3.4.1).
بعد إصلاح الاستعلامات (ADR-0010) وصل p95 = 63ms لكن الحمل المستهدف 1,200 RPS.
قوائم الطلبات تُقرأ ~40× أكثر مما تُكتب، وعدم الاتساق لمدة قصيرة **مقبول تجاريًا**
(المنتج وافق: «حتى 30 ثانية مقبول في القوائم، لكن تفاصيل الطلب يجب أن تكون فورية»).

## القرار
`HybridCache` (L1 في الذاكرة 10s + L2 في Redis 30s) على **القوائم فقط**،
بمفتاح يشمل المستأجر والمستخدم والفلاتر، وإبطال بالوسوم (`RemoveByTagAsync`) بعد كل كتابة مؤثرة.
تفاصيل الطلب والكتابات **بلا كاش**.

## البدائل المدروسة
| البديل | لماذا لم نختاره |
|---|---|
| Output cache على endpoint مفوّض | خطر تسريب بين المستخدمين لو أخطأنا في `SetVaryByAuthorizedUser`؛ صعوبة إبطال دقيقة |
| Redis فقط (بلا L1) | latency شبكة لكل قراءة ساخنة (2-4ms) × 1,200 RPS = ضغط غير لازم |
| بلا كاش (تحسين الاستعلام فقط) | لا يحقق السعة المستهدفة عند 1,200 RPS بحسب القياس |
| TTL طويل (10 دقائق) | يتجاوز ما وافق عليه المنتج؛ يزيد نافذة عدم الاتساق |

## التبعات
**إيجابية:** p95 من 63ms إلى 24ms، والسعة من 512 إلى 1,240 RPS، ضغط القاعدة −82%.
**سلبية:** عدم اتساق ≤ 30s على القوائم (موثق ومقبول) · L1 قد يحتفظ ببيانات قديمة لو فقدنا رسالة pub/sub
(شبكة الأمان: `LocalCacheExpiration` = 10s) · تعقيد إبطال إضافي في كل مسار كتابة.
**مخاطر:** إبطال منسي بعد كتابة جديدة → تخفيف: اختبار تكامل يثبت إن الكتابة تليها قراءة جديدة،
ومراجعة أي مسار كتابة جديد في checklist الـPR.

## شروط إعادة النظر
- لو نسبة الإصابة < 40% لمدة أسبوع (يعني الكاش ما بيستحقش تعقيده)
- لو شكوى منتَج من عدم اتساق القوائم → تقليل TTL أو إزالة الكاش عن القوائم المتأثرة
- لو صار L2 (Redis) نقطة فشل: راجع fail-open وسلوك Degraded

## مراجع
- درس 2.1.6 (الكاش) · 3.3.1 (Redis) · قياسات `results/05-final/`
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء ADR الشائعة (بتخليها بلا قيمة)",
             "md": """
- **ADR لكل قرار صغير** (`TTL = 30s` كمستند منفصل لكل إعداد) → ضجيج وماحدش بيقرأ.
  القاعدة: **one-way door** أو تكلفة/خلاف حقيقي → ADR. قرار قابل للتجربة → PR عادي.
- **بلا قسم «التكاليف المقبولة»** → إعلان تسويقي مش قرار. لو ما فيش سلبيات، إنت ما درستش البدائل.
- **بلا بدائل مدروسة** → بعد 6 شهور حد هيقترح نفس البديل وتعيد النقاش من الصفر.
- **تعديل ADR مقبول بدل كتابة واحد جديد** → السجل بيفقد معناه. الصح: `Superseded by ADR-0014`.
- **حالة `Proposed` للأبد** → القرار إما مقبول أو مرفوض؛ علّق قرارًا بموعد/صاحب.
- **كتابة بلا سياق رقمي** («النظام بطيء») → بلا أرقام، ما تعرفش إمتى تراجع القرار.
- **دفنها في Confluence** → لازم في الـrepo جنب الكود، وتتراجع في نفس الـPR اللي بيغير المعمارية.
"""},
            {"type": "heading", "level": 2, "text": "3) التفكير في المقايضات (الجزء اللي بيتسأل عنه في المقابلات)"},
            {"type": "table", "head": ["السؤال", "الإجابة الضعيفة", "الإجابة القوية"], "rows": [
                ["«ليه استخدمت CQRS؟»", "«لأنه نمط شائع»", "«القراءات 40× الكتابات ومحتاجة projections مختلفة تمامًا؛ الفصل خلى مسار القراءة يستخدم Dapper بلا قيود EF. التكلفة: ضعف عدد الأنواع وoutbox للاتساق»"],
                ["«ليه PostgreSQL مش MongoDB؟»", "«SQL أفضل»", "«عندنا معاملات عبر 3 جداول وقيود فريدة وتقارير ad-hoc — كلها نقاط ضعف المستندية. حجمنا الحالي (2M صف) بعيد عن حد التوسع الأفقي اللي يبرر NoSQL»"],
                ["«إيه أسوأ حاجة في تصميمك؟»", "«مفيش»", "«الاتساق eventual عبر الموديولات: الشحن ممكن يتأخر ثواني بعد الطلب. قبلناه لأن البديل (معاملة موزعة) أغلى بكتير. عندنا فحص تكامل كل ساعة بيقيس الفجوة»"],
                ["«إمتى تغير القرار؟»", "«لما نحتاج»", "«لو p95 تعدى 300ms لأسبوعين، أو فريق ثالث انضم — دول شروط مكتوبة في ADR-0007»"],
                ["«إزاي قِست التحسن؟»", "«حسّيت إنه أسرع»", "«k6 بـ50 VUs على بيئة ثابتة: p95 من 812 إلى 24ms، 68% من التحسّن من فهرس مركّب — القياسات محفوظة في results/»"],
            ]},
            {"type": "callout", "kind": "tip", "title": "كيف تستخدم ADRs في البحث عن وظيفة (المرحلة 10)",
             "md": """
1. **في الـrepo**: مجلد `docs/adr/` بـ5-8 قرارات حقيقية = دليل إنك بتفكر كمهندس مش ككاتب كود.
2. **في المقابلة**: جهّز قصة STAR واحدة لكل ADR مهم (السياق → القرار → القياس → النتيجة).
   الأسئلة اللي هتتجاب: «ليه ده؟»، «إيه التكلفة؟»، «إمتى تراجعه؟» — وكلها مكتوبة عندك.
3. **في السيرة**: سطر واحد بأرقام مستمدة من ADRs («خفّضت p95 بنسبة 97% عبر إعادة تصميم الفهارس والكاش»).
4. **لا تكتب ADRs وهمية**: المراجع بيشمّها. اكتب القرارات اللي عملتها فعلًا في مشروعك — حتى لو صغيرة.
"""},
            {"type": "code", "lang": "bash", "filename": "docs/adr/README.md + tools", "title": "الفهرس + أتمتة بسيطة", "code": r'''
# سجل القرارات المعمارية (ADR Index)

| # | العنوان | الحالة | التاريخ | قابل للتراجع |
|---|---------|--------|---------|---------------|
| [0001](0001-use-dotnet-10-lts.md) | اعتماد .NET 10 LTS كمنصة | Accepted | 2026-10-02 | one-way |
| [0003](0003-postgresql-as-primary-store.md) | PostgreSQL كمصدر الحقيقة | Accepted | 2026-10-05 | one-way |
| [0007](0007-modular-monolith-over-microservices.md) | Modular Monolith بدل Microservices | Accepted | 2026-10-22 | one-way |
| [0010](0010-composite-index-orders.md) | فهرس مركّب لمسار القوائم | Accepted | 2026-10-22 | two-way |
| [0011](0011-hybridcache-ttl-30s.md) | HybridCache بـTTL 30s للقوائم | Accepted | 2026-10-22 | two-way |
| [0012](0012-outbox-for-cross-module.md) | Outbox للتواصل بين الموديولات | Accepted | 2026-10-22 | one-way |
| [0009](0009-event-sourcing-not-now.md) | عدم اعتماد Event Sourcing حاليًا | Rejected | 2026-10-20 | two-way |

> القواعد: ملف لكل قرار · لا تعديل بعد القبول (يُستبدل) · ADR مرفوض يُحفظ **كمان** (بيوفر نقاشًا معادًا).

# ── أتمتة اختيارية ──
# ① توليد رقم وملف جديد من القالب:
n=0013; cp docs/adr/0000-template.md docs/adr/$n-my-decision.md

# ② فحص في CI: كل ADR له حالة وتاريخ وقسم تبعات (يمنع المستندات الناقصة)
for f in docs/adr/[0-9]*.md; do
  grep -q "^- \*\*الحالة\*\*" "$f" || { echo "❌ $f بلا حالة"; exit 1; }
  grep -q "^## التبعات"        "$f" || { echo "❌ $f بلا تبعات"; exit 1; }
  grep -q "^## البدائل"        "$f" || { echo "❌ $f بلا بدائل"; exit 1; }
done
echo "✅ ADRs مكتملة"

# ③ ربط ADR بالكود: علّق في الـcode برقم القرار
# // ADR-0011: TTL قصير مقصود — عدم اتساق ≤30s مقبول تجاريًا
'''},
            {"type": "checkpoints", "items": [
                "أكتب ADR بقالب ثابت: سياق رقمي، قرار، بدائل، تبعات إيجابية **وسلبية**، وشروط إعادة نظر.",
                "أفرّق بين one-way وtwo-way doors وأكتب ADR فقط للقرارات الصعبة أو المكلفة.",
                "أحتفظ بالسجل في الـrepo مفهرسًا، وأستبدل القرارات (superseded) بدل تعديلها.",
                "أستخدم ADRs في المقابلات: قصة STAR بأرقام وتكلفة وشروط مراجعة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه القرار اللي يستحق ADR؟",
                 "options": [
                     "تغيير اسم متغير",
                     "one-way door أو قرار بتكلفة/خلاف حقيقي: اختيار قاعدة بيانات، حدود موديولات، نمط تخزين، TTL كاش مؤثر تجاريًا",
                     "كل commit",
                     "إصلاح bug",
                 ], "answer": 1,
                 "explain": "القاعدة العملية: لو القرار صعب الرجوع أو ليه تكلفة تشغيلية/تجارية → ADR. لو تجربه وتقيس في ساعة → PR عادي."},
                {"q": "قرار اتغير بعد 4 شهور. تعمل إيه بالـADR الأصلي؟",
                 "options": [
                     "عدّله في مكانه",
                     "احذفه",
                     "اكتب ADR جديد واجعل القديم `Superseded by ADR-XXXX` — السجل التاريخي هو القيمة",
                     "اتركه بلا حالة",
                 ], "answer": 2,
                 "explain": "لو مسحت التاريخ، الفريق هيعيد نفس التجربة الفاشلة. الـsuperseding بيوضح تطور التفكير."},
                {"q": "قسم «التبعات السلبية» — ليه الأهم؟",
                 "options": [
                     "شكلي",
                     "لأنه إثبات إنك درست المقايضات: كل قرار له تكلفة، وغيابها يعني إنك بتبيع مش بتقرر",
                     "يقلل الثقة في القرار",
                     "مطلوب قانونيًا",
                 ], "answer": 1,
                 "explain": "في المقابلة، السؤال «إيه أسوأ حاجة في تصميمك؟» بيكشف الفرق بين مهندس ومبرمج. الإجابة «مفيش» = إنذار أحمر."},
                {"q": "«شروط إعادة النظر» لازم تكون…",
                 "options": [
                     "عامة («لما نحتاج»)",
                     "مقاسة ومرتبطة بحدث («لو p95 > 300ms لأسبوعين» أو «لو فريق ثالث انضم»)",
                     "تواريخ ثابتة",
                     "غير موجودة",
                 ], "answer": 1,
                 "explain": "الشرط المقاس بيحوّل المراجعة من نقاش عاطفي لقرار مبني على بيانات — وبيخلي القرار صالح للتدقيق بعد سنة."},
                {"q": "ADR مرفوض (Rejected) — تحتفظ بيه؟",
                 "options": [
                     "لا، احذفه",
                     "نعم — بيوفر على الفريق إعادة اقتراح نفس البديل وبيوثق ليه اترفض",
                     "حوّله لمقبول",
                     "انقله لمكان تاني",
                 ], "answer": 1,
                 "explain": "مثال: ADR «عدم اعتماد Event Sourcing حاليًا» بأدلة — لما حد يقترحه بعد سنة، النقاش بيبدأ من نهاية النقاش السابق."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "3 ADRs حقيقية لمشروعك",
                 "md": "اكتب 3 قرارات فعلية في مشروعك (واحد one-way على الأقل، وواحد two-way، وواحد **مرفوض** أو superseded) بالقالب الكامل، وأضف فهرسًا في `docs/adr/README.md`.",
                 "criteria": [
                     "كل ADR فيه: حالة، تاريخ، سياق **بأرقام**، قرار، بدائل (≥2) بأسباب الرفض، تبعات إيجابية وسلبية، شروط إعادة نظر",
                     "واحد على الأقل one-way door وواحد two-way door (مصنّفان صراحة)",
                     "واحد مرفوض أو superseded (مش كلهم مقبولين — ده غير واقعي)",
                     "فهرس بجدول في README",
                     "قرار واحد مرتبط بكود بتعليق `// ADR-NNNN`",
                 ],
                 "hint": "مش لاقي قرارات؟ شوف الـrepo: ليه اخترت Postgres؟ ليه FluentValidation مش DataAnnotations؟ ليه xUnit مش NUnit؟ ليه Dockerfile متعدد المراحل؟ كلها قرارات فيها بدائل وتكاليف."},
                {"id": "t2", "title": "فحص ADRs في CI + قصة مقابلة",
                 "md": "أضف فحصًا في CI يتأكد إن كل ADR مكتمل الأقسام، واكتب قصة STAR واحدة (صفحة) عن أهم قرار: السياق بالأرقام، القرار، التنفيذ، القياس، والنتيجة — جاهزة تُقال في مقابلة.",
                 "criteria": [
                     "سكربت فحص يفشل لو ADR بلا حالة/تبعات/بدائل (مثبت بفشل مفتعل)",
                     "قصة STAR بـ5 أقسام فيها رقمين على الأقل وقياس للنتيجة",
                     "القصة تتضمن التكلفة المقبولة وشرط إعادة النظر (مش نجاح فقط)",
                     "بروفة: احكِ القصة في أقل من 3 دقائق (سجّل نفسك أو اكتب النسخة المختصرة)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "ADR — Documenting architecture decisions", "url": "https://adr.github.io/"},
                {"label": "MADR template", "url": "https://adr.github.io/madr/"},
                {"label": "AWS — Architectural decision records", "url": "https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html"},
                {"label": ".NET architecture — design principles", "url": "https://learn.microsoft.com/dotnet/architecture/modern-web-apps-azure/architectural-principles"},
                {"label": "ThoughtWorks Tech Radar — Lightweight ADRs", "url": "https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records"},
            ]},
        ],
    },
]
