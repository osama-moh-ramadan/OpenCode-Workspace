/* الوحدة 6 — Architecture وEF Core: الحدود، التتبّع، والأداء. */
Academy.addModule({
  id: "architecture",
  title: "Architecture & Data",
  tagline: "لا تبنِ قصرًا من طبقات قبل أن تحتاجها. لكن عندما تحتاجها، اجعل الحدود صلبة والاستعلامات سريعة.",
  icon: "▤",
  color: "#fbbf24",
  lessons: [
    {
      id: "efcore-modeling",
      title: "EF Core Modeling: من الكائن إلى الجدول",
      duration: 28,
      level: "متوسط",
      summary:
        "قاعدة البيانات ليست تفصيلًا لاحقًا. قرارات المفاتيح والعلاقات والفهارس والقيود تحدد صحة التطبيق وأداءه. سنحوّل نموذج المجال إلى مخطط واضح وقابل للتطور.",
      keywords: ["EF Core", "DbContext", "IEntityTypeConfiguration", "relationships", "indexes", "migrations", "concurrency", "decimal precision"],
      objectives: [
        "تفرّق بين نموذج المجال ونموذج التخزين.",
        "تضبط المفاتيح والعلاقات والقيود صراحةً بدل الاعتماد على الاصطلاحات.",
        "تختار الفهارس المناسبة وتشرح تكلفتها.",
        "تستخدم migrations لتطوير المخطط بأمان.",
        "تفهم optimistic concurrency ودور row version."
      ],
      concept: `
        <p>EF Core ليس «ORM يحفظ الكائنات» فقط. هو طبقة تحويل بين نموذج C# ومخطط علائقي: جداول، أعمدة، مفاتيح، علاقات، فهارس، وقيود. كل قرار في النموذج يتحول إلى SQL عند التشغيل أو إلى migration عند التطوير. إذا تركت كل شيء للاصطلاحات، ستحصل على مخطط يعمل ولكن قد يكون ضعيفًا في القيود والأداء.</p>
        <h3>نموذج المجال مقابل نموذج التخزين</h3>
        <p>في Domain Model قد يكون السعر قيمة <code>Money</code>، والحالة enum، والعنوان value object. في قاعدة البيانات قد يصبح السعر عمودين (amount/currency)، والحالة نصًا أو int، والعنوان أعمدة مدمجة. لا تخلط بين الاثنين: الكيان يحمي قواعد العمل، والتكوين يحدد كيف يُخزَّن. أحيانًا تستخدم owned types أو value converters لتقريب المسافة، لكن لا تجعل قاعدة البيانات تملي كل تفاصيل المجال.</p>
        <h3>المفاتيح والعلاقات</h3>
        <p>اختر مفتاحًا مستقرًا. <code>Guid</code> مناسب للمعرّفات المولّدة ويسهّل التوزيع، لكنه أكبر من int ويؤثر على الفهارس. المفتاح المركّب مفيد لجدول ربط many-to-many. العلاقة one-to-many تُعرّف بـ<code>HasOne/WithMany/HasForeignKey</code>. حدد <code>OnDelete</code> بوضوح: <code>Cascade</code> قد يحذف بيانات كثيرة بالخطأ؛ <code>Restrict</code> يجبرك على قرار صريح. لا تترك الحذف للاصطلاح.</p>
        <h3>القيود والفهارس</h3>
        <p>القيد الفريد على SKU أو البريد يمنع التكرار تحت التزامن، وهو أفضل من فحص «هل موجود؟» ثم إدراج. الفهرس يسرّع القراءة لكنه يبطئ الكتابة ويستهلك مساحة. أضف فهرسًا لعمود تستخدمه في <code>WHERE</code> أو <code>ORDER BY</code> أو <code>JOIN</code> بشكل متكرر، لا لكل عمود. الفهرس المركّب يفيد إذا كان ترتيب أعمدته يطابق الاستعلام. راجع خطط التنفيذ قبل إضافة فهارس عشوائية.</p>
        <h3>الدقة والأنواع</h3>\n        <p><code>decimal(18,2)</code> يعني 18 رقمًا إجمالًا ومنزلتين عشريتين. حدد الدقة لكل سعر وكمية ونسبة؛ الافتراضي قد يقطع القيم أو يخزنها بشكل غير متوقع. لا تستخدم <code>double</code> للمال. التواريخ استخدم <code>DateTimeOffset</code> أو UTC بوضوح، لا تخلط المناطق الزمنية. النصوص <code>nvarchar(max)</code> بلا طول قد تمنع الفهارس وتسبب أداءً سيئًا؛ حدد أطوالًا واقعية.</p>\n        <h3>Migrations ليست زرًا سحريًا</h3>\n        <p>كل migration ملف C# يصف تغيير المخطط. راجعه قبل التطبيق: هل يحذف عمودًا؟ هل يعيد بناء جدول كبير؟ هل يحتاج migration بيانات منفصلة؟ في الإنتاج، لا تشغّل <code>database update</code> تلقائيًا عند بدء كل نسخة إن كان هناك عدة replicas. استخدم خطوة نشر واحدة، أو أداة migrations، أو SQL مراجع. احتفظ بنسخة احتياطية وخطة rollback.</p>\n        <h3>التزامن</h3>\n        <p>إذا عدّل مستخدمان نفس الصف، قد يكتب الثاني فوق الأول. <strong>Optimistic concurrency</strong> يستخدم <code>rowversion</code> أو <code>ConcurrencyToken</code>: القراءة تحمل النسخة، والكتابة تشترط أن تكون لم تتغير. إذا تغيرت، يرمي EF Core <code>DbUpdateConcurrencyException</code>، فتقرر: إعادة تحميل، دمج، أو 409. هذا أفضل من قفل pessimist دائم يقلل التزامن.</p>\n      `,
      walkthrough: [
        {
          title: "كيان المنتج",
          code: `public sealed class Product
{
    public Guid Id { get; set; }
    public required string Name { get; set; }
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public required string Sku { get; set; }
    public Guid CategoryId { get; set; }
    public Category Category { get; set; } = null!;
    public ProductStatus Status { get; set; }
    public bool IsDeleted { get; set; }
    public byte[] RowVersion { get; set; } = Array.Empty<byte>();
}`,
          lang: "csharp",
          body: `<p>هذا كيان تخزين قابل للتعديل، وليس DTO. <code>required</code> يفرض الاسم وSKU عند الإنشاء في C#، لكنه لا يفرضهما في قاعدة البيانات؛ التكوين يفعل ذلك. <code>Category</code> مرجع تنقّل، و<code>CategoryId</code> مفتاح أجنبي. <code>Status</code> enum و<code>IsDeleted</code> للحذف المنطقي. <code>RowVersion</code> سيُستخدم للتزامن التفاؤلي.</p>`
        },
        {
          title: "الطرف الآخر للعلاقة",
          code: `public sealed class Category
{
    public Guid Id { get; set; }
    public required string Name { get; set; }
    public ICollection<Product> Products { get; } = new List<Product>();
}`,
          lang: "csharp",
          body: `<p><code>ICollection&lt;Product&gt;</code> مجموعة تنقّل. EF Core يستطيع ملءها عند التحميل، لكن لا تفترض أنها محمّلة دائمًا. لا تجعلها <code>List</code> عامًا قابلًا للاستبدال؛ واجهة للقراءة مع تهيئة داخلية أفضل. العلاقة one-to-many تُكوَّن من جهة المنتج بـ<code>HasOne/WithMany</code>.</p>`
        },
        {
          title: "DbContext وDbSet",
          code: `public sealed class AppDbContext(
    DbContextOptions<AppDbContext> options)
    : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);
    }
}`,
          lang: "csharp",
          body: `<p><code>DbContext</code> يمثل جلسة عمل مع قاعدة البيانات: change tracker، اتصال منطقي، وترجمة استعلامات. <code>DbSet</code> نقطة بداية الاستعلام. <code>ApplyConfigurationsFromAssembly</code> يطبّق كل <code>IEntityTypeConfiguration</code>، فيبقى <code>OnModelCreating</code> نظيفًا. لا تضع منطق أعمال في الـ DbContext؛ هو مسؤولية persistence.</p>`
        },
        {
          title: "تكوين صريح للجدول والمفتاح",
          code: `public sealed class ProductConfiguration
    : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.ToTable("Products");
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Name)
            .HasMaxLength(120)
            .IsRequired();
    }
}`,
          lang: "csharp",
          body: `<p><code>ToTable</code> يثبت اسم الجدول، <code>HasKey</code> يثبت المفتاح، و<code>HasMaxLength</code> ينتج <code>nvarchar(120)</code> بدل <code>max</code>. <code>IsRequired</code> ينتج <code>NOT NULL</code>. هذه القيود تحمي البيانات من أي مسار، لا من الـ API فقط. التكوين الصريح يجعل المخطط مرئيًا في الكود بدل تخمين الاصطلاحات.</p>`
        },
        {
          title: "دقة السعر",
          code: `builder.Property(p => p.Price)
    .HasPrecision(18, 2)
    .IsRequired();`,
          lang: "csharp",
          body: `<p><code>HasPrecision(18, 2)</code> ينتج عمودًا مثل <code>decimal(18,2)</code>: 16 رقمًا قبل الفاصلة ومنزلتان بعدها. مناسب لأسعار معظم المتاجر. إن كنت تحتاج عملات بثلاث منازل أو مبالغ كبيرة، اختر دقة مختلفة ووثّقها. لا تترك EF يستنتج نوعًا افتراضيًا قد يختلف بين موفري قواعد البيانات.</p>`
        },
        {
          title: "فهرس فريد للـSKU",
          code: `builder.Property(p => p.Sku)
    .HasMaxLength(40)
    .IsRequired();

builder.HasIndex(p => p.Sku).IsUnique();`,
          lang: "csharp",
          body: `<p>الفهرس الفريد يمنع تكرار SKU حتى لو أرسل عميلان الطلب في نفس اللحظة. الفحص في الكود وحده لا يكفي بسبب race condition. عند محاولة إدراج مكرر، ترمي قاعدة البيانات استثناءً؛ حوّله إلى 409 برسالة آمنة. الفهرس يسرّع البحث بالـSKU أيضًا، لكنه يضيف تكلفة كتابة صغيرة.</p>`
        },
        {
          title: "علاقة مع منع الحذف المتسلسل",
          code: `builder.HasOne(p => p.Category)
    .WithMany(c => c.Products)
    .HasForeignKey(p => p.CategoryId)
    .OnDelete(DeleteBehavior.Restrict);`,
          lang: "csharp",
          body: `<p><code>HasOne/WithMany</code> يحدد العلاقة، و<code>HasForeignKey</code> يثبت العمود. <code>Restrict</code> يمنع حذف تصنيف مرتبط بمنتجات، فيجبرك على نقل المنتجات أو تعطيلها أولًا. <code>Cascade</code> قد يحذف كل منتجات التصنيف بضغطة واحدة؛ لا تستخدمه بلا وعي. اختر السلوك حسب قواعد العمل ووثّقه.</p>`
        },
        {
          title: "تحويل enum وفلتر عام",
          code: `builder.Property(p => p.Status)
    .HasConversion<string>()
    .HasMaxLength(20);

builder.HasQueryFilter(p => !p.IsDeleted);`,
          lang: "csharp",
          body: `<p><code>HasConversion&lt;string&gt;</code> يخزّن الحالة كنص مقروء بدل رقم غامض، لكنه يستهلك مساحة أكبر. <code>HasQueryFilter</code> يخفي المحذوف منطقيًا من كل استعلام افتراضيًا. تذكّر أن الفلتر يؤثر على العلاقات وعلى <code>IgnoreQueryFilters</code>؛ استخدمه بوعي. الحذف المنطقي يحتاج فهرسًا على <code>IsDeleted</code> أو فلترًا جزئيًا حسب قاعدة البيانات.</p>`
        },
        {
          title: "تزامن تفاؤلي",
          code: `builder.Property(p => p.RowVersion)
    .IsRowVersion();`,
          lang: "csharp",
          body: `<p><code>IsRowVersion</code> يجعل العمود token يتغير تلقائيًا عند التحديث (حسب الموفر). عند الحفظ، يضيف EF Core شرطًا مثل <code>WHERE Id = @id AND RowVersion = @old</code>. إذا كان عدد الصفوف المتأثرة صفرًا، يرمي <code>DbUpdateConcurrencyException</code>. لا تلتقطه وتتجاهله؛ أعد المحاولة أو أعد 409.</p>`
        },
        {
          title: "أنشئ migration وراجعها",
          code: `dotnet ef migrations add InitialCreate
dotnet ef database update`,
          lang: "bash",
          body: `<p><code>migrations add</code> يقارن النموذج بقاعدة البيانات الحالية وينتج ملف C# قابلًا للمراجعة. اقرأ الملف قبل التطبيق: هل الأعمدة الجديدة nullable؟ هل هناك فقد بيانات؟ <code>database update</code> يطبّق migrations على قاعدة التطوير. في الإنتاج، لا تشغّله من كل نسخة تطبيق؛ استخدم خطوة نشر واحدة وأبقِ نسخة احتياطية.</p>`
        }
      ],
      compare: {
        intro: `<p>نموذجان يبدوان متشابهين في C#، لكن أحدهما يترك قاعدة البيانات بلا قيود والآخر يحميها.</p>`,
        before: {
          label: "اصطلاحات بلا قيود",
          lang: "csharp",
          title: "قبل",
          code: `public class Product
{
    public int Id { get; set; }
    public string Sku { get; set; }
    public double Price { get; set; }
    public string Status { get; set; }
    public Category Category { get; set; }
}`,
          points: [
            "SKU قد يتكرر بلا قيد فريد.",
            "double يسبب أخطاء تقريب في السعر.",
            "الحالة نص حر بلا قيم محددة.",
            "العلاقة قد تحذف cascade بلا قرار."
          ]
        },
        after: {
          label: "مخطط صريح",
          lang: "csharp",
          title: "بعد",
          code: `public sealed class ProductConfiguration
    : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> b)
    {
        b.HasKey(p => p.Id);
        b.Property(p => p.Sku)
            .HasMaxLength(40).IsRequired();
        b.HasIndex(p => p.Sku).IsUnique();
        b.Property(p => p.Price)
            .HasPrecision(18, 2);
        b.Property(p => p.Status)
            .HasConversion<string>().HasMaxLength(20);
        b.HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}`,
          points: [
            "SKU فريد ومحدد الطول.",
            "السعر بدقة عشرية.",
            "الحالة محصورة في enum.",
            "حذف التصنيف لا يمسح المنتجات."
          ]
        },
        verdict: `<p>التكوين الصريح ليس حشوًا؛ هو عقد بين التطبيق وقاعدة البيانات. اجعله في ملفات منفصلة لكل كيان، وراجعه مع migration في نفس الـ PR.</p>`
      },
      internals: `
        <p>عند بدء التطبيق، يبني EF Core <strong>model</strong>: كيانات، خصائص، مفاتيح، علاقات، محولات، وفهارس. هذا النموذج يُخزَّن ويُعاد استخدامه. في التطوير قد يُبنى عند أول استخدام، وفي الإنتاج يمكن استخدام compiled model لتقليل وقت البدء. أي تغيير في التكوين يحتاج migration وإعادة بناء النموذج.</p>
        <p><strong>Change Tracker</strong> يحتفظ بمراجع الكيانات وقيمها الأصلية. عند <code>SaveChanges</code> يقارن القيم الحالية بالأصلية وينتج INSERT/UPDATE/DELETE. هذا سبب أهمية <code>AsNoTracking</code> للقراءة: يقلل الذاكرة وعمل المقارنة. التتبع ليس عيبًا؛ هو ضروري للتعديل، لكنه مكلف عندما لا تحتاجه.</p>
        <p>العلاقات تُترجم إلى مفاتيح أجنبية وقيود. <code>Include</code> ينتج JOIN أو استعلامات إضافية. كثير من العلاقات المتداخلة قد ينتج <strong>cartesian explosion</strong>؛ <code>AsSplitQuery</code> يفصلها بتكلفة رحلات إضافية. لا تحل مشكلة الأداء بـInclude أكثر؛ قِس SQL أولًا.</p>
        <h3>Migrations والبيانات الحقيقية</h3>
        <p>Migration يصف تغيير المخطط، لكنه لا يعرف كيف تملأ عمودًا جديدًا غير nullable في جدول كبير. أضف العمود nullable، املأ البيانات على دفعات، ثم اجعله NOT NULL في migration لاحق. لا تجعل migration يمسح بيانات «لتنظيف» الجدول. اختبر migrations على نسخة تشبه الإنتاج، لا على قاعدة فارغة فقط.</p>
        <h3>الفهارس والقيود</h3>
        <p>الفهرس B-tree يسرّع البحث والترتيب والربط، لكنه يستهلك مساحة ويبطئ INSERT/UPDATE. الفهرس المركب يفيد إذا استخدمت الأعمدة بترتيب البادئة. الفهرس الفريد قيد صحة وأداء معًا. راقب الاستعلامات البطيئة وخطط التنفيذ؛ لا تضف فهرسًا لكل عمود «احتياطًا».</p>
      `,
      internalsTable: {
        head: ["العنصر", "ماذا يفعل", "تكلفة/تحذير"],
        rows: [
          ["HasKey", "يحدد المفتاح الأساسي", "مفتاح كبير يؤثر على الفهارس"],
          ["HasIndex", "يسرّع البحث/الترتيب", "يبطئ الكتابة ويستهلك مساحة"],
          ["HasPrecision", "يضبط دقة decimal", "دقة خاطئة تقطع القيم"],
          ["OnDelete", "يحدد سلوك حذف العلاقة", "Cascade قد يحذف بيانات واسعة"],
          ["IsRowVersion", "تزامن تفاؤلي", "يتطلب معالجة DbUpdateConcurrencyException"],
          ["HasQueryFilter", "يخفي صفوفًا افتراضيًا", "قد يخفي بيانات في تقارير"]
        ]
      },
      tips: [
        {
          title: "اكتب التكوين صراحةً",
          body: "استخدم <code>IEntityTypeConfiguration</code> لكل كيان. حدد الجدول والمفتاح والأطوال والدقة والعلاقات. الاصطلاحات جيدة للبداية، لكنها لا تكفي لعقد إنتاجي."
        },
        {
          title: "اجعل القيود في قاعدة البيانات",
          body: "الفهرس الفريد والمفتاح الأجنبي وNOT NULL تحمي من أي مسار، حتى السكربتات اليدوية. لا تعتمد على تحقق الـ API وحده."
        },
        {
          title: "راجع كل migration",
          body: "افتح ملف migration واقرأ SQL. اختبره على بيانات حقيقية. لا تطبّق migrations تلقائيًا من كل replica، وضع خطة rollback."
        },
        {
          title: "لا تعِد الكيان للعميل",
          body: "الكيان يحمل تفاصيل التخزين والتنقلات. استخدم DTOs. هذا يمنع over-posting ويكسر الاعتماد على مخطط قاعدة البيانات."
        }
      ],
      quiz: [
        {
          q: "ما وظيفة HasIndex(p => p.Sku).IsUnique()؟",
          options: [
            "يجعل SKU مفتاحًا أساسيًا.",
            "يمنع تكرار SKU على مستوى قاعدة البيانات ويسرّع البحث.",
            "يخفي SKU من الاستعلامات.",
            "يحوّل SKU إلى decimal."
          ],
          answer: 1,
          explain: "الفهرس الفريد قيد يمنع التكرار تحت التزامن، ويسرّع البحث. لا يجعله مفتاحًا أساسيًا ولا يحل محل التحقق من قواعد العمل."
        },
        {
          q: "لماذا نستخدم HasPrecision للسعر؟",
          options: [
            "لتسريع الحفظ دائمًا.",
            "لتحديد عدد الأرقام والمنازل العشرية ومنع فقدان الدقة.",
            "لتحويل السعر إلى string.",
            "لإلغاء الحاجة إلى DTO."
          ],
          answer: 1,
          explain: "HasPrecision يضبط نوع العمود مثل decimal(18,2). الدقة الخاطئة قد تقطع القيم أو تسبب اختلافات بين قواعد البيانات."
        },
        {
          q: "ما دور RowVersion؟",
          options: [
            "يحفظ تاريخ الإنشاء تلقائيًا فقط.",
            "يكتشف أن الصف تغيّر منذ قراءته ويرمي DbUpdateConcurrencyException.",
            "يمنع كل التعديلات المتزامنة بالقفل الدائم.",
            "يشفّر الصف."
          ],
          answer: 1,
          explain: "RowVersion token يتغير مع التحديث. عند الحفظ يشترط EF Core النسخة القديمة، فيكشف التعارض بدل الكتابة فوق تغيير مستخدم آخر."
        }
      ],
      capstone: {
        title: "مخطط Souq الأولي",
        goal: "حوّل كيانات المنتج والتصنيف إلى مخطط واضح مع قيود وفهارس وmigration أولى.",
        tasks: [
          "أضف <code>Product</code> و<code>Category</code> إلى <code>AppDbContext</code> مع علاقة one-to-many.",
          "أنشئ <code>ProductConfiguration</code> تحدد الجدول والمفتاح وأطوال الاسم وSKU.",
          "أضف فهرسًا فريدًا على SKU وفهرسًا على <code>CategoryId</code>.",
          "اضبط <code>Price</code> بدقة <code>decimal(18,2)</code> وأضف <code>RowVersion</code>.",
          "أنشئ migration باسم <code>InitialCatalog</code> وراجع SQL قبل تطبيقها."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه التكوين",
          code: `builder.HasIndex(p => p.Sku).IsUnique();
builder.Property(p => p.Price).HasPrecision(18, 2);
builder.HasOne(p => p.Category)
    .WithMany(c => c.Products)
    .HasForeignKey(p => p.CategoryId)
    .OnDelete(DeleteBehavior.Restrict);`,
        },
      },
    },
    {
      id: "efcore-queries",
      title: "EF Core Queries: استعلامات تُترجم إلى SQL",
      duration: 30,
      level: "متوسط",
      summary:
        "الاستعلام الذي تكتبه في C# ليس ما تنفذه قاعدة البيانات بالضرورة. ستتعلم كيف تقرأ SQL الناتج، تتجنب N+1 وcartesian explosion، وتبني قراءة سريعة ومُرقّمة.",
      keywords: ["EF Core", "IQueryable", "projection", "AsNoTracking", "Include", "pagination", "N+1", "compiled query"],
      objectives: [
        "تشرح كيف يتحول تعبير LINQ إلى SQL.",
        "تستخدم الإسقاط وAsNoTracking لتقليل البيانات والتتبع.",
        "تتجنب N+1 وcartesian explosion.",
        "تبني ترقيم صفحات ثابتًا وآمنًا.",
        "تقرأ SQL الناتج وتقيس قبل التحسين."
      ],
      concept: `
        <p>كل استعلام EF Core يبدأ من <code>IQueryable&lt;T&gt;</code>. <code>Where</code> و<code>Select</code> و<code>OrderBy</code> لا تنفّذ SQL؛ تبني <strong>expression tree</strong>. عند <code>ToListAsync</code> أو <code>FirstOrDefaultAsync</code> يترجم الموفر الشجرة إلى SQL ويرسلها. إذا استدعيت <code>ToList</code> مبكرًا، فأنت تسحب البيانات إلى الذاكرة ثم تفلتر هناك؛ قد يكون كارثيًا على جدول كبير.</p>
        <h3>الإسقاط قبل النقل</h3>
        <p>لا تجلب الكيان كاملًا ثم تحوّله إلى DTO في الذاكرة. استخدم <code>Select(p => new ProductDto(...))</code> ليقرأ EF الأعمدة المطلوبة فقط. هذا يقلل I/O والشبكة والذاكرة، ويمنع إرجاع حقول حساسة. الإسقاط أيضًا يقلل مشاكل التتبع لأنه لا يعيد كيانات متتبعة إن كان DTO.</p>
        <h3>التتبع ليس مجانيًا</h3>
        <p>في القراءة التي لا ستعدّل، استخدم <code>AsNoTracking</code>. يقلل الذاكرة وعمل Change Tracker ويسرّع الاستعلامات الكبيرة. لا تستخدمه إذا ستعدّل الكيان في نفس الـ context وتحفظ؛ التغييرات لن تُكتشف. <code>AsNoTrackingWithIdentityResolution</code> مفيد عند الحاجة لهوية موحدة دون تتبع.</p>
        <h3>N+1 وInclude</h3>\n        <p>N+1 يحدث عندما تجلب قائمة ثم تستعلم عن علاقة لكل عنصر. الحل ليس دائمًا <code>Include</code> أعمى؛ قد ينتج JOIN ضخمًا أو تكرارًا. استخدم الإسقاط للعلاقة المطلوبة، أو <code>AsSplitQuery</code> عند الحاجة. قِس عدد الاستعلامات وSQL. Lazy loading يجعل N+1 أسهل في الحدوث، لذلك لا تفعّله افتراضيًا في API.</p>\n        <h3>الترقيم</h3>\n        <p><code>Skip/Take</code> يحتاج <code>OrderBy</code> ثابتًا، وإلا قد تتكرر أو تختفي صفوف بين الصفحات. الترقيم بالـ offset يتباطأ في الصفحات العميقة على الجداول الكبيرة؛ cursor pagination باستخدام مفتاح مرتّب أفضل. ضع حدًا أقصى لـ<code>pageSize</code>، وأعد metadata واضحة (total أو next cursor).</p>\n        <h3>الاستعلامات المجمّعة</h3>\n        <p>EF Core يخزن خطة الترجمة لكل شكل استعلام، لكن بناء الشجرة نفسها متكرر. <code>EF.CompileAsyncQuery</code> يفيد الاستعلامات الساخنة جدًا، لكنه يقلل المرونة ويصعّب القراءة. لا تستخدمه قبل القياس. الاستعلام البطيء غالبًا يحتاج فهرسًا أو إسقاطًا أفضل، لا micro-optimization.</p>\n      `,
      walkthrough: [
        {
          title: "ابدأ من DbSet",
          code: `var query = _db.Products.AsNoTracking();`,
          lang: "csharp",
          body: `<p><code>_db.Products</code> هو <code>IQueryable&lt;Product&gt;</code>. <code>AsNoTracking</code> يخبر EF ألا يحتفظ بنسخة مراقبة. لم يُنفّذ SQL بعد؛ هذا وصف. إذا أضفت شروطًا لاحقًا، ستُدمج في نفس الاستعلام بدل تنفيذ عدة استعلامات.</p>`
        },
        {
          title: "أضف الفلترة في SQL",
          code: `.Where(p => p.IsActive && !p.IsDeleted);`,
          lang: "csharp",
          body: `<p>الشرط يتحول إلى <code>WHERE IsActive = 1 AND IsDeleted = 0</code> (حسب الموفر). استخدم أعمدة مفهرسة للشروط المتكررة. لا تستدعي method C# عادية لا يستطيع الموفر ترجمتها؛ قد يحدث استثناء أو تحميل جزئي. افحص SQL عند الشك.</p>`
        },
        {
          title: "رتّب قبل الترقيم",
          code: `.OrderBy(p => p.Name)
.ThenBy(p => p.Id);`,
          lang: "csharp",
          body: `<p><code>OrderBy</code> ينتج ORDER BY. أضف <code>ThenBy</code> بمفتاح فريد لكسر التعادل، وإلا قد يتغير ترتيب الصفوف المتساوية بين الصفحات. الترتيب على عمود غير مفهرس قد يكون مكلفًا. لا تفترض ترتيبًا افتراضيًا من قاعدة البيانات.</p>`
        },
        {
          title: "اسقط إلى DTO",
          code: `.Select(p => new ProductDto(
    p.Id,
    p.Name,
    p.Price,
    p.Stock > 0));`,
          lang: "csharp",
          body: `<p>الإسقاط يحدد الأعمدة:<code>SELECT Id, Name, Price, Stock</code> بدل كل الأعمدة. كما يحوّل <code>Stock &gt; 0</code> إلى تعبير SQL أو يحسبه بعد القراءة حسب الموفر. الـ DTO يمنع إرجاع حقول داخلية، ويقلل بيانات الشبكة. لا تستخدم <code>Select(p =&gt; p)</code> ثم تحوّل في الذاكرة.</p>`
        },
        {
          title: "أضف الترقيم",
          code: `.Skip((page - 1) * pageSize)
.Take(pageSize);`,
          lang: "csharp",
          body: `<p><code>Skip/Take</code> يترجمان إلى <code>OFFSET/FETCH</code> أو <code>LIMIT/OFFSET</code>. تحقق من <code>page &gt;= 1</code> و<code>pageSize</code> بين 1 و100 قبل البناء. الصفحات العميقة تصبح أبطأ لأن قاعدة البيانات تفحص صفوفًا كثيرة. للجداول الكبيرة، استخدم cursor pagination بدل offset.</p>`
        },
        {
          title: "نفّذ مرة واحدة",
          code: `var items = await query.ToListAsync(ct);`,
          lang: "csharp",
          body: `<p>هنا يُنفّذ SQL فعليًا. <code>ToListAsync</code> يفتح الاتصال، يرسل الأمر، يقرأ الصفوف، ويبني القائمة. <code>await</code> يحرر الخيط أثناء الانتظار. <code>ct</code> يسمح بالإلغاء عند انقطاع العميل. لا تستدعي <code>ToList</code> المتزامن داخل طلب ASP.NET Core إلا لسبب واضح.</p>`
        },
        {
          title: "اجلب التفاصيل بعلاقة واحدة",
          code: `var product = await _db.Products
    .AsNoTracking()
    .Include(p => p.Category)
    .FirstOrDefaultAsync(p => p.Id == id, ct);`,
          lang: "csharp",
          body: `<p><code>Include</code> يجلب التصنيف مع المنتج. استخدمه عندما تحتاج العلاقة فعلًا، لا في كل استعلام. لعلاقات كثيرة، قد ينتج JOIN ضخمًا؛ <code>AsSplitQuery</code> يفصل الاستعلامات بتكلفة رحلات إضافية. <code>FirstOrDefaultAsync</code> يعيد null عند عدم الوجود، وهو مناسب للبحث بمعرّف.</p>`
        },
        {
          title: "ميّز بين First وSingle",
          code: `var bySku = await _db.Products
    .SingleOrDefaultAsync(p => p.Sku == sku, ct);`,
          lang: "csharp",
          body: `<p><code>SingleOrDefault</code> يفترض أن النتيجة صفر أو واحد، ويرمي إذا وجد أكثر من واحد. مناسب لعمود فريد مثل SKU. <code>FirstOrDefault</code> يختار أول صف حسب ترتيب غير مضمون إن لم تحدد OrderBy. لا تستخدم First للتحقق من التفرد؛ استخدم قيدًا فريدًا في قاعدة البيانات.</p>`
        },
        {
          title: "اقرأ SQL الناتج",
          code: `var sql = query.ToQueryString();
_logger.LogDebug("SQL: {Sql}", sql);`,
          lang: "csharp",
          body: `<p><code>ToQueryString</code> يعرض SQL المتوقع دون تنفيذه. استخدمه في التطوير والاختبارات للتأكد من وجود WHERE/ORDER BY/LIMIT. في الإنتاج، فعّل logging منخفض المستوى أو OpenTelemetry. لا تسجّل معاملات حساسة. راجع خطة التنفيذ والفهارس عند البطء.</p>`
        },
        {
          title: "استعلام مجمّع للساخن فقط",
          code: `private static readonly Func<AppDbContext, Guid,
    CancellationToken, Task<ProductDto?>> GetById =
    EF.CompileAsyncQuery((AppDbContext db, Guid id,
        CancellationToken ct) =>
        db.Products.AsNoTracking()
          .Where(p => p.Id == id)
          .Select(p => new ProductDto(p.Id, p.Name, p.Price))
          .FirstOrDefault());`,
          lang: "csharp",
          body: `<p><code>CompileAsyncQuery</code> يخزن delegate لاستعلام ثابت الشكل. يفيد عند تنفيذ ملايين المرات بنفس الشكل. لا تستخدمه لاستعلامات ديناميكية أو نادرة؛ سيزيد التعقيد بلا فائدة. قِس أولًا، وتأكد أن الترجمة نفسها هي العنق لا قاعدة البيانات.</p>`
        }
      ],
      compare: {
        intro: `<p>الاستعلامان يعيدان نفس النتيجة، لكن أحدهما يجلب كل شيء ويفلتر في الذاكرة.</p>`,
        before: {
          label: "تحميل ثم فلترة",
          lang: "csharp",
          title: "قبل",
          code: `var all = await _db.Products.ToListAsync();
return all.Where(p => p.IsActive)
          .OrderBy(p => p.Name)
          .Skip((page - 1) * size)
          .Take(size)
          .ToList();`,
          points: [
            "يجلب كل الصفوف إلى الذاكرة.",
            "الفلترة والترقيم بعد النقل.",
            "يتتبع كل الكيانات بلا حاجة.",
            "لا يستفيد من فهرس WHERE."
          ]
        },
        after: {
          label: "استعلام واحد مترجم",
          lang: "csharp",
          title: "بعد",
          code: `return await _db.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .OrderBy(p => p.Name)
    .ThenBy(p => p.Id)
    .Skip((page - 1) * size)
    .Take(size)
    .Select(p => new ProductDto(
        p.Id, p.Name, p.Price, p.Stock > 0))
    .ToListAsync(ct);`,
          points: [
            "WHERE وORDER BY وLIMIT في SQL.",
            "AsNoTracking يقلل الذاكرة.",
            "الإسقاط يقرأ الأعمدة المطلوبة.",
            "ThenBy يثبت ترتيب الصفحات."
          ]
        },
        verdict: `<p>القاعدة: لا تعبر حدود الذاكرة قبل أن تضيّق النتيجة في قاعدة البيانات. الإسقاط والترقيم ليسا تحسينًا متقدمًا؛ هما الأساس.</p>`
      },
      internals: `
        <p>EF Core يحوّل expression tree إلى SQL عبر موفر قاعدة البيانات. الترجمة تحدث مرة لكل شكل استعلام تقريبًا، ثم تُعاد الاستفادة من الخطة. الاستعلام نفسه يُرسل بمعاملات (parameterized) لتقليل هجمات SQL injection والاستفادة من plan cache. لا تبنِ SQL بـstring interpolation.</p>
        <p>عند القراءة، يفتح EF اتصالًا (أو يأخذه من pool)، ينفّذ command، يقرأ rows، ثم يحوّلها إلى كيانات أو DTOs. مع التتبع، ينشئ snapshot للقيم الأصلية. هذا يفسر لماذا <code>AsNoTracking</code> أسرع وأخف للقراءة. مع الإسقاط إلى DTO، لا يوجد تتبع أصلًا لأن النتيجة ليست كيانًا.</p>
        <p><strong>N+1</strong> يظهر عندما تنفّذ استعلامًا للقائمة ثم استعلامًا لكل عنصر عند الوصول لعلاقة غير محمّلة. الحل: Include أو projection أو split query، حسب شكل البيانات. لا تفعّل Lazy Loading في API؛ يجعل N+1 يحدث في طبقات لا ترى فيها SQL.</p>\n        <h3>Cartesian explosion</h3>\n        <p>عند Include لعلاقتين one-to-many معًا، قد ينتج JOIN يكرر الصفوف بشكل كبير. <code>AsSplitQuery</code> يرسل استعلامات منفصلة ويجمعها، لكنه يزيد الرحلات. قِس حجم النتيجة وعدد الرحلات. أحيانًا الإسقاط إلى DTO مسطح أفضل من Include.</p>\n        <h3>الترقيم والثبات</h3>\n        <p>Offset pagination يقرأ ويزيح كل الصفوف السابقة، لذا يتباطأ مع الصفحات العميقة. Cursor pagination يستخدم آخر قيمة مرتّبة:<code>WHERE (Name, Id) &gt; (@lastName, @lastId)</code>. يحتاج فهرسًا مركبًا وترتيبًا فريدًا. لا تخلط بينه وبين Skip/Take في نفس العقد.</p>\n        <h3>القياس</h3>\n        <p>استخدم <code>ToQueryString</code>، logging، وOpenTelemetry لرؤية SQL والزمن وعدد الاستعلامات. راقب <code>DbContext</code> scope: لا تعِش طوال التطبيق. استخدم <code>IDbContextFactory</code> في الخدمات الخلفية. اختبر على بيانات بحجم واقعي؛ جدول 10 صفوف لا يكشف مشاكل الأداء.</p>\n      `,
      internalsTable: {
        head: ["المشكلة", "العلامة", "الحل"],
        rows: [
          ["N+1", "استعلامات كثيرة متتالية", "Include أو projection أو split query"],
          ["تحميل زائد", "SELECT * ثم فلترة", "Where وSelect قبل ToList"],
          ["تتبع غير ضروري", "ذاكرة عالية للقراءة", "AsNoTracking"],
          ["صفحات عميقة بطيئة", "OFFSET كبير", "Cursor pagination"],
          ["JOIN متضخم", "صفوف مكررة كثيرة", "AsSplitQuery أو projection"],
          ["ترتيب غير ثابت", "صفوف تتكرر بين الصفحات", "OrderBy + ThenBy بمفتاح فريد"]
        ]
      },
      tips: [
        {
          title: "لا تعبر للذاكرة مبكرًا",
          body: "أضف Where وSelect وOrderBy وSkip/Take قبل ToList. أي ToList مبكر يجعل ما بعده LINQ to Objects ويفقد ترجمة SQL."
        },
        {
          title: "أسقط DTOs",
          body: "لا تجلب الكيان كاملًا لتعيد 3 حقول. الإسقاط يقلل I/O ويحمي الحقول الحساسة ويجعل العقد واضحًا."
        },
        {
          title: "استخدم AsNoTracking للقراءة",
          body: "في استعلامات العرض التي لا ستعدّل، أوقف التتبع. استخدم التتبع فقط عند الحاجة إلى SaveChanges."
        },
        {
          title: "اقرأ SQL واختبر ببيانات واقعية",
          body: "استخدم ToQueryString وlogging وخطط التنفيذ. أضف فهارسًا بناءً على استعلامات حقيقية، لا تخمينًا."
        }
      ],
      quiz: [
        {
          q: "متى يتحول استعلام EF Core إلى SQL؟",
          options: [
            "عند كتابة Where مباشرة.",
            "عند التعداد أو ToListAsync/FirstOrDefaultAsync.",
            "عند إنشاء DbContext.",
            "عند استدعاء AsNoTracking."
          ],
          answer: 1,
          explain: "LINQ يبني expression tree. التنفيذ الفعلي يبدأ عند التعداد أو method تنفيذ مثل ToListAsync. Where وSelect لا تنفذان SQL وحدهما."
        },
        {
          q: "ما فائدة الإسقاط Select إلى DTO؟",
          options: [
            "يجلب كل الأعمدة ثم يحذفها.",
            "يقرأ الأعمدة المطلوبة فقط ويقلل البيانات والتتبع.",
            "يمنع استخدام الفهارس.",
            "يجعل الاستعلام متزامنًا."
          ],
          answer: 1,
          explain: "الإسقاط يحدد الأعمدة التي تُقرأ، ويقلل الشبكة والذاكرة، ويمنع إرجاع حقول غير مطلوبة."
        },
        {
          q: "ما سبب مشكلة N+1؟",
          options: [
            "استخدام Where قبل Select.",
            "استعلام لقائمة ثم استعلام لكل عنصر لتحميل علاقة.",
            "استخدام AsNoTracking.",
            "إضافة فهرس فريد."
          ],
          answer: 1,
          explain: "N+1 يحدث عند تحميل قائمة ثم طلب علاقة لكل عنصر، فينتج استعلام إضافي لكل صف. الحل Include أو projection أو split query حسب الحالة."
        }
      ],
      capstone: {
        title: "قراءة المنتجات بكفاءة",
        goal: "أضف endpoint قائمة منتجات مع ترقيم وإسقاط وقياس، ثم حسّن استعلام التفاصيل.",
        tasks: [
          "اكتب <code>GetProductsAsync(page, pageSize, ct)</code> باستخدام <code>AsNoTracking</code> و<code>Select</code> إلى DTO.",
          "أضف <code>OrderBy(Name).ThenBy(Id)</code> و<code>Skip/Take</code> مع حد أقصى 100.",
          "أضف endpoint تفاصيل يجلب التصنيف بـ<code>Include</code> أو projection، وارجع 404 عند عدم الوجود.",
          "سجّل SQL باستخدام <code>ToQueryString</code> في الاختبار وتأكد من WHERE/ORDER BY/LIMIT.",
          "أضف فهرسًا على <code>IsActive, Name</code> واختبر خطة التنفيذ قبل/بعد."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه الاستعلام",
          code: `return await _db.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .OrderBy(p => p.Name)
    .ThenBy(p => p.Id)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .Select(p => new ProductDto(
        p.Id, p.Name, p.Price, p.Stock > 0))
    .ToListAsync(ct);`,
        },
      },
    },
    {
      id: "efcore-transactions-concurrency",
      title: "EF Core: المعاملات، التزامن، وإعادة المحاولة",
      duration: 30,
      level: "متقدم",
      summary:
        "العمليات المالية لا تحتمل نصف نجاح. ستتعلم حدود المعاملة، مستويات العزل، التعارض بين المستخدمين، وإعادة المحاولة الآمنة عندما ترفض قاعدة البيانات العملية.",
      keywords: ["transaction", "ACID", "isolation", "RowVersion", "DbUpdateConcurrencyException", "deadlock", "execution strategy", "outbox", "idempotency"],
      objectives: [
        "تحدد حدود المعاملة حول أكثر من عملية حفظ.",
        "تفرّق بين implicit وexplicit transactions.",
        "تتعامل مع DbUpdateConcurrencyException دون الكتابة فوق تغيير الآخرين.",
        "تختار مستوى عزل مناسبًا وتشرح تكلفته.",
        "تعيد المحاولة بأمان عند deadlock أو transient failure."
      ],
      concept: `
        <p>المعاملة (transaction) تجمع عمليات في وحدة ذرية: إما تنجح كلها أو تفشل كلها. عند تنفيذ <code>SaveChanges</code>، يغلّف EF Core التغييرات في معاملة ضمنية تلقائيًا. لكن هذا لا يكفي عندما تحتاج حفظين منفصلين أو عملية على خدمة أخرى. إن أنشأت طلبًا ثم خصمت المخزون في <code>SaveChanges</code> ثانٍ، فقد ينجح الأول ويفشل الثاني، فتبقى البيانات غير متسقة.</p>
        <h3>حدود المعاملة</h3>
        <p>المعاملة الجيدة قصيرة: لا تفتحها أثناء استدعاء شبكة أو انتظار مستخدم. افصل القراءة البطيئة عن الكتابة، وابدأ المعاملة قرب التغيير. كلما طالت، زاد احتجاز الأقفال أو snapshot، وقل التزامن. لا تفتح معاملة حول عدة استعلامات قراءة فقط إلا إذا كنت تحتاج اتساقًا لحظيًا بينها.</p>
        <h3>مستويات العزل</h3>
        <p><code>ReadCommitted</code> الافتراضي في كثير من قواعد البيانات: لا تقرأ بيانات غير مثبتة. <code>RepeatableRead</code> يمنع تغيّر الصفوف المقروءة، و<code>Serializable</code> يمنع ظواهر التزامن تقريبًا بالكامل لكنه يقلل التزامن وقد يسبب deadlocks. <code>Snapshot</code> يقرأ نسخة ثابتة دون حجب القراء، لكنه يحتاج دعمًا وإدارة إصدارات. اختر حسب الحاجة، لا «الأقوى دائمًا».</p>
        <h3>التزامن التفاؤلي</h3>
        <p>بدل قفل الصف طوال القراءة، أضف <code>RowVersion</code>. عند الحفظ يتحقق EF Core أن النسخة لم تتغير. إذا تغيرت، يرمي <code>DbUpdateConcurrencyException</code>. هذا يعني أن مستخدمًا آخر سبقك، وليس أن قاعدة البيانات تعطلت. قرر: أعد التحميل ودمج، أعد 409، أو أعد المحاولة إذا كانت العملية قابلة للدمج. لا تتجاهل الاستثناء.</p>
        <h3>Deadlocks وإعادة المحاولة</h3>
        <p>Deadlock يحدث عندما تنتظر معاملتان موارد بعضهما. قاعدة البيانات تختار أحد الطرفين وتلغيه. هذا خطأ عابر غالبًا، لكن إعادة المحاولة يجب أن تكون <strong>idempotent</strong>؛ وإلا قد تنشئ طلبين أو تخصم مرتين. استخدم <code>CreateExecutionStrategy</code> لإعادة المحاولة، وأعد تنفيذ المعاملة كاملة، لا نصفها.</p>
        <h3>ما لا تحله المعاملة</h3>
        <p>المعاملة المحلية لا تضم خدمة دفع خارجية أو broker. إذا حفظت الطلب ثم فشل نشر الحدث، فقدت الحدث. <strong>Outbox Pattern</strong> يحفظ الحدث في جدول داخل نفس المعاملة، ثم ينشره عامل خلفي مرة واحدة على الأقل. المستهلك يجب أن يكون idempotent. هذا ليس تعقيدًا زائدًا؛ هو الحد الفاصل بين نظام يعمل ونظام يبدو أنه يعمل.</p>
      `,
      walkthrough: [
        {
          title: "معاملة SaveChanges الضمنية",
          code: `order.Status = OrderStatus.Placed;
order.PlacedAt = DateTimeOffset.UtcNow;
await _db.SaveChangesAsync(ct);`,
          lang: "csharp",
          body: `<p><code>SaveChangesAsync</code> يجمّع التغييرات في معاملة واحدة افتراضيًا. إذا فشل أحد الأوامر، تُلغى المجموعة. لكن هذا يخص هذا الاستدعاء فقط. إن كنت عدّلت المخزون في <code>SaveChanges</code> آخر، فكل استدعاء معاملة مستقلة. لا تفترض أن كل تغييرات الـ context تُحفظ معًا عبر استدعاءات متعددة.</p>`
        },
        {
          title: "افتح معاملة صريحة",
          code: `await using var tx = await _db.Database
    .BeginTransactionAsync(ct);`,
          lang: "csharp",
          body: `<p><code>BeginTransactionAsync</code> يبدأ معاملة على اتصال قاعدة البيانات. <code>await using</code> يضمن التحرير حتى عند الاستثناء. استخدمها عندما تحتاج أكثر من <code>SaveChanges</code> أو أمر SQL خام داخل نفس الوحدة. لا تفتحها قبل استدعاءات شبكة طويلة؛ احتفظ بها قصيرة.</p>`
        },
        {
          title: "نفّذ ثم Commit",
          code: `try
{
    _db.Orders.Add(order);
    product.Stock -= order.Quantity;
    await _db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
}
catch
{
    await tx.RollbackAsync(ct);
    throw;
}`,
          lang: "csharp",
          body: `<p>الطلب وخفض المخزون يُحفظان معًا. إن فشل أي جزء، <code>Rollback</code> يعيد الحالة. لاحظ أن <code>SaveChanges</code> قد ينجح ثم يفشل <code>Commit</code> لأسباب نادرة؛ لا تعِد إنشاء الطلب في <code>catch</code> بلا مفتاح idempotency. في الإنتاج، استخدم execution strategy بدل try/catch بسيط للـ transient failures.</p>`
        },
        {
          title: "أعد المحاولة بالاستراتيجية",
          code: `var strategy = _db.Database.CreateExecutionStrategy();

await strategy.ExecuteAsync(async () =>
{
    await using var tx = await _db.Database
        .BeginTransactionAsync(ct);

    _db.Orders.Add(order);
    product.Stock -= order.Quantity;
    await _db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
});`,
          lang: "csharp",
          body: `<p><code>CreateExecutionStrategy</code> يعرف الأخطاء العابرة التي يدعمها الموفر. أعد تنفيذ <strong>المعاملة كاملة</strong> داخل delegate. لا تحتفظ بكيانات متتبعة من محاولة فاشلة؛ قد تحتاج سياقًا جديدًا أو إعادة تحميل. وتأكد أن العملية idempotent عبر مفتاح فريد، لأن إعادة المحاولة قد تحدث بعد نجاح غير مؤكد.</p>`
        },
        {
          title: "اكتشف تعارض التحديث",
          code: `catch (DbUpdateConcurrencyException ex)
{
    var entry = ex.Entries.Single();
    var databaseValues = await entry
        .GetDatabaseValuesAsync(ct);
    // قرر: دمج، إعادة تحميل، أو 409.
}`,
          lang: "csharp",
          body: `<p>الاستثناء يعني أن الصف تغيّر أو حُذف منذ قراءته. <code>GetDatabaseValuesAsync</code> يجلب القيم الحالية. لا تكتب فوقها تلقائيًا. قرار الدمج يعتمد على قواعد العمل: هل تعديل السعر يتعارض مع تعديل المخزون؟ إن كان التعارض حقيقيًا، أعد 409 مع رسالة واضحة. لا تحوّله إلى 500.</p>`
        },
        {
          title: "أعد 409 بدل الكتابة فوق الآخر",
          code: `return TypedResults.Problem(
    title: "Product was modified",
    detail: "Reload the product and try again.",
    statusCode: StatusCodes.Status409Conflict);`,
          lang: "csharp",
          body: `<p>409 يخبر العميل أن الطلب صالح لكن الحالة تغيرت. أضف معرف النسخة أو رابط إعادة القراءة إن كان العقد يدعم ذلك. لا ترجع 500 لأن التعارض متوقع. ولا ترجع 200 مع تجاهل التغيير. العميل يحتاج فرصة لإعادة القراءة والدمج الواعي.</p>`
        },
        {
          title: "مستوى العزل ليس ترفًا",
          code: `await using var tx = await _db.Database
    .BeginTransactionAsync(
        IsolationLevel.Serializable, ct);`,
          lang: "csharp",
          body: `<p><code>Serializable</code> يمنع قراءات/كتابات متداخلة قد تسبب عدم اتساق، لكنه يزيد الاحتجاز والـdeadlocks. استخدمه فقط عندما تكون صحة النتيجة أهم من التزامن، مثل تخصيص رقم تسلسلي أو عملية محاسبية حساسة. اختبر تحت حمل متزامن. لا تغيّر مستوى العزل عالميًا لمجرد «الاحتياط».</p>`
        },
        {
          title: "تعامل مع القيد الفريد",
          code: `catch (DbUpdateException ex)
    when (IsUniqueViolation(ex))
{
    return TypedResults.Problem(
        title: "SKU already exists",
        statusCode: StatusCodes.Status409Conflict);
}`,
          lang: "csharp",
          body: `<p>حتى مع فحص مسبق، قد يسبقك طلب آخر بين الفحص والإدراج. الفهرس الفريد هو الحكم النهائي. التقط <code>DbUpdateException</code> وافحص رمز الخطأ الخاص بالموفر (مثل 23505 في PostgreSQL أو 2601/2627 في SQL Server). لا تلتقط كل <code>DbUpdateException</code> كأنه تكرار؛ قد يكون خطأ اتصال أو قيدًا آخر.</p>`
        },
        {
          title: "اكتب حدث Outbox في نفس المعاملة",
          code: `_db.OutboxMessages.Add(new OutboxMessage
{
    Id = Guid.NewGuid(),
    Type = "OrderPlaced",
    Payload = JsonSerializer.Serialize(orderPlaced),
    OccurredAt = DateTimeOffset.UtcNow
});

await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);`,
          lang: "csharp",
          body: `<p>الحدث يُحفظ في جدول Outbox داخل نفس معاملة الطلب. عامل خلفي يقرأ الرسائل غير المنشورة وينشرها، ثم يعلّمها. هذا يضمن «مرة واحدة على الأقل» بدل فقدان الحدث. المستهلك يجب أن يتعامل مع التكرار باستخدام معرف الحدث. لا تنشر مباشرة بين <code>SaveChanges</code> و<code>Commit</code> وتعتمد على الحظ.</p>`
        },
        {
          title: "اجعل إعادة المحاولة idempotent",
          code: `CREATE UNIQUE INDEX IX_Orders_IdempotencyKey
ON Orders (IdempotencyKey);`,
          lang: "sql",
          body: `<p>مفتاح idempotency فريد يمنع إنشاء طلبين عند إعادة محاولة العميل أو الشبكة. خزّن المفتاح مع الطلب، وعند التكرار أعد نتيجة الطلب الأول. لا تعتمد على فحص في الذاكرة. الفهرس الفريد يجعل القرار ذريًا تحت التزامن. هذا مكمل للمعاملة، وليس بديلًا عنها.</p>`
        }
      ],
      compare: {
        intro: `<p>حفظان منفصلان قد يتركان طلبًا بلا خصم مخزون، أو خصمًا بلا طلب. المعاملة تجمعهما.</p>`,
        before: {
          label: "حفظان مستقلان",
          lang: "csharp",
          title: "قبل",
          code: `_db.Orders.Add(order);
await _db.SaveChangesAsync(ct);

product.Stock -= order.Quantity;
await _db.SaveChangesAsync(ct);`,
          points: [
            "فشل الثاني يترك طلبًا بلا خصم.",
            "لا توجد وحدة ذرية.",
            "إعادة المحاولة قد تنشئ طلبًا مكررًا.",
            "التعارض لا يُكتشف."
          ]
        },
        after: {
          label: "معاملة + قيد",
          lang: "csharp",
          title: "بعد",
          code: `await using var tx = await _db.Database
    .BeginTransactionAsync(ct);

try
{
    _db.Orders.Add(order);
    product.Stock -= order.Quantity;
    await _db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
}
catch
{
    await tx.RollbackAsync(ct);
    throw;
}`,
          points: [
            "الطلب والمخزون ينجحان أو يفشلان معًا.",
            "Rollback يعيد الحالة.",
            "أضف RowVersion لمنع الكتابة فوق تعديل آخر.",
            "أضف IdempotencyKey لمنع التكرار."
          ]
        },
        verdict: `<p>المعاملة وحدها لا تكفي. تحتاج قيودًا، تزامنًا، ومفتاح idempotency لتغطية إعادة المحاولة والشبكات غير الموثوقة.</p>`
      },
      internals: `
        <p>EF Core يستخدم اتصال قاعدة البيانات لبدء المعاملة. عند <code>SaveChanges</code> يرسل الأوامر ضمن المعاملة الحالية إن وجدت. إذا لم توجد، ينشئ معاملة ضمنية ويغلقها. <code>Commit</code> يثبت التغييرات، و<code>Rollback</code> يلغيها. لا تشارك <code>DbContext</code> بين طلبات متزامنة؛ ليس thread-safe.</p>
        <p>مستويات العزل تتحكم في الظواهر: dirty reads، non-repeatable reads، phantom reads. كلما زاد العزل، زادت الأقفال أو إصدارات snapshot، وقل التزامن. <code>Serializable</code> قد يسبب deadlocks متكررة. اختبر السلوك على موفر قاعدة البيانات الفعلي، لا على InMemory provider.</p>
        <p><strong>Optimistic concurrency</strong> لا يمنع التعارض؛ يكتشفه. هذا أرخص من قفل الصف عند القراءة في أنظمة القراءة الكثيرة. عند التعارض، لا يوجد حل عام: الدمج قد يكون صحيحًا لحقل واحد وخطأً لحقل آخر. قرار العمل يجب أن يكون في الكود، لا في EF Core.</p>
        <h3>Deadlocks</h3>
        <p>تحدث عندما ينتظر كل طرف قفلًا يملكه الآخر. الحل: رتّب الوصول إلى الموارد بنفس الترتيب، قصّر المعاملات، واستخدم فهارس تقلل نطاق الأقفال. إعادة المحاولة مع backoff وجitter تساعد، لكن يجب أن تكون العملية idempotent. لا تعد المحاولة بلا حد؛ ضع سقفًا وسجّل.</p>
        <h3>Outbox</h3>
        <p>لا يمكنك جعل قاعدة البيانات وbroker في معاملة واحدة (إلا بأنظمة معقدة). Outbox يحوّل المشكلة إلى: اكتب الحدث مع البيانات في معاملة محلية، ثم انشره لاحقًا. العامل يحتاج قفلًا/تأشيرًا لمنع نسختين من النشر، والمستهلك يحتاج deduplication. هذا نمط أساسي في الأنظمة الموزعة، وليس تحسينًا اختياريًا.</p>
      `,
      internalsTable: {
        head: ["المفهوم", "ماذا يحمي", "التكلفة"],
        rows: [
          ["Implicit transaction", "SaveChanges واحد", "لا يشمل استدعاءات أخرى"],
          ["Explicit transaction", "عدة عمليات محلية", "أقفال/مدة أطول"],
          ["ReadCommitted", "من dirty reads", "قد تظهر قراءات غير قابلة للتكرار"],
          ["Serializable", "من معظم ظواهر التزامن", "deadlocks وتزامن أقل"],
          ["RowVersion", "من الكتابة فوق تغيير", "يحتاج معالجة 409/دمج"],
          ["Outbox", "فقدان الأحداث بعد الحفظ", "جدول وعامل ونشر at-least-once"]
        ]
      },
      tips: [
        {
          title: "اجعل المعاملة قصيرة",
          body: "لا تنتظر شبكة أو مستخدمًا داخل معاملة. ابدأها قرب التغيير، وأغلقها فورًا. المعاملة الطويلة تقلل التزامن وتزيد deadlocks."
        },
        {
          title: "لا تتجاهل تعارض التزامن",
          body: "DbUpdateConcurrencyException يعني أن قرار العمل مطلوب. أعد التحميل أو أعد 409. لا تكتب فوق تغيير مستخدم آخر بصمت."
        },
        {
          title: "أعد المحاولة للعمليات idempotent فقط",
          body: "استخدم execution strategy مع مفتاح فريد. إعادة إنشاء طلب بلا مفتاح قد تكرر الشراء. سجّل المحاولات وضع سقفًا."
        },
        {
          title: "الأحداث عبر Outbox",
          body: "لا تنشر حدثًا قبل commit أو بعده بلا ضمان. احفظه في Outbox ضمن المعاملة، وانشره من عامل، واجعل المستهلك يتحمل التكرار."
        }
      ],
      quiz: [
        {
          q: "متى تحتاج معاملة صريحة؟",
          options: [
            "عند قراءة صف واحد.",
            "عند الحاجة إلى أكثر من SaveChanges أو عمليات مترابطة ذريًا.",
            "عند كل استعلام GET.",
            "عند استخدام AsNoTracking."
          ],
          answer: 1,
          explain: "SaveChanges الواحد له معاملة ضمنية. المعاملة الصريحة تلزم عند تجميع عدة عمليات/حفظات في وحدة واحدة."
        },
        {
          q: "ماذا يعني DbUpdateConcurrencyException؟",
          options: [
            "انقطاع الاتصال دائمًا.",
            "الصف تغيّر أو حُذف منذ قراءته، فلم يُطبّق التحديث.",
            "خطأ في صياغة SQL.",
            "نجاح العملية."
          ],
          answer: 1,
          explain: "هو تعارض تزامن تفاؤلي. يجب التعامل معه بقرار عمل: دمج، إعادة تحميل، أو 409، لا تجاهل."
        },
        {
          q: "لماذا نحتاج Outbox؟",
          options: [
            "لتسريع كل الاستعلامات.",
            "لضمان عدم فقدان حدث عند الحفظ خارج معاملة broker.",
            "لإلغاء الحاجة إلى فهارس.",
            "لتشفير قاعدة البيانات."
          ],
          answer: 1,
          explain: "Outbox يحفظ الحدث مع البيانات في معاملة محلية، ثم ينشره عامل. يضمن at-least-once، ويحتاج المستهلك ليكون idempotent."
        }
      ],
      capstone: {
        title: "إنشاء طلب Souq بأمان",
        goal: "نفّذ عملية إنشاء طلب تخصم المخزون وتكتب حدث Outbox في معاملة واحدة، وتتعامل مع التعارض والتكرار.",
        tasks: [
          "أنشئ <code>PlaceOrderAsync</code> تبدأ معاملة صريحة وتضيف الطلب وتخصم المخزون.",
          "أضف <code>RowVersion</code> إلى المنتج وتعامل مع <code>DbUpdateConcurrencyException</code> بإرجاع 409.",
          "أضف <code>IdempotencyKey</code> فريدًا للطلب واختبر إرسال نفس الطلب مرتين.",
          "أضف جدول <code>OutboxMessages</code> واكتب حدث <code>OrderPlaced</code> في نفس المعاملة.",
          "اختبر تعارضًا متزامنًا بطلبين على آخر قطعة، وتأكد أن واحدًا فقط ينجح."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه العملية",
          code: `await using var tx = await _db.Database
    .BeginTransactionAsync(ct);

_db.Orders.Add(order);
product.Stock -= order.Quantity;
_db.OutboxMessages.Add(outboxMessage);

await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);`,
        },
      },
    },
    {
      id: "clean-architecture",
      title: "Clean Architecture: حدود لا تتسرّب",
      duration: 26,
      level: "متقدم",
      summary:
        "ما الذي يجعل الكود قابلًا للتغيير؟ ليس عدد المجلدات، بل اتجاه التبعيات. سنرى الطبقات الأربع، وقاعدة الاعتماد، ومتى يكون التعقيد مبررًا.",
      keywords: ["Clean Architecture", "Domain", "Application", "Infrastructure", "CQRS", "ports and adapters"],
      objectives: [
        "ترسم اتجاه التبعيات بين الطبقات.",
        "تفصل Domain عن EF Core وعن HTTP.",
        "تكتب use case واضحًا بدل Controller ضخم.",
        "تعرف متى تتوقف عن إضافة طبقات.",
      ],
      concept: `
        <p><strong>Clean Architecture</strong> ليست وصفة مجلدات؛ إنها قاعدة واحدة: <em>التبعيات تتجه إلى الداخل</em>. المركز هو <strong>Domain</strong> (قواعد العمل)، وحوله <strong>Application</strong> (حالات الاستخدام)، ثم <strong>Infrastructure</strong> (التنفيذ التقني)، وأخيرًا <strong>Api</strong> (HTTP والتكوين).</p>
        <ul>
          <li><strong>Domain</strong>: كيانات وقواعد لا تعرف قاعدة بيانات ولا JSON ولا ASP.NET. لو حذفت كل التقنيات، يجب أن تبقى قابلة للفهم.</li>
          <li><strong>Application</strong>: use cases (أوامر واستعلامات)، وواجهات (ports) لما تحتاجه من الخارج: <code>IProductRepository</code>، <code>IEmailSender</code>، <code>IClock</code>.</li>
          <li><strong>Infrastructure</strong>: تنفيذ تلك الواجهات بـ EF Core وRedis وSMTP. تعتمد على Application، وليس العكس.</li>
          <li><strong>Api</strong>: نقاط النهاية، DI،Middleware. هي <em>Composition Root</em> التي تعرف كل شيء وتركّب الجميع.</li>
        </ul>
        <p>الفائدة العملية: يمكنك اختبار قواعد العمل بلا قاعدة بيانات، وتغيير PostgreSQL إلى SQL Server دون لمس Domain، وإضافة واجهة gRPC فوق نفس use cases. العدو الحقيقي ليس «الكود القبيح»، بل <strong>التبعية في الاتجاه الخاطئ</strong>: Domain تعرف <code>DbContext</code>، أو Application تعرف <code>HttpContext</code>.</p>
        <h3>CQRS خفيف</h3>
        <p>لا تحتاج MediatR لتطبيق CQRS. افصل ببساطة:</p>
        <ul>
          <li><strong>Command</strong>: يغيّر الحالة (<code>CreateProductCommand</code>) ويعيد معرّفًا أو Result.</li>
          <li><strong>Query</strong>: يقرأ فقط (<code>GetProductQuery</code>) ويعيد DTO جاهزًا للعرض.</li>
        </ul>
        <p>هذا الفصل يمنع «خدمة تفعل كل شيء»، ويسمح بتحسين القراءة والكتابة كلٌّ على حدة. لكنه ليس دينًا: تطبيق صغير بخمسة endpoints قد يكون أوضح بخدمات تقليدية.</p>
        <h3>متى لا تستخدمها؟</h3>
        <p>إذا كان المشروع CRUD بسيطًا وفريقًا صغيرًا، فطبقات متعددة قد تضاعف الوقت دون قيمة. ابدأ بـ Minimal API + خدمات، وعندما يصبح التغيير مؤلمًا، اسحب الحدود. المعمارية الجيدة هي أقل تعقيد يسمح بالتغيير، لا أكثر تعقيد يبدو مهنيًا.</p>
      `,
      compare: {
        intro: `<p>نفس العملية: إنشاء منتج. في الأولى كل شيء في الـ endpoint؛ في الثانية الـ endpoint يعرف فقط كيف يترجم HTTP إلى use case.</p>`,
        before: {
          label: "Fat endpoint",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapPost("/api/products", async (
    CreateProductRequest request,
    SouqDbContext db,
    IValidator<CreateProductRequest> validator,
    ILogger<Program> logger) =>
{
    var validation = await validator.ValidateAsync(request);
    if (!validation.IsValid) return Results.ValidationProblem(validation.ToDictionary());

    if (await db.Products.AnyAsync(p => p.Sku == request.Sku))
        return Results.Conflict("SKU already exists");

    var product = new Product
    {
        Name = request.Name,
        Sku = request.Sku,
        Price = request.Price,
        CreatedAt = DateTime.UtcNow
    };

    db.Products.Add(product);
    await db.SaveChangesAsync();

    logger.LogInformation("Product {Sku} created", product.Sku);
    return Results.Created($"/api/products/{product.Id}", product);
});`,
          points: [
            "HTTP + Validation + Data + Business + Logging في مكان واحد.",
            "لا يمكن اختبار القاعدة دون قاعدة بيانات.",
            "أي تغيير تقني يمسّ نقطة النهاية.",
          ],
        },
        after: {
          label: "Layered use case",
          lang: "csharp",
          title: "Application/Products/CreateProduct.cs",
          code: `public sealed record CreateProductCommand(
    string Name, string Sku, decimal Price, int CategoryId);

public sealed record CreateProductResult(int Id);

public sealed class CreateProductHandler
{
    private readonly IProductRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IClock _clock;

    public CreateProductHandler(
        IProductRepository repository,
        IUnitOfWork unitOfWork,
        IClock clock)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _clock = clock;
    }

    public async Task<CreateProductResult> HandleAsync(
        CreateProductCommand command, CancellationToken ct)
    {
        if (await _repository.SkuExistsAsync(command.Sku, ct))
            throw new ConflictException("SKU موجود بالفعل.");

        var product = Product.Create(
            command.Name, command.Sku,
            Money.From(command.Price), command.CategoryId, _clock.UtcNow);

        await _repository.AddAsync(product, ct);
        await _unitOfWork.SaveChangesAsync(ct);

        return new CreateProductResult(product.Id);
    }
}

// Api/Endpoints/Products.cs
group.MapPost("/", async (
    CreateProductRequest request,
    CreateProductHandler handler,
    CancellationToken ct) =>
{
    var result = await handler.HandleAsync(
        new CreateProductCommand(request.Name, request.Sku,
            request.Price, request.CategoryId), ct);

    return TypedResults.Created($"/api/v1/products/{result.Id}", result);
});`,
          points: [
            "الـ endpoint يترجم HTTP فقط.",
            "قواعد العمل قابلة للاختبار بلا قاعدة بيانات.",
            "استبدال التنفيذ التقني لا يمسّ use case.",
          ],
        },
        verdict: `<p>لاحظ أن الطبقات لم تُضف «سحرًا»؛ أضافت <strong>حدًا</strong>. الثمن: ملفات أكثر وتحويلات. المكسب: عندما يتضاعف عدد العمليات، تبقى كل عملية صغيرة وقابلة للاختبار. القرار يعتمد على العمر المتوقع للمشروع، لا على أناقة الرسم.</p>`,
      },
      walkthrough: [
        {
          title: "اتجاه الاعتماد",
          code: `Api -> Application -> Domain\nInfrastructure -> Application/Domain\nDomain -> لا يعتمد على أحد`,
          lang: "text",
          body: `<p>المجال في المركز. لا يعرف EF Core أو ASP.NET. التطبيق يعرّف حالات الاستخدام. البنية التحتية تنفّذ الواجهات. الـAPI يعرض HTTP. إذا عكسنا الاتجاه، يصبح اختبار المجال صعبًا ويرتبط بإطار العمل.</p>`
        },
        {
          title: "كيان المجال",
          code: `public sealed class Order\n{\n    private readonly List<OrderLine> _lines = new();\n    public Guid Id { get; private set; }\n    public OrderStatus Status { get; private set; }\n\n    public void AddLine(Guid productId, Money price, int quantity)\n    {\n        if (quantity <= 0) throw new DomainException("Quantity must be positive");\n        _lines.Add(new OrderLine(productId, price, quantity));\n    }\n}`,
          lang: "csharp",
          body: `<p>الكيان يحمي ثوابته. لا تضع <code>public set</code> لكل شيء. <code>AddLine</code> يمنع كمية غير صالحة. السعر value object. لا تعرف هذه الطبقة <code>DbContext</code>. اختبر القواعد بدون قاعدة بيانات.</p>`
        },
        {
          title: "واجهة حالة الاستخدام",
          code: `public interface IPlaceOrder\n{\n    Task<Guid> HandleAsync(PlaceOrderCommand command, CancellationToken ct);\n}\n\npublic sealed record PlaceOrderCommand(\n    Guid UserId,\n    IReadOnlyList<PlaceOrderItem> Items);`,
          lang: "csharp",
          body: `<p>الواجهة تعبّر عن نية العمل، لا عن جدول. <code>PlaceOrderCommand</code> DTO خاص بالتطبيق. لا تمرّر <code>HttpRequest</code> أو كيان EF. هذا الحد يجعل حالة الاستخدام قابلة للاختبار والاستدعاء من API/worker.</p>`
        },
        {
          title: "تنفيذ حالة الاستخدام",
          code: `public sealed class PlaceOrderHandler(\n    IOrderRepository orders,\n    IProductRepository products,\n    IUnitOfWork unitOfWork) : IPlaceOrder\n{\n    public async Task<Guid> HandleAsync(PlaceOrderCommand command, CancellationToken ct)\n    {\n        var order = Order.Create(command.UserId);\n        foreach (var item in command.Items)\n        {\n            var product = await products.GetAsync(item.ProductId, ct)\n                ?? throw new NotFoundException("Product not found");\n            order.AddLine(product.Id, product.Price, item.Quantity);\n        }\n        await orders.AddAsync(order, ct);\n        await unitOfWork.CommitAsync(ct);\n        return order.Id;\n    }\n}`,
          lang: "csharp",
          body: `<p>المنطق هنا، لا في endpoint. الواجهات تُعرّف في التطبيق وتُنفّذ في البنية التحتية. المعاملة عند حدود حالة الاستخدام. لا تعرف هذه الطبقة SQL. اختبر بـfakes. لاحظ أن التحقق من المخزون/الدفع يحتاج خطوات إضافية.</p>`
        },
        {
          title: "نقطة النهاية رقيقة",
          code: `group.MapPost("/orders", async (\n    PlaceOrderRequest request,\n    IPlaceOrder handler,\n    ClaimsPrincipal user,\n    CancellationToken ct) =>\n{\n    var userId = user.GetUserId();\n    var command = request.ToCommand(userId);\n    var id = await handler.HandleAsync(command, ct);\n    return TypedResults.Created($"/api/v1/orders/{id}", new { id });\n});`,
          lang: "csharp",
          body: `<p>الـendpoint يحوّل HTTP إلى command ثم يعيد نتيجة. لا يحتوي قواعد العمل. لا يحقن <code>DbContext</code>. المصادقة/التفويض في pipeline. هذا يسمح باستدعاء نفس الحالة من CLI/worker. الأخطاء تُترجم إلى ProblemDetails في طبقة API.</p>`
        },
        {
          title: "التنفيذ في البنية التحتية",
          code: `public sealed class OrderRepository(SouqDbContext db) : IOrderRepository\n{\n    public Task AddAsync(Order order, CancellationToken ct)\n    {\n        db.Orders.Add(order);\n        return Task.CompletedTask;\n    }\n\n    public Task<Order?> GetAsync(Guid id, CancellationToken ct) =>\n        db.Orders.Include(o => o.Lines)\n            .SingleOrDefaultAsync(o => o.Id == id, ct);\n}`,
          lang: "csharp",
          body: `<p>EF Core تفصيل بنية تحتية. المجال لا يرى <code>DbContext</code>. استخدم <code>Include</code> بحذر. لا تعرض <code>IQueryable</code> للخارج. الواجهة تعبّر عن احتياج المجال، لا عن SQL. يمكن استبدالها بـDapper/API لاحقًا.</p>`
        },
        {
          title: "Composition Root",
          code: `builder.Services.AddScoped<IPlaceOrder, PlaceOrderHandler>();\nbuilder.Services.AddScoped<IOrderRepository, OrderRepository>();\nbuilder.Services.AddScoped<IProductRepository, ProductRepository>();\nbuilder.Services.AddScoped<IUnitOfWork, EfUnitOfWork>();\nbuilder.Services.AddDbContext<SouqDbContext>(...);`,
          lang: "csharp",
          body: `<p>كل الربط في مكان واحد. التطبيق لا يعرف التنفيذ. استخدم <code>AddScoped</code> حسب العمر. لا تسجّل <code>DbContext</code> Singleton. تحقق من التسجيلات عند البدء. هذا هو المكان الذي يمكن تبديل التنفيذ فيه.</p>`
        },
        {
          title: "اختبار الحدود",
          code: `var orders = new FakeOrderRepository();\nvar products = new FakeProductRepository();\nvar handler = new PlaceOrderHandler(orders, products, new FakeUnitOfWork());\n\nvar id = await handler.HandleAsync(command, CancellationToken.None);\n\nAssert.NotEqual(Guid.Empty, id);\nAssert.Single(orders.Items);`,
          lang: "csharp",
          body: `<p>لا تحتاج قاعدة بيانات/HTTP لاختبار المنطق. استبدل الواجهات. اختبر الحالات: منتج غير موجود، كمية غير صالحة، فشل الحفظ. هذا مكسب Clean Architecture الحقيقي: سرعة ووضوح. لا تختبر التفاصيل الداخلية.</p>`
        }
      ],
      internals: `
        <p>اتجاه التبعيات يُفرَض على مستوى المشاريع: <code>Api → Infrastructure → Application → Domain</code>، و<code>Api</code> قد يعرف الكل لأنه يركّب. ممنوع <code>Domain → Infrastructure</code> أو <code>Application → Api</code>. إن احتجت شيئًا من الخارج في Application، عرّف واجهة (Port) واترك التنفيذ لـ Infrastructure (Adapter).</p>
        <p>هذا هو نمط <strong>Ports and Adapters</strong>. الفائدة ليست «تبديل قاعدة البيانات غدًا» فقط، بل <strong>الاختبار</strong>: يمكنك تنفيذ <code>IProductRepository</code> بقائمة في الذاكرة واختبار use case في أجزاء من الثانية.</p>
        <p>الـ <strong>Composition Root</strong> في Api هو المكان الوحيد الذي يعرف كل التنفيذات. هذا يمنع تسريب حزم EF Core إلى طبقات لا تحتاجها. لاحظ أن هذا يختلف عن «حظر EF نهائيًا»: Infrastructure تستخدمه بحرية، لكنها تعيد كيانات Domain أو DTOs، لا <code>IQueryable</code> مفتوحًا.</p>
        <p>حدّد المعاملات (Transactions) عند حد Unit of Work. لا تفتح معاملة في كل repository method؛ اجعل use case يقرر متى يُحفظ التغيير. في EF Core، <code>SaveChangesAsync</code> ينفّذ معاملة ضمنية تغطي كل التغييرات المتراكمة. للعمليات المعقدة، استخدم معاملة صريحة عبر <code>IDbContextTransaction</code>.</p>
      `,
      internalsTable: {
        head: ["الطبقة", "تعرف", "لا تعرف"],
        rows: [
          ["Domain", "قواعد العمل والأنواع", "EF, HTTP, JSON, DI"],
          ["Application", "use cases والعقود", "DbContext, HttpContext"],
          ["Infrastructure", "EF Core, Redis, SDKs", "HTTP endpoints"],
          ["Api", "HTTP, DI, Middleware", "تفاصيل SQL"],
        ],
      },
      tips: [
        {
          title: "ابدأ ببساطة",
          body: "مشروع واحد بأربعة مجلدات منطقية أفضل من أربعة مشاريع فارغة. افصل عندما يصبح الحد مؤلمًا أو عندما تحتاج اختبارًا معزولًا.",
        },
        {
          title: "لا تُرجع IQueryable من المستودع",
          body: "إرجاع <code>IQueryable</code> يسمح لطبقة API بتكوين استعلامات لا تعرفها Infrastructure، ويكسر الحد. أعد DTOs أو كيانات مع شروط واضحة.",
        },
        {
          title: "فرض الحدود باختبارات",
          body: "استخدم NetArchTest أو ArchUnitNET للتأكد أن Domain لا يشير إلى EF Core. القاعدة غير المفروضة تتحلل خلال أسابيع.",
        },
        {
          title: "الـ Mapping اليدوي غالبًا أسرع",
          body: "AutoMapper مريح لكنه يضيف Reflection وتكلفة بدء. في المسارات الساخنة، اكتب <code>ToDto()</code> صريحًا. الوضوح والأداء يفوزان.",
        },
      ],
      quiz: [
        {
          q: "ما قاعدة الاعتماد في Clean Architecture؟",
          options: [
            "كل الطبقات تعتمد على Infrastructure.",
            "التبعيات تتجه إلى الداخل نحو Domain.",
            "Api تعتمد على Domain فقط.",
            "لا توجد تبعيات بين الطبقات.",
          ],
          answer: 1,
          explain:
            "Domain في المركز ولا يعتمد على أحد. Application يعتمد عليه، Infrastructure ينفّذ عقوده، وApi يركّب الكل.",
        },
        {
          q: "أين يوضع IProductRepository؟",
          options: ["Domain", "Application كـ Port", "Infrastructure", "Api"],
          answer: 1,
          explain:
            "الواجهة عقد يحتاجه use case، فتكون في Application. التنفيذ في Infrastructure.",
        },
        {
          q: "متى تكون Clean Architecture مبالغة؟",
          options: [
            "عندما يكون التطبيق CRUD بسيطًا وفريقًا صغيرًا.",
            "عندما يوجد أكثر من 10 جداول.",
            "عند استخدام PostgreSQL.",
            "عند وجود اختبارات.",
          ],
          answer: 0,
          explain:
            "التعقيد الإضافي قد لا يعوّض قيمته في تطبيق صغير قصير العمر. ابدأ بسيطًا واستخرج الحدود عند الحاجة.",
        },
      ],
      capstone: {
        title: "تقسيم Souq إلى طبقات",
        goal: "نحوّل المشروع من ملفات متداخلة إلى أربعة مشاريع بحدود واضحة، مع نقل كيان Product إلى Domain.",
        tasks: [
          "أنشئ مشاريع <code>Souq.Domain</code> و<code>Souq.Application</code> و<code>Souq.Infrastructure</code>.",
          "اضبط المراجع: Api → Infrastructure → Application → Domain.",
          "انقل <code>Product</code> و<code>Money</code> إلى Domain بلا أي using لـ EF.",
          "عرّف <code>IProductRepository</code> و<code>IUnitOfWork</code> في Application.",
          "أضف اختبارًا يثبت أن Domain لا يعتمد على EF Core.",
        ],
        code: {
          lang: "bash",
          title: "إنشاء الطبقات",
          code: `dotnet new classlib -n Souq.Domain -o src/Souq.Domain
dotnet new classlib -n Souq.Application -o src/Souq.Application
dotnet new classlib -n Souq.Infrastructure -o src/Souq.Infrastructure

dotnet add src/Souq.Application reference src/Souq.Domain
dotnet add src/Souq.Infrastructure reference src/Souq.Application
dotnet add src/Souq.Api reference src/Souq.Infrastructure`,
        },
      },
    },
    {
      id: "efcore-tracking",
      title: "DbContext + Change Tracker",
      duration: 25,
      level: "متوسط",
      summary:
        "DbContext ليس مجرد غلاف لـ SQL. سنفهم وحدة العمل، خريطة الهوية، تتبّع التغييرات، والترحيلات — وأين تظهر التكلفة الخفية.",
      keywords: ["EF Core", "DbContext", "Change Tracker", "migrations", "Npgsql", "concurrency token"],
      objectives: [
        "تشرح دورة حياة DbContext ودور Change Tracker.",
        "تكتب علاقات وقيودًا عبر Fluent API.",
        "تدير الترحيلات (Migrations) بأمان.",
        "تستخدم Concurrency Token لمنع lost updates.",
      ],
      concept: `
        <p><strong>EF Core</strong> هو ORM رسمي: يحوّل LINQ إلى SQL، ويتتبّع التغييرات، ويحفظها في معاملة واحدة. <code>DbContext</code> يمثّل <strong>وحدة عمل</strong> (Unit of Work) و<strong>خريطة هوية</strong> (Identity Map): لكل مفتاح كائن واحد فقط داخل الجلسة، حتى لو استعلمت عنه مرتين.</p>
        <p>دورة الحياة النموذجية:</p>
        <ol>
          <li>تفتح نطاقًا (في ASP.NET Core: الطلب).</li>
          <li>تستعلم، فيُسجَّل الكائن في Change Tracker بحالة <code>Unchanged</code>.</li>
          <li>تعدّل خاصية، فتصبح الحالة <code>Modified</code>.</li>
          <li><code>SaveChangesAsync</code> يبني أوامر UPDATE المطلوبة فقط، وينفّذها في معاملة.</li>
          <li>يُدمَّر الـ Context في نهاية الطلب ويُعاد الاتصال إلى البركة.</li>
        </ol>
        <h3>لماذا Scoped؟</h3>
        <p>لأن Change Tracker يحمل حالة. لو عاش Context طويلًا، لتراكمت الكائنات، وظهرت بيانات قديمة، وحدثت أخطاء «A second operation started on this context». الـ Scoped يضمن جلسة نظيفة لكل طلب، ويجعل التزامن بلا مشاركة حالة.</p>
        <h3>الترحيلات</h3>
        <p><code>dotnet ef migrations add InitialCreate</code> يقرأ نموذجك ويولّد كود C# لإنشاء الجداول. ثم <code>dotnet ef database update</code> يطبّقه. الترحيلات يجب أن تكون في Git، وأن تُطبَّق في CI/CD كخطوة منفصلة، لا عبر <code>EnsureCreated</code> في الإنتاج (فهي تتجاوز نظام الترحيلات كله).</p>
        <h3>التزامن</h3>
        <p>سيناريو <em>Lost Update</em>: موظفان يفتحان نفس المنتج ويعدّلان السعر. الثاني يحفظ فوق الأول دون أن يدري. الحل: <code>RowVersion</code> أو <code>xmin</code> في PostgreSQL كـ <strong>Concurrency Token</strong>، فيفشل التحديث الثاني بـ <code>DbUpdateConcurrencyException</code> وتقرر أنت: أعد المحاولة أم أبلغ المستخدم.</p>
      `,
      compare: {
        intro: `<p>ADO.NET يمنحك تحكمًا كاملًا مقابل كود يدوي. EF Core يقلّل الكود لكن يخفي بعض التكلفة. المقارنة ليست «أيهما أفضل» بل «ما الذي تريد إدارته».</p>`,
        before: {
          label: "ADO.NET يدوي",
          lang: "csharp",
          title: "ProductRepository.cs",
          code: `public async Task<Product?> GetAsync(int id, CancellationToken ct)
{
    const string sql = @"SELECT id, name, sku, price
                         FROM products WHERE id = @id";

    await using var connection = new NpgsqlConnection(_connectionString);
    await connection.OpenAsync(ct);

    await using var command = new NpgsqlCommand(sql, connection);
    command.Parameters.AddWithValue("id", id);

    await using var reader = await command.ExecuteReaderAsync(ct);
    if (!await reader.ReadAsync(ct)) return null;

    return new Product
    {
        Id = reader.GetInt32(0),
        Name = reader.GetString(1),
        Sku = reader.GetString(2),
        Price = reader.GetDecimal(3)
    };
}`,
          points: [
            "تحكم كامل في SQL والأداء.",
            "كتابة يدوية لكل استعلام وكل علاقة.",
            "أخطاء الأعمدة والأسماء تظهر وقت التشغيل.",
          ],
        },
        after: {
          label: "EF Core",
          lang: "csharp",
          title: "ProductRepository.cs",
          code: `public sealed class ProductRepository(SouqDbContext db) : IProductRepository
{
    public Task<Product?> GetAsync(int id, CancellationToken ct) =>
        db.Products.FirstOrDefaultAsync(p => p.Id == id, ct);

    public Task<List<Product>> ListAsync(CancellationToken ct) =>
        db.Products
          .AsNoTracking()
          .OrderBy(p => p.Name)
          .Take(100)
          .ToListAsync(ct);
}

// SouqDbContext.cs
public sealed class SouqDbContext(DbContextOptions<SouqDbContext> options)
    : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(p => p.Id);
            entity.Property(p => p.Name).HasMaxLength(200).IsRequired();
            entity.Property(p => p.Sku).HasMaxLength(20).IsRequired();
            entity.HasIndex(p => p.Sku).IsUnique();
            entity.Property(p => p.Price).HasPrecision(18, 2);
            entity.Property(p => p.Version).IsRowVersion();
        });
    }
}`,
          points: [
            "استعلامات آمنة الأنواع وقابلة للتركيب.",
            "العلاقات والقيود موصوفة في مكان واحد.",
            "سهل الاختبار مع InMemory أو Testcontainers.",
          ],
        },
        verdict: `<p>EF Core ليس «إخفاء SQL»، بل طبقة تحويل. تعامل معه كأداة تُنتج SQL، وراقب هذا SQL. في المشاريع الصغيرة يوفر أسابيع؛ في المسارات الحرجة قد تحتاج استعلامات مُحسّنة يدويًا أو <code>FromSql</code> — وهذا مسموح تمامًا.</p>`,
      },
      walkthrough: [
        {
          title: "استعلام متتبع",
          code: `var product = await db.Products\n    .SingleAsync(p => p.Id == id);\n\nproduct.ChangePrice(new Money(120, "SAR"));\nawait db.SaveChangesAsync();`,
          lang: "csharp",
          body: `<p>الاستعلام الافتراضي متتبع. EF يحتفظ بالكيان في Change Tracker ويسجّل التغيير. <code>SaveChanges</code> ينتج UPDATE. لا تحتاج <code>Update()</code> لكيان متتبع. هذا مناسب للكتابة، لكنه يحمل تكلفة ذاكرة في القراءة الكبيرة.</p>`
        },
        {
          title: "AsNoTracking للقراءة",
          code: `var products = await db.Products\n    .AsNoTracking()\n    .Where(p => p.IsActive)\n    .Select(p => new ProductDto(p.Id, p.Name, p.Price.Amount))\n    .ToListAsync();`,
          lang: "csharp",
          body: `<p><code>AsNoTracking</code> يمنع الاحتفاظ بالكيانات. مناسب لـAPI للقراءة. مع <code>Select</code> تجلب الأعمدة المطلوبة فقط. لا تستخدمه إذا ستعدّل ثم تحفظ. لا تعتمد عليه لتحسين استعلام بطيء بلا فهرس/projection.</p>`
        },
        {
          title: "Identity Map",
          code: `var a = await db.Products.SingleAsync(p => p.Id == id);\nvar b = await db.Products.SingleAsync(p => p.Id == id);\n\nConsole.WriteLine(ReferenceEquals(a, b)); // True`,
          lang: "csharp",
          body: `<p>داخل نفس <code>DbContext</code>، EF يعيد نفس النسخة للكيان نفسه. هذا Identity Map. يمنع تعارض النسخ. لكنه يعني أن الكائن قد يحمل حالة قديمة إذا عدّلته قاعدة البيانات خارج السياق. لا تشارك <code>DbContext</code> بين طلبات.</p>`
        },
        {
          title: "Attach وUpdate",
          code: `var product = new Product { Id = id };\ndb.Products.Attach(product);\nproduct.ChangePrice(price);\nawait db.SaveChangesAsync();`,
          lang: "csharp",
          body: `<p><code>Attach</code> يبدأ التتبع بحالة Unchanged. ثم التغيير يحدد الحقول. <code>Update</code> يعلّم كل الحقول معدّلة، وقد يكتب قيمًا لم تقصدها. فضّل تحميل الكيان أو Attach + تعديل محدد. احذر من كيانات detached تحمل حالة قديمة.</p>`
        },
        {
          title: "Detached Graph",
          code: `var order = new Order { Id = id };\norder.Lines.Add(new OrderLine(...));\ndb.Orders.Update(order);\nawait db.SaveChangesAsync();`,
          lang: "csharp",
          body: `<p>الرسم المنفصل معقد. <code>Update</code> قد يعلّم السطور الجديدة/القديمة كلها. قد تحذف سطورًا لم تقصدها. حمّل الرسم المتتبع وعدّله، أو استخدم عمليات محددة. اختبر SQL الناتج. لا تعتمد على التخمين.</p>`
        },
        {
          title: "Projection بدل التتبع",
          code: `var dto = await db.Orders\n    .AsNoTracking()\n    .Where(o => o.Id == id)\n    .Select(o => new OrderDto(\n        o.Id,\n        o.Status,\n        o.Lines.Select(l => new LineDto(l.ProductId, l.Quantity)).ToList()))\n    .SingleAsync();`,
          lang: "csharp",
          body: `<p>Projection يقلل البيانات والذاكرة. EF يترجمه إلى SQL بأعمدة محددة. لا تحتاج تتبعًا لعرض DTO. اختبر SQL. لا تضع منطقًا معقدًا داخل Select لا يترجم. هذا أفضل من تحميل الرسم كاملًا ثم تحويله.</p>`
        },
        {
          title: "نطاق قصير",
          code: `using var scope = scopeFactory.CreateScope();\nvar db = scope.ServiceProvider.GetRequiredService<SouqDbContext>();\nawait ProcessBatchAsync(db);\n// ينتهي النطاق ويتخلص من الـcontext`,
          lang: "csharp",
          body: `<p><code>DbContext</code> ليس thread-safe. لا تشاركه بين مهام متوازية. في worker، أنشئ نطاقًا لكل دفعة. لا تحتفظ به طويلًا. هذا يمنع تراكم Change Tracker وبيانات قديمة. استخدم cancellation.</p>`
        },
        {
          title: "قاعدة القرار",
          code: `قراءة DTO -> AsNoTracking + Select\nتعديل كيان -> tracked + SaveChanges\nرسم منفصل -> حمّل/عدّل أو عملية محددة\nخارج الطلب -> scope جديد`,
          lang: "text",
          body: `<p>اختر حسب العملية. لا تجعل كل شيء متتبعًا أو غير متتبع. راقب الذاكرة وعدد الاستعلامات. اختبر السلوك، لا نوع التتبع فقط. التتبع تفصيل أداء/سلامة، وليس شعارًا.</p>`
        }
      ],
      internals: `
        <p>عند أول استعلام، يبني EF Core <strong>Model</strong> من خصائصك وFluent API. هذا البناء يكلّف وقتًا، ولهذا يُنصح بتسخين التطبيق أو استخدام compiled model في السيناريوهات الحساسة للبدء. ثم يُترجم تعبير LINQ إلى شجرة استعلام، تُحوَّل إلى SQL وتُخزَّن في ذاكرة مؤقتة حسب شكل الاستعلام.</p>
        <p><strong>Change Tracker</strong> يحتفظ بكل كائن ونسخة من قيمه الأصلية (Snapshot). عند <code>SaveChanges</code> يقارن الحالي بالأصلي ليبني التغييرات. هذه المقارنة تكلّف ذاكرة ووقتًا يتناسبان مع عدد الكائنات المتتبَّعة. في القراءة فقط، استخدم <code>AsNoTracking</code> لتجنّب هذه التكلفة بالكامل.</p>
        <p>الاتصالات تُدار عبر <strong>Connection Pooling</strong> في مزوّد قاعدة البيانات. فتح اتصال وإغلاقه ليس إنشاء Socket جديدًا كل مرة. لكن إبقاء Context حيًّا لا يبقي الاتصال مفتوحًا بالضرورة؛ EF يفتحه عند الحاجة ويغلقه. المشكلة الحقيقية هي الحالة المتراكمة والتزامن.</p>
        <p>الترحيلات نفسها كود C# يمكن مراجعته. لا تعدّل ترحيلًا طُبّق في الإنتاج؛ أنشئ ترحيلًا جديدًا. وإذا احتجت تغييرًا خطيرًا (حذف عمود)، فخطط له على مراحل: أضف الجديد، انسخ البيانات، أوقف القديم، ثم احذفه.</p>
      `,
      internalsTable: {
        head: ["العملية", "التكلفة", "ملاحظة"],
        rows: [
          ["Tracking query", "Snapshot + Dictionary", "مناسب للكتابة"],
          ["AsNoTracking", "أقل ذاكرة وأسرع", "للقراءة فقط"],
          ["SaveChanges", "معاملة + أوامر مجمّعة", "افتراضيًا معاملة واحدة"],
          ["Include", "JOIN أو استعلامات إضافية", "احترس من التكرار"],
        ],
      },
      tips: [
        {
          title: "لا تحتفظ بـ DbContext",
          body: "لا تخزّنه في Singleton ولا في حقل static ولا في BackgroundService. استخدم نطاقًا لكل عملية. هذا يحل معظم أخطاء «context disposed» و«second operation».",
        },
        {
          title: "لا تستخدم EnsureCreated في الإنتاج",
          body: "تتجاوز نظام الترحيلات وقد تفشل في التحديثات. استخدم <code>dotnet ef database update</code> أو bundle في CI/CD.",
        },
        {
          title: "أضف فهارس لكل ما تستعلم به",
          body: "المفتاح الأساسي مفهرس تلقائيًا، لكن <code>Sku</code> و<code>CategoryId</code> و<code>CreatedAt</code> لا. راجع خطط الاستعلام قبل الإنتاج.",
        },
        {
          title: "استخدم Concurrency Token",
          body: "أضف <code>xmin</code> في PostgreSQL أو <code>rowversion</code> في SQL Server لمنع الكتابة فوق تغييرات الآخرين. تعامل مع الاستثناء كحالة عمل، لا كخطأ نظام.",
        },
      ],
      quiz: [
        {
          q: "ما دور Change Tracker؟",
          options: [
            "يحفظ الاستعلامات في Redis.",
            "يتتبّع الكائنات وقيمها الأصلية ليبني أوامر التحديث.",
            "يدير اتصالات الشبكة فقط.",
            "ينشئ ملفات الترحيل تلقائيًا.",
          ],
          answer: 1,
          explain:
            "يحتفظ بالكائنات وحالتها (Added/Modified/Deleted) وينتج أوامر SQL عند SaveChanges.",
        },
        {
          q: "لماذا نستخدم AsNoTracking في القراءة؟",
          options: [
            "لتجاهل قيود قاعدة البيانات.",
            "لتجنّب تكلفة التتبّع والـ Snapshot وتسريع الاستعلامات.",
            "لأنه يمنع SQL Injection.",
            "لأنه يفعّل التخزين المؤقت تلقائيًا.",
          ],
          answer: 1,
          explain:
            "بدون تتبّع لا تُحفظ نسخ من القيم ولا تُسجَّل الكيانات في Identity Map، فتقل الذاكرة والوقت.",
        },
        {
          q: "ما أفضل مكان لتطبيق الترحيلات في الإنتاج؟",
          options: [
            "داخل Program.cs عند كل إقلاع.",
            "كخطوة نشر منفصلة/CI-CD بعد نسخ احتياطي.",
            "يدويًا على قاعدة الإنتاج دون سجل.",
            "عبر EnsureCreated.",
          ],
          answer: 1,
          explain:
            "الترحيل خطوة نشر مدارة، لا أثر جانبي لكل إقلاع. هذا يمنع سباقات التوسع الأفقي ويسمح بالتراجع.",
        },
      ],
      capstone: {
        title: "DbContext والترحيل الأول",
        goal: "نربط Souq.NET بقاعدة PostgreSQL عبر EF Core، وننشئ أول جدول Products بترحيل قابل للمراجعة.",
        tasks: [
          "أضف حزم Npgsql.EntityFrameworkCore.PostgreSQL وMicrosoft.EntityFrameworkCore.Design.",
          "أنشئ <code>SouqDbContext</code> مع <code>DbSet&lt;Product&gt;</code> وإعدادات Fluent API.",
          "شغّل <code>dotnet ef migrations add InitialCreate</code> وراجع ملف الترحيل.",
          "شغّل <code>dotnet ef database update</code> وتأكد من وجود الجدول.",
          "أضف بيانات Seed لمنتج واحد على الأقل.",
        ],
        code: {
          lang: "csharp",
          title: "تسجيل DbContext",
          code: `builder.Services.AddDbContext<SouqDbContext>(options =>
{
    options.UseNpgsql(
        builder.Configuration.GetConnectionString("Default"),
        npgsql => npgsql.EnableRetryOnFailure(3));

    if (builder.Environment.IsDevelopment())
        options.EnableDetailedErrors().EnableSensitiveDataLogging();
});`,
        },
      },
    },
    {
      id: "efcore-performance",
      title: "EF Core Performance: N+1 / AsNoTracking / الترقيم",
      duration: 27,
      level: "متقدم",
      summary:
        "استعلام واحد بطيء أفضل من مئة استعلام سريع. سنكشف N+1، ونقصّ التتبّع، ونستخدم Projection وKeyset Pagination وفهارس صحيحة.",
      keywords: ["N+1", "AsNoTracking", "projection", "pagination", "keyset", "AsSplitQuery", "index"],
      objectives: [
        "تكتشف N+1 وCartesian Explosion.",
        "تستخدم Projection لاختيار الأعمدة المطلوبة فقط.",
        "تطبّق ترقيمًا فعّالًا وآمنًا.",
        "تقيس التحسين بـ SQL وBenchmark بدل التخمين.",
      ],
      concept: `
        <p><strong>N+1</strong> هو أشهر عدو: تستعلم عن 100 منتج (استعلام واحد)، ثم داخل حلقة تقرأ تصنيف كل منتج (100 استعلام). المجموع 101 رحلة ذهاب وعودة إلى قاعدة البيانات. حتى لو كان كل استعلام سريعًا، فالشبكة والتأخير يقتلان الأداء.</p>
        <p>يظهر N+1 غالبًا مع <em>Lazy Loading</em>: الخاصية <code>product.Category.Name</code> تُحمَّل عند الوصول. الحل ليس «إضافة Include لكل شيء»، بل <strong>تحديد شكل البيانات المطلوبة</strong> مسبقًا عبر Projection:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>var items = await db.Products
    .AsNoTracking()
    .Where(p =&gt; p.IsActive)
    .OrderBy(p =&gt; p.Id)
    .Select(p =&gt; new ProductListItem(
        p.Id, p.Name, p.Price, p.Category.Name))
    .Take(50)
    .ToListAsync(ct);</code></pre>
        <p>هذا يُنتج SQL واحدًا يختار الأعمدة الأربعة فقط، بلا تتبّع، وبلا تحميل كيانات كاملة. الفرق في الذاكرة والزمن كبير جدًا في القوائم.</p>
        <h3>الترقيم ليس Skip/Take دائمًا</h3>
        <p><code>Skip(10000).Take(20)</code> يجبر قاعدة البيانات على قراءة وتجاهل 10000 صف. في الجداول الكبيرة، استخدم <strong>Keyset Pagination</strong>:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>var page = await db.Products
    .Where(p =&gt; p.Id &gt; lastId)
    .OrderBy(p =&gt; p.Id)
    .Take(20)
    .ToListAsync(ct);</code></pre>
        <p>هذا يستخدم الفهرس مباشرة ويبدأ من الموضع المطلوب. الثمن: لا يمكن القفز إلى صفحة رقم 50 مباشرة، لكن واجهات العرض الحديثة تستخدم «تحميل المزيد» أصلًا.</p>
        <h3>Include المتعدد</h3>
        <p><code>Include(p =&gt; p.Images).Include(p =&gt; p.Reviews)</code> قد يُنتج <em>Cartesian Explosion</em>: كل صورة تتكرر مع كل مراجعة. الحل: <code>AsSplitQuery()</code> لتنفيذ استعلامات منفصلة، أو Projection مباشر. قِس الفرق؛ أحيانًا الاستعلام الواحد أسرع، وأحيانًا المنفصل.</p>
      `,
      compare: {
        intro: `<p>نفس قائمة المنتجات: الأولى تختار كل شيء وتتبّع كل شيء؛ الثانية تختار ما تحتاجه فقط. لاحظ الفرق في SQL والذاكرة.</p>`,
        before: {
          label: "تحميل كامل + حلقة",
          lang: "csharp",
          title: "ProductsService.cs",
          code: `var products = await db.Products.ToListAsync(ct); // كل الأعمدة

var result = new List<ProductDto>();
foreach (var product in products)
{
    // N+1: استعلام لكل منتج
    var category = await db.Categories
        .FirstAsync(c => c.Id == product.CategoryId, ct);

    result.Add(new ProductDto(
        product.Id, product.Name, product.Price,
        category.Name));
}

return result;`,
          points: [
            "101 استعلام بدل واحد.",
            "تحميل أعمدة غير مستخدمة.",
            "تتبّع 100 كائن بلا حاجة.",
          ],
        },
        after: {
          label: "Projection + NoTracking",
          lang: "csharp",
          title: "ProductsService.cs",
          code: `var items = await db.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .OrderBy(p => p.Id)
    .Select(p => new ProductDto(
        p.Id,
        p.Name,
        p.Price,
        p.Category.Name))
    .Take(50)
    .ToListAsync(ct);

return items;`,
          points: [
            "استعلام واحد بأعمدة محددة.",
            "لا تتبّع ولا Snapshot.",
            "SQL واضح ويمكن فهرسته.",
          ],
        },
        verdict: `<p>الـ Projection هو أهم تحسين في EF Core، لأنه يحدد ما تعبره الشبكة وما يخصصه CLR. قبل أن تفكر في Redis أو microservices، تأكد أن استعلاماتك لا تجلب أعمدة وصفوفًا لا تحتاجها.</p>`,
      },
      walkthrough: [
        {
          title: "N+1",
          code: `var orders = await db.Orders.ToListAsync();\nforeach (var order in orders)\n{\n    var lines = await db.OrderLines\n        .Where(l => l.OrderId == order.Id)\n        .ToListAsync();\n}`,
          lang: "csharp",
          body: `<p>استعلام للأوامر ثم استعلام لكل طلب. مع 100 طلب = 101 استعلام. الحل: <code>Include</code> أو projection. راقب SQL. لا تفترض أن EF يحل ذلك تلقائيًا. N+1 من أكثر أسباب بطء APIs.</p>`
        },
        {
          title: "Projection",
          code: `var items = await db.Orders\n    .AsNoTracking()\n    .Select(o => new OrderSummaryDto(\n        o.Id,\n        o.Status,\n        o.Lines.Count,\n        o.Lines.Sum(l => l.Quantity * l.UnitPrice)))\n    .ToListAsync();`,
          lang: "csharp",
          body: `<p>اطلب ما تحتاجه فقط. EF يترجم <code>Count/Sum</code> إلى SQL. أقل بيانات وأقل ذاكرة. لا تحمّل الكيانات كاملة لعرض قائمة. اختبر SQL. قد تحتاج فهرسًا للأعمدة المستخدمة في الترتيب/الفلترة.</p>`
        },
        {
          title: "AsNoTracking",
          code: `var products = await db.Products\n    .AsNoTracking()\n    .Where(p => p.IsActive)\n    .OrderBy(p => p.Name)\n    .Take(50)\n    .ToListAsync();`,
          lang: "csharp",
          body: `<p>للقراءة فقط. يقلل الذاكرة ووقت التتبع. لا تستخدمه إذا ستعدّل. لا يعوّض عن فهرس أو projection. قِس قبل/بعد. لا تضع <code>AsNoTracking</code> في كل مكان بلا فهم.</p>`
        },
        {
          title: "Compiled Query",
          code: `private static readonly Func<SouqDbContext, Guid, Task<Product?>> GetProduct =\n    EF.CompileAsyncQuery((SouqDbContext db, Guid id) =>\n        db.Products.AsNoTracking().SingleOrDefault(p => p.Id == id));\n\nvar product = await GetProduct(db, id);`,
          lang: "csharp",
          body: `<p>الاستعلامات المتكررة تستفيد من تجميع شجرة التعبير. مناسب للمسارات الساخنة البسيطة. لا تستخدمه لكل استعلام؛ يقلل الوضوح. قِس الفرق. لا يحل مشكلة SQL بطيء أو فهرس ناقص.</p>`
        },
        {
          title: "Split Query",
          code: `var order = await db.Orders\n    .AsSplitQuery()\n    .Include(o => o.Lines)\n    .Include(o => o.Payments)\n    .SingleAsync(o => o.Id == id);`,
          lang: "csharp",
          body: `<p>مع عدة Includes، JOIN واحد قد يضخم الصفوف. <code>AsSplitQuery</code> ينفّذ استعلامات منفصلة. قد يزيد round trips. استخدمه عند تضخم النتائج. اختبر. لا تجعله الافتراضي بلا قياس.</p>`
        },
        {
          title: "Indexes",
          code: `CREATE INDEX ix_orders_user_created\nON orders (user_id, created_at DESC);\n\nCREATE INDEX ix_products_active_name\nON products (name) WHERE is_active;`,
          lang: "sql",
          body: `<p>الفهرس يطابق WHERE/ORDER BY. الفهرس المركب يساعد الترتيب والفلترة. لا تفرط في الفهارس؛ تكلفة كتابة/مساحة. راجع execution plan. استخدم <code>EXPLAIN ANALYZE</code>. لا تخمّن.</p>`
        },
        {
          title: "Pagination",
          code: `var page = await db.Products\n    .AsNoTracking()\n    .Where(p => p.IsActive)\n    .OrderBy(p => p.Name).ThenBy(p => p.Id)\n    .Skip((pageNumber - 1) * pageSize)\n    .Take(Math.Clamp(pageSize, 1, 100))\n    .ToListAsync();`,
          lang: "csharp",
          body: `<p>لا ترجع كل الصفوف. رتّب ترتيبًا فريدًا لصفحات مستقرة. حدد أقصى حجم. <code>Skip/Take</code> قد يبطؤ في الصفحات العميقة؛ استخدم keyset للجداول الكبيرة. أعد بيانات وصفية للعميل.</p>`
        },
        {
          title: "قِس",
          code: `dotnet run -c Release\n# راقب p95 وSQL وعدد الاستعلامات\n# BenchmarkDotNet للمسار الحرج\n# EXPLAIN ANALYZE للاستعلام`,
          lang: "bash",
          body: `<p>لا تحسّن بلا قياس. استخدم logs/OpenTelemetry لعدد الاستعلامات والزمن. BenchmarkDotNet للكود. <code>EXPLAIN ANALYZE</code> لـPostgreSQL. حسّن عنق الزجاجة الحقيقي. التغيير قد يزيد شيئًا آخر.</p>`
        }
      ],
      internals: `
        <p>EF Core يُخزّن خطة الاستعلام (Query Plan) بعد الترجمة، لكنه يعيد التحقق من الشكل عند اختلاف المعاملات. لهذا لا تبنِ استعلامات بأشكال لا نهائية داخل حلقات؛ استخدم معاملات ثابتة. ويمكن استخدام <code>EF.CompileAsyncQuery</code> للاستعلامات المتكررة جدًا لتجاوز جزء من التحليل.</p>
        <p><strong>AsNoTracking</strong> يلغي Identity Map وSnapshot، لكنه يعني أن الكائنات التي تعيدها ليست مرتبطة بالـ Context. إن احتجت تعديلها لاحقًا، فأعد استعلامها متتبَّعة أو استخدم <code>Attach</code>. لا تستخدم NoTracking ثم تتوقع أن <code>SaveChanges</code> يرى تغييراتك.</p>
        <p><strong>Projection</strong> يترجم إلى <code>SELECT</code> محدد. لكن انتبه: استدعاء method مخصص داخل <code>Select</code> قد يفشل في الترجمة أو يُنفَّذ على العميل. إذا رأيت تحذير EF عن «client evaluation»، فالاستعلام يجلب صفوفًا أكثر مما تتوقع.</p>
        <p>الفهارس هي النصف الآخر. <code>WHERE IsActive = true ORDER BY Id</code> قد يحتاج فهرسًا مركّبًا <code>(IsActive, Id)</code> لخدمة الفلترة والترتيب معًا. استخدم <code>EXPLAIN ANALYZE</code> في PostgreSQL لترى هل الخطة Index Scan أم Seq Scan. لا تفهرس كل شيء: كل فهرس يبطئ الكتابة ويزيد المساحة.</p>
      `,
      internalsTable: {
        head: ["المشكلة", "العلامة", "الحل"],
        rows: [
          ["N+1", "مئات الاستعلامات المتشابهة", "Projection أو Include محسوب"],
          ["Cartesian Explosion", "صفوف متضاعفة", "AsSplitQuery أو Projection"],
          ["Skip كبير", "زمن يزداد مع رقم الصفحة", "Keyset pagination"],
          ["Seq Scan", "EXPLAIN يظهر Seq Scan", "فهرس مركّب مناسب"],
        ],
      },
      tips: [
        {
          title: "سجّل SQL في التطوير",
          body: "استخدم <code>EnableSensitiveDataLogging</code> في التطوير فقط، و<code>ToQueryString()</code> لطباعة SQL قبل التنفيذ. لا تنشر هذه الإعدادات إلى الإنتاج.",
        },
        {
          title: "لا ترجع IQueryable",
          body: "إرجاعه يسمح للمستدعي بإضافة استعلامات لا تراها، وقد يسبب N+1 أو تجاوز حدود. أعد نتيجة مادية أو DTO.",
        },
        {
          title: "استخدم ExecuteUpdate للكتل",
          body: "<code>ExecuteUpdateAsync</code> ينفّذ UPDATE واحدًا على الخادم بدل تحميل آلاف الكائنات وتعديلها. مناسب للعمليات الجماعية.",
        },
        {
          title: "قِس قبل وبعد",
          body: "استخدم BenchmarkDotNet أو سجلات EF مع مدة الاستعلام. «يبدو أسرع» ليس دليلًا. سجّل عدد الاستعلامات أيضًا، لا الزمن فقط.",
        },
      ],
      quiz: [
        {
          q: "ما هو N+1؟",
          options: [
            "استعلام واحد يعيد N صفوف.",
            "استعلام أساسي ثم استعلام إضافي لكل عنصر في النتيجة.",
            "خطأ في الترحيلات.",
            "نوع من الفهارس.",
          ],
          answer: 1,
          explain:
            "هو تحميل قائمة ثم استعلام كل علاقة داخل حلقة، فيتحول استعلام واحد إلى N+1 رحلة.",
        },
        {
          q: "أي تقنية تختار الأعمدة المطلوبة فقط؟",
          options: ["Include", "AsNoTracking", "Projection عبر Select", "Lazy Loading"],
          answer: 2,
          explain:
            "Select إلى DTO يترجم إلى SELECT بالأعمدة المحددة فقط، بدل جلب الكيان كاملًا.",
        },
        {
          q: "لماذا Keyset Pagination أفضل من Skip الكبير؟",
          options: [
            "لأنها تعيد بيانات أقل دائمًا.",
            "لأنها تستخدم شرطًا على المفتاح/الفهرس وتبدأ من الموضع مباشرة.",
            "لأنها لا تحتاج ترتيبًا.",
            "لأنها تعمل بدون قاعدة بيانات.",
          ],
          answer: 1,
          explain:
            "Skip يقرأ ويتجاهل الصفوف السابقة، بينما Keyset يبدأ من آخر معرّف عبر الفهرس.",
        },
      ],
      capstone: {
        title: "تحسين قائمة منتجات Souq.NET",
        goal: "نحوّل endpoint القائمة من تحميل كامل إلى استعلام مُحسّن مُقاس، مع ترقيم وفهرس مناسب.",
        tasks: [
          "استبدل <code>ToListAsync</code> الكامل بـ Projection إلى <code>ProductListItem</code>.",
          "أضف <code>AsNoTracking</code> و<code>Take</code> مع حد أقصى.",
          "طبّق Keyset Pagination باستخدام <code>afterId</code>.",
          "أضف فهرسًا مركّبًا على <code>(IsActive, Id)</code> في Fluent API.",
          "اطبع SQL بـ <code>ToQueryString()</code> وقارن عدد الاستعلامات قبل وبعد.",
        ],
        code: {
          lang: "csharp",
          title: "Keyset endpoint",
          code: `group.MapGet("/", async (
    int? afterId,
    IProductReadService service,
    CancellationToken ct) =>
{
    var page = await service.ListAsync(afterId ?? 0, 20, ct);
    return TypedResults.Ok(page);
});

// الاستعلام
var rows = await db.Products
    .AsNoTracking()
    .Where(p => p.IsActive && p.Id > afterId)
    .OrderBy(p => p.Id)
    .Select(p => new ProductListItem(
        p.Id, p.Name, p.Price, p.Category.Name))
    .Take(size)
    .ToListAsync(ct);`,
        },
      },
    },
    {
      id: "domain-modeling",
      title: "Domain Modeling: Entities وValue Objects وAggregates",
      duration: 32,
      level: "متقدم",
      summary:
        "الكود الذي يمنع الحالات غير الصالحة أفضل من الكود الذي يتحقق منها لاحقًا. سنبني نموذج طلب حقيقي يحمي قواعده بنفسه.",
      keywords: ["DDD", "entity", "value object", "aggregate", "invariants", "domain events", "repository", "ubiquitous language"],
      objectives: [
        "تفرّق بين Entity وValue Object.",
        "تحدد Aggregate Root وحدود المعاملة.",
        "تحمي invariants داخل النموذج لا في الـ endpoint.",
        "تستخدم domain events دون ربط المجال بالبنية.",
        "تعزل persistence عبر repository interface."
      ],
      concept: `
        <p><strong>Domain Modeling</strong> يعني تمثيل قواعد العمل بأسماء وسلوك، لا جدولًا من الحقول. إذا كان <code>Order</code> مجرد DTO فيه <code>Status</code> و<code>Total</code>، فأي كود يستطيع جعله <code>Placed</code> بلا منتجات أو تغيير الإجمالي. النموذج الغني يجعل الحالات غير الصالحة غير قابلة للتمثيل.</p>
        <h3>Entity وValue Object</h3>
        <p><strong>Entity</strong> لها هوية مستمرة حتى لو تغيرت خصائصها: <code>Order</code> يبقى نفسه بعد إضافة سطر. <strong>Value Object</strong> تُعرَّف بقيمتها: <code>Money(100, "EGP")</code> يساوي <code>Money(100, "EGP")</code>، ولا معنى لتغييره جزئيًا. اجعل Value Objects immutable وسجلًا صغيرًا. لا تستخدم <code>decimal</code> عاريًا لكل مبلغ إذا كانت العملة جزءًا من المعنى.</p>
        <h3>Aggregate وحدود المعاملة</h3>
        <p><strong>Aggregate</strong> مجموعة كائنات تُحمّل وتُحفظ معًا، وله <strong>Aggregate Root</strong> واحد. <code>Order</code> و<code>OrderLine</code> داخل حد واحد؛ لا تعدّل سطرًا من خارج الطلب. حدود الـ aggregate تحدد ما يمكن حفظه في معاملة واحدة. لا تجعل aggregate ضخمًا يشمل المنتج والمخزون والدفع؛ هذا يسبب تعارضات وأداءً سيئًا. المرجع لكيان آخر يكون بالمعرّف، لا بكائن كامل.</p>
        <h3>Invariants</h3>
        <p>القاعدة الثابتة: «لا يمكن ترتيب طلب فارغ»، «الكمية أكبر من صفر»، «لا يمكن تعديل طلب بعد شحنه». ضعها في النموذج، لا في controller. استخدم constructors خاصة وfactory methods وطرقًا ذات أسماء سلوكية. لا تفتح setters عامة لكل شيء. إذا كان الاختبار يحتاج كسر القاعدة لاختبار مسار آخر، فالتصميم يحتاج مراجعة.</p>
        <h3>Domain Events</h3>
        <p>حدث المجال يصف شيئًا وقع: <code>OrderPlaced</code>. لا تنشر بريدًا أو message broker من داخل الكيان. سجّل الحدث في الـ aggregate، ثم تعامل معه في طبقة التطبيق بعد الحفظ. هذا يبقي المجال نقيًا وقابلًا للاختبار. النشر نفسه يحتاج Outbox لضمان عدم الفقدان.</p>
        <h3>Persistence Ignorance</h3>
        <p>المجال لا يعرف EF Core. عرّف <code>IOrderRepository</code> في طبقة المجال، ونفّذه في Infrastructure. لا تجعل <code>DbContext</code> يظهر في قواعد العمل. هذا يسهّل اختبار الوحدة ويسمح بتغيير التخزين. لكن لا تبالغ: لا تحتاج repository لكل كيان صغير إن كان EF Core كافيًا. الحدود قرار، لا طقس.</p>
      `,
      walkthrough: [
        {
          title: "Value Object للمال",
          code: `public sealed record Money\n{\n    public decimal Amount { get; }\n    public string Currency { get; }\n\n    private Money(decimal amount, string currency)\n    {\n        Amount = amount;\n        Currency = currency;\n    }\n\n    public static Money Of(decimal amount, string currency = "EGP")\n    {\n        if (amount < 0) throw new ArgumentOutOfRangeException(nameof(amount));\n        if (string.IsNullOrWhiteSpace(currency)) throw new ArgumentException(nameof(currency));\n        return new Money(decimal.Round(amount, 2), currency);\n    }\n\n    public Money Add(Money other)\n    {\n        if (other.Currency != Currency) throw new InvalidOperationException("Currency mismatch");\n        return Of(Amount + other.Amount, Currency);\n    }\n}`,
          lang: "csharp",
          body: `<p>الـ constructor خاص، فلا يمكن إنشاء مبلغ سالب خارج factory. <code>Of</code> يتحقق ويقرّب. <code>Add</code> يمنع جمع عملتين مختلفتين. هذا النوع يحمل معنى السعر والعملة معًا، بدل تمرير <code>decimal</code> في كل مكان. استخدام record يعطي قيمة متساوية لكنه لا يمنع البناء المباشر؛ لذلك الـ constructor الخاص مهم.</p>`
        },
        {
          title: "Entity بسلوك لا setters",
          code: `public sealed class Product\n{\n    public Guid Id { get; private set; }\n    public string Name { get; private set; } = null!;\n    public Money Price { get; private set; } = null!;\n    public int Stock { get; private set; }\n\n    public void DecreaseStock(int quantity)\n    {\n        if (quantity <= 0) throw new ArgumentOutOfRangeException(nameof(quantity));\n        if (quantity > Stock) throw new InvalidOperationException("Insufficient stock");\n        Stock -= quantity;\n    }\n}`,
          lang: "csharp",
          body: `<p>لا يوجد <code>Stock = -5</code> من الخارج. كل تغيير يمر عبر <code>DecreaseStock</code> الذي يحمي القاعدة. <code>private set</code> يسمح لـEF Core بالتحميل لكن يمنع التعديل العشوائي. لاحظ أن السعر <code>Money</code> وليس decimal. الاسم <code>DecreaseStock</code> يعبّر عن نية العمل، لا عن تحديث عمود.</p>`
        },
        {
          title: "Aggregate Root",
          code: `public sealed class Order\n{\n    private readonly List<OrderLine> _lines = new();\n    private readonly List<object> _events = new();\n\n    public Guid Id { get; private set; } = Guid.NewGuid();\n    public Guid UserId { get; private set; }\n    public OrderStatus Status { get; private set; } = OrderStatus.Draft;\n    public IReadOnlyCollection<OrderLine> Lines => _lines;\n    public IReadOnlyCollection<object> DomainEvents => _events;\n\n    private Order() { }\n\n    public static Order Create(Guid userId)\n        => new() { UserId = userId };\n}`,
          lang: "csharp",
          body: `<p><code>Order</code> هو الجذر. المجموعة خاصة للقراءة فقط، فلا يستطيع كود خارجي إضافة سطر متجاوزًا القواعد. <code>DomainEvents</code> تُجمع داخل الكيان وتُقرأ لاحقًا. الـ constructor الخاص يستخدمه EF Core. <code>Create</code> هي نقطة الإنشاء العامة. لا تجعل <code>UserId</code> قابلًا للتغيير بعد الإنشاء.</p>`
        },
        {
          title: "أضف سطرًا بقاعدة",
          code: `public void AddLine(Guid productId, Money unitPrice, int quantity)\n{\n    if (Status != OrderStatus.Draft)\n        throw new InvalidOperationException("Order is not editable");\n    if (quantity <= 0)\n        throw new ArgumentOutOfRangeException(nameof(quantity));\n\n    var line = new OrderLine(productId, unitPrice, quantity);\n    _lines.Add(line);\n}`,
          lang: "csharp",
          body: `<p>القاعدة «لا تعديل بعد الطلب» داخل aggregate. لا تعتمد على الـ endpoint لتذكّرها. <code>OrderLine</code> يمكن أن يكون entity صغيرًا داخل الحد. إذا كان المنتج نفسه aggregate آخر، احتفظ بـ<code>productId</code> فقط. لا تمرّر كائن <code>Product</code> كاملًا؛ قد تغيّره من داخل الطلب.</p>`
        },
        {
          title: "احسب الإجمالي في النموذج",
          code: `public Money Total => _lines\n    .Select(l => l.LineTotal)\n    .Aggregate(Money.Of(0), (sum, next) => sum.Add(next));\n\npublic sealed record OrderLine(\n    Guid ProductId, Money UnitPrice, int Quantity)\n{\n    public Money LineTotal => UnitPrice.Multiply(Quantity);\n}`,
          lang: "csharp",
          body: `<p>الإجمالي مشتق، لا حقل قابل للتلاعب. <code>OrderLine</code> تحسب سطرها. هذا يمنع تضاربًا بين <code>Total</code> والمجاميع. إذا كان الحساب مكلفًا جدًا، يمكن تخزينه مع إعادة حسابه عند التغيير، لكن لا تفتحه للتعديل الخارجي. أضف <code>Multiply</code> إلى <code>Money</code> مع التحقق.</p>`
        },
        {
          title: "انتقال حالة صريح",
          code: `public void Place()\n{\n    if (Status != OrderStatus.Draft)\n        throw new InvalidOperationException("Order already placed");\n    if (_lines.Count == 0)\n        throw new InvalidOperationException("Cannot place empty order");\n\n    Status = OrderStatus.Placed;\n    _events.Add(new OrderPlaced(Id, UserId, Total));\n}\n\npublic void Cancel()\n{\n    if (Status is OrderStatus.Shipped or OrderStatus.Delivered)\n        throw new InvalidOperationException("Cannot cancel shipped order");\n    Status = OrderStatus.Cancelled;\n}`,
          lang: "csharp",
          body: `<p>الحالة لا تُكتب من الخارج. <code>Place</code> يتحقق من عدم الفراغ ثم يسجل الحدث. <code>Cancel</code> يمنع الإلغاء بعد الشحن. استخدم enum واضحًا، ولا تقبل string عشوائيًا. إذا احتجت انتقالات معقدة، ارسم state machine واختبر كل انتقال مسموح وممنوع.</p>`
        },
        {
          title: "حدث مجال بسيط",
          code: `public sealed record OrderPlaced(\n    Guid OrderId,\n    Guid UserId,\n    Money Total,\n    DateTimeOffset OccurredAt = default)\n{\n    public DateTimeOffset OccurredAt { get; init; } =\n        OccurredAt == default ? DateTimeOffset.UtcNow : OccurredAt;\n}`,
          lang: "csharp",
          body: `<p>الحدث يحمل بيانات كافية للمستهلك، لا مرجعًا إلى aggregate متغير. استخدم وقتًا UTC. لا تنشر البريد أو HTTP من الكيان. طبقة التطبيق تقرأ الأحداث بعد الحفظ وتنشرها. إن كان النشر يحتاج ضمانًا، استخدم Outbox. الحدث جزء من اللغة المشتركة، فسمّه بصيغة الماضي.</p>`
        },
        {
          title: "Repository في المجال",
          code: `public interface IOrderRepository\n{\n    Task<Order?> FindAsync(Guid id, CancellationToken ct);\n    void Add(Order order);\n    Task SaveChangesAsync(CancellationToken ct);\n}`,
          lang: "csharp",
          body: `<p>المجال يطلب سلوك التخزين، لا <code>DbContext</code>. التنفيذ في Infrastructure يستخدم EF Core. هذا يسهّل fake في اختبار الوحدة. لا تعرّف repository عامًا لكل كيان إن لم تحتج؛ أحيانًا <code>DbContext</code> في طبقة التطبيق كافٍ. الواجهة هنا لأن الطلب aggregate حرج ويستحق حدًا واضحًا.</p>`
        },
        {
          title: "اربط EF بالحقل الخاص",
          code: `builder.HasMany(o => o.Lines)\n    .WithOne()\n    .HasForeignKey("OrderId");\n\nbuilder.Metadata\n    .FindNavigation(nameof(Order.Lines))!\n    .SetPropertyAccessMode(PropertyAccessMode.Field);\n\n// طبّق OwnsOne على OrderLine.UnitPrice في تكوين منفصل.`,
          lang: "csharp",
          body: `<p>EF Core يمكنه الوصول إلى الحقل الخاص عند ضبط <code>PropertyAccessMode.Field</code>. هذا يحافظ على encapsulation. <code>OwnsOne</code> يخزّن <code>Money</code> كأعمدة في نفس الجدول. لاحظ أن <code>Total</code> خاصية محسوبة؛ في الواقع لا تُخزَّن عادة، لذا لا تستخدم هذا التكوين لها مباشرة. طبّق owned type على <code>OrderLine.UnitPrice</code> بدلًا من ذلك. المبدأ: اجعل التكوين يخدم النموذج، لا العكس.</p>`
        },
        {
          title: "اختبر القاعدة",
          code: `[Fact]\npublic void Place_EmptyOrder_Throws()\n{\n    var order = Order.Create(Guid.NewGuid());\n\n    var ex = Assert.Throws<InvalidOperationException>(() => order.Place());\n\n    Assert.Contains("empty", ex.Message);\n}`,
          lang: "csharp",
          body: `<p>اختبار الوحدة يحمي invariant دون قاعدة بيانات. أضف اختبارات للانتقالات: Place مرة واحدة، Cancel بعد الشحن، AddLine بعد Place. لا تختبر نص الرسالة الكامل إن كان عقدًا داخليًا؛ يكفي النوع. هذه الاختبارات أسرع وأوضح من اختبار التكامل للقواعد نفسها.</p>`
        }
      ],
      compare: {
        intro: `<p>النموذجان يمثلان الطلب نفسه، لكن أحدهما يسمح بحالات مستحيلة.</p>`,
        before: {
          label: "Anemic Model",
          lang: "csharp",
          title: "قبل",
          code: `public class Order\n{\n    public Guid Id { get; set; }\n    public string Status { get; set; } = "Draft";\n    public decimal Total { get; set; }\n    public List<OrderLine> Lines { get; set; } = new();\n}\n\n// في endpoint\norder.Status = "Placed";\norder.Total = 0;`,
          points: [
            "أي كود يغيّر الحالة والإجمالي.",
            "لا منع لطلب فارغ.",
            "القواعد موزعة في controllers.",
            "لا يوجد حدث مجال."
          ]
        },
        after: {
          label: "Rich Model",
          lang: "csharp",
          title: "بعد",
          code: `public void Place()\n{\n    if (Status != OrderStatus.Draft)\n        throw new InvalidOperationException("Order already placed");\n    if (_lines.Count == 0)\n        throw new InvalidOperationException("Cannot place empty order");\n\n    Status = OrderStatus.Placed;\n    _events.Add(new OrderPlaced(Id, UserId, Total));\n}`,
          points: [
            "الحالة تُغيّر بسلوك مسمى.",
            "الطلب الفارغ مرفوض.",
            "القاعدة قريبة من البيانات.",
            "الحدث يُسجل مع الانتقال."
          ]
        },
        verdict: `<p>ليس كل مشروع يحتاج DDD كاملًا. لكن عندما تكون القواعد المالية أو انتقالات الحالة حرجة، استثمر في نموذج يحميها بدل مطاردتها في كل endpoint.</p>`
      },
      internals: `
        <p>الـ Aggregate هو وحدة الاتساق. عند الحفظ، تُحفظ تغييرات الجذر والأبناء في معاملة واحدة. لا تشارك كيانًا داخليًا مع aggregate آخر. استخدم المعرّفات للربط. إذا احتجت تعديل مخزون منتجين في طلب واحد، فقد تحتاج معاملة على مستوى التطبيق أو سياسة تعويض، لا aggregate عملاق.</p>
        <p>Value Objects تُخزَّن كأعمدة مدمجة أو عبر value converter. EF Core يحتاج constructor خاصًا أو طريقة تحويل. اختبر mapping في اختبار تكامل. لا تفترض أن كل record قابل للتحويل تلقائيًا. إذا كان النوع معقدًا، استخدم owned type أو عمودين واضحين.</p>
        <h3>Domain Events</h3>
        <p>الأحداث لا تُنشر من الكيان. اجمعها، ثم بعد <code>SaveChanges</code> مرّرها إلى dispatcher. إن أردت ضمان عدم الفقدان، اكتبها في Outbox داخل نفس المعاملة. لا تخلط حدث المجال الداخلي مع حدث تكامل خارجي؛ الثاني عقد بين خدمات ويحتاج schema مستقلة.</p>
        <h3>حدود الـ Aggregate</h3>
        <p>اجعل الـ aggregate صغيرًا. <code>Order</code> مع سطوره معقول. <code>Order</code> مع <code>Product</code> و<code>Customer</code> و<code>Payment</code> ككائنات كاملة غير معقول. المرجع بالمعرّف يقلل التحميل والتضارب. المعاملة الواحدة تحدد الحد، وليس الرسم البياني للعلاقات.</p>
      `,
      internalsTable: {
        head: ["المفهوم", "السؤال", "القرار"],
        rows: [
          ["Entity", "هل لها هوية مستمرة؟", "Order, Product"],
          ["Value Object", "هل تساويها بقيمتها؟", "Money, Address"],
          ["Aggregate", "ما حدود الاتساق؟", "Order + Lines"],
          ["Invariant", "ما الذي يجب ألا يحدث أبدًا؟", "طلب فارغ"],
          ["Domain Event", "ماذا وقع؟", "OrderPlaced"],
          ["Repository", "كيف نحفظ الجذر؟", "واجهة في المجال"]
        ]
      },
      tips: [
        {
          title: "اجعل الحالة غير الصالحة غير قابلة للتمثيل",
          body: "private setters، constructors خاصة، وطرق سلوكية. لا تفتح كل شيء ثم تحقق في controller."
        },
        {
          title: "صغّر الـ Aggregate",
          body: "احتفظ بالكيان الجذري وأبنائه الذين يجب أن يتسقوا معًا. اربط الكيانات الأخرى بالمعرّف."
        },
        {
          title: "لا تربط المجال بـEF",
          body: "استخدم repository interface عند الحاجة، وابقِ DbContext في Infrastructure. اختبر النموذج دون قاعدة بيانات."
        },
        {
          title: "الأحداث تُسجل لا تُنشر",
          body: "اجمع domain events داخل الكيان، وعالجها بعد الحفظ. استخدم Outbox إذا كان الفقدان غير مقبول."
        }
      ],
      quiz: [
        {
          q: "ما الفرق الأساسي بين Entity وValue Object؟",
          options: [
            "Entity أسرع دائمًا.",
            "Entity لها هوية، Value Object تُعرَّف بقيمتها.",
            "Value Object لا يمكن أن تحتوي decimal.",
            "Entity لا تُحفظ في قاعدة البيانات."
          ],
          answer: 1,
          explain: "Order يبقى نفسه بعد تغيّر خصائصه. Money(100, EGP) تساوي Money(100, EGP) ولا تحتاج هوية."
        },
        {
          q: "أين توضع قاعدة «لا يمكن ترتيب طلب فارغ»؟",
          options: [
            "في controller فقط.",
            "داخل Aggregate/Order في طريقة Place.",
            "في قاعدة البيانات فقط.",
            "في الواجهة الأمامية."
          ],
          answer: 1,
          explain: "القاعدة يجب أن تكون قريبة من البيانات وتُفرض من أي مسار. الـ endpoint قد يُنسى أو يُستدعى من خدمة أخرى."
        },
        {
          q: "لماذا لا ينشر الكيان الحدث مباشرة؟",
          options: [
            "لأن الأحداث بطيئة.",
            "لإبقاء المجال نقيًا وقابلًا للاختبار، والنشر بعد الحفظ/عبر Outbox.",
            "لأن الأحداث لا تحتاج بيانات.",
            "لأن EF لا يدعم الأحداث."
          ],
          answer: 1,
          explain: "الكيان يسجل الحدث فقط. طبقة التطبيق تنشره بعد الحفظ، وOutbox يضمن عدم الفقدان."
        }
      ],
      capstone: {
        title: "نموذج طلب Souq",
        goal: "ابنِ Order aggregate يحمي السطور والإجمالي وانتقالات الحالة، واختبر قواعده.",
        tasks: [
          "أنشئ <code>Money</code> immutable مع التحقق والتقريب ومنع اختلاف العملة.",
          "أنشئ <code>Order</code> بمجموعة سطور خاصة و<code>AddLine</code> يرفض الكمية غير الصالحة.",
          "أضف <code>Total</code> محسوبًا و<code>Place</code> يرفض الطلب الفارغ.",
          "أضف <code>OrderPlaced</code> domain event وسجّله عند الانتقال.",
          "اكتب اختبارات وحدة للطلب الفارغ، الكمية السالبة، والإلغاء بعد الشحن."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه النموذج",
          code: `public void Place()\n{\n    if (Status != OrderStatus.Draft)\n        throw new InvalidOperationException("Order already placed");\n    if (_lines.Count == 0)\n        throw new InvalidOperationException("Cannot place empty order");\n\n    Status = OrderStatus.Placed;\n    _events.Add(new OrderPlaced(Id, UserId, Total));\n}`,
        },
      },
    },
    {
      id: "modular-monolith-cqrs",
      title: "Modular Monolith وCQRS-lite",
      duration: 32,
      level: "متقدم",
      summary:
        "لا تبدأ بالـMicroservices. قسّم المونوليث إلى وحدات أعمال بحدود واضحة، وافصل القراءة عن الكتابة عندما يستحق الأمر.",
      keywords: ["modular monolith", "CQRS", "vertical slice", "module boundary", "MediatR", "read model", "architecture tests"],
      objectives: [
        "تقسّم النظام حسب قدرات الأعمال لا حسب الطبقات.",
        "تعزل كل module بعقد عام وتفاصيل داخلية.",
        "تستخدم CQRS-lite للقراءة والكتابة دون تعقيد Event Sourcing.",
        "تحدد حدود المعاملة والاتساق.",
        "تفرّق بين المونوليث النظيف والـDistributed Monolith."
      ],
      concept: `
        <p><strong>Modular Monolith</strong> تطبيق واحد يُنشر كوحدة، لكنه مقسّم داخليًا إلى modules لكل منها مسؤولية وعقد. هذا يعطيك بساطة النشر مع حدود واضحة، ويؤجل تعقيد الشبكة حتى تحتاجها فعلًا. الـMicroservices ليست هدفًا؛ هي تكلفة تشغيلية تُدفع عندما تكون الحدود والفرق المستقلة تستحقها.</p>
        <h3>التقسيم حسب الأعمال</h3>
        <p>لا تقسّم إلى <code>Controllers</code> و<code>Services</code> و<code>Repositories</code> فقط؛ هذه طبقات تقنية. قسّم إلى <code>Catalog</code> و<code>Orders</code> و<code>Payments</code> و<code>Identity</code>. كل module يملك بياناته وسلوكه وعقده. <code>Orders</code> لا يقرأ جدول <code>Products</code> مباشرة؛ يطلب من <code>Catalog</code> عبر عقد. هذا يمنع شبكة اعتماديات لا تنتهي.</p>
        <h3>عقد عام وتفاصيل مخفية</h3>
        <p>كل module يعرض DTOs/Interfaces صغيرة في namespace عام، ويخفي DbContext والكيانات والخدمات الداخلية. استخدم <code>InternalsVisibleTo</code> بحذر، أو اجعل الأنواع <code>internal</code>. اختبار معماري يمنع أي module من الوصول إلى <code>Catalog.Infrastructure</code>. الحدود التي لا تُفرض بالكود تتحلل بسرعة.</p>
        <h3>CQRS-lite</h3>
        <p>CQRS تعني فصل نموذج الكتابة عن نموذج القراءة. لا تحتاج Event Sourcing أو قاعدة قراءة منفصلة. ابدأ بأوامر صغيرة (<code>CreateProduct</code>) واستعلامات مباشرة/Projection. افصل عندما تختلف احتياجات القراءة عن الكتابة، أو عندما تصبح الاستعلامات معقدة. CQRS ليست مكتبة؛ هي قرار حدود.</p>
        <h3>MediatR أم لا؟</h3>
        <p>MediatR يساعد في dispatch ومعالجة cross-cutting concerns، لكنه يضيف طبقة غير مباشرة. استخدمه عندما تحتاج pipeline behaviors (logging/validation/transaction) أو عندما تكثر الأوامر. يمكنك تحقيق نفس الفصل بواجهات صريحة وhandlers مسجلة في DI. لا تضف مكتبة لأنها مشهورة؛ أضفها لأنها تحل مشكلة قابلة للقياس.</p>
        <h3>الاتساق والمعاملات</h3>
        <p>داخل module، معاملة قاعدة بيانات واحدة. بين modules، لا تفترض معاملة موزعة. استخدم أحداث تكامل وOutbox، واقبل الاتساق النهائي. إذا كان <code>Orders</code> يحتاج التأكد من المنتج، اطلب بياناته عبر عقد ثم خزّن snapshot للسعر والاسم. لا تعتمد على قراءة حية من جدول module آخر.</p>
        <h3>متى Microservices؟</h3>
        <p>عندما تحتاج فرقًا مستقلة النشر، أو حدودًا تفرض عزلًا تنظيميًا/تقنيًا، أو مقياسًا مختلفًا. إذا كانت الفرق تعمل على نفس قاعدة البيانات وتنشر معًا، فأنت distributed monolith بتكلفة شبكة. ابدأ modular monolith، وقسّم عندما يصبح الحد مؤلمًا.</p>
      `,
      walkthrough: [
        {
          title: "هيكل module",
          code: `src/\n  Modules/\n    Catalog/\n      Catalog.Contracts/\n      Catalog.Domain/\n      Catalog.Infrastructure/\n      Catalog.Api/\n    Orders/\n      Orders.Contracts/\n      Orders.Domain/\n      Orders.Infrastructure/\n      Orders.Api/`,
          lang: "text",
          body: `<p>كل module يملك طبقاته الداخلية، لكن <code>Contracts</code> فقط هو العام. <code>Catalog.Api</code> يسجّل endpoints، و<code>Infrastructure</code> يملك DbContext. لا تضع كل الكيانات في مشروع مشترك؛ هذا يعيد المونوليث بلا حدود. ابدأ بمجلدات واضحة، ولا تنشئ مشروعًا لكل مجلد إن لم تحتج عزلًا على مستوى التجميع.</p>`
        },
        {
          title: "تسجيل module",
          code: `public static class CatalogModule\n{\n    public static IServiceCollection AddCatalog(\n        this IServiceCollection services, IConfiguration config)\n    {\n        services.AddDbContext<CatalogDbContext>(o =>\n            o.UseNpgsql(config.GetConnectionString("Catalog")));\n        services.AddScoped<IProductReader, ProductReader>();\n        services.AddScoped<CreateProductHandler>();\n        return services;\n    }\n\n    public static IEndpointRouteBuilder MapCatalog(\n        this IEndpointRouteBuilder app)\n    {\n        var group = app.MapGroup("/api/v1/catalog");\n        group.MapGet("/products", GetProducts.Endpoint);\n        group.MapPost("/products", CreateProduct.Endpoint);\n        return app;\n    }\n}`,
          lang: "csharp",
          body: `<p><code>AddCatalog</code> و<code>MapCatalog</code> يخفيان تفاصيل التركيب. <code>Program.cs</code> يصبح قائمة modules، لا ملفًا ضخمًا. كل module يختار DbContext/اتصاله. لا تشارك <code>DbContext</code> بين modules؛ هذا يكسر الحد. استخدم اتصالًا/مخططًا منفصلًا أو على الأقل جداول وملكية واضحة.</p>`
        },
        {
          title: "عقد عام صغير",
          code: `namespace Catalog.Contracts;\n\npublic sealed record ProductSummary(\n    Guid Id,\n    string Name,\n    decimal Price,\n    bool InStock);\n\npublic interface IProductCatalog\n{\n    Task<ProductSummary?> FindAsync(Guid id, CancellationToken ct);\n}`,
          lang: "csharp",
          body: `<p><code>ProductSummary</code> هو كل ما يحتاجه <code>Orders</code>. لا يكشف الكيان أو الحقول الداخلية. الواجهة تعرّف قدرة الأعمال، لا جدولًا. التنفيذ داخل Catalog. إذا احتاج Orders بيانات أكثر لاحقًا، أضف حقلًا متوافقًا أو عقدًا جديدًا؛ لا تفتح الكيان.</p>`
        },
        {
          title: "DbContext خاص بالmodule",
          code: `internal sealed class CatalogDbContext(\n    DbContextOptions<CatalogDbContext> options)\n    : DbContext(options)\n{\n    public DbSet<Product> Products => Set<Product>();\n\n    protected override void OnModelCreating(ModelBuilder modelBuilder)\n    {\n        modelBuilder.HasDefaultSchema("catalog");\n        modelBuilder.ApplyConfigurationsFromAssembly(\n            typeof(CatalogDbContext).Assembly);\n    }\n}`,
          lang: "csharp",
          body: `<p><code>internal</code> يمنع modules أخرى من الوصول إليه. <code>HasDefaultSchema</code> يعزل الجداول بصريًا ويقلل التصادم. لا تضع DbContext مشتركًا لكل النظام. إن كان لديك عدة modules في نفس قاعدة البيانات، ملكية الجداول يجب أن تكون واضحة، ومنع الاستعلام المباشر يُفرض بالمراجعة/الاختبارات.</p>`
        },
        {
          title: "Command واضح",
          code: `public sealed record CreateProductCommand(\n    string Name, decimal Price, int Stock);\n\ninternal sealed class CreateProductHandler(\n    CatalogDbContext db, ILogger<CreateProductHandler> logger)\n{\n    public async Task<Guid> HandleAsync(\n        CreateProductCommand command, CancellationToken ct)\n    {\n        var product = Product.Create(\n            command.Name, Money.Of(command.Price), command.Stock);\n        db.Products.Add(product);\n        await db.SaveChangesAsync(ct);\n        logger.LogInformation("Product {Id} created", product.Id);\n        return product.Id;\n    }\n}`,
          lang: "csharp",
          body: `<p>الأمر يعبّر عن نية: إنشاء منتج. الـhandler داخلي ويطبق قواعد المجال. لا تضع منطق التسعير في endpoint. <code>SaveChanges</code> هنا معاملة واحدة داخل module. إذا احتجت نشر حدث، استخدم Outbox في نفس المعاملة. لا تجعل handler يعرف HTTP؛ هذا يجعله قابلًا للاختبار وإعادة الاستخدام.</p>`
        },
        {
          title: "Query بإسقاط",
          code: `internal sealed class GetProductsHandler(CatalogDbContext db)\n{\n    public Task<List<ProductSummary>> HandleAsync(\n        int take, CancellationToken ct)\n        => db.Products.AsNoTracking()\n            .Where(p => p.IsActive)\n            .OrderBy(p => p.Name)\n            .Take(Math.Clamp(take, 1, 100))\n            .Select(p => new ProductSummary(\n                p.Id, p.Name, p.Price.Amount, p.Stock > 0))\n            .ToListAsync(ct);\n}`,
          lang: "csharp",
          body: `<p>الاستعلام لا يحمّل الكيان كاملًا؛ يسقط إلى DTO. هذا نموذج قراءة مستقل. لا تحتاج repository لكل استعلام؛ EF Core مناسب للقراءة. إذا صار الاستعلام ثقيلًا، أضف فهرسًا أو read model. لا تخلط منطق الكتابة في query handler.</p>`
        },
        {
          title: "Endpoint رفيع",
          code: `internal static class CreateProduct\n{\n    public static async Task<IResult> Endpoint(\n        CreateProductCommand command,\n        CreateProductHandler handler,\n        CancellationToken ct)\n    {\n        var id = await handler.HandleAsync(command, ct);\n        return TypedResults.Created($"/api/v1/catalog/products/{id}", id);\n    }\n}`,
          lang: "csharp",
          body: `<p>الـendpoint يترجم HTTP إلى command ويعيد نتيجة. لا يحوي قواعد عمل. هذا يجعل الاختبار أسهل ويقلل التكرار. استخدم <code>TypedResults</code> لتوثيق الاستجابة. أضف validation filter أو FluentValidation قبل handler. لا تضع try/catch لكل استثناء؛ استخدم معالجًا عامًا.</p>`
        },
        {
          title: "اعزل الاتساق بين modules",
          code: `public sealed class OrderService(\n    IProductCatalog catalog,\n    OrdersDbContext db)\n{\n    public async Task AddItemAsync(Guid orderId, Guid productId,\n        int quantity, CancellationToken ct)\n    {\n        var product = await catalog.FindAsync(productId, ct)\n            ?? throw new NotFoundException("Product not found");\n\n        var order = await db.Orders.FindAsync([orderId], ct)\n            ?? throw new NotFoundException("Order not found");\n\n        order.AddLine(product.Id, Money.Of(product.Price), quantity);\n        await db.SaveChangesAsync(ct);\n    }\n}`,
          lang: "csharp",
          body: `<p><code>Orders</code> لا يقرأ جدول المنتجات. يطلب <code>ProductSummary</code> من عقد Catalog، ثم يخزّن السعر كـsnapshot في سطر الطلب. هذا يحمي الطلب من تغير السعر لاحقًا. لا تحتفظ بكائن Product كاملًا. لاحظ أن العملية معاملة داخل Orders فقط؛ تحديث المخزون يحتاج حدثًا/سياسة منفصلة.</p>`
        },
        {
          title: "CQRS-lite بدون تعقيد",
          code: `// الكتابة: command + handler + domain\n// القراءة: query handler + projection\n// لا Event Sourcing، لا قاعدة قراءة منفصلة في البداية.\n\npublic sealed record ProductDetails(\n    Guid Id, string Name, decimal Price, int Stock);`,
          lang: "csharp",
          body: `<p>ابدأ بأبسط فصل: أمر للكتابة، واستعلام للقراءة. لا تضف أحداثًا لكل تغيير. عندما تصبح القراءة معقدة أو تحتاج أداءً مختلفًا، أضف read model. CQRS لا تعني أن كل شيء يجب أن يكون async message. الاستخدام المفرط يخلق نظامًا يصعب تتبعه.</p>`
        },
        {
          title: "اختبر الحدود المعمارية",
          code: `[Fact]\npublic void Orders_DoesNotReferenceCatalogInfrastructure()\n{\n    var assembly = typeof(Orders.Domain.Order).Assembly;\n    var referenced = assembly.GetReferencedAssemblies();\n\n    Assert.DoesNotContain(referenced,\n        a => a.Name == "Catalog.Infrastructure");\n}`,
          lang: "csharp",
          body: `<p>اختبار معماري يمنع كسر الحدود قبل أن يتحول إلى فوضى. يمكنك استخدام NetArchTest أو فحص المراجع. أضف اختبارات: Domain لا يشير إلى Infrastructure، وOrders لا يشير إلى Catalog.DbContext. الحدود المكتوبة فقط في الوثائق تنسى. اجعلها تفشل في CI.</p>`
        }
      ],
      compare: {
        intro: `<p>المونوليث الطبقي يعمل، لكن كل شيء يعرف كل شيء. المونوليث المعياري يفرض حدودًا داخل عملية واحدة.</p>`,
        before: {
          label: "مونوليث مشترك",
          lang: "csharp",
          title: "قبل",
          code: `public class AppDbContext : DbContext\n{\n    public DbSet<Product> Products { get; set; }\n    public DbSet<Order> Orders { get; set; }\n}\n\n// OrdersService يقرأ Product مباشرة\nvar product = await _db.Products.FindAsync(id);`,
          points: [
            "كل module يعتمد على كل الجداول.",
            "تغيير جدول يكسر modules أخرى.",
            "لا حدود نشر/اختبار واضحة.",
            "CQRS غير موجود؛ نموذج واحد لكل شيء."
          ]
        },
        after: {
          label: "Modules + Contracts",
          lang: "csharp",
          title: "بعد",
          code: `var product = await _catalog.FindAsync(productId, ct)\n    ?? throw new NotFoundException();\n\norder.AddLine(product.Id, Money.Of(product.Price), quantity);\nawait _ordersDb.SaveChangesAsync(ct);`,
          points: [
            "Orders يعتمد على عقد صغير.",
            "Catalog يملك بياناته.",
            "السعر snapshot داخل الطلب.",
            "حدود قابلة للاختبار المعماري."
          ]
        },
        verdict: `<p>الحدود الجيدة تقلل تكلفة التغيير. ابدأ بمونوليث معياري، وفكّك module إلى خدمة فقط عندما تحتاج استقلالًا حقيقيًا.</p>`
      },
      internals: `
        <p>في المونوليث المعياري، كل module يمكن أن يملك DbContext وschema خاصًا. النشر واحد، لكن التطوير والاختبار يمكن أن يكونا مستقلين. الاتصال بين modules عبر واجهات Contracts أو أحداث تكامل. لا تستدعِ handler داخلي من module آخر؛ استخدم العقد العام.</p>
        <p>CQRS-lite تفصل نموذج القراءة عن الكتابة دون Event Sourcing. الأوامر تمر عبر handler وتغيّر aggregate. الاستعلامات تستخدم projection مباشرة. هذا يقلل تعقيد تحميل aggregate كامل للعرض. لا تضف read database منفصلة إلا عند حاجة أداء/شكل بيانات واضحة.</p>
        <h3>الاتساق</h3>
        <p>داخل module: معاملة واحدة. بين modules: أحداث وOutbox واتساق نهائي. لا تفترض أن حفظ الطلب وحفظ المخزون ذريان. استخدم idempotency وتعويضًا. إذا كان الاتساق الفوري مطلوبًا، أعد النظر في حدود الـmodule؛ قد تكون العمليتان في aggregate واحد.</p>
        <h3>Microservices</h3>
        <p>الخدمة المستقلة تحتاج عقدًا، مراقبة، نشرًا، وبيانات. إذا لم تستطع نشرها دون نشر البقية، فأنت distributed monolith. ابدأ monolith، وقسّم عندما تنضج الحدود. الـmodular monolith ليس نسخة أقل؛ هو خيار معماري ناضج.</p>
      `,
      internalsTable: {
        head: ["القرار", "المونوليث المعياري", "Microservices"],
        rows: [
          ["النشر", "واحد", "مستقل لكل خدمة"],
          ["الاتصال", "in-process contracts", "شبكة/عقود"],
          ["المعاملات", "محلية داخل module", "saga/outbox"],
          ["التعقيد", "منخفض/متوسط", "مرتفع"],
          ["الفريق", "مشترك/حدود واضحة", "فرق مستقلة"]
        ]
      },
      tips: [
        {
          title: "قسّم حسب الأعمال",
          body: "Catalog وOrders وPayments، لا Controllers وServices. كل module يملك بياناته وسلوكه."
        },
        {
          title: "أخفِ التفاصيل",
          body: "Contracts فقط عامة. DbContext والكيانات والhandlers داخلية. افرض الحدود باختبار معماري."
        },
        {
          title: "CQRS-lite أولًا",
          body: "أوامر واستعلامات منفصلة دون Event Sourcing. أضف read model فقط عند حاجة واضحة."
        },
        {
          title: "لا تتعجل Microservices",
          body: "إذا كانت الفرق تنشر معًا وتشارك البيانات، فالتقسيم شبكة بلا فائدة. ابدأ monolith معياري."
        }
      ],
      quiz: [
        {
          q: "ما الفرق بين Modular Monolith وMicroservices؟",
          options: [
            "لا فرق.",
            "المونوليث يُنشر كوحدة لكنه مقسم داخليًا؛ الخدمات تُنشر مستقلة.",
            "المونوليث لا يمكن أن يحتوي modules.",
            "Microservices أسرع دائمًا."
          ],
          answer: 1,
          explain: "المونوليث المعياري يحافظ على نشر واحد مع حدود داخلية. Microservices تفصل النشر والشبكة بتكلفة تشغيلية."
        },
        {
          q: "ماذا تعني CQRS-lite؟",
          options: [
            "Event Sourcing إلزامي.",
            "فصل الأوامر عن الاستعلامات دون تعقيد قاعدة قراءة منفصلة.",
            "استخدام Redis فقط.",
            "إلغاء قاعدة البيانات."
          ],
          answer: 1,
          explain: "CQRS-lite تفصل نماذج القراءة/الكتابة، لكنها لا تفرض Event Sourcing أو read database منفصلة."
        },
        {
          q: "كيف يتصل Orders بـCatalog؟",
          options: [
            "بقراءة جدول Products مباشرة.",
            "عبر عقد عام صغير مثل IProductCatalog/ProductSummary.",
            "بنسخ CatalogDbContext.",
            "باستخدام نفس الكيان Product."
          ],
          answer: 1,
          explain: "العقد العام يخفي التفاصيل ويمنع الاعتماد على جدول/كيان module آخر."
        }
      ],
      capstone: {
        title: "تقسيم Souq إلى Modules",
        goal: "افصل Catalog عن Orders بعقد واضح، وطبّق CQRS-lite واختبار حدود.",
        tasks: [
          "أنشئ مجلدات <code>Catalog</code> و<code>Orders</code> مع Contracts/Domain/Infrastructure/Api.",
          "أضف <code>IProductCatalog</code> و<code>ProductSummary</code> كعقد عام فقط.",
          "انقل <code>CatalogDbContext</code> إلى infrastructure الخاص بـCatalog واجعله internal.",
          "افصل <code>CreateProductCommand</code> عن <code>GetProducts</code> query projection.",
          "أضف اختبارًا معماريًا يمنع Orders من الإشارة إلى Catalog.Infrastructure."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه العقد",
          code: `public sealed record ProductSummary(\n    Guid Id, string Name, decimal Price, bool InStock);\n\npublic interface IProductCatalog\n{\n    Task<ProductSummary?> FindAsync(Guid id, CancellationToken ct);\n}`,
        },
      },
    },
    {
      id: "outbox-messaging",
      title: "Outbox & Messaging: لا تفقد الأحداث",
      duration: 32,
      level: "متقدم",
      summary:
        "حفظ الطلب ثم نشر الحدث عمليتان منفصلتان. إذا فشلت الثانية، فقدت النظام. Outbox يحوّل النشر إلى نتيجة مضمونة من نفس المعاملة.",
      keywords: ["Outbox", "at-least-once", "idempotent consumer", "inbox", "SKIP LOCKED", "dead letter", "eventual consistency", "broker"],
      objectives: [
        "تشرح مشكلة dual-write.",
        "تحفظ الحدث في Outbox داخل نفس معاملة البيانات.",
        "تنفّذ عامل نشر آمنًا مع retries وdead letter.",
        "تجعل المستهلك idempotent باستخدام Inbox.",
        "تراقب lag والفشل وتتعامل مع الترتيب."
      ],
      concept: `
        <p>تخيل إنشاء طلب ثم نشر <code>OrderPlaced</code> إلى broker. إذا نجح الحفظ وفشل النشر، لا يعرف باقي النظام بالطلب. وإذا نشرت أولًا ثم فشل الحفظ، يعرف النظام بطلب غير موجود. هذا هو <strong>dual-write problem</strong>؛ لا يمكنك جعل قاعدة البيانات وbroker في معاملة واحدة موثوقة ببساطة.</p>
        <h3>Outbox</h3>
        <p>اكتب الحدث في جدول <code>OutboxMessages</code> داخل نفس معاملة قاعدة البيانات التي تحفظ الطلب. إذا نجحت المعاملة، الحدث محفوظ. عامل خلفي يقرأ الجدول وينشره، ثم يعلّمه كمعالَج. هذا يضمن <strong>at-least-once</strong>: قد ينشر أكثر من مرة، لكن لا يفقد الحدث. المستهلك يجب أن يتحمل التكرار.</p>
        <h3>لماذا at-least-once؟</h3>
        <p>بعد نشر الرسالة قد يتعطل العامل قبل تعليمها. عند إعادة التشغيل ينشرها مرة أخرى. هذا مقبول إذا كان المستهلك idempotent. <strong>Exactly-once</strong> عبر الشبكة والأنظمة الموزعة وهم غالبًا؛ ابنِ على التكرار بأمان بدل البحث عن سحر. استخدم معرف الحدث الفريد لمنع الأثر المزدوج.</p>
        <h3>Inbox للمستهلك</h3>
        <p>المستهلك يحفظ <code>MessageId</code> في جدول Inbox مع أثر العملية في نفس المعاملة. إذا وصل نفس المعرف، يتجاهله. لا تعتمد على فحص «هل عالجت؟» ثم تنفيذ؛ استخدم قيدًا فريدًا أو <code>INSERT ... ON CONFLICT DO NOTHING</code>. هذا يجعل التكرار آمنًا حتى تحت التزامن.</p>
        <h3>العامل والـSKIP LOCKED</h3>
        <p>إذا كان لديك عدة نسخ من العامل، استخدم <code>FOR UPDATE SKIP LOCKED</code> ليجلس كل عامل على صفوف مختلفة دون انتظار. لا تقرأ ثم تحدّث دون قفل، وإلا قد تنشر نفس الرسالة مرتين من عاملين. عالج على دفعات صغيرة، وحدّث الحالة بعد النشر. افصل النشر عن المعاملة الطويلة.</p>
        <h3>الفشل والترتيب</h3>
        <p>أضف عدد المحاولات و<code>NextAttemptAt</code> وbackoff مع jitter. بعد حد أقصى، انقل الرسالة إلى dead letter وأطلق تنبيهًا؛ لا تسمح لرسالة سامة بإيقاف الطابور. للترتيب، استخدم مفتاح partition مثل <code>OrderId</code> في broker، أو تسلسلًا لكل aggregate. النشر المتوازي قد يغيّر الترتيب.</p>
        <h3>متى CDC؟</h3>
        <p>Change Data Capture (مثل Debezium) يقرأ WAL وينشر التغييرات دون جدول Outbox. مفيد لكنه يضيف بنية تحتية وتعقيدًا. ابدأ بـOutbox جدولي واضح. لا تجعل Outbox سجلًا أبديًا؛ احذف/أرشف الرسائل المعالجة بعد فترة، وراقب حجم الجدول.</p>
      `,
      walkthrough: [
        {
          title: "كيان OutboxMessage",
          code: `public sealed class OutboxMessage\n{\n    public Guid Id { get; init; } = Guid.NewGuid();\n    public string Type { get; init; } = null!;\n    public string Payload { get; init; } = null!;\n    public DateTimeOffset OccurredAt { get; init; } = DateTimeOffset.UtcNow;\n    public DateTimeOffset? ProcessedAt { get; set; }\n    public DateTimeOffset? NextAttemptAt { get; set; }\n    public int Attempts { get; set; }\n}`,
          lang: "csharp",
          body: `<p><code>Id</code> هو معرف الرسالة/idempotency. <code>Type</code> يحدد schema، و<code>Payload</code> JSON. <code>ProcessedAt</code> و<code>Attempts</code> لإدارة العامل. لا تخزّن كائنًا كاملًا؛ خزّن بيانات كافية. استخدم <code>OccurredAt</code> UTC. أضف فهرسًا على <code>(ProcessedAt, OccurredAt)</code>.</p>`
        },
        {
          title: "اكتب الطلب والحدث معًا",
          code: `await using var tx = await _db.Database\n    .BeginTransactionAsync(ct);\n\n_db.Orders.Add(order);\n_db.OutboxMessages.Add(new OutboxMessage\n{\n    Type = "OrderPlaced",\n    Payload = JsonSerializer.Serialize(new OrderPlaced(\n        order.Id, order.UserId, order.Total.Amount))\n});\n\nawait _db.SaveChangesAsync(ct);\nawait tx.CommitAsync(ct);`,
          lang: "csharp",
          body: `<p>هذه هي النقطة المركزية: الطلب والحدث في نفس المعاملة. إذا فشل أي جزء، لا يُحفظ شيء. لا تنشر إلى broker هنا. <code>Payload</code> يجب أن يكون عقد تكامل مستقرًا، لا كيان EF. لا تضع كائنات ضخمة أو أسرارًا في الحدث. استخدم serializer موحدًا يدعم الإصدارات.</p>`
        },
        {
          title: "اقرأ الرسائل بأمان",
          code: `SELECT id, type, payload, attempts\nFROM outbox_messages\nWHERE processed_at IS NULL\n  AND (next_attempt_at IS NULL OR next_attempt_at <= now())\nORDER BY occurred_at\nFOR UPDATE SKIP LOCKED\nLIMIT 20;`,
          lang: "sql",
          body: `<p><code>SKIP LOCKED</code> يسمح لعدة عمال بالعمل دون تصادم. <code>LIMIT</code> يبقي الدفعة صغيرة. <code>next_attempt_at</code> يؤجل الفاشلة بدل إعادة المحاولة فورًا. لا تستخدم <code>SELECT</code> عاديًا ثم تحدّث لاحقًا بلا قفل؛ قد تنشر نسختان. نفّذ الالتقاط والتعليم في تدفق واضح.</p>`
        },
        {
          title: "عامل النشر",
          code: `public sealed class OutboxPublisher(\n    IServiceScopeFactory scopes,\n    IMessageBus bus,\n    ILogger<OutboxPublisher> logger) : BackgroundService\n{\n    protected override async Task ExecuteAsync(CancellationToken ct)\n    {\n        while (!ct.IsCancellationRequested)\n        {\n            await PublishBatchAsync(scopes, bus, logger, ct);\n            await Task.Delay(TimeSpan.FromSeconds(2), ct);\n        }\n    }\n}`,
          lang: "csharp",
          body: `<p><code>BackgroundService</code> يعمل طوال عمر التطبيق، لكن لا تحقن <code>DbContext</code> Scoped مباشرة. استخدم <code>IServiceScopeFactory</code> لإنشاء scope لكل دفعة. لا تمسك scope طويلًا. أضف <code>try/catch</code> حول الدورة حتى لا يوقف استثناء العامل كله. سجّل lag وعدد الرسائل.</p>`
        },
        {
          title: "انشر ثم علّم",
          code: `foreach (var message in batch)\n{\n    try\n    {\n        await bus.PublishAsync(message.Type, message.Payload, ct);\n        message.ProcessedAt = DateTimeOffset.UtcNow;\n    }\n    catch (Exception ex)\n    {\n        message.Attempts++;\n        message.NextAttemptAt = DateTimeOffset.UtcNow\n            .AddSeconds(Math.Pow(2, message.Attempts));\n        logger.LogWarning(ex, "Outbox {Id} failed", message.Id);\n    }\n}\nawait db.SaveChangesAsync(ct);`,
          lang: "csharp",
          body: `<p>النشر قد ينجح ثم يفشل الحفظ؛ لذا التكرار ممكن. لا تعتمد على «لن يحدث». استخدم backoff مع jitter لتجنب thundering herd. بعد عدد محاولات أقصى، انقل إلى dead letter ولا تستمر في إعادة المحاولة. لا تسجّل payload كاملًا إن كان يحتوي بيانات حساسة.</p>`
        },
        {
          title: "نظّف الرسائل المعالجة",
          code: `DELETE FROM outbox_messages\nWHERE processed_at < now() - interval '7 days';`,
          lang: "sql",
          body: `<p>Outbox ليس أرشيفًا. احذف المعالجة القديمة أو أرشفها بعد فترة. بدون تنظيف، يصبح الجدول ضخمًا ويبطئ الاستعلامات. احتفظ بما يكفي للتحقيق. شغّل التنظيف في وظيفة منفصلة، لا في مسار النشر الحرج. راقب النمو.</p>`
        },
        {
          title: "Inbox للمستهلك",
          code: `CREATE TABLE inbox_messages (\n    message_id uuid PRIMARY KEY,\n    processed_at timestamptz NOT NULL DEFAULT now()\n);\n\nINSERT INTO inbox_messages(message_id)\nVALUES (@id)\nON CONFLICT (message_id) DO NOTHING;`,
          lang: "sql",
          body: `<p>إذا أدرجت صفًا جديدًا، عالج الرسالة. إذا كان موجودًا، تجاهلها. نفّذ الإدراج وأثر العملية في نفس معاملة المستهلك. هذا يمنع التكرار حتى لو وصلت الرسالة مرتين. لا تستخدم فحصًا منفصلًا ثم إدراجًا؛ سباق التزامن قد يمرر الاثنين.</p>`
        },
        {
          title: "اربط المستهلك بمعاملة",
          code: `await using var tx = await db.Database.BeginTransactionAsync(ct);\n\nvar inserted = await db.Database.ExecuteSqlInterpolatedAsync($@"\n    INSERT INTO inbox_messages(message_id)\n    VALUES ({messageId})\n    ON CONFLICT (message_id) DO NOTHING", ct);\n\nif (inserted == 0) return;\n\norder.MarkAsPaid();\nawait db.SaveChangesAsync(ct);\nawait tx.CommitAsync(ct);`,
          lang: "csharp",
          body: `<p>الإدراج و<code>MarkAsPaid</code> في معاملة واحدة. إذا فشل التحديث، لا يبقى Inbox معلّمًا. إذا نجح الاثنان، التكرار القادم يجد المعرف ويتجاهل. هذا هو جوهر idempotency. لا تفصل «تمت المعالجة» عن الأثر الفعلي.</p>`
        },
        {
          title: "Dead letter والمراقبة",
          code: `// بعد 5 محاولات: انقل إلى outbox_dead_letters\n// وأطلق تنبيهًا: oldest unprocessed، failure rate، lag.\nSELECT count(*) AS pending,\n       min(occurred_at) AS oldest\nFROM outbox_messages\nWHERE processed_at IS NULL;`,
          lang: "sql",
          body: `<p>راقب عدد الرسائل المعلقة وعمر أقدمها. lag المتزايد يعني أن العامل متوقف أو broker بطيء. معدل الفشل المرتفع يعني مشكلة عقد/مستهلك. لا تكتفِ بسجلات النشر؛ راقب النتيجة. Dead letter يحتاج تشغيلًا يدويًا ومراجعة، لا حذفًا صامتًا.</p>`
        },
        {
          title: "حافظ على ترتيب المفتاح",
          code: `await bus.PublishAsync(\n    type: "OrderPlaced",\n    payload: json,\n    partitionKey: order.Id.ToString(),\n    ct);`,
          lang: "csharp",
          body: `<p>استخدم <code>OrderId</code> كمفتاح partition حتى تصل أحداث الطلب نفسه بالترتيب إلى نفس القسم. النشر المتوازي لأحداث نفس الطلب قد يعكس الترتيب. لا تفترض ترتيبًا عالميًا بين الطلبات. إذا كان الترتيب شرطًا، صمّم المستهلك ليتحمله أو استخدم تسلسلًا.</p>`
        }
      ],
      compare: {
        intro: `<p>الكتابة المزدوجة تفصل عمليتين لا يمكن ضمانهما معًا. Outbox يجعلهما قرارًا واحدًا.</p>`,
        before: {
          label: "Dual write",
          lang: "csharp",
          title: "قبل",
          code: `await _db.SaveChangesAsync(ct);\nawait _bus.PublishAsync("OrderPlaced", json, ct);`,
          points: [
            "فشل النشر بعد الحفظ يفقد الحدث.",
            "النشر قبل الحفظ قد ينشر طلبًا غير موجود.",
            "إعادة المحاولة قد تكرر النشر.",
            "لا سجل يمكن إعادة تشغيله."
          ]
        },
        after: {
          label: "Transactional Outbox",
          lang: "csharp",
          title: "بعد",
          code: `await using var tx = await _db.Database.BeginTransactionAsync(ct);\n_db.Orders.Add(order);\n_db.OutboxMessages.Add(outboxMessage);\nawait _db.SaveChangesAsync(ct);\nawait tx.CommitAsync(ct);`,
          points: [
            "الحدث محفوظ مع البيانات.",
            "عامل مستقل ينشر ويعيد المحاولة.",
            "at-least-once مضمون.",
            "المستهلك يمنع التكرار بـInbox."
          ]
        },
        verdict: `<p>Outbox لا يجعل النظام متسقًا فورًا؛ يجعله لا يفقد الأحداث. الاتساق النهائي يحتاج مستهلكًا idempotent ومراقبة.</p>`
      },
      internals: `
        <p>المعاملة المحلية تضمن كتابة الطلب والحدث معًا. بعد commit، العامل يقرأ الحدث. إذا تعطل قبل النشر، يبقى <code>ProcessedAt</code> فارغًا ويعيد المحاولة. إذا تعطل بعد النشر وقبل التعليم، يعيد النشر. لذلك at-least-once هو الضمان الواقعي.</p>
        <p><code>FOR UPDATE SKIP LOCKED</code> يسمح بتعدد العمال. لكنه لا يضمن الترتيب العالمي. استخدم مفتاح partition أو consumer واحد لكل مفتاح. لا تجعل العامل يمسك قفلًا أثناء استدعاء broker طويلًا إن كان ذلك يمنع غيره؛ استخدمclaim/lease أو معالجة دفعية.</p>
        <h3>Idempotency</h3>
        <p>Inbox table مع قيد فريد هو الحل. أثر العملية والمعالجة في نفس المعاملة. إذا كان الأثر خارج قاعدة البيانات (بريد/دفع)، استخدم idempotency key لدى المزود. لا يمكنك ضمان exactly-once عبر خدمتين بقاعدة واحدة فقط؛ صمّم كل خطوة لتكون قابلة للتكرار.</p>
        <h3>Schema والتطور</h3>
        <p>حدث التكامل عقد. أضف حقولًا اختيارية، لا تغيّر معنى حقل. استخدم <code>Type</code> + version مثل <code>OrderPlaced.v1</code>. احتفظ بالتوافق مع المستهلكين القدامى. لا تضع كائنات المجال مباشرة في payload. اختبر المستهلك ضد نسخة الحدث الجديدة.</p>
        <h3>التشغيل</h3>
        <p>راقب lag، أقدم رسالة، معدل الفشل، وحجم dead letter. شغّل التنظيف والأرشفة. اختبر تعطل العامل أثناء النشر. اختبر رسالة سامة. اختبر تكرار نفس الرسالة. هذه الاختبارات أهم من happy path.</p>
      `,
      internalsTable: {
        head: ["العنصر", "الوظيفة", "الخطر"],
        rows: [
          ["Outbox table", "حفظ الحدث مع البيانات", "نمو غير محدود"],
          ["SKIP LOCKED", "تعدد عمال بلا تصادم", "لا يضمن الترتيب"],
          ["Publish + mark", "نشر ثم تعليم", "تكرار بعد التعطل"],
          ["Inbox", "منع أثر مزدوج", "يحتاج نفس المعاملة"],
          ["Backoff", "تأخير المحاولات", "رسالة سامة"],
          ["Dead letter", "عزل الفاشل", "يحتاج تشغيلًا يدويًا"]
        ]
      },
      tips: [
        {
          title: "اكتب الحدث في نفس المعاملة",
          body: "لا تنشر من داخل الكيان ولا بين SaveChanges وCommit. Outbox داخل المعاملة هو الضمان."
        },
        {
          title: "صمّم للمضاعفة",
          body: "at-least-once هو الواقع. استخدم Inbox/idempotency key، واختبر وصول الرسالة مرتين."
        },
        {
          title: "راقب lag",
          body: "عدد الرسائل المعلقة وعمر أقدمها أهم من سجل «تم النشر». راقب dead letter ومعدل الفشل."
        },
        {
          title: "لا تسحق الترتيب",
          body: "استخدم partition key مثل OrderId. لا تفترض ترتيبًا عالميًا بين الطلبات."
        }
      ],
      quiz: [
        {
          q: "ما المشكلة التي يحلها Outbox؟",
          options: [
            "بطء الاستعلامات.",
            "فقدان/تكرار الأحداث عند الجمع بين قاعدة البيانات وbroker.",
            "ضعف تشفير JWT.",
            "زيادة حجم الذاكرة."
          ],
          answer: 1,
          explain: "Outbox يحفظ الحدث مع البيانات في معاملة واحدة، ثم ينشره عامل، فيمنع فقدانه."
        },
        {
          q: "لماذا يجب أن يكون المستهلك idempotent؟",
          options: [
            "لأن الشبكة بطيئة.",
            "لأن Outbox يضمن at-least-once وقد تصل الرسالة أكثر من مرة.",
            "لأن قاعدة البيانات لا تدعم المعاملات.",
            "لتقليل حجم JSON."
          ],
          answer: 1,
          explain: "التكرار ممكن بعد تعطل العامل أو إعادة المحاولة. Inbox/key يمنع الأثر المزدوج."
        },
        {
          q: "ما فائدة FOR UPDATE SKIP LOCKED؟",
          options: [
            "تسريع كل الاستعلامات.",
            "تسمح لعمال متعددين بمعالجة صفوف مختلفة دون انتظار.",
            "تضمن الترتيب العالمي.",
            "تشفّر الرسائل."
          ],
          answer: 1,
          explain: "كل عامل يقفل صفوفًا مختلفة ويتخطى المقفلة. لا تضمن الترتيب، لكنها تمنع التصادم."
        }
      ],
      capstone: {
        title: "Outbox لطلبات Souq",
        goal: "اكتب OrderPlaced في Outbox مع الطلب، وانشره بعامل آمن، واجعل مستهلك الدفع idempotent.",
        tasks: [
          "أضف جدول <code>OutboxMessages</code> مع فهرس على <code>(ProcessedAt, OccurredAt)</code>.",
          "احفظ الطلب والحدث في معاملة واحدة داخل <code>PlaceOrder</code>.",
          "أضف عامل نشر يقرأ دفعات بـ<code>SKIP LOCKED</code> ويعيد المحاولة.",
          "أضف جدول <code>inbox_messages</code> ومستهلكًا يمنع تكرار <code>OrderPlaced</code>.",
          "أضف مراقبة lag وdead letter، واختبر تعطل العامل وتكرار الرسالة."
        ],
        code: {
          lang: "sql",
          title: "Outbox query",
          code: `SELECT id, type, payload\nFROM outbox_messages\nWHERE processed_at IS NULL\nORDER BY occurred_at\nFOR UPDATE SKIP LOCKED\nLIMIT 20;`,
        },
      },
    },
  ],
});
