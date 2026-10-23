# -*- coding: utf-8 -*-
"""Stage 9 — module 2 (part B): s9-m2-l4 (الأنماط), l5 (تمرين موقوت)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════
# l4 — الأنماط: two pointers · sliding window · prefix sums
# ══════════════════════════════════════════════════════════════════
_L4 = {
    "id": "s9-m2-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الدرس ده **أعلى عائد في المقابلات**: ثلاث عائلات من الأنماط تحل ما لا يقل عن 40% من مسائل المقابلات المتوسطة، وكثير منها يظهر في شغل حقيقي (تحليل سلاسل logs · نوافذ معدلات · تجميعات تقارير).\n\nالدرس: تعرف **علامة المسألة** (إمتى تستخدم أي نمط) → الكود الصحيح → الفخاخ (الحدود، التكرارات، الأرقام السالبة)."},

        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "Two pointers (opposite)", "def": "مؤشران من الطرفين يقتربان: مصفوفة **مرتّبة**، مجموع هدف، قلب، palindrome. O(n)."},
            {"term": "Two pointers (same direction)", "def": "مؤشر سريع وبطيء: إزالة تكرارات في المكان · كشف دورة · إيجاد العنصر الأوسط."},
            {"term": "Sliding window (fixed)", "def": "نافذة بحجم ثابت k تنزلق: مجموع/متوسط كل نافذة بـO(n) بدل O(n·k)."},
            {"term": "Sliding window (variable)", "def": "نافذة تتمدد وتتقلص حسب شرط (أطول/أقصر نطاق يحقق شرطًا). O(n) — كل عنصر يدخل ويخرج مرة."},
            {"term": "Prefix sum", "def": "`pre[i] = sum(a[0..i-1])` ⇒ مجموع `[l, r)` = `pre[r] - pre[l]` بـO(1)."},
            {"term": "Prefix + hashmap", "def": "لعدّ/إيجاد نطاقات مجموعها k: خزّن البادئات السابقة في `Dictionary`. O(n)."},
            {"term": "Difference array", "def": "لتعديلات نطاقات كثيرة: `diff[l] += v; diff[r+1] -= v` ثم بادئة تراكمية — O(1) لكل تعديل."},
            {"term": "Monotonic window", "def": "نافذة بقيم رتيبة (deque) لإيجاد الأقصى/الأدنى في كل نافذة بحجم k بـO(n)."},
            {"term": "Kadane", "def": "أقصى مجموع نطاق متصل: `best = max(x, best + x)` — أقصر sliding window في العالم."},
            {"term": "Shrink condition", "def": "شرط تقليص النافذة (`while (sum > target) shrink`) — أساس النافذة المتغيرة الصحيحة."},
            {"term": "Off-by-one في النوافذ", "def": "أشهر خطأ: نافذة `[l, r)` أو `[l, r]`؟ اختر اصطلاحًا واحدًا والتزم به في كل الكود."},
            {"term": "Signed vs unsigned", "def": "السالبة تكسر بعض الأنماط: النافذة المتغيرة للتقليص تفترض أن التقليص يقلل المجموع — غير صحيح مع أرقام سالبة."},
        ]},

        {"type": "heading", "level": 2, "text": "① علامة المسألة: كيف تعرف النمط في 10 ثوانٍ"},
        {"type": "table", "caption": "شجرة قرار سريعة",
         "head": ["تسمع في السؤال", "النمط", "شرط أساسي", "التعقيد"],
         "rows": [
             ["«مصفوفة **مرتّبة**» + زوج/ثلاثي بمجموع", "Two pointers (طرفان)", "مرتّبة", "O(n)"],
             ["«أطول/أقصر نطاق يحقق شرطًا» + أعداد موجبة", "Sliding window متغيرة", "موجبة", "O(n)"],
             ["«كل نافذة بحجم k»", "Sliding window ثابتة", "—", "O(n)"],
             ["«عدد النطاقات بمجموع = k»", "Prefix + `Dictionary`", "أي أرقام", "O(n)"],
             ["«عدّة تحديثات على نطاقات ثم قراءة»", "Difference array", "—", "O(1) للتعديل"],
             ["«أقصى مجموع متصل»", "Kadane", "—", "O(n)"],
             ["«أقصى في كل نافذة»", "Deque رتيبة", "—", "O(n)"],
             ["«احذف التكرارات في المكان»", "Two pointers نفس الاتجاه", "مرتّبة", "O(n) · O(1)"],
         ]},
        {"type": "callout", "kind": "warn", "title": "الشرط اللي بيوقّع الناس",
         "md": "**Sliding window المتغيرة تحتاج «مونوتونية»**: التقليص لازم **يقلل** المقياس دائمًا. لذلك:\n✅ «أطول نطاق مجموعه ≤ target» مع **أعداد موجبة** — صحيح.\n❌ نفس السؤال مع **أرقام سالبة** — غير صحيح (تقليص النافذة قد يزيد المجموع!). الحل: prefix + hashmap.\n**② «مرتّبة»**: لو السؤال لا يذكر الترتيب، فمؤشرا الطرفين يحتاجان `Sort` — احسب O(n log n) في جوابك.\n**③** اذكر أن التعديل في المكان قد يكون ممنوعًا (API يرجع نسخة) — اسأل."},

        {"type": "heading", "level": 2, "text": "② Two pointers — ثلاثة أشكال بثلاث حالات"},
        {"type": "code", "lang": "csharp", "title": "Patterns/TwoPointers.cs", "filename": "Algorithms/TwoPointers.cs", "code": r'''public static class TwoPointers
{
    // ── ① طرفان: مجموع في مصفوفة مرتّبة ─────────────────────────
    public static (int, int)? PairSum(int[] sorted, int target)
    {
        int l = 0, r = sorted.Length - 1;
        while (l < r)
        {
            var sum = sorted[l] + sorted[r];
            if (sum == target) return (l, r);
            if (sum < target) l++;
            else r--;
        }
        return null;                        // ✅ شرط `l < r` يمنع استخدام نفس العنصر
    }

    // ── ② طرفان: هل السلسلة متناظرة ─────────────────────────────
    public static bool IsPalindrome(ReadOnlySpan<char> s)
    {
        int l = 0, r = s.Length - 1;
        while (l < r)
        {
            if (s[l] != s[r]) return false;
            l++; r--;
        }
        return true;
    }

    // ── ③ نفس الاتجاه: احذف التكرارات في المكان ─────────────────
    /// <summary>يعيد الطول الجديد — والعناصر الفريدة في بداية المصفوفة.</summary>
    public static int RemoveDuplicates(Span<int> sorted)
    {
        if (sorted.Length == 0) return 0;
        var write = 1;                        // أول عنصر فريد دائمًا
        for (var read = 1; read < sorted.Length; read++)
        {
            if (sorted[read] == sorted[write - 1]) continue;
            sorted[write++] = sorted[read];
        }
        return write;
    }

    // ── ④ نفس الاتجاه: العنصر الأوسط (fast/slow) ─────────────────
    public static int? MiddleOfList(IReadOnlyList<int> list)
    {
        if (list.Count == 0) return null;
        int slow = 0, fast = 0;
        while (fast + 1 < list.Count)         // fast يتقدم خطوتين
        {
            slow++;
            fast += 2;
        }
        return list[slow];
    }

    // ── ⑤ ثلاثي مجموعه صفر (3Sum) — O(n²) بعد الفرز ──────────────
    public static IReadOnlyList<(int, int, int)> ThreeSum(int[] nums)
    {
        var result = new List<(int, int, int)>();
        Array.Sort(nums);

        for (var i = 0; i < nums.Length - 2; i++)
        {
            if (i > 0 && nums[i] == nums[i - 1]) continue;      // ✅ تجنّب التكرار
            int l = i + 1, r = nums.Length - 1;
            while (l < r)
            {
                var sum = nums[i] + nums[l] + nums[r];
                if (sum == 0)
                {
                    result.Add((nums[i], nums[l], nums[r]));
                    l++; r--;
                    while (l < r && nums[l] == nums[l - 1]) l++;   // ✅ تجاوز المكرر
                    while (l < r && nums[r] == nums[r + 1]) r--;
                }
                else if (sum < 0) l++;
                else r--;
            }
        }
        return result;
    }
}'''},
        {"type": "callout", "kind": "tip", "title": "لماذا 3Sum هي «المقابلة الكاملة» في سؤال واحد",
         "md": "لأنها تجمع: فرز O(n log n) · حلقات متداخلة مع مؤشرين · **تجنّب التكرار** (أصعب جزء) · حدود مصفوفة قصيرة.\n**خطأ شائع**: تخطّي التكرار بمقارنة الإجابة (`HashSet`) بدل تخطّيه في المؤشر — يبطئ ويستهلك ذاكرة، والأسوأ أن يفوّت الحالات.\n**قاعدة:** بعد إيجاد حل، حرّك المؤشرين **ثم** تخطَّ العناصر المكررة — لا العكس."},

        {"type": "heading", "level": 2, "text": "③ Sliding window — النسختان"},
        {"type": "code", "lang": "csharp", "title": "Patterns/SlidingWindow.cs", "filename": "Algorithms/SlidingWindow.cs", "code": r'''public static class SlidingWindow
{
    // ── ① ثابتة: أقصى متوسط نافذة بحجم k ─────────────────────────
    public static double MaxAverage(int[] nums, int k)
    {
        if (k <= 0 || nums.Length < k) throw new ArgumentException("k غير صالح");

        double sum = 0;
        for (var i = 0; i < k; i++) sum += nums[i];      // نافذة أولى

        var best = sum;
        for (var i = k; i < nums.Length; i++)
        {
            sum += nums[i] - nums[i - k];                 // أضف الجديد واخصم الخارج
            if (sum > best) best = sum;
        }
        return best / k;
    }

    // ── ② متغيرة: أطول نطاق مجموعه ≤ target (أعداد موجبة) ────────
    public static int LongestAtMost(int[] positives, int target)
    {
        int l = 0, sum = 0, best = 0;
        for (var r = 0; r < positives.Length; r++)
        {
            sum += positives[r];
            while (sum > target && l <= r)                // ✅ تقليص
            {
                sum -= positives[l];
                l++;
            }
            best = Math.Max(best, r - l + 1);
        }
        return best;
    }

    // ── ③ متغيرة: أطول سلسلة بلا حروف مكررة ─────────────────────
    public static int LongestUniqueSubstring(ReadOnlySpan<char> s)
    {
        var lastIndex = new Dictionary<char, int>(128);
        int l = 0, best = 0;

        for (var r = 0; r < s.Length; r++)
        {
            if (lastIndex.TryGetValue(s[r], out var prev) && prev >= l)
                l = prev + 1;                             // ✅ اقفز بعد التكرار السابق

            lastIndex[s[r]] = r;
            best = Math.Max(best, r - l + 1);
        }
        return best;
    }

    // ── ④ متغيرة: أقصر نطاق مجموعه ≥ target (موجبة) ─────────────
    public static int MinLengthAtLeast(int[] positives, int target)
    {
        int l = 0, sum = 0, best = int.MaxValue;
        for (var r = 0; r < positives.Length; r++)
        {
            sum += positives[r];
            while (sum >= target)
            {
                best = Math.Min(best, r - l + 1);
                sum -= positives[l++];
            }
        }
        return best == int.MaxValue ? 0 : best;
    }

    // ── ⑤ Kadane: أقصى مجموع نطاق متصل (يسمح بالسالب) ──────────
    public static (int Best, int Start, int End) MaxSubArray(int[] nums)
    {
        if (nums.Length == 0) throw new ArgumentException("مصفوفة فارغة");

        int best = nums[0], bestStart = 0, bestEnd = 0;
        int cur = nums[0], curStart = 0;

        for (var i = 1; i < nums.Length; i++)
        {
            if (nums[i] > cur + nums[i]) { cur = nums[i]; curStart = i; }
            else cur += nums[i];

            if (cur > best) { best = cur; bestStart = curStart; bestEnd = i; }
        }
        return (best, bestStart, bestEnd);
    }

    // ── ⑥ أقصى في كل نافذة بحجم k — deque رتيبة O(n) ────────────
    public static int[] MaxSlidingWindow(int[] nums, int k)
    {
        if (k <= 0 || nums.Length < k) return [];
        var result = new int[nums.Length - k + 1];
        var deque = new LinkedList<int>();      // تخزين الفهارس، تنازليًا بالقيمة

        for (var i = 0; i < nums.Length; i++)
        {
            // ① أخرج الفهارس الخارجة من النافذة
            if (deque.First is { } first && first.Value <= i - k) deque.RemoveFirst();

            // ② أخرج كل ما هو أصغر — لن يكون أقصى أبدًا
            while (deque.Last is { } last && nums[last.Value] <= nums[i]) deque.RemoveLast();

            deque.AddLast(i);
            if (i >= k - 1) result[i - k + 1] = nums[deque.First!.Value];
        }
        return result;
    }
}'''},
        {"type": "table", "caption": "أخطاء النوافذ الأكثر تكرارًا",
         "head": ["الخطأ", "الأثر", "الإصلاح"],
         "rows": [
             ["`while (sum >= target)` بدل `>`", "نافذة فارغة أو نتيجة خاطئة", "راجع شرط الحدود في السؤال بالحرف"],
             ["نسيان `l <= r`", "`l` يتجاوز `r` ويخصم عناصر خارج النافذة", "أضف الشرط أو استخدم `while (l < r)`"],
             ["`best = Math.Max(best, r - l)` بدل `r - l + 1`", "النتيجة أقل بواحد", "الطول = `r - l + 1` لنافذة مغلقة"],
             ["عدم تحديث `lastIndex` بعد القفز", "قفزات خاطئة لاحقًا", "حدّث دائمًا بعد المعالجة"],
             ["استخدام نافذة متغيرة مع أرقام سالبة", "نتيجة خاطئة صامتة", "prefix + `Dictionary`"],
         ]},

        {"type": "heading", "level": 2, "text": "④ Prefix sums — الحل اللي بيبدو سحرًا"},
        {"type": "code", "lang": "csharp", "title": "Patterns/PrefixSums.cs", "filename": "Algorithms/PrefixSums.cs", "code": r'''public static class PrefixSums
{
    /// <summary>بادئة بطول n+1: pre[0]=0 ⇒ مجموع [l, r) = pre[r] - pre[l].</summary>
    public static long[] Build(int[] a)
    {
        var pre = new long[a.Length + 1];
        for (var i = 0; i < a.Length; i++) pre[i + 1] = pre[i] + a[i];
        return pre;
    }

    public static long Range(long[] pre, int l, int rInclusive) =>
        pre[rInclusive + 1] - pre[l];          // ✅ اصطلاح واضح: [l, r]

    // ── عدد النطاقات التي مجموعها k (يعمل مع السالب أيضًا) ───────
    public static int CountSubarraysSumK(int[] nums, int k)
    {
        var seen = new Dictionary<long, int> { [0] = 1 };   // نطاق فارغ
        long sum = 0;
        var count = 0;

        foreach (var x in nums)
        {
            sum += x;
            // عدد البادئات السابقة التي تساوي sum - k
            if (seen.TryGetValue(sum - k, out var c)) count += c;
            seen[sum] = seen.GetValueOrDefault(sum) + 1;
        }
        return count;
    }

    // ── أطول نطاق مجموعه k (بالسالب) ─────────────────────────────
    public static int LongestSubarraySumK(int[] nums, int k)
    {
        var firstSeen = new Dictionary<long, int> { [0] = -1 };   // البادئة ⇒ أول فهرس
        long sum = 0;
        var best = 0;

        for (var i = 0; i < nums.Length; i++)
        {
            sum += nums[i];
            if (firstSeen.TryGetValue(sum - k, out var start))
                best = Math.Max(best, i - start);
            firstSeen.TryAdd(sum, i);            // ✅ أول ظهور فقط (الأطول)
        }
        return best;
    }

    // ── Difference array: تعديلات نطاقات ثم قراءة الكل ──────────
    /// <summary>مثال واقعي: 200 ألف عملية «أضف رصيدًا لنطاق مستخدمين» ثم تقرير.</summary>
    public static long[] ApplyRangeUpdates(int n, IEnumerable<(int L, int R, int V)> updates)
    {
        var diff = new long[n + 1];
        foreach (var (l, r, v) in updates)
        {
            diff[l] += v;
            if (r + 1 < n) diff[r + 1] -= v;
        }

        for (var i = 1; i < n; i++) diff[i] += diff[i - 1];   // بادئة تراكمية
        return diff[..n];
    }

    // ── مصفوفة تراكمية ثنائية الأبعاد (صور/تقارير) ──────────────
    public static long[][] Build2D(int[][] grid)
    {
        var h = grid.Length;
        var w = h == 0 ? 0 : grid[0].Length;
        var pre = new long[h + 1][];
        for (var i = 0; i <= h; i++) pre[i] = new long[w + 1];

        for (var i = 1; i <= h; i++)
        for (var j = 1; j <= w; j++)
            pre[i][j] = grid[i - 1][j - 1]
                      + pre[i - 1][j] + pre[i][j - 1] - pre[i - 1][j - 1];

        return pre;
    }

    /// <summary>مجموع مستطيل [r1..r2] × [c1..c2] بـO(1).</summary>
    public static long RectSum(long[][] pre, int r1, int c1, int r2, int c2) =>
        pre[r2 + 1][c2 + 1] - pre[r1][c2 + 1] - pre[r2 + 1][c1] + pre[r1][c1];
}'''},
        {"type": "callout", "kind": "note", "title": "لماذا `prefix + Dictionary` يعمل مع السالب",
         "md": "لأنه لا يعتمد على «التقليص يقلل المجموع». هو يسأل: «هل رأيت بادئة تساوي `sum - k`؟» — سؤال صحيح رياضيًا لأي أرقام.\n**الثمن:** ذاكرة O(n) (قاموس بكل البادئات).\n**متى تختار النافذة بدلًا منه؟** لو الأرقام موجبة والعايز **أطول/أقصر** بمعيار أحادي — النافذة O(1) ذاكرة وأقل تعقيدًا."},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تحدد النمط من صياغة السؤال قبل كتابة أي كود.",
            "تعرف أن مؤشري الطرفين يحتاجان ترتيبًا وتحسب O(n log n).",
            "تكتب نافذة ثابتة بحجم k بتحديث O(1) لكل خطوة.",
            "تكتب نافذة متغيرة بشرط تقليص صحيح وتشرح حدود `l <= r`.",
            "تعرف أن النافذة المتغيرة تتعطل مع الأرقام السالبة.",
            "تكتب Kadane مع بداية ونهاية النطاق لا المجموع فقط.",
            "تنفّذ deque رتيبة للأقصى في نافذة بـO(n).",
            "تستخدم بادئة بطول n+1 وتستخرج مجموع نطاق بـ`pre[r+1] - pre[l]`.",
            "تعدّ النطاقات بمجموع k بـ`Dictionary` (يعمل مع السالب).",
            "تستخدم difference array لتعديلات نطاقات كثيرة.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "8 أسئلة.",
         "questions": [
             {"q": "أطول نطاق مجموعه ≤ 10 في مصفوفة فيها أرقام سالبة — هل تصلح النافذة المتغيرة؟",
              "options": ["نعم", "لا — التقليص قد يزيد المجموع؛ استخدم prefix + Dictionary",
                          "نعم لو كان الحجم ثابتًا", "لا يوجد حل"],
              "answer": 1,
              "explain": "النافذة المتغيرة تفترض أن إزالة عنصر تقلل المقياس. مع السالب قد تزيد، فينهار الافتراض ويصبح الحل صامتًا وخاطئًا — وهذا من أخطر الأخطاء لأنه يمر في الاختبارات البسيطة."},
             {"q": "ما تعقيد `CountSubarraysSumK`؟",
              "options": ["O(n²)", "O(n) زمن وO(n) مساحة", "O(n log n)", "O(1)"],
              "answer": 1,
              "explain": "تمريرة واحدة مع قاموس للبادئات: O(n) زمن، وقاموس بحجم n. المقايضة: مساحة مقابل تحويل O(n²) إلى O(n)."},
             {"q": "لماذا `l < r` وليس `l <= r` في PairSum؟",
              "options": ["لتقليل التكرار", "لمنع استخدام العنصر نفسه مرتين (l == r يعطي مجموع 2× نفس العنصر)",
                          "لتحسين الأداء", "لا فرق"],
              "answer": 1,
              "explain": "`l == r` يعني جمع العنصر مع نفسه، وهذا غالبًا غير مسموح. نفس القاعدة تنطبق في 3Sum: `l < r` بعد أن يكون `i` ثابتًا."},
             {"q": "في نافذة بحجم k، كيف تجعل التحديث O(1)؟",
              "options": ["أعد جمع النافذة", "أضف العنصر الداخل واخصم الخارج: `sum += a[i] - a[i-k]`",
                          "استخدم فرزًا", "استخدم Set"],
              "answer": 1,
              "explain": "إعادة الجمع تعني O(n·k). التحديث بفارق واحد O(1) يحول الخوارزمية إلى O(n) كاملة. نفس المبدأ ينطبق على المتوسط والتباين والعدّادات."},
             {"q": "Kadane — ماذا تفعل عندما يكون `nums[i] > cur + nums[i]`؟",
              "options": ["أضيف العنصر", "أبدأ نطاقًا جديدًا من هذا العنصر (لأن ما قبله يضرّ)",
                          "أتوقف", "أعيد التعيين لصفر"],
              "answer": 1,
              "explain": "إذا كان ما قبل العنصر يقلل المجموع، فالأفضل بدء نطاق جديد. تتبّع `curStart` يتيح لك إعادة النطاق نفسه لا المجموع فقط — وهذا ما يسأل عنه المحاورون."},
             {"q": "لماذا `pre` بطول n+1 بدل n؟",
              "options": ["توفير ذاكرة", "ليكون لدى النطاق الفارغ بادئة (pre[0]=0) وتصبح صيغة `pre[r+1]-pre[l]` موحدة بلا حالات خاصة",
                          "لأن .NET يفرض ذلك", "لتحسين الأداء فقط"],
              "answer": 1,
              "explain": "إضافة عنصر صفري في البداية تلغي الحالات الخاصة عند l = 0. هذا نمط عام في البرمجة: صفّ حارس (sentinel) يبسّط الحدود ويمنع off-by-one."},
             {"q": "Deque رتيبة — لماذا نزيل من الخلف كل ما هو أصغر؟",
              "options": ["لتوفير ذاكرة", "لأن أي عنصر أصغر سيخرج قبل الحالي وليس له أمل أن يكون الأقصى — فيمكن الاستغناء عنه",
                          "للترتيب الأبجدي", "لتفادي التكرار"],
              "answer": 1,
              "explain": "إذا دخل عنصر أكبر، فكل عنصر أصغر قبله سيُغطى بهذا الأكبر داخل أي نافذة تحتويه. إبقاؤه بلا فائدة. النتيجة deque تنازلية تعطي الأقصى من الرأس بـO(1)."},
             {"q": "Difference array تُستخدم عندما:",
              "options": ["قراءة كثيرة وتعديل قليل", "تعديلات نطاقات كثيرة ثم قراءة — O(1) لكل تعديل وO(n) مرة واحدة للبناء النهائي",
                          "مصفوفة ثابتة", "بيانات نصية"],
              "answer": 1,
              "explain": "بدل O(n) لكل تعديل، نسجّل التغيير عند بداية النطاق وعكسه عند نهايته. ثم تمريرة بادئة تعطي القيم النهائية. مثالي لتقارير «أضف X لكل مستخدم من L إلى R»."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "تطبيق + مقارنة.",
         "items": [
            {"id": "s9-m2-l4-t1",
             "title": "مهمة 1: 6 مسائل بثلاثة أنماط",
             "md": "حل: PairSum · 3Sum · LongestAtMost · LongestUniqueSubstring · CountSubarraysSumK · MaxSubArray. كل حل: تعقيد + اختبارات + نسخة ساذجة للمقارنة.",
             "criteria": [
                 "6 حلول تعمل + 5 اختبارات لكل حل (فارغ · عنصر واحد · الكل مكرر · أرقام سالبة حيث ينطبق · حدود).",
                 "تعقيد مكتوب لكل حل (زمن + مساحة) مع التبرير.",
                 "نسخة O(n²) لكل مسألة + اختبار تكافؤ عشوائي 1000 حالة.",
                 "شرح مكتوب: أي مسألة لا تصلح لها النافذة المتغيرة ولماذا.",
                 "حالة أرقام سالبة في CountSubarraysSumK تعمل بشكل صحيح (والنافذة تفشل — موثّق).",
             ],
             "hint": "ابدأ بالنسخة الساذجة دائمًا — تعطيك مصدر حقيقة للاختبار العشوائي. وللـ3Sum: اختبر مصفوفة كلها أصفار `[0,0,0,0]` — يجب أن تُرجع ثلاثية واحدة فقط (وهو ما يكشف أخطاء تجاوز التكرار).",
             "solution": "النتيجة النموذجية: الحلول الخطية تمر على 1000 حالة عشوائية مقارنة بالساذجة. أكثر خطأ يظهر: نسيان `+1` في الطول أو فشل تخطي التكرار في 3Sum. الاختبار العشوائي هو ما يكشفها فورًا.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.dictionary-2",
                 "https://learn.microsoft.com/dotnet/api/system.array.sort",
             ]},
            {"id": "s9-m2-l4-t2",
             "title": "مهمة 2: عدّاد معدل حقيقي (Rate limiter) بالنافذة",
             "md": "نفّذ عدّاد معدل لطلبات API بنافذة زمنية منزلقة: 100 طلب/دقيقة لكل مستخدم. ثم نسخة ثابتة النافذة، وقارن السلوك عند الحدود.",
             "criteria": [
                 "نافذة منزلقة دقيقة (deque بزمن الطلبات) — تسمح 100 في أي 60 ثانية متحركة.",
                 "نافذة ثابتة (عدّاد كل دقيقة) — وأظهر حالتي الحدود (burst) بالأرقام.",
                 "متعدد الخيوط: 20 خيطًا لا يحققون أكثر من 100 نجاح (`Interlocked` أو lock).",
                 "اختبار بالزمن المُزيف (`TimeProvider`) بلا انتظار حقيقي.",
                 "جدول مقارنة: عدد الطلبات المسموح بها في سيناريو ذروة على الحد الفاصل.",
             ],
             "hint": "استخدم `TimeProvider.GetUtcNow()` بدل `DateTime.UtcNow` لتتمكن من اختبار الزمن. النافذة المنزلقة: `Deque<(timestamp)>` — عند كل طلب أزل كل ما هو أقدم من `now - 60s` ثم افحص الطول. لا تسجّل كل الطلبات في Redis للتجربة المحلية؛ يكفي في الذاكرة.",
             "solution": "النتيجة: النافذة المنزلقة أكثر دقة لكنها تخزّن 100 طابع زمني/مستخدم؛ الثابتة أرخص لكنها تسمح بانفجار حتى 200 طلب في ثانيتين على الحد. وهذا قرار حقيقي في الإنتاج: دقة مقابل ذاكرة. النسخة الإنتاجية غالبًا token bucket بـ`Redis` scripts.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.threading.interlocked",
                 "https://learn.microsoft.com/dotnet/api/system.timeprovider",
                 "https://learn.microsoft.com/aspnet/core/performance/rate-limit",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Rate limiting في ASP.NET Core", "url": "https://learn.microsoft.com/aspnet/core/performance/rate-limit"},
            {"label": "Dictionary<TKey,TValue>", "url": "https://learn.microsoft.com/dotnet/api/system.collections.generic.dictionary-2"},
            {"label": "TimeProvider (اختبار الزمن)", "url": "https://learn.microsoft.com/dotnet/api/system.timeprovider"},
            {"label": "Span<T> وReadOnlySpan<T>", "url": "https://learn.microsoft.com/dotnet/standard/memory-and-spans/"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════
# l5 — تمرين موقوت: 20 مسألة
# ══════════════════════════════════════════════════════════════════
_L5 = {
    "id": "s9-m2-l5",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الدرس ده **جلسة تدريب موقوتة، مش قراءة**. 40 دقيقة: 20 مسألة في **دفعتين** (10 × 15 دقيقة لكل دفعة مع مراجعة) — لأن المقابلة الحقيقية لا تعطيك وقتًا مفتوحًا.\n\nالعنوان الكبير: *التدريب على التسليم تحت ضغط* — اللي بتفتقده أكثر من المعرفة هو **إدارة الوقت** و**الكلام أثناء الحل**."},

        {"type": "terms", "title": "قواعد الجلسة", "items": [
            {"term": "Timeboxing", "def": "سقف زمني صارم لكل مسألة: 8 دقائق للمتوسط. إذا لم تنته، توقف — وسجّل السبب بدل الاستمرار."},
            {"term": "Think aloud", "def": "الكلام بصوت عالٍ أثناء الحل: المتطلب → النمط → التعقيد → الكود. المحاور يقيس التواصل لا الكود فقط."},
            {"term": "Clarify first", "def": "أسئلة قبل الكود: الحدود؟ الأرقام سالبة؟ هل نعدّل المكان؟ حجم المدخل؟ هذا يعطيك 1–2 دقيقة مجانية."},
            {"term": "Brute force then optimize", "def": "ابدأ بالحل الساذج على السبورة (يضمن وجود حل)، ثم حسّنه أمام المحاور — الطريقة الأكثر قبولًا."},
            {"term": "Dry run", "def": "تتبّع يدوي بمثال صغير قبل التشغيل — يكشف 80% من أخطاء الحدود."},
            {"term": "Error log", "def": "سجل أخطائك المتكررة (off-by-one · نسيان visited · شرط تقليص). استهدافه يضاعف تحسنك."},
            {"term": "Spaced repetition", "def": "أعد حل نفس المسألة بعد يوم وأسبوع — أسرع من حل مسائل جديدة دون تثبيت."},
            {"term": "Pattern recall", "def": "لكل مسألة: اكتب اسم النمط قبل الكود. لو لم تعرف النمط، فالمشكلة في التصنيف لا في التنفيذ."},
        ]},

        {"type": "heading", "level": 2, "text": "① الدفعة A — 10 مسائل (15 دقيقة)"},
        {"type": "table", "caption": "احسب النتيجة: 1 نقطة للحل الصحيح، 0.5 إذا عرفت النمط بلا وقت كافٍ",
         "head": ["#", "المسألة", "النمط", "الهدف الزمني"],
         "rows": [
             ["1", "أقصى عنصر في مصفوفة", "مسح خطي", "1 د"],
             ["2", "هل السلسلة متناظرة (palindrome)؟", "مؤشران طرفان", "2 د"],
             ["3", "عكس مصفوفة في المكان", "مؤشران", "2 د"],
             ["4", "أقصى مجموع نطاق متصل", "Kadane", "5 د"],
             ["5", "ثاني أكبر عنصر (بلا فرز)", "مسح بحالتين", "3 د"],
             ["6", "أول عنصر غير مكرر في سلسلة", "Dictionary + مسحين", "5 د"],
             ["7", "دمج مصفوفتين مرتّبتين", "مؤشران", "5 د"],
             ["8", "إزالة التكرارات في المكان", "مؤشران نفس الاتجاه", "4 د"],
             ["9", "أقصى فرق بين عنصرين (الأصغر قبل الأكبر)", "مسح بحد أدنى", "5 د"],
             ["10", "تاريخان — عدد الأيام بينهما", "DateTime + تحقق حدود", "4 د"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Timed/SetA.cs — الحلول المرجعية للدفعة A", "filename": "Algorithms/TimedSetA.cs", "code": r'''public static class TimedSetA
{
    // 1) O(n)
    public static int Max(int[] a)
    {
        if (a.Length == 0) throw new ArgumentException("فارغة");
        var m = a[0];
        foreach (var x in a) if (x > m) m = x;
        return m;
    }

    // 2) O(n) · O(1)
    public static bool IsPalindrome(ReadOnlySpan<char> s)
    {
        int l = 0, r = s.Length - 1;
        while (l < r) { if (s[l] != s[r]) return false; l++; r--; }
        return true;
    }

    // 3) O(n) · O(1)
    public static void ReverseInPlace(Span<int> a)
    {
        for (int i = 0, j = a.Length - 1; i < j; i++, j--)
            (a[i], a[j]) = (a[j], a[i]);
    }

    // 4) Kadane — O(n)
    public static int MaxSubArray(int[] a)
    {
        var best = a[0]; var cur = a[0];
        for (var i = 1; i < a.Length; i++)
        {
            cur = Math.Max(a[i], cur + a[i]);
            best = Math.Max(best, cur);
        }
        return best;
    }

    // 5) ثاني أكبر — O(n) · O(1) — انتبه للتكرارات
    public static int? SecondLargest(int[] a)
    {
        if (a.Length < 2) return null;
        int first = int.MinValue, second = int.MinValue;

        foreach (var x in a)
        {
            if (x > first) { second = first; first = x; }
            else if (x < first && x > second) second = x;   // ✅ التكرار يُتجاهل
        }
        return second == int.MinValue ? null : second;
    }

    // 6) أول عنصر غير مكرر — O(n)
    public static int? FirstUnique(ReadOnlySpan<char> s)
    {
        Span<int> counts = stackalloc int[128];
        foreach (var c in s) counts[c]++;

        for (var i = 0; i < s.Length; i++)
            if (counts[s[i]] == 1) return i;
        return null;
    }

    // 7) دمج مرتّبتين — O(n+m) · O(n+m)
    public static int[] MergeSorted(int[] a, int[] b)
    {
        var result = new int[a.Length + b.Length];
        int i = 0, j = 0, k = 0;

        while (i < a.Length && j < b.Length)
            result[k++] = a[i] <= b[j] ? a[i++] : b[j++];

        while (i < a.Length) result[k++] = a[i++];
        while (j < b.Length) result[k++] = b[j++];
        return result;
    }

    // 8) إزالة التكرارات — O(n) · O(1)
    public static int RemoveDuplicates(Span<int> sorted)
    {
        if (sorted.Length == 0) return 0;
        var w = 1;
        for (var r = 1; r < sorted.Length; r++)
            if (sorted[r] != sorted[w - 1]) sorted[w++] = sorted[r];
        return w;
    }

    // 9) أقصى فرق (بيع ثم شراء) — O(n)
    public static int MaxProfit(int[] prices)
    {
        var min = prices[0];
        var best = 0;
        foreach (var p in prices)
        {
            if (p < min) min = p;
            else if (p - min > best) best = p - min;
        }
        return best;
    }

    // 10) فرق الأيام — انتبه للحدود والتوقيت
    public static int DaysBetween(DateOnly from, DateOnly to) =>
        Math.Abs(to.DayNumber - from.DayNumber);
}'''},
        {"type": "callout", "kind": "tip", "title": "الدفعة A عالمية: 15 دقيقة واقعية؟",
         "md": "المسائل 1–9 تُحل في ~10 دقائق لو الأنماط محفوظة. المسألة 10 سهلة لكن **شرطها هو التحقق**: تواريخ صالحة · `DateOnly` بدل `DateTime` (لا مشاكل توقيت) · الفرق قد يكون سالبًا.\n**أضف 2 دقيقة للقراءة والتحقق في كل مسألة** — هذا الواقع في المقابلة: 40% من الوقت يذهب للفهم لا للكتابة."},

        {"type": "heading", "level": 2, "text": "② الدفعة B — 10 مسائل (20 دقيقة)"},
        {"type": "table", "caption": "مستوى أعلى قليلًا — نفس الأنماط بتوليف",
         "head": ["#", "المسألة", "النمط", "الهدف"],
         "rows": [
             ["11", "زوجان مجموعهما هدف في مصفوفة مرتّبة", "مؤشران طرفان", "3 د"],
             ["12", "أطول سلسلة بلا تكرار", "نافذة متغيرة", "7 د"],
             ["13", "أقصر نطاق مجموعه ≥ هدف (موجبة)", "نافذة متغيرة", "7 د"],
             ["14", "عدّ النطاقات التي مجموعها k", "prefix + Dictionary", "8 د"],
             ["15", "أقصى متوسط نافذة بحجم k", "نافذة ثابتة", "4 د"],
             ["16", "أكبر عنصر في كل نافذة بحجم k", "deque رتيبة", "10 د"],
             ["17", "قوسان صالحان؟", "مكدس", "4 د"],
             ["18", "دمج نطاقات متداخلة", "فرز + مؤشر", "7 د"],
             ["19", "دوران مصفوفة بمقدار k", "عكس ثلاث مرات", "6 د"],
             ["20", "بحث في مصفوفة مدوّرة مرتّبة", "بحث ثنائي معدّل", "8 د"],
         ]},
        {"type": "code", "lang": "csharp", "title": "Timed/SetB.cs — الحلول المرجعية للدفعة B (مختصرة)", "filename": "Algorithms/TimedSetB.cs", "code": r'''public static class TimedSetB
{
    // 11) مؤشران
    public static (int, int)? PairSum(int[] sorted, int t)
    {
        int l = 0, r = sorted.Length - 1;
        while (l < r)
        {
            var s = sorted[l] + sorted[r];
            if (s == t) return (l, r);
            if (s < t) l++; else r--;
        }
        return null;
    }

    // 12) نافذة متغيرة — O(n)
    public static int LongestUnique(ReadOnlySpan<char> s)
    {
        Span<int> last = stackalloc int[128];
        last.Fill(-1);
        int l = 0, best = 0;
        for (var r = 0; r < s.Length; r++)
        {
            if (last[s[r]] >= l) l = last[s[r]] + 1;
            last[s[r]] = r;
            best = Math.Max(best, r - l + 1);
        }
        return best;
    }

    // 13) أقصر نطاق مجموعه ≥ t
    public static int MinLen(int[] a, int t)
    {
        int l = 0, sum = 0, best = int.MaxValue;
        for (var r = 0; r < a.Length; r++)
        {
            sum += a[r];
            while (sum >= t) { best = Math.Min(best, r - l + 1); sum -= a[l++]; }
        }
        return best == int.MaxValue ? 0 : best;
    }

    // 14) عدّ النطاقات
    public static int CountSumK(int[] a, int k)
    {
        var seen = new Dictionary<long, int> { [0] = 1 };
        long sum = 0; var count = 0;
        foreach (var x in a)
        {
            sum += x;
            if (seen.TryGetValue(sum - k, out var c)) count += c;
            seen[sum] = seen.GetValueOrDefault(sum) + 1;
        }
        return count;
    }

    // 15) نافذة ثابتة
    public static double MaxAvg(int[] a, int k)
    {
        double sum = 0;
        for (var i = 0; i < k; i++) sum += a[i];
        var best = sum;
        for (var i = k; i < a.Length; i++)
        {
            sum += a[i] - a[i - k];
            if (sum > best) best = sum;
        }
        return best / k;
    }

    // 16) deque رتيبة
    public static int[] MaxInWindow(int[] a, int k)
    {
        var res = new int[a.Length - k + 1];
        var dq = new LinkedList<int>();
        for (var i = 0; i < a.Length; i++)
        {
            if (dq.First is { } f && f.Value <= i - k) dq.RemoveFirst();
            while (dq.Last is { } l && a[l.Value] <= a[i]) dq.RemoveLast();
            dq.AddLast(i);
            if (i >= k - 1) res[i - k + 1] = a[dq.First!.Value];
        }
        return res;
    }

    // 17) أقواس
    public static bool ValidBrackets(ReadOnlySpan<char> s)
    {
        Span<char> st = stackalloc char[Math.Min(s.Length, 512)];
        var top = 0;
        foreach (var c in s)
        {
            if (c is '(' or '[' or '{') { if (top == st.Length) return false; st[top++] = c; }
            else if (c is ')' or ']' or '}')
            {
                if (top == 0) return false;
                var open = st[--top];
                if ((c == ')' && open != '(') || (c == ']' && open != '[') || (c == '}' && open != '{'))
                    return false;
            }
        }
        return top == 0;
    }

    // 18) دمج نطاقات
    public static IReadOnlyList<(int, int)> Merge(IEnumerable<(int S, int E)> intervals)
    {
        var sorted = intervals.OrderBy(i => i.S).ThenBy(i => i.E).ToList();
        var result = new List<(int, int)>();
        foreach (var (s, e) in sorted)
        {
            if (result.Count > 0 && s <= result[^1].Item2)          // متداخل
                result[^1] = (result[^1].Item1, Math.Max(result[^1].Item2, e));
            else result.Add((s, e));
        }
        return result;
    }

    // 19) دوران بعكس ثلاث مرات — O(n) · O(1)
    public static void Rotate(Span<int> a, int k)
    {
        if (a.Length == 0) return;
        k %= a.Length;
        if (k < 0) k += a.Length;
        Reverse(a);                       // كل المصفوفة
        Reverse(a[..k]);                  // الجزء الأول
        Reverse(a[k..]);                  // الباقي

        static void Reverse(Span<int> s)
        {
            for (int i = 0, j = s.Length - 1; i < j; i++, j--)
                (s[i], s[j]) = (s[j], s[i]);
        }
    }

    // 20) بحث ثنائي في مدوّرة — O(log n)
    public static int SearchRotated(int[] a, int target)
    {
        int lo = 0, hi = a.Length - 1;
        while (lo <= hi)
        {
            var mid = lo + ((hi - lo) >> 1);
            if (a[mid] == target) return mid;

            // أي نصف مرتّب؟
            if (a[lo] <= a[mid])                                   // اليسار مرتّب
            {
                if (target >= a[lo] && target < a[mid]) hi = mid - 1;
                else lo = mid + 1;
            }
            else                                                   // اليمين مرتّب
            {
                if (target > a[mid] && target <= a[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }
}'''},
        {"type": "callout", "kind": "warn", "title": "مسألتان فيهما فخ حقيقي",
         "md": "**#16 (deque):** إذا نسيت `<=` عند إزالة الخلف، ستحتفظ بعناصر مكافئة ويزداد الحجم — النتيجة صحيحة لكن الأداء ينحرف. وإذا نسيت إزالة الخلف **قبل** الإضافة، يخرج الأقصى القديم.\n**#20 (مدوّرة):** الخطأ الشائع هو `target >= a[lo]` بدل `>` أو نسيان المساواة على الطرف. اختبرها بـ`[4,5,6,7,0,1,2]` مع أهداف: 0 · 4 · 7 · 3 (غير موجود) · 9."},

        {"type": "heading", "level": 2, "text": "③ بعد الجلسة: التقييم والسجل"},
        {"type": "table", "caption": "كيف تقيس نفسك (لا «حليت/ما حلتش»)",
         "head": ["المؤشر", "كيف تقيسه", "الهدف", "إن لم تصل"],
         "rows": [
             ["نسبة الحل الصحيح من أول محاولة", "عدد المسائل بلا تشغيل", "≥ 60%", "راجع الأنماط لا الكود"],
             ["زمن الوصول للنمط", "سجّل الوقت قبل الكتابة", "≤ 60 ثانية", "تمرين تصنيف: 30 مسألة في 10 دقائق"],
             ["أخطاء الحدود", "عدّها في سجلك", "≤ 2 لكل 10", "dry run إلزامي بمثال صغير"],
             ["جودة الشرح", "سجّل نفسك صوتيًا مرة", "منظم: متطلب → نمط → تعقيد → كود → اختبار", "تدرّب مع شخص/كاميرا"],
             ["الوقت الكلي", "40 دقيقة", "≥ 14 مسألة", "قلّل زمن التفكير وابدأ بالحل الساذج"],
         ]},
        {"type": "code", "lang": "text", "title": "تمبلت سجل الأخطاء (استخدمه كل جلسة)", "filename": "docs/error-log.txt", "code": r'''
| # | المسألة | النمط | الوقت | الخطأ | التصنيف | الإصلاح |
|---|---------|-------|-------|-------|---------|---------|
| 1 | أطول سلسلة بلا تكرار | نافذة | 9د   | نسيت r-l+1 | حدود | اصطلاح [l,r] موثّق |
| 2 | عدّ النطاقات | prefix | 12د  | نسيت البادئة [0]=1 | حالة خاصة | قائمة تحقق |
| 3 | أقصى في نافذة | deque | 15د  | أزلت الخلف بعد الإضافة | ترتيب | خطوات مكتوبة |

تصنيفات الأخطاء: حدود · نمط خاطئ · حالة خاصة · ترتيب عمليات · تعقيد · لغة/API.
كل أسبوع: أكثر تصنيف متكرر ⇒ درس واحد مركّز عليه.
'''},

        {"type": "checkpoints", "title": "هل أنت جاهز؟", "items": [
            "أنجزت 20 مسألة في ≤ 40 دقيقة (أو 14+ مع تسجيل أسباب التأخير).",
            "حصلت على ≥ 60% صحيح من أول محاولة بدون تشغيل.",
            "سجّلت النمط لكل مسألة قبل كتابة الكود.",
            "أكثر من 13 مسألة بلا خطأ حدود واحد.",
            "شرحت مسألتين بصوت عالٍ في دقيقتين لكل منهما.",
            "عندك سجل أخطاء مكتوب بتصنيفات (لا «أخطاء عامة»).",
            "تعرف 3 نقاط ضعف حقيقية وخصّصت لها تدريبًا الأسبوع القادم.",
        ]},

        {"type": "tasks", "title": "التسليم", "intro": "جلسة موثّقة.",
         "items": [
            {"id": "s9-m2-l5-t1",
             "title": "سجّل جلسة 40 دقيقة كاملة",
             "md": "نفّذ الجلستين (A وB) بمؤقت حقيقي، بدون إنترنت، وسجّل كل شيء في سجل الأخطاء، ثم قيّم نفسك بالجدول أعلاه.",
             "criteria": [
                 "40 دقيقة موقّتة فعلًا (لقطة من المؤقّت أو الطابع الزمني).",
                 "أكواد 20 مسألة محفوظة (حتى غير المكتملة) في مستودع.",
                 "سجل أخطاء مُصنّف لكل مسألة أخفقت فيها.",
                 "تقييم مكتوب بأرقام: نسبة النجاح · زمن الوصول للنمط · عدد أخطاء الحدود.",
                 "تسجيل صوتي/فيديو لمسألتين بصوت عالٍ (2 دقيقة لكل واحدة).",
                 "خطة تدريب الأسبوع التالي: 3 مسائل مستهدفة بنوع الخطأ المتكرر.",
             ],
             "hint": "لا تستخدم الإنترنت أو مساعد AI — الجلسة قياس لقدرتك الحالية. اختر 3 مسائل من الـ20 لإعادة حلها بعد 48 ساعة (spaced repetition). وإن لم تكمل 20، سجّل السبب بصراحة: هل كان نمطًا مفقودًا أم تنفيذًا بطيئًا أم قراءة سيئة للسؤال؟ — الجواب يحدد تدريبك.",
             "solution": "النتيجة النموذجية لأول جلسة: 12–15 مسألة، ونسبة نجاح 50–65%. الأخطاء الأكثر شيوعًا: حدود (40%) ونمط خاطئ (25%). بعد 3 جلسات موثّقة تصبح 18 مسألة و≥75% — والتحسن الحقيقي يأتي من **تصنيف الأخطاء** لا من حل مسائل أكثر.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/api/system.diagnostics.stopwatch",
                 "https://learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "مجموعات مسائل .NET/C#", "url": "https://learn.microsoft.com/dotnet/csharp/"},
            {"label": "Stopwatch (قياس الزمن)", "url": "https://learn.microsoft.com/dotnet/api/system.diagnostics.stopwatch"},
            {"label": "TimeProvider", "url": "https://learn.microsoft.com/dotnet/api/system.timeprovider"},
        ]},
    ],
}

LESSONS_S9_E = [_L4, _L5]
