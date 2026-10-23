"""Stage 4, Module 2 — DDD & CQRS (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S4_C = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s4-m2-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
DDD التكتيكي هو مجموعة أنماط بتجاوب على سؤال واحد: **فين تقع قاعدة العمل، وإيه حدود الوحدة اللي
لازم تكون متسقة في لحظة واحدة؟**

الأنماط دي (Value Object، Entity، Aggregate، Domain Event، Domain Service، Repository) مش زخرفة —
كل واحد بيحل مشكلة حقيقية: Primitive Obsession بيخليك تكرر نفس التحقق في 12 مكان،
والـAggregate الكبير بيخلي كل طلب يقفل صفوف كتير، وبلا Domain Events بتوصل لاتصالات متشابكة بين الموديولات.

هنا نبنيهم بكود حقيقي على Postgres/EF Core 10، مع الاختبارات اللي بتثبت القواعد.
"""},
            {"type": "terms", "items": [
                {"term": "Ubiquitous Language", "def": "لغة موحدة بين الفريق والكود. لو البيزنس بيقول «عميل» والكود فيه `User` → كل محادثة بتحتاج ترجمة، والأخطاء بتتسرب."},
                {"term": "Value Object (VO)", "def": "كائن بلا هوية: المساواة بالقيمة، غير قابل للتعديل، بيتحقق من نفسه. `Money`، `Address`، `DateRange`، `Email`."},
                {"term": "Primitive Obsession", "def": "استخدام `decimal`/`string` مكان المفاهيم → التحقق والتحويل والعمليات مبعثرة وبلا ضمان."},
                {"term": "Entity", "def": "كائن له هوية تستمر عبر الزمن؛ المساواة بالمعرّف مش بالخصائص."},
                {"term": "Aggregate", "def": "مجموعة كيانات وVOs تُعامل كوحدة **للتناسق** (consistency boundary). لها جذر واحد."},
                {"term": "Aggregate Root", "def": "الكيان الوحيد المسموح الوصول له من بره. كل التعديلات تمر به، وهو اللي بيحمي الـinvariants."},
                {"term": "Invariant", "def": "قاعدة لازم تفضل صحيحة دايمًا داخل الـaggregate (المجموع = مجموع السطور، الحالة تسمح بالعملية، الكمية ≥ 1)."},
                {"term": "Transactional Boundary", "def": "القاعدة الذهبية: **aggregate واحد لكل معاملة**. لو محتاج تعديل اتنين → اتساق eventual عبر حدث."},
                {"term": "Domain Event", "def": "حاجة حصلت في المجال (بصيغة الماضي): `OrderPlaced`. يُرفع من الجذر ويُكتب في outbox عند الالتزام."},
                {"term": "Domain Service", "def": "منطق مجال لا ينتمي لكيان واحد (يخص عدة aggregates أو قاعدة خارجية) — بلا حالة (stateless)."},
                {"term": "Repository", "def": "تجريد يشبه المجموعة **لجذر aggregate واحد** — لا repository لكل جدول."},
                {"term": "Factory", "def": "إنشاء aggregate معقد بطريقة صحيحة (غالبًا static factory method داخل الجذر)."},
                {"term": "Eventual Consistency", "def": "الاتساق عبر الـaggregates يتم لاحقًا عبر أحداث — مش في نفس المعاملة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) Value Objects: نهاية Primitive Obsession"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Shared/Money.cs", "title": "VO كامل: تحقق + عمليات + مساواة + تسلسل", "code": r'''
namespace Shop.Domain.Shared;

/// <summary>
/// Value Object: بلا هوية، غير قابل للتعديل، بيتحقق من نفسه.
/// `readonly record struct` = مساواة بالقيمة تلقائيًا + صفر تخصيص + لا يمكن تعديله.
/// </summary>
public readonly record struct Money(decimal Amount, string Currency)
    : IComparable<Money>, IFormattable
{
    public static readonly Money Zero = new(0m, "EGP");

    // ★ التحقق في الـconstructor: مستحيل يوجد Money غير صالح في أي مكان في النظام
    public Money
    {
        if (Amount < 0m) throw new ArgumentOutOfRangeException(nameof(Amount), "المبلغ لا يمكن أن يكون سالبًا");
        if (string.IsNullOrWhiteSpace(Currency)) throw new ArgumentException("العملة مطلوبة", nameof(Currency));
        if (Currency.Length != 3) throw new ArgumentException("رمز العملة 3 أحرف (ISO 4217)", nameof(Currency));

        Currency = Currency.Trim().ToUpperInvariant();
        Amount = Math.Round(Amount, 2, MidpointRounding.AwayFromZero);   // تطبيع: 10.005 → 10.01
    }

    // ── عمليات آمنة: تمنع خلط العملات في وقت الترجمة تقريبًا وفي التشغيل قطعًا ──
    public Money Add(Money other) => WithSameCurrency(other, (a, b) => new Money(a.Amount + b.Amount, a.Currency));
    public Money Subtract(Money other) => WithSameCurrency(other, (a, b) =>
    {
        var v = a.Amount - b.Amount;
        return v < 0 ? throw new InvalidOperationException("الناتج سالب: استخدم Refund بدل الخصم") : new Money(v, a.Currency);
    });
    public Money Multiply(decimal factor) => new(Amount * factor, Currency);
    public Money Multiply(int quantity) => new(Amount * quantity, Currency);

    public bool IsZero => Amount == 0m;
    public int CompareTo(Money other) => WithSameCurrency(other, (a, b) => a.Amount.CompareTo(b.Amount));
    public static bool operator >(Money a, Money b) => a.CompareTo(b) > 0;
    public static bool operator <(Money a, Money b) => a.CompareTo(b) < 0;
    public static bool operator >=(Money a, Money b) => a.CompareTo(b) >= 0;
    public static bool operator <=(Money a, Money b) => a.CompareTo(b) <= 0;
    public static Money operator +(Money a, Money b) => a.Add(b);
    public static Money operator -(Money a, Money b) => a.Subtract(b);

    private T WithSameCurrency<T>(Money other, Func<Money, Money, T> op) =>
        Currency != other.Currency
            ? throw new CurrencyMismatchException(Currency, other.Currency)
            : op(this, other);

    public string ToString(string? format, IFormatProvider? provider = null) =>
        $"{Amount.ToString(format ?? "N2", provider)} {Currency}";

    public override string ToString() => ToString("N2", CultureInfo.InvariantCulture);

    public static Money Parse(string text)
    {
        var parts = text.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length == 2
            ? new Money(decimal.Parse(parts[0], CultureInfo.InvariantCulture), parts[1])
            : throw new FormatException($"صيغة Money غير صالحة: '{text}' (المتوقع '10.50 EGP')");
    }
}

public sealed class CurrencyMismatchException(string a, string b)
    : InvalidOperationException($"لا يمكن الجمع بين عملتين مختلفتين: {a} و{b}");
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Shared/ValueObjects.cs", "title": "VOs تانية: Email، DateRange، Address", "code": r'''
/// <summary>VO بنمط تحقق — بديل عن تكرار Regex في كل DTO.</summary>
public readonly record struct Email(string Value)
{
    public Email
    {
        if (string.IsNullOrWhiteSpace(Value)) throw new ArgumentException("البريد مطلوب", nameof(Value));
        Value = Value.Trim().ToLowerInvariant();
        if (Value.Length > 320 || !Value.Contains('@') || Value.Contains(' '))
            throw new FormatException($"بريد غير صالح: {Value}");
    }
    public string Domain => Value[(Value.IndexOf('@') + 1)..];
    public static bool TryCreate(string? input, out Email email)
    {
        try { email = new Email(input ?? string.Empty); return true; }
        catch (Exception) { email = default; return false; }
    }
}

/// <summary>VO لفترة زمنية — القواعد (بداية قبل نهاية، لا فترات صفرية) مضمونة دائمًا.</summary>
public readonly record struct DateRange(DateOnly From, DateOnly To)
{
    public DateRange
    {
        if (To < From) throw new ArgumentException($"النهاية {To} قبل البداية {From}", nameof(To));
    }
    public int Days => To.DayNumber - From.DayNumber + 1;
    public bool Contains(DateOnly d) => d >= From && d <= To;
    public bool Overlaps(DateRange other) => From <= other.To && other.From <= To;
    public static DateRange LastDays(int days, DateOnly today) => new(today.AddDays(-days + 1), today);
}

/// <summary>VO مركّب — لاحظ إن التحقق بيحمي القاعدة كاملة («مدينة بلا بلد» مستحيلة).</summary>
public readonly record struct Address(
    string Line1, string City, string Country, string? PostalCode = null)
{
    public Address
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(Line1);
        ArgumentException.ThrowIfNullOrWhiteSpace(City);
        ArgumentException.ThrowIfNullOrWhiteSpace(Country);
        if (Country.Length != 2) throw new ArgumentException("رمز البلد حرفان (ISO 3166)", nameof(Country));
        Line1 = Line1.Trim(); City = City.Trim(); Country = Country.Trim().ToUpperInvariant();
    }
}

// ✗ المقابل (Primitive Obsession): decimal total; string currency; string email; DateTime from, to;
//    string addressLine1, city, country, postalCode;
//    → نفس التحقق مكرر في 12 مكان، وممكن توصل حالة غير صالحة من أي مسار.
'''},
            {"type": "callout", "kind": "tip", "title": "Value Objects في EF Core 10: 3 طرق",
             "md": """
| الطريقة | الكود | متى |
|---|---|---|
| **Complex type** (EF 10) | `builder.ComplexProperty(o => o.Total)` → أعمدة مسطّحة `total_amount`, `total_currency` | ★ الأفضل للـVOs الصغيرة داخل الـaggregate (لا هوية، ولا تُقرأ منفصلة) |
| **Owned entity** | `builder.OwnsOne(o => o.Address, a => a.Property(x => x.City).HasColumnName("city"))` | VO له حقول كتير أو محتاج جدول خاص/JSON |
| **JSON column** | `builder.OwnsOne(o => o.Address).ToJson()` | بيانات متغيرة الشكل/نادرة الفلترة |
| **Value Converter** | `builder.Property(o => o.Total).HasConversion(...)` | VO بسيط يُخزَّن في عمود واحد (`Email` في `text`) |

راجع درس 3.2.2 للمقارنة التفصيلية والقيود. الأهم: **الـVO يفضل VO في الـDomain** —
التخزين قرار بنية تحتية في `IEntityTypeConfiguration` داخل Infrastructure.
"""},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/Persistence/Configurations/OrderConfiguration.cs", "title": "تخطيط VO في البنية التحتية (Domain لا يعرف EF)", "code": r'''
public sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> b)
    {
        b.ToTable("orders", "orders");
        b.HasKey(o => o.Id);
        b.Property(o => o.Id).ValueGeneratedNever();

        // ★ complex type (EF 10): أعمدة مسطّحة بلا كيان منفصل
        b.ComplexProperty(o => o.Total, money =>
        {
            money.Property(m => m.Amount).HasColumnName("total_amount").HasPrecision(18, 2);
            money.Property(m => m.Currency).HasColumnName("total_currency").HasMaxLength(3).IsFixedLength();
        });

        // ✓ VO بسيط في عمود واحد: value converter
        b.Property(o => o.CustomerEmail)
         .HasConversion(v => v.Value, v => new Email(v))
         .HasMaxLength(320);

        // ✓ Address مدمج كـJSON (يتغير شكله نادرًا ولا يُفلتر به)
        b.ComplexProperty(o => o.ShippingAddress).ToJson();

        b.Property(o => o.Status).HasConversion<string>().HasMaxLength(24);
        b.HasIndex(o => new { o.Status, o.CreatedAt, o.Id })
         .IncludeProperties(o => new { o.Total, o.CustomerId })       // فهرس مغطّي (درس 3.1.1)
         .HasDatabaseName("ix_orders_status_created_covering");

        // الـaggregate الداخلي: owned collection (لا يُقرأ ولا يُكتب منفصلًا)
        b.OwnsMany(o => o.Lines, line =>
        {
            line.ToTable("order_lines", "orders");
            line.WithOwner().HasForeignKey("OrderId");
            line.HasKey("OrderId", "ProductId");
            line.Property(l => l.Quantity);
            line.ComplexProperty(l => l.UnitPrice, m =>
            {
                m.Property(x => x.Amount).HasColumnName("unit_price_amount").HasPrecision(18, 2);
                m.Property(x => x.Currency).HasColumnName("unit_price_currency").HasMaxLength(3);
            });
        });
        b.Navigation(o => o.Lines).UsePropertyAccessMode(PropertyAccessMode.Field);   // ✓ الوصول للحقل الخاص
    }
}
'''},
            {"type": "heading", "level": 2, "text": "2) Aggregates: حدود التناسق والمعاملة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Orders/Order.cs", "title": "جذر aggregate يحمي الـinvariants ويرفع الأحداث", "code": r'''
namespace Shop.Domain.Orders;

/// <summary>
/// Aggregate Root: `Order` + `OrderLine`s.
/// الحدود: كل قواعد الطلب (الحالة، المجموع، عدم تكرار المنتج، حد السطور) مفروضة هنا **دائمًا**.
/// ما خارج الحدود (`Customer`, `Product`, `Shipment`) = aggregates أخرى → **معرّفات فقط**، لا مراجع كائنات.
/// </summary>
public class Order : AggregateRoot
{
    public const int MaxLines = 50;

    private readonly List<OrderLine> _lines = [];

    public Guid Id { get; private init; }
    public Guid CustomerId { get; private init; }          // ★ معرّف فقط — لا `Customer Customer`
    public Email CustomerEmail { get; private init; }
    public OrderStatus Status { get; private set; }
    public Money Total { get; private set; }
    public Address ShippingAddress { get; private set; }
    public DateTimeOffset CreatedAt { get; private init; }
    public DateTimeOffset? CancelledAt { get; private set; }
    public string? CancellationReason { get; private set; }
    public int Version { get; private set; }               // ★ concurrency token (درس 3.1.2)

    public IReadOnlyList<OrderLine> Lines => _lines;
    public bool CanBeModified => Status == OrderStatus.Placed;

    private Order() { }                                     // EF فقط

    // ── Factory: الإنشاء الصحيح الوحيد ──
    public static Order Place(
        Guid customerId, Email customerEmail, Address shippingAddress,
        IEnumerable<(Guid ProductId, string Name, int Quantity, Money UnitPrice)> lines, IClock clock)
    {
        if (customerId == Guid.Empty) throw new ArgumentException("معرّف العميل مطلوب", nameof(customerId));

        var order = new Order
        {
            Id = Guid.NewGuid(),
            CustomerId = customerId,
            CustomerEmail = customerEmail,
            ShippingAddress = shippingAddress,
            Status = OrderStatus.Placed,
            CreatedAt = clock.UtcNow,
            Version = 1,
        };

        var materialized = lines.ToList();
        if (materialized.Count == 0) throw new EmptyOrderException(order.Id);
        if (materialized.Count > MaxLines) throw new TooManyOrderLinesException(order.Id, materialized.Count, MaxLines);

        foreach (var l in materialized) order.AddLine(l.ProductId, l.Name, l.Quantity, l.UnitPrice);
        order.Recalculate();

        order.Raise(new OrderPlaced(order.Id, order.CustomerId, order.Total, order.ShippingAddress, order.CreatedAt));
        return order;
    }

    // ── السلوك: كل تعديل يمر بقاعدة ──
    public void AddLine(Guid productId, string name, int quantity, Money unitPrice)
    {
        EnsureModifiable();
        if (quantity < 1) throw new ArgumentOutOfRangeException(nameof(quantity), "الكمية ≥ 1");
        if (_lines.Count >= MaxLines && _lines.All(l => l.ProductId != productId))
            throw new TooManyOrderLinesException(Id, _lines.Count + 1, MaxLines);

        var existing = _lines.Find(l => l.ProductId == productId);
        if (existing is not null) existing.IncreaseQuantity(quantity);      // ★ invariant: لا تكرار منتج
        else _lines.Add(new OrderLine(productId, name.Trim(), quantity, unitPrice));

        Recalculate();
        Version++;
    }

    public void ChangeShippingAddress(Address newAddress)
    {
        EnsureModifiable();
        if (Status == OrderStatus.Placed && newAddress.Country != ShippingAddress.Country)
            throw new InvalidOperationException("تغيير بلد الشحن بعد الطلب يحتاج إلغاء وإعادة إنشاء (تختلف الرسوم)");

        ShippingAddress = newAddress;
        Version++;
    }

    public void Cancel(string reason, IClock clock)
    {
        if (Status is OrderStatus.Shipped or OrderStatus.Delivered)
            throw new OrderCannotBeCancelledException(Id, Status);
        ArgumentException.ThrowIfNullOrWhiteSpace(reason);

        Status = OrderStatus.Cancelled;
        CancelledAt = clock.UtcNow;
        CancellationReason = reason.Trim();
        Version++;

        Raise(new OrderCancelled(Id, CustomerId, Total, CancellationReason, CancelledAt.Value));
    }

    public void Ship(IClock clock)
    {
        EnsureTransition(OrderStatus.Placed, OrderStatus.Shipped);
        Status = OrderStatus.Shipped;
        Version++;
        Raise(new OrderShipped(Id, ShippingAddress, clock.UtcNow));
    }

    public void MarkDelivered(IClock clock)
    {
        EnsureTransition(OrderStatus.Shipped, OrderStatus.Delivered);
        Status = OrderStatus.Delivered;
        Version++;
        Raise(new OrderDelivered(Id, Total, clock.UtcNow));
    }

    private void EnsureModifiable()
    {
        if (!CanBeModified)
            throw new OrderCannotBeModifiedException(Id, Status);
    }

    private void EnsureTransition(OrderStatus from, OrderStatus to)
    {
        if (Status != from) throw new InvalidOrderTransitionException(Id, Status, to);
    }

    /// <summary>★ الـinvariant الأساسي: المجموع دايمًا = مجموع السطور (مستحيل يتفارق).</summary>
    private void Recalculate() =>
        Total = _lines.Aggregate(Money.Zero, (sum, l) => sum + l.Subtotal);
}

/// <summary>كيان داخل الـaggregate: له هوية محلية، لكن لا يُوصول له من بره الجذر.</summary>
public class OrderLine
{
    public Guid ProductId { get; private init; }
    public string Name { get; private init; }
    public int Quantity { get; private set; }
    public Money UnitPrice { get; private init; }
    public Money Subtotal => UnitPrice.Multiply(Quantity);
    public const int MaxQuantity = 999;

    internal OrderLine(Guid productId, string name, int quantity, Money unitPrice)
    {
        ProductId = productId; Name = name; UnitPrice = unitPrice; Quantity = quantity;
    }
    private OrderLine() { Name = string.Empty; }

    internal void IncreaseQuantity(int by)
    {
        if (Quantity + by > MaxQuantity)
            throw new InvalidOperationException($"الحد الأقصى للكمية {MaxQuantity} لكل سطر");
        Quantity += by;
    }
}
'''},
            {"type": "table", "head": ["الكائن", "داخل aggregate الطلب؟", "السبب", "التكلفة لو غلط"], "rows": [
                ["`OrderLine`", "✓ داخل", "المجموع invariant يعتمد عليه، ويتغير مع الطلب دائمًا", "—"],
                ["`Address` (الشحن)", "✓ داخل (VO)", "لقطة تاريخية: لازم ما تتغيرش بعد الشحن", "—"],
                ["`Customer`", "✗ بره (معرّف فقط)", "كيان مستقل بحياة أطول، يتعدل من مسارات تانية", "لو داخل: كل طلب بيقفل صف العميل → تنازعات وأداء كارثي"],
                ["`Product`", "✗ بره (معرّف + اسم منسوخ)", "كتالوج مستقل، وحجمه كبير", "لو داخل: تعديل سعر منتج يعدّل ملايين الطلبات"],
                ["`Shipment`", "✗ بره (aggregate مستقل)", "دورة حياة مختلفة (تتبع، ناقل، إعادة شحن)", "لو داخل: تعديل شحنة يلمس aggregate الطلب كله"],
                ["`Payment`", "✗ بره + حدث", "مزود خارجي وحالة مستقلة، ومعاملة واحدة لكل aggregate", "لو داخل: معاملة موزعة مخفية داخل معاملة قاعدة"],
                ["`Invoice`", "✗ بره + حدث", "يُنشأ بعد التسليم، وقد يُعاد إصداره", "لو داخل: aggregate بيكبر بلا حدود"],
            ]},
            {"type": "callout", "kind": "danger", "title": "القاعدة الذهبية: aggregate واحد لكل معاملة",
             "md": """
لو معاملتك بتعدّل `Order` و`Shipment` و`Customer` معًا → حدودك غلط.

**لييه؟** كل aggregate بيُقفل/يُتحقق من إصداره بشكل مستقل؛ تعديل اتنين في معاملة واحدة =
تنازعات (deadlocks)، أقفال أطول، وصعوبة فصلهم لموديولات/خدمات لاحقًا.

**الحل:** عدّل `Order` في المعاملة، وارفع `OrderShipped` → مستهلك في aggregate `Shipment` يعالجه لاحقًا
(idempotent + outbox). ده **اتساق eventual مقصود**، مش خلل.

**استثناء وحيد مقبول:** عمليات صغيرة جدًا ومتلازمة فعلًا (مثل `Order` وسطوره) — ودي داخل aggregate واحد أصلًا.

ولما تختار الحدود: **ابدأ صغيرًا**. aggregate كبير = أقفال أوسع وتنازعات أكتر، وتصغيره لاحقًا أصعب بكتير من تكبيره.
"""},
            {"type": "heading", "level": 2, "text": "3) Domain Events وDomain Services"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Orders/Events.cs", "title": "أحداث: ماضي، غير قابلة للتعديل، وتحمل ما يحتاجه المستهلك", "code": r'''
namespace Shop.Domain.Orders;

// ★ التسمية بصيغة الماضي (حاجة حصلت) — الأوامر بصيغة المصدر/المضارع (PlaceOrder)
public sealed record OrderPlaced(
    Guid OrderId, Guid CustomerId, Money Total, Address ShippingAddress, DateTimeOffset OccurredAt) : IDomainEvent;

public sealed record OrderCancelled(
    Guid OrderId, Guid CustomerId, Money Total, string Reason, DateTimeOffset OccurredAt) : IDomainEvent;

public sealed record OrderShipped(
    Guid OrderId, Address ShippingAddress, DateTimeOffset OccurredAt) : IDomainEvent;

public sealed record OrderDelivered(
    Guid OrderId, Money Total, DateTimeOffset OccurredAt) : IDomainEvent;

// قواعد تصميم الأحداث:
// ① الماضي: `OrderPlaced` لا `PlaceOrder`
// ② غير قابل للتعديل: `sealed record` بلا setters
// ③ ذاتي الاحتواء: يحمل البيانات اللي المستهلك محتاجها (بلا نداء رجوع للقاعدة في كل مستهلك)
// ④ بلا تفاصيل تقنية: لا `DbContext` ولا `HttpRequest` ولا معرّفات اتصال
// ⑤ عقد عام: لو الحدث بيخرج بره الموديول → يصير جزءًا من `Contracts` ولا يتغير تغييرًا كاسرًا
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Domain/Pricing/PricingPolicy.cs", "title": "Domain Service: قاعدة تخص أكتر من aggregate (بلا حالة)", "code": r'''
namespace Shop.Domain.Pricing;

/// <summary>
/// Domain Service: خصم الشحن يعتمد على (إجمالي الطلب + بلد الوجهة + فئة العميل) —
/// لا ينتمي لكيان واحد، ولا يجب أن يسكن في Application (ده **منطق مجال**).
/// ★ بلا حالة (stateless) → يُسجَّل كـsingleton.
/// </summary>
public sealed class ShippingPricingPolicy(IClock clock)
{
    private static readonly Dictionary<string, Money> BaseRates = new()
    {
        ["EG"] = new Money(35m, "EGP"),
        ["SA"] = new Money(180m, "EGP"),
        ["AE"] = new Money(210m, "EGP"),
    };

    public Money Calculate(Money orderTotal, Address destination, CustomerTier tier)
    {
        if (!BaseRates.TryGetValue(destination.Country, out var baseRate))
            throw new UnsupportedDestinationException(destination.Country);    // ★ فشل صريح، لا صفر افتراضي

        var rate = baseRate;

        // قواعد المجال (مش إعدادات تقنية):
        if (orderTotal >= new Money(1500m, orderTotal.Currency)) rate = Money.Zero;    // شحن مجاني فوق حد
        if (tier == CustomerTier.Gold) rate = rate.Multiply(0.5m);                      // خصم فئة
        if (IsPeakSeason(clock.UtcNow)) rate = rate.Multiply(1.25m);                    // موسم الذروة

        return new Money(Math.Round(rate.Amount, 2), rate.Currency);
    }

    private static bool IsPeakSeason(DateTimeOffset now) =>
        now.Month == 11 || (now.Month == 12 && now.Day <= 25);
}

public enum CustomerTier { Standard, Silver, Gold }
public sealed class UnsupportedDestinationException(string country)
    : InvalidOperationException($"لا نشحن إلى {country}");

// ✗ متى لا تستخدم Domain Service:
//   • لو القاعدة تخص كيانًا واحدًا → method في الكيان (الأفضل دائمًا)
//   • لو الكود بيوصل قاعدة بيانات أو HTTP → ده Application/Infrastructure (مش Domain Service)
//   • لو بقى «God Service» بيجمع كل المنطق → راجع حدود الـaggregates
'''},
            {"type": "heading", "level": 2, "text": "4) اختبارات الـinvariants (أسرع وأهم اختبارات في مشروعك)"},
            {"type": "code", "lang": "csharp", "filename": "tests/Shop.UnitTests/Domain/OrderTests.cs", "title": "بلا قاعدة، بلا mocks، بلا شبكة — أجزاء من الثانية", "code": r'''
public class OrderTests
{
    private static readonly FixedClock Clock = new(new DateTimeOffset(2026, 10, 22, 10, 0, 0, TimeSpan.Zero));
    private static readonly Address Cairo = new("12 Tahrir Sq", "Cairo", "EG", "11511");
    private static readonly Email Email = new("buyer@example.com");

    private static Order NewOrder(params (Guid, string, int, Money)[] lines) =>
        Order.Place(Guid.NewGuid(), Email, Cairo,
            lines.Length > 0 ? lines : [(Guid.NewGuid(), "Keyboard", 2, new Money(250m, "EGP"))], Clock);

    [Fact]
    public void Total_always_equals_sum_of_lines()
    {
        var order = NewOrder(
            (Guid.NewGuid(), "Mouse", 2, new Money(100m, "EGP")),
            (Guid.NewGuid(), "Pad", 1, new Money(50.5m, "EGP")));

        order.Total.Should().Be(new Money(250.5m, "EGP"));
    }

    [Fact]
    public void Adding_same_product_twice_merges_into_one_line()
    {
        var productId = Guid.NewGuid();
        var order = NewOrder((productId, "Mouse", 2, new Money(100m, "EGP")));

        order.AddLine(productId, "Mouse", 3, new Money(100m, "EGP"));

        order.Lines.Should().HaveCount(1, "لا تكرار لنفس المنتج في سطرين (invariant)");
        order.Lines[0].Quantity.Should().Be(5);
        order.Total.Should().Be(new Money(500m, "EGP"));
    }

    [Fact]
    public void Cannot_cancel_after_shipping()
    {
        var order = NewOrder();
        order.Ship(Clock);

        var act = () => order.Cancel("changed mind", Clock);

        act.Should().Throw<OrderCannotBeCancelledException>()
           .Which.Status.Should().Be(OrderStatus.Shipped);
        order.Status.Should().Be(OrderStatus.Shipped, "العملية المرفوضة لا تغيّر الحالة");
        order.CancelledAt.Should().BeNull();
    }

    [Fact]
    public void Cannot_exceed_line_limit()
    {
        var order = NewOrder();
        var act = () => { for (var i = 0; i < Order.MaxLines + 1; i++)
                order.AddLine(Guid.NewGuid(), $"P{i}", 1, new Money(1m, "EGP")); };

        act.Should().Throw<TooManyOrderLinesException>();
    }

    [Fact]
    public void Cannot_mix_currencies_in_one_order()
    {
        var order = NewOrder((Guid.NewGuid(), "Mouse", 1, new Money(100m, "EGP")));

        var act = () => order.AddLine(Guid.NewGuid(), "Imported", 1, new Money(10m, "USD"));

        act.Should().Throw<CurrencyMismatchException>();
    }

    [Fact]
    public void Placing_raises_OrderPlaced_with_snapshot_data()
    {
        var order = NewOrder();

        order.DomainEvents.Should().ContainSingle()
             .Which.Should().BeOfType<OrderPlaced>()
             .Which.Total.Should().Be(order.Total);
    }

    [Fact]
    public void Every_mutation_bumps_version_for_optimistic_concurrency()
    {
        var order = NewOrder();
        var before = order.Version;

        order.AddLine(Guid.NewGuid(), "Cable", 1, new Money(20m, "EGP"));

        order.Version.Should().Be(before + 1);
    }
}

/// <summary>منفذ الزمن للاختبار — السبب الحقيقي إن IClock في Domain.</summary>
public sealed class FixedClock(DateTimeOffset now) : IClock
{
    public DateTimeOffset UtcNow { get; set; } = now;
}
'''},
            {"type": "heading", "level": 2, "text": "5) أخطاء DDD التكتيكي الشائعة"},
            {"type": "table", "head": ["الخطأ", "الشكل", "الإصلاح"], "rows": [
                ["Aggregate ضخم", "`Order` فيه `Customer` و`Shipment` و`Payment` كمراجع كائنات", "معرّفات فقط + أحداث؛ aggregate صغير بأقفل أقل"],
                ["Anemic model", "كيانات بـgetters و`OrderService` بيعدّل كل حاجة", "انقل القواعد لجوه الكيان (درس 4.1.1)"],
                ["VO بلا تحقق", "`new Money(-5, \"EGPS\")` مقبول", "تحقق في الـconstructor + `readonly record struct`"],
                ["VO له هوية", "`Money` بيُقارن بـId", "المساواة بالقيمة؛ الهوية للكيانات فقط"],
                ["حدث كأمر (RPC)", "`PleaseCancelOrder` كـDomain Event", "الأحداث ماضية وصفية؛ الأوامر عبر Application"],
                ["Repository لكل جدول", "`IOrderLineRepository`, `IAddressRepository`", "repository واحد لجذر الـaggregate فقط"],
                ["Domain Service بيوصل DB", "الخدمة بتنادي `DbContext`", "مرّر البيانات كمعاملات؛ الوصول للـInfrastructure في Application"],
                ["لغة غير موحدة", "الكود `User`/`Client` والبيزنس «عميل»", "اسم واحد في كل مكان (Glossary في README + مراجعة)"],
                ["تعديل aggregate تاني في نفس المعاملة", "خصم مخزون + إنشاء طلب في معاملة", "aggregate واحد + حدث (اتساق eventual)"],
                ["أحداث بلا outbox", "نشر مباشر بعد `SaveChanges` → فقد عند الانهيار", "outbox في نفس المعاملة (درس 4.2.3)"],
            ]},
            {"type": "checkpoints", "items": [
                "أنمذج المفاهيم كـValue Objects بتحقق في الـconstructor وأتخلص من Primitive Obsession.",
                "أحدد حدود الـaggregate بالـinvariants لا بالراحة، وأخلي كل معاملة تعدّل aggregate واحدًا.",
                "أربط الـaggregates الأخرى بمعرّفات فقط وأتواصل بينها بأحداث ماضية غير قابلة للتعديل.",
                "أكتب اختبارات وحدة للقواعد (بلا قاعدة ولا mocks) وأخزّن الـVOs في EF بـcomplex/owned types.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "إيه الفرق بين Entity وValue Object؟",
                 "options": [
                     "الـEntity أكبر",
                     "Entity له هوية تستمر مع تغير الخصائص (المساواة بالمعرّف)؛ VO بلا هوية والمساواة بالقيمة وغير قابل للتعديل",
                     "VO يتخزن في جدول",
                     "لا فرق",
                 ], "answer": 1,
                 "explain": "مثال: `Order` كيان (نفس الطلب رغم تغير حالته)، و`Money(100, EGP)` VO (أي نسختين متساويتين = نفس القيمة)."},
                {"q": "`Money` بـ`readonly record struct` بدل `class` — الفائدة؟",
                 "options": [
                     "أقل كودًا فقط",
                     "مساواة بالقيمة تلقائيًا + عدم قابلية للتعديل + صفر تخصيص على الكومة (قيمة على الـstack)",
                     "يسمح بالوراثة",
                     "أسرع في EF",
                 ], "answer": 1,
                 "explain": "للـVOs الصغيرة دي مكاسب حقيقية: `Money a = b; a += x;` ينشئ نسخة جديدة ولا يعدّل الأصل — وده بالظبط اللي عايزينه."},
                {"q": "ليه `Order` بيحمل `CustomerId` مش `Customer Customer`؟",
                 "options": [
                     "توفير ذاكرة",
                     "Customer aggregate مستقل: المرجع بالكائن بيجرّه لنفس حدود التناسق (أقفال أوسع، معاملات أكبر) ويمنع الفصل لاحقًا",
                     "EF لا يدعمه",
                     "أسهل في التسلسل",
                 ], "answer": 1,
                 "explain": "القاعدة: عبر حدود الـaggregate → معرّفات فقط. لو محتاج بيانات العميل: استعلام منفصل أو انسخ ما يلزم (مثل اسم المنتج في السطر)."},
                {"q": "معاملة محتاجة تنقص المخزون وتسجل الطلب. التصميم الصحيح؟",
                 "options": [
                     "aggregate واحد يحتوي الاثنين",
                     "تعديل `Order` في معاملته + رفع `OrderPlaced` → مستهلك في `Stock` aggregate ينقص المخزون (idempotent، عبر outbox)",
                     "تعديل الاثنين في معاملة واحدة على نفس DbContext",
                     "استخدام معاملة موزعة (2PC)",
                 ], "answer": 1,
                 "explain": "اتساق eventual مقصود. التكلفة: المخزون ممكن يتأخر أجزاء من الثانية، ومحتاج تعويض لو فشل (حجز مؤقت + انتهاء صلاحية)."},
                {"q": "متى تستخدم Domain Service؟",
                 "options": [
                     "لأي منطق عمل",
                     "لما القاعدة تخص أكتر من aggregate أو لا تنتمي لكيان واحد، وتبقى بلا حالة ولا تصل لقاعدة/شبكة",
                     "بدل الـhandlers",
                     "لما الكيان كبير",
                 ], "answer": 1,
                 "explain": "الأفضل دايمًا method في الكيان. Domain Service حل استثنائي — ولو بدأ يجمع كل المنطق، فحدودك محتاجة مراجعة."},
                {"q": "repository لـ`OrderLine` — حكم صحيح؟",
                 "options": [
                     "مطلوب للـCRUD",
                     "مرفوض: `OrderLine` جزء من aggregate الطلب، ويُوصول له عبر الجذر فقط (`order.AddLine(...)`) — repository واحد للجذر",
                     "مطلوب للأداء",
                     "اختياري دائمًا",
                 ], "answer": 1,
                 "explain": "لو سمحت بتعديل السطور من بره الجذر، الـinvariant (المجموع = مجموع السطور) ممكن ينكسر بسهولة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "3 Value Objects في مشروعك",
                 "md": "اختار 3 مفاهيم مستخدمة كـprimitives (مبلغ/عملة، بريد، فترة تاريخية، عنوان، كمية، مرجع طلب) وحوّلها لـVOs بتحقق كامل وعمليات آمنة. حدّث التخطيط في EF والـhandlers، وأضف اختبارات وحدة لكل قاعدة.",
                 "criteria": [
                     "كل VO بـ`readonly record struct` مع تحقق في الـconstructor (مستحيل تنشئ نسخة غير صالحة)",
                     "العمليات الآمنة (جمع/طرح/مقارنة) بترفض الحالات الغلط باستثناء واضح",
                     "تخطيط EF معرّف في Infrastructure (complex/owned/converter) وبلا attributes في Domain",
                     "≥ 8 اختبارات وحدة تغطي الحدود (سالب، عملة مختلفة، طول أقصى، فترة معكوسة)",
                     "حذف التحقق المكرر من الـDTOs/Validators (الدليل: عدد الأسطر المحذوفة)",
                 ],
                 "hint": "لو التسلسل JSON broke: اعمل `JsonConverter` لكل VO في طبقة Api (مش في Domain)، أو استخدم constructor parameter matching في System.Text.Json."},
                {"id": "t2", "title": "أعد رسم حدود aggregate",
                 "md": "ارسم aggregate الحالي في مشروعك (كيانات + علاقات)، وحدد: أنهي كائنات لازم تخرج (معرّف فقط)، أنهي invariant داخل الحدود، وأنهي تعديل بيحصل عبر aggregate تاني في نفس المعاملة. نفّذ التغيير واختبره.",
                 "criteria": [
                     "رسم قبل/بعد (نص أو صورة) مع مبرر لكل كائن (داخل/خارج) مبني على invariant",
                     "لا معاملة تعدّل أكتر من aggregate واحد (اختبار/مراجعة يثبتها)",
                     "كل الآثار الجانبية عبر aggregates أخرى صارت أحداثًا تُكتب في outbox",
                     "اختبار وحدة لكل invariant + اختبار idempotency لمستهلك حدث واحد",
                     "قياس: عدد الصفوف المقفولة/زمن المعاملة قبل وبعد (لو انطبق)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "DDD — Domain model design (MS Learn)", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice"},
                {"label": "Effective Aggregate Design (Vaughn Vernon)", "url": "https://www.dddcommunity.org/library/vernon_2011/"},
                {"label": "Value Objects explained", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/implement-value-objects"},
                {"label": "EF Core — Owned & complex types", "url": "https://learn.microsoft.com/ef/core/modeling/owned-entities"},
                {"label": "Domain events design & implementation", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation"},
                {"label": "Refactoring Guru — domain logic patterns", "url": "https://refactoring.guru/design-patterns"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s4-m2-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
CQRS كلمة بتتقال كتير وبتُفهم غلط في الغالب: **مش معناها Event Sourcing**، ومش معناها إنك تعمل
40 نوع DTO لكل جدول. معناها ببساطة: **نموذج للقراءة مختلف عن نموذج للكتابة**، لأن المتطلبات مختلفة فعلًا.

والأهم: CQRS **مستويات**، مش زر تشغيل/إيقاف. أغلب المشاريع لازم تبدأ بالمستوى الأول
(فصل الاستعلامات عن الأوامر) وتقف هناك. المستوى التالت (read models منفصلة + أحداث) بيحتاج سببًا مقاسًا.

وهنبني هنا المستوى الأول والتاني بـMediatR: commands/queries/handlers + **pipelines** (validation، logging،
معاملات، أداء، idempotency) — وهي القيمة الحقيقية لـMediatR، مش الـdispatch نفسه.
"""},
            {"type": "terms", "items": [
                {"term": "CQS", "def": "مبدأ أصغر وأقدم: الدالة إما تعدّل أو ترجع بيانات — لا الاثنين. CQRS هو تطبيقه على مستوى المعمارية."},
                {"term": "Command", "def": "نية تغيير حالة (`PlaceOrder`) — لا ترجع بيانات عرض، وترجع نجاح/فشل أو معرّف."},
                {"term": "Query", "def": "طلب بيانات (`GetOrderDetails`) — لا يعدّل شيئًا، ويرجع DTO مُصمَّمًا للعرض."},
                {"term": "Read Model / Projection", "def": "بنية بيانات مُحسَّنة للقراءة (جدول منسوخ، view، مستند) تُبنى من أحداث/استعلامات."},
                {"term": "Mediator", "def": "وسيط يفصل المُرسِل عن المعالج: `ISender.Send(request)`. بيفتح الباب لـpipelines مشتركة."},
                {"term": "Pipeline Behavior", "def": "وسيط حول كل handler: validation، logging، معاملات، قياس أداء، idempotency — مكانه الوحيد بدل تكراره."},
                {"term": "Notification", "def": "حدث بلا متلقٍّ محدد (`INotification`) — يُبث لكل المعالجات المسجلة (أساس أحداث المجال محليًا)."},
                {"term": "Eventual Consistency", "def": "لو الـread model بيتبنى من أحداث، فهناك نافذة عدم اتساق — لازم تكون مقاسة ومعلنة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) المستويات الأربعة (اختار أدنى مستوى يكفيك)"},
            {"type": "table", "head": ["المستوى", "الوصف", "التكلفة", "الفائدة", "إمتى"], "rows": [
                ["**0** — نفس النموذج", "Entity واحدة للقراءة والكتابة (CRUD)", "الأقل", "بسيطة، لكن الاستعلامات بتتقيد بـEF والعلاقات", "أدوات صغيرة/لوحات إدارة"],
                ["**1** — فصل الأنواع (الأشهر)", "Commands وQueries منفصلة، كل واحد بـDTO خاصه، نفس قاعدة البيانات", "منخفضة", "★ وضوح، validation مختلف لكل اتجاه، قراءة بلا قيود الكتابة", "**ابدأ هنا** — يكفي أغلب المشاريع"],
                ["**2** — Read models منفصلة", "جداول/views منسوخة للقراءة (نفس القاعدة أو Redis/OpenSearch)", "متوسطة", "استعلامات معقدة/سريعة بلا joins، وفصل حمل القراءة", "لو القراءة 20× الكتابة وفيها تجميعات ثقيلة"],
                ["**3** — Event Sourcing", "الأحداث مصدر الحقيقة، والحالة تُبنى منها", "عالية جدًا", "تدقيق كامل، إعادة بناء projections، time travel", "مجال مالي/حجوزات بتدقيق صارم (درس 4.2.4)"],
            ]},
            {"type": "callout", "kind": "warn", "title": "خرافات CQRS اللي بتكلف فرق كتير",
             "md": """
- **«CQRS يتطلب Event Sourcing»** → غلط. المستوى 1 و2 بلا أي event sourcing.
- **«CQRS يعني قاعدتين بيانات»** → نادرًا لازم. أغلب الوقت نفس Postgres بجداول/views مختلفة.
- **«كل عملية تحتاج Command + Query + 4 DTOs»** → للـCRUD البسيط ده ضجيج. استخدمه لما فيه فرق حقيقي بين نموذجي القراءة والكتابة.
- **«MediatR إجباري لـCQRS»** → الـpattern مستقل. MediatR بيضيف قيمة حقيقية في الـ**pipelines**، مش في الـdispatch.
- **«القراءة من projection أفضل دائمًا»** → لو الاستعلام بسيط، القراءة المباشرة من جداول الكتابة أبسط وأدق (بلا نافذة اتساق).
"""},
            {"type": "heading", "level": 2, "text": "2) الأمر ومسار الكتابة"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Application/Orders/PlaceOrder.cs", "title": "Command + Handler + Validator (مسار الكتابة عبر الـDomain)", "code": r'''
using Shop.Domain.Orders;

namespace Shop.Application.Orders;

public sealed record PlaceOrderCommand(
    Guid CustomerId, string CustomerEmail, ShippingAddressInput Address, IReadOnlyList<OrderLineInput> Lines)
    : IRequest<PlaceOrderResult>;

public sealed record ShippingAddressInput(string Line1, string City, string Country, string? PostalCode);
public sealed record OrderLineInput(Guid ProductId, string Name, int Quantity, decimal UnitPrice, string Currency);
public sealed record PlaceOrderResult(Guid OrderId, string Status, decimal Total, string Currency);

public sealed class PlaceOrderValidator : AbstractValidator<PlaceOrderCommand>
{
    public PlaceOrderValidator()
    {
        RuleFor(x => x.CustomerId).NotEmpty();
        RuleFor(x => x.CustomerEmail).NotEmpty().EmailAddress().MaximumLength(320);
        RuleFor(x => x.Address).NotNull();
        RuleFor(x => x.Address.Country).Length(2);
        RuleFor(x => x.Lines).NotEmpty().Must(l => l.Count <= Order.MaxLines);
        RuleForEach(x => x.Lines).ChildRules(line =>
        {
            line.RuleFor(l => l.Quantity).InclusiveBetween(1, OrderLine.MaxQuantity);
            line.RuleFor(l => l.UnitPrice).GreaterThanOrEqualTo(0);
            line.RuleFor(l => l.Currency).Length(3);
        });
    }
}

public sealed class PlaceOrderHandler(
    IOrderRepository orders, IUnitOfWork uow, IClock clock, ILogger<PlaceOrderHandler> log)
    : IRequestHandler<PlaceOrderCommand, PlaceOrderResult>
{
    public async Task<PlaceOrderResult> Handle(PlaceOrderCommand cmd, CancellationToken ct)
    {
        // ① تحويل المدخلات لأنواع المجال (VOs تتحقق تاني — دفاع مزدوج مقصود)
        var address = new Address(cmd.Address.Line1, cmd.Address.City, cmd.Address.Country, cmd.Address.PostalCode);
        var lines = cmd.Lines.Select(l => (l.ProductId, l.Name, l.Quantity, new Money(l.UnitPrice, l.Currency)));

        // ② المنطق في الـDomain (factory + invariants)
        var order = Order.Place(cmd.CustomerId, new Email(cmd.CustomerEmail), address, lines, clock);

        // ③ الحفظ + كتابة الأحداث في outbox ذرّيًا (درس 4.2.3)
        orders.Add(order);
        await uow.SaveChangesAsync(ct);

        log.LogInformation("order placed {OrderId} total={Total}", order.Id, order.Total);
        return new PlaceOrderResult(order.Id, order.Status.ToString(), order.Total.Amount, order.Total.Currency);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "3) الاستعلام ومسار القراءة (بلا قيود الكتابة)"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Application/Orders/GetOrderDetails.cs", "title": "Query بيرجع DTO مصمم للعرض — عبر Dapper لا EF", "code": r'''
namespace Shop.Application.Orders;

// ★ الاستعلام يرجع **شكل الشاشة**، لا شكل الـDomain
public sealed record OrderDetailsResponse(
    Guid Id, string Reference, string CustomerName, string CustomerEmail, string Status,
    string StatusLabel, decimal Total, string Currency, string ShippingSummary,
    DateTimeOffset PlacedAt, IReadOnlyList<OrderLineDto> Lines, IReadOnlyList<OrderTimelineEntry> Timeline);

public sealed record OrderLineDto(Guid ProductId, string Name, int Quantity, decimal UnitPrice, decimal Subtotal);
public sealed record OrderTimelineEntry(string Event, DateTimeOffset At, string? Detail);

public sealed record GetOrderDetailsQuery(Guid OrderId) : IRequest<OrderDetailsResponse?>;

/// <summary>
/// مسار القراءة **لا يمر بالـDomain ولا بـEF tracking**: SQL واحد مُصمَّم للشاشة.
/// ده المعنى العملي لـCQRS: الكتابة تحمي القواعد، والقراءة تُحسَّن للعرض والأداء.
/// </summary>
public sealed class GetOrderDetailsHandler(IOrderReadModel readModel)
    : IRequestHandler<GetOrderDetailsQuery, OrderDetailsResponse?>
{
    public Task<OrderDetailsResponse?> Handle(GetOrderDetailsQuery q, CancellationToken ct) =>
        readModel.GetDetailsAsync(q.OrderId, ct);
}

// ── المنفذ في Application، والتنفيذ في Infrastructure (Dapper، درس 3.1.3) ──
public interface IOrderReadModel
{
    Task<OrderDetailsResponse?> GetDetailsAsync(Guid orderId, CancellationToken ct);
    Task<PagedResult<OrderSummaryResponse>> ListAsync(OrderListCriteria criteria, CancellationToken ct);
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/ReadModels/OrderReadModel.cs", "title": "التنفيذ: SQL واحد بـQueryMultiple بدل 5 استعلامات", "code": r'''
/// <summary>ترجمة الحالة لنص معروض — في Infrastructure لأن العرض قرار تسليم.</summary>
internal static class StatusLabels
{
    public static string Of(string status) => status switch
    {
        "Placed"    => "تم التسجيل",
        "Shipped"   => "قيد الشحن",
        "Delivered" => "تم التسليم",
        "Cancelled" => "ملغى",
        _           => status,
    };
}

public sealed class OrderReadModel(AppDbContext db) : IOrderReadModel
{
    private const string DetailsSql = """
        SELECT o.id, o.reference, c.name AS customer_name, o.customer_email, o.status,
               o.total_amount, o.total_currency, o.created_at,
               a.line1 || ', ' || a.city || ', ' || a.country AS shipping_summary
        FROM orders.orders o
        JOIN catalog.customers c ON c.id = o.customer_id
        LEFT JOIN LATERAL (SELECT * FROM orders.order_addresses WHERE order_id = o.id AND kind = 'shipping') a ON TRUE
        WHERE o.id = @OrderId;

        SELECT product_id, name, quantity, unit_price_amount AS unit_price,
               quantity * unit_price_amount AS subtotal
        FROM orders.order_lines WHERE order_id = @OrderId ORDER BY name;

        SELECT event_type AS event, occurred_at AS at, detail
        FROM orders.order_timeline WHERE order_id = @OrderId ORDER BY occurred_at DESC LIMIT 20;
        """;

    public async Task<OrderDetailsResponse?> GetDetailsAsync(Guid orderId, CancellationToken ct)
    {
        var connection = db.Database.GetDbConnection();          // ★ مشاركة الاتصال (درس 3.1.3)
        if (connection.State != ConnectionState.Open) await connection.OpenAsync(ct);

        using var multi = await connection.QueryMultipleAsync(
            new CommandDefinition(DetailsSql, new { OrderId = orderId },
                commandTimeout: 5, cancellationToken: ct));

        var head = await multi.ReadSingleOrDefaultAsync<OrderHeadRowAsync>();
        if (head is null) return null;

        var lines = (await multi.ReadAsync<OrderLineRow>()).ToList();
        var timeline = (await multi.ReadAsync<OrderTimelineRow>()).ToList();

        return new OrderDetailsResponse(
            head.Id, head.Reference, head.CustomerName, head.CustomerEmail,
            head.Status, StatusLabels.Of(head.Status), head.TotalAmount, head.TotalCurrency,
            head.ShippingSummary ?? "—", head.CreatedAt,
            lines.Select(l => new OrderLineDto(l.ProductId, l.Name, l.Quantity, l.UnitPrice, l.Subtotal)).ToList(),
            timeline.Select(t => new OrderTimelineEntry(t.Event, t.At, t.Detail)).ToList());
    }

    private sealed record OrderHeadRowAsync(Guid Id, string Reference, string CustomerName, string CustomerEmail,
        string Status, decimal TotalAmount, string TotalCurrency, DateTimeOffset CreatedAt, string? ShippingSummary);
    private sealed record OrderLineRow(Guid ProductId, string Name, int Quantity, decimal UnitPrice, decimal Subtotal);
    private sealed record OrderTimelineRow(string Event, DateTimeOffset At, string? Detail);
}
'''},
            {"type": "heading", "level": 2, "text": "4) القيمة الحقيقية لـMediatR: الـPipelines"},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Application/Common/Behaviors.cs", "title": "5 behaviors: validation، logging، أداء، معاملة، idempotency", "code": r'''
// ═══ ① Validation: مكان واحد بدل نسيانه في كل handler ═══
public sealed class ValidationBehavior<TRequest, TResponse>(IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse> where TRequest : IRequest<TResponse>
{
    // ✓ التوقيع في MediatR 12.5+/13: RequestHandlerDelegate<TResponse> (في إصدارات أقدم: <TRequest, TResponse>)
    //   تحقق من توقيع الإصدار عندك قبل النسخ.
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        if (!validators.Any()) return await next();

        var context = new ValidationContext<TRequest>(request);
        var failures = (await Task.WhenAll(validators.Select(v => v.ValidateAsync(context, ct))))
            .SelectMany(r => r.Errors).Where(f => f is not null).ToList();

        if (failures.Count > 0) throw new ValidationException(failures);   // → 400 عبر IExceptionHandler
        return await next();
    }
}

// ═══ ② Performance: يكشف الـhandlers البطيئة تلقائيًا ═══
public sealed class PerformanceBehavior<TRequest, TResponse>(
    ILogger<PerformanceBehavior<TRequest, TResponse>> log, TimeProvider time)
    : IPipelineBehavior<TRequest, TResponse> where TRequest : IRequest<TResponse>
{
    private static readonly System.Diagnostics.Metrics.Histogram<double> Duration =
        new System.Diagnostics.Metrics.Meter("Shop.Application", "1.0.0")
            .CreateHistogram<double>("handler.duration", unit: "ms");

    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        var start = time.GetTimestamp();
        var name = typeof(TRequest).Name;
        try { return await next(); }
        finally
        {
            var elapsed = time.GetElapsedTime(start).TotalMilliseconds;
            Duration.Record(elapsed, new KeyValuePair<string, object?>("handler", name));
            if (elapsed > 500) log.LogWarning("slow handler {Handler}: {Elapsed:F0}ms", name, elapsed);
        }
    }
}

// ═══ ③ Transaction: معاملة لكل أمر (وليس للاستعلامات) ═══
public sealed class TransactionBehavior<TRequest, TResponse>(AppDbContext db, ILogger<TransactionBehavior<TRequest, TResponse>> log)
    : IPipelineBehavior<TRequest, TResponse> where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        // ★ الاستعلامات لا تفتح معاملات (تكلفة بلا فائدة)
        if (typeof(TRequest).Name.EndsWith("Query", StringComparison.Ordinal)) return await next();

        // ✓ مع استراتيجية إعادة المحاولة: لازم نلف المعاملة داخل الـexecution strategy (درس 3.1.2)
        var strategy = db.Database.CreateExecutionStrategy();
        return await strategy.ExecuteAsync(async () =>
        {
            await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);
            try
            {
                var response = await next();          // handler يعمل SaveChanges + يكتب الـoutbox
                await tx.CommitAsync(ct);
                return response;
            }
            catch
            {
                await tx.RollbackAsync(ct);
                log.LogWarning("transaction rolled back for {Handler}", typeof(TRequest).Name);
                throw;
            }
        });
    }
}

// ═══ ④ Idempotency: نفس مفتاح الطلب مرتين = أثر واحد ═══
public sealed class IdempotencyBehavior<TRequest, TResponse>(AppDbContext db, ILogger<IdempotencyBehavior<TRequest, TResponse>> log)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>, IIdempotentRequest
{
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        var existing = await db.IdempotencyKeys.FindAsync([request.IdempotencyKey], ct);
        if (existing is not null)
        {
            log.LogInformation("replay of {Key} → نتيجة مخزنة", request.IdempotencyKey);
            return JsonSerializer.Deserialize<TResponse>(existing.ResponseJson)!;   // ✓ نفس الاستجابة
        }

        var response = await next();

        db.IdempotencyKeys.Add(new IdempotencyKey(request.IdempotencyKey, typeof(TRequest).Name,
            JsonSerializer.Serialize(response), DateTimeOffset.UtcNow));
        await db.SaveChangesAsync(ct);            // داخل نفس معاملة الـbehavior السابق
        return response;
    }
}
public interface IIdempotentRequest { string IdempotencyKey { get; } }

// ═══ ⑤ Logging: سجل موحّد لكل عملية (بلا تكرار في كل handler) ═══
public sealed class LoggingBehavior<TRequest, TResponse>(ILogger<LoggingBehavior<TRequest, TResponse>> log)
    : IPipelineBehavior<TRequest, TResponse> where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        using (log.BeginScope(new Dictionary<string, object> { ["handler"] = typeof(TRequest).Name }))
        {
            log.LogDebug("→ {Request}", Summarize(request));
            try
            {
                var response = await next();
                log.LogDebug("← {Request} ok", typeof(TRequest).Name);
                return response;
            }
            catch (Exception ex)
            {
                log.LogError(ex, "✗ {Request} failed", typeof(TRequest).Name);
                throw;
            }
        }
    }
    private static string Summarize(object r) =>       // ✓ لا تسجل بيانات حساسة كاملة
        r is IIdempotentRequest i ? i.IdempotencyKey : r.GetType().Name;
}
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Api/Program.cs", "title": "التركيب: ترتيب الـpipelines مهم", "code": r'''
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssemblyContaining<PlaceOrderCommand>();

    // ★ الترتيب من الخارج للداخل: ما يُنفَّذ أولًا يُسجَّل أولًا
    cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));        // 1. سجل كل شيء
    cfg.AddOpenBehavior(typeof(PerformanceBehavior<,>));    // 2. قِس زمن الكل (بما فيه الـvalidation)
    cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));     // 3. ارفض المدخلات الغلط بدريًا (قبل معاملة)
    cfg.AddOpenBehavior(typeof(IdempotencyBehavior<,>));    // 4. تحقق من التكرار
    cfg.AddOpenBehavior(typeof(TransactionBehavior<,>));    // 5. المعاملة حول التنفيذ الفعلي
});

builder.Services.AddValidatorsFromAssemblyContaining<PlaceOrderValidator>(ServiceLifetime.Scoped);

// ── Endpoint رفيع: تسليم فقط ──
// ★ انتبه: لا تنادِ sender.Send مرتين في نفس السطر (ينفّذ الأمر مرتين!) — خزّن النتيجة أولًا
app.MapPost("/api/orders", async (PlaceOrderCommand cmd, ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(cmd, ct);
    return Results.Created($"/api/orders/{result.OrderId}", result);
}).WithName("PlaceOrder").WithTags("Orders").RequireAuthorization("Orders.Write");

app.MapGet("/api/orders/{id:guid}", async (Guid id, ISender sender, CancellationToken ct) =>
    await sender.Send(new GetOrderDetailsQuery(id), ct) is { } details ? Results.Ok(details) : Results.NotFound());
'''},
            {"type": "heading", "level": 2, "text": "5) المستوى 2: read model منفصل (projection)"},
            {"type": "code", "lang": "sql", "filename": "db/011_order_summary_projection.sql", "title": "جدول projection — يُبنى من الأحداث ولا يُكتب يدويًا", "code": r'''
CREATE SCHEMA IF NOT EXISTS reporting;

-- ★ جدول قراءة مُحسَّن: صف واحد لكل طلب، بلا joins وقت القراءة
CREATE TABLE reporting.order_summary (
    order_id       uuid PRIMARY KEY,
    reference      text        NOT NULL,
    customer_id    uuid        NOT NULL,
    customer_name  text        NOT NULL,
    status         text        NOT NULL,
    total_amount   numeric(18,2) NOT NULL,
    total_currency char(3)     NOT NULL,
    line_count     int         NOT NULL DEFAULT 0,
    country        char(2)     NOT NULL,
    placed_at      timestamptz NOT NULL,
    last_event_at  timestamptz NOT NULL,
    projection_ver bigint      NOT NULL DEFAULT 0        -- ★ لـidempotency والترتيب
);

CREATE INDEX ix_order_summary_customer_placed
    ON reporting.order_summary (customer_id, placed_at DESC);
CREATE INDEX ix_order_summary_status_placed
    ON reporting.order_summary (status, placed_at DESC) INCLUDE (total_amount, reference);

-- نقطة تفتيش الـprojection: إلى أين وصلنا في الـoutbox/الأحداث
CREATE TABLE reporting.projection_checkpoints (
    projection     text PRIMARY KEY,
    last_event_id  bigint NOT NULL,
    updated_at     timestamptz NOT NULL DEFAULT now()
);

-- إعادة بناء كاملة لو لزم (rebuild) — لازم تكون ممكنة دائمًا
-- TRUNCATE reporting.order_summary; ثم شغّل الـprojector من البداية
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Infrastructure/Projections/OrderSummaryProjector.cs", "title": "عامل projection: idempotent، قابل لإعادة البناء", "code": r'''
/// <summary>
/// يقرأ الأحداث من الـoutbox بالترتيب ويحدّث جدول القراءة.
/// ★ idempotent: `projection_ver` يمنع تطبيق حدث قديم فوق حالة أحدث.
/// ★ قابل لإعادة البناء: احذف الجدول وشغّل من البداية (بلا فقدان).
/// </summary>
/// <summary>مقاييس الـprojection — التأخير أهم رقم تشغيلي هنا.</summary>
public static class Metrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Infrastructure.projections", "1.0.0");
    public static readonly Histogram<long> ProjectorLag =
        Meter.CreateHistogram<long>("projector.batch.size", unit: "events");
    public static readonly ObservableGauge<long> Age =
        Meter.CreateObservableGauge("projector.lag.seconds", () => 0L, unit: "s",
            description: "عمر أقدم حدث غير معالَج — يُحسب من نقطة التفتيش");
}

public sealed class OrderSummaryProjector(
    AppDbContext db, IServiceScopeFactory scopes, ILogger<OrderSummaryProjector> log) : BackgroundService
{
    private const string Name = "order_summary";
    private const int Batch = 100;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var ctx = scope.ServiceProvider.GetRequiredService<AppDbContext>();

                var lastId = await ctx.ProjectionCheckpoints
                    .Where(c => c.Projection == Name).Select(c => c.LastEventId)
                    .FirstOrDefaultAsync(stoppingToken);

                // ✓ SKIP LOCKED: عدة نسخ لا تعالج نفس الأحداث (درس 2.3.x)
                var events = await ctx.OutboxMessages
                    .Where(m => m.Id > lastId && m.Type.StartsWith("order."))
                    .OrderBy(m => m.Id).Take(Batch)
                    .ToListAsync(stoppingToken);

                if (events.Count == 0) { await Task.Delay(500, stoppingToken); continue; }

                foreach (var message in events)
                {
                    switch (message.Type)
                    {
                        case "order.placed":   await ApplyPlacedAsync(ctx, message, stoppingToken); break;
                        case "order.cancelled": await ApplyStatusAsync(ctx, message, "Cancelled", stoppingToken); break;
                        case "order.shipped":  await ApplyStatusAsync(ctx, message, "Shipped", stoppingToken); break;
                        default: log.LogDebug("ignoring {Type}", message.Type); break;
                    }

                    // ✓ تقدم نقطة التفتيش في نفس معاملة التغيير (بلا فقد ولا تكرار ضار)
                    await UpsertCheckpointAsync(ctx, message.Id, stoppingToken);
                }

                await ctx.SaveChangesAsync(stoppingToken);
                Metrics.ProjectorLag.Record(events.Count, new KeyValuePair<string, object?>("projection", Name));
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                log.LogError(ex, "projection {Name} failed; retrying", Name);
                await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);
            }
        }
    }

    private static async Task ApplyPlacedAsync(AppDbContext ctx, OutboxMessage m, CancellationToken ct)
    {
        var e = JsonSerializer.Deserialize<OrderPlaced>(m.Payload)!;
        await ctx.Database.ExecuteSqlInterpolatedAsync($"""
            INSERT INTO reporting.order_summary
                (order_id, reference, customer_id, customer_name, status,
                 total_amount, total_currency, line_count, country, placed_at, last_event_at, projection_ver)
            SELECT o.id, o.reference, o.customer_id, c.name, 'Placed',
                   {e.Total.Amount}, {e.Total.Currency}, o.line_count, o.country, o.created_at,
                   {m.OccurredAt}, {m.Id}
            FROM orders.orders o JOIN catalog.customers c ON c.id = o.customer_id
            WHERE o.id = {e.OrderId}
            ON CONFLICT (order_id) DO UPDATE SET
                status = EXCLUDED.status, last_event_at = EXCLUDED.last_event_at,
                projection_ver = EXCLUDED.projection_ver
            WHERE reporting.order_summary.projection_ver < EXCLUDED.projection_ver;
            """, ct);
    }

    private static Task ApplyStatusAsync(AppDbContext ctx, OutboxMessage m, string status, CancellationToken ct) =>
        ctx.Database.ExecuteSqlInterpolatedAsync($"""
            UPDATE reporting.order_summary
            SET status = {status}, last_event_at = {m.OccurredAt}, projection_ver = {m.Id}
            WHERE order_id = {(JsonSerializer.Deserialize<OrderStatusEvent>(m.Payload)).OrderId}
              AND projection_ver < {m.Id};
            """, ct);

    private static Task UpsertCheckpointAsync(AppDbContext ctx, long eventId, CancellationToken ct) =>
        ctx.Database.ExecuteSqlInterpolatedAsync($"""
            INSERT INTO reporting.projection_checkpoints (projection, last_event_id, updated_at)
            VALUES ({Name}, {eventId}, now())
            ON CONFLICT (projection) DO UPDATE
            SET last_event_id = EXCLUDED.last_event_id, updated_at = now();
            """, ct);
}
'''},
            {"type": "callout", "kind": "note", "title": "تكلفة المستوى 2: نافذة عدم اتساق",
             "md": """
القراءة من `reporting.order_summary` **ليست لحظية**: فيه تأخير (عادةً 50ms–2s) بين الكتابة وظهورها.

**التعامل العملي:**
- **قيس التأخير** وانشره كـmetric (`projector.lag`) ونبّه لو تجاوز حدًا (مثلًا 5s).
- **بعد الكتابة، اقرأ من مصدر الكتابة** في نفس الطلب (أو أرجع النتيجة من الـcommand نفسه) —
  المستخدم ما يستناش الـprojection عشان يشوف اللي عمله.
- **اجعل إعادة البناء ممكنة دائمًا** (truncate + projector من الصفر) — هتحتاجها لما تضيف حقلًا.
- **لا تخلط**: استعلامات التقارير من الـprojection، واستعلامات التفاصيل الدقيقة من جداول الكتابة.
- لو التأخير غير مقبول في حالة ما → استخدم المستوى 1 (استعلام مباشر مع index جيد) لهذه الحالة تحديدًا.
"""},
            {"type": "heading", "level": 2, "text": "6) MediatR: إمتى يستحق وإمتى يكون ضجيجًا؟"},
            {"type": "table", "head": ["الحالة", "MediatR؟", "السبب"], "rows": [
                ["عندك behaviors مشتركة (validation/معاملات/قياس)", "✓ نعم", "دي القيمة الحقيقية — مكان واحد بدل تكراره في كل مسار"],
                ["ميزات كتير بنمط موحد وفريق متوسط", "✓ نعم", "نمط متوقع يسهّل الـonboarding والمراجعة"],
                ["CRUD بسيط بـ3 عمليات", "✗ لا", "واجهة مباشرة (`IOrderService`) أوضح وبلا indirection"],
                ["مسار أداء حرج (hot path)", "△ قِس", "فيه overhead بسيط للتوزيع؛ قارن بنداء مباشر"],
                ["فريق بيشتكي من صعوبة تتبع التنفيذ", "△ راجع", "الحل: تسمية واضحة + مجلد لكل feature + توثيق النمط"],
                ["محتاج أحداث داخلية (domain events)", "✓ مفيد", "`INotification` + `IPublisher` بدل بناء ناقل داخلي"],
            ]},
            {"type": "checkpoints", "items": [
                "أختار مستوى CQRS الأدنى الكافي (الأغلب: المستوى 1) وأسجّل القرار في ADR.",
                "أفصل الأوامر (عبر Domain + معاملة + outbox) عن الاستعلامات (DTO للشاشة، Dapper/view، بلا tracking).",
                "أستخدم MediatR لقيمته الحقيقية: pipelines مشتركة (validation، logging، قياس، معاملات، idempotency) بترتيب مقصود.",
                "لو بنيت projection: أقيس التأخير، وأجعل القراءة بعد الكتابة من مصدر الكتابة، وأضمن إمكانية إعادة البناء.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "CQRS بالحد الأدنى يعني إيه؟",
                 "options": [
                     "Event Sourcing + قاعدتين",
                     "نموذج قراءة مختلف عن نموذج الكتابة (commands/queries بأنواع مختلفة) — حتى لو على نفس قاعدة البيانات",
                     "استخدام MediatR",
                     "فصل الـAPI عن الـUI",
                 ], "answer": 1,
                 "explain": "المستوى 1 (فصل الأنواع) يكفي أغلب المشاريع. القواعد المنفصلة والأحداث مستوى أعلى يحتاج سببًا مقاسًا."},
                {"q": "ليه مسار القراءة ما يمرش بالـDomain؟",
                 "options": [
                     "للأداء فقط",
                     "لأن القراءة لا تغيّر حالة ولا تحتاج فرض invariants؛ شكلها الأمثل هو شكل الشاشة (DTO) وSQL مُحسَّن بلا قيود الكتابة",
                     "الـDomain بطيء",
                     "ممنوع تقنيًا",
                 ], "answer": 1,
                 "explain": "ده جوهر CQRS: الكتابة تحمي القواعد، والقراءة تُصمَّم للعرض والأداء. لو القراءة محتاجة قواعد → فيه خلل في الحدود."},
                {"q": "ترتيب behaviors: validation قبل المعاملة ولا بعدها؟",
                 "options": [
                     "بعدها — أدق",
                     "قبلها — ارفض المدخلات الغلط قبل فتح معاملة (توفير اتصال/قفل وسجل أنظف)",
                     "الترتيب غير مهم",
                     "في نفس الوقت",
                 ], "answer": 1,
                 "explain": "القاعدة: الأرخص والأكثر رفضًا أولًا (logging → قياس → validation → idempotency → معاملة → تنفيذ)."},
                {"q": "read model من أحداث — المستخدم عدّل بياناته وفتح الصفحة فلم يرَ التغيير. السبب والحل؟",
                 "options": [
                     "bug في الـUI",
                     "نافذة عدم اتساق في الـprojection؛ الحل: أرجع النتيجة من الـcommand نفسه أو اقرأ من مصدر الكتابة بعد التعديل، وقِس الـlag",
                     "زد الـTTL",
                     "استخدم Redis",
                 ], "answer": 1,
                 "explain": "الاتساق eventual تكلفة مقصودة للمستوى 2 — لازم تكون مقاسة ومعلنة، والتجربة الحرجة (بعد كتابة مباشرة) تُعالج صراحة."},
                {"q": "projection بيستقبل نفس الحدث مرتين (إعادة تسليم). الحماية؟",
                 "options": [
                     "تجاهل المشكلة",
                     "idempotency: مفتاح/إصدار (`projection_ver`) مع شرط في UPDATE/UPSERT يرفض تطبيق حدث أقدم أو مكرر",
                     "إيقاف المستهلك",
                     "حذف الجدول",
                 ], "answer": 1,
                 "explain": "at-least-once = تكرار متوقع. كمان `projection_ver` بيحل مشكلة الترتيب لو وصل حدث قديم بعد حدث أحدث."},
                {"q": "مشروع CRUD صغير (لوحة إدارة) — CQRS وMediatR؟",
                 "options": [
                     "إلزامي دائمًا",
                     "غالبًا مبالغة: واجهة مباشرة + Minimal APIs أبسط وأوضح، وأضف الأنماط لما يظهر ألم حقيقي",
                     "ممنوع",
                     "MediatR فقط",
                 ], "answer": 1,
                 "explain": "الأنماط أدوات لمشاكل محددة. استخدامها بلا مشكلة = تعقيد وتكلفة صيانة بلا عائد (وسجّل القرار في ADR)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "افصل مسار قراءة واحد (المستوى 1)",
                 "md": "اختار استعلامًا ثقيلًا في مشروعك (قائمة/تفاصيل) وأعد بناءه كـQuery منفصل يرجع DTO مصممًا للشاشة عبر Dapper/view — بلا EF tracking وبلا مرور بالـDomain. قِس الفرق.",
                 "criteria": [
                     "Query + Response DTO في Application، والتنفيذ (SQL) في Infrastructure خلف منفذ",
                     "الاستعلام يرجع **فقط** الحقول المعروضة (لا كيان كامل)، وعدد round-trips ≤ 1 (QueryMultiple أو join)",
                     "قياس قبل/بعد (p95 وعدد الاستعلامات) في ملف النتائج",
                     "اختبار تكامل على Postgres حقيقي يقارن النتيجة مع البيانات المزروعة",
                     "لا معاملة ولا tracking في مسار القراءة (اختبار/مراجعة)",
                 ],
                 "hint": "لو النتيجة محتاجة بيانات من موديول تاني: اعمل join داخل SQL (نفس القاعدة) أو اقرأ عبر عقد الموديول — ولا تنسخ جداوله."},
                {"id": "t2", "title": "Pipelines + قرار مستوى CQRS",
                 "md": "أضف 3 behaviors على الأقل (validation، قياس، معاملات للأوامر فقط) بترتيب مقصود، واكتب ADR يحدد مستوى CQRS في مشروعك مع شروط الانتقال للمستوى التالي.",
                 "criteria": [
                     "3 behaviors مسجلة بترتيب موثق + تعليق يشرح ليه الترتيب ده",
                     "الاستعلامات لا تفتح معاملات (اختبار يثبتها)",
                     "مقياس `handler.duration` بوسم لكل handler + تنبيه للبطيء",
                     "ADR: المستوى الحالي، البدائل، التكاليف، وشرط مقاس للانتقال للمستوى 2",
                     "اختبار: أمر ببيانات غلط → 400 قبل فتح أي معاملة (يُثبت بالسجل/العدّاد)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "CQRS pattern (MS Learn)", "url": "https://learn.microsoft.com/azure/architecture/patterns/cqrs"},
                {"label": "CQRS in .NET architecture guide", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/cqrs-microservice-reads"},
                {"label": "MediatR", "url": "https://github.com/jbogard/MediatR"},
                {"label": "Dapper", "url": "https://github.com/DapperLib/Dapper"},
                {"label": "FluentValidation — ASP.NET integration", "url": "https://docs.fluentvalidation.net/en/latest/aspnet.html"},
                {"label": "Materialized views (PostgreSQL)", "url": "https://www.postgresql.org/docs/current/rules-materializedviews.html"},
            ]},
        ],
    },
]
