/* الوحدة 2 — تشريح أول Web API: الملفات، Program.cs، وKestrel. */
Academy.addModule({
  id: "anatomy",
  title: "تشريح أول Web API",
  tagline: "من القالب إلى فهم كل ملف: أين يُقرأ الإعداد، كيف يبدأ المضيف، ومن يستقبل HTTP فعلًا.",
  icon: "⌘",
  color: "#22d3ee",
  lessons: [
    {
      id: "http-fundamentals",
      title: "HTTP للـBackend: الطلب، الاستجابة، والعقد",
      duration: 20,
      level: "مبتدئ",
      summary:
        "قبل أن تكتب أول endpoint، افهم العقد الذي يتكلم به كل عميل: method، مسار، ترويسات، جسم، وحالة. هذه المفردات هي ما يحدد إن كان الـ API مفهومًا وآمنًا أم مجرد دوال تُستدعى عن بُعد.",
      keywords: ["HTTP", "REST", "status codes", "headers", "idempotency", "content negotiation", "Kestrel", "API design"],
      objectives: [
        "تقرأ طلب HTTP خامًا وتحدد أجزاءه.",
        "تختار method وstatus code sesuai لنية العملية.",
        "تفرّق بين safe وidempotent وتشرح أثرها على إعادة المحاولة.",
        "تصمم مسارات REST بأسماء موارد لا أفعال.",
        "تستخدم الترويسات للتفاوض على المحتوى والتخزين المؤقت والأمان."
      ],
      concept: `
        <p>HTTP ليس «نقل JSON». هو <strong>بروتوكول طلب/استجابة</strong> نصي في HTTP/1.1 وثنائي في HTTP/2 وHTTP/3. العميل يرسل طلبًا يحتوي على method وtarget وإصدار وترويسات وجسم اختياري، والخادم يرد بحالة وترويسات وجسم. كل ما تفعله في ASP.NET Core — routing، binding، middleware — هو تفسير لهذا العقد ثم إنتاج رد صحيح.</p>
        <h3>تشريح الطلب</h3>\n        <p>السطر الأول هو <code>METHOD /path?query HTTP/1.1</code>. ثم ترويسات مثل <code>Host</code> و<code>Accept</code> و<code>Authorization</code>. بعد سطر فارغ يأتي الجسم إن وُجد. الطلب <code>GET</code> لا يحمل عادةً جسمًا؛ بياناته في المسار والاستعلام. الطلب <code>POST</code> يحمل جسمًا غالبًا، ويجب أن يحدد <code>Content-Type</code> صيغته. الخادم لا يخمّن: إن أرسلت JSON بلا <code>application/json</code> فقد يرفضه الـ binder أو يتعامل معه كخطأ.</p>\n        <h3>الـ Methods ليست زينة</h3>\n        <p><code>GET</code> للقراءة، <code>POST</code> للإنشاء أو عملية غير idempotent، <code>PUT</code> لاستبدال مورد كامل، <code>PATCH</code> لتعديل جزئي، <code>DELETE</code> للحذف. لكن الأهم من الاسم هو الدلالة: <strong>Safe</strong> يعني أن العملية لا تغيّر حالة الخادم (GET، HEAD). <strong>Idempotent</strong> يعني أن تكرارها بنفس المدخلات يعطي نفس الحالة النهائية، حتى لو اختلفت الاستجابة (PUT، DELETE). هذا مهم لأن الشبكات تعيد المحاولة، والوسطاء قد يعيدون الطلب دون علمك.</p>\n        <h3>الحالات تحكي القصة</h3>\n        <p>العائلة <code>2xx</code> نجاح، <code>3xx</code> إعادة توجيه أو cached، <code>4xx</code> خطأ من العميل، <code>5xx</code> خطأ من الخادم. لا تُرجع <code>200</code> مع <code>{ \"success\": false }</code> لكل شيء؛ هذا يخفي الحقيقة عن الـ cache والمراقبة والعميل. <code>201 Created</code> مع <code>Location</code> عند إنشاء مورد، <code>204 No Content</code> عند نجاح بلا جسم، <code>400</code> لطلب مشوّه، <code>401</code> لهوية مفقودة/غير صالحة، <code>403</code> لهوية صالحة بلا صلاحية، <code>404</code> لمورد غير موجود، <code>409</code> لتعارض حالة، و<code>422</code> لمدخلات صحيحة الشكل لكنها مخالفة لقواعد العمل إن اخترت هذا الاصطلاح.</p>\n        <h3>REST: موارد لا أفعال</h3>\n        <p>في REST، المسار يسمّي <strong>المورد</strong> وليس العملية. <code>/api/products</code> مورد، و<code>/api/products/5</code> مورد فرعي. الفعل يأتي من method، والفلترة من query. لا تصمم <code>/getProducts</code> و<code>/createProduct</code>؛ هذا أسلوب RPC وليس خطأً دينيًا، لكنه يجعل الـ API غير متوقع ويصعب توحيده. الاستثناءات الوظيفية مثل <code>/orders/5/cancel</code> مقبولة عندما لا توجد طريقة REST طبيعية للتعبير عن الانتقال.</p>\n        <h3>بلا حالة</h3>\n        <p>HTTP بطبيعته <strong>stateless</strong>: كل طلب يجب أن يحمل ما يحتاجه من هوية وسياق. الخادم لا يحتفظ بجلسة في الذاكرة بين الطلبات؛ وإلا لما استطعت تشغيل عدة نسخ خلف load balancer. لذلك JWT أو API key أو cookie موقّع يُرسل مع كل طلب. الحالة الحقيقية تعيش في قاعدة بيانات أو cache مشترك، لا في حقل static داخل process.</p>\n        <h3>التفاوض والتخزين المؤقت</h3>\n        <p><code>Accept</code> يقول ما الصيغة التي يقبلها العميل، و<code>Content-Type</code> يقول ما الصيغة المرسلة. <code>Cache-Control</code> و<code>ETag</code> و<code>If-None-Match</code> تسمح بإرجاع <code>304 Not Modified</code> بدل إعادة الجسم. لا تضع <code>Cache-Control: public</code> على بيانات مستخدم؛ قد تُخزَّن في وسيط مشترك. الأمان والـ caching يسيران معًا، لا بعد التفكير.</p>\n      `,
      walkthrough: [
        {
          title: "سطر الطلب",
          code: `GET /api/products?page=2&pageSize=20 HTTP/1.1`,
          lang: "http",
          body: `<p><code>GET</code> يطلب قراءة. <code>/api/products</code> هو target، والاستعلام <code>page=2&amp;pageSize=20</code> يفلتر/يرقّم. <code>HTTP/1.1</code> يحدد إصدار البروتوكول. لا يوجد جسم في هذا الطلب؛ أي بيانات إضافية يجب أن تكون في المسار أو الترويسات أو الاستعلام، مع مراعاة أن الاستعلام يظهر في السجلات.</p>`
        },
        {
          title: "ترويسة Host",
          code: `Host: api.souq.example`,
          lang: "http",
          body: `<p><code>Host</code> إلزامية في HTTP/1.1 وتحدد المورد الافتراضي على الخادم. خلف reverse proxy، قد تحتاج <code>Forwarded</code> أو <code>X-Forwarded-Host</code> لمعرفة الأصل الحقيقي، لكن لا تثق بها من الإنترنت دون إعداد صحيح. ASP.NET Core يستخدم هذه المعلومات في إنشاء الروابط المطلقة والتحقق من allowed hosts.</p>`
        },
        {
          title: "تفاوض المحتوى",
          code: `Accept: application/json`,
          lang: "http",
          body: `<p>العميل يقول إنه يقبل JSON. إذا لم يستطع الخادم إنتاج صيغة مقبولة، فالصحيح <code>406 Not Acceptable</code> وليس إرسال XML رغمًا عنه. في ASP.NET Core، إعداد formatters يحدد ما يمكن إنتاجه. لا تخلط <code>Accept</code> (ما أريده في الرد) مع <code>Content-Type</code> (ما أرسلته في الطلب).</p>`
        },
        {
          title: "الهوية في ترويسة",
          code: `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`,
          lang: "http",
          body: `<p>بيانات الاعتماد تُرسل في ترويسة <code>Authorization</code>، وليس في query string. الروابط تُسجَّل في المتصفحات والوسطاء وتاريخ الزيارات. <code>Bearer</code> يعني أن من يحمل التوكن يستطيع استخدامه، لذلك يجب أن يكون الاتصال TLS وأن تكون صلاحية التوكن قصيرة. الخادم يتحقق من التوقيع والصلاحية والصلاحيات قبل تنفيذ العملية.</p>`
        },
        {
          title: "جسم POST",
          code: `POST /api/products HTTP/1.1\nHost: api.souq.example\nContent-Type: application/json\nContent-Length: 74\n\n{\"name\":\"قهوة عربية\",\"price\":39.5}`,
          lang: "http",
          body: `<p><code>Content-Type</code> يحدد صيغة الجسم، و<code>Content-Length</code> طوله بالبايتات. بعد السطر الفارغ يبدأ الجسم. الخادم يقرأه ضمن حد أقصى، ثم يفكّه ويربطه بكائن. <code>POST</code> ليس idempotent: إعادة إرسال نفس الطلب قد تنشئ منتجين. لذلك تحتاج مفتاح idempotency عند العمليات المالية أو الحساسة.</p>`
        },
        {
          title: "استجابة الإنشاء",
          code: `HTTP/1.1 201 Created\nLocation: /api/products/8f14e45f-ceea-4b7a-9f7e-2d9a3f6c1b22`,
          lang: "http",
          body: `<p><code>201</code> تعني أن موردًا جديدًا أُنشئ. <code>Location</code> يعطي العميل عنوانه، فيستطيع قراءته دون تخمين. بعض الفرق ترجع المورد كاملًا في الجسم، وبعضها لا. الأهم أن الحالة والترويسة تعبّران عن الحقيقة. لا ترجع <code>200</code> لمجرد أن الكود لم يرمِ استثناءً.</p>`
        },
        {
          title: "ترويسات الرد والتخزين",
          code: `Content-Type: application/json; charset=utf-8\nCache-Control: no-store\nETag: "a91f2c"`,
          lang: "http",
          body: `<p><code>Content-Type</code> يخبر العميل كيف يفك الجسم. <code>Cache-Control: no-store</code> يمنع تخزين بيانات حساسة. <code>ETag</code> بصمة نسخة من المورد؛ يستخدمها العميل في <code>If-None-Match</code>، فيرد الخادم <code>304</code> إن لم تتغير. لا تضع ETag ثم تنسى التحقق منه؛ ستحصل على cache لا يعرف التحديثات.</p>`
        },
        {
          title: "أخطاء ذات معنى",
          code: `HTTP/1.1 404 Not Found\nContent-Type: application/problem+json\n\n{\"type\":\"https://tools.ietf.org/html/rfc9110\",\"title\":\"Not Found\",\"status\":404}`,
          lang: "http",
          body: `<p><code>404</code> تعني أن المورد غير موجود، و<code>409 Conflict</code> تعني أن الطلب صالح لكنه يتعارض مع الحالة الحالية (مثل بريد مستخدم مسبقًا)، و<code>422</code> تعني أن الشكل صحيح لكن القيم مخالفة لقواعد العمل. <strong>Problem Details</strong> صيغة موحدة للأخطاء، وليست رسالة stack trace. لا تكشف تفاصيل داخلية للعميل.</p>`
        },
        {
          title: "مفتاح إعادة المحاولة",
          code: `POST /api/orders HTTP/1.1\nIdempotency-Key: 7f3c2a9e-4d1b-4c6e-9f20-1a5b8c7d6e4f`,
          lang: "http",
          body: `<p>عند انقطاع الشبكة بعد إرسال الطلب، قد يعيد العميل المحاولة. لو كان الطلب إنشاء طلب شراء، فقد يُنشئ طلبين. <code>Idempotency-Key</code> معرف فريد يرسله العميل؛ الخادم يحفظ نتيجة المفتاح ويعيد نفس النتيجة عند التكرار. هذا ليس بديلًا عن معاملة قاعدة بيانات، لكنه يحمي الحد الذي لا تعرف فيه هل وصل الطلب أم لا.</p>`
        }
      ],
      compare: {
        intro: `<p>المقارنة ليست بين «REST» و«غير REST» كحرب مذهبية، بل بين عقد يمكن التنبؤ به وعقد يحتاج توثيقًا لكل استدعاء.</p>`,
        before: {
          label: "أفعال في المسار",
          lang: "http",
          title: "API بأسلوب RPC",
          code: `GET /getProducts\nGET /getProductById?id=5\nPOST /createProduct\nPOST /deleteProduct?id=5`,
          points: [
            "كل عملية تحتاج اسمًا جديدًا وتوثيقًا خاصًا.",
            "الحذف بـPOST يخالف دلالة HTTP.",
            "لا يمكن استخدام cache الـ GET بشكل طبيعي.",
            "المسارات تكشف تفاصيل التنفيذ."
          ]
        },
        after: {
          label: "موارد وmethods",
          lang: "http",
          title: "API بأسلوب REST",
          code: `GET /api/products\nGET /api/products/5\nPOST /api/products\nDELETE /api/products/5`,
          points: [
            "المورد ثابت، والـ method يحدد العملية.",
            "DELETE idempotent، وGET آمن.",
            "الفلترة والترقيم في query.",
            "العقد أوضح للعميل والوسطاء."
          ]
        },
        verdict: `<p>لا يعني REST أن كل شيء يجب أن يكون CRUD. العمليات الانتقالية مثل <code>/orders/5/cancel</code> مشروعة، لكن اجعلها استثناءً موثقًا لا قاعدة. الأهم أن يكون السلوك متسقًا عبر كل الموارد.</p>`
      },
      internals: `\n        <p>Kestrel يستقبل بايتات TCP ويفكّها إلى طلب HTTP. في HTTP/1.1 يكون الترويسات نصية ويُحتفظ بالاتصال مفتوحًا (keep-alive) لعدة طلبات متتالية. في HTTP/2 تُرسل الإطارات بشكل ثنائي مع HPACK لضغط الترويسات، ويمكن تعدد طلبات متزامنة على اتصال واحد. HTTP/3 يعمل فوق QUIC/UDP ويقلل تأخير إنشاء الاتصال، لكنه لا يغيّر دلالات method/status التي تصمم بها الـ API.</p>\n        <p>كل طلب يمر عبر pipeline: Kestrel → hosting → middleware → routing → endpoint → response. ترويسات مثل <code>Content-Length</code> و<code>Transfer-Encoding</code> تحدد كيف يُقرأ الجسم. الحدود الافتراضية ل حجم الجسم والترويسات موجودة لحماية الذاكرة؛ لا ترفعها بلا قياس. إن كان الملف كبيرًا، استخدم streaming أو multipart مع حد واضح، لا <code>byte[]</code> ضخمًا.</p>\n        <p>الـ stateless له ثمن: كل طلب يعيد التحقق من التوكن ويقرأ الإعدادات أو الكاش. لكنه يسمح بتوزيع الحمل وتشغيل نسخ متعددة بلا sticky sessions. أي حالة مشتركة (سلة، جلسة، rate limit) يجب أن تعيش في Redis أو قاعدة بيانات، لا في <code>static Dictionary</code> داخل عملية واحدة.</p>\n        <h3>إعادة المحاولة والتزامن</h3>\n        <p>حتى PUT idempotent قد يتعارض مع تعديلين متزامنين. استخدم <code>If-Match</code> مع ETag أو رقم نسخة (row version) لتطبيق التفاؤل. وعند إنشاء مورد، اجعل قاعدة البيانات تفرض قيدًا فريدًا بدل الاعتماد على فحص «هل موجود؟» ثم إدراج، لأن بينهما نافذة سباق.</p>\n        <h3>ما لا يفعله HTTP</h3>\n        <p>HTTP لا يضمن أن الطلب وصل مرة واحدة، ولا أن الخادم أكمل العمل قبل انقطاع الاتصال. هو يضمن شكل الرسالة ودلالات الحالة إن التُزم بها. لذلك تحتاج idempotency وعمليات ذرية ومراقبة. لا تفترض أن <code>200</code> وصل للعميل يعني أنه رأى النتيجة؛ قد يكون الاتصال انقطع بعد إرسال الاستجابة.</p>\n      `,
      internalsTable: {
        head: ["Method", "Safe", "Idempotent", "الاستخدام النموذجي"],
        rows: [
          ["GET", "نعم", "نعم", "قراءة مورد أو قائمة"],
          ["HEAD", "نعم", "نعم", "ترويسات فقط"],
          ["POST", "لا", "لا", "إنشاء أو عملية غير قابلة للتكرار"],
          ["PUT", "لا", "نعم", "استبدال مورد كامل"],
          ["PATCH", "لا", "ليس مضمونًا", "تعديل جزئي"],
          ["DELETE", "لا", "نعم", "حذف مورد"]
        ]
      },
      tips: [
        {
          title: "سمِّ الموارد لا الأفعال",
          body: "استخدم <code>/api/products</code> و<code>/api/products/{id}</code>. الأفعال تأتي من method. الاستثناءات الانتقالية مثل <code>/cancel</code> وثّقها بوضوح."
        },
        {
          title: "لا تخلط 401 و403",
          body: "<code>401</code> تعني «من أنت؟» أو التوكن غير صالح. <code>403</code> تعني «أعرف من أنت، لكن لا تملك الصلاحية». الخلط يربك العميل ويسرّب معلومات أقل أو أكثر مما ينبغي."
        },
        {
          title: "استخدم Idempotency-Key للعمليات الحساسة",
          body: "الدفع وإنشاء الطلب والتحويلات المالية تحتاج مفتاحًا يمنع التكرار عند إعادة المحاولة. خزّن المفتاح والنتيجة في قاعدة البيانات مع قيد فريد، لا في ذاكرة العملية."
        },
        {
          title: "لا تضع أسرارًا في query string",
          body: "روابط الـ API تظهر في السجلات والتاريخ والمراجع. استخدم <code>Authorization</code> أو cookies آمنة. حتى لو كان الاتصال TLS، فالتسجيل قد يحتفظ بالمسار كاملًا."
        }
      ],
      quiz: [
        {
          q: "أي method يُعتبر idempotent؟",
          options: ["POST", "PUT", "PATCH دائمًا", "لا يوجد method idempotent"],
          answer: 1,
          explain: "PUT يستبدل المورد بنفس الحالة عند تكراره بنفس الجسم. POST ليس idempotent، وPATCH قد يكون أو لا يكون حسب تصميمه."
        },
        {
          q: "ما الفرق بين 401 و403؟",
          options: [
            "لا فرق؛ كلاهما خطأ في الخادم.",
            "401 تعني أن الهوية مفقودة أو غير صالحة، و403 تعني أن الهوية صالحة لكن الصلاحية غير كافية.",
            "401 للمورد غير الموجود، و403 للطلب المشوّه.",
            "403 تعني إعادة توجيه دائمة."
          ],
          answer: 1,
          explain: "401 تحدٍ للمصادقة: من أنت؟ 403 قرار تفويض: أعرفك لكن ممنوع. الخلط بينهما يجعل تشخيص العميل أصعب."
        },
        {
          q: "لماذا نحتاج Idempotency-Key مع POST؟",
          options: [
            "لأن POST لا يمكن أن يحمل JSON.",
            "لمنع إنشاء سجلين عند إعادة المحاولة بسبب انقطاع الشبكة.",
            "لتشفير جسم الطلب تلقائيًا.",
            "لتحويل POST إلى GET."
          ],
          answer: 1,
          explain: "POST غير idempotent. إذا انقطع الاتصال بعد وصول الطلب، قد يعيد العميل الإرسال. المفتاح يسمح للخادم بإرجاع نتيجة الطلب الأول بدل إنشاء مورد ثانٍ."
        }
      ],
      capstone: {
        title: "عقد HTTP لـ Souq API",
        goal: "اكتب عقد endpoints واضحًا قبل تنفيذها، ثم اختبر الحالات الأساسية بـ curl أو ملف .http.",
        tasks: [
          "وثّق <code>GET /api/products</code> و<code>GET /api/products/{id}</code> مع الاستعلام والاستجابة.",
          "أضف <code>POST /api/products</code> يعيد <code>201</code> و<code>Location</code>، و<code>DELETE /api/products/{id}</code> يعيد <code>204</code> أو <code>404</code>.",
          "أضف <code>Idempotency-Key</code> إلى <code>POST /api/orders</code> ووثّق سلوك التكرار.",
          "أضف <code>ETag</code> أو <code>Cache-Control</code> مناسبًا لقراءة تفاصيل منتج عام.",
          "اختبر 401 و403 و404 و409 بطلبين على الأقل، وسجّل الاستجابات في <code>docs/api.md</code>."
        ],
        code: {
          lang: "csharp",
          title: "خريطة أولية للـ endpoints",
          code: `app.MapGet("/api/products", (CancellationToken ct) => ...);\napp.MapGet("/api/products/{id:guid}", (Guid id, CancellationToken ct) => ...);\napp.MapPost("/api/products", (CreateProductRequest request, CancellationToken ct) => ...);\napp.MapDelete("/api/products/{id:guid}", (Guid id, CancellationToken ct) => ...);`,
        },
      },
    },
    {
      id: "project-anatomy",
      title: "ملفات المشروع: من csproj إلى appsettings",
      duration: 20,
      level: "مبتدئ",
      summary:
        "كل ملف في قالب webapi له سبب وجود. سنفتح المشروع ملفًا ملفًا، ونفهم ترتيب مصادر الإعداد، والفرق بين بيئة التطوير والإنتاج، وكيف يصل الطلب من المنفذ إلى الكود.",
      keywords: ["csproj", "appsettings", "launchSettings", "Environment", "configuration", "content root", "OpenAPI"],
      objectives: [
        "تشرح وظيفة كل ملف أساسي في مشروع Web API.",
        "تعرف ترتيب أولوية مصادر الإعداد في ASP.NET Core.",
        "تفرّق بين Development وProduction وأثرهما الأمني.",
        "تفهم الفرق بين ContentRoot وWebRoot.",
      ],
      concept: `
        <p>قالب <code>dotnet new webapi</code> في .NET 10 ينتج مشروعًا صغيرًا مقصودًا: ملف <code>Program.cs</code>، ملف مشروع، إعدادات، ومجلد خصائص. لا توجد مجلدات Controllers أو Models لأن القالب الافتراضي يستخدم <strong>Minimal APIs</strong>. هذا ليس نقصًا؛ إنه اختيار تصميمي: ابدأ صغيرًا وأضف طبقات عندما تحتاجها.</p>
        <h3>خريطة الملفات</h3>
        <ul>
          <li><code>Souq.Api.csproj</code>: هوية المشروع، الـ TFM، والحزم. لا تضع منطقًا هنا.</li>
          <li><code>Program.cs</code>: نقطة الدخول وتكوين الحاوية وخط الأنابيب. في القالب الصغير يكون كل شيء فيه.</li>
          <li><code>appsettings.json</code>: إعدادات مشتركة بين البيئات. يجب ألا يحتوي أسرارًا.</li>
          <li><code>appsettings.Development.json</code>: تجاوزات محلية تُحمَّل فوق الملف الأساسي.</li>
          <li><code>Properties/launchSettings.json</code>: كيف تشغّل محليًا (منفذ، بيئة، متغيرات). لا يُنشر.</li>
          <li><code>obj/</code> و<code>bin/</code>: نواتج البناء. لا تُرفع إلى Git.</li>
        </ul>
        <p>ملف <code>appsettings.json</code> ليس «ملف الإعداد الوحيد». ASP.NET Core يبني سلسلة مزوّدات إعداد، وكل مزوّد لاحق يتفوق على السابق. الترتيب الافتراضي تقريبًا: <code>appsettings.json</code> ← <code>appsettings.{Environment}.json</code> ← User Secrets (في Development) ← متغيرات البيئة ← وسائط سطر الأوامر. هذا الترتيب هو سبب كون متغيرات البيئة أقوى من الملفات — وهو ما نعتمد عليه في Docker.</p>
        <h3>البيئة ليست مجرد نص</h3>
        <p><code>ASPNETCORE_ENVIRONMENT</code> يحدد اسم البيئة. عند <code>Development</code> تُفعّل تفاصيل الأخطاء وSwagger/OpenAPI محليًا، وتُحمَّل ملفات إعداد التطوير. عند <code>Production</code> تُخفى التفاصيل ويجب أن تكون الإعدادات صارمة. لا تعتمد على <code>IsDevelopment()</code> كآلية أمان وحيدة؛ اجعل السلوك الافتراضي آمنًا حتى لو نُسي المتغير.</p>
        <h3>ContentRoot مقابل WebRoot</h3>
        <p><strong>ContentRoot</strong> هو جذر ملفات التطبيق (حيث appsettings وملفات المحتوى). <strong>WebRoot</strong> هو <code>wwwroot</code> للملفات الثابتة. عند تشغيل التطبيق من مجلد مختلف (مثل خدمة systemd أو Docker) قد يتغيّر ContentRoot، فتضيع ملفات الإعداد. هذا سبب شائع لخطأ «configuration file not found» في الإنتاج.</p>
      `,
      walkthrough: [
        {
          title: "Sdk في أعلى ملف المشروع",
          code: `<Project Sdk="Microsoft.NET.Sdk.Web">`,
          lang: "xml",
          body: `<p>هذا السطر يحدد نوع المشروع. <code>Microsoft.NET.Sdk.Web</code> يضيف مراجع ASP.NET Core وأدوات النشر وقواعد بناء الويب. لو استخدمت <code>Microsoft.NET.Sdk</code> العادي، ستحتاج إضافة إطار العمل يدويًا. الـ SDK ليس حزمة NuGet تُحمَّل لكل مشروع؛ هو جزء من بيئة .NET.</p>`
        },
        {
          title: "الإطار المستهدف",
          code: `<TargetFramework>net10.0</TargetFramework>`,
          lang: "xml",
          body: `<p>يحدد إصدار .NET الذي سيُبنى عليه المشروع. <code>net10.0</code> يعني .NET 10. لا تخلط بينه وبين <code>net48</code> (NET Framework) أو <code>netstandard2.0</code> (واجهة مشتركة للمكتبات). تغيير هذا السطر قد يغيّر واجهات API المتاحة وسلوك runtime بالكامل.</p>`
        },
        {
          title: "Nullability وUsing الضمنية",
          code: `<Nullable>enable</Nullable>
<ImplicitUsings>enable</ImplicitUsings>`,
          lang: "xml",
          body: `<p><code>Nullable</code> يفعّل تحليل nullable reference types، فيحذرك من احتمال null. <code>ImplicitUsings</code> يضيف using شائعة مثل <code>System</code> و<code>System.Linq</code> تلقائيًا، فيقلل الضوضاء. هذان الخياران ليسا تجميليين؛ الأول يمنع أخطاء، والثاني يقلل كودًا مكررًا. لا تعطّلهما لمجرد أن التحذيرات تزعجك.</p>`
        },
        {
          title: "مرجع حزمة",
          code: `<ItemGroup>
  <PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
</ItemGroup>`,
          lang: "xml",
          body: `<p><code>PackageReference</code> يربط المشروع بحزمة NuGet وإصدار محدد. عند restore، يبني MSBuild شجرة الاعتماديات ويكتبها في <code>project.assets.json</code>. لا تنسخ DLL من مجلد إلى آخر؛ هذا يكسر التتبع الأمني والتحديث. استخدم <code>dotnet add package</code> أو محررًا يفهم المشروع.</p>`
        },
        {
          title: "ملف تشغيل التطوير",
          code: `{
  "profiles": {
    "https": {
      "commandName": "Project",
      "applicationUrl": "https://localhost:7090;http://localhost:5090",
      "environmentVariables": {
        "ASPNETCORE_ENVIRONMENT": "Development"
      }
    }
  }
}`,
          lang: "json",
          body: `<p><code>launchSettings.json</code> يخصّ التشغيل المحلي فقط، ولا يُنشر. يحدد المنافذ والمتغيرات وطريقة التشغيل. <code>ASPNETCORE_ENVIRONMENT=Development</code> يفعّل صفحة الأخطاء التفصيلية وOpenAPI في المثال. لا تعتمد على هذا الملف في الإنتاج؛ الإعداد يأتي من بيئة النشر.</p>`
        },
        {
          title: "إعدادات التطبيق",
          code: `{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}`,
          lang: "json",
          body: `<p><code>appsettings.json</code> إعدادات افتراضية تُقرأ عند بدء المضيف. ترتيب الأولوية: الملف الأساسي، ثم ملف البيئة، ثم user secrets في التطوير، ثم متغيرات البيئة، ثم وسائط سطر الأوامر. لا تضع أسرارًا هنا. <code>AllowedHosts</code> يحمي من Host header attacks عند ضبطه بقيمة محددة بدل <code>*</code>.</p>`
        },
        {
          title: "Program.cs نقطة البداية",
          code: `var builder = WebApplication.CreateBuilder(args);
builder.Services.AddOpenApi();
var app = builder.Build();
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.Run();`,
          lang: "csharp",
          body: `<p>هذه هي دورة الحياة كاملة: إنشاء builder يقرأ الإعدادات ويسجل الخدمات، ثم Build يبني الحاوية، ثم تسجيل endpoint، ثم Run يبدأ Kestrel. لاحظ أن <code>MapGet</code> لا ينفّذ الـ lambda الآن؛ هو يسجّله. عند وصول طلب <code>/health</code> فقط يُنفّذ ويعيد JSON. شرح كل سطر بالتفصيل في درس Program.cs.</p>`
        },
        {
          title: "مجلدات لا ترفعها إلى Git",
          code: `bin/
obj/`,
          lang: "bash",
          body: `<p><code>bin</code> مخرجات البناء، و<code>obj</code> ملفات وسيطة مثل <code>project.assets.json</code> وملفات MSBuild. كلاهما يُولَّد من المصدر والـ csproj، ورفعهما يسبب تعارضات وملفات ضخمة. أضفهما إلى <code>.gitignore</code> منذ أول commit. استثناء واحد: بعض ملفات <code>obj</code> الخاصة بالنشر النهائي لا تُرفع أيضًا.</p>`
        }
      ],
      compare: {
        intro: `<p>نفس نقطة النهاية يمكن كتابتها بنمطين. Minimal API يضعها في سطر واحد، بينما Controller يحتاج ملفًا وكائنًا وسمات. أيهما أفضل يعتمد على حجم السطح الذي تديره.</p>`,
        before: {
          label: "Controller تقليدي",
          lang: "csharp",
          title: "ProductsController.cs",
          code: `[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _service;

    public ProductsController(IProductService service) => _service = service;

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<ProductDto>>> GetAll(
        CancellationToken ct)
    {
        var products = await _service.GetAllAsync(ct);
        return Ok(products);
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ProductDto>> GetById(int id, CancellationToken ct)
    {
        var product = await _service.GetByIdAsync(id, ct);
        return product is null ? NotFound() : Ok(product);
    }
}`,
          points: [
            "ملف منفصل لكل مجموعة، مع سمات ووراثة.",
            "اكتشاف تلقائي عبر Application Parts.",
            "مناسب للفرق الكبيرة وسطح API واسع.",
          ],
        },
        after: {
          label: "Minimal API",
          lang: "csharp",
          title: "Program.cs",
          code: `var group = app.MapGroup("/api/products")
    .WithTags("Products");

group.MapGet("/", async (IProductService service, CancellationToken ct) =>
    TypedResults.Ok(await service.GetAllAsync(ct)));

group.MapGet("/{id:int}", async Task<Results<Ok<ProductDto>, NotFound>> (
    int id, IProductService service, CancellationToken ct) =>
{
    var product = await service.GetByIdAsync(id, ct);
    return product is null ? TypedResults.NotFound() : TypedResults.Ok(product);
});`,
          points: [
            "كود أقل وبدء أسرع، وربط تلقائي للـ DI.",
            "نتائج مُصنّفة (TypedResults) تُحسّن OpenAPI.",
            "مناسب للـ APIs الصغيرة والمتوسطة.",
          ],
        },
        verdict: `<p>القالب الافتراضي اليوم يوصي بـ Minimal APIs للمشاريع الجديدة. لكن القرار الحقيقي ليس أيديولوجيًا: إذا كنت تحتاج <em>Model Binding</em> متقدمًا أو <em>Application Parts</em> أو فريقًا اعتاد Controllers، فاستخدمها. المهم أن يكون الاختيار واعيًا وثابتًا في المشروع.</p>`,
      },
      internals: `
        <p>عند بدء التشغيل، يبحث المضيف عن ContentRoot ثم يبني <code>IConfigurationRoot</code>. كل مزوّد يعيد أزواج مفتاح/قيمة، والقراءة تكون آخر قيمة فازت. هذا يعني أن <code>ConnectionStrings:Default</code> في متغير بيئة يُكتب هكذا:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>ConnectionStrings__Default=Host=db;Database=souq;Username=app;Password=...</code></pre>
        <p>لاحظ الشرطة المزدوجة <code>__</code> لأن النقطتين غير مسموحتين في أسماء متغيرات البيئة على Linux. هذه التفصيلة تكسر نشرات كثيرة.</p>
        <p>بعد بناء الإعداد، تُسجَّل الخدمات في <code>IServiceCollection</code>. هذا مجرد <em>وصف</em>؛ لا يُنشأ كائن ولا تُفتح اتصالات. ثم <code>builder.Build()</code> يبني <code>IServiceProvider</code> ويتحقق من صلاحية النطاقات (في Development). بعدها يُبنى خط الأنابيب، ثم <code>app.Run()</code> يبدأ Kestrel ويحجز المنفذ.</p>
        <p>أما <code>launchSettings.json</code> فلا يدخل في سلسلة الإعداد كملف عادي؛ Visual Studio و<code>dotnet run</code> يقرآنه لضبط متغيرات البيئة وعنوان URL قبل بدء العملية. ولهذا لا ترى إعداداته داخل التطبيق المنشور.</p>
      `,
      internalsTable: {
        head: ["المصدر", "الأولوية", "الاستخدام النموذجي"],
        rows: [
          ["appsettings.json", "1 (الأدنى)", "قيم افتراضية آمنة"],
          ["appsettings.{Env}.json", "2", "تجاوزات التطوير"],
          ["User Secrets", "3 (Development فقط)", "مفاتيح محلية"],
          ["Environment Variables", "4", "Docker وCI والإنتاج"],
          ["Command line args", "5 (الأعلى)", "تشغيل مؤقت/اختبار"],
        ],
      },
      tips: [
        {
          title: "افصل الإعداد عن الكود",
          body: "لا تقرأ <code>Configuration[\"...\"]</code> داخل الخدمات. اربط الإعداد بنوع مُصنّف عبر <code>IOptions&lt;T&gt;</code> مع تحقق عند البدء. سنطبّق ذلك في درس DI.",
        },
        {
          title: "اجعل Production آمنًا افتراضيًا",
          body: "لا تضع <code>if (env.IsDevelopment())</code> حول أشياء يجب أن تعمل دائمًا. اجعل الميزات الخطرة (OpenAPI UI، تفاصيل الأخطاء) هي المستثناة، لا العكس.",
        },
        {
          title: "ممنوع أسرار في appsettings",
          body: "أي قيمة تُرفع إلى Git تُعتبر مسرّبة. حتى لو حذفتها لاحقًا، تبقى في تاريخ المستودع. استخدم Secrets أو متغيرات البيئة من البداية.",
        },
        {
          title: "افحص منفذ التشغيل",
          body: "إذا لم تستجب نقطة النهاية، تحقق من <code>applicationUrl</code> في launchSettings ومن مخرجات السجل «Now listening on». لا تخمّن المنفذ.",
        },
      ],
      quiz: [
        {
          q: "أي مصدر إعداد له الأولوية الأعلى افتراضيًا؟",
          options: ["appsettings.json", "appsettings.Development.json", "متغيرات البيئة", "وسائط سطر الأوامر"],
          answer: 3,
          explain:
            "الوسائط تُضاف آخرًا فتتفوق على الجميع. الترتيب: appsettings ثم ملف البيئة ثم Secrets ثم متغيرات البيئة ثم الوسائط.",
        },
        {
          q: "ما الذي يفعله <code>builder.Build()</code>؟",
          options: [
            "يبدأ Kestrel ويستقبل الطلبات.",
            "ينشئ IServiceProvider ويجهّز التطبيق قبل بناء خط الأنابيب.",
            "ينشر التطبيق إلى الإنتاج.",
            "يعيد تحميل appsettings تلقائيًا.",
          ],
          answer: 1,
          explain:
            "Build() يبني حاوية الخدمات ويجهّز WebApplication. بدء الاستماع يحدث في app.Run().",
        },
        {
          q: "لماذا لا يُنشر launchSettings.json؟",
          options: [
            "لأنه ملف ثنائي.",
            "لأنه يخصّ التشغيل المحلي فقط، والإنتاج يعتمد متغيرات بيئة حقيقية.",
            "لأنه يحتوي كود C#.",
            "لأنه خاص بـ IIS فقط.",
          ],
          answer: 1,
          explain:
            "هو أداة تطوير لتحديد المنفذ والبيئة محليًا. الإنتاج يضبط القيم عبر متغيرات البيئة أو منصة النشر.",
        },
      ],
      capstone: {
        title: "تنظيف قالب Souq.Api",
        goal: "نجعل المشروع نظيفًا وذا معنى: نحذف مثال الطقس، نضيف Health endpoint، ونضبط إعدادات البيئة قبل بناء أي ميزة.",
        tasks: [
          "احذف نقطة WeatherForecast ومعه نوعها إن وُجد.",
          "أضف <code>GET /health</code> تعيد حالة الخدمة واسم البيئة.",
          "أضف <code>appsettings.Development.json</code> قيمة <code>App:Name</code> واستخدمها في الاستجابة.",
          "أضف <code>.gitignore</code> يغطي <code>bin/</code> و<code>obj/</code> و<code>.env</code>.",
          "شغّل التطبيق وتأكد أن <code>/health</code> تعمل في Development فقط بالقيم الصحيحة.",
        ],
        code: {
          lang: "csharp",
          title: "Health endpoint",
          code: `app.MapGet("/health", (IConfiguration config, IWebHostEnvironment env) =>
    Results.Ok(new
    {
        status = "ok",
        app = config["App:Name"] ?? "Souq.Api",
        environment = env.EnvironmentName,
        utc = DateTimeOffset.UtcNow
    }));`,
        },
      },
    },
    {
      id: "program-cs",
      title: "Program.cs سطرًا بسطر وTop-Level Statements",
      duration: 22,
      level: "متوسط",
      summary:
        "ما الذي يحدث فعليًا عند تشغيل Program.cs؟ سنفكّك top-level statements، ونفصل بين تسجيل الخدمات وبناء خط الأنابيب، ونفهم لماذا الترتيب يغيّر السلوك.",
      keywords: ["top-level statements", "WebApplicationBuilder", "WebApplication", "middleware order", "Build", "Run", "partial Program"],
      objectives: [
        "تشرح كيف يحوّل المترجم top-level statements إلى method Main.",
        "تفرّق بين builder.Services وapp.Use* وapp.Map*.",
        "ترتّب Middleware ترتيبًا صحيحًا وتفسّر سبب كل موضع.",
        "تستخدم <code>public partial class Program</code> لاختبارات التكامل.",
      ],
      concept: `
        <p>ملف Program.cs في القالب يبدو كسكربت، لكنه ليس كذلك. C# يسمح بـ <strong>Top-Level Statements</strong>: كتابة التعليمات خارج أي class. المترجم يغلّفها تلقائيًا في <code>class Program</code> ودالة <code>Main(string[] args)</code>، ويعيد كتابة <code>return</code> و<code>await</code> بما يناسب. النتيجة طريقة <code>async Task Main</code> مخفية. هذا يفسّر لماذا لا تستطيع تعريف أكثر من ملف top-level في نفس المشروع.</p>
        <p>البنية الذهنية الصحيحة من ثلاث طبقات:</p>
        <ol>
          <li><strong>builder</strong>: مرحلة التسجيل. تضيف خدمات إلى الحاوية وتضبط الإعداد والسجلات. لا يوجد طلب بعد.</li>
          <li><strong>app</strong>: مرحلة التكوين. تبني خط الأنابيب: <code>Use...</code> للمكوّنات الوسيطة، و<code>Map...</code> لنقاط النهاية.</li>
          <li><strong>Run</strong>: مرحلة التشغيل. Kestrel يستمع، والمضيف يدير دورة الحياة والإيقاف اللطيف.</li>
        </ol>
        <p>الخطأ الشائع: الاعتقاد أن <code>app.MapGet</code> ينفّذ الكود فورًا. الحقيقة أنه يسجّل <em>Endpoint</em> في جدول التوجيه. الكود يُنفّذ فقط عند وصول طلب يطابق القالب.</p>
        <h3>لماذا الترتيب مهم؟</h3>
        <p>الـ Middleware يشبه طبقات بصل: كل طبقة تستدعي التالية، ويمكنها أن تعمل قبل وبعد. إذا وضعت <code>UseAuthorization</code> بعد <code>MapGet</code> فلن تُطبَّق على نقطة النهاية، لأن التوجيه يكون قد اختار التنفيذ. وإذا وضعت <code>UseCors</code> بعد المصادقة، فقد تُرفض طلبات preflight قبل معالجتها. الترتيب ليس ذوقًا؛ إنه منطق تنفيذ.</p>
        <h3>نقطة النهاية والمضيف</h3>
        <p><code>app.Run()</code> يحجز المنفذ ويبدأ حلقة الاستقبال. عند وصول إشارة إيقاف (SIGTERM في Docker)، يبدأ <strong>Graceful Shutdown</strong>: يتوقف عن قبول اتصالات جديدة، ويعطي الطلبات الجارية وقتًا محددًا لتنتهي. هذا هو الفرق بين نشر بلا أخطاء ونشر يقطع طلبات المستخدمين.</p>
      `,
      walkthrough: [
        {
          title: "إنشاء الـ Builder وقراءة الإعدادات",
          code: `var builder = WebApplication.CreateBuilder(args);`,
          body: `<p>هذا السطر لا يشغّل الخادم ولا ينشئ طلبًا. هو ينشئ كائنًا يدير دورة حياة التطبيق: يحدد <code>ContentRoot</code> (مجلد المشروع الذي تُقرأ منه الملفات)، ويبني سلسلة الإعدادات بالترتيب: <code>appsettings.json</code> ثم <code>appsettings.{Environment}.json</code> ثم متغيرات البيئة ثم وسائط سطر الأوامر. الوسائط التي تصل في <code>args</code> لها الأولوية الأعلى، ولهذا تستطيع تشغيل نفس النشر بإعداد مختلف دون تعديل ملف.</p><p>الـ builder يسجّل أيضًا الخدمات الأساسية: Logging، Options، Hosting، Routing، وKestrel. لا يوجد اتصال شبكي بعد. الفكرة المهمة: <strong>مرحلة التسجيل</strong> منفصلة عن <strong>مرحلة التشغيل</strong>.</p>`
        },
        {
          title: "تسجيل ProblemDetails",
          code: `builder.Services.AddProblemDetails();`,
          body: `<p>يضيف خدمة تُحوّل الأخطاء إلى شكل <code>application/problem+json</code> قياسي: <code>type</code>، <code>title</code>، <code>status</code>، <code>detail</code>، و<code>instance</code>. مجرد التسجيل لا يغيّر أي استجابة؛ تحتاجه middleware مثل <code>UseExceptionHandler</code> أو <code>UseStatusCodePages</code> لكي يستخدمه. تسجيله مبكرًا يجعل كل الأخطاء في الـ API لها عقد واحد يفهمه العميل.</p>`
        },
        {
          title: "تسجيل OpenAPI",
          code: `builder.Services.AddOpenApi();`,
          body: `<p>يضيف الخدمات التي تقرأ نقاط النهاية والأوصاف وتولّد مستند OpenAPI. هذا أيضًا تسجيل فقط. لاحقًا يربط <code>app.MapOpenApi()</code> مسارًا يعرض المستند، لكنه يظهر في بيئة التطوير فقط في المثال. في الإنتاج قد تعرضه خلف بوابة داخلية أو تمنعه تمامًا لأنه يكشف شكل الـ API.</p>`
        },
        {
          title: "تسجيل CORS قبل الاستخدام",
          code: `builder.Services.AddCors(options =>
{
    options.AddPolicy("web", policy =>
        policy.WithOrigins("https://app.souq.example")
              .AllowAnyHeader()
              .AllowAnyMethod());
});`,
          body: `<p>هنا نعرّف سياسة باسم <code>web</code> تسمح لمتصفح التطبيق الأمامي بالاتصال بالـ API. المتصفح هو الذي يفرض CORS، وليس الخادم؛ الخادم يرسل ترويسات <code>Access-Control-Allow-*</code> ليقرر المتصفح هل يسمح بالقراءة. لاحظ أننا لم نستخدم <code>AllowAnyOrigin</code>؛ نحدد أصلًا معروفًا. في الإنتاج لا تخلط <code>AllowCredentials</code> مع أصل مفتوح، لأن المتصفحات ترفض ذلك لأسباب أمنية.</p><p>السياسة يجب أن تُسجّل قبل <code>UseCors</code>، وإلا فشل التطبيق عند بدء التشغيل برسالة أن السياسة غير موجودة. هذا مثال على أن ترتيب التسجيل وترتيب الأنابيب شيئان مختلفان.</p>`
        },
        {
          title: "تسجيل خدمة التطبيق",
          code: `builder.Services.AddScoped<IProductService, ProductService>();`,
          body: `<p>نربط الواجهة <code>IProductService</code> بالتنفيذ <code>ProductService</code> بعمر <strong>Scoped</strong>: يخلق الـ DI container نسخة واحدة لكل طلب HTTP، ويعيد استخدامها داخل الطلب نفسه، ثم يتخلص منها بعده إن كانت <code>IDisposable</code>. هذا مناسب لخدمة تستخدم <code>DbContext</code> لأن DbContext نفسه Scoped وليس آمنًا للمشاركة بين طلبات متوازية.</p><p>السطر لا ينشئ <code>ProductService</code> الآن. الـ container يسجّل «وصفة» فقط، وينشئ الكائن عند أول طلب يحتاجه. هذا هو <strong>Lazy Resolution</strong>، ويقلل زمن بدء التشغيل.</p>`
        },
        {
          title: "بناء الـ Provider والتحقق من التكوين",
          code: `var app = builder.Build();`,
          body: `<p><code>Build()</code> يجمّد تسجيلات الخدمات، وينشئ <code>IServiceProvider</code> الجذري، ويتحقق من بعض الإعدادات. من هذه اللحظة لا يمكن إضافة خدمة جديدة إلى نفس الحاوية. كما تُنشأ الخدمات المفردة (Singleton) التي طلبتها أثناء البناء، وقد يظهر خطأ هنا إذا كان تنفيذها يعتمد على خدمة Scoped، لأن Singleton لا يجوز أن يحتفظ بـ Scoped.</p><p>بعد <code>Build</code> ننتقل من مرحلة «ماذا لدينا؟» إلى مرحلة «كيف يعالج الطلب؟». الخادم لم يبدأ الاستماع بعد.</p>`
        },
        {
          title: "وضع معالج الأخطاء أولًا",
          code: `app.UseExceptionHandler();`,
          body: `<p>يضيف Middleware في أول الأنبوب تقريبًا. عندما يرمي أي مكوّن لاحق استثناءً غير معالج، يلتقطه هذا المكوّن، ويسجّل الخطأ، ثم يعيد تنفيذ الطلب عبر مسار داخلي ينتج استجابة ProblemDetails بدلًا من كشف stack trace للعميل.</p><p>لماذا أولًا؟ لأن Middleware يعمل مثل طبقات: كل طبقة تستطيع أن تلتقط ما يحدث في الطبقات الأعمق. إذا وضعته بعد المصادقة أو التوجيه، فلن يحمي الأخطاء التي تحدث قبله. لكن لا تضعه قبل middleware لا يحتاج حماية مثل <code>UseHttpsRedirection</code> إلا بوعي؛ الترتيب هنا قرار معماري.</p>`
        },
        {
          title: "تحويل أكواد الحالة الفارغة",
          code: `app.UseStatusCodePages();`,
          body: `<p>إذا أرجع endpoint حالة <code>404</code> أو <code>401</code> بلا جسم، يضيف هذا المكوّن جسمًا مناسبًا. لا يعمل إذا كانت الاستجابة تحتوي جسمًا بالفعل. فائدته أن العميل لا يستلم استجابة فارغة يصعب تفسيرها، لكنه ليس بديلًا عن معالجة الأخطاء المتوقعة في منطق التطبيق.</p>`
        },
        {
          title: "تقييد OpenAPI ببيئة التطوير",
          code: `if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}`,
          body: `<p>هذا <code>if</code> يُنفّذ مرة واحدة عند بدء التطبيق، وليس مع كل طلب. <code>IsDevelopment</code> تقرأ متغير البيئة <code>ASPNETCORE_ENVIRONMENT</code>. إذا كانت القيمة <code>Development</code> يُسجَّل مسار المستند؛ وإلا فلا وجود للمسار أصلًا، ولن يستطيع أحد الوصول إليه حتى لو عرف الرابط.</p><p>هذا أفضل من إخفاء الرابط في الواجهة فقط. الأمان الحقيقي هو عدم تسجيل نقطة النهاية في الإنتاج، أو حمايتها بسياسة واضحة.</p>`
        },
        {
          title: "إجبار HTTPS",
          code: `app.UseHttpsRedirection();`,
          body: `<p>يقرأ منفذ HTTPS من الإعدادات ويعيد توجيه طلبات HTTP إليه بحالة <code>307</code> أو <code>308</code> حسب الإعداد. في Docker خلف reverse proxy، قد يكون التوجيه مطلوبًا عند الـ proxy لا داخل التطبيق؛ وإلا حدثت حلقة توجيه إذا كان الـ proxy يتحدث HTTP مع التطبيق. الحل عادةً: فعّل <code>ForwardedHeaders</code> واضبط <code>ASPNETCORE_FORWARDEDHEADERS_ENABLED</code> بحذر، أو أنهِ TLS عند الـ proxy واعتبر الشبكة الداخلية موثوقة.</p>`
        },
        {
          title: "تفعيل CORS قبل المصادقة",
          code: `app.UseCors("web");`,
          body: `<p>يطبّق السياسة المسجلة على الطلبات. موضعه مهم: قبل <code>UseAuthentication</code> و<code>UseAuthorization</code>، لأن طلبات preflight من المتصفح لا تحمل عادة توكن المصادقة. إذا وضعته بعد المصادقة فقد تُرفض طلبات <code>OPTIONS</code> قبل أن تصل إلى CORS.</p><p>تذكّر: CORS ليس جدار حماية للـ API. هو يمنع صفحات الويب الأخرى من قراءة الاستجابة في المتصفح؛ أي عميل مثل curl يستطيع تجاهله. الحماية الحقيقية تأتي من المصادقة والتحقق من المدخلات.</p>`
        },
        {
          title: "المصادقة ثم التصريح",
          code: `app.UseAuthentication();
app.UseAuthorization();`,
          body: `<p><code>UseAuthentication</code> يقرأ بيانات الاعتماد (JWT في ترويسة <code>Authorization</code>)، يتحقق من التوقيع والصلاحية، وينشئ <code>ClaimsPrincipal</code> ويضعه في <code>HttpContext.User</code>. لا يمنع الطلب إذا لم يوجد توكن؛ فقط يملأ الهوية إن وجدت.</p><p><code>UseAuthorization</code> يأتي بعده لأنه يحتاج الهوية ليقرر هل يسمح بالوصول إلى المورد. لو عكست الترتيب، ستصبح القرارات مبنية على هوية فارغة. كلاهما يجب أن يسبق <code>Map...</code> حتى تُطبَّق السياسات على نقاط النهاية.</p>`
        },
        {
          title: "تسجيل نقطة فحص صحة",
          code: `app.MapGet("/health", () => Results.Ok(new { status = "ok" }));`,
          body: `<p>هذا السطر لا ينفّذ <code>Results.Ok</code> الآن. هو يسجّل مسارًا و<code>RequestDelegate</code> في جدول التوجيه. عند وصول <code>GET /health</code> يُنشأ كائن مجهول، يُسلسل إلى JSON، وتُكتب ترويسة <code>Content-Type: application/json</code>. هذا الفحص سريع ولا يلمس قاعدة البيانات؛ للفحص العميق استخدم <code>AddHealthChecks</code> مع فحص قاعدة البيانات والكاش، لكن اجعل فحص الحياة (liveness) منفصلًا حتى لا يعيد orchestrator تشغيل التطبيق بسبب تعطل قاعدة بيانات خارجية.</p>`
        },
        {
          title: "تجميع نقاط نهاية المنتجات",
          code: `app.MapProductEndpoints();`,
          body: `<p>هذه طريقة extension method تنقل تعريفات المنتجات إلى ملف آخر، لكنها تُنفّذ أثناء بناء الأنبوب وتضيف المسارات إلى نفس <code>IEndpointRouteBuilder</code>. الفائدة تنظيمية وليست أداءً؛ التوجيه في النهاية جدول واحد. عند نمو المشروع، اجعل كل مجموعة موارد في ملف، لكن لا تنشئ «mini framework» قبل أن تحتاجه.</p>`
        },
        {
          title: "بدء الاستماع ودورة الحياة",
          code: `app.Run();`,
          body: `<p><code>Run()</code> يبدأ مضيف ASP.NET Core: يبني خادم Kestrel، يربط المنفذ، يبدأ حلقة قبول الاتصالات، ثم يحجز الخيط الحالي حتى تتوقف العملية. عند وصول <code>SIGTERM</code> (مثل <code>docker stop</code>)، يبدأ الإيقاف اللطيف: يتوقف عن قبول اتصالات جديدة، ينتظر الطلبات الجارية حتى مهلة الإعداد، ثم يغلق الـ provider ويتخلص من الموارد.</p><p>في اختبارات التكامل لا تستدعي <code>Run()</code> مباشرة؛ استخدم <code>WebApplicationFactory&lt;Program&gt;</code> الذي يشغّل المضيف في الذاكرة. ولهذا يُستخدم <code>public partial class Program { }</code> في نهاية الملف ليكون نوعًا عامًا يمكن للاختبارات الرجوع إليه.</p>`
        }
      ],
      compare: {
        intro: `<p>قبل .NET 6 كان كل مشروع يحتاج <code>Startup.cs</code> بدالتين: <code>ConfigureServices</code> و<code>Configure</code>. النمط الحديث يدمجهما في ملف واحد، لكنه يحافظ على نفس الفصل المنطقي.</p>`,
        before: {
          label: "نمط Startup القديم",
          lang: "csharp",
          title: "Startup.cs + Program.cs",
          code: `public class Startup
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddControllers();
        services.AddScoped<IProductService, ProductService>();
    }

    public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
    {
        if (env.IsDevelopment()) app.UseDeveloperExceptionPage();

        app.UseRouting();
        app.UseAuthorization();
        app.UseEndpoints(endpoints => endpoints.MapControllers());
    }
}

public class Program
{
    public static void Main(string[] args) =>
        CreateHostBuilder(args).Build().Run();
}`,
          points: [
            "ملفان ودالتان وتفويض صريح للإعداد.",
            "ترتيب UseRouting/UseEndpoints يدوي.",
            "يصعب قراءة التكوين كاملًا في مكان واحد.",
          ],
        },
        after: {
          label: "Top-level حديث",
          lang: "csharp",
          title: "Program.cs",
          code: `var builder = WebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails();
builder.Services.AddOpenApi();
builder.Services.AddCors(options =>
{
    options.AddPolicy("web", policy =>
        policy.WithOrigins("https://app.souq.example")
              .AllowAnyHeader()
              .AllowAnyMethod());
});
builder.Services.AddScoped<IProductService, ProductService>();

var app = builder.Build();

app.UseExceptionHandler();
app.UseStatusCodePages();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseCors("web");

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapProductEndpoints();

app.Run();`,
          points: [
            "تكوين واضح من أعلى لأسفل.",
            "الخدمات ثم الأنابيب ثم التشغيل.",
            "سهل التقسيم إلى extension methods لاحقًا.",
          ],
        },
        verdict: `<p>Top-level statements ليست «كودًا سحريًا»؛ هي نفس نموذج Startup بصياغة أقصر. المكسب الحقيقي هو أنك ترى دورة حياة التطبيق كاملة في شاشة واحدة. عند نمو المشروع، لا تكدّس كل شيء هنا: انقل التسجيلات إلى <code>AddInfrastructure()</code> ونقاط النهاية إلى <code>MapCatalogEndpoints()</code>.</p>`,
      },
      internals: `
        <p>دعنا نفكّك ما يفعله <code>WebApplication.CreateBuilder(args)</code>:</p>
        <ul>
          <li>ينشئ <code>HostApplicationBuilder</code> ويضبط ContentRoot.</li>
          <li>يبني سلسلة الإعداد من appsettings ومتغيرات البيئة والوسائط.</li>
          <li>يضيف سجلات Console/Debug/EventSource افتراضيًا.</li>
          <li>يسجّل خدمات ASP.NET Core الأساسية: Routing، Hosting، Options، Logging.</li>
          <li>يجهّز Kestrel كخادم افتراضي، لكنه لا يستمع بعد.</li>
        </ul>
        <p><code>builder.Services</code> هو <code>IServiceCollection</code>: قائمة من <code>ServiceDescriptor</code>. كل استدعاء <code>AddScoped</code> يضيف وصفًا، لا كائنًا. عند <code>Build()</code> تُبنى الحاوية. في Development يُفعّل <strong>ValidateScopes</strong>، فيرمي استثناءً إذا حاولت حلّ خدمة Scoped من الجذر — شبكة أمان ممتازة.</p>
        <p>ثم <code>WebApplication</code> يبني <code>RequestDelegate</code> نهائيًا. كل <code>Use</code> يضيف طبقة تغلّف الطبقة السابقة. في النهاية لديك دالة واحدة: <code>Task Invoke(HttpContext)</code>. Kestrel ينشئ <code>HttpContext</code> لكل اتصال ويمرّره إليها. كل تخصيص لـ <code>HttpContext</code> (Headers، Items، Response) هو في النهاية تعديل على كائن واحد يعبر السلسلة.</p>
        <p>أما <code>app.Run()</code> فينفّذ <code>StartAsync</code> على المضيف، الذي يبدأ <code>IServer.StartAsync</code>. ثم ينتظر <code>WaitForShutdown</code>. أي كود بعد <code>Run()</code> لا يُنفّذ حتى يتوقف التطبيق. لهذا لا تضع منطق تهيئة بعده.</p>
      `,
      tips: [
        {
          title: "Program.cs للتنسيق فقط",
          body: "إذا تجاوز الملف 80 سطرًا، ابدأ التقسيم: <code>builder.Services.AddApplication()</code>، <code>AddInfrastructure()</code>، <code>app.MapApi()</code>. هذا يجعل الاختبار والقراءة أسهل.",
        },
        {
          title: "لا تحلّ Scoped عند البدء",
          body: "استدعاء <code>app.Services.CreateScope()</code> ثم حلّ DbContext وتشغيل migration عند كل إقلاع فكرة شائعة لكنها خطرة في التوسع الأفقي. استخدم مهمة ترحيل منفصلة أو أداة نشر.",
        },
        {
          title: "أضف partial Program للاختبار",
          body: "أضف في نهاية Program.cs: <code>public partial class Program { }</code>. هذا يسمح لـ <code>WebApplicationFactory&lt;Program&gt;</code> ببدء التطبيق كاملًا في اختبارات التكامل.",
        },
        {
          title: "اختبر الإيقاف اللطيف",
          body: "شغّل التطبيق في Docker ثم أرسل SIGTERM أثناء طلب طويل. إن قُطع الطلب، اضبط <code>HostOptions.ShutdownTimeout</code>. النشر الحقيقي يختبر هذه اللحظة.",
        },
      ],
      quiz: [
        {
          q: "ماذا يحدث عند استدعاء <code>builder.Services.AddScoped&lt;T&gt;()</code>؟",
          options: [
            "يُنشأ كائن T فورًا.",
            "تُضاف وصفة تسجيل إلى IServiceCollection، ويُنشأ الكائن لاحقًا عند الطلب.",
            "يبدأ Kestrel.",
            "تُنفّذ كل نقاط النهاية مرة واحدة.",
          ],
          answer: 1,
          explain:
            "التسجيل يضيف ServiceDescriptor فقط. الحاوية تبني الكائن عند الحاجة، وفق النطاق المحدد (Transient/Scoped/Singleton).",
        },
        {
          q: "أين يجب أن يوضع UseAuthentication بالنسبة إلى UseAuthorization؟",
          options: [
            "بعد UseAuthorization.",
            "قبل UseAuthorization، لأن المصادقة تحدد هوية المستخدم قبل تقييم السياسات.",
            "لا علاقة للترتيب.",
            "داخل MapGet فقط.",
          ],
          answer: 1,
          explain:
            "المصادقة تبني ClaimsPrincipal، والتفويض يقرأها. لو تأخّرت المصادقة، ستُقيَّم السياسات على مستخدم مجهول.",
        },
        {
          q: "ما الذي يفعله <code>app.Run()</code> عمليًا؟",
          options: [
            "يبني الحاوية من جديد.",
            "يبدأ المضيف وKestrel وينتظر إشارة الإيقاف.",
            "ينفّذ كل الـ endpoints.",
            "ينشر التطبيق إلى Docker.",
          ],
          answer: 1,
          explain:
            "Run يبدأ تشغيل المضيف ثم ينتظر الإيقاف. الكود بعده لا يُنفّذ إلا بعد توقف التطبيق.",
        },
      ],
      capstone: {
        title: "تقسيم Program.cs إلى إضافات",
        goal: "نجعل Program.cs نظيفًا وقابلًا للنمو عبر نقل التسجيلات ونقاط النهاية إلى extension methods، مع إبقاء دورة الحياة واضحة.",
        tasks: [
          "أنشئ <code>Extensions/ServiceCollectionExtensions.cs</code> فيه <code>AddSouqServices</code>.",
          "أنشئ <code>Endpoints/ProductEndpoints.cs</code> فيه <code>MapProductEndpoints</code>.",
          "أضف <code>public partial class Program { }</code> في نهاية Program.cs.",
          "أضف <code>builder.Services.AddProblemDetails()</code> و<code>app.UseExceptionHandler()</code>.",
          "تأكد أن Program.cs لا يتجاوز 30 سطرًا وأن التطبيق يعمل.",
        ],
        code: {
          lang: "csharp",
          title: "Endpoints/ProductEndpoints.cs",
          code: `namespace Souq.Api.Endpoints;

public static class ProductEndpoints
{
    public static IEndpointRouteBuilder MapProductEndpoints(
        this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products").WithTags("Products");

        group.MapGet("/", () =>
            TypedResults.Ok(Array.Empty<ProductDto>()));

        return app;
    }
}

public record ProductDto(int Id, string Name, decimal Price);`,
        },
      },
    },
    {
      id: "kestrel",
      title: "Kestrel: كيف يستقبل تطبيقك HTTP فعلًا",
      duration: 21,
      level: "متوسط",
      summary:
        "Kestrel هو خادم HTTP المدمج. سنفهم دورة الاتصال، حدود الطلب، HTTP/2 وHTTP/3، ولماذا يجب أن يقف خلف Reverse Proxy في الإنتاج.",
      keywords: ["Kestrel", "reverse proxy", "HTTP/2", "HTTP/3", "limits", "TLS", "ForwardedHeaders"],
      objectives: [
        "تفسّر موقع Kestrel في مسار الطلب من Socket إلى Endpoint.",
        "تضبط المنافذ والحدود ومهلات الاتصال في الإعداد.",
        "تعرف متى تستخدم HTTP/2 أو HTTP/3.",
        "تتعامل مع Forwarded Headers خلف Nginx أو منصة سحابية.",
      ],
      concept: `
        <p>ASP.NET Core لا يأتي بخادم HTTP خارجي؛ Kestrel هو الخادم. يفتح Socket، يستقبل الاتصالات، يفكّ ترميز HTTP، ينشئ <code>HttpContext</code>، ثم يمرّر الطلب إلى خط الأنابيب. عند انتهاء المعالجة يكتب الاستجابة ويعيد الاتصال إلى بركة الاتصالات أو يغلقه وفق <code>Connection: keep-alive</code>.</p>
        <p>Kestrel ممتاز وقادر على مواجهة الإنترنت مباشرة، لكن الممارسة الإنتاجية الشائعة هي وضعه <strong>خلف Reverse Proxy</strong> مثل Nginx أو Caddy أو Ingress في Kubernetes. لماذا؟ لأن الـ Proxy يتولى TLS، وضغط الاستجابات، وتحديد المعدل، وتوزيع الحمل، وشهادة العميل، بينما يبقى Kestrel خفيفًا وقريبًا من التطبيق.</p>
        <h3>المنافذ والعناوين</h3>
        <p>يمكن ضبط الاستماع بثلاث طرق: <code>ASPNETCORE_URLS</code> (الأبسط)، قسم <code>Kestrel:Endpoints</code> في appsettings، أو <code>builder.WebHost.ConfigureKestrel</code> برمجيًا. في Docker استخدم <code>http://+:8080</code> للاستماع على كل الواجهات. المنفذ <code>+</code> أو <code>*</code> يعني كل العناوين، وليس localhost فقط — خطأ يمنع الحاوية من استقبال الطلبات.</p>
        <h3>الحدود ليست تفاصيل</h3>
        <p>كل خادم HTTP يحتاج حدودًا ضد إساءة الاستخدام: حجم body، عدد الهيدرات، مهلة الهيدرات، مهلة البقاء. القيم الافتراضية معقولة، لكن تطبيق رفع ملفات قد يحتاج رفع الحد، وتطبيقًا حساسًا قد يحتاج خفضه. الحد يُطبَّق على مستوى الخادم، ويمكن تجاوزه لنقطة نهاية محددة عبر <code>IHttpMaxRequestBodySizeFeature</code> أو <code>[RequestSizeLimit]</code> في Controllers.</p>
        <h3>HTTP/2 وHTTP/3</h3>
        <p>HTTP/2 يتيح تعدد الطلبات على اتصال واحد (Multiplexing) ويقلّل زمن التحميل. HTTP/3 يعمل فوق QUIC/UDP ويحسّن الأداء على الشبكات المتغيرة، لكنه يحتاج TLS وشهادة صحيحة، وقد لا يدعمه كل Reverse Proxy. لا تفعّله «لأنه أحدث»؛ اختبره مع البنية الفعلية.</p>
      `,
      walkthrough: [
        {
          title: "اضبط Kestrel قبل Build",
          code: `builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenAnyIP(8080);
});`,
          lang: "csharp",
          body: `<p><code>ConfigureKestrel</code> يعدّل خادم HTTP قبل بناء المضيف. الإعداد هنا يخص <strong>Kestrel</strong>، لا Middleware ولا Routing. لا تضع منطق أعمال في هذا الـ callback؛ هو يُنفّذ مرة عند الإعداد. إن كنت خلف IIS أو Nginx فقد لا تحتاج ضبط المنافذ يدويًا، لكنك تحتاج ضبط الحدود وForwardedHeaders.</p>`
        },
        {
          title: "اربط عنوانًا ومنفذًا",
          code: `options.ListenAnyIP(8080);`,
          lang: "csharp",
          body: `<p><code>ListenAnyIP</code> يستمع على كل عناوين IPv4/IPv6 المتاحة، أي ما يعادل <code>0.0.0.0</code> و<code>[::]</code>. في Docker هذا مطلوب غالبًا كي يصل الاتصال من خارج الحاوية. في جهازك المحلي، <code>ListenLocalhost</code> أكثر أمانًا لأنه لا يعرّض المنفذ للشبكة. تذكّر أن جدار الحماية وsecurity groups قد تمنع الاتصال رغم صحة الإعداد.</p>`
        },
        {
          title: "أضف TLS على منفذ آخر",
          code: `options.ListenLocalhost(5001, listen =>
    listen.UseHttps());`,
          lang: "csharp",
          body: `<p><code>UseHttps</code> يفعّل TLS على نقطة الاستماع. في التطوير يستخدم <code>dotnet dev-certs</code>، وفي الإنتاج شهادة من مدير أسرار أو مركز شهادات. TLS يشفّر الاتصال ويحمي التوكنات، لكنه لا يستبدل المصادقة. في النشر خلف reverse proxy، قد ينتهي TLS عند الـ proxy وتصل الطلب عبر HTTP داخلي؛ اضبط <code>ForwardedHeaders</code> كي يعرف التطبيق أن الأصل HTTPS.</p>`
        },
        {
          title: "حدّد حجم جسم الطلب",
          code: `options.Limits.MaxRequestBodySize = 10 * 1024 * 1024;`,
          lang: "csharp",
          body: `<p>هذا الحد يمنع طلبًا ضخمًا من استهلاك الذاكرة أو إسقاط الخادم. تجاوزه يعطي <code>413 Payload Too Large</code>. القيمة بالميغابايت هنا تقريبية؛ احسبها حسب نوع التطبيق. لرفع ملفات كبيرة، استخدم streaming أو multipart مع حد واضح، لا ترفع الحد إلى غيغابايت لمجرد أن الاختبار المحلي نجح. بعض الحدود يمكن تجاوزها لكل endpoint عبر <code>IHttpMaxRequestBodySizeFeature</code>.</p>`
        },
        {
          title: "احمِ من اتصالات بطيئة",
          code: `options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);
options.Limits.KeepAliveTimeout = TimeSpan.FromMinutes(2);`,
          lang: "csharp",
          body: `<p><code>RequestHeadersTimeout</code> يحدد كم ينتظر Kestrel اكتمال الترويسات. اتصال يفتح socket ويرسل بايتات ببطء (Slowloris) يمكن أن يحتجز موارد؛ المهلة تحدّه. <code>KeepAliveTimeout</code> يحدد بقاء الاتصال الخامل لإعادة الاستخدام. قيم قصيرة جدًا تقطع عملاء شرعيين، وقيم طويلة جدًا تحتجز اتصالات. راقب <code>Kestrel</code> metrics قبل التغيير.</p>`
        },
        {
          title: "اضبط التزامن كضغط خلفي",
          code: `options.Limits.MaxConcurrentConnections = 1000;
options.Limits.MaxConcurrentUpgradedConnections = 100;`,
          lang: "csharp",
          body: `<p>هذه حدود <strong>اتصالات</strong> لا طلبات. عند بلوغها يرفض Kestrel اتصالات جديدة بدل أن ينهار. <code>MaxConcurrentUpgradedConnections</code> يخص WebSockets وSignalR بعد ترقية الاتصال. لا تجعلها حلاً سحريًا: إن كان كل طلب ينتظر قاعدة بيانات بطيئة، رفع الحد يؤجل المشكلة. الإصلاح الحقيقي هو async، فهارس، وtimeouts.</p>`
        },
        {
          title: "شغّل المضيف وانتظر الإيقاف",
          code: `app.Run();`,
          lang: "csharp",
          body: `<p><code>Run</code> يبدأ Kestrel ويحجز الخيط الرئيسي حتى إشارة إيقاف. عند <code>SIGTERM</code> يبدأ <strong>graceful shutdown</strong>: يتوقف قبول اتصالات جديدة، تُمنح الطلبات الجارية وقتًا، ثم تُغلق الموارد. في Kubernetes، اضبط <code>terminationGracePeriodSeconds</code> أكبر من مهلة الإيقاف. لا تستخدم <code>Environment.Exit</code> لإنهاء الطلبات فجأة.</p>`
        },
        {
          title: "نسخة غير متزامنة للاختبارات",
          code: `await app.RunAsync(cancellationToken);`,
          lang: "csharp",
          body: `<p><code>RunAsync</code> يسمح للمستدعي بالانتظار والإلغاء، وهو مفيد في integration tests التي تشغّل التطبيق على منفذ عشوائي ثم توقفه. الإلغاء يمر عبر دورة حياة المضيف، لا يقتل الخيوط. لا تستبدل <code>Run</code> بـ<code>Task.Run</code>؛ هذا يخلق مضيفًا بلا تحكم واضح.</p>`
        },
        {
          title: "لا تنسَ الوكيل العكسي",
          code: `app.UseForwardedHeaders(new ForwardedHeadersOptions
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor
        | ForwardedHeaders.XForwardedProto
});`,
          lang: "csharp",
          body: `<p>خلف Nginx أو load balancer، يرى Kestrel عنوان الوكيل وبروتوكول HTTP الداخلي. <code>ForwardedHeaders</code> يقرأ <code>X-Forwarded-For/Proto</code> ليصحّح <code>RemoteIpAddress</code> والـ scheme. لا تثق بهذه الترويسات من الإنترنت مباشرة؛ اضبط KnownProxies أو KnownNetworks وإلا يستطيع عميل تزوير IP. هذا الإعداد يجب أن يكون قبل أي Middleware يعتمد على العنوان أو HTTPS.</p>`
        }
      ],
      compare: {
        intro: `<p>في .NET Framework كان التطبيق يُستضاف داخل IIS عبر <code>System.Web</code>. اليوم التطبيق مضيف بنفسه، وIIS إن وُجد يصبح Proxy. الفرق يغيّر شكل النشر والتشخيص.</p>`,
        before: {
          label: "استضافة IIS",
          lang: "xml",
          title: "web.config",
          code: `<configuration>
  <system.webServer>
    <handlers>
      <add name="aspNetCore" path="*" verb="*"
           modules="AspNetCoreModuleV2" />
    </handlers>
    <aspNetCore processPath="dotnet"
                arguments=".\\Souq.Api.dll"
                stdoutLogEnabled="true" />
  </system.webServer>
</configuration>`,
          points: [
            "مرتبط بـ Windows وIIS.",
            "إعداد النشر موزّع بين web.config وIIS Manager.",
            "التشخيص يعتمد على سجلات IIS.",
          ],
        },
        after: {
          label: "Kestrel مباشرة أو خلف Proxy",
          lang: "json",
          title: "appsettings.json",
          code: `{
  "Kestrel": {
    "Endpoints": {
      "Http": { "Url": "http://0.0.0.0:8080" }
    },
    "Limits": {
      "MaxRequestBodySize": 10485760,
      "MaxRequestHeadersTotalSize": 32768,
      "RequestHeadersTimeout": "00:00:30",
      "KeepAliveTimeout": "00:02:00"
    },
    "AddServerHeader": false
  }
}`,
          points: [
            "يعمل على أي نظام.",
            "الإعداد جزء من الكود ويمكن مراجعته.",
            "جاهز للحاويات والـ Reverse Proxy.",
          ],
        },
        verdict: `<p>الانتقال إلى Kestrel لا يعني «لا نحتاج Proxy». يعني أن التطبيق لم يعد رهينة خادم واحد. يمكنك تشغيله على Linux في حاوية، ووضعه خلف Nginx أو Cloud Load Balancer، وتشخيصه من سجلات موحّدة.</p>`,
      },
      internals: `
        <p>دورة الطلب داخل Kestrel تقريبًا:</p>
        <ol>
          <li><strong>Accept loop</strong>: خيط يستقبل الاتصالات من Socket ويوزّعها.</li>
          <li><strong>Connection middleware</strong>: يقرأ البايتات، يفكّ ترميز HTTP، ويطبّق حدود الحجم والزمن.</li>
          <li><strong>HttpContext</strong>: ينشئ كائنًا لكل طلب مع Request/Response/Features.</li>
          <li><strong>Pipeline</strong>: يمرّر الطلب إلى <code>RequestDelegate</code> النهائي.</li>
          <li><strong>Response</strong>: يكتب الهيدرات والجسم، وقد يضغطها إن فُعّل الضغط.</li>
        </ol>
        <p>Kestrel يستخدم <strong>System.IO.Pipelines</strong> و<code>MemoryPool</code> لتقليل نسخ البيانات وتخصيص الذاكرة. هذا سبب كونه من أسرع خوادم HTTP في فئته. لكن الأداء لا يعني الأمان: بلا حدود، يمكن لطلب ضخم أن يستهلك الذاكرة أو يجمّد الاتصال.</p>
        <p>عند العمل خلف Proxy، تأتي الهيدرات <code>X-Forwarded-For</code> و<code>X-Forwarded-Proto</code>. بدون معالجتها، يرى تطبيقك أن كل الطلبات من عنوان الـ Proxy، فتفشل سياسات تحديد المعدل وسجلات التدقيق وروابط إعادة التوجيه. فعّل <code>UseForwardedHeaders</code> واضبط الشبكات الموثوقة فقط — لا تثق بأي Proxy عشوائي.</p>
      `,
      internalsTable: {
        head: ["الحد", "الافتراضي", "متى تغيّره؟"],
        rows: [
          ["MaxRequestBodySize", "30 MB", "رفع ملفات كبير أو تقييد أشد"],
          ["MaxRequestHeadersTotalSize", "32 KB", "توكنات/كوكيز ضخمة"],
          ["RequestHeadersTimeout", "30 ثانية", "حماية من Slowloris"],
          ["KeepAliveTimeout", "130 ثانية", "توازن بين زمن الاتصال والموارد"],
        ],
      },
      tips: [
        {
          title: "لا تنشر Kestrel عاريًا على الإنترنت",
          body: "استخدم Proxy أو Load Balancer يتولى TLS والتحديد. إن اضطررت، فعّل HTTPS مع شهادة صحيحة وHSTS، وقيّد المنافذ.",
        },
        {
          title: "استمع على 0.0.0.0 في الحاويات",
          body: "الاستماع على <code>localhost</code> داخل الحاوية يعني أن الخارج لا يستطيع الوصول. استخدم <code>http://+:8080</code> أو <code>ASPNETCORE_URLS</code>.",
        },
        {
          title: "اضبط ForwardedHeaders",
          body: "بدونها تفقد IP العميل وHTTPS الأصلي. اضبط <code>KnownProxies</code> أو <code>KnownNetworks</code>، ولا تمسح القائمة كاملة في الإنتاج.",
        },
        {
          title: "راقب 413 و429",
          body: "الاستجابات 413 (Payload Too Large) و429 (Too Many Requests) ليست أخطاء عشوائية؛ غالبًا حدود خادم أو Proxy. راجع سجلات الاثنين معًا.",
        },
      ],
      quiz: [
        {
          q: "ما موقع Kestrel في ASP.NET Core؟",
          options: [
            "مكتبة JSON فقط.",
            "خادم HTTP المدمج الذي يستقبل الاتصالات ويمرّرها إلى خط الأنابيب.",
            "أداة نشر إلى IIS.",
            "بديل عن Dependency Injection.",
          ],
          answer: 1,
          explain:
            "Kestrel هو خادم HTTP الافتراضي والمدمج. ينشئ HttpContext لكل طلب ويمرّره إلى الـ pipeline.",
        },
        {
          q: "لماذا نضع Nginx أمام Kestrel في الإنتاج؟",
          options: [
            "لأن Kestrel لا يدعم HTTP.",
            "للتولّي عن TLS والضغط والتحديد والتوزيع، مع إبقاء التطبيق بسيطًا.",
            "لأن Kestrel أبطأ من IIS دائمًا.",
            "لأن .NET لا يعمل على Linux.",
          ],
          answer: 1,
          explain:
            "الفصل بين مسؤوليات الخادم والتطبيق ممارسة إنتاجية شائعة. Kestrel يستطيع العمل مباشرة، لكن Proxy يوفّر طبقة تشغيل ناضجة.",
        },
        {
          q: "ماذا تفعل عند رؤية IP الـ Proxy بدل IP العميل؟",
          options: [
            "تعطّل السجلات.",
            "تستخدم UseForwardedHeaders مع إعداد الشبكات الموثوقة.",
            "تغيّر منفذ Kestrel.",
            "تحذف X-Forwarded-For يدويًا.",
          ],
          answer: 1,
          explain:
            "ForwardedHeaders middleware يقرأ هيدرات الـ Proxy ويحدّث Connection.RemoteIpAddress وScheme، بشرط الثقة بالـ Proxy فقط.",
        },
      ],
      capstone: {
        title: "ضبط Kestrel لـ Souq.NET",
        goal: "نجهّز خادم المشروع لبيئة حاوية: منفذ ثابت، حدود واضحة، وإخفاء هوية الخادم، مع استعداد لـ Proxy لاحقًا.",
        tasks: [
          "أضف قسم <code>Kestrel</code> في appsettings.json بمنفذ <code>8080</code> وحدود طلب 10MB.",
          "أخفِ هيدر <code>Server</code> عبر <code>AddServerHeader = false</code>.",
          "أضف <code>UseForwardedHeaders</code> في Program.cs مع تعليق يوضح ضرورة ضبط الـ Proxy الموثوق.",
          "شغّل التطبيق وتحقق من عدم ظهور هيدر Server في الاستجابة.",
          "اختبر إرسال body أكبر من الحد وتأكد من استجابة 413.",
        ],
        code: {
          lang: "csharp",
          title: "ضبط الخادم برمجيًا",
          code: `builder.WebHost.ConfigureKestrel(options =>
{
    options.AddServerHeader = false;
    options.Limits.MaxRequestBodySize = 10 * 1024 * 1024;
    options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);
});

builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders =
        ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
    // في الإنتاج: اضبط KnownProxies/KnownNetworks بدقة.
});

var app = builder.Build();
app.UseForwardedHeaders();`,
        },
      },
    },
  ],
});
