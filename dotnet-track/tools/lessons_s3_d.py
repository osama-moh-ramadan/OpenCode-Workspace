"""Stage 3, Module 3 — Caching, alternative storage & measurement (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S3_D = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s3-m3-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
Redis هو «السكين السويسري» للـbackend: كاش موزّع، أقفال، عدّادات، طوابير خفيفة، pub/sub.
وسبب أغلب مشاكله مش صعوبة الـAPI — ده **سوء فهم لطبيعته**: Redis مش قاعدة بيانات (تسليم غير متزامن،
بيانات ممكن تضيع)، ومفاتيحه بلا حدود = ذاكرة بلا حدود، وقفل موزّع مكتوب غلط = أسوأ من بلا قفل.

الدرس ده: cache-aside بـTTL وإبطال صحيح، أقفال موزّعة **بعناية** (مع fencing tokens)،
وطوابير خفيفة (Lists/Streams/Pub-Sub) — وإمتى تسيب Redis وتروح لوسيط رسائل حقيقي.
"""},
            {"type": "terms", "items": [
                {"term": "`ConnectionMultiplexer`", "def": "الاتصال بـRedis. **Singleton واحد للتطبيق كله** — thread-safe ويدير الاتصالات داخليًا. أكثر من واحد = استنزاف اتصالات."},
                {"term": "Cache-aside", "def": "النمط الأشهر: اقرأ من الكاش، ولو فاشل اقرأ من المصدر واكتب في الكاش بـTTL."},
                {"term": "TTL (Expiry)", "def": "مدة صلاحية المفتاح. شبكة أمان ضد الإبطال المنسي، لكنها ليست بديلًا عن الإبطال المقصود."},
                {"term": "Eviction policy", "def": "سلوك Redis عند امتلاء الذاكرة: `noeviction` (يرفض الكتابة)، `allkeys-lru`، `volatile-lru`، `volatile-ttl`."},
                {"term": "Cache Stampede", "def": "لحظة انتهاء مفتاح ساخن: مئات الطلبات تحسب نفس القيمة على المصدر معًا."},
                {"term": "Fencing Token", "def": "رقم تسلسلي متزايد يُمنح مع القفل، ويُفحص عند المورد المحمي — الحماية الحقيقية من القفل المنتهي."},
                {"term": "Redis Streams", "def": "طابور دائم بمجموعات مستهلكين وACKs وقائمة pending — أقرب لوسيط رسائل حقيقي من Lists."},
                {"term": "Pub/Sub", "def": "بث لحظي **بلا ضمان تسليم**: المشترك غير المتصل يفقد الرسالة. للإشارات لا للأحداث الحرجة."},
                {"term": "Keyspace notification", "def": "إشعارات بتغيّر المفاتيح (تحتاج تفعيلها، وتكلف ذاكرة/CPU، وبلا ضمان تسليم)."},
            ]},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم والتشغيل", "code": r'''
dotnet add Shop.Api package Microsoft.Extensions.Caching.StackExchangeRedis
dotnet add Shop.Api package StackExchange.Redis
dotnet add Shop.Api package Microsoft.Extensions.Caching.Hybrid     # L1+L2 معًا (من درس الكاش)

docker run --rm -p 6379:6379 --name shop-redis redis:7-alpine
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses|evicted_keys"
redis-cli CONFIG GET maxmemory-policy
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Caching/RedisSetup.cs", "title": "التهيئة الصحيحة: multiplexer واحد + إعدادات أمان", "code": r'''
using StackExchange.Redis;

public static class RedisSetup
{
    public static IServiceCollection AddRedisCache(this IServiceCollection services, IConfiguration config)
    {
        var cs = config.GetConnectionString("Redis")
                 ?? throw new InvalidOperationException("ConnectionStrings:Redis مطلوب");

        // ★ Singleton واحد لكل التطبيق (لا تخلق multiplexer لكل عملية)
        services.AddSingleton<IConnectionMultiplexer>(_ =>
            ConnectionMultiplexer.Connect(ConfigurationOptions.Parse(cs, configure: o =>
            {
                o.AbortOnConnectFail = false;      // ✓ لا تفشل الإقلاع لو Redis واقع — اخدم من المصدر
                o.ConnectRetry = 3;
                o.ConnectTimeout = 5_000;
                o.SyncTimeout = 2_000;             // سقف زمني للعمليات (وإلا طلباتك تتعلّق)
                o.AsyncTimeout = 2_000;
                o.ClientName = $"shop-api:{Environment.MachineName}";
                o.Ssl = config.GetValue<bool>("Redis:UseTls");
            })));

        // IDistributedCache: واجهة بسيطة (byte[]) — مناسبة لقيم صغيرة
        services.AddStackExchangeRedisCache(o =>
        {
            o.Configuration = cs;
            o.InstanceName = "shop:";              // prefix منطقي لعزل البيئات/التطبيقات
        });

        // HybridCache: L1 في الذاكرة + L2 في Redis + حماية من stampede (الموصى به للبيانات المحسوبة)
        services.AddHybridCache(o =>
        {
            o.DefaultEntryOptions = new HybridCacheEntryOptions
            {
                Expiration = TimeSpan.FromMinutes(10),
                LocalCacheExpiration = TimeSpan.FromSeconds(30),
            };
            o.MaximumPayloadBytes = 256 * 1024;    // ✓ ارفض القيم الضخمة
        });

        services.AddSingleton<IRedisCacheService, RedisCacheService>();
        services.AddSingleton<IDistributedLockFactory, RedisLockFactory>();

        return services;
    }
}

/// <summary>
/// غلاف عملي فوق IDatabase: تسلسل JSON قوي النوع + TTL + قياس + فشل آمن (fall-through للمصدر).
/// </summary>
public sealed class RedisCacheService(
    IConnectionMultiplexer redis, ILogger<RedisCacheService> log, TimeProvider time) : IRedisCacheService
{
    private IDatabase Db => redis.GetDatabase();

    public async Task<T?> GetOrSetAsync<T>(
        string key, Func<CancellationToken, ValueTask<T>> factory,
        TimeSpan ttl, CancellationToken ct) where T : class
    {
        var started = time.GetTimestamp();
        try
        {
            var cached = await Db.StringGetAsync(key);
            if (cached.HasValue)
            {
                CacheMetrics.Hits.Add(1, new("key", Prefix(key)));
                return JsonSerializer.Deserialize<T>(cached.ToString(), AppJson.Options);
            }
        }
        catch (RedisException ex)
        {
            // ★ فشل الكاش لا يُفشل الطلب: اخدم من المصدر وسجّل
            log.LogWarning(ex, "redis read failed for {Key}; falling back to source", key);
            CacheMetrics.Errors.Add(1, new("op", "get"));
        }

        CacheMetrics.Misses.Add(1, new("key", Prefix(key)));
        var value = await factory(ct);

        if (value is not null)
        {
            try
            {
                var payload = JsonSerializer.SerializeToUtf8Bytes(value, AppJson.Options);
                if (payload.Length > 128 * 1024)
                    log.LogWarning("large cache value {Key}: {Size}KB — راجع التصميم",
                        key, payload.Length / 1024);

                await Db.StringSetAsync(key, payload, ttl, When.Always);
            }
            catch (RedisException ex)
            {
                log.LogWarning(ex, "redis write failed for {Key}", key);
                CacheMetrics.Errors.Add(1, new("op", "set"));
            }
        }

        CacheMetrics.LoadDuration.Record(time.GetElapsedTime(started).TotalMilliseconds, new("key", Prefix(key)));
        return value;
    }

    public async Task InvalidateAsync(string key, CancellationToken ct = default)
    {
        await Db.KeyDeleteAsync(key);
        CacheMetrics.Evictions.Add(1, new("key", Prefix(key)));
    }

    /// <summary>إبطال بنمط (prefix) — انتبه: KEYS ممنوع في الإنتاج؛ استخدم SCAN.</summary>
    public async Task<int> InvalidateByPrefixAsync(string prefix, CancellationToken ct)
    {
        var server = redis.GetServers().FirstOrDefault(s => s.IsConnected && !s.IsReplica)
                     ?? throw new InvalidOperationException("لا يوجد Redis server متاح");

        var deleted = 0;
        // ✓ SCAN (async enumerable) بدل KEYS: لا يحجب الخادم
        await foreach (var key in server.KeysAsync(db: 0, pattern: $"{prefix}*", pageSize: 500).WithCancellation(ct))
        {
            await Db.KeyDeleteAsync(key);
            deleted++;
        }
        CacheMetrics.Evictions.Add(deleted, new("key", Prefix(prefix)));
        return deleted;
    }

    private static string Prefix(string key) => key.Contains(':') ? key[..key.IndexOf(':')] : key;
}

public static class CacheMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Api.cache", "1.0.0");
    public static readonly Counter<long> Hits = Meter.CreateCounter<long>("cache.hits");
    public static readonly Counter<long> Misses = Meter.CreateCounter<long>("cache.misses");
    public static readonly Counter<long> Errors = Meter.CreateCounter<long>("cache.errors");
    public static readonly Counter<long> Evictions = Meter.CreateCounter<long>("cache.evictions");
    public static readonly Histogram<double> LoadDuration =
        Meter.CreateHistogram<double>("cache.load.duration", unit: "ms");
}
'''},
            {"type": "callout", "kind": "warn", "title": "Redis: 6 قواعد تشغيلية تنقذك",
             "md": """
1. **`maxmemory` و`maxmemory-policy` مضبوطان صراحة**: للكاش الخالص استخدم `allkeys-lru` أو `volatile-lru`
   (مع TTL على كل مفتاح). لو `noeviction` وامتلات الذاكرة → **كل الكتابات تفشل** (بما فيها أقفالك وطوابيرك).
2. **لا تخزّن بياناتك الأساسية في Redis**: النسخ المتماثل **غير متزامن** (فقدان بيانات في نافذة الفشل)،
   و`AOF everysec` يعني فقد ثانية. Redis = كاش/تنسيق، مش system of record.
3. **مفاتيح بأسماء منظمة**: `shop:orders:{id}` و`shop:catalog:list:{hash}` — يسهّل الإبطال والمراقبة وعزل البيئات.
4. **قيم صغيرة**: كل قيمة > 100KB = مشكلة شبكة وتسلسل. خزّن projection لا كيان كامل.
5. **TTL على كل مفتاح**: شبكة أمان ضد الإبطال المنسي. مفتاح بلا TTL = تسريب ذاكرة دائم.
6. **افشل مفتوحًا (fail-open) للكاش**: `RedisException` → اخدم من المصدر وسجّل، ولا تُرجع 500 للمستخدم.
"""},
            {"type": "heading", "level": 2, "text": "الإبطال: الجزء الصعب فعلًا"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Caching/CacheInvalidation.cs", "title": "3 استراتيجيات + إبطال L1 عبر pub/sub لكل النسخ", "code": r'''
/// <summary>
/// الاستراتيجية ①: مفتاح بإصدار (versioned key) — الأبسط والأأمن.
/// عند التغيير: زد الإصدار؛ المفاتيح القديمة تموت بـTTL بلا مطاردة.
/// </summary>
public sealed class VersionedCacheKeys(IRedisCacheService cache)
{
    public async Task<string> ProductKeyAsync(Guid productId, CancellationToken ct)
    {
        var version = await cache.GetOrSetAsync(
            "shop:ver:products",
            async token => await GetVersionAsync(token),
            ttl: TimeSpan.FromMinutes(5), ct);

        return $"shop:products:v{version}:{productId}";
    }

    public Task BumpProductsVersionAsync(CancellationToken ct) => SetVersionAsync(ct);

    private Task<int> GetVersionAsync(CancellationToken ct) => Task.FromResult(1);   // من جدول/مفتاح Redis
    private Task SetVersionAsync(CancellationToken ct) => Task.CompletedTask;           // INCR على مفتاح الإصدار
}

/// <summary>
/// الاستراتيجية ②: وسوم (HybridCache) — إبطال مجموعة مفاتيح بنداء واحد.
/// (راجع درس الكاش في المرحلة 2: RemoveByTagAsync)
/// </summary>

/// <summary>
/// الاستراتيجية ③: إبطال L1 في كل النسخ عبر Redis pub/sub.
/// المشكلة: HybridCache يبقي نسخة محلية؛ النشر بين النسخ يحلّ عدم الاتساق.
/// </summary>
public sealed class CacheInvalidationBroadcaster(
    IConnectionMultiplexer redis, ILogger<CacheInvalidationBroadcaster> log) : IHostedService
{
    private const string Channel = "shop:cache:invalidate";
    private readonly string _nodeId = Guid.NewGuid().ToString("N");
    private Action<RedisChannel, RedisValue>? _handler;

    public Task StartAsync(CancellationToken ct)
    {
        var subscriber = redis.GetSubscriber();

        _handler = async (channel, message) =>
        {
            var payload = JsonSerializer.Deserialize<InvalidationMessage>(message.ToString());
            if (payload is null || payload.NodeId == _nodeId) return;      // تجاهل رسائلك

            log.LogDebug("invalidating {Key} from node {Node}", payload.Key, payload.NodeId);
            await InvalidateLocalAsync(payload.Key);                        // أزل من L1 المحلي
        };

        return subscriber.SubscribeAsync(RedisChannel.Literal(Channel), _handler);
    }

    public Task StopAsync(CancellationToken ct) =>
        _handler is null ? Task.CompletedTask
                         : redis.GetSubscriber().UnsubscribeAsync(RedisChannel.Literal(Channel));

    public Task BroadcastAsync(string key, CancellationToken ct) =>
        redis.GetSubscriber().PublishAsync(RedisChannel.Literal(Channel),
            JsonSerializer.Serialize(new InvalidationMessage(_nodeId, key)));

    private Task InvalidateLocalAsync(string key) => Task.CompletedTask;   // إزالة من الذاكرة المحلية
    private sealed record InvalidationMessage(string NodeId, string Key);
}
'''},
            {"type": "callout", "kind": "note", "title": "تحذير: pub/sub بلا ضمان تسليم",
             "md": """
نسخة كانت مقطوعة لحظة النشر → ما استلمتش الإبطال → **L1 عندها بيانات قديمة حتى انتهاء TTL المحلي**.
عشان كده `LocalCacheExpiration` القصير (10-30 ثانية) مش رفاهية: هو شبكة الأمان لهذا السيناريو بالظبط.

لو بياناتك لا تتحمل أي عدم اتساق → **لا تستخدم L1** لها (Redis فقط)، أو اجعل TTL المحلي = 0.
"""},
            {"type": "heading", "level": 2, "text": "الأقفال الموزّعة: بعناية أو لا تستخدمها"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Infrastructure/Locking/RedisLockFactory.cs", "title": "SET NX PX + قيمة فريدة + تحرير بـLua + fencing token", "code": r'''
using StackExchange.Redis;

public interface IDistributedLock : IAsyncDisposable
{
    string Key { get; }
    long FenceToken { get; }        // ★ رقم تسلسلي يفحصه المورد المحمي
    bool Acquired { get; }
}

public sealed class RedisLockFactory(IConnectionMultiplexer redis, ILogger<RedisLockFactory> log)
    : IDistributedLockFactory
{
    // تحرير ذرّي: احذف فقط لو القيمة بتاعتك (وإلا هتحذف قفل حد تاني)
    private const string ReleaseScript = """
        if redis.call("GET", @key) == @value then
            return redis.call("DEL", @key)
        else
            return 0
        end
        """;

    public async Task<IDistributedLock?> TryAcquireAsync(
        string key, TimeSpan lease, TimeSpan wait, CancellationToken ct)
    {
        var db = redis.GetDatabase();
        var value = Guid.NewGuid().ToString("N");
        var deadline = TimeProvider.System.GetUtcNow() + wait;

        while (TimeProvider.System.GetUtcNow() < deadline)
        {
            ct.ThrowIfCancellationRequested();

            // ★ SET key value NX PX ms — ذرّي: إنشاء + انتهاء صلاحية في أمر واحد
            var acquired = await db.StringSetAsync($"lock:{key}", value, lease, When.NotExists);
            if (acquired)
            {
                // fencing token متزايد: يحمي من «قفل انتهى وأنت لسه شغال»
                var fence = await db.StringIncrementAsync($"fence:{key}");
                return new RedisLock(db, key, value, fence, lease, ReleaseScript, log);
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100), ct);
        }

        return null;                                     // ما قدرتش خلال المهلة
    }

    private sealed class RedisLock(
        IDatabase db, string key, string value, long fence, TimeSpan lease,
        string releaseScript, ILogger log) : IDistributedLock
    {
        public string Key => key;
        public long FenceToken => fence;
        public bool Acquired { get; private set; } = true;

        public async ValueTask DisposeAsync()
        {
            try
            {
                var released = (int)await db.ScriptEvaluateAsync(releaseScript, new
                {
                    key = $"lock:{key}",
                    value = (RedisValue)value,
                });

                if (released == 0)
                {
                    // ★ القفل انتهى قبل ما تخلص شغلك → عملك ممكن يتعارض مع قفل تاني
                    log.LogWarning("lock {Key} expired before release (lease={Lease}) — check work duration", key, lease);
                }
                Acquired = false;
            }
            catch (RedisException ex) { log.LogError(ex, "failed releasing lock {Key}", key); }
        }
    }
}

// الاستخدام الصحيح: القفل قصير، والمورد المحمي يفحص الـfence token
public sealed class ReportGenerator(IDistributedLockFactory locks, AppDbContext db)
{
    public async Task<bool> GenerateAsync(DateOnly day, CancellationToken ct)
    {
        await using var gate = await locks.TryAcquireAsync(
            $"report:{day:yyyy-MM-dd}", lease: TimeSpan.FromSeconds(30), wait: TimeSpan.FromSeconds(2), ct);

        if (gate is null) return false;                       // حد تاني بيولّده

        // ★ لو المهمة ممكن تتجاوز مدة الإيجار: جدّد الإيجار (watchdog) أو قلّل النطاق
        // ★ والمورد الحساس (كتابة النتيجة) يتحقق إن fence token الحالي ≥ token العملية
        await WriteReportAsync(day, gate.FenceToken, ct);
        return true;
    }

    private Task WriteReportAsync(DateOnly day, long fence, CancellationToken ct) => Task.CompletedTask;
}
'''},
            {"type": "callout", "kind": "danger", "title": "الحقيقة عن الأقفال الموزّعة في Redis",
             "md": """
قفل Redis (حتى Redlock) **ليس ضمانًا مطلقًا**: لو توقفت العملية (GC pause طويل، VM migration) بعد أخذ القفل
وقبل إنهاء الشغل، عملية تانية ممكن تاخد نفس القفل → تنفيذ متزامن.

- **Fencing token** هو الحل العملي: المورد المحمي (جدول/خدمة) بيرفض أي عملية بـtoken أقدم من آخر token نُفّذ.
- **لو الصوابية حرجة** (مدفوعات، مخزون، فواتير): استخدم **قفل في قاعدة البيانات** —
  `pg_advisory_lock` (درس BackgroundService) أو قيد فريد/`SELECT … FOR UPDATE`. أقوى وأبسط لأن المصدر نفسه هو الحكم.
- **لا تمسك قفلًا لعمل طويل**: جدّد الإيجار (watchdog) أو جزّئ الشغل.
- **احترم مدة الانتظار**: `TryAcquire` بمهلة + فشل واضح أفضل من طابور صامت.
"""},
            {"type": "heading", "level": 2, "text": "طوابير خفيفة: Lists مقابل Streams مقابل Pub/Sub"},
            {"type": "table", "head": ["الآلية", "الدوام", "التسليم", "أنسب حالة", "متى تتركها"], "rows": [
                ["Pub/Sub", "✗", "بلا ضمان (غير المتصل يفقد)", "إشارات/إبطال كاش/بث لحظي", "أي حدث يجب ألا يُفقد"],
                ["Lists (`LPUSH`/`BRPOP`)", "✓ (بينما في الذاكرة)", "مرة واحدة، بلا ACK", "طوابير عمل بسيطة داخلية", "لو محتاج إعادة تسليم/مستهلكين متعددين منظمين"],
                ["**Streams** (`XADD`/`XREADGROUP`)", "✓ + سجل", "مجموعات مستهلكين + ACK + pending", "طابور جاد بخفة Redis", "لو محتاج routing معقد/أولويات/DLQ غني → RabbitMQ/Service Bus"],
                ["Sorted Sets (تأخير/جدولة)", "✓", "يدوي (فحص دوري)", "مهام مؤجلة، rate limiting", "حجوم كبيرة → وسيط حقيقي"],
            ]},
            {"type": "code", "lang": "csharp", "title": "Streams: منتج + مجموعة مستهلكين + ACK + معالجة المعلق", "code": r'''
public sealed class RedisStreamWorker(
    IConnectionMultiplexer redis, IServiceScopeFactory scopeFactory, ILogger<RedisStreamWorker> log)
    : BackgroundService
{
    private const string Stream = "shop:jobs";
    private const string Group = "workers";
    private readonly string _consumer = $"api-{Environment.MachineName}-{Environment.ProcessId}";

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var db = redis.GetDatabase();

        // أنشئ المجموعة مرة واحدة (idempotent: BUSYGROUP = موجودة بالفعل)
        try { await db.StreamCreateConsumerGroupAsync(Stream, Group, createStream: true); }
        catch (RedisServerException ex) when (ex.Message.Contains("BUSYGROUP")) { /* موجودة */ }

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                // ① عالج الرسائل المعلقة أولًا (من مستهلك مات) —Claim/Pending
                await RetryPendingAsync(db, stoppingToken);

                // ② اقرأ رسائل جديدة
                var entries = await db.StreamReadGroupAsync(
                    Stream, Group, _consumer, count: 10, noAck: false);

                if (entries is null || entries.Length == 0)
                {
                    await Task.Delay(250, stoppingToken);        // لا تدوير ساخن (busy loop)
                    continue;
                }

                foreach (var entry in entries)
                {
                    try
                    {
                        await using var scope = scopeFactory.CreateAsyncScope();
                        var handler = scope.ServiceProvider.GetRequiredService<IJobHandler>();
                        await handler.HandleAsync(entry.Values.ToDictionary(n => n.Name.ToString(), n => n.Value.ToString()),
                                                  stoppingToken);

                        await db.StreamAcknowledgeAsync(Stream, Group, entry.Id);    // ✓ ACK بعد النجاح
                    }
                    catch (Exception ex) when (ex is not OperationCanceledException)
                    {
                        // لا ACK → الرسالة تفضل pending وتُعاد معالجتها (idempotency ضرورية!)
                        log.LogError(ex, "job {EntryId} failed; left pending for retry", entry.Id.ToString());
                    }
                }
            }
            catch (OperationCanceledException) { break; }
            catch (RedisException ex)
            {
                log.LogError(ex, "redis stream read failed; backing off");
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
        }
    }

    private async Task RetryPendingAsync(IDatabase db, CancellationToken ct)
    {
        var pending = await db.StreamPendingMessagesAsync(Stream, Group, count: 20, _consumer);
        foreach (var p in pending.Where(p => p.DeliveryCount > 3))
        {
            // بعد N محاولات: انقلها لطابور dead-letter بدل الدوران اللانهائي
            await db.StreamAddAsync("shop:jobs:dlq", "originalId", p.MessageId.ToString());
            await db.StreamAcknowledgeAsync(Stream, Group, p.MessageId);
            log.LogWarning("moved {MessageId} to DLQ after {Count} deliveries", p.MessageId, p.DeliveryCount);
        }
    }
}

public interface IJobHandler
{
    Task HandleAsync(Dictionary<string, string> payload, CancellationToken ct);
}
'''},
            {"type": "heading", "level": 2, "text": "استخدامات تانية مفيدة"},
            {"type": "code", "lang": "csharp", "title": "عدّادات، rate limiting، ومهام مؤجلة", "code": r'''
// ① عدّاد بفترة انتهاء (مثال: حد API بسيط مشترك بين النسخ)
public async Task<bool> TryIncrementAsync(string key, int limit, TimeSpan window, CancellationToken ct)
{
    var db = redis.GetDatabase();
    var count = await db.StringIncrementAsync(key);
    if (count == 1) await db.KeyExpireAsync(key, window);      // أول ضربة تحدد النافذة
    return count <= limit;
}

// ② نافذة منزلقة بـSorted Set (أدق من العداد الثابت)
public async Task<bool> AllowAsync(string key, int limit, TimeSpan window, CancellationToken ct)
{
    var db = redis.GetDatabase();
    var now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    var batch = db.CreateBatch();

    batch.KeySortedSetRemoveRangeByScoreAsync(key, 0, now - (long)window.TotalMilliseconds);
    batch.SortedSetAddAsync(key, $"{now}:{Guid.NewGuid():N}", now);
    batch.KeyExpireAsync(key, window);
    batch.Execute();

    var count = await db.SortedSetLengthAsync(key);
    return count <= limit;
}

// ③ مهمة مؤجلة (delayed job) بـSorted Set — بديل خفيف لجدولة كاملة
public async Task ScheduleAsync(string payload, DateTimeOffset runAt, CancellationToken ct) =>
    await redis.GetDatabase().SortedSetAddAsync("shop:delayed", payload, runAt.ToUnixTimeMilliseconds());

// والعامل: XCLAIM/XREAD… ببساطة اقرأ ما استحق
public async Task<IReadOnlyList<string>> DueAsync(CancellationToken ct)
{
    var now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    var due = await redis.GetDatabase().SortedSetRangeByScoreAsync("shop:delayed", double.NegativeInfinity, now);
    foreach (var item in due) await redis.GetDatabase().SortedSetRemoveAsync("shop:delayed", item);
    return due.Select(v => v.ToString()).ToList();
}
'''},
            {"type": "checkpoints", "items": [
                "أضبط Redis بـmultiplexer واحد وtimeouts و`AbortOnConnectFail=false` وفشل مفتوح للكاش.",
                "أنفّذ cache-aside بـTTL وقيم صغيرة وقياس hit/miss، وأبطل بطرق مقصودة (إصدار/وسوم/pub-sub).",
                "أفهم حدود القفل الموزّع وأستخدم fencing token، وألجأ لقفل القاعدة لما الصوابية حرجة.",
                "أختار بين Lists/Streams/Pub-Sub بحسب الدوام والتسليم، وأعرف متى أنتقل لوسيط رسائل حقيقي.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه `ConnectionMultiplexer` لازم يكون singleton؟",
                 "options": [
                     "متطلب ترجمة",
                     "كل واحد يفتح مجموعة اتصالات خاصة → استنزاف اتصالات Redis وذاكرة؛ المكتبة thread-safe وتدير الاتصالات داخليًا",
                     "أسرع في التسلسل",
                     "يمنع الأقفال",
                 ], "answer": 1,
                 "explain": "خطأ شائع: إنشاء multiplexer لكل طلب/عملية. واحد للتطبيق (أو واحد لكل إعداد مختلف)."},
                {"q": "`maxmemory-policy` = `noeviction` والذاكرة امتلت. إيه اللي هيحصل؟",
                 "options": [
                     "Redis يحذف أقدم المفاتيح",
                     "كل أوامر الكتابة تفشل بـOOM — بما فيها أقفالك وطوابيرك",
                     "يتباطأ فقط",
                     "يعيد التشغيل",
                 ], "answer": 1,
                 "explain": "للكاش الخالص استخدم `allkeys-lru`/`volatile-lru` + TTL على كل مفتاح. ولو Redis مشترك مع طوابير/أقفال: افصله في instance مختلف."},
                {"q": "أخذت قفل Redis، وشغلك اتأخر (GC pause) وانتهى الإيجار، وعملية تانية أخذت القفل. النتيجة؟",
                 "options": [
                     "لا شيء — القفل يحميك",
                     "تنفيذ متزامن لنفس العمل الحرج؛ الحماية الحقيقية: fencing token يفحصه المورد المحمي",
                     "Redis يرمي استثناء",
                     "القفل يتجدد تلقائيًا",
                 ], "answer": 1,
                 "explain": "ده جوهر نقد Redlock. الحل: token متزايد + رفض العمليات الأقدم عند المورد، أو استخدم قفل قاعدة البيانات."},
                {"q": "Pub/Sub مناسب لإيه بالظبط؟",
                 "options": [
                     "طابور مهام حرجة",
                     "إشارات لحظية لا يضر فقدانها (إبطال كاش، إشعارات، بث تحديثات)",
                     "تخزين دائم",
                     "تسليم مضمون بين الخدمات",
                 ], "answer": 1,
                 "explain": "بلا دوام وبلا ضمان تسليم: المشترك غير المتصل يفقد الرسالة. للأحداث الحرجة استخدم Streams أو وسيط رسائل."},
                {"q": "`KEYS pattern*` في الإنتاج — ليه ممنوع؟",
                 "options": [
                     "غير مدعوم",
                     "يحجب خادم Redis (أحادي الخيط) أثناء فحص كل المفاتيح → تجميد لكل العملاء؛ استخدم `SCAN`",
                     "يرجع نتائج خاطئة",
                     "يستهلك ذاكرة",
                 ], "answer": 1,
                 "explain": "`SCAN`/`KeysAsync` يتصفح تدريجيًا بلا حجب. ولو محتاج إبطال جماعي متكرر: صمّم بمفاتيح إصدار أو وسوم بدل المطاردة."},
                {"q": "Redis واقع بالكامل — سلوك الـAPI المطلوب؟",
                 "options": [
                     "500 لكل الطلبات",
                     "فشل مفتوح: اخدم من المصدر (مع تحميل أعلى) وسجّل ونبّه، ولا تُفشل الطلبات",
                     "أعد التشغيل",
                     "ارجع بيانات فارغة",
                 ], "answer": 1,
                 "explain": "الكاش تحسين مش اعتماد. `AbortOnConnectFail=false` + `try/catch RedisException` + metric للخطأ = تصميم صحيح."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "Redis في مشروعك (بأمان)",
                 "md": "شغّل Redis بـTestcontainers، وطبّق HybridCache أو `RedisCacheService` على مسار قراءة ساخن، مع TTL ومفاتيح منظمة وإبطال بعد الكتابة وقياس hit/miss. أثبت إن سقوط Redis لا يُفشل الطلبات.",
                 "criteria": [
                     "multiplexer واحد singleton + timeouts مضبوطة + `AbortOnConnectFail=false`",
                     "كل مفتاح له TTL واسم منظم (`app:domain:key`)",
                     "إبطال مقصود بعد كل كتابة مؤثرة (اختبار يثبت القراءة الجديدة)",
                     "نسبة إصابة و`cache.errors` منشورة كـmetrics",
                     "اختبار: إيقاف حاوية Redis → الطلبات تنجح (من المصدر) مع تحذير في اللوج",
                     "لا قيم > 100KB (سجّل أكبر قيمة)",
                 ],
                 "hint": "لو القراءات أبطأ بعد إضافة الكاش: غالبًا القيمة كبيرة أو التسلسل مكلف — خزّن projection أصغر، وقِس تكلفة `Serialize/Deserialize` مقابل تكلفة الاستعلام."},
                {"id": "t2", "title": "قفل موزّع أو طابور",
                 "md": "اختار واحدة: (أ) قفل Redis بـfencing token يمنع تكرار توليد تقرير يومي، أو (ب) طابور Redis Streams بمجموعة مستهلكين + ACK + DLQ لمهمة خلفية. نفّذها واختبر الحالات الحرجة.",
                 "criteria": [
                     "(أ) اختباران متزامنان → تنفيذ واحد فقط، وتحرير القفل ذرّي بـLua، وسجل تحذيري لو انتهت مدة الإيجار",
                     "(ب) فشل معالج → الرسالة تبقى pending وتُعاد، وبعد N محاولات → DLQ",
                     "قرار مكتوب: هل القفل/الطابور ده كافٍ لو الصوابية حرجة؟ (ولماذا لا تنتقل لـRabbitMQ)",
                     "idempotency في المعالج (إعادة التسليم لا تكرر الأثر)",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Redis documentation", "url": "https://redis.io/docs/latest/"},
                {"label": "StackExchange.Redis basics", "url": "https://stackexchange.github.io/StackExchange.Redis/Basics"},
                {"label": "Distributed caching in ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/distributed"},
                {"label": "Redis Streams", "url": "https://redis.io/docs/latest/develop/data-types/streams/"},
                {"label": "How to do distributed locking (Kleppmann)", "url": "https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html"},
                {"label": "Redis persistence (RDB/AOF)", "url": "https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s3-m3-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
«نستخدم MongoDB لأن مفيش schema» — دي أشهر حجة وأغلب الوقت سبب لمشاكل بعدين.
الـNoSQL مش «أحدث فإذن أفضل»؛ ده **نموذج بيانات مختلف** بيبدّل مقايضات: مرونة في الشكل وقابلية توسع أفقية،
مقابل ضعف في الانضمّامات والاستعلامات العابرة للأغريغات والقيود.

الدرس ده: نمذجة مستندية صحيحة (embed مقابل reference)، **partition keys في Cosmos DB** (القرار الأغلى)،
مستويات الاتساق، وجدول قرار واضح: إمتى SQL وإمتى NoSQL — وليه في أغلب مشاريع .NET الإجابة «الاتنين».
"""},
            {"type": "terms", "items": [
                {"term": "Aggregate", "def": "وحدة اتساق في النمذجة المستندية: تُقرأ وتُكتب ككل (طلب + سطوره). حدودها تحدد ما يُدمج وما يُفصل."},
                {"term": "Embed (دمج)", "def": "تخزين البيانات المرتبطة داخل المستند → قراءة واحدة سريعة؛ مخاطره: تكرار ونمو غير محدود."},
                {"term": "Reference (إسناد)", "def": "تخزين معرّف فقط → بلا تكرار؛ ثمنه: أكثر من قراءة أو `$lookup` (أبطأ من join علائقي)."},
                {"term": "Document size limit", "def": "MongoDB: 16MB للمستند. مصفوفة بلا حدود (logs/comments) = قنبلة موقوتة."},
                {"term": "Write amplification", "def": "تعديل مدمج صغير يعيد كتابة مستند كبير → تكلفة كتابة وذاكرة أعلى."},
                {"term": "Partition Key (Cosmos)", "def": "الحقل اللي يحدد التقسيم الفيزيائي. بيقرر أداء الاستعلامات والتكلفة وقابلية التوسع — **أصعب قرار وأصعب تغيير**."},
                {"term": "Hot Partition", "def": "تقسيم يستقبل أغلب الحمل (مثل تاريخ أو مستأجر ضخم) → اختناق رغم سعة إجمالية فائضة."},
                {"term": "RU/s", "def": "وحدة تكلفة Cosmos: كل عملية تستهلك Request Units بحسب الحجم والتعقيد. استعلام عبر أقسام = تكلفة مضاعفة."},
                {"term": "Consistency Levels", "def": "5 مستويات في Cosmos: Strong → Bounded Staleness → **Session (الافتراضي)** → Consistent Prefix → Eventual."},
                {"term": "Change Feed", "def": "تدفّق تغييرات من Cosmos (أو MongoDB Change Streams) → أساس الـCDC وبناء read models."},
                {"term": "Polyglot Persistence", "def": "استخدام أكثر من مخزن بحسب المهمة: SQL مصدر الحقيقة، والمستندية/البحث/الكاش لقراءات معينة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) جدول القرار: SQL ولا NoSQL؟"},
            {"type": "table", "head": ["المتطلب", "SQL (Postgres/SQL Server)", "MongoDB", "Cosmos DB"], "rows": [
                ["علاقات كثيرة-إلى-كثير واستعلامات عابرة", "✓ الأفضل", "✗ `$lookup` مكلف", "✗ joins غير مدعومة فعليًا"],
                ["معاملات عبر أغريغات", "✓ قوية ونافذة", "△ (4.0+ replica set، مكلفة)", "△ داخل قسم منطقي واحد"],
                ["قيود فريدة/مفاتيح أجنبية", "✓ مدمجة", "△ فريد على مستوى المستند/الفهرس", "△ محدود (unique على نفس partition key)"],
                ["مخطط مرن/متغير بسرعة", "△ (migrations)", "✓", "✓"],
                ["بيانات هرمية تُقرأ كوحدة", "△ (عدة جداول/joins)", "✓ مثالي", "✓ مثالي"],
                ["كتابة بحجم ضخم + توسع أفقي", "△ (sharding معقد)", "✓", "✓✓ (مصمم له)"],
                ["تقارير/تحليلات ad-hoc", "✓ الأفضل", "△ aggregation pipeline", "△ (أو Synapse/Fabric)"],
                ["كمون منخفض عالميًا", "△", "△", "✓ (توزيع جغرافي)"],
                ["تكلفة تشغيلية", "منخفضة/معروفة", "متوسطة", "بحسب RU/s — قد تفاجئك"],
                ["فريق .NET + EF Core", "✓ ناضج تمامًا", "△ (driver + provider رسمي حديث)", "△ (SDK بلا ORM ناضج)"],
            ]},
            {"type": "callout", "kind": "tip", "title": "القرار الواقعي في أغلب مشاريع .NET",
             "md": """
**Postgres/SQL Server كمصدر الحقيقة** (معاملات، قيود، علاقات، تقارير) +
**مخازن متخصصة للقراءات**: Redis للكاش، Elasticsearch/OpenSearch للبحث النصي،
MongoDB/Cosmos لسجلات الأحداث أو كتالوجات مرنة أو بيانات تسلسلية ضخمة.

ابدأ بـSQL **دائمًا** إلا لو عندك دليل: حجم بيانات/معدل كتابة/مرونة مخطط **تفرض** غير ذلك.
«ممكن نحتاج نتوسع» ليست سببًا — التوسع الرأسي بيوصّل لملايين الطلبات يوميًا.
"""},
            {"type": "heading", "level": 2, "text": "2) MongoDB: النمذجة والـdriver"},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Catalog package MongoDB.Driver
dotnet add Shop.Infrastructure package Microsoft.Azure.Cosmos
dotnet add Shop.Api package StackExchange.Redis
# provider EF Core رسمي من MongoDB (حالة النضج تتطور — تحقق من التوثيق قبل الاعتماد في الإنتاج)
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Catalog/Documents.cs", "title": "نمذجة: embed لما يُقرأ معًا، reference لما ينمو بلا حدود", "code": r'''
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

/// <summary>
/// ✓ embed: مراجعات المنتج تُقرأ دائمًا مع صفحة المنتج (حجم محدود).
/// ✗ لا تُدمج سجلات بلا حدود (أحداث، رسائل) — انفصلها في مجموعة خاصة.
/// </summary>
public sealed class ProductDocument
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string Id { get; init; } = default!;

    [BsonElement("sku")] public required string Sku { get; init; }
    [BsonElement("name")] public required string Name { get; init; }
    [BsonElement("slug")] public required string Slug { get; init; }

    // ✓ embed: سمات مرنة تختلف بين الفئات (السبب الحقيقي لاختيار مستندية)
    [BsonElement("attributes")] public Dictionary<string, object> Attributes { get; init; } = [];

    // ✓ embed: قيمة مركّبة صغيرة
    [BsonElement("price")] public PriceDocument Price { get; init; } = default!;

    // ✓ embed مع حد صريح (آخر 20 مراجعة فقط) — لا نمو غير محدود
    [BsonElement("top_reviews")] public List<ReviewEmbed> TopReviews { get; init; } = [];

    // ✗ reference: الفئة كيان له حياة مستقلة ويُستخدم في قوائم/فلاتر كتير
    [BsonElement("category_id")] public required string CategoryId { get; init; }

    [BsonElement("tags")] public List<string> Tags { get; init; } = [];
    [BsonElement("schema_version")] public int SchemaVersion { get; init; } = 2;   // ★ لإدارة تطور المخطط
    [BsonElement("updated_at")] public DateTimeOffset UpdatedAt { get; init; }
}

public sealed record PriceDocument(
    [property: BsonElement("amount")] decimal Amount,
    [property: BsonElement("currency")] string Currency);

public sealed record ReviewEmbed(
    [property: BsonElement("author")] string Author,
    [property: BsonElement("rating")] int Rating,
    [property: BsonElement("excerpt")] string Excerpt,
    [property: BsonElement("at")] DateTimeOffset At);

/// <summary>مجموعة منفصلة للسجلات بلا حدود — مرتبطة بمعرّف المنتج.</summary>
public sealed class ProductEventDocument
{
    [BsonId][BsonRepresentation(BsonType.ObjectId)] public string Id { get; init; } = default!;
    [BsonElement("product_id")] public required string ProductId { get; init; }
    [BsonElement("type")] public required string Type { get; init; }
    [BsonElement("payload")] public BsonDocument Payload { get; init; } = new();
    [BsonElement("at")] public DateTimeOffset At { get; init; }
    [BsonElement("expires_at")] public DateTimeOffset? ExpiresAt { get; init; }     // TTL index يحذفها تلقائيًا
}
'''},
            {"type": "table", "head": ["القرار", "Embed", "Reference", "معيار الحسم"], "rows": [
                ["سطور الطلب داخل مستند الطلب", "✓", "", "تُقرأ وتُكتب دائمًا معًا (aggregate واحد)"],
                ["العميل داخل مستند الطلب", "", "✓", "كيان مستقل، يُعدَّل، ويُستخدم في أماكن كثيرة"],
                ["مراجعات المنتج", "جزئيًا (آخر 20)", "✓ (كلها)", "الحجم: غير محدود → مجموعة منفصلة"],
                ["الفئة/القسم", "", "✓", "يتغير مستقلًا ويُفلتر به في قوائم"],
                ["سجل أحداث/تدقيق", "", "✓ + TTL index", "نمو بلا حدود داخل مستند = كارثة"],
                ["عنوان الشحن للطلب", "✓", "", "لقطة تاريخية لا يجب أن تتغير"],
                ["الصور/الملفات", "", "✓ (GridFS/S3/blob)", "لا تخزّن ثنائيات داخل المستندات"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "Shop.Catalog/MongoCatalogStore.cs", "title": "الـdriver: فهارس صريحة + استعلامات آمنة + إسقاطات", "code": r'''
using MongoDB.Driver;

public sealed class MongoCatalogStore(IConfiguration config, ILogger<MongoCatalogStore> log) : ICatalogStore
{
    private readonly MongoClient _client = new(config.GetConnectionString("Mongo"));
    private IMongoCollection<ProductDocument> Products =>
        _client.GetDatabase("shop").GetCollection<ProductDocument>("products");

    /// <summary>
    /// ★ الفهارس كود (تُطبَّق عند الإقلاع/في migration داخلي) — مش إضافة يدوية على قاعدة الإنتاج.
    /// </summary>
    public async Task EnsureIndexesAsync(CancellationToken ct)
    {
        var builder = Builders<ProductDocument>.IndexKeys;

        await Products.Indexes.CreateManyAsync(
        [
            new CreateIndexModel<ProductDocument>(builder.Ascending(p => p.Sku),
                new CreateIndexOptions { Unique = true, Name = "ux_sku" }),
            new CreateIndexModel<ProductDocument>(builder.Ascending(p => p.CategoryId).Descending(p => p.UpdatedAt),
                new CreateIndexOptions { Name = "ix_category_updated" }),           // فهرس مركّب لنمط الاستعلام
            new CreateIndexModel<ProductDocument>(builder.Text(p => p.Name),
                new CreateIndexOptions { Name = "tx_name" }),
            new CreateIndexModel<ProductDocument>(builder.Ascending(p => p.Tags),
                new CreateIndexOptions { Name = "ix_tags" }),                        // multikey
        ], cancellationToken: ct);

        log.LogInformation("mongo indexes ensured");
    }

    /// <summary>قراءة بفلترة وترقيم — FilterDefinition تبني استعلامًا آمنًا (لا دمج نصوص).</summary>
    public async Task<IReadOnlyList<ProductDocument>> SearchAsync(
        string? text, string? categoryId, IReadOnlyList<string>? tags,
        int page, int size, CancellationToken ct)
    {
        var filter = Builders<ProductDocument>.Filter.Empty;

        if (!string.IsNullOrWhiteSpace(categoryId))
            filter &= Builders<ProductDocument>.Filter.Eq(p => p.CategoryId, categoryId);

        if (tags is { Count: > 0 })
            filter &= Builders<ProductDocument>.Filter.All(p => p.Tags, tags);

        if (!string.IsNullOrWhiteSpace(text))
            filter &= Builders<ProductDocument>.Filter.Text(text);

        var projection = Builders<ProductDocument>.Projection
            .Exclude(p => p.TopReviews)                       // ✓ إسقاط: لا تجلب ما لا يُعرض
            .Exclude(p => p.Attributes);

        return await Products
            .Find(filter)
            .Project<ProductDocument>(projection)
            .SortByDescending(p => p.UpdatedAt)
            .Skip(Math.Max(0, (page - 1)) * Math.Clamp(size, 1, 100))
            .Limit(Math.Clamp(size, 1, 100))
            .ToListAsync(ct);
    }

    /// <summary>upsert ذرّي — بلا «اقرأ ثم احفظ» (سباق).</summary>
    public async Task UpsertAsync(ProductDocument doc, CancellationToken ct)
    {
        var filter = Builders<ProductDocument>.Filter.Eq(p => p.Sku, doc.Sku);
        await Products.ReplaceOneAsync(filter, doc, new ReplaceOptions { IsUpsert = true }, ct);
    }

    /// <summary>تحديث جزئي (بلا إعادة كتابة المستند كاملًا).</summary>
    public async Task SetPriceAsync(string sku, decimal amount, string currency, CancellationToken ct)
    {
        var update = Builders<ProductDocument>.Update
            .Set(p => p.Price, new PriceDocument(amount, currency))
            .Set(p => p.UpdatedAt, DateTimeOffset.UtcNow);

        var result = await Products.UpdateOneAsync(
            Builders<ProductDocument>.Filter.Eq(p => p.Sku, sku), update, cancellationToken: ct);

        if (result.MatchedCount == 0) throw new NotFoundException("Product", sku);
    }

    /// <summary>تجميع: أنبوبة aggregation (مكافئ GROUP BY) — الأقوى في المستندية.</summary>
    public async Task<IReadOnlyList<CategoryStat>> StatsByCategoryAsync(CancellationToken ct) =>
        await Products.Aggregate()
            .Group(p => p.CategoryId, g => new CategoryStat(g.Key, g.Count(), g.Average(p => p.Price.Amount)))
            .SortByDescending(s => s.Products)
            .Limit(20)
            .ToListAsync(ct);

    public sealed record CategoryStat(string CategoryId, int Products, decimal AvgPrice);
}
'''},
            {"type": "callout", "kind": "warn", "title": "أخطاء MongoDB الكلاسيكية",
             "md": """
- **مصفوفة بلا حدود داخل مستند** (كل التعليقات/الأحداث) → المستند بيكبر لحد 16MB والكتابة بتبطيء بشكل كارثي. افصلها في مجموعة.
- **بلا فهارس** → كل استعلام `COLLSCAN`. افحص بـ`explain("executionStats")` وتأكد من `IXSCAN`.
- **`$lookup` كبديل join في كل مكان** → أداء سيئ وتصميم خاطئ؛ لو محتاج joins كتير، استخدم SQL.
- **دمج بيانات بتتغير كتير** (سعر، مخزون) → تكرار وعدم اتساق. استخدم reference أو حدث تغيير عبر Change Streams.
- **لا خطة لتطور المخطط** → أضف `schema_version` في كل مستند ومهاجر (migration task) يحدّث تدريجيًا، أو اقرأ بطريقة متسامحة.
- **كتابة بلا `WriteConcern` مقصود** → الافتراضي قد لا يضمن الدوام؛ للعمليات الحرجة استخدم `w: "majority"` و`journal: true`.
- **تخزين ثنائيات (صور/PDF) في المستندات** → استخدم GridFS أو object storage.
"""},
            {"type": "heading", "level": 2, "text": "3) Cosmos DB: partition key هو القرار كله"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/Cosmos/OrderContainer.cs", "title": "اختيار partition key + استعلامات داخل القسم", "code": r'''
using Microsoft.Azure.Cosmos;

public sealed class CosmosOrderStore(CosmosClient client) : IOrderStore
{
    private Container Orders => client.GetContainer("shop", "orders");

    /// <summary>
    /// ★ partition key = customerId:
    ///   • كل استعلامات العميل داخل قسم واحد → RU أقل وزمن ثابت
    ///   • معاملات عبر عناصر نفس العميل ممكنة (transactional batch)
    ///   • توزيع متساوٍ (عدد عملاء كبير) → لا hot partition
    ///
    /// ✗ اختيارات سيئة شائعة:
    ///   • orderDate → كل كتابات اليوم على قسم واحد (hot partition)
    ///   • country → أقسام قليلة وضخمة (توزيع غير متساوٍ)
    ///   • id → توزيع ممتاز لكن كل استعلامات «طلبات عميل» تصير cross-partition (مكلفة)
    /// </summary>
    public async Task<IReadOnlyList<OrderDto>> ListForCustomerAsync(
        Guid customerId, int size, CancellationToken ct)
    {
        var pk = new PartitionKey(customerId.ToString());

        var query = new QueryDefinition(
            "SELECT TOP @size o.id, o.status, o.total, o.createdAt FROM o ORDER BY o.createdAt DESC")
            .WithParameter("@size", Math.Clamp(size, 1, 100));          // ✓ parameters دائمًا

        // ✓ تمرير partitionKey: يحوّل الاستعلام من cross-partition لـsingle-partition (فرق تكلفة كبير)
        using var iterator = Orders.GetItemQueryIterator<OrderDto>(query, requestOptions:
            new QueryRequestOptions { PartitionKey = pk, MaxItemCount = size });

        var results = new List<OrderDto>();
        while (iterator.HasMoreResults) results.AddRange(await iterator.ReadNextAsync(ct));
        return results;
    }

    /// <summary>قراءة عنصر بمعرّف + partition key = أرخص عملية في Cosmos (نقطة قراءة).</summary>
    public async Task<OrderDto?> GetAsync(Guid customerId, Guid orderId, CancellationToken ct)
    {
        try
        {
            return await Orders.ReadItemAsync<OrderDto>(
                orderId.ToString(), new PartitionKey(customerId.ToString()), cancellationToken: ct);
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    /// <summary>عمليات ذرّية داخل نفس القسم (بديل المعاملات العابرة).</summary>
    public async Task AddOrderWithAuditAsync(Guid customerId, OrderDto order, AuditEntry audit, CancellationToken ct)
    {
        var batch = Orders.CreateTransactionalBatch(new PartitionKey(customerId.ToString()))
            .CreateItem(order)
            .CreateItem(audit);

        using var response = await batch.ExecuteAsync(ct);
        response.EnsureSuccessStatusCode();
    }

    /// <summary>Change Feed: أساس بناء read models / مزامنة مع SQL.</summary>
    public async Task StreamChangesAsync(Func<OrderDto, CancellationToken, Task> handle, CancellationToken ct)
    {
        var processor = Orders.GetChangeFeedProcessorBuilder<OrderDto>(
            "orders-sync", (changes, token) => Task.WhenAll(changes.Select(c => handle(c, token))))
            .WithInstanceName($"{Environment.MachineName}-{Environment.ProcessId}")
            .WithLeaseContainer(client.GetContainer("shop", "leases"))
            .Build();

        await processor.StartAsync();
        ct.Register(async () => await processor.StopAsync());
    }
}
'''},
            {"type": "table", "head": ["مستوى الاتساق", "الضمان", "التكلفة/الكمون", "إمتى"], "rows": [
                ["Strong", "كل القراءات ترى آخر التزام", "الأعلى (زمن + RU)", "مال/مخزون حيث الاتساق أهم من التوفر"],
                ["Bounded Staleness", "تأخر محدود (زمن أو عدد إصدارات)", "متوسطة", "مزامنة بين مناطق مع ضمانات معقولة"],
                ["**Session** (الافتراضي)", "اتساق داخل جلسة المستخدم نفسه", "منخفضة", "★ أغلب التطبيقات: المستخدم يشوف كتاباته"],
                ["Consistent Prefix", "لا ترى ترتيبًا مخلوطًا (لا قفزات للوراء)", "أقل", "تحليلات/سجلات مرتبة"],
                ["Eventual", "بلا ضمان ترتيب", "الأرخص", "عدادات، توصيات، بيانات قابلة للتقارب"],
            ]},
            {"type": "callout", "kind": "note", "title": "تكلفة Cosmos: RU/s مش «عدد الطلبات»",
             "md": """
- **قراءة نقطة** (id + partition key) ≈ 1 RU لمستند 1KB. **استعلام cross-partition** = مئات/آلاف RU.
- **حجم المستند** بيضاعف التكلفة: خزّن projection لا كائن ضخم، وتجنّب الحقول غير المستخدمة.
- **الفهارس**: سياسة الفهرسة الافتراضية تفهرس كل المسارات → تكلفة كتابة أعلى. قيّدها (`indexingPolicy` بـ`excludedPaths`).
- **التصميم أولًا ثم التكلفة**: اختيار partition key غلط ما يتصلحش بضبط RU — يحتاج إعادة تصميم وترحيل بيانات.
- **قيس بـ`RequestCharge`**: `response.RequestCharge` بيرجعلك التكلفة لكل نداء → سجّلها كـmetric.
"""},
            {"type": "heading", "level": 2, "text": "4) Polyglot: SQL مصدر الحقيقة + مخازن متخصصة"},
            {"type": "code", "lang": "csharp", "title": "نمط عملي: write model في Postgres، read models في مخازن متخصصة", "code": r'''
// ① الكتابة: SQL فقط (معاملات، قيود، قواعد عمل)
public async Task<Guid> CreateOrderAsync(CreateOrderCommand cmd, CancellationToken ct)
{
    await using var tx = await db.Database.BeginTransactionAsync(ct);
    var order = await orders.CreateAsync(cmd, ct);                   // Postgres
    db.OutboxMessages.Add(OutboxMessage.Of("order.created", order)); // ✓ outbox في نفس المعاملة
    await db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
    return order.Id;
}

// ② المزامنة: عامل outbox ينشر الأحداث (at-least-once)
public sealed class OutboxDispatcher(AppDbContext db, IEventPublisher publisher) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var batch = await db.OutboxMessages
                .Where(m => m.SentAt == null)
                .OrderBy(m => m.CreatedAt)
                .Take(50).ToListAsync(stoppingToken);

            foreach (var message in batch)
            {
                await publisher.PublishAsync(message.Type, message.Payload, stoppingToken);
                message.SentAt = DateTimeOffset.UtcNow;               // idempotent على المستهلك
            }
            await db.SaveChangesAsync(stoppingToken);
            await Task.Delay(200, stoppingToken);
        }
    }
}

// ③ المستهلكون يبنون read models متخصصة (كل واحد لمهمته)
public sealed class CatalogProjectionHandlers(ICatalogStore mongo, ISearchIndexer search, IRedisCacheService cache)
{
    public async Task On(OrderCreated order, CancellationToken ct)
    {
        await mongo.UpsertAsync(order.ToProductDocument(), ct);        // MongoDB: كتالوج مرن + سمات
        await search.IndexAsync(order.ToSearchDoc(), ct);              // OpenSearch: بحث نصي سريع
        await cache.InvalidateAsync($"shop:catalog:list", ct);         // Redis: إبطال القوائم
    }
}

// ④ القراءة: أنسب مخزن لكل استعلام — والقاعدة: المصدر الحقيقي هو SQL
'''},
            {"type": "checkpoints", "items": [
                "أبرر اختيار SQL أو NoSQL بمعيار (علاقات/معاملات/قيود مقابل مرونة/حجم/توسع) — مش بالموضة.",
                "أنمذج مستنديًا بقرار embed مقابل reference مبني على نمط الوصول وحدود النمو.",
                "أختار partition key في Cosmos بحسب نمط الاستعلام والتوزيع، وأفهم أثره على RU وعلى hot partitions.",
                "أبني نمط polyglot: SQL مصدر حقيقة + outbox + read models متخصصة، مع فهارس وقياس للتكلفة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "سطور الطلب: embed داخل مستند الطلب ولا reference؟",
                 "options": [
                     "Reference دائمًا",
                     "Embed — تُقرأ وتُكتب مع الطلب كوحدة اتساق واحدة (aggregate) وحجمها محدود",
                     "مصفوفة بلا حدود في مستند منفصل",
                     "جدول علائقي داخل Mongo",
                 ], "answer": 1,
                 "explain": "القاعدة: ما يُقرأ ويُكتب معًا يُدمج. العميل/الفئة/الأحداث = reference لأنها كيانات مستقلة أو بلا حدود."},
                {"q": "partition key بـ`orderDate` في Cosmos — المشكلة؟",
                 "options": [
                     "لا مشكلة",
                     "Hot partition: كل كتابات اليوم تتكدس في قسم واحد → اختناق رغم سعة إجمالية فائضة",
                     "تكلفة تخزين أعلى",
                     "لا يدعم الفرز",
                 ], "answer": 1,
                 "explain": "المفتاح المثالي: cardinality عالية + توزيع متساوٍ + مطابق لنمط الاستعلام الأساسي (مثل `customerId`)."},
                {"q": "استعلام Cosmos بدون تمرير partition key — الأثر؟",
                 "options": [
                     "لا أثر",
                     "يصبح cross-partition (fan-out لكل الأقسام) → RU أعلى بكتير وزمن أطول",
                     "يرجع نتائج خاطئة",
                     "يفشل تلقائيًا",
                 ], "answer": 1,
                 "explain": "أغلب تحسينات Cosmos تختصر في: صمّم الاستعلامات لتبقى داخل قسم واحد ومرّر المفتاح صراحة."},
                {"q": "مستوى الاتساق الافتراضي في Cosmos وإمتى ترفعه؟",
                 "options": [
                     "Strong دائمًا",
                     "Session (المستخدم يرى كتاباته)؛ ارفعه لـStrong للعمليات المالية الحساسة مع قبول تكلفة/زمن أعلى",
                     "Eventual دائمًا",
                     "Bounded Staleness",
                 ], "answer": 1,
                 "explain": "Session يكفي أغلب التطبيقات وأرخص. القرار تجاري: كم تتحمل من عدم اتساق مقابل التكلفة والتوفر؟"},
                {"q": "مشروع .NET متوسط الحجم (متجر، تقارير، مستخدمين) — أنهي تخزين؟",
                 "options": [
                     "MongoDB لأنه مرن",
                     "Postgres/SQL Server مصدر الحقيقة + Redis للكاش (+ بحث متخصص لو محتاج) — NoSQL فقط لدليل مقاس",
                     "Cosmos DB لأنه سحابي",
                     "خليط من الثلاثة من البداية",
                 ], "answer": 1,
                 "explain": "البساطة + المعاملات + التقارير + EF Core الناضج = SQL. أضف مخازن متخصصة لما يظهر دليل قياسي على الحاجة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "قرار تخزين موثق",
                 "md": "اكتب ADR لاختيار التخزين في مشروعك: جدول بالمتطلبات (علاقات/معاملات/قيود/حجم/معدل كتابة/مرونة مخطط) وتقييم كل خيار، والقرار مع شروط إعادة النظر. لو اخترت إضافة مخزن NoSQL: حدد الحالة الدقيقة اللي بيخدمها.",
                 "criteria": [
                     "جدول متطلبات بـ6 معايير على الأقل وتقييم لكل خيار",
                     "قرار صريح مع **دليل** (حجم/معدل كتابة/نمط استعلام) مش تفضيل",
                     "شروط إعادة النظر قابلة للقياس (مثال: «لو تجاوز الجدول X صفًا أو p95 القراءة Y»)",
                     "لو polyglot: تحديد مصدر الحقيقة وآلية المزامنة واتساقها",
                 ]},
                {"id": "t2", "title": "read model في مخزن متخصص",
                 "md": "ابنِ مسارًا كاملًا: كتابة في SQL + outbox + مستهلك يبني read model في MongoDB (أو Redis/OpenSearch) + endpoint قراءة من المخزن المتخصص. شغّله بـTestcontainers واختبر المزامنة.",
                 "criteria": [
                     "الكتابة في SQL فقط (المستند لا يُكتب من الـAPI مباشرة)",
                     "outbox داخل نفس المعاملة (بلا فقد) والمستهلك idempotent",
                     "اختبار: إنشاء/تعديل في SQL → يظهر في الـread model (مع انتظار/استطلاع محدد)",
                     "فهارس المخزن المتخصص معرّفة ككود وتُطبَّق عند الإقلاع",
                     "قرار مكتوب: أنهي استعلامات تُخدم من المخزن المتخصص وأنهي من SQL",
                 ],
                 "hint": "لو الاختبار غير مستقر بسبب زمن المزامنة: استخدم استطلاعًا بحد زمني (poll until or timeout) بدل `Task.Delay` ثابت، وسجّل زمن المزامنة كـmetric."},
            ]},
            {"type": "resources", "items": [
                {"label": "MongoDB C# driver", "url": "https://www.mongodb.com/docs/drivers/csharp/current/"},
                {"label": "MongoDB — Data modeling", "url": "https://www.mongodb.com/docs/manual/data-modeling/"},
                {"label": "Azure Cosmos DB documentation", "url": "https://learn.microsoft.com/azure/cosmos-db/"},
                {"label": "Cosmos DB — Choose a partition key", "url": "https://learn.microsoft.com/azure/cosmos-db/nosql/partitioning-overview"},
                {"label": "Cosmos DB — Consistency levels", "url": "https://learn.microsoft.com/azure/cosmos-db/consistency-levels"},
                {"label": "Outbox pattern (MassTransit)", "url": "https://masstransit.io/documentation/configuration/outbox"},
                {"label": "LiteDB", "url": "https://www.litedb.org/"},
            ]},
        ],
    },
]
