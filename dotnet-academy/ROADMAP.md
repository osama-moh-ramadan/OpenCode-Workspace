# خريطة مسار Souq Academy

هذه هي الخريطة المرجعية التي يُبنى عليها المحتوى. الهدف ليس تجميع عناوين، بل مسار
واحد يبدأ من أول سطر C# وينتهي بـ API منشور ومشروع يمكن الدفاع عنه في مقابلة عمل.

## مبدأ المحتوى

كل درس يجب أن يجيب على أربعة أسئلة:

1. **لماذا يوجد هذا المفهوم؟** المشكلة التي يحلها قبل تعريفه.
2. **كيف يُكتب؟** كود كامل قابل للتشغيل، لا أجزاء مبتورة.
3. **ماذا يحدث في الخلفية؟** CLR، GC، Kestrel، EF Core، الشبكة، أو قاعدة البيانات.
4. **كيف يُستخدم في مشروع حقيقي؟** خطوة Souq.NET ومهمة يمكن التحقق منها.

## مواصفات كل درس

- شرح مفاهيمي تدريجي من الصفر، بمصطلحات تقنية إنجليزية والشرح عربي.
- قسم **الكود سطرًا بسطر**: 8–15 خطوة، لكل خطوة وظيفتها وما يحدث خلفها.
- مقارنة **قبل / بعد** لنمط شائع مقابل النمط الحديث.
- تحليل أداء وذاكرة وتأثير على الإنتاج.
- 4 نصائح مهنية ومصائد شائعة على الأقل.
- 3 أسئلة اختبار بتفسير فوري.
- 4–5 خطوات مشروع مترابطة.
- لا عناصر ناقصة، ولا «TODO»، ولا أسئلة بلا إجابة.

## الوحدات والدروس المستهدفة

| # | الوحدة | الدروس | الناتج |
|---|--------|--------|--------|
| 1 | الأساس: من أول سطر إلى أول طلب | 4 | فهم .NET وCLR، C# للـBackend، CLI |
| 2 | تشريح المشروع وHTTP | 4 | HTTP، المشروع، Program.cs، Kestrel |
| 3 | DI والإعدادات | 2 | أعمار DI ومصائدها |
| 4 | Middleware والأنبوب | 2 | الأنبوب، الترتيب، Middleware مخصص |
| 5 | تصميم API احترافي | 5 | Routing/Binding، DTO/Validation، Errors، Pagination/Versioning/Idempotency |
| 6 | البيانات والمعمارية | 9 | EF Core، Clean Architecture، Domain Modeling، CQRS/Modular Monolith، Outbox |
| 7 | الأمان | 3 | JWT، Authorization، OWASP/CORS/Rate Limiting/Data Protection |
| 8 | التشغيل والإنتاج | 5 | Caching، GC/الذاكرة/JSON، Docker، Observability، CI/CD |
| 9 | الاختبارات والجودة | 4 | Unit، Integration/Testcontainers، TDD/Analyzers، Load Testing |
| 10 | المشروع والوظيفة | 4 | Capstone Build/Deploy، Portfolio/Interview، Next Steps |
| 11 | مواضيع متقدمة | 4 | gRPC/SignalR، GraphQL، Saga/Microservices، Data Protection |

المجموع: **11 وحدة / 46 درسًا**.

## الدروس بالتفصيل

### 1. الأساس

1. `dotnet-ecosystem` — .NET SDK vs Runtime vs CLR، IL/JIT، GC، ودورة حياة التطبيق.
2. `csharp-backend-1` — الأنواع، `var`، nullability، classes/records، الخصائص، والواجهات.
3. `csharp-backend-2` — Collections، LINQ، `async/await`، الاستثناءات، و`IDisposable`.
4. `dotnet-cli` — إنشاء المشروع، الحلول، الحزم، البناء، التشغيل، والنشر.

### 2. تشريح المشروع وHTTP

5. `http-fundamentals` — Methods، Status Codes، Headers، REST، Idempotency، وContent Negotiation.
6. `project-anatomy` — `.csproj`، `launchSettings.json`، `appsettings`، المجلدات، وملف الحل.
7. `program-cs` — Top-level statements، Builder/Services/Pipeline/Run، ترتيب Middleware، وGraceful Shutdown.
8. `kestrel` — الاستماع، TLS، الحدود، Timeouts، الاتصالات، والإيقاف اللطيف.

### 3. DI والإعدادات

9. `di-lifetimes` — Transient/Scoped/Singleton، ملكية الكائنات، والتحقق من النطاقات.
10. `di-pitfalls` — Captive Dependency، Service Locator، `HttpContext` في Singleton، والتصميم القابل للاختبار.

### 4. Middleware والأنبوب

11. `middleware-mechanics` — الأنبوب، الترتيب، Short-circuit، `InvokeAsync`، والاستثناءات.
12. `custom-middleware` — كتابة Middleware، `IMiddleware`، Correlation ID، واختبار السلوك.

### 5. تصميم API

13. `routing-binding` — Route Templates، Constraints، Model Binding، و`[FromBody]`.
14. `results-openapi` — `IResult`/`TypedResults`، Serialization، OpenAPI، وDocumentation.
15. `dto-validation` — DTOs، Records، FluentValidation، Validation Problem Details، وMass Assignment.
16. `errors-logging` — `IExceptionHandler`، Problem Details، Serilog، Structured Logs، وCorrelation.
17. `api-evolution` — Pagination/Filtering/Sorting، Versioning، Idempotency Keys، وDeprecation.

### 6. البيانات والمعمارية

18. `efcore-modeling` — DbContext، Entities، Keys، Relationships، Conventions، وMigrations.
19. `efcore-tracking` — Change Tracker، Identity Map، `AsNoTracking`، وDetached entities.
20. `efcore-queries` — LINQ Translation، Projection، N+1، Eager/Lazy/Explicit Loading، وPagination.
21. `efcore-performance` — Indexes، Compiled Queries، Split Queries، Execution Plans، وAsNoTracking.
22. `efcore-transactions-concurrency` — Transactions، Isolation، Optimistic Concurrency، وRaw SQL.
23. `clean-architecture` — الاعتماديات، الطبقات، Use Cases، DTO Boundaries، وقابلية الاختبار.
24. `domain-modeling` — Entities/Value Objects/Aggregates، Invariants، وDomain Events.
25. `modular-monolith-cqrs` — Vertical Slices، CQRS-lite، MediatR، ومتى تختار Microservices.
26. `outbox-messaging` — Outbox Pattern، Integration Events، Idempotent Consumers، وMessage Brokers.

### 7. الأمان

27. `jwt-auth` — التوقيع، التحقق، Claims، Refresh Tokens، وتخزين المفاتيح.
28. `authorization` — Policies، Roles، Claims، Resource-based Authorization، و`[Authorize]`.
29. `security-hardening` — BOLA/BFLA، Injection، Mass Assignment، SSRF، CORS، Rate Limiting، HTTPS، وData Protection.

### 8. التشغيل

30. `caching` — Output Cache، Hybrid Cache، Redis، Invalidation، وCache Keys.
31. `memory-performance` — GC Generations، Allocations، `Span<T>`، `ArrayPool`، JSON Source Generation.
32. `docker-deploy` — Multi-stage Dockerfile، Compose، Secrets، Migrations، Reverse Proxy، وHTTPS.
33. `observability` — Serilog، OpenTelemetry، Traces/Metrics/Logs، Health Checks، وDashboards.
34. `ci-cd-cloud` — GitHub Actions، Publish، Azure Container Apps/App Service، Managed Identity، وZero-downtime.

### 9. الاختبارات

35. `unit-testing` — xUnit، Arrange/Act/Assert، Mocks/Fakes، واختبار السلوك لا التنفيذ.
36. `integration-testing` — `WebApplicationFactory`، Testcontainers، قاعدة بيانات معزولة، وAuth في الاختبار.
37. `tdd-analyzers` — TDD، Coverage، EditorConfig، Analyzers، وCI Quality Gates.
38. `load-testing` — BenchmarkDotNet، k6/NBomber، Profiling، وتفسير النتائج.

### 10. المشروع والوظيفة

39. `capstone-build` — تجميع Souq.NET: المجلدات، القرارات، المنتجات، السلة، الطلبات، والاختبارات.
40. `capstone-deploy` — نشر المشروع، Smoke Tests، Observability، وRunbook.
41. `portfolio-interview` — README احترافي، Portfolio، CV، أسئلة Backend، وSystem Design.
42. `next-steps` — خطة تعلم مستمرة، Cloud، Open Source، وتجنب tutorial hell.

### 11. مواضيع متقدمة

43. `grpc-signalr` — protobuf، HTTP/2، Streaming، Deadlines، SignalR Hubs، وBackplane.
44. `graphql` — Schema/Resolvers، DataLoader، Authorization، Depth/Complexity، وCaching.
45. `saga-microservices` — Orchestration/Choreography، Compensation، Idempotency، وOutbox.
46. `data-protection` — التشفير مقابل التجزئة، Key Ring، إدارة الأسرار، Redaction، والنسخ.

## ربط المشروع

كل درس يضيف خطوة إلى **Souq.NET E-Commerce API**. صفحة «المشروع» في التطبيق تجمع
كل الخطوات (231+ خطوة) في مسار واحد، وتسمح بتعليمها دون فصلها عن الدروس.

النطاق النهائي للمشروع:

- منتجات مع CRUD وبحث وترقيم صفحات.
- مصادقة JWT وصلاحيات Admin/Customer.
- سلة وطلبات ومعاملات ومنع تكرار الطلب.
- EF Core مع علاقات وترحيلات واستعلامات محسّنة.
- كاش، مراقبة، اختبارات تكامل، Docker، ونشر.
- README وOpenAPI يصلحان كعرض في Portfolio.

## المصادر المرجعية

- Microsoft Learn — ASP.NET Core: <https://learn.microsoft.com/aspnet/core/>
- Microsoft Learn — Minimal APIs: <https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/>
- Microsoft Learn — EF Core: <https://learn.microsoft.com/ef/core/>
- Microsoft Learn — Security: <https://learn.microsoft.com/aspnet/core/security/>
- Microsoft Learn — Testing: <https://learn.microsoft.com/aspnet/core/test/>
- Microsoft Learn — Performance: <https://learn.microsoft.com/aspnet/core/performance/>
- Microsoft Learn — Host and deploy: <https://learn.microsoft.com/aspnet/core/host-and-deploy/>
- Microsoft Learn — .NET architecture: <https://learn.microsoft.com/dotnet/architecture/>
- roadmap.sh — ASP.NET Core: <https://roadmap.sh/aspnet-core>
- roadmap.sh — Backend: <https://roadmap.sh/backend>
- OWASP API Security Top 10: <https://owasp.org/API-Security/editions/2023/en/0x00-header/>
- Twelve-Factor App: <https://12factor.net/>

## حالة التنفيذ

- الواجهة الجديدة: مكتملة.
- دعم شرح الكود سطرًا بسطر: مكتمل في المحرّك ومطبّق على كل الدروس الـ46.
- المحتوى الحالي: 46 درسًا تعمل داخل الواجهة الجديدة؛ أُضيفت دروس C# وHTTP وEF Core ونتائج API والمعاملات وتطوير API وتقسية الأمان، واختبارات الوحدة والتكامل وTDD وLoad Testing وDomain Modeling وModular Monolith/CQRS وOutbox/Messaging وObservability وCI/CD وCapstone وPortfolio، وgRPC/SignalR وGraphQL وSaga وData Protection.
- كل درس يضم: مفهومًا، Walkthrough، مقارنة قبل/بعد، Internals، نصائح، 3 أسئلة، ومهام مشروع.
- لا دروس فارغة أو عناصر «TODO»؛ اجتاز المحتوى فحص الاكتمال.
- الهدف تحقق: 11 وحدة / 46 درسًا / 138 سؤالًا / 231 مهمة مشروع.
