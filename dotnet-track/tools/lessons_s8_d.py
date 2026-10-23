# -*- coding: utf-8 -*-
"""Stage 8 module 1 (part D): s8-m1-l4 (حالات الواجهة: تحميل وخطأ وفراغ)."""

TODAY = "2026-10-22"

_L4 = {
    "id": "s8-m1-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الفرق بين واجهة «بتشتغل» وواجهة «محترفة» مش في الألوان — في **الحالات**: إيه اللي بيحصل أول ما تفتح الصفحة؟ وإيه اللي تشوفه وهي بتجيب البيانات؟ ولو مفيش بيانات؟ ولو الخادم وقع؟ ولو النت قطع؟ أغلب المطورين بيكتبوا حالة النجاح بس، فالمنتج بيبدو مكسورًا في أول يوم استخدام حقيقي. في الدرس ده: **آلة حالات** واحدة (TS) بتشتغل في أي إطار · تنفيذها في React وفي Blazor جنبًا لجنب · قواعد التحميل (skeleton مقابل spinner وتأخير 200ms وحجز المساحة) · أنواع الحالات الفارغة · معالجة الأخطاء بربطها بالـcorrelationId · **optimistic UI** بـrollback · والوصولية (aria-live وإدارة التركيز) — و12 تفصيلة صغيرة بتفرّق."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "الحالات الست لأي بيانات بعيدة", "def": "`idle` (ما طلبناش لسه) · `loading` (جارٍ الجلب) · `success` (فيه بيانات) · `empty` (نجح بس صفر نتائج) · `error` (فشل) · `partial/stale` (فيه بيانات قديمة وبنجلب الأحدث). **empty مش حالة من error** — ده أشهر خلط."},
            {"term": "Skeleton", "def": "هيكل رمادي بنفس شكل المحتوى المتوقع، بيومي (`animate-pulse`). بيقلل الإحساس بالانتظار **لأنه بيحجز المساحة** — بشرط يكون قريبًا من الشكل النهائي، وإلا يبقى كذب بصري."},
            {"term": "Spinner", "def": "مؤشر دوران عام. مناسب للعمليات **غير معروفة المدة/الشكل** (حفظ · إرسال) — ومش مناسب لجلب قائمة (استخدم skeleton أو احتفظ بالمحتوى القديم)."},
            {"term": "تأخير 200ms", "def": "لا تعرض spinner قبل 200–300ms من بدء الطلب: لو الرد أسرع، الـspinner بيظهر ويختفي في لحظة (وميض مزعج). القاعدة: استجابة تحت 0.1s تبدو فورية، وتحت 1s تحافظ على تدفق المستخدم."},
            {"term": "CLS (Cumulative Layout Shift)", "def": "مقياس «العناصر بتتحرك فجأة»: صورة/قائمة بتحمّل فتدفع المحتوى لأسفل. العلاج: **احجز المساحة** (`min-h-*` · `aspect-ratio` · skeleton بأبعاد ثابتة)."},
            {"term": "Stale-while-revalidate", "def": "اعرض البيانات المخزنة فورًا (قديمة) واجلب الأحدث في الخلفية وحدّث. تجربة سلسة جدًا — بس محتاج مؤشر «جارٍ التحديث» لو البيانات حساسة (رصيد/مخزون)."},
            {"term": "Optimistic UI", "def": "طبّق التغيير في الواجهة قبل تأكيد الخادم، مع **خطة تراجع** لو فشل. يناسب العمليات منخفضة الخطورة القابلة للانعكاس (نقل عنصر · إعجاب) ولا يناسب المالية (5.1.3)."},
            {"term": "Rollback", "def": "إرجاع الحالة لما كانت عليه عند فشل عملية متفائلة + رسالة توضح السبب. من غيره، المستخدم بيفتكر إن التغيير اتنفذ."},
            {"term": "Error boundary", "def": "مكوّن بيمسك أخطاء العرض في جزء من الشجرة ويعرض واجهة بديلة بدل الشاشة البيضاء. **مدمج في Blazor** (`<ErrorBoundary>`) · في React محتاج مكتبة (`react-error-boundary`) أو class component."},
            {"term": "`aria-live`", "def": "منطقة بتعلن تغييراتها لقارئ الشاشة: `polite` (بعد ما يخلص الكلام الحالي — للحالة «تم الحفظ») · `assertive` (فورًا — للأخطاء). و`role=\"status\"` = polite · `role=\"alert\"` = assertive."},
            {"term": "إدارة التركيز (focus management)", "def": "نقل التركيز لمكان منطقي عند: فتح modal (لأول عنصر قابل للتركيز + حبس التركيز) · إغلاقه (رجوع للعنصر اللي فتحه) · تغيير الصفحة/التبويب · ظهور خطأ (لأول حقل غلط)."},
            {"term": "Debounce مقابل Throttle", "def": "**Debounce**: نفّذ بعد ما يتوقف المستخدم عن الكتابة بـX ms (بحث). **Throttle**: نفّذ كل X ms مهما حدث (scroll/resize). الاتنين بيقللوا الطلبات — ومعاهم إلغاء للطلب السابق (8.1.2)."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① الحالات الست — وما تعرضه في كل واحدة"},
        {"type": "table", "caption": "الجدول ده هو 80% من جودة الواجهة",
         "head": ["الحالة", "ما تعرضه", "الخطأ الشائع", "إزاي تختبرها"],
         "rows": [
             ["**idle**", "لا شيء أو دعوة للبدء (زر «تحميل الطلبات» لو الجلب يدوي/مكلف)", "تنفيذ الجلب تلقائيًا لصفحات ما تتفتحش أصلًا", "افتح الصفحة بدون توجيه (route) لجلب"],
             ["**loading (أول مرة)**", "skeleton بنفس شكل المحتوى (3–6 صفوف) + تأخير 200ms قبل ظهوره + `aria-busy=\"true\"`", "spinner في نص صفحة فاضية · skeleton بأبعاد غلط → CLS", "خفّض السرعة في أدوات المطور (Slow 3G) والتقط صورة"],
             ["**loading (إعادة جلب)**", "**احتفظ بالمحتوى القديم** + مؤشر خفيف (شريط أعلى/شفافية 70%) + عطّل الأزرار", "مسح القائمة واستبدالها بـspinner (المستخدم بيضيع مكانه)", "اعمل pagination/ترشيح وراقب هل المحتوى بيختفي"],
             ["**empty**", "رسالة توضح **لماذا** فاضي + الخطوة التالية (CTA): «لا طلبات بعد — أنشئ أول طلب» أو «لا نتائج لـ«xyz» — امسح المرشحات»", "«لا توجد بيانات» بس (ميت) · أو الخلط بينها وبين الخطأ", "ابحث عن قيمة مستحيلة · امسح كل البيانات في بيئة اختبار"],
             ["**error**", "سبب بلغة المستخدم + إجراء (إعادة محاولة/تسجيل دخول/اتصال بالدعم) + `correlationId` + **احتفاظ بالمدخلات**", "«حدث خطأ» بس · أو عرض stack trace (7.2.3) · أو إخفاء الفشل كحالة فراغ", "افصل الشبكة · أرجع 500 من mock · أرجع 401"],
             ["**success**", "المحتوى + وقت آخر تحديث + إجراءات متاحة حسب الصلاحية", "بلا مؤشر تحديث (المستخدم ما يعرفش لو البيانات قديمة)", "قارن وقت التحديث مع الخادم"],
             ["**partial/stale**", "بيانات قديمة + «جارٍ التحديث…» + منع إجراءات حساسة لو الفرق مهم", "عرض بيانات قديمة كأنها حالية (خطر في الرصيد/المخزون)", "افتح تبويب تاني وارجع بعد 10 دقائق"],
         ]},
        {"type": "callout", "kind": "goal", "title": "القاعدة الحاكمة",
         "md": "**كل مكوّن بيعرض بيانات بعيدة لازم يكون فيه `switch` على الحالات الست — والحالات دي جزء من تعريف «المكوّن خلص»، مش تحسين لاحق.**\n\nاختبار سريع لأي شاشة: اقطع النت → إيه اللي ظهر؟ · ارجع 500 من الخادم → إيه اللي ظهر؟ · أرجع قائمة فاضية → إيه اللي ظهر؟ · حمّل ببطء (Slow 3G) → فيه CLS؟ لو أي إجابة «مش عارف»، الشاشة لسه ما خلصتش."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② آلة الحالات — مرة واحدة، وتشتغل في أي إطار"},
        {"type": "code", "lang": "javascript", "title": "src/ui/remote.ts — نوع الحالات + التحولات (بلا اعتماد على إطار)", "filename": "src/ui/remote.ts", "code": r'''import type { ApiError } from "../api/types";

/**
 * الحالات الست لبيانات بعيدة — discriminated union (8.1.1).
 * الفائدة: المترجم بيجبرك تتعامل مع كل حالة في switch (بلا default صامت).
 */
export type Remote<T> =
  | { readonly kind: "idle" }
  | { readonly kind: "loading" }                                   // أول جلب
  | { readonly kind: "refreshing"; readonly data: T }              // إعادة جلب (بيانات قديمة معروضة)
  | { readonly kind: "success"; readonly data: T; readonly at: number }
  | { readonly kind: "empty" }
  | { readonly kind: "error"; readonly error: ApiError; readonly stale?: T };

export const idle = <T>(): Remote<T> => ({ kind: "idle" });
export const loading = <T>(): Remote<T> => ({ kind: "loading" });

export function success<T>(data: T, isEmpty: (value: T) => boolean): Remote<T> {
  // حالة فارغة = نجاح بلا عناصر (لا تخلطها بالخطأ)
  return isEmpty(data) ? { kind: "empty" } : { kind: "success", data, at: Date.now() };
}

export function failure<T>(error: ApiError, previous?: T): Remote<T> {
  return { kind: "error", error, stale: previous };
}

/** بيانات قديمة معروفة + جلب جارٍ → refreshing (stale-while-revalidate). */
export function refreshing<T>(data: T): Remote<T> {
  return { kind: "refreshing", data };
}

/** هل المحتوى القديم يظهر أثناء الجلب؟ */
export const hasVisibleData = <T>(state: Remote<T>): boolean =>
  state.kind === "success" || state.kind === "refreshing" ||
  (state.kind === "error" && state.stale !== undefined);

/** هل الإجراءات (حذف/تعديل) مسموحة الآن؟ */
export const canMutate = <T>(state: Remote<T>): boolean =>
  state.kind === "success" || state.kind === "refreshing";

/** نص حالة للقارئ الشاشة (aria-live) — لا يعتمد على اللون أو الأيقونة فقط. */
export function statusText<T>(state: Remote<T>, labels: {
  loading: string; empty: string; error: (e: ApiError) => string; count: (n: number) => string;
}): string {
  switch (state.kind) {
    case "idle":       return "";
    case "loading":    return labels.loading;
    case "refreshing": return labels.loading;
    case "empty":      return labels.empty;
    case "error":      return labels.error(state.error);
    case "success": {
      const n = Array.isArray(state.data) ? state.data.length : 1;
      return labels.count(n);
    }
  }
}
'''},
        {"type": "code", "lang": "javascript", "title": "OrdersList.tsx — نفس الحالات في React (مع إلغاء وdebounce للبحث)", "filename": "src/features/orders/OrdersList.tsx", "code": r'''import { useCallback, useEffect, useRef, useState } from "react";
import { listOrders } from "../../api/orders";
import type { Order } from "../../api/types";
import {
  failure, hasVisibleData, idle, loading, refreshing, statusText, success,
  type Remote,
} from "../../ui/remote";

const LABELS = {
  loading: "جارٍ تحميل الطلبات",
  empty: "لا توجد طلبات مطابقة",
  error: (e: { title: string }) => e.title,
  count: (n: number) => `${n} طلبًا معروضًا`,
};

/** تأخير ظهور الـskeleton: يمنع الوميض عند الرد السريع. */
function useDelayedFlag(active: boolean, delayMs = 200): boolean {
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (!active) { setShow(false); return; }
    const id = setTimeout(() => setShow(true), delayMs);
    return () => clearTimeout(id);
  }, [active, delayMs]);
  return show;
}

/** debounce للبحث + إلغاء الطلب السابق (8.1.2). */
function useDebounced<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}

export function OrdersList() {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [state, setState] = useState<Remote<readonly Order[]>>(() => idle());
  const debouncedQuery = useDebounced(query);
  const isRefreshing = hasVisibleData(state);
  const showSkeleton = useDelayedFlag(state.kind === "loading");
  const controllerRef = useRef<AbortController | null>(null);

  const load = useCallback(async (nextCursor: string | null, keepPrevious: boolean) => {
    // إلغاء الطلب السابق: يمنع وصول استجابة قديمة بعد جديدة
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setState((prev) => (keepPrevious && prev.kind === "success"
      ? refreshing(prev.data)
      : loading()));

    try {
      // في مشروعك: مدّد خيارات listOrders (8.1.1) بحقل query ومرّر debouncedQuery
      const page = await listOrders(nextCursor, { signal: controller.signal });
      setState(success(page.items, (items) => items.length === 0));
      setCursor(page.nextCursor ?? null);
    } catch (err) {
      if (controller.signal.aborted) return;          // إلغاء مقصود: لا حالة خطأ
      // setState بدالة: نتجنب stale closure على `state`
      setState((prev) => failure(toApiErrorLike(err), previousData(prev)));
    }
  }, [state]);

  useEffect(() => {
    void load(null, isRefreshing);
    return () => controllerRef.current?.abort();       // فك الارتباط = إلغاء
  }, [debouncedQuery]);                                // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="grid gap-4" aria-busy={state.kind === "loading" || state.kind === "refreshing"}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <label className="grid gap-1">
          <span className="text-sm font-medium">بحث</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="رقم الطلب أو اسم العميل"
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <button
          type="button"
          onClick={() => void load(cursor, true)}
          disabled={!cursor}
          className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
        >
          تحميل المزيد
        </button>
      </div>

      {/* إعلان الحالة لقارئ الشاشة (polite: لا يقاطع) */}
      <p className="sr-only" role="status" aria-live="polite">
        {statusText(state, LABELS)}
      </p>

      {showSkeleton && !hasVisibleData(state) ? <OrdersSkeleton rows={5} /> : null}

      {hasVisibleData(state) ? (
        <ul className={"grid gap-2 " + (state.kind === "refreshing" ? "opacity-70" : "")}>
          {(state.kind === "success" || state.kind === "refreshing"
            ? state.data
            : (state as { stale?: readonly Order[] }).stale ?? []
          ).map((order) => (
            <li key={order.id} className="card flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate font-medium" dir="ltr">{order.id}</p>
                <p className="text-sm text-ink-muted">{order.status}</p>
              </div>
              <p className="tabular-nums text-sm" dir="ltr">{order.total} {order.currency}</p>
            </li>
          ))}
        </ul>
      ) : null}

      {state.kind === "empty" ? (
        <EmptyState
          title={query ? "لا نتائج مطابقة" : "لا طلبات بعد"}
          hint={query ? `لم نجد شيئًا لـ«${query}» — جرّب مسح البحث أو المرشحات.`
                      : "أول ما يصل طلب جديد هيظهر هنا."}
          action={query ? { label: "مسح البحث", onClick: () => setQuery("") } : undefined}
        />
      ) : null}

      {state.kind === "error" ? <ErrorPanel error={state.error} onRetry={() => void load(null, false)} /> : null}
    </section>
  );
}

function OrdersSkeleton({ rows }: { rows: number }) {
  return (
    <ul className="grid gap-2" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => (
        // أبعاد ثابتة = حجز مساحة = بلا CLS
        <li key={i} className="card flex animate-pulse items-center justify-between gap-3">
          <div className="grid gap-2">
            <div className="h-4 w-40 rounded bg-gray-200" />
            <div className="h-3 w-24 rounded bg-gray-200" />
          </div>
          <div className="h-4 w-20 rounded bg-gray-200" />
        </li>
      ))}
    </ul>
  );
}

function EmptyState({ title, hint, action }: {
  title: string; hint: string; action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="card grid justify-items-center gap-2 py-10 text-center">
      <p className="font-medium">{title}</p>
      <p className="max-w-prose text-sm text-ink-muted">{hint}</p>
      {action ? (
        <button type="button" onClick={action} className="btn-primary mt-2">{action.label}</button>
      ) : null}
    </div>
  );
}

function ErrorPanel({ error, onRetry }: {
  error: { status: number; title: string; detail?: string; correlationId?: string };
  onRetry: () => void;
}) {
  return (
    <div className="card grid gap-2 border-danger/30 bg-danger/5 py-6 text-center" role="alert">
      <p className="font-medium text-danger">{error.title}</p>
      {error.detail ? <p className="text-sm text-ink-muted">{error.detail}</p> : null}
      <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
        <button type="button" onClick={onRetry} className="btn-primary">إعادة المحاولة</button>
        {error.status === 401 ? (
          <a href="/bff/login" className="rounded-md border px-3 py-2 text-sm">تسجيل الدخول</a>
        ) : null}
      </div>
      {error.correlationId ? (
        <p className="mt-2 text-xs text-ink-muted">
          مرجع للمتابعة: <code dir="ltr">{error.correlationId}</code>
        </p>
      ) : null}
    </div>
  );
}

// مساعدات صغيرة (التحويل موجود في 8.1.2 — هنا للإحالة فقط)
function toApiErrorLike(err: unknown) {
  return (err ?? { status: 0, title: "تعذر الوصول إلى الخادم" }) as
    { status: number; title: string; detail?: string; correlationId?: string };
}
function previousData<T>(state: Remote<T>): T | undefined {
  return state.kind === "success" || state.kind === "refreshing" ? state.data : undefined;
}
'''},
        {"type": "code", "lang": "text", "title": "OrdersList.razor — نفس الحالات الست في Blazor (مقارنة مباشرة)", "filename": "src/Shop.Admin/Features/Orders/OrdersList.razor", "code": r'''@*
  نفس آلة الحالات في Blazor — لاحظ الفروق الجوهرية عن React:
    • StateHasChanged() بدل setState
    • <ErrorBoundary> مدمج (في React محتاج مكتبة)
    • CancellationTokenSource للإلغاء (زي الـBackend بالظبط)
    • RenderMode: Server = حالة على الخادم · WebAssembly = حالة في المتصفح (8.2.1)
*@
@page "/orders"
@implements IDisposable
@using Shop.Api.Client
@inject OrdersApiClient Api

<ErrorBoundary @ref="_boundary">
  <ChildContent>
    <section class="grid gap-4" aria-busy="@(_state.Kind is StateKind.Loading or StateKind.Refreshing)">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <label class="grid gap-1">
          <span class="text-sm font-medium">بحث</span>
          @* @oninput مع debounce يدوي (Blazor ما فيهوش hook جاهز) *@
          <input type="search" value="@_query" @oninput="OnQueryChanged"
                 placeholder="رقم الطلب أو اسم العميل"
                 class="rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </label>
        <button type="button" class="rounded-md border px-3 py-1.5 text-sm"
                disabled="@(_cursor is null)" @onclick="LoadMore">تحميل المزيد</button>
      </div>

      <p class="sr-only" role="status" aria-live="polite">@StatusText</p>

      @switch (_state.Kind)
      {
        case StateKind.Idle:
          break;

        case StateKind.Loading when !_showSkeleton:
          break;                     @* تأخير 200ms: لا وميض *@

        case StateKind.Loading:
          <OrdersSkeleton Rows="5" />
          break;

        case StateKind.Empty:
          <div class="card grid justify-items-center gap-2 py-10 text-center">
            <p class="font-medium">@(_query.Length > 0 ? "لا نتائج مطابقة" : "لا طلبات بعد")</p>
            <p class="max-w-prose text-sm text-ink-muted">
              @(_query.Length > 0 ? $"لم نجد شيئًا لـ«{_query}» — جرّب مسح البحث."
                                  : "أول ما يصل طلب جديد هيظهر هنا.")
            </p>
            @if (_query.Length > 0)
            {
              <button type="button" class="btn-primary mt-2" @onclick="() => ClearQuery()">مسح البحث</button>
            }
          </div>
          break;

        case StateKind.Error:
          <div class="card grid gap-2 border-danger/30 bg-danger/5 py-6 text-center" role="alert">
            <p class="font-medium text-danger">@_state.Error!.Title</p>
            @if (!string.IsNullOrEmpty(_state.Error.Detail))
            {
              <p class="text-sm text-ink-muted">@_state.Error.Detail</p>
            }
            <div class="mt-2 flex flex-wrap items-center justify-center gap-2">
              <button type="button" class="btn-primary" @onclick="Reload">إعادة المحاولة</button>
              @if (_state.Error.Status == 401)
              {
                <a href="/bff/login" class="rounded-md border px-3 py-2 text-sm">تسجيل الدخول</a>
              }
            </div>
            @if (!string.IsNullOrEmpty(_state.Error.CorrelationId))
            {
              <p class="mt-2 text-xs text-ink-muted">
                مرجع للمتابعة: <code dir="ltr">@_state.Error.CorrelationId</code>
              </p>
            }
          </div>
          break;

        case StateKind.Success:
        case StateKind.Refreshing:
          <ul class="grid gap-2 @(_state.Kind == StateKind.Refreshing ? "opacity-70" : "")">
            @foreach (var order in _state.Items)
            {
              <li class="card flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate font-medium" dir="ltr">@order.Id</p>
                  <p class="text-sm text-ink-muted">@order.Status</p>
                </div>
                <p class="tabular-nums text-sm" dir="ltr">@order.Total @order.Currency</p>
              </li>
            }
          </ul>
          break;
      }
    </section>
  </ChildContent>
  <ErrorContent Context="ex">
    @* بديل الشاشة البيضاء: خطأ عرض غير متوقع *@
    <div class="card grid gap-2 py-6 text-center" role="alert">
      <p class="font-medium text-danger">تعذر عرض هذا القسم</p>
      <p class="text-sm text-ink-muted">أعد تحميل الصفحة، ولو تكررت المشكلة بلّغ الدعم بالمرجع.</p>
      <button type="button" class="btn-primary mx-auto" @onclick="Reset">إعادة ضبط القسم</button>
    </div>
  </ErrorContent>
</ErrorBoundary>

@code {
    // Api محقون بـ@inject أعلاه. الأنواع: OrderDto/ApiError/ApiException من مشروع العميل.
    private CancellationTokenSource? _cts;
    private System.Timers.Timer? _debounce;
    private System.Timers.Timer? _skeletonDelay;

    private string _query = "";
    private string? _cursor;
    private RemoteState _state = RemoteState.Idle();
    private bool _showSkeleton;
    private ErrorBoundary? _boundary;

    private string StatusText => _state.Kind switch
    {
        StateKind.Loading or StateKind.Refreshing => "جارٍ تحميل الطلبات",
        StateKind.Empty => "لا توجد طلبات مطابقة",
        StateKind.Error => _state.Error?.Title ?? "خطأ",
        StateKind.Success => $"{_state.Items.Count} طلبًا معروضًا",
        _ => "",
    };

    protected override async Task OnInitializedAsync() => await LoadAsync(keepPrevious: false);

    private void OnQueryChanged(ChangeEventArgs e)
    {
        _query = e.Value?.ToString() ?? "";
        // debounce 300ms: نلغي المؤقت السابق ونبدأ جديدًا
        _debounce?.Stop();
        _debounce = new System.Timers.Timer(300) { AutoReset = false };
        _debounce.Elapsed += async (_, _) => await InvokeAsync(async () => await LoadAsync(keepPrevious: true));
        _debounce.Start();
    }

    private async Task LoadAsync(bool keepPrevious)
    {
        _cts?.Cancel();
        _cts = new CancellationTokenSource();
        var token = _cts.Token;

        // تأخير الـskeleton 200ms
        if (!keepPrevious)
        {
            _state = RemoteState.Loading();
            _showSkeleton = false;
            _skeletonDelay = new System.Timers.Timer(200) { AutoReset = false };
            _skeletonDelay.Elapsed += async (_, _) =>
                await InvokeAsync(() => { _showSkeleton = true; StateHasChanged(); });
            _skeletonDelay.Start();
        }
        else
        {
            _state = RemoteState.Refreshing(_state.Items);
        }
        StateHasChanged();

        try
        {
            var page = await Api.ListOrdersAsync(_cursor, _query, token);
            _cursor = page.NextCursor;
            _state = page.Items.Count == 0 && !keepPrevious
                ? RemoteState.Empty()
                : RemoteState.Success(page.Items);
        }
        catch (OperationCanceledException) when (token.IsCancellationRequested)
        {
            return;                     // إلغاء مقصود — لا حالة خطأ
        }
        catch (ApiException ex)
        {
            _state = RemoteState.Error(ex.ToApiError());
        }
        catch (HttpRequestException)
        {
            _state = RemoteState.Error(new ApiError(0, "تعذر الوصول إلى الخادم"));
        }
        finally
        {
            StateHasChanged();
        }
    }

    private Task Reload() => LoadAsync(keepPrevious: false);
    private Task LoadMore() => LoadAsync(keepPrevious: true);
    private void ClearQuery() { _query = ""; _ = LoadAsync(keepPrevious: true); }
    private void Reset() { _boundary?.Recover(); _ = LoadAsync(keepPrevious: false); }

    public void Dispose()
    {
        _cts?.Cancel();
        _cts?.Dispose();
        _debounce?.Dispose();
        _skeletonDelay?.Dispose();
    }
}

@* آلة الحالات في Blazor (نفس الشكل المنطقي لـRemote<T> في TS) *@
public enum StateKind { Idle, Loading, Refreshing, Success, Empty, Error }

public sealed record RemoteState
{
    public StateKind Kind { get; init; } = StateKind.Idle;
    public IReadOnlyList<OrderDto> Items { get; init; } = [];
    public ApiError? Error { get; init; }

    public static RemoteState Idle() => new();
    public static RemoteState Loading() => new() { Kind = StateKind.Loading };
    public static RemoteState Refreshing(IReadOnlyList<OrderDto> items) =>
        new() { Kind = StateKind.Refreshing, Items = items };
    public static RemoteState Success(IReadOnlyList<OrderDto> items) =>
        new() { Kind = StateKind.Success, Items = items };
    public static RemoteState Empty() => new() { Kind = StateKind.Empty };
    public static RemoteState Error(ApiError error) => new() { Kind = StateKind.Error, Error = error };
}
'''},
        {"type": "callout", "kind": "note", "title": "الفروق اللي تهمك بين React وBlazor في الحالات",
         "md": "• **إعادة الرسم**: React `setState` → إعادة رسم المكوّن · Blazor `StateHasChanged()` (ولو من thread تاني: `InvokeAsync(StateHasChanged)`).\n• **Error boundary**: Blazor مدمج (`<ErrorBoundary>` مع `Recover()`) · React محتاج `react-error-boundary` أو class component (الـhooks ما بتمسكش أخطاء العرض).\n• **الإلغاء**: `AbortController` في JS مقابل `CancellationTokenSource` في Blazor — **نفس المنطق** اللي تعرفه من الـBackend.\n• **الحالة فين؟**: Blazor Server الحالة على الخادم (فكل مستخدم له دائرة — انتبه للذاكرة) · WebAssembly في المتصفح (8.2.1).\n• **debounce**: React بـhook · Blazor بـ`System.Timers.Timer` أو مكتبة — ولو Blazor Server، الـdebounce بيقلل عدد مرات إعادة الرسم على الخادم كمان."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ التحميل: skeleton مقابل spinner — وبلا قفزات"},
        {"type": "table", "caption": "قواعد التحميل (كل قاعدة ليها سبب قابل للقياس)",
         "head": ["القاعدة", "التنفيذ", "السبب"],
         "rows": [
             ["أخّر المؤشر 200–300ms", "`useDelayedFlag(loading, 200)` · `Timer(200)` في Blazor", "الاستجابة السريعة مع spinner = وميض مزعج"],
             ["skeleton بأبعاد المحتوى المتوقع", "ارتفاع ثابت لكل صف · `aspect-ratio` للصور", "يمنع CLS (قفز المحتوى) — مقياس أداء حقيقي"],
             ["أعد الجلب بدون مسح المحتوى", "حالة `refreshing` + `opacity-70` + شريط تقدم أعلى", "المستخدم ما يفقدش مكانه ولا القراءة"],
             ["عطّل الأفعال أثناء الحفظ", "`disabled` + نص «جارٍ الحفظ…» + `aria-busy`", "يمنع إرسال مزدوج (ومع idempotency key طبقة تانية)"],
             ["لا skeleton لعمليات قصيرة", "spinner صغير على الزر نفسه", "skeleton يوحي بجلب بيانات، مش بحفظ"],
             ["احترم تقليل الحركة", "`prefers-reduced-motion` يوقف `animate-pulse`", "دوار الحركة/الصداع (a11y)"],
             ["صفحة طويلة: جلب تدريجي", "pagination/cursor (2.2.2) + «تحميل المزيد» أو infinite scroll مع حدود", "جلب 5,000 صف مرة واحدة يدمر الأداء والتجربة"],
             ["قياس", "Lighthouse: CLS وLCP · وسجل «زمن لأول محتوى مفيد»", "ما لا يُقاس ما يتحسّن"],
         ]},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ الحالة الفارغة: خمسة أنواع مختلفة"},
        {"type": "table", "caption": "نوع الفراغ × الرسالة × الإجراء (لا تكتب «لا توجد بيانات» لكل الحالات)",
         "head": ["النوع", "المثال", "الرسالة", "الإجراء (CTA)"],
         "rows": [
             ["**أول استخدام**", "مستخدم جديد فتح صفحة الطلبات", "«لا طلبات بعد — أول ما يوصل طلب هيظهر هنا»", "زر «إنشاء طلب» أو رابط لدليل البدء"],
             ["**بلا نتائج بحث**", "بحث عن `xyz-999`", "«لا نتائج لـ«xyz-999»»", "زر «مسح البحث» + اقتراحات (هل تقصد…)"],
             ["**بعد ترشيح**", "مرشح «ملغي» بلا عناصر", "«لا طلبات ملغية في هذه الفترة»", "زر «إزالة المرشحات» + عرض عدد العناصر المخفية"],
             ["**بعد حذف**", "حذفت آخر عنصر في القائمة", "«حُذف العنصر» + حالة فارغة", "تراجع (undo) لمدة 5–10 ثوانٍ — أفضل تجربة ممكنة"],
             ["**فراغ بسبب صلاحيات**", "مستخدم بلا صلاحية رؤية القسم", "«لا تملك صلاحية عرض هذه البيانات» (**لا** تعرض فراغًا مضللًا)", "طلب صلاحية / تواصل مع المدير"],
         ]},
        {"type": "callout", "kind": "warn", "title": "فخّ الفراغ المضلل",
         "md": "أخطر خطأ: **403 أو خطأ شبكة بيتعرض كحالة فارغة**. المستخدم بيفتكر إن مفيش بيانات، والحقيقة إن فيه بيانات هو ما يقدرش يشوفها (أو الخادم واقع). القاعدة: `empty` **فقط** لما الاستجابة 200 والمجموعة فاضية — وأي حاجة تانية حالة خطأ برسالتها الصحيحة. وده بيظهر في الاختبار: أرجع 403 وشوف هل ظهر «لا توجد بيانات» (غلط) ولا «ليست لديك صلاحية» (صح)."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ Optimistic UI — بحذر"},
        {"type": "code", "lang": "javascript", "title": "optimistic.ts — تحديث متفائل مع rollback (نمط TanStack Query)", "filename": "src/ui/optimistic.ts", "code": r'''import type { QueryClient } from "@tanstack/react-query";

/**
 * تحديث متفائل: نعرض النتيجة فورًا، ونحتفظ بنسخة للرجوع إليها.
 * الشروط الثلاثة لاستخدامه:
 *   1) العملية منخفضة الخطورة وقابلة للانعكاس (نقل/إخفاء/إعجاب) — لا مالية.
 *   2) الخادم بيتحقق فعلًا (التفاؤل UX مش تفويض — 7.2.3).
 *   3) فيه مؤشر «جارٍ الحفظ» ورسالة واضحة عند الفشل.
 */
export async function optimisticUpdate<TItem>(options: {
  queryClient: QueryClient;
  queryKey: readonly unknown[];
  itemId: string;
  patch: Partial<TItem>;
  mutate: () => Promise<void>;
  buildErrorMessage: (error: unknown) => string;
  onNotify: (message: string, kind: "error" | "info") => void;
}): Promise<void> {
  const { queryClient, queryKey, itemId, patch, mutate, buildErrorMessage, onNotify } = options;

  // 1) لقطة للرجوع إليها (قبل التغيير — قاعدة مألوفة من الاختبارات 1.2.4)
  const snapshot = queryClient.getQueryData(queryKey);

  // 2) طبّق التغيير محليًا
  queryClient.setQueryData(queryKey, (old: unknown) => patchList<TItem>(old, itemId, patch));
  onNotify("جارٍ الحفظ…", "info");

  try {
    await mutate();                     // النداء الفعلي للخادم
    onNotify("تم الحفظ", "info");
  } catch (error) {
    // 3) rollback + سبب واضح (لا تسيب الواجهة في حالة كذب)
    queryClient.setQueryData(queryKey, snapshot);
    onNotify(buildErrorMessage(error), "error");
    throw error;                        // دَع الطبقة الأعلى تعرف بالفشل
  } finally {
    // 4) إعادة جلب للتأكد من تطابق الحالة مع الخادم (قد تكون هناك آثار جانبية)
    await queryClient.invalidateQueries({ queryKey });
  }
}

function patchList<TItem>(list: unknown, itemId: string, patch: Partial<TItem>): unknown {
  if (!Array.isArray(list)) return list;
  return (list as TItem[]).map((item) =>
    typeof item === "object" && item !== null && (item as { id?: unknown }).id === itemId
      ? { ...item, ...patch }
      : item);
}

/**
 * تراجع (undo) بدل الحذف الفوري — نمط أفضل للحذف:
 *   احذف من الواجهة، انتظر 8 ثوانٍ، ولو المستخدم ما تراجعش نفّذ الحذف.
 *   الخادم ممكن يدعم هذا بحذف ناعم (soft delete) + مهمة تنظيف (7.2.5).
 */
export function scheduleDelete(options: {
  onUndoWindow: (cancel: () => void) => void;
  commit: () => Promise<void>;
  windowMs?: number;
}): void {
  const { onUndoWindow, commit, windowMs = 8_000 } = options;
  let cancelled = false;

  onUndoWindow(() => { cancelled = true; });
  setTimeout(() => {
    if (!cancelled) void commit();
  }, windowMs);
}
'''},
        {"type": "table", "caption": "متى تستخدم Optimistic UI ومتى ترفضه",
         "head": ["العملية", "متفائل؟", "السبب"],
         "rows": [
             ["إعجاب/حفظ في المفضلة", "**نعم**", "منخفضة الخطورة وقابلة للانعكاس فورًا"],
             ["نقل عنصر بين القوائم", "**نعم**", "قابلية انعكاس واضحة + فشل نادر"],
             ["تعديل حالة طلب (مدفوع → ملغي)", "لا", "لها آثار مالية/تشغيلية — استنى التأكيد"],
             ["إنشاء طلب/دفع", "**لا**", "عمليات مالية (5.1.3): التفاؤل هنا بيخلق التباسًا قانونيًا ومحاسبيًا"],
             ["حذف عنصر", "نعم **مع تراجع** (undo 8 ثوانٍ)", "أفضل تجربة + أمان (soft delete + مهمة تنظيف)"],
             ["رفع ملف كبير", "لا (شريط تقدم حقيقي)", "الفشل شائع والتقدم مهم"],
         ]},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ الوصولية في الحالات الديناميكية"},
        {"type": "table", "caption": "تسع قواعد وصولية للحالات (من غيرها الواجهة «بتشتغل» بس مش متاحة)",
         "head": ["#", "القاعدة", "التنفيذ"],
         "rows": [
             ["1", "أعلن الحالة الديناميكية", "منطقة `role=\"status\" aria-live=\"polite\"` لنص الحالة · `role=\"alert\"` للأخطاء (assertive)"],
             ["2", "علّم الحاوي بأنه مشغول", "`aria-busy=\"true\"` أثناء الجلب/الحفظ"],
             ["3", "أعلن خطأ الحقل بجانبه", "`aria-invalid=\"true\"` + `aria-describedby=\"err-email\"` ورسالة الخطأ بعنصر له ذلك الـid"],
             ["4", "أدر التركيز عند الخطأ", "نقل التركيز لأول حقل غلط (`field.focus()`) — مش مجرد تلوينه"],
             ["5", "modal: احبس التركيز", "نقل التركيز لأول عنصر + Tab محصور داخليًا + Esc للإغلاق + إرجاع التركيز للعنصر الفاتح"],
             ["6", "skeleton بلا معنى لقارئ الشاشة", "`aria-hidden=\"true\"` على الـskeleton + النص البديل في `role=\"status\"`"],
             ["7", "لا تعتمد على اللون وحده", "شارة الحالة فيها نص («مدفوع») مش نقطة خضراء فقط"],
             ["8", "احترم تقليل الحركة", "`prefers-reduced-motion` يوقف pulse/انتقالات (8.1.3)"],
             ["9", "الأزرار: عطّل أم أخفِ؟", "**عطّل** مع سبب (tooltip/نص) — الإخفاء بيخلي المستخدم ما يعرفش إن الفعل موجود"],
         ]},
        {"type": "callout", "kind": "tip", "title": "اختبار الوصولية في 5 دقائق",
         "md": "**① افصل الفأرة**: اتحرك بـTab من أول الصفحة — هل كل الوظائف متاحة والترتيب منطقي وحلقة التركيز واضحة؟\n**② شغّل قارئ شاشة** (NVDA على Windows · VoiceOver على macOS/iOS): هل الحالة والأخطاء بتُعلن؟\n**③ شغّل `axe-core`** (إضافة متصفح أو `@axe-core/cli`): صفر أخطاء حرجة.\n**④ كبّر لـ200%**: هل فيه overflow أفقي أو نص مقصوص؟\n**⑤ اختبر تباين النص** بأداة تباين (≥ 4.5:1 للنص العادي)."},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ اثنتا عشرة تفصيلة بتخلي المنتج يبدو احترافيًا"},
        {"type": "table", "caption": "تفاصيل صغيرة، أثر كبير",
         "head": ["#", "التفصيلة", "البديل السيئ"],
         "rows": [
             ["1", "«تم الحفظ» لمدة 3 ثوانٍ بعد كل حفظ", "بلا أي تأكيد (المستخدم يعيد الضغط)"],
             ["2", "زر بلون/نص متغير أثناء الحفظ («جارٍ الحفظ…» + تعطيل)", "زر فعال يسمح بإرسال مزدوج"],
             ["3", "تراجع (undo) بعد الحذف بدل نافذة تأكيد", "«هل أنت متأكد؟» لكل حاجة (المستخدم بيوافق تلقائيًا)"],
             ["4", "وقت آخر تحديث نسبي («منذ دقيقتين») + زر تحديث", "لا يعرف المستخدم إذا كانت البيانات حية"],
             ["5", "أخطاء مرتبطة بالحقل مع نص قابل للفهم", "رسالة عامة أعلى النموذج"],
             ["6", "احتفاظ بمدخلات النموذج بعد الفشل", "مسح النموذج عند الخطأ"],
             ["7", "تحميل المزيد بدل ترقيم في القوائم الطويلة", "ترقيم مع 63 صفحة بلا بحث"],
             ["8", "حالة offline واضحة + إعادة محاولة تلقائية عند العودة (`online` event)", "طلبات تفشل بصمت"],
             ["9", "لوحة مفاتيح: `/` للبحث · `Esc` للإغلاق · `Enter` للإرسال", "فأرة فقط"],
             ["10", "أرقام بـ`tabular-nums` و`dir=\"ltr\"` في صفحة عربية", "أرقام غير متحاذية ومقلوبة"],
             ["11", "رسالة 429 بعدّاد تنازلي («أعد المحاولة بعد 12 ثانية»)", "زر إعادة محاولة يضغطه المستخدم 20 مرة"],
             ["12", "سجل أخطاء الواجهة يُرسل للخادم (مع correlationId)", "أخطاء في console محدش بيشوفها"],
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أسمّي الحالات الست لبيانات بعيدة وأعرف إن `empty` مش `error`.",
            "أبني آلة حالات (discriminated union في TS / enum+record في C#) تفرض التعامل مع كل حالة.",
            "أستخدم skeleton بأبعاد ثابتة (بلا CLS) وتأخير 200ms قبل ظهوره، وأحتفظ بالمحتوى القديم عند إعادة الجلب.",
            "أكتب 5 حالات فراغ مختلفة برسائل وإجراءات مختلفة، وأتجنب «الفراغ المضلل» عند 403/خطأ شبكة.",
            "أعالج الأخطاء بـ: سبب بلغة المستخدم · إجراء · correlationId · احتفاظ بالمدخلات · error boundary (Blazor مدمج/React بمكتبة).",
            "أستخدم optimistic UI للعمليات منخفضة الخطورة مع snapshot + rollback + invalidate، وأرفضه للعمليات المالية، وأفضل undo للحذف.",
            "أطبّق 9 قواعد وصولية للحالات الديناميكية (aria-live · aria-busy · aria-describedby · إدارة التركيز · aria-hidden للـskeleton).",
            "أستخدم debounce للبحث مع إلغاء الطلب السابق (`AbortController`/`CancellationTokenSource`) ومعالجة `AbortError` كإلغاء لا خطأ.",
            "أعرف 12 تفصيلة تجربة استخدام وأقدر أطبق 6 منها في ساعة.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على حالات الواجهة.",
         "questions": [
             {"q": "الاستجابة رجعت 200 بمجموعة فاضية، وفي حالة تانية رجعت 403. ما الفرق في العرض؟",
              "options": ["الاتنان حالة فارغة «لا توجد بيانات»",
                          "200 الفاضية = حالة empty برسالة وسبب، و403 = حالة خطأ «ليست لديك صلاحية» — الخلط بينهما فراغ مضلل",
                          "الاتنان خطأ",
                          "403 = empty لأن المستخدم لا يرى شيئًا"],
              "answer": 1,
              "explain": "`empty` يعني «لا بيانات موجودة» — بينما 403 يعني «فيها بيانات لكنك لا تملك الوصول». الخلط بيخلي المستخدم (والدعم) يدور على مشكلة مش موجودة. نفس المنطق لخطأ الشبكة: لا تعرضه كفراغ."},
             {"q": "لماذا تؤخر ظهور الـspinner/skeleton 200–300ms؟",
              "options": ["لتوفير الطلبات",
                          "لتجنب وميض المؤشر عند الردود السريعة — الاستجابة تحت 0.1s تبدو فورية أصلًا",
                          "لتحسين SEO",
                          "لتقليل استهلاك CPU"],
              "answer": 1,
              "explain": "لو الطلب بيخلص في 80ms، الـspinner هيظهر ويختفي فورًا (وميض مزعج). التأخير بيخلي الاستجابات السريعة تبدو فورية، والبطيئة بتظهر مؤشر بعد لحظة قصيرة. نفس الفكرة للتأخير بين `loading` و`refreshing`."},
             {"q": "سبب CLS (قفز المحتوى) الأشهر في القوائم، وعلاجه؟",
              "options": ["سرعة الشبكة — علاجها CDN",
                          "skeleton أو صور بأبعاد مختلفة عن المحتوى الفعلي — العلاج حجز المساحة (أبعاد ثابتة/aspect-ratio/min-h)",
                          "كثرة الطلبات — علاجها الكاش",
                          "الخطوط — علاجها font-display"],
              "answer": 1,
              "explain": "لما المحتوى الحقيقي يحل محل placeholder بأبعاد مختلفة، كل اللي تحت بيتحرك. احجز المساحة بأبعاد قريبة من الواقع (ارتفاع صف ثابت · `aspect-video` للصور) وقِس بـLighthouse."},
             {"q": "أي عملية يناسبها Optimistic UI؟",
              "options": ["إنشاء دفع مالي",
                          "إعجاب/نقل عنصر بين القوائم (منخفضة الخطورة وقابلة للانعكاس) مع snapshot وrollback",
                          "حذف بيانات شخصية نهائيًا",
                          "تحويل رصيد"],
              "answer": 1,
              "explain": "الشروط: قابلة للانعكاس + الخادم بيتحقق فعلًا + فيه مؤشر حفظ ورسالة فشل واضحة. العمليات المالية والقانونية لازم تستنى التأكيد (5.1.3)، والحذف الأفضل فيه نمط undo مع soft delete."},
             {"q": "أفضل طريقة لإعلان «جارٍ التحميل» و«حدث خطأ» لقارئ الشاشة؟",
              "options": ["تغيير لون العنوان",
                          "`role=\"status\"` (aria-live polite) للحالة، و`role=\"alert\"` (assertive) للخطأ، مع `aria-busy` على الحاوي",
                          "`title` attribute",
                          "لا شيء — قارئ الشاشة يرى المحتوى تلقائيًا"],
              "answer": 1,
              "explain": "التغييرات الديناميكية ما بتُعلنش تلقائيًا. `polite` بينتظر نهاية الكلام الحالي (مناسب للحالة)، و`assertive` بيقاطع (مناسب للأخطاء). و`aria-hidden=\"true\"` على الـskeleton لأنه بلا معنى."},
             {"q": "البحث الفوري (search-as-you-type) بيعمل 15 طلبًا في الثانية وأحيانًا بيظهر نتائج قديمة فوق الجديدة. الحل؟",
              "options": ["زيادة حجم الصفحة",
                          "debounce (250–300ms) + إلغاء الطلب السابق بـAbortController + تجاهل AbortError",
                          "تقليل عدد النتائج",
                          "استخدام POST بدل GET"],
              "answer": 1,
              "explain": "الـdebounce بيقلل الطلبات، والإلغاء بيمنع السباق (استجابة قديمة توصل بعد جديدة). و`AbortError` إلغاء مقصود فلا تعرضه كخطأ (8.1.2). ومفتاح الكاش لازم يشمل نص البحث."},
             {"q": "ErrorBoundary في Blazor مقابل React؟",
              "options": ["الاثنان مدمجان",
                          "Blazor فيه `<ErrorBoundary>` مدمج مع `Recover()` · React محتاج مكتبة (react-error-boundary) أو class component لأن الـhooks لا تمسك أخطاء العرض",
                          "React مدمج وBlazor لا",
                          "لا يوجد مفهوم كهذا"],
              "answer": 1,
              "explain": "من غير error boundary، خطأ في عرض مكوّن بيحول الشاشة كلها لبيضاء. في Blazor لفّ القسم بـ`<ErrorBoundary>` مع `ErrorContent` واستخدم `Recover()` لإعادة المحاولة. في React استخدم `react-error-boundary` (أو class component مع `componentDidCatch`)."},
             {"q": "زر «حذف» لطلب — ما الأفضل تجربةً وأمانًا؟",
              "options": ["نافذة تأكيد «هل أنت متأكد؟»",
                          "حذف فوري مع شريط تراجع (undo) لـ8 ثوانٍ + soft delete في الخادم ومهمة تنظيف",
                          "حذف فوري بلا تراجع",
                          "نقله لصفحة أخرى أولًا"],
              "answer": 1,
              "explain": "نافذة التأكيد بتتوافق عليها تلقائيًا (habituation) وما بتمنعش الأخطاء. الـundo بيدي أمانًا فعليًا مع تجربة أسرع — ويتنفذ بـsoft delete + مهمة تنظيف (زي RetentionWorker في 7.2.5). ووثّق في سجل التدقيق من حذف ومتى (7.2.3)."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "مكوّن بالحالات الست + تدقيق تجربة/وصولية.",
         "items": [
            {"id": "s8-m1-l4-t1",
             "title": "مهمة 1: مكوّن قائمة بالحالات الست (في إطارك المختار)",
             "md": "ابنِ مكوّن «قائمة الطلبات» بالحالات الست كلها، مع بحث (debounce + إلغاء) · skeleton بتأخير 200ms وأبعاد ثابتة · 3 حالات فراغ مختلفة · لوحة خطأ بـcorrelationId وإعادة محاولة · refreshing بلا مسح المحتوى. نفّذه في **React أو Blazor** (اللي هتكمل بيه في 8.2) — واستخدم `Remote<T>` من الدرس (أو `RemoteState` في Blazor).",
             "criteria": [
                 "نوع/سجل حالات بست حالات (`idle/loading/refreshing/success/empty/error`) و`switch` **بلا default صامت** (المترجم يجبرك تغطيها).",
                 "skeleton: تأخير 200ms · ≥ 4 صفوف · **أبعاد ثابتة** · `aria-hidden=\"true\"` · بلا `animate-pulse` عند `prefers-reduced-motion`.",
                 "بحث: debounce 250–300ms · إلغاء الطلب السابق · `AbortError`/`OperationCanceledException` لا يُعرض كخطأ · مفتاح الكاش يشمل نص البحث.",
                 "**3 حالات فراغ مختلفة** (أول استخدام · بلا نتائج بحث · بعد ترشيح) برسالة وإجراء لكل واحدة.",
                 "لوحة خطأ: عنوان بلغة المستخدم · إجراء (إعادة محاولة / تسجيل دخول عند 401) · `correlationId` ظاهر · **احتفاظ بمدخلات البحث**.",
                 "`refreshing`: المحتوى القديم ظاهر بشفافية + `aria-busy` + بلا قفزات.",
                 "وصولية: `role=\"status\"` للحالة · `role=\"alert\"` للخطأ · `aria-busy` · حلقة تركيز واضحة · أهداف لمس ≥ 44px.",
                 "**5 لقطات** (loading/empty/error/success/refreshing) + لقطة على 320px واتجاه RTL.",
                 "اختباران: واحد يثبت إن 403 يعرض خطأ صلاحية (مش فراغ) · وواحد يثبت إن الاستجابة القديمة المُلغاة ما تكتبش فوق الجديدة.",
             ],
             "hint": "للاختبارات: في React استخدم Testing Library مع mock لـ`listOrders` (يرفض بـ`ApiError{status:403}` مرة، ويرجع `[]` مرة) واثبت النص الظاهر. في Blazor استخدم `bunit` (`TestContext` + `RenderComponent<OrdersList>()` + mock للـAPI). ولإثبات إلغاء السباق: ارجع استجابة بطيئة للأول ثم سريعة للثاني واثبت إن المعروض من الثانية. ولو skeleton بيسبب CLS: قِس بـLighthouse قبل/بعد إضافة الأبعاد الثابتة.",
             "solution": "الأخطاء النموذجية: (1) `switch` بـ`default` صامت بيخفي حالة — استخدم exhaustive check (`const _exhaustive: never = state` في TS أو حذف default في Blazor). (2) الناس بتعرض `empty` عند 403 — وده بالظبط اللي الاختبار الأول بيكشفه. (3) الإلغاء بيتنسى عند فك الارتباط (unmount/Dispose) فبيظهر تحذير «تحديث حالة على مكوّن مفكوك». (4) skeleton بأبعاد غلط بيسبب CLS أسوأ من عدم وجوده — قِس. (5) الـdebounce في Blazor Server بيقلل إعادة الرسم على الخادم كمان — فائدته مضاعفة. النتيجة المتوقعة: مكوّن ~250 سطرًا (React) أو ~200 سطر razor + ~120 سطر كود، و5 لقطات متسقة، واختباران يعديان.",
             "resources": [
                 "https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates",
                 "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/handle-errors",
                 "https://testing-library.com/docs/react-testing-library/intro/",
                 "https://bunit.dev/",
                 "https://web.dev/learn/accessibility/",
             ]},
            {"id": "s8-m1-l4-t2",
             "title": "مهمة 2: تدقيق تجربة ووصولية لصفحة قائمة (12 بندًا)",
             "md": "خد أي صفحة قائمة عندك (أو صفحة 8.1.3) ونفّذ عليها تدقيقًا من 12 بندًا: قطع النت · 500 · 401 · 403 · قائمة فاضية · بحث بلا نتائج · Slow 3G · تكبير 200% · عرض 320px · RTL/LTR · Tab بلا فأرة · axe-core. لكل بند: ما المتوقع · ما حدث فعلًا · الإصلاح · هل اتعمل.",
             "criteria": [
                 "جدول تدقيق 12 صفًا بالأعمدة: السيناريو · المتوقع · الفعلي · الإصلاح · الحالة (تم/مؤجل بمالك وتاريخ).",
                 "**≥ 8 إصلاحات منفذة فعليًا** (مش مقترحة) مع diff/commit لكل واحدة.",
                 "قياس قبل/بعد: CLS وLCP من Lighthouse + حجم CSS/JS + عدد الطلبات للبحث (قبل/بعد debounce).",
                 "نتيجة `axe-core` (أو Lighthouse accessibility): صفر أخطاء حرجة + قائمة بالتحذيرات وقرار لكل واحدة.",
                 "اختبار بلوحة المفاتيح فقط: مسار كامل (بحث → نتيجة → تفاصيل → رجوع) مع ملاحظة على أي نقطة فقدت التركيز أو كان الترتيب غير منطقي.",
                 "اختبار RTL/LTR: لقطة لكل اتجاه مع صفر خصائص مادية (من 8.1.3) وملاحظة على الأرقام/الأكواد.",
                 "سيناريو offline: ما الذي يظهر عند قطع النت، وهل فيه إعادة محاولة عند العودة (حدث `online`)، وهل المدخلات محفوظة.",
                 "خلاصة نصف صفحة: أعلى 3 مشاكل أثّرت على التجربة وإصلاحها، وبند واحد قررّت تأجيله وسببه.",
             ],
             "hint": "أسرع طريقة للسيناريوهات: أدوات المطور → Network → Offline/Slow 3G، و→ Devices → 320px، و→ Rendering → force `prefers-reduced-motion` و`prefers-color-scheme: dark`. ولـ500/403 بدون تعديل الخادم: استخدم إضافة متصفح لتعديل الاستجابات (Requestly/ModHeader) أو mock في بيئة تطوير. ولو `axe-core` مش متاح: Lighthouse فيه نفس القواعد تقريبًا.",
             "solution": "النتائج النموذجية لأول تدقيق: 12–20 مشكلة، وأشهر 5: (1) 403 بيتعرض كفراغ، (2) CLS من skeleton/صور بلا أبعاد، (3) رسائل خطأ عامة بلا إجراء ولا correlationId، (4) أزرار بلا اسم متاح (أيقونات فقط) — بيصلحها `aria-label`، (5) تباين النص الرمادي الفاتح أقل من 4.5:1. ومكسبان سهلان بأثر كبير: تأكيد «تم الحفظ» لمدة 3 ثوانٍ، وundo بدل نافذة تأكيد الحذف. وأهم ملاحظة: التدقيق ده بيكلف ساعة وبيحسّن المنتج أكتر من أي إعادة تصميم — وبيديك قائمة ملموسة تحكي عنها في المقابلة («عملت تدقيق تجربة/وصولية بـ12 سيناريو وأصلحت 8 مشاكل، وCLS نزل من 0.24 إلى 0.02»).",
             "resources": [
                 "https://web.dev/learn/accessibility/",
                 "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions",
                 "https://github.com/dequelabs/axe-core",
                 "https://developer.chrome.com/docs/lighthouse",
                 "https://www.w3.org/WAI/WCAG22/quickref/",
                 "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/handle-errors",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "MDN: ARIA Live Regions", "url": "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions"},
            {"label": "web.dev: تعلّم الوصولية", "url": "https://web.dev/learn/accessibility/"},
            {"label": "WCAG 2.2: مرجع سريع", "url": "https://www.w3.org/WAI/WCAG22/quickref/"},
            {"label": "TanStack Query: التحديثات المتفائلة", "url": "https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates"},
            {"label": "Blazor: معالجة الأخطاء وErrorBoundary", "url": "https://learn.microsoft.com/aspnet/core/blazor/fundamentals/handle-errors"},
            {"label": "web.dev: CLS", "url": "https://web.dev/articles/cls"},
            {"label": "Nielsen Norman: أزمنة الاستجابة", "url": "https://www.nngroup.com/articles/response-times-3-important-limits/"},
            {"label": "MDN: prefers-reduced-motion", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion"},
        ]},
    ],
}

LESSONS_S8_D = [_L4]
