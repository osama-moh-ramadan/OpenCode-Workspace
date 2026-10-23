"""Stage 6, Module 1 — Docker & isolated compute (lesson 3): image size & security."""

TODAY = "2026-10-22"

LESSONS_S6_B = [
    {
        "id": "s6-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
حجم الصورة مش موضوع «توفير مساحة» — ده **ثلاث تكاليف حقيقية**:
1. **زمن السحب**: صورة 800MB على node جديدة = دقايق قبل ما الخدمة تشتغل (وبطء في الـrollout والـautoscaling).
2. **سطح الهجوم**: كل حزمة في الصورة = ثغرات محتملة (CVEs) + أدوات يفيد المهاجم (shell، package manager، curl).
3. **التكلفة**: تخزين ونقل في الـregistry، وذاكرة/قرص على الـnodes.

بس **التصغير مش الهدف الوحيد**: الصورة الآمنة = صغيرة + non-root + بلا أدوات غير ضرورية + مفحوصة + موقّعة + مثبّتة بـdigest.
الدرس ده بيديك الأرقام الحقيقية لصور .NET 10، وخيارات قواعد الصور، وأوامر الفحص، وتصليد وقت التشغيل —
وكمان **الفخ اللي بيقع فيه أغلب المطورين العرب**: صور chiseled/alpine **ما فيهاش ICU** → سلوك مختلف للفرز/التنسيق العربي.
"""},
            {"type": "terms", "items": [
                {"term": "Chiseled (Ubuntu)", "def": "صورة distroless مبنية بـ`chisel`: بلا shell، بلا package manager، بلا أدوات شبكة، non-root افتراضيًا. `aspnet:10.0-noble-chiseled`."},
                {"term": "`-extra` variant", "def": "نفس الصورة **+ icu + tzdata** — مطلوبة لأي تطبيق بيستخدم ثقافات/مناطق زمنية (`noble-chiseled-extra`)."},
                {"term": "Alpine", "def": "توزيعة musl صغيرة جدًا (`aspnet:10.0-alpine`). صغيرة ومرنة، بس musl ≠ glibc (فروق في السلوك والأداء في حالات معينة)."},
                {"term": "runtime-deps", "def": "أصغر قاعدة: مكتبات النظام فقط — بتُستخدم مع نشر **self-contained** أو **NativeAOT** (التطبيق شايل الـruntime بتاعه)."},
                {"term": "Globalization Invariant Mode", "def": "`DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true` — تشغيل بلا ICU: بلا ثقافات، بلا فرز/مقارنة لغوية صحيحة، تنسيق أرقام/تواريخ مبسّط."},
                {"term": "Non-root (APP_UID)", "def": "مستخدم `app` بـUID **1654** موجود في كل صور .NET 8+؛ `USER $APP_UID` هو النمط الموصى به."},
                {"term": "Read-only root FS", "def": "نظام ملفات الحاوية للقراءة فقط + `tmpfs` للمسارات القابلة للكتابة — يمنع تثبيت أدوات/تعديل ملفات بعد الاختراق."},
                {"term": "Capability drop / no-new-privileges", "def": "إسقاط صلاحيات Linux غير المستخدمة (`cap_drop: [ALL]`) ومنع تصعيد الصلاحيات — يقلل أثر أي اختراق."},
                {"term": "CVE", "def": "Common Vulnerabilities and Exposures — معرّف لثغرة معروفة. المهم: **الثغرات القابلة للاستغلال/القابلة للإصلاح** مش العدد المطلق."},
                {"term": "SBOM", "def": "Software Bill of Materials — قائمة مكونات الصورة/التطبيق (CycloneDX/SPDX). أساس فحص الثغرات المستمر والامتثال."},
                {"term": "Image signing / attestation", "def": "توقيع الصورة (cosign/Notation) وإثباتات بناء — عشان النشر يكون من صور موثوقة المصدر فقط."},
                {"term": "Digest pinning", "def": "الإشارة للصورة بـ`@sha256:…` بدل `:tag` — يضمن إنك بتشغّل نفس البايتات بالظبط (وبيقفل باب «اتغيّرت من غير ما أعرف»)."},
                {"term": "Ephemeral debug container", "def": "حاوية تشخيص مؤقتة تُحقن جنب حاوية بلا shell (`kubectl debug`) — بديل تثبيت curl جوه الصورة."},
            ]},
            {"type": "heading", "level": 2, "text": "1) الأرقام الحقيقية: حجم صور .NET 10 (compressed)"},
            {"type": "table", "head": ["قاعدة الصورة", "نوع النشر", "distroless", "Globalization (ICU)", "الحجم المضغوط", "ملاحظة"], "rows": [
                ["`aspnet:10.0-noble-chiseled`", "framework-dependent", "✓", "✗", "**52.81 MB**", "★ الخيار المتوازن: صغير + بلا shell"],
                ["`aspnet:10.0-noble-chiseled-extra`", "framework-dependent", "✓", "✓", "**67.68 MB**", "لازم لأي تطبيق بيستخدم ثقافات/مناطق زمنية (فرز عربي، تنسيق تواريخ)"],
                ["`aspnet:10.0-alpine`", "framework-dependent", "✗", "✗", "**51.93 MB**", "musl + فيه shell/`apk` (تشخيص أسهل)"],
                ["`aspnet:10.0-alpine-extra`", "framework-dependent", "✗", "✓", "**66.50 MB**", "تحقق من توفر الوسم في إصدارك (التوثيق بيذكر توفره على runtime-deps أكيد)"],
                ["`runtime-deps:10.0-noble-chiseled`", "self-contained + trimming", "✓", "✗", "**21.86 MB**", "بلا runtime مشترك — التطبيق شايل كل حاجة"],
                ["`runtime-deps:10.0-noble-chiseled`", "**NativeAOT**", "✓", "✗", "**11.60 MB**", "أصغر خيار عملي — بس AOT له قيود (reflection/EF Core)"],
                ["`runtime-deps:10.0-alpine`", "NativeAOT", "✗", "✗", "**10.69 MB**", "أصغر على الإطلاق"],
                ["`aspnet:10.0` (Debian bookworm/trixie)", "framework-dependent", "✗", "✓", "~100–110 MB", "الافتراضي: فيه shell وأدوات — تشخيص أسهل، سطح هجوم أكبر"],
                ["`aspnet:10.0-noble` (Ubuntu كامل)", "framework-dependent", "✗", "✓", "~90 MB مضغوط / ~220 MB مفكوك", "لما تحتاج حزم نظام فعلًا"],
                ["`sdk:10.0`", "—", "✗", "✓", "~800 MB", "★ للبناء فقط — ما توصلش للصورة النهائية أبدًا"],
            ]},
            {"type": "callout", "kind": "note", "title": "الأرقام بتتغير — قِس بنفسك دايمًا",
             "md": """
الأرقام فوق من تقرير الأحجام الرسمي لصور .NET 10 (الحجم **المضغوط** في الـregistry).
الحجم المفكوك على القرص أكبر بـ2–3×. **قِس صورتك الفعلية**:
```bash
docker images shop/orders --format '{{.Repository}}:{{.Tag}} → {{.Size}}'
docker image inspect shop/orders:1.4.0 --format 'layers={{len .RootFS.Layers}}'
docker history shop/orders:1.4.0 --format 'table {{.Size}}\\t{{.CreatedBy}}' | head -15
```
**القاعدة العملية**: صورة .NET service معقولة = **أقل من 120MB مفكوكة** (framework-dependent)
أو **أقل من 60MB** (self-contained/AOT). لو أكبر، فيه حاجة غلط (طبقة build تسربت، حزم نظام، ملفات بيانات).

⚠ **الحجم مش مقياس الأمان الوحيد**: صورة صغيرة فيها تطبيق مصاب بـSSRF أخطر من صورة كبيرة مضبوطة الصلاحيات.
الأمان = حجم معقول + non-root + read-only + cap_drop + بلا ثغرات حرجة قابلة للإصلاح + digest ثابت.
"""},
            {"type": "heading", "level": 2, "text": "2) ثلاث صور: chiseled · AOT · مع دعم الثقافة العربية"},
            {"type": "code", "lang": "dockerfile", "filename": "src/Shop.Orders/Dockerfile.chiseled", "title": "A) chiseled + non-root + read-only friendly (الأصغر عمليًا لخدمة ويب)", "code": r'''
# syntax=docker/dockerfile:1

# ══════ البناء ══════
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
ARG TARGETARCH
WORKDIR /src

COPY src/Shop.Orders/Shop.Orders.csproj                   src/Shop.Orders/
COPY src/Shop.Contracts/Shop.Contracts.csproj             src/Shop.Contracts/
COPY src/Shop.ServiceDefaults/Shop.ServiceDefaults.csproj src/Shop.ServiceDefaults/

RUN --mount=type=cache,id=nuget-${TARGETARCH},target=/root/.nuget/packages \
    dotnet restore src/Shop.Orders/Shop.Orders.csproj --arch "${TARGETARCH}" --os linux /p:UseAppHost=false

COPY . .

RUN --mount=type=cache,id=nuget-${TARGETARCH},target=/root/.nuget/packages \
    dotnet publish src/Shop.Orders/Shop.Orders.csproj \
        -c "${BUILD_CONFIGURATION}" --arch "${TARGETARCH}" --os linux --no-restore \
        /p:UseAppHost=false /p:InvariantGlobalization=false \
        -o /app/publish

# ══════ التشغيل: distroless chiseled ══════
# ★ -extra لأننا محتاجين ICU + tzdata:
#   • فرز/مقارنة نص عربي (ORDER BY collation، StringComparison)
#   • تنسيق عملات/تواريخ (EGP، تقويم هجري)
#   • مناطق زمنية (Africa/Cairo) — بلا tzdata كل التوقيتات هتبقى UTC بدون تحويل
FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled-extra AS final

ENV ASPNETCORE_HTTP_PORTS=8080 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_gcServer=1 \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false \
    DOTNET_EnableDiagnostics=0

WORKDIR /app
COPY --from=build /app/publish .

# ✓ non-root: UID 1654 (موجود في الصورة) — النمط الموصى به USER $APP_UID
USER $APP_UID

EXPOSE 8080
ENTRYPOINT ["dotnet", "Shop.Orders.dll"]

# ── ملاحظات تشغيلية ──
# • مفيش shell في chiseled: `docker exec … sh` هيفشل. التشخيص:
#     docker logs · docker exec لأمر من التطبيق · ephemeral container في K8s (kubectl debug)
#     أو تنسخ ملفات بـ: docker create + docker cp
# • DOTNET_EnableDiagnostics=0 بيقفل pipes الخاصة بالـdiagnostics (أصغر سطح هجوم) —
#   فعّلها فقط وقت التشخيص.
# • لو محتاج صورة أصغر ومش محتاج ثقالات: noble-chiseled + DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true
#   (اختبر الفرز/التنسيق العربي قبل ما تعتمد ده!)
'''},
            {"type": "code", "lang": "dockerfile", "filename": "src/Shop.Notifications/Dockerfile.aot", "title": "B) NativeAOT — أصغر صورة وأعلى أداء إقلاع (لقيود واضحة)", "code": r'''
# syntax=docker/dockerfile:1

# ══════ البناء: AOT بيحتاج أدوات النظام (clang/zlib) — موجودة في صورة SDK ══════
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG TARGETARCH
WORKDIR /src

COPY src/Shop.Notifications/Shop.Notifications.csproj src/Shop.Notifications/
COPY src/Shop.Contracts/Shop.Contracts.csproj         src/Shop.Contracts/

RUN --mount=type=cache,id=nuget-aot,target=/root/.nuget/packages \
    dotnet restore src/Shop.Notifications/Shop.Notifications.csproj --arch "${TARGETARCH}" --os linux

COPY . .

# ★ NativeAOT: يترجم لملف تنفيذي أصلي واحد — إقلاع أسرع وذاكرة أقل وحجم أصغر بكثير
#   القيود: reflection ديناميكي محدود · EF Core يحتاج source-generated/compiled models ·
#   بعض المكتبات مش متوافقة → راقب تحذيرات IL2xxx/IL3xxx واعتبرها أخطاء
RUN --mount=type=cache,id=nuget-aot,target=/root/.nuget/packages \
    dotnet publish src/Shop.Notifications/Shop.Notifications.csproj \
        -c Release --arch "${TARGETARCH}" --os linux \
        /p:PublishAot=true \
        /p:IlcOptimizationPreference=Size \
        /p:InvariantGlobalization=false \
        /p:TreatWarningsAsErrors=true \
        -o /app/publish

# ══════ التشغيل: runtime-deps (أصغر قاعدة) ══════
FROM mcr.microsoft.com/dotnet/runtime-deps:10.0-noble-chiseled-extra AS final

ENV ASPNETCORE_HTTP_PORTS=8080 \
    DOTNET_RUNNING_IN_CONTAINER=true

WORKDIR /app
COPY --from=build /app/publish .

USER $APP_UID
EXPOSE 8080

# ✓ AOT بينتج ملف تنفيذي أصلي — مش `dotnet App.dll`
ENTRYPOINT ["./Shop.Notifications"]

# ── بديل بلا Dockerfile خالص (نشر من SDK مباشرة) ──
#   dotnet publish src/Shop.Notifications -c Release /t:PublishContainer \
#     -p ContainerBaseImage=mcr.microsoft.com/dotnet/runtime-deps:10.0-noble-chiseled-extra \
#     -p ContainerRepository=ghcr.io/<org>/shop-notifications \
#     -p ContainerImageTag=1.4.0
#   (فيه كمان خاصية ContainerFamily=alpine/noble-chiseled لاختيار القاعدة — تحقق من توثيق إصدارك)
'''},
            {"type": "code", "lang": "bash", "title": "قياس · فحص ثغرات · SBOM · توقيع · تشخيص بلا shell", "code": r'''
# ═══ 1) القياس (قبل أي تحسين — سجّل الأرقام) ═══
docker build -f src/Shop.Orders/Dockerfile.chiseled -t shop/orders:chiseled .
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E 'shop/|REPOSITORY'
docker history shop/orders:chiseled --format 'table {{.Size}}\t{{.CreatedBy}}' | head -20
docker run --rm --entrypoint dotnet shop/orders:chiseled --info | head -5   # ← يفشل في chiseled (بلا entrypoint متاح)

# ═══ 2) فحص الثغرات (Trivy — الأشهر ومجاني) ═══
trivy image --scanners vuln --severity CRITICAL,HIGH \
            --ignore-unfixed \                 # ★ ركّز على اللي فيه إصلاح فعلًا
            --exit-code 1 \                    # ← gate في CI
            shop/orders:chiseled
trivy image --format table --severity CRITICAL shop/orders:chiseled | head -40
trivy fs --scanners vuln,misconfig .           # تبعيات الكود + أخطاء تكوين (Dockerfile/compose/K8s)
trivy config --exit-code 1 .                   # misconfiguration في Dockerfile/manifests

# بديل/مكمّل: Docker Scout
docker scout quickview shop/orders:chiseled
docker scout cves --only-severity critical shop/orders:chiseled

# ═══ 3) SBOM (قائمة المكونات — للفحص المستمر والامتثال) ═══
trivy image --format cyclonedx --output sbom.cdx.json shop/orders:chiseled
trivy sbom --severity CRITICAL,HIGH sbom.cdx.json          # ✓ افحص الـSBOM نفسه (يفضل شغال بعد النشر)
# في CI: action جاهز (microsoft/sbom-action) — راجع درس 6.3.2

# ═══ 4) التوقيع والتحقق (منع صور مجهولة المصدر من النشر) ═══
cosign sign --yes ghcr.io/<org>/shop-orders@sha256:<digest>
cosign verify --certificate-identity-regexp 'https://github.com/<org>/.*' \
              --certificate-oidc-issuer https://token.actions.githubusercontent.com \
              ghcr.io/<org>/shop-orders@sha256:<digest>

# ═══ 5) تثبيت بالـdigest (مش tag) ═══
docker inspect shop/orders:chiseled --format '{{index .RepoDigests 0}}'
#   → shop/orders@sha256:abc…  ← ده اللي يتحط في manifests الإنتاج

# ═══ 6) التشغيل المتصلد محليًا (اقرأ الجدول تحت) ═══
docker run -d --name hardened \
  --user 1654:1654 \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --pids-limit 256 \
  --memory 512m --cpus 1.0 \
  -p 127.0.0.1:8080:8080 \
  shop/orders:chiseled

# تحقق إن التطبيق لسه شغال (read-only ممكن يكسر أي كتابة على القرص)
curl -s -o /dev/null -w 'health %{http_code}\n' http://localhost:8080/health
docker exec hardened id 2>&1 | head -1          # ← هيفشل في chiseled (بلا shell) — ده متوقع

# ═══ 7) تشخيص بلا shell (chiseled/distroless) ═══
docker logs --tail 200 hardened
docker inspect hardened --format '{{json .State}}'
docker create --name tmp shop/orders:chiseled && docker cp tmp:/app ./app-dump && docker rm tmp
# في Kubernetes: حاوية تشخيص مؤقتة جنب الحاوية المستهدفة
kubectl debug -it pod/shop-orders-xxx --image=mcr.microsoft.com/dotnet/sdk:10.0 \
              --target=orders -- /bin/bash
'''},
            {"type": "table", "head": ["الخطر", "إزاي تكتشفه", "الإصلاح"], "rows": [
                ["الحاوية بتشتغل بـroot", "`docker exec … id` أو `docker inspect --format '{{.Config.User}}'` فارغ", "`USER $APP_UID` في Dockerfile + `runAsNonRoot: true` في K8s"],
                ["صورة `:latest` أو tag متغير", "`docker inspect` + manifests", "tag بإصدار/commit sha + **digest** في manifests الإنتاج"],
                ["أسرار في الطبقات", "`docker history` + `trivy image --scanners secret`", "احذف من Dockerfile، لفّ السر فورًا، واستخدم runtime env/Key Vault (درس 6.2.3)"],
                ["CVEs حرجة قابلة للإصلاح", "`trivy image --severity CRITICAL --ignore-unfixed --exit-code 1`", "حدّث قاعدة الصورة والحزم (rebase شهري) + gate في CI"],
                ["shell + package manager جوه الصورة", "`docker exec … sh` نجح", "استخدم chiseled/distroless أو alpine بدون أدوات (وشخّص من بره)"],
                ["نظام ملفات قابل للكتابة", "تشغيل بلا `--read-only`", "`read_only: true` + `tmpfs /tmp` للمسارات المطلوبة فقط"],
                ["صلاحيات Linux زائدة", "بلا `cap_drop`", "`cap_drop: [ALL]` وأضف فقط المطلوب نادرًا + `no-new-privileges`"],
                ["منافذ إدارة مكشوفة (15672/pgAdmin/5432)", "`docker compose ps` / manifests", "loopback فقط محليًا، وبلا كشف خالص في الإنتاج (NetworkPolicy في K8s)"],
                ["بلا حدود موارد", "`docker stats` / manifests", "`mem_limit`/`cpus` (compose) و`resources.limits` (K8s) — درس 6.1.5"],
                ["صورة غير موقّعة في الإنتاج", "policy admission (cosign/policy-controller)", "وقّع في CI + سياسة قبول ترفض غير الموقّع"],
                ["globalization مكسور بصمت (فرز عربي/توقيت)", "اختبار على الصورة النهائية مش على الجهاز", "`-extra` variant أو `apk add icu-libs icu-data-full` + `INVARIANT=false` + اختبارات ثقافة"],
            ]},
            {"type": "callout", "kind": "danger", "title": "فخ ICU: صورتك صغيرة والفرز العربي بقى غلط",
             "md": """
**العرض**: على جهازك (Windows/macOS) كل حاجة تمام، وجوه الصورة الصغيرة:
- `ORDER BY name` بيرتب النص العربي بطريقة مختلفة عن المتوقع (collation بلا ICU).
- `string.Compare(a, b, StringComparison.CurrentCulture)` بيرمي أو بيتصرف كـinvariant.
- `TimeZoneInfo.FindSystemTimeZoneById("Africa/Cairo")` بيفشل (`TimeZoneNotFoundException`) — **مفيش tzdata**.
- تنسيق تواريخ/عملات (`ar-EG`, `CultureInfo`) بيرجع شكل مبسّط أو يرمي.
- أو الرسالة الصريحة: `Couldn't find a valid ICU package installed on the system`.

**السبب**: صور `alpine` و`noble-chiseled` (والـdistroless) **ما بتضمنش `icu` ولا `tzdata`** —
بتشتغل في **globalization invariant mode** افتراضيًا.

**الحل (بالترتيب):**
1. **استخدم `-extra`**: `aspnet:10.0-noble-chiseled-extra` (+15MB تقريبًا) — الحل الأنضف.
2. **على Alpine**: `apk add --no-cache icu-libs icu-data-full tzdata` + `ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false`
   (بيكسر مبدأ «بلا package manager» — استخدمه لو Alpine مطلوب فعلًا).
3. **لو فعلاً مش محتاج ثقالات** (خدمة داخلية بتتعامل مع ASCII وأرقام وUTC بس):
   `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true` — و**وثّق القرار في ADR** واختبره.
4. **الأهم**: أضف **اختبار يعمل على الصورة النهائية** (مش على الجهاز) بيتحقق من:
   فرز نص عربي، تحويل `Africa/Cairo`، وتنسيق عملة `ar-EG`. الاختبار ده بيمنع رجوع المشكلة.

⚠ **musl (Alpine) مش glibc**: فيه فروق سلوك/أداء في حالات معينة (DNS، بعض الحزم الأصلية، الـregex الثقيلة).
لو بتعتمد على مكتبات native، اختبر على الصورة الفعلية قبل ما تلتزم.
"""},
            {"type": "code", "lang": "csharp", "filename": "src/Shop.Orders/HealthSelfCheck.cs", "title": "نمط: فحص صحة من جوه الصورة بلا shell ولا curl (يشتغل في chiseled)", "code": r'''
// ★ المشكلة: HEALTHCHECK في Dockerfile بيحتاج shell أو curl — ومفيش في chiseled/distroless،
//   وتثبيت curl بيكبر الصورة ويضيف ثغرات.
// الحل: التطبيق نفسه بيقدم وضع فحص (`--health`) بيخرج 0 (صحي) أو 1 (غير صحي)،
//   فيستخدمه compose/أي أداة فحص بلا أي أداة نظام إضافية.

public static class HealthSelfCheck
{
    /// <summary>يُنادى في أول Program.cs قبل بناء الـhost.</summary>
    public static async Task<int> RunIfRequestedAsync(string[] args)
    {
        if (!args.Contains("--health")) return -1;                 // ← -1 = مش وضع فحص، كمّل عادي

        var url = Environment.GetEnvironmentVariable("HEALTHCHECK_URL")
                  ?? $"http://127.0.0.1:{Environment.GetEnvironmentVariable("ASPNETCORE_HTTP_PORTS") ?? "8080"}/health";

        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
            using var response = await http.GetAsync(url);

            // ✓ 200 = صحي · 503 = غير صحي (degraded) · أي حاجة تانية = فشل
            await Console.Out.WriteLineAsync($"{(response.IsSuccessStatusCode ? "healthy" : "unhealthy")}: {(int)response.StatusCode}");
            return response.IsSuccessStatusCode ? 0 : 1;
        }
        catch (Exception ex)
        {
            await Console.Error.WriteLineAsync($"health probe failed: {ex.Message}");
            return 1;
        }
    }
}

// ── في Program.cs ──
// var selfCheck = await HealthSelfCheck.RunIfRequestedAsync(args);
// if (selfCheck >= 0) return selfCheck;          // ✓ وضع الفحص: اخرج فورًا
// var builder = WebApplication.CreateBuilder(args);
// …

// ── الاستخدام في Dockerfile (لو محتاج فحص من جوه الصورة) ──
// HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
//   CMD ["dotnet", "Shop.Orders.dll", "--health"]
//
// ── أو في compose (يفضّل: بلا HEALTHCHECK في الصورة) ──
// healthcheck:
//   test: ["CMD", "dotnet", "Shop.Orders.dll", "--health"]
//   interval: 15s
//   timeout: 5s
//   retries: 5
//   start_period: 30s
//
// ⚠ في Kubernetes: استخدم httpGet probe (بلا أي أداة ولا أمر) — أرخص وأوضح:
//   readinessProbe: { httpGet: { path: /health, port: 8080 } }
//   livenessProbe:  { httpGet: { path: /alive,  port: 8080 } }
'''},
            {"type": "heading", "level": 2, "text": "3) تصليد وقت التشغيل (compose وKubernetes)"},
            {"type": "code", "lang": "yaml", "filename": "compose/hardened.yml", "title": "إعدادات الأمان للخدمة — compose وK8s جنب بعض", "code": r'''
# ═══════════ Docker Compose ═══════════
services:
  orders:
    image: ghcr.io/<org>/shop-orders@sha256:<digest>   # ★ digest ثابت، مش tag
    user: "1654:1654"                                   # ✓ non-root (APP_UID)
    read_only: true                                     # ✓ جذر الملفات للقراءة فقط
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m                  # ← المسار الوحيد القابل للكتابة
    cap_drop: [ALL]                                     # ✓ إسقاط كل صلاحيات Linux
    security_opt:
      - no-new-privileges:true                          # ✓ منع تصعيد الصلاحيات
      - seccomp=./infra/seccomp-allowlist.json          # (اختياري متقدم: قائمة استدعاءات نظام مسموحة)
    pids_limit: 256                                     # ✓ حماية من fork bomb
    mem_limit: 512m
    cpus: "1.0"
    restart: unless-stopped
    init: true
    # ✗ بلا published ports للخدمات الداخلية — الـgateway فقط مكشوف
    networks: [shop-internal]
    healthcheck:
      test: ["CMD", "dotnet", "Shop.Orders.dll", "--health"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 30s

networks:
  shop-internal:
    internal: true          # ★ شبكة معزولة: بلا وصول للإنترنت (للخدمات اللي ما تحتاجهوش)

---
# ═══════════ Kubernetes (نفس النوايا، صيغة تانية) ═══════════
# apiVersion: apps/v1
# kind: Deployment
# spec:
#   template:
#     spec:
#       securityContext:
#         runAsNonRoot: true
#         seccompProfile: { type: RuntimeDefault }
#       containers:
#         - name: orders
#           image: ghcr.io/<org>/shop-orders@sha256:<digest>
#           securityContext:
#             runAsUser: 1654
#             runAsGroup: 1654
#             readOnlyRootFilesystem: true
#             allowPrivilegeEscalation: false
#             capabilities: { drop: ["ALL"] }
#           ports: [{ containerPort: 8080 }]
#           resources:
#             requests: { cpu: "100m", memory: "128Mi" }
#             limits:   { cpu: "1000m", memory: "512Mi" }
#           readinessProbe: { httpGet: { path: /health, port: 8080 }, periodSeconds: 10 }
#           livenessProbe:  { httpGet: { path: /alive,  port: 8080 }, periodSeconds: 20 }
#           volumeMounts: [{ name: tmp, mountPath: /tmp }]
#       volumes:
#         - name: tmp
#           emptyDir: { sizeLimit: 64Mi }
#
# ✓ تحقق آليًا من كل ده:
#   trivy config ./k8s            (misconfigurations)
#   kubectl get pod -o jsonpath='{.items[*].spec.containers[*].securityContext}'
#   kube-bench / kubescape للـcluster نفسه
'''},
            {"type": "callout", "kind": "warn", "title": "الصورة الصغيرة ليها ثمن — اعرفه قبل ما تلتزم",
             "md": """
**chiseled/distroless:**
- ✓ أصغر سطح هجوم، بلا shell/package manager، non-root افتراضيًا.
- ✗ **تشخيص أصعب**: مفيش `sh` ولا `curl` ولا `ps`. هتعتمد على لوجات التطبيق والمقاييس
  و`kubectl debug` (ephemeral container) و`docker cp`.
- ✗ بعض الأدوات (APM agents، profilers مثل `dotnet-trace`) بتحتاج مسارات/مكتبات مش موجودة →
  `DOTNET_EnableDiagnostics=0` بيقفلها أصلًا؛ فعّلها وقت التشخيص فقط.

**alpine (musl):**
- ✓ صغيرة وفيها `apk` وshell → تشخيص أسهل.
- ✗ musl ≠ glibc: فروق في DNS resolution والأداء في بعض الحالات، وتوافق مكتبات native أقل.

**NativeAOT:**
- ✓ ~11MB، إقلاع فوري، ذاكرة أقل — ممتاز لـworkers وخدمات صغيرة.
- ✗ قيود حقيقية: reflection ديناميكي، بعض مكتبات MassTransit/EF Core تحتاج إعداد خاص
  (compiled models / source generators)، وتحذيرات `IL2xxx/IL3xxx` لازم تُعامل كأخطاء.

**القاعدة العملية**: ابدأ بـ`aspnet:10.0-noble-chiseled-extra` لخدمات الويب
(أمان + ثقافات سليمة + حجم معقول)، وجرّب AOT للخدمات الصغيرة/الحساسة للإقلاع.
وبلاش تنزل لـ`noble-chiseled` (بلا extra) إلا بعد اختبار الثقافة/المناطق الزمنية.
"""},
            {"type": "steps", "title": "خطة تأمين صورة في 8 خطوات", "items": [
                {"title": "قِس خط الأساس", "md": "الحجم والطبقات وزمن السحب — عشان تعرف إن التحسين حصل فعلًا.", "code": "docker images shop/orders --format '{{.Size}}'\ndocker history shop/orders --format 'table {{.Size}}\\t{{.CreatedBy}}' | head"},
                {"title": "اختار القاعدة الصح", "md": "chiseled-extra لخدمات الويب · alpine لو محتاج shell · runtime-deps+AOT للأصغر. وقرّر بناءً على احتياجك للثقافات.", "code": "FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled-extra"},
                {"title": "non-root + منفذ 8080", "md": "`USER $APP_UID` و`ASPNETCORE_HTTP_PORTS=8080`. تحقق بعد البناء.", "code": "docker run --rm --entrypoint dotnet shop/orders:x --version\ndocker inspect shop/orders:x --format '{{.Config.User}} · {{.Config.Env}}'"},
                {"title": "افحص الثغرات وأضف gate", "md": "CRITICAL/HIGH قابلة للإصلاح = البناء يفشل. و`--ignore-unfixed` عشان ما تغرقش في ضوضاء.", "code": "trivy image --scanners vuln --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 shop/orders:x"},
                {"title": "افحص التكوين مش الصورة بس", "md": "Dockerfile وcompose وmanifests فيها أخطاء تكوين (منافذ مكشوفة، privileges، بلا حدود).", "code": "trivy config --exit-code 1 .\ntrivy fs --scanners vuln,misconfig,secret ."},
                {"title": "ولّد SBOM وخزّنه", "md": "SBOM بيفضل يفيدك بعد النشر (ثغرة جديدة في مكتبة قديمة). خزّنه كـartifact مع كل إصدار.", "code": "trivy image --format cyclonedx --output sbom.cdx.json shop/orders:x\ntrivy sbom --severity CRITICAL sbom.cdx.json"},
                {"title": "وقّع وثبّت بالـdigest", "md": "التوقيع في CI + النشر بالـdigest + سياسة قبول ترفض غير الموقّع.", "code": "cosign sign --yes ghcr.io/<org>/shop-orders@sha256:<digest>\n# وفي manifests: image: ghcr.io/<org>/shop-orders@sha256:<digest>"},
                {"title": "تصليد وقت التشغيل + اختبار", "md": "read-only + cap_drop + no-new-privileges + حدود + شبكة داخلية — وبعدين **اختبر إن التطبيق لسه شغال** (كتير من التطبيقات بتكتب على القرص).", "code": "docker run -d --read-only --tmpfs /tmp --cap-drop ALL \\\n  --security-opt no-new-privileges:true --user 1654:1654 \\\n  -p 127.0.0.1:8080:8080 shop/orders:x\ncurl -s -o /dev/null -w '%{http_code}\\n' http://localhost:8080/health"}]},
            {"type": "checkpoints", "items": [
                "أختار قاعدة الصورة بأرقام حقيقية (chiseled/chiseled-extra/alpine/runtime-deps/AOT) وأعرف حجم كل واحدة وتكلفتها.",
                "أتجنب فخ ICU/tzdata: أستخدم `-extra` أو أثبّت ICU، وأختبر الفرز العربي والمناطق الزمنية على **الصورة النهائية**.",
                "أشغّل non-root (UID 1654) على 8080، وأفحص الصورة بـTrivy (ثغرات + تكوين + أسرار) وأولّد SBOM.",
                "أتصلد وقت التشغيل: read-only + tmpfs + cap_drop ALL + no-new-privileges + حدود موارد + شبكة داخلية.",
                "أوقّع الصور وأثبتها بالـdigest، وأعرف إزاي أتشخص من غير shell (ephemeral containers · `--health` mode · `docker cp`).",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "تطبيقك بيفرز نص عربي وبيتعامل مع منطقة `Africa/Cairo`. أنهي قاعدة صورة تختار؟",
                 "options": [
                     "`aspnet:10.0-noble-chiseled` (الأصغر)",
                     "`aspnet:10.0-noble-chiseled-extra` — لأنها بتضم icu + tzdata؛ بدونهم الفرز/التنسيق/المناطق الزمنية بتتكسر أو تشتغل invariant",
                     "`runtime-deps` + invariant mode",
                     "أي صورة مع `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true`",
                 ], "answer": 1,
                 "explain": "chiseled/alpine الافتراضية بلا ICU ولا tzdata → `TimeZoneNotFoundException` وسلوك فرز مختلف. `-extra` بتضيف icu+tzdata بزيادة ~15MB."},
                {"q": "الفرق بين `USER app` و`USER $APP_UID`؟",
                 "options": [
                     "مفيش فرق",
                     "`$APP_UID` (1654) أوضح وبيتوافق مع K8s `runAsUser` الرقمي وما يعتمدش على وجود اسم المستخدم في الصورة — النمط الموصى به",
                     "`app` أأمن",
                     "`$APP_UID` يحتاج root",
                 ], "answer": 1,
                 "explain": "الاتنين نفس الـUID. الـenv var بيتجنب الأرقام السحرية المكررة وبيشتغل حتى في صور distroless اللي قائمة المستخدمين فيها محدودة."},
                {"q": "الصورة chiseled (بلا shell) وعايز تتشخص. تعمل إيه؟",
                 "options": [
                     "تثبت curl وbash في الصورة",
                     "تعتمد على لوجات/مقاييس التطبيق + `kubectl debug` (حاوية تشخيص مؤقتة) أو `docker cp` — وتضيف وضع `--health` في التطبيق للفحص",
                     "ترجع لصورة Debian كاملة",
                     "ما تتشخصش",
                 ], "answer": 1,
                 "explain": "تثبيت أدوات تشخيص في صورة الإنتاج = حجم + ثغرات + سطح هجوم. التشخيص من **بره** الحاوية هو النمط الصحيح."},
                {"q": "`trivy image --severity CRITICAL,HIGH --exit-code 1` فشل في CI على ثغرة في مكتبة نظام **ما ليهاش إصلاح**. التصرف؟",
                 "options": [
                     "تعطّل الفحص",
                     "`--ignore-unfixed` للثغرات بلا إصلاح متاح + استثناء موثق بمدة انتهاء (واستمرار المتابعة)، مع إبقاء الـgate على القابلة للإصلاح",
                     "تقبل الفشل دايمًا",
                     "تحذف المكتبة",
                 ], "answer": 1,
                 "explain": "الـgate بيكون له قيمة لو بيركز على اللي تقدر تصلحه. الاستثناءات لازم تكون مكتوبة بمسؤول وتاريخ انتهاء (وإلا بتتراكم للأبد)."},
                {"q": "`read_only: true` كسر التطبيق. أشيع سبب؟",
                 "options": [
                     "الصورة كبيرة",
                     "التطبيق بيكتب على القرص (temp files، لوجات ملف، DataProtection keys، cache) — الحل: `tmpfs /tmp` أو volume مخصص، أو نقل الكتابة لـRedis/Storage",
                     "non-root",
                     "cap_drop",
                 ], "answer": 1,
                 "explain": "أمثلة .NET شائعة: `PersistKeysToFileSystem` لـDataProtection، لوجات ملف، `Path.GetTempPath()`. حوّلها لـtmpfs/volume أو لخدمة خارجية."},
                {"q": "ليه تنشر بـdigest (`@sha256:…`) بدل `:tag` في الإنتاج؟",
                 "options": [
                     "أسرع",
                     "الـtag ممكن يُعاد توجيهه لمحتوى مختلف، فالـdigest بيضمن إنك بتشغّل نفس البايتات بالظبط وبيخلي الـrollback حقيقي",
                     "أصغر",
                     "مطلوب من Docker",
                 ], "answer": 1,
                 "explain": "التكرارية (reproducibility) هي السبب: لو `:1.4.0` اتبنت تاني، المحتوى اختلف وانت مش هتعرف. الـdigest بيقفل الباب ده."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "صغّر وأمّن صورتك بأرقام",
                 "md": "حوّل خدمة واحدة من صورتك الحالية لأصغر قاعدة مناسبة (chiseled-extra أو AOT)، وصلّدها وقت التشغيل، وقِس الفرق: حجم، زمن سحب، مستخدم، ثغرات CRITICAL/HIGH قبل/بعد. وثّق القرار في ADR.",
                 "criteria": [
                     "جدول قياس: الحجم (مضغوط/مفكوك) · عدد الطبقات · ثغرات CRITICAL/HIGH · زمن السحب — قبل وبعد",
                     "الحجم النهائي: ≤ 120MB مفكوكة (framework-dependent) أو ≤ 60MB (self-contained/AOT)",
                     "`USER $APP_UID` + تشغيل فعلي على 8080 + `docker inspect` يثبت المستخدم والمنفذ",
                     "تصليد وقت التشغيل مطبّق ومُختبر: `read_only` + `tmpfs /tmp` + `cap_drop ALL` + `no-new-privileges` + حدود ذاكرة/CPU + `/health` بيرد 200",
                     "فحص الثغرات: `trivy image --severity CRITICAL,HIGH --ignore-unfixed` نظيف أو فيه استثناءات موثقة بمدة انتهاء",
                     "SBOM مولّد ومخزّن كـartifact + فحص الـSBOM نفسه",
                     "ADR: القاعدة المختارة × البدائل المرفوضة × الأثر على الثقافة/التشخيص × خطة إعادة القاعدة (rebase) شهريًا",
                 ],
                 "hint": "لو `read_only` كسر التطبيق: شوف اللوجات لأول استثناء (`UnauthorizedAccessException`) — هيقولك المسار بالظبط. حوّله لـtmpfs أو volume.",
                 "solution": "",
                 "resources": [
                     {"label": ".NET image variants (chiseled/extra/aot)", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/image-variants.md"},
                     {"label": ".NET image size report", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/sample-image-size-report.md"},
                     {"label": "Trivy", "url": "https://trivy.dev/"}]},
                {"id": "t2", "title": "اختبار الثقافة والتشخيص على الصورة النهائية",
                 "md": "اكتب اختبارين يشتغلوا **ضد الصورة** (مش على جهازك): (1) ثقافة/مناطق زمنية — فرز نص عربي، تحويل Africa/Cairo، تنسيق عملة ar-EG؛ (2) تشخيص بلا shell — إثبات إنك تقدر تجيب اللوجات والحالة وتنسخ ملف من حاوية chiseled. شغّلهم في CI.",
                 "criteria": [
                     "اختبار ثقافة بيتنفذ جوه/ضد الحاوية النهائية ويثبت: فرز عربي صحيح + `TimeZoneInfo` بـ`Africa/Cairo` شغال + تنسيق `ar-EG` سليم",
                     "الاختبار بينجح على `-extra` و**بيفشل** على القاعدة بلا ICU (أثبت الاتنين — ده دليل إن الاختبار له قيمة)",
                     "سكريبت تشخيص بلا shell: `docker logs` + `docker inspect` + `docker create`/`docker cp` (أو `kubectl debug`) — مع مخرجات محفوظة",
                     "وضع `--health` في التطبيق شغال ومستخدم في compose healthcheck أو Dockerfile HEALTHCHECK",
                     "الاختبارين في CI (job واحد) مع فشل واضح لو الصورة رجعت بلا ICU",
                     "فقرة في `docs/images.md`: القاعدة المستخدمة، وليه، وإزاي تتشخص من غير shell، وخطة التحديث الشهري",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": ".NET distroless/chiseled docs", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/distroless.md"},
                     {"label": "Globalization invariant mode", "url": "https://learn.microsoft.com/dotnet/core/runtime-config/globalization"},
                     {"label": "Kubernetes ephemeral debug containers", "url": "https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/"}]},
            ]},
            {"type": "resources", "items": [
                {"label": ".NET image variants", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/image-variants.md"},
                {"label": ".NET distroless images", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/distroless.md"},
                {"label": ".NET image size comparison", "url": "https://github.com/dotnet/dotnet-docker/blob/main/documentation/sample-image-size-report.md"},
                {"label": "Announcing .NET chiseled containers", "url": "https://devblogs.microsoft.com/dotnet/announcing-dotnet-chiseled-containers/"},
                {"label": "Trivy scanner", "url": "https://trivy.dev/"},
                {"label": "Docker Scout", "url": "https://docs.docker.com/scout/"},
                {"label": "cosign / Sigstore signing", "url": "https://docs.sigstore.dev/cosign/overview/"},
                {"label": "Kubernetes security context", "url": "https://kubernetes.io/docs/tasks/configure-pod-container/security-context/"},
                {"label": "OWASP Docker security cheat sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html"},
            ]},
        ],
    },
]
