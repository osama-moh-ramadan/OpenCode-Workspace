/* الوحدة 10 — المشروع والوظيفة: بناء Souq.NET ونشره والاستعداد للسوق. */
Academy.addModule({
  id: "career",
  title: "المشروع والوظيفة",
  tagline: "الدرس الأخير ليس نهاية التعلم؛ هو أول نسخة تصلح أن تعرضها وتنشرها وتدافع عن قراراتها.",
  icon: "★",
  color: "#f59e0b",
  lessons: [
    {
      id: "capstone-build",
      title: "Capstone Build: تجميع Souq.NET كاملًا",
      duration: 36,
      level: "متقدم",
      summary:
        "سنحوّل الدروس إلى تطبيق واحد متماسك: كتالوج، سلة، طلبات، دفع، صلاحيات، اختبارات، وعقد API. لا صفحات وهمية ولا ميزات نصف مكتملة.",
      keywords: ["capstone", "solution structure", "catalog", "cart", "orders", "payments", "outbox", "seed data"],
      objectives: [
        "تجمّع الحل في مشاريع وحدود واضحة.",
        "تربط الكتالوج والسلة والطلب والدفع في تدفق واحد.",
        "تحدد المعاملات والـidempotency في المسار الحرج.",
        "تضيف بيانات تجريبية واختبارات نهاية إلى نهاية.",
        "تتحقق من قائمة اكتمال المشروع قبل النشر."
      ],
      concept: `
        <p>المشروع النهائي ليس مجموع الدروس. هو قرارات مترابطة: من يملك البيانات؟ أين تنتهي المعاملة؟ ماذا يحدث إذا فشل الدفع؟ كيف نمنع طلبًا مكررًا؟ سنبني نسخة واحدة قابلة للتشغيل، لا مخططًا نظريًا.</p>
        <h3>حدود الحل</h3>
        <p>ابدأ بمشاريع واضحة: <code>Souq.Api</code>، <code>Souq.Domain</code>، <code>Souq.Infrastructure</code>، واختبارات. يمكن تقسيم المجال إلى modules داخلية (Catalog/Orders/Payments) دون إنشاء خدمة لكل module. الـAPI يعرض HTTPS وJSON وProblemDetails. الـDomain لا يعرف EF Core. Infrastructure يملك DbContext والتكاملات.</p>
        <h3>التدفق الحرج</h3>
        <p>المستخدم يتصفح المنتجات، يضيف للسلة، ينشئ طلبًا، يدفع، ثم يرى حالته. السلة قد تكون client-side أو server-side؛ اختر واحدة ووثّقها. إنشاء الطلب يجب أن يتحقق من المخزون والسعر، ويحفظ snapshot، ويكتب Outbox، ويكون idempotent. الدفع لا يحدث داخل معاملة قاعدة البيانات؛ استخدم حالة Pending ثم تأكيدًا عبر webhook/event.</p>
        <h3>المعاملات</h3>
        <p>حفظ الطلب وسطوره وحدث <code>OrderPlaced</code> في معاملة واحدة. خصم المخزون قد يكون في نفس المعاملة إذا كان داخل نفس قاعدة البيانات، أو عبر سياسة تعويض/حجز. لا تجمع اتصال مزود الدفع في المعاملة. افصل: اطلب الدفع، احفظ الحالة Pending، ثم استقبل التأكيد وتحقق من التوقيع/idempotency.</p>
        <h3>الأمان</h3>
        <p>JWT للمصادقة، سياسات للتفويض، وفحص ملكية الطلب. لا تعتمد على إخفاء المعرفات. استخدم DTOs للمدخلات، وRate Limiting للمسارات الحساسة. الأسرار في البيئة/خزنة. لا تسجّل التوكن أو بيانات البطاقة. استخدم HTTPS وHSTS في الإنتاج.</p>
        <h3>العقد والاختبار</h3>
        <p>OpenAPI موثّق، أخطاء موحدة، ترقيم صفحات، وإصدارات. اختبارات وحدة للمنطق، تكامل لـAPI/DB، واختبار E2E لمسار الشراء. Smoke tests بعد النشر. لا تعتبر المشروع مكتملًا إذا كان يعمل محليًا فقط؛ يجب أن يعمل من صورة/Compose مع بيانات مهيأة.</p>
        <h3>قائمة الاكتمال</h3>
        <p>تسجيل/دخول، كتالوج، بحث/ترقيم، سلة، طلب، دفع (محاكاة على الأقل)، حالة الطلب، لوحة إدارة، صلاحيات، Outbox، مراقبة، اختبارات، README، وبيانات seed. كل عنصر يجب أن يكون قابلًا للتجربة، لا وعدًا في الوثائق.</p>
      `,
      walkthrough: [
        {
          title: "هيكل الحل",
          code: `Souq.sln\nsrc/\n  Souq.Api/\n  Souq.Domain/\n  Souq.Infrastructure/\ntests/\n  Souq.UnitTests/\n  Souq.IntegrationTests/\ndocker-compose.yml\nREADME.md`,
          lang: "text",
          body: `<p>ابدأ بهيكل صغير. لا تنشئ 12 مشروعًا قبل الحاجة. <code>Domain</code> للكيانات والقواعد، <code>Infrastructure</code> لـEF والتكاملات، <code>Api</code> للعقد وHTTP. أضف مشاريع الاختبار. المجلدات تعكس الحدود، لا الطبقات فقط.</p>`
        },
        {
          title: "نموذج البيانات الأساسي",
          code: `public sealed class Product\n{\n    public Guid Id { get; private set; }\n    public string Name { get; private set; } = null!;\n    public Money Price { get; private set; } = null!;\n    public int Stock { get; private set; }\n    public bool IsActive { get; private set; }\n}\n\npublic sealed class Order\n{\n    public Guid Id { get; private set; }\n    public Guid UserId { get; private set; }\n    public OrderStatus Status { get; private set; }\n    public IReadOnlyCollection<OrderLine> Lines => _lines;\n}`,
          lang: "csharp",
          body: `<p>هذه ليست كل الحقول؛ هذه الحدود الأساسية. المنتج يحمل السعر والمخزون، والطلب يحمل snapshot للسطور. استخدم <code>Money</code> بدل decimal عاري. لا تعرض الكيانات مباشرة. أضف <code>RowVersion</code> للمنتج والطلب عند الحاجة للتزامن.</p>`
        },
        {
          title: "سجّل الوحدات",
          code: `builder.Services.AddCatalog(builder.Configuration);\nbuilder.Services.AddOrders(builder.Configuration);\nbuilder.Services.AddPayments(builder.Configuration);\n\nvar app = builder.Build();\napp.MapCatalog();\napp.MapOrders();\napp.MapPayments();\napp.Run();`,
          lang: "csharp",
          body: `<p>كل module يسجّل خدماته ومساره. <code>Program.cs</code> يبقى قائمة قرارات واضحة. لا تضع كل الـendpoints فيه. رتّب middleware قبل <code>Map*</code>: HTTPS، CORS، auth، authorization، rate limiter. تأكد من أن المسارات لا تتصادم.</p>`
        },
        {
          title: "مسار الكتالوج",
          code: `group.MapGet("/products", async (\n    int page, int size, string? search,\n    CatalogDbContext db, CancellationToken ct) =>\n{\n    var query = db.Products.AsNoTracking()\n        .Where(p => p.IsActive);\n\n    if (!string.IsNullOrWhiteSpace(search))\n        query = query.Where(p => p.Name.Contains(search));\n\n    var items = await query\n        .OrderBy(p => p.Name).ThenBy(p => p.Id)\n        .Skip((Math.Max(page, 1) - 1) * Math.Clamp(size, 1, 100))\n        .Take(Math.Clamp(size, 1, 100))\n        .Select(p => new ProductDto(p.Id, p.Name, p.Price.Amount, p.Stock > 0))\n        .ToListAsync(ct);\n\n    return TypedResults.Ok(items);\n});`,
          lang: "csharp",
          body: `<p>الكتالوج عام للقراءة. استخدم <code>AsNoTracking</code> و<code>Select</code> وترتيبًا فريدًا. ابحث بـ<code>Contains</code> مع فهم أداء <code>%term%</code>؛ للبحث المتقدم استخدم full-text. لا تُرجع المخزون الحقيقي إن كان حساسًا؛ أعد <code>InStock</code>. وثّق <code>pageSize</code> والحد الأقصى.</p>`
        },
        {
          title: "إنشاء الطلب",
          code: `await using var tx = await db.Database.BeginTransactionAsync(ct);\n\nvar order = Order.Create(userId);\nforeach (var item in request.Items)\n{\n    var product = await db.Products\n        .SingleAsync(p => p.Id == item.ProductId && p.IsActive, ct);\n\n    product.DecreaseStock(item.Quantity);\n    order.AddLine(product.Id, product.Price, item.Quantity);\n}\n\norder.Place();\ndb.Orders.Add(order);\ndb.OutboxMessages.Add(OrderPlaced.From(order));\n\nawait db.SaveChangesAsync(ct);\nawait tx.CommitAsync(ct);`,
          lang: "csharp",
          body: `<p>هذا هو القلب. التحقق من المنتج، خصم المخزون، إضافة السطر، ثم Place، ثم Outbox. كل ذلك في معاملة. السعر snapshot من المنتج وقت الطلب. لا تقبل سعرًا من العميل. أضف idempotency key قبل التنفيذ. اختبر طلبين متزامنين على آخر قطعة.</p>`
        },
        {
          title: "الدفع كحالة لا كمعاملة",
          code: `order.MarkPaymentPending(paymentIntentId);\nawait db.SaveChangesAsync(ct);\n\n// لاحقًا: webhook موقّع + idempotent\nif (!await paymentVerifier.IsValidAsync(request, ct))\n    return Results.Unauthorized();\n\norder.MarkAsPaid();\nawait db.SaveChangesAsync(ct);`,
          lang: "csharp",
          body: `<p>لا تضع اتصال مزود الدفع داخل معاملة قاعدة البيانات. أنشئ PaymentIntent، احفظ Pending، ثم أكّد عبر webhook. تحقق من التوقيع، واسمح بالتكرار عبر معرف الحدث. لا تعتمد على نجاح redirect المتصفح. إذا فشل الدفع، أعد الطلب/المخزون وفق سياسة واضحة.</p>`
        },
        {
          title: "صلاحيات الملكية",
          code: `var order = await db.Orders\n    .AsNoTracking()\n    .FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId, ct);\n\nreturn order is null ? Results.NotFound() : Results.Ok(order);`,
          lang: "csharp",
          body: `<p>الطلب ليس عامًا. أضف شرط المالك في الاستعلام. استخدم 404 لمنع كشف الوجود. للإدارة، سياسة منفصلة <code>CanManageOrders</code>، لا تجعل الدور admin يمر من كل شيء. اختبر مستخدم A مع طلب B. أضف logging دون PII.</p>`
        },
        {
          title: "أخطاء موحدة",
          code: `builder.Services.AddProblemDetails();\napp.UseExceptionHandler();\napp.UseStatusCodePages();`,
          lang: "csharp",
          body: `<p>كل خطأ يجب أن يخرج بـProblemDetails وtraceId. لا ترجع stack trace. أضف <code>ValidationProblemDetails</code> لأخطاء 400. استخدم استثناءات مجال واضحة (NotFound/Conflict). سجّل الخطأ داخليًا. اختبر 400/401/403/404/409، لا happy path فقط.</p>`
        },
        {
          title: "بيانات Seed للتجربة",
          code: `if (app.Environment.IsDevelopment())\n{\n    using var scope = app.Services.CreateScope();\n    await SeedData.RunAsync(scope.ServiceProvider);\n}`,
          lang: "csharp",
          body: `<p>بيانات seed تجعل المشروع قابلًا للتجربة فورًا: تصنيفات ومنتجات ومستخدم تجريبي. لا تضع كلمات مرور إنتاج. لا تشغّل seed في production. اجعلها idempotent. أضف صورًا/روابط محلية أو صورًا افتراضية، لا تعتمد على CDN خارجي إن كان المشروع محليًا.</p>`
        },
        {
          title: "قائمة اكتمال",
          code: `[ ] تسجيل/دخول\n[ ] كتالوج + بحث + ترقيم\n[ ] سلة وطلب\n[ ] دفع محاكى + webhook\n[ ] صلاحيات وملكية\n[ ] Outbox + مراقبة\n[ ] اختبارات وحدة/تكامل/E2E\n[ ] Docker + README + seed`,
          lang: "text",
          body: `<p>لا تعلن الاكتمال قبل تجربة كل بند من واجهة/HTTP. اختبر من نسخة نظيفة: clone، compose up، migrations، seed، ثم مسار شراء. إذا احتاج خطوة يدوية غير موثقة، فالمشروع غير مكتمل. اجعل README يشرح الخطوات بالضبط.</p>`
        }
      ],
      compare: {
        intro: `<p>مجموعة دروس منفصلة ليست منتجًا. القيمة في التدفق المتماسك.</p>`,
        before: {
          label: "أجزاء منفصلة",
          lang: "text",
          title: "قبل",
          code: `products endpoint\norders endpoint\npayment endpoint\nبدون ربط أو صلاحيات أو بيانات تجريبية`,
          points: [
            "لا مسار شراء كامل.",
            "لا معاملة بين الطلب والمخزون.",
            "لا اختبار E2E.",
            "لا طريقة تشغيل موثقة."
          ]
        },
        after: {
          label: "Souq.NET",
          lang: "text",
          title: "بعد",
          code: `Catalog -> Cart -> Order -> Payment -> Status\n+ Auth + Ownership + Outbox + Tests\n+ Docker + Seed + README`,
          points: [
            "تدفق عميل كامل.",
            "معاملات وidempotency.",
            "حدود وصلاحيات.",
            "تشغيل من نسخة نظيفة."
          ]
        },
        verdict: `<p>المشروع الجيد ليس أكبر عدد endpoints؛ هو تدفق واحد مكتمل يمكن شرحه واختباره ونشره.</p>`
      },
      internals: `
        <p>الطلب يمر عبر middleware ثم endpoint ثم handler ثم domain ثم EF. عند الحفظ، Change Tracker ينتج SQL داخل معاملة. Outbox يُكتب مع الطلب. بعد commit، عامل ينشر الحدث. الدفع خارجي؛ حالته تُحدّث عبر webhook موثّق. أي خطوة خارجية يجب أن تكون idempotent.</p>
        <p>السلة قرار: client-side (localStorage) أسهل، server-side يسمح بالمزامنة بين الأجهزة. لا تخلط. إذا كانت client-side، أعد التحقق من السعر والمخزون عند إنشاء الطلب. لا تثق بأي سعر قادم من العميل.</p>
        <h3>المخزون</h3>
        <p>خصم المخزون داخل معاملة الطلب يمنع البيع الزائد في قاعدة واحدة. مع التوسع، قد تحتاج حجزًا/تعويضًا. اختبر التزامن. لا تعتمد على فحص <code>Stock &gt; 0</code> ثم تحديث منفصل بلا قيد/تزامن.</p>
        <h3>الاختبار</h3>
        <p>وحدة للمنطق (السعر، الحالة)، تكامل للـAPI/DB، وE2E لمسار الشراء. استخدم Testcontainers. أضف اختبار BOLA وتكرار الطلب. لا تجعل E2E هشًا بالاعتماد على بيانات مشتركة.</p>
      `,
      internalsTable: {
        head: ["الجزء", "المسؤولية", "اختبار"],
        rows: [
          ["Catalog", "منتجات ومخزون", "ترقيم/بحث"],
          ["Orders", "سطور وحالة", "طلب فارغ/تزامن"],
          ["Payments", "حالة الدفع", "webhook/تكرار"],
          ["Auth", "هوية وسياسات", "401/403/BOLA"],
          ["Outbox", "أحداث", "تعطل/تكرار"],
          ["E2E", "تدفق كامل", "شراء من الصفر"]
        ]
      },
      tips: [
        {
          title: "أكمل تدفقًا واحدًا",
          body: "لا تضف ميزات جديدة قبل أن يعمل الشراء من الكتالوج إلى الدفع. العمق أهم من الاتساع."
        },
        {
          title: "لا تثق بالعميل",
          body: "السعر والخصم والمخزون تُحسب/تُتحقق في الخادم. DTO لا يقبل حقولًا حساسة."
        },
        {
          title: "افصل الدفع",
          body: "لا تجعله داخل معاملة DB. Pending + webhook موقّع + idempotency."
        },
        {
          title: "اختبر نسخة نظيفة",
          body: "clone + compose + seed + شراء. إذا لم يعمل، فالمشروع غير جاهز."
        }
      ],
      quiz: [
        {
          q: "أين تحسب سعر الطلب؟",
          options: [
            "من السعر المرسل في الطلب.",
            "من سعر المنتج في الخادم وقت الإنشاء، مع snapshot.",
            "في الواجهة فقط.",
            "من خصم العميل."
          ],
          answer: 1,
          explain: "الخادم هو مصدر الحقيقة. خزّن snapshot للسعر في سطر الطلب."
        },
        {
          q: "لماذا الدفع خارج معاملة قاعدة البيانات؟",
          options: [
            "لأنه أسرع دائمًا.",
            "لأن مزود الدفع خدمة خارجية ولا يمكن ضمه لمعاملة محلية موثوقة.",
            "لأن EF لا يدعمه.",
            "لأن webhook غير آمن."
          ],
          answer: 1,
          explain: "استخدم Pending ثم تأكيدًا موثّقًا/idempotent. لا تجمع اتصال الشبكة في معاملة DB."
        },
        {
          q: "ماذا يثبت أن المشروع مكتمل؟",
          options: [
            "وجود مجلدات كثيرة.",
            "تشغيل تدفق شراء كامل من نسخة نظيفة مع اختبارات وتوثيق.",
            "عدد endpoints.",
            "استخدام أحدث مكتبة."
          ],
          answer: 1,
          explain: "الاكتمال تجربة قابلة للتكرار، لا قائمة تقنيات."
        }
      ],
      capstone: {
        title: "Souq.NET النهائي",
        goal: "جمّع تدفق الشراء كاملًا من الكتالوج إلى تأكيد الدفع، مع صلاحيات واختبارات وتشغيل موثق.",
        tasks: [
          "أنشئ الحل بمشاريع Api/Domain/Infrastructure واختبارات.",
          "نفّذ Catalog مع بحث وترقيم وDTO.",
          "نفّذ Orders مع معاملة وخفض مخزون وOutbox.",
          "نفّذ Payments بحالة Pending وwebhook موقّع/idempotent.",
          "أضف بيانات seed واختبر الشراء E2E من نسخة نظيفة."
        ],
        code: {
          lang: "csharp",
          title: "قلب الطلب",
          code: `var product = await db.Products.SingleAsync(p => p.Id == item.ProductId, ct);\nproduct.DecreaseStock(item.Quantity);\norder.AddLine(product.Id, product.Price, item.Quantity);\norder.Place();\ndb.Orders.Add(order);\ndb.OutboxMessages.Add(OrderPlaced.From(order));\nawait db.SaveChangesAsync(ct);`,
        },
      },
    },
    {
      id: "capstone-deploy",
      title: "Capstone Deploy: Docker وHTTPS وRunbook",
      duration: 32,
      level: "متقدم",
      summary:
        "المشروع الذي لا يعمل من صورة نظيفة ليس جاهزًا. سنبني Dockerfile، Compose، migrations، HTTPS، مراقبة، ونسخًا احتياطيًا.",
      keywords: ["Docker", "Compose", "reverse proxy", "HTTPS", "migrations", "backup", "smoke test", "runbook"],
      objectives: [
        "تكتب Dockerfile multi-stage صغيرًا وآمنًا.",
        "تشغّل API وPostgreSQL وRedis محليًا بـCompose.",
        "تفصل الأسرار والإعدادات بين البيئات.",
        "تنفّذ migrations وhealth checks بشكل صحيح.",
        "تخطط backup وrollback وRunbook."
      ],
      concept: `
        <p>النشر ليس نسخ ملفات. هو إعادة إنتاج البيئة: صورة، إعداد، قاعدة بيانات، شبكة، شهادة، ومراقبة. إذا احتاج المشروع خطوات يدوية غير موثقة، فلن تستطيع إصلاحه ليلًا.</p>
        <h3>Dockerfile</h3>
        <p>استخدم multi-stage: SDK للبناء، runtime للتشغيل. انشر <code>Release</code>، وثبّت الإصدار. شغّل كمستخدم غير root. لا تنسخ <code>appsettings.Development.json</code> أو الأسرار. استخدم <code>.dockerignore</code>. الصورة النهائية صغيرة وأقل سطح هجوم.</p>
        <h3>Compose</h3>
        <p>API + PostgreSQL + Redis + reverse proxy (Caddy/Nginx) + collector/seq اختياري. استخدم شبكة داخلية؛ لا تنشر قاعدة البيانات للخارج. صحّة الخدمات و<code>depends_on</code> مع healthcheck. الأسرار من env_file/خزنة، لا في YAML. البيانات في volume.</p>
        <h3>HTTPS</h3>
        <p>أنهِ TLS عند reverse proxy أو البوابة. Caddy يمكنه إدارة الشهادات محليًا/تلقائيًا. أعد توجيه HTTP إلى HTTPS. فعّل HSTS في الإنتاج. لا تضع شهادة خاصة في الصورة. اختبر من المتصفح لا من curl فقط.</p>
        <h3>Migrations</h3>
        <p>شغّل migration كخطوة/خدمة منفصلة قبل API أو ضمن نشر متوافق. لا تجعل كل replica تطبّقها. خذ نسخة احتياطية قبل التغييرات الخطيرة. اختبر من قاعدة فارغة ومن نسخة قديمة. لا تحذف أعمدة قبل توقف الإصدار القديم.</p>
        <h3>المراقبة والنسخ</h3>
        <p>health/readiness، logs JSON، metrics، traces. راقب الأخطاء وp95 وOutbox. Backup دوري مع اختبار restore؛ نسخة لم تُستعد ليست نسخة. حدد RPO/RTO. وثّق Runbook: أعراض، فحص، إجراء، rollback، جهة الاتصال.</p>
        <h3>التحقق النهائي</h3>
        <p>من clone نظيف: <code>docker compose up</code>، migrations، seed، ثم شراء. Smoke tests. اختبار تعطل DB/Redis. اختبار rollback. لا تعلن الجاهزية قبل ذلك. المشروع ليس Demo فقط؛ يجب أن يكون قابلًا للتشغيل والصيانة.</p>
      `,
      walkthrough: [
        {
          title: "Dockerfile multi-stage",
          code: `FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build\nWORKDIR /src\nCOPY . .\nRUN dotnet publish src/Souq.Api/Souq.Api.csproj \\\n    -c Release -o /app/publish\n\nFROM mcr.microsoft.com/dotnet/aspnet:10.0\nWORKDIR /app\nCOPY --from=build /app/publish .\nUSER $APP_UID\nEXPOSE 8080\nENTRYPOINT ["dotnet", "Souq.Api.dll"]`,
          lang: "dockerfile",
          body: `<p>مرحلة SDK للبناء فقط. <code>publish</code> ينتج ملفات التشغيل. الصورة النهائية لا تحتوي SDK. <code>USER $APP_UID</code> مستخدم غير root (متغير موجود في صورة .NET). استخدم <code>.dockerignore</code> لاستبعاد bin/obj/.git. ثبّت الإصدار بدل latest عند الإنتاج.</p>`
        },
        {
          title: "Compose للخدمات",
          code: `services:\n  api:\n    build: .\n    env_file: .env\n    depends_on:\n      db:\n        condition: service_healthy\n    ports: ["8080:8080"]\n\n  db:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_DB: souq\n      POSTGRES_USER: souq\n      POSTGRES_PASSWORD_FILE: /run/secrets/db_password\n    volumes: ["pgdata:/var/lib/postgresql/data"]\n    healthcheck:\n      test: ["CMD-SHELL", "pg_isready -U souq"]\n      interval: 5s\n\nvolumes:\n  pgdata:`,
          lang: "yaml",
          body: `<p>API يعتمد على DB بصحة، لا مجرد بدء الحاوية. <code>POSTGRES_PASSWORD_FILE</code> يقرأ سرًا من ملف. البيانات في volume. لا تنشر 5432 للخارج في الإنتاج. أضف Redis/proxy/collector عند الحاجة. الاستماع الافتراضي في .NET 8+ هو 8080 داخل الحاوية.</p>`
        },
        {
          title: "إعداد البيئة",
          code: `ASPNETCORE_ENVIRONMENT=Production\nConnectionStrings__Souq=Host=db;Database=souq;Username=souq\nJwt__Issuer=https://souq.example\nJwt__Audience=souq-api\nJwt__SigningKey_FILE=/run/secrets/jwt_key`,
          lang: "text",
          body: `<p>استخدم متغيرات بيئة بأسماء الإعداد الهرمية (<code>__</code>). لا تضع المفتاح في الملف. <code>_FILE</code> يقرأ من secret. أبقِ appsettings للإعدادات غير الحساسة. تحقق من الإعداد عند البدء (Options validation). لا تسجّل القيم.</p>`
        },
        {
          title: "خدمة migration",
          code: `migrate:\n  build: .\n  command: ["dotnet", "ef", "database", "update", "--no-build"]\n  env_file: .env\n  depends_on:\n    db:\n      condition: service_healthy\n  restart: "no"`,
          lang: "yaml",
          body: `<p>خدمة منفصلة تنتهي بعد التطبيق. لا تضع <code>database update</code> في كل API replica. <code>restart: "no"</code> يمنع حلقة إعادة. في الإنتاج قد تستخدم job/CI. اختبر migration على نسخة قديمة. خذ backup قبل التغيير.</p>`
        },
        {
          title: "Reverse proxy وHTTPS",
          code: `api.souq.example {\n    reverse_proxy api:8080\n    encode gzip\n}\n\n# Caddy يدير شهادة TLS تلقائيًا للنطاق الحقيقي.`,
          lang: "text",
          body: `<p>Caddy يوجّه النطاق إلى API. في الإنتاج استخدم شهادة صحيحة وDNS. أضف HSTS وحدود حجم الطلب. لا تعرض API مباشرة على الإنترنت إن كان proxy يغطي TLS. اختبر WebSocket/streaming إن كنت تستخدمه.</p>`
        },
        {
          title: "Health checks",
          code: `healthcheck:\n  test: ["CMD", "curl", "-f", "http://localhost:8080/health/ready"]\n  interval: 10s\n  timeout: 3s\n  retries: 5`,
          lang: "yaml",
          body: `<p>readiness يفحص DB/Outbox. liveness منفصل. لا تجعل interval قصيرًا جدًا. إذا فشل readiness، لا ترسل حركة. إذا فشل liveness، أعد التشغيل. اختبر الفحص عند إيقاف DB. لا تضع فحصًا بطيئًا يسبب تذبذبًا.</p>`
        },
        {
          title: "مراقبة وتجميع",
          code: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317\nSerilog__WriteTo__0__Name=Console`,
          lang: "text",
          body: `<p>أرسل traces/metrics إلى collector. اجمع logs في stdout (Docker يلتقطها) أو Seq. لا تعتمد على ملفات داخل الحاوية. أضف service/version resource. راقب p95 والأخطاء وOutbox lag. لا تجمع PII.</p>`
        },
        {
          title: "Backup وRestore",
          code: `pg_dump -h db -U souq -Fc souq > souq.dump\npg_restore -h db -U souq -d souq_restore souq.dump`,
          lang: "bash",
          body: `<p>اختبر restore على قاعدة منفصلة. خزّن النسخ خارج الخادم. حدد RPO/RTO. شفّر النسخ إن كانت تحتوي بيانات. لا تحفظ كلمة المرور في السكربت. جدولة النسخ لا تكفي؛ يجب اختبار الاستعادة.</p>`
        },
        {
          title: "Smoke Tests",
          code: `curl -f https://api.souq.example/health/ready\ncurl -f https://api.souq.example/api/v1/products\n# ثم سيناريو شراء آمن في staging`,
          lang: "bash",
          body: `<p>بعد <code>compose up</code> نفّذ smoke tests. تحقق من readiness والكتالوج وطلب تجريبي. لا تنشئ بيانات حقيقية. إذا فشل، افحص logs والحاويات. أضف السكربت إلى CI/CD.</p>`
        },
        {
          title: "Runbook",
          code: `1. تحقق من /health/ready وlogs.\n2. راجع DB/Redis/Outbox lag.\n3. إذا كان النشر سببًا: أوقف الترويج/ارجع.\n4. إذا كانت migration: تحقق من التوافق قبل rollback.\n5. وثّق الحادثة والسبب.`,
          lang: "text",
          body: `<p>Runbook قصير وقابل للتنفيذ. أضف أسماء الخدمات والأوامر. لا تكتب «افحص النظام». حدد من يتصل بمن. اختبره مع فريق. بعد كل حادثة، أضف تحسينًا. هذا ما يحول المشروع من Demo إلى نظام.</p>`
        }
      ],
      compare: {
        intro: `<p>التشغيل اليدوي يعمل على جهازك؛ Compose يعيده من الصفر.</p>`,
        before: {
          label: "تشغيل يدوي",
          lang: "bash",
          title: "قبل",
          code: `createdb souq\ndotnet run --project src/Souq.Api\n# إعدادات وبيانات في ذاكرة الشخص`,
          points: [
            "لا إعادة إنتاج.",
            "أسرار على الجهاز.",
            "لا health/backup.",
            "لا HTTPS."
          ]
        },
        after: {
          label: "Compose + Runbook",
          lang: "bash",
          title: "بعد",
          code: `docker compose up -d\ndocker compose run --rm migrate\ncurl -f https://api.souq.example/health/ready`,
          points: [
            "بيئة قابلة للتكرار.",
            "secrets وmigrations منفصلة.",
            "HTTPS وhealth.",
            "backup/rollback موثق."
          ]
        },
        verdict: `<p>الجاهزية للإنتاج تعني أن شخصًا آخر يستطيع تشغيل المشروع وإصلاحه دونك، لا أنك شغّلته مرة على جهازك.</p>`
      },
      internals: `
        <p>Docker يبني طبقات؛ ضع restore/publish في ترتيب يستفيد من cache. الصورة النهائية تحتوي runtime فقط. الحاوية ليست VM؛ لا تكتب بيانات دائمة داخلها. استخدم volumes للـDB. اضبط memory/CPU limits. راقب restart loops.</p>
        <p>Compose ينشئ شبكة افتراضية؛ الأسماء تحل كـDNS. <code>depends_on</code> مع healthcheck ينتظر الجاهزية. لا تعتمد على ترتيب بدء فقط. migrations يجب أن تنتهي قبل API. إذا كان النشر rolling، استخدم توافق expand/contract.</p>
        <h3>HTTPS</h3>
        <p>TLS عند proxy. HSTS يمنع downgrade. Forwarded headers مهمة لمعرفة scheme/IP خلف proxy. لا تثق برؤوس forwarded من عميل مباشر دون proxy موثوق. اختبر redirect.</p>
        <h3>Backup</h3>
        <p>RPO يحدد كم بيانات يمكن فقدها، RTO كم وقت للاستعادة. النسخ يجب أن تكون مشفرة وخارجية ومختبرة. لا تنسَ secrets/config. Runbook يحدد الإجراء. حادثة بلا restore مختبَر قد تنتهي بفقدان بيانات.</p>
      `,
      internalsTable: {
        head: ["العنصر", "الغرض", "تحذير"],
        rows: [
          ["Dockerfile", "صورة قابلة للتكرار", "لا أسرار/root"],
          ["Compose", "بيئة محلية/صغيرة", "ليس بديلًا عن orchestrator"],
          ["Migration job", "مخطط متوافق", "لا من كل replica"],
          ["Proxy", "TLS/HTTP", "Forwarded headers"],
          ["Health", "قرار الحركة", "لا DB في liveness"],
          ["Backup", "استعادة", "يجب اختبارها"]
        ]
      },
      tips: [
        {
          title: "شغّل من صورة نظيفة",
          body: "لا تعتمد على bin/obj أو قاعدة موجودة. clone + compose + migrations + seed + شراء."
        },
        {
          title: "الأسرار خارج الصورة",
          body: "env_file/file secrets/خزنة. لا تضعها في Dockerfile أو Git أو logs."
        },
        {
          title: "Migrations منفصلة",
          body: "job واحد، وليس كل replica. اختبر من نسخة قديمة، وخطط للتوافق."
        },
        {
          title: "Backup مختبَر",
          body: "نسخة لم تُستعد ليست نسخة. اختبر restore ووثّق RPO/RTO."
        }
      ],
      quiz: [
        {
          q: "لماذا multi-stage Dockerfile؟",
          options: [
            "لزيادة حجم الصورة.",
            "للبناء بـSDK وتشغيل runtime فقط، فتصغر الصورة وتقل المخاطر.",
            "لتشغيل كل شيء كroot.",
            "لإلغاء migrations."
          ],
          answer: 1,
          explain: "مرحلة البناء منفصلة عن runtime. الصورة النهائية لا تحتوي SDK."
        },
        {
          q: "أين تشغّل migrations؟",
          options: [
            "في كل replica عند البدء.",
            "في job/خدمة واحدة قبل النشر.",
            "من المتصفح.",
            "بعد حذف الجدول."
          ],
          answer: 1,
          explain: "job واحد يمنع التصادم. يجب أن يكون التغيير متوافقًا مع rolling."
        },
        {
          q: "ما الفرق بين liveness وreadiness في Compose؟",
          options: [
            "لا فرق.",
            "liveness يعيد التشغيل عند التعليق؛ readiness يقرر إرسال الحركة.",
            "readiness يفحص TLS فقط.",
            "liveness يخص قاعدة البيانات فقط."
          ],
          answer: 1,
          explain: "افصلهما. لا تضع فحص DB في liveness."
        }
      ],
      capstone: {
        title: "نشر Souq.NET",
        goal: "شغّل المشروع من Compose مع HTTPS وmigrations ومراقبة وbackup، واختبر الاستعادة.",
        tasks: [
          "اكتب Dockerfile multi-stage وشغّل الصورة كمستخدم غير root.",
          "أضف Compose لـAPI/PostgreSQL/Redis/proxy مع healthchecks.",
          "أضف خدمة migration منفصلة وبيانات seed.",
          "فعّل HTTPS وHSTS وOpenTelemetry/health checks.",
          "نفّذ backup وrestore على قاعدة منفصلة، واكتب Runbook."
        ],
        code: {
          lang: "yaml",
          title: "Compose",
          code: `services:\n  api:\n    build: .\n    env_file: .env\n    depends_on:\n      db:\n        condition: service_healthy\n  db:\n    image: postgres:16-alpine\n    volumes: ["pgdata:/var/lib/postgresql/data"]\nvolumes:\n  pgdata:`,
        },
      },
    },
    {
      id: "portfolio-interview",
      title: "Portfolio وInterview: اعرض ما بنيته",
      duration: 28,
      level: "متوسط",
      summary:
        "المشروع الجيد لا يتحدث عن نفسه. سنحوّله إلى README ومخطط وديمو وقصص مقابلة تُظهر قراراتك لا قائمة مكتباتك.",
      keywords: ["portfolio", "README", "architecture diagram", "STAR", "CV", "system design", "code review", "interview"],
      objectives: [
        "تكتب README يشرح المشروع وتشغيله وقراراته.",
        "ترسم مخططًا معماريًا مفهومًا.",
        "تحضّر ديمو قصيرًا ومسار شراء.",
        "تحوّل العمل إلى نقاط CV وSTAR.",
        "تجيب عن أسئلة Backend وSystem Design بثقة."
      ],
      concept: `
        <p>المقابل يريد معرفة كيف تفكر، لا أنك أكملت كورسًا. الـPortfolio هو دليل: مشكلة، قرارات، كود، اختبار، نشر، وما تعلمته. اجعل كل عنصر قابلًا للتحقق. لا تضع شعارات تقنيات بلا سياق.</p>
        <h3>README</h3>
        <p>ابدأ بجملة: ماذا يفعل المشروع ولمن؟ ثم صورة/وصف قصير، رابط ديمو إن وجد، خطوات تشغيل من نسخة نظيفة، المتطلبات، متغيرات البيئة، migrations، seed، واختبارات. أضف قسم قرارات: لماذا modular monolith؟ لماذا Outbox؟ لماذا PostgreSQL؟ واذكر tradeoffs. لا تضع أسرارًا أو بيانات حقيقية.</p>
        <h3>المخطط</h3>
        <p>مخطط C4 مبسط: العميل، API، modules، DB، broker/Outbox، observability. أظهر الحدود والتدفقات. لا ترسم كل class. اشرح لماذا هذه الحدود. المخطط الجيد يجيب عن سؤال «كيف يتدفق الطلب؟» في دقيقة.</p>
        <h3>الديمو</h3>
        <p>سيناريو 5–7 دقائق: تسجيل، تصفح، إضافة للسلة، طلب، دفع محاكى، عرض الحالة. أظهر Logs/Trace أو Outbox lag إن أمكن. لا تعرض تسجيل شاشة طويلًا. اختبر الديمو قبل المقابلة، وجهّز خطة بديلة (بيانات seed/فيديو).</p>
        <h3>CV وSTAR</h3>
        <p>نقطة قوية: «بنيت API بـ.NET وPostgreSQL، خفضت p95 من 280 إلى 140ms بإسقاط DTO وفهرس، وأضفت اختبارات تكامل وCI». هذا يذكر الأثر والأدلة. استخدم STAR: Situation، Task، Action، Result. لا تقل «استخدمت EF Core» فقط؛ قل ماذا حلّيت ولماذا اخترت الحل.</p>
        <h3>أسئلة المقابلة</h3>
        <p>راجع الأساسيات: DI lifetimes، async/await، HTTP، EF tracking/N+1، transactions/concurrency، auth، caching، testing. ثم System Design: متطلبات، تقديرات، API، بيانات، تدفق، اختناقات، tradeoffs. لا تحفظ إجابة؛ تدرّب على التفكير بصوت عالٍ.</p>
        <h3>النقد والتعلّم</h3>
        <p>اعرض نقطة ضعف حقيقية وما فعلته. لا تدّعِ أن كل شيء مثالي. Interviewer يقدر الوعي بالtradeoffs. بعد كل مقابلة، دوّن الأسئلة التي أخطأت فيها وارجع للمصدر. الـPortfolio عملية مستمرة، ليس صفحة ثابتة.</p>
      `,
      walkthrough: [
        {
          title: "README يشرح من أنت",
          code: `# Souq.NET\n\nArabic-first e-commerce API built with .NET, PostgreSQL, and EF Core.\n\n## Run\ncp .env.example .env\ndocker compose up -d\ndocker compose run --rm migrate\ndotnet test\n\n## Architecture\n![diagram](docs/architecture.png)\n\n## Decisions\n- Modular monolith: boundaries without network cost.\n- Outbox: no lost OrderPlaced events.\n- Testcontainers: integration tests on PostgreSQL.`,
          lang: "markdown",
          body: `<p>أول شاشة يجب أن تجيب: ماذا، لمن، وكيف أشغّله. لا تبدأ بقائمة 20 مكتبة. أضف قسم Decisions مع أسباب. اذكر ما لا يفعله المشروع (Scope) لتجنب توقعات خاطئة. لا تنسَ الترخيص إن كان عامًا.</p>`
        },
        {
          title: "مخطط معماري",
          code: `Client -> API (Catalog/Orders/Payments)\n              |        |\n           PostgreSQL  Outbox -> Broker\n              |\n         Observability (logs/metrics/traces)`,
          lang: "text",
          body: `<p>ابدأ بالتدفق. أظهر الحدود والاعتماديات. اشرح أن Outbox داخل نفس DB transaction، وأن الدفع خارجي. لا ترسم تفاصيل لا تستطيع الدفاع عنها. استخدم Mermaid أو صورة واضحة. تأكد أن المخطط يطابق الكود.</p>`
        },
        {
          title: "ديمو 5 دقائق",
          code: `1. Login\n2. Browse/search products\n3. Add to cart\n4. Place order (show idempotency)\n5. Simulate payment webhook\n6. Show order status + trace/log\n7. Show tests/CI briefly`,
          lang: "text",
          body: `<p>اختر مسارًا واحدًا وأتقنه. لا تتنقل بين 20 شاشة. أظهر قرارًا واحدًا مثيرًا (Outbox/معاملة/صلاحية). جهّز بيانات seed مسبقًا. إذا فشل الديمو، اشرح ما كان يجب أن يحدث ولا تعتذر كثيرًا. اختبر الإنترنت/المتصفح.</p>`
        },
        {
          title: "نقطة CV قوية",
          code: `Built Souq.NET, an Arabic-first e-commerce API (.NET, PostgreSQL, EF Core).\n- Added transactional Outbox + idempotent consumers; no lost OrderPlaced events.\n- Reduced p95 from 280ms to 140ms via DTO projection and composite index.\n- Added Testcontainers integration tests and GitHub Actions CI.`,
          lang: "text",
          body: `<p>كل نقطة: فعل + تقنية + أثر/دليل. الأرقام ليست وهمية؛ اذكر كيف قستها. لا تضع «مبتدئ/خبير» بلا دليل. اجعل المشروع قابلًا للفتح في 30 ثانية (README + ديمو).</p>`
        },
        {
          title: "قصة STAR",
          code: `S: checkout sometimes created duplicate orders on retry.\nT: make order creation safe under network retries.\nA: added Idempotency-Key + unique index + transactional outbox.\nR: duplicate orders dropped to 0 in load tests; retries return the original order.`,
          lang: "text",
          body: `<p>القصة يجب أن تكون حقيقية وقابلة للدفاع. اشرح البدائل التي رفضتها ولماذا. أظهر ما تعلمته. لا تجعل STAR سردًا طويلًا؛ 90 ثانية ثم أسئلة. حضّر قصتين: bug/incident، وقرار تصميم.</p>`
        },
        {
          title: "أسئلة Backend",
          code: `- Scoped vs Singleton؟\n- Why AsNoTracking?\n- How do you avoid N+1?\n- Optimistic vs pessimistic concurrency?\n- 401 vs 403?\n- How does Outbox work?\n- When would you split a microservice?`,
          lang: "text",
          body: `<p>اربط كل إجابة بمشروعك. لا ترد بتعريف فقط؛ أعطِ مثالًا وtradeoff. إذا لم تعرف، قل كيف تبحث/تتحقق. المقابل يقيّم التفكير أكثر من الحفظ. راجع أساسيات HTTP وEF وSQL قبل المقابلة.</p>`
        },
        {
          title: "System Design",
          code: `1. Clarify requirements + scale.\n2. Define API + data model.\n3. Draw flow and boundaries.\n4. Discuss consistency, failures, caching.\n5. Identify bottlenecks and tradeoffs.`,
          lang: "text",
          body: `<p>لا تبدأ بالرسم العشوائي. اسأل عن المستخدمين، القراءة/الكتابة، الاتساق، والميزانية. قدّم نسخة بسيطة أولًا ثم وسّع. اذكر failure modes. لا تقل «نستخدم Kafka» بلا سبب. قِس الافتراضات بصوت عالٍ.</p>`
        },
        {
          title: "GitHub نظيف",
          code: `README + LICENSE + .gitignore\ndocs/architecture.png\ndocker-compose.yml\n.env.example (no secrets)\n.github/workflows/ci.yml\ntests/`,
          lang: "text",
          body: `<p>لا ترفع bin/obj/.env. أضف وصفًا ومواضيع للمستودع. اجعل commit history مفهومًا. أضف Issues/roadmap إن أردت. لا تضع صورًا ضخمة. تأكد أن الروابط تعمل. الـPortfolio نفسه يجب أن يكون نظيفًا.</p>`
        },
        {
          title: "خطة التحضير",
          code: `أسبوع 1: أساسيات + مراجعة كود المشروع\nأسبوع 2: 20 سؤال Backend + إجابات مرتبطة بالمشروع\nأسبوع 3: 3 تمارين System Design + ديمو\nأسبوع 4: مقابلات تجريبية + تحسين CV/README`,
          lang: "text",
          body: `<p>تدرّب بصوت عالٍ، لا بالقراءة فقط. سجّل نفسك. اطلب من صديق/مرشد نقدًا. راجع الأسئلة التي أخطأت فيها. النوم والتحضير أفضل من حفظ إجابات. المقابلة مهارة تُمارس.</p>`
        }
      ],
      compare: {
        intro: `<p>وصف المشروع كقائمة تقنيات يضعك مع مئات المتقدمين. وصف القرارات والأثر يميزك.</p>`,
        before: {
          label: "CV ضعيف",
          lang: "text",
          title: "قبل",
          code: `E-commerce project using .NET, EF Core, SQL, Docker.\n- Used repository pattern.\n- Used JWT.`,
          points: [
            "لا مشكلة/أثر.",
            "لا أدلة أو أرقام.",
            "لا يوضح التفكير.",
            "يشبه كل CV آخر."
          ]
        },
        after: {
          label: "CV قوي",
          lang: "text",
          title: "بعد",
          code: `Built Souq.NET (.NET/PostgreSQL). Added transactional Outbox + idempotent consumers.\n- Reduced duplicate orders to 0 under retry tests.\n- Cut p95 280ms -> 140ms with projection + index.\n- CI: unit/integration tests + Testcontainers.`,
          points: [
            "مشكلة وحل.",
            "أثر قابل للقياس.",
            "تقنيات في سياق.",
            "قابل للتحقق في المستودع."
          ]
        },
        verdict: `<p>اجعل كل جملة قابلة للسؤال: «كيف قست؟»، «لماذا هذا الحل؟». إذا لم تستطع الدفاع، احذفها.</p>`
      },
      internals: `
        <p>المقابل يبحث عن إشارات: تفكير منهجي، تواصل، عمق تقني، ووعي بالtradeoffs. المشروع يعطي أدلة ملموسة. لا تحفظ إجابات؛ حضّر قصصًا وأرقامًا. اربط كل مفهوم بمثال من Souq.</p>
        <p>System Design ليس رسمًا كاملًا. ابدأ بالمتطلبات، قدّر الحمل، صمّم API/بيانات، ثم تدفق. اذكر consistency/caching/failure. إذا اقترحت microservice، اشرح التكلفة. إذا اقترحت cache، اشرح invalidation. interviewer يريد التفكير لا اسم تقنية.</p>
        <h3>التقييم</h3>
        <p>غالبًا: communication، problem solving، coding، depth، collaboration. الديمو والـREADME يغطيان communication. STAR يغطي collaboration. الأسئلة التقنية تغطي depth. تدرّب على كل بُعد.</p>
        <h3>بعد المقابلة</h3>
        <p>دوّن الملاحظات فورًا. أصلح فجوة معرفية واحدة. لا تلوم interviewer. كرر. الرفض معلومة، ليس حكمًا على قيمتك. استمر في بناء أدلة جديدة.</p>
      `,
      internalsTable: {
        head: ["العنصر", "ماذا يثبت", "خطأ شائع"],
        rows: [
          ["README", "تواصل/تشغيل", "قائمة تقنيات"],
          ["Diagram", "تفكير معماري", "تفاصيل بلا حدود"],
          ["Demo", "المنتج يعمل", "تنقل عشوائي"],
          ["CV", "أثر", "بدون أرقام"],
          ["STAR", "قرار/تعاون", "سرد طويل"],
          ["System Design", "تفكير", "تقنيات بلا سبب"]
        ]
      },
      tips: [
        {
          title: "اجعل التشغيل واضحًا",
          body: "README يشرح clone + compose + migrate + test. إذا احتاج خطوة غير موثقة، أصلحها."
        },
        {
          title: "اربط كل تقنية بقرار",
          body: "لماذا Outbox؟ لماذا PostgreSQL؟ لماذا modular monolith؟ اذكر البديل والتكلفة."
        },
        {
          title: "أرقام لها طريقة قياس",
          body: "p95، duplicate orders، test count. لا تخترع. اشرح كيف قست."
        },
        {
          title: "تدرّب بصوت عالٍ",
          body: "سجّل ديمو/إجابة. اطلب نقدًا. المقابلة مهارة تواصل، لا حفظ."
        }
      ],
      quiz: [
        {
          q: "ما أفضل بداية لـREADME؟",
          options: [
            "قائمة 30 مكتبة.",
            "جملة عن المشكلة/المستخدم ثم خطوات التشغيل.",
            "صورة شخصية.",
            "كود كامل."
          ],
          answer: 1,
          explain: "ابدأ بالقيمة والتشغيل. التفاصيل التقنية لاحقًا مع قرارات."
        },
        {
          q: "ما نقطة CV الأقوى؟",
          options: [
            "استخدمت EF Core.",
            "خفّضت p95 من 280 إلى 140ms بإسقاط DTO وفهرس.",
            "قرأت كتابًا.",
            "أعرف Docker."
          ],
          answer: 1,
          explain: "المشكلة + الإجراء + الأثر القابل للقياس يثبت القدرة."
        },
        {
          q: "كيف تبدأ System Design؟",
          options: [
            "ارسم Kafka فورًا.",
            "وضّح المتطلبات والحمل ثم API/بيانات/تدفق.",
            "اكتب كودًا كاملًا.",
            "اسأل عن الراتب."
          ],
          answer: 1,
          explain: "المتطلبات والافتراضات أولًا، ثم تصميم بسيط وتوسيع مبني على tradeoffs."
        }
      ],
      capstone: {
        title: "حزمة التقديم",
        goal: "جهّز README ومخططًا وديمو ونقاط CV وقصص STAR للمشروع.",
        tasks: [
          "اكتب README يشرح المشكلة والتشغيل والقرارات والاختبارات.",
          "أضف مخططًا معماريًا يطابق الكود.",
          "سجّل ديمو 5 دقائق لمسار الشراء مع Trace/Outbox.",
          "اكتب 3 نقاط CV فيها أثر قابل للقياس.",
          "حضّر قصتي STAR: حادثة تكرار طلب، وقرار معماري."
        ],
        code: {
          lang: "text",
          title: "هيكل README",
          code: `# Souq.NET\nWhat it does\nRun\nArchitecture\nDecisions\nTests\nTradeoffs`,
        },
      },
    },
    {
      id: "next-steps",
      title: "Next Steps: خريطة ما بعد الأكاديمية",
      duration: 24,
      level: "متوسط",
      summary:
        "لا تنتهي الخريطة هنا. سنختار ما تستثمر فيه بعد .NET Backend، ونبني خطة تعلم مستمرة بلا مطاردة كل تقنية.",
      keywords: ["gRPC", "GraphQL", "SignalR", "microservices", "saga", "cloud", "open source", "learning plan"],
      objectives: [
        "تختار بين العمق والاتساع حسب هدفك.",
        "تعرف متى تستخدم gRPC/GraphQL/SignalR.",
        "تفهم Saga ومتى تحتاج Microservices.",
        "تبني خطة 90 يومًا قابلة للقياس.",
        "تتجنب tutorial hell وتتعلم بالمشاريع."
      ],
      concept: `
        <p>بعد إتقان API وEF والأمان والاختبار والنشر، السؤال ليس «ما التقنية التالية؟» بل «أي مشكلة أريد حلها؟». كل تقنية تكلفة تعلم وتشغيل. اختر بناءً على هدف وظيفي/منتج، لا لأنها في الترند.</p>
        <h3>العمق أولًا</h3>
        <p>Backend قوي يعني فهم HTTP، SQL، التزامن، التوزيع، والأداء. إذا كانت الأساسيات هشة، إضافة Kubernetes/GraphQL لا تنقذ. تعمق في .NET وEF وPostgreSQL والاختبار. اقرأ كود مكتبات مفتوحة. حل مشاكل حقيقية.</p>
        <h3>gRPC</h3>
        <p>مناسب للاتصال الداخلي عالي الأداء، عقود صارمة، streaming، وبيئات متعددة اللغات. ليس أفضل من REST لواجهات عامة/متصفح. يحتاج protobuf وتوليد كود. استخدمه عندما تحتاج أداءً/عقدًا داخليًا، لا لمجرد «أسرع».</p>
        <h3>GraphQL</h3>
        <p>يفيد عندما يحتاج العملاء حقولًا مختلفة ويقلل over/under-fetching. يضيف تعقيد authorization وN+1 وcaching. ابدأ REST؛ انتقل إذا كانت احتياجات الواجهات متنوعة فعلًا. لا تستخدمه كبديل تلقائي.</p>
        <h3>SignalR وRealtime</h3>
        <p>لإشعارات الطلب/الدردشة/التحديثات الحية. يحتاج إدارة اتصالات، scale-out بـbackplane، وإعادة اتصال. لا تستخدمه لكل شيء. WebSocket ليس بديلًا عن API عادي.</p>
        <h3>Microservices وSaga</h3>
        <p>عندما تحتاج فرقًا مستقلة النشر/مقياسًا مختلفًا. تدفع ثمن الشبكة، المراقبة، والاتساق. Saga يدير معاملات موزعة عبر خطوات وتعويض. ابدأ modular monolith، وفكّك عند الحاجة. لا تبنِ distributed monolith.</p>
        <h3>السحابة وKubernetes</h3>
        <p>تعلّم أساسيات الحاويات، CI/CD، IAM، الشبكات، وقواعد البيانات المُدارة. Kubernetes أداة تشغيل؛ لا تبدأ به لمشروع صغير. افهم الفرق بين App Service/Container Apps وK8s. التكلفة والمراقبة جزء من التصميم.</p>
        <h3>خطة التعلم</h3>
        <p>اختر هدفًا واحدًا لمدة 90 يومًا. ابنِ ميزة صغيرة كل أسبوع. اقرأ مصدرًا واحدًا بعمق. اكتب ما تعلمته. راجع أسبوعيًا. تجنب جمع الدورات؛ التطبيق والملاحظات هما ما يثبت. علّم غيرك لتكشف الفجوات.</p>
      `,
      walkthrough: [
        {
          title: "اختر هدفًا",
          code: `90-day goal:\n- عمق: PostgreSQL + EF performance + testing\n- أو: Cloud deployment + observability\n- أو: Realtime + SignalR\nاختر واحدًا فقط.`,
          lang: "text",
          body: `<p>الهدف الواحد يمنع التشتت. اربطه بمشروع/وظيفة. اكتب معيار نجاح: «أنشر Souq على سحابة وأراقب p95» أو «أحسّن استعلامات 10x». لا تبدأ ثلاثة مسارات معًا.</p>`
        },
        {
          title: "gRPC: متى؟",
          code: `service Catalog {\n  rpc GetProduct(GetProductRequest) returns (ProductReply);\n  rpc WatchStock(WatchRequest) returns (stream StockUpdate);\n}`,
          lang: "protobuf",
          body: `<p>استخدم gRPC للاتصال الداخلي/streaming. عقود protobuf صارمة وتوليد كود. لا تعرضه للمتصفح مباشرة إلا عبر grpc-web/بوابة. أضف deadlines وretries. وثّق الإصدارات. لا تستخدمه لمجرد benchmark.</p>`
        },
        {
          title: "GraphQL: متى؟",
          code: `query {\n  product(id: "...") {\n    name\n    price\n    reviews(first: 5) { rating }\n  }\n}`,
          lang: "graphql",
          body: `<p>يفيد العملاء الذين يطلبون أشكالًا مختلفة. تحتاج authorization لكل حقل، dataloader لـN+1، وحدود عمق/تعقيد. caching أصعب. ابدأ REST إن كان لديك عميل واحد واحتياجات ثابتة.</p>`
        },
        {
          title: "SignalR",
          code: `builder.Services.AddSignalR();\napp.MapHub<OrderHub>("/hubs/orders");\n\nawait hub.Clients.User(userId)\n    .SendAsync("OrderPaid", orderId);`,
          lang: "csharp",
          body: `<p>لإشعار المستخدم بحالة الطلب. استخدم Groups/Users، وأعد الاتصال. للتوسع، backplane (Redis). لا ترسل بيانات حساسة بلا authorization. افصل الإشعار عن المعاملة الأساسية عبر Outbox/event.</p>`
        },
        {
          title: "Saga",
          code: `OrderPlaced -> ReserveStock -> Payment -> Confirm\n                      | fail -> ReleaseStock\n                      | fail -> CancelOrder`,
          lang: "text",
          body: `<p>Saga سلسلة خطوات محلية مع تعويض. لا معاملة موزعة. كل خطوة idempotent وقابلة لإعادة المحاولة. استخدم Outbox. صمّم حالات وtimeouts. راقب sagas العالقة. ابدأ بمعاملة واحدة إن أمكن.</p>`
        },
        {
          title: "Cloud basics",
          code: `- Container registry\n- Managed PostgreSQL\n- Secret store / OIDC\n- CI/CD\n- Logs/metrics/traces\n- Backup/RTO`,
          lang: "text",
          body: `<p>قبل Kubernetes، أتقن نشر حاوية + قاعدة مُدارة + أسرار + مراقبة. هذه 80% من الإنتاج. تعلّم IAM والشبكات والتكلفة. Kubernetes عند الحاجة orch/فرق. لا تبنِ cluster لمشروع شخصي بلا داعٍ.</p>`
        },
        {
          title: "Open source",
          code: `1. اقرأ CONTRIBUTING.\n2. ابدأ بـdocs/test صغير.\n3. افتح issue قبل تغيير كبير.\n4. أضف اختبارًا.\n5. راجع الكود بعمق.`,
          lang: "text",
          body: `<p>المساهمة تبني قراءة كود ومراجعة وتواصلًا. ابدأ بمشروع تستخدمه. لا تبدأ بإعادة كتابة. اتبع الأسلوب. الصبر جزء. سيرة GitHub النشطة إشارة، لكن الجودة أهم من العدد.</p>`
        },
        {
          title: "خطة 90 يومًا",
          code: `Week 1-2: أساس + قياس\nWeek 3-6: ميزة أسبوعية\nWeek 7-10: أداء/اختبار/نشر\nWeek 11-12: عرض/توثيق/مراجعة`,
          lang: "text",
          body: `<p>اجعلها واقعية. ساعة يوميًا أفضل من 8 ساعات مرة واحدة. اربط كل أسبوع بمخرج. راجع الجمعة: ما تعلمت، ما عرقل، ما التالي. لا تملأ الوقت بدورات. ابنِ.</p>`
        },
        {
          title: "علّم لتتعلم",
          code: `- اكتب ملاحظة تقنية.\n- اشرح قرارًا في README.\n- قدّم demo/internal talk.\n- أجب عن سؤال في مجتمع.`,
          lang: "text",
          body: `<p>الشرح يكشف الفجوات. اكتب بلغتك. لا تنشر أسرارًا. التعليم يثبت الفهم ويبني حضورًا. لا تحتج بأنك مبتدئ؛ اشرح ما تعرفه بدقة. الصحبة والمراجعة تسرّع التعلم.</p>`
        }
      ],
      compare: {
        intro: `<p>جمع الدورات يبدو تقدمًا؛ بناء ميزة يثبت التقدم.</p>`,
        before: {
          label: "Tutorial loop",
          lang: "text",
          title: "قبل",
          code: `دورة .NET\nدورة EF\nدورة Docker\nدورة Kubernetes\n... بلا مشروع مكتمل`,
          points: [
            "معرفة سطحية.",
            "لا أدلة/قرارات.",
            "تشتت ونسيان.",
            "خوف من المقابلة."
          ]
        },
        after: {
          label: "Project loop",
          lang: "text",
          title: "بعد",
          code: `ميزة صغيرة -> اختبار -> نشر -> قياس\n-> ملاحظة -> تحسين -> تكرار`,
          points: [
            "فهم عميق.",
            "أدلة في المستودع.",
            "قرارات وtradeoffs.",
            "ثقة مبنية على تجربة."
          ]
        },
        verdict: `<p>التعلم بالمشاريع + مراجعة موجهة أفضل من الاستهلاك. اختر هدفًا، ابنِ، قِس، ووثّق.</p>`
      },
      internals: `
        <p>التعلم الفعال يحتاج استرجاعًا نشطًا وتغذية راجعة. ابنِ، أخطئ، أصلح. الملاحظات والمراجعة تمنع إعادة نفس الخطأ. التباعد (spaced repetition) للأساسيات. لا تعتمد على إعادة القراءة.</p>
        <p>اختيار التقنية: ابدأ من المتطلبات والقيود. gRPC للعقود الداخلية/streaming، GraphQL لتنوع العملاء، SignalR للحيوية، microservices للاستقلال التشغيلي. كلها تضيف تعقيدًا. REST + monolith يغطي كثيرًا من الحالات.</p>
        <h3>المقابلات</h3>
        <p>العمق في الأساسيات + مشروع حقيقي أقوى من قائمة تقنيات. تدرّب على الشرح. اربط كل مفهوم بمثال. لا تخف من «لا أعرف»؛ اشرح كيف ستتعلم.</p>
        <h3>الاستمرارية</h3>
        <p>حدد وقتًا أسبوعيًا. تابع مصدرًا واحدًا. شارك. راجع. لا تقارن نفسك بالجميع. المسار طويل؛ الاستمرارية أهم من السرعة.</p>
      `,
      internalsTable: {
        head: ["التقنية", "متى", "التكلفة"],
        rows: [
          ["gRPC", "داخلي/streaming", "protobuf/أدوات"],
          ["GraphQL", "عملاء متنوعون", "auth/N+1/caching"],
          ["SignalR", "تحديثات حية", "اتصالات/backplane"],
          ["Saga", "معاملات موزعة", "تعويض/مراقبة"],
          ["K8s", "orch/فرق", "تعقيد تشغيلي"],
          ["Cloud", "نشر مُدار", "تكلفة/IAM"]
        ]
      },
      tips: [
        {
          title: "اختر هدفًا واحدًا",
          body: "90 يومًا لمسار واحد. اربطه بمخرج قابل للعرض. لا تجمع كل التقنيات."
        },
        {
          title: "ابنِ كل أسبوع",
          body: "ميزة صغيرة + اختبار + نشر. المشروع يثبت الفهم أكثر من الشهادة."
        },
        {
          title: "اقرأ مصدرًا واحدًا",
          body: "كود مكتبة/وثيقة رسمية بعمق. لا تتنقل بين 20 مقالًا."
        },
        {
          title: "علّم ووثّق",
          body: "اشرح ما تعلمته. الملاحظات والـdemo يكشفان الفجوات ويبنيان حضورًا."
        }
      ],
      quiz: [
        {
          q: "متى تختار gRPC؟",
          options: [
            "لكل API عام.",
            "للاتصال الداخلي/streaming بعقود صارمة.",
            "بدل قاعدة البيانات.",
            "لأنه أسهل من REST دائمًا."
          ],
          answer: 1,
          explain: "gRPC مناسب للداخل/الأداء/streaming. REST غالبًا أفضل للواجهات العامة."
        },
        {
          q: "ما تكلفة GraphQL؟",
          options: [
            "لا تكلفة.",
            "authorization لكل حقل، N+1، caching أعقد.",
            "يمنع TypeScript.",
            "لا يدعم الاستعلامات."
          ],
          answer: 1,
          explain: "GraphQL يضيف تعقيدًا في الأمان والأداء والتخزين المؤقت."
        },
        {
          q: "ما أفضل خطة تعلم؟",
          options: [
            "جمع الدورات فقط.",
            "هدف واحد + مشروع أسبوعي + قياس/توثيق.",
            "حفظ المصطلحات.",
            "تعلم كل تقنية في وقت واحد."
          ],
          answer: 1,
          explain: "التطبيق والمراجعة والتوثيق يثبتون الفهم. التشتت يقلل العمق."
        }
      ],
      capstone: {
        title: "خطة الـ90 يومًا",
        goal: "اختر مسارًا واحدًا بعد الأكاديمية وابنِ خطة قابلة للقياس.",
        tasks: [
          "اختر هدفًا واحدًا (PostgreSQL/Cloud/Realtime) واكتب معيار نجاح.",
          "حدد ميزة صغيرة لكل أسبوع لمدة 12 أسبوعًا.",
          "اختر مصدرًا رسميًا واحدًا ووثيقة/كتابًا واحدًا.",
          "أضف قياسًا (p95/اختبار/مستخدم) لكل مرحلة.",
          "اكتب ملاحظة تقنية أو قدّم ديمو داخلي عمّا بنيته."
        ],
        code: {
          lang: "text",
          title: "قالب الخطة",
          code: `Goal:\nSuccess metric:\nWeekly deliverable:\nSource of truth:\nReview day:`,
        },
      },
    },
  ],
});
