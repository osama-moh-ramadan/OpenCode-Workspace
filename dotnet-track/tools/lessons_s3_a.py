"""Stage 3, Module 1 — SQL you must know without an ORM (lessons 1-3 of 3)."""

TODAY = "2026-10-22"

LESSONS_S3_A = [
    # ------------------------------------------------------------------ l1
    {
        "id": "s3-m1-l1",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
الـORM بيكتب SQL — وأنت لازم تقدر **تقرأ** اللي كتبه وتحكم عليه. في المقابلات والسؤال الأشهر:
«استعلام بيستغرق 3 ثواني، بتعمل إيه؟» الإجابة الصح مش «أضيف فهرس» — الإجابة: **اقرأ خطة التنفيذ**،
اعرف الفرق بين التقدير والواقع، وبعدين قرّر.

الدرس ده (PostgreSQL أساسًا مع المقابل في SQL Server): أنواع الفهارس وترتيب الأعمدة، قراءة `EXPLAIN ANALYZE`،
واكتشاف الفهارس غير المستخدمة والزائدة والناقصة.
"""},
            {"type": "terms", "items": [
                {"term": "B-tree", "def": "البنية الافتراضية للفهارس: بحث/نطاق/ترتيب بـ`O(log n)`. لا يفيد في `LIKE '%abc%'` ولا في دوال على العمود."},
                {"term": "Clustered index", "def": "ترتيب الصفوف الفعلي في الجدول (واحد فقط لكل جدول). في Postgres: `CLUSTER` (لمرة واحدة) — مش زي SQL Server."},
                {"term": "Nonclustered / Secondary", "def": "فهرس منفصل عن ترتيب الصفوف؛ في Postgres كل الفهارس `CREATE INDEX` من النوع ده."},
                {"term": "Composite index", "def": "فهرس على أكثر من عمود — الترتيب حاسم: أعمدة المساواة أولًا ثم عمود النطاق/الترتيب."},
                {"term": "Covering index (`INCLUDE`)", "def": "فهرس يحتوي الأعمدة المطلوبة في الاستعلام → بلا رجوع للجدول (Index Only Scan)."},
                {"term": "Partial / Filtered index", "def": "فهرس على جزء من الصفوف (`WHERE deleted_at IS NULL`) — أصغر وأسرع وأدق."},
                {"term": "Seq Scan", "def": "مسح كامل للجدول. مش دائمًا خطأ: لو هتقرأ أغلب الصفوف، المسح أسرع من الفهرس."},
                {"term": "Index Scan مقابل Bitmap Heap Scan", "def": "الأول يجلب صفوفًا مرتبة واحدًا واحدًا؛ التاني يجمع مواقع أولًا (أفضل للانتقائية المنخفضة/الترتيب العشوائي)."},
                {"term": "Selectivity / Cardinality", "def": "قدرة العمود على تضييق النتيجة. فهرس على عمود `boolean` = انتقائية شبه معدومة = غالبًا بلا فائدة."},
                {"term": "Key Lookup", "def": "(SQL Server) رجوع للجدول لجلب أعمدة غير موجودة في الفهرس — مكلف جدًا؛ حله `INCLUDE`."},
            ]},
            {"type": "heading", "level": 2, "text": "1) قراءة خطة التنفيذ: المهارة الأساسية"},
            {"type": "code", "lang": "sql", "filename": "diagnostics/explain.sql", "title": "EXPLAIN ANALYZE مع BUFFERS — والمصادر التانية للتشخيص", "code": r'''
-- ★ ANALYZE = تنفيذ فعلي (احذر على UPDATE/DELETE: لفّها في transaction واعمل ROLLBACK)
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT o.id, o.created_at, o.total, c.country
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid'
  AND o.created_at >= now() - interval '30 days'
ORDER BY o.created_at DESC, o.id DESC
LIMIT 21;

-- للأمان مع الكتابات:
BEGIN;
EXPLAIN (ANALYZE, BUFFERS) UPDATE orders SET status = 'shipped' WHERE status = 'paid';
ROLLBACK;

-- أبطأ الاستعلامات إجمالًا (يتطلب pg_stat_statements)
SELECT round(total_exec_time::numeric, 1) AS total_ms,
       calls,
       round(mean_exec_time::numeric, 2)   AS mean_ms,
       rows,
       left(query, 120)                    AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- جداول بتتمسح بالكامل (علامة فهرس ناقص)
SELECT relname, seq_scan, seq_tup_read, idx_scan,
       round(100.0 * seq_scan / nullif(seq_scan + idx_scan, 0), 1) AS seq_scan_pct
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
'''},
            {"type": "code", "lang": "text", "filename": "خطة تنفيذ حقيقية (معلّقة سطر بسطر)", "title": "إزاي تقرأ المخرَج", "code": r'''
 Limit  (cost=1.42..236.11 rows=21 width=76) (actual time=0.061..2.874 rows=21 loops=1)
   Buffers: shared hit=318
   ->  Index Scan using ix_orders_createdat_id on orders o
         (cost=0.42..5123.90 rows=458 width=48) (actual time=0.041..2.402 rows=210 loops=1)
         Index Cond: (created_at >= (now() - '30 days'))
         Filter: (status = 'paid')
         Rows Removed by Filter: 3912          ← ★ 95% من الصفوف اتقريت واتبعتت!
         Buffers: shared hit=290
   ->  Index Scan using customers_pkey on customers c
         (cost=0.28..0.31 rows=1 width=36) (actual time=0.008..0.009 rows=1 loops=210)
         Buffers: shared hit=28

القراءة:
1) (cost=.. rows=..)  = تقدير المخطط   |   (actual time=.. rows=.. loops=..) = الواقع
   → لو التقدير بعيد عن الواقع (458 مقابل 4122) فالإحصائيات قديمة: ANALYZE orders;
2) "Rows Removed by Filter: 3912"  = الفهرس ما غطّاش status → الحل: فهرس مركّب (status, created_at DESC, id DESC)
3) "Buffers: shared hit=290" مقابل "read=..." = من الكاش مقابل من القرص (read عالي = I/O فعلي)
4) Nested Loop مع loops=210 = استعلام فرعي لكل صف → انتبه لـN+1 على مستوى SQL
5) Sort Method: external merge  Disk: 12MB = تجاوز work_mem → فرز على القرص (بطيء جدًا)
'''},
            {"type": "callout", "kind": "warn", "title": "علامات الخطر في أي خطة تنفيذ",
             "md": """
- **`Rows Removed by Filter` كبيرة** → الفهرس بيغطي شرط واحد بس؛ محتاج فهرس مركّب.
- **تقدير `rows` بعيد عن `actual rows` بعشرات المرات** → إحصائيات قديمة (`ANALYZE`) أو correlation معقد.
- **`Sort Method: external merge Disk`** → فرز على القرص: زوّد `work_mem` للجلسة أو قلّل البيانات أو أضف فهرس يغطي الترتيب.
- **`Seq Scan` على جدول ملايين الصفوف مع انتقائية عالية** → فهرس ناقص.
- **`Nested Loop` مع `loops` بالآلاف** → نمط N+1؛ حوّله لـ`Hash Join` بجلب المفاتيح مرة واحدة.
- **`Key Lookup` (SQL Server) كتير** → الفهرس مش covering؛ أضف `INCLUDE`.
- **`Buffers: shared read` عالي باستمرار** → الكاش (shared_buffers) صغير أو الجدول/الفهرس منتفخ (`VACUUM`/`REINDEX`).
"""},
            {"type": "heading", "level": 2, "text": "2) اختيار الفهرس الصح"},
            {"type": "code", "lang": "sql", "filename": "migrations/2026_10_orders_indexes.sql", "title": "أمثلة عملية — كل فهرس له سبب مكتوب", "code": r'''
-- ① فهرس مركّب للترقيم (cursor pagination من المرحلة 2)
--    الترتيب: مساواة (status) ← نطاق/ترتيب (created_at DESC) ← مكسّر تعادل (id DESC)
--    INCLUDE: يخلي الاستعلام covered (بلا رجوع للجدول)
CREATE INDEX CONCURRENTLY ix_orders_status_created_id
    ON orders (status, created_at DESC, id DESC)
    INCLUDE (customer_id, total, currency);

-- ② فهرس جزئي للصفوف الحية فقط (soft delete): أصغر وأسرع
CREATE INDEX CONCURRENTLY ix_orders_active
    ON orders (customer_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- ③ فهرس على مفتاح أجنبي (Postgres ما بيعملهوش تلقائيًا!)
CREATE INDEX CONCURRENTLY ix_orders_customer_id ON orders (customer_id);

-- ④ فهرس فريد يمنع التكرار على مستوى البيانات (مش على مستوى التطبيق)
CREATE UNIQUE INDEX CONCURRENTLY ux_customers_email ON customers (lower(email));

-- ⑤ JSONB: فهرس GIN لاستعلامات على أعمدة JSON
CREATE INDEX CONCURRENTLY ix_orders_metadata_gin ON orders USING gin (metadata jsonb_path_ops);

-- ⑥ بحث نصي: GIN مع tsvector (أو pg_trgm للـLIKE '%…%')
CREATE INDEX CONCURRENTLY ix_products_name_trgm ON products USING gin (name gin_trgm_ops);

-- ★ CONCURRENTLY: لا يقفل الجدول للكتابة — لكن:
--   • لا يمكن داخل transaction
--   • أبطأ، ولو فشل يسيب فهرس INVALID لازم يتحذف
-- تحقق بعد الإنشاء:
SELECT indexrelid::regclass AS index, indisvalid, indisready
FROM pg_index
WHERE NOT indisvalid;
'''},
            {"type": "table", "head": ["الموقف", "الفهرس المناسب", "ملاحظة"], "rows": [
                ["ترقيم cursor على `(created_at, id)`", "مركّب بترتيب مطابق للـ`ORDER BY`", "بدون `id` كمكسّر تعادل: صفوف مكررة/مفقودة"],
                ["`WHERE status='paid' ORDER BY created_at`", "مركّب: `(status, created_at DESC)`", "المساواة أولًا ثم النطاق/الترتيب — العكس ما يفيدش"],
                ["قراءة أعمدة قليلة ثابتة", "covering بـ`INCLUDE`", "يمنع الرجوع للجدول (Index Only Scan)"],
                ["soft delete / صفوف حية فقط", "partial index بشرط `WHERE`", "أصغر وأدق، لكن الاستعلام لازم يطابق الشرط"],
                ["`LIKE '%كلمة%'`", "GIN + `pg_trgm`", "B-tree العادي لا يعمل مع بادئة غير ثابتة"],
                ["استعلامات على JSON", "GIN على `jsonb` (`jsonb_path_ops`)", "أصغر وأسرع من GIN الافتراضي لمعظم الحالات"],
                ["عمود `boolean` أو حالة بثلاث قيم", "✗ غالبًا لا", "انتقائية منخفضة جدًا؛ الأفضل فهرس مركّب أو partial"],
                ["جدول كتابة كثيفة (logs/events)", "قليل من الفهارس + فهارس partial زمنية", "كل فهرس = تكلفة على كل INSERT/UPDATE"],
            ]},
            {"type": "callout", "kind": "danger", "title": "ترتيب الأعمدة في الفهرس المركّب: القاعدة اللي بتضيّع ساعات",
             "md": """
الفهرس المركّب `(a, b, c)` **بيشتغل كـprefix**: يفيد استعلامات على `(a)`، `(a,b)`، `(a,b,c)` —
لكن **لا يفيد** `(b)` أو `(c)` لوحدها.

والقاعدة الثانية: **أعمدة المساواة أولًا، عمود النطاق/الترتيب آخرًا**.
`(created_at, status)` لاستعلام `WHERE status='paid' AND created_at >= X` بيوقف عند أول نطاق،
بينما `(status, created_at)` بيستخدم الاتنين.

قبل ما تضيف فهرس جديد: اسأل هل فهرس موجود يغطيه كـprefix؟ وهل الجدول بيتكتب فيه كتير؟
"""},
            {"type": "heading", "level": 2, "text": "3) التنظيف: فهارس ميتة وزائدة وناقصة"},
            {"type": "code", "lang": "sql", "filename": "diagnostics/index_hygiene.sql", "title": "3 استعلامات تحافظ بيها على قاعدة بياناتك", "code": r'''
-- ① فهارس غير مستخدمة (احذف بعد مراقبة دورة عمل كاملة: شهر/ربع)
SELECT s.relname            AS table,
       s.indexrelname       AS index,
       s.idx_scan,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size,
       i.indisunique        AS is_unique,          -- ★ لا تحذف فهرسًا يدعم قيدًا
       i.indisprimary       AS is_primary
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0
  AND NOT i.indisunique
  AND NOT i.indisprimary
  AND s.schemaname = 'public'
ORDER BY pg_relation_size(s.indexrelid) DESC;

-- ② فهارس زائدة (نفس الجدول والأعمدة بالترتيب) — الأكبر غالبًا هو الزائد
WITH defs AS (
  SELECT tablename, indexname, indexdef,
         row_number() OVER (PARTITION BY tablename, indexdef ORDER BY indexname) AS rn
  FROM pg_indexes
  WHERE schemaname = 'public'
)
SELECT tablename, indexname, indexdef FROM defs WHERE rn > 1;

-- ③ فهارس prefix-zائدة: (a) موجود و(a,b) موجود → (a) غالبًا بلا داعٍ
SELECT a.indexrelid::regclass AS maybe_redundant,
       b.indexrelid::regclass AS covered_by
FROM pg_index a
JOIN pg_index b
  ON a.indrelid = b.indrelid
 AND a.indrelid <> 0
 AND a.indkey::text <> b.indkey::text
 AND b.indkey::text LIKE a.indkey::text || ' %'      -- b يبدأ بأعمدة a
 AND a.indrelid::regclass::text NOT LIKE 'pg_%';

-- تكلفة الفهارس على الكتابة (قبل ما تضيف واحد جديد)
SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd DESC
LIMIT 15;

-- تضخم الفهرس (bloat) وإعادة البناء بلا قفل
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes ORDER BY pg_relation_size(indexrelid) DESC LIMIT 15;
-- REINDEX INDEX CONCURRENTLY ix_orders_status_created_id;
'''},
            {"type": "code", "lang": "sql", "filename": "المقابل في SQL Server", "title": "لو مشروعك SQL Server", "code": r'''
SET STATISTICS IO, TIME ON;
SELECT ... ;                     -- راجع رسائل tab "Messages": logical reads لكل جدول
SET STATISTICS IO, TIME OFF;

-- الفهارس غير المستخدمة
SELECT OBJECT_NAME(s.object_id) AS table_name, i.name AS index_name,
       s.user_seeks, s.user_scans, s.user_lookups, s.user_updates,
       p.rows
FROM sys.dm_db_index_usage_stats s
JOIN sys.indexes i ON i.object_id = s.object_id AND i.index_id = s.index_id
JOIN sys.partitions p ON p.object_id = s.object_id AND p.index_id = s.index_id
WHERE s.database_id = DB_ID() AND i.index_id > 0
ORDER BY s.user_seeks + s.user_scans + s.user_lookups ASC;

-- الفهارس المقترحة (استرشادية — لا تطبقها أعمى: فيها تكرار وتكلفة كتابة)
SELECT OBJECT_NAME(d.object_id) AS table_name, d.equality_columns, d.inequality_columns,
       d.included_columns, s.user_seeks, s.avg_total_user_cost
FROM sys.dm_db_missing_index_details d
JOIN sys.dm_db_missing_index_groups g ON g.index_handle = d.index_handle
JOIN sys.dm_db_missing_index_group_stats s ON s.group_handle = g.index_group_handle
ORDER BY s.user_seeks * s.avg_total_user_cost DESC;

-- فهرس covering
CREATE NONCLUSTERED INDEX ix_orders_status_created
    ON orders (status, created_at DESC) INCLUDE (customer_id, total, currency);

-- فهرس مفلتر
CREATE NONCLUSTERED INDEX ix_orders_active ON orders (customer_id, created_at DESC)
    WHERE deleted_at IS NULL;
'''},
            {"type": "heading", "level": 2, "text": "منهجية العمل: 5 خطوات مش «جرّب فهرس»"},
            {"type": "steps", "title": "استعلام بطيء؟ امشي بالترتيب", "items": [
                {"title": "التقط الاستعلام الحقيقي",
                 "md": "من `pg_stat_statements` أو من لوجات EF Core (`EnableSensitiveDataLogging` في التطوير فقط) — مش من تخمينك. انتبه: استعلام الـORM ممكن يختلف عمّا تتوقع (فرز/أعمدة زائدة)."},
                {"title": "اقرأ الخطة بالأرقام",
                 "md": "`EXPLAIN (ANALYZE, BUFFERS)`. حدد: أنهي عقدة بتاخد أكبر وقت فعلي؟ هل التقدير قريب من الواقع؟ هل فيه `Rows Removed by Filter` أو فرز على القرص؟"},
                {"title": "شكّك في الاستعلام قبل الفهرس",
                 "md": "هل بتجلب أعمدة ما تحتاجهاش؟ هل فيه `ORDER BY` بلا `LIMIT`؟ هل الـ`JOIN` لازم؟ هل ممكن projection بدل كيانات كاملة؟ كثير من البطء سببه الاستعلام مش الفهرس."},
                {"title": "أضف/عدّل فهرس واحد وقِس",
                 "md": "تغيير واحد في المرة، و`ANALYZE` بعد التغيير. قِس p95 تحت حمل (مش مرة واحدة) — التحسن العشوائي بيخدع."},
                {"title": "راجع التكلفة على الكتابة والحجم",
                 "md": "الفهرس الجديد بيكلف في كل INSERT/UPDATE وبيأكل مساحة. سجل القرار: المشكلة، الخطة قبل، الحل، الخطة بعد، الأرقام."},
            ]},
            {"type": "callout", "kind": "tip", "title": "خلّي الفهارس كود (Migrations) مش تعديلات يدوية",
             "md": """
أي فهرس تضيفه يدويًا على قاعدة الإنتاج = فرق بين البيئات وباج «بيشتغل عندي».
الحل: الفهرس يتكتب في **EF Core Migration** (أو ملف SQL مُدار)، ويُطبَّق عبر الـpipeline:
```csharp
migrationBuilder.CreateIndex(
    name: "ix_orders_status_created_id",
    table: "orders",
    columns: new[] { "status", "created_at", "id" },
    descending: new[] { false, true, true });
```
وللجداول الضخمة استخدم `CONCURRENTLY` عبر SQL خام في الـmigration مع `migrationBuilder.Sql(...)`
وتذكّر إن `CONCURRENTLY` **لا يعمل داخل transaction** → `migrationBuilder.Sql(..., suppressTransaction: true)`.
"""},
            {"type": "checkpoints", "items": [
                "أقرأ `EXPLAIN (ANALYZE, BUFFERS)` وأميّز التقدير من الواقع وأحدد العقدة الأبطأ.",
                "أختار نوع الفهرس وترتيب أعمدة مركّب صحيح (مساواة ← نطاق/ترتيب) وأعرف دور `INCLUDE`.",
                "أستخدم فهارس جزئية/فريدة/GIN للحالات المناسبة ولا أفهرس أعمدة منخفضة الانتقائية.",
                "أكتشف الفهارس غير المستخدمة والزائدة والناقصة وأضيف الفهارس عبر migrations لا يدويًا.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "`Rows Removed by Filter: 3912` في الخطة معناه إيه؟",
                 "options": [
                     "الاستعلام رجّع 3912 صف",
                     "الفهرس اختار صفوفًا كثيرة ثم طُبّق الشرط بعدها → فهرسك لا يغطي كل الشروط (مركّب أنسب)",
                     "فيه صفوف محذوفة",
                     "الإحصائيات قديمة",
                 ], "answer": 1,
                 "explain": "ده مؤشر مباشر إن الفهرس مش مثالي: غطّى `created_at` لكن `status` اتفحص بعد القراءة. الحل: فهرس `(status, created_at …)`."},
                {"q": "فهرس `(created_at, status)` لاستعلام `WHERE status='paid' AND created_at >= X ORDER BY created_at` — المشكلة؟",
                 "options": [
                     "لا مشكلة",
                     "عمود النطاق أولًا بيوقف استخدام العمود التاني بكفاءة؛ الترتيب الصحيح `(status, created_at)`",
                     "محتاج INCLUDE",
                     "محتاج فهرس جزئي",
                 ], "answer": 1,
                 "explain": "المساواة أولًا ثم النطاق. لو النطاق الأول، باقي الأعمدة ما بتتستخدمش لتضييق البحث (بتتفلتر بعد القراءة)."},
                {"q": "ليه `CREATE INDEX CONCURRENTLY` مهم على جدول كبير؟",
                 "options": [
                     "أسرع",
                     "لا يقفل الكتابة على الجدول — لكن لا يعمل داخل transaction ولو فشل يترك فهرسًا INVALID",
                     "يستهلك مساحة أقل",
                     "يعمل فهرس covering تلقائيًا",
                 ], "answer": 1,
                 "explain": "لصفر downtime. ثمنه: أبطأ، وممنوع داخل transaction، ولازم تتحقق من `pg_index.indisvalid` بعده."},
                {"q": "فهرس على عمود `is_active boolean` في جدول 10 ملايين صف — تقييمك؟",
                 "options": [
                     "ممتاز دائمًا",
                     "غالبًا بلا فائدة: انتقائية منخفضة (نتيجتين فقط) → الأفضل فهرس جزئي `WHERE is_active` أو مركّب مع أعمدة تانية",
                     "يحتاج INCLUDE",
                     "يحتاج GIN",
                 ], "answer": 1,
                 "explain": "لو 90% من الصفوف `true`، المخطط هيختار Seq Scan لأنه أرخص. الفهرس الجزئي على الجزء النادر هو الحل."},
                {"q": "أول خطوة قبل إضافة أي فهرس؟",
                 "options": [
                     "تحديث الإحصائيات",
                     "التقاط الاستعلام الحقيقي وقراءة خطة تنفيذه بالأرقام (وقد يكون الحل في الاستعلام نفسه)",
                     "إضافة فهرس مركّب",
                     "زيادة الذاكرة",
                 ], "answer": 1,
                 "explain": "كتير من «البطء» سببه جلب أعمدة/صفوف غير ضرورية، أو فرز بلا LIMIT، أو N+1 على مستوى الـORM — والفهرس ما يحلش ده."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "تشخيص وتحسين استعلام حقيقي",
                 "md": "اختار أبطأ استعلام في مشروعك (من `pg_stat_statements` أو لوجات EF). التقط خطته، حدّد المشكلة بدقة، أضف فهرسًا واحدًا عبر migration، وقِس قبل/بعد تحت حمل.",
                 "criteria": [
                     "الخطة قبل وبعد محفوظة في ملف (نص كامل مش لقطة شاشة)",
                     "تشخيص مكتوب: العقدة الأبطأ + سببها (Filter rows / Sort on disk / Seq scan / Key lookup)",
                     "الفهرس مُضاف في migration (لا تعديل يدوي) وله اسم يوضح غرضه",
                     "قياس: زمن الاستعلام وp95 للمسار قبل/بعد بأرقام",
                     "قرار موثق لو أضفت فهرسًا: أثره على الكتابة وحجمه",
                 ],
                 "hint": "لو التحسّن أقل من المتوقع: تأكد إن الاستعلام **مطابق** للـprefix بتاع الفهرس (نفس الأعمدة بنفس الترتيب ونفس اتجاه DESC)، وشغّل `ANALYZE orders;` بعد التغيير."},
                {"id": "t2", "title": "نظافة الفهارس",
                 "md": "شغّل استعلامات القسم 3 على قاعدة بياناتك: الفهارس غير المستخدمة، الزائدة، والـprefix-زائدة. احذف ما تثبت عدم حاجته (في migration) ووثّق قرارك.",
                 "criteria": [
                     "تقرير بالنتائج (جدول: الفهرس، الحجم، الاستخدام، القرار)",
                     "لا حذف لفهرس يدعم قيدًا فريدًا أو primary key",
                     "الحذف عبر migration + تحقق إن الاستعلامات الرئيسية ما تأثرتش (اختبارات)",
                     "ملاحظة بحجم المساحة المستردة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "PostgreSQL — Using EXPLAIN", "url": "https://www.postgresql.org/docs/current/using-explain.html"},
                {"label": "PostgreSQL — Indexes", "url": "https://www.postgresql.org/docs/current/indexes.html"},
                {"label": "pg_stat_statements", "url": "https://www.postgresql.org/docs/current/pgstatstatements.html"},
                {"label": "EF Core — Indexes and query performance", "url": "https://learn.microsoft.com/ef/core/performance/"},
                {"label": "SQL Server — Query Performance and Tuning", "url": "https://learn.microsoft.com/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store"},
                {"label": "Use The Index, Luke (مرجع بصري ممتاز)", "url": "https://use-the-index-luke.com/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l2
    {
        "id": "s3-m1-l2",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
لما اتنين من المستخدمين بيشتروا **آخر قطعة** من نفس المنتج في نفس اللحظة — مين يكسب؟
الإجابة بتحددها: مستوى العزل، ونوع القفل، وتصميم المعاملة. والغلط هنا بيبان كباجات «نادرة»:
رصيد سالب، طلب مدفوع مرتين، أو deadlock بيقفل الطلبات.

الدرس ده: مستويات العزل والأنومالي المرتبطة بيها، القفل المتشائم مقابل التفاؤلي (مع كود EF Core)،
تشخيص الـdeadlock من الـtrace، وتصميم معاملات قصيرة وقابلة لإعادة المحاولة.
"""},
            {"type": "terms", "items": [
                {"term": "ACID", "def": "Atomicity (كله أو ولا حاجة) · Consistency · Isolation (المعاملات لا تتداخل) · Durability (الالتزام دائم)."},
                {"term": "Dirty Read", "def": "قراءة بيانات معاملة لم تلتزم بعد (ممكن تتراجع). يحدث عند Read Uncommitted."},
                {"term": "Non-repeatable Read", "def": "قراءة نفس الصف مرتين في معاملة واحدة بقيمتين مختلفتين (حد تاني عدّل والتزم)."},
                {"term": "Phantom Read", "def": "صفوف **جديدة** تظهر في نفس النطاق داخل المعاملة (حد تاني أدرج)."},
                {"term": "Write Skew", "def": "أنومالي أخطر: معاملتان تقرآن نفس البيانات وتكتبان نتائج متعارضة — Snapshot Isolation لا يمنعها."},
                {"term": "Read Committed", "def": "الافتراضي في Postgres/SQL Server: لا dirty reads، لكن non-repeatable وphantom ممكنة."},
                {"term": "Repeatable Read / Snapshot", "def": "لقطة ثابتة للقراءات داخل المعاملة. في Postgres = snapshot isolation (يمنع phantom)."},
                {"term": "Serializable", "def": "أقوى مستوى: كأن المعاملات تعمل بالترتيب. في Postgres عبر SSI ويرمي `40001` يطلب إعادة محاولة."},
                {"term": "RCSI", "def": "(SQL Server) Read Committed Snapshot Isolation: القراءات من نسخة دون قفل — تقليل التعارض."},
                {"term": "Optimistic Concurrency", "def": "بلا قفل: تحقق عند الحفظ إن الصف ما اتغيرش (`xmin`/`RowVersion`) → `DbUpdateConcurrencyException`."},
                {"term": "Pessimistic Concurrency", "def": "قفل مسبق: `SELECT … FOR UPDATE` يمنع التعديل المتزامن حتى نهاية المعاملة."},
                {"term": "Deadlock", "def": "معاملة أ تستنى قفل بتمسكه ب، وب تستنى قفل بتمسكه أ. القاعدة بتكتشفه وتلغي واحدة."},
            ]},
            {"type": "table", "head": ["المستوى", "Dirty", "Non-repeatable", "Phantom", "Write Skew", "التكلفة"], "rows": [
                ["Read Uncommitted", "✗ ممكن", "✗ ممكن", "✗ ممكن", "✗ ممكن", "الأقل (لا تستخدمه عمليًا)"],
                ["Read Committed (الافتراضي)", "✓ ممنوع", "✗ ممكن", "✗ ممكن", "✗ ممكن", "منخفضة"],
                ["Repeatable Read", "✓", "✓", "PG: ✓ / SQL Server: ✗", "✗ ممكن", "متوسطة (أقفال/تراجع أكثر)"],
                ["Snapshot (RCSI)", "✓", "✓", "✓", "✗ ممكن", "متوسطة + tempdb/version store"],
                ["Serializable", "✓", "✓", "✓", "✓ ممنوع", "الأعلى + إعادة محاولات (40001)"],
            ]},
            {"type": "callout", "kind": "note", "title": "قاعدة عملية: المستوى الافتراضي + حماية صريحة للنقاط الحرجة",
             "md": """
لا ترفع مستوى العزل لكل المعاملات (تكلفة وتراجعات كتير). الصحيح:
**Read Committed افتراضيًا**، ومعاملات قصيرة، و**حماية صريحة** للنقاط الحساسة (مخزون، رصيد، كوبونات):
قفل متشائم `FOR UPDATE` **أو** تفاؤلي بـ`xmin`/`RowVersion` + إعادة محاولة — أو Serializable لمعاملات منطقية معقدة.
"""},
            {"type": "heading", "level": 2, "text": "1) المخزون: الحل الصحيح لحالة «آخر قطعة»"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/StockService.cs", "title": "قفل متشائم (pessimistic) — للعمليات القصيرة والحرجة", "code": r'''
public sealed class StockService(AppDbContext db, ILogger<StockService> log)
{
    /// <summary>
    /// SELECT … FOR UPDATE: يقفل صف المنتج حتى نهاية المعاملة.
    /// ★ المعاملة قصيرة ولا تحتوي أي I/O خارجي (لا HTTP ولا إرسال بريد).
    /// </summary>
    public async Task ReserveAsync(Guid productId, int quantity, CancellationToken ct)
    {
        await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);
        try
        {
            // EF Core لا يولّد FOR UPDATE → SQL خام مقصود ومعامل (parameterized)
            var row = await db.Database
                .SqlQueryRaw<StockRow>(
                    "SELECT id, stock, reserved FROM products WHERE id = {0} FOR UPDATE", productId)
                .SingleOrDefaultAsync(ct);

            if (row is null) throw new NotFoundException("Product", productId);

            var available = row.Stock - row.Reserved;
            if (available < quantity)
                throw new InsufficientStockException(productId, requested: quantity, available);

            await db.Products
                .Where(p => p.Id == productId)
                .ExecuteUpdateAsync(s => s.SetProperty(p => p.Reserved, p => p.Reserved + quantity), ct);

            await tx.CommitAsync(ct);
        }
        catch
        {
            await tx.RollbackAsync(CancellationToken.None);   // ✓ rollback بلا token ملغى
            throw;
        }
    }

    public sealed record StockRow(Guid Id, int Stock, int Reserved);
}
'''},
            {"type": "code", "lang": "csharp", "filename": "Shop.Api/Features/Orders/OptimisticStockService.cs", "title": "قفل تفاؤلي (optimistic) — الأفضل تحت تعارض منخفض", "code": r'''
public sealed class OptimisticStockService(AppDbContext db, ILogger<OptimisticStockService> log)
{
    /// <summary>
    /// بلا أقفال: نقرأ، نحسب، ونحفظ مع تحقق من الإصدار.
    /// Postgres: `xmin` يعمل كـconcurrency token تلقائي (في التكوين: UseXminAsConcurrencyToken).
    /// </summary>
    public async Task ReserveAsync(Guid productId, int quantity, CancellationToken ct)
    {
        const int maxAttempts = 4;

        for (var attempt = 1; ; attempt++)
        {
            var product = await db.Products.AsTracking().SingleOrDefaultAsync(p => p.Id == productId, ct)
                          ?? throw new NotFoundException("Product", productId);

            if (product.Stock - product.Reserved < quantity)
                throw new InsufficientStockException(productId, quantity, product.Stock - product.Reserved);

            product.Reserved += quantity;

            try
            {
                await db.SaveChangesAsync(ct);
                return;                                   // ✓ نجح: الإصدار ما اتغيرش
            }
            catch (DbUpdateConcurrencyException ex)
            {
                db.ChangeTracker.Clear();                 // ★ افصل الكيانات القديمة قبل إعادة المحاولة

                if (attempt == maxAttempts)
                {
                    log.LogWarning("optimistic concurrency exhausted product={ProductId} attempts={Attempts}",
                        productId, attempt);
                    throw new ConflictException("Product", productId, "تعارض متكرر؛ أعد المحاولة");
                }

                // backoff أسي + jitter عشان المحاولات ما تصطدمش في نفس اللحظة
                var delay = TimeSpan.FromMilliseconds(20 * Math.Pow(2, attempt))
                          + TimeSpan.FromMilliseconds(Random.Shared.Next(0, 30));
                await Task.Delay(delay, ct);
            }
        }
    }
}

// التكوين (Postgres): xmin كـconcurrency token
public sealed class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> b)
    {
        b.ToTable("products");
        b.UseXminAsConcurrencyToken();          // Npgsql: إصدار صف تلقائي بلا عمود إضافي
        b.Property(p => p.Stock).HasColumnName("stock");
    }
}

// SQL Server المقابل:
// b.Property(p => p.RowVersion).IsRowVersion();   // byte[] + [Timestamp]
'''},
            {"type": "table", "head": ["المعيار", "Pessimistic (`FOR UPDATE`)", "Optimistic (`xmin`/`RowVersion`)"], "rows": [
                ["التعارض المتوقع", "عالي (صف ساخن، منافسة شديدة)", "منخفض/متوسط"],
                ["السلوك عند التعارض", "انتظار (قد يصل لـdeadlock)", "فشل الحفظ + إعادة محاولة"],
                ["زمن استجابة متوقع", "متقلب (انتظار القفل)", "ثابت غالبًا، وذيل عند التعارض"],
                ["خطر", "قفل محتجز + اتصال مشغول + deadlock", "livelock لو التعارض عالي جدًا"],
                ["مناسب لـ", "حجز مخزون، تحويل رصيد، عدّادات", "تعديل كيانات (طلب، عميل، منتج)"],
                ["شرط", "معاملة قصيرة بلا I/O خارجي", "منطق إعادة محاولة + فصل ChangeTracker"],
            ]},
            {"type": "callout", "kind": "danger", "title": "3 أخطاء بتحوّل المعاملات لكوارث",
             "md": """
**① I/O خارجي داخل المعاملة** (HTTP لمزوّد دفع، إرسال بريد، نداء خدمة):
القفل محتجز طول زمن الشبكة → اتصالات القاعدة بتتنفذ → انهيار تحت الحمل.
الحل: **خارج** المعاملة، أو استخدم outbox (اكتب الرسالة في نفس الـtransaction وخلي worker يبعتها).

**② `EnableRetryOnFailure` مع معاملة يدوية**: EF بيرمي إن استراتيجية التنفيذ ما تدعمش معاملات يبدأها المستخدم.
الحل: لفّ المعاملة في استراتيجية التنفيذ:
```csharp
var strategy = db.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () =>
{
    await using var tx = await db.Database.BeginTransactionAsync(ct);
    /* ... */
    await tx.CommitAsync(ct);
});
```

**③ إعادة محاولة بلا فصل الكيانات**: بعد `DbUpdateConcurrencyException`، الكيانات في الـChangeTracker لسه قديمة؛
`SaveChanges` التالي يفشل تاني. `db.ChangeTracker.Clear()` (أو scope جديد) قبل إعادة القراءة.
"""},
            {"type": "heading", "level": 2, "text": "2) Deadlock: التشخيص من الـtrace"},
            {"type": "code", "lang": "sql", "filename": "diagnostics/deadlocks.sql", "title": "اللي بتدور عليه في اللوجات + الحالة الحالية", "code": r'''
-- ★ فعّل تسجيل الـdeadlocks (الافتراضي: مسجّل بالفعل عند حدوثه)
SHOW log_lock_waits;                 -- off افتراضيًا
ALTER SYSTEM SET log_lock_waits = on;         -- يسجّل الانتظارات > deadlock_timeout
ALTER SYSTEM SET deadlock_timeout = '1s';
SELECT pg_reload_conf();

-- شكل الرسالة في اللوج (Postgres):
--   ERROR:  deadlock detected
--   DETAIL: Process 1234 waits for ShareLock on transaction 567; blocked by process 890.
--           Process 890 waits for ShareLock on transaction 1234; blocked by process 1234.
--   HINT:   See server log for query details.
--   CONTEXT: while locking tuple (3,17) in relation "orders"
-- ★ الـCONTEXT بيقولك **الجدول والصف** — ده المفتاح للتشخيص

-- ماذا يُقفل الآن ومن ينتظر؟
SELECT blocked.pid       AS blocked_pid,
       blocked.usename   AS blocked_user,
       left(blocked.query, 80)  AS blocked_query,
       blocking.pid      AS blocking_pid,
       left(blocking.query, 80) AS blocking_query,
       now() - blocked.query_start AS waiting_for
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY (pg_blocking_pids(blocked.pid))
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0
ORDER BY waiting_for DESC;

-- معاملات مفتوحة من زمان (قاتل صامت: قفل محتجز من اتصال منسي)
SELECT pid, usename, state, xact_start, now() - xact_start AS tx_age, left(query, 90)
FROM pg_stat_activity
WHERE state <> 'idle' AND xact_start IS NOT NULL
ORDER BY tx_age DESC LIMIT 20;

-- حواجز الأمان: لا تترك معاملة مفتوحة للأبد
ALTER SYSTEM SET lock_timeout = '5s';
ALTER SYSTEM SET statement_timeout = '30s';
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';
SELECT pg_reload_conf();

-- SELECT … FOR UPDATE بطرق أنضف للطوابير
SELECT id FROM jobs WHERE status = 'pending'
ORDER BY scheduled_at
FOR UPDATE SKIP LOCKED          -- ✓ يتخطى الصفوف المقفولة: بلا انتظار وبلا deadlock
LIMIT 10;

SELECT id FROM orders WHERE id = '…' FOR UPDATE NOWAIT;   -- يفشل فورًا بدل الانتظار
'''},
            {"type": "steps", "title": "منهجية منع الـdeadlock (أرخص من تشخيصه)", "items": [
                {"title": "رتّب الوصول للموارد بترتيب ثابت",
                 "md": "لو معاملة بتعدّل الطلب ثم المنتج، خلي **كل** الكود يعمل نفس الترتيب. أغلب الـdeadlocks سببها ترتيب معكوس في مسارين."},
                {"title": "قلّل حجم ومدة المعاملة",
                 "md": "احسب خارج المعاملة، وافتحها قبل الكتابة مباشرة، والتزم فورًا. لا HTTP ولا بريد ولا حسابات طويلة جواها."},
                {"title": "استخدم `SKIP LOCKED`/`NOWAIT` للطوابير",
                 "md": "نمط الـqueue على جدول: `FOR UPDATE SKIP LOCKED` بيمنع الانتظار والتعارض خالص."},
                {"title": "اعمل batches صغيرة وبترتيب ثابت",
                 "md": "تحديث 10 آلاف صف في معاملة واحدة = قفلات كتير ومدة طويلة. دفعات بـ`ORDER BY id` تقلل التعارض."},
                {"title": "ضع حواجز زمنية وأعد المحاولة",
                 "md": "`lock_timeout` و`statement_timeout` و`idle_in_transaction_session_timeout` + إعادة محاولة على `40001`/`40P01` بـbackoff وjitter."},
                {"title": "سجّل واعرض القياسات",
                 "md": "عدّاد للـdeadlocks وإعادة المحاولات (بوسم العملية). ارتفاع الرقم = تصميم فيه صفوف ساخنة، مش «حظ وحش»."},
            ]},
            {"type": "code", "lang": "csharp", "title": "إعادة محاولة موحّدة على أخطاء التعارض", "code": r'''
/// <summary>
/// Postgres: 40001 serialization_failure و 40P01 deadlock_detected — الاثنان قابلان لإعادة المحاولة.
/// SQL Server: 1205 deadlock victim.
/// </summary>
public static class TransactionRetry
{
    private static readonly string[] RetryableSqlStates = ["40001", "40P01"];

    private static readonly System.Diagnostics.Metrics.Meter Meter = new("Shop.Api.db", "1.0.0");
    private static readonly Counter<long> ConflictRetries =
        Meter.CreateCounter<long>("db.conflict.retries", description: "إعادة محاولات بسبب تعارض");

    public static async Task<T> RunAsync<T>(
        Func<CancellationToken, Task<T>> action,
        ILogger log, string operation,
        int maxAttempts = 3, CancellationToken ct = default)
    {
        for (var attempt = 1; ; attempt++)
        {
            try { return await action(ct); }
            catch (Exception ex) when (attempt < maxAttempts && IsRetryable(ex))
            {
                var delay = TimeSpan.FromMilliseconds(30 * Math.Pow(2, attempt))
                          + TimeSpan.FromMilliseconds(Random.Shared.Next(0, 50));
                log.LogWarning("retryable conflict on {Operation} (attempt {Attempt}), retrying in {Delay}",
                    operation, attempt, delay);
                ConflictRetries.Add(1, new("operation", operation));
                await Task.Delay(delay, ct);
            }
        }
    }

    /// <summary>التعارض ممكن يظهر من SaveChanges (DbUpdateException) أو من SQL خام مباشرة.</summary>
    private static bool IsRetryable(Exception ex) =>
        FindPostgresError(ex) is { } pg && RetryableSqlStates.Contains(pg.SqlState);

    private static PostgresException? FindPostgresError(Exception? ex)
    {
        while (ex is not null)
        {
            if (ex is PostgresException pg) return pg;
            ex = ex.InnerException;
        }
        return null;
    }
}

// الاستخدام: العملية كلها (قراءة + كتابة) داخل إعادة المحاولة
await TransactionRetry.RunAsync(async ct =>
{
    await using var scope = scopeFactory.CreateAsyncScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await stock.ReserveAsync(productId, quantity, ct);
    return true;
}, log, "reserve-stock", ct: stoppingToken);
'''},
            {"type": "heading", "level": 2, "text": "3) Serializable وإمتى تستحقه"},
            {"type": "code", "lang": "csharp", "title": "مثال write skew: اللي Repeatable Read ما بيمنعوش", "code": r'''
// السيناريو: طبيبَان على استدعاء (on-call) — والقاعدة: واحد على الأقل لازم يفضل.
// معاملتان متزامنتان: كل واحدة تقرأ "فيه 2 على الاستدعاء" فتُلغي نفسها → النتيجة: صفر.
// Read Committed و Repeatable Read (snapshot) يسمحان بها. Serializable يمنعها.

await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.Serializable, ct);
try
{
    var onCall = await db.Doctors.CountAsync(d => d.IsOnCall, ct);
    if (onCall <= 1) throw new ConflictException("Schedule", shiftId, "لا يمكن إلغاء آخر طبيب على الاستدعاء");

    await db.Doctors.Where(d => d.Id == doctorId)
        .ExecuteUpdateAsync(s => s.SetProperty(d => d.IsOnCall, false), ct);

    await tx.CommitAsync(ct);
}
catch (DbUpdateException ex) when ((ex.InnerException as PostgresException)?.SqlState == "40001")
{
    await tx.RollbackAsync(CancellationToken.None);
    throw new ConflictException("Schedule", shiftId, "تعارض مع عملية أخرى؛ أعد المحاولة");
}
// ★ Serializable في Postgres = إعادة محاولات جزء من التصميم، مش خطأ. اجعل العملية idempotent وقابلة للإعادة.
'''},
            {"type": "callout", "kind": "warn", "title": "حدود ومستويات العزل في EF Core",
             "md": """
- **المستوى على المعاملة، مش على الاستعلام**: `BeginTransactionAsync(IsolationLevel.Serializable)` بيأثر على كل الاستعلامات جواها.
- **Postgres**: Repeatable Read = snapshot isolation → **write skew ممكن**؛ Serializable (SSI) هو اللي بيمنعه (ويرمي 40001).
- **SQL Server**: RCSI بيقلل التعارض (القراءات ما بتقفلش) لكنه snapshot isolation برضه → write skew ممكن.
- **MySQL/InnoDB**: الافتراضي Repeatable Read مع next-key locks (سلوك مختلف تمامًا — لا تفترض خبرتك مع Postgres).
- **لا تخلط مستويات مختلفة في مسار عمل واحد** بدون فهم: معاملة داخلية بمستوى مختلف بتتجاهل غالبًا (nested transactions).
- `SaveChangesAsync` لوحدها = معاملة ضمنية واحدة لكل التغييرات (atomic) — مش محتاج transaction يدوي إلا لو فيه أكثر من خطوة.
"""},
            {"type": "checkpoints", "items": [
                "أختار مستوى العزل بحسب الأنومالي المسموح بها والتكلفة، وأحمي النقاط الحرجة صراحة.",
                "أطبّق pessimistic (`FOR UPDATE`) أو optimistic (`xmin`/`RowVersion`) بحسب معدل التعارض.",
                "أشخّص deadlock من الـtrace (`CONTEXT` بالجدول والصف) وأمنعه بترتيب موارد ثابت ومعاملات قصيرة.",
                "أعيد المحاولة بأمان على 40001/40P01 مع backoff وjitter وفصل الـChangeTracker.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "ليه ممنوع نداء HTTP لمزوّد الدفع داخل معاملة القاعدة؟",
                 "options": [
                     "بطء الشبكة فقط",
                     "القفل يظل محتجزًا زمن الشبكة → استنزاف الاتصالات وانهيار تحت الحمل؛ الحل: خارج المعاملة أو outbox",
                     "يسبب deadlock دائمًا",
                     "EF Core يمنعه",
                 ], "answer": 1,
                 "explain": "قاعدة ذهبية: المعاملة تفتح قبل الكتابة مباشرة وتلتزم فورًا. أي I/O خارجي يبقى بره أو عبر outbox."},
                {"q": "`DbUpdateConcurrencyException` حصل — أول خطوة قبل إعادة المحاولة؟",
                 "options": [
                     "إعادة SaveChanges فورًا",
                     "`db.ChangeTracker.Clear()` (أو scope جديد) ثم إعادة القراءة والحساب",
                     "رفع مستوى العزل",
                     "إضافة فهرس",
                 ], "answer": 1,
                 "explain": "الكيانات المتتبَّعة لسه قديمة؛ إعادة المحاولة عليها تفشل تاني (livelock). افصل ثم اقرأ من جديد."},
                {"q": "منع write skew (آخر طبيب على الاستدعاء) يحتاج إيه؟",
                 "options": [
                     "Read Committed كافٍ",
                     "Serializable (أو قفل صريح على مجموعة الصفوف/الجدول)",
                     "Repeatable Read",
                     "فهرس مركّب",
                 ], "answer": 1,
                 "explain": "write skew بينجو في مستويات snapshot لأن كل معاملة تقرأ لقطة صالحة. Serializable في Postgres (SSI) بيكتشفه ويرمي 40001."},
                {"q": "`FOR UPDATE SKIP LOCKED` بيحل إيه؟",
                 "options": [
                     "يسرّع الفهرس",
                     "نمط الطابور على جدول: كل عامل ياخد صفوفًا غير مقفولة → بلا انتظار وبلا deadlock",
                     "يمنع القراءة",
                     "يرفع مستوى العزل",
                 ], "answer": 1,
                 "explain": "ده الأساس في job queues المبنية على قاعدة البيانات. `NOWAIT` بديل لو عايز تفشل فورًا بدل التخطي."},
                {"q": "إيه فايدة `idle_in_transaction_session_timeout`؟",
                 "options": [
                     "تسريع الاستعلامات",
                     "قتل الاتصالات اللي سايبه معاملة مفتوحة (قفل محتجز بلا سبب) — أشهر سبب لتوقف مفاجئ في النظام",
                     "منع deadlock",
                     "تقليل حجم اللوجات",
                 ], "answer": 1,
                 "explain": "معاملة مفتوحة منسية = أقفال متراكمة + منع VACUUM + تضخم الجداول. حد زمني واضح أفضل من تحقيق يدوي."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "احجز المخزون بشكل صحيح",
                 "md": "نفّذ حجز مخزون بطريقتين (pessimistic وoptimistic) واكتب اختبار تعارض حقيقي: 20 طلبًا متزامنًا على منتج بمخزون 5 → لازم ينجح 5 فقط والمخزون ما يصبحش سالبًا.",
                 "criteria": [
                     "اختبار التزامن ناجح: 5 نجاحات و15 رفضًا (لا رصيد سالب، لا تجاوز)",
                     "المعاملة لا تحتوي أي I/O خارجي (راجع الكود ووثّق)",
                     "إعادة المحاولة مع backoff وjitter و`ChangeTracker.Clear()`",
                     "قياس: عدد إعادة المحاولات/التعارضات metric منشور",
                     "قرار مكتوب: أنهي طريقة اخترت للإنتاج وليه",
                 ],
                 "hint": "لعمل تعارض حقيقي في اختبار: استخدم Testcontainers (Postgres فعلي) و`Task.WhenAll` على 20 مهمة، كل واحدة بـscope/DbContext خاص. على InMemory أو SQLite الاختبار مش هيكشف المشكلة."},
                {"id": "t2", "title": "تشخيص قفلات",
                 "md": "أضف حواجز زمنية (`lock_timeout`, `statement_timeout`, `idle_in_transaction_session_timeout`) واستعلامات مراقبة (من يقفل من؟ معاملات مفتوحة قديمة). نفّذ سيناريو deadlock متعمدًا في بيئة تطوير وسجّل الرسالة من اللوج مع تحليلها.",
                 "criteria": [
                     "الحواجز مطبقة عبر migration/إعداد موثق (مش تعديل يدوي)",
                     "سيناريو deadlock مُنتَج عمدًا + الرسالة الكاملة محفوظة + تفسير من السطر `CONTEXT`",
                     "استعلام مراقبة جاهز في `diagnostics/` يُظهر من يقفل من",
                     "خطة إصلاح مكتوبة: تغيير ترتيب الموارد أو تقصير المعاملة أو SKIP LOCKED",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "PostgreSQL — Transaction Isolation", "url": "https://www.postgresql.org/docs/current/transaction-iso.html"},
                {"label": "PostgreSQL — Explicit Locking", "url": "https://www.postgresql.org/docs/current/explicit-locking.html"},
                {"label": "EF Core — Transactions & concurrency", "url": "https://learn.microsoft.com/ef/core/saving/transactions"},
                {"label": "EF Core — Concurrency tokens", "url": "https://learn.microsoft.com/ef/core/saving/concurrency"},
                {"label": "SQL Server — Isolation levels & RCSI", "url": "https://learn.microsoft.com/sql/t-sql/statements/set-transaction-isolation-level-transact-sql"},
                {"label": "Designing Data-Intensive Applications (ch. 7-9)", "url": "https://dataintensive.net/"},
            ]},
        ],
    },
    # ------------------------------------------------------------------ l3
    {
        "id": "s3-m1-l3",
        "updatedAt": TODAY,
        "blocks": [
            {"type": "text", "md": """
EF Core كافي لـ95% من الشغل — لكن فيه 5% بيكون فيها SQL الخام أسرع أو أوضح أو الإمكانية الوحيدة:
تقارير بتجميعات معقدة، قراءات عالية الحجم بمسارات ساخنة، window functions وCTEs،
وقراءات ضخمة للتصدير. هنا **Dapper** بييجي: micro-ORM بيعمل mapping من صفوف لـobjects بأقل overhead.

الدرس ده: إمتى تستحق Dapper، كتابة استعلامات آمنة ضد SQL injection، الـmapping والأنواع المخصصة،
وأهم نقطة عملية: **مشاركة الاتصال والمعاملة** بين EF Core وDapper في نفس مسار العمل.
"""},
            {"type": "terms", "items": [
                {"term": "Micro-ORM", "def": "طبقة mapping رفيعة فوق ADO.NET: بلا change tracking ولا migrations ولا LINQ provider."},
                {"term": "`QueryAsync<T>`", "def": "استعلام يرجع مجموعة كائنات من النوع T."},
                {"term": "`ExecuteAsync`", "def": "تنفيذ INSERT/UPDATE/DELETE أو DDL؛ يرجع عدد الصفوف المتأثرة."},
                {"term": "`QueryMultipleAsync`", "def": "عدة نتائج من round-trip واحد (تقرير فيه أكثر من جدول) — توفير شبكة حقيقي."},
                {"term": "Multi-mapping", "def": "تقسيم صفوف JOIN إلى أكثر من كائن (`Query<Order, Customer, Order>(…, splitOn: \"customer_id\")`)."},
                {"term": "`CommandDefinition`", "def": "الطريقة الكاملة: sql + params + transaction + timeout + **CancellationToken**."},
                {"term": "`SqlMapper.AddTypeHandler`", "def": "تعليم Dapper أنواعك المخصصة (DateOnly, Money, JSON columns)."},
                {"term": "Parameters", "def": "قيم مُمرَّرة كـparameters (لا دمج نصوص) — الحماية الوحيدة الحقيقية من SQL injection."},
            ]},
            {"type": "table", "head": ["المعيار", "EF Core", "Dapper", "ADO.NET خام"], "rows": [
                ["سرعة القراءة (projections)", "جيدة", "أعلى (mapping أخف)", "الأعلى نظريًا (بلا mapping)"],
                ["كتابة/تحديث كيانات", "ممتاز (tracking + graph)", "يدوي (SQL صريح)", "يدوي"],
                ["SQL معقد (CTE/window)", "محدود (raw SQL متاح)", "طبيعي", "طبيعي"],
                ["مigrations وتطور النموذج", "مدمج", "✗ (عليك)", "✗"],
                ["حماية من injection", "مدمجة في LINQ", "بالـparameters", "بالـparameters"],
                ["منحنى التعلم/الإنتاجية", "أعلى إنتاجية", "متوسط", "أقل"],
                ["الأنسب", "الكتابة + منطق العمل + التطوير السريع", "مسارات قراءة ساخنة وتقارير", "حالات نادرة جدًا (bulk COPY)"],
            ]},
            {"type": "callout", "kind": "tip", "title": "قاعدة الاستخدام في مشروع حقيقي",
             "md": """
**EF Core للكتابة ونموذج البيانات. Dapper للقراءات الساخنة والتقارير.**
مش «نختار واحد» — الاتنين بيتشاركوا نفس الـconnection ونفس الـtransaction (القسم 3).
ولا تحط Dapper في الـDomain: عرّف واجهة قراءة (`IOrderReadModel`) ونفّذها بـDapper في Infrastructure.
"""},
            {"type": "code", "lang": "bash", "filename": "terminal", "title": "الحزم", "code": r'''
dotnet add Shop.Api package Dapper
# Npgsql / Microsoft.Data.SqlClient موجودين أصلًا مع EF Core
'''},
            {"type": "heading", "level": 2, "text": "1) الأساسيات بأمان"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/ReadModels/OrderReadModel.cs", "title": "قراءة ساخنة: projection دقيق + parameters + CancellationToken", "code": r'''
using Dapper;

public sealed class OrderReadModel(IDbConnectionFactory connections) : IOrderReadModel
{
    /// <summary>
    /// ★ SQL ثابت تمامًا؛ كل المدخلات parameters. لا string interpolation ولا concat أبدًا.
    /// </summary>
    public async Task<IReadOnlyList<OrderRow>> ListAsync(
        OrderListQuery q, CancellationToken ct)
    {
        const string sql = """
            SELECT o.id,
                   o.created_at,
                   o.status,
                   o.total,
                   o.currency,
                   c.id      AS customer_id,
                   c.email   AS customer_email,
                   c.country
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.deleted_at IS NULL
              AND (@status  IS NULL OR o.status      = @status)
              AND (@country IS NULL OR c.country     = @country)
              AND (@from    IS NULL OR o.created_at >= @from)
              AND (@to      IS NULL OR o.created_at <  @to)
            ORDER BY o.created_at DESC, o.id DESC
            LIMIT @size OFFSET @offset;
            """;

        await using var conn = await connections.OpenAsync(ct);

        var rows = await conn.QueryAsync<OrderRow>(new CommandDefinition(
            sql,
            new
            {
                status = q.Status?.ToString(),          // ✓ null = لا فلترة
                country = q.Country,
                from = q.From?.UtcDateTime,
                to = q.To?.UtcDateTime,
                size = Math.Clamp(q.Size, 1, 100),
                offset = q.Offset,
            },
            commandTimeout: 10,                          // ✓ سقف زمني صريح
            cancellationToken: ct));                     // ✓ إلغاء حقيقي

        return [.. rows];
    }

    /// <summary>تقرير بعدة نتائج في round-trip واحد — أوفر من 3 استعلامات.</summary>
    public async Task<SalesReport> GetSalesReportAsync(DateOnly day, CancellationToken ct)
    {
        const string sql = """
            SELECT date_trunc('hour', o.created_at) AS hour,
                   count(*)                         AS orders,
                   sum(o.total)                     AS revenue
            FROM orders o
            WHERE o.created_at >= @from AND o.created_at < @to AND o.status <> 'cancelled'
            GROUP BY 1 ORDER BY 1;

            SELECT c.country, count(*) AS orders, sum(o.total) AS revenue
            FROM orders o JOIN customers c ON c.id = o.customer_id
            WHERE o.created_at >= @from AND o.created_at < @to AND o.status <> 'cancelled'
            GROUP BY c.country ORDER BY revenue DESC LIMIT 20;

            SELECT count(*) AS total_orders, coalesce(sum(o.total), 0) AS total_revenue
            FROM orders o
            WHERE o.created_at >= @from AND o.created_at < @to AND o.status <> 'cancelled';
            """;

        var from = day.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var to = from.AddDays(1);

        await using var conn = await connections.OpenAsync(ct);
        using var multi = await conn.QueryMultipleAsync(new CommandDefinition(
            sql, new { from, to }, commandTimeout: 30, cancellationToken: ct));

        var hourly = (await multi.ReadAsync<HourlyBucket>()).ToList();
        var byCountry = (await multi.ReadAsync<CountryBucket>()).ToList();
        var totals = await multi.ReadFirstAsync<Totals>();

        return new SalesReport(day, hourly, byCountry, totals);
    }

    public sealed record OrderRow(Guid Id, DateTimeOffset CreatedAt, string Status,
                                  decimal Total, string Currency,
                                  Guid CustomerId, string CustomerEmail, string Country);
    public sealed record HourlyBucket(DateTime Hour, int Orders, decimal Revenue);
    public sealed record CountryBucket(string Country, int Orders, decimal Revenue);
    public sealed record Totals(int TotalOrders, decimal TotalRevenue);
    public sealed record SalesReport(DateOnly Day, List<HourlyBucket> Hourly,
                                     List<CountryBucket> ByCountry, Totals Totals);
}
'''},
            {"type": "callout", "kind": "danger", "title": "SQL injection في Dapper: الطرق الثلاث اللي بتوقع الناس",
             "md": """
**① دمج نص في SQL** — مهما كان المصدر «موثوقًا»:
```csharp
// ✗ كارثة: العميل بيتحكم في الـSQL
var sql = $"SELECT * FROM products WHERE name LIKE '%{name}%' ORDER BY {sort}";
```
```csharp
// ✓ القيمة parameter
const string sql = "SELECT * FROM products WHERE name LIKE @pattern";
var rows = await conn.QueryAsync<Product>(sql, new { pattern = $"%{EscapeLike(name)}%" });
```

**② `ORDER BY` ديناميكي** — الأعمدة **لا يمكن** تمريرها كـparameters → whitelist صريح:
```csharp
private static readonly Dictionary<string, string> Sorts = new(StringComparer.OrdinalIgnoreCase)
{
    ["created_desc"] = "o.created_at DESC, o.id DESC",
    ["total_desc"] = "o.total DESC, o.id DESC",
    ["country_asc"] = "c.country ASC, o.id DESC",
};
var orderBy = Sorts.GetValueOrDefault(sort ?? "", Sorts["created_desc"]);   // ✗ لا قيمة من العميل مباشرة
```

**③ أسماء جداول/أعمدة ديناميكية (multi-tenancy)** — استخدم خريطة معرّفات داخلية أو مخطط منفصل،
ولا تبني اسم جدول من مدخلات المستخدم. ولو اضطررت: تحقق بـregex صارم + قائمة مسموحات.

وكمان: `EscapeLike` بينظّف `%` و`_` و`\\` عشان المستخدم ما يقدرش يوسّع البحث أو يعمل ReDoS على الفهرس.
"""},
            {"type": "heading", "level": 2, "text": "2) الـmapping والأنواع المخصصة"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/DapperSetup.cs", "title": "تهيئة مرة واحدة: أسماء أعمدة، أنواع مخصصة، JSON", "code": r'''
using Dapper;
using System.Text.Json;

public static class DapperSetup
{
    public static void Configure()
    {
        // ① أعمدة snake_case ↔ خصائص PascalCase
        DefaultTypeMap.MatchNamesWithUnderscores = true;

        // ② أنواع .NET اللي Dapper ما يعرفهاش افتراضيًا
        SqlMapper.AddTypeHandler(new DateOnlyHandler());
        SqlMapper.AddTypeHandler(new TimeOnlyHandler());
        SqlMapper.AddTypeHandler(new DecimalHandler());

        // ③ أعمدة JSON/JSONB ↔ كائنات قوية النوع
        SqlMapper.AddTypeHandler(new JsonHandler<OrderMetadata>());

        // ④ أمان: لا توسّع حجم الاستعلام بلا حدود
        SqlMapper.Settings.CommandTimeout = 30;
        SqlMapper.Settings.ApplyNullValues = false;
    }

    private sealed class DateOnlyHandler : SqlMapper.TypeHandler<DateOnly>
    {
        public override void SetValue(IDbDataParameter parameter, DateOnly value) => parameter.Value = value;
        public override DateOnly Parse(object value) => value switch
        {
            DateOnly d => d,
            DateTime dt => DateOnly.FromDateTime(dt),
            string s => DateOnly.Parse(s),
            _ => throw new DataException($"Cannot convert {value.GetType()} to DateOnly"),
        };
    }

    private sealed class TimeOnlyHandler : SqlMapper.TypeHandler<TimeOnly>
    {
        public override void SetValue(IDbDataParameter parameter, TimeOnly value) => parameter.Value = value;
        public override TimeOnly Parse(object value) => value switch
        {
            TimeOnly t => t,
            TimeSpan ts => TimeOnly.FromTimeSpan(ts),
            DateTime dt => TimeOnly.FromDateTime(dt),
            _ => throw new DataException($"Cannot convert {value.GetType()} to TimeOnly"),
        };
    }

    /// <summary>أعمدة numeric من القاعدة قد تصل كـdouble/long — نحوّلها لـdecimal بأمان.
    /// (لو عندك بنية Money بقيمة+عملة: خزّنها عمودين أو JSON واستخدم JsonHandler أدناه.)</summary>
    private sealed class DecimalHandler : SqlMapper.TypeHandler<decimal>
    {
        public override void SetValue(IDbDataParameter parameter, decimal value) => parameter.Value = value;
        public override decimal Parse(object value) => value switch
        {
            decimal d => d,
            double dbl => (decimal)dbl,
            long l => l,
            int i => i,
            _ => Convert.ToDecimal(value),
        };
    }

    private sealed class JsonHandler<T> : SqlMapper.TypeHandler<T> where T : class
    {
        public override void SetValue(IDbDataParameter parameter, T? value)
        {
            parameter.Value = value is null ? DBNull.Value
                : new NpgsqlParameter { Value = JsonSerializer.Serialize(value), NpgsqlDbType = NpgsqlDbType.Jsonb };
        }

        public override T? Parse(object value) => value switch
        {
            null or DBNull => null,
            string json => JsonSerializer.Deserialize<T>(json, AppJson.Options),
            byte[] bytes => JsonSerializer.Deserialize<T>(bytes, AppJson.Options),
            _ => throw new DataException($"Cannot parse JSON column into {typeof(T).Name}"),
        };
    }
}

/// <summary>اتصالات مقروءة: قراءة من replica، كتابة على primary — قرار يُخفى خلف واجهة.</summary>
public interface IDbConnectionFactory
{
    Task<NpgsqlConnection> OpenAsync(CancellationToken ct);
    Task<NpgsqlConnection> OpenReadAsync(CancellationToken ct);      // replica لو متاح
}

public sealed class NpgsqlConnectionFactory(IConfiguration config) : IDbConnectionFactory
{
    public async Task<NpgsqlConnection> OpenAsync(CancellationToken ct) =>
        await Open(config.GetConnectionString("Default")!, ct);

    public async Task<NpgsqlConnection> OpenReadAsync(CancellationToken ct) =>
        await Open(config.GetConnectionString("ReadReplica") ?? config.GetConnectionString("Default")!, ct);

    private static async Task<NpgsqlConnection> Open(string cs, CancellationToken ct)
    {
        var conn = new NpgsqlConnection(cs);
        await conn.OpenAsync(ct);
        return conn;
    }
}
'''},
            {"type": "heading", "level": 2, "text": "3) مشاركة الاتصال والمعاملة مع EF Core (أهم قسم)"},
            {"type": "code", "lang": "csharp", "filename": "Shop.Infrastructure/EfDapperBridge.cs", "title": "نفس الـconnection ونفس الـtransaction — بلا اتصالين", "code": r'''
using Dapper;
using Microsoft.EntityFrameworkCore.Storage;

/// <summary>
/// قاعدة ذهبية: لو العملية فيها كتابة بـEF وقراءة بـDapper، لازم يشوفوا **نفس** المعاملة.
/// وإلا: الدقائق بتقرأ حالة غير ملتزمة/قديمة والسلوك يبقى غير متوقع.
/// </summary>
public sealed class OrderFulfillment(AppDbContext db, ILogger<OrderFulfillment> log)
{
    public async Task FulfillAsync(Guid orderId, CancellationToken ct)
    {
        // ✓ استخدم اتصال ومعاملة EF الحالية
        var connection = db.Database.GetDbConnection();
        if (connection.State != ConnectionState.Open) await connection.OpenAsync(ct);

        await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);
        var dbTx = tx.GetDbTransaction();

        try
        {
            // 1) كتابة عبر EF (نموذج البيانات + validation + events)
            var order = await db.Orders.SingleAsync(o => o.Id == orderId, ct);
            order.Status = OrderStatus.Processing;
            await db.SaveChangesAsync(ct);

            // 2) قراءة ثقيلة عبر Dapper — على نفس الاتصال والمعاملة
            const string sql = """
                SELECT p.id, p.name, p.sku, l.quantity, l.unit_price
                FROM order_lines l JOIN products p ON p.id = l.product_id
                WHERE l.order_id = @orderId
                ORDER BY l.position;
                """;

            var lines = await connection.QueryAsync<FulfillmentLine>(new CommandDefinition(
                sql, new { orderId }, transaction: dbTx, commandTimeout: 10, cancellationToken: ct));

            // 3) تحديث جماعي عبر Dapper (أسرع من تحميل الكيانات وتعديلها)
            const string decrement = """
                UPDATE products p
                SET stock = p.stock - l.quantity,
                    updated_at = now()
                FROM order_lines l
                WHERE l.product_id = p.id AND l.order_id = @orderId;
                """;

            var affected = await connection.ExecuteAsync(new CommandDefinition(
                decrement, new { orderId }, transaction: dbTx, commandTimeout: 10, cancellationToken: ct));

            log.LogInformation("fulfilled order {OrderId}: {Lines} lines, {Affected} products",
                orderId, lines.Count(), affected);

            await tx.CommitAsync(ct);                    // ✓ الالتزام مرة واحدة للجميع
        }
        catch
        {
            await tx.RollbackAsync(CancellationToken.None);
            throw;
        }
    }

    public sealed record FulfillmentLine(Guid Id, string Name, string Sku, int Quantity, decimal UnitPrice);
}
'''},
            {"type": "callout", "kind": "warn", "title": "فخاخ الجمع بين EF وDapper",
             "md": """
- **اتصالين مختلفين** → قراءات Dapper ما تشوفش تغييرات EF غير الملتزمة (أو تشوف حالة قديمة). استخدم `db.Database.GetDbConnection()`.
- **معاملة EF من غير تمريرها لـDapper** → `transaction: dbTx` في كل `CommandDefinition`. نسيانها = Dapper برا المعاملة.
- **`EnableRetryOnFailure` + معاملة يدوية** → استثناء (نفس فخ الدرس السابق). لفّ الكل في `CreateExecutionStrategy().ExecuteAsync(...)`.
- **Change Tracking متضارب**: لو Dapper عدّل صفوفًا يتتبعها EF، `SaveChanges` بعده قد يفشل بـconcurrency أو يتجاهل التغييرات. رتّب الخطوات: Dapper أولًا ثم اقرأ كيانات EF، أو افصل المسارات.
- **Migrations**: Dapper ما بيعرفش النموذج → أي عمود جديد تضيفه في migration لازم ينعكس في SQL المكتوب يدويًا (اختبار قراءة يحميك).
- **التسميات**: `MatchNamesWithUnderscores` عام. لو عندك أعمدة مش snake_case، استخدم aliases في SQL (`AS CustomerEmail`).
"""},
            {"type": "heading", "level": 2, "text": "4) Bulk: لما Dapper نفسه ما يكفيش"},
            {"type": "code", "lang": "csharp", "title": "إدراج 100k صف: 3 طرق بالترتيب الأسرع", "code": r'''
// ✗ بطيء: ExecuteAsync لكل صف (أو حتى multi-row INSERT بآلاف القيم)
foreach (var r in rows) await conn.ExecuteAsync("INSERT INTO events (...) VALUES (@a, @b)", r);

// ✓ جيد: دفعات (batch) من 500-1000 صف في عبارة واحدة
foreach (var batch in rows.Chunk(500))
{
    const string sql = """
        INSERT INTO events (id, type, payload, created_at)
        SELECT * FROM unnest(@ids::uuid[], @types::text[], @payloads::jsonb[], @times::timestamptz[]);
        """;
    await conn.ExecuteAsync(sql, new
    {
        ids = batch.Select(r => r.Id).ToArray(),
        types = batch.Select(r => r.Type).ToArray(),
        payloads = batch.Select(r => JsonSerializer.Serialize(r.Payload)).ToArray(),
        times = batch.Select(r => r.CreatedAt.UtcDateTime).ToArray(),
    });
}

// ✓✓ الأسرع (Npgsql): COPY binary — مخصص للإدراج الضخم
await using var conn = new NpgsqlConnection(connectionString);
await conn.OpenAsync(ct);
await using var writer = await conn.BeginBinaryImportAsync(
    "COPY events (id, type, payload, created_at) FROM STDIN (FORMAT BINARY)", ct);

foreach (var r in rows)
{
    await writer.StartRowAsync(ct);
    await writer.WriteAsync(r.Id, ct);
    await writer.WriteAsync(r.Type, ct);
    await writer.WriteAsync(JsonSerializer.Serialize(r.Payload), NpgsqlTypes.NpgsqlDbType.Jsonb, ct);
    await writer.WriteAsync(r.CreatedAt.UtcDateTime, ct);
}
await writer.CompleteAsync(ct);
// ملاحظة: COPY ما بيحدّثش التسلسلات (sequences) — اضبطها يدويًا لو العمود identity
'''},
            {"type": "code", "lang": "csharp", "title": "اختبار مسار القراءة: Dapper يحتاج قاعدة حقيقية", "code": r'''
[Collection("Postgres")]
public sealed class OrderReadModelTests(PostgresFixture db) : IAsyncLifetime
{
    public ValueTask InitializeAsync() => new(db.ResetAsync().AsTask());
    public ValueTask DisposeAsync() => ValueTask.CompletedTask;

    /// <summary>نفس مصانع الاتصال لكل الاختبارات —مؤشر إلى قاعدة الـTestcontainer.</summary>
    private OrderReadModel CreateReadModel() => new(new NpgsqlConnectionFactory(
        new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["ConnectionStrings:Default"] = db.ConnectionString,
        }).Build()));

    [Fact]
    public async Task List_filters_by_status_and_country()
    {
        // ✓ بذر عبر EF (نموذج صحيح) والقراءة عبر Dapper (SQL مكتوب يدويًا)
        await using (var ctx = db.CreateContext())
        {
            ctx.Orders.AddRange(
                AnOrder.WithStatus(OrderStatus.Paid).WithCountry("EG").Build(),
                AnOrder.WithStatus(OrderStatus.Paid).WithCountry("SA").Build(),
                AnOrder.WithStatus(OrderStatus.New).WithCountry("EG").Build());
            await ctx.SaveChangesAsync();
        }

        var readModel = CreateReadModel();

        var result = await readModel.ListAsync(
            new OrderListQuery { Status = OrderStatus.Paid, Country = "EG", Size = 20, Offset = 0 },
            CancellationToken.None);

        result.Should().HaveCount(1);
        result[0].Country.Should().Be("EG");
        result[0].Status.Should().Be("Paid");
    }

    [Fact]
    public async Task Sort_whitelist_ignores_unknown_values()
    {
        var readModel = CreateReadModel();

        // ✗ قيمة فرز من العميل ما تصلش للـSQL أبدًا
        var act = () => readModel.ListAsync(
            new OrderListQuery { Sort = "1; DROP TABLE orders--", Size = 20 }, CancellationToken.None);

        var rows = await act();
        rows.Should().NotBeNull();                       // يرجع ترتيباً افتراضياً آمناً
        // وأثبت إن الجدول لسه موجود:
        await using var ctx = db.CreateContext();
        (await ctx.Orders.CountAsync()).Should().BeGreaterThanOrEqualTo(0);
    }
}
'''},
            {"type": "checkpoints", "items": [
                "أقرر إمتى أستخدم Dapper (قراءات ساخنة/تقارير/SQL معقد) وإمتى ألتزم بـEF Core.",
                "أكتب SQL ثابتًا مع parameters لكل المدخلات وwhitelist للفرز والأعمدة الديناميكية.",
                "أضبط الـmapping (snake_case، DateOnly/TimeOnly، أعمدة JSON) مرة واحدة عند الإقلاع.",
                "أشارك الاتصال والمعاملة بين EF وDapper وألتزم مرة واحدة، وأختبر مسارات القراءة على قاعدة حقيقية.",
            ]},
            {"type": "quiz", "title": "اختبر نفسك", "questions": [
                {"q": "أنهي حالة تستحق Dapper فعلًا؟",
                 "options": [
                     "حفظ كيان مع علاقاته",
                     "قراءة تقرير بتجميعات وwindow functions على مسار ساخن يحتاج SQL صريحًا",
                     "إدارة الـmigrations",
                     "تتبع تغييرات الكيانات",
                 ], "answer": 1,
                 "explain": "Dapper بلا change tracking وبلا migrations. قوته في القراءة المباشرة والـSQL الصريح بأقل overhead."},
                {"q": "`ORDER BY` من مدخل العميل — الحل الصحيح؟",
                 "options": [
                     "تمريره كـparameter",
                     "whitelist يترجم القيمة لجملة فرز ثابتة من كودك",
                     "تنظيف الأحرف الخاصة",
                     "منع الفرز",
                 ], "answer": 1,
                 "explain": "الأعمدة/اتجاهات الفرز لا يمكن تمريرها كـparameters في SQL. الـwhitelist هو الحل الوحيد الآمن (والتنظيف وحده غير كافٍ)."},
                {"q": "كتابة بـEF وقراءة بـDapper في نفس العملية — إيه المطلوب؟",
                 "options": [
                     "اتصالان منفصلان",
                     "`db.Database.GetDbConnection()` + تمرير `tx.GetDbTransaction()` لكل أمر Dapper + commit واحد",
                     "تشغيل Dapper بعد الـcommit",
                     "لا يمكن الجمع",
                 ], "answer": 1,
                 "explain": "بدون مشاركة المعاملة: Dapper يشوف حالة مختلفة (قديمة/غير ملتزمة) والسلوك يبقى غير متوقع وصعب التشخيص."},
                {"q": "`QueryMultipleAsync` — فايدتها؟",
                 "options": [
                     "فرز النتائج",
                     "عدة مجموعات نتائج في round-trip واحد → توفير زمن شبكة لتقارير متعددة الأجزاء",
                     "دعم الـtransactions",
                     "تحسين الفهارس",
                 ], "answer": 1,
                 "explain": "للتقارير: 3 استعلامات = 3 round-trips. مع `QueryMultiple` = واحدة، والفرق واضح في latency العالية."},
                {"q": "إدراج 200 ألف صف — الأسرع والأصح على Postgres؟",
                 "options": [
                     "`ExecuteAsync` لكل صف",
                     "`COPY` binary عبر `BeginBinaryImportAsync` (أو دفعات كبيرة بـunnest)",
                     "EF `AddRange` + `SaveChanges`",
                     "Transaction لكل صف",
                 ], "answer": 1,
                 "explain": "`COPY` مصمم للإدراج الضخم. انتبه: لا يحدّث الـsequences تلقائيًا، ولا يطلق triggers بنفس سلوك INSERT العادي."},
            ]},
            {"type": "tasks", "title": "مهام الدرس", "items": [
                {"id": "t1", "title": "مسار قراءة بـDapper",
                 "md": "حوّل أبطأ قراءة في مشروعك (أو تقرير) إلى read model بـDapper: SQL ثابت، parameters لكل المدخلات، whitelist للفرز، `CommandDefinition` مع timeout وCancellationToken، واختبار على Postgres حقيقي (Testcontainers).",
                 "criteria": [
                     "لا string interpolation في أي SQL (راجع الكود سطرًا سطرًا)",
                     "whitelist للفرز مع اختبار يثبت تجاهل قيمة خبيثة",
                     "اختبار على قاعدة حقيقية (مش SQLite/InMemory) ناجح",
                     "قياس زمن القراءة قبل/بعد (EF مقابل Dapper) بنفس البيانات والحمل",
                     "واجهة `IOrderReadModel` في التطبيق والتنفيذ في Infrastructure (الـDomain ما يعرفش Dapper)",
                 ],
                 "hint": "لو الأعمدة ما بتتطابقش: فعّل `DefaultTypeMap.MatchNamesWithUnderscores = true` **قبل** أول استعلام (في الإقلاع)، أو استخدم `AS` aliases في SQL."},
                {"id": "t2", "title": "جسر EF + Dapper في معاملة واحدة",
                 "md": "ابنِ عملية واحدة فيها: كتابة عبر EF، قراءة عبر Dapper، وتحديث جماعي عبر Dapper — كلها داخل معاملة واحدة والتزام واحد. أثبت باختبار إن الفشل في الخطوة الثالثة بيرجع كل شيء (بلا تغييرات جزئية).",
                 "criteria": [
                     "اتصال واحد ومعاملة واحدة (ممرَّرة لـDapper)",
                     "اختبار: خطأ متعمد في الخطوة الأخيرة → الحالة ترجع كما كانت",
                     "لا I/O خارجي داخل المعاملة",
                     "سجل (log) يوضح عدد الصفوف المتأثرة والمدة",
                 ]},
            ]},
            {"type": "resources", "items": [
                {"label": "Dapper", "url": "https://github.com/DapperLib/Dapper"},
                {"label": "EF Core — Raw SQL queries", "url": "https://learn.microsoft.com/ef/core/querying/raw-sql"},
                {"label": "EF Core — Connection strings & transactions", "url": "https://learn.microsoft.com/ef/core/miscellaneous/connection-strings"},
                {"label": "Npgsql — Bulk copy (COPY)", "url": "https://www.npgsql.org/doc/copy.html"},
                {"label": "OWASP SQL Injection Prevention Cheat Sheet", "url": "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"},
            ]},
        ],
    },
]
