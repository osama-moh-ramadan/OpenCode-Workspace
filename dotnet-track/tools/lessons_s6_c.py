"""Stage 6, Module 1 — Kubernetes fundamentals (lesson 4)."""

TODAY = "2026-10-22"

LESSONS_S6_C = [
    {
        "id": "s6-m1-l4",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
**Compose بيشغّل حاويات. Kubernetes بيدير حالة نظام.** الفرق ده هو كل الحكاية:
لما حاوية تقع، K8s بيعيد جدولتها على node تانية. لما الحمل يزيد، بيضيف نسخ. لما تنشر إصدار جديد،
بيبدّل النسخ تدريجيًا ويرجع للإصدار السابق بأمر واحد.

الدرس ده هدفه حاجتين عمليتين:
1. **خريطة مسار الطلب** من المتصفح للحاوية (DNS → Ingress → Service → Endpoints → Pod) — من غيرها كل عطل هيبدو سحرًا.
2. **manifests تكتبها بنفسك** (Namespace/Deployment/Service/Ingress) وتشغّلها على cluster محلي (kind/minikube).

⚠ **قبل ما تبدأ**: Kubernetes مهارة مطلوبة في إعلانات الشغل، بس **مش شرط لكل مشروع**.
لو فريق صغير أو نظام من 3 خدمات، Container Apps/App Service ممكن يكونوا أنسب (درس 6.2.1).
هنا بنتعلم الأساس اللي يخليك **تفهم** أي منصة حاويات، وتشتغل بثقة لو الشركة بتستخدم K8s.
"""},
            {"type": "terms", "items": [
                {"term": "Cluster / Node / Control Plane", "def": "الـcluster = مجموعة nodes (أجهزة/VMs) + control plane (API server، scheduler، controller manager، etcd). انت بتتكلم مع الـAPI server فقط."},
                {"term": "Pod", "def": "أصغر وحدة نشر: حاوية واحدة (أو أكتر) بتتشارك الشبكة والتخزين. ★ الـPods **مؤقتة** — بتتموت وتتحل محلها."},
                {"term": "ReplicaSet / Deployment", "def": "الـDeployment بيوصف الحالة المرغوبة (صورة، عدد نسخ، استراتيجية تحديث) وبيدير ReplicaSets اللي بتحافظ على العدد."},
                {"term": "Service (ClusterIP)", "def": "عنوان ثابت وموزّع حمل لمجموعة Pods متغيرة. النوع الافتراضي ClusterIP = داخلي فقط داخل الـcluster."},
                {"term": "Endpoints / EndpointSlice", "def": "القائمة الفعلية لعناوين الـPods الجاهزة اللي الـService بيوجّه لها. ★ لو فاضية = مفيش Pod جاهز = 503."},
                {"term": "Ingress / IngressClass", "def": "قواعد HTTP(S) للدخول من بره (host/path → service). بيحتاج **Ingress controller** شغال (nginx/Traefik/ALB)."},
                {"term": "NodePort / LoadBalancer", "def": "NodePort = منفذ على كل node (30000-32767) · LoadBalancer = LB سحابي خارجي (يتعمل تلقائيًا على AKS/EKS/GKE)."},
                {"term": "Namespace", "def": "تقسيم منطقي داخل الـcluster (dev/staging/prod أو لكل فريق). الأسماء والـDNS والـquotas بتُدار على مستواه."},
                {"term": "Label / Selector", "def": "كل الربط في K8s بالـlabels: Deployment → Pods، Service → Pods، NetworkPolicy → Pods. غلطة في label = خدمة مش متوصلة."},
                {"term": "CoreDNS", "def": "DNS الداخلي: `orders` أو `orders.shop.svc.cluster.local` → ClusterIP. ★ ده نفسه discovery بالاسم اللي استخدمته في Aspire."},
                {"term": "kubelet / kube-proxy / CNI", "def": "kubelet = وكيل الـnode بيشغّل الحاويات · kube-proxy = قواعد التوجيه للـServices · CNI = الشبكة بين الـPods."},
                {"term": "Gateway API", "def": "الجيل التالي من Ingress (أدوار وأدق تعبيرًا). موجود في التوزيعات الحديثة — تعلّم Ingress الأول وشوفه بعدين."},
            ]},
            {"type": "heading", "level": 2, "text": "1) خريطة مسار الطلب (احفظها — دي مفتاح كل تشخيص)"},
            {"type": "code", "lang": "text", "filename": "docs/k8s-request-path.md", "title": "من المتصفح للحاوية — وكل نقطة فشل محتملة", "code": r'''
 ① المتصفح:  https://shop.example.com/api/orders
      │  DNS عام (A/CNAME) → عنوان الـLoad Balancer
      ▼
 ② Load Balancer (سحابي) — Ingress type: LoadBalancer
      │  يوجّه 443/80 لـnodes اللي عليها Ingress controller pods
      ▼
 ③ Ingress Controller (nginx pod) — يقرأ قواعد الـIngress
      │  host: shop.example.com  +  path: /api/orders (Prefix)  →  backend
      │  ⚠ فشل هنا = 404 (مفيش قاعدة مطابقة) أو 503 (مفيش endpoints) أو خطأ شهادة TLS
      ▼
 ④ Service "orders" (ClusterIP 10.96.x.x:80) — عنوان ثابت افتراضي
      │  kube-proxy/iptables/IPVS بيوزّع الحمل على الـEndpoints
      │  ⚠ Endpoints فاضية = مفيش Pod **جاهز** (readiness فاشل) = 503
      ▼
 ⑤ EndpointSlice:  10.244.1.7:8080 · 10.244.2.9:8080   ← Pods جاهزة فعلًا
      │
      ▼
 ⑥ Pod "orders-7d9f…" → Container على containerPort 8080
         │  ASP.NET Core بيسمع على 8080 (ASPNETCORE_HTTP_PORTS)
         ▼
      ⑦ النداءات الداخلية من جوه الـcluster:
         orders  →  http://catalog:8080            (نفس الـnamespace)
         orders  →  http://catalog.shop-prod.svc.cluster.local:8080   (namespace مختلف)
         ★ نفس الكود اللي كتبته في Aspire (`https+http://catalog`) — discovery بالاسم

 ⑧ البيانات: Pod → Service "postgres" (أو managed DB خارج الـcluster برابط اتصال)
    ⚠ قواعد البيانات stateful: في الإنتاج المُدار (Azure Database/Flexible Server) أسهل وأأمن
      من تشغيل Postgres جوه الـcluster (StatefulSet + تخزين + نسخ احتياطي)

 ── نقاط الفشل الأشهر حسب الرقم ──
 ① DNS/شهادة منتهية            → المتصفح بيرفض قبل ما يوصل لأي حاجة
 ② LB صحي بس مفيش controller    → timeout
 ③ قواعد Ingress غلط / TLS سر مفقود → 404 / 502 / handshake error
 ④ Service selector ما بيطابقش labels الـPod → Endpoints فاضية → 503
 ⑤ readiness probe فاشل         → Pod شغال بس مش في الـEndpoints (مفيش حركة)
 ⑥ image غلط / منفذ غلط         → CrashLoopBackOff أو اتصال مرفوض
 ⑦ DNS داخلي / NetworkPolicy مانع → timeout من خدمة لخدمة
'''},
            {"type": "heading", "level": 2, "text": "2) Manifests كاملة لنظام المتجر"},
            {"type": "code", "lang": "yaml", "filename": "k8s/base/orders.yaml", "title": "Namespace + Deployment + Service + Ingress", "code": r'''
apiVersion: v1
kind: Namespace
metadata:
  name: shop
  labels:
    app.kubernetes.io/part-of: shop
    environment: dev
---
# ══════════════ Deployment: الحالة المرغوبة للخدمة ══════════════
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
  namespace: shop
  labels: &labels                       # ✓ anchor لإعادة الاستخدام (kustomize أفضل — تحت)
    app.kubernetes.io/name: orders
    app.kubernetes.io/part-of: shop
    app.kubernetes.io/version: "1.4.0"
spec:
  replicas: 2                           # ★ ≥2 دايمًا في الإنتاج (نسخة واحدة = downtime عند أي node issue)
  revisionHistoryLimit: 5               # عشان rollback يقدر يرجع لإصدارات سابقة
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0                 # ✓ مفيش نسخة تقل أثناء التحديث (بلا downtime)
      maxSurge: 1                       # نسخة إضافية مؤقتة
  selector:
    matchLabels:
      app.kubernetes.io/name: orders    # ⚠ لازم يطابق template.metadata.labels **بالظبط**
  template:
    metadata:
      labels:
        *labels
      annotations:
        # ✓ حيلة شائعة لإجبار rollout عند تغيير ConfigMap/Secret
        shop.example.com/config-hash: "REPLACE_ME"
    spec:
      serviceAccountName: orders        # هوية مخصصة (لا تستخدم default)
      terminationGracePeriodSeconds: 45 # مهلة الإيقاف اللطيف (درس 6.1.5)
      securityContext:                  # على مستوى الـPod
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: orders
          # ★ digest ثابت — بلا :latest (درس 6.1.3)
          image: ghcr.io/<org>/shop-orders@sha256:REPLACE_WITH_DIGEST
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: ASPNETCORE_HTTP_PORTS
              value: "8080"
            - name: OTEL_SERVICE_NAME
              value: orders
          envFrom:                      # ✓ كل الإعداد من ConfigMap (درس 6.1.5)
            - configMapRef: { name: orders-config }
          # ★ الأسرار: مفاتيح مختارة — مش Secret كامل بالغلط
          #   (والإنتاج الأفضل: CSI Secrets Store / External Secrets — درس 6.2.3)
          env:
            - name: ConnectionStrings__shopdb
              valueFrom:
                secretKeyRef: { name: orders-secrets, key: shopdb }
            - name: ConnectionStrings__rabbit
              valueFrom:
                secretKeyRef: { name: orders-secrets, key: rabbit }
          resources:
            requests: { cpu: "100m", memory: "256Mi" }   # ← أساس الجدولة والـHPA
            limits:   { cpu: "1000m", memory: "512Mi" }  # ← memory limit = OOMKill لو تجاوز
          # ═══ Probes: 3 أنواع بأدوار مختلفة (درس 6.1.5 بالتفصيل) ═══
          startupProbe:                 # يحمي الإقلاع البطيء من الـliveness
            httpGet: { path: /alive, port: http }
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:               # يقرر: هل يوجَّه لها traffic؟
            httpGet: { path: /health, port: http }
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          livenessProbe:                # يقرر: هل نعيد تشغيل الحاوية؟
            httpGet: { path: /alive, port: http }   # ★ /alive بلا تبعيات — مش /health!
            periodSeconds: 20
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:              # على مستوى الحاوية
            runAsUser: 1654             # ✓ مستخدم `app` في صور .NET 8+
            runAsGroup: 1654
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities: { drop: ["ALL"] }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - name: tmp
          emptyDir: { sizeLimit: 64Mi }
---
# ══════════════ Service: عنوان ثابت + توزيع حمل داخلي ══════════════
apiVersion: v1
kind: Service
metadata:
  name: orders                # ← الاسم ده هو عنوان الـDNS: http://orders:8080
  namespace: shop
  labels:
    app.kubernetes.io/name: orders
spec:
  type: ClusterIP             # داخلي فقط — الوصول من بره عبر Ingress
  selector:
    app.kubernetes.io/name: orders     # ⚠ لازم يطابق labels الـPods
  ports:
    - name: http
      port: 8080              # منفذ الـService
      targetPort: http        # ✓ بالإسم (أوضح) مش بالرقم
---
# ══════════════ Ingress: الدخول من بره ══════════════
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
  namespace: shop
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "2m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"   # ★ من ميزانية المهلة (درس 5.2.4)
spec:
  ingressClassName: nginx     # ⚠ لازم يتطابق مع الـcontroller المثبت
  tls:
    - hosts: [shop.example.com]
      secretName: shop-tls    # شهادة في Secret من نوع kubernetes.io/tls (أو cert-manager)
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /api/orders
            pathType: Prefix
            backend:
              service: { name: orders,  port: { number: 8080 } }
          - path: /api/catalog
            pathType: Prefix
            backend:
              service: { name: catalog, port: { number: 8080 } }
          - path: /
            pathType: Prefix
            backend:
              service: { name: gateway, port: { number: 8080 } }
'''},
            {"type": "code", "lang": "yaml", "filename": "k8s/kustomization.yaml", "title": "kustomize: نفس الـmanifests لكل بيئة بلا نسخ ملفات", "code": r'''
# ★ الحل العملي لـ«dev/staging/prod بملفات مختلفة»:
#   قاعدة واحدة (base) + overlays بتعدّل الفرق فقط.
# kustomize مدمج في kubectl: `kubectl apply -k k8s/overlays/prod`

# ── k8s/base/kustomization.yaml ──
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: shop
resources:
  - orders.yaml
  - catalog.yaml
  - payments.yaml
  - gateway.yaml
  - ingress.yaml
commonLabels:
  app.kubernetes.io/part-of: shop

# ── k8s/overlays/dev/kustomization.yaml ──
# apiVersion: kustomize.config.k8s.io/v1beta1
# kind: Kustomization
# namespace: shop-dev
# resources: [../../base]
# replicas:
#   - name: orders
#     count: 1
# patches:
#   - target: { kind: Deployment, name: orders }
#     patch: |-
#       - op: replace
#         path: /spec/template/spec/containers/0/resources/requests/memory
#         value: 128Mi

# ── k8s/overlays/prod/kustomization.yaml ──
# namespace: shop-prod
# resources: [../../base]
# replicas:
#   - name: orders
#     count: 4
# images:                              # ★ تثبيت الصورة بالـdigest لكل إصدار
#   - name: ghcr.io/<org>/shop-orders
#     digest: sha256:REPLACE_WITH_DIGEST
# patches:
#   - path: hpa.yaml                   # HPA في الإنتاج فقط (درس 6.1.5)
#   - path: pdb.yaml
#   - path: networkpolicy.yaml
'''},
            {"type": "heading", "level": 2, "text": "3) cluster محلي: من صفر لخدمة شغالة"},
            {"type": "code", "lang": "bash", "title": "kind أو minikube + ingress-nginx + نشر وفحص", "code": r'''
# ═══ 1) cluster محلي (kind — الأخف والأسرع للتعلم) ═══
# تثبيت: https://kind.sigs.k8s.io/docs/user/quick-start/#installation
cat > kind.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:            # ★ يخلي Ingress controller يوصل من جهازك
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
      - containerPort: 443
        hostPort: 8443
        protocol: TCP
  - role: worker
  - role: worker
EOF

kind create cluster --name shop --config kind.yaml
kubectl cluster-info --context kind-shop
kubectl get nodes -o wide

# بديل: minikube
#   minikube start --driver=docker --cpus=4 --memory=8g
#   minikube addons enable ingress metrics-server

# ═══ 2) صوَرِك جوه الـcluster (kind ما بيسحبش من daemon جهازك تلقائيًا) ═══
kind load docker-image shop/orders:1.4.0 --name shop
kind load docker-image shop/catalog:1.4.0 --name shop
# أو استخدم registry محلي (أقرب للواقع):
#   docker run -d --restart=always -p 127.0.0.1:5001:5000 --name registry registry:2
#   docker tag shop/orders:1.4.0 localhost:5001/shop-orders:1.4.0 && docker push localhost:5001/shop-orders:1.4.0
# (minikube: `minikube image load shop/orders:1.4.0` أو `eval $(minikube docker-env)`)

# ═══ 3) Ingress controller + metrics-server (مطلوب لـHPA و`kubectl top`) ═══
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# ⚠ على cluster محلي بشهادات ذاتية قد تحتاج: --kubelet-insecure-tls (شوف توثيق metrics-server)

# ═══ 4) النشر ═══
kubectl apply -k k8s/overlays/dev            # أو kubectl apply -f k8s/base/
kubectl -n shop get pods -o wide -w          # ← راقب الحاويات وهي بتطلع (Ctrl+C للخروج)

# تحقق من الربط بالـlabels (أشهر مصدر مشاكل)
kubectl -n shop get deploy orders -o jsonpath='{.spec.selector.matchLabels}{"\n"}'
kubectl -n shop get pods -L app.kubernetes.io/name
kubectl -n shop get endpoints orders          # ★ لو فاضية → الـselector أو الـreadiness غلط
kubectl -n shop get endpointslices

# ═══ 5) جرّب الطلبات ═══
kubectl -n shop port-forward svc/orders 8080:8080 &
curl -s http://localhost:8080/health
curl -s http://localhost:8080/alive

# عبر الـIngress (kind بيفتح 8080 محليًا) — بلا DNS حقيقي:
curl -s -H 'Host: shop.example.com' http://localhost:8080/api/orders/health

# اختبار DNS الداخلي من جوه الـcluster (بيثبت discovery بالاسم)
kubectl -n shop run dns-test --rm -it --restart=Never --image=mcr.microsoft.com/dotnet/sdk:10.0 -- \
  bash -lc 'getent hosts orders; getent hosts catalog.shop.svc.cluster.local'

# ═══ 6) التحديث والـrollback ═══
kubectl -n shop set image deploy/orders orders=ghcr.io/<org>/shop-orders@sha256:<new-digest>
kubectl -n shop rollout status deploy/orders --timeout=180s
kubectl -n shop rollout history deploy/orders
kubectl -n shop rollout undo deploy/orders              # ← رجوع فوري للإصدار السابق
kubectl -n shop scale deploy/orders --replicas=4

# ═══ 7) الهدم ═══
kubectl delete -k k8s/overlays/dev
kind delete cluster --name shop
'''},
            {"type": "code", "lang": "bash", "title": "kubectl للتشخيص: الأوامر اللي هتستخدمها كل يوم", "code": r'''
# ── نظرة عامة ──
kubectl -n shop get all                          # pods/services/deployments/…
kubectl -n shop get pods -o wide --sort-by=.status.startTime
kubectl -n shop get events --sort-by=.lastTimestamp | tail -30   # ★ أول مكان تبص فيه

# ── ليه الـPod مش شغال؟ ──
kubectl -n shop describe pod <pod>               # Events + أسباب الجدولة + نتائج الـprobes
kubectl -n shop get pod <pod> -o jsonpath='{.status.containerStatuses[*].state}{"\n"}'
kubectl -n shop get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}'
#   → OOMKilled · Error · ContainerStatusUnknown · …

# ── اللوجات ──
kubectl -n shop logs <pod> --tail 200 -f
kubectl -n shop logs <pod> --previous            # ★ لوجات الحاوية **السابقة** (بعد crash/restart)
kubectl -n shop logs -l app.kubernetes.io/name=orders --all-containers --tail 100

# ── جوه الحاوية ──
kubectl -n shop exec -it <pod> -- sh             # (لو الصورة فيها shell)
kubectl -n shop exec <pod> -- printenv | grep -E 'ASPNETCORE|OTEL|ConnectionStrings' | sed 's/Password=.*/Password=***/'
# ★ صورة chiseled/distroless بلا shell → حاوية تشخيص مؤقتة:
kubectl -n shop debug -it <pod> --image=mcr.microsoft.com/dotnet/sdk:10.0 --target=orders -- /bin/bash
# من جواها: curl http://localhost:8080/health   (بتتشارك الشبكة مع الحاوية المستهدفة)

# ── الشبكة ──
kubectl -n shop get svc,endpoints,ingress
kubectl -n shop describe ingress shop
kubectl -n ingress-nginx logs -l app.kubernetes.io/component=controller --tail 100 | grep -E ' 50[0-9] | 404 '
kubectl get networkpolicy -A

# ── الموارد (يحتاج metrics-server) ──
kubectl -n shop top pods
kubectl -n shop top nodes
kubectl describe node <node> | grep -A6 'Allocated resources'   # ★ ليه الـPod Pending؟

# ── مقارنة قبل التطبيق (مفيد في الـPR) ──
kubectl diff -k k8s/overlays/prod

# ── حالة الـrollout ──
kubectl -n shop rollout status deploy/orders
kubectl -n shop get rs --sort-by=.metadata.creationTimestamp | tail -5
'''},
            {"type": "table", "head": ["العَرَض", "السبب الأشهر", "أمر التشخيص", "الإصلاح"], "rows": [
                ["`ImagePullBackOff` / `ErrImagePull`", "اسم/وسم صورة غلط، أو registry خاص بلا `imagePullSecrets`", "`describe pod` → Events", "صحّح الصورة (digest)، أو أضف secret للسحب"],
                ["`CrashLoopBackOff`", "التطبيق بيرمي عند الإقلاع (إعداد ناقص/منفذ غلط/DB مش متاح)", "`logs --previous`", "صلّح السبب — مش زيادة الـbackoff"],
                ["`Pending` (بلا جدولة)", "موارد غير كافية (requests أكبر من المتاح) أو nodeSelector/taints", "`describe pod` + `describe node` → Allocated resources", "قلّل الـrequests أو زوّد nodes"],
                ["`OOMKilled` (يعيد التشغيل باستمرار)", "استهلاك الذاكرة تجاوز الـlimit (.NET بيوسّع الـGC heap حسب المتاح)", "`jsonpath …lastState.terminated.reason` + `top pods`", "زوّد limit واضبط `DOTNET_GCHeapHardLimitPercent`/طلبات الذاكرة (درس 6.1.5)"],
                ["Pod `Running` بس مفيش traffic", "`readinessProbe` فاشل → الـPod بره الـEndpoints", "`get endpoints orders` (فاضية؟)", "صلّح سبب فشل الفحص (تبعيات/مهلة) — مش إلغاء الـprobe"],
                ["`CreateContainerConfigError`", "ConfigMap/Secret أو مفتاح داخلهم مش موجود", "`describe pod`", "أنشئ المورد أو صحّح اسم المفتاح"],
                ["Ingress بيرد 404", "host/path مش مطابق، أو `ingressClassName` غلط", "`describe ingress` + لوجات الـcontroller", "طابق القواعد مع الطلب (Host header)"],
                ["Ingress بيرد 503", "مفيش endpoints جاهزة للـService الخلفي", "`get endpoints` للخدمة المستهدفة", "شوف الـreadiness/الـlabels"],
                ["خدمة تنادي خدمة تانية: timeout", "اسم DNS غلط / namespace مختلف / NetworkPolicy مانع", "`kubectl debug` + `getent hosts <svc>` + `get networkpolicy -A`", "الاسم الكامل `<svc>.<ns>.svc.cluster.local` أو سياسة سماح"],
                ["`Evicted`", "ضغط موارد على الـnode (disk/memory)", "`describe pod` → `Evicted`", "حدود موارد + تنظيف صور/لوجات على الـnode"],
            ]},
            {"type": "table", "head": ["المفهوم", "Docker Compose", "Kubernetes"], "rows": [
                ["تعريف الخدمة", "`services: orders:` في YAML", "`Deployment` + `Service` (موردَين منفصلين)"],
                ["عدد النسخ", "`--scale orders=3` (يدوي)", "`spec.replicas` + `HPA` (تلقائي)"],
                ["discovery بالاسم", "اسم الخدمة = hostname على الشبكة", "اسم الـService = DNS عبر CoreDNS (نفس الشكل)"],
                ["منافذ للخارج", "`ports: [\"8080:8080\"]`", "`Ingress` (HTTP) أو `Service type: LoadBalancer`"],
                ["فحص الصحة", "`healthcheck:` في الحاوية", "`readinessProbe`/`livenessProbe`/`startupProbe` من الـkubelet"],
                ["البيانات", "`volumes:` (named/bind)", "`PersistentVolumeClaim` + `StatefulSet` (أو DB مُدارة بره)"],
                ["الإعدادات/الأسرار", "`.env` / `env_file`", "`ConfigMap` / `Secret` (+ CSI/External Secrets)"],
                ["إعادة التشغيل", "`restart: unless-stopped`", "الـcontroller بيعيد الجدولة تلقائيًا على أي node"],
                ["التحديث", "`up -d` (إعادة إنشاء)", "`RollingUpdate` + `rollout undo` (بلا downtime)"],
                ["العزل", "شبكات وprofiles", "`Namespace` + `NetworkPolicy` + `ResourceQuota`"],
            ]},
            {"type": "callout", "kind": "tip", "title": "8 قواعد لـmanifests محترمة",
             "md": """
1. **labels موحّدة** (`app.kubernetes.io/name|part-of|version|component`) — كل الربط والفلترة والمراقبة بتعتمد عليها.
2. **`selector` = `template.labels` بالظبط** — أشهر سبب لـEndpoints فاضية و503.
3. **الصورة بالـdigest**، وبلا `:latest`، و`imagePullPolicy: IfNotPresent` (digest ثابت = بلا سحب زائد).
4. **3 probes بأدوارها**: `startup` للإقلاع البطيء، `readiness` = `/health` (مع التبعيات)،
   `liveness` = `/alive` (**بلا تبعيات**) — درس 2.3.4 و6.1.5.
5. **`requests` و`limits` لكل حاوية** — بلاها الجدولة تخمين والـHPA مش هيشتغل.
6. **`securityContext` متصلد**: non-root 1654 + `readOnlyRootFilesystem` + `capabilities.drop: [ALL]` + `seccompProfile`.
7. **`replicas ≥ 2` + `PodDisruptionBudget` + topology spread** — نسخة واحدة معناها downtime عند أي صيانة.
8. **الـmanifests كود في المستودع وتُراجع في الـPR** — `kubectl diff` قبل `apply`، وkustomize/Helm للبيئات
   (بلا نسخ مجلدات `prod/` و`dev/` كاملة).

⚠ **بلا `kubectl apply` يدوي في الإنتاج**: أي تغيير لازم يجي من الـpipeline (أو GitOps — درس 6.3.3)،
وإلا هتوصل لحالة «الـcluster مش زي الكود» ومحدش يعرف الحقيقة.
"""},
            {"type": "callout", "kind": "warn", "title": "إمتى K8s **مش** الاختيار الصح",
             "md": """
**اختار K8s لو:**
- عندك ≥ فريقين بينشروا بشكل مستقل، أو ≥ 8–10 خدمات.
- محتاج تحكم دقيق في الجدولة/الموارد/الشبكة (multi-tenant، عزل قوي).
- محتاج portability بين سحب أو تشغيل hybrid/on-prem.
- فيه شخص/فريق **يملك** المنصة (تشغيل، ترقيات، أمان، مراقبة).

**اختار Container Apps / App Service / ECS لو:**
- فريق صغير، 2–5 خدمات، ومفيش منصة متخصصة.
- التكلفة التشغيلية (وقت الفريق) أهم من التحكم الكامل.
- النظام event-driven بسيط (Container Apps بيدعم scale-to-zero وKEDA مدمج).

**الأرقام اللي لازم تعرفها**: تشغيل K8s إنتاجي بيكلّف وقتًا حقيقيًا — ترقيات (كل ~4 شهور إصدار)،
أمان (RBAC/NetworkPolicy/secrets)، مراقبة، حوادث. فريق من 3 مطورين بدون DevOps هيقضي وقتًا
في المنصة أكثر من المنتج. **التعقيد تكلفة، مش ميزة.**

✅ **الخلاصة العملية للسوق**: تعلّم الأساس (الدرس ده) + manifests + تشخيص — ده مطلوب في أغلب إعلانات
وظائف .NET المتوسطة/السينيور. وبعدين اختار المنصة بحسب حجم النظام، مش بحسب الحماس.
"""},
            {"type": "checkpoints", "items": [
                "أشرح مسار الطلب من المتصفح للحاوية (DNS → LB → Ingress controller → Service → Endpoints → Pod) وأحدد نقطة الفشل من العَرَض.",
                "أكتب manifests كاملة: Namespace + Deployment (labels/strategy/probes/resources/securityContext) + Service + Ingress بـTLS.",
                "أشغّل cluster محلي (kind/minikube)، أحمل الصور، أثبّت ingress-nginx وmetrics-server، وأنشر وأتحقق.",
                "أتشخص بـkubectl: `describe` · `logs --previous` · `events` · `get endpoints` · `top` · `debug` · `rollout undo`.",
                "أفرّق بين compose وK8s، وأعرف إمتى K8s مش الاختيار الصح (التعقيد تكلفة).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "الـPod `Running` و`READY 0/1`، والـIngress بيرد 503. السبب؟",
                 "options": [
                     "الصورة غلط",
                     "الـ`readinessProbe` فاشل → الـPod خارج الـEndpoints → مفيش هدف للـService. شوف `kubectl get endpoints` وسبب فشل الفحص",
                     "الـIngress controller واقع",
                     "الـnamespace غلط",
                 ], "answer": 1,
                 "explain": "تصميم النظام مقصود: readiness بيتحكم في توجيه الحركة. لو `/health` بيرد 503 (تابع واقع)، الـPod بيتشال من الـEndpoints لحد ما يتعافى — وده السلوك الصحيح."},
                {"q": "ليه `livenessProbe` لازم يشير لـ`/alive` مش `/health`؟",
                 "options": [
                     "أسرع",
                     "لأن `/health` بيتحقق من التبعيات: لو DB وقعت، كل النسخ هتفشل liveness → K8s يعيد تشغيلهم كلهم → انهيار متسلسل بدل انتظار التعافي",
                     "مطلوب من ASP.NET Core",
                     "عشان الـlogs",
                 ], "answer": 1,
                 "explain": "liveness معناه «الحاوية دي ميتة ولازم تعيد تشغيلها». فشل تابع خارجي مش معناه إن تطبيقك ميت — عشان كده نفصل `/alive` (رخيص) عن `/health` (التبعيات)."},
                {"q": "الـService `orders` موجود بس `kubectl get endpoints orders` فاضي. أشيك على إيه أولًا؟",
                 "options": [
                     "الـIngress",
                     "تطابق `spec.selector` في الـService مع `template.metadata.labels` في الـDeployment، وحالة readiness للـPods",
                     "الـnamespace",
                     "الصلاحيات",
                 ], "answer": 1,
                 "explain": "الربط كله بالـlabels. غلطة حرف في الـselector = Service بلا أهداف = 503. وبعدها شوف readiness."},
                {"q": "خدمة `orders` في namespace `shop` عايزة تنادي `catalog` في namespace `shop-prod`. العنوان؟",
                 "options": [
                     "`http://catalog:8080`",
                     "`http://catalog.shop-prod.svc.cluster.local:8080` — الاسم المختصر يعمل بس جوه نفس الـnamespace",
                     "`http://localhost:8080`",
                     "`http://catalog.prod:8080`",
                 ], "answer": 1,
                 "explain": "DNS الداخلي: `<service>` = نفس الـnamespace، `<service>.<namespace>` = namespace تاني، `<service>.<ns>.svc.cluster.local` = الاسم الكامل."},
                {"q": "الـPod حالته `Pending` ومش بيتجدول. أشيك على إيه؟",
                 "options": [
                     "اللوجات",
                     "`kubectl describe pod` (Events) + `kubectl describe node` → Allocated resources — غالبًا الـ`requests` أكبر من المتاح، أو taints/nodeSelector",
                     "الـIngress",
                     "الـSecrets",
                 ], "answer": 1,
                 "explain": "الجدولة بتعتمد على الـrequests (مش limits). لو مجموع الـrequests على الـnode تجاوز المتاح، الـPod يفضل Pending."},
                {"q": "نشرت إصدار جديد والخدمة باظت. أسرع رجوع آمن؟",
                 "options": [
                     "`kubectl delete deploy` وإعادة apply",
                     "`kubectl rollout undo deployment/orders` (بيرجع لـReplicaSet السابق) — وبعدها تحقق بـ`rollout status` وصلّح السبب",
                     "إعادة تشغيل الـPods",
                     "تعديل الصورة يدويًا",
                 ], "answer": 1,
                 "explain": "الـDeployment بيحتفظ بـReplicaSets سابقة (`revisionHistoryLimit`)، فالـrollback فوري. ★ بس لو فيه migration غير متوافقة، الرجوع للكود لوحده مش كفاية — عشان كده expand/contract (درس 3.3.4)."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "انشر نظامك على cluster محلي",
                 "md": "أنشئ cluster بـkind أو minikube، وانشر خدمتين + gateway + Ingress بـmanifests مكتوبة في المستودع (kustomize overlays لـdev)، وأثبت إن الطلب بيمشي من بره الـcluster للخدمة ومنها لخدمة تانية بالـDNS الداخلي.",
                 "criteria": [
                     "كل الـmanifests في `k8s/` بالمستودع (base + overlays) — بلا `kubectl apply` من ملفات مؤقتة",
                     "Deployment فيه: labels موحّدة · `selector` مطابق · 3 probes · requests/limits · securityContext متصلد · RollingUpdate بـ`maxUnavailable: 0`",
                     "الصورة بالـdigest (مش `:latest`) و`imagePullPolicy` مضبوطة",
                     "Service (ClusterIP) + Ingress بـ`ingressClassName` صحيح — وطلب من بره الـcluster بيرد 200 (مخرجات curl مع Host header)",
                     "إثبات discovery داخلي: خدمة تنادي التانية بـ`http://<svc>:8080` بنجاح (مخرجات من داخل pod أو `kubectl debug`)",
                     "`kubectl get endpoints` غير فاضية لكل خدمة (مخرجات محفوظة)",
                     "إثبات rollout وrollback: `set image` → `rollout status` → `rollout undo` (مخرجات الثلاثة)",
                     "`docs/k8s.md`: أمر التشغيل من صفر + المتطلبات + إزاي تتشخص (أهم 8 أوامر kubectl)",
                 ],
                 "hint": "ابدأ بخدمة واحدة + Service واطلبها بـ`port-forward`. لما تنجح، أضف الـIngress. لما تنجح، أضف الخدمة التانية والنداء الداخلي. كل خطوة بدليل.",
                 "solution": "",
                 "resources": [
                     {"label": "kind — quick start", "url": "https://kind.sigs.k8s.io/docs/user/quick-start/"},
                     {"label": "Kubernetes concepts", "url": "https://kubernetes.io/docs/concepts/"},
                     {"label": "ingress-nginx on kind", "url": "https://kubernetes.github.io/ingress-nginx/deploy/"},
                 ]},
                {"id": "t2", "title": "تشخيص 6 أعطال مفتعلة",
                 "md": "افتعل 6 أعطال مختلفة في cluster محلي (صورة غلط · selector غلط · readiness فاشل · memory limit صغير · ConfigMap ناقص · قاعدة Ingress غلط)، وشخّص كل واحد **بالأوامر فقط** وسجّل: العَرَض، الأمر اللي كشفه، السبب الجذري، والإصلاح.",
                 "criteria": [
                     "6 أعطال مختلفة الأنواع — لكل واحد الأمر اللي افتعله (موثق عشان تتخلص منه)",
                     "لكل عطل: العَرَض الظاهر (`kubectl get pods` / كود HTTP) مقابل السبب الحقيقي",
                     "الأمر التشخيصي الحاسم مذكور لكل عطل (`describe` / `logs --previous` / `get endpoints` / `jsonpath lastState` / `describe node`)",
                     "عطل `OOMKilled` مثبت بـ`lastState.terminated.reason` مع تفسير سلوك .NET مع حدود الذاكرة",
                     "عطل readiness مثبت بـEndpoints فاضية + 503 من الـIngress (مش من التطبيق)",
                     "جدول في `docs/k8s-troubleshooting.md`: العَرَض × التشخيص × السبب × الإصلاح (6 صفوف على الأقل)",
                     "بعد كل إصلاح: دليل إن الحالة رجعت سليمة (Pods ready + طلب 200)",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Debug running pods", "url": "https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/"},
                     {"label": "kubectl cheat sheet", "url": "https://kubernetes.io/docs/reference/kubectl/cheatsheet/"},
                     {"label": "Pod lifecycle & conditions", "url": "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"},
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Kubernetes concepts", "url": "https://kubernetes.io/docs/concepts/"},
                {"label": "Deployments", "url": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/"},
                {"label": "Services", "url": "https://kubernetes.io/docs/concepts/services-networking/service/"},
                {"label": "Ingress", "url": "https://kubernetes.io/docs/concepts/services-networking/ingress/"},
                {"label": "Gateway API", "url": "https://gateway-api.sigs.k8s.io/"},
                {"label": "kubectl reference", "url": "https://kubernetes.io/docs/reference/kubectl/"},
                {"label": "kind (Kubernetes in Docker)", "url": "https://kind.sigs.k8s.io/"},
                {"label": "Kustomize", "url": "https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/"},
                {"label": "AKS docs (Azure Kubernetes Service)", "url": "https://learn.microsoft.com/azure/aks/"},
            ]},
        ],
    },
]
