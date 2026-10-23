/* الوحدة 1 — الأساس: ما هو .NET وكيف تُثبّت بيئتك. */
Academy.addModule({
  id: "foundation",
  title: "الأساس",
  tagline: "قبل أول سطر كود: افهم المنصة، الإصدارات، وأدوات CLI التي ستقضي بها يومك.",
  icon: "◈",
  color: "#8b5cf6",
  lessons: [
    {
      id: "dotnet-ecosystem",
      title: "ما هو .NET فعلًا؟ SDK / Runtime / CLR",
      duration: 16,
      level: "مبتدئ",
      summary:
        "ثلاث كلمات تختلط على كل مبتدئ: SDK وRuntime وCLR. سنفصلها بدقة، ونفهم كيف يتحول كود C# إلى تعليمات ينفّذها المعالج، وأين تقف ASP.NET Core من كل هذا.",
      keywords: ["CLR", "IL", "JIT", "SDK", "Runtime", "BCL", "LTS", "net10.0", "NuGet"],
      objectives: [
        "تفرّق بين SDK وRuntime وCLR وBCL دون خلط.",
        "تعرف لماذا C# تُترجم إلى IL وليست إلى كود آلة مباشرة.",
        "تختار إصدار .NET المناسب للإنتاج (LTS مقابل STS).",
        "تقرأ Target Framework Moniker مثل net10.0 وتفهم دلالته.",
      ],
      concept: `
        <p><strong>.NET ليست لغة برمجة.</strong> هي <em>منصة</em> كاملة: محرّك تشغيل، ومكتبة أساسية ضخمة، وأدوات بناء، ومجمّع حزم. C# هي اللغة الأشهر فوقها، لكن فوقها أيضًا F# وVB.NET. عندما تقول «أنا مطوّر .NET Backend» فأنت تعني: أكتب C# وأشغّلها على runtime .NET وأستخدم ASP.NET Core لبناء HTTP APIs.</p>
        <p>تخيّل مصنعًا: <strong>SDK</strong> هو الورشة كاملة — الآلات والمترجم وأدوات الفحص. <strong>Runtime</strong> هو خط الإنتاج الذي يشغّل المنتج النهائي. <strong>CLR</strong> (Common Language Runtime) هو قلب هذا الخط: يحمّل الكود، يتحقق منه، يترجمه، يدير الذاكرة، ويعالج الاستثناءات. <strong>BCL</strong> (Base Class Library) هو صندوق الأدوات القياسي: كل أنواع <code>System.*</code> من النصوص والملفات والشبكة إلى JSON والتشفير.</p>
        <p>لماذا لا تُترجم C# مباشرة إلى كود آلة؟ لأن ذلك يمنحك <strong>IL</strong> (Intermediate Language): لغة وسيطة مستقلة عن المعالج. عند التشغيل، يقوم الـ CLR بترجمتها عبر <strong>JIT</strong> (Just-In-Time) إلى تعليمات x64 أو ARM64 المناسبة للجهاز. هذه الطبقة هي سرّ «اكتب مرة، شغّل في كل مكان»، وهي أيضًا ما يسمح بتحسينات وقت التشغيل مثل <em>Tiered Compilation</em>.</p>
        <h3>أين تقف ASP.NET Core؟</h3>
        <p>ASP.NET Core ليست runtime منفصلًا؛ إنها <strong>إطار عمل ويب</strong> مبني فوق BCL. تستخدم <code>Microsoft.AspNetCore.*</code> وتضيف: خادم HTTP اسمه Kestrel، نظام Routing، Dependency Injection مدمج، Middleware، ومكوّنات المصادقة والتخزين المؤقت. لذلك كل ما تتعلمه عن CLR وGC وAsync ينطبق حرفيًا على API الذي ستبنيه.</p>
        <h3>LTS أم STS؟</h3>
        <p>إصدارات .NET تأتي بنمطين. <strong>LTS</strong> (Long-Term Support) يُدعم ثلاث سنوات ويُنصح به للإنتاج — مثل .NET 8 و.NET 10. <strong>STS</strong> (Standard-Term Support) يُدعم 18 شهرًا ويجلب الميزات الأحدث — مثل .NET 9. القاعدة العملية: الإنتاج على LTS، والتجربة على STS. في 2026، <code>net10.0</code> هو الخيار الافتراضي لمعظم الفرق.</p>
        <p>وأخيرًا <strong>NuGet</strong>: مدير الحزم. كل مكتبة خارجية — FluentValidation أو Serilog أو EF Core — تُضاف كـ PackageReference في ملف المشروع، ويُثبّت الإصدار بدقة في <code>packages.lock.json</code> عند تفعيل القفل. لا تنسخ DLL يدويًا؛ هذا ليس أسلوب .NET الحديث.</p>
      `,
      walkthrough: [
        {
          title: "اعرف ما المثبّت فعلًا",
          code: `dotnet --info`,
          lang: "bash",
          body: `<p>يعرض الأمر إصدارات SDK المثبتة، وRuntimes المتاحة، وRID (مثل <code>linux-x64</code>)، ومجلد التثبيت. هذا أول أمر تشغّله عند أي مشكلة «لا يعمل المشروع». لاحظ الفرق: قد يوجد Runtime لتشغيل تطبيق، لكن لا يوجد SDK لبناء مشروع. وجود <code>dotnet</code> في PATH لا يعني أن SDK موجودًا.</p>`
        },
        {
          title: "أنشئ مشروعًا من قالب",
          code: `dotnet new webapi -n Souq.Api --framework net10.0`,
          lang: "bash",
          body: `<p><code>dotnet new</code> يقرأ قوالب مثبتة مع الـ SDK. القالب ينشئ <code>Souq.Api.csproj</code> و<code>Program.cs</code> و<code>appsettings.json</code> و<code>Properties/launchSettings.json</code>. لا يترجم C# ولا يشغّل شيئًا؛ هو ينسخ ملفات ويستبدل الاسم. استخدم <code>dotnet new list</code> لرؤية القوالب المتاحة.</p>`
        },
        {
          title: "استعد الحزم",
          code: `dotnet restore`,
          lang: "bash",
          body: `<p>Restore يقرأ المراجع في ملف المشروع، يحل شجرة الحزم وإصداراتها، وينزّل ما ينقص من NuGet. ينتج ملف <code>obj/project.assets.json</code> الذي يصف الحزم والمسارات الدقيقة. هذا الملف هو سبب نجاح البناء دون إنترنت لاحقًا. لا تعدّله يدويًا؛ أعد تشغيل restore بدلًا من ذلك.</p>`
        },
        {
          title: "ابنِ من C# إلى IL",
          code: `dotnet build -c Release`,
          lang: "bash",
          body: `<p><code>build</code> يشغّل MSBuild، الذي يستدعي Roslyn لترجمة C# إلى IL وmetadata. ينتج <code>bin/Release/net10.0/Souq.Api.dll</code> وملفات <code>deps.json</code> و<code>runtimeconfig.json</code>. لا يحدث JIT هنا؛ الترجمة إلى كود الآلة تحدث عند التشغيل. <code>-c Release</code> يفعّل التحسينات ويقلل معلومات التصحيح.</p>`
        },
        {
          title: "شغّل المضيف",
          code: `dotnet run --project src/Souq.Api`,
          lang: "bash",
          body: `<p><code>run</code> يبني إن لزم، ثم يقرأ <code>launchSettings.json</code> ويضبط متغيرات البيئة مثل <code>ASPNETCORE_ENVIRONMENT=Development</code>، ويبدأ <code>Program.cs</code>. يصل التنفيذ إلى <code>app.Run()</code> فيبدأ Kestrel بالاستماع على المنفذ المحدد. أول طلب يمرّ بـ JIT لترجمة methods إلى تعليمات المعالج.</p>`
        },
        {
          title: "أرسل أول طلب HTTP",
          code: `curl -i http://localhost:5000/health`,
          lang: "bash",
          body: `<p><code>curl</code> يفتح اتصال TCP، يرسل طلب HTTP، ثم يقرأ الاستجابة. Kestrel يفكّ الطلب، يمرره عبر Middleware، يطابق Route، ينفّذ الـ endpoint، ويعيد JSON مع <code>Content-Type: application/json</code>. <code>-i</code> يعرض الترويسات وحالة الاستجابة، وهي أفضل من رؤية الجسم فقط عند التشخيص.</p>`
        },
        {
          title: "انشر كتطبيق يعتمد على الإطار",
          code: `dotnet publish -c Release -o ./publish`,
          lang: "bash",
          body: `<p><code>publish</code> ينتج الملفات التي تحتاجها للتشغيل، لا ملفات التطوير. النشر الافتراضي <strong>framework-dependent</strong>: يحتاج الخادم إلى .NET Runtime المطابق. الفائدة حجم أصغر وتحديثات أمنية مركزية. العيب أن الخادم يجب أن يملك الإصدار الصحيح، وإلا ظهر خطأ «framework not found».</p>`
        },
        {
          title: "انشر نسخة مكتفية ذاتيًا",
          code: `dotnet publish -c Release -r linux-x64 --self-contained true -o ./publish-linux`,
          lang: "bash",
          body: `<p><code>-r</code> يحدد RID، و<code>--self-contained</code> يضم Runtime داخل المخرجات. تعمل النسخة على جهاز لا يملك .NET، لكن الحجم أكبر وتحتاج إعادة نشر عند تحديث Runtime. في Docker غالبًا تختار صورة <code>aspnet</code> runtime وتنشر framework-dependent؛ كلا الخيارين صحيح حسب بيئة التشغيل.</p>`
        }
      ],
      compare: {
        intro: `
          <p>الفارق بين .NET Framework القديم و.NET الحديث يظهر بوضوح في ملف المشروع نفسه. الأول كان مرتبطًا بـ Windows وIIS ويحمل قائمة مراجع طويلة؛ الثاني ملف SDK-style قصير يصف الهدف فقط، ويتولّى الـ SDK الباقي.</p>
        `,
        before: {
          label: "مشروع .NET Framework 4.8",
          lang: "xml",
          title: "Legacy.csproj",
          code: `<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <TargetFrameworkVersion>v4.8</TargetFrameworkVersion>
    <UseIISExpress>true</UseIISExpress>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System" />
    <Reference Include="System.Web" />
    <Reference Include="System.Core" />
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
</Project>`,
          points: [
            "مرتبط بـ Windows وIIS فقط.",
            "مراجع إطار العمل تُكتب يدويًا.",
            "النشر يعني نسخ ملفات إلى خادم أو حزمة Web Deploy.",
          ],
        },
        after: {
          label: "مشروع .NET 10 حديث",
          lang: "xml",
          title: "Souq.Api.csproj",
          code: `<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <InvariantGlobalization>false</InvariantGlobalization>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
  </ItemGroup>
</Project>`,
          points: [
            "يعمل على Linux وWindows وmacOS.",
            "المجلد بأكمله مشروع؛ لا قوائم ملفات يدوية.",
            "نشر مكتفٍ بذاته: publish ينتج مجلدًا قابلًا للتشغيل.",
          ],
        },
        verdict: `<p>ملف SDK-style ليس مجرد اختصار بصري: هو عقد بينك وبين MSBuild. الـ SDK يضيف المراجع الضمنية، ويجمع الملفات تلقائيًا، ويوحّد سلوك البناء عبر الأنظمة. ولهذا تستطيع بناء صورة Docker على Linux لنفس المشروع الذي تفتحه على Windows.</p>`,
      },
      internals: `
        <p>داخل CLR تمرّ الشيفرة بأربع مراحل:</p>
        <ol>
          <li><strong>Roslyn</strong> يترجم C# إلى IL مع <em>metadata</em> تصف الأنواع والأعضاء.</li>
          <li><strong>Assembly Loader</strong> يحمّل ملف <code>.dll</code> ويتحقق من الهوية والإصدار.</li>
          <li><strong>JIT</strong> يترجم كل method عند أول استدعاء إلى تعليمات المعالج، ثم يخزّن الناتج.</li>
          <li><strong>GC</strong> يدير الذاكرة المُدارة على heap منظم إلى أجيال (Generations) لتقليل التكلفة.</li>
        </ol>
        <p>هذا يعني أن زمن أول طلب في API قد يكون أطول قليلًا بسبب الـ JIT. في الإنتاج يستخدم .NET <em>Tiered Compilation</em>: ترجمة سريعة غير محسّنة أولًا، ثم ترجمة محسّنة في الخلفية للـ methods الساخنة. ولهذا قد تتحسن أرقام الأداء بعد دقائق من تشغيل التطبيق دون أن تغيّر سطرًا.</p>
        <p>أما <strong>GC</strong> فيقسّم الـ heap إلى Gen0 وGen1 وGen2 و<strong>LOH</strong> (Large Object Heap) للكائنات الأكبر من 85 كيلوبايت تقريبًا. جمع Gen0 رخيص لأنه يمسّ كائنات عمرها قصير. المشكلة تبدأ عندما تخصّص كائنات كبيرة أو كثيرة في مسار الطلب: كل تخصيص يقرّبك من collection، وكل collection يوقف الخيوط لحظيًا. لهذا سنعود لاحقًا إلى <code>Span&lt;T&gt;</code> و<code>ArrayPool</code> وJSON source generation.</p>
        <h3>ما الذي يحدث عند التشغيل؟</h3>
        <p>الأمر <code>dotnet run</code> يبني المشروع أولًا، ثم يبحث عن ملف <code>*.runtimeconfig.json</code> ليعرف إصدار runtime المطلوب، ثم يبدأ عملية المضيف. هذا الملف هو سبب رسالة الخطأ الشهيرة «framework not found»: الـ SDK موجود، لكن الـ Runtime المطابق غير مثبّت.</p>
      `,
      internalsTable: {
        head: ["المكوّن", "وظيفته", "هل تحتاجه للتطوير؟"],
        rows: [
          ["SDK", "المترجم + MSBuild + القوالب + أدوات CLI", "نعم، إلزامي للبناء"],
          ["Runtime", "المضيف الذي يشغّل التطبيق", "نعم، للتشغيل المحلي"],
          ["CLR", "تنفيذ IL، GC، الاستثناءات، الخيوط", "يأتي داخل Runtime"],
          ["BCL", "أنواع System.* القياسية", "يأتي مع Runtime"],
          ["ASP.NET Core", "Kestrel، Routing، DI، Middleware", "حزمة إطار عمل فوق BCL"],
        ],
      },
      tips: [
        {
          title: "ثبّت SDK لا Runtime فقط",
          body: "كثيرون يثبّتون Runtime ثم يتساءلون لماذا لا يعمل الأمر <code>dotnet new</code>. الـ SDK يتضمن Runtime، والعكس غير صحيح. تحقّق بـ <code>dotnet --list-sdks</code> و<code>dotnet --list-runtimes</code>.",
        },
        {
          title: "ثبّت إصدار SDK في المستودع",
          body: "أضف <code>global.json</code> يحدد إصدار SDK مع <code>rollForward: latestPatch</code> حتى لا يختلف البناء بين أعضاء الفريق. هذا يمنع «يعمل عندي فقط» قبل أن يبدأ.",
        },
        {
          title: "لا تخلط .NET Framework بـ .NET 10",
          body: "أسماء مثل <code>System.Web</code> و<code>Global.asax</code> تخصّ الماضي. أي درس أو مكتبة تتحدث عن <em>.NET Framework</em> قد لا تعمل هنا. ابحث دائمًا عن <code>net10.0</code> أو <code>ASP.NET Core</code>.",
        },
        {
          title: "الإنتاج على LTS",
          body: "اختر .NET 10 LTS للخدمات الإنتاجية. ترقية إصدار رئيسي كل 18 شهرًا ليست مشروعًا مجانيًا؛ LTS يمنحك نافذة ثلاث سنوات للاستقرار والتخطيط.",
        },
      ],
      quiz: [
        {
          q: "ما الفرق الجوهري بين SDK وRuntime؟",
          options: [
            "SDK يشغّل التطبيق، وRuntime يبنيه.",
            "SDK يبني ويترجم، وRuntime يشغّل التطبيق.",
            "لا فرق؛ اسمان لنفس المكوّن.",
            "SDK خاص بـ Linux وRuntime خاص بـ Windows.",
          ],
          answer: 1,
          explain:
            "الـ SDK يحتوي المترجم وMSBuild والقوالب، بينما الـ Runtime يحتوي المضيف وCLR الذي ينفّذ التطبيق. تثبيت SDK يتضمن Runtime، لكن العكس غير صحيح.",
        },
        {
          q: "لماذا تترجم C# إلى IL بدلًا من كود آلة مباشرة؟",
          options: [
            "لأن IL أسرع دائمًا من كود الآلة.",
            "لأن IL مستقل عن المعالج ويسمح بتحسينات وقت التشغيل والتوافق عبر الأنظمة.",
            "لأن كود الآلة لا يدعم الكائنات.",
            "لأن IL يخفي الكود المصدري فقط.",
          ],
          answer: 1,
          explain:
            "IL لغة وسيطة محمولة. الـ CLR يترجمها عبر JIT إلى تعليمات المعالج المناسب، ما يتيح العمل على x64 وARM64 وتحسينات مثل Tiered Compilation.",
        },
        {
          q: "أي إصدار تختار لخدمة إنتاجية في 2026؟",
          options: [".NET 9 STS", ".NET 10 LTS", ".NET Framework 4.8", "أحدث preview دائمًا"],
          answer: 1,
          explain:
            ".NET 10 هو LTS بدعم ثلاث سنوات، وهو الخيار المتوازن للإنتاج. STS مناسب للتجربة والميزات الجديدة، و.NET Framework مسار منفصل قديم.",
        },
      ],
      capstone: {
        title: "قرارات المشروع قبل أول سطر",
        goal: "قبل بناء Souq.NET، نثبّت الأساس: إصدار المنصة، اسم الحل، وقاعدة قرارات مكتوبة. المهندس الجيد يبدأ بقرارات واضحة لا بتخمين.",
        tasks: [
          "ثبّت .NET 10 SDK وتحقّق من <code>dotnet --list-sdks</code>.",
          "أنشئ مجلد المشروع <code>Souq</code> وضع فيه ملف <code>README.md</code>.",
          "اكتب في README: الإصدار المختار (net10.0)، سبب اختيار LTS، ونمط النشر المستقبلي (Docker).",
          "أنشئ ملف <code>global.json</code> يثبّت إصدار SDK مع <code>rollForward: latestPatch</code>.",
        ],
        code: {
          lang: "bash",
          title: "تثبيت SDK في المستودع",
          code: `dotnet new globaljson --sdk-version 10.0.100 --roll-forward latestPatch
cat global.json
mkdir Souq && cd Souq
git init`,
        },
      },
    },
    {
      id: "dotnet-cli",
      title: "dotnet CLI: مشروعك الأول بأوامر حقيقية",
      duration: 18,
      level: "مبتدئ",
      summary:
        "الـ CLI هو سطر الأوامر الرسمي لـ .NET: ينشئ المشاريع، يستعيد الحزم، يبني، يشغّل، وينشر. سنتعلم الأوامر التي تستخدمها يوميًا، وكيف يعمل البناء من الداخل.",
      keywords: ["dotnet new", "dotnet run", "MSBuild", "NuGet", "launchSettings", "dotnet watch", "publish"],
      objectives: [
        "تنشئ solution ومشاريع بأوامر <code>dotnet new</code> و<code>dotnet sln</code>.",
        "تفهم دورة restore → build → run → publish.",
        "تقرأ مخرجات البناء وتعرف من أين تأتي الحزم.",
        "تستخدم <code>dotnet watch</code> و<code>dotnet user-secrets</code> بأمان.",
      ],
      concept: `
        <p>الـ CLI ليس بديلًا عن IDE؛ هو الطبقة الحقيقية التي يستدعيها IDE تحت الغطاء. عندما تضغط Run في Visual Studio أو Rider، فإنهما ينفّذان في النهاية أوامر MSBuild وdotnet مشابهة. إتقان الأوامر يجعلك قادرًا على العمل على خادم Linux بلا واجهة، وفي CI/CD، وداخل حاويات Docker.</p>
        <p>دورة الحياة الأساسية أربع خطوات:</p>
        <ul>
          <li><strong>restore</strong>: يقرأ ملفات المشروع، يحلّ شجرة الحزم من NuGet، ويكتب ملفات <code>project.assets.json</code>.</li>
          <li><strong>build</strong>: يشغّل MSBuild، يترجم C# عبر Roslyn، ويضع الناتج في <code>bin/</code> والملفات الوسيطة في <code>obj/</code>.</li>
          <li><strong>run</strong>: يبني إن لزم، ثم يشغّل التطبيق مع متغيرات البيئة من <code>launchSettings.json</code>.</li>
          <li><strong>publish</strong>: ينتج مجلدًا أو حزمة قابلة للنشر، بعد تحسينات مثل trimming أو ReadyToRun عند الطلب.</li>
        </ul>
        <p>القوالب (<em>templates</em>) تختصر البداية: <code>dotnet new webapi</code> ينشئ Minimal API، و<code>dotnet new webapi --use-controllers</code> ينشئ نمط Controllers. القالب ليس سحرًا — يمكنك قراءة ملفاته ثم تعديلها، ويجب أن تفعل.</p>
        <h3>ما هو launchSettings.json؟</h3>
        <p>ملف داخل <code>Properties/</code> يحدد كيف تشغّل التطبيق محليًا: المنفذ، متغيرات البيئة، و<code>ASPNETCORE_ENVIRONMENT</code>. هو <strong>لا يُنشر</strong> مع التطبيق ولا يؤثر على الإنتاج. في Docker ستضبط نفس القيم عبر متغيرات بيئة حقيقية. الخلط بينه وبين <code>appsettings.json</code> من أكثر أسباب الحيرة عند المبتدئين.</p>
        <h3>الأسرار ليست في appsettings</h3>
        <p><code>appsettings.json</code> يُرفع إلى Git. لذلك لا تضع فيه كلمات مرور أو مفاتيح JWT. استخدم <code>dotnet user-secrets</code> محليًا، ومتغيرات بيئة أو Key Vault في الإنتاج. هذا ليس ترفًا أمنيًا؛ إنه الفرق بين تسريب مفتاح في أول أسبوع أو عدمه.</p>
      `,
      walkthrough: [
        {
          title: "أنشئ Solution",
          code: `dotnet new sln -n Souq`,
          lang: "bash",
          body: `<p>الـ Solution ملف تنظيمي يجمع عدة مشاريع: API، Tests، Domain، Infrastructure. لا يشارك في التشغيل ولا يُترجم نفسه؛ هو قائمة مشاريع يستخدمها <code>dotnet build</code> و<code>dotnet test</code>. إنشاءه أولًا يجعل إضافة المشاريع لاحقًا أمرًا واحدًا.</p>`
        },
        {
          title: "أنشئ مشروع API في مجلد",
          code: `dotnet new webapi -n Souq.Api -o src/Souq.Api`,
          lang: "bash",
          body: `<p><code>-n</code> يحدد اسم المشروع وnamespace، و<code>-o</code> يحدد المجلد. فصل المجلدات الآن يمنع فوضى لاحقًا عندما تضيف <code>tests</code> و<code>src</code>. القالب ينشئ مشروعًا قابلاً للتشغيل فورًا، لكنه ليس تصميمك النهائي.</p>`
        },
        {
          title: "أضف المشروع إلى الحل",
          code: `dotnet sln Souq.sln add src/Souq.Api/Souq.Api.csproj`,
          lang: "bash",
          body: `<p>هذا يعدّل ملف الحل ليضم مسار المشروع. لو نسيت هذه الخطوة، سيعمل <code>dotnet build src/Souq.Api</code> لكن <code>dotnet build</code> على الحل قد لا يجد المشروع. تحقق بـ <code>dotnet sln list</code>. في المستودعات الكبيرة، أضف كل مشروع مرة واحدة واحتفظ بالملف في Git.</p>`
        },
        {
          title: "أنشئ مشروع اختبارات",
          code: `dotnet new xunit -n Souq.Api.Tests -o tests/Souq.Api.Tests`,
          lang: "bash",
          body: `<p>قالب xUnit ينشئ مشروع اختبارات وحزمة <code>xunit</code> و<code>Microsoft.NET.Test.Sdk</code>. الاختبارات مشروع منفصل حتى لا تُنشر مع الـ API. ضعه في <code>tests</code> واعطه اسمًا يوضح ماذا يختبر. لا تخلط اختبارات الوحدة والتكامل في مشروع واحد بلا تنظيم.</p>`
        },
        {
          title: "اربط الاختبارات بالمشروع",
          code: `dotnet add tests/Souq.Api.Tests reference src/Souq.Api`,
          lang: "bash",
          body: `<p><code>reference</code> يضيف <code>ProjectReference</code>، فيستطيع مشروع الاختبار رؤية أنواع الـ API. هذا مرجع وقت ترجمة، وليس نسخًا للملفات. لا تجعل مشروع الإنتاج يشير إلى مشروع الاختبارات؛ اتجاه الاعتماد يجب أن يكون من الخارج إلى الداخل فقط.</p>`
        },
        {
          title: "أضف حزمة NuGet",
          code: `dotnet add src/Souq.Api package FluentValidation.AspNetCore --version 11.3.0`,
          lang: "bash",
          body: `<p>الأمر يعدّل <code>.csproj</code> ويضيف <code>PackageReference</code> ثم يعيد restore. تثبيت الإصدار صراحة يجعل البناء قابلًا للتكرار. لا تعتمد على «أحدث إصدار» في الإنتاج؛ قد يتغير السلوك بين نسخة وأخرى. راجع الحزم دوريًا للتحديثات الأمنية.</p>`
        },
        {
          title: "ابنِ الحل كاملًا",
          code: `dotnet build Souq.sln -c Release`,
          lang: "bash",
          body: `<p>البناء على الحل يبني كل المشاريع بترتيب الاعتماديات. <code>-c Release</code> يستخدم إعدادات التحسين. راقب التحذيرات؛ <code>Nullable</code> و<code>TreatWarningsAsErrors</code> يحوّلان التحذيرات المهمة إلى أخطاء في CI. لا تعوّد نفسك على تجاهل التحذيرات.</p>`
        },
        {
          title: "شغّل الاختبارات",
          code: `dotnet test Souq.sln -c Release --no-build`,
          lang: "bash",
          body: `<p><code>test</code> يكتشف مشاريع الاختبار وينفّذها. <code>--no-build</code> يستخدم مخرجات البناء السابقة، ما يسرّع CI بعد خطوة build. النتيجة تعرض عدد النجاح والفشل، وتُعيد exit code غير صفري عند الفشل، وهذا ما يوقف خط الـ CI. لا تنشر إذا فشل الاختبار.</p>`
        },
        {
          title: "راقب التغييرات أثناء التطوير",
          code: `dotnet watch --project src/Souq.Api run`,
          lang: "bash",
          body: `<p><code>watch</code> يراقب الملفات ويعيد البناء/التشغيل عند التغيير. مناسب للتطوير السريع، وليس للإنتاج. بعض التغييرات مثل تعديل توقيع method أو إعدادات قد تحتاج إعادة تشغيل كاملة. لا تعتمد عليه لتجاوز اختبارات أو بناء Release.</p>`
        }
      ],
      compare: {
        intro: `<p>قبل عشر سنوات كانت البداية تعني إنشاء مشروع في Visual Studio، تعديل csproj، واستخدام IIS Express. اليوم تكفي أربعة أوامر للحصول على API يعمل ويستجيب على منفذ محدد.</p>`,
        before: {
          label: "سير عمل يدوي",
          lang: "bash",
          title: "الطريقة القديمة",
          code: `# إنشاء مشروع عبر Visual Studio ثم:
# 1) تعديل csproj يدوياً لإضافة المراجع
# 2) فتح Package Manager Console
Install-Package Newtonsoft.Json
# 3) الضغط على F5 لتشغيل IIS Express
# 4) نشر عبر Web Deploy إلى IIS`,
          points: [
            "خطوات موزعة بين أدوات مختلفة.",
            "صعوبة الأتمتة على Linux أو داخل CI.",
            "إعدادات النشر مرتبطة بجهاز المطوّر.",
          ],
        },
        after: {
          label: "سير عمل CLI حديث",
          lang: "bash",
          title: "الطريقة الحديثة",
          code: `dotnet new sln -n Souq
dotnet new webapi -n Souq.Api -o src/Souq.Api
dotnet sln add src/Souq.Api/Souq.Api.csproj

dotnet add src/Souq.Api package FluentValidation.AspNetCore
dotnet restore
dotnet build -c Release
dotnet run --project src/Souq.Api`,
          points: [
            "كل شيء قابل للتكرار والأتمتة.",
            "نفس الأوامر على Linux وWindows وmacOS.",
            "جاهز للنسخ داخل Dockerfile أو GitHub Actions.",
          ],
        },
        verdict: `<p>الفارق ليس سرعة الكتابة فقط، بل <strong>القابلية للتكرار</strong>. أي أمر تنجح في تشغيله على جهازك يجب أن ينجح في CI. عندما تكون كل خطوة أمرًا نصيًا، تصبح البنية التحتية جزءًا من الكود.</p>`,
      },
      internals: `
        <p>عند تنفيذ <code>dotnet build</code> يحدث تسلسل دقيق:</p>
        <ol>
          <li>يقرأ MSBuild ملف <code>.csproj</code> ويقيّم الخصائص والـ SDK المستورد.</li>
          <li>ينفّذ هدف <code>Restore</code> إن لزم، فيحلّ الإصدارات ويكتب <code>obj/project.assets.json</code>.</li>
          <li>يمرّر الملفات إلى Roslyn، الذي ينتج <code>.dll</code> من نوع assembly مع metadata.</li>
          <li>ينسخ الموارد و<code>appsettings.json</code> إلى <code>bin/&lt;Config&gt;/&lt;tfm&gt;/</code>.</li>
          <li>يكتب <code>deps.json</code> (شجرة التبعيات) و<code>runtimeconfig.json</code> (إصدار runtime والإعدادات).</li>
        </ol>
        <p><strong>البناء التزايدي</strong> (incremental) يعني أن MSBuild يقارن تواريخ الملفات ولا يعيد ترجمة ما لم يتغيّر. لهذا البناء الثاني أسرع بكثير. لكن هذا قد يخفي مشاكل عندما تعتمد على ملفات خارجية؛ نظّف بـ <code>dotnet clean</code> عند الشك.</p>
        <p>أما <strong>NuGet</strong> فيستخدم ذاكرة تخزين مؤقت عالمية في <code>~/.nuget/packages</code>. لا تُنسخ الحزم داخل كل مشروع؛ هذا يجعل المستودع ضخمًا وبطيئًا. ومع <code>packages.lock.json</code> يمكنك تثبيت الشجرة كاملة لضمان بناء متطابق.</p>
        <p>في زمن التشغيل، <code>dotnet run</code> ليس سوى عملية <code>dotnet exec</code> بعد البناء. راقب <code>ASPNETCORE_ENVIRONMENT</code>: عند ضبطه على <code>Development</code> تُفعّل صفحة الاستثناءات التفصيلية وملفات إعداد التطوير؛ في <code>Production</code> تُخفى التفاصيل، وهذا سلوك أمني مقصود.</p>
      `,
      tips: [
        {
          title: "استخدم dotnet watch أثناء التطوير",
          body: "<code>dotnet watch run</code> يعيد البناء والتشغيل عند حفظ الملف. وفّر دقائق يوميًا، لكن تذكّر أنه ليس بديلًا عن اختبارات. أوقفه عند قياس الأداء.",
        },
        {
          title: "لا ترفع bin وobj إلى Git",
          body: "ملفات البناء قابلة لإعادة الإنتاج وضخمة. أضف <code>bin/</code> و<code>obj/</code> و<code>.vs/</code> إلى <code>.gitignore</code>. القالب الرسمي <code>dotnet new gitignore</code> يغطي ذلك.",
        },
        {
          title: "ثبّت الحزم بإصدار صريح",
          body: "تجنّب <code>Version=\"*\"</code> في الإنتاج؛ قد يتغيّر البناء دون تغيير كودك. استخدم إصدارًا محددًا، وفعّل القفل عند الحاجة، وحدّث بوعي عبر PR.",
        },
        {
          title: "الأسرار في user-secrets",
          body: "نفّذ <code>dotnet user-secrets init</code> ثم <code>set Jwt:Key ...</code>. تُخزَّن خارج المستودع وتُحمَّل في Development فقط. في الإنتاج استخدم متغيرات بيئة.",
        },
      ],
      quiz: [
        {
          q: "إلى ماذا يشير <code>dotnet run</code> ضمنيًا؟",
          options: [
            "ينشر التطبيق إلى IIS مباشرة.",
            "يبني المشروع (إن لزم) ثم يشغّل الناتج مع إعدادات التشغيل المحلية.",
            "يشغّل آخر نسخة من NuGet فقط.",
            "ينشئ حاوية Docker تلقائيًا.",
          ],
          answer: 1,
          explain:
            "dotnet run يبني المشروع ثم ينفّذ الناتج. ويقرأ launchSettings.json للمنفذ ومتغيرات البيئة في التطوير المحلي فقط.",
        },
        {
          q: "أين يجب حفظ مفتاح توقيع JWT أثناء التطوير؟",
          options: ["appsettings.json داخل المستودع", "user-secrets أو متغيرات بيئة", "داخل Program.cs كثابت", "في README"],
          answer: 1,
          explain:
            "appsettings.json يُرفع إلى Git، لذا لا يصلح للأسرار. user-secrets مخصص للتطوير المحلي، ومتغيرات البيئة/مدير الأسرار للإنتاج.",
        },
        {
          q: "ما وظيفة ملف project.assets.json؟",
          options: [
            "يحدد منفذ التطبيق.",
            "يصف شجرة الحزم التي حلّها NuGet ومساراتها.",
            "يحتوي كود C# المترجم.",
            "يضبط إعدادات Kestrel.",
          ],
          answer: 1,
          explain:
            "هو ناتج عملية restore ويصف الحزم والإصدارات والمسارات التي سيستخدمها البناء. لا تعدّله يدويًا.",
        },
      ],
      capstone: {
        title: "هيكل حل Souq",
        goal: "نبني الهيكل الذي سنضيف إليه بقية الدروس: Solution واحدة، ومشروع API أولي، وتشغيل ناجح على المنفذ المحلي.",
        tasks: [
          "أنشئ Solution باسم <code>Souq</code> ومشروع <code>Souq.Api</code> من قالب <code>webapi</code>.",
          "أضف المشروع إلى الـ Solution وتحقّق من البناء بـ <code>dotnet build</code>.",
          "شغّل التطبيق بـ <code>dotnet run</code> وافتح <code>/openapi/v1.json</code> للتأكد من عمله.",
          "احذف نقطة النهاية التجريبية WeatherForecast واستبدلها بـ <code>GET /health</code> تعيد <code>{ status: \"ok\" }</code>.",
          "شغّل <code>dotnet watch run</code> وعدّل نص الاستجابة لتتأكد من إعادة التحميل التلقائي.",
        ],
        code: {
          lang: "csharp",
          title: "Program.cs بعد التنظيف",
          code: `var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();`,
        },
      },
    },

    {
      id: "csharp-backend-1",
      title: "C# للـBackend: الأنواع، Nullability، والكائنات",
      duration: 24,
      level: "مبتدئ",
      summary:
        "قبل أن تبني API، يجب أن تفهم كيف تمثّل C# البيانات: value types مقابل reference types، ولماذا nullable ليس رفاهية، وكيف تحمي الكائنات بقواعد لا يستطيع أي endpoint كسرها.",
      keywords: ["C#", "value types", "reference types", "nullable", "required", "record", "class", "decimal", "encapsulation"],
      objectives: [
        "تفرّق بين value type وreference type وتعرف أين يعيش كل منهما.",
        "تستخدم nullable reference types و<code>required</code> لمنع القيم الفارغة غير المقصودة.",
        "تختار <code>class</code> أو <code>record</code> أو <code>struct</code> بناءً على الغرض.",
        "تستخدم <code>decimal</code> للمال وتشرح لماذا <code>double</code> خطأ هنا.",
        "تحمي حالة الكائن بقواعد أعمال داخل الكائن نفسه."
      ],
      concept: `
        <p>C# لغة <strong>statically typed</strong>: كل متغير له نوع معروف وقت الترجمة. النوع ليس «شكليًا»؛ هو عقد يحدد ما يمكن تخزينه، وما يمكن استدعاؤه، وكم بايت يُحجز، وهل القيمة تُنسخ أم تُشارَك. عندما تكتب <code>string name</code> فأنت تقول للمترجم: هذا المتغير إما يشير إلى نص، أو يكون <code>null</code> إذا سمحت بذلك. وعندما تكتب <code>decimal price</code> فأنت تطلب تمثيلًا عشريًا دقيقًا، لا تقريبًا ثنائيًا.</p>
        <p>أهم تقسيم في C# هو <strong>value type</strong> مقابل <strong>reference type</strong>. الأنواع البسيطة مثل <code>int</code> و<code>bool</code> و<code>decimal</code> و<code>Guid</code> و<code>DateTime</code> هي value types: المتغير يحمل القيمة نفسها. أما <code>class</code> و<code>interface</code> و<code>string</code> و<code>array</code> فهي reference types: المتغير يحمل <em>مرجعًا</em> إلى كائن على الـ managed heap. هذا يفسّر لماذا نسخ <code>int</code> ينسخ قيمته، بينما نسخ كائن <code>Product</code> ينسخ المرجع فقط، فيرى الاثنان نفس البيانات.</p>
        <h3>Nullability ليس تفصيلًا</h3>
        <p>في مشروع Backend، معظم الأخطاء تأتي من قيم غير متوقعة: اسم فارغ، معرّف مفقود، كائن لم يُحمّل من قاعدة البيانات. منذ C# 8 يمكنك تفعيل <strong>Nullable Reference Types</strong> في ملف المشروع. عندها <code>string</code> تعني «نص غير فارغ»، و<code>string?</code> تعني «قد يكون null». المترجم يحذّرك عند احتمال null، ويجبرك على التعامل معه قبل الاستخدام. هذه ليست حماية وقت التشغيل، لكنها تمنع أخطاء كثيرة قبل النشر.</p>
        <p>لإجبار من ينشئ الكائن على تمرير قيمة، استخدم <code>required</code>. ولو أردت أن تكون القيمة غير قابلة للتغيير بعد الإنشاء، استخدم <code>init</code> بدل <code>set</code>. هذا يجعل الكائن أقرب إلى <strong>immutable DTO</strong>، وهو ما نريده لبيانات الدخول والخروج في الـ API: لا يستطيع أي middleware أو endpoint لاحق تغيير الحقول بالخطأ.</p>
        <h3>لماذا decimal وليس double؟</h3>
        <p><code>double</code> يستخدم IEEE 754 binary floating point. لا يستطيع تمثيل <code>0.1</code> بدقة لأن المقام 10 لا يقبل القسمة على 2. النتيجة أخطاء تراكمية: <code>0.1 + 0.2</code> قد لا يساوي <code>0.3</code> تمامًا. في المال هذا غير مقبول. <code>decimal</code> يستخدم تمثيلًا عشريًا بقاعدة 10، وله دقة 28–29 رقمًا، ويُستخدم في الأسعار والضرائب والفوائد. مقابله: أبطأ قليلًا وأكبر حجمًا، لكن صحة الفاتورة أهم من nanoseconds.</p>
        <h3>class أم record أم struct؟</h3>
        <p>استخدم <strong>class</strong> لكيان له هوية ودورة حياة، مثل <code>Product</code> أو <code>Order</code>. استخدم <strong>record</strong> لبيانات تُقارن بقيمها، مثل DTO أو رسالة أو نتيجة استعلام. الـ record يمنحك مساواة قيمية و<code>with</code> وعرضًا مقروءًا، لكنه ليس بديلًا تلقائيًا عن كيانات EF Core لأن EF يحتاج أحيانًا خصائص قابلة للتغيير وتتبعًا. استخدم <strong>struct</strong> فقط لأنواع صغيرة جدًا (عادة 16 بايت أو أقل) وقصيرة العمر، وإلا وقعت في نسخ متكرر وأداء أسوأ.</p>
        <h3>الكائن مسؤول عن قواعده</h3>
        <p>لا تترك <code>Stock = -5</code> ممكنًا من أي مكان. إذا كان المخزون لا يصبح سالبًا، فالكائن نفسه يجب أن يرفض العملية. هذا هو <strong>Encapsulation</strong> العملي: ليس getters/setters، بل منع الحالات غير الصالحة. لاحقًا سترى أن هذا الأساس هو ما يجعل Domain Model أفضل من كائن بيانات مفتوح.</p>
      `,
      walkthrough: [
        {
          title: "تعريف كيان Product",
          code: `public sealed class Product
{`,
          body: `<p><code>public</code> يعني أن النوع متاح خارج الـ assembly. <code>sealed</code> يمنع الوراثة: لا نريد أن يغيّر أي نوع آخر سلوك المنتج. <code>class</code> يجعل <code>Product</code> reference type؛ المتغير سيحمل مرجعًا إلى كائن على الـ heap. القوس يبدأ تعريف الحالة والسلوك.</p>`
        },
        {
          title: "معرّف لا يتغيّر",
          code: `    public required Guid Id { get; init; }`,
          body: `<p><code>Guid</code> value type بحجم 16 بايت، مناسب للمعرّفات المولّدة دون الاعتماد على تسلسل قاعدة البيانات. <code>required</code> يجبر أي كائن جديد على تعيينه؛ لا يمكن إنشاء <code>Product</code> بدونه. <code>init</code> يسمح بالتعيين أثناء الإنشاء أو object initializer فقط، ثم يصبح للقراءة. وراء الكواليس، المترجم يولّد setter خاصًا يُستدعى في مرحلة التهيئة، وليس خاصية ثابتة فعلية.</p>`
        },
        {
          title: "اسم إلزامي",
          code: `    public required string Name { get; set; }`,
          body: `<p><code>string</code> reference type، ومع Nullable Reference Types مفعّلة فهي تعني «ليس null». <code>required</code> يمنع النسيان، لكنه لا يمنع تمرير <code>""</code> أو مسافات. لذلك نحتاج تحققًا من المحتوى في طبقة الطلب أو في الكائن نفسه. <code>set</code> يسمح بتعديل الاسم لاحقًا؛ إن أردت ثبات الاسم استخدم <code>init</code>. لا تجعل كل شيء <code>set</code> لمجرد الراحة.</p>`
        },
        {
          title: "سعر بدقة عشرية",
          code: `    public decimal Price { get; set; }`,
          body: `<p><code>decimal</code> value type بحجم 128 بت، يمثل الأعداد العشرية بدقة تصل إلى 28–29 رقمًا. مناسب للأسعار والضرائب. لا تستخدم <code>double</code> للمال؛ أخطاء التمثيل الثنائي تتراكم في الفواتير. لاحظ أن <code>decimal</code> لا يمنع السعر السالب؛ هذه قاعدة عمل يجب إضافتها في التحقق أو في الكائن.</p>`
        },
        {
          title: "المخزون كعدد صحيح",
          code: `    public int Stock { get; set; }`,
          body: `<p><code>int</code> value type بحجم 32 بت، القيمة الافتراضية له عند إنشاء الكائن هي <code>0</code>. لا يمكن أن يحمل كسورًا، وهذا مناسب لعدد القطع. لكنه يسمح بالسالب. إذا كان المخزون لا يصبح سالبًا، فلا تكتفِ بالتحقق في الـ endpoint؛ أي مسار آخر قد يعدّله. القاعدة يجب أن تكون قريبة من البيانات.</p>`
        },
        {
          title: "خاصية محسوبة بلا تخزين",
          code: `    public bool IsAvailable => Stock > 0;`,
          body: `<p>هذه <strong>expression-bodied property</strong>. لا يوجد حقل خلفها؛ تُحسب عند القراءة من قيمة <code>Stock</code>. لا تستهلك مساحة إضافية في الكائن، لكنها ليست مجانية تمامًا: كل قراءة تنفّذ المقارنة. الـ JIT قد يدخلها (inline) في المسارات الساخنة. لا تجعلها <code>{ get; set; }</code> وتخزّن قيمة مكررة يمكن أن تتعارض مع المخزون.</p>`
        },
        {
          title: "عملية تغيّر الحالة بأمان",
          code: `    public void DecreaseStock(int quantity)
    {
        if (quantity <= 0)
            throw new ArgumentOutOfRangeException(nameof(quantity));

        if (Stock < quantity)
            throw new InvalidOperationException("الكمية المطلوبة أكبر من المخزون.");

        Stock -= quantity;
    }`,
          body: `<p>الدالة تفرض <strong>invariant</strong>: الكمية الموجبة، وعدم النزول تحت الصفر. <code>nameof(quantity)</code> يُحسب وقت الترجمة ويضع اسم المعامل في الاستثناء، ما يساعد السجلات. <code>ArgumentOutOfRangeException</code> للمدخل غير الصالح، و<code>InvalidOperationException</code> لحالة العمل غير المسموحة. هذه الاستثناءات تُعالج لاحقًا في Middleware مركزي وتحوّل إلى Problem Details، لا تتركها تصل كـ stack trace.</p>`
        },
        {
          title: "إنشاء الكائن وفرض required",
          code: `var product = new Product
{
    Id = Guid.NewGuid(),
    Name = "قهوة عربية",
    Price = 39.50m,
    Stock = 12
};`,
          body: `<p><code>var</code> ليس «نوعًا ديناميكيًا»؛ المترجم يستنتج <code>Product</code> من الجهة اليمنى. الـ object initializer يعيّن الخصائص بعد إنشاء الكائن. لأن الخصائص <code>required</code>، لن يترجم الكود إذا نسيت واحدة. <code>m</code> في <code>39.50m</code> تجعل الرقم <code>decimal</code> وليس <code>double</code>. الكائن الجديد يُخصّص على الـ heap، والمتغير يحمل مرجعه.</p>`
        },
        {
          title: "قيمة قد تكون null",
          code: `Product? maybe = await repository.GetByIdAsync(id, cancellationToken);
if (maybe is null)
{
    return Results.NotFound();
}`,
          body: `<p><code>Product?</code> تعني أن النتيجة قد تكون null، وهو أمر طبيعي عند البحث عن معرّف غير موجود. المترجم يفرض فحصها قبل الوصول إلى <code>maybe.Name</code>. <code>is null</code> نمط مطابقة واضح، و<code>return</code> مبكر يقلل التعشيش. لاحظ أن <code>await</code> لا يعني أن الكود يعمل على خيط جديد؛ هو يحرر الخيط الحالي أثناء انتظار I/O ثم يكمل. سنفصّل ذلك في الدرس التالي.</p>`
        },
        {
          title: "فصل البيانات عن الـ API",
          code: `public sealed record ProductDto(
    Guid Id,
    string Name,
    decimal Price,
    bool IsAvailable);`,
          body: `<p><code>record</code> مناسب لبيانات القراءة: مساواة قيمية، وطباعة مقروءة، وثبات نسبي. لا نعيد كيان <code>Product</code> مباشرة إلى العميل لأنه يكشف الحقول الداخلية ويسمح بـ <strong>over-posting</strong>. الـ DTO يحدد العقد الخارجي بوضوح. <code>sealed</code> يمنع الوراثة، و<code>record</code> يولد constructor وخصائص <code>init</code> تلقائيًا. لا تستخدم record ككيان EF Core افتراضيًا؛ افهم احتياجات التتبع أولًا.</p>`
        }
      ],
      compare: {
        intro: `<p>النمط القديم يفتح كل شيء للجميع: خصائص قابلة للكتابة، سعر <code>double</code>، واسم قد يكون null دون أن يعرف أحد. النمط الحديث يجعل العقد صريحًا ويمنع الحالات غير الصالحة.</p>`,
        before: {
          label: "كائن مفتوح بلا قواعد",
          lang: "csharp",
          title: "Product.cs قبل",
          code: `public class Product
{
    public int Id { get; set; }
    public string Name { get; set; }
    public double Price { get; set; }
    public int Stock { get; set; }
}`,
          points: [
            "Name قد يكون null أو فارغًا دون تحذير.",
            "double يسبب أخطاء تقريب في المال.",
            "أي كود يستطيع وضع Stock سالب.",
            "لا توجد هوية ثابتة أو قواعد أعمال."
          ]
        },
        after: {
          label: "كيان يحمي حالته",
          lang: "csharp",
          title: "Product.cs بعد",
          code: `public sealed class Product
{
    public required Guid Id { get; init; }
    public required string Name { get; set; }
    public decimal Price { get; private set; }
    public int Stock { get; private set; }
    public bool IsAvailable => Stock > 0;

    public void ChangePrice(decimal newPrice)
    {
        if (newPrice <= 0)
            throw new ArgumentOutOfRangeException(nameof(newPrice));

        Price = newPrice;
    }

    public void DecreaseStock(int quantity)
    {
        if (quantity <= 0 || Stock < quantity)
            throw new InvalidOperationException("كمية غير صالحة.");

        Stock -= quantity;
    }
}`,
          points: [
            "required يمنع إنشاء كائن ناقص.",
            "decimal يحفظ دقة السعر.",
            "الخصائص المالية خاصة، والتغيير يمر عبر قواعد.",
            "الحالة غير الصالحة تُرفض في مكان واحد."
          ]
        },
        verdict: `<p>الفكرة ليست «اجعل كل شيء private»، بل اجعل كل تغيير يمر عبر عملية تعرف القواعد. هذا يقلل الأخطاء في الـ endpoints ويجعل الاختبارات أوضح: تختبر سلوك الكائن لا تفاصيل setters.</p>`
      },
      internals: `
        <p>عند إنشاء كائن reference type، يخصص CLR مساحة على الـ managed heap تحتوي على <strong>object header</strong> (مؤشر إلى Method Table ومعلومات تزامن/GC) ثم الحقول. المتغير المحلي لا يحتوي الكائن نفسه؛ يحتوي مرجعًا (pointer) إليه. لذلك نسخ المتغير لا ينسخ الكائن. أما <code>int</code> و<code>decimal</code> و<code>Guid</code> فتُخزَّن قيمتها مباشرة في المتغير أو داخل الكائن، وتُنسخ بالكامل عند الإسناد.</p>
        <p><code>decimal</code> ليس نوعًا بدائيًا في المعالج؛ هو struct مكوّن من 128 بت (أربع كلمات) مع flags للعلامة والعدد العشري. العمليات عليه أبطأ من <code>double</code> لأنها تُنفّذ برمجيًا/بمساعدة مكتبة، لكنها دقيقة. في مسار طلب عادي، الفرق لا يُلاحظ؛ في حلقات ملايين الحسابات قد يظهر. اختر الصحة أولًا، وقِس قبل التحسين.</p>
        <p>Nullable Reference Types ليست تغييرًا في تمثيل <code>string</code> وقت التشغيل؛ <code>string?</code> و<code>string</code> كلاهما مرجع. الفرق في <strong>metadata</strong> وتحليل المترجم. يمكنك التحقق وقت التشغيل عبر reflection، لكن لا تعتمد على ذلك كحماية أمنية. المدخلات القادمة من الشبكة تحتاج تحققًا فعليًا (validation) لأن أي عميل يمكنه إرسال JSON بأي شكل.</p>
        <p>كل كائن جديد يزيد ضغط الـ GC. إنشاء DTOs كثيرة لكل طلب أمر طبيعي، لكن إنشاء آلاف الكائنات الوسيطة في حلقة ساخنة قد يرفع Gen0 collections. لاحظ أيضًا أن <code>string</code> غير قابل للتغيير (immutable): كل عملية مثل <code>Substring</code> أو <code>Replace</code> تنشئ نصًا جديدًا. في معالجة النصوص الكثيفة، استخدم <code>StringBuilder</code> أو <code>Span&lt;char&gt;</code> بدل سلسلة عمليات.</p>
        <h3>required وinit وقت التشغيل</h3>
        <p><code>required</code> يفرضه المترجم عبر <code>RequiredMemberAttribute</code> و<code>SetsRequiredMembers</code>، ويظهر أيضًا في metadata. التحقق يحدث عند الترجمة وفي بعض سيناريوهات التسلسل، لكنه ليس حارسًا أمنيًا. إذا وصل JSON ناقصًا إلى model binder، فقد يحصل الكائن على قيم افتراضية. لهذا نستخدم DTO + Validation، لا نعتمد على required وحده.</p>
      `,
      internalsTable: {
        head: ["النوع", "الفئة", "التخزين", "ملاحظة"],
        rows: [
          ["int", "value type", "4 بايت داخل المتغير/الكائن", "القيمة الافتراضية 0"],
          ["decimal", "value type", "128 بت", "دقة عشرية للمال"],
          ["Guid", "value type", "16 بايت", "مناسب للمعرّفات المولّدة"],
          ["string", "reference type", "مرجع إلى heap", "غير قابل للتغيير"],
          ["Product", "reference type", "مرجع إلى heap", "له هوية ودورة حياة"],
          ["record DTO", "reference type", "مرجع إلى heap", "مساواة قيمية"]
        ]
      },
      tips: [
        {
          title: "فعّل Nullable في المشروع كله",
          body: "تأكد من <code>&lt;Nullable&gt;enable&lt;/Nullable&gt;</code> و<code>&lt;TreatWarningsAsErrors&gt;</code> في CI على الأقل. التحذيرات التي تتجاهلها اليوم تصبح NullReferenceException في الإنتاج غدًا."
        },
        {
          title: "لا تستخدم record لكل شيء",
          body: "record ممتاز لـ DTOs ورسائل الأحداث ونتائج الاستعلام. لكن كيانات EF Core تحتاج غالبًا خصائص قابلة للتتبع وconstructors معينة. استخدم record للعقود، وclass للكيانات ذات السلوك."
        },
        {
          title: "المال دائمًا decimal",
          body: "استخدم <code>decimal</code> للأسعار والضرائب والخصومات. حدد أيضًا العملة (USD/EGP) وعدد المنازل العشرية في العقد. لا تترك التقريب لقاعدة البيانات وحدها."
        },
        {
          title: "لا تفتح setters للجميع",
          body: "كل <code>public set</code> هو باب لتغيير حالة دون قواعد. اجعلها <code>private set</code> أو <code>init</code>، ووفّر methods مثل <code>ChangePrice</code> و<code>DecreaseStock</code> تفحص القواعد."
        }
      ],
      quiz: [
        {
          q: "أي جملة تصف الفرق بين value type وreference type بشكل صحيح؟",
          options: [
            "value type يُخزَّن دائمًا على الـ heap، وreference type على الـ stack.",
            "value type يحمل القيمة نفسها، وreference type يحمل مرجعًا إلى كائن.",
            "reference type لا يمكن أن يكون null.",
            "value type أبطأ دائمًا من reference type."
          ],
          answer: 1,
          explain: "value type مثل int وdecimal يحمل القيمة مباشرة، بينما class وstring يحملان مرجعًا إلى كائن على الـ managed heap. مكان التخزين يعتمد على السياق، وليس قاعدة مطلقة."
        },
        {
          q: "لماذا نستخدم decimal بدل double للأسعار؟",
          options: [
            "لأن decimal أسرع في كل العمليات.",
            "لأن double لا يمكن تخزين أرقام سالبة.",
            "لأن decimal يمثل الكسور العشرية بدقة مناسبة للمال، بينما double ثنائي وقد يراكم أخطاء تقريب.",
            "لأن decimal نوع مرجعي يمكن مشاركته بين الطلبات."
          ],
          answer: 2,
          explain: "double يستخدم تمثيلًا ثنائيًا لا يمثل 0.1 بدقة، ما يسبب أخطاء في المبالغ. decimal تمثيل عشري بدقة 28–29 رقمًا، وهو الخيار الصحيح للمال."
        },
        {
          q: "ما وظيفة required في الخصائص؟",
          options: [
            "يمنع تغيير القيمة بعد الإنشاء.",
            "يجبر من ينشئ الكائن على تعيين الخاصية، وإلا فشل الترجمة.",
            "يجعل الخاصية متاحة عبر HTTP تلقائيًا.",
            "يحوّل النوع إلى value type."
          ],
          answer: 1,
          explain: "required يفرض تعيين الخاصية عند الإنشاء عبر object initializer أو constructor موسوم. أما منع التغيير بعد الإنشاء فهو وظيفة init أو private set. required ليس تحققًا أمنيًا من مدخلات الشبكة."
        }
      ],
      capstone: {
        title: "نمذجة كيانات Souq",
        goal: "أضف كيانات المنتج والتصنيف إلى مشروع Souq.NET بقواعد واضحة، واستخدم DTO لعقد القراءة بدل كشف الكيان.",
        tasks: [
          "أنشئ مجلد <code>Domain/Entities</code> وأضف <code>Product</code> و<code>Category</code>.",
          "اجعل <code>Product.Price</code> من نوع <code>decimal</code>، وأضف قاعدة تمنع السعر غير الموجب.",
          "أضف method باسم <code>DecreaseStock</code> ترفض الكمية السالبة والتي تتجاوز المخزون.",
          "أنشئ <code>ProductDto</code> كـ record يحتوي Id وName وPrice وIsAvailable فقط.",
          "أضف اختبارًا بسيطًا يثبت أن <code>DecreaseStock</code> يرمي استثناءً عند تجاوز المخزون."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه النمذجة",
          code: `public sealed class Product
{
    public required Guid Id { get; init; }
    public required string Name { get; set; }
    public decimal Price { get; private set; }
    public int Stock { get; private set; }
    public bool IsAvailable => Stock > 0;
}`,
        },
      },
    },
    {
      id: "csharp-backend-2",
      title: "C# للـBackend: Collections، LINQ، وasync/await",
      duration: 28,
      level: "مبتدئ",
      summary:
        "الـ Backend كله انتظار: انتظار قاعدة البيانات، الشبكة، والملفات. ستتعلم كيف تكتب استعلامات LINQ تُترجم إلى SQL، ولماذا async ليس مجرد await، وكيف تمنع حرق خيوط الخادم.",
      keywords: ["C#", "LINQ", "IQueryable", "async", "await", "Task", "CancellationToken", "thread pool", "EF Core"],
      objectives: [
        "تختار Collection مناسبًا وتشرح تكلفة البحث والإضافة.",
        "تفرّق بين <code>IEnumerable</code> و<code>IQueryable</code> وتأجيل التنفيذ.",
        "تكتب method غير متزامنة بشكل صحيح مع <code>CancellationToken</code>.",
        "تشرح ماذا يحدث للخيط أثناء <code>await</code> ولماذا <code>.Result</code> خطر.",
        "تعالج الاستثناءات عند حدود التطبيق دون إخفاء الأخطاء."
      ],
      concept: `
        <p>في لعبة صغيرة، يكفي <code>List&lt;T&gt;</code> لكل شيء. في API حقيقي، اختيار الـ collection والاستعلام يحدد استهلاك الذاكرة وزمن الاستجابة. <code>List&lt;T&gt;</code> مناسب للبيانات في الذاكرة، <code>Dictionary&lt;TKey,TValue&gt;</code> للبحث السريع بالمفتاح، <code>HashSet&lt;T&gt;</code> للتحقق من التكرار، و<code>IReadOnlyList&lt;T&gt;</code> لواجهة قراءة فقط. لا تفضّل نوعًا لأنك اعتدت عليه؛ اختر حسب العملية الغالبة.</p>
        <p>ثم يأتي <strong>LINQ</strong>. عندما تكتب <code>_db.Products.Where(...)</code> فأنت لا تنفّذ شيئًا بعد. تبني <strong>expression tree</strong> يصف الاستعلام. EF Core يقرأ الشجرة ويترجمها إلى SQL. هذا هو الفرق بين <code>IQueryable&lt;T&gt;</code> (وصف استعلام قابل للترجمة) و<code>IEnumerable&lt;T&gt;</code> (بيانات تُعدّد في الذاكرة). إذا استدعيت <code>ToList()</code> مبكرًا، فأنت تسحب كل الصفوف ثم تفلتر في الذاكرة؛ كارثة على جدول كبير.</p>
        <p><strong>async/await</strong> ليسا خيوطًا جديدة. عند <code>await</code> لعملية I/O، يحرر الـ runtime الخيط الحالي ليعمل على طلب آخر، ثم يكمل التنفيذ عندما تكتمل العملية. هذا يسمح لخادم بعدد خيوط محدود بخدمة آلاف الطلبات المنتظرة. إذا استخدمت <code>.Result</code> أو <code>.Wait()</code>، فأنت تحجز خيطًا كاملًا في انتظار I/O، وقد تصل إلى <strong>thread pool starvation</strong>.</p>
        <h3>لماذا CancellationToken؟</h3>
        <p>المستخدم قد يغلق المتصفح، أو يرفع الطلب مهلة، أو يتوقف الـ orchestrator. <code>CancellationToken</code> يمرر هذه الرغبة إلى قاعدة البيانات والشبكة، فيتوقف العمل بدلًا من إكماله بلا فائدة. مرّره في كل طبقة، ولا تبتلعه. <code>OperationCanceledException</code> ليس خطأ خادمًا؛ لا تحوّله إلى 500.</p>
        <h3>الاستثناءات عند الحدود</h3>
        <p>لا تلتقط <code>Exception</code> في كل method. اتركها تنتقل إلى Middleware مركزي يعرف كيف يسجلها ويحوّلها إلى Problem Details. التقط فقط ما تعرف كيف تعالجه: خطأ متوقع، إعادة محاولة، أو تحويل إلى نتيجة عمل. الابتلاع الصامت (<code>catch { }</code>) يجعل التشخيص مستحيلًا.</p>
        <h3>IDisposable وawait using</h3>
        <p>الموارد غير المُدارة مثل اتصالات الشبكة والملفات تحتاج تحريرًا. <code>using</code> يضمن <code>Dispose</code> حتى عند الاستثناء. مع الأنواع التي تنفّذ <code>IAsyncDisposable</code> استخدم <code>await using</code>. لا تترك <code>DbContext</code> أو <code>HttpResponseMessage</code> بلا تحرير.</p>
      `,
      walkthrough: [
        {
          title: "توقيع method غير متزامنة",
          code: `public async Task<IReadOnlyList<ProductDto>> GetProductsAsync(
    CancellationToken cancellationToken)`,
          body: `<p><code>async</code> يسمح باستخدام <code>await</code> ويحوّل جسم الدالة إلى <strong>state machine</strong>. <code>Task&lt;IReadOnlyList&lt;ProductDto&gt;&gt;</code> هو وعد بنتيجة لاحقًا، وليس النتيجة نفسها. <code>IReadOnlyList</code> يمنع المستدعي من تعديل القائمة، لكنه لا يمنع تعديل العناصر إن كانت مرجعية. <code>CancellationToken</code> معامل اختياري من الناحية اللغوية، لكنه إلزامي عمليًا في أي I/O.</p>`
        },
        {
          title: "الوصول إلى DbSet",
          code: `var products = await _db.Products`,
          body: `<p><code>_db.Products</code> خاصية <code>DbSet&lt;Product&gt;</code> وتنفّذ <code>IQueryable&lt;Product&gt;</code>. لا يوجد SQL بعد. الـ DbContext يملك <strong>Change Tracker</strong> واتصالًا منطقيًا، لكنه لا يفتح اتصالًا فعليًا حتى ينفّذ الاستعلام. هذا الوصول رخيص جدًا مقارنة بتحميل البيانات.</p>`
        },
        {
          title: "إيقاف التتبع للقراءة",
          code: `    .AsNoTracking()`,
          body: `<p>يخبر EF Core ألا يحتفظ بنسخة مراقبة من كل صف. مناسب لاستعلامات القراءة التي لن تُعدّل الكيان. الفائدة: ذاكرة أقل، وسرعة أعلى، وتجنب Identity Map عندما لا تحتاجه. لا تستخدمه إذا ستعدّل الكيانات في نفس الـ context ثم تحفظ؛ التغييرات لن تُكتشف تلقائيًا.</p>`
        },
        {
          title: "فلترة تُترجم إلى SQL",
          code: `    .Where(p => p.IsActive)`,
          body: `<p>هذا lambda لا يُنفّذ في C#. هو يتحول إلى تعبير (Expression) يقرأه موفر EF Core ويترجمه إلى <code>WHERE IsActive = 1</code>. الشرط يجب أن يكون قابلًا للترجمة. إذا استخدمت method عادية لا يعرفها الموفر، فقد يحدث استثناء أو تحميل جزئي في الذاكرة. افحص الـ SQL في التطوير.</p>`
        },
        {
          title: "ترتيب النتائج",
          code: `    .OrderBy(p => p.Name)`,
          body: `<p><code>OrderBy</code> يضيف <code>ORDER BY Name</code> إلى الاستعلام. الترتيب على عمود بلا index قد يكون مكلفًا على ملايين الصفوف. إذا كان الترتيب متكررًا، أضف index مناسبًا. لا تفترض أن ترتيب قاعدة البيانات ثابت بدون <code>ORDER BY</code>؛ SQL لا يضمنه.</p>`
        },
        {
          title: "إسقاط الأعمدة المطلوبة فقط",
          code: `    .Select(p => new ProductDto(p.Id, p.Name, p.Price))`,
          body: `<p>الـ projection يحدد الأعمدة التي ستُقرأ. بدل تحميل كل أعمدة المنتج، يترجم EF Core إلى <code>SELECT Id, Name, Price</code>. هذا يقلل I/O والشبكة والذاكرة. كما يمنع إرجاع حقول حساسة بالخطأ. الـ DTO هنا record، فيُنشأ كائن جديد لكل صف؛ تخصيص صغير لكنه ضروري للعقد.</p>`
        },
        {
          title: "تنفيذ الاستعلام بشكل غير متزامن",
          code: `    .ToListAsync(cancellationToken);`,
          body: `<p>هنا فقط يتحول الوصف إلى SQL ويُنفّذ. <code>ToListAsync</code> يفتح الاتصال، يرسل الأمر، يقرأ الصفوف، ويبني القائمة. <code>await</code> يحرر الخيط أثناء الانتظار. <code>CancellationToken</code> يُمرَّر إلى موفر قاعدة البيانات، فيمكن إلغاء الأمر. لا تستخدم <code>ToList()</code> المتزامن داخل طلب ASP.NET Core إلا لسبب واضح.</p>`
        },
        {
          title: "إعادة النتيجة",
          code: `return products;`,
          body: `<p>الـ state machine يضع القائمة في <code>Task</code> المكتمل ويعيدها للمستدعي. لا يوجد خيط جديد أُنشئ لهذه الدالة. إذا حدث استثناء قبل الإرجاع، يُوضع في الـ Task ويُعاد رفعه عند <code>await</code> في المستدعي. لا تعِد <code>IQueryable</code> من repository؛ سيُنفّذ لاحقًا في سياق قد يكون أُغلق، وقد تفلت الاستعلامات من الطبقة التي تملك قاعدة البيانات.</p>`
        },
        {
          title: "معالجة الإلغاء عند الحد",
          code: `catch (OperationCanceledException)
    when (cancellationToken.IsCancellationRequested)
{
    throw;
}`,
          body: `<p>إذا أُلغي الطلب، لا تحوّله إلى خطأ 500. أعد رفعه ليقرر الإطار أو الـ middleware الاستجابة المناسبة (غالبًا 499 أو لا استجابة). <code>when</code> يقيّد الـ catch بحالة الإلغاء الفعلية، حتى لا تبتلع timeout غير متعلق بالطلب. لا تكتب <code>catch (Exception) { }</code>؛ هذا يخفي أخطاء حقيقية.</p>`
        },
        {
          title: "استخدام النتيجة في endpoint",
          code: `var items = await service.GetProductsAsync(httpContext.RequestAborted);
return Results.Ok(items);`,
          body: `<p><code>HttpContext.RequestAborted</code> يُلغى عندما يقطع العميل الاتصال. تمريره إلى الخدمة يوقف الاستعلام بدل إكماله بلا مستهلك. <code>Results.Ok</code> ينتج 200 مع JSON. لاحظ أن الاستجابة تُسلسل لاحقًا؛ إذا كانت القائمة كبيرة جدًا، فكّر في الترقيم (pagination) بدل إرجاع كل الصفوف.</p>`
        }
      ],
      compare: {
        intro: `<p>المقارنة هنا ليست بين «قديم» و«جديد» فقط، بل بين نمط يحجز خيوطًا ويجلب بيانات زائدة، ونمط يستخدم I/O غير متزامن وإسقاطًا دقيقًا.</p>`,
        before: {
          label: "متزامن ويسحب كل شيء",
          lang: "csharp",
          title: "ProductsController.cs قبل",
          code: `public List<Product> Get()
{
    var all = _db.Products.ToList();
    return all.Where(p => p.IsActive)
              .OrderBy(p => p.Name)
              .ToList();
}`,
          points: [
            "ToList الأول يجلب كل الصفوف إلى الذاكرة.",
            "الفلترة والترتيب يحدثان بعد تحميل البيانات.",
            "العملية المتزامنة تحجز خيطًا أثناء I/O.",
            "يعيد الكيان كاملًا بدل DTO."
          ]
        },
        after: {
          label: "غير متزامن وإسقاط دقيق",
          lang: "csharp",
          title: "ProductsService.cs بعد",
          code: `public async Task<IReadOnlyList<ProductDto>> GetAsync(
    CancellationToken cancellationToken)
{
    return await _db.Products
        .AsNoTracking()
        .Where(p => p.IsActive)
        .OrderBy(p => p.Name)
        .Select(p => new ProductDto(p.Id, p.Name, p.Price))
        .ToListAsync(cancellationToken);
}`,
          points: [
            "الفلترة والترتيب والإسقاط تُترجم إلى SQL.",
            "AsNoTracking يقلل الذاكرة والتتبع.",
            "await يحرر الخيط أثناء الانتظار.",
            "CancellationToken يوقف العمل عند إلغاء الطلب."
          ]
        },
        verdict: `<p>النسخة الثانية لا تجلب عمودًا لا تحتاجه، ولا تحجز خيطًا أثناء انتظار قاعدة البيانات، وتسمح بالإلغاء. هذه هي القاعدة الافتراضية لأي قراءة في API إنتاجي.</p>`
      },
      internals: `
        <p>عند تنفيذ <code>await</code> على عملية I/O غير مكتملة، يُنشئ المترجم <strong>state machine</strong> يحفظ المتغيرات المحلية وموضع التنفيذ. إذا كانت العملية لم تكتمل، يعيد state machine الـ Task إلى المستدعي ويحرر الخيط. عند اكتمال I/O، يستأنف الـ continuation. لذلك async ليس «مجانيًا»: هناك تخصيص للـ state machine وTask، لكن التكلفة صغيرة مقابل حجز خيط أثناء انتظار بطيء.</p>
        <p>في ASP.NET Core لا تحتاج عادةً إلى <code>ConfigureAwait(false)</code>، لأن الإطار لا يستخدم <code>SynchronizationContext</code> مخصصًا. في مكتبات عامة أو واجهات سطح مكتب، قد يكون مهمًا لتجنب العودة إلى خيط الواجهة. لا تنسخه بلا فهم.</p>
        <p><code>Task</code> reference type، و<code>ValueTask</code> struct يمكن أن يقلل التخصيص في المسارات الساخنة جدًا عندما تكون النتيجة متاحة غالبًا بشكل متزامن. لا تستبدل كل Task بـ ValueTask؛ قواعد استخدامه دقيقة (لا تنتظر أكثر من مرة، ولا تخزنه). قِس أولًا.</p>
        <p><strong>Thread pool starvation</strong> يحدث عندما تحجز كل خيوط الـ pool في انتظار متزامن. مع حجم طلبات كبير، يتأخر الخادم حتى للطلبات التي لا تحتاج قاعدة بيانات. الحل: async من الأعلى إلى الأسفل، وعدم استخدام <code>.Result</code> أو <code>.Wait()</code> داخل مسار الطلب.</p>
        <h3>LINQ deferred execution</h3>
        <p>استعلام LINQ لا يُنفّذ عند بنائه. كل <code>Where</code> و<code>Select</code> يضيف عقدة إلى التعبير. التنفيذ يبدأ عند <code>foreach</code> أو <code>ToList</code> أو <code>Count</code>. هذا مفيد للتركيب، لكنه خطر إذا أعدت <code>IEnumerable</code> من method ثم عدّدته أكثر من مرة: قد يُنفّذ الاستعلام مرتين. استخدم <code>ToList</code> عند الحدود، أو ارجع <code>IReadOnlyList</code>.</p>
        <p>EF Core يترجم التعبير إلى SQL عبر موفر قاعدة البيانات. ليست كل دوال C# قابلة للترجمة. إذا وجدت نفسك تستخدم <code>AsEnumerable</code> قبل <code>Where</code>، فأنت تسحب البيانات إلى الذاكرة وتفلتر هناك. راجع الـ SQL الناتج باستخدام <code>ToQueryString()</code> أو logging.</p>
      `,
      tips: [
        {
          title: "async في كل الطبقات",
          body: "لا تخلط method متزامنة تستدعي <code>Task.Result</code>. اجعل السلسلة كلها async: endpoint، service، repository، وEF Core. أي حلقة متزامنة تلوّث الفائدة."
        },
        {
          title: "مرّر CancellationToken",
          body: "أضف <code>CancellationToken</code> إلى كل method I/O، ومرّره إلى EF Core وHttpClient. لا تبتلع <code>OperationCanceledException</code>؛ أعد رفعه بعد التنظيف."
        },
        {
          title: "لا تعِد IQueryable من الطبقات",
          body: "إعادة <code>IQueryable</code> تسمح للمستدعي بإضافة شروط وتنفيذ استعلامات لا تعرفها الطبقة. أعد DTOs أو قوائم محددة. هذا يسهل الاختبار ويحمي الأداء."
        },
        {
          title: "افحص SQL قبل التحسين",
          body: "استخدم <code>ToQueryString()</code> أو logging EF Core لترى SQL الفعلي. لا تفترض أن LINQ سيُترجم كما تتخيل. أضف indexes بناءً على الاستعلامات الحقيقية."
        }
      ],
      quiz: [
        {
          q: "ما الفرق الأساسي بين IEnumerable وIQueryable؟",
          options: [
            "IEnumerable أسرع دائمًا.",
            "IQueryable يصف استعلامًا يمكن ترجمته إلى SQL، وIEnumerable يعمل على بيانات في الذاكرة.",
            "IQueryable لا يدعم Where.",
            "لا فرق؛ كلاهما واجهة واحدة."
          ],
          answer: 1,
          explain: "IQueryable يحمل expression tree يمكن لموفر EF Core ترجمته إلى SQL. IEnumerable يعمل على بيانات موجودة في الذاكرة بعد التعداد. استدعاء ToList مبكرًا يحوّل الثانية إلى الأولى."
        },
        {
          q: "ماذا يحدث للخيط عند await لعملية I/O؟",
          options: [
            "يُقتل الخيط.",
            "يبقى محجوزًا حتى تكتمل العملية.",
            "يُحرَّر لخدمة عمل آخر، ثم يُستأنف التنفيذ عند اكتمال العملية.",
            "يُنشأ خيط جديد لكل await."
          ],
          answer: 2,
          explain: "await لا يحجز الخيط أثناء انتظار I/O. الـ runtime يحرره ليعمل على طلب آخر، ثم يستأنف الـ continuation. هذا هو أساس قابلية التوسع في ASP.NET Core."
        },
        {
          q: "أي نمط يسبب thread pool starvation؟",
          options: [
            "استخدام await مع CancellationToken.",
            "استخدام ToListAsync.",
            "استخدام Task.Result أو Task.Wait داخل مسار الطلب.",
            "استخدام AsNoTracking."
          ],
          answer: 2,
          explain: "Task.Result وWait يحجزان الخيط أثناء انتظار العملية. تحت الحمل، تنفد خيوط الـ pool وتتأخر الطلبات. استخدم await بدلًا منهما."
        }
      ],
      capstone: {
        title: "أول استعلام غير متزامن في Souq",
        goal: "أضف خدمة قراءة المنتجات التي تستخدم EF Core وDTO وCancellationToken، واختبر أنها لا تعيد كيانات خام.",
        tasks: [
          "أنشئ <code>IProductReadService</code> و<code>ProductReadService</code> في طبقة Application.",
          "نفّذ method <code>GetActiveAsync(CancellationToken)</code> تستخدم <code>AsNoTracking</code> و<code>Select</code> إلى <code>ProductDto</code>.",
          "أضف endpoint <code>GET /api/products</code> يمرّر <code>HttpContext.RequestAborted</code>.",
          "أضف ترقيم صفحات بسيطًا باستخدام <code>Skip</code> و<code>Take</code> مع حد أقصى للصفحة.",
          "اختبر الاستعلام بـ <code>ToQueryString()</code> وتأكد من وجود <code>WHERE</code> و<code>ORDER BY</code> و<code>LIMIT</code>."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه الخدمة",
          code: `return await _db.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .OrderBy(p => p.Name)
    .Select(p => new ProductDto(p.Id, p.Name, p.Price))
    .ToListAsync(cancellationToken);`,
        },
      },
    },

  ],
});
