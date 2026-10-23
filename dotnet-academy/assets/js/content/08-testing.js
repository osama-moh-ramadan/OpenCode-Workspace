/* الوحدة 9 — الاختبارات والجودة: Unit وIntegration. */
Academy.addModule({
  id: "testing",
  title: "الاختبارات والجودة",
  tagline: "الاختبار الجيد لا يثبت أن الكود يعمل فقط؛ يثبت أنك تستطيع تغييره دون خوف.",
  icon: "✓",
  color: "#22c55e",
  lessons: [
    {
      id: "unit-testing",
      title: "Unit Testing: اختبر السلوك لا التنفيذ",
      duration: 28,
      level: "متوسط",
      summary:
        "اختبار الوحدة السريع هو شبكة أمانك أثناء إعادة التصميم. سنكتب اختبارات xUnit حقيقية، ونفرّق بين الاختبار الذي يحمي السلوك والاختبار الذي يقيّدك بالتفاصيل.",
      keywords: ["xUnit", "Fact", "Theory", "Assert", "test double", "fake", "AAA", "coverage"],
      objectives: [
        "تنشئ مشروع xUnit وتربطه بمشروع التطبيق.",
        "تكتب Arrange/Act/Assert واضحًا.",
        "تستخدم Fact وTheory للحالات الحدّية.",
        "تختار fake أو mock دون إفراط.",
        "تعرف حدود Code Coverage."
      ],
      concept: `
        <p><strong>اختبار الوحدة</strong> يتحقق من سلوك قطعة صغيرة من الكود بسرعة ودون شبكة أو قاعدة بيانات. ليس هدفه إثبات أن كل شيء يعمل؛ هدفه حماية قرار واحد: «عند هذا المدخل، يجب أن يحدث هذا». عندما تفشل الاختبارات بعد تعديل، فهي تخبرك أن سلوكًا مهمًا تغيّر، لا أنك كتبت سطرًا مختلفًا.</p>
        <h3>السلوك مقابل التنفيذ</h3>
        <p>الاختبار الجيد يقول: «الخصم 10% على 3 قطع بسعر 19.99 يعطي 53.97». الاختبار السيئ يقول: «تم استدعاء <code>Calculate</code> مرة واحدة ثم <code>Round</code>». الثاني يمنعك من إعادة التسمية أو تحسين الكود دون كسر الاختبار، رغم أن السلوك لم يتغير. اختبر النتيجة الظاهرة، لا تسلسل الاستدعاءات، إلا إذا كان التسلسل نفسه عقدًا مهمًا.</p>
        <h3>Arrange / Act / Assert</h3>
        <p>رتب المدخلات والتبعيات، نفّذ العملية، ثم تحقق من النتيجة. اجعل كل اختبار يحكي قصة واحدة. إذا احتجت ثلاث عمليات Act، فغالبًا لديك ثلاثة اختبارات. لا تضع منطقًا معقدًا في الاختبار؛ إن احتجت شروطًا كثيرة، استخدم <code>Builder</code> أو <code>Theory</code>. الاسم الجيد يشرح السلوك: <code>CalculateTotal_RejectsNonPositiveQuantity</code>.</p>
        <h3>Fact وTheory</h3>
        <p><code>[Fact]</code> حالة واحدة. <code>[Theory]</code> مع <code>[InlineData]</code> يشغّل نفس الاختبار بمدخلات متعددة، وهو ممتاز للحدود: صفر، سالب، قيمة قصوى، null. لا تكرر الاختبار يدويًا لكل قيمة. أضف اسمًا وصفيًا لكل حالة عند الحاجة. الحدود هي المكان الذي تظهر فيه الأخطاء، لا المسار السعيد فقط.</p>
        <h3>Test Doubles</h3>
        <p><strong>Fake</strong> تنفيذ بسيط يعمل فعليًا (قائمة في الذاكرة). <strong>Stub</strong> يعيد قيمة ثابتة. <strong>Mock</strong> يتحقق من الاستدعاءات. <strong>Spy</strong> يسجلها. لا تستخدم Mock لكل شيء؛ الاختبار المليء بالتوقعات يصبح هشًا. فضّل fake بسيطًا عندما تحتاج تعاونًا، وmock فقط عند التحقق من تفاعل خارجي مهم.</p>
        <h3>السرعة والحتمية</h3>
        <p>اختبار الوحدة يجب أن يعمل في أجزاء من الثانية، دون إنترنت أو وقت حقيقي أو ملفات. استبدل <code>IClock</code> و<code>IEmailSender</code> و<code>IOrderRepository</code>. لا تعتمد على ترتيب تنفيذ الاختبارات أو حالة مشتركة. إذا نجح الاختبار أحيانًا وفشل أحيانًا، فهو ليس اختبار وحدة موثوقًا؛ أصلح السبب لا تكرر التشغيل.</p>
        <h3>التغطية ليست ضمانًا</h3>
        <p>Code Coverage يقيس الأسطر التي نُفّذت، لا الحالات التي تحققت. سطر بلا فرع قد يكون مغطى ولا يتحقق من شيء. استخدم التغطية كمؤشر لا هدفًا. اكتب اختبارات للحدود والأخطاء والسلوك المالي الحساس. Mutation Testing أقوى لكنه أبطأ؛ استخدمه في الوحدات الحرجة.</p>
      `,
      walkthrough: [
        {
          title: "أنشئ مشروع الاختبارات",
          code: `dotnet new xunit -o tests/Souq.UnitTests\ndotnet add tests/Souq.UnitTests reference src/Souq.Domain\ndotnet test tests/Souq.UnitTests`,
          lang: "bash",
          body: `<p><code>dotnet new xunit</code> ينشئ مشروع اختبارات مستقلًا. الفصل مهم: مشروع التطبيق لا يحمل مكتبة الاختبار. أضف مرجعًا إلى المشروع الذي تختبره فقط، لا إلى الـ API كله. شغّل <code>dotnet test</code> مبكرًا للتأكد من أن القالب يعمل قبل إضافة كودك.</p>`
        },
        {
          title: "اكتب أول Fact",
          code: `public sealed class PricingServiceTests\n{\n    [Fact]\n    public void CalculateTotal_AppliesDiscount_AndRounds()\n    {\n        var service = new PricingService();\n\n        var total = service.CalculateTotal(19.99m, 3, 0.10m);\n\n        Assert.Equal(53.97m, total);\n    }\n}`,
          lang: "csharp",
          body: `<p>الاسم يصف الحالة والنتيجة. المدخلات واقعية: 19.99 × 3 = 59.97، وبعد خصم 10% = 53.973، فيجب التقريب إلى 53.97. الاختبار لا يحتاج قاعدة بيانات لأنه يختبر حسابًا نقيًا. لاحظ <code>m</code> على الأرقام العشرية؛ <code>decimal</code> وليس <code>double</code>.</p>`
        },
        {
          title: "غطِّ الحدود بـTheory",
          code: `[Theory]\n[InlineData(0)]\n[InlineData(-1)]\n[InlineData(int.MinValue)]\npublic void CalculateTotal_RejectsNonPositiveQuantity(int quantity)\n{\n    var service = new PricingService();\n\n    var ex = Assert.Throws<ArgumentOutOfRangeException>(() =>\n        service.CalculateTotal(10m, quantity, 0m));\n\n    Assert.Equal("quantity", ex.ParamName);\n}`,
          lang: "csharp",
          body: `<p><code>[Theory]</code> يشغّل الحالات الثلاث كاختبارات مستقلة. نتحقق من نوع الاستثناء واسم المعامل، لا من نص الرسالة الكامل الذي قد يتغير. الصفر والسالب و<code>int.MinValue</code> تمثل حدودًا مختلفة. أضف حالة الكمية الكبيرة جدًا إذا كان لديك حد أعلى في قواعد العمل.</p>`
        },
        {
          title: "اختبر الخصم غير الصالح",
          code: `[Theory]\n[InlineData(-0.01)]\n[InlineData(1.01)]\npublic void CalculateTotal_RejectsInvalidDiscount(decimal discount)\n{\n    var service = new PricingService();\n\n    Assert.Throws<ArgumentOutOfRangeException>(() =>\n        service.CalculateTotal(10m, 1, discount));\n}`,
          lang: "csharp",
          body: `<p>الخصم يجب أن يكون بين 0 و1. اختبر ما قبل الحد وما بعده، لا القيم الصحيحة فقط. إن كان 1 مسموحًا (خصم 100%)، أضف اختبارًا له كحالة صحيحة. حدود القيم هي عقد؛ وثّقها في الاختبار وفي الكود. لا تعتمد على تحقق الـ API وحده؛ الخدمة قد تُستدعى من BackgroundService.</p>`
        },
        {
          title: "استخدم fake بسيطًا",
          code: `public interface IOrderRepository\n{\n    Task<Order?> FindAsync(Guid id, CancellationToken ct);\n}\n\npublic sealed class FakeOrderRepository : IOrderRepository\n{\n    private readonly Dictionary<Guid, Order> _orders = new();\n\n    public void Add(Order order) => _orders[order.Id] = order;\n\n    public Task<Order?> FindAsync(Guid id, CancellationToken ct)\n        => Task.FromResult(_orders.GetValueOrDefault(id));\n}`,
          lang: "csharp",
          body: `<p><code>FakeOrderRepository</code> تنفيذ حقيقي بسيط في الذاكرة. لا يحتاج Mock framework. يمكنك إضافة طلب ثم اختبار الخدمة. هذا يبقي الاختبار مقروءًا، لكنه لا يختبر SQL أو العلاقات. لتلك الطبقة استخدم اختبار تكامل. الـ fake يجب أن يحاكي العقد، لا أن يخفي أخطاء الإنتاج.</p>`
        },
        {
          title: "اختبر التعاون مع fake",
          code: `[Fact]\npublic async Task PlaceOrder_WhenOrderMissing_ReturnsNotFound()\n{\n    var orders = new FakeOrderRepository();\n    var service = new OrderService(orders);\n\n    var result = await service.CancelAsync(Guid.NewGuid(), CancellationToken.None);\n\n    Assert.False(result);\n}`,
          lang: "csharp",
          body: `<p>الاختبار يرتب fake فارغًا، ينفّذ الإلغاء، ويتحقق من النتيجة. لا يهتم بكيفية استعلام الـ fake. إذا كانت الخدمة تحتاج سلوكًا أكثر تعقيدًا، أضف طلبًا إلى الـ fake. لا تختبر أن <code>FindAsync</code> استُدعيت مرة واحدة إلا إذا كان عدد الاستدعاءات جزءًا من متطلب أداء مهم.</p>`
        },
        {
          title: "اختبر async والإلغاء",
          code: `[Fact]\npublic async Task GetProduct_WhenCancelled_ThrowsOperationCanceled()\n{\n    var repo = new SlowRepository();\n    using var cts = new CancellationTokenSource();\n    cts.Cancel();\n\n    await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>\n        repo.GetAsync(Guid.NewGuid(), cts.Token));\n}`,
          lang: "csharp",
          body: `<p>الإلغاء سلوك يجب اختباره. استخدم <code>ThrowsAnyAsync</code> لأن الأنواع الفرعية مثل <code>TaskCanceledException</code> مقبولة. لا تنتظر تأخيرًا حقيقيًا طويلًا؛ استخدم fake يلاحظ التوكن. إذا كانت الخدمة تبتلع الإلغاء وتعيد نتيجة، فقد تخالف عقد الأداء. اختبر ما يهم، لا كل تفصيل.</p>`
        },
        {
          title: "لا تكرر بيانات الإعداد",
          code: `public sealed class OrderBuilder\n{\n    private Guid _userId = Guid.NewGuid();\n    private decimal _total = 100m;\n\n    public OrderBuilder WithTotal(decimal total)\n    {\n        _total = total;\n        return this;\n    }\n\n    public Order Build() => new(Guid.NewGuid(), _userId, _total);\n}`,
          lang: "csharp",
          body: `<p>Builder يقلل الضوضاء عندما تحتاج كائنًا كبيرًا بقيم افتراضية. اجعل الاختبار يوضح فقط ما يهم: <code>new OrderBuilder().WithTotal(0).Build()</code>. لا تخفِ كل شيء؛ لا يزال القارئ يحتاج فهم الحالة. استخدمه عندما تتكرر البيانات، لا لكل كائن صغير.</p>`
        },
        {
          title: "شغّل الاختبارات مع التغطية",
          code: `dotnet test tests/Souq.UnitTests \\\n  --collect:"XPlat Code Coverage"`,
          lang: "bash",
          body: `<p>هذا يجمع تقرير تغطية. افتح التقرير لترى الفروع غير المغطاة، لا النسبة فقط. لا ترفع النسبة باختبارات بلا Assert. ركّز على قواعد العمل والحدود. في CI، افشل عند انخفاض التغطية في مشاريع حرجة، لكن لا تجعل رقمًا عامًا يمنع أي تغيير.</p>`
        },
        {
          title: "شغّل اختبارًا واحدًا بسرعة",
          code: `dotnet test --filter "FullyQualifiedName~PricingServiceTests"`,
          lang: "bash",
          body: `<p>أثناء التطوير، شغّل الاختبارات المتعلقة بتغييرك فقط للسرعة، ثم شغّل المجموعة كاملة قبل الدفع. لا تعتمد على المرشح في CI؛ قد يخفي فشلًا في مكان آخر. اجعل أسماء الاختبارات منظمة حسب الطبقة أو الميزة لتسهيل الفلترة.</p>`
        }
      ],
      compare: {
        intro: `<p>الاختباران يمران، لكن أحدهما يحمي السلوك والآخر يقيّد التنفيذ.</p>`,
        before: {
          label: "اختبار الهيكل الداخلي",
          lang: "csharp",
          title: "قبل",
          code: `var mock = new Mock<IPricingCalculator>();\nmock.Setup(x => x.Multiply(19.99m, 3)).Returns(59.97m);\nmock.Setup(x => x.Round(53.973m)).Returns(53.97m);\n\nvar service = new PricingService(mock.Object);\nservice.CalculateTotal(19.99m, 3, 0.10m);\n\nmock.Verify(x => x.Multiply(19.99m, 3), Times.Once);\nmock.Verify(x => x.Round(53.973m), Times.Once);`,
          points: [
            "يربط الاختبار بتسلسل الاستدعاءات.",
            "أي إعادة هيكلة تكسر الاختبار.",
            "لا يتحقق من النتيجة النهائية.",
            "يستخدم mock رغم أن الحساب نقي."
          ]
        },
        after: {
          label: "اختبار السلوك",
          lang: "csharp",
          title: "بعد",
          code: `[Fact]\npublic void CalculateTotal_AppliesDiscount_AndRounds()\n{\n    var service = new PricingService();\n\n    var total = service.CalculateTotal(19.99m, 3, 0.10m);\n\n    Assert.Equal(53.97m, total);\n}`,
          points: [
            "يتحقق من النتيجة التي يراها المستخدم.",
            "لا يهتم بكيفية الحساب داخليًا.",
            "سريع وواضح.",
            "يسمح بإعادة التصميم دون كسر."
          ]
        },
        verdict: `<p>اختبر ما يجب أن يظل صحيحًا، لا كيف كتبته. استخدم mock عند وجود تفاعل خارجي لا يمكن اختباره حقيقيًا، لا لمجرد أن المكتبة موجودة.</p>`
      },
      internals: `
        <p>xUnit ينشئ نسخة جديدة من class الاختبار لكل test method، ما يقلل تسرب الحالة. الاختبارات قد تعمل بالتوازي حسب المجموعات؛ لا تعتمد على ترتيبها. <code>IClassFixture</code> يشارك إعدادًا ثقيلًا داخل class، و<code>ICollectionFixture</code> بين classes. لا تشارك حالة قابلة للتغيير بين اختبارات متوازية.</p>
        <p><code>Assert.Equal</code> يقارن القيم، و<code>Assert.Throws</code> يتحقق من نوع الاستثناء. لا تختبر نص الرسالة إلا إذا كان عقدًا عامًا. للـ async، استخدم <code>await Assert.ThrowsAsync</code> ولا تستدعي <code>.Result</code>. أي تأخير حقيقي في اختبار الوحدة علامة على أنه ليس اختبار وحدة.</p>
        <h3>Test Doubles</h3>
        <p>Fake ينفّذ السلوك، Stub يعيد قيمة، Mock يتحقق من التفاعل. الإفراط في Mock يجعل الاختبار يعيد كتابة التنفيذ. إذا كان الكائن قيمة أو حسابًا نقيًا، استخدمه حقيقيًا. إذا كان خارجيًا (بريد، دفع، ساعة)، استبدله. لا تستخدم Mock لكي تتجنب تصميم واجهة قابلة للاختبار.</p>
        <h3>التغطية</h3>
        <p>Coverage يقيس ما نُفّذ، لا ما تحقق. سطر <code>if</code> قد يُنفّذ دون اختبار الفرع الآخر. استخدم تقارير الفروع، واكتب اختبارات للحالات السلبية. Mutation testing يعدّل الكود ويختبر إن كانت الاختبارات تكتشف التغيير؛ مفيد للوحدات المالية. لا تجعل رقم التغطية بديلًا عن التفكير.</p>
      `,
      internalsTable: {
        head: ["المفهوم", "ماذا يعني", "الاستخدام"],
        rows: [
          ["Fact", "حالة واحدة", "سلوك محدد"],
          ["Theory", "حالات متعددة", "الحدود والمدخلات"],
          ["Fake", "تنفيذ بسيط", "تعاون في الذاكرة"],
          ["Stub", "قيمة ثابتة", "التحكم في تبعية"],
          ["Mock", "تحقق من الاستدعاء", "تفاعل خارجي مهم"],
          ["Coverage", "أسطر نُفّذت", "مؤشر لا هدف"]
        ]
      },
      tips: [
        {
          title: "اختبار واحد، سلوك واحد",
          body: "إذا احتاج الاختبار عدة Act أو شروطًا كثيرة، قسّمه. الاسم يجب أن يصف النتيجة المتوقعة."
        },
        {
          title: "ابدأ بالحدود",
          body: "صفر، سالب، null، الحد الأقصى، التكرار. هذه الحالات تكشف الأخطاء أكثر من المسار السعيد."
        },
        {
          title: "لا تفرط في Mock",
          body: "استخدم fake بسيطًا للتعاون، وmock فقط للتفاعل الخارجي الذي يهم. اختبر النتيجة قبل الاستدعاء."
        },
        {
          title: "حافظ على السرعة والحتمية",
          body: "لا شبكة، لا وقت حقيقي، لا ترتيب. إذا كان الاختبار بطيئًا أو متقلبًا، فقد أصبح عائقًا لا شبكة أمان."
        }
      ],
      quiz: [
        {
          q: "ما الفرق بين Fact وTheory؟",
          options: [
            "Fact للاختبارات البطيئة فقط.",
            "Theory يشغّل نفس الاختبار بمدخلات متعددة.",
            "Fact لا يستخدم Assert.",
            "Theory لا يعمل مع async."
          ],
          answer: 1,
          explain: "Theory مع InlineData يكرر الاختبار لقيم مختلفة، مناسب للحدود. Fact حالة واحدة."
        },
        {
          q: "متى نستخدم Fake بدل Mock؟",
          options: [
            "عندما نحتاج التحقق من عدد الاستدعاءات بدقة.",
            "عندما نحتاج تنفيذًا بسيطًا يعمل فعليًا في الذاكرة.",
            "عندما نريد اختبار قاعدة بيانات حقيقية.",
            "عندما نريد قياس الأداء."
          ],
          answer: 1,
          explain: "Fake ينفّذ العقد ببساطة، مثل مستودع في الذاكرة. Mock مناسب للتحقق من التفاعل، لا لكل شيء."
        },
        {
          q: "ماذا تقيس Code Coverage؟",
          options: [
            "عدد الحالات التي تحققت.",
            "نسبة الأسطر/الفروع التي نُفّذت أثناء الاختبارات.",
            "سرعة الاختبارات.",
            "عدد الأخطاء في الإنتاج."
          ],
          answer: 1,
          explain: "التغطية تقيس التنفيذ لا صحة التحقق. يمكن تغطية سطر دون Assert فعّال."
        }
      ],
      capstone: {
        title: "شبكة أمان لحساب سعر Souq",
        goal: "اكتب اختبارات وحدة لحساب السعر والخصم والحدود، واربطها بمشروع الاختبارات.",
        tasks: [
          "أنشئ مشروع <code>Souq.UnitTests</code> وأضف مرجعًا إلى مشروع المجال.",
          "اكتب اختبارًا لحساب الإجمالي مع خصم وتقريب إلى منزلتين.",
          "أضف <code>[Theory]</code> للكميات الصفرية والسلبية والحد الأقصى.",
          "أضف fake لمستودع الطلبات واختبر حالة عدم وجود الطلب.",
          "شغّل <code>dotnet test</code> مع تقرير تغطية، وأصلح أي فرع غير مغطى في حساب السعر."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه الاختبار",
          code: `[Fact]\npublic void CalculateTotal_AppliesDiscount_AndRounds()\n{\n    var service = new PricingService();\n\n    var total = service.CalculateTotal(19.99m, 3, 0.10m);\n\n    Assert.Equal(53.97m, total);\n}`,
        },
      },
    },
    {
      id: "integration-testing",
      title: "Integration Testing: API حقيقي وقاعدة بيانات حقيقية",
      duration: 32,
      level: "متقدم",
      summary:
        "اختبار الوحدة لا يرى routing ولا serialization ولا SQL. سنشغّل API داخل TestServer مع PostgreSQL حقيقي، ونختبر العقد من الخارج.",
      keywords: ["WebApplicationFactory", "TestServer", "Testcontainers", "PostgreSQL", "IAsyncLifetime", "integration test", "authentication"],
      objectives: [
        "تشغّل API كاملًا داخل اختبار دون فتح منفذ شبكة.",
        "تستبدل قاعدة البيانات بحاوية PostgreSQL معزولة.",
        "تختبر status code وJSON وProblemDetails.",
        "تختبر المصادقة والتفويض في pipeline حقيقي.",
        "تعزل الاختبارات وتنظف الموارد."
      ],
      concept: `
        <p><strong>Integration Test</strong> يختبر عدة طبقات معًا: routing، model binding، validation، middleware، EF Core، وقاعدة البيانات. لا يعني ذلك اختبار كل النظام يدويًا؛ يعني اختبار الحدود الحقيقية التي لا تظهر في اختبار الوحدة. خطأ في اسم JSON أو ترتيب middleware لن يكتشفه اختبار <code>PricingService</code>.</p>
        <h3>WebApplicationFactory</h3>
        <p><code>WebApplicationFactory&lt;Program&gt;</code> يشغّل التطبيق في ذاكرة الاختبار باستخدام <code>TestServer</code>، دون Kestrel أو منفذ TCP. <code>CreateClient()</code> يعيد <code>HttpClient</code> يمر عبر pipeline الحقيقي. يمكنك تجاوز التسجيلات بـ<code>ConfigureWebHost</code>. هذا أقرب إلى الإنتاج من استدعاء controller مباشرة، وأسرع من نشر خدمة كاملة.</p>
        <h3>قاعدة بيانات حقيقية</h3>
        <p>InMemory provider لا يفرض مفاتيح أجنبية أو قيودًا علائقية أو SQL حقيقيًا. SQLite في الذاكرة أفضل من InMemory لكنه يختلف عن PostgreSQL. <strong>Testcontainers</strong> يشغّل PostgreSQL في Docker ويعطيك اتصالًا مؤقتًا. هذا يختبر migrations والقيود والاستعلامات الفعلية. التكلفة: Docker مطلوب، والبدء أبطأ. اجعلها اختبارات تكامل لا اختبارات وحدة.</p>
        <h3>العزل والبيانات</h3>
        <p>كل test class أو collection تحتاج قاعدة معزولة أو تنظيفًا موثوقًا. لا تشارك قاعدة قابلة للتغيير بين اختبارات متوازية. استخدم <code>IAsyncLifetime</code> لبدء/إيقاف الحاوية، وطبّق migrations مرة واحدة. ازرع البيانات عبر API أو fixture واضحة. لا تعتمد على ترتيب الاختبارات. الحاوية الجديدة لكل collection أبطأ لكنها أقل تقلبًا.</p>
        <h3>ماذا تختبر؟</h3>
        <p>المسار السعيد، 400 مع تفاصيل التحقق، 401/403، 404، 409، وترقيم الصفحات. تحقق من <code>Content-Type</code> وشكل JSON وحقول ProblemDetails. اختبر أن المستخدم A لا يرى طلب B. لا تكرر كل اختبار وحدة على مستوى API؛ ركّز على التكامل والعقد.</p>
        <h3>المصادقة</h3>
        <p>لا تحتاج خادم هوية حقيقيًا لكل اختبار. يمكنك إضافة مخطط اختبار أو إصدار JWT بمفتاح اختبار. لكن اختبر أيضًا رفض التوكن المنتهي أو الخاطئ. لا تتجاوز <code>UseAuthentication</code> كله، وإلا لن تختبر التفويض. استخدم سياسات حقيقية مع مستخدم اختبار.</p>
        <h3>الاستقرار في CI</h3>
        <p>انتظر جاهزية الحاوية، ضع timeout، وسجّل logs عند الفشل. لا تعتمد على Docker المحلي فقط؛ شغّل الاختبارات في CI. إذا كانت بطيئة جدًا، افصلها عن اختبارات الوحدة في job مستقل. لا تجعلها اختيارية في الفرع الرئيسي. اختبار تكامل فاشل أهم من عشرة ناجحين بلا معنى.</p>
      `,
      walkthrough: [
        {
          title: "أضف حزم الاختبار",
          code: `dotnet add tests/Souq.IntegrationTests package Microsoft.AspNetCore.Mvc.Testing\ndotnet add tests/Souq.IntegrationTests package Testcontainers.PostgreSql\ndotnet add tests/Souq.IntegrationTests reference src/Souq.Api`,
          lang: "bash",
          body: `<p><code>Microsoft.AspNetCore.Mvc.Testing</code> يوفر <code>WebApplicationFactory</code> وTestServer. <code>Testcontainers.PostgreSql</code> يدير حاوية PostgreSQL. أضف مرجعًا إلى مشروع API فقط لاختبار النهاية إلى النهاية. لا تضع حزم الاختبار في مشروع الإنتاج.</p>`
        },
        {
          title: "اجعل Program مرئيًا",
          code: `// نهاية Program.cs\npublic partial class Program { }`,
          lang: "csharp",
          body: `<p>Top-level statements تولّد class <code>Program</code> داخليًا. إضافة <code>public partial class Program</code> تجعله متاحًا لـ<code>WebApplicationFactory&lt;Program&gt;</code>. لا تضف منطقًا هنا؛ مجرد جسر للاختبار. بعض القوالب تفعل ذلك تلقائيًا، لكن التحقق منه يمنع خطأ compilation غامضًا.</p>`
        },
        {
          title: "أنشئ Factory للحاوية",
          code: `public sealed class SouqApiFactory : WebApplicationFactory<Program>,\n    IAsyncLifetime\n{\n    private readonly PostgreSqlContainer _db = new PostgreSqlBuilder()\n        .WithImage("postgres:16-alpine")\n        .Build();\n\n    public async Task InitializeAsync() => await _db.StartAsync();\n\n    public new async Task DisposeAsync()\n    {\n        await _db.DisposeAsync();\n        await base.DisposeAsync();\n    }\n}`,
          lang: "csharp",
          body: `<p>الحاوية تُنشأ لكل factory. <code>IAsyncLifetime</code> يضمن بدءها قبل الاختبارات. <code>DisposeAsync</code> يوقفها حتى لو فشل اختبار. لا تبدأ الحاوية داخل constructor متزامن. استخدم صورة محددة الإصدار، لا <code>latest</code>، لنتائج قابلة للتكرار.</p>`
        },
        {
          title: "استبدل DbContext",
          code: `protected override void ConfigureWebHost(IWebHostBuilder builder)\n{\n    builder.ConfigureServices(services =>\n    {\n        services.RemoveAll<DbContextOptions<AppDbContext>>();\n        services.AddDbContext<AppDbContext>(options =>\n            options.UseNpgsql(_db.GetConnectionString()));\n    });\n}`,
          lang: "csharp",
          body: `<p><code>RemoveAll</code> يحذف تسجيل الإنتاج. أضف DbContext جديدًا يشير إلى الحاوية. لا تنسَ حذف أي تسجيل آخر يعتمد على الاتصال القديم. استخدم نفس الموفر (Npgsql) لاختبار SQL الحقيقي. لا تستبدل قاعدة البيانات بـInMemory في اختبار تكامل.</p>`
        },
        {
          title: "طبّق migrations",
          code: `using var scope = Services.CreateScope();\nvar db = scope.ServiceProvider.GetRequiredService<AppDbContext>();\nawait db.Database.MigrateAsync();`,
          lang: "csharp",
          body: `<p>شغّل migrations على قاعدة الاختبار لإنشاء المخطط. هذا يختبر أن migrations نفسها صالحة. لا تستخدم <code>EnsureCreated</code> في الإنتاج؛ هو لا يدير التغييرات. نفّذ ذلك بعد بدء الحاوية وقبل أول طلب. إذا فشلت migration، أفشل الاختبار برسالة واضحة.</p>`
        },
        {
          title: "اختبر GET من الخارج",
          code: `[Fact]\npublic async Task GetProducts_ReturnsOkAndJson()\n{\n    var client = _factory.CreateClient();\n\n    var response = await client.GetAsync("/api/v1/products");\n\n    response.EnsureSuccessStatusCode();\n    Assert.Equal("application/json",\n        response.Content.Headers.ContentType?.MediaType);\n}`,
          lang: "csharp",
          body: `<p><code>CreateClient</code> يمر عبر routing وmiddleware وserialization. نتحقق من 200 ونوع المحتوى. يمكنك قراءة JSON إلى DTO والتحقق من الحقول. لا تختبر كل حقل في كل اختبار؛ ركّز على العقد المهم. استخدم <code>EnsureSuccessStatusCode</code> لرسالة فشل أوضح.</p>`
        },
        {
          title: "اختبر 400 وProblemDetails",
          code: `var response = await client.PostAsJsonAsync(\n    "/api/v1/products",\n    new { name = "", price = -1 });\n\nAssert.Equal(HttpStatusCode.BadRequest, response.StatusCode);\nvar problem = await response.Content\n    .ReadFromJsonAsync<ValidationProblemDetails>();\nAssert.NotNull(problem);\nAssert.True(problem!.Errors.ContainsKey("Name"));`,
          lang: "csharp",
          body: `<p>هذا يختبر validation filter وserialization وشكل الخطأ. لا تكتف بـ400؛ تحقق من <code>ValidationProblemDetails</code> وحقول الأخطاء. استخدم أسماء الخصائص كما تظهر في JSON. اختبر أيضًا 404 و409، لأن العملاء يعتمدون على رموز الحالة لا على النص فقط.</p>`
        },
        {
          title: "اختبر التفويض بمستخدم آخر",
          code: `var client = _factory.CreateClient();\nclient.DefaultRequestHeaders.Authorization =\n    new AuthenticationHeaderValue("Bearer", TokenFor(userA));\n\nvar response = await client.GetAsync($"/api/v1/orders/{orderOfUserB}");\n\nAssert.Equal(HttpStatusCode.NotFound, response.StatusCode);`,
          lang: "csharp",
          body: `<p>هذا اختبار BOLA الحقيقي. لا يكفي اختبار 401 بلا توكن. أنشئ توكنًا لمستخدم A واطلب مورد B. استخدم مفتاح اختبار ومخطط مصادقة حقيقيًا. تحقق من 404/403 حسب عقدك. أضف اختبارًا لتوكن منتهٍ أو توقيع خاطئ.</p>`
        },
        {
          title: "اعزل كل اختبار",
          code: `public class ProductsTests : IClassFixture<SouqApiFactory>\n{\n    private readonly SouqApiFactory _factory;\n\n    public ProductsTests(SouqApiFactory factory) => _factory = factory;\n\n    [Fact]\n    public async Task Create_Then_Get_ReturnsProduct()\n    {\n        var client = _factory.CreateClient();\n        // أنشئ بيانات بمعرّف فريد لهذا الاختبار.\n    }\n}`,
          lang: "csharp",
          body: `<p><code>IClassFixture</code> يشارك factory داخل class فقط. استخدم بيانات فريدة (SKU أو بريد) لكل اختبار لتجنب التعارض. لا تعتمد على أن الاختبار السابق أنشأ منتجًا. إذا احتجت عزلًا كاملًا، استخدم transaction أو قاعدة جديدة لكل collection. نظّف ما أنشأته عند الحاجة.</p>`
        },
        {
          title: "شغّل اختبارات التكامل في CI",
          code: `dotnet test tests/Souq.IntegrationTests \\\n  --logger "console;verbosity=normal"`,
          lang: "bash",
          body: `<p>شغّلها في CI مع Docker متاح. لا تجعلها ضمن اختبارات الوحدة السريعة إن كانت بطيئة. احتفظ بسجل الحاوية عند الفشل. اختبر على نفس صورة PostgreSQL المستخدمة في الإنتاج. إذا كان CI لا يدعم Docker، استخدم خدمة قاعدة بيانات مؤقتة، لا InMemory.</p>`
        }
      ],
      compare: {
        intro: `<p>InMemory يبدو أسهل، لكنه لا يختبر ما يحدث فعليًا في PostgreSQL.</p>`,
        before: {
          label: "InMemory Provider",
          lang: "csharp",
          title: "قبل",
          code: `services.AddDbContext<AppDbContext>(options =>\n    options.UseInMemoryDatabase("tests"));`,
          points: [
            "لا يفرض مفاتيح أجنبية أو قيودًا.",
            "لا يختبر SQL أو migrations.",
            "قد ينجح حيث تفشل PostgreSQL.",
            "لا يكشف مشاكل المعاملات."
          ]
        },
        after: {
          label: "PostgreSQL حقيقي",
          lang: "csharp",
          title: "بعد",
          code: `services.RemoveAll<DbContextOptions<AppDbContext>>();\nservices.AddDbContext<AppDbContext>(options =>\n    options.UseNpgsql(_db.GetConnectionString()));`,
          points: [
            "نفس موفر الإنتاج.",
            "قيود وفهارس وSQL حقيقية.",
            "migrations تُختبر فعليًا.",
            "حاوية معزولة قابلة للتكرار."
          ]
        },
        verdict: `<p>استخدم InMemory لاختبار منطق بسيط إن كان مناسبًا، لكن لا تسميه اختبار تكامل. القرارات المتعلقة بالبيانات تحتاج قاعدة حقيقية.</p>`
      },
      internals: `
        <p><code>WebApplicationFactory</code> يبني التطبيق مرة واحدة ويستخدم <code>TestServer</code> لمعالجة الطلبات في الذاكرة. لا يفتح منفذًا، لكنه يمر عبر middleware وDI وrouting. <code>CreateClient</code> يعيد HttpClient مرتبطًا بالخادم. هذا يجعله أسرع من HTTP حقيقي، لكنه لا يختبر Kestrel أو TLS أو reverse proxy.</p>
        <p>عند تجاوز الخدمات، احذر أن تعيد تسجيل تبعيات أخرى تشير إلى الإعداد القديم. استخدم <code>RemoveAll</code> ثم أضف البديل. رتّب الإعداد قبل بناء الخادم. <code>ConfigureWebHost</code> يعمل في مرحلة بناء الـ host، لا بعد أول طلب.</p>
        <h3>Testcontainers</h3>
        <p>Testcontainers يبدأ حاوية Docker ويعيد connection string. يحتاج Docker daemon متاحًا. استخدم صورة محددة، وانتظر حتى تصبح جاهزة. أغلق الحاوية دائمًا. في CI، قد تحتاج إلى تفعيل Docker أو خدمة PostgreSQL. الحاوية لكل collection توازن بين العزل والسرعة.</p>
        <h3>العزل والتوازي</h3>
        <p>xUnit يشغّل collections بالتوازي. إذا شاركت قاعدة واحدة، استخدم بيانات فريدة أو transaction لكل اختبار. لا تعتمد على تنظيف global بين اختبارات متوازية. بعض الفرق تستخدم قاعدة واحدة وتسلسل الاختبارات؛ هذا يخفي مشاكل العزل ويبطئ. الأفضل عزل واضح.</p>
        <h3>المصادقة</h3>
        <p>يمكنك تسجيل مخطط اختبار يقرأ رؤوسًا ويبني Claims. هذا يختبر سياسات التفويض دون خادم هوية. لكنه قد لا يختبر توقيع JWT الحقيقي. اجمع بين اختبار مخطط للسياسات واختبار token حقيقي للمسار الحرج. لا تتجاوز middleware المصادقة بالكامل.</p>
      `,
      internalsTable: {
        head: ["العنصر", "ماذا يختبر", "تحذير"],
        rows: [
          ["WebApplicationFactory", "pipeline كامل في الذاكرة", "لا يختبر Kestrel/TLS"],
          ["Testcontainers", "قاعدة بيانات حقيقية", "يتطلب Docker"],
          ["MigrateAsync", "صلاحية migrations", "لا تستخدم EnsureCreated"],
          ["IClassFixture", "مشاركة إعداد", "بيانات مشتركة قد تتلوث"],
          ["Test auth handler", "سياسات التفويض", "لا يختبر توقيع JWT الحقيقي"],
          ["HttpClient", "العقد من الخارج", "لا تختبر تفاصيل داخلية"]
        ]
      },
      tips: [
        {
          title: "اختبر من الخارج",
          body: "استخدم HttpClient وstatus/JSON. لا تستدعي services مباشرة في اختبار تكامل API؛ هذا يختبر التنفيذ لا العقد."
        },
        {
          title: "قاعدة بيانات حقيقية",
          body: "استخدم PostgreSQL عبر Testcontainers. InMemory لا يفرض القيود ولا يختبر SQL أو migrations."
        },
        {
          title: "اعزل البيانات",
          body: "بيانات فريدة أو قاعدة لكل collection. لا تعتمد على ترتيب الاختبارات أو حالة مشتركة."
        },
        {
          title: "اختبر السيناريوهات السلبية",
          body: "400 و401 و403 و404 و409. هذه هي العقود التي يخطئ فيها العملاء، واكتشافها في الإنتاج مكلف."
        }
      ],
      quiz: [
        {
          q: "ما فائدة WebApplicationFactory؟",
          options: [
            "يشغّل Kestrel على منفذ عام.",
            "يشغّل التطبيق في الذاكرة ويمرر الطلبات عبر pipeline الحقيقي.",
            "يستبدل قاعدة البيانات بـInMemory تلقائيًا.",
            "يقيس أداء الشبكة."
          ],
          answer: 1,
          explain: "يستخدم TestServer لمعالجة الطلبات داخل الذاكرة مع routing وmiddleware وDI، دون فتح منفذ."
        },
        {
          q: "لماذا نستخدم Testcontainers PostgreSQL؟",
          options: [
            "لأنه أسرع من اختبار الوحدة دائمًا.",
            "لاختبار SQL والقيود وmigrations على نفس موفر الإنتاج.",
            "لتجنب كتابة Assert.",
            "لتشغيل API على الإنترنت."
          ],
          answer: 1,
          explain: "الحاوية توفر قاعدة حقيقية معزولة، فتكشف ما لا يكشفه InMemory مثل القيود والاستعلامات."
        },
        {
          q: "أي اختبار أفضل لثغرة BOLA؟",
          options: [
            "اختبار أن المستخدم بلا توكن يحصل على 401.",
            "اختبار أن المستخدم A لا يستطيع قراءة مورد المستخدم B.",
            "اختبار أن JSON يحتوي حقل id.",
            "اختبار أن قاعدة البيانات تعمل."
          ],
          answer: 1,
          explain: "BOLA يحدث مع مستخدم مصادق يصل إلى مورد غيره. اختبار 401 وحده لا يكشفه."
        }
      ],
      capstone: {
        title: "اختبار تكامل Souq API",
        goal: "شغّل API مع PostgreSQL حقيقي واختبر الكتالوج والتحقق والملكية من الخارج.",
        tasks: [
          "أنشئ <code>SouqApiFactory</code> مع حاوية PostgreSQL وطبّق migrations.",
          "أضف اختبار GET للمنتجات يتحقق من 200 و<code>application/json</code>.",
          "أضف اختبار POST بمدخلات غير صالحة يتحقق من 400 و<code>ValidationProblemDetails</code>.",
          "أضف اختبار BOLA: مستخدم A يطلب طلب مستخدم B ويحصل على 404.",
          "شغّل الاختبارات في CI مع Docker وتأكد من تنظيف الحاوية."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه الاختبار",
          code: `var client = _factory.CreateClient();\nclient.DefaultRequestHeaders.Authorization =\n    new AuthenticationHeaderValue("Bearer", TokenFor(userA));\n\nvar response = await client.GetAsync($"/api/v1/orders/{orderOfUserB}");\n\nAssert.Equal(HttpStatusCode.NotFound, response.StatusCode);`,
        },
      },
    },
    {
      id: "tdd-analyzers",
      title: "TDD والجودة: Red → Green → Refactor",
      duration: 26,
      level: "متوسط",
      summary:
        "TDD ليس طقسًا دينيًا؛ هو حلقة صغيرة تقلل التصميم الخاطئ وتجعل الاختبار يسبق الكود. سنربطها بـAnalyzers وCI Quality Gates.",
      keywords: ["TDD", "red green refactor", "mutation testing", "analyzers", "EditorConfig", "warnings as errors", "CI"],
      objectives: [
        "تطبق دورة Red/Green/Refactor على ميزة صغيرة.",
        "تكتب اختبارًا يفشل لسبب صحيح.",
        "تستخدم Analyzers لالتقاط الأخطاء قبل التشغيل.",
        "تفرّق بين Coverage وMutation Testing.",
        "تجعل الجودة بوابة في CI لا نصيحة."
      ],
      concept: `
        <p><strong>TDD</strong> يقلب الترتيب المعتاد: اكتب اختبارًا يفشل أولًا، ثم أقل كود يجعله ينجح، ثم حسّن التصميم. الفائدة ليست «اختبارات أكثر» فقط؛ هي أنك تصمم من وجهة نظر المستخدم، وتتأكد أن الاختبار قادر على الفشل. اختبار ينجح قبل كتابة الميزة لا يثبت شيئًا.</p>
        <h3>Red: فشل صحيح</h3>
        <p>الخطوة الحمراء يجب أن تفشل للسبب المتوقع، لا بسبب خطأ compilation أو مرجع ناقص. اقرأ رسالة الفشل: هل الميزة غير موجودة؟ هل النتيجة خاطئة؟ إذا فشل الاختبار لسبب آخر، أصلح الإعداد أولًا. اختبار لا يفشل أبدًا هو اختبار بلا قيمة. هذه الخطوة تكشف أيضًا أن الاختبار يختبر السلوك الصحيح.</p>
        <h3>Green: أقل كود</h3>
        <p>اكتب أبسط تنفيذ يجعل الاختبار ينجح، حتى لو كان مباشرًا. لا تضف abstractions أو حالات لم يطلبها اختبار. ثم أضف اختبارًا للحالة التالية. هذا يمنع over-engineering ويجعل كل سطر مبررًا. «أقل كود» لا يعني كودًا سيئًا؛ يعني عدم بناء مستقبل متخيل.</p>
        <h3>Refactor: بلا تغيير سلوك</h3>
        <p>بعد الأخضر، حسّن الأسماء والبنية وأزل التكرار، مع بقاء الاختبارات خضراء. هذه هي اللحظة الآمنة لإعادة التصميم. لا تخلط refactor مع ميزة جديدة؛ إذا تغير السلوك، أضف اختبارًا أولًا. الـ refactor الصغير المتكرر أفضل من إعادة كتابة ضخمة.</p>
        <h3>Analyzers ليست رفاهية</h3>
        <p>Roslyn Analyzers تلتقط أنماطًا خطيرة قبل التشغيل: <code>async void</code>، إهمال <code>ConfigureAwait</code> حسب السياق، استخدام <code>DateTime.Now</code>، أو تسريب <code>HttpClient</code>. فعّل <code>AnalysisLevel</code> المناسب، واجعل التحذيرات المهمة أخطاء. لا تطفئ تحذيرًا لأنك لا تفهمه؛ اقرأه أو استثنه بسبب موثق.</p>
        <h3>Quality Gates</h3>
        <p>الجودة تحتاج بوابة في CI: build بلا تحذيرات، اختبارات، تنسيق، وفحص أمني. لا تجعل التغطية رقمًا مقدسًا. <strong>Mutation Testing</strong> يعدّل الكود ويختبر إن كانت الاختبارات تكتشف التغيير؛ أقوى من التغطية لكنه أبطأ. استخدمه في الوحدات الحرجة (الأسعار، الصلاحيات، المعاملات).</p>
      `,
      walkthrough: [
        {
          title: "اكتب اختبارًا يفشل",
          code: `[Fact]\npublic void ApplyCoupon_WhenExpired_ReturnsFalse()\n{\n    var coupon = new Coupon("SAVE10", 0.10m,\n        expiresAt: DateTimeOffset.UtcNow.AddDays(-1));\n\n    var applied = coupon.TryApply(100m, out var total);\n\n    Assert.False(applied);\n    Assert.Equal(100m, total);\n}`,
          lang: "csharp",
          body: `<p>هذا الاختبار يصف سلوكًا غير موجود بعد. شغّله؛ يجب أن يفشل لأن <code>TryApply</code> غير موجود أو لأن الكوبون المنتهي لا يُرفض. لا تكتب التنفيذ الآن. لاحظ أن الاختبار يحدد العقد: bool + out total. التصميم يبدأ من الاستخدام.</p>`
        },
        {
          title: "شغّل الاختبار واقرأ الفشل",
          code: `dotnet test --filter "FullyQualifiedName~ApplyCoupon_WhenExpired"`,
          lang: "bash",
          body: `<p>الفشل المتوقع هو compilation error لأن الدالة غير موجودة، أو Assert failure لأن السلوك غير مطبق. إذا فشل لسبب غير متوقع، أصلحه. لا تبدأ بالتنفيذ قبل رؤية الفشل الصحيح. هذه الخطوة تبدو بطيئة لكنها تمنع اختبارًا وهميًا ينجح دائمًا.</p>`
        },
        {
          title: "اكتب أقل تنفيذ",
          code: `public bool TryApply(decimal subtotal, out decimal total)\n{\n    if (DateTimeOffset.UtcNow > _expiresAt)\n    {\n        total = subtotal;\n        return false;\n    }\n\n    total = subtotal * (1 - _discount);\n    return true;\n}`,
          lang: "csharp",
          body: `<p>التنفيذ يغطي الحالة الحمراء فقط. لا تضف بعد حالات الاستخدام أو التحقق من الحد الأدنى حتى تكتب اختبارًا لها. لاحظ استخدام <code>DateTimeOffset.UtcNow</code>؛ في اختبار حقيقي الأفضل حقن <code>IClock</code> لتجنب الاعتماد على الوقت. التصميم يتحسن عندما يطلب الاختبار ذلك.</p>`
        },
        {
          title: "أضف الحالة التالية",
          code: `[Fact]\npublic void ApplyCoupon_WhenValid_AppliesDiscount()\n{\n    var coupon = new Coupon("SAVE10", 0.10m,\n        expiresAt: DateTimeOffset.UtcNow.AddDays(1));\n\n    var applied = coupon.TryApply(100m, out var total);\n\n    Assert.True(applied);\n    Assert.Equal(90m, total);\n}`,
          lang: "csharp",
          body: `<p>الآن أضف السلوك الصحيح. لا تعد كتابة كل شيء؛ التنفيذ الحالي قد يمر بالفعل. شغّل الاختبارين معًا. إذا فشل الجديد، عدّل أقل قدر. لاحظ أن الاختبار يستخدم وقتًا مستقبليًا؛ في اختبار حقيقي استخدم clock ثابتًا لتجنب flakiness عند منتصف الليل.</p>`
        },
        {
          title: "Refactor بأمان",
          code: `public bool TryApply(decimal subtotal, out decimal total)\n{\n    if (IsExpired(DateTimeOffset.UtcNow))\n    {\n        total = subtotal;\n        return false;\n    }\n\n    total = ApplyDiscount(subtotal);\n    return true;\n}\n\nprivate bool IsExpired(DateTimeOffset now) => now > _expiresAt;\nprivate decimal ApplyDiscount(decimal subtotal) => subtotal * (1 - _discount);`,
          lang: "csharp",
          body: `<p>استخرجنا الشرطين إلى دوال واضحة. السلوك لم يتغير، والاختبارات ما زالت خضراء. لا تخلط إعادة التسمية مع تغيير الحساب. إذا أردت تغيير التقريب، اكتب اختبارًا أولًا. الـ refactor يجعل الكود أسهل للقراءة والاختبار التالي.</p>`
        },
        {
          title: "فعّل Analyzers",
          code: `<PropertyGroup>\n  <AnalysisLevel>latest-recommended</AnalysisLevel>\n  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n  <Nullable>enable</Nullable>\n</PropertyGroup>`,
          lang: "xml",
          body: `<p><code>AnalysisLevel</code> يفعّل قواعد Roslyn الموصى بها. <code>TreatWarningsAsErrors</code> يمنع دمج تحذيرات جديدة. ابدأ بـ<code>latest-recommended</code>، لا <code>all</code>، لتجنب ضوضاء هائلة. إذا كان مشروعًا قديمًا، فعّل القواعد تدريجيًا. التحذير الذي لا يُفهم ولا يُصلح يصبح ضوضاء، لكن تجاهله كله أسوأ.</p>`
        },
        {
          title: "اضبط الشدة في EditorConfig",
          code: `[*.cs]\n dotnet_diagnostic.CS8618.severity = error\ndotnet_diagnostic.CA2007.severity = none\n dotnet_diagnostic.IDE0005.severity = warning`,
          lang: "ini",
          body: `<p><code>.editorconfig</code> يثبت سياسة الفريق. لا تضع <code>none</code> لقاعدة لأنها مزعجة فقط؛ وثّق السبب. <code>CA2007</code> (ConfigureAwait) قد لا يناسب تطبيقات ASP.NET Core، لكنه مهم في المكتبات. راجع القواعد مع الفريق، وثبّت الملف في المستودع. الإعداد المحلي وحده لا يحمي CI.</p>`
        },
        {
          title: "أضف بوابة تنسيق",
          code: `dotnet format --verify-no-changes\ndotnet build --warnaserror\ndotnet test`,
          lang: "bash",
          body: `<p><code>dotnet format --verify-no-changes</code> يفشل إذا كان التنسيق مختلفًا. <code>--warnaserror</code> يضمن عدم دمج تحذيرات. <code>dotnet test</code> يشغّل الاختبارات. اجعل هذه الخطوات في CI قبل النشر. لا تصلح التنسيق تلقائيًا في CI؛ افشل واطلب إصلاحًا محليًا، أو استخدم خطوة تنسيق منفصلة.</p>`
        },
        {
          title: "قِس جودة الاختبارات",
          code: `dotnet test --collect:"XPlat Code Coverage"\n# ثم استخدم أداة mutation testing على وحدة السعر.`,
          lang: "bash",
          body: `<p>التغطية تكشف الملفات غير المختبرة. Mutation Testing يعدّل <code>+</code> إلى <code>-</code> أو شرطًا إلى عكسه ويرى هل تفشل الاختبارات. إذا بقي الطافر حيًا، فاختباراتك لا تتحقق من السلوك. ابدأ بوحدة السعر والصلاحيات. لا تشغّل mutation على كل المشروع في كل commit؛ مكلف.</p>`
        }
      ],
      compare: {
        intro: `<p>الاختبار بعد الكود يوثّق ما فعلته؛ TDD يكتشف ما يجب أن تفعله.</p>`,
        before: {
          label: "اختبار لاحق",
          lang: "csharp",
          title: "قبل",
          code: `// كتبنا التنفيذ أولًا، ثم اختبارًا يمر مباشرة.\nvar coupon = new Coupon("SAVE10", 0.1m, future);\nAssert.True(coupon.TryApply(100m, out _));`,
          points: [
            "الاختبار قد ينجح دون أن يثبت الحالة المهمة.",
            "التصميم يتبع التنفيذ لا الاستخدام.",
            "الحالات الحدّية تُنسى.",
            "لا تعرف إن كان الاختبار قادرًا على الفشل."
          ]
        },
        after: {
          label: "دورة TDD",
          lang: "csharp",
          title: "بعد",
          code: `[Fact]\npublic void ApplyCoupon_WhenExpired_ReturnsFalse()\n{\n    var coupon = new Coupon("SAVE10", 0.1m, past);\n\n    var applied = coupon.TryApply(100m, out var total);\n\n    Assert.False(applied);\n    Assert.Equal(100m, total);\n}`,
          points: [
            "الاختبار يفشل أولًا للسبب الصحيح.",
            "التنفيذ الأدنى يجعل السلوك واضحًا.",
            "الحالات تُضاف واحدة تلو الأخرى.",
            "Refactor آمن بعد الأخضر."
          ]
        },
        verdict: `<p>TDD ليس ضمانًا للجودة، لكنه يجبرك على تعريف السلوك قبل التنفيذ. استخدمه في المنطق المعقد والحدود، لا في كل سطر واجهة.</p>`
      },
      internals: `
        <p>مشغل xUnit يكتشف الاختبارات عبر reflection، ينشئ instance لكل test، وينفّذها. فشل compilation يمنع الاكتشاف كله. في دورة TDD، الفشل الأول قد يكون compile error، وهذا مقبول كخطوة حمراء إن كان يعبر عن العقد الجديد. لكن لا تخلط بين خطأ إعداد وفشل سلوك.</p>
        <p>Analyzers تعمل داخل Roslyn أثناء البناء. كل قاعدة لها ID وشدة قابلة للضبط في <code>.editorconfig</code> أو <code>.csproj</code>. <code>TreatWarningsAsErrors</code> يحوّل التحذيرات إلى أخطاء، ما قد يكسر البناء بعد تحديث SDK. ثبّت إصدار SDK في <code>global.json</code> وراجع القواعد عند الترقية.</p>
        <h3>Mutation Testing</h3>
        <p>الأداة تنشئ mutants: تغييرات صغيرة في الكود. إذا نجحت الاختبارات رغم التغيير، فالمutant حي، أي أن الاختبارات لا تكتشف هذا السلوك. النسبة <code>mutation score</code> تقيس القتلى. مكلفة لأنها تشغّل الاختبارات مرات كثيرة. استخدمها على الوحدات الحرجة فقط، مع timeout.</p>
        <h3>Quality Gate</h3>
        <p>بوابة CI الجيدة: build، analyzers، format، tests، فحص حزم، واختبارات تكامل. لا تجعل كل شيء شرطًا في كل commit إذا كان بطيئًا؛ افصل jobs. لكن لا تسمح بدمج يقلل التغطية أو يضيف تحذيرات. الجودة ثقافة، ليست أداة واحدة.</p>
      `,
      internalsTable: {
        head: ["الممارسة", "ماذا تمنع", "التكلفة"],
        rows: [
          ["Red first", "اختبارًا لا يفشل", "وقت كتابة أولي"],
          ["Minimal green", "over-engineering", "قد يبدو الكود بسيطًا"],
          ["Refactor", "تراكم التعقيد", "يحتاج انضباطًا"],
          ["Analyzers", "أنماطًا خطيرة", "ضوضاء إن لم تضبط"],
          ["Mutation", "اختبارات ضعيفة", "بطيء"],
          ["CI gate", "تراجع الجودة", "وقت بناء"]
        ]
      },
      tips: [
        {
          title: "اجعل الخطوة صغيرة",
          body: "اختبار واحد، تنفيذ واحد، refactor واحد. الخطوات الصغيرة تعطيك تغذية راجعة سريعة وتقلل التصميم الخاطئ."
        },
        {
          title: "لا تكتب abstraction مبكرًا",
          body: "أضف الواجهة عندما يطلبها اختبار أو تغيير حقيقي. التجريد قبل الحاجة يزيد التعقيد بلا فائدة."
        },
        {
          title: "اضبط التحذيرات تدريجيًا",
          body: "ابدأ بالقواعد الموصى بها، وأصلح القديم بالتدريج. لا تطفئ قاعدة بلا سبب موثق."
        },
        {
          title: "استخدم Mutation للحرج",
          body: "الأسعار والصلاحيات والمعاملات تستحق اختبارات قوية. لا تستهلك وقت CI كله في mutation لكل ملف."
        }
      ],
      quiz: [
        {
          q: "ما الخطوة الأولى في TDD؟",
          options: [
            "كتابة التنفيذ الكامل.",
            "كتابة اختبار يفشل للسبب الصحيح.",
            "إعادة تسمية الملفات.",
            "قياس التغطية."
          ],
          answer: 1,
          explain: "تبدأ باختبار أحمر يصف السلوك. إذا لم يفشل، فلا يثبت أن الميزة كانت ناقصة."
        },
        {
          q: "لماذا نكتب أقل كود في الخطوة الخضراء؟",
          options: [
            "لتقليل جودة الكود.",
            "لتجنب بناء حالات/تجريدات لم يطلبها اختبار.",
            "لأن الاختبارات لا تحتاج تنفيذًا.",
            "لتسريع CI فقط."
          ],
          answer: 1,
          explain: "أقل تنفيذ يجعل كل سطر مبررًا ويمنع over-engineering. تُضاف الحالات لاحقًا باختبارات."
        },
        {
          q: "ما الفرق بين Coverage وMutation Testing؟",
          options: [
            "لا فرق.",
            "Coverage يقيس التنفيذ، Mutation يختبر إن كانت الاختبارات تكتشف تغيير السلوك.",
            "Mutation أسرع دائمًا.",
            "Coverage يختبر الإنتاج."
          ],
          answer: 1,
          explain: "التغطية لا تضمن قوة Assertions. Mutation يغيّر الكود ويرى هل تفشل الاختبارات."
        }
      ],
      capstone: {
        title: "جودة Souq في CI",
        goal: "طبّق TDD على قاعدة خصم، وفعّل Analyzers وبوابة جودة تمنع التراجع.",
        tasks: [
          "اكتب اختبارًا فاشلًا لقاعدة كوبون منتهي ثم نفّذها بأقل كود.",
          "أضف اختبارًا للحالة الصحيحة والحد الأدنى للطلب.",
          "فعّل <code>AnalysisLevel</code> و<code>TreatWarningsAsErrors</code> في مشروع المكتبة.",
          "أضف <code>dotnet format --verify-no-changes</code> و<code>dotnet test</code> إلى CI.",
          "شغّل فحص تغطية على وحدة السعر وأضف اختبارًا لفرع غير مغطى."
        ],
        code: {
          lang: "xml",
          title: "إعداد الجودة",
          code: `<PropertyGroup>\n  <AnalysisLevel>latest-recommended</AnalysisLevel>\n  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n  <Nullable>enable</Nullable>\n</PropertyGroup>`,
        },
      },
    },
    {
      id: "load-testing",
      title: "Load Testing: قِس قبل أن تُحسّن",
      duration: 30,
      level: "متقدم",
      summary:
        "الاختبار الوظيفي يقول «يعمل»، والأداء يقول «يعمل تحت الحمل». سنقيس throughput وp95 وp99، ونفهم لماذا المتوسط يكذب.",
      keywords: ["k6", "NBomber", "BenchmarkDotNet", "p95", "p99", "throughput", "SLO", "profiling"],
      objectives: [
        "تحدد SLO وحملًا واقعيًا قبل القياس.",
        "تكتب سيناريو k6 مع ramp-up وthresholds.",
        "تفسر p95/p99 وthroughput ومعدل الأخطاء.",
        "تستخدم BenchmarkDotNet للكود الساخن.",
        "تحدد الاختناق قبل تغيير الكود."
      ],
      concept: `
        <p><strong>Load Testing</strong> ليس «شغّل 1000 طلب وشاهد إن نجح». هو تجربة محددة: ما الحمل المتوقع؟ ما نسبة القراءة/الكتابة؟ ما SLO؟ ما البيئة؟ بدون هذه الأسئلة، النتائج أرقام بلا معنى. ابدأ من تجربة المستخدم: 95% من طلبات المنتجات أقل من 300ms، ومعدل الأخطاء أقل من 1% تحت 200 مستخدم متزامن.</p>
        <h3>المتوسط يكذب</h3>
        <p>متوسط 100ms قد يخفي 5% من الطلبات عند ثانية. استخدم <strong>p95</strong> و<strong>p99</strong>: 95% من الطلبات أسرع من القيمة. p99 يكشف الذيل الذي يعاني منه المستخدمون. راقب أيضًا الحد الأقصى وعدد الطلبات المرفوضة. لا تقدم تقريرًا بمتوسط فقط.</p>
        <h3>Throughput والتشبع</h3>
        <p>Throughput هو عدد الطلبات الناجحة في الثانية. قد يزيد حتى نقطة تشبع ثم ينهار. راقب CPU، الذاكرة، اتصالات قاعدة البيانات، وqueue length. إذا كان الخادم مشبعًا، إضافة حمل لا تزيد الإنتاجية بل تزيد الزمن. ابحث عن العنق: قاعدة البيانات، serialization، قفل، GC، أو شبكة.</p>
        <h3>Open vs Closed Model</h3>
        <p>في النموذج المغلق، كل مستخدم افتراضي ينتظر الاستجابة قبل إرسال التالي. في المفتوح، يرسل بمعدل ثابت حتى لو تأخر الخادم. النموذج المفتوح قد يكشف الانهيار تحت الحمل الحقيقي. اختر حسب نمط المستخدمين. وثّق النموذج؛ النتائج غير قابلة للمقارنة بدونه.</p>
        <h3>BenchmarkDotNet مقابل Load Test</h3>
        <p>BenchmarkDotNet يقيس method صغيرة بدقة، مع warmup وإحصاءات. Load Test يقيس النظام كاملًا عبر HTTP. لا تستخدم BenchmarkDotNet لقياس endpoint فيه قاعدة بيانات وشبكة. استخدمه للكود الساخن بعد أن يحدد load test المكان. الاثنان أدوات مختلفة.</p>
        <h3>البيئة والبيانات</h3>
        <p>اختبر على بيئة تشبه الإنتاج: نفس قاعدة البيانات تقريبًا، نفس عدد النسخ، نفس الإعدادات. لا تختبر على جهازك مع 10 صفوف وتعمم. استخدم بيانات واقعية الحجم، وخذ baseline قبل التغيير. لا تشغّل الحمل على الإنتاج دون موافقة وخطة.</p>
      `,
      walkthrough: [
        {
          title: "حدد SLO والحمولة",
          code: `SLO:\n- p95 < 300ms لـGET /api/v1/products\n- معدل الأخطاء < 1%\n- 200 مستخدم متزامن\n- 70% قراءة / 30% كتابة`,
          lang: "text",
          body: `<p>اكتب هذا قبل الأداة. SLO يحدد النجاح، والحمولة تحدد السيناريو. بدون نسبة القراءة/الكتابة قد تختبر نظامًا مختلفًا. حدد أيضًا مدة الاختبار وfترة ramp-up. إذا لم تعرف الحمل، ابدأ من بيانات الإنتاج أو توقعات العمل، لا من رقم عشوائي.</p>`
        },
        {
          title: "اكتب سيناريو k6",
          code: `import http from "k6/http";\nimport { check, sleep } from "k6";\n\nexport const options = {\n  stages: [\n    { duration: "1m", target: 50 },\n    { duration: "3m", target: 200 },\n    { duration: "1m", target: 0 }\n  ],\n  thresholds: {\n    http_req_duration: ["p(95)<300"],\n    http_req_failed: ["rate<0.01"]\n  }\n};\n\nexport default function () {\n  const res = http.get("https://staging.souq.example/api/v1/products");\n  check(res, { "status 200": (r) => r.status === 200 });\n  sleep(1);\n}`,
          lang: "javascript",
          body: `<p><code>stages</code> يصعد تدريجيًا إلى 200 ثم يهبط. <code>thresholds</code> يجعل الاختبار يفشل إذا تجاوز p95 أو معدل الخطأ. <code>check</code> يتحقق من الحالة، لكنه لا يوقف السيناريو. <code>sleep(1)</code> يحاكي تفكير المستخدم؛ بدونه قد تولّد حملًا غير واقعي. عدّل المسار والبيانات حسب staging.</p>`
        },
        {
          title: "شغّل الاختبار",
          code: `k6 run load/products.js`,
          lang: "bash",
          body: `<p>k6 يعرض p95 وp99 وthroughput ومعدل الفشل. لا تنظر إلى المتوسط فقط. راقب أيضًا <code>http_req_waiting</code> (time to first byte) و<code>http_req_connecting</code>. إذا فشل threshold، لا ترفع الحدود؛ افهم السبب. احفظ النتيجة كـbaseline للمقارنة.</p>`
        },
        {
          title: "راقب الخادم أثناء الحمل",
          code: `dotnet-counters monitor -n Souq.Api \\\n  --counters System.Runtime,Microsoft.AspNetCore.Hosting`,
          lang: "bash",
          body: `<p>راقب CPU، GC heap، exceptions/sec، وعدد الطلبات. <code>dotnet-counters</code> يعطي صورة سريعة. إذا كان CPU منخفضًا والزمن مرتفعًا، فالعنق قد يكون قاعدة بيانات أو I/O أو قفلًا. إذا كان GC متكررًا، فقد يكون allocation. لا تحسّن بناءً على الحدس.</p>`
        },
        {
          title: "حلل توزيع الزمن",
          code: `# k6 summary\nhttp_req_duration........: avg=120ms p(90)=210ms p(95)=280ms p(99)=900ms\nhttp_req_failed..........: 0.40%\nhttp_reqs................: 24000  80/s`,
          lang: "text",
          body: `<p>p95 جيد لكن p99 = 900ms، أي أن 1% من المستخدمين ينتظرون قرابة ثانية. ابحث عن الطلبات البطيئة: هل هي كتابة؟ هل تزامن قاعدة بيانات؟ هل GC؟ المتوسط 120ms كان سيخفي المشكلة. اربط p99 بعدد الطلبات ونوعها.</p>`
        },
        {
          title: "قِس method ساخنة",
          code: `[MemoryDiagnoser]\npublic class PricingBenchmarks\n{\n    private readonly PricingService _service = new();\n\n    [Benchmark]\n    public decimal Calculate() =>\n        _service.CalculateTotal(19.99m, 3, 0.10m);\n}`,
          lang: "csharp",
          body: `<p>BenchmarkDotNet يشغّل warmup ثم قياسات متعددة ويقدم إحصاءات. <code>MemoryDiagnoser</code> يعرض allocations. استخدمه للكود الحسابي الساخن، لا لـendpoint كامل. لا تقارن نتائج من أجهزة مختلفة. ثبّت الإعدادات وأعد التشغيل قبل الاعتماد.</p>`
        },
        {
          title: "اختبر النموذج المفتوح",
          code: `export const options = {\n  scenarios: {\n    constant_rate: {\n      executor: "constant-arrival-rate",\n      rate: 100,\n      timeUnit: "1s",\n      duration: "5m",\n      preAllocatedVUs: 50,\n      maxVUs: 200\n    }\n  }\n};`,
          lang: "javascript", 
          body: `<p>هذا النموذج يرسل 100 طلب/ث بغض النظر عن زمن الاستجابة، ما يكشف التشبع. راقب <code>dropped_iterations</code>؛ إذا زاد، فالنظام لا يستطيع مواكبة المعدل. النموذج المغلق قد يخفي ذلك لأن المستخدمين ينتظرون. اختر النموذج حسب واقع المستخدمين.</p>`
        },
        {
          title: "حسّن عنقًا واحدًا وأعد القياس",
          code: `// قبل: استعلام بلا فهرس + تحميل كل الأعمدة\n// بعد: إسقاط DTO + فهرس (IsActive, Name)\nawait _db.Products.AsNoTracking()\n    .Where(p => p.IsActive)\n    .OrderBy(p => p.Name).ThenBy(p => p.Id)\n    .Select(p => new ProductDto(p.Id, p.Name, p.Price))\n    .Take(50)\n    .ToListAsync(ct);`,
          lang: "csharp",
          body: `<p>غيّر شيئًا واحدًا ثم أعد نفس الاختبار. إذا حسّنت شيئين معًا، لن تعرف أيهما أفاد. ابدأ بالاستعلامات والفهارس، ثم serialization، ثم GC. لا تضف cache قبل فهم الحمل؛ قد يخفي المشكلة. قارن p95/p99 وthroughput، لا الإحساس.</p>`
        },
        {
          title: "وثّق النتيجة والقرار",
          code: `Baseline: p95 280ms, p99 900ms, 80 req/s\nAfter index+projection: p95 140ms, p99 250ms, 150 req/s\nDecision: اعتماد التغيير، مراقبة p99 أسبوعيًا.`,
          lang: "text",
          body: `<p>التقرير يجب أن يذكر البيئة والحمولة والإعداد والتغيير. بدون ذلك لا يمكن تكرار النتيجة. اربطها بـSLO، وحدد ما إذا كان التحسين كافيًا. راقب الإنتاج بعد النشر؛ الحمل الحقيقي قد يختلف. الأداء عملية مستمرة، لا رقم لمرة واحدة.</p>`
        }
      ],
      compare: {
        intro: `<p>قياس متوسط طلب واحد لا يخبرك كيف يتصرف النظام تحت الحمل.</p>`,
        before: {
          label: "قياس ساذج",
          lang: "bash",
          title: "قبل",
          code: `time curl http://localhost:5000/api/products\n# avg 80ms -> "سريع!"`,
          points: [
            "طلب واحد لا يمثل الحمل.",
            "المتوسط يخفي الذيل.",
            "لا قاعدة بيانات واقعية.",
            "لا يراقب التشبع أو الأخطاء."
          ]
        },
        after: {
          label: "اختبار حمل محدد",
          lang: "javascript",
          title: "بعد",
          code: `export const options = {\n  stages: [{ duration: "3m", target: 200 }],\n  thresholds: {\n    http_req_duration: ["p(95)<300", "p(99)<800"],\n    http_req_failed: ["rate<0.01"]\n  }\n};`,
          points: [
            "حمل متدرج ومدة كافية.",
            "SLO واضح لـp95/p99.",
            "معدل أخطاء كشرط فشل.",
            "قابل للتكرار على staging."
          ]
        },
        verdict: `<p>الأداء يُقاس بسيناريو وSLO، لا برقم واحد. راقب الذيل والتشبع، وحسّن عنقًا واحدًا في كل مرة.</p>`
      },
      internals: `
        <p>زمن الاستجابة توزيع، لا رقم. p95 يعني أن 95% من الطلبات أسرع من القيمة. p99 يكشف الذيل. المتوسط يتأثر بالقيم الشاذة وقد يخفي أن 10% من المستخدمين يعانون. استخدم أيضًا histogram وmax. راقب الأخطاء والطلبات المرفوضة، لأن استبعادها من المتوسط يجعل النتيجة تبدو أفضل كذبًا.</p>
        <p><strong>Coordinated omission</strong> يحدث عندما يتأخر مولّد الحمل بسبب انتظار الاستجابة، فلا يرسل الطلبات التي كان المستخدم سيرسلها. النموذج المفتوح يقلل ذلك. وثّق عدد المستخدمين الافتراضيين ومعدل الإرسال. لا تقارن نتائج أدوات/نماذج مختلفة مباشرة.</p>
        <h3>ما بعد HTTP</h3>
        <p>قد يكون العنق في connection pool، أو قفل قاعدة بيانات، أو GC، أو thread pool. <code>dotnet-counters</code> و<code>dotnet-trace</code> وOpenTelemetry تساعد. لا ترفع <code>MaxPoolSize</code> بلا قياس؛ قد تزيد التزاحم. لا ترفع timeout لتخفي البطء. ابحث عن السبب.</p>
        <h3>البيئة</h3>
        <p>CPU/الذاكرة/الشبكة في staging يجب أن تشبه الإنتاج. إذا كانت staging أضعف، النتائج متحفظة؛ إن كانت أقوى، مضللة. استخدم نفس صورة Docker وإعدادات Kestrel. لا تشغّل اختبار الحمل على جهاز تطوير مع قاعدة بيانات محلية. وثّق الفروق.</p>
      `,
      internalsTable: {
        head: ["المقياس", "المعنى", "التحذير"],
        rows: [
          ["p95", "95% أسرع من القيمة", "لا يظهر أسوأ 5%"],
          ["p99", "99% أسرع من القيمة", "يكشف الذيل"],
          ["Throughput", "طلبات ناجحة/ث", "قد ينهار بعد التشبع"],
          ["Error rate", "نسبة الفشل", "يجب أن يكون شرط فشل"],
          ["GC/CPU", "صحة العملية", "اربطه بالحمل"],
          ["Dropped iterations", "حمل لم يُرسل", "يكشف تشبع المولد"]
        ]
      },
      tips: [
        {
          title: "ابدأ بـSLO",
          body: "حدد p95/p99 ومعدل الأخطاء والحمل قبل الأداة. بدون هدف، كل رقم يبدو مقبولًا أو سيئًا بلا معنى."
        },
        {
          title: "لا تستخدم المتوسط",
          body: "اعرض p95 وp99 والحد الأقصى. الذيل هو ما يشعر به المستخدمون، خاصة في الدفع والطلبات."
        },
        {
          title: "غيّر شيئًا واحدًا",
          body: "أعد نفس الاختبار بعد كل تحسين. إذا غيّرت الفهرس والcache معًا، لن تعرف السبب."
        },
        {
          title: "اختبر بيئة واقعية",
          body: "نفس قاعدة البيانات والنسخ والإعدادات. لا تعمم نتيجة جهاز محلي على الإنتاج."
        }
      ],
      quiz: [
        {
          q: "ماذا يعني p95 = 300ms؟",
          options: [
            "كل الطلبات 300ms.",
            "95% من الطلبات أسرع من 300ms.",
            "5% من الطلبات أسرع من 300ms.",
            "متوسط الزمن 300ms."
          ],
          answer: 1,
          explain: "p95 هو percentile 95: 95% من القياسات أقل من القيمة. لا يخبرك عن أسوأ 5%."
        },
        {
          q: "لماذا النموذج المفتوح مهم؟",
          options: [
            "لأنه أسرع دائمًا.",
            "يكشف التشبع عندما لا يستطيع النظام مواكبة معدل الوصول.",
            "لأنه لا يحتاج بيانات.",
            "ليقلل عدد الطلبات."
          ],
          answer: 1,
          explain: "constant-arrival-rate يرسل بمعدل ثابت بغض النظر عن الاستجابة، فيظهر dropped iterations والتشبع."
        },
        {
          q: "متى تستخدم BenchmarkDotNet؟",
          options: [
            "لاختبار endpoint كامل مع قاعدة بيانات.",
            "لقياس method صغيرة/ساخنة بدقة.",
            "لاختبار واجهة المستخدم.",
            "لنشر التطبيق."
          ],
          answer: 1,
          explain: "BenchmarkDotNet للكود المحلي الساخن. Load test لل نظام الكامل عبر HTTP."
        }
      ],
      capstone: {
        title: "قياس أداء Souq",
        goal: "أنشئ baseline لـGET products، حدد عنقًا، وحسّنه مع دليل قبل/بعد.",
        tasks: [
          "حدد SLO لـp95/p99 ومعدل الأخطاء وعدد المستخدمين.",
          "اكتب سيناريو k6 مع stages وthresholds لـ<code>/api/v1/products</code>.",
          "شغّل الاختبار على staging وسجّل p95 وp99 وthroughput.",
          "راقب <code>dotnet-counters</code> وحدد عنقًا واحدًا (استعلام/فهرس/GC).",
          "طبّق تحسينًا واحدًا وأعد القياس، ووثّق النتيجة قبل/بعد."
        ],
        code: {
          lang: "javascript",
          title: "thresholds",
          code: `thresholds: {\n  http_req_duration: ["p(95)<300", "p(99)<800"],\n  http_req_failed: ["rate<0.01"]\n}`,
        },
      },
    },
  ],
});
