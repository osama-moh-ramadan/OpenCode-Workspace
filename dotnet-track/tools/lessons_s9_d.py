# -*- coding: utf-8 -*-
"""Stage 9 — module 2 (part A): s9-m2-l1..l3 (تعقيد، هياكل، رسوم)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════
# l1 — التعقيد والمصفوفات والسلاسل والقواميس
# ══════════════════════════════════════════════════════════════════
_L1 = {
    "id": "s9-m2-l1",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "مقابلات .NET فيها شقّان: **السلوكي** (s10-m3) و**التقني**. الشق التقني فيه سؤال واحد لا يخطئه أحد: **«ما تعقيد الحل ده؟»** — ولذلك الدرس ده مش «خوارزميات للامتحان»، هو **أداة قياس** هتستخدمها في كل مراجعة كود بعد كده.\n\nالهدف العملي: تقرأ أي كود وتقول تعقيده في 10 ثوانٍ · وتحوّل حلًا O(n²) إلى O(n) بـ`Dictionary` · وتقلّل التخصيصات بـ`Span<T>`."},

        {"type": "terms", "title": "المصطلحات الأساسية", "items": [
            {"term": "Big-O", "def": "الحد الأعلى لنمو الزمن/الذاكرة مع حجم المدخل. نتجاهل الثوابت: O(2n) = O(n)."},
            {"term": "Amortized", "def": "متوسط التكلفة على مدى عمليات كثيرة. `List.Add` = O(1) amortized رغم أن بعض الإضافات O(n) عند التوسيع."},
            {"term": "Space complexity", "def": "ذاكرة إضافية نسبية للمدخل. O(1) = بلا بنية جديدة · O(n) = قاموس/قائمة مساعدة."},
            {"term": "Hash collision", "def": "مفتاحان بنفس الـhash → تعارض. في .NET يُحلّ بالسلاسل/العنونة المفتوحة، والبحث يتدهور إلى O(n) في أسوأ حالة."},
            {"term": "Dictionary<TKey,TValue>", "def": "خريطة hash: إدراج/بحث O(1) متوسط. مهم: **تُثبِّت ترتيبًا غير مضمون** — لا تعتمد على الترتيب."},
            {"term": "HashSet<T>", "def": "مجموعة بلا تكرار، O(1) للاحتوائية (`Contains`) — أداة «هل رأيت هذا؟»."},
            {"term": "Span<T> / ReadOnlySpan<T>", "def": "نافذة على ذاكرة موجودة بلا نسخ (stack/array/string). أساس تقليل التخصيصات في .NET الحديث."},
            {"term": "StringBuilder", "def": "بناء سلاسل متغير الطول بـO(1) amortized للإضافة بدل O(n) لكل `+`."},
            {"term": "Two-pointer", "def": "مؤشران يتحركان على مصفوفة/سلسلة — يحوّل مسائل O(n²) إلى O(n) عندما يكون الترتيب متاحًا."},
            {"term": "Prefix sums", "def": "مصفوفة تراكمية: مجموع أي نطاق = `pre[r] - pre[l]` بـO(1) بعد O(n) بناء."},
            {"term": "In-place", "def": "تعديل نفس المصفوفة بذاكرة O(1) — يُطلب كثيرًا في المقابلات."},
            {"term": "Off-by-one", "def": "أشهر سبب فشل: حدود الحلقة `i < n` مقابل `i <= n`، أو نطاق `[l, r)` مقابل `[l, r]`."},
        ]},

        {"type": "heading", "level": 2, "text": "① جدول التعقيدات اللي لازم تكون تلقائيًا"},
        {"type": "table", "caption": "مرجع سريع — .NET 10",
         "head": ["العملية", "البنية", "متوسط", "أسوأ حالة", "ملاحظة"],
         "rows": [
             ["وصول بفهرس", "`T[]` / `List<T>`", "O(1)", "O(1)", "—"],
             ["بحث خطي", "`T[]`", "O(n)", "O(n)", "استخدمه فقط للمجموعات الصغيرة (< 20)"],
             ["بحث ثنائي", "مصفوفة مرتّبة", "O(log n)", "O(log n)", "`Array.BinarySearch` أو `span.BinarySearch`"],
             ["إدراج في الوسط", "`List<T>`", "O(n)", "O(n)", "الانزياح هو التكلفة — استخدم `LinkedList` نادرًا فقط"],
             ["إضافة في النهاية", "`List<T>`", "O(1) amortized", "O(n) عند التوسيع", "اضبط السعة مسبقًا لو تعرف الحجم"],
             ["بحث بمفتاح", "`Dictionary`", "O(1)", "O(n)", "الأسوأ عند تعارض hash سيئ"],
             ["احتوائية", "`HashSet`", "O(1)", "O(n)", "—"],
             ["أصغر/أكبر", "`SortedSet`/`PriorityQueue`", "O(log n)", "O(log n)", "PriorityQueue في .NET جاهزة (heap)"],
             ["إضافة/حذف بالطرفين", "`LinkedList`/`Deque` يدوي", "O(1)", "O(1)", "لكن الوصول بالوسط O(n)"],
             ["تجميع", "`GroupBy` LINQ", "O(n)", "O(n)", "تخصيصات أعلى من حلقة يدوية — قِس"],
         ]},
        {"type": "callout", "kind": "tip", "title": "كيف تحسب في 10 ثوانٍ",
         "md": "**①** هل فيه حلقة داخل حلقة على نفس `n`؟ → O(n²).\n**②** هل تنصّف المشكلة في كل خطوة؟ → O(log n).\n**③** هل كل عنصر يُزار مرة واحدة؟ → O(n).\n**④** هل الترتيب (`Array.Sort`) قبل أي شيء؟ → أضف O(n log n) وهي غالبًا المهيمنة.\n**⑤** اذكر الذاكرة أيضًا: `Dictionary` بـn عنصر = O(n) مساحة."},

        {"type": "heading", "level": 2, "text": "② من O(n²) إلى O(n): الحالة الكلاسيكية"},
        {"type": "code", "lang": "csharp", "title": "TwoSum — ثلاث درجات تحسّن، بنفس الواجهة", "filename": "Algorithms/TwoSum.cs", "code": r'''public static class TwoSum
{
    // ── ① ساذج: O(n²) زمن · O(1) مساحة ───────────────────────────
    public static (int, int)? Naive(int[] nums, int target)
    {
        for (var i = 0; i < nums.Length; i++)
        for (var j = i + 1; j < nums.Length; j++)
            if (nums[i] + nums[j] == target) return (i, j);
        return null;
    }

    // ── ② مرتب: O(n log n) زمن (فرز) · O(1) مساحة — مؤشران ──────
    public static bool Sorted(int[] nums, int target)
    {
        Array.Sort(nums);
        int l = 0, r = nums.Length - 1;
        while (l < r)
        {
            var sum = nums[l] + nums[r];
            if (sum == target) return true;
            if (sum < target) l++;      // نحتاج أكبر
            else r--;                    // نحتاج أصغر
        }
        return false;
    }

    // ── ③ hash: O(n) زمن · O(n) مساحة — الحل المطلوب غالبًا ─────
    public static (int, int)? OnePass(int[] nums, int target)
    {
        var seen = new Dictionary<int, int>(capacity: nums.Length);
        for (var i = 0; i < nums.Length; i++)
        {
            var need = target - nums[i];
            if (seen.TryGetValue(need, out var j)) return (j, i);
            seen[nums[i]] = i;           // نسجّل بعد الفحص (يمنع استخدام نفس العنصر مرتين)
        }
        return null;
    }
}

/*
 المقايضة في سطر:
   n = 10,000 → Naive ≈ 50 مليون مقارنة · OnePass ≈ 10,000 عملية hash.
   الثمن: قاموس بحجم n (≈ 40–80 بايت/عنصر) — وهذا مقبول.
   القاعدة: نضحي بمساحة O(n) لنشتري زمنًا O(n) إلا لو الذاكرة مقيّدة صراحةً.
*/'''},
        {"type": "code", "lang": "csharp", "title": "Span<T> — نفس الحل بلا تخصيص (نسخة إنتاجية)", "filename": "Algorithms/SpanBasics.cs", "code": r'''using System.Buffers;

public static class SpanBasics
{
    /// <summary>بحث ثنائي على Span: بلا نسخ وبلا LINQ.</summary>
    public static int BinarySearch(ReadOnlySpan<int> sorted, int target)
    {
        var lo = 0;
        var hi = sorted.Length - 1;
        while (lo <= hi)
        {
            var mid = lo + ((hi - lo) >> 1);     // لا (lo+hi)/2 — يمنع overflow
            var v = sorted[mid];
            if (v == target) return mid;
            if (v < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return ~lo;                              // نقطة الإدراج (نفس دلالة Array.BinarySearch)
    }

    /// <summary>عدّ الكلمات في سطر طويل — بلا `Split` (الذي يخصّص مصفوفة + سلاسل).</summary>
    public static int CountWords(ReadOnlySpan<char> text)
    {
        var count = 0;
        var inWord = false;
        foreach (var c in text)
        {
            if (char.IsWhiteSpace(c)) { inWord = false; }
            else if (!inWord) { inWord = true; count++; }
        }
        return count;
    }

    /// <summary>قلب جزء من مصفوفة في المكان (in-place) — أساس reverse words.</summary>
    public static void Reverse(Span<char> span)
    {
        for (int i = 0, j = span.Length - 1; i < j; i++, j--)
            (span[i], span[j]) = (span[j], span[i]);
    }

    /// <summary>معالجة سطر ضخم من الشبكة بلا تخصيص كامل — مثال واقعي.</summary>
    public static int CountDelimiter(Stream utf8Stream, byte delimiter, int bufferSize = 4096)
    {
        var buffer = ArrayPool<byte>.Shared.Rent(bufferSize);
        try
        {
            var total = 0;
            int read;
            while ((read = utf8Stream.Read(buffer, 0, buffer.Length)) > 0)
            {
                var span = buffer.AsSpan(0, read);
                foreach (var b in span)
                    if (b == delimiter) total++;
            }
            return total;
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);   // ✅ لا تنسَ الإرجاع
        }
    }
}'''},
        {"type": "table", "caption": "أين تُستخدم Span فعليًا في الشغل اليومي",
         "head": ["الحالة", "قبل", "بعد", "المكسب"],
         "rows": [
             ["`Substring` في حلقة", "تخصيص سلسلة لكل جزء", "`ReadOnlySpan<char>` + `Slice`", "صفر تخصيص"],
             ["تحليل CSV/سجل ضخم", "`Split(',')`", "المسح بـSpan", "ذاكرة أقل 5–10×"],
             ["معالجة bytes من الشبكة", "`byte[]` جديد لكل قراءة", "`ArrayPool` + `Span`", "تقليل GC pressure"],
             ["تحويل رقم من نص", "`int.Parse(s.Substring(1))`", "`int.Parse(s.AsSpan(1))`", "صفر تخصيص"],
         ]},
        {"type": "callout", "kind": "warn", "title": "أخطاء Span الشائعة",
         "md": "**① `Span<T>` لا يمكن تخزينه في حقل** من class (struct فقـط و`ref struct` — لا يُعبّئ الـheap).\n**② `async` + `Span` = خطأ ترجمة** — استخدم `Memory<T>` في الدوال غير المتزامنة.\n**③ `stackalloc` حجمه محدود** — لا تخصص به حجمًا من مدخل مستخدم (StackOverflow).\n**④ نسيان إرجاع `ArrayPool`** — تسريب دائم يظهر كاستهلاك ذاكرة متزايد.\n**⑤ `Span` ليس آمنًا بعد انتهاء صلاحية الذاكرة الأصلية** — لا ترجعه من دالة كمرجع لذاكرة محلية."},

        {"type": "heading", "level": 2, "text": "③ السلاسل: 4 أخطاء أداء شائعة"},
        {"type": "code", "lang": "csharp", "title": "Strings/StringPitfalls.cs — قبل/بعد", "filename": "Algorithms/StringPitfalls.cs", "code": r'''using System.Text;

public static class StringPitfalls
{
    // ❌ O(n²): كل `+=` ينسخ السلسلة كاملة
    public static string BuildBad(IEnumerable<string> parts)
    {
        var s = "";
        foreach (var p in parts) s += p;
        return s;
    }

    // ✅ O(n): StringBuilder بسعة مبدئية
    public static string BuildGood(IReadOnlyList<string> parts)
    {
        var sb = new StringBuilder(capacity: parts.Sum(p => p.Length));
        foreach (var p in parts) sb.Append(p);
        return sb.ToString();
    }

    // ✅ أفضل عندما يكون المصدر مصفوفة: تخصيص واحد فقط
    public static string JoinGood(string[] parts) => string.Concat(parts);

    // ❌ مقارنة بلا وعي بالحالة/الثقافة في بيانات تقنية
    public static bool CompareBad(string a, string b) => a.ToLower() == b.ToLower();

    // ✅ مقارنة صريحة (ثقافة ثابتة + تجاهل الحالة) — أسرع وبلا تخصيص
    public static bool CompareGood(string a, string b) =>
        string.Equals(a, b, StringComparison.OrdinalIgnoreCase);

    // ❌ التحقق من الفراغ بطريقة فضفاضة
    public static bool BlankBad(string? s) => s == null || s.Trim().Length == 0;

    // ✅ بلا تخصيص
    public static bool BlankGood(string? s) => string.IsNullOrWhiteSpace(s);

    // ❌ `Split` ثم معالجة جزء واحد
    public static string FirstTokenBad(string line) => line.Split(',')[0];

    // ✅ Span: بلا مصفوفة وسيطة
    public static ReadOnlySpan<char> FirstToken(ReadOnlySpan<char> line)
    {
        var idx = line.IndexOf(',');
        return idx < 0 ? line : line[..idx];
    }

    // ✅ قلب كلمات بلا `Split` — O(n) زمن · O(1) مساحة إضافية
    public static string ReverseWords(string s)
    {
        var arr = s.ToCharArray().AsSpan();
        SpanBasics.Reverse(arr);                       // اقلب كل شيء
        var start = 0;
        for (var i = 0; i <= arr.Length; i++)
        {
            if (i == arr.Length || arr[i] == ' ')
            {
                SpanBasics.Reverse(arr[start..i]);      // اقلب كل كلمة
                start = i + 1;
            }
        }
        return new string(arr);
    }
}

/*
 ملاحظة: `string.Concat(string[])` يحسب الطول الكلي مرة واحدة ويخصص سلسلة واحدة —
 أسرع من `StringBuilder` عندما تكون الأجزاء كلها متاحة في مصفوفة.
*/'''},
        {"type": "table", "caption": "قواعد سريعة للسلاسل",
         "head": ["القاعدة", "السبب"],
         "rows": [
             ["`+=` في حلقة = ❌", "كل إضافة تُنشئ سلسلة جديدة O(n) — O(n²) إجمالًا"],
             ["قارن بـ`StringComparison.Ordinal` للبيانات", "أسرع وأصح لمعرّفات/مفاتيح (لا قواعد لغوية)"],
             ["استخدم `OrdinalIgnoreCase` لا `ToLower()`", "بلا تخصيص + بلا فروق ثقافية"],
             ["`StringBuilder` لما العدد غير معروف", "تخصيصات أقل ونمو أسّي للسعة"],
             ["`Span` لما الجزء صغير ومؤقت", "صفر تخصيص"],
             ["`StringComparison.CurrentCulture` للنصوص للمستخدم فقط", "لغة/حروف عربية تحتاج مقارنة ثقافية"],
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تحسب تعقيد كود موجود (زمن + مساحة) بلا تشغيله.",
            "تعرف متوسط/أسوأ حالة في `Dictionary` وتشرح سبب الأسوأ.",
            "تحوّل بحثًا مزدوجًا إلى `Dictionary`/`HashSet` وتبيّن ثمن المساحة.",
            "تستخدم مؤشرين على مصفوفة مرتّبة وتشرح لماذا ينجح.",
            "تكتب `Span`/`ReadOnlySpan` بلا `Substring` ولا `Split`.",
            "تعرف قيود `Span` (لا حقول، لا `async`، `stackalloc` محدود).",
            "تستخدم `ArrayPool` وتُرجع المخزن في `finally`.",
            "تفرّق بين `Ordinal` و`CurrentCulture` في المقارنات.",
            "تضبط `capacity` مسبقًا في `List`/`StringBuilder` عند معرفة الحجم.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة — حساب سريع وأخطاء شائعة.",
         "questions": [
             {"q": "`Dictionary` بحث بمفتاح — ما أسوأ تعقيد؟",
              "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
              "answer": 2,
              "explain": "المتوسط O(1) لكن عند تعارض hash متكرر (دالة hash سيئة أو هجوم مقصود) تتحول السلسلة إلى بحث خطي O(n). .NET الحديث فيه حماية من hash flooding، لكن المبدأ صحيح."},
             {"q": "لماذا `s += x` في حلقة تعتبر O(n²)؟",
              "options": ["لأن `+` بطيء", "لأن كل إضافة تُنشئ سلسلة جديدة وتنسخ المحتوى الحالي — مجموع الأطوال = 1+2+…+n",
                          "لأن السلاسل غير قابلة للتغيير فقط", "لأسباب GC"],
              "answer": 1,
              "explain": "النسخ التراكمي هو المشكلة: 10 آلاف قطعة = ~50 مليون نسخة محرف. الحل `StringBuilder` (سعة متزايدة) بزمن O(n)."},
             {"q": "`List<T>.Add` — ما التعقيد؟",
              "options": ["O(1) دائمًا", "O(1) amortized مع O(n) عند التوسيع", "O(n) دائمًا", "O(log n)"],
              "answer": 1,
              "explain": "السعة تتضاعف عند الامتلاء (نسخ O(n)) وتحدث نادرًا، فالمتوسط O(1). لو تعرف الحجم، مرّر `capacity` لتجنب النسخ."},
             {"q": "أي حالة لا يصح فيها استخدام `Span<T>`؟",
              "options": ["داخل دالة متزامنة", "كحقل في class، أو داخل `async` (استخدم `Memory<T>`)",
                          "مع المصفوفات", "مع `stackalloc`"],
              "answer": 1,
              "explain": "`Span<T>` هو `ref struct`: لا يُعبّأ في الـheap فيمنع أن يكون حقلًا في class، ولا يمر عبر `await`. الحل في الشيفرة غير المتزامنة: `Memory<T>`/`ReadOnlyMemory<T>`."},
             {"q": "لماذا `Ordinal` أفضل من `CurrentCulture` لمقارنة المفاتيح؟",
              "options": ["أدق لغويًا", "مقارنة بايت/محرف مباشرة: أسرع وحتمية، ولا تخلط قواعد لغوية في بيانات تقنية",
                          "لأن الثقافة لا تعمل مع العربية", "لأنها أبطأ لكن أصح"],
              "answer": 1,
              "explain": "المفاتيح والمعرّفات ليست نصًا للمستخدم. `Ordinal` حتمي وسريع. `CurrentCulture` يُستخدم لعرض/فرز النصوص للمستخدم فقط (وحتى هناك قد تحتاج `InvariantCulture` للثبات)."},
             {"q": "ما أفضل تحسين لـ«هل يحتوي هذا الاسم على تكرار؟»",
              "options": ["`List.Contains`", "`HashSet<string>`", "ترتيب ثم بحث ثنائي", "`IndexOf`"],
              "answer": 1,
              "explain": "`HashSet.Add` ترجع false عند التكرار بزمن O(1) متوسط — أسرع من O(n²) في `List.Contains`. الترتيب O(n log n) أقل كفاءة."},
             {"q": "متى تختار الحل O(n log n) على O(n) بمساحة O(n)؟",
              "options": ["أبدًا", "عندما تكون الذاكرة مقيّدة (مثلًا معالجة ملايين العناصر في بيئة محدودة)",
                          "دائمًا", "عندما تكون n صغيرة فقط"],
              "answer": 1,
              "explain": "المقايضة الحقيقية: زمن مقابل مساحة. لو الذاكرة مقيّدة (حاوية 512MB، دفعة كبيرة) فالفرز في المكان أفضل رغم الزمن الأعلى. القرار يُكتب صراحة."},
             {"q": "ما الخطر في `stackalloc` بحجم من مدخل المستخدم؟",
              "options": ["بطء", "StackOverflow وانهيار العملية — المكدس محدود (غالبًا 1MB)",
                          "تسريب ذاكرة", "خطأ ترجمة"],
              "answer": 1,
              "explain": "`stackalloc` يخصص على مكدس الخيط. حجم كبير/متغيّر = انهيار فوري غير قابل للالتقاط. القاعدة: حجم ثابت صغير (`<= 256` بايت تقريبًا)، وإلا `ArrayPool`."},
         ]},

        {"type": "tasks", "title": "مهمة واحدة", "intro": "تحسين حقيقي بالقياس.",
         "items": [
            {"id": "s9-m2-l1-t1",
             "title": "حوّل دالة O(n²) إلى O(n) وقِس",
             "md": "خُذ دالة من مشروعك (أو من الكود أعلاه) فيها حلقة داخل حلقة، وحسّنها بـ`Dictionary`/`HashSet` أو مؤشرين. قِس الزمن بـ`Stopwatch` أو BenchmarkDotNet على أحجام 1k/10k/100k.",
             "criteria": [
                 "بيان التعقيد قبل وبعد مكتوب (زمن + مساحة) مع التبرير.",
                 "ثلاثة أحجام قياس على الأقل + جدول نتائج (ms) ونسبة التسريع.",
                 "اختبارات تكافؤ: 10 حالات على الأقل (بما فيها مدخل فارغ، عنصر واحد، تكرارات).",
                 "نسخة ثانية بـ`Span`/`StringBuilder` لو العملية على نصوص — مع قياس التخصيصات (`GC.GetAllocatedBytesForCurrentThread`).",
                 "ملاحظة مكتوبة عن المقايضة: ماذا دفعت من مساحة مقابل الزمن.",
             ],
             "hint": "استخدم `Stopwatch` مع تسخين (warm-up) قبل القياس، أو BenchmarkDotNet لو محتاج دقة. وللتحقق من التكافؤ، اكتب اختبارًا يقارن النتيجة القديمة بالجديدة على مدخلات عشوائية — أسرع طريقة لكشف خطأ off-by-one.",
             "solution": "النتيجة النموذجية: تحسّن 50–500× عند n = 10k، مع زيادة ذاكرة خطية. الأهم: تكتشف أن بعض الحالات (n صغير) لا تتحسن أصلًا — فالتحسين الحقيقي هو **قرار مبني على قياس** لا على حدس.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.diagnostics.stopwatch",
                 "https://learn.microsoft.com/dotnet/standard/memory-and-spans/memory-t-usage-guidelines",
                 "https://benchmarkdotnet.org/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Memory<T> وSpan<T> — إرشادات", "url": "https://learn.microsoft.com/dotnet/standard/memory-and-spans/memory-t-usage-guidelines"},
            {"label": "StringComparison best practices", "url": "https://learn.microsoft.com/dotnet/standard/base-types/best-practices-strings"},
            {"label": "Dictionary<TKey,TValue>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.dictionary-2"},
            {"label": "BenchmarkDotNet", "url": "https://benchmarkdotnet.org/"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════
# l2 — القوائم والمكدسات والطوابير والأشجار
# ══════════════════════════════════════════════════════════════════
_L2 = {
    "id": "s9-m2-l2",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الدرس ده بيغطي **الهياكل اللي تُسأل فعليًا** في مقابلات .NET: مكدس، طابور، قائمة مرتبطة، شجرة ثنائية (بحث + اجتياز). وفي كل هيكل: التنفيذ اليدوي (مطلوب في المقابلة) + النسخة الإنتاجية من .NET (اللي تستخدمها في الشغل).\n\n**الفرق بين الاتنين هو الفرق بين Junior وSenior**: تعرف تنفّذ يدويًا لتشرح المبدأ، وتستخدم `Stack<T>`/`PriorityQueue` في الإنتاج لأنها مختبرة وأسرع."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Stack (LIFO)", "def": "آخر داخل أول خارج: `Push`/`Pop`/`Peek` بـO(1). الاستخدامات: undo · تراجع DFS · تقييم تعبيرات · call stack."},
            {"term": "Queue (FIFO)", "def": "أول داخل أول خارج: `Enqueue`/`Dequeue` بـO(1). الاستخدامات: BFS · معالجة مهام · مخازن مؤقتة."},
            {"term": "Deque", "def": "طابور ثنائي الطرفين — إضافة/حذف من الطرفين O(1). .NET ليس فيه `Deque<T>` جاهز؛ يُبنى بـ`LinkedList` أو مصفوفة دائرية."},
            {"term": "Linked List", "def": "عقد تشير لبعضها: إدراج/حذف O(1) عند معرفة العقدة، لكن الوصول O(n) وذاكرة أعلى (مؤشرات)."},
            {"term": "BST (شجرة بحث ثنائية)", "def": "كل يسار أصغر وكل يمين أكبر: بحث/إدراج/حذف O(h) حيث h ارتفاع الشجرة (O(log n) متوازنة، O(n) منحرفة)."},
            {"term": "Traversal", "def": "اجتياز الشجرة: **In-order** (يسار، جذر، يمين → مرتبة في BST) · Pre-order (جذر أولًا → تسلسل) · Post-order (جذر أخيرًا → حذف/تقييم) · Level-order (BFS بطابور)."},
            {"term": "Height vs Depth", "def": "الارتفاع = أطول مسار من الجذر لورقة · العمق = المسافة من الجذر لعقدة معينة."},
            {"term": "Balanced tree", "def": "شجرة تحفظ الارتفاع O(log n) (AVL/Red-Black). `SortedDictionary` في .NET = شجرة أحمر-أسود."},
            {"term": "Heap / PriorityQueue", "def": "شجرة ثنائية كاملة بقاعدة ترتيب جزئي: `Peek` O(1) و`Enqueue`/`Dequeue` O(log n). مثالية لـ«أهم/أرخص عنصر الآن»."},
            {"term": "Monotonic stack", "def": "مكدس يحفظ ترتيبًا رتيبًا — يحل مسائل «العنصر الأكبر التالي» و«أكبر مستطيل» بـO(n)."},
            {"term": "Ring buffer", "def": "مصفوفة دائرية ثابتة السعة للطوابير عالية المعدل — بلا تخصيص لكل عنصر."},
            {"term": "Null ref في الشجرة", "def": "أشهر مصدر `NullReferenceException`: عدم فحص `node.Left/Right` قبل التكرار — والاجتياز العودي يجب أن يبدأ بشرط الخروج."},
        ]},

        {"type": "heading", "level": 2, "text": "① المكدس والطابور: التنفيذ + الاستخدام الصحيح"},
        {"type": "code", "lang": "csharp", "title": "Structures/StackAndQueue.cs — تنفيذ يدوي بمصفوفة (سريع، بلا LinkedList)", "filename": "Algorithms/StackAndQueue.cs", "code": r'''using System.Runtime.CompilerServices;

/// <summary>مكدس على مصفوفة نامية — نفس فكرة Stack<T> الداخلي.</summary>
public sealed class IntStack
{
    private int[] _items = new int[16];
    public int Count { get; private set; }
    public bool IsEmpty => Count == 0;

    public void Push(int value)
    {
        if (Count == _items.Length) Array.Resize(ref _items, _items.Length * 2);
        _items[Count++] = value;
    }

    public int Pop()
    {
        if (Count == 0) throw new InvalidOperationException("المكدس فارغ");
        var v = _items[--Count];
        _items[Count] = 0;            // يمنع احتجاز مراجع (مهم للأنواع المرجعية)
        return v;
    }

    public int Peek() => Count > 0 ? _items[Count - 1]
        : throw new InvalidOperationException("المكدس فارغ");
}

/// <summary>طابور على مصفوفة دائرية — Dequeue بـO(1) بلا إزاحة.</summary>
public sealed class IntQueue
{
    private int[] _items = new int[16];
    private int _head;          // موضع أول عنصر
    private int _count;

    public int Count => _count;
    public bool IsEmpty => _count == 0;

    public void Enqueue(int value)
    {
        if (_count == _items.Length) Grow();
        _items[(_head + _count) % _items.Length] = value;
        _count++;
    }

    public int Dequeue()
    {
        if (_count == 0) throw new InvalidOperationException("الطابور فارغ");
        var v = _items[_head];
        _items[_head] = 0;
        _head = (_head + 1) % _items.Length;
        _count--;
        return v;
    }

    private void Grow()
    {
        var next = new int[_items.Length * 2];
        for (var i = 0; i < _count; i++) next[i] = _items[(_head + i) % _items.Length];
        _items = next;
        _head = 0;
    }
}

/// <summary>أشهر سؤال مكدس: أقواس متوازنة — O(n).</summary>
public static class BracketValidator
{
    public static bool IsValid(ReadOnlySpan<char> s)
    {
        Span<char> stack = stackalloc char[Math.Min(s.Length, 256)];
        var top = 0;

        foreach (var c in s)
        {
            switch (c)
            {
                case '(' or '[' or '{':
                    if (top == stack.Length) return false;   // عمق أكبر من الحد
                    stack[top++] = c;
                    break;
                case ')' when top > 0 && stack[top - 1] == '(':
                case ']' when top > 0 && stack[top - 1] == '[':
                case '}' when top > 0 && stack[top - 1] == '{':
                    top--;
                    break;
                case ')' or ']' or '}':
                    return false;                             // إغلاق بلا فتح مطابق
            }
        }
        return top == 0;
    }
}'''},
        {"type": "table", "caption": "متطلبات تصميم صحيحة",
         "head": ["السؤال", "الجواب", "السبب"],
         "rows": [
             ["`Stack<T>` أم `List<T>` كبديل؟", "`Stack<T>`", "واجهة واضحة تمنع العبث بالوسط + أداء مماثل"],
             ["`Queue<T>` على `List<T>` + `RemoveAt(0)`؟", "❌ أبدًا", "`RemoveAt(0)` = O(n) إزاحة لكل عنصر"],
             ["`LinkedList<T>` لـqueue؟", "لا للحالات العادية", "تخصيص عقدة لكل عنصر؛ `Queue<T>` أسرع وأقل ذاكرة"],
             ["`ConcurrentQueue<T>` متى؟", "عند تعدد كتابة/قراءة", "آمن بلا أقفال يدوية؛ وإلا فالسرعة أقل"],
             ["هل `Queue<T>` بالخيط الآمن؟", "لا", "يحتاج قفلًا أو `ConcurrentQueue`/`Channel<T>`"],
         ]},
        {"type": "callout", "kind": "tip", "title": "في الإنتاج: `Channel<T>` لا `Queue<T>`",
         "md": "لو عايز طابور بين منتج ومستهلك داخل العملية، فـ`System.Threading.Channels.Channel<T>` هو الخيار الصحيح: حدود سعة (backpressure) · انتظار غير متزامن (`ReadAllAsync`) · إغلاق نظيف · أداء عالٍ.\n`ConcurrentQueue` مناسبة لتبادل بسيط بلا انتظار؛ `Queue` العادية ليست آمنة للخيوط."},
        {"type": "code", "lang": "csharp", "title": "Structures/ChannelExample.cs — backpressure حقيقي", "filename": "Algorithms/ChannelExample.cs", "code": r'''using System.Threading.Channels;

public sealed class BoundedPipeline
{
    private readonly Channel<WorkItem> _channel = Channel.CreateBounded<WorkItem>(
        new BoundedChannelOptions(capacity: 1_000)
        {
            FullMode = BoundedChannelFullMode.Wait,   // المنتج ينتظر بدل فقدان بيانات
            SingleReader = true,
            SingleWriter = false,
        });

    public ValueTask ProduceAsync(WorkItem item, CancellationToken ct) =>
        _channel.Writer.WriteAsync(item, ct);

    public async Task ConsumeAllAsync(Func<WorkItem, CancellationToken, Task> handle, CancellationToken ct)
    {
        await foreach (var item in _channel.Reader.ReadAllAsync(ct))
            await handle(item, ct);
    }

    public void Complete() => _channel.Writer.TryComplete();
}

public sealed record WorkItem(string Id, string Payload);

/*
 لماذا `BoundedChannelFullMode.Wait`؟
   لو المنتج أسرع من المستهلك، الطابور غير المحدود ينمو حتى يستهلك الذاكرة (OOM).
   الانتظار يعطي backpressure حقيقيًا — وهو الأصح للأنظمة التي تعرف سقف قدرتها.
*/'''},

        {"type": "heading", "level": 2, "text": "② القائمة المرتبطة: متى تستحق فعلًا؟"},
        {"type": "table", "caption": "المقارنة (n = 100,000)",
         "head": ["العملية", "`List<T>`", "`LinkedList<T>`", "الحكم"],
         "rows": [
             ["إضافة للنهاية", "O(1) amortized", "O(1)", "تعادل"],
             ["إدراج/حذف في الوسط", "O(n) (إزاحة)", "O(1) لو العقدة معروفة", "LinkedList أفضل **فقط** مع مرجع للعقدة"],
             ["الوصول بالفهرس", "O(1)", "O(n)", "List أفضل بكثير"],
             ["ذاكرة لكل عنصر", "~4–8 بايت", "~32+ بايت (Node + مؤشرات)", "List أفضل 4×"],
             ["توافق مع GC", "ممتاز (مصفوفة متصلة)", "سيئ (عقد مبعثرة)", "List أفضل للأداء العام"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Structures/LruCache.cs — الحالة الوحيدة اللي LinkedList تستحق فيها", "filename": "Algorithms/LruCache.cs", "code": r'''/// <summary>
/// LRU Cache = Dictionary + LinkedList — O(1) لكل عملية.
/// هنا LinkedList ضرورية: نحتاج حذف عقدة **بمرجع** بلا بحث.
/// </summary>
public sealed class LruCache<TKey, TValue> where TKey : notnull
{
    private readonly int _capacity;
    private readonly Dictionary<TKey, LinkedListNode<Entry>> _map;
    private readonly LinkedList<Entry> _order = new();   // الأحدث في الرأس

    public LruCache(int capacity)
    {
        if (capacity <= 0) throw new ArgumentOutOfRangeException(nameof(capacity));
        _capacity = capacity;
        _map = new Dictionary<TKey, LinkedListNode<Entry>>(capacity);
    }

    public TValue? Get(TKey key)
    {
        if (!_map.TryGetValue(key, out var node)) return default;

        // انقله للرأس لأنه صار «مستخدمًا حديثًا»
        _order.Remove(node);
        _order.AddFirst(node);
        return node.Value.Value;
    }

    public void Set(TKey key, TValue value)
    {
        if (_map.TryGetValue(key, out var node))
        {
            node.Value = node.Value with { Value = value };
            _order.Remove(node);
            _order.AddFirst(node);
            return;
        }

        if (_map.Count == _capacity)
        {
            var lru = _order.Last!;          // الأقدم
            _order.RemoveLast();
            _map.Remove(lru.Value.Key);
        }

        var added = _order.AddFirst(new Entry(key, value));
        _map[key] = added;
    }

    private readonly record struct Entry(TKey Key, TValue Value);
}'''},
        {"type": "callout", "kind": "note", "title": "متى تستخدم `LinkedList` في الإنتاج",
         "md": "**①** محتاج مرجع عقدة صريح (LRU · قوائم تشغيل) · **②** إدخال/حذف متكرر في الوسط **وأنت تملك العقدة** · **③** دمج قوائم.\nغير ذلك: `List<T>` أفضل في كل شيء تقريبًا (تجمّع الذاكرة وأداء الـcache).\n**قاعدة:** لو مش عارف ليه تستخدم LinkedList، فأنت مش محتاجها."},

        {"type": "heading", "level": 2, "text": "③ الشجرة الثنائية: البحث والاجتياز"},
        {"type": "code", "lang": "csharp", "title": "Trees/BinaryTree.cs — إدراج + 4 اجتيازات + عمليات كلاسيكية", "filename": "Algorithms/BinaryTree.cs", "code": r'''public sealed class TreeNode(int value)
{
    public int Value { get; init; } = value;
    public TreeNode? Left { get; set; }
    public TreeNode? Right { get; set; }
}

public sealed class BinarySearchTree
{
    public TreeNode? Root { get; private set; }

    // ── إدراج متكرر: O(h) ──────────────────────────────────────────
    public void Insert(int value) => Root = Insert(Root, value);

    private static TreeNode Insert(TreeNode? node, int value)
    {
        if (node is null) return new TreeNode(value);
        if (value < node.Value) node.Left = Insert(node.Left, value);
        else if (value > node.Value) node.Right = Insert(node.Right, value);
        return node;                       // القيمة موجودة ⇒ لا تكرار
    }

    public bool Contains(int value)
    {
        var node = Root;
        while (node is not null)                 // بلا عودية: أقل ثابتًا وآمن
        {
            if (value == node.Value) return true;
            node = value < node.Value ? node.Left : node.Right;
        }
        return false;
    }

    // ── الاجتيازات ────────────────────────────────────────────────
    public List<int> InOrder()   { var r = new List<int>(); InOrder(Root, r); return r; }
    public List<int> PreOrder()  { var r = new List<int>(); PreOrder(Root, r); return r; }
    public List<int> PostOrder() { var r = new List<int>(); PostOrder(Root, r); return r; }

    private static void InOrder(TreeNode? n, List<int> acc)
    {
        if (n is null) return;               // ✅ شرط الخروج أولًا
        InOrder(n.Left, acc);
        acc.Add(n.Value);
        InOrder(n.Right, acc);
    }

    private static void PreOrder(TreeNode? n, List<int> acc)
    {
        if (n is null) return;
        acc.Add(n.Value);
        PreOrder(n.Left, acc);
        PreOrder(n.Right, acc);
    }

    private static void PostOrder(TreeNode? n, List<int> acc)
    {
        if (n is null) return;
        PostOrder(n.Left, acc);
        PostOrder(n.Right, acc);
        acc.Add(n.Value);
    }

    /// <summary>Level-order (BFS) بطابور — تُستخدم لطباعة الشجرة بالطبقات.</summary>
    public IReadOnlyList<IReadOnlyList<int>> LevelOrder()
    {
        var result = new List<IReadOnlyList<int>>();
        if (Root is null) return result;

        var queue = new Queue<TreeNode>();
        queue.Enqueue(Root);

        while (queue.Count > 0)
        {
            var level = new List<int>();
            for (var i = queue.Count; i > 0; i--)     // عدد طبقة كامل
            {
                var n = queue.Dequeue();
                level.Add(n.Value);
                if (n.Left is not null) queue.Enqueue(n.Left);
                if (n.Right is not null) queue.Enqueue(n.Right);
            }
            result.Add(level);
        }
        return result;
    }

    /// <summary>الارتفاع: أقصى عمق — O(n).</summary>
    public int Height() => Height(Root);
    private static int Height(TreeNode? n) =>
        n is null ? 0 : 1 + Math.Max(Height(n.Left), Height(n.Right));

    /// <summary>هل الشجرة متوازنة؟ (|فرق الارتفاع| ≤ 1 في كل عقدة) — O(n).</summary>
    public bool IsBalanced() => Check(Root) != -1;

    private static int Check(TreeNode? n)
    {
        if (n is null) return 0;
        var l = Check(n.Left);
        if (l == -1) return -1;
        var r = Check(n.Right);
        if (r == -1) return -1;
        if (Math.Abs(l - r) > 1) return -1;
        return 1 + Math.Max(l, r);
    }

    /// <summary>أقل قيمة (أقصى يسار) وأكبر قيمة (أقصى يمين) — O(h).</summary>
    public int? Min()
    {
        if (Root is null) return null;
        var n = Root;
        while (n.Left is not null) n = n.Left;
        return n.Value;
    }

    /// <summary>الحذف — أصعب عملية في BST (3 حالات).</summary>
    public void Remove(int value) => Root = Remove(Root, value);

    private static TreeNode? Remove(TreeNode? node, int value)
    {
        if (node is null) return null;
        if (value < node.Value) { node.Left = Remove(node.Left, value); return node; }
        if (value > node.Value) { node.Right = Remove(node.Right, value); return node; }

        // ① بلا أطفال أو طفل واحد
        if (node.Left is null) return node.Right;
        if (node.Right is null) return node.Left;

        // ② طفلان: استبدل بأصغر قيمة في اليمين ثم احذفها
        var successor = node.Right;
        while (successor.Left is not null) successor = successor.Left;
        return new TreeNode(successor.Value)
        {
            Left = node.Left,
            Right = Remove(node.Right, successor.Value),
        };
    }
}'''},
        {"type": "table", "caption": "اجتياز أم آخر — أي واحد لأي غرض",
         "head": ["الغرض", "الاجتياز", "السبب"],
         "rows": [
             ["ترتيب تصاعدي في BST", "In-order", "يسار → جذر → يمين يعطي ترتيبًا"],
             ["نسخ/تسلسل الشجرة", "Pre-order", "الجذر أولًا يُنشئ الشجرة عند إعادة البناء"],
             ["حذف/تقييم تعبير", "Post-order", "الأبناء قبل الأب"],
             ["الطبقات/أقصر عدد حواف", "Level-order (BFS)", "طابور يضمن الزيارة بالطبقات"],
             ["أقصى عمق/مسار", "DFS (أي ترتيب)", "بسيط بالعودية أو مكدس"],
         ]},
        {"type": "callout", "kind": "warn", "title": "مصائد الشجرة في المقابلة",
         "md": "**① نسيان `null` check** → `NullReferenceException` فوري.\n**② عودية على شجرة منحرفة (10⁵ عقدة)** → `StackOverflowException` **لا يُلتقط**. الحل: نسخة تكرارية بمكدس صريح.\n**③ الخلط بين الارتفاع والعمق** — عرّفهما قبل الكود.\n**④ `BST` غير متوازنة = أسوأ من القائمة** (O(n) بحث) — اذكر ذلك قبل أن يسألوا.\n**⑤ في .NET الإنتاج: `SortedDictionary` (أحمر-أسود) أو `SortedSet`** — لا تكتب BST بنفسك إلا للتعلم/المقابلة."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تنفّذ `Stack`/`Queue` على مصفوفة وتشرح لماذا `RemoveAt(0)` ممنوع.",
            "تكتب `Queue` دائرية (ring buffer) وتشرح `%` في الحساب.",
            "تعرف أن `Queue<T>` ليست آمنة للخيوط وتختار `Channel<T>`/`ConcurrentQueue`.",
            "تفهم `BoundedChannelFullMode.Wait` كـbackpressure.",
            "تستخدم `LinkedList` فقط مع مرجع عقدة (LRU) وتشرح ثمنها.",
            "تنفّذ BST بإدراج/بحث/حذف (3 حالات) وتشرح التعقيد بدلالة الارتفاع.",
            "تكتب 4 اجتيازات وتعرف استخدام كل واحد.",
            "تفرّق بين الارتفاع والعمق وتكتب فحص التوازن O(n).",
            "تستخدم `SortedDictionary`/`PriorityQueue` في الإنتاج بدل كتابة شجرة.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "7 أسئلة.",
         "questions": [
             {"q": "لماذا `List<T>.RemoveAt(0)` ممنوع كتنفيذ طابور؟",
              "options": ["لا يعمل", "لأنه O(n): يزيح كل العناصر — الطابور يصبح O(n²) لإفراغه",
                          "يستهلك ذاكرة", "يفقد الترتيب"],
              "answer": 1,
              "explain": "الإزاحة المباشرة لكل عنصر تجعل n عملية Dequeue = O(n²). `Queue<T>` بمصفوفة دائرية تجعلها O(1). هذه من أشهر أخطاء الأداء في كود إنتاجي حقيقي."},
             {"q": "ما أفضل بنية لـ«أعطني أرخص 10 طلبات» مع إضافة مستمرة؟",
              "options": ["`List` + `Sort` كل مرة", "`PriorityQueue` (heap) بحجم 10", "`Dictionary`", "`LinkedList`"],
              "answer": 1,
              "explain": "`PriorityQueue` (min-heap) بحجم 10: كل إضافة O(log 10) = O(1)، واستخراج الأرخص O(log n). الفرز المتكرر O(n log n) لكل عملية — أسوأ بمرات."},
             {"q": "اجتياز يعطي القيم مرتّبة في BST هو:",
              "options": ["Pre-order", "In-order", "Post-order", "Level-order"],
              "answer": 1,
              "explain": "In-order (يسار، جذر، يمين) يزور القيم بترتيب تصاعدي في BST صحيحة. لهذا يُستخدم للتحقق من صحة الشجرة أو تحويلها لقائمة مرتّبة."},
             {"q": "ما تعقيد البحث في BST منحرفة (كل إدخال أكبر من السابق)؟",
              "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
              "answer": 2,
              "explain": "الشجرة تتحول لقائمة مرتبطة فعليًا، والبحث يصبح خطيًا. لذلك تُستخدم الأشجار المتوازنة (أحمر-أسود في `SortedDictionary`) في الإنتاج."},
             {"q": "`LinkedList` مقابل `List` لإدراج 10,000 عنصر في المنتصف مع معرفة الموضع:",
              "options": ["LinkedList أسرع دائمًا", "List أسرع عمليًا (تجمّع ذاكرة + إزاحة memmove سريعة) رغم O(n)",
                          "متساويان", "لا يمكن المقارنة"],
              "answer": 1,
              "explain": "الإزاحة في `List` عملية `memmove` متصلة سريعة جدًا، بينما `LinkedList` تحتاج تخصيص عقد ومطاردة مؤشرات مبعثرة في الذاكرة. العملي يغلب النظري إلا مع مرجع عقدة."},
             {"q": "ماذا يحدث لو استخدمت `Channel.CreateUnbounded` مع منتج أسرع من المستهلك؟",
              "options": ["backpressure تلقائي", "نمو غير محدود للذاكرة حتى OOM — لا يوجد backpressure",
                          "خطأ ترجمة", "يتجاهل العناصر"],
              "answer": 1,
              "explain": "غير المحدود لا يرجع ضغطًا للمنتج. في الأنظمة التي تعرف سقفها، استخدم `CreateBounded` مع `FullMode.Wait` (أو `DropOldest` لو الفقدان مقبول)."},
             {"q": "التنفيذ العوديّ لاجتياز شجرة عميقة جدًا (10⁶ عقدة) يعرّضك لـ:",
              "options": ["بطء فقط", "`StackOverflowException` — لا يمكن التقاطه، العملية تنهار",
                          "تسريب ذاكرة", "خطأ ترجمة"],
              "answer": 1,
              "explain": "كل استدعاء عودي يأخذ إطارًا على مكدس الخيط (~1MB). الشجرة العميقة تتجاوزه فينهار التطبيق فورًا بلا `catch`. الحل: نسخة تكرارية بمكدس صريح على الـheap."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "تنفيذ + تشخيص.",
         "items": [
            {"id": "s9-m2-l2-t1",
             "title": "مهمة 1: نفّذ LRU Cache + مقارنة",
             "md": "نفّذ LRU بـ`Dictionary` + `LinkedList` (O(1))، ثم نسخة بـ`List` (O(n))، وقِس الفرق على 100 ألف عملية.",
             "criteria": [
                 "النسخة O(1): `Get` و`Set` بلا أي بحث خطي.",
                 "النسخة O(n): تعمل وتُنتج نفس النتائج على نفس التسلسل (اختبار تكافؤ).",
                 "جدول قياس زمني لـ3 أحجام ذاكرة (100 · 10k · 100k) ونسبة الفرق.",
                 "اختبارات: طرد الأقدم · تحديث قيمة موجودة يحركها للرأس · سعة 1 · سعة غير صالحة ترمي استثناء.",
                 "شرح مكتوب: لماذا `LinkedList` ضرورية هنا وليست في طابور عادي.",
             ],
             "hint": "أهم تفصيل: عند `Set` لمفتاح موجود، لازم **تحريك العقدة للرأس** وإلا أصبح الترتيب خاطئًا. ولاختبار الطرد، املأ السعة +1 وتحقّق أن أقدم مفتاح اختفى. في القياس، أضف تسخينًا ثم قِس فقط زمن العمليات.",
             "solution": "النتيجة: فرق 20–100× لصالح O(1) عند 100k عملية. الأهم أن الاختبارات المتكافئة تكشف عادة خطأ الترتيب عند تحديث قيمة موجودة — وهو أكثر خطأ شائع في تنفيذ LRU.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.linkedlist-1",
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.dictionary-2",
             ]},
            {"id": "s9-m2-l2-t2",
             "title": "مهمة 2: شجرة + اجتيازات باختبارات",
             "md": "نفّذ BST كاملة (إدراج · بحث · حذف · 4 اجتيازات · ارتفاع · توازن) واكتب 8 اختبارات.",
             "criteria": [
                 "حذف يعالج الحالات الثلاث (ورقة · طفل واحد · طفلان) — باختبار لكل حالة.",
                 "`InOrder` على إدخال [5,3,8,1,4,7,9] ينتج [1,3,4,5,7,8,9].",
                 "`LevelOrder` ينتج طبقات صحيحة (اختبار على نفس الشجرة).",
                 "`Height` و`IsBalanced` يعملان على شجرة منحرفة ومتوازنة.",
                 "نسخة تكرارية للبحث (بلا عودية) — وموثّق لماذا.",
                 "اختبار أداء: 10 آلاف عقدة عشوائية مقابل 10 آلاف مرتبة تصاعديًا (الفرق في الارتفاع).",
             ],
             "hint": "عند الحذف بعقدتين، ابحث عن **أصغر قيمة في الشجرة اليمنى** (in-order successor) واستبدل، ثم احذفها عوديًا. لو استخدمت أكبر قيمة يسار (predecessor) فكذلك صحيح — لكن اختر واحدة والتزم بها في الاختبارات.",
             "solution": "النتيجة: 8 اختبارات خضراء + قياس يوضح أن الإدخال المرتّب يعطي ارتفاع 10,000 (شجرة منحرفة) مقابل ~30 للعشوائي — وهذا دليل عملي على لماذا `SortedDictionary` لازمة.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.sorteddictionary-2",
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Stack<T>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.stack-1"},
            {"label": "Queue<T>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.queue-1"},
            {"label": "PriorityQueue<TElement,TPriority>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2"},
            {"label": "System.Threading.Channels", "url": "https://learn.microsoft.com/dotnet/core/extensions/channels"},
            {"label": "SortedDictionary", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.sorteddictionary-2"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════
# l3 — الرسوم والمسارات
# ══════════════════════════════════════════════════════════════════
_L3 = {
    "id": "s9-m2-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الرسوم (Graphs) هي **أكثر بنية تُسأل في المقابلات بعد المصفوفات**، وأكثرها ارتباطًا بالشغل الواقعي: تبعيات المشاريع · مسارات الطلبات في الميكروسيرفيسز · توصيات · اكتشاف دورات في خدمات · شبكات.\n\nالدرس: تمثيل (مصفوفة/قوائم تجاور) · BFS وDFS · أقصر مسار بلا أوزان · اكتشاف دورات · الترتيب الطوبولوجي — وكلها بـC# نظيفة."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Adjacency matrix", "def": "مصفوفة n×n: `m[i][j] = 1` لو يوجد حرف. O(n²) ذاكرة، فحص الحرف O(1) — جيدة للرسوم الكثيفة."},
            {"term": "Adjacency list", "def": "لكل عقدة قائمة جيران: O(V+E) ذاكرة — الأفضل عمليًا (أغلب الرسوم متفرقة)."},
            {"term": "BFS", "def": "بحث بالعرض بطابور: يزور بالطبقات ⇒ **يعطي أقصر مسار بعدد الحواف** في رسم بلا أوزان. O(V+E)."},
            {"term": "DFS", "def": "بحث بالعمق بمكدس/عودية: يستكشف فرعًا كاملًا قبل غيره. O(V+E). مناسب للاتصال/الدورات/التوبولوجي."},
            {"term": "Visited set", "def": "مجموعة العقد المزارة — **بدونها** تدور في حلقة لا نهائية عند وجود دورة."},
            {"term": "Connected components", "def": "عدد المجموعات المترابطة = عدد مرات تشغيل BFS/DFS على عقد غير مزارة."},
            {"term": "Topological sort", "def": "ترتيب عقد DAG بحيث تأتي كل عقدة قبل تابعيها (Kahn بـin-degree أو DFS post-order). يفشل لو وُجدت دورة."},
            {"term": "Cycle detection", "def": "في رسم موجّه: DFS بحالة (مزار/في المسار) أو Kahn (لو بقي عقد ⇒ دورة). في غير موجّه: تتبّع الأب."},
            {"term": "Dijkstra", "def": "أقصر مسار بأوزان غير سالبة بـ`PriorityQueue`: O((V+E) log V)."},
            {"term": "Union-Find (DSU)", "def": "بنية للانتماء للمجموعات: `Find`/`Union` شبه O(1) بـpath compression — ممتازة لكشف الدورات/الاتصال."},
            {"term": "Bipartite", "def": "رسم يمكن تلوينه بلونين بحيث لا يتصل متشابهان — يُفحص بـBFS مع صبغ الطبقات."},
            {"term": "Degrees", "def": "in-degree (عدد الحواف الداخلة) وout-degree (الخارجة) — أساس Kahn والتحليل."},
        ]},

        {"type": "heading", "level": 2, "text": "① التمثيل: القرار الأول"},
        {"type": "table", "caption": "كيف تخزّن الرسم",
         "head": ["المعيار", "Matrix", "List", "الأفضل"],
         "rows": [
             ["الذاكرة", "O(V²)", "O(V+E)", "List إلا للكثيف"],
             ["فحص «هل يوجد حرف؟»", "O(1)", "O(degree)", "Matrix"],
             ["المرور على كل الجيران", "O(V) دائمًا", "O(degree)", "List"],
             ["V = 10,000 وE = 20,000", "100M خلية ❌", "سريع ✅", "List"],
             ["V = 500 وكل شيء متصل", "مقبول ✅", "مقبول", "أيهما"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Graphs/Graph.cs — قوائم تجاور + BFS + DFS + مكوّنات", "filename": "Algorithms/Graph.cs", "code": r'''using System.Collections.Generic;

/// <summary>رسم بقوائم تجاور — O(V+E) ذاكرة، ويصلح لرسم عشوائي/كبير.</summary>
public sealed class Graph
{
    private readonly Dictionary<int, List<int>> _adj = new();
    public bool Directed { get; }

    public Graph(bool directed = false) => Directed = directed;

    public void AddVertex(int v) => _adj.TryAdd(v, []);

    public void AddEdge(int from, int to)
    {
        AddVertex(from);
        AddVertex(to);
        _adj[from].Add(to);
        if (!Directed) _adj[to].Add(from);
    }

    public IReadOnlyList<int> Neighbors(int v) =>
        _adj.TryGetValue(v, out var list) ? list : [];

    public IEnumerable<int> Vertices => _adj.Keys;

    // ── BFS: أقصر مسار بعدد الحواف ──────────────────────────────
    /// <summary>يرجع المسار من start إلى target أو null. O(V+E).</summary>
    public IReadOnlyList<int>? ShortestPath(int start, int target)
    {
        if (!_adj.ContainsKey(start)) return null;
        if (start == target) return [start];

        var visited = new HashSet<int> { start };
        var parent = new Dictionary<int, int>();
        var queue = new Queue<int>();
        queue.Enqueue(start);

        while (queue.Count > 0)
        {
            var v = queue.Dequeue();
            foreach (var n in Neighbors(v))
            {
                if (!visited.Add(n)) continue;      // ✅ قبل الإضافة للطابور
                parent[n] = v;

                if (n == target) return BuildPath(parent, start, target);
                queue.Enqueue(n);
            }
        }
        return null;
    }

    private static List<int> BuildPath(Dictionary<int, int> parent, int start, int target)
    {
        var path = new List<int>();
        for (var at = target; at != start; at = parent[at]) path.Add(at);
        path.Add(start);
        path.Reverse();
        return path;
    }

    // ── DFS تكرارية (بلا stack overflow) ────────────────────────
    public IReadOnlyList<int> DfsPreOrder(int start)
    {
        var result = new List<int>();
        var visited = new HashSet<int>();
        var stack = new Stack<int>();
        stack.Push(start);

        while (stack.Count > 0)
        {
            var v = stack.Pop();
            if (!visited.Add(v)) continue;
            result.Add(v);

            // نضيف الجيران بترتيب معكوس حتى يُزار الأول أولًا
            var neighbors = Neighbors(v);
            for (var i = neighbors.Count - 1; i >= 0; i--)
                if (!visited.Contains(neighbors[i])) stack.Push(neighbors[i]);
        }
        return result;
    }

    // ── المكوّنات المتصلة ───────────────────────────────────────
    public int CountComponents()
    {
        var visited = new HashSet<int>();
        var components = 0;

        foreach (var v in Vertices)
        {
            if (visited.Contains(v)) continue;
            components++;
            var stack = new Stack<int>();
            stack.Push(v);
            while (stack.Count > 0)
            {
                var cur = stack.Pop();
                if (!visited.Add(cur)) continue;
                foreach (var n in Neighbors(cur))
                    if (!visited.Contains(n)) stack.Push(n);
            }
        }
        return components;
    }

    // ── كشف دورة في رسم موجّه (DFS بالألوان) ───────────────────
    /// <summary>0=غير مزار · 1=في المسار الحالي · 2=انتهى</summary>
    public bool HasCycle()
    {
        var color = new Dictionary<int, int>();
        foreach (var v in Vertices)
            if (Get(color, v) == 0 && VisitCycle(v, color)) return true;
        return false;
    }

    private bool VisitCycle(int v, Dictionary<int, int> color)
    {
        color[v] = 1;
        foreach (var n in Neighbors(v))
        {
            var c = Get(color, n);
            if (c == 1) return true;                    // ✅ عودة للمسار الحالي = دورة
            if (c == 0 && VisitCycle(n, color)) return true;
        }
        color[v] = 2;
        return false;
    }

    private static int Get(Dictionary<int, int> d, int k) => d.TryGetValue(k, out var v) ? v : 0;
}'''},
        {"type": "callout", "kind": "warn", "title": "5 أخطاء في BFS/DFS",
         "md": "**① إضافة `visited` عند الخروج من الطابور لا عند الإضافة** → العقدة تُضاف عدة مرات فتنفجر الذاكرة (خصوصًا في BFS).\n**② نسيان `visited` تمامًا** → حلقة لا نهائية مع أي دورة.\n**③ BFS مع أوزان** → لا يعطي أقصر مسار وزني (استخدم Dijkstra).\n**④ عودية عميقة على 10⁶ عقدة** → `StackOverflow` (لا يُلتقط) — استخدم مكدسًا صريحًا.\n**⑤ إعادة إنشاء `List`/`HashSet` داخل حلقة** → تدهور من O(V+E) إلى أسوأ."},

        {"type": "heading", "level": 2, "text": "② التوبولوجي: الحالة الأكثر ارتباطًا بالشغل"},
        {"type": "code", "lang": "csharp", "title": "Graphs/TopologicalSort.cs — ترتيب المهام/المستأجرين + كشف دورة", "filename": "Algorithms/TopologicalSort.cs", "code": r'''/// <summary>
/// ترتيب تبعيات (DAG): «ابدأ بما لا يعتمد على شيء».
/// تطبيقات واقعية: ترتيب طلبات migrations · مهام build · وركفلوز · تبعيات DI.
/// </summary>
public static class TopologicalSort
{
    /// <summary>Kahn: نبدأ بالعقد ذات in-degree = 0. يرجع null لو وُجدت دورة.</summary>
    public static IReadOnlyList<int>? Kahn(IReadOnlyDictionary<int, List<int>> edges)
    {
        var inDegree = new Dictionary<int, int>();
        foreach (var (from, tos) in edges)
        {
            inDegree.TryAdd(from, 0);
            foreach (var to in tos)
            {
                inDegree.TryAdd(to, 0);
                inDegree[to]++;
            }
        }

        var ready = new Queue<int>(inDegree.Where(kv => kv.Value == 0).Select(kv => kv.Key));
        var order = new List<int>(inDegree.Count);

        while (ready.Count > 0)
        {
            var v = ready.Dequeue();
            order.Add(v);
            if (!edges.TryGetValue(v, out var tos)) continue;
            foreach (var to in tos)
                if (--inDegree[to] == 0) ready.Enqueue(to);
        }

        // ✅ لو لم تُرتَّب كل العقد ⇒ دورة موجودة
        return order.Count == inDegree.Count ? order : null;
    }

    /// <summary>نفس النتيجة بأصغر رقم أولًا (حتمية) — مفيدة في الاختبارات والبناء المتكرر.</summary>
    public static IReadOnlyList<int>? KahnStable(IReadOnlyDictionary<int, List<int>> edges)
    {
        var inDegree = new Dictionary<int, int>();
        foreach (var (from, tos) in edges)
        {
            inDegree.TryAdd(from, 0);
            foreach (var to in tos) { inDegree.TryAdd(to, 0); inDegree[to]++; }
        }

        var ready = new PriorityQueue<int, int>();
        foreach (var kv in inDegree.Where(kv => kv.Value == 0)) ready.Enqueue(kv.Key, kv.Key);

        var order = new List<int>();
        while (ready.TryDequeue(out var v, out _))
        {
            order.Add(v);
            if (!edges.TryGetValue(v, out var tos)) continue;
            foreach (var to in tos)
                if (--inDegree[to] == 0) ready.Enqueue(to, to);
        }
        return order.Count == inDegree.Count ? order : null;
    }
}

/*
 مثال واقعي: اكتشاف دورة في تبعيات حقن الخدمات عند بدء التطبيق،
 أو في خط أنابيب CI: (build → test → package → deploy) بترتيب صحيح.
*/'''},
        {"type": "table", "caption": "BFS / DFS / Dijkstra / Topo — اختيار سريع",
         "head": ["المسألة", "الخوارزمية", "التعقيد"],
         "rows": [
             ["أقصر مسار بلا أوزان", "**BFS**", "O(V+E)"],
             ["هل يوجد مسار؟/استكشاف كامل", "DFS", "O(V+E)"],
             ["أقصر مسار بأوزان موجبة", "**Dijkstra** بـ`PriorityQueue`", "O((V+E) log V)"],
             ["أوزان سالبة", "Bellman-Ford", "O(V·E)"],
             ["ترتيب تبعيات", "**Kahn (Topo)**", "O(V+E)"],
             ["دورة في رسم موجّه", "DFS بالألوان أو Kahn", "O(V+E)"],
             ["عدد المكوّنات", "BFS/DFS من كل عقدة", "O(V+E)"],
             ["مجموعات متصلة مع إضافات", "Union-Find", "≈O(1) لكل عملية"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Graphs/Dijkstra.cs — أقصر مسار بأوزان (شبكات/تكاليف)", "filename": "Algorithms/Dijkstra.cs", "code": r'''/// <summary>رسم موزون موجب — أوزان 0/سالبة غير مدعومة (استخدم Bellman-Ford).</summary>
public sealed class WeightedGraph
{
    private readonly Dictionary<string, List<(string To, int Weight)>> _adj = new();

    public void AddEdge(string from, string to, int weight)
    {
        if (weight < 0) throw new ArgumentException("Dijkstra لا يدعم أوزانًا سالبة", nameof(weight));
        _adj.TryAdd(from, []);
        _adj.TryAdd(to, []);
        _adj[from].Add((to, weight));
    }

    /// <summary>يرجع المسافة والتكلفة لكل عقدة يمكن الوصول إليها.</summary>
    public (Dictionary<string, int> Dist, Dictionary<string, string> Prev) Shortest(string source)
    {
        var dist = new Dictionary<string, int>(StringComparer.Ordinal) { [source] = 0 };
        var prev = new Dictionary<string, string>(StringComparer.Ordinal);

        // أولوية بالمسافة: الأقرب غير المنتهي أولًا
        var queue = new PriorityQueue<string, int>();
        queue.Enqueue(source, 0);
        var done = new HashSet<string>(StringComparer.Ordinal);

        while (queue.TryDequeue(out var v, out var d))
        {
            if (d > dist.GetValueOrDefault(v, int.MaxValue)) continue;   // نسخة قديمة
            if (!done.Add(v)) continue;

            foreach (var (to, w) in _adj.GetValueOrDefault(v, []))
            {
                var candidate = d + w;
                if (candidate >= dist.GetValueOrDefault(to, int.MaxValue)) continue;
                dist[to] = candidate;
                prev[to] = v;
                queue.Enqueue(to, candidate);      // إدخال جديد بأولوية أفضل
            }
        }
        return (dist, prev);
    }

    public IReadOnlyList<string>? PathTo(IReadOnlyDictionary<string, string> prev, string target)
    {
        if (!prev.ContainsKey(target)) return null;
        var path = new List<string> { target };
        var at = target;
        while (prev.TryGetValue(at, out var p)) { path.Add(p); at = p; }
        path.Reverse();
        return path;
    }
}'''},
        {"type": "callout", "kind": "note", "title": "متى تظهر الرسوم في شغل .NET الفعلي",
         "md": "**①** ترتيب migrations متعددة قواعد البيانات · **②** تحليل تبعيات الخدمات (كشف دورة بين خدمتين تتبادلان الاستدعاء) · **③** سير عمل (workflow engine) · **④** صلاحيات متوارثة (graph of roles) · **⑤** توصيات (من شاهد X شاهد Y) · **⑥** فحص صلاحية DI عند بدء التشغيل.\nفي كلها: نفس الكود تقريبًا — BFS/DFS/Topo. اللي يتغير هو مصدر البيانات فقط."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تختار قوائم تجاور للرسوم المتفرقة وتبرّر بـO(V+E).",
            "تعلّم `visited` عند الإضافة للطابور لا عند الخروج.",
            "تستخرج المسار بـ`parent` map وتعيد بناءه بترتيب صحيح.",
            "تكتب DFS تكرارية وتشرح لماذا (StackOverflow).",
            "تعدّ المكوّنات المتصلة وتشرح O(V+E).",
            "تكشف دورة في رسم موجّه بثلاث حالات ألوان.",
            "تنفّذ Kahn وترجع `null` عند وجود دورة.",
            "تستخدم `PriorityQueue` في Dijkstra وتتجاهل النسخ القديمة (stale entries).",
            "تعرف متى تحتاج Dijkstra بدل BFS.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "7 أسئلة.",
         "questions": [
             {"q": "متجر 50,000 منتج و200,000 علاقة — أي تمثيل؟",
              "options": ["مصفوفة n×n", "قوائم تجاور", "Dictionary مفرد", "شجرة"],
              "answer": 1,
              "explain": "المصفوفة تحتاج 2.5 مليار خلية (غير عملي). قوائم التجاور بـO(V+E) = 250 ألف إدخال — فرق هائل."},
             {"q": "BFS يضمن أقصر مسار عندما:",
              "options": ["الرسم موزون", "كل الحواف بنفس التكلفة (بلا أوزان)", "الرسم موجّه فقط", "دائمًا"],
              "answer": 1,
              "explain": "BFS يزور بالطبقات فالمسار الأول لهدف هو الأقل حواف. مع أوزان مختلفة، عدد الحواف لا يمثل التكلفة — تحتاج Dijkstra."},
             {"q": "أين تُضاف العقدة إلى `visited` في BFS الصحيح؟",
              "options": ["عند خروجها من الطابور", "قبل إضافتها للطابور", "بعد زيارة كل جيرانها", "لا تُضاف"],
              "answer": 1,
              "explain": "لو أضفتها عند الخروج، فقد تُضاف للطابور عشرات المرات قبل معالجتها (في رسم كثيف) ويمكن أن تخسر معنى الطبقات وتستهلك ذاكرة كبيرة."},
             {"q": "Kahn يرجع ترتيبًا أقصر من عدد العقد. ماذا يعني؟",
              "options": ["خطأ في الكود", "يوجد دورة — بعض العقد لا يصل in-degree فيها لصفر أبدًا",
                          "الرسم غير متصل", "الرسم موجّه"],
              "answer": 1,
              "explain": "In-degree = 0 تعني «لا تبعية متبقية». في الدورة، كل عقدة فيها تبعية داخلية فلا تُحرَّر — وعدد المخرجات < عدد العقد يكشف ذلك."},
             {"q": "ما فائدة `PriorityQueue` في Dijkstra؟",
              "options": ["ترتيب أبجدي", "إخراج العقدة صاحبة أصغر مسافة مؤقتة أولًا — يضمن ألا تُحسَّن بعد التثبيت",
                          "تخزين الحواف", "تقليل الذاكرة"],
              "answer": 1,
              "explain": "Dijkstra جشع: يثبّت أقرب عقدة. `PriorityQueue<string,int>` تعطي هذه بسهولة. ملاحظة: تحقّق من المسافة المخزنة قبل المعالجة لتجاهل الإدخالات القديمة."},
             {"q": "لماذا DFS تكرارية أفضل من عودية على رسم كبير؟",
              "options": ["أسرع دائمًا", "لأن العودية تستهلك مكدس الخيط ويمكن أن تنهار بـStackOverflow على 10⁶ عقدة",
                          "أقل ذاكرة", "لا فرق"],
              "answer": 1,
              "explain": "مكدس الخيط محدود (~1MB) والانهيار لا يُلتقط. المكدس الصريح على الـheap يمكن أن ينمو بحد أكبر — وفي المقابلة يفضّل أن تذكر أن النسخة التكرارية أكثر أمانًا."},
             {"q": "أي سؤال شعبي يُحل بـ«DFS ثلاثي الألوان»؟",
              "options": ["أقصر مسار", "كشف دورة في رسم موجّه", "ترتيب أبجدي", "عدّ الحواف"],
              "answer": 1,
              "explain": "أبيض (غير مزار) / رمادي (في المسار الحالي) / أسود (منتهٍ). العودة إلى عقدة رمادية = دورة. في الرسم غير الموجّه يكفي تتبّع الأب لتجنّب اعتبار الحرف نفسه عودة."},
         ]},

        {"type": "tasks", "title": "مهمة واحدة", "intro": "رسم حقيقي من مجالك.",
         "items": [
            {"id": "s9-m2-l3-t1",
             "title": "مهمة: حلّل تبعيات الخدمات/المهام برسم",
             "md": "ابنِ رسمًا من بيانات حقيقية (تبعيات مشاريع .sln · خدمات · مهام CI) ونفّذ: ترتيبًا طوبولوجيًا · كشف دورة · إيجاد مسار أقصر بين عقدتين · عدّ المكوّنات.",
             "criteria": [
                 "مصدر البيانات حقيقي (ملف/API/قاعدة) — لا رسم مُختلق بالكامل.",
                 "`Kahn` يرجع ترتيبًا صحيحًا (تحقق آلي: كل حرف يظهر بعد أصله).",
                 "كشف الدورة يعطي **مسار الدورة** نفسه لا مجرد `true`.",
                 "BFS يعطي مسارًا ويعرضه (لا طولًا فقط).",
                 "عدّ المكوّنات + تقرير بالمكوّنات المنفصلة.",
                 "5 اختبارات: رسم بلا حواف · عقدة واحدة · دورة ذاتية · دورتان · رسم متصل تمامًا.",
             ],
             "hint": "أسهل مصدر بيانات واقعي: اقرأ `*.csproj` و`ProjectReference` من الحل — ينتج رسمًا حقيقيًا للتبعيات. ولعرض الدورة، خلال DFS احتفظ بالمكدس الحالي؛ عند العودة لعقدة رمادية خذ الشريحة من موضعها حتى القمة.",
             "solution": "النتيجة النموذجية: ترتيب بناء صحيح، وكشف دورة (لو وُجدت) مع الطباعة، وتقرير مكوّنات يكشف مشاريع معزولة. الأهم: تعديل التقرير ليصبح جزءًا من CI (`dotnet build` يفعلها بالفعل للمشاريع، لكن تحليل الخدمات لا) — وهنا القيمة الحقيقية.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2",
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.queue-1",
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.hashset-1",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "PriorityQueue (heap)", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2"},
            {"label": "HashSet<T>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.hashset-1"},
            {"label": "Queue<T>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.queue-1"},
        ]},
    ],
}

LESSONS_S9_D = [_L1, _L2, _L3]
