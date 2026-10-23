# -*- coding: utf-8 -*-
"""Stage 6 module 3 (part B): s6-m3-l3 (النشر المستمر Blue-Green/Canary), s6-m3-l4 (Bicep وTerraform)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s6-m3-l3 — النشر المستمر: Blue-Green وCanary
# ══════════════════════════════════════════════════════════════════════════
_L3 = {
    "id": "s6-m3-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "النشر اللحظي (كل commit بينزل إنتاج فورًا) مش هدف في حد ذاته — الهدف **تقليل زمن الرجوع وخطر التغيير**. في الدرس ده: استراتيجيات النشر الخمسة بأرقامها (Recreate · Rolling · Blue-Green · Canary · Shadow) وتنفيذها الفعلي على **App Service slots** و**Container Apps revisions** و**Kubernetes ingress canary / Argo Rollouts**. والأهم: **توافق قاعدة البيانات أثناء وجود إصدارين شغالين في نفس الوقت** (لأن canary معناه كده بالظبط)، والتحقق بعد النشر، والرجوع التلقائي المبني على مؤشرات مش على الإحساس، وفصل **النشر عن الإصدار** بـfeature flags."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Recreate", "def": "أوقف القديم ثم شغّل الجديد: **توقف كامل** لكنه الأبسط. ينفع لبيئات التطوير أو لتغييرات غير متوافقة."},
            {"term": "Rolling update", "def": "استبدال النسخ تدريجيًا (K8s: `maxUnavailable`/`maxSurge`). بلا توقف، بس الإصدارين شغالين معًا لفترة — وده يفرض توافق قاعدة البيانات."},
            {"term": "Blue-Green", "def": "بيئتان متطابقتان: الأخضر يستقبل الحركة، والأزرق بيتنشر فيه الإصدار الجديد، ثم **تحويل لحظي**. أسرع رجوع (حوّل للحظة القديمة) وأغلى تكلفة (ضعف الموارد لفترة)."},
            {"term": "Canary", "def": "النسخة الجديدة تاخد **نسبة صغيرة من الحركة** (1–10%)، تراقب المؤشرات، وبعدين تزيد تدريجيًا أو ترجع. أقل خطرًا لكن أبطأ."},
            {"term": "Shadow / Mirror", "def": "نسخة من الحركة الحقيقية بتتبعت للخدمة الجديدة **بدون رد على المستخدم** — لاختبار الأداء/السلوك بلا خطر. بتضاعف الحمل على التبعيات (قاعدة البيانات!) فاحسبها."},
            {"term": "Progressive delivery", "def": "أتمتة خطوات الـcanary: وزن → انتظار → تحليل مؤشرات → زيادة أو رجوع تلقائي (Argo Rollouts / Flagger)."},
            {"term": "Slot (App Service)", "def": "بيئة مطابقة للإنتاج على نفس الخطة. `swap` بين الاتنين = blue-green لحظي. فيه **slot settings** (إعدادات لا تنتقل مع الـswap)."},
            {"term": "Revision (Container Apps)", "def": "نسخة غير قابلة للتغيير من تعريف التطبيق؛ `activeRevisionsMode: Multiple` بيسمح بوجود أكتر من واحدة وتقسيم الحركة بينها."},
            {"term": "Bake time", "def": "مدة المراقبة بعد كل زيادة وزن (مثال: 10–15 دقيقة) قبل الخطوة الجاية. قصيرة = مش هتشوف المشكلة؛ طويلة = نشر بطيء."},
            {"term": "Auto-rollback", "def": "رجوع تلقائي لما مؤشر يتجاوز عتبة (معدل 5xx · p95 · تشبع طابور). محتاج **خط أساس** قبل النشر للمقارنة."},
            {"term": "فصل النشر عن الإصدار", "def": "**Deploy** = الكود نزل. **Release** = المستخدمين شافوه. الـfeature flags بتخلي الاثنين مستقلين: تنشر كودًا مطفيًا وتشغّله وقت ما تحب وترجعه في ثانية."},
            {"term": "التوافق الأمامي/الخلفي للمخطط", "def": "أثناء النشر التدريجي إصداران بيقرأوا ويكتبوا نفس الجداول: التغييرات لازم تكون **توسيع/تضييق** (expand/contract) مش تعديل مباشر (3.5)."},
        ]},

        # ── 1) الاستراتيجيات
        {"type": "heading", "level": 2, "text": "① الاستراتيجيات الخمسة بأرقامها"},
        {"type": "table", "caption": "التكلفة هنا = موارد إضافية + تعقيد، وزمن الرجوع = من القرار لعودة الحركة السليمة",
         "head": ["الاستراتيجية", "التوقف", "زمن الرجوع", "تكلفة إضافية", "الخطر", "إمتى تستخدمها"],
         "rows": [
             ["Recreate", "**نعم** (ثوانٍ–دقائق)", "دقائق (إعادة نشر القديم)", "صفر", "مرتفع (كل المستخدمين يتأثروا)",
              "dev/staging · تغيير غير متوافق تمامًا · مهام batch"],
             ["Rolling", "لا (لو `maxUnavailable: 0`)", "دقائق (إصدار قديم + انتظار)", "قليلة (`maxSurge`)", "متوسط",
              "**الافتراضي** لـKubernetes/ACA · التغييرات المتوافقة"],
             ["Blue-Green", "لا (تحويل لحظي)", "**ثوانٍ** (حوّل للحظة القديمة)", "**~2×** لفترة", "منخفض",
              "تغييرات كبيرة · إصدارات runtime/إطار · لما الرجوع السريع أهم من التكلفة"],
             ["Canary", "لا", "**ثوانٍ–دقيقة** (حوّل 100% للقديمة)", "قليلة", "**الأدنى** (نسبة صغيرة فقط تتأثر)",
              "الإنتاج الحقيقي · تغييرات في مسارات حساسة · لما عندك مؤشرات ومراقبة جيدة"],
             ["Shadow", "لا", "لا يحتاج رجوع (مفيش أثر على المستخدم)", "**~2×** على الخدمة والتبعيات", "شبه صفر للمستخدم، مرتفع لقاعدة البيانات",
              "اختبار أداء/سلوك إصدار جديد على حمل حقيقي قبل تمكينه"],
         ]},
        {"type": "callout", "kind": "note", "title": "ملاحظتان بيغيّروا القرار",
         "md": "**① Canary وBlue-Green مش بديلين عن الاختبارات** — هما بيقللوا **نصف القطر** (blast radius) بس. لو الاختبارات ضعيفة (1.2) هتكتشف العطل في الإنتاج برضه، بس عند 5% من المستخدمين بدل 100%. **② النشر التدريجي بيضاعف مدة تعايش الإصدارين** — يعني متطلبات توافق قاعدة البيانات والعقود بتبقى **أشد**، مش أخف. canary لمدة يوم كامل = يوم كامل فيه إصدار قديم وجديد بيكتبوا في نفس الجداول."},

        # ── 2) التنفيذ
        {"type": "heading", "level": 2, "text": "② التنفيذ على المنصات الثلاثة"},
        {"type": "code", "lang": "bash", "title": "deploy/strategies.sh — App Service وContainer Apps", "filename": "deploy/strategies.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
RG=rg-shop-prod

# ══════════ أ) App Service: Blue-Green بـslots ══════════
APP=shop-orders
az webapp deployment slot create --name "$APP" --resource-group "$RG" --slot staging

# إعدادات لا تنتقل مع الـswap (connection strings/أسماء موارد مختلفة لكل slot):
az webapp config appsettings set --name "$APP" --resource-group "$RG" --slot staging \
  --slot-settings "ConnectionStrings__Default=<staging-connection>" "WEBSITE_SLOT_NAME=staging"

# انشر في الـslot واختبر **بإعدادات الإنتاج الحقيقية** (نفس الخطة/الشبكة):
az webapp deploy --name "$APP" --resource-group "$RG" --slot staging --type zip --src-path publish.zip
curl -fsS "https://$APP-staging.azurewebsites.net/health" || { echo "staging غير صحي"; exit 1; }

# التحويل اللحظي (blue-green):
az webapp deployment slot swap --name "$APP" --resource-group "$RG" \
  --slot staging --target-slot production
# الرجوع = swap عكسي (الإصدار القديم لسه دافئ في staging):
az webapp deployment slot swap --name "$APP" --resource-group "$RG" \
  --slot production --target-slot staging

# تحويل تلقائي بعد نجاح staging (اختياري — بلا موافقة بشرية):
az webapp config set --name "$APP" --resource-group "$RG" --auto-swap-slot-name staging

# ══════════ ب) Container Apps: canary بـrevisions ══════════
CA=orders
IMAGE=acrshopprod.azurecr.io/shop/orders@sha256:<DIGEST>   # digest ثابت (6.3.1)

# وضع متعدد النسخ ضروري لتقسيم الحركة:
az containerapp revision set-mode --name "$CA" --resource-group "$RG" --mode Multiple
CURRENT=$(az containerapp show -n "$CA" -g "$RG" --query properties.latestRevisionName -o tsv)
NEW="orders--r$(date +%Y%m%d%H%M)"

az containerapp revision copy --name "$CA" --resource-group "$RG" \
  --revision "$NEW" --image "$IMAGE"

# 5% → راقب 15 دقيقة → 25% → راقب → 100%
az containerapp ingress set --name "$CA" --resource-group "$RG" \
  --traffic-split "$CURRENT=95" --traffic-split "$NEW=5"
sleep 900
az containerapp ingress set --name "$CA" --resource-group "$RG" \
  --traffic-split "$CURRENT=75" --traffic-split "$NEW=25"
sleep 900
az containerapp ingress set --name "$CA" --resource-group "$RG" \
  --traffic-split "$NEW=100"

# الرجوع الفوري (النسخة القديمة لسه نشطة):
#   az containerapp ingress set --name $CA -g $RG --traffic-split "$CURRENT=100"
# إيقاف نسخة قديمة بعد الاستقرار:
az containerapp revision deactivate --name "$CA" --resource-group "$RG" --revision "$CURRENT"
az containerapp revision list --name "$CA" --resource-group "$RG" -o table
'''},
        {"type": "code", "lang": "yaml", "title": "k8s/canary-ingress.yaml — canary على Kubernetes بـingress-nginx", "filename": "k8s/canary-ingress.yaml", "code": r'''# الفكرة: Ingress ثاني بنفس الـhost/path لكن بتعليقات canary،
# فالـcontroller بيوزّع الحركة بين الخدمة الأساسية وخدمة الـcanary.
# ⚠ ingress-nginx: النسب تقريبية (مش دقيقة تمامًا عند الأحجام الصغيرة).
---
apiVersion: v1
kind: Service
metadata:
  name: orders-canary
  namespace: shop
spec:
  selector: { app: orders, track: canary }     # نفس الـlabels + track
  ports: [{ name: http, port: 80, targetPort: http }]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-canary
  namespace: shop
spec:
  replicas: 2                                   # نسخ كافية لقراءة مؤشرات ذات معنى
  selector:
    matchLabels: { app: orders, track: canary }
  template:
    metadata:
      labels: { app: orders, track: canary }
    spec:
      containers:
        - name: orders
          image: acrshopprod.azurecr.io/shop/orders@sha256:<DIGEST>
          ports: [{ name: http, containerPort: 8080 }]
          readinessProbe:
            httpGet: { path: /health, port: 8080 }
            periodSeconds: 10
            failureThreshold: 3
          resources:
            requests: { cpu: 250m, memory: 512Mi }
            limits:   { memory: 512Mi }          # CPU limit متعمد تركه مفتوحًا (6.1.5)
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orders-canary
  namespace: shop
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"          # 10% من الحركة
    # توزيع أدق: مستخدمون داخليون أولًا بلا أي نسبة:
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "always"
    # أو نسبة من ملفات تعريف الارتباط (لجلسات متسقة):
    nginx.ingress.kubernetes.io/canary-by-cookie: "canary"
spec:
  ingressClassName: nginx
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service: { name: orders-canary, port: { name: http } }
---
# بعد التحقق: احذف الـcanary ingress ورفع النسخة الجديدة كأساسية:
#   kubectl -n shop delete ingress orders-canary
#   kubectl -n shop set image deploy/orders orders=...@sha256:<DIGEST>
#   kubectl -n shop rollout status deploy/orders
'''},
        {"type": "code", "lang": "yaml", "title": "k8s/argo-rollout.yaml — تقدمي بمراقبة تلقائية (اختياري)", "filename": "k8s/argo-rollout.yaml", "code": r'''# Argo Rollouts بيأتمت خطوات الـcanary: وزن → انتظار → تحليل → زيادة أو رجوع.
# ⚠ ثبّت الإضافة أولًا (kubectl create namespace argo-rollouts + apply للـmanifests)
#   وتحقق من إصدار API/الحقول في الإصدار المثبت عندك.
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: orders
  namespace: shop
spec:
  replicas: 6
  selector:
    matchLabels: { app: orders }
  template:
    metadata:
      labels: { app: orders }
    spec:
      containers:
        - name: orders
          image: acrshopprod.azurecr.io/shop/orders@sha256:<DIGEST>
          ports: [{ name: http, containerPort: 8080 }]
          resources:
            requests: { cpu: 250m, memory: 512Mi }
            limits: { memory: 512Mi }
          readinessProbe:
            httpGet: { path: /health, port: 8080 }
  strategy:
    canary:
      canaryService: orders-canary
      stableService: orders-stable
      trafficRouting:
        nginx:
          stableIngress: orders            # الـIngress الأساسي
      steps:
        - setWeight: 5
        - pause: { duration: 10m }         # bake time: راقب المؤشرات
        - setWeight: 25
        - pause: { duration: 10m }
        - setWeight: 60
        - pause: {}                        # انتظار موافقة يدوية: kubectl argo rollouts promote
        - setWeight: 100
      analysis:                            # يحتاج مزود مقاييس (Prometheus/App Insights)
        templates:
          - templateName: success-rate
        startingStep: 1                    # ابدأ التحليل بعد أول وزن
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: shop
spec:
  metrics:
    - name: success-rate
      interval: 2m
      count: 5
      successCondition: result[0] >= 0.995   # أقل من 99.5% نجاح → فشل
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="orders-canary",code!~"5.."}[2m]))
            /
            sum(rate(http_requests_total{service="orders-canary"}[2m]))
'''},

        # ── 3) قاعدة البيانات
        {"type": "heading", "level": 2, "text": "③ توافق قاعدة البيانات: لأن canary يعني إصدارين شغالين معًا"},
        {"type": "callout", "kind": "danger", "title": "القاعدة الذهبية للنشر التدريجي",
         "md": "**خلال النشر، الإصدار القديم والجديد بيقرأوا ويكتبوا في نفس قاعدة البيانات في نفس الوقت.** أي تغيير في المخطط لازم يكون متوافق مع **الاتنين** — وده معنى expand/contract من درس 3.5: **وسّع** (أضف عمود/جدول جديد، اكتب في الاثنين) → **انشر** → **هاجر البيانات** → **ضيّق** (احذف القديم) في إصدار لاحق. التغييرات اللي بتكسر (إعادة تسمية عمود · حذف عمود · تغيير نوع · إضافة NOT NULL بلا قيمة افتراضية) = عطل فوري لنسبة من المستخدمين."},
        {"type": "table", "caption": "كل تغيير وإزاي تعديه بأمان أثناء canary",
         "head": ["التغيير", "آمن مباشرة؟", "الطريقة الآمنة (expand/contract)", "عدد الإصدارات المطلوبة"],
         "rows": [
             ["إضافة جدول جديد", "✓", "أضفه وأنشر الكود اللي يستخدمه", "1"],
             ["إضافة عمود nullable أو بقيمة افتراضية", "✓", "أضفه أولًا، ثم انشر الكود اللي يقرأه", "1–2"],
             ["إضافة عمود `NOT NULL`", "✗", "أضفه nullable + قيمة افتراضية + املأه + **بعدين** ضيف القيد في إصدار لاحق", "2–3"],
             ["إعادة تسمية عمود", "✗", "أضف العمود الجديد → انسخ/اكتب في الاثنين → انقل القراءات → احذف القديم", "3"],
             ["حذف عمود", "✗", "أوقف الكتابة → أوقف القراءة → احذف في إصدار لاحق (بعد التأكد من عدم وجود نسخ قديمة)", "2–3"],
             ["تغيير نوع عمود", "✗", "عمود جديد بالنوع المطلوب → هجرة تدريجية → تبديل القراءات → حذف القديم", "3"],
             ["إضافة فهرس", "✓ (مع الانتباه)", "`CREATE INDEX CONCURRENTLY` في PostgreSQL (بلا قفل كتابة) — راجع 3.1.1", "1"],
             ["حذف فهرس", "△", "تأكد إن الإصدار القديم ما بيستخدمهوش (لو فيه canary قديم شغال → انتظر)", "2"],
             ["تغيير دلالة قيمة (مثلًا حالة جديدة في enum)", "△", "الإصدار القديم لازم يتجاهل القيم المجهولة بأمان (2.1.x) — أضف الحالة ثم انشر", "2"],
             ["تغيير في مفتاح API (حذف/تغيير نوع)", "✗", "إصدار جديد من الـAPI + توسيع/تضييع (2.1.x و3.5) + إخطار المستهلكين", "2+"],
         ]},
        {"type": "code", "lang": "sql", "title": "migrations/2026_10_rename_order_reference.sql — النمط الآمن على 3 إصدارات", "filename": "migrations/2026_10_rename_order_reference.sql", "code": r'''-- ═══ الإصدار N: توسيع (expand) — بلا أي كسر ═══
-- العمود الجديد nullable، والفهرس يُبنى بلا قفل كتابة:
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_reference text;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_orders_order_reference ON orders (order_reference);

-- الكود في الإصدار N يكتب في العمودين معًا ويقرأ من القديم:
--   INSERT ... (reference_code, order_reference) VALUES (@r, @r)
--   UPDATE ... SET reference_code = @r, order_reference = @r WHERE id = @id

-- ═══ بين N وN+1: هجرة البيانات على دفعات (بلا قفل طويل) ═══
UPDATE orders
   SET order_reference = reference_code
 WHERE order_reference IS NULL
   AND id IN (SELECT id FROM orders WHERE order_reference IS NULL LIMIT 5000 FOR UPDATE SKIP LOCKED);
-- كرّر حتى صفر صفوف (job خلفي أو أمر مجدول)، وراقب التأخير (3.1.2).

-- ═══ الإصدار N+1: تبديل القراءات ═══
-- الكود يقرأ من order_reference ويكتب في الاثنين (للأمان أثناء canary).
-- تحقق: لا استعلامات قديمة تعتمد على reference_code (من pg_stat_statements):
SELECT query, calls FROM pg_stat_statements
 WHERE query ILIKE '%reference_code%' ORDER BY calls DESC LIMIT 10;

-- ═══ الإصدار N+2: تضييق (contract) ═══
ALTER TABLE orders ALTER COLUMN order_reference SET NOT NULL;   -- بعد التأكد من امتلاء كل الصفوف
DROP INDEX CONCURRENTLY IF EXISTS ix_orders_reference_code;
ALTER TABLE orders DROP COLUMN IF EXISTS reference_code;

-- قاعدة: لا تدمج «التوسيع» و«التضييق» في نفس النشر —
-- وإلا الإصدار القديم (لسه شغال في canary) هيكسر.
'''},

        # ── 4) التحقق والرجوع
        {"type": "heading", "level": 2, "text": "④ التحقق بعد النشر والرجوع المبني على مؤشرات"},
        {"type": "code", "lang": "bash", "title": "deploy/verify-and-rollback.sh", "filename": "deploy/verify-and-rollback.sh", "code": r'''#!/usr/bin/env bash
set -uo pipefail
CA=orders; RG=rg-shop-prod
URL=$(az containerapp show -n "$CA" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
NEW_REV="${1:?اسم النسخة الجديدة مطلوب}"

# ═══ 1) Smoke tests: مسارات حقيقية مش /health بس ═══
echo "── فحوصات الدخان ──"
fail=0
check() { # check <الاسم> <المسار> <الكود المتوقع>
  local name=$1 path=$2 want=$3
  local got
  got=$(curl -s -o /dev/null -w '%{http_code}' "https://$URL$path" || echo 000)
  if [ "$got" = "$want" ]; then echo "  ✓ $name ($got)"
  else echo "  ✗ $name: المتوقع $want والفعلي $got"; fail=1; fi
}
check "alive"      "/alive"            200
check "health"     "/health"           200
check "catalog"    "/api/v1/catalog"   200
check "auth مطلوب" "/api/v1/orders"    401
check "404 صحيح"   "/api/v1/nope"      404

# ═══ 2) خط الأساس قبل المقارنة (بدونه مفيش حكم) ═══
# سجّل p95 ومعدل الأخطاء للنسخة القديمة **قبل** رفع الوزن، وخزّنه في متغير/ملف.
BASELINE_P95=${BASELINE_P95:-250}        # ms — من القياس السابق (2.3.4 / 3.4)
BASELINE_ERR=${BASELINE_ERR:-0.2}        # %

# ═══ 3) مراقبة لمدة Bake time ═══
echo "── مراقبة 10 دقائق ──"
END=$((SECONDS+600))
while [ $SECONDS -lt $END ]; do
  # مثال: من Application Insights / Prometheus (عدّل الاستعلام حسب مزودك)
  ERR=$(curl -s "https://$URL/metrics" | awk '/^http_requests_failed_ratio/ {print $2}')
  P95=$(curl -s "https://$URL/metrics" | awk '/^http_request_duration_p95_ms/ {print $2}')
  echo "  err=${ERR:-?}  p95=${P95:-?}  (baseline: ${BASELINE_ERR}% / ${BASELINE_P95}ms)"
  # عتبات الرجوع: خطأ > 1% أو p95 > 2× خط الأساس
  if [ -n "${ERR:-}" ] && awk "BEGIN{exit !($ERR > 1.0)}"; then
    echo "✗ معدل الأخطاء تجاوز العتبة → رجوع"; ROLLBACK=1; break
  fi
  if [ -n "${P95:-}" ] && awk "BEGIN{exit !($P95 > 2 * $BASELINE_P95)}"; then
    echo "✗ p95 تجاوز ضعف خط الأساس → رجوع"; ROLLBACK=1; break
  fi
  sleep 60
done

# ═══ 4) الرجوع: أمر واحد، مُختبَر مسبقًا ═══
if [ "${fail:-0}" = 1 ] || [ "${ROLLBACK:-0}" = 1 ]; then
  CURRENT=$(az containerapp revision list -n "$CA" -g "$RG" \
             --query "[?name!='$NEW_REV' && properties.active].name | [0]" -o tsv)
  az containerapp ingress set -n "$CA" -g "$RG" --traffic-split "$CURRENT=100"
  az containerapp revision deactivate -n "$CA" -g "$RG" --revision "$NEW_REV"
  echo "↩ رجعنا إلى $CURRENT — افتح incident وسجّل السبب"
  exit 1
fi

# ═══ 5) النجاح: رقِّ الوزن ═══
az containerapp ingress set -n "$CA" -g "$RG" --traffic-split "$NEW_REV=100"
echo "✅ $NEW_REV يستقبل 100% من الحركة"
'''},
        {"type": "code", "lang": "csharp", "title": "FeatureFlags.cs — افصل النشر عن الإصدار", "filename": "src/Orders.Api/FeatureFlags.cs", "code": r'''using Microsoft.FeatureManagement;
using Microsoft.FeatureManagement.FeatureFilters;

namespace Shop.Orders;

public static class FeatureFlags
{
    public const string NewCheckout = "Checkout:v2";
    public const string FastShipping = "Shipping:FastOption";

    /// <summary>
    /// التسجيل: الأعلام من الإعدادات (App Configuration في الإنتاج — 6.2.3)،
    /// فيمكن إطفاء/تشغيل علم **بدون نشر** — وده معنى الرجوع في ثانية.
    /// </summary>
    public static IServiceCollection AddShopFeatureFlags(
        this IServiceCollection services, IConfiguration cfg)
    {
        services.AddFeatureManagement(cfg.GetSection("FeatureManagement"))
                .AddFeatureFilter<PercentageFilter>()      // نسبة من المستخدمين
                .AddFeatureFilter<TimeWindowFilter>();     // نافذة زمنية (إطلاق مجدول)
        return services;
    }
}

// الاستخدام في endpoint: المسار الجديد مطفي افتراضيًا، والكود منشور:
public static class CheckoutEndpoints
{
    public static IEndpointRouteBuilder MapCheckout(this IEndpointRouteBuilder app)
    {
        app.MapPost("/checkout", async (
            CheckoutRequest req,
            IFeatureManager features,
            ICheckoutV1 v1,
            ICheckoutV2 v2,
            CancellationToken ct) =>
        {
            // القرار لكل طلب — يعني الإيقاف فوري لكل المستخدمين
            if (await features.IsEnabledAsync(FeatureFlags.NewCheckout))
                return await v2.ExecuteAsync(req, ct);

            return await v1.ExecuteAsync(req, ct);
        })
        // أو على مستوى الـendpoint كله:
        .RequireFeatureGate(FeatureFlags.NewCheckout);     // يرجع 404 لما العلم مطفي

        return app;
    }
}

/* الإعدادات (appsettings.json / App Configuration):
{
  "FeatureManagement": {
    "Checkout:v2": {
      "EnabledFor": [
        { "Name": "Percentage", "Parameters": { "Value": 5 } }   // 5% أولًا
      ]
    },
    "Shipping:FastOption": {
      "EnabledFor": [
        { "Name": "TimeWindow",
          "Parameters": { "Start": "2026-11-01T00:00:00Z", "End": "2026-11-30T00:00:00Z" } }
      ]
    }
  }
}
⚠ قواعد مهمة:
   • كل علم لازم يكون له **تاريخ انتهاء** وحذف من الكود بعد الإطلاق — وإلا الكود يمتلئ بفروع ميتة.
   • اختبر المسارين (مفعّل/مطفى) في CI — وإلا المسار المطفي بيتكسر في صمت.
   • الأعلام مش بديلًا عن canary: الـflag بيتحكم في **السلوك**، وcanary بيتحكم في **النسخة**.
*/
'''},

        # ── 5) القرار
        {"type": "heading", "level": 2, "text": "⑤ اختيار الاستراتيجية: قرار مبني على 4 أسئلة"},
        {"type": "steps", "title": "اسأل بالترتيب",
         "items": [
             {"title": "1) التغيير متوافق مع قاعدة البيانات والعقود؟",
              "md": "لو **لا** → إما تعمل expand/contract (3 إصدارات) أو تختار **Recreate** في نافذة صيانة. النشر التدريجي مع تغيير كاسر = عطل مؤكد لنسبة من المستخدمين.",
              "code": ""},
             {"title": "2) عندك مؤشرات وخط أساس؟",
              "md": "canary بلا مؤشرات (معدل 5xx · p95 · تشبع طابور) وبلا خط أساس = **وهم أمان**: هتنشر لـ5% ومحدش هياخد باله إلا لما توصل 100%. لو مفيش مؤشرات، ابدأ بـblue-green (رجوعه لحظي ومش محتاج تحليل).",
              "code": ""},
             {"title": "3) إيه تكلفة الرجوع مقابل تكلفة الموارد الإضافية؟",
              "md": "Blue-green بيكلف ~2× موارد لفترة بس بيرجع في ثوانٍ. Canary بيكلف أقل بس بياخد وقت أطول للرجوع. للمشروع الشخصي: **ACA revisions** بيديك الاتنين تقريبًا ببلاش (النسخة القديمة بتفضل موجودة).",
              "code": ""},
             {"title": "4) التغيير في كود ولا في منصة؟",
              "md": "تغيير runtime/إصدار إطار/إعدادات منصة → **blue-green** (سلوك مختلف جذريًا). تغيير ميزة داخل إصدار ثابت → **canary**. تغيير بنية تحتية (6.3.4) → what-if + نافذة تغيير + خطة رجوع مكتوبة.",
              "code": ""},
         ]},
        {"type": "callout", "kind": "tip", "title": "خمس قواعد للنشر المستمر",
         "md": "**① انشر بـdigest/إصدار ثابت** — مش `latest` (6.3.1). **② الرجوع لازم يكون أمرًا واحدًا مُختبَرًا** (جرّبه في staging كل شهر). **③ لا تنشر يوم الجمعة ولا قبل إجازة** — ليس خرافة: زمن الاكتشاف بيتمد لما مفيش حد يراقب. **④ كل نشر لازم يصاحبه smoke tests آلية** مش فحص يدوي. **⑤ قِس زمن الرجوع (MTTR) مش عدد النشرات** — الهدف مش «100 نشر في اليوم» بل «أي عطل يرجع في أقل من 5 دقائق»."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق بين الاستراتيجيات الخمسة وأرقامها (توقف · زمن رجوع · تكلفة · خطر).",
            "أقدر أنفذ blue-green بـApp Service slots (مع slot settings وauto-swap) وأرجع بـswap عكسي.",
            "أقدر أنفذ canary بـACA revisions (set-mode Multiple + traffic split متدرج) وبـKubernetes ingress annotations.",
            "فاهم إن canary = إصداران شغالان معًا، فأطبق expand/contract على أي تغيير في المخطط.",
            "أعرف أكتب smoke tests بعد النشر (مسارات حقيقية + أكواد متوقعة) مش `/health` فقط.",
            "أقدر أبني رجوعًا تلقائيًا بعتبات على معدل الأخطاء وp95 **مقابل خط أساس** محفوظ قبل النشر.",
            "أفرق بين النشر (deploy) والإصدار (release) وأستخدم feature flags بنسبة/نافذة زمنية، وعارف قواعد انتهاء الأعلام.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الاستراتيجيات والتوافق.",
         "questions": [
             {"q": "هتعيد تسمية عمود `reference_code` إلى `order_reference` وتستخدم canary. الطريقة الصح؟",
              "options": ["migration واحد بيعيد التسمية قبل النشر", "**3 إصدارات**: أضف العمود الجديد واكتب في الاثنين → هاجر البيانات وبدّل القراءات → احذف القديم", "أوقف الخدمة ودقائق ونفذ", "استخدم view بديل"],
              "answer": 1,
              "explain": "أثناء الـcanary الإصدار القديم لسه بيكتب/يقرأ العمود القديم، فإعادة التسمية المباشرة تكسره فورًا. expand/contract هو الحل (3.5) — وقاعدة: لا تدمج توسيعًا وتضييقًا في نفس النشر."},
             {"q": "ليه blue-green أسرع رجوعًا من canary؟",
              "options": ["لأنه أرخص", "**لأن النسخة القديمة كاملة وجاهزة ودافئة: الرجوع = تحويل لحظي للحركة، بينما canary محتاج قرارًا مبنيًا على مؤشرات وبعدها تحويل**", "لأنه بلا توقف", "لأنه يحتاج موارد أقل"],
              "answer": 1,
              "explain": "الثمن: blue-green بيكلف ~2× موارد لفترة. ACA revisions بيديك تقريبًا نفس الميزة ببلاش لأن النسخ القديمة بتفضل نشطة."},
             {"q": "عملت canary بـ5% ومفيش عندك مؤشرات ولا خط أساس. ده معناه إيه؟",
              "options": ["نشر آمن", "**وهم أمان**: لو العطل بيظهر عند 10% من الطلبات أو بعد 30 دقيقة، هتوصل لـ100% قبل ما تلاحظ", "أفضل من rolling", "يحتاج موافقة بشرية"],
              "answer": 1,
              "explain": "canary بيقلل نصف القطر **لو حد بيراقب ويقدر يحكم**. من غير معدل أخطاء وp95 وخط أساس، مفيش معيار للقرار — فارجع لـblue-green حتى تجهّز المراقبة (2.3.4)."},
             {"q": "feature flag وcanary — إيه الفرق؟",
              "options": ["الشيء نفسه", "**الـflag بيتحكم في السلوك داخل نفس النسخة (إطفاء فوري بلا نشر)، وcanary بيتحكم في أي نسخة من الكود بتخدم نسبة من الحركة**", "canary أسرع", "الـflag يحتاج نشرًا لتغييره"],
              "answer": 1,
              "explain": "الأقوى: الجمع بينهم — تنشر الكود الجديد مطفيًا بـflag (نشر آمن)، ثم تشغّله تدريجيًا (إصدار آمن) وترجعه في ثانية من غير نشر."},
             {"q": "smoke test بينجح على `/health` لكن المستخدمين بيشتكوا. السبب الأشهر؟",
              "options": ["`/health` بطيء", "**الفحص بيغطي مسارًا لا يعتمد على التبعيات الحقيقية** (قاعدة بيانات/طابور/خدمة خارجية) — لازم مسارات عمل حقيقية بأكواد متوقعة (200/401/404)", "الـcanary غلط", "الـDNS"],
              "answer": 1,
              "explain": "صمّم الـsmoke tests كأصغر نسخة من سيناريو مستخدم: قائمة تُقرأ من القاعدة · طلب يحتاج مصادقة يرجع 401 · مسار غير موجود يرجع 404. كده بتكشف مشاكل الاتصال والصلاحيات مش مجرد إقلاع العملية."},
             {"q": "إمتى تختار Recreate رغم التوقف؟",
              "options": ["دايمًا في الإنتاج", "**لما التغيير غير متوافق مع الإصدار القديم (مخطط/عقد) ومفيش وقت لعمل expand/contract — في نافذة صيانة معلنة، أو في dev/staging**", "لأنه أسرع", "لأنه أرخص من blue-green"],
              "answer": 1,
              "explain": "التوقف أحيانًا أرخص من التعقيد: dev/staging وbatch jobs وتغييرات غير متوافقة جذريًا. في الإنتاج: نافذة صيانة معلنة + رجوع مُختبَر + إخطار المستخدمين."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "canary حقيقي بمؤشرات + رجوع مُختبَر.",
         "items": [
             {"id": "t1", "title": "مهمة 1: canary متدرج بمؤشرات ورجوع تلقائي",
              "md": "**السياق:** عايز تنشر نسخة جديدة من `Orders.Api` على منصة من اختيارك (ACA / App Service / Kubernetes).\n\n**المطلوب:**\n1. اختَر الاستراتيجية وبرر الاختيار في `docs/adr/0016-deployment-strategy.md` (بالأربعة أسئلة من الدرس).\n2. `deploy/canary.sh`: ينشر بـ**digest** · يبدأ بـ5% · ينتظر 10 دقائق · 25% · 10 دقائق · 60% · انتظار موافقة يدوية · 100%. وكل خطوة بتطبع حالة الحركة.\n3. `deploy/verify-and-rollback.sh`: smoke tests (5 مسارات على الأقل بأكواد متوقعة) + مراقبة بمقارنة **خط أساس محفوظ** + عتبات رجوع رقمية (معدل أخطاء · p95) + أمر رجوع واحد.\n4. سجّل خط الأساس **قبل** البدء (من staging أو من قياس سابق) في `docs/baseline.md` — بلا خط أساس مفيش حكم.\n5. **تجربة رجوع متعمدة**: انشر نسخة فيها عطل (مثال: مسار بيرمي exception أو p95 مرتفع عمدًا) ووثّق إن السكريبت رجع تلقائيًا، **وزمن الرجوع بالثواني**.\n6. اكتب `docs/rollback-runbook.md`: أمر الرجوع · مين ينفذه · إيه اللي يتحقق بعده · وإزاي نتأكد إن المستخدمين رجعوا لخدمة سليمة.\n7. غيّر واحدًا في قاعدة البيانات (إضافة عمود nullable) وطبّق expand/contract مع النشر — ووثّق إن الإصدار القديم استمر شغالًا أثناء الـcanary.",
              "criteria": [
                  "ADR فيه اختيار الاستراتيجية بالأربعة أسئلة (توافق · مؤشرات · تكلفة · نوع التغيير).",
                  "النشر بـdigest ثابت، والسكريبت متدرج بـbake times مكتوبة (مش sleep عشوائي).",
                  "smoke tests بخمس مسارات حقيقية بأكواد متوقعة (منها 401 و404) — مش `/health` فقط.",
                  "خط أساس محفوظ **قبل** النشر + عتبات رجوع رقمية (مقارنة صريحة).",
                  "تجربة رجوع متعمدة **ناجحة** بزمن مقاس بالثواني.",
                  "runbook رجوع فيه الأمر والمسؤول والتحقق اللاحق.",
                  "تغيير قاعدة البيانات تم بـexpand/contract مع دليل إن الإصدار القديم اشتغل أثناء الـcanary.",
                  "ملاحظة عن حد المنصة (مثلًا: النسب في ingress-nginx تقريبية / عدد النسخ في ACA).",
              ],
              "hint": "أصعب جزء: الحصول على مقاييس لكل revision منفصلة. على ACA استخدم `az containerapp revision list` + Application Insights مع بعد (dimension) باسم الـrevision؛ على Kubernetes استخدم label `track=canary` في المقاييس. ولو مفيش مقاييس جاهزة، ابدأ بأبسط إشارة: عدد 5xx من سجلات الـingress خلال آخر دقيقتين.",
              "solution": "التنفيذ النموذجي على ACA: `revision set-mode Multiple` → `revision copy` بصورة بـdigest → `ingress set --traffic-split old=95 new=5` → سكريبت المراقبة بيقرأ معدل الأخطاء من Application Insights (أو `/metrics` لو مكشوف داخليًا) ويقارن بخط الأساس من `docs/baseline.md` → زيادة تدريجية → موافقة يدوية عند 60% → 100% ثم `revision deactivate` للقديم. تجربة الرجوع المتعمدة: نسخة فيها `Thread.Sleep(3000)` في مسار → p95 يتجاوز 2× خط الأساس → السكريبت بيحوّل 100% للنسخة القديمة ويعطّل الجديدة؛ الزمن النموذجي من الاكتشاف لعودة الحركة = **30–90 ثانية**. تغيير قاعدة البيانات: إضافة عمود nullable في إصدار، نشر بـcanary، التأكد إن الإصدار القديم بيكتب/يقرأ عادي (لأن العمود الجديد nullable)، ثم إصدار تالي بيقرأ العمود الجديد، ثم إصدار ثالث بيضيق (NOT NULL/حذف القديم).",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/container-apps/revisions",
                  "https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots",
                  "https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#canary",
                  "https://argo-rollouts.readthedocs.io/en/stable/",
                  "https://martinfowler.com/bliki/CanaryRelease.html",
                  "https://martinfowler.com/bliki/BlueGreenDeployment.html",
              ]},
             {"id": "t2", "title": "مهمة 2: افصل النشر عن الإصدار بـfeature flags",
              "md": "**السياق:** ميزة جديدة (مثلًا «دفع سريع») عايز تنشرها مطفية، وتشغّلها تدريجيًا، وترجعها في ثانية لو فيه مشكلة.\n\n**المطلوب:**\n1. أضف `Microsoft.FeatureManagement` وسجّل الأعلام من الإعدادات (ويفضل من App Configuration في الإنتاج عشان التغيير **بدون نشر**).\n2. عَلَم `Checkout:v2` بـ**Percentage filter** يبدأ 5%، وعَلَم `Shipping:FastOption` بـ**TimeWindow** لإطلاق مجدول.\n3. المسار الجديد خلف العلم، والمسار القديم لسه موجود — **واختبر الاثنين في CI** (اختباران على الأقل: علم مفعّل → المسار الجديد؛ علم مطفي → القديم).\n4. اكتب `docs/feature-flags.md`: جدول الأعلام (الاسم · الوصف · الحالة · المالك · **تاريخ الانتهاء المخطط** · كيفية الإطفاء الفوري) + قاعدة حذف العلم من الكود بعد الإطلاق.\n5. أضف **قياسًا** لكل مسار (عدّاد/مقياس يوضح عدد الطلبات عبر v1 مقابل v2) عشان تقدر تحكم على الإطلاق.\n6. جرّب الإطفاء الفعلي: فعّل العلم، اطلب 20 مرة، وثّق النسبة التقريبية؛ ثم أطفئه من الإعدادات ووثّق إن كل الطلبات رجعت للمسار القديم **بدون نشر**.\n7. أضف فحصًا في CI يفشل لو فيه علم **بدون تاريخ انتهاء** في الجدول (سكربت بسيط يقرأ `docs/feature-flags.md`).",
              "criteria": [
                  "الأعلام تُقرأ من الإعدادات (مش ثابتة في الكود) ويمكن تغييرها بدون نشر.",
                  "Percentage filter شغال (نسبة تقريبية موثقة بالقياس) وTimeWindow مضبوط بتوقيت UTC.",
                  "اختباران في CI يغطيان المسارين (مفعّل/مطفى) — وبيفشلوا لو مسار اتكسر.",
                  "جدول أعلام فيه المالك وتاريخ الانتهاء وكيفية الإطفاء الفوري.",
                  "قياس لكل مسار (v1 مقابل v2) يمكن الاعتماد عليه في قرار الإطلاق.",
                  "دليل إطفاء فوري من الإعدادات بدون نشر (مخرجات قبل/بعد).",
                  "فحص CI يمنع الأعلام بلا تاريخ انتهاء.",
                  "ملاحظة صريحة عن الفرق بين العلم وcanary (سلوك مقابل نسخة).",
              ],
              "hint": "للاختبارات: اضبط الإعدادات في `WebApplicationFactory` بـ`ConfigureAppConfiguration` وأضف `FeatureManagement:Checkout:v2:EnabledFor:0:Name = Percentage` مع `Value = 100` أو `0` — كده تتحكم في المسار من الاختبار مباشرة. وللقياس: `Meter` من `System.Diagnostics.Metrics` بعدّادين (checkout_v1_total / checkout_v2_total) يظهروا في Prometheus/App Insights.",
              "solution": "البنية: `IFeatureManager` من الإعدادات + `AddFeatureFilter<PercentageFilter>()` و`TimeWindowFilter`. الـendpoint بيفحص `IsEnabledAsync` لكل طلب (أو `RequireFeatureGate` لإرجاع 404). الاختبارات: (1) مع Value=100 → الاستجابة فيها علامة المسار الجديد (2) مع Value=0 → المسار القديم. القياس: عدّادان يفرقوا المسارين في لوحة المراقبة — وده اللي بيخلي قرار الإطلاق مبنيًا على أرقام (مثلًا: v2 p95 أقل 20% ومعدل الأخطاء نفسه). الإطفاء الفوري: تغيير القيمة في App Configuration → الطلبات الجاية كلها على v1 خلال ثوانٍ (بلا نشر وبلا إعادة تشغيل، لو `ReloadInterval` مضبوط — 6.2.3). فحص CI: سكربت Python صغير يقرأ جدول `docs/feature-flags.md` ويفشل لو عمود «تاريخ الانتهاء» فاضي أو تاريخ منتهي — عشان الأعلام الميتة ما تتراكمش في الكود.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/azure-app-configuration/quickstart-aspnet-core-app",
                  "https://learn.microsoft.com/en-us/dotnet/api/microsoft.featuremanagement",
                  "https://github.com/microsoft/FeatureManagement-Dotnet",
                  "https://learn.microsoft.com/en-us/azure/azure-app-configuration/concept-feature-flags",
                  "https://martinfowler.com/articles/feature-toggles.html",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Container Apps: revisions وتقسيم الحركة", "url": "https://learn.microsoft.com/en-us/azure/container-apps/revisions"},
            {"label": "App Service: deployment slots وswap", "url": "https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots"},
            {"label": "ingress-nginx: تعليقات canary", "url": "https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/"},
            {"label": "Argo Rollouts", "url": "https://argo-rollouts.readthedocs.io/en/stable/"},
            {"label": "Kubernetes Deployment strategy", "url": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy"},
            {"label": "Canary Release (Martin Fowler)", "url": "https://martinfowler.com/bliki/CanaryRelease.html"},
            {"label": "Feature Toggles (Martin Fowler)", "url": "https://martinfowler.com/articles/feature-toggles.html"},
            {"label": "FeatureManagement-Dotnet", "url": "https://github.com/microsoft/FeatureManagement-Dotnet"},
            {"label": "Parallel Change (expand/contract)", "url": "https://martinfowler.com/bliki/ParallelChange.html"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s6-m3-l4 — Bicep وTerraform: البنية ككود
# ══════════════════════════════════════════════════════════════════════════
_L4 = {
    "id": "s6-m3-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "لو البنية التحتية اتعملت بالنقر في الـPortal، فإنت مش عندك بنية — عندك **حالة غير موثقة**. في الدرس ده: البنية ككود بـ**Bicep** (لغة Microsoft، بلا ملف حالة، دعم day-0 للموارد الجديدة) و**Terraform** (ملف حالة + lock + drift + multi-cloud). هتكتب نفس النظام (resource group · Container Apps env · PostgreSQL · Key Vault · Log Analytics) بالأداتين، وتفهم الفرق الجوهري: **ARM هو مصدر الحقيقة مقابل state file انت مسؤول عنه** — وإيه معنى `what-if` و`plan` وحدودهم، و**deployment stacks** اللي بتحذف الموارد اللي بطلت تصرّح بيها."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "IaC", "def": "البنية كمصدر يُراجع ويُختبر ويُراجع تاريخه: نفس مبادئ الكود (PRs · اختبارات · إصدارات)."},
            {"term": "Bicep", "def": "لغة DSL بتُترجم إلى ARM templates. **بلا ملف حالة**: Azure Resource Manager بيقارن القالب بالواقع وقت النشر. دعم فوري (day-0) لأي مورد جديد."},
            {"term": "ARM", "def": "طبقة إدارة الموارد في Azure: كل عملية إنشاء/تعديل بتعدي عليها، وهي مصدر الحقيقة اللي Bicep بيعتمد عليها."},
            {"term": "`targetScope`", "def": "نطاق النشر في Bicep: `resourceGroup` (الأشهر) · `subscription` · `managementGroup` · `tenant`. لازم يُصرَّح به صراحةً."},
            {"term": "`.bicepparam`", "def": "ملف قيم المعاملات لكل بيئة (dev/prod) — بديل `parameters.json` وأسهل قراءةً."},
            {"term": "`what-if`", "def": "معاينة التغييرات قبل النشر: `+ Create` · `- Delete` · `~ Modify` · `= NoChange` · `* Deploy` · `Ignore`. مكافئ `terraform plan` — **بحدود** (أدناه)."},
            {"term": "Deployment stack", "def": "ميزة ARM بتجمّع الموارد اللي أنشأها نشر معًا وتدعم `--action-on-unmanage detach|delete`: يعني **حذف الموارد اللي بطلت تصرّح بيها** — بلا stacks الموارد بتتراكم (orphans)."},
            {"term": "State file (Terraform)", "def": "ملف `terraform.tfstate` بيسجل ما أنشأته الأداة وربطه بالواقع. **حساس** (قد يحتوي قيمًا سرية نصًا) ولا يُرفع لـGit أبدًا؛ يُخزَّن في backend (Azure Storage) مع **قفل**."},
            {"term": "Drift", "def": "فرق بين الكود والواقع (حد عدّل من الـPortal). Terraform بيكشفه في `plan`؛ Bicep بيكشفه في `what-if` (بحدود)."},
            {"term": "Azure Verified Modules (AVM)", "def": "وحدات Microsoft مُختبَرة لكل من Bicep وTerraform، منشورة في سجل عام: `br/public:avm/res/<provider>/<type>:<version>`."},
            {"term": "السجل الخاص (Bicep)", "def": "وحدات منشورة في **ACR** كـOCI artifacts: `br:myacr.azurecr.io/bicep/modules/storage:1.2.0`. النطاقات المسموحة: `*.azurecr.io` · `mcr.microsoft.com` · `ghcr.io`."},
            {"term": "`@secure()` و`getSecret()`", "def": "في Bicep: معامل سري لا يظهر في السجلات، وقراءة سر من Key Vault **كمرجع** وقت النشر (لا قيمة مكتوبة في الملف)."},
            {"term": "OpenTofu", "def": "فرع من Terraform بترخيص MPL متوافق معه — خيار لو الترخيص مشكلة عندك."},
        ]},

        # ── 1) القرار
        {"type": "heading", "level": 2, "text": "① Bicep مقابل Terraform: قرار 2026"},
        {"type": "table", "caption": "الاتنين بيشتغلوا مع OIDC وCI/CD — الفرق في نموذج الحالة والنطاق",
         "head": ["المعيار", "Bicep", "Terraform (azurerm 4.x)"],
         "rows": [
             ["المصدر للحقيقة", "**ARM نفسه** (بلا ملف حالة)", "**state file** مخزّن في backend + قفل"],
             ["المسؤولية التشغيلية", "أقل: مفيش backend ولا قفل ولا جراحة حالة", "أكثر: backend + قفل + `state mv/rm/import` عند اللزوم"],
             ["دعم مورد جديد", "**day-0** (مباشرة من ARM API)", "ينتظر تحديث الـprovider (أو استخدم `azapi`)"],
             ["كشف الانحراف والحذف", "`what-if` + **deployment stacks** للحذف عند إلغاء التصريح", "`plan` بيكشف الانحراف **وبيحذف** الموارد المزالة من الكود (سلوك أساسي)"],
             ["النطاقات", "4 نطاقات أصلية في ملف واحد (`targetScope`)", "يحتاج provider blocks وإسناد أدوار لكل نطاق"],
             ["multi-cloud / مزودون خارجيون", "Azure فقط (+ امتداد Microsoft Graph)", "**أي مزود**: AWS/GCP/Cloudflare/GitHub/… (أكبر سجل وحدات)"],
             ["الوحدات", "AVM (عام في MCR) + سجل خاص في ACR", "AVM + Terraform Registry (أكبر بكتير)"],
             ["المعاينة قبل التطبيق", "`az deployment group what-if` (فيه noise في بعض الموارد)", "`terraform plan` — والمطبق **نفس الملف** المُراجَع (أدق)"],
             ["الأسرار", "`@secure()` + `getSecret()` من Key Vault", "variables حساسة + **state يحتوي قيمًا نصًا** → حماية مشددة"],
             ["منحنى التعلم لفريق .NET", "أقرب (لغة Microsoft، تكامل مع az CLI)", "HCL + مفاهيم الحالة والقفل"],
             ["الأنسب", "**Azure-only ومشروع جديد** · فرق بتحب البساطة", "**multi-cloud** · تكامل مع SaaS · بنية موجودة بالفعل على Terraform"],
         ]},
        {"type": "callout", "kind": "note", "title": "قرار عملي (مش «الأفضل مطلقًا»)",
         "md": "**Azure فقط ومشروع جديد → Bicep**: بلا backend ولا state ولا قفل، ودعم فوري للموارد الجديدة، وAVM بيغطيلك أغلب الأنماط. **عندك AWS/GCP أو مزودون خارجيون (Cloudflare/GitHub) أو بنية Terraform موجودة → خليك على Terraform**: تكلفة الترحيل أعلى من المكسب. **عندك ARM templates قديمة → `az bicep decompile`** لترقيتها. **الترخيص مشكلة → OpenTofu** (متوافق مع Terraform). والأهم: **اختار أداة واحدة والتزم بيها** — أداتين معًا = مصدرين للحقيقة = انحراف مؤكد."},

        # ── 2) Bicep
        {"type": "heading", "level": 2, "text": "② Bicep: نفس النظام كاملًا"},
        {"type": "code", "lang": "text", "title": "infra/main.bicep", "filename": "infra/main.bicep", "code": r'''targetScope = 'resourceGroup'          // صرّح بالنطاق دائمًا

// ── معاملات: موثقة ومقيدة ──
@description('بادئة أسماء الموارد (حروف وأرقام، بلا شرطات في بعض الخدمات)')
@minLength(3)
@maxLength(12)
param namePrefix string

@description('البيئة')
@allowed([ 'dev', 'staging', 'prod' ])
param environment string = 'dev'

@description('المنطقة — كل الموارد في منطقة واحدة لتقليل latency وegress')
param location string = resourceGroup().location

@description('طبقة حوسبة PostgreSQL')
@allowed([ 'Burstable', 'GeneralPurpose', 'MemoryOptimized' ])
param pgTier string = 'Burstable'

@description('هل نفعّل HA (يضاخف الحوسبة تقريبًا — 6.2.4)')
param enableHa bool = false

@description('مدة الاحتفاظ بالسجلات بالأيام')
@minValue(7)
@maxValue(730)
param logRetentionDays int = 30

@description('معرّف كائن Entra ID لمدير قاعدة البيانات (مصادقة Entra بدل كلمة السر)')
param pgAdminObjectId string

@secure()
@description('مفتاح Log Analytics — يُمرَّر كمرجع Key Vault من ملف .bicepparam (getSecret)')
param laSharedKey string

// ⚠ أسماء مخرجات وحدات AVM بتختلف بين الإصدارات (workspaceId / uri / resourceId):
//   راجع README الوحدة المثبتة قبل ما تعتمد على اسم مخرج.
// ⚠ getSecret() مكانها الموثّق = ملف المعاملات (.bicepparam)، لا القالب نفسه.

// ── مشتقات (لا تكرر الأسماء يدويًا) ──
var suffix = '${namePrefix}-${environment}'
var commonTags = {
  project: 'shop'
  env: environment
  owner: 'platform'
  managedBy: 'bicep'                    // يوضح إن التعديل اليدوي = drift
}

// ── وحدات AVM من السجل العام (ثبّت الإصدار دائمًا) ──
// تحقق من أحدث إصدار: https://aka.ms/avm أو سجل mcr.microsoft.com/bicep
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'logAnalytics'
  params: {
    name: 'la-${suffix}'
    location: location
    retentionInDays: logRetentionDays
    tags: commonTags
  }
}

module keyVault 'br/public:avm/res/key-vault/vault:0.10.1' = {
  name: 'keyVault'
  params: {
    name: 'kv-${suffix}'
    location: location
    enableRbacAuthorization: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    tags: commonTags
  }
}

// ── مورد خام (بدون AVM) — لاحظ تصريح API version والتحقق منها ──
//   az provider show --namespace Microsoft.DBforPostgreSQL \
//     --query "resourceTypes[?resourceType=='flexibleServers'].apiVersions[0]" -o tsv
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: 'pg-${suffix}'
  location: location
  sku: pgTier == 'Burstable' ? {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  } : {
    name: 'Standard_D2ds_v5'
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '17'                       // تحقق من الإصدارات المدعومة حاليًا
    storage: {
      storageSizeGB: environment == 'prod' ? 128 : 32
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: environment == 'prod' ? 30 : 7
      geoRedundantBackup: enableHa ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: enableHa ? 'ZoneRedundant' : 'Disabled'
    }
    administrators: [                   // مصادقة Entra ID بدل كلمة سر (6.2.3)
      {
        administratorType: 'ActiveDirectory'
        login: 'deploy-mi'
        sid: pgAdminObjectId
        tenantId: tenant().tenantId
      }
    ]
  }
  tags: commonTags
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'env-${suffix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.outputs.workspaceId
        // سر يُقرأ من Key Vault كمرجع — لا قيمة في الملف:
        sharedKey: laSharedKey
      }
    }
  }
  tags: commonTags
}

// ── موارد مشروطة: private endpoint للإنتاج فقط ──
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = if (environment == 'prod') {
  name: 'pe-pg-${suffix}'
  location: location
  properties: {
    subnet: { id: '/subscriptions/${subscription().subscriptionId}/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-shop/subnets/snet-data' }
    privateLinkServiceConnections: [
      {
        name: 'pg-connection'
        properties: {
          privateLinkServiceId: postgres.id
          groupIds: [ 'postgresqlServer' ]
        }
      }
    ]
  }
  tags: commonTags
}

// ── مخرجات: تُستخدم في CI (نشر التطبيق) — لا تُسرِّب قيمًا حساسة ──
output containerAppsEnvironmentId string = containerAppsEnv.id
output postgresFqdn string = postgres.properties.fqdn
output keyVaultUri string = keyVault.outputs.uri
output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceId
'''},
        {"type": "code", "lang": "json", "title": "infra/prod.bicepparam مقابل dev", "filename": "infra/prod.bicepparam", "code": r'''using './main.bicep'

param namePrefix = 'shop'
param environment = 'prod'
param location = 'westeurope'
param pgTier = 'GeneralPurpose'
param enableHa = true
param logRetentionDays = 90

// قيمة سرية كمرجع Key Vault — getSecret() مكانها هنا (ملف المعاملات):
param laSharedKey = keyVault.getSecret('la-shared-key')
param pgAdminObjectId = '<OBJECT_ID_OF_DEPLOY_MI>'

// ───────── dev.bicepparam ─────────
// param environment = 'dev'
// param pgTier = 'Burstable'
// param enableHa = false          // لا HA في التطوير (6.2.4)
// param logRetentionDays = 30     // احتفاظ أقل = أرخص (6.2.5)
// param laSharedKey = keyVault.getSecret('la-shared-key')
// param pgAdminObjectId = '<OBJECT_ID>'
'''},
        {"type": "code", "lang": "bash", "title": "infra/bicep-ops.sh — بناء · معاينة · نشر · stacks", "filename": "infra/bicep-ops.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
RG=rg-shop-prod

# ═══ 1) الأدوات والتحليل الثابت ═══
az bicep version
az bicep install            # أو az bicep upgrade
# الـlinter بيشتغل ضمن build (تحذيرات) وفي إضافة VS Code — مفيش أمر lint مستقل:
az bicep build --file infra/main.bicep           # يولّد ARM JSON + أخطاء/تحذيرات التحليل
az bicep generate-params --file infra/main.bicep --output-format bicepparam
az bicep format --file infra/main.bicep          # تنسيق موحّد (زي dotnet format)
az bicep version                                 # وثبّت الإصدار في CI: az bicep install --version …

# ═══ 2) المعاينة قبل النشر — خطوة إلزامية في الإنتاج ═══
az deployment group what-if \
  --resource-group "$RG" \
  --template-file infra/main.bicep \
  --parameters infra/prod.bicepparam \
  --result-format FullResourcePayloads | tee artifacts/whatif.txt
# الرموز: + Create · - Delete · ~ Modify · = NoChange · * Deploy · Ignore
# ⚠ Create لمورد موجود = اسم/نوع/نطاق غلط (هينشئ نسخة مكررة) — أصلحه قبل النشر.
# ⚠ Delete = اقرأه مرتين؛ قد يكون موردًا عليه بيانات.

# ═══ 3) النشر (تزايدى افتراضيًا: لا يحذف ما بطلتَ تصرّح به) ═══
az deployment group create \
  --resource-group "$RG" \
  --name "deploy-$(date +%Y%m%d-%H%M)" \
  --template-file infra/main.bicep \
  --parameters infra/prod.bicepparam \
  --confirm-with-what-if               # يطالبك بتأكيد الفرق قبل التطبيق

# ═══ 4) Deployment stack: إدارة دورة حياة كاملة (حذف غير المُصرَّح به) ═══
az stack group create \
  --name shop-prod-stack \
  --resource-group "$RG" \
  --template-file infra/main.bicep \
  --parameters infra/prod.bicepparam \
  --action-on-unmanage detach \
  --deny-settings-mode denyDelete \
  --yes
# الأعلام أعلاه: detach = اترك المورد غير المُدار؛ delete = احذفه (احذر — جرّبه على dev).
#   denyDelete = يمنع الحذف اليدوي من الـPortal.
az stack group list --resource-group "$RG" -o table
az stack group show --name shop-prod-stack --resource-group "$RG" -o json | head -n 40
# ⚠ --action-on-unmanage delete بيحذف موارد فعلًا: جرّبه على dev أولًا، وافهم الفرق.

# ═══ 5) وحدات خاصة في سجل ACR (إعادة استخدام بين المشروعات) ═══
az bicep publish --file infra/modules/postgres.bicep \
  --target br:acrshopprod.azurecr.io/bicep/modules/postgres:v1.2.0
# bicepconfig.json: عرّف alias للسجل عشان ما تكررش الـFQDN في كل ملف:
#   { "moduleAliases": { "br": { "shop": { "registry": "acrshopprod.azurecr.io", "modulePath": "bicep/modules" } } } }
# ثم الاستهلاك:  module pg 'br/shop:postgres:v1.2.0' = { … }

# ═══ 6) ترحيل ARM قديم → Bicep ═══
az bicep decompile --file legacy/template.json
# ═══ 7) التحقق بعد النشر من الخصائص الأمنية (what-if له نقاط عمياء) ═══
az postgres flexible-server show -n pg-shop-prod -g "$RG" \
  --query "{publicAccess:properties.network.publicNetworkAccess,ha:properties.highAvailability.mode}" -o json
az keyvault show -n kv-shop-prod -g "$RG" \
  --query "{rbac:properties.enableRbacAuthorization,purge:properties.enablePurgeProtection}" -o json
'''},

        # ── 3) حدود what-if
        {"type": "heading", "level": 2, "text": "③ حدود المعاينة: `what-if` مش `terraform plan`"},
        {"type": "table", "caption": "نقاط عمياء موثقة — وده سبب خطوة التحقق بعد النشر",
         "head": ["الحالة", "اللي بيحصل", "التصرف"],
         "rows": [
             ["خصائص ما صرّحتش بها في القالب وقيمتها الافتراضية مضبوطة من الخدمة",
              "قد تُبلَّغ خطأً كـ**Delete** (noise)",
              "اقرأ الـdiff على مستوى الخصائص، وأضف الخصائص المهمة صراحةً للقالب"],
             ["تعبيرات لا تُقيَّم خارج النشر: `reference()` · `listKeys()` · معاملات `@secure` · `utcNow()`",
              "**تظهر دائمًا كتغيير** حتى لو مفيش فرق",
              "توقّعها واستبعدها ذهنيًا من الحكم؛ لا تُلغي النشر بسببها"],
             ["تغيير أمني حساس (NSG rules · RBAC · firewall · public access)",
              "أحيانًا يُبلَّغ كـ**NoChange** رغم إنه بيتغير",
              "**تحقق بعد النشر** بـ`az resource show` أو بـAzure Policy compliance — لا تعتمد على المعاينة وحدها"],
             ["مورد موجود بالفعل واسمه/نوعه مطابق جزئيًا",
              "يظهر كـ**Create** → نشره ينشئ نسخة مكررة بدل تبنّيه",
              "أصلح الاسم/النطاق حتى يختفي الـCreate، أو استخدم **import**/stacks للتبني"],
             ["حذف مورد من الكود (نشر عادي بلا stacks)",
              "**لا يُحذف** — يتراكم كمورد يتيم بيتفوتر",
              "استخدم deployment stacks بـ`--action-on-unmanage` أو احذفه يدويًا ووثّق"],
             ["تغيير في Terraform",
              "`plan` بيكشف الانحراف والحذف، والملف المطبَّق **نفس** المُراجَع",
              "مرّر ملف الـplan من job المراجعة لـjob التطبيق (`terraform plan -out` ثم `apply plan.tfplan`)"],
         ]},

        # ── 4) Terraform
        {"type": "heading", "level": 2, "text": "④ Terraform: نفس النظام بنموذج الحالة"},
        {"type": "code", "lang": "text", "title": "infra-tf/versions.tf + providers.tf + backend", "filename": "infra-tf/versions.tf", "code": r'''terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"          # ثبّت الخط الرئيسي؛ راجع CHANGELOG قبل 5.x
    }
  }

  # الحالة في Azure Storage (لا في Git) + قفل:
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstateshop"
    container_name       = "tfstate"
    key                  = "shop-prod.tfstate"
    use_oidc             = true    # مصادقة بلا secret (نفس فكرة 6.3.1)
    # client_id / subscription_id / tenant_id تُمرَّر كمتغيرات بيئة في CI:
    #   ARM_CLIENT_ID · ARM_SUBSCRIPTION_ID · ARM_TENANT_ID · ARM_USE_OIDC=true
  }
}
'''},
        {"type": "code", "lang": "text", "title": "infra-tf/main.tf", "filename": "infra-tf/main.tf", "code": r'''provider "azurerm" {
  features {
    resource_group { prevent_deletion_if_contains_resources = true }   # حماية من حذف غير مقصود
    key_vault      { purge_soft_delete_on_destroy = false }            # لا تمسح soft-deleted
  }
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  use_oidc        = true
}

locals {
  suffix = "${var.name_prefix}-${var.environment}"
  tags = {
    project   = "shop"
    env       = var.environment
    managedBy = "terraform"
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-shop-${var.environment}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "la-${local.suffix}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days      # 30 للتطوير، 90 للإنتاج (6.2.5)
  tags                = local.tags
}

resource "azurerm_key_vault" "this" {
  name                       = "kv-${local.suffix}"
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 90
  tags                       = local.tags
}

# PostgreSQL Flexible Server — طبقة Burstable للتطوير (6.2.4):
resource "azurerm_postgresql_flexible_server" "this" {
  name                   = "pg-${local.suffix}"
  resource_group_name    = azurerm_resource_group.this.name
  location               = azurerm_resource_group.this.location
  sku_name               = var.pg_sku            # "Standard_B1ms" أو "Standard_D2ds_v5"
  version                = "17"
  backup_retention_days  = var.environment == "prod" ? 30 : 7
  storage_mb             = var.environment == "prod" ? 131072 : 32768
  zone_redundant_ha_enabled = var.enable_ha      # يضاعف الحوسبة تقريبًا

  # مصادقة Entra ID بدل كلمة سر (6.2.3):
  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = false
  }

  tags = local.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = "env-${local.suffix}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = azurerm_resource_group.this.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  tags                       = local.tags
}

# ── وحدة AVM لـTerraform (بديل كتابة الموارد يدويًا) ──
# module "storage" {
#   source  = "Azure/avm-res-storage-storageaccount/azurerm"
#   version = "~> 0.4"          # ثبّت الإصدار وراجع CHANGELOG
#   name    = "st${replace(local.suffix, "-", "")}"
#   ...
# }

# ── مخرجات: تُستهلك في CI (نشر التطبيق) ──
output "postgres_fqdn" { value = azurerm_postgresql_flexible_server.this.fqdn }
output "keyvault_uri"  { value = azurerm_key_vault.this.vault_uri }
output "aca_env_id"    { value = azurerm_container_app_environment.this.id }

# ⚠ لا تُخرج قيمًا حساسة:  output "x" { value = … ; sensitive = true }
# ⚠ ملف الحالة قد يحتوي قيمًا نصًا (بما فيها ما يُعتبر سريًا) →
#   خزّنه في backend مشفّر + صلاحيات ضيقة + بلا رفع لـGit.
'''},
        {"type": "code", "lang": "bash", "title": "infra-tf/tf-ops.sh — init · plan · apply · حالة", "filename": "infra-tf/tf-ops.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
cd infra-tf

# ═══ 1) التهيئة والمصادقة بـOIDC (بلا secret) ═══
export ARM_USE_OIDC=true
export ARM_CLIENT_ID="$AZURE_CLIENT_ID"
export ARM_SUBSCRIPTION_ID="$AZURE_SUBSCRIPTION_ID"
export ARM_TENANT_ID="$AZURE_TENANT_ID"
terraform init -input=false -reconfigure
terraform version && terraform providers

# ═══ 2) المعاينة كملف (يُراجَع ثم يُطبَّق كما هو — نفس البايتات) ═══
terraform fmt -check -recursive
terraform validate
terraform plan -var-file="prod.tfvars" -out=tfplan -input=false -detailed-exitcode
CODE=$?   # 0 = لا تغييرات · 1 = خطأ · 2 = فيه تغييرات
echo "plan exit code: $CODE"
terraform show -no-color tfplan > artifacts/plan.txt      # يُنشر كتعليق على الـPR

# ═══ 3) التطبيق بعد الموافقة البشرية (6.3.5) ═══
terraform apply -input=false tfplan
# ⚠ لا تستخدم `terraform apply -auto-approve` في الإنتاج.

# ═══ 4) تبني مورد موجود (من Portal) بدل إعادة إنشائه ═══
terraform import azurerm_resource_group.this /subscriptions/<SUB>/resourceGroups/rg-shop-prod
# أو (أحدث) كتلة import في الكود:
#   import { to = azurerm_key_vault.this  id = "/subscriptions/…/vaults/kv-shop-prod" }

# ═══ 5) عمليات الحالة (احذر — كل واحدة بتغيّر الحقيقة المسجلة) ═══
terraform state list | head -n 30
terraform state show azurerm_postgresql_flexible_server.this | head -n 40
terraform state mv azurerm_key_vault.this module.kv.azurerm_key_vault.this   # إعادة هيكلة
terraform state rm azurerm_resource_group.old                                # إزالة من الإدارة (لا حذف)

# ═══ 6) كشف الانحراف دوريًا (لو حد عدّل من Portal) ═══
terraform plan -var-file="prod.tfvars" -detailed-exitcode -input=false | tee artifacts/drift.txt
# كود خروج 2 = فيه فرق بين الكود والواقع → افتح issue وصحّح الكود (لا الواقع) عادةً

# ═══ 7) فحص أمني للحالة والإعدادات (tfsec/checkov) ═══
# تحقق من الأداة الحالية واسم الأمر في إصدارك:
#   checkov -d . --framework terraform --quiet
#   tfsec .
'''},

        # ── 5) CI/CD للبنية
        {"type": "heading", "level": 2, "text": "⑤ CI/CD للبنية: معاينة في الـPR ونشر بعد موافقة"},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/infra.yml", "filename": ".github/workflows/infra.yml", "code": r'''name: Infrastructure

on:
  pull_request:
    paths: ["infra/**", ".github/workflows/infra.yml"]
  push:
    branches: [main]
    paths: ["infra/**"]

permissions:
  contents: read
  pull-requests: write      # لنشر المعاينة كتعليق

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2                # OIDC بصلاحيات قراءة فقط للتحقق
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Build & lint Bicep
        run: |
          az bicep build --file infra/main.bicep
          az bicep generate-params --file infra/main.bicep --output-format bicepparam
      # تحقق بلا صلاحية نشر (Azure CLI ≥ 2.76):
      - name: What-If (validation only)
        if: github.event_name == 'pull_request'
        run: |
          az deployment group what-if \
            --resource-group rg-shop-dev \
            --template-file infra/main.bicep \
            --parameters infra/dev.bicepparam \
            --validation-level Template ProviderNoRbac \
            --result-format ResourceIdOnly > artifacts/whatif.txt
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('artifacts/whatif.txt', 'utf8').slice(0, 60000);
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '### Bicep what-if\n```\n' + body + '\n```'
            });

  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: validate
    runs-on: ubuntu-latest
    environment: production        # required reviewers → موافقة قبل تغيير البنية
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: What-If ثم النشر
        run: |
          set -euo pipefail
          az deployment group what-if -g rg-shop-prod \
            --template-file infra/main.bicep --parameters infra/prod.bicepparam | tee whatif.txt
          if grep -qE '^\s*- ' whatif.txt; then
            echo "⚠ فيه موارد هتتحذف — راجع whatif.txt قبل المتابعة"; exit 1
          fi
          az deployment group create -g rg-shop-prod \
            --name "deploy-${{ github.run_number }}-${{ github.sha }}" \
            --template-file infra/main.bicep --parameters infra/prod.bicepparam
      - name: تحقق من الخصائص الأمنية بعد النشر
        run: |
          az keyvault show -n kv-shop-prod -g rg-shop-prod \
            --query "{rbac:properties.enableRbacAuthorization,purge:properties.enablePurgeProtection}" -o json
          az postgres flexible-server show -n pg-shop-prod -g rg-shop-prod \
            --query "{public:properties.network.publicNetworkAccess}" -o json
'''},
        {"type": "callout", "kind": "danger", "title": "8 أخطاء في البنية ككود (كل واحد حصل فعلًا في الإنتاج)",
         "md": "**① رفع `terraform.tfstate` لـGit**: قد يحتوي قيمًا سرية نصًا → backend مشفّر + صلاحيات ضيقة. **② تعديل من الـPortal**: انحراف صامت → اجعل `managedBy` tag + سياسة «كل تغيير عبر PR». **③ نشر بلا `plan`/`what-if`**: حذف غير مقصود لموارد عليها بيانات. **④ أسرار مكتوبة في الملفات أو ملفات المعاملات**: استخدم `@secure()` + `getSecret()` (Bicep) أو Key Vault/data sources (Terraform). **⑤ قالب/ملف ضخم واحد**: انفجار نصف القطر → وحدات لكل مجال (network · data · app) ونشرات منفصلة. **⑥ إصدارات وحدات غير مثبتة** (`~>` واسع أو بلا إصدار): تحديث بيقفل البناء → ثبّت وراجع CHANGELOG. **⑦ بلا قفل على الحالة المشتركة**: `apply` متزامن بيفسد الحالة → backend بقفل + `plan -out` في CI. **⑧ الاعتماد على المعاينة وحدها للأمان**: تحقق بعد النشر من NSG/RBAC/firewall/public access."},

        {"type": "steps", "title": "⑥ تبني IaC لمشروع موجود (من Portal إلى كود) — 6 خطوات",
         "items": [
             {"title": "1) صدّر الواقع الحالي",
              "md": "Bicep: `az resource group export` بيطلع ARM JSON ثم `az bicep decompile`. Terraform: `import` blocks أو `terraform import` لكل مورد. الهدف: كود يصف ما هو موجود فعلًا **بدون أي تغيير**.",
              "code": "az group export -g rg-shop-prod > artifacts/current.json\naz bicep decompile --file artifacts/current.json   # راجع الناتج ونظّفه — التصدير الخام فوضوي"},
             {"title": "2) أثبت إن الكود = الواقع (لا تغييرات)",
              "md": "شغّل `what-if`/`plan` حتى يرجع **NoChange** لكل الموارد. أي `Create` لمورد موجود = اسم/نوع/نطاق غلط. دي أهم خطوة: لو عدّيتها، أول نشر هيكرّر موارد.",
              "code": "az deployment group what-if -g rg-shop-prod --template-file infra/main.bicep --parameters infra/prod.bicepparam --result-format ResourceIdOnly | grep -E '^\\s*[+~-]' || echo 'لا تغييرات ✓'"},
             {"title": "3) نظّف القالب: معاملات · وسوم · وحدات",
              "md": "استخرج القيم المتغيرة لمعاملات (بيئة/منطقة/طبقة)، أضف وسومًا موحدة، وقسّم إلى وحدات (`modules/network.bicep` · `modules/data.bicep`). لا تخلط أسماء مكتوبة يدويًا.",
              "code": ""},
             {"title": "4) افصل البيئات بملفات معاملات",
              "md": "`dev.bicepparam` / `prod.bicepparam` (أو `dev.tfvars`/`prod.tfvars`) — مع **مجموعات موارد منفصلة** (لا بيئة مشتركة). وخلي dev بلا HA وباحتفاظ سجلات أقل (6.2.4/6.2.5).",
              "code": ""},
             {"title": "5) أدخله CI: تحقق في الـPR ونشر بعد موافقة",
              "md": "`what-if`/`plan` كتعليق على الـPR (بـ`--validation-level` لو الصلاحيات محدودة)، ثم نشر من job مربوط بـ`environment: production` فيه required reviewers (6.3.5).",
              "code": ""},
             {"title": "6) اضبط إدارة دورة الحياة والانحراف",
              "md": "Bicep: deployment stack بـ`--action-on-unmanage` عشان الموارد المُزالة تتحذف أو تتفصل بوعي. Terraform: `plan` دوري (أسبوعيًا) لكشف الانحراف + issue لأي فرق. وسياسة مكتوبة: **مفيش تعديل من الـPortal إلا في حادث، وبعده PR يُحدّث الكود**.",
              "code": ""},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق الجوهري: Bicep بلا حالة (ARM مصدر الحقيقة) مقابل Terraform بملف حالة + backend + قفل.",
            "أقدر أختار الأداة بمعايير: Azure-only/جديد → Bicep · multi-cloud أو بنية موجودة → Terraform.",
            "أقدر أكتب Bicep فيه `targetScope` · معاملات موثقة ومقيدة · وسوم · وحدات AVM مثبّتة الإصدار · موارد مشروطة · مخرجات.",
            "أعرف رموز `what-if` الستة وحدوده (noise · تعبيرات لا تُقيَّم · تغييرات أمنية بتظهر NoChange) وأتحقق بعد النشر.",
            "أعرف إن النشر العادي **لا يحذف** الموارد المُزالة من الكود، وإن deployment stacks بـ`--action-on-unmanage` هو الحل.",
            "أقدر أهيّئ Terraform بـbackend azurerm وOIDC، وأعمل `plan -out` ثم `apply` لنفس الملف، وأفهم حساسية ملف الحالة.",
            "أعرف خطة تبني IaC لمشروع موجود (تصدير → إثبات NoChange → تنظيف → بيئات → CI → دورة حياة).",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الأداتين والمعاينة.",
         "questions": [
             {"q": "ليه Bicep «بلا ملف حالة» ميزة ومسؤولية أقل؟",
              "options": ["لأنه أسرع", "**لأن ARM نفسه مصدر الحقيقة: مفيش backend تؤمّنه ولا قفل ولا جراحة حالة ولا خطر تسريب قيم سرية من ملف الحالة**", "لأنه بيدعم multi-cloud", "لأنه بيحذف الموارد تلقائيًا"],
              "answer": 1,
              "explain": "الثمن: من غير deployment stacks، الموارد اللي بتزيلها من الكود **ما بتتحذفش** (بتتراكم وتتفوتر). Terraform بيحذفها كسلوك أساسي — بس بيقابله مسؤولية الحالة والقفل."},
             {"q": "`what-if` أظهر `+ Create` لخادم PostgreSQL موجود فعلًا. تعمل إيه؟",
              "options": ["انشر عادي", "**أصلح الاسم/النوع/النطاق في القالب حتى يختفي الـCreate** — وإلا هتنشئ نسخة مكررة (وخادم جديد بيتفوتر)", "احذف الخادم الحالي", "استخدم Terraform"],
              "answer": 1,
              "explain": "ده أشهر فشل في تبني IaC: الكود ما بيطابقش الواقع. القاعدة: المعاينة لازم ترجع `NoChange` قبل أول نشر حقيقي."},
             {"q": "شلت موردًا من `main.bicep` ونشرت. إيه اللي حصل للمورد في Azure؟",
              "options": ["اتحذف", "**فضل موجود وبيتفوتر** — النشر العادي تزايدي؛ الحذف يحتاج deployment stack بـ`--action-on-unmanage delete/detach` أو حذفًا يدويًا", "اتوقف", "اتنقل لمجموعة تانية"],
              "answer": 1,
              "explain": "علشان كده الموارد اليتيمة بتتراكم. في Terraform الحذف تلقائي من `plan`/`apply` — وده سبب إن `plan` لازم يُقرأ قبل التطبيق."},
             {"q": "ليه `terraform apply` في CI لازم يطبّق **ملف الـplan** المحفوظ؟",
              "options": ["أسرع", "**عشان التغيير المطبَّق يكون مطابقًا بالبايت للتغيير المُراجَع في الـPR** — `apply` جديد ممكن يقيّم الظروف بشكل مختلف (وقت/حالة/اعتماديات)", "أقل صلاحيات", "بيقلل حجم الحالة"],
              "answer": 1,
              "explain": "`terraform plan -out=tfplan` ثم `terraform apply tfplan` — النمط القياسي للمراجعة الحقيقية. وده فرق دقيق بيتميز فيه Terraform عن what-if في Bicep."},
             {"q": "أمان: إيه الغلط الأخطر في Terraform؟",
              "options": ["استخدام modules", "**رفع `terraform.tfstate` لمستودع Git**: قد يحتوي قيمًا حساسة نصًا → backend مشفّر بصلاحيات ضيقة + قفل", "`terraform fmt`", "تثبيت إصدار الـprovider"],
              "answer": 1,
              "explain": "ملف الحالة سجل كامل لكل ما أُنشئ، وقيم بعض الخصائص بتُخزَّن فيه كنص. الحماية: backend (Azure Storage) + تشفير + صلاحيات محدودة + بلا نسخ محلية مشتركة + `sensitive = true` في المخرجات."},
             {"q": "تحققت من `what-if` وكله `NoChange`. هل كده الخصائص الأمنية مؤكدة؟",
              "options": ["نعم دائمًا", "**لا**: بعض التغييرات الحساسة (NSG/RBAC/firewall/public access) قد تُبلَّغ كـNoChange، وتعبيرات مثل `listKeys()`/`utcNow()`/`@secure` لا تُقيَّم خارج النشر → تحقق بعد النشر بـ`az resource show` أو Policy", "لا لأن what-if غير موثوق", "نعم لو استخدمت FullResourcePayloads"],
              "answer": 1,
              "explain": "المعاينة أداة قوية لكن لها نقاط عمياء موثقة. القاعدة العملية: الخصائص الأمنية تُتحقق **بعد** النشر بأمر صريح أو سياسة Azure Policy."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "بنية كاملة ككود + تبني واقع موجود.",
         "items": [
             {"id": "t1", "title": "مهمة 1: اكتب بنيتك كاملة بـBicep (أو Terraform) وانشرها",
              "md": "**السياق:** نظام `shop` على Azure: resource group · Container Apps environment · تطبيق · PostgreSQL Flexible · Key Vault · Storage · Log Analytics.\n\n**المطلوب:**\n1. اختَر الأداة واكتب **ADR** (`docs/adr/0017-iac-tool.md`) بمعايير القرار (Azure-only؟ multi-cloud؟ خبرة الفريق؟ بنية موجودة؟).\n2. `infra/main.bicep` (أو `infra-tf/main.tf`) بمعاملات موثقة ومقيدة (`@allowed`/`@minValue`) + وسوم موحدة فيها `managedBy` + **وحدات AVM مثبّتة الإصدار** لموردين على الأقل.\n3. ملفا معاملات: `dev` (Burstable · بلا HA · احتفاظ 30 يومًا) و`prod` (GeneralPurpose · HA · 90 يومًا) — **ومجموعتا موارد منفصلتان**.\n4. الأسرار بـ`getSecret()`/Key Vault (لا قيمة في الملفات) + مصادقة Entra ID لقاعدة البيانات (بلا password).\n5. **معاينة إلزامية**: سكربت يشغّل `what-if`/`plan` ويطبع الملخص، ويفشل لو فيه `- Delete` غير متوقع.\n6. نشر فعلي لـdev ثم prod (أو dev فقط لو الميزانية محدودة) + **تحقق بعد النشر** من 3 خصائص أمنية (`enableRbacAuthorization` · `enablePurgeProtection` · `publicNetworkAccess`) بأمر صريح.\n7. اكتب `docs/iac-runbook.md`: إزاي أضيف موردًا · إزاي أغيّر طبقة · إزاي أتعامل مع الانحراف · وإزاي أحذف موردًا (bلا stacks / بـstacks).\n8. (Bicep) أنشئ deployment stack على dev بـ`--action-on-unmanage detach` وارفع/احذف موردًا من الكود لتوضيح الفرق — ووثّق النتيجة.",
              "criteria": [
                  "ADR يبرر الأداة بمعايير واضحة (مش تفضيل).",
                  "معاملات موثقة بـdecorators وقيم مقيدة + وسوم فيها `managedBy`.",
                  "وحدتا AVM على الأقل بإصدارات مثبتة (بلا `latest`).",
                  "ملفا معاملات لبيئتين **بمجموعتي موارد منفصلتين** وفروق واضحة (طبقة/HA/احتفاظ).",
                  "صفر أسرار في الملفات + مصادقة Entra ID لقاعدة البيانات.",
                  "سكربت معاينة يفشل عند `Delete` غير متوقع، ومُختبَر بتجربة (احذف موردًا من الكود وشوف النتيجة).",
                  "نشر فعلي + تحقق **بعد** النشر من 3 خصائص أمنية بمخرجات.",
                  "runbook فيه إضافة/تغيير/انحراف/حذف.",
                  "(Bicep) تجربة deployment stack موثقة بالفرق عن النشر العادي.",
              ],
              "hint": "أسهل مسار لو مفيش Azure عندك: اكتب الكود وشغّل `az bicep build` (يترجم ويكشف الأخطاء من غير نشر) + `az deployment group validate` (يتحقق من الصلاحيات والمخطط بدون إنشاء). ولو عندك اشتراك، ابدأ بـdev فقط وخلي الموارد قابلة للحذف (`az group delete`). وللـAPI versions: استخدم الأمر `az provider show --namespace … --query resourceTypes[…]` بدل ما تنسخ إصدارًا من مقال قديم.",
              "solution": "الهيكل الناتج: `infra/main.bicep` (المعاملات + الوسوم + 3 وحدات AVM: log-analytics · key-vault · storage + موارد خام لـPostgreSQL وACA environment + private endpoint مشروط بالإنتاج) و`infra/dev.bicepparam` و`infra/prod.bicepparam` و`infra/bicep-ops.sh` و`docs/iac-runbook.md`. ADR نموذجي: Bicep لأن النظام Azure-only ومشروع جديد والفريق .NET (بلا خبرة Terraform)، والعواقب: بلا ملف حالة (أبسط) مقابل حاجة لـdeployment stacks للحذف، وبدعم day-0 للموارد الجديدة. التحقق بعد النشر بيكشف عادةً إن `publicNetworkAccess` لسه `Enabled` (الافتراضي) رغم إن القالب كان يقصد private endpoint → تُصلح بإضافة الخاصية صراحةً (مثال حي على حدود المعاينة). تجربة الـstack: حذف مورد من الكود مع `detach` بيخليه يبقى في Azure ويخرج من إدارة الـstack؛ مع `delete` بيحذفه فعلًا — فالتجربة على dev فقط.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/",
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/modules",
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-what-if",
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-to-tenant",
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/stacks",
                  "https://azure.github.io/Azure-Verified-Modules/",
                  "https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs",
                  "https://developer.hashicorp.com/terraform/language/backend/azurerm",
              ]},
             {"id": "t2", "title": "مهمة 2: بنية ككود في CI + سياسة انحراف",
              "md": "**السياق:** البنية بقت كود (المهمة 1)، ومحتاج تضمن إنها تُراجع وتُختبر وتُنشر بأمان.\n\n**المطلوب:**\n1. `.github/workflows/infra.yml`: job **validate** على PR (build/lint + `what-if` أو `plan` + نشر الناتج **كتعليق على الـPR**) وjob **deploy** على main مربوط بـ`environment: production` (required reviewers من 6.3.5).\n2. استخدم **OIDC** للمصادقة (بلا secret) مع **دورين مختلفين**: قراءة/تحقق للـPR، ومساهِم للنشر — ووثّق الفرق.\n3. لو الصلاحيات محدودة في PR: استخدم `--validation-level Template ProviderNoRbac` (Azure CLI ≥ 2.76) واذكر الحد في الوثيقة.\n4. فحص أمان للبنية في CI (checkov أو tfsec أو Azure Policy as code) بعتبة: صفر CRITICAL/HIGH — ووثّق الاستثناءات بتبرير.\n5. **كشف انحراف مجدول**: workflow أسبوعي يشغّل `what-if`/`plan` ويقارن بالواقع، ولو فيه فرق يفتح **issue** تلقائيًا (بأسماء الموارد والخصائص).\n6. سياسة مكتوبة `docs/iac-policy.md`: مين يعدّل البنية · إزاي · إيه الممنوع (تعديل Portal) · إيه اللي يتعمل بعد حادث اضطر فيه حد يعدّل يدويًا (PR خلال 24 ساعة) · وإزاي تُدار موارد خارج الإدارة (import).\n7. اختبار تراجع للبنية: اختبار يتحقق إن `dev.bicepparam` فيه `enableHa=false` و`logRetentionDays<=30` و`prod` فيه العكس — يعني **قواعد التكلفة مفروضة آليًا** (6.2.5).",
              "criteria": [
                  "المعاينة تظهر **كتعليق على الـPR** (مش في سجلات بس) — دليل بصري مُرفق.",
                  "النشر خلف `environment: production` بـrequired reviewers + موافقة موثقة.",
                  "OIDC بدورين مختلفين (تحقق مقابل نشر) والفرق موثق.",
                  "استخدام `--validation-level` (أو مكافئه في Terraform) مع ذكر الحد.",
                  "فحص أمان بعتبة صفر HIGH/CRITICAL + جدول استثناءات بتبرير وتاريخ انتهاء.",
                  "كشف انحراف أسبوعي يفتح issue بأسماء الموارد والخصائص المختلفة.",
                  "سياسة IaC مكتوبة فيها مسار «تعديل يدوي في حادث» بمهلة PR.",
                  "اختبار تراجع يفرض قواعد التكلفة على ملفات المعاملات (HA off وretention منخفض في dev).",
              ],
              "hint": "لتعليق الـPR: `actions/github-script` مع قراءة ملف `whatif.txt` وتقصيره (حد التعليق 65,536 حرفًا). وللدورين: أنشئ app registration واحد بـfederated credentials مختلفة — واحد بـ`environment:production` (دور Contributor على مجموعة الموارد) وآخر للتحقق (Reader) مربوط بـ`ref:refs/heads/*` أو بيئة `ci-readonly`. وللاختبار: اقرأ ملفات `.bicepparam`/`.tfvars` في اختبار xUnit وافشل لو `enableHa = true` في dev.",
              "solution": "البنية: `infra.yml` بـjobين + `scripts/iac-checks.sh` (فحص قواعد التكلفة على ملفات المعاملات) + workflow `drift-check.yml` أسبوعي + `docs/iac-policy.md`. الدوران: **ci-readonly** (Reader على مجموعة الموارد + `--validation-level ProviderNoRbac`) للـPRs، و**prod-deployer** (Contributor على مجموعة موارد الإنتاج فقط، مربوط بـ`environment:production` مع required reviewers) للنشر. الفحص الأمني: checkov/tfsec على `infra-tf/` أو Azure Policy على الموارد المنشورة مع جدول استثناءات (مثال: `publicNetworkAccess` مسموح في dev فقط حتى تاريخ محدد). كشف الانحراف: `what-if` أسبوعيًا؛ أي `~ Modify` أو `- Delete` → issue بقائمة الموارد. اختبار التراجع: xUnit بيقرأ `infra/dev.bicepparam` و`prod.bicepparam` ويؤكد: dev → `enableHa=false`, `logRetentionDays<=30`, `pgTier=Burstable`؛ prod → `enableHa=true`, `logRetentionDays>=90`. النتيجة: قواعد التكلفة من 6.2.5 بقت مفروضة آليًا بدل ما تكون نصيحة.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-what-if",
                  "https://docs.github.com/en/actions/use-cases-and-examples/deploying/deploying-to-azure",
                  "https://learn.microsoft.com/en-us/cli/azure/deployment/group",
                  "https://www.checkov.io/",
                  "https://learn.microsoft.com/en-us/azure/governance/policy/",
                  "https://azure.github.io/Azure-Verified-Modules/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Bicep: التوثيق الأساسي", "url": "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/"},
            {"label": "Bicep modules والسجلات", "url": "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/modules"},
            {"label": "Bicep what-if", "url": "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-what-if"},
            {"label": "Deployment stacks (إدارة دورة الحياة)", "url": "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-stacks"},
            {"label": "Azure Verified Modules", "url": "https://azure.github.io/Azure-Verified-Modules/"},
            {"label": "Terraform: azurerm provider", "url": "https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs"},
            {"label": "Terraform: backend azurerm", "url": "https://developer.hashicorp.com/terraform/language/backend/azurerm"},
            {"label": "Terraform: استيراد الموارد", "url": "https://developer.hashicorp.com/terraform/language/import"},
            {"label": "النشر إلى Azure من GitHub Actions", "url": "https://docs.github.com/en/actions/use-cases-and-examples/deploying/deploying-to-azure"},
        ]},
    ],
}

LESSONS_S6_I = [_L3, _L4]
