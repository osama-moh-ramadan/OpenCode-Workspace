# -*- coding: utf-8 -*-
"""Stage 9 — module 1 (parts C): s9-m1-l3 (إشعارات), l4 (Feed), l5 (تقسيم/نسخ)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════
# l3 — خدمة إشعارات
# ══════════════════════════════════════════════════════════════════
_L3 = {
    "id": "s9-m1-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "خدمة الإشعارات هي **الاختبار الحقيقي لأي مطور خلفي**: فيها كل شيء — طابور · مستهلكون · idempotency · إعادة محاولة · dead-letter · تفضيلات المستخدم · قنوات متعددة · خصوصية · ولا يجوز أن تُفشل العملية الأصلية.\n\nالطلب في السوق على «Senior .NET» بيختبر فهمك لها عمليًا: أي نظام فيه بريد/OTP/push. الدرس بيوصلك لتصميم كامل + كود المكوّن الأساسي."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Notification vs Message", "def": "الإشعار **حدث موجّه للمستخدم** عبر قناة (بريد/SMS/push/داخل التطبيق). الرسالة هي **محتوى** قد يُعاد استخدامه في أكثر من قناة."},
            {"term": "Fan-out", "def": "توزيع حدث واحد على عدة مستلمين/قنوات. هنا: مستخدم واحد → 3 قنوات محتملة، أو حدث → 1000 مستخدم."},
            {"term": "Template + Render", "def": "قوالب ({{name}}، {{orderId}}) تُدمج ببيانات لحظية لإنتاج نص لكل لغة/قناة. لا نصوص مكتوبة في الكود."},
            {"term": "Provider abstraction", "def": "واجهة موحّدة (`IChannelSender`) يتحقق منها SendGrid/SES/Twilio/Firebase — فيسهل التبديل والتجربة والاختبار."},
            {"term": "Exponential backoff + jitter", "def": "تأخير متزايد مع عشوائية: 1s, 4s, 16s… + jitter يمنع تزامن آلاف المحاولات. مع حد أقصى وحد زمني."},
            {"term": "Dead-letter queue (DLQ)", "def": "وجهة للرسائل التي فشلت بعد كل المحاولات — تُراجع يدويًا/آليًا بدل أن تُفقد صامتة."},
            {"term": "Poison message", "def": "رسالة تفشل دائمًا (بيانات تالفة) — إعادة المحاولة لا تفيد؛ تحتاج تمييزًا مبكرًا إلى DLQ."},
            {"term": "Quiet hours / Rate limit per user", "def": "احترام ساعات الهدوء (توقيت المستخدم) وسقف إشعارات لكل مستخدم/يوم — مسألة تجربة واحتفاظ لا تقنية فقط."},
            {"term": "Deliverability", "def": "فرص وصول البريد: SPF/DKIM/DMARC + نطاق فرعي + سمعة IP. بدونها كل الكود يذهب للسبام."},
            {"term": "Dedup key", "def": "مفتاح يمنع نفس الحدث من إنتاج إشعارين (مثلاً `order-123:shipped:email`)."},
            {"term": "Preference center", "def": "تفضيلات المستخدم لكل (نوع حدث × قناة) + unsubscribe تشريعي."},
        ]},

        {"type": "heading", "level": 2, "text": "① المتطلبات والأرقام"},
        {"type": "table", "caption": "ما نبنيه",
         "head": ["البند", "القرار"],
         "rows": [
             ["المصدر", "أحداث من خدمات أخرى (OrderPlaced · PaymentFailed · PasswordChanged)"],
             ["القنوات", "بريد (الأساس) · push · SMS (للحساس فقط) · داخل التطبيق"],
             ["المتطلبات", "at-least-once · تأخير ≤ 30 ثانية للأحداث العادية · OTP ≤ 3 ثوانٍ"],
             ["ممنوع", "أن تُفشل عملية الطلب بسبب فشل إشعار · إرسال إشعار مكرر · إرسال ليلًا للعادي"],
             ["الاحتفاظ", "سجل التسليم 90 يومًا · المحتوى 30 يومًا (PII)"],
             ["الأرقام", "500 حدث/ثانية ذروة · متوسط 2.2 إشعار/حدث · 1,100 إرسال/ثانية · 60% بريد"],
         ]},
        {"type": "code", "lang": "text", "title": "التدفق الكامل", "filename": "docs/notification-flow.txt", "code": r'''
 Service A ──(outbox)──► Bus ──► [notification-worker]
                                    │
                         ┌──────────┴───────────┐
                   1) تحقق dedup (Redis/DB)       │
                   2) اقرأ التفضيلات               │
                   3) اختر القنوات                 │
                   4) Render من قالب + لغة         │
                         │
              ┌──────────┼──────────┬─────────────┐
           Email      Push        SMS        InApp
           provider   provider    provider    DB
              │          │           │           │
              └──── سجل النتيجة (delivery) ───────┘
                    │
              فشل قابل للإعادة ──► retry (backoff)
              فشل دائم/بعد 5 محاولات ──► DLQ + تنبيه
'''},
        {"type": "callout", "kind": "warn", "title": "قاعدة الحدود (Bounded Context)",
         "md": "خدمة الإشعارات **لا تعرف** معنى «الطلب»: بتستقبل حدثًا ببيانات لازمة للعرض فقط. لو بدأت تسأل `Orders` عن تفاصيل إضافية في وقت الإرسال، فأنت خلقت اقترانًا وتحمّلت تعقيدًا بلا داعٍ (4.x).\nالحل: **الحدث يحمل بيانات كافية** (Event-carried state) — أو تُخزَّن نسخة قراءة (materialized view) عند الاستقبال.\nالثمن: الحدث أكبر. الفائدة: لا استدعاء متزامن في مسار التسليم، ولا سلسلة فشل."},

        {"type": "heading", "level": 2, "text": "② الكود: مستهلك idempotent + قنوات + إعادة محاولة"},
        {"type": "code", "lang": "csharp", "title": "Notifications/NotificationWorker.cs — المستهلك الأساسي", "filename": "src/Notifier/NotificationWorker.cs", "code": r'''using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

/// <summary>
/// مستهلك أحداث: يقرأ حزمة، يُنتج إشعارًا لكل (مستخدم × قناة مسموحة)، يسجّل النتيجة.
/// الضمانات: at-least-once + dedup + retry مع backoff + DLQ.
/// </summary>
public sealed class NotificationWorker(
    IMessageBus bus,
    NotifierDb db,
    IPreferenceService prefs,
    ITemplateRenderer renderer,
    IEnumerable<IChannelSender> senders,
    IDedupeStore dedupe,
    IOptions<NotifierOptions> options,
    ILogger<NotificationWorker> log) : BackgroundService
{
    private readonly Dictionary<Channel, IChannelSender> _byChannel =
        senders.ToDictionary(s => s.Channel);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var message in bus.ConsumeAsync<IncomingEvent>("notifications", stoppingToken))
        {
            try
            {
                await HandleAsync(message, stoppingToken);
                await bus.AckAsync(message, stoppingToken);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                // إعادة التسليم تتولاها الباص؛ نسجّل المحاولة فقط
                log.LogError(ex, "فشل معالجة الحدث {EventId} ({Type})",
                    message.Id, message.TemplateKey);
            }
        }
    }

    private async Task HandleAsync(IncomingEvent evt, CancellationToken ct)
    {
        var recipients = await ResolveRecipientsAsync(evt, ct);
        var opts = options.Value;

        foreach (var recipient in recipients)
        {
            var preferences = await prefs.GetAsync(recipient.UserId, ct);

            foreach (var channel in SelectChannels(evt, preferences))
            {
                // ✅ مفتاح منع التكرار: نفس الحدث + نفس المستخدم + نفس القناة = إشعار واحد
                var dedupeKey = $"{evt.Id}:{recipient.UserId}:{channel}";
                if (!await dedupe.TryAcquireAsync(dedupeKey, TimeSpan.FromHours(24), ct))
                {
                    log.LogDebug("تخطّي مكرر {Key}", dedupeKey);
                    continue;
                }

                if (!QuietHours.Allows(evt.Severity, preferences, recipient.TimeZone,
                        DateTimeOffset.UtcNow, opts.QuietHours))
                {
                    // جدولة للصباح بدل الإسقاط
                    await bus.ScheduleAsync(evt, RunAt: QuietHours.NextAllowed(
                        recipient.TimeZone, opts.QuietHours), ct);
                    continue;
                }

                var content = await renderer.RenderAsync(new RenderRequest(
                    TemplateKey: evt.TemplateKey,
                    Channel: channel,
                    Culture: preferences.Culture,
                    Data: evt.Data), ct);

                await SendWithRetryAsync(evt, recipient, channel, content, ct);
            }
        }
    }

    private async Task SendWithRetryAsync(
        IncomingEvent evt, Recipient recipient, Channel channel, RenderedContent content, CancellationToken ct)
    {
        var sender = _byChannel[channel];
        var opts = options.Value;

        for (var attempt = 1; attempt <= opts.MaxAttempts; attempt++)
        {
            var record = DeliveryRecord.Start(evt.Id, recipient.UserId, channel);
            try
            {
                var result = await sender.SendAsync(new OutboundMessage(
                    recipient.Address(channel), content.Subject, content.Body, content.Meta), ct);

                record.Succeed(result.ProviderId);
                await db.DeliveryRecords.AddAsync(record, ct);
                await db.SaveChangesAsync(ct);
                return;
            }
            catch (PermanentSendException ex)
            {
                // بريد غير صالح/رقم محظور: إعادة المحاولة بلا فائدة → DLQ فورًا
                record.Fail(ex.Message, isPermanent: true);
                await db.SaveChangesAsync(ct);
                await bus.DeadLetterAsync(evt, $"دائم: {ex.Message}", ct);
                return;
            }
            catch (TransientSendException ex) when (attempt < opts.MaxAttempts)
            {
                record.Retry(ex.Message, attempt);
                await db.SaveChangesAsync(ct);

                var delay = Backoff.Delay(attempt, opts.BaseDelay, opts.MaxDelay);
                log.LogWarning("محاولة {Attempt} فشلت ({Channel}) — إعادة بعد {Delay}",
                    attempt, channel, delay);
                await Task.Delay(delay, ct);
            }
            catch (TransientSendException ex)
            {
                record.Fail(ex.Message, isPermanent: false);
                await db.SaveChangesAsync(ct);
                await bus.DeadLetterAsync(evt, $"استنفدت المحاولات: {ex.Message}", ct);
                return;
            }
        }
    }

    private static IEnumerable<Channel> SelectChannels(IncomingEvent evt, Preferences p)
    {
        // تفضيل المستخدم يحكم — إلا ما كان إلزاميًا (أمني)
        if (evt.IsSecurityCritical) return [Channel.Email];
        return evt.AllowedChannels.Where(c => p.IsEnabled(evt.Kind, c));
    }

    private Task<List<Recipient>> ResolveRecipientsAsync(IncomingEvent evt, CancellationToken ct) =>
        evt.AudienceKind switch
        {
            AudienceKind.Single => db.Users
                .Where(u => u.Id == evt.UserId)
                .Select(u => new Recipient(u.Id, u.Email, u.Phone, u.PushToken, u.TimeZone))
                .ToListAsync(ct),
            AudienceKind.OrderOwners => db.OrderOwners /* نسخة قراءة محلية */
                .Where(o => o.OrderId == evt.OrderId)
                .Select(o => new Recipient(o.UserId, o.Email, o.Phone, o.PushToken, o.TimeZone))
                .ToListAsync(ct),
            _ => Task.FromResult(new List<Recipient>()),
        };
}

/// <summary>تأخير أسّي مع jitter — بلا jitter كل النسخ تعيد في نفس اللحظة.</summary>
public static class Backoff
{
    private static readonly double[] Jitter = [0.85, 1.0, 1.15];

    public static TimeSpan Delay(int attempt, TimeSpan baseDelay, TimeSpan max)
    {
        var raw = baseDelay * Math.Pow(2, attempt - 1);
        var capped = raw > max ? max : raw;
        var factor = Jitter[Random.Shared.Next(Jitter.Length)];
        return TimeSpan.FromMilliseconds(capped.TotalMilliseconds * factor);
    }
}
'''},
        {"type": "code", "lang": "csharp", "title": "Notifications/ChannelSender.cs — تجريد المزوّد + تصنيف الأخطاء", "filename": "src/Notifier/Channels/ChannelSender.cs", "code": r'''public enum Channel { Email, Push, Sms, InApp }

public interface IChannelSender
{
    Channel Channel { get; }
    Task<SendResult> SendAsync(OutboundMessage message, CancellationToken ct);
}

public sealed record OutboundMessage(string To, string? Subject, string Body, IReadOnlyDictionary<string, string> Meta);
public sealed record SendResult(string ProviderId);

/// <summary>فشل يستحق إعادة المحاولة (5xx، مهلة، حد معدل).</summary>
public sealed class TransientSendException(string message, Exception? inner = null)
    : Exception(message, inner);

/// <summary>فشل لا يُصلَح بإعادة المحاولة (بريد غير صالح، 550، رقم موقوف).</summary>
public sealed class PermanentSendException(string message, Exception? inner = null)
    : Exception(message, inner);

/// <summary>مثال: مزوّد بريد بـHTTP. يصنّف الأخطاء بدقة — وهذا أهم سطر في الملف.</summary>
public sealed class EmailSender(HttpClient http, IOptions<EmailOptions> opts) : IChannelSender
{
    public Channel Channel => Channel.Email;

    public async Task<SendResult> SendAsync(OutboundMessage message, CancellationToken ct)
    {
        using var response = await http.PostAsJsonAsync("/v3/mail/send", new
        {
            personalizations = new[] { new { to = new[] { new { email = message.To } } } },
            from = new { email = opts.Value.FromAddress, name = opts.Value.FromName },
            subject = message.Subject,
            content = new[] { new { type = "text/html", value = message.Body } },
        }, ct);

        if (response.IsSuccessStatusCode)
            return new SendResult(response.Headers.TryGetValues("X-Message-Id", out var ids)
                ? ids.First() : Guid.NewGuid().ToString("N"));

        var status = (int)response.StatusCode;
        var body = await response.Content.ReadAsStringAsync(ct);

        throw status switch
        {
            // 429: تجاوز حد → إعادة محاولة مع انتظار Retry-After
            429 => new TransientSendException($"rate limited: {body}"),
            >= 500 => new TransientSendException($"provider {status}: {body}"),
            // 400 مع بريد غير صالح = دائم. 401/403 = خطأ إعداد (يُنبه لا يُعاد)
            400 or 422 => new PermanentSendException($"invalid recipient: {body}"),
            401 or 403 => new PermanentSendException($"auth misconfigured: {status}"),
            _ => new TransientSendException($"unexpected {status}: {body}"),
        };
    }
}
'''},
        {"type": "table", "caption": "تصنيف الأخطاء = نصف تصميم الإشعارات",
         "head": ["الحالة", "نوع الخطأ", "الإجراء الصحيح", "لو أعدت المحاولة"],
         "rows": [
             ["5xx من المزوّد", "مؤقت", "إعادة مع backoff", "تنجح عادةً — صحيح"],
             ["429 / حد معدل", "مؤقت", "احترام `Retry-After` + تهدئة", "تنجح — لكن بلا احترام الرأس تُعاقب"],
             ["مهلة شبكة", "مؤقت", "إعادة (رسالة قد تكون وصلت ⇒ idempotency عند المزوّد)", "قد تُرسل مرتين — استخدم مفتاح رسالة"],
             ["بريد غير صالح (550)", "دائم", "DLQ فورًا + تعليم العنوان", "تفشل 5 مرات بلا فائدة"],
             ["401/403", "إعداد", "تنبيه تشغيلي + إيقاف الدفعة", "تستهلك الحصة وتفشل"],
             ["بيانات قالب ناقصة", "دائم", "DLQ + إصلاح القالب", "تفشل دائمًا"],
         ]},

        {"type": "heading", "level": 2, "text": "③ اختيار المزوّد: ما لا يقوله التسويق"},
        {"type": "table", "caption": "معايير القرار (بريد)",
         "head": ["المعيار", "ما تسأل عنه", "لماذا يهم"],
         "rows": [
             ["Deliverability", "SPF/DKIM/DMARC؟ نطاق فرعي؟ سمعة IP مشترك أم مخصص؟", "أكبر سبب لفشل البريد ليس الكود بل السمعة"],
             ["Idempotency", "هل يقبل `Idempotency-Key`/رسالة مفتاح؟", "يمنع إرسالًا مزدوجًا عند إعادة المحاولة"],
             ["Webhooks", "bounce · complaint · delivered · opened؟", "لتحديث سجل التسليم وتعطيل العناوين السيئة"],
             ["التسعير", "لكل 1000 أم اشتراك؟", "قد يكون الفرق 10× بين مزوّدين"],
             ["الموقع", "منطقة الإرسال/الاحتفاظ", "متطلبات خصوصية (PDPL) وكمون"],
             ["الحصة", "حد يومي/ثانية وهل قابل للزيادة؟", "الذروة قد تصطدم بحد غير معلن"],
         ]},
        {"type": "callout", "kind": "tip", "title": "الاختيار العملي",
         "md": "**البريد**: مزوّد يقوم بالتحقق من SPF/DKIM/DMARC ويدعم Webhooks للـbounce — والبدء بنطاق فرعي (`mail.yoursite.com`) يحمي نطاقك الأساسي.\n**SMS**: الأغلى والأدق: احجزه لـOTP/الأمان فقط، مع مزوّد يدعم أرقامًا محلية في مصر (`EG`) وتأكيد التسليم.\n**Push**: FCM/APNs مباشرة أو عبر مزوّد؛ تذكّر أن **حالة الإذن** عند المستخدم متقلّبة — اعمل fallback للبريد.\n**داخل التطبيق**: أسهل وأرخص قناة، ويجب أن تكون دائمًا موجودة كسجل (inbox) — حتى لو القنوات الأخرى فشلت."},

        {"type": "heading", "level": 2, "text": "④ OTP: حالة خاصة صارمة"},
        {"type": "table", "caption": "فروق OTP عن الإشعار العادي",
         "head": ["الجانب", "الإشعار العادي", "OTP"],
         "rows": [
             ["الزمن", "≤ 30 ثانية", "**≤ 3 ثوانٍ** (مسار متزامن) وليس عبر الطابور نفسه"],
             ["التكرار", "مسموح مع dedup", "**ممنوع** إرسال عند كل ضغطة — rate limit لكل رقم/جهاز"],
             ["التخزين", "سجل 90 يومًا", "**الرمز مُهشَّر** في Redis/DB بـTTL 5 دقائق ولا يُسجَّل في اللوج"],
             ["المحاولات", "5", "3 محاولات تحقق ثم إبطال الرمز"],
             ["التكلفة", "منخفضة لمعظم القنوات", "كل رسالة تكلفة — حد أقصى 5/ساعة/رقم"],
             ["الأمان", "PII في القالب", "لا تذكر الرمز في اللوج/التحليلات · حماية من التعداد"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Otp/OtpService.cs — توليد آمن + حد معدل + تحقق بثبات زمني", "filename": "src/Notifier/Otp/OtpService.cs", "code": r'''using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Caching.Distributed;

public sealed class OtpService(IDistributedCache cache, ISmsSender sms, ILogger<OtpService> log)
{
    private const int MaxAttempts = 3;
    private static readonly TimeSpan Ttl = TimeSpan.FromMinutes(5);

    public async Task<OtpRequestResult> RequestAsync(string phone, CancellationToken ct)
    {
        // ① حد معدل: 5/ساعة لكل رقم (يمنع استنزاف الرصيد والانتحال)
        var hourlyKey = $"otp:rl:{phone}:{DateTimeOffset.UtcNow:yyyyMMddHH}";
        var count = await cache.GetStringAsync(hourlyKey, ct);
        var sent = string.IsNullOrEmpty(count) ? 0 : int.Parse(count);
        if (sent >= 5) return OtpRequestResult.TooMany();

        // ② رمز عشوائي آمن (لا Random)
        var code = RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");

        // ③ نخزّن (salt + هش) لا الرمز، وTTL قصير
        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Hash(salt, code);
        await cache.SetStringAsync($"otp:{phone}", $"{Convert.ToHexString(salt)}:{hash}",
            new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = Ttl,
        }, ct);
        await cache.SetStringAsync($"otp:att:{phone}", "0", new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = Ttl,
        }, ct);

        // ④ إرسال + سجل بلا رمز
        await sms.SendAsync(phone, $"رمز التحقق: {code}. صالح 5 دقائق. لا تشاركه.", ct);
        log.LogInformation("OTP أُرسل لرقم ينتهي بـ{suffix}", phone[^4..]);

        await cache.SetStringAsync(hourlyKey, (sent + 1).ToString(), new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(1),
        }, ct);

        return OtpRequestResult.Sent();
    }

    public async Task<bool> VerifyAsync(string phone, string candidate, CancellationToken ct)
    {
        var storedHash = await cache.GetStringAsync($"otp:{phone}", ct);
        if (storedHash is null) return false;

        var attempts = int.Parse(await cache.GetStringAsync($"otp:att:{phone}", ct) ?? "0");
        if (attempts >= MaxAttempts)
        {
            await cache.RemoveAsync($"otp:{phone}", ct);   // إبطال بعد 3 محاولات
            return false;
        }

        await cache.SetStringAsync($"otp:att:{phone}", (attempts + 1).ToString(), ct);

        // نستعيد الـsalt من المخزون ونعيد حساب الهش بنفس الطريقة
        var parts = storedHash.Split(':');
        if (parts.Length != 2) return false;
        var salt = Convert.FromHexString(parts[0]);
        var expected = parts[1];
        var actual = Hash(salt, candidate);

        // مقارنة ثابتة الزمن (تمنع timing attack)
        var ok = CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(actual),
            Encoding.ASCII.GetBytes(expected));

        if (ok) await cache.RemoveAsync($"otp:{phone}", ct);   // استعمال واحد
        return ok;
    }

    private static string Hash(byte[] salt, string code) =>
        Convert.ToHexString(SHA256.HashData([.. salt, .. Encoding.UTF8.GetBytes(code)]));
}
'''},
        {"type": "callout", "kind": "danger", "title": "5 أخطاء OTP شائعة",
         "md": "**① `Random` بدل `RandomNumberGenerator`** — قابل للتنبؤ ⇒ اختراق.\n**② تخزين الرمز نصًا مع تسجيله** — أي وصول للسجلات = اختراق حسابات.\n**③ مقارنة `==`** — تسريب زمني (نظريًا)؛ الأصح `FixedTimeEquals`.\n**④ بلا حد معدل** — فاتورة SMS ضخمة + إزعاج + تعداد أرقام.\n**⑤ رمز صالح للأبد** — TTL 5 دقائق + استعمال واحد + إبطال بعد 3 محاولات."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تفصل «الإشعار» عن «الحدث» وتربط بينهما قالبيًا.",
            "تصمّم تدفقًا كاملًا: حدث → worker → dedupe → تفضيلات → render → قناة → سجل.",
            "تضمن idempotency بمفتاح (حدث+مستخدم+قناة) لا بمنطق عرضي.",
            "تصنّف أخطاء المزوّد إلى مؤقت/دائم/إعداد وتتعامل مع كل نوع صحيحًا.",
            "تطبّق backoff أسّي مع jitter وحد أقصى للمحاولات.",
            "تعرف متى تذهب الرسالة إلى DLQ وتضع تنبيهًا له.",
            "تختار مزوّد البريد بمعايير deliverability وwebhooks لا بالسعر فقط.",
            "تخصّص مسارًا مختلفًا لـOTP (تحقق متزامن، الهش، حد معدل، استعمال واحد).",
            "تحترم ساعات الهدوء والتفضيلات، وتجدول بدل الإسقاط.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "7 أسئلة.",
         "questions": [
             {"q": "أين يقع مفتاح منع التكرار الصحيح؟",
              "options": ["معرّف الرسالة فقط", "مزيج (الحدث + المستخدم + القناة) — لأن نفس الحدث قد ينتج عدة إشعارات مشروعة",
                          "عنوان البريد", "وقت الإرسال"],
              "answer": 1,
              "explain": "لو استخدمت معرّف الحدث فقط، فأول قناة تنجح ستمنع الباقي. المفتاح المزيّن يضمن قناة واحدة لكل مستخدم لكل حدث، مع السماح بقنوات مختلفة."},
             {"q": "مزوّد البريد أعاد 429 — ما التصرف؟",
              "options": ["إعادة فورية", "إعادة بعد احترام `Retry-After` مع backoff وتهدئة",
                          "إلى DLQ فورًا", "تجاهل الرسالة"],
              "answer": 1,
              "explain": "429 مؤقت لكنه رسالة صريحة: أنت تتجاوز الحد. الإعادة الفورية تضاعف العقوبة. القرار: انتظار الرأس (أو backoff) ثم إعادة — ومع تكرار ذلك، طلب رفع الحصة."},
             {"q": "لماذا jitter في backoff؟",
              "options": ["لتقليل التكلفة", "لمنع تزامن آلاف المحاولات عند تعافي الخدمة (thundering herd)",
                          "لزيادة السرعة", "لأسباب تجميلية"],
              "answer": 1,
              "explain": "بدون jitter، كل النسخ/الرسائل تعيد في نفس الثانية فتسقط الخدمة المتعافية مرة أخرى. العشوائية ±15% توزّع الحمل."},
             {"q": "ما دلالة خطأ 550 من مزوّد البريد؟",
              "options": ["مؤقت", "دائم (بريد غير صالح) — لا تُعِد المحاولة، أرسل لـDLQ وعلّم العنوان",
                          "خطأ إعداد", "مهلة"],
              "answer": 1,
              "explain": "550 = mailbox unavailable. إعادة المحاولة 5 مرات تستهلك الحصة وتضر السمعة. الصح: تسجيل الفشل النهائي وتعطيل العنوان حتى يحدّثه المستخدم."},
             {"q": "أين يجب أن يكون مفتاح OTP؟",
              "options": ["plain text في Redis", "plain text في القاعدة", "**هش** مع TTL قصير واستعمال واحد", "في الـJWT"],
              "answer": 2,
              "explain": "أي رمز حساس يُخزَّن هشًا (بـsalt). مع TTL 5 دقائق واستعمال واحد وإبطال بعد 3 محاولات، تصبح قيمة أي تسريب محدودة جدًا."},
             {"q": "حدث «طلب تم شحنه» يحتاج اسم العميل والمنتج. أين تأتي البيانات؟",
              "options": ["استدعاء خدمة الطلبات وقت الإرسال", "الحدث يحمل البيانات اللازمة (event-carried state) أو تُبنى نسخة قراءة محلية",
                          "من ذاكرة المستهلك", "من قاعدة التطبيق مباشرة"],
              "answer": 1,
              "explain": "الاستدعاء وقت الإرسال يخلق اقترانًا زمنيًا ونقطة فشل جديدة. حمل البيانات في الحدث أو بناء projection عند الاستقبال يحافظ على استقلال الخدمة (4.x)."},
             {"q": "ما القناة التي يجب أن تعمل دائمًا كسجل حتى لو فشل البريد؟",
              "options": ["SMS", "Push", "In-App (inbox داخل التطبيق)", "لا شيء"],
              "answer": 2,
              "explain": "قناة داخلية مخزّنة في القاعدة ليست معتمدة على مزوّد خارجي، فتضمن أن المستخدم يرى ما فاته. كثير من الأنظمة تعتبرها الأساس وتجعل البقية إشعارات إضافية."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "خدمة إشعارات تعمل فعلًا + OTP آمن.",
         "items": [
            {"id": "s9-m1-l3-t1",
             "title": "مهمة 1: خدمة إشعارات بمستهلك idempotent",
             "md": "نفّذ worker يستهلك حدثًا وينتج إشعارات على قناتين (بريد + in-app) مع dedupe وتفضيلات وسجل تسليم وDLQ.",
             "criteria": [
                 "حدث واحد ينتج إشعارًا واحدًا لكل (مستخدم × قناة) — إثبات بإعادة تسليم نفس الحدث 3 مرات.",
                 "تصنيف أخطاء المزوّد إلى مؤقت/دائم مع اختبارات لكل نوع (500، 429، 550).",
                 "backoff أسّي مع jitter وحد أقصى، وانتقال إلى DLQ بعد الاستنفاد.",
                 "احترام التفضيلات + ساعات الهدوء (جدولة بدل إسقاط).",
                 "سجل تسليم (`DeliveryRecord`) لكل محاولة: الحالة، المحاولة، سبب الفشل.",
                 "قناة in-app تعمل دائمًا كسجل حتى لو فشل البريد.",
                 "قالب واحد على الأقل بلغتين مع بيانات لحظية.",
                 "3 اختبارات على الأقل: تكرار الحدث · فشل مؤقت ثم نجاح · فشل دائم إلى DLQ.",
             ],
             "hint": "ابدأ بجدول `DeliveryRecords` ومفتاح dedupe في Redis — لو لم يوجدا، ستُنتج إشعارات مكررة عند أول إعادة تسليم. لاختبار الفشل المؤقت: موك `IChannelSender` يرمي `TransientSendException` مرتين ثم ينجح — وتحقّق من عدد المحاولات والأزمنة.",
             "solution": "النتيجة النموذجية: مستهلك ~150 سطرًا + مزوّد بريد مصنِّف للأخطاء + قناة in-app. أصعب جزء: التمييز بين المؤقت والدائم — إعادة المحاولة على 550 تحرق السمعة، وعدم إعادة المحاولة على 503 تُفقد إشعارات. وثّق جدول التصنيف في README.",
             "resources": [
                 "https://learn.microsoft.com/azure/architecture/patterns/retry",
                 "https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling",
                 "https://www.pollydocs.org/",
             ]},
            {"id": "s9-m1-l3-t2",
             "title": "مهمة 2: OTP آمن بحدود",
             "md": "نفّذ خدمة OTP: توليد آمن، هش، TTL، استعمال واحد، 3 محاولات، حد معدل 5/ساعة، ولا رمز في اللوج.",
             "criteria": [
                 "`RandomNumberGenerator` فقط — لا `Random`.",
                 "التخزين هش بـsalt، ولا يُسجَّل الرمز في أي لوج (فحص grep).",
                 "TTL 5 دقائق + استعمال واحد + إبطال بعد 3 محاولات فاشلة.",
                 "حد معدل لكل رقم/ساعة + رسالة واضحة عند التجاوز.",
                 "`FixedTimeEquals` للمقارنة.",
                 "اختبارات: صحيح ينجح مرة واحدة · خاطئ 3 مرات يُبطل · تجاوز الحد يمنع الإرسال.",
                 "صفحة/أمر لتنظيف مفاتيح OTP المنتهية (أو TTL كافٍ موثّق).",
             ],
             "hint": "انتبه إلى أن إعادة إرسال رمز جديد يجب أن تُبطل القديم (تخزين قيمة واحدة لكل رقم). وفي الاختبارات، اعزل الوقت (`TimeProvider`) حتى لا تنتظر 5 دقائق فعلية.",
             "solution": "النتيجة: خدمة ~120 سطرًا و4 اختبارات. النقطة اللي بيغفلها الكثيرون: **إعادة الإرسال** — إذا لم تُبطل الرمز القديم، يصبح لديك رمزان صالحان (ثقب أمني). الحل: مفتاح واحد لكل رقم + استبدال دائم.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.security.cryptography.randomnumbergenerator",
                 "https://learn.microsoft.com/aspnet/core/performance/caching/distributed",
                 "https://owasp.org/www-project-authentication-cheat-sheet/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Queue-Based Load Leveling", "url": "https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling"},
            {"label": "Retry pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/retry"},
            {"label": "Circuit Breaker", "url": "https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker"},
            {"label": "Polly (المرونة في .NET)", "url": "https://www.pollydocs.org/"},
            {"label": "DistributedCache في ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/caching/distributed"},
            {"label": "DMARC وSPF/DKIM", "url": "https://learn.microsoft.com/microsoft-365/security/office-365-security/email-authentication-dmarc-configure"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════
# l4 — Feed
# ══════════════════════════════════════════════════════════════════
_L4 = {
    "id": "s9-m1-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الـ**Feed** (الخط الزمني) هو السؤال اللي بيميز السينيور: **تكتب وقت النشر أم وقت القراءة؟**\n\nسؤال بسيط، وجوابه بيحدد تكلفة النظام كله. الدرس بيقارن استراتيجيتي fan-out بأرقام حقيقية، وينتهي بتصميم هجين هو اللي بتستخدمه تويتر/إنستجرام فعليًا."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Fan-out on write", "def": "عند النشر: اكتب المحتوى في **صندوق** (inbox/fanout table) كل متابع. القراءة رخيصة جدًا، والكتابة مكلفة."},
            {"term": "Fan-out on read", "def": "عند القراءة: اجمع منشورات كل من تتابعه ودمجها وترتيبها. الكتابة رخيصة، والقراءة مكلفة."},
            {"term": "Celebrity problem", "def": "حساب بملايين المتابعين يجعل fan-out on write انفجارًا كتابيًا. يُعالَج بهجين: لا تُفرّغ حسابات المشاهير، ادمجها وقت القراءة."},
            {"term": "Timeline store", "def": "جدول `user_id, item_id, created_at, rank` — مفتاح أساسي مركّب (user, time desc) لقراءة صفحة واحدة."},
            {"term": "Cursor pagination", "def": "ترقيم بـ(cursor = time+id) بدل OFFSET — ثابت مع الإضافات الجديدة ولا يكرر عناصر (3.3)."},
            {"term": "Fanout queue", "def": "طابور ينفّذ توزيع المنشور على المتابعين على دفعات؛ التقدّم قابل للاستئناف عند الفشل."},
            {"term": "Ranking", "def": "ترتيب غير زمني (تفاعل/حداثة/جودة) — يغيّر المتطلبات: يحتاج حساب مسبق أو حساب وقت القراءة."},
            {"term": "Backfill", "def": "بناء خط زمني لمستخدم جديد من بيانات موجودة، أو إعادة بناء بعد تغيير المنطق."},
            {"term": "Tombstone", "def": "علامة حذف تحفظ بها الاتساق في النسخ الموزعة بدل حذف فوري."},
        ]},

        {"type": "heading", "level": 2, "text": "① المقارنة الحاسمة"},
        {"type": "table", "caption": "Fan-out: أين تدفع الثمن؟",
         "head": ["الاستراتيجية", "عند النشر", "عند القراءة", "متى تناسب", "العيب القاتل"],
         "rows": [
             ["**Write**", "N كتابة (N = المتابعون)", "قراءة واحدة من جدولك", "مستخدمون بمتابعين قليلين (متوسط < 1000)", "مشهور بـ5M متابع = 5M كتابة"],
             ["**Read**", "كتابة واحدة", "دمج K مصدر (K = من تتابع) + ترتيب", "نشر ثقيل، متابعون بمتابعين كثيرين", "بطء عند متابعة 1000 حساب"],
             ["**Hybrid**", "كتب للمتابعين العاديين، تخطَّ المشاهير", "دمج قصير: جدولك + منشورات المشاهير", "**كل منصة حقيقية**", "تعقيد أعلى قليلًا"],
         ]},
        {"type": "code", "lang": "text", "title": "الأرقام التي تحسم القرار", "filename": "docs/feed-numbers.txt", "code": r'''
الافتراض: 10M مستخدم · 1M منشور/يوم · متوسط 200 متابع · 5% حسابات ثقيلة (متابعوها > 10k)

Write fan-out الكامل:
  1M منشور × 200 = 200M صف/يوم  ← 2,300 صف/ثانية متوسط، 8,000 في الذروة
  حجم: 200M × 40B ≈ 8GB/يوم (فقط فهارس)  → 3TB/سنة. غير مقبول.

Read fan-out الكامل:
  قراءة = 200 مصدر × دمج ≈ 20–60ms لكل صفحة، مع 20 قراءة/مستخدم/يوم
  → 10M × 20 = 200M استعلام/يوم على جداول مختلفة + ضغط كبير على القاعدة.

Hybrid:
  الثقيلون (5% من المستخدمين) لا يُفرّغون. متوسط المتابعين الفعلي 200 - 50 = 150
  1M × 150 = 150M صف/يوم… لا يزال كبيرًا ⇒ **قلّل الدقة**:
   • لا تُفرّغ لكل متابع فورًا إنما على دفعات (batched, الترتيب لا يهم داخل ثانية)
   • قيّد الحجم:احتفظ بآخر 800 عنصر في خط الزمن لكل مستخدم (TTL/تقليم)
   • المستخدمون الخاملون (> 30 يومًا) لا يُفرّغ لهم — يُبنى خطهم عند عودتهم (lazy)
  النتيجة: 150M × 0.35 ≈ 50M صف/يوم ≈ 600/ثانية — قابل للإدارة.
'''},
        {"type": "callout", "kind": "tip", "title": "الجواب اللي يُقنع في المقابلة",
         "md": "«أبدأ بـ**fan-out on write** لأن المتوسط 200 متابع؛ وأضيف **Hybrid** بمجرد أن يتجاوز 1% من الحسابات 10k متابع؛ وأُبقي **قراءة الزمن الحقيقي** للمشاهير مدموجة في نفس المسار. وأكتب حد إعادة النظر بالأرقام: إذا تجاوزت الكتابة 2,000/ث أو الشعرية 40% → أعيد التصميم».\nمش «أستخدم Redis» — بل **قرار + ثمن + شرط تغيير**."},

        {"type": "heading", "level": 2, "text": "② الكود: جدول خط الزمن + قراءة هجينة"},
        {"type": "code", "lang": "csharp", "title": "Feed/FeedService.cs — كتابة بالتوزيع + قراءة مدموجة", "filename": "src/Feed/FeedService.cs", "code": r'''using Microsoft.EntityFrameworkCore;

/// <summary>
/// Hybrid feed:
///   • نشر → توزيع على المتابعين (على دفعات، بمفتاح (userId, itemId) فريد).
///   • قراءة → من جدول خط الزمن + دمج منشورات المشاهير (بلا توزيع لهم).
/// </summary>
public sealed class FeedService(FeedDb db, IFanoutQueue queue, ILogger<FeedService> log)
{
    private const int TimelineCap = 800;     // سقف العناصر المحفوظة لكل مستخدم
    private const int FanoutPage = 500;      // حجم الدفعة
    private const int PageSize = 20;

    // ── النشر ──────────────────────────────────────────────────
    public async Task PublishAsync(Post post, CancellationToken ct)
    {
        db.Posts.Add(post);
        await db.SaveChangesAsync(ct);

        // ندخل الحدث للطابور؛ التوزيع ينفّذه عامل مستقل (5.2.5 outbox)
        await queue.EnqueueAsync(new FanoutJob(post.Id, post.AuthorId, post.CreatedAt), ct);
    }

    // ── العامل: التوزيع على المتابعين ─────────────────────────
    public async Task RunFanoutAsync(CancellationToken ct)
    {
        await foreach (var job in queue.DequeueAsync(ct))
        {
            var cursor = job.CursorUserId;
            var fans = await db.Follows
                .Where(f => f.FolloweeId == job.AuthorId && f.IsCelebrity == false)
                .Where(f => cursor == null || string.Compare(f.FollowerId, cursor) > 0)
                .OrderBy(f => f.FollowerId)
                .Take(FanoutPage)
                .Select(f => f.FollowerId)
                .ToListAsync(ct);

            if (fans.Count == 0)
            {
                await queue.CompleteAsync(job, ct);
                continue;
            }

            var rows = fans.Select(userId => new TimelineEntry
            {
                UserId = userId,
                PostId = job.PostId,
                AuthorId = job.AuthorId,
                CreatedAt = job.CreatedAt,
                Rank = job.CreatedAt.ToUnixTimeMilliseconds(),
            }).ToList();

            // insert متساهل: تكرار المفتاح (userId, postId) يُتجاهل بلا فشل الدفعة
            await db.Database.ExecuteSqlRawAsync("""
                INSERT INTO timeline_entries (user_id, post_id, author_id, created_at, rank)
                SELECT * FROM UNNEST(@p0::text[], @p1::text[], @p2::text[], @p3::timestamptz[], @p4::bigint[])
                ON CONFLICT (user_id, post_id) DO NOTHING
                """, [fans.ToArray(), Enumerable.Repeat(job.PostId, fans.Count).ToArray(),
                      Enumerable.Repeat(job.AuthorId, fans.Count).ToArray(),
                      Enumerable.Repeat(job.CreatedAt, fans.Count).ToArray(),
                      Enumerable.Repeat(job.CreatedAt.ToUnixTimeMilliseconds(), fans.Count).ToArray()],
                ct);

            // استئناف من آخر مستخدم — الوظيفة قابلة للتكرار بلا ضرر (idempotent)
            await queue.CheckpointAsync(job, fans[^1], ct);
        }
    }

    // ── القراءة ───────────────────────────────────────────────
    public async Task<IReadOnlyList<FeedItem>> GetTimelineAsync(
        string userId, long? cursorRank, CancellationToken ct)
    {
        // ① خط الزمن المُعدّ مسبقًا (الكتاب العاديون)
        var mine = await db.Timeline
            .Where(t => t.UserId == userId && (cursorRank == null || t.Rank < cursorRank))
            .OrderByDescending(t => t.Rank)
            .Take(PageSize)
            .Join(db.Posts, t => t.PostId, p => p.Id,
                  (t, p) => new FeedItem(p.Id, p.AuthorId, p.Text, p.CreatedAt, t.Rank))
            .ToListAsync(ct);

        // ② منشورات المشاهير (غير موزّعة) — دمج ديناميكي
        var celebs = await db.Follows
            .Where(f => f.FollowerId == userId && f.IsCelebrity)
            .Select(f => f.FolloweeId)
            .ToListAsync(ct);

        if (celebs.Count > 0)
        {
            var fromCelebs = await db.Posts
                .Where(p => celebs.Contains(p.AuthorId)
                         && (cursorRank == null || p.Rank < cursorRank))
                .OrderByDescending(p => p.Rank)
                .Take(PageSize)
                .Select(p => new FeedItem(p.Id, p.AuthorId, p.Text, p.CreatedAt, p.Rank))
                .ToListAsync(ct);

            mine = mine.Concat(fromCelebs)
                .DistinctBy(i => i.PostId)
                .OrderByDescending(i => i.Rank)
                .Take(PageSize)
                .ToList();
        }

        return mine;
    }

    /// <summary>تقليم: يمنع نمو جدول الخط الزمني بلا حد.</summary>
    public Task TrimAsync(string userId, CancellationToken ct) =>
        db.Database.ExecuteSqlRawAsync("""
            DELETE FROM timeline_entries
            WHERE user_id = {0}
              AND post_id NOT IN (
                SELECT post_id FROM timeline_entries
                WHERE user_id = {0} ORDER BY rank DESC LIMIT {1})
            """, [userId, TimelineCap], ct);
}
'''},
        {"type": "table", "caption": "قرارات التخزين والفهارس",
         "head": ["الجدول", "المفتاح", "الفهرس", "لماذا"],
         "rows": [
             ["`timeline_entries`", "`(user_id, post_id)` فريد", "`(user_id, rank DESC)`", "قراءة صفحة واحدة بأقل I/O + منع التكرار"],
             ["`posts`", "`post_id`", "`(author_id, rank DESC)`", "جلب منشورات المشاهير ومنشورات الحساب"],
             ["`follows`", "`(follower_id, followee_id)`", "`(followee_id)` جزئي `is_celebrity=false`", "التوزيع يقرأ المتابعين العاديين فقط"],
             ["تقليم", "—", "مهمة دورية", "سقف 800 عنصر/مستخدم"],
         ]},
        {"type": "callout", "kind": "warn", "title": "ثلاث مصائد في الـFeed",
         "md": "**① `OFFSET 10000`** — يقرأ ويرمي؛ استخدم cursor (3.3).\n**② حساب جديد لا يتابع أحدًا** — يجب أن يرى محتوى استكشاف (fallback) وإلا يخرج فورًا. هذا قرار منتج وله أثر تقني.\n**③ الخاملون يستهلكون كتابة** — لا تُفرّغ لمستخدم لم يفتح التطبيق شهرًا؛ ابنِ خطه عند عودته (lazy backfill) وأضف TTL/تقليم."},

        {"type": "heading", "level": 2, "text": "③ الحسابات الضخمة: الحل الكامل"},
        {"type": "table", "caption": "3 خطوات",
         "head": ["الخطوة", "التنفيذ", "الأثر"],
         "rows": [
             ["التصنيف", "عدّاد متابعين → `is_celebrity` عند تجاوز 50k", "لا توزيع لمشاهير"],
             ["القراءة", "دمج منشورات المشاهير بـ`(author_id, rank)` خلال نافذة زمنية قصيرة", "زمن إضافي ~10ms"],
             ["التخزين المؤقت", "كاش منشورات المشاهير لكل مستخدم 30–60 ثانية", "تقلّل الحمل على `posts`"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Feed/CelebrityPolicy.cs — قرار التصنيف + القراءة من الكاش", "filename": "src/Feed/CelebrityPolicy.cs", "code": r'''/// <summary>
/// متى يعتبر الحساب «مشهورًا»؟ القرار يُبنى على التكلفة لا على الشهرة:
///   التكلفة = عدد المتابعين × معدل النشر اليومي
///   الحد: 100,000 عملية توزيع/يوم ≈ 1.2 في الثانية (مقبول).
/// </summary>
public static class CelebrityPolicy
{
    private const long FanoutPerDayBudget = 100_000;

    public static bool IsCelebrity(int followers, double postsPerDay) =>
        followers * postsPerDay > FanoutPerDayBudget;

    // أمثلة:
    //   20,000 متابع × 2 منشور = 40,000  → عادي
    //   60,000 متابع × 2 منشور = 120,000 → مشهور (يُستثنى من التوزيع)
    //    5,000 متابع × 30 منشورًا = 150,000 → مشهور (نشر كثيف!)
}

public sealed record FeedItem(string PostId, string AuthorId, string Text, DateTimeOffset CreatedAt, long Rank);
public sealed record FanoutJob(string PostId, string AuthorId, DateTimeOffset CreatedAt, string? CursorUserId = null);
'''},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تقارن fan-out on write/read بالتكلفة (كتابات/قراءات) لا بالإحساس.",
            "تحسب عدد صفوف خط الزمن يوميًا من (منشورات × متابعين) وتقرر إن كان مقبولًا.",
            "تعرف `celebrity problem` وتشرح الهجين بدقة.",
            "تصمّم جدول `timeline_entries` بمفتاح مركّب فريد وفهرس `(user, rank desc)`.",
            "تستخدم cursor لا OFFSET، وتشرح لماذا.",
            "تجعل التوزيع على دفعات مع checkpoint قابل للاستئناف.",
            "تقلّم خط الزمن بسقف، وتتعامل مع الخاملين بـlazy backfill.",
            "تضيف fallback للمستخدم الجديد.",
            "تعرف أثر الترتيب (Ranking) على التصميم ومتى تنتقل لحساب مسبق.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة.",
         "questions": [
             {"q": "منصة بها متوسط 200 متابع ونشر 1M منشور/يوم — أي استراتيجية تبدأ بها؟",
              "options": ["Read fan-out", "Write fan-out (مع hybrid للمشاهير)",
                          "بلا خط زمني", "مزامنة كاملة"],
              "answer": 1,
              "explain": "200 متابع × 1M = 200M صف/يوم وهو كبير — لذا تبدأ بـwrite fan-out **مع تقييد** (تقليم، دفعات، استثناء الخاملين والمشاهير). البدء بـread fan-out يجعل كل قراءة تدمج 200 مصدرًا."},
             {"q": "ما التكلفة الأساسية في fan-out on write؟",
              "options": ["مساحة القرص فقط", "الكتابات المضاعفة (متابعون × منشور) وضغط الإدراج",
                          "زمن القراءة", "الفهارس"],
              "answer": 1,
              "explain": "القراءة رخيصة جدًا (صف واحد لكل صفحة)، لكن الكتابة تتضاعف بعدد المتابعين، وتحتاج طابورًا ودفعات وقابلية استئناف."},
             {"q": "لماذا نستثني المشاهير من التوزيع؟",
              "options": ["لأنهم لا يريدون", "لأن منشورًا واحدًا قد يعني ملايين الكتابات — فتُدمج منشوراتهم وقت القراءة",
                          "لتوفير مساحة القرص", "لأسباب قانونية"],
              "answer": 1,
              "explain": "التكلفة = متابعون × منشورات. حساب بـ5M متابع × 3 منشورات = 15M كتابة يوميًا لحساب واحد. الحل: دمجهم في القراءة من فهرس `(author_id, rank)`."},
             {"q": "لماذا `ON CONFLICT DO NOTHING` مهم في التوزيع؟",
              "options": ["لتحسين الأداء فقط", "لجعل العملية idempotent: إعادة معالجة دفعة بعد فشل لا تُنشئ صفوفًا مكررة",
                          "لتصغير الفهارس", "لتجنب المفاتيح الأجنبية"],
              "answer": 1,
              "explain": "العامل قد يُعاد تشغيله من checkpoint سابق. بدون `ON CONFLICT`، ستفشل الدفعة كلها أو تنشئ تكرارًا. معه، الإعادة آمنة — وهي شرط أي معالجة قابلة للاستئناف."},
             {"q": "مستخدم جديد لا يتابع أحدًا — ما الإجراء؟",
              "options": ["feed فارغ", "محتوى استكشاف (fallback) + اقتراحات متابعة",
                          "خطأ", "إيقاف الحساب"],
              "answer": 1,
              "explain": "feed فارغ = أول تجربة سيئة = مغادرة. القرار منتج + تقني: fallback لمحتوى رائج/موصى من فهرس منفصل، يعمل حتى لو خط الزمن الشخصي فارغ."},
             {"q": "ما التغيير إذا انتقلنا لترتيب (Ranking) بدل الزمن؟",
              "options": ["لا شيء", " يحتاج حساب الدرجة مسبقًا عند التوزيع أو حسابها عند القراءة؛ وتصبح قابلية الترقيم بالمؤشر أصعب",
                          "يكفي تغيير ORDER BY", "نلغي الكاش"],
              "answer": 1,
              "explain": "مع الترتيب، `rank` ليس زمنيًا فقط: تحتاج درجة محسوبة (تفاعل/حداثة/جودة) وقد تتغير بعد النشر. أثر ذلك: إعادة حساب دورية، أو حساب لحظي عند القراءة، وصعوبة ترقيم ثابت (تحتاج snapshot/مؤشر مركّب)."},
         ]},

        {"type": "tasks", "title": "مهمة واحدة", "intro": "خط زمني هجين قابل للقياس.",
         "items": [
            {"id": "s9-m1-l4-t1",
             "title": "مهمة: نفّذ خط زمني هجين",
             "md": "نفّذ `timeline_entries` + توزيع على دفعات + قراءة مدموجة مع منشورات المشاهير + تقليم، واختبره بسيناريو مستخدم عادي ومشهور.",
             "criteria": [
                 "جدول `timeline_entries` بمفتاح فريد `(user_id, post_id)` وفهرس `(user_id, rank DESC)`.",
                 "التوزيع على دفعات 500 مع checkpoint قابل للاستئناف و`ON CONFLICT DO NOTHING`.",
                 "استثناء المشاهير بقاعدة مكتوبة (متابعون × منشورات/يوم) لا برقم عشوائي.",
                 "القراءة تدمج المصدرين بلا تكرار وترتيب صحيح + cursor للصفحة التالية.",
                 "تقليم بسقف 800 عنصر مُختبر (أدخل 1000 وتحقّق).",
                 "اختبار: منشور من حساب عادي يظهر؛ منشور من مشهور يظهر عبر الدمج؛ حساب جديد يرى fallback.",
                 "قياس: زمن قراءة صفحة أولى وثانية بالأرقام قبل/بعد الدمج.",
             ],
             "hint": "لو نفّذت `ON CONFLICT` بشكل صحيح، فإعادة تشغيل الوظيفة من checkpoint قديم لن تُنشئ تكرارًا — اختبر ذلك عمدًا. وللقياس: استخدم 10,000 متابع تجريبيين (`generate_series`) وقس الإدراج كدفعة واحدة مقابل دفعات 500.",
             "solution": "النتيجة: خط زمني يقرأ صفحة في < 20ms بحجم 10 آلاف متابع، وتوزيع ~5,000 صف/ثانية على دفعات. أهم درس: **التحكم في حجم التوزيع** (تقليم + استثناء خاملين + المشاهير) هو ما يجعل التصميم قابلًا للتشغيل، لا اختيار أداة الكاش.",
             "resources": [
                 "https://learn.microsoft.com/azure/architecture/patterns/materialized-view",
                 "https://learn.microsoft.com/ef/core/modeling/indexes",
                 "https://www.postgresql.org/docs/current/sql-insert.html",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Materialized View pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/materialized-view"},
            {"label": "Indexed views / الفهارس المركّبة في EF Core", "url": "https://learn.microsoft.com/ef/core/modeling/indexes"},
            {"label": "ترقيم بالمفاتيح", "url": "https://learn.microsoft.com/azure/architecture/best-practices/api-design"},
            {"label": "PostgreSQL INSERT ON CONFLICT", "url": "https://www.postgresql.org/docs/current/sql-insert.html"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════
# l5 — التقسيم والنسخ والاتساق
# ══════════════════════════════════════════════════════════════════
_L5 = {
    "id": "s9-m1-l5",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "آخر درس في وحدة تصميم الأنظمة، وأكثرها «هندسة»: **التقسيم (Sharding) · النسخ (Replication) · إعادة التوازن** — ومعه السؤال اللي بيتكرر: *ليه بياناتي بتظهر قديمة؟*\n\nهنا تتعلم تختار `shard key` وتبرّرها، وتشرح `replication lag` بأثر ملموس، وتصمّم نقل بيانات **بلا توقف**."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Shard / Partition", "def": "تجزئة أفقية لجدول عبر عقد متعددة. `Shard key` تحدد القطعة. الهدف: حجم وكتابة أكبر من عقدة واحدة."},
            {"term": "Shard key مرشّح", "def": "الحقل الذي تقسم به. الخصائص: توزيع متساوٍ · يظهر في كل استعلام ساخن · لا يُحدَّث · لا يخلق نقاطًا ساخنة."},
            {"term": "Hot shard / skew", "def": "قطعة تحمل حصة أكبر من غيرها (مستخدم ضخم/تاريخ اليوم) → تصبح عنق الزجاجة رغم التوزيع."},
            {"term": "Directory / Lookup service", "def": "خدمة صغيرة تحوّل `key → shard`، تتيح إعادة التوازن بلا إعادة حساب عند العملاء."},
            {"term": "Consistent hashing", "def": "توزيع على حلقة: إضافة/حذف عقدة تنقل ~1/N فقط من المفاتيح بدل إعادة توزيع كامل."},
            {"term": "Replication lag", "def": "تأخر النسخة المتابعة عن الأساسية. ينتج: قراءة قديمة، فقدان بيانات عند failover، واختناق قراءة."},
            {"term": "Read-your-writes", "def": "ضمان أن المستخدم يرى كتابته هو على الأقل. تحقّقه بـ: قراءة من الأساسي بعد الكتابة، أو session stickiness، أو انتظار LSN."},
            {"term": "Failover", "def": "ترقية نسخة بديلة عند فشل الأساسي. خطرها: فقدان كتابات غير منسوخة (RPO>0) أو تقسيم دماغ (split-brain)."},
            {"term": "Dual-write / dual-read", "def": "مرحلة انتقالية: اكتب للقديم والجديد، اقرأ من الجديد مع fallback — أساس الترحيل الآمن."},
            {"term": "Resharding", "def": "إعادة توزيع البيانات على قطع أكثر. تُنفَّذ بـcopy + dual-write + cutover + cleanup."},
            {"term": "Quorum (R+W > N)", "def": "في أنظمة N نسخ: نجاح القراءة/الكتابة عند R/W نسخ. `R+W>N` تعطي تماسكًا أقوى (مثال N=3, R=2, W=2)."},
        ]},

        {"type": "heading", "level": 2, "text": "① اختيار Shard key: 5 معايير وحكم"},
        {"type": "table", "caption": "ثلاثة مرشحين على نظام طلبات",
         "head": ["المفتاح", "التوزيع", "الاستعلامات الساخنة", "الثمن"],
         "rows": [
             ["`customer_id`", "متساوٍ عادةً", "كل استعلامات العميل تصل لقطعة واحدة ✅", "عميل ضخم = hot shard · تقارير كلية تحتاج جولة على كل القطع"],
             ["`order_id` (hash)", "متساوٍ جدًا", "الوصول المباشر ممتاز ✅ لكن «طلبات العميل» تصبح جولة على كل القطع ❌", "استعلامات النطاق مكلفة"],
             ["`created_at` (شهري)", "حسب الزمن ⇒ قطعة اليوم ساخنة", "تقارير زمنية ممتازة", "**أسوأ خيار للكتابة** (كل الكتابات على قطعة واحدة)"],
         ]},
        {"type": "callout", "kind": "tip", "title": "القاعدة الذهبية",
         "md": "**`shard key` = الحقل الموجود في أشهر استعلام + الأكثر توزيعًا.**\nفي نظام SaaS متعدد المستأجرين، `tenant_id` هو الجواب في 90% من الحالات: كل شيء عن مستأجر واحد يقع في مكان واحد، والعزل أسهل، والاحتفاظ/الحذف يصبح أسهل (مقابل: عميل ضخم يحتاج قطعة خاصة — «pinning»).\n**وأي مفتاح تختاره، اكتب قرارك في ADR:** لماذا · ما الثمن · ما الاستعلامات التي أصبحت مكلفة · متى تعيد التقييم."},
        {"type": "code", "lang": "csharp", "title": "Sharding/ShardRouter.cs — توجيه بمفتاح + دليل + قراءة مُقاسة", "filename": "src/Sharding/ShardRouter.cs", "code": r'''/// <summary>
/// توجيه بسيط: hash(tenantId) % N. عيبه: تغيير N يعيد توزيع كل شيء.
/// الحل عند التوسع: consistent hashing أو شاردات منطقية (virtual shards).
/// </summary>
public sealed class ShardRouter(IShardDirectory directory)
{
    public async Task<ShardConnection> ResolveAsync(string tenantId, CancellationToken ct)
    {
        var shardId = await directory.GetShardAsync(tenantId, ct)
            ?? InlineHash(tenantId);
        return await directory.GetConnectionAsync(shardId, ct);
    }

    /// <summary>توزيع محلي حتمي — نفس المستأجر دائمًا نفس القطعة.</summary>
    private static string InlineHash(string tenantId)
    {
        // FNV-1a: سريع وحتمي (لا يعتمد على GetHashCode المتغيّر بين العمليات)
        var hash = 2166136261u;
        foreach (var c in tenantId)
        {
            hash ^= c;
            hash *= 16777619u;
        }
        return $"shard-{hash % 16:D2}";    // 16 قطعة منطقية
    }
}

/// <summary>
/// 16 قطعة منطقية → عدد قليل من قواعد البيانات.
/// إضافة قاعدة جديدة = نقل 3–4 قطع منطقية فقط ⇒ حركة بيانات محدودة.
/// </summary>
public sealed class ShardDirectory(IConfiguration config) 
{
    private static readonly IReadOnlyDictionary<string, string> LogicalToPhysical =
        new Dictionary<string, string>
        {
            ["shard-00"] = "db0", ["shard-01"] = "db0", ["shard-02"] = "db0", ["shard-03"] = "db0",
            ["shard-04"] = "db1", ["shard-05"] = "db1", ["shard-06"] = "db1", ["shard-07"] = "db1",
            ["shard-08"] = "db2", ["shard-09"] = "db2", ["shard-10"] = "db2", ["shard-11"] = "db2",
            ["shard-12"] = "db3", ["shard-13"] = "db3", ["shard-14"] = "db3", ["shard-15"] = "db3",
        };

    public Task<string?> GetShardAsync(string tenantId, CancellationToken ct) =>
        Task.FromResult<string?>($"shard-{Fnv(tenantId) % 16:D2}");

    public Task<ShardConnection> GetConnectionAsync(string shardId, CancellationToken ct)
    {
        var physical = LogicalToPhysical[shardId];
        return Task.FromResult(new ShardConnection(
            physical,
            config.GetConnectionString(physical)!));
    }

    private static uint Fnv(string s)
    {
        var hash = 2166136261u;
        foreach (var c in s) { hash ^= c; hash *= 16777619u; }
        return hash;
    }
}

public sealed record ShardConnection(string ShardId, string ConnectionString);
'''},
        {"type": "table", "caption": "متى لا تُقسّم",
         "head": ["الحالة", "القرار"],
         "rows": [
             ["جدول < 500GB وكتابة < 5k/ث", "**لا تُقسّم** — فهرس + replica + أرشفة"],
             ["تقارير كلية (cross-tenant)", "تُقسّم لكن مع مستودع تحليلي منفصل (OLAP)"],
             ["مشروع جديد غير متأكد من الشكل", "لا تُقسّم — لكن **ضع `tenant_id` في كل جدول من اليوم الأول** (أرخص قرار)"],
             ["حاجة لعزل تنظيمي/إقامة بيانات", "قسّم بحسب المنطقة لا بالحجم"],
         ]},

        {"type": "heading", "level": 2, "text": "② النسخ وreplication lag: من أين تأتي المشكلة"},
        {"type": "code", "lang": "text", "title": "مسار النسخة المتابعة", "filename": "docs/replication.txt", "code": r'''
  كتابة ──► Primary ──(WAL stream)──► Replica1
                  │                    Replica2
                  └──────────────►  Replica3 (تحليلات)

تأخر النسخ (lag) يزداد بسبب:
  1) كتابة كثيفة على الأساسي (WAL أكثر مما تستطيع النسخة تطبيقه)
  2) نسخة مشغولة باستعلامات ثقيلة (تنافس على I/O)
  3) شبكة بين المنطقتين (عبر المناطق = ms عشرات)
  4) نسخة جديدة تبني/تعيد المزامنة

الأثر الملموس (وإن كان lag = 200ms فقط):
  مستخدم ينشئ طلبًا ثم يفتح قائمته فورًا → لا يرى طلبه ⇒ «النظام ضاع بياناتي!»
  الإصلاح: read-your-writes (قراءة من الأساسي لفترة قصيرة أو عبر LSN).
'''},
        {"type": "code", "lang": "csharp", "title": "Replication/ReadYourWrites.cs — تجاوز النسخة المتابعة عند الحاجة", "filename": "src/Sharding/ReadYourWrites.cs", "code": r'''using Microsoft.EntityFrameworkCore;

/// <summary>
/// سياسة قراءة تحترم read-your-writes:
///   • بعد كتابة المستخدم (خلال نافذة قصيرة) ⇒ قراءة من الأساسي.
///   • غير ذلك ⇒ قراءة من نسخة متابعة (أرخص وأسرع).
/// </summary>
public sealed class ReadRouter(
    IDbContextFactory<ShopDbContext> primary,
    IDbContextFactory<ShopDbContext> replica,
    IWriteMarker marker)
{
    public async Task<T> QueryAsync<T>(string userId, Func<ShopDbContext, Task<T>> query, CancellationToken ct)
    {
        var usePrimary = await marker.HasRecentWriteAsync(userId, ct)
            // أول قراءة بعد الكتابة قد تكون على نفس الاتصال المفتوح
            || marker.IsFirstReadAfterWrite(userId);

        await using var db = usePrimary
            ? await primary.CreateDbContextAsync(ct)
            : await replica.CreateDbContextAsync(ct);

        return await query(db);
    }
}

/// <summary>يُستدعى في أي endpoint كتابة: يعلّم أن هذا المستخدم كتب للتو.</summary>
public sealed class WriteMarker(IDistributedCache cache)
{
    private static readonly TimeSpan Window = TimeSpan.FromSeconds(5);

    public async Task MarkAsync(string userId, CancellationToken ct) =>
        await cache.SetStringAsync($"rw:{userId}", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = Window }, ct);

    public async Task<bool> HasRecentWriteAsync(string userId, CancellationToken ct) =>
        await cache.GetStringAsync($"rw:{userId}", ct) is not null;

    public bool IsFirstReadAfterWrite(string userId) => true;   // مبسّط: نعتمد على النافذة
}

/*
 بديل أدق (بلا كاش): بعد الكتابة أعِد LSN/`xmin` ثم في القراءة
 انتظر النسخة حتى تصل لهذا الـLSN:
   SELECT pg_current_wal_insert_lsn();      -- بعد الكتابة
   SELECT pg_last_wal_replay_lsn();         -- على النسخة
   while (replay < target) await Task.Delay(5, ct);
 هذا يضمن الرؤية بدقة وبلا نافذة زمنية عشوائية — لكنه يقيّدك بـPostgreSQL.
*/
'''},
        {"type": "table", "caption": "3 ضمانات اتساق تختار بينها صراحة",
         "head": ["الضمان", "كيف تحققه", "التكلفة"],
         "rows": [
             ["Read-your-writes", "قراءة من الأساسي في نافذة 5 ثوانٍ بعد الكتابة · أو انتظار LSN", "حمل أعلى قليلًا على الأساسي"],
             ["Monotonic reads", "تثبيت المستخدم على نسخة واحدة (sticky بمعرّف الجلسة)", "توزيع أقل كفاءة"],
             ["Consistent prefix", "قراءة من نفس المصدر خلال جلسة/عملية", "تعقيد أقل من SLA دقيق"],
         ]},

        {"type": "heading", "level": 2, "text": "③ إعادة التوازن بلا توقف: 6 مراحل"},
        {"type": "steps", "title": "Resharding دون downtime",
         "items": [
            {"title": "① جهّز الوجهة", "md": "قاعدة/قطعة جديدة بنفس المخطط + فهارس (بلا فهارس غير ضرورية أثناء النسخ — تُنشأ بعده).\n**ناتج:** destination جاهزة ومتاحة للكتابة."},
            {"title": "② انسخ لقطة (snapshot)", "md": "`pg_dump`/لقطة فيزيائية أو `COPY` على دفعات بالليل؛ سجّل **LSN/نقطة البداية**.\n**ناتج:** غالبية البيانات موجودة."},
            {"title": "③ مزامنة الفرق (catch-up)", "md": "طبّق تغييرات WAL منذ LSN (logical replication) أو dual-write من الآن.\n**ناتج:** الفرق صغير وقابل للحاق."},
            {"title": "④ مفتاح التوجيه (Switching)", "md": "حدّث الدليل `tenant → shard` في **ترانزاكشن واحد**؛ اجعل القراءة dual-read (جديد ثم قديم عند الفشل).\n**ناتج:** القراءات تذهب للجديد تدريجيًا (1% → 10% → 100%)."},
            {"title": "⑤ أوقف الكتابة على القديم", "md": "بعد التأكد من صفر فرق (تأخير < ثانية) ومراقبة الأخطاء. أبقِ القديم للقراءة فقط أسبوعًا.\n**ناتج:** rollback ممكن في دقائق."},
            {"title": "⑥ نظّف", "md": "أرشف القديم + أزل dual-write + وثّق. لا تحذف قبل أسبوعين على الأقل.\n**ناتج:** تكلفة أقل وتعقيد أقل."},
         ]},
        {"type": "callout", "kind": "danger", "title": "5 أخطاء في resharding",
         "md": "**① نسخ بلا قياس معدل** — يستهلك I/O ويوقف الإنتاج.\n**② نشر التوجيه لكل العملاء دفعة واحدة** — أي خطأ = انقطاع كامل.\n**③ حذف القديم فورًا** — بلا rollback.\n**④ نسيان الفهارس/القيود/التسلسلات على الوجهة** — أعطال غريبة بعد النقل.\n**⑤ نسيان «المستأجرين المتجولين»** — بيانات تخص مستأجر في قطعة أخرى (تحقق آلي: كل صف يجب أن يطابق shard الخاص بمستأجره)."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تختار `shard key` من الاستعلامات الساخنة لا من الراحة، وتشرح الثمن.",
            "تعرف لماذا `created_at` مفتاح سيئ للكتابة، ومتى يكون مفيدًا (تقارير/أرشفة).",
            "تستخدم قطعًا منطقية أكثر من الفيزيائية لتقليل حركة البيانات.",
            "تشرح `replication lag` بأثر منتج ملموس وليس بتعريف.",
            "تنفّذ read-your-writes بنافذة زمنية أو بانتظار LSN.",
            "تعرف مخاطر failover (RPO>0، split-brain) وكيف تقللها.",
            "تصمّم resharding بـ6 مراحل مع rollback في كل مرحلة.",
            "تعرف متى **لا** تُقسّم وتذكر شرط إعادة النظر رقميًا.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة.",
         "questions": [
             {"q": "اخترت `created_at` كـshard key لجدول أحداث. ما النتيجة؟",
              "options": ["توزيع مثالي", "كل الكتابات على قطعة اليوم = hot shard؛ أما التقارير الزمنية فممتازة",
                          "لا يمكن التقسيم", "تحتاج UUID"],
              "answer": 1,
              "explain": "التقسيم بالزمن يعطي «قطعة واحدة ساخنة» لكل الكتابات الحالية. مناسب للأرشفة/الاحتفاظ (احذف الشهر القديم بسرعة)، غير مناسب للكتابة الحية."},
             {"q": "ما فائدة القطع المنطقية (virtual shards) أكثر من الفيزيائية؟",
              "options": ["أسرع في الاستعلام", "إضافة قاعدة جديدة تنقل عددًا محدودًا من القطع المنطقية بدل إعادة توزيع كل المفاتيح",
                          "تقليل التكلفة فقط", "لا فائدة"],
              "answer": 1,
              "explain": "لو عندك 16 قطعة منطقية على 4 قواعد، فإضافة قاعدة تعني نقل 3–4 قطع منطقية فقط — حركة بيانات محسوبة، وقابلة للتنفيذ تدريجيًا بلا downtime."},
             {"q": "مستخدم ينشئ طلبًا فلا يرى طلبه في القائمة فورًا. السبب والحل؟",
              "options": ["خطأ في الواجهة", "replication lag — اقرأ من الأساسي في نافذة قصيرة بعد الكتابة (read-your-writes)",
                          "فهرس ناقص", "كاش قديم"],
              "answer": 1,
              "explain": "الكتابة ذهبت للأساسي والقراءة من نسخة متأخرة. الحل: نافذة read-your-writes في الكاش، أو انتظار LSN على النسخة — وكلاهما يجب توثيقه كقرار واختباره."},
             {"q": "ما خطر failover بلا فحص تأخير النسخ؟",
              "options": ["لا خطر", "فقدان كتابات لم تُنسخ (RPO>0) وقد يحدث split-brain إذا لم يُعزل القديم",
                          "بطء القراءة", "تكلفة أعلى"],
              "answer": 1,
              "explain": "ترقية نسخة متأخرة تعني فقدان آخر الكتابات. الحلول: quorum/synchronous replication حسب الحاجة، وعزل الأساسي القديم (fencing) لمنع الكتابة المزدوجة."},
             {"q": "أي مرحلة يجب أن تسبق نشر التوجيه الجديد؟",
              "options": ["حذف القديم", "اللحاق الكامل (صفر فرق) + مزامنة الفروق + فحص عدد الصفوف/المجاميع",
                          "إيقاف التطبيق", "زيادة الفهارس على القديم"],
              "answer": 1,
              "explain": "نشر التوجيه قبل اللحاق = قراءات ناقصة. الأمان: تحقق من التطابق (عدد صفوف + checksums + عينات)، ثم نشر التوجيه تدريجيًا مع dual-read."},
             {"q": "متى يكون القرار الصحيح «لا تُقسّم»؟",
              "options": ["دائمًا", "عندما يكون الجدول < 500GB والكتابة < 5k/ث: فهرس + replica + أرشفة كافية",
                          "عند وجود مستأجرين", "عند استخدام PostgreSQL"],
              "answer": 1,
              "explain": "التقسيم يضيف تعقيدًا (استعلامات موزعة، معاملات، إعادة توازن). يُؤجَّل حتى تُستنفد البدائل. لكن ضع `tenant_id` في كل جدول من اليوم الأول — قرار رخيص يفتح الباب لاحقًا."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "قرار تقسيم + خطة ترحيل.",
         "items": [
            {"id": "s9-m1-l5-t1",
             "title": "ADR: shard key وخطة إعادة توازن",
             "md": "اكتب قرار تقسيم لجدول كبير في مشروعك: المفتاح · البدائل · الثمن · خطة إعادة التوازن من 6 مراحل · إجراء rollback.",
             "criteria": [
                 "3 مرشحين للمفتاح مع تحليل (توزيع · استعلام ساخن · hot shard · استعلامات كلية).",
                 "قرار مبرّر + الاستعلامات التي أصبحت مكلفة وطريقة معالجتها.",
                 "تصميم قطع منطقية (N) على قواعد فيزيائية (M) وعدد القطع المنقولة عند التوسع.",
                 "خطة resharding 6 مراحل مع **خطر وrollback لكل مرحلة**.",
                 "ضمان read-your-writes مكتوب (نافذة/LSN) واختبار له.",
                 "حدود إعادة النظر رقميًا (حجم/كتابة/skew).",
                 "سطر «لا نُقسّم الآن لأن…» إن كان هذا القرار.",
             ],
             "hint": "ابدأ بكتابة **أشهر 5 استعلامات** في نظامك ثم ابحث عن الحقل المشترك. لو كانت الاستعلامات تبدأ دائمًا بـ`WHERE tenant_id = @t` فالجواب محسوم. وتذكّر: عميل واحد ضخم قد يحتاج «تثبيتًا» على قطعة خاصة (`pinned shard`) — اذكر ذلك كحالة معالجة لا استثناء مفاجئ.",
             "solution": "القرار النموذجي: `tenant_id` كمفتاح + 16 قطعة منطقية على 4 قواعد + تثبيت العملاء الضخمين + تقارير عبر OLAP. أهم ما في المراجعة: وجود **rollback مكتوب** لكل مرحلة، وحد رقمي لإعادة النظر، وتصريح بالاستعلامات التي ستتألم (تقارير كلية).",
             "resources": [
                 "https://learn.microsoft.com/azure/architecture/patterns/sharding",
                 "https://learn.microsoft.com/azure/architecture/patterns/index-table",
                 "https://www.postgresql.org/docs/current/wal-intro.html",
                 "https://learn.microsoft.com/azure/architecture/patterns/materialized-view",
             ]},
            {"id": "s9-m1-l5-t2",
             "title": "قياس تأخير النسخ واختبار read-your-writes",
             "md": "شغّل PostgreSQL أساسيًا + نسخة متابعة (compose)، قِس التأخير، واكتب اختبارًا يُثبت أن سياسة read-your-writes تُصلح المشكلة.",
             "criteria": [
                 "`compose.yaml` بـPostgreSQL primary + replica.",
                 "قياس `pg_last_wal_replay_lsn()` مقابل `pg_current_wal_insert_lsn()` في تقرير (لقطات).",
                 "إنتاج تأخير مقصود (استعلام ثقيل/`pg_sleep`/كتابة كثيفة) وقياسه رقميًا.",
                 "اختبار يوضح: قراءة من النسخة = لا يرى؛ قراءة من الأساسي = يرى.",
                 "شرح مكتوب لنافذة الـ5 ثوانٍ ومتى يجب استخدام LSN بدلًا منها.",
             ],
             "hint": "أسهل طريقة لتوليد تأخير مقصود: `SELECT pg_wal_replay_pause()` على النسخة، نفّذ كتابات على الأساسي، قِس الفرق، ثم `pg_wal_replay_resume()`. للقياس اليومي استخدم `pg_stat_replication` (عمود `replay_lag`) لا LSN فقط، لأنه يعطيك تأخيرًا زمنيًا مباشرًا.",
             "solution": "النتيجة: تأخير مقاس من 50ms إلى ثوانٍ حسب الحمل. الأهم: إثبات أن السياسة صحيحة — القراءة الفورية من النسخة لا ترى الصف الجديد بينما الأساسي يراه. ثم اختبار يمر: بعد الكتابة، القراءة تذهب للأساسي خلال النافذة، وبعد 5 ثوانٍ تعود للنسخة.",
             "resources": [
                 "https://www.postgresql.org/docs/current/warm-standby.html",
                 "https://www.postgresql.org/docs/current/monitoring-stats.html",
                 "https://learn.microsoft.com/azure/architecture/patterns/cqrs",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Sharding pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/sharding"},
            {"label": "Index Table pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/index-table"},
            {"label": "PostgreSQL: WAL والنسخ", "url": "https://www.postgresql.org/docs/current/wal-intro.html"},
            {"label": "PostgreSQL: Warm Standby", "url": "https://www.postgresql.org/docs/current/warm-standby.html"},
            {"label": "CQRS pattern", "url": "https://learn.microsoft.com/azure/architecture/patterns/cqrs"},
            {"label": "Materialized View", "url": "https://learn.microsoft.com/azure/architecture/patterns/materialized-view"},
        ]},
    ],
}

LESSONS_S9_C = [_L3, _L4, _L5]
