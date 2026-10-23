"""Stage 2, Module 3 — Realtime & background work (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S2_D = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s2-m3-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
فيه حاجات المستخدم مستني يشوفها **دلوقتي**: حالة الطلب اتغيرت، المخزون نفد، إشعار من الدعم.
الـpolling (كل 5 ثواني) بيستهلك طلبات بلا فايدة وبيبقى متأخر. الحلول الحقيقية ثلاثة:
**SignalR** (اتصال ثنائي الاتجاه، الأبسط والأشهر في .NET)، **SSE** (اتجاه واحد من الخادم، أخف وأبسط بروتوكوليًا)،
و**WebSocket** خام (تحكم كامل، شغل أكتر).

الدرس ده: تبني Hub يبعت تحديثات لمجموعة مستخدمين، تتعامل مع إعادة الاتصال والأخطاء،
وتختار بين SignalR وSSE بمعيار واضح — مش بحسب الموضة.
"""},
            {"type": "terms", "items": [
                {"term": "Hub", "def": "نقطة نهاية SignalR: تستقبل استدعاءات من العملاء وتبعت لهم أحداثًا."},
                {"term": "ConnectionId", "def": "معرّف اتصال واحد. المستخدم الواحد ممكن يكون له أكثر من اتصال (موبايل + لابتوب)."},
                {"term": "Group", "def": "مجموعة اتصالات تبعت لها مرة واحدة (`orders:<customerId>`) — أهم أداة للخصوصية والأداء."},
                {"term": "`IHubContext<THub>`", "def": "طريقة الإرسال من خارج الـHub (من service أو handler أو consumer) — الاستخدام الأشهر."},
                {"term": "Strongly-typed Hub", "def": "`Hub<IOrdersClient>`: الواجهة بتعرّف الأحداث فتاخد IntelliSense وفحص ترجمة."},
                {"term": "Backplane", "def": "وسيط (Redis/Azure SignalR Service) يربط أكثر من نسخة من التطبيق عشان الرسائل توصل لكل الاتصالات."},
                {"term": "SSE (Server-Sent Events)", "def": "`text/event-stream` فوق HTTP: اتجاه واحد من الخادم، إعادة اتصال تلقائية من المتصفح، وبلا مكتبات."},
                {"term": "`IUserIdProvider`", "def": "يقرر أنهي claim يمثّل «المستخدم» عشان `Clients.User(id)` يشتغل."},
            ]},
            {"type": "table", "head": ["المعيار", "SignalR", "SSE", "Polling"], "rows": [
                ["الاتجاه", "ثنائي (العميل ينادي الخادم والعكس)", "من الخادم فقط", "العميل يطلب"],
                ["التأخير", "فوري", "فوري", "بقدْر الفترة"],
                ["البروتوكول", "WebSocket (مع fallback لـSSE/long-polling)", "HTTP عادي", "HTTP عادي"],
                ["إعادة الاتصال", "يدوية/بمكتبة (`withAutomaticReconnect`)", "تلقائية من المتصفح", "لا حاجة"],
                ["الحمل على الخادم", "اتصالات طويلة + backplane للتوسع", "اتصالات طويلة أخف", "طلبات متكررة"],
                ["المرور عبر proxies/WAF", "قد يحتاج ضبط (WebSocket upgrade)", "أبسط", "الأسهل"],
                ["المتصفح", "كل المتصفحات", "كل المتصفحات الحديثة", "كل شيء"],
                ["أنسب حالة", "شات، لوحات تحكم، أوامر متبادلة", "تقدّم مهمة، إشعارات، أسعار، تدفّق AI", "بيانات نادرة التغيّر"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قاعدة الاختيار في سطر",
             "md": """
**لو العميل محتاج يبعت حاجة للخادم عبر نفس القناة → SignalR. لو التدفق اتجاه واحد → SSE (أخف وأبسط).**
أمثلة: إشعارات حالة الطلب وتقدّم التصدير وأسعار اللحظي = SSE. شات ودعم مباشر ولعبة = SignalR.
ولو عندك 3 مستهلكين فقط وبيانات تتغير كل ساعة → polling بسيط أوفر تشغيليًا.
"""},
            {"type": "heading", "level": 2, "text": "1) SignalR: Hub آمن ومنظّم"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
# الخادم: مدمج في ASP.NET Core
dotnet add Shop.Api package Microsoft.AspNetCore.SignalR.StackExchangeRedis   # للتوسع (اختياري)
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Realtime/OrdersHub.cs", "title": "Strongly-typed Hub + مجموعات + تفويض", "code": r'''
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;

/// <summary>عقد الأحداث المتجهة للعميل — فحص ترجمة بدل أسماء سحرية.</summary>
public interface IOrdersClient
{
    Task OrderStatusChanged(OrderStatusChangedEvent evt);
    Task StockLevelChanged(StockLevelChangedEvent evt);
    Task Notification(string message);
}

public sealed record OrderStatusChangedEvent(Guid OrderId, string Status, DateTimeOffset At);
public sealed record StockLevelChangedEvent(Guid ProductId, int Remaining);

[Authorize]                                        // ✓ لا hub عام بلا مصادقة
public sealed class OrdersHub(ICurrentUser user, ILogger<OrdersHub> log)
    : Hub<IOrdersClient>, IAsyncDisposable
{
    /// <summary>
    /// مجموعة لكل مستخدم: العميل يشوف طلباته هو فقط.
    /// ✗ لا تعتمد على اسم مجموعة يرسله العميل — ده BOLA فوري.
    /// </summary>
    public override async Task OnConnectedAsync()
    {
        if (user.UserId is { } id)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, GroupFor(id));
            log.LogInformation("signalr connected user={UserId} connection={ConnectionId}", id, Context.ConnectionId);
        }
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        if (user.UserId is { } id) await Groups.RemoveFromGroupAsync(Context.ConnectionId, GroupFor(id));
        if (exception is not null)
            log.LogWarning(exception, "signalr disconnected with error user={UserId}", user.UserId);
        await base.OnDisconnectedAsync(exception);
    }

    /// <summary>
    /// طلب تحديث حالة طلب — عبر الـHub. لاحظ فحص الملكية: الـHub endpoint زي أي endpoint.
    /// </summary>
    public async Task SubscribeToOrder(Guid orderId)
    {
        var allowed = await Orders.AuthorizeAccessAsync(orderId, user, Context.User!);
        if (!allowed) throw new HubException("غير مصرّح بمتابعة هذا الطلب");   // رسالة آمنة للعميل

        await Groups.AddToGroupAsync(Context.ConnectionId, $"order:{orderId:N}");
    }

    public static string GroupFor(Guid userId) => $"user:{userId:N}";
    public static string GroupForOrder(Guid orderId) => $"order:{orderId:N}";

    public ValueTask DisposeAsync() => ValueTask.CompletedTask;
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Program.cs", "title": "التسجيل + المصادقة عبر query string للـWebSocket", "code": r'''
builder.Services.AddSignalR(options =>
{
    options.EnableDetailedErrors = false;             // ✓ لا ترسل stack trace للعميل
    options.MaximumReceiveMessageSize = 32 * 1024;    // حد صريح (الافتراضي 32KB)
    options.ClientTimeoutInterval = TimeSpan.FromSeconds(30);
    options.KeepAliveInterval = TimeSpan.FromSeconds(15);
    options.HandshakeTimeout = TimeSpan.FromSeconds(15);
})
// التوسع: أكثر من نسخة تحتاج backplane، وإلا الرسائل تضيع للاتصالات على النسخ الأخرى
.AddStackExchangeRedis(config.GetConnectionString("Redis")!);

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        // ... إعدادات التحقق من درس JWT
        options.Events.OnMessageReceived = ctx =>
        {
            // WebSocket ما يقدرش يبعت رؤوس → التوكن في query string (بتوثيق وتأمين أدناه)
            var token = ctx.Request.Query["access_token"];
            if (!string.IsNullOrEmpty(token) && ctx.HttpContext.Request.Path.StartsWithSegments("/hubs"))
                ctx.Token = token;
            return Task.CompletedTask;
        };
    });

// يرسل لأي مستخدم عبر Clients.User(id) — حدد الـclaim المعتمد
builder.Services.AddSingleton<IUserIdProvider, SubClaimUserIdProvider>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapHub<OrdersHub>("/hubs/orders").RequireAuthorization();
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Realtime/SubClaimUserIdProvider.cs", "title": "IUserIdProvider", "code": r'''
using System.Security.Claims;
using Microsoft.AspNetCore.SignalR;

public sealed class SubClaimUserIdProvider : IUserIdProvider
{
    // ✓ نفس الـclaim اللي ICurrentUser بيعتمد عليه — اتساق بين المصادقة والـrealtime
    public string? GetUserId(ClaimsPrincipal user) =>
        user.FindFirstValue(JwtRegisteredClaimNames.Sub) ?? user.FindFirstValue(ClaimTypes.NameIdentifier);
}
'''},
            {"type": "heading", "level": 2, "text": "2) الإرسال من خارج الـHub (الاستخدام الأشهر)"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/OrdersHandlers.cs", "title": "IHubContext داخل الـservice — حدث واحد بعد نجاح العملية", "code": r'''
using Microsoft.AspNetCore.SignalR;

public sealed class OrderService(
    AppDbContext db, IHubContext<OrdersHub, IOrdersClient> hub, TimeProvider time,
    ILogger<OrderService> log) : IOrderService
{
    public async Task CancelAsync(Guid orderId, ICurrentUser user, CancellationToken ct)
    {
        var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == orderId, ct)
                    ?? throw new NotFoundException("Order", orderId);

        if (!order.CanCancel()) throw new ConflictException("Order", orderId, "الحالة لا تسمح بالإلغاء");
        if (order.CustomerId != user.UserId && !user.Roles.Contains(Roles.Admin))
            throw new ForbiddenException("Order", orderId);

        order.Status = OrderStatus.Cancelled;
        order.UpdatedAt = time.GetUtcNow();
        await db.SaveChangesAsync(ct);

        // ✓ بعد الحفظ — لا تبعت حدثًا عن حالة لم تُلتزم بعد
        // ✓ لمجموعة المستخدم + مجموعة الطلب (مش Clients.All — تسريب وأداء سيئ)
        var evt = new OrderStatusChangedEvent(order.Id, order.Status.ToString(), order.UpdatedAt);
        await Task.WhenAll(
            hub.Clients.Group(OrdersHub.GroupFor(order.CustomerId)).OrderStatusChanged(evt),
            hub.Clients.Group(OrdersHub.GroupForOrder(order.Id)).OrderStatusChanged(evt));

        log.LogInformation("order cancelled order={OrderId} by={UserId}", orderId, user.UserId);
    }
}

/// <summary>بديل أنضف معماريًا: نشر حدث domain واشتراك hub-notifier فيه (فصل كامل).</summary>
public sealed class OrderRealtimeNotifier(IHubContext<OrdersHub, IOrdersClient> hub)
{
    public Task HandleAsync(OrderStatusChanged domainEvent, CancellationToken ct) =>
        hub.Clients.Group(OrdersHub.GroupFor(domainEvent.CustomerId))
           .OrderStatusChanged(new OrderStatusChangedEvent(
               domainEvent.OrderId, domainEvent.Status.ToString(), domainEvent.At));
}
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء SignalR اللي بتاكل وقت",
             "md": """
- **`Clients.All` لحدث يخص مستخدم واحد** → تسريب بيانات + حمل بلا معنى. استخدم مجموعات.
- **نسخ متعددة بلا backplane** → العميل المتصل بنسخة تانية ما يستلمش حاجة (ويظهر كـ«يشتغل أحيانًا»).
- **توكن في query string** → بيظهر في access logs والـproxy. خفّفها: توكن قصير العمر، ولا تسجّل الـquery string، وافصل مسار `/hubs` في اللوجات.
- **رسائل كبيرة** → حد الاستقبال 32KB افتراضيًا؛ ابعت **معرّفات** وخلى العميل يجلب التفاصيل، مش الكائن كله.
- **استدعاء الـHub من `ExecuteAsync` بلا scope** → الـ`IHubContext` singleton فده آمن، لكن خدمات EF scoped لازم من scope (الدرس الجاي).
- **استثناء داخل hub method** → بيوصل العميل كرسالة عامة؛ فعّل `EnableDetailedErrors` فقط في التطوير.
"""},
            {"type": "code", "lang": "javascript", "filename": "wwwroot/js/orders-realtime.js", "title": "العميل: إعادة اتصال وأخطاء وحالة UI", "code": r'''
import * as signalR from "@microsoft/signalr";

export function connectOrdersHub(getAccessToken, handlers) {
  const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/orders", {
      accessTokenFactory: getAccessToken,
      skipNegotiation: true,                 // WebSocket مباشرة (يتطلب backplane/خادم يدعمه)
      transport: signalR.HttpTransportType.WebSockets,
    })
    .withAutomaticReconnect([0, 2000, 5000, 15000, 30000])   // ✓ فترات متصاعدة
    .configureLogging(signalR.LogLevel.Warning)
    .build();

  connection.on("OrderStatusChanged", handlers.onOrderStatusChanged);
  connection.on("StockLevelChanged", handlers.onStockLevelChanged);
  connection.on("Notification", handlers.onNotification);

  connection.onreconnecting(() => handlers.onState("reconnecting"));
  connection.onreconnected(async () => {
    handlers.onState("connected");
    // ★ بعد إعادة الاتصال: المجموعات والاشتراكات ضاعت — أعد تسجيلها
    for (const orderId of handlers.subscribedOrderIds()) {
      await connection.invoke("SubscribeToOrder", orderId);
    }
    await handlers.resync();                  // اجلب الحالة الحالية لسد فجوة الأحداث
  });
  connection.onclose(() => handlers.onState("closed"));

  // إعادة محاولة دائمة لو فشلت البداية (شبكات الموبايل)
  const start = async () => {
    try {
      await connection.start();
      handlers.onState("connected");
    } catch (err) {
      handlers.onState("retrying");
      setTimeout(start, 10000);
    }
  };
  void start();

  return connection;
}
'''},
            {"type": "callout", "kind": "note", "title": "الحدث اللي هيفوتك: resync بعد إعادة الاتصال",
             "md": """
إعادة الاتصال **ما بتعوضش** الأحداث اللي فاتت. لو العميل بينادي `onreconnected` بس من غير ما يجلب
الحالة الحالية، هيفضل يعرض حالة قديمة للأبد.

النمط الصحيح: اتصال + **لقطة حالة أولية** (`GET /api/orders?updatedSince=…`) ثم أحداث تزايدية.
ولو التسلسل مهم فعلًا، ابعت رقم نسخة (`version`/`seq`) مع كل حدث وتجاهل القديم، أو استخدم قناة
مست durable (Redis Streams / Service Bus) بدل الـHub للتسليم المضمون.
"""},
            {"type": "heading", "level": 2, "text": "3) SSE: أخف حل لتدفّق اتجاه واحد"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Realtime/ProgressEndpoints.cs", "title": "SSE مكتوبة يدويًا — تعمل على أي إصدار، وبلا مكتبات", "code": r'''
using System.Runtime.CompilerServices;
using Microsoft.AspNetCore.Http.Json;
using Microsoft.Extensions.Options;

public static IEndpointRouteBuilder MapRealtimeApi(this IEndpointRouteBuilder app)
{
    var group = app.MapGroup("/api/stream").WithTags("Realtime").RequireAuthorization();

    /// <summary>تقدّم تصدير ملف: أحداث حتى الانتهاء.</summary>
    group.MapGet("/exports/{exportId:guid}/progress", async (
        Guid exportId, HttpContext http, IExportProgress progress,
        IOptions<JsonOptions> json, CancellationToken ct) =>
    {
        // ✓ رؤوس SSE الثلاثة — بدونها المتصفح ما يعاملهاش كتدفّق
        http.Response.Headers.ContentType = "text/event-stream; charset=utf-8";
        http.Response.Headers.CacheControl = "no-store, no-transform";
        http.Response.Headers["X-Accel-Buffering"] = "no";     // يمنع buffering في nginx
        http.Response.Headers.Connection = "keep-alive";

        // دفق غير متزامن من الخدمة — والـCancellationToken من HttpContext.RequestAborted
        await foreach (var update in progress.WatchAsync(exportId, ct).WithCancellation(ct))
        {
            var payload = JsonSerializer.Serialize(update, json.Value.SerializerOptions);

            await http.Response.WriteAsync($"id: {update.Seq}\n", ct);      // id → Last-Event-ID عند الإعادة
            await http.Response.WriteAsync($"event: progress\n", ct);
            await http.Response.WriteAsync($"data: {payload}\n\n", ct);     // سطرا نهاية إلزاميان
            await http.Response.Body.FlushAsync(ct);                        // ✓ Flush وإلا الأحداث تتحجز

            if (update.IsFinal) break;
        }
    }).Produces<OrderExportProgress>(contentType: "text/event-stream");

    return app;
}

public sealed record OrderExportProgress(int Seq, string State, int Processed, int Total, bool IsFinal);

public interface IExportProgress
{
    IAsyncEnumerable<OrderExportProgress> WatchAsync(Guid exportId, CancellationToken ct);
}

public sealed record ExportState(string State, int Processed, int Total, bool Done);

public interface IExportStateStore
{
    Task<ExportState> ReadAsync(Guid exportId, CancellationToken ct);
}

/// <summary>تنفيذ بسيط فوق Channel — نفس القناة اللي بيكتب فيها الـBackgroundService.</summary>
public sealed class ChannelExportProgress(IExportStateStore store) : IExportProgress
{
    private static readonly TimeSpan PollFallback = TimeSpan.FromSeconds(2);

    public async IAsyncEnumerable<OrderExportProgress> WatchAsync(
        Guid exportId, [EnumeratorCancellation] CancellationToken ct)
    {
        var seq = 0;
        while (!ct.IsCancellationRequested)
        {
            var state = await store.ReadAsync(exportId, ct);
            yield return new OrderExportProgress(++seq, state.State, state.Processed, state.Total, state.Done);
            if (state.Done) yield break;

            await Task.Delay(PollFallback, ct);   // بديل: انتظر على Channel/Redis PubSub بدل التأخير
        }
    }
}
'''},
            {"type": "code", "lang": "javascript", "filename": "wwwroot/js/export-progress.js", "title": "العميل: EventSource (إعادة اتصال تلقائية)", "code": r'''
export function watchExport(exportId, onProgress, onDone, onError) {
  // EventSource ما يبعتش Authorization header — استخدم كوكي جلسة،
  // أو مكتبة (event-source-polyfill / fetch-event-source) تسمح برؤوس مخصصة.
  const source = new EventSource(`/api/stream/exports/${exportId}/progress`, { withCredentials: true });

  source.addEventListener("progress", (e) => {
    const update = JSON.parse(e.data);
    onProgress(update);
    if (update.isFinal) { onDone(update); source.close(); }
  });

  source.onerror = (err) => {
    // المتصفح بيعيد الاتصال تلقائيًا. لو القفل نهائي (401/404) اقفل يدويًا
    if (source.readyState === EventSource.CLOSED) onError(err);
  };

  return () => source.close();
}
'''},
            {"type": "callout", "kind": "note", "title": ".NET 10 وSSE",
             "md": """
ASP.NET Core 10 أضاف دعمًا مدمجًا لـServer-Sent Events في Minimal APIs (بدل الكتابة اليدوية أعلاه).
النمط اليدوي ده صحيح وشغال على أي إصدار — لكن قبل ما تعتمد على API مدمج، راجع
[What's new in ASP.NET Core 10](https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0)
للتأكد من الأسماء الدقيقة والسلوك في إصدارك (تجنّبًا لأي اختلاف بين الإصدارات).
"""},
            {"type": "heading", "level": 2, "text": "4) التوسع والمراقبة"},
            {"type": "table", "head": ["الموقف", "الحل"], "rows": [
                ["نسخة واحدة", "SignalR في الذاكرة (بلا backplane)"],
                ["نسخ متعددة (K8s/scale set)", "Redis backplane أو **Azure SignalR Service** (يدير الاتصالات عنك)"],
                ["اتصالات بالآلاف على نسخة واحدة", "راجع حدود الـthreads والـGC؛ وفكّر في خدمة مخصصة للـrealtime"],
                ["تسليم مضمون/ترتيب", "قناة مست durable (Redis Streams، Service Bus) + لقطة حالة عند الاتصال"],
                ["قياس", "metrics: عدد الاتصالات، زمن الإرسال، أخطاء handshake، وحجم الرسائل"],
                ["اختبار", "اختبر المنطق في الـservice/`IHubContext` mock، واختبار integration للـhandshake والتفويض"],
            ]},
            {"type": "code", "lang": "csharp", "title": "اختبار Hub logic بدون اتصالات حقيقية", "code": r'''
[Fact]
public async Task Cancel_publishes_to_customer_group_only()
{
    var hub = Substitute.For<IHubContext<OrdersHub, IOrdersClient>>();
    var clients = Substitute.For<IHubClients<IOrdersClient>>();
    var clientProxy = Substitute.For<IOrdersClient>();
    hub.Clients.Returns(clients);
    clients.Group(OrdersHub.GroupFor(customerId)).Returns(clientProxy);

    var service = new OrderService(db, hub, clock, log);
    await service.CancelAsync(orderId, AnUser.Customer(customerId), CancellationToken.None);

    await clientProxy.Received(1).OrderStatusChanged(Arg.Is<OrderStatusChangedEvent>(
        e => e.OrderId == orderId && e.Status == "Cancelled"));

    // ✓ لم نرسل لكل الاتصالات
    clients.DidNotReceiveWithAnyArgs().All(default!);
}
'''},
            {"type": "checkpoints", "items": [
                "أختار بين SignalR وSSE وpolling بمعيار الاتجاه والتأخير والتكلفة التشغيلية.",
                "أبني Hub مفوَّض يبعت لمجموعات (مش `Clients.All`) وأرسل من `IHubContext` بعد الحفظ.",
                "أضبط backplane للتوسع، وأتعامل مع إعادة الاتصال + resync على العميل.",
                "أنفّذ SSE صحيحة (رؤوس + flush + `RequestAborted`) وأختبر منطق الـrealtime بمعزل عن الاتصالات.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "لو محتاج تبعت تقدّم مهمة للعميل فقط (مفيش أوامر من العميل) — أنهي أنسب؟",
                 "options": ["SignalR", "SSE", "WebSocket خام", "Long polling"], "answer": 1,
                 "explain": "اتجاه واحد → SSE: أخف، بلا مكتبة على العميل (`EventSource`)، وإعادة اتصال تلقائية من المتصفح."},
                {"q": "تطبيقك على 3 نسخ والعميل بيشتكي إن التحديثات بتوصل أحيانًا. السبب؟",
                 "options": [
                     "المتصفح بطيء",
                     "مفيش backplane: النسخة اللي بتبعت مش اللي عليها اتصال العميل",
                     "التوكن منتهي",
                     "المجموعات غلط",
                 ], "answer": 1,
                 "explain": "الحل: Redis backplane أو Azure SignalR Service. التشخيص السريع: جرّب نسخة واحدة وشوف هل المشكلة اختفت."},
                {"q": "ليه نبعت بعد `SaveChangesAsync` مش قبله؟",
                 "options": [
                     "أسرع",
                     "عشان العميل ما يستلمش حدثًا عن حالة ممكن تفشل أو تتراجع (transaction)",
                     "متطلب SignalR",
                     "لتقليل الرسائل",
                 ], "answer": 1,
                 "explain": "حدث قبل الالتزام = العميل شاف حالة ما حصلتش. الأفضل معماريًا: outbox pattern للأحداث الحرجة."},
                {"q": "بعد إعادة الاتصال، إيه الإجراء اللي الناس بتنساه؟",
                 "options": [
                     "إعادة تحميل الصفحة",
                     "إعادة الاشتراك في المجموعات + جلب لقطة حالة (resync) لسد الأحداث الفائتة",
                     "تغيير التوكن",
                     "تقليل حجم الرسائل",
                 ], "answer": 1,
                 "explain": "الـgroups مرتبطة بالـconnectionId اللي مات. والأحداث اللي حصلت أثناء الانقطاع مش هتتعوض لوحدها."},
                {"q": "حد `MaximumReceiveMessageSize` 32KB — إيه الخطر لو كبّرته بلا سبب؟",
                 "options": [
                     "رسائل أبطأ",
                     "استهلاك ذاكرة وهجمات استنزاف (عميل يبعت رسائل ضخمة) — والأفضل إرسال معرّفات بدل كائنات كاملة",
                     "فقدان الرسائل",
                     "لا خطر",
                 ], "answer": 1,
                 "explain": "صمّم الرسائل صغيرة: `{ orderId, status }` والعميل يجلب التفاصيل لو محتاج. ده أأمن وأسرع وأبسط."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تحديثات حالة الطلب لحظيًا",
                 "md": "أضف Hub مفوَّض (`/hubs/orders`) يبعت `OrderStatusChanged` لمجموعة المستخدم عند أي تغيير حالة، وعميل JavaScript بـ`withAutomaticReconnect` وresync. أرسل من `IHubContext` داخل الـservice بعد `SaveChangesAsync`.",
                 "criteria": [
                     "الـHub يتطلب مصادقة (`[Authorize]` + `RequireAuthorization`) ويرفض 401 بلا توكن",
                     "مستخدم A لا يستلم أحداث مستخدم B (اختبار/تحقق يدوي بحسابين)",
                     "العميل يعيد الاتصال ويشتغل بعد فصل الخادم 10 ثوانٍ",
                     "لا استخدام لـ`Clients.All` في أي مسار",
                     "اختبار unit للمنطق باستخدام `IHubContext` mock",
                 ],
                 "hint": "لو الاتصال بيرجع 401 رغم توكن صالح: تأكد من `OnMessageReceived` بيقرأ `access_token` من الـquery string **للمسار `/hubs` فقط**، وإن `IUserIdProvider` بيستخدم نفس الـclaim الموجود في التوكن."},
                {"id": "t2", "title": "SSE لتقدّم مهمة",
                 "md": "بدّل (أو أضف) مسار SSE يعرض تقدّم عملية طويلة (تصدير/معالجة) مع `id:` و`event:` وflush صحيح، وعميل `EventSource` يحدّث شريط تقدّم. أثبت إن إلغاء الطلب (قفل التبويب) بيوقف الشغل على الخادم.",
                 "criteria": [
                     "الرؤوس الثلاثة صحيحة والأحداث بتظهر تدريجيًا (مش في الآخر مرة واحدة)",
                     "`HttpContext.RequestAborted` بيوقف التكرار (تحقق من اللوجات)",
                     "الحدث الأخير `isFinal` ويقفل الاتصال من العميل",
                     "مسار محمي بمصادقة وموثق في OpenAPI بـ`text/event-stream`",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "SignalR overview", "url": "https://learn.microsoft.com/aspnet/core/signalr/introduction"},
                {"label": "SignalR hubs API guide", "url": "https://learn.microsoft.com/aspnet/core/signalr/hubs"},
                {"label": "Scale-out with Redis backplane", "url": "https://learn.microsoft.com/aspnet/core/signalr/redis-backplane"},
                {"label": "JWT auth with SignalR", "url": "https://learn.microsoft.com/aspnet/core/signalr/authn-and-authz"},
                {"label": "MDN — Server-Sent Events", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events"},
                {"label": "What's new in ASP.NET Core 10", "url": "https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s2-m3-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
`BackgroundService` شكله أبسط كلاس في .NET — وهو مصدر أشهر الباجات المتقطعة:
تسريب scopes، استثناء بيوقف التطبيق كله، شغل بيكمل بعد الإيقاف، ومهام بتتنفذ مرتين على أكثر من نسخة.

الدرس ده: تكتب hosted service **آمن** (scope لكل تكرار، تعامل مع `StoppingToken`، عزل الاستثناءات)،
وتبني نمط producer/consumer بـ`Channels` — وبعدين تقرر إمتى تحتاج queue worker بدل in-process.
"""},
            {"type": "terms", "items": [
                {"term": "`IHostedService`", "def": "عقد `StartAsync`/`StopAsync` — الـhost بيناديهم عند الإقلاع والإيقاف."},
                {"term": "`BackgroundService`", "def": "تنفيذ جاهز لـ`IHostedService` مع `ExecuteAsync(stoppingToken)`. singleton بطبيعته."},
                {"term": "`IServiceScopeFactory`", "def": "الطريقة الصحيحة للحصول على خدمات scoped (DbContext) من singleton."},
                {"term": "`StoppingToken`", "def": "إلغاء عند الإيقاف. لازم توصل **لكل** عملية I/O وإلا الإيقاف هيتأخر/يتوقف."},
                {"term": "`BackgroundServiceExceptionBehavior`", "def": "سلوك الـhost عند استثناء غير معالج: `StopHost` (الافتراضي في .NET 6+) أو `Ignore`."},
                {"term": "Channel", "def": "طابور داخل العملية (`System.Threading.Channels`) بحدود وback-pressure — أنضف من `ConcurrentQueue` + polling."},
                {"term": "`PeriodicTimer`", "def": "مؤقت دوري بسيط ومحترم للإلغاء — بديل أنظف من `Task.Delay` في حلقة."},
                {"term": "Graceful shutdown", "def": "الإيقاف اللطيف: إشارة → إنهاء الشغل الجاري → خروج ضمن `ShutdownTimeout` (افتراضيًا 30 ثانية)."},
            ]},
            {"type": "heading", "level": 2, "text": "النمط الصحيح: scope لكل تكرار + عزل الأخطاء"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Background/AbandonedOrderWorker.cs", "title": "worker دوري مكتوب بشكل آمن", "code": r'''
using Microsoft.Extensions.Hosting;

public sealed class AbandonedOrderWorker(
    IServiceScopeFactory scopeFactory,          // ★ singleton لا يأخذ DbContext مباشرة
    ILogger<AbandonedOrderWorker> log,
    TimeProvider time) : BackgroundService
{
    private static readonly TimeSpan Interval = TimeSpan.FromMinutes(5);
    private const int BatchSize = 50;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // ✓ تأخير البدء: اترك التطبيق يكمل إقلاعه (health checks, migrations) قبل أول تشغيل
        await Task.Delay(TimeSpan.FromSeconds(15), stoppingToken).ConfigureAwait(false);

        using var timer = new PeriodicTimer(Interval);

        // ✓ الحلقة كلها داخل try: استثناء غير معالج في ExecuteAsync بيوقف الـhost (الافتراضي StopHost)
        try
        {
            do
            {
                try
                {
                    await RunOnceAsync(stoppingToken).ConfigureAwait(false);
                }
                catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
                {
                    break;                       // إيقاف لطيف — مش خطأ
                }
                catch (Exception ex)
                {
                    // ✓ سجّل واستمر: فشل دورة واحدة لا يجب أن يسقط العملية كلها
                    log.LogError(ex, "abandoned-order sweep failed; will retry next interval");
                    Metrics.WorkerFailures.Add(1, new("worker", "abandoned-orders"));
                }
            }
            while (await timer.WaitForNextTickAsync(stoppingToken).ConfigureAwait(false));
        }
        catch (OperationCanceledException)
        {
            log.LogInformation("abandoned-order worker stopping");
        }
    }

    private async Task RunOnceAsync(CancellationToken ct)
    {
        // ★ scope جديد لكل دورة: DbContext scoped، ولا يجوز مشاركته بين الدورات
        await using var scope = scopeFactory.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var orders = scope.ServiceProvider.GetRequiredService<IOrderService>();

        var cutoff = time.GetUtcNow() - TimeSpan.FromMinutes(30);

        var stale = await db.Orders
            .Where(o => o.Status == OrderStatus.New && o.CreatedAt < cutoff)
            .OrderBy(o => o.CreatedAt)
            .Take(BatchSize)
            .Select(o => o.Id)
            .ToListAsync(ct);                    // ✓ ct مُمرَّر

        if (stale.Count == 0) return;

        var cancelled = 0;
        foreach (var id in stale)
        {
            ct.ThrowIfCancellationRequested();
            try
            {
                await orders.CancelAbandonedAsync(id, ct);
                cancelled++;
            }
            catch (ConflictException)
            {
                // عنصر واحد غير قابل للإلغاء (اتدفع مثلًا) — لا توقف الدفعة كلها
                log.LogInformation("skipped order {OrderId}: state changed", id);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                log.LogError(ex, "failed cancelling abandoned order {OrderId}", id);
            }
        }

        log.LogInformation("abandoned sweep: {Found} found, {Cancelled} cancelled", stale.Count, cancelled);
        Metrics.WorkerRuns.Add(1, new("worker", "abandoned-orders", "result", "ok"));
    }
}

// Program.cs
builder.Services.AddHostedService<AbandonedOrderWorker>();

// سلوك الاستثناءات: قرّر عمدًا (الافتراضي StopHost)
builder.Services.Configure<HostOptions>(o =>
{
    o.ShutdownTimeout = TimeSpan.FromSeconds(20);                       // مهلة الإيقاف اللطيف
    o.BackgroundServiceExceptionBehavior = BackgroundServiceExceptionBehavior.StopHost;
    // في Kubernetes: StopHost أفضل — الـpod يعيد التشغيل. Ignore يخفي الأعطال.
});
'''},
            {"type": "callout", "kind": "danger", "title": "أشهر 6 أخطاء في BackgroundService",
             "md": """
1. **حقن `AppDbContext` مباشرة في الـconstructor** → الـservice singleton والـDbContext scoped: استثناء
   أو (أسوأ) context مشترك بين دورات متوازية → `InvalidOperationException` متقطعة وتسريب ذاكرة.
2. **مفيش `try/catch` حول الحلقة** → استثناء واحد (timeout شبكة) بيقفل التطبيق كله في .NET 6+.
3. **عدم تمرير `stoppingToken`** → `ToListAsync()`/`HttpClient` بيكملوا بعد الإيقاف، والـhost بيستنى 30 ثانية ثم يقتل.
4. **`ExecuteAsync` بيعمل `await` لعمل طويل قبل أول `await` حقيقي** → `StartAsync` بيتأخر والإقلاع يتجمد. ابدأ الشغل بعد أول نقطة تعليق، أو استخدم قناة.
5. **شغل متوازي بلا حدود** (`Parallel.ForEach` على 10 آلاف عنصر) → استنزاف اتصال القاعدة. حدد درجة توازي.
6. **نسخ متعددة بتنفذ نفس المهمة** → تكرار شحنات/رسائل. تحتاج distributed lock أو queue أو leader election.
"""},
            {"type": "heading", "level": 2, "text": "producer/consumer بقناة: أنضف نمط لعمل داخل العملية"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Background/EmailQueue.cs", "title": "قناة محدودة + consumer + معالجة دفعية", "code": r'''
using System.Threading.Channels;

/// <summary>
/// طابور داخل العملية. الحدود (Bounded) مهمة: بلا حدود، أي تباطؤ في المعالجة = ذاكرة بلا سقف.
/// `Wait` عند الامتلاء = back-pressure طبيعي على الـAPI بدل الانهيار.
/// </summary>
public sealed class EmailQueue
{
    private readonly Channel<OutgoingEmail> _channel = Channel.CreateBounded<OutgoingEmail>(
        new BoundedChannelOptions(capacity: 500)
        {
            FullMode = BoundedChannelFullMode.Wait,
            SingleReader = true,
            SingleWriter = false,
        });

    public ValueTask EnqueueAsync(OutgoingEmail email, CancellationToken ct) =>
        _channel.Writer.WriteAsync(email, ct);

    public IAsyncEnumerable<OutgoingEmail> ReadAllAsync(CancellationToken ct) =>
        _channel.Reader.ReadAllAsync(ct);

    public bool TryComplete() => _channel.Writer.TryComplete();
}

public sealed record OutgoingEmail(Guid Id, string To, string Subject, string Body);

public sealed class EmailSenderWorker(
    EmailQueue queue, IEmailSender sender, ILogger<EmailSenderWorker> log,
    IServiceScopeFactory scopeFactory) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        log.LogInformation("email sender started");

        await foreach (var email in queue.ReadAllAsync(stoppingToken).ConfigureAwait(false))
        {
            try
            {
                await using var scope = scopeFactory.CreateAsyncScope();
                var store = scope.ServiceProvider.GetRequiredService<IOutboxStore>();

                // ✓ idempotency: لو الرسالة اتبعتت قبلًا (إعادة تشغيل بعد crash) ما تتبعتش تاني
                if (await store.IsSentAsync(email.Id, stoppingToken)) continue;

                await sender.SendAsync(email, stoppingToken);
                await store.MarkSentAsync(email.Id, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                // ✗ ما تبتلعش الرسالة: أرجعها للطابور بعد تأخير (أو لطابور dead-letter)
                log.LogError(ex, "failed sending email {EmailId}", email.Id);
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
                await queue.EnqueueAsync(email with { }, stoppingToken);
            }
        }

        log.LogInformation("email sender stopped");
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        queue.TryComplete();                       // أوقف القبول، واملأ ما في الطابور
        await base.StopAsync(cancellationToken);
    }
}

// الاستخدام من handler — بلا انتظار الإرسال في مسار الطلب (يقلل زمن الاستجابة)
await emailQueue.EnqueueAsync(new OutgoingEmail(id, to, subject, body), ct);
return TypedResults.Accepted();                    // 202: اتقبلت، هتتنفذ قريبًا
'''},
            {"type": "callout", "kind": "warn", "title": "حدود القنوات داخل العملية",
             "md": """
القناة **في الذاكرة**: لو العملية وقعت، كل الرسائل اللي جواها ضاعت. مقبول لـ: إشعارات قابلة لإعادة التوليد،
مهام غير حرجة. غير مقبول لـ: مدفوعات، شحن، فواتير، رسائل يجب ألا تُفقد.

للحالات الحرجة استخدم واحدًا من:
- **Outbox في قاعدة البيانات**: اكتب الرسالة في نفس transaction تغيير الحالة، وworker بيقراها ويخلصها (at-least-once + idempotent).
- **Queue حقيقي**: RabbitMQ / Azure Service Bus / SQS عبر MassTransit (إعادة محاولة، DLQ، ترتيب، تعدد مستهلكين).
"""},
            {"type": "heading", "level": 2, "text": "القرار: hosted service ولا queue worker ولا scheduler؟"},
            {"type": "table", "head": ["الاحتياج", "الحل", "ليه"], "rows": [
                ["مهمة دورية بسيطة داخل العملية", "`BackgroundService` + `PeriodicTimer`", "بلا بنية إضافية؛ مقبول لو فشل دورة مش كارثة"],
                ["شغل ناتج عن طلب ويب (بلا انتظار)", "Channel + consumer worker", "فصل زمن الاستجابة عن زمن المعالجة"],
                ["جدولة cron مع إعادة محاولة ولوحة تحكم", "Hangfire أو Quartz (الدرس الجاي)", "تخزين دائم، retries، رؤية، إعادة تشغيل بعد سقوط العملية"],
                ["رسائل يجب ألا تُفقد / تعدد خدمات", "MassTransit + RabbitMQ/Service Bus", "تسليم مضمون، DLQ، تعدد مستهلكين، فصل تشغيلي"],
                ["مهام ثقيلة/متقطعة (تقارير ليلية)", "مهمة مجدولة منفصلة (K8s CronJob / Functions)", "عزل الموارد عن خدمة الـAPI"],
                ["نفس المهمة على أكثر من نسخة", "Distributed lock أو queue واحد", "منع التنفيذ المزدوج"],
            ]},
            {"type": "code", "lang": "csharp", "title": "نسخ متعددة: قفل موزّع بسيط بـPostgres (advisory lock)", "code": r'''
/// <summary>
/// يمنع تنفيذ نفس الدورة على أكثر من نسخة في نفس الوقت.
/// advisory lock في Postgres: يُحرَّر تلقائيًا عند انتهاء الجلسة (لا يتعلّق لو fellت النسخة).
/// </summary>
public sealed class PostgresSweepLock(AppDbContext db, ILogger<PostgresSweepLock> log)
{
    public async Task<IDisposable?> TryAcquireAsync(long key, CancellationToken ct)
    {
        var acquired = await db.Database
            .SqlQueryRaw<bool>("SELECT pg_try_advisory_lock({0}) AS value", key)
            .SingleAsync(ct);

        if (!acquired)
        {
            log.LogDebug("sweep {Key} already running on another instance", key);
            return null;
        }
        return new Releaser(db, key, log);
    }

    private sealed class Releaser(AppDbContext db, long key, ILogger log) : IDisposable
    {
        public void Dispose()
        {
            try { db.Database.ExecuteSqlRaw("SELECT pg_advisory_unlock({0})", key); }
            catch (Exception ex) { log.LogWarning(ex, "failed releasing advisory lock {Key}", key); }
        }
    }
}

// في الـworker
using var gate = await sweepLock.TryAcquireAsync(key: 4242, stoppingToken);
if (gate is null) return;                 // نسخة تانية شغالة — تخطَّ الدورة بهدوء
await RunOnceAsync(stoppingToken);
'''},
            {"type": "heading", "level": 2, "text": "اختبار الـworker"},
            {"type": "code", "lang": "csharp", "title": "اختبر المنطق، مش الحلقة", "code": r'''
public sealed class AbandonedOrderWorkerTests
{
    [Fact]
    public async Task Cancels_only_orders_older_than_cutoff()
    {
        // ★ المنطق مستخرج في service قابل للاختبار — الـworker مجرد حلقة توقيت
        var service = new AbandonedOrderSweeper(db, clock, notifier);
        clock.Set(new DateTimeOffset(2026, 10, 22, 12, 0, 0, TimeSpan.Zero));

        db.Orders.AddRange(
            AnOrder.WithStatus(OrderStatus.New).CreatedAt(clock.Now - TimeSpan.FromMinutes(45)).Build(),
            AnOrder.WithStatus(OrderStatus.New).CreatedAt(clock.Now - TimeSpan.FromMinutes(5)).Build(),
            AnOrder.WithStatus(OrderStatus.Paid).CreatedAt(clock.Now - TimeSpan.FromHours(3)).Build());
        await db.SaveChangesAsync();

        var result = await service.SweepAsync(batchSize: 50, CancellationToken.None);

        result.Cancelled.Should().Be(1);
        result.Skipped.Should().Be(2);
    }

    [Fact]
    public async Task Worker_stops_promptly_on_cancellation()
    {
        using var cts = new CancellationTokenSource();
        var worker = new AbandonedOrderWorker(scopeFactory, log, clock);

        var run = worker.StartAsync(cts.Token);
        cts.CancelAfter(TimeSpan.FromMilliseconds(200));

        // ✓ لو الـstoppingToken مُمرَّر صح، الإيقاف فوري — وإلا الاختبار ده هيتعلّق
        await worker.StopAsync(CancellationToken.None).WaitAsync(TimeSpan.FromSeconds(2));
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أكتب `BackgroundService` بـscope لكل دورة و`try/catch` حول الحلقة وتمرير `stoppingToken` في كل مكان.",
                "أستخدم `Channels` بحدود (back-pressure) لنمط producer/consumer وأفهم حدوده في الذاكرة.",
                "أختار بين hosted service وscheduler وqueue worker بمعيار الدوام والتسليم المضمون.",
                "أمنع التنفيذ المزدوج على نسخ متعددة (lock/queue) وأجعل المعالج idempotent.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `AppDbContext` في constructor الـ`BackgroundService` خطأ؟",
                 "options": [
                     "بطيء",
                     "الـworker singleton والـDbContext scoped → عمر غير متطابق: سياق مشترك/مغلق واستثناءات متقطعة",
                     "EF Core ما بيدعمش",
                     "يحتاج transaction",
                 ], "answer": 1,
                 "explain": "الحل: `IServiceScopeFactory` و`CreateAsyncScope()` **داخل كل دورة**، ثم التخلص منه في نهاية الدورة."},
                {"q": "استثناء غير معالج داخل `ExecuteAsync` — إيه اللي بيحصل افتراضيًا في .NET 6+؟",
                 "options": [
                     "يُسجَّل ويُكمل",
                     "الـhost بيتوقف بالكامل (`BackgroundServiceExceptionBehavior.StopHost`)",
                     "يعيد المحاولة تلقائيًا",
                     "يوقف الـworker فقط",
                 ], "answer": 1,
                 "explain": "سلوك مقصود: فشل صامت أخطر. في K8s الـpod هيتعاد تشغيله — لكن الأفضل `try/catch` داخل الحلقة مع تسجيل وقياس."},
                {"q": "القناة (Channel) غير محدودة `CreateUnbounded` — الخطر؟",
                 "options": [
                     "أبطأ",
                     "استهلاك ذاكرة بلا سقف لو المستهلك أبطأ من المنتج (والانهيار بدل الـback-pressure)",
                     "فقدان ترتيب",
                     "تعارضات",
                 ], "answer": 1,
                 "explain": "`Bounded` مع `FullMode.Wait` بيديك back-pressure طبيعي: المنتج يستنى بدل ما الذاكرة تنفجر."},
                {"q": "تطبيقك على 3 نسخ بيوقف الطلبات المتروكة. النتيجة المتوقعة من غير قفل؟",
                 "options": [
                     "أسرع",
                     "التنفيذ الثلاثي: محاولات متضاربة، رسائل مكررة، وسجلات مضللة",
                     "لا شيء",
                     "قفل تلقائي",
                 ], "answer": 1,
                 "explain": "الحل: قفل موزّع (advisory lock/Redis)، أو queue بمستهلك واحد، أو K8s CronJob منفصل، أو leader election."},
                {"q": "ليه تمرير `stoppingToken` لكل عملية I/O مهم؟",
                 "options": [
                     "متطلب ترجمة",
                     "الإيقاف اللطيف: بدونه الشغل بيكمل بعد إشارة الإيقاف فيستهلك مهلة `ShutdownTimeout` ثم يُقتل قسرًا",
                     "لتقليل اللوجات",
                     "لتحسين الأداء",
                 ], "answer": 1,
                 "explain": "في K8s القتل القسري = transaction ناقصة وحالة متضاربة. مرّر التوكن في `ToListAsync`, `HttpClient`, `Task.Delay`, `WaitForNextTickAsync`."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "worker آمن ومختبر",
                 "md": "حوّل أي مهمة دورية عندك (تنظيف، مزامنة، تقارير) إلى `BackgroundService` بالنمط الآمن: scope لكل دورة، `PeriodicTimer`، `try/catch` داخل الحلقة، `stoppingToken` في كل I/O، واستخرج المنطق في service قابل للاختبار.",
                 "criteria": [
                     "لا يوجد DbContext أو أي خدمة scoped في الـconstructor",
                     "فشل دورة واحدة لا يوقف التطبيق (اختبار: اجعل الـservice يرمي مرة وأكد الاستمرار)",
                     "إيقاف التطبيق يتم في أقل من 5 ثوانٍ (قِس ووثّق)",
                     "قياس (metric) لعدد الدورات والفشل",
                     "اختباران unit للمنطق المستخرج",
                 ],
                 "hint": "لو الإيقاف بطيء: ابحث عن أي نداء I/O بلا `stoppingToken` — غالبًا `Task.Delay` أو استعلام قاعدة بيانات."},
                {"id": "t2", "title": "طابور داخل العملية مع idempotency",
                 "md": "انقل عملًا بطيئًا من مسار الطلب (إرسال بريد/إشعار/توليد ملف) إلى قناة محدودة + consumer، وأعد 202 فورًا. أضف outbox/idempotency key بحيث إعادة التشغيل لا تكرر التنفيذ.",
                 "criteria": [
                     "قناة `Bounded` بحد معلن و`FullMode.Wait`",
                     "زمن استجابة الـendpoint قلّ (قِس قبل/بعد)",
                     "إعادة تشغيل التطبيق أثناء المعالجة لا ترسل نفس الرسالة مرتين (اختبار أو تحقق)",
                     "فشل عنصر واحد لا يفقد الطابور ولا يوقف المستهلك",
                     "قرار موثق: هل الحالة دي محتاجة queue حقيقي بدل قناة في الذاكرة؟",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Background tasks with hosted services", "url": "https://learn.microsoft.com/dotnet/core/extensions/background-service"},
                {"label": "Queued background service example", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/host/hosted-services"},
                {"label": "System.Threading.Channels", "url": "https://learn.microsoft.com/dotnet/core/extensions/channels"},
                {"label": "Graceful shutdown / HostOptions", "url": "https://learn.microsoft.com/dotnet/core/extensions/generic-host"},
                {"label": "PostgreSQL advisory locks", "url": "https://www.postgresql.org/docs/current/explicit-locking.html"},
            ]},
        ],
    },
]
