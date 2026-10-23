"""Stage 4, Module 1 — Project structures (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S4_A = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s4-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
المعمارية مش شكل المجلدات — المعمارية هي **قواعد اتجاه الاعتماد**: مين يُسمح له إنه يعرف مين.
القاعدة دي هي اللي بتحدد إن تغيير في قاعدة البيانات ما يكسرش منطق العمل، وإن اختبارات الـDomain تشتغل بلا قاعدة،
وإن مطور جديد يعرف فين يحط الكود من غير ما يسأل.

Clean/Onion Architecture هي الأشهر في .NET، وموجودة في مرجع مايكروسوفت الرسمي وفي مشاريع حقيقية زي eShop.
لكن 90% من التطبيقات اللي بتستخدمها **بتطبقها غلط**: طبقات فاضية، Domain بلا سلوك (anemic)،
و`Application` معتمد على `Infrastructure` من وراء الستار. هنا هنبنيها صح ونفرضها باختبارات.
"""},
            {"type": "terms", "items": [
                {"term": "Dependency Rule", "def": "الاعتمادات تتجه للداخل فقط. `Domain` لا يعتمد على شيء، و`Application` على `Domain`، و`Infrastructure`/`Api` على الاثنين."},
                {"term": "Domain", "def": "قواعد العمل الجوهرية: Entities بسلوك، Value Objects، Domain Events، استثناءات مجال. **بلا أي اعتماد تقني** (لا EF، لا JSON، لا HTTP)."},
                {"term": "Application", "def": "حالات الاستخدام (use cases): أوامر/استعلامات، DTOs، validation، و**المنافذ** (interfaces) اللي بتعرفها الطبقة الخارجية."},
                {"term": "Infrastructure", "def": "التفاصيل التقنية: EF Core DbContext وMigrations، مخازن، عملاء HTTP خارجيين، تخزين ملفات، مراسلة. بتنفّذ منافذ `Application`."},
                {"term": "Port (منفذ)", "def": "واجهة معرّفة في `Application` (مثل `IOrderRepository`) — العقد اللي `Infrastructure` بتنفّذه. ده اللي بيعكس اتجاه الاعتماد."},
                {"term": "Adapter", "def": "التنفيذ في `Infrastructure` (`EfOrderRepository`). ممكن تستبدله (اختبارات: in-memory/fake)."},
                {"term": "Composition Root", "def": "المكان الوحيد اللي بيتسجل فيه كل شيء في الـDI — في `Program.cs` (طبقة `Api`). الطبقات الداخلية لا تعرف عن DI."},
                {"term": "Anemic Domain Model", "def": "كيانات بلا سلوك (getters/setters فقط) وكل المنطق في services → أشهر فشل في تطبيق Clean Architecture."},
                {"term": "Architecture Test", "def": "اختبار يفحص التجميعات (assemblies) ويرفض أي اعتماد ممنوع — بيحوّل القاعدة المعمارية من وثيقة لـCI أحمر."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الهيكل واتجاه الاعتماد"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحل (solution) بالمشاريع والمراجع", "code": r'''
# ── المشاريع ──
dotnet new classlib -n Shop.Domain          -o src/Shop.Domain
dotnet new classlib -n Shop.Application     -o src/Shop.Application
dotnet new classlib -n Shop.Infrastructure  -o src/Shop.Infrastructure
dotnet new web      -n Shop.Api             -o src/Shop.Api
dotnet new xunit    -n Shop.UnitTests       -o tests/Shop.UnitTests
dotnet new xunit    -n Shop.ArchTests       -o tests/Shop.ArchTests
dotnet new xunit    -n Shop.IntegrationTests -o tests/Shop.IntegrationTests

# ── اتجاه الاعتماد (القاعدة الوحيدة اللي لازم تتحفظ) ──
dotnet add src/Shop.Application    reference src/Shop.Domain
dotnet add src/Shop.Infrastructure reference src/Shop.Application   # (وبيجيب Domain بالتبعية)
dotnet add src/Shop.Api            reference src/Shop.Application src/Shop.Infrastructure

# ★ انتبه: Domain بلا مراجع إطلاقًا. Application لا يرجع Infrastructure.
# لو حصل، عندك دائرة (circular reference) — والمشروع أصلًا مش هيترجم.

# ── أدوات فرض المعمارية ──
dotnet add tests/Shop.ArchTests package NetArchTest.Rules
# بديل: ArchUnitNET (أقوى في قواعد الطبقات والـslices)
'''},
            {"type": "table", "head": ["نوع الكود", "المشروع", "ملاحظة حاسمة"], "rows": [
                ["Entity بسلوك (`Order.Cancel()`)", "**Domain**", "يرفع Domain Event بدل ما ينادي خدمة خارجية"],
                ["Value Object (`Money`, `Address`)", "**Domain**", "`readonly record struct` + تحقق في الـconstructor"],
                ["Domain Event (`OrderCancelled`)", "**Domain**", "record بسيط — بلا اعتماد على MediatR/RabbitMQ"],
                ["استثناء مجال (`InsufficientStockException`)", "**Domain**", "تُترجم لـHTTP في `Api` (مش تُرمى كـ400 من Domain)"],
                ["خدمة مجال نقية (`PricingPolicy`)", "**Domain**", "لو القاعدة تخص عدة aggregates"],
                ["Command/Query + Handler", "**Application**", "حالة استخدام واحدة لكل ملف/مجلد"],
                ["منفذ (`IOrderRepository`, `IClock`, `IEventPublisher`)", "**Application**", "التعريف هنا، التنفيذ في Infrastructure"],
                ["DTO / Response records", "**Application**", "لا تُرجع Entity للـAPI"],
                ["Validators (FluentValidation)", "**Application**", "تحقق الشكل/المدخلات؛ قواعد العمل في Domain"],
                ["DbContext + Mappings + Migrations", "**Infrastructure**", "EF هنا فقط — ولا attribute واحد في Domain"],
                ["تنفيذ المنافذ (`EfOrderRepository`, `SystemClock`)", "**Infrastructure**", "قابل للاستبدال في الاختبارات"],
                ["عملاء خارجيين (Stripe/SendGrid/HttpClient)", "**Infrastructure**", "خلف منفذ + Polly (درس المرحلة 2)"],
                ["Endpoints / Middleware / Auth / DI wiring", "**Api**", "طبقة تسليم رقيقة — لا منطق عمل"],
                ["اختبارات وحدة للـDomain", "**tests/UnitTests**", "تشتغل بلا قاعدة ولا شبكة (في أجزاء من الثانية)"],
            ]},
            {"type": "heading", "level": 2, "text": "2) Domain: سلوك وقواعد، لا حقول"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Orders/Order.cs", "title": "Entity غني: الحالة تتغير من خلال السلوك فقط", "code": r'''
namespace Shop.Domain.Orders;

public class Order : AggregateRoot
{
    private readonly List<OrderLine> _lines = [];

    public Guid Id { get; private init; }                 // ✓ private setters: التعديل عبر السلوك فقط
    public Guid CustomerId { get; private init; }
    public OrderStatus Status { get; private set; }
    public Money Total { get; private set; }
    public DateTimeOffset CreatedAt { get; private init; }
    public DateTimeOffset? CancelledAt { get; private set; }
    public string? CancellationReason { get; private set; }
    public IReadOnlyList<OrderLine> Lines => _lines;      // ✓ لا تسريب للمجموعة الداخلية

    private Order() { }                                   // لـEF فقط

    public static Order Place(Guid customerId, IEnumerable<OrderLine> lines, IClock clock)
    {
        ArgumentNullException.ThrowIfNull(customerId);
        var materialized = lines.ToList();
        if (materialized.Count == 0)
            throw new EmptyOrderException(customerId);    // ★ استثناء مجال (يُترجم في Api)

        var order = new Order
        {
            Id = Guid.NewGuid(),
            CustomerId = customerId,
            Status = OrderStatus.Placed,
            CreatedAt = clock.UtcNow,
        };

        foreach (var line in materialized) order.AddLine(line);   // كل سطر يمر بنفس القاعدة
        order.RecalculateTotal();

        order.Raise(new OrderPlaced(order.Id, order.CustomerId, order.Total, order.CreatedAt));
        return order;
    }

    public void Cancel(string reason, IClock clock)
    {
        if (Status is OrderStatus.Shipped or OrderStatus.Delivered)
            throw new OrderCannotBeCancelledException(Id, Status);     // ← قاعدة عمل في مكانها الصحيح

        if (string.IsNullOrWhiteSpace(reason))
            throw new ArgumentException("سبب الإلغاء مطلوب", nameof(reason));

        Status = OrderStatus.Cancelled;
        CancelledAt = clock.UtcNow;
        CancellationReason = reason.Trim();

        Raise(new OrderCancelled(Id, CustomerId, Total, CancelledAt.Value, CancellationReason));
    }

    public void Ship(IClock clock)
    {
        if (Status != OrderStatus.Placed)
            throw new InvalidOrderTransitionException(Id, Status, OrderStatus.Shipped);

        Status = OrderStatus.Shipped;
        Raise(new OrderShipped(Id, clock.UtcNow));
    }

    private void AddLine(OrderLine line)
    {
        if (Status != OrderStatus.Placed)
            throw new InvalidOperationException("لا يمكن تعديل طلب غير بحالة Placed");

        // ★ قاعدة عمل: منع تكرار نفس المنتج في سطرين
        var existing = _lines.FirstOrDefault(l => l.ProductId == line.ProductId);
        if (existing is not null) existing.IncreaseQuantity(line.Quantity);
        else _lines.Add(line);
    }

    private void RecalculateTotal() =>
        Total = _lines.Aggregate(Money.Zero, (sum, l) => sum + l.Subtotal);
}

public abstract class AggregateRoot
{
    private readonly List<IDomainEvent> _events = [];
    public IReadOnlyList<IDomainEvent> DomainEvents => _events;
    protected void Raise(IDomainEvent e) => _events.Add(e);
    public void ClearEvents() => _events.Clear();          // تُنادى بعد النشر (من Infrastructure)
}

public interface IDomainEvent { DateTimeOffset OccurredAt { get; } }
public interface IClock { DateTimeOffset UtcNow { get; } }   // ★ منفذ في Domain: الزمن قابل للاختبار
'''},
            {"type": "callout", "kind": "warn", "title": "علامات Anemic Domain Model (افحص مشروعك)",
             "md": """
- كل خصائص الكيان `public set` ومفيش ولا method غير getters → الكيان **مجموعة بيانات**، مش نموذج مجال.
- فيه `OrderService.CancelOrder(orderId, reason)` بيعدّل الحالة من بره → القاعدة مبعثرة وكل خدمة ممكن تعدلها بشكل مختلف.
- اختباراتك كلها بتختبر services، ولا اختبار واحد لكيان → **قواعد العمل غير محمية**.
- الـvalidation كله في الـAPI/DTO → Domain ممكن تدخله حالة غير صالحة من أي مسار تاني (job، مستهلك حدث، migration).
- `if (order.Status == "cancelled")` منتشرة في 14 مكان → مفيش مكان واحد بيعرّف «إيه معنى الإلغاء».

**الإصلاح:** انقل كل `if` يخص حالة الكيان لجوه الكيان كـmethod، واجعل setters خاصة، وارفع Domain Events بدل نداء خدمات خارجية.
"""},
            {"type": "heading", "level": 2, "text": "3) Application: حالات الاستخدام والمنافذ"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Application/Orders/CancelOrder.cs", "title": "Command + Handler + منفذ — بلا أي اعتماد تقني", "code": r'''
using Shop.Domain.Orders;

namespace Shop.Application.Orders;

// ── الطلب والاستجابة: records بسيطة ──
public sealed record CancelOrderCommand(Guid OrderId, string Reason);
public sealed record CancelOrderResult(Guid OrderId, string Status, DateTimeOffset CancelledAt);

// ── المنافذ: تُعرَّف هنا، وتُنفَّذ في Infrastructure ──
public interface IOrderRepository
{
    Task<Order?> FindAsync(Guid id, CancellationToken ct);
    void Add(Order order);                                  // Add فقط — الحفظ مسؤولية الـUnitOfWork
}

public interface IUnitOfWork
{
    /// <summary>يحفظ التغييرات وينشر أحداث الـDomain المتراكمة في نفس المعاملة (outbox).</summary>
    Task<int> SaveChangesAsync(CancellationToken ct);
}

public interface IEventPublisher
{
    Task PublishAsync(IDomainEvent domainEvent, CancellationToken ct);
}

// ── حالة الاستخدام: تنسيق، لا قواعد عمل ──
public sealed class CancelOrderHandler(
    IOrderRepository orders, IUnitOfWork uow, IEventPublisher publisher,
    IClock clock, ILogger<CancelOrderHandler> log)
{
    public async Task<CancelOrderResult> HandleAsync(CancelOrderCommand command, CancellationToken ct)
    {
        var order = await orders.FindAsync(command.OrderId, ct)
                    ?? throw new OrderNotFoundException(command.OrderId);     // استثناء تطبيق

        order.Cancel(command.Reason, clock);              // ★ القاعدة في Domain — هنا مجرد تنسيق

        await uow.SaveChangesAsync(ct);                   // يحفظ + يكتب الأحداث في outbox ذرّيًا

        log.LogInformation("order {OrderId} cancelled: {Reason}", order.Id, command.Reason);
        return new CancelOrderResult(order.Id, order.Status.ToString(), order.CancelledAt!.Value);
    }
}

// ── استثناءات التطبيق (تُترجم لـHTTP في طبقة Api) ──
public sealed class OrderNotFoundException(Guid id)
    : Exception($"الطلب {id} غير موجود");

// ── Validator: تحقق من شكل المدخلات (مش قواعد العمل) ──
public sealed class CancelOrderCommandValidator : AbstractValidator<CancelOrderCommand>
{
    public CancelOrderCommandValidator()
    {
        RuleFor(x => x.OrderId).NotEmpty();
        RuleFor(x => x.Reason).NotEmpty().MaximumLength(500);
    }
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/Persistence/EfOrderRepository.cs", "title": "Adapter + UnitOfWork ينشر الأحداث عبر outbox", "code": r'''
using Shop.Application.Orders;
using Shop.Domain.Orders;

namespace Shop.Infrastructure.Persistence;

public sealed class EfOrderRepository(AppDbContext db) : IOrderRepository
{
    public Task<Order?> FindAsync(Guid id, CancellationToken ct) =>
        db.Orders.Include(o => o.Lines).FirstOrDefaultAsync(o => o.Id == id, ct);
        // ★ EF-specific (Include) يبقى هنا — مش في Application
}

public sealed class UnitOfWork(AppDbContext db, IEventPublisher publisher, ILogger<UnitOfWork> log)
    : IUnitOfWork
{
    public async Task<int> SaveChangesAsync(CancellationToken ct)
    {
        // ① اجمع أحداث الـDomain من كل الـaggregates المتتبَّعة
        var roots = db.ChangeTracker.Entries<AggregateRoot>()
            .Where(e => e.Entity.DomainEvents.Count > 0)
            .Select(e => e.Entity)
            .ToList();

        var events = roots.SelectMany(r => r.DomainEvents).ToList();

        // ② حوّلها لرسائل outbox **قبل** الالتزام (ذرّية مع البيانات)
        foreach (var domainEvent in events)
            db.OutboxMessages.Add(OutboxMessage.From(domainEvent));

        // ③ احفظ البيانات والـoutbox في SaveChanges واحد
        var saved = await db.SaveChangesAsync(ct);

        // ④ انشر في العملية (للمستهلكين المحليين) ونظّف
        foreach (var domainEvent in events)
        {
            try { await publisher.PublishAsync(domainEvent, ct); }
            catch (Exception ex)
            {
                // ✓ الفشل هنا لا يلغي المعاملة: الـoutbox هيسلّم الرسالة لاحقًا
                log.LogWarning(ex, "in-process publish failed for {Event}; outbox will retry",
                    domainEvent.GetType().Name);
            }
        }

        foreach (var root in roots) root.ClearEvents();
        return saved;
    }
}
'''},
            {"type": "heading", "level": 2, "text": "4) فرض المعمارية باختبار (مش بوثيقة)"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.ArchTests/LayerDependencyTests.cs", "title": "NetArchTest: الاتجاه ممنوع عكسه", "code": r'''
using NetArchTest.Rules;
using Xunit;

public class LayerDependencyTests
{
    private static readonly Assembly Domain = typeof(Shop.Domain.Orders.Order).Assembly;
    private static readonly Assembly Application = typeof(Shop.Application.Orders.CancelOrderCommand).Assembly;
    private static readonly Assembly Infrastructure = typeof(Shop.Infrastructure.Persistence.EfOrderRepository).Assembly;

    [Fact]
    public void Domain_does_not_depend_on_any_other_layer()
    {
        var result = Types.InAssembly(Domain)
            .ShouldNot()
            .HaveDependencyOnAny("Shop.Application", "Shop.Infrastructure", "Shop.Api",
                                 "Microsoft.EntityFrameworkCore", "Microsoft.AspNetCore",
                                 "System.Text.Json", "MediatR", "Npgsql", "StackExchange.Redis")
            .GetResult();

        result.IsSuccessful.Should().BeTrue(FailureList(result));
    }

    [Fact]
    public void Application_does_not_depend_on_Infrastructure_or_Api()
    {
        var result = Types.InAssembly(Application)
            .ShouldNot()
            .HaveDependencyOnAny("Shop.Infrastructure", "Shop.Api", "Microsoft.EntityFrameworkCore")
            .GetResult();

        result.IsSuccessful.Should().BeTrue(FailureList(result));
    }

    [Fact]
    public void Domain_entities_do_not_expose_public_setters()
    {
        var offenders = Types.InAssembly(Domain)
            .That().Inherit(typeof(AggregateRoot))
            .GetTypes()
            .SelectMany(t => t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
            .Where(p => p.SetMethod is { IsPublic: true })
            .Select(p => $"{p.DeclaringType!.Name}.{p.Name}")
            .ToList();

        offenders.Should().BeEmpty("خصائص الـaggregate تُعدَّل عبر السلوك فقط: {0}", string.Join(", ", offenders));
    }

    [Fact]
    public void Handlers_are_sealed_and_have_single_dependency_source()
    {
        var result = Types.InAssembly(Application)
            .That().HaveNameEndingWith("Handler")
            .Should().BeSealed()
            .GetResult();

        result.IsSuccessful.Should().BeTrue(FailureList(result));
    }

    private static string FailureList(ArchTestResult result) =>
        "المخالفات: " + string.Join(", ", result.FailingTypeNames?.Take(15) ?? []);
}
'''},
            {"type": "callout", "kind": "note", "title": "متى Clean Architecture مبالغة؟",
             "md": """
- **أداة سطر أوامر صغيرة / سكربت / نموذج أولي** → مشروع واحد ومجلدات. التكلفة > العائد.
- **CRUD بلا قواعد عمل** (لوحة إدارة، تقرير) → طبقات كاملة = نسخ ولصق بين DTO وEntity بلا فائدة.
  استخدم بنية أبسط (Feature folders داخل مشروع واحد).
- **فريق من شخص واحد ولمدة شهرين** → الحدود بتحميك من نفسك، لكنها بتبطئك؛ خذ القرار بوعي وسجّله في ADR.

القاعدة: **العمارة تتناسب مع تعقيد المجال وعمر المشروع وحجم الفريق**. ابدأ بسيط،
وأضف حدودًا لما يظهر الألم (اختبارات بطيئة، تغييرات بتكسر حاجات بعيدة، فرق متعددة).
"""},
            {"type": "heading", "level": 2, "text": "5) Repository مقابل DbContext مباشرة"},
            {"type": "table", "head": ["الحالة", "القرار", "السبب"], "rows": [
                ["Domain فيه سلوك وقواعد حقيقية", "✓ Repository خلف منفذ", "يحمي Domain من EF ويخلي الاختبارات بلا قاعدة"],
                ["CRUD بسيط على جداول", "✗ DbContext مباشرة في الـHandler", "Repository بيصير غلاف شفاف = طبقة بلا قيمة (درس 1.1.1)"],
                ["مسار قراءة ساخن يحتاج Dapper/projection معقدة", "✓ منفذ read-model مخصص", "`IOrderReadModel` (درس 3.1.3) — مش repository عام"],
                ["اختبارات وحدة للـDomain", "✓ لا repository ولا DbContext", "اختبر الكيان نفسه (بلا أي mock)"],
                ["اختبارات تكامل للـHandlers", "✓ DbContext حقيقي + Testcontainers", "mock الـrepository بيخفي أخطاء EF الفعلية"],
                ["تحتاج `IQueryable` في Application", "△ بحذر شديد", "بيسرّب EF لـApplication؛ لو لازم، استخدم Specification pattern أو منفذ ضيق"],
            ]},
            {"type": "checkpoints", "items": [
                "أرسم اتجاه الاعتماد (Domain ← Application ← Infrastructure/Api) وأمنع عكسه بمراجع المشاريع واختبارات معمارية.",
                "أوزّع الكود صح: قواعد العمل في Domain بسلوك، حالات الاستخدام في Application، التفاصيل التقنية في Infrastructure.",
                "أتجنب Anemic Domain Model: setters خاصة، أحداث مجال، واستثناءات مجال تُترجم في طبقة التسليم.",
                "أعرّف Repository فقط لما بيضيف قيمة، وأختبر التكامل بـDbContext حقيقي بدل mock.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `IClock` (منفذ للزمن) معرّف في Domain مش في Infrastructure؟",
                 "options": [
                     "عشان الأداء",
                     "لأن Domain محتاج الزمن لتطبيق قواعده (CreatedAt/CancelledAt)، والاتجاه الصحيح هو تعريف العقد في الداخل والتنفيذ في الخارج",
                     "عشان DateTime بطيء",
                     "متطلب EF Core",
                 ], "answer": 1,
                 "explain": "ده جوهر Dependency Inversion: الطبقة الداخلية تعرّف **ما تحتاجه**، والخارجية تنفّذه. النتيجة: اختبارات Domain بتتحكم في الزمن."},
                {"q": "`Order` فيه `public string Status { get; set; }` و`OrderService` بيعدّله. المشكلة الأساسية؟",
                 "options": [
                     "الأداء",
                     "Anemic Domain Model: قواعد الانتقال بين الحالات مش محمية — أي كود يقدر يخالفها",
                     "حجم الملف",
                     "محتاج interface",
                 ], "answer": 1,
                 "explain": "الإصلاح: `private set` + methods (`Cancel()`/`Ship()`) بترفع استثناء لو الانتقال غير مسموح، واختبارات وحدة للقواعد دي."},
                {"q": "استثناء `InsufficientStockException` يُرمى من Domain — مين يحوّله لـ409؟",
                 "options": [
                     "Domain نفسه (يرجع كود HTTP)",
                     "طبقة Api عبر `IExceptionHandler` (درس 2.1.4) — Domain لا يعرف شيئًا عن HTTP",
                     "Infrastructure",
                     "المترجم",
                 ], "answer": 1,
                 "explain": "لو Domain عرف HTTP/StatusCode، بقي معتمدًا على ASP.NET → كسرنا Dependency Rule واختبارات Domain بقت تحتاج ويب."},
                {"q": "متى Repository بيصير طبقة بلا قيمة؟",
                 "options": [
                     "دائمًا",
                     "لما بيكون غلاف شفاف لـDbContext في CRUD بسيط (Find/Save بلا منطق) — `DbContext` نفسه هو UoW + Repository",
                     "لما فيه Domain غني",
                     "لما نستخدم Testcontainers",
                 ], "answer": 1,
                 "explain": "القاعدة: أضف abstraction لما فيه سبب (حماية Domain، استبدال، مسار قراءة مختلف). بلا سبب = boilerplate وصيانة إضافية."},
                {"q": "اختبار تكامل لـ`CancelOrderHandler` — إزاي تجهز `IOrderRepository`؟",
                 "options": [
                     "Mock بـNSubstitute",
                     "DbContext حقيقي (Testcontainers/Postgres) مع الـadapter الحقيقي — عشان تختبر التخطيط والاستعلامات فعليًا",
                     "In-memory provider",
                     "لا تختبره",
                 ], "answer": 1,
                 "explain": "mock الـrepository بيثبت إن كودك بينادي الـmock صح، مش إن الاستعلام يشتغل. الـmockات للوحدات المعزولة (ساعة، عميل خارجي)."},
                {"q": "`Shop.Application` فيه `using Microsoft.EntityFrameworkCore;` — ده يعني إيه؟",
                 "options": [
                     "عادي",
                     "كسر للمعمارية: تفاصيل تقنية تسربت لطبقة حالات الاستخدام (اختباراتك بقت تحتاج قاعدة، وأي تغيير في EF بيوصل لجوه)",
                     "تحسين أداء",
                     "مطلوب لـInclude",
                 ], "answer": 1,
                 "explain": "اختبار المعمارية بيرفضه تلقائيًا (`HaveDependencyOnAny` بيمنع `Microsoft.EntityFrameworkCore`). الحل: نقل الكود لـInfrastructure خلف منفذ."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "أعد هيكلة aggregate واحد",
                 "md": "اختار أهم كيان في مشروعك وانقله لنموذج غني: setters خاصة، methods للسلوك مع فرض القواعد، Domain Events، واستثناءات مجال. حدّث الـhandlers والـAPI، وأضف اختبارات وحدة للقواعد.",
                 "criteria": [
                     "لا `public set` على خصائص الـaggregate (اختبار معماري يثبتها)",
                     "كل انتقال حالة ممنوع بيرفع استثناء مجال، مع اختبار وحدة لكل حالة",
                     "اختبارات Domain تشتغل بلا قاعدة بيانات ولا mocks وفي أقل من ثانية",
                     "الـhandler بقى تنسيقًا فقط (لا `if` يخص قواعد العمل)",
                     "ترجمة استثناءات المجال لـHTTP في `IExceptionHandler` (مش في Domain)",
                     "لا attributes تقنية (EF/JSON) على أنواع الـDomain",
                 ],
                 "hint": "لو EF بيشتكي من الـconstructors الخاصة: أضف `private` constructor فاضي واستخدم `HasColumnName`/shadow properties في `IEntityTypeConfiguration` داخل Infrastructure."},
                {"id": "t2", "title": "اختبارات معمارية في CI",
                 "md": "أضف مشروع `ArchTests` بقواعد: Domain بلا اعتماد تقني، Application بلا Infrastructure/EF، handlers sealed، ولا public setters في الـaggregates. شغّلها في CI كخطوة إلزامية.",
                 "criteria": [
                     "4 قواعد معمارية على الأقل، كل واحدة برسالة فشل تشرح القاعدة والمخالفة",
                     "الاختبار يفشل فعلًا عند مخالفة مفتعلة (جرّب وأثبت في الـPR)",
                     "خطوة في GitHub Actions تشغّل `ArchTests` قبل النشر",
                     "قاعدة إضافية تخص مشروعك (تسمية، مكان DTOs، منع `IQueryable` في Application)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET architecture guides (MS Learn)", "url": "https://learn.microsoft.com/dotnet/architecture/"},
                {"label": "Clean Architecture example — eShop", "url": "https://github.com/dotnet-architecture/eShop"},
                {"label": "ardaris/CleanArchitecture", "url": "https://github.com/ardaris/CleanArchitecture"},
                {"label": "The Clean Architecture (Uncle Bob)", "url": "https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html"},
                {"label": "NetArchTest", "url": "https://github.com/BenMorris/NetArchTest"},
                {"label": "Repository & Unit of Work pattern", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s4-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
في الطبقات الأفقية (الدرس السابق)، إضافة ميزة «إلغاء طلب» بتلمس: `Domain/Order.cs`،
`Application/Orders/CancelOrder.cs`، `Application/IOrderRepository.cs`، `Infrastructure/EfOrderRepository.cs`،
`Api/OrdersEndpoints.cs`، و3 ملفات اختبارات في 3 مشاريع. **6 ملفات في 4 مشاريع** عشان ميزة واحدة.

الـ**Vertical Slice** بيعكس التنظيم: بدل ما تنظّم بالتقنية (Controllers/Services/Repositories)،
نظّم **بالميزة** — كل slice فيها كل ما يخص حالة استخدام واحدة، غالبًا في ملف واحد.
ده مش بديل عن الـDomain؛ ده تنظيم **طبقة التطبيق والتسليم**.
"""},
            {"type": "terms", "items": [
                {"term": "Vertical Slice", "def": "شريحة رأسية = حالة استخدام كاملة (endpoint + handler + DTO + validation + tests) في مكان واحد."},
                {"term": "Feature Folder", "def": "مجلد لكل ميزة (`Features/Orders/Cancel/`) بدل مجلد لكل تقنية (`Controllers/`, `Services/`)."},
                {"term": "Cohesion by feature", "def": "الأشياء اللي بتتغير معًا تقع معًا — تغيير ميزة = تعديل ملف واحد غالبًا."},
                {"term": "Endpoint Filter / Group", "def": "آلية Minimal APIs لربط slice بمسار وسياسات (auth، validation، cache) — درس 2.1.x."},
                {"term": "Mediator (MediatR)", "def": "وسيط يفصل المُرسِل عن المعالج: `ISender.Send(command)`. اختياري في الـslices — أحيانًا handler مباشر أوضح."},
                {"term": "Shared Kernel", "def": "الحد الأدنى المشترك بين الشرائح (Domain، value objects، helpers). لازم يبقى صغير ومراقب."},
                {"term": "Feature Envy / Duplication", "def": "أكبر مخاطر الـslices: نفس القاعدة تظهر في 3 شرائح. الحل: انقلها لـDomain أو shared kernel."},
                {"term": "Contract Test", "def": "اختبار يثبت إن الشرائح المختلفة بتتفق على نفس السلوك لقاعدة مشتركة (يمنع التفرّق الصامت)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) slice كامل في ملف واحد"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Api/Features/Orders/CancelOrder.cs", "title": "endpoint + command + handler + validator + response — كلها معًا", "code": r'''
using Shop.Domain.Orders;
using Shop.Domain.Shared;

namespace Shop.Api.Features.Orders.CancelOrder;

// ═════════════ ① العقد (Contract) ═════════════
public sealed record Request(Guid OrderId, string Reason);
public sealed record Response(Guid OrderId, string Status, DateTimeOffset CancelledAt);

// ═════════════ ② الـEndpoint (التسليم) ═════════════
public static class Endpoint
{
    public static void Map(IEndpointRouteBuilder app) =>
        app.MapPost("/orders/{orderId:guid}/cancel", Handle)
           .WithName("CancelOrder")
           .WithTags("Orders")
           .WithSummary("يلغي طلبًا بحسب قواعد المجال")
           .RequireAuthorization("Orders.Write")
           .Produces<Response>(StatusCodes.Status200OK)
           .ProducesProblem(StatusCodes.Status404NotFound)
           .ProducesProblem(StatusCodes.Status409Conflict)
           .AddEndpointFilter(async (ctx, next) =>            // ★ validation محلي للـslice
           {
               var request = ctx.Arguments.OfType<Request>().FirstOrDefault();
               if (request is null) return await next(ctx);

               var result = await new Validator().ValidateAsync(request, ctx.HttpContext.RequestAborted);
               return result.IsValid ? await next(ctx)
                                     : Results.ValidationProblem(result.ToDictionary());
           });

    private static async Task<IResult> Handle(
        Request request, Guid orderId, ISender sender, CancellationToken ct)
    {
        if (request.OrderId != orderId)
            return Results.Problem(statusCode: 400, detail: "عدم تطابق بين المسار والجسم");

        var result = await sender.Send(request with { OrderId = orderId }, ct);
        return Results.Ok(result);
    }
}

// ═════════════ ③ التحقق من المدخلات ═════════════
public sealed class Validator : AbstractValidator<Request>
{
    public Validator()
    {
        RuleFor(x => x.OrderId).NotEmpty();
        RuleFor(x => x.Reason).NotEmpty().MaximumLength(500)
            .WithMessage("سبب الإلغاء مطلوب (500 حرف كحد أقصى)");
    }
}

// ═════════════ ④ حالة الاستخدام (Application) ═════════════
public sealed class Handler(
    AppDbContext db, IClock clock, ILogger<Handler> log) : IRequestHandler<Request, Response>
{
    public async Task<Response> Handle(Request request, CancellationToken ct)
    {
        var order = await db.Orders
            .Include(o => o.Lines)
            .FirstOrDefaultAsync(o => o.Id == request.OrderId, ct)
            ?? throw new OrderNotFoundException(request.OrderId);

        order.Cancel(request.Reason, clock);          // ★ القاعدة لسه في Domain — مش هنا

        await db.SaveChangesAsync(ct);                // يحفظ + يكتب أحداث الـoutbox

        log.LogInformation("order {OrderId} cancelled", order.Id);
        return new Response(order.Id, order.Status.ToString(), order.CancelledAt!.Value);
    }
}

// ═════════════ ⑤ أخطاء الـslice (تُترجم مركزياً) ═════════════
public sealed class OrderNotFoundException(Guid id) : Exception($"الطلب {id} غير موجود");
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Api/Program.cs", "title": "التسجيل: خريطة الشرائح + اكتشاف تلقائي", "code": r'''
var builder = WebApplication.CreateBuilder(args);

// البنية التحتية المشتركة (Domain/Infrastructure لسه مشاريع منفصلة)
builder.Services.AddShopPersistence(builder.Configuration);
builder.Services.AddShopMessaging(builder.Configuration);
builder.Services.AddProblemDetails().AddExceptionHandler<GlobalExceptionHandler>();

// ★ MediatR: يفحص التجميعات ويسجل كل الـhandlers/validators
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<Program>());
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

var app = builder.Build();
app.UseExceptionHandler();

// الخيار أ: تسجيل صريح (واضح، سهل التتبع، بلا سحر)
var orders = app.MapGroup("/api").RequireAuthorization();
Shop.Api.Features.Orders.CancelOrder.Endpoint.Map(orders);
Shop.Api.Features.Orders.PlaceOrder.Endpoint.Map(orders);
Shop.Api.Features.Orders.ListOrders.Endpoint.Map(orders);
Shop.Api.Features.Catalog.SearchProducts.Endpoint.Map(orders);

// الخيار ب: اكتشاف تلقائي (أقل boilerplate، أقل وضوحًا)
// app.MapSlicesFromAssembly(typeof(Program).Assembly);   // عبر reflection على أنواع IEndpointFeature

app.Run();

/// <summary>عقد موحّد لو اخترت الاكتشاف التلقائي.</summary>
public interface IEndpointFeature
{
    static abstract void Map(IEndpointRouteBuilder app);
}
'''},
            {"type": "heading", "level": 2, "text": "2) المقارنة الصريحة"},
            {"type": "table", "head": ["المعيار", "طبقات أفقية (Clean)", "Vertical Slice"], "rows": [
                ["تغيير ميزة واحدة", "6+ ملفات في 3-4 مشاريع", "**ملف 1-2** في مجلد الميزة"],
                ["اكتشاف الكود", "«فين منطق الإلغاء؟» → تدور في الطبقات", "«Features/Orders/Cancel» → كل شيء هنا"],
                ["فرض الحدود", "**قوي** (مشاريع منفصلة + اختبارات معمارية)", "أضعف (كل شيء في نفس التجميع) — يحتاج اختبارات/اتفاقيات"],
                ["إعادة الاستخدام", "طبيعي عبر الطبقات المشتركة", "خطر التكرار → يحتاج shared kernel منضبط"],
                ["قواعد العمل المعقدة (مجال غني)", "**مناسبة** (Domain واضح ومحمي)", "ممكنة لكن أسهل إنها تتسرب للـhandlers"],
                ["اختبار الوحدة", "مباشر لكل طبقة", "للـhandler (مع DbContext حقيقي) — أقل عزلًا"],
                ["onboarding مطور جديد", "يحتاج فهم الطبقات والاتجاه", "**أسرع**: يقرأ slice كامل ويفهم النمط"],
                ["فرق كبيرة (5+ فرق)", "**أفضل** (حدود مشاريع + CI)", "يحتاج انضباطًا ومراجعة أقوى"],
                ["التحول لميكروسيرفيسز", "أسهل (الطبقات واضحة)", "أسهل **كمان** لو الـslices مجمّعة كموديولات (درس 4.1.3)"],
                ["مناسب أكتر لـ", "أنظمة بمجال معقد وعمر طويل", "APIs بميزات مستقلة وفرق صغيرة/متوسطة"],
            ]},
            {"type": "callout", "kind": "danger", "title": "أكبر خطر في Vertical Slice: تكرار قواعد المجال",
             "md": """
لما كل slice بيكتب منطقها الخاص، القاعدة الواحدة بتظهر في 3 نسخ **بسلوك مختلف**:
`CancelOrder` بيرفض الإلغاء بعد الشحن، و`RefundOrder` ما بيفحصش، و`UpdateOrder` بيتجاهل الحالة خالص.

**الحماية (3 آليات معًا):**
1. **Domain project حقيقي** بكيانات غنية (الدرس السابق) — الـslice بينسّق، والقاعدة في الكيان.
   الـslice بلا Domain = نموذج مجال فقير (anemic) مضروب في عدد الشرائح.
2. **اختبار معماري** يمنع منطق المجال في الـhandlers: مثلًا رفض `if (x.Status == ...)` أو نداء
   أكثر من aggregate داخل handler واحد.
3. **Contract tests** لأي قاعدة مشتركة: اختبار واحد يمر على كل المسارات اللي بتعدل الطلب ويثبت نفس النتيجة.

القاعدة العملية: **slice = تنسيق وتسليم. Domain = قواعد.** لو handler فيه أكتر من `if` يخص حالة كيان → انقله للـDomain.
"""},
            {"type": "heading", "level": 2, "text": "3) التواصل بين الشرائح"},
            {"type": "code", "lang": "csharp", "title": "لا نداء مباشر بين الشرائح — استخدم الأحداث أو Domain", "code": r'''
// ═══ ✗ slice بيتصل بـslice تاني مباشرة ═══
public sealed class BadHandler(CancelOrder.Handler cancelHandler, Notifications.Handler notify)
{
    public async Task Handle(Request r, CancellationToken ct)
    {
        var result = await cancelHandler.Handle(new CancelOrder.Request(r.OrderId, r.Reason), ct);
        await notify.Handle(new Notifications.Request(result.OrderId, "cancelled"), ct);
        // ← اقتران صريح: أي تغيير في slice تاني بيكسر ده، والاختبار بقى معقد
    }
}

// ═══ ✓ الطريقة 1: حدث مجال (مفضل — نفس المعاملة عبر outbox) ═══
public sealed class OrderCancelledHandler(AppDbContext db, IEmailSender email, ILogger<OrderCancelledHandler> log)
    : INotificationHandler<OrderCancelled>
{
    public async Task Handle(OrderCancelled notification, CancellationToken ct)
    {
        log.LogInformation("notify customer for {OrderId}", notification.OrderId);
        await email.SendOrderCancelledAsync(notification.OrderId, ct);
    }
}
// الشريحة اللي بتلغي الطلب ما تعرفش حاجة عن الإشعارات — الـoutbox يضمن التسليم (درس 4.2.3)

// ═══ ✓ الطريقة 2: استعلام مشترك في Application (للقراءة فقط) ═══
public sealed record GetOrderSummaryQuery(Guid OrderId) : IRequest<OrderSummary>;
// slice العرض بينادي الاستعلام (مش handler شريحة تانية) — الاستعلامات عامة بطبيعتها

// ═══ ✓ الطريقة 3: shared kernel للأنواع والـhelpers ═══
// src/Shop.Domain/Shared/Money.cs, IClock.cs, Pagination.cs
// ★ قاعدة: shared kernel يبقى **صغيرًا**؛ كل إضافة له تحتاج مراجعة (وإلا بقى طبقة مخفية)
'''},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.Tests/Features/Orders/CancelOrderTests.cs", "title": "اختبار الـslice: من HTTP للقاعدة في اختبار واحد", "code": r'''
public class CancelOrderSliceTests(PostgresFixture db) : IClassFixture<PostgresFixture>
{
    [Fact]
    public async Task Cancel_shipped_order_returns_409_and_does_not_change_state()
    {
        // Arrange: حالة واقعية كاملة (بلا mocks للـhandler)
        var order = Order.Place(TestData.CustomerId, TestData.Lines(2), new FixedClock());
        order.Ship(new FixedClock());
        await db.SeedAsync(order);

        await using var app = db.CreateWebApplication();          // WebApplicationFactory على قاعدة حقيقية
        var client = app.CreateClient();

        // Act
        var response = await client.PostAsJsonAsync(
            $"/api/orders/{order.Id}/cancel", new { orderId = order.Id, reason = "customer request" });

        // Assert: العقد + الحالة
        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Title.Should().Be("OrderCannotBeCancelled");

        var stored = await db.GetOrderAsync(order.Id);
        stored.Status.Should().Be(OrderStatus.Shipped, "الإلغاء المرفوض ما يغيّرش الحالة");
        stored.CancelledAt.Should().BeNull();
    }

    [Fact]
    public async Task Cancel_placed_order_persists_state_and_writes_outbox_event()
    {
        var order = Order.Place(TestData.CustomerId, TestData.Lines(1), new FixedClock());
        await db.SeedAsync(order);
        await using var app = db.CreateWebApplication();

        var response = await app.CreateClient().PostAsJsonAsync(
            $"/api/orders/{order.Id}/cancel", new { orderId = order.Id, reason = "out of stock" });

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<Response>();
        body!.Status.Should().Be("Cancelled");

        // ★ الذرّية: الحدث في outbox في نفس المعاملة (بلا فقد)
        var outbox = await db.GetOutboxAsync(order.Id);
        outbox.Should().ContainSingle(m => m.Type == "order.cancelled");
        outbox.Single().SentAt.Should().BeNull("المرسل لسه ما اشتغلش");
    }
}
'''},
            {"type": "callout", "kind": "tip", "title": "متى تختار Vertical Slice؟",
             "md": """
**اختاره لو:**
- API بميزات مستقلة نسبيًا (CRUD + عمليات واضحة) وفريق 1-6 مطورين.
- سرعة التسليم ووضوح «فين كود الميزة» أهم من الحدود الصارمة.
- عندك **Domain project غني** تحمي القواعد (شرط، مش رفاهية).

**ابقَ على الطبقات (أو استخدم Modular Monolith) لو:**
- مجال معقد بقواعد متشابكة عبر aggregates كثيرة (تأمين، محاسبة، تسعير متقدم).
- فرق متعددة (5+) بتشتغل على نفس الكود ولازم حدود مفروضة بالـcompiler.
- عندك متطلبات امتثال/مراجعة تفصل المسؤوليات تقنيًا.

**الحل الوسط الشائع والأفضل في مشاريع كتير:** Domain + Application كمشاريع (حدود مفروضة)،
وطبقة التسليم منظمة بـslices داخل مشروع الـAPI. ده بيجمع حماية القواعد وسرعة الميزات.
"""},
            {"type": "checkpoints", "items": [
                "أنظّم الكود بالميزة (slice) وأجمع endpoint/handler/DTO/validator في مكان واحد.",
                "أحافظ على Domain غني وأمنع تسرب قواعد العمل للـhandlers (اختبارات معمارية + contract tests).",
                "أوصل بين الشرائح بالأحداث (outbox) أو الاستعلامات المشتركة، لا بنداء handler مباشر.",
                "أختبر الـslice من HTTP للقاعدة على قاعدة بيانات حقيقية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "الميزة الأساسية لـVertical Slice؟",
                 "options": [
                     "أداء أعلى",
                     "تماسك أعلى: الأشياء التي تتغير معًا تقع معًا → تغيير ميزة = تعديل ملف/ملفين بدل 6 في 4 مشاريع",
                     "بلا اختبارات",
                     "فرض حدود أقوى من الطبقات",
                 ], "answer": 1,
                 "explain": "التكلفة: حدود أضعف (نفس التجميع) وخطر تكرار القواعد. الحدود الأقوى لسه من نصيب مشاريع منفصلة + اختبارات معمارية."},
                {"q": "slice بيحتوي `if (order.Status == OrderStatus.Placed) { ... }` لتحديد هل يُسمح بالخصم. الحكم؟",
                 "options": [
                     "عادي — ده مكانه",
                     "قاعدة مجال تسربت للـhandler: انقلها لـ`Order` كـmethod (مثل `CanDiscount()`) واختبرها هناك",
                     "حوّلها لـvalidator",
                     "احذفها",
                 ], "answer": 1,
                 "explain": "لو القاعدة دي مستخدمة في slice تاني كمان، هتتكرر بسلوك مختلف — وده أسوأ سيناريو في الـslices."},
                {"q": "slice للإلغاء محتاج يبعت إيميل. أفضل توصيل؟",
                 "options": [
                     "ينادي handler شريحة الإشعارات مباشرة",
                     "يرفع `OrderCancelled` (يُكتب في outbox في نفس المعاملة) ومستهلك مستقل يبعت الإيميل",
                     "يكتب الإيميل داخل نفس الـhandler",
                     "يستخدم event bus خارجي مباشرة بلا outbox",
                 ], "answer": 1,
                 "explain": "الحدث بيفصل الشرائح، والـoutbox بيضمن عدم الفقد لو سقطت العملية بعد الالتزام. النشر المباشر بلا outbox = رسائل ضائعة عند الفشل."},
                {"q": "MediatR في الـslices — لازم؟",
                 "options": [
                     "نعم دائمًا",
                     "لا: مفيد لفصل المرسل عن المعالج ولـpipelines (validation/logging/transactions)، لكن handler مباشر + interface ضيق أوضح في حالات كتير",
                     "ممنوع",
                     "يحل محل Domain",
                 ], "answer": 1,
                 "explain": "التكلفة: سحر (reflection/IL emit)، stack traces أطول، وindirection. قيمته الحقيقية في الـbehaviors المشتركة (validation, transactions, logging) — استخدمه لما تحتاجها."},
                {"q": "Shared Kernel (المشترك بين الشرائح) — القاعدة الصحيحة؟",
                 "options": [
                     "حط فيه كل ما يتكرر",
                     "يبقى صغيرًا ومراجعًا: أنواع مجال نقية وhelpers ثابتة؛ أي منطق عمل يدخله يحتاج مراجعة لأنه بيبقى طبقة مخفية",
                     "احذفه بالكامل",
                     "اجعله مشروع Infrastructure",
                 ], "answer": 1,
                 "explain": "shared kernel ضخم = طبقة «Common» اللي الكل بيعتمد عليها وكل تغيير فيها بيكسر كل حاجة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "حوّل ميزتين إلى slices",
                 "md": "اختار ميزتين موجودتين (واحدة كتابة وواحدة قراءة) وأعد تنظيمهما كـslices كاملة (endpoint + handler + DTO + validator + tests في مجلد الميزة). قارن عدد الملفات المعدّلة قبل/بعد في تقرير قصير.",
                 "criteria": [
                     "كل slice في مجلد/ملف واحد مع عقد واضح (Request/Response records)",
                     "validation مربوط بالـslice (endpoint filter) ويرجع 400 بشكل متسق",
                     "OpenAPI يعرض الميزتين بشكل صحيح (tags/summaries/Produces)",
                     "قواعد العمل لسه في Domain (اختبار معماري يثبت إن الـhandler بلا منطق حالة)",
                     "اختبار slice واحد على الأقل من HTTP للقاعدة على Postgres حقيقي",
                     "تقرير: عدد الملفات المعدّلة لإضافة حقل جديد قبل/بعد",
                 ],
                 "hint": "لو الميزة القراءة معقدة (تقارير/joins): اعمل slice بيستخدم read-model منفذ (Dapper من درس 3.1.3) بدل ما تحشر الاستعلام في الـhandler."},
                {"id": "t2", "title": "حارس ضد تكرار القواعد",
                 "md": "أضف اختبار contract يثبت إن كل المسارات اللي بتعدّل حالة الطلب بتطبق نفس القاعدة (مثلًا: لا يمكن تعديل/إلغاء/خصم بعد الشحن)، واختبار معماري يمنع منطق الحالة في الـhandlers.",
                 "criteria": [
                     "اختبار `[Theory]` يمر على كل endpoints تعديل الطلب ويثبت نفس الاستجابة (409) للحالة الممنوعة",
                     "اختبار معماري يفشل لو handler فيه مقارنة حالة (`Status ==`) أو تعديل مباشر لخصائص aggregate",
                     "الاختباران في CI",
                     "ملاحظة في README: «القواعد في Domain، الشرائح تنسّق» + مثال صحيح/خاطئ",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Vertical Slice Architecture (Jimmy Bogard)", "url": "https://www.jimmybogard.com/vertical-slice-architecture/"},
                {"label": "Minimal APIs — Endpoint filters & groups", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis"},
                {"label": "MediatR", "url": "https://github.com/jbogard/MediatR"},
                {"label": "FluentValidation", "url": "https://docs.fluentvalidation.net/"},
                {"label": "Feature Folders discussion", "url": "https://learn.microsoft.com/dotnet/architecture/modern-web-apps-azure/architectural-principles"},
            ]},
        ],
    },
]
