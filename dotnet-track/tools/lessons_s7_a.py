# -*- coding: utf-8 -*-
"""Stage 7 module 1 (part A): s7-m1-l1 (أعمدة المراقبة الثلاثة), s7-m1-l2 (OpenTelemetry في .NET)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s7-m1-l1 — أعمدة المراقبة الثلاثة
# ══════════════════════════════════════════════════════════════════════════
_L1 = {
    "id": "s7-m1-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "«عندنا لوجنج» مش معنى إن النظام قابل للمراقبة. المراقبة بتجاوب على أسئلة، وكل سؤال له **إشارة مناسبة**: هل فيه مشكلة دلوقتي؟ (مقياس) · ليه الطلب ده بطيء؟ (تتبع) · إيه اللي حصل بالظبط في الطلب ده؟ (سجل). في الدرس ده: الفرق الحقيقي بين الأعمدة الثلاثة · إزاي تصنّف كل إشارة عندك · **نماذج RED/USE والإشارات الذهبية** · وإيه اللي تقيسه لكل خدمة في نظام `shop` — مع **التكلفة** كعامل تصميم (لأن أغلى غلطة في المراقبة مش نقص البيانات، بل **cardinality** بترفع الفاتورة وبتبطئ الاستعلامات)."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Log (سجل)", "def": "حدث **منفصل** له وقت ووصف وحقول: «الطلب o-123 فشل بسبب timeout في خدمة الدفع». غني بالتفاصيل، كبير الحجم، وأغلى تخزينًا."},
            {"term": "Metric (مقياس)", "def": "قيمة **مجمّعة عبر الزمن**: عدّاد (requests_total) · توزيع (duration histogram) · قيمة لحظية (queue_depth). صغير الحجم، سريع الاستعلام، ومناسب للتنبيهات."},
            {"term": "Trace (تتبع)", "def": "رحلة طلب واحد عبر الخدمات. مكوّن من **spans** (كل span = وحدة عمل بمدتها وسماتها وأبوه). بيجاوب «أين ضاع الوقت؟»."},
            {"term": "Span", "def": "وحدة داخل الـtrace: اسم · وقت بداية · مدة · سمات (tags) · أحداث (events) · حالة · span أب. مجموع الـspans بيرسم شجرة الرحلة."},
            {"term": "Exemplar", "def": "ربط نقطة في مقياس (مثلًا p99 في هيستوجرام) بـ**trace_id محدد** — يعني من الرسم البياني تقفز مباشرة لرحلة طلب بطيء. ده اللي بيخلي المقياس والتتبع نظامًا واحدًا."},
            {"term": "Cardinality", "def": "عدد السلاسل الزمنية المختلفة = حاصل ضرب قيم السمات. سمة زي `user_id` أو `order_id` بتفجّر العدد لملايين → تكلفة وانهيار أداء."},
            {"term": "Sampling", "def": "أخذ عينة من الـtraces (مثلًا 10%) لتقليل الحجم. **Head sampling** قرار عند البداية؛ **Tail sampling** قرار بعد اكتمال الرحلة (يحتفظ بالأخطاء والبطيئة)."},
            {"term": "RED", "def": "نموذج للخدمات: **Rate** (طلب/ثانية) · **Errors** (نسبة الفشل) · **Duration** (توزيع الزمن). بيركّز على تجربة المستخدم."},
            {"term": "USE", "def": "نموذج للموارد: **Utilization** (نسبة الاستخدام) · **Saturation** (الطابور/الانتظار) · **Errors**. بيركّز على الآلة (CPU · ذاكرة · pool اتصالات · قرص)."},
            {"term": "الإشارات الذهبية الأربع", "def": "Latency · Traffic · Errors · Saturation (من Google SRE) — عمليًا: RED للطلبات + Saturation للموارد."},
            {"term": "Collector", "def": "عملية مستقلة تستقبل الإشارات (receivers) وتعالجها (batch · sampling · حجب بيانات · توحيد سمات) وتصدّرها للخلفيات — يعني تطبيقك ما يعرفش تفاصيل الباك-إند."},
            {"term": "مراقبة مقابل قابلية ملاحظة", "def": "**المراقبة** = أسئلة معروفة مسبقًا (لوحات وتنبيهات). **قابلية الملاحظة** = تقدر تسأل سؤالًا جديدًا عن النظام من غير ما تنشر كودًا."},
        ]},

        # ── 1
        {"type": "heading", "level": 2, "text": "① الفرق الحقيقي: السؤال · الشكل · الحجم · التكلفة"},
        {"type": "table", "caption": "مش «ثلاثة أنواع بيانات» — ثلاثة أدوار مختلفة في التحقيق",
         "head": ["", "**السجل (Log)**", "**المقياس (Metric)**", "**التتبع (Trace)**"],
         "rows": [
             ["السؤال اللي بيجاوبه", "إيه اللي حصل **بالظبط** في هذا الحدث؟", "هل فيه مشكلة **دلوقتي**؟ وكم حجمها؟", "**أين** ضاع الوقت في هذا الطلب؟"],
             ["الشكل", "حدث منفصل بحقول (structured)", "سلسلة زمنية مجمّعة (counter/histogram/gauge)", "شجرة spans برحلة واحدة"],
             ["الحجم لكل طلب", "~200 بايت – 2 KB (حسب الحقول)", "~0 (مجمّع في الذاكرة ثم يُصدَّر كل فترة)", "~0.5 – 5 KB لكل span × عدد الخدمات"],
             ["التكلفة النسبية", "**الأعلى** (استيعاب لكل GB + فهرسة)", "**الأقل** (لو الـcardinality مضبوطة)", "متوسطة (وترتفع بلا sampling)"],
             ["مناسب للتنبيه؟", "ضعيف (بطيء + مكلف للعدّ)", "**نعم — الأساس**", "لا (للتحقيق بعد التنبيه)"],
             ["الاحتفاظ النموذجي", "7–30 يومًا ساخن، ثم بارد/أرشيف", "أسابيع–شهور بدقة مخفّضة (downsampling)", "أيام–أسبوعين (وغالبًا مع sampling)"],
             ["مثال من `shop`", "`order o-123 failed: payment timeout after 8s`", "`http_server_request_duration_seconds_bucket{route=POST /orders}`", "طلب `/orders` → gateway → orders → DB → payments → rabbitmq"],
             ["إمتى **ما ينفعش**", "تحديد «هل الخدمة سليمة؟» (بطيء ومكلف)", "تشخيص حالة **واحدة** محددة (بيفقد التفاصيل)", "مراقبة مستمرة لكل الطلبات بتكلفة منخفضة"],
             ["الترتيب في التحقيق", "٣: التفاصيل النهائية", "١: اكتشاف المشكلة وحجمها", "٢: تحديد المكان (أي خدمة/استعلام)"],
         ]},
        {"type": "callout", "kind": "note", "title": "المثال اللي بيوضح العلاقة (حادث حقيقي الشكل)",
         "md": "**مقياس** بينبّهك: معدل 5xx في `orders` وصل 3% (من 0.1%). **تتبع** بيقولك: 90% من الزمن في span اسمه `Npgsql ExecuteReader` على استعلام `GET /orders/{id}` — يعني المشكلة في قاعدة البيانات مش في الكود. **سجل** بيقولك بالظبط: `timeout: canceling statement due to statement timeout, order=o-123, statement=SELECT … FROM orders JOIN order_items …`. ثلاث إشارات، ثلاث أسئلة، وإجابة واحدة. لو عندك عمود واحد بس، هتقضي ساعتين في التخمين."},

        # ── 2
        {"type": "heading", "level": 2, "text": "② صنّف إشاراتك: 10 أسئلة تشغيلية والإشارة الصح لكل واحد"},
        {"type": "table", "caption": "اكتب الجدول ده لنظامك — هو اللي بيحدد إيه اللي تقيسه فعلًا",
         "head": ["السؤال", "الإشارة", "الاسم/الحقل المحدد", "مستوى التنبيه"],
         "rows": [
             ["هل الخدمة شغالة وتستقبل حركة؟", "مقياس", "`up` / وجود سلاسل `http_server_request_duration_seconds_count`", "حرج (page)"],
             ["كم طلب/ثانية وعلى أي مسارات؟", "مقياس", "`http_server_request_duration_seconds_count` بمعدل + سمة `http.route`", "لا (معلوماتي)"],
             ["ما نسبة الفشل؟", "مقياس", "نسبة `http.response.status_code` في نطاق 5xx", "حرج (SLO — 7.1.5)"],
             ["ما p50/p95/p99 للزمن؟", "مقياس", "`histogram_quantile` على `http_server_request_duration_seconds_bucket`", "تحذير"],
             ["أين يضيع الوقت في الطلب البطيء؟", "تتبع", "span tree + أطول span + exemplar من p99", "لا (تحقيق)"],
             ["لماذا فشل هذا الطلب بالذات؟", "سجل", "`TraceId` + الاستثناء + `OrderId`", "لا (تحقيق)"],
             ["هل القاعدة/الطابور مشبعة؟", "مقياس", "USE: اتصالات مستخدمة/الحد · طول الطابور · عمر أقدم رسالة", "تحذير/حرج"],
             ["هل الـGC أو الـthread pool بيخنق التطبيق؟", "مقياس", "`dotnet_gc_heap_size` · `dotnet_thread_pool_queue_length` · وقت GC", "تحذير"],
             ["هل نسخة واحدة سيئة أم الكل؟", "مقياس + تتبع", "تقسيم على `service.instance.id` / `server.address`", "لا"],
             ["هل التغيير الأخير هو السبب؟", "مقياس + سجل نشر", "مقارنة قبل/بعد النشر (annotation على اللوحة) + `deployments.log`", "لا"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قاعدة التصنيف (لو محتار)",
         "md": "**لو الإجابة رقم يُقارَن عبر الزمن أو يُنبَّه عليه → مقياس. لو الإجابة رحلة/توزيع زمن → تتبع. لو الإجابة تفاصيل حالة واحدة → سجل.** والخطأ الشائع: تحويل السجلات لمقاييس بالعدّ عليها (log-based metrics) — يعمل، بس أبطأ وأغلى وأقل دقة من مقياس أصلي في التطبيق. العدّ على السجلات مقبول كحل مؤقت أو لأحداث نادرة."},

        # ── 3
        {"type": "heading", "level": 2, "text": "③ RED + USE: إيه اللي تقيسه لكل خدمة (من غير ما تخترع)"},
        {"type": "table", "caption": "النموذجين بيكملوا بعض: RED لتجربة المستخدم، USE لصحة الموارد",
         "head": ["النموذج", "البعد", "المقياس في .NET/OTel", "اللوحة", "التنبيه"],
         "rows": [
             ["RED", "**Rate**", "`rate(http_server_request_duration_seconds_count[5m])`", "طلبات/ثانية لكل مسار", "انخفاض مفاجئ (فقدان حركة) — غالبًا منبّه كاذب، فاستخدمه بحذر"],
             ["RED", "**Errors**", "نسبة `status_code` 5xx من الإجمالي", "نسبة الفشل + تفصيل حسب المسار", "**حرج**: SLO burn rate (7.1.5)"],
             ["RED", "**Duration**", "`histogram_quantile(0.95, …)`", "p50/p95/p99", "تحذير: p95 تجاوز ضعف خط الأساس"],
             ["USE", "**Utilization**", "`dotnet_gc_heap_size` / حد الذاكرة · CPU · اتصالات DB مستخدمة", "نسبة من الحد", "تحذير عند 75%، حرج عند 90%"],
             ["USE", "**Saturation**", "طول طابور thread pool · طول طابور RabbitMQ · عمر أقدم رسالة · طلبات منتظرة", "طابور + عمر", "**حرج**: طابور بيكبر لمدة 5 دقائق"],
             ["USE", "**Errors**", "`dotnet_gc_collections` · إعادة محاولات HTTP · dead letters · `db_client_operation_duration` بفشل", "أخطاء موارد", "تحذير: DLQ عمقه > 0"],
             ["إضافي (طوابير)", "**Lag**", "عدد الرسائل غير المستهلكة · زمن المعالجة لكل رسالة", "lag عبر الزمن", "حرج: lag يتجاوز 10 دقائق من الإنتاج"],
             ["إضافي (أعمال)", "**Business KPI**", "`orders_placed_total` · `checkout_completed_total`", "مقارنة بنفس الوقت أمس/الأسبوع", "تحذير: انخفاض > 30% مقابل الأسبوع السابق"],
         ]},
        {"type": "code", "lang": "csharp", "title": "src/ServiceDefaults/Observability.cs — إيه اللي تقيسه لكل خدمة", "filename": "src/ServiceDefaults/Observability.cs", "code": r'''using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace Shop.Observability;

/// <summary>
/// الأدوات (instruments) المخصصة لكل خدمة. القواعد:
///   • الأسماء بصيغة OTel: snake_case مع وحدة واضحة (لا تُضف الوحدة في الاسم لو السمات تكفي).
///   • الوحدات المعيارية: "s" للثواني · "ms" · "By" للبايت · "1" للعدّ · "{order}" للكيانات.
///   • السمات (tags) قليلة ومحدودة القيم — لا معرّفات (user_id/order_id) في سمات المقاييس.
/// </summary>
public sealed class ShopMetrics : IDisposable
{
    // اسم الـMeter هو اللي بتضيفه في AddMeter("Shop.Orders")
    private readonly Meter _meter = new("Shop.Orders", "1.0.0");

    // ── RED: الأخطاء والمدة بيسجلها ASP.NET Core تلقائيًا ──
    // http_server_request_duration_seconds (histogram) + http_server_active_requests

    // ── أعمال: عدّادات بأسماء واضحة ──
    public Counter<long> OrdersPlaced { get; }
    public Counter<long> OrdersFailed { get; }
    public Counter<long> PaymentsRetried { get; }

    // ── موارد/طوابير: قيم لحظية تُقرأ عند الجمع (Observable) ──
    public ObservableGauge<int> OutboxPending { get; }
    public ObservableGauge<double> OldestOutboxMessageAge { get; }

    // ── توزيع زمن لعملية داخلية (مثال: خطوة في الـcheckout) ──
    public Histogram<double> CheckoutStepDuration { get; }

    private readonly Func<int> _outboxCount;
    private readonly Func<double> _oldestAge;

    public ShopMetrics(Func<int> outboxCount, Func<double> oldestAgeSeconds)
    {
        _outboxCount = outboxCount;
        _oldestAge = oldestAgeSeconds;

        OrdersPlaced = _meter.CreateCounter<long>(
            "shop_orders_placed", "{order}", "عدد الطلبات المكتملة");
        OrdersFailed = _meter.CreateCounter<long>(
            "shop_orders_failed", "{order}", "عدد الطلبات الفاشلة");
        PaymentsRetried = _meter.CreateCounter<long>(
            "shop_payments_retried", "1", "عدد محاولات الدفع المعادة");

        OutboxPending = _meter.CreateObservableGauge(
            "shop_outbox_pending", () => _outboxCount(), "{message}",
            "عدد رسائل الـoutbox غير المرسلة — مؤشر صحة الناشر");
        OldestOutboxMessageAge = _meter.CreateObservableGauge(
            "shop_outbox_oldest_age", () => _oldestAge(), "s",
            "عمر أقدم رسالة غير مرسلة — أهم من العدد: بيكشف ناشر متوقف");

        CheckoutStepDuration = _meter.CreateHistogram<double>(
            "shop_checkout_step_duration", "s", "زمن كل خطوة في الـcheckout");
    }

    /// <summary>
    /// السمات المسموحة: قيم محدودة ومعروفة مسبقًا.
    /// ⚠ لا تضع OrderId/CustomerId/Email هنا — دي تنتمي للسجلات والـtrace، مش للمقياس.
    /// </summary>
    public void RecordOrderPlaced(string channel, string paymentProvider) =>
        OrdersPlaced.Add(1,
            new KeyValuePair<string, object?>("shop.order.channel", channel),
            new KeyValuePair<string, object?>("shop.payment.provider", paymentProvider));

    public void RecordStep(string stepName, double seconds, bool ok) =>
        CheckoutStepDuration.Record(seconds,
            new KeyValuePair<string, object?>("shop.checkout.step", stepName),
            new KeyValuePair<string, object?>("shop.checkout.ok", ok));

    public void Dispose() => _meter.Dispose();
}

/// <summary>
/// تتبع مخصص لرحلة أعمال (مش طلب HTTP واحد) — مثلًا saga عبر عدة خدمات.
/// </summary>
public static class ShopTracing
{
    public static readonly ActivitySource Source = new("Shop.Orders", "1.0.0");

    public static Activity? StartCheckout(string orderId, decimal total)
    {
        var activity = Source.StartActivity("checkout", ActivityKind.Internal);
        if (activity is null) return null;          // sampling مفعّل أو لا يوجد مستمع

        // السمات هنا مفصلة ومسموح فيها المعرّفات (الـtrace حجمه محدود ومُعيَّن):
        activity.SetTag("shop.order.id", orderId);
        activity.SetTag("shop.order.total", total);
        activity.SetTag("shop.order.currency", "EGP");
        return activity;
    }

    // تقبل Activity? لأن StartActivity بيرجع null لما مفيش مستمع أو الـsampling رفض:
    public static void AddPaymentEvent(Activity? activity, string provider, string result)
    {
        if (activity is null) return;
        activity.AddEvent(new ActivityEvent("payment_attempted",
            tags: new ActivityTagsCollection
            {
                { "shop.payment.provider", provider },
                { "shop.payment.result", result },
            }));
    }

    public static void Fail(Activity? activity, Exception ex)
    {
        if (activity is null) return;
        activity.SetStatus(ActivityStatusCode.Error, ex.Message);
        activity.SetTag("exception.type", ex.GetType().FullName);
        activity.SetTag("exception.message", ex.Message);   // ⚠ بلا بيانات شخصية
    }
}
'''},

        # ── 4) التكلفة
        {"type": "heading", "level": 2, "text": "④ التكلفة: البند اللي بيقرر تصميم المراقبة"},
        {"type": "table", "caption": "الأرقام تقريبية (أكتوبر 2026) ومختلفة بين المزودين — الفكرة في **النِسَب** لا القيم",
         "head": ["الإشارة", "وحدة الفوترة", "المحرك الأكبر للتكلفة", "التقليل (بالترتيب)"],
         "rows": [
             ["السجلات", "لكل **GB استيعاب** (+ احتفاظ/فهرسة)", "مستوى اللوج (Information على EF Core = كل استعلام) · health checks كل 10 ثوانٍ · stack traces مكررة",
              "① مستوى Warning للمسارات الصاخبة ② استبعاد `/health` و`/alive` ③ sampling للسجلات المتكررة ④ احتفاظ 30 يومًا ⑤ حجب الحقول الكبيرة"],
             ["المقاييس", "لكل **سلسلة زمنية نشطة** (cardinality) أو لكل عينة", "سمات بقيم غير محدودة (`user_id`, `order_id`, `path` بلا قالب, `sql.statement`)",
              "① سمات محدودة القيم ② قوالب المسارات (`/orders/{id}` لا `/orders/123`) ③ `CardinalityLimit` و`TagKeys` ④ حذف المقاييس غير المستخدمة"],
             ["التتبع", "لكل **مليون span** (أو لكل GB)", "100% sampling على خدمة ذات حركة عالية · spans داخلية بلا قيمة · health checks",
              "① head sampling (10% مثلًا) ② **tail sampling** (احتفظ بكل الأخطاء والبطيئة) ③ استبعاد مسارات الفحص ④ تقليل spans الداخلية"],
             ["البنية (الخلفية)", "لكل عقدة/سعة", "تشغيل stack كامل لخدمة واحدة صغيرة",
              "للمشروع الفردي: Aspire Dashboard محليًا + OTLP لخلفية مُدارة صغيرة، أو Prometheus+Grafana على عقدة واحدة"],
         ]},
        {"type": "callout", "kind": "danger", "title": "انفجار الـcardinality: الغلطة اللي بتوقع أنظمة المراقبة",
         "md": "مقياس بسمة `path=/orders/123` بدل `http.route=/orders/{id}` بينتج سلسلة زمنية **لكل طلب** — ملايين السلاسل، استعلامات بطيئة، وفاتورة ضخمة. نفس الشيء لـ`user_id` أو `sql.statement` الكامل أو `exception.message` (فيه معرّفات ونصوص متغيرة). **القاعدة:** سمة المقياس لازم تكون من مجموعة قيم **محدودة ومعروفة مسبقًا** (مسار مُقَوْلَب · اسم عملية · كود حالة · اسم بيئة · نسخة · instance id). المعرّفات والنصوص الحرة مكانها **السجلات والـspans**."},

        # ── 5) الخطة
        {"type": "steps", "title": "⑤ خطة مراقبة لخدمة واحدة من الصفر (6 خطوات)",
         "items": [
             {"title": "1) اكتب 5 أسئلة لازم تجاوبها في 2 دقيقة",
              "md": "مثلًا: هل الخدمة سليمة؟ كم نسبة الفشل؟ ما p95؟ هل الطابور بيتراكم؟ هل النسخة الجديدة أسوأ؟ الأسئلة دي هي **المواصفات** — واللوحات بتتصمم عشانها، مش العكس.",
              "code": ""},
             {"title": "2) اجمع RED من الإطار أولًا (بلا كود)",
              "md": "ASP.NET Core بيصدر `http_server_request_duration_seconds` (histogram فيه status_code وroute) و`http_server_active_requests`. فعّل الـinstrumentation وخلي الباقي يجي مجانًا.",
              "code": "dotnet add package OpenTelemetry.Instrumentation.AspNetCore"},
             {"title": "3) أضف USE للموارد اللي بتملكها",
              "md": "runtime (.NET): GC heap · thread pool · استثناءات. موارد خارجية: اتصالات القاعدة المستخدمة/الحد · طول الطابور · عمر أقدم رسالة · اتصالات HTTP المفتوحة. **عمر أقدم رسالة أهم من العدد**.",
              "code": "dotnet add package OpenTelemetry.Instrumentation.Runtime"},
             {"title": "4) أضف مقاييس أعمال قليلة (2–4)",
              "md": "طلبات مكتملة · عمليات فشل · خطوات رحلة حرجة. الأرقام دي بتخلي المنتج/الدعم يفهموا الحالة من غير ما يقروا لوج.",
              "code": ""},
             {"title": "5) اربط الأعمدة: TraceId في السجلات + exemplars في المقاييس",
              "md": "من اللوحة (p99) → exemplar → الـtrace → السجل المرتبط → الاستثناء. الربط ده بيقلل زمن التشخيص من ساعة لدقائق.",
              "code": ""},
             {"title": "6) اضبط التكلفة قبل ما تكبّر",
              "md": "مستويات لوج · استبعاد `/health` · sampling · حدود cardinality · احتفاظ. وقِس: كم GB/يوم وكم سلسلة زمنية نشطة — واكتب الرقم في `docs/observability.md`.",
              "code": ""},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أقدر أصنّف أي إشارة عندي على العمود الصح وأقول السؤال اللي بتجاوبه.",
            "عارف ترتيب التحقيق: مقياس (اكتشاف) ← تتبع (تحديد المكان) ← سجل (التفاصيل).",
            "أقدر أطبق RED على خدمة وUSE على مواردها، وأعرف إن «عمر أقدم رسالة» أهم من عدد الرسائل.",
            "أعرف أكتب أسماء وأدوات مقاييس بصيغة OTel (وحدات `s`/`By`/`1` وأسماء snake_case).",
            "فاهم خطر الـcardinality وأعرف إزاي أمنعه (مسارات مُقَوْلبة · سمات محدودة · `CardinalityLimit`).",
            "أعرف الفرق بين head وtail sampling وإمتى أستخدم كل واحد.",
            "أقدر أحسب تكلفة تقريبية لكل إشارة وأرتب إجراءات التقليل.",
            "أعرف الفرق بين المراقبة (أسئلة معروفة) وقابلية الملاحظة (أسئلة جديدة).",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الأعمدة والتكلفة.",
         "questions": [
             {"q": "مستخدم اشتكى إن طلب معين فشل. إيه ترتيب الإشارات الأكثر كفاءة؟",
              "options": ["سجل ← مقياس ← تتبع", "**مقياس (هل فيه نمط/كم عدد المتأثرين) ← تتبع (أين ضاع الوقت/أين فشل) ← سجل (التفاصيل بالظبط)**", "تتبع ← سجل ← مقياس", "سجل فقط"],
              "answer": 1,
              "explain": "المقياس بيرخص السؤال الأول (هل ده حالة فردية ولا حادث؟) والتتبع بيحدد المكان، والسجل بيدي التفاصيل. البدء بالسجلات = بحث في ملايين الأسطر بلا دليل."},
             {"q": "ليه `path=/orders/123` في سمة مقياس كارثة؟",
              "options": ["بطيء في الكتابة", "**بينشئ سلسلة زمنية جديدة لكل طلب (انفجار cardinality) → تكلفة ضخمة واستعلامات بطيئة؛ الصح `http.route=/orders/{id}`**", "بيكشف بيانات شخصية", "بيكسر الـhistogram"],
              "answer": 1,
              "explain": "سمة المقياس لازم من مجموعة قيم محدودة. المسار المُقَوْلَب بيديك نفس الفائدة (زمن كل مسار) بسلسلة واحدة. المعرّف ينتمي للسجل/الـspan."},
             {"q": "خدمة مستهلكة لطابور. إيه أهم مقياس لصحتها؟",
              "options": ["عدد الرسائل المستهلكة", "**عمر أقدم رسالة غير معالجة (lag بالزمن)** — العدد ممكن يبقى طبيعيًا بينما الناشر/المستهلك متوقف", "حجم الطابور بالبايت", "عدد المستهلكين"],
              "answer": 1,
              "explain": "عدد الرسائل بيتأثر بمعدل الإنتاج، فممكن يبدو طبيعيًا في كارثة. العمر بيكشف التوقف فورًا، وده سبب إن KEDA بيتوسع على طول الطابور بينما التنبيه بيكون على العمر (6.1.5)."},
             {"q": "exemplar بيحل إيه؟",
              "options": ["يقلل حجم السجلات", "**بيربط نقطة في مقياس (مثلًا عينة من p99) بـtrace_id → تقفز من اللوحة لرحلة طلب حقيقية مباشرة**", "بيستبدل الـsampling", "بيقيس الـcardinality"],
              "answer": 1,
              "explain": "ده اللي بيخلي الأعمدة نظامًا واحدًا بدل ثلاث جزر. يحتاج دعم من الخلفية (Prometheus مع OTLP أو خلفيات مُدارة)."},
             {"q": "tail sampling أفضل من head sampling في إيه؟",
              "options": ["أرخص دايمًا", "**بيقرر بعد اكتمال الرحلة فيحتفظ بكل الأخطاء والطلبات البطيئة ويعيّن عينة من الناجحة** — head بياخد قراره قبل ما يعرف النتيجة", "أسرع", "ما يحتاجش Collector"],
              "answer": 1,
              "explain": "الثمن: tail sampling محتاج Collector بذاكرة كافية لتخزين الرحلات أثناء اكتمالها، وبيأخر التصدير. للمشروع الصغير head sampling بنسبة 10% مع الاحتفاظ بكل الأخطاء في التطبيق كافٍ."},
             {"q": "إيه أغلى إشارة عادةً؟ ولماذا؟",
              "options": ["المقاييس لأنها دائمة", "**السجلات لأنها تُفوتر لكل GB استيعاب، وحجمها بيتضاعف بأخطاء إعداد بسيطة (EF Core على Information · health checks · stack traces)**", "التتبع لأنه لكل طلب", "كلهم متساوون"],
              "answer": 1,
              "explain": "عشان كده أول إجراء لتقليل الفاتورة هو مستوى السجلات واستبعاد مسارات الفحص (6.2.5). المقاييس أرخص بكتير لو الـcardinality مضبوطة."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "خطة مراقبة مكتوبة + قياس فعلي لإشاراتك.",
         "items": [
             {"id": "t1", "title": "مهمة 1: خطة مراقبة لخدمتين (مواصفات قبل الأدوات)",
              "md": "**السياق:** نظام `shop` فيه `orders` و`catalog` + worker على طابور.\n\n**المطلوب:** `docs/observability-plan.md` فيه:\n1. **10 أسئلة تشغيلية** لكل خدمة مرتبة بالأهمية (من «هل هي سليمة؟» لـ«هل النسخة الجديدة أسوأ؟»).\n2. جدول لكل سؤال: الإشارة (مقياس/تتبع/سجل) · **الاسم الدقيق** للمقياس أو الحقل · مستوى التنبيه (page/ticket/لا) · اللوحة اللي هيظهر فيها.\n3. قائمة **المقاييس المطلوبة**: RED (من الإطار) + USE (runtime + موارد خارجية) + 3 مقاييس أعمال + 2 للطابور — مع الوحدة والسمات المسموحة لكل واحد.\n4. **قائمة السمات الممنوعة** صراحةً (معرّفات · نصوص حرة · مسارات غير مُقَوْلبة) مع السبب والبديل لكل واحدة.\n5. تقدير **الحجم**: كم سلسلة زمنية نشطة متوقعة (احسبها: عدد المقاييس × حاصل ضرب قيم السمات) · كم GB سجلات/يوم (احسبها من عدد الأسطر × متوسط الحجم) · كم span/يوم (من عدد الطلبات × عدد الخدمات × نسبة sampling).\n6. خطة **الاحتفاظ والتكلفة**: ساخن/بارد لكل إشارة + رقم شهري تقديري + أول 3 إجراءات تقليل لو تجاوز الحجم التقدير.\n7. مسودة **لوحة واحدة** (اسمها وأقسامها بالترتيب) تجاوب على الأسئلة الخمسة الأولى خلال ثانيتين.",
              "criteria": [
                  "10 أسئلة لكل خدمة مرتبة، وكل سؤال مربوط بإشارة واسم دقيق.",
                  "قائمة مقاييس فيها الوحدة والسمات المسموحة (مش أسماء بس).",
                  "قائمة سمات ممنوعة بالسبب والبديل.",
                  "حساب حجم فعلي لثلاث إشارات (سلاسل زمنية · GB/يوم · spans/يوم) بالافتراضات مكتوبة.",
                  "تقدير تكلفة شهري + 3 إجراءات تقليل مرتبة بالأثر.",
                  "مسودة لوحة بأقسام مرتبة (الأهم أولًا) مع ذكر مكان الـannotations الخاصة بالنشر.",
                  "تمييز صريح بين ما يأتي من الإطار مجانًا وما يحتاج كودًا مخصصًا.",
                  "فقرة عن الربط بين الأعمدة (TraceId في السجل + exemplar في المقياس) وكيف يُستخدم في التحقيق.",
              ],
              "hint": "لحساب السلاسل الزمنية: اضرب قيم السمات. مثال: مقياس HTTP فيه route (10 قيم) × status_code (6) × method (4) × instance (3) = 720 سلسلة — معقول. أضف `user_id` بـ10,000 قيمة = 7.2 مليون سلسلة — كارثة. وللحجم: 200 ألف طلب/يوم × 5 أسطر سجل × 400 بايت ≈ 400 MB/يوم.",
              "solution": "النتيجة النموذجية: الأسئلة الخمسة الأولى (سليمة؟ نسبة الفشل؟ p95؟ الطابور؟ النسخة الجديدة؟) كلها **مقاييس** بتتناسب مع لوحة واحدة: صف أول RED (rate/errors/p95) · صف ثاني USE (ذاكرة/GC · اتصالات القاعدة · thread pool) · صف ثالث الطابور (lag بالعمر · طول · DLQ) · صف رابع أعمال (طلبات مكتملة/فاشلة) · وكله بتقسيم على النسخة والنسخة الفردية، مع annotations من `deployments.log`. الحساب النموذجي: ~1,200 سلسلة زمنية · ~0.4–1 GB سجلات/يوم (قبل الضبط) · ~100 ألف span/يوم مع sampling 10% على 3 خدمات. التكلفة: السجلات هي البند الأكبر؛ أول ثلاثة إجراءات تقليل: مستوى Warning لـEF Core وASP.NET · استبعاد `/health` و`/alive` · احتفاظ 30 يومًا.",
              "resources": [
                  "https://opentelemetry.io/docs/concepts/signals/",
                  "https://sre.google/sre-book/monitoring-distributed-systems/",
                  "https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/",
                  "https://brendangregg.com/usemethod.html",
                  "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics",
                  "https://opentelemetry.io/docs/specs/semconv/",
              ]},
             {"id": "t2", "title": "مهمة 2: اربط الأعمدة الثلاثة في تحقيق واحد (تمرين حادث)",
              "md": "**السياق:** الهدف مش أدوات أكتر — الهدف **زمن تشخيص أقصر**.\n\n**المطلوب:**\n1. تأكد إن خدمتين عندك بتصدروا الإشارات الثلاث (OTLP) لخلفية واحدة (Aspire Dashboard محليًا أو Collector + Prometheus/Grafana + Loki/Seq).\n2. أضف **TraceId/SpanId** لكل سطر سجل (enricher) و`service.instance.id` و`deployment.environment` كـResource attributes.\n3. أضف **exemplars** (أو على الأقل `TraceId` كسمة في سجلات الأخطاء) بحيث من أي خطأ تقدر توصل للـtrace.\n4. احقن عطلًا متعمدًا (مثلًا: استعلام بلا فهرس أو `Task.Delay(4000)` في مسار) واضرب حملًا بسيطًا.\n5. **سجّل التحقيق كقصة زمنية** في `docs/incident-drill.md`: الوقت · الإشارة اللي كشفت · السؤال التالي · الإشارة اللي جاوبت · الوقت الكلي من الاكتشاف لمعرفة السبب الجذري.\n6. قارن: نفّذ نفس التحقيق **بالسجلات فقط** (عطّل المقياس والتتبع مؤقتًا) وسجّل الزمن — واكتب الفرق.\n7. استنتج 3 تحسينات على خطة المهمة 1 بناءً على التجربة (مثال: مقياس ناقص · سمة مفقودة · لوحة مش واضحة).",
              "criteria": [
                  "الإشارات الثلاث ظاهرة في خلفية واحدة ومترابطة (مش ثلاث جزر).",
                  "كل سطر سجل فيه TraceId (ومُثبت بلقطة/مخرج).",
                  "Resource attributes فيها `service.name` و`service.version` و`deployment.environment` و`service.instance.id`.",
                  "عطل متعمد + حمل + تحقيق موثق **بأزمنة** (اكتشاف · تحديد · سبب جذري).",
                  "مقارنة «السجلات فقط» مقابل «الأعمدة الثلاثة» برقمين زمنيين.",
                  "3 تحسينات مستنتجة من التجربة ومكتوبة في خطة المراقبة.",
                  "ملاحظة عن حجم البيانات الناتجة عن التمرين وإجراءات التقليل المطبقة.",
              ],
              "hint": "أسهل stack محلي: Aspire Dashboard (OTLP على 4317/18889) للـtraces+logs+metrics، أو `otel/opentelemetry-collector-contrib` + Prometheus + Grafana + Loki في Compose. وللحصول على exemplars في Grafana من Prometheus، يحتاج Prometheus استقبال OTLP (مفعّل في الإصدارات الحديثة) — ولو مش متاح، يكفي أن يكون TraceId في السجلات.",
              "solution": "النتائج النموذجية: مع الأعمدة الثلاثة الزمن من التنبيه لمعرفة السبب = **3–8 دقائق** (مقياس يكشف نسبة 5xx ← exemplar/trace يحدد span الاستعلام ← سجل فيه نص الاستعلام والـOrderId). بالسجلات فقط = **20–45 دقيقة** (بحث نصي في آلاف الأسطر ومحاولة ربط الأحداث يدويًا). التحسينات الشائعة بعد التمرين: (1) إضافة مقياس `db_client_operation_duration` لأن الـtrace كان بيظهر span بلا تفاصيل الاستعلام (2) قَوْلبة المسارات لأن `path` كان بيفجّر الـcardinality (3) نقل health checks من مستوى Information لاستبعاد كامل لأنهم كانوا 40% من حجم السجلات.",
              "resources": [
                  "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel",
                  "https://aspire.dev/",
                  "https://opentelemetry.io/docs/collector/",
                  "https://grafana.com/docs/loki/latest/",
                  "https://sre.google/workbook/example-postmortem/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "OpenTelemetry: مفاهيم الإشارات", "url": "https://opentelemetry.io/docs/concepts/signals/"},
            {"label": "Google SRE: مراقبة الأنظمة الموزعة", "url": "https://sre.google/sre-book/monitoring-distributed-systems/"},
            {"label": "طريقة RED (Grafana)", "url": "https://grafana.com/blog/2018-08-02/the-red-method-how-to-instrument-your-services/"},
            {"label": "طريقة USE (Brendan Gregg)", "url": "https://brendangregg.com/usemethod.html"},
            {"label": "مقاييس .NET (System.Diagnostics.Metrics)", "url": "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics"},
            {"label": "الاتفاقيات الدلالية لـOTel", "url": "https://opentelemetry.io/docs/specs/semconv/"},
            {"label": "Sampling في OTel", "url": "https://opentelemetry.io/docs/concepts/sampling/"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s7-m1-l2 — OpenTelemetry في .NET
# ══════════════════════════════════════════════════════════════════════════
_L2 = {
    "id": "s7-m1-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "درس 5.3.2 كان «شغّل التتبع». الدرس ده هو **الإتقان**: بنية OTel في .NET (API/SDK/Exporter/Collector) · الأدوات الفعلية (`ActivitySource` · `Meter` · الـinstruments الستة) · **نشر السياق** عبر HTTP وgRPC والطوابير والمهام الخلفية · ربط السجلات بالتتبع · الـsampling وحدود الـcardinality · والـCollector كطبقة تحكم. ومع كل جزء: **الأخطاء اللي بتخلي التتبع يظهر مقطّعًا أو ما يظهرش خالص** — لأن 90% من مشاكل OTel إعدادات مش كود."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "OTel API مقابل SDK", "def": "**API** = الواجهات اللي بيستخدمها كود المكتبات (بلا تنفيذ). **SDK** = التنفيذ (معالجة · دفعات · تصدير). تطبيقك يسجّل SDK مرة واحدة؛ المكتبات تستخدم API فقط."},
            {"term": "`Activity` / `ActivitySource`", "def": "نوع .NET الأساسي (`System.Diagnostics`) المكافئ لـspan: `ActivitySource.StartActivity` بينشئ span لو فيه مستمع. الـSDK بيستمع لمصادر محددة بـ`AddSource`."},
            {"term": "`Meter` / instruments", "def": "ستة أدوات: `Counter` · `UpDownCounter` · `Histogram` · `Gauge` (لحظي) · `ObservableCounter` · `ObservableGauge` · `ObservableUpDownCounter` — بتُقاس عند الجمع بدل ما تُسجّل."},
            {"term": "W3C trace context", "def": "البروتوكول الافتراضي لنشر السياق: هيدر `traceparent` (و`tracestate`) — بدونه كل خدمة بتعمل trace منفصل وتشوف «رحلات مقطّعة»."},
            {"term": "Baggage", "def": "حقول key-value بتنتقل مع السياق عبر الخدمات (مثلًا `tenant_id`). **احذر**: بتتبعت لكل span وبتزيد الحجم — استخدمها للقليل الضروري."},
            {"term": "Resource", "def": "سمات ثابتة للعملية كلها: `service.name` · `service.version` · `deployment.environment` · `service.instance.id` · `host.name`. بتُضبط مرة بـ`ConfigureResource`."},
            {"term": "OTLP", "def": "بروتوكول التصدير: **gRPC على 4317** أو **HTTP/protobuf على 4318**. أهم سبب لفشل التصدير: خلط البروتوكولين أو المنفذين."},
            {"term": "`UseOtlpExporter()`", "def": "تسجيل **مقطع عرضي** لكل الإشارات الثلاث بمكالمة واحدة (من 1.8) — ويقرأ `OTEL_EXPORTER_OTLP_*` من البيئة. **لا يمكن جمعه مع `AddOtlpExporter` لكل إشارة**: بيرمي `NotSupportedException`."},
            {"term": "Semantic conventions", "def": "أسماء سمات ومقاييس معيارية (`http.route` · `db.system` · `server.address`). الالتزام بيها بيخلي اللوحات الجاهزة تعمل من غير تعديل."},
            {"term": "Tail sampling", "def": "قرار الاحتفاظ بالـtrace بعد اكتماله (في Collector): احتفظ بكل الأخطاء وبطء > x ms، وعيّنة من الباقي."},
            {"term": "Zero-code instrumentation", "def": "وكيل `opentelemetry-dotnet-instrumentation` بيضيف تتبع/مقاييس من غير تعديل الكود (يدعم .NET 10 ومقاييس ASP.NET Core 10) — مفيد لأنظمة قديمة أو للتجربة."},
        ]},

        # ── 1) البنية
        {"type": "heading", "level": 2, "text": "① البنية: من `Activity` في كودك إلى الخلفية"},
        {"type": "code", "lang": "text", "title": "مسار الإشارة (افهمه مرة، وشخّص للأبد)", "filename": "docs/otel-pipeline.txt", "code": r'''  كودك                     OTel API/SDK داخل العملية              خارج العملية
 ┌────────────────┐   ┌───────────────────────────────────┐   ┌──────────────────────┐
 │ ActivitySource │──▶│ TracerProvider                     │   │ Collector (اختياري)   │
 │  .StartActivity│   │  • Sampler (ParentBased/TraceIdRatio)│──▶│ receivers: otlp      │
 │ Meter          │──▶│  • Processor (Batch)               │OTLP│ processors:          │
 │  .Counter/     │   │  • SpanProcessor limits            │4317│  • batch             │
 │   Histogram    │   │  • Resource (service.name …)       │   │  • memory_limiter    │
 │ ILogger        │──▶│ MeterProvider (readers/views)      │   │  • tail_sampling     │
 │                │   │ LoggerProvider                     │   │  • attributes/redaction│
 └────────────────┘   └───────────────┬───────────────────┘   │ exporters:           │
                                      │                        │  • otlphttp → الخلفية │
             نشر السياق               │                        │  • prometheusremotewrite│
     traceparent / tracestate ────────┼───▶ الخدمة التالية    │  • loki / debug      │
                                      │                        └──────────┬───────────┘
                                      ▼                                   ▼
                              (بدون Collector: تصدير مباشر)      Prometheus · Grafana · Jaeger
                                                                 App Insights · Aspire Dashboard · Loki

 نقاط الفشل الأشهر على المسار:
   ① AddSource ناقص → الـspans المخصصة لا تُجمع
   ② Sampler = 0 أو AlwaysOff → لا شيء يُصدَّر
   ③ بروتوكول/منفذ غلط (4317 gRPC مقابل 4318 HTTP) → فشل صامت أو 404
   ④ UseOtlpExporter + AddOtlpExporter معًا → NotSupportedException
   ⑤ traceparent لا يُمرَّر عبر الطابور/الـgRPC → traces مقطّعة
   ⑥ memory_limiter غير مضبوط في Collector → إعادة تشغيل/فقدان بيانات
'''},

        # ── 2) المشروع
        {"type": "heading", "level": 2, "text": "② الحزم والتسجيل الكامل"},
        {"type": "code", "lang": "xml", "title": "src/ServiceDefaults/ServiceDefaults.csproj (إصدارات أكتوبر 2026)", "filename": "src/ServiceDefaults/ServiceDefaults.csproj", "code": r'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsAspireSharedProject>true</IsAspireSharedProject>
  </PropertyGroup>

  <ItemGroup>
    <FrameworkReference Include="Microsoft.AspNetCore.App" />
  </ItemGroup>

  <ItemGroup>
    <!-- الحالة في أكتوبر 2026: OpenTelemetry .NET مستقر في الإشارات الثلاث
         (Traces · Metrics · Logs) — والمشروع تخرّج من CNCF في مايو 2026.
         ثبّت الإصدارات وراجع CHANGELOG قبل الترقية الكبرى. -->
    <PackageReference Include="Microsoft.Extensions.Http.Resilience" Version="10.0.0" />
    <PackageReference Include="Microsoft.Extensions.ServiceDiscovery" Version="10.0.0" />

    <PackageReference Include="OpenTelemetry" Version="1.20.*" />
    <PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.20.*" />
    <PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.20.*" />
    <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.15.*" />
    <PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.15.*" />
    <PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.15.*" />
    <!-- لقاعدة البيانات: يضيف db.* spans ومقاييس -->
    <PackageReference Include="OpenTelemetry.Instrumentation.SqlClient" Version="1.15.*" />
    <!-- للتشخيص المحلي فقط (لا تُصدره للإنتاج): -->
    <PackageReference Include="OpenTelemetry.Exporter.Console" Version="1.20.*" />

    <!-- ⚠ OpenTelemetry.Exporter.Prometheus.AspNetCore ما زال **beta/prerelease**
         ومبني على مواصفة OpenMetrics التجريبية. للإنتاج: صدّر OTLP لـCollector
         وخلّي الـCollector يحوّل لـPrometheus (remote write أو OTLP receiver). -->
  </ItemGroup>
</Project>
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — التسجيل الكامل (traces + metrics + logs)", "filename": "src/Orders.Api/Program.cs", "code": r'''using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Shop.Observability;

var builder = WebApplication.CreateBuilder(args);

// ── 1) المورد: هوية الخدمة (بيظهر في كل إشارة) ──
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r
        .AddService(
            serviceName: "orders-api",
            serviceVersion: typeof(Program).Assembly.GetName().Version?.ToString() ?? "0.0.0",
            serviceInstanceId: Environment.MachineName)
        // البيئة من الإعدادات — مهم لفصل dev/prod في نفس الخلفية:
        .AddAttributes(new Dictionary<string, object>
        {
            ["deployment.environment.name"] = builder.Environment.EnvironmentName,
            ["shop.tier"] = builder.Configuration["Shop:Tier"] ?? "standard",
        }))

    // ── 2) التتبع ──
    .WithTracing(t => t
        // instrumentation جاهزة:
        .AddAspNetCoreInstrumentation(o =>
        {
            // استبعد مسارات الفحص — أكبر مصدر ضجيج وتكلفة (7.1.1):
            o.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health")
                           && !ctx.Request.Path.StartsWithSegments("/alive");
            // سمات إضافية على span الطلب:
            o.EnrichWithHttpRequest = (act, req) => act.SetTag("http.scheme", req.Scheme);
            // سجل الاستثناءات كـevents:
            o.RecordException = true;
        })
        .AddHttpClientInstrumentation(o => o.RecordException = true)
        .AddSqlClientInstrumentation(o =>
        {
            o.SetDbStatementForText = true;   // نص SQL — ⚠ فيه بيانات؛ احجبه في Collector لو لازم
            o.RecordException = true;
        })
        // مصادرك المخصصة (من 7.1.1):
        .AddSource("Shop.Orders")
        .AddSource("Shop.Workers")
        // ⚠ نسيان AddSource = الـspans المخصصة لا تُجمع (أشهر سبب لـ«التتبع ناقص»)
        .SetSampler(new ParentBasedTraceIdRatioSampler(
            builder.Configuration.GetValue("Telemetry:SampleRatio", 0.1)))
        // ⚠ لو اخترت UseOtlpExporter() (الأسلوب المقطعي بالأسفل) فاحذف AddOtlpExporter من هنا.
        .AddOtlpExporter())

    // ── 3) المقاييس ──
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()          // GC · thread pool · استثناءات · ذاكرة
        .AddMeter("Shop.Orders")
        .AddMeter("Microsoft.AspNetCore.Hosting")
        .AddMeter("Microsoft.AspNetCore.Server.Kestrel")
        .AddMeter("System.Net.Http")
        .AddMeter("System.Net.NameResolution")
        // view واحد لكل أداة (view مكرر على نفس الاسم = تعارض):
        // يجمع حدود الهيستوجرام + حد الـcardinality + السمات المسموحة معًا.
        // الوحدة بالثواني حسب اتفاقية OTel — لا تخلط ms مع s في نفس المقياس.
        .AddView("http_server_request_duration_seconds", new ExplicitBucketHistogramConfiguration
        {
            Boundaries = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
            CardinalityLimit = 2000,
            TagKeys = ["http.route", "http.request.method", "http.response.status_code",
                       "network.protocol.version", "server.address", "error.type"],
        })
        .AddView("shop_checkout_step_duration", new ExplicitBucketHistogramConfiguration
        {
            Boundaries = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
        })
        .AddOtlpExporter())

    // ── 4) السجلات (stable في OTel .NET) ──
    .WithLogging(l => l
        .AddOtlpExporter())   // أو استخدم Serilog sink (7.1.3) — اختر مسارًا واحدًا
    ;

// ── البديل المختصر: تسجيل مقطعي لكل الإشارات من متغيرات البيئة ──
// OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
// OTEL_SERVICE_NAME=orders-api  ·  OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=prod
//
// ⚠ قاعدة صارمة: UseOtlpExporter() وAddOtlpExporter() لكل إشارة
//    **لا يجتمعان** → NotSupportedException عند الإقلاع.
//    ولو مشروعك بيستخدم Aspire ServiceDefaults فهو بيسجل UseOtlpExporter تلقائيًا
//    لما OTEL_EXPORTER_OTLP_ENDPOINT موجود — فاختار أحد الأسلوبين (5.3.1/5.3.2).
// builder.Services.AddOpenTelemetry().UseOtlpExporter();

var app = builder.Build();

// /metrics عبر Prometheus exporter = **beta**: استخدمه محليًا،
// وفي الإنتاج صدّر OTLP لـCollector (7.1.4).
app.MapDefaultEndpoints();
app.Run();
'''},

        # ── 3) أدوات مخصصة
        {"type": "heading", "level": 2, "text": "③ الأدوات المخصصة: spans ومقاييس بتاعتك"},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Api/CheckoutService.cs — instrumentation صحيح", "filename": "src/Orders.Api/CheckoutService.cs", "code": r'''using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace Shop.Orders;

public sealed class CheckoutService(ShopMetrics metrics, PaymentClient payments, ILogger<CheckoutService> log)
{
    public async Task<CheckoutResult> CheckoutAsync(CheckoutRequest req, CancellationToken ct)
    {
        // ── span لكل وحدة عمل ذات معنى (لا لكل دالة) ──
        using Activity? activity = ShopTracing.StartCheckout(req.OrderId, req.Total);
        if (activity is not null)
        {
            activity.SetTag("shop.checkout.items", req.Items.Count);
        }

        try
        {
            // خطوة 1: تحقق من المخزون — span فرعي (الابن تلقائي من السياق الحالي)
            var reserved = await WithStepAsync("reserve_stock", req.OrderId,
                () => payments.ReserveStockAsync(req, ct), ct);
            if (!reserved)
            {
                metrics.RecordStep("reserve_stock", 0, ok: false);
                return CheckoutResult.Failed("out_of_stock");
            }

            // خطوة 2: الدفع (استدعاء HTTP — HttpClientInstrumentation بيعمل span تلقائيًا)
            var sw = ValueStopwatch.StartNew();
            var paid = await payments.ChargeAsync(req, ct);
            metrics.RecordStep("charge_payment", sw.GetElapsedTime().TotalSeconds, paid);
            ShopTracing.AddPaymentEvent(activity, "stripe", paid ? "ok" : "declined");

            if (!paid) return CheckoutResult.Failed("payment_declined");

            metrics.RecordOrderPlaced(req.Channel, req.PaymentProvider);
            log.LogInformation("Order {OrderId} placed for {Amount} {Currency}",
                req.OrderId, req.Total, "EGP");          // ← سجل مهيكَل بحقول قابلة للبحث
            return CheckoutResult.Ok(req.OrderId);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            if (activity is not null) ShopTracing.Fail(activity, ex);
            metrics.OrdersFailed.Add(1,
                new KeyValuePair<string, object?>("shop.failure.kind", Classify(ex)));
            log.LogError(ex, "Checkout failed for {OrderId}", req.OrderId);
            throw;
        }
    }

    /// <summary>نمط مساعد: span + مقياس + تسجيل خطأ لكل خطوة.</summary>
    private static async Task<T> WithStepAsync<T>(string step, string orderId,
        Func<Task<T>> action, CancellationToken ct)
    {
        using var activity = ShopTracing.Source.StartActivity($"checkout.{step}", ActivityKind.Internal);
        activity?.SetTag("shop.checkout.step", step);
        activity?.SetTag("shop.order.id", orderId);

        var sw = ValueStopwatch.StartNew();
        try
        {
            return await action();
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.RecordException(ex);
            throw;
        }
        finally
        {
            activity?.SetTag("shop.step.duration_s", sw.GetElapsedTime().TotalSeconds);
        }
    }

    /// <summary>
    /// تصنيف مبسط للفشل — سمة مقياس بقيم محدودة (لا رسالة الاستثناء النصية!).
    /// </summary>
    private static string Classify(Exception ex) => ex switch
    {
        TimeoutException => "timeout",
        HttpRequestException => "http",
        InvalidOperationException => "state",
        _ => "unknown",
    };
}

public record CheckoutRequest(string OrderId, decimal Total, IReadOnlyList<string> Items,
    string Channel, string PaymentProvider);
public record CheckoutResult(bool Ok, string? OrderId, string? Reason)
{
    public static CheckoutResult Ok(string id) => new(true, id, null);
    public static CheckoutResult Failed(string reason) => new(false, null, reason);
}
'''},

        # ── 4) النشر عبر الحدود
        {"type": "heading", "level": 2, "text": "④ نشر السياق: HTTP وgRPC والطوابير والمهام الخلفية"},
        {"type": "table", "caption": "أين ينتشر السياق تلقائيًا وأين تحتاج كودًا",
         "head": ["الحد", "تلقائي؟", "الآلية", "لو مش شغال"],
         "rows": [
             ["HTTP صادر بـ`HttpClient`/`IHttpClientFactory`", "**نعم** (مع `AddHttpClientInstrumentation`)",
              "هيدر `traceparent` يُحقن تلقائيًا", "تأكد إنك بتستخدم `HttpClient` من المصنع (مش `new HttpClient`) وإن `Propagator` افتراضي W3C"],
             ["HTTP وارد لـASP.NET Core", "**نعم**", "قراءة `traceparent` وإنشاء span أب", "لو فيه proxy بيحذف الهيدرز → ضبط الـgateway"],
             ["gRPC", "**نعم** (يستخدم HTTP/2 نفسه)", "`traceparent` في metadata", "تحقق من `Grpc.Net.Client` مع `HttpClient` مُعدَّن"],
             ["**RabbitMQ / طوابير**", "**جزئيًا** — MassTransit بينشر السياق تلقائيًا، لكن الرسائل اليدوية تحتاج كودًا",
              "هيدرز الرسالة: `traceparent` + `tracestate`", "احقن يدويًا عند النشر واقرأه عند الاستهلاك (الكود بالأسفل)"],
             ["Kafka", "حسب المكتبة", "هيدرز السجل (record headers)", "نفس نمط الطوابير"],
             ["`BackgroundService` / مهام مجدولة", "**لا** — مفيش طلب وارد", "ابدأ root activity بنفسك + `Baggage` لو محتاج", "الكود بالأسفل"],
             ["Blazor/SignalR", "جزئي", "حسب الإصدار والرسالة", "ابدأ span لكل عملية أعمال"],
             ["قاعدة بيانات (ADO.NET/EF)", "**نعم** مع `AddSqlClientInstrumentation`", "span ابن للعملية الحالية", "النص الكامل لـSQL يتحكم فيه `SetDbStatementForText`"],
         ]},
        {"type": "code", "lang": "csharp", "title": "src/Shop.Messaging/TracePropagation.cs — نشر السياق عبر الطابور", "filename": "src/Shop.Messaging/TracePropagation.cs", "code": r'''using System.Diagnostics;
using System.Text;
using RabbitMQ.Client;           // ⚠ الإصدار 7.x غيّر بعض الـAPIs لنمط غير متزامن —
using RabbitMQ.Client.Events;    //   تحقق من التواقيع في إصدارك (النمط هنا يوضح الفكرة).

namespace Shop.Messaging;

/// <summary>
/// نشر W3C trace context عبر رسائل RabbitMQ — بدونه الـtrace بينقطع عند الطابور
/// وبتشوف «رحلتين منفصلتين» بدل رحلة واحدة.
/// (MassTransit بيعمل ده تلقائيًا — الكود ده للرسائل اليدوية أو للفهم.)
/// </summary>
public static class TracePropagation
{
    private const string TraceParent = "traceparent";
    private const string TraceState = "tracestate";

    // ── عند النشر ──
    public static void Inject(IBasicProperties props)
    {
        props.Headers ??= new Dictionary<string, object?>();

        // W3C Propagator الافتراضي بيكتب traceparent من Activity.Current:
        var headers = new Dictionary<string, string>();
        Propagators.DefaultTextMapPropagator.Inject(
            new PropagationContext(Activity.Current?.Context ?? default, Baggage.Current),
            carrier: headers,
            setter: (carrier, key, value) => carrier[key] = value);

        foreach (var (k, v) in headers) props.Headers[k] = Encoding.UTF8.GetBytes(v);
    }

    // ── عند الاستهلاك ──
    public static Activity? ExtractAndStart(BasicDeliverEventArgs args, string operationName)
    {
        var headers = new Dictionary<string, string>();
        if (args.BasicProperties.Headers is not null)
        {
            foreach (var kv in args.BasicProperties.Headers)
            {
                headers[kv.Key] = kv.Value switch
                {
                    byte[] b => Encoding.UTF8.GetString(b),
                    string s => s,
                    _ => kv.Value?.ToString() ?? string.Empty,
                };
            }
        }

        var ctx = Propagators.DefaultTextMapPropagator.Extract(
            new PropagationContext(default, Baggage.Empty),
            carrier: headers,
            getter: (carrier, key) =>
                carrier.TryGetValue(key, out var v) ? new[] { v } : Enumerable.Empty<string>());

        // span من نوع Consumer وأبوه هو سياق الرسالة → الرحلة تتصل:
        var activity = new Activity(operationName)
            .SetParentId(ctx.ActivityContext.TraceId, ctx.ActivityContext.SpanId, ctx.ActivityContext.TraceFlags)
            .SetKind(ActivityKind.Consumer)
            .Start();

        foreach (var kv in ctx.Baggage) activity.SetBaggage(kv.Key, kv.Value);
        activity.SetTag("messaging.system", "rabbitmq");
        activity.SetTag("messaging.operation", "receive");
        return activity;
    }
}

/// <summary>مهمة خلفية: مفيش طلب وارد، فابدأ root activity بنفسك.</summary>
public sealed class OutboxDispatcherWorker(IServiceScopeFactory scopes, ILogger<OutboxDispatcherWorker> log)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            // root span لكل دورة — بدونه الشغل الخفي لا يظهر في أي trace:
            using var activity = new Activity("outbox.dispatch_cycle")
                .SetKind(ActivityKind.Internal)
                .Start();
            activity.SetTag("shop.worker", "outbox");

            try
            {
                using var scope = scopes.CreateScope();
                var dispatcher = scope.ServiceProvider.GetRequiredService<IOutboxDispatcher>();
                var sent = await dispatcher.DispatchPendingAsync(ct);
                activity.SetTag("shop.outbox.sent", sent);
            }
            catch (OperationCanceledException) { /* إيقاف لطيف (6.1.5) */ }
            catch (Exception ex)
            {
                activity.SetStatus(ActivityStatusCode.Error, ex.Message);
                activity.RecordException(ex);
                log.LogError(ex, "Outbox dispatch cycle failed");
            }

            await Task.Delay(TimeSpan.FromSeconds(2), ct);
        }
    }
}
'''},

        # ── 5) ربط السجلات
        {"type": "heading", "level": 2, "text": "⑤ ربط السجلات بالتتبع (أعلى عائد استثمار في الدرس)"},
        {"type": "code", "lang": "csharp", "title": "Log correlation — TraceId في كل سطر", "filename": "src/ServiceDefaults/LogCorrelation.cs", "code": r'''using Serilog;
using Serilog.Configuration;
using Serilog.Core;
using Serilog.Events;
using System.Diagnostics;

namespace Shop.Observability;

/// <summary>
/// يضيف TraceId/SpanId لكل سطر سجل من Activity.Current.
/// النتيجة: من أي خطأ في اللوج → انسخ الـTraceId → افتح الرحلة كاملة.
/// (بديل جاهز: Serilog.Enrichers.Span — تحقق من توافقه مع إصدارك.)
/// </summary>
public sealed class TraceContextEnricher : ILogEventEnricher
{
    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        var current = Activity.Current;
        if (current is null) return;

        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("TraceId", current.TraceId.ToString()));
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("SpanId", current.SpanId.ToString()));
        if (current.ParentSpanId != default)
            logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("ParentSpanId", current.ParentSpanId.ToString()));
    }
}

public static class LoggerEnrichmentConfigurationExtensions
{
    public static LoggerConfiguration WithTraceContext(this LoggerEnrichmentConfiguration cfg) =>
        cfg.With<TraceContextEnricher>();
}

/* الإعداد في Program.cs:
   Log.Logger = new LoggerConfiguration()
       .Enrich.FromLogContext()
       .Enrich.WithTraceContext()                       // ← الربط
       .Enrich.WithProperty("service", "orders-api")
       .Enrich.WithProperty("environment", builder.Environment.EnvironmentName)
       .WriteTo.Console(outputTemplate:
           "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} " +
           "{TraceId}{NewLine}{Exception}")              // ← يظهر في السطر
       .WriteTo.OpenTelemetry(...)                      // (7.1.3)
       .CreateLogger();

   ولو بتستخدم OTel logs مباشرة (WithLogging) فـSDK بيضيف TraceId/SpanId تلقائيًا
   كحقول في سجل OTLP — بس output template في الكونسول لسه محتاج {TraceId}.
*/
'''},

        # ── 6) Collector
        {"type": "heading", "level": 2, "text": "⑥ Collector: طبقة التحكم اللي بتنقذك"},
        {"type": "code", "lang": "yaml", "title": "otel/collector-config.yaml", "filename": "otel/collector-config.yaml", "code": r'''# Collector = مكان واحد تتحكم منه في: الدفعات · الذاكرة · الـsampling · حجب البيانات · الخلفيات.
# الصورة: otel/opentelemetry-collector-contrib (فيه معالجات tail_sampling وredaction).
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  # ① حماية الذاكرة أولًا (بدونه Collector بياخد كل الذاكرة ويعيد التشغيل):
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 25

  # ② دفعات لتقليل عدد الطلبات:
  batch:
    timeout: 5s
    send_batch_size: 1024

  # ③ حجب البيانات الحساسة من السمات والسجلات:
  attributes/redact:
    actions:
      - key: db.statement
        action: hash            # أو delete — القرار حسب سياستك (7.2.5)
      - key: http.request.header.authorization
        action: delete
      - key: shop.customer.email
        action: hash

  # ④ توحيد السمات (بيئة/إصدار) لو التطبيق ما بيبعتهاش:
  resource:
    attributes:
      - key: deployment.environment.name
        from_attribute: environment
        action: upsert

  # ⑤ tail sampling: احتفظ بكل الأخطاء والبطيئة، وعيّن الباقي:
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    policies:
      - name: keep-errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: keep-slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: keep-checkout
        type: string_attribute
        string_attribute: { key: shop.checkout.step, values: [charge_payment] }
      - name: sample-rest
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }

exporters:
  # المسار الموصى به للإنتاج: OTLP للخلفية المُدارة/الذاتية
  otlphttp/backend:
    endpoint: http://tempo:4318        # أو الخلفية المُدارة
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
  debug:
    verbosity: basic                    # للتشخيص المحلي فقط

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, attributes/redact, resource, tail_sampling, batch]
      exporters: [otlphttp/backend, debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes/redact, batch]
      exporters: [loki]
  telemetry:
    logs: { level: info }
    metrics:
      level: detailed                   # راقب الـCollector نفسه (7.1.4)
'''},

        # ── 7) التشخيص
        {"type": "heading", "level": 2, "text": "⑦ التشخيص: 10 أسباب لـ«التتبع مش ظاهر»"},
        {"type": "table", "caption": "رتّب الفحص بالترتيب — 90% من الحالات في أول 4 صفوف",
         "head": ["العرض", "السبب الأشهر", "الفحص", "الإصلاح"],
         "rows": [
             ["لا spans خالصًا", "`OTEL_EXPORTER_OTLP_ENDPOINT` غير مضبوط أو التطبيق ما سجّلش SDK",
              "`env | grep OTEL` + `AddExporter(Console)` مؤقتًا", "ضبط المتغير أو تسجيل `AddOpenTelemetry` (وتأكد إنه بيتنفذ فعليًا)"],
             ["`NotSupportedException` عند الإقلاع", "جمع `UseOtlpExporter()` مع `AddOtlpExporter()` لكل إشارة (أو ServiceDefaults بيعملها)",
              "رسالة الاستثناء بتقول كده صراحةً", "اختر أسلوبًا واحدًا: إما المقطعي أو لكل إشارة"],
             ["الـspans المخصصة ناقصة", "`AddSource(\"Shop.Orders\")` غير مضاف",
              "قارن أسماء المصادر في الكود مع المسجلة", "أضف كل `ActivitySource` بـ`AddSource` (أو `AddSource(\"Shop.*\")` لو مدعوم في إصدارك)"],
             ["traces مقطّعة عند الطابور", "`traceparent` لا يُحقن في هيدرز الرسالة",
              "افحص هيدرز الرسالة المستهلكة", "استخدم `Propagators.DefaultTextMapPropagator` (inject/extract) — أو MassTransit"],
             ["فشل تصدير 404/غير مدعوم", "خلط البروتوكول والمنفذ: gRPC=4317 مقابل HTTP=4318 (والمسار `/v1/traces`)",
              "`AddOtlpExporter(o => …)` أو `OTEL_EXPORTER_OTLP_PROTOCOL`", "وحّد: `grpc` مع 4317، أو `http/protobuf` مع 4318"],
             ["كل حاجة اتسقطت (sampling)", "Sampler = 0 أو `AlwaysOff` أو `ParentBased` مع أب غير مُعيَّن",
              "اطبع نسبة العينة من الإعدادات", "`ParentBasedTraceIdRatioSampler(0.1)` وخلي القرار في Collector (tail)"],
             ["السجلات بلا TraceId", "السجل خارج نطاق `Activity.Current` (مثلًا في worker أو بعد `ConfigureAwait`)",
              "اطبع `Activity.Current?.TraceId` في نفس السطر", "ابدأ root activity في الـworker (الكود أعلاه) + enricher"],
             ["المقاييس ناقصة/مقطوعة", "الـMeter غير مضاف بـ`AddMeter` أو حدود cardinality بتسقط نقاط",
              "سجلات SDK بتحذير عن السلاسل المتجاوزة", "أضف الـMeter · ارفع `CardinalityLimit` أو قلل السمات"],
             ["الـCollector بيعيد التشغيل", "مفيش `memory_limiter` أو `decision_wait` كبير مع حمل عالي",
              "مقاييس الـCollector نفسه (`otelcol_process_memory_rss`)", "أضف `memory_limiter` أول المعالجات · قلل `num_traces` · زد الذاكرة"],
             ["الفاتورة/الحجم انفجر", "سمات بقيم غير محدودة أو sampling 100% أو سجلات Information",
              "عدد السلاسل الزمنية وحجم الاستيعاب في الخلفية", "قَوْلبة المسارات · `TagKeys` · tail sampling · مستويات سجلات (7.1.1)"],
         ]},
        {"type": "callout", "kind": "warn", "title": "أربع قواعد ما تكسرهمش",
         "md": "**① `AddSource` لكل `ActivitySource` مخصص** — وإلا الكود شغال والـSDK مش بيسمعه. **② لا تجمع `UseOtlpExporter` مع `AddOtlpExporter`** — استثناء عند الإقلاع. **③ وحدة المقاييس في السمة مش في الاسم**: `http_server_request_duration_seconds` بالثواني حسب الاتفاقية — لا تخلط ms مع s في نفس المقياس. **④ لا تسمتر معرّفات في سمات المقاييس** — المعرّف مكانه الـspan والسجل. وكمان: **`Activity.Current` بيعتمد على السياق** — في المهام الخلفية/بعد الطابور ابدأ span بنفسك."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف بنية OTel (API · SDK · Exporter · Collector) وأقدر أرسم مسار الإشارة من كودي للخلفية.",
            "أقدر أسجل traces + metrics + logs في `Program.cs` مع `ConfigureResource` واستبعاد `/health`.",
            "عارف فرق `UseOtlpExporter()` (مقطعي لكل الإشارات) عن `AddOtlpExporter()` (لكل إشارة) وإنهم ما يجتمعوش.",
            "أقدر أكتب `ActivitySource` و`Meter` بأدوات صحيحة (Counter/Histogram/ObservableGauge) ووحدات وسمات مضبوطة.",
            "أقدر أنشر السياق عبر HTTP/gRPC والطوابير، وأبدأ root activity في المهام الخلفية.",
            "أقدر أربط السجلات بالتتبع (TraceId في كل سطر) وأعرف قيمة الـexemplars.",
            "أعرف أظبط sampling (head/tail) وحدود cardinality (`CardinalityLimit`/`TagKeys`/`AddView`).",
            "أقدر أشخّص «التتبع مش ظاهر» من جدول الـ10 أسباب بالترتيب.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على OTel في .NET.",
         "questions": [
             {"q": "التطبيق شغال وبيصدر، بس الـspans اللي كتبتها بـ`ShopTracing.Source.StartActivity` مش ظاهرة. السبب الأشهر؟",
              "options": ["الـsampling", "**`AddSource(\"Shop.Orders\")` غير مضاف في `WithTracing`** — الـSDK بيسمع فقط للمصادر المسجلة", "الـCollector", "اسم الـspan"],
              "answer": 1,
              "explain": "ده أشهر سبب لـ«الكود صح والتتبع ناقص». سجّل كل `ActivitySource` (والأسماء case-sensitive)، وتأكد إن `Activity.Current` مش null (يعني فيه مستمع فعلًا)."},
             {"q": "جمعت `UseOtlpExporter()` مع `WithTracing(t => t.AddOtlpExporter())`. النتيجة؟",
              "options": ["تصدير مزدوج (نسخة لكل وجهة)", "**`NotSupportedException` عند الإقلاع** — الأسلوبان لا يجتمعان في نفس `IServiceCollection`", "أداء أبطأ", "لا شيء"],
              "answer": 1,
              "explain": "قاعدة موثقة في README المُصدِّر. وخلي بالك: Aspire ServiceDefaults بيسجل `UseOtlpExporter` تلقائيًا لما `OTEL_EXPORTER_OTLP_ENDPOINT` موجود — فلو ضفت `AddOtlpExporter` يدويًا هيقع الإقلاع."},
             {"q": "الـtraces بتظهر كرحلتين منفصلتين: واحدة للـAPI وواحدة للـworker المستهلك من الطابور. السبب؟",
              "options": ["الـworker بلا `AddSource`", "**سياق W3C (`traceparent`) لا يُحقن/يُستخرج في هيدرز الرسالة** → مفيش أب مشترك", "الـCollector بيقطع", "الـsampling"],
              "answer": 1,
              "explain": "HTTP وgRPC بينشروا السياق تلقائيًا، لكن الطوابير تحتاج حقنًا/استخراجًا صريحًا (`Propagators.DefaultTextMapPropagator`) — أو استخدام MassTransit اللي بيعمله لك. وفي الـworker ابدأ span بـ`ActivityKind.Consumer` مع `SetParentId`."},
             {"q": "ليه مُصدِّر Prometheus في OTel .NET ما زال beta، وإيه البديل للإنتاج؟",
              "options": ["بطيء؛ استخدم console exporter", "**مبني على مواصفة OpenMetrics التجريبية وقد يتغير؛ للإنتاج صدّر OTLP لـCollector وخلّيه يحوّل (remote write أو OTLP receiver في Prometheus)**", "ما بيشتغلش على Linux", "بيتطلب Prometheus 3.x"],
              "answer": 1,
              "explain": "الـendpoint `/metrics` (pull) مفيد محليًا وللتجربة. الإنتاج: OTLP → Collector → Prometheus، وده كمان بيديك exemplars ومعالجة مركزية."},
             {"q": "مقياس `http_server_request_duration_seconds` فيه 4 ملايين سلسلة زمنية. أول حاجة تفحصها؟",
              "options": ["حجم الهيستوجرام", "**قيم السمات: هل `http.route` مُقَوْلَب ولا المسار الفعلي؟ وهل فيه سمة زي `user_id`؟ ثم اضبط `TagKeys` و`CardinalityLimit`**", "عدد النسخ", "فترة الجمع"],
              "answer": 1,
              "explain": "الانفجار سببه سمة بقيم غير محدودة. الحل: قَوْلبة المسارات (الإطار بيعملها لو الـrouting matched) + تقييد السمات المسموحة + حد للسلاسل مع تحذير في السجلات."},
             {"q": "tail sampling في Collector بيحل إيه مش بيحلّه head sampling؟",
              "options": ["بيقلل الحجم أكتر دايمًا", "**بيحتفظ بكل الرحلات الفاشلة/البطيئة ويعيّن من الناجحة** — لأن القرار بيتاخد بعد اكتمال الرحلة، بينما head بيقرر قبل ما يعرف النتيجة", "بيسرع التطبيق", "بيقلل الـcardinality"],
              "answer": 1,
              "explain": "الثمن: ذاكرة و`decision_wait` في Collector (بيخزن الرحلات لحد ما تكتمل). التركيبة الشائعة: sampling خفيف في التطبيق + tail sampling في Collector للاحتفاظ بالحالات المهمة."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "تتبع متصل عبر الخدمات + ضبط تكلفة.",
         "items": [
             {"id": "t1", "title": "مهمة 1: تتبع متصل من الـgateway لقاعدة البيانات والطابور",
              "md": "**السياق:** نظام `shop`: gateway/BFF → `orders` → (PostgreSQL + `payments` عبر HTTP) → نشر رسالة → `worker` يستهلكها.\n\n**المطلوب:**\n1. `ServiceDefaults` بتسجيل OTel كامل: `ConfigureResource` (service.name/version/instance + `deployment.environment.name`) · traces · metrics · logs — **بأسلوب واحد** (إما `UseOtlpExporter` أو لكل إشارة) مع تعليق يشرح السبب.\n2. استبعاد `/health` و`/alive` من التتبع والمقاييس (filter) وقياس الفرق في الحجم قبل/بعد.\n3. `ActivitySource` مخصص مع span لكل خطوة أعمال ذات معنى (checkout: reserve_stock · charge_payment · publish_event) + سمات + events + حالة خطأ.\n4. **نشر السياق عبر الطابور**: inject عند النشر وextract عند الاستهلاك مع `ActivityKind.Consumer` (أو MassTransit + تحقق إن السياق اتنقل).\n5. root activity في الـ`BackgroundService` (outbox dispatcher) بحيث شغله يظهر في التتبع.\n6. **ربط السجلات**: TraceId/SpanId في كل سطر (enricher أو Serilog.Enrichers.Span) + `{TraceId}` في output template.\n7. Collector بـ`memory_limiter` و`batch` و**tail sampling** (احتفظ بالأخطاء والبطيئة > 1s وعيّن 10% من الباقي) وحجب `db.statement`/`authorization`.\n8. **الدليل**: لقطة/مخرج لرحلة واحدة كاملة من gateway لـworker (5 spans على الأقل عبر عمليتين) + سجل فيه نفس الـTraceId + حجم البيانات قبل/بعد الـsampling والفلاتر.",
              "criteria": [
                  "تسجيل OTel واحد بلا تعارض (`UseOtlpExporter` **أو** `AddOtlpExporter`) ومعلّق السبب.",
                  "Resource attributes كاملة (name/version/instance/environment) — ظاهرة في الخلفية.",
                  "`/health` و`/alive` مستبعدة، مع رقم حجم قبل/بعد.",
                  "spans مخصصة بأسماء وسمات وأحداث وحالة خطأ صحيحة (`ActivityStatusCode.Error` + `RecordException`).",
                  "السياق منتشر عبر الطابور (الدليل: الـworker span ابن الناشر).",
                  "root activity في الـworker/المهام الخلفية (شغلها ظاهر).",
                  "TraceId في كل سطر سجل (مُثبت بمخرج).",
                  "Collector فيه `memory_limiter` **أول المعالجات** + tail sampling بـ4 سياسات + حجب سمات حساسة.",
                  "رحلة واحدة موثقة بـ5+ spans عبر عمليتين + رقم حجم قبل/بعد.",
              ],
              "hint": "أسهل خلفية محلية: Aspire Dashboard (يقبل OTLP على 4317/18889 ويعرض الإشارات الثلاث) — مثالي لإثبات الاتصال. وبعدها Collector + Tempo/Jaeger + Prometheus + Grafana + Loki. وللتحقق من النشر: اطبع هيدرز الرسالة المستهلكة وشوف `traceparent`. ولو `Activity.Current` null في الكود، فمعناها مفيش مستمع → راجع `AddSource`.",
              "solution": "الترتيب العملي: (1) Aspire Dashboard محليًا + `OTEL_EXPORTER_OTLP_ENDPOINT` (2) تسجيل OTel في ServiceDefaults **بـ`UseOtlpExporter` وحده** (لأن ServiceDefaults قد يسجله تلقائيًا) (3) filters لاستبعاد الفحص — الحجم بينزل عادةً 20–40% (4) `ShopTracing` + `ShopMetrics` (5) حقن/استخراج السياق في رسائل RabbitMQ (6) root activity في الـoutbox worker (7) enricher للـTraceId في Serilog (8) Collector بـtail sampling. الدليل النموذجي: رحلة `POST /checkout` فيها spans: `POST /checkout` (gateway) → `checkout` (orders) → `checkout.reserve_stock` → `POST /payments/charge` (HTTP client) → `INSERT orders` (SqlClient) → `publish order-placed` → `process order-placed` (worker, Consumer). الحجم: مع sampling 10% + tail + استبعاد الفحص، الحجم بينزل عادةً 60–85% مع الاحتفاظ **بكل** الأخطاء.",
              "resources": [
                  "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel",
                  "https://opentelemetry.io/docs/languages/dotnet/",
                  "https://opentelemetry.io/docs/languages/dotnet/exporters/",
                  "https://github.com/open-telemetry/opentelemetry-dotnet",
                  "https://opentelemetry.io/docs/collector/configuration/",
                  "https://opentelemetry.io/docs/specs/otel/context/api-propagators/",
                  "https://aspire.dev/",
              ]},
             {"id": "t2", "title": "مهمة 2: اضبط التكلفة والجودة — قياس ثم تقليل بلا فقدان إشارة",
              "md": "**السياق:** التتبع شغال لكن الحجم (والتكلفة) كبير، وفيه ضجيج.\n\n**المطلوب:**\n1. **قياس الوضع الحالي** لمدة 24 ساعة (أو تحت حمل k6): حجم الاستيعاب بالـGB · عدد السلاسل الزمنية النشطة · عدد الـspans/يوم · أكبر 5 مصادر حجمًا (حسب المسار/الخدمة/مستوى السجل).\n2. طبّق 5 إجراءات تقليل مرتبة بالأثر: مستويات سجلات · استبعاد مسارات الفحص · sampling (head ثم tail) · `TagKeys`/`CardinalityLimit` · حجب الحقول الكبيرة (`db.statement`) — وقِس **بعد كل إجراء**.\n3. أضف حدودًا وقائية: `CardinalityLimit` لكل histogram مهم + `SpanLimits` (عدد السمات/الأحداث/الروابط) + تحذير في السجلات لو SDK أسقط نقاط.\n4. اضبط Collector: `memory_limiter` + `batch` بأحجام مناسبة + مراقبة الـCollector نفسه (مقاييسه في لوحة).\n5. اكتب `docs/observability-cost.md`: جدول قبل/بعد لكل إجراء (الحجم · الأثر على القدرة التشخيصية) · الرقم الشهري المتوقع · و«ما الذي لم نقلله ولماذا».\n6. **اختبار عدم الفقدان**: تأكد إن بعد كل التقليل، لسه قادر تجاوب على الأسئلة الخمسة الأولى من خطة 7.1.1 (جرّب تحقيقًا كاملًا على عطل متعمد).",
              "criteria": [
                  "قياس خط أساس بأرقام حقيقية (GB · سلاسل زمنية · spans/يوم) + أكبر 5 مصادر حجمًا.",
                  "5 إجراءات تقليل مطبقة **ومقيسة بعد كل واحد** (جدول قبل/بعد).",
                  "حدود وقائية: `CardinalityLimit` + `SpanLimits` + ملاحظة عن تحذيرات الإسقاط.",
                  "Collector بـ`memory_limiter` أولًا + batch مضبوط + مقاييسه مرصودة.",
                  "وثيقة تكلفة فيها الرقم الشهري المتوقع وفقرة «ما لم نقلله ولماذا».",
                  "**اختبار تحقيق كامل بعد التقليل** يثبت إن الأسئلة الخمسة لسه قابلة للإجابة.",
                  "ملاحظة عن المقايضة: sampling بيقلل التكلفة وبيخفي الأنماط النادرة — وكيف تعوضها (tail sampling للأخطاء).",
              ],
              "hint": "أسهل 3 مكاسب بالترتيب: (1) `Logging:LogLevel:Microsoft.EntityFrameworkCore = Warning` (2) استبعاد `/health` و`/alive` من التتبع والمقاييس (3) sampling 10% + tail للأخطاء. ولقياس السلاسل الزمنية في Prometheus: `prometheus_tsdb_head_series` و`count by (__name__)({__name__=~\".+\"})`. ولو بتستخدم خلفية مُدارة، شوف صفحة الاستهلاك/الـusage فيها.",
              "solution": "الأرقام النموذجية لمشروع صغير: قبل = ~1.5–3 GB سجلات/يوم + ~150 ألف span/يوم + ~5,000 سلسلة زمنية. بعد الإجراءات: السجلات ↓70% (مستويات + استبعاد الفحص + حجب `db.statement`)، الـspans ↓80% (sampling 10% + tail يحتفظ بكل الأخطاء والبطيئة)، السلاسل الزمنية ↓50% (TagKeys + قَوْلبة المسارات). الحدود الوقائية: `CardinalityLimit = 2000` على histograms الطلبات · `SpanLimits { AttributeCountLimit = 64, EventCountLimit = 32 }` · مراقبة `otelcol_refused_spans` و`otelcol_dropped_metric_points`. اختبار عدم الفقدان: بعد التقليل، التحقيق على عطل متعمد لسه بينجح لأن tail sampling محتفظ بكل الرحلات الفاشلة — وده الدرس الأهم: **التقليل الذكي بيحافظ على الإشارات النادرة المهمة**، مش بيقص كل حاجة بنسبة ثابتة.",
              "resources": [
                  "https://opentelemetry.io/docs/collector/configuration/",
                  "https://opentelemetry.io/docs/concepts/sampling/",
                  "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics",
                  "https://prometheus.io/docs/prometheus/latest/querying/basics/",
                  "https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "OTel لـ.NET (الدليل الرسمي)", "url": "https://opentelemetry.io/docs/languages/dotnet/"},
            {"label": "المُصدِّرات (OTLP · Prometheus · Console)", "url": "https://opentelemetry.io/docs/languages/dotnet/exporters/"},
            {"label": "مستودع opentelemetry-dotnet (الإصدارات وCHANGELOG)", "url": "https://github.com/open-telemetry/opentelemetry-dotnet"},
            {"label": "قابلية الملاحظة في .NET (Microsoft Learn)", "url": "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel"},
            {"label": "مثال: OTel + Prometheus + Grafana + Jaeger", "url": "https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-prgrja-example"},
            {"label": "إعداد الـCollector (receivers/processors/exporters)", "url": "https://opentelemetry.io/docs/collector/configuration/"},
            {"label": "الاتفاقيات الدلالية (أسماء السمات والمقاييس)", "url": "https://opentelemetry.io/docs/specs/semconv/"},
            {"label": "نشر السياق (W3C Trace Context)", "url": "https://www.w3.org/TR/trace-context/"},
        ]},
    ],
}

LESSONS_S7_A = [_L1, _L2]
