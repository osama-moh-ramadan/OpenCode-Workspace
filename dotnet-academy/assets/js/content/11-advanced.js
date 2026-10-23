/* الوحدة 11 — مواضيع متقدمة: gRPC/SignalR وGraphQL. */
Academy.addModule({
  id: "advanced",
  title: "مواضيع متقدمة",
  tagline: "أدوات إضافية لا تبدأ بها، لكن تعرف متى تحتاجها وكيف تستخدمها دون أن تدفع ثمنها بلا داعٍ.",
  icon: "◆",
  color: "#38bdf8",
  lessons: [
    {
      id: "grpc-signalr",
      title: "gRPC وSignalR: عقود سريعة وتحديثات حية",
      duration: 30,
      level: "متقدم",
      summary:
        "gRPC للاتصال الداخلي الصارم، وSignalR للدفع اللحظي للعميل. سنفهم كليهما ومتى يكون REST أبسط وأفضل.",
      keywords: ["gRPC", "protobuf", "HTTP/2", "streaming", "SignalR", "WebSocket", "backplane", "deadline"],
      objectives: [
        "تعرف متى تختار gRPC بدل REST.",
        "تعريف service ورسائل protobuf.",
        "تضبط deadlines وأخطاء gRPC.",
        "تبني Hub وتدفع إشعارًا لمستخدم.",
        "تخطط لإعادة الاتصال والتوسع."
      ],
      concept: `
        <p><strong>gRPC</strong> إطار RPC يعتمد HTTP/2 وprotobuf. يعطيك عقودًا صارمة، توليد كود، streaming، وأداءً جيدًا للاتصال الداخلي. ليس بديلًا تلقائيًا عن REST للواجهات العامة؛ المتصفح يحتاج grpc-web/بوابة، والعقد الثنائي أصعب في التصحيح اليدوي.</p>
        <h3>Protobuf</h3>
        <p>تعرّف الرسائل والحقول بأرقام. الأرقام هي العقد، لا الأسماء. لا تغيّر رقم حقل موجود؛ أضف رقمًا جديدًا واترك القديم. استخدم <code>optional</code>/حقول جديدة للتوافق. لا تحذف رقمًا وتعيد استخدامه. احتفظ بملفات proto في مستودع مشترك وولّد الكود في CI.</p>
        <h3>Streaming وDeadlines</h3>
        <p>gRPC يدعم unary، server streaming، client streaming، وbidirectional. استخدم streaming للبيانات المتدفقة، لا لكل شيء. اضبط deadline لكل استدعاء؛ بدونها قد ينتظر الخادم/العميل بلا نهاية. مرّر cancellation. أخطاء gRPC لها status codes مثل <code>NotFound</code> و<code>InvalidArgument</code> و<code>Unavailable</code>، لا تعيد HTTP 500 فقط.</p>
        <h3>SignalR</h3>
        <p><strong>SignalR</strong> يبني اتصالًا مستمرًا بين الخادم والعميل (WebSocket مع fallback) ويدير الاتصال وإعادة الاتصال. مناسب لإشعارات الطلب، الدردشة، والتحديثات الحية. ليس بديلًا عن API عادي؛ استخدمه للدفع من الخادم، وREST/gRPC للأوامر والاستعلامات.</p>
        <h3>Groups وUsers</h3>
        <p>يمكنك الإرسال لكل العملاء، لمجموعة، أو لمستخدم محدد. اربط الاتصال بهوية موثقة. لا تثق بـ<code>userId</code> قادم من العميل. أرسل بيانات أقل ما يمكن. لا ترسل أسرارًا أو تفاصيل طلب لا يملكه المستخدم. اختبر أن مستخدمًا لا يتلقى إشعار غيره.</p>
        <h3>التوسع</h3>
        <p>مع عدة replicas، تحتاج backplane (Redis) أو Azure SignalR Service حتى تصل الرسائل لكل النسخ. WebSocket اتصال طويل؛ خطط لإعادة الاتصال وdraining عند النشر. راقب عدد الاتصالات. لا تضع منطقًا حرجًا في حدث الاتصال فقط؛ افصل الحالة عن الاتصال.</p>
        <h3>الاختيار</h3>
        <p>REST للواجهات العامة والبسيطة. gRPC للداخل/الأداء/streaming. SignalR للدفع الحي. لا تستخدم الثلاثة في مشروع صغير بلا سبب. كل تقنية تضيف تشغيلًا واختبارًا ومراقبة.</p>
      `,
      walkthrough: [
        {
          title: "عرّف عقد protobuf",
          code: `syntax = "proto3";\noption csharp_namespace = "Souq.Contracts";\n\nservice Catalog {\n  rpc GetProduct(GetProductRequest) returns (ProductReply);\n  rpc WatchStock(WatchRequest) returns (stream StockUpdate);\n}\n\nmessage GetProductRequest { string id = 1; }\nmessage ProductReply { string id = 1; string name = 2; double price = 3; }\nmessage WatchRequest { string product_id = 1; }\nmessage StockUpdate { int32 stock = 1; }`,
          lang: "protobuf",
          body: `<p>الأرقام <code>1,2,3</code> هي عقد wire. لا تغيّرها. <code>stream</code> يجعل الرد متعددًا. استخدم أسماء واضحة. لا تضع <code>decimal</code> مباشرة في proto؛ استخدم string أو int64 بوحدات صغيرة لتجنب فقدان الدقة. أضف حقولًا جديدة بأرقام جديدة.</p>`
        },
        {
          title: "نفّذ الخدمة",
          code: `public sealed class CatalogService(CatalogDbContext db)\n    : Catalog.CatalogBase\n{\n    public override async Task<ProductReply> GetProduct(\n        GetProductRequest request, ServerCallContext context)\n    {\n        var id = Guid.Parse(request.Id);\n        var product = await db.Products.AsNoTracking()\n            .SingleOrDefaultAsync(p => p.Id == id, context.CancellationToken)\n            ?? throw new RpcException(new Status(\n                StatusCode.NotFound, "Product not found"));\n\n        return new ProductReply\n        {\n            Id = product.Id.ToString(),\n            Name = product.Name,\n            Price = (double)product.Price.Amount\n        };\n    }\n}`,
          lang: "csharp",
          body: `<p>الكلاس المولّد <code>CatalogBase</code>. استخدم <code>context.CancellationToken</code>. ارمِ <code>RpcException</code> بحالة مناسبة بدل exception عام. لا ترجع كيان EF. لاحظ تحويل decimal إلى double هنا للتوضيح فقط؛ في المال استخدم string/int64 لتجنب الدقة.</p>`
        },
        {
          title: "سجّل gRPC",
          code: `builder.Services.AddGrpc(options =>\n{\n    options.MaxReceiveMessageSize = 4 * 1024 * 1024;\n    options.EnableDetailedErrors = builder.Environment.IsDevelopment();\n});\n\napp.MapGrpcService<CatalogService>();`,
          lang: "csharp",
          body: `<p><code>AddGrpc</code> يسجّل الخدمات. حدد حجم الرسالة. لا تفعّل <code>EnableDetailedErrors</code> في الإنتاج؛ قد يكشف تفاصيل. gRPC يحتاج HTTP/2؛ تأكد من proxy/TLS. للمتصفح استخدم grpc-web. أضف health checks.</p>`
        },
        {
          title: "عميل مع deadline",
          code: `using var channel = GrpcChannel.ForAddress("https://catalog.internal");\nvar client = new Catalog.CatalogClient(channel);\n\nvar reply = await client.GetProductAsync(\n    new GetProductRequest { Id = id.ToString() },\n    deadline: DateTime.UtcNow.AddSeconds(2));`,
          lang: "csharp",
          body: `<p>deadline يمنع الانتظار الأبدي. استخدم <code>GrpcChannel</code> وأعد استخدامه؛ لا تنشئ قناة لكل طلب. أضف retry للـ<code>Unavailable</code> فقط، مع idempotency. سجّل latency. لا تضع عنوانًا داخليًا في الكود؛ استخدم إعدادات.</p>`
        },
        {
          title: "أخطاء gRPC",
          code: `throw new RpcException(new Status(\n    StatusCode.InvalidArgument, "Quantity must be positive"));`,
          lang: "csharp",
          body: `<p>استخدم الحالات القياسية: InvalidArgument، NotFound، AlreadyExists، FailedPrecondition، Unavailable. لا تحوّل كل خطأ إلى Unknown. أضف تفاصيل آمنة فقط. العميل يجب أن يتعامل مع الحالة. راقب معدل الأخطاء حسب الحالة.</p>`
        },
        {
          title: "Hub للإشعارات",
          code: `public sealed class OrderHub : Hub\n{\n    public override async Task OnConnectedAsync()\n    {\n        var userId = Context.UserIdentifier\n            ?? throw new HubException("Unauthenticated");\n        await Groups.AddToGroupAsync(Context.ConnectionId, $"user:{userId}");\n        await base.OnConnectedAsync();\n    }\n}`,
          lang: "csharp",
          body: `<p><code>UserIdentifier</code> يأتي من المصادقة. لا تقبل userId من رسالة العميل. أضف الاتصال لمجموعة المستخدم. لا تضع منطق أعمال ثقيلًا في OnConnected. اختبر أن المستخدم غير المصادق يُرفض. استخدم <code>[Authorize]</code> على Hub.</p>`
        },
        {
          title: "اربط Hub",
          code: `builder.Services.AddSignalR();\napp.MapHub<OrderHub>("/hubs/orders").RequireAuthorization();`,
          lang: "csharp",
          body: `<p><code>RequireAuthorization</code> يمنع الاتصال المجهول. CORS يجب أن يسمح بالأصل والcredentials إذا لزم. للمتصفح، استخدم عميل SignalR. لا تعرض Hub على مسار يتعارض مع API. أضف health/مراقبة للاتصالات.</p>`
        },
        {
          title: "أرسل لمستخدم",
          code: `await hub.Clients.User(userId.ToString())\n    .SendAsync("OrderPaid", new { orderId, status = "Paid" });`,
          lang: "csharp",
          body: `<p><code>Clients.User</code> يستخدم معرف المستخدم الموثّق. لا ترسل لكل العملاء. أرسل الحد الأدنى من البيانات. افصل الإشعار عن المعاملة: استخدم Outbox/event ثم Hub. إذا فشل الإرسال، لا تفشل عملية الدفع. سجّل الفشل وأعد المحاولة/اتركه للحدث.</p>`
        },
        {
          title: "توسّع وأعد الاتصال",
          code: `builder.Services.AddSignalR()\n    .AddStackExchangeRedis("redis:6379");\n\n// العميل: withAutomaticReconnect()`,
          lang: "csharp",
          body: `<p>Redis backplane يوزّع الرسائل بين النسخ. بدونه، المستخدم المتصل بنسخة أخرى لا يستلم. العميل يعيد الاتصال تلقائيًا، لكنه قد يفقد أحداثًا أثناء الانقطاع؛ استخدم API/حالة عند العودة. راقب الاتصالات والذاكرة. اختبر النشر أثناء اتصال.</p>`
        }
      ],
      compare: {
        intro: `<p>REST وgRPC وSignalR تحل مشاكل مختلفة. اختيار خاطئ يضيف تعقيدًا بلا فائدة.</p>`,
        before: {
          label: "Polling لكل شيء",
          lang: "csharp",
          title: "قبل",
          code: `while (true)\n{\n    var status = await http.GetFromJsonAsync($"/orders/{id}");\n    if (status == "Paid") break;\n    await Task.Delay(2000);\n}`,
          points: [
            "حمل زائد واستهلاك بطارية.",
            "تأخير في الإشعار.",
            "لا يستفيد من اتصال حي.",
            "قد يخفي فشل الشبكة."
          ]
        },
        after: {
          label: "SignalR + REST",
          lang: "csharp",
          title: "بعد",
          code: `await hub.Clients.User(userId)\n    .SendAsync("OrderPaid", new { orderId });\n\n// REST للاستعلام الأولي/الاحتياطي\nGET /api/v1/orders/{id}`,
          points: [
            "دفع فوري عند الحدث.",
            "REST يبقى مصدر الحقيقة.",
            "إعادة اتصال/حالة عند العودة.",
            "حمل أقل."
          ]
        },
        verdict: `<p>استخدم gRPC للداخل الصارم، SignalR للحيوية، REST للعقد العام. لا تستبدل الكل بتقنية واحدة.</p>`
      },
      internals: `
        <p>gRPC فوق HTTP/2، وprotobuf أصغر/أسرع من JSON غالبًا. لكن التصحيح اليدوي أصعب، والمتصفح يحتاج grpc-web. deadlines وcancellation أساسيان. الأخطاء جزء من العقد، وليست استثناءً عامًا.</p>
        <p>SignalR يبدأ بـWebSocket وقد يستخدم SSE/long polling. الاتصال مرتبط بـConnectionId، والهوية من المصادقة. Groups تُدار في الذاكرة/backplane. عند التوسع، كل نسخة تعرف مجموعاتها فقط؛ backplane يمرر الرسائل. اختبر انقطاع الاتصال وإعادة الاتصال.</p>
        <h3>الأمان</h3>
        <p>gRPC يحتاج TLS/mTLS داخليًا حسب التهديد. SignalR يحتاج auth وCORS. لا ترسل بيانات مستخدم آخر. تحقق من الملكية عند كل حدث. لا تعتمد على إخفاء أسماء الأحداث.</p>
        <h3>المراقبة</h3>
        <p>راقب gRPC latency/status codes، وعدد اتصالات SignalR، وإعادة الاتصال، وفشل الإرسال. اربط بالـtrace. لا تسجّل الرسائل الحساسة.</p>
      `,
      internalsTable: {
        head: ["التقنية", "الاستخدام", "التكلفة"],
        rows: [
          ["gRPC", "داخلي/streaming", "protobuf/HTTP2"],
          ["SignalR", "دفع حي", "اتصالات/backplane"],
          ["REST", "عقد عام", "حمل polling إن استخدم"],
          ["grpc-web", "متصفح", "بوابة/قيود"],
          ["Redis backplane", "توسع SignalR", "بنية إضافية"],
          ["deadline", "منع انتظار", "يجب اختياره بعناية"]
        ]
      },
      tips: [
        {
          title: "لا تستخدم gRPC للواجهة العامة",
          body: "REST/JSON أبسط للمتصفح والعملاء. gRPC للداخل والعقود الصارمة."
        },
        {
          title: "اضبط deadline دائمًا",
          body: "كل استدعاء gRPC يحتاج مهلة وإلغاء. لا تنتظر للأبد."
        },
        {
          title: "الإشعار ليس مصدر الحقيقة",
          body: "SignalR يدفع تحديثًا، لكن الحالة تُقرأ من API. تعامل مع إعادة الاتصال."
        },
        {
          title: "خطط للتوسع",
          body: "backplane ضروري مع عدة replicas. اختبر النشر أثناء الاتصالات."
        }
      ],
      quiz: [
        {
          q: "متى يكون gRPC مناسبًا؟",
          options: [
            "لواجهة عامة في المتصفح فقط.",
            "للاتصال الداخلي/streaming بعقود صارمة.",
            "بدل قاعدة البيانات.",
            "لكل endpoint."
          ],
          answer: 1,
          explain: "gRPC ممتاز للداخل/الأداء/streaming. REST غالبًا أفضل للعام."
        },
        {
          q: "لماذا deadline؟",
          options: [
            "لزيادة الحمل.",
            "لمنع انتظار غير محدود وتحرير الموارد.",
            "لتشفير الرسائل.",
            "لتغيير proto."
          ],
          answer: 1,
          explain: "deadline يحدد مهلة الاستدعاء ويمنع التعليق."
        },
        {
          q: "كيف ترسل إشعارًا لمستخدم واحد؟",
          options: [
            "Clients.All",
            "Clients.User(userId)",
            "Groups.AddToGroupAsync لكل الناس",
            "HTTP polling"
          ],
          answer: 1,
          explain: "Clients.User يرسل للمستخدم الموثّق المحدد."
        }
      ],
      capstone: {
        title: "gRPC وSignalR في Souq",
        goal: "أضف عقد Catalog داخليًا وإشعار OrderPaid حيًا، مع أمان وإعادة اتصال.",
        tasks: [
          "عرّف <code>Catalog.proto</code> مع GetProduct وWatchStock.",
          "نفّذ الخدمة وأضف deadline/أخطاء gRPC.",
          "أضف Hub مع <code>[Authorize]</code> ومجموعة لكل مستخدم.",
          "أرسل <code>OrderPaid</code> بعد حدث الطلب دون إفشال الدفع.",
          "فعّل Redis backplane واختبر إعادة الاتصال والنشر."
        ],
        code: {
          lang: "csharp",
          title: "إرسال",
          code: `await hub.Clients.User(userId.ToString())\n    .SendAsync("OrderPaid", new { orderId, status = "Paid" });`,
        },
      },
    },
    {
      id: "graphql",
      title: "GraphQL: مرونة للعميل وتكلفة للخادم",
      duration: 30,
      level: "متقدم",
      summary:
        "GraphQL يسمح للعميل بطلب ما يحتاجه فقط، لكنه يضيف تعقيد authorization وN+1 وcaching. سنستخدمه بوعي.",
      keywords: ["GraphQL", "HotChocolate", "resolver", "DataLoader", "N+1", "depth limit", "persisted query", "authorization"],
      objectives: [
        "تعرّف متى يفيد GraphQL فعليًا.",
        "تبني schema وquery/mutation.",
        "تحل N+1 بـDataLoader.",
        "تضبط authorization وحدود التعقيد.",
        "تفهم تكلفة caching والأخطاء."
      ],
      concept: `
        <p><strong>GraphQL</strong> لغة استعلام بعقد schema. العميل يحدد الحقول التي يريدها، فيقل over-fetching/under-fetching. مناسب عندما تختلف احتياجات العملاء كثيرًا. ليس أسرع تلقائيًا؛ قد يجلب الخادم أكثر مما تتوقع إذا لم تصمم resolvers بعناية.</p>
        <h3>Schema وResolvers</h3>
        <p>Schema يحدد الأنواع والحقول. Resolver ينفّذ كل حقل. query للقراءة، mutation للتغيير، subscription للحيوية. اجعل schema عقدًا عامًا مستقرًا. لا تكشف كيان EF. استخدم DTOs/أنواع GraphQL. وثّق الحقول وحدودها.</p>
        <h3>N+1</h3>
        <p>إذا طلب العميل 20 منتجًا مع تصنيف كل واحد، قد ينفّذ resolver استعلامًا لكل تصنيف. <strong>DataLoader</strong> يجمع الطلبات في دفعة واحدة. هذا أهم تحسين. استخدمه للعلاقات. لا تفترض أن GraphQL نفسه يحل N+1.</p>
        <h3>Authorization</h3>
        <p>كل حقل قد يحتاج صلاحية. لا تتحقق فقط عند root query. استخدم سياسات/مصادر بيانات. لا تعِد كائنًا كاملًا ثم تعتمد على العميل. افحص الملكية. اختبر أن مستخدمًا لا يقرأ حقلًا/موردًا ليس له.</p>
        <h3>التعقيد والحدود</h3>
        <p>استعلام واحد قد يطلب شجرة ضخمة. اضبط max depth، max complexity، وtimeout. حدد حجم الصفحات. ارفض introspection في الإنتاج إن أردت. استخدم persisted queries لتقليل الحمولة ومنع الاستعلامات العشوائية.</p>
        <h3>Caching</h3>
        <p>HTTP caching أصعب لأن الاستعلام POST. استخدم persisted queries + CDN/GET، أو caching على مستوى resolver. الإبطال معقد. لا تضع cache لمستخدم دون مفتاح صحيح. راقب hit rate. REST قد يكون أبسط إذا كانت الاحتياجات ثابتة.</p>
        <h3>الأخطاء</h3>
        <p>GraphQL قد يرجع 200 مع أخطاء في <code>errors</code>. يجب أن يعرف العميل كيف يتعامل. لا تسرّب stack traces. استخدم error codes/extensions آمنة. اربط partial success. راقب الأخطاء حسب الحقل.</p>
      `,
      walkthrough: [
        {
          title: "عرّف schema",
          code: `type Product {\n  id: ID!\n  name: String!\n  price: Decimal!\n  inStock: Boolean!\n  category: Category\n}\n\ntype Query {\n  products(search: String, first: Int = 20): [Product!]!\n  product(id: ID!): Product\n}`,
          lang: "graphql",
          body: `<p>ابدأ بالأنواع التي يحتاجها العميل. <code>!</code> يعني non-null. <code>first</code> يحدد حجم الصفحة. لا تضع كل الحقول الداخلية. استخدم <code>Decimal</code> scalar مخصصًا للمال. وثّق الحد الأقصى لـ<code>first</code>.</p>`
        },
        {
          title: "Resolver للاستعلام",
          code: `[UseProjection]\npublic IQueryable<Product> GetProducts(\n    string? search, CatalogDbContext db)\n{\n    var query = db.Products.AsNoTracking();\n    if (!string.IsNullOrWhiteSpace(search))\n        query = query.Where(p => p.Name.Contains(search));\n    return query;\n}`,
          lang: "csharp",
          body: `<p>HotChocolate يمكنه ترجمة الاستعلام إلى IQueryable. <code>UseProjection</code> يقرأ الحقول المطلوبة. لا تستدع <code>ToList</code> داخل resolver إن كان projection ممكنًا. أضف حدودًا/ترتيبًا. اختبر SQL. لا تعِد الكيان إذا كان schema منفصلًا.</p>`
        },
        {
          title: "Resolver لعلاقة",
          code: `[DataLoader]\npublic Task<Category?> GetCategoryAsync(\n    [Parent] Product product,\n    CategoryBatchLoader loader,\n    CancellationToken ct)\n    => loader.LoadAsync(product.CategoryId, ct);`,
          lang: "csharp",
          body: `<p><code>DataLoader</code> يجمع معرفات التصنيفات في دفعة واحدة. بدونه قد يحدث N+1. أضف cancellation. استخدم batch loader لكل طلب/scope. اختبر عدد الاستعلامات. هذا أهم من تحسين serializer.</p>`
        },
        {
          title: "Mutation",
          code: `type Mutation {\n  createProduct(input: CreateProductInput!): CreateProductPayload!\n}`,
          lang: "graphql",
          body: `<p>استخدم input/payload واضحين. لا ترجع الكيان كاملًا إن لم يحتج. أضف أخطاء حقول. mutation يجب أن تمر عبر نفس قواعد المجال. لا تجعل GraphQL طبقة منطق منفصلة. استخدم idempotency للطلبات الحساسة.</p>`
        },
        {
          title: "Authorization لكل حقل",
          code: `[Authorize(Policy = "CanManageCatalog")]\npublic Task<Product> CreateProduct(...)\n\n// وفي resolver الحقل الحساس:\nif (product.UserId != userId) throw new GraphQLException("Forbidden");`,
          lang: "csharp",
          body: `<p>لا تعتمد على autorization عند root فقط. الحقول/العلاقات قد تكشف بيانات. استخدم سياسات وملكية. أعد خطأ آمنًا. اختبر مستخدمًا بلا صلاحية. GraphQL لا يغني عن التفويض؛ يزيد سطحه.</p>`
        },
        {
          title: "حدود التعقيد",
          code: `builder.Services\n    .AddGraphQLServer()\n    .AddQueryType<Query>()\n    .AddMaxExecutionDepth(10)\n    .AddMaxExecutionComplexity(1000);`,
          lang: "csharp",
          body: `<p>الحدود تمنع استعلامات مدمرة. اختر قيمًا بناءً على schema. أضف timeout. اختبر استعلامًا عميقًا. لا تسمح بحجم صفحات ضخم. راقب الحقول الأكثر تكلفة. الحدود ليست بديلًا عن indexes.</p>`
        },
        {
          title: "Persisted Queries",
          code: `query ProductPage($id: ID!) {\n  product(id: $id) { id name price }\n}`,
          lang: "graphql",
          body: `<p>خزّن الاستعلامات المعتمدة ومرّر hash. يقلل الحمولة ويمنع استعلامات عشوائية. يسهّل CDN/caching. أضف إصدارات. لا تسمح بـarbitrary queries في production إن كان النموذج يسمح.</p>`
        },
        {
          title: "أخطاء آمنة",
          code: `throw new GraphQLException(\n    ErrorBuilder.New()\n        .SetMessage("Product not found")\n        .SetCode("PRODUCT_NOT_FOUND")\n        .Build());`,
          lang: "csharp",
          body: `<p>استخدم code ثابتًا ورسالة آمنة. لا تضع stack/SQL. وثّق الأخطاء. اختبر partial errors. سجّل traceId. العميل يحتاج التمييز بين not found/validation/forbidden.</p>`
        },
        {
          title: "هل تحتاجه فعلًا؟",
          code: `استخدم REST إذا:\n- عميل واحد واحتياجات ثابتة\n- caching HTTP مهم\n- فريق صغير\n\nاستخدم GraphQL إذا:\n- عملاء متنوعون\n- schema غنية\n- تقليل round trips مهم`,
          lang: "text",
          body: `<p>لا تنتقل إلى GraphQL لأنها مشهورة. REST + DTOs يغطي معظم الحالات. GraphQL يضيف تعقيدًا أمنيًا/أدائيًا. ابدأ بسيطًا، وانتقل عند ألم حقيقي.</p>`
        }
      ],
      compare: {
        intro: `<p>REST يحدد الاستجابة؛ GraphQL يتركها للعميل. الحرية تكلفة.</p>`,
        before: {
          label: "REST ثابت",
          lang: "text",
          title: "قبل",
          code: `GET /products -> كل الحقول\nGET /products/1 -> كل الحقول\n// عميل يحتاج الاسم فقط`,
          points: [
            "Over-fetching.",
            "Round trips متعددة.",
            "بسيط/caching سهل.",
            "عقد واضح."
          ]
        },
        after: {
          label: "GraphQL",
          lang: "graphql",
          title: "بعد",
          code: `query {\n  products(first: 20) {\n    name\n    category { name }\n  }\n}`,
          points: [
            "العميل يطلب ما يحتاجه.",
            "استعلام واحد للعلاقات.",
            "يحتاج DataLoader/حدود.",
            "authorization لكل حقل."
          ]
        },
        verdict: `<p>GraphQL ليس ترقية تلقائية. استخدمه عندما تكون مرونة العميل تستحق تعقيد الخادم.</p>`
      },
      internals: `
        <p>GraphQL parser يتحقق من schema ثم ينفّذ resolvers. قد ينفّذ حقولًا بالتوازي. N+1 شائع في العلاقات. DataLoader يجمع الطلبات في نافذة قصيرة. راقب عدد الاستعلامات لكل طلب.</p>
        <p>HTTP غالبًا POST، لذا caching التقليدي صعب. persisted queries + GET/CDN يساعد. لا تخلط caching مستخدم بمستخدم. استخدم cache keys صحيحة.</p>
        <h3>الأمان</h3>
        <p>introspection قد تكشف schema. عطّله في الإنتاج إن لم تحتجه. حدد depth/complexity. تحقق من المدخلات. لا تثق بالعميل. افحص الملكية. استخدم rate limiting. GraphQL ليس بابًا خلفيًا آمنًا.</p>
        <h3>الأداء</h3>
        <p>projection إلى SQL، DataLoader، indexes، وحدود صفحات. لا تجلب كيانًا كاملًا لكل حقل. اختبر بـSQL logging. قد يكون REST أبسط وأسرع لحالة واحدة.</p>
      `,
      internalsTable: {
        head: ["المشكلة", "الحل", "تحذير"],
        rows: [
          ["N+1", "DataLoader", "per-request scope"],
          ["استعلام ضخم", "depth/complexity", "قيم واقعية"],
          ["Caching", "persisted queries/CDN", "مفاتيح صحيحة"],
          ["Authorization", "سياسات/ملكية", "كل حقل"],
          ["Over-fetching", "projection", "اختبر SQL"],
          ["أخطاء", "codes/extensions", "لا stack"]
        ]
      },
      tips: [
        {
          title: "لا تبدأ بـGraphQL",
          body: "REST يغطي معظم الحالات. انتقل عند تنوع عملاء/حاجة مرونة حقيقية."
        },
        {
          title: "DataLoader إلزامي للعلاقات",
          body: "بدونه N+1 يلتهم الأداء. اختبر عدد الاستعلامات."
        },
        {
          title: "أمّن كل حقل",
          body: "المصادقة عند root لا تكفي. افحص الملكية والصلاحيات في resolver."
        },
        {
          title: "حدود صارمة",
          body: "depth/complexity/timeout/page size. GraphQL يسمح للعميل بطلب شجرة ضخمة."
        }
      ],
      quiz: [
        {
          q: "ما أكبر خطر أداء في GraphQL؟",
          options: [
            "JSON أكبر.",
            "N+1 في resolvers العلاقات.",
            "لا يدعم HTTPS.",
            "لا يمكن استخدامه مع .NET."
          ],
          answer: 1,
          explain: "كل حقل/علاقة قد ينفّذ استعلامًا. DataLoader يجمع الطلبات."
        },
        {
          q: "كيف تحمي من استعلام ضخم؟",
          options: [
            "زيادة timeout فقط.",
            "depth/complexity limits وpage size.",
            "تعطيل authorization.",
            "استخدام GET فقط."
          ],
          answer: 1,
          explain: "حدود التعقيد والعمق تمنع استعلامات مدمرة، مع timeout."
        },
        {
          q: "متى تفضل REST؟",
          options: [
            "عند تنوع عملاء كبير.",
            "عند عميل واحد واحتياجات ثابتة وcaching HTTP مهم.",
            "عند الحاجة لشجرة علاقات معقدة.",
            "دائمًا."
          ],
          answer: 1,
          explain: "REST أبسط وأفضل للعقود الثابتة/caching. GraphQL للمرونة."
        }
      ],
      capstone: {
        title: "GraphQL لكتالوج Souq",
        goal: "أضف schema للكتالوج مع DataLoader وحدود وأمان، وقارن الأداء بـREST.",
        tasks: [
          "عرّف <code>Product</code> و<code>Category</code> و<code>Query</code> في schema.",
          "نفّذ resolver للكتالوج مع projection وحد أقصى للصفحة.",
          "أضف DataLoader لعلاقة التصنيف واختبر عدد الاستعلامات.",
          "أضف سياسة/manage catalog وفحص ملكية حيث يلزم.",
          "اضبط depth/complexity وpersisted queries، وقارن p95 مع REST."
        ],
        code: {
          lang: "graphql",
          title: "Query",
          code: `query {\n  products(first: 20) {\n    name\n    price\n    category { name }\n  }\n}`,
        },
      },
    },
    {
      id: "saga-microservices",
      title: "Saga وMicroservices: معاملات بلا معاملة موزعة",
      duration: 30,
      level: "متقدم",
      summary:
        "عندما تنفصل الخدمات، تفقد المعاملة الواحدة. Saga يدير الخطوات والتعويض، لكنه يضيف حالات وفشلًا يجب مراقبته.",
      keywords: ["Saga", "orchestration", "choreography", "compensation", "idempotency", "microservices", "outbox", "distributed monolith"],
      objectives: [
        "تقرر متى تستحق Microservices التكلفة.",
        "تصمم Saga بخطوات وتعويض.",
        "تتعامل مع timeouts وretries وidempotency.",
        "تختار orchestration أو choreography.",
        "تراقب Sagas العالقة وتختبرها."
      ],
      concept: `
        <p>المعاملة الموزعة ليست معاملة قاعدة بيانات. لا يمكنك ببساطة <code>BeginTransaction</code> عبر شبكة. <strong>Saga</strong> سلسلة خطوات محلية، كل خدمة تنفّذ عملها وتعوض عند الفشل. النتيجة اتساق نهائي، لا ذرية لحظية.</p>
        <h3>متى Microservices؟</h3>
        <p>عندما تحتاج فرقًا مستقلة النشر، حدودًا تنظيمية، مقياسًا مختلفًا، أو تقنية مختلفة. إذا كانت الفرق تنشر معًا وتشارك قاعدة البيانات، فأنت distributed monolith بتكلفة شبكة. ابدأ modular monolith؛ فكّك عند ألم حقيقي.</p>
        <h3>Orchestration vs Choreography</h3>
        <p><strong>Orchestration</strong>: منسق مركزي يعرف الخطوات والحالة. أسهل للتتبع والتشخيص، لكنه نقطة تركيز. <strong>Choreography</strong>: كل خدمة تتفاعل مع أحداث. أقل اقترانًا، لكن تتبع التدفق أصعب. اختر حسب التعقيد والفريق. لا تخلط النموذجين بلا سبب.</p>
        <h3>التعويض</h3>
        <p>كل خطوة تحتاج إجراء تعويض: إلغاء حجز، استرجاع مبلغ، تحرير مخزون. التعويض ليس rollback سحريًا؛ قد يفشل أيضًا. صمّمه idempotent وقابلًا لإعادة المحاولة. لا تفترض أن الخطوة السابقة لم تحدث.</p>
        <h3>الحالات والفشل</h3>
        <p>خزّن حالة Saga: Started، Reserved، Paid، Completed، Failed، Compensating. أضف timeouts وdeadlines. استخدم Outbox للأحداث. كل خطوة تحتاج idempotency key. لا تترك Saga عالقة بلا مراقبة؛ أضف job للتنبيه/الاستئناف.</p>
        <h3>الاتساق</h3>
        <p>المستخدم قد يرى Pending. وضّح ذلك في الواجهة. لا تعرض نجاحًا قبل اكتمال Saga. إذا فشل الدفع، أعد المخزون. إذا فشل التعويض، تدخل يدوي/مراقبة. الاتساق النهائي يحتاج تعريفًا واضحًا للمدة المقبولة.</p>
        <h3>الاختبار</h3>
        <p>اختبر كل خطوة وكل تعويض. اختبر انقطاع خدمة في منتصف Saga. اختبر تكرار الرسالة. اختبر timeout. استخدم Testcontainers/محاكاة. لا تختبر happy path فقط. راقب sagas العالقة ومعدل التعويض.</p>
      `,
      walkthrough: [
        {
          title: "حدود الخدمة",
          code: `Orders -> Payment\n       -> Inventory\n       -> Shipping\n\n// كل خدمة تملك بياناتها.\n// Orders لا يقرأ جدول Payment.`,
          lang: "text",
          body: `<p>ابدأ بالحدود. كل خدمة تملك بياناتها وقاعدة قرارها. لا تجعل Orders يستعلم جدول Payment مباشرة. التعامل عبر API/أحداث. الحدود الخاطئة تجعل Saga معقدة بلا فائدة.</p>`
        },
        {
          title: "حالة Saga",
          code: `public enum OrderSagaState\n{\n    Started,\n    StockReserved,\n    PaymentPending,\n    Paid,\n    Completed,\n    Compensating,\n    Failed\n}`,
          lang: "csharp",
          body: `<p>الحالة صريحة وقابلة للتخزين. لا تعتمد على ذاكرة العامل. كل انتقال مسموح ومختبر. أضف <code>UpdatedAt</code> و<code>LastError</code>. استخدم enum/جدول، لا string عشوائي.</p>`
        },
        {
          title: "منسق Saga",
          code: `public sealed class OrderSaga(OrderSagaStore store, IInventory inventory,\n    IPayment payments, ILogger<OrderSaga> logger)\n{\n    public async Task HandleAsync(Guid orderId, CancellationToken ct)\n    {\n        var saga = await store.GetAsync(orderId, ct);\n        if (saga.State == OrderSagaState.Started)\n        {\n            await inventory.ReserveAsync(orderId, ct);\n            saga.State = OrderSagaState.StockReserved;\n            await store.SaveAsync(saga, ct);\n        }\n    }\n}`,
          lang: "csharp",
          body: `<p>المنسق يقرأ الحالة وينفّذ الخطوة التالية. لا تنفّذ كل الخطوات في ذاكرة واحدة إن كانت طويلة. احفظ الحالة بعد كل خطوة. استخدم idempotency عند الاستدعاء. إذا فشل الحفظ بعد الحجز، قد تحتاج استئنافًا/تعويضًا.</p>`
        },
        {
          title: "تعويض",
          code: `if (paymentFailed)\n{\n    saga.State = OrderSagaState.Compensating;\n    await store.SaveAsync(saga, ct);\n    await inventory.ReleaseAsync(orderId, ct);\n    saga.State = OrderSagaState.Failed;\n    await store.SaveAsync(saga, ct);\n}`,
          lang: "csharp",
          body: `<p>التعويض خطوة صريحة. لا تعتمد على exception. إذا فشل <code>ReleaseAsync</code>، أعد المحاولة وسجّل. لا تعلن Failed قبل نجاح التعويض أو تحويله لتدخل يدوي. كل تعويض idempotent.</p>`
        },
        {
          title: "Idempotency",
          code: `await inventory.ReserveAsync(\n    orderId,\n    idempotencyKey: $"order:{orderId}:reserve",\n    ct);`,
          lang: "csharp",
          body: `<p>الخدمة المستقبلة تخزّن المفتاح/النتيجة. تكرار الطلب لا يحجز مرتين. استخدم مفتاحًا مشتقًا من العملية، لا عشوائيًا. اربطه بالمستخدم/الطلب. اختبر التكرار. هذا أساس Saga آمنة.</p>`
        },
        {
          title: "Timeout وRetry",
          code: `using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);\ncts.CancelAfter(TimeSpan.FromSeconds(10));\nawait payments.AuthorizeAsync(orderId, cts.Token);`,
          lang: "csharp",
          body: `<p>كل استدعاء شبكي يحتاج مهلة. أعد المحاولة للأخطاء العابرة فقط، مع backoff. لا تكرر عملية غير idempotent. إذا انتهت المهلة، قد تكون العملية نجحت؛ تحقق بالحالة/المفتاح قبل التعويض. سجّل النتيجة.</p>`
        },
        {
          title: "Outbox للأحداث",
          code: `db.OutboxMessages.Add(new OutboxMessage\n{\n    Type = "StockReserved",\n    Payload = JsonSerializer.Serialize(new { orderId })\n});\nawait db.SaveChangesAsync(ct);`,
          lang: "csharp",
          body: `<p>لا تنشر حدثًا قبل commit. Outbox يضمن عدم الفقدان. المستهلك idempotent. استخدم partition key للترتيب. راقب lag. هذا يربط Saga بالأحداث دون dual-write.</p>`
        },
        {
          title: "مراقبة Sagas",
          code: `SELECT state, count(*), min(updated_at)\nFROM order_sagas\nWHERE state NOT IN ('Completed','Failed')\nGROUP BY state;`,
          lang: "sql",
          body: `<p>راقب العالقة وعمرها. Saga في Compensating طويلًا إشارة خطر. أضف تنبيهًا. وثّق إجراء الاستئناف/التدخل. اختبر تعطل خدمة. لا تترك الحالة في logs فقط.</p>`
        }
      ],
      compare: {
        intro: `<p>المعاملة المحلية بسيطة؛ Saga تشتري الاستقلال بتعقيد الفشل.</p>`,
        before: {
          label: "Distributed monolith",
          lang: "text",
          title: "قبل",
          code: `Orders -> Payment -> Inventory\nكلها نفس DB ونشر واحد\nمعاملة واحدة وهمية عبر الشبكة`,
          points: [
            "لا استقلال حقيقي.",
            "شبكة بلا فائدة.",
            "تعقيد نشر بلا حدود.",
            "مشاكل الاتساق نفسها."
          ]
        },
        after: {
          label: "Saga",
          lang: "text",
          title: "بعد",
          code: `Started -> Reserve -> Pay -> Complete\n   fail -> Release -> Failed\nOutbox + idempotency + monitoring`,
          points: [
            "حدود ملكية واضحة.",
            "تعويض صريح.",
            "at-least-once + idempotency.",
            "مراقبة الحالات العالقة."
          ]
        },
        verdict: `<p>لا تنتقل إلى Microservices إلا إذا كانت التكلفة مبررة. وإذا انتقلت، صمّم Saga كحالة لا كسلسلة استدعاءات متفائلة.</p>`
      },
      internals: `
        <p>Saga لا تحتفظ بأقفال موزعة. كل خطوة معاملة محلية. التعويض يعكس الأثر. قد يحدث تعويض بعد نجاح جزئي. لذلك idempotency ومراقبة ضرورية.</p>
        <p>Orchestrator يخزن الحالة ويقرر. Choreography يعتمد على الأحداث. كلاهما يحتاج Outbox وidempotent consumers. لا تعتمد على ترتيب عالمي. استخدم partition key للكيان.</p>
        <h3>الفشل</h3>
        <p>timeouts قد تعني نجاحًا غير مؤكد. تحقق قبل التعويض. retries قد تكرر. dead letter يحتاج تدخلًا. لا تحذف Saga فاشلة بلا تحقيق. Runbook للحالات العالقة.</p>
        <h3>الاختبار</h3>
        <p>اختبر كل انتقال/تعويض، تعطل خدمة، تكرار رسالة، timeout. استخدم بيئة تشبه الإنتاج. راقب p95 والمعدل. لا تختبر happy path فقط.</p>
      `,
      internalsTable: {
        head: ["العنصر", "الوظيفة", "الخطر"],
        rows: [
          ["Saga state", "تتبع التقدم", "حالات عالقة"],
          ["Compensation", "عكس الأثر", "فشل التعويض"],
          ["Idempotency", "منع التكرار", "مفتاح خاطئ"],
          ["Outbox", "أحداث مضمونة", "lag"],
          ["Timeout", "منع الانتظار", "نجاح غير مؤكد"],
          ["Monitoring", "كشف العالق", "ضجيج"]
        ]
      },
      tips: [
        {
          title: "لا تبدأ Microservices",
          body: "ابدأ modular monolith. فكّك عند حاجة نشر/فريق/مقياس حقيقية."
        },
        {
          title: "كل خطوة تعويض",
          body: "صمّم compensation idempotent. لا تفترض rollback سحريًا."
        },
        {
          title: "تحقق قبل التعويض",
          body: "timeout قد يعني نجاحًا. استخدم الحالة/idempotency key."
        },
        {
          title: "راقب العالق",
          body: "Saga بلا مراقبة تصبح بيانات مفقودة. تنبيه وعمر وحالة."
        }
      ],
      quiz: [
        {
          q: "ما Saga؟",
          options: [
            "معاملة موزعة ذرية.",
            "سلسلة خطوات محلية مع تعويض عند الفشل.",
            "نوع من قواعد البيانات.",
            "بديل HTTP."
          ],
          answer: 1,
          explain: "Saga لا توفر ذرية موزعة؛ تدير التقدم والتعويض."
        },
        {
          q: "لماذا idempotency؟",
          options: [
            "لتسريع الشبكة.",
            "لأن retries/timeouts قد تكرر الخطوة.",
            "لتشفير الرسائل.",
            "لإلغاء Outbox."
          ],
          answer: 1,
          explain: "كل خطوة قد تُستدعى أكثر من مرة. المفتاح يمنع أثرًا مزدوجًا."
        },
        {
          q: "ماذا تفعل قبل تعويض بعد timeout؟",
          options: [
            "تعويض فورًا دائمًا.",
            "تحقق من الحالة/النتيجة لأن العملية قد تكون نجحت.",
            "حذف Saga.",
            "إعادة كل شيء من البداية."
          ],
          answer: 1,
          explain: "timeout ليس فشلًا مؤكدًا. تحقق قبل عكس الأثر."
        }
      ],
      capstone: {
        title: "Saga لطلب Souq",
        goal: "صمّم Saga لحجز المخزون والدفع، مع تعويض وidempotency ومراقبة.",
        tasks: [
          "حدد خطوات Saga وحالاتها وانتقالاتها.",
          "أضف Reserve/Release للمخزون مع idempotency key.",
          "أضف Authorize Payment مع timeout وتحقق قبل التعويض.",
          "اكتب الحالة في جدول وOutbox بعد كل خطوة.",
          "أضف استعلام/تنبيه للـSagas العالقة واختبر تعطل خدمة."
        ],
        code: {
          lang: "csharp",
          title: "تعويض",
          code: `saga.State = OrderSagaState.Compensating;\nawait store.SaveAsync(saga, ct);\nawait inventory.ReleaseAsync(orderId, ct);\nsaga.State = OrderSagaState.Failed;\nawait store.SaveAsync(saga, ct);`,
        },
      },
    },
    {
      id: "data-protection",
      title: "Data Protection: تشفير وأسرار وبيانات حساسة",
      duration: 28,
      level: "متقدم",
      summary:
        "حماية البيانات ليست تشفير عمود فقط. سنغطي المفاتيح، التشفير، التجزئة، السجلات، النسخ، والوصول.",
      keywords: ["Data Protection", "encryption at rest", "hashing", "key rotation", "PII", "GDPR", "secrets", "redaction"],
      objectives: [
        "تفرّق بين التشفير والتجزئة.",
        "تستخدم Data Protection API وتخزين المفاتيح.",
        "تحمي PII في السجلات والنسخ.",
        "تدير الأسرار وتدوّرها.",
        "تخطط للوصول والتدقيق والحذف."
      ],
      concept: `
        <p>حماية البيانات طبقات: TLS أثناء النقل، تشفير القرص/قاعدة البيانات أثناء التخزين، تشفير حقول حساسة، تجزئة كلمات المرور، إدارة مفاتيح، وصلاحيات وصول. لا تكتفِ بواحدة. ولا تشفّر كل شيء بلا خطة مفاتيح؛ ستفقد القدرة على القراءة.</p>
        <h3>التشفير مقابل التجزئة</h3>
        <p><strong>التشفير</strong> قابل للعكس بمفتاح: مناسب لبيانات تحتاج قراءة (رقم هاتف/عنوان). <strong>التجزئة</strong> أحادية الاتجاه: لكلمات المرور والتحقق. لا تشفّر كلمة مرور؛ استخدم hash قويًا مع salt (ASP.NET Identity/Argon2/bcrypt). لا تستخدم MD5/SHA1 لكلمات المرور.</p>
        <h3>Data Protection API</h3>
        <p>في ASP.NET Core، <code>IDataProtector</code> يشفّر/يحمي payloads (tokens، حقول صغيرة). المفاتيح يجب أن تُخزَّن بشكل دائم ومشترك بين النسخ (Redis/DB/شهادة)، لا في ذاكرة الحاوية. وإلا تفشل فك التشفير بعد restart/scale. احمِ key ring بصلاحيات مناسبة. دوّر المفاتيح.</p>
        <h3>الأسرار</h3>
        <p>مفاتيح التشفير/التوقيع/الاتصال ليست إعدادات عادية. استخدم Secret Manager/خزنة/متغيرات بيئة، وصلاحيات ضيقة. لا تضعها في Git أو صورة Docker أو logs. دوّرها عند الاشتباه. افصل مفاتيح البيئات. لا تشارك مفتاح production مع التطوير.</p>
        <h3>PII والسجلات</h3>
        <p>لا تسجّل البريد/الهاتف/العنوان/التوكن. استخدم redaction. حدد مدة الاحتفاظ. لا تضع PII في metrics labels أو traces. إذا احتجت التدقيق، سجّل معرفًا آمنًا. اطلب أقل بيانات ممكنة (data minimization). وثّق الأساس القانوني إن كان النظام حقيقيًا.</p>
        <h3>الوصول والنسخ</h3>
        <p>مبدأ least privilege. فصل أدوار القراءة/الكتابة. سجّل الوصول الحساس. النسخ الاحتياطية قد تحتوي بيانات غير مشفرة؛ شفّرها واحمِ مفاتيحها. اختبر restore. حدد من يمكنه الوصول. الحذف يجب أن يشمل النسخ/النسخ المؤقتة حسب السياسة.</p>
        <h3>الحوادث</h3>
        <p>إذا تسرّب مفتاح: دوّره، ألغِ الجلسات/التوكنات، افحص السجلات، وقيّم البيانات. لا تحذف الأدلة. خطط للإشعار حسب القانون. اختبر الاستجابة. الأمان عملية، لا إعداد مرة واحدة.</p>
      `,
      walkthrough: [
        {
          title: "صنّف البيانات",
          code: `Public: product name, price\nInternal: stock, order id\nSensitive: email, phone, address\nSecret: password hash, JWT key, DB password`,
          lang: "text",
          body: `<p>التصنيف يحدد الحماية. لا تشفّر كل شيء بالتساوي. ابدأ بـPII والأسرار. وثّق من يقرأ/يكتب. راجع التصنيف عند إضافة حقل. data minimization يقلل المخاطر.</p>`
        },
        {
          title: "احمِ حقلًا",
          code: `public sealed class CustomerProtector(IDataProtectionProvider provider)\n{\n    private readonly IDataProtector _protector =\n        provider.CreateProtector("Souq.Customer.v1");\n\n    public string Protect(string value) => _protector.Protect(value);\n    public string Unprotect(string value) => _protector.Unprotect(value);\n}`,
          lang: "csharp",
          body: `<p><code>CreateProtector</code> يعزل الغرض. استخدم purpose ثابتًا/مُصدّرًا. لا تخزّن ciphertext في حقل أطول من اللازم. أضف عمودًا/نوعًا مناسبًا. اختبر round-trip وفشل مفتاح خاطئ. لا تحمّل كل الحقول في كل استعلام.</p>`
        },
        {
          title: "ثبّت key ring",
          code: `builder.Services.AddDataProtection()\n    .PersistKeysToDbContext<KeyDbContext>()\n    .SetApplicationName("Souq");\n\n// أو shared Redis/volume مع صلاحيات.`,
          lang: "csharp",
          body: `<p>المفاتيح يجب أن تبقى بعد restart وتُشارك بين replicas. <code>SetApplicationName</code> يثبت النطاق. لا تحفظ المفاتيح في ملف داخل الحاوية بلا volume. احمِ الوصول. اختبر فك التشفير بعد إعادة النشر. خطط للتدوير.</p>`
        },
        {
          title: "تشفير أثناء النقل والتخزين",
          code: `TLS 1.2+ للاتصالات\nPostgreSQL: تشفير القرص/النسخ\nS3/Backups: تشفير + مفاتيح منفصلة\nالحقول الحساسة: IDataProtector`,
          lang: "text",
          body: `<p>TLS يحمي أثناء النقل. تشفير القرص/DB يحمي النسخ المادية. تشفير الحقل يحمي من قراءة غير مصرح بها داخل DB. اجمع الطبقات حسب التهديد. لا تعتمد على TLS لحماية البيانات المخزنة.</p>`
        },
        {
          title: "كلمات المرور",
          code: `var hasher = new PasswordHasher<User>();\nuser.PasswordHash = hasher.HashPassword(user, password);\n\nvar result = hasher.VerifyHashedPassword(\n    user, user.PasswordHash, password);`,
          lang: "csharp",
          body: `<p>استخدم PasswordHasher/Identity أو Argon2/bcrypt. لا تشفّر كلمة المرور. salt تلقائي. لا تسجّل كلمة المرور. أضف rate limiting/MFA. لا تكشف إن كان البريد موجودًا في reset. راجع الخوارزمية عند الترقية.</p>`
        },
        {
          title: "الأسرار",
          code: `Jwt__SigningKey_FILE=/run/secrets/jwt_key\nConnectionStrings__Souq_FILE=/run/secrets/db\n# لا تضع القيم في appsettings/Git.`,
          lang: "text",
          body: `<p>استخدم <code>_FILE</code>/خزنة. صلاحيات 0400. لا تضعها في logs. افصل مفاتيح البيئات. دوّرها. إذا تسرّبت، اعتبرها مخترقة. لا تعِد استخدام مفتاح التطوير في production.</p>`
        },
        {
          title: "نقّح السجلات",
          code: `logger.LogInformation("Order {OrderId} paid", order.Id);\n// لا: email, phone, token, card, full request body\n\noptions.Redact("Authorization");\noptions.Redact("Email");`,
          lang: "csharp",
          body: `<p>استخدم قائمة حقول مسموحة. لا تسجّل body كاملًا. أضف redaction في Serilog/OTel. راجع logs دوريًا. حدد retention. PII في logs نسخة إضافية من البيانات تحتاج حماية.</p>`
        },
        {
          title: "النسخ والوصول",
          code: `- شفّر النسخ\n- اختبر restore\n- صلاحيات ضيقة\n- سجّل الوصول\n- احذف حسب السياسة`,
          lang: "text",
          body: `<p>النسخة غير المحمية ثغرة. شفّرها بمفتاح منفصل. اختبر الاستعادة. حدد من يصل. سجّل الوصول الإداري. الحذف يجب أن يشمل النسخ حسب السياسة. لا تنسَ بيئات staging.</p>`
        }
      ],
      compare: {
        intro: `<p>تخزين PII كنص واضح يجعل أي تسريب قاعدة بيانات كارثة.</p>`,
        before: {
          label: "نص واضح",
          lang: "csharp",
          title: "قبل",
          code: `user.Email = request.Email;\nuser.Phone = request.Phone;\nlogger.LogInformation("User " + request.Email);`,
          points: [
            "أي قراءة DB تكشف PII.",
            "السجل يحتوي بريدًا.",
            "النسخ غير محمية.",
            "لا خطة تدوير مفاتيح."
          ]
        },
        after: {
          label: "طبقات حماية",
          lang: "csharp",
          title: "بعد",
          code: `user.Email = protector.Protect(request.Email);\nuser.PasswordHash = hasher.HashPassword(user, request.Password);\nlogger.LogInformation("User {UserId} created", user.Id);`,
          points: [
            "حقل مشفّر.",
            "كلمة مرور مجزأة.",
            "سجل بلا PII.",
            "مفاتيح مُدارة/مدوّرة."
          ]
        },
        verdict: `<p>لا يوجد حل واحد. اجمع TLS، تشفير التخزين، حماية الحقول، تجزئة كلمات المرور، إدارة مفاتيح، وتقليل البيانات.</p>`
      },
      internals: `
        <p>Data Protection يستخدم AES + HMAC ومفاتيح مُدارة. الـpayload محمي ضد التعديل. المفاتيح لها صلاحية/تدوير. إذا فُقد key ring، لا يمكن فك البيانات. إذا تسرّب، تنكشف. لذلك التخزين/الصلاحيات/النسخ مهمة.</p>
        <p>التجزئة لكلمات المرور تستخدم salt/work factor. التشفير للبيانات التي تحتاج استرجاع. لا تخلط. لا تستخدم تشفيرًا متماثلًا يدويًا بلا مكتبة مُدققة. لا تخترع بروتوكولًا.</p>
        <h3>PII</h3>
        <p>قلل الجمع. افصل الحقول الحساسة. حدد retention. لا تضعها في metrics. السجلات والنسخ جزء من النطاق. وثّق الأساس والموافقة إن لزم. احذف عند الطلب حسب السياسة.</p>
        <h3>الحوادث</h3>
        <p>خطة: اكتشف، احتوِ، دوّر المفاتيح، ألغِ الجلسات، افحص، أبلغ. لا تحذف الأدلة. اختبر الخطة. الأمان يحتاج مراجعة دورية واختبار اختراق.</p>
      `,
      internalsTable: {
        head: ["البيانات", "الأداة", "ملاحظة"],
        rows: [
          ["كلمة المرور", "hash + salt", "لا تشفير"],
          ["PII", "IDataProtector", "key ring ثابت"],
          ["النقل", "TLS", "HSTS"],
          ["النسخ", "تشفير", "مفتاح منفصل"],
          ["الأسرار", "vault/env", "تدوير"],
          ["السجلات", "redaction", "retention"]
        ]
      },
      tips: [
        {
          title: "لا تشفّر كلمة المرور",
          body: "استخدم hash قويًا مع salt. التشفير القابل للعكس غير مناسب."
        },
        {
          title: "ثبّت المفاتيح",
          body: "key ring دائم ومشترك. بدونه تفشل بعد restart/scale."
        },
        {
          title: "قلل PII",
          body: "لا تجمع/تسجّل ما لا تحتاجه. Redaction وretention."
        },
        {
          title: "خطط للتسريب",
          body: "تدوير المفاتيح وإلغاء الجلسات وفحص/إبلاغ. لا تنتظر الحادثة."
        }
      ],
      quiz: [
        {
          q: "كيف تخزن كلمة المرور؟",
          options: [
            "نص واضح.",
            "تشفير متماثل.",
            "hash قوي مع salt.",
            "Base64."
          ],
          answer: 2,
          explain: "كلمة المرور تُجزّأ، لا تُشفّر. استخدم PasswordHasher/Argon2/bcrypt."
        },
        {
          q: "لماذا key ring دائم؟",
          options: [
            "لتسريع DB.",
            "حتى يمكن فك التشفير بعد restart/scale.",
            "لتشفير TLS.",
            "لإلغاء الحاجة للأسرار."
          ],
          answer: 1,
          explain: "المفاتيح في ذاكرة الحاوية تضيع. خزّنها بشكل مشترك/دائم."
        },
        {
          q: "ماذا تسجّل من طلب مستخدم؟",
          options: [
            "كل الجسم.",
            "Authorization.",
            "معرفات آمنة ورسائل منظمة بلا PII.",
            "كلمة المرور."
          ],
          answer: 2,
          explain: "قلل البيانات. لا تسجّل توكنات/PII. استخدم redaction."
        }
      ],
      capstone: {
        title: "حماية بيانات Souq",
        goal: "أضف تشفير حقول PII، key ring دائم، redaction، وسياسة تدوير/نسخ.",
        tasks: [
          "صنّف حقول Customer وحدد Sensitive/Secret.",
          "استخدم <code>IDataProtector</code> لحقل البريد/الهاتف مع purpose.",
          "ثبّت key ring في DB/Redis واختبر بعد restart.",
          "أضف redaction للسجلات واختبر عدم ظهور PII.",
          "شفّر النسخ واختبر restore، ووثّق خطة تدوير المفاتيح."
        ],
        code: {
          lang: "csharp",
          title: "Protector",
          code: `var protector = provider.CreateProtector("Souq.Customer.v1");\nvar cipher = protector.Protect(email);\nvar plain = protector.Unprotect(cipher);`,
        },
      },
    },
  ],
});
