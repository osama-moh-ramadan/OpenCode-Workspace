# -*- coding: utf-8 -*-
"""Stage 8 module 2 (part H): s8-m2-l4 (ربط React بـAPI: OIDC وRTK Query)."""

TODAY = "2026-10-22"

_L4 = {
    "id": "s8-m2-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "بعد ما فهمت الأساس (8.2.3)، الخطوة العملية هي **طبقة بيانات منظمة** بدل `fetch` موزّع في المكوّنات: كاش · إعادة جلب · إلغاء · تحميل/خطأ · إبطال بعد الطفرة · وإعادة محاولة ذكية. وفي نفس الوقت: **مصادقة صحيحة** لم تطبّقها في 8.1.2 (نمط BFF) بشكل كامل في تطبيق React منفصل.\n\nالدرس ده بيعطيك **الخريطة الكاملة**: جدول قرار بين TanStack Query وRTK Query · إعداد RTK Query بالكامل (baseQuery بـrefresh وإلغاء وتحويل ProblemDetails) · العلامات (tags) والإبطال بعد الطفرة · حماية المسارات حسب الصلاحيات · والفرق العملي بين **BFF** (موصى به) و**OIDC من الـSPA بـPKCE** (لما مفيش خادم تملكه) — مع الكود والتحذيرات."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "طبقة بيانات (data layer)", "def": "الطبقة المسؤولة عن جلب/كاش/تحديث بيانات الخادم — لا المكوّنات. الفكرة: كل مكوّن يسأل «عايز الطلبات» والطبقة تدير الباقي (مفتاح، كاش، إعادة جلب، إلغاء)."},
            {"term": "RTK Query", "def": "طبقة بيانات مدمجة في **Redux Toolkit**: `createApi` + `fetchBaseQuery` + endpoints + hooks مولّدة (`useGetOrdersQuery`) + **tags** للإبطال. مناسبة لو فريقك على Redux أو عايز codegen قوي من OpenAPI."},
            {"term": "TanStack Query", "def": "مكتبة كاش مستقلة عن إدارة الحالة (v5.104 في أكتوبر 2026): `useQuery`/`useMutation` + `queryKey` + `staleTime`/`gcTime` + `invalidateQueries`. أخف وأشيع في المشاريع الحديثة."},
            {"term": "Tag-based invalidation", "def": "نمط RTK: كل endpoint بيعلن `providesTags`، وكل mutation بتعلن `invalidatesTags` — فأي تغيير بيجبر الاستعلامات المرتبطة تعيد الجلب تلقائيًا. بديله في TanStack: `invalidateQueries({ queryKey })`."},
            {"term": "codegen من OpenAPI", "def": "توليد endpoints وأنواع من مستند OpenAPI 3.1 بتاع الـAPI (2.1.1) — يمنع أخطاء الأسماء ويخلي تغيير العقد يظهر كخطأ ترجمة."},
            {"term": "BFF للمصادقة", "def": "المتصفح بياخد **كوكي جلسة HttpOnly** فقط؛ الخادم يحمل التوكنات ويوكّل الطلبات. (نفس 8.1.2 — وده النمط الموصى به من RFC 10017)."},
            {"term": "OIDC في الـSPA (public client)", "def": "SPA بيعمل Authorization Code + **PKCE** بنفسه مع مزود الهوية، ويحمل access token قصير في الذاكرة. يُستخدم لما مفيش خادم تملكه — بقيود أمنية (8.1.2)."},
            {"term": "Silent renew / refresh", "def": "جلب access token جديد قبل انتهائه: في BFF بنداء `/auth/refresh` يقرأ كوكي الـrefresh · في SPA بـ`oidc-client-ts`/`msal-browser` (تجديد صامت + تدوير)."},
            {"term": "Protected route", "def": "مسار بيتطلب حالة مصادقة/دور. مهم: هو **تجربة مستخدم** — الحماية الحقيقية في الـAPI (7.2.3)."},
            {"term": "Optimistic mutation", "def": "تحديث الكاش محليًا قبل تأكيد الخادم (RTK: `onQueryStarted` + `updateQueryData`)، مع تراجع عند الفشل (pattern 8.1.4 ⑤)."},
            {"term": "Polling / refetchInterval", "def": "إعادة جلب دورية للبيانات شبه الحية القصيرة (حالة طلب) بدل WebSocket — أرخص تعقيدًا وأسوأ زمن استجابة (2.2.11 يقارن SSE/WebSocket)."},
            {"term": "Error normalization", "def": "تحويل كل فشل (HTTP/شبكة/انتهاء جلسة) لشكل واحد يفهمه UI — في RTK عبر `baseQuery` مخصص بيرجع `{ error }` من ProblemDetails."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① TanStack Query أو RTK Query؟"},
        {"type": "table", "caption": "المقارنة العملية — اختار واحد وامشِ",
         "head": ["المعيار", "**TanStack Query v5**", "**RTK Query**", "ملاحظة"],
         "rows": [
             ["الفلسفة", "كاش لبيانات الخادم فقط (مش إدارة حالة عامة)", "جزء من Redux Toolkit (بتستخدمه جوه store)", "لو فريقك بلا Redux، TanStack أخف"],
             ["الحجم", "~12KB gzip", "~14KB + Redux", "فرق بسيط عمليًا"],
             ["التوليد من OpenAPI", "يدوي/بسيط (أنواع + fetcher)", "**codegen قوي** (`@rtk-query/codegen-openapi`)", "قوة RTK الحقيقية في المشاريع الكبيرة"],
             ["إبطال الكاش", "`invalidateQueries({ queryKey })`", "**tags** `providesTags`/`invalidatesTags`", "tags أوضح للفرق الكبيرة"],
             ["DevTools", "ممتازة (مخصصة)", "Redux DevTools (مع كل الـstore)", "الاتنان كافيان"],
             ["التكامل مع Blazor/SSR", "دعم SSR/hydration ناضج", "ممكن لكن أقل شيوعًا", "لو عندك SSR، TanStack أسهل"],
             ["أشيع في السوق (2026)", "**الأوسع** في مشاريع React الحديثة", "شائع مع فرق Redux القائمة", "لو بتبدأ من صفر: TanStack"],
             ["قرار الدرس", "—", "**نكتب RTKQuery** لأنه بيدّي أوضح مثال على تحويل الأخطاء وtags + codegen", "والتطبيق يتنقل بينهما بسهولة"],
         ]},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② RTK Query: الإعداد الكامل (baseQuery + تحويل الأخطاء)"},
        {"type": "code", "lang": "javascript", "title": "src/api/baseQuery.ts — ترويسات، كوكي، CSRF، تحويل ProblemDetails", "filename": "src/api/baseQuery.ts", "code": r'''import {
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";
import type { ApiError } from "./types";

/** الترويسات الموحدة: كوكي الجلسة + دفاع CSRF (8.1.2). */
const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE ?? "/api",
  credentials: "include",                 // نمط BFF: كوكي HttpOnly فقط
  prepareHeaders: (headers) => {
    headers.set("Accept", "application/json");
    headers.set("X-Csrf", "1");           // ترويسة مطلوبة للطلبات المعدّلة
    return headers;
  },
});

/**
 * baseQuery مناسب للإنتاج:
 *   • يحوّل أي فشل إلى ApiError موحّد (شكل واحد للـUI).
 *   • عند 401: محاولة تجديد **مرة واحدة** ثم إعادة الطلب (single-flight — 8.1.2).
 *   • بلا تكرار لا نهائي: نمنع إعادة المحاولة لطلب التجديد نفسه.
 */
export const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  ApiError
> = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error?.status === 401 && !isAuthEndpoint(args)) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      result = await rawBaseQuery(args, api, extraOptions);
    }
  }

  if (result.error) {
    return { error: normalizeError(result.error) };
  }

  return { data: result.data };
};

// إشارة مشتركة: طلبات متعددة فاشلة بـ401 → تجديد واحد فقط
let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  refreshPromise ??= (async () => {
    try {
      const res = await fetch("/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "X-Csrf": "1" },
        signal: AbortSignal.timeout(10_000),
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      // نترك الإشارة تُصفَّر بعد دورة الحدث التالية
      setTimeout(() => { refreshPromise = null; }, 0);
    }
  })();

  const ok = await refreshPromise;
  if (!ok) {
    // في BFF: إعادة توجيه لتسجيل الدخول مع الرجوع لنفس المسار
    // (الخادم يتحقق أن returnUrl نسبي — 8.1.2)
    const back = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/bff/login?returnUrl=${back}`);
  }
  return ok;
}

function isAuthEndpoint(args: string | FetchArgs): boolean {
  const url = typeof args === "string" ? args : args.url;
  return url.startsWith("/auth/") || url.startsWith("/bff/");
}

/** يحوّل خطأ fetchBaseQuery إلى ApiError (نفس الشكل في كل التطبيق). */
export function normalizeError(err: FetchBaseQueryError): ApiError {
  // خطأ شبكة/إلغاء/مهلة: FetchBaseQueryError بـstatus === 'FETCH_ERROR' أو 'TIMEOUT_ERROR' أو 'CUSTOM_ERROR'
  if (typeof err.status === "string") {
    const isTimeout = err.status === "TIMEOUT_ERROR";
    return {
      status: 0,
      title: isTimeout ? "انتهت مهلة الاتصال" : "تعذر الوصول إلى الخادم",
      detail: isTimeout ? undefined : "تحقق من الاتصال ثم أعد المحاولة.",
    };
  }

  const data = err.data as Partial<{
    title: string; detail: string; traceId: string;
    errors: Record<string, string[]>;
  }> | undefined;

  return {
    status: err.status,
    title: data?.title ?? defaultTitle(err.status),
    detail: data?.detail,
    correlationId: data?.traceId,
    fieldErrors: data?.errors,
  };
}

function defaultTitle(status: number): string {
  if (status === 403) return "ليست لديك صلاحية لهذا الإجراء";
  if (status === 404) return "العنصر غير موجود";
  if (status === 409) return "تعارض مع حالة أحدث — حدّث البيانات";
  if (status === 429) return "طلبات كثيرة — حاول بعد قليل";
  if (status >= 500) return "خطأ في الخادم";
  return `طلب غير ناجح (${status})`;
}

'''},
        {"type": "code", "lang": "javascript", "title": "src/api/shopApi.ts — createApi + endpoints + tags + تحويل النتائج", "filename": "src/api/shopApi.ts", "code": r'''import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "./baseQuery";
import type { OrderDto, PageDto, CreateOrderRequest, ApiError } from "./types";

/**
 * الـAPI الواحد للتطبيق: كل endpoint هنا، وكل hook مولّد منه.
 * لاحظ: tags بتمنع «الواجهة مش بتتحدث» — أشهر شكوى في التطبيقات اليدوية.
 */
export const shopApi = createApi({
  reducerPath: "shopApi",
  baseQuery: baseQueryWithReauth,
  tagTypes: ["Order", "Customer", "Cart"],
  keepUnusedDataFor: 60,        // ثوانٍ يُحتفظ بالكاش بعد آخر مستخدم
  refetchOnFocus: false,        // فعّلها لو البيانات بتتغير كتير وبتحتاج تحديث عند الرجوع للتاب
  refetchOnReconnect: true,     // عند عودة الشبكة أعد الجلب (8.1.4 offline)
  endpoints: (builder) => ({
    // ── قراءة ──────────────────────────────────────────────────────
    getOrders: builder.query<PageDto<OrderDto>, { cursor?: string; q?: string }>({
      query: ({ cursor, q }) => ({
        url: "orders",
        params: { limit: 20, ...(cursor ? { cursor } : {}), ...(q ? { q } : {}) },
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({ type: "Order" as const, id })),
              { type: "Order" as const, id: "LIST" },
            ]
          : [{ type: "Order" as const, id: "LIST" }],
      // دمج الصفحات لـ«تحميل المزيد» (cursor)
      serializeQueryArgs: ({ endpointName, queryArgs }) =>
        `${endpointName}(${queryArgs.q ?? ""})`,   // الكاش لكل نص بحث، وليس لكل cursor
      merge: (current, incoming) => {
        current.items.push(...incoming.items);
        current.nextCursor = incoming.nextCursor;
      },
      forceRefetch: ({ currentArg, previousArg }) => currentArg?.cursor !== previousArg?.cursor,
    }),

    getOrder: builder.query<OrderDto, string>({
      query: (id) => `orders/${encodeURIComponent(id)}`,
      providesTags: (_r, _e, id) => [{ type: "Order", id }],
    }),

    // ── كتابة ──────────────────────────────────────────────────────
    createOrder: builder.mutation<OrderDto, CreateOrderRequest>({
      query: (body) => ({
        url: "orders",
        method: "POST",
        body,
        headers: {
          // مفتاح idempotency: UUID جديد لكل عملية إرسال واحدة (5.2.5)
          "Idempotency-Key": crypto.randomUUID(),
        },
      }),
      invalidatesTags: [{ type: "Order", id: "LIST" }],   // ← القائمة هتتجلب تلقائيًا
    }),

    cancelOrder: builder.mutation<OrderDto, { id: string; reason: string }>({
      query: ({ id, reason }) => ({
        url: `orders/${encodeURIComponent(id)}/cancel`,
        method: "POST",
        body: { reason },
        headers: { "Idempotency-Key": crypto.randomUUID() },
      }),
      // ✅ تحديث متفائل: نظهر الإلغاء فورًا ونتراجع لو فشل الخادم
      async onQueryStarted({ id }, { dispatch, queryFulfilled }) {
        const patch = dispatch(
          shopApi.util.updateQueryData("getOrder", id, (draft) => {
            draft.status = "cancelled";
          }),
        );
        try {
          await queryFulfilled;
        } catch {
          patch.undo();          // rollback (8.1.4 ⑤)
        }
      },
      invalidatesTags: (_r, _e, { id }) => [{ type: "Order", id }, { type: "Order", id: "LIST" }],
    }),

    // ── مصادقة (نمط BFF) ───────────────────────────────────────────
    getMe: builder.query<{ isAuthenticated: boolean; name?: string; roles: string[] }, void>({
      query: () => "bff/user",
    }),
  }),
});

/**
 * ربط النتيجة بـApiError موحّد للـUI.
 * (RTK بيرجع { error } بـApiError بفضل baseQuery المخصص.)
 */
export type QueryError = ApiError;

export const {
  useGetOrdersQuery,
  useGetOrderQuery,
  useCreateOrderMutation,
  useCancelOrderMutation,
  useGetMeQuery,
} = shopApi;
'''},
        {"type": "code", "lang": "javascript", "title": "src/features/orders/OrdersPage.tsx — استخدام الـhooks + الحالات + التحميل التدريجي", "filename": "src/features/orders/OrdersPage.tsx", "code": r'''import { useState } from "react";
import { useGetOrdersQuery, useCancelOrderMutation } from "../../api/shopApi";
import type { ApiError } from "../../api/types";
import { useDebounced } from "../../hooks/useDebounced";

export function OrdersPage() {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState<string | undefined>();
  const debouncedQuery = useDebounced(query, 300);

  // نفس الـhook بيدير: كاش + إعادة جلب عند الرجوع + إلغاء عند تغيير المفاتيح
  const { data, error, isLoading, isFetching, refetch } = useGetOrdersQuery({
    q: debouncedQuery,
    cursor,
  });

  const [cancelOrder, { isLoading: isCancelling, error: cancelError }] = useCancelOrderMutation();

  const apiError = (error ?? cancelError) as ApiError | undefined;

  return (
    <section className="grid gap-4" aria-busy={isLoading || isFetching}>
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">الطلبات</h1>
        <button type="button" className="rounded-md border px-3 py-1.5 text-sm"
                onClick={() => void refetch()} disabled={isFetching}>
          {isFetching ? "جارٍ التحديث…" : "تحديث"}
        </button>
      </header>

      <label className="grid gap-1">
        <span className="text-sm font-medium">بحث</span>
        <input type="search" value={query} onChange={(e) => { setQuery(e.target.value); setCursor(undefined); }}
               placeholder="رقم الطلب أو اسم العميل"
               className="rounded-md border px-3 py-2 text-sm" />
      </label>

      <p className="sr-only" role="status" aria-live="polite">
        {isLoading ? "جارٍ تحميل الطلبات" : data ? `${data.items.length} طلبًا معروضًا` : ""}
      </p>

      {/* ① أول تحميل: skeleton */}
      {isLoading ? (
        <ul className="grid gap-2" aria-hidden="true">
          {[0, 1, 2, 3].map((i) => (
            <li key={i} className="card h-16 animate-pulse bg-gray-100" />
          ))}
        </ul>
      ) : null}

      {/* ② خطأ */}
      {apiError ? (
        <div className="card grid gap-2 border-danger/30 bg-danger/5 py-6 text-center" role="alert">
          <p className="font-medium text-danger">{apiError.title}</p>
          {apiError.detail ? <p className="text-sm text-ink-muted">{apiError.detail}</p> : null}
          <button type="button" className="btn-primary mx-auto" onClick={() => void refetch()}>
            إعادة المحاولة
          </button>
          {apiError.correlationId ? (
            <p className="text-xs text-ink-muted">مرجع: <code dir="ltr">{apiError.correlationId}</code></p>
          ) : null}
        </div>
      ) : null}

      {/* ③ فراغ */}
      {!isLoading && !apiError && data && data.items.length === 0 ? (
        <div className="card grid justify-items-center gap-2 py-10 text-center">
          <p className="font-medium">{debouncedQuery ? "لا نتائج مطابقة" : "لا طلبات بعد"}</p>
          {debouncedQuery ? (
            <button type="button" className="btn-primary mt-2" onClick={() => setQuery("")}>
              مسح البحث
            </button>
          ) : null}
        </div>
      ) : null}

      {/* ④ نجاح (مع إبقاء المحتوى أثناء إعادة الجلب) */}
      {data && data.items.length > 0 ? (
        <ul className={"grid gap-2 " + (isFetching ? "opacity-70" : "")}>
          {data.items.map((order) => (
            <li key={order.id} className="card flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate font-medium" dir="ltr">{order.id}</p>
                <p className="text-sm text-ink-muted">{order.status}</p>
              </div>
              <p className="tabular-nums text-sm" dir="ltr">{order.total} {order.currency}</p>
              <button
                type="button"
                className="rounded-md border px-3 py-1.5 text-sm"
                disabled={isCancelling || order.status === "cancelled"}
                onClick={() => void cancelOrder({ id: order.id, reason: "customer-request" })}
              >
                إلغاء
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {/* ⑤ تحميل المزيد (cursor) */}
      {data?.nextCursor ? (
        <button type="button" className="rounded-md border px-3 py-2 text-sm"
                disabled={isFetching}
                onClick={() => setCursor(data.nextCursor ?? undefined)}>
          {isFetching ? "جارٍ التحميل…" : "تحميل المزيد"}
        </button>
      ) : null}
    </section>
  );
}
'''},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ المصادقة: BFF أو OIDC في الـSPA — والفرق العملي"},
        {"type": "table", "caption": "الخياران — ماذا يعني كل واحد في كود React",
         "head": ["الجانب", "**BFF (موصى به)**", "**OIDC في الـSPA (PKCE)**"],
         "rows": [
             ["ما يحمله المتصفح", "**كوكي `HttpOnly` فقط** — صفر توكنات في JS", "access token قصير **في الذاكرة** + refresh في كوكي أو تجديد صامت"],
             ["مين بيعمل التبادل", "الخادم (confidential client) — بسر محفوظ", "المتصفح (public client) — بلا سر + PKCE"],
             ["الأثر عند XSS", "يسرق جلسة كوكي (محدودة/قابلة للإبطال) — **لا يستطيع قراءة التوكنات**", "يقدر يستخدم الـaccess token طول صلاحيته (وقد يصل للـrefresh لو مخزّن خطأ)"],
             ["CSRF", "مطلوب دفاع (SameSite + ترويسة `X-Csrf`)", "غير معرّض (لا كوكيز مصادقة)"],
             ["CORS", "لا (نفس الأصل)", "مطلوب إعداد على الـAPI + origins"],
             ["تجديد", "`POST /auth/refresh` (كوكي) — نسمّيه في `baseQuery`", "`oidc-client-ts`/`msal-browser` silent renew + تدوير"],
             ["الخروج", "RP-initiated logout من الخادم", "end session endpoint + مسح الحالة"],
             ["متى تختاره", "**أي منتج جاد وتملك الخادم**", "SPA بلا خادم خلفي · أو API مشترك بين عدة عملاء"],
         ]},
        {"type": "code", "lang": "javascript", "title": "auth/oidc.ts — OIDC في الـSPA بـPKCE (لما مفيش BFF) + التحذيرات", "filename": "src/auth/oidc.ts", "code": r'''import { UserManager, WebStorageStateStore, type User } from "oidc-client-ts";

/**
 * ⚠️ هذا النمط للضرورة فقط (SPA بلا خادم) — الموصى به هو BFF (8.1.2).
 * القواعد الأمنية:
 *   1) Authorization Code + PKCE فقط (لا implicit — RFC 9700).
 *   2) access token **في الذاكرة** لا localStorage (8.1.2 ①).
 *   3) refresh token: إما في كوكي HttpOnly من الخادم أو تجديد صامت + تدوير.
 *   4) state/nonce مفعّلان + تحقق من ID token بمكتبة مصانة.
 *   5) أقل scopes ممكنة + audience مقيد.
 */

const config = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY as string,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID as string,
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: window.location.origin,
  response_type: "code",
  scope: "openid profile shop.api",
  // PKCE: المكتبة بتولّد code_verifier/challenge تلقائيًا مع response_type=code
  // والحالة بتُخزَّن في sessionStorage (آمن للحالة، مش للتوكنات)
  userStore: new WebStorageStateStore({ store: window.sessionStorage }),
  automaticSilentRenew: true,
  // access token: مدة قصيرة من المزود (5–15 دقيقة)
};

export const userManager = new UserManager(config);

/** التوكن في الذاكرة فقط — يُفقد عند إعادة التحميل (وهذا مقصود). */
let inMemoryAccessToken: string | null = null;

export async function initAuth(): Promise<User | null> {
  // معالجة الـcallback: المكتبة بتقرأ code من الـURL وتتبادله بـPKCE
  const user = await userManager.signinRedirectCallback().catch(() => null);
  if (user) {
    inMemoryAccessToken = user.access_token;
    // تنظيف الـURL بعد المعالجة
    window.history.replaceState({}, document.title, "/");
    return user;
  }

  const existing = await userManager.getUser();
  if (existing && !existing.expired) {
    inMemoryAccessToken = existing.access_token;
    return existing;
  }

  return null;
}

/** تجديد صامت: المكتبة بتستخدم refresh token/iframe حسب إعداد المزود. */
userManager.events.addSilentRenewError((err) => {
  console.warn("فشل التجديد الصامت — سيُطلب تسجيل الدخول", err);
  inMemoryAccessToken = null;
});

userManager.events.addUserLoaded((user) => {
  inMemoryAccessToken = user.access_token;
});

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export async function login(): Promise<void> {
  await userManager.signinRedirect();     // مع PKCE + state + nonce
}

export async function logout(): Promise<void> {
  inMemoryAccessToken = null;
  await userManager.signoutRedirect();
}

/** يُستخدم في interceptor: يجيب توكنًا صالحًا أو يعيد null. */
export async function getValidToken(): Promise<string | null> {
  const user = await userManager.getUser();
  if (!user || user.expired) return null;
  inMemoryAccessToken = user.access_token;
  return inMemoryAccessToken;
}
'''},
        {"type": "code", "lang": "javascript", "title": "auth/ProtectedRoute.tsx — حماية مسار (تجربة مستخدم، لا حماية بيانات)", "filename": "src/auth/ProtectedRoute.tsx", "code": r'''import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { useGetMeQuery } from "../api/shopApi";

/**
 * حماية مسار: تجربة مستخدم.
 * ⚠️ ليست حماية بيانات: في SPA كل الكود والحزم متاحة — والـAPI هو من يفرض الصلاحيات (7.2.3).
 */
export function ProtectedRoute({
  children,
  requiredRole,
}: {
  children: ReactNode;
  requiredRole?: string;
}) {
  const location = useLocation();
  const { data, isLoading } = useGetMeQuery();

  if (isLoading) {
    return (
      <div className="grid gap-2 p-6" aria-busy="true">
        <p className="sr-only" role="status">جارٍ التحقق من الجلسة</p>
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
      </div>
    );
  }

  if (!data?.isAuthenticated) {
    // نبعت المسار الحالي للرجوع إليه بعد الدخول (وتحقق الخادم من أنه نسبي!)
    const back = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/bff/login?returnUrl=${back}`} replace />;
  }

  if (requiredRole && !data.roles.includes(requiredRole)) {
    return (
      <div className="card grid gap-2 py-10 text-center" role="alert">
        <p className="font-medium">ليس لديك صلاحية لهذه الصفحة</p>
        <p className="text-sm text-ink-muted">تواصل مع مسؤول النظام لمنحك الدور المطلوب.</p>
      </div>
    );
  }

  return <>{children}</>;
}
'''},
        {"type": "callout", "kind": "danger", "title": "خمسة أخطاء مصادقة في تطبيقات React (كلها شائعة)",
         "md": "**① توكن في `localStorage`** — OWASP صريحة: لا. (8.1.2)\n**② حماية صفحة كأنها حماية بيانات** — المستخدم يقدر يستدعي الـAPI أو يعدّل الحالة في المتصفح؛ التفويض في الخادم.\n**③ `client_secret` في حزمة الـSPA** — أي سر في المتصفح مكشوف (وهو الحال أيضًا في أي `VITE_*`).\n**④ `open redirect` في `returnUrl`** — لازم تحقق (مسارات نسبية فقط) وإلا المهاجم يستخدم موقعك للتحويل لموقع خبيث؛ الكود في 8.1.2 بيعمل ده على الخادم.\n**⑤ الاعتماد على `exp` من غير تجديد** — التوكن بتخلص فجأة وكل الطلبات 401؛ لازم single-flight refresh + تسجيل خروج نظيف."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ الاختبار والقياس: إزاي تختبر طبقة بيانات"},
        {"type": "code", "lang": "javascript", "title": "src/features/orders/OrdersPage.test.tsx — MSW + طبقة البيانات الحقيقية", "filename": "src/features/orders/OrdersPage.test.tsx", "code": r'''import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { describe, expect, it, beforeAll, afterAll, beforeEach } from "vitest";
import { makeStore } from "../../app/store";
import { OrdersPage } from "./OrdersPage";

// MSW: نحاكي الشبكة على مستوى HTTP — فنختبر الكود الحقيقي (baseQuery + reauth + tags)
const server = setupServer(
  http.get("/api/orders", ({ request }) => {
    const url = new URL(request.url);
    if (url.searchParams.get("q") === "boom") {
      return HttpResponse.json(
        { title: "خطأ في الخادم", status: 500, traceId: "abc-123" },
        { status: 500, headers: { "Content-Type": "application/problem+json" } },
      );
    }
    return HttpResponse.json({
      items: [{ id: "ORD-1", status: "paid", total: "199.99", currency: "EGP", placedAt: "2026-10-22T10:00:00Z" }],
      nextCursor: null,
    });
  }),
);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
beforeEach(() => server.resetHandlers());

function renderWithStore() {
  return render(
    <Provider store={makeStore()}>
      <OrdersPage />
    </Provider>,
  );
}

describe("OrdersPage", () => {
  it("يعرض skeleton ثم الطلبات", async () => {
    renderWithStore();
    expect(document.querySelector("[aria-hidden=true]")).toBeTruthy();  // skeleton
    expect(await screen.findByText("ORD-1")).toBeInTheDocument();
  });

  it("يعرض خطأ 500 مع correlationId", async () => {
    renderWithStore();
    await userEvent.type(screen.getByRole("searchbox"), "boom");
    // debounce 300ms
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument(), { timeout: 2000 });
    expect(screen.getByText(/abc-123/)).toBeInTheDocument();
  });

  it("يستدعي الـAPI مرة واحدة بعد debounce", async () => {
    let calls = 0;
    server.events.on("request:start", ({ request }) => {
      if (new URL(request.url).pathname === "/api/orders") calls++;
    });
    renderWithStore();
    await userEvent.type(screen.getByRole("searchbox"), "abc");
    await waitFor(() => expect(calls).toBeGreaterThanOrEqual(2)); // أول جلب + بعد debounce
    expect(calls).toBeLessThanOrEqual(3);
  });
});
'''},
        {"type": "table", "caption": "ستة قرارات إعداد في طبقة البيانات — وأثر كل قرار",
         "head": ["الإعداد", "القيمة المقترحة", "الأثر", "متى تغيّرها"],
         "rows": [
             ["`staleTime`", "10–30 ثانية للقوائم الإدارية", "أقل = بيانات أحدث وأكثر طلبات", "بيانات حرجة (رصيد/مخزون): 0–5 ثوانٍ"],
             ["`gcTime` (TanStack) / `keepUnusedDataFor` (RTK)", "60–300 ثانية", "مدة بقاء الكاش بعد آخر استخدام", "قوائم كبيرة: قصّرها لتوفير الذاكرة"],
             ["`refetchOnReconnect`", "`true`", "تحديث بعد انقطاع الشبكة", "نادرًا ما تُعطّلها"],
             ["`refetchOnFocus`", "`false` (افتراضي RTK) / قابل للضبط", "تحديث عند الرجوع للتاب", "لوحات تشغيل: `true`"],
             ["`refetchInterval`", "بلا (أو 30–60 ثانية لحالة طلب)", "بيانات شبه حية بلا تعقيد WebSocket", "لا تستخدمه للحظات الحرجة — استخدم SSE/WebSocket (2.2.11)"],
             ["`polling` / retry", "RTK: بلا retry افتراضيًا للـmutations", "إعادة محاولة تلقائية للقراءات فقط (8.1.2)", "لا تعيد محاولة POST بلا idempotency"],
         ]},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ من OpenAPI إلى types: العقد الحي"},
        {"type": "code", "lang": "bash", "title": "توليد العميل من OpenAPI على كل تغيير (مع RTK codegen)", "filename": "scripts/gen-api.sh", "code": r'''#!/usr/bin/env bash
# يولّد أنواع/عميل من OpenAPI 3.1 (ASP.NET Core 10 — 2.1.1).
set -euo pipefail

API_URL="${API_URL:-http://localhost:8080}"
OUT="${OUT:-src/api/generated}"

echo "== 1) نزّل مستند OpenAPI =="
curl -fsS "$API_URL/openapi/v1.json" -o /tmp/openapi.json
jq -r '.openapi' /tmp/openapi.json | sed 's/^/version: /'

echo "== 2) طريقتان — اختر واحدة =="

# (أ) أنواع فقط — مع TanStack Query (أو fetch يدوي)
npx openapi-typescript /tmp/openapi.json -o "$OUT/schema.d.ts"

# (ب) عميل + hooks كاملة — مع RTK Query
#   ملف الإعداد: openapi.config.ts
cat > openapi.config.ts <<'EOF'
import type { ConfigFile } from "@rtk-query/codegen-openapi";

export default {
  schemaFile: "/tmp/openapi.json",
  apiFile: "../src/api/emptyApi.ts",
  apiImport: "emptyApi",
  outputFile: "../src/api/generated/shopApi.ts",
  exportName: "shopApi",
  hooks: true,
  filterEndpoints: (name) => !name.toLowerCase().includes("internal"),
} satisfies ConfigFile;
EOF
# npx @rtk-query/codegen-openapi openapi.config.ts

echo "== 3) افحص الفرق (يفشل الـCI لو العقد تغيّر والعملاء لم يُحدَّثوا) =="
git diff --exit-code -- "$OUT" \
  || { echo "✗ العقد تغيّر: شغّل gen-api.sh والتزم الناتج."; exit 1; }

echo "تم ✅"
'''},
        {"type": "callout", "kind": "note", "title": "قواعد العقد بين الواجهة والـAPI",
         "md": "**① مستند OpenAPI هو المرجع** — لو الـAPI تغيّر وما اتولّدتش الأنواع، الـCI يفشل (زي contract tests في 5.3.2 بس للأنواع).\n**② لا تعدّل الملفات المولّدة** — أي تعديل بيضيع في التوليد التالي. لو محتاج تعديل، عدّل الـAPI أو أضف wrapper.\n**③ الأنواع المولّدة لا تعني التحقق** — البيانات الحرجة لسه محتاجة تحقق وقت التشغيل (8.1.1 ③).\n**④ استبعد endpoints داخلية** (`filterEndpoints`) — العميل العام ما يحتاجش كل شيء، وده بيقلل الحزمة.\n**⑤ الأخطاء موحّدة**: كل endpoints بترجع ProblemDetails (2.2.3) — و`baseQuery` بتحولها لشكل واحد."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أختار بين TanStack Query وRTK Query بمعايير (الفلسفة · التوليد · tags · السياق) لا بالذوق.",
            "أكتب `baseQuery` مخصص يحوّل كل فشل إلى `ApiError` موحّد (شبكة/مهلة/HTTP/ProblemDetails).",
            "أنفّذ تجديد جلسة **single-flight** عند 401 داخل قاعدة الطبقة، مع منع إعادة المحاولة لطلبات المصادقة.",
            "أصمّم tags (`providesTags`/`invalidatesTags`) بحيث تتحدث القوائم والتفاصيل تلقائيًا بعد كل طفرة.",
            "أضيف تحديثًا متفائلًا مع `patch.undo()` عند الفشل.",
            "أربط الحالات الأربع (تحميل/خطأ/فراغ/نجاح) بمخرجات الـhook وأحافظ على المحتوى أثناء `isFetching`.",
            "أفرّق بين BFF (كوكي HttpOnly) وOIDC في الـSPA (PKCE + توكن في الذاكرة) وأعرف مخاطر كل واحد.",
            "أستخدم `oidc-client-ts`/`msal-browser` مع `<UserManager>` وقواعد: PKCE · بلا localStorage للتوكن · تدوير refresh.",
            "أكتب `ProtectedRoute` كتجربة مستخدم وأعرف أن الحماية الفعلية في الـAPI.",
            "أختبر طبقة البيانات بـMSW (شبكة محاكاة) وأتحقق من debounce/الأخطاء/correlationId.",
            "أولّد الأنواع/العميل من OpenAPI وأفشل الـCI إن لم تتزامن.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على طبقة البيانات والمصادقة.",
         "questions": [
             {"q": "ما وظيفة `baseQuery` المخصص في RTK Query؟",
              "options": ["تحديد شكل الـstore",
                          "تنفيذ الطلب لكل endpoints: ترويسات موحدة + تحويل كل فشل لـApiError + إمكانية تجديد الجلسة وإعادة المحاولة",
                          "توليد hooks",
                          "إدارة tags"],
              "answer": 1,
              "explain": "هو الطبقة اللي كل endpoint بتمر عليها — فأفضل مكان لـ: كوكي credentials · ترويسة CSRF · تحويل ProblemDetails · single-flight refresh على 401 · ومنع حلقات إعادة المحاولة. وده اللي بيخلي كل الفشل بشكل واحد في الـUI."},
             {"q": "لماذا `providesTags` و`invalidatesTags` مهمة؟",
              "options": ["مهام إضافية للـreducers",
                          "بتربط endpoints القراءة بالكتابة فتتجلب القوائم/التفاصيل تلقائيًا بعد أي طفرة — تمنع «الواجهة مش بتتحدث»",
                          "لتقليل حجم الحزمة",
                          "بديل للكاش"],
              "answer": 1,
              "explain": "بدون tags، لازم تنادي refetch يدويًا في كل مكان وأي نسيان = بيانات قديمة. tags بتبني شبكة علاقات بين البيانات، فأي mutation بتعلن تأثرها وتعيد الجلب تلقائيًا (ونفس الفكرة في TanStack بـ`invalidateQueries`)."},
             {"q": "المستخدم بيستخدم نمط BFF — ما الذي يُخزَّن في المتصفح؟",
              "options": ["access token في localStorage", "كوكي جلسة HttpOnly فقط", "refresh token في sessionStorage", "التوكنات في IndexedDB"],
              "answer": 1,
              "explain": "BFF بيرجّع كوكي HttpOnly فقط، والتوكنات في الخادم. أي سكربت (XSS) ما يقدرش يقرأ الكوكي — فأثره محدود، والـCSRF بيتعالج بـSameSite + ترويسة مخصصة."},
             {"q": "SPA بلا خادم خلفي: أين يوضع access token؟",
              "options": ["localStorage", "sessionStorage", "في الذاكرة (متغير/closure) مع تجديد صامت/تدوير refresh", "في كوكي غير HttpOnly"],
              "answer": 2,
              "explain": "التوصية: access token في الذاكرة فقط، وrefresh token في كوكي HttpOnly من الخادم أو بالتدوير مع التجديد الصامت. localStorage مرفوض (8.1.2)، وسنقبل أن التحديث الكامل للصفحة يفقد الـaccess (ويُستعاد بالتجديد)."},
             {"q": "ما دور `ProtectedRoute` في React؟",
              "options": ["حماية بيانات المستخدم",
                          "تجربة مستخدم (تحويل/رسالة) — والتفويض الحقيقي على الـAPI",
                          "تشفير الطلبات",
                          "إدارة التوكنات"],
              "answer": 1,
              "explain": "المستخدم يقدر يعدّل الحالة في المتصفح أو يستدعي الـAPI مباشرة. الحماية في الخادم: policies + فحص ملكية (2.2.1/7.2.3) + اختبارات (7.2.4). الواجهة بتخفي فقط."},
             {"q": "أفضل إعداد لبيانات قائمة إدارية بتتغير بشكل متقطع؟",
              "options": ["`staleTime: 0` و`refetchInterval: 1s`",
                          "`staleTime` 10–30ث · و`refetchOnReconnect: true` · وتحديث يدوي/بعد الطفرات",
                          "بلا كاش",
                          "كاش أبدي"],
              "answer": 1,
              "explain": "البيانات الإدارية المتقطعة التغير لا تحتاج polling كل ثانية (حمل بلا فائدة)، لكن تحتاج كاشًا قصيرًا + إعادة جلب بعد الطفرات وعند عودة الشبكة. للحظات الحرجة استخدم SSE/WebSocket (2.2.11)."},
             {"q": "أضفت `Idempotency-Key: crypto.randomUUID()` في mutation إنشاء. ما الفائدة؟",
              "options": ["تسريع الطلب",
                          "إعادة المحاولة الآمنة: لو الطلب اتنفذ فعلًا ولم يرجع الرد، الخادم ما ينشئش سجلًا مكررًا (5.2.5)",
                          "تشفير الجسم",
                          "منع CSRF"],
              "answer": 1,
              "explain": "الـkey بيثبت هوية العملية — فالخادم بيحفظ النتيجة ويُرجعها لو نفس الـkey تكرر. من غيرها، إعادة المحاولة (شبكة/انقطاع/مستخدم بيضغط تاني) بتعمل طلبين. لاحظ: لازم يتولد **لكل عملية** لا لكل طلب/رسمة."},
             {"q": "MSW في اختبارات طبقة البيانات — ليه أفضل من mock للدوال؟",
              "options": ["أسرع دائمًا",
                          "لأنه يحاكي الشبكة فعليًا فتختبر baseQuery والأخطاء والـtags والـreauth الحقيقيين، لا دوالًا موهومة",
                          "لأنه إلزامي مع RTK",
                          "لأنه يقلل حجم الحزمة"],
              "answer": 1,
              "explain": "لو موّكت `fetch` أو دالة الجلب فقط، أنت بتختبر الوهم — ومش هتكشف إن `baseQuery` بيعيد المحاولة غلط أو إن الخطأ مش متحول. MSW بيقاطع على مستوى HTTP فيمر الكود الحقيقي بكل طبقاته."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "طبقة بيانات كاملة + مصادقة صحيحة.",
         "items": [
            {"id": "s8-m2-l4-t1",
             "title": "مهمة 1: طبقة بيانات واحدة تعمل مع الـAPI بتاعك",
             "md": "نفّذ `baseQuery` + `createApi` (RTK) أو `queryClient` + hooks (TanStack) لمشروعك: تحويل أخطاء موحّد · single-flight refresh · tags/إبطال · تحديث متفائل واحد · ودمج صفحات للـcursor. اربطها بصفحة الطلبات واستبدل الـfetch اليدوي كله.",
             "criteria": [
                 "`baseQuery` واحد يحوّل: شبكة/مهلة → `ApiError{status:0}` · HTTP → ProblemDetails (`title`/`detail`/`traceId`/`errors`) · ويستخدم `X-Csrf` + `credentials: include`.",
                 "تجديد جلسة **single-flight** عند 401 (3 طلبات متوازية → تجديد واحد) + **منع** إعادة المحاولة على `/auth/*`.",
                 "**≥ 4 endpoints**: قائمة (cursor) · تفاصيل · إنشاء (بـ`Idempotency-Key`) · إلغاء (بمتفائل + `undo`).",
                 "tags أو مفاتيح إبطال: بعد الإنشاء/الإلغاء، القائمة والتفاصيل بتتحدث **تلقائيًا** (بدليل: لقطة/سجل قبل وبعد).",
                 "الصفحة تستخدم `isLoading` (أول مرة) و`isFetching` (إعادة جلب مع إبقاء المحتوى) وتغطي الحالات الأربع + `correlationId` في الخطأ.",
                 "**صفر `fetch`** خارج `baseQuery`/طبقة الـAPI (فحص grep).",
                 "**≥ 5 اختبارات MSW**: نجاح · 403 · 500 مع traceId · 429 + `Retry-After` · إلغاء طلب عند تغيير البحث.",
                 "قرار مكتوب: TanStack أم RTK، وليه (بناءً على جدول الدرس + حالة فريقك).",
             ],
             "hint": "لو اخترت TanStack: `queryKey` لازم يشمل كل المدخلات (`['orders', {q, cursor}]`) + `queryFn` ياخد `signal` من الـcontext ويمرره لـfetch (إلغاء تلقائي). وللـsingle-flight استخدم promise مشترك (زي 8.1.2). ولـ`merge` في RTK: انتبه إن `serializeQueryArgs` لازم يستثني الـcursor وإلا كل صفحة بتاخد كاش منفصل. ولو عايز تشوف الطلبات: RTK DevTools أو `react-query-devtools`.",
             "solution": "النتائج النموذجية: أكبر تحسن هو اختفاء `useEffect` الجلب اليدوي المكرر في كل صفحة (والتكرار بين الصفحات بينزل من ~60 سطرًا لكل صفحة إلى ~5). ثاني أكبر مكسب: tags بتمنع «الواجهة القديمة بعد الحفظ» بدون أي refetch يدوي. أصعب جزء: الـsingle-flight — أول محاولة بتدي 3 تجديدات متوازية ومستخدم مسجّل خروج عشوائيًا (لأن التدوير بيبطل التوكنات) وقاعدة 8.1.2 بتحلها. وفي الاختبارات: MSW بيخليك تكتشف إن `baseQuery` ما كانش بيحوّل `TIMEOUT_ERROR` — فالصفحة كانت بتعرض «غير معروف». النتيجة: طبقة واحدة، ~200 سطر، تغطي كل التطبيق، و5 اختبارات تعدي.",
             "resources": [
                 "https://redux-toolkit.js.org/rtk-query/overview",
                 "https://redux-toolkit.js.org/rtk-query/usage/automated-refetching",
                 "https://tanstack.com/query/latest/docs/framework/react/overview",
                 "https://mswjs.io/docs/",
                 "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/openapi",
             ]},
            {"id": "s8-m2-l4-t2",
             "title": "مهمة 2: مصادقة كاملة (BFF أو SPA) + حماية + اختبارات",
             "md": "نفّذ المصادقة: إما **BFF** (8.1.2) واستهلاكه من React (كوكي فقط + `/bff/user` + `/bff/login` + logout) أو **OIDC في الـSPA** (PKCE + توكن في الذاكرة + تجديد صامت) لو مفيش خادم تملكه. وأضف `ProtectedRoute` + اختبارات.",
             "criteria": [
                 "**قرار مكتوب**: النمط المختار · لماذا · ما المخاطرة المقبولة · وكيف يُدار التجديد/الخروج.",
                 "في BFF: `credentials: include` فقط · لا توكنات في JS · `/bff/user` يرجع `isAuthenticated/name/roles` فقط · تسجيل خروج RP-initiated.",
                 "في SPA: `oidc-client-ts`/`msal-browser` + `response_type=code` + PKCE + state/nonce · access token **في الذاكرة** (لا `localStorage`) · تجديد صامت/تدوير · مسح شامل عند الخروج.",
                 "`ProtectedRoute` (+ حماية دور) مع حالة تحميل وتجربة واضحة + `returnUrl` **يُتحقق منه على الخادم** (مسارات نسبية).",
                 "**منع** أي سر في الحزمة: فحص وجود `client_secret` أو `api_key` داخل `src/` يرجع فاضي + مراجعة متغيرات `VITE_*` (كلها مكشوفة).",
                 "اختبارات MSW: مستخدم غير مصادَق → تحويل للدخول · مصادَق بلا دور → رسالة صلاحية · مصادَق بالدور → المحتوى · 401 أثناء الجلسة → تجديد ثم نجاح · فشل التجديد → تحويل.",
                 "تحقق يدوي مُوثّق: تسجيل دخول · تحديث صفحة (انتهاء access في SPA/استمرار جلسة في BFF) · انتهاء الجلسة بعد خمول · خروج.",
                 "قائمة تدقيق من 8.1.2 (تخزين التوكن/الالتفاف على redirect/تسجيل التوكنات) — كل بند: مطبّق أم لا ولماذا.",
             ],
             "hint": "للتجربة السريعة في SPA: مزود محلي (Keycloak/Zitadel) بـ`docker compose` (2.2.8) أو Entra dev tenant. لو استخدمت BFF، اختبار «تحديث الصفحة» هو أهم اختبار: في BFF الجلسة مستمرة (كوكي)، وفي SPA الـaccess في الذاكرة بيضيع — فمحتاج `signinSilent` أو تجديد عند الإقلاع (ودي أهم فرق تجربة). واختبر حالة انتهاء الجلسة أثناء استخدام التطبيق (بدون refresh): 401 → تجديد → إعادة الطلب.",
             "solution": "النتائج النموذجية: BFF أبسط تجربة (لا إدارة توكنات في الواجهة، ولا CORS، وتحديث الصفحة أوتوماتيك) وأقل مخاطرة عند XSS — والثمن: تحتاج خادمًا يملك الجلسة (وأنت بالفعل تملكه في مشروع .NET). نمط SPA (PKCE) مرن أكثر لكنه يحمّل الواجهة مسؤولية التجديد ويمنحك CORS وإدارة حالة مصادقة أكثر. والأخطاء اللي بتظهر غالبًا: `returnUrl` مفتوح بلا تحقق (خطر open redirect)، ونسيان `X-Csrf` على POST فيبدأ كل شيء بـ403، و`localStorage` لتوكن «مؤقتًا» — اللي بيرجع في المراجعة. النتيجة المطلوبة: **كل حالة مصادقة عندها اختبار**، ومفيش ولا سر في `src/`، وسيناريو الخروج يمسح كل شيء.",
             "resources": [
                 "https://github.com/authts/oidc-client-ts",
                 "https://learn.microsoft.com/entra/identity-platform/v2-protocols-oidc",
                 "https://datatracker.ietf.org/doc/html/rfc9700",
                 "https://oauth.net/2/browser-based-apps/",
                 "https://mswjs.io/docs/",
                 "https://learn.microsoft.com/aspnet/core/security/authentication/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "RTK Query: نظرة عامة", "url": "https://redux-toolkit.js.org/rtk-query/overview"},
            {"label": "RTK Query: الجلب التلقائي بـtags", "url": "https://redux-toolkit.js.org/rtk-query/usage/automated-refetching"},
            {"label": "RTK Query: codegen من OpenAPI", "url": "https://redux-toolkit.js.org/rtk-query/usage/code-generation"},
            {"label": "TanStack Query v5", "url": "https://tanstack.com/query/latest/docs/framework/react/overview"},
            {"label": "oidc-client-ts", "url": "https://github.com/authts/oidc-client-ts"},
            {"label": "MSW: محاكاة الشبكة في الاختبارات", "url": "https://mswjs.io/docs/"},
            {"label": "RFC 9700: أفضل ممارسات OAuth", "url": "https://datatracker.ietf.org/doc/html/rfc9700"},
            {"label": "ASP.NET Core: OpenAPI", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/openapi"},
        ]},
    ],
}

LESSONS_S8_H = [_L4]
