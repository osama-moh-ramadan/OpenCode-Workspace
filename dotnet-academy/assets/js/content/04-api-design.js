/* الوحدة 5 — تصميم الـ API: التوجيه، الربط، DTOs، الأخطاء، والسجلات. */
Academy.addModule({
  id: "api-design",
  title: "تصميم الـ API",
  tagline: "واجهة برمجية جيدة ليست «تعمل» فقط: عقد واضح، أخطاء مفهومة، وحدود لا تتسرّب.",
  icon: "⇢",
  color: "#34d399",
  lessons: [
    {
      id: "routing-binding",
      title: "Routing + Model Binding: من المسار إلى الكائن",
      duration: 24,
      level: "متوسط",
      summary:
        "كيف يعرف ASP.NET Core أي دالة ينفّذ، ومن أين يقرأ كل معامل؟ سنفكّك قوالب المسارات، القيود، مصادر الربط، والفرق العملي بين Minimal APIs وControllers.",
      keywords: ["routing", "route constraints", "model binding", "minimal api", "MapGroup", "TypedResults"],
      objectives: [
        "تكتب قوالب مسار دقيقة مع قيود تمنع الأخطاء.",
        "تعرف من أين يُربط كل معامل (route/query/body/header/service).",
        "تختار بين Minimal API وController بناءً على متطلبات حقيقية.",
        "تعيد نتائج مُصنّفة تُنتج OpenAPI صحيحًا.",
      ],
      concept: `
        <p>عند وصول طلب، يمرّ عبر <strong>Endpoint Routing</strong>: جدول من القوالب، ومطابق يختار أفضل تطابق. ثم يُنشأ <code>Endpoint</code> يحمل الـ delegate والبيانات الوصفية (Metadata): السياسات، أسماء المستندات، وأشكال الاستجابة.</p>
        <p>قالب المسار ليس نصًا عشوائيًا. <code>/api/products/{id:int}</code> يعني: مقطع إلزامي اسمه id، ويجب أن يكون عددًا صحيحًا. إن أرسلت <code>/api/products/abc</code> فلن يطابق القالب، والنتيجة 404 لا 400 — نقطة يخطئ فيها كثيرون. أضف قيودًا (<code>:int</code>, <code>:guid</code>, <code>:min(1)</code>, <code>:length(3,20)</code>) لتوضيح العقد ولتجنّب الغموض بين مسارين.</p>
        <h3>مصادر الربط</h3>
        <ul>
          <li><strong>Route</strong>: قيمة من قالب المسار.</li>
          <li><strong>Query</strong>: من <code>?page=2&amp;size=20</code>.</li>
          <li><strong>Body</strong>: JSON في جسم الطلب، يُفكّ عبر System.Text.Json.</li>
          <li><strong>Header</strong>: عبر <code>[FromHeader]</code> في Controllers أو نوع مخصص.</li>
          <li><strong>Services</strong>: أي نوع مسجّل في DI يُحقن تلقائيًا.</li>
          <li><strong>Special</strong>: <code>HttpContext</code>، <code>CancellationToken</code>، <code>ClaimsPrincipal</code>، <code>IFormFile</code>.</li>
        </ul>
        <p>القاعدة في Minimal APIs: الأنواع البسيطة (int, string, Guid, DateTime) تُقرأ من المسار أو الـ query، والأنواع المركّبة (class/record) تُقرأ من الجسم كـ JSON. إذا احتجت تحكمًا صريحًا، استخدم السمات أو <code>AsParameters</code> لتجميع المعاملات في record.</p>
        <h3>Minimal أم Controllers؟</h3>
        <p>Minimal APIs أخف: لا Controller Activation، ولا Filter Pipeline كامل، ولا Model Binder تقليدي. مناسبة لمعظم الخدمات الحديثة. Controllers تتفوق إذا احتجت <em>Model Binding</em> مخصصًا، أو <em>Application Parts</em>، أو OData، أو فريقًا يعتمد عليه. لا تخلط النمطين في نفس المورد بلا سبب.</p>
        <h3>TypedResults</h3>
        <p>استخدام <code>Results.Ok(x)</code> يرجع <code>IResult</code> ويخفي الأنواع عن OpenAPI. <code>TypedResults.Ok(x)</code> يعيد نوعًا معروفًا وقت الترجمة، فيستطيع المولّد وصف الاستجابات بدقة، وتساعدك الاختبارات على التحقق من النوع. هذا فرق صغير في الكتابة، كبير في جودة العقد.</p>
      `,
      walkthrough: [
        {
          title: "قالب المسار والقيود",
          code: `app.MapGet("/api/products/{id:guid}",
    (Guid id) => Results.Ok(id));`,
          lang: "csharp",
          body: `<p><code>{id:guid}</code> مقطع ديناميكي مع قيد نوع. الطلب <code>/api/products/42</code> لا يطابق، ويعطي 404 قبل تنفيذ الـ endpoint. القيد ليس تحقق أعمال؛ هو تصفية مسار. استخدم <code>:int</code> و<code>:guid</code> و<code>:length(3,10)</code> حسب الشكل، لكن افحص القيم وقواعد العمل داخل الـ endpoint أو الـ validator.</p>`
        },
        {
          title: "من أين تأتي القيمة؟",
          code: `app.MapGet("/api/products/{id:guid}",
    ([FromRoute] Guid id,
     [FromQuery] int page,
     [FromHeader(Name = "X-Tenant")] string tenant) => ...);`,
          lang: "csharp",
          body: `<p><code>FromRoute</code> من المسار، <code>FromQuery</code> من <code>?page=2</code>، و<code>FromHeader</code> من ترويسة. في Minimal APIs يستنتج الإطار المصدر عادةً، لكن السمات توضح العقد وتزيل الغموض. لا تضع بيانات حساسة في route/query لأنها تظهر في السجلات. لكل مصدر حدود ودلالة مختلفة.</p>`
        },
        {
          title: "جسم واحد فقط",
          code: `app.MapPost("/api/products",
    ([FromBody] CreateProductRequest request) => ...);`,
          lang: "csharp",
          body: `<p>يُقرأ جسم الطلب مرة واحدة، لذلك لا يمكن أن يكون لديك أكثر من معامل <code>[FromBody]</code>. الـ JSON يُربط بالخصائص أو الـ constructor. إذا كان الجسم مشوّهًا أو <code>Content-Type</code> غير مدعوم، يعيد الإطار 400/415 قبل الكود. لا تحاول قراءة <code>Request.Body</code> يدويًا بعد أن استهلكه الـ binder.</p>`
        },
        {
          title: "قيم افتراضية للاستعلام",
          code: `app.MapGet("/api/products",
    (int page = 1, int pageSize = 20) => ...);`,
          lang: "csharp",
          body: `<p>القيم الافتراضية تجعل المعامل اختياريًا في query. لكنها لا تفرض حدًا أقصى؛ طلب <code>?pageSize=100000</code> سيُقبل إذا لم تتحقق. اضبط <code>pageSize</code> بين 1 و100، وارجع 400 أو <code>ValidationProblem</code> عند التجاوز. الترقيم ليس تجميلًا؛ هو حماية للذاكرة وقاعدة البيانات.</p>`
        },
        {
          title: "قيود لا تغني عن التحقق",
          code: `app.MapGet("/api/products/{id:guid}",
    (Guid id) => ...);

app.MapGet("/api/products/{slug:length(3,80)}",
    (string slug) => ...);`,
          lang: "csharp",
          body: `<p>القيد يمنع القيم غير المطابقة للشكل، لكنه لا يعرف إن كان المنتج موجودًا أو مصرحًا لك. <code>:length</code> يتحقق من الطول فقط. قاعدة العمل «السعر موجب» أو «المخزون كافٍ» تحتاج تحققًا آخر. افصل بين <strong>شكل المدخل</strong> و<strong>قواعد العمل</strong>؛ الخلط يجعل الرسائل غامضة.</p>`
        },
        {
          title: "أسبقية المسارات",
          code: `app.MapGet("/api/products/featured", () => ...);
app.MapGet("/api/products/{id:guid}", (Guid id) => ...);`,
          lang: "csharp",
          body: `<p>المقاطع الحرفية لها أسبقية على الديناميكية عادةً، لكن لا تُبنِ التصميم على ترتيب التسجيل. تجنّب المسارات المتقاطعة التي يمكن أن تطابق أكثر من endpoint. استخدم قيودًا واضحة مثل <code>:guid</code>، واختبر <code>/featured</code> و<code>/8f14...</code>. المسار الغامض يظهر كخطأ 500 أو سلوك متغير يصعب تشخيصه.</p>`
        },
        {
          title: "أنشئ رابط المورد بعد الإنشاء",
          code: `var created = TypedResults.Created(
    $"/api/products/{product.Id}", product);
return created;`,
          lang: "csharp",
          body: `<p><code>Created</code> ينتج 201 مع <code>Location</code>. استخدم <code>TypedResults</code> عندما تريد نوع استجابة معروفًا لـ OpenAPI والاختبارات. لا تبنِ الرابط يدويًا بأصل ثابت؛ استخدم <code>LinkGenerator</code> أو <code>CreatedAtRoute</code> إذا كان المسار معقدًا أو خلف proxy. الرابط يجب أن يعمل من بيئة النشر لا من localhost فقط.</p>`
        },
        {
          title: "الوصول الخام عند الحاجة",
          code: `var rawId = context.Request.RouteValues["id"];
var page = context.Request.Query["page"].ToString();`,
          lang: "csharp",
          body: `<p>يمكنك قراءة القيم يدويًا من <code>HttpContext</code> عندما لا يناسبك binding، مثل middleware أو endpoint ديناميكي. القيم تصل كنصوص؛ التحويل والتحقق مسؤوليتك. تجنّب هذا في المسارات العادية لأنه يكرر ما يفعله الإطار ويفقد مزايا OpenAPI والاختبارات.</p>`
        },
        {
          title: "أعد أخطاء التحقق بوضوح",
          code: `var errors = new Dictionary<string, string[]>
{
    ["pageSize"] = new[] { "pageSize must be <= 100" }
};
return TypedResults.ValidationProblem(errors);`,
          lang: "csharp",
          body: `<p><code>ValidationProblem</code> ينتج 400 بصيغة Problem Details مع أخطاء مرتبطة بالحقول. لا ترجع نصًا عامًا مثل «بيانات غير صحيحة»؛ العميل يحتاج معرفة الحقل. في Minimal APIs، <code>ValidationProblem</code> أو <code>Results.ValidationProblem</code> واضحان. لا تخلط 400 (مدخل غير صالح) مع 409 (تعارض حالة) أو 422 إن اعتمدته لفصل دلالي.</p>`
        }
      ],
      compare: {
        intro: `<p>نفس المورد مرتين: Controller بسمات، وMinimal API بمجموعة مسارات. لاحظ كم من «السحر الضمني» يختفي في الثانية — وكم من المرونة يبقى في الأولى.</p>`,
        before: {
          label: "Controller",
          lang: "csharp",
          title: "ProductsController.cs",
          code: `[ApiController]
[Route("api/v1/products")]
public sealed class ProductsController : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<PagedResult<ProductDto>>> List(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
        => Ok(await _service.ListAsync(page, size, ct));

    [HttpGet("{id:int:min(1)}")]
    [ProducesResponseType<ProductDto>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProductDto>> Get(int id, CancellationToken ct)
    {
        var item = await _service.GetAsync(id, ct);
        return item is null ? NotFound() : Ok(item);
    }
}`,
          points: [
            "سمات صريحة وواضحة، لكنها كثيرة.",
            "Model Binding المتقدم جاهز.",
            "اكتشاف عبر Application Parts.",
          ],
        },
        after: {
          label: "Minimal API",
          lang: "csharp",
          title: "Endpoints/ProductEndpoints.cs",
          code: `public static class ProductEndpoints
{
    public static IEndpointRouteBuilder MapProducts(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/v1/products")
            .WithTags("Products")
            .WithOpenApi();

        group.MapGet("/", async (
            IProductService service,
            int page = 1,
            int size = 20,
            CancellationToken ct = default) =>
        {
            var result = await service.ListAsync(page, size, ct);
            return TypedResults.Ok(result);
        });

        group.MapGet("/{id:int:min(1)}", async Task<Results<Ok<ProductDto>, NotFound>> (
            int id, IProductService service, CancellationToken ct) =>
        {
            var item = await service.GetAsync(id, ct);
            return item is null ? TypedResults.NotFound() : TypedResults.Ok(item);
        });

        return app;
    }
}`,
          points: [
            "ربط تلقائي للمعاملات البسيطة من query/route.",
            "TypedResults توثّق الاستجابات.",
            "تجميع منطقي عبر MapGroup.",
          ],
        },
        verdict: `<p>Minimal APIs ليست «نسخة مبسطة» من Controllers؛ إنها نموذج مختلف: دوال صريحة بدل اكتشاف ضمني. اختر بناءً على حاجة الفريق والعقد، لا على الموضة. الأهم أن يكون الـ API متسقًا: نفس أسلوب الأخطاء، نفس نمط التسمية، ونفس التوثيق.</p>`,
      },
      internals: `
        <p>مطابق المسارات في ASP.NET Core مبني على <strong>DFA</strong> (Deterministic Finite Automaton)، وليس مرورًا خطيًا على القوالب. يُبنى هيكل شجري من المقاطع، فتصبح المطابقة سريعة حتى مع آلاف المسارات. الأولوية: المقطع الحرفي يتفوق على المعامل، والمعامل المقيّد يتفوق على غير المقيّد، و<code>{*path}</code> آخر ما يُجرَّب.</p>
        <p>في Minimal APIs، يُستخدم <strong>RequestDelegateFactory</strong> لتحليل توقيع الدالة وقت البناء، وإنتاج كود ربط مخصص. لا يوجد Reflection في كل طلب. هذا سبب كونها أسرع من Controllers في المسارات البسيطة: لا إنشاء Controller، ولا تشغيل Filter Pipeline كامل، ولا Model Binder تقليدي.</p>
        <p>نوع الإرجاع مهم: إذا أعدت <code>IResult</code>، فالإطار يعرف فقط أنه نتيجة، ويحتاج OpenAPI إلى بيانات وصفية إضافية. أما <code>TypedResults</code> و<code>Results&lt;Ok&lt;T&gt;, NotFound&gt;</code> فتحمل الأنواع في التوقيع، فيستنتج المولّد الحالات الممكنة. هذه «أنواع كتوثيق» وليست ترفًا.</p>
        <p>عند فكّ JSON، يستخدم ASP.NET Core <code>System.Text.Json</code> بإعدادات افتراضية: camelCase، تجاهل الخصائص غير المعروفة، ورفض JSON غير صالح. في .NET 10 يمكن توليد المسلسِلات (source generation) لتحسين البدء وتقليل الذاكرة؛ سنراها في درس الأداء.</p>
      `,
      internalsTable: {
        head: ["القالب", "ماذا يطابق؟", "ملاحظة"],
        rows: [
          ["/products/{id:int}", "/products/42", "42 فقط، وليس abc"],
          ["/products/{slug:alpha}", "/products/phone", "حروف فقط"],
          ["/files/{*path}", "/files/a/b/c.txt", "Catch-all، أدنى أولوية"],
          ["/products/{id:guid}", "/products/<guid>", "مناسب للمعرّفات الموزعة"],
        ],
      },
      tips: [
        {
          title: "لا تضع أفعالًا في المسار",
          body: "استخدم <code>POST /orders/{id}/cancel</code> عند الحاجة لعملية غير CRUD، لا <code>GET /cancelOrder</code>. الأفعال في HTTP methods، والمسارات للموارد.",
        },
        {
          title: "قيّد المعاملات مبكرًا",
          body: "قيد <code>{id:int}</code> يمنع الوصول إلى منطقك بقيم غير صالحة، ويجعل 404/400 متوقعة. أضف <code>min(1)</code> للمعرّفات الموجبة.",
        },
        {
          title: "استخدم MapGroup للاتساق",
          body: "المجموعة تشارك البادئة والوسوم والسياسات. هذا يقلل احتمال نسيان <code>RequireAuthorization</code> على مسار واحد.",
        },
        {
          title: "لا تخلط 404 و400",
          body: "مسار غير مطابق = 404. جسم غير صالح أو فشل تحقق = 400. قيمة غير موجودة في قاعدة البيانات = 404. الاتساق هنا جزء من العقد.",
        },
      ],
      quiz: [
        {
          q: "ماذا يحدث لطلب <code>/api/products/abc</code> مع القالب <code>{id:int}</code>؟",
          options: ["يُرجع 400 بسبب تحويل فاشل", "لا يطابق المسار فيُرجع 404", "يُرجع 500", "يُحوَّل تلقائيًا إلى 0"],
          answer: 1,
          explain:
            "القيد يمنع المطابقة أصلًا، فلا يصل الطلب إلى الـ endpoint. النتيجة 404 وليست خطأ تحويل.",
        },
        {
          q: "أي نوع إرجاع يحسّن دقة OpenAPI؟",
          options: ["object", "IResult فقط", "TypedResults / Results<T1,T2>", "string دائمًا"],
          answer: 2,
          explain:
            "الأنواع المُصنّفة تحمل الحالات الممكنة في التوقيع، فيستنتج مولّد OpenAPI الاستجابات بدقة.",
        },
        {
          q: "أين تُقرأ الأنواع المركّبة (class/record) افتراضيًا في Minimal API؟",
          options: ["من الـ query", "من جسم الطلب كـ JSON", "من الهيدرات", "من المسار"],
          answer: 1,
          explain:
            "الأنواع البسيطة تُقرأ من route/query، والمركّبة من body افتراضيًا، ما لم تحدّد خلاف ذلك بسمة.",
        },
      ],
      capstone: {
        title: "مجموعة مسارات المنتجات",
        goal: "نبني أول مورد حقيقي في Souq.NET: مسارات CRUD مع قيود وتجميع ونتائج مُصنّفة، دون قاعدة بيانات بعد.",
        tasks: [
          "أنشئ <code>MapGroup(\"/api/v1/products\")</code> وأضف الوسوم.",
          "أضف <code>GET /</code> مع page وsize كـ query parameters.",
          "أضف <code>GET /{id:int:min(1)}</code> يعيد 404 عند عدم الوجود.",
          "أضف <code>POST /</code> يستقبل DTO ويعيد 201 مع رابط المورد.",
          "تحقق من ظهور كل المسارات في OpenAPI.",
        ],
        code: {
          lang: "csharp",
          title: "النتائج المُصنّفة",
          code: `group.MapPost("/", async Task<Results<Created<ProductDto>, ValidationProblem>> (
    CreateProductRequest request,
    IProductService service,
    CancellationToken ct) =>
{
    var created = await service.CreateAsync(request, ct);
    return TypedResults.Created($"/api/v1/products/{created.Id}", created);
});`,
        },
      },
    },
    {
      id: "results-openapi",
      title: "Results & OpenAPI: عقد قابل للاختبار والتوثيق",
      duration: 24,
      level: "متوسط",
      summary:
        "الـ endpoint ليس دالة ترجع كائنًا؛ هو عقد حالة ومحتوى. سنستخدم TypedResults لنجعل الاستجابات جزءًا من نوع الدالة، ثم نولّد OpenAPI يصف العقد للعميل والاختبارات.",
      keywords: ["TypedResults", "IResult", "ProblemDetails", "OpenAPI", "Produces", "operation metadata", "contract testing"],
      objectives: [
        "تفرّق بين Results وTypedResults وأثر ذلك على OpenAPI.",
        "تعيد الحالة والمحتوى الصحيحين لكل نتيجة عمل.",
        "توثّق الاستجابات الناجحة والأخطاء في OpenAPI.",
        "تستخدم ProblemDetails للأخطاء القابلة للقراءة آليًا.",
        "تختبر عقد الـ API لا النص فقط."
      ],
      concept: `
        <p>في Minimal APIs، الـ endpoint يعيد <strong>IResult</strong>. هذا abstraction يحدد الحالة والترويسات والجسم. يمكنك كتابة <code>Results.Ok(x)</code> أو <code>Results.NotFound()</code>، لكن النوع الثابت سيكون <code>IResult</code>؛ أي أن OpenAPI والاختبارات لا يعرفان أي الحالات ممكنة. <strong>TypedResults</strong> يعيد نوعًا محددًا مثل <code>Ok&lt;T&gt;</code> أو <code>NotFound</code>، ويسمح بتركيب اتحاد أنواع مثل <code>Results&lt;Ok&lt;ProductDto&gt;, NotFound&gt;</code>.</p>
        <p>لماذا يهم؟ لأن العقد ليس «يرجع JSON». العقد هو: متى 200، متى 404، متى 409، وما شكل الجسم في كل حالة. عندما يكون النوع صريحًا، يستطيع مولّد OpenAPI وصف الاستجابات، وتستطيع الاختبارات التحقق من أن التغيير لم يكسر العميل. هذا لا يمنع الأخطاء وقت التشغيل، لكنه يجعل النية جزءًا من الكود.</p>
        <h3>النتيجة الصحيحة لكل حالة</h3>
        <p><code>Ok</code> للقراءة الناجحة، <code>Created</code> للإنشاء مع <code>Location</code>، <code>NoContent</code> للحذف أو التحديث بلا جسم، <code>NotFound</code> للمورد الغائب، <code>ValidationProblem</code> للمدخلات غير الصالحة، <code>Conflict</code> لتعارض حالة، و<code>Problem</code> لخطأ عمل موثق. لا ترجع <code>200</code> مع <code>{ success: false }</code>؛ هذا يجعل الـ cache والمراقبة والعميل عاجزة عن فهم النتيجة.</p>
        <h3>OpenAPI ليس توثيقًا فقط</h3>
        <p>OpenAPI يصف المسارات والعمليات والمخططات والاستجابات والأمان. يمكن توليد عميل TypeScript أو اختبارات عقد أو بوابات API منه. في .NET 10 تستخدم <code>AddOpenApi</code> و<code>MapOpenApi</code>، وتضيف <code>WithName</code> و<code>WithSummary</code> و<code>Produces&lt;T&gt;</code> و<code>ProducesProblem</code> لإثراء الوثيقة. لا تفعّل <code>MapOpenApi</code> في الإنتاج بلا حماية؛ هو يكشف بنية API وقد يكشف تفاصيل داخلية.</p>
        <h3>Problem Details</h3>
        <p>صيغة <code>application/problem+json</code> تعطي حقولًا مثل <code>type</code> و<code>title</code> و<code>status</code> و<code>detail</code> و<code>instance</code>. العميل يستطيع التعامل معها آليًا بدل تحليل نص عربي. لا تضع stack trace أو أسماء جداول أو مسارات داخلية في <code>detail</code>. سجّل التفاصيل في الخادم واربطها بـ<code>traceId</code>، وأعد للعميل رسالة آمنة.</p>
        <h3>العقد والاختبارات</h3>
        <p>اختبار الـ endpoint لا يقتصر على «الحالة 200». اختبر 404، 400، 409، وشكل <code>ProblemDetails</code>، ووجود <code>Location</code>، ونوع المحتوى. يمكنك حفظ نسخة من OpenAPI ومقارنتها في CI لاكتشاف تغييرات غير مقصودة. التغيير الذي يكسر العقد يجب أن يكون قرارًا واعيًا مع إصدار جديد أو توافق خلفي.</p>
      `,
      walkthrough: [
        {
          title: "اتحاد نتائج في توقيع الدالة",
          code: `app.MapGet("/api/products/{id:guid}",
    async Task<Results<Ok<ProductDto>, NotFound>> (
        Guid id, IProductService service, CancellationToken ct) =>`,
          lang: "csharp",
          body: `<p><code>Task&lt;Results&lt;Ok&lt;ProductDto&gt;, NotFound&gt;&gt;</code> يقول للمترجم ولـ OpenAPI: هذه العملية تعيد 200 بجسم <code>ProductDto</code> أو 404 بلا جسم ناجح. النوع ليس زينة؛ هو مصدر المعلومات للمولّد. لاحظ أن <code>Task</code> لأن العملية غير متزامنة، و<code>Results&lt;,&gt;</code> اتحاد حالات وليس قائمة استثناءات.</p>`
        },
        {
          title: "أعد 200 بنوع معروف",
          code: `return TypedResults.Ok(product);`,
          lang: "csharp",
          body: `<p><code>TypedResults.Ok</code> يعيد <code>Ok&lt;ProductDto&gt;</code>، فيعرف المولّد مخطط الجسم. <code>Results.Ok</code> يعيد <code>IResult</code> وقد يضطر OpenAPI لوصف استجابة عامة. استخدم <code>TypedResults</code> افتراضيًا في Minimal APIs الحديثة. لا تستخدم <code>object</code> أو <code>dynamic</code> في توقيع الاستجابة؛ ستفقد العقد.</p>`
        },
        {
          title: "أعد 404 صريحًا",
          code: `return TypedResults.NotFound();`,
          lang: "csharp",
          body: `<p>الحالة 404 تعني أن المورد غير موجود، لا أن المستخدم غير مصرح. لا ترجع <code>Ok(null)</code> أو 200 مع جسم فارغ. إذا أردت شرحًا آمنًا، استخدم <code>Problem</code> أو <code>NotFound</code> مع توثيق <code>ProducesProblem(404)</code>. لا تكشف ما إذا كان المورد موجودًا لمستخدم لا يملك صلاحية؛ قد يكون 404 أفضل أمنيًا من 403 في بعض السيناريوهات.</p>`
        },
        {
          title: "الإنشاء مع Location",
          code: `return TypedResults.Created(
    $"/api/products/{product.Id}", product);`,
          lang: "csharp",
          body: `<p><code>Created</code> ينتج 201 و<code>Location</code> والجسم. الرابط يجب أن يكون مطلقًا أو نسبيًا صحيحًا حسب العقد؛ في الإنتاج خلف proxy استخدم <code>LinkGenerator</code> أو <code>CreatedAtRoute</code> لتجنب أصل localhost. لا تُرجع 200 للإنشاء لمجرد أن الكود نجح؛ 201 تحمل معنى مهمًا للعميل والـ cache.</p>`
        },
        {
          title: "الحذف بلا جسم",
          code: `return TypedResults.NoContent();`,
          lang: "csharp",
          body: `<p><code>NoContent</code> ينتج 204 ويخبر العميل أن العملية نجحت ولا يوجد جسم. مناسب للحذف أو التحديث الذي لا يعيد المورد. لا ترجع 200 مع <code>{}</code> لمجرد أنك تريد جسمًا. إذا كان المورد غير موجود، قرر العقد: 404 أم 204 idempotent؟ وثّق القرار واختبره.</p>`
        },
        {
          title: "أخطاء التحقق كـ Problem",
          code: `var errors = new Dictionary<string, string[]>
{
    ["pageSize"] = new[] { "pageSize must be between 1 and 100" }
};
return TypedResults.ValidationProblem(errors);`,
          lang: "csharp",
          body: `<p><code>ValidationProblem</code> ينتج 400 بصيغة Problem Details مع خريطة أخطاء لكل حقل. العميل يستطيع تمييز الحقل وإظهار رسالة مناسبة. لا ترجع <code>BadRequest(\"invalid\")</code> فقط. لا تخلط التحقق من الشكل مع تعارض الحالة: بريد مكرر قد يكون 409، ومدخل غير صالح 400، حسب عقدك.</p>`
        },
        {
          title: "تعارض عمل موثق",
          code: `return TypedResults.Problem(
    title: "Product already exists",
    detail: "A product with the same SKU already exists.",
    statusCode: StatusCodes.Status409Conflict);`,
          lang: "csharp",
          body: `<p><code>Problem</code> ينتج <code>application/problem+json</code> بحالة 409. استخدمه لتعارض حالة العمل، مثل SKU مكرر أو نسخة قديمة. لا تضع تفاصيل SQL أو اسم القيد. أضف <code>type</code> ثابتًا إن كان العميل يعتمد عليه، واربط <code>traceId</code> بالسجلات. لا تستخدم 500 لخطأ يتوقعه العميل ويعالجه.</p>`
        },
        {
          title: "أثرِ وثيقة OpenAPI",
          code: `.WithName("GetProduct")
.WithSummary("يرجع منتجًا واحدًا")
.WithDescription("404 إذا لم يوجد المنتج.")
.Produces<ProductDto>(StatusCodes.Status200OK)
.ProducesProblem(StatusCodes.Status404NotFound);`,
          lang: "csharp",
          body: `<p><code>WithName</code> يعطي operationId مستقرًا يستخدمه توليد العملاء. <code>WithSummary</code> و<code>WithDescription</code> يشرحان العملية. <code>Produces&lt;T&gt;</code> و<code>ProducesProblem</code> يوثقان الحالات. لا تعتمد على التعليقات فقط؛ المولّد يقرأ metadata. حافظ على أسماء ومسارات مستقرة، وغيّرها فقط مع إصدار جديد.</p>`
        },
        {
          title: "ولّد الوثيقة في التطوير",
          code: `builder.Services.AddOpenApi();

var app = builder.Build();
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}`,
          lang: "csharp",
          body: `<p><code>AddOpenApi</code> يسجل خدمات التوليد، و<code>MapOpenApi</code> يعرض المستند عادةً على <code>/openapi/v1.json</code>. لا تفعّله في الإنتاج بلا مصادقة أو شبكة داخلية. OpenAPI يصف العقد ولكنه لا يفرض التفويض؛ <code>RequireAuthorization</code> و<code>UseAuthorization</code> هما الحماية الفعلية. راجع المستند في CI لاكتشاف تغييرات العقد.</p>`
        }
      ],
      compare: {
        intro: `<p>المقارنة بين endpoint يعيد <code>IResult</code> غامضًا وآخر يعلن حالاته؛ الفرق يظهر في OpenAPI والاختبارات، لا في الاستجابة فقط.</p>`,
        before: {
          label: "نتيجة غامضة",
          lang: "csharp",
          title: "قبل",
          code: `app.MapGet("/api/products/{id}", async (Guid id, Db db) =>
{
    var p = await db.Products.FindAsync(id);
    return p is null ? Results.NotFound() : Results.Ok(p);
});`,
          points: [
            "التوقيع يعيد IResult، فلا يعرف المولّد الحالات.",
            "لا توجد metadata للحالة أو المخطط.",
            "يعيد الكيان مباشرة بدل DTO.",
            "الاختبار لا يعرف شكل 404."
          ]
        },
        after: {
          label: "عقد صريح",
          lang: "csharp",
          title: "بعد",
          code: `app.MapGet("/api/products/{id:guid}",
    async Task<Results<Ok<ProductDto>, NotFound>> (
        Guid id, IProductService service, CancellationToken ct) =>
    {
        var product = await service.GetAsync(id, ct);
        return product is null
            ? TypedResults.NotFound()
            : TypedResults.Ok(product);
    })
    .WithName("GetProduct")
    .Produces<ProductDto>(StatusCodes.Status200OK)
    .ProducesProblem(StatusCodes.Status404NotFound);`,
          points: [
            "الحالات جزء من نوع الدالة.",
            "DTO يحدد مخطط الاستجابة.",
            "OpenAPI يوثق 200 و404.",
            "الاختبارات تستطيع التحقق من العقد."
          ]
        },
        verdict: `<p>لا تحتاج TypedResults في كل سطر، لكن اجعل الاستجابات العامة صريحة. إذا كان endpoint يعيد خمس حالات، فالاتحاد نوع طويل لكنه توثيق حقيقي. استخدم <code>Produces</code> للحالات التي لا يعبّر عنها النوع وحده.</p>`
      },
      internals: `
        <p>عند تنفيذ endpoint، يختار ASP.NET Core <code>IResult</code> ثم يستدعي <code>ExecuteAsync</code> لكتابة الحالة والترويسات والجسم. <code>TypedResults</code> تعيد أنواعًا تنفّذ <code>IResult</code> أيضًا، لكن نوعها الثابت يحمل معلومات إضافية يقرأها ApiExplorer ومولّد OpenAPI. لا يوجد سحر وقت التشغيل: الاتحاد يظل كائنًا واحدًا، لكن metadata تُبنى وقت بدء التطبيق من توقيع الـ endpoint.</p>
        <p>OpenAPI document يُولد من مجموعة endpoints وmetadata: route، methods، parameters، request body، responses، security. المخططات تُشتق من أنواع DTO، وقد تحتاج <code>JsonSerializerOptions</code> متسقة. إذا كانت الحالة تُكتب يدويًا عبر <code>HttpContext.Response</code>، فقد لا يستطيع المولّد رؤيتها. هذا سبب عملي لتفضيل النتائج المعلنة.</p>
        <p>Problem Details تُسلسل كـ<code>application/problem+json</code>. الحقول القياسية تساعد العملاء، لكن لا تضع فيها بيانات حساسة. يجب أن يطابق <code>status</code> في الجسم حالة HTTP الفعلية؛ عدم التطابق يربك العملاء والمراقبة. استخدم <code>IExceptionHandler</code> مركزيًا لتحويل الاستثناءات غير المتوقعة إلى 500 آمن مع traceId.</p>
        <h3>الاختبار والتعاقد</h3>
        <p>اختبار integration يرسل طلبًا حقيقيًا ويتحقق من الحالة والترويسات والجسم. اختبار العقد يمكنه مقارنة OpenAPI المحفوظ بالنسخة المولدة، أو تشغيل مستهلك وهمي. أي تغيير في اسم حقل أو نوعه قد يكون كسرًا حتى لو بقي 200. أضف اختبارات للحالات السلبية، لا للناجحة فقط.</p>
        <h3>ما لا يفعله OpenAPI</h3>
        <p>OpenAPI لا يمنع هجومًا، ولا يفرض authorization، ولا يتحقق من صحة كل قيمة. هو وصف. الأمان يأتي من المصادقة والتفويض والتحقق وحدود المعدل. لا تنشر المستند للعامة إن كان يكشف مسارات إدارية أو مخططات داخلية. الأفضل توليده في CI ونشره داخليًا أو خلف بوابة.</p>
      `,
      internalsTable: {
        head: ["النتيجة", "الحالة", "الجسم", "الاستخدام"],
        rows: [
          ["Ok<T>", "200", "T", "قراءة ناجحة"],
          ["Created<T>", "201", "T + Location", "إنشاء مورد"],
          ["NoContent", "204", "لا جسم", "حذف/تحديث بلا محتوى"],
          ["ValidationProblem", "400", "ProblemDetails + errors", "مدخلات غير صالحة"],
          ["Problem", "409/500...", "ProblemDetails", "تعارض أو خطأ موثق"],
          ["NotFound", "404", "غالبًا بلا جسم", "مورد غير موجود"]
        ]
      },
      tips: [
        {
          title: "استخدم TypedResults افتراضيًا",
          body: "اجعل نوع الاستجابة صريحًا في endpoints العامة. استخدم <code>Results&lt;Ok&lt;T&gt;, NotFound&gt;</code> للحالتين الشائعتين، وأضف <code>Produces</code> لما لا يظهر في النوع."
        },
        {
          title: "لا تعِد الكيانات مباشرة",
          body: "أعد DTOs ثابتة. الكيان قد يكشف حقولًا داخلية أو يتغير مع قاعدة البيانات. الـ DTO هو عقد الـ API، ويجب أن يتغير بقرار واعٍ."
        },
        {
          title: "وثّق الأخطاء لا النجاح فقط",
          body: "أضف <code>ProducesProblem(400)</code> و<code>404</code> و<code>409</code>. العميل يحتاج معرفة شكل الخطأ أكثر من معرفة شكل 200. استخدم Problem Details بدل نصوص حرة."
        },
        {
          title: "احمِ مستند OpenAPI",
          body: "لا تفعّل <code>MapOpenApi</code> للعامة في الإنتاج. ضعه خلف مصادقة أو شبكة داخلية، أو ولّده في CI. المستند يكشف سطح الهجوم وبنية التطبيق."
        }
      ],
      quiz: [
        {
          q: "ما ميزة TypedResults على Results في Minimal APIs؟",
          options: [
            "أسرع دائمًا في التنفيذ.",
            "يحمل نوع الاستجابة معلومات يستطيع OpenAPI والاختبارات استخدامها.",
            "يمنع كل الأخطاء وقت التشغيل.",
            "لا يحتاج HTTP status code."
          ],
          answer: 1,
          explain: "TypedResults يعيد أنواعًا مثل Ok<T> وNotFound، فيستطيع المولّد وصف الحالات والمخططات. ليس حارسًا أمنيًا ولا بديلًا عن الاختبارات."
        },
        {
          q: "أي نتيجة مناسبة لحذف ناجح بلا جسم؟",
          options: ["Ok(null)", "Created", "NoContent", "ValidationProblem"],
          answer: 2,
          explain: "NoContent ينتج 204 ويخبر العميل بالنجاح دون جسم. Ok(null) قد ينتج 200 بجسم فارغ أو null، وهو عقد غامض."
        },
        {
          q: "ماذا يفعل OpenAPI؟",
          options: [
            "يفرض المصادقة على كل endpoint.",
            "يصف عقد الـ API للعملاء والأدوات، لكنه لا يحمي التطبيق.",
            "يمنع إعادة المحاولة.",
            "يحوّل كل استجابة إلى ProblemDetails."
          ],
          answer: 1,
          explain: "OpenAPI وصف للعقد. الحماية تأتي من المصادقة والتفويض والتحقق وحدود المعدل. لا تنشره للعامة دون حماية."
        }
      ],
      capstone: {
        title: "عقد نتائج Souq API",
        goal: "حوّل endpoints المنتجات إلى نتائج معلنة، ووثّق حالات النجاح والفشل، ثم تحقق من OpenAPI.",
        tasks: [
          "أعد كتابة <code>GET /api/products/{id}</code> باستخدام <code>Results&lt;Ok&lt;ProductDto&gt;, NotFound&gt;</code>.",
          "أضف <code>WithName</code> و<code>WithSummary</code> و<code>Produces&lt;ProductDto&gt;</code> و<code>ProducesProblem</code>.",
          "أضف <code>ValidationProblem</code> لمدخلات <code>pageSize</code> غير الصالحة.",
          "أضف <code>Problem</code> بحالة 409 لتعارض SKU مكرر، دون كشف تفاصيل قاعدة البيانات.",
          "ولّد <code>/openapi/v1.json</code> في التطوير واحفظ نسخة في <code>docs/openapi.json</code> للاختبار."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه العقد",
          code: `app.MapGet("/api/products/{id:guid}",
    async Task<Results<Ok<ProductDto>, NotFound>> (
        Guid id, IProductService service, CancellationToken ct) =>
    {
        var product = await service.GetAsync(id, ct);
        return product is null
            ? TypedResults.NotFound()
            : TypedResults.Ok(product);
    })
    .WithName("GetProduct")
    .ProducesProblem(StatusCodes.Status404NotFound);`,
        },
      },
    },
    {
      id: "dto-validation",
      title: "DTOs + FluentValidation: عقد لا يتسرّب",
      duration: 25,
      level: "متوسط",
      summary:
        "لا تُعرّض Entity للعميل، ولا تثق بمدخلاته. سنصمّم DTOs مستقلة، ونطبّق تحققًا واضحًا، ونعيد أخطاء RFC 9457 مفهومة.",
      keywords: ["DTO", "FluentValidation", "DataAnnotations", "ProblemDetails", "ValidationProblem", "record"],
      objectives: [
        "تفصل بين Entity وRequest/Response DTOs.",
        "تستخدم DataAnnotations أو FluentValidation حسب التعقيد.",
        "تعيد أخطاء تحقق موحّدة عبر ProblemDetails.",
        "تتجنب الثغرات الناتجة عن ربط الكيانات مباشرة.",
      ],
      concept: `
        <p><strong>DTO</strong> (Data Transfer Object) هو عقد النقل بين العميل والـ API. ليس Entity، وليس Model داخليًا. Entity تصف تخزين البيانات وعلاقاتها وقد تحتوي حقولًا حساسة (PasswordHash, IsDeleted, RowVersion). DTO تصف ما يُسمح للعميل برؤيته أو إرساله — لا أكثر.</p>
        <p>افصل دائمًا بين:</p>
        <ul>
          <li><code>CreateProductRequest</code>: الحقول المسموح إرسالها عند الإنشاء.</li>
          <li><code>UpdateProductRequest</code>: قد تختلف (لا يمكن تغيير SKU مثلًا).</li>
          <li><code>ProductDto</code>: شكل الاستجابة، معرّفاته وأسعاره المحسوبة.</li>
        </ul>
        <p>استخدام <code>record</code> مناسب هنا: قيمة غير قابلة للتغيير بعد الإنشاء، ومقارنة قيمة، وكتابة أقل. لكن احترس من ربطها المباشر بالـ Entity؛ قد تحتاج تحكمًا في التحويل (Mapping) وحقولًا محسوبة.</p>
        <h3>التحقق على ثلاث طبقات</h3>
        <ol>
          <li><strong>شكل الطلب</strong>: هل JSON صالح؟ هل الحقول المطلوبة موجودة؟ (400)</li>
          <li><strong>قواعد الحقل</strong>: طول الاسم، نطاق السعر، صيغة البريد. (400/422)</li>
          <li><strong>قواعد العمل</strong>: هل SKU مكرر؟ هل المخزون كافٍ؟ (409/422) — هذه ليست مسؤولية Validator بسيط.</li>
        </ol>
        <p>في .NET 10 أصبح لمinimal APIs تحقق مدمج عبر <code>builder.Services.AddValidation()</code>، يعتمد على <code>DataAnnotations</code> ومولّد مصدر (source generator)، ويعيد 400 مع تفاصيل الأخطاء. مناسب للقواعد البسيطة. أما FluentValidation فيتفوق في القواعد المركّبة والرسائل المخصصة والتحقق غير المتزامن (مثل فحص تكرار SKU في قاعدة البيانات).</p>
        <h3>لماذا FluentValidation؟</h3>
        <p>لأنه يفصل قواعد التحقق عن الـ DTO، ويسمح بـ <code>RuleFor</code> متسلسل، ورسائل قابلة للترجمة، واختبارات مستقلة. لا تخلط النمطين عشوائيًا: اختر نمطًا أساسيًا للمشروع ووثّقه.</p>
      `,
      walkthrough: [
        {
          title: "افصل عقد الدخل عن الكيان",
          code: `public sealed record CreateProductRequest(
    string Name,
    decimal Price,
    int Stock);`,
          lang: "csharp",
          body: `<p>الـ DTO يحدد ما يسمح للعميل بإرساله، لا كل ما تحتويه قاعدة البيانات. لا تستخدم كيان EF Core كـ request؛ قد يسمح بحقول مثل <code>Id</code> أو <code>CreatedAt</code> أو <code>IsAdmin</code>. الـ record مناسب لعقد ثابت نسبيًا، لكنه لا يمنع قيمًا غير صالحة؛ التحقق خطوة منفصلة.</p>`
        },
        {
          title: "قواعد FluentValidation",
          code: `public sealed class CreateProductRequestValidator
    : AbstractValidator<CreateProductRequest>
{
    public CreateProductRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(120);

        RuleFor(x => x.Price)
            .GreaterThan(0);

        RuleFor(x => x.Stock)
            .GreaterThanOrEqualTo(0);
    }
}`,
          lang: "csharp",
          body: `<p>كل <code>RuleFor</code> يعرّف قاعدة ورسالة خطأ مرتبطة بالخاصية. <code>NotEmpty</code> ترفض null والنص الفارغ، و<code>MaximumLength</code> تمنع نصًا أطول من العمود. <code>GreaterThan(0)</code> تمنع السعر الصفري أو السالب. هذه قواعد مدخلات، ليست قواعد أعمال مثل «SKU فريد» التي تحتاج قاعدة بيانات.</p>`
        },
        {
          title: "سجّل المدققين",
          code: `builder.Services.AddValidatorsFromAssemblyContaining<
    CreateProductRequestValidator>();`,
          lang: "csharp",
          body: `<p><code>AddValidatorsFromAssemblyContaining</code> يكتشف كل <code>IValidator&lt;T&gt;</code> في assembly ويسجلها. هذا يقلل التسجيل اليدوي ويضمن أن المدقق الجديد متاح. تأكد أن الـ assembly الصحيح هو المصدر؛ مدقق في مشروع آخر لن يُكتشف تلقائيًا. سجّل الـ validators كـ scoped افتراضيًا.</p>`
        },
        {
          title: "تحقق قبل تنفيذ العمل",
          code: `var result = await validator.ValidateAsync(request, ct);
if (!result.IsValid)
{
    var errors = result.ToDictionary();
    return TypedResults.ValidationProblem(errors);
}`,
          lang: "csharp",
          body: `<p><code>ValidateAsync</code> يشغّل كل القواعد ويعيد <code>ValidationResult</code>. <code>ToDictionary</code> ينتج خريطة اسم الحقل إلى رسائل. أعد <code>ValidationProblem</code> قبل لمس قاعدة البيانات أو تعديل الحالة. لا ترمِ استثناءً لكل خطأ تحقق؛ 400 مع تفاصيل هو العقد المتوقع. تأكد أن أسماء الحقول تطابق JSON (camelCase) كي يفهمها العميل.</p>`
        },
        {
          title: "استخدم Endpoint Filter للتحقق العام",
          code: `app.MapPost("/api/products", CreateProduct)
   .AddEndpointFilter(async (context, next) =>
   {
       var request = context.Arguments
           .OfType<CreateProductRequest>().FirstOrDefault();
       if (request is null) return TypedResults.BadRequest();
       var validator = context.HttpContext.RequestServices
           .GetRequiredService<IValidator<CreateProductRequest>>();
       var result = await validator.ValidateAsync(request);
       return result.IsValid
           ? await next(context)
           : TypedResults.ValidationProblem(result.ToDictionary());
   });`,
          lang: "csharp",
          body: `<p>الـ endpoint filter يغلّف التنفيذ ويمكنه إعادة نتيجة قبل الـ handler. مناسب للتحقق المتكرر، لكنه يضيف طبقة غير مرئية في التوقيع. استخدمه عندما تريد تطبيقه على مجموعة endpoints، أو اكتب تحققًا صريحًا إن كان أوضح. لا تحقن scoped services في constructor الـ filter؛ استخدم <code>RequestServices</code> أو معاملات مسجلة حسب النمط.</p>`
        },
        {
          title: "لا تخلط التحقق بقواعد العمل",
          code: `var exists = await repository.SkuExistsAsync(
    request.Sku, ct);
if (exists)
{
    return TypedResults.Problem(
        title: "SKU already exists",
        statusCode: StatusCodes.Status409Conflict);
}`,
          lang: "csharp",
          body: `<p>تكرار SKU ليس خطأ شكل؛ المدخل صالح لكنه يتعارض مع حالة قاعدة البيانات. لذلك 409 أنسب من 400. لا تنفّذ <code>Exists</code> ثم <code>Insert</code> بلا قيد فريد؛ بينهما سباق. اجعل قاعدة البيانات تفرض القيد، وحوّل خطأ القيد إلى 409. هذا يجعل العملية صحيحة تحت التزامن.</p>`
        },
        {
          title: "DTOs منفصلة لكل عملية",
          code: `public sealed record UpdateProductRequest(
    string Name,
    decimal Price);

public sealed record ProductDto(
    Guid Id,
    string Name,
    decimal Price,
    bool IsAvailable);`,
          lang: "csharp",
          body: `<p>لا تستخدم DTO واحدًا للإنشاء والتحديث والقراءة. كل عملية لها حقول مسموحة ومطلوبة مختلفة. <code>UpdateProductRequest</code> قد لا يسمح بتغيير ID، و<code>ProductDto</code> يضيف حقول قراءة محسوبة. هذا يمنع over-posting ويجعل OpenAPI دقيقًا. أسماء واضحة أفضل من <code>ProductModel</code> الغامض.</p>`
        },
        {
          title: "تحقق من التحديث الجزئي",
          code: `public sealed record PatchProductRequest(
    string? Name,
    decimal? Price);

RuleFor(x => x.Price)
    .GreaterThan(0)
    .When(x => x.Price.HasValue);`,
          lang: "csharp",
          body: `<p>في PATCH، الحقل الغائب يعني «لا تغيّره»، وليس «اجعله null». استخدم <code>decimal?</code> و<code>When</code> لتطبيق القاعدة فقط عند وجود قيمة. لا تخلط بين null (غائب/مسح) و0 (قيمة صالحة أو غير صالحة حسب القاعدة). وثّق دلالة null لكل حقل، واختبر طلبًا بحقل واحد فقط.</p>`
        },
        {
          title: "اختبر المدخلات لا النجاح فقط",
          code: `var response = await client.PostAsJsonAsync(
    "/api/products",
    new { name = "", price = 0, stock = -1 });

Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
var problem = await response.Content
    .ReadFromJsonAsync<ValidationProblemDetails>();
Assert.Contains("name", problem!.Errors.Keys);`,
          lang: "csharp",
          body: `<p>الاختبار الجيد يرسل مدخلات غير صالحة ويتحقق من 400 ومن مفاتيح الأخطاء. لا تكتفِ بأن الـ endpoint يعمل مع مدخل صحيح. غطِّ: اسم فارغ، سعر صفر، مخزون سالب، JSON مشوّه، ونوع محتوى خاطئ. هذه الحالات هي ما سيراه العميل الحقيقي، وتكشف أخطاء الربط والتسمية.</p>`
        }
      ],
      compare: {
        intro: `<p>الطريقة القديمة تربط Entity مباشرة وتتحقق بـ ifs مبعثرة. الطريقة الحديثة تفصل العقد وتُرجع أخطاء منظمة يمكن للعميل التعامل معها آليًا.</p>`,
        before: {
          label: "Entity مباشرة + ifs",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapPost("/api/products", async (Product product, SouqDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(product.Name))
        return Results.BadRequest("name is required");

    if (product.Price <= 0)
        return Results.BadRequest("price must be positive");

    if (product.Name.Length > 200)
        return Results.BadRequest("name too long");

    db.Products.Add(product);
    await db.SaveChangesAsync();

    // يعيد Entity كاملة، بما فيها حقول داخلية
    return Results.Ok(product);
});`,
          points: [
            "العميل يستطيع تعيين Id أو IsDeleted.",
            "رسائل الأخطاء نصوص غير موحّدة.",
            "التحقق مكرر في كل عملية.",
          ],
        },
        after: {
          label: "DTO + Validator + ProblemDetails",
          lang: "csharp",
          title: "Products/CreateProduct.cs",
          code: `public sealed record CreateProductRequest(
    string Name,
    string Sku,
    decimal Price,
    int CategoryId);

public sealed class CreateProductValidator : AbstractValidator<CreateProductRequest>
{
    public CreateProductValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("اسم المنتج مطلوب.")
            .MaximumLength(200);

        RuleFor(x => x.Sku)
            .NotEmpty()
            .Matches("^[A-Z0-9-]{3,20}$")
            .WithMessage("SKU يجب أن يكون 3-20 حرفًا كبيرًا أو أرقامًا.");

        RuleFor(x => x.Price)
            .GreaterThan(0)
            .LessThan(1_000_000);

        RuleFor(x => x.CategoryId).GreaterThan(0);
    }
}

app.MapPost("/api/v1/products", async (
    CreateProductRequest request,
    IValidator<CreateProductRequest> validator,
    IProductService service,
    CancellationToken ct) =>
{
    var result = await validator.ValidateAsync(request, ct);
    if (!result.IsValid)
        return Results.ValidationProblem(result.ToDictionary());

    var created = await service.CreateAsync(request, ct);
    return Results.Created($"/api/v1/products/{created.Id}", created);
});`,
          points: [
            "عقد إدخال واضح ومحدود.",
            "قواعد قابلة للاختبار ومترجمة.",
            "استجابة خطأ قياسية RFC 9457.",
          ],
        },
        verdict: `<p>الفصل بين DTO وEntity ليس بيروقراطية؛ إنه خط دفاع. كل حقل في Entity لا تريده أن يصل من العميل يجب ألا يكون في DTO الإدخال. وكل حقل داخلي لا تريده أن يخرج يجب ألا يكون في DTO الاستجابة.</p>`,
      },
      internals: `
        <p><strong>DataAnnotations</strong> تعمل عبر Reflection عادةً، لكن .NET 10 استخدمت مولّد مصدر للتحقق في Minimal APIs: يُحلّل أنواع المعاملات وقت الترجمة ويولّد كود تحقق مباشر. الفائدة: بدء أسرع وتخصيص أقل، لكن الأنواع يجب أن تكون في نفس assembly الذي يستدعي <code>AddValidation</code>.</p>
        <p><strong>FluentValidation</strong> يبني مخطط القواعد مرة واحدة عند إنشاء الـ validator، ثم ينفّذها. القواعد المتزامنة سريعة؛ القواعد غير المتزامنة (<code>MustAsync</code>) تفتح اتصالًا بقاعدة البيانات، لذا استخدمها فقط عند الضرورة وليس لكل حقل. تذكّر أن التحقق لا يعوّض عن قيود قاعدة البيانات: سباق التزامن يمكن أن يمرّ من Validator ثم يفشل عند الإدخال.</p>
        <p>شكل الخطأ مهم بقدر نجاح الطلب. <strong>ProblemDetails</strong> (RFC 9457) هو الصيغة القياسية: <code>type</code>, <code>title</code>, <code>status</code>, <code>detail</code>, <code>instance</code>. أما أخطاء التحقق فتأخذ <code>errors</code> كخريطة من اسم الحقل إلى قائمة رسائل. العميل يستطيع عرضها بجانب الحقول بدل نص عام.</p>
        <p>الفرق بين 400 و422: 400 يعني أن الطلب غير صالح بنيويًا أو فشل تحقق أساسي. 422 يعني أن الشكل صحيح لكن المحتوى لا يمكن معالجته منطقيًا. كثير من الفرق تستخدم 400 فقط للتحقق، وهذا مقبول إذا كان متسقًا وموثقًا. الأهم: لا تُرجع 200 مع <code>{ success: false }</code>.</p>
      `,
      tips: [
        {
          title: "لا تربط Entity أبدًا",
          body: "حتى لو كان الحقل «غير مهم»، قد يغيّره عميل خبيث (Over-posting). DTO الإدخال يجب أن يحتوي فقط ما تسمح به صراحة.",
        },
        {
          title: "افصل Create عن Update",
          body: "استخدام DTO واحد لكل العمليات يجعل حقولًا مطلوبة في الإنشاء اختيارية في التعديل. الفصل يمنع أخطاء منطقية ويكشفها مبكرًا.",
        },
        {
          title: "رسائل أخطاء للبشر وآخر للآلة",
          body: "أضف <code>errorCode</code> ثابتًا في الاستجابة للعميل الآلي، ورسالة عربية للعرض. لا تعتمد على نص الرسالة في منطق العميل.",
        },
        {
          title: "التحقق ليس تفويضًا",
          body: "التحقق من أن <code>CategoryId</code> موجود لا يعني أن المستخدم يملك حق استخدامه. تحقق الملكية في طبقة التفويض/الخدمة.",
        },
      ],
      quiz: [
        {
          q: "لماذا لا يجوز ربط Entity مباشرة بجسم الطلب؟",
          options: [
            "لأن Entity أبطأ.",
            "لأنه يسمح بتعديل حقول غير مسموحة (Over-posting) ويكشف تفاصيل داخلية.",
            "لأن JSON لا يدعم الكائنات.",
            "لأن Entity لا تحتوي خصائص.",
          ],
          answer: 1,
          explain:
            "العميل قد يعيّن Id أو IsDeleted أو حقولًا حساسة. DTO يحدّ السطح المسموح به صراحة.",
        },
        {
          q: "أي صيغة مناسبة لأخطاء التحقق القياسية؟",
          options: ["نص عادي", "HTML", "ProblemDetails مع errors", "200 مع success=false"],
          answer: 2,
          explain:
            "RFC 9457 (ProblemDetails) يوفر شكلًا موحدًا، وerrors تربط الرسائل بالحقول.",
        },
        {
          q: "متى يكون FluentValidation أفضل من DataAnnotations؟",
          options: [
            "عندما تكون القواعد بسيطة جدًا.",
            "عند الحاجة لقواعد مركّبة أو غير متزامنة أو رسائل مخصصة.",
            "عندما لا تريد أي تحقق.",
            "فقط مع Controllers.",
          ],
          answer: 1,
          explain:
            "FluentValidation يفصل القواعد ويسمح بالتسلسل والتحقق غير المتزامن والرسائل القابلة للترجمة.",
        },
      ],
      capstone: {
        title: "عقد منتجات Souq.NET",
        goal: "نستبدل الكائنات المؤقتة بعقد حقيقي: DTOs للإدخال والإخراج، تحقق كامل، واستجابة أخطاء موحّدة.",
        tasks: [
          "أنشئ <code>CreateProductRequest</code> و<code>UpdateProductRequest</code> و<code>ProductDto</code> كـ records.",
          "أضف <code>CreateProductValidator</code> بقواعد الاسم وSKU والسعر.",
          "سجّل الفاليديتورات في DI واستخدمها في نقاط النهاية.",
          "أعد <code>ValidationProblem</code> عند الفشل و<code>Created</code> عند النجاح.",
          "أرسل طلبًا فارغًا وتأكد من شكل الاستجابة وحقول الأخطاء.",
        ],
        code: {
          lang: "csharp",
          title: "تسجيل الفاليديتورات",
          code: `builder.Services.AddValidatorsFromAssemblyContaining<CreateProductValidator>();

app.MapPost("/api/v1/products", async (
    CreateProductRequest request,
    IValidator<CreateProductRequest> validator,
    IProductService service,
    CancellationToken ct) =>
{
    var validation = await validator.ValidateAsync(request, ct);
    if (!validation.IsValid)
        return Results.ValidationProblem(validation.ToDictionary());

    var dto = await service.CreateAsync(request, ct);
    return Results.Created($"/api/v1/products/{dto.Id}", dto);
});`,
        },
      },
    },
    {
      id: "errors-logging",
      title: "Global Exception Handling + Structured Logging",
      duration: 26,
      level: "متقدم",
      summary:
        "لا تملأ الكود بـ try/catch. عالج الأخطاء في حد واحد، وأعد ProblemDetails آمنًا، وسجّل ما يكفي للتشخيص دون تسريب الأسرار.",
      keywords: ["IExceptionHandler", "ProblemDetails", "Serilog", "structured logging", "ILogger", "correlation"],
      objectives: [
        "تعالج الاستثناءات مركزيًا عبر IExceptionHandler.",
        "تفرّق بين خطأ متوقع (4xx) وخطأ نظام (5xx).",
        "تكتب سجلات منظمة قابلة للبحث بدل نصوص ملصوقة.",
        "تحمي البيانات الحساسة من التسجيل.",
      ],
      concept: `
        <p>الاستثناء في .NET ليس فشلًا دائمًا؛ هو إشارة. بعض الاستثناءات متوقعة (منتج غير موجود، مخزون غير كافٍ)، وبعضها خلل (NullReference، فشل اتصال قاعدة البيانات). الخلط بينهما ينتج API يُرجع 500 لكل شيء، أو يسجّل أخطاء متوقعة ككوارث.</p>
        <h3>المعالج المركزي</h3>
        <p>منذ .NET 8 يوجد <code>IExceptionHandler</code>. تسجّله بـ <code>AddExceptionHandler&lt;T&gt;()</code> وتفعّل <code>UseExceptionHandler()</code>. الإطار يستدعي <code>TryHandleAsync</code> عند أي استثناء غير معالَج. إن أعدت <code>true</code>، فقد تولّيت الاستجابة؛ وإن أعدت <code>false</code>، يجرّب المعالج التالي ثم الافتراضي.</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>public sealed class GlobalExceptionHandler(
    IProblemDetailsService problemDetails,
    ILogger&lt;GlobalExceptionHandler&gt; logger) : IExceptionHandler
{
    public async ValueTask&lt;bool&gt; TryHandleAsync(
        HttpContext context, Exception exception, CancellationToken ct)
    {
        var (status, title) = exception switch
        {
            NotFoundException =&gt; (404, "المورد غير موجود"),
            ConflictException =&gt; (409, "تعارض في البيانات"),
            _ =&gt; (500, "حدث خطأ غير متوقع")
        };

        logger.LogError(exception, "Unhandled exception for {Path}", context.Request.Path);

        context.Response.StatusCode = status;
        return await problemDetails.TryWriteAsync(new ProblemDetailsContext
        {
            HttpContext = context,
            ProblemDetails = { Status = status, Title = title }
        });
    }
}</code></pre>
        <h3>السجلات المنظمة</h3>
        <p><code>logger.LogInformation(\"User \" + id + \" logged in\")</code> ينتج نصًا لا يمكن الاستعلام عنه. القوالب المنظمة:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>logger.LogInformation("User {UserId} logged in from {Ip}", userId, ip);</code></pre>
        <p>هنا <code>UserId</code> و<code>Ip</code> خصائص (Properties) في الحدث، يمكن البحث عنها في Seq أو Elastic أو Loki. Serilog يبني على هذا المفهوم ويضيف Sinks وEnrichers وRequest Logging.</p>
        <p>قاعدة إنتاجية: سجّل <strong>مرة واحدة عند الحد</strong>. لا تسجّل الخطأ في الخدمة ثم في الـ endpoint ثم في المعالج. هذا يضخّم السجلات ويصعّب معرفة السبب الحقيقي. وكل سجل يجب أن يجيب: ماذا حدث، لأي طلب، وبأي معرف تتبّع؟</p>
      `,
      walkthrough: [
        {
          title: "سجّل Problem Details",
          code: `builder.Services.AddProblemDetails();
app.UseExceptionHandler();`,
          lang: "csharp",
          body: `<p><code>AddProblemDetails</code> يسجل خدمة إنشاء استجابات الأخطاء القياسية. <code>UseExceptionHandler</code> يضيف middleware يلتقط الاستثناءات غير المعالجة ويحوّلها إلى استجابة بدل أن يرى العميل stack trace. ضعه قرب بداية الأنبوب ليغلّف بقية الـ middleware. في التطوير قد تظهر صفحة تفصيلية، لكن الإنتاج يجب أن يعيد رسالة آمنة.</p>`
        },
        {
          title: "استثناء يعبّر عن حالة العمل",
          code: `public sealed class ProductNotFoundException : Exception
{
    public ProductNotFoundException(Guid id)
        : base($"Product {id} was not found.")
        => ProductId = id;

    public Guid ProductId { get; }
}`,
          lang: "csharp",
          body: `<p>استثناء مخصص يجعل النية واضحة في طبقة الخدمة، بدل إرجاع null في كل مكان. يحمل <code>ProductId</code> للاستخدام في السجل والاستجابة. لا تضع رسالة داخلية حساسة في <code>Message</code> ثم تعيدها للعميل كما هي. الاستثناء للتحكم في التدفق الاستثنائي، وليس لكل نتيجة متوقعة مثل فشل تحقق.</p>`
        },
        {
          title: "حوّل الاستثناء إلى 404",
          code: `public sealed class ProductNotFoundHandler
    : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext context,
        Exception exception,
        CancellationToken ct)
    {
        if (exception is not ProductNotFoundException ex)
            return false;

        context.Response.StatusCode = StatusCodes.Status404NotFound;
        await context.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Title = "Product not found",
            Status = StatusCodes.Status404NotFound,
            Detail = "The requested product does not exist."
        }, ct);
        return true;
    }
}`,
          lang: "csharp",
          body: `<p>إرجاع <code>false</code> يعني «لست مسؤولًا عن هذا الاستثناء» فينتقل إلى المعالج التالي. إرجاع <code>true</code> يعني أنك كتبت الاستجابة. استخدم <code>WriteAsJsonAsync</code> مع <code>ct</code>. لا تضع رسالة الاستثناء الخام في <code>Detail</code>؛ قد تكشف معرفات أو تفاصيل داخلية. سجّل التفاصيل في الخادم واربطها بـtraceId.</p>`
        },
        {
          title: "سجّل المعالج",
          code: `builder.Services.AddExceptionHandler<
    ProductNotFoundHandler>();
builder.Services.AddProblemDetails();
app.UseExceptionHandler();`,
          lang: "csharp",
          body: `<p>يجب تسجيل المعالج في DI قبل <code>UseExceptionHandler</code>. يمكن تسجيل عدة معالجات؛ الإطار يجربها بالترتيب حتى واحد يعيد <code>true</code>. إن لم يعالج أي منها، ينتج المعالج الافتراضي 500. لا تنسَ <code>AddProblemDetails</code> وإلا قد لا تجد خدمة إنشاء الاستجابة القياسية.</p>`
        },
        {
          title: "سجّل حقولًا لا نصوصًا",
          code: `logger.LogWarning(
    "Product {ProductId} not found. TraceId {TraceId}",
    id,
    context.TraceIdentifier);`,
          lang: "csharp",
          body: `<p>استخدم <strong>structured logging</strong>: أسماء الحقول بين الأقواس تسمح بالبحث والتصفية. لا تستخدم string interpolation لبناء الرسالة؛ يفقد السجل بنيته. <code>TraceId</code> يربط السجل بالطلب والعميل. لا تسجّل كلمات مرور أو توكنات أو بيانات شخصية. مستوى <code>Warning</code> مناسب لخطأ عميل متوقع مثل 404.</p>`
        },
        {
          title: "اربط التتبع بـActivity",
          code: `var traceId = Activity.Current?.TraceId.ToString()
    ?? context.TraceIdentifier;
context.Response.Headers["X-Trace-Id"] = traceId;`,
          lang: "csharp",
          body: `<p><code>Activity.Current</code> يمثل span في OpenTelemetry. <code>TraceId</code> يربط الطلب بكل الخدمات المشاركة. <code>TraceIdentifier</code> معرف ASP.NET Core المحلي. أعد معرفًا واحدًا متسقًا في الترويسة وProblem Details والسجلات. لا تعرض معرفات داخلية أخرى أو أسماء خوادم.</p>`
        },
        {
          title: "لا تسجّل 400 كخطأ خادم",
          code: `if (statusCode >= 500)
    logger.LogError("Request failed with {StatusCode}", statusCode);
else if (statusCode >= 400)
    logger.LogWarning("Client error {StatusCode}", statusCode);`,
          lang: "csharp",
          body: `<p>كل 400 ليس حادثًا يستدعي تنبيهًا. السجلات المليئة بأخطاء التحقق المتوقعة تخفي المشاكل الحقيقية. استخدم <code>Warning</code> أو <code>Information</code> لأخطاء العميل، و<code>Error</code> لـ5xx. أضف Sampling وحدودًا للسجلات. راقب المعدل والنوع، لا العدد الخام فقط.</p>`
        },
        {
          title: "لا تكتب استجابة بعد بدئها",
          code: `if (context.Response.HasStarted)
{
    logger.LogError("Response already started");
    return true;
}

context.Response.StatusCode = StatusCodes.Status500InternalServerError;`,
          lang: "csharp",
          body: `<p>إذا بدأت الاستجابة، لا يمكنك تغيير الحالة أو الترويسات. محاولة الكتابة قد ترمي استثناءً داخل معالج الاستثناء نفسه. افحص <code>HasStarted</code> وسجّل الحالة. الأفضل أن تترك المعالج المركزي يكتب الاستجابة قبل أن يبدأ أي middleware بإرسال الجسم. هذا سبب إضافي لترتيب معالجة الأخطاء أولًا.</p>`
        },
        {
          title: "افصل سلوك التطوير عن الإنتاج",
          code: `if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler();
    app.UseHsts();
}`,
          lang: "csharp",
          body: `<p>صفحة المطور تعرض stack trace وتفاصيل الطلب؛ لا تظهرها للعامة أبدًا. في الإنتاج استخدم معالج Problem Details وHSTS. لا تعتمد على <code>ASPNETCORE_ENVIRONMENT</code> فقط إن كان يمكن تغييره بالخطأ؛ تحقق من إعداد النشر. اختبر استجابة 500 في بيئة تشبه الإنتاج.</p>`
        }
      ],
      compare: {
        intro: `<p>الطريقة القديمة تكرّر try/catch وترجع نصوصًا. الطريقة الحديثة تعالج في طبقة واحدة وتُرجع عقدًا ثابتًا، مع سجلات قابلة للاستعلام.</p>`,
        before: {
          label: "try/catch في كل endpoint",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapGet("/api/products/{id}", async (int id, SouqDbContext db) =>
{
    try
    {
        var product = await db.Products.FindAsync(id);
        if (product is null) return Results.NotFound();
        return Results.Ok(product);
    }
    catch (Exception ex)
    {
        Console.WriteLine("ERROR: " + ex.Message);
        return Results.Problem("Something went wrong");
    }
});`,
          points: [
            "نفس الكود في كل نقطة نهاية.",
            "رسالة غير مفيدة للعميل ولا للمشغّل.",
            "تسريب تفاصيل داخلية في السجل/الاستجابة.",
          ],
        },
        after: {
          label: "معالج مركزي + Serilog",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services.AddProblemDetails();
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();

builder.Host.UseSerilog((context, services, configuration) =>
{
    configuration
        .ReadFrom.Configuration(context.Configuration)
        .ReadFrom.Services(services)
        .Enrich.FromLogContext()
        .WriteTo.Console(new CompactJsonFormatter());
});

var app = builder.Build();

app.UseExceptionHandler();
app.UseSerilogRequestLogging(options =>
{
    options.MessageTemplate =
        "HTTP {RequestMethod} {RequestPath} responded {StatusCode} in {Elapsed:0.0000} ms";
});

app.MapGet("/api/products/{id:int}", async (
    int id, IProductService service, CancellationToken ct) =>
{
    var product = await service.GetAsync(id, ct);
    return product is null ? Results.NotFound() : Results.Ok(product);
});`,
          points: [
            "منطق الأخطاء في مكان واحد.",
            "سجلات JSON منظمة مع مدة الطلب.",
            "نقاط النهاية تبقى نظيفة.",
          ],
        },
        verdict: `<p>المكسب ليس جماليًا: عندما يشتكي عميل من خطأ، تبحث عن <code>TraceId</code> أو <code>CorrelationId</code> في السجلات فترى القصة كاملة. بدون سجلات منظمة، ستبحث في نصوص حرة بين ملايين الأسطر.</p>`,
      },
      internals: `
        <p>ترتيب معالجة الاستثناء: <code>UseExceptionHandler</code> يجب أن يكون أول Middleware تقريبًا، حتى يغلّف كل ما بعده. عند حدوث استثناء، تبدأ رحلة الصعود في السلسلة حتى تصل إلى طبقة تلتقطه. إن لم يوجد، يُغلق الاتصال أو يُرجع 500 افتراضي.</p>
        <p>يستخدم المعالج <code>IProblemDetailsService</code> لكتابة الاستجابة، ويحترم <code>ProblemDetailsOptions</code> مثل <code>CustomizeProblemDetails</code>. في الإنتاج لا تُرجع <code>exception.StackTrace</code> أو <code>Message</code> الخام؛ قد تحتوي مسارات ملفات أو أسماء جداول أو بيانات عميل.</p>
        <p><strong>Serilog</strong> ليس بديلًا عن ILogger؛ هو مزوّد خلف الواجهة. عند استخدام <code>builder.Host.UseSerilog</code> يصبح الـ Logger المصنع هو Serilog، وتبقى <code>ILogger&lt;T&gt;</code> كما هي في الكود. هذا يسمح بتغيير الـ Sink دون لمس الخدمات.</p>
        <p>الـ Sinks غير المتزامنة (مثل HTTP أو Elasticsearch) تستخدم قنوات داخلية وذاكرة محدودة. إن امتلأت، قد تُسقِط الأحداث أو تحجب التطبيق حسب الإعداد. راقب <code>Serilog.Debugging.SelfLog</code> عند الفقدان، واضبط <code>queueLimit</code> و<code>batchPostingLimit</code> بوعي.</p>
      `,
      internalsTable: {
        head: ["الحالة", "Status", "هل تُسجَّل كخطأ؟"],
        rows: [
          ["فشل تحقق", "400", "لا، Information/Warning فقط"],
          ["غير مصرّح", "401/403", "لا، قد تُسجَّل كأمان"],
          ["مورد غير موجود", "404", "لا"],
          ["تعارض عمل", "409/422", "Warning, ليس Error"],
          ["استثناء غير متوقع", "500", "Error مع StackTrace داخليًا فقط"],
        ],
      },
      tips: [
        {
          title: "لا تسجّل PII أو أسرار",
          body: "لا تسجّل كلمات المرور أو التوكنات أو أرقام البطاقات. استخدم Destructurama أو سياسة تقنيع صارمة. السجل نفسه هدف للهجوم.",
        },
        {
          title: "استخدم LoggerMessage المولّد",
          body: "في المسارات الساخنة، <code>[LoggerMessage]</code> يقلل التخصيص والتحليل. السجلات ليست مجانية، خصوصًا عند مستوى Information لكل طلب.",
        },
        {
          title: "ميّز الأخطاء المتوقعة",
          body: "أنشئ استثناءات مجال مثل <code>NotFoundException</code> و<code>ConflictException</code>، وحوّلها إلى 404/409. لا ترمِ Exception عامًا لكل شيء.",
        },
        {
          title: "TraceId في كل استجابة",
          body: "أعد <code>traceId</code> في ProblemDetails (خاصية extensions) واطلبه من العميل عند الإبلاغ. هذا يقلّص زمن التشخيص من ساعات إلى دقائق.",
        },
      ],
      quiz: [
        {
          q: "ما وظيفة IExceptionHandler؟",
          options: [
            "يُسجّل كل طلب ناجح.",
            "يعالج الاستثناءات غير المعالَجة مركزيًا ويكتب استجابة موحّدة.",
            "يُعيد تشغيل التطبيق.",
            "يمنع كل الاستثناءات.",
          ],
          answer: 1,
          explain:
            "هو نقطة التقاط مركزية تُستدعى من UseExceptionHandler، وتعيد true إذا كتبت الاستجابة.",
        },
        {
          q: "أي صيغة سجل أفضل للبحث؟",
          options: [
            "logger.LogInformation(\"user \" + id + \" logged in\")",
            "logger.LogInformation(\"User {UserId} logged in\", id)",
            "Console.WriteLine($\"user {id}\")",
            "File.AppendAllText(\"log.txt\", id)",
          ],
          answer: 1,
          explain:
            "القوالب المنظمة تحوّل UserId إلى خاصية قابلة للاستعلام، بدل نص ملصوق.",
        },
        {
          q: "ماذا تُرجع للعميل عند استثناء غير متوقع؟",
          options: [
            "Stack trace كامل.",
            "رسالة عامة مع ProblemDetails وtraceId، والتفاصيل في السجل الداخلي.",
            "200 لتجنب إظهار الخطأ.",
            "اسم الجدول والاستعلام.",
          ],
          answer: 1,
          explain:
            "لا تُسرّب تفاصيل داخلية. ProblemDetails مع traceId يسمح بالدعم دون كشف البنية الداخلية.",
        },
      ],
      capstone: {
        title: "معالج أخطاء وسجلات Souq.NET",
        goal: "نجعل كل خطأ في المشروع يخرج بعقد واحد، وكل طلب له سجل منظم يمكن تتبّعه.",
        tasks: [
          "أضف <code>AddProblemDetails()</code> و<code>AddExceptionHandler&lt;GlobalExceptionHandler&gt;()</code>.",
          "أنشئ استثناءات <code>NotFoundException</code> و<code>ConflictException</code> وحوّلها إلى 404/409.",
          "اضبط Serilog مع Console JSON وRequest Logging.",
          "أضف <code>traceId</code> إلى استجابة الأخطاء.",
          "أطلق خطأً متعمدًا وتأكد من عدم ظهور StackTrace للعميل ومن وجوده في السجل.",
        ],
        code: {
          lang: "csharp",
          title: "استثناءات المجال",
          code: `public sealed class NotFoundException(string message) : Exception(message);
public sealed class ConflictException(string message) : Exception(message);

// في المعالج
var (status, title) = exception switch
{
    NotFoundException => (StatusCodes.Status404NotFound, "المورد غير موجود"),
    ConflictException => (StatusCodes.Status409Conflict, "تعارض في البيانات"),
    _ => (StatusCodes.Status500InternalServerError, "خطأ غير متوقع")
};`,
        },
      },
    },
    {
      id: "api-evolution",
      title: "تطوير API دون كسر العملاء",
      duration: 30,
      level: "متقدم",
      summary:
        "الـ API عقد طويل العمر. سنتعلم كيف نضيف ونحسّن دون كسر التطبيقات القديمة، ومتى نحتاج إصدارًا جديدًا، وكيف نخطط لإيقاف نسخة بأمان.",
      keywords: ["API versioning", "backward compatibility", "deprecation", "Sunset", "OpenAPI", "contract testing", "cursor pagination", "idempotency"],
      objectives: [
        "تميّز التغيير المتوافق من التغيير الكاسر.",
        "تخطط لإصدارات API وإيقاف النسخ القديمة.",
        "تثبت عقد الاستجابة والخطأ باختبارات تعاقدية.",
        "تصمم ترقيمًا وفلترة قابلة للتطور.",
        "تستخدم Idempotency-Key للطلبات القابلة للتكرار."
      ],
      concept: `
        <p>الـ API ليس الكود الذي تكتبه اليوم؛ هو عقد يعتمد عليه تطبيق جوال ولوحة إدارة وعميل خارجي. عندما تغيّر اسم حقل أو معنى استجابة، قد لا يظهر الخطأ عندك، بل عند عميل لم تحدّثه. لذلك التعامل مع الـ API كعقد مُصدَّر أهم من سرعة إضافة الحقول.</p>
        <h3>ما هو التغيير المتوافق؟</h3>
        <p>إضافة حقل اختياري، إضافة endpoint جديد، أو إضافة قيمة enum جديدة <em>قد</em> تكون متوافقة إذا كان العميل يتجاهل ما لا يعرفه. أما حذف حقل، إعادة تسميته، تغيير نوعه، تغيير معناه، أو جعل حقل اختياري إلزاميًا فهي تغييرات كاسرة. حتى تشديد التحقق أو تغيير رمز الخطأ قد يكسر عميلًا يعتمد عليه. القاعدة: لا تغيّر دلالة شيء موجود؛ أضف بديلًا واترك القديم لفترة انتقالية.</p>
        <h3>الإصدارات ليست لكل تغيير</h3>
        <p>لا تنشئ <code>v2</code> لمجرد إضافة حقل. الإصدار الجديد يعني عقدًا غير متوافق يجب صيانته بالتوازي. استخدم إصدارًا رئيسيًا عندما تحتاج تغييرًا كاسرًا حقًا، مثل إعادة تصميم الموارد أو نموذج الأخطاء. الإصدار في المسار مثل <code>/api/v1/products</code> واضح للعملاء والبوابات، لكنه يضاعف الصيانة. الإصدار في header أو media type أنظف نظريًا لكنه أصعب في الاختبار والدعم اليومي.</p>
        <h3>الإيقاف ليس حذفًا مفاجئًا</h3>
        <p>قبل إيقاف نسخة: أعلن التاريخ، أضف <code>Deprecation</code> و<code>Sunset</code> و<code>Link</code> إلى البديل، وحدّث الوثائق ورسائل الخطأ. راقب من لا يزال يستخدمها. لا تحذف endpoint في نفس يوم إصدار البديل. العميل يحتاج وقتًا للنشر، وأنت تحتاج بيانات لتعرف من تأثر. الإيقاف عملية تواصل وهندسة، لا زر في الكود.</p>
        <h3>العقد يشمل الأخطاء والترقيم</h3>
        <p>شكل <code>ProblemDetails</code>، رموز الحالة، معنى <code>nextCursor</code>، وحدود <code>pageSize</code> كلها جزء من العقد. إذا غيّرت ترتيب النتائج أو أضفت فلترًا يغيّر النتائج الافتراضية، فقد تكسر توقعات العميل. ثبّت ترتيبًا فريدًا للترقيم، ووثّق حدود الفلاتر والفرز، وارفض القيم غير المعروفة بوضوح بدل تجاهلها بصمت.</p>
        <h3>اختبر العقد لا التنفيذ فقط</h3>
        <p>اختبار الوحدة لا يكتشف أنك حذفت حقلًا من JSON. استخدم اختبارات تعاقدية تقارن OpenAPI أو لقطات الاستجابة، واختبر العميل الحقيقي إن أمكن. عند إضافة حقل، تأكد أن العميل القديم يتجاهله. عند تغيير نوع، افترض أن كل عميل سينكسر حتى تثبت العكس. أدرج فحص العقد في CI قبل النشر.</p>
        <h3>إعادة المحاولة جزء من التصميم</h3>
        <p>الشبكة قد تعيد إرسال POST دون أن تعرف هل نجح. <code>Idempotency-Key</code> يسمح للخادم بإرجاع نتيجة الطلب الأول بدل إنشاء طلب جديد. هذا مكمل للمعاملة، لا بديل عنها. صمّم مفاتيح فريدة، خزّن نتيجة الاستجابة، وحدد مدة الاحتفاظ. العميل الذي يعيد المحاولة يجب أن يحصل على نفس النتيجة، لا على طلبين.</p>
      `,
      walkthrough: [
        {
          title: "اعزل عقد الاستجابة عن الكيان",
          code: `public sealed record ProductV1(\n    Guid Id,\n    string Name,\n    decimal Price);`,
          lang: "csharp",
          body: `<p><code>ProductV1</code> هو العقد العام، وليس كيان EF Core. لا يُسرّب الحقول الداخلية ولا يتغير تلقائيًا عند تعديل جدول. حتى لو أعدت تسمية عمود في قاعدة البيانات، يبقى JSON كما هو. اجعل الـ DTO في طبقة API أو Contracts، ولا تعِد <code>Product</code> مباشرة.</p>`
        },
        {
          title: "أضف حقلًا اختياريًا",
          code: `public sealed record ProductV1(\n    Guid Id,\n    string Name,\n    decimal Price,\n    string? ImageUrl = null);`,
          lang: "csharp",
          body: `<p>إضافة <code>ImageUrl</code> في النهاية بقيمة افتراضية <code>null</code> لا تكسر العميل القديم؛ سيحصل على null أو سيتجاهل الحقل. لا تجعله إلزاميًا في نفس التغيير. إن كان الحقل مطلوبًا للعملاء الجدد، أضفه كاختياري أولًا، ثم وثّق متى سيصبح إلزاميًا بإصدار جديد.</p>`
        },
        {
          title: "احذر تغيير معنى الحقل",
          code: `// v1: Price = السعر قبل الضريبة\n// v2: Price = السعر النهائي شامل الضريبة\n// هذا تغيير كاسر حتى لو بقي الاسم والنوع.`,
          lang: "csharp",
          body: `<p>العميل لا يرى SQL ولا نواياك؛ يرى رقمًا. تغيير <code>Price</code> من سعر قبل الضريبة إلى سعر شامل يغيّر كل حساب لديه. أضف <code>PriceExcludingTax</code> و<code>PriceIncludingTax</code> بوضوح، أو أنشئ v2. الوضوح في الأسماء أرخص من دعم حوادث بسبب سوء فهم.</p>`
        },
        {
          title: "ثبّت الإصدار في المسار",
          code: `var v1 = app.MapGroup("/api/v1/products");\nvar v2 = app.MapGroup("/api/v2/products");\n\nv1.MapGet("/", GetProductsV1);\nv2.MapGet("/", GetProductsV2);`,
          lang: "csharp",
          body: `<p>المجموعات تجعل الإصدار مرئيًا في الـ URL. يمكنك استخدام مكتبة <code>Asp.Versioning</code> لاحقًا، لكن الفكرة واحدة: كل إصدار له endpoints وعقود مستقلة. لا تضع منطق الأعمال مرتين؛ اجعل الطبقة الداخلية مشتركة، والاختلاف في التحويل والعقد.</p>`
        },
        {
          title: "أعلن الإيقاف في الاستجابة",
          code: `app.Use(async (context, next) =>\n{\n    context.Response.OnStarting(() =>\n    {\n        context.Response.Headers.Append(\n            "Deprecation", "@1767225600");\n        context.Response.Headers.Append(\n            "Sunset", "Thu, 01 Jan 2026 00:00:00 GMT");\n        context.Response.Headers.Append(\n            "Link", "</api/v2/products>; rel=\\"successor-version\\"");\n        return Task.CompletedTask;\n    });\n    await next();\n});`,
          lang: "csharp",
          body: `<p><code>Deprecation</code> يعلن أن النسخة ستُوقف، و<code>Sunset</code> يحدد الموعد النهائي، و<code>Link</code> يشير إلى البديل. لا تعتمد على بريد إلكتروني فقط. ضع الإعلان في الوثائق والاستجابة وسجل التغييرات. استخدم تنسيقات HTTP الصحيحة واختبر التواريخ؛ تاريخ خاطئ أسوأ من عدم وجود إعلان.</p>`
        },
        {
          title: "خطة إيقاف قابلة للقياس",
          code: `1. أعلن v2 ووثّق الفروق.\n2. راقب عدد طلبات v1 حسب العميل.\n3. أرسل تنبيهات قبل Sunset بثلاثة أشهر.\n4. أوقف الكتابة في v1 أولًا.\n5. أوقف القراءة ثم احذف الكود بعد انتهاء المهلة.`,
          lang: "text",
          body: `<p>الإيقاف على مراحل يقلل المخاطرة. ابدأ بمنع العمليات الجديدة، ثم القراءة، ثم الحذف. راقب استخدام v1 بعد كل مرحلة. لا تحذف الكود في نفس نشر v2؛ قد تحتاج rollback. احتفظ بفترة سماح مكتوبة ومعلنة.</p>`
        },
        {
          title: "ترقيم cursor ثابت",
          code: `public sealed record ProductPage(\n    IReadOnlyList<ProductV1> Items,\n    DateTimeOffset? NextCreatedAt,\n    Guid? NextId);`,
          lang: "csharp",
          body: `<p>بدل <code>page</code> و<code>offset</code> اللذين يتباطآن في الصفحات العميقة، استخدم cursor من آخر عنصر. أعد <code>NextCreatedAt</code> و<code>NextId</code> كـopaque للمستخدم، أو غلّفهما في string موقّع. لا تكشف تفاصيل داخلية أكثر من اللازم، ولا تسمح للعميل بتزوير cursor يغيّر الاستعلام.</p>`
        },
        {
          title: "فلترة وفرز بمسموح فقط",
          code: `var sort = request.Sort switch\n{\n    "price" => (IQueryable<Product>) q.OrderBy(p => p.Price),\n    "name" => q.OrderBy(p => p.Name).ThenBy(p => p.Id),\n    _ => q.OrderByDescending(p => p.CreatedAt).ThenBy(p => p.Id)\n};\n\nvar take = Math.Clamp(request.PageSize, 1, 100);\nvar items = await sort.Take(take + 1).ToListAsync(ct);`,
          lang: "csharp",
          body: `<p>لا تمرّر اسم عمود من العميل إلى SQL. استخدم قائمة بيضاء من مفاتيح الفرز. <code>Math.Clamp</code> يمنع pageSize ضخمًا. نجلب <code>take + 1</code> لنعرف هل توجد صفحة تالية دون استعلام Count إضافي. أضف <code>ThenBy(Id)</code> لضمان ترتيب فريد.</p>`
        },
        {
          title: "اختبر العقد في CI",
          code: `var openApi = await client.GetStringAsync("/openapi/v1.json");\nawait Verifier.Verify(openApi);`,
          lang: "csharp",
          body: `<p>اختبار لقطة OpenAPI يكشف حذف حقل أو تغيير نوعه قبل النشر. استخدم مكتبة snapshot مناسبة أو قارن ملف OpenAPI المولّد بملف مرجعي. عند التغيير المتعمد، راجع الفرق واعتمده في PR. لا تجعل الاختبار يتجاوز نفسه تلقائيًا؛ الموافقة يجب أن تكون واعية.</p>`
        },
        {
          title: "Idempotency-Key للطلبات الحساسة",
          code: `POST /api/v1/orders\nIdempotency-Key: 8f14e45f-ea2b-4b7c-9f3a-2f0c1d6e9a11\nContent-Type: application/json`,
          lang: "http",
          body: `<p>الخادم يخزن المفتاح مع نتيجة الطلب. إن وصل نفس المفتاح مرة أخرى، يعيد النتيجة المخزنة بدل إنشاء طلب جديد. المفتاح يجب أن يكون فريدًا لكل عملية عميل، لا ثابتًا لكل المستخدمين. اربطه بالمستخدم والمسار، وحدد مدة صلاحية. هذا يحمي من إعادة المحاولة بعد timeout، لا من إساءة استخدام متعمدة فقط.</p>`
        }
      ],
      compare: {
        intro: `<p>تغييران يبدوان صغيرين، لكن أحدهما يحافظ على العقد والآخر يكسره.</p>`,
        before: {
          label: "تغيير كاسر",
          lang: "csharp",
          title: "قبل",
          code: `public sealed record ProductDto(\n    Guid Id,\n    string Title,   // كان Name\n    decimal Price); // أصبح شامل الضريبة`,
          points: [
            "حذف/إعادة تسمية Name يكسر العملاء.",
            "تغيير معنى Price يفسد الحسابات.",
            "لا إصدار جديد ولا فترة انتقال.",
            "اختبار الوحدة قد يمر رغم الكسر."
          ]
        },
        after: {
          label: "تغيير متوافق",
          lang: "csharp",
          title: "بعد",
          code: `public sealed record ProductV1(\n    Guid Id,\n    string Name,\n    decimal Price,\n    string? Title = null);\n\npublic sealed record ProductV2(\n    Guid Id,\n    string Name,\n    decimal PriceExcludingTax,\n    decimal PriceIncludingTax);`,
          points: [
            "Name بقي كما هو.",
            "Title أضيف كحقل اختياري.",
            "v2 يعبّر عن السعرين بوضوح.",
            "v1 يبقى مدعومًا حتى Sunset."
          ]
        },
        verdict: `<p>التوافق ليس جمودًا؛ هو إضافة بديل واضح مع الحفاظ على القديم. الإصدار الجديد مخصص للتغيير الكاسر، لا لكل تحسين.</p>`
      },
      internals: `
        <p>ASP.NET Core يسلسل DTO إلى JSON باستخدام <code>System.Text.Json</code>. افتراضيًا يتجاهل الحقول غير المعروفة عند القراءة، لكن لا تعتمد على ذلك كضمان توافق. اسم الخاصية في JSON هو العقد، و<code>JsonPropertyName</code> يثبته حتى لو أعدت تسمية خاصية C#. تغيير الاسم في C# دون تثبيت JSON قد يغيّر العقد بصمت.</p>
        <p>عند إضافة إصدار في المسار، يوجّه routing الطلب إلى مجموعة endpoints مختلفة. المنطق الداخلي يمكن أن يكون خدمة واحدة، لكن التحويل إلى DTO مختلف. لا تكرر قواعد العمل في v1 وv2؛ كرر العقد فقط. هذا يقلل احتمال أن تصلح خطأً في نسخة وتنساه في الأخرى.</p>
        <h3>OpenAPI كمرآة</h3>
        <p>OpenAPI يوثّق المسارات والمخططات، لكنه لا يمنع تغييرًا كاسرًا تلقائيًا. استخدمه في اختبار تعاقدي: توليد الملف ومقارنته بنسخة مرجعية. أي فرق يحتاج مراجعة. وثّق أمثلة الاستجابة والأخطاء، لا الأنواع فقط. العميل يحتاج معرفة شكل <code>ProblemDetails</code> وحقول الترقيم.</p>
        <h3>الترقيم والاتساق</h3>
        <p>Offset pagination يعتمد على ترتيب ثابت، وإلا تتكرر الصفوف أو تختفي. Cursor pagination يستخدم آخر قيمة مرتّبة، ويحتاج فهرسًا يطابق ترتيب الاستعلام. لا تخلط بين cursor وoffset في نفس endpoint. أعد حدًا أقصى واضحًا، وتعامل مع cursor غير الصالح كـ400 لا كخطأ 500.</p>
        <h3>الإيقاف والتوافق</h3>
        <p>HTTP يوفّر <code>Deprecation</code> و<code>Sunset</code> و<code>Link</code>، لكنه لا يضمن أن العميل يقرؤها. اجمع بين الرؤوس والوثائق والمراقبة. حذف الإصدار القديم يحتاج قرارًا مبنيًا على بيانات استخدام، لا على تاريخ فقط. خطط لـrollback إن اكتشفت عميلًا متأخرًا.</p>
      `,
      internalsTable: {
        head: ["التغيير", "متوافق؟", "الإجراء"],
        rows: [
          ["إضافة حقل اختياري", "غالبًا نعم", "أضفه في النهاية بوضوح"],
          ["حذف أو إعادة تسمية حقل", "لا", "إصدار رئيسي + فترة انتقال"],
          ["تغيير نوع الحقل", "لا", "حقل جديد أو إصدار جديد"],
          ["تغيير معنى الحقل", "لا", "أسماء صريحة أو إصدار جديد"],
          ["إضافة قيمة enum", "قد لا", "وثّق التعامل مع القيم غير المعروفة"],
          ["تشديد التحقق", "قد لا", "إعلان مسبق أو إصدار جديد"]
        ]
      },
      tips: [
        {
          title: "لا تصدّر الكيان",
          body: "استخدم DTOs ثابتة. الكيان يتغير مع قاعدة البيانات، والـ API يجب أن يتغير بقرار واعٍ."
        },
        {
          title: "أضف ولا تكسر",
          body: "الحقل الجديد اختياري أولًا. لا تغيّر اسمًا أو معنى حقل قائم. إن اضطررت، فالإصدار الجديد هو الحل."
        },
        {
          title: "خطط للإيقاف",
          body: "أعلن Deprecation وSunset، راقب الاستخدام، وامنح مهلة واقعية. لا تحذف نسخة لأنك انتهيت منها."
        },
        {
          title: "اختبر العقد",
          body: "لقطة OpenAPI واختبارات استجابة تكشف الحذف أو تغيير النوع. اجعل مراجعة الفرق جزءًا من الـ PR."
        }
      ],
      quiz: [
        {
          q: "أي تغيير التالي كاسر للعقد؟",
          options: [
            "إضافة حقل اختياري في نهاية الاستجابة.",
            "إضافة endpoint جديد.",
            "إعادة تسمية حقل JSON موجود أو حذفه.",
            "إضافة قيمة جديدة إلى enum مع توثيقها."
          ],
          answer: 2,
          explain: "إعادة التسمية أو الحذف تغيّر عقدًا يعتمد عليه العميل. الإضافات قد تكون متوافقة، لكن يجب اختبارها وتوثيقها."
        },
        {
          q: "متى ننشئ إصدار API جديد؟",
          options: [
            "عند كل إضافة حقل.",
            "عند تغيير كاسر لا يمكن الحفاظ فيه على التوافق.",
            "عند كل إصلاح خطأ.",
            "عند تغيير اسم جدول قاعدة البيانات."
          ],
          answer: 1,
          explain: "الإصدار الجديد مخصص للتغيير غير المتوافق الذي يحتاج عقدًا مستقلًا. التغييرات المتوافقة تُضاف دون إصدار جديد."
        },
        {
          q: "ما فائدة Idempotency-Key؟",
          options: [
            "تسريع الاستعلامات.",
            "منع إنشاء طلب مكرر عند إعادة المحاولة.",
            "تشفير الاستجابة.",
            "إلغاء الحاجة إلى المصادقة."
          ],
          answer: 1,
          explain: "المفتاح يسمح للخادم بإعادة نتيجة الطلب الأول عند تكرار نفس العملية، فيحمي من التكرار بعد timeout أو إعادة محاولة."
        }
      ],
      capstone: {
        title: "تطوير Souq API بأمان",
        goal: "أضف تحسينات متوافقة إلى API، وثبّت العقد، وجهّز خطة إيقاف للنسخة القديمة.",
        tasks: [
          "أضف <code>ImageUrl</code> كحقل اختياري إلى <code>ProductV1</code> دون تغيير حقول موجودة.",
          "أنشئ <code>ProductV2</code> يوضح السعر قبل/بعد الضريبة، واربطه بمسار <code>/api/v2/products</code>.",
          "أضف رؤوس <code>Deprecation</code> و<code>Sunset</code> و<code>Link</code> إلى v1 في بيئة الاختبار.",
          "أضف اختبار لقطة OpenAPI يفشل عند حذف حقل أو تغيير نوعه.",
          "أضف دعم <code>Idempotency-Key</code> لإنشاء الطلب واختبر إعادة الإرسال."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه التوافق",
          code: `public sealed record ProductV1(\n    Guid Id,\n    string Name,\n    decimal Price,\n    string? ImageUrl = null);\n\npublic sealed record ProductV2(\n    Guid Id,\n    string Name,\n    decimal PriceExcludingTax,\n    decimal PriceIncludingTax);`,
        },
      },
    },
  ],
});
