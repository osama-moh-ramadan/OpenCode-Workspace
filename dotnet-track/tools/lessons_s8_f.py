# -*- coding: utf-8 -*-
"""Stage 8 module 2 (part F): s8-m2-l2 (مكونات Blazor والحالة)."""

TODAY = "2026-10-22"

_L2 = {
    "id": "s8-m2-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "بعد ما اخترت وضع العرض (8.2.1)، السؤال بقى: **إزاي تبني مكوّنات تُعاد استخدامها، وتدير الحالة بينها، وتوصّلها بالـAPI من غير فوضى؟** Blazor مش عنده Redux ولا Pinia — بس عنده أدوات كافية لو عرفت ترتيبها: **Parameters** (واجهة المكوّن) · **EventCallback** (التواصل لفوق) · **Cascading values** (تمرير عبر الشجرة) · **حالة في خدمة Scoped** (للمشترك بين الصفحات) · و`@key`/`ShouldRender`/`Virtualize` للأداء.\n\nوفي الآخر: **إزاي تبني مكوّن API واحدة تعمل في Server وWASM** (نفس الكود، قاعدة مختلفة) — وده أهم مهارة عملية في المسار ده، ويُبنى على آلة الحالات من 8.1.4."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "[Parameter]", "def": "خاصية عامة بتتحدد من الأب — **واجهة المكوّن**. القاعدة: **غير قابل للتعديل** (immutable) — لا تعدّل الـParameter جوه المكوّن، فالانعكاس بيحصل في أوقات مش متوقعة."},
            {"term": "EventCallback<T>", "def": "حدث بيبعت قيمة **لفوق** (مقابل Action/Func في C#، بس بيضمن `StateHasChanged` للأب). `EventCallback` بلا قيمة للحدث المجرّد."},
            {"term": "CascadingValue / [CascadingParameter]", "def": "تمرير قيمة **لأسفل الشجرة** بلا تمريرها يدويًا في كل مستوى (ثيم · لغة · هوية مستخدم · حالة سلة). `IsFixed=\"true\"` بيمنع إعادة التقييم للأداء."},
            {"term": "RenderFragment / ChildContent", "def": "محتوى يمرّره الأب ويتحط جوه المكوّن (`@ChildContent`) — أساس المكوّنات القابلة للتركيب (بطاقة/حوار). و`RenderFragment<T>` للمحتوى المتكرر (قوالب)."},
            {"term": "Scoped service (حالة مشتركة)", "def": "خدمة في نطاق الدائرة/التطبيق: **نسخة واحدة لكل مستخدم (Server) أو لكل تحميل (WASM)**. هي المكان الصح للحالة المشتركة بين الصفحات (سلة/تصفية/إشعارات)."},
            {"term": "@key", "def": "هوية عنصر في حلقة — بتخلي Blazor يحافظ على حالة المكوّن المرتبط بالعنصر (لا يعيد استخدام مكوّن عنصر آخر). مطلوبة للقوائم القابلة للتعديل/الترتيب."},
            {"term": "ShouldRender", "def": "دالة بتحدد هل المكوّن يُعاد رسمه. تُستخدم للأداء في المكوّنات الثقيلة — بس **الادّعاء الخاطئ بيسبب واجهة قديمة** (منطق الـstate لازم يكون صح)."},
            {"term": "Virtualize", "def": "مكوّن مدمج بيعرض العناصر **المرئية فقط** من قائمة طويلة (windowing) مع طلبات مؤجّلة (`ItemsProvider`). ضروري للقوائم الكبيرة."},
            {"term": "OwningComponentBase", "def": "بيدي المكوّن **نطاق DI خاص** (خدمة Scoped تُنشأ وتُدمَّر مع المكوّن) — مفيد لو الخدمة ثقيلة أو تحتاج تُحرَّر بعد الاستخدام."},
            {"term": "State container", "def": "خدمة بتمسك الحالة + حدث `OnChange`، والمكوّنات بتشترك فيها (بديل الأنماط: Flux/Redux مبسطًا). في Blazor دي الطريقة القياسية للحالة المشتركة."},
            {"term": "Component library / RCL", "def": "مكتبة مكوّنات (Razor Class Library) تُشارك بين تطبيقاتك (لوحة إدارة + واجهة العميل) — مع `_Imports.razor` وwwwroot مشتركة."},
            {"term": "JS interop", "def": "نداء JS من C# (`IJSRuntime`) والعكس. يستخدم لأشياء مش مغطاة (مكتبة رسم بياني، clipboard، geolocation). القاعدة: **حدّده في خدمة صغيرة** ولا تنشره في كل مكوّن، ودايمًا `try/catch` لأن الوضع الثابت (prerender) بلا JS."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① خريطة أدوات الحالة: إيه فين"},
        {"type": "table", "caption": "أربع طبقات للحالة — استخدم كل واحدة لغرضها",
         "head": ["نوع الحالة", "المثال", "الأداة", "العمر"],
         "rows": [
             ["**حالة المكوّن**", "مفتوح/مغلق · نص بحث · صفحة حالية · رسالة خطأ", "حقول خاصة في `@code`", "حياة المكوّن"],
             ["**حالة الأب↔الابن**", "قائمة بتاخد بيانات · مكوّن بيبلّغ عن اختيار", "`[Parameter]` لأسفل · `EventCallback<T>` لأعلى", "حياة الأب"],
             ["**حالة عبر الشجرة**", "ثيم · لغة · هوية مستخدم · نموذج حالي", "`CascadingValue`", "حياة الجذر/الدائرة"],
             ["**حالة مشتركة بين الصفحات**", "سلة · تصفية محفوظة · إشعارات · تفضيلات جلسة", "**خدمة Scoped** + حدث `OnChange`", "حياة الدائرة (Server) / التحميل (WASM) — و`[PersistentState]` للحالة اللي تعيش تحول الصفحات"],
             ["**حالة دائمة**", "مسودة · طلبات · طابور مزامنة", "قاعدة بيانات/API (+ IndexedDB في WASM لو أوفلاين)", "دائم"],
         ]},
        {"type": "callout", "kind": "goal", "title": "القاعدة اللي بتمنع الفوضى",
         "md": "**① البيانات القادمة من الخادم = حالة بعيدة** → آلة الحالات (`Remote<T>`/`RemoteState` من 8.1.4) في خدمة أو مكوّن wrapper.\n**② أي حاجة بيشاركها أكتر من مكوّن** → خدمة Scoped (مش `static`!).\n**③ أي حاجة بتحتاج تعيش بعد الدائرة/التحميل** → الخادم (API/DB).\n**④ `static` في Blazor = مشكلة**: الحالة الساكنة في Blazor Server **بتتشارك بين كل المستخدمين** (الدوائر كلها في نفس العملية) — وأخطر من تسريب بيانات. ممنوع.\n**⑤ متعملش `[Parameter]` mutable**: لو محتاج تعديل داخلي، انسخه لحقل خاص في `OnParametersSet`."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② مكوّنات قابلة لإعادة الاستخدام — بالكود"},
        {"type": "code", "lang": "text", "title": "DataState.razor — مكوّن واحد بيلفّ الحالات الست (reusable)", "filename": "src/Shop.Admin.Shared/Components/DataState.razor", "code": r'''@* مكوّن عرض عام: بيستقبل آلة الحالة ويعرض loading/empty/error/content.
   الفكرة: الصفحات تكتب منطق الجلب فقط، والعرض الموحّد هنا. *@
@typeparam T

@* النسخة العامة من آلة الحالات (8.1.4): T = نوع العنصر الواحد المعروض. *@
@code {
    public enum StateKind { Idle, Loading, Refreshing, Success, Empty, Error }

    public sealed record RemoteState<TItem>
    {
        public StateKind Kind { get; init; } = StateKind.Idle;
        public IReadOnlyList<TItem> Data { get; init; } = [];
        public ApiError? Error { get; init; }

        public static RemoteState<TItem> Idle() => new();
        public static RemoteState<TItem> Loading() => new() { Kind = StateKind.Loading };
        public static RemoteState<TItem> Refreshing(IReadOnlyList<TItem> data) => new() { Kind = StateKind.Refreshing, Data = data };
        public static RemoteState<TItem> Success(IReadOnlyList<TItem> data) => new() { Kind = StateKind.Success, Data = data };
        public static RemoteState<TItem> Empty() => new() { Kind = StateKind.Empty };
        public static RemoteState<TItem> Error(ApiError error) => new() { Kind = StateKind.Error, Error = error };
    }
}

@if (State.Kind == StateKind.Loading)
{
    <div class="grid gap-2" aria-hidden="true">
        @for (var i = 0; i < SkeletonRows; i++)
        {
            <div class="card flex animate-pulse items-center justify-between gap-3">
                <div class="grid gap-2">
                    <div class="h-4 w-40 rounded bg-gray-200"></div>
                    <div class="h-3 w-24 rounded bg-gray-200"></div>
                </div>
                <div class="h-4 w-20 rounded bg-gray-200"></div>
            </div>
        }
    </div>
}
else if (State.Kind == StateKind.Empty)
{
    <div class="card grid justify-items-center gap-2 py-10 text-center">
        <p class="font-medium">@(EmptyTitle ?? "لا توجد بيانات")</p>
        @if (!string.IsNullOrEmpty(EmptyHint))
        {
            <p class="max-w-prose text-sm text-ink-muted">@EmptyHint</p>
        }
        @if (EmptyAction is not null)
        {
            <button type="button" class="btn-primary mt-2" @onclick="EmptyAction">@EmptyActionLabel</button>
        }
    </div>
}
else if (State.Kind == StateKind.Error)
{
    <div class="card grid gap-2 border-danger/30 bg-danger/5 py-6 text-center" role="alert">
        <p class="font-medium text-danger">@State.Error!.Title</p>
        @if (!string.IsNullOrEmpty(State.Error.Detail))
        {
            <p class="text-sm text-ink-muted">@State.Error.Detail</p>
        }
        <div class="mt-2 flex flex-wrap items-center justify-center gap-2">
            @if (OnRetry.HasDelegate)
            {
                <button type="button" class="btn-primary" @onclick="OnRetry">إعادة المحاولة</button>
            }
            @if (State.Error.Status == 401)
            {
                <a href="/bff/login" class="rounded-md border px-3 py-2 text-sm">تسجيل الدخول</a>
            }
        </div>
        @if (!string.IsNullOrEmpty(State.Error.CorrelationId))
        {
            <p class="mt-2 text-xs text-ink-muted">مرجع: <code dir="ltr">@State.Error.CorrelationId</code></p>
        }
    </div>
}
else
{
    @* النجاح/التحديث: المحتوى اللي الأب بيحدده *@
    <div class="@(State.Kind == StateKind.Refreshing ? "opacity-70" : "")">
        @ChildContent(State.Data)
    </div>
}

@code {
    /// <summary>الحالة الحالية — النسخة العامة من آلة الحالات في 8.1.4.</summary>
    [Parameter, EditorRequired] public RemoteState<T> State { get; set; } = RemoteState<T>.Idle();

    /// <summary>محتوى العرض عند النجاح — بياخد العناصر.</summary>
    [Parameter, EditorRequired] public RenderFragment<IReadOnlyList<T>> ChildContent { get; set; } = default!;

    [Parameter] public int SkeletonRows { get; set; } = 5;
    [Parameter] public string? EmptyTitle { get; set; }
    [Parameter] public string? EmptyHint { get; set; }
    [Parameter] public string EmptyActionLabel { get; set; } = "إجراء";
    [Parameter] public EventCallback EmptyAction { get; set; }
    [Parameter] public EventCallback OnRetry { get; set; }
}
'''},
        {"type": "code", "lang": "text", "title": "OrdersPage.razor — الصفحة بقت قصيرة (منطق فقط)", "filename": "src/Shop.Admin/Features/Orders/OrdersPage.razor", "code": r'''@page "/orders"
@rendermode InteractiveServer
@attribute [Authorize(Policy = "ApiUser")]
@inject IOrdersApi Api

<PageHeader Title="الطلبات" Subtitle="@($"{_state.Data.Count} طلبًا")">
    <Actions>
        <button type="button" class="rounded-md border px-3 py-1.5 text-sm" @onclick="Reload">تحديث</button>
        <button type="button" class="btn-primary" @onclick="OpenCreate">طلب جديد</button>
    </Actions>
</PageHeader>

<DataState T="OrderDto" State="_state" OnRetry="Reload"
           EmptyTitle="@(_query.Length > 0 ? "لا نتائج مطابقة" : "لا طلبات بعد")"
           EmptyHint="@(_query.Length > 0 ? $"لم نجد شيئًا لـ«{_query}» — جرّب مسح البحث." : "أول ما يصل طلب جديد هيظهر هنا.")"
           EmptyActionLabel="مسح البحث" EmptyAction="ClearQuery">
    <ChildContent Context="orders">
        <ul class="grid gap-2">
            @foreach (var order in orders)
            {
                @* @key ضروري: بدونها Blazor بيعيد استخدام مكوّن عنصر آخر عند الحذف/الترتيب *@
                <OrderRow @key="order.Id" Order="order" OnSelected="Select" />
            }
        </ul>
    </ChildContent>
</DataState>

@code {
    private RemoteState<OrderDto> _state = RemoteState<OrderDto>.Idle();
    private string _query = "";
    private CancellationTokenSource? _cts;

    // [PersistentState] من 8.2.1: ما نعيدش الجلب بعد الـprerender
    [PersistentState]
    public IReadOnlyList<OrderDto>? Cached { get; set; }

    protected override async Task OnInitializedAsync()
    {
        if (Cached is { } cached)
        {
            _state = RemoteState<OrderDto>.Success(cached);
            return;
        }

        await LoadAsync();
    }

    private async Task LoadAsync()
    {
        _cts?.Cancel();
        _cts = new CancellationTokenSource();
        var token = _cts.Token;

        _state = _state.Kind == StateKind.Success
            ? RemoteState<OrderDto>.Refreshing(_state.Data)     // لا نمسح المحتوى
            : RemoteState<OrderDto>.Loading();
        StateHasChanged();

        try
        {
            var items = await Api.GetOrdersAsync(_query, token);
            _state = items.Count == 0 && _query.Length == 0
                ? RemoteState<OrderDto>.Empty()
                : RemoteState<OrderDto>.Success(items);
            Cached = items;
        }
        catch (OperationCanceledException) when (token.IsCancellationRequested)
        {
            return;                          // إلغاء مقصود — لا حالة خطأ
        }
        catch (ApiException ex)
        {
            _state = RemoteState<OrderDto>.Error(ex.ToApiError());
        }
        finally
        {
            StateHasChanged();
        }
    }

    private Task Reload() => LoadAsync();
    private Task ClearQuery() { _query = ""; return LoadAsync(); }
    private void Select(OrderDto order) { /* فتح لوحة التفاصيل… */ }
    private void OpenCreate() { /* … */ }
}
'''},
        {"type": "callout", "kind": "note", "title": "قواعد تصميم المكوّنات (تفرق بين مكتبة ومكوّن عشوائي)",
         "md": "**① واجهة صريحة**: `[Parameter, EditorRequired]` للمطلوب · قيم افتراضية منطقية للباقي · `EventCallback` للأحداث.\n**② بلا اعتماد على الأب**: المكوّن ما يقرأش خدمات الأب أو يفترض ترتيبًا في الصفحة.\n**③ منطق العرض مش منطق العمل**: `DataState` بيعرض؛ الجلب في الصفحة/الخدمة.\n**④ `RenderFragment` للمحتوى**: `ChildContent`/`Header`/`Actions` — تخلق مكوّنات تركيب قوية (بطاقة/حوار/شريط أدوات).\n**⑤ `@typeparam` للمكوّنات العامة**: نفس مكوّن القائمة يخدم `OrderDto` و`CustomerDto`.\n**⑥ اختبار المكوّن بـ`bunit`**: كل حالة (تحميل/فراغ/خطأ/نجاح) اختبار — ودي أسهل بكتير من تقليب الصفحات يدويًا."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ الحالة المشتركة: خدمة Scoped + أحداث"},
        {"type": "code", "lang": "csharp", "title": "CartState.cs — حالة مشتركة (سلة) مع حدث تغيير + استمرار", "filename": "src/Shop.Admin.Shared/State/CartState.cs", "code": r'''using Microsoft.Extensions.Logging;

namespace Shop.Admin.Shared.State;

/// <summary>
/// حالة سلة مشتركة بين مكوّنات كتير.
/// القواعد:
///   • Scoped: نسخة واحدة لكل مستخدم (Server) أو لكل تحميل (WASM) — **لا static**.
///   • التعديل بيعدي على دوال فقط (لا قائمة عامة قابلة للتغيير من بره).
///   • كل تغيير بيرفع حدث؛ المكوّنات بتشترك وبتفك الاشتراك في Dispose.
///   • في مشروع حقيقي: أي تعديل مهم يتأكد من الخادم (8.1.2) — والـoptimistic في 8.1.4.
/// </summary>
public sealed class CartState(ILogger<CartState> log)
{
    private readonly List<CartLine> _lines = [];

    /// <summary>حدث التغيير. EventHandler مش EventCallback (ده للحالة مش لـUI مباشرة).</summary>
    public event EventHandler? Changed;

    public IReadOnlyList<CartLine> Lines => _lines;
    public int ItemCount => _lines.Sum(l => l.Quantity);
    public decimal Total => _lines.Sum(l => l.UnitPrice * l.Quantity);
    public bool IsEmpty => _lines.Count == 0;

    public void Add(string sku, string name, decimal unitPrice, int quantity = 1)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        var index = _lines.FindIndex(l => l.Sku == sku);
        if (index >= 0)
        {
            _lines[index] = _lines[index] with { Quantity = _lines[index].Quantity + quantity };
        }
        else
        {
            _lines.Add(new CartLine(sku, name, unitPrice, quantity));
        }

        log.LogInformation("سلة: أُضيف {Sku} × {Qty} (الإجمالي {Count})", sku, quantity, ItemCount);
        NotifyChanged();
    }

    public void Remove(string sku)
    {
        if (_lines.RemoveAll(l => l.Sku == sku) > 0)
        {
            NotifyChanged();
        }
    }

    public void Clear()
    {
        if (_lines.Count == 0) return;
        _lines.Clear();
        NotifyChanged();
    }

    /// <summary>استبدال كامل (مثلًا بعد استرجاع مسودة من الخادم).</summary>
    public void ReplaceAll(IEnumerable<CartLine> lines)
    {
        _lines.Clear();
        _lines.AddRange(lines);
        NotifyChanged();
    }

    private void NotifyChanged() => Changed?.Invoke(this, EventArgs.Empty);
}

public sealed record CartLine(string Sku, string Name, decimal UnitPrice, int Quantity);
'''},
        {"type": "code", "lang": "text", "title": "CartBadge.razor — اشتراك + تفكيك صحيح (أشهر تسريب في Blazor)", "filename": "src/Shop.Admin.Shared/Components/CartBadge.razor", "code": r'''@inject CartState Cart
@implements IDisposable

<a href="/cart" class="relative inline-flex items-center gap-2 rounded-md px-2 py-1 hover:bg-gray-100">
    القائمة
    @if (Cart.ItemCount > 0)
    {
        <span class="rounded-full bg-brand-600 px-2 py-0.5 text-xs text-white tabular-nums">
            @Cart.ItemCount
        </span>
    }
</a>

<p class="sr-only" role="status" aria-live="polite">@_announcement</p>

@code {
    private string _announcement = "";

    protected override void OnInitialized() => Cart.Changed += OnCartChanged;

    private void OnCartChanged(object? sender, EventArgs e)
    {
        // لو الحدث جه من خارج دورة العرض، لازم InvokeAsync
        _ = InvokeAsync(() =>
        {
            _announcement = $"عدد عناصر السلة: {Cart.ItemCount}";
            StateHasChanged();
        });
    }

    /// <summary>
    /// بدون Dispose: الخدمة Scoped بتعيش أطول من المكوّن،
    /// فبتحتفظ بمرجع للمكوّن = تسريب ذاكرة في Blazor Server (يتراكم لكل تنقل).
    /// </summary>
    public void Dispose() => Cart.Changed -= OnCartChanged;
}
'''},
        {"type": "table", "caption": "أنماط الحالة المشتركة — والمقايضة",
         "head": ["النمط", "كيف", "مناسب لـ", "احتياط"],
         "rows": [
             ["**خدمة Scoped + event**", "الأبسط والأشهر (الكود أعلاه)", "سلة · تصفية · إشعارات · تفضيلات", "**دايمًا `Dispose`** لتفكيك الاشتراك"],
             ["**Cascading + callback**", "`CascadingValue` بقيمة + `EventCallback` للأب", "ثيم · لغة · حالة نموذج متعدد الخطوات", "`IsFixed` للأداء لو القيمة ما بتتغيرش"],
             ["**مكتبة حالة** (Fluxor/BlazorState)", "Redux-like: actions/reducers/store", "تطبيقات كبيرة بفريق كبير", "تعقيد إضافي — مش مبرَّر لمشروع صغير"],
             ["**مخزن على الخادم**", "مسودة في DB/Redis + مفتاح للمستخدم", "نماذج طويلة · عربات تُستأنف بعد ساعات", "ينجو من انقطاع الدائرة/النشر (8.2.1)"],
             ["**`[PersistentState]` على الخدمة**", "`RegisterPersistentService<T>(RenderMode…)`", "حالة سلة/تصفية تعيش تحول الصفحات", "Scoped فقط · وبيانات غير حساسة"],
         ]},
        {"type": "callout", "kind": "danger", "title": "ثلاثة أخطاء حالة خطيرة في Blazor Server",
         "md": "**① `static`**: أي حقل/خدمة `static` بتتشارك بين **كل المستخدمين** على نفس العملية. مرجع StackOverflow شهير: `private static List<Order> orders;` في مكوّن = مستخدم بيشوف طلبات مستخدم تاني (خرق بيانات — 7.2.3).\n**② عدم تفكيك الاشتراك**: الخدمة Scoped/مفردة بتحتفظ بمرجع للمكوّن بعد اختفائه → تسريب ذاكرة يتراكم مع كل تنقل (وبيبان بعد ساعات تشغيل).\n**③ تعديل الـParameter**: `[Parameter]` بيتبع القيم من الأب؛ لو المكوّن عدّله، الأب مش هيعرف والقيمة هتترجع في الـrender التالي — النتيجة حالة غامضة. انسخ في `OnParametersSet` وعدّل النسخة."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ مكوّن API واحد للوضعين (Server/WASM) — أهم مهارة عملية"},
        {"type": "code", "lang": "csharp", "title": "IOrdersApi + تنفيذين (HTTP للـWASM · مباشر للـServer) + تسجيل حسب الوضع", "filename": "src/Shop.Admin.Shared/Api/OrdersApi.cs", "code": r'''namespace Shop.Admin.Shared.Api;

/// <summary>
/// العقد الوحيد اللي بيعتمد عليه كل الكود المشترك.
/// التنفيذ بيتغير حسب الوضع: في WASM لازم HTTP (لا EF ولا DB في المتصفح)،
/// وفي Server ممكن يكون مباشر (EF) أو HTTP — حسب المعمارية.
/// </summary>
public interface IOrdersApi
{
    Task<IReadOnlyList<OrderDto>> GetOrdersAsync(string? query = null, CancellationToken ct = default);
    Task<OrderDto> CreateAsync(CreateOrderRequest request, CancellationToken ct = default);
}

public sealed record OrderDto(string Id, string Status, string Total, string Currency, DateTimeOffset PlacedAt);
public sealed record CreateOrderRequest(string Sku, int Quantity);

// ── تنفيذ 1: HTTP (يعمل في المتصفح والـServer) ────────────────────────
public sealed class HttpOrdersApi(IHttpClientFactory factory) : IOrdersApi
{
    public async Task<IReadOnlyList<OrderDto>> GetOrdersAsync(string? query = null, CancellationToken ct = default)
    {
        var client = factory.CreateClient("shop-api");
        var url = "orders" + (string.IsNullOrWhiteSpace(query) ? "" : $"?q={Uri.EscapeDataString(query)}");
        var items = await client.GetFromJsonAsync<List<OrderDto>>(url, ct);
        return items ?? [];
    }

    public async Task<OrderDto> CreateAsync(CreateOrderRequest request, CancellationToken ct = default)
    {
        var client = factory.CreateClient("shop-api");
        using var response = await client.PostAsJsonAsync("orders", request, ct);
        response.EnsureSuccessStatusCode();
        return (await response.Content.ReadFromJsonAsync<OrderDto>(ct))!;
    }
}

// ── تنفيذ 2: مباشر على الخادم (لو المشروع monolithic وبلا API) ─────────
public sealed class ServerOrdersApi(ShopDbContext db) : IOrdersApi
{
    public async Task<IReadOnlyList<OrderDto>> GetOrdersAsync(string? query = null, CancellationToken ct = default)
    {
        var q = db.Orders.AsNoTracking();
        if (!string.IsNullOrWhiteSpace(query))
        {
            q = q.Where(o => EF.Functions.Like(o.Reference, $"%{query}%"));
        }

        return await q.OrderByDescending(o => o.PlacedAt)
            .Take(200)
            .Select(o => new OrderDto(o.Reference, o.Status.ToString(), o.Total.ToString(), o.Currency, o.PlacedAt))
            .ToListAsync(ct);
    }

    public async Task<OrderDto> CreateAsync(CreateOrderRequest request, CancellationToken ct = default)
    {
        // منطق الإنشاء الحقيقي في 2.2.x/5.2.5 (idempotency!)
        // Order = كيان المشروع (المراحل 3–4) — مش DTO
        var order = new Order { Reference = $"ORD-{Random.Shared.Next(1000, 9999)}", PlacedAt = DateTimeOffset.UtcNow };
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return new OrderDto(order.Reference, "placed", "0", "EGP", order.PlacedAt);
    }
}
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — التسجيل حسب الوضع (سطر واحد يفرق)", "filename": "src/Shop.Admin/Program.cs (تسجيل الخدمات)", "code": r'''// ═══ على الخادم ══════════════════════════════════════════════════════
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents()
    .AddInteractiveWebAssemblyComponents();

// نسخة الخادم: HTTP client موجّه للـAPI (أو ServerOrdersApi لو monolith)
builder.Services.AddScoped<IOrdersApi>(sp =>
    new HttpOrdersApi(sp.GetRequiredService<IHttpClientFactory>()));
builder.Services.AddHttpClient("shop-api", c => c.BaseAddress = new Uri(builder.Configuration["Api:BaseUrl"]!));

// …

// ═══ على العميل (Program.cs في مشروع .Client) ════════════════════════
// نفس العقد — تنفيذ HTTP فقط (مفيش DB في المتصفح)
var clientBuilder = WebAssemblyHostBuilder.CreateDefault(args);
clientBuilder.Services.AddScoped<IOrdersApi>(sp =>
    new HttpOrdersApi(sp.GetRequiredService<IHttpClientFactory>()));
clientBuilder.Services.AddHttpClient("shop-api", c => c.BaseAddress = new Uri(clientBuilder.Configuration["Api:BaseUrl"]!));
await clientBuilder.Build().RunAsync();

// ═══ النتيجة ═════════════════════════════════════════════════════════
// كل المكوّنات المشتركة بتستخدم IOrdersApi — فبتعمل في الوضعين بلا تغيير.
// ═══ التحذير ═════════════════════════════════════════════════════════
// أي تنفيذ بيتحمّل في المتصفح لازم يكون آمنًا:
//   • بلا أسرار/connection strings (8.2.1).
//   • والـAPI على الخادم هو اللي بيفرض الصلاحيات (7.2.3) — لا تعتمد على إخفاء زر.
'''},
        {"type": "code", "lang": "text", "title": "OnParametersSetAsync مقابل OnInitializedAsync — وإزاي تتجنب النداء المزدوج", "filename": "docs/blazor-lifecycle.md", "code": r'''## دورة الحياة — الترتيب والأثر العملي

~~~text
SetParametersAsync (الأب بيمرر قيم جديدة)
  ├─ OnInitialized / OnInitializedAsync     ← مرة واحدة عند أول إنشاء
  ├─ OnParametersSet / OnParametersSetAsync ← كل مرة تتغير قيم الـParameters
  ├─ (render)
  └─ OnAfterRender(Async) firstRender       ← بعد ما الـDOM اترسم (JS interop مسموح هنا فقط)
~~~

| الحالة | استخدم |
|---|---|
| جلب بيانات أول مرة | `OnInitializedAsync` (+ `[PersistentState]` لتجنب التكرار) |
| جلب بيانات **بتعتمد على Parameter** (زى `OrderId`) | `OnParametersSetAsync` |
| التعامل مع DOM/JS (رسم، قياس، مكتبة) | `OnAfterRenderAsync(firstRender: true)` |
| تغيير قيم الـParameters جوّه المكوّن | ❌ ممنوع — انسخ في `OnParametersSet` |
| إلغاء العمل عند تفكيك المكوّن | `IDisposable`/`IAsyncDisposable` + `CancellationTokenSource` |

## فخّ «النداء المزدوج» — مثلث الحل
1) جلب في `OnInitializedAsync` + prerender مفعّل
   → بيتنفذ مرتين (SSR ثم تفاعلي).
2) `[PersistentState]` على النتيجة + `??=` → نداء واحد ✅
3) ولو البيانات حساسة للوقت: `RestoreBehavior = SkipInitialValue` (8.2.1).

## فخّ «النداء المتكرر» مع Parameters
كل تغيّر Parameter بيعيد `OnParametersSetAsync` — فجلب بلا `??=` أو بلا مقارنة
بالقيمة السابقة بيعمل طلبات مكررة مع كل رسمة. الحل: قارن بالقيمة القديمة وسجّل آخر Id.
~~~csharp
private string? _loadedId;
protected override async Task OnParametersSetAsync()
{
    if (_loadedId == OrderId) return;      // ما تعيدش الجلب لنفس الـId
    _loadedId = OrderId;
    await LoadAsync();
}
~~~
'''},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ الأداء: 4 أدوات تكفي"},
        {"type": "table", "caption": "تحسين الأداء في Blazor — بالترتيب الصحيح",
         "head": ["الأداة", "تحل إيه", "مثال", "الفخّ"],
         "rows": [
             ["**`@key`**", "إعادة استخدام مكوّن لعنصر مختلف في حلقة (فقدان تركيز/حالة)", "`<OrderRow @key=\"order.Id\" …>`", "مفتاح متغيّر كل رسمة (مثل `Guid.NewGuid()`) = إعادة بناء دائمًا"],
             ["**`Virtualize`**", "قوائم آلاف العناصر — يرسم المرئي فقط", "`<Virtualize Items=\"_orders\" Context=\"o\">…</Virtualize>` أو `ItemsProvider` للجلب التدريجي", "محتاج ارتفاع صف ثابت وإلا بيحسب غلط"],
             ["**`ShouldRender`**", "منع إعادة رسم مكوّن ثقيل بلا تغيير", "قارن معاملات في `ShouldRender`", "منطق خاطئ = واجهة قديمة (صعب تشخيصه)"],
             ["**`IsFixed` في Cascading**", "إعادة تقييم كل مستهلكين القيمة المشتركة", "`<CascadingValue Value=\"Theme\" IsFixed=\"true\">`", "لو القيمة بتتغير فعلًا، لا تستخدمه"],
             ["**`OwningComponentBase`**", "خدمة ثقيلة تُنشأ/تُحرَّر مع المكوّن", "لوحة تقارير بتفتح DbContext خاص", "نطاق مختلف = النسخة مش مشتركة مع باقي المكوّنات"],
             ["**lazy loading (WASM)**", "حجم التحميل الأول", "تجميعات التقارير تُحمّل عند الحاجة", "تأخير أول فتح للصفحة المؤجلة"],
             ["**pagination (API)**", "جلب آلاف الصفوف من الخادم", "cursor pagination (2.2.2)", "الـ`Virtualize` بلا `ItemsProvider` بتحمّل الكل في الذاكرة"],
         ]},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ نمط عملي: صفحة الطلبات كاملة مع الحالة والصلاحيات"},
        {"type": "code", "lang": "text", "title": "Authorization + تركيب المكوّنات (Header/Actions/Card) + JS interop محدود", "filename": "docs/blazor-patterns.razor", "code": r'''@* ═══ الصلاحيات: التفويض في الخادم أيضًا، والواجهة للعرض فقط ═══ *@
@attribute [Authorize(Policy = "Orders.Read")]
@inject AuthenticationStateProvider AuthProvider

@* لو عايز تظهر/تخفي عناصر حسب الدور: *@
<AuthorizeView Policy="Orders.Manage">
    <Authorized>
        <button type="button" class="btn-primary" @onclick="OpenCreate">طلب جديد</button>
    </Authorized>
    <NotAuthorized>
        <span class="text-xs text-ink-muted">لا تملك صلاحية الإنشاء</span>
    </NotAuthorized>
</AuthorizeView>

@* أو بـRoles: <AuthorizeView Roles="admin,manager"> … </AuthorizeView> *@

@code {
    // في الكود: خد الهوية من AuthenticationStateProvider — لا من HttpContext (8.2.1)
    protected override async Task OnInitializedAsync()
    {
        var state = await AuthProvider.GetAuthenticationStateAsync();
        var user = state.User;
        if (!user.Identity?.IsAuthenticated ?? true)
        {
            return;   // التوجيه بيحصل عبر [Authorize] أو الـlayout
        }

        _displayName = user.FindFirst("name")?.Value ?? user.Identity!.Name ?? "مستخدم";
    }

    private string _displayName = "";
    private void OpenCreate() { /* … */ }
}

@* ═══ مكوّنات تركيب: Header بعناصر إضافية ═════════════════════════════ *@
<PageHeader Title="الطلبات">
    <Actions>
        <button class="rounded-md border px-3 py-1.5 text-sm">تصدير</button>
    </Actions>
</PageHeader>

@* PageHeader.razor *@
@code {
    [Parameter, EditorRequired] public string Title { get; set; } = "";
    [Parameter] public string? Subtitle { get; set; }
    [Parameter] public RenderFragment? Actions { get; set; }
}

@* ═══ JS interop: محدود وموثّق ═══════════════════════════════════════
   1) عرّف دالة JS صغيرة في wwwroot/js/shop.js
   2) غلّفها في خدمة C# واحدة (IosService) مع try/catch
   3) استدعها في OnAfterRenderAsync (مش OnInitialized — الـDOM مش جاهز)
   4) في prerender (static) مفيش JS: تحقق أولًا أو استخدم try/catch
*@
@inject IJSRuntime JS
@code {
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (!firstRender) return;
        try
        {
            await JS.InvokeVoidAsync("shop.focusFirstInput", "orders-search");
        }
        catch (JSException)
        {
            // بيحصل في prerender/SSR — مش خطأ حقيقي
        }
    }
}
'''},
        {"type": "callout", "kind": "note", "title": "Blazor و`AuthorizeView`: إخفاء الزر مش تفويض",
         "md": "`AuthorizeView` بيغيّر **ما يُعرض** — لكنه **ليس** حدّ أمان: في WASM كل الكود والبيانات متاحة للمستخدم، وفي Server المستخدم يقدر يستدعي الـAPI مباشرة. التفويض الحقيقي دايمًا على الخادم: policies على الـendpoints (2.2.1) + فحص ملكية المورد (7.2.3) + اختبارات (7.2.4). الواجهة بس بتخفي ما مالوش لازمة عشان التجربة.\n\nونفس الكلام على `[Authorize]` في Blazor WebAssembly: بيحمي **تجربة التنقل** وبيعتمد على حالة مصادقة مزوّد حقيقي — لكن الحماية الفعلية للبيانات في الـAPI."},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ مكتبة مكوّنات مشتركة: تنظيم المشروع"},
        {"type": "code", "lang": "text", "title": "بنية حل نموذجية (Blazor Web App + مشاريع مشتركة)", "filename": "docs/blazor-solution-layout.txt", "code": r'''Shop.sln
├── src/Shop.Domain/                 # كيانات وقواعد الأعمال (بلا اعتماد على UI)
├── src/Shop.Infrastructure/         # EF Core · تكاملات · تنفيذ الـAPI الداخلي
├── src/Shop.Api/                    # ASP.NET Core API (يستهلكه WASM والواجهات)
├── src/Shop.Admin/                  # Blazor Web App (خادم: SSR + InteractiveServer)
│   ├── Components/App.razor
│   ├── Components/Routes.razor
│   └── Program.cs                   # Registration للخادم
├── src/Shop.Admin.Client/           # المكوّنات المشتركة اللي بتشتغل في المتصفح
│   ├── _Imports.razor
│   ├── Components/                  # DataState · PageHeader · OrderRow …
│   ├── Pages/                       # صفحات تفاعلية
│   ├── State/CartState.cs           # Scoped + event (8.2.2 ③)
│   ├── Api/OrdersApi.cs             # IOrdersApi + HttpOrdersApi
│   └── Program.cs                   # Registration للمتصفح
├── src/Shop.Ui.Shared/              # (اختياري) RCL لمكونات مشتركة بين لوحات متعددة
│   ├── _Imports.razor
│   ├── wwwroot/                     # CSS/صور/خطوط
│   └── Components/*.razor
└── tests/
    ├── Shop.Admin.Tests/            # bunit للمكوّنات + اختبارات الحالة
    └── Shop.Api.Tests/              # تكامل (1.2.5)

## قواعد ثابتة
1) المشروع `.Client` **ممنوع** يشير لمشروع الخادم أو Infrastructure (وإلا أسرار/حزم للنات).
2) أي كود مشترك لازم يشتغل في الوضعين: بلا EF، بلا IO، بلا HttpContext.
3) الأنواع المشتركة (DTOs) في مشروع مشترك — لا تكرار.
4) `_Imports.razor` في المشترك بيخدم كل المكونات المشتركة.
5) CSS/أصول في `wwwroot` المشترك أو في الخارج (8.1.3) — لا تعتمد على مسارات الخادم.
6) المكتبات: راجع حجم تأثيرها على WASM (8.2.1 ⑤) قبل إضافتها.
'''},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أختار الأداة الصح لكل نوع حالة: مكوّن · Parameter/EventCallback · Cascading · خدمة Scoped · خادم.",
            "أعرف إن `static` في Blazor Server بيتشارك بين كل المستخدمين (خرق بيانات) وأتجنبه.",
            "أبني مكوّنًا قابلًا لإعادة الاستخدام بـ`[Parameter, EditorRequired]` · `EventCallback<T>` · `ChildContent` · `@typeparam`.",
            "أدير حالة مشتركة بخدمة Scoped + حدث، **وأفك الاشتراك في `Dispose`** (وإلا تسريب ذاكرة).",
            "أعرف إن `[Parameter]` لازم يفضل غير معدّل وأنسخه في `OnParametersSet` عند الحاجة.",
            "أفرّق بين `OnInitializedAsync` و`OnParametersSetAsync` و`OnAfterRenderAsync` وأستخدم كل واحد صح.",
            "أمنع النداء المزدوج والمتكرر (`[PersistentState]` + مقارنة الـId).",
            "أبني `IOrdersApi` بت في تنفيذين (HTTP/Mobily) وأسجل حسب الوضع — فالمكوّنات المشتركة تعمل في Server وWASM.",
            "أستخدم أدوات الأداء بالترتيب: `@key` · `Virtualize` · `ShouldRender` · `IsFixed` · `OwningComponentBase` · pagination.",
            "أعرف أن `AuthorizeView`/`[Authorize]` للعرض فقط وأن التفويض الحقيقي في الـAPI.",
            "أنظّم الحل بحيث مشروع `.Client` بلا وصول للخادم/Infrastructure وبلا أسرار.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على مكونات Blazor والحالة.",
         "questions": [
             {"q": "زميلك كتب `private static List<OrderDto> _cache = new();` في مكوّن Blazor Server. ما الخطر؟",
              "options": ["لا خطر، static سريع",
                          "الحالة الساكنة مشتركة بين **كل** المستخدمين على نفس العملية → مستخدم يقدر يشوف بيانات مستخدم آخر",
                          "بطء في الأداء فقط",
                          "خطأ ترجمة"],
              "answer": 1,
              "explain": "في Blazor Server كل الدوائر بتشتغل في نفس العملية، فالـstatic مشترك بين الجميع — خرق بيانات حقيقي (7.2.3) وأخطر من مجرد تسريب ذاكرة. الحل: خدمة Scoped (نسخة لكل مستخدم) أو حالة مكوّن."},
             {"q": "متى تستخدم `OnParametersSetAsync` بدل `OnInitializedAsync`؟",
              "options": ["دائمًا",
                          "عندما يعتمد جلب البيانات على قيمة Parameter (مثل OrderId) تتغير من الأب — مع مقارنة بالقيمة السابقة لتفادي الطلبات المتكررة",
                          "في WASM فقط",
                          "عندما تحتاج JS"],
              "answer": 1,
              "explain": "`OnParametersSetAsync` بيتنفذ مع كل تغيير في الـParameters — فلو جلبت بلا مقارنة هتعمل طلبات مكررة مع كل رسمة. سجّل آخر Id وسجّل مقارنة. أما `OnInitializedAsync` فأول مرة فقط (مع prerender بيتنفذ مرتين — 8.2.1)."},
             {"q": "لماذا يجب `Dispose` لتفكيك `Cart.Changed -= OnCartChanged`؟",
              "options": ["تحسين جمالي",
                          "الخدمة Scoped/المفردة بتعيش أطول من المكوّن فبتحتفظ بمرجعه → تسريب ذاكرة يتراكم لكل تنقل",
                          "لمنع الاستثناءات",
                          "لأن Blazor يمنع الاشتراك"],
              "answer": 1,
              "explain": "كل تنقل بيعمل مكوّن جديد; الاشتراك القديم بيفضل معلّق على الخدمة فيمنع جمع المكوّن. الأعراض: ذاكرة بتزيد مع الوقت وزمن استجابة بيسوء. القاعدة: كل `+=` له `-=` في `Dispose`."},
             {"q": "أفضل طريقة لتمرير «الثيم» لكل المكوّنات؟",
              "options": ["Parameter في كل مكوّن",
                          "`CascadingValue` مع `IsFixed=\"true\"` لو القيمة ما بتتغيرش (أو بدونها لو بتتغير)",
                          "static field",
                          "localStorage في كل مكوّن"],
              "answer": 1,
              "explain": "Cascading بيخدم الشجرة كلها بلا تمرير يدوي — والمستهلكون بيعيدوا التقييم لما تتغير القيمة. `IsFixed` بيحسّن الأداء لما القيمة ثابتة؛ لكن استخدامه مع قيمة متغيرة بيدي قيم قديمة."},
             {"q": "لديك قائمة 10,000 صف. ما الحل الصحيح؟",
              "options": ["عرض الكل بـ`@key` فقط",
                          "`Virtualize` (windowing) + `ItemsProvider` للجلب من الـAPI على دفعات — بدل تحميل الكل في الذاكرة",
                          "`ShouldRender` فقط",
                          "تحميل الكل ثم فلترة في المتصفح"],
              "answer": 1,
              "explain": "`Virtualize` بترسم المرئي فقط، و`ItemsProvider` بتخلي الجلب تدريجيًا (متناسق مع pagination/cursor 2.2.2). `@key` مهمة للصحة لكنها مش بتحل حجم البيانات، و`ShouldRender` بتحل الرسم لا حجم البيانات."},
             {"q": "كيف تجعل نفس المكوّن يعمل في InteractiveServer وInteractiveWebAssembly؟",
              "options": ["نسختين من المكوّن",
                          "عقد `IOrdersApi` واحد + تنفيذ HTTP (للـWASM) وتنفيذ HTTP/مباشر (للـServer) مسجّل بـDI حسب الوضع",
                          "استخدام EF Core في المتصفح",
                          "قراءة HttpContext"],
              "answer": 1,
              "explain": "المكوّن المشترك يعتمد على الواجهة فقط. في المتصفح لازم HTTP (مفيش DB ولا أسرار)، وفي الخادم ممكن HTTP أو EF مباشرة. نفس الكود يعمل في الوضعين — وده نمط الـports/adapters (4.x) مطبّقًا على الـUI."},
             {"q": "هل `AuthorizeView` حماية كافية لمنع مستخدم من تنفيذ عملية إدارية؟",
              "options": ["نعم",
                          "لا — إخفاء عرض فقط؛ الحماية في الـAPI (policies + فحص ملكية) وفي WASM كل الكود متاح",
                          "نعم في WASM فقط",
                          "نعم لو مع `[Authorize]`"],
              "answer": 1,
              "explain": "أي حماية في الواجهة قابلة للتجاوز (المستخدم يقدر يستدعي الـAPI مباشرة أو يعدّل الحالة). التفويض دايمًا على الخادم — والواجهة للعرض فقط (7.2.3). واختبار T-001 (IDOR) بيثبت ده."},
             {"q": "متى تستخدم `OwningComponentBase`؟",
              "options": ["دائمًا بدل Scoped",
                          "عندما تحتاج خدمة Scoped تُنشأ وتُحرَّر مع المكوّن (خدمة ثقيلة/DbContext خاص بلوحة معينة)",
                          "في WASM فقط",
                          "لجعل الحالة عامة بين كل المستخدمين"],
              "answer": 1,
              "explain": "بيدي نطاق DI خاصًا بالمكوّن — مفيد لخدمة ثقيلة أو سياق قاعدة بيانات للوحة قراءة فقط. لكن النسخة بتبقى معزولة عن الخدمات المشتركة، فما تستخدمهاش للحالة المشتركة (اللي محتاجة Scoped عادي)."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "مكوّنات مشتركة + حالة تعمل في الوضعين.",
         "items": [
            {"id": "s8-m2-l2-t1",
             "title": "مهمة 1: مكتبة مكوّنات مشتركة (DataState + PageHeader + Row)",
             "md": "ابنِ في مشروع `.Client`/Shared ثلاث مكوّنات: `DataState<T>` (يعرض الحالات الست من 8.1.4) · `PageHeader` (Title/Subtitle/Actions مع `RenderFragment`) · `OrderRow` (يقبل `OrderDto` ويبلّغ بالاختيار عبر `EventCallback<OrderDto>`). استخدمها في صفحة طلبات كاملة مع بحث وإلغاء وجلب آمن.",
             "criteria": [
                 "`DataState<T>` بـ`@typeparam` + `[Parameter, EditorRequired]` + `RenderFragment<IReadOnlyList<T>>` + `OnRetry`/`EmptyAction` + skeleton مع `aria-hidden` + `role=\"alert\"` للخطأ + `correlationId`.",
                 "`PageHeader` فيه `RenderFragment? Actions` ويُستخدم في ≥ 3 صفحات بلا تكرار.",
                 "`OrderRow` يقبل بيانات + `EventCallback<OrderDto>` (لا يعدّل الـParameter) ويستخدم `@key` عند عرضه في حلقة.",
                 "الصفحة: بحث + إلغاء (`CancellationTokenSource`) + `refreshing` بلا مسح المحتوى + 3 حالات فراغ + `[PersistentState]` لتقليل النداء المزدوج.",
                 "**لا `static`** في أي حالة (فحص grep) ولا تعديل Parameter.",
                 "`bunit`: **4 اختبارات** على الأقل (loading · empty · error 403 يعرض خطأ لا فراغ · success) + اختبار إن `OrderRow` بيبلّغ بالاختيار.",
                 "قياس صغير: عدد أسطر صفحة الطلبات قبل/بعد استخراج `DataState` (دليل إعادة الاستخدام).",
             ],
             "hint": "في `bunit` لاختبار `RenderFragment` استخدم `cut.FindAll(\"li\")` بعد `WaitForAssertion`. ولاختبار `EventCallback` استخدم `cut.Find(\"button\").Click()` ثم تحقق من المتغير اللي استقبل القيمة في الأب. ولو الـskeleton ظهر في الاختبار بسرعة، اقصر تأخير 8.1.4 في بيئة الاختبار (أو افصل المنطق في خدمة قابلة للاختبار). وتأكد إن `_Imports.razor` في المشترك فيه `@using Shop.Admin.Shared.Components`.",
             "solution": "النتائج النموذجية: صفحة الطلبات بتنزل من ~220 سطرًا إلى ~120 بعد استخراج `DataState` — والتكرار بين الصفحات بيختفي. الاختبارات بتكشف حاجات مش باينة بالعين: `aria-hidden` في الـskeleton، وإن الخطأ 403 بيتعرض كخطأ مش فراغ، وإن `OrderRow` فعلًا بيبلّغ بالمعرّف الصح. أصعب جزء عملي: تمرير `RenderFragment<T>` مع سياق (`Context=\"orders\"`) — لو نسيت `Context` هتلاقي خطأ ترجمة غير واضح؛ اكتبه صراحةً. وأهم تحسين جودة: **كل حالة من الست** بقى لها اختبار، فأي تعديل مستقبلي في العرض بيتحقق آليًا.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/blazor/components/",
                 "https://learn.microsoft.com/aspnet/core/blazor/components/templated-components",
                 "https://learn.microsoft.com/aspnet/core/blazor/components/lifecycle",
                 "https://bunit.dev/docs/getting-started/",
             ]},
            {"id": "s8-m2-l2-t2",
             "title": "مهمة 2: حالة مشتركة (سلة) + خدمة API للوضعين + استمرار",
             "md": "نفّذ `CartState` (Scoped + حدث تغيير) و`CartBadge` (اشتراك/تفكيك) و`IOrdersApi` بت في تنفيذين مع تسجيل حسب الوضع، وطبّق `[PersistentState]`/`RegisterPersistentService` للـCartState لتعيش تحول الصفحات. واختبر أن كل ده يشتغل في `InteractiveServer` و`InteractiveWebAssembly` (أو `Auto`).",
             "criteria": [
                 "`CartState`: قائمة خاصة + دوال تعديل فقط + `Changed` event + خصائص محسوبة (`ItemCount`/`Total`) + `ReplaceAll` للاسترجاع.",
                 "`CartBadge`: يشترك في `OnInitialized` ويفك في `Dispose` **مع `InvokeAsync`** لتحديث الواجهة من حدث خارجي · وإعلان `aria-live` لعدد العناصر.",
                 "**≥ 3 مكوّنات** بتستخدم `CartState` (Badge · زر إضافة · صفحة السلة) — والتغيير في واحد بيتنعكس في الكل فورًا.",
                 "`IOrdersApi` + `HttpOrdersApi` (للـWASM) + تنفيذ للـServer، ومسجّل في `Program.cs` للطرفين — والمكوّنات المشتركة تشتغل في الوضعين **بلا تعديل**.",
                 "`[PersistentState]`/`RegisterPersistentService` مطبّق على `CartState` (مع مراعاة إن البيانات غير حساسة).",
                 "إثبات بمقياس/سجل: التحول بين صفحتين **ما بيضيّعش** محتوى السلة.",
                 "اختبار `bunit` للحالة: إضافة/حذف/تفريغ + حدث التغيير + العدد والإجمالي — واختبار للمكوّن بعدم تسريب الاشتراك (بعد `Dispose` الحدث ما بيأثرش).",
                 "قرار مكتوب: هل تخزين السلة في الخادم (بعد الدائرة) مطلوب لمنتجك؟ وما تكلفته؟ (8.2.1).",
             ],
             "hint": "لو الحدث بيترمي من مكوّن تاني في نفس الدورة، `InvokeAsync` آمن. ولـ`[PersistentState]` على خدمة: `builder.Services.AddScoped<CartState>();` + `RegisterPersistentService<CartState>(RenderMode.Server)` — انتبه: الخدمات المسجلة كده لازم تكون Scoped والخصائص المراد حفظها عليها `[PersistentState]`. واختبر إعادة التحميل بعد تحويل الوضع: في `Auto`، أول تنقل للسيرفر والتاني للمتصفح — راقب إن السلة لسه موجودة (ودي أهم تجربة لـ`InteractiveAuto`).",
             "solution": "الملاحظات النموذجية: أول نسخة بتنسى `InvokeAsync` فالعداد ما بيتحدثش لما التغيير يحصل من مكوّن تاني (أو بتظهر رسالة «The current thread is not associated with the Dispatcher») — والحل هو اللف بـ`InvokeAsync`. ثانيًا: بدون `Dispose` بيحصل تسريب — بيتضح بشكل حقيقي لوحة المراقبة بعد تنقلات كثيرة. ثالثًا: في `Auto` الحالة بتنتقل عبر `PersistentState`، لكن أي بيانات جايّة من `IOrdersApi` بتُجلب مرة أخرى في الوضع الجديد إلا لو فيه كاش/`[PersistentState]`. وأهم قرار معماري بيطلع من المهمة: **السلة الحقيقية لازم تكون في الخادم** (مسودة مرتبطة بالمستخدم) لأن الدائرة/التحميل بيتصفرا — والـ`CartState` في الذاكرة تبقى طبقة عرض سريعة فوقها.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/blazor/state-management/",
                 "https://learn.microsoft.com/aspnet/core/blazor/components/prerendering-and-integration",
                 "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/dependency-injection",
                 "https://learn.microsoft.com/aspnet/core/blazor/components/event-handling",
                 "https://bunit.dev/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Blazor: أساسيات المكوّنات", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/"},
            {"label": "Blazor: المكوّنات القابلة للتركيب (RenderFragment)", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/templated-components"},
            {"label": "Blazor: إدارة الحالة", "url": "https://learn.microsoft.com/aspnet/core/blazor/state-management/"},
            {"label": "Blazor: حقن التبعية", "url": "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/dependency-injection"},
            {"label": "Blazor: معالجة الأحداث", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/event-handling"},
            {"label": "Blazor: تحسين أداء المكوّنات (Virtualize)", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/virtualization"},
            {"label": "Blazor: دورة حياة المكوّن", "url": "https://learn.microsoft.com/aspnet/core/blazor/components/lifecycle"},
            {"label": "bUnit", "url": "https://bunit.dev/"},
        ]},
    ],
}

LESSONS_S8_F = [_L2]
