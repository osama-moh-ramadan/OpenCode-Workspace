# -*- coding: utf-8 -*-
"""Stage 6 module 2 (part B): s6-m2-l3 (Key Vault + Managed Identity), s6-m2-l4 (Azure data services)."""

TODAY = "2026-10-22"

# ══════════════════════════════════════════════════════════════════════════
# s6-m2-l3 — Key Vault وManaged Identity
# ══════════════════════════════════════════════════════════════════════════
_L3 = {
    "id": "s6-m2-l3",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "في الدرس السابق (6.1.5) تعلّمت إزاي تفصل الإعدادات عن الأسرار في Kubernetes. على Azure فيه إجابة أقوى بكثير: **مفيش سر في تطبيقك خالص**. التطبيق بياخد **هوية** (Managed Identity)، والهوية بتاخد **صلاحية** (RBAC) على Key Vault أو قاعدة البيانات أو Storage — والباقي توكنات قصيرة العمر بتتجدد لوحدها. الدرس ده بيعلّمك السلسلة الكاملة: إنشاء vault بصلاحيات صحيحة · قراءة السر في .NET بطريقة آمنة · **الطريقة المختلفة لكل منصة** (App Service references / Container Apps secrets / AKS CSI driver) · تدوير السر من غير توقف · وحماية مفاتيح Data Protection اللي بتكسر الجلسات في التطبيقات متعددة النسخ."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "Managed Identity", "def": "هوية تُدار تلقائيًا في Microsoft Entra ID لخدمة Azure. **System-assigned**: مرتبطة بمورد واحد وبتتموت معه. **User-assigned**: مورد مستقل يُربط بعدة خدمات (أفضل للأسرار المشتركة أو لإعادة الإنشاء)."},
            {"term": "RBAC", "def": "الصلاحيات الحديثة الموصى بها: أدوار مثل **Key Vault Secrets User** (قراءة القيم) أو **AcrPull** على نطاق مورد. بديلها القديم «access policies» — الجديد أدق وأسهل تدقيقًا."},
            {"term": "Key Vault", "def": "خدمة لتخزين **secrets** (قيم) · **keys** (مفاتيح تشفير) · **certificates** (شهادات TLS). كل قراءة بتُسجَّل في سجل تدقيق."},
            {"term": "Soft-delete وPurge protection", "def": "حذف قابل للتراجع (افتراضي) + حماية من المسح النهائي لفترة. بدونهما، حذف غلط = فقدان نهائي للسر وشهادات TLS."},
            {"term": "Key Vault reference", "def": "في App Service/Functions: قيمة إعداد بتكتب كـ`@Microsoft.KeyVault(SecretUri=…)` فتُجلب وقت التشغيل **وتُحدَّث تلقائيًا عند التدوير** من غير إعادة نشر."},
            {"term": "Secrets Store CSI Driver", "def": "في AKS: بيوصّل أسرار Key Vault للـPod كملفات (أو يزامنها كـKubernetes Secret) باستخدام Workload Identity."},
            {"term": "Workload Identity", "def": "ربط ServiceAccount في Kubernetes بـManaged Identity عبر **federated credential** — يعني Pod بياخد هوية Azure من غير سر. (نظام Pod Identity القديم **مهجور**.)"},
            {"term": "`DefaultAzureCredential`", "def": "سلسلة اعتماد بتجرّب بالترتيب: Environment → Workload Identity → Managed Identity → SharedTokenCache → Visual Studio/Code → Azure CLI → Azure PowerShell → Azure Developer CLI. مريحة محليًا، لكن في الإنتاج الأفضل اعتماد **حتمي**."},
            {"term": "`ManagedIdentityCredential`", "def": "الاعتماد المحدد: يستخدم هوية الخدمة فقط. توصية Microsoft للإنتاج (سلوك متوقع، بلا تسلسل طويل عند الفشل)."},
            {"term": "تدوير السر (Rotation)", "def": "تغيير قيمة السر بدون توقف: اكتب الجديد → وزّعه → تحقق → احذف القديم. في Key Vault ممكن تلقائيًا لبعض الخدمات."},
            {"term": "App Configuration", "def": "خدمة للإعدادات غير السرية (feature flags، قيم لكل بيئة) مع **مراجع لـKey Vault** للقيم السرية — فصل أنظف من vault مليء بمفاتيح إعداد."},
            {"term": "Data Protection keys", "def": "مفاتيح ASP.NET Core لتشفير الكوكيز/tokens الحماية. لو كل نسخة ولّدت مفاتيحها محليًا، **النسخة الثانية مش هتفك تشفير كوكي الأولى** — لازم تخزين مشترك."},
        ]},

        # ── 1
        {"type": "heading", "level": 2, "text": "① القاعدة الذهبية: الهوية بدل السر — وطريقة إيصال السر تختلف حسب المنصة"},
        {"type": "callout", "kind": "goal", "title": "الهدف",
         "md": "لا connection strings فيها كلمات سر في Git · لا أسرار في `appsettings.json` · لا `--admin-enabled true` على ACR · لا client secret في متغيرات البيئة. بدل ده: **Managed Identity + RBAC بأقل امتياز**، والأسرار القليلة المتبقية (مفاتيح مزودين خارجيين) في **Key Vault** مع تدقيق لكل قراءة."},
        {"type": "table", "caption": "إزاي توصل السر/الهوية للتطبيق حسب المنصة (من 6.2.1)",
         "head": ["المنصة", "الهوية", "الطريقة الموصى بها للأسرار", "Key Vault references؟", "تحديث عند التدوير"],
         "rows": [
             ["App Service / Functions", "system- أو user-assigned على الـwebapp",
              "**مراجع Key Vault في app settings** (`@Microsoft.KeyVault(SecretUri=…)`) أو `AddAzureKeyVault` في الكود",
              "✓ مدعومة أصلًا (وتُحدَّث تلقائيًا)", "تلقائي للمراجع؛ للكود محتاج `ReloadInterval` أو إعادة تشغيل"],
             ["Container Apps", "system- أو user-assigned على الـcontainer app",
              "`az containerapp secret set` + `secretRef` في env، **أو** قراءة من Key Vault في الكود بالهوية",
              "✗ (لا توجد مراجع KV كما في App Service)", "إعادة ضبط السر + rollout، أو قراءة بالكود مع reload"],
             ["AKS", "**Workload Identity** (ServiceAccount + federated credential)",
              "**Secrets Store CSI Driver** مع `SecretProviderClass` (ملفات أو مزامنة كـK8s Secret)",
              "△ عبر CSI (تُركّب كملفات)", "إعادة مزامنة دورية بالـdriver (فعّل `enableSecretRotation`)"],
             ["محليًا (dev)", "لا هوية — `az login` أو Visual Studio",
              "**dotnet user-secrets** (1.1.x) أو vault تطوير منفصل",
              "—", "يدوي"],
         ]},

        # ── 2
        {"type": "heading", "level": 2, "text": "② الإنشاء والصلاحيات بـAzure CLI"},
        {"type": "code", "lang": "bash", "title": "azure/40-keyvault.sh", "filename": "azure/40-keyvault.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail

LOC=westeurope; RG=rg-shop-dev; VAULT=kv-shop-dev      # اسم الـvault عالمي: حروف وأرقام وشرطات
SUB=$(az account show --query id --output tsv)

# ═══ 1) إنشاء vault: RBAC مفعّل + حماية من المسح + تدقيق ═══
az keyvault create --name "$VAULT" --resource-group "$RG" --location "$LOC" \
  --enable-rbac-authorization true \
  --retention-days 90 \
  --enable-purge-protection true
# ماذا تفعل الأعلام أعلاه:
#   --enable-rbac-authorization true  → الصلاحيات بـRBAC (مش access policies القديمة)
#   --retention-days 90               → soft-delete: 90 يومًا للتراجع عن الحذف
#   --enable-purge-protection true    → يمنع المسح النهائي حتى للمالك
# ⚠ قاعدة bash: لا تضع تعليقًا في نفس سطر "\" (الشرطة الخلفية) — يكسر الأمر.

# ═══ 2) صلاحيات للبشر: أقل امتياز ═══
az role assignment create --role "Key Vault Secrets Officer" \
  --assignee-object-id "$(az ad signed-in-user show --query id -o tsv)" \
  --assignee-principal-type User --scope "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.KeyVault/vaults/$VAULT"
# Secrets Officer = يقرأ/يكتب/يدوّر الأسرار، ولا يمسح الـvault ولا يغيّر الصلاحيات.

# ═══ 3) كتابة سر (القيمة من stdin أو متغير — لا من سطر الأوامر المكشوف في history) ═══
read -rs DB_PASSWORD && printf '%s' "$DB_PASSWORD" | \
  az keyvault secret set --vault-name "$VAULT" --name "orders-db-password" --file /dev/stdin
az keyvault secret set --vault-name "$VAULT" --name "orders-conn" \
  --value "Server=sql-shop.database.windows.net;Database=shop;Authentication=Active Directory Default"
# أسماء الأسرار: استخدم `--` لتمثيل التداخل، فتُقرأ في .NET كمفاتيح متداخلة:
#   Orders__Retry__MaxAttempts  →  configuration["Orders:Retry:MaxAttempts"]
az keyvault secret set --vault-name "$VAULT" --name "Orders--MaxTotalWithoutApproval" --value "5000"

# ═══ 4) هوية التطبيق + صلاحية القراءة فقط ═══
# App Service:
az webapp identity assign --name shop-orders --resource-group "$RG"
PRINCIPAL=$(az webapp identity show --name shop-orders --resource-group "$RG" --query principalId -o tsv)
VAULT_ID=$(az keyvault show --name "$VAULT" --resource-group "$RG" --query id -o tsv)
az role assignment create --role "Key Vault Secrets User" \
  --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal --scope "$VAULT_ID"

# Container Apps:
az containerapp identity assign --name orders --resource-group "$RG" --system-assigned
az role assignment create --role "Key Vault Secrets User" \
  --assignee-object-id "$(az containerapp identity show --name orders --resource-group "$RG" --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal --scope "$VAULT_ID"

# ═══ 5) مرجع Key Vault في إعدادات App Service (الطريقة الأبسط والأدق) ═══
az webapp config appsettings set --name shop-orders --resource-group "$RG" --settings \
  'ConnectionStrings__Default=@Microsoft.KeyVault(SecretUri=https://kv-shop-dev.vault.azure.net/secrets/orders-conn/)'
# التحقق إن المرجع اتحلّ فعلًا (مش رسالة خطأ مخفية):
az webapp config appsettings list --name shop-orders --resource-group "$RG" \
  --query "[?contains(name,'KeyVaultReferenceStatus')]" --output table

# ═══ 6) تدقيق: من قرأ ماذا ومتى ═══
az monitor diagnostic-settings create --name kv-audit \
  --resource "$VAULT_ID" --workspace "$(az monitor log-analytics workspace show -g $RG -n la-shop-dev --query id -o tsv)" \
  --logs '[{"category":"AuditEvent","enabled":true}]'
# استعلام مفيد في Log Analytics:
#   AzureDiagnostics | where ResourceProvider == "MICROSOFT.KEYVAULT"
#     | project TimeGenerated, OperationName, identity_claim_appid_s, clientInfo_s
'''},
        {"type": "code", "lang": "yaml", "title": "k8s/secretproviderclass.yaml — AKS: أسرار Key Vault كملفات في الـPod", "filename": "k8s/secretproviderclass.yaml", "code": r'''# المتطلبات:
#   az aks create ... --enable-addons azure-keyvault-secrets-provider   (أو على cluster قائم)
#   az aks update ... --enable-oidc-issuer --enable-workload-identity
#
# ① ServiceAccount في الـnamespace مرتبط بالهوية عبر annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-sa
  namespace: shop
  annotations:
    azure.workload.identity/client-id: "<USER_ASSIGNED_CLIENT_ID>"
---
# ② الهوية المُدارة تحتاج federated credential موجّه للـServiceAccount
#    (الأمر في الملف التالي — لا تُخزّن أي سر هنا)
# ③ SecretProviderClass: أي أسرار تُجلب وبأي هوية
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: orders-kv
  namespace: shop
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"          # Pod Identity مهجور — لا تستخدمه
    useVMManagedIdentity: "false"    # false = نستخدم Workload Identity بالـclientID
    clientID: "<USER_ASSIGNED_CLIENT_ID>"
    keyvaultName: "kv-shop-dev"
    tenantId: "<TENANT_ID>"
    objects: |
      array:
        - |
          objectName: orders-conn
          objectType: secret
        - |
          objectName: Orders--MaxTotalWithoutApproval
          objectType: secret
        - |
          objectName: shop-tls
          objectType: cert           # شهادات TLS أيضًا
  # ④ اختياري: مزامنة القيم كـKubernetes Secret عادي (لـenv vars)
  secretObjects:
    - secretName: orders-kv-synced
      type: Opaque
      data:
        - objectName: orders-conn
          key: ConnectionStrings__Default
        - objectName: Orders--MaxTotalWithoutApproval
          key: Orders__MaxTotalWithoutApproval
---
# ⑤ الـDeployment: تسمية Workload Identity + الـvolume
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
  namespace: shop
spec:
  replicas: 2
  selector:
    matchLabels: { app: orders }
  template:
    metadata:
      labels:
        app: orders
        azure.workload.identity/use: "true"   # بدونها لا يُحقن التوكن → فشل مصادقة
    spec:
      serviceAccountName: orders-sa
      containers:
        - name: orders
          image: acrshopdev.azurecr.io/shop/orders@sha256:<DIGEST>
          ports: [{ name: http, containerPort: 8080 }]
          envFrom:
            - secretRef: { name: orders-kv-synced }   # الطريقة الأبسط: env
          volumeMounts:
            - name: kv
              mountPath: /mnt/secrets-store
              readOnly: true
      volumes:
        - name: kv
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes:
              secretProviderClass: orders-kv
'''},
        {"type": "code", "lang": "bash", "title": "azure/41-workload-identity.sh + فحص وتدوير", "filename": "azure/41-workload-identity.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
RG=rg-shop-dev; VAULT=kv-shop-dev; ID_NAME=mi-shop-aks

# ═══ 1) هوية user-assigned + صلاحية قراءة على الـvault ═══
az identity create --name "$ID_NAME" --resource-group "$RG"
CLIENT_ID=$(az identity show -n "$ID_NAME" -g "$RG" --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show -n "$ID_NAME" -g "$RG" --query principalId -o tsv)
az role assignment create --role "Key Vault Secrets User" --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --scope "$(az keyvault show -n "$VAULT" -g "$RG" --query id -o tsv)"

# ═══ 2) اربط الهوية بـServiceAccount في الـcluster (federated credential) ═══
AKS_OIDC_ISSUER=$(az aks show -n aks-shop -g "$RG" --query oidcIssuerProfile.issuerUrl -o tsv)
az identity federated-credential create --name orders-fic \
  --identity-name "$ID_NAME" --resource-group "$RG" \
  --issuer "$AKS_OIDC_ISSUER" \
  --subject "system:serviceaccount:shop:orders-sa" \
  --audiences api://AzureADTokenExchange
# انتبه: هناك حد لعدد الـfederated credentials لكل هوية — راجع توثيق AKS Identity Binding
# (الخيار الموصى به حديثًا لأنه يتجاوز حد Workload Identity).

# ═══ 3) فحص سريع: هل السر وصل للـPod فعلًا؟ ═══
kubectl -n shop get secretproviderclass orders-kv -o yaml | tail -n 20
kubectl -n shop describe pod -l app=orders | grep -A5 -i "csi\|secrets-store" || true
kubectl -n shop exec deploy/orders -- sh -c 'printenv | grep -c ConnectionStrings || true'
kubectl -n shop logs -l app=orders --tail=50 | grep -i "credential\|401\|403" || echo "لا أخطاء مصادقة"

# ═══ 4) تدوير سر بدون توقف (النمط الآمن) ═══
#   أ) أضف القيمة الجديدة (الإصدار الجديد في Key Vault — القديم لسه موجود)
printf '%s' "$NEW_DB_PASSWORD" | az keyvault secret set --vault-name "$VAULT" \
  --name "orders-db-password" --file /dev/stdin
#   ب) حدّث قاعدة البيانات/المزود ليقبل القيمتين لفترة (أو دوّر في نافذة صيانة)
#   ج) أعد تشغيل التطبيق/الـrollout ليقرأ الإصدار الجديد
kubectl -n shop rollout restart deploy/orders && kubectl -n shop rollout status deploy/orders
#   د) تحقق ثم ألغِ القيمة القديمة (احذف الإصدار القديم — لا تحذف السر كله)
az keyvault secret show-versions --vault-name "$VAULT" --name "orders-db-password" --output table

# ═══ 5) استرجاع بعد حذف غلط (soft-delete) ═══
az keyvault secret recover --vault-name "$VAULT" --name "orders-db-password"
az keyvault recover --name "$VAULT"          # استرجاع vault محذوف خلال فترة الاحتفاظ

# ═══ 6) مراجعة: من يملك وصولًا؟ (تدقيق دوري) ═══
az role assignment list --scope "$(az keyvault show -n "$VAULT" -g "$RG" --query id -o tsv)" \
  --output table
'''},

        # ── 3) الكود
        {"type": "heading", "level": 2, "text": "③ الكود: قراءة الأسرار والاعتماد الحتمي في .NET"},
        {"type": "code", "lang": "csharp", "title": "src/Orders.Api/Infrastructure/AzureSecrets.cs", "filename": "src/Orders.Api/Infrastructure/AzureSecrets.cs", "code": r'''using Azure.Core;
using Azure.Extensions.AspNetCore.Configuration.Secrets;
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
using Microsoft.Extensions.Azure;

namespace Shop.Orders.Infrastructure;

public static class AzureSecrets
{
    /// <summary>
    /// يبني اعتمادًا حتميًا: Managed Identity في Azure، وسلسلة تطوير محددة محليًا.
    /// لا تستخدم DefaultAzureCredential في الإنتاج — تسلسلها الطويل يجعل الفشل
    /// بطيئًا وغامضًا، وقد يلتقط اعتمادًا غير مقصود من البيئة.
    /// </summary>
    public static TokenCredential BuildCredential(IConfiguration cfg, IHostEnvironment env)
    {
        if (env.IsProduction() || env.IsStaging())
        {
            var clientId = cfg["Azure:UserAssignedClientId"];   // اختياري (user-assigned)
            return string.IsNullOrWhiteSpace(clientId)
                ? new ManagedIdentityCredential()                                    // system-assigned
                : new ManagedIdentityCredential(ManagedIdentityId.FromUserAssignedClientId(clientId));
        }

        // تطوير محلي: سلسلة قصيرة وصريحة (az login أو Visual Studio) — بلا env credentials
        return new ChainedTokenCredential(
            new AzureCliCredential(),
            new AzurePowerShellCredential(),
            new VisualStudioCredential());
    }

    /// <summary>يضيف Key Vault كمصدر إعداد، مع فلترة أسماء وإعادة تحميل اختيارية.</summary>
    public static WebApplicationBuilder AddVault(this WebApplicationBuilder builder, TokenCredential credential)
    {
        var vaultName = builder.Configuration["Azure:KeyVaultName"]
            ?? throw new InvalidOperationException("Azure:KeyVaultName مطلوب");

        builder.Configuration.AddAzureKeyVault(
            new Uri($"https://{vaultName}.vault.azure.net/"),
            credential,
            new AzureKeyVaultConfigurationOptions
            {
                // ① اقرأ فقط أسرار تطبيقك من vault مشترك — أمان + إقلاع أسرع:
                Manager = new PrefixSecretManager("Orders"),
                // ② null (الافتراضي) = بلا إعادة تحميل. ضع مدة لو محتاج تدويرًا حيًا:
                ReloadInterval = TimeSpan.FromMinutes(15),
            });
        return builder;
    }

    /// <summary>عملاء Azure SDK بعميل واحد وهوية واحدة (Singleton — شارك كاش التوكن).</summary>
    public static IServiceCollection AddAzureServiceClients(
        this IServiceCollection services, IConfiguration cfg, TokenCredential credential)
    {
        services.AddAzureClients(cb =>
        {
            cb.UseCredential(credential);                 // كل العملاء يستخدمون نفس الاعتماد
            cb.AddSecretClient(new Uri($"https://{cfg["Azure:KeyVaultName"]}.vault.azure.net"));
            cb.AddBlobServiceClient(new Uri($"https://{cfg["Azure:StorageAccountUrl"]}"));
            // ConfigureClientDefaults: مهلة + إعادة محاولة موحّدة (نفس روح 5.2.3)
            cb.ConfigureDefaults(o =>
            {
                o.Retry.MaxRetries = 3;
                o.Retry.Mode = Azure.Core.RetryMode.Exponential;
                o.Diagnostics.IsLoggingContentEnabled = false;   // ⚠ لا تسجّل محتوى الأسرار
            });
        });
        return services;
    }

    /// <summary>يقرأ سرًا عند الحاجة (تدوير/قيم ديناميكية) بدل تخزينه في الذاكرة.</summary>
    public static async Task<string> GetSecretAsync(SecretClient client, string name, CancellationToken ct)
    {
        KeyVaultSecret secret = await client.GetSecretAsync(name, cancellationToken: ct);
        return secret.Value;
    }
}

/// <summary>
/// يحمّل الأسرار ذات البادئة فقط. الأسماء في الـvault: Orders--ConnectionString
/// تُقرأ كمفتاح Orders:ConnectionString (الشرطة المزدوجة = علامة التداخل).
/// </summary>
internal sealed class PrefixSecretManager(string prefix) : KeyVaultSecretManager
{
    public override bool Load(SecretProperties properties) =>
        properties.Name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase);

    public override string GetKey(KeyVaultSecret secret) =>
        secret.Name[(prefix.Length + 2)..].Replace("--", ConfigurationPath.KeyDelimiter);
}
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — الترتيب مهم", "filename": "src/Orders.Api/Program.cs", "code": r'''using Shop.Orders.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// ① الاعتماد أولًا (مبنيًا من البيئة — لا من سر)
var credential = AzureSecrets.BuildCredential(builder.Configuration, builder.Environment);

// ② ثم Key Vault كمصدر إعداد (قبل تسجيل أي خدمة تقرأ إعدادًا سريًا)
builder.AddVault(credential);

// ③ خيارات مُتحقَّق منها عند الإقلاع (6.1.5) — لو السر ناقص، فشل سريع وواضح
builder.Services.Configure<OrderOptions>(builder.Configuration.GetSection("Orders"))
       .ValidateDataAnnotations()
       .ValidateOnStart();

// ④ عملاء Azure بهوية واحدة
builder.Services.AddAzureServiceClients(builder.Configuration, credential);

// ⑤ قواعد البيانات بهوية Entra ID (مفيش password في connection string)
builder.Services.AddDbContext<ShopDbContext>(o =>
    o.UseSqlServer(builder.Configuration.GetConnectionString("Default")));
// ConnectionStrings:Default =
//   Server=sql-shop.database.windows.net;Database=shop;Authentication=Active Directory Default
// ← يحتاج Microsoft.Data.SqlClient + Azure.Identity، وهوية التطبيق لها دور على قاعدة البيانات.

// ⑥ مفاتيح Data Protection: ضروري عند تعدد النسخ (App Service/ACA/AKS)
builder.Services.AddDataProtection()
       .SetApplicationName("shop-orders")                 // ثابت بين النسخ والإصدارات
       .PersistKeysToAzureBlobStorage(
            new Uri($"{builder.Configuration["Azure:StorageAccountUrl"]}/dataprotection/keys.xml"),
            credential)
       .ProtectKeysWithAzureKeyVault(
            new Uri($"https://{builder.Configuration["Azure:KeyVaultName"]}.vault.azure.net/keys/dp-protect"),
            credential);

var app = builder.Build();
app.MapDefaultEndpoints();     // /health و/alive من ServiceDefaults (5.3.1)
app.Run();
'''},

        # ── 4) الأخطاء
        {"type": "heading", "level": 2, "text": "④ أخطاء بتحوّل الأمان لعطل أو لثغرة"},
        {"type": "table", "caption": "9 أخطاء شائعة في Key Vault/Managed Identity",
         "head": ["الخطأ", "النتيجة", "الصحيح"],
         "rows": [
             ["`--enable-rbac-authorization` مطفأ واستخدام access policies",
              "صلاحيات قديمة غير مدققة مركزيًا ومخالفة لتوصية Microsoft",
              "فعّل RBAC من الإنشاء واستخدم أدوار `Key Vault Secrets User/Officer`"],
             ["دور `Key Vault Secrets User` غير مُسند للهوية",
              "**403 Forbidden** عند الإقلاع — والتطبيق يفشل في القراءة",
              "`az role assignment create … --assignee-object-id <principalId>` ثم انتظر دقائق لانتشار الصلاحية"],
             ["`DefaultAzureCredential` في الإنتاج",
              "تسلسل اعتماد طويل: فشل بطيء غامض، وقد يلتقط اعتمادًا من متغيرات البيئة",
              "`ManagedIdentityCredential` صريحة (حتمية) — وسلسلة تطوير منفصلة محليًا"],
             ["إنشاء `TokenCredential`/`SecretClient` لكل طلب",
              "استنزاف التوكنات و429 من Entra ID وارتفاع زمن الاستجابة",
              "سجّلها **Singleton** (أو عبر `AddAzureClients`) وشارك كاش التوكن"],
             ["قراءة كل أسرار vault مشترك",
              "إقلاع بطيء + تسريب أسرار تطبيقات أخرى في الذاكرة",
              "`KeyVaultSecretManager` بفلترة بادئة + vault لكل تطبيق/بيئة"],
             ["`ReloadInterval = null` مع توقع تدوير حي",
              "السر الجديد ما يوصلش إلا بعد إعادة نشر/إعادة تشغيل",
              "ضع `ReloadInterval` واستخدم `IOptionsMonitor`، أو Key Vault references في App Service (تُحدَّث تلقائيًا)"],
             ["مفاتيح Data Protection محلية في تعدد النسخ",
              "كوكي/tokens من نسخة لا تُفك في أخرى: خروج عشوائي للمستخدمين و401s",
              "`PersistKeysToAzureBlobStorage` + `ProtectKeysWithAzureKeyVault` + `SetApplicationName` ثابت"],
             ["vault بلا purge protection",
              "حذف غلط (أو سكربت سيئ) = فقدان نهائي للسر وشهادات TLS",
              "`--enable-purge-protection true` + `--retention-days 90` + صلاحيات محدودة"],
             ["سر مكتوب في سطر أمر أو في سجلات CI",
              "يظهر في history/logs ويُسرَّب",
              "مرّره من stdin/ملف أو من secret مخزن في الـCI، واطبع اسمه فقط لا قيمته"],
         ]},
        {"type": "callout", "kind": "tip", "title": "افصل «إعدادات» عن «أسرار»",
         "md": "**Key Vault** للقيم السرية (كلمات سر، مفاتيح مزودين، شهادات). **App Configuration** للإعدادات العادية (قيم لكل بيئة + feature flags) مع **مراجع Key Vault** داخلها للقيم السرية. النتيجة: تطبيقك يقرأ من مصدرين واضحين، والـvault يفضل صغيرًا ومدققًا، والتدوير يبقى واضحًا. وللمشروع الشخصي: vault واحد لكل بيئة (dev/stg/prod) كافٍ تمامًا — لا تبالغ في التقسيم."},

        # ── 5) خطة
        {"type": "steps", "title": "⑤ خطة من 7 خطوات لتأمين مشروع موجود (نفّذها بالترتيب)",
         "items": [
             {"title": "1) جرد الأسرار",
              "md": "ابحث في المستودع عن كل ما يشبه سرًا: `grep -rniE \"password|secret|connectionstring|api[_-]?key\" src/ --include=*.cs --include=*.json --include=*.yml`. اكتب قائمة: الاسم · أين يُستخدم · هل يمكن استبداله بهوية؟",
              "code": "grep -rniE \"password|secret|connectionstring|api[_-]?key\" src/ --include=*.cs --include=*.json --include=*.yml | grep -v node_modules"},
             {"title": "2) احذف ما يمكن حذفه بالهوية",
              "md": "قواعد بيانات Azure SQL/PostgreSQL · Storage · Service Bus · Event Hubs · Key Vault نفسها: كلها تدعم **Entra ID auth** مع Managed Identity. كل سر تحذفه نهائيًا = خطر أقل للأبد.",
              "code": "az sql server ad-admin create --resource-group rg-shop-dev --server-name sql-shop --display-name orders-mi --object-id $PRINCIPAL_ID"},
             {"title": "3) أنشئ vault لكل بيئة بـRBAC وpurge protection",
              "md": "`kv-shop-dev` · `kv-shop-prod`. ولا تخلط بيئات في vault واحد: الصلاحيات والتدقيق والتدوير كلها تبقى ملخبطة.",
              "code": "az keyvault create --name kv-shop-prod --resource-group rg-shop-prod --location westeurope --enable-rbac-authorization true --enable-purge-protection true --retention-days 90"},
             {"title": "4) انقل الباقي للـvault وغيّر الكود",
              "md": "استخدم `PrefixSecretManager` + `ManagedIdentityCredential` في الإنتاج و`ChainedTokenCredential` محليًا. اختبر محليًا بـ`az login` و`dotnet user-secrets` للقيم غير السرية.",
              "code": "dotnet user-secrets set \"Azure:KeyVaultName\" \"kv-shop-dev\"   # اسم غير سري — آمِن في user-secrets"},
             {"title": "5) امنح الصلاحيات بأقل امتياز وتحقق",
              "md": "دور `Key Vault Secrets User` على نطاق الـvault فقط. بعد الإسناد انتظر دقائق (انتشار الصلاحيات) ثم تحقق من التطبيق بطلب `/health`.",
              "code": "az role assignment list --scope $VAULT_ID --output table"},
             {"title": "6) نظّف التاريخ والذاكرة",
              "md": "لو سر قديم اتسرب في commit سابق: **اعتبره مكشوفًا**. دوّره فورًا، واحذفه من التاريخ (`git filter-repo`) لو المستودع عام، وافحص سجلات CI. الحذف من الملف الحالي وحده لا يكفي.",
              "code": "git log -p --all -S \"$OLD_SECRET\" -- . | head -n 20   # هل السر موجود في التاريخ؟"},
             {"title": "7) فعّل التدقيق والتدوير الدوري",
              "md": "diagnostic settings لـ`AuditEvent` نحو Log Analytics + استعلام شهري «من قرأ ماذا» + خطة تدوير (90 يومًا للأسرار الخارجية، وتلقائي حيث تدعمه الخدمة).",
              "code": "AzureDiagnostics | where ResourceProvider == \"MICROSOFT.KEYVAULT\" and OperationName == \"SecretGet\" | summarize reads=count() by identity_claim_appid_s, bin(TimeGenerated, 1d)"},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف الفرق بين system-assigned وuser-assigned Managed Identity وإمتى أختار كل واحدة.",
            "أقدر أنشئ vault بـRBAC وpurge protection وأسند `Key Vault Secrets User` لهوية تطبيق.",
            "أعرف إن طريقة إيصال السر تختلف: **references** في App Service · **secrets/secretRef أو قراءة بالكود** في Container Apps · **CSI + Workload Identity** في AKS.",
            "بني `TokenCredential` حتميًا (Managed Identity في الإنتاج، سلسلة تطوير قصيرة محليًا) وسجّلته Singleton.",
            "أقدر أفلتر أسرار vault مشترك بـ`KeyVaultSecretManager` وأقرأ `Orders--X` كـ`Orders:X`.",
            "أعرف مشكلة مفاتيح Data Protection في تعدد النسخ وحلها (Blob + Key Vault + اسم تطبيق ثابت).",
            "أقدر أدوّر سرًا بدون توقف (إصدار جديد → توزيع → تحقق → إلغاء القديم) وأسترجع بعد حذف غلط.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الهوية والأسرار.",
         "questions": [
             {"q": "تطبيقك على Container Apps وبيحتاج قراءة سر من Key Vault. إيه الصح؟",
              "options": ["Key Vault reference في env vars", "إسناد Managed Identity للتطبيق + دور `Key Vault Secrets User` ثم القراءة بـAzure SDK في الكود (أو `containerapp secret set` + `secretRef`)", "وضع السر في الـimage", "`--admin-enabled true` على ACR"],
              "answer": 1,
              "explain": "مراجع `@Microsoft.KeyVault(...)` ميزة App Service/Functions، مش Container Apps. في ACA: هوية مُدارة + قراءة بالكود، أو أسرار ACA مع `secretRef`."},
             {"q": "ليه `DefaultAzureCredential` مش مثالية في الإنتاج؟",
              "options": ["لأنها بطيئة جدًا", "لأنها تجربة تسلسل اعتماد طويل: فشل غامض/بطيء، وقد تلتقط اعتمادًا غير مقصود من متغيرات البيئة؛ الأفضل `ManagedIdentityCredential` الحتمية", "لأنها لا تدعم Managed Identity", "لأنها تحتاج client secret"],
              "answer": 1,
              "explain": "توصية Microsoft: استخدم اعتمادًا حتميًا في الإنتاج. `DefaultAzureCredential` مريحة محليًا لأنها تجرّب CLI/IDE وغيرها، وده نفسه سبب الخطورة في الإنتاج."},
             {"q": "نشرت نسختين من التطبيق على AKS، والمستخدمين بيخرجوا عشوائيًا وبييجي لهم 401. السبب الأرجح؟",
              "options": ["الـHPA", "مفاتيح Data Protection مخزنة محليًا في كل Pod → كل نسخة بتشفّر بمفاتيح مختلفة", "الـIngress", "مشكلة DNS"],
              "answer": 1,
              "explain": "الحل: `PersistKeysToAzureBlobStorage` (تخزين مشترك) + `ProtectKeysWithAzureKeyVault` (حماية المفاتيح) + `SetApplicationName` ثابت. نفس المنطق ينطبق على ACA/App Service متعدد النسخ."},
             {"q": "في AKS، إيه اللي بيربط Pod بهوية Azure من غير سر مخزّن؟",
              "options": ["Kubernetes Secret فيه client secret", "ServiceAccount + تسمية `azure.workload.identity/use: \"true\"` + federated credential على هوية user-assigned (Workload Identity)", "Pod Identity (المهجور)", "`useVMManagedIdentity: true`"],
              "answer": 1,
              "explain": "Workload Identity هو المسار الموصى به:الـfederated credential بيربط الهوية بالـServiceAccount، والتسمية بتخلي webhook يحقن التوكن. Pod Identity مهجور، و`useVMManagedIdentity` بيستخدم هوية الـnode (صلاحية أوسع من المطلوب)."},
             {"q": "عندك vault مشترك بين 4 تطبيقات. إيه الخطأ الأخطر؟",
              "options": ["استخدام `KeyVaultSecretManager` بفلترة بادئة", "إسناد دور القراءة لكل التطبيقات على نطاق الـvault **بدون فلترة** فتقرأ أسرار بعضها", "إنشاء vault لكل بيئة", "تفعيل purge protection"],
              "answer": 1,
              "explain": "أقل امتياز معناه: كل تطبيق يقرأ أسراره فقط. الفلترة بالبادئة (`Orders--…`) بتقلل السطح وبتسرع الإقلاع. الأفضل: vault لكل تطبيق/بيئة."},
             {"q": "دوّرت سر قاعدة البيانات في Key Vault لكن التطبيق لسه بيستخدم القديم. ليه؟",
              "options": ["Key Vault بيخزّن نسخة مؤقتة", "لأن `AzureKeyVaultConfigurationOptions.ReloadInterval` الافتراضي `null` (بلا إعادة تحميل) — ومحتاج إعادة تشغيل/نشر، أو استخدم مراجع App Service اللي بتُحدَّث تلقائيًا", "لأن الـRBAC بطيء", "لأن السر الجديد في إصدار مختلف"],
              "answer": 1,
              "explain": "بدون `ReloadInterval` القيمة تُقرأ مرة واحدة عند الإقلاع. الحلول: ضع مدة إعادة تحميل + `IOptionsMonitor`، أو `rollout restart`، أو (في App Service) مراجع Key Vault اللي بتُحدَّث عند التدوير."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "من «سر في ملف» إلى «هوية + vault + تدوير موثّق».",
         "items": [
             {"id": "t1", "title": "مهمة 1: إزالة كل الأسرار من تطبيقك واستبدالها بهوية",
              "md": "**السياق:** `Orders.Api` فيه connection string بكلمة سر في `appsettings.json`، ومفتاح مزوّد بريد في متغير بيئة، وACR بـ`admin-enabled true`.\n\n**المطلوب:**\n1. اكتب **جردًا** في `docs/secrets-inventory.md`: كل سر · مكانه · تصنيفه (سري/غير سري) · القرار (استبدال بهوية / نقل للvault / إبقاؤه في App Configuration).\n2. أنشئ vault بـRBAC + purge protection + `retention-days 90`، وانقل إليه ما لا يمكن استبداله بهوية.\n3. فعّل Managed Identity للتطبيق وأسند **`Key Vault Secrets User`** على نطاق الـvault فقط.\n4. عدّل الكود: `BuildCredential` حتمي (Managed Identity في الإنتاج / سلسلة تطوير قصيرة محليًا) + `AddAzureKeyVault` مع `PrefixSecretManager(Orders)` ببادئة التطبيق + `ReloadInterval`.\n5. استبدل مصادقة قاعدة البيانات بـEntra ID (`Authentication=Active Directory Default`) واحذف كلمة السر نهائيًا، وأوقف `admin-enabled` على ACR واستخدم دور `AcrPull`.\n6. **أدلة**: لقطة/مخرجات تثبت (أ) `appsettings.json` بلا أي سر (ب) `az role assignment list` على نطاق الـvault (ج) طلب `/health` ناجح بعد التغيير (د) `grep` على المستودع لا يجد سرًا قديمًا.\n7. اكتب `docs/secret-rotation.md`: خطوات التدوير بدون توقف + من المسؤول + كيف تتحقق.",
              "criteria": [
                  "جرد كامل ومصنّف، وكل بند فيه قرار (مش قائمة بلا نهاية).",
                  "vault بـRBAC + purge protection مفعّلين فعليًا (موثق بالأمر).",
                  "الدور المُسند هو `Key Vault Secrets User` **على نطاق الـvault** (مش Contributor/Owner على المجموعة).",
                  "الكود يستخدم `ManagedIdentityCredential` في الإنتاج وسلسلة تطوير قصيرة محليًا — و`TokenCredential` مسجّل كـSingleton.",
                  "فلترة بالبادئة (`PrefixSecretManager` ببادئة `Orders`) مع تحويل `--` إلى مفاتيح متداخلة، ومُختبَر بقراءة قيمة فعلية.",
                  "قاعدة البيانات بـEntra ID auth وبلا كلمة سر، وACR بلا admin password (دور `AcrPull`).",
                  "الأدلة الأربعة موجودة، و`grep` النهائي نظيف.",
                  "`docs/secret-rotation.md` بخطوات قابلة للتنفيذ (إصدار جديد → توزيع → تحقق → إلغاء القديم) وبخطة للسر المسرَّب في تاريخ Git.",
              ],
              "hint": "ابدأ بالأصعب: قاعدة البيانات. `az sql server ad-admin create` بيضيف مدير Entra ID للخادم، وبعدها أنشئ user في القاعدة للهوية (`CREATE USER [orders-mi] FROM EXTERNAL PROVIDER`) ومنحه الدور المطلوب (`ALTER ROLE db_datareader/db_datawriter ADD MEMBER …`). لو دي قاعدة PostgreSQL، فعّل مصادقة Entra من إعدادات الخادم واستخدم حزمة المصادقة المناسبة لإصدار Npgsql — تحقق من التوثيق لأن الأسماء بتتغير.",
              "solution": "الترتيب العملي: (1) جرد (2) إنشاء vault وتفعيل purge protection (3) إسناد هوية للتطبيق + دور قراءة (4) إنشاء admin Entra ID على خادم SQL + user في القاعدة + أدوار (5) تغيير connection string إلى `Authentication=Active Directory Default` وحذف كلمة السر (6) تعديل `Program.cs` بالاعتماد الحتمي و`PrefixSecretManager` (7) نشر لبيئة staging والتحقق من `/health` و`/orders` (8) إلغاء `admin-enabled` على ACR وإسناد `AcrPull` (9) تدوير مفتاح البريد المخزّن وحذفه من تاريخ Git لو لزم (10) كتابة runbook التدوير. أهم نتيجة: **عدد الأسرار في التطبيق ينقص** — كل سر مستبدل بهوية هو خطر مُزال للأبد، مش خطر مُدار.",
              "resources": [
                  "https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration",
                  "https://learn.microsoft.com/en-us/dotnet/azure/sdk/authentication/best-practices",
                  "https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide",
                  "https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices",
                  "https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-configure",
                  "https://learn.microsoft.com/en-us/azure/container-registry/tutorial-kubernetes-managed-identity",
              ]},
             {"id": "t2", "title": "مهمة 2: أسرار AKS عبر CSI + Workload Identity (أو بديل محلي)",
              "md": "**السياق:** لو عندك cluster (AKS أو kind محلي) عايز توصّل أسرار Key Vault للـPods من غير Kubernetes Secrets مكتوبة يدويًا.\n\n**المطلوب:**\n1. على AKS: فعّل `azure-keyvault-secrets-provider` و`--enable-workload-identity`، أنشئ هوية user-assigned + `federated-credential` مربوط بـ`system:serviceaccount:shop:orders-sa`.\n2. اكتب `SecretProviderClass` يجلب سرين وشهادة، مع `secretObjects` للمزامنة كـKubernetes Secret، و`Deployment` فيه التسمية `azure.workload.identity/use: \"true\"` وتركيب الـvolume.\n3. **أدلة فشل ونجاح متعمدة**: احذف التسمية → وثّق رسالة الخطأ؛ أرجعها → وثّق إن السر وصل (`printenv`/ملف في `/mnt/secrets-store`).\n4. فعّل تدوير الأسرار (rotation) في الـdriver ووثّق كيف تتحقق إن القيمة اتحدثت في الـPod بدون إعادة نشر.\n5. لو مفيش AKS متاح: طبّق نفس المنطق محليًا بـExternal Secrets Operator أو بـSOPS+age (6.1.5) واكتب مقارنة من 6 أسطر: **الأمان · التدوير · التعقيد · الاعتماد على Azure · قابلية النقل · التدقيق**.\n6. أضف فحصًا في CI (`scripts/check-no-plaintext-secrets.sh`) يفشل لو ظهر `stringData:` بقيمة حقيقية أو `password=` في ملفات k8s.",
              "criteria": [
                  "الـmanifests كاملة وتُطبَّق بنجاح (أو بديل محلي مكافئ مع مقارنة).",
                  "الهوية مرتبطة بـfederated credential بالموضوع الصحيح `system:serviceaccount:<ns>:<sa>`.",
                  "تجربة فشل متعمدة موثقة (حذف التسمية) + تجربة نجاح (السر وصل).",
                  "التدوير مفعّل ومُختبَر: القيمة الجديدة ظهرت في الـPod **بدون إعادة نشر** (أو وثّقت الحد الزمني للمزامنة).",
                  "مقارنة (لو استخدمت بديلًا محليًا) بمحاور محددة وبتوصية صريحة.",
                  "فحص CI بيمنع الأسرار المكتوبة نصًا في manifests وبيفشل البناء.",
                  "ملاحظة صريحة عن حد الـfederated credentials لكل هوية وعن خيار AKS Identity Binding الأحدث.",
              ],
              "hint": "أشهر فشل: `azure.workload.identity/use: \"true\"` ناقصة، أو الـ`subject` في الـfederated credential فيه namespace/sa غلط، أو الدور مُسند لـclientId بدل principalId. للتحقق السريع: `kubectl -n shop describe pod` وابحث عن أخطاء تركيب الـCSI volume، و`kubectl -n shop logs` للـdriver pod في namespace `kube-system`.",
              "solution": "الترتيب: (1) `az aks update --enable-oidc-issuer --enable-workload-identity` (2) `az identity create` + `az role assignment create --role \"Key Vault Secrets User\"` بـ**principalId** (3) `az identity federated-credential create --subject system:serviceaccount:shop:orders-sa` (4) ServiceAccount بالـannotation `azure.workload.identity/client-id` (5) `SecretProviderClass` + `secretObjects` (6) Deployment بالتسمية + `serviceAccountName` + الـvolume (7) فحص: `kubectl exec … -- cat /mnt/secrets-store/orders-conn` و`printenv ConnectionStrings__Default`. تجربة الفشل: حذف التسمية بيمنع حقن التوكن → خطأ مصادقة في logs الـdriver؛ إرجاعها + إعادة إنشاء الـPod بيحلها. التدوير: فعّل `enableSecretRotation: \"true\"` و`rotationPollInterval` في الـSecretProviderClass، دوّر السر في الـvault، وانتظر فترة الاستطلاع ثم تحقق من القيمة داخل الـPod. سكريبت CI: `grep -RnE 'password:|stringData:' k8s/ && exit 1` مع استثناء الملفات اللي قيمها من مولّد (kustomize secretGenerator).",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver",
                  "https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-identity-access",
                  "https://azure.github.io/secrets-store-csi-driver-provider-azure/docs/configurations/identity-access-modes/",
                  "https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation",
                  "https://external-secrets.io/latest/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "Key Vault configuration provider في ASP.NET Core", "url": "https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration"},
            {"label": "أفضل ممارسات المصادقة بمكتبة Azure.Identity لـ.NET", "url": "https://learn.microsoft.com/en-us/dotnet/azure/sdk/authentication/best-practices"},
            {"label": "دليل RBAC لـKey Vault", "url": "https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide"},
            {"label": "أفضل ممارسات Key Vault", "url": "https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices"},
            {"label": "Managed Identity في App Service (مراجع Key Vault)", "url": "https://learn.microsoft.com/en-us/azure/app-service/app-service-key-vault-references"},
            {"label": "Secrets Store CSI Driver على AKS", "url": "https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver"},
            {"label": "Workload Identity federation", "url": "https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation"},
            {"label": "حماية مفاتيح Data Protection بـKey Vault", "url": "https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/configuration/overview"},
            {"label": "Azure App Configuration + مراجع Key Vault", "url": "https://learn.microsoft.com/en-us/azure/azure-app-configuration/use-key-vault-references-dotnet-core"},
        ]},
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# s6-m2-l4 — بيانات Azure: SQL Database وPostgreSQL Flexible Server وStorage
# ══════════════════════════════════════════════════════════════════════════
_L4 = {
    "id": "s6-m2-l4",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "قاعدة البيانات هي أغلى بند في فاتورة مشروع صغير — وأصعب حاجة تغيّرها بعدين. في الدرس ده: **Azure SQL Database** (DTU مقابل vCore مقابل Serverless وليه DTU بيحبسك) · **PostgreSQL Flexible Server** (Burstable للتطوير، وStop/Start اللي بيوفرلك فلوس فعلًا) · **Blob Storage** للملفات · **Cosmos DB** وإمتى تستاهل · وقرارات النسخ الاحتياطي وHA والـIOPS والشبكة الخاصة. ومع كل اختيار: **رقم تقريبي وتاريخ**، لأن الأسعار بتتغير والحاسبة هي المصدر الوحيد الموثوق."},

        {"type": "terms", "title": "مصطلحات الدرس", "items": [
            {"term": "DTU", "def": "وحدة مجمّعة (CPU + ذاكرة + I/O) في Azure SQL Database: Basic/Standard/Premium. بسيطة، لكن **غير مؤهلة للـreservations أو Hybrid Benefit أو Savings Plans** — يعني محبوس في السعر الكامل."},
            {"term": "vCore", "def": "نموذج Azure SQL الحديث: تشتري vCores وتخزينًا منفصلًا (General Purpose / Business Critical / Hyperscale). مؤهل للـreservations والتوفير."},
            {"term": "Serverless (SQL)", "def": "vCore بفوترة للثانية مع **auto-pause** بعد خمول: توفير حقيقي لأحمال متقطعة — وثمنه زمن استئناف (ثوانٍ) عند أول طلب."},
            {"term": "Flexible Server (PostgreSQL)", "def": "PostgreSQL مُدار بثلاث طبقات حوسبة: **Burstable** (B-series، الأرخص، للتطوير/حمل خفيف) · **General Purpose** (Ddsv5) · **Memory Optimized** (Edsv5)."},
            {"term": "Stop/Start", "def": "في Flexible Server: إيقاف الخادم يوقف فوترة الحوسبة (التخزين يستمر) و**يعيد التشغيل تلقائيًا بعد 7 أيام** — مثالي لبيئات التطوير."},
            {"term": "Zone-redundant HA", "def": "نسخة احتياطية في منطقة توافر أخرى مع failover تلقائي — **بتضاعف تكلفة الحوسبة تقريبًا**. قرارك: هل التطبيق يتحمل دقائق توقف؟"},
            {"term": "PITR", "def": "نسخ احتياطي بنقطة زمنية (Point-In-Time Restore). ضمن حدود حجم البيانات مجاني؛ ما زاد يُحسب (تقريبيًا ~0.12 دولار/GB شهريًا LRS — تحقق)."},
            {"term": "IOPS", "def": "عدد عمليات الإدخال/الإخراج في الثانية. في Flexible Server فيه IOPS ضمن التخزين وإمكانية شراء إضافية؛ اختناق IOPS بيظهر كـlatency عالي رغم CPU منخفض."},
            {"term": "Blob tiers + Lifecycle", "def": "Hot (متكرر الوصول) · Cool · Archive (نادر، استرجاعه بطيء ومكلف). سياسة دورة حياة بتنقل الملفات تلقائيًا حسب العمر."},
            {"term": "Cosmos DB RU/s", "def": "وحدات الطلب/الثانية: سعة تشتريها (provisioned) أو autoscale. **partition key** هو أهم قرار تصميم — اختيار غلط = hot partition وأداء سيئ."},
            {"term": "Private endpoint", "def": "ربط الخدمة بشبكتك الافتراضية بعنوان خاص، فتُلغى الإتاحة العامة — أمان أفضل وتكلفة شبكة إضافية."},
        ]},

        # ── 1
        {"type": "heading", "level": 2, "text": "① خريطة الاختيار: أي خدمة لأي حاجة"},
        {"type": "table", "caption": "الأرقام **تقديرية بأكتوبر 2026 لمنطقة غرب أوروبا** — استخدم الحاسبة دائمًا قبل الالتزام",
         "head": ["الخدمة", "نموذج الفوترة", "الحد الأدنى التقريبي", "إمتى تختارها", "إمتى لا"],
         "rows": [
             ["Azure SQL Database (DTU Basic/S0)", "حزمة DTU شهرية", "~5 دولار (Basic 5 DTU) · ~15 دولار (S0)",
              "تجربة سريعة، قاعدة صغيرة جدًا، أو ترحيل من SQL Server بمقاس مألوف",
              "إنتاج جاد: **بلا reservations ولا Hybrid Benefit** → سعر كامل للأبد"],
             ["Azure SQL Database (vCore General Purpose)", "لكل vCore-hour + تخزين/GB + backup", "vCore واحد ~180 دولار/شهر (تقديري) — قابل للتوفير بالحجز",
              "إنتاج SQL Server مستقر، تحتاج تحكمًا في الحوسبة/التخزين وخصومات",
              "مشروع شخصي بحمل خفيف (مكلف مقابل Burstable)"],
             ["Azure SQL Database **Serverless**", "لكل ثانية vCore + auto-pause", "منخفض جدًا مع الخمول (الحوسبة تتوقف)",
              "حمل متقطع/غير متوقع (dev/staging، تطبيق بموجات)",
              "latency حساس: الاستئناف بعد السكون يستغرق ثوانٍ"],
             ["**PostgreSQL Flexible Server (Burstable B1ms)**", "حجم ثابت + تخزين/GB + backup", "**~12–15 دولار/شهر** (1 vCore/2 GiB)",
              "**الافتراضي لمشروع .NET شخصي/ناشئ** على PostgreSQL — أرخص بداية حقيقية",
              "حمل إنتاجي مستمر (Burstable فيه حدود CPU credits)"],
             ["PostgreSQL Flexible (General Purpose D2ds/D4ds)", "لكل vCore + تخزين + IOPS", "عشرات إلى مئات الدولارات",
              "إنتاج بحمل مستقر، تحتاج HA وread replicas",
              "تطوير/تجربة (HA تضاعف التكلفة)"],
             ["Blob Storage", "لكل GB حسب الطبقة + عمليات + egress", "قروش لأول GBs؛ أول ~100 GB egress شهريًا مجاني",
              "رفع ملفات المستخدمين: صور المنتجات، فواتير PDF، نسخ احتياطية، Data Protection keys",
              "استعلامات علائقية أو معاملات"],
             ["Cosmos DB", "RU/s (provisioned أو autoscale) + تخزين", "منخفض مع autoscale/minimal؛ يرتفع بسرعة مع RU",
              "حجم ضخم + latency منخفض عالميًا + نموذج بيانات وثائقي واضح",
              "استعلامات علائقية معقدة/joins ومعاملات عبر كيانات (EF Core provider محدود)"],
             ["Azure Database for Redis (Managed)", "لكل طبقة/حجم", "عشرات الدولارات",
              "cache/جلسات/طوابير خفيفة مُدارة",
              "تطوير محلي (استخدم Redis في Docker/Compose — 6.1.2)"],
         ]},
        {"type": "callout", "kind": "tip", "title": "توصية عملية لمشروع شخصي بميزانية محدودة",
         "md": "**PostgreSQL Flexible Server بـBurstable B1ms (~12–15 دولار/شهر) + Blob Storage + Container Apps Consumption** = نظام كامل بعشرات الدولارات شهريًا، وأغلبه داخل المنح المجانية في الشهور الأولى. و**أوقف خادم التطوير** في الليل/الويكند (`az postgres flexible-server stop`) — لكن تذكر إنه **بيعيد التشغيل تلقائيًا بعد 7 أيام**، فجدول إيقاف أسبوعي أفضل من الاعتماد على الإيقاف اليدوي."},

        # ── 2) SQL
        {"type": "heading", "level": 2, "text": "② Azure SQL Database: القرار اللي بيحبسك (DTU مقابل vCore)"},
        {"type": "table", "caption": "مقارنة نماذج الشراء في Azure SQL",
         "head": ["", "DTU (Basic/Standard/Premium)", "vCore Provisioned", "vCore Serverless"],
         "rows": [
             ["وحدة الفوترة", "DTUs مجمّعة", "vCores لكل ساعة", "vCores لكل ثانية (+ auto-pause)"],
             ["التخزين", "ضمن الطبقة", "منفصل (لكل GB)", "منفصل (لكل GB)"],
             ["**Reserved capacity**", "**✗ غير مؤهل**", "✓ (سنة/3 سنوات — يغطي الحوسبة فقط)", "✗"],
             ["**Hybrid Benefit**", "**✗**", "✓ (لو عندك تراخيص SQL Server بـSoftware Assurance)", "✗"],
             ["**Savings Plan for Databases** (من مارس 2026)", "**✗**", "✓", "✓ (حتى ~35%)"],
             ["الحد الأدنى التقريبي", "~5 دولار/شهر", "مئات الدولارات (2 vCore GP)", "~منخفض مع السكون"],
             ["المرونة", "منخفضة (طبقات ثابتة)", "عالية (غيّر vCores/التخزين)", "الأعلى (يتوسع وينزل تلقائيًا)"],
             ["الأنسب", "تجربة/قاعدة صغيرة جدًا", "إنتاج مستقر ومعروف الحجم", "أحمال متقطعة + dev/staging"],
         ]},
        {"type": "callout", "kind": "warn", "title": "التفاصيل اللي بتوقع الناس",
         "md": "**① الـreservation يغطي الحوسبة فقط**: التخزين والنسخ الاحتياطي والشبكة والترخيص (لو مش Hybrid Benefit) بيفضلوا بسعر PAYG. **② الخادم مقابل القاعدة**: في Azure SQL انت بتدفع لكل **قاعدة بيانات** (أو elastic pool) — عشر قواعد صغيرة = عشر فواتير. الحل للمشروع الصغير: **قاعدة واحدة بمخططات (schemas)** أو **elastic pool** لو الأحمال متبادلة. **③ auto-pause في Serverless**: الاستئناف بيستغرق ثوانٍ، فلو أول طلب من مستخدم حقيقي، ده latency ملحوظ — خليه لـdev/staging. **④ النسخ الاحتياطي**: PITR ضمن حد حجم البيانات مجاني، والزيادة تُحسب؛ احتفظ بمدة احتفاظ قصيرة (7 أيام) لبيئات التطوير."},
        {"type": "code", "lang": "bash", "title": "azure/50-data.sh — إنشاء وقواعد تشغيلية", "filename": "azure/50-data.sh", "code": r'''#!/usr/bin/env bash
set -euo pipefail
LOC=westeurope; RG=rg-shop-dev; SUB=$(az account show --query id -o tsv)

# ═══════════ المسار أ) PostgreSQL Flexible Server (الافتراضي لمشروع صغير) ═══════════
# Burstable B1ms: أرخص بداية حقيقية. بدون HA للتطوير.
# ⚠ إصدار PostgreSQL المدعوم بيتغير: تحقق بـ az postgres flexible-server list-skus
az postgres flexible-server create \
  --resource-group "$RG" --name pg-shop-dev --location "$LOC" \
  --tier Burstable --sku-name Standard_B1ms \
  --storage-size 32 --backup-retention 7 \
  --version 17 \
  --public-access 0.0.0.0/0     # للتطوير فقط — للإنتاج: private endpoint/VNet
# ⚠ تحقق من إصدار PostgreSQL المدعوم حاليًا:  az postgres flexible-server list-skus -l $LOC

# توفير فعلي: أوقف خادم التطوير (الحوسبة تتوقف، التخزين يستمر)
az postgres flexible-server stop  --name pg-shop-dev --resource-group "$RG"
az postgres flexible-server start --name pg-shop-dev --resource-group "$RG"
# ⚠ الخادم الموقوف يُعاد تشغيله تلقائيًا بعد 7 أيام → جدول أسبوعي (CI/Logic App/func timer)

# مصادقة Entra ID بدل كلمة السر (الدرس 6.2.3):
az postgres flexible-server ad-admin create --resource-group "$RG" \
  --server-name pg-shop-dev --display-name you@example.com --object-id "$MY_OBJECT_ID"
# PgBouncer مدمج: فعّله لتقليل اتصالات EF Core الكثيرة
az postgres flexible-server parameter set --resource-group "$RG" --server-name pg-shop-dev \
  --name pgbouncer.enabled --value true

# ═══════════ المسار ب) Azure SQL Database ═══════════
az sql server create --resource-group "$RG" --name sql-shop-dev --location "$LOC" \
  --admin-user sqladmin --admin-password "$SQL_ADMIN_PASSWORD"   # ثم عطّل الوصول بكلمة السر
az sql server ad-admin create --resource-group "$RG" --server-name sql-shop-dev \
  --display-name orders-mi --object-id "$APP_PRINCIPAL_ID"

# Serverless مع auto-pause (dev/staging):
az sql db create --resource-group "$RG" --server sql-shop-dev --name shop \
  --edition GeneralPurpose --compute-model Serverless \
  --capacity 1 --min-capacity 0.5 --auto-pause-delay 60
# auto-pause-delay بالدقائق؛ الاستئناف بعد السكون يستغرق ثوانٍ (لا تستخدمه لحساس latency)
# vCore provisioned (إنتاج مستقر) — وبعدها اشتري reservation للحوسبة:
az sql db create --resource-group "$RG" --server sql-shop-dev --name shop \
  --edition GeneralPurpose --compute-model Provisioned --capacity 2 --storage-size 100

# قاعدة واحدة فقط للتجربة (DTU) — تذكر إنها غير مؤهلة لأي خصم:
az sql db create --resource-group "$RG" --server sql-shop-dev --name shop-dtu \
  --service-objective Basic

# ═══════════ التخزين: Storage account + container ═══════════
az storage account create --resource-group "$RG" --name stshopdev \
  --location "$LOC" --sku Standard_LRS --kind StorageV2 \
  --min-tls-version TLS1_2 --allow-blob-public-access false --https-only true
az storage container create --name product-images --account-name stshopdev --auth-mode login

# سياسة دورة حياة: Cool بعد 30 يومًا، Archive بعد 180 (توفير تلقائي)
az storage account management-policy create --account-name stshopdev --resource-group "$RG" \
  --policy '{
    "rules": [{
      "name": "age-out",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": { "blobTypes": ["blockBlob"], "prefixMatch": ["product-images/"] },
        "actions": {
          "baseBlob": {
            "tierToCool":    { "daysAfterModificationGreaterThan": 30 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 180 },
            "delete":        { "daysAfterModificationGreaterThan": 730 }
          }
        }
      }
    }]
  }'

# ═══════════ الشبكة والأمان (للإنتاج) ═══════════
# private endpoint = لا إتاحة عامة + تكلفة شبكة إضافية:
az network private-endpoint create --name pe-pg-shop --resource-group "$RG" \
  --vnet-name vnet-shop --subnet snet-data \
  --private-connection-resource-id "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.DBforPostgreSQL/flexibleServers/pg-shop-prod" \
  --group-id postgresqlServer --connection-name pg --manual-request false 2>/dev/null || \
  echo "راجع أعلام الأمر في إصدارك: az network private-endpoint create --help"

# ═══════════ الفاتورة: وشوفها بنفسك (الدرس 6.2.5) ═══════════
az consumption usage list --query "[?contains(instanceName,'pg-shop')].{n:instanceName,cost:pretaxCost}" -o table 2>/dev/null || \
  echo "استخدم: Cost Management → Cost analysis في الـPortal (أدق وأوضح)"
'''},
        {"type": "code", "lang": "csharp", "title": "الاتصال بهوية Entra ID + حساب اتصالات الـpool", "filename": "src/Orders.Api/Infrastructure/DataAccess.cs", "code": r'''using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;
using Azure.Storage.Sas;
using Microsoft.Data.SqlClient;   // يدعم Authentication=Active Directory Default مع Azure.Identity
using Microsoft.EntityFrameworkCore;

namespace Shop.Orders.Infrastructure;

public static class DataAccess
{
    /// <summary>
    /// connection string بلا كلمة سر — الهوية المُدارة هي الاعتماد.
    /// Server=sql-shop.database.windows.net;Database=shop;Authentication=Active Directory Default
    /// </summary>
    public static void ConfigureSql(IServiceCollection services, IConfiguration cfg)
    {
        var cs = cfg.GetConnectionString("Default")
                 ?? throw new InvalidOperationException("ConnectionStrings:Default مطلوب");

        services.AddDbContextPool<ShopDbContext>(o => o.UseSqlServer(cs, sql =>
        {
            sql.EnableRetryOnFailure(maxRetryCount: 3,
                maxRetryDelay: TimeSpan.FromSeconds(4), errorNumbersToAdd: null);
            sql.CommandTimeout(15);
        }), poolSize: 8);      // ⚠ انظر حساب الـpool بالأسفل
    }

    /// <summary>
    /// حساب اتصالات قاعدة البيانات — نفس منطق 6.1.5 لكنه هنا بالأرقام:
    ///   maxReplicas × poolSize ≤ 0.8 × max_connections
    /// PostgreSQL B1ms: max_connections صغيرة (حسب الذاكرة) → pool صغير جدًا.
    /// </summary>
    public static (int PoolSize, int MaxReplicas) PlanConnections(int maxConnections, int replicas)
    {
        var budget = (int)(maxConnections * 0.8);          // اترك 20% للإدارة والصيانة
        var perReplica = Math.Max(2, budget / Math.Max(1, replicas));
        return (perReplica, replicas);
    }

    /// <summary>تحميل/رفع ملف في Blob بهوية (بلا SAS وبلا مفتاح حساب).</summary>
    public static async Task UploadProductImageAsync(
        BlobContainerClient container, string productId, Stream data, CancellationToken ct)
    {
        BlobClient blob = container.GetBlobClient($"product-images/{productId}.jpg");
        await blob.UploadAsync(data, new BlobUploadOptions
        {
            // طبقة Cool للصور القديمة تُدار بسياسة دورة الحياة، لا يدويًا
            HttpHeaders = { ContentType = "image/jpeg" },
        }, cancellationToken: ct);
    }

    /// <summary>
    /// رابط قراءة مؤقت: استخدم SAS **فقط** لما العميل خارج Azure ومحتاج وصولًا مباشرًا.
    /// البديل الأفضل: وكيل في تطبيقك يقرأ بالهوية ويبعت البايتات (تدفقًا).
    /// </summary>
    // ⚠ GenerateSasUri يتطلب عميلًا مبنيًا بمفتاح الحساب (shared key)، لا بهوية مُدارة.
    //   لو تطبيقك بالهوية فقط: اقرأ بالبديل (وكيل تدفقي) أو أصدر SAS من خدمة متخصصة.
    public static Uri CreateReadSas(BlobClient blob, TimeSpan ttl) =>
        blob.GenerateSasUri(BlobSasPermissions.Read, DateTimeOffset.UtcNow.Add(ttl));
}
'''},

        # ── 3) قرارات التشغيل
        {"type": "heading", "level": 2, "text": "③ قرارات التشغيل: HA · النسخ الاحتياطي · الشبكة · الترحيل"},
        {"type": "table", "caption": "قرارات لازم تتحسم بدري (تغييرها لاحقًا مكلف)",
         "head": ["القرار", "الخيارات", "التكلفة التقريبية", "التوصية لمشروع صغير"],
         "rows": [
             ["HA (توافر عالي)", "بدون · Zone-redundant (PostgreSQL) · Business Critical (SQL)",
              "**~2× الحوسبة** للـzone-redundant",
              "بدون HA في dev/staging · وHA في الإنتاج فقط لو توقف دقائق = خسارة حقيقية"],
             ["مدة الاحتفاظ بالنسخ", "7 · 14 · 35 يومًا", "زيادة التخزين فوق الحد المجاني تُحسب",
              "7 أيام للتطوير · 30–35 للإنتاج (مع اختبار استرجاع فعلي مرة كل ربع سنة)"],
             ["الشبكة", "عام مع جدار ناري · VNet + private endpoint",
              "private endpoint + معالجة بيانات إضافية",
              "dev: عام مع تقييد IP · prod: private endpoint + تعطيل الوصول العام"],
             ["المصادقة", "كلمة سر · Entra ID (هوية مُدارة)", "بلا تكلفة إضافية",
              "**Entra ID دائمًا** — يلغي سرًا كاملًا من النظام (6.2.3)"],
             ["تخزين الملفات", "داخل القاعدة (BLOB) · Blob Storage",
              "Blob أرخص بكثير ويسهل توزيعه بـCDN",
              "Blob Storage + سياسة دورة حياة + CDN للصور العامة"],
             ["عدد القواعد", "قاعدة لكل خدمة · قاعدة واحدة بمخططات · elastic pool",
              "كل قاعدة = فاتورة حوسبة مستقلة",
              "قاعدة واحدة بمخططات (modular monolith — 4.2) حتى يثبت العكس"],
             ["IOPS", "ضمن التخزين · إضافي", "الإضافي يُحسب لكل IOPS",
              "ابدأ بالضمني، وقِس (3.1.1) قبل الشراء — الاختناق الحقيقي غالبًا استعلامات لا IOPS"],
         ]},
        {"type": "callout", "kind": "danger", "title": "ثلاثة أخطاء بتكلّف فلوس فعلًا",
         "md": "**① HA على بيئة تطوير**: مضاعفة الحوسبة مقابل لا شيء. **② قواعد بيانات متعددة مبكرًا**: كل قاعدة بفاتورة حوسبة مستقلة، وانت لسه في modular monolith. **③ نسيان الموارد بعد التجربة**: خادم PostgreSQL أو SQL Database أو Container App environment بيفضل شغالًا وبيتفوتر — **احذف مجموعة الموارد كاملة** بعد كل تجربة (`az group delete -n rg-experiment --no-wait`). والأهم: **Azure ما بيوقفش الموارد تلقائيًا عند تجاوز الميزانية** — فيه تنبيهات بس (6.2.5)."},

        {"type": "steps", "title": "④ خطوات نقل قاعدة بيانات محلية إلى Azure",
         "items": [
             {"title": "1) قِس قبل ما تشتري",
              "md": "من درس 3.1.1 و5.4: حجم البيانات · عدد الاستعلامات/ثانية · أبطأ 5 استعلامات · حجم اتصال الـpool الفعلي. الأرقام دي هي اللي بتحدد SKU، مش التخمين.",
              "code": "SELECT pg_size_pretty(pg_database_size(current_database()));\nSELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"},
             {"title": "2) اختار الخدمة والطبقة بحساب",
              "md": "PostgreSQL → Flexible Burstable (dev) ثم General Purpose (prod). SQL Server → Serverless (dev) ثم vCore GP مع reservation (prod). وثّق القرار في ADR مع الأرقام والتاريخ.",
              "code": "az postgres flexible-server list-skus --location westeurope --output table"},
             {"title": "3) صدّر البيانات",
              "md": "PostgreSQL: `pg_dump` بصيغة مخصصة. SQL Server: bacpac عبر Azure Data Studio أو `sqlpackage`. الملفات الكبيرة → ارفعها لـBlob أولًا ثم استوردها.",
              "code": "pg_dump -Fc -h localhost -U shop -d shop -f shop.dump\n# أو: sqlpackage /a:Export /sf:shop.bacpac /tsn:localhost /tdn:shop"},
             {"title": "4) أنشئ الهدف بمصادقة Entra ID",
              "md": "أنشئ الخادم/القاعدة، أضف admin Entra ID، أسند الهوية المُدارة، واختبر الاتصال من بيئة النشر (لا من جهازك) — عشان تتأكد من قواعد الشبكة.",
              "code": "az postgres flexible-server ad-admin create -g rg-shop-prod -s pg-shop-prod --display-name deploy-mi --object-id $PRINCIPAL_ID"},
             {"title": "5) استورد وتحقق من العدد والقيود",
              "md": "استورد، ثم قارن: عدد الصفوف لكل جدول · الفهارس · الـconstraints · التسلسلات (sequences) · وخطط الصلاحيات. الترحيل الناقص بيبان بعد أسابيع مش فورًا.",
              "code": "psql \"$PROD_DSN\" -c '\\dt+' -c 'SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10;'"},
             {"title": "6) شغّل migrations EF Core في CI (نمط 6.1.2)",
              "md": "بنفس مبدأ job الـmigrations one-shot: `dotnet ef database update` في pipeline قبل نشر النسخة الجديدة، وبفحص سابق (3.5) للتوسيع/التضييق.",
              "code": "dotnet ef database update --project src/Orders.Infrastructure --startup-project src/Orders.Api --connection \"$PROD_DSN\""},
             {"title": "7) بدّل الحركة وتحقق ثم احذف القديم",
              "md": "نافذة توقف قصيرة أو نسخ مزدوج للكتابة (حسب حجمك). تحقق من p95 وأخطاء الاتصال (2.3.4)، واحتفظ بالمصدر القديم 7 أيام قبل الحذف.",
              "code": "kubectl -n shop set env deploy/orders ConnectionStrings__Default=\"$NEW_DSN\" && kubectl -n shop rollout status deploy/orders"},
         ]},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "أعرف إن DTU **غير مؤهل** للـreservations/Hybrid Benefit/Savings Plans، وده سبب كافي لتجنبه في الإنتاج.",
            "أقدر أختار بين SQL Serverless وvCore provisioned وPostgreSQL Burstable حسب نمط الحمل (متقطع/مستقر/تطوير).",
            "عارف إن **PostgreSQL Flexible Burstable B1ms** هو أرخص بداية حقيقية (~12–15 دولار/شهر تقديريًا).",
            "أستخدم Stop/Start لخادم التطوير، وعارف حد **إعادة التشغيل التلقائي بعد 7 أيام**.",
            "أقدر أتصل بهوية Entra ID (بلا كلمة سر) في SQL وأفعّل مصادقة Entra في PostgreSQL.",
            "أحسب اتصالات الـpool مقابل `max_connections` وعدد النسخ (0.8 × الحد).",
            "أعرف خيارات Blob (طبقات + دورة حياة + SAS مقابل وكيل) ومتى Cosmos DB يستاهل فعلًا.",
            "أقدر أرحّل قاعدة محلية إلى Azure بسبع خطوات مع تحقق من الأعداد والقيود.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "6 أسئلة على الاختيار والتكلفة والتشغيل.",
         "questions": [
             {"q": "مشروع .NET شخصي على PostgreSQL، حمل خفيف، ميزانية محدودة. البداية الصح؟",
              "options": ["Azure SQL Business Critical", "PostgreSQL Flexible Server بـ**Burstable B1ms** (~12–15 دولار/شهر) بلا HA", "Cosmos DB بـautoscale", "SQL Database vCore 2 cores"],
              "answer": 1,
              "explain": "Burstable هو الأرخص فعليًا للبداية، وبلا HA (اللي بيضاعف الحوسبة). ارفعه لـGeneral Purpose لما يثبت الحمل — التغيير سهل نسبيًا مقارنة بنقل قاعدة بين خدمات مختلفة."},
             {"q": "ليه DTU اختيار سيئ لإنتاج جاد؟",
              "options": ["بطيء", "**غير مؤهل للـreserved capacity ولا Hybrid Benefit ولا Savings Plans** — تدفع السعر الكامل للأبد ومرونته محدودة", "لا يدعم التخزين", "لا يدعم النسخ الاحتياطي"],
              "answer": 1,
              "explain": "DTU مناسبة لتجربة سريعة أو قاعدة صغيرة جدًا. للإنتاج: vCore (provisioned مع reservation) أو Serverless (مع Savings Plan for Databases للأحمال المتقطعة)."},
             {"q": "SQL Serverless مع auto-pause. إيه الثمن؟",
              "options": ["لا يوجد ثمن", "زمن استئناف (ثوانٍ) عند أول طلب بعد السكون → latency ملحوظ للمستخدم الأول", "فقدان بيانات", "عدم دعم النسخ الاحتياطي"],
              "answer": 1,
              "explain": "التوفير حقيقي للأحمال المتقطعة وبيئات dev/staging. للإنتاج الحساس للـlatency: عطل auto-pause أو استخدم provisioned مع min capacity."},
             {"q": "أوقفت خادم PostgreSQL Flexible للتطوير. إيه اللي لازم تعرفه؟",
              "options": ["هيفضل موقوف للأبد", "**يُعاد تشغيله تلقائيًا بعد 7 أيام** (والتخزين بيتفوتر طول الوقت) — فجدول إيقاف دوري أفضل", "البيانات بتتمسح", "الحوسبة بتستمر في الفوترة"],
              "answer": 1,
              "explain": "الإيقاف يوقف فوترة الحوسبة فقط، والخزنة تستمر. الاعتماد على الإيقاف اليدوي بيفشل؛ استخدم وظيفة مجدولة (6.2.2) أو CI schedule."},
             {"q": "10 نسخ من التطبيق، و`max_connections` = 100. إيه حجم الـpool الآمن لكل نسخة؟",
              "options": ["10", "**8** (0.8 × 100 = 80 ميزانية ÷ 10 نسخ = 8 لكل نسخة)", "20", "100"],
              "answer": 1,
              "explain": "القاعدة من 6.1.5: `maxReplicas × pool ≤ 0.8 × max_connections`. تجاوزها بيسبب رفض اتصالات تحت التوسع — وهي مشكلة بتظهر في الذروة فقط (أصعب وقت)."},
             {"q": "الصور بتتراكم في Blob Storage. إزاي تقلل التكلفة من غير كود؟",
              "options": ["احذفها يدويًا", "**سياسة دورة حياة**: Cool بعد 30 يومًا، Archive بعد 180، حذف بعد 730", "انقلها لقاعدة البيانات", "غيّر المنطقة"],
              "answer": 1,
              "explain": "الطبقات الأرخص (Cool/Archive) مقابل latency استرجاع أعلى. سياسة دورة الحياة بتنفذ ده تلقائيًا حسب عمر الملف — وانتبه إن Archive استرجاعه بطيء ومكلف فاحسب نمط الوصول أولًا."},
         ]},

        {"type": "tasks", "title": "مهمتان", "intro": "اختيار موثّق بالأرقام + ترحيل فعلي.",
         "items": [
             {"id": "t1", "title": "مهمة 1: قرار قاعدة بيانات موثّق بالأرقام (ADR + جدول تكلفة)",
              "md": "**السياق:** تطبيقك (من مشروع المرحلة 5) محتاج قاعدة بيانات على Azure. الحمل المتوقع: 20 مستخدمًا نشطًا، ~500 طلب/ساعة في الذروة، بيانات ~2 GB تنمو 200 MB شهريًا.\n\n**المطلوب:**\n1. `docs/adr/0015-azure-data-store.md`: القرار · السياق · **3 بدائل مقيّمة بالأرقام** (PostgreSQL Flexible Burstable / SQL Serverless / SQL vCore GP) · العواقب · إشارة المراجعة.\n2. `docs/azure-data-cost.md`: جدول تكلفة شهري تقديري لكل بديل من [الحاسبة](https://azure.microsoft.com/en-us/pricing/calculator/) — **مع ذكر التاريخ والمنطقة** وتفصيل البنود (حوسبة · تخزين · نسخ احتياطي · شبكة) + ذكر أي خصم ممكن (Savings Plan for Databases / reserved capacity) ولأي بديل ينطبق.\n3. حساب اتصالات الـpool: من `max_connections` للطبقة المختارة × عدد النسخ المتوقع (1 و5) — واكتب النتيجة في الكود كـcomment وفي الوثيقة.\n4. قرار HA والنسخ الاحتياطي والشبكة (dev مقابل prod) في جدول واحد بتبرير لكل خلية.\n5. **خطة إيقاف التوفير**: كم ساعة/أسبوع هيشتغل خادم التطوير، وإيه الآلية (وظيفة مجدولة/CI schedule) — واحسب التوفير الشهري التقريبي.\n6. فقرة «إمتى نعيد التقييم»: مؤشرات (p95 latency · CPU credits · حجم البيانات · عدد المستخدمين) وعتبات رقمية.",
              "criteria": [
                  "ADR فيه 3 بدائل مقيّمة **بأرقام من الحاسبة** مع التاريخ والمنطقة (مش «تقريبًا رخيص»).",
                  "قرار صريح مرتبط بنمط الحمل (20 مستخدمًا/500 طلب ساعة/2 GB) — مش تفضيل شخصي.",
                  "جدول التكلفة مفصّل البنود ويشمل النسخ الاحتياطي والشبكة (البنود المنسية).",
                  "ذكر دقيق لما ينطبق عليه خصم: **Savings Plan for Databases** (من مارس 2026) و**reserved capacity** — وأن DTU غير مؤهل لأيٍّ منهما.",
                  "حساب الـpool بالأرقام لحالة نسخة واحدة و5 نسخ مع القاعدة `≤ 0.8 × max_connections`.",
                  "جدول قرارات HA/نسخ/شبكة لـdev وprod بتبرير لكل خلية.",
                  "خطة إيقاف بخسارة صفرية (آلية + توفير شهري تقديري) مع ذكر حد الـ7 أيام.",
                  "فقرة إعادة تقييم بعتبات رقمية (مثال: لو p95 > 300ms أو CPU credits نفدت → ارفع الطبقة).",
              ],
              "hint": "في الحاسبة: اختار «Azure Database for PostgreSQL Flexible Server» → Burstable → B1ms → 32 GB storage → backup 7 days → غرب أوروبا. وسجّل الرقم. كرّر لـ«Azure SQL Database» مع Serverless (min 0.5 vCore، max 2، auto-pause بعد 60 دقيقة) — هتلاقي الفرق كبير في السيناريو الخفيف. ولـBurstable راجع مفهوم CPU credits: الحمل المستمر بيستهلكها وبعدها الأداء بيتقلص.",
              "solution": "النتيجة المتوقعة: **PostgreSQL Flexible Burstable B1ms** يفوز للحمل ده (~12–15 دولار + تخزين/نسخ)، لأن SQL Serverless رغم السكون بيحسب لكل ثانية vCore والاستئناف بيأثر على أول طلب، وvCore GP مبالغ فيه (مئات الدولارات). القرار مع HA=لا للتطوير ونعم للإنتاج لو توقف دقائق = خسارة، والنسخ 7 أيام dev / 30 يومًا prod، والشبكة عامة مقيدة بـIP للتطوير وprivate endpoint للإنتاج، والمصادقة Entra ID في الحالتين. الـpool: لو `max_connections` ≈ 50 (B1ms حسب الذاكرة — تحقق بالأمر `SHOW max_connections`) فـ0.8 × 50 = 40؛ نسخة واحدة → pool ≤ 40 (ولكن اختر 8–10 للسلامة)؛ 5 نسخ → 8 لكل نسخة. خطة الإيقاف: تشغيل dev من 9ص إلى 7م في أيام العمل = ~50 ساعة/أسبوع بدل 168 → توفير ~70% من حوسبة التطوير. إعادة التقييم: CPU credits منخفضة باستمرار / p95 > 300ms / حجم > 20 GB / مستخدمون > 200 → ارفع لـGeneral Purpose D2ds_v5.",
              "resources": [
                  "https://azure.microsoft.com/en-us/pricing/calculator/",
                  "https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-compute-storage",
                  "https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-backup-restore",
                  "https://learn.microsoft.com/en-us/azure/azure-sql/database/purchasing-models",
                  "https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview",
                  "https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/",
              ]},
             {"id": "t2", "title": "مهمة 2: ارحّل قاعدة بياناتك المحلية إلى Azure وتحقق",
              "md": "**السياق:** عندك قاعدة PostgreSQL (أو SQL) شغالة في Docker من المرحلة 6.1.2 ومحتاج تنقلها إلى Azure بأقل توقف.\n\n**المطلوب:**\n1. أنشئ الخادم بالطبقة المختارة في المهمة 1 + مصادقة Entra ID + (اختياري) private endpoint.\n2. صدّر (`pg_dump -Fc` أو `sqlpackage`) → ارفع لـBlob → استورد في الهدف.\n3. **تحقق بالعدد**: جدول يقارن `n_live_tup`/عدد الصفوف لكل جدول قبل وبعد، + قائمة الفهارس والـconstraints والتسلسلات.\n4. شغّل `dotnet ef database update` (أو migrations) في بيئة نشر مكررة لما عملته في 6.1.2.\n5. بدّل connection string للتطبيق (من Key Vault/الهوية — 6.2.3) واعمل rollout، ثم قِس: p50/p95 قبل وبعد + عدد أخطاء الاتصال.\n6. اكتب `docs/migration-report.md`: المدة الفعلية · حجم البيانات · الأخطاء اللي ظهرت وحلها · زمن التوقف · وخطة الرجوع (rollback).\n7. **اختبار الاسترجاع**: استرجع نسخة PITR إلى خادم مؤقت وتحقق من بيانات جدول واحد — ووثّق المدة (ده اللي بيثبت إن النسخ الاحتياطي حقيقي).",
              "criteria": [
                  "الخادم منشور بمصادقة Entra ID وبلا كلمة سر في أي ملف (أو موثّق سبب وجودها مؤقتًا).",
                  "جدول مقارنة الصفوف قبل/بعد لكل جدول — **بدون فروق** (أو فروق مبررة).",
                  "الفهارس والـconstraints والتسلسلات متطابقة (مخرجات مُرفقة).",
                  "الاتصال من التطبيق تم من بيئة النشر (لا من جهازك) ونجح — دليل على صحة قواعد الشبكة.",
                  "قياس p50/p95 وأخطاء الاتصال قبل وبعد مع تفسير أي فرق (قرب المنطقة · حجم الطبقة · pool).",
                  "`docs/migration-report.md` بالأرقام الفعلية + أخطاء وحلولها + خطة رجوع قابلة للتنفيذ.",
                  "اختبار استرجاع PITR فعلي مع زمن الاسترجاع المكتوب (مش «النسخ الاحتياطي موجود»).",
                  "تنظيف: حذف الموارد المؤقتة وخادم الاسترجاع بعد الاختبار.",
              ],
              "hint": "أسرع مسار للأخطاء: قواعد جدار الحماية (خادم Azure SQL بيحتاج `az sql server firewall-rule create` أو private endpoint)، وحجم الـpool مقابل `max_connections` الصغيرة في Burstable، و`search_path`/الصلاحيات لو استخدمت مستخدمًا مختلفًا عن المالك. وللاسترجاع: `az postgres flexible-server restore --name … --restore-point-in-time …` ينشئ خادمًا جديدًا — وده هو الاختبار الحقيقي.",
              "solution": "الخطوات بالنتائج النموذجية: تصدير 2 GB يستغرق دقائق محلية، والرفع لـBlob يعتمد على سرعتك (غالبًا أطول خطوة)، والاستيراد على B1ms أبطأ من المتوقع (فكّر في إيقاف الـautovacuum مؤقتًا أو زيادة الطبقة أثناء الاستيراد ثم تخفيضها). الأخطاء الأشهر: (1) 403 من قاعدة البيانات → ناقص `ad-admin`/user من Entra (2) `too many connections` → قلّل pool أو ارفع الطبقة (3) latency أعلى من المحلي → طبيعي: الشبكة + حجم B1ms؛ تأكد إن الاستعلامات مفهرسة (3.1.1). التوقف الفعلي ممكن يبقى ~0 لو عملت نافذة قراءة فقط قصيرة + تحويل connection string. اختبار الاسترجاع: PITR لخادم مؤقت يستغرق من دقائق لعشرات الدقائق حسب الحجم — وثّق الرقم لأن ده هو RTO الحقيقي عندك. الرجوع: احتفظ بالخادم/الملف المصدر 7 أيام، والـrollback = إعادة connection string للقديم (من Key Vault بإصدار سابق).",
              "resources": [
                  "https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-migrate-dump-restore",
                  "https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-restore-server-portal",
                  "https://learn.microsoft.com/en-us/azure/azure-sql/database/database-import",
                  "https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction",
                  "https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/",
              ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": "PostgreSQL Flexible Server: الحوسبة والتخزين", "url": "https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-compute-storage"},
            {"label": "PostgreSQL Flexible Server: التسعير", "url": "https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/"},
            {"label": "Azure SQL Database: نماذج الشراء (DTU/vCore)", "url": "https://learn.microsoft.com/en-us/azure/azure-sql/database/purchasing-models"},
            {"label": "SQL Database Serverless", "url": "https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview"},
            {"label": "مصادقة Microsoft Entra مع Azure SQL", "url": "https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-configure"},
            {"label": "Blob Storage: الطبقات ودورة الحياة", "url": "https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-overview"},
            {"label": "اختيار متجر بيانات على Azure", "url": "https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/data-store-overview"},
            {"label": "Cosmos DB: اختيار partition key", "url": "https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview"},
            {"label": "حاسبة تسعير Azure", "url": "https://azure.microsoft.com/en-us/pricing/calculator/"},
        ]},
    ],
}

LESSONS_S6_F = [_L3, _L4]
