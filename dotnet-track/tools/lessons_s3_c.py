"""Stage 3, Module 2 — Advanced EF Core (lessons 3-4 of 4)."""

TODAY = "2026-10-22"

LESSONS_S3_C = [
    # ------------------------------------------------------------------ l3
    {
        "id": "s3-m2-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
النمط التقليدي للكتابة في EF Core — حمّل الكيانات، عدّلها، `SaveChanges` — ممتاز لصف أو صفين.
لكنه كارثة لتغيير 50 ألف صف: بتجلب بيانات عبر الشبكة، بتبني snapshots لكل كيان، وبتستهلك ذاكرة وGC.

**`ExecuteUpdate`/`ExecuteDelete`** بيغيروا المعادلة: عبارة `UPDATE`/`DELETE` واحدة بتتنفذ **داخل** قاعدة البيانات،
بلا نقل بيانات وبلا change tracking. الدرس ده: الاستخدام الآمن، الحدود اللي لازم تعرفها (تجاوز الـvalidation
والـauditing وconcurrency tokens)، واختيار الأداة الصح للـbulk insert.
"""},
            {"type": "terms", "items": [
                {"term": "`ExecuteUpdate`/`ExecuteUpdateAsync`", "def": "يترجم الاستعلام + `SetProperty` لعبارة UPDATE واحدة؛ يرجع عدد الصفوف المتأثرة."},
                {"term": "`ExecuteDelete`/`ExecuteDeleteAsync`", "def": "نفس الفكرة للحذف — DELETE واحدة بلا تحميل."},
                {"term": "Affected Rows", "def": "عدد الصفوف المتأثرة. **لازم تفحصه**: هو إشارة النجاح/التعارض الوحيدة."},
                {"term": "Server-side update", "def": "التغيير بيحدث في القاعدة — البيانات ما بتمرّش على التطبيق (توفير شبكة وذاكرة)."},
                {"term": "Change Tracker bypass", "def": "الكيانات المتتبَّعة في نفس الـDbContext ما بتتحدثش → تصبح قديمة (stale)."},
                {"term": "Interceptor bypass", "def": "`SaveChanges` interceptors والـauditing وأحداث الـdomain **لا تعمل** — لازم تعوّضها صراحة."},
                {"term": "Concurrency token bypass", "def": "لا فحص `xmin`/`RowVersion` → احمِ نفسك بشرط `WHERE` صريح."},
                {"term": "Bulk insert", "def": "إدراج ضخم: `COPY` (Postgres) أو دفعات أو مكتبات خارجية — `AddRange` وحده لا يكفي لمئات الآلاف."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الاستخدام الصحيح: WHERE حارس + فحص الصفوف"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Stock/BulkStockOps.cs", "title": "تحديث جماعي آمن ومشروط", "code": r'''
public sealed class StockOperations(AppDbContext db, ILogger<StockOperations> log)
{
    /// <summary>
    /// ✗ بلا ExecuteUpdate: تحميل 5,000 كيان + تعديل + حفظ (ثوانٍ وذاكرة ضخمة)
    /// ✓ عبارة واحدة، بلا نقل بيانات
    /// </summary>
    public async Task<int> MarkAbandonedAsCancelledAsync(TimeSpan olderThan, CancellationToken ct)
    {
        var cutoff = TimeProvider.System.GetUtcNow() - olderThan;
        var now = TimeProvider.System.GetUtcNow();

        var affected = await db.Orders
            .Where(o => o.Status == OrderStatus.Abandoned && o.CreatedAt < cutoff)
            .ExecuteUpdateAsync(s => s
                .SetProperty(o => o.Status, OrderStatus.Cancelled)
                .SetProperty(o => o.UpdatedAt, now)                       // ★ الـaudit يدويًا
                .SetProperty(o => o.CancelReason, "abandoned-timeout"),
                ct);

        log.LogInformation("cancelled {Affected} abandoned orders (cutoff={Cutoff})", affected, cutoff);
        return affected;
    }

    /// <summary>
    /// ★ الحارس في WHERE: خصم مشروط بتوفر المخزون — وفحص الصفوف المتأثرة هو دليل النجاح.
    /// ده بيعوّض غياب concurrency token في ExecuteUpdate.
    /// </summary>
    public async Task<bool> TryDecrementStockAsync(Guid productId, int quantity, CancellationToken ct)
    {
        var affected = await db.Products
            .Where(p => p.Id == productId && p.Stock >= quantity)          // ← الشرط الحاسم
            .ExecuteUpdateAsync(s => s
                .SetProperty(p => p.Stock, p => p.Stock - quantity)        // حساب من العمود نفسه
                .SetProperty(p => p.UpdatedAt, TimeProvider.System.GetUtcNow()),
                ct);

        if (affected == 0)
        {
            // إما المنتج غير موجود أو المخزون غير كافٍ — ميّز بينهما لو الرسالة تهم المستخدم
            var exists = await db.Products.AnyAsync(p => p.Id == productId, ct);
            if (!exists) throw new NotFoundException("Product", productId);

            log.LogWarning("insufficient stock product={ProductId} requested={Qty}", productId, quantity);
            return false;
        }

        return true;
    }

    /// <summary>تحديث جماعي بحد أعلى للحماية من «UPDATE بلا WHERE».</summary>
    public async Task<int> RepriceCategoryAsync(Guid categoryId, decimal factor, int maxRows, CancellationToken ct)
    {
        if (factor is <= 0 or > 10) throw new ArgumentOutOfRangeException(nameof(factor));

        // ✓ حد صريح: نعدّ أولًا، ونرفض لو النطاق أوسع من المتوقع (حماية من خطأ في الشرط)
        var candidates = await db.Products.CountAsync(p => p.CategoryId == categoryId, ct);
        if (candidates > maxRows)
            throw new ConflictException("Category", categoryId,
                $"التغيير سيشمل {candidates} منتجًا (الحد {maxRows}) — نفّذه كمهمة خلفية");

        var affected = await db.Products
            .Where(p => p.CategoryId == categoryId)
            .ExecuteUpdateAsync(s => s
                .SetProperty(p => p.Price, p => p.Price * factor)
                .SetProperty(p => p.UpdatedAt, TimeProvider.System.GetUtcNow()),
                ct);

        await db.Database.ExecuteSqlInterpolatedAsync(
            $"SELECT pg_notify('catalog_changed', {categoryId.ToString()})", ct);   // ← إبطال كاش (درس Redis)

        return affected;
    }

    /// <summary>حذف جماعي — بنفس قواعد الحذر (WHERE صريح + فحص الصفوف + سجل).</summary>
    public async Task<int> PurgeCancelledOlderThanAsync(DateTimeOffset before, CancellationToken ct)
    {
        var affected = await db.Orders
            .Where(o => o.Status == OrderStatus.Cancelled && o.UpdatedAt < before)
            .ExecuteDeleteAsync(ct);

        log.LogInformation("purged {Affected} cancelled orders older than {Before}", affected, before);
        return affected;
    }
}
'''},
            {"type": "callout", "kind": "danger", "title": "ما اللي بيتم تجاوزه؟ (أخطر جزء في الدرس)",
             "md": """
`ExecuteUpdate` بيتجاوز كل اللي بيحصل في `SaveChanges`:

| بيتجاوز | الأثر | التعويض |
|---|---|---|
| **قواعد الـDomain والـinvariants** | تحديث ممكن يكسر قاعدة عمل (خصم على منتج مقفل) | شروط `WHERE` صريحة + استخدم الكيانات للتغييرات المنطقية |
| **الـValidation (FluentValidation/annotations)** | قيم غير صالحة بتدخل القاعدة | قيود القاعدة (CHECK/NOT NULL) + تحقق في الـservice |
| **Concurrency tokens (`xmin`/`RowVersion`)** | فقد تحديثات متزامنة بصمت | شرط الإصدار في `WHERE` + فحص `affected` |
| **`SaveChanges` interceptors / الـaudit** | `UpdatedAt`/`UpdatedBy` لا يُحدَّث | `SetProperty` صريح + سجل (log) بالعملية |
| **أحداث الـDomain / outbox** | مستهلكون لا يعرفون بالتغيير | `pg_notify`/رسالة صريحة بعد الالتزام |
| **الكاش** | بيانات قديمة مخزّنة | إبطال مقصود بعد الالتزام |

القاعدة: **`ExecuteUpdate` للتغييرات الميكانيكية الجماعية** (حالة، سعر، تنظيف) —
**مش** للعمليات اللي فيها منطق عمل (إنشاء طلب، دفع، حجز مخزون مع قواعد).
"""},
            {"type": "heading", "level": 2, "text": "2) داخل معاملة + مع الـChange Tracker"},
            {"type": "code", "lang": "csharp", "title": "المشاركة في معاملة واحدة، وتجنّب الكيانات القديمة", "code": r'''
public sealed class BatchShipService(AppDbContext db, ILogger<BatchShipService> log)
{
    public async Task ShipPendingAsync(Guid warehouseId, CancellationToken ct)
    {
        await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);
        try
        {
            // ① قراءة للتحقق (كيانات أو projection)
            var pending = await db.Orders
                .Where(o => o.WarehouseId == warehouseId && o.Status == OrderStatus.Ready)
                .Select(o => o.Id)
                .Take(500)
                .ToListAsync(ct);

            if (pending.Count == 0) { await tx.CommitAsync(ct); return; }

            // ② تحديث جماعي بعبارة واحدة (بلا تحميل الكيانات)
            var updated = await db.Orders
                .Where(o => pending.Contains(o.Id) && o.Status == OrderStatus.Ready)   // ← إعادة الفحص (سباق)
                .ExecuteUpdateAsync(s => s
                    .SetProperty(o => o.Status, OrderStatus.Shipped)
                    .SetProperty(o => o.ShippedAt, TimeProvider.System.GetUtcNow())
                    .SetProperty(o => o.UpdatedAt, TimeProvider.System.GetUtcNow()), ct);

            // ③ كتابة رسالة outbox في **نفس** المعاملة (تسليم مضمون بلا فقد)
            db.OutboxMessages.Add(new OutboxMessage
            {
                Id = Guid.NewGuid(),
                Type = "orders.shipped.batch",
                Payload = JsonSerializer.Serialize(new { warehouseId, count = updated, orderIds = pending }),
                CreatedAt = DateTimeOffset.UtcNow,
            });
            await db.SaveChangesAsync(ct);

            await tx.CommitAsync(ct);
            log.LogInformation("shipped {Updated} orders from warehouse {WarehouseId}", updated, warehouseId);

            // ★ لو فيه كيانات متتبَّعة في نفس الـcontext من قبل التحديث الجماعي:
            //   قيمها بقت قديمة. افصلها أو استخدم context منفصل للقراءة التالية.
            db.ChangeTracker.Clear();
        }
        catch
        {
            await tx.RollbackAsync(CancellationToken.None);
            throw;
        }
    }
}
'''},
            {"type": "callout", "kind": "warn", "title": "حدود تقنية لازم تعرفها",
             "md": """
- **لا يعمل مع `Include`** — التحديث على الاستعلام نفسه (ضمّ عبر `Where` على navigation مدعوم بحسب الحالة).
- **`SetProperty` بيشتغل على أعمدة** — لا نداءات دوال .NET اعتباطية؛ استخدم تعبيرات قابلة للترجمة (حساب على العمود، `DateTime` عبر provider، EF Core 10 بيدعم lambdas عادية).
- **الكيانات المحمّلة مسبقًا لا تتحدث** → `ChangeTracker.Clear()` أو context منفصل.
- **لا أحداث ولا interceptors** (الجدول أعلاه).
- **`ExecuteUpdate` داخل حلقة** = نفي الغرض. اجمع الشرط في عبارة واحدة.
- **مع `EnableRetryOnFailure`**: لو استخدمت معاملة يدوية، لفّها في `CreateExecutionStrategy().ExecuteAsync(...)` (فخ معروف من درس المعاملات).
- **Query filters بتُطبَّق** (ممتاز للـtenancy) — لكن تحقق باختبار، ولا تفترض.
"""},
            {"type": "heading", "level": 2, "text": "3) Bulk insert: اختيار الأداة بحسب الحجم"},
            {"type": "table", "head": ["الحجم", "الأداة", "ملاحظات"], "rows": [
                ["1-100 صف", "`Add`/`AddRange` + `SaveChangesAsync`", "الأسهل، مع tracking وvalidation — كافي تمامًا"],
                ["100-5,000 صف", "`AddRange` + `SaveChanges` + دفعات (`MaxBatchSize`)", "قلّل حجم الدفعة لو الذاكرة/GC ارتفع"],
                ["5,000-100,000 صف", "`COPY` (Npgsql `BeginBinaryImport`) أو multi-row INSERT", "بلا tracking؛ الأسرع على Postgres"],
                [">100,000 صف / دوري", "مهمة خلفية + `COPY` على دفعات", "اعزل عن مسار الطلب (درس BackgroundService)"],
                ["تحديث جماعي (مش إدراج)", "`ExecuteUpdateAsync`", "بلا نقل بيانات إطلاقًا"],
                ["حذف جماعي", "`ExecuteDeleteAsync`", "انتبه للقيود (FK) والأداء على جداول كبيرة"],
                ["عمليات معقدة (merge/upsert)", "SQL خام (`INSERT … ON CONFLICT`) أو مكتبة bulk", "upsert في عبارة واحدة أرخص بكثير"],
            ]},
            {"type": "code", "lang": "csharp", "title": "Upsert بعبارة واحدة (بدل اقرأ-ثم-احفظ)", "code": r'''
// ✗ نمط مكلف وسباق: قراءة ثم إدراج/تحديث (يتطلب قفلًا أو إعادة محاولة)
var existing = await db.Products.FirstOrDefaultAsync(p => p.Sku == sku, ct);
if (existing is null) { db.Products.Add(product); } else { existing.Price = product.Price; }
await db.SaveChangesAsync(ct);

// ✓ upsert ذرّي: INSERT … ON CONFLICT (Postgres) — عبارة واحدة، بلا سباق
var affected = await db.Database.ExecuteSqlInterpolatedAsync($"""
    INSERT INTO products (id, sku, name, price, stock, updated_at)
    VALUES ({product.Id}, {product.Sku}, {product.Name}, {product.Price}, {product.Stock}, now())
    ON CONFLICT (sku) DO UPDATE
        SET price      = EXCLUDED.price,
            stock      = EXCLUDED.stock,
            name       = EXCLUDED.name,
            updated_at = now()
    """, ct);

// SQL Server المقابل: MERGE (بحذر من سباقات MERGE المعروفة) أو UPDLOCK + HOLDLOCK داخل معاملة
// ولاحظ: ExecuteSqlInterpolated بيحوّل القيم لـparameters تلقائيًا (لا دمج نصوص)
'''},
            {"type": "code", "lang": "csharp", "title": "مقارنة أداء: أرقام نموذجية لإدراج 50,000 صف (Postgres، جهاز تطوير)", "code": r'''
// الأداة                                  الزمن        الذاكرة المخصّصة   ملاحظات
// ───────────────────────────────────────  ───────────  ─────────────────  ─────────────────────────
// Add + SaveChanges لكل صف                 ~180 s       عالية جدًا         ✗ 50k round-trip + 50k transaction
// AddRange + SaveChanges (مرة واحدة)       ~38 s        ~600 MB            tracking + snapshots + batch inserts
// AddRange بدفعات 1,000 + SaveChanges      ~22 s        ~120 MB            أفضل ذاكرة، لسه tracking
// بلا tracking: db.AddRange ثم SaveChanges ~22 س        نفسها              (tracking مطلوب للإدراج — لا فرق كبير)
// Dapper multi-row INSERT (دفعات 500)      ~9 s         ~35 MB             SQL ثابت + parameters
// Npgsql COPY (BeginBinaryImport)          ~2.5 s       ~20 MB             ✓ الأسرع — بلا SQL نصي
//
// الخلاصة: الفرق بين الأسوأ والأفضل ≈ 70 مرة. القرار يعتمد على الحجم والتكرار.
// ★ قِس على بياناتك وأجهزتك — الأرقام دي اتجاهية، مش مرجعية.
'''},
            {"type": "heading", "level": 2, "text": "4) اختبارات الكتابات الجماعية"},
            {"type": "code", "lang": "csharp", "title": "اختبارات حقيقية على Postgres (لا InMemory)", "code": r'''
[Collection("Postgres")]
public sealed class BulkOperationsTests(PostgresFixture db) : IAsyncLifetime
{
    public ValueTask InitializeAsync() => new(db.ResetAsync().AsTask());
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;

    [Fact]
    public async Task Decrement_stock_fails_when_insufficient_without_going_negative()
    {
        await using (var ctx = db.CreateContext())
        {
            ctx.Products.Add(new Product { Id = productId, Sku = "W-1", Name = "Widget", Price = 10m, Stock = 3 });
            await ctx.SaveChangesAsync();
        }

        var ops = new StockOperations(db.CreateContext(), log);

        (await ops.TryDecrementStockAsync(productId, 2, CancellationToken.None)).Should().BeTrue();
        (await ops.TryDecrementStockAsync(productId, 5, CancellationToken.None)).Should().BeFalse();

        await using var verify = db.CreateContext();
        var stock = await verify.Products.Where(p => p.Id == productId).Select(p => p.Stock).SingleAsync();
        stock.Should().Be(1);                                  // ✓ لا سالب ولا تجاوز
    }

    [Fact]
    public async Task ExecuteUpdate_respects_tenant_query_filter()
    {
        // ★ يثبت إن التحديث الجماعي لا يمس مستأجرًا آخر
        await using var ctx = db.CreateContext(tenantId: tenantA);
        ctx.Products.AddRange(
            new Product { Id = Guid.NewGuid(), TenantId = tenantA, Sku = "A", Price = 10m },
            new Product { Id = Guid.NewGuid(), TenantId = tenantB, Sku = "B", Price = 10m });
        await ctx.SaveChangesAsync();

        var affected = await ctx.Products.ExecuteUpdateAsync(
            s => s.SetProperty(p => p.Price, 20m), CancellationToken.None);

        affected.Should().Be(1);
        var bPrice = await db.CreateContext(tenantId: tenantB).Products
            .Where(p => p.TenantId == tenantB).Select(p => p.Price).SingleAsync();
        bPrice.Should().Be(10m);                               // لم يُمَس
    }

    [Fact]
    public async Task Bulk_cancel_participates_in_transaction_and_rolls_back()
    {
        await using var ctx = db.CreateContext();
        await using var tx = await ctx.Database.BeginTransactionAsync();

        await ctx.Orders.Where(o => o.Status == OrderStatus.Abandoned)
                        .ExecuteUpdateAsync(s => s.SetProperty(o => o.Status, OrderStatus.Cancelled));

        await tx.RollbackAsync();

        var stillAbandoned = await ctx.Orders.CountAsync(o => o.Status == OrderStatus.Abandoned);
        stillAbandoned.Should().BeGreaterThan(0);              // ✓ لا تغيير بعد التراجع
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أستخدم `ExecuteUpdate`/`ExecuteDelete` للتغييرات الميكانيكية الجماعية بشرط `WHERE` حارس وفحص للصفوف.",
                "أعوّض ما يُتجاوز: audit، concurrency، أحداث/ـoutbox، وإبطال الكاش.",
                "أختار أداة الإدراج الضخم بحسب الحجم (`AddRange` ← دفعات ← `COPY`/upsert).",
                "أختبر الكتابات الجماعية على قاعدة حقيقية (تعارض، عزل مستأجرين، rollback).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`ExecuteUpdateAsync` رجّع 0. إيه التصرف؟",
                 "options": [
                     "اعمل commit عادي",
                     "افحص السبب (الشرط الحارس لم يتحقق/المورد غير موجود) وتعامل معه كحالة عمل صريحة",
                     "أعد المحاولة 10 مرات",
                     "ارمِ 500",
                 ], "answer": 1,
                 "explain": "0 صفوف متأثرة ليست خطأً تقنيًا — هي غالبًا إشارة عمل (مخزون غير كافٍ، حالة تغيّرت). ميّز الحالات برسائل مختلفة."},
                {"q": "ليه لازم تحدّث `UpdatedAt` بنفسك مع `ExecuteUpdate`؟",
                 "options": [
                     "متطلب ترجمة",
                     "لأن `SaveChanges` interceptors والـauditing لا تعمل في هذا المسار",
                     "لأن EF لا يعرف الوقت",
                     "لتسريع الاستعلام",
                 ], "answer": 1,
                 "explain": "كل ما هو مبني على SaveChanges (audit، أحداث، outbox) يتجاوز. عوّضه صراحة أو استخدم المسار التقليدي."},
                {"q": "تحديث سعر 50 ألف منتج — أنهي طريقة؟",
                 "options": [
                     "تحميل الكيانات وتعديلها وحفظها",
                     "`ExecuteUpdateAsync` بشرط وفحص للصفوف (ومهمة خلفية لو الحجم كبير)",
                     "حذف وإعادة إدراج",
                     "Dapper لكل صف",
                 ], "answer": 1,
                 "explain": "عبارة واحدة داخل القاعدة، بلا نقل بيانات. ولو هياخد وقتًا طويلًا: نقله لمهمة خلفية بدفعات (درس الجدولة)."},
                {"q": "بعد `ExecuteUpdate`، الكيانات المحمّلة في نفس الـDbContext…؟",
                 "options": [
                     "تُحدَّث تلقائيًا",
                     "تبقى قديمة (stale) — `ChangeTracker.Clear()` أو context منفصل قبل القراءة التالية",
                     "تسبب استثناء",
                     "تُحذف",
                 ], "answer": 1,
                 "explain": "التحديث حدث في القاعدة فقط. القراءة من الـtracker هترجع قيم ما قبل التحديث → باج صامت."},
                {"q": "إدراج 500 ألف صف في استيراد ليلي — الأداة الأنسب؟",
                 "options": [
                     "`AddRange` + `SaveChanges` مرة واحدة",
                     "مهمة خلفية مع `COPY` binary على دفعات (وعزل عن مسار الطلب)",
                     "Dapper صفًا صفًا",
                     "`ExecuteUpdate`",
                 ], "answer": 1,
                 "explain": "`COPY` أسرع بعشرات المرات، والدفعات تحمي الذاكرة، والمهمة الخلفية تعزل الأثر عن المستخدمين."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تحويل مسار جماعي لـExecuteUpdate",
                 "md": "اختار عملية في مشروعك بتحمّل كيانات وتعدّلها (تنظيف، تغيير حالة، تسعير) وحوّلها لـ`ExecuteUpdateAsync` بشرط حارس وفحص للصفوف وتعويض للـaudit. قِس الزمن والذاكرة قبل/بعد على 10 آلاف صف.",
                 "criteria": [
                     "شرط `WHERE` يضمن الأمان (لا تحديث أوسع من المقصود) + حد أقصى للحجم",
                     "`UpdatedAt`/`UpdatedBy` مضبوطة صراحة",
                     "قياس مسجل: زمن قبل/بعد وعدد الصفوف",
                     "إبطال كاش/إشعار بعد الالتزام (لو فيه كاش على البيانات دي)",
                     "3 اختبارات: نجاح، شرط حارس فاشل (0 صفوف)، rollback داخل معاملة",
                 ],
                 "hint": "لو الاختبارات على InMemory/SQLite بتفشل: `ExecuteUpdate` يحتاج مزوّدًا علائقيًا حقيقيًا — استخدم Testcontainers (Postgres)."},
                {"id": "t2", "title": "استيراد ضخم",
                 "md": "ابنِ مسار استيراد (CSV/JSON) لجدول كبير باستخدام upsert ذرّي (`ON CONFLICT`) أو `COPY`، داخل مهمة خلفية بدفعات، مع تقرير نتيجة (مدرج/محدّث/مرفوض) ومعالجة أخطاء الصفوف دون إيقاف الاستيراد.",
                 "criteria": [
                     "50 ألف صف تُستورد في أقل من 15 ثانية على جهازك (رقم مسجل)",
                     "صف تالف لا يوقف الاستيراد ويُبلَّغ في التقرير",
                     "الاستيراد idempotent (تشغيله مرتين لا يكرر البيانات)",
                     "يعمل كمهمة خلفية (202 + تقدّم) مش داخل مسار الطلب",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "EF Core — ExecuteUpdate / ExecuteDelete", "url": "https://learn.microsoft.com/ef/core/saving/execute-insert-update-delete"},
                {"label": "EF Core — Bulk operations guidance", "url": "https://learn.microsoft.com/ef/core/performance/"},
                {"label": "EF Core — Raw SQL", "url": "https://learn.microsoft.com/ef/core/querying/raw-sql"},
                {"label": "PostgreSQL — INSERT ON CONFLICT (upsert)", "url": "https://www.postgresql.org/docs/current/sql-insert.html"},
                {"label": "Npgsql — COPY / binary import", "url": "https://www.npgsql.org/doc/copy.html"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l4
    {
        "id": "s3-m2-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الـmigrations بتشتغل بسهولة على جهازك. المشاكل بتبدأ لما: فريق من 6 مطورين بيضيفوا migrations في نفس الأسبوع،
والنشر بيحصل على قاعدة فيها 40 مليون صف، والنظام **ما ينفعش يقف**.

الدرس ده: نمط **expand/contract** للتغييرات بلا توقف، قواعد SQL اللي بتقفل الجداول وإزاي تتجنبها،
إدارة تعارضات الـmigrations بين المطورين، ونشر آمن من الـpipeline (بما فيه: مين يطبّق ومتى).
"""},
            {"type": "terms", "items": [
                {"term": "Expand / Contract (Parallel Change)", "def": "أضف الجديد ← انقل/ازدوج الكتابة ← حوّل القراءة ← احذف القديم. كل خطوة نشر منفصل ومتوافق."},
                {"term": "Model Snapshot", "def": "ملف `ModelSnapshot.cs` يمثّل حالة النموذج الحالية — مصدر توليد الـmigration التالية (ومصدر أغلب تعارضات الفريق)."},
                {"term": "`__EFMigrationsHistory`", "def": "جدول يسجل الـmigrations المطبقة — أساس `--idempotent` وتتبّع الحالة."},
                {"term": "Idempotent Script", "def": "SQL يُطبّق بأمان مهما كانت الحالة الحالية (يفحص التاريخ قبل التنفيذ)."},
                {"term": "`ACCESS EXCLUSIVE` lock", "def": "أقوى قفل في Postgres: يمنع القراءة والكتابة. أي DDL بياخده على الجدول = توقف لحظي."},
                {"term": "`NOT VALID` + `VALIDATE CONSTRAINT`", "def": "طريقة إضافة قيد بأقل قفل: يُطبق فورًا على الجديد، ثم يُتحقق من القديم بقفل ضعيف."},
                {"term": "Data Migration / Backfill", "def": "نقل/تحويل بيانات موجودة — لازم يكون بدفعات وقابلًا للإعادة (idempotent)."},
                {"term": "Forward-fix", "def": "سياسة الإنتاج: لا تراجع (Down) — صلّح للأمام بـmigration جديد."},
            ]},
            {"type": "heading", "level": 2, "text": "1) أي DDL بيقفل الجدول؟ (Postgres)"},
            {"type": "table", "head": ["العملية", "القفل", "الخطر", "البديل الآمن"], "rows": [
                ["`ADD COLUMN` (بلا default متغيّر)", "لحظي (PG 11+)", "منخفض", "—"],
                ["`ADD COLUMN … DEFAULT <ثابت>`", "لحظي (PG 11+)", "منخفض", "—"],
                ["`ADD COLUMN … DEFAULT <تعبير متغيّر>`", "**إعادة كتابة الجدول**", "عالي جدًا", "أضف nullable ثم املأ بدفعات"],
                ["`SET NOT NULL`", "**ACCESS EXCLUSIVE + فحص كامل**", "عالي على جدول كبير", "`ADD CONSTRAINT … NOT VALID` ثم `VALIDATE CONSTRAINT`"],
                ["`DROP COLUMN`", "لحظي", "متوسط (الكود القديم)", "expand/contract: أوقف الاستخدام أولًا"],
                ["`RENAME COLUMN`", "لحظي لكن **يكسر الكود القديم**", "عالي", "أضف عمودًا جديدًا، ازدوج، ثم احذف"],
                ["`ALTER COLUMN TYPE`", "**إعادة كتابة الجدول + الفهارس**", "عالي جدًا", "عمود جديد بالنوع المطلوب + backfill + تبديل"],
                ["`CREATE INDEX`", "**SHARE (يمنع الكتابة)**", "عالي", "`CREATE INDEX CONCURRENTLY`"],
                ["`REINDEX`", "يقفل الجدول", "عالي", "`REINDEX CONCURRENTLY`"],
                ["`ADD FOREIGN KEY`", "يفحص الجدول (SHARE ROW EXCLUSIVE)", "متوسط", "`NOT VALID` ثم `VALIDATE CONSTRAINT`"],
                ["`UPDATE` ضخم في معاملة واحدة", "أقفال صفية طويلة + تضخم WAL", "عالي", "دفعات بـ`LIMIT` في معاملات صغيرة"],
            ]},
            {"type": "code", "lang": "sql", "filename": "migrations/safe_patterns.sql", "title": "الأنماط الآمنة في Postgres", "code": r'''
-- ① NOT NULL بلا توقف
ALTER TABLE orders ADD CONSTRAINT orders_note_not_null
    CHECK (shipping_note IS NOT NULL) NOT VALID;          -- يطبق على الجديد فورًا (قفل لحظي)
-- املأ الصفوف القديمة بدفعات في مهمة خلفية… ثم:
ALTER TABLE orders VALIDATE CONSTRAINT orders_note_not_null;   -- SHARE UPDATE EXCLUSIVE: لا يمنع القراءة/الكتابة

-- ② فهرس بلا قفل كتابة (لا يعمل داخل transaction!)
CREATE INDEX CONCURRENTLY ix_orders_note ON orders (shipping_note);

-- ③ FK بلا فحص طويل
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer;

-- ④ backfill بدفعات (لا معاملة واحدة على 40 مليون صف)
DO $$
DECLARE rows_updated int := 1;
BEGIN
  WHILE rows_updated > 0 LOOP
    WITH batch AS (
      SELECT id FROM orders
      WHERE country IS NULL AND created_at > now() - interval '90 days'
      LIMIT 5000
      FOR UPDATE SKIP LOCKED
    )
    UPDATE orders o
       SET country = c.country
      FROM batch b JOIN customers c ON c.id = o.customer_id
     WHERE o.id = b.id;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    COMMIT;                                               -- PG 11+: COMMIT داخل DO block
    PERFORM pg_sleep(0.05);                               -- اترك مجالًا للحمل الحي
  END LOOP;
END $$;

-- ⑤ تحقق من الأقفال قبل/أثناء التطبيق
SELECT relation::regclass AS locked_object, mode, granted, pid
FROM pg_locks WHERE NOT granted;
'''},
            {"type": "heading", "level": 2, "text": "2) expand/contract: إعادة تسمية عمود بلا توقف"},
            {"type": "code", "lang": "csharp", "filename": "4 migrations · 3 نشرات", "title": "الخطوات الكاملة لتغيير `total` إلى `amount` + `currency`", "code": r'''
// ══════ الخطوة 1 (EXPAND): أضف الجديد — متوافق مع الكود القديم ══════
// Migration: 20261022_01_AddAmountColumns
migrationBuilder.AddColumn<decimal>("amount", "orders", type: "numeric(18,2)", nullable: true);
migrationBuilder.AddColumn<string>("currency", "orders", type: "character(3)", nullable: true, fixedLength: true);
// + data migration: انسخ القيم القديمة (بدفعات لو الجدول ضخم)
migrationBuilder.Sql("""
    UPDATE orders SET amount = total, currency = 'EGP'
    WHERE amount IS NULL AND id IN (SELECT id FROM orders WHERE amount IS NULL LIMIT 50000);
    """, suppressTransaction: false);

// ══════ الكود (نفس النشرة): ازدواج الكتابة، قراءة من الجديد ══════
// SaveChanges: order.Amount = order.Total; order.Currency ??= "EGP";
// القراءة: SELECT amount, currency (مع fallback: COALESCE(amount, total))

// ══════ الخطوة 2 (MIGRATE): بعد التأكد من استقرار القراءة على الجديد ══════
// Migration: 20261105_01_MakeAmountRequired  (نشرة تانية، بعد أيام)
migrationBuilder.Sql("ALTER TABLE orders ADD CONSTRAINT orders_amount_not_null CHECK (amount IS NOT NULL) NOT VALID;");
// …بعد اكتمال الـbackfill:
migrationBuilder.Sql("ALTER TABLE orders VALIDATE CONSTRAINT orders_amount_not_null;");

// ══════ الخطوة 3 (CONTRACT): احذف القديم — بعد نشر كل الخدمات ══════
// Migration: 20261120_01_DropTotalColumn  (نشرة تالتة)
migrationBuilder.DropColumn("total", "orders");

// قواعد الحاكمة:
// • كل خطوة = migration + نشرة منفصلة، والنظام يعمل في كل لحظة (old code + new schema ✅)
// • لا تحذف عمودًا إلا بعد التأكد إن **كل** المستهلكين (خدمات، تقارير، BI، مهام) توقفوا عنه
// • احتفظ بـ`Down()` للتطوير فقط؛ في الإنتاج السياسة forward-fix
'''},
            {"type": "callout", "kind": "warn", "title": "لما يكون expand/contract مبالغة؟",
             "md": """
مش كل تغيير يستحق 3 نشرات. قيّم بحسب:
- **حجم الجدول**: جدول بـ10 آلاف صف ≠ 40 مليون صف.
- **نافذة التوقف**: فيه صيانة ليلية؟ يبقى تغيير مباشر مقبول.
- **عدد المستهلكين**: خدمة واحدة = نشر ذرّي (الكود + الـmigration معًا) ممكن.
- **خطر القفل**: `ADD COLUMN` nullable = آمن دائمًا تقريبًا؛ `ALTER TYPE` = خطر دائمًا.

القاعدة العملية: **التغييرات الآمنة لحظيًا تُنفَّذ مباشرة، والتغييرات المقفلة/الكاسرة تمر عبر expand/contract.**
"""},
            {"type": "heading", "level": 2, "text": "3) الفريق: تعارضات الـmigrations والـsnapshot"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "سير العمل اليومي", "code": r'''
# أدوات EF (ثبّت الإصدار المطابق لإصدار مشروعك)
dotnet tool install -g dotnet-ef
dotnet ef --version

# إضافة migration (اسم واضح: فعل + مفعول)
dotnet ef migrations add AddOrderAuditColumns --project Shop.Infrastructure --startup-project Shop.Api
dotnet ef migrations list --project Shop.Infrastructure --startup-project Shop.Api

# مراجعة الـSQL قبل التطبيق (أهم خطوة في المراجعة!)
dotnet ef migrations script --idempotent --project Shop.Infrastructure --startup-project Shop.Api -o review.sql

# التراجع عن migration **لم يُطبَّق** (محليًا فقط)
dotnet ef migrations remove --project Shop.Infrastructure --startup-project Shop.Api

# هل فيه تغييرات في النموذج بلا migration؟ (يُستخدم كحارس في CI)
dotnet ef migrations has-pending-model-changes --project Shop.Infrastructure --startup-project Shop.Api
'''},
            {"type": "steps", "title": "قواعد الفريق (بتوفر ساعات من حل التعارضات)", "items": [
                {"title": "migration واحد لكل PR",
                 "md": "PR فيه تغييران غير مرتبطان = تعارض شبه مضمون مع الفروع التانية. قسّم الشغل."},
                {"title": "أسماء موحّدة وتواريخ واضحة",
                 "md": "`AddOrderAuditColumns`، `BackfillCustomerCountry` — الاسم يشرح النية في سجل الـmigrations."},
                {"title": "لا تعدّل migration مُطبَّق أبدًا",
                 "md": "تعديل ملف مطبّق = بيئات مختلفة. أضف migration جديد (forward-fix). ولو محليًا لم يُطبَّق: `migrations remove` ثم أعد الإنشاء."},
                {"title": "حل تعارض الـsnapshot بطريقة واحدة",
                 "md": "الخطوات: ادمج فرع `main` ← احذف migration المحلي (`dotnet ef migrations remove`) ← أعد إنشاءه (`migrations add`) ← راجع الـSQL الناتج. **لا تدمج `ModelSnapshot.cs` يدويًا سطر بسطر** إلا لو فاهم تمامًا."},
                {"title": "راجع الـSQL في الـPR مش ملفات C#",
                 "md": "الـmigration كود مولّد؛ المراجعة الحقيقية على `dotnet ef migrations script` — هناك تظهر الأقفال وإعادة كتابة الجداول."},
                {"title": "الـbackfill يفصل عن تغيير الشكل",
                 "md": "migration يضيف العمود + مهمة/سكربت منفصل يملأ البيانات. خلطهم في معاملة واحدة = قفل طويل وفشل صامت."},
                {"title": "اختبار مسار الترقية",
                 "md": "في CI: ابدأ من نسخة القاعدة السابقة (أو من backup مصغّر)، طبّق الـmigrations، وشغّل الاختبارات. ده بيكشف migrations بتشتغل على قاعدة فاضية بس."},
            ]},
            {"type": "code", "lang": "yaml", "filename": ".github/workflows/migrations.yml", "title": "CI/CD: حراسة + توليد + تطبيق آمن", "code": r'''
name: migrations

on:
  pull_request:
    paths: ["src/**", "migrations/**"]
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: "10.0.x" }

      - name: Install EF tools
        run: dotnet tool install -g dotnet-ef

      - name: Build
        run: dotnet build --configuration Release --warnaserror

      # ★ حارس: تغيير في النموذج بلا migration = فشل
      - name: No pending model changes
        run: dotnet ef migrations has-pending-model-changes
               --project src/Shop.Infrastructure --startup-project src/Shop.Api

      # ★ حارس: الـmigrations تُطبَّق على قاعدة حقيقية (Testcontainers) وتختبر
      - name: Integration tests (migrate + tests)
        run: dotnet test --filter Category=Integration --configuration Release

      - name: Generate idempotent SQL (artifact للمراجعة)
        run: |
          dotnet ef migrations script --idempotent \
            --project src/Shop.Infrastructure --startup-project src/Shop.Api \
            -o artifacts/migrations.sql
      - uses: actions/upload-artifact@v4
        with: { name: migrations-sql, path: artifacts/migrations.sql }

  apply:
    needs: verify
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production            # حماية + موافقة يدوية
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with: { creds: ${{ secrets.AZURE_CREDENTIALS }} }

      # ★ مهمة منفصلة قبل النشر: قفل استشاري يمنع تطبيقين متزامنين
      - name: Apply migrations (with advisory lock)
        run: |
          psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
          SELECT pg_advisory_lock(9001);          -- قفل واحد لكل التطبيقين
          SQL
          dotnet ef database update --project src/Shop.Infrastructure --startup-project src/Shop.Api
          psql "$DATABASE_URL" -c "SELECT pg_advisory_unlock(9001);"

      - name: Deploy application
        run: ./deploy.sh                          # بعد نجاح الـmigrations فقط
'''},
            {"type": "callout", "kind": "danger", "title": "`MigrateAsync` عند الإقلاع: إمتى مقبول وإمتى خطر",
             "md": """
```csharp
// مقبول: بيئة تطوير، أو نسخة واحدة، أو مهام قصيرة
using var scope = app.Services.CreateScope();
await scope.ServiceProvider.GetRequiredService<AppDbContext>().Database.MigrateAsync(ct);
```

**خطر في الإنتاج مع عدة نسخ**: كل النسخ بتحاول التطبيق في نفس اللحظة → سباق، أقفال، وفشل جزئي.
ولو migration فيه `CREATE INDEX` (بلا `CONCURRENTLY`) → قفل كتابة على جدول كبير أثناء النشر.

البدائل بالترتيب الأفضل:
1. **خطوة منفصلة في الـpipeline** (زي الـworkflow أعلاه) قبل النشر — أوضح وأسهل تدقيقًا.
2. **مهمة/Job منفصلة** (K8s Job أو init container) مع **قفل استشاري** في القاعدة.
3. **leader election** بين النسخ ثم `MigrateAsync` (معقّد — تجنبه إلا لو مضطر).

وفي كل الحالات: `expand/contract` عشان الكود القديم يشتغل مع الـschema الجديد أثناء التدرج في النشر.
"""},
            {"type": "heading", "level": 2, "text": "4) اختبار الـmigrations"},
            {"type": "code", "lang": "csharp", "title": "اختبار مسار الترقية (مش قاعدة فاضية فقط)", "code": r'''
public sealed class MigrationTests
{
    /// <summary>كل الـmigrations تُطبَّق بالترتيب على قاعدة حقيقية.</summary>
    [Fact]
    public async Task All_migrations_apply_in_order()
    {
        await using var container = new PostgreSqlBuilder().WithImage("postgres:17-alpine").Build();
        await container.StartAsync();

        var options = new DbContextOptionsBuilder<AppDbContext>().UseNpgsql(container.GetConnectionString()).Options;
        await using var db = new AppDbContext(options, new FixedTenantContext(tenantId));

        var migrator = db.GetService<IMigrator>();
        var applied = new List<string>();

        foreach (var migration in db.Database.GetMigrations())
        {
            await migrator.MigrateAsync(migration, CancellationToken.None);   // واحدة واحدة
            applied.Add(migration);
        }

        applied.Should().HaveCountGreaterThan(5);
        await db.Database.ExecuteSqlRawAsync("SELECT 1");                    // الاتصال سليم
    }

    /// <summary>
    /// مسار الترقية: ابدأ من حالة الإصدار السابق، طبّق الجديد، وتأكد إن البيانات اتحافظت.
    /// ده الاختبار اللي بيكشف migrations بتشتغل بس على قاعدة فاضية.
    /// </summary>
    [Fact]
    public async Task Upgrade_from_previous_release_preserves_data()
    {
        await using var container = new PostgreSqlBuilder().WithImage("postgres:17-alpine").Build();
        await container.StartAsync();
        var cs = container.GetConnectionString();

        // 1) ابنِ حالة الإصدار السابق (من snapshot قديم أو من dump مصغّر)
        await ApplyUpToAsync(cs, "20261001_00_PreAuditColumns");
        await SeedLegacyDataAsync(cs);

        // 2) طبّق كل ما هو جديد
        await ApplyUpToAsync(cs, targetMigration: null);

        // 3) تحقق: البيانات القديمة لسه مقروءة بالنموذج الجديد
        var options = new DbContextOptionsBuilder<AppDbContext>().UseNpgsql(cs).Options;
        await using var db = new AppDbContext(options, new FixedTenantContext(tenantId));

        var orders = await db.Orders.ToListAsync();
        orders.Should().NotBeEmpty();
        orders.Should().OnlyContain(o => o.Currency == "EGP");               // القيمة الافتراضية للـbackfill
        orders.Should().OnlyContain(o => o.Amount > 0);                      // البيانات القديمة اتنقلت
    }

    private static async Task ApplyUpToAsync(string cs, string? targetMigration) { /* IMigrator.MigrateAsync */ await Task.CompletedTask; }
    private static async Task SeedLegacyDataAsync(string cs) { /* INSERT بالـschema القديم */ await Task.CompletedTask; }
}
'''},
            {"type": "table", "head": ["البند", "المطلوب", "أداة/مكان"], "rows": [
                ["تغيير نموذج بلا migration", "فشل الـPR", "`dotnet ef migrations has-pending-model-changes`"],
                ["الـSQL المولّد", "مراجعة بشرية في كل PR", "`migrations script --idempotent` كـartifact"],
                ["التطبيق على قاعدة حقيقية", "ناجح في كل PR", "اختبارات Integration بـTestcontainers"],
                ["مسار الترقية من الإصدار السابق", "ناجح قبل النشر", "اختبار `Upgrade_from_previous_release`"],
                ["أقفال DDL الخطرة", "لا `SET NOT NULL`/`ALTER TYPE`/`CREATE INDEX` مباشر على جداول كبيرة", "مراجعة + `pg_stat_activity` وقت التطبيق"],
                ["التطبيق المتزامن", "ممنوع", "قفل استشاري أو خطوة pipeline واحدة"],
                ["Backfill ضخم", "بدفعات وخارج المعاملة الطويلة", "سكربت/مهمة منفصلة قابلة لإعادة التشغيل"],
                ["التراجع", "forward-fix موثق + نسخة احتياطية قبل التغييرات الكبيرة", "سياسة الفريق + `pg_dump`/snapshot"],
            ]},
            {"type": "checkpoints", "items": [
                "أطبّق expand/contract للتغييرات الكاسرة وأعرف أنهي DDL بيقفل الجدول وإزاي أتجنبه.",
                "أستخدم `NOT VALID` + `VALIDATE CONSTRAINT` و`CREATE INDEX CONCURRENTLY` على الجداول الكبيرة.",
                "أدير تعارضات الـmigrations في الفريق بقواعد واضحة (PR واحد، لا تعديل مطبَّق، حل الـsnapshot بطريقة واحدة).",
                "أنشر الـmigrations من خطوة منفصلة بقفل استشاري، وأحمي بـCI (pending changes + SQL artifact + مسار ترقية).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`ALTER COLUMN total TYPE numeric(18,4)` على جدول 40 مليون صف — تقييمك؟",
                 "options": [
                     "آمن، لحظي",
                     "يعيد كتابة الجدول والفهارس بقفل ACCESS EXCLUSIVE → توقف؛ البديل: عمود جديد بالنوع + backfill بدفعات + تبديل",
                     "يحتاج فهرس فقط",
                     "آمن لو في الليل",
                 ], "answer": 1,
                 "explain": "تغيير النوع من أخطر عمليات DDL. expand/contract هو الطريق، أو نافذة صيانة معلنة."},
                {"q": "ليه `ADD CONSTRAINT … NOT VALID` ثم `VALIDATE CONSTRAINT`؟",
                 "options": [
                     "أسرع في الكتابة",
                     "القيد يُطبق فورًا على الكتابات الجديدة بقفل لحظي، والتحقق من البيانات القديمة يتم بقفل لا يمنع القراءة/الكتابة",
                     "يتجنب الحاجة للـbackfill",
                     "يعمل فهرس تلقائيًا",
                 ], "answer": 1,
                 "explain": "`SET NOT NULL` العادي يفحص الجدول كله بقفل ACCESS EXCLUSIVE. التقسيم ده بيخلي الإضافة بلا توقف."},
                {"q": "3 نسخ في K8s وكل واحدة بتنادي `MigrateAsync` عند الإقلاع. المشكلة؟",
                 "options": [
                     "لا مشكلة",
                     "سباق على التطبيق + أقفال متعارضة + فشل عشوائي أثناء النشر؛ الحل خطوة منفصلة أو Job بقفل استشاري",
                     "بطء الإقلاع فقط",
                     "تكرار البيانات",
                 ], "answer": 1,
                 "explain": "الهجرة مهمة **واحدة** لكل نشر. خليها خطوة pipeline أو Job منفصل، أو على الأقل بقفل استشاري في القاعدة."},
                {"q": "مطوّر عدّل ملف migration مُطبَّق بالفعل في الإنتاج. التصرف؟",
                 "options": [
                     "اعمل force apply",
                     "ارفض التغيير: أضف migration جديدًا يصحّح الحالة (forward-fix) — التعديل يخلق فرقًا بين البيئات",
                     "احذف الجدول وأعد إنشاءه",
                     "عدّل الـsnapshot يدويًا",
                 ], "answer": 1,
                 "explain": "جدول `__EFMigrationsHistory` بيقول إن النسخة دي اتطبقت؛ التعديل لن يُنفَّذ في البيئات القائمة → فرق صامت وخطير."},
                {"q": "أهم artifact لمراجعة migration في الـPR؟",
                 "options": [
                     "ملف الـDesigner",
                     "الـSQL المولّد (`migrations script`) — فيه تظهر الأقفال وإعادة كتابة الجداول",
                     "الـModelSnapshot",
                     "اسم الـmigration",
                 ], "answer": 1,
                 "explain": "كود الـmigration مولّد ومرتّب؛ المخاطر الحقيقية (DDL مقفل، UPDATE ضخم) تظهر في SQL."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تغيير كاسر بطريقة expand/contract",
                 "md": "اختار تغييرًا كاسرًا حقيقيًا في مشروعك (إعادة تسمية عمود، تغيير نوع، فصل عمود إلى اثنين) ونفّذه عبر 3 migrations و3 نشرات مفترضة، مع backfill بدفعات. وثّق كل خطوة وما الذي يحدث لو نشر الكود القديم على الـschema الجديد.",
                 "criteria": [
                     "لا DDL بيقفل الجدول في أي خطوة (راجع الـSQL المولّد واحفظه)",
                     "backfill بدفعات مع `LIMIT`/`SKIP LOCKED` وقابل لإعادة التشغيل (idempotent)",
                     "جدول توافق: كل نشرة × كل نسخة كود → يعمل/لا يعمل (مع التبرير)",
                     "اختبار مسار الترقية ينجح (من الحالة القديمة للبيانات إلى الجديدة)",
                 ],
                 "hint": "لو عايز تجربة حقيقية: املأ جدولًا بمليون صف بـ`generate_series` في Testcontainers، وقِس مدة كل DDL (`\\timing` في psql) — هتشوف الفرق بين `SET NOT NULL` و`NOT VALID` بنفسك."},
                {"id": "t2", "title": "حراسة الـmigrations في CI",
                 "md": "أضف في الـpipeline: `has-pending-model-changes`، توليد SQL idempotent كـartifact، اختبار كل الـmigrations بالترتيب على Testcontainers، واختبار ترقية من الإصدار السابق. وطبّق الـmigrations في خطوة منفصلة بقفل استشاري قبل النشر.",
                 "criteria": [
                     "PR فيه تغيير نموذج بلا migration → فشل (جرّبه)",
                     "artifact بالـSQL متاح للمراجعة في كل PR",
                     "اختبار يطبّق كل الـmigrations واحدة واحدة وينجح",
                     "خطوة التطبيق تستخدم قفلًا استشاريًا (أو Job منفصل) و`ON_ERROR_STOP=1`",
                     "سياسة forward-fix مكتوبة في CONTRIBUTING/README",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "EF Core — Migrations", "url": "https://learn.microsoft.com/ef/core/managing-schemas/migrations/"},
                {"label": "EF Core — Migrations in team environments", "url": "https://learn.microsoft.com/ef/core/managing-schemas/migrations/teams"},
                {"label": "EF Core — Applying migrations (production guidance)", "url": "https://learn.microsoft.com/ef/core/managing-schemas/migrations/applying"},
                {"label": "PostgreSQL — Explicit Locking", "url": "https://www.postgresql.org/docs/current/explicit-locking.html"},
                {"label": "PostgreSQL — ALTER TABLE", "url": "https://www.postgresql.org/docs/current/sql-altertable.html"},
                {"label": "Refactoring Databases — Expansion/Contraction", "url": "https://www.prisma.io/dataguides/expand-and-contract"},
            ]},
        ],
    },
]
