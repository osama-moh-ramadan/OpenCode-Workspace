"""Curriculum data, part A: stages 1-5 (after EF Core -> architecture/microservices).

Each lesson: L(title_ar, title_en, summary_ar, minutes, objectives, resources, kind)
Resources are (label, url) tuples. Official/stable links only.
"""


def L(title, title_en, summary, minutes, objectives, resources=(), kind="lesson"):
    return {
        "title": title,
        "title_en": title_en,
        "summary": summary,
        "minutes": minutes,
        "objectives": list(objectives),
        "resources": [{"label": l, "url": u} for l, u in resources],
        "kind": kind,
    }


def M(title, title_en, summary, lessons):
    return {"title": title, "title_en": title_en, "summary": summary, "lessons": lessons}


def S(title, title_en, summary, outcome, level, weeks, modules):
    return {
        "title": title,
        "title_en": title_en,
        "summary": summary,
        "outcome": outcome,
        "level": level,
        "weeks": weeks,
        "modules": modules,
    }


ML = "https://learn.microsoft.com"
DOTNET = ML + "/dotnet"
ASPNET = ML + "/aspnet/core"
EFCORE = ML + "/ef/core"
AZURE = ML + "/azure"

STAGES_A = [
    # ------------------------------------------------------------------ Stage 1
    S(
        "الكود المحترف والاختبار",
        "Professional Code Quality & Testing",
        "أول محطة بعد EF Core: تحوّل الكود اللي «شغال» لكود فريق إنتاجي — مبادئ، تحقق، أخطاء، لوجنج، واختبارات حقيقية.",
        "تقدر تبني Web API منظم، مُتحقَّق من مدخلاته، بيشرح أخطاءه بـProblemDetails، ومغطى باختبارات Unit + Integration بتشتغل على قاعدة بيانات حقيقية في Container.",
        "متوسط",
        "3-4 أسابيع",
        [
            M(
                "هندسة الكود اليومي",
                "Everyday Code Engineering",
                "الحاجات اللي بتفرق بين Junior وMid في أول Code Review: SOLID عمليًا، DI lifetimes، Options، Validation، الأخطاء، واللوجنج.",
                [
                    L(
                        "SOLID عمليًا مش نظريًا",
                        "SOLID in Practice, Not in Slides",
                        "إزاي المبادئ الخمسة بتبان في كود ASP.NET Core الحقيقي، وإمتى تطبيقها بيضر.",
                        30,
                        [
                            "تكسر كود Service مسؤولة عن كل حاجة وتعيد توزيع مسؤولياتها",
                            "تستخدم Dependency Inversion عشان تختبر Logic من غير قاعدة بيانات",
                            "تتعرف على over-engineering وإمتى تقف",
                        ],
                        [("Microsoft: Architectural principles", DOTNET + "/architecture/"), ("Refactoring Guru", "https://refactoring.guru/design-patterns")],
                    ),
                    L(
                        "دورة حياة الـDI والـScoped trap",
                        "DI Lifetimes and the Captive Dependency Trap",
                        "Singleton/Scoped/Transient في ASP.NET Core، وإزاي Singleton يمسك Scoped فيبوظ كل حاجة.",
                        25,
                        [
                            "تختار الـlifetime الصح لكل خدمة وتبررها",
                            "تكتشف captive dependency قبل ما تكسر Request",
                            "تستخدم keyed services وFactory patterns",
                        ],
                        [("Dependency injection in ASP.NET Core", ASPNET + "/fundamentals/dependency-injection")],
                    ),
                    L(
                        "الإعدادات والـOptions Pattern والأسرار",
                        "Configuration, Options Pattern and Secrets",
                        "appsettings، المتغيرات البيئية، User Secrets، IOptions/IOptionsSnapshot/IOptionsMonitor، وإزاي تمنع magic strings.",
                        25,
                        [
                            "تبني Strongly-typed settings لكل بيئة",
                            "تخزن الأسرار بره الكود وSource Control",
                            "تفرق بين IOptions وIOptionsSnapshot ومتى تحتاج reload",
                        ],
                        [("Options pattern", DOTNET + "/core/extensions/options"), ("Safe storage of app secrets", ASPNET + "/security/app-secrets")],
                    ),
                    L(
                        "التحقق من المدخلات: FluentValidation",
                        "Input Validation with FluentValidation",
                        "التحقق في Minimal APIs وControllers، قواعد قابلة للقراءة، ورسائل أخطاء تصلح للواجهة.",
                        30,
                        [
                            "تكتب Validators مفصولة عن الـDomain",
                            "ترجع 400 بإجابة موحّدة ومفهومة",
                            "تتحقق من المدخلات في الـMinimal API في .NET 10",
                        ],
                        [("FluentValidation docs", "https://docs.fluentvalidation.net/"), ("Custom validation in Minimal APIs", ASPNET + "/fundamentals/minimal-apis")],
                    ),
                    L(
                        "معالجة الأخطاء وProblemDetails",
                        "Error Handling and ProblemDetails (RFC 9457)",
                        "Exception middleware، ExceptionHandler، تحويل الاستثناءات لاستجابات موحّدة، وإزاي ما تسرّبش stack trace للعميل.",
                        30,
                        [
                            "تبني Error pipeline واحد لكل الـAPI",
                            "تفرق بين أخطاء العميل (4xx) وأخطاء السيرفر (5xx)",
                            "تستخدم ProblemDetails وValidationProblemDetails",
                        ],
                        [("Handle errors in ASP.NET Core web APIs", ASPNET + "/web-api/handle-errors")],
                    ),
                    L(
                        "اللوجنج المهيكل مع Serilog",
                        "Structured Logging with Serilog",
                        "ليه Log templates أهم من string interpolation، Sinks، Enrichers، وCorrelationId عبر الطلبات.",
                        25,
                        [
                            "تكتب Logs قابلة للبحث مش نص مطبوع",
                            "تربط كل سجلات الطلب الواحد بـCorrelationId",
                            "تتحكم في مستويات اللوجنج لكل بيئة",
                        ],
                        [("Logging in .NET", DOTNET + "/core/extensions/logging"), ("Serilog", "https://serilog.net/")],
                    ),
                    L(
                        "C# الحديث اللي لازم يبقى عادة",
                        "Modern C# Habits (records, pattern matching, nullability)",
                        "records، nullable reference types، pattern matching، collection expressions، وfield keyword في C# 14.",
                        30,
                        [
                            "تستخدم records للـDTOs والقيم",
                            "تتخلص من NullReferenceException بالـnullable annotations",
                            "تكتب pattern matching بدل سلاسل if",
                        ],
                        [("What's new in C# 14", DOTNET + "/csharp/whats-new/csharp-14"), ("Records", DOTNET + "/csharp/fundamentals/types/records")],
                    ),
                ],
            ),
            M(
                "الاختبار الحقيقي",
                "Real Testing",
                "من xUnit v3 وMicrosoft.Testing.Platform لحد Testcontainers: اختبارات بتديك ثقة فعلية وقت النشر.",
                [
                    L(
                        "خريطة الاختبارات: Unit وIntegration وContract",
                        "The Test Map: Unit, Integration, Contract",
                        "إيه اللي يُختبر على كل مستوى، وإزاي توزّع مجهودك على الهرم من غير ما تغرق.",
                        20,
                        [
                            "تصنّف كل اختبار عندك على المستوى الصح",
                            "تحدد نسبة معقولة لكل نوع في مشروعك",
                            "تفهم تكلفة كل مستوى وسرعته",
                        ],
                        [("Testing in .NET", DOTNET + "/core/testing/")],
                    ),
                    L(
                        "xUnit v3 وMicrosoft.Testing.Platform",
                        "xUnit v3 and Microsoft.Testing.Platform",
                        "الفروق عن VSTest، الـfixtures، الـtraits، وتشغيل الاختبارات من CLI وCI.",
                        30,
                        [
                            "تنشئ مشروع اختبارات بـxUnit v3",
                            "تستخدم IClassFixture/ICollectionFixture لمشاركة الإعداد",
                            "تشغّل الاختبارات بـdotnet test مع Microsoft.Testing.Platform",
                        ],
                        [("xUnit.net", "https://xunit.net/"), ("Microsoft.Testing.Platform", DOTNET + "/core/testing/unit-testing-platform")],
                    ),
                    L(
                        "الـMocking بدون مبالغة (NSubstitute)",
                        "Mocking Without Overdoing It (NSubstitute)",
                        "إمتى تعمل Substitute وإمتى تستخدم كائن حقيقي بسيط، وإزاي الاختبار المفرط في الـMocking بيكذب عليك.",
                        30,
                        [
                            "تعزل التبعيات الخارجية فقط",
                            "تكتب Assertions على السلوك مش على التفاصيل الداخلية",
                            "تكتشف الاختبار الهش (brittle) وتصلحه",
                        ],
                        [("NSubstitute", "https://nsubstitute.github.io/"), ("Shouldly", "https://docs.shouldly.io/")],
                    ),
                    L(
                        "اختبار الـAPI بـWebApplicationFactory",
                        "Integration Testing with WebApplicationFactory",
                        "تشغيل الـpipeline الحقيقي (routing، auth، validation، serialization) داخل الاختبار.",
                        35,
                        [
                            "تبني Test harness للـAPI بتاعك",
                            "تبدّل التبعيات الحقيقية ببديل مناسب للاختبار",
                            "تختبر سيناريوهات فشل مش سيناريوهات النجاح بس",
                        ],
                        [("Integration tests in ASP.NET Core", ASPNET + "/test/integration-tests")],
                    ),
                    L(
                        "Testcontainers: قاعدة بيانات حقيقية في الاختبار",
                        "Testcontainers: a Real Database in Your Tests",
                        "ليه InMemory provider بيكذب، وإزاي تشغّل SQL Server/PostgreSQL/Redis في Container داخل الاختبارات.",
                        35,
                        [
                            "تشغّل Postgres/SQL Server في اختبارتك بـTestcontainers",
                            "تدير Migrations وSeed Data في الاختبار",
                            "تحافظ على سرعة الاختبارات مع عزل كل اختبار",
                        ],
                        [("Testcontainers", "https://testcontainers.com/"), ("EF Core testing", EFCORE + "/testing/")],
                    ),
                    L(
                        "بيانات الاختبار والتغطية",
                        "Test Data, Fixtures and Coverage",
                        "Bogus/AutoFixture للبيانات الوهمية، الـgolden files، وتغطية مقاسة بدون عبادة النسبة.",
                        25,
                        [
                            "تولّد بيانات اختبار واقعية",
                            "تقيس التغطية وتفهم أرقامها بصدق",
                            "تحدد الأهداف المهمة للتغطية مش الرقم",
                        ],
                        [("Bogus", "https://github.com/bchavez/Bogus"), ("AutoFixture", "https://github.com/AutoFixture/AutoFixture")],
                    ),
                ],
            ),
            M(
                "مشروع المرحلة 1",
                "Stage 1 Capstone",
                "تطبيق عملي يجمع هندسة الكود والاختبار في مشروع واحد يُقيَّم.",
                [
                    L(
                        "Capstone: من CRUD فوضوي إلى API مُختبَر",
                        "Capstone: From Messy CRUD to a Tested API",
                        "خد Web API بسيط (أو بتاع شغلك) وحوّله لمشروع إنتاجي: طبقات، validation، ProblemDetails، Serilog، و75%+ تغطية على الـLogic.",
                        240,
                        [
                            "تعيد هيكلة مشروع موجود بدون كسر سلوكه",
                            "تضيف طبقة اختبارات Unit + Integration تشتغل في CI",
                            "توثّق قراراتك في ADRs قصيرة",
                        ],
                        [("Testing in .NET", DOTNET + "/core/testing/"), ("ASP.NET Core web API", ASPNET + "/web-api/")],
                        kind="capstone",
                    ),
                ],
            ),
        ],
    ),
    # ------------------------------------------------------------------ Stage 2
    S(
        "ASP.NET Core المتقدم وAPIs إنتاجية",
        "Advanced ASP.NET Core & Production APIs",
        "كل ما يحوّل الـAPI من «يشتغل على جهازي» إلى خدمة موثّقة، مؤمَّنة، محدودة المعدل، وصحية التشغيل.",
        "تنشر API بـOpenAPI/Scalar، JWT + Policies، Rate Limiting، Caching، Health Checks، وBackground services.",
        "متوسط → متقدم",
        "4 أسابيع",
        [
            M(
                "تصميم الـAPI الحديث",
                "Modern API Design",
                "Minimal APIs في .NET 10، التوثيق، الإصدارات، الترقيم (pagination)، والاستجابات الموحّدة.",
                [
                    L(
                        "Minimal APIs مقابل Controllers: اختيار مبرر",
                        "Minimal APIs vs Controllers: a Justified Choice",
                        "إمتى تختار كل واحد، وإزاي Minimal APIs في .NET 10 بقت تدعم Validation وJSON Patch.",
                        30,
                        [
                            "تبني Endpoints بـMinimal APIs مع Endpoint Filters",
                            "تنظم الكود بـExtension methods لكل Feature",
                            "تقرر بين Minimal APIs وControllers بمعايير واضحة",
                        ],
                        [("Minimal APIs overview", ASPNET + "/fundamentals/minimal-apis"), ("What's new in ASP.NET Core 10", ASPNET + "/what-is-new/")],
                    ),
                    L(
                        "OpenAPI 3.1 وScalar: توثيق يعيش مع الكود",
                        "OpenAPI 3.1 and Scalar: Docs That Live With the Code",
                        "توليد المواصفة، تحسين الوصف بالـAttributes، وواجهة Scalar بدل Swagger UI.",
                        30,
                        [
                            "تولّد OpenAPI document من مشروعك",
                            "تكتب أوصاف وأمثلة للاستجابات",
                            "تعرض الواجهة التفاعلية للمستهلكين",
                        ],
                        [("OpenAPI in ASP.NET Core", ASPNET + "/web-api/openapi/"), ("Scalar", "https://github.com/scalar/scalar")],
                    ),
                    L(
                        "الإصدارات والترقيم والفرز والفلترة",
                        "Versioning, Pagination, Sorting and Filtering",
                        "إزاي تغيّر الـAPI من غير ما تكسر العملاء، وتصميم قوائم مقسّمة بأداء ثابت.",
                        35,
                        [
                            "تنفّذ API versioning بدون كسر",
                            "تبني Cursor pagination أسرع من Offset",
                            "تصمم Filter/Sort contract موحّد",
                        ],
                        [("Versioning guidance", ASPNET + "/web-api/"), ("Pagination patterns", DOTNET + "/architecture/")],
                    ),
                    L(
                        "الـMiddleware وEndpoint Filters",
                        "Middleware and Endpoint Filters",
                        "الفرق بينهم، ترتيب الـpipeline، وبناء Cross-cutting concerns (توقيت، tenant، audit).",
                        30,
                        [
                            "تكتب Middleware مخصص بأداء مقبول",
                            "تستخدم Endpoint Filters للـcross-cutting",
                            "تفهم ترتيب الـpipeline وأثره على الأخطاء",
                        ],
                        [("ASP.NET Core middleware", ASPNET + "/fundamentals/middleware/")],
                    ),
                    L(
                        "الـRate Limiting والحماية من الإساءة",
                        "Rate Limiting and Abuse Protection",
                        "Fixed/Sliding window وToken bucket وConcurrency limiters، وإزاي تحمي خدمة من عميل شره.",
                        25,
                        [
                            "تطبق Rate limiting على Endpoints حساسة",
                            "ترجع 429 مع Retry-After صحيح",
                            "تفرق بين الحد على المستخدم والحد على الـIP",
                        ],
                        [("Rate limiting middleware", ASPNET + "/performance/rate-limit")],
                    ),
                    L(
                        "الـCaching في ASP.NET Core",
                        "Caching: Memory, Output and Distributed",
                        "IMemoryCache، Output Caching، IDistributedCache، وTag-based invalidation.",
                        30,
                        [
                            "تختار طبقة الكاش المناسبة لكل حالة",
                            "تضبط إبطال الكاش بشكل صحيح",
                            "تقيس الأثر الفعلي للكاش على زمن الاستجابة",
                        ],
                        [("Caching in ASP.NET Core", ASPNET + "/performance/caching/")],
                    ),
                ],
            ),
            M(
                "المصادقة والتفويض",
                "Authentication & Authorization",
                "من JWT وRefresh tokens إلى Identity وOIDC وPolicies — وأمان الـAPI في 2026.",
                [
                    L(
                        "المصادقة مقابل التفويض: المفاهيم قبل الكود",
                        "AuthN vs AuthZ: Concepts Before Code",
                        "Claims، Principals، Schemes، Policies، Roles — والمفردات اللي بتلخبط في المقابلات.",
                        25,
                        [
                            "تشرح الفرق بين المصادقة والتفويض بمثال من كودك",
                            "تقرأ ClaimsPrincipal وتستخدمها صح",
                            "تصمم Policy بدل Role-checks المتناثرة",
                        ],
                        [("Overview of ASP.NET Core authentication", ASPNET + "/security/authentication/")],
                    ),
                    L(
                        "JWT Access + Refresh tokens بشكل سليم",
                        "JWT Access + Refresh Tokens Done Right",
                        "إصدار التوكنات، انتهاء الصلاحية، التدوير (rotation)، الإبطال، وأخطاء شائعة بتسبب اختراقات.",
                        40,
                        [
                            "تنفّذ إصدار وتحقق JWT",
                            "تبني Refresh token rotation مع كشف إعادة الاستخدام",
                            "تخزن المفاتيح بشكل آمن وتدوّرها",
                        ],
                        [("JWT Bearer authentication", ASPNET + "/security/authentication/jwt"), ("OWASP Top 10", "https://owasp.org/www-project-top-ten/")],
                    ),
                    L(
                        "ASP.NET Core Identity في المشاريع الحقيقية",
                        "ASP.NET Core Identity in Real Projects",
                        "تخزين المستخدمين، الأدوار، 2FA، إعادة تعيين كلمة السر، وتخصيص Identity بدون كسر الترقية.",
                        35,
                        [
                            "تدمج Identity مع EF Core وAPI",
                            "تفعّل 2FA وlockout policies",
                            "تفصل بين Identity والـDomain layer",
                        ],
                        [("ASP.NET Core Identity", ASPNET + "/security/authentication/identity")],
                    ),
                    L(
                        "OpenID Connect وExternal providers",
                        "OpenID Connect and External Providers",
                        "تسجيل الدخول بـGoogle/Microsoft/Entra ID، الـflows الصحيحة، وPKCE لتطبيقات العميل.",
                        35,
                        [
                            "تضيف Login خارجي لمشروعك",
                            "تختار الـflow الصحيح حسب نوع العميل",
                            "تتعامل مع refresh وإلغاء الربط",
                        ],
                        [("OAuth/OIDC in ASP.NET Core", ASPNET + "/security/authentication/")],
                    ),
                    L(
                        "تأمين الـAPI: رؤوس، CORS، أسرار، OWASP",
                        "API Hardening: Headers, CORS, Secrets, OWASP",
                        "قائمة فحص أمنية عملية قبل النشر، وأهم ثغرات الـAPI في 2026.",
                        30,
                        [
                            "تضبط Security headers وCORS بشكل مقصود",
                            "تدير الأسرار عبر Key Vault/User Secrets",
                            "تنفّذ قائمة فحص OWASP API Top 10",
                        ],
                        [("OWASP API Security", "https://owasp.org/www-project-api-security/"), ("Azure Key Vault", AZURE + "/key-vault/")],
                    ),
                ],
            ),
            M(
                "الوقت الحقيقي والمهام الخلفية",
                "Realtime & Background Work",
                "SignalR، Worker services، الجدولة، وHealth checks — أي اللي بيشتغل لما مفيش مستخدم بيطلب.",
                [
                    L(
                        "SignalR: تحديثات فورية للواجهة",
                        "SignalR: Realtime Updates",
                        "Hubs، transports، المجموعات، وإعادة الاتصال، ومتى تستخدم Server-Sent Events بدلها.",
                        35,
                        [
                            "تبني Hub يبعت تحديثات لمجموعة مستخدمين",
                            "تتعامل مع إعادة الاتصال والأخطاء",
                            "تختار بين SignalR وSSE (الجديد في .NET 10)",
                        ],
                        [("SignalR overview", ASPNET + "/signalr/introduction"), ("Server-Sent Events in .NET 10", ASPNET + "/what-is-new/")],
                    ),
                    L(
                        "BackgroundService وIHostedService",
                        "BackgroundService and IHostedService",
                        "مهام دورية، Scope داخل مهمة خلفية، أخطاء صامتة، والإلغاء النظيف.",
                        30,
                        [
                            "تكتب Background service لا تسرّب Scope",
                            "تتعامل مع StoppingToken والأخطاء",
                            "تقرر بين Hosted service وQueue worker",
                        ],
                        [("Background tasks with hosted services", ASPNET + "/fundamentals/host/hosted-services")],
                    ),
                    L(
                        "الجدولة: Hangfire مقابل Quartz مقابل MediatR jobs",
                        "Scheduling: Hangfire vs Quartz vs Native",
                        "مقارنة عملية لجدولة المهام، والمراقبة، وإعادة المحاولة.",
                        25,
                        [
                            "تختار أداة جدولة بحسب الاحتياج",
                            "تنفّذ Cron jobs قابلة للمراقبة",
                            "تتعامل مع المهام المكررة والـidempotency",
                        ],
                        [("Quartz.NET", "https://www.quartz-scheduler.net/"), ("Hangfire", "https://www.hangfire.io/")],
                    ),
                    L(
                        "Health Checks وReadiness",
                        "Health Checks and Readiness",
                        "فحوصات قاعدة البيانات والتبعيات، ونشرها لـload balancer وKubernetes probes.",
                        25,
                        [
                            "تضيف Health checks لتبعياتك",
                            "تفرق بين Liveness وReadiness",
                            "تعرض حالة الخدمة بشكل آمن داخليًا",
                        ],
                        [("Health checks in ASP.NET Core", ASPNET + "/health-checks/")],
                    ),
                ],
            ),
            M(
                "مشروع المرحلة 2",
                "Stage 2 Capstone",
                "API جاهز للإنتاج بكل ما سبق.",
                [
                    L(
                        "Capstone: API إنتاجي موثّق ومؤمَّن",
                        "Capstone: A Documented, Secured Production API",
                        "خدمة كاملة: JWT + Refresh، Policies، Rate limiting، Output caching، SignalR notifications، Background worker، Health checks، Scalar docs، واختبارات Integration.",
                        300,
                        [
                            "تنفّذ كل عناصر القائمة في مشروع واحد متماسك",
                            "توثّق القرارات الأمنية والمعمارية",
                            "تقيس الأداء قبل وبعد الكاش",
                        ],
                        [("ASP.NET Core web API", ASPNET + "/web-api/"), ("Security overview", ASPNET + "/security/")],
                        kind="capstone",
                    ),
                ],
            ),
        ],
    ),
    # ------------------------------------------------------------------ Stage 3
    S(
        "البيانات والأداء",
        "Data & Performance",
        "بعد ما الـAPI بيشتغل: يبقى سريع. SQL حقيقي، EF Core متقدّم، Redis، NoSQL، وقياس بدل التخمين.",
        "تخفض زمن استجابة خدمة بعشرة أضعاف بأدلة قياس، وتفهم الـSQL اللي يولّده EF Core وتصلحه.",
        "متقدم",
        "4 أسابيع",
        [
            M(
                "SQL اللي لازم تعرفه من غير ORM",
                "SQL You Must Know Without an ORM",
                "الفهارس، خطط التنفيذ، العزل، والأقفال — عشان تعرف ليه الاستعلام بطيء.",
                [
                    L(
                        "الفهارس وخطط التنفيذ",
                        "Indexes and Execution Plans",
                        "أنواع الفهارس في SQL Server/PostgreSQL، قراءة خطة التنفيذ، واكتشاف الـscan القاتل.",
                        40,
                        [
                            "تقرأ Execution plan وتستنتج سبب البطء",
                            "تختار الفهرس الصح (Clustered/Nonclustered/Composite)",
                            "تكتشف الفهارس غير المستخدمة والزائدة",
                        ],
                        [("PostgreSQL: Using indexes", "https://www.postgresql.org/docs/current/indexes.html"), ("SQL Server query performance", ML + "/sql/relational-databases/performance/")],
                    ),
                    L(
                        "المعاملات ومستويات العزل والـLocking",
                        "Transactions, Isolation Levels and Locking",
                        "Read Committed مقابل Repeatable Read مقابل Serializable، والـDeadlocks وإزاي تمنعها.",
                        35,
                        [
                            "تختار مستوى العزل المناسب لكل عملية",
                            "تشخّص Deadlock من الـtrace",
                            "تصمم معاملات قصيرة تقلل التعارض",
                        ],
                        [("EF Core transactions", EFCORE + "/saving/transactions/"), ("PostgreSQL transaction isolation", "https://www.postgresql.org/docs/current/transaction-iso.html")],
                    ),
                    L(
                        "Dapper: لما تحتاج سرعة SQL الخام",
                        "Dapper: When You Need Raw SQL Speed",
                        "Micro-ORM، الـmapping، الـparameterization، وإزاي تستخدمه جنب EF Core في نفس المشروع.",
                        30,
                        [
                            "تكتب استعلامات Dapper بأمان ضد SQL injection",
                            "تحدد الحالات اللي يستحق فيها Dapper",
                            "تشارك Connection/Transaction بين EF وDapper",
                        ],
                        [("Dapper", "https://github.com/DapperLib/Dapper")],
                    ),
                ],
            ),
            M(
                "EF Core متقدم",
                "Advanced EF Core",
                "الأداء والتعبير في EF Core 10: projections، ExecuteUpdate، Named query filters، Complex types.",
                [
                    L(
                        "أداء الاستعلامات: N+1 وProjections وAsNoTracking",
                        "Query Performance: N+1, Projections, AsNoTracking",
                        "أشهر أسباب البطء في تطبيقات EF Core وإزاي تكتشفها من الـlogs.",
                        35,
                        [
                            "تقضي على N+1 بـInclude أو projection",
                            "تستخدم AsNoTracking في مسارات القراءة",
                            "تقيس أثر كل تغيير بالأرقام",
                        ],
                        [("EF Core performance", EFCORE + "/performance/performance-tuning")],
                    ),
                    L(
                        "EF Core 10: Complex types وNamed query filters وLeftJoin",
                        "EF Core 10: Complex Types, Named Query Filters, LeftJoin",
                        "الجديد في EF Core 10 وإزاي يقلل الكود ويحسّن الترجمة للـSQL.",
                        35,
                        [
                            "تنمذج بياناتك بـComplex types بدل الجداول الزائدة",
                            "تستخدم Named query filters للـsoft-delete وmulti-tenancy",
                            "تكتب LeftJoin/RightJoin الجديدة",
                        ],
                        [("What's new in EF Core 10", EFCORE + "/what-is-new/ef-core-10.0/whats-new")],
                    ),
                    L(
                        "الكتابات السريعة: ExecuteUpdate وBulk operations",
                        "Fast Writes: ExecuteUpdate, ExecuteDelete and Bulk Ops",
                        "تحديث/حذف مباشر في قاعدة البيانات بدون تحميل الكيانات، وحدود كل أسلوب.",
                        30,
                        [
                            "تنفّذ تحديثات جماعية آمنة",
                            "تتعامل مع Concurrency tokens",
                            "تختار بين EF bulk ومكتبات خارجية",
                        ],
                        [("ExecuteUpdate/ExecuteDelete", EFCORE + "/saving/execute-insert-update-delete")],
                    ),
                    L(
                        "Migrations في فرق حقيقية وCI/CD",
                        "Migrations in Real Teams and CI/CD",
                        "استراتيجيات الترحيل الآمن، الترحيلات التوسعية مقابل التدميرية، والتطبيق في النشر.",
                        30,
                        [
                            "تكتب Migration لا يوقف النظام (expand/contract)",
                            "تدير تعارضات الـMigrations بين المطورين",
                            "تنشر الـMigrations بأمان من الـpipeline",
                        ],
                        [("EF Core migrations", EFCORE + "/managing-schemas/migrations/")],
                    ),
                ],
            ),
            M(
                "الكاش والتخزين البديل والقياس",
                "Caching, Alternate Stores and Measurement",
                "Redis، MongoDB/Cosmos DB، البحث، ثم BenchmarkDotNet وk6 لإثبات التحسن.",
                [
                    L(
                        "Redis: كاش موزع، جلسات، طوابير خفيفة",
                        "Redis: Distributed Cache, Sessions, Light Queues",
                        "أنماط الكاش (cache-aside، write-through)، الإبطال، وأخطاء الكاش الشائعة.",
                        35,
                        [
                            "تنفّذ Cache-aside مع TTL وإبطال صحيح",
                            "تستخدم Redis للـdistributed locking بعناية",
                            "تقيس hit ratio وتفهم أثره",
                        ],
                        [("Redis docs", "https://redis.io/docs/latest/"), ("Distributed caching in ASP.NET Core", ASPNET + "/performance/caching/distributed")],
                    ),
                    L(
                        "NoSQL: MongoDB وCosmos DB وإمتى تستخدمهم",
                        "NoSQL: MongoDB and Cosmos DB, and When",
                        "نمذجة البيانات المستندية، الـpartitions، ومتى يكون NoSQL قرارًا خاطئًا.",
                        30,
                        [
                            "تنمذج بيانات مستندية بدون تكرار مضر",
                            "تفهم Partition keys وأثرها على الأداء",
                            "تبرر اختيار SQL أو NoSQL في تصميمك",
                        ],
                        [("Azure Cosmos DB", AZURE + "/cosmos-db/"), ("MongoDB EF Core provider", EFCORE + "/providers/")],
                    ),
                    L(
                        "القياس: BenchmarkDotNet وk6 وProfiling",
                        "Measurement: BenchmarkDotNet, k6 and Profiling",
                        "من غير قياس إنت بتخمن: micro-benchmarks، اختبارات حمل، ومحللات الأداء.",
                        35,
                        [
                            "تقيس كودًا حساسًا للأداء بطريقة صحيحة",
                            "تشغّل اختبار حمل على API وتحلل p95/p99",
                            "تستخدم dotnet-trace/dotnet-counts للتشخيص",
                        ],
                        [("BenchmarkDotNet", "https://benchmarkdotnet.org/"), ("Diagnostic tools", DOTNET + "/core/diagnostics/"), ("k6", "https://grafana.com/docs/k6/")],
                    ),
                    L(
                        "async/await في العمق وSpan<T> وNativeAOT",
                        "async/await in Depth, Span<T> and NativeAOT",
                        "إزاي يشتغل async فعلًا، أخطاء الاستنزاف (starvation)، وتقليل التخصيصات بـSpan، ومتى NativeAOT مناسب.",
                        40,
                        [
                            "تشرح state machine للـasync وإزاي الـthread pool بيتعامل معها",
                            "تتجنب .Result/.Wait() وdeadlocks",
                            "تقلل التخصيصات بـSpan/Memory في مسارات ساخنة",
                        ],
                        [("Async guidance", DOTNET + "/standard/asynchronous-programming-patterns/"), ("Span<T>", DOTNET + "/api/system.span-1"), ("NativeAOT", DOTNET + "/core/deploying/native-aot/")],
                    ),
                ],
            ),
            M(
                "مشروع المرحلة 3",
                "Stage 3 Capstone",
                "تحسين خدمة حقيقية بأهداف أداء مرقّمة.",
                [
                    L(
                        "Capstone: من 800ms إلى 80ms بدليل",
                        "Capstone: From 800ms to 80ms, With Evidence",
                        "خد خدمة بطيئة (أو ولّدها) وحسّنها بفهارس، projections، Redis، وضبط async — وقدّم تقرير قياس قبل/بعد مع k6.",
                        240,
                        [
                            "تضع أهداف أداء رقمية (p95، throughput) قبل البدء",
                            "تنفّذ تحسينات متعددة الطبقات وتقيس كل واحدة",
                            "تكتب تقرير أداء يشرح الأثر والسبب",
                        ],
                        [("EF Core performance", EFCORE + "/performance/"), ("k6", "https://grafana.com/docs/k6/")],
                        kind="capstone",
                    ),
                ],
            ),
        ],
    ),
    # ------------------------------------------------------------------ Stage 4
    S(
        "المعمارية والأنماط",
        "Architecture & Patterns",
                        "الفرق بين Mid وSenior: تفكير في أنظمة مش في ميزات. Clean Architecture، Modular Monolith، DDD، CQRS.",
        "تصمم نظامًا مقسّم الوحدات، تفصل الـDomain عن EF Core، وتبرر كل قرار معماري بـADR.",
        "متقدم",
        "3 أسابيع",
        [
            M(
                "هياكل المشاريع",
                "Project Structures",
                "Layered، Clean/Onion، Hexagonal، وVertical Slice — وإزاي تختار بدون تقليد أعمى.",
                [
                    L(
                        "Clean/Onion Architecture في مشروع حقيقي",
                        "Clean/Onion Architecture in a Real Project",
                        "اتجاه الاعتماديات، طبقة Domain لا تعرف EF Core، وApplication كـports.",
                        35,
                        [
                            "تبني حلًا من 4 مشاريع باتجاه اعتماديات صحيح",
                            "تعزل الـDomain عن البنية التحتية",
                            "تتجنب تسريب الـDTOs للـDomain",
                        ],
                        [(".NET architecture guides", DOTNET + "/architecture/"), ("Clean architecture sample", "https://github.com/ardalis/CleanArchitecture")],
                    ),
                    L(
                        "Vertical Slice: بديل عملي للطبقات",
                        "Vertical Slice Architecture: a Pragmatic Alternative",
                        "تنظيم الكود حول الـfeatures مش حول الطبقات، وإمتى يناسب الفرق الصغيرة.",
                        30,
                        [
                            "تنظّج مشروعًا حول features/slices",
                            "تقارن تكلفة التغيير بين الأسلوبين",
                            "تحدد متى تختار كل أسلوب",
                        ],
                        [("Vertical slice architecture", DOTNET + "/architecture/")],
                    ),
                    L(
                        "Modular Monolith: الخيار الصحيح في أغلب الأحيان",
                        "Modular Monolith: the Right Default",
                        "حدود الوحدات، الاتصال بينها، وقواعد منع التحوّل لـBig Ball of Mud.",
                        35,
                        [
                            "تقسّم تطبيقًا لوحدات بحدود صريحة",
                            "تفرض قيود الاعتماديات (اختبارات معمارية)",
                            "تبرر قرار Monolith مقابل Microservices",
                        ],
                        [("Modular monolith guidance", DOTNET + "/architecture/cloud-native/"), ("NetArchTest", "https://github.com/BenMorris/NetArchTest")],
                    ),
                    L(
                        "قرارات موثقة: ADRs وTrade-offs",
                        "Documented Decisions: ADRs and Trade-offs",
                        "إزاي تكتب قرارًا معماريًا يفهمه من بعدك، وتدافع عنه في Review.",
                        20,
                        [
                            "تكتب ADR مختصرًا ومفيدًا",
                            "تسجل البدائل المرفوضة وأسبابها",
                            "تحدّث القرارات مع تغير الظروف",
                        ],
                        [("Architecture decision records", "https://adr.github.io/")],
                    ),
                ],
            ),
            M(
                "DDD وCQRS",
                "DDD Tactics and CQRS",
                "Aggregates، Domain events، Value objects، ثم CQRS مع MediatR ونمط الـOutbox.",
                [
                    L(
                        "DDD التكتيكي: Aggregates وValue Objects وDomain Events",
                        "Tactical DDD: Aggregates, Value Objects, Domain Events",
                        "نمذجة قواعد العمل داخل الكيانات بدل تركها في الـControllers.",
                        40,
                        [
                            "تحدد Aggregate boundaries صحيحة",
                            "تنقل قواعد العمل لداخل الـDomain",
                            "تصدر Domain events بدون ربطها بـEF Core",
                        ],
                        [("Domain-Driven Design", DOTNET + "/architecture/microservices/architect-microservice-container-applications/"), ("DDD reference", "https://learn.microsoft.com/dotnet/architecture/")],
                    ),
                    L(
                        "CQRS مع MediatR: الفصل بين القراءة والكتابة",
                        "CQRS with MediatR: Separating Reads and Writes",
                        "Commands/Queries، الـpipeline behaviors (validation، logging، transactions)، ومتى CQRS مبالغة.",
                        35,
                        [
                            "تنفّذ CQRS بسيط بدون Event Sourcing",
                            "تبني Pipeline behaviors للـcross-cutting",
                            "تحدد متى لا تحتاج CQRS",
                        ],
                        [("MediatR", "https://github.com/jbogard/MediatR"), ("CQRS pattern", AZURE + "/architecture/patterns/cqrs")],
                    ),
                    L(
                        "Outbox وInbox: موثوقية بلا فقدان رسائل",
                        "Outbox and Inbox: Reliable Messaging Without Lost Events",
                        "حفظ الأحداث في نفس معاملة قاعدة البيانات ونشرها لاحقًا، واستقبال idempotent.",
                        30,
                        [
                            "تنفّذ Outbox pattern مع EF Core",
                            "تضمن Idempotent consumption",
                            "تشرح مشاكل Dual write وتحلها",
                        ],
                        [("Outbox pattern (MassTransit)", "https://masstransit.io/documentation/outbox"), ("Azure architecture patterns", AZURE + "/architecture/patterns/")],
                    ),
                    L(
                        "Event Sourcing: افهمه قبل ما ترفضه أو تعشقه",
                        "Event Sourcing: Understand It Before You Love or Reject It",
                        "فكرة الحالة كمجموعة أحداث، الـprojections، والتكاليف التشغيلية.",
                        25,
                        [
                            "تشرح Event Sourcing وميزاته وتكاليفه",
                            "تبني Projection بسيط",
                            "تقرر متى لا تستخدمه (وهذا الغالب)",
                        ],
                        [("Event Sourcing pattern", AZURE + "/architecture/patterns/event-sourcing")],
                    ),
                ],
            ),
            M(
                "مشروع المرحلة 4",
                "Stage 4 Capstone",
                "تصميم وتنفيذ نظام معماري متكامل.",
                [
                    L(
                        "Capstone: Modular Monolith بـCQRS وOutbox",
                        "Capstone: Modular Monolith with CQRS and Outbox",
                        "نظام حجز/طلبات مقسّم لوحدات، Domain غني، CQRS، Outbox، اختبارات معمارية تمنع تسريب الاعتماديات، وADRs لكل قرار.",
                        300,
                        [
                            "تبني نظامًا بحدود وحدات مفروضة باختبارات",
                            "تنفّذ Domain events وOutbox",
                            "توثّق 5 قرارات معمارية بـADRs",
                        ],
                        [(".NET architecture guides", DOTNET + "/architecture/"), ("Azure architecture center", AZURE + "/architecture/")],
                        kind="capstone",
                    ),
                ],
            ),
        ],
    ),
    # ------------------------------------------------------------------ Stage 5
    S(
        "الميكروسيرفيسز والمراسلة",
        "Microservices & Messaging",
                        "لما النظام يكبر فعلًا: تقسيم، RabbitMQ/Kafka، MassTransit، gRPC، YARP، و.NET Aspire للتنسيق.",
        "تشغّل نظامًا من 3 خدمات تتواصل بالأحداث، مع Gateway وResilience ولوحة Aspire.",
        "متقدم",
        "4 أسابيع",
        [
            M(
                "التقسيم والاتصال",
                "Decomposition & Communication",
                "حدود الخدمات، gRPC، REST بين الخدمات، وAPI Gateway.",
                [
                    L(
                        "إمتى ميكروسيرفيسز وإمتى لأ",
                        "When Microservices — and When Not",
                        "مؤشرات الحاجة الحقيقية للتقسيم، وتكلفة التشغيل اللي بتظهر متأخر.",
                        30,
                        [
                            "تقيّم نظامًا وتقرر إن كان يحتاج تقسيم",
                            "تحسب التكلفة التشغيلية مقابل الفائدة",
                            "تخطط لانتقال تدريجي من Monolith",
                        ],
                        [("Microservices architecture", DOTNET + "/architecture/cloud-native/microservices/"), ("Azure: Microservices design patterns", AZURE + "/architecture/microservices/")],
                    ),
                    L(
                        "حدود الخدمات وتقسيم البيانات",
                        "Service Boundaries and Data Decomposition",
                        "Database-per-service، الـshared data problem، وطرق التكامل بدون اقتران.",
                        35,
                        [
                            "تقسّم البيانات بين الخدمات بدون تكرار ضار",
                            "تتعامل مع الاتساق النهائي",
                            "تصمم Integration events بين الخدمات",
                        ],
                        [("Data management in microservices", AZURE + "/architecture/microservices/")],
                    ),
                    L(
                        "gRPC للاتصال الداخلي",
                        "gRPC for Internal Communication",
                        "عقود Proto، الأداء مقابل REST، streaming، ومتى لا تستخدمه.",
                        30,
                        [
                            "تبني خدمة gRPC بين خدمتين",
                            "تستخدم streaming للحالات المناسبة",
                            "تقارن gRPC بـREST من ناحية الأداء والتعقيد",
                        ],
                        [("gRPC services in ASP.NET Core", ASPNET + "/grpc/")],
                    ),
                    L(
                        "API Gateway بـYARP",
                        "API Gateway with YARP",
                        "توجيه، تجميع، مصادقة موحّدة، وBFF للواجهات المختلفة.",
                        30,
                        [
                            "تبني Gateway بـYARP يوجّه لخدماتك",
                            "تنفّذ Backend-for-Frontend",
                            "تدير إعدادات التوجيه ديناميكيًا",
                        ],
                        [("YARP", "https://github.com/dotnet/yarp"), ("Gateway Aggregation pattern", AZURE + "/architecture/patterns/gateway-aggregation")],
                    ),
                ],
            ),
            M(
                "المراسلة والاعتمادية",
                "Messaging & Resilience",
                "RabbitMQ/Kafka/Service Bus مع MassTransit، أنماط Saga، وPolly للصمود.",
                [
                    L(
                        "RabbitMQ وMassTransit: أول حدث حقيقي",
                        "RabbitMQ and MassTransit: Your First Real Event",
                        "Exchanges، Queues، Routing keys، Consumers، وأخطاء التسليم.",
                        40,
                        [
                            "تشغّل RabbitMQ في Docker وتنشر حدثًا",
                            "تبني Consumer بـMassTransit",
                            "تتعامل مع إعادة المحاولة والفشل النهائي (DLQ)",
                        ],
                        [("RabbitMQ tutorials", "https://www.rabbitmq.com/tutorials"), ("MassTransit", "https://masstransit.io/documentation")],
                    ),
                    L(
                        "Kafka وAzure Service Bus: الفرق والاستخدام",
                        "Kafka and Azure Service Bus: Differences and Use",
                        "Event streaming مقابل Message broker، الـordering، والـpartitions.",
                        30,
                        [
                            "تفرق بين نمطي المراسلة وتختار المناسب",
                            "تفهم الـpartitioning والـordering guarantees",
                            "تربط MassTransit بـService Bus",
                        ],
                        [("Apache Kafka", "https://kafka.apache.org/documentation/"), ("Azure Service Bus", AZURE + "/service-bus-messaging/")],
                    ),
                    L(
                        "Sagas والاتساق النهائي",
                        "Sagas and Eventual Consistency",
                        "تنسيق عملية موزعة عبر خدمات، والتعويض عند الفشل.",
                        35,
                        [
                            "تنفّذ Saga بـMassTransit لعملية متعددة الخطوات",
                            "تصمم خطوات تعويضية",
                            "تشرح الاتساق النهائي لفريق غير تقني",
                        ],
                        [("Saga pattern", AZURE + "/architecture/reference-architectures/microservices/saga")],
                    ),
                    L(
                        "Polly وStandard Resilience: retries وcircuit breakers",
                        "Polly and Standard Resilience",
                        "Retry، Circuit breaker، Timeout، Bulkhead — وإعداد Microsoft.Extensions.Resilience.",
                        30,
                        [
                            "تضيف Resilience pipeline لعميل HTTP",
                            "تضبط Circuit breaker بحدود صحيحة",
                            "تتجنب كوارث retry storms",
                        ],
                        [("Polly docs", "https://www.pollydocs.org/"), ("Resilience in .NET", DOTNET + "/core/resilience/")],
                    ),
                    L(
                        "Idempotency وإعادة المحاولة الآمنة",
                        "Idempotency and Safe Retries",
                        "مفاتيح idempotency، كشف التكرار، وضمان معالجة الرسالة مرة واحدة فعلًا.",
                        25,
                        [
                            "تنفّذ Idempotent consumer",
                            "تستخدم Inbox pattern لمنع التكرار",
                            "تصمم API يقبل Idempotency-Key",
                        ],
                        [("Idempotent receiver", "https://masstransit.io/documentation/consume-idempotent"), ("Azure patterns", AZURE + "/architecture/patterns/")],
                    ),
                ],
            ),
            M(
                "التنسيق مع .NET Aspire",
                "Orchestration with .NET Aspire",
                "AppHost، Service discovery، Integrations، ولوحة Aspire للمراقبة أثناء التطوير.",
                [
                    L(
                        ".NET Aspire: AppHost وService Discovery",
                        ".NET Aspire: AppHost and Service Discovery",
                        "تشغيل كل الخدمات محليًا بأمر واحد مع اكتشاف تلقائي.",
                        35,
                        [
                            "تبني Aspire AppHost ينسّق خدماتك",
                            "تستخدم Service discovery بدل URLs ثابتة",
                            "تضيف Integrations جاهزة (Redis، Postgres، RabbitMQ)",
                        ],
                        [(".NET Aspire", DOTNET + "/aspire/"), ("Aspire service discovery", DOTNET + "/aspire/")],
                    ),
                    L(
                        "لوحة Aspire والتشخيص المحلي",
                        "Aspire Dashboard and Local Diagnostics",
                        "تتبع الطلبات عبر الخدمات، اللوجنج، والمقاييس أثناء التطوير.",
                        30,
                        [
                            "تقرأ Distributed traces في اللوحة",
                            "تربط اللوجنج بالـtrace",
                            "تشخّص فشل في سلسلة خدمات",
                        ],
                        [("Aspire dashboard", DOTNET + "/aspire/fundamentals/dashboard/"), ("OpenTelemetry in .NET", DOTNET + "/core/diagnostics/observability-with-otel")],
                    ),
                    L(
                        "اختبار الأنظمة الموزعة وContract tests",
                        "Testing Distributed Systems and Contract Tests",
                        "اختبار التكامل بين الخدمات، Pact/contract testing، وبيئات ephemeral.",
                        30,
                        [
                            "تكتب اختبارات تكامل بين خدمتين",
                            "تطبق Contract testing لمنع الكسر",
                            "تشغّل الاختبارات في CI مع Testcontainers",
                        ],
                        [("Pact", "https://docs.pact.io/"), ("Testcontainers", "https://testcontainers.com/")],
                    ),
                    L(
                        "أنماط جاهزة: Cache-aside وCircuit breaker وBulkhead وThrottling",
                        "Cloud Design Patterns You Will Actually Use",
                        "جولة مركزة في أهم أنماط Azure Architecture Center مع تنفيذها في .NET.",
                        25,
                        [
                            "تختار النمط المناسب لكل مشكلة",
                            "تنفّذ 3 أنماط في مشروعك",
                            "توثّق النمط المستخدم في ADR",
                        ],
                        [("Azure Architecture patterns", AZURE + "/architecture/patterns/")],
                    ),
                ],
            ),
            M(
                "مشروع المرحلة 5",
                "Stage 5 Capstone",
                "نظام موزع صغير يعمل فعليًا على جهازك.",
                [
                    L(
                        "Capstone: 3 خدمات + RabbitMQ + Aspire",
                        "Capstone: 3 Services + RabbitMQ + Aspire",
                        "نظام طلبات: Orders API، Payments worker، Notifications service — تتواصل بالأحداث، مع Outbox، Polly، Gateway، ولوحة Aspire.",
                        360,
                        [
                            "تشغّل النظام كاملًا بأمر واحد",
                            "تثبت عدم فقدان الأحداث عند فشل خدمة",
                            "توثّق مخطط النظام وتدفق الأحداث",
                        ],
                        [(".NET Aspire", DOTNET + "/aspire/"), ("Microservices sample", "https://github.com/dotnet-architecture/eShop")],
                        kind="capstone",
                    ),
                ],
            ),
        ],
    ),
]
