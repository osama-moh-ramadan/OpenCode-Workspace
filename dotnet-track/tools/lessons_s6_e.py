# -*- coding: utf-8 -*-
"""Stage 6 module 2 (part A): s6-m2-l1 (App Service vs Container Apps vs AKS), s6-m2-l2 (Azure Functions)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s6-m2-l1 — App Service مقابل Container Apps مقابل AKS
# ══════════════════════════════════════════════════════════════════════════
_L1 = {
    "id": "s6-m2-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "عندك صورة Docker جاهزة من المرحلة اللي فاتت. السؤال دلوقتي: **تشغّلها فين على Azure؟** الإجابة الغلط بتكلّف فلوس كل شهر وإجابة صح بتوفرلك ساعات تشغيل. في الدرس ده هتقارن 4 خدمات (App Service · Container Apps · AKS · Container Instances) بمعايير حقيقية: **العبء التشغيلي · scale-to-zero · cold start · التحكم في الشبكة · طريقة النشر والإصدارات · الحد الأقصى للتوسع · نموذج الفوترة** — وهتخرج بقرار مكتوب (ADR) مش بإحساس."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "App Service", "def": "PaaS كلاسيكي للويب: تنشر كود (zip) أو صورة حاوية، وخطة (Plan) بتدفع مقابلها سواء فيه حمل أو لا. فيه **Deployment slots** للنشر الآمن."},
            {"term": "Container Apps (ACA)", "def": "حاويات مُدارة مبنية على Kubernetes **من غير ما تشوف الـAPI**: revisions، ingress مبني على Envoy، **scale-to-zero**، وقواعد توسع مبنية على KEDA، وDapr مدمج."},
            {"term": "AKS", "def": "Kubernetes مُدار: بتاخد الـ**control plane** مُدار وبتدير **node pools** بنفسك. كل حاجة في المرحلة اللي فاتت (kubectl/HPA/Ingress) بتشتغل هنا."},
            {"term": "Container Instances (ACI)", "def": "حاوية واحدة أو مجموعة من غير orchestration: مهام قصيرة، CI runners، batch. ملهاش ingress أو scaling تلقائي."},
            {"term": "Scale-to-zero", "def": "الخدمة تنزّل عدد النسخ لصفر لما مفيش حمل، **فماتدفعش حاجة** — وتدفع أول ما يوصل طلب (بس بتستنى cold start)."},
            {"term": "Cold start", "def": "زمن أول طلب بعد فترة سكون: إقلاع الحاوية + إقلاع الـruntime + تحميل الـassembly. في .NET بيتراوح بين أجزاء من الثانية وثوانٍ حسب الحجم والخطة."},
            {"term": "Revision (في ACA)", "def": "نسخة غير قابلة للتغيير من تعريف التطبيق. كل نشر بيعمل revision جديدة، وبتقدر **تقسم الـtraffic** بينها (canary) أو ترجع لأي واحدة."},
            {"term": "Deployment slot (في App Service)", "def": "بيئة مطابقة للإنتاج على نفس الخطة؛ تنشر فيها، تختبر، وبعدين **swap** فوري.Slots مدفوعة حسب الخطة (Premium عادةً)."},
            {"term": "Consumption / Dedicated", "def": "في ACA: **Consumption** = فوترة على vCPU-second وذاكرة-second مع منحة مجانية شهرية، و**Dedicated** = على node pool ثابت (لأحمال مستمرة أو متطلبات خاصة)."},
            {"term": "Resource group", "def": "حاوية إدارية لكل موارد البيئة. حدود الصلاحيات والـtags وحذف البيئة كلها بتتم على مستوى المجموعة."},
        ]},

        # ── 1) الخدمات الأربعة
        {"type": "heading", "level": 2, "text": "① الخدمات الأربعة في جملة واحدة — ثم الجدول اللي بيحسم"},
        {"type": "text", "md": "**App Service**: «عايز موقع/API واحد يشتغل دايمًا بأقل إدارة». **Container Apps**: «عايز حاويات microservices بتتوسع بالأحداث وبتنزل لصفر من غير ما أدير cluster». **AKS**: «محتاج Kubernetes نفسه: CRDs/operators/StatefulSets/DaemonSets/service mesh مخصص/GPU/تحكم كامل في الشبكة». **ACI**: «عايز أشغّل حاوية مرة واحدة وأخلص»."},
        {"type": "table", "caption": "مقارنة 2026 — الأرقام التقريبية من توثيق Azure ومقارنات منشورة؛ تحقق من صفحة التسعير لمنطقتك",
         "head": ["المعيار", "App Service", "Container Apps", "AKS", "Container Instances"],
         "rows": [
             ["التجريد", "PaaS (كود أو حاوية)", "حاويات مُدارة على K8s مخفي", "Kubernetes مُدار", "حاوية واحدة"],
             ["العبء التشغيلي", "**منخفض**", "**منخفض–متوسط**", "**مرتفع** (nodes/tr upgrades/networking)", "منخفض"],
             ["Scale-to-zero", "✗ (دايمًا ≥1 instance)", "✓ **أصلي**", "△ (محتاج KEDA بنفسك)", "✗ (تشغيل لمرة واحدة)"],
             ["Cold start", "مفيش (دايمًا دافئ)", "ثوانٍ من الصفر؛ <~1 ثانية مع minReplicas", "مفيش عادةً (pods على nodes دافئة)", "ثوانٍ"],
             ["التوسع بالأحداث (KEDA)", "✗", "✓ **مدمج** (Service Bus/Kafka/HTTP backlog…)", "△ يدوي (تثبّت KEDA)", "✗"],
             ["حد التوسع (توثيق Microsoft)", "30 instances في Premium · 200 في ASE", "**1,000 replica لكل revision** · 15 environment لكل region", "**5,000 nodes** في Standard/Premium", "حسب الكوتا"],
             ["canary / blue-green", "**Slots** + توزيع traffic", "**Revisions** + توزيع traffic", "أي ingress controller / mesh", "✗"],
             ["التحكم في الشبكة", "محدود (VNet integration للتصدير)", "VNet injection + ingress داخلي/خارجي", "**كامل** (CNI/NSG/policies)", "أساسي"],
             ["Service mesh / Dapr", "✗", "**Dapr مدمج** + Envoy مُدار", "Istio/Linkerd يدوي", "✗"],
             ["نموذج الفوترة", "لكل instance-hour في الخطة (حتى مع صفر حمل)", "**vCPU-second + GiB-second** + طلبات، مع منحة مجانية", "VMs للـnodes (دايمًا) + control plane حسب الـtier", "لكل ثانية تشغيل"],
             ["Windows containers", "✓ (Premium)", "✗ (Linux فقط)", "✓", "✓"],
             ["إمتى تختاره", "موقع/API واحد، حمل ثابت، أقل إدارة", "**الافتراضي لمعظم أحمال .NET الحاوية الجديدة**", "لما تحتاج Kubernetes فعلًا", "مهام قصيرة/batch"],
         ]},
        {"type": "callout", "kind": "note", "title": "إرشاد Microsoft نفسه (Azure Architecture Center)",
         "md": "**ابدأ بـContainer Apps** لما عايز مبادئ microservices مدمجة (service discovery · Dapr · توسع لكل تطبيق مع scale-to-zero) من غير إدارة cluster. **اختار AKS** لما تحتاج وصول مباشر لـKubernetes API أو service mesh مخصص أو تحكم دقيق في الـnodes والشبكة. **استخدم Functions** للأحمال الحدثية المتقطعة اللي بتستفيد من الفوترة بالثانية. وApp Service للويب التقليدي/الـlift-and-shift."},

        # ── 2) مسار القرار
        {"type": "heading", "level": 2, "text": "② مسار القرار: 5 أسئلة بالترتيب (مش «أيهم أحسن»)"},
        {"type": "steps", "title": "اسأل بالترتيب — أول «آه» بيحسم",
         "items": [
             {"title": "1) محتاج Kubernetes API نفسه؟",
              "md": "CRDs/operators مخصصة · StatefulSet · DaemonSet · service mesh محدد (Istio) · node pools خاصة (GPU/Spot) · سياسات admission · شبكة CNI معقدة. لو آه → **AKS** (ومفيش بديل بينهم). ووقتها خليك مستعد لتكلفة تشغيل حقيقية: **نصف وقت شخص على الأقل بخبرة Kubernetes** — دي نصيحة عملية مش مبالغة.",
              "code": ""},
             {"title": "2) الحمل «موقع/API واحد» مش سرب خدمات؟",
              "md": "تطبيق واحد، حمل ثابت ومتوقع، وفريق بيحب النشر بالكود (مش بالصور)، ومحتاج slots جاهزة وcustom domain وشهادات مُدارة → **App Service**. ملحوظة مهمة: لو الحمل ثابت ودايمًا فوق الصفر، **App Service غالبًا أرخص** من ACA Consumption (خطة Standard بتُدفع شهريًا مقابل vCPU-seconds مستمرة).",
              "code": ""},
             {"title": "3) النموذج «دالة بتتفعّل بحدث»؟",
              "md": "Webhook · رسالة على طابور · ملف وصل Blob · مؤقت · حدث من Event Grid — وشغل قصير (دقائق) → **Azure Functions** (الدرس الجاي). ولو الشغل ده نفسه جزء من نظام أكبر، ممكن تشغّل Functions **على Container Apps** وتفضل في منصة واحدة.",
              "code": ""},
             {"title": "4) مهمة قصيرة/مرة واحدة؟",
              "md": "Batch · تشغيل migration · CI runner · تجربة سريعة → **ACI** (أو **Container Apps Jobs** لو عايز جدولة وإعادة محاولة مُدارة).",
              "code": ""},
             {"title": "5) غير كده؟",
              "md": "→ **Container Apps**: حاويات، microservices، شغل خلفي على طوابير، توسع بالأحداث، scale-to-zero للتوفير، revisions للـcanary، وDapr لو محتاج. ده **الافتراضي** لمشاريع .NET الحاوية الجديدة في 2026.",
              "code": ""},
         ]},
        {"type": "callout", "kind": "tip", "title": "القاعدة الاقتصادية اللي بتغيّر القرار",
         "md": "**ACA Consumption بتكسب لما الخدمة بتقضي وقت تحت ~40% استخدام في الشهر** (أو بتنزل لصفر بالليل/الويكند). **ولما الحمل مستمر 24/7**، الحساب بينعكس: vCPU-seconds المستمرة بتبقى أغلى من خطة App Service أو من nodes محفوظة بـreservation. يعني: مشروع شخصي بزيارات متقطعة → ACA. خدمة داخلية تحت ضغط دائم → قارن بالأرقام قبل ما تقرر."},

        # ── 3) التنفيذ
        {"type": "heading", "level": 2, "text": "③ التنفيذ: نفس الصورة على المنصات الثلاثة بـAzure CLI"},
        {"type": "code", "lang": "bash", "title": "azure/00-shared.sh", "filename": "azure/00-shared.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

# ═══ متغيرات واحدة لكل المنصات (لازم كل حاجة في نفس الـregion لتقليل latency وegress) ═══
export LOC=westeurope                 # أقرب منطقة لمصر: westeurope أو northeurope
export RG=rg-shop-dev
export ACR=acrshopdev                 # أسماء ACR عالمية: حروف وأرقام فقط
export IMAGE=shop/orders
export TAG=1.4.0                      # أو digest من CI (الدرس 6.1.3)

# ═══ 1) مجموعة موارد + سجل صور ═══
az group create --name "$RG" --location "$LOC" --tags "env=dev" "project=shop" "owner=you"
az acr create --resource-group "$RG" --name "$ACR" --sku Basic --admin-enabled false

# بناء الصورة في السحابة من غير Docker محلي (مفيد لو جهازك ضعيف):
az acr build --registry "$ACR" --image "$IMAGE:$TAG" --platform linux/amd64 ./src/Orders.Api

# ═══ 2) هوية واحدة تُستخدم في المنصات الثلاثة: Managed Identity (الدرس 6.2.3) ═══
# المبدأ: مفيش كلمة سر ولا connection string فيها سر في أي manifest أو إعداد.
# كل منصة بتدي الخدمة هوية، والهوية تاخد صلاحيات بأقل امتياز:
#   ACR  → دور AcrPull (لقراءة الصور)
#   Key Vault → دور "Key Vault Secrets User" (للقراءة فقط)
#   SQL/PostgreSQL → Entra ID authentication (مفيش password خالص)

echo "الخطوة الجاية: اختار منصة من الملفات الثلاثة اللي بعد ده."
'''},
        {"type": "code", "lang": "bash", "title": "azure/10-container-apps.sh — الخيار الافتراضي", "filename": "azure/10-container-apps.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
source ./azure/00-shared.sh

# ═══ 1) بيئة Container Apps (البيئة = الحدود المشتركة للشبكة/السجلات/Dapr) ═══
az containerapp env create \
  --name env-shop-dev --resource-group "$RG" --location "$LOC"

# ═══ 2) هوية للتطبيق + صلاحية سحب الصور من ACR ═══
az containerapp create --name orders --resource-group "$RG" \
  --environment env-shop-dev --image "$ACR.azurecr.io/$IMAGE:$TAG" \
  --registry-server "$ACR.azurecr.io" --registry-identity system \
  --cpu 0.5 --memory 1Gi --min-replicas 1 --max-replicas 10 \
  --ingress external --target-port 8080 --transport auto \
  --scale-rule-name http --scale-rule-type http \
  --scale-rule-metadata concurrent-requests=10 \
  --env-vars "ASPNETCORE_ENVIRONMENT=Production"

# الأسرار تُضبط بأمر مستقل (قيمها من CI/Key Vault — الدرس 6.2.3)، وتُستدعى بـsecretRef:
az containerapp secret set --name orders --resource-group "$RG" \
  --secrets rabbitmq-conn="$RABBITMQ_CONNECTION"

PRINCIPAL=$(az containerapp identity show --name orders --resource-group "$RG" \
  --query principalId --output tsv)
az role assignment create --role AcrPull \
  --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --scope "$(az acr show --name "$ACR" --resource-group "$RG" --query id --output tsv)"

# ═══ 3) فحص: العنوان، النسخ، السجلات، الأحداث ═══
az containerapp show --name orders --resource-group "$RG" \
  --query "properties.configuration.ingress.fqdn" --output tsv
az containerapp replica list --name orders --resource-group "$RG" --output table
az containerapp logs show --name orders --resource-group "$RG" --follow
az containerapp revision list --name orders --resource-group "$RG" --output table

# ═══ 4) canary حقيقي: نسخة جديدة تاخد 10% من الـtraffic ═══
az containerapp revision copy --name orders --resource-group "$RG" \
  --revision orders--rev2 --image "$ACR.azurecr.io/$IMAGE:1.5.0"
az containerapp ingress set --name orders --resource-group "$RG" \
  --traffic-split orders--rev1=90 --traffic-split orders--rev2=10
# لو المؤشرات ساءت → رجّع كل الحركة للنسخة القديمة في أمر واحد:
az containerapp ingress set --name orders --resource-group "$RG" \
  --traffic-split orders--rev1=100

# ═══ 5) توسع بطول طابور RabbitMQ (بديل KEDA ScaledObject في 6.1.5) ═══
# أسماء أنواع القواعد وحقول الـmetadata بتتغير بين الإصدارات:
#   az containerapp scale-rule-type show  / أو التوثيق — تحقق قبل ما تعتمد عليها.
az containerapp update --name orders --resource-group "$RG" \
  --scale-rule-name queue --scale-rule-type rabbitmq \
  --scale-rule-metadata queueName=orders-queue queueLength=50 \
  --scale-rule-auth connectionString-secret-ref=rabbitmq-conn

# ═══ 6) التصريح الكامل كتعريف (أفضل من الأوامر: يُراجع ويُخزّن في Git) ═══
#   az containerapp create --name orders --resource-group $RG --yaml containerapp.yaml
#   az containerapp update --name orders --resource-group $RG --yaml containerapp.yaml
'''},
        {"type": "code", "lang": "yaml", "title": "azure/containerapp.yaml — ACA تصريحيًا (قابل للمراجعة في PR)", "filename": "azure/containerapp.yaml", "code": r'''# az containerapp create --name orders --resource-group rg-shop-dev --yaml azure/containerapp.yaml
properties:
  managedEnvironmentId: /subscriptions/<SUB_ID>/resourceGroups/rg-shop-dev/providers/Microsoft.App/managedEnvironments/env-shop-dev
  configuration:
    activeRevisionsMode: Multiple      # Single = كل الحركة لآخر revision (الأبسط)
    ingress:
      external: true
      targetPort: 8080                 # نفس ASPNETCORE_HTTP_PORTS في الصورة
      transport: auto
      allowInsecure: false
      corsPolicy:
        allowedOrigins: ["https://shop.example.com"]
    secrets:                           # القيم تُحقن من CI؛ لا تُكتب في Git
      - name: rabbitmq-conn
        value: ""
    registries:
      - server: acrshopdev.azurecr.io
        identity: system               # سحب الصور بالهوية المُدارة (مفيش admin password)
  template:
    revisionSuffix: rev1
    scale:
      maxReplicas: 10
      minReplicas: 1                   # 0 = scale-to-zero (وفّر، واستحمل cold start)
      rules:
        - name: http
          custom:
            type: http
            metadata:
              concurrentRequests: "10"  # توسع بعدد الطلبات المتزامنة — أدق من CPU لـI/O
    containers:
      - image: acrshopdev.azurecr.io/shop/orders@sha256:<DIGEST>   # digest ثابت (6.1.3)
        name: orders
        resources:
          cpu: 0.5
          memory: 1Gi
        env:
          - name: ASPNETCORE_ENVIRONMENT
            value: Production
          - name: ConnectionStrings__RabbitMq
            secretRef: rabbitmq-conn
        probes:                         # نفس منطق الـ3 probes من 6.1.5
          - type: startup
            tcpSocket: { port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12
          - type: readiness
            httpGet: { path: /health, port: 8080 }
            periodSeconds: 10
            failureThreshold: 3
          - type: liveness
            httpGet: { path: /alive, port: 8080 }
            periodSeconds: 20
            failureThreshold: 3
'''},
        {"type": "code", "lang": "bash", "title": "azure/20-app-service.sh + azure/30-aks.sh", "filename": "azure/20-app-service.sh", "code": r'''#!/usr/bin/env bash
# ─────────────── App Service (Linux) ───────────────
set -euo pipefail
source ./azure/00-shared.sh

az appservice plan create --name asp-shop --resource-group "$RG" \
  --is-linux --sku P1v3                 # P1v3: خطة إنتاجية بـslots وتوسع تلقائي
# سلسلة الـruntime بتتغير بين الإصدارات — اقرأ القائمة بدل ما تخمّن:
az webapp list-runtimes --linux | grep -i dotnet

az webapp create --name shop-orders --resource-group "$RG" --plan asp-shop \
  --deployment-container-image-name "$ACR.azurecr.io/$IMAGE:$TAG"

# هوية + سحب الصور + إعدادات
az webapp identity assign --name shop-orders --resource-group "$RG"
az role assignment create --role AcrPull \
  --assignee-object-id "$(az webapp identity show --name shop-orders --resource-group "$RG" --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal \
  --scope "$(az acr show --name "$ACR" --resource-group "$RG" --query id -o tsv)"
az webapp config appsettings set --name shop-orders --resource-group "$RG" \
  --settings ASPNETCORE_ENVIRONMENT=Production WEBSITES_PORT=8080
# سر من Key Vault من غير ما تشوف قيمته (الدرس 6.2.3):
az webapp config appsettings set --name shop-orders --resource-group "$RG" \
  --settings 'ConnectionStrings__Default=@Microsoft.KeyVault(SecretUri=https://kv-shop-dev.vault.azure.net/secrets/orders-db/)'

# النشر الآمن: slot → اختبار → swap (توزيع traffic اختياري للـcanary)
az webapp deployment slot create --name shop-orders --resource-group "$RG" --slot staging
az webapp deploy --name shop-orders --resource-group "$RG" --slot staging --type zip --src-path publish.zip
az webapp deployment slot swap --name shop-orders --resource-group "$RG" \
  --slot staging --target-slot production

# ─────────────── AKS (لو مسارك رقم 1 في القرار) ───────────────
az aks create --resource-group "$RG" --name aks-shop \
  --node-count 3 --node-vm-size Standard_D2s_v5 \
  --enable-managed-identity --network-plugin azure \
  --tier standard \
  --enable-addons monitoring \
  --attach-acr "$ACR"                   # يمنح kubelet identity دور AcrPull تلقائيًا
# ملاحظة: --tier standard = control plane مدفوع بالساعة؛ قارنه بـ--tier free قبل ما تختار

az aks get-credentials --resource-group "$RG" --name aks-shop
# ومن هنا: كل ما تعلمته في 6.1.4 و6.1.5 يشتغل كما هو (kustomize/HPA/PDB/Ingress):
kubectl apply -k k8s/overlays/dev
kubectl -n shop rollout status deploy/orders
'''},

        # ── 4) ما الذي تتخلى عنه
        {"type": "heading", "level": 2, "text": "④ إيه اللي بتاخده وإيه اللي بتسيبه في كل اختيار"},
        {"type": "table", "caption": "المقايضات الصريحة — اقرأ عمود «بتسيب» قبل ما توقع",
         "head": ["المنصة", "بتاخد", "بتسيب / بتخاطر بـ", "إشارة إنك لازم تنقل"],
         "rows": [
             ["App Service", "أقل إدارة · slots · شهادات وdomains مُدارة · مراقبة جاهزة · أسعار متوقعة",
              "مفيش scale-to-zero · مفيش توسع بالأحداث · تحكم شبكة محدود · Windows/Linux حسب الخطة · تكلفة ثابتة حتى مع صفر حمل",
              "الحمل بقى متقطع جدًا (بتدفع مقابل سكون) أو محتاج توسع بطول طابور"],
             ["Container Apps", "حاويات + scale-to-zero + KEDA + revisions/canary + Dapr + ingress وشهادات مُدارة · فوترة بالثانية",
              "**مفيش Kubernetes API**: لا kubectl ولا CRDs ولا operators · تحكم أقل في الشبكة والجدولة · Linux فقط · cold start من الصفر · حدود (1000 replica/revision)",
              "محتاج operator مخصص/StatefulSet/mesh محدد/GPU أو تحكم كامل في الشبكة"],
             ["AKS", "كل Kubernetes: تحكم كامل · CRDs · mesh · node pools خاصة · قابلية نقل لأي سحابة · 5,000 nodes",
              "**إدارة حقيقية**: ترقيات nodes، networking، ingress controller، مراقبة cluster، أمان، وتكلفة nodes دايمًا شغالة + control plane",
              "— (انت بالفعل في أقصى تحكم)"],
             ["ACI / ACA Jobs", "تشغيل فوري لحاوية واحدة · فوترة بالثانية · مثالي لمهام قصيرة",
              "لا ingress ولا service discovery ولا scaling تلقائي · إعادة المحاولة والجدولة محدودة",
              "المهمة بقت خدمة مستمرة أو محتاجة توسع"],
         ]},
        {"type": "callout", "kind": "warn", "title": "ثلاثة قرارات بتبقى غالية لو اتأخرت",
         "md": "**① المنطقة (Region)**: كل مواردك لازم في منطقة واحدة قريبة من مستخدميك (westeurope/northeurope لمصر) — نقل خدمة بين المناطق لاحقًا يعني downtime وegress وتغيير عناوين. **② اسم ACR عالمي ولا بيتغيّر**: اختار اسم من الأول. **③ الـtags والـresource groups**: قسّم حسب بيئة (rg-shop-dev / -stg / -prod) ووسم بـ`env` و`project` و`owner` — ده اللي هيعملك «مين بيدفع كام» في درس 6.2.5. لو عملت ده من أول يوم، الفاتورة هتبقى مقروءة."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أقدر أحسم بين App Service وACA وAKS بخمسة أسئلة مرتبة (K8s API؟ خدمة واحدة؟ حدثية؟ مهمة قصيرة؟ غير كده ACA).",
            "عارف إن ACA مبنية على Kubernetes لكنها **ما بتديكش الـAPI** — وده مقصود (إدارة أقل) مش نقص.",
            "أعرف أعمل environment وcontainer app من صورة في ACR بهوية مُدارة (بلا admin password).",
            "أقدر أعمل canary بـrevisions (تقسيم traffic) أو بـslots (App Service) وأرجع في ثانية.",
            "فاهم إن **scale-to-zero توفير مش مجاني**: الثمن cold start، والحل `minReplicas` للحساسين للـlatency.",
            "عارف حدود التوسع المعلنة: 30 instances (App Service Premium) · 1,000 replicas/revision (ACA) · 5,000 nodes (AKS).",
            "أقدر أكتب ADR من 5 سطور يبرر الاختيار لزميل أو لمقابل عمل.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على القرار والمقايضات.",
         "questions": [
             {"q": "خدمة .NET في حاوية، حملها متقطع جدًا (ذروة نهارًا وصفر بالليل)، ومحتاجتها تتوسع بعدد رسائل طابور Service Bus. الأفضل؟",
              "options": ["App Service P1v3", "Container Apps (Consumption) مع scale rule على الطابور", "AKS بـ3 nodes", "ACI"],
              "answer": 1,
              "explain": "ACA بتوفر scale-to-zero (صفر تكلفة بالليل) وقواعد توسع KEDA مدمجة على Service Bus. App Service مفيهاش scale-to-zero ولا KEDA؛ AKS هيخليك تدفع مقابل nodes دايمًا شغالة + إدارة cluster؛ ACI ملهاش توسع تلقائي."},
             {"q": "ليه ACA مش «Kubernetes كامل»؟",
              "options": ["لأنها بتشتغل على VMs مش containers", "لأن Microsoft بتدير الـKubernetes داخليًا وما بتظهرش الـAPI: مفيش kubectl ولا CRDs ولا operators", "لأنها بتدعم Linux بس", "لأنها محدودة بـ1,000 replica"],
              "answer": 1,
              "explain": "ACA مبنية على Kubernetes فعلًا، لكن الـcontrol plane مخفي: انت بتعرّف revisions/scale/ingress، ومش بتقدر تستخدم الموارد الأصلية. ده مقايضة مقصودة: إدارة أقل مقابل تحكم أقل. لو محتاج الـAPI → AKS."},
             {"q": "حمل **مستمر 24/7** على خدمة واحدة. أي اختيار غالبًا أرخص؟",
              "options": ["ACA Consumption دايمًا", "App Service خطة مناسبة أو ACA Dedicated/AKS مع reservation — لأن vCPU-seconds المستمرة بتتجمع", "ACI", "Functions Consumption"],
              "answer": 1,
              "explain": "الفوترة بالثانية بتكسب لما فيه سكون. مع حمل مستمر، الحساب بينعكس: خطة ثابتة (App Service) أو nodes محفوظة بـreservation غالبًا أرخص. القاعدة العملية: متوسط استخدام فوق ~40% من الشهر → قارن الالتزامات."},
             {"q": "إزاي تعمل canary (10% من الحركة للنسخة الجديدة) على ACA؟",
              "options": ["`kubectl set image`", "revision جديدة + `ingress set --traffic-split` بنسب، والرجوع بتحويل 100% للـrevision القديمة", "إنشاء App Service slot", "تغيير الـDNS يدويًا"],
              "answer": 1,
              "explain": "الـrevisions غير قابلة للتغيير وبتتعايش، وتوزيع الـtraffic بينها مدمج في الـingress. (في App Service المقابل هو slots، وفي AKS هو ingress controller/mesh.)"},
             {"q": "عندك manifests kustomize + HPA + PDB + Ingress جاهزة من 6.1.4/6.1.5. أي منصة بتشغّلها **كما هي**؟",
              "options": ["App Service", "Container Apps", "AKS", "ACI"],
              "answer": 2,
              "explain": "AKS هي اللي بتديك Kubernetes API، فملفاتك تشتغل بدون تغيير. ACA ليها نموذجها الخاص (`containerapp.yaml`) ولو فيه تشابه مفاهيمي كبير (probes/scale/ingress). App Service وACI ملهمش علاقة بالـmanifests."},
             {"q": "أيه القرار اللي بيبقى غالي لو اتأخر؟",
              "options": ["اسم الـcontainer", "المنطقة (region) وتقسيم الـresource groups والـtags", "عدد الـprobes", "نوع الـshell في الصورة"],
              "answer": 1,
              "explain": "نقل موارد بين المناطق = downtime وegress وتغيير عناوين وDNS. تقسيم الـresource groups حسب البيئة والـtags (env/project/owner) هو اللي بيمكّنك من تحليل التكلفة والصلاحيات لاحقًا (6.2.5) — رخيص دلوقتي وصعب بعدين."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "الاختبار الحقيقي للقرار: تنفّذه وتقيسه بالفلوس.",
         "items": [
             {"id": "t1", "title": "مهمة 1: قرار مكتوب (ADR) + تقدير تكلفة بثلاثة سيناريوهات",
              "md": "**السياق:** فريقك عايز ينقل `Orders.Api` (صورة Docker جاهزة) على Azure. الحمل المتوقع: 3 أوقات ذروة يوميًا، صفر تقريبًا بالليل، وطابور RabbitMQ بيوصل لـ5,000 رسالة في الذروة.\n\n**المطلوب:** اكتب `docs/adr/0014-azure-compute.md` فيه: القرار · السياق · **جدول مقارنة بثلاثة خيارات** (ACA / App Service / AKS) بالأرقام · البدائل المرفوضة وسبب الرفض · العواقب (إيجابية وسلبية) · وإشارة الرجوع.\n\n**أضف `docs/azure-cost-estimate.md`** فيه تقدير شهري لثلاثة سيناريوهات (خفيف 2 vCPU·ساعة/يوم · متوسط 10 · مستمر 48) على المنصات الثلاثة، باستخدام [حاسبة التسعير](https://azure.microsoft.com/pricing/calculator/) مع **لقطة شاشة أو أرقام مكتوبة وتاريخ** — وقارن بالنتيجة: عند أي سيناريو بينعكس الترتيب؟",
              "criteria": [
                  "ADR بصيغة «القرار / السياق / البدائل / العواقب» ومختوم بتاريخ وموقع عليه كقرار (مش تقرير).",
                  "جدول مقارنة فيه على الأقل: scale-to-zero · التوسع بالأحداث · العبء التشغيلي · نموذج الفوترة · حد التوسع · canary.",
                  "استنتاج صريح: ACA للاختيار الحالي، **وسبب** مرتبط بالحمل المتقطع والطابور (مش تفضيل شخصي).",
                  "تقدير التكلفة بثلاثة سيناريوهات من الحاسبة الرسمية، مع ذكر **منحة ACA المجانية** (vCPU-seconds/GiB-seconds/طلبات) وأثرها على السيناريو الخفيف.",
                  "إجابة صريحة على «عند أي حمل بينعكس الترتيب؟» برقم تقريبي (مثال: فوق ~40% استخدام شهري).",
                  "فقرة «إشارة الرجوع»: متى ننقل لـAKS (حاجة لـCRD/operator/GPU/mesh) ومين هيكلف ده إيه.",
              ],
              "hint": "افتح الحاسبة واختار «Container Apps» وجرّب: 0.5 vCPU / 1 GiB / متوسط 6 ساعات نشاط يوميًا / 300,000 طلب — وقارنها بـApp Service P1v3 (instance واحدة 24×7). الفرق هيكون كبير في السيناريو الخفيف ويقل في المستمر. وثّق الأرقام بتاريخ لأن الأسعار بتتغير.",
              "solution": "قرار نموذجي: **ACA Consumption** مع `minReplicas: 1` للـAPI (تجنب cold start في الذروة) و`minReplicas: 0` للخدمات الخلفية المستهلكة للطابور، وscale rule على طول الطابور. الأسباب: (1) الحمل متقطع → scale-to-zero يوفر (2) التوسع بالطابور مدمج (KEDA) (3) العبء التشغيلي منخفض لفريق صغير (4) revisions تديني canary وrollback. التقدير: السيناريو الخفيف غالبًا **داخل المنحة المجانية أو بضعة دولارات**، والمتوسط بعشرات الدولارات، والمستمر 24/7 بيقارب أو يزيد عن App Service P1v3 — وعند النقطة دي بنعيد التقييم نحو Dedicated plan + reservation. العواقب السلبية المقرونة بالقرار: مفيش Kubernetes API (يعني مهارات kubectl من 6.1.4 مش هتُستخدم مباشرة)، cold start عند minReplicas=0، وحد 1,000 replica لكل revision.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/compute-decision-tree",
                  "https://learn.microsoft.com/en-us/azure/container-apps/compare-options",
                  "https://learn.microsoft.com/en-us/azure/architecture/microservices/design/compute-options",
                  "https://azure.microsoft.com/en-us/pricing/calculator/",
              ]},
             {"id": "t2", "title": "مهمة 2: انشر الصورة فعليًا على Container Apps وقِس",
              "md": "**السياق:** القرار مش نظري — لازم تشوفه شغال وتقيس سلوكه.\n\n**المطلوب:**\n1. `az containerapp env create` ثم انشر `shop/orders` من ACR بـ**هوية مُدارة** (بلا `--admin-enabled true`).\n2. اضبط `minReplicas: 0` و`maxReplicas: 5` وقاعدة توسع HTTP بـ`concurrentRequests: 10`.\n3. قِس **cold start**: اترك التطبيق ساكنًا 10 دقائق، ثم اطلب أول طلب وسجّل الزمن، ثم اطلب 20 طلبًا متتالية وسجّل p50/p95. كرّر بـ`minReplicas: 1` وقارن.\n4. اضرب حملًا بـk6 (`--vus 50 --duration 2m`) وراقب `az containerapp replica list` كل 10 ثوانٍ — وثّق كم نسخة وصلت ومتى نزلت.\n5. اعمل **revision جديدة** بـtag مختلف، قسّم الحركة 90/10، ثم ارجع لـ100% للقديمة — وسجّل الأوامر والوقت المستغرق للرجوع.\n6. اكتب `docs/aca-notes.md` بالأرقام + لقطة من السجلات + استنتاج: هل الاختيار كان صحيحًا لهذا الحمل؟",
              "criteria": [
                  "النشر تم بهوية مُدارة + دور `AcrPull` (مش admin password) — والأمر موثق.",
                  "قياس cold start برقمين: أول طلب بعد السكون، وp95 بعد الإحماء — **مع `minReplicas: 0` مقابل `1`**.",
                  "ملاحظة عدد النسخ تحت حمل k6 ومتى تصاعدت ومتى نزلت (مع زمن نافذة النزول).",
                  "تعديل revision وتقسيم traffic 90/10 ثم الرجوع — **وزمن الرجوع** مكتوب بالثواني.",
                  "`docs/aca-notes.md` فيه جدول أرقام واستنتاج صريح مرتبط بالحمل (مش «كله تمام»).",
                  "تنظيف: `az group delete` أو إيقاف الموارد بعد التجربة (مع ملاحظة إن ACA Consumption بتنزل لصفر تلقائيًا).",
              ],
              "hint": "لقياس cold start استخدم `curl -w '%{time_total}\\n' -o /dev/null -s https://<fqdn>/alive` — أول رقم بعد السكون هو الإقلاع البارد. لو الرقم كبير (ثوانٍ) فده ثمن scale-to-zero، والحل `minReplicas: 1` أو `startup probe` أسرع. وللرجوع السريع احتفظ بالأمر في ملف `scripts/rollback.sh` قبل ما تبدأ التجربة.",
              "solution": "الأرقام النموذجية اللي هتشوفها: أول طلب بعد 10 دقائق سكون = **2–8 ثوانٍ** (سحب الصورة + إقلاع .NET)، وبعدها p95 يرجع لعشرات المللي ثانية. مع `minReplicas: 1` مفيش cold start لكن فيه تكلفة مستمرة صغيرة. تحت k6 بـ50 VU ومع `concurrentRequests: 10` هتوصل لـ5 نسخ خلال دقيقة تقريبًا، والنزول بيستغرق دقائق (نافذة استقرار). الـrollback بـ`ingress set --traffic-split rev1=100` بيتم في **ثوانٍ** لأن النسخة القديمة لسه موجودة وجاهزة — دي أكبر ميزة عملية لـrevisions مقابل «نشر جديد وانتظار». الاستنتاج الصحيح: للحمل المتقطع الاختيار موفر ومريح؛ لو الخدمة بقت حساسة للـlatency على أول طلب، ارفع `minReplicas` وادفع الفرق.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/container-apps/quickstart-cli",
                  "https://learn.microsoft.com/en-us/azure/container-apps/revisions",
                  "https://learn.microsoft.com/en-us/azure/container-apps/scale-app",
                  "https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview",
                  "https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Choose an Azure compute service (قرار رسمي من Microsoft)", "url": "https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/compute-decision-tree"},
            {"label": "Container Apps مقابل خيارات الحاويات الأخرى", "url": "https://learn.microsoft.com/en-us/azure/container-apps/compare-options"},
            {"label": "اختيار الحوسبة للـmicroservices (مقارنة قدرات)", "url": "https://learn.microsoft.com/en-us/azure/architecture/microservices/design/compute-options"},
            {"label": "Container Apps: revisions وتوزيع الحركة", "url": "https://learn.microsoft.com/en-us/azure/container-apps/revisions"},
            {"label": "Container Apps: قواعد التوسع", "url": "https://learn.microsoft.com/en-us/azure/container-apps/scale-app"},
            {"label": "App Service: deployment slots", "url": "https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots"},
            {"label": "AKS: مفاهيم ومقارنة الـtiers", "url": "https://learn.microsoft.com/en-us/azure/aks/intro-kubernetes"},
            {"label": "حاسبة تسعير Azure", "url": "https://azure.microsoft.com/en-us/pricing/calculator/"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s6-m2-l2 — Azure Functions والحوسبة بلا خوادم
# ══════════════════════════════════════════════════════════════════════════
_L2 = {
    "id": "s6-m2-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "مش كل شغل يستاهل خدمة شغالة 24 ساعة. webhook، رسالة على طابور، ملف وصل storage، مهمة مجدولة، أو **سير عمل طويل** فيه انتظار وموافقات — دول نموذج Azure Functions. في الدرس ده: **نموذج isolated worker** (الوحيد المدعوم لـ.NET 10)، الخطط الأربعة وأرقامها، و**Durable Functions** لسير العمل اللي «بينام أسبوع ويكمل» من غير ما تفقد الحالة — مع القواعد الحتمية اللي بتكسر الـorchestrator لو خالفتها."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Trigger", "def": "الحدث اللي بيشغّل الدالة: HTTP · Timer · Service Bus · Event Grid · Blob · Queue · Cosmos DB. دالة واحدة = trigger واحد."},
            {"term": "Binding", "def": "اختصار للإدخال/الإخراج: بدل ما تكتب كود قراءة/إرسال، تصرّح `BlobInput`/`ServiceBusOutput` والمنصة بتنفذ."},
            {"term": "Isolated worker model", "def": "كودك في **عملية .NET مستقلة** بتتكلم مع الـhost عبر gRPC: `Program.cs` + DI كامل + middleware + أي إصدار .NET حديث. **النموذج in-process انتهى دعمه 2026-11-10**."},
            {"term": "Consumption / Flex Consumption / Premium", "def": "خطط الاستضافة: Consumption (الأرخص، timeout قصير، بلا VNet، **.NET 10 غير مدعوم على Linux Consumption**) · Flex Consumption (أسرع إقلاعًا، timeout أطول، VNet، مخصص لكل دالة) · Premium (دافئ دايمًا، بلا cold start)."},
            {"term": "Cold start", "def": "زمن تجهيز أول instance بعد السكون. بيتحسّن بـPremium/Flex (instances مُسخّنة) وبـNative AOT في isolated worker."},
            {"term": "Durable Functions", "def": "امتداد بيديك **سير عمل بحالة**: orchestrator يحدد الخطوات، activities تنفذ الشغل، والمنصة بتخزن الحالة وبتكمل بعد فشل/إعادة تشغيل/انتظار أيام."},
            {"term": "Orchestrator determinism", "def": "الـorchestrator **بيتعاد تشغيله (replay)** من الأول عند كل خطوة، فلازم يدي نفس القرارات: ممنوع `DateTime.UtcNow` / `Guid.NewGuid()` / I/O مباشر / `Task.Delay` — استخدم بدائل الـcontext."},
            {"term": "Checkpoint / History", "def": "سجل خطوات الـorchestration المخزّن؛ منه بيتم الـreplay ومنه بتعرف وصلت فين. حجمه بيكبر مع عدد الخطوات → نمط Fan-out/Fan-in والإصدارات."},
            {"term": "`FUNCTIONS_WORKER_RUNTIME`", "def": "إعداد التطبيق اللي بيقول للـhost أي worker يشغّل: **`dotnet-isolated`**. لو غلط أو متعارض مع الكود المنشور، التطبيق يدخل في حالة خطأ و500 لكل الدوال."},
            {"term": "DLQ / إعادة المحاولة", "def": "الرسالة اللي فشل استهلاكها بعد كل المحاولات بتروح **Dead-Letter Queue** — لازم يكون فيه خطة لمعالجتها مش تجاهلها."},
        ]},

        # ── 1) القرار الكبير
        {"type": "heading", "level": 2, "text": "① قرار 2026 الإجباري: isolated worker + الخطة الصح"},
        {"type": "callout", "kind": "danger", "title": "معلومتان لازم تحفظهم",
         "md": "**① نموذج in-process انتهى دعمه في 10 نوفمبر 2026** (نفس يوم نهاية دعم .NET 8 و9) — أي مشروع جديد لازم **isolated worker** (`FUNCTIONS_WORKER_RUNTIME=dotnet-isolated`)، وهو الوحيد اللي بيدعم .NET 9/10/11. **② .NET 10 ما بيشتغلش على Linux Consumption** — لو عايز Linux و.NET 10 فالخطة هي **Flex Consumption** (أو Premium/Dedicated). التحقق قبل ما تبني: اقرأ صفحة دعم الإصدارات، لأن التفاصيل دي بتتغير."},
        {"type": "table", "caption": "خطط Azure Functions (2026) — الأرقام تقريبية ومن توثيق Microsoft؛ تحقق لخطتك ومنطقتك",
         "head": ["", "Consumption", "Flex Consumption", "Premium", "Dedicated (App Service Plan)"],
         "rows": [
             ["النسخ", "0 → ~200", "0 → ~1000", "1 → ~100 (دافئ)", "حسب الخطة"],
             ["Timeout", "~5 د افتراضيًا / 10 كحد أقصى", "~30 د", "~60 د (وقد تكون غير محدودة)", "غير محدود"],
             ["VNet", "✗", "✓", "✓", "✓"],
             ["Cold start", "الأسوأ (ثوانٍ)", "أقل (instances مُسخّنة)", "شبه معدوم", "مفيش"],
             [".NET 10 على Linux", "**✗**", "✓", "✓", "✓"],
             ["التوسع", "لكل function app", "**لكل دالة** (أدق)", "لكل app", "يدوي/تلقائي حسب الخطة"],
             ["الفوترة", "لكل تنفيذ + GB-s (مع منحة مجانية)", "لكل تنفيذ + GB-s", "لكل instance (دايمًا)", "لكل instance في الخطة"],
             ["الأنسب", "حمل خفيف/متقطع، Windows", "**الإنتاج بلا خوادم لـ.NET 10**", "latency حساس + VNet", "أحمال طويلة/مستمرة أو مشاركة خطة"],
         ]},

        # ── 2) المشروع
        {"type": "heading", "level": 2, "text": "② المشروع: csproj + Program.cs + ثلاث دوال"},
        {"type": "code", "lang": "xml", "title": "src/Shop.Notifications/Shop.Notifications.csproj", "filename": "src/Shop.Notifications/Shop.Notifications.csproj", "code": r'''<Project Sdk="Azure.Functions.Sdk/1.0.0">
  <!-- ⚠ SDK جديد (مش Microsoft.NET.Sdk.Functions القديم): بيولّد metadata الدوال وقت البناء -->

  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <OutputType>Exe</OutputType>                     <!-- isolated worker = تطبيق قابل للتنفيذ -->
    <AzureFunctionsVersion>v4</AzureFunctionsVersion>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <!-- Native AOT مدعوم في isolated worker وبيقلل cold start جذريًا —
         بس جرّبه: بعض الحزم بتعتمد على reflection/emit. -->
    <!-- <PublishAot>true</PublishAot> -->
  </PropertyGroup>

  <ItemGroup>
    <!-- تحسينات الإقلاع الموصى بها: Framework reference لـASP.NET Core -->
    <FrameworkReference Include="Microsoft.AspNetCore.App" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Azure.Functions.Worker" Version="2.50.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.Http" Version="3.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore" Version="2.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.ServiceBus" Version="5.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.Timer" Version="4.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.Extensions.DurableTask" Version="1.*" />
    <PackageReference Include="Microsoft.Azure.Functions.Worker.OpenTelemetry" Version="1.*" />
    <!-- الإصدارات بتتحرك بسرعة: خد آخر مستقر من NuGet ولا تُثبّت أرقامًا من الذاكرة -->
  </ItemGroup>
</Project>
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — نفس Generic Host اللي تعرفه", "filename": "src/Shop.Notifications/Program.cs", "code": r'''using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Shop.Notifications.Services;

var builder = FunctionsApplication.CreateBuilder(args);

// ConfigureFunctionsWebApplication = تكامل ASP.NET Core:
// تستخدم HttpRequest/HttpResponse وMinimal API وmiddleware العادية.
// (بدونها: HttpRequestData/HttpResponseData — نموذج أقدم وأقل راحة.)
builder.ConfigureFunctionsWebApplication();

builder.Services.AddApplicationInsightsTelemetryWorkerService();
builder.Services.ConfigureFunctionsApplicationInsights();

// كل ما بنيته في المراحل السابقة يُعاد استخدامه هنا حرفيًا:
builder.Services.Configure<OrderOptions>(builder.Configuration.GetSection("Orders"))
       .ValidateDataAnnotations()
       .ValidateOnStart();
builder.Services.AddSingleton<EmailSender>();
builder.Services.AddHttpClient("payments", c => c.Timeout = TimeSpan.FromSeconds(8));
// للتتبع الموزّع (5.3.2): أضف AddOpenTelemetry() مع OTLP exporter كما في بقية خدماتك،
// وتحقق من اسم حزمة تكامل Functions مع OpenTelemetry في إصدارك قبل الاعتماد عليها.

var host = builder.Build();
host.Run();
'''},
        {"type": "code", "lang": "csharp", "title": "Functions.cs — HTTP + Service Bus + Timer", "filename": "src/Shop.Notifications/Functions.cs", "code": r'''using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace Shop.Notifications;

public class Functions(ILogger<Functions> log, EmailSender email)
{
    // ── HTTP: Minimal API عادي (بفضل ConfigureFunctionsWebApplication) ──
    [Function("Ping")]
    public IActionResult Ping([HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "ping")]
        HttpRequest req) => Results.Ok(new { ok = true, at = DateTimeOffset.UtcNow });

    [Function("Webhook")]
    public async Task<IActionResult> Webhook(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "webhooks/payments")]
        HttpRequest req, CancellationToken ct)
    {
        // ⚠ أي webhook لازم يتعامل مع «نفس الرسالة مرتين» (الدرس 5.2.4):
        var payload = await JsonSerializer.DeserializeAsync<PaymentEvent>(req.Body, cancellationToken: ct);
        if (payload is null) return Results.BadRequest();

        // Idempotency: جدول/مفتاح مخصص — مش افتراض إن الرسالة جديدة.
        if (!await email.MarkSeenAsync(payload.EventId, ct))
        {
            log.LogInformation("Duplicate webhook {EventId} ignored", payload.EventId);
            return Results.Ok(new { ignored = true });
        }

        await email.SendReceiptAsync(payload, ct);
        return Results.Accepted();
    }

    // ── Service Bus: trigger + إخراج بـbinding ──
    [Function("OnOrderPlaced")]
    [ServiceBusOutput("orders-audit", Connection = "ServiceBus")]   // قيمة الإرجاع = رسالة
    public async Task<string> OnOrderPlaced(
        [ServiceBusTrigger("orders-placed", Connection = "ServiceBus")] string body,
        FunctionContext ctx)
    {
        var log = ctx.GetLogger<Functions>();
        var e = JsonSerializer.Deserialize<OrderPlaced>(body)!;
        await email.SendOrderConfirmationAsync(e, CancellationToken.None);
        return JsonSerializer.Serialize(new { e.OrderId, auditedAt = DateTimeOffset.UtcNow });
        // ⚠ لو رميت exception، المنصة تعيد المحاولة ثم ترمي الرسالة للـDLQ.
        //   ففكر: أي أخطاء تستاهل إعادة محاولة وأيها لازم تُسجَّل وتُبتلع؟
    }

    // ── Timer: CRON بالتوقيت العالمي (مش توقيت جهازك) ──
    [Function("NightlyReport")]
    public async Task NightlyReport(
        [TimerTrigger("0 30 2 * * *", RunOnStartup = false)] TimerInfo info)
    {
        log.LogInformation("Nightly report at {When}", info.ScheduleStatus?.Next);
        await email.BuildDailyReportAsync(CancellationToken.None);
        // RunOnStartup=false مهم: وإلا اشتغلت الدالة عند كل نشر/إعادة تشغيل.
    }
}

public record PaymentEvent(string EventId, string OrderId, decimal Amount, string Currency);
public record OrderPlaced(string OrderId, string Email, decimal Total);
'''},

        # ── 3) Durable
        {"type": "heading", "level": 2, "text": "③ Durable Functions: سير عمل بينام أسبوع ويكمل"},
        {"type": "text", "md": "تخيل «طلب فيه موافقة»: احجز المخزون → لو المبلغ > 5,000 جنيه استنى موافقة مدير (**قد تستغرق أيامًا**) → اخصم الدفع → أرسل الشحن → لو فشل أي شيء اعمل تعويض. بالكود العادي ده يعني طوابير وجداول حالة ومؤقتات ومراقبة. بـDurable Functions ده **orchestrator واحد مقروء**، والمنصة بتخزن الحالة وبتكمل بعد فشل أو إعادة تشغيل."},
        {"type": "code", "lang": "csharp", "title": "OrderApprovalOrchestration.cs — النمط الكامل", "filename": "src/Shop.Notifications/OrderApprovalOrchestration.cs", "code": r'''using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.DurableTask;          // ⚠ مساحة أسماء isolated worker (مش WebJobs)
using Microsoft.Extensions.Logging;

namespace Shop.Notifications.Orchestrations;

public record OrderRequest(string OrderId, string CustomerEmail, decimal Total);
public record ApprovalDecision(bool Approved, string By);

public class OrderApprovalOrchestration
{
    // ── نقطة البداية: HTTP يُشغّل الـorchestration ويرجع فورًا بمعرف النسخة ──
    [Function("StartApproval")]
    public async Task<HttpResponseData> StartApproval(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "orders/approvals")]
        HttpRequestData req,
        [DurableTaskTrigger] DurableTaskClient client,
        CancellationToken ct)
    {
        var input = await req.ReadFromJsonAsync<OrderRequest>()
                    ?? throw new InvalidOperationException("body required");

        // InstanceId ثابت مشتق من معرف الطلب = حماية من تشغيل مزدوج (idempotency):
        var instanceId = $"approval-{input.OrderId}";

        // Idempotency: نفحص أولًا، ولو المنصة رفضت تكرار المعرف نلتقط ونرجع 409
        // (نافذة سباق صغيرة بين الفحص والبدء — عالجها بالتقاط الاستثناء لا بالافتراض).
        var existing = await client.GetInstancesAsync(instanceId, getInputsAndOutputs: false, ct);
        if (existing is not null)
            return req.CreateResponse(System.Net.HttpStatusCode.Conflict);

        await client.ScheduleNewOrchestrationInstanceAsync(
            "OrderApproval", input, new StartOrchestrationOptions { InstanceId = instanceId });

        var resp = req.CreateResponse(System.Net.HttpStatusCode.Accepted);
        await resp.WriteAsJsonAsync(new { instanceId, statusQuery = $"/runtime/webhooks/durableTask/instances/{instanceId}" });
        return resp;
    }

    // ── الـOrchestrator: حتمي 100% (القواعد في الجدول الجاي) ──
    [Function("OrderApproval")]
    public static async Task<string> OrderApproval(TaskOrchestrationContext ctx, OrderRequest req)
    {
        ILogger log = ctx.CreateReplaySafeLogger(nameof(OrderApproval));   // ✓ logger آمن للـreplay
        log.LogInformation("Approval started for {OrderId}", req.OrderId);

        // 1) احجز المخزون
        var reservation = await ctx.CallActivityAsync<string>("ReserveStock", req.OrderId);

        try
        {
            // 2) موافقة لو المبلغ كبير — مع انتظار خارجي (قد يستغرق أيامًا)
            if (req.Total > 5000m)
            {
                // انتظار حدث خارجي بمهلة = نمط «الموافقة البشرية»:
                var decision = await ctx.WaitForExternalEvent<ApprovalDecision>(
                    "ManagerApproval", TimeSpan.FromDays(3));

                if (!decision.Approved)
                    return await CompensateAsync(ctx, req.OrderId, reservation, "rejected by manager");
            }

            // 3) Fan-out: شغل ثلاث مهام بالتوازي وانتظر الكل (نمط شائع جدًا)
            var tasks = new[]
            {
                ctx.CallActivityAsync<bool>("ChargePayment", req),
                ctx.CallActivityAsync<bool>("NotifyWarehouse", req),
                ctx.CallActivityAsync<bool>("SendCustomerEmail", req),
            };
            var results = await Task.WhenAll(tasks);

            if (!results.All(r => r))
                return await CompensateAsync(ctx, req.OrderId, reservation, "downstream failure");

            // 4) مؤجَّل: تابع بعد 7 أيام — CreateTimer بدل Task.Delay (المنصة بتخزّن المؤقت)
            await ctx.CreateTimer(TimeSpan.FromDays(7), ctx.CancellationToken);

            await ctx.CallActivityAsync("CloseOrder", req.OrderId);
            return "completed";
        }
        catch (TaskFailedException ex)
        {
            log.LogError(ex, "Activity failed: {Name}", ex.Name);
            return await CompensateAsync(ctx, req.OrderId, reservation, ex.Message);
        }
    }

    private static async Task<string> CompensateAsync(
        TaskOrchestrationContext ctx, string orderId, string reservation, string reason)
    {
        // التعويض نفسه activity (يعني بيتخزن وله إعادة محاولة):
        await ctx.CallActivityAsync("ReleaseStock", reservation);
        await ctx.CallActivityAsync("NotifyFailure", (orderId, reason));
        return $"compensated: {reason}";
    }

    // ── استقبال الموافقة البشرية من الخارج (يرفع الحدث المُنتظَر) ──
    [Function("Approve")]
    public async Task<IActionResult> Approve(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "orders/approvals/{instanceId}/approve")]
        HttpRequest req, string instanceId,
        [DurableTaskTrigger] DurableTaskClient client, CancellationToken ct)
    {
        var decision = await req.ReadFromJsonAsync<ApprovalDecision>(ct)
                       ?? new ApprovalDecision(false, "unknown");
        await client.RaiseEventAsync(instanceId, "ManagerApproval", decision, ct);
        return Results.Accepted();
    }
}

// ── الأنشطة في class مستقل: DI عادي بالـconstructor (الأنشطة مكان كل I/O) ──
public class StockActivities(StockService stock)
{
    [Function("ReserveStock")]
    public Task<string> ReserveStock(TaskActivityContext ctx, string orderId) =>
        stock.ReserveAsync(orderId, ctx.CancellationToken);

    [Function("ReleaseStock")]
    public Task ReleaseStock(TaskActivityContext ctx, string reservation) =>
        stock.ReleaseAsync(reservation, ctx.CancellationToken);

    [Function("CloseOrder")]
    public Task CloseOrder(TaskActivityContext ctx, string orderId) =>
        stock.FinalizeAsync(orderId, ctx.CancellationToken);
}

public class PaymentActivities(PaymentClient payments, EmailSender email)
{
    [Function("ChargePayment")]
    public Task<bool> ChargePayment(TaskActivityContext ctx, OrderRequest req) =>
        payments.ChargeAsync(req.OrderId, req.Total, ctx.CancellationToken);

    [Function("SendCustomerEmail")]
    public Task<bool> SendCustomerEmail(TaskActivityContext ctx, OrderRequest req) =>
        email.SendOrderConfirmationAsync(req.OrderId, req.CustomerEmail, ctx.CancellationToken);

    [Function("NotifyFailure")]
    public Task NotifyFailure(TaskActivityContext ctx, (string OrderId, string Reason) info) =>
        email.SendFailureNoticeAsync(info.OrderId, info.Reason, ctx.CancellationToken);
}
'''},
        {"type": "table", "caption": "قواعد الحتمية — أي مخالفة بتفسد الـreplay وبتنتج سلوك عشوائي صعب التشخيص",
         "head": ["ممنوع في الـorchestrator", "البديل الصح", "ليه"],
         "rows": [
             ["`DateTime.UtcNow` / `DateTime.Now`", "`ctx.CurrentUtcDateTime`", "الـreplay بيحصل في وقت مختلف → قرار مختلف (مثال: مهلة الموافقة)"],
             ["`Guid.NewGuid()`", "`ctx.NewGuid()`", "المعرّفات لازم تتطابق بين الإعادة والإعادة"],
             ["`Task.Delay(...)`", "`ctx.CreateTimer(...)` / `ctx.SleepAsync(...)`", "المؤقت لازم يُخزَّن في المنصة عشان ينجو من إعادة التشغيل"],
             ["استدعاء HTTP/قاعدة بيانات/بريد مباشرة", "لفّه في **activity** و`CallActivityAsync`", "أي I/O بيحصل مرتين أو أكتر مع كل replay"],
             ["`ILogger` عادي", "`ctx.CreateReplaySafeLogger(...)`", "الـlogger العادي بيسجّل نفس السطر مع كل replay"],
             ["`ConfigureAwait(false)`", "لا تستخدمه في الـorchestrator", "خيط إعادة التشغيل بيحتاج يستمر على نفس السياق — ممكن يكسر التنفيذ"],
             ["اعتماد على ترتيب تنفيذ المهام المتوازية", "`Task.WhenAll` وقراءة النتائج بعد الكل", "الأنشطة المتوازية بتكمل بترتيب غير مضمون"],
             ["تغيير متغير حالة (state) محلي بعد `await`", "اعتمد على نتائج الأنشطة و`ctx`", "الحالة الحقيقية في سجل الـorchestration، مش في الذاكرة"],
         ]},

        # ── 4) التطوير المحلي والنشر
        {"type": "heading", "level": 2, "text": "④ التطوير المحلي والنشر والتشخيص"},
        {"type": "code", "lang": "bash", "title": "functions-devops.sh", "filename": "functions-devops.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

# ═══ 1) الأدوات ═══
dotnet tool install -g Microsoft.Azure.Functions.CoreTools   # أو من حزمة المنصة
npm i -g azurite                                             # محاكي Storage محليًا
func --version

# ═══ 2) مشروع جديد بالنموذج الصح من أول أمر ═══
func init Shop.Notifications --worker-runtime dotnet-isolated --target-framework net10.0
cd Shop.Notifications && func new --template "HTTP trigger" --name Ping

# ═══ 3) الإعدادات المحلية (لا تُرفع لـGit) ═══
cat > local.settings.json <<'JSON'
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "ServiceBus": "Endpoint=sb://<ns>.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...",
    "Orders__MaxTotalWithoutApproval": "5000"
  }
}
JSON
# .gitignore: local.settings.json

# ═══ 4) شغّل محليًا (Azurite في طرفية أخرى) ═══
azurite --silent --location /tmp/azurite &
func start            # يطبع عناوين كل دالة: http://localhost:7071/api/ping

# ═══ 5) اختبار الدالة محليًا (HTTP) ═══
curl -s http://localhost:7071/api/ping | jq
# إرسال رسالة تجريبية لطابور (لو مربوط بـService Bus حقيقي):
az servicebus topic message send --namespace-name <ns> --topic-name orders-placed \
  --body '{"orderId":"o-1","email":"a@b.c","total":120}' 2>/dev/null || echo "استخدم Portal/SDK"

# ═══ 6) النشر (الأفضل من CI — الدرس 6.3.1) ═══
dotnet publish src/Shop.Notifications -c Release -o publish/
az functionapp create --resource-group rg-shop-dev --name fn-shop-notifications \
  --storage-account stshopdev --consumption-plan-location westeurope \
  --functions-version 4 --runtime dotnet-isolated --os-type Linux
# ⚠ لو Linux و.NET 10 → استخدم Flex Consumption (الخطة Consumption ما تدعمش .NET 10 على Linux)
az functionapp config appsettings set --name fn-shop-notifications --resource-group rg-shop-dev \
  --settings FUNCTIONS_WORKER_RUNTIME=dotnet-isolated
az functionapp deployment source config-zip --name fn-shop-notifications \
  --resource-group rg-shop-dev --src publish.zip

# ═══ 7) التشخيص: السجلات والتتبع والحالة ═══
az monitor app-insights metrics show --app fn-shop-notifications --resource-group rg-shop-dev \
  --metric requests/duration --interval PT1M
func durable get-history --connection-string-name AzureWebJobsStorage --task-hub-name <hub> 2>/dev/null || true
# الأسهل عمليًا: Application Insights → «Failures» و«End-to-end transaction details»
# ولفحص orchestration معيّن: اقرأ الحالة من الـstatus query URL اللي رجّعته الدالة.
'''},
        {"type": "callout", "kind": "warn", "title": "إمتى Functions مش الاختيار الصح",
         "md": "**① شغل أطول من حد الخطة** (10 د في Consumption): استخدم Durable أو خدمة عادية. **② اتصال دائم** (WebSocket/SSE/gRPC streaming): Functions مش مصممة له → App Service/ACA. **③ حالة في الذاكرة** (cache محلي، singleton counters): كل تنفيذ ممكن يكون على instance جديد → استخدم Redis/Storage. **④ حمل مستمر عالي**: الفوترة لكل تنفيذ بتبقى أغلى من خدمة ثابتة. **⑤ «function sprawl»**: 200 دالة صغيرة بلا اختبارات ولا عقود = نظام مستحيل الفهم؛ احتفظ بالحدود الواضحة (نفس منطق الـbounded contexts في 5.1.2). والقاعدة: لو الدالة بتعمل أكتر من «استقبال حدث → تحويل → استدعاء/حفظ → إخراج»، فكر في خدمة."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف إن **isolated worker** هو النموذج الوحيد المدعوم لـ.NET 10، وإن in-process انتهى دعمه 10 نوفمبر 2026.",
            "أعرف إن **Linux Consumption ما بيدعمش .NET 10** → Flex Consumption هو مسار الإنتاج على Linux.",
            "أقدر أبني مشروع Functions بـ`Azure.Functions.Sdk` + `OutputType Exe` + `ConfigureFunctionsWebApplication` وأعيد استخدام كل الـDI/Options/OTel اللي بنيته قبل كده.",
            "أفرق بين trigger وbinding، وأعرف أتعامل مع التكرار (idempotency) والـDLQ.",
            "أقدر أكتب orchestrator حتمي وأنقل كل I/O للأنشطة، وأستخدم `CurrentUtcDateTime`/`NewGuid`/`CreateTimer`/`CreateReplaySafeLogger`.",
            "أعرف نمط Fan-out/Fan-in والانتظار لحدث خارجي (موافقة بشرية) والتعويض عند الفشل.",
            "أقدر أشغّل محليًا بـAzurite وأنشر بـzip من CI وأشخّص بـApplication Insights.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على النموذج والخطط وDurable.",
         "questions": [
             {"q": "مشروع Functions جديد على .NET 10 وLinux. أي خطة + أي نموذج؟",
              "options": ["Consumption + in-process", "Flex Consumption (أو Premium/Dedicated) + **isolated worker**", "Consumption + isolated", "أي خطة + in-process"],
              "answer": 1,
              "explain": "in-process انتهى دعمه 10 نوفمبر 2026 وما بيدعمش .NET 10 أصلًا. و.NET 10 على Linux محتاج Flex Consumption (أو Premium/Dedicated) — Consumption على Linux مش مدعوم لـ.NET 10."},
             {"q": "`FUNCTIONS_WORKER_RUNTIME` مضبوط `dotnet` بينما الكود المنشور isolated. النتيجة؟",
              "options": ["هيشتغل عادي", "التطبيق يدخل حالة خطأ و500 لكل الدوال — الإعداد والكود لازم يتغيروا معًا (يفضَّل عبر slot)", "هيشتغل أبطأ", "هيتحول تلقائيًا"],
              "answer": 1,
              "explain": "ده أشهر خطأ في الهجرة: الـhost بيحاول يشغّل worker غلط. الحل: غيّر الإعداد والكود معًا، واستخدم deployment slot للتأكد قبل الإنتاج."},
             {"q": "ليه `DateTime.UtcNow` ممنوعة داخل الـorchestrator؟",
              "options": ["بطيئة", "لأن الـorchestrator بيتعاد تشغيله (replay) في أوقات مختلفة → قرارات مختلفة وسجل فاسد؛ البديل `ctx.CurrentUtcDateTime`", "لأنها مش thread-safe", "لأنها بتستهلك ذاكرة"],
              "answer": 1,
              "explain": "Durable بيعيد تشغيل الـorchestrator من الأول بعد كل نشاط. أي قيمة غير حتمية (وقت/عشوائي/I/O) بتنتج مسار مختلف عن المسجل. كل الشغل الحقيقي يروح للأنشطة."},
             {"q": "محتاج «استنى موافقة مدير لحد 3 أيام ثم كمّل». الأنسب؟",
              "options": ["`Task.Delay(3 أيام)` في دالة عادية", "`ctx.WaitForExternalEvent<ApprovalDecision>(\"ManagerApproval\", TimeSpan.FromDays(3))` في orchestrator + دالة HTTP ترفع الحدث", "طابور مع رسالة مؤجلة 3 أيام", "Timer function تفحص كل دقيقة"],
              "answer": 1,
              "explain": "الانتظار لحدث خارجي بمهلة هو نمط Durable المصمم للحالة دي: الحالة بتُخزَّن، مفيش عملية شغالة بتستهلك موارد، والموافقة بتوصل من HTTP فترفع الحدث ويكمل الـorchestrator."},
             {"q": "دالة Service Bus trigger رمَت exception. بيحصل إيه؟",
              "options": ["الرسالة بتضيع", "إعادة محاولة حسب السياسة، ثم **DLQ** — ولازم يكون فيه خطة لمعالجة الرسائل الميتة", "التطبيق بيتوقف", "الرسالة بترجع للطابور للأبد"],
              "answer": 1,
              "explain": "ده السلوك المتوقع. قرارك الهندسي: أي استثناء يستاهل إعادة محاولة (مؤقت: شبكة/قفل DB) وأيها «سم» (payload غلط) لازم يُسجَّل ويُرمى للـDLQ. وراقب عمق الـDLQ كمؤشر (2.3.4)."},
             {"q": "إيه اللي **مش** سبب لاستخدام Functions؟",
              "options": ["webhook خارجي", "مهمة مجدولة ليلية", "اتصال WebSocket دائم يبعت تحديثات لحظية", "معالجة رسالة من طابور"],
              "answer": 2,
              "explain": "الاتصالات الطويلة/الدائمة (WebSocket/SSE/gRPC streaming) محتاجة عملية شغالة باستمرار → App Service أو Container Apps (SignalR درس 2.3.1). الباقي حالات Functions الكلاسيكية."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "دالة شغالة + سير عمل حتمي باختبارات.",
         "items": [
             {"id": "t1", "title": "مهمة 1: webhook + مستهلك طابور على isolated worker — مع idempotency وDLQ",
              "md": "**السياق:** مزوّد دفع بيبعت webhook، ونظام الطلبات بينشر `order-placed` على Service Bus. عايزين دالتين: واحدة تستقبل الـwebhook، والتانية تستهلك الرسالة وتبعت بريد تأكيد.\n\n**المطلوب:**\n1. مشروع Functions بـ`Azure.Functions.Sdk` و`net10.0` و`OutputType Exe` و`ConfigureFunctionsWebApplication`.\n2. دالة `Webhook` بـ`AuthorizationLevel.Function`: تتحقق من توقيع المزوّد (HMAC بمفتاح من Key Vault/env)، وتفحص `EventId` ضد جدول/مفتاح idempotency، وترجع `202 Accepted` أو `200 {ignored:true}`.\n3. دالة `OnOrderPlaced` بـService Bus trigger + `ServiceBusOutput` لـ`orders-audit`، ومعالجة أخطاء صريحة: أخطاء مؤقتة → ارمِ (إعادة محاولة)، أخطاء بيانات → سجّل وأرجع (تجنب حلقة لا نهائية).\n4. `local.settings.json` + تشغيل محلي بـAzurite + سكريبت `curl` يختبر الحالتين (جديد/مكرر).\n5. **اختبارات**: unit tests للدالة باستخدام فئات مجردة (مش platform) — اختبار «مكرر → لا يرسل بريد» و«توقيع غلط → 401».",
              "criteria": [
                  "المشروع isolated worker بالكامل (مفيش أي `Microsoft.Azure.WebJobs.*`) ويشتغل بـ`func start`.",
                  "التحقق من التوقيع قبل أي معالجة، والمفتاح من إعداد/Key Vault (مش ثابت في الكود).",
                  "Idempotency: تنفيذ مكرر لنفس `EventId` **ما يبعتش بريد مرتين** — ومُثبت باختبار.",
                  "سياسة أخطاء مكتوبة في الكود بتعليق: أي الاستثناءات تُرمى (إعادة محاولة) وأيها تُبتلع (بيانات فاسدة) + ملاحظة عن الـDLQ.",
                  "`ServiceBusOutput` مستخدم للإخراج (مش SDK يدوي) — مع شرح سبب الاختيار.",
                  "اختباران على الأقل (مكرر/توقيع غلط) بيعملوا في `dotnet test` من غير Azure.",
                  "ملف `docs/functions-runbook.md`: أوامر التشغيل المحلي، النشر، ومكان مراقبة الفشل والـDLQ.",
              ],
              "hint": "للاختبارات من غير Azure: اجعل منطق الدالة في class عادي (`WebhookHandler`) والدالة نفسها غلاف رقيق — كده تختبر الـhandler مباشرة. وللتوقيع استخدم `HMACSHA256` مع مقارنة ثابتة الزمن (`CryptographicOperations.FixedTimeEquals`). ولو عايز idempotency محليًا للاختبار، `IMemoryCache`/`ConcurrentDictionary` خلف واجهة.",
              "solution": "البنية: `Functions.cs` (غلاف رقيق: deserialize + استدعاء handler + إرجاع result) و`Handlers/WebhookHandler.cs` (المنطق: تحقق توقيع → idempotency → أمر) و`Services/ISeenStore.cs` (تنفيذان: in-memory للاختبار، Redis/SQL للإنتاج). الاختبارات: (1) نفس `EventId` مرتين → `SendReceiptAsync` اتنادت مرة واحدة (بتحقق من mock) (2) توقيع غلط → `Results.Unauthorized` وما وصلش للمتجر (3) payload غير صالح → 400. دالة الطابور: `try { … } catch (JsonException) { log + return null /* لا إعادة محاولة */ }` مقابل ترك الاستثناءات المؤقتة تطلع. ملاحظة runbook: راقب `ServiceBus/DLQ` كمؤشر صحة (2.3.4)، واعمل صفحة/سكريبت يعيد تشغيل الرسائل الميتة بعد إصلاح السبب.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/azure-functions/dotnet-isolated-process-guide",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-service-bus-trigger",
                  "https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/functions-test-local",
                  "https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite",
              ]},
             {"id": "t2", "title": "مهمة 2: Durable orchestration بموافقة بشرية + تعويض + اختبارات حتمية",
              "md": "**السياق:** «طلب فيه موافقة»: احجز المخزون → لو `Total > 5000` استنى موافقة مدير (حتى 3 أيام) → نفّذ الدفع والشحن والبريد بالتوازي → عند أي فشل اعمل تعويض (حرر المخزون + أخطِر).\n\n**المطلوب:**\n1. `StartApproval` (HTTP) يبدأ orchestration بـ**InstanceId مشتق من `OrderId`** ويمنع التشغيل المزدوج.\n2. `OrderApproval` orchestrator **حتمي 100%**: `CreateReplaySafeLogger`، `CurrentUtcDateTime`، `WaitForExternalEvent` بمهلة، `Task.WhenAll` للأنشطة المتوازية، و`CreateTimer`/`SleepAsync` للمتابعة بعد 7 أيام.\n3. الأنشطة: `ReserveStock` · `ChargePayment` · `NotifyWarehouse` · `SendCustomerEmail` · `ReleaseStock` · `NotifyFailure` · `CloseOrder` — كلها بتستقبل `TaskActivityContext` وبتستخدم DI.\n4. دالة `Approve` (HTTP) ترفع الحدث `ManagerApproval`.\n5. **مخطط حالة** في `docs/approval-flow.md`: الحالات (Started → AwaitingApproval → Charging → Completed / Compensated / TimedOut) والانتقالات ومن المسؤول عن كل انتقال.\n6. **اختبارات**: على الأقل (أ) مسار بدون موافقة يكمل (ب) رفض → تعويض (ج) مهلة الموافقة → تعويض بسبب timeout — باستخدام Durable Task test APIs أو بتشغيل الأنشطة كـunit tests مع mocks.",
              "criteria": [
                  "مفيش أي `DateTime.UtcNow`/`Guid.NewGuid()`/`Task.Delay`/I/O مباشر داخل الـorchestrator (يُفحص بالقراءة).",
                  "`InstanceId` مشتق من `OrderId` ومحاولة بدء مكرر بترجع 409 (مش نسخة ثانية).",
                  "مسار الموافقة: انتظار حدث خارجي بمهلة 3 أيام، وقرار الرفض بيقود لتعويض.",
                  "Fan-out/Fan-in بـ`Task.WhenAll` مع فحص **كل** النتائج (مش افتراض النجاح).",
                  "التعويض نفسه أنشطة مخزَّنة (`ReleaseStock` + `NotifyFailure`) — يعني بينجو من إعادة التشغيل.",
                  "مخطط حالة مكتوب فيه الانتقالات والمسؤول عنها وحالة `TimedOut`.",
                  "ثلاثة اختبارات على المسارات الثلاثة بتشتغل في `dotnet test`.",
                  "فقرة في `docs/approval-flow.md` عن **حدود الـhistory**: إمتى يكبر السجل وإزاي تتعامل (أنشطة أقل/أكبر، fan-out محدود، أو continue-as-new).",
              ],
              "hint": "الحيلة الاختبارية الأهم: افصل المنطق في أنشطة قابلة للاختبار (كل activity class لها dependencies واضحة)، واختبر الـorchestrator كـ«ترتيب» باستخدام mocks. ولو استخدمت `Task.WhenAll` خد بالك إن النتائج بترجع بمصفوفة بنفس ترتيب المهام (مش ترتيب الإكمال). وللمهلة: `WaitForExternalEvent<T>(name, timeout)` بيرمي `TaskFailedException`/`OperationCanceledException` حسب الإصدار — لفّه في try/catch وسجّل `TimedOut` صراحةً.",
              "solution": "التدفق: `Started` → `ReserveStock` (نجاح) → [لو Total ≤ 5000] مباشرة إلى `Charging`؛ [لو > 5000] → `AwaitingApproval` مع مهلة 3 أيام: (أ) `Approved=true` → `Charging` (ب) `Approved=false` → `Compensated(rejected)` (ج) انتهت المهلة → `Compensated(timeout)`. في `Charging`: ثلاثة أنشطة بالتوازي؛ لو أي نتيجة false → `Compensated(downstream)`، وإلا `CreateTimer(7d)` → `CloseOrder` → `Completed`. الاختبارات: mock `StockService` و`PaymentService`، وشغّل الحالات الثلاثة بتغيير `Total` وقرار الموافقة. فقرة حدود الـhistory: كل نشاط بيضيف حدثًا للسجل، فـfan-out بآلاف العناصر بيضخّم الـhistory ويبطّئ الـreplay — الحل: دفعات (batches) من 50–100 مع `Task.WhenAll` لكل دفعة، أو تقسيم إلى orchestrations فرعية (sub-orchestrations)، أو `ContinueAsNew` للمهام الطويلة جدًا.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-dotnet-isolated-overview",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions/durable-functions-phone-verification",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions/durable-functions-orchestrations",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions/durable-functions-perf-and-scale",
                  "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions/durable-functions-external-events",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "دليل C# في نموذج isolated worker (مرجع أساسي)", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/dotnet-isolated-process-guide"},
            {"label": "الفروق بين isolated وin-process", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/dotnet-isolated-in-process-differences"},
            {"label": "مقارنة إصدارات runtime Azure Functions", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/functions-versions"},
            {"label": "Durable Functions في isolated worker", "url": "https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-dotnet-isolated-overview"},
            {"label": "أنماط الـorchestration (fan-out/fan-in · monitoring · human interaction)", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions/durable-functions-overview"},
            {"label": "خطط الاستضافة ومقارنتها", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale"},
            {"label": "Azurite (محاكي Storage محليًا)", "url": "https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite"},
            {"label": "Core Tools والأوامر", "url": "https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local"},
        ]},
    ],
}

LESSONS_S6_E = [_L1, _L2]
