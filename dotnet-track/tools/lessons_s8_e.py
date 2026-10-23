# -*- coding: utf-8 -*-
"""Stage 8 module 2 (part E): s8-m2-l1 (Blazor: Server مقابل WebAssembly)."""

TODAY = "2026-10-22"

_L1 = {
    "id": "s8-m2-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "Blazor في .NET 10 مش «نموذج استضافة واحد» — ده **أربع أوضاع عرض (render modes)** في نفس التطبيق، وتقدر تختار لكل **مكوّن** على حدة: `Static` (SSR ثابت) · `InteractiveServer` (تفاعلي على الخادم عبر SignalR) · `InteractiveWebAssembly` (تفاعلي في المتصفح) · `InteractiveAuto` (سيرفر أولًا ثم WASM). القرار ده بيحدد **فين الكود بتاعك بيشتغل · شكل الشبكة · حجم التحميل · التكلفة · وإيه اللي بيحصل لما الاتصال يقع** — يعني قرار معماري مش تفضيل شخصي.\n\nالدرس ده بيديك: جدول المقارنة الكامل بأرقام · إزاي تختار لكل صفحة · **آثار SignalR العملية** (دائرة/حالة على الخادم · انقطاع · إعادة اتصال) · **جديد .NET 10** ([PersistentState] · استمرار حالة الدائرة · العمل أثناء enhanced navigation) · وإزاي تقيس حجم WASM وأداء الإقلاع بنفسك بدل ما تعتمد على كلام المدونات."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Render mode", "def": "طريقة عرض المكوّن: `Static` (HTML من الخادم بلا تفاعل) · `InteractiveServer` · `InteractiveWebAssembly` · `InteractiveAuto`. الافتراضي **Static** — والتفاعل بيتطلب صراحة."},
            {"term": "Static SSR", "def": "الخادم بيبني HTML مرة لكل طلب زي MVC/Razor Pages — بلا دائرة ولا JS كبير. مناسب للصفحات المحتوى/الـSEO. بس **أي تفاعل** (زر، نموذج ديناميكي) محتاج وضع تفاعلي أو نموذج HTML عادي."},
            {"term": "Circuit (دائرة)", "def": "جلسة تفاعلية على الخادم بتمسك حالة المكوّنات وبتتواصل مع المتصفح عبر **SignalR/WebSocket**. كل مستخدم (كل تاب) = دائرة = ذاكرة على الخادم."},
            {"term": "Blazor WebAssembly", "def": "تشغيل .NET (مُجمّع لـWASM) داخل المتصفح. الكود بيشتغل عند المستخدم — فأول تحميل بيبقى أكبر، بس بعد كده مفيش ذهاب-وعودة للسيرفر لكل تفاعل."},
            {"term": "Interactive Auto", "def": "أول زيارة: الخادم (سريع جدًا لأن الـWASM لسه بيتحمّل في الخلفية) · الزيارات التالية: المتصفح. أفضل توازن للنظام العام — بشرط إن الحالة تتنقل بأمان."},
            {"term": "Prerendering", "def": "الخادم بيبني HTML أولًا (عشان سرعة الظهور والـSEO)، وبعدين المكوّن بيعيد التشغيل **مرة تانية** في وضع تفاعلي. النتيجة: `OnInitializedAsync` بيتنفذ مرتين واستدعاء بيانات مكرر — وده اللي `[PersistentState]` بيحله."},
            {"term": "[PersistentState]", "def": "**جديد .NET 10**: سِمة على **خاصية عامة** بتخلي قيمتها تتحفظ أثناء prerender وتُسترجع في الوضع التفاعلي — بدل ~25 سطرًا يدوية بـ`PersistentComponentState`. خيارات: `AllowUpdates` (تحديث أثناء enhanced navigation) · `RestoreBehavior`."},
            {"term": "Circuit state persistence", "def": "**جديد .NET 10**: Blazor يقدر يحفظ حالة الدائرة لما الاتصال ينقطع مدة طويلة أو لما تتوقف الدائرة عمدًا (`Blazor.pause()`)، ويرجّعها عند إعادة الاتصال من **نفس التاب** — لـ`InteractiveServer` فقط، وبتضيع مع أي refresh كامل."},
            {"term": "Enhanced navigation", "def": "التنقل بين الصفحات بيتحاكى بدون إعادة تحميل كاملة (fetch + تحديث الـDOM). أسرع للمستخدم — وفي .NET 10 بقى بيدعم حالة `[PersistentState]` كذلك."},
            {"term": "AOT مقابل Interpreted (WASM)", "def": "الافتراضي: تشغيل مُفسَّر/مُجمّع جزئيًا (تحميل أصغر، إقلاع أسرع نسبيًا) · **AOT** (`RunAOTCompilation`): أداء حسابي أعلى بكتير **لكن حجم تحميل أكبر بوضوح وبناء أبطأ**. متفعلهاش قبل ما تقيس."},
            {"term": "Offline/Deployment", "def": "WASM بينشر كملفات ثابتة (CDN/Blazor Web App) — فممكن يشتغل أوفلاين (PWA) — بينما Server محتاج اتصال دائم بالخادم."},
            {"term": "SignalR reconnection", "def": "لما الاتصال يقع، Blazor بيحاول يعيد الاتصال ويعرض واجهة «إعادة الاتصال». .NET 10 بيحفظ الحالة لتحسين التجربة — بس التجربة الحقيقية محتاجة تصميم: مؤشر واضح + إعادة محاولة + عدم فقدان المدخلات."},
            {"term": "Component render mode propagation", "def": "الوضع بينتقل من الأب للابن — **ما ينفعش** ابن يكون تفاعلي بوضع مختلف عن أب تفاعلي. وممكن يكون فيه أشقاء بأوضاع مختلفة داخل صفحة ثابتة."},
            {"term": "HttpContext في Static SSR", "def": "متاح كـCascadingParameter في الوضع الثابت فقط (لأنه بيشتغل داخل الطلب) — و**غير متاح** في الوضع التفاعلي. من هنا أشهر خطأ: كود بيقرأ HttpContext في وضع تفاعلي."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① الجدول الحاكم: أربع أوضاع × عشرة معايير"},
        {"type": "table", "caption": "اختيار وضع العرض — المعايير اللي بتفرق فعلًا",
         "head": ["المعيار", "**Static SSR**", "**Interactive Server**", "**Interactive WebAssembly**", "**Interactive Auto**"],
         "rows": [
             ["فين C# بيشتغل", "الخادم — مرة لكل طلب", "الخادم (داخل دائرة SignalR)", "**المتصفح** (WASM)", "الخادم أولًا ثم المتصفح"],
             ["تفاعل (أزرار/نماذج حية)", "❌ (نماذج HTML تقليدية ممكنة)", "✅", "✅", "✅"],
             ["اتصال دائم مطلوب", "لا", "**نعم** (WebSocket)", "لا (بعد التحميل)", "أول زيارة نعم، بعدها لا"],
             ["التحميل الأول", "HTML فقط — **الأسرع**", "~90KB لـ`blazor.web.js`", "**الأثقل** (WASM runtime + التطبيق + DLLs)", "خفيف أولًا ثم WASM في الخلفية"],
             ["بعد التحميل: زمن الاستجابة", "كل تفاعل = طلب كامل", "دائرة → الخادم (شبكة!) لكل حدث", "محلي — بلا شبكة (أسرع تفاعل)", "حسب الوضع النشط"],
             ["ذاكرة الخادم لكل مستخدم", "لا شيء بعد الطلب", "**دائرة كاملة في الذاكرة**", "لا شيء", "أول زيارة فقط"],
             ["قابلية التوسع الأفقي", "عالية جدًا", "محتاج **sticky sessions** أو وسيط (2.2.12)", "عالية (ملفات ثابتة)", "عالية بعد أول زيارة"],
             ["عمل أوفلاين", "لا", "لا", "**ممكن** (PWA)", "جزئيًا"],
             ["الوصول للـDB/الأسرار", "مباشر ✅", "مباشر ✅", "**ممنوع** — كل شيء في المتصفح مكشوف (7.2.2)", "الأول مباشر · الباقي محتاج API"],
             ["الأنسب لـ", "محتوى · SEO · صفحات تسويق · تقارير للطباعة", "**لوحات إدارية داخلية** · تطبيقات بتقرأ DB مباشرة", "PWA · تطبيقات تفاعلية كثيفة · عمل أوفلاين", "تطبيقات عامة كثيرة الصفحات"],
         ]},
        {"type": "callout", "kind": "goal", "title": "قاعدة القرار في 30 ثانية",
         "md": "**① صفحة محتوى/SEO/تقرير؟** → `Static` (+ نموذج HTML لو محتاج إدخال).\n**② لوحة إدارية داخلية وفريقك .NET؟** → `InteractiveServer` — أسرع بناء، الكود على الخادم، والـDB قريبة.\n**③ تطبيق مستخدمين عام (كثير الاستخدام، تفاعل كثيف، أو أوفلاين)؟** → `InteractiveWebAssembly` أو `Auto`.\n**④ مش عارف؟** → `Static` للصفحات الثابتة + `Auto` للتفاعلية — ده الافتراضي الأنضف في .NET 10.\n\n**والقرار الأخطر**: أي وضع بيشتغل في المتصفح (WASM/Auto) معناها إن **كل حاجة في الحزمة مكشوفة** — لا connection strings ولا مفاتيح ولا منطق تفويض سري. التفويض الحقيقي في API على الخادم (7.2.3)."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② التفعيل والإعداد في .NET 10"},
        {"type": "code", "lang": "csharp", "title": "Program.cs — تفعيل الأوضاع (Blazor Web App)", "filename": "src/Shop.Admin/Program.cs", "code": r'''var builder = WebApplication.CreateBuilder(args);

// ── 1) خدمات مكوّنات Razor + الأوضاع التفاعلية ─────────────────────────
builder.Services
    .AddRazorComponents()
    .AddInteractiveServerComponents()          // يفعّل InteractiveServer
    .AddInteractiveWebAssemblyComponents();   // يفعّل WebAssembly + Auto

// خدمات التطبيق: الـAPI client آمن للاستخدام في الـWASM (بلا أسرار!)
builder.Services.AddScoped<OrdersApiClient>();
builder.Services.AddScoped<CartState>();      // حالة في النطاق — انظر 8.2.2

// ربط حالة الدائرة (جديد .NET 10) — اختياري لكن مفيد للوحات الإدخال الطويلة
builder.Services.Configure<CircuitOptions>(o =>
{
    o.DisconnectedCircuitRetentionPeriod = TimeSpan.FromMinutes(3);
    // o.DetailedErrors = app.Environment.IsDevelopment();  // لا تفعلها في الإنتاج (تسريب)
});

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseSecurityHeaders();       // من 7.2.3
app.UseAntiforgery();           // مطلوب لنماذج SSR والـendpoints

app.MapStaticAssets();          // .NET 9+: أصول ثابتة بـfingerprint وكاش ذكي

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode()
    .AddInteractiveWebAssemblyRenderMode()
    .AddAdditionalAssemblies(typeof(Shop.Admin.Client._Imports).Assembly); // مشروع الزبون

app.Run();
'''},
        {"type": "code", "lang": "text", "title": "تطبيق الأوضاع: على مستوى المكوّن، الصفحة، أو التطبيق", "filename": "docs/blazor-render-modes.razor-examples", "code": r'''@* ═══ 1) على مستوى التطبيق (App.razor) ═══════════════════════════════
   الوضع يُطبّق على كل الصفحات التفاعلية — والـStatic يفضل افتراضيًا *@
<Routes @rendermode="InteractiveServer" />
@* أو: <Routes @rendermode="InteractiveAuto" />  ·  <Routes @rendermode="InteractiveWebAssembly" /> *@

@* ═══ 2) على مستوى الصفحة ═════════════════════════════════════════════
   الطريقة الأوضح والأكثر أمانًا: كل صفحة تعلن احتياجها *@
@page "/orders"
@rendermode InteractiveServer
@attribute [Authorize(Policy = "ApiUser")]

@*
   أو مع تعطيل prerender (نادرًا ما تحتاجه):
   @rendermode @(new InteractiveServerRenderMode(prerender: false))
   → بيمنع النداء المزدوج لكن بيفقد سرعة الظهور والـSEO.
*@

@* ═══ 3) على مستوى المكوّن (جزر تفاعلية داخل صفحة ثابتة) ═════════════
   صفحة تسويقية ثابتة (SEO) + آلة حاسبة تفاعلية فقط *@
@page "/pricing"
@* الصفحة نفسها Static — لا @rendermode هنا *@

<h1>الأسعار</h1>
<p>محتوى ثابت مفهرس — HTML من الخادم بلا JS.</p>

<PriceCalculator @rendermode="InteractiveServer" />   @* الجزيرة التفاعلية *@
<LiveChat @rendermode="InteractiveWebAssembly" />       @* شقيق بوضع مختلف = مسموح *@

@* ═══ 4) قاعدة مهمة ══════════════════════════════════════════════════
   الأب التفاعلي بيورّث وضعه للأبناء: مكوّن InteractiveServer
   لا يجوز أن يحتوي على InteractiveWebAssembly — ويُرمى خطأ وقت التشغيل.
   والمكوّنات المشتركة (في مشروع .Client) تعمل في الوضعين،
   بشرط ما تستخدمش واجهات الخادم فقط.
*@
'''},
        {"type": "callout", "kind": "warn", "title": "ثلاثة أخطاء إعداد بتضيّع نص يوم",
         "md": "**① نسيان `AddInteractiveWebAssemblyComponents`** بينما الصفحة مكتوب عليها `InteractiveWebAssembly` → خطأ «لم يتم العثور على خدمات» أو سقوط للوضع الثابت.\n**② نسخة من المكوّن في المشروع الخطأ**: مكوّنات `.Client` لازم تكون في مشروع المكتبة المشترك (اللي بيشير ليه الخادم والـWASM) — مش في مشروع الخادم. وكل الـ`@using` بتاعتها في `_Imports.razor` للمشترك.\n**③ نسيان `UseAntiforgery()`** → نماذج SSR (`EditForm` بـstatic) بترفض بـ400: «The required antiforgery...» — استدعها **بعد** `UseRouting` وقبل الـendpoints."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ Blazor Server: آثار SignalR اللي لازم تحسبها"},
        {"type": "table", "caption": "الآثار العملية (مش النظرية) — وكيف تتعامل",
         "head": ["الأثر", "ما يحدث فعلًا", "التعامل الصحيح"],
         "rows": [
             ["**ذاكرة لكل مستخدم**", "كل دائرة بتحتفظ بحالة المكوّنات + المكوّنات نفسها + الخدمات الـScoped",
              "قلّل الحالة المحفوظة · لا تحتفظ بقوائم ضخمة في الذاكرة · راقب عدد الدوائر والذاكرة (7.1.1) · `DisconnectedCircuitRetentionPeriod` قصير"],
             ["**كل حدث = رحلة شبكة**", "ضغطة زر بتروح للسيرفر وترجع — على شبكة بطيئة بيبان التأخير",
              "لا تعمل حلقة تكرار حساسة على الخادم · استخدم CSS للتفاعلات البصرية البسيطة · لو محتاج تفاعل فوري كثيف → WASM"],
             ["**انقطاع الاتصال**", "الشبكة/الهاتف يقطع → واجهة «إعادة الاتصال»؛ الحالة تُفقد بعد مهلة السماح (افتراضي ~3 دقائق)",
              ".NET 10: **استمرار حالة الدائرة** بيحسّن ده · صمّم واجهة إعادة اتصال واضحة · **احفظ المسودات في الخادم** للنماذج الطويلة"],
             ["**التوسع الأفقي**", "دائرتين على نسختين مختلفتين = أخطاء غامضة",
              "**sticky sessions** على الـingress (2.2.12) · أو وسيط Redis للـSignalR (`AddStackExchangeRedis` — يحتاج تأكيد توثيق إصدارك) · وراقب بعد كل نشر"],
             ["**الخمول وموارد السيرفر**", "تابات منسية بتاكل ذاكرة (ودوائر مفتوحة)",
              "مهلة خمول للدوائر · إغلاق الدوائر المنقطعة · مراقبة عدد الدوائر كمقياس أعمال"],
             ["**عدم قابلية الشغل للاختبار محليًا**", "الكود بيعتمد على دائرة حقيقية",
              "الاختبارات: `bunit` للمكوّنات · واختبارات API للتكامل · لا تعتمد على `HttpContext` في الكود التفاعلي"],
             ["**HttpContext غير متاح**", "`[CascadingParameter] HttpContext` شغال في Static فقط",
              "مرّر ما تحتاجه (معرّف المستخدم/التفويض) عبر `AuthenticationStateProvider` أو خدمة — لا تقرأ HttpContext في وضع تفاعلي"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قاعدة عملية: Blazor Server = تطبيق «طرفية رقيقة»",
         "md": "فكّر فيه زي تطبيق سطح مكتب بيشتغل على السيرفر: **كل ما تحتفظ بيه في الذاكرة بيدفع تمنه السيرفر لكل مستخدم**. عشان كده:\n\n• الحالة اللي لازم تعيش أطول من الدائرة → **قاعدة بيانات** (مسودة/سلة) مش ذاكرة.\n• القوائم الكبيرة → **pagination على الخادم** (2.2.2) مش تحميل الكل ثم فلترة في المكوّن.\n• الصور/الأصول الثقيلة → CDN/أصول ثابتة (6.2.4).\n• وراقب: عدد الدوائر · الذاكرة/دائرة · زمن الاستجابة عبر الشبكة (7.1.4)."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ جديد .NET 10: الحالة لا تُفقد بعد اليوم"},
        {"type": "code", "lang": "text", "title": "PersistentState — قبل وبعد (الفرق 25 سطرًا مقابل سطر)", "filename": "docs/persistent-state.razor", "code": r'''@* ═══════════ قبل .NET 10: يدويًا (وكان عرضة للخطأ) ═══════════ *@
@page "/orders-before"
@implements IDisposable
@inject PersistentComponentState AppState

@code {
    private PersistingComponentStateSubscription _sub;
    public List<OrderDto>? Orders { get; set; }

    protected override async Task OnInitializedAsync()
    {
        // هل جاءت القيم من مرحلة الـprerender؟
        if (!AppState.TryTakeFromJson<List<OrderDto>>(nameof(Orders), out var cached))
        {
            Orders = await Api.GetOrdersAsync();          // نداء واحد
        }
        else
        {
            Orders = cached;
        }

        // سجّل الـcallback اللي بيحفظ الحالة قبل الـprerender
        _sub = AppState.RegisterOnPersisting(() =>
        {
            AppState.PersistAsJson(nameof(Orders), Orders);
            return Task.CompletedTask;
        });
    }

    public void Dispose() => _sub.Dispose();
}

@* ═══════════ بعد .NET 10: سِمة واحدة على خاصية عامة ═══════════ *@
@page "/orders"
@rendermode InteractiveServer

@code {
    // لازم public property (الـframework بيستخدم الإنعكاس/source-gen)
    [PersistentState]
    public List<OrderDto>? Orders { get; set; }

    protected override async Task OnInitializedAsync()
    {
        // لو الحالة موجودة من prerender/الدائرة السابقة، ما بننفذش النداء
        Orders ??= await Api.GetOrdersAsync();
    }
}
'''},
        {"type": "table", "caption": "خيارات [PersistentState] والاستمرار — متى تستخدم كل واحد",
         "head": ["الخيار/الميزة", "ما يفعله", "متى تستخدمه"],
         "rows": [
             ["`[PersistentState]`", "يحفظ قيمة خاصة عامة أثناء prerender ويسترجعها عند التفاعل — **يمنع النداء المزدوج والوميض**", "كل صفحة بتجيب بيانات في `OnInitializedAsync` وبتُعرض تفاعليًا"],
             ["`AllowUpdates = true`", "بيسمح بتحديث الحالة أثناء **enhanced navigation** (ولو انتقلت ورجعت)", "بيانات تتغير بين الصفحات (عدّاد سلة/إشعارات)"],
             ["`RestoreBehavior = SkipInitialValue`", "يتجاهل لقطة الـSSR ويجيب بيانات جديدة", "بيانات حساسة للوقت (رصيد/مخزون) ما ينفعش تتعرض من لقطة"],
             ["`RestoreBehavior = SkipLastSnapshot`", "بيتجاهل آخر لقطة بعد إعادة الاتصال ويجيب الجديد", "لوحات مراقبة/تقارير لازم تكون محدثة بعد الرجوع"],
             ["`RegisterPersistentService<T>(RenderMode...)`", "يحفظ حالة **خدمة** (Scoped فقط) بالطريقة نفسها", "حالة سلة/تصفية مشتركة بين مكوّنات كتير"],
             ["Circuit state persistence", "يحفظ حالة الدائرة عند انقطاع طويل أو `Blazor.pause()` — ويسترجعها عند العودة من **نفس التاب**", "نماذج/معالجات طويلة · مستخدم قفل التاب أو قفل الموبايل"],
         ]},
        {"type": "callout", "kind": "danger", "title": "ثلاثة تحذيرات على الحالة المحفوظة",
         "md": "**① في WASM وAuto: الحالة المتسلسلة بتوصل للمتصفح** — يعني **أي حد يقدر يقرأها**. متحفظش توكنات ولا بيانات شخصية مش مسموح بيها ولا حقول سرية. في `InteractiveServer` الحالة بتُشفَّر بـData Protection، لكن في CSR بتتكتب في الصفحة — تعامل معاها كبيانات **عامة**.\n**② لازم JSON-serializable**: كيانات EF أو كائنات فيها مراجع دائرية بتفشل أو تنتج حمولة ضخمة — استخدم DTOs.\n**③ ما تفرطش**: تخزين 5,000 صف في الحالة = حمولة كبيرة على كل طلب. احفظ اللي يحتاجه العرض فقط + الملخّصات.\n\nوكمان: `@key` في الحلقات لمنع تعارض تركيب المكوّنات · والاستمرار اختياري (opt-in) — مش بيفعّل نفسه."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ WebAssembly: حجم وأداء — قِس بنفسك"},
        {"type": "code", "lang": "bash", "title": "قياس الحجم والأداء (أرقامك أهم من أي مدونة)", "filename": "scripts/measure-wasm.sh", "code": r'''#!/usr/bin/env bash
# قياس فعلي لحجم تحميل Blazor WASM وأداء الإقلاع.
set -euo pipefail

echo "== 1) نشر Release (مضغوط بـbrotli/gzip زي الإنتاج) =="
dotnet publish src/Shop.Admin/Shop.Admin.csproj -c Release -o artifacts/wa-publish

echo "== 2) حجم ما سيُحمّل فعلًا للـWASM =="
# .NET بينشر ملفات .br و.gz إلى جانب الأصل — قِس المضغوط
du -sh artifacts/wa-publish/wwwroot/_framework
find artifacts/wa-publish/wwwroot/_framework -name '*.br' -printf '%s\n' \
  | awk '{ s += $1 } END { printf "brotli total: %.1f MB\n", s/1048576 }'
find artifacts/wa-publish/wwwroot/_framework -name '*.gz' -printf '%s\n' \
  | awk '{ s += $1 } END { printf "gzip total:   %.1f MB\n", s/1048576 }'

echo "== 3) أكبر 10 ملفات (لو فيه ملف ضخم غالبًا حزمة/مكتبة) =="
find artifacts/wa-publish/wwwroot/_framework -name '*.br' -printf '%s %p\n' \
  | sort -rn | head -10 | awk '{ printf "%8.2f KB  %s\n", $1/1024, $2 }'

echo "== 4) هل AOT مفعّل؟ (حجم أكبر بوضوح) =="
grep -R "RunAOTCompilation" src/Shop.Admin/Shop.Admin.csproj || echo "AOT غير مفعّل (الافتراضي)"

echo "== 5) القياس الحقيقي (يدوي — مهم) =="
cat <<'NOTE'
شغّل:
  dotnet run --project src/Shop.Admin -c Release
ثم في المتصفح:
  • DevTools → Network → Disable cache → Hard reload
    → سجّل: transferred (الأهم) · DOMContentLoaded · Load
    → فلتر على _framework واقلب على Brotli
  • Lighthouse (Mobile, Slow 4G) → LCP · TBT · CLS · TTI
  • Performance → تسجيل 5 ثوانٍ للإقلاع → ابحث عن long tasks
قِس قبل/بعد أي تغيير (AOT · trimming · lazy loading للمكوّنات/التجميعات).
NOTE

echo "== 6) تقليل الحجم: Lazy loading للمكوّنات =="
cat <<'NOTE'
<!-- لا تحمّل كل الصفحات في الحزمة الأولى -->
<Router AppAssembly="typeof(Program).Assembly" AdditionalAssemblies="new[]{ typeof(_Imports).Assembly }">
  <Found Context="routeData">
    <RouteView RouteData="routeData" DefaultLayout="typeof(Layout.MainLayout)" />
    <FocusOnNavigate RouteData="routeData" Selector="h1" />
  </Found>
</Router>
<!-- + <BlazorWebAssemblyLazyLoad Include="Shop.Admin.Reports.dll" /> في csproj/الـindex -->
NOTE
'''},
        {"type": "table", "caption": "أرقام تقريبية للمقارنة — وأهمية القياس الحقيقي",
         "head": ["البند", "المدى المعتاد", "ما الذي يغيّره"],
         "rows": [
             ["`blazor.web.js` (Server)", "~90KB", "ثابت تقريبًا — لا يكبر مع التطبيق"],
             ["WASM runtime + framework", "1.5–2MB (قبل الضغط)", "إصدار .NET · trimming"],
             ["حزمة التطبيق + DLLs", "مئات الكيلوبايت → عدة ميجابايت", "عدد الحزم · صفحات ثقيلة · مكتبات UI"],
             ["**المضغوط (brotli) للتحميل الفعلي**", "غالبًا **2–4MB** لتطبيق متوسط (**قِس** — الرقم بيعتمد على تبعياتك)", "الضغط · ما تحمّله في البداية"],
             ["AOT", "**يزيد الحجم بوضوح** ويزيد وقت البناء، ويحسّن الحساب", "العمليات الحسابية الثقيلة فقط"],
             ["زمن الإقلاع على 4G", "ثوانٍ (يقل مع Auto + الكاش)", "حجم الحزمة · عدد الطلبات · cache headers"],
         ]},
        {"type": "callout", "kind": "note", "title": "ليه Auto بيحل أغلب مشكلة الحجم",
         "md": "في `InteractiveAuto` أول زيارة بتاخد HTML من الخادم (ظهور فوري) والـWASM بيتحمّل **في الخلفية**؛ والزيارات التالية بقت في المتصفح (تفاعل محلي بلا شبكة). النتيجة: **أول تجربة سريعة + تجربة محلية بعدها**.\n\nلكن انتبه: (1) الزيارة الأولى لازم فيها دائرة SignalR — فالسيرفر بيتحمل جزءًا من الحمل؛ (2) الحالة لازم تتنقل بأمان بين الوضعين (نفس قيود WASM: بيانات عامة فقط)؛ (3) **الوضع بينتقل عند التنقل التالي** — مش في نفس الصفحة."},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ الاختبار والتصحيح: إزاي تتعامل مع «بيشتغل على جهازي»"},
        {"type": "table", "caption": "أدوات وممارسات لكل وضع",
         "head": ["الحاجة", "Server", "WASM", "أدوات"],
         "rows": [
             ["اختبار مكوّن معزول", "✅ `bunit`", "✅ `bunit`", "`bunit` (RenderComponent<T> + Services + JSInterop mock)"],
             ["تصحيح C# في المتصفح", "على الخادم عادي", "**Chrome/Edge DevTools** مع breakpoints في C#", "debugging WASM (`inspectUri`) — يحتاج تشغيل بمصحح"],
             ["الأخطاء الحقيقية", "سجلات الخادم", "console المتصفح + App Insights/OTel من العميل", "7.1.2 + `WebAssembly` instrumentation"],
             ["الأداء", "زمن الشبكة + ذاكرة الدوائر", "حجم التحميل + long tasks", "7.1.4 + Lighthouse"],
             ["فحص a11y", "HTML الناتج", "DOM بعد الترطيب (hydration)", "8.1.4 (aria-live · تركيز · تباين)"],
             ["العمل أوفلاين", "غير ممكن", "PWA (manifest + service worker)", "WASM فقط"],
         ]},
        {"type": "code", "lang": "bash", "title": "اختبار مكوّن بـbunit (مثال يحاكي حالات 8.1.4)", "filename": "tests/Shop.Admin.Tests/OrdersListTests.cs", "code": r'''// حزمة: bunit (+ xUnit). تُشغّل المكوّن بلا متصفح ولا دائرة.
using Bunit;
using Microsoft.Extensions.DependencyInjection;
using Shouldly;
using Xunit;

public sealed class OrdersListTests : TestContext
{
    [Fact]
    public void Shows_error_state_when_api_returns_forbidden()
    {
        // ترتيب: بديل للـAPI بيرجع 403
        Services.AddSingleton<IOrdersApi>(new StubApi(
            () => throw new ApiException(403, "ليست لديك صلاحية")));

        var cut = RenderComponent<OrdersList>();
        cut.WaitForAssertion(() =>
        {
            cut.Find("[role=alert]").TextContent.ShouldContain("ليست لديك صلاحية");
            // ولا يعرض حالة فارغة مضللة (8.1.4)
            cut.Markup.ShouldNotContain("لا توجد طلبات");
        });
    }

    [Fact]
    public void Renders_skeleton_with_aria_hidden_then_data()
    {
        var api = new StubApi(() => Task.FromResult(new[] { new OrderDto("ORD-1", "placed", "199.99", "EGP", DateTimeOffset.UtcNow) }));
        Services.AddSingleton<IOrdersApi>(api);

        var cut = RenderComponent<OrdersList>();
        // أثناء الجلب: skeleton مخفي عن قارئ الشاشة
        cut.FindAll("[aria-hidden=true]").Count.ShouldBeGreaterThan(0);

        cut.WaitForAssertion(() => cut.FindAll("li.card").Count.ShouldBe(1));
    }

    private sealed class StubApi(Func<Task<OrderDto[]>> impl) : IOrdersApi
    {
        public Task<OrderDto[]> GetOrdersAsync(CancellationToken ct = default) => impl();
    }
}
'''},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ قرار مكتوب: إزاي تختار لمشروعك"},
        {"type": "steps", "title": "خمس خطوات تخرج منها بقرار مبرر", "items": [
            {"title": "صنّف صفحاتك",
             "md": "اكتب جدولًا: صفحة · محتوى أم تفاعلية · داخلية أم عامة · هل تحتاج SEO · كم مستخدم متوقع في نفس اللحظة. الجدول ده بيحدد الأوضاع."},
            {"title": "اختار الوضع الافتراضي",
             "md": "`Static` لكل ما هو محتوى · `Auto` (أو `Server` للداخلي) للتفاعلي. لا تحط تفاعل على مستوى التطبيق كله إلا لو التطبيق كله تفاعلي."},
            {"title": "احسب تكلفة الخادم (لو Server/Auto)",
             "md": "ذاكرة ≈ (عدد المستخدمين المتزامنين × ذاكرة الدائرة) + هامش. قِس ذاكرة دائرة واحدة تحت حمل حقيقي (7.1.4)، وحدد `DisconnectedCircuitRetentionPeriod` المناسب. واختبر التوسع بنسختين + sticky sessions."},
            {"title": "قِس حجم WASM (لو WASM/Auto)",
             "md": "شغّل `measure-wasm.sh`، وسجّل transferred في Network مع Brotli. لو > ~3MB، قلّل الحزم واعمل lazy loading للتقارير/الصفحات الثقيلة قبل ما تفكر في AOT."},
            {"title": "اكتب صفحة قرار (ADR)",
             "md": "زي 4.1.1: السياق · الخيارات · القرار · العواقب · إمتى نراجعه. مثال: «اخترنا Auto لأن X؛ التكلفة Y؛ المقياس الذي سيراجع القرار: حجم WASM > 4MB أو ذاكرة الدوائر > Z»."},
        ]},
        {"type": "callout", "kind": "danger", "title": "خمسة أخطاء معمارية شائعة في Blazor",
         "md": "**① تشغيل كل التطبيق في وضع تفاعلي** (بدل Static للصفحات الثابتة) → تحميل أبطأ وتكلفة بلا مقابل.\n**② استخدام Blazor Server لتطبيق عام كبير** بلا قياس الذاكرة → انهيار السيرفر عند أول ذروة.\n**③ وضع أسرار في مشروع `.Client`** → كل الأسرار مكشوفة في المتصفح (7.2.2).\n**④ الاعتماد على `HttpContext` في الكود التفاعلي** → يعمل في prerender ويفشل عند أول تفاعل.\n**⑤ تحميل كل البيانات في الذاكرة لحساب الإجماليات** → الخادم بيحمل بيانات كل المستخدمين. الحل: تجميع على قاعدة البيانات (3.4) واستعلامات مُفهرسة."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أسمّي أوضاع العرض الأربعة وأعرف أين يُشغَّل الكود في كل واحد.",
            "أختار الوضع لكل صفحة بقاعدة القرار، وأعرف لماذا الوضع الافتراضي `Static`.",
            "أعرف آثار Blazor Server العملية: ذاكرة لكل دائرة · كل حدث = رحلة شبكة · sticky sessions للتوسع · مهلة الدوائر المنقطعة.",
            "أفعّل الأوضاع في `Program.cs` (`AddInteractiveServerComponents` / `AddInteractiveWebAssemblyComponents` + `MapRazorComponents<App>()`) وأعرف أخطاء الإعداد الثلاثة.",
            "أشرح مشكلة النداء المزدوج بسبب prerender وأحلها بـ`[PersistentState]` (بدل 25 سطرًا يدوية).",
            "أعرف خيارات `AllowUpdates` و`RestoreBehavior` ومتى أستخدم كل واحد.",
            "أعرف استمرار حالة الدائرة في .NET 10 (لـServer فقط · نفس التاب · تُفقد مع refresh) وحدوده.",
            "أعرف أن الحالة في WASM/Auto تكون **مكشوفة للمتصفح** وأن التفويض والأسرار مكانها الخادم.",
            "أقيس حجم WASM المضغوط وأداء الإقلاع بنفسي، وأقلّله (lazy loading · تقليل الحزم) قبل التفكير في AOT.",
            "أختبر المكوّنات بـ`bunit` وأفهم فروق التصحيح بين Server وWASM.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على أوضاع Blazor.",
         "questions": [
             {"q": "أين يعمل كود C# في `InteractiveServer` مقارنة بـ`InteractiveWebAssembly`؟",
              "options": ["الاتنان في المتصفح",
                          "Server على الخادم داخل دائرة SignalR · WebAssembly في المتصفح بعد تحميل runtime",
                          "الاتنان على الخادم",
                          "Server في المتصفح وWASM على الخادم"],
              "answer": 1,
              "explain": "Server: المكوّنات بتتنفذ على الخادم وبتتواصل عبر WebSocket (الدائرة). WebAssembly: كل الكود بيتحمّل ويعمل في المتصفح — فمفيش اتصال دائم، لكن التحميل الأول أكبر وكل حاجة في الحزمة مكشوفة."},
             {"q": "ما النتيجة العملية لكون `InteractiveServer` بيحتفظ بدائرة لكل مستخدم؟",
              "options": ["لا فرق عن WASM",
                          "ذاكرة الخادم بتزيد لكل مستخدم متزامن، والتوسع الأفقي يحتاج sticky sessions أو وسيط للـSignalR",
                          "كل مستخدم بيحصل على نسخة من التطبيق في المتصفح",
                          "الاستجابة أبطأ في كل الأحوال"],
              "answer": 1,
              "explain": "الدائرة بتحمل حالة المكوّنات + الخدمات الـScoped. لو وزّع الطلب على نسخة تانية بنفس العميل بلا sticky sessions، الدائرة «بتضيع» وتظهر أخطاء غامضة. عشان كده اختبار التوسع بنسختين مطلوب (6.1.5)."},
             {"q": "لماذا `OnInitializedAsync` بيتنفذ مرتين في وضع تفاعلي مع prerender؟",
              "options": ["خطأ في Blazor",
                          "الخادم بيبني HTML أولًا (prerender) ثم بيعيد تشغيل المكوّن في الوضع التفاعلي — فالحل [PersistentState]",
                          "بسبب SignalR",
                          "بسبب الـDI"],
              "answer": 1,
              "explain": "الـprerender بيمر بدورة حياة كاملة (بلا `OnAfterRender`) وبعده الوضع التفاعلي بيعيد الدورة — فبيحصل نداءان للبيانات ووميض. `[PersistentState]` (جديد .NET 10) بيحفظ القيمة من الـprerender ويسترجعها، فالنداء الثاني بيلاقيها موجودة (`Orders ??= await …`)."},
             {"q": "في `InteractiveWebAssembly`، هل يمكن قراءة connection string أو مفتاح API في الكود؟",
              "options": ["نعم، الحزمة مشفرة",
                          "لا — كل حاجة في الحزمة متاحة للمستخدم (بيانات عامة)، والأسرار والتفويض الحقيقي في الخادم",
                          "نعم لو AOT مفعّل",
                          "نعم لو HTTPS"],
              "answer": 1,
              "explain": "المتصفح بياخد الملفات ويفكها — التشفير أو الضغط مش حماية. أي مفتاح/سلسلة اتصال/منطق تفويض سري لازم يبقى على الخادم، والعميل يكلم API محمي (7.2.2/7.2.3)."},
             {"q": "أفضل وصف لميزة استمرار حالة الدائرة في .NET 10؟",
              "options": ["تحفظ الحالة إلى الأبد حتى مع refresh",
                          "تحفظ حالة الدائرة عند انقطاع طويل أو إيقاف عمدي، وتسترجعها عند العودة من نفس التاب — لـServer فقط وتضيع مع full refresh",
                          "تعمل في WASM فقط",
                          "تشتغل تلقائيًا بلا إعداد"],
              "answer": 1,
              "explain": "الميزة تحسّن تجربة الانقطاع (تاب مقفول/موبايل بدّل تطبيق/شبكة تقطعت) لكنها مش تخزين دائم: full refresh بيضيّعها، وهي opt-in، و`Interactive Server` فقط، والحالة لازم تكون JSON-serializable."},
             {"q": "صفحة تسويق عامة + آلة حاسبة أسعار تفاعلية فقط. الأنسب؟",
              "options": ["كل التطبيق InteractiveServer",
                          "الصفحة Static (SEO وسرعة) والحاسبة مكوّن تفاعلي بوضع InteractiveServer/WebAssembly",
                          "كل التطبيق WebAssembly",
                          "Static فقط بلا تفاعل"],
              "answer": 1,
              "explain": "احقن التفاعل في «جزيرة» داخل صفحة ثابتة — البلازر بيسمح بأشقاء بأوضاع مختلفة. كده بتحصل على HTML مفهرس وسريع، وتفاعل فقط حيث تحتاجه (بدل تحميل runtime كامل لكل زائر)."},
             {"q": "لماذا لا يصلح `[CascadingParameter] HttpContext` في الكود التفاعلي؟",
              "options": ["بطيء",
                          "متاح في Static SSR فقط (داخل الطلب) — في الوضع التفاعلي مفيش HttpContext، فالكود بيفشل بعد أول تفاعل",
                          "لأنه ممنوع أمنيًا",
                          "لأنه يعمل في WASM فقط"],
              "answer": 1,
              "explain": "Static SSR بيشتغل داخل طلب HTTP فالـcontext موجود؛ الدائرة/المتصفح مفيش فيهم طلب HTTP لكل حدث. خد هوية المستخدم من `AuthenticationStateProvider` أو مرّر خدمة، ولا تبني منطقًا على HttpContext في مكوّن تفاعلي."},
             {"q": "ما الاستراتيجية الصح لتقليل حجم WASM قبل التفكير في AOT؟",
              "options": ["تفعيل AOT أولًا",
                          "قياس المضغوط (brotli) · تقليل الحزم · lazy loading للمكوّنات/التجميعات الثقيلة · ثم AOT لو فيه حسابات ثقيلة فعلًا",
                          "حذف كل المكتبات",
                          "تقليل عدد الطلبات فقط"],
              "answer": 1,
              "explain": "AOT بيزوّد الحجم ويطوّل البناء. القاعدة: قِس transferred الحقيقي، وقلّل ما تحمّله في البداية (lazy loading)، وراجع تبعياتك. AOT مبرَّر فقط لو فيه حسابات ثقيلة على العميل (صور/رسوم/معالجة بيانات)."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "قرار مبرر + قياس فعلي.",
         "items": [
            {"id": "s8-m2-l1-t1",
             "title": "مهمة 1: تطبيق Blazor Web App بأوضاع مختلطة + قياس",
             "md": "أنشئ `Blazor Web App` (.NET 10) فيه: صفحة محتوى `Static` · صفحة `InteractiveServer` بتجيب بيانات من API · وصفحة/مكوّن `InteractiveWebAssembly` أو `Auto` يشارك نفس المكوّنات المشتركة. ثم قِس: ذاكرة/دائرة على الخادم · وحجم تحميل WASM المضغوط · وزمن الإقلاع.",
             "criteria": [
                 "`Program.cs` فيه `AddRazorComponents().AddInteractiveServerComponents().AddInteractiveWebAssemblyComponents()` و`MapRazorComponents<App>()` بالوضعين + `UseAntiforgery()` + `MapStaticAssets()`.",
                 "**4 صفحات**: Static (محتوى/SEO) · InteractiveServer · InteractiveWebAssembly (أو Auto) · صفحة Static فيها مكوّن تفاعلي واحد كـ«جزيرة».",
                 "مكوّن مشترك في مشروع `.Client` مستخدم من الوضعين — **بلا أي واجهة خادم فقط** ولا أسرار.",
                 "`[PersistentState]` مطبّق على صفحة بتجلب بيانات، وبدليل يوضح **نداءً واحدًا** فقط (عدّاد في الـAPI أو سجل) بدل نداءين.",
                 "قياس ذاكرة: عدد الدوائر وذاكرة العملية قبل/بعد 5 مستخدمين متزامنين (سكربت/أداة)، مع استنتاج «ذاكرة لكل دائرة تقريبًا».",
                 "قياس WASM: حجم `_framework` المضغوط (brotli/gzip) + transferred في Network + زمن LCP على Slow 4G (قبل/بعد lazy loading لمكوّن ثقيل).",
                 "**صفحة قرار (ADR)** فيها: السياق · الخيارات الأربعة · القرار لكل صفحة · العواقب (تكلفة/تعقيد) · ومعيار مراجعة القرار.",
                 "اختبار `bunit` واحد لمكوّن مشترك يثبت حالة من 8.1.4 (خطأ/تحميل/فراغ).",
             ],
             "hint": "إنشاء المشروع: `dotnet new blazor -n Shop.Admin --interactivity Server --all-interactive false` (راجع خيارات القالب في `dotnet new blazor --help` — القالب بيتغير بين الإصدارات). لو الـWASM مش ظاهر: تأكد إن الصفحة `@rendermode InteractiveWebAssembly` وإن مشروع `.Client` مضاف في `AddAdditionalAssemblies`. ولقياس الذاكرة: `dotnet-counters monitor -p <pid> --counters System.Runtime` (مثلًا `dotnet.gc.heap`/`working set`) مع 5 تابات مفتوحة، أو `ps -o rss`. وللـlazy loading: ابدأ بمكوّن تقارير ثقيل واستخدم `BlazorWebAssemblyLazyLoad` — وقِس الفرق في transferred.",
             "solution": "النتائج النموذجية: صفحة Static مالهاش أي JS تقريبًا (بضع كيلوبايت) وتُفهرس بسهولة · InteractiveServer بتدي تفاعل كامل بتحميل أول صغير (~90KB) لكن ذاكرة الخادم بتزيد لكل تاب (عشرات الكيلوبايت لكل دائرة في تطبيق بسيط، وأكتر مع حالة أكبر) · WASM بيبقى تحميله الأول ثقيل (بحدود 2–4MB مضغوط لتطبيق متوسط) وبعدها التفاعل محلي أسرع من Server. و[PersistentState] بيقلل نداءات البيانات للنص — والتأثير الأوضح بيكون في الصفحات اللي بتستعلم استعلامًا ثقيلًا. أهم مخرج: **جدولك أنت** بالأرقام — لأن الأرقام بتختلف مع تبعياتك وشبكتك، والـADR اللي بيوثق القرار بمقياس مراجعة هو اللي بيفرق في المقابلة.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/blazor/components/render-modes",
                 "https://learn.microsoft.com/aspnet/core/blazor/state-management/prerendered-state-persistence",
                 "https://learn.microsoft.com/aspnet/core/blazor/state-management/server",
                 "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/signalr",
                 "https://learn.microsoft.com/aspnet/core/host-and-deploy/blazor/webassembly",
                 "https://bunit.dev/",
             ]},
            {"id": "s8-m2-l1-t2",
             "title": "مهمة 2: اختبار الانقطاع والتوسع (سيناريوهات واقعية)",
             "md": "على تطبيق المهمة 1: اختبر سلوك `InteractiveServer` في أربعة سيناريوهات — انقطاع شبكة قصير · انقطاع طويل (تجاوز مهلة السماح) · إعادة اتصال بعد إيقاف عمدي (`Blazor.pause()` إن كان متاحًا في إصدارك) · ونشر نسخة جديدة أثناء وجود دوائر مفتوحة. وسجّل ما حدث فعلًا وكيف حسّنت التجربة.",
             "criteria": [
                 "سجل لكل سيناريو: ما فعلته · ما ظهر للمستخدم · هل ضاعت الحالة · الوقت حتى الاستعادة.",
                 "**انقطاع قصير** (< 30 ثانية): إعادة اتصال تلقائية وواجهة واضحة (لا شاشة بيضاء).",
                 "**انقطاع طويل** (> `DisconnectedCircuitRetentionPeriod`): سلوك معروف وموثّق + رسالة للمستخدم + **مسودة محفوظة** إن كانت الصفحة نموذجًا.",
                 "إثبات أثر `[PersistentState]` على استعادة الحالة بعد الانقطاع (أو `RestoreBehavior` المناسب).",
                 "**نشر نسخة جديدة أثناء وجود دوائر**: ما الذي يحدث؟ (تحذير للمستخدم/إعادة تحميل) وكيف تمنع فقدان مدخلات.",
                 "التوسع: تشغيل نسختين + موازن بلا sticky sessions → إثبات المشكلة · ثم sticky sessions (أو وسيط) → إثبات الحل.",
                 "جدول ملخص: السيناريو · التوقع · الفعلي · التحسين المطبّق (مع diff).",
                 "قرار مكتوب: هل تحتاج استمرار الدائرة/الدوامات في مشروعك؟ وما التكلفة (ذاكرة/إعداد) مقابل الفائدة؟",
             ],
             "hint": "محاكاة انقطاع الشبكة: DevTools → Network → Offline ثم Online. ولو عايز تتحكم في المهلة بدقة: `DisconnectedCircuitRetentionPeriod = TimeSpan.FromSeconds(20)` في التطوير واختبر. أما «نشر نسخة جديدة» فمحليًا ممكن بإيقاف التطبيق وإعادة تشغيله على المنفذ نفسه — دوائر العملاء هتقع وتعيد الاتصال بالنسخة الجديدة (وده بالظبط سيناريو النشر الحقيقي مع تحديثات مستمرة). ولو مش قادر تجرّب `Blazor.pause()` (توفره بيتغير)، وثّق ذلك واستخدم الانقطاع اليدوي بدلًا منه.",
             "solution": "الملاحظات النموذجية: الانقطاع القصير بيتعافى تلقائيًا وبيبان تنبيه «جارٍ إعادة الاتصال» — وده مقبول. الانقطاع الطويل بيضيّع الحالة إلا لو استخدمت `[PersistentState]`/مسودة على الخادم؛ وأغلب الفرق بتكتشف إن **المستخدم بيقفل التاب وييجي بعد ساعة** فيضيع شغله — والحل الصح مسودة servler-side (API) مش الاعتماد على الدائرة. أما النشر أثناء وجود دوائر فهو أشهر مفاجأة: النسخة الجديدة بتبدأ بلا دوائر قديمة، والمستخدم بيلاقي إعادة اتصال فاشلة أو رسالة — لازم تحذير واضح + حفظ مسودة + خطة نشر (blue-green من 6.3.3). وفي التوسع: بلا sticky sessions بتظهر أخطاء «دائرة غير موجودة» بشكل عشوائي — وده بيبان فورًا لما تجرب نسختين.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/signalr",
                 "https://learn.microsoft.com/aspnet/core/blazor/state-management/server",
                 "https://learn.microsoft.com/aspnet/core/host-and-deploy/blazor/server",
                 "https://learn.microsoft.com/aspnet/core/signalr/scale",
                 "https://learn.microsoft.com/aspnet/core/blazor/components/prerendering-and-integration",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "ASP.NET Core Blazor: أوضاع العرض", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/render-modes"},
            {"label": "Blazor: استمرار الحالة المُ prerendered", "url": "https://learn.microsoft.com/aspnet/core/blazor/state-management/prerendered-state-persistence"},
            {"label": "Blazor: إدارة الحالة على الخادم (استمرار الدائرة)", "url": "https://learn.microsoft.com/aspnet/core/blazor/state-management/server"},
            {"label": "Blazor: أساسيات SignalR وإعادة الاتصال", "url": "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/signalr"},
            {"label": ".NET 10: ما الجديد في ASP.NET Core (Blazor)", "url": "https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0"},
            {"label": "Blazor: النشر واستضافة WASM", "url": "https://learn.microsoft.com/aspnet/core/host-and-deploy/blazor/webassembly"},
            {"label": "bUnit: اختبار المكوّنات", "url": "https://bunit.dev/"},
            {"label": "ASP.NET Core SignalR: التوسع الأفقي", "url": "https://learn.microsoft.com/aspnet/core/signalr/scale"},
        ]},
    ],
}

LESSONS_S8_E = [_L1]
