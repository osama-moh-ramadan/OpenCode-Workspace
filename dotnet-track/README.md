# مسار .NET — من بعد EF Core لحد الوظيفة

تطبيق تعلّم **محلي بالكامل** مبني على نمط منصات التعلّم التفاعلية (مسار → مراحل → دروس → شرح وكود → Quiz ومهام → تتبّع تقدّم)،
بكود وتصميم أصليين ومحتوى خاص بالمسار. **من غير تسجيل دخول، ومن غير إنترنت، والتقدّم بيتحفظ على جهازك.**

> نقطة البداية المفترضة: خلصت C# → OOP → LINQ → ASP.NET Core Web API → **Entity Framework Core**.
> من هناك لحد ما تمضي عقد: **10 مراحل · 36 موديول · 134 درس ومهمة · ~111 ساعة · 10 مشاريع مرحلة (Capstones)**.
> الإصدار المستهدف: **.NET 10 (LTS) · C# 14 · EF Core 10 · ASP.NET Core 10 · Aspire 13**.

---

## تشغيل التطبيق

الطريقة الأولى (Python — من غير أي تثبيت):
```bash
cd dotnet-track
python3 server.py            # → http://127.0.0.1:8123
PORT=9000 python3 server.py  # منفذ مختلف
```

الطريقة التانية (Node 18+):
```bash
node server.mjs              # → http://127.0.0.1:8123
```

افتح العنوان في المتصفح وخلاص. كل حاجة تعمل offline بعد أول تحميل.

### الفرق بين السيرفر وفتح `index.html` مباشرة
التطبيق بيشتغل في الحالتين، لكن **السيرفر المحلي أفضل** لأنه:
- بيحفظ تقدّمك في ملف حقيقي `progress.json` على جهازك (مش بس في `localStorage`)، فتنقله بين الأجهزة والمتصفحات.
- بيتجنب قيود `file://` على `fetch` (لو فتحت الملف مباشرة في بعض المتصفحات، المنهج ممكن ما يتحمّلش).

`progress.json` بيتكتب ذريًا (atomic write) ومحدود بـ4MB، وهو **مش** في git.

---

## المراحل العشرة

| # | المرحلة | المحتوى الأساسي | المدة |
|---|---|---|---|
| 1 | الكود المحترف والاختبار | SOLID عمليًا، DI lifetimes، Options والأسرار، FluentValidation، ProblemDetails، Serilog، C# الحديث، ثم xUnit v3 / NSubstitute / WebApplicationFactory / Testcontainers | 3-4 أسابيع |
| 2 | ASP.NET Core المتقدم وAPIs إنتاجية | Minimal APIs، OpenAPI 3.1 + Scalar، الإصدارات والترقيم، Middleware/Filters، Rate limiting، Caching، JWT + Refresh، Identity، OIDC، تأمين الـAPI، SignalR، BackgroundService، Health checks | 4 أسابيع |
| 3 | البيانات والأداء | SQL (فهارس، خطط تنفيذ، عزل، deadlocks)، Dapper، EF Core 10 متقدم، Migrations في CI، Redis، NoSQL، BenchmarkDotNet/k6، async في العمق، Span، NativeAOT | 4 أسابيع |
| 4 | المعمارية والأنماط | Clean/Onion، Vertical Slice، Modular Monolith، ADRs، DDD تكتيكي، CQRS + MediatR، Outbox/Inbox، Event Sourcing | 3 أسابيع |
| 5 | الميكروسيرفيسز والمراسلة | حدود الخدمات، gRPC، YARP، RabbitMQ/Kafka/Service Bus، MassTransit، Sagas، Polly/Resilience، Idempotency، .NET Aspire، Contract tests | 4 أسابيع |
| 6 | الحاويات والسحابة وDevOps | Docker وCompose وتأمين الصور، Kubernetes الأساسي، Azure (Container Apps/Functions/Key Vault/البيانات/التكلفة)، GitHub Actions، Quality gates، Blue-Green/Canary، Bicep/Terraform | 4 أسابيع |
| 7 | المراقبة والتشغيل والأمان | الأعمدة الثلاثة، OpenTelemetry، Serilog مركزي، Prometheus/Grafana، SLOs وتنبيهات، Runbooks وPostmortems، سلسلة التوريد وSBOM، OWASP، Threat modeling، بيانات شخصية | 3 أسابيع |
| 8 | الواجهة والتسليم الكامل | JS/TS لمطور Backend، استهلاك API بأمان، CSS/Tailwind، حالات الواجهة، ثم مسار Blazor أو React، وللمحة MAUI/Avalonia | 3 أسابيع |
| 9 | تصميم الأنظمة ومهارات السينيور | مفردات التصميم، 3 مسائل تصميم (URL shortener / Notifications / Feed)، Sharding وReplication، خوارزميات للمقابلات، Code Review، Agile، Git workflows، الكتابة التقنية | 4 أسابيع |
| 10 | البورتفوليو والبحث عن وظيفة | 3 مشاريع توظيف، README وتوثيق، GitHub profile، النشر live، Open Source، CV وATS، LinkedIn، الشهادات، المجتمعات، مراحل المقابلة، بنك 60 سؤال، Live coding/Take-home، STAR، التفاوض والرواتب، أول 90 يوم | 3-4 أسابيع |

كل مرحلة بتنتهي بـ**Capstone** بمعايير قبول قابلة للقياس (مش «اتعلمت الموضوع»).

---

## إيه جوه كل درس

- **أهداف** — في النهاية هتكون قادر على إيه بالظبط.
- **شرح عربي** والمصطلحات والكود بالإنجليزي (زي سوق الشغل).
- **كود حقيقي** بـC#/.NET 10 مع تلوين بناءً على محلل مكتوب خصيصًا للتطبيق (من غير أي CDN أو مكتبات خارجية).
- **مصطلحات، جداول مقارنة، خطوات مرقّمة، وتنبيهات** (تحذير/نصيحة/معلومة).
- **Quiz** بأسئلة اختيار من متعدد: تصحيح فوري + شرح لكل إجابة + النتيجة محفوظة + إعادة محاولة.
- **مهام كود** بمعايير قبول، تلميح، وحل مرجعي (بيظهر لما تفتحه إنت).
- **نقاط تحقق** قبل ما تعلّم الدرس كمكتمل.
- **مصادر** رسمية (Microsoft Learn + توثيق المكتبات).
- **ملاحظاتك** الخاصة بالدرس — بتتحفظ تلقائيًا.

---

## حالة المحتوى

**كل الدروس مكتوبة: 134 درسًا / 111.1 ساعة.** المراحل العشر مكتملة 100% بما فيها العشرة Capstones،
وآخر مرحلة (البورتفوليو والبحث عن وظيفة) تغطي: اختيار 3 مشاريع · README وتوثيق · GitHub والملف الشخصي ·
نشر حي على Azure · مساهمة Open Source · السيرة الذاتية · LinkedIn · الشهادات · المجتمعات ·
جولات المقابلة · بنك 60 سؤالًا تقنيًا · Live coding والـtake-home · قصص STAR · التفاوض على العروض ·
أول 90 يومًا · Capstone «Job-Ready Kit».

| المرحلة | الحالة | الدروس المكتوبة | المتبقي |
|---|---|---|---|
| 1 · الكود المحترف والاختبار | ✅ مكتملة | 14/14 (10.2 س) | — |
| 2 · ASP.NET Core المتقدم وAPIs إنتاجية | ✅ مكتملة | 16/16 (12.7 س) | — |
| 3 · البيانات والأداء | ✅ مكتملة | 12/12 (10.2 س) | — |
| 4 · المعمارية والأنماط | ✅ مكتملة | 9/9 (9.2 س) | — |
| 5 · الميكروسيرفيسز والمراسلة | ✅ مكتملة | 14/14 (12.8 س) | — |
| 6 · الحاويات والسحابة وDevOps | ✅ مكتملة | 16/16 (13.5 س) | — |
| 7 · المراقبة والتشغيل والأمان | ✅ مكتملة | 11/11 (8.9 س) | — |
| 8 · الواجهة والتسليم الكامل | ✅ مكتملة | 10/10 (10.4 س) | — |
| 9 · تصميم الأنظمة ومهارات السينيور | ✅ مكتملة | 16/16 (12.5 س) | — |
| 10 · البورتفوليو والبحث عن وظيفة | ✅ مكتملة | 16/16 (10.8 س) | — |

لوحة «المحتوى بيتكتب» لسه موجودة في التطبيق كخلفية احتياطية لو أضفت درسًا جديدًا في المنهج قبل كتابته،
لكن كل الدروس الحالية عندها محتوى كامل.

كل درس ملف JSON مستقل في `content/lessons/` (134 ملفًا) — من غير ما تلمس كود التطبيق.
المصدر في `tools/lessons_s*.py`، والبناء بـ`npm run build` (أو `python3 tools/build_lessons.py && python3 tools/build.py`).

---

## بنية المشروع

```
dotnet-track/
├── index.html                 # هيكل الصفحة (RTL، بدون أي اعتماديات خارجية)
├── assets/
│   ├── css/app.css            # نظام التصميم: tokens + مكونات + وضع فاتح/داكن + responsive
│   └── js/
│       ├── app.js             # الإقلاع + الراوتر (hash-based)
│       ├── views.js           # الشاشات: الرئيسية، المراحل، المرحلة، الدرس، البحث، التقدّم
│       ├── blocks.js          # عرض كتل المحتوى + تفاعل الـQuiz والمهام
│       ├── curriculum.js      # تحميل المنهج والفهرسة والبحث
│       ├── store.js           # التقدّم: localStorage + مزامنة progress.json
│       ├── md.js              # محوّل markdown-lite (آمن: بيهرب كل HTML)
│       ├── highlight.js       # تلوين كود C#/JSON/Bash/YAML/XML/SQL/Dockerfile/HTTP/JS
│       └── util.js            # أدوات DOM وتنسيق
├── content/
│   ├── curriculum.json        # المنهج الكامل (مولّد — ما تعدّلوش بإيدك)
│   └── lessons/<id>.json      # محتوى كل درس جاهز
├── tools/
│   ├── stages_a.py            # بيانات المراحل 1-5
│   ├── stages_b.py            # بيانات المراحل 6-10
│   ├── build.py               # يولّد content/curriculum.json
│   ├── lessons_s1_a.py        # محتوى دروس المرحلة 1 (1-4)
│   ├── lessons_s1_b.py        # محتوى دروس المرحلة 1 (5-7) + Capstone
│   ├── build_lessons.py       # يكتب ملفات الدروس + يتحقق من صحتها
│   └── smoke-test.mjs         # اختبار jsdom لكل الشاشات والتفاعلات
├── server.py                  # سيرفر محلي (Python stdlib)
├── server.mjs                 # سيرفر محلي (Node، بدون اعتماديات)
├── progress.json              # تقدّمك — بيتنشأ تلقائيًا ومش في git
└── package.json
```

### إضافة/تعديل المحتوى (بدون لمس كود التطبيق)

```bash
# 1) عدّل tools/stages_a.py أو stages_b.py (عناوين/أهداف/مصادر)
# 2) أو أضف درس كامل في tools/lessons_s1_b.py (أو ملف جديد واستورده في build_lessons.py)
python3 tools/build_lessons.py   # يكتب content/lessons/*.json + يتحقق من الأنواع والإجابات
python3 tools/build.py           # يحدّث curriculum.json وعلامات "hasContent"
```

`build_lessons.py` بيرفض: نوع block مجهول، سؤال Quiz بإجابة خارج النطاق، جدول أعمدته مش متطابقة،
مصدر من غير رابط http(s)، ومهمة من غير معايير قبول — عشان المحتوى ما يكسرش العرض.

### صيغة كتل الدرس

```
text/md · heading · code{lang,title,filename,code} · callout{kind:tip|warn|note|goal}
table{head,rows} · steps{items} · terms{items} · checkpoints{items}
quiz{questions:[{q,options,answer,explain}]} · tasks{items:[{title,md,criteria,hint,solution}]}
resources{items:[{label,url}]}
```

داخل نصوص `md` تقدر تستخدم: `##` عناوين، `**bold**`, `` `code` ``, قوائم `-` و`1.`، `>` اقتباس،
جداول `|`، fenced code blocks بـ```` ```csharp ````، وروابط `[label](url)`.

---

## الاختبارات

```bash
npm i -D jsdom
npm test        # 40+ فحص: الإقلاع، المراحل، الدرس، الـQuiz، الحفظ، البحث، التقدّم، السمة، 404
```

الاختبار بيشغّل نفس وحدات التطبيق الحقيقية داخل jsdom مع fetch بيقرأ ملفات المشروع،
وبيتأكد مثلًا إن مفيش markdown خام بيسرب للواجهة، وإن النقر على إجابة Quiz يحفظ النتيجة،
وإن تعليم درس كمكتمل يحدّث الحلقة في الهيدر ويكتب في `localStorage` ويبعت لـ`progress.json`.

---

## الخصوصية

- مفيش حسابات، مفيش تحليلات، مفيش أي طلب لأي نطاق خارجي (كل الأصول محلية، حتى الـfavicon مرسوم inline).
- الروابط الخارجية في «المصادر» بتفتح في تبويب جديد بـ`rel="noopener noreferrer"` — وده بناءً على طلبك الصريح.
- تقدّمك في `localStorage` + `progress.json`. تقدر تصدّره/تستورده/تصفّره من شاشة «تقدّمي».

---

## ملاحظات

- التطبيق **أصلي** في الكود والتصميم والمحتوى: لم يُنسخ أي كود أو أصول أو شعار من أي منصة تعلّم تجارية.
- الخطوط من خطوط النظام (Segoe UI / Noto Naskh Arabic / Tahoma) عشان يشتغل offline بالكامل.
- الواجهة RTL، وبلوكات الكود LTR بشكل صريح.
