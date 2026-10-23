"""Stage 5, Module 1 — Decomposition & communication (lessons 1-2 of 4)."""

TODAY = "2026-10-22"

LESSONS_S5_A = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s5-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الميكروسيرفيسز **مش ترقية تقنية** — دي مقايضة تنظيمية وتشغيلية: بتشتري استقلالية النشر
والتوسع المستقل وعزل الأعطال، وبتدفع مقابلها الشبكة، المعاملات الموزعة، المراقبة الإجبارية،
وCI/CD لكل خدمة، وتعقيد الاختبار والتطوير المحلي.

الدرس ده مش «إزاي تعمل ميكروسيرفيسز» — ده «**إمتى تستاهل**». وهنعمله بأدوات:
سكور كارد بأرقام، تحليل churn واقتران من الـgit، وقائمة جاهزية تشغيلية **لازم تكتمل قبل أول فصل**.

وفي الآخر: مسار الفصل التدريجي (Strangler) لو القرار كان «نعم».
"""},
            {"type": "terms", "items": [
                {"term": "Conway's Law", "def": "هيكل النظام بينسخ هيكل التواصل في المؤسسة. لو فريق واحد → خدمة واحدة غالبًا صح؛ فصل الخدمات بلا فصل فرق = حدود وهمية."},
                {"term": "Deployment Coupling", "def": "عدم قدرتك على نشر تغيير إلا مع تغييرات تانية (جدول نشر مشترك، خوف من كسر حاجة) — من أقوى مبررات الفصل."},
                {"term": "Scaling Profile", "def": "شكل حمل كل جزء (RPS، ذاكرة، CPU/GPU، نمط الذروة). اختلاف واضح = مبرر تقني للفصل."},
                {"term": "Distributed Systems Fallacies", "def": "8 افتراضات خاطئة: الشبكة موثوقة، الزمن صفر، العرض لا نهائي، آمنة، الطوبولوجيا ثابتة، في مدير واحد، تكلفة النقل صفر، الشبكة متجانسة."},
                {"term": "Monolith First", "def": "ابدأ بموديولار مونوليث بحدود واضحة، وافصل خدمة لما يظهر دليل — مش قبله."},
                {"term": "Strangler Fig", "def": "استبدال تدريجي: مرّر الطلبات عبر gateway، انقل مسارًا مسارًا، واحذف القديم لما يفضى."},
                {"term": "Ops Maturity", "def": "جاهزيتك التشغيلية: CI/CD آلي، مراقبة موزعة (tracing)، إدارة أسرار، بيئات، نشر متدرج، on-call."},
                {"term": "Cognitive Load", "def": "الحمل الذهني على الفريق. خدمة إضافية = مستودع + pipeline + مراقبة + on-call + ترقيات اعتماديات."},
                {"term": "Blast Radius", "def": "نطاق تأثير الفشل. الفصل بيصغّره — لكن فقط لو فيه عزل حقيقي (timeouts/circuit breakers/bulkheads)."},
            ]},
            {"type": "heading", "level": 2, "text": "1) التكلفة الحقيقية (قائمة «لازم تبنيها قبل ما تفصل»)"},
            {"type": "table", "head": ["ما تحتاجه قبل الفصل", "لييه", "الحالة في أغلب الفرق"], "rows": [
                ["CI/CD آلي لكل خدمة (build/test/scan/deploy)", "نشر يدوي × N خدمات = خطأ بشري × N", "غالبًا ناقص"],
                ["**Distributed tracing** (OpenTelemetry + correlation id)", "بلاه، طلب واحد بيبقى 12 سطر لوج في 5 خدمات بلا ربط", "نادراً جاهز"],
                ["Metrics + dashboards + alerts لكل خدمة", "«الطلب بطيء» بلا مقاييس = تخمين", "جزئي"],
                ["إدارة أسرار وإعدادات مركزية", "أسرار مكررة في N أماكن = تسريب + تدوير مستحيل", "غالبًا ناقص"],
                ["Service discovery أو gateway", "عناوين الخدمات في الإعدادات = كسر عند أي تغيير", "—"],
                ["Contract tests بين الخدمات", "بلاها: تغيير في خدمة يكسر المستهلك في الإنتاج", "نادراً"],
                ["بيئة محلية تشغّل النظام كله (compose/Aspire)", "بلاها: المطور ما يقدرش يختبر تغييره", "جزئي"],
                ["نشر متدرج + rollback آلي", "فشل نشر خدمة واحدة ممكن يوقف ميزة كاملة", "نادراً"],
                ["معالجة معاملات موزعة (Saga/outbox)", "«احفظ وانقل» بقت مشكلتك", "—"],
                ["On-call وخبرة تشغيل أنظمة موزعة", "الأعطال بتظهر 2 صباحًا بشكل مختلف تمامًا", "غالبًا ناقص"],
                ["ميزانية بنية تحتية أعلى (حاويات، شبكات، مراقبة)", "3 خدمات = 3× حد أدنى من الموارد + overhead", "يُستهان به"],
            ]},
            {"type": "callout", "kind": "warn", "title": "الرقم اللي لازم تعرفه",
             "md": """
كل خدمة إضافية بتضيف **تكلفة ثابتة** مستمرة: مستودع، pipeline، ترقيات اعتماديات، مراقبة، توثيق، on-call،
وتنسيق إصدارات. في الفرق الصغيرة (أقل من ~10 مطورين) التكلفة دي بتاكل كل ميزة الاستقلالية.

القاعدة التقريبية المنتشرة في الصناعة (وقابلة للنقاش): **فريق واحد (2-pizza) لكل 1-3 خدمات**،
ومش أكتر من خدمة لكل 2-3 مطورين. لو عندك 4 مطورين و8 خدمات → إنت بتدير بنية تحتية مش منتج.
"""},
            {"type": "heading", "level": 2, "text": "2) سكور كارد القرار (بالأرقام، مش بالإحساس)"},
            {"type": "table", "head": ["#", "السؤال", "الدليل المطلوب", "نقاط"], "rows": [
                ["1", "هل فريقان أو أكتر بيُعطَّلوا بسبب جدول نشر مشترك؟", "سجل النشر: كم مرة تأجل/انتظر فريق تاني (ساعات/شهر)", "≥ 4 ساعات/أسبوع = 2 · أقل = 0"],
                ["2", "هل فيه جزء له ملف توسع مختلف بوضوح؟", "قياس حمل لكل موديول (RPS/CPU/ذاكرة) من الـmetrics", "≥ 3× فرق = 2 · < 3× = 0"],
                ["3", "هل الحدود والبيانات مملوكة بوضوح؟", "اختبار معماري + صفر FK متقاطع (مشروع المرحلة 4)", "نعم = 2 · جزئي = 1 · لأ = 0"],
                ["4", "هل عندك CI/CD آلي ومراقبة موزعة؟", "جدول الجاهزية أعلاه (11 بندًا)", "≥ 8 جاهز = 2 · 4-7 = 1 · < 4 = 0"],
                ["5", "هل فيه متطلب امتثال يفرض عزلًا فيزيائيًا؟", "متطلب مكتوب (PCI/HIPAA/سيادة بيانات)", "نعم = 2 · لأ = 0"],
                ["6", "هل الموديول المرشح مستقر عقديًا؟", "عدد تغييرات العقد في آخر 6 شهور (من git)", "≤ 2 = 2 · 3-5 = 1 · > 5 = 0"],
                ["7", "هل حجم الفريق يسمح بملكية خدمة؟", "عدد المطورين المتفرغين للخدمة", "≥ 3 = 2 · 2 = 1 · 1 = 0"],
                ["8", "هل التوسع الرأسي ما بقاش يكفي؟", "قياس: الحمل مقابل السعة المقاسة (k6)", "> 70% من السعة + لا يمكن التوسع رأسيًا = 2"],
                ["9", "هل فيه احتياج تقني مختلف فعلًا؟", "متطلب موثق (GPU، لغة، تخزين متخصص)", "نعم = 1 · لأ = 0"],
                ["10", "هل جربت وقيست الحلول الأبسط؟", "موديولار مونوليث + تحسين أداء + كاش (قياسات محفوظة)", "نعم = 1 · لأ = 0"],
            ]},
            {"type": "callout", "kind": "goal", "title": "قراءة النتيجة",
             "md": """
- **0-6 نقاط**: لا تفصل. كمّل على modular monolith، وقِس كل 3 شهور.
- **7-11 نقطة**: افصل **خدمة واحدة** كحد أقصى (الأعلى نقاطًا في البنود 1-3)، واحتفظ بالباقي مدمجًا.
  وشرط: أكمل جدول الجاهزية أولًا.
- **12+ نقطة**: الفصل مبرر. ابدأ بخدمتين، وضع خطة 6 شهور للباقي، وراقب تكلفة التشغيل كل شهر.

⚠️ البند 4 (الجاهزية التشغيلية) **شرط مانع**: لو صفر، النتيجة الكلية بلا قيمة — ابني الجاهزية أولًا.
"""},
            {"type": "heading", "level": 2, "text": "3) أدوات القرار: churn واقتران من الـgit"},
            {"type": "code", "lang": "bash", "filename": "tools/analyze-service-candidates.sh", "title": "أنهي جزء مرشح للفصل؟ (بيانات مش إحساس)", "code": r'''
#!/usr/bin/env bash
# يقيس لكل موديول: معدل التغيير (churn)، عدد المساهمين، الاقتران بباقي الكود، وحجمه.
set -euo pipefail
SINCE="${SINCE:-6 months ago}"
MODULES=("Catalog" "Orders" "Shipping" "Notifications" "Identity")

printf "%-16s %8s %8s %10s %10s %8s\n" MODULE COMMITS AUTHORS CHURN_LINES COUPLING SIZE_LOC

for m in "${MODULES[@]}"; do
  dir="src/Modules/Shop.$m"
  [ -d "$dir" ] || continue

  # ① عدد التغييرات والمساهمين (من سجل git)
  commits=$(git log --since="$SINCE" --oneline -- "$dir" | wc -l | tr -d ' ')
  authors=$(git log --since="$SINCE" --pretty='%an' -- "$dir" | sort -u | wc -l | tr -d ' ')

  # ② حجم التغيير الفعلي (أسطر مضافة + محذوفة)
  churn=$(git log --since="$SINCE" --numstat --pretty=format: -- "$dir" \
          | awk 'NF==3 {add+=$1; del+=$2} END {print add+del}')

  # ③ الاقتران: كام سطر في الموديول بيشير لموديولات تانية؟
  coupling=$(grep -rn "using Shop\." "$dir" --include=*.cs 2>/dev/null \
             | grep -v "Shop.$m" | grep -v "Shop.Kernel" | wc -l | tr -d ' ')

  # ④ الحجم الحالي
  loc=$(find "$dir" -name '*.cs' -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')

  printf "%-16s %8s %8s %10s %10s %8s\n" "$m" "$commits" "$authors" "${churn:-0}" "$coupling" "$loc"
done

echo
echo "── التفسير ──"
echo "مرشح جيد للفصل = churn عالي (بيتغير كتير) + coupling منخفض (معتمد على نفسه) + مؤلفين كتير (فريق مختلف)"
echo "مرشح سيئ       = coupling عالي (هتكسر كل حاجة لما تفصله) أو churn منخفض (مالوش داعي)"
'''},
            {"type": "code", "lang": "text", "filename": "docs/service-decision-worksheet.md", "title": "ورقة القرار (املأها بالأرقام)", "code": r'''
# ورقة قرار: هل نفصل خدمة <اسم الموديول>؟

التاريخ: 2026-10-22 · المراجع: ADR-0007 (modular monolith)

## 1. القياسات
| المقياس | القيمة | المصدر |
|---|---|---|
| p95 الحالي للمسار | 61ms | results/read-model/before-after.md |
| السعة المقاسة (نسخة واحدة) | 1,240 RPS | results/05-final/summary.json |
| الحمل الفعلي في الذروة | 210 RPS (17%) | Grafana — 30 يومًا |
| churn الموديول (6 شهور) | 41 commit / 5 مؤلفين | analyze-service-candidates.sh |
| الاقتران بموديولات تانية | 3 مراجع (كلها Contracts) | نفس السكربت |
| تأخيرات النشر المشترك | 1.5 ساعة/شهر | سجل النشر |
| الأحداث المتبادلة | 3 منشورة / 2 مستهلكة | خريطة الموديولات |

## 2. السكور كارد
| # | البند | النقاط | الدليل |
|---|---|---|---|
| 1 | تعطيل نشر مشترك | 0 | 1.5 ساعة/شهر فقط |
| 2 | ملف توسع مختلف | 0 | كل الموديولات تحت 20% من السعة |
| 3 | حدود وبيانات واضحة | 2 | اختبارات معمارية خضراء + صفر FK |
| 4 | جاهزية تشغيلية | 1 | 6/11 بندًا (ناقص tracing وcontract tests وprogressive delivery) |
| 5 | متطلب امتثال | 0 | لا يوجد |
| 6-10 | ... | ... | ... |
| **الإجمالي** | | **7/20** | |

## 3. القرار
**لا نفصل الآن** (7 نقاط + البند 4 ناقص = شرط مانع).

## 4. ما سنفعله بدل ذلك
1. نكمل جدول الجاهزية (tracing + contract tests) — 3 أسابيع.
2. نقيس كل 3 شهور بنفس الورقة.
3. أول مرشح عند الحاجة: `Notifications` (churn أعلى، اقتران أقل، وفشله لا يجب أن يؤثر على الطلبات).

## 5. شروط تغيير القرار (مقاسة)
- تأخيرات النشر المشترك > 4 ساعات/أسبوع لمدة شهر
- أو حمل موديول واحد > 70% من سعة النسخة مع استحالة التوسع الرأسي
- أو متطلب امتثال مكتوب يفرض عزل بيانات
'''},
            {"type": "heading", "level": 2, "text": "4) أسباب صحيحة مقابل أسباب خاطئة"},
            {"type": "table", "head": ["السبب", "الحكم", "التعليق"], "rows": [
                ["فريقان بيتعطّلوا بالنشر المشترك (مقاس)", "✓ صحيح", "أقوى مبرر على الإطلاق — الميكروسيرفيسز حل تنظيمي أولًا"],
                ["جزء واحد بيستهلك 80% من الموارد وحِمله مختلف", "✓ صحيح", "توسع مستقل مبرر — بشرط القياس"],
                ["متطلب امتثال يفرض عزل بيانات الدفع", "✓ صحيح", "عزل فيزيائي/شبكة مش ممكن داخل عملية واحدة"],
                ["احتياج GPU/لغة مختلفة لموديول واحد", "✓ صحيح", "عزل تقني حقيقي (مثل خدمة توصيات)"],
                ["عزل الأعطال: فشل X ما يجب أن يسقط Y", "△ جزئي", "يتحقق كمان بـcircuit breakers وbulkheads داخل العملية — جرّبها أولًا"],
                ["«الميكروسيرفيسز أحدث»", "✗ خاطئ", "موضة مش معيار؛ التكلفة ثابتة والفائدة مش مضمونة"],
                ["«عايزين نتوسع»", "✗ غامض", "التوسع الرأسي + التحسين بيوصّل لملايين الطلبات؛ اطلب رقمًا"],
                ["«الكود بقى كبير»", "✗ خاطئ", "الحل حدود (modular)، مش عمليات منفصلة"],
                ["«كل شركة كبيرة بتعملها»", "✗ خاطئ", "الشركات الكبيرة عندها مئات الفرق — ده السبب الحقيقي عندهم"],
                ["«عايزين نستخدم Kubernetes»", "✗ خاطئ", "عربة قبل الحصان؛ K8s تكلفة تشغيلية إضافية"],
                ["«الـmonolith بطيء في التطوير»", "△ افحص", "غالبًا السبب: اختبارات بطيئة، اقتران، بلا حدود — كل ده بيتحل من غير فصل"],
                ["«فريق جديد يحتاج يستقل»", "✓ صحيح", "Conway's law: هيكل الفريق بيحدد الهيكل الصحيح للنظام"],
            ]},
            {"type": "callout", "kind": "note", "title": "الاتجاه المعاكس موجود فعلًا",
             "md": """
فيه حالات موثقة لفرق رجعت من الموزّع للمدمج بعد ما قاست التكلفة. أشهر مثال حديث فريق
**Amazon Prime Video** (2023): نشروا إن نقل جزء من نظام مراقبة الفيديو من بنية موزعة/serverless
لتطبيق مدمج واحد خفّض تكلفة التشغيل بشكل كبير (بحسب ما نشروا، بنسبة ~90% لهذا المكوّن).

الدرس مش «الميكروسيرفيسز غلط» — الدرس إن **المقايضة بتتقيس**:
لما الحمل صغير والحدود مش محتاجة عزل، تكلفة التنسيق بتتجاوز الفائدة.

كمان شائع: فرق بتبدأ بـmodular monolith وبتفصل خدمة واحدة لما تظهر الحاجة،
وده أسهل بكتير من الرجوع من 12 خدمة موزعة لنظام واحد.
"""},
            {"type": "heading", "level": 2, "text": "5) لو القرار «نعم»: مسار الفصل التدريجي"},
            {"type": "steps", "title": "Strangler: 7 خطوات", "items": [
                {"title": "اختر خدمة واحدة (الأقل خطرًا)",
                 "md": "المعايير: اقتران منخفض، حدود بيانات واضحة، وفشلها لا يسقط النظام. تجنّب البدء بخدمة الطلبات/المدفوعات."},
                {"title": "اكمل الجاهزية أولًا",
                 "md": "tracing بـcorrelation id، contract tests، CI/CD للخدمة الجديدة، مراقبة، وإدارة أسرار. **قبل** أول سطر كود."},
                {"title": "افصل البيانات (الأصعب)",
                 "md": "انقل الجداول لـschema/قاعدة الخدمة، واحذف الـFKs المتقاطعة، وابدأ بالأحداث للمزامنة. ده بيستغرق أطول من فصل الكود."},
                {"title": "ضع gateway أمام المسار",
                 "md": "YARP (درس 5.1.4) يوجّه للمسار الجديد أو القديم بحسب قاعدة — عشان تقدر تنقل تدريجيًا وترجع فورًا."},
                {"title": "انقل الوظائف تدريجيًا مع feature flag",
                 "md": "نسبة 1% ← 10% ← 50% ← 100%، مع مقارنة النتائج (shadow traffic) قبل تحويل الحركة."},
                {"title": "قِس قبل وبعد",
                 "md": "زمن التسليم (lead time)، معدل الفشل، p95، تكلفة التشغيل، وزمن on-call. لو الأرقام ساءت → ارجع (وده قرار سليم مش فشل)."},
                {"title": "احذف الكود القديم",
                 "md": "الخطوة اللي أغلب الفرق بتنساها → نظامين شغالين للأبد. حدّد تاريخًا واحذف."},
            ]},
            {"type": "checkpoints", "items": [
                "أقيس مبررات الفصل (تعطيل النشر، ملفات التوسع، الامتثال) بأرقام من سجل النشر والـmetrics.",
                "أعرف التكلفة الثابتة لكل خدمة وأتحقق من الجاهزية التشغيلية (11 بندًا) قبل أي فصل.",
                "أستخدم سكور كارد وورقة قرار، وأسجّل النتيجة والقرار في ADR بشروط إعادة نظر.",
                "لو قررت الفصل: أتبع مسار Strangler بأول خدمة منخفضة الخطر وأقيس قبل/بعد.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "أقوى مبرر لفصل خدمة؟",
                 "options": [
                     "حجم الكود",
                     "تعطيل نشر مشترك مقاس بين فريقين (أو متطلب امتثال يفرض عزلًا فيزيائيًا)",
                     "استخدام أحدث التقنيات",
                     "سرعة التنفيذ",
                 ], "answer": 1,
                 "explain": "الميكروسيرفيسز حل تنظيمي/تشغيلي أولًا. لو مفيش فريقين بيتعطّلوا، أغلب الفوائد مش هتحصل والتكاليف هتفضل."},
                {"q": "«الـmonolith بتاعنا بطيء في التطوير، هنقسمه لميكروسيرفيسز». التقييم؟",
                 "options": [
                     "منطقي",
                     "غالبًا تشخيص غلط: البطء سببه اقتران/اختبارات بطيئة/بلا حدود — وكلها تُحل بموديولار مونوليث أرخص",
                     "مستحيل",
                     "يعتمد على اللغة",
                 ], "answer": 1,
                 "explain": "قس أولًا: زمن الاختبارات، churn والاقتران، وتأخيرات النشر. لو الحدود هي المشكلة، الفصل بيضيف الشبكة كمان."},
                {"q": "أنهي موديول مرشح جيد للفصل أولًا؟",
                 "options": [
                     "الأكبر حجمًا",
                     "churn عالي + اقتران منخفض + فشلُه لا يسقط النظام (مثل Notifications)",
                     "الأهم تجاريًا (Orders)",
                     "اللي فيه أكتر bugs",
                 ], "answer": 1,
                 "explain": "ابدأ بالمنخفض الخطورة عشان تبني الجاهزية (tracing، CI/CD، contract tests) على حالة بسيطة قبل ما تفصل المسار الحرج."},
                {"q": "ليه البند «الجاهزية التشغيلية» شرط مانع في السكور كارد؟",
                 "options": [
                     "بيروقراطية",
                     "بلا tracing وCI/CD ومراقبة: الفصل بيحوّل مشكلة بطء تطوير لمشكلة أعطال غير قابلة للتشخيص — تكلفة أعلى بلا فائدة",
                     "مطلب قانوني",
                     "يقلل الأداء",
                 ], "answer": 1,
                 "explain": "أنظمة موزعة بلا مراقبة = «الطلب بطيء» و12 سطر لوج في 5 خدمات بلا رابط. ابني الأدوات قبل البنية."},
                {"q": "أصعب جزء في فصل خدمة؟",
                 "options": [
                     "نقل الكود",
                     "فصل البيانات: نقل الجداول، حذف FKs المتقاطعة، والمزامنة بالأحداث مع اتساق eventual",
                     "كتابة Dockerfile",
                     "إعداد الـgateway",
                 ], "answer": 1,
                 "explain": "الكود بيتنقل في أيام؛ البيانات بتاخد أسابيع لأنها بتغيّر ضمانات الاتساق وتفرض أحداثًا وprojections."},
                {"q": "بعد الفصل، الأرقام ساءت (lead time أعلى، أعطال أكتر). التصرف؟",
                 "options": [
                     "كمل — التغيير يحتاج وقت",
                     "قيس بدقة، ولو التكلفة أعلى من الفائدة بعد فترة محددة → ارجع للدمج ووثّق القرار في ADR",
                     "احذف المراقبة",
                     "أضف خدمات أكتر",
                 ], "answer": 1,
                 "explain": "الرجوع قرار هندسي سليم لو مدعوم بأرقام — مش فشل. عشان كده قياس قبل/بعد لازم يبدأ من أول يوم."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "ورقة قرار مبنية على قياس",
                 "md": "املأ ورقة القرار (الأعلاه) لنظامك أو لمشروع المرحلة 4: اجمع 7 مقاييس على الأقل من مصادر حقيقية (سجل نشر، metrics، git، قياس أداء)، واملأ السكور كارد، واكتب القرار مع شروط إعادة النظر.",
                 "criteria": [
                     "≥ 7 مقاييس بمصدر لكل واحد (مش تقديرات)",
                     "السكور كارد مملوء (10 بنود) مع دليل لكل بند",
                     "قرار صريح (لا نفصل / نفصل خدمة واحدة / نفصل أكثر) مبني على النقاط",
                     "تقييم جدول الجاهزية (11 بندًا) وخطة لسد الناقص",
                     "شروط إعادة نظر مقاسة + تاريخ المراجعة التالية",
                     "ADR يلخّص القرار (ولو كان «لا نفصل»)",
                 ],
                 "hint": "مش لاقي metrics؟ شغّل مشروعك محليًا بـk6 وجمع `dotnet-counters` لمدة 10 دقائق — ده مصدر قياس حقيقي."},
                {"id": "t2", "title": "تحليل المرشحين + خطة جاهزية",
                 "md": "شغّل سكربت تحليل churn/الاقتران على مشروعك، وارسم مصفوفة المرشحين (churn × اقتران × حجم). اختَر مرشحًا أول وخطط لفصله: ما الذي يجب بناؤه أولًا (tracing، contract tests، CI/CD)، وكيف تفصل بياناته، وكيف تقيس النجاح.",
                 "criteria": [
                     "جدول بالمقاييس لكل موديول (commits، مؤلفين، churn، اقتران، حجم)",
                     "مصفوفة تفسير (مرشح جيد/سيئ وليه)",
                     "خطة جاهزية: 5 عناصر على الأقل مع تقدير زمن لكل واحد",
                     "خطة فصل البيانات (الجداول، FKs، الأحداث، المزامنة، فترة الانتقال)",
                     "مقاييس نجاح ما بعد الفصل (lead time، p95، معدل الفشل، التكلفة)",
                     "خطة تراجع (rollback) لو الأرقام ساءت",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Microservices.io — Decomposition patterns", "url": "https://microservices.io/patterns/decomposition/index.html"},
                {"label": ".NET — Choose between monolith and microservices", "url": "https://learn.microsoft.com/dotnet/architecture/cloud-native/choosing-between-monolith-and-microservices"},
                {"label": "Strangler Fig application", "url": "https://martinfowler.com/bliki/StranglerFigApplication.html"},
                {"label": "Fallacies of distributed computing", "url": "https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing"},
                {"label": "Amazon Science blog (Prime Video case)", "url": "https://www.amazon.science/blog"},
                {"label": "Team Topologies", "url": "https://teamtopologies.com/"},
                {"label": "System design primer", "url": "https://github.com/donnemartin/system-design-primer"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s5-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لو فصلت خدمات وخليتهم **يشاركوا نفس قاعدة البيانات** → ما عملتش ميكروسيرفيسز،
عملت monolith موزّع: نفس الاقتران، زائد تكلفة الشبكة. ده أشهر غلط وأصعب واحد يتراجع عنه.

الدرس ده عن الحاجة اللي بتحدد نجاح التقسيم فعلًا: **حدود الخدمات وملكية البيانات**.
هنغطي: Bounded Contexts وخريطة السياق (context map)، ملكية البيانات وقواعد عدم المشاركة،
إزاي تتعامل مع الحاجة الطبيعية لبيانات من خدمة تانية (5 أنماط)،
والمعاملات العابرة للخدمات (Sagas بالتعويض)، وإصدار العقود.
"""},
            {"type": "terms", "items": [
                {"term": "Bounded Context", "def": "حدود لغوية ونموذجية: كلمة «منتج» معناها مختلف في الكتالوج عنه في الشحن عنه في المحاسبة. كل سياق له نموذجه الخاص."},
                {"term": "Context Map", "def": "رسم للعلاقات بين السياقات (مَن يعتمد على مَن وبأي نمط) — أهم وثيقة معمارية في الأنظمة الموزعة."},
                {"term": "Database per Service", "def": "كل خدمة تملك مخزنها الخاص (قاعدة أو schema). لا خدمة تانية تقرأ منه مباشرة."},
                {"term": "Shared Database (anti-pattern)", "def": "قاعدة مشتركة → أي تغيير مخطط يتطلب تنسيق نشر بين كل الخدمات = اقتران كامل."},
                {"term": "Anti-Corruption Layer (ACL)", "def": "طبقة ترجمة بين سياقك وسياق خارجي/قديم — تحمي نموذجك من تلوث نموذجهم."},
                {"term": "Open Host Service / Published Language", "def": "خدمة تعرض مجموعة بروتوكولات/عقود موثقة يستهلكها كثيرون (مثل API عام بصيغة قياسية)."},
                {"term": "Customer-Supplier", "def": "علاقة بين فريقين حيث المستهلك له صوت في أولويات المزوّد (عقد متفاوض عليه)."},
                {"term": "Conformist", "def": "المستهلك يتبنى نموذج المزوّد بالكامل (بلا تفاوض) — مناسب لمزوّد خارجي لا يتغير."},
                {"term": "Saga", "def": "سلسلة عمليات محلية عبر خدمات، كل واحدة لها **إجراء تعويضي**. نوعان: orchestration (منسّق مركزي) وchoreography (أحداث متسلسلة)."},
                {"term": "Compensating Action", "def": "إجراء يعكس أثر خطوة سابقة (إلغاء حجز، رد مبلغ) — بديل الـrollback في الأنظمة الموزعة."},
                {"term": "API Composition", "def": "خدمة/بوابة تجمع نتائج نداءات متعددة في استجابة واحدة (للواجهات)."},
                {"term": "Data Duplication", "def": "نسخ البيانات المطلوبة محليًا (عبر أحداث) — ثمن الاستقلالية، ويحتاج استراتيجية اتساق."},
            ]},
            {"type": "heading", "level": 2, "text": "1) رسم الحدود: Bounded Contexts"},
            {"type": "code", "lang": "text", "filename": "docs/context-map.md", "title": "خريطة السياق (وثيقة حية)", "code": r'''
# Context Map — نظام المتجر

## السياقات (Bounded Contexts)
| السياق | اللغة الخاصة به | «المنتج» هنا يعني | المالك (فريق) | المخزن |
|---|---|---|---|---|
| Catalog | Product, Category, Attribute, Price | عنصر قابل للبيع بوصف وصور وسعر | فريق المنصة | catalog (Postgres) |
| Orders | Order, OrderLine, Total, Status | سطر مُسعَّر في طلب (اسم + سعر منسوخ) | فريق التجارة | orders (Postgres) |
| Shipping | Shipment, Parcel, Carrier, Weight | عنصر له وزن وأبعاد يُشحن | فريق اللوجستيات | shipping (Postgres) |
| Payments | Invoice, Charge, Refund, PSP | مبلغ مستحق/محصل | فريق المدفوعات | payments (Postgres + PSP) |
| Notifications | Message, Template, Channel, Delivery | محتوى + وجهة | فريق المنصة | notifications (Postgres) |
| Identity | User, Role, Tenant, Session | مستخدم له صلاحيات | فريق الأمان | identity (Postgres) |

★ لاحظ: «المنتج» له 3 معانٍ مختلفة في 3 سياقات. ده **صحيح** — مش تكرار يجب توحيده.

## العلاقات بين السياقات (أنماط Context Mapping)
| من | إلى | النمط | العقد | ملاحظات |
|---|---|---|---|---|
| Orders | Catalog | **Customer-Supplier** | `ICatalogModule` (سعر/مخزون لحظي) | Orders له أولوية في طلبات التغيير |
| Orders | Shipping | **Published Language** (أحداث) | `order.placed@2`, `order.cancelled@2` | عقد موثق + إصدارات |
| Shipping | Orders | **Conformist** | يقرأ `OrderSnapshot` كما هو | بلا تفاوض — الشحن يتكيف |
| Payments | PSP خارجي | **Anti-Corruption Layer** | مترجم داخلي `IPaymentGateway` | لا تسريب نموذج Stripe لجوه |
| Notifications | كل السياقات | **Open Host** (اشتراك في أحداث) | يستهلك أي `IIntegrationEvent` | يضيف نفسه بلا تغيير المصدر |
| Identity | الكل | **Shared Kernel** (محدود) | `UserId`, `TenantId` فقط | ★ صغير ومتفق عليه ومراجع |
| Reporting | الكل | **CDC / نسخ** | جداول read-only في warehouse | بلا نداءات وقت التشغيل |

## قواعد لا تُكسر
1. لا خدمة تقرأ جداول خدمة تانية (ولا view ولا join).
2. كل ما تحتاجه خدمة من أخرى: نداء عقد متزامن (للقراءة الفورية) أو حدث (للأثر الجانبي).
3. أي تكرار بيانات له مالك واحد (المصدر) وخطة اتساق مكتوبة.
4. Shared Kernel مقصور على معرّفات وأنواع قيمة — ممنوع منطق عمل.
'''},
            {"type": "callout", "kind": "tip", "title": "إزاي تلاقي الحدود الصح (مش بالتخمين)",
             "md": """
**4 إشارات تستخدمها معًا:**
1. **اللغة**: لو نفس الكلمة لها معنيان («منتج» في الكتالوج مقابل الشحن) → حدود.
   ولو كلمتان مختلفتان لنفس المعنى → سياق واحد.
2. **معدل التغيير**: الأشياء اللي بتتغير معًا تسكن معًا. قِس churn من git (درس 5.1.1).
3. **الـinvariants**: القواعد اللي لازم تكون صحيحة لحظيًا تحدد حدود المعاملة (aggregate/خدمة).
   القواعد اللي تتحمل تأخيرًا → عبر الأحداث.
4. **الملكية التنظيمية**: مين هيوصل on-call لده؟ حدود بلا مالك = حدود وهمية (Conway's law).

**اختبار سريع:** لو تخيّلت إن الجزء ده فشل تمامًا لمدة ساعة — أنهي ميزة بتقع؟
لو الإجابة «ميزة واحدة واضحة» → حد محتمل جيد. لو «كل شيء» → إنت لسه في monolith ذهنيًا.
"""},
            {"type": "heading", "level": 2, "text": "2) ملكية البيانات: القواعد والبدائل"},
            {"type": "table", "head": ["النموذج", "الوصف", "الحكم", "متى"], "rows": [
                ["**قاعدة لكل خدمة**", "خادم/قاعدة مستقلة لكل خدمة", "✓ الهدف النهائي", "خدمات حقيقية بفرق منفصلة"],
                ["**schema لكل خدمة** (نفس الخادم)", "خدمة واحدة Postgres، schemas معزولة وصلاحيات محدودة", "✓★ خطوة انتقالية ممتازة", "modular monolith → فصل تدريجي"],
                ["جداول مشتركة بين خدمتين", "خدمتان تقرأان/تكتبان نفس الجدول", "✗ مرفوض", "أبدًا (ده monolith موزّع)"],
                ["قاعدة واحدة + «كل خدمة تشوف جداولها» بالاتفاق", "عزل بالاتفاق لا بالصلاحيات", "✗ ينهار", "أبدًا (أول deadline بيكسره)"],
                ["مخزن متخصص لكل خدمة", "Postgres للطلبات، Mongo للكتالوج، OpenSearch للبحث", "✓ لو مبرر", "polyglot persistence (درس 3.3.2)"],
            ]},
            {"type": "code", "lang": "sql", "filename": "db/service-ownership.sql", "title": "عزل فعلي بالصلاحيات (مش بالاتفاق)", "code": r'''
-- ① مستخدم قاعدة لكل خدمة بصلاحيات على schema الخاص بها فقط
CREATE ROLE orders_svc  LOGIN PASSWORD :'orders_pw';
CREATE ROLE catalog_svc LOGIN PASSWORD :'catalog_pw';
CREATE ROLE shipping_svc LOGIN PASSWORD :'shipping_pw';

GRANT USAGE ON SCHEMA orders  TO orders_svc;
GRANT ALL     ON ALL TABLES IN SCHEMA orders  TO orders_svc;
ALTER DEFAULT PRIVILEGES IN SCHEMA orders GRANT ALL ON TABLES TO orders_svc;

GRANT USAGE ON SCHEMA catalog TO catalog_svc;
GRANT ALL     ON ALL TABLES IN SCHEMA catalog TO catalog_svc;

-- ★ العزل الحقيقي: خدمة الشحن لا تستطيع قراءة جداول الطلبات إطلاقًا
-- (ما فيهوش GRANT لـshipping_svc على orders) → أي محاولة تفشل بـpermission denied

-- ② قراءة عبر عقد فقط: لو الشحن محتاج بيانات طلب، ياخدها من API/حدث — مش من الجدول

-- ③ فحص الانتهاكات: هل فيه كائن في schema خدمة بيمتلكه مستخدم خدمة تانية؟
SELECT table_schema, table_name, grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema IN ('orders','catalog','shipping','payments')
ORDER BY table_schema, grantee;

-- ④ مراقبة: هل فيه استعلام بيلمس أكثر من schema؟ (مؤشر كسر حدود)
SELECT calls, left(query, 140) AS query
FROM pg_stat_statements
WHERE query ~* '\\borders\\.' AND query ~* '\\b(catalog|shipping|payments)\\.'
ORDER BY calls DESC LIMIT 20;

-- ⑤ عند الفصل النهائي: انقل البيانات بأداة نسخ + تحقق من العدد/المجاميع
--    (pg_dump --schema=orders | pg_restore -d orders_db) ثم قارن:
--    SELECT count(*), sum(total_amount) FROM orders.orders;   على الطرفين
'''},
            {"type": "heading", "level": 3, "text": "3) الحاجة الطبيعية لبيانات خدمة تانية — 6 أنماط"},
            {"type": "table", "head": ["الحاجة", "النمط", "الاتساق", "التكلفة", "مثال"], "rows": [
                ["بيانات لحظية لاتخاذ قرار في نفس الطلب", "**نداء عقد متزامن** (gRPC/REST) + timeout + circuit breaker", "قوي", "اقتران وقت التشغيل (فشل مزوّد = فشلك)", "التحقق من المخزون قبل تأكيد الطلب"],
                ["بيانات تُعرض معًا (واجهة)", "**API composition** في الـgateway/BFF", "قوي (لحظي)", "نداءات متعددة + زمن", "صفحة تفاصيل الطلب (طلب + شحن + دفع)"],
                ["بيانات تُستخدم كتيرًا محليًا", "**نسخة محلية محدَّثة بالأحداث** (denormalized copy)", "eventual", "تخزين مكرر + نافذة اتساق", "اسم المنتج وسعره في سطر الطلب"],
                ["بحث/فلترة عبر مجالات", "**خدمة بحث** تُبنى من أحداث (OpenSearch)", "eventual", "بنية إضافية + إعادة فهرسة", "بحث في الكتالوج بخصائص من سياقات متعددة"],
                ["تقارير وتحليلات", "**CDC/ETL لمخزن بيانات** (warehouse)", "eventual (دقائق)", "بنية تحليلات", "تقرير مبيعات شهري عبر 4 مجالات"],
                ["تنفيذ عملية عبر خدمات", "**Saga** بإجراءات تعويضية", "eventual + تعويض", "تعقيد منطق التعويض", "طلب = خصم مخزون + دفع + شحن"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Infrastructure/CatalogAcl.cs", "title": "Anti-Corruption Layer + نسخة محلية من بيانات الكتالوج", "code": r'''
// ═══ المشكلة: خدمة الكتالوج بترجع نموذجها الخاص (ProductDto بحقول كتير وأسماء مختلفة) ═══
// لو Orders استخدمته مباشرة: أي تغيير في الكتالوج بيكسر Orders، ونموذج الكتالوج بيتسرب لجوه.

// ── ① نموذجنا الداخلي (ما نحتاجه فعلًا فقط) ──
public readonly record struct CatalogItemRef(
    Guid ProductId, string DisplayName, Money UnitPrice, int AvailableStock, bool IsSellable);

// ── ② منفذ (بلا تفاصيل النقل) ──
public interface ICatalogGateway
{
    Task<IReadOnlyList<CatalogItemRef>> GetItemsAsync(IReadOnlyList<Guid> productIds, CancellationToken ct);
}

// ── ③ الـACL: يترجم نموذجهم لنموذجنا، ويتعامل مع الفشل بصراحة ──
public static class Metrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Orders.acl", "1.0.0");
    public static readonly Counter<long> StaleCatalogReads =
        Meter.CreateCounter<long>("catalog.stale_reads");        // ⚠ أي زيادة = الكتالوج غير متاح
}

public sealed class CatalogAcl(
    ICatalogClient client,                  // gRPC/HTTP client مولّد من عقد الكتالوج
    IRedisCacheService cache,
    ILogger<CatalogAcl> log) : ICatalogGateway
{
    private static readonly TimeSpan Ttl = TimeSpan.FromSeconds(20);

    public async Task<IReadOnlyList<CatalogItemRef>> GetItemsAsync(
        IReadOnlyList<Guid> productIds, CancellationToken ct)
    {
        var ids = productIds.Distinct().ToList();

        // ✓ نسخة محلية قصيرة العمر (كاش) — تقلل الاقتران الزمني والزمن
        return await cache.GetOrSetAsync(
            $"orders:catalog:{string.Join(',', ids.OrderBy(x => x))}",
            async token =>
            {
                try
                {
                    var response = await client.GetProductsAsync(new GetProductsRequest(ids), token);

                    // ★ الترجمة هنا: أسماء مختلفة، وحدات مختلفة، حالات مختلفة
                    return response.Items.Select(i => new CatalogItemRef(
                        ProductId: i.Id,
                        DisplayName: i.Title,                                   // هم Title، إحنا DisplayName
                        UnitPrice: new Money(i.PriceMinorUnits / 100m, i.CurrencyCode),  // ★ وحدات أصغر → Money
                        AvailableStock: i.Stock?.Available ?? 0,                  // هم nullable، إحنا صفر افتراضي
                        IsSellable: i.Status == "ACTIVE" && (i.Stock?.Available ?? 0) > 0))
                        .ToList();
                }
                catch (Exception ex) when (ex is not OperationCanceledException)
                {
                    // ✓ فشل المزوّد لا يفشلنا بالكامل: نسخة قديمة معلنة أو فشل صريح
                    log.LogWarning(ex, "catalog unavailable for {Count} ids", ids.Count);
                    // (GetAsync<T> جزء من تجريد الكاش — أضفه لـIRedisCacheService من درس 3.3.1:
                    //  قراءة بلا حساب، ترجع null لو المفتاح غير موجود)
                    var stale = await cache.GetAsync<IReadOnlyList<CatalogItemRef>?>(
                        "orders:catalog:stale", token);

                    if (stale is not null)
                    {
                        Metrics.StaleCatalogReads.Add(1);
                        return stale;                       // ⚠ مقبول فقط للأسعار غير الحرجة
                    }
                    throw new DependencyUnavailableException("catalog");   // → 503 بلا كذب
                }
            }, Ttl, ct);
    }
}

// ── ④ نسخة محلية دائمة (لما تكون البيانات مطلوبة في كل طلب ولا تتحمل زمن الشبكة) ──
// جدول orders.catalog_snapshots (product_id PK, name, price, updated_at)
// يُحدَّث من حدث `product.price_changed` (مستهلك idempotent) — مش من نداء متزامن.
public sealed class CatalogSnapshotProjector(OrdersDbContext db, ILogger<CatalogSnapshotProjector> log)
    : INotificationHandler<IntegrationEventEnvelope<ProductPriceChanged>>
{
    public async Task Handle(IntegrationEventEnvelope<ProductPriceChanged> e, CancellationToken ct)
    {
        await db.Database.ExecuteSqlInterpolatedAsync($"""
            INSERT INTO orders.catalog_snapshots (product_id, name, price_minor, currency, updated_at)
            VALUES ({e.Event.ProductId}, {e.Event.Title}, {e.Event.PriceMinorUnits}, {e.Event.CurrencyCode}, {e.Event.OccurredAt})
            ON CONFLICT (product_id) DO UPDATE
            SET name = EXCLUDED.name, price_minor = EXCLUDED.price_minor, currency = EXCLUDED.currency,
                updated_at = EXCLUDED.updated_at
            WHERE orders.catalog_snapshots.updated_at < EXCLUDED.updated_at
            """, ct);                                          // ★ شرط يمنع تطبيق حدث أقدم (ترتيب معكوس)

        log.LogDebug("catalog snapshot updated for {ProductId}", e.Event.ProductId);
    }
}
'''},
            {"type": "heading", "level": 2, "text": "4) المعاملات عبر الخدمات: Sagas"},
            {"type": "table", "head": ["النوع", "كيف يعمل", "المزايا", "العيوب", "إمتى"], "rows": [
                ["**Orchestration** (منسّق مركزي)", "خدمة/مكوّن واحد يقرر الخطوات وينادي كل خدمة ويعوّض عند الفشل", "التدفق واضح ومركزي، سهل الاختبار والتتبع، سهل إضافة خطوات", "المنسّق نقطة مركزية (لكن بلا منطق عمل)", "★ أغلب الحالات — خصوصًا العمليات الحرجة"],
                ["**Choreography** (أحداث متسلسلة)", "كل خدمة تستمع لحدث وتنفذ خطوتها وتنشر الحدث التالي", "اقتران منخفض، بلا مركز", "التدفق مشتت — صعب الفهم/الاختبار/تتبع الحالات، وحلقات فشل محتملة", "تدفقات بسيطة (2-3 خطوات) بلا تعويض معقد"],
                ["2PC / معاملات موزعة", "التزام على مرحلتين عبر خدمات", "اتساق قوي", "✗ أقفال طويلة، فشل المنسّق، غير مدعوم عمليًا عبر خدمات مستقلة", "تقريبًا أبدًا"],
                ["Best-effort (بلا saga)", "نداءات متسلسلة بلا تعويض", "بسيط", "حالة غير متسقة عند أي فشل (خصم مخزون بلا طلب!)", "نموذج أولي فقط"],
            ]},
            {"type": "code", "lang": "csharp", "filename": "src/Services/Orders/Sagas/PlaceOrderSaga.cs", "title": "منسّق صريح: خطوات + تعويضات + مهلات + حالات", "code": r'''
/// <summary>
/// Saga بتنسيق مركزي (بلا اعتماد على مكتبة — نفس الفكرة في MassTransit/Wolverine، درس 5.2.3).
/// ★ الحالات تُحفظ في قاعدة الخدمة (state machine دائم) عشان نقدر نستأنف بعد انهيار.
/// </summary>
public static class SagaMetrics
{
    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Orders.sagas", "1.0.0");
    public static readonly Counter<long> Started = Meter.CreateCounter<long>("sagas.started");
    public static readonly Counter<long> Completed = Meter.CreateCounter<long>("sagas.completed");
    public static readonly Counter<long> Compensations = Meter.CreateCounter<long>("sagas.compensations");
    public static readonly Counter<long> CompensationFailures =
        Meter.CreateCounter<long>("sagas.compensation_failures");   // ★ تنبيه حرج لو زاد عن صفر
}

public sealed class PlaceOrderSaga(
    ICatalogGateway catalog, IPaymentsClient payments, IShippingClient shipping,
    SagaStore store, ILogger<PlaceOrderSaga> log, TimeProvider time)
{
    private static readonly TimeSpan StepTimeout = TimeSpan.FromSeconds(15);
    private static readonly TimeSpan SagaTimeout = TimeSpan.FromMinutes(5);

    public async Task<SagaResult> RunAsync(PlaceOrderRequest request, CancellationToken ct)
    {
        SagaMetrics.Started.Add(1);
        var saga = await store.CreateAsync<SagaState>(new SagaState
        {
            Id = Guid.NewGuid(), OrderId = request.OrderId, Status = SagaStatus.Started,
            StartedAt = time.GetUtcNow(), Deadline = time.GetUtcNow() + SagaTimeout,
        }, ct);

        try
        {
            // ── الخطوة 1: حجز المخزون (قابل للتعويض) ──
            saga = await store.MarkStepAsync(saga.Id, SagaStep.ReserveStock, ct);
            var stock = await catalog.ReserveAsync(request.OrderId, request.Lines, StepTimeout, ct);
            saga.ReservationId = stock.ReservationId;

            // ── الخطوة 2: تحصيل الدفع (قابل للتعويض) ──
            saga = await store.MarkStepAsync(saga.Id, SagaStep.CapturePayment, ct);
            var payment = await payments.CaptureAsync(request.OrderId, stock.Total, request.IdempotencyKey, StepTimeout, ct);
            saga.PaymentId = payment.ChargeId;

            // ── الخطوة 3: جدولة الشحن (آخر خطوة — تعويضها اختياري) ──
            saga = await store.MarkStepAsync(saga.Id, SagaStep.ScheduleShipment, ct);
            await shipping.ScheduleAsync(request.OrderId, stock.ShippingAddress, StepTimeout, ct);

            await store.CompleteAsync(saga.Id, ct);
            SagaMetrics.Completed.Add(1);
            log.LogInformation("saga {SagaId} completed for {OrderId}", saga.Id, request.OrderId);
            return SagaResult.Completed(request.OrderId);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            log.LogError(ex, "saga {SagaId} failed at step; compensating", saga.Id);
            await CompensateAsync(saga, ex, ct);
            return SagaResult.Failed(request.OrderId, saga.CurrentStep, ex.Message);
        }
    }

    /// <summary>التعويض **بالترتيب العكسي**، وكل خطوة تعويض مستقلة (فشلها لا يوقف الباقي).</summary>
    private async Task CompensateAsync(SagaState saga, Exception cause, CancellationToken ct)
    {
        // ③ الشحن — ★ >= مش >: لو فشلنا **أثناء** الجدولة، ما نعرفش لو تمت → حاول الإلغاء
        //   (والإلغاء لازم يكون idempotent: إلغاء شحنة غير موجودة = نجاح صامت)
        if (saga.CurrentStep >= SagaStep.ScheduleShipment)
            await TryAsync(() => shipping.CancelAsync(saga.OrderId, ct), "cancel-shipment", ct);

        // ② الدفع → رد المبلغ (الأهم: لا تترك تحصيلًا بلا طلب!)
        if (saga.PaymentId is not null)
            await TryAsync(() => payments.RefundAsync(saga.PaymentId!.Value, "saga-compensation", ct), "refund", ct);

        // ① المخزون → تحرير الحجز
        if (saga.ReservationId is not null)
            await TryAsync(() => catalog.ReleaseAsync(saga.ReservationId!.Value, ct), "release-stock", ct);

        await store.CompensatedAsync(saga.Id, cause.Message, ct);
        SagaMetrics.Compensations.Add(1, new("step", saga.CurrentStep.ToString()));
    }

    private async Task TryAsync(Func<Task> action, string name, CancellationToken ct)
    {
        try { await action(); }
        catch (Exception ex)
        {
            // ★ فشل التعويض = حالة تحتاج تدخلًا بشريًا (لا تبتلعها!)
            log.LogCritical(ex, "compensation '{Name}' failed for saga — requires manual resolution", name);
            SagaMetrics.CompensationFailures.Add(1, new("step", name));
            await store.MarkNeedsManualAsync(name, ex.Message, ct);
        }
    }
}

public enum SagaStep { Started = 0, ReserveStock = 1, CapturePayment = 2, ScheduleShipment = 3 }
public enum SagaStatus { Started, Running, Completed, Compensating, Compensated, NeedsManual }
public enum SagaResultKind { Completed, Failed }

public sealed record SagaResult(SagaResultKind Kind, Guid OrderId, SagaStep? FailedStep = null, string? Error = null)
{
    public static SagaResult Completed(Guid orderId) => new(SagaResultKind.Completed, orderId);
    public static SagaResult Failed(Guid orderId, SagaStep step, string error) =>
        new(SagaResultKind.Failed, orderId, step, error);
}

public sealed class SagaState
{
    public Guid Id { get; set; }
    public Guid OrderId { get; set; }
    public SagaStatus Status { get; set; }
    public SagaStep CurrentStep { get; set; }
    public Guid? ReservationId { get; set; }
    public Guid? PaymentId { get; set; }
    public DateTimeOffset StartedAt { get; set; }
    public DateTimeOffset Deadline { get; set; }
}
'''},
            {"type": "callout", "kind": "danger", "title": "5 قواعد Sagas اللي بتفرق بين نظام شغال وكارثة",
             "md": """
1. **كل خطوة لازم تكون idempotent** — المنسّق هيعيد المحاولة (timeout/انهيار)، فالتكرار متوقع.
2. **الحالة تُحفظ قبل النداء**، لا بعده — لو انهرت بين النداء والحفظ، هتنسى إن الخطوة تمت.
3. **مهلة لكل خطوة + مهلة للـsaga كله** — بلا مهلة، saga بيتعلّق للأبد ويحجز موارد.
4. **فشل التعويض = تنبيه حرج** (مش log وتحريك) — ده معناه فلوس/مخزون في حالة غير معروفة.
5. **لا تنفذ منطق عمل في المنسّق** — المنسّق يرتّب الخطوات فقط؛ القواعد في الخدمات.

وكمان: **صمّم الخطوات بحيث تكون التعويضات نادرة** — ابدأ بأرخص/أسهل خطوة قابلة للفشل
(تحقق، حجز) واختم بالخطوات الأصعب في الرجوع (تحصيل مالي).
"""},
            {"type": "heading", "level": 2, "text": "5) إصدار العقود (Contracts): قواعد التوافق"},
            {"type": "table", "head": ["التغيير", "الحكم", "الطريقة الآمنة"], "rows": [
                ["إضافة حقل اختياري للحدث", "✓ متوافق خلفيًا", "أضف بقيمة افتراضية؛ المستهلكون القدامى يتجاهلوه"],
                ["إضافة حدث جديد", "✓ متوافق", "المستهلك بيتجاهل الأنواع غير المعروفة (لا يفشل)"],
                ["إضافة endpoint جديد", "✓ متوافق", "—"],
                ["حذف حقل من الحدث", "✗ كاسر", "أوقف استخدامه أولًا (deprecated) → انتظر كل المستهلكين → احذف في إصدار جديد"],
                ["إعادة تسمية حقل", "✗ كاسر", "أضف الجديد، انسخ القيم في الاثنين، هاجِر المستهلكين، احذف القديم"],
                ["تغيير نوع حقل (int → string)", "✗ كاسر", "حقل جديد + فترة انتقال + upcasting"],
                ["تغيير دلالة حقل (السعر شامل الضريبة)", "✗✗ أخطر نوع (كسر صامت)", "حقل جديد باسم مختلف (`priceWithTax`) — لا تغيّر دلالة اسم موجود أبدًا"],
                ["تغيير مسار/اسم endpoint", "✗ كاسر", "إصدار مسار (`/v2/…`) ودعم الاثنين لفترة معلنة"],
                ["إضافة حالة جديدة لـenum", "△ خطر على المستهلكين", "المستهلك لازم يتعامل مع `default` (لا استثناء)"],
            ]},
            {"type": "code", "lang": "csharp", "title": "اختبار توافق العقد (يمنع الكسر في CI)", "code": r'''
/// <summary>
/// Contract test: يثبت إن الحدث المنشور **اليوم** لسه قابل للقراءة بالمستهلك القديم،
/// وإن شكل الـpayload ما اتغيرش تغييرًا كاسرًا (snapshot للعقد).
/// </summary>
[UsesVerify]                                  // Verify.Xunit
public class OrderPlacedContractTests
{
    /// <summary>إعدادات تسلسل ثابتة للعقد (ترتيب خصائص مستقر — عشان الـsnapshot يكون قابلًا للمقارنة).</summary>
    private static class ContractJson
    {
        public static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
        {
            WriteIndented = true,
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.Never,
        };
    }

    [Fact]
    public Task Payload_shape_is_unchanged()
    {
        var evt = new OrderPlaced(
            new OrderId(Guid.Parse("11111111-1111-1111-1111-111111111111")),
            Guid.Parse("22222222-2222-2222-2222-222222222222"),
            new Money(250.50m, "EGP"),
            new Address("12 Tahrir", "Cairo", "EG"),
            new DateTimeOffset(2026, 10, 22, 10, 0, 0, TimeSpan.Zero));

        // Verify بيحفظ snapshot معتمد؛ أي تغيير في الشكل يفشل الاختبار ويستدعي مراجعة
        return Verify(JsonSerializer.Serialize(evt, ContractJson.Options))
            .UseFileName("contracts/order.placed.v2");
    }

    [Fact]
    public void Old_consumer_can_read_current_payload()
    {
        // ★ نسخة قديمة من المستهلك (نوع v1) تقرأ الـpayload الحالي
        const string CurrentPayload = """
            {"orderId":"11111111-1111-1111-1111-111111111111","total":{"amount":250.50,"currency":"EGP"},
             "shippingAddress":{"line1":"12 Tahrir","city":"Cairo","country":"EG"},"occurredAt":"2026-10-22T10:00:00Z",
             "newFieldInV2":"whatever"}
            """;

        var v1 = JsonSerializer.Deserialize<OrderPlacedV1>(CurrentPayload, ContractJson.Options);

        v1.Should().NotBeNull();
        v1!.Total.Amount.Should().Be(250.50m);
        v1.ShippingAddress.City.Should().Be("Cairo");     // الحقول القديمة لسه موجودة بنفس الدلالة
    }

    [Fact]
    public void Unknown_enum_state_does_not_throw()
    {
        var act = () => JsonSerializer.Deserialize<ShipmentStatusHolder>(
            """{"status":"DRONE_DELIVERED"}""", ContractJson.Options);

        act.Should().NotThrow("المستهلك لازم يتعامل مع حالات جديدة من المزوّد");
    }

    private sealed record OrderPlacedV1(Guid OrderId, Money Total, AddressV1 ShippingAddress, DateTimeOffset OccurredAt);
    private sealed record AddressV1(string Line1, string City, string Country);
    private sealed record ShipmentStatusHolder(string Status);
}
'''},
            {"type": "checkpoints", "items": [
                "أرسم Bounded Contexts بأدلة (اللغة، churn، invariants، الملكية) وأوثق العلاقات في context map.",
                "أفرض ملكية البيانات فعليًا (schema/قاعدة لكل خدمة + صلاحيات + فحوصات على القاعدة).",
                "أختار نمط الوصول للبيانات بحسب الحاجة (نداء متزامن/نسخة محلية/تركيب/بحث/CDC/Saga) وأوثق اتساقه.",
                "أنفّذ Sagas بمنسّق صريح: خطوات idempotent، حالة محفوظة، مهلات، تعويض بالترتيب العكسي، وتنبيه عند فشل التعويض.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "خدمتان بتقرأا وتكتبا في نفس الجدول. التقييم؟",
                 "options": [
                     "كفاءة (بلا نداءات شبكة)",
                     "anti-pattern: اقتران كامل — أي تغيير مخطط يحتاج تنسيق نشر بين الخدمتين، وده يسلب كل ميزة للفصل",
                     "مسموح لو الخدمتان صغيرتان",
                     "يحتاج فهرسًا",
                 ], "answer": 1,
                 "explain": "البديل: مالك واحد للجدول + نداء عقد للقراءة الفورية أو نسخة محلية محدَّثة بالأحداث."},
                {"q": "خدمة الشحن محتاجة اسم المنتج وسعره مع كل شحنة. أفضل نمط؟",
                 "options": [
                     "join على جدول الكتالوج",
                     "نسخة محلية (snapshot) محدَّثة من أحداث الكتالوج + قراءة فورية عبر العقد عند الحاجة القصوى",
                     "نداء متزامن لكل شحنة",
                     "تخزينه في Redis مشترك",
                 ], "answer": 1,
                 "explain": "النسخة المحلية بتقلل الاقتران الزمني والزمن، بشرط: المالك واحد للبيانات الأصلية وخطة اتساق مكتوبة (ومنع تطبيق حدث أقدم)."},
                {"q": "ليه orchestration مفضل على choreography في أغلب الحالات؟",
                 "options": [
                     "أسرع",
                     "التدفق والحالات في مكان واحد → أسهل في الفهم والاختبار والتتبع ومعالجة الفشل والتعويض",
                     "بلا حاجة لأحداث",
                     "مطلب MassTransit",
                 ], "answer": 1,
                 "explain": "choreography أقصر في التدفقات البسيطة، لكن مع 4+ خطوات وتعويضات بيصير مستحيل التتبع («فين الوقفة؟»)."},
                {"q": "فشل إجراء التعويض (رد المبلغ) في saga. التصرف؟",
                 "options": [
                     "سجّل warning وكمل",
                     "تنبيه حرج + حالة `NeedsManual` + سجل كامل — ده معناه أموال/مخزون في حالة غير معروفة",
                     "أعد تشغيل الخدمة",
                     "احذف الـsaga",
                 ], "answer": 1,
                 "explain": "فشل التعويض أخطر من فشل الخطوة الأصلية. لازم يبقى ظاهر (تنبيه + لوحة + أداة معالجة يدوية)."},
                {"q": "خدمة غيّرت معنى `price` من «بدون ضريبة» لـ«شامل الضريبة» بلا تغيير الاسم. الحكم؟",
                 "options": [
                     "تغيير متوافق",
                     "أخطر أنواع الكسر (كسر صامت): المستهلكون القدامى هيحسبوا أرقامًا خاطئة بلا أي خطأ تقني",
                     "يحتاج فهرسًا",
                     "مسموح مع إصدار جديد",
                 ], "answer": 1,
                 "explain": "القاعدة: لا تغيّر دلالة اسم موجود. أضف `priceWithTax` وخلي الاثنين لفترة، وهاجِر المستهلكين."},
                {"q": "إيه دور Anti-Corruption Layer؟",
                 "options": [
                     "تشفير البيانات",
                     "ترجمة نموذج خدمة/نظام خارجي لنموذجك الداخلي — يمنع تسرب مفاهيمهم ويحصر تغييرهم في مكان واحد",
                     "منع الهجمات",
                     "ضغط الاستجابات",
                 ], "answer": 1,
                 "explain": "بدونه: `PriceMinorUnits` و`Status == \"ACTIVE\"` تنتشر في كل كودك، وأي تغيير عندهم يكسر 20 مكانًا."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "خريطة سياق + ملكية بيانات",
                 "md": "ارسم context map لنظامك (أو لمشروع المرحلة 4 كخدمات افتراضية): السياقات، اللغة الخاصة بكل واحد، نمط العلاقة بين كل زوجين، والمخزن المملوك. ثم طبّق ملكية البيانات فعليًا (schemas + صلاحيات + فحص انتهاكات).",
                 "criteria": [
                     "≥ 5 سياقات بجدول (اللغة/معنى «المنتج»/المالك/المخزن)",
                     "جدول العلاقات بنمط مسمى لكل زوج (7 أنماط معروفة)",
                     "قواعد لا تُكسر مكتوبة (4 قواعد على الأقل)",
                     "SQL يطبّق الصلاحيات ويكشف الانتهاكات (فحص `role_table_grants` + `pg_stat_statements`)",
                     "اختبار/فحص يثبت إن خدمة ما تقدرش تقرأ جداول خدمة تانية (محاولة مفترضة تفشل)",
                 ]},
                {"id": "t2", "title": "Saga واحد بتعويضات واختبارات فشل",
                 "md": "نفّذ saga لعمليه عبر خدمتين/موديولين (مثل: حجز مخزون → تحصيل → جدولة شحن) بمنسّق صريح وحالة محفوظة ومهلات وتعويضات. اختبر كل حالات الفشل.",
                 "criteria": [
                     "الحالة تُحفظ **قبل** كل نداء (اختبار: انهيار محاكى بعد النداء → الاستئناف صحيح)",
                     "كل خطوة idempotent (اختبار إعادة تنفيذ خطوة)",
                     "مهلة لكل خطوة + مهلة للـsaga (اختبار timeout → تعويض)",
                     "فشل خطوة وسطى → تعويض بالترتيب العكسي (اختبار يثبت نداء التعويضات)",
                     "فشل تعويض → حالة NeedsManual + تنبيه (اختبار)",
                     "مقياس لعدد الـsagas المكتملة/المعوَّضة/المعلقة",
                 ],
                 "hint": "لو اختبار الاستئناف صعب: اجعل المنسّق يبدأ من `CurrentStep` المحفوظة، وافحص في بداية كل خطوة «هل تمت فعلًا؟» عبر معرّف العملية (idempotency key)."},
            ]},
            {"type": "resources", "items": [
                {"label": "Microservices.io — Database per service", "url": "https://microservices.io/patterns/data/database-per-service.html"},
                {"label": "Saga pattern", "url": "https://microservices.io/patterns/data/saga.html"},
                {"label": "API Composition", "url": "https://microservices.io/patterns/data/api-composition.html"},
                {"label": "DDD — Context mapping (MS Learn)", "url": "https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice"},
                {"label": "Anti-corruption layer (Azure Architecture)", "url": "https://learn.microsoft.com/azure/architecture/patterns/anti-corruption-layer"},
                {"label": "Consumer-driven contract testing (Pact)", "url": "https://docs.pact.io/"},
                {"label": "Verify (snapshot testing)", "url": "https://github.com/VerifyTests/Verify"},
            ]},
        ],
    },
]
