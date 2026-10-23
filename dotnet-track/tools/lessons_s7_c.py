# -*- coding: utf-8 -*-
"""Stage 7 module 1 (part C): s7-m1-l5 (SLOs والتنبيهات بدون ضجيج)."""

TODAY = "2026-10-22"

_L5 = {
    "id": "s7-m1-l5",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "لو كل حاجة مهمة، مفيش حاجة مهمة — وده بالظبط تعريف **إرهاق التنبيهات**: تنبيهات كتير فمحدش بيقرا. الحل مش تنبيهات أقل بس، بل **تنبيهات على الأعراض مبنية على هدف رقمي (SLO)**: لما «ميزانية الأخطاء» بتتحرق بسرعة → page؛ لما بتتحرق ببطء → ticket؛ وغير كده → مفيش تنبيه أصلًا. في الدرس ده: SLI/SLO/SLA · إزاي تختار SLI من مقاييسك الحقيقية · تحديد هدف واقعي بالأرقام · **error budget وسياساته** · تنبيهات multi-window multi-burn-rate بأرقام Google SRE Workbook · وAlertmanager للتجميع والكبت والصمت."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "SLI (مؤشر)", "def": "**قياس فعلي** لجودة الخدمة من منظور المستخدم: نسبة الطلبات الناجحة · نسبة الطلبات أسرع من 300ms · زمن معالجة الرسالة. لازم يُحسب من مقاييس موجودة (7.1.4)."},
            {"term": "SLO (هدف)", "def": "**هدف داخلي** على الـSLI: «99.9% من الطلبات تنجح خلال 30 يومًا». هو اللي بيحكم التنبيهات والقرارات."},
            {"term": "SLA (اتفاقية)", "def": "**عقد مع العميل** فيه تعويض عند المخالفة. دايمًا أضعف من الـSLO (مثال: SLA 99.5% مع SLO 99.9%) عشان يكون فيه هامش قبل الالتزام القانوني."},
            {"term": "Error budget", "def": "الكمية المسموح بها من الفشل: لو SLO = 99.9% لفترة 30 يومًا، الميزانية = 0.1% ≈ **43.2 دقيقة** أو 1,000 طلب فاشل من مليون."},
            {"term": "Burn rate", "def": "سرعة استهلاك الميزانية نسبةً للسرعة «الطبيعية»: 14.4× يعني بتستهلك 14.4 ضعف المعدل المسموح (يعني الميزانية الشهرية تخلص في ~يومين)."},
            {"term": "Multi-window", "def": "ربط نافذة طويلة (1h) بنافذة قصيرة (5m): الطويلة بتأكد إن فيه استهلاك حقيقي، والقصيرة بتأكد إنه **لسه بيحصل دلوقتي** — يعني التنبيه بيختفي دقائق بعد الإصلاح بدل ساعات."},
            {"term": "تنبيه على الأعراض", "def": "تنبيه لما المستخدم متأثر (نسبة فشل · زمن استجابة · ميزانية محترقة) — مش لما CPU عالي أو الـheap كبر (دي **أسباب** تُفحص لا تُنبَّه)."},
            {"term": "Page مقابل Ticket", "def": "**Page** = صحّي حد دلوقتي (يحتاج تدخل فوري). **Ticket** = شغل في ساعات العمل (مشكلة حقيقية بس مش طارئة). أي تنبيه مش page ولا ticket → احذفه."},
            {"term": "Grouping / Inhibition / Silence", "def": "أدوات Alertmanager: **تجميع** التنبيهات المتشابهة في إشعار واحد · **كبت** التنبيهات الفرعية لما السبب الرئيسي مُنبَّه · **صمت** أثناء الصيانة المخطط لها."},
            {"term": "Ack (إقرار)", "def": "تأكيد إن حد شاف التنبيه وبيتعامل معه — بيوقف التصعيد. بدونه التنبيه بيتكرر أو بيصعّد لحد تاني."},
            {"term": "سياسة ميزانية الأخطاء", "def": "قرار مكتوب: لما الميزانية تخلص (أو تقارب)، إيه اللي بيتوقف (نشر ميزات جديدة) وإيه اللي بيتركز عليه (موثوقية) — وليه ده قرار منتج مش هندسي فقط."},
            {"term": "SLO قابل للمراجعة", "def": "الهدف بيتراجع كل ربع سنة بالأرقام الفعلية: لو بتحققه دايمًا بسهولة → ارفعه أو وفّر تكلفة؛ لو بتكسره دايمًا → إما أصلح النظام أو صحّح الهدف."},
        ]},

        # ── 1
        {"type": "heading", "level": 2, "text": "① SLI/SLO/SLA بكلمات بسيطة — وإزاي تختار SLI من مقاييسك"},
        {"type": "table", "caption": "أنواع الـSLI — والصيغة من مقاييس 7.1.4 مباشرة",
         "head": ["نوع الـSLI", "السؤال", "الصيغة (PromQL على مقاييسنا)", "مثال هدف"],
         "rows": [
             ["**التوافر (Availability)**", "ما نسبة الطلبات اللي نجحت؟",
              "`1 - (rate(..._count{http_response_status_code=~\"5..\"}[5m]) / rate(..._count[5m]))`",
              "99.9% من الطلبات تنجح"],
             ["**الزمن (Latency)**", "ما نسبة الطلبات الأسرع من حد؟",
              "`sum(rate(..._bucket{le=\"0.3\"}[5m])) / sum(rate(..._count[5m]))`",
              "95% من الطلبات تحت 300ms"],
             ["**الجودة (Quality)**", "هل النتيجة كاملة/صحيحة (بدون degradation)؟",
              "نسبة الاستجابات الكاملة مقابل المخفّضة (من مقياس أعمال)",
              "99% من الاستجابات كاملة"],
             ["**الحداثة (Freshness)**", "البيانات حديثة قد إيه؟",
              "`max(shop_outbox_oldest_age_seconds) < 60` أو عمر أحدث سجل/تحديث",
              "أقدم رسالة غير معالجة < 60 ثانية"],
             ["**الصحة (Correctness)**", "هل المعالجة صحت؟",
              "عدد الرسائل في DLQ مقابل المعالجة · فرق التسويات",
              "DLQ = 0 لمدة 24 ساعة"],
             ["**الإنتاجية (Throughput)**", "هل بنلحق الحمل؟",
              "`sum(rate(shop_orders_placed_total[5m]))` مقابل السعة المخططة",
              "200 طلب/ثانية بلا تجاوز p95"],
             ["**التغطية (Coverage)**", "هل الخدمة متاحة لكل العملاء؟",
              "نسبة المناطق/النسخ السليمة (`up == 1`)",
              "100% من النسخ سليمة لمدة 5 دقائق"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قواعد اختيار SLI (تلات قواعد تكفي)",
         "md": "**① قِسه من منظور المستخدم** (عند الـgateway/الـingress، مش داخل الخدمة) — لأن المستخدم بيحكم على التجربة الكلية. **② اختار SLI واحدًا أساسيًا لكل خدمة** وواحد ثانوي (مثلًا: توافر + زمن) — أكتر من كده بيضيع التركيز. **③ لازم يكون محسوبًا من مقياس موجود فعلًا** — لو محتاج كود جديد، اكتبه (7.1.1/7.1.2) قبل ما تحلم بهدف. وأهم سؤال: **هل الرقم ده بيتغير لما المستخدم يتأثر؟** لو لأ، فهو مقياس صحة مش SLI."},

        # ── 2
        {"type": "heading", "level": 2, "text": "② تحديد الهدف: الأرقام اللي بتقرر"},
        {"type": "table", "caption": "فترة 30 يومًا — كم خطأ مسموح؟ (احسبها بنفسك: 43,200 دقيقة)",
         "head": ["SLO", "الفشل المسموح", "بالزمن (30 يومًا)", "من مليون طلب", "التكلفة/التعقيد التقريبي", "لمين"],
         "rows": [
             ["99%", "1%", "**7.2 ساعات**", "10,000", "منخفضة جدًا (نسخة واحدة، بلا HA)", "أدوات داخلية · dashboards · dev"],
             ["99.5%", "0.5%", "**3.6 ساعات**", "5,000", "منخفضة (نسخة واحدة + نشر آمن)", "تطبيقات داخلية · مواقع صغيرة"],
             ["**99.9%**", "0.1%", "**43.2 دقيقة**", "1,000", "متوسطة (نسخة واحدة على الأقل + canary + مراقبة)", "**الافتراضي المعقول لمعظم الخدمات**"],
             ["99.95%", "0.05%", "**21.6 دقيقة**", "500", "أعلى (HA · منطقتان · اختبارات فشل)", "خدمة إيرادية بمستخدمين دائمين"],
             ["99.99%", "0.01%", "**4.3 دقائق**", "100", "عالية جدًا (multi-region · failover تلقائي · on-call 24/7)", "دفع · بنوك · بنى حرجة"],
         ]},
        {"type": "callout", "kind": "warn", "title": "ثلاث حقائق قبل ما تختار رقمًا",
         "md": "**① كل «9» إضافية بتكلف أضعافًا** (HA · multi-region · on-call · اختبارات فشل) — من 99.9% لـ99.99% الفرق 10 أضعاف في ميزانية الخطأ، والتكلفة مش خطية. **② التبعيات بتحدد سقفك**: لو قاعدة البيانات المُدارة SLA بتاعها 99.99% ومزوّد الدفع 99.9%، فـ99.99% عندك وهم. **احسب**: توافر السلسلة ≈ حاصل ضرب توافر المكونات المطلوبة. **③ SLO أضعف من SLA وأقوى من الواقع**: الـSLO هدف داخلي بيخلي التنبيه ييجي **قبل** ما تكسر العقد، ولو الـSLO أعلى من الواقع بكثير هتكسره دايمًا فمحدش هياخده بجد."},

        # ── 3
        {"type": "heading", "level": 2, "text": "③ Error budget: الرقم اللي بيحوّل النقاش لقرار"},
        {"type": "code", "lang": "text", "title": "docs/slo-orders.md — حساب وميزانية وسياسة", "filename": "docs/slo-orders.md", "code": r'''# SLO لخدمة orders

## 1) الـSLI
التوافر: نسبة طلبات HTTP اللي **مش 5xx**، مقاسة عند الـingress (تجربة المستخدم).
الصيغة:
    success_ratio = 1 - ( sum(rate(http_server_request_duration_seconds_count{
                        service="orders-api", http_response_status_code=~"5.."}[5m]))
                      / sum(rate(http_server_request_duration_seconds_count{
                        service="orders-api"}[5m])) )

ثانوي (الزمن): 95% من الطلبات تحت 300ms
    sum(rate(..._bucket{le="0.3"}[5m])) / sum(rate(..._count[5m])) >= 0.95

## 2) الـSLO والفترة
SLO = 99.9% · الفترة = 30 يومًا متدحرجة (rolling) — مش شهر تقويمي.
الفشل المسموح = 0.1% = 43.2 دقيقة ≈ 1,000 طلب من كل مليون.

## 3) ميزانية الخطأ (error budget)
الميزانية الكلية للفترة = 0.001 × إجمالي الطلبات
المستهلك حتى الآن       = 0.001 × إجمالي الطلبات − الطلبات الفاشلة
نسبة النجاح الفعلية      = 1 − نسبة الفشل على 30 يومًا
الميزانية المتبقية (%)   = (نسبة النجاح الفعلية − SLO) ÷ (1 − SLO) × 100
                           (لو الناتج سالب → الميزانية مستهلكة بالكامل)

استعلامات جاهزة (30d):
    # نسبة النجاح على 30 يومًا
    1 - (
      sum(increase(http_server_request_duration_seconds_count{service="orders-api",
                   http_response_status_code=~"5.."}[30d]))
      /
      sum(increase(http_server_request_duration_seconds_count{service="orders-api"}[30d]))
    )
    # الميزانية المتبقية كنسبة (0 = مستهلكة، 1 = كاملة)
    (<نسبة النجاح أعلاه> - 0.999) / 0.001

## 4) سياسة الميزانية (قرار مكتوب — يوقع عليه مالك الخدمة)
| المتبقي من الميزانية | القرار |
|---|---|
| فوق 50% | نشر عادي · تجربة (canary أسرع · ميزات أكثر جرأة) |
| 25–50% | نشر عادي مع canary أطول ومراقبة أقدم |
| 10–25% | **تجميد الميزات غير الحرجة** · التركيز على إصلاح الأسباب المتكررة |
| تحت 10% | **وقف النشر غير الأمني** · خطة موثوقية (أسبوع) · مراجعة SLO |
| مستهلكة بالكامل | حادث موثّق (postmortem) + إجراء وقائي + إبلاغ أصحاب المصلحة |

## 5) المراجعة
كل ربع سنة: قارن SLO بالواقع.
  • حققناه بسهولة 3 شهور؟ → ارفعه أو وفّر تكلفة (HA زائدة؟)
  • كسرناه مرتين+؟ → خطة موثوقية أو تصحيح الهدف (مش تقليله لإخفاء المشكلة).
آخر مراجعة: 2026-10-22 · المالك: …
'''},

        # ── 4) التنبيهات
        {"type": "heading", "level": 2, "text": "④ التنبيهات: الأعراض ومعدل الاحتراق (الأرقام من Google SRE Workbook)"},
        {"type": "table", "caption": "multi-window multi-burn-rate — الثلاث مستويات القياسية (لـSLO 99.9% وفترة 30 يومًا)",
         "head": ["الخطورة", "النافذة الطويلة", "النافذة القصيرة", "Burn rate", "الميزانية المستهلكة عند الإطلاق", "الإشعار"],
         "rows": [
             ["**حرج**", "1 ساعة", "5 دقائق", "**14.4×**", "2% (يعني الميزانية تخلص في ~يومين)", "**Page** — صحّي حد"],
             ["**متوسط**", "6 ساعات", "30 دقيقة", "**6×**", "5% (تخلص في ~5 أيام)", "**Page** (أو تنبيه عاجل)"],
             ["**بطيء**", "3 أيام", "6 ساعات", "**1×**", "10%", "**Ticket** — ساعات العمل"],
         ]},
        {"type": "code", "lang": "text", "title": "الحساب: من أين جاءت 14.4؟", "filename": "docs/burn-rate-math.txt", "code": r'''الحساب (لأي SLO وأي نافذة):

   burn_rate = (نسبة الميزانية المستهلكة × طول الفترة بالدقائق) ÷ طول النافذة بالدقائق

الفترة = 30 يومًا = 43,200 دقيقة.

  ① 2% في ساعة واحدة:
      (0.02 × 43,200) ÷ 60 = 864 ÷ 60 = 14.4×
      → المعنى: لو استهلكنا 2% كل ساعة، الميزانية كلها (100%) تخلص في 50 ساعة ≈ يومين.

  ② 5% في 6 ساعات:
      (0.05 × 43,200) ÷ 360 = 2,160 ÷ 360 = 6×

  ③ 10% في 3 أيام:
      (0.10 × 43,200) ÷ 4,320 = 4,320 ÷ 4,320 = 1×   (أي المعدل «الطبيعي» المسموح)

القاعدة العامة للعتبة في PromQL (مقارنة بنسبة الفشل المقاسة):

      عتبة = burn_rate × (1 − SLO)

  لـSLO 99.9%  (1 − SLO = 0.001):
      الحرج  = 14.4 × 0.001 = 0.0144  → 1.44% نسبة فشل
      المتوسط = 6   × 0.001 = 0.0060  → 0.60%
      البطيء  = 1   × 0.001 = 0.0010  → 0.10%

  لـSLO 99.5%  (1 − SLO = 0.005):
      الحرج  = 14.4 × 0.005 = 0.072   → 7.2% نسبة فشل
      (يعني النظام الأضعف هدفًا بيتحمل نسبة فشل أعلى قبل ما يُنبَّه — وده منطقي)

لماذا نافذتان؟
  • الطويلة وحدها: التنبيه يفضل شغال ساعات بعد الإصلاح (لأن النافذة لسه فيها البيانات القديمة).
  • القصيرة وحدها: ضجيج — دقيقة سيئة واحدة تطلق page.
  • الاثنان معًا (AND): نطلق فقط لو فيه استهلاك حقيقي **ولسه بيحصل دلوقتي** →
    التنبيه بيختفي خلال دقائق بعد الإصلاح (النافذة القصيرة بتفضل).
'''},
        {"type": "code", "lang": "yaml", "title": "observability/slo-rules.yml — القواعد جاهزة للنسخ", "filename": "observability/slo-rules.yml", "code": r'''groups:
  # ── 1) SLI محسوب مسبقًا (recording rules) لكل نافذة محتاجينها ──
  - name: slo-recording
    interval: 30s
    rules:
      # نسبة الفشل لكل خدمة (بدون تقسيم على المسارات — الـSLO على الخدمة كلها)
      - record: service:sli_error:ratio_rate5m
        expr: |
          sum by (service) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[5m]))
          /
          sum by (service) (
            rate(http_server_request_duration_seconds_count[5m]))

      - record: service:sli_error:ratio_rate30m
        expr: |
          sum by (service) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[30m]))
          /
          sum by (service) (
            rate(http_server_request_duration_seconds_count[30m]))

      - record: service:sli_error:ratio_rate1h
        expr: |
          sum by (service) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[1h]))
          /
          sum by (service) (
            rate(http_server_request_duration_seconds_count[1h]))

      - record: service:sli_error:ratio_rate6h
        expr: |
          sum by (service) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[6h]))
          /
          sum by (service) (
            rate(http_server_request_duration_seconds_count[6h]))

      - record: service:sli_error:ratio_rate3d
        expr: |
          sum by (service) (
            rate(http_server_request_duration_seconds_count{http_response_status_code=~"5.."}[3d]))
          /
          sum by (service) (
            rate(http_server_request_duration_seconds_count[3d]))

  # ── 2) تنبيهات multi-window multi-burn-rate ──
  #    العتبة = burn_rate × (1 − SLO)  حيث SLO = 0.999 → (1 − SLO) = 0.001
  - name: slo-alerts
    rules:
      # ① حرج: 2% من الميزانية في ساعة (14.4×) — ومؤكد بنافذة 5m
      - alert: OrdersSLOFastBurn
        expr: |
          service:sli_error:ratio_rate1h{service="orders-api"} > (14.4 * 0.001)
          and
          service:sli_error:ratio_rate5m{service="orders-api"} > (14.4 * 0.001)
        labels:
          severity: critical
          slo: "99.9"
          notify: page
        annotations:
          summary: "orders-api بيحرق 2% من ميزانية الأخطاء في ساعة (14.4×)"
          description: >
            نسبة الفشل على ساعة {{ $value | humanizePercentage }}.
            الميزانية الشهرية هتخلص في ~يومين لو استمر المعدل.
          runbook: "docs/runbooks/orders-slo-burn.md"
          dashboard: "https://grafana.local/d/shop-red"

      # ② متوسط: 5% في 6 ساعات (6×) — ومؤكد بنافذة 30m
      - alert: OrdersSLOSlowBurn
        expr: |
          service:sli_error:ratio_rate6h{service="orders-api"} > (6 * 0.001)
          and
          service:sli_error:ratio_rate30m{service="orders-api"} > (6 * 0.001)
        labels:
          severity: warning
          slo: "99.9"
          notify: page
        annotations:
          summary: "orders-api بيحرق 5% من الميزانية في 6 ساعات (6×)"
          runbook: "docs/runbooks/orders-slo-burn.md"

      # ③ بطيء: 10% في 3 أيام (1×) — تذكرة لا page
      - alert: OrdersSLOBudgetDrain
        expr: |
          service:sli_error:ratio_rate3d{service="orders-api"} > (1 * 0.001)
          and
          service:sli_error:ratio_rate6h{service="orders-api"} > (1 * 0.001)
        labels:
          severity: info
          slo: "99.9"
          notify: ticket
        annotations:
          summary: "استهلاك ميزانية orders-api أعلى من المسموح على 3 أيام"
          runbook: "docs/runbooks/orders-slo-budget.md"

      # ④ SLI الزمن (ثانوي): 95% تحت 300ms
      - alert: OrdersLatencySLO
        expr: |
          (
            sum(rate(http_server_request_duration_seconds_bucket{service="orders-api",le="0.3"}[1h]))
            /
            sum(rate(http_server_request_duration_seconds_count{service="orders-api"}[1h]))
          ) < 0.95
        for: 15m
        labels: { severity: warning, notify: ticket }
        annotations:
          summary: "أقل من 95% من طلبات orders-api تحت 300ms على ساعة"
          runbook: "docs/runbooks/orders-latency.md"

      # ⑤ تنبيه على الميزانية المتبقية (لا على المعدل) — للإنذار المبكر
      # الميزانية المتبقية كنسبة = (نجاح_30d − SLO) ÷ (1 − SLO)؛ ننبه لو أقل من 10%
      - alert: OrdersErrorBudgetLow
        expr: |
          (
            (
              1 - (
                sum(increase(http_server_request_duration_seconds_count{service="orders-api",http_response_status_code=~"5.."}[30d]))
                /
                sum(increase(http_server_request_duration_seconds_count{service="orders-api"}[30d]))
              )
            ) - 0.999
          ) / 0.001 < 0.1
        labels: { severity: info, notify: ticket }
        annotations:
          summary: "أقل من 10% من ميزانية أخطاء orders-api متبقي لهذا الشهر"
          description: "فعّل سياسة الميزانية: تجميد الميزات غير الحرجة (docs/slo-orders.md)"
'''},

        # ── 5) تقليل الضجيج
        {"type": "heading", "level": 2, "text": "⑤ تقليل الضجيج: التوجيه والتجميع والكبت والصمت"},
        {"type": "table", "caption": "تنبيه سيئ مقابل تنبيه جيد — نفس النظام",
         "head": ["سيئ (بيسبب إرهاق)", "ليه سيئ", "جيد (بديل)"],
         "rows": [
             ["`CPU > 80%` → page", "سبب مش عرض: CPU عالي ممكن يكون حمل طبيعي بلا أثر على المستخدم",
              "page فقط على burn rate · وCPU يبقى لوحة/تذكرة لو استمر"],
             ["`pod restarted` → page لكل pod", "20 نسخة = 20 تنبيه لحادث واحد",
              "تجميع على `alertname`+`service` + تنبيه واحد لو نسبة النسخ غير السليمة > حد"],
             ["`disk 85%` → page", "فيه ساعات للتصرف", "ticket عند 80% · page عند 95% أو لو النمو سريع"],
             ["`5xx > 0` → page", "أي نظام فيه أخطاء نادرة → تنبيه دائم",
              "نسبة فشل مقابل burn rate (يعني مقارنة بالميزانية مش بالصفر)"],
             ["`certificate expires in 30 days` → page", "مش طارئ", "ticket (30 يومًا) · page (7 أيام)"],
             ["تنبيه بلا runbook", "المستيقظ مش عارف يعمل إيه → وقت ضائع",
              "كل تنبيه فيه رابط runbook بخطوات تشخيص وتخفيف"],
             ["تنبيه يتكرر كل 5 دقائق طول الليل", "بلا قيمة بعد أول مرة",
              "`repeat_interval: 4h` + `group_wait`/`group_interval` مضبوطين"],
         ]},
        {"type": "code", "lang": "yaml", "title": "observability/alertmanager.yml", "filename": "observability/alertmanager.yml", "code": r'''global:
  resolve_timeout: 5m
  slack_api_url: "https://hooks.slack.com/services/REPLACE_ME"   # من secret، لا من Git

route:
  receiver: default
  group_by: ["alertname", "service", "environment"]   # حادث واحد = إشعار واحد
  group_wait: 30s          # استنى 30s لتجميع تنبيهات الحادث نفسه
  group_interval: 5m       # لو وصل تنبيه جديد لنفس المجموعة
  repeat_interval: 4h      # لا تكرر التنبيه المستمر أكتر من كل 4 ساعات
  routes:
    # ① page: يروح لخدمة on-call (PagerDuty/Opsgenie) مع تكرار أقصر
    - matchers: [ 'notify = page' ]
      receiver: oncall-page
      group_wait: 10s
      repeat_interval: 1h
      continue: false

    # ② ticket: يفتح قضية (أو قناة) في ساعات العمل
    - matchers: [ 'notify = ticket' ]
      receiver: tickets
      repeat_interval: 24h

    # ③ معلومات الميزانية: قناة المنتج/الهندسة
    - matchers: [ 'severity = info' ]
      receiver: slack-slo
      repeat_interval: 24h

# الكبت: لما الخدمة كلها ساقطة، لا تُرسل تنبيهات فرعية لكل مسار/نسخة
inhibit_rules:
  - source_matchers: [ 'alertname = ServiceDown', 'severity = critical' ]
    target_matchers: [ 'severity = warning' ]
    equal: ["service"]

  - source_matchers: [ 'alertname = OrdersSLOFastBurn' ]
    target_matchers: [ 'alertname = OrdersSLOSlowBurn' ]
    equal: ["service"]

# الصمت: أثناء الصيانة المخطط لها (من الـUI أو amtool) — بلا تنبيهات متوقعة
#   amtool silence add alertname="OrdersSLOFastBurn" --duration 2h \
#     --comment "نشر مخطط" --author "oncall"

receivers:
  - name: default
    slack_configs:
      - channel: "#shop-alerts"
        send_resolved: true
        title: '{{ .GroupLabels.alertname }} ({{ .Status }})'
        text: >
          {{ range .Alerts }}*{{ .Annotations.summary }}*
          {{ if .Annotations.runbook }}runbook: {{ .Annotations.runbook }}{{ end }}
          {{ end }}

  - name: oncall-page
    # PagerDuty/Opsgenie — routing key من secret:
    pagerduty_configs:
      - routing_key: "<from-secret>"
        severity: critical

  - name: tickets
    webhook_configs:
      - url: "http://ticket-bridge:8080/create"    # خدمة صغيرة تفتح issue

  - name: slack-slo
    slack_configs:
      - channel: "#slo-review"
        send_resolved: false
'''},

        # ── 6) دورة حياة التنبيه
        {"type": "heading", "level": 2, "text": "⑥ دورة حياة التنبيه: من الرنة للـpostmortem (تمهيد لـ7.2.1)"},
        {"type": "table", "caption": "لكل مرحلة زمن مستهدف ومسؤول وأدلة",
         "head": ["المرحلة", "الزمن المستهدف", "المسؤول", "الأدوات/الأدلة"],
         "rows": [
             ["الإطلاق (alert fires)", "—", "Prometheus", "قاعدة SLO + `for`/نوافذ"],
             ["الإشعار (notify)", "أقل من دقيقة من الإطلاق", "Alertmanager", "تجميع + routing + runbook link"],
             ["الإقرار (ack)", "**أقل من 5 دقائق** (page)", "on-call", "ack في أداة الـpaging (بيوقف التصعيد)"],
             ["التقييم الثلاثي (triage)", "أقل من 10 دقائق", "on-call", "اللوحة (7.1.4) ← الـtrace ← السجل (7.1.3)"],
             ["التخفيف (mitigate)", "**أقل من 30 دقيقة**", "on-call + مالك الخدمة", "رجوع الإصدار (6.3.3) · توسع · feature flag off · عزل نسخة"],
             ["الحل والتحقق", "—", "on-call", "عودة الـSLI للمستوى الطبيعي + اختفاء التنبيه (بفضل النافذة القصيرة)"],
             ["المراجعة (postmortem)", "خلال 48 ساعة", "الفريق", "وثيقة بلا لوم: التسلسل الزمني · السبب الجذري · الإجراء الوقائي · هل التنبيه كان مناسبًا؟"],
             ["مراجعة التنبيه نفسه", "أسبوعيًا (15 دقيقة)", "on-call", "جدول: كل تنبيه اشتغل · هل كان حقيقيًا · زمن الإقرار · الإجراء"],
         ]},
        {"type": "callout", "kind": "danger", "title": "7 أخطاء بتحوّل المراقبة لضجيج",
         "md": "**① تنبيهات على الأسباب** (CPU/ذاكرة) بدل الأعراض (SLI/burn rate) — النتيجة: صفحات بلا أثر على المستخدم. **② مفيش `for` ولا نافذة قصيرة** — دقيقة سيئة تطلق page. **③ تنبيه بلا runbook** — المستيقظ بيبدأ من الصفر الساعة 3 فجرًا. **④ تكرار بلا حدود** (`repeat_interval` قصير) — التنبيه بيتجاهل بعد العاشرة. **⑤ كل التنبيهات page** — لما كل حاجة عاجلة، مفيش حاجة عاجلة. **⑥ مفيش مراجعة دورية** — التنبيهات الميتة (اللي ما اشتغلتش من شهور أو اللي بتشتغل وتُتجاهل) بتتراكم. **⑦ SLO بلا مالك** — هدف من غير حد مسؤول عنه ومن غير سياسة ميزانية = رقم في لوحة."},

        {"type": "steps", "title": "⑦ خطة تطبيق SLO على خدمة واحدة (6 خطوات)",
         "items": [
             {"title": "1) اختار SLI واحدًا أساسيًا + واحدًا ثانويًا",
              "md": "التوافر (نسبة غير 5xx) كأساس، والزمن (95% تحت X) كثانوي. تأكد إنهم محسوبين من مقاييس موجودة (7.1.4) — ولو مش موجودة، أضفها أولًا.",
              "code": "curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count[5m]))'"},
             {"title": "2) قِس الواقع لمدة أسبوع قبل ما تحدد الهدف",
              "md": "الهدف مبني على بيانات: ما نسبة النجاح الفعلية؟ ما p95؟ لو الواقع 99.5% فهدف 99.99% = كسر دائم وفقدان مصداقية.",
              "code": ""},
             {"title": "3) اكتب SLO + سياسة ميزانية في `docs/slo-<service>.md`",
              "md": "بالصيغة والفترة (30 يومًا متدحرجة) والميزانية بالأرقام والسياسة (إيه اللي بيتوقف عند 10%) والمالك وتاريخ المراجعة.",
              "code": ""},
             {"title": "4) أضف recording rules + تنبيهات multi-window",
              "md": "3 مستويات: 14.4× (1h/5m) page · 6× (6h/30m) page/عاجل · 1× (3d/6h) ticket. وكل تنبيه فيه `runbook` و`dashboard` في الـannotations.",
              "code": "promtool check rules observability/slo-rules.yml"},
             {"title": "5) اضبط Alertmanager (تجميع · كبت · تكرار · توجيه)",
              "md": "page → on-call · ticket → قضايا · info → قناة SLO. و`group_wait: 30s` و`repeat_interval: 4h` للتقليل.",
              "code": "amtool check-config observability/alertmanager.yml\namtool config routes test --config.file=observability/alertmanager.yml alertname=OrdersSLOFastBurn notify=page"},
             {"title": "6) اختبر وحذّر وراجع",
              "md": "حقن عطل متعمد → تأكد إن التنبيه الصح اشتغل بالشكل الصح واختفى بعد الإصلاح. وراجع أسبوعيًا: كل تنبيه اشتغل، هل كان حقيقيًا، وإيه الإجراء.",
              "code": ""},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أفرق بين SLI (قياس) وSLO (هدف داخلي) وSLA (عقد بتعويض) وأعرف ترتيبهم (SLA أضعف من SLO).",
            "أقدر أختار SLI من منظور المستخدم وأحسبه من مقاييس موجودة بصيغة PromQL.",
            "أعرف أحول SLO لميزانية خطأ بالأرقام (دقائق وطلبات) وأقارن تكلفة كل «9» إضافية.",
            "أقدر أحسب burn rate لأي نافذة: (نسبة الميزانية × دقائق الفترة) ÷ دقائق النافذة → 14.4× لـ2%/1h.",
            "أعرف ليه النافذتان (طويلة + قصيرة) معًا: اكتشاف حقيقي + اختفاء سريع بعد الإصلاح.",
            "أفرق بين page وticket وأعرف إن التنبيه اللي مش واحد منهم يتحذف.",
            "أقدر أضبط Alertmanager: grouping · inhibition · silence · repeat_interval · routing حسب `notify`.",
            "عندي سياسة ميزانية مكتوبة (إيه اللي بيتوقف وإمتى) ومالك ومراجعة ربع سنوية.",
            "أعرف دورة حياة التنبيه بأزمنة مستهدفة (ack < 5 دقائق · mitigate < 30) وربطها بالـpostmortem.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على SLOs والتنبيهات.",
         "questions": [
             {"q": "SLO = 99.9% لفترة 30 يومًا. كم ميزانية الخطأ بالزمن؟",
              "options": ["7.2 ساعات", "**43.2 دقيقة** (0.1% من 43,200 دقيقة)", "4.3 دقائق", "21.6 دقيقة"],
              "answer": 1,
              "explain": "30 يومًا = 43,200 دقيقة × 0.001 = 43.2 دقيقة. و4.3 دقائق هي ميزانية 99.99% — وده اللي بيوضح ليه كل «9» إضافية بتغير متطلبات البنية جذريًا."},
             {"q": "ليه 14.4× كعتبة لـ«2% في ساعة»؟",
              "options": ["رقم عشوائي من Google", "**(0.02 × 43,200 دقيقة) ÷ 60 دقيقة = 14.4** — يعني لو استمر المعدل ده، ميزانية الشهر تخلص في ~يومين", "لأنه 1/0.07", "لأنه ضعف الـSLO"],
              "answer": 1,
              "explain": "الصيغة العامة: `burn_rate = (نسبة الميزانية × طول الفترة) ÷ طول النافذة`. ولو SLO مختلف، العتبة = `burn_rate × (1 − SLO)`."},
             {"q": "ليه نربط نافذة طويلة بنافذة قصيرة (AND)؟",
              "options": ["لتقليل عدد القواعد", "**الطويلة بتأكد إن فيه استهلاك حقيقي (مش ضجيج)، والقصيرة بتأكد إنه لسه بيحصل دلوقتي — فيختفي التنبيه خلال دقائق بعد الإصلاح بدل ساعات**", "لأن Prometheus بيفرضه", "لتحسين الأداء"],
              "answer": 1,
              "explain": "النافذة الطويلة وحدها بتفضل «مشتعلة» بعد الإصلاح لأن البيانات القديمة لسه في النافذة. القصيرة وحدها بتطلق page من دقيقة سيئة."},
             {"q": "CPU في الخدمة وصل 85% والمستخدمين مش متأثرين. تعمل إيه؟",
              "options": ["page فورًا", "**لا تنبه كـpage: ده سبب مش عرض — خليها لوحة وticket لو استمرت، والـpage يبقى على burn rate/SLI**", "تجاهلها تمامًا", "أعد تشغيل النسخ"],
              "answer": 1,
              "explain": "التنبيه على الأعراض بيضمن إن كل page يعني «مستخدم متأثر». الأسباب (CPU/ذاكرة/GC) تُفحص في اللوحة بعد التنبيه، لا قبله."},
             {"q": "SLA مع العميل 99.5%. إيه الـSLO الداخلي المناسب؟",
              "options": ["99.5% (نفس الرقم)", "**99.9% (أقوى من الـSLA)** — عشان التنبيه الداخلي ييجي قبل ما تكسر العقد ويكون فيه هامش للتصرف", "99%", "99.99% دايمًا"],
              "answer": 1,
              "explain": "الـSLO أقوى من الـSLA وأقوى من الواقع الحالي. ولو حطيت 99.99% من غير بنية تدعمها، هتكسره دايمًا فالهدف يفقد معناه (والتنبيهات تتجاهل)."},
             {"q": "ميزانية الأخطاء لخدمة وصلت 5%. إيه التصرف حسب السياسة؟",
              "options": ["نشر عادي", "**تجميد الميزات غير الحرجة والتركيز على الموثوقية (وحسب السياسة: تحت 10% = وقف النشر غير الأمني + خطة موثوقية)**", "تقليل الـSLO", "إيقاف التنبيهات"],
              "answer": 1,
              "explain": "الميزانية أداة قرار: لما تخلص، الأولوية للموثوقية مش للميزات. وتقليل الـSLO لإخفاء المشكلة = تدمير لمصداقية الهدف (إلا لو مراجعة ربع سنوية مبررة بأرقام)."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "SLO حقيقي + تنبيهات مختبرة.",
         "items": [
             {"id": "t1", "title": "مهمة 1: عرّف SLO لخدمتين واحسب الميزانية بالأرقام",
              "md": "**السياق:** نظام `shop`: `orders-api` (واجهة مستخدم) و`outbox-worker` (خلفي).\n\n**المطلوب:**\n1. `docs/slo-orders.md` و`docs/slo-worker.md`: لكل خدمة **SLI أساسي + ثانوي** بصيغة PromQL حقيقية (مشتغلة على مقاييسك) + SLO + فترة (30 يومًا متدحرجة).\n2. **حساب الميزانية بالأرقام** لكل خدمة: بالدقائق · بعدد الرسائل/الطلبات · وبنسبة من الميزانية المتبقية حاليًا (استعلام جاهز).\n3. **مبرر الهدف**: قِس الواقع لمدة 24 ساعة على الأقل (أو تحت حمل k6) واكتب: الواقع = X% ، الهدف = Y% ، والفجوة + ليه الهدف ده مش أعلى/أقل (بما فيه **توافر التبعيات**: قاعدة البيانات · RabbitMQ · مزوّد الدفع).\n4. **سياسة ميزانية** بجدول (فوق 50% / 25–50% / 10–25% / تحت 10% / مستهلكة) + المالك + تاريخ المراجعة.\n5. للـworker: SLI مختلف عن الـAPI — مثلًا **الحداثة** (عمر أقدم رسالة < 60 ثانية) أو **الصحة** (DLQ = 0) — مع تبرير ليه التوافر مش الـSLI المناسب لخدمة خلفية.\n6. **لوحة SLO** في Grafana: نسبة النجاح على 30 يومًا · الميزانية المتبقية (gauge) · burn rate الحالي · مقارنة بالهدف (خط أحمر) · ورابط من اللوحة للـrunbook.\n7. `docs/slo-review.md`: قالب مراجعة ربع سنوية (الواقع مقابل الهدف · عدد الحوادث · أهم 3 أسباب · قرار: ارفع/ثبّت/خططة موثوقية).",
              "criteria": [
                  "SLI لكل خدمة بصيغة PromQL **تشتغل فعلًا** (مُثبتة بمخرج استعلام).",
                  "حساب الميزانية بثلاث وحدات (دقائق · طلبات/رسائل · نسبة متبقية) + استعلام جاهز.",
                  "قياس واقع (24 ساعة أو تحت حمل) ومقارنة بالهدف مع تفسير الفجوة.",
                  "ذكر توافر التبعيات وأثره على سقف الـSLO (حساب تقريبي).",
                  "سياسة ميزانية بجدول ومالك وتاريخ مراجعة.",
                  "SLI الـworker مختلف ومبرر (حداثة/صحة بدل توافر).",
                  "لوحة SLO بأربع عناصر على الأقل + رابط runbook.",
                  "قالب مراجعة ربع سنوية بقرارات محددة (رفع/تثبيت/خطة موثوقية).",
              ],
              "hint": "للقياس السريع من غير 30 يوم: استخدم `increase(...[1h])` ووسّع النافذة تدريجيًا، أو شغّل حمل k6 لمدة ساعة واحسب نسبة الفشل. وللميزانية المتبقية: `(SLO − (1 − نسبة_الفشل_30d)) / (1 − SLO)` — ولو القيمة سالبة فالميزانية مستهلكة. ولوحة الـgauge: استخدم panel من نوع `gauge` بحدود 0–100%.",
              "solution": "النتائج النموذجية: `orders-api` الواقع ~99.95% تحت حمل عادي → SLO **99.9%** (ميزانية 43.2 دقيقة/1,000 طلب من مليون) مع هامش أمان، والسبب إن التبعيات (PostgreSQL المُدارة 99.99% + RabbitMQ ذاتي الاستضافة ~99.9%) بتحدد السقف عند ~99.9%. `outbox-worker`: التوافر مش مفيد (مفيش طلبات مستخدم) → SLI أساسي = **الحداثة**: `max(shop_outbox_oldest_age_seconds) < 60` لمدة 99% من 30 يومًا (ميزانية: 43.2 دقيقة يُسمح فيها بتأخير)، وثانوي = **الصحة**: `rabbitmq_queue_messages{dlq} == 0`. سياسة الميزانية: فوق 50% نشر عادي · 25–50% canary أطول · 10–25% تجميد الميزات · تحت 10% وقف النشر غير الأمني وخطة موثوقية أسبوع · مستهلكة = postmortem + إبلاغ. أهم درس: الهدف اللي مش مبني على قياس واقع بيكون إما سهل جدًا (بلا قيمة) أو مستحيلًا (بيتجاهلوه).",
              "resources": [
                  "https://sre.google/sre-book/service-level-objectives/",
                  "https://sre.google/workbook/implementing-slos/",
                  "https://sre.google/workbook/alerting-on-slos/",
                  "https://learn.microsoft.com/en-us/azure/well-architected/reliability/metrics",
                  "https://prometheus.io/docs/prometheus/latest/querying/operators/",
              ]},
             {"id": "t2", "title": "مهمة 2: تنبيهات multi-window مُختبَرة + Alertmanager بلا ضجيج",
              "md": "**السياق:** الـSLO معرّف (مهمة 1) — فاضل التنبيه ييجي صح ومن غير ضجيج.\n\n**المطلوب:**\n1. `observability/slo-rules.yml`: recording rules للـSLI على 5 نوافذ (5m · 30m · 1h · 6h · 3d) + **ثلاث تنبيهات** multi-window multi-burn-rate (14.4×/1h+5m page · 6×/6h+30m page · 1×/3d+6h ticket) + تنبيه على SLI الزمن + تنبيه على الميزانية المتبقية < 10%.\n2. كل تنبيه فيه: `severity` · `notify` · `summary` · `description` بالقيمة · **`runbook`** · `dashboard`.\n3. `observability/alertmanager.yml`: routing حسب `notify` · `group_by` · `group_wait/interval` · `repeat_interval` · **inhibition** (ServiceDown يكبت التحذيرات · FastBurn يكبت SlowBurn) · ثلاثة مستقبلات (page/ticket/info).\n4. **تحقق ثابت**: `promtool check rules` و`amtool check-config` — ومخرجاتهما مرفقة.\n5. **اختبار حي لكل مستوى** (ده أهم بند): حقن معدل أخطاء ~2% (عتبة الحرج) وتأكيد إن `FastBurn` اشتغل **خلال ~دقيقتين**؛ ثم أوقف العطل وتأكيد إن التنبيه اختفى **خلال دقائق** (بفضل نافذة الـ5m). كرّر لمستوى 6× بمعدل ~0.7% وسجّل الأزمنة.\n6. **قياس الضجيج**: سجّل لمدة أسبوع (أو من بيانات سابقة): عدد التنبيهات · كم منها كان حقيقيًا · زمن الإقرار · كم إشعار لكل حادث (قبل/بعد الـgrouping) — واكتب الخلاصة في `docs/alerting-review.md`.\n7. اكتب 3 runbooks (`docs/runbooks/…`): لكل تنبيه — الأعراض · أول 3 فحوصات · التخفيف (بما فيه أمر الرجوع من 6.3.3) · التصعيد · ما بعد الحادث.\n8. مراجعة: احذف/عدّل أي تنبيه ما اشتغلش أو اتُجاهل — ووثّق القرار.",
              "criteria": [
                  "5 نوافذ recording rules + 3 تنبيهات burn rate بالعتبات الصحيحة (`14.4 × 0.001` …).",
                  "كل تنبيه فيه runbook + dashboard + description بالقيمة.",
                  "Alertmanager فيه grouping + inhibition قاعدتين على الأقل + 3 مستقبلات + `repeat_interval` مختلف لكل مسار.",
                  "`promtool check rules` و`amtool check-config` ناجحان (مخرجات مرفقة).",
                  "**اختبار حي لكل من المستويين الحرج والمتوسط** بأزمنة: الإطلاق · الإشعار · الاختفاء بعد الإصلاح.",
                  "جدول قياس ضجيج: عدد التنبيهات · الحقيقي منها · زمن الإقرار · إشعارات/حادث قبل وبعد.",
                  "3 runbooks بخطوات تشخيص وتخفيف وتصعيد.",
                  "قرار مراجعة لكل تنبيه (إبقاء/تعديل/حذف) مع السبب.",
                  "ملاحظة عن المقايضة: النوافذ الطويلة بتأخر الاكتشاف والقصيرة بتزيد الضجيج — وكيف اخترت.",
              ],
              "hint": "لحقن معدل أخطاء: أضف مسار اختبار بيرمي exception بنسبة معينة (مثلًا `if (Random.Shared.NextDouble() < 0.02) throw …`) واطلبه بـk6 — ده أدق من محاولة كسر حاجة حقيقية. وخلي بالك: التنبيه بيحتاج النافذة الطويلة **والقصيرة** معًا، فلو حققت عطلًا لمدة دقيقة واحدة بس مش هيوصل لـ14.4× على ساعة. جرّب عطلًا مستمرًا 10 دقائق. ولو `promtool` مش مثبت، حمّله من إصدار Prometheus نفسه.",
              "solution": "النتائج النموذجية: مع عطل 2% مستمر، `FastBurn` بيطلق بعد ~2–4 دقائق (النوافذ بتحتاج تمتلئ) والإشعار بيوصل مجمّعًا في Slack/PagerDuty خلال ثوانٍ، وبعد إيقاف العطل بيختفي خلال ~5–6 دقائق (نافذة الـ5m بتفضل). مع عطل 0.7%، `SlowBurn` بيطلق بعد ~30–40 دقيقة (نافذة 6h بتحتاج وقت) — وده مقصود: الحوادث البطيئة تُكتشف أبطأ بس من غير ضجيج. قياس الضجيج نموذجيًا: قبل التجميع = 12–20 إشعارًا لحادث واحد؛ بعده = إشعار واحد + تحديثات كل 5 دقائق. وأهم قرار مراجعة: حذف تنبيهات الأسباب (CPU/ذاكرة) من مسار الـpage وتحويلها للوحة/ticket — وده بيقلل الـpages بنسبة كبيرة من غير أي فقدان في التغطية الحقيقية.",
              "resources": [
                  "https://sre.google/workbook/alerting-on-slos/",
                  "https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/",
                  "https://prometheus.io/docs/alerting/latest/alertmanager/",
                  "https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/",
                  "https://sre.google/workbook/postmortem-culture/",
                  "https://sre.google/sre-book/eliminating-toil/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Google SRE Book: أهداف مستوى الخدمة", "url": "https://sre.google/sre-book/service-level-objectives/"},
            {"label": "Google SRE Workbook: تطبيق SLOs", "url": "https://sre.google/workbook/implementing-slos/"},
            {"label": "Google SRE Workbook: التنبيه على SLOs (المصدر للأرقام)", "url": "https://sre.google/workbook/alerting-on-slos/"},
            {"label": "Alertmanager: التجميع والكبت والصمت", "url": "https://prometheus.io/docs/alerting/latest/alertmanager/"},
            {"label": "Prometheus: قواعد التنبيه", "url": "https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/"},
            {"label": "Azure Well-Architected: مقاييس الموثوقية", "url": "https://learn.microsoft.com/en-us/azure/well-architected/reliability/metrics"},
            {"label": "SRE Workbook: ثقافة ما بعد الحادث", "url": "https://sre.google/workbook/postmortem-culture/"},
        ]},
    ],
}

LESSONS_S7_C = [_L5]
