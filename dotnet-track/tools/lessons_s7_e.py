# -*- coding: utf-8 -*-
"""Stage 7 module 2 (part E): s7-m2-l2 (أمان سلسلة التوريد: SBOM والتوقيع والتبعيات)."""

TODAY = "2026-10-22"

_L2 = {
    "id": "s7-m2-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "أغلب الكود اللي بيشتغل في إنتاجك **مش كودك**: تبعيات NuGet، صور أساسية، أدوات بناء، actions في الـCI. أي واحدة فيهم مخترقة = إنتاجك مخترق، من غير ما تكتب سطر غلط. في 2025 صدر **OWASP Top 10:2025** وحوّل «التبعيات القديمة» لفئة كاملة اسمها **A03 Software Supply Chain Failures** — وده كان أعلى إجماع بين خبراء الأمن المشاركين. الدرس ده عملي بالكامل: **تولّد SBOM** (قائمة مكونات) لمشروع .NET وصورتك · **تفحصه** وتتعامل مع الثغرات بعقلانية (VEX) · **تحدّث التبعيات** بـDependabot من غير ما تكسر الإنتاج · **توقّع** الصور وتربطها بـ**provenance** · وتمنع في الـcluster أي صورة **ما اتوقّعتش من مستودعك**."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "SBOM", "def": "**Software Bill of Materials**: قائمة آلة القراءة بكل مكونات برنامجك (اسم · إصدار · معرّف · ترخيص · mối العلاقات). من غيرها أنت ما تعرفش إن `System.Text.Json 9.0.1` جوه صورتك لما تطلع ثغرة عليه."},
            {"term": "CycloneDX", "def": "صيغة SBOM من OWASP (الحالي 1.6) — **الأقوى للأمن**: تدعم VEX والتبعية والسلسلة. الناتج الأساسي لأدوات الفحص (Trivy/Grype/Dependency-Track)."},
            {"term": "SPDX", "def": "صيغة SBOM قياسية (ISO/IEC 5962:2021) — **الأقوى للتراخيص والامتثال**. أداة Microsoft الرسمية (`sbom-tool`) بتخرج SPDX."},
            {"term": "purl", "def": "**Package URL**: المعرّف الموحد للحزمة، مثلًا `pkg:nuget/Newtonsoft.Json@13.0.3`. هو المفتاح اللي بيطابق ثغرة بحزمة عندك — بدونه المطابقة بالاسم بس وبتخطئ."},
            {"term": "SCA", "def": "**Software Composition Analysis**: فحص التبعيات مقابل قواعد ثغرات (NVD/GHSA/OSV). بيجيب لك قائمة، مش حكم — الحكم محتاج سياق (هل الكود المتأثر بيتنادى أصلًا؟)."},
            {"term": "VEX", "def": "**Vulnerability Exploitability eXchange**: بيان قابل للتوقيع يقول: الثغرة X في المكوّن Y **لا تؤثر علينا** (not_affected) لأن… أو **تؤثر** والـstatus under_investigation. بيحوّل 200 إنذار لـ5 قرارات."},
            {"term": "Provenance", "def": "سجل موقّع يوصف **كيف اتبنى الناتج**: من أي مستودع/commit/workflow، بإيه المدخلات، ومن أي أداة بناء. الصيغة: بيان **in-toto** يحمل predicate من نوع `https://slsa.dev/provenance/v1`."},
            {"term": "SLSA", "def": "**Supply-chain Levels for Software Artifacts** (OpenSSF) — مستويات نضج للبناء. المواصفة **v1.2 (نوفمبر 2025)** فيها مسار Build (L0–L3) ومسار Source جديد. مش شهادة، بل وصف للضمانات."},
            {"term": "Sigstore", "def": "منظومة توقيع بلا مفاتيح طويلة العمر: **Fulcio** (شهادات قصيرة العمر مرتبطة بهوية OIDC) + **Rekor** (سجل شفافية عام) + **cosign** (أداة التوقيع لـOCI)."},
            {"term": "Keyless signing", "def": "التوقيع بهوية الـworkflow (OIDC من GitHub Actions) بدل مفتاح مخزّن. بينهي أعظم سبب لفشل مبادرات التوقيع: **محدش عايز يمتلك المفتاح السري**."},
            {"term": "Attestation", "def": "بيان موقّع **عن** ناتج (provenance · SBOM · نتيجة فحص) مربوط به بالـdigest. بيتخزن جنب الصورة في الـregistry أو في GitHub Attestations API."},
            {"term": "Digest مقابل Tag", "def": "`sha256:…` **غير قابل للتغيير** · `v1.2.3` مؤشر متغيّر. أي تحقق أمني لازم يكون على الـdigest — لو وقّعت tag، أي حد بصلاحيات دفع يقدر يحرّكه."},
            {"term": "Lockfile", "def": "`packages.lock.json`: النسخ **المحلولة** لكل التبعيات (بما فيها غير المباشرة). بيخلي البناء قابلًا للتكرار والـSBOM دقيقًا، وبشرط `RestoreLockedMode` ما يتغيّرش في CI بالصدفة."},
            {"term": "Typosquatting", "def": "حزمة باسم شبه حزمة مشهورة (`Newtonsott.Json` أو بحروف يونانية متشابهة). بيتماسك بفحص الأسماء في PRs وقائمة مصادر مسموحة (allowlist)."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① خريطة السلسلة: 8 مراحل و8 تهديدات"},
        {"type": "code", "lang": "text", "title": "أين يُهاجَم نظامك — من اللابتوب للإنتاج", "filename": "docs/supply-chain-map.txt", "code": r'''   ①مطوّر          ②مستودع          ③بناء (CI)              ④سجل             ⑤نشر           ⑥تشغيل
  ┌──────────┐    ┌───────────┐    ┌────────────────┐     ┌──────────┐    ┌───────────┐   ┌──────────┐
  │ لابتوب   │───▶│ Git + PR  │───▶│ Actions runner │────▶│ ACR/GHCR │───▶│ Bicep/CD  │──▶│ AKS/ACA  │
  │ مفاتيح   │    │ تبعيات    │    │ NuGet restore  │     │ صورة+SBOM│    │ (6.3.4)   │   │ النسخ    │
  │ IDE/ext  │    │ actions   │    │ publish+build  │     │ توقيع    │    │ digest    │   │ سحب      │
  └──────────┘    └───────────┘    └────────────────┘     └──────────┘     └───────────┘   └──────────┘
   تهديد:          تهديد:            تهديد:                 تهديد:           تهديد:          تهديد:
   سرقة SSH/       push مباشر        تبعيات ملوثة           tag متحرك       نشر بـlatest    سحب صورة
   PAT مسرب        على main          typosquatting          صورة بلا توقيع  بلا تحقق        غير موقعة
   امتداد IDE      actions غير       build غير معزول        SBOM ناقص       أسرار في        من مستودع
   خبيث            مثبّتة بـtag      (مفاتيح في الخطوات)                    الـmanifest     عام
   ▼               ▼                 ▼                      ▼               ▼               ▼
   إجراء:          إجراء:            إجراء:                 إجراء:          إجراء:          إجراء:
   MFA + secret    حماية فرع         lockfile +             توقيع keyless   تثبيت الـdigest admission
   scanning        + SHA pinning     RestoreLockedMode      + provenance    في manifests    policy
   للمفاتيح        + مراجعة الأسماء  + NuGetAudit           + SBOM مرتبط    + IaC review    + digest pinning
                                     + build معزول           + فحص vuln                     + pull by identity

  ⑦ التحديث المستمر: ثغرة جديدة تظهر بعد النشر بـ6 أشهر
     ▼ إجراء: SBOM مخزّن لكل إصدار + إعادة فحص دورية (مش فحص وقت البناء فقط)

  ⑧ الطرف الثالث: تبعية سحابية/مدفوعات/خرائط
     ▼ إجراء: قائمة معالجات (7.2.5) + SLA + timeout/circuit breaker (5.2.4) + خطة degrade
'''},
        {"type": "table", "caption": "التهديد × الإجراء المضاد × الأداة (استخدم الجدول ده كقائمة تنفيذ)",
         "head": ["المرحلة", "التهديد الواقعي", "الإجراء المضاد", "الأداة في مشروعنا"],
         "rows": [
             ["① مطوّر", "مفتاح/توكن مسرّب في commit أو في `.env`", "فحص أسرار في CI + pre-commit · تدوير فوري · MFA", "`gitleaks` (استخدمناه في 6.3.2) · GitHub secret scanning"],
             ["② مستودع", "تغيير مباشر على main · action خارجي محدّث تلقائيًا", "حماية فرع + مراجعة إلزامية · **تثبيت الـactions بـSHA** · مراجعة أسماء الحزم الجديدة", "branch protection · `actions/*` pinned (6.3.1)"],
             ["③ بناء", "تبعية ملوثة/typosquatting · build غير قابل للتكرار", "lockfile + `RestoreLockedMode` · `NuGetAudit` كتحذير صارم · مصدر NuGet مسموح", "`packages.lock.json` · `NuGet.Config` allowlist"],
             ["④ سجل", "صورة بلا توقيع · tag متحرك · SBOM مفقود", "توقيع keyless · provenance attestation · SBOM مربوط بالصورة · مسح ثغرات قبل الدفع", "`cosign` · `actions/attest` · `syft`/`trivy`"],
             ["⑤ نشر", "النشر بـ`latest` أو tag بدل digest", "الـmanifests بتثبيت digest · مراجعة IaC · what-if قبل التطبيق", "kustomize + digest (6.1.4) · Bicep (6.3.3)"],
             ["⑥ تشغيل", "الـcluster بيسحب أي صورة", "**admission policy**: لا تعمل صورة غير موقعة من هوية محددة · سحب بهوية (Workload Identity)", "Sigstore policy-controller / Kyverno · ACR + MI (6.2.3)"],
             ["⑦ بعد النشر", "ثغرة تُكتشف في تبعية قديمة", "SBOM مخزّن لكل إصدار + **إعادة فحص دورية** + سياسة تحديث خلال N يومًا للـcritical", "Dependency-Track أو `trivy sbom` مجدول"],
             ["⑧ طرف ثالث", "تبعية سحابية تقع أو تتغير شروطها", "قائمة معالجات · timeout + circuit breaker · مسار degrade · اختبار فشل التبعية", "Polly (5.2.4) · feature flags (7.2.1)"],
         ]},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② SBOM لمشروع .NET: توليد وفحص"},
        {"type": "code", "lang": "bash", "title": "scripts/sbom.sh — ولّد SBOM للتطبيق وللصورة، وافحص الاتنين", "filename": "scripts/sbom.sh", "code": r'''#!/usr/bin/env bash
# يولّد SBOM بصيغتين من البناء الفعلي + صورة، ثم يفحص الثغرات في الاتنين.
# المتطلبات: dotnet 10 SDK · docker · syft · trivy · cyclonedx-cli (اختياري للتحقق)
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/shop/orders-api:2.9.0}"
OUT="${OUT:-artifacts/sbom}"
mkdir -p "$OUT"

echo "== 1) ثبّت الأدوات (مرة واحدة) =="
dotnet tool install --global CycloneDX || dotnet tool update --global CycloneDX
dotnet tool install --global Microsoft.Sbom.DotNetTool || true

echo "== 2) بناء بإخراج lockfile (شرط لـSBOM دقيق) =="
dotnet restore src/Orders.Api/Orders.Api.csproj
dotnet publish src/Orders.Api/Orders.Api.csproj -c Release -o "$OUT/publish"

echo "== 3) CycloneDX للتطبيق (JSON · غير مباشر · بلا تبعيات تطوير/اختبار) =="
# الأوامر: -j = JSON · -rs = فحص المشاريع المرجعية · -d = استبعاد dev dependencies
# -t = استبعاد مشاريع الاختبار · --set-name/--set-version = هوية المكوّن الجذر
dotnet-CycloneDX src/Orders.Api/Orders.Api.csproj \
  -o "$OUT" -f orders-api.cdx.json -j -rs -d -t \
  --set-name "Shop.Orders.Api" --set-version "${VERSION:-2.9.0}"

echo "== 4) SPDX من أداة Microsoft (لطلبات التراخيص/العملاء) =="
sbom-tool generate -b "$OUT/publish" -bc src/Orders.Api \
  -pn "Shop.Orders.Api" -pv "${VERSION:-2.9.0}" -ps "Shop" \
  -m "$OUT" || echo "sbom-tool فشل — استخدم CycloneDX فقط (تحقق من إصدار الأداة)"

echo "== 5) SBOM للصورة نفسها (بيشمل الأساس + الحزم النظامية) =="
syft "$IMAGE" -o cyclonedx-json="$OUT/image.cdx.json"

echo "== 6) افحص الثغرات في SBOM (مش في الصورة — أسرع ويعيد فحص الإصدارات القديمة) =="
trivy sbom "$OUT/orders-api.cdx.json" --severity HIGH,CRITICAL --format table
trivy sbom "$OUT/image.cdx.json"    --severity HIGH,CRITICAL --format table

echo "== 7) افحص الصورة كاملة (vuln + secrets + misconfig) =="
trivy image "$IMAGE" --scanners vuln,secret,misconfig \
  --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 --format table

echo "== 8) تدقيق NuGet الأصلي (يشتغل من غير أدوات خارجية) =="
dotnet list src/Orders.Api/Orders.Api.csproj package --vulnerable --include-transitive || true
dotnet list src/Orders.Api/Orders.Api.csproj package --deprecated || true

echo "== 9) تحقق من صلاحية الصيغة (اختياري) =="
if command -v cyclonedx-cdx >/dev/null 2>&1; then
  cyclonedx-cdx validate --input-file "$OUT/orders-api.cdx.json" --input-format json
fi

echo "تم ✅ — الناتج في $OUT (ارفعه مع الإصدار، واحتفظ به لكل إصدار)"
'''},
        {"type": "code", "lang": "xml", "title": "Directory.Build.props — اجعل البناء قابلًا للتكرار والتدقيق افتراضيًا", "filename": "Directory.Build.props", "code": r'''<Project>
  <PropertyGroup>
    <!-- 1) قفل النسخ: SBOM دقيق + بناء متطابق + كاش NuGet في CI (6.3.1) -->
    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
    <RestoreLockedMode Condition="'$(CI)' == 'true'">true</RestoreLockedMode>
    <NuGetAudit>true</NuGetAudit>
    <!-- direct = الحزم المباشرة فقط · all = تشمل غير المباشرة (أدق وأضجّ) -->
    <NuGetAuditMode>all</NuGetAuditMode>
    <NuGetAuditLevel>moderate</NuGetAuditLevel>

    <!-- 2) هوية ثابتة للبناء: تُستخدم في provenance وفي SBOM -->
    <VersionPrefix Condition="'$(VersionPrefix)' == ''">0.0.0</VersionPrefix>
    <InformationalVersion Condition="'$(GIT_SHA)' != ''">$(VersionPrefix)+$(GIT_SHA)</InformationalVersion>

    <!-- 3) حتمية: نفس المصدر + نفس الأدوات = نفس البايتات (يسهّل التحقق) -->
    <Deterministic>true</Deterministic>
    <ContinuousIntegrationBuild Condition="'$(CI)' == 'true'">true</ContinuousIntegrationBuild>
    <EmbedUntrackedSources>false</EmbedUntrackedSources>
    <InvariantGlobalization>false</InvariantGlobalization>
  </PropertyGroup>
</Project>
'''},
        {"type": "callout", "kind": "warn", "title": "أربعة أخطاء بتخلي الـSBOM بلا قيمة",
         "md": "**① توليده من شجرة المصدر بدل الناتج المبني** — كده بيفوتك الحزم اللي دخلت الصورة فعلًا وأساس الصورة نفسه. ولّد من `bin/Release` أو من الصورة (بـ`syft`).\n**② نسيان الأساس والنظام** — SBOM التطبيق ما يقولش إن الصورة فيها `openssl` أو `libssl3`. عشان كده لازم **SBOM للصورة** بالإضافة للتطبيق.\n**③ فحص مرة واحدة وقت البناء** — الثغرات بتُكتشف بعد شهور. خزّن الـSBOM لكل إصدار وأعد فحصه دوريًا (Dependency-Track أو `trivy sbom` مجدول أسبوعيًا).\n**④ إنذار بلا قرار** — 200 ثغرة بدون VEX = الفريق بيتجاهل التقرير كله. اكتب **قرارًا لكل ثغرة**: not_affected / scheduled / accepted."},
        {"type": "table", "caption": "CycloneDX مقابل SPDX — ومتى تخرج الاتنين",
         "head": ["الجانب", "CycloneDX", "SPDX"],
         "rows": [
             ["الجهة", "OWASP", "Linux Foundation (ISO/IEC 5962:2021)"],
             ["الأقوى في", "**الأمن**: ثغرات · VEX · تبعية · سلسلة توريد", "**التراخيص والامتثال**: عقود · عملاء · مشتريات"],
             ["الأدوات في .NET", "`dotnet-CycloneDX` · `syft` · `trivy` · Dependency-Track", "`Microsoft.Sbom.DotNetTool` · `Microsoft.Sbom.Targets` · `syft`"],
             ["صيغة الملف", "`bomFormat: CycloneDX`, `specVersion: 1.6`", "`spdxVersion: SPDX-2.3` (و3.0 الجديد)"],
             ["التوقيع داخل المستند", "يدعم توقيع المستند وإصداره داخليًا", "يعتمد على توقيع/ملف خارجي، وله `NOASSERTION` للمجهول"],
             ["قرارنا", "**الأساسي** للفحص والأتمتة", "نسخة إضافية عند طلب عميل/مشتريات"],
         ]},
        {"type": "callout", "kind": "note", "title": "العناصر الدنيا للـSBOM (اسأل عنها أي مورد)",
         "md": "أي SBOM مفيد لازم يقول: **اسم المورد** (مش اسم الأداة) · **اسم المكوّن** · **إصداره** · **معرّف واحد على الأقل** (purl/CPE) · **العلاقات** (من يعتمد على من) · **توقيت الإنشاء** · **أداة الإنشاء وإصدارها** · **هوية المستند وإصداره** · **والتصريح بالمجهول صراحةً** بدل اختراع قيمة. CISA بتحدّث قائمة «العناصر الدنيا» دوريًا (تحديث 2026 أضاف حقول زي سياق الإنشاء وإصدار الصيغة) — **تحقق من النسخة الحالية قبل ما تكتب سياسة مشتريات**. وللمكتبات اللي بتنتجها: `Microsoft.Sbom.Targets` مع `<GenerateSBOM>true</GenerateSBOM>` بيضمّن SPDX داخل الـ`.nupkg` نفسه."},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ التحديثات: Dependabot من غير ما يكسر الإنتاج"},
        {"type": "code", "lang": "yaml", "title": ".github/dependabot.yml — ثلاث منظومات + مجموعات + استثناءات", "filename": ".github/dependabot.yml", "code": r'''version: 2
registries:
  # لو عندك حزم خاصة (5.1/6.1) — عرّفها هنا عشان التحديثات تشتغل
  nuget-shop:
    type: nuget-feed
    url: https://nuget.pkg.github.com/shop/index.json
    username: ${{ secrets.PKG_USER }}
    password: ${{ secrets.PKG_TOKEN }}

updates:
  # ── 1) تبعيات .NET ─────────────────────────────────────────
  - package-ecosystem: nuget
    directory: "/"
    schedule:
      interval: weekly
      day: saturday            # تحديثات في وقت منخفض الحركة
      time: "06:00"
    open-pull-requests-limit: 10
    registries: ["nuget-shop"]
    labels: ["dependencies", "security"]
    groups:
      # تجميع التحديثات الصغيرة في PR واحد = ضجيج أقل ومراجعة أسرع
      dotnet-minor-patch:
        update-types: ["minor", "patch"]
      otel:
        patterns: ["OpenTelemetry*"]
      efcore:
        patterns: ["Microsoft.EntityFrameworkCore*"]
    ignore:
      # لا نرفع إصدارًا رئيسيًا تلقائيًا: قرار معماري يُراجع يدويًا
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
      # مثال: ثبّت حزمة لسبب معروف واكتب السبب في التعليق
      - dependency-name: "MassTransit"
        versions: ["9.x"]

  # ── 2) أفعال GitHub: ثبّت بالـSHA وراجع التحديثات ───────────
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels: ["ci", "security"]
    # Dependabot بيقترح التثبيت بـSHA؛ لا تقبل تحديث tag عائم (6.3.1)

  # ── 3) الصور الأساسية في Dockerfiles ─────────────────────────
  - package-ecosystem: docker
    directory: "/src"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels: ["containers", "security"]
    # يراقب سطر FROM: تحديث mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled
'''},
        {"type": "code", "lang": "bash", "title": "scripts/dependency-audit.sh — بوابة أسبوعية للثغرات (CI + cron)", "filename": "scripts/dependency-audit.sh", "code": r'''#!/usr/bin/env bash
# يقرر: هل نوقف النشر؟ القاعدة:
#   critical/high لها إصلاح متاح (fixable)  -> فشل (exit 1)
#   critical/high بلا إصلاح + بلا VEX       -> تحذير + تذكرة
#   moderate/low                            -> تقرير فقط
set -euo pipefail

REPORT="${REPORT:-artifacts/security/trivy.json}"
mkdir -p "$(dirname "$REPORT")"

echo "== مسح التبعيات والصورة =="
trivy fs . --scanners vuln --severity HIGH,CRITICAL --format json --output "$REPORT" || true

# عدّ الثغرات القابلة للإصلاح
FIXABLE=$(jq '[.Results[]?.Vulnerabilities[]? | select(.FixedVersion != null and .FixedVersion != "")] | length' "$REPORT" 2>/dev/null || echo 0)
UNFIXED=$(jq '[.Results[]?.Vulnerabilities[]? | select(.FixedVersion == null or .FixedVersion == "")] | length' "$REPORT" 2>/dev/null || echo 0)

echo "قابلة للإصلاح: $FIXABLE · بلا إصلاح: $UNFIXED"

echo "== قائمة القابلة للإصلاح (دي اللي بنوقف عليها النشر) =="
jq -r '.Results[]?.Vulnerabilities[]?
  | select(.FixedVersion != null and .FixedVersion != "")
  | "\(.Severity)\t\(.PkgName)\t\(.InstalledVersion) -> \(.FixedVersion)\t\(.VulnerabilityID)"' "$REPORT" 2>/dev/null | sort -u

echo "== بلا إصلاح: تحتاج VEX أو تذكرة =="
jq -r '.Results[]?.Vulnerabilities[]?
  | select(.FixedVersion == null or .FixedVersion == "")
  | "\(.Severity)\t\(.PkgName)\t\(.VulnerabilityID)"' "$REPORT" 2>/dev/null | sort -u

if [[ "${FIXABLE:-0}" -gt 0 ]]; then
  echo "✗ توجد ثغرات عالية/حرجة بإصلاح متاح — حدّث قبل النشر."
  exit 1
fi
echo "✓ لا توجد ثغرات عالية بإصلاح متاح."
'''},
        {"type": "callout", "kind": "tip", "title": "VEX: حوّل الضجيج لقرار مكتوب (مثال حقيقي)",
         "md": "لما يطلع إنذار على `Newtonsoft.Json 13.0.3` وأنت **لا تستخدم مسار deserialization المتأثر**، اكتب بيان VEX موقّع بدل ما تتجاهله صامتًا — كده الفحص الجاي بيعرف إن ده قرار مش إهمال:\n\n```json\n{\n  \"bomFormat\": \"CycloneDX\",\n  \"specVersion\": \"1.6\",\n  \"vulnerabilities\": [{\n    \"id\": \"GHSA-5crp-9r3c-p9vr\",\n    \"analysis\": {\n      \"state\": \"not_affected\",\n      \"justification\": \"vulnerable_code_not_in_execute_path\",\n      \"detail\": \"التطبيق لا يستدعي JsonConvert.DeserializeObject على مدخلات خارجية؛ كل القراءة عبر System.Text.Json.\"\n    }\n  }]\n}\n```\n\nالقواعد: **الحالة مش رأي** (`not_affected` لازم بتبرير مكتوب + دليل) · **VEX بيتراجع** كل ربع سنة · **ممنوع `not_affected` لثغرة critical بلا اختبار يثبت إن المسار مش مستخدم** · خليه ملف في الريبو (`security/vex.cdx.json`) عشان يمر على المراجعة زي الكود."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ التوقيع والـprovenance: بلا مفاتيح"},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/release.yml — بناء + توقيع + provenance + SBOM attestation", "filename": ".github/workflows/release.yml", "code": r'''name: release
on:
  push:
    tags: ["v*"]

env:
  REGISTRY: ghcr.io
  IMAGE: shop/orders-api

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write          # OIDC -> شهادة Sigstore قصيرة العمر
      attestations: write      # حفظ الـattestation
      artifact-metadata: write # سجل تخزين الناتج
    outputs:
      digest: ${{ steps.buildx.outputs.digest }}
      version: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v5          # ثبّت بالـSHA في مشروعك الحقيقي (6.3.1)

      - uses: actions/setup-dotnet@v5
        with:
          dotnet-version: 10.0.x
          cache: true                      # يتطلب packages.lock.json

      - name: Restore (locked)
        run: dotnet restore --locked-mode

      - name: Test + security gate
        run: |
          dotnet test -c Release --collect:"XPlat Code Coverage"
          ./scripts/dependency-audit.sh

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE }}

      - id: buildx
        name: Build & push (by digest)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: src/Orders.Api/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            VERSION=${{ github.ref_name }}
            GIT_SHA=${{ github.sha }}
          # لا ننشر بـlatest وحده: الـdigest هو الهوية
          outputs: type=image,push=true

      # ── SBOM من الصورة المبنية (مش من المصدر) ─────────────────
      - name: Generate SBOM (CycloneDX from image)
        uses: anchore/sbom-action@v0
        with:
          image: ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.buildx.outputs.digest }}
          format: cyclonedx-json
          output-file: sbom.cdx.json
          upload-artifact: false

      # ── 1) provenance (SLSA build) ────────────────────────────
      - name: Attest build provenance
        uses: actions/attest@v4
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          subject-digest: ${{ steps.buildx.outputs.digest }}
          push-to-registry: true

      # ── 2) attestation للـSBOM نفسه ───────────────────────────
      - name: Attest SBOM
        uses: actions/attest@v4
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          subject-digest: ${{ steps.buildx.outputs.digest }}
          sbom-path: sbom.cdx.json
          push-to-registry: true

      # ── 3) توقيع cosign keyless (بديل/مكمّل للـattestations) ──
      - name: Sign image with cosign (keyless)
        uses: sigstore/cosign-installer@v3
      - run: |
          cosign sign --yes \
            ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.buildx.outputs.digest }}

      - name: Attach the SBOM as a cosign attestation
        run: |
          cosign attest --yes \
            --predicate sbom.cdx.json --type cyclonedx \
            ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.buildx.outputs.digest }}

      # ── احتفظ بالـSBOM عندك: بيانات تشغيل Actions محدودة المدة ──
      - name: Archive SBOM + provenance
        uses: actions/upload-artifact@v4
        with:
          name: sbom-${{ github.ref_name }}
          path: sbom.cdx.json
          retention-days: 400
'''},
        {"type": "code", "lang": "bash", "title": "deploy/verify-image.sh — تحقق قبل ما تنشر (مش بعد)", "filename": "deploy/verify-image.sh", "code": r'''#!/usr/bin/env bash
# يتحقق من هوية الصورة وسلامة بنائها قبل النشر.
# القاعدة: التحقّق بالـdigest، وتثبيت الهوية (repo + workflow) لا المصدر وحده.
set -euo pipefail

REPO="shop/orders-api"                       # org/name كما في GHCR
IMAGE="ghcr.io/${REPO}"
DIGEST="${1:?استخدم: verify-image.sh sha256:...}"
SIGNER_WORKFLOW="shop/orders-api/.github/workflows/release.yml"
OIDC_ISSUER="https://token.actions.githubusercontent.com"

echo "== 1) تحقق من attestation عبر GitHub CLI =="
gh attestation verify "oci://${IMAGE}@${DIGEST}" --repo "${REPO}"

echo "== 2) تحقق من التوقيع مع تثبيت الهوية (ليس المصدر وحده) =="
# --certificate-identity-regexp يثبت أي workflow في هذا المستودع؛
# للتحديد الأدق استخدم --certificate-identity مع مسار الـworkflow والـref.
cosign verify \
  --certificate-identity-regexp "^https://github.com/${REPO}/\.github/workflows/release\.yml@refs/tags/v.*" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}@${DIGEST}"

echo "== 3) تحقق من attestation الـprovenance واستخرج الحمولة =="
# النوع slsaprovenance1 = predicate من SLSA v1 (ما تخرجه GitHub artifact attestations)
# النوع slsaprovenance  = predicate v0.2 (مولّدات أقدم)
cosign verify-attestation --type slsaprovenance1 \
  --certificate-identity-regexp "^https://github.com/${REPO}/" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}@${DIGEST}" \
  | jq -r '.payload' | base64 -d | jq '.predicate.buildDefinition, .predicate.runDetails.builder'

echo "== 4) تحقق من attestation الـSBOM وافحصه فورًا =="
cosign verify-attestation --type cyclonedx \
  --certificate-identity-regexp "^https://github.com/${REPO}/" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}@${DIGEST}" \
  | jq -r '.payload' | base64 -d > /tmp/sbom.cdx.json
trivy sbom /tmp/sbom.cdx.json --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1

echo "✓ الصورة مقبولة: ${IMAGE}@${DIGEST}"
'''},
        {"type": "table", "caption": "مستويات SLSA Build (v1.2 — نوفمبر 2025): إيه اللي بيثبت وكل مستوى",
         "head": ["المستوى", "المتطلب الأساسي", "بيحمي من", "كيف تصله على GitHub Actions", "ما لا يغطيه"],
         "rows": [
             ["**L0**", "لا متطلبات", "—", "الوضع الافتراضي بلا provenance", "كل حاجة"],
             ["**L1**", "provenance موجود ومتاح للمستهلك", "الأخطاء العرضية · غياب قابلية التدقيق", "خطوة تولّد بيان in-toto (غير موقّع)", "التزوير — أي حد يقدر يكتب بيانًا"],
             ["**L2**", "provenance **موقّع من منصة بناء مستضافة** + المستأجرون ما يقدروش يغيروا محتواه", "تزوير الـprovenance · العبث بعد البناء", "`actions/attest` مع `id-token: write` (توقيع Sigstore بهوية الـworkflow)", "منصة البناء نفسها · بناء على runner ذاتي الاستضافة"],
             ["**L3**", "البناء **معزول** ومادة التوقيع **لا يمكن** لخطوات المستخدم الوصول إليها", "اختراق بنية البناء · تزوير من مستأجرين آخرين", "توليد الـattestation داخل **reusable workflow** مشترك بين المستودعات + تثبيت الموقّع بـ`gh attestation verify --signer-workflow`", "صحة المصدر نفسه · ثغرات الكود · سلاسل التبعية وقت التشغيل"],
         ]},
        {"type": "callout", "kind": "danger", "title": "تغييرات 2026 اللي لازم تعرفها (وفخاخ شائعة)",
         "md": "**① `slsa-framework/slsa-github-generator` بقى غير مُصان نشطًا (أعلنوا ده في 7 أغسطس 2026)** — التوجيه الحالي هو **GitHub artifact attestations** (`actions/attest`). متبنيش عليه workflow جديد.\n**② `actions/attest-build-provenance` من الإصدار 4 بقى مجرد غلاف على `actions/attest`** — الاستخدام الجديد: `actions/attest` (بيدعم provenance · SBOM · custom predicate).\n**③ التوافر**: الـattestations متاحة في المستودعات **العامة** على كل الخطط الحالية، وفي الخاصة/الداخلية محتاجة **GitHub Enterprise Cloud** — ومش مدعومة على GitHub Enterprise Server.\n**④ المستودعات الخاصة** بتستخدم نسخة Sigstore الخاصة بـGitHub **بدون سجل شفافية عام** — يعني التحقق مربوط بهوية GitHub بس.\n**⑤ الاحتفاظ**: GitHub قلّل مدة الاحتفاظ ببيانات تشغيل Actions (changelog يوليو 2026) — **أرشِف الـSBOM والـprovenance في تخزينك** لكل إصدار، ما تعتمدش على صفحة الـrun.\n**⑥ الأهم**: التحقق بالتوقيع **وحده بلا قيمة** لو ما ثبتّش الهوية: قبول أي شهادة من `token.actions.githubusercontent.com` معناه قبول أي مستودع على GitHub. ثبّت **المستودع والـworkflow** (ولـL3 مسار الـreusable workflow)."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ المنع عند الإدخال: لا تشغّل صورة ما اتوقعتش"},
        {"type": "text", "md": "التوقيع في الـCI نصف الشغل. النصف الثاني: **الـcluster يرفض** أي صورة ما اجتازتش التحقق — وإلا أي حد بصلاحيات نشر يقدر يتجاوز كل ده. ده اسمه **admission policy** وبيتنفذ بـadmission controller (webhook) بيفحص طلب إنشاء الـPod قبل ما يبدأ."},
        {"type": "code", "lang": "yaml", "title": "deploy/policy/cluster-image-policy.yaml — Sigstore policy-controller", "filename": "deploy/policy/cluster-image-policy.yaml", "code": r'''# policy-controller (Sigstore): يرفض أي Pod صورته غير مستوفية للسياسة.
# التثبيت: helm install policy-controller sigstore/policy-controller -n cosign-system
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-signed-shop-images
spec:
  images:
    # السياسة تنطبق على سجلنا فقط (لا تكسر صور النظام)
    - glob: "ghcr.io/shop/**"
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          # تثبيت الهوية: هذا المستودع بالذات، وهذا الـworkflow بالذات
          - issuer: https://token.actions.githubusercontent.com
            subjectRegExp: "^https://github\\.com/shop/orders-api/\\.github/workflows/release\\.yml@refs/tags/v.*$"
      # اشترط attestation للـprovenance (مش توقيعًا فقط)
      attestations:
        - name: must-have-slsa-provenance
          predicateType: https://slsa.dev/provenance/v1
        - name: must-have-sbom
          predicateType: https://spdx.dev/Document
---
# استثناء الأدوات الموثوقة (monitoring/ingress) — بلا استثناءات هتعطّل الـcluster كله
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: allow-known-vendors
spec:
  images:
    - glob: "mcr.microsoft.com/**"
    - glob: "registry.k8s.io/**"
    - glob: "ghcr.io/open-telemetry/**"
  authorities:
    - keyless: {}     # تحقق من التوقيع إن وُجد، وإلا اقبل من هذه السجلات
'''},
        {"type": "callout", "kind": "warn", "title": "اختيار أداة الـadmission (تحقق من إصدارك)",
         "md": "فيه أكتر من تنفيذ، والـAPI بيتطور:\n\n• **Sigstore policy-controller** — `ClusterImagePolicy` (المستخدم أعلاه) · مبني خصيصًا لـSigstore · بيدعم اشتراط attestations بسياسات CUE/Rego.\n• **Kyverno** — عنده تحقق من الصور؛ في الإصدارات الحديثة (1.13+) التحقق اتنقل لـ`spec.validate[].imageVerifier` في `ClusterPolicy`، و1.15 أضاف نوع `ImageValidatingPolicy`. **لا تنسخ YAML من مقال قديم — اقرأ توثيق إصدارك المثبت**.\n• **Azure**: لو على AKS، فيه تكامل مُدار للتحقق من الصور/التوقيعات — راجع خيارات AKS الحالية بدل ما تبني webhook بنفسك.\n\nقاعدة تشغيلية مهمة: **طبّق السياسة في وضع audit الأول** (تسجل المخالفات بدون رفض) لمدة أسبوع، وبعدين اقلبها لـenforce. الانتقال المباشر للرفض بيكسر النشر في نص الليل."},
        {"type": "table", "caption": "سبعة أخطاء بتخلي سلسلة التوريد شكلها مؤمّنة وهي مش كده",
         "head": ["#", "الخطأ", "ليه خطر", "الصحيح"],
         "rows": [
             ["1", "التحقق بالتوقيع **بدون تثبيت الهوية**", "بيقبل أي صورة موقعة من أي مستودع على GitHub", "`--certificate-identity-regexp` يثبت المستودع والـworkflow + الـissuer"],
             ["2", "النشر والتحقق بالـ**tag**", "الـtag مؤشر متحرك: يتغير من غير ما يتغير الناتج", "كل حاجة بالـdigest `@sha256:…` في الـmanifests والتوقيع والتحقق"],
             ["3", "مفتاح توقيع مخزّن في secret للـworkflow", "أي اختراق للـCI = مفتاح التوقيع · وبيتحول لـ«محدش مسؤول عنه»", "keyless بـOIDC + Fulcio (شهادة قصيرة العمر) + Rekor"],
             ["4", "SBOM من **شجرة المصدر** مرة واحدة", "بيفوّت أساس الصورة والحزم النظامية · وبيتقادم", "SBOM للصورة المبنية بالـdigest + أرشفة لكل إصدار + إعادة فحص دورية"],
             ["5", "Dependabot مفعّل لكن **الـPRs مقفولة**", "تحديثات أمان متراكمة = ثغرة معروفة ومتاحة الاستغلال لأسابيع", "مجموعات (groups) لتقليل العدد + سياسة زمنية: critical خلال 48 ساعة"],
             ["6", "رفع الإصدارات الرئيسية تلقائيًا", "EF Core/ASP.NET major = تغييرات سلوك تكسر الإنتاج", "ignore لـsemver-major + ترقية مجدولة مع اختبار كامل (6.3.3 expand/contract)"],
             ["7", "فحص الثغرات في CI **فقط** بلا بوابة", "التقرير بيتولد ومحدش بيقراه", "`--exit-code 1` على القابل للإصلاح + VEX مكتوب للباقي + مسؤولية واضحة"],
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أقدر أشرح الفرق بين **SBOM** (ماذا بداخله) و**provenance** (كيف اتبنى) و**VEX** (هل الثغرة تؤثر فعلًا).",
            "أولّد CycloneDX لتطبيق .NET وSPDX للصورة، وأعرف ليه لازم **الاتنين**.",
            "أعرف العناصر الدنيا لأي SBOM مفيد، وأميّز «مجهول مصرَّح به» من «قيمة مخترعة».",
            "أضبط lockfile + `RestoreLockedMode` + `NuGetAudit` وأشرح أثر كل واحد.",
            "أكتب `dependabot.yml` بثلاث منظومات مع مجموعات واستثناء للإصدارات الرئيسية.",
            "أوقّع صورة keyless وأربطها بـprovenance وSBOM attestation، وأتحقق منها **بالـdigest** مع تثبيت الهوية.",
            "أعرف مستويات SLSA Build L1/L2/L3 وإزاي أصل لـL3 (reusable workflow) — وأعرف إن `slsa-github-generator` بقى غير مُصان.",
            "أمنع في الـcluster تشغيل أي صورة غير موقعة من هويتي، وأطبّق السياسة في وضع audit أولًا.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على سلسلة التوريد.",
         "questions": [
             {"q": "ثغرة حرجة اتعلنت في `Newtonsoft.Json 13.0.3` الموجودة في SBOM مشروعك. ما أول إجراء صحيح؟",
              "options": ["تجاهلها لأنها transitive dependency",
                          "تحديد هل الكود المتأثر مستخدم فعلًا، ثم التحديث لو فيه نسخة مُصلحة أو كتابة VEX مبرر",
                          "حذف الحزمة من المشروع فورًا",
                          "تعطيل الفحص حتى تصدر نسخة جديدة"],
              "answer": 1,
              "explain": "الـSBOM بيجاوب «إيه اللي عندي»، والقرار محتاج سياق: هل المسار المتأثر بيتنفذ؟ لو فيه إصلاح → حدّث واختبر. لو مفيش إصلاح والمسار مش مستخدم → اكتب VEX بحالة not_affected مع تبرير ودليل. التجاهل الصامت = نفس النتيجة بس من غير سجل قرار."},
             {"q": "ليه لازم تولّد SBOM للصورة المبنية بالإضافة للتطبيق؟",
              "options": ["لأن SBOM التطبيق غير دقيق",
                          "لأن الصورة تحتوي حزم نظامية وأساس runtime لا يظهران في تبعيات NuGet",
                          "لأن الصيغتين مختلفتان",
                          "لأنه مطلوب قانونيًا دائمًا"],
              "answer": 1,
              "explain": "SBOM التطبيق بيقول الحزم من `packages.lock.json`. لكن الصورة فيها `mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled` وفيه `libssl3`/`openssl` — وثغرات الأساس دي أكتر اللي بيحصل. عشان كده `syft <image>` بالإضافة لـ`dotnet-CycloneDX`."},
             {"q": "ما الفرق العملي بين توقيع بـkeyless (Sigstore/Fulcio) ومفتاح مخزّن في GitHub secret؟",
              "options": ["لا فرق، الاتنين تشفير",
                          "keyless يربط التوقيع بهوية الـworkflow بشهادة قصيرة العمر، فلا يوجد مفتاح طويل العمر يُسرق أو يحتاج تدويرًا",
                          "keyless أبطأ لكن أكثر أمانًا في النقل",
                          "المفتاح المخزّن مطلوب للمستودعات العامة فقط"],
              "answer": 1,
              "explain": "keyless بينهي مشكلتين: مفيش سر طويل العمر يُسرق/يتسرب، والهوية الموقعة هي الـworkflow نفسه (repo + ref) فالتحقق بيثبت **مين بنى** مش بس **إن حد وقّع**.والثمن إن التحقق محتاج تثبيت الهوية (subjectRegExp) — وإلا قبلت أي مستودع."},
             {"q": "`cosign verify --certificate-oidc-issuer https://token.actions.githubusercontent.com` فقط. ما المشكلة؟",
              "options": ["الـissuer خطأ",
                          "يقبل أي صورة بُنيت بأي workflow على GitHub — لازم تثبيت الهوية (المستودع/الـworkflow)",
                          "لا يعمل مع الصور",
                          "يحتاج مفتاح عام إضافي"],
              "answer": 1,
              "explain": "الـissuer وحده معناه «أي مستودع على GitHub Actions». أضف `--certificate-identity` أو `--certificate-identity-regexp` لتثبيت مستودعك والـworkflow والـref. القاعدة: **التوقيع بلا تثبيت هوية = بلا قيمة**."},
             {"q": "إيه اللي بيخلي بناءك SLSA Build L3 بدل L2؟",
              "options": ["توقيع الصورة بـcosign",
                          "وجود SBOM مرفق",
                          "عزل البناء بحيث مادة التوقيع لا يمكن لخطوات المستخدم الوصول إليها — عمليًا توليد الـprovenance داخل reusable workflow",
                          "استخدام runner أسرع"],
              "answer": 2,
              "explain": "L2 = provenance موقّع من منصة مستضافة. L3 بيضيف **العزل وعدم القابلية للتزوير**: خطوات البناء بتاعتك ما تقدرش توصل لمادة التوقيع. على GitHub ده بيتحقق بتوليد الـattestation داخل reusable workflow مشترك، والتحقق بـ`gh attestation verify --signer-workflow`."},
             {"q": "`packages.lock.json` + `RestoreLockedMode=true` في CI بيحققوا إيه؟",
              "options": ["تسريع البناء فقط",
                          "بناء قابل للتكرار: النسخ محلولة ومثبتة، فلا تدخل حزمة جديدة أو إصدار مختلف بدون تغيير صريح في الـlockfile",
                          "تشفير الحزم",
                          "منع استخدام الحزم الخاصة"],
              "answer": 1,
              "explain": "الـlockfile بيسجّل النسخ المحلولة (بما فيها غير المباشرة)، و`RestoreLockedMode` بيفشل البناء لو القفل محتاج تعديل. ده شرطين: **SBOM دقيق** (نفس النسخ اللي اتبنت) و**منع دخول تبعية جديدة بالصدفة** عبر تحديث transitive. وكمان شرط كاش `setup-dotnet` في CI (6.3.1)."},
             {"q": "أفضل طريقة لتقليل ضجيج PRs التحديثات من غير ما تفقد التغطية الأمنية؟",
              "options": ["تعطيل Dependabot",
                          "رفع `open-pull-requests-limit` إلى 100",
                          "مجموعات (groups) للـminor/patch + تجاهل الإصدارات الرئيسية + سياسة زمنية للـcritical",
                          "قبول كل التحديثات تلقائيًا"],
              "answer": 2,
              "explain": "المجموعات بتجمع تحديثات minor/patch في PR واحد (ضجيج أقل ومراجعة أسرع)، والإصدارات الرئيسية قرار معماري يُراجع يدويًا، والـcritical له مهلة قصيرة. القبول التلقائي بيكسر الإنتاج لأن التحديث الأمني ممكن يكون breaking."},
             {"q": "طبّقت ClusterImagePolicy بوضع enforce فورًا، وفشل نشر كل الصور بما فيها monitoring. السبب الأرجح؟",
              "options": ["الـcluster لا يدعم السياسات",
                          "الـglob كان أوسع من سجلنا فطبق السياسة على صور موردين لا نوقعها",
                          "cosign غير مثبت",
                          "الـSBOM ناقص"],
              "answer": 1,
              "explain": "الغلط النموذجي: glob بلا حدود أو سياسة عامة بلا استثناءات للسجلات الموثوقة (mcr.microsoft.com · registry.k8s.io). الصح: حصر السياسة في `ghcr.io/shop/**` + سياسات استثناء للموردين + **وضع audit أولًا** لمدة أسبوع لمراقبة المخالفات قبل الرفض."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "SBOM مفحوص + سلسلة توقيع وتحقق كاملة.",
         "items": [
            {"id": "s7-m2-l2-t1",
             "title": "مهمة 1: SBOM مزدوج + بوابة ثغرات + قرارات VEX",
             "md": "على مشروعك (Shop أو أي مشروع .NET حقيقي عندك): فعّل الـlockfile و`NuGetAudit` في `Directory.Build.props`، وولّد **CycloneDX للتطبيق** و**CycloneDX للصورة**، وافحص الاتنين بـTrivy، واكتب بوابة CI ترفض الثغرات القابلة للإصلاح. ثم اتخذ **قرارًا مكتوبًا** لكل ثغرة متبقية (تحديث / VEX / تذكرة).",
             "criteria": [
                 "`Directory.Build.props` فيه `RestorePackagesWithLockFile` + `RestoreLockedMode` في CI + `NuGetAudit`/`NuGetAuditMode`/`NuGetAuditLevel`، مع `packages.lock.json` مُلتزم في الريبو.",
                 "ملفا SBOM مولّدان: `orders-api.cdx.json` (من التطبيق) و`image.cdx.json` (من الصورة) — مع **مقارنة عدد المكونات** في كل واحد وتفسير الفرق (أساس الصورة + الحزم النظامية).",
                 "بوابة CI (`dependency-audit.sh` أو مكافئ) تفشل عند وجود ثغرة HIGH/CRITICAL **لها إصلاح متاح**، مع مخرجات مفهومة (الحزمة · الإصدار · الهدف · المعرّف).",
                 "**جدول قرارات**: لكل ثغرة متبقية → الحالة (fix / not_affected / risk_accepted) · التبرير · الدليل · المالك · تاريخ المراجعة التالية.",
                 "ملف VEX واحد على الأقل (`security/vex.cdx.json`) بحالة `not_affected` وتبرير **مدعوم بدليل** (اختبار/مسار كود) — مش رأي.",
                 "إعادة فحص مجدولة (cron أسبوعي) تعيد فحص SBOM الإصدارات المنشورة، مش فقط البناء الجديد.",
             ],
             "hint": "لو `syft`/`trivy` مش مثبتين: `brew install syft trivy` أو حمّل binary من Releases، أو استخدم صورهم في CI (`aquasec/trivy`). ولو عايز نتيجة سريعة من غير أدوات: `dotnet list package --vulnerable --include-transitive` بيشتغل من الـSDK مباشرة (بيستخدم NuGet audit feed). خد بالك إن `trivy sbom` محتاج SBOM بصيغة CycloneDX أو SPDX، وإن الثغرات «بلا إصلاح» هتكون أغلبية النتائج — ودي بالظبط اللي بيتعامل معاها بـVEX أو تذكرة مش بالتجاهل.",
             "solution": "النتائج النموذجية لمشروع .NET 10 حديث: SBOM التطبيق فيه ~120–250 مكوّن (معظمها غير مباشر من `Microsoft.Extensions.*`)، وSBOM الصورة بيضيف ~15–40 مكوّنًا نظاميًا من الأساس (libc/openssl/zlib في noble-chiseled أو alpine). الثغرات النموذجية: 0–2 high قابلة للإصلاح في الحزم غير المباشرة (تُحل برفع إصدار الحزمة الأب)، و5–20 «بلا إصلاح» في الحزم النظامية (غالبًا صور chiseled أقل تأثرًا لأن الحزم مقطوعة). القرار النموذجي: تحديث ما يمكن، وVEX للحزم غير المستخدمة في مسار التنفيذ، وتذكرة متابعة للباقي مع مراجعة ربع سنوية. أهم اكتشاف متوقع: **عدد المكونات غير المباشرة أكبر بكثير مما تتخيل** — وده بالظبط سبب إن الـSBOM ضروري مش رفاهية.",
             "resources": [
                 "https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages",
                 "https://github.com/CycloneDX/cyclonedx-dotnet",
                 "https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-list-package",
                 "https://trivy.dev/latest/docs/target/sbom/",
                 "https://cyclonedx.org/capabilities/vex/",
                 "https://www.cisa.gov/sbom",
             ]},
            {"id": "s7-m2-l2-t2",
             "title": "مهمة 2: توقيع + provenance + منع في الإدخال",
             "md": "ابنِ سلسلة كاملة: workflow يبني ويدفع **بالـdigest**، يولّد SBOM من الصورة، يربط provenance + SBOM attestation، ويوقّع keyless. ثم سكربت تحقق (`verify-image.sh`) يثبّت الهوية ويستخرج الـprovenance ويفحص الـSBOM. وأخيرًا سياسة admission في cluster (أو kind محلي) ترفض صور سجلك غير الموقعة — **طبّقها audit أولًا ثم enforce**.",
             "criteria": [
                 "Workflow يدفع بالـdigest ويخرج الـdigest كـoutput، ويستخدم `actions/attest` (provenance + SBOM) و`cosign sign --yes` — بالصلاحيات الصحيحة (`id-token`/`attestations`/`artifact-metadata`/`packages`).",
                 "**أرشيف SBOM** محفوظ لكل إصدار (artifact أو تخزين خارجي) مع تعليل: بيانات تشغيل Actions محدودة المدة.",
                 "`verify-image.sh` ينفذ: `gh attestation verify` + `cosign verify` مع `--certificate-identity-regexp` يثبت المستودع **والـworkflow** + استخراج predicate الـprovenance + فحص SBOM بـTrivy.",
                 "سياسة admission (`ClusterImagePolicy` أو مكافئ Kyverno لإصدارك) بـglob محصور في سجلك + استثناءات للسجلات الموثوقة + اشتراط `predicateType` للـprovenance.",
                 "**دليل الوضعين**: لقطة/سجل من وضع audit يُظهر مخالفة مرفوضة نظريًا، ثم سجل من وضع enforce يُظهر رفض Pod فعلي (وصورة مقبولة تمر).",
                 "اختبار سلبي: حاول نشر صورة غير موقعة (أو من مستودع آخر) وأثبت إن السياسة رفضتها — مع رسالة الخطأ.",
                 "صفحة قرار قصيرة: SLSA level الحالي (L2/L3) · ما الذي ينقص للوصول للـL3 · وهل الـattestations متاحة على خطتك (عامة/خاصة).",
             ],
             "hint": "للتجربة محليًا من غير سحابة: `kind create cluster` ثم `helm install policy-controller sigstore/policy-controller -n cosign-system` (أو Kyverno)، ووقّع صورة محلية بـ`cosign sign` مع `COSIGN_EXPERIMENTAL=1` في الإصدارات الأقدم أو keyless افتراضيًا في الحديثة — ولو الـregistry محلي (kind) فاستخدم `reg:5000/shop/app@sha256:...`. ولو عايز تتجنب تعقيد الـadmission مؤقتًا: نفّذ التحقق في **خطوة نشر** داخل الـCD (`verify-image.sh` قبل `kubectl apply`) — أضعف من admission بس أفضل من مفيش، واكتب ده صراحةً في صفحة القرار.",
             "solution": "النتيجة النموذجية: أول محاولة `cosign verify` بتفشل برسالة «no matching signatures» لأنك نسيت `--yes` في التوقيع أو وقعت بالـtag وبتتحقق بالـdigest — وقّع وتحقق بنفس الـdigest. ثاني فشل شائع: الـattestation محفوظ في GitHub (خاص) و`push-to-registry: true` محتاج صلاحيات على الـregistry، فالحل إما تفعيل الدفع للسجل أو الاعتماد على `gh attestation verify`. في وضع audit هتكتشف إن عندك صور من سجلات ما كنتش فاكرها (sidecars للـmonitoring، init containers) — دي بتتحول لسياسة استثناء. والاختبار السلبي الأهم: صورة من `docker.io/library/nginx` تحت glob الخاص بيك لازم تُرفض؛ لو اتقبلت فالـglob غلط. مستوى SLSA النموذجي بعد المهمة: **L2**، وللوصول لـL3 انقل خطوة الـattestation لـreusable workflow في مستودع منفصل وثبّت `--signer-workflow` في التحقق.",
             "resources": [
                 "https://docs.github.com/en/actions/concepts/security/artifact-attestations",
                 "https://github.com/actions/attest",
                 "https://docs.sigstore.dev/cosign/signing/signing_with_blobs/",
                 "https://slsa.dev/spec/v1.0/levels",
                 "https://docs.sigstore.dev/policy-controller/overview/",
                 "https://kyverno.io/docs/verifying-images/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "OWASP Top 10:2025 — A03 Software Supply Chain Failures", "url": "https://top10.owasp.org/2025/"},
            {"label": "OWASP DevSecOps Guideline: توقيع النواتج والـprovenance", "url": "https://owasp.github.io/DevSecOpsGuideline/"},
            {"label": "CycloneDX module for .NET", "url": "https://github.com/CycloneDX/cyclonedx-dotnet"},
            {"label": "CISA: SBOM (العناصر الدنيا)", "url": "https://www.cisa.gov/sbom"},
            {"label": "SLSA: المستويات والمواصفة", "url": "https://slsa.dev/spec/v1.0/levels"},
            {"label": "GitHub Docs: artifact attestations", "url": "https://docs.github.com/en/actions/concepts/security/artifact-attestations"},
            {"label": "Sigstore: cosign وpolicy-controller", "url": "https://docs.sigstore.dev/"},
            {"label": "Trivy: فحص SBOM والصور", "url": "https://trivy.dev/latest/docs/target/sbom/"},
            {"label": "NuGet: تدقيق الحزم (NuGetAudit)", "url": "https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages"},
        ]},
    ],
}

LESSONS_S7_E = [_L2]
