/* الوحدة 7 — الأمان: المصادقة والتفويض. */
Academy.addModule({
  id: "security",
  title: "الأمان",
  tagline: "المصادقة تجيب «من أنت؟»، والتفويض يجيب «ماذا يُسمح لك؟». الخلط بينهما يفتح ثغرات صامتة.",
  icon: "⛨",
  color: "#fb7185",
  lessons: [
    {
      id: "jwt-auth",
      title: "JWT Authentication: من التوقيع إلى التحقق",
      duration: 27,
      level: "متقدم",
      summary:
        "JWT ليس تشفيرًا؛ إنه توقيع. سنفهم بنيته، ونضبط JwtBearer بأمان، ونصمّم دورة حياة Access/Refresh تحمي المستخدم.",
      keywords: ["JWT", "JwtBearer", "claims", "refresh token", "HS256", "RS256", "PasswordHasher"],
      objectives: [
        "تشرح أجزاء JWT الثلاثة وما يضمنه التوقيع.",
        "تضبط AddJwtBearer بتحقق كامل من المُصدر والجمهور والعمر.",
        "تصمّم Access Token قصير العمر وRefresh Token قابلًا للتدوير.",
        "تخزّن كلمات المرور بتجزئة آمنة لا عكسية.",
      ],
      concept: `
        <p><strong>JWT</strong> (JSON Web Token) سلسلة من ثلاثة أجزاء: <code>header.payload.signature</code>. الترويسة تصف الخوارزمية، والحمولة تحمل <em>Claims</em> (مطالبات) مثل <code>sub</code> و<code>role</code> و<code>exp</code>، والتوقيع يثبت أن الخادم أصدره ولم يُعدَّل.</p>
        <p><strong>مهم جدًا:</strong> الحمولة <em>ليست مشفّرة</em>، بل Base64Url فقط. أي شخص يملك التوكن يستطيع قراءة محتواه. لذلك لا تضع فيها كلمة مرور أو رقم بطاقة أو سرًّا. التوقيع يضمن السلامة (لم تُعدَّل)، لا السرية.</p>
        <h3>Authentication أم Authorization؟</h3>
        <p><strong>Authentication</strong> تتحقق من الهوية: هل التوكن صالح؟ من المستخدم؟ <strong>Authorization</strong> تقرر الصلاحية: هل يستطيع حذف هذا المنتج؟ الأولى تُنشئ <code>ClaimsPrincipal</code>، والثانية تقرأه وتقرر. الخلط بينهما (مثل فحص الدور داخل كود المصادقة) يجعل السياسات مستحيلة الاختبار.</p>
        <h3>ما الذي يجب التحقق منه؟</h3>
        <ul>
          <li><strong>التوقيع</strong> بمفتاح صحيح (وليس <code>alg: none</code>).</li>
          <li><strong>Issuer</strong> المتوقع.</li>
          <li><strong>Audience</strong> (لمن صدر).</li>
          <li><strong>Lifetime</strong> (<code>exp</code> و<code>nbf</code>).</li>
          <li><strong>ClockSkew</strong> — افتراضي 5 دقائق، قلّله إلى دقيقة مثلًا.</li>
        </ul>
        <p>إهمال أي بند يعني قبول توكنات لا يجب قبولها. ولهذا لا تكتب التحقق يدويًا إن كان بإمكانك استخدام <code>JwtBearer</code> المُختبَر.</p>
        <h3>Access وRefresh</h3>
        <p>Access Token قصير العمر (5–15 دقيقة) لتقليل أثر السرقة. Refresh Token طويل العمر (أيام) يُخزَّن بأمان ويُستخدم لإصدار Access جديد. الأفضل أن يكون <strong>قابلًا للتدوير</strong>: كل استخدام يُبطل القديم ويصدر جديدًا، مع كشف إعادة الاستخدام (Reuse Detection) كإشارة اختراق.</p>
        <h3>كلمات المرور</h3>
        <p>لا تُخزَّن أبدًا كنص. استخدم <code>PasswordHasher&lt;T&gt;</code> من ASP.NET Core Identity (PBKDF2) أو Argon2. التجزئة يجب أن تكون بطيئة مقصودة ومملّحة. ولا تسجّل كلمة المرور أو التوكن في أي سجل.</p>
      `,
      compare: {
        intro: `<p>الطريقة القديمة تفحص هيدر Authorization بنفسها وتقارن نصًا ثابتًا. الطريقة الحديثة تسلّم الأمر لمصادقة قياسية قابلة للتكوين والاختبار.</p>`,
        before: {
          label: "فحص يدوي في Middleware",
          lang: "csharp",
          title: "Program.cs",
          code: `app.Use(async (context, next) =>
{
    if (context.Request.Path.StartsWithSegments("/api/private"))
    {
        var header = context.Request.Headers.Authorization.ToString();
        if (header != "Bearer super-secret-static-token")
        {
            context.Response.StatusCode = 401;
            return;
        }
    }

    await next(context);
});`,
          points: [
            "توكن ثابت لا ينتهي ولا يحمل هوية.",
            "لا تحقق من التوقيع أو الجمهور.",
            "لا يمكن تمييز المستخدمين أو أدوارهم.",
          ],
        },
        after: {
          label: "JwtBearer",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.MapInboundClaims = false;
        options.RequireHttpsMetadata = true;
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwt.Issuer,
            ValidateAudience = true,
            ValidAudience = jwt.Audience,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(jwt.Key)),
            NameClaimType = "sub",
            RoleClaimType = "role"
        };
    });

builder.Services.AddAuthorization();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/api/private", (ClaimsPrincipal user) =>
        Results.Ok(new { user = user.Identity!.Name }))
   .RequireAuthorization();`,
          points: [
            "تحقق كامل من كل الحقول الحساسة.",
            "هوية موحّدة تُستخدم في كل السياسات.",
            "قابل للاختبار والتبديل إلى RS256.",
          ],
        },
        verdict: `<p>الفرق الحقيقي ليس في السطور، بل في <strong>سطح الهجوم</strong>. الكتابة اليدوية تنسى دائمًا بندًا واحدًا: الجمهور، أو العمر، أو الخوارزمية. المكتبة تجمع هذه الفحوص في مكان واحد وتحدّثها مع الثغرات المكتشفة.</p>`,
      },
      walkthrough: [
        {
          title: "سجّل المصادقة",
          code: `builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)\n    .AddJwtBearer(options =>\n    {\n        options.TokenValidationParameters = new TokenValidationParameters\n        {\n            ValidateIssuer = true,\n            ValidIssuer = jwt.Issuer,\n            ValidateAudience = true,\n            ValidAudience = jwt.Audience,\n            ValidateIssuerSigningKey = true,\n            IssuerSigningKey = new SymmetricSecurityKey(key),\n            ValidateLifetime = true,\n            ClockSkew = TimeSpan.FromSeconds(30)\n        };\n    });`,
          lang: "csharp",
          body: `<p>كل <code>Validate*</code> مهم. تعطيل التحقق من الإصدار/الجمهور يفتح بابًا لاستخدام توكن من نظام آخر. <code>ClockSkew</code> يسمح بفارق ساعة بسيط. المفتاح من خزنة/إعداد، لا من الكود. لا تسجّل التوكن.</p>`
        },
        {
          title: "أنشئ الـClaims",
          code: `var claims = new[]\n{\n    new Claim(JwtRegisteredClaimNames.Sub, user.Id.ToString()),\n    new Claim(JwtRegisteredClaimNames.Email, user.Email),\n    new Claim(ClaimTypes.Role, "Customer"),\n    new Claim("permission", "orders.read")\n};`,
          lang: "csharp",
          body: `<p><code>sub</code> معرف المستخدم. لا تضع بيانات حساسة/كبيرة في التوكن؛ التوكن مقروء. الأدوار/الصلاحيات يمكن أن تتقادم؛ استخدم عمرًا قصيرًا/تحققًا عند الحاجة. لا تضع كلمة المرور. حافظ على أسماء claims ثابتة.</p>`
        },
        {
          title: "وقّع التوكن",
          code: `var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.SigningKey));\nvar credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);\n\nvar token = new JwtSecurityToken(\n    issuer: jwt.Issuer,\n    audience: jwt.Audience,\n    claims: claims,\n    expires: DateTime.UtcNow.AddMinutes(15),\n    signingCredentials: credentials);\n\nreturn new JwtSecurityTokenHandler().WriteToken(token);`,
          lang: "csharp",
          body: `<p>التوقيع يمنع التعديل. استخدم مفتاحًا قويًا (32+ بايت) وخزنة. عمر قصير (15 دقيقة). لا تضع <code>expires</code> في الماضي. الخوارزمية يجب أن تطابق التحقق. لا تقبل <code>none</code>. احفظ مفتاح التدوير.</p>`
        },
        {
          title: "نقطة تسجيل الدخول",
          code: `var user = await users.FindByEmailAsync(request.Email);\nif (user is null || !hasher.Verify(user, request.Password))\n    return Results.Unauthorized();\n\nvar access = tokenService.Create(user);\nvar refresh = await refreshStore.CreateAsync(user.Id);\nreturn Results.Ok(new { access, refresh });`,
          lang: "csharp",
          body: `<p>لا تكشف إن كان البريد موجودًا. استخدم رسالة عامة. تحقق من كلمة المرور بـhash. أنشئ access قصير وrefresh طويل. خزّن refresh كhash/معرف. أضف rate limiting. لا تسجّل كلمة المرور/التوكن.</p>`
        },
        {
          title: "اطلب المصادقة",
          code: `app.UseAuthentication();\napp.UseAuthorization();\n\ngroup.MapGet("/orders", (ClaimsPrincipal user) =>\n    GetOrders(user.GetUserId()))\n    .RequireAuthorization();`,
          lang: "csharp",
          body: `<p>الترتيب مهم: authentication ثم authorization. <code>RequireAuthorization</code> يمنع المجهول. لا تعتمد على وجود claim فقط؛ تحقق من الصلاحية/الملكية. أعد 401 للمجهول و403 للممنوع. اختبر كليهما.</p>`
        },
        {
          title: "Refresh Token",
          code: `var stored = await refreshStore.GetAsync(request.RefreshToken);\nif (stored is null || stored.ExpiresAt < DateTime.UtcNow || stored.Revoked)\n    return Results.Unauthorized();\n\nawait refreshStore.RevokeAsync(stored.Id);\nvar newAccess = tokenService.Create(stored.UserId);\nvar newRefresh = await refreshStore.CreateAsync(stored.UserId);`,
          lang: "csharp",
          body: `<p>دوران refresh يقلل إعادة الاستخدام. خزّن hash، لا القيمة. ألغِ القديم عند الاستخدام. اربطه بالجهاز/الجلسة إن أمكن. إذا سُرّب، ألغِ العائلة. لا تجعل refresh صالحًا للأبد. سجّل الأحداث الأمنية دون التوكن.</p>`
        },
        {
          title: "إدارة المفاتيح",
          code: `Jwt__SigningKey_FILE=/run/secrets/jwt_key\nJwt__Issuer=https://souq.example\nJwt__Audience=souq-api`,
          lang: "text",
          body: `<p>المفتاح من secret store. لا في Git/appsettings. افصل بيئات. دوّر المفاتيح مع دعم مفتاحين أثناء الانتقال. إذا تسرّب، دوّر فورًا وألغِ الجلسات. راقب فشل التحقق. لا تضع المفتاح في logs.</p>`
        },
        {
          title: "مصائد شائعة",
          code: `❌ ValidateIssuer = false\n❌ مفتاح ضعيف/مخزّن في الكود\n❌ عمر طويل بلا revoke\n❌ بيانات حساسة في claims\n❌ قبول alg=none\n✅ تحقق كامل + عمر قصير + refresh مُدار`,
          lang: "text",
          body: `<p>التوكن ليس جلسة سحرية. إذا سُرّب، يصل حتى انتهاء صلاحيته. لذلك عمر قصير وrevoke. لا تعتمد على إخفاء claims. اختبر توكن منتهي/موقّع بمفتاح آخر/جمهور مختلف. الأمان تفاصيل.</p>`
        }
      ],
      internals: `
        <p>عند وصول التوكن، يفكّ <code>JwtBearerHandler</code> الأجزاء الثلاثة، يقرأ الترويسة ليعرف الخوارزمية، ثم يتحقق من التوقيع بالمفتاح. بعدها يتحقق من <code>iss</code> و<code>aud</code> و<code>exp</code> و<code>nbf</code> مع هامش الساعة. إن نجح، يبني <code>ClaimsIdentity</code> ويعيّن <code>HttpContext.User</code>.</p>
        <p>الخوارزميات: <strong>HS256</strong> تستخدم سرًّا مشتركًا؛ بسيطة لكن كل خدمة تتحقق تحتاج السر نفسه، وأي تسريب يعني انتحالًا كاملًا. <strong>RS256/ES256</strong> تستخدم مفتاحًا خاصًا للتوقيع وعامًا للتحقق، فتستطيع الخدمات التحقق دون معرفة سر التوقيع. في الأنظمة الموزعة، asymmetric هو الخيار الافتراضي.</p>
        <p>التوكن عديم الحالة: لا تحتاج قاعدة بيانات للتحقق، ولهذا يسهل التوسع. الثمن: لا يمكن إبطاله قبل انتهاء صلاحيته إلا بقائمة إلغاء (Denylist) أو تغيير المفتاح. لهذا Access قصير العمر ضروري: يقلل نافذة سوء الاستخدام.</p>
        <p>Refresh Token يجب أن يُخزَّن كـ <strong>hash</strong> لا كنص، مع: المستخدم، تاريخ الانتهاء، حالة الإبطال، ومعرّف الجهاز إن أردت. عند التدوير، اربط التوكن الجديد بالقديم؛ إعادة استخدام توكن مُبطَل تعني أن نسخة مسروقة، فأبطل السلسلة كلها.</p>
      `,
      internalsTable: {
        head: ["Claim", "المعنى", "ملاحظة أمنية"],
        rows: [
          ["sub", "معرّف المستخدم", "ثابت ولا يتغيّر"],
          ["iss / aud", "المُصدر والجمهور", "تحقق منهما دائمًا"],
          ["exp / nbf", "الصلاحية", "Access قصير"],
          ["role / permission", "الصلاحيات", "لا تُشتق من مدخلات العميل"],
          ["jti", "معرّف التوكن", "مفيد لقوائم الإلغاء"],
        ],
      },
      tips: [
        {
          title: "HTTPS ليس اختياريًا",
          body: "أي توكن يُرسل عبر HTTP مكشوف يمكن سرقته. فعّل HSTS ووجّه كل HTTP إلى HTTPS. لا تُصدر توكنات في بيئة غير مشفرة.",
        },
        {
          title: "لا تضع أسرارًا في الحمولة",
          body: "الحمولة مقروءة. ضع فيها معرّفات وأدوارًا، لا كلمات مرور أو مفاتيح. أي شيء حساس يبقى في الخادم.",
        },
        {
          title: "قلّل ClockSkew",
          body: "الافتراضي 5 دقائق يوسّع نافذة التوكن المنتهي. اضبطه بحسب دقة ساعات خوادمك، غالبًا 30-60 ثانية.",
        },
        {
          title: "خطّط لإبطال التوكن",
          body: "عند تسجيل الخروج أو تغيير كلمة المرور، أضف <code>jti</code> إلى denylist قصيرة العمر، أو غيّر <code>SecurityStamp</code> وأعد إصدار التوكنات.",
        },
      ],
      quiz: [
        {
          q: "هل حمولة JWT مشفّرة؟",
          options: [
            "نعم، لا يمكن قراءتها إلا بالخادم.",
            "لا، هي Base64Url قابلة للقراءة، والتوقيع يضمن عدم التعديل فقط.",
            "نعم إذا استخدمت HS256.",
            "فقط عند استخدام HTTPS.",
          ],
          answer: 1,
          explain:
            "JWT موقّع وليس مشفّرًا. أي طرف يملك التوكن يستطيع قراءة الـ claims.",
        },
        {
          q: "أي خيار يجب تفعيله لمنع قبول توكن منتهي؟",
          options: ["ValidateIssuer", "ValidateLifetime", "SaveToken", "RequireHttpsMetadata"],
          answer: 1,
          explain:
            "ValidateLifetime يتحقق من exp وnbf مع ClockSkew. إهماله يجعل التوكنات المنتهية صالحة.",
        },
        {
          q: "لماذا نستخدم Refresh Token؟",
          options: [
            "لأن Access لا ينتهي.",
            "لتقليل عمر Access مع إمكانية إصدار توكن جديد دون إعادة إدخال كلمة المرور.",
            "لتشفير الحمولة.",
            "لتخزين كلمة المرور.",
          ],
          answer: 1,
          explain:
            "Access قصير يقلل الضرر عند السرقة، وRefresh طويل مُدار يسمح بتجربة استخدام سلسة.",
        },
      ],
      capstone: {
        title: "تسجيل ودخول وتوكنات Souq.NET",
        goal: "نبني دورة مصادقة كاملة: تسجيل مستخدم بتجزئة آمنة، تسجيل دخول، إصدار Access/Refresh، وحماية مسار إنشاء منتج.",
        tasks: [
          "أنشئ كيان <code>AppUser</code> مع <code>PasswordHash</code> (وليس كلمة مرور).",
          "استخدم <code>PasswordHasher&lt;AppUser&gt;</code> عند التسجيل والتحقق عند الدخول.",
          "أصدر Access Token بـ <code>sub</code> و<code>role</code> و<code>jti</code> لمدة 10 دقائق.",
          "أصدر Refresh Token عشوائيًا وخزّن hash له مع تاريخ الانتهاء.",
          "أضف <code>POST /api/auth/refresh</code> يتحقق من التوكن ويدوّره.",
          "احمِ <code>POST /api/v1/products</code> بـ <code>RequireAuthorization</code>.",
        ],
        code: {
          lang: "csharp",
          title: "إصدار التوكن",
          code: `var claims = new List<Claim>
{
    new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
    new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString("N")),
    new("role", user.Role)
};

var credentials = new SigningCredentials(
    new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.Key)),
    SecurityAlgorithms.HmacSha256);

var token = new JwtSecurityToken(
    issuer: jwt.Issuer,
    audience: jwt.Audience,
    claims: claims,
    expires: DateTime.UtcNow.AddMinutes(10),
    signingCredentials: credentials);

return new JwtSecurityTokenHandler().WriteToken(token);`,
        },
      },
    },
    {
      id: "authorization",
      title: "Authorization: Policies + Resource-Based Access",
      duration: 24,
      level: "متقدم",
      summary:
        "وجود توكن لا يعني صلاحية. سنبني سياسات واضحة، ونفرّق بين 401 و403، ونمنع IDOR بفحص الملكية عند الاستعلام نفسه.",
      keywords: ["Authorization", "policies", "claims", "requirements", "IDOR", "resource-based", "401", "403"],
      objectives: [
        "تفرّق بين دور المستخدم وصلاحيته الدقيقة.",
        "تبني Policy مع Requirement وHandler مخصص.",
        "تستخدم Resource-Based Authorization للملكية.",
        "تمنع IDOR عبر الفلترة في الاستعلام لا بعده.",
      ],
      concept: `
        <p>بعد المصادقة، لديك <code>ClaimsPrincipal</code>. التفويض يجيب: هل هذا الفاعل مسموح له بهذا الفعل على هذا المورد؟ هناك ثلاثة مستويات:</p>
        <ul>
          <li><strong>Role</strong>: Admin / Customer. بسيط لكنه خشن؛ لا يميز «مشرف مبيعات» من «مشرف دعم».</li>
          <li><strong>Permission/Claim</strong>: <code>catalog:write</code>، <code>orders:refund</code>. أدق وقابل للتوسع.</li>
          <li><strong>Resource</strong>: هل هذا الطلب يخص هذا المستخدم؟ لا يمكن تقريره من التوكن وحده.</li>
        </ul>
        <h3>Policies</h3>
        <p>السياسة تجمع شروطًا في مكان واحد وتُطبَّق بالاسم:</p>
        <pre dir="ltr" style="background:var(--panel-2);padding:10px;border-radius:8px;overflow:auto"><code>builder.Services.AddAuthorization(options =&gt;
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser().Build();

    options.AddPolicy("CanManageCatalog", policy =&gt;
        policy.RequireClaim("permission", "catalog:write"));
});</code></pre>
        <p><strong>FallbackPolicy</strong> يجعل كل شيء محميًا افتراضيًا. هذا أفضل من نسيان <code>[Authorize]</code> على endpoint حساس. اجعل الاستثناءات صريحة عبر <code>AllowAnonymous</code>.</p>
        <h3>Requirement مخصص</h3>
        <p>عندما لا تكفي Claims بسيطة (مثل «عمر 18+» أو «بريد موثّق»)، أنشئ <code>IAuthorizationRequirement</code> و<code>AuthorizationHandler</code>. الإطار يقيّم كل الـ handlers؛ إن نجح أحدها، تحقّق الشرط (ما لم تستخدم <code>RequireAssertion</code>).</p>
        <h3>Resource-Based</h3>
        <p>«هل يملك هذا المستخدم الطلب رقم 42؟» لا يُحلّ في Middleware لأن المورد يُحمَّل داخل الـ endpoint. استخدم <code>IAuthorizationService.AuthorizeAsync(User, resource, policy)</code> بعد تحميل المورد. وإن فشل، أعد <strong>404</strong> بدل 403 إذا أردت إخفاء وجود المورد — قرار أمني شائع.</p>
        <h3>IDOR</h3>
        <p><em>Insecure Direct Object Reference</em>: تغيير <code>/orders/42</code> إلى <code>/orders/43</code> لقراءة طلب غيرك. الفحص بعد الجلب (<code>if (order.UserId != me) return Forbid()</code>) صحيح لكنه يترك المورد محمّلًا وقد يُنسى في مسار آخر. الأفضل: <strong>فلترة الاستعلام نفسه</strong> بـ <code>Where(o =&gt; o.UserId == me)</code>، فتصبح 404 طبيعية.</p>
      `,
      compare: {
        intro: `<p>الفحص المباشر للأدوار يبدو بسيطًا حتى تتغير القواعد. السياسة تفصل «القاعدة» عن «مكان التطبيق».</p>`,
        before: {
          label: "فحص دور داخل endpoint",
          lang: "csharp",
          title: "Program.cs",
          code: `app.MapDelete("/api/products/{id:int}", async (
    int id, ClaimsPrincipal user, IProductService service) =>
{
    if (!user.IsInRole("Admin") && !user.IsInRole("Manager"))
        return Results.Forbid();

    if (user.HasClaim("department", "Support"))
        return Results.Forbid();

    await service.DeleteAsync(id);
    return Results.NoContent();
});

app.MapPost("/api/products", async (ProductDto dto, ClaimsPrincipal user) =>
{
    if (!user.HasClaim("permission", "catalog:write"))
        return Results.Forbid();

    // ...
});`,
          points: [
            "القواعد مكررة ومبعثرة.",
            "نسيان فحص في مسار جديد وارد.",
            "لا يمكن اختبار السياسة بمعزل.",
          ],
        },
        after: {
          label: "Policies",
          lang: "csharp",
          title: "Program.cs",
          code: `builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser().Build();

    options.AddPolicy("CanManageCatalog", policy =>
        policy.RequireClaim("permission", "catalog:write"));
});

var products = app.MapGroup("/api/v1/products")
    .RequireAuthorization("CanManageCatalog");

products.MapDelete("/{id:int}", async (
    int id, IProductService service, CancellationToken ct) =>
{
    await service.DeleteAsync(id, ct);
    return Results.NoContent();
});`,
          points: [
            "قاعدة واحدة قابلة للاختبار.",
            "تطبيق على مجموعة كاملة.",
            "افتراضي آمن عبر FallbackPolicy.",
          ],
        },
        verdict: `<p>السياسة ليست تجميلًا: هي <strong>عقد قابل للاختبار</strong>. يمكنك كتابة اختبار يثبت أن مستخدمًا بلا <code>catalog:write</code> يحصل على 403، وأن حامل الصلاحية يحصل على 204. هذا أرخص بكثير من مراجعة كل endpoint يدويًا كل مرة.</p>`,
      },
      walkthrough: [
        {
          title: "سجّل سياسة",
          code: `builder.Services.AddAuthorization(options =>\n{\n    options.AddPolicy("CanManageCatalog", policy =>\n        policy.RequireClaim("permission", "catalog.write"));\n\n    options.AddPolicy("CanReadOrders", policy =>\n        policy.RequireAuthenticatedUser()\n              .RequireClaim("permission", "orders.read"));\n});`,
          lang: "csharp",
          body: `<p>السياسة تعبّر عن قدرة، لا عن دور. <code>RequireClaim</code> يتحقق من الصلاحية. يمكن دمج شروط. لا تكرر الشروط في كل endpoint. أسماء السياسات ثابتة. وثّق من يملك ماذا.</p>`
        },
        {
          title: "طبّق السياسة",
          code: `group.MapPost("/products", CreateProduct)\n    .RequireAuthorization("CanManageCatalog");`,
          lang: "csharp",
          body: `<p>الـendpoint يطلب السياسة. لا تفحص الدور يدويًا. إذا لم تتحقق، 403. المجهول 401. اختبر المستخدم العادي/الإداري. لا تضع السياسة بعد تنفيذ المنطق. الرفض يجب أن يحدث قبل العمل.</p>`
        },
        {
          title: "ملكية المورد",
          code: `var order = await db.Orders\n    .AsNoTracking()\n    .SingleOrDefaultAsync(o => o.Id == id, ct);\n\nif (order is null) return Results.NotFound();\nif (order.UserId != user.GetUserId() && !user.HasClaim("permission", "orders.manage"))\n    return Results.Forbid();\n\nreturn Results.Ok(order);`,
          lang: "csharp",
          body: `<p>BOLA: لا تكفي المصادقة. افحص الملكية. 404 يمنع كشف الوجود. المدير قد يملك صلاحية إدارة. لا تعتمد على معرف غير قابل للتخمين. اختبر مستخدم A مع مورد B. هذا أهم اختبار أمني.</p>`
        },
        {
          title: "Resource-based Authorization",
          code: `public sealed class OrderOwnerHandler\n    : AuthorizationHandler<OrderOwnerRequirement, Order>\n{\n    protected override Task HandleRequirementAsync(\n        AuthorizationHandlerContext context,\n        OrderOwnerRequirement requirement,\n        Order order)\n    {\n        if (order.UserId.ToString() == context.User.FindFirstValue(ClaimTypes.NameIdentifier))\n            context.Succeed(requirement);\n        return Task.CompletedTask;\n    }\n}`,
          lang: "csharp",
          body: `<p>عندما تعتمد الصلاحية على المورد نفسه. سجّل handler/requirement. استخدم <code>IAuthorizationService.AuthorizeAsync</code>. لا تضع منطق الملكية في controller ضخم. اختبر النجاح والفشل. لا تنسَ المدير.</p>`
        },
        {
          title: "الأدوار أم الصلاحيات؟",
          code: `// هش\n[Authorize(Roles = "Admin")]\n\n// أفضل للتوسع\n[Authorize(Policy = "CanManageCatalog")]`,
          lang: "csharp",
          body: `<p>الأدوار بسيطة لكنها تخلط الهوية بالقدرة. السياسات تسمح بتغيير من يملك القدرة دون تعديل الكود. لا تجعل Admin يمر من كل شيء تلقائيًا. افصل الصلاحيات الحساسة. راجعها دوريًا.</p>`
        },
        {
          title: "مجموعة endpoints",
          code: `var admin = app.MapGroup("/api/v1/admin")\n    .RequireAuthorization("CanManageCatalog");\n\nadmin.MapGet("/products", ListAll);\nadmin.MapDelete("/products/{id}", Delete);`,
          lang: "csharp",
          body: `<p>طبّق السياسة على المجموعة لتقليل النسيان. لا تخلط مسارات عامة وإدارية. تأكد أن كل endpoint داخل المجموعة يحتاج السياسة. اختبر مسارًا جديدًا. لا تعتمد على اسم المسار.</p>`
        },
        {
          title: "اختبر 401/403/BOLA",
          code: `401: بلا توكن\n403: توكن بلا صلاحية\n404: مورد غير موجود/غير مملوك\n200: المالك أو المدير`,
          lang: "text",
          body: `<p>اكتب اختبارات تكامل لهذه الحالات. لا تختبر happy path فقط. تحقق من عدم تسريب بيانات في 403/404. استخدم مستخدمين مختلفين. هذه الاختبارات تمنع أخطر ثغرات API.</p>`
        },
        {
          title: "مبدأ أقل صلاحية",
          code: `- امنح أقل claim لازم\n- افصل صلاحيات القراءة/الكتابة\n- راجع الوصول دوريًا\n- سجّل العمليات الحساسة\n- لا تثق بالعميل`,
          lang: "text",
          body: `<p>الصلاحية ليست شعارًا. كل claim يزيد سطح الهجوم. راجع من يحتاج ماذا. سجّل من فعل ماذا دون PII. ألغِ الوصول عند تغير الدور. اختبر بعد كل تغيير. الأمان صيانة مستمرة.</p>`
        }
      ],
      internals: `
        <p><code>AuthorizationMiddleware</code> يعمل بعد Routing وقبل تنفيذ الـ endpoint. يقرأ <code>Endpoint.Metadata</code> ليجد السياسات المطلوبة، ثم يستدعي <code>IAuthorizationService.AuthorizeAsync</code>. إن فشل، يفرّق بين:</p>
        <ul>
          <li><strong>401 Unauthorized</strong>: لا توجد هوية أو فشلت المصادقة.</li>
          <li><strong>403 Forbidden</strong>: الهوية معروفة لكنها لا تملك الصلاحية.</li>
        </ul>
        <p>كتابة 401 بدل 403 (أو العكس) تربك العملاء وتخفي سبب الرفض. الإطار يختار تلقائيًا وفق نتيجة الـ handlers، لكن في Resource-Based قد تحتاج <code>Forbid()</code> صريحًا.</p>
        <p>الـ Policy قد تتكون من شروط متعددة. <code>RequireClaim</code> و<code>RequireRole</code> تُضاف كـ Requirements. كل Requirement يُقيَّم عبر Handler أو Assertion. إذا لم يكن هناك Handler مسجّل، تفشل السياسة ولا تُتجاهل — وهذا سلوك آمن مقصود.</p>
        <p>الـ Claims تأتي من التوكن أو من <code>IClaimsTransformation</code>. استخدم التحويل لإضافة claims محسوبة من قاعدة البيانات (مثل صلاحيات حديثة) بحذر: كل طلب يتحمّل تكلفة إضافية. البديل: اجعل التوكن يحمل الصلاحيات وأعد إصداره عند تغيّرها.</p>
      `,
      internalsTable: {
        head: ["الحالة", "الرمز", "المعنى"],
        rows: [
          ["لا توكن/توكن باطل", "401", "المصادقة مطلوبة"],
          ["توكن صالح بلا صلاحية", "403", "الهوية معروفة، الفعل مرفوض"],
          ["مورد غير موجود/غير مملوك", "404", "إخفاء الوجود (اختياري)"],
          ["سياسة غير مسجّلة", "500", "خطأ تكوين، ليس نجاحًا"],
        ],
      },
      tips: [
        {
          title: "Deny by default",
          body: "استخدم FallbackPolicyRequireAuthenticatedUser، وافتح المسارات العامة بـ <code>AllowAnonymous</code> صراحة. هذا يمنع نسيان الحماية.",
        },
        {
          title: "لا تثق بأي معرّف من العميل",
          body: "لا تقرأ <code>UserId</code> من جسم الطلب أو الـ query لاتخاذ قرار ملكية. خذه من <code>User.FindFirst(\"sub\")</code> فقط.",
        },
        {
          title: "افلتر في الاستعلام",
          body: "بدل جلب الطلب ثم فحص ملكيته، أضف شرط الملكية إلى <code>Where</code>. يمنع IDOR حتى لو نُسي فحص لاحق.",
        },
        {
          title: "اختبر السياسات",
          body: "اختبارات التكامل التي تتوقع 401/403 هي أرخص تأمين. لا تعتمد على مراجعة بشرية لكل تغيير.",
        },
      ],
      quiz: [
        {
          q: "ما الفرق بين 401 و403؟",
          options: [
            "لا فرق.",
            "401 يعني المصادقة مطلوبة/فاشلة، و403 يعني الهوية معروفة لكن غير مصرّح لها.",
            "401 للقراءة و403 للكتابة.",
            "403 يعني خطأ في الخادم.",
          ],
          answer: 1,
          explain:
            "401 تحدي مصادقة، و403 رفض تفويض لهوية معروفة. الخلط بينهما يضلل العميل.",
        },
        {
          q: "أين تُقيَّم Resource-Based Authorization؟",
          options: [
            "في Middleware قبل تحميل المورد.",
            "داخل الـ endpoint بعد تحميل المورد عبر IAuthorizationService.",
            "في قاعدة البيانات فقط.",
            "في JWT نفسه.",
          ],
          answer: 1,
          explain:
            "تحتاج المورد نفسه لاتخاذ القرار، لذا تُقيَّم بعد تحميله داخل التنفيذ.",
        },
        {
          q: "ما أفضل دفاع ضد IDOR؟",
          options: [
            "إخفاء المعرّفات فقط.",
            "فلترة الاستعلام بمالك المورد المستخرج من الهوية.",
            "استخدام أرقام عشوائية.",
            "تعطيل GET.",
          ],
          answer: 1,
          explain:
            "الفلترة في الاستعلام تمنع الوصول أصلًا، بدل الاعتماد على فحص لاحق قابل للنسيان.",
        },
      ],
      capstone: {
        title: "سياسات كتالوج وطلبات Souq.NET",
        goal: "نضيف تفويضًا دقيقًا: صلاحية إدارة الكتالوج، وسياسة ملكية للطلبات، مع رفض آمن واختبارات 401/403.",
        tasks: [
          "أضف سياسة <code>CanManageCatalog</code> تتطلب claim باسم <code>catalog:write</code>.",
          "طبّقها على مجموعة مسارات المنتجات.",
          "أضف <code>OrderOwnerRequirement</code> وHandler يتحقق من <code>order.UserId</code>.",
          "استخدم <code>IAuthorizationService</code> في <code>GET /api/orders/{id}</code> وأعد 404 عند عدم الملكية.",
          "أضف اختبار تكامل: بلا توكن 401، وبتوكن بلا صلاحية 403.",
        ],
        code: {
          lang: "csharp",
          title: "Resource-based check",
          code: `group.MapGet("/api/orders/{id:int}", async (
    int id,
    ClaimsPrincipal user,
    IAuthorizationService authorization,
    IOrderService orders,
    CancellationToken ct) =>
{
    var order = await orders.FindAsync(id, ct);
    if (order is null) return Results.NotFound();

    var result = await authorization.AuthorizeAsync(user, order, "OrderOwner");
    return result.Succeeded ? Results.Ok(order) : Results.NotFound();
});`,
        },
      },
    },
    {
      id: "security-hardening",
      title: "تقسية API: OWASP وCORS وRate Limiting",
      duration: 32,
      level: "متقدم",
      summary:
        "الأمان ليس إضافة توكن فقط. سنغطي أشهر أخطاء API، ونضبط CORS والحدود ومصادر الثقة بحيث لا تتحول ميزة صغيرة إلى ثغرة.",
      keywords: ["OWASP API Top 10", "BOLA", "IDOR", "mass assignment", "CORS", "rate limiting", "security headers", "secrets"],
      objectives: [
        "تحدد الأصول وحدود الثقة قبل كتابة كود الأمان.",
        "تمنع BOLA/IDOR بالفلترة على المالك لا بفحص لاحق.",
        "تستخدم DTOs لمنع mass assignment.",
        "تضبط CORS وسياسات المصادر والاعتمادات بدقة.",
        "تطبق Rate Limiting وتتعامل مع 429 وRetry-After."
      ],
      concept: `
        <p>الأمان سلسلة قرارات، لا ميزة واحدة. قبل أن تسأل «هل أضفت JWT؟»، اسأل: ما الأصول التي نحميها؟ من الفاعلون؟ أين تنتهي ثقة الخادم؟ ما أسوأ ما يحدث إذا انتحل مستخدم هوية آخر؟ نموذج التهديد يحدد ما يستحق الحماية، لا قائمة فحص ننسخها.</p>
        <h3>BOLA/IDOR: الثغرة الأولى</h3>
        <p><strong>Broken Object Level Authorization</strong> يحدث عندما تتحقق من تسجيل الدخول فقط، ثم تجلب المورد بالمعرف دون التأكد أن المستخدم يملكه. المهاجم يغيّر <code>/orders/10</code> إلى <code>/orders/11</code>. الحل ليس إخفاء المعرفات، بل فلترة الاستعلام على المالك أو تفويض المورد. أعد 404 بدل 403 إن كنت لا تريد كشف وجود المورد. اختبر كل endpoint بمعرف مستخدم آخر.</p>
        <h3>Mass assignment</h3>
        <p>إذا ربطت جسم الطلب مباشرة بكيان <code>Product</code> أو <code>User</code>، يمكن للعميل إرسال <code>IsAdmin: true</code> أو <code>Price: 0</code>. استخدم DTO يحتوي فقط الحقول المسموح تغييرها، ثم طبّق قواعد العمل في الخدمة. لا تعتمد على إخفاء الحقل في الواجهة؛ المهاجم لا يستخدم واجهتك. الـ DTO أيضًا يمنع over-posting ويوثّق العقد.</p>
        <h3>Injection وSQL</h3>
        <p>EF Core يستخدم معاملات افتراضيًا، لكن <code>FromSqlRaw</code> مع string interpolation أو <code>ExecuteSqlRaw</code> بمدخلات المستخدم يفتح الباب. استخدم <code>FromSqlInterpolated</code> أو معاملات صريحة. لا تبنِ أسماء أعمدة من الطلب؛ استخدم قائمة بيضاء. الحقن لا يخص SQL فقط: CSV injection، template injection، وcommand injection كلها نتيجة خلط البيانات بالتعليمات.</p>
        <h3>CORS ليس مصادقة</h3>
        <p>CORS سياسة يفرضها المتصفح لمنع صفحة من أصل مختلف من قراءة استجابة. هو لا يمنع <code>curl</code> أو خادمًا من استدعاء API، ولا يغني عن المصادقة. لا تستخدم <code>AllowAnyOrigin</code> مع <code>AllowCredentials</code>؛ هذا مزيج خطير وغالبًا غير مدعوم. حدد الأصول بدقة، والطرق والرؤوس المطلوبة فقط. preflight هو طلب OPTIONS يتحقق قبل الطلب الفعلي.</p>
        <h3>Rate limiting</h3>
        <p>الحدود تحمي من الإساءة ومن أخطاء العميل التي تسبب حملاً كبيرًا. لكنها ليست بديلًا عن المصادقة أو التحقق. اختر partition صحيحًا: IP قد يشترك فيه مستخدمون خلف NAT، والمستخدم المصادق أفضل. استخدم token bucket للسماح بدفعات قصيرة، أو fixed window للبساطة. أعد 429 مع <code>Retry-After</code> ولا تكشف تفاصيل داخلية. اختبر الحدود تحت تزامن.</p>
        <h3>الأسرار والإعدادات</h3>
        <p>لا تضع مفاتيح في Git أو في appsettings العامة. استخدم Secret Manager في التطوير ومتغيرات البيئة/خزنة أسرار في الإنتاج. لا تسجّل التوكنات أو كلمات المرور أو رؤوس Authorization. افحص الحزم بحثًا عن ثغرات، وثبّت الإصدارات. أخطاء التهيئة مثل تفعيل Swagger في الإنتاج أو رسائل تفصيلية قد تكشف أكثر من أي ثغرة كود.</p>
      `,
      walkthrough: [
        {
          title: "حدد الأصل وحدود الثقة",
          code: `// الأصل: طلبات المستخدم وبيانات الدفع.\n// الفاعل: زائر، عميل، موظف، خدمة داخلية.\n// الحد: الإنترنت -> API -> قاعدة البيانات.\n// القرار: كل مورد مملوك له هوية، وكل مسار يتحقق منها.`,
          lang: "text",
          body: `<p>اكتب هذا قبل الكود. في Souq، الطلب والمنتج والدفع أصول حساسة. الزائر يقرأ الكتالوج فقط، العميل يرى طلباته، الموظف يرى ما تسمح به سياسته. أي مسار لا يوضح «من يملك ماذا» هو مرشح لثغرة.</p>`
        },
        {
          title: "افلتر على المالك في الاستعلام",
          code: `var order = await _db.Orders\n    .AsNoTracking()\n    .FirstOrDefaultAsync(o =>\n        o.Id == id && o.UserId == userId, ct);\n\nreturn order is null ? Results.NotFound() : Results.Ok(order);`,
          lang: "csharp",
          body: `<p>المعرّف وحده لا يكفي. الشرط <code>o.UserId == userId</code> يجعل قاعدة البيانات ترفض الوصول قبل أن يصل الكائن إلى الذاكرة. لا تجلب الطلب ثم تفحص <code>if (order.UserId != userId)</code> بعد ذلك فقط؛ الفحص المتأخر يمكن نسيانه أو تجاوزه. أعد 404 إن أردت عدم كشف وجود الطلب.</p>`
        },
        {
          title: "جسم طلب محدود الحقول",
          code: `public sealed record UpdateProductRequest(\n    string Name,\n    decimal Price,\n    int Stock);\n\n// لا يوجد IsAdmin أو SellerId أو CreatedAt.`,
          lang: "csharp",
          body: `<p>هذا DTO يحدد ما يمكن للعميل تغييره. لا تستخدم <code>Product</code> كجسم الطلب. حتى لو أرسل العميل <code>IsAdmin</code>، لن يُربط لأنه غير موجود. ثم تحقق من الصلاحية وقواعد العمل في الخدمة. الحقول التي لا يعرفها العميل تُتجاهل أو تُرفض حسب العقد، لكن لا تُمرّر إلى الكيان.</p>`
        },
        {
          title: "استعلام خام بمعاملات",
          code: `var products = await _db.Products\n    .FromSqlInterpolated($@"\n        SELECT * FROM Products\n        WHERE CategoryId = {categoryId}\n          AND Price <= {maxPrice}")\n    .AsNoTracking()\n    .ToListAsync(ct);`,
          lang: "csharp",
          body: `<p><code>FromSqlInterpolated</code> يحوّل القيم إلى معاملات، لا يدمجها كنص. لا تستخدم <code>FromSqlRaw($"... {value}")</code> لأن string interpolation يبني SQL قبل EF. حتى مع المعاملات، لا تمرّر أسماء أعمدة أو ترتيب من العميل. استخدم <code>EF.Functions</code> أو LINQ حيث ممكن.</p>`
        },
        {
          title: "فعّل HTTPS وHSTS",
          code: `builder.Services.AddHsts(options =>\n{\n    options.MaxAge = TimeSpan.FromDays(365);\n    options.IncludeSubDomains = true;\n});\n\napp.UseHttpsRedirection();\napp.UseHsts();`,
          lang: "csharp",
          body: `<p>HSTS يخبر المتصفح أن يستخدم HTTPS دائمًا، ويمنع هجمات downgrade. لا تفعّله في التطوير مع شهادة محلية غير موثوقة. في الإنتاج، أنهِ TLS عند البوابة أو الخادم حسب البنية، لكن لا تنقل البيانات الحساسة عبر HTTP. أضف إعادة توجيه دائمة من HTTP إن كانت البوابة لا تفعل ذلك.</p>`
        },
        {
          title: "رؤوس أمان أساسية",
          code: `app.Use(async (context, next) =>\n{\n    context.Response.Headers["X-Content-Type-Options"] = "nosniff";\n    context.Response.Headers["X-Frame-Options"] = "DENY";\n    context.Response.Headers["Referrer-Policy"] = "no-referrer";\n    await next();\n});`,
          lang: "csharp",
          body: `<p>هذه الرؤوس ليست علاجًا لكل شيء، لكنها تقلل مخاطر MIME sniffing وclickjacking وتسريب referrer. لـ API نقي، بعض الرؤوس أقل أهمية، لكنها مفيدة لواجهات Swagger أو صفحات أخطاء. لا تضف CSP عشوائيًا؛ اكتب سياسة تناسب تطبيقك واختبرها.</p>`
        },
        {
          title: "CORS بأصل محدد",
          code: `builder.Services.AddCors(options =>\n{\n    options.AddPolicy("web", policy =>\n        policy.WithOrigins("https://app.souq.example")\n              .WithMethods("GET", "POST", "PUT", "DELETE")\n              .WithHeaders("Authorization", "Content-Type")\n              .AllowCredentials());\n});`,
          lang: "csharp",
          body: `<p>هذا يسمح لصفحة الويب على الأصل المحدد فقط. لا تستخدم <code>AllowAnyOrigin</code> مع credentials. لا تعكس أي Origin يصل إليك. إذا كانت عدة بيئات، ضع قائمة صريحة لكل بيئة. تذكّر أن CORS يحمي المتصفح، لا الخادم؛ المصادقة والتفويض يبقيان مسؤوليتك.</p>`
        },
        {
          title: "رتّب Middleware بشكل صحيح",
          code: `app.UseHttpsRedirection();\napp.UseCors("web");\napp.UseAuthentication();\napp.UseAuthorization();\napp.UseRateLimiter();\napp.MapControllers();`,
          lang: "csharp",
          body: `<p>CORS يجب أن يعمل قبل المصادقة وبعد HTTPS، حتى تُعالج طلبات preflight دون توكن. المصادقة قبل التفويض. Rate limiter قبل endpoints ليرفض الطلبات الزائدة مبكرًا. الترتيب الخاطئ قد يجعل preflight يفشل أو يجعل الحدود لا تُطبق. اختبر OPTIONS فعليًا.</p>`
        },
        {
          title: "حد عام لكل API",
          code: `builder.Services.AddRateLimiter(options =>\n{\n    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;\n    options.AddFixedWindowLimiter("api", opt =>\n    {\n        opt.PermitLimit = 100;\n        opt.Window = TimeSpan.FromMinutes(1);\n        opt.QueueLimit = 0;\n    });\n});\n\napp.UseRateLimiter();`,
          lang: "csharp",
          body: `<p>هذا حد ثابت 100 طلب في الدقيقة لكل partition افتراضي. <code>QueueLimit = 0</code> يرفض فورًا بدل تكديس الطلبات. الحد العام يحمي من الطفرات، لكنه قد يعاقب مستخدمًا مشتركًا خلف NAT. استخدم حدًا لكل مستخدم مصادق، أو اجمع بين IP والمستخدم.</p>`
        },
        {
          title: "حد لكل مستخدم",
          code: `options.AddPolicy("per-user", context =>\n{\n    var userId = context.User.FindFirstValue(ClaimTypes.NameIdentifier)\n                 ?? context.Connection.RemoteIpAddress?.ToString()\n                 ?? "anonymous";\n\n    return RateLimitPartition.GetFixedWindowLimiter(userId, _ =>\n        new FixedWindowRateLimiterOptions\n        {\n            PermitLimit = 60,\n            Window = TimeSpan.FromMinutes(1),\n            QueueLimit = 0\n        });\n});`,
          lang: "csharp",
          body: `<p>المستخدم المصادق يُحدد بهويته، والزائر بعنوان IP كحل احتياطي. تذكر أن IP يمكن أن يتغير أو يُشارك. لا تستخدم البريد أو اسم المستخدم كـpartition لأن قيمته غير مستقرة أو قابلة للتزوير. رتّب <code>UseAuthentication</code> قبل limiter إذا أردت الوصول إلى <code>context.User</code>.</p>`
        },
        {
          title: "أعد 429 مع Retry-After",
          code: `options.OnRejected = async (context, ct) =>\n{\n    context.HttpContext.Response.StatusCode = 429;\n    context.HttpContext.Response.Headers.RetryAfter = "60";\n    await context.HttpContext.Response.WriteAsJsonAsync(new\n    {\n        title = "Too many requests",\n        status = 429\n    }, ct);\n};`,
          lang: "csharp",
          body: `<p><code>Retry-After</code> يخبر العميل متى يعيد المحاولة. لا ترجع تفاصيل عن الحدود الداخلية أو عناوين أخرى. 429 يعني «أبطئ»، لا «غير مصرح». لا تضع حدًا صارمًا جدًا على endpoints المصادقة فقط فتمنع المستخدمين الشرعيين؛ استخدم حدودًا مختلفة للمصادقة والقراءة والكتابة.</p>`
        },
        {
          title: "لا تسرّب الأسرار في السجلات",
          code: `logger.LogInformation(\n    "Order {OrderId} placed by {UserId}",\n    order.Id, userId);\n\n// لا تسجّل: Authorization, password, card number, tokens.`,
          lang: "csharp",
          body: `<p>السجلات أصل أمني. لا تسجّل رؤوس Authorization أو جسم الطلب كاملًا. استخدم معرفات آمنة ورسائل منظمة. افحص appsettings وGit history عن مفاتيح. استخدم Secret Manager في التطوير وخزنة أسرار في الإنتاج، ودوّر المفاتيح عند الاشتباه. الأمان يشمل ما تكتبه في السجل، لا ما تمنعه في الـ endpoint فقط.</p>`
        }
      ],
      compare: {
        intro: `<p>الإعدادان يبدوان «آمنين»، لكن أحدهما يترك الباب مفتوحًا للمهاجم.</p>`,
        before: {
          label: "إعداد مفتوح",
          lang: "csharp",
          title: "قبل",
          code: `app.UseCors(p => p\n    .AllowAnyOrigin()\n    .AllowAnyMethod()\n    .AllowAnyHeader());\n\napp.MapGet("/orders/{id}", async (int id, AppDb db) =>\n    await db.Orders.FindAsync(id));`,
          points: [
            "أي أصل يستطيع قراءة الاستجابة.",
            "لا تحقق من ملكية الطلب.",
            "كل الطرق والرؤوس مسموحة.",
            "لا حد لعدد الطلبات."
          ]
        },
        after: {
          label: "تقسية موجهة",
          lang: "csharp",
          title: "بعد",
          code: `app.UseCors("web");\napp.UseRateLimiter();\n\napp.MapGet("/orders/{id}", async (\n    int id, ClaimsPrincipal user, AppDb db, CancellationToken ct) =>\n{\n    var userId = user.FindFirstValue(ClaimTypes.NameIdentifier);\n    var order = await db.Orders.AsNoTracking()\n        .FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId, ct);\n    return order is null ? Results.NotFound() : Results.Ok(order);\n});`,
          points: [
            "أصل محدد فقط.",
            "الملكية شرط في الاستعلام.",
            "حدود طلبات مطبقة.",
            "لا كشف وجود مورد ليس للمستخدم."
          ]
        },
        verdict: `<p>الأمان ليس قائمة رؤوس؛ هو منع الوصول غير المصرح به في كل طبقة. CORS وRate Limiting إضافيان، لكنهما لا يغنيان عن التفويض.</p>`
      },
      internals: `
        <p>عند وصول طلب، يمر عبر middleware بالترتيب. HTTPS redirect يمنع النص المكشوف، CORS يعالج الطلبات المتقاطعة، المصادقة تبني <code>ClaimsPrincipal</code>، التفويض يقرر، والـ rate limiter يرفض ما تجاوز الحد. ترتيب خاطئ قد يعني أن preflight يُرفض أو أن الحد لا يرى هوية المستخدم. اختبر الترتيب، لا تفترضه.</p>
        <p><strong>BOLA</strong> لا يظهر في اختبارات المصادقة العادية لأن المستخدم مصادق فعلًا. اختبار التفويض يحتاج مستخدمين مختلفين وموارد لكل منهما. اكتب اختبار تكامل: مستخدم A يطلب مورد B ويجب أن يحصل على 404/403. هذا الاختبار أهم من عشرات اختبارات الـ happy path.</p>
        <h3>CORS وpreflight</h3>
        <p>المتصفح يرسل OPTIONS إذا كان الطلب غير بسيط (Authorization، Content-Type JSON، أو method غير بسيط). الخادم يرد بـAccess-Control-Allow-Origin/Methods/Headers. إذا كان credentials مفعّلًا، لا يجوز استخدام <code>*</code> للأصل. CORS لا يمنع طلبات الخادم إلى الخادم؛ إذا كان API عامًا، فالمصادقة هي الحماية.</p>
        <h3>Rate limiting</h3>
        <p>الخوارزميات تختلف: fixed window بسيط لكنه يسمح بانفجار عند حدود النافذة؛ sliding window أدق؛ token bucket يسمح بدفعات مع تجديد تدريجي. اختر حسب السلوك. الموزع عبر عدة replicas يحتاج مخزنًا مشتركًا (Redis) أو بوابة تدير الحدود. الحد المحلي وحده لا يحمي عند التوسع الأفقي.</p>
        <h3>الأسرار</h3>
        <p>مفتاح توقيع JWT أو اتصال قاعدة البيانات إذا تسرب يعني اختراقًا كاملًا. لا تحفظه في صورة Docker أو ملف في المستودع. استخدم حقن إعدادات، وصلاحيات وصول ضيقة، ودوّر المفاتيح. راقب الوصول غير المتوقع. الأمان عملية تشغيلية مستمرة، وليس إعدادًا لمرة واحدة.</p>
      `,
      internalsTable: {
        head: ["الخطر", "مثال", "الدفاع"],
        rows: [
          ["BOLA/IDOR", "تغيير معرّف الطلب", "فلترة على المالك في الاستعلام"],
          ["Mass assignment", "إرسال IsAdmin", "DTO محدود + قواعد عمل"],
          ["Injection", "دمج نص في SQL", "معاملات وقائمة بيضاء"],
          ["CORS مفتوح", "AllowAnyOrigin + credentials", "أصول محددة وطرق محددة"],
          ["Abuse", "آلاف الطلبات", "Rate limit + 429 + مراقبة"],
          ["تسريب أسرار", "توكن في السجل", "عدم التسجيل + خزنة أسرار"]
        ]
      },
      tips: [
        {
          title: "افحص الملكية في الاستعلام",
          body: "لا تجلب المورد ثم تفحص المالك. أضف شرط المالك إلى WHERE، وأعد 404 إن أردت عدم كشف الوجود."
        },
        {
          title: "DTOS فقط للمدخلات",
          body: "لا تربط الكيان مباشرة. حدد الحقول المسموح تغييرها، وطبّق قواعد العمل في طبقة الخدمة."
        },
        {
          title: "CORS ليس جدار حماية",
          body: "هو سياسة متصفح. لا تحمي API عامًا. استخدم مصادقة وتفويضًا وحدودًا، واضبط الأصول بدقة."
        },
        {
          title: "اختبر السيناريوهات السلبية",
          body: "مستخدم A يطلب مورد B، طلب بلا توكن، طلب بتوكن منتهٍ، تجاوز الحد. هذه الاختبارات تكشف الثغرات الحقيقية."
        }
      ],
      quiz: [
        {
          q: "ما هو BOLA/IDOR؟",
          options: [
            "خطأ في تنسيق JSON.",
            "وصول مستخدم مصادق إلى مورد لا يملكه بتغيير المعرّف.",
            "هجوم على شهادة TLS.",
            "زيادة عدد الطلبات."
          ],
          answer: 1,
          explain: "BOLA يحدث عندما يتحقق النظام من المصادقة فقط، لا من ملكية المورد. الحل فلترة المورد على المالك أو تفويضه."
        },
        {
          q: "ما وظيفة CORS؟",
          options: [
            "يمنع كل المستخدمين غير المصادقين.",
            "يفرض على المتصفح قيود الأصل للطلبات المتقاطعة.",
            "يشفر قاعدة البيانات.",
            "يحدد عدد الطلبات في الدقيقة."
          ],
          answer: 1,
          explain: "CORS سياسة يفرضها المتصفح. لا يمنع curl ولا يغني عن المصادقة والتفويض."
        },
        {
          q: "ماذا يعني 429 Too Many Requests؟",
          options: [
            "الخادم تعطل.",
            "العميل تجاوز حد الطلبات المسموح.",
            "المستخدم غير مصادق.",
            "المورد غير موجود."
          ],
          answer: 1,
          explain: "429 يعني تجاوز حد المعدل. أضف Retry-After وسجّل الحدث، ولا تكشف تفاصيل داخلية."
        }
      ],
      capstone: {
        title: "تقسية Souq API",
        goal: "أغلق ثغرات الوصول، واضبط CORS والحدود، وأثبت أن الاختبارات السلبية تفشل كما يجب.",
        tasks: [
          "أضف اختبار تكامل يثبت أن مستخدمًا لا يستطيع قراءة طلب مستخدم آخر (BOLA).",
          "استبدل ربط الكيان في تحديث المنتج بـ<code>UpdateProductRequest</code> محدود الحقول.",
          "اضبط سياسة CORS لأصل الواجهة فقط مع الرؤوس والطرق المطلوبة.",
          "أضف Rate Limiter لكل مستخدم مع 429 و<code>Retry-After</code>.",
          "أضف رؤوس أمان وفعّل HSTS في بيئة الإنتاج، وتأكد من عدم تسجيل Authorization."
        ],
        code: {
          lang: "csharp",
          title: "اتجاه الحماية",
          code: `var order = await _db.Orders.AsNoTracking()\n    .FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId, ct);\n\nreturn order is null ? Results.NotFound() : Results.Ok(order);`,
        },
      },
    },
  ],
});
