"""Stage 6, Module 1 — Docker & isolated compute (lessons 1 & 2)."""

TODAY = "2026-10-22"

LESSONS_S6_A = [
    # ══════════════════════════════════════════════════════════════════
    # s6-m1-l1 — Dockerfile لمشروع .NET: multi-stage وlayer caching
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s6-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لحد دلوقتي كل حاجة بتشتغل على جهازك. **الصورة (Image) هي وحدة التسليم** في العالم الحقيقي:
ملف واحد فيه runtime + تطبيقك + تبعياته، بيتبني مرة وبيشتغل بنفس الشكل في CI وstaging وproduction.

الدرس ده بيغطي 3 حاجات بتفرق مع كل فريق .NET:
1. **Dockerfile multi-stage** — تبني بـSDK وتشغّل بـruntime فقط (صورة صغيرة وآمنة).
2. **Layer caching** — ترتيب الطبقات يخلي البناء ياخد 20 ثانية بدل 6 دقايق.
3. **التشغيل والشبكة محليًا** — أوامر حقيقية للفحص والتشخيص.

⚠ ملحوظة: لو انت عملت المرحلة 5 بـ**Aspire**، فـAspire بيولّد صور/تشغيل تلقائيًا للتطوير.
الدockerfile **لسه مطلوب** — لأنه اللي بيتبني في CI وبينتشر للإنتاج. Aspire بينسّق، وDockerfile بيوصف.
"""},
            {"type": "terms", "items": [
                {"term": "Image / Container", "def": "الصورة = قالب للقراءة فقط بطبقات. الحاوية = نسخة شغالة من الصورة بحالة قابلة للكتابة (بتضيع لما تقف)."},
                {"term": "Layer", "def": "كل تعليمة في Dockerfile بتضيف طبقة (تقريبًا). الطبقة بتتخزن مرة وتُشارك بين الصور — عشان كده الترتيب مهم."},
                {"term": "Multi-stage Build", "def": "مراحل متعددة في ملف واحد: مرحلة بناء فيها SDK، ومرحلة نهائية فيها runtime فقط. النتيجة: صورة صغيرة بلا أدوات بناء."},
                {"term": "Build Context", "def": "المجلد اللي بيتبعت للـdaemon عند البناء. كل ما كبر، كل ما البناء أبطأ — `.dockerignore` بيقلصه."},
                {"term": "Build Cache / Cache Mount", "def": "إعادة استخدام نتائج طبقات سابقة. `--mount=type=cache` بيخلي كاش NuGet يعيش بين البناءات من غير ما يدخل في الصورة."},
                {"term": "Registry / Tag / Digest", "def": "الـregistry مخزن الصور (Docker Hub/GHCR/ACR). الـtag اسم قابل للتغيير (`:1.4.0`)، والـdigest بصمة ثابتة (`@sha256:…`) — الإنتاج بالـdigest."},
                {"term": "Platform", "def": "`linux/amd64` أو `linux/arm64`. لو جهازك ARM (Apple Silicon) والإنتاج amd64، لازم `--platform` وإلا الصورة مش هتشتغل."},
                {"term": "ENTRYPOINT / CMD", "def": "ENTRYPOINT = الأمر الثابت، CMD = الوسائط الافتراضية. لـ.NET: `ENTRYPOINT [\"dotnet\", \"App.dll\"]`."},
                {"term": "Non-root User", "def": "صور .NET من 8+ فيها مستخدم `app` (UID 1654) والمنفذ الافتراضي 8080 (بلا root، بلا الحاجة لصلاحيات)."},
                {"term": "UseAppHost=false", "def": "بلا ملف تنفيذي أصلي (`.exe`/apphost) — التشغيل عبر `dotnet App.dll`، وده اللي ينفع مع non-root وصور runtime."},
            ]},
            {"type": "heading", "level": 2, "text": "1) Dockerfile إنتاجي كامل"},
            {"type": "code", "lang": "dockerfile", "filename": "src/Shop.Orders/Dockerfile", "title": "multi-stage + cache mount + non-root + ترتيب طبقات صحيح", "code": r'''
# syntax=docker/dockerfile:1
# ↑ يخبر BuildKit بأحدث صيغة (مطلوب لـ --mount=type=cache)

# ══════════════ المرحلة 1: البناء (SDK — كبيرة، بس ما بتوصلش للصورة النهائية) ══════════════
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
ARG TARGETARCH                                # ★ multi-arch: amd64 أو arm64 حسب منصة البناء
WORKDIR /src

# ── ① انسخ ملفات المشاريع (.csproj) **فقط** ──
# السبب: طبقة restore تتكسر فقط لو csproj اتغيّر — مش كل ما تلمس ملف كود.
COPY src/Shop.Orders/Shop.Orders.csproj                 src/Shop.Orders/
COPY src/Shop.Contracts/Shop.Contracts.csproj           src/Shop.Contracts/
COPY src/Shop.ServiceDefaults/Shop.ServiceDefaults.csproj src/Shop.ServiceDefaults/

# ── ② restore مع كاش NuGet بين البناءات (مش جوه الصورة) ──
RUN --mount=type=cache,id=nuget-${TARGETARCH},target=/root/.nuget/packages \
    dotnet restore src/Shop.Orders/Shop.Orders.csproj \
        --arch "${TARGETARCH}" \
        --os linux \
        /p:UseAppHost=false

# ── ③ دلوقتي فقط انسخ باقي الكود ──
# ⚠ لو COPY . . كانت قبل restore، أي تعديل في أي ملف كان هيكسر كاش الـrestore (بناء 6 دقايق كل مرة)
COPY . .

# ── ④ النشر: إخراج مستقل عن أدوات البناء ──
RUN --mount=type=cache,id=nuget-${TARGETARCH},target=/root/.nuget/packages \
    dotnet publish src/Shop.Orders/Shop.Orders.csproj \
        -c "${BUILD_CONFIGURATION}" \
        --arch "${TARGETARCH}" \
        --os linux \
        --no-restore \
        /p:UseAppHost=false \
        -o /app/publish

# ══════════════ المرحلة 2: التشغيل (runtime فقط — صغيرة) ══════════════
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
ARG BUILD_CONFIGURATION=Release

# ✓ صور .NET 8+ فيها مستخدم غير root (`app`, UID 1654) ومتغير APP_UID
ENV ASPNETCORE_HTTP_PORTS=8080 \
    ASPNETCORE_ENVIRONMENT=Production \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false \
    DOTNET_gcServer=1 \
    DOTNET_TieredPGO=1

WORKDIR /app
COPY --from=build /app/publish .

# ✓ لا root: لو اتسرب التطبيق، المهاجم جوه حاوية بصلاحيات محدودة
USER $APP_UID

EXPOSE 8080

# ⚠ HEALTHCHECK داخل الصورة **بيحتاج أداة** (curl/wget) وصور .NET الحديثة ما فيهاش —
#   وchiseled/distroless مافيهاش shell أصلًا. الحل الصحيح: فحص الصحة من المنسّق
#   (K8s httpGet probe / compose healthcheck) — راجع درس 6.1.2 و6.1.5.
#   لو لازم فحص من جوه الصورة، طبّق وضع `--health` في تطبيقك نفسه (نمط متقدم في درس 6.1.3).

# ★ ENTRYPOINT ثابت + CMD للوسائط: تقدر تمرر وسائط إضافية وقت التشغيل
ENTRYPOINT ["dotnet", "Shop.Orders.dll"]
CMD []

# ── ملاحظات ──
# • الحجم المتوقع للمرحلة النهائية: ~90–110MB (Debian slim) · ~45–55MB (alpine) · ~30MB (chiseled)
# • لو التطبيق بيستخدم System.Text.Json فقط ومش محتاج ICU، تقدر تفعّل
#   DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true وتصغّر الصورة (alpine/chiseled-extralite) —
#   بس احذر: بيبطّل collation/فرز عربي صحيح. اختبر قبل ما تفعّله.
'''},
            {"type": "code", "lang": "text", "filename": ".dockerignore", "title": "ملف في جذر المستودع (بيقلص الـcontext من GBs لـMBs)", "code": r'''
# ── مخرجات البناء والتبعيات (أهم بند: بيوفر دقايق) ──
**/bin/
**/obj/
**/out/
**/publish/
**/node_modules/

# ── أدوات واختبارات (مش محتاجينها جوه الصورة) ──
**/*.Tests/
**/tests/
**/TestResults/
**/*.trx
**/coverage*.xml
**/coverage*.json

# ── مستودع وأدوات تطوير ──
.git/
.gitignore
.github/
.vs/
.vscode/
.idea/
**/*.user
**/*.suo

# ── أسرار وبيئة (⚠ أهم بند أمنيًا) ──
**/appsettings.*.json
**/*.pfx
**/*.pem
**/*.key
**/.env
**/.env.*
**/secrets/
**/user-secrets*

# ── ملفات كبيرة/غير ضرورية للبناء ──
**/*.md
docs/
**/*.png
**/*.jpg
**/*.mp4
docker-compose*.yml
Dockerfile*
!.dockerignore

# ── حاويات/بيانات محلية ──
data/
logs/
**/*.db
**/*.sqlite
'''},
            {"type": "callout", "kind": "warn", "title": "`.dockerignore` والأسرار: غلطة بتكلف كتير",
             "md": """
**بلا `.dockerignore`، الـbuild context بيشمل كل حاجة** — بما فيها `.git/` (كل تاريخ المستودع)
و`appsettings.Production.json` و`.env`.النتيجة:
1. البناء بطيء (مئات MB بتتبعت للـdaemon كل مرة).
2. **الأسرار ممكن تدخل في طبقات الصورة** حتى لو ما استخدمتهاش — أي حد يسحب الصورة يقدر يستخرجها
   من الطبقات (`docker history` / تفكيك الطبقات).
3. ملفات الاختبارات والمخرجات بتلوث الصورة.

✅ **قاعدة**: الأسرار ما تدخلش الصورة **أبدًا** — لا في `ENV`، ولا `ARG`، ولا `COPY`.
بتوصل للتطبيق وقت التشغيل من: environment (compose/K8s Secret) · Key Vault + Managed Identity (درس 6.2.3) ·
mounted files. ولو دخل سر في صورة بالغلط: **اعتبره مكشوف** ولفّه (rotate) فورًا — حذف الطبقة مش كفاية.
"""},
            {"type": "heading", "level": 2, "text": "2) ترتيب الطبقات: إيه اللي بيكسر الكاش؟"},
            {"type": "table", "head": ["الترتيب", "النتيجة", "الحكم"], "rows": [
                ["`COPY . .` ← `RUN dotnet restore`", "أي تعديل في أي ملف = restore كامل من الصفر", "✗ الأسوأ (6 دقايق لكل بناء)"],
                ["`COPY *.csproj` ← `RUN restore` ← `COPY . .` ← `RUN publish`", "restore بيتكسر فقط لو التبعيات اتغيرت", "★ الصحيح"],
                ["`RUN restore` بلا `--mount=type=cache`", "الكاش جوه الطبقة → بيتكسر مع الطبقة + الصورة بتكبر", "✗ استخدم cache mount"],
                ["`RUN apt-get update && apt-get install -y curl` في المرحلة النهائية", "بيكسر الكاش + بيضيف حجم + سطح هجوم", "✗ تجنّب؛ استخدم فحص من المنسّق"],
                ["`ENV` متغيرة (مثل `BUILD_DATE`) قبل `COPY`", "كل بناء يكسر كل الطبقات بعده", "✗ حطّها في الآخر أو استخدم labels"],
                ["`ARG` مستخدم في `RUN` بعد الطبقة", "تغيير الـARG بيكسر الطبقة دي فقط (مقبول)", "△ افهم أثره"],
                ["ملفات متغيرة كثيرًا (README/CHANGELOG) في الـcontext", "تكسر `COPY . .` — بس restore محمي لو مرتب صح", "△ أضفها لـ`.dockerignore`"],
                ["`dotnet publish` بلا `--no-restore`", "restore تاني داخل publish = وقت مضاعف", "✗ استخدم `--no-restore`"],
            ]},
            {"type": "code", "lang": "bash", "title": "البناء · التشغيل · الفحص · القياس", "code": r'''
# ═══ 1) البناء ═══
cd <repo-root>                       # ★ الـcontext = جذر المستودع (عشان المشاريع المرجعية)
docker build -f src/Shop.Orders/Dockerfile \
  -t shop/orders:1.4.0 \
  -t shop/orders:sha-$(git rev-parse --short HEAD) \
  --build-arg BUILD_CONFIGURATION=Release \
  .

# بناء متعدد المنصات (جهاز ARM → إنتاج amd64)
docker buildx create --use --name shop-builder 2>/dev/null || true
docker buildx build --platform linux/amd64,linux/arm64 \
  -f src/Shop.Orders/Dockerfile -t ghcr.io/<org>/shop-orders:1.4.0 --push .

# بديل بلا Dockerfile ولا Docker daemon: SDK container publishing
dotnet publish src/Shop.Orders -c Release /t:PublishContainer \
  -p ContainerRepository=ghcr.io/<org>/shop-orders \
  -p ContainerImageTag=1.4.0 \
  -p ContainerBaseImage=mcr.microsoft.com/dotnet/aspnet:10.0

# ═══ 2) الشبكة والتشغيل محليًا ═══
docker network create shop-net 2>/dev/null || true

docker run -d --name shop-orders \
  --network shop-net \
  -p 8080:8080 \
  -e ASPNETCORE_ENVIRONMENT=Development \
  -e ConnectionStrings__shopdb="Host=shop-postgres;Port=5432;Database=shopdb;Username=postgres;Password=local" \
  -e ConnectionStrings__rabbit="amqp://shop:local@shop-rabbit:5672/shop" \
  --health-cmd "" \
  shop/orders:1.4.0

# ⚠ أسماء الـhosts جوه الشبكة = أسماء الحاويات (shop-postgres) مش localhost

# ═══ 3) الفحص والتشخيص ═══
docker ps --filter name=shop-orders --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs -f --tail 200 shop-orders                       # اللوجات (stdout/stderr)
docker exec -it shop-orders sh                              # shell (مش متاح في chiseled/distroless)
docker inspect shop-orders --format '{{json .State.Health}}'
docker stats --no-stream shop-orders                        # CPU/ذاكرة لحظية
docker top shop-orders                                      # العمليات (تأكد إنها مش root)

# ═══ 4) القياس: حجم الصورة والطبقات ═══
docker images shop/orders --format '{{.Repository}}:{{.Tag}} {{.Size}}'
docker history shop/orders:1.4.0 --format 'table {{.Size}}\t{{.CreatedBy}}' | head -20
docker image inspect shop/orders:1.4.0 --format '{{.Os}}/{{.Architecture}} · layers={{len .RootFS.Layers}}'

# ═══ 5) التأكد إنها بتشتغل فعلًا ═══
curl -s -o /dev/null -w 'health %{http_code}\n' http://localhost:8080/health
curl -s http://localhost:8080/alive

# ═══ 6) التحقق إن الكاش شغال (البناء التاني لازم ياخد ثواني) ═══
time docker build -f src/Shop.Orders/Dockerfile -t shop/orders:cache-test .
#   ← عدّل ملف Program.cs وابدأ من جديد: المفروض restore/publish يُعاد بس **restore لا**
'''},
            {"type": "callout", "kind": "tip", "title": "8 قواعد لصورة .NET محترمة",
             "md": """
1. **multi-stage دائمًا** — SDK في مرحلة، runtime في النهائية. (فرق الحجم: ~800MB → ~100MB)
2. **`COPY *.csproj` قبل `COPY . .`** — عشان كاش الـrestore يعيش.
3. **`--mount=type=cache` لـNuGet** — تسريع كبير من غير تضخيم الصورة.
4. **non-root (`USER $APP_UID`) + منفذ 8080** — صور .NET 8+ جاهزة لده؛ لا ترجع لـroot ولا لـ5000.
5. **tags واضحة + digest للنشر**: `:1.4.0` و`:sha-abc1234` للتتبع، و**بالـdigest** في manifests الإنتاج
   (`@sha256:…`) — `latest` معناها «مش عارف إنت بتشغّل إيه».
6. **بلا أسرار في الصورة** (ولا `ARG`/`ENV`/`COPY`) — ولا `.git` في الـcontext.
7. **لا تثبت أدوات في المرحلة النهائية** (curl/vim/ssh) — حجم + ثغرات + سطح هجوم.
   التشخيص من بره: `docker exec` (لو فيه shell) أو ephemeral containers في K8s.
8. **اختبر الصورة، مش الكود بس**: شغّلها وافحص `/health` قبل ما تدفعها للـregistry (درس 6.3.1).
"""},
            {"type": "heading", "level": 2, "text": "3) 3 طرق لبناء الصورة — اختار بوعي"},
            {"type": "table", "head": ["الطريقة", "المميزات", "العيوب", "إمتى"], "rows": [
                ["**Dockerfile multi-stage**", "تحكم كامل · يعمل في أي CI · مفهوم لكل الفرق · يدعم multi-arch", "البناء أبطأ (يحتاج daemon) · ملف لازم يتصان", "★ الافتراضي لمعظم الفرق"],
                ["**SDK container publishing** (`/t:PublishContainer`)", "بلا Dockerfile ولا Docker daemon · سريع جدًا في CI · يعتمد على .NET SDK فقط", "تحكم أقل (لا أدوات نظام/خطوات مخصصة) · بعض الإعدادات عبر MSBuild properties", "CI بسيط · مشاريع بلا احتياجات نظام خاصة"],
                ["**نشر خارج الصورة + runtime-deps**", "أصغر صورة · فصل كامل بين البناء والتعبئة · يناسب AOT", "خطوتين (publish ثم COPY) · لازم تطابق إصدار runtime-deps", "NativeAOT · صور minimal · توفير أقصى"],
                ["**Jib-like / Buildpacks (Cloud Native Buildpacks)**", "بلا Dockerfile · طبقات محسّنة تلقائيًا", "منظومة تانية للتعلم · تحكم أقل في التفاصيل", "فرق بتستخدم `pack`/Paketo فعلًا"],
            ]},
            {"type": "steps", "title": "ابنِ صورتك الأولى في 7 خطوات", "items": [
                {"title": "أضف `.dockerignore` في جذر المستودع", "md": "قبل أي Dockerfile. تحقق إن الـcontext صغير.", "code": "du -sh .git node_modules **/bin **/obj 2>/dev/null\n# بعد الإضافة: قارن زمن `docker build` الأول"},
                {"title": "اكتب Dockerfile بمرحلتين", "md": "SDK للبناء، aspnet للتشغيل. انسخ csproj أولًا.", "code": "FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build\n…\nFROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final"},
                {"title": "ابنِ وقِس", "md": "سجّل الحجم وزمن البناء — دول أرقامك الأساسية للمقارنة بعد التحسين.", "code": "docker build -f src/Shop.Orders/Dockerfile -t shop/orders:baseline .\ndocker images shop/orders:baseline --format '{{.Size}}'"},
                {"title": "شغّلها وتأكد من `/health`", "md": "بلا تشغيل فعلي، «الصورة اتبنت» مش دليل إنها بتشتغل.", "code": "docker run -d --name t -p 8080:8080 shop/orders:baseline\ncurl -s -o /dev/null -w '%{http_code}\\n' http://localhost:8080/health"},
                {"title": "تحقق من المستخدم والمنفذ", "md": "لازم non-root و8080. لو لقيت root أو 5000، صلّح قبل ما تكمل.", "code": "docker exec t id            # uid=1654(app)\ndocker exec t printenv ASPNETCORE_HTTP_PORTS"},
                {"title": "افحص الطبقات والحجم", "md": "شوف أنهي طبقة كبيرة وليه. الطبقات المكررة = إهدار.", "code": "docker history shop/orders:baseline --format 'table {{.Size}}\\t{{.CreatedBy}}' | head"},
                {"title": "اجعل البناء جزءًا من CI", "md": "بناء + فحص ثغرات + دفع للـregistry بـtag بالـcommit وdigest ثابت (درس 6.3.1 و6.1.3).", "code": "# في GitHub Actions\n# docker/build-push-action@v6 مع cache-from/cache-to: type=gha"}]},
            {"type": "checkpoints", "items": [
                "أكتب Dockerfile multi-stage لمشروع .NET بترتيب طبقات يستفيد من الكاش (csproj ← restore ← copy ← publish).",
                "أستخدم `--mount=type=cache` لكاش NuGet و`--no-restore` مع publish، وأفهم ليه `COPY . .` في الأول كارثة.",
                "أشغّل الحاوية non-root على 8080 وأتحقق من المستخدم والمنفذ والصحة.",
                "أكتب `.dockerignore` يمنع تسريب الأسرار ويقلص الـcontext، وأفهم فرق tag مقابل digest.",
                "أختار بين Dockerfile وSDK container publishing وruntime-deps/AOT بحسب الحاجة.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه ننسخ ملفات `.csproj` قبل باقي الكود؟",
                 "options": [
                     "عشان الترتيب الأبجدي",
                     "عشان طبقة `restore` تتكسر فقط عند تغيير التبعيات — أي تعديل في الكود ما يعيدش تحميل الحزم",
                     "مطلوب من BuildKit",
                     "عشان الصورة تصغر",
                 ], "answer": 1,
                 "explain": "ده جوهر layer caching: الطبقات الثابتة (التبعيات) الأول، والمتغيرة (الكود) في الآخر. الفرق عمليًا: 20 ثانية مقابل 6 دقايق."},
                {"q": "`--mount=type=cache,target=/root/.nuget/packages` بيحقق إيه؟",
                 "options": [
                     "بيخزّن الحزم جوه الصورة",
                     "كاش NuGet يعيش بين البناءات **من غير** ما يدخل في طبقات الصورة — تسريع بلا تضخيم",
                     "بيسرّع النشر",
                     "بديل عن restore",
                 ], "answer": 1,
                 "explain": "الكاش ده خارج الصورة (mount مؤقت وقت تنفيذ التعليمة). لو خزنت الحزم في طبقة، الصورة هتكبر والكاش هيتكسر مع الطبقة."},
                {"q": "إيه المنفذ والمستخدم الافتراضيان في صور ASP.NET Core من .NET 8؟",
                 "options": [
                     "5000 وroot",
                     "**8080** ومستخدم غير root (`app`, UID 1654 عبر `APP_UID`)",
                     "80 وroot",
                     "8080 وroot",
                 ], "answer": 1,
                 "explain": "التغيير ده معناه إنك ما تحتاجش صلاحيات root ولا `ASPNETCORE_URLS=http://+:80`. ولو الكود القديم بيفترض 5000، حدّث المنفذ في compose/K8s."},
                {"q": "حطيت كلمة سر قاعدة البيانات في `ENV` جوه Dockerfile. الحكم؟",
                 "options": [
                     "مقبول لو الصورة خاصة",
                     "خطأ أمني: السر بيثبت في طبقات الصورة ويستخرجه أي حد يقدر يسحبها — ولو اتسرب، لفّ السر فورًا (حذف الطبقة مش كفاية)",
                     "مقبول مع .dockerignore",
                     "مقبول لو multi-stage",
                 ], "answer": 1,
                 "explain": "الأسرار وقت **التشغيل** (environment/Secret/Key Vault + Managed Identity)، مش وقت البناء. `.dockerignore` بيمنع دخول ملفات، مش `ENV` المكتوبة يدويًا."},
                {"q": "ليه `HEALTHCHECK` جوه صورة .NET غالبًا مش فكرة جيدة؟",
                 "options": [
                     "بيبطّئ الإقلاع",
                     "بيحتاج أداة (curl/wget) مش موجودة في صور .NET الحديثة — وchiseled/distroless مافيهاش shell أصلًا. الأفضل فحص الصحة من المنسّق (K8s httpGet / compose)",
                     "Docker ما بيدعمهوش",
                     "بيتعارض مع /health",
                 ], "answer": 1,
                 "explain": "تثبيت curl عشان healthcheck = حجم + ثغرات + سطح هجوم. المنسّق (K8s/compose) عنده فحص HTTP مدمج بلا أدوات جوه الصورة."},
                {"q": "في الإنتاج، تشغّل الصورة بأي مرجع؟",
                 "options": [
                     "`:latest`",
                     "**digest ثابت** (`image@sha256:…`) أو tag إصدار محدد — `latest` معناها إنك مش عارف بتشغّل إيه والـrollback مستحيل",
                     "اسم الصورة فقط",
                     "tag بتاريخ البناء",
                 ], "answer": 1,
                 "explain": "الـdigest بصمة لا تتغير. الـtag ممكن يُعاد توجيهه لنفس الاسم بمحتوى مختلف، وده بيكسر التكرارية والـrollback."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "Dockerfile محسّن بأرقام قبل/بعد",
                 "md": "اكتب Dockerfile multi-stage لواحدة من خدماتك مع `.dockerignore` كامل، وقِس: حجم الصورة، زمن البناء البارد، زمن البناء بعد تعديل ملف كود، والمستخدم/المنفذ. قارن بنسخة «ساذجة» (`COPY . .` أولًا) وأثبت الفرق بالأرقام.",
                 "criteria": [
                     "Dockerfile بمرحلتين (SDK → aspnet) مع `COPY *.csproj` قبل `COPY . .`",
                     "`--mount=type=cache` لـNuGet + `--no-restore` في publish + `/p:UseAppHost=false`",
                     "`.dockerignore` بيستثني `.git` و`bin/obj` و`tests` **وكل ملفات الأسرار**",
                     "الحاوية بتشتغل non-root على 8080 (`docker exec … id` = uid 1654) و`/health` بيرد 200",
                     "جدول أرقام: الحجم/البناء البارد/البناء بعد تعديل — للنسخة الساذجة مقابل المحسّنة (فرق ≥ 50% في زمن البناء الدافئ)",
                     "tag بإصدار + tag بـcommit sha، وإثبات `docker history` إن طبقة الـrestore مش بتتكسر عند تعديل كود",
                     "بلا أدوات مثبتة في المرحلة النهائية (لا curl/vim) — واكتب إزاي بتتشخص من غيرهم",
                 ],
                 "hint": "عدّل سطرًا في `Program.cs` وابنِ تاني: المفروض تشوف `CACHED` على خطوة الـrestore. لو ما ظهرش، الترتيب لسه غلط.",
                 "solution": "",
                 "resources": [
                     {"label": "Docker with .NET", "url": "https://learn.microsoft.com/dotnet/core/docker/"},
                     {"label": "Dockerfile reference", "url": "https://docs.docker.com/reference/dockerfile/"},
                     {"label": ".NET container deployment guidance", "url": "https://learn.microsoft.com/dotnet/core/deploying/"},
                 ]},
                {"id": "t2", "title": "تشغيل الخدمة مع تبعياتها على شبكة واحدة",
                 "md": "شغّل صورتك في شبكة Docker مع Postgres وRabbitMQ (حاويات جاهزة)، ومرّر الإعدادات عبر environment فقط (بلا تعديل كود)، وأثبت إن الخدمة بتشتغل وبتقرأ/تكتب في قاعدة البيانات وتستهلك من الوسيط.",
                 "criteria": [
                     "`docker network create` + كل الحاويات جواه (بأسماء ثابتة تُستخدم كـhostnames)",
                     "الخدمة بتوصل لـPostgres وRabbitMQ بأسماء الحاويات — مفيش `localhost` في الإعدادات",
                     "كل الإعدادات من environment/`--env-file` — `git grep` يثبت إن مفيش سر في Dockerfile أو appsettings",
                     "إثبات وظيفة: طلب HTTP بينشئ صف في DB + حدث في الطابور (مخرجات `psql` و`rabbitmqctl`)",
                     "إعادة تشغيل الحاوية ما بتفقدش البيانات (volumes) — مخرجات قبل/بعد",
                     "ملاحظة موثقة: إيه اللي حصل لما أوقفت DB (سلوك واضح: فشل صريح/إعادة محاولة) — مش صمت",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Docker networking", "url": "https://docs.docker.com/engine/network/"},
                     {"label": "Manage data in Docker", "url": "https://docs.docker.com/engine/storage/"}
            ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Docker with .NET", "url": "https://learn.microsoft.com/dotnet/core/docker/"},
                {"label": ".NET Docker images (tags & changelog)", "url": "https://github.com/dotnet/dotnet-docker"},
                {"label": "SDK container publishing (no Dockerfile)", "url": "https://learn.microsoft.com/dotnet/core/docker/publish-as-container"},
                {"label": "Dockerfile best practices", "url": "https://docs.docker.com/build/building/best-practices/"},
                {"label": "BuildKit & cache mounts", "url": "https://docs.docker.com/build/cache/"},
                {"label": "Buildx / multi-platform", "url": "https://docs.docker.com/build/building/multi-platform/"},
            ]},
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # s6-m1-l2 — Docker Compose: نظامك كامل محليًا
    # ══════════════════════════════════════════════════════════════════
    {
        "id": "s6-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
صورة واحدة بتحل «تطبيقك بيتشغل في أي مكان». بس نظامك **مش حاوية واحدة**:
فيه Postgres وRedis وRabbitMQ و4 خدمات وgateway. **Docker Compose** بيوصف النظام ده كله في ملف YAML واحد
وبيشغّله بأمر واحد — مع شبكة داخلية، وvolumes للبيانات، وhealthchecks، وترتيب إقلاع.

**العلاقة بـAspire (درس 5.3.1):** Aspire أفضل للتطوير اليومي (لوحة، discovery، أوامر).
Compose هو **اللغة المشتركة**: بيشتغل في CI، وعلى جهاز أي مطور بلا .NET SDK، وفي البيئات المشتركة،
وبيوصف بنية قابلة للنشر. كتير من الفرق بتستخدم الاتنين: Aspire للتطوير + Compose للتكامل/CI.
"""},
            {"type": "terms", "items": [
                {"term": "Service", "def": "تعريف حاوية (image أو build) مع إعداداتها: environment، ports، volumes، depends_on، healthcheck."},
                {"term": "Network", "def": "شبكة داخلية بين الخدمات. الأسماء = hostnames (`shop-postgres`). الخدمات اللي مش على نفس الشبكة ما تتشوفش."},
                {"term": "Volume (named/bind)", "def": "named = تديره Docker (بيانات DB) · bind = مسار من جهازك (كود/ملفات إعداد). الاتنين بيختلفوا في الأداء والقابلية للنقل."},
                {"term": "`depends_on` + condition", "def": "ترتيب الإقلاع: `service_started` (الافتراضي) · `service_healthy` (ينتظر الصحة) · `service_completed_successfully` (ينتظر انتهاء مهمة)."},
                {"term": "Healthcheck", "def": "فحص دوري جوه الحاوية يحدد حالتها (healthy/unhealthy) — هو اللي يخلي `service_healthy` ذا معنى."},
                {"term": "Profiles", "def": "تجميع خدمات اختيارية (`--profile monitoring`) عشان ما تشغّلش كل حاجة دائمًا."},
                {"term": "`env_file`", "def": "ملف `.env` بمتغيرات بيئة — **لازم يكون في `.gitignore`** وفيه `.env.example` موثق."},
                {"term": "Ports: published مقابل target", "def": "`\"8080:8080\"` = منفذ المضيف:منفذ الحاوية. الخدمات الداخلية **ما تحتاجش** published ports."},
                {"term": "Restart policy", "def": "`no` · `always` · `on-failure` · `unless-stopped`. للتطوير: `unless-stopped` — للإنتاج على K8s: المنسّق بيتعامل معاها."},
                {"term": "Override file", "def": "`docker-compose.override.yml` بيتحمّل تلقائيًا مع `docker-compose.yml` — للتطوير فقط (منافذ، بيئة، bind mounts)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) ملف compose كامل لنظام المرحلة 5"},
            {"type": "code", "lang": "yaml", "filename": "docker-compose.yml", "title": "بنية + 5 خدمات + healthchecks + ترتيب إقلاع", "code": r'''
# ★ الصيغة الحديثة: مفيش `version:` (اتشالت؛ بتتحذر لو موجودة)
name: shop

# ═══ قيم مشتركة (anchors) — تقليل التكرار بلا سحر ═══
x-dotnet-service: &dotnet-service
  restart: unless-stopped
  init: true                     # ✓ PID 1 سليم: يلمّ العمليات اليتيمة ويستقبل الإشارات
  networks: [shop-net]
  security_opt:
    - no-new-privileges:true     # ✓ تصعيد صلاحيات ممنوع (درس 6.1.3)
  logging:
    driver: json-file
    options: { max-size: "10m", max-file: "3" }   # ✓ بلا لوجات تملأ القرص

x-app-env: &app-env
  ASPNETCORE_ENVIRONMENT: Production
  ASPNETCORE_HTTP_PORTS: "8080"
  DOTNET_gcServer: "1"
  OTEL_SERVICE_NAME: ${OTEL_SERVICE_NAME:-shop}

services:
  # ══════════ البنية التحتية ══════════
  postgres:
    image: postgres:18-alpine
    container_name: shop-postgres       # ⚠ اسم ثابت = ما ينفعش replicas (شوف الـdanger تحت)
    environment:
      POSTGRES_USER: shop
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?required — حطها في .env}   # ✓ فشل صريح لو ناقصة
      POSTGRES_DB: shopdb
    volumes:
      - pg-data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d:ro   # ✓ سكربتات التهيئة عند أول تشغيل فقط
    ports:
      - "127.0.0.1:5432:5432"          # ★ ربط على loopback فقط — بلا كشف عام
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop -d shopdb"]
      interval: 5s
      timeout: 5s
      retries: 12
      start_period: 20s
    networks: [shop-net]

  redis:
    image: redis:8-alpine
    command: ["redis-server", "--appendonly", "yes", "--maxmemory", "256mb",
              "--maxmemory-policy", "allkeys-lru"]
    volumes: [redis-data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks: [shop-net]

  rabbitmq:
    image: rabbitmq:4-management-alpine
    hostname: shop-rabbit                # ✓ اسم العقدة ثابت (بيأثر على بيانات الوسيط)
    environment:
      RABBITMQ_DEFAULT_USER: shop
      RABBITMQ_DEFAULT_PASS: ${RABBIT_PASSWORD:?required — حطها في .env}
      RABBITMQ_DEFAULT_VHOST: shop
    volumes:
      - rabbit-data:/var/lib/rabbitmq
      - ./infra/rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
      - ./infra/rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro  # ★ البنية ككود (درس 5.2.1)
    ports:
      - "127.0.0.1:5672:5672"
      - "127.0.0.1:15672:15672"          # لوحة الإدارة — loopback فقط
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 10s
      retries: 12
      start_period: 40s
    networks: [shop-net]

  # ══════════ مهمة لمرة واحدة: الترحيلات والبذر ══════════
  migrations:
    build:
      context: .
      dockerfile: src/Shop.Orders/Dockerfile
    command: ["dotnet", "Shop.Orders.dll", "--migrate"]   # ✓ وضع خاص في التطبيق (expand/contract — درس 3.3.4)
    environment:
      <<: *app-env
      ConnectionStrings__shopdb: ${ORDERS_DB_CONNECTION}
    depends_on:
      postgres: { condition: service_healthy }
    restart: "no"                        # ★ مهمة: ما تعيدش للأبد
    networks: [shop-net]

  # ══════════ الخدمات ══════════
  catalog:
    build: { context: ., dockerfile: src/Shop.Catalog/Dockerfile }
    image: shop/catalog:${IMAGE_TAG:-dev}
    <<: *dotnet-service
    environment:
      <<: *app-env
      OTEL_SERVICE_NAME: catalog
      ConnectionStrings__shopdb: ${CATALOG_DB_CONNECTION}
      ConnectionStrings__cache: redis:6379
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
      migrations: { condition: service_completed_successfully }   # ✓ الترحيلات خلصت الأول

  orders:
    build: { context: ., dockerfile: src/Shop.Orders/Dockerfile }
    image: shop/orders:${IMAGE_TAG:-dev}
    <<: *dotnet-service
    environment:
      <<: *app-env
      OTEL_SERVICE_NAME: orders
      ConnectionStrings__shopdb: ${ORDERS_DB_CONNECTION}
      ConnectionStrings__cache: redis:6379
      ConnectionStrings__rabbit: amqp://shop:${RABBIT_PASSWORD}@rabbitmq:5672/shop
      Services__catalog: http://catalog:8080          # ✓ discovery يدوي في compose (درس 6.1.1)
    ports:
      - "127.0.0.1:8081:8080"
    depends_on:
      postgres:  { condition: service_healthy }
      rabbitmq:  { condition: service_healthy }
      migrations: { condition: service_completed_successfully }

  payments:
    build: { context: ., dockerfile: src/Shop.Payments/Dockerfile }
    image: shop/payments:${IMAGE_TAG:-dev}
    <<: *dotnet-service
    environment:
      <<: *app-env
      OTEL_SERVICE_NAME: payments
      ConnectionStrings__shopdb: ${PAYMENTS_DB_CONNECTION}
      ConnectionStrings__rabbit: amqp://shop:${RABBIT_PASSWORD}@rabbitmq:5672/shop
    depends_on:
      rabbitmq:  { condition: service_healthy }
      migrations: { condition: service_completed_successfully }
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512M }        # ✓ حدود (bulkhead على مستوى الحاوية)

  notifications:
    build: { context: ., dockerfile: src/Shop.Notifications/Dockerfile }
    image: shop/notifications:${IMAGE_TAG:-dev}
    <<: *dotnet-service
    environment:
      <<: *app-env
      OTEL_SERVICE_NAME: notifications
      ConnectionStrings__rabbit: amqp://shop:${RABBIT_PASSWORD}@rabbitmq:5672/shop
    depends_on:
      rabbitmq: { condition: service_healthy }

  gateway:
    build: { context: ., dockerfile: src/Shop.Gateway/Dockerfile }
    image: shop/gateway:${IMAGE_TAG:-dev}
    <<: *dotnet-service
    environment:
      <<: *app-env
      OTEL_SERVICE_NAME: gateway
      Services__orders:  http://orders:8080
      Services__catalog: http://catalog:8080
    ports:
      - "8080:8080"                                   # ← الوحيد المكشوف للخارج
    depends_on:
      orders:  { condition: service_started }
      catalog: { condition: service_started }

  # ══════════ اختيارية: مراقبة ══════════
  aspire-dashboard:
    image: mcr.microsoft.com/aspire/dashboard:latest
    profiles: [monitoring]                            # ← ما تشتغلش إلا بـ --profile monitoring
    ports:
      - "127.0.0.1:18888:18888"
      - "127.0.0.1:4317:18889"
    environment:
      ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS: "true"   # ✓ محلي فقط + loopback
    networks: [shop-net]

volumes:
  pg-data:
  redis-data:
  rabbit-data:

networks:
  shop-net:
    driver: bridge
'''},
            {"type": "code", "lang": "yaml", "filename": "docker-compose.override.yml", "title": "للتطوير فقط (بيتحمّل تلقائيًا — ومتضافش للـCI)", "code": r'''
# ★ يُحمّل تلقائيًا مع docker-compose.yml في `docker compose up`
# في CI استخدم: docker compose -f docker-compose.yml up   (بلا override)
services:
  orders:
    environment:
      ASPNETCORE_ENVIRONMENT: Development
      OTEL_EXPORTER_OTLP_ENDPOINT: http://aspire-dashboard:18889   # ← لوحة محلية (درس 5.3.2)
    ports:
      - "8081:8080"

  catalog:
    environment:
      ASPNETCORE_ENVIRONMENT: Development
    ports:
      - "8082:8080"

  postgres:
    ports:
      - "127.0.0.1:5432:5432"     # وصول مباشر من IDE/أدوات

  # ✓ تسريع دورة التطوير: Compose Watch بيعيد البناء/التشغيل عند تعديل الكود
  #   (يحتاج Compose 2.22+ — تحقق من `docker compose version`)
  # develop:
  #   watch:
  #     - action: rebuild
  #       path: ./src/Shop.Orders
'''},
            {"type": "code", "lang": "bash", "filename": ".env.example", "title": "متغيرات البيئة (انسخه لـ`.env` — و`.env` في `.gitignore`)", "code": r'''
# ── نسخة موثقة تُرفع للـgit؛ `.env` الحقيقي لا يُرفع أبدًا ──
POSTGRES_PASSWORD=change-me-local-only
RABBIT_PASSWORD=change-me-local-only

# connection strings كاملة (بلا أسرار في ملف compose)
ORDERS_DB_CONNECTION=Host=postgres;Port=5432;Database=shopdb;Username=shop;Password=change-me-local-only
CATALOG_DB_CONNECTION=Host=postgres;Port=5432;Database=shopdb;Username=shop;Password=change-me-local-only
PAYMENTS_DB_CONNECTION=Host=postgres;Port=5432;Database=shopdb;Username=shop;Password=change-me-local-only

IMAGE_TAG=dev
OTEL_SERVICE_NAME=shop-local

# ✓ تأكد:
#   grep -n "\.env" .gitignore     → لازم يكون موجود
#   git check-ignore -v .env       → لازم يتجاهل
'''},
            {"type": "heading", "level": 2, "text": "2) أوامر compose اللي هتستخدمها كل يوم"},
            {"type": "code", "lang": "bash", "title": "تشغيل · فحص · تشخيص · إيقاف", "code": r'''
# ═══ تحقق من الملف قبل ما تشغّل (بيهرّ الأخطاء بدري) ═══
docker compose config --quiet && echo "compose file OK"
docker compose config | less          # ← يعرض الملف **بعد** دمج override وحل المتغيرات

# ═══ التشغيل ═══
docker compose up -d --build          # بناء + تشغيل في الخلفية
docker compose --profile monitoring up -d   # ← مع خدمات المراقبة الاختيارية
docker compose up -d orders payments  # ← خدمات محددة (وتبعياتها تلقائيًا)
docker compose -f docker-compose.yml up -d  # ★ في CI: بلا override

# ═══ الحالة ═══
docker compose ps                     # الحالة + المنافذ
docker compose ps --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'
docker compose top                    # العمليات جوه كل حاوية

# ═══ اللوجات ═══
docker compose logs -f --tail 100 orders
docker compose logs --since 10m --no-log-prefix payments | grep -i error

# ═══ التشخيص ═══
docker compose exec orders sh -c 'id; printenv | grep -E "ASPNETCORE|ConnectionStrings" | sed "s/Password=.*/Password=***/"'
docker compose exec postgres psql -U shop -d shopdb -c '\dt' -c 'SELECT COUNT(*) FROM orders.orders;'
docker compose exec rabbitmq rabbitmqctl list_queues name messages_ready consumers
docker compose exec redis redis-cli info memory | head -5

# ═══ فحص الصحة يدويًا ═══
curl -s -o /dev/null -w 'orders  %{http_code}\n' http://localhost:8081/health
curl -s -o /dev/null -w 'gateway %{http_code}\n' http://localhost:8080/health

# ═══ اختبار الفشل (درس 5.3.3 / capstone المرحلة 5) ═══
docker compose stop payments          # ← أثبت إن الأحداث ما بتضيعش (Outbox + redelivery)
docker compose start payments
docker compose kill -s SIGKILL orders # ← فشل عنيف: إعادة تشغيل وسلوك واضح

# ═══ التحديث والنشر المحلي ═══
docker compose pull                   # سحب أحدث الصور
docker compose up -d --no-deps --force-recreate orders   # إعادة إنشاء خدمة واحدة فقط

# ═══ الإيقاف ═══
docker compose down                   # يوقف ويشيل الحاويات والشبكة
docker compose down --remove-orphans  # + خدمات مش موجودة في الملف دلوقتي
docker compose down -v                # ⚠⚠ **يمحو الـvolumes = كل البيانات** — لا تستخدمه بلا تفكير

# ═══ القياس ═══
docker stats --no-stream              # CPU/ذاكرة لكل حاوية
docker compose ps -q | xargs docker inspect --format '{{.Name}} {{.State.Health.Status}}'
'''},
            {"type": "table", "head": ["condition في `depends_on`", "معناها", "متى تستخدمها", "الفخ"], "rows": [
                ["`service_started` (افتراضي)", "العملية بدأت — **مش معناه إنها جاهزة**", "خدمات بتتعافى بنفسها (retry)", "تفتكر إن DB جاهزة وهي لسه بتتهيّأ"],
                ["`service_healthy`", "أول healthcheck نجح", "★ قواعد البيانات، الوسيط، أي تابع حرج", "بلا healthcheck في التابع = الشرط بلا معنى (ويسبب خطأ)"],
                ["`service_completed_successfully`", "الحاوية اشتغلت وخرجت بكود 0", "مهام لمرة واحدة: migrations، seed، codegen", "لو المهمة فشلت → التابعين ما يشتغلوش (مقصود)"],
                ["(بلا `depends_on`)", "ترتيب عشوائي", "خدمات مستقلة تمامًا", "تطبيقات بتفترض ترتيبًا ضمنيًا"],
                ["`restart: on-failure` + depends_on", "إعادة محاولة عند الفشل", "مستهلكين رسائل", "حلقة إعادة لا نهائية لو السبب تكوين غلط"],
                ["`long` restart + `start_period`", "مهلة إقلاع قبل اعتبارها فاشلة", "تطبيقات JVM/.NET بتحميل ثقيل", "healthcheck retries قليلة → الحاوية تُعتبر فاشلة وهي لسه بتقلع"],
            ]},
            {"type": "callout", "kind": "danger", "title": "9 أخطاء في compose بتكلّف وقت (وبيانات)",
             "md": """
1. **`docker compose down -v` بلا تفكير** = محو قواعد البيانات والوسيط. استخدم `down` عادي، و`-v` فقط لو تقصد إعادة ضبط كاملة.
2. **`container_name` ثابت** = ما تقدرش تشغّل أكثر من نسخة (`docker compose up --scale orders=3` هيفشل).
   استخدم أسماء الشبكة (service names) بدلًا منه.
3. **المنشور مقابل المستهدف**: `"8080:8080"` = مضيف:حاوية. لو صورتك بتسمع على 8080 وكتبت `"8080:80"` → مفيش اتصال.
4. **كشف منافذ البنية العامة**: `-p 5432:5432` بلا `127.0.0.1` = قاعدة بياناتك مفتوحة للشبكة.
   ★ اربط على loopback دائمًا محليًا، ولا تكشف DB/Redis/RabbitMQ خالص لو مش محتاج.
5. **أسرار في ملف compose** (أو في `.env` مرفوع للـgit) — استخدم `.env` + `.gitignore` + `.env.example` موثق،
   وفي الإنتاج: K8s Secrets/Key Vault (درس 6.2.3).
6. **`depends_on` بلا healthcheck** = وهم الترتيب. الخدمة تبدأ وDB لسه بتتهيّأ → فشل وصخب.
7. **الاعتماد على `latest`** = البيئة بتتغير من غير ما تعمل deploy. ثبّت الإصدارات في كل الصور.
8. **compose override في CI** = الإعدادات المحلية بتتسرب للاختبارات. استخدم `-f docker-compose.yml` صراحةً.
9. **مفيش حدود موارد** = حاوية واحدة بتاكل ذاكرة الجهاز كله. `deploy.resources.limits` + `mem_limit` محليًا.

⚠ **compose مش منصة إنتاج**: مفيش rescheduling، ولا rolling updates، ولا service discovery ديناميكي،
ولا autoscaling. هو ممتاز للتطوير/CI/بيئات صغيرة ثابتة — وللإنتاج الحقيقي Kubernetes أو Container Apps (درس 6.1.4 و6.2.1).
"""},
            {"type": "table", "head": ["", "Docker Compose", ".NET Aspire", "Kubernetes"], "rows": [
                ["الغرض الأساسي", "تشغيل نظام متعدد الحاويات", "تطوير محلي منسّق + telemetry", "تشغيل إنتاجي مرن"],
                ["الملف", "`docker-compose.yml`", "AppHost (كود C#)", "manifests YAML/Helm"],
                ["يحتاج", "Docker فقط", ".NET SDK + Docker", "cluster (محلي/سحابي)"],
                ["Service discovery", "أسماء الخدمات (DNS)", "`services__x__https__0` تلقائيًا", "DNS + Services + Ingress"],
                ["ترتيب الإقلاع", "`depends_on` + healthchecks", "`WaitFor`/`WaitForCompletion`", "probes (بلا ترتيب صريح)"],
                ["إعادة جدولة/توسع تلقائي", "✗", "✗", "✓ (HPA/rollouts)"],
                ["Rolling update / rollback", "✗ (إعادة إنشاء)", "✗", "✓"],
                ["لوحة تشخيص", "✗ (logs فقط)", "✓ (traces/metrics/logs)", "عبر أدوات خارجية"],
                ["متعدد اللغات", "✓ ممتاز", "✓ (Java/Go/TS/Python…)", "✓"],
                ["مناسب لـ", "CI · بيئات صغيرة · مشاركة البيئة", "تطوير يومي · تشخيص", "إنتاج · فرق كبيرة · SLA"],
            ]},
            {"type": "checkpoints", "items": [
                "أكتب compose file كامل لنظامي: بنية تحتية + خدمات + شبكة + volumes + healthchecks + ترتيب إقلاع.",
                "أفرّق بين `service_started` و`service_healthy` و`service_completed_successfully` وأستخدم كل واحد في مكانه.",
                "أفصل إعدادات التطوير في `docker-compose.override.yml` وأتجنبه في CI، وأدير الأسرار عبر `.env` (غير مرفوع) + `.env.example`.",
                "أتقن أوامر التشغيل والتشخيص: `config` · `ps` · `logs` · `exec` · `down` (وأعرف خطر `-v`).",
                "أعرف حدود compose مقابل Aspire مقابل Kubernetes وأختار الأداة المناسبة للغرض.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`depends_on: postgres: {condition: service_healthy}` — الشرط اللازم؟",
                 "options": [
                     "مفيش شرط",
                     "خدمة postgres يكون عندها **healthcheck** معرّف — وإلا الشرط بلا معنى (أو خطأ)",
                     "restart policy",
                     "volume مشترك",
                 ], "answer": 1,
                 "explain": "`service_healthy` بيتطلب healthcheck في التابع. بدونه compose ما يقدرش يعرف «صحي» من «بدأت العملية»."},
                {"q": "مهمة الترحيلات (migrations) — إزاي تُعرّف؟",
                 "options": [
                     "خدمة عادية بـ`restart: always`",
                     "خدمة بأمر خاص + `restart: \"no\"` + التابعين بيستخدموا `service_completed_successfully`",
                     "بلا تعريف (تتنفذ يدويًا)",
                     "داخل الـentrypoint لكل خدمة",
                 ], "answer": 1,
                 "explain": "لو كل خدمة بتعمل migrations في الـstartup → سباق وصراعات. الأفضل مهمة واحدة تُنفَّذ مرة، والباقي ينتظر نجاحها."},
                {"q": "`ports: [\"5432:5432\"]` لخدمة postgres. المشكلة؟",
                 "options": [
                     "مفيش مشكلة",
                     "المنفذ منشور على **كل** الواجهات → أي جهاز على الشبكة يقدر يوصل لقاعدة بياناتك. اربط `127.0.0.1:5432:5432` أو ما تنشرهوش خالص",
                     "الترتيب غلط",
                     "بيبطّئ الإقلاع",
                 ], "answer": 1,
                 "explain": "القاعدة: الخدمات الداخلية على الشبكة الداخلية فقط. النشر يكون للمضيف المحلي (loopback) أو للـgateway فقط."},
                {"q": "`container_name: shop-orders` — إيه أثره؟",
                 "options": [
                     "مفيش أثر",
                     "يمنع تشغيل أكثر من نسخة من الخدمة (`--scale`) ويسبب تعارض أسماء لو النظام اتشغل مرتين",
                     "بيسرّع الإقلاع",
                     "مطلوب للشبكة",
                 ], "answer": 1,
                 "explain": "استخدم اسم الخدمة كـhostname (compose بيحلّه تلقائيًا). الأسماء الثابتة بتكسر التوسع والتشغيل المتعدد."},
                {"q": "إمتى تستخدم `docker-compose.override.yml`؟",
                 "options": [
                     "في CI والإنتاج",
                     "لإعدادات التطوير المحلي فقط (منافذ، بيئة Development، OTLP للوحة) — وفي CI تستخدم `-f docker-compose.yml` بدونه",
                     "دائمًا",
                     "للأسرار",
                 ], "answer": 1,
                 "explain": "الـoverride بيتحمّل تلقائيًا محليًا. في CI لازم تستثنيه صراحةً عشان الاختبارات تشتغل بإعدادات قريبة من الإنتاج."},
                {"q": "`docker compose down -v` بيعمل إيه؟",
                 "options": [
                     "يوقف الحاويات بس",
                     "يوقف الحاويات **ويمحو الـvolumes** = كل البيانات المحلية (قواعد البيانات، الرسائل) تضيع",
                     "يحذف الصور من الـregistry",
                     "يعيد البناء",
                 ], "answer": 1,
                 "explain": "`down` = إزالة الحاويات والشبكة. `-v` تضيف محو البيانات. استخدمها فقط لما تقصد إعادة ضبط كاملة للبيئة."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "compose يشغّل نظامك كاملًا بأمر واحد",
                 "md": "اكتب `docker-compose.yml` لنظامك (بنية تحتية + كل الخدمات + gateway) مع healthchecks وترتيب إقلاع صحيح ومهمة migrations، و`.env.example` موثق، و`docker-compose.override.yml` للتطوير. أثبت إن مطور جديد يقدر يشغّل النظام بأمرين فقط.",
                 "criteria": [
                     "`docker compose config --quiet` ناجح (بلا أخطاء/تحذيرات)",
                     "كل تابع حرج عليه healthcheck + `service_healthy`، ومهمة الترحيلات `service_completed_successfully` مع `restart: \"no\"`",
                     "مفيش أسرار في الملف: `${VAR:?required}` + `.env.example` + `.env` في `.gitignore` (مخرجات `git check-ignore`)",
                     "البنية التحتية منشورة على `127.0.0.1` فقط (أو مش منشورة خالص) — والـgateway هو الوحيد المكشوف",
                     "`init: true` + `no-new-privileges` + حدود موارد + حدود لوجات لكل خدمة .NET",
                     "إثبات: `docker compose up -d --build` من استنساخ نظيف → كل الخدمات healthy + `/health` بـ200 + طلب أعمال كامل بينجح (مخرجات SQL/الوسيط)",
                     "إثبات الترتيب: أوقف postgres وشغّل `up` → اللوجات بتوضح الانتظار لحد الصحة (مش فشل)",
                     "فقرة في README: أمران للتشغيل + المتطلبات + إزاي توقف/تمحو البيانات",
                 ],
                 "hint": "ابدأ بالبنية التحتية وحدها (postgres+redis+rabbit) وتأكد إنهم healthy، بعدين أضف خدمة واحدة، وبعدين الباقي. إضافة الكل مرة واحدة بتصعّب التشخيص.",
                 "solution": "",
                 "resources": [
                     {"label": "Compose file reference", "url": "https://docs.docker.com/reference/compose-file/"},
                     {"label": "Compose healthchecks & startup order", "url": "https://docs.docker.com/compose/how-tos/startup-order/"},
                 ]},
                {"id": "t2", "title": "سيناريو فشل + مراقبة محلية",
                 "md": "شغّل النظام مع بروفايل مراقبة (Aspire dashboard أو pgAdmin/Portainer)، ونفّذ 3 سيناريوهات فشل (إيقاف مستهلك · قتل DB · ملء طابور)، وسجّل الملاحظات (لوجات/طوابير/حالات) وإزاي النظام اتصرف — وقارن بالسلوك المتوقع من capstone المرحلة 5.",
                 "criteria": [
                     "بروفايل مراقبة اختياري (`--profile monitoring`) بلا كشف عام (loopback فقط)",
                     "3 سيناريوهات: `stop payments` · `kill postgres` · ذروة رسائل في طابور — لكل واحد الأمر + المخرجات",
                     "لكل سيناريو: السلوك المتوقع (مكتوب **قبل** التنفيذ) مقابل الملاحظ + تفسير الفرق",
                     "إثبات إن الأحداث ما ضاعتش (Outbox/redelivery) — استعلام SQL + عدد الرسائل في الطابور",
                     "إثبات إن `restart: unless-stopped`/`init: true` بيشتغلوا (الحاوية رجعت لوحدها)",
                     "جدول «إيه اللي ناقص في compose مقابل الإنتاج» (rescheduling/rolling update/discovery) — 3 صفوف على الأقل",
                 ],
                 "solution": "",
                 "resources": [
                     {"label": "Compose profiles", "url": "https://docs.docker.com/compose/how-tos/profiles/"},
                     {"label": "Aspire dashboard standalone", "url": "https://aspire.dev/dashboard/standalone/"},
                     {"label": "RabbitMQ CLI/monitoring", "url": "https://www.rabbitmq.com/docs/monitoring"}
            ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Docker Compose docs", "url": "https://docs.docker.com/compose/"},
                {"label": "Compose file specification", "url": "https://docs.docker.com/reference/compose-file/"},
                {"label": "Startup order & healthchecks", "url": "https://docs.docker.com/compose/how-tos/startup-order/"},
                {"label": "Compose in CI/CD", "url": "https://docs.docker.com/compose/how-tos/integration-testing/"},
                {"label": "Migrate from Docker Compose to Aspire", "url": "https://aspire.dev/app-host/migrate-from-docker-compose/"},
                {"label": "PostgreSQL Docker image", "url": "https://hub.docker.com/_/postgres"},
            ]},
        ],
    },
]
