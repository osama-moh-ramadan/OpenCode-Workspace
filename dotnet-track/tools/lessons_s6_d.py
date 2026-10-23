"""Stage 6, Module 1 — Kubernetes config, secrets & scaling (lesson 5)."""

TODAY = "2026-10-22"

LESSONS_S6_D = [
    {
        "id": "s6-m1-l5",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الصورة **ثابتة** — نفس البايتات من dev لـprod. اللي بيتغير هو **الإعداد والموارد وعدد النسخ**.
الدرس ده بيغطي الأربعة أعمدة اللي بتفرّق بين «K8s شغال» و«K8s بيسبب حوادث»:

1. **الإعدادات والأسرار**: ConfigMap/Secret بره الصورة، وتطبيق بيقرأها بـ`IOptions` مع تحقق عند الإقلاع.
2. **Probes**: الفرق بين readiness وliveness وstartup — وإعدادات محسوبة مش منسوخة.
3. **الموارد**: requests مقابل limits، وQoS، وسلوك **.NET تحديدًا** جوه الحاوية (GC وcgroups).
4. **التوسع**: HPA وKEDA (لأن نظامنا event-driven)، وPDB، و**الإيقاف اللطيف** — لأن التوسع معناه إيقاف Pods باستمرار.

⚠ القاعدة اللي بتحكم كل ده: **أي رقم هنا لازم يكون من قياس** (p95 CPU، عمق الطابور، حجم الـheap)،
مش من مثال على الإنترنت. الأرقام المنسوخة هي سبب أغلب حوادث autoscaling.
"""},
            {"type": "terms", "items": [
                {"term": "ConfigMap", "def": "إعداد غير سري (key/value أو ملفات). يوصل للتطبيق كـenv أو volume. ★ `immutable: true` بيمنع التعديل العرضي ويحسّن الأداء."},
                {"term": "Secret", "def": "بيانات حساسة — **base64 مش تشفير**. لازم: encryption at rest في etcd، أو RBAC ضيق، أو مصدر خارجي (Key Vault/External Secrets)."},
                {"term": "env مقابل volume mount", "def": "الـenv أبسط بس ظاهر في `describe pod` (ومرئي لأي حد بصلاحيات قراءة). الملفات المرفوعة أأمن للأسرار الكبيرة/الشهادات."},
                {"term": "requests", "def": "الموارد المضمونة للحاوية — **أساس الجدولة** وأساس حساب HPA (نسبة الاستخدام = فعل ÷ request)."},
                {"term": "limits", "def": "السقف. تجاوز limit الـCPU = **throttling** (بطء)، وتجاوز limit الذاكرة = **OOMKilled** (إعادة تشغيل)."},
                {"term": "QoS Class", "def": "`Guaranteed` (requests == limits لكل الموارد) · `Burstable` (فيه requests) · `BestEffort` (ولا حاجة). بيحدد أولوية الطرد (eviction) عند ضغط الموارد."},
                {"term": "HPA", "def": "Horizontal Pod Autoscaler (`autoscaling/v2`): يعدّل `replicas` حسب مقياس (CPU/ذاكرة/مقياس مخصص). ★ يحتاج metrics-server وrequests معرّفة."},
                {"term": "KEDA", "def": "توسع event-driven: من طول الطابور (RabbitMQ/Kafka)، عدد الرسائل، cron، أو أي مقياس خارجي — ويدعم **scale-to-zero**."},
                {"term": "PDB (PodDisruptionBudget)", "def": "يضمن حد أدنى من النسخ المتاحة أثناء الإخلاء الطوعي (node drain/trقيات). بلا PDB = صيانة واحدة تُوقع الخدمة."},
                {"term": "topologySpreadConstraints", "def": "توزيع النسخ على zones/nodes — عشان فشل zone واحدة ما يسقطش الخدمة كلها."},
                {"term": "Graceful Shutdown", "def": "عند SIGTERM: توقف قبول عمل جديد، تكمّل الشغل الجاري، تفلش المقاييس/اللوجات، وتخرج — خلال `terminationGracePeriodSeconds`."},
                {"term": "preStop hook", "def": "أمر قبل SIGTERM (عادة `sleep 5`) — يعطي وقتًا لإزالة الـPod من الـEndpoints قبل ما التطبيق يقفل (يمنع 503s أثناء الـrollout)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الإعدادات والأسرار: بره الصورة تمامًا"},
            {"type": "code", "lang": "yaml", "filename": "k8s/base/config.yaml", "title": "ConfigMap + Secret + Kustomize generators (بلا أسرار في git)", "code": r'''
# ══════════ ConfigMap: إعداد غير سري ══════════
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-config
  namespace: shop
immutable: true                       # ✓ يمنع التعديل العرضي + يقلل حمل الـAPI server
data:
  # ★ أسماء مفاتيح بصيغة .NET: __ (شرطتين سفليتين) = ":" في الـconfiguration
  ASPNETCORE_ENVIRONMENT: "Production"
  ASPNETCORE_HTTP_PORTS: "8080"
  Orders__Outbox__BatchSize: "100"
  Orders__Outbox__DispatchIntervalSeconds: "2"
  Orders__Resilience__PaymentTimeoutSeconds: "20"
  Orders__RateLimit__PerTenantPerMinute: "120"
  OTEL_RESOURCE_ATTRIBUTES: "deployment.environment=prod,service.version=1.4.0"
---
# ══════════ Secret: بيانات حساسة ══════════
# ⚠ المثال ده للتوضيح المحلي فقط — **لا ترفع Secret ببيانات حقيقية للـgit**
apiVersion: v1
kind: Secret
metadata:
  name: orders-secrets-local-example
  namespace: shop
type: Opaque
stringData:                           # ✓ stringData (نص صريح) أسهل من data (base64 يدوي)
  shopdb: "Host=pg.shop.svc.cluster.local;Port=5432;Database=shopdb;Username=orders;Password=***"
  rabbit: "amqp://shop:***@rabbitmq.shop.svc.cluster.local:5672/shop"
# في الإنتاج (الأفضل — اختر واحدًا):
#   ① Azure Key Vault + CSI Secrets Store driver  (درس 6.2.3)
#   ② External Secrets Operator (يسحب من Key Vault/AWS SM/GCP SM ويولّد Secret)
#   ③ SOPS + age/GPG: ملفات مشفرة في git وتفك في الـpipeline
#   ④ Managed Identity: بلا سر أصلًا (الهوية هي السر)
---
# ══════════ الاستخدام في الـDeployment ══════════
# (جزء من containers[0] — راجع درس 6.1.4 للملف الكامل)
#
#   envFrom:
#     - configMapRef: { name: orders-config }      # كل مفاتيح الـConfigMap كـenv
#   env:
#     - name: ConnectionStrings__shopdb
#       valueFrom: { secretKeyRef: { name: orders-secrets, key: shopdb } }
#     - name: ConnectionStrings__rabbit
#       valueFrom: { secretKeyRef: { name: orders-secrets, key: rabbit } }
#
#   # أو كملفات (أأمن للشهادات/المفاتيح الكبيرة + تطبيق بيقرأ من مسار)
#   volumeMounts:
#     - { name: config, mountPath: /app/config, readOnly: true }
#   volumes:
#     - name: config
#       configMap:
#         name: orders-config
#         items: [{ key: appsettings.Production.json, path: appsettings.Production.json }]
---
# ══════════ Kustomize: توليد تلقائي + rollout عند التغيير ══════════
# k8s/overlays/prod/kustomization.yaml
#
# configMapGenerator:
#   - name: orders-config
#     behavior: replace
#     literals:
#       - Orders__RateLimit__PerTenantPerMinute=240
#     options:
#       disableNameSuffixHash: false      # ★ يضيف hash للاسم → الـDeployment بيتحدث تلقائيًا
#                                         #   (بديل أنضف من annotation الـconfig-hash اليدوي في درس 6.1.4)
# secretGenerator:
#   - name: orders-secrets
#     behavior: replace
#     envs: [secrets.prod.env]            # ⚠ الملف ده **مش في git** (gitignored) — بييجي من CI secret
#     options:
#       disableNameSuffixHash: false
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Configuration/OrderOptions.cs", "title": "التطبيق بيقرأ الإعداد بأمان: Options + تحقق عند الإقلاع", "code": r'''
// requires: using Microsoft.Extensions.Options; using System.ComponentModel.DataAnnotations;

/// <summary>
/// ★ بلا `config["Orders:RateLimit:PerTenantPerMinute"]` منتشر في الكود.
/// Options مُحققة عند الإقلاع = فشل سريع وواضح بدل سلوك غريب في الإنتاج.
/// </summary>
public sealed class OrderOptions
{
    public const string SectionName = "Orders";

    [Required] public OutboxOptions Outbox { get; init; } = new();
    [Required] public ResilienceOptions Resilience { get; init; } = new();
    [Required] public RateLimitOptions RateLimit { get; init; } = new();

    public sealed class OutboxOptions
    {
        [Range(1, 1000)]      public int  BatchSize { get; init; } = 100;
        [Range(1, 60)]        public int  DispatchIntervalSeconds { get; init; } = 2;
        [Range(1, 30)]        public int  MaxRetries { get; init; } = 5;
    }

    public sealed class ResilienceOptions
    {
        [Range(1, 120)]       public int  PaymentTimeoutSeconds { get; init; } = 20;
        [Range(1, 100)]       public int  PaymentPermitLimit { get; init; } = 12;
    }

    public sealed class RateLimitOptions
    {
        [Range(1, 100_000)]   public int  PerTenantPerMinute { get; init; } = 120;
        [Range(0, 1_000_000)] public int  GlobalPerSecond { get; init; } = 5_000;
    }
}

// ── التسجيل في Program.cs ──
// builder.Services.AddOptions<OrderOptions>()
//     .BindConfiguration(OrderOptions.SectionName)
//     .ValidateDataAnnotations()                       // ✓ [Range]/[Required]
//     .Validate(o => o.Resilience.PaymentTimeoutSeconds < 30,
//                   "ميزانية المهلة: timeout الدفع لازم < 30s (docs/timeout-budget.md)")
//     .ValidateOnStart();                              // ★ يفشل عند الإقلاع، مش عند أول طلب

// ── الاستخدام (بلا IConfiguration في الـdomain) ──
public sealed class OrderService(IOptions<OrderOptions> options, ILogger<OrderService> log)
{
    private readonly OrderOptions _o = options.Value;

    public int BatchSize => _o.Outbox.BatchSize;

    public void Describe() => log.LogInformation(
        "orders config: batch={Batch} interval={Interval}s paymentTimeout={Timeout}s permit={Permit} rateLimit={Rate}/min",
        _o.Outbox.BatchSize, _o.Outbox.DispatchIntervalSeconds,
        _o.Resilience.PaymentTimeoutSeconds, _o.Resilience.PaymentPermitLimit,
        _o.RateLimit.PerTenantPerMinute);
}

// ── connection strings: نفس المبدأ ──
// var cs = builder.Configuration.GetConnectionString("shopdb")
//     ?? throw new InvalidOperationException(
//          "ConnectionStrings:shopdb مفقود — تأكد من ConfigMap/Secret (درس 6.1.5)");
'''},
            {"type": "heading", "level": 2, "text": "2) Probes: 3 أسئلة مختلفة — وإعدادات محسوبة"},
            {"type": "table", "head": ["الـprobe", "السؤال اللي بيجاوبه", "المسار", "الفشل يعني", "إعداد نموذجي"], "rows": [
                ["`startupProbe`", "خلص الإقلاع؟", "`/alive`", "الحاوية تُقتل وتُعاد (قبل ما readiness/liveness يبدأوا)", "`periodSeconds: 2` × `failureThreshold: 30` = مهلة 60 ثانية للإقلاع"],
                ["`readinessProbe`", "جاهزة تستقبل طلبات؟", "`/health` (مع التبعيات)", "تشيلها من الـEndpoints (**بلا إعادة تشغيل**)", "`periodSeconds: 10`, `timeoutSeconds: 3`, `failureThreshold: 3`"],
                ["`livenessProbe`", "الحاوية ميتة/معلّقة؟", "`/alive` (**رخيص، بلا تبعيات**)", "إعادة تشغيل الحاوية", "`periodSeconds: 20`, `timeoutSeconds: 3`, `failureThreshold: 3`"],
                ["`gRPC` probe", "نفس الأسئلة لخدمة gRPC", "خدمة `grpc.health.v1.Health`", "—", "`grpc: { port: 9090 }` (يحتاج K8s 1.24+)"],
                ["`exec` probe", "تطبيقات بلا HTTP", "أمر داخل الحاوية (أو `--health` mode من درس 6.1.3)", "—", "`exec: { command: [\"dotnet\",\"App.dll\",\"--health\"] }`"],
            ]},
            {"type": "code", "lang": "yaml", "filename": "k8s/base/probes-and-resources.yaml", "title": "probes + موارد + QoS — الجزء الحرج في الـDeployment", "code": r'''
# (مقتطف من containers[0])

# ═══ 1) Probes مضبوطة بحساب ═══
startupProbe:
  httpGet: { path: /alive, port: http, scheme: HTTP }
  periodSeconds: 2
  failureThreshold: 30          # ★ 2 × 30 = 60 ثانية مهلة إقلاع (قيس إقلاعك البارد واضبطها)
  timeoutSeconds: 2

readinessProbe:
  httpGet:
    path: /health               # ✓ بيعتمد على التبعيات: DB/Redis/RabbitMQ (درس 2.3.4)
    port: http
    httpHeaders:                # ✓ فحص خفيف: ما تعملش استعلامات ثقيلة جوه /health
      - { name: X-Probe, value: readiness }
  periodSeconds: 10
  timeoutSeconds: 3             # ⚠ لو /health أبطأ من ده → فشل وهمي → 503
  failureThreshold: 3           # 3 × 10 = 30 ثانية قبل شيل الحركة
  successThreshold: 1

livenessProbe:
  httpGet: { path: /alive, port: http }   # ★ /alive = "العملية بترد" فقط — بلا DB/Redis
  periodSeconds: 20
  timeoutSeconds: 3
  failureThreshold: 3           # 3 × 20 = 60 ثانية قبل إعادة التشغيل (بلا تسرّع)

# ═══ 2) الموارد: requests = الجدولة والـHPA · limits = السقف ═══
resources:
  requests:
    cpu: "250m"                 # ← من قياس p95 الفعلي (مش تخمين)
    memory: "384Mi"
  limits:
    cpu: "1000m"                # ✓ CPU limit أعلى من الـrequest (تجنب throttling مستمر)
    memory: "512Mi"             # ★ memory: تجاوزها = OOMKilled. خلي الـheap مضبوط (تحت)

# ═══ 3) إعدادات .NET للذاكرة داخل الحاوية (env أو ConfigMap) ═══
env:
  - name: DOTNET_gcServer
    value: "1"                  # Server GC = أداء أعلى، ذاكرة أكبر. مع limit صغير → جرّب "0"
  - name: DOTNET_GCHeapHardLimitPercent
    value: "0.65"               # ★ الـheap ≤ 65% من limit الحاوية — يسيب مساحة لـstack/native/sockets
  - name: DOTNET_GCConserveMemory
    value: "5"                  # 0–9: أعلى = ذاكرة أقل مقابل GC أكثر
  - name: DOTNET_RUNNING_IN_CONTAINER
    value: "true"               # (موجود في الصور الرسمية بالفعل)
  - name: DOTNET_EnableDiagnostics
    value: "0"                  # يقفل diagnostics pipes (أصغر سطح هجوم) — فعّله وقت التشخيص فقط

# ═══ 4) الإيقاف اللطيف ═══
# (على مستوى الـPod spec)
#   terminationGracePeriodSeconds: 45
#   containers[0].lifecycle:
#     preStop:
#       exec: { command: ["sleep", "5"] }   # ⚠ يحتاج shell — في chiseled استخدم sidecar أو زيادة المهلة
'''},
            {"type": "callout", "kind": "note", "title": ".NET داخل الحاوية: 5 حقائق بتغيّر إعداداتك",
             "md": """
1. **الـruntime بيقرأ cgroups**: عدد المعالجات والذاكرة المتاحة بيتحددوا من حدود الحاوية، مش من الـnode.
   عشان كده limit صغير = thread pool وGC بأعداد أصغر (كفاءة، بس انتبه للأداء).
2. **Server GC (`DOTNET_gcServer=1`) بيحجز ذاكرة لكل core**: مع limit 256Mi و4 cores ممكن توصل لـOOM بسرعة.
   للحاويات الصغيرة جرّب `DOTNET_gcServer=0` (Workstation GC) وقارن p95 والذاكرة.
3. **الـheap الافتراضي ~75% من الذاكرة المتاحة**: عشان كده `DOTNET_GCHeapHardLimitPercent=0.65` (أو أقل)
   مع `memory limit` واضح = حماية من OOMKilled. قِس `dotnet_total_memory` و`process_working_set` مقابل الـlimit.
4. **memory limit بلا request = QoS `Burstable`** → أولوية طرد أعلى عند ضغط الـnode.
   للخدمات الحرجة: `requests.memory == limits.memory` (**Guaranteed**).
5. **CPU throttling بيتظهر كـp95 عالي مش كأخطاء**: قِس `container_cpu_cfs_throttled_periods_total`
   (أو في Azure/Grafana). لو عالي → زوّد الـCPU limit أو شيله (مع request واضح).

⚠ **`DOTNET_GCHeapHardLimitPercent` وغيرها إعدادات حساسة للإصدار** — تحقق من توثيق runtimeconfig
لإصدارك قبل ما تعتمد عليها في الإنتاج، وقيس الأثر (مش «ضبطتها فالأداء اتحسن»).
"""},
            {"type": "heading", "level": 2, "text": "3) التوسع: HPA · KEDA · PDB · توزيع النسخ"},
            {"type": "code", "lang": "yaml", "filename": "k8s/overlays/prod/scaling.yaml", "title": "HPA للـAPI وKEDA للـworkers وPDB وتوزيع zones", "code": r'''
# ══════════ ① HPA: للخدمات HTTP (CPU/ذاكرة) ══════════
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders-hpa, namespace: shop }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: orders }
  minReplicas: 2                 # ★ ≥2: نسخة واحدة = downtime عند أي صيانة
  maxReplicas: 12                # ← من حساب: max × pool connections ≤ DB max_connections (تحت)
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }   # نسبة من **request** مش limit
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 80 }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0                 # اصعد فورًا
      policies:
        - { type: Percent, value: 100, periodSeconds: 60 }      # ضاعف كل دقيقة (محدود)
    scaleDown:
      stabilizationWindowSeconds: 300               # ★ انزل ببطء (منع flapping)
      policies:
        - { type: Pods, value: 1, periodSeconds: 60 }
---
# ══════════ ② KEDA: للـworkers (طول طابور RabbitMQ) ══════════
# ⚠ KEDA بينشئ HPA بنفسه — **لا تعرّف HPA يدوي على نفس الـDeployment** (تعارض وflapping)
apiVersion: v1
kind: Secret
metadata: { name: rabbitmq-keda, namespace: shop }
stringData:
  host: "amqp://shop:PASSWORD@rabbitmq.shop.svc.cluster.local:5672/shop"   # ← من Key Vault/ESO في الإنتاج
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: payments-scaler, namespace: shop }
spec:
  scaleTargetRef: { name: payments }        # اسم الـDeployment
  minReplicaCount: 1                        # (0 = scale-to-zero: ممكن بس بيأخر أول رسالة)
  maxReplicaCount: 20
  pollingInterval: 30
  cooldownPeriod: 300
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown: { stabilizationWindowSeconds: 300 }
  triggers:
    - type: rabbitmq
      metadata:
        protocol: amqp
        queueName: order-placed              # ← من definitions.json (درس 5.2.1)
        mode: QueueLength
        value: "100"                         # ★ الهدف: ≤100 رسالة لكل نسخة
        activationValue: "5"                 # يبدأ التوسع من 5 رسائل (لو minReplicaCount=0)
      authenticationRef: { name: rabbitmq-keda }
# (تحقق من أسماء حقول الـtrigger في إصدار KEDA عندك — بتتطور)
---
# ══════════ ③ PDB: صيانة بلا إسقاط الخدمة ══════════
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: orders-pdb, namespace: shop }
spec:
  minAvailable: 2                 # أو maxUnavailable: 1 — من عدد النسخ الفعلي
  selector:
    matchLabels: { app.kubernetes.io/name: orders }
---
# ══════════ ④ توزيع النسخ على zones (أضفه لـPod spec) ══════════
# topologySpreadConstraints:
#   - maxSkew: 1
#     topologyKey: topology.kubernetes.io/zone
#     whenUnsatisfiable: ScheduleAnyway      # ← DoNotSchedule لو العدد كافٍ والـzones متوفرة
#     labelSelector:
#       matchLabels: { app.kubernetes.io/name: orders }
---
# ══════════ ⑤ حدود للـnamespace كله (حماية من جيران صاخبين) ══════════
apiVersion: v1
kind: ResourceQuota
metadata: { name: shop-quota, namespace: shop }
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    pods: "60"
'''},
            {"type": "code", "lang": "bash", "title": "فحص وتشخيص التوسع + حساب اتصال البيانات", "code": r'''
# ═══ 1) هل الـHPA شغال؟ وليه مش بيوسّع؟ ═══
kubectl -n shop get hpa                       # TARGETS: <unknown>/70% = مشكلة!
kubectl -n shop describe hpa orders-hpa       # ★ الأحداث بتقول السبب (مفيش metrics؟ requests ناقصة؟)
kubectl -n shop get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/shop/pods" | head -20
kubectl get apiservices | grep metrics        # metrics-server True؟
kubectl -n shop top pods --sort-by=cpu

# أسباب `TARGETS: <unknown>` الأشهر:
#   ① metrics-server مش مثبت  ② الـDeployment بلا `resources.requests.cpu`  ③ الـHPA بيشير لـdeployment غلط

# ═══ 2) KEDA ═══
kubectl -n shop get scaledobject,scaledjob
kubectl -n shop describe scaledobject payments-scaler     # الشروط والحالة
kubectl -n shop get hpa keda-hpa-payments-scaler          # KEDA بينشئ HPA باسم keda-hpa-<name>
kubectl -n keda logs -l app.kubernetes.io/name=keda-operator --tail 100 | grep -i error

# ═══ 3) جرّب التوسع فعليًا (بلا تخمين) ═══
# حمّل الخدمة بـk6 (درس 3.4.1) وراقب:
k6 run --vus 50 --duration 2m scripts/load-orders.js &
watch -n 3 'kubectl -n shop get hpa,pods -l app.kubernetes.io/name=orders'
# ثم تحقق من:
kubectl -n shop top pods
kubectl -n shop get events --sort-by=.lastTimestamp | grep -iE 'scale|oom|evict|throttl'

# ═══ 4) الإيقاف اللطيف: اختبره مش تفترضه ═══
kubectl -n shop rollout restart deploy/orders             # إعادة تشغيل تدريجية
watch -n 1 'kubectl -n shop get pods -o wide; echo; curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Host: shop.example.com" http://localhost:8080/api/orders/health'
# ✓ المطلوب: **صفر 503s** أثناء الـrollout. لو ظهرت 503s → preStop/terminationGracePeriod مش مضبوطة

# ═══ 5) PDB: تأكد إن الصيانة ممكنة ═══
kubectl -n shop get pdb
kubectl -n shop drain <node> --ignore-daemonsets --delete-emptydir-data --dry-run=server
#   ← لو قال "cannot evict pod … violates PodDisruptionBudget" → PDB شغال (مقصود) بس تحقق إنك
#     ما حطّتش minAvailable = عدد النسخ (يمنع أي إخلاء للأبد)

# ═══ 6) ★ حساب اتصال قاعدة البيانات (أشهر حادث بعد التوسع) ═══
#   max_replicas × Max Pool Size (لكل نسخة) ≤ max_connections × 0.8
#   مثال: 12 نسخة × 100 اتصال = 1200 اتصال — وAzure Database for PostgreSQL Flexible D4s = ~400!
kubectl -n shop get deploy -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.replicas}{"\n"}{end}'
#   → عدّل Max Pool Size في connection string أو قلّل maxReplicas أو استخدم PgBouncer (درس 3.4.2)

# ═══ 7) جودة QoS الحالية ═══
kubectl -n shop get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.qosClass}{"\n"}{end}'
'''},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/Infrastructure/GracefulShutdown.cs", "title": "الإيقاف اللطيف في .NET (لأن التوسع = إيقاف مستمر)", "code": r'''
// requires: using Microsoft.Extensions.Hosting; using Microsoft.Extensions.Options;

/// <summary>
/// ★ لما K8s بيقلّل النسخ أو بيعمل rollout، حاوياتك بتستقبل SIGTERM **باستمرار**.
/// الهدف: لا طلبات فاشلة، ولا رسائل ضايعة، ولا مقاييس مفقودة.
/// </summary>
public static class GracefulShutdown
{
    public static WebApplicationBuilder ConfigureGracefulShutdown(this WebApplicationBuilder builder)
    {
        // ① مهلة الإيقاف: لازم أقل من terminationGracePeriodSeconds في الـmanifest
        //    (الافتراضي في .NET 8+ = 30 ثانية؛ كان 5 قبل كده — تحقق من إصدارك)
        builder.Services.Configure<HostOptions>(o =>
        {
            o.ShutdownTimeout = TimeSpan.FromSeconds(30);
        });

        return builder;
    }

    /// <summary>يُسجَّل بعد بناء التطبيق: ترتيب الإيقاف مهم.</summary>
    public static WebApplication UseGracefulShutdown(this WebApplication app)
    {
        var lifetime = app.Services.GetRequiredService<IHostApplicationLifetime>();
        var log = app.Services.GetRequiredService<ILoggerFactory>().CreateLogger("Shutdown");
        var outbox = app.Services.GetService<OutboxDispatcher>();

        lifetime.ApplicationStopping.Register(() =>
        {
            // ② أوقف إنتاج شغل جديد **قبل** ما توقف المعالجة
            log.LogInformation("SIGTERM received — stopping acceptance of new work");

            // ③ أوقف الـdispatcher (بلا رسائل جديدة للوسيط) وانتظر الجاري
            outbox?.RequestStop();

            // ④ افلش المقاييس واللوجات (وإلا آخر دقايق من البيانات بتضيع)
            app.Services.GetService<MetricsFlusher>()?.Flush();
            Log.CloseAndFlush();

            // ⚠ لا تعمل شغل طويل هنا: عندك ShutdownTimeout بس، وبعدها SIGKILL
            log.LogInformation("Shutdown preparations complete");
        });

        lifetime.ApplicationStopped.Register(() =>
            app.Services.GetService<ILoggerFactory>()
                       .CreateLogger("Shutdown")
                       .LogInformation("Stopped cleanly"));

        return app;
    }
}

/// <summary>مثال: dispatcher بيقف بلطف (بدل ما يقطع في نص دفعة).</summary>
public sealed class OutboxDispatcher(ILogger<OutboxDispatcher> log)
{
    private readonly CancellationTokenSource _cts = new();
    private int _inFlight;

    public void RequestStop()
    {
        _cts.Cancel();                                   // ✓ بلا دورات جديدة
        var waited = 0;
        while (Volatile.Read(ref _inFlight) > 0 && waited < 10_000)
        {
            Thread.Sleep(100);                           // انتظر الجاري (محدود بزمن)
            waited += 100;
        }
        if (Volatile.Read(ref _inFlight) > 0)
            log.LogWarning("shutdown with {Count} outbox batches still in flight", _inFlight);
    }

    public void BeginBatch() => Interlocked.Increment(ref _inFlight);
    public void EndBatch()   => Interlocked.Decrement(ref _inFlight);
    public CancellationToken StopToken => _cts.Token;
}

public sealed class MetricsFlusher
{
    public void Flush() { /* e.g. ForceFlush on the MeterProvider */ }
}

// ── في Program.cs ──
// var builder = WebApplication.CreateBuilder(args);
// builder.ConfigureGracefulShutdown();
// builder.AddServiceDefaults();
// …
// var app = builder.Build();
// app.UseGracefulShutdown();
// app.MapDefaultEndpoints();
// app.Run();     // ← ASP.NET Core بيتعامل مع SIGTERM: يوقف قبول طلبات جديدة ويكمّل الجاري

// ── MassTransit: الإيقاف اللطيف مدمج ──
// الـhost بيوقف المستهلكين وينتظر الرسائل الجارية عند SIGTERM (بشرط إن الـbus مسجّل في الـDI).
// ★ تأكد إن `terminationGracePeriodSeconds` أكبر من أطول رسالة عندك، وإلا K8s هيقتلها بـSIGKILL.
'''},
            {"type": "table", "head": ["المشكلة", "السبب", "الإصلاح"], "rows": [
                ["503s أثناء الـrollout", "الـPod اتشال من الـEndpoints **بعد** ما بدأ يقفل (سباق)", "`preStop: sleep 5` + `terminationGracePeriodSeconds` كافٍ + `maxUnavailable: 0`"],
                ["`OOMKilled` بعد التوسع", "Server GC + limit صغير، أو heap قريب من الـlimit", "`DOTNET_GCHeapHardLimitPercent=0.65` · جرّب `gcServer=0` · زوّد limit من قياس"],
                ["p95 عالي بلا أخطاء", "CPU throttling (limit منخفض)", "قِس `throttled_periods` → زوّد limit أو شيله مع request واضح"],
                ["HPA `TARGETS: <unknown>`", "metrics-server ناقص أو مفيش `requests.cpu`", "ثبّت metrics-server + أضف requests (الـHPA بيحسب نسبة من الـrequest)"],
                ["توسع/انكماش متكرر (flapping)", "`scaleDown.stabilizationWindowSeconds` صغير أو هدف حساس", "نافذة 300s للنزول + هدف 70–80% + سياسات محدودة"],
                ["DB رفض الاتصالات بعد التوسع", "`max_replicas × pool size > max_connections`", "قلّل الـpool أو maxReplicas، أو أضف PgBouncer (درس 3.4.2)"],
                ["صيانة node بتوقع الخدمة", "بلا PDB، أو نسخة واحدة", "`PodDisruptionBudget` + `replicas ≥ 2` + topology spread"],
                ["رسائل ضايعة عند scale-down", "الـworker اتقتل في نص رسالة (SIGKILL)", "مهلة كافية + MassTransit graceful stop + idempotency (درس 5.2.5)"],
                ["KEDA مش بيوسّع من الصفر", "`activationValue` أعلى من الطول الفعلي، أو secret غلط", "`describe scaledobject` + لوجات keda-operator + تحقق من `activationValue`"],
                ["إعداد اتغيّر بس التطبيق ما حسّش", "ConfigMap مُحدّث بس الـPod قديم (env ما بيتحدثش)", "kustomize hash suffix أو `kubectl rollout restart` — الـvolume mounts بتتحدث، الـenv لأ"],
            ]},
            {"type": "callout", "kind": "danger", "title": "9 أخطاء إعدادات/توسع بتسبب حوادث حقيقية",
             "md": """
1. **أسرار في git** (Secret manifest بقيم حقيقية) — اعتبرها مكشوفة ولفّها. استخدم Key Vault/ESO/SOPS.
2. **`livenessProbe` على `/health`** (مع التبعيات) — DB تقع → كل النسخ تعيد التشغيل → انهيار كامل بدل degradation.
3. **بلا `requests`** — الجدولة تخمين، والـHPA مش هيشتغل، والـQoS = BestEffort (أول من يُطرد).
4. **`requests.memory` بعيد عن الواقع** (10Mi لتطبيق .NET) — جدولة مفرطة على الـnode ثم OOM/Eviction للجميع.
5. **`minAvailable` في PDB = عدد النسخ** — ولا node يتصيّن أبدًا (`drain` معلق للأبد).
6. **HPA على CPU لخدمة IO-bound** — CPU منخفض والطوابير بتزيد. استخدم RPS أو طول الطابور (KEDA).
7. **HPA + KEDA على نفس الـDeployment** — تعارض وflapping. واحد بس.
8. **`kubectl scale` يدوي في الإنتاج** — الحالة بتبعد عن الكود. أي تغيير من الـpipeline/GitOps.
9. **بلا اختبار للإيقاف اللطيف** — «إحنا عاملين graceful shutdown» بلا إثبات = 503s عند أول rollout.
   ★ اختبره: `rollout restart` أثناء حمل، والمطلوب صفر أخطاء.

✅ **قاعدة الذهب**: كل رقم (requests/limits/replicas/targets/mهلة) لازم يكون **من قياس** وموثّق في
`docs/capacity.md` مع تاريخ القياس والحمل المقابل. الأرقام بلا مصدر = حوادث مستقبلية.
"""},
            {"type": "checkpoints", "items": [
                "أفصل الإعداد عن الصورة بـConfigMap/Secret (+ kustomize generators بـhash) وأقرأها في .NET بـ`IOptions` مع `ValidateOnStart`.",
                "أضبط 3 probes بأدوارها وأحسب مهلها (`periodSeconds × failureThreshold`)، وأفهم فرق readiness (يشيل الحركة) عن liveness (يعيد التشغيل).",
                "أحدد requests/limits من قياس، وأفهم QoS وCPU throttling مقابل OOMKilled، وأضبط إعدادات .NET للذاكرة في الحاوية.",
                "أوسّع بـHPA للخدمات HTTP وKEDA للـworkers (طول الطابور)، مع PDB وtopology spread وحدود موارد للـnamespace.",
                "أطبّق وأختبر الإيقاف اللطيف (SIGTERM + ShutdownTimeout + preStop) بحيث الـrollout بيحصل بصفر 503s.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "الـHPA بيظهر `TARGETS: <unknown>/70%`. أشيع سبب؟",
                 "options": [
                     "الـDeployment واقع",
                     "مفيش `resources.requests.cpu` معرّفة (الـHPA بيحسب النسبة من الـ**request**) أو metrics-server مش مثبت",
                     "الـreplicas قليلة",
                     "الصورة كبيرة",
                 ], "answer": 1,
                 "explain": "بلا requests مفيش مقام للنسبة. `kubectl describe hpa` بيقولك السبب صراحةً، و`kubectl get apiservices | grep metrics` بيتأكد من الـmetrics-server."},
                {"q": "حد تجاوز `limits.memory` في .NET بيحصل إيه؟",
                 "options": [
                     "throttling",
                     "**OOMKilled**: الحاوية تُقتل وتُعاد (وتشوفها في `lastState.terminated.reason`) — على عكس CPU اللي بيؤدي لthrottling وبطء",
                     "رفض الطلبات",
                     "GC أسرع",
                 ], "answer": 1,
                 "explain": "الذاكرة مورد قاتل، والـCPU مورد خانق. عشان كده الـmemory limit لازم يكون مضبوط مع `DOTNET_GCHeapHardLimitPercent` وقياس الـheap الفعلي."},
                {"q": "حدّثت ConfigMap (env) بس التطبيق لسه بالإعداد القديم. ليه؟",
                 "options": [
                     "الـConfigMap مش immutable",
                     "متغيرات البيئة بتُحقن عند بدء الحاوية فقط — لازم `rollout restart` (أو kustomize hash suffix يولّد اسم جديد فيعمل rollout تلقائيًا). الـvolume mounts بتتحدث، الـenv لأ",
                     "الـnamespace غلط",
                     "K8s بيأخر التحديث ساعة",
                 ], "answer": 1,
                 "explain": "ده سبب استخدام `configMapGenerator` مع `disableNameSuffixHash: false`: اسم الـConfigMap بيتغير → الـPod template يتغير → rollout تلقائي."},
                {"q": "خدمة Payments بتعالج من طابور RabbitMQ. أنسب آلية توسع؟",
                 "options": [
                     "HPA على CPU",
                     "**KEDA** مع trigger على طول الطابور (عدد رسائل لكل نسخة) — لأن CPU مش بيعكس حجم الشغل المتراكم في نظام event-driven",
                     "HPA على الذاكرة",
                     "replicas ثابتة كبيرة",
                 ], "answer": 1,
                 "explain": "مستهلك ممكن يكون CPU بتاعه 10% ووراه 50,000 رسالة. التوسع لازم يتبع **مؤشر الشغل** (الطابور)، وKEDA كمان بيدعم scale-to-zero."},
                {"q": "12 نسخة × `Max Pool Size=100` وقاعدة البيانات بتسمح بـ400 اتصال. النتيجة؟",
                 "options": [
                     "كله تمام (12×100 = 1200 بس بيستخدموا قليل)",
                     "تحت الحمل كل نسخة هتفتح اتصالاتها → رفض اتصالات/timeout من DB. لازم: `max_replicas × pool ≤ 0.8 × max_connections` أو PgBouncer",
                     "K8s بيمنع ده",
                     "الـHPA هيقلل النسخ",
                 ], "answer": 1,
                 "explain": "أشهر حادث بعد تفعيل autoscaling. احسبها **قبل** ما توسّع، ووثّقها في `docs/capacity.md` (درس 3.4.2 عن pooling)."},
                {"q": "ليه `preStop: sleep 5` + `terminationGracePeriodSeconds: 45`؟",
                 "options": [
                     "عشان الإقلاع يبقى أسرع",
                     "إزالة الـPod من الـEndpoints بتحصل بالتوازي مع SIGTERM — النوم القصير بيخلي التطبيق يخدم الطلبات الجارية لحد ما التوجيه يتحدّث، والمهلة الكافية بتخليه يكمّل شغله قبل SIGKILL (صفر 503s)",
                     "مطلوب من .NET",
                     "بيوفّر موارد",
                 ], "answer": 1,
                 "explain": "بلا الـpreStop، فيه نافذة زمنية الـIngress/kube-proxy لسه بيوجّهوا لـPod بيقفل → 502/503 أثناء كل rollout. اختبره بحمل أثناء `rollout restart`."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "إعدادات وأسرار مفصولة عن الصورة",
                 "md": "انقل كل إعداد خدمة واحدة لـConfigMap/Secret (مع kustomize generators وhash)، واقرأها في التطبيق عبر `IOptions` مع `ValidateOnStart`، وأثبت إن تغيير إعداد بيعمل rollout تلقائي وإن إعداد غلط بيمنع الإقلاع برسالة واضحة.",
                 "criteria": [
                     "مفيش `appsettings.Production.json` ولا أسرار في الصورة (`docker exec`/تفكيك يثبت) ولا في git",
                     "ConfigMap `immutable: true` + مفاتيح بصيغة `Section__Key` + `envFrom` في الـDeployment",
                     "Secret من مصدر خارجي (Key Vault CSI/External Secrets/SOPS) أو مولّد في CI — وموثّق إزاي يتلفّ (rotate)",
                     "`IOptions<OrderOptions>` بـ`ValidateDataAnnotations` + `Validate` مخصص + `ValidateOnStart`",
                     "إثبات 1: تغيير literal في kustomize → `kubectl apply -k` → rollout تلقائي (hash) → القيمة الجديدة ظاهرة في التطبيق (لوج/endpoint)",
                     "إثبات 2: قيمة خارج الـ`[Range]` → الـPod يفشل عند الإقلاع برسالة واضحة (مش سلوك غريب) — مع مخرجات `logs`",
                     "`docs/config.md`: جدول كل مفتاح × المصدر (ConfigMap/Secret) × القيمة الافتراضية × مين بيغيرها",
                 ],
                 "hint": "خلي الـapplication يطبع ملخص الإعداد عند الإقلاع (بلا أسرار) — سطر واحد بيوفر ساعات تشخيص: «config: batch=100 interval=2s timeout=20s».",
                 "solution": "",
                 "resources": [
                     {"label": "ConfigMaps", "url": "https://kubernetes.io/docs/concepts/configuration/configmap/"},
                     {"label": "Secrets (وحدود التشفير)", "url": "https://kubernetes.io/docs/concepts/configuration/secret/"},
                     {"label": "Kustomize generators", "url": "https://kubectl.docs.kubernetes.io/guides/config_management/"},
                 ]},
                {"id": "t2", "title": "توسع مُقاس + rollout بصفر أخطاء",
                 "md": "اضبط requests/limits من قياس حقيقي، وفعّل HPA (أو KEDA لو worker) بأهداف مبررة، وأضف PDB وtopology spread، وطبّق الإيقاف اللطيف. أثبت بحمل حقيقي: التوسع بيحصل، الـDB مش بيتخنق، والـrollout بيتم بصفر 503s.",
                 "criteria": [
                     "requests/limits من قياس (k6 + `kubectl top`) — `docs/capacity.md` فيه الأرقام والحمل المقابل والتاريخ",
                     "HPA (أو KEDA ScaledObject) بأهداف مبررة + `behavior` (scaleUp فوري، scaleDown بنافذة 300s) + min/max replicas",
                     "حساب اتصالات DB مكتوب ومُحترم: `maxReplicas × pool ≤ 0.8 × max_connections` (أو PgBouncer)",
                     "PDB + topologySpreadConstraints + ResourceQuota للـnamespace",
                     "إثبات التوسع: حمل → `kubectl get hpa,pods -w` بيظهر زيادة النسخ + `top pods` (مخرجات محفوظة)",
                     "إثبات الإيقاف اللطيف: `rollout restart` أثناء الحمل → **صفر 503s** (سكريبت بيقيس الأكواد أثناء الـrollout)",
                     "إعدادات .NET للذاكرة مضبوطة (`GCHeapHardLimitPercent`/`gcServer`) مع مقياس heap مقابل limit قبل/بعد",
                     "جدول `docs/scaling.md`: المقياس × الهدف × من أين جاء الرقم × إيه اللي حصل لما اتغير",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Horizontal Pod Autoscaler", "url": "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"},
                     {"label": "KEDA docs", "url": "https://keda.sh/docs/"},
                     {"label": "Pod Disruptions", "url": "https://kubernetes.io/docs/concepts/workloads/pods/disruptions/"},
                     {"label": "Resource management for Pods", "url": "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Kubernetes configuration", "url": "https://kubernetes.io/docs/concepts/configuration/"},
                {"label": "Configure liveness/readiness/startup probes", "url": "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"},
                {"label": "Horizontal Pod Autoscaling", "url": "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"},
                {"label": "KEDA — Kubernetes Event-driven Autoscaling", "url": "https://keda.sh/docs/"},
                {"label": "Pod Disruption Budgets", "url": "https://kubernetes.io/docs/tasks/run-application/configure-pdb/"},
                {"label": ".NET runtime configuration (GC & container knobs)", "url": "https://learn.microsoft.com/dotnet/core/runtime-config/"},
                {"label": "ASP.NET Core graceful shutdown", "url": "https://learn.microsoft.com/aspnet/core/fundamentals/host/web-host"},
                {"label": "External Secrets Operator", "url": "https://external-secrets.io/"},
            ]},
        ],
    },
]
