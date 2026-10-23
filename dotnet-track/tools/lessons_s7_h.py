# -*- coding: utf-8 -*-
"""Stage 7 module 2 (part H): s7-m2-l5 (البيانات الشخصية: تشفير وحذف وتدقيق)."""

TODAY = "2026-10-22"

_L5 = {
    "id": "s7-m2-l5",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الدرس ده مختلف عن الباقي: **المتطلبات جاية من القانون مش من المعمارية**، وبتأثر على تصميم الجداول والـAPI والنسخ الاحتياطي — يعني لازم تعرفها **قبل** ما تبني. وإحنا في وقت حساس تحديدًا: القانون المصري **151/2020** فضل خمس سنين بلا لائحة تنفيذية، واللائحة صدرت بالقرار الوزاري **816 لسنة 2025** واتنفذت في نوفمبر 2025، والمادة 6 من قانون الإصدار بتدي **سنة لتوفيق الأوضاع** — يعني الموعد النهائي **نهاية أكتوبر/أول نوفمبر 2026**. لو منتجك بيتعامل مع بيانات أشخاص في مصر، ده مش بند «بعدين». ولو بتبيع لعملاء في الاتحاد الأوروبي، فـGDPR بينطبق عليك كمان. هنا: خريطة بيانات · **تشفير حقلي بـAesGcm** مع blind index للبحث · **حق الحذف والتصدير** بكود · مشكلة **النسخ الاحتياطي** وحلها بـcrypto-shredding · سجل معالجة البيانات · وخطوات امتثال عملية. **تنبيه**: ده درس هندسي — التفاصيل القانونية محتاجة مراجعة مع مختص."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "بيانات شخصية", "def": "أي بيانات بتسمح بالتعرف على شخص طبيعي مباشرة أو غير مباشرة: اسم · هاتف · بريد · عنوان IP · رقم قومي · معرّف جهاز · موقع. **المعرّف الداخلي (user_id) بيانات شخصية** لأنه قابل للربط."},
            {"term": "بيانات حساسة/فئات خاصة", "def": "بيانات تتطلب حماية أعلى: صحة · دين/معتقدات · رأي سياسي · بيانات حيوية (بصمة) · أطفال · بيانات جنائية · (وفي القانون المصري: البيانات المالية في بعض السياقات). معالجتها بتحتاج أساسًا قانونيًا أقوى."},
            {"term": "المتحكم (Controller)", "def": "الجهة اللي بتقرر **لماذا وكيف** تُعالج البيانات. عليها أغلب الالتزامات (الأساس القانوني · حقوق الأفراد · الإخطار · السجل). لو أنت بتبني منتجك، فأنت متحكم."},
            {"term": "المعالج (Processor)", "def": "الجهة اللي بتعالج البيانات **نيابة عن** المتحكم (مزود سحابة · خدمة بريد · تحليلات). محتاج عقد معالجة (GDPR مادة 28) وتعليمات مكتوبة."},
            {"term": "أساس المعالجة (Lawful basis)", "def": "السبب القانوني المسموح به للمعالجة: **موافقة** · تنفيذ عقد · التزام قانوني · مصلحة حيوية · مصلحة عامة · **مصلحة مشروعة** (مع اختبار توازن). لازم تحدده **قبل** الجمع وتوثقه."},
            {"term": "حق الحذف/الإلغاء", "def": "حق الفرد يطلب محو بياناته (GDPR مادة 17 «حق النسيان» · وفي القانون المصري حق إلغاء/محو). مش مطلق: فيه استثناءات (التزام قانوني · مطالبات قضائية · مصلحة عامة)."},
            {"term": "حق النقل (Portability)", "def": "تصدير بيانات الشخص بصيغة **مقروءة آليًا وشائعة** (JSON/CSV) — البيانات اللي هو قدمها أو اللي اتولدت من نشاطه (مادة 20)."},
            {"term": "إخفاء الهوية مقابل إزالة الهوية", "def": "**إخفاء الهوية (Anonymization)**: يستحيل إعادة التعرف → **خارج نطاق القانون**. **إزالة الهوية (Pseudonymization)**: تستبدل المعرّف بمفتاح قابل للربط → **لسه بيانات شخصية** بس حماية أعلى (مادة 32)."},
            {"term": "Crypto-shredding", "def": "تشفير بيانات كل شخص **بمفتاح خاص به** (DEK)، ولما يطلب الحذف → **احذف المفتاح** فالبيانات بقت غير قابلة للفك، حتى في النسخ الاحتياطية. الحل العملي لمشكلة «النسخ ما بتتنسيش»."},
            {"term": "Blind index", "def": "عمود إضافي فيه HMAC حتمي للقيمة المشفرة، يسمح بالبحث عن **المساواة** (`WHERE email_blind = HMAC(?)`) من غير فك التشفير. بيتشاف منه المساواة فقط، مش الأنماط."},
            {"term": "سجل المعالجة (RoPA)", "def": "**Records of Processing Activities** (مادة 30): سجل لكل غرض معالجة: البيانات · الأساس · المدة · المستلمون · النقل خارج الحدود · الإجراءات الأمنية. ده أول مستند بيطلبه أي مدقق."},
            {"term": "مسؤول حماية البيانات (DPO)", "def": "دور مطلوب في حالات معينة (معالجة واسعة/منتظمة · فئات خاصة · جهة عامة). في مصر القانون بيفرض تعيين مسؤول حماية بيانات مسجل في حالات محددة وعدم التعيين له غرامة."},
            {"term": "تقييم أثر الحماية (DPIA)", "def": "**Data Protection Impact Assessment** (مادة 35): تقييم إلزامي قبل معالجة عالية الخطر (تتبع واسع · فئات خاصة · قرارات آلية مؤثرة). ناتجه: مخاطر + إجراءات."},
            {"term": "الاحتفاظ بالحد الأدنى", "def": "ما تخزنش أكتر مما تحتاج، ولا أطول مما تحتاج (مادة 5(1)(e) «تحديد التخزين»). عمليًا: **جدول مدد احتفاظ** + مهمة حذف مجدولة."},
            {"term": "الخصوصية بالتصميم", "def": "**Privacy by design & by default** (مادة 25): الحماية جزء من التصميم مش إضافة — أقل بيانات · أقصر مدة · إخفاء افتراضي · تشفير افتراضي."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① الإطار القانوني — ومواعيد 2026"},
        {"type": "table", "caption": "مصر: قانون حماية البيانات الشخصية 151/2020 — الوضع في أكتوبر 2026",
         "head": ["البند", "التفاصيل", "الأثر الهندسي عليك"],
         "rows": [
             ["القانون", "**رقم 151 لسنة 2020** — صدر في 15 يوليو 2020 وبدأ العمل به في أكتوبر 2020", "مبادئ وحقوق والتزامات عامة منذ 2020"],
             ["اللائحة التنفيذية", "**القرار الوزاري 816 لسنة 2025** — نُشرت في الجريدة الرسمية ودخلت حيز النفاذ في نوفمبر 2025", "التفاصيل التنفيذية (إجراءات/تراخيص/إخطارات) بقت محددة"],
             ["فترة توفيق الأوضاع", "المادة 6 من قانون الإصدار: **سنة من تاريخ صدور اللائحة** → تنتهي **نهاية أكتوبر/أول نوفمبر 2026**", "**الموعد ده بعد أيام** — لو متأخر، ابدأ بخريطة البيانات والأسس القانونية (أقل مجهود بأعلى أثر)"],
             ["الجهة الرقابية", "**مركز حماية البيانات الشخصية** (تابع وزارة الاتصالات) + بوابة إلكترونية للتراخيص والتصاريح", "احتمال تحتاج **ترخيص/تصريح** كنشاط معالجة — راجع مع مستشار قبل ما تبني مسار نقل بيانات"],
             ["الجزاءات", "غرامات إدارية (ملخصات منشورة: من ~200 ألف إلى ~5 ملايين جنيه) · وعدم تعيين مسؤول حماية بيانات مسجل له غرامة (ملخصات: ~200 ألف إلى ~2 مليون)", "التكلفة مش بس مالية: السمعة والثقة. الحماية أرخص بكتير من المخالفة"],
             ["الاختصاص القضائي", "**المحاكم الاقتصادية** تختص بالجرائم المخالفة للقانون (المادة 5 من قانون الإصدار)", "أي نزاع بيروح لمسار قضائي متخصص — جهّز سجلاتك كدليل"],
             ["الإخطار عند الخرق", "التزام إخطار المركز وصاحب البيانات عند الخرق (التفاصيل في القانون واللائحة)", "خطة الاستجابة (7.2.3) + سجل تدقيق (7.2.3) = القدرة على تحديد الأثر والإخطار بدقة"],
         ]},
        {"type": "table", "caption": "مقارنة سريعة: GDPR (الاتحاد الأوروبي) مقابل القانون المصري — لأغراض التصميم",
         "head": ["الموضوع", "GDPR", "القانون المصري 151/2020 + اللائحة", "ملاحظة تصميم"],
         "rows": [
             ["النطاق خارج الإقليم", "ينطبق لو بتعرض سلع/خدمات لأشخاص في الاتحاد أو بتراقب سلوكهم", "ينطبق على المعالجة المرتبطة بمقيمين في الجمهورية (وحالات أخرى في النص)", "صمم كأن الأشد بينطبق — أرخص من نظامين"],
             ["الأساس القانوني", "6 أسس (مادة 6)", "موافقة + حالات محددة في القانون واللائحة", "جدول أساس المعالجة في خريطة البيانات (أسفل)"],
             ["حق الحذف", "مادة 17 — بدون تأخير غير مبرر، وعمليًا خلال شهر (قابل للتمديد شهرين)", "حق إلغاء/محو مع التزام المحو فور انتهاء الغرض وإخطار صاحب البيانات (ملخصات: خلال 30 يومًا للطلبات عبر الإنترنت)", "صمم **مسار حذف قابل للتنفيذ خلال أيام** مش أسابيع"],
             ["حق النقل", "مادة 20 — صيغة مقروءة آليًا", "حق الاطلاع/الحصول على البيانات لدى المتحكم", "export endpoint موحد (JSON) يخدم الاتنين"],
             ["إخطار الخرق", "72 ساعة للجهة الرقابية (مادة 33) + الأفراد لو خطر عالٍ (مادة 34)", "إخطار المركز وصاحب البيانات حسب القانون واللائحة", "خطة 7.2.3 + قدرة تحديد الأثر من سجل التدقيق"],
             ["سجل المعالجة", "مادة 30 (RoPA) — إلزامي فوق 250 موظفًا أو عند معالجة منتظمة/حساسة", "التزامات توثيق ومسك سجلات في القانون واللائحة", "احتفظ بـRoPA دائمًا — هو أول مستند في أي تدقيق"],
             ["مسؤول حماية البيانات", "مادة 37 في حالات محددة", "**تعيين مسؤول حماية بيانات مسجل** مطلوب في حالات محددة مع غرامة على عدم التعيين", "حدد مين المسؤول داخليًا حتى لو ما كانش «DPO» رسمي"],
             ["النقل عبر الحدود", "كفاية/ضمانات (SCCs) — الفصل الخامس", "**ترخيص/تصريح** لنقل البيانات الشخصية خارج مصر (حسب اللائحة)", "لو بتخزن في سحابة خارج مصر → ده بند جوهري، راجعه قانونيًا **قبل** اختيار المنطقة"],
             ["العقوبات", "حتى 4% من الإيراد العالمي أو 20 مليون يورو", "غرامات مالية + جزاءات في القانون واللائحة", "المخاطرة المالية مش أكبر بند — فقدان ثقة العملاء أكبر"],
         ]},
        {"type": "callout", "kind": "danger", "title": "حدود هذا الدرس (مهم)",
         "md": "**ده درس هندسي، مش استشارة قانونية.** الأرقام والمواعيد أعلاه مجمعة من نصوص منشورة وملخصات قانونية، وفيها تفاصيل بتتغير (خصوصًا بعد نفاذ اللائحة 816/2025 وبدء عمل مركز حماية البيانات الشخصية).\n\nالقاعدة العملية: **ابنِ النظام بحيث يقدر يثبت الامتثال**، وخلي المحامي/المختص يحدد المتطلبات:\n• خريطة بيانات + أساس معالجة لكل غرض (تقدر تعملها النهاردة).\n• مسار حذف/تصدير قابل للتنفيذ خلال أيام (تقدر تبنيه النهاردة).\n• تشفير في النقل والتخزين + سجل تدقيق (تقدر تبنيه النهاردة).\n• سجل معالجة + سياسة احتفاظ + خطة خرق (تقدر تكتبها النهاردة).\n• الترخيص/التصريح والنقل عبر الحدود وتعيين مسؤول حماية البيانات (**محتاجة مختص**)."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② خريطة البيانات: أول مستند لازم تعمله"},
        {"type": "text", "md": "من غير خريطة بيانات، كل حاجة بعد كده تخمين: ما تعرفش تحذف (مش عارف البيانات فين)، ولا تثبت أساس المعالجة، ولا تحسب أثر خرق. الخريطة دي **بتتعمل في ساعة** وبتوفّر أسابيع. ابدأ من قاعدة البيانات (الجداول والأعمدة) ومن عقود الـAPI (اللي بيتبعت لجوه وبره)، ومن اللوجنج (أكتر مكان بيتسرب فيه بيانات)."},
        {"type": "code", "lang": "text", "title": "docs/data-inventory.md — خريطة بيانات shop (نموذج مملوء)", "filename": "docs/data-inventory.md", "code": r'''# خريطة البيانات الشخصية — shop
> آخر تحديث: 2026-10-22 · المالك: سارة · المراجعة: كل ربع سنة أو مع أي تغيير في الجمع
> التصنيف: PII = بيانات شخصية · S-PII = حساسة · NON = غير شخصية

## 1) الجداول والأعمدة
| الجدول | العمود | التصنيف | مثال | أساس المعالجة | مدة الاحتفاظ | تشفير | طريقة الحذف | يظهر أين؟ |
|---|---|---|---|---|---|---|---|---|
| customers | full_name | PII | «منى إبراهيم» | تنفيذ عقد | مدة الحساب + 5 سنوات (فوترة) | ❌ (يُبحث به) | مسح القيمة + tombstone | API/Dashboard |
| customers | email | PII | mona@example.com | تنفيذ عقد + موافقة للتسويق | مدة الحساب + 3 سنوات | ✅ حقلي + blind index | مسح + حذف DEK | API/رسائل |
| customers | phone | PII | 01012345678 | تنفيذ عقد (توصيل) | مدة الحساب + سنة | ✅ حقلي | مسح + حذف DEK | API/SMS |
| customers | national_id | **S-PII** | 29xxxxxxx12 | التزام قانوني (فوترة ضريبية) | 6 سنوات (قانوني) | ✅ حقلي + KMS | **لا يُحذف قبل انتهاء المدة القانونية** → إخفاء هوية بعدها | الفوترة فقط |
| customers | marketing_consent | NON (لكن يحكم معالجة) | true | موافقة | حتى السحب + سجل إثبات | ❌ | احتفظ بسجل السحب | — |
| addresses | address_line | PII | «12 ش التحرير، الدقي» | تنفيذ عقد | مدة الحساب + سنة | ❌ | مسح | API/توصيل |
| addresses | geo_point | PII (موقع) | 30.04,31.23 | موافقة (تتبع) | 30 يومًا (ثم تجميع) | ❌ | **حذف تلقائي بعد 30 يومًا** | خرائط التوصيل |
| orders | customer_id | PII (معرّف قابل للربط) | 7f3a… | تنفيذ عقد | 6 سنوات (فوترة/ضرائب) | ❌ | إخفاء هوية (pseudonymize) بعد المدة | API/تقارير |
| orders | notes | PII (قد يحوي بيانات حساسة عرضًا) | «اتصل بعد المغرب» | تنفيذ عقد | سنة | ✅ حقلي | مسح | API |
| payments | card_last4 | PII | 4242 | تنفيذ عقد | 6 سنوات | ❌ (آخر 4 فقط) | احتفاظ قانوني | API/فواتير |
| payments | card_token | NON (token لدى المزود) | tok_1a2b | تنفيذ عقد | 6 سنوات | ❌ | — | — |
| audit_entries | actor_id, source_ip | PII | sub=… / 41.x.x.x | مصلحة مشروعة (أمن) | 12 شهرًا | ❌ | **إخفاء هوية بعد المدة** (لا حذف: دليل قانوني) | الأمن |
| log_store | رسائل السجلات | PII عرضًا | هاتف/بريد في نص رسالة | مصلحة مشروعة (تشغيل) | 30 يومًا | ❌ | **الإخفاء قبل الكتابة** (7.1.3) + انتهاء الاحتفاظ | Seq/Loki |

## 2) أين تخرج البيانات من سيطرتنا (مستلمون/معالجون)
| المستلم | الغرض | ما يُرسل | الأساس/العقد | خارج الحدود؟ |
|---|---|---|---|---|
| مزود الدفع | تنفيذ عملية | مبلغ + معرّف طلب + بطاقة (مباشرة للمزود، لا تمر علينا) | عقد معالج | ✅ (تحقق: ترخيص/ضمانات) |
| مزود SMS/بريد | إشعارات | هاتف/بريد + قالب | عقد معالج | ✅/❌ حسب المزود |
| مزود السحابة (Azure) | استضافة | كل ما سبق | عقد معالج + منطقة محددة | اختر **منطقة** عن قصد |
| مراقبة (Grafana Cloud مثلًا) | مقاييس/سجلات | سجلات مُخفاة | عقد معالج | ✅ → **لا ترسل PII** |

## 3) ما الذي لا نجمعه (قرار مكتوب)
- لا نجمع بيانات حيوية (بصمة/وجه).
- لا نجمع الموقع المستمر — فقط عنوان التوصيل + نقطة جغرافية تُحذف بعد 30 يومًا.
- لا نحتفظ بأرقام البطاقات كاملة أبدًا (tokenization لدى المزود).
- لا ننسخ إنتاجًا لبيئات الاختبار — بيانات وهمية بـBogus فقط (1.2.6).

## 4) الفجوات الحالية (بملّاك وتواريخ)
| # | الفجوة | الإجراء | المالك | التاريخ |
|---|---|---|---|---|
| 1 | `phone` مشفر في جدول قديم | migration بـexpand/contract (3.3.4) | كريم | 2026-11-10 |
| 2 | لا يوجد مسار حذف آلي لـgeo_point | مهمة حذف مجدولة (2.2.10) | منى | 2026-11-05 |
| 3 | السجلات فيها أرقام هواتف | تفعيل `PiiRedactionEnricher` (7.1.3) | منى | 2026-10-30 |
| 4 | لا يوجد سجل معالجة (RoPA) | كتابة `docs/ropa.md` | سارة | 2026-11-20 |
'''},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ التشفير: في النقل، في التخزين، وعلى مستوى الحقل"},
        {"type": "table", "caption": "أربع طبقات تشفير — كل واحدة بتحل مشكلة مختلفة",
         "head": ["الطبقة", "بتحمي من", "الأداة في مشروعنا", "الحد (ما تحميش من)"],
         "rows": [
             ["**في النقل (TLS)**", "التنصت/الوسيط على الشبكة", "TLS 1.2+ في الـingress · HTTPS إجباري + HSTS (7.2.3) · TLS داخلي للطوابير والـDB", "ما يحميش من اختراق التطبيق أو سرقة البيانات من القرص"],
             ["**في التخزين (على مستوى القرص/الخدمة)**", "سرقة القرص · وصول غير مصرح للتخزين", "Azure Disk/Storage encryption · SQL Server TDE · PostgreSQL على تخزين مشفر", "ما يحميش من استعلام غير مصرح به عبر التطبيق (المفتاح متاح للخدمة)"],
             ["**على مستوى الحقل (تطبيق)**", "قراءة عمود كامل لو اتسربت قاعدة/نسخة احتياطية · تقليل أثر IDOR", "`FieldEncryption` بـAesGcm + DEK لكل سجل/مستخدم (أسفل) · أو Data Protection API", "ما يحميش من تسرب عبر الـAPI نفسه · بيمنع البحث بـLIKE/الترتيب"],
             ["**المفاتيح (KMS/Key Vault)**", "سرقة المفاتيح · صعوبة التدوير", "Key Vault/KMS مع Managed Identity (6.2.3) · KEK في HSM · تدوير مجدول", "ما يحميش من صلاحية واسعة على الـvault نفسه (7.2.3)"],
         ]},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Infrastructure/Security/FieldEncryption.cs — تشفير حقلي بـAesGcm + blind index", "filename": "src/Orders.Infrastructure/Security/FieldEncryption.cs", "code": r'''using System.Buffers.Text;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Caching.Memory;

namespace Shop.Infrastructure.Security;

/// <summary>
/// تشفير حقلي بنمط المغلّف (envelope):
///   DEK (مفتاح لكل نطاق — مثلًا لكل عميل) ← يُغلَّف بـKEK من Key Vault.
///   الناتج المخزّن: base64( nonce(12) || ciphertext || tag(16) )
/// القواعد:
///   • AesGcm في .NET 8+ يتطلب تحديد حجم الـtag في الباني (الباني القديم obsolete: SYSLIB0053).
///   • nonce عشوائي جديد لكل عملية تشفير — إعادة استخدامه تدمّر أمان GCM بالكامل.
///   • الحذف = حذف الـDEK (crypto-shredding) فيصبح المحتوى غير قابل للفك.
/// </summary>
public interface IFieldEncryptor
{
    string Encrypt(string plaintext, KeyPurpose purpose);
    string Decrypt(string stored, KeyPurpose purpose);
    string BlindIndex(string plaintext, KeyPurpose purpose);
}

/// <summary>يفصل الأغراض حتى لا يعمل توكن من غرض في غرض آخر (purpose separation).</summary>
public enum KeyPurpose
{
    CustomerContact = 1,
    OrderNotes = 2,
    PaymentReference = 3,
}

public sealed class FieldEncryptor(IKeyProvider keys, ILogger<FieldEncryptor> logger) : IFieldEncryptor
{
    private const int NonceSize = 12;   // AES-GCM: 96 بت
    private const int TagSize = 16;     // 128 بت

    public string Encrypt(string plaintext, KeyPurpose purpose)
    {
        ArgumentException.ThrowIfNullOrEmpty(plaintext);
        var dek = keys.GetDataKey(purpose);   // 32 بايت (AES-256) — من الكاش المحلي بعد فك الغلاف
        var plainBytes = Encoding.UTF8.GetBytes(plaintext);
        var output = new byte[NonceSize + plainBytes.Length + TagSize];

        var nonce = output.AsSpan(0, NonceSize);
        var cipher = output.AsSpan(NonceSize, plainBytes.Length);
        var tag = output.AsSpan(NonceSize + plainBytes.Length, TagSize);
        RandomNumberGenerator.Fill(nonce);    // nonce جديد لكل تشفير

        using var aes = new AesGcm(dek, TagSize);
        aes.Encrypt(plainBytes, cipher, tag, nonce);

        return Base64.EncodeToString(output);
    }

    public string Decrypt(string stored, KeyPurpose purpose)
    {
        ArgumentException.ThrowIfNullOrEmpty(stored);
        var buffer = Base64.DecodeFromChars(stored.AsSpan());
        if (buffer.Length < NonceSize + TagSize)
        {
            // لا تكشف تفاصيل: سجل الحدث كاشتباه عبث وأرجع خطأ عامًا
            logger.LogWarning("قيمة مشفرة أقصر من الحد الأدنى — احتمال عبث أو مفتاح خاطئ");
            throw new CryptographicException("قيمة غير صالحة");
        }

        var dek = keys.GetDataKey(purpose);
        var nonce = buffer.AsSpan(0, NonceSize);
        var cipher = buffer.AsSpan(NonceSize, buffer.Length - NonceSize - TagSize);
        var tag = buffer.AsSpan(buffer.Length - TagSize, TagSize);
        var plain = new byte[cipher.Length];

        using var aes = new AesGcm(dek, TagSize);
        aes.Decrypt(nonce, cipher, tag, plain);   // يرمي CryptographicException لو العبث/المفتاح غلط
        return Encoding.UTF8.GetString(plain);
    }

    /// <summary>
    /// فهرس أعمى: HMAC حتمي يسمح بالبحث عن المساواة فقط.
    /// مفتاح منفصل عن مفتاح التشفير (عشان تسرب واحد ما يكشفش الاتنين).
    /// </summary>
    public string BlindIndex(string plaintext, KeyPurpose purpose)
    {
        var key = keys.GetBlindIndexKey(purpose);
        // تطبيع: trim + lower + إزالة المسافات — عشان «Mona@X.com » و«mona@x.com» يتطابقوا
        var normalized = plaintext.Trim().ToLowerInvariant();
        var hash = HMACSHA256.HashData(key, Encoding.UTF8.GetBytes(normalized));
        return Convert.ToHexString(hash);
    }
}

/// <summary>يوفر الـDEK (مغلَّفًا بـKEK من Key Vault) ومفتاح الـblind index.</summary>
public interface IKeyProvider
{
    byte[] GetDataKey(KeyPurpose purpose);
    byte[] GetBlindIndexKey(KeyPurpose purpose);
}

/// <summary>
/// تطبيق عملي: KEK في Key Vault (6.2.3)، والـDEK يُغلَّف/يُفك بـWrapKey/UnwrapKey.
/// في الإنتاج خُزّن الـDEK المغلَّف جنب الصف (أو لكل عميل) واحذفه عند طلب الحذف.
/// </summary>
public sealed class KeyVaultKeyProvider(
    Azure.Security.KeyVault.Keys.Cryptography.CryptographyClient crypto,
    Azure.Security.KeyVault.Secrets.SecretClient secrets,
    IMemoryCache cache,
    ILogger<KeyVaultKeyProvider> logger) : IKeyProvider
{
    public byte[] GetDataKey(KeyPurpose purpose)
        => cache.GetOrCreate($"dek:{purpose}", _ => LoadSecret($"dek-{purpose.ToString().ToLowerInvariant()}"))!;

    public byte[] GetBlindIndexKey(KeyPurpose purpose)
        => cache.GetOrCreate($"bik:{purpose}", _ => LoadSecret($"blindindex-{purpose.ToString().ToLowerInvariant()}"))!;

    private byte[] LoadSecret(string name)
    {
        var value = secrets.GetSecret(name).Value.Value;
        var key = Convert.FromHexString(value);
        if (key.Length != 32)
        {
            logger.LogError("طول المفتاح {Name} ليس 32 بايت", name);
            throw new InvalidOperationException("مفتاح غير صالح");
        }

        return key;
    }

    // مثال لفك غلاف DEK مخزّن (يُستخدم لو خزّنت DEKs مغلّفة لكل سجل):
    public byte[] Unwrap(byte[] wrappedDek)
        => crypto.UnwrapKey(
               Azure.Security.KeyVault.Keys.Cryptography.KeyWrapAlgorithm.RsaOaep256,
               wrappedDek)
           .Value.Key;   // Response<UnwrapResult>.Value.Key
}
'''},
        {"type": "code", "lang": "csharp", "title": "EncryptedStringConverter + تسجيل في EF Core (تشفير شفاف للكود)", "filename": "src/Orders.Infrastructure/Persistence/EncryptedStringConverter.cs", "code": r'''using Microsoft.EntityFrameworkCore.Storage.ValueConversion;
using Shop.Infrastructure.Security;

namespace Shop.Infrastructure.Persistence;

/// <summary>
/// يشفّر/يفك تلقائيًا عند القراءة والكتابة. الميزة: كود التطبيق يشتغل بـstring عادي.
/// التحذير: لا تستخدم العمود المشفر في WHERE/LIKE/ORDER BY — استخدم blind index.
/// </summary>
public sealed class EncryptedStringConverter(IFieldEncryptor encryptor, KeyPurpose purpose)
    : ValueConverter<string, string>(
        v => encryptor.Encrypt(v, purpose),
        v => encryptor.Decrypt(v, purpose));

public static class EncryptedPropertyExtensions
{
    /// <summary>
    /// يطبّق التشفير على عمود + يضيف blind index للبحث بالمساواة.
    /// الاستدعاء في OnModelCreating أو IEntityTypeConfiguration.
    /// </summary>
    public static Microsoft.EntityFrameworkCore.Metadata.Builders.PropertyBuilder<string>
        IsEncrypted(
            this Microsoft.EntityFrameworkCore.Metadata.Builders.PropertyBuilder<string> builder,
            IFieldEncryptor encryptor,
            KeyPurpose purpose,
            int maxLength = 1024)
    {
        // قيمة عشوائية (nonce) معناها الطول يتغير: احجز مساحة كافية
        builder.HasConversion(new EncryptedStringConverter(encryptor, purpose))
               .HasMaxLength(maxLength);
        return builder;
    }
}

// ── مثال الاستخدام في الكيان والتكوين ──────────────────────────────────
public sealed class Customer
{
    public Guid Id { get; set; }
    public string FullName { get; set; } = "";      // يُبحث به → غير مشفر (قرار موثق)
    public string Email { get; set; } = "";          // مشفر
    public string EmailBlindIndex { get; set; } = ""; // للبحث بالمساواة (فهرس فريد)
    public string? Phone { get; set; }               // مشفر
    public string? PhoneBlindIndex { get; set; }     // للبحث (اختياري حسب الحاجة)
    public string? MarketingConsentAt { get; set; }  // ISO 8601 — إثبات الموافقة
    public bool Erased { get; set; }                 // tombstone بعد الحذف
    public DateTimeOffset? ErasedAtUtc { get; set; }
    public Guid DataKeyRef { get; set; }             // مرجع الـDEK — يُحذف لتنفيذ crypto-shredding
}

public sealed class CustomerConfiguration(IFieldEncryptor encryptor)
    : Microsoft.EntityFrameworkCore.IEntityTypeConfiguration<Customer>
{
    public void Configure(
        Microsoft.EntityFrameworkCore.Metadata.Builders.EntityTypeBuilder<Customer> b)
    {
        b.ToTable("customers");
        b.HasKey(x => x.Id);

        b.Property(x => x.Email).IsEncrypted(encryptor, KeyPurpose.CustomerContact, maxLength: 1024);
        b.Property(x => x.Phone).IsEncrypted(encryptor, KeyPurpose.CustomerContact, maxLength: 1024);

        // فهرس فريد على العمود الأعمى — يمنع التكرار ويسمح بالبحث
        b.HasIndex(x => x.EmailBlindIndex).IsUnique();
        b.HasIndex(x => x.PhoneBlindIndex);

        b.Property(x => x.FullName).HasMaxLength(200);
    }
}
'''},
        {"type": "callout", "kind": "warn", "title": "ست مقايضات لازم تعرفها قبل التشفير الحقلي",
         "md": "**① البحث بيتغير**: مش هتقدر تعمل `LIKE '%mona%'` أو ترتيب على عمود مشفر. الحلول: blind index للمساواة · أو خزن أجزاء قابلة للبحث (آخر 4 أرقام) · أو ابحث في خدمة خارجية مؤمّنة.\n**② الطول بيتغير**: القيمة المشفرة أطول (nonce+tag+base64) → `HasMaxLength` كافي وإلا هتتفاجأ بـ`String or binary data would be truncated`.\n**③ الفهرس الفريد على النص المشفر بلا قيمة** (كل تشفير مختلف بسبب الـnonce) → الفهرس الفريد يكون على **blind index**.\n**④ الأداء**: فك التشفير لكل صف في قائمة كبيرة مكلف → شفّر الحقول الحساسة فقط، مش كل الجدول.\n**⑤ التدوير**: لو دوّرت المفتاح، لازم تعيد تشفير البيانات — صمم بحيث الـDEK **لكل سجل/مستخدم** (تدوير رخيص) مش مفتاح واحد لكل حاجة.\n**⑥ الـbackup**: التشفير بيحمي النسخة، بس لو المفتاح في نفس النسخة فمفيش فايدة — **المفاتيح في Key Vault/KMS منفصل** (6.2.3)."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ حق الحذف والتصدير — بكود"},
        {"type": "text", "md": "الحذف أصعب مما يبدو لأن البيانات **بتعيش في أكتر من مكان**: الجدول الأساسي · الكاش · الطابور · السجلات · فهرس البحث · النسخ الاحتياطي · عند معالج خارجي (مزود بريد). الحل العملي: **مسار حذف واحد بيجمع كل المخازن** + **crypto-shredding للنسخ الاحتياطي** + **tombstone** يثبت إن الحذف حصل (من غير ما يحتفظ بالبيانات)."},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Api/Endpoints/PersonalDataEndpoints.cs — تصدير + طلب حذف", "filename": "src/Orders.Api/Endpoints/PersonalDataEndpoints.cs", "code": r'''using System.Security.Claims;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc;

namespace Shop.Api.Endpoints;

/// <summary>
/// مساران: التصدير (حق النقل/الاطلاع) وطلب الحذف (حق المحو).
/// القواعد:
///   • المصادقة إلزامية: المستخدم يشوف بياناته هو فقط (لا تمرر userId من المدخلات).
///   • rate limit على التصدير (بيانات كثيرة + تكلفة) — انظر 2.2.5.
///   • كل طلب يُدقَّق (7.2.3) — لأنه وصول لبيانات شخصية بالجملة.
///   • الحذف غير متزامن: نؤكد الاستلام، وننفذ في مهمة خلفية، ونسجل الإثبات.
/// </summary>
public static class PersonalDataEndpoints
{
    public static void MapPersonalData(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/me")
            .RequireAuthorization()
            .RequireRateLimiting("personal-data");

        // ── التصدير: صيغة مقروءة آليًا (JSON) ─────────────────────────
        group.MapGet("/export", async (
            IPersonalDataExporter exporter,
            ClaimsPrincipal user,
            HttpContext http,
            CancellationToken ct) =>
        {
            var subjectId = user.GetSubjectId();     // من التوكن، لا من المدخلات
            var payload = await exporter.ExportAsync(subjectId, ct);

            // يُدقَّق: من · متى · حجم البيانات · السبب (7.2.3)
            http.Items["Audit.Reason"] = "data-subject-export";

            return Results.File(
                JsonSerializer.SerializeToUtf8Bytes(payload, ExportJson.Options),
                contentType: "application/json",
                fileDownloadName: $"my-data-{DateTime.UtcNow:yyyyMMdd}.json");
        })
        .WithName("ExportPersonalData")
        .WithSummary("تصدير بياناتي الشخصية بصيغة JSON");

        // ── الحذف: نؤكد الاستلام وننفذ خلفيًا ─────────────────────────
        group.MapPost("/erasure", async (
            [FromBody] ErasureRequest request,
            IErasureService erasure,
            ClaimsPrincipal user,
            HttpContext http,
            CancellationToken ct) =>
        {
            var subjectId = user.GetSubjectId();

            // منع الإرسال المزدوج (idempotency — 5.2.5)
            var existing = await erasure.FindOpenRequestAsync(subjectId, ct);
            if (existing is not null)
            {
                return Results.Ok(new { status = "already_received", reference = existing.Reference });
            }

            var result = await erasure.EnqueueAsync(
                subjectId,
                request.Reason ?? "data-subject-request",
                ct);

            http.Items["Audit.Reason"] = "data-subject-erasure-request";

            // 202 Accepted: الطلب اتسجل والتنفيذ جارٍ (قد يستغرق دقائق)
            return Results.Accepted($"/me/erasure/{result.Reference}", new
            {
                reference = result.Reference,
                receivedAtUtc = result.ReceivedAtUtc,
                // التزام زمني واضح — لا تكتب «في أقرب وقت»
                targetCompletionUtc = result.ReceivedAtUtc.AddDays(7),
                note = "سنخطرك على البريد المسجل عند الاكتمال. قد نحتفظ ببيانات محددة لالتزام قانوني مع إخفاء هويتك.",
            });
        })
        .WithName("RequestErasure")
        .WithSummary("طلب محو بياناتي الشخصية");

        // ── حالة الطلب: إثبات التنفيذ (لك وللجهة الرقابية) ───────────
        group.MapGet("/erasure/{reference}", async (
            string reference,
            IErasureService erasure,
            ClaimsPrincipal user,
            CancellationToken ct) =>
        {
            var status = await erasure.GetStatusAsync(reference, user.GetSubjectId(), ct);
            return status is null ? Results.NotFound() : Results.Ok(status);
        })
        .WithName("GetErasureStatus");
    }

    private static string GetSubjectId(this ClaimsPrincipal user)
        => user.FindFirst("sub")?.Value
           ?? throw new UnauthorizedAccessException("معرّف المستخدم غير موجود في التوكن");
}

public sealed record ErasureRequest(string? Reason);

public static class ExportJson
{
    public static readonly JsonSerializerOptions Options = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };
}
'''},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Infrastructure/Privacy/ErasureService.cs — جمع كل المخازن + إثبات", "filename": "src/Orders.Infrastructure/Privacy/ErasureService.cs", "code": r'''using Microsoft.EntityFrameworkCore;

namespace Shop.Infrastructure.Privacy;

/// <summary>
/// ينفذ الحذف عبر كل المخازن بالترتيب، ويسجل إثباتًا (بدون الاحتفاظ بالبيانات نفسها).
/// الاستراتيجية:
///   1) tombstone + إخفاء هوية في النظام الأساسي (يُبقى مرجعًا للالتزام القانوني).
///   2) حذف من المشتقات (كاش · فهرس بحث · طابور · جلسات).
///   3) crypto-shredding: حذف/إبطال مفتاح البيانات → النسخ الاحتياطية تبقى غير قابلة للفك.
///   4) إخطار المعالجين الخارجيين (بريد/SMS/تحليلات) بمحو البيانات لديهم.
/// </summary>
public interface IErasureService
{
    Task<ErasureReceipt> EnqueueAsync(string subjectId, string reason, CancellationToken ct);
    Task<ErasureReceipt?> FindOpenRequestAsync(string subjectId, CancellationToken ct);
    Task<ErasureStatus?> GetStatusAsync(string reference, string subjectId, CancellationToken ct);
    Task ExecuteAsync(string reference, CancellationToken ct);
}

public sealed record ErasureReceipt(string Reference, DateTimeOffset ReceivedAtUtc);

public sealed record ErasureStatus(
    string Reference,
    string State,                       // received | in_progress | completed | partially_failed
    DateTimeOffset ReceivedAtUtc,
    DateTimeOffset? CompletedAtUtc,
    IReadOnlyList<StoreResult> Stores,
    string? FailureNote);

public sealed record StoreResult(string Store, string Action, string Outcome);

public sealed class ErasureService(
    ShopDbContext db,
    IKeyStore keyStore,
    IDerivedStoreCleaner cleaner,
    IProcessorNotifier notifier,
    IAuditWriter audit,
    ILogger<ErasureService> logger) : IErasureService
{
    public async Task<ErasureReceipt> EnqueueAsync(string subjectId, string reason, CancellationToken ct)
    {
        var reference = $"ER-{DateTime.UtcNow:yyyyMMdd}-{Guid.NewGuid().ToString("N")[..8]}";
        db.ErasureRequests.Add(new ErasureRequestEntity
        {
            Reference = reference,
            SubjectId = subjectId,       // يُخفى بعد الاكتمال (لا يبقى قابلًا للربط)
            Reason = reason,
            State = "received",
            ReceivedAtUtc = DateTimeOffset.UtcNow,
        });
        await db.SaveChangesAsync(ct);

        await audit.WriteAsync("Erasure.Requested", subjectId, reference, ct);
        // النشر في طابور للتنفيذ غير المتزامن (5.2.1) — لا تنفذ في نفس الطلب
        await cleaner.PublishAsync("privacy.erasure.requested",
            new { reference, subjectId }, ct);

        return new ErasureReceipt(reference, DateTimeOffset.UtcNow);
    }

    public async Task<ErasureReceipt?> FindOpenRequestAsync(string subjectId, CancellationToken ct)
    {
        var row = await db.ErasureRequests
            .AsNoTracking()
            .Where(r => r.SubjectId == subjectId && r.State != "completed")
            .OrderByDescending(r => r.ReceivedAtUtc)
            .FirstOrDefaultAsync(ct);

        return row is null ? null : new ErasureReceipt(row.Reference, row.ReceivedAtUtc);
    }

    public async Task<ErasureStatus?> GetStatusAsync(string reference, string subjectId, CancellationToken ct)
    {
        var row = await db.ErasureRequests.AsNoTracking()
            .FirstOrDefaultAsync(r => r.Reference == reference && r.SubjectId == subjectId, ct);
        if (row is null) return null;

        return new ErasureStatus(
            row.Reference, row.State, row.ReceivedAtUtc, row.CompletedAtUtc,
            row.StoreResults.Select(s => new StoreResult(s.Store, s.Action, s.Outcome)).ToList(),
            row.FailureNote);
    }

    public async Task ExecuteAsync(string reference, CancellationToken ct)
    {
        var row = await db.ErasureRequests.FirstOrDefaultAsync(r => r.Reference == reference, ct)
                  ?? throw new InvalidOperationException("طلب غير موجود");

        row.State = "in_progress";
        await db.SaveChangesAsync(ct);

        var results = new List<StoreResult>();
        var failures = new List<string>();

        async Task Step(string store, string action, Func<Task> work)
        {
            try
            {
                await work();
                results.Add(new StoreResult(store, action, "done"));
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "فشل الحذف في {Store}", store);
                results.Add(new StoreResult(store, action, "failed"));
                failures.Add(store);
            }
        }

        // 1) النظام الأساسي: إخفاء القيم (لا حذف الصف: الالتزام القانوني يحتاج الإثبات)
        await Step("postgres:customers", "anonymize", async () =>
        {
            // ExecuteUpdateAsync (3.3.4): تحديث جماعي بدون تحميل الكيانات
            await db.Customers
                .Where(c => c.Id == row.SubjectGuid)
                .ExecuteUpdateAsync(s => s
                    .SetProperty(c => c.Email, "erased@invalid.local")
                    .SetProperty(c => c.Phone, (string?)null)
                    .SetProperty(c => c.FullName, "ERASED")
                    .SetProperty(c => c.EmailBlindIndex, $"erased-{row.Reference}")
                    .SetProperty(c => c.PhoneBlindIndex, (string?)null)
                    .SetProperty(c => c.Erased, true)
                    .SetProperty(c => c.ErasedAtUtc, DateTimeOffset.UtcNow)
                    .SetProperty(c => c.DataKeyRef, Guid.Empty), ct);
        });

        // 2) المشتقات: كاش · فهرس بحث · جلسات · طوابير · توكنات
        await Step("redis", "delete-keys", () => cleaner.ClearCacheAsync(row.SubjectId, ct));
        await Step("search-index", "delete-docs", () => cleaner.DeleteFromSearchAsync(row.SubjectId, ct));
        await Step("sessions/tokens", "revoke", () => cleaner.RevokeSessionsAsync(row.SubjectId, ct));
        await Step("queue/dlq", "purge-messages", () => cleaner.PurgeQueuedMessagesAsync(row.SubjectId, ct));

        // 3) crypto-shredding: إبطال المفتاح → أي نسخة احتياطية تصبح غير قابلة للفك
        await Step("key-store", "revoke-data-key", () => keyStore.RevokeAsync(row.SubjectGuid, ct));

        // 4) المعالجون الخارجيون: إخطار بالمحو (عقد المعالجة بيلزمهم)
        await Step("processors", "notify", () => notifier.NotifyErasureAsync(row.SubjectId, ct));

        // 5) السجلات: لا تُحذف (دليل تشغيلي/قانوني) لكن تُخفى هويتها
        await Step("audit/logs", "pseudonymize", () => cleaner.PseudonymizeLogsAsync(row.SubjectId, ct));

        row.StoreResults = results
            .Select(r => new StoreResultEntity { Store = r.Store, Action = r.Action, Outcome = r.Outcome })
            .ToList();
        row.FailureNote = failures.Count == 0 ? null : string.Join(",", failures);
        row.State = failures.Count == 0 ? "completed" : "partially_failed";
        row.CompletedAtUtc = DateTimeOffset.UtcNow;

        // إخفاء هوية مرجع الطلب نفسه بعد الاكتمال (يبقى الإثبات، يزول الربط)
        row.SubjectId = $"erased-{row.Reference}";

        await db.SaveChangesAsync(ct);
        await audit.WriteAsync(row.State == "completed" ? "Erasure.Completed" : "Erasure.PartialFailure",
            row.SubjectId, reference, ct);

        if (failures.Count > 0)
        {
            // تنبيه: الحذف التزام قانوني — الفشل يحتاج تدخلًا بشريًا سريعًا
            await cleaner.PublishAsync("privacy.erasure.failed", new { reference, failures }, ct);
        }
    }
}

/// <summary>الواجهات اللي بيستخدمها ErasureService (نفّذها لكل مخزن عندك).</summary>
public interface IKeyStore
{
    /// <summary>إبطال مفتاح بيانات المستخدم → crypto-shredding لكل النسخ.</summary>
    Task RevokeAsync(Guid subjectGuid, CancellationToken ct);
}

public interface IDerivedStoreCleaner
{
    Task PublishAsync(string topic, object payload, CancellationToken ct);
    Task ClearCacheAsync(string subjectId, CancellationToken ct);
    Task DeleteFromSearchAsync(string subjectId, CancellationToken ct);
    Task RevokeSessionsAsync(string subjectId, CancellationToken ct);
    Task PurgeQueuedMessagesAsync(string subjectId, CancellationToken ct);
    Task PseudonymizeLogsAsync(string subjectId, CancellationToken ct);
}

/// <summary>إخطار المعالجين الخارجيين (بريد/SMS/تحليلات) بمحو بيانات الشخص لديهم.</summary>
public interface IProcessorNotifier
{
    Task NotifyErasureAsync(string subjectId, CancellationToken ct);
}

/// <summary>كتابة صف في سجل التدقيق (7.2.3) لأحداث الخصوصية.</summary>
public interface IAuditWriter
{
    Task WriteAsync(string action, string actorOrSubject, string detail, CancellationToken ct);
}

public sealed class ErasureRequestEntity
{
    public Guid Id { get; set; }
    public string Reference { get; set; } = "";
    public string SubjectId { get; set; } = "";
    public Guid SubjectGuid { get; set; }
    public string Reason { get; set; } = "";
    public string State { get; set; } = "received";
    public DateTimeOffset ReceivedAtUtc { get; set; }
    public DateTimeOffset? CompletedAtUtc { get; set; }
    public string? FailureNote { get; set; }
    public List<StoreResultEntity> StoreResults { get; set; } = [];
}

public sealed class StoreResultEntity
{
    public Guid Id { get; set; }
    public string Store { get; set; } = "";
    public string Action { get; set; } = "";
    public string Outcome { get; set; } = "";
}
'''},
        {"type": "table", "caption": "أين تعيش البيانات الشخصية — وطريقة الحذف في كل مكان (جدول لا غنى عنه)",
         "head": ["المكان", "طريقة الحذف", "التحدي", "الحل العملي"],
         "rows": [
             ["قاعدة البيانات الأساسية", "`ExecuteUpdateAsync` لإخفاء القيم أو `ExecuteDeleteAsync` للحذف", "قيود FK + الالتزام القانوني بالاحتفاظ (فوترة)", "tombstone + إخفاء هوية + جدول مدد احتفاظ"],
             ["الكاش (Redis/HybridCache)", "حذف المفاتيح المرتبطة بالمستخدم", "المفاتيح مش دايما فيها معرّف المستخدم", "اتفاقية تسمية مفاتيح (`cust:{id}:…`) + فهرس مفاتيح"],
             ["الطوابير والـDLQ", "تصفية/حذف الرسائل أو تركها تنتهي بالـTTL", "الرسائل بتُستهلك وتُكتب في مكان تاني", "TTL قصير + لا تضع PII في حمولة الأحداث (استخدم معرّفات)"],
             ["السجلات المركزية", "**لا تُحذف** — تُخفى هويتها", "السجلات دليل تشغيلي وقانوني", "إخفاء PII **قبل الكتابة** (7.1.3) + احتفاظ 30 يومًا + استبدال المعرّف"],
             ["فهرس البحث (Elastic/OpenSearch)", "حذف المستندات بمعرّف المستخدم", "التزامن مع القاعدة", "مستمع لحدث الحذف + إعادة بناء الفهرس دوريًا"],
             ["النسخ الاحتياطية", "**crypto-shredding**: إبطال المفتاح", "النسخ غير قابلة للتعديل (WORM) وقد تحتفظ بها لشهور", "DEK لكل سجل/مستخدم + توثيق السياسة: «النسخ تفقد قابلية الفك عند إبطال المفتاح»"],
             ["تقارير/مستودع بيانات (BI)", "إعادة بناء من مصدر مُخفى الهوية", "بيانات مجمعة بتحتوي معرّفات", "aggregation بدون معرّفات + جدول مدد"],
             ["المعالجون الخارجيون (بريد/SMS/تحليلات)", "إخطار بمحو البيانات لديهم", "مش بتتحكم في تنفيذهم", "عقد معالجة (مادة 28/اللائحة) + بند محو + سجل الإخطارات"],
             ["بريد العميل/إشعارات مرسلة", "ما تقدرش تستردها", "خرجت من سيطرتك", "قلّل ما تُرسل (خصوصية بالتصميم) + وثّق في الخريطة"],
         ]},
        {"type": "callout", "kind": "note", "title": "الاستثناءات: ما الذي يُحتفظ به رغم طلب الحذف؟",
         "md": "حق الحذف **مش مطلق**. الحالات المعتادة للاحتفاظ (مع إخفاء الهوية قدر الإمكان):\n\n• **التزام قانوني**: فواتير وسجلات ضريبية (عادةً 5–6 سنوات) · سجلات المعاملات المالية.\n• **مطالبات قانونية**: بيانات لازمة لدفاع في نزاع قائم أو محتمل (مثل سجل تدقيق عملية مشكوك فيها).\n• **المصلحة العامة/الصحة**: حالات نادرة ومحددة.\n• **أمن النظام**: سجل التدقيق الأمني — يُحتفظ به **مُخفى الهوية** (استبدال الـactor_id بقيمة غير قابلة للربط بعد انتهاء المدة).\n\nالقاعدة الهندسية: **احتفظ بأقل ما يلزم، مخفي الهوية، مع أساس قانوني مكتوب لكل بند** — وسجّل القرار في `docs/data-inventory.md`. ولو احتفظت ببيانات تعرف الشخص بيها بلا أساس، فأنت في مخالفة حتى بعد «الحذف»."},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ الاحتفاظ والتدقيق: مهمة حذف تلقائية + سجل معالجة"},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Infrastructure/Privacy/RetentionWorker.cs — حذف تلقائي منسيّ الصلاحية", "filename": "src/Orders.Infrastructure/Privacy/RetentionWorker.cs", "code": r'''using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Shop.Infrastructure.Privacy;

public sealed record RetentionOptions(
    int GeoPointsDays = 30,          // موقع: يُحذف بعد 30 يومًا ثم يُجمَّع
    int LogsDays = 30,
    int AuditPseudonymizeAfterDays = 365,   // إخفاء هوية سجل التدقيق بعد سنة
    int BatchSize = 500,
    int DelaySeconds = 3600);

/// <summary>
/// الاحتفاظ بالحد الأدنى يُنفَّذ بمهمة مجدولة، لا بيد بشرية.
/// القواعد: دفعات صغيرة (لا تقفل الجدول) · عدّاد للحذف (يُدقَّق) · فشل آمن (أعد المحاولة).
/// </summary>
public sealed class RetentionWorker(
    IServiceScopeFactory scopes,
    IOptions<RetentionOptions> options,
    IAuditWriter audit,
    ILogger<RetentionWorker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // إزاحة عشوائية بسيطة لتجنب تزامن النسخ (2.2.10)
        await Task.Delay(TimeSpan.FromSeconds(Random.Shared.Next(30, 120)), stoppingToken);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var db = scope.ServiceProvider.GetRequiredService<ShopDbContext>();
                var o = options.Value;

                // 1) موقع جغرافي منتهي الصلاحية — حذف فعلي
                var geoCutoff = DateTimeOffset.UtcNow.AddDays(-o.GeoPointsDays);
                // دفعة محدودة: نختار المعرّفات أولًا ثم نحذف بها — أضمن عبر المزودات
                var geoIds = await db.AddressGeoPoints
                    .Where(g => g.CapturedAtUtc < geoCutoff)
                    .OrderBy(g => g.Id)
                    .Take(o.BatchSize)
                    .Select(g => g.Id)
                    .ToListAsync(stoppingToken);
                var deletedGeo = geoIds.Count == 0
                    ? 0
                    : await db.AddressGeoPoints
                        .Where(g => geoIds.Contains(g.Id))
                        .ExecuteDeleteAsync(stoppingToken);

                // 2) إخفاء هوية سجل التدقيق القديم (لا حذف: دليل قانوني)
                var auditCutoff = DateTimeOffset.UtcNow.AddDays(-o.AuditPseudonymizeAfterDays);
                // AuditEntries = جدول التدقيق من 7.2.3 (Shop.Infrastructure.Audit)
                var auditIds = await db.AuditEntries
                    .Where(a => a.OccurredAtUtc < auditCutoff && a.ActorId != null)
                    .OrderBy(a => a.Id)
                    .Take(o.BatchSize)
                    .Select(a => a.Id)
                    .ToListAsync(stoppingToken);
                var pseudonymized = auditIds.Count == 0
                    ? 0
                    : await db.AuditEntries
                        .Where(a => auditIds.Contains(a.Id))
                        .ExecuteUpdateAsync(s => s
                            .SetProperty(a => a.ActorId, "pseudonymized")
                            .SetProperty(a => a.SourceIp, (string?)null), stoppingToken);

                if (deletedGeo > 0 || pseudonymized > 0)
                {
                    logger.LogInformation("احتفاظ: حُذف {Geo} نقطة موقع، وأُخفيت هوية {Audit} صف تدقيق",
                        deletedGeo, pseudonymized);
                    await audit.WriteAsync("Retention.Applied", "system",
                        $"geo={deletedGeo};audit={pseudonymized}", stoppingToken);
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;   // إيقاف نظيف (6.1.5)
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "فشل دورة الاحتفاظ — ستُعاد المحاولة");
            }

            await Task.Delay(TimeSpan.FromSeconds(options.Value.DelaySeconds), stoppingToken);
        }
    }
}
'''},
        {"type": "code", "lang": "text", "title": "docs/ropa.md — سجل معالجة البيانات (أول مستند يطلبه أي مدقق)", "filename": "docs/ropa.md", "code": r'''# سجل أنشطة المعالجة (RoPA) — shop
> المتحكم: <اسم الشركة> · عنوان: <...> · مسؤول حماية البيانات: <اسم/بريد>
> آخر تحديث: 2026-10-22 · المراجعة: كل ربع سنة + مع أي غرض معالجة جديد

## غرض 1: تنفيذ الطلبات والتوصيل
- **البيانات**: اسم · عنوان · هاتف · بريد · تفاصيل الطلب · موقع لحظة التوصيل
- **الأساس القانوني**: تنفيذ عقد
- **الفئات**: عملاء مسجلون وضيفون
- **المصدر**: من المستخدم مباشرة
- **الاحتفاظ**: مدة الحساب + 6 سنوات للفواتير (التزام ضريبي) · الموقع 30 يومًا
- **المستلمون**: مزود توصيل (معالج) · مزود دفع (متحكم مستقل)
- **نقل عبر الحدود**: ✅ مزود الدفع — <الضمانات/التصريح: يُراجع قانونيًا>
- **إجراءات الحماية**: TLS · تشفير حقلي للهاتف والبريد · أقل صلاحيات · سجل تدقيق · نسخ مشفرة
- **حقوق الفرد**: اطلاع · تصحيح · محو (مع استثناء الفوترة) · نقل · اعتراض على التسويق

## غرض 2: التسويق بالبريد/الرسائل
- **البيانات**: بريد · هاتف · سجل تفضيلات
- **الأساس القانوني**: **موافقة صريحة** (تُسحب في أي وقت)
- **الاحتفاظ**: حتى السحب + 3 سنوات إثباتًا للموافقة/السحب
- **إثبات الموافقة**: `marketing_consent_at` + سجل تدقيق لحدث الموافقة/السحب + نص السياسة المعروض
- **المستلمون**: مزود بريد (معالج بعقد)
- **ملاحظة هندسية**: رابط إلغاء اشتراك في كل رسالة · سحب فوري من قوائم الإرسال · لا تعتمد على «سيُنفذ قريبًا»

## غرض 3: الأمن ومنع الاحتيال
- **البيانات**: IP · User-Agent · سجل تدقيق · محاولات دخول · معرّفات جلسات
- **الأساس القانوني**: مصلحة مشروعة (اختبار توازن موثق: ضروري لحماية الخدمة ولا يطغى على حقوق الفرد)
- **الاحتفاظ**: 12 شهرًا ثم إخفاء هوية
- **المستلمون**: داخلي (فريق الأمن) · مزود مراقبة (معالج — **بلا PII**)
- **إجراءات الحماية**: إخفاء PII قبل الكتابة للسجلات (7.1.3) · وصول مقيد · تنبيهات (7.1.5)

## غرض 4: التحسين والتحليلات
- **البيانات**: أحداث استخدام **مجمعة ومجهولة الهوية** (بلا معرّفات فردية)
- **الأساس القانوني**: مصلحة مشروعة / موافقة (لو أدوات تتبع)
- **الضمان**: تجميع قبل التخزين · لا ربط بين الجلسات · حذف المعرّفات في نقطة الالتقاط

## ما لا نعالجه (قرار موثق)
- بيانات حيوية · فئات خاصة (صحة/دين/سياسة) · بيانات أطفال تحت <سن> بلا موافقة ولي الأمر ·
  قرارات آلية مؤثرة قانونيًا بدون تدخل بشري

## سجل التغييرات
| التاريخ | التغيير | من |
|---|---|---|
| 2026-10-22 | إنشاء السجل | سارة |
'''},

        # ───────────────────────────────────────────── ⑥
        {"type": "heading", "level": 2, "text": "⑥ خطة الامتثال: سبع خطوات تبدأ النهاردة"},
        {"type": "steps", "title": "من الصفر إلى قدرة إثبات الامتثال", "items": [
            {"title": "اعمل خريطة البيانات (يوم واحد)",
             "md": "امشِ على الجداول + عقود الـAPI + السجلات + المستلمين الخارجيين. صنف كل حقل: PII/S-PII/NON + أساس المعالجة + مدة الاحتفاظ + طريقة الحذف. **من غيرها كل خطوة تالية تخمين.** (القالب في `docs/data-inventory.md`.)"},
            {"title": "حدد أساس المعالجة لكل غرض واكتب RoPA (يومان)",
             "md": "لكل غرض: البيانات · الأساس · المدة · المستلمون · النقل عبر الحدود · الحماية. ده أول مستند بيُطلب في أي تدقيق، وبيكشف الأغراض اللي **مالهاش أساس** (أخطر فئة)."},
            {"title": "قلّل الجمع والاحتفاظ (أسبوع)",
             "md": "احذف الحقول اللي مش محتاجها (أرخص إجراء أمني) · قلل المدد · أوقف جمع الموقع المستمر · اجعل التحليلات مجمعة. **أقل بيانات = أقل خطر وأقل تكلفة امتثال.**"},
            {"title": "طبّق الحماية التقنية (أسبوعان)",
             "md": "TLS + HSTS (7.2.3) · تشفير حقلي للحقول الحساسة + blind index · إخفاء PII في السجلات (7.1.3) · أقل صلاحيات على مخازن البيانات · بيانات وهمية في البيئات غير الإنتاجية (Bogus)."},
            {"title": "ابنِ مساري التصدير والحذف (أسبوعان)",
             "md": "`GET /me/export` بصيغة JSON + `POST /me/erasure` غير متزامن بجمع كل المخازن + إثبات التنفيذ + crypto-shredding للنسخ. **اختبرهم فعليًا** على بيانات تجريبية — المسار غير المختبر = غير موجود."},
            {"title": "دقّق وانبّه وأثبت (أسبوع)",
             "md": "سجل تدقيق لكل وصول/تصدير/حذف (7.2.3) + مهمة احتفاظ تلقائية + تنبيه عند فشل الحذف + تقرير ربع سنوي: عدد الطلبات · زمن التنفيذ · الإخفاقات."},
            {"title": "جهّز الجانب القانوني/التنظيمي (بمختص)",
             "md": "سياسة خصوصية منشورة ومفهومة · نموذج موافقة + إثبات · عقود معالجة مع الموردين · **ترخيص/تصريح** لو مطلوب · موقف النقل عبر الحدود · تعيين مسؤول حماية البيانات لو انطبق · خطة إخطار الخرق بمواعيدها · وDPIA لأي معالجة عالية الخطر."},
        ]},
        {"type": "callout", "kind": "tip", "title": "الخصوصية بالتصميم: خمسة قرارات بتوفّر عليك الشغل",
         "md": "**① لا تخزن ما يمكنك اشتقاقه**: العمر من تاريخ الميلاد؟ خزّن التاريخ واحسب العمر — أو العكس حسب ما تحتاجه فعلًا.\n**② لا تجمع ما لا تحتاجه في هذا الغرض**: حقل «الرقم القومي» مطلوب للفوترة فقط → لا تطلبه عند التسجيل.\n**③ استخدم معرّفات بدل البيانات**: الأحداث في الطوابير تحمل `customer_id` مش هاتف/بريد.\n**④ اجعل الإخفاء هو الافتراض**: السجلات والـAPI والتقارير تُخفي تلقائيًا، والكشف استثناء مُسجَّل.\n**⑤ اختبر المسارات الحساسة**: اختبار تكاملي يثبت إن `/me/export` بيرجع بيانات المستخدم الحالي فقط، وإن `/me/erasure` بيمسح من الكاش وفهرس البحث فعلًا."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق بين **بيانات شخصية** و**حساسة**، وأعرف إن المعرّف الداخلي بيانات شخصية (قابل للربط).",
            "أقدر أسمّي أساس المعالجة لكل غرض في نظامي، وأعرف إن الأساس بيتحدد **قبل** الجمع.",
            "أعرف الوضع المصري الحالي: القانون 151/2020 · اللائحة بالقرار 816/2025 نافذة من نوفمبر 2025 · **فترة توفيق الأوضاع سنة → تنتهي نهاية أكتوبر/أول نوفمبر 2026**.",
            "أفرّق بين **إخفاء الهوية** (خارج النطاق) و**إزالة الهوية** (لسه بيانات شخصية).",
            "أعمل خريطة بيانات وجدول مدد احتفاظ، وأعرف المستلمين والمعالجين والنقل عبر الحدود.",
            "أنفّذ تشفيرًا حقليًا بـAesGcm مع nonce عشوائي وtag 16 بايت، وأعرف إن الـctor بلا حجم tag بقى obsolete.",
            "أستخدم **blind index** للبحث بالمساواة على عمود مشفر، وأعرف ليه الفهرس الفريد على النص المشفر بلا قيمة.",
            "أنفّذ مسار حذف يجمع كل المخازن (قاعدة · كاش · طابور · فهرس · سجلات · نسخ · معالجون) مع tombstone وإثبات.",
            "أعرف **crypto-shredding** كحل لمشكلة النسخ الاحتياطية غير القابلة للتعديل.",
            "أعرف الاستثناءات اللي بتسمح بالاحتفاظ رغم طلب الحذف، وإزاي أوثّقها.",
            "أكتب سجل معالجة (RoPA) وأعرف إنه أول مستند في أي تدقيق.",
            "أعرف إن ده درس هندسي وإن التفاصيل القانونية محتاجة مراجعة مع مختص.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة على البيانات الشخصية.",
         "questions": [
             {"q": "مستخدم طلب حذف حسابه، وعندك فاتورة ضريبية لازم تحتفظ بها 6 سنوات. التصرف الصحيح؟",
              "options": ["ترفض الطلب كليًا",
                          "تحذف الحساب وكل شيء بما فيه الفاتورة",
                          "تنفّذ الحذف على كل ما يمكن حذفه، وتحتفظ بالحد الأدنى المطلوب قانونًا مخفي الهوية قدر الإمكان مع توثيق الأساس",
                          "تؤجل الطلب 6 سنوات"],
              "answer": 2,
              "explain": "حق الحذف مش مطلق: الالتزام القانوني استثناء. بس الاستثناء **محدود بأقل ما يلزم** — تحتفظ ببيانات الفاتورة فقط، تخفي هوية الباقي، وتوثّق الأساس والمدة في خريطة البيانات وسجل المعالجة. الرفض الكلي أو التأجيل لسنوات مخالف."},
             {"q": "ليه التشفير الحقلي وحده ما يحلش مشكلة النسخ الاحتياطية؟",
              "options": ["لأن النسخ لا تُشفّر",
                          "لأن النسخ غالبًا غير قابلة للتعديل (WORM) وقد تبقى شهورًا، فالمفتاح وحده هو نقطة التحكم → crypto-shredding",
                          "لأن التشفير بطيء",
                          "لأن النسخ تُحذف تلقائيًا"],
              "answer": 1,
              "explain": "ما تقدرش تعدّل نسخة احتياطية مغلقة. الحل: مفتاح بيانات **لكل سجل/مستخدم** (DEK)، وعند طلب الحذف تُبطل المفتاح فتصبح البيانات في كل النسخ غير قابلة للفك. ده بيحتاج تصميم مسبق — لو المفتاح واحد لكل الجدول، إبطاله بيكسر كل البيانات."},
             {"q": "عمود `email` مشفر بـAesGcm وعملت عليه فهرس فريد. ما المشكلة؟",
              "options": ["الفهرس يبطئ الكتابة",
                          "لا مشكلة",
                          "الفهرس بلا فائدة: الـnonce العشوائي يجعل نفس البريد يُنتج قيمًا مختلفة، فلا يكشف التكرار — الفهرس الفريد يكون على blind index",
                          "يجب حذف الفهرس لأسباب أمنية"],
              "answer": 2,
              "explain": "AesGcm مع nonce جديد لكل تشفير = نفس النص يُنتج ciphertext مختلف كل مرة (وده مطلوب أمنيًا). للبحث/التفريد استخدم `BlindIndex` (HMAC حتمي بمفتاح منفصل) وخزّنه في عمود إضافي عليه الفهرس."},
             {"q": "أي واحد يُعتبر بيانات شخصية؟",
              "options": ["اسم المستخدم في جدول",
                          "معرّف داخلي `customer_id` مرتبط بجدول فيه الاسم",
                          "عنوان IP في السجلات",
                          "كل ما سبق"],
              "answer": 3,
              "explain": "التعريف: أي بيانات تسمح بالتعرف على شخص **مباشرة أو غير مباشر**. المعرّف الداخلي قابل للربط (فهو بيانات شخصية)، وعنوان IP يعتبر كذلك في أغلب التفسيرات. عشان كده السجلات (7.1.3) محتاجة إخفاء مش «مفيهاش حاجة»."},
             {"q": "الفرق بين إزالة الهوية (pseudonymization) وإخفاء الهوية (anonymization)؟",
              "options": ["لا فرق، الاتنين يخرجان البيانات من النطاق",
                          "إزالة الهوية تستخدم مفتاحًا قابلًا للربط فتبقى البيانات شخصية (حماية أعلى) · الإخفاء يجعل إعادة التعرف مستحيلة فتخرج من النطاق",
                          "الإخفاء يتطلب تشفيرًا أقوى",
                          "إزالة الهوية ممنوعة"],
              "answer": 1,
              "explain": "de-identification بمفتاح (استبدال الاسم بـ`erased-REF`) = pseudonymization: **لسه بيانات شخصية** بس إجراء حماية معترف به (مادة 32). Anonymization الحقيقي (تجميع/إزالة كل ما يسمح بالربط) = خارج النطاق — بس تحقيقه صعب عمليًا (خصوصًا مع بيانات إضافية متاحة)."},
             {"q": "الوضع القانوني في مصر في أكتوبر 2026؟",
              "options": ["القانون 151/2020 مؤجل حتى إشعار آخر",
                          "اللائحة التنفيذية صدرت بالقرار 816/2025 ونُفذت في نوفمبر 2025، وفترة توفيق الأوضاع سنة تنتهي نهاية أكتوبر/أول نوفمبر 2026",
                          "لا توجد لائحة تنفيذية حتى الآن",
                          "القانون ينطبق على الشركات الأجنبية فقط"],
              "answer": 1,
              "explain": "القانون صدر 2020 لكنه فضل بلا تفاصيل تنفيذية لخمس سنين. اللائحة بالقرار الوزاري 816/2025 اتنشرت ونُفذت في نوفمبر 2025، والمادة 6 من قانون الإصدار بتدي سنة لتوفيق الأوضاع. **تحقق دائمًا من النص الحالي مع مختص** — التفاصيل (تراخيص/إخطارات) في اللائحة."},
             {"q": "أفضل مكان لإخفاء البيانات الشخصية من السجلات؟",
              "options": ["بعد الكتابة، بفحص دوري",
                          "قبل الكتابة (destructuring policy + redaction enricher) — لأن ما كُتب يصعب سحبه من كل النسخ والمستهلكين",
                          "في واجهة العرض فقط",
                          "لا داعي: السجلات داخلية"],
              "answer": 1,
              "explain": "السجلات بتتنسخ لمخزن مركزي وبتُقرأ من فرق ومن أدوات تحليل — فأي PII اتكتب اتنشر. الحل في 7.1.3: `PiiDestructuringPolicy` (تسجيل معرّف بدل الكائن) + `PiiRedactionEnricher` (أنماط هاتف/بطاقة/بريد) + السجلات نفسها محمية ومحددة الاحتفاظ."},
             {"q": "في `AesGcm` بـ.NET 10، إيه المطلوب عند الإنشاء؟",
              "options": ["`new AesGcm(key)` عادي",
                          "`new AesGcm(key, tagSizeInBytes)` — الباني بلا حجم tag بقى obsolete (SYSLIB0053)، مع nonce عشوائي جديد لكل تشفير",
                          "استخدام `RijndaelManaged` بدلها",
                          "لا يحتاج مفتاحًا، يستخدم DPAPI تلقائيًا"],
              "answer": 1,
              "explain": "من .NET 8 الباني `AesGcm(byte[])` obsolete ولازم تحدد حجم الـtag (12–16 بايت؛ 16 هو المعتاد). وأخطر خطأ عملي: **إعادة استخدام nonce** مع نفس المفتاح = انهيار أمان GCM. وDPAPI (`ProtectedData`) خاص بـWindows ومش مناسب للحاويات."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "خريطة + تشفير + مسار حذف مُختبر.",
         "items": [
            {"id": "s7-m2-l5-t1",
             "title": "مهمة 1: خريطة بيانات + تشفير حقلي + blind index",
             "md": "على مشروعك: اعمل خريطة بيانات كاملة (كل الجداول + الـAPIs + السجلات + المستلمين)، واختار 2–3 حقول حساسة وشفرها حقليًا بـAesGcm عبر EF Core `ValueConverter`، وأضف blind index للبحث بالمساواة. اكتب migration بـexpand/contract (3.3.4) لنقل البيانات الموجودة.",
             "criteria": [
                 "`docs/data-inventory.md`: **≥ 10 حقول** مصنفة (PII/S-PII/NON) مع أساس المعالجة · مدة الاحتفاظ · التشفير · طريقة الحذف · أين يظهر · من يصل.",
                 "قسم المستلمين/المعالجين مع «خارج الحدود؟» + قسم «ما لا نجمعه» بقرار مكتوب + جدول فجوات بملّاك وتواريخ.",
                 "`IFieldEncryptor` بـAesGcm: nonce 12 بايت عشوائي لكل تشفير · tag 16 بايت · `new AesGcm(key, 16)` · فصل الأغراض (`KeyPurpose`).",
                 "`BlindIndex` بـHMACSHA256 بمفتاح **منفصل** + تطبيع (trim/lower) + فهرس فريد عليه.",
                 "تكوين EF Core (`ValueConverter`) يشفّر وي فك تلقائيًا + `HasMaxLength` كافي للقيمة المشفرة + تعليق يمنع الاستخدام في `LIKE/ORDER BY`.",
                 "**migration بـexpand/contract**: عمود جديد → نسخ/تشفير البيانات → تحقق → تبديل → حذف القديم (مع rollback مكتوب).",
                 "3 اختبارات: roundtrip (تشفير→فك) · قيمة مشفرة مختلفة لنفس النص (nonce عشوائي) · بحث بـblind index يلاقي السجل الصح + قيمة تانية ما تلاقيهوش.",
                 "قرار مكتوب: لماذا شفرّت هذه الحقول دون غيرها (المقايضات: البحث · الأداء · الطول).",
             ],
             "hint": "في الاختبارات، `IKeyProvider` الوهمي بيرجع مفتاح ثابت (32 بايت) — استخدم `Convert.ToHexString` أو `RandomNumberGenerator.GetBytes(32)` ولا تستخدم مفتاح أقصر من 32 بايت وإلا `AesGcm` هيرمي. ولو قاعدة بياناتك SQLite في الاختبارات، الـ`ValueConverter` بيشتغل عادي. للتحويل: اكتب migration يدوي (لا تعتمد على التحويل التلقائي في الـmigration لأن الـconverter محتاج service — نفذ التشفير في كود الـmigration أو في مهمة ترحيل منفصلة على دفعات).",
             "solution": "المشاكل النموذجية: (1) `String or binary data would be truncated` لأن `HasMaxLength(256)` ما يكفيش للقيمة المشفرة (base64 لـ nonce+text+tag) — احسب: `(12 + len + 16) × 4/3` وأضف هامشًا. (2) الفهرس الفريد على العمود المشفر ما بيمسكش التكرار (كل تشفير مختلف) — انقله لـ`EmailBlindIndex`. (3) الكود القديم اللي بيعمل `WHERE email = @x` بينكسر صامتًا (يرجع 0 صفوف) — حوّله لـ`WHERE email_blind_index = @hmac`. (4) في الـmigration: التشفير داخل `Up()` محتاج مفتاح، والمفاتيح مش متاحة وقت الـmigration عادة — الحل الأنضف: أضف العمود الجديد في migration، وشغّل **مهمة ترحيل** (console/worker) تنسخ وتشفر على دفعات، ثم migration تاني يبدّل ويحذف. ده بالظبط نمط expand/contract من 3.3.4. (5) اختبار «قيمة مشفرة مختلفة لنفس النص» بيثبت إن الـnonce عشوائي — لو فشل، فأنت بتعيد استخدام nonce وده ثغرة حرجة.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.security.cryptography.aesgcm",
                 "https://learn.microsoft.com/dotnet/standard/security/",
                 "https://learn.microsoft.com/ef/core/modeling/value-conversions",
                 "https://learn.microsoft.com/azure/key-vault/general/overview",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html",
             ]},
            {"id": "s7-m2-l5-t2",
             "title": "مهمة 2: مسار تصدير + حذف مُختبر + احتفاظ تلقائي + RoPA",
             "md": "نفّذ `GET /me/export` و`POST /me/erasure` (غير متزامن بجمع كل المخازن + إثبات) + `RetentionWorker` + `docs/ropa.md`. واختبر المسارين باختبارات تكامل حقيقية (WebApplicationFactory + Testcontainers) تثبت إن البيانات اختفت من الكاش والطابور وفهرس البحث مش من القاعدة بس.",
             "criteria": [
                 "`GET /me/export`: JSON بصيغة مفهومة · **بيانات المستخدم الحالي فقط** (معرّف من التوكن مش من المدخلات) · rate-limited · مُدقَّق (سجل تدقيق بحجم البيانات).",
                 "`POST /me/erasure`: يرجع 202 بمرجع · idempotent (طلب مكرر ما ينشئش طلبًا جديدًا) · تنفيذ غير متزامن عبر طابور · حالة قابلة للاستعلام (`/me/erasure/{ref}`).",
                 "التنفيذ يغطي **≥ 6 مخازن**: القاعدة (tombstone/إخفاء) · الكاش · الطابور/DLQ · فهرس البحث · الجلسات/التوكنات · سجلات (إخفاء هوية) · إخطار المعالجين.",
                 "**crypto-shredding**: `IKeyStore.RevokeAsync` يُبطل مفتاح بيانات المستخدم + اختبار يثبت إن فك التشفير بعد الإبطال بيرمي (مش بيرجع قيمة).",
                 "سجل إثبات لكل طلب: المرجع · الحالة · نتائج كل مخزن · وقت الاكتمال · الإخفاقات — مع إخفاء هوية `SubjectId` بعد الاكتمال.",
                 "**تنبيه عند الفشل**: لو مخزن فشل، الحالة `partially_failed` + رسالة في الطابور/تنبيه (الحذف التزام، والفشل يحتاج تدخلًا).",
                 "`RetentionWorker`: حذف/إخفاء هوية لدفعات محدودة · عدّاد يُدقَّق · توقف نظيف عند الإلغاء · إزاحة عشوائية ضد التزامن.",
                 "**4 اختبارات تكامل**: تصدير يرجع بياناتي فقط (مستخدم تاني ما يشوفهاش) · حذف يمسح من الكاش/الطابور/الفهرس · فك التشفير يفشل بعد إبطال المفتاح · الطلب المكرر يرجع نفس المرجع.",
                 "`docs/ropa.md` بـ**≥ 3 أغراض معالجة**: لكل غرض البيانات · الأساس · المدة · المستلمون · النقل عبر الحدود · الحماية · حقوق الفرد — + قسم «ما لا نعالجه».",
             ],
             "hint": "في الاختبارات: استخدم `Testcontainers` (1.2.5) مع Redis container للكاش وحاوية طابور (RabbitMQ) — وإلا الاختبار بيثبت الحاجة السهلة (القاعدة) بس. لفهرس البحث لو ما عندكش واحد، اعمل واجهة `IDerivedStoreCleaner` بـfake يسجل الاستدعاءات واثبت إنه اتنادى بالمعرّف الصح. ولـcrypto-shredding: `IKeyStore` الوهمي يحتفظ بقاموس مفاتيح و`RevokeAsync` بيحذف المفتاح، فاختبار فك التشفير بعده لازم يرمي `CryptographicException` (أو `KeyNotFoundException` لو صممت كده — بس حدد التوقع ووثقه). وخلي بالك: إخفاء هوية سجلات التدقيق لازم ما يكسرش إثبات الحذف — احتفظ بالمرجع (`ER-…`) واحذف الربط بالمستخدم.",
             "solution": "النتائج النموذجية: أول تنفيذ بيغطي القاعدة والكاش وينسى **الطابور وفهرس البحث** — وده بيظهر في الاختبار التكاملي (لو كتبته صح). ثاني اكتشاف: الحذف المتزامن داخل الطلب بياخد ثواني وبيفشل مع أي تبعية بطيئة، فالتنفيذ غير المتزامن (طابور + حالة) مش رفاهية. ثالث اكتشاف: `SubjectId` في سجل الإثبات نفسه بيانات شخصية — والحل إنك تحتفظ بالمرجع وتُخفي الهوية بعد الاكتمال (زي ما في الكود). رابعًا: أغلب الفرق بتكتشف إن عندها بيانات شخصية في **السجلات والنسخ والتقارير** أكتر من القاعدة — فمسار الحذف الحقيقي أطول مما يتوقع، وخريطة البيانات (المهمة 1) هي اللي بتخليه قابل للاكتشاف. وأهم مخرَج غير تقني: **زمن التنفيذ** — لو الطلب بياخد أكتر من أيام، فأنت محتاج أتمتة أكتر أو مخازن أقل.",
             "resources": [
                 "https://learn.microsoft.com/aspnet/core/security/gdpr",
                 "https://learn.microsoft.com/dotnet/standard/security/",
                 "https://learn.microsoft.com/ef/core/what-is-new/ef-core-7.0/whatsnew#executeupdate-and-executedelete-bulk-updates",
                 "https://cheatsheetseries.owasp.org/cheatsheets/Choosing_and_Using_Security_Questions_Cheat_Sheet.html",
                 "https://commission.europa.eu/law/law-topic/data-protection_en",
                 "https://gdpr.eu/what-is-gdpr/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Microsoft Learn: دعم GDPR في ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/security/gdpr"},
            {"label": "Microsoft Learn: الأمان في .NET (التشفير)", "url": "https://learn.microsoft.com/dotnet/standard/security/"},
            {"label": "OWASP: Cryptographic Storage Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"},
            {"label": "OWASP: Logging Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html"},
            {"label": "المفوضية الأوروبية: حماية البيانات (GDPR)", "url": "https://commission.europa.eu/law/law-topic/data-protection_en"},
            {"label": "Azure Key Vault: نظرة عامة", "url": "https://learn.microsoft.com/azure/key-vault/general/overview"},
            {"label": "EF Core: تحويلات القيم (Value Converters)", "url": "https://learn.microsoft.com/ef/core/modeling/value-conversions"},
            {"label": "LINDDUN: منهجية تهديدات الخصوصية", "url": "https://linddun.org/"},
        ]},
        {"type": "callout", "kind": "note", "title": "ملاحظة عن القانون المصري (اقرأها مرة تانية)",
         "md": "الأرقام والمواعيد في هذا الدرس (القانون 151/2020 · القرار الوزاري 816/2025 · فترة توفيق الأوضاع · نطاق الغرامات · اختصاص المحاكم الاقتصادية) مأخوذة من نصوص منشورة وملخصات قانونية متاحة في 2026. **قبل أي قرار امتثال**: اقرأ النص الرسمي المنشور في الجريدة الرسمية، وراجع موقع/تواصل **مركز حماية البيانات الشخصية** التابع لوزارة الاتصالات، واستعن بمحامٍ مختص في حماية البيانات — خصوصًا في موضوعات: **الترخيص/التصريح** · **نقل البيانات عبر الحدود** · **تعيين مسؤول حماية بيانات مسجل** · **مواعيد وإجراءات إخطار الخرق**."},
    ],
}

LESSONS_S7_H = [_L5]
