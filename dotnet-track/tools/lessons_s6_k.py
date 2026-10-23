# -*- coding: utf-8 -*-
"""Stage 6 module 4: s6-m4-l1 — Capstone (من الكود إلى Azure بضغطة merge)."""

TODAY = "2026-10-22"

_L1 = {
    "id": "s6-m4-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الهدف: **نظام المرحلة 5 (الخدمات + الطوابير + المراقبة) منشور على Azure، وبيتحدث من Git لوحده، وبيفشل بأمان**. مش «رفعت نسخة ونجحت» — بل: بنية تُعاد إنشاؤها بأمر واحد · pipeline فيه بوابات بتكسر البناء فعلًا · نشر بـ**digest** بيمشي عبر 3 بيئات بـparity مثبت · canary بمؤشرات ورجوع **مجرَّب** لا مكتوب · أسرار بالهوية بلا سر واحد مخزّن · وفاتورة محسوبة قبل ما تبدأ. المشروع 6 ساعات (7 جلسات) والمُخرَج: مستودع + بيئة شغالة + `CAPSTONE.md` فيه الأدلة."},

        {"type": "terms", "title": "مفردات المشروع", "items": [
            {"term": "Artifact (القطعة الفنية)", "def": "الصورة + الـ**digest** الثابت. تُبنى **مرة واحدة** وتُرقّى بين البيئات — مش إعادة بناء لكل بيئة."},
            {"term": "Evidence (دليل)", "def": "مخرج أمر محفوظ بتاريخ يثبت إن خطوة حصلت فعلًا (what-if · نتائج بوابات · قياس p95 · رقم الفاتورة). من غير دليل = ما حصلش."},
            {"term": "Gate (بوابة)", "def": "فحص **required** بيكسر البناء/الدمج عند حد رقمي (تغطية · ثغرات · معمارية · parity)."},
            {"term": "Parity", "def": "تطابق البيئات في الإصدارات والمخطط ومفاتيح الإعداد؛ الاختلاف فقط في الحجم والتكلفة والبيانات."},
            {"term": "Rollback مُجرَّب", "def": "أمر رجوع واحد نُفّذ فعلًا في staging وزمنه مقاس بالثواني — مش فقرة في وثيقة."},
            {"term": "MTTR", "def": "الزمن من اكتشاف العطل لعودة الخدمة. الهدف في المشروع: **أقل من 5 دقائق** للإصدارات، وأقل من 30 للبنية."},
            {"term": "Cost envelope", "def": "سقف تكلفة شهري مكتوب (مثال: 50 دولارًا) + بنود + تنبيهات + إجراء عند التجاوز."},
            {"term": "Break-glass", "def": "مسار طوارئ محدود وموثّق، ويليه **PR خلال 24 ساعة** يرد الكود للواقع."},
            {"term": "Deployment stack", "def": "إدارة دورة حياة موارد Bicep: حذف/فصل الموارد اللي بطلت تصرّح بيها (بدل تراكمها)."},
            {"term": "Zero-secret pipeline", "def": "لا client secret ولا admin password ولا connection string فيها كلمة سر: OIDC + Managed Identity + Key Vault."},
        ]},

        # ── 1) الخريطة
        {"type": "heading", "level": 2, "text": "① الشكل النهائي: من commit لمستخدم — وكل نقطة فشل فيها حارس"},
        {"type": "code", "lang": "text", "title": "خريطة النظام (ارسمها بنفسك في CAPSTONE.md)", "filename": "docs/capstone-map.txt", "code": r'''  المطوّر                 GitHub                              Azure (3 مجموعات موارد)
 ┌────────┐   push   ┌───────────────────────────┐   OIDC    ┌──────────────────────────────┐
 │ feature│─────────▶│ CI (PR)                    │           │  rg-shop-dev                 │
 │ branch │          │  • restore --locked-mode   │           │   ACA env · orders·catalog   │
 └────────┘          │  • build /warnaserror      │           │   PostgreSQL B1ms (يُوقف ليلًا)│
     │               │  • unit + architecture     │           │   kv-shop-dev · la-shop-dev  │
     ▼               │  • coverage gate (رقمي)     │           └──────────────────────────────┘
 ┌────────┐          │  • gitleaks · dependency    │                        ▲
 │   PR   │─────────▶│  • what-if كتعليق على الـPR  │────────────────────────┘ نشر تلقائي
 └────────┘          └─────────────┬─────────────┘   (environment: dev)
     │                             │ merge (protected + merge queue)
     ▼                             ▼
   مراجعة                     ┌───────────────────────────┐
   بشرية                      │ Release                    │
                              │  • build image (مرة واحدة) │
                              │  • SBOM + provenance       │
                              │  • cosign sign (keyless)   │
                              │  • attestation             │
                              │  • OUTPUT: digest          │
                              └─────────────┬─────────────┘
                                            │ ترقية نفس الـdigest (promote.yml)
                        ┌───────────────────┼───────────────────────┐
                        ▼                   ▼                       ▼
              ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
              │ rg-shop-staging  │ │ environment:       │ │ rg-shop-prod             │
              │ نفس الإصدارات     │ │ staging (تلقائي)   │ │ environment: production  │
              │ حجم أصغر · بلا HA │ │ • smoke tests      │ │ • required reviewers     │
              │ • قياس خط الأساس  │ │ • parity-check     │ │ • canary 5→25→60→100     │
              └──────────────────┘ └──────────────────┘ │ • verify + auto-rollback   │
                                                        │ • HA · retention 90 · PE   │
                                                        └──────────────────────────┘
                                                                   │
                              ┌────────────────────────────────────┴─────────────┐
                              ▼                                                  ▼
                     المراقبة (من المرحلة 5)                              التكلفة والتدقيق
              /health · /alive · p95 · معدل 5xx · طول طابور        Cost analysis · budget 50$
              OTel → App Insights/Log Analytics                    deployments.log · audit شهري

الحُرّاس على المسار: بوابات CI ← موافقة PR ← توقيع الصورة ← موافقة بيئة الإنتاج ← canary بمؤشرات ← تحقق بعد النشر ← رجوع بأمر واحد
'''},
        {"type": "callout", "kind": "goal", "title": "الخمس قواعد الحاكمة للمشروع (لو خالفت واحدة، المشروع ناقص)",
         "md": "**① تُبنى مرة، تُرقّى بالـdigest** — مفيش إعادة بناء بين البيئات. **② صفر أسرار مخزّنة** — OIDC للنشر وManaged Identity للتطبيق وKey Vault لما يتبقى. **③ كل بوابة لها حد رقمي وخطة فشل** — مش «نتمنى تكون الجودة عالية». **④ الرجوع مُجرَّب ومقيس** — نفّذته في staging وسجّلت الزمن. **⑤ البنية ككود هي الحقيقة** — أي تغيير يدوي من Portal يتبعه PR خلال 24 ساعة."},

        # ── 2) النطاق
        {"type": "heading", "level": 2, "text": "② النطاق: إيه اللي داخل وإيه اللي خارج (اكتبه قبل ما تبدأ)"},
        {"type": "table", "caption": "نطاق مُتفق عليه = مشروع يخلص. أي بند «خارج» له سبب مكتوب",
         "head": ["البند", "داخل النطاق", "خارج النطاق", "السبب"],
         "rows": [
             ["الخدمات", "2–3 خدمات من مشروع المرحلة 5 (مثلًا orders + catalog + worker) + gateway/BFF لو موجود",
              "كل الخدمات السبع", "الوقت: التركيز على **مسار النشر** مش على عدد الخدمات"],
             ["المنصة", "**Container Apps** (Consumption) في منطقة واحدة (westeurope/northeurope)",
              "AKS · multi-region · service mesh", "ACA = أقل عبء تشغيلي وأرخص لمشروع فردي (6.2.1)، وAKS محتاج cluster كامل"],
             ["البيانات", "PostgreSQL Flexible **Burstable B1ms** + Blob Storage + Redis مُدار أو في الحاوية",
              "Cosmos DB · SQL vCore · Event Hubs", "أرخص بداية حقيقية (~12–15 دولار) وكفاية للحمل (6.2.4)"],
             ["الرسائل", "RabbitMQ (من المرحلة 5) على ACA أو Azure Service Bus",
              "Kafka", "إعادة استخدام ما بُني في 5.2.1 بلا إعادة تعلم"],
             ["البنية ككود", "**Bicep**: قالب واحد + 3 ملفات معاملات + deployment stack على dev",
              "Terraform + Bicep معًا", "أداة واحدة = مصدر حقيقة واحد (6.3.4)"],
             ["CI/CD", "GitHub Actions: CI + Release + Promote + Infra + drift أسبوعي",
              "Azure DevOps · Argo CD · GitOps كامل", "المنصة المتاحة مجانًا لمستودع شخصي"],
             ["النشر", "Canary على ACA بـrevisions + smoke tests + auto-rollback بعتبات",
              "Argo Rollouts · Flagger · shadow traffic", "ACA بيدي canary أصلي بلا إضافات"],
             ["الأسرار", "Managed Identity + Key Vault (vault لكل بيئة) + صفر أسرار في Git",
              "External Secrets Operator · HSM · Premium vault", "الحد الأدنى الآمن والكافي"],
             ["المراقبة", "`/health` و`/alive` + OTel → App Insights/Log Analytics + لوحة p95 و5xx وطابور",
              "Grafana stack كامل · alerting متقدم · SLO burn-rate", "يكفي لاتخاذ قرار الرجوع (6.3.3)"],
             ["التكلفة", "تقدير مكتوب + budget بتنبيهات 50/80/100 + إيقاف dev + تقرير شهري",
              "reservations/Savings Plans (تحتاج 60 يوم قياس)", "مشروع 6 ساعات ما لوش تاريخ استهلاك بعد (6.2.5)"],
             ["الاختبارات", "بوابات: وحدة · تكامل (Testcontainers) · تغطية رقمية · معمارية · عقود · ثغرات صور",
              "اختبار حمل كامل (k6 لساعات) · chaos engineering", "قياس أساسي للحمل يكفي لقرار canary"],
         ]},

        # ── 3) الجلسات
        {"type": "heading", "level": 2, "text": "③ الجلسات السبع (360 دقيقة) — كل جلسة بمُخرَج ودليل"},
        {"type": "steps", "title": "اشتغل بالترتيب: كل جلسة بتبني على اللي قبلها",
         "items": [
             {"title": "الجلسة 1 (50 دقيقة): البنية ككود — 3 بيئات تُنشأ بأمر واحد",
              "md": "**اعمل:** `infra/main.bicep` (resource group · ACA environment · PostgreSQL Flexible · Key Vault · Log Analytics · Storage · Container App) + `dev/staging/prod.bicepparam` + وسوم موحدة فيها `managedBy` و`env`. أنشئ البيئات الثلاث. **الدليل:** `what-if` يرجع `NoChange` في التشغيل الثاني، و`parity-check` أخضر، وقائمة موارد لكل بيئة.",
              "code": r'''az bicep build --file infra/main.bicep
az deployment group create -g rg-shop-dev    --template-file infra/main.bicep --parameters infra/dev.bicepparam
az deployment group create -g rg-shop-staging --template-file infra/main.bicep --parameters infra/staging.bicepparam
# الدليل 1: معاينة ثانية = لا تغييرات
az deployment group what-if -g rg-shop-dev --template-file infra/main.bicep --parameters infra/dev.bicepparam \
  --result-format ResourceIdOnly | tee artifacts/whatif-dev.txt
# الدليل 2: دورة حياة (stack) على dev — احذف موردًا من الكود وشوف detach مقابل delete
az stack group create --name shop-dev-stack --resource-group rg-shop-dev \
  --template-file infra/main.bicep --parameters infra/dev.bicepparam \
  --action-on-unmanage detach --deny-settings-mode denyDelete --yes
# الدليل 3: الموارد الفعلية
az resource list -g rg-shop-dev -o table
az resource list -g rg-shop-prod -o table''',
              },
             {"title": "الجلسة 2 (50 دقيقة): الصورة والسجل — صغيرة وموقعة وبلا ثغرات حرجة",
              "md": "**اعمل:** `Dockerfile` متعدد المراحل على `aspnet:10.0-noble-chiseled` (أو NativeAOT لو الخدمة تسمح) + `.dockerignore` + بناء في CI بـ`buildx` + دفع لـACR بهوية (بلا admin password) + **SBOM وprovenance وتوقيع cosign**. **الدليل:** حجم الصورة · نتيجة Trivy · مخرجات `cosign verify` · الـdigest.",
              "code": r'''# الدليل: الحجم (من 6.1.3 — الهدف أقل من 100 MB مضغوطة للـchiseled)
docker build -f Dockerfile -t shop/orders:local .
docker image ls shop/orders:local
# الدليل: الثغرات
trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed shop/orders:local
# الدليل: التوقيع والتحقق (keyless)
cosign sign --yes $ACR.azurecr.io/shop/orders@$DIGEST
cosign verify $ACR.azurecr.io/shop/orders@$DIGEST --certificate-identity-regexp "https://github.com/"
# الدليل: SBOM مُرفق بالصورة (يُنتجه build-push-action بـ sbom: true ويُخزَّن كـartifact في السجل)
#   الطريقة الرسمية للفحص: Docker Scout / Microsoft Defender for Containers، أو:
#   docker sbom <image>   (لو Docker Desktop/CLI فيه الأمر في إصدارك)
docker sbom shop/orders:local 2>/dev/null | head -n 15 || \
  echo "راجع الـSBOM من أداة السجل — تأكد إنه موجود قبل ما تعتمد عليه وقت ثغرة"''',
              },
             {"title": "الجلسة 3 (55 دقيقة): CI وبوابات الجودة — اكسر البناء عمدًا 3 مرات",
              "md": "**اعمل:** `.github/workflows/ci.yml` (restore مقفل · build بتحذيرات كأخطاء · وحدة · تكامل بـTestcontainers · بوابة تغطية رقمية · gitleaks · dependency review) + `quality.yml` للجدول الأسبوعي. **الدليل:** 3 PRs تكسر البوابات عمدًا (اختبار فاشل · تغطية تحت الحد · اعتماد مخالف للمعمارية) وكل واحد **فشل فعلًا**.",
              "code": r'''# الأدلة: لقطة/مخرج لكل تجربة كسر
#   ① اختبار فاشل        → job "Unit tests" أحمر
#   ② حذف اختبارين       → بوابة التغطية: "line coverage = 74.2% (threshold 80%)"
#   ③ Domain يعتمد على EF → اختبار معماري: "المجال اعتمد على طبقة أعلى: Shop.Domain.Services.X"
python3 scripts/coverage_gate.py coverage-report/Cobertura.xml 80
dotnet test tests/Shop.ArchitectureTests -c Release --no-build --logger "trx"
bash scripts/quality-gates.sh 2>&1 | tee artifacts/quality-local.txt''',
              },
             {"title": "الجلسة 4 (55 دقيقة): نشر بلا سر واحد — OIDC + بيئات + موافقة",
              "md": "**اعمل:** app registration + federated credentials (`environment:dev`/`staging`/`production`) + GitHub Environments (production بـrequired reviewers وbranch policy) + `release.yml` (بناء + توقيع + إخراج digest) + `promote.yml` (ترقية **نفس الـdigest** عبر البيئات). **الدليل:** مخرجات `az account show` من داخل الـworkflow · لقطة الـjob **واقف في انتظار الموافقة** · تأكيد إن staging وprod على نفس الـdigest.",
              "code": r'''# الدليل 1: لا أسرار Azure في المستودع
grep -rniE "AZURE_CREDENTIALS|client_secret|admin-enabled true|password=" .github/ infra/ scripts/ || echo "✅ صفر أسرار"
# الدليل 2: سلسلة الثقة
az ad app federated-credential list --id $APP_ID --query "[].{name:name,subject:subject}" -o table
gh api repos/$OWNER/$REPO/environments --jq '.environments[] | .name'
# الدليل 3: نفس digest في البيئتين
for E in staging prod; do
  printf "%-8s " "$E"
  az containerapp show -n orders -g rg-shop-$E --query "properties.template.containers[0].image" -o tsv
done
# الدليل 4: من وافق ومن نشر
gh api "repos/$OWNER/$REPO/deployments?per_page=5" \
  --jq '.[] | "\(.created_at) \(.environment) \(.sha[0:8]) \(.creator.login)"' ''',
              },
             {"title": "الجلسة 5 (55 دقيقة): canary + smoke tests + رجوع مُجرَّب بالثواني",
              "md": "**اعمل:** `deploy/canary.sh` (5% → 25% → 60% → موافقة → 100% مع bake time) + `deploy/smoke.sh` (5 مسارات بأكواد متوقعة: 200/200/200/401/404) + `deploy/verify-and-rollback.sh` (خط أساس + عتبات + أمر رجوع). **الدليل:** **تجربة رجوع متعمدة** بنسخة فيها عطل (مثلًا `Thread.Sleep(3000)` في مسار) وزمن الرجوع مقاس بالثواني، وتوزيع حركة موثق بعد كل خطوة.",
              "code": r'''# الدليل 1: خط الأساس قبل النشر (يُحفظ في docs/baseline.md)
bash deploy/smoke.sh staging | tee artifacts/smoke-staging.txt
# الدليل 2: canary متدرج
az containerapp revision list -n orders -g rg-shop-prod -o table
az containerapp ingress show -n orders -g rg-shop-prod --query traffic -o table
# الدليل 3: تجربة الرجوع (الأهم في المشروع كله)
time bash deploy/rollback-drill.sh staging        # نسخة معطوبة → اكتشاف → رجوع
#   الناتج المتوقع: "↩ رجعنا إلى orders--rev12" + زمن بالثواني
# الدليل 4: بعد الرجوع، الخدمة سليمة
bash deploy/smoke.sh prod | tee artifacts/smoke-after-rollback.txt''',
              },
             {"title": "الجلسة 6 (50 دقيقة): الإعدادات والأسرار والتوسع والإيقاف اللطيف",
              "md": "**اعمل:** ConfigMap/env بمفاتيح **متطابقة** بين البيئات (قيم مختلفة) + Key Vault لكل بيئة + `IOptions` بـ`ValidateOnStart` + 3 probes مضبوطة بحساب المهلة + requests/limits مع knobs الـGC + HPA/KEDA على طول طابور RabbitMQ + PDB + إيقاف لطيف (`ShutdownTimeout` + تصريف Outbox). **الدليل:** جدول المفاتيح لكل بيئة · نتيجة اختبار التوسع بحمل k6 · مخرجات `kubectl`/`az` للنسخ تحت الحمل · سجل يوضح تصريف العمل عند `rollout restart`.",
              "code": r'''# الدليل 1: parity في المفاتيح (القيم مختلفة، المفاتيح لا)
bash scripts/parity-check.sh | tee artifacts/parity.txt
# الدليل 2: التوسع تحت حمل (من 6.1.5)
k6 run --vus 50 --duration 2m scripts/load.js &
watch -n 5 'az containerapp replica list -n orders -g rg-shop-staging -o table'
# الدليل 3: الإيقاف اللطيف — صفر 503 أثناء إعادة النشر
az containerapp revision restart -n orders -g rg-shop-staging &
for i in $(seq 1 60); do
  curl -s -o /dev/null -w "%{http_code}\n" https://$URL/api/v1/catalog >> artifacts/restart-codes.txt
  sleep 1
done
grep -c 503 artifacts/restart-codes.txt || echo "✅ صفر 503"''',
              },
             {"title": "الجلسة 7 (45 دقيقة): التكلفة والتدقيق والتوثيق",
              "md": "**اعمل:** `docs/cost-estimate.md` (بنود + حساب ACA بالثواني لـ3 سيناريوهات + قرار الالتزام) + budget بتنبيهات 50/80/100 + إيقاف dev ليلًا + workflow تقرير شهري + `docs/deployments.log` + **`CAPSTONE.md`** بكل الأدلة. **الدليل:** رقم التكلفة الفعلي من Cost analysis مقابل التقدير · لقطة التنبيه · سجل النشر · ملف الـcapstone مكتمل.",
              "code": r'''# الدليل 1: التكلفة الفعلية مقابل التقدير
az consumption usage list --query "[].{r:instanceName,cost:pretaxCost}" -o table | head -n 20
# الدليل 2: الميزانية والتنبيهات
az consumption budget list -o table
# الدليل 3: الموارد المنسية (تسريب الفلوس)
az disk list --query "[?diskState=='Unattached'].name" -o tsv
az network public-ip list --query "[?ipConfiguration==null].ipAddress" -o tsv
# الدليل 4: الانحراف بين الكود والواقع (أسبوعيًا)
az deployment group what-if -g rg-shop-prod --template-file infra/main.bicep \
  --parameters infra/prod.bicepparam --result-format ResourceIdOnly | tee artifacts/drift.txt''',
              },
         ]},

        # ── 4) الأدلة
        {"type": "heading", "level": 2, "text": "④ الأدلة المطلوبة: جدول «إزاي أثبت إني عملتها»"},
        {"type": "table", "caption": "كل دليل = مخرج أمر محفوظ بتاريخ. لو مش موجود، البند مش متحقق",
         "head": ["#", "الإثبات", "الأمر/المكان", "الشكل المتوقع"],
         "rows": [
             ["1", "البنية تُعاد إنشاؤها بأمر", "`az deployment group create …` ×3", "3 مجموعات موارد بموارد متطابقة الأنواع ومختلفة الحجم"],
             ["2", "الكود = الواقع", "`what-if` ثاني", "`= NoChange` لكل الموارد (ولا `Create` ولا `Delete`)"],
             ["3", "لا انحراف", "`artifacts/drift.txt`", "فارغ أو مبرر"],
             ["4", "صورة صغيرة", "`docker image ls`", "أقل من ~100 MB للـchiseled (أو ~12 MB للـAOT)"],
             ["5", "بلا ثغرات حرجة", "`trivy image --exit-code 1`", "كود خروج 0 · صفر CRITICAL · HIGH بلا إصلاح موثّق"],
             ["6", "صورة موقعة", "`cosign verify`", "تحقق ناجح بهوية GitHub للمستودع"],
             ["7", "digest ثابت", "`az containerapp show --query …image`", "`@sha256:…` في **كل** البيئات (لا `:latest`)"],
             ["8", "بوابة تغطية تفشل تحت الحد", "لقطة من PR تجريبي", "`✗ FAIL: التغطية تحت الحد بنقص X نقطة`"],
             ["9", "بوابة المعمارية", "`dotnet test tests/Shop.ArchitectureTests`", "6 قواعد خضراء + تجربة كسر موثقة"],
             ["10", "صفر أسرار", "`grep` + قائمة secrets المستودع", "لا client secret ولا admin password ولا كلمة سر اتصال"],
             ["11", "OIDC شغال", "`az account show` من داخل job", "اشتراك صحيح بلا secret + `id-token: write`"],
             ["12", "موافقة بشرية", "لقطة Deployments", "job واقف «Waiting for reviewers» ثم موافقة باسم"],
             ["13", "parity", "`scripts/parity-check.sh`", "✅ مع diff مفاتيح فارغ بين staging وprod"],
             ["14", "smoke tests", "`deploy/smoke.sh`", "5 مسارات: 200/200/200/401/404"],
             ["15", "canary متدرج", "`az containerapp ingress show`", "أوزان موثقة بعد كل خطوة (5→25→60→100)"],
             ["16", "**رجوع مُجرَّب**", "`time deploy/rollback-drill.sh`", "اكتشاف → رجوع في **أقل من 90 ثانية** + خدمة سليمة بعده"],
             ["17", "توسع تحت حمل", "`az containerapp replica list` + k6", "تصاعد النسخ ثم نزولها (مع نافذة الاستقرار)"],
             ["18", "إيقاف لطيف", "ملف أكواد أثناء restart", "**صفر 503** (أو مبرر ومقاس)"],
             ["19", "التكلفة", "`docs/cost-estimate.md` + Cost analysis", "تقدير مقابل فعلي ±30% مع تفسير الفرق"],
             ["20", "ميزانية وتنبيهات", "`az consumption budget list`", "حد + تنبيهات 50/80/100% + إجراء عند التجاوز"],
             ["21", "تدقيق النشر", "`docs/deployments.log`", "سطر لكل نشر: التاريخ · البيئة · digest · الموافِق · النتيجة"],
             ["22", "التوثيق", "`CAPSTONE.md`", "كل الأدلة أعلاه مضمّنة أو مربوطة + القرارات + ما تعلمته"],
         ]},
        {"type": "code", "lang": "bash", "title": "scripts/evidence.sh — اجمع كل الأدلة في ملف واحد بتاريخ", "filename": "scripts/evidence.sh", "code": r'''#!/usr/bin/env bash
# يجمع أدلة الـCapstone في artifacts/evidence-YYYYMMDD-HHMM/ — شغّله في نهاية كل جلسة.
set -uo pipefail
OUT="artifacts/evidence-$(date +%Y%m%d-%H%M)"; mkdir -p "$OUT"
say() { echo "── $1" | tee -a "$OUT/INDEX.md"; }

say "1) البنية: الموارد في كل بيئة"
for E in dev staging prod; do
  az resource list -g "rg-shop-$E" -o table > "$OUT/resources-$E.txt" 2>&1
done

say "2) الانحراف: what-if (لا تغييرات متوقعة)"
for E in dev staging prod; do
  az deployment group what-if -g "rg-shop-$E" \
    --template-file infra/main.bicep --parameters "infra/$E.bicepparam" \
    --result-format ResourceIdOnly > "$OUT/whatif-$E.txt" 2>&1
done

say "3) إصدار التطبيق (digest) في كل بيئة — لازم متطابق"
for E in dev staging prod; do
  printf "%-8s " "$E" >> "$OUT/image-digests.txt"
  az containerapp show -n orders -g "rg-shop-$E" \
    --query "properties.template.containers[0].image" -o tsv >> "$OUT/image-digests.txt" 2>&1
done

say "4) parity"
bash scripts/parity-check.sh > "$OUT/parity.txt" 2>&1

say "5) حجم الصورة وثغراتها"
docker image ls shop/orders > "$OUT/image-size.txt" 2>&1
trivy image --severity CRITICAL,HIGH --ignore-unfixed --format table \
  "$(head -n3 "$OUT/image-digests.txt" | tail -n1 | awk '{print $2}')" > "$OUT/trivy.txt" 2>&1 || true

say "6) صفر أسرار"
grep -rniE "AZURE_CREDENTIALS|client_secret|admin-enabled true|password=" \
  .github/ infra/ scripts/ src/ > "$OUT/secrets-scan.txt" 2>&1 \
  && echo "⚠ فيه نتائج — راجع الملف" >> "$OUT/INDEX.md" \
  || echo "✅ صفر أسرار" >> "$OUT/secrets-scan.txt"

say "7) سلسلة الثقة (OIDC) والبيئات"
az ad app federated-credential list --id "${APP_ID:-}" \
  --query "[].{name:name,subject:subject}" -o table > "$OUT/oidc.txt" 2>&1 || true
gh api "repos/$OWNER/$REPO/environments" --jq '.environments[].name' > "$OUT/gh-environments.txt" 2>&1 || true

say "8) smoke tests + حالة التوزيع"
bash deploy/smoke.sh staging > "$OUT/smoke-staging.txt" 2>&1 || true
az containerapp ingress show -n orders -g rg-shop-prod --query traffic -o table > "$OUT/traffic-split.txt" 2>&1 || true

say "9) التكلفة والميزانية"
az consumption budget list -o table > "$OUT/budgets.txt" 2>&1 || true
az monitor log-analytics workspace list --query "[].{n:name,d:retentionInDays}" -o table > "$OUT/log-retention.txt" 2>&1 || true

echo; echo "الأدلة في: $OUT" ; ls -1 "$OUT" | sed 's/^/  /'
echo "انسخ الملخص إلى CAPSTONE.md واربط كل دليل بالجلسة المناسبة."
'''},

        # ── 5) اختبارات النشر
        {"type": "heading", "level": 2, "text": "⑤ اختبارات على «النشر» نفسه (مش على الكود)"},
        {"type": "code", "lang": "csharp", "title": "tests/Shop.DeploymentTests/Invariants.cs — قواعد البنية مفروضة باختبارات", "filename": "tests/Shop.DeploymentTests/Invariants.cs", "code": r'''using System.Text.RegularExpressions;
using Xunit;

namespace Shop.DeploymentTests;

/// <summary>
/// اختبارات على ملفات البنية والإعدادات نفسها — بتشتغل في CI من غير Azure.
/// الفكرة: قواعد 6.2.5 و6.3.5 بقت **مفروضة آليًا** بدل ما تكون نصيحة في وثيقة.
/// </summary>
public class Invariants
{
    private static readonly string RepoRoot = FindRepoRoot();

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !File.Exists(Path.Combine(dir.FullName, "global.json"))) dir = dir.Parent;
        return dir?.FullName ?? throw new InvalidOperationException("لم يُعثر على جذر المستودع");
    }

    private static string Read(string relative) =>
        File.ReadAllText(Path.Combine(RepoRoot, relative));

    // ⚠ الملفات لازم **تصرّح** بالقيم (مش تعليقات) عشان الاختبار يقرأها.
    [Theory]
    [InlineData("infra/dev.bicepparam", false, 30, "Burstable")]
    [InlineData("infra/prod.bicepparam", true, 90, "GeneralPurpose")]
    public void Environments_follow_the_cost_policy(string file, bool expectHa, int minRetention, string expectedTier)
    {
        var text = Read(file);
        Assert.Contains($"enableHa = {(expectHa ? "true" : "false")}", text);
        var retention = int.Parse(Regex.Match(text, @"logRetentionDays\s*=\s*(\d+)").Groups[1].Value);
        if (expectHa) Assert.True(retention >= minRetention, $"{file}: الاحتفاظ أقل من {minRetention}");
        else Assert.True(retention <= minRetention, $"{file}: الاحتفاظ في dev أعلى من {minRetention} (تكلفة بلا فائدة)");
        Assert.Contains(expectedTier, text);
    }

    [Fact]
    public void No_image_uses_a_mutable_tag()
    {
        foreach (var file in Directory.EnumerateFiles(RepoRoot, "*.yml", SearchOption.AllDirectories)
                     .Concat(Directory.EnumerateFiles(RepoRoot, "*.yaml", SearchOption.AllDirectories))
                     .Where(f => !f.Contains("node_modules")))
        {
            var text = File.ReadAllText(file);
            Assert.DoesNotContain(":latest", text);            // لا tag متحرك
            Assert.DoesNotContain("admin-enabled true", text); // لا ACR admin password
        }
    }

    [Fact]
    public void Workflows_declare_least_privilege_permissions()
    {
        foreach (var wf in Directory.EnumerateFiles(Path.Combine(RepoRoot, ".github/workflows"), "*.yml"))
        {
            var text = File.ReadAllText(wf);
            Assert.Contains("permissions:", text);              // صلاحيات مصرّحة
            Assert.DoesNotContain("write-all", text);           // ولا واسعة
        }
    }

    [Fact]
    public void Production_environment_is_gated()
    {
        var promote = Read(".github/workflows/promote.yml");
        Assert.Contains("environment: production", promote);    // موافقة بشرية
        Assert.Contains("id-token: write", promote);            // OIDC
        Assert.DoesNotContain("AZURE_CREDENTIALS", promote);    // بلا secret
    }

    [Fact]
    public void Every_feature_flag_has_an_expiry_date()
    {
        // الجدول في docs/feature-flags.md: | الاسم | الوصف | الحالة | المالك | تاريخ الانتهاء | الإطفاء |
        var doc = Read("docs/feature-flags.md");
        var rows = doc.Split('\n')
                      .Where(l => l.TrimStart().StartsWith('|') && !l.Contains("---"))
                      .Skip(1);                       // تخطَّ سطر العناوين
        Assert.NotEmpty(rows);

        foreach (var row in rows)
        {
            var name = row.Split('|').Skip(1).FirstOrDefault()?.Trim() ?? "?";
            Assert.Matches(@"\d{4}-\d{2}-\d{2}", row);   // لازم فيه تاريخ انتهاء بصيغة ISO
            // (الأعلام الميتة بتتراكم كفروع ميتة في الكود — 6.3.3)
            _ = name;
        }
    }

    [Fact]
    public void Rollback_command_is_documented_and_single_line()
    {
        var runbook = Read("docs/rollback-runbook.md");
        Assert.Contains("az containerapp ingress set", runbook);   // أمر واحد
        Assert.Contains("الثواني", runbook);                        // الزمن مُقاس
        Assert.Contains("drill", runbook, StringComparison.OrdinalIgnoreCase); // ومُجرَّب
    }
}
'''},
        {"type": "code", "lang": "bash", "title": "deploy/rollback-drill.sh — تدريب الرجوع (يتنفذ شهريًا)", "filename": "deploy/rollback-drill.sh", "code": r'''#!/usr/bin/env bash
# تدريب الرجوع: ينشر نسخة معطوبة عمدًا في staging، ويتأكد إن الحارس بيكتشفها وبيرجع.
# لو السكريبت ده فشل، يبقى plan الرجوع عندك على الورق بس.
set -uo pipefail
ENV="${1:-staging}"
RG="rg-shop-$ENV"
URL=$(az containerapp show -n orders -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
GOOD=$(az containerapp show -n orders -g "$RG" --query properties.latestRevisionName -o tsv)

echo "النسخة السليمة الحالية: $GOOD"
echo "── 1) انشر نسخة معطوبة (صورة فيها مسار بطيء عمدًا) ──"
BAD="orders--drill$(date +%s)"
az containerapp revision copy -n orders -g "$RG" --revision "$BAD" \
  --image "${BAD_IMAGE:?حدد BAD_IMAGE = صورة التدريب المعطوبة}"
az containerapp ingress set -n orders -g "$RG" --traffic-split "$GOOD=50" --traffic-split "$BAD=50"

echo "── 2) شغّل الحارس (اكتشاف + رجوع) وقِس الزمن ──"
START=$(date +%s)
BASELINE_P95=250 BASELINE_ERR=0.2 bash deploy/verify-and-rollback.sh "$BAD"
END=$(date +%s)
ELAPSED=$((END - START))

echo "── 3) تحقق إن الخدمة رجعت سليمة ──"
bash deploy/smoke.sh "$ENV" || { echo "✗ الرجوع فشل — افتح incident فورًا"; exit 1; }

echo
echo "✅ تدريب الرجوع نجح"
echo "   الزمن من البداية لعودة الحركة: ${ELAPSED}s  (الهدف: أقل من 90 ثانية)"
echo "$(date -Iseconds) env=$ENV drill=ok elapsed=${ELAPSED}s good=$GOOD bad=$BAD" >> docs/deployments.log
[ "$ELAPSED" -gt 90 ] && { echo "⚠ أبطأ من الهدف — راجع bake time وعتبات الكشف"; exit 2; } || exit 0
'''},

        # ── 6) أوضاع الفشل
        {"type": "heading", "level": 2, "text": "⑥ 12 وضع فشل متوقع في المشروع — وإزاي تتعامل"},
        {"type": "table", "caption": "دي الأخطاء اللي بتحصل فعلًا لأول مرة على السحابة (كلها حصلت لحد قبلك)",
         "head": ["#", "العرض", "السبب الأشهر", "الإصلاح/الوقاية"],
         "rows": [
             ["1", "`what-if` يُظهر `Create` لمورد موجود", "اسم/نوع/نطاق في القالب لا يطابق الواقع", "صلّح الاسم حتى يختفي الـCreate؛ أو `import`/stack للتبني (6.3.4)"],
             ["2", "فشل مصادقة في job النشر (`AADSTS700021`)", "الـsubject في الـfederated credential لا يطابق سياق التشغيل (branch مقابل environment)", "credential لكل pattern؛ و`environment:` في الـjob مطابق (6.3.1)"],
             ["3", "`403 Forbidden` على `az containerapp update`", "الدور ناقص أو على نطاق غلط", "Contributor على **مجموعة الموارد** فقط + انتظار انتشار الصلاحية"],
             ["4", "الصورة لا تُسحب (`Unauthorized`)", "ACR بلا دور `AcrPull` للهوية (و`admin-enabled false`)", "إسناد `AcrPull` لهوية الـcontainer app + `--registry-identity system`"],
             ["5", "التطبيق `Running` لكن 0/1 جاهز", "الـreadiness probe على مسار غير موجود أو المنفذ غلط", "probe على `/health` والمنفذ = `ASPNETCORE_HTTP_PORTS` (6.1.4)"],
             ["6", "`OOMKilled` بعد دقائق من الحمل", "حد الذاكرة أقل من heap الـServer GC", "رفع limit أو `DOTNET_GCHeapHardLimitPercent=0.65` أو `gcServer=0` (6.1.5)"],
             ["7", "أول طلب بعد السكون يستغرق 6 ثوانٍ", "scale-to-zero + cold start", "`minReplicas: 1` للواجهة و0 للـworkers؛ وثّق المقايضة (6.2.1)"],
             ["8", "بوابة التغطية حمراء على كل PR", "الحد على المشروع كله في مشروع قديم", "حد على **الكود الجديد** + حد عام منخفض يُرفع تدريجيًا (6.3.2)"],
             ["9", "الفاتورة أعلى من التقدير بـ3×", "استيعاب السجلات (EF Core على Information) أو dev شغال 24/7", "Warning للمسارات الصاخبة + retention 30 + إيقاف dev (6.2.5)"],
             ["10", "staging نجح وprod فشل", "فرق parity: مفتاح إعداد ناقص أو صلاحية أو إصدار مخطط", "`parity-check.sh` كـgate قبل النشر (6.3.5)"],
             ["11", "503s أثناء إعادة النشر", "الـprobes/الإيقاف اللطيف غير مضبوطين أو `preStop` ناقص", "`ShutdownTimeout` + تصريف Outbox + `preStop sleep` (6.1.5)"],
             ["12", "موارد منسية بتتفوتر بعد التجارب", "مجموعات تجارب ما اتحذفتش + أقراص/IPs يتيمة", "فحص شهري + `az group delete` بعد كل تجربة (6.2.5)"],
         ]},

        # ── 7) التسليم
        {"type": "heading", "level": 2, "text": "⑦ معايير التسليم (Definition of Done) — 22 بندًا"},
        {"type": "checkpoints", "title": "لا تعتبر المشروع منتهيًا قبل ما تعدي على كل بند", "items": [
            "1. البنية كلها في `infra/` كقالب **واحد** + 3 ملفات قيم، وتُنشأ بأمر واحد لكل بيئة.",
            "2. `what-if` ثاني يرجع `NoChange` — الكود = الواقع (ولا مورد مُنشأ يدويًا).",
            "3. deployment stack مفعّل على dev ومُجرَّب (detach مقابل delete مفهوم وموثق).",
            "4. الصورة chiseled/AOT بأقل من ~100 MB، و`trivy` صفر CRITICAL، وSBOM + provenance + توقيع cosign.",
            "5. كل البيئات تشتغل بـ**digest** (ولا `:latest` في أي ملف — ومفروض باختبار).",
            "6. CI فيه: restore مقفل · تحذيرات كأخطاء · وحدة · تكامل · بوابة تغطية رقمية · معمارية · gitleaks · dependency review.",
            "7. **ثلاث تجارب كسر متعمدة موثقة** (اختبار · تغطية · معمارية) — كل واحدة فشّلت البناء.",
            "8. البوابات البطيئة (Trivy على الصورة · Stryker · drift) على جدول، مش على كل PR.",
            "9. صفر أسرار Azure في المستودع: OIDC للنشر · Managed Identity للتطبيق · Key Vault للباقي (ومفروض باختبار).",
            "10. federated credentials منفصلة لكل بيئة بالـsubject الصح، وأدوار محدودة بمجموعات الموارد.",
            "11. GitHub Environments: production بـrequired reviewers + branch policy؛ dev/staging تلقائي.",
            "12. `promote.yml` بيرقّي **نفس الـdigest** — ومثبت بمخرجات من البيئتين.",
            "13. smoke tests بـ5 مسارات وأكواد متوقعة (200/200/200/401/404) بعد كل نشر.",
            "14. خط أساس (p95 · معدل أخطاء) مسجّل **قبل** النشر في staging.",
            "15. canary متدرج بأوزان موثقة وبake times، مع موافقة يدوية قبل 100%.",
            "16. **تدريب رجوع منفّذ ومقيس**: اكتشاف → رجوع في أقل من 90 ثانية → خدمة سليمة بعده.",
            "17. probes مضبوطة بحساب المهلة + requests/limits + knobs الـGC + HPA/KEDA على الطابور + PDB.",
            "18. إيقاف لطيف بلا 503s أثناء إعادة النشر (موثق بملف أكواد).",
            "19. `parity-check.sh` أخضر بين staging وprod (digest · مخطط · مفاتيح · إصدار PostgreSQL · publicNetworkAccess).",
            "20. `docs/cost-estimate.md` بتقدير مقابل **فعلي** (فرق ±30% مفسَّر) + budget بتنبيهات 50/80/100 + إيقاف dev ليلًا.",
            "21. `docs/deployments.log` فيه سطر لكل نشر (التاريخ · البيئة · digest · الموافِق · النتيجة) + تدقيق من GitHub/Azure.",
            "22. `CAPSTONE.md` مكتمل: الخريطة · النطاق · الأدلة الـ22 · القرارات (ADRs) · أوضاع الفشل اللي حصلت فعلًا · ما تعلمته.",
        ]},
        {"type": "table", "caption": "معايير التقييم (لو بتقيّم نفسك أو بتعرضه على حد) — 7 محاور × 5 مستويات",
         "head": ["المحور", "1 (ناقص)", "3 (مقبول)", "5 (ممتاز)"],
         "rows": [
             ["البنية ككود", "موارد من Portal أو قوالب مكررة", "قالب + معاملات لكل بيئة، `what-if` قبل النشر",
              "قالب واحد + modules/AVM + stack لإدارة دورة الحياة + كشف drift أسبوعي + اختبارات على ملفات البنية"],
             ["الـpipeline", "build فقط", "CI + بوابات + نشر يدوي",
              "CI + release موقّع + promote بالـdigest + بوابات مكسورة عمدًا مُوثقة + زمن PR أقل من 5 دقائق"],
             ["الأمان", "أسرار في متغيرات المستودع", "OIDC + Key Vault",
              "صفر أسرار (مفروض باختبار) + هوية لكل بيئة + أدوار محدودة + pin بـSHA + تدقيق وصول"],
             ["النشر والرجوع", "نشر مباشر بلا تحقق", "canary + smoke tests",
              "canary متدرج + خط أساس + عتبات رجوع تلقائي + **تدريب رجوع مقيس** + سجل نشر"],
             ["المرونة والتوسع", "إعدادات افتراضية", "probes + requests/limits",
              "probes محسوبة + HPA/KEDA على الطابور + PDB + إيقاف لطيف بلا 503s + حساب اتصالات القاعدة"],
             ["التكلفة", "مفيش تقدير", "تقدير من الحاسبة",
              "تقدير + حساب يدوي بالثواني + فعلي مقابل تقدير + budget وتنبيهات + إيقاف dev + تقرير شهري"],
             ["التوثيق والأدلة", "README عام", "خطوات التشغيل",
              "`CAPSTONE.md` بـ22 دليلًا + ADRs + runbooks (نشر/رجوع/طوارئ) + مصفوفة تغييرات + ما تعلمته"],
         ]},

        # ── 8) القالب
        {"type": "heading", "level": 2, "text": "⑧ قالب `CAPSTONE.md` — املأه وأنت بتشتغل مش في الآخر"},
        {"type": "code", "lang": "text", "title": "CAPSTONE.md", "filename": "CAPSTONE.md", "code": r'''# Capstone المرحلة 6 — من الكود إلى Azure بضغطة merge

**الاسم:** …      **التاريخ:** …      **المستودع:** …      **المنطقة:** westeurope

## 1) الملخص التنفيذي (5 أسطر)
نظام من … خدمة منشور على Container Apps في 3 بيئات، بيتحدّث من Git بـpipeline
بلا أسرار، بـcanary ورجوع مُجرَّب في … ثانية، وبتكلفة فعلية … دولار/شهر مقابل تقدير … دولار.

## 2) الخريطة
(الصق `docs/capstone-map.txt` بعد ما تعدّله على نظامك الحقيقي)

## 3) النطاق
| داخل | خارج | السبب |
|---|---|---|
| … | … | … |

## 4) القرارات (ADRs)
| # | القرار | البدائل المرفوضة | السبب | الرابط |
|---|---|---|---|---|
| 14 | Container Apps بدل AKS/App Service | … | … | docs/adr/0014 |
| 15 | PostgreSQL Burstable | SQL Serverless · vCore | … | docs/adr/0015 |
| 16 | canary بـrevisions | blue-green · rolling | … | docs/adr/0016 |
| 17 | Bicep بدل Terraform | … | … | docs/adr/0017 |

## 5) الأدلة (22 بندًا)
| # | الإثبات | الأمر | النتيجة | الملف |
|---|---|---|---|---|
| 1 | البنية تُعاد إنشاؤها | `az deployment group create …` | ✅ 3 مجموعات | artifacts/resources-*.txt |
| … | … | … | … | … |

## 6) الأرقام
| المقياس | القيمة |
|---|---|
| زمن CI على PR | … دقيقة |
| حجم الصورة | … MB |
| ثغرات CRITICAL/HIGH | 0 / … |
| تغطية الأسطر | …% |
| p95 (staging) | … ms |
| زمن الرجوع (drill) | … ثانية |
| 503s أثناء إعادة النشر | … |
| التكلفة الفعلية/الشهر | … دولار |
| الفرق مقابل التقدير | …% |

## 7) أوضاع الفشل اللي حصلت فعلًا
| العرض | السبب | الحل | الوقاية الدائمة |
|---|---|---|---|

## 8) ما تعلمته (3 أشياء هتعملها مختلف المرة الجاية)
1. …
2. …
3. …

## 9) التشغيل
| المهمة | الأمر |
|---|---|
| إنشاء بيئة | `az deployment group create -g rg-shop-dev --template-file infra/main.bicep --parameters infra/dev.bicepparam` |
| نشر | `gh workflow run promote.yml -f digest=sha256:… -f target=staging` |
| رجوع | `bash deploy/rollback-drill.sh prod` أو الأمر الواحد في `docs/rollback-runbook.md` |
| جمع الأدلة | `bash scripts/evidence.sh` |
| فحص parity | `bash scripts/parity-check.sh` |
| التكلفة | `az consumption usage list -o table` + `docs/cost/YYYY-MM.md` |

## 10) تنظيف
- [ ] حذفت مجموعات التجارب
- [ ] أوقفت خادم dev (ومعيّاد استئنافه معروف: 7 أيام)
- [ ] التأكد من عدم وجود أقراص/IPs يتيمة
'''},
        {"type": "callout", "kind": "tip", "title": "سكريبت الـ3 دقائق في المقابلة (احفظه)",
         "md": "**① المشكلة:** «كان عندي نظام ميكروسيرفيسز بيشتغل محليًا بـCompose، والنشر كان يدويًا — يعني كل إصدار فيه خطر وكل رجوع بياخد نص ساعة». **② اللي عملته:** «حوّلت البنية لـBicep بثلاث بيئات من قالب واحد، وبنيت pipeline: صورة موقعة بـdigest، بوابات جودة رقمية (تغطية + معمارية + ثغرات)، ونشر بـOIDC من غير سر واحد، وترقية نفس الـdigest عبر البيئات مع parity-check آلي». **③ النتيجة بالأرقام:** «canary متدرج بعتبات رجوع تلقائي، وتدريب رجوع مقيس بـ**X ثانية**، وفاتورة **Y دولار** مقابل تقدير Z، وزمن CI **N دقائق**». **④ أصعب حاجة:** «اكتشفت إن staging كان بينجح وprod بيفشل بسبب مفتاح إعداد ناقص — فعملت سكربت parity بقارن **مفاتيح** الإعداد مش القيم، وبقى gate قبل النشر». **⑤ اللي اتعلمته:** «البوابات اللي مش بتفشل أبدًا = بوابات معطّلة؛ عشان كده كسرت البناء عمدًا 3 مرات أتأكد إنهم شغالين»."},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على قرارات المشروع.",
         "questions": [
             {"q": "ليه تبني الصورة مرة واحدة وترقّي الـdigest بدل ما تبني لكل بيئة؟",
              "options": ["أسرع بس", "**لأن اللي اختُبر في staging لازم يكون بالبايت اللي بينزل في prod** — البناء المتكرر بيُدخل اختلافات (ترتيب طبقات · حزم عائمة · زمن بناء) فبيفقد الاختبار معناه", "لأن ACR ما بيدعمش", "لأنه أرخص في التخزين"],
              "answer": 1,
              "explain": "ده أساس «promote the same artifact». مع digest ثابت، الفرق الوحيد بين البيئات هو الإعداد والحجم — وده اللي يخلي اختبار staging ذا قيمة."},
             {"q": "في المشروع، ليه اخترنا Container Apps مش AKS رغم إننا تعلمنا Kubernetes؟",
              "options": ["لأن AKS صعب", "**لأن العبء التشغيلي والتكلفة لأقل من 20 خدمة وفريق صغير ما بيبررواش cluster كامل** — ومهارات K8s بتفضل مفهومة عبر مفاهيم ACA (probes/scale/ingress)", "لأن ACA بيدعم Kubernetes API", "لأن AKS مش متاح"],
              "answer": 1,
              "explain": "القرار مبني على معايير 6.2.1: مفيش حاجة في النطاق بتطلب CRDs/operators/GPU/mesh مخصص، فـACA بيدي canary وKEDA وscale-to-zero بأقل إدارة. ولو ظهر شرط يتطلب الـAPI، النقل لـAKS موجود في ADR كـ«إشارة رجوع»."},
             {"q": "ليه «تدريب الرجوع» بند تسليم مش اختياري؟",
              "options": ["مطلوب من Azure", "**لأن خطة الرجوع غير المُجرَّبة بتفشل وقت الحادث بالذات** (أمر غلط · صلاحية ناقصة · نسخة قديمة اتعطّلت) — والهدف MTTR أقل من 5 دقائق", "بيوفر فلوس", "بيسرع النشر"],
              "answer": 1,
              "explain": "الحادث أسوأ وقت تكتشف فيه إن `revision deactivate` عطلت النسخة القديمة أو إن الدور ناقص. التدريب الشهري بيحوّل الرجوع من «أمل» لـ«أمر مُقاس»."},
             {"q": "staging نجح وكل البوابات خضرا، وprod فشل. أول حاجة تفحصها في مشروع زي ده؟",
              "options": ["الكود", "**فرق parity**: مفتاح إعداد ناقص · إصدار مخطط أقدم · صلاحية/هوية مختلفة · حجم أصغر بكثير بيخفي اختناقًا", "الـDNS", "السجلات"],
              "answer": 1,
              "explain": "عشان كده `parity-check.sh` gate قبل النشر: بيقارن digest · إصدار migrations · **مفاتيح** الإعداد · إصدار PostgreSQL · `publicNetworkAccess` · الأدوار. الفرق في المفاتيح هو الأشهر والأصعب في الاكتشاف."},
             {"q": "ليه حطينا اختبارات على ملفات البنية (`Invariants.cs`) مش بس على الكود؟",
              "options": ["عشان الاختبارات تبقى أكتر", "**عشان قواعد التكلفة والأمان في ملفات الإعدادات مش في الكود** — مثلًا HA في dev أو `:latest` أو احتفاظ 90 يومًا للتطوير: كلها فلوس وخطر بلا أي اختبار كود", "لأن Bicep مش قابل للاختبار", "لأنها أسرع"],
              "answer": 1,
              "explain": "النظام بيتكون من كود + إعدادات + بنية. اختبارات الـinvariants بتفرض سياسة التكلفة والأمان آليًا في CI، فالتغيير الغلط بيتكسر قبل ما يتنشر (وده أرخص بكتير من اكتشافه في الفاتورة)."},
             {"q": "مشروع 6 ساعات: تشتري reservation أو Savings Plan في الجلسة 7؟",
              "options": ["نعم توفيرًا", "**لا**: الالتزام بيتبني على 60 يوم قياس فعلي، ومشروع جديد مفيش له تاريخ استهلاك — الصح: تقدير + budget + تنبيهات + بنية رخيصة، والالتزام لاحقًا", "نعم لو الميزانية صغيرة", "لا لأن Azure ما بيوفرهمش"],
              "answer": 1,
              "explain": "الترتيب الصح من 6.2.5: صغّر البنية → اضبط السجلات → أوقف غير المستخدم → Dev/Test → **ثم** التزام على الجزء المستقر. الالتزام على حجم غلط = خسارة صافية لأنه غير قابل للإلغاء."},
         ]},

        {"type": "tasks", "title": "المشروع: 3 مهام مترابطة", "intro": "نفّذهم بالترتيب — كل مهمة بتسلّم اللي بعدها.",
         "items": [
             {"id": "t1", "title": "مهمة 1: من المستودع إلى 3 بيئات (البنية + الصورة + CI)",
              "md": "**السياق:** خد نظام المرحلة 5 (أو جزءًا منه: 2–3 خدمات + PostgreSQL + RabbitMQ) وحوّله لنظام يُنشأ بأمر.\n\n**المطلوب (الجلسات 1–3):**\n1. `infra/main.bicep` + `dev/staging/prod.bicepparam` بكل الموارد (ACA env · Container Apps · PostgreSQL Flexible · Key Vault · Log Analytics · Storage) بوسوم فيها `managedBy` و`env`، وإنشاء البيئات الثلاث بأوامر موثقة.\n2. `Dockerfile` chiseled/AOT لكل خدمة + `.dockerignore` + بناء في CI ودفع لـACR بهوية (`AcrPull`) بـ**digest** + SBOM/provenance/tوقيع cosign.\n3. `.github/workflows/ci.yml` فيه البوابات: restore مقفل · `/warnaserror` · وحدة · تكامل (Testcontainers) · **بوابة تغطية رقمية** · اختبارات معمارية · gitleaks · dependency review، مع `permissions` ضيقة و`concurrency` و`timeout-minutes`.\n4. **ثلاث تجارب كسر متعمدة** (اختبار فاشل · تغطية تحت الحد · اعتماد مخالف للمعمارية) موثقة بمخرجات.\n5. `scripts/evidence.sh` يشتغل ويجمع الأدلة 1–9 في مجلد بتاريخ.\n6. ADRs: `0014` (اختيار المنصة) · `0015` (اختيار قاعدة البيانات) · `0017` (اختيار أداة IaC) — كل واحد بالبدائل المرفوضة والأرقام.",
              "criteria": [
                  "البيئات الثلاث تُنشأ بأمر واحد لكل بيئة من **قالب واحد** (بلا تكرار موارد).",
                  "`what-if` ثاني = `NoChange` في البيئات الثلاث (دليل مرفق).",
                  "وسوم موحدة فيها `env` و`managedBy` على كل مورد مدفوع.",
                  "الصورة أقل من ~100 MB (أو ~12 MB للـAOT) و`trivy` صفر CRITICAL وموثّق.",
                  "الدفع لـACR بهوية + `AcrPull` (ولا `admin-enabled true` في أي ملف — ومفروض باختبار).",
                  "CI فيه البوابات الثمانية و`permissions: contents: read` و`timeout-minutes` و`if: always()` على رفع النتائج.",
                  "ثلاث تجارب كسر موثقة **بمخرجات فعلية** (مش «نجحت التجربة»).",
                  "3 ADRs بالبدائل والأرقام (مش وصفية).",
                  "`scripts/evidence.sh` ينتج مجلدًا بأدلة 1–9 + `INDEX.md`.",
              ],
              "hint": "ابدأ بـdev فقط وخلّي البقية نسخًا من ملف المعاملات — أسرع طريق لفهم القالب. ولو الوقت ضيق: خدمة واحدة + worker واحد كفاية لإثبات المسار كله. وللـdigest في CI: استخدم `steps.push.outputs.digest` من `docker/build-push-action` ومرّره كـ`outputs` للـjob.",
              "solution": "الترتيب العملي: (1) اكتب `main.bicep` بموارد dev أولًا وانشر (2) استخرج القيم المتغيرة لمعاملات وأنشئ `staging/prod.bicepparam` (3) شغّل `what-if` مرتين وأثبت `NoChange` (4) Dockerfile chiseled لكل خدمة وبنِ محليًا وقِس الحجم (5) `release.yml` يبني ويدفع ويوقع ويخرج الـdigest (6) `ci.yml` بالبوابات + تجارب الكسر الثلاث (7) `evidence.sh`. الأرقام النموذجية: حجم الصورة chiseled ~55–90 MB، CI على PR ~3–5 دقائق بعد الكاش، التغطية بعد البوابة 78–85%، وتكلفة dev ~25–35 دولارًا شهريًا (مع إيقاف الخادم ليلًا أقل من 20).",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/",
                  "https://learn.microsoft.com/en-us/azure/container-apps/",
                  "https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-net",
                  "https://learn.microsoft.com/en-us/dotnet/core/docker/build-container",
                  "https://trivy.dev/latest/docs/",
                  "https://docs.sigstore.dev/cosign/overview/",
              ]},
             {"id": "t2", "title": "مهمة 2: النشر بلا أسرار + canary + رجوع مُجرَّب",
              "md": "**السياق:** البنية والصورة جاهزين (مهمة 1). فاضل مسار النشر الآمن.\n\n**المطلوب (الجلسات 4–5):**\n1. `azure/70-oidc.sh`: app registration + service principal + **دور Contributor على مجموعة موارد واحدة لكل بيئة** + **federated credentials منفصلة** (`environment:dev`/`staging`/`production`) + متغيرات GitHub على مستوى البيئة (مش secrets).\n2. GitHub Environments: `production` بـ**required reviewers** + `deployment_branch_policy: protected`؛ و`dev`/`staging` تلقائي.\n3. `promote.yml`: يرقّي **نفس الـdigest** من staging لـproduction (بـ`needs` و`environment`) وأرشفة دليل النشر في `$GITHUB_STEP_SUMMARY`.\n4. `deploy/smoke.sh` (5 مسارات بأكواد متوقعة) + `deploy/canary.sh` (5→25→60→موافقة→100 مع bake time) + `deploy/verify-and-rollback.sh` (خط أساس + عتبات + رجوع).\n5. **`deploy/rollback-drill.sh` مُنفَّذ فعلًا على staging**: نسخة معطوبة عمدًا → اكتشاف → رجوع → تحقق، **والزمن مقاس بالثواني** ومكتوب في `docs/deployments.log`.\n6. `docs/rollback-runbook.md` (الأمر · المسؤول · التحقق اللاحق) + `docs/approval-checklist.md` (8 بنود) + `docs/change-matrix.md` (8 أنواع تغيير).\n7. اختبارات `tests/Shop.DeploymentTests` (Invariants) شغالة في CI وبتفشل لو حد كتب `:latest` أو شال `environment: production` أو نسي تاريخ انتهاء لعلم.",
              "criteria": [
                  "صفر أسرار Azure في المستودع (يُثبت بـgrep + باختبار Invariants).",
                  "federated credentials منفصلة لكل بيئة بالـsubject الصح (مخرجات `az ad app federated-credential list`).",
                  "الأدوار محدودة بمجموعة الموارد لكل بيئة (مش Contributor على الاشتراك).",
                  "production بـrequired reviewers + branch policy (لقطة/مخرجات `gh api`).",
                  "staging وprod على **نفس الـdigest** (مخرجات مقارنة).",
                  "smoke tests بخمس مسارات وأكواد متوقعة منها 401 و404.",
                  "**تدريب رجوع مُنفَّذ** بزمن مقاس بالثواني + خدمة سليمة بعده (دليل مرفق).",
                  "canary بأوزان موثقة بعد كل خطوة وبake times معلنة + موافقة يدوية قبل 100%.",
                  "runbook رجوع + checklist موافقة + مصفوفة تغييرات (8 صفوف).",
                  "اختبارات Invariants شغالة في CI ومُثبت إنها بتفشل على مخالفة متعمدة.",
              ],
              "hint": "أصعب خطوة عمليًا هي الحصول على مقاييس لكل revision عشان تعتبـارات الرجوع التلقائي. أبسط حل: سجّل عدد 5xx من logs الـcontainer app (`az containerapp logs show`) خلال آخر دقيقتين وقارنه بخط الأساس — إشارة خشنة لكنها حقيقية. ولو مفيش وقت لعتبات تلقائية، خلي الرجوع يدويًا بس **مقيس** (ده اللي بيتقيم فعلًا).",
              "solution": "الترتيب: (1) نفّذ `70-oidc.sh` واختبر بـjob صغير فيه `azure/login` + `az account show` (2) أنشئ البيئات بالـAPI وضيف الـvariables (3) `release.yml` → `outputs.digest` (4) `promote.yml` بـ`needs` (5) `smoke.sh` ثم `canary.sh` ثم `verify-and-rollback.sh` (6) `rollback-drill.sh` على staging وقِس الزمن (7) اختبارات Invariants. الأرقام النموذجية: زمن الرجوع من الاكتشاف لعودة الحركة **30–90 ثانية** (تحويل 100% لنسخة موجودة ودافئة)، وزمن التدريب كله ~5 دقائق. أشهر فشل: `AADSTS700021` بسبب subject غلط، و403 بسبب دور على نطاق غلط، و`Unauthorized` على سحب الصورة بسبب نقص `AcrPull`.",
              "resources": [
                  "https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure",
                  "https://learn.microsoft.com/en-us/azure/container-apps/revisions",
                  "https://docs.github.com/en/actions/deployment/targeting-different-environments/managing-environments-for-deployment",
                  "https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation",
                  "https://sre.google/sre-book/managing-incidents/",
              ]},
             {"id": "t3", "title": "مهمة 3: المرونة والتكلفة والتدقيق — وتسليم CAPSTONE.md",
              "md": "**السياق:** النظام بيتنشر بأمان. فاضل يفضى شغال بأمان: مرونة تحت الحمل، وفاتورة محسوبة، وتدقيق يُراجع.\n\n**المطلوب (الجلسات 6–7):**\n1. إعدادات وأسرار: vault لكل بيئة + مفاتيح إعداد **متطابقة** بين البيئات (قيم مختلفة) + `IOptions` بـ`ValidateOnStart` + `scripts/parity-check.sh` كـgate قبل النشر.\n2. مرونة: 3 probes بحساب المهلة مكتوب + requests/limits مع `DOTNET_GCHeapHardLimitPercent`/`gcServer` + **HPA أو KEDA على طول طابور RabbitMQ** + PDB + إيقاف لطيف (`ShutdownTimeout` + تصريف Outbox).\n3. **قياس تحت حمل**: k6 (50 VU لمدة دقيقتين) مع تسجيل عدد النسخ كل 5 ثوانٍ، وملف أكواد أثناء `revision restart` لإثبات **صفر 503** (أو تفسير مقاس).\n4. تكلفة: `docs/cost-estimate.md` (بنود + حساب ACA يدوي بالثواني لـ3 سيناريوهات + مقارنة منصات) + budget بتنبيهات 50/80/100 + إيقاف dev ليلًا بجدول + `cost-report.yml` شهري ينشئ `docs/cost/YYYY-MM.md`.\n5. تدقيق: `docs/deployments.log` + `scripts/deployment-audit.sh` (آخر 20 نشرًا من GitHub + Azure Activity Log) + workflow **كشف انحراف** أسبوعي يفتح issue لو `what-if` فيه فرق.\n6. `CAPSTONE.md` كامل بالقالب (الجلسة 8): خريطة · نطاق · ADRs · 22 دليلًا · جدول أرقام · أوضاع فشل حقيقية · ما تعلمته · أوامر التشغيل · قائمة تنظيف.\n7. **نفّذ التنظيف فعلًا**: احذف مجموعات التجارب، أوقف dev، وتأكد من عدم وجود موارد يتيمة — ووثّق الأثر على التكلفة.",
              "criteria": [
                  "parity-check أخضر بين staging وprod (و**مكسور عمدًا مرة** لإثبات إنه بيكشف).",
                  "probes بحساب المهلة مكتوب (`period × failureThreshold`) واختيار المسارات مبرر (`/alive` للـliveness لا `/health`).",
                  "توسع مبني على طول الطابور (HPA/KEDA) + PDB + مخرجات تُظهر تصاعد النسخ تحت k6 ونزولها.",
                  "ملف أكواد أثناء إعادة النشر يثبت صفر 503 (أو رقم مفسَّر).",
                  "تقدير تكلفة بحساب يدوي بالثواني لـ3 سيناريوهات + **رقم فعلي** من Cost analysis + تفسير الفرق.",
                  "budget + تنبيهات 50/80/100 + إجراء مكتوب عند التجاوز (مع ذكر إن Azure ما بيوقفش الموارد).",
                  "إيقاف dev مجدول (مع التعامل مع حد إعادة التشغيل التلقائي بعد 7 أيام).",
                  "سجل نشر + سكربت تدقيق + workflow كشف انحراف أسبوعي.",
                  "`CAPSTONE.md` فيه 22 دليلًا مرفقًا/مربوطًا + 3 أشياء اتعلمتها + أوامر التشغيل + قائمة تنظيف مُنفذة.",
              ],
              "hint": "لحساب ACA اليدوي: الثواني × vCPU ناقص المنحة (180,000 vCPU-s) × 0.000024 + الثواني × GiB ناقص 360,000 × 0.000003. ولصفر 503 أثناء إعادة النشر: تأكد إن الـreadiness probe بيفصل النسخة عن الحركة **قبل** ما تبدأ في الإيقاف، وإن `preStop` بيدي مهلة (ولو الصورة chiseled بلا shell، استخدم نقطة إيقاف في التطبيق أو صورة فيها أمر sleep — 6.1.5). ولو الفاتورة الفعلية أعلى من التقدير، أول بند تفحصه: استيعاب السجلات.",
              "solution": "النتائج النموذجية: parity ✅ بين staging وprod مع diff مفاتيح فارغ، وكسر متعمد (متغير في prod فقط) بيتكشف ❌. التوسع: من نسخة إلى 4–5 نسخ خلال دقيقة تحت 50 VU مع نزول بعد دقائق (نافذة استقرار). صفر 503 أثناء `revision restart` لو الـprobes والإيقاف اللطيف مضبوطين؛ لو ظهرت 503s فغالبًا الـliveness على `/health` (بيعتمد على تبعيات) أو `ShutdownTimeout` أقصر من تصريف العمل. التكلفة: dev ~20–30 دولارًا (مع الإيقاف الليلي) · staging ~40–50 · prod ~70–100، والفرق مقابل التقدير عادةً من السجلات أو من نسخة دائمة (`minReplicas: 1`) نسيت تحسبها. التدقيق: `deployments.log` بسطر لكل نشر + تقرير شهري + issue انحراف لو `what-if` فيه فرق. التنظيف: حذف مجموعات التجارب بيوفر فورًا، وإيقاف dev بيوفر ~40–60% من تكلفته.",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/container-apps/scale-app",
                  "https://keda.sh/docs/latest/",
                  "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets",
                  "https://azure.microsoft.com/en-us/pricing/calculator/",
                  "https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs",
                  "https://k6.io/docs/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر المشروع", "items": [
            {"label": "Azure Container Apps (التوثيق الكامل)", "url": "https://learn.microsoft.com/en-us/azure/container-apps/"},
            {"label": "GitHub Actions (التوثيق)", "url": "https://docs.github.com/en/actions/"},
            {"label": "Bicep", "url": "https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/"},
            {"label": "Key Vault وManaged Identity", "url": "https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices"},
            {"label": "OIDC مع Azure من GitHub", "url": "https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure"},
            {"label": "Cost Management + الميزانيات", "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/"},
            {"label": "KEDA (التوسع بالأحداث)", "url": "https://keda.sh/docs/latest/"},
            {"label": "Google SRE Book (إدارة الحوادث وما بعدها)", "url": "https://sre.google/sre-book/table-of-contents/"},
            {"label": "Azure Well-Architected Framework", "url": "https://learn.microsoft.com/en-us/azure/well-architected/"},
            {"label": "Trivy", "url": "https://trivy.dev/latest/docs/"},
            {"label": "Cosign / Sigstore", "url": "https://docs.sigstore.dev/cosign/overview/"},
            {"label": "k6 (اختبار الحمل)", "url": "https://k6.io/docs/"},
        ]},
    ],
}

LESSONS_S6_K = [_L1]
