# -*- coding: utf-8 -*-
"""Stage 8 module 2 (part G): s8-m2-l3 (React أساسي لمطور .NET)."""

TODAY = "2026-10-22"

_L3 = {
    "id": "s8-m2-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "React في 2026 لسه **أكبر سوق للتوظيف** في الواجهات — ولو إعلان الوظيفة بيقول «.NET + React» فده معناه إنك هتكتب الاتنين. الخبر الحلو إن React **بسيط فكريًا**: مكوّنات هي دوال، والحالة قيم، والواجهة = دالة في الحالة (`UI = f(state)`). الخبر الوحش إن الفروق الدقيقة (قواعد الـhooks · الـclosures القديمة · التبعيات · إعادة الرسم) بتوقّع مطوري الـBackend أسابيع.\n\nالدرس ده **مش كورس React كامل** — ده **الحد الأدنى الكافي لمطور .NET**: مكوّنات وprops وحالة · قواعد الـhooks · `useEffect` الصح والغلط · القوائم والمفاتيح · النماذج بـReact 19 (`useActionState`/`useOptimistic`) · السياق · تقسيم الحزم والـSuspense · وأخطاء النماذج الذهنية اللي بتتكرر مع كل مطور C#."},

        {"type": "terms", "title": "مصطلحات الدرس (بمقابلها في .NET)", "items": [
            {"term": "JSX/TSX", "def": "صياغة بتشبه HTML داخل TS — بتتحول لنداءات دوال. **مش قوالب** (مفيش syntax خاص زي Razor): كل شيء تعبير JS. `{expr}` = إدراج قيمة، والشرط بـ`&&` أو `?:`."},
            {"term": "Component", "def": "دالة بترجع JSX: `function OrderRow(props: Props) { … }`. مقابلها في Blazor: `.razor` — بس هنا مفيش ملف منفصل ولا `@code`؛ المنطق والـmarkup في نفس المكان (co-location)."},
            {"term": "Props", "def": "معاملات المكوّن (**للقراءة فقط** — زي `[Parameter]` في Blazor بس بلا تعديل داخلي). تغييرها من الأب = إعادة رسم الابن."},
            {"term": "State", "def": "قيم المكوّن اللي بتتغير: `const [x, setX] = useState(0)`. **الـsetter مش متزامن بالمعنى اللي تتوقعه** — React بيجمّع التحديثات (batching) وبيعيد الرسم بعدها."},
            {"term": "Rules of Hooks", "def": "الـhooks بتُنادى **بنفس الترتيب في كل رسمة**: ممنوع داخل شروط/حلقات/دوال متداخلة. React بيعتمد على الترتيب لربط الحالة بالمكوّن — مخالفتها = أخطاء غامضة أو انفجار."},
            {"term": "Re-render", "def": "إعادة تنفيذ دالة المكوّن لما تتغير الحالة/الـprops (أو الأب بيرسم). **مش إعادة تحميل الصفحة** — React بيقارن الناتج ويحدّث الـDOM بالفرق (reconciliation)."},
            {"term": "Key", "def": "هوية عنصر في قائمة: `<li key={order.id}>`. غلط (index أو مفقود) = أخطاء حالة وتركيز عند الحذف/الترتيب — نظير `@key` في Blazor (8.2.2)."},
            {"term": "Effect (useEffect)", "def": "مزامنة مع **نظام خارجي** (اشتراك · مؤقت · DOM · WebSocket) — **مش** مكان لجلب البيانات ولا لاشتقاق قيم. البنية: `useEffect(fn, deps)` + دالة تنظيف."},
            {"term": "Ref (useRef)", "def": "قيمة باقية بين الرسمات **بلا** إعادة رسم + مقبض على عنصر DOM. تُستخدم للـtimer/الـAbortController وللتركيز."},
            {"term": "Context", "def": "تمرير قيمة لأسفل الشجرة بلا props متسلسلة (ثيم · مصادقة · لغة) — مقابل `CascadingValue` في Blazor. **مش** بديل لإدارة حالة كبيرة."},
            {"term": "React Compiler", "def": "مترجم بيحسّن التذكير (memoization) تلقائيًا — **1.0 في أكتوبر 2025** واختياري (مفعّل افتراضيًا في قوالب Vite/Next/Expo الجديدة). لو مفعّل، `useMemo`/`useCallback` بتقل أهميتها."},
            {"term": "Suspense / lazy", "def": "تأجيل تحميل جزء من الشجرة (`React.lazy` + `<Suspense fallback>`) — تقسيم الحزم (code splitting). مفيد لصفحات ثقيلة (تقارير/رسوم)."},
            {"term": "Error boundary", "def": "مكوّن بيمسك أخطاء العرض ويعرض بديلًا — **لازم class component** أو مكتبة (`react-error-boundary`)؛ الـhooks ما بتمسكش أخطاء العرض (8.1.4)."},
            {"term": "StrictMode", "def": "في التطوير بيستدعي المكوّنات والـeffects **مرتين** عن قصد لكشف التنظيف الناقص — مش خطأ، وبيختفي في الإنتاج. اللي بيكشفه أخطاء حقيقية."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① المكوّن: دالة + props + حالة"},
        {"type": "code", "lang": "javascript", "title": "src/components/OrderRow.tsx — مكوّن بسيط بكل الأساسيات", "filename": "src/components/OrderRow.tsx", "code": r'''// مكوّن = دالة. Props = معاملات للقراءة فقط.
// ملاحظة: React 19 مش محتاج import لـReact في المشاريع الحديثة (JSX transform جديد).

export type OrderStatus = "placed" | "paid" | "shipped" | "cancelled";

export interface OrderRowProps {
  readonly order: {
    readonly id: string;
    readonly status: OrderStatus;
    readonly total: string;      // decimal كنص (8.1.1)
    readonly currency: "EGP" | "USD";
  };
  readonly selected?: boolean;
  /** الحدث بيطلع لفوق — زي EventCallback في Blazor */
  readonly onSelect?: (id: string) => void;
}

const STATUS_LABEL: Record<OrderStatus, string> = {
  placed: "تم الطلب",
  paid: "مدفوع",
  shipped: "تم الشحن",
  cancelled: "ملغي",
};

export function OrderRow({ order, selected = false, onSelect }: OrderRowProps) {
  return (
    <li
      className={
        "card flex items-center justify-between gap-3 " +
        (selected ? "outline outline-2 outline-brand-600" : "")
      }
    >
      <div className="min-w-0">
        <p className="truncate font-medium" dir="ltr">{order.id}</p>
        <p className="text-sm text-ink-muted">{STATUS_LABEL[order.status]}</p>
      </div>
      <p className="tabular-nums text-sm" dir="ltr">{order.total} {order.currency}</p>
      <button
        type="button"
        className="rounded-md border px-3 py-1.5 text-sm"
        // تمرير الحدث لأعلى. لاحظ: (id) هنا مش (event)
        onClick={() => onSelect?.(order.id)}
        disabled={!onSelect}
      >
        تفاصيل
      </button>
    </li>
  );
}
'''},
        {"type": "code", "lang": "javascript", "title": "useState/useReducer — الحالة والقواعد", "filename": "src/components/CounterDemo.tsx", "code": r'''import { useReducer, useState } from "react";

/** useState: حالة بسيطة. */
export function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div className="card flex items-center gap-3">
      <button
        type="button"
        className="rounded-md border px-3 py-1.5"
        // ⚠️ setCount(count + 1) مرتين متتاليتين = +1 مش +2
        //    لأن React بيجمّع التحديثات (batching) وكلاهما يقرأ نفس count القديم.
        //    الصح للتحديث المتسلسل: الدالة (updater function)
        onClick={() => {
          setCount((c) => c + 1);
          setCount((c) => c + 1);   // الآن النتيجة +2
        }}
      >
        +2
      </button>
      <span className="tabular-nums">{count}</span>
      <button type="button" className="rounded-md border px-3 py-1.5" onClick={() => setCount(0)}>
        تصفير
      </button>
    </div>
  );
}

/** useReducer: حالة مركّبة/انتقالات واضحة (نظير آلة الحالات من 8.1.4). */
type Action =
  | { type: "typing"; value: string }
  | { type: "submit" }
  | { type: "success" }
  | { type: "failure"; error: string };

interface FormState {
  value: string;
  status: "idle" | "submitting" | "success" | "error";
  error?: string;
}

const initialState: FormState = { value: "", status: "idle" };

function reducer(state: FormState, action: Action): FormState {
  switch (action.type) {
    case "typing":
      return { ...state, value: action.value, error: undefined };
    case "submit":
      return { ...state, status: "submitting", error: undefined };
    case "success":
      return { ...state, status: "success", value: "" };
    case "failure":
      return { ...state, status: "error", error: action.error };
    default: {
      // exhaustiveness: لو أضفت action جديد، المترجم هيصرخ هنا
      const _exhaustive: never = action;
      return state;
    }
  }
}

export function useOrderForm() {
  const [state, dispatch] = useReducer(reducer, initialState);
  return { state, dispatch };
}
'''},
        {"type": "table", "caption": "من C#/Blazor إلى React — ترجمة سريعة",
         "head": ["المفهوم", "Blazor / C#", "React / TS", "الفخّ"],
         "rows": [
             ["واجهة المكوّن", "`[Parameter]`", "`props` (interface للـprops)", "Props للقراءة فقط — لا تعدّلها"],
             ["حدث للأب", "`EventCallback<T>`", "`onSomething: (v: T) => void`", "لا تمرّر الحدث كـ`onClick={handler(id)}` — بتستدعيها فورًا"],
             ["حالة محلية", "حقل في `@code` + `StateHasChanged`", "`useState`", "الـsetter غير متزامن — والتحديث المتسلسل محتاج updater function"],
             ["حالة مركّبة", "enum + record", "`useReducer` + discriminated union", "`switch` بلا exhaustiveness = حالة غير معالَجة بصمت"],
             ["مزامنة مع نظام خارجي", "`OnAfterRenderAsync` + JS interop", "`useEffect` + تنظيف", "الـdeps الناقصة = قيم قديمة؛ الزائدة = حلقات"],
             ["مفتاح العنصر", "`@key`", "`key` prop", "استخدام index في قائمة قابلة للتعديل"],
             ["تمرير عبر الشجرة", "`CascadingValue`", "`createContext` + `useContext`", "الإفراط فيه = صعوبة تتبع مصدر القيمة"],
             ["إعادة الرسم", "`StateHasChanged()`", "تلقائي عند تغيّر الحالة/الـprops", "لا تستدعي دالة الرسم يدويًا — تغيّر الحالة هو اللي بيرسم"],
             ["خطأ في العرض", "`<ErrorBoundary>`", "class component / `react-error-boundary`", "الـtry/catch حوالين JSX مش بيمسك أخطاء العرض"],
         ]},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② قواعد الـhooks — اللي بتفشل بصمت"},
        {"type": "code", "lang": "javascript", "title": "hooks-rules.tsx — الأخطاء الأربعة الشائعة وإصلاحها", "filename": "src/examples/hooks-rules.tsx", "code": r'''import { useEffect, useRef, useState } from "react";

// ❌ خطأ 1: hook داخل شرط/حلقة — الترتيب بيتغير بين الرسمات
function BadConditional({ isAdmin }: { isAdmin: boolean }) {
  // if (isAdmin) { const [a, setA] = useState(0); }  ← ممنوع
  return <div />;
}

// ✅ الصح: نادِ كل الـhooks دائمًا، وغيّر المنطق لا عدد النداءات
function GoodConditional({ isAdmin }: { isAdmin: boolean }) {
  const [count, setCount] = useState(0);
  return isAdmin ? <button onClick={() => setCount(count + 1)}>{count}</button> : null;
}

// ❌ خطأ 2: effect بلا dep فيه متغير متغير → حلقة لا نهائية
function BadLoop() {
  const [items, setItems] = useState<number[]>([]);
  // useEffect(() => { setItems([...items, 1]); });  ← بلا deps: بيرسم → يعدّل → يرسم …
  return <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>;
}

// ✅ الصح: deps صحيحة (أو لا تعدّل حالة غير مرتبطة بالـeffect)
function GoodLoop() {
  const [items, setItems] = useState<number[]>([1]);
  const [add, setAdd] = useState(false);

  useEffect(() => {
    if (!add) return;
    setItems((prev) => [...prev, prev.length + 1]);   // updater: بلا اعتماد على items في الـclosure
    setAdd(false);
  }, [add]);

  return (
    <div>
      <button onClick={() => setAdd(true)}>أضف</button>
      <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>
    </div>
  );
}

// ❌ خطأ 3: stale closure — الـeffect شاف قيمة قديمة
function BadStale() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // count هنا بقى 0 للأبد (من أول رسمة) — لأن deps فاضية
      setCount(count + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}

// ✅ الصح: updater function (أو ضيف count للـdeps مع إعادة إنشاء المؤقت)
function GoodCounter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setCount((c) => c + 1), 1000);
    return () => clearInterval(id);          // ✅ تنظيف إلزامي
  }, []);

  return <p className="tabular-nums">{count}</p>;
}

// ❌ خطأ 4: تعديل الحالة مباشرة (mutation) — React مش هيرسم
function BadMutation() {
  const [, force] = useState(0);
  const items = useRef<number[]>([]);
  const add = () => {
    items.current.push(1);       // تعديل بلا رسم — الواجهة مش هتتحدث
    force((n) => n + 1);         // hack: بنجبر رسم يدويًا
  };
  return <button onClick={add}>{items.current.length}</button>;
}

// ✅ الصح: حالة جديدة دائمًا (immutable update)
function GoodImmutable() {
  const [items, setItems] = useState<number[]>([]);
  return (
    <button onClick={() => setItems((prev) => [...prev, 1])}>
      {items.length}
    </button>
  );
}

export { BadConditional, GoodConditional, BadLoop, GoodLoop, BadStale, GoodCounter, BadMutation, GoodImmutable };
'''},
        {"type": "callout", "kind": "danger", "title": "أربع قواعد إن حفظتها تجنبت 80% من أخطاء React",
         "md": "**① الـhooks بترتيب ثابت**: ممنوع في شرط/حلقة/دالة عادية. لو محتاج شرطًا، حط الشرط **داخل** الـhook أو حوالين الـJSX.\n**② الحالة غير قابلة للتعديل**: `setItems(prev => [...prev, x])` — مش `items.push(x)`.\n**③ كل effect له تنظيف**: اشتراك/مؤقت/مستمع/`AbortController` → `return () => cleanup()`، وإلا تسريب وسلوك مكرر (وده اللي `StrictMode` بيكشفه في التطوير).\n**④ الـsetter غير متزامن**: لو التحديث الجديد بيعتمد على القديم، استخدم الصيغة الدالة `setX(prev => …)` — وإلا هتقرأ قيمة قديمة (زي حقل عداد بيفضل ثابت)."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ useEffect: إمتى تستخدمه — وإمتى تكون بتعمل غلط"},
        {"type": "table", "caption": "قرار سريع: هل تحتاج effect؟",
         "head": ["الحالة", "استخدم effect؟", "البديل الصح"],
         "rows": [
             ["جلب بيانات من API", "**لا**", "TanStack Query/RTK Query (8.1.2 ⑤) — بتديك كاش وتحميل/خطأ وإلغاء"],
             ["اشتقاق قيمة من props/state", "**لا**", "احسبها في نفس الرسمة (`const total = items.reduce(…)`)"],
             ["إعادة ضبط الحالة عند تغيّر prop", "**لا**", "`key` على المكوّن (يعيد إنشاءه) أو حساب مشتق"],
             ["الاستجابة لحدث مستخدم", "**لا**", "داخل الـhandler نفسه"],
             ["مؤقت/interval", "**نعم**", "effect + `clearInterval` في التنظيف"],
             ["الاشتراك في WebSocket/EventSource", "**نعم**", "effect + إغلاق في التنظيف (2.2.11)"],
             ["قراءة/تعديل DOM (مكتبة رسم، تمرير، تركيز)", "**نعم**", "effect + `ref`"],
             ["حفظ تفضيل في `localStorage`", "نعم (بحذر)", "effect على القيمة — أو اكتب وقت الحدث نفسه"],
             ["تحليل/تحليلات عند تغيير شاشة", "نعم", "effect مربوط بمفتاح المسار"],
         ]},
        {"type": "code", "lang": "javascript", "title": "useEffect الصحيح: اشتراك + تنظيف + إلغاء (نمط حقيقي)", "filename": "src/hooks/useOrderUpdates.ts", "code": r'''import { useEffect, useRef, useState } from "react";

/**
 * يفتح EventSource لأحداث الطلب ويغلقها عند تفكيك المكوّن/تغيير المعرّف.
 * (الخادم: SSE من 2.2.11 — نفس النمط ينطبق على SignalR/WebSocket.)
 */
export function useOrderUpdates(orderId: string): {
  lastStatus: string | null;
  connected: boolean;
  error: string | null;
} {
  const [lastStatus, setLastStatus] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!orderId) return;

    const source = new EventSource(`/api/orders/${encodeURIComponent(orderId)}/events`);
    sourceRef.current = source;

    const onOpen = () => { setConnected(true); setError(null); };
    const onStatus = (e: MessageEvent) => setLastStatus(String(e.data));
    const onError = () => {
      // EventSource بيعيد المحاولة تلقائيًا — ما نعرضش خطأ نهائي إلا لو أُغلق
      setConnected(false);
      if (source.readyState === EventSource.CLOSED) {
        setError("انقطع الاتصال بالأحداث. أعد تحميل الصفحة للمتابعة.");
      }
    };

    source.addEventListener("open", onOpen);
    source.addEventListener("status", onStatus as EventListener);
    source.addEventListener("error", onError);

    // ✅ التنظيف: أغلق الاتصال وأزل المستمعين
    return () => {
      source.removeEventListener("open", onOpen);
      source.removeEventListener("status", onStatus as EventListener);
      source.removeEventListener("error", onError);
      source.close();
      sourceRef.current = null;
      setConnected(false);
    };
  }, [orderId]);   // ← dep صحيح: يُعاد الاشتراك عند تغيّر الطلب

  return { lastStatus, connected, error };
}
'''},
        {"type": "callout", "kind": "note", "title": "`useEffectEvent`: قيم حديثة بلا إعادة اشتراك (React 19.2)",
         "md": "المشكلة الكلاسيكية: عندك اشتراك لازم يفضل زي ما هو، بس الـcallback محتاج يقرأ **أحدث** قيمة (زي `theme` أو `onMessage`). الحل القديم: `ref` بيتحدّث في effect — والحل الجديد في React 19.2 هو **`useEffectEvent`**:\n\n~~~tsx\nconst onMessage = useEffectEvent((msg: Msg) => {\n  // بيقرأ أحدث props/state دائمًا، ولا يجب إضافته للـdeps\n  showToast(`${msg.text} (${theme})`);\n});\n\nuseEffect(() => {\n  const s = subscribe(onMessage);\n  return () => s.unsubscribe();\n}, []);   // ← اشتراك واحد، والقيم حديثة\n~~~\n\nالقواعد: `useEffectEvent` **ما ينفعش** يُنادى خارج الـeffects، ولا يُمرَّر كـprop. لو إصدارك أقدم، استخدم نمط `useRef` (احفظ أحدث قيمة في ref واقرأها من الـsubscription)."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ القوائم والمفاتيح والرسم الشرطي"},
        {"type": "code", "lang": "javascript", "title": "lists-conditional.tsx — الأخطاء الأربعة في القوائم والشرط", "filename": "src/examples/lists-conditional.tsx", "code": r'''import { useState } from "react";

interface Item { id: string; name: string }

export function ListsDemo() {
  const [items, setItems] = useState<Item[]>([
    { id: "a", name: "أ" },
    { id: "b", name: "ب" },
    { id: "c", name: "ج" },
  ]);
  const [count, setCount] = useState(0);

  return (
    <div className="grid gap-4">
      {/* ✅ المفتاح = هوية ثابتة (id) */}
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>

      {/* ❌ المفتاح = index: عند الحذف من الأول بتتنقل الحالة/التركيز للعنصر الغلط */}
      {/* {items.map((item, i) => <li key={i}>{item.name}</li>)} */}

      {/* ❌ فخّ الرقم صفر: count && … بيطبع 0 عندما count = 0 */}
      {/* {count && <p>لديك {count} عناصر</p>} */}

      {/* ✅ حوّلها لمنطق منطقي */}
      {count > 0 && <p>لديك {count} عناصر</p>}

      {/* ✅ للبدائل الأربعة: ternary أو switch في دالة */}
      {items.length === 0 ? <p>لا عناصر</p> : <p>{items.length} عنصر</p>}

      <button type="button" className="rounded-md border px-3 py-1.5"
              onClick={() => setItems((prev) => prev.slice(1))}>
        احذف الأول
      </button>

      {/* ✅ قائمة قابلة للتعديل: مرّر الحالة للابن عبر props وليس index */}
      <ul className="grid gap-2">
        {items.map((item) => (
          <EditableRow
            key={item.id}
            name={item.name}
            onRename={(name) =>
              setItems((prev) => prev.map((x) => (x.id === item.id ? { ...x, name } : x)))
            }
          />
        ))}
      </ul>

      <button type="button" onClick={() => setCount((c) => c + 1)}>زد العداد</button>
    </div>
  );
}

function EditableRow({ name, onRename }: { name: string; onRename: (n: string) => void }) {
  const [draft, setDraft] = useState(name);   // حالة محلية — آمنة لأن المكوّن مربوط بمفتاح ثابت
  return (
    <li className="flex gap-2">
      <input value={draft} onChange={(e) => setDraft(e.target.value)} className="rounded-md border px-2 py-1" />
      <button type="button" className="rounded-md border px-2 py-1" onClick={() => onRename(draft)}>
        حفظ
      </button>
    </li>
  );
}
'''},
        {"type": "code", "lang": "javascript", "title": "React 19: النماذج بـActions (useActionState) + useOptimistic", "filename": "src/components/OrderForm.tsx", "code": r'''import { useActionState, useOptimistic, useState } from "react";
import { createOrder } from "../api/orders";

/**
 * React 19: <form action={fn}> بتدي حالة الانتظار والنتيجة بلا useState/useEffect يدوية.
 * useActionState: [state, formAction, isPending]
 * - state: نتيجة آخر action (أو القيمة الابتدائية)
 * - formAction: تمرّرها لـ<form action>
 * - isPending: true أثناء التنفيذ (لتعطيل الزر وإظهار مؤشر)
 */
export function OrderForm() {
  const [result, formAction, isPending] = useActionState(
    async (_prev: { ok: boolean; message: string } | null, formData: FormData) => {
      const sku = String(formData.get("sku") ?? "").trim();
      const qty = Number(formData.get("qty") ?? 1);

      if (!sku) return { ok: false, message: "أدخل رمز المنتج." };
      if (!Number.isInteger(qty) || qty < 1) return { ok: false, message: "الكمية يجب أن تكون 1 أو أكثر." };

      try {
        await createOrder({ sku, qty });
        return { ok: true, message: "تم إنشاء الطلب." };
      } catch (err) {
        const e = err as { title?: string; detail?: string };
        return { ok: false, message: e.title ?? e.detail ?? "تعذر إنشاء الطلب." };
      }
    },
    null,
  );

  return (
    <form action={formAction} className="card grid gap-3">
      <label className="grid gap-1">
        <span className="text-sm font-medium">رمز المنتج</span>
        <input name="sku" required className="rounded-md border px-3 py-2" />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">الكمية</span>
        <input name="qty" type="number" min={1} defaultValue={1}
               className="rounded-md border px-3 py-2 tabular-nums" />
      </label>

      <button type="submit" disabled={isPending} className="btn-primary">
        {isPending ? "جارٍ الإنشاء…" : "إنشاء الطلب"}
      </button>

      {/* إعلان النتيجة لقارئ الشاشة (8.1.4) */}
      {result ? (
        <p role={result.ok ? "status" : "alert"}
           className={result.ok ? "text-sm text-success" : "text-sm text-danger"}>
          {result.message}
        </p>
      ) : null}
    </form>
  );
}

/**
 * useOptimistic: تحديث متفائل — بيرجع للحالة الأصلية تلقائيًا عند الفشل
 * (نفس فكرة 8.1.4 ⑤ بس بلا snapshot يدوي).
 */
export function CartList({ items }: { items: { sku: string; name: string }[] }) {
  const [pendingAdd, setPendingAdd] = useState<string | null>(null);
  const [optimisticItems, addOptimistic] = useOptimistic(
    items,
    (current, sku: string) => [...current, { sku, name: "…" }],
  );

  async function handleAdd(sku: string) {
    setPendingAdd(sku);
    addOptimistic(sku);                     // يظهر فورًا داخل <form action> أو transition
    try {
      await fetch(`/api/cart/${encodeURIComponent(sku)}`, { method: "POST", headers: { "X-Csrf": "1" } });
    } finally {
      setPendingAdd(null);
    }
  }

  return (
    <ul>
      {optimisticItems.map((i) => <li key={i.sku}>{i.name}</li>)}
      <button type="button" onClick={() => void handleAdd("SKU-1")} disabled={pendingAdd !== null}>
        أضف للسلة
      </button>
    </ul>
  );
}
'''},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ السياق والأداء والتنظيم"},
        {"type": "code", "lang": "javascript", "title": "theme-context.tsx — سياق ثيم مع provider تركيب", "filename": "src/context/ThemeContext.tsx", "code": r'''import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("theme");
    return saved === "dark" ? "dark" : "light";
  });

  // القيمة مُعاد بناؤها فقط عند تغيّر theme — وإلا كل مستهلك بيرسم مع كل رسمة للأب
  const value = useMemo<ThemeContextValue>(() => ({
    theme,
    toggle: () => setTheme((t) => {
      const next = t === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      document.documentElement.dataset.theme = next;
      return next;
    }),
  }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme يجب أن يُستخدم داخل <ThemeProvider>");
  return ctx;
}
'''},
        {"type": "table", "caption": "أداء React: 6 أدوات — وما تغيّر مع React Compiler",
         "head": ["الأداة", "تحل إيه", "مع React Compiler (1.0)", "الفخّ"],
         "rows": [
             ["**`key` صحيح**", "صحّة القوائم والحالة", "لسه إلزامي", "index/مفقود"],
             ["**`React.lazy` + `Suspense`**", "حجم الحزمة الأول (تقسيم)", "لسه أساسي", "تقسيم مفرط = طلبات كثيرة ومؤشرات تحميل"],
             ["**`useMemo`/`useCallback`**", "تقليل إعادة الحساب/تغيير الهوية", "**مترجم بيعملها تلقائيًا** في الغالب", "إضافتها بلا قياس = تعقيد بلا فائدة"],
             ["**`memo`**", "منع إعادة رسم مكوّن ثقيل", "مترجم بيتعامل معاها", "مقارنة props ضحلة — كائن جديد كل رسمة = بلا فائدة"],
             ["**`useTransition`/`startTransition`**", "تحديثات ثقيلة بلا تجميد الواجهة", "لسه مفيد", "استخدامه لعمليات شبكة بدل حالات الحساب"],
             ["**`Virtualize` (مكتبة)**", "قوائم ضخمة", "لسه ضروري", "— (البديل: `@tanstack/react-virtual`)"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قاعدة الأداء: قِس قبل، وقِس بعد",
         "md": "**①** React بيحذّر: «لا تُحسّن قبل القياس». استخدم **React DevTools → Profiler** وحدد المكوّن الغالي فعلًا.\n**②** مع React Compiler (مفعّل في القوالب الجديدة) أغلب `useMemo`/`useCallback` بقت غير ضرورية — **لو شغّال على نسخة 19.2+** راجع التوثيق قبل إضافتها يدويًا.\n**③** أهم تحسينين عمليًا: **تقسيم الحزم** (Suspense + lazy للصفحات) و**Virtualize** للقوائم الكبيرة — مش التذكير الدقيق.\n**④** إعادة الرسم مش مشكلة في حد ذاتها: مشكلة لو الرسمة غالية (حسابات/عناصر كثيرة) أو متكررة بلا داعٍ (timer بلا سبب)."},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ التنظيم: هيكل مشروع React لمطور .NET"},
        {"type": "code", "lang": "text", "title": "هيكل مقترح — Vertical Slice (4.2) لكن للواجهة", "filename": "docs/react-structure.txt", "code": r'''src/
├── main.tsx                  # نقطة الدخول: createRoot + Providers
├── app/
│   ├── App.tsx               # التوجيه (router) + الـlayout
│   ├── providers.tsx         # QueryClient · ThemeProvider · AuthProvider
│   └── routes.tsx            # تعريف المسارات (lazy للصفحات الثقيلة)
├── api/
│   ├── client.ts             # العميل الموحّد (8.1.2)
│   ├── types.ts              # الأنواع (مولّدة من OpenAPI حيث ممكن)
│   └── orders.ts             # endpoints الخاصة بالطلبات
├── features/                 # ← العمود الفقري: كل ميزة مجلد
│   ├── orders/
│   │   ├── OrdersPage.tsx
│   │   ├── OrderForm.tsx
│   │   ├── useOrders.ts      # query/mutation
│   │   └── orders.test.tsx
│   └── customers/…
├── components/               # مكوّنات عامة قابلة لإعادة الاستخدام (Button · DataState)
├── context/                  # Theme/Auth/Toast
├── hooks/                    # hooks عامة (useDebounced · useOnline)
├── styles/app.css            # Tailwind v4 (8.1.3)
└── test/setup.ts             # Vitest + Testing Library + msw

## قواعد
1) الميزة الواحدة في مجلد واحد (features/orders) — مفيش مجلد global للـcomponents الخاصة بميزة.
2) `components/` للمكوّنات العامة فقط (بلا معرفة بمجال الأعمال).
3) كل استدعاء API عبر `api/` أو hook الميزة — ممنوع `fetch` موزّع في المكوّنات.
4) كل صفحة lazy-loaded في الراوتر (تقسيم الحزم).
5) الاختبار بجنب الكود (`*.test.tsx`) — والاختبارات على السلوك لا التنفيذ.
6) لا أسرار ولا مفاتيح (8.1.1 ⑦) — كل شيء في الحزمة مكشوف.
'''},
        {"type": "code", "lang": "bash", "title": "إعداد المشروع + Router + الاختبار", "filename": "terminal/react-setup.sh", "code": r'''# 1) المشروع (Vite + React + TS)
npm create vite@latest shop-web -- --template react-ts
cd shop-web
npm install

# 2) التوجيه (React Router v7 — الوضع المكتبي/SPA)
npm install react-router

# 3) طبقة البيانات (TanStack Query — تُستخدم في 8.2.4)
npm install @tanstack/react-query
npm install -D @tanstack/react-query-devtools

# 4) الاختبار
npm install -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom msw
npm pkg set scripts.test="vitest run"
npm pkg set scripts.typecheck="tsc --noEmit"
npm pkg set scripts.lint="eslint src --max-warnings=0"

# 5) Tailwind v4 (8.1.3)
npm install tailwindcss @tailwindcss/vite

# 6) تشغيل
npm run dev
npm run typecheck
npm run test

# ملاحظة: React 19 بيتطلب JSX transform جديد (افتراضي في قالب Vite الحالي) —
# فمش محتاج import React في كل ملف.
''',
         },
        {"type": "code", "lang": "javascript", "title": "app/routes.tsx + DataState بسيط (نفس فلسفة 8.1.4)", "filename": "src/app/routes.tsx", "code": r'''import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";

// كل صفحة في حزمة منفصلة — تحميل أولي أصغر
const OrdersPage = lazy(() => import("../features/orders/OrdersPage"));
const CustomersPage = lazy(() => import("../features/customers/CustomersPage"));

function PageFallback() {
  return (
    <div className="grid gap-2 p-6" aria-busy="true">
      <p className="sr-only" role="status">جارٍ تحميل الصفحة</p>
      <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
      <div className="h-24 w-full animate-pulse rounded bg-gray-200" />
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    // عناصر الـlayout (شريط تنقل) — تُحمَّل مرة واحدة
    element: <AppLayout />,
    children: [
      { index: true, element: <Suspense fallback={<PageFallback />}><OrdersPage /></Suspense> },
      { path: "orders", element: <Suspense fallback={<PageFallback />}><OrdersPage /></Suspense> },
      { path: "customers", element: <Suspense fallback={<PageFallback />}><CustomersPage /></Suspense> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

export function App() {
  return <RouterProvider router={router} />;
}

// مكوّنات بديلة صغيرة (توضيحية)
function AppLayout() { return <main className="min-h-screen bg-surface p-6" />; }
function NotFound() { return <p className="p-6">الصفحة غير موجودة — <a href="/">رجوع</a></p>; }
'''},

        # ───────────────────────────────────────────── ⑦
        {"type": "heading", "level": 2, "text": "⑦ عشر عادات تفصل مطور .NET الجاد عن «كتب حاجة React»"},
        {"type": "table", "caption": "أخطاء النماذج الذهنية — وما تفعله بدلًا منها",
         "head": ["#", "العادة الخاطئة", "الصحيح"],
         "rows": [
             ["1", "جلب البيانات في `useEffect` يدويًا", "TanStack/RTK Query — كاش وإلغاء وتحليل حالات مجاني"],
             ["2", "حالة مشتقة في state (`useState` ثم effect يحدّثها)", "احسب المشتق في الرسمة"],
             ["3", "`useEffect` بيزامن props مع state", "`key` على المكوّن لإعادة الإنشاء"],
             ["4", "تعديل الكائن/المصفوفة مباشرة", "استبدال غير قابل للتعديل (`{...x}`, `[…arr]`)"],
             ["5", "استدعاء الحدث في الـJSX: `onClick={save(id)}`", "`onClick={() => save(id)}`"],
             ["6", "مفتاح = index في قائمة قابلة للتعديل", "معرّف ثابت"],
             ["7", "تجاهل التنظيف في الـeffects", "دالة تنظيف لكل اشتراك/مؤقت/AbortController"],
             ["8", "`fetch` موزّع في المكوّنات", "طبقة `api/` + hook لكل ميزة"],
             ["9", "إخفاء عناصر حسب الدور كحماية", "التفويض في الـAPI + إخفاء للعرض فقط (7.2.3)"],
             ["10", "`useMemo`/`useCallback` في كل مكان", "قِس أولًا؛ ومع React Compiler قلّلها"],
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أشرح `UI = f(state)` وأعرف إن إعادة الرسم = إعادة تنفيذ الدالة ثم تحديث الـDOM بالفرق.",
            "أكتب مكوّنًا بـTSX بـprops للقراءة فقط وحدث `(v: T) => void` للأعلى.",
            "أعرف الأربع قواعد الذهبية: ترتيب الـhooks · الحالة غير قابلة للتعديل · تنظيف الـeffects · الـsetter غير متزامن (استخدم updater).",
            "أفرّق بين ما يحتاج `useEffect` وما لا يحتاجه (جلب/اشتقاق/أحداث = لا).",
            "أستخدم `useRef` و`useEffectEvent` للقيم الحديثة بلا إعادة اشتراك.",
            "أكتب قوائم بمفاتيح صحيحة، وأتجنب فخّ `count && …` مع القيمة 0، وأستخدم ternary/switch.",
            "أستخدم React 19: `<form action>` + `useActionState` + `useOptimistic` بدل يدوي.",
            "أبني سياقًا بـprovider + `useMemo` للقيمة وحماية الاستخدام بـ`useContext` مع خطأ واضح.",
            "أقسّم الحزم بـ`React.lazy` + `Suspense`، وأفهم أثر React Compiler على `useMemo`/`useCallback`.",
            "أرتّب المشروع بـfeatures + api + components، وأختبر بـVitest/Testing Library.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على React لمطور .NET.",
         "questions": [
             {"q": "`onClick={() => { setCount(count + 1); setCount(count + 1); }}` — ما النتيجة؟",
              "options": ["+2", "+1 لأن كلا الاستدعاءين قرأ نفس القيمة القديمة", "خطأ ترجمة", "صفر"],
              "answer": 1,
              "explain": "React بيجمّع التحديثات في نفس الحدث؛ كل استدعاء بـ`count` القديم فالناتج نفسه. الصحيح للتحديث المتسلسل: `setCount(c => c + 1)` مرتين."},
             {"q": "أي مما يلي **لا** يحتاج `useEffect`؟",
              "options": ["فتح WebSocket وإغلاقه", "مؤقت يعمل كل ثانية", "اشتقاق إجمالي السلة من عناصرها", "قراءة مستمع حدث على `window`"],
              "answer": 2,
              "explain": "القيم المشتقة تُحسب في نفس الرسمة (`items.reduce(…)`) — لا state ولا effect. الباقي مزامنة مع نظام خارجي فتحتاج effect + تنظيف."},
             {"q": "لماذا `useEffect` بلا مصفوفة تبعيات (ولا تنظيف) مع `setState` داخلية قد تسبب حلقة لا نهائية؟",
              "options": ["لأن React بطيء",
                          "لأن الـeffect يعمل بعد كل رسمة، وتعديل الحالة يسبب رسمة جديدة → effect جديد… وهكذا",
                          "لأن setState محظور في effects",
                          "لأن المصفوفة الفارغة إلزامية"],
              "answer": 1,
              "explain": "بلا deps الـeffect بينفذ بعد كل رسمة؛ ولو عدّل حالة بلا شرط توقف داخل حلقة. الحل: deps صحيحة، أو شرط داخل الـeffect، أو — الأفضل — تحويل المنطق لمكانه الصحيح (handler/قيمة مشتقة/مكتبة بيانات)."},
             {"q": "قائمة أدوات بأزرار حذف، والمفتاح هو `index`. ما الخطر؟",
              "options": ["لا خطر",
                          "React بيعيد استخدام حالة/عناصر DOM للموضع نفسه، فيتنقل التركيز/الحالة لعنصر آخر بعد الحذف",
                          "بطء في الأداء فقط",
                          "خطأ ترجمة"],
              "answer": 1,
              "explain": "index مش هوية — بعد حذف العنصر الأول، العنصر التاني بياخد index 0 فيورّث حالة/تركيز العنصر السابق. استخدم معرّفًا ثابتًا (`order.id`) زي `@key` في Blazor."},
             {"q": "`{count && <Badge count={count} />}` عندما `count = 0` — ماذا يُعرض؟",
              "options": ["لا شيء", "الرقم 0 نفسه (لأن 0 falsy وتُعاد قيمته)", "خطأ", "Badge بقيمة 0"],
              "answer": 1,
              "explain": "أشهر فخّ في JSX: `&&` بترجع المعامل الأيسر لو كان falsy — فبيظهر «0». استخدم `count > 0 && …` أو ternary."},
             {"q": "ما فائدة `useActionState` في React 19؟",
              "options": ["إدارة الحالة العامة",
                          "<form action> بياخد دالة async، وتاخد [state, formAction, isPending] — فتحصل على نتيجة الانتظار والحالة بلا useEffect يدوي",
                          "بديل لـuseReducer فقط",
                          "لجلب البيانات"],
              "answer": 1,
              "explain": "دي طريقة React 19 للنماذج: الفورم بيعمل submit للـaction (server أو client)، و`isPending` بيديك مؤشر الانتظار، و`state` نتيجة آخر تنفيذ — فبتختفي الحاجة لـ`useState` للتحميل والخطأ."},
             {"q": "بعد تفعيل React Compiler، ما موقف `useMemo`/`useCallback`؟",
              "options": ["ممنوعة",
                          "بتقل أهميتها لأن المترجم بيعمل تحسين التذكير تلقائيًا — فالأفضل قياس الحاجة قبل إضافتها يدويًا",
                          "إلزامية كما هي",
                          "بتشتغل في الإنتاج فقط"],
              "answer": 1,
              "explain": "React Compiler 1.0 (أكتوبر 2025) بيحلل المكوّنات ويضيف التذكير تلقائيًا. مع ذلك: لسه فيه حالات تحتاج تحكمًا يدويًا، والقاعدة العامة «قِس قبل ما تحسّن» (8.2.3 ⑤)."},
             {"q": "مكوّن `OrderRow` استثمر `onSelect` في `onClick={onSelect(order.id)}`. ما المشكلة؟",
              "options": ["بطء",
                          "الاستدعاء بيحصل وقت الرسم مش عند الضغط — الحل `onClick={() => onSelect(order.id)}`",
                          "لا مشكلة",
                          "خطأ ترجمة"],
              "answer": 1,
              "explain": "`onClick={fn(x)}` بينفذ `fn` فورًا ويحط ناتجها (عادة undefined) كـhandler. لازم تمرر دالة: `() => fn(x)`. غلطة رقم 5 في جدول العادات."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "صفحة React كاملة + إصلاح أخطاء حقيقية.",
         "items": [
            {"id": "s8-m2-l3-t1",
             "title": "مهمة 1: صفحة طلبات React كاملة (بلا مكتبة بيانات)",
             "md": "ابنِ صفحة طلبات في Vite + React 19 + TS: قائمة بحالات التحميل/الفراغ/الخطأ (بلا TanStack — عشان تفهم الأساس قبل 8.2.4)، بحث بـdebounce وإلغاء، نموذج إنشاء بـ`<form action>` + `useActionState`، وتفاصيل مع `ErrorBoundary`. استخدم Tailwind v4 من 8.1.3 ونفس مفاهيم 8.1.4.",
             "criteria": [
                 "`tsconfig` صارم (من 8.1.1) و`eslint` بصفر تحذيرات + `npm run typecheck` و`npm test` ناجحان.",
                 "قائمة بمفاتيح `id` وأزرار حذف/تفاصيل — مع دليل إن الحالة/التركيز لا تنتقل بالخطأ (اختبار أو لقطة).",
                 "بحث: `useDebounced` بـ`useEffect` + تنظيف + `AbortController` وإلغاء الطلب السابق، و`AbortError` مش خطأ.",
                 "نموذج `<form action>` + `useActionState`: `isPending` بيعطّل الزر ويعرض «جارٍ الإنشاء»، ونتيجة النجاح/الفشل بـ`role=status`/`role=alert`.",
                 "`ErrorBoundary` حوالين منطقة المحتوى (class component أو `react-error-boundary`) مع زر إعادة ضبط.",
                 "**صفر** `useEffect` لجلب البيانات في أول تحميل — الجلب في hook واضح مع حالات (وده مقصود قبل TanStack).",
                 "3 اختبارات Vitest + Testing Library: حالة خطأ 403 · إرسال نموذج ناجح · بحث بيستدعي الـAPI مرة واحدة بعد debounce.",
                 "ملف `docs/react-vs-blazor.md`: 8 فروق من جدول الدرس بأمثلة من كودك.",
             ],
             "hint": "اختبار الـdebounce: `vi.useFakeTimers()` + `await vi.advanceTimersByTimeAsync(300)` ثم تحقق من عدد الاستدعاءات. واختبار `useActionState`: `userEvent.type` ثم `userEvent.click` على submit، وانتظر النص الجديد بـ`findByRole` (React 19 بيعمل transitions فلازم `await`). ولو الـ`ErrorBoundary` مش بيمسك خطأ: تأكد إن الخطأ بيحصل **أثناء العرض** لا داخل event handler (أخطاء الـhandlers مش بتمسكها boundaries).",
             "solution": "النتائج النموذجية: أول نسخة بتقع في فخّ الجلب في `useEffect` بلا إلغاء → استجابة قديمة بتكتب فوق الجديدة؛ والتجربة بتكشفها. تاني أكبر مشكلة: نموذج بـ`useState` لكل حقل ثم `onSubmit` يدوي — وReact 19 بيخليها أبسط بـ`action`. وفي الاختبارات، أكثر عقبة هي الانتظار الصحيح (transitions) — استخدم `findBy*` بدل `getBy*`. النتيجة المتوقعة: ~350 سطرًا موزعة على 6–8 ملفات، و3 اختبارات تعدي، وصفحة شبه مطابقة لسلوك نسخة Blazor من 8.2.2 — وده بيخلي الفرق بين التقنيتين واضحًا في ذهنك.",
             "resources": [
                 "https://react.dev/learn",
                 "https://react.dev/reference/react/useActionState",
                 "https://testing-library.com/docs/react-testing-library/intro/",
                 "https://vitest.dev/guide/",
                 "https://reactrouter.com/",
             ]},
            {"id": "s8-m2-l3-t2",
             "title": "مهمة 2: تشريح 4 مكوّنات فيها أخطاء (وامنع تكرارها بـlint)",
             "md": "خد الأربع حالات الخاطئة من كود الدرس (`hooks-rules.tsx`: شرط حول hook · حلقة effect · stale closure · mutation) وأعد إنتاجها في مشروعك، وسجّل السلوك الفعلي (رسالة الخطأ/الواجهة المكسورة)، ثم أصلح كل واحدة واشرح المبدأ. وأضف قواعد ESLint تمنع تكرارها.",
             "criteria": [
                 "4 تقارير: الحالة · العَرَض الفعلي (رسالة React في console أو سلوك UI مصوّر) · السبب · الإصلاح · المبدأ.",
                 "`hooks/rules-of-hooks` و`react-hooks/exhaustive-deps` مفعّلتان في ESLint — مع مثال على تحذير حقيقي ومحتواه.",
                 "إثبات أثر `StrictMode`: effect بينفذ مرتين في التطوير، وسلوكك **صحيح مع التنظيف** (لقطة/سجل).",
                 "مثال `useEffectEvent` (أو نمط `useRef`) بديلًا عن deps مضللة — مع شرح لماذا الاشتراك ما بيعادش.",
                 "اختبار يفشل قبل الإصلاح وينجح بعده (واحد على الأقل من الأربعة).",
                 "خلاصة نصف صفحة: أي اثنين من الأخطاء الأربعة شفتهم فعلًا في كود إنتاج/مشروع سابق؟",
             ],
             "hint": "استخدم `npx eslint --print-config src/file.tsx` للتأكد من تفعيل القواعد. ولو `react-hooks/exhaustive-deps` بيصرخ على دالة داخلية: لفّها في `useCallback` أو انقلها خارج المكوّن، أو استخدم `useEffectEvent` لو الحالة ده هو الصح. ولإثبات `StrictMode`: عدّاد في `console.log` داخل effect — هتشوف 2 في التطوير و1 في الإنتاج (بعد `npm run build && npm run preview`).",
             "solution": "الأعراض النموذجية: (1) hook داخل شرط → «Rendered more hooks than during the previous render» أو ترتيب حالة غلط؛ (2) effect بلا deps مع setState → «Maximum update depth exceeded»؛ (3) stale closure → العداد بيفضل 0 أو القيمة القديمة (وده أخبثها لأنه **ما بيرميش خطأ**)؛ (4) mutation → الواجهة ما بتتحدثش. القاعدة العملية اللي بتطلع من التجربة: **أخطاء React الصامتة (stale closure/mutation) أغلى بكتير من اللي بترمي**، فالقواعد الآلية (ESLint + `strict` + React Compiler) مش رفاهية — هي اللي بتمسك الصامت. وأكتر فائدة مستدامة: تحويل الـ4 أنماط لاختبارات/قواعد في الريبو تمنع رجوعها.",
             "resources": [
                 "https://react.dev/reference/rules",
                 "https://react.dev/learn/synchronizing-with-effects",
                 "https://react.dev/learn/you-might-not-need-an-effect",
                 "https://react.dev/reference/react/useEffectEvent",
                 "https://www.npmjs.com/package/eslint-plugin-react-hooks",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "React: التعلّم", "url": "https://react.dev/learn"},
            {"label": "React: قواعد React", "url": "https://react.dev/reference/rules"},
            {"label": "React: قد لا تحتاج إلى Effect", "url": "https://react.dev/learn/you-might-not-need-an-effect"},
            {"label": "React: useActionState", "url": "https://react.dev/reference/react/useActionState"},
            {"label": "React: useEffectEvent", "url": "https://react.dev/reference/react/useEffectEvent"},
            {"label": "React Router", "url": "https://reactrouter.com/"},
            {"label": "Testing Library", "url": "https://testing-library.com/docs/react-testing-library/intro/"},
            {"label": "eslint-plugin-react-hooks", "url": "https://www.npmjs.com/package/eslint-plugin-react-hooks"},
        ]},
    ],
}

LESSONS_S8_G = [_L3]
