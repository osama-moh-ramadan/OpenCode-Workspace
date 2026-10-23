# -*- coding: utf-8 -*-
"""Stage 6 module 3 (part A): s6-m3-l1 (GitHub Actions), s6-m3-l2 (الجودة المفروضة آليًا)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s6-m3-l1 — GitHub Actions لمشروع .NET
# ══════════════════════════════════════════════════════════════════════════
_L1 = {
    "id": "s6-m3-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "كل اللي بنيته — الصورة الصغيرة، الاختبارات، الـmanifests، الهوية المُدارة — بيضيع لو النشر لسه «من جهازي». في الدرس ده هتبني pipeline حقيقي لـ.NET على GitHub Actions: **CI على كل PR** (restore مقفل · build بتحذيرات كأخطاء · اختبارات بتغطية · نتائج منشورة) · **Release** (صورة بـdigest ثابت + SBOM + provenance + توقيع cosign + attestation) · **Deploy بلا سر واحد** عن طريق OIDC وfederated credentials مربوطة بـ**GitHub Environment** فيه موافقة بشرية. وهتعرف إزاي تخلّي الـpipeline سريع (cache + matrix + مسارات مُفلترة + reusable workflows)."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Workflow / Job / Step", "def": "الـ**workflow** = ملف YAML بيُشغَّل بأحداث (push/PR/schedule). الـ**job** = وحدة تنفيذ على runner (بتشتغل بالتوازي افتراضيًا). الـ**step** = أمر أو action داخل job."},
            {"term": "Runner", "def": "الجهاز اللي بينفّذ: **GitHub-hosted** (`ubuntu-latest` — مجاني للحسابات العامة ودقائق محدودة للخاصة) أو **self-hosted** (أسرع/أرخص للأحمال الثقيلة، بس مسؤوليتك أمنيًا)."},
            {"term": "`permissions`", "def": "صلاحيات الـ`GITHUB_TOKEN` لكل workflow/job. **الافتراضي الآمن: `contents: read` فقط**، وتضيف `id-token: write` للـOIDC و`attestations: write` للـattestations. صلاحيات واسعة = خطر لو action اختُرق."},
            {"term": "OIDC + federated credential", "def": "الـworkflow بياخد توكن قصير العمر من GitHub، وEntra ID بيبدّله بتوكن Azure بعد التحقق من `issuer` و`subject` و`audiences`. **مفيش client secret مخزّن نهائيًا**."},
            {"term": "GitHub Environment", "def": "كيان في إعدادات المستودع (`production`/`staging`) بيحمل: **required reviewers** (حتى 6) · **wait timer** · **deployment branches** · secrets/variables خاصة به. وبيظهر في `subject` توكن الـOIDC."},
            {"term": "Pinning بـSHA", "def": "تثبيت الـaction على commit SHA كامل (`azure/login@8c334a1…`) بدل tag (`@v2`) — حماية من اختراق upstream. الأهم للـactions الخارجية (غير `actions/*`)."},
            {"term": "`global.json`", "def": "تثبيت إصدار SDK للمشروع كله (محليًا وفي CI). `setup-dotnet` بيقراه عبر `global-json-file` — يعني CI ومحطة التطوير على نفس الإصدار دائمًا."},
            {"term": "Lock file (`packages.lock.json`)", "def": "قائمة الحزم بإصداراتها الدقيقة. بيمكّن `dotnet restore --locked-mode` (يرفض أي تغيير غير مقصود) و**بيخلي cache الـNuGet شغال فعلًا** (مفتاح الكاش بيعتمد عليه)."},
            {"term": "Cache وArtifacts", "def": "**Cache** = تسريع بين التشغيلات (NuGet/صور Docker). **Artifact** = مخرجات محفوظة من job لـjob (نتائج اختبارات · تقرير تغطية · zip منشور · **digest الصورة**)."},
            {"term": "`concurrency`", "def": "إلغاء/تسلسل التشغيلات المتزامنة لنفس الفرع: `group` + `cancel-in-progress` — بيوفر دقائق runner وبيمنع نشرين متعارضين."},
            {"term": "Reusable workflow", "def": "workflow بـ`workflow_call` بيتنادى من workflows تانية — يعني CI موحّد لكل الخدمات في الـmonorepo بدل نسخ/لصق."},
            {"term": "Merge queue", "def": "طابور دمج في GitHub: كل PR بيتدمج بعد ما يُختبر **مع التغييرات السابقة في الطابور** — بيمنع «أخضر لوحده، مكسور مع غيره»."},
        ]},

        # ── 1) الشكل العام
        {"type": "heading", "level": 2, "text": "① شكل الـpipeline: 7 محطات من commit لـproduction"},
        {"type": "steps", "title": "المسار الكامل (وكل محطة ليها سبب)",
         "items": [
             {"title": "1) PR: تحقق سريع (أقل من 5 دقائق)",
              "md": "restore مقفل · build بتحذيرات كأخطاء · تنسيق · اختبارات وحدة · اختبارات معمارية. الهدف: feedback فوري للمطوّر. لو أبطأ من 5 دقائق، المطوّر هيبدأ يتجاهله.",
              "code": ""},
             {"title": "2) PR: اختبارات التكامل على Testcontainers",
              "md": "job منفصل (بيشتغل بالتوازي) فيه PostgreSQL/Redis/RabbitMQ حقيقية (1.2.4 و5.3.3). لو بطيء، شغّله على `pull_request` بس للمسارات الحساسة أو على merge queue.",
              "code": ""},
             {"title": "3) بعد الدمج على main: بناء الصورة ونشرها بـdigest",
              "md": "صورة متعددة المراحل (6.1.1) + SBOM + provenance + توقيع cosign + attestation. **المُخرج المهم: الـdigest** — هو اللي هيتنقل بين البيئات (مش tag متحرك).",
              "code": ""},
             {"title": "4) نشر تلقائي لـdev/staging",
              "md": "بنفس الـdigest، مع `environment: staging` (بلا موافقة عادةً)، وبعده **smoke tests** على `/health` و`/alive` ومسار عمل حقيقي (6.3.3).",
              "code": ""},
             {"title": "5) البنية ككود: what-if قبل النشر",
              "md": "لو فيه تغيير في `infra/`، شغّل `az deployment group what-if` (أو `terraform plan`) وانشر الناتج كتعليق على الـPR — البنية بتتراجع زي الكود (6.3.4).",
              "code": ""},
             {"title": "6) موافقة بشرية ثم إنتاج",
              "md": "`environment: production` بـ**required reviewers** — الـjob بيقف لحد ما حد يوافق. والـfederated credential مربوط بنفس البيئة، يعني **تجاوز branch protection ما يفيدش**: بلا موافقة مفيش توكن Azure أصلًا.",
              "code": ""},
             {"title": "7) تحقق بعد النشر + رجوع جاهز",
              "md": "smoke tests + مراقبة p95 والأخطاء (2.3.4) + أمر رجوع واحد مُختبَر (6.3.3). النشر من غير خطة رجوع = قمار.",
              "code": ""},
         ]},

        # ── 2) CI
        {"type": "heading", "level": 2, "text": "② ملف CI الكامل"},
        {"type": "code", "lang": "json", "title": "global.json + csproj: تثبيت الإصدار والقفل", "filename": "global.json", "code": r'''{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestFeature",
    "allowPrerelease": false
  }
}

// وفي كل csproj (أو Directory.Build.props مرة واحدة):
//   <PropertyGroup>
//     <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
//     <RestoreLockedMode Condition="'$(CI)' == 'true'">true</RestoreLockedMode>
//     <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
//     <AnalysisLevel>latest-recommended</AnalysisLevel>
//   </PropertyGroup>
//
// ليه: lock file = (1) restore --locked-mode يرفض الحزم الجديدة غير المقصودة
//                (2) مفتاح cache الـNuGet في setup-dotnet بيعتمد عليه
//      TreatWarningsAsErrors = التحذيرات ما تتراكمش لحد ما تبقى مستحيلة الإصلاح
'''},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/ci.yml", "filename": ".github/workflows/ci.yml", "code": r'''name: CI
# ⚠ ملاحظة تثبيت: الأفعال هنا مكتوبة بـtags (v4/v6) للوضوح التعليمي.
#   في مستودع حقيقي ثبّت الأفعال **الخارجية** على commit SHA كامل
#   (مثال: azure/login@8c334a195cbb38e46038007b304988d888bf676a) وخلي Dependabot يقترح التحديث.
# ملاحظة YAML: بعض المحللات بتقرأ المفتاح `on` كقيمة boolean — GitHub بيتعامل معها صح.
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  merge_group:                    # لو فعّلت merge queue (موصى به)
    types: [checks_requested]

# أقل صلاحيات — وتُرفع فقط في الـjob اللي محتاجها:
permissions:
  contents: read

env:
  DOTNET_NOLOGO: "true"
  DOTNET_CLI_TELEMETRY_OPTOUT: "true"
  NUGET_PACKAGES: ${{ github.workspace }}/.nuget/packages   # يخلي الـcache صغيرًا ومتوقعًا
  CONFIGURATION: Release

# ألغِ التشغيلات القديمة لنفس الفرع (توفير دقائق + منع تعارض):
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}   # لا تلغِ على main

jobs:
  build-test:
    name: Build & Test (${{ matrix.tfm }})
    runs-on: ubuntu-latest
    timeout-minutes: 15                 # لا تترك job عالقًا يستهلك دقائق
    strategy:
      fail-fast: false                  # شغّل كل المصفوفة حتى لو واحد فشل
      matrix:
        tfm: [net10.0]                  # أضف net8.0 لو مكتبة متعددة الأهداف
    steps:
      - uses: actions/checkout@v4

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          global-json-file: global.json  # نفس إصدار SDK محليًا وفي CI
          cache: true
          cache-dependency-path: |
            **/packages.lock.json
            **/Directory.Packages.props

      - name: Restore (locked)
        run: dotnet restore --locked-mode

      - name: Format (verify only)
        if: github.event_name == 'pull_request'
        run: dotnet format --verify-no-changes --severity info

      - name: Build (warnings as errors)
        run: dotnet build --no-restore -c ${{ env.CONFIGURATION }} /warnaserror

      - name: Architecture tests
        run: dotnet test tests/Shop.ArchitectureTests -c ${{ env.CONFIGURATION }} --no-build

      - name: Unit tests + coverage
        run: >
          dotnet test tests/Shop.UnitTests -c ${{ env.CONFIGURATION }} --no-build
          --collect:"XPlat Code Coverage"
          --results-directory ${{ github.workspace }}/coverage
          --logger "trx;LogFileName=unit.trx"

      - name: Upload results
        if: always()                     # النتائج مهمة خصوصًا عند الفشل
        uses: actions/upload-artifact@v4
        with:
          name: results-${{ matrix.tfm }}
          path: |
            coverage/**/*.xml
            **/*.trx
          retention-days: 14

  integration:
    name: Integration (Testcontainers)
    runs-on: ubuntu-latest
    timeout-minutes: 25
    needs: build-test
    if: github.event_name != 'merge_group'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { global-json-file: global.json, cache: true }
      - run: dotnet restore --locked-mode
      - name: Integration tests (Docker required)
        run: >
          dotnet test tests/Shop.IntegrationTests -c ${{ env.CONFIGURATION }}
          --collect:"XPlat Code Coverage" --results-directory ${{ github.workspace }}/coverage
          --logger "trx;LogFileName=integration.trx"
        env:
          TESTCONTAINERS_RYUK_DISABLED: "false"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-results
          path: ["coverage/**/*.xml", "**/*.trx"]
          retention-days: 14

  quality-gate:
    name: Quality gate
    runs-on: ubuntu-latest
    needs: [build-test, integration]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { path: artifacts }
      - name: Merge coverage & enforce threshold
        run: |
          dotnet tool install -g dotnet-reportgenerator-globaltool
          reportgenerator \
            -reports:"artifacts/**/coverage.cobertura.xml" \
            -targetdir:"coverage-report" \
            -reporttypes:"Cobertura;MarkdownSummaryGithub"
          # البوابة الرقمية (الدرس 6.3.2): افشل تحت الحد
          python3 - <<'PY'
          import sys, xml.etree.ElementTree as ET
          rate = float(ET.parse("coverage-report/Cobertura.xml").getroot().attrib["line-rate"]) * 100
          print(f"line coverage = {rate:.1f}% (threshold 80%)")
          sys.exit(0 if rate >= 80 else 1)
          PY
          cat coverage-report/SummaryGithub.md >> "$GITHUB_STEP_SUMMARY"

  # ── CI على المسارات الحساسة فقط: فلترة المسارات توفر دقائق ──
  # paths: ['src/**', 'tests/**', 'global.json', '**/*.csproj', '**/packages.lock.json']
'''},

        # ── 3) Release + الأمان
        {"type": "heading", "level": 2, "text": "③ Release: صورة موقعة بـdigest + نشر بلا أسرار"},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/release.yml", "filename": ".github/workflows/release.yml", "code": r'''name: Release & Deploy

on:
  push:
    tags: ["v*.*.*"]          # نسخة صريحة — أفضل من النشر على كل push لـmain
  workflow_dispatch:
    inputs:
      environment:
        description: "البيئة المستهدفة"
        type: choice
        options: [staging, production]
        default: staging

permissions:
  contents: read

env:
  REGISTRY: acrshopprod.azurecr.io
  IMAGE: shop/orders

jobs:
  package:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write          # لتوقيع cosign بلا مفاتيح (keyless)
      attestations: write      # لـattestation من GitHub
      packages: read
    outputs:
      digest: ${{ steps.push.outputs.digest }}
      image: ${{ env.REGISTRY }}/${{ env.IMAGE }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { global-json-file: global.json, cache: true }
      - run: dotnet publish src/Orders.Api -c Release -o publish/

      - uses: docker/setup-buildx-action@v3
      # الدخول للسجل بالهوية (OIDC) — بلا ACR_USERNAME/PASSWORD وبلا admin password:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: az acr login --name acrshopprod

      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=sha,format=long

      - id: push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: mode=max          # SBOM/مصدر البناء
          sbom: true

      # توقيع بلا مفاتيح مخزّنة (6.1.3):
      - uses: sigstore/cosign-installer@v3
      - name: Sign image
        run: cosign sign --yes ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.push.outputs.digest }}

      # إثبات مصدر البناء قابل للتحقق:
      - uses: actions/attest-build-provenance@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true

  deploy-staging:
    needs: package
    runs-on: ubuntu-latest
    environment: staging           # بلا مراجعين → تلقائي
    permissions:
      contents: read
      id-token: write               # OIDC
    steps:
      - name: Login to Azure (OIDC — بلا secret)
        uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}            # معرّفات، لا أسرار → vars
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy by digest (ليس بـtag متحرك)
        run: |
          az containerapp update \
            --name orders --resource-group rg-shop-staging \
            --image ${{ needs.package.outputs.image }}@${{ needs.package.outputs.digest }}
          az containerapp revision list -n orders -g rg-shop-staging -o table

      - name: Smoke tests (6.3.3)
        run: |
          URL=$(az containerapp show -n orders -g rg-shop-staging \
                 --query properties.configuration.ingress.fqdn -o tsv)
          for i in $(seq 1 30); do
            code=$(curl -s -o /dev/null -w '%{http_code}' "https://$URL/health" || true)
            [ "$code" = "200" ] && { echo "healthy"; exit 0; }
            sleep 5
          done
          echo "التطبيق لم يصبح صحيًا"; exit 1

  deploy-production:
    needs: [package, deploy-staging]
    runs-on: ubuntu-latest
    environment: production        # required reviewers → الـjob ينتظر موافقة بشرية
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Canary ثم كل الحركة (6.3.3)
        run: |
          set -euo pipefail
          IMAGE="${{ needs.package.outputs.image }}@${{ needs.package.outputs.digest }}"
          NEW="orders--${{ github.run_number }}"
          # التقط اسم النسخة الحالية **قبل** النسخ (بعدها latestRevisionName هيبقى الجديد):
          CURRENT=$(az containerapp show -n orders -g rg-shop-prod \
                     --query properties.latestRevisionName -o tsv)
          az containerapp revision copy -n orders -g rg-shop-prod \
            --revision "$NEW" --image "$IMAGE"
          az containerapp ingress set -n orders -g rg-shop-prod \
            --traffic-split "$CURRENT=90" --traffic-split "$NEW=10"
          echo "راجع المؤشرات 15 دقيقة ثم رقِّ:"
          echo "  az containerapp ingress set -n orders -g rg-shop-prod --traffic-split \"$NEW\"=100"
          echo "وللرجوع الفوري:"
          echo "  az containerapp ingress set -n orders -g rg-shop-prod --traffic-split \"$CURRENT\"=100"
'''},
        {"type": "code", "lang": "bash", "title": "azure/70-oidc.sh — إعداد النشر بلا سر (مرة واحدة)", "filename": "azure/70-oidc.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

ORG=your-org; REPO=shop; RG=rg-shop-prod

# ═══ 1) App registration + service principal ═══
az ad app create --display-name "github-actions-$REPO" >/dev/null
APP_ID=$(az ad app list --display-name "github-actions-$REPO" --query "[0].appId" -o tsv)
az ad sp create --id "$APP_ID" >/dev/null
OBJ_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# ═══ 2) صلاحية محدودة: Contributor على مجموعة موارد الإنتاج فقط ═══
az role assignment create --role Contributor \
  --assignee-object-id "$OBJ_ID" --assignee-principal-type ServicePrincipal \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RG"
# لو النشر بيعدّل أسرار/أدوار → أضف "User Access Administrator" على نطاق الـvault فقط،
# ولا تمنح Contributor على مستوى الاشتراك.

# ═══ 3) federated credentials: واحد لكل بيئة (subject مختلف) ═══
# البيئة (موصى به — بيشتغل مع required reviewers):
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-prod-env",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:'"$ORG"'/'"$REPO"':environment:production",
  "description": "GitHub Actions OIDC for the production environment",
  "audiences": ["api://AzureADTokenExchange"]
}'
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-staging-env",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:'"$ORG"'/'"$REPO"':environment:staging",
  "audiences": ["api://AzureADTokenExchange"]
}'
# الفرع (للاختبارات على main من غير environment):
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:'"$ORG"'/'"$REPO"':ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
# قيود: حتى 20 federated credentials لكل app registration،
# وissuer/subject حتى 600 حرف. راجع التوثيق قبل ما تعتمد على الأرقام.

# ═══ 4) في GitHub: Environments + variables (مش secrets!) ═══
# Settings → Environments → New: "staging" و"production"
#   production: Required reviewers = فريقك · Deployment branches = main فقط · Wait timer = 0
#   Environment variables (معرّفات، ليست أسرارًا):
#     AZURE_CLIENT_ID=$APP_ID
#     AZURE_TENANT_ID=<tenant>
#     AZURE_SUBSCRIPTION_ID=<subscription>
# gh variable set NAME --body VALUE --env ENVIRONMENT   (تحقق: gh variable set --help)
gh variable set AZURE_CLIENT_ID     --body "$APP_ID"                 --env production
gh variable set AZURE_TENANT_ID     --body "$(az account show --query tenantId -o tsv)" --env production
gh variable set AZURE_SUBSCRIPTION_ID --body "$(az account show --query id -o tsv)"     --env production

# ═══ 5) تحقق ═══
echo "لو الـworkflow فشل بـ AADSTS700016/700021 → الـsubject مش مطابق (environment مقابل ref)"
echo "لو فشل بـ 403 على az → ناقص دور على مجموعة الموارد"
'''},
        {"type": "table", "caption": "إيه يتخزن فين — وأهم قرار أمني في الـpipeline",
         "head": ["النوع", "المثال", "أين يُخزَّن", "ليه"],
         "rows": [
             ["**معرّفات** (ليست أسرارًا)", "`AZURE_CLIENT_ID` · `AZURE_TENANT_ID` · `AZURE_SUBSCRIPTION_ID`",
              "**Variables** (على مستوى البيئة)", "ظاهرة ومراجَعة في الـlogs — ومفيش سبب لإخفائها، وإخفاؤها بيعقّد التشخيص"],
             ["**أسرار حقيقية**", "مفاتيح مزودين خارجيين · `ACR_PASSWORD` (لو مش مستخدم OIDC)",
              "**Secrets** على مستوى البيئة (مش المستودع كله)", "الوصول مقصور على jobs البيئة دي — تسريب أقل"],
             ["**بلا تخزين أصلًا**", "دخول Azure للنشر",
              "**OIDC + federated credential**", "مفيش سر يدوّر ولا يتسرّب؛ والثقة مرتبطة بـrepo+environment، يعني موافقة بشرية = شرط للوصول"],
             ["**Actions**", "`azure/login@v2`",
              "**pin بـSHA** للأفعال الخارجية", "tag بيتحرك: اختراق upstream = كود خبيث في pipeline بينشر لإنتاجك"],
         ]},
        {"type": "callout", "kind": "danger", "title": "5 أخطاء بتفتح ثغرة أو بتوقف النشر",
         "md": "**① `AZURE_CREDENTIALS`/client secret مع OIDC**: وجود سر «احتياطي» معناه إنك لسه معرض للتسريب — احذفه. **② `subject` غلط**: لو الـfederated credential بـ`ref:refs/heads/main` والـjob فيه `environment: production` → فشل مصادقة (`AADSTS700021`/`700016`)؛ اعمل credential لكل pattern مستخدم. **③ `permissions: write-all` ضمنيًا**: أي action مخترق يقدر يعدّل الكود وينشره — خلي الافتراضي `contents: read` وارفع الصلاحيات per-job. **④ `azure/functions-action` مع `publish-profile` و`azure/login` معًا**: الأسلوبان متعارضان ولو مرّرت الاثنين، الـaction بيستخدم publish-profile ويتجاهل جلستك الآمنة. **⑤ tag متحرك للنشر** (`:latest` أو `:main`): النشر بيتكرر بصورة مختلفة عن اللي اختُبرت — انشر بـ**digest** دايمًا."},

        # ── 4) السرعة
        {"type": "heading", "level": 2, "text": "④ السرعة: pipeline بطيء = pipeline بيتجاهل"},
        {"type": "table", "caption": "تقنيات التسريع — المكسب مقابل الثمن",
         "head": ["التقنية", "المكسب", "الثمن/الشرط", "إمتى تستخدمها"],
         "rows": [
             ["`setup-dotnet` مع `cache: true` + `packages.lock.json`",
              "توفير 30–90 ثانية في الـrestore", "لازم lock file (وإلا الكاش ما يشتغلش)", "دايمًا"],
             ["`concurrency` + `cancel-in-progress` على PRs",
              "إلغاء تشغيلات ميتة = دقائق runner", "لو `true` على main ممكن تلغى تشغيل مهم", "PRs نعم · main بحذر"],
             ["`paths` filters على الـworkflow",
              "ما يشغلش CI لتغيير في `docs/`", "ممكن يفوّت تغيير مؤثر (مثل تعديل reusable workflow)", "للمستودعات الكبيرة"],
             ["تقسيم الاختبارات لـjobs متوازية (unit/integration/e2e)",
              "الزمن الكلي = أبطأ job مش المجموع", "تكلفة دقائق أعلى (runner لكل job)", "دايمًا لما المجموع > 5 دقائق"],
             ["`docker/build-push-action` مع `cache-from/to: type=gha`",
              "بناء صورة في ثوانٍ بدل دقائق", "حد حجم الكاش (10 GB لكل مستودع)", "لأي pipeline فيه صور"],
             ["Reusable workflow (`workflow_call`) + composite actions",
              "CI موحّد لكل الخدمات + صيانة أقل", "تعقيد أولي في تمرير المدخلات/المخرجات", "monorepo أو 3+ خدمات"],
             ["Self-hosted runners",
              "أسرع (كاش دائم) وأرخص للأحمال الثقيلة", "**مسؤولية أمنيّة**: عزل · تحديثات · fork PRs خطر", "لما الدقائق المدفوعة بقت بندًا في الفاتورة"],
             ["Merge queue",
              "يمنع كسر main من PRs «خضرا لوحدها»", "زمن انتظار أطول للدمج", "لما فريقك > 3 مطورين"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قاعدة الـ5 دقائق",
         "md": "خلي هدفك: **feedback على PR في أقل من 5 دقائق**. لما تتجاوز، المطوّر بيبدأ يدمج من غير ما يقرا النتيجة — والبوابة بقت ديكور. الأدوات: jobs متوازية · اختبارات سريعة في الـPR والثقيلة على main/merge queue · كاش · وفلترة مسارات. وقِس: GitHub بيديك زمن كل job في الـUI — راجع أبطأ 3 خطوات شهريًا."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أقدر أكتب workflow فيه `permissions` بأقل امتياز و`concurrency` و`timeout-minutes` وmatrix.",
            "أعرف تثبيت إصدار SDK بـ`global.json` + `global-json-file`، وتفعيل `packages.lock.json` + `--locked-mode` (وهو شرط لعمل الكاش).",
            "أقدر أنشر صورة بـ**digest** مع SBOM/provenance وتوقيع cosign وattestation، وتمرير الـdigest لـjob النشر.",
            "فاهم OIDC بالكامل: `id-token: write` + `azure/login` + federated credential بـ`subject` مربوط بـ**environment**.",
            "أعرف الفرق بين secrets وvariables وأين يُخزَّن كل واحد، وإزاي أعمل required reviewers لبيئة الإنتاج.",
            "أقدر أثبّت الـactions بـSHA وأفهم ليه ده قرار أمني مش ترف.",
            "أعرف 4 تقنيات لتسريع الـpipeline وأقدر أقيس أبطأ الخطوات.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الـpipeline والأمان.",
         "questions": [
             {"q": "`setup-dotnet` مع `cache: true` ما بيعملش كاش للـNuGet. السبب الأشهر؟",
              "options": ["الـrunner لا يدعم الكاش", "**مفيش lock file** (`packages.lock.json`) — الكاش بيحسب المفتاح من ملفات القفل", "`NUGET_PACKAGES` غير مضبوط", "الإصدار `10.0.x` بدل `10.0.100`"],
              "answer": 1,
              "explain": "لازم `RestorePackagesWithLockFile=true` (ويُفضَّل `RestoreLockedMode` في CI) عشان يتولد `packages.lock.json` ويُستخدم كمفتاح للكاش — وهو نفسه اللي بيمكّن `restore --locked-mode`."},
             {"q": "الـjob فيه `environment: production` والـfederated credential موضوع بـ`subject: repo:org/repo:ref:refs/heads/main`. النتيجة؟",
              "options": ["هيشتغل عادي", "**فشل مصادقة**: الـsubject في التوكن بقى `environment:production` ولا يطابق القيد — لازم credential لكل pattern", "هيشتغل بصلاحيات أقل", "GitHub هيعدّل الـsubject تلقائيًا"],
              "answer": 1,
              "explain": "الـclaim بيتولد من سياق التشغيل. الحل الصحيح: credential بـ`environment:production` للإنتاج، وآخر بـ`environment:staging`، وثالث بـ`ref:refs/heads/main` للاختبارات. وميزة البيئة: بتشتغل مع required reviewers."},
             {"q": "ليه تربط الـfederated credential بـ**environment** بدل branch؟",
              "options": ["أسرع", "لأن البيئة بتضيف **موافقة بشرية** (required reviewers) وحماية فروع — يعني بلا موافقة لا يوجد توكن Azure أصلًا", "لأن branch مش مدعوم", "لأن البيئة تدعم client secret"],
              "answer": 1,
              "explain": "الثقة المرتبطة بفرع ملهاش human-in-the-loop: لو الـworkflow اتشغّل على main، هينشر. البيئة بتخلي الوصول للسحابة نفسه خلف موافقة."},
             {"q": "ليه تثبّت الـactions بـcommit SHA؟",
              "options": ["أسرع في التحميل", "لأن الـtag متحرك: لو الـaction الخارجي اختُرق، الإصدار الجديد بيشغّل كودًا خبيثًا بصلاحيات pipeline الإنتاج", "مطلوب من GitHub", "يمنع أخطاء YAML"],
              "answer": 1,
              "explain": "الأهم للـactions غير `actions/*`. التثبيت بـSHA بيخلي التحديث قرارًا واعيًا في PR (وممكن Dependabot يقترحه). وخلي `permissions` ضيقة عشان تقلل أثر أي اختراق."},
             {"q": "النشر بيستخدم `--image repo/app:latest`. المشكلة؟",
              "options": ["الصورة كبيرة", "**النشر مش مرتبط بالنسخة المُختبَرة**: `latest` بيتغير، فالرجوع والـcanary والتدقيق كلها بلا معنى — انشر بـdigest", "ACR لا يدعمه", "يبطّئ السحب"],
              "answer": 1,
              "explain": "الـdigest (`@sha256:…`) غير قابل للتغيير: اللي اختبرته في staging هو نفسه اللي بينزل في الإنتاج، والرجوع = إعادة نشر digest قديم."},
             {"q": "عندك `AZURE_CREDENTIALS` (client secret) كـsecret «احتياطي» مع OIDC شغال. التصرف الصح؟",
              "options": ["اتركه للاحتياط", "**احذفه**: وجود سر طويل العمر = خطر تسريب ودوران مفقود، وOIDC بيغطي كل الحالات", "حوّله لـvariable", "استخدمه بدل OIDC"],
              "answer": 1,
              "explain": "«احتياطي» في الأمان معناه «مسار غير مُراقَب». لو OIDC فشل، أصلح الإعداد (subject/دور) بدل ما ترجع للسر."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "pipeline شغال + نشر بلا سر.",
         "items": [
             {"id": "t1", "title": "مهمة 1: CI كامل لمشروعك (بوابات + كاش + نتائج)",
              "md": "**السياق:** عندك حل .NET من المراحل السابقة (services + tests) ومحتاج CI على GitHub.\n\n**المطلوب:**\n1. `global.json` بإصدار SDK محدد + `RestorePackagesWithLockFile` و`TreatWarningsAsErrors` في `Directory.Build.props`، ورفع `packages.lock.json` للمستودع.\n2. `.github/workflows/ci.yml` فيه: `permissions: contents: read` · `concurrency` · `timeout-minutes` · job **build+unit** وjob **integration** (Testcontainers) بالتوازي/بالتسلسل حسب اختيارك المبرر · upload للنتائج بـ`if: always()`.\n3. job **quality-gate** بيدمج تقارير التغطية بـReportGenerator و**بيفشل تحت 80%** (أو حد تختاره وتبرره) وبيكتب ملخص في `GITHUB_STEP_SUMMARY`.\n4. فلترة مسارات (`paths`) بحيث تغييرات `docs/…` ما تشغّلش CI.\n5. **قياس**: سجّل زمن التشغيل قبل وبعد تفعيل الكاش (لقطة أو أرقام) — واكتب الفرق في `docs/ci-notes.md` مع أبطأ 3 خطوات.\n6. أضف **merge queue** أو على الأقل branch protection بـrequired checks (واكتب الإعدادات في `docs/ci-notes.md`).\n7. اختبر الفشل متعمدًا: ارفع PR فيه اختبار فاشل وفيه تحذير compiler وفيه حزمة جديدة بدون تحديث lock file — وثّق إن كل واحد منهم **كسر الـpipeline فعلًا**.",
              "criteria": [
                  "`global.json` + lock files مرفوعة و`restore --locked-mode` شغال في CI.",
                  "التحذيرات أخطاء (`/warnaserror` أو `TreatWarningsAsErrors`) ومُثبتة بتجربة فشل.",
                  "بوابة تغطية رقمية تفشل تحت الحد، مع ملخص في `GITHUB_STEP_SUMMARY`.",
                  "`permissions` ضيقة على مستوى الـworkflow و`timeout-minutes` على كل job.",
                  "`if: always()` على رفع النتائج (وإلا مش هتشوف سبب الفشل).",
                  "قياس زمن قبل/بعد الكاش برقمين + قائمة أبطأ 3 خطوات.",
                  "branch protection أو merge queue موثق (أسماء الـrequired checks).",
                  "ثلاث تجارب فشل متعمدة موثقة (اختبار · تحذير · lock file) — كل واحدة كسرت الـpipeline.",
              ],
              "hint": "أسهل طريقة لكسر الكاش عن غير قصد: تنسى رفع `packages.lock.json` (يظهر في `.gitignore` الافتراضي لبعض القوالب). وللتغطية: `--collect:\"XPlat Code Coverage\"` بيطلع `coverage.cobertura.xml` في مجلد GUID لكل مشروع — استخدم `…/coverage.cobertura.xml` في ReportGenerator. وللاختبارات البطيئة: `dotnet test --filter Category!=Slow` في الـPR وjob كامل على main.",
              "solution": "الملفات الناتجة: `global.json` · `Directory.Build.props` (lock+warnaserror+AnalysisLevel) · `.github/workflows/ci.yml` (3 jobs) · إعدادات branch protection (required: `Build & Test`, `Integration`, `Quality gate` + linear history + merge queue). الأرقام النموذجية: أول تشغيل ~4–6 دقائق، وبعد الكاش ~2–4 دقائق (التوفير الأكبر في الـrestore). أبطأ الخطوات نموذجيًا: (1) اختبارات التكامل مع سحب صور Testcontainers (2) `dotnet build` للحل الكامل (3) ReportGenerator. تجارب الفشل: اختبار فاشل → job أحمر؛ تحذير → فشل build؛ حزمة جديدة بلا تحديث lock → فشل `restore --locked-mode` برسالة واضحة. أهم قرار: خلي الـPR pipeline تحت 5 دقائق و انقل الثقيل لـmain/merge queue.",
              "resources": [
                  "https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-net",
                  "https://github.com/actions/setup-dotnet",
                  "https://learn.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files",
                  "https://github.com/danielpalme/ReportGenerator",
                  "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches",
                  "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue",
              ]},
             {"id": "t2", "title": "مهمة 2: نشر إلى Azure بـOIDC + environments + digest",
              "md": "**السياق:** عايز `release.yml` ينشر صورتك إلى Container Apps (أو App Service/Functions) **من غير سر Azure واحد**.\n\n**المطلوب:**\n1. `azure/70-oidc.sh`: app registration + service principal + **دور محدود على مجموعة موارد واحدة** + **federated credentials منفصلة** لـ`environment:staging` و`environment:production`.\n2. GitHub Environments: `staging` (بلا مراجعين) و`production` (**required reviewers** + deployment branches = main).\n3. `AZURE_CLIENT_ID/TENANT_ID/SUBSCRIPTION_ID` كـ**variables** على مستوى البيئة (مش secrets).\n4. `release.yml`: job `package` بيبني الصورة وينشرها بـdigest + SBOM + provenance + توقيع cosign + attestation، و`outputs.digest`؛ job `deploy-staging` ينشر بالـdigest ويعمل smoke test؛ job `deploy-production` بـ`needs` و`environment: production` ويعمل canary 90/10.\n5. **أدلة**: لقطة من سجل التشغيل تُظهر (أ) الـjob واقف في انتظار الموافقة (ب) نجاح `az account show` بعد الموافقة (ج) الـdigest المنشور مطابق لما اختُبر في staging.\n6. **تجربة فشل متعمدة**: غيّر الـsubject في الـfederated credential (أو شغّل من فرع غير مصرح له) ووثّق رسالة الخطأ وإزاي شخّصتها.\n7. اكتب `docs/deploy-runbook.md`: إزاي أنشر · إزاي أرجع (أمر واحد) · مين يوافق · إيه اللي أتأكد منه بعد النشر · وإيه اللي أعمل لو الموافقة اتأخرت.\n8. pin كل الـactions الخارجية بـ**commit SHA** (واكتب سكربت `scripts/pin-actions.sh` أو جدول في الوثيقة بالمراجعات الحالية).",
              "criteria": [
                  "مفيش `AZURE_CREDENTIALS` ولا client secret في المستودع (يُتحقق بـgrep) — والنشر بـOIDC فقط.",
                  "دور Azure محدود بمجموعة موارد (مش Contributor على الاشتراك) وموثق بالأمر.",
                  "federated credentials منفصلة لكل بيئة بالـsubject الصحيح (`environment:…`).",
                  "المعرّفات في **variables** والأسرار الحقيقية (لو فيه) في **secrets** على مستوى البيئة.",
                  "النشر بـ**digest** من `outputs` (مش tag) — ومُثبت إن staging وproduction نزلوا نفس الـdigest.",
                  "smoke test بعد النشر بـretry/timeout وفشل صريح لو التطبيق مش صحي.",
                  "canary 90/10 في الإنتاج + أمر الترقية لـ100% + أمر الرجوع في الـrunbook.",
                  "دليل الانتظار للموافقة + تجربة فشل مصادقة موثقة بالتشخيص.",
                  "pin بـSHA لكل الـactions الخارجية.",
              ],
              "hint": "أشهر ثلاث رسائل خطأ: `AADSTS700016` (التطبيق مش موجود في الـtenant) · `AADSTS700021`/`700022` (الـsubject/الثقة مش مطابقة) · `403 Forbidden` على `az containerapp update` (الدور ناقص أو على نطاق غلط). وللاختبار السريع من غير ما تنشر: job فيه `azure/login` + `az account show` + `az ad sp show --id $OBJ_ID` — لو نجح، السلسلة كلها سليمة.",
              "solution": "الترتيب العملي: (1) نفّذ `azure/70-oidc.sh` (2) أنشئ البيئتين في GitHub وضيف الـvariables (3) شغّل workflow صغير فيه `azure/login` + `az account show` للتأكد (4) ضيف `package` job واستخرج الـdigest كـoutput (5) `deploy-staging` بالـdigest + smoke test (6) `deploy-production` بـ`needs: [package, deploy-staging]` و`environment: production` (7) جرّب الانتظار للموافقة (8) جرّب الفشل المتعمد بتغيير الـsubject ووثّق الرسالة (9) اكتب الـrunbook: النشر = tag جديد أو `workflow_dispatch`؛ الرجوع = `az containerapp revision set-mode/ingress set --traffic-split orders--current=100` أو إعادة نشر digest سابق؛ التحقق بعد النشر = `/health` + p95 + معدل الأخطاء 15 دقيقة. النتيجة الأهم: **سلسلة ثقة بلا أسرار**: GitHub environment ← موافقة بشرية ← توكن OIDC قصير العمر ← دور محدود على مجموعة موارد.",
              "resources": [
                  "https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure",
                  "https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation",
                  "https://learn.microsoft.com/en-us/azure/container-apps/github-actions",
                  "https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment",
                  "https://docs.sigstore.dev/cosign/overview/",
                  "https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "GitHub Actions: بناء واختبار .NET", "url": "https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-net"},
            {"label": "actions/setup-dotnet (المدخلات والكاش)", "url": "https://github.com/actions/setup-dotnet"},
            {"label": "تأمين النشر: OIDC مع Azure", "url": "https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure"},
            {"label": "Workload Identity federation في Entra", "url": "https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation"},
            {"label": "GitHub Environments وقواعد الحماية", "url": "https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment"},
            {"label": "أفضل ممارسات أمان GitHub Actions", "url": "https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions"},
            {"label": "النشر إلى Container Apps بـGitHub Actions", "url": "https://learn.microsoft.com/en-us/azure/container-apps/github-actions"},
            {"label": "merge queue", "url": "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s6-m3-l2 — الجودة المفروضة آليًا
# ══════════════════════════════════════════════════
_L2 = {
    "id": "s6-m3-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الـpipeline السريع بلا بوابات = ناقل سريع للأعطال. في الدرس ده هتحوّل «المعايير» من كلام في الـPR review إلى **فحوصات بتفشل البناء**: تنسيق وتحذيرات كأخطاء · **بوابة تغطية** رقمية · **اختبارات معمارية** تمنع تسريب الاعتماديات · **فحص ثغرات الصور** · **مراجعة التبعيات** · **SBOM وتوقيع** · وكشف كسر العقود (OpenAPI/Pact). ومع كل بوابة: **الحد الرقمي، والسرعة، وخطة التعامل مع الفشل** — لأن البوابة اللي بتصرخ طول الوقت بتتعطّل."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Required status checks", "def": "فحوصات لازم تنجح قبل الدمج (branch protection). من غيرها الـCI «نصيحة»."},
            {"term": "بوابة التغطية (coverage gate)", "def": "حد رقمي على نسبة التغطية يفشل البناء لو اتكسر. المفيد: **حد على الكود الجديد/المتغير** مش على المشروع كله (وإلا المشروع القديم بيمنعك للأبد)."},
            {"term": "اختبار الطفرات (Mutation testing)", "def": "أداة (Stryker) بتعدّل كودك عمدًا (مثل `<` إلى `<=`) وتشوف هل اختباراتك بتكتشف التغيير. بتكشف «تغطية عالية واختبارات ضعيفة»."},
            {"term": "اختبار معماري", "def": "اختبار وحدة على **الاعتماديات بين الطبقات** (NetArchTest): Domain ما يعرفش EF · Application ما يعرفش ASP.NET · الخ. بيمنع تآكل المعمارية (4.1/4.2)."},
            {"term": "كسر العقد (breaking change)", "def": "تغيير في API بيكسر عميلًا موجودًا: حذف مسار/حقل · تغيير نوع · إضافة حقل مطلوب. يُكشف بمقارنة OpenAPI أو باختبارات العقد (Pact)."},
            {"term": "Dependency review", "def": "فحص PR بيوضح: الحزم الجديدة · تراخيصها · هل فيها تنبيهات أمان · هل فيها كود بناء (build scripts)."},
            {"term": "SBOM", "def": "قائمة مكونات الصورة/الحزمة (CycloneDX/SPDX). بتجاوب «أنا متأثر بثغرة X في مكتبة Y؟» في دقائق بدل أيام."},
            {"term": "Renovate / Dependabot", "def": "بوتات بتفتح PRs لتحديث التبعيات. الفرق المهم: التجميع (grouping) وسياسة التحديثات الكبرى والجدول — عشان ما يغرقوش الفريق."},
            {"term": "Flaky test", "def": "اختبار بينجح ويفشل عشوائيًا من غير تغيير في الكود. أخطر حاجة في الـCI: بيقتل الثقة في البوابة. الحل: عزل (quarantine) + issue + مهلة إصلاح."},
            {"term": "Secret scanning / push protection", "def": "فحص المستودع وPRs بحثًا عن أسرار ومنع رفعها أصلًا — طبقة أخيرة بعد ما تفشل كل الطبقات."},
            {"term": "Deterministic build", "def": "بناء ينتج نفس البايتات من نفس المصدر (مهم للتحقق من الـattestations وللكاش)."},
        ]},

        # ── 1) البوابات
        {"type": "heading", "level": 2, "text": "① البوابات: جدول الحد والسرعة وخطة الفشل"},
        {"type": "table", "caption": "كل بوابة لازم يكون لها حد رقمي وزمن وخطة فشل — وإلا هتتعطّل",
         "head": ["البوابة", "الأداة", "الحد الموصى به", "الزمن التقريبي", "لو فشلت"],
         "rows": [
             ["التنسيق والتحليل", "`dotnet format --verify-no-changes` + analyzers",
              "صفر انحراف · `TreatWarningsAsErrors`", "10–40 ثانية",
              "صلح محليًا بـ`dotnet format`؛ لو قاعدة غلط → `EditorConfig`/`.editorconfig` + suppress بتبرير"],
             ["اختبارات الوحدة", "xUnit v3 (1.2.1)", "**100% نجاح**", "20–60 ثانية",
              "لا تدمج. لو flaky → عزل فوري (الأسفل)"],
             ["التغطية", "coverlet + ReportGenerator",
              "**80% على الكود الجديد** · وحد أدنى عام (مثال 60%)", "10–20 ثانية",
              "أضف اختبارات للمسار الجديد؛ **لا ترفع الحد لتبرير فشل**"],
             ["اختبارات المعمارية", "NetArchTest",
              "صفر اعتماد مخالف", "1–3 ثوانٍ",
              "صلح الاعتماد أو اكتب ADR يبرر الاستثناء (4.1.3)"],
             ["اختبارات التكامل/العقود", "Testcontainers + Pact (5.3.3)",
              "100% نجاح على المسارات الحرجة", "2–6 دقائق",
              "شغّلها job منفصل؛ لو بطيئة → على main/merge queue"],
             ["الطفرات (mutation)", "Stryker.NET",
              "≥ 60–70% للمشروعات الجديدة (تدريجيًا)", "10–40 دقيقة",
              "**على جدول (ليلًا/أسبوعيًا)** مش على كل PR — واعمل issue للنتيجة"],
             ["ثغرات الصورة", "Trivy / Docker Scout (6.1.3)",
              "صفر CRITICAL · HIGH بدون إصلاح متاح = مقبول مؤقتًا بـissue", "30–90 ثانية",
              "حدّث الصورة الأساسية/الحزمة؛ `--ignore-unfixed` للثغرات بلا حل"],
             ["التبعيات الجديدة", "dependency-review + Dependabot/Renovate",
              "لا حزمة بتنبيه أمان معروف · تراخيص متوافقة", "5–15 ثانية",
              "راجع الترخيص والبديل؛ لا توافق على حزمة بلا صيانة"],
             ["كسر العقد (API)", "مقارنة OpenAPI + Pact provider verification",
              "صفر كسر غير مُعلَن", "10–60 ثانية",
              "إصدار جديد (versioning 2.1.x) + مسار توسيع/تضييق (3.5)"],
             ["الأسرار في الكود", "secret scanning + push protection + gitleaks في CI",
              "صفر تسريب", "<10 ثوانٍ",
              "**دوّر السر فورًا** ثم احذفه — الحذف وحده لا يكفي (6.2.3)"],
             ["SBOM + توقيع", "`sbom: true` + cosign + attestations",
              "موجود لكل صورة منشورة", "10–30 ثانية",
              "لا تنشر صورة بلا SBOM — هتبقى أعمى عند ثغرة جديدة"],
         ]},
        {"type": "callout", "kind": "warn", "title": "قاعدة البوابة اللي بتعيش",
         "md": "**بوابة بتفشل من غير خطة = بوابة بتتعطّل.** لكل بوابة حدد: (1) الحد الرقمي (2) مين مسؤول عن إصلاح الفشل (3) إمتى يُسمح بالاستثناء وكيف يُسجَّل (ADR/issue بملصق + تاريخ انتهاء). والأهم: **ابدأ بمستوى أدنى واقعي وارفعه تدريجيًا** — مشروع قديم بتغطية 35% ما تحطّش له بوابة 80% على الكود كله؛ حطّ البوابة على **الكود الجديد** بس وارفع الحد العام كل ربع سنة."},

        # ── 2) الـworkflow
        {"type": "heading", "level": 2, "text": "② ملف البوابات (نفس الأوامر محليًا وفي CI)"},
        {"type": "code", "lang": "yaml", "title": ".github/workflows/quality.yml", "filename": ".github/workflows/quality.yml", "code": r'''name: Quality Gates

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 2 * * 1"        # الاثنين 02:00 — للبوابات البطيئة (mutation/ثغرات)
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write          # لنشر تعليقات المراجعة على الـPR
  security-events: write        # لو رفعت نتائج SARIF لـCode Scanning

jobs:
  static:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { global-json-file: global.json, cache: true }
      - run: dotnet restore --locked-mode
      - name: Format
        run: dotnet format --verify-no-changes --severity info
      - name: Build with warnings as errors
        run: dotnet build -c Release --no-restore /warnaserror
      - name: Architecture tests
        run: dotnet test tests/Shop.ArchitectureTests -c Release --no-build --logger "trx"

  coverage:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    needs: static
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { global-json-file: global.json, cache: true }
      - run: dotnet restore --locked-mode
      - name: Tests with coverage
        run: >
          dotnet test -c Release --no-restore
          --collect:"XPlat Code Coverage" --results-directory coverage
      - name: Merge & gate
        run: |
          dotnet tool install -g dotnet-reportgenerator-globaltool
          reportgenerator -reports:"coverage/**/coverage.cobertura.xml" \
            -targetdir:coverage-report -reporttypes:"Cobertura;MarkdownSummaryGithub" \
            -assemblyfilters:"-*.Tests;-*.Designer"
          python3 scripts/coverage_gate.py coverage-report/Cobertura.xml 80
          cat coverage-report/SummaryGithub.md >> "$GITHUB_STEP_SUMMARY"

  secrets-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }        # التاريخ الكامل لكشف الأسرار المرفوعة سابقًا
      - name: gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  dependency-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: AGPL-1.0-only,AGPL-3.0-only   # عدّل حسب سياستك

  image-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build (no push)
        uses: docker/build-push-action@v6
        with: { context: ., push: false, tags: "local/orders:scan", sbom: true }
      - name: Trivy
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: local/orders:scan
          format: sarif
          output: trivy.sarif
          exit-code: "1"
          severity: CRITICAL,HIGH
          ignore-unfixed: true
      - uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: trivy.sarif }

  mutation:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { global-json-file: global.json, cache: true }
      - run: dotnet restore --locked-mode
      - name: Stryker (على مشروع واحد في كل مرة)
        run: |
          dotnet tool install -g dotnet-stryker
          # اسم راية الحد بيتغير بين الإصدارات (كانت threshold-break قديمًا):
          #   dotnet stryker --help   ← تحقق قبل الاعتماد عليها، أو ضع الحدود في stryker-config.json
          dotnet stryker -p src/Orders.Application/Orders.Application.csproj \
            --reporter markdown --break-at 50 --concurrency 4
      - uses: actions/upload-artifact@v4
        with: { name: mutation-report, path: "**/reports/**/*.md" }
'''},
        {"type": "code", "lang": "bash", "title": "scripts/quality-gates.sh — نفّذها محليًا قبل ما تدفع", "filename": "scripts/quality-gates.sh", "code": r'''#!/usr/bin/env bash
# نفس بوابات CI على جهازك: ما تدفعش commit يكسر الـpipeline.
set -uo pipefail          # بلا -e عشان نشوف كل الفحوصات لا أولها فقط
FAIL=0

run() { echo; echo "═══ $1 ═══"; shift; "$@" || { echo "✗ فشل"; FAIL=1; }; }

run "التنسيق"            dotnet format --verify-no-changes --severity info
run "البناء (تحذيرات=أخطاء)" dotnet build -c Release /warnaserror
run "اختبارات المعمارية"   dotnet test tests/Shop.ArchitectureTests -c Release --no-build
run "اختبارات الوحدة"      dotnet test tests/Shop.UnitTests -c Release --no-build \
                            --collect:"XPlat Code Coverage" --results-directory coverage

echo; echo "═══ بوابة التغطية ═══"
if command -v reportgenerator >/dev/null; then
  reportgenerator -reports:"coverage/**/coverage.cobertura.xml" \
    -targetdir:coverage-report -reporttypes:Cobertura >/dev/null
  python3 scripts/coverage_gate.py coverage-report/Cobertura.xml 80 || FAIL=1
else
  echo "ثبّت الأداة: dotnet tool install -g dotnet-reportgenerator-globaltool"
fi

echo; echo "═══ الأسرار ═══"
if command -v gitleaks >/dev/null; then gitleaks detect --source . --no-banner || FAIL=1
else echo "gitleaks غير مثبت (اختياري محليًا — CI بيفحصه)"; fi

echo
[ "$FAIL" = 0 ] && echo "✅ كل البوابات نجحت" || { echo "❌ فيه بوابات فشلت"; exit 1; }
'''},
        {"type": "code", "lang": "bash", "title": "scripts/coverage_gate.py — بوابة رقمية قابلة للتفاوض عليها", "filename": "scripts/coverage_gate.py", "code": r'''#!/usr/bin/env python3
"""بوابة تغطية: تفشل لو النسبة تحت الحد.
الاستخدام: python3 scripts/coverage_gate.py coverage-report/Cobertura.xml 80
ملاحظة: البوابة على المشروع كله قاسية للمشروعات القديمة؛
الأفضل (لما تتوفر الأداة) بوابة على **الكود المتغير** في الـPR."""
import sys
import xml.etree.ElementTree as ET

path, threshold = sys.argv[1], float(sys.argv[2])
root = ET.parse(path).getroot()
line_rate = float(root.attrib["line-rate"]) * 100
branch_rate = float(root.attrib.get("branch-rate", 0)) * 100

print(f"line coverage   = {line_rate:.1f}%  (threshold {threshold:.0f}%)")
print(f"branch coverage = {branch_rate:.1f}%")

# تفاصيل: أسوأ 5 ملفات (هي اللي تستاهل اختبارات):
worst = []
for cls in root.iter("class"):
    r = float(cls.attrib.get("line-rate", 0)) * 100
    worst.append((r, cls.attrib.get("filename", "?")))
for r, f in sorted(worst)[:5]:
    print(f"   {r:5.1f}%  {f}")

if line_rate < threshold:
    print(f"✗ FAIL: التغطية تحت الحد بنقص {threshold - line_rate:.1f} نقطة")
    sys.exit(1)
print("✓ PASS")
'''},

        # ── 3) المعمارية والعقود
        {"type": "heading", "level": 2, "text": "③ بوابتان بيحموا المعمارية والعقود (أغلى بوابتين لو اتكسروا)"},
        {"type": "code", "lang": "csharp", "title": "tests/Shop.ArchitectureTests/LayerTests.cs", "filename": "tests/Shop.ArchitectureTests/LayerTests.cs", "code": r'''using NetArchTest.Rules;
using Xunit;

namespace Shop.ArchitectureTests;

/// <summary>
/// قواعد المعمارية من المرحلة 4 — مفروضة آليًا بدل الـPR review.
/// أي مخالفة = اختبار فاشل = الـCI أحمر.
/// </summary>
public class LayerTests
{
    // Marker = نوع فارغ في كل مشروع للرجوع إليه (أو استخدم أي نوع موجود فعلًا في المشروع).
    private static readonly System.Reflection.Assembly Domain = typeof(Shop.Domain.Marker).Assembly;
    private static readonly System.Reflection.Assembly Application = typeof(Shop.Application.Marker).Assembly;
    private static readonly System.Reflection.Assembly Infrastructure = typeof(Shop.Infrastructure.Marker).Assembly;
    private static readonly System.Reflection.Assembly Api = typeof(Shop.Api.Marker).Assembly;

    [Fact]
    public void Domain_has_no_dependency_on_any_other_layer()
    {
        var result = Types.InAssembly(Domain)
            .ShouldNot().HaveDependencyOnAny(
                "Shop.Application", "Shop.Infrastructure", "Shop.Api",
                "Microsoft.EntityFrameworkCore", "Microsoft.AspNetCore", "Dapper")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "المجال اعتمد على طبقة أعلى: " + string.Join(", ", result.FailingTypeNames ?? Array.Empty<string>()));
    }

    [Fact]
    public void Application_does_not_know_about_EF_or_AspNet()
    {
        var result = Types.InAssembly(Application)
            .ShouldNot().HaveDependencyOnAny(
                "Microsoft.EntityFrameworkCore", "Microsoft.AspNetCore.Mvc")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "التطبيق تسرّب إليه تفاصيل البنية: " + string.Join(", ", result.FailingTypeNames ?? []));
    }

    [Fact]
    public void Api_does_not_reference_Infrastructure_directly()
    {
        // API يعتمد على Application (العقود) — والبنية تُحقن بالـDI من الـcomposition root فقط.
        var result = Types.InAssembly(Api)
            .That().ResideInNamespaceContaining("Features")
            .ShouldNot().HaveDependencyOn("Shop.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful, "handlers بتعرف تفاصيل البنية — اكسر الاعتماد بواجهة");
    }

    [Fact]
    public void Handlers_are_sealed_and_have_single_responsibility_shape()
    {
        // قاعدة فريق: كل handler اسمها *Handler ومغلقة (sealed) — تمنع التوريث الخفي.
        var result = Types.InAssembly(Application)
            .That().HaveNameEndingWith("Handler")
            .Should().BeSealed()
            .GetResult();

        Assert.True(result.IsSuccessful, "handlers غير مغلقة: " + string.Join(", ", result.FailingTypeNames ?? []));
    }

    [Fact]
    public void No_layer_leaks_into_tests_assemblies()
    {
        // اختبار بسيط لكن قيم: يمنع نسخ أنواع بين المشروعات (duplicated DTOs).
        var result = Types.InAssembly(Application)
            .ShouldNot().ResideInNamespaceContaining("Shop.Infrastructure")
            .GetResult();
        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void Modules_do_not_reference_each_other_internals()
    {
        // Modular monolith (4.2): الوصول فقط عبر العقود العامة.
        var result = Types.InAssembly(Application)
            .That().ResideInNamespaceContaining("Modules.Orders")
            .ShouldNot().HaveDependencyOn("Shop.Application.Modules.Catalog.Internal")
            .GetResult();

        Assert.True(result.IsSuccessful, "وحدة Orders بتعرف internals وحدة Catalog");
    }
}
'''},
        {"type": "code", "lang": "bash", "title": "scripts/contract-gates.sh — OpenAPI diff + Pact provider verification", "filename": "scripts/contract-gates.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts
BASE=docs/openapi/Orders.Api.json      # الخط الأساسي الملتزَم في المستودع

# ═══ 1) ولّد OpenAPI وقت البناء (بلا راية مخترعة) ═══
# في src/Orders.Api.csproj:
#   <PackageReference Include="Microsoft.Extensions.ApiDescription.Server" Version="10.*">
#     <PrivateAssets>all</PrivateAssets>
#     <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
#   </PackageReference>
#   <OpenApiGenerateDocuments>true</OpenApiGenerateDocuments>
#   <OpenApiGenerateDocumentsOnBuild>true</OpenApiGenerateDocumentsOnBuild>
#   <OpenApiDocumentsDirectory>$(MSBuildThisFileDirectory)../../docs/openapi</OpenApiDocumentsDirectory>
dotnet build src/Orders.Api -c Release
NEW=$(ls -t docs/openapi/*.json | head -n 1)
echo "المستند المولّد: $NEW"

# ═══ 2) قارن بالعقد الملتزَم — الكسر يُفشل البناء ═══
if command -v oasdiff >/dev/null; then
  # الراية --fail-on ترجع كود خروج غير صفري عند الكسر بمستوى ERR (تحقق في إصدارك):
  oasdiff breaking "$BASE" "$NEW" --fail-on ERR --format markdown | tee artifacts/openapi-breaking.md
else
  # بوابة بديلة رخيصة: أي تغيير في العقد لازم ييجي مع تحديث CHANGELOG في نفس الـPR
  if ! git diff --quiet "$BASE"; then
    git diff --name-only HEAD | grep -q "CHANGELOG-api.md" || {
      echo "✗ العقد اتغير من غير إدخال في CHANGELOG-api.md"; exit 1; }
    echo "⚠ العقد اتغير — تأكد إنه تغيير متوافق رجعيًا (2.1.x) ووثّقه"
  fi
  echo "oasdiff غير مثبت — البوابة الحقيقية تبقى اختبارات العقد (Pact) بالأسفل"
fi

# ═══ 2) تحقق المزوّد من عقود المستهلكين (5.3.3) ═══
dotnet test tests/Shop.ProviderVerificationTests -c Release \
  --filter "Category=ProviderVerification" --logger "trx;LogFileName=pact.trx"

# ═══ 3) تحديث الخط الأساسي = قرار صريح في الـPR (مش تلقائي) ═══
# بعد ما تتأكد إن التغيير متوافق رجعيًا (أو إنك عملت إصدارًا جديدًا):
#   cp "$NEW" "$BASE" && git add "$BASE" CHANGELOG-api.md
# ترك التحديث يدويًا مقصود: لو الـCI بيحدّث الأساس لوحده، الكسر هيمر من غير ما حد ياخد باله.
echo "الملف الجديد: $NEW | الأساس: $BASE"
'''},

        # ── 4) التبعيات والأمان
        {"type": "heading", "level": 2, "text": "④ التبعيات والأسرار: البوابات اللي بتمنع حادثة قبل ما تحصل"},
        {"type": "table", "caption": "أدوات الأمان والتبعيات في CI — وإعدادها الصحيح",
         "head": ["الخطر", "الأداة/الإعداد", "الإعداد الموصى به", "ملاحظة عملية"],
         "rows": [
             ["ثغرة في مكتبة/صورة", "Dependabot أو Renovate + Trivy/Scout",
              "تجميع التحديثات الصغيرة أسبوعيًا · تحديثات الأمان فورًا · `ignore-unfixed` للثغرات بلا حل",
              "بوت التحديثات بلا سياسة = 200 PR مفتوح ومحدش بيقرأ"],
             ["حزمة خبيثة/مشكوك فيها في PR", "`actions/dependency-review-action`",
              "`fail-on-severity: high` + قائمة تراخيص مرفوضة + كشف build scripts",
              "المراجعة بتظهر الحزم **الجديدة** فقط — وده اللي محتاج عين"],
             ["سر مرفوع في commit", "Secret scanning + push protection + gitleaks في CI",
              "فعّل push protection على المستودع · `fetch-depth: 0` في CI لكشف التاريخ",
              "**لو اتسرّب: دوّره أولًا**، ثم احذفه من التاريخ (6.2.3)"],
             ["كود خبيث في action خارجي", "pin بـSHA + مراجعة `permissions`",
              "ثبّت كل action خارجي على SHA · `permissions: contents: read` افتراضيًا",
              "tag بيتحرك = سلسلة إمداد مفتوحة"],
             ["صورة بلا مصدر معروف", "SBOM + provenance + cosign + attestations (6.1.3/6.3.1)",
              "لا تنشر صورة بلا SBOM وتوقيع",
              "عند ثغرة جديدة: `cosign verify` + SBOM يجاوبوا «هل أنا متأثر؟» في دقائق"],
             ["اعتماد على إصدار عائم", "lock files + `--locked-mode` + pin للإصدارات في csproj",
              "`RestorePackagesWithLockFile` · تجنب `*` في إصدارات الحزم",
              "إصدار عائم = بناء النهاردة غير بناء بكرة (وCI أخضر بشكل كاذب)"],
             ["تآكل المعمارية", "NetArchTest في CI (أعلاه)",
              "بوابة required check — مش اختيارية",
              "أرخص بوابة بأعلى قيمة: ثانية واحدة وتمنع شهور من إعادة الهيكلة"],
             ["اختبارات flaky", "عزل (quarantine) + سياسة",
              "ملصق `quarantine` + استبعاد من required checks + **issue بمهلة 14 يوم** ثم حذف",
              "البديل (تجاهلها) بيقتل ثقة الفريق في الـCI كله"],
         ]},
        {"type": "callout", "kind": "tip", "title": "ترتيب التفعيل (لا تفعّل كل حاجة في يوم)",
         "md": "**الأسبوع 1:** التنسيق + التحذيرات كأخطاء + اختبارات الوحدة (بوابة required). **الأسبوع 2:** بوابة التغطية على **الكود الجديد** فقط بحد منخفض (50%) + رفعها تدريجيًا. **الأسبوع 3:** اختبارات المعمارية (NetArchTest) + secret scanning. **الأسبوع 4:** فحص الصور (Trivy) + dependency review + SBOM/توقيع. **بعدها:** mutation testing على جدول أسبوعي + OpenAPI diff + Pact. كل أسبوع بوابة واحدة، وكل بوابة بتتعطّل لو فشلت 3 مرات بلا خطة."},

        {"type": "steps", "title": "⑤ خطة تفعيل البوابات على مشروع موجود (6 خطوات)",
         "items": [
             {"title": "1) قِس الوضع الحالي من غير ما تمنع حاجة",
              "md": "شغّل كل الفحوصات بوضع «تقرير فقط» (مش required checks): التغطية الحالية · عدد التحذيرات · الثغرات · مخالفات المعمارية. الأرقام دي بتحدد الحدود الواقعية.",
              "code": "bash scripts/quality-gates.sh 2>&1 | tee docs/quality-baseline.md"},
             {"title": "2) نظّف الديون الرخيصة أولًا",
              "md": "`dotnet format` على المشروع كله + إصلاح التحذيرات (أو suppress بتبرير) — ده بيخلي `warnaserror` ممكنًا من غير ألم.",
              "code": "dotnet format && dotnet build /warnaserror"},
             {"title": "3) فعّل البوابات السريعة كـrequired checks",
              "md": "التنسيق · البناء · اختبارات الوحدة · المعمارية. دي أقل من دقيقتين وبتدي أغلب القيمة.",
              "code": ""},
             {"title": "4) أضف بوابة التغطية على الكود الجديد",
              "md": "حد منخفض في البداية (50%) وزيده كل ربع سنة. الأهم: **لا تُخفض الحد أبدًا لتبرير فشل** — خفضه مرة واحدة بيقتل مصداقيته.",
              "code": ""},
             {"title": "5) أضف بوابات الأمان (صور + تبعيات + أسرار)",
              "md": "Trivy على الصورة · dependency review على PRs · push protection · SBOM وتوقيع لكل صورة منشورة.",
              "code": ""},
             {"title": "6) البوابات البطيئة على جدول",
              "md": "mutation testing أسبوعيًا + OpenAPI diff عند تغيير `src/…/Endpoints` + Pact provider verification قبل النشر. وراقب زمن الـpipeline شهريًا.",
              "code": ""},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق بين «CI بيشتغل» و«بوابة required» — ومن غير required checks الـCI نصيحة.",
            "أقدر أكتب بوابة تغطية رقمية (سكربت يقرأ Cobertura ويفشل تحت الحد) وأفهم ليه البوابة على **الكود الجديد** أفضل.",
            "أقدر أكتب اختبارات معمارية بـNetArchTest تمنع تسريب EF/ASP.NET للطبقات العليا.",
            "أعرف إمتى أشغّل mutation testing (على جدول، بحد `break-at`) وليه مش على كل PR.",
            "أقدر أفعّل dependency review وsecret scanning وأتعامل مع تسريب سر بالترتيب الصح (تدوير ثم حذف).",
            "أعرف سياسة التعامل مع flaky tests (عزل + issue + مهلة + حذف) وليه التجاهل أخطر.",
            "عندي خطة تفعيل تدريجية (بوابة كل أسبوع) بدل تفعيل كل شيء مرة واحدة.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على البوابات.",
         "questions": [
             {"q": "مشروع قديم بتغطية 35%. حطيت بوابة 80% على المشروع كله. النتيجة المتوقعة؟",
              "options": ["الفريق هيكتب اختبارات بسرعة", "**الـCI هيبقى أحمر دايمًا فبيتجاهلوه أو بيعطّلوه** — الصح: بوابة على الكود الجديد/المتغير وحد عام منخفض يُرفع تدريجيًا", "التغطية هترتفع تلقائيًا", "مفيش مشكلة"],
              "answer": 1,
              "explain": "بوابة مستحيلة = بوابة معطّلة. الخطة: حد على الكود المتغير (مثال 80%) + حد عام واقعي (مثال 50%) يُرفع كل ربع سنة، وممنوع تخفيضه لتبرير فشل."},
             {"q": "التغطية 92% لكن mutation score 40%. ده معناه إيه؟",
              "options": ["الاختبارات ممتازة", "**الاختبارات بتنفّذ الكود من غير ما تتحقق من سلوكه** (assertions ضعيفة) — الطفرات بتكشف ده", "الأداة غلط", "التغطية محسوبة غلط"],
              "answer": 1,
              "explain": "الـmutation testing بيعدّل الكود عمدًا (مثل `<` إلى `<=`) ولو الاختبارات فضلت خضرا فمعناه إنها ما بتفحصش النتيجة. ده سبب إن mutation بوابة قيمة حتى مع تغطية عالية."},
             {"q": "ليه اختبارات المعمارية (NetArchTest) من أعلى البوابات قيمة؟",
              "options": ["لأنها بطيئة", "**لأنها تمنع تآكل المعمارية في ثوانٍ، وديون المعمارية أغلى بكتير من ديون الاختبارات** — إعادة هيكلة بعد سنة أصعب من رفض PR النهاردة", "لأنها بديل للاختبارات", "لأنها بتقيس التغطية"],
              "answer": 1,
              "explain": "قاعدة «Domain ما يعرفش EF» بتتكسر تدريجيًا في PRs صغيرة، ولو اكتُشفت بعد سنة = إعادة هيكلة كبيرة. الاختبار بيمنعها في ثانية."},
             {"q": "اختبار تكامل بينجح 9 مرات ويفشل مرة عشوائيًا. التصرف؟",
              "options": ["أعد تشغيله لحد ما ينجح", "**اعزله (quarantine) فورًا من required checks + افتح issue بمهلة إصلاح (مثال 14 يوم) ثم احذفه أو أصلحه**", "احذفه مباشرة", "اتركه — 90% كفاية"],
              "answer": 1,
              "explain": "إعادة التشغيل بتخفي المشكلة وبتقتل الثقة. الحذف المباشر بيخسر تغطية. العزل بمهلة = تحافظ على الإشارات وتمنع تآكل الثقة. وغالبًا السبب: اعتماد على الوقت/الترتيب/منفذ مشترك/بيانات متشاركة (1.2.5)."},
             {"q": "Trivy لقى ثغرة HIGH في مكتبة أساسية ومفيش إصدار مُصلَح. تعمل إيه؟",
              "options": ["تعطّل الفحص", "**`--ignore-unfixed` للثغرات بلا إصلاح متاح + issue موثّق فيه التعويض (WAF/تقييد شبكة/تقليل الصلاحيات) + متابعة للتحديث**", "تحذف المكتبة", "تنشر على أي حال من غير توثيق"],
              "answer": 1,
              "explain": "الهدف: البوابة تفضل صارمة على **القابل للإصلاح** (وإلا هتتعطّل)، مع مسار معلن وغير قابل للتجاهل للباقي. والتوثيق بيخلي القرار قابل للمراجعة بدل ما يبقى إخفاءً."},
             {"q": "ليه SBOM + توقيع الصورة مش «ترف أمني»؟",
              "options": ["مطلوب من GitHub", "**بدونهم ما تعرفش إنك متأثر بثغرة جديدة**: SBOM بيجاوب «أيه اللي جوه صورتي؟» والتوقيع بيثبت «الصورة دي من build بتاعي» — في دقائق بدل أيام", "بيقلل حجم الصورة", "بيسرع النشر"],
              "answer": 1,
              "explain": "لما تطلع ثغرة في مكتبة، السؤال الأول: «أي من صورنا فيها المكتبة دي وبأي إصدار؟» من غير SBOM الإجابة بتاخد أيام من البحث اليدوي."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "بوابات شغالة + قياس أثرها.",
         "items": [
             {"id": "t1", "title": "مهمة 1: فعّل 5 بوابات على مشروعك وقِس أثرها",
              "md": "**السياق:** مشروعك فيه CI (6.3.1) لكن بلا بوابات حقيقية.\n\n**المطلوب:**\n1. `docs/quality-baseline.md`: قياس الوضع الحالي (التغطية · عدد التحذيرات · الثغرات في الصورة · مخالفات المعمارية · زمن الـpipeline) — **قبل** تفعيل أي بوابة.\n2. فعّل 5 بوابات كـ**required checks**: التنسيق/التحذيرات · اختبارات الوحدة · **بوابة التغطية** (سكربت `coverage_gate.py`) · **اختبارات المعمارية** (NetArchTest بـ4 قواعد على الأقل) · **secret scanning**.\n3. أضف بوابة سادسة على جدول أسبوعي: Trivy على الصورة أو Stryker على مشروع واحد (اختَر وبرر الاختيار بالزمن/القيمة).\n4. `scripts/quality-gates.sh` يشغّل نفس البوابات محليًا (بدون CI) وبيطبع ملخصًا.\n5. **اختبار عكسي**: لكل بوابة، ارفع PR يكسرها عن قصد (تغيير تنسيق · اختبار فاشل · حذف اختبار لتقليل التغطية · اعتماد `Domain` على EF · سر تجريبي في ملف) ووثّق إن كل واحدة **فشّلت البناء** — مع لقطة/مخرج.\n6. سياسة flaky tests مكتوبة في `docs/testing-policy.md`: تعريف · عزل · مهلة · مصير الاختبار المعزول.\n7. بعد أسبوع: قِس أثر البوابات (عدد الفشل المُلتقَط قبل الدمج · زمن الـpipeline · أي بوابة اتكسرت كذبًا false positive) واكتب الخلاصة في `docs/quality-baseline.md`.",
              "criteria": [
                  "قياس **قبل** و**بعد** بأرقام (مش انطباع).",
                  "5 بوابات required checks فعلًا (لقطة من إعدادات branch protection).",
                  "بوابة التغطية بسكربت مستقل يعمل محليًا وفي CI بنفس الحد.",
                  "4 قواعد معمارية على الأقل، وكل قاعدة برسالة فشل مفهومة (بتقول إيه النوع المخالف).",
                  "secret scanning شغال على التاريخ الكامل (`fetch-depth: 0`) + push protection مفعّل.",
                  "البوابة السادسة (Trivy أو Stryker) على جدول مع تبرير الاختيار.",
                  "5 اختبارات عكسية موثقة (كل بوابة كُسرت عن قصد وفشّلت البناء).",
                  "سياسة flaky tests مكتوبة بمهلة ومصير واضح.",
                  "خلاصة أسبوع: الفشل المُلتقَط + زمن الـpipeline + أي false positives وخطة لها.",
              ],
              "hint": "أصعب خطوة عمليًا: `warnaserror` في مشروع فيه تحذيرات قديمة. الحل: شغّل `dotnet format` أولًا، وبعدين أصلح التحذيرات بالتدريج أو استخدم `<NoWarn>` **بقائمة محددة وتعليق يبرر كل واحدة** (مش تعطيل شامل). وللأسرار التجريبية: استخدم قيمة وهمية واضحة مثل `AKIAIOSFODNN7EXAMPLE` وتأكد إنها مكتشفة ثم احذفها فورًا.",
              "solution": "الترتيب النموذجي والنتائج: القياس قبل = تغطية 42% · 87 تحذيرًا · 3 ثغرات HIGH في الصورة · 6 مخالفات معمارية · زمن pipeline 6 دقائق. بعد التنظيف (format + إصلاح تحذيرات + suppress موثّق) → التحذيرات صفر فـ`warnaserror` بقى ممكن. البوابات الخمس اشتغلت واختبارات المعمارية كشفت إن `Domain` بيستورد `Microsoft.EntityFrameworkCore` في مكانين (عادةً بسبب attributes مثل `[Required]` من DataAnnotations — الحل: استبدلها بأنواع المجال أو انقلها لطبقة التطبيق). الاختبارات العكسية الخمسة كلها فشّلت البناء. بعد أسبوع: 11 محاولة دمج اتكسرت قبل الوصول لـmain (7 تنسيق/تحذيرات · 2 تغطية · 1 معمارية · 1 اختبار) وfalse positive واحد (قاعدة معمارية صارمة على مشروع الاختبارات نفسه → استُثنيت بـ`.That().ResideOutsideOfNamespace`). زمن الـpipeline بقى 4:30 بعد الكاش.",
              "resources": [
                  "https://github.com/BenMorris/NetArchTest",
                  "https://github.com/danielpalme/ReportGenerator",
                  "https://stryker-mutator.io/docs/stryker-net/Introduction/",
                  "https://github.com/gitleaks/gitleaks",
                  "https://trivy.dev/latest/docs/",
                  "https://docs.github.com/en/code-security/secret-scanning",
                  "https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview",
              ]},
             {"id": "t2", "title": "مهمة 2: بوابة العقود — OpenAPI diff + Pact provider verification",
              "md": "**السياق:** API مستهلك من عميلين (ويب وتطبيق موبايل) — أي كسر في العقد بيبقى حادثة.\n\n**المطلوب:**\n1. صدّر OpenAPI من التطبيق كخطوة بناء (أو أمر) وثبّته في `docs/openapi/main.json`.\n2. `scripts/contract-gates.sh`: يصدّر النسخة الجديدة · يقارنها · **يفشل عند الكسر** · ويطبع جدول التغييرات في ملخص الـPR.\n3. اختبارات **provider verification** بـPact (5.3.3) تعمل في CI ضد عقود المستهلكين المنشورة، وتُشغَّل قبل أي نشر.\n4. سياسة إصدارات مكتوبة في `docs/api-versioning.md`: إيه اللي يُعتبر كسرًا (حذف مسار/حقل · تغيير نوع · إضافة حقل مطلوب) وإيه اللي مسموح (إضافة حقل اختياري · مسار جديد) — والمسار المطلوب عند الكسر (إصدار جديد + expand/contract من 3.5 + إعلان للمستهلكين).\n5. **اختبار عكسي**: احذف حقلًا من استجابة موجودة وغيّر نوعًا، ووثّق إن البوابة فشّلت البناء **قبل** الدمج.\n6. أضف فحصًا بسيطًا للتوافق الرجعي في الاختبارات: اختبار وحدة يفك تشفير **مثال استجابة قديم محفوظ** (golden file) بالنموذج الحالي — بيكشف كسر deserialization عند العملاء.\n7. اكتب في `docs/contract-runbook.md`: إيه اللي أعمله لو البوابة فشلت (3 مسارات: تراجع عن التغيير · إصدار جديد · تفاوض مع المستهلك).",
              "criteria": [
                  "OpenAPI مُصدَّر آليًا ومثبت في المستودع كمرجع للمقارنة.",
                  "مقارنة تكتشف الكسر وتُفشل البناء (موثّق بتجربة عكسية).",
                  "ملخص التغييرات يظهر في الـPR (تعليق أو `GITHUB_STEP_SUMMARY`) بصيغة مقروءة.",
                  "Pact provider verification يعمل في CI ومطلوب قبل النشر.",
                  "سياسة إصدارات واضحة بقائمة «كسر» و«مسموح» ومسار التعامل مع الكسر.",
                  "اختبار golden file لفك تشفير استجابة قديمة بالنموذج الحالي.",
                  "runbook بثلاثة مسارات عند فشل البوابة.",
                  "ملاحظة صريحة عن حدود أداة المقارنة (بعض التغييرات الدلالية لا تُكشف) وأن اختبارات العقد هي الحماية الحقيقية.",
              ],
              "hint": "لو أداة مقارنة OpenAPI مش متاحة عندك، ابدأ بأبسط بوابة فعالة: **فشل الـPR لو `docs/openapi/main.json` اتغير من غير ملف `CHANGELOG-api.md` مُحدَّث** (فحص في CI بمقارنة المسارات المتغيرة). دي بوابة رخيصة وبتمنع «تغيير صامت في العقد». وPact بيغطي الباقي لأنه بيختبر السلوك مش الشكل.",
              "solution": "البوابة المركّبة: (1) CI يصدّر OpenAPI → يقارن بـ`docs/openapi/main.json` → لو فيه تغييرات كاسرة (حذف مسار/خاصية · تغيير نوع · خاصية جديدة مطلوبة) يفشل ويطبع الجدول (2) لو التغيير مسموح (إضافة اختيارية) ينجح ويطلب تحديث changelog (3) Pact provider verification يعمل ضد العقود المنشورة — وده اللي بيكشف الكسر الدلالي اللي مش بيبان في المخطط (4) اختبار golden file: `sample-order-response-v1.json` محفوظ + `JsonSerializer.Deserialize<OrderResponseV1>` + assertions على الحقول القديمة. التجربة العكسية: حذف `orderId` من الاستجابة → فشل في (1) و(3) و(4) معًا؛ تغيير نوعه من `string` إلى `Guid` → فشل في (1) و(4). الـrunbook: تراجع عن التغيير (الأرخص) · إصدار جديد `v2` مع expand/contract (للتغيير المطلوب) · تفاوض مع المستهلك (لو المستهلك داخلي وقابل للتحديث في نفس الأسبوع).",
              "resources": [
                  "https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/aspnetcore-openapi",
                  "https://docs.pact.io/",
                  "https://github.com/pact-foundation/pact-net",
                  "https://learn.microsoft.com/en-us/aspnet/core/web-api/jsonpatch",
                  "https://github.com/Tufin/oasdiff",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "تحليل الكود في .NET (analyzers)", "url": "https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview"},
            {"label": "NetArchTest", "url": "https://github.com/BenMorris/NetArchTest"},
            {"label": "ReportGenerator (دمج تقارير التغطية)", "url": "https://github.com/danielpalme/ReportGenerator"},
            {"label": "Stryker.NET (اختبار الطفرات)", "url": "https://stryker-mutator.io/docs/stryker-net/Introduction/"},
            {"label": "Trivy", "url": "https://trivy.dev/latest/docs/"},
            {"label": "dependency-review-action", "url": "https://github.com/actions/dependency-review-action"},
            {"label": "Secret scanning وpush protection", "url": "https://docs.github.com/en/code-security/secret-scanning"},
            {"label": "Pact: اختبارات العقد", "url": "https://docs.pact.io/"},
            {"label": "Dependabot: إعداد التحديثات", "url": "https://docs.github.com/en/code-security/dependabot/working-with-dependabot-updates"},
        ]},
    ],
}

LESSONS_S6_H = [_L1, _L2]
