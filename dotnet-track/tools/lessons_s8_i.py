# -*- coding: utf-8 -*-
"""Stage 8 — module 2 (part I): s8-m2-l5 (لمحة MAUI وAvalonia — اختياري)."""

TODAY = "2026-10-22"

_L5 = {
    "id": "s8-m2-l5",
    "updatedAt": TODAY,
    "blocks": [
        {"type": "text", "md": "الدرس ده **اختياري** (20 دقيقة). وجوده مهم لسبب واحد: أن جزءًا من وظائف السوق (Desktop/Mobile في نقاط البيع وأدوات المخازن) بيطلب مهارة مختلفة — ولازم تعرف بسرعة: MAUI أم Avalonia أم تتجاهل الموضوع؟\n\nالدرس مش هيعلّمك UI كامل — هو **خريطة قرار** + **شاشة واحدة** تعملها في أي واحد فيهم، عشان تعرف حجم التكلفة الحقيقي قبل ما تبدأ."},
        {"type": "terms", "title": "مصطلحات", "items": [
            {"term": "MAUI", "def": ".NET Multi-platform App UI — وريث Xamarin.Forms: مشروع واحد بـC#/XAML يبني Android · iOS · Windows · **Mac Catalyst** عبر Handlers. مدعوم رسميًا من مايكروسوفت مع .NET."},
            {"term": "Avalonia", "def": "إطار UI مفتوح المصدر (MIT) يرسم بنفسه عبر **Skia** بدل أدوات النظام: Windows · macOS · **Linux (X11/Wayland)** · ونموذج WASM تجريبي. أقرب للإحساس بـWPF، وشعبيته في أدوات الـDesktop كبيرة."},
            {"term": "Uno Platform", "def": "إطار رابع بيدّعي التوافق مع WinUI API على منصات كثيرة (بما فيها الويب). خيار ثالث تستحق تعرفه اسمًا فقط في هذا الدرس."},
            {"term": "Handlers (MAUI)", "def": "الطبقة اللي بتحوّل كل عنصر تحكم مشترك (Button · Entry · CollectionView) للعنصر الأصلي في كل منصة. مشكلات المنصات بتظهر هنا غالبًا."},
            {"term": "MVVM", "def": "نمط فصل الواجهة عن المنطق: `ViewModel` بيحمل الحالة والأوامر (`ICommand`)، والـView بتربط بـBinding. نفس منطق 4.x في الويب/Blazor."},
            {"term": "CommunityToolkit.Mvvm", "def": "حزمة مولّدات كود: `[ObservableProperty]` (خاصية مربوطة تلقائيًا) و`[RelayCommand]` (أمر تلقائي) — بتقلل كود الـViewModel بشكل ضخم."},
            {"term": "Shell / Navigation", "def": "توجيه الصفحات داخل التطبيق: في MAUI `Shell` (routes + flyout + tabs) · في Avalonia `NavigationView`/`Frame` أو مكتبة مثل FluentAvalonia."},
            {"term": "Single-project + Platform folders", "def": "مشروع واحد بيستهدف منصات متعددة، وكل منصة لها مجلد `Platforms/<Android|iOS|Windows|MacCatalyst>` فيه كود خاص. الشيفرة المشتركة في الجذر."},
            {"term": "Native AOT / trimming", "def": "نشر بلا JIT لتقليل الحجم وزمن البدء — بيقلل المرونة (reflection) ويحتاج اختبارًا. مهم في تطبيقات Desktop الموزّعة."},
            {"term": "Packaging", "def": "توزيع التطبيق: MSIX/`msixbundle` (Win) · `.dmg` (macOS) · `.apk`/`.aab` (Android) · `.ipa` (iOS) · AppImage/`.deb` (Linux). كل منصة لها قواعد توقيع."},
        ]},

        # ───────────────────────────────────────────── ①
        {"type": "heading", "level": 2, "text": "① خريطة القرار: MAUI أم Avalonia أم Uno؟"},
        {"type": "table", "caption": "أكتوبر 2026 — أهم 9 معايير",
         "head": ["المعيار", "**MAUI**", "**Avalonia 11.3.x**", "**Uno 6.x**"],
         "rows": [
             ["الترخيص", "MIT (جزء من .NET)", "MIT", "Apache 2.0 + تجاري"],
             ["Windows", "✅ (WinUI 3)", "✅", "✅"],
             ["macOS", "✅ **Mac Catalyst فقط**", "✅ أصلي", "✅"],
             ["Linux", "❌ (غير مدعوم رسميًا)", "✅ **X11/Wayland**", "✅"],
             ["Mobile (iOS/Android)", "✅ ناضج", "✅ (أقل نضجًا من MAUI)", "✅"],
             ["الويب (WASM)", "❌", "🔶 تجريبي", "✅ (نقطة قوة)"],
             ["الرسم", "عناصر المنصة الأصلية (Handlers)", "Skia (رسم موحد عبر المنصات)", "WinUI-like فوق Skia"],
             ["دعم مايكروسوفت", "**رسمي وأولوية**", "مجتمع + شركة Avalonia", "شركة + مجتمع"],
             ["أفضل حالة استخدام", "تطبيق موبايل + ويندوز بفريق .NET", "**Desktop على Linux/3 منصات بإحساس WPF**", "واجهة واحدة لكل شيء بما فيها الويب"],
         ]},
        {"type": "callout", "kind": "note", "title": "خبر حالي مهم (2026)",
         "md": "مايكروسوفت وأفالونيا أعلنوا في **مارس 2026** عن تعاون لجعل **منصات Linux وWASM مدعومة عبر backend من Avalonia داخل MAUI** — لكنه **معاينة** ومستهدِف **.NET 11 GA**، مش شيء تعتمد عليه النهارده في الإنتاج.\n**معناه العملي:** لو محتاج Linux اليوم → **Avalonia**. لو محتاج موبايل بوضوح → **MAUI**. لو محتاج واجهة واحدة لكل شيء بما فيهم الويب → **Uno**.\nو**MAUI 11** بيوصل GA في نوفمبر 2026 (مع .NET 11) — وكما العادة، ابدأ بمشروع على LTS (.NET 10) لو بتشتغل جاد."},
        {"type": "table", "caption": "قرار سريع في 4 أسئلة",
         "head": ["سؤالك", "الإجابة", "القرار"],
         "rows": [
             ["محتاج Linux في الإنتاج؟", "نعم", "**Avalonia** (الوحيد المدعوم فعليًا)"],
             ["التطبيق أساسًا موبايل (iOS/Android) بأنماط منصة؟", "نعم", "**MAUI**"],
             ["Desktop Windows فقط + تكامل WinUI؟", "نعم", "MAUI أو Avalonia — شوف فريقك"],
             ["واجهة واحدة للويب والموبايل والـDesktop؟", "نعم", "**Uno** … أو **Blazor** لو التنازل عن التجربة الأصلية مقبول"],
             ["مشروعك ويب/APIs والسوق مش بيطلب Desktop؟", "نعم", "**اتخطّاه** — الوقت أحسن في s9/s10"],
         ]},
        {"type": "callout", "kind": "tip", "title": "قاعدة الأولويات",
         "md": "لو هدفك وظيفة **Backend/Full-stack .NET**، فـDesktop هو **إضافة** مش أساس. الأولوية: API + قاعدة بيانات + اختبارات + سحابة + مراقبة (المراحل 1–7)، ثم واجهة واحدة تتقنها (Blazor **أو** React)، وبعدها — لو السوق عندك بيطلب — شاشة Desktop واحدة بـAvalonia أو MAUI كـ«عيّنة قدرة»، مش منتج كامل.\n**تحذير تكلفة:** تطبيق Desktop جاد ≠ شاشة واحدة: توقيع · تحديثات · تغليف لكل نظام · اختلافات إدخال (لوحة مفاتيح/لمس) · واختبارات واجهة. ده مشروع بحد ذاته."},

        # ───────────────────────────────────────────── ②
        {"type": "heading", "level": 2, "text": "② الأساس المشترك: MVVM + DI + أوامر"},
        {"type": "code", "lang": "csharp", "title": "ViewModels/OrdersViewModel.cs — نفس الكود يشتغل في MAUI وAvalonia", "filename": "ViewModels/OrdersViewModel.cs", "code": r'''using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace Shop.Desktop.ViewModels;

/// <summary>
/// ViewModel واحد — لا يعرف شيئًا عن MAUI ولا Avalonia.
/// (نفس مبدأ فصل المنطق في Blazor/React: 8.2.2 · 8.2.3)
/// </summary>
public sealed partial class OrdersViewModel : ObservableObject
{
    private readonly IOrdersApi _api;
    private readonly ILogger<OrdersViewModel> _logger;

    public OrdersViewModel(IOrdersApi api, ILogger<OrdersViewModel> logger)
    {
        _api = api;
        _logger = logger;
    }

    // المولّد بيبني الخاصية العامة Orders + OnPropertyChanged تلقائيًا
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasOrders))]
    [NotifyPropertyChangedFor(nameof(IsEmpty))]
    [NotifyCanExecuteChangedFor(nameof(CancelCommand))]
    private IReadOnlyList<OrderDto> _orders = [];

    // حالة الشاشة: enum أفضل من 4 خصائص bool متناقضة (8.1.4)
    [ObservableProperty]
    private ViewState _state = ViewState.Loading;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasError))]
    private string? _errorMessage;

    [ObservableProperty]
    private OrderDto? _selected;

    public bool HasOrders => Orders.Count > 0;
    public bool IsEmpty => State == ViewState.Ready && Orders.Count == 0;
    public bool HasError => State == ViewState.Error;

    // الأمر بيتولد مع CanExecute + NotifyCanExecuteChanged
    [RelayCommand]
    private async Task LoadAsync(CancellationToken ct)
    {
        State = ViewState.Loading;
        ErrorMessage = null;

        try
        {
            Orders = await _api.GetOrdersAsync(ct);
            State = ViewState.Ready;
        }
        catch (OperationCanceledException) when (ct.IsCancellationRequested)
        {
            // إلغاء مقصود (المستخدم غيّر الصفحة) — لا خطأ
        }
        catch (ApiException ex)
        {
            _logger.LogWarning(ex, "فشل تحميل الطلبات: {Status}", ex.StatusCode);
            ErrorMessage = ex.StatusCode == 401
                ? "انتهت الجلسة — سجّل الدخول مرة أخرى."
                : "تعذّر تحميل الطلبات. جرّب مرة أخرى.";
            State = ViewState.Error;
        }
    }

    [RelayCommand(CanExecute = nameof(CanCancel))]
    private async Task CancelAsync(OrderDto? order, CancellationToken ct)
    {
        if (order is null) return;

        // تحديث متفائل (نفس فكرة 8.1.4 ⑤) — مع تراجع عند الفشل
        var previous = Orders;
        Orders = Orders.Select(o => o.Id == order.Id ? o with { Status = "cancelled" } : o).ToList();

        try
        {
            await _api.CancelAsync(order.Id, ct);
        }
        catch (ApiException ex)
        {
            Orders = previous;
            ErrorMessage = "تعذّر إلغاء الطلب — تم التراجع.";
            _logger.LogWarning(ex, "فشل إلغاء الطلب {OrderId}", order.Id);
        }
    }

    private bool CanCancel(OrderDto? order) =>
        order is { Status: not "cancelled" } && State == ViewState.Ready;
}

public enum ViewState { Loading, Ready, Error }

public sealed record OrderDto(string Id, string Status, decimal Total, string Currency);

public interface IOrdersApi
{
    Task<IReadOnlyList<OrderDto>> GetOrdersAsync(CancellationToken ct);
    Task CancelAsync(string id, CancellationToken ct);
}

public sealed class ApiException(string message, int statusCode) : Exception(message)
{
    public int StatusCode { get; } = statusCode;
}
'''},
        {"type": "callout", "kind": "tip", "title": "لماذا هذا الكود هو 80% من الشغل",
         "md": "**① الـViewModel قابل للاختبار بلا واجهة** — بتعمل instance بـ`IOrdersApi` موك وتتحقق من الحالات (Loading → Ready/Error، الإلغاء المتفائل، التراجع). ده اللي بيخلي تطبيقات Desktop قابلة للصيانة.\n**② المولّدات بتوفر مئات السطور** — `[ObservableProperty]` + `[RelayCommand]` بدل كتابة `INotifyPropertyChanged` يدويًا.\n**③ نفس الـViewModel يخدم MAUI وAvalonia** — الفرق في XAML والتغليف فقط. وده قرار ذكي: **لا تحبس منطقك في الـView**.\n**④ DI مشترك**: `builder.Services.AddTransient<OrdersViewModel>()` (MAUI) / `AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace()`+`Services` (Avalonia) — التسجيل نفسه تقريبًا.\n**⑤ `CancellationToken` في كل أمر** — التنقّل السريع بين الصفحات بيلغي الطلبات (نفس 8.1.2)."},
        {"type": "code", "lang": "csharp", "title": "ViewModels/OrdersViewModel.Tests.cs — اختبار الـViewModel بلا واجهة (xUnit v3 + NSubstitute)", "filename": "tests/OrdersViewModelTests.cs", "code": r'''using NSubstitute;
using Shouldly;
using Xunit;

public sealed class OrdersViewModelTests
{
    private readonly IOrdersApi _api = Substitute.For<IOrdersApi>();
    private readonly ILogger<OrdersViewModel> _logger =
        Substitute.For<ILogger<OrdersViewModel>>();

    [Fact]
    public async Task Load_SetsReadyAndOrders()
    {
        _api.GetOrdersAsync(Arg.Any<CancellationToken>())
            .Returns([new OrderDto("ORD-1", "paid", 199.99m, "EGP")]);

        var vm = new OrdersViewModel(_api, _logger);
        await vm.LoadCommand.ExecuteAsync(null);

        vm.State.ShouldBe(ViewState.Ready);
        vm.Orders.Count.ShouldBe(1);
        vm.HasOrders.ShouldBeTrue();
        vm.IsEmpty.ShouldBeFalse();
    }

    [Fact]
    public async Task Load_On401_SetsFriendlyError()
    {
        _api.GetOrdersAsync(Arg.Any<CancellationToken>())
            .Returns<IReadOnlyList<OrderDto>>(_ => throw new ApiException("unauthorized", 401));

        var vm = new OrdersViewModel(_api, _logger);
        await vm.LoadCommand.ExecuteAsync(null);

        vm.State.ShouldBe(ViewState.Error);
        vm.HasError.ShouldBeTrue();
        vm.ErrorMessage!.ShouldContain("الجلسة");   // رسالة للمستخدم، لا stack trace
    }

    [Fact]
    public async Task Cancel_Optimistic_ThenRollsBackOnFailure()
    {
        var order = new OrderDto("ORD-1", "paid", 10m, "EGP");
        _api.GetOrdersAsync(Arg.Any<CancellationToken>()).Returns([order]);
        _api.CancelAsync("ORD-1", Arg.Any<CancellationToken>())
            .Returns(Task.FromException(new ApiException("conflict", 409)));

        var vm = new OrdersViewModel(_api, _logger);
        await vm.LoadCommand.ExecuteAsync(null);
        await vm.CancelCommand.ExecuteAsync(order);

        vm.Orders.Single().Status.ShouldBe("paid");           // تراجع
        vm.ErrorMessage.ShouldNotBeNull();
    }

    [Fact]
    public async Task Cancel_IsDisabled_ForAlreadyCancelledOrder()
    {
        var order = new OrderDto("ORD-1", "cancelled", 10m, "EGP");
        _api.GetOrdersAsync(Arg.Any<CancellationToken>()).Returns([order]);

        var vm = new OrdersViewModel(_api, _logger);
        await vm.LoadCommand.ExecuteAsync(null);

        vm.CancelCommand.CanExecute(order).ShouldBeFalse();
    }
}
'''},

        # ───────────────────────────────────────────── ③
        {"type": "heading", "level": 2, "text": "③ شاشة واحدة في MAUI"},
        {"type": "code", "lang": "xml", "title": "MainPage.xaml — CollectView + States + Binding إلى الـViewModel", "filename": "Pages/MainPage.xaml", "code": r'''<?xml version="1.0" encoding="utf-8" ?>
<ContentPage xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             xmlns:vm="clr-namespace:Shop.Desktop.ViewModels"
             x:Class="Shop.Desktop.Pages.MainPage"
             x:DataType="vm:OrdersViewModel"
             Title="الطلبات">

  <Grid RowDefinitions="Auto,*,Auto" Padding="16" RowSpacing="12">

    <!-- رأس + حالة -->
    <HorizontalStackLayout Grid.Row="0" Spacing="12">
      <Label Text="الطلبات" FontSize="20" FontAttributes="Bold" VerticalOptions="Center" />
      <ActivityIndicator IsRunning="{Binding State, Converter={StaticResource LoadingConverter}}"
                         IsVisible="{Binding State, Converter={StaticResource LoadingConverter}}" />
      <Button Text="تحديث" Command="{Binding LoadCommand}" />
    </HorizontalStackLayout>

    <!-- الحالات: خطأ / فراغ / قائمة -->
    <VerticalStackLayout Grid.Row="1" Spacing="8" IsVisible="{Binding HasError}">
      <Label Text="{Binding ErrorMessage}" TextColor="Crimson" />
      <Button Text="إعادة المحاولة" Command="{Binding LoadCommand}" />
    </VerticalStackLayout>

    <Label Grid.Row="1" Text="لا طلبات بعد" IsVisible="{Binding IsEmpty}"
           HorizontalOptions="Center" VerticalOptions="Center" TextColor="Gray" />

    <CollectionView Grid.Row="1" ItemsSource="{Binding Orders}"
                    IsVisible="{Binding HasOrders}"
                    SelectionMode="None">
      <CollectionView.ItemTemplate>
        <DataTemplate x:DataType="vm:OrderDto">
          <Border Padding="12" Margin="0,4" StrokeThickness="1">
            <Grid ColumnDefinitions="*,Auto,Auto" ColumnSpacing="12">
              <Label Grid.Column="0" Text="{Binding Id}" FontFamily="Mono" />
              <Label Grid.Column="1" Text="{Binding Status}" />
              <Label Grid.Column="2" Text="{Binding Total, StringFormat='{0:N2}'}" />
            </Grid>
          </Border>
        </DataTemplate>
      </CollectionView.ItemTemplate>
    </CollectionView>

    <!-- زر إلغاء للعنصر المحدد -->
    <Button Grid.Row="2" Text="إلغاء الطلب المحدد"
            Command="{Binding CancelCommand}"
            CommandParameter="{Binding Selected}" />
  </Grid>
</ContentPage>
'''},
        {"type": "code", "lang": "csharp", "title": "MauiProgram.cs — تسجيل DI + HttpClient + Handlers", "filename": "MauiProgram.cs", "code": r'''using Microsoft.Extensions.Logging;
using Shop.Desktop.Pages;
using Shop.Desktop.ViewModels;

namespace Shop.Desktop;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder
            .UseMauiApp<App>()
            .ConfigureFonts(fonts => fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular"));

#if DEBUG
        builder.Logging.AddDebug();
#endif

        // DI: نفس منهج ASP.NET Core (2.1.x)
        builder.Services.AddSingleton<App>();
        builder.Services.AddSingleton<MainPage>();
        builder.Services.AddTransient<OrdersViewModel>();

        // HttpClient المتصل بالـAPI (نفس نمط 8.1.2: تجديد/مهلة/ترويسات)
        builder.Services.AddHttpClient<IOrdersApi, OrdersApiClient>(http =>
        {
            http.BaseAddress = new Uri(DeviceInfo.Platform == DevicePlatform.Android
                ? "http://10.0.2.2:8080/"     // محاكي Android يرى المضيف على 10.0.2.2
                : "https://localhost:7080/");
            http.Timeout = TimeSpan.FromSeconds(15);
        });

        return builder.Build();
    }
}
'''},
        {"type": "callout", "kind": "warn", "title": "مطبات MAUI العملية (كلها ظهرت مع الجميع)",
         "md": "**① `localhost` على محاكي/جهاز حقيقي** — محاكي Android: `10.0.2.2` · iOS simulator: `localhost` عادةً · جهاز حقيقي: **IP الماكينة على الشبكة** + شهادة dev موثوقة. حاجة تنسى تستثنيها من `HttpClientHandler` في التطوير فقط.\n**② Build لكل منصة منفصل** — `dotnet build -f net10.0-android` · `-f net10.0-maccatalyst` … مش build واحد.\n**③ Mac Catalyst مش macOS أصلي** — بعض مكتبات macOS لا تعمل، والتجربة مش مطابقة 100%.\n**④ لوحة المفاتيح واللمس** — نفس الشاشة لازم تتعامل مع الاتنين (اختبر على Windows بالماوس وعلى Android باللمس).\n**⑤ الأداء مع القوائم الكبيرة** — `CollectionView` + `ItemsSource` ثابت أحسن من إعادة بناء القائمة في كل تغيير؛ وافتح `IncrementalLoading`."},

        # ───────────────────────────────────────────── ④
        {"type": "heading", "level": 2, "text": "④ نفس الشاشة في Avalonia"},
        {"type": "code", "lang": "xml", "title": "MainWindow.axaml — نفس الـViewModel، XAML مختلف", "filename": "Views/MainWindow.axaml", "code": r'''<Window xmlns="https://github.com/avaloniaui"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:vm="clr-namespace:Shop.Desktop.ViewModels"
        x:Class="Shop.Desktop.Views.MainWindow"
        x:DataType="vm:OrdersViewModel"
        Title="الطلبات" Width="900" Height="600">

  <DockPanel Margin="16">

    <StackPanel DockPanel.Dock="Top" Orientation="Horizontal" Spacing="12">
      <TextBlock Text="الطلبات" FontSize="20" FontWeight="Bold" VerticalAlignment="Center" />
      <ProgressBar IsIndeterminate="True" Width="120"
                   IsVisible="{Binding State, Converter={StaticResource IsLoading}}" />
      <Button Content="تحديث" Command="{Binding LoadCommand}" />
    </StackPanel>

    <StackPanel DockPanel.Dock="Bottom" Orientation="Horizontal" Spacing="8">
      <Button Content="إلغاء الطلب المحدد"
              Command="{Binding CancelCommand}"
              CommandParameter="{Binding Selected}" />
    </StackPanel>

    <Panel>
      <!-- خطأ -->
      <StackPanel Spacing="8" IsVisible="{Binding HasError}" VerticalAlignment="Center">
        <TextBlock Text="{Binding ErrorMessage}" Foreground="Crimson" TextWrapping="Wrap" />
        <Button Content="إعادة المحاولة" Command="{Binding LoadCommand}" />
      </StackPanel>

      <!-- فراغ -->
      <TextBlock Text="لا طلبات بعد" IsVisible="{Binding IsEmpty}"
                 HorizontalAlignment="Center" VerticalAlignment="Center"
                 Foreground="Gray" />

      <!-- قائمة -->
      <ListBox ItemsSource="{Binding Orders}" IsVisible="{Binding HasOrders}"
               SelectedItem="{Binding Selected}">
        <ListBox.ItemTemplate>
          <DataTemplate x:DataType="vm:OrderDto">
            <Grid ColumnDefinitions="*,Auto,Auto" ColumnSpacing="12" Margin="6">
              <TextBlock Grid.Column="0" Text="{Binding Id}" FontFamily="monospace" />
              <TextBlock Grid.Column="1" Text="{Binding Status}" />
              <TextBlock Grid.Column="2" Text="{Binding Total, StringFormat={}{0:N2}}" />
            </Grid>
          </DataTemplate>
        </ListBox.ItemTemplate>
      </ListBox>
    </Panel>
  </DockPanel>
</Window>
'''},
        {"type": "code", "lang": "csharp", "title": "Program.cs — Avalonia: DI + منصات + تغليف", "filename": "Program.cs", "code": r'''using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;

namespace Shop.Desktop;

internal static class Program
{
    [STAThread]
    public static void Main(string[] args) =>
        BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);

    // UsePlatformDetect ➜ يختار X11/Wayland/Win32/macOS تلقائيًا عبر Skia
    public static AppBuilder BuildAvaloniaApp() =>
        AppBuilder.Configure<App>()
            .UsePlatformDetect()
            .WithInterFont()
            .LogToTrace();
}

// App.axaml.cs — نقطة تركيب DI
public partial class App : Application
{
    public static IServiceProvider Services { get; private set; } = default!;

    public override void OnFrameworkInitializationCompleted()
    {
        var services = new ServiceCollection();
        services.AddSingleton<IOrdersApi, OrdersApiClient>();
        services.AddTransient<OrdersViewModel>();
        services.AddHttpClient<IOrdersApi, OrdersApiClient>(http =>
        {
            http.BaseAddress = new Uri("https://api.example.com/");  // إنتاج
            http.Timeout = TimeSpan.FromSeconds(15);
        });

        // نسجّل الـViews ولا نستخدم `new` يدويًا
        services.AddTransient<MainWindow>();
        Services = services.BuildServiceProvider();

        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.MainWindow = Services.GetRequiredService<MainWindow>();
        }

        base.OnFrameworkInitializationCompleted();
    }
}
'''},
        {"type": "table", "caption": "من وين تجيب كل منصة (مختصر التغليف)",
         "head": ["الهدف", "Maui", "Avalonia", "ملاحظة عملية"],
         "rows": [
             ["Windows", "`dotnet publish -f net10.0-windows10.0.19041.0` → MSIX", "`dotnet publish -r win-x64 --self-contained` → exe/zip", "MSIX تحتاج شهادة توقيع للتوزيع الواسع"],
             ["macOS", "`-f net10.0-maccatalyst` → .app/.pkg", "`-r osx-arm64` → .app/.dmg", "التوقيع + **notarization** إلزامي عمليًا"],
             ["Linux", "—", "`-r linux-x64` → AppImage/`.deb`", "Avalonia هي الخيار الوحيد المدعوم"],
             ["Android", "`-f net10.0-android` → .aab (Play)", "`-f net10.0-android` → .aab", "Play يتطلب التوقيع وإخلاء البيانات"],
             ["iOS", "`-f net10.0-ios` → .ipa", "`-f net10.0-ios` → .ipa", "يحتاج جهاز Mac + حساب Apple"],
             ["Web", "—", "🔶 تجريبي", "لا تعتمد عليه في منتج"],
         ]},

        # ───────────────────────────────────────────── ⑤
        {"type": "heading", "level": 2, "text": "⑤ هل يستحق وقتك الآن؟ — مصفوفة قرار"},
        {"type": "table", "caption": "قرّر بصراحة",
         "head": ["حالتك", "القرار", "الشغل المطلوب", "ما تكسبه"],
         "rows": [
             ["مطوّر Backend عايز وظيفة API/Cloud", "**اتخطّاه**", "0 ساعة", "وقتك يروح لـs9/s10 — أعلى عائد"],
             ["Full-stack في شركة تعمل Blazor", "**اتخطّاه**", "0 ساعة", "Blazor كفاية لتغطية Desktop الأساسي (PWA+) — 8.2.1"],
             ["السوق عندك بيطلب Desktop .NET (نقاط بيع/مخازن)", "**ادخل بـAvalonia**", "20–40 ساعة", "مجال وظائف أقل منافسة"],
             ["محتاج موبايل داخلي بأداء أصلي", "**ادخل بـMAUI**", "40–60 ساعة", "مهارة نادرة في فرق .NET"],
             ["محتاج واجهة واحدة للويب والموبايل", "**Uno** أو Blazor", "—", "قرار معماري مش قرار تعلّم"],
         ]},
        {"type": "callout", "kind": "goal", "title": "لو قررت تدخل — حدد سقفًا",
         "md": "**شاشة واحدة + 4 اختبارات ViewModel = «عيّنة قدرة» كافية في البورتفوليو.** لا تحاول بناء منتج: التوقيع والتحديثات وتعدد المنصات مشروع مستقل.\n**خطر شائع:** 4 أسابيع من التعلم على منتج Desktop لن يفعله أحد بعدها → مهارة فاسدة. البديل: شاشة صغيرة، تنشرها على GitHub README (بلقطة)، وتحطها في السيرة كـ«عيّنة». **20–40 ساعة كافية جدًا.**"},

        {"type": "checkpoints", "title": "وقفة تحقق", "items": [
            "تفرّق بين MAUI وAvalonia وUno: الترخيص · المنصات المدعومة · ما تُهيئه (أدوات المنصة مقابل Skia) · دعم مايكروسوفت.",
            "تعرف أن MAUI بلا Linux وبلا WASM، وأنه Mac Catalyst فقط على macOS.",
            "تعرف أن تعاون Avalonia داخل MAUI معاينة ومستهدِف .NET 11 — لا تعتمد عليه الآن.",
            "تكتب ViewModel واحدًا بـ`[ObservableProperty]`/`[RelayCommand]` لا يعرف شيئًا عن الإطار.",
            "تستخدم `enum` لحالة الشاشة + `CanExecute` لتعطيل الأوامر + `CancellationToken` في كل أمر.",
            "تختبر الـViewModel بلا واجهة (xUnit v3 + NSubstitute + Shouldly) و8.1.2 تقلب الأولويات.",
            "تسجّل DI في MAUI (`MauiProgram`) وAvalonia (`App.OnFrameworkInitializationCompleted`).",
            "تعرف مطبات `localhost` على المحاكي (`10.0.2.2` لـAndroid) وبناء كل منصة بـ`-f`.",
            "تعرف شكل التغليف لكل منصة (MSIX · dmg + notarization · AppImage · aab/ipa).",
            "تتخذ قرارًا موثقًا: تتخطّاه أم تدخله، وبأي سقف ساعات.",
        ]},

        {"type": "quiz", "title": "اختبر نفسك", "intro": "7 أسئلة — قرارات وأساسيات.",
         "questions": [
             {"q": "مشروعك لازم يشتغل على Linux في الإنتاج. أي إطار؟",
              "options": ["MAUI", "Avalonia", "Uno فقط", "Blazor Server"],
              "answer": 1,
              "explain": "MAUI لا يدعم Linux رسميًا. Avalonia يرسم بـSkia ويدعم X11/Wayland. (تعاون Avalonia/AUI كـbackend لـMAUI معاينة ومستهدِف .NET 11 — لا يُبنى عليه قرار إنتاجي في 2026.)"},
             {"q": "ما العلاقة بين MAUI وXAML؟",
              "options": ["MAUI يستخدم XAML للواجهة وC# للمنطق، ويترجم العناصر إلى عناصر المنصة عبر Handlers",
                          "MAUI لا يستخدم XAML",
                          "MAUI يستخدم HTML",
                          "XAML لغة خاصة بـWindows فقط"],
              "answer": 0,
              "explain": "MAUI يربط عناصر واجهة مشتركة بعناصر المنصة الأصلية عبر Handlers؛ ولو ظهرت مشكلة «العنصر شكل مختلف على iOS» فالسبب غالبًا Handler أو خاصية غير مدعومة على المنصة."},
             {"q": "ما دور `[RelayCommand]` و`[ObservableProperty]`؟",
              "options": ["تزيين للتوثيق فقط",
                          "مولّدات كود تبني `ICommand` و`INotifyPropertyChanged` تلقائيًا من الحقول/الدوال",
                          "تحويل XAML إلى C#",
                          "إدارة التنقل"],
              "answer": 1,
              "explain": "CommunityToolkit.Mvvm مولّدات مصدر (source generators) بتوفر مئات السطور: خاصية عامة مع إشعارات، وأمر مع `CanExecute` وتحديثه. النتيجة: ViewModel أنظف وقابل للاختبار."},
             {"q": "لماذا تختبر الـViewModel بلا واجهة؟",
              "options": ["لأن الواجهة لا تُختبر أبدًا",
                          "لأن المنطق كله في الـViewModel: الحالات والأوامر والأخطاء والتراجع — فاختباره يحمي 80% من السلوك بسرعة وثبات",
                          "لأن xUnit لا يعمل مع الواجهات",
                          "لتقليل حجم التطبيق"],
              "answer": 1,
              "explain": "اختبار UI الحقيقي بطيء وهشّ. أما الـViewModel فمنطق خالص: موك لـ`IOrdersApi` واختبار الحالات (Loading/Ready/Error/Empty)، الإلغاء المتفائل، والتراجع. هذا يعطيك ثقة عالية بأقل تكلفة."},
             {"q": "تطبيق MAUI على محاكي Android يحاول الوصول إلى `https://localhost:7080`. ما الخطأ؟",
              "options": ["لا شيء — يعمل",
                          "المحاكي يرى المضيف على `10.0.2.2` وليس `localhost` (ومع شهادة dev) — وإلا فالاتصال يفشل",
                          "يجب استخدام IP عام",
                          "MAUI لا يدعم HTTPS"],
              "answer": 1,
              "explain": "`localhost` داخل المحاكي يشير إلى المحاكي نفسه. الحل: `10.0.2.2` (أو IP الماكينة للأجهزة الحقيقية)، مع ثقة في شهادة التطوير في بيئة التطوير فقط."},
             {"q": "أي عبارة عن الحالة ممارسة سيئة؟",
              "options": ["`enum ViewState { Loading, Ready, Error, Empty }`",
                          "4 خصائص bool: `IsLoading` و`IsReady` و`HasError` و`IsEmpty` بلا قيود",
                          "`HasError => State == ViewState.Error`",
                          "`IsEmpty => State == ViewState.Ready && Orders.Count == 0`"],
              "answer": 1,
              "explain": "أربع booleans مستقلة تسمح بحالات مستحيلة (Loading && Error && Empty) وتُنتج أخطاء عرض. enum واحد + خصائص مشتقة يمنع المستحيل (نفس مبدأ 8.1.4 ①)."},
             {"q": "ما القرار الأنسب لمطوّر Backend موجّه لوظيفة API/Cloud، والسوق لا يطلب Desktop؟",
              "options": ["تعلّم MAUI وAvalonia معًا لزيادة الفرص",
                          "تخطّي الموضوع وتوجيه الوقت إلى s9 (تصميم الأنظمة) وs10 (البحث عن وظيفة) — أعلى عائد",
                          "بناء تطبيق Desktop كامل",
                          "تعلّم Uno فقط"],
              "answer": 1,
              "explain": "الندرة مهارة مردودة فقط لو السوق بيطلبها. لو السوق عندك Backend/Cloud، فساعة في تصميم الأنظمة والتواصل البنيوي في المقابلات (s9/s10) تساوي أكثر من 40 ساعة في Desktop لن تستخدمها."},
         ]},

        {"type": "tasks", "title": "مهمة اختيارية واحدة", "intro": "«عيّنة قدرة» — 20 دقيقة قراءة + 4–8 ساعات تنفيذ.",
         "items": [
            {"id": "s8-m2-l5-t1",
             "title": "مهمة: شاشة واحدة + اختبارات (MAUI أو Avalonia) — أو قرار مكتوب بالتخطّي",
             "md": "**مسار A (تنفيذ):** اعمل شاشة طلبات واحدة تربط الـAPI بتاعك (أو بيانات وهمية) بـ`OrdersViewModel` واحد و4 اختبارات. **مسار B (تخطّي):** اكتب قرارًا موثقًا (ADR قصير) بثلاثة أسباب مهنية وبديلك الزمني.",
             "criteria": [
                 "**مسار A:** مشروع واحد يستهدف منصتين على الأقل (`-f net10.0-windows10.0.19041.0` و`-f net10.0-android` أو `osx-arm64`).",
                 "`OrdersViewModel` **بلا أي اعتماد على MAUI/Avalonia** (لا `using Microsoft.Maui…` في مجلد ViewModels) — تحقق بـgrep.",
                 "حالة `enum` واحدة + خصائص مشتقة + `CancellationToken` في كل أمر + إلغاء متفائل مع تراجع.",
                 "**≥ 4 اختبارات xUnit v3** للـViewModel بـNSubstitute (نجاح · 401 · تراجع · تعطيل الأمر).",
                 "شاشة XAML فيها: مؤشر تحميل · رسالة خطأ مع إعادة محاولة · حالة فراغ · قائمة · زر إلغاء معطّل حسب `CanExecute`.",
                 "DI مسجّل بشكل صحيح + `HttpClient` بعنوان صحيح بحسب المنصة (`10.0.2.2` لـAndroid).",
                 "لقطة شاشة على **منصتين** في `docs/` + سطر كيف شغّلته لكل منصة.",
                 "**مسار B:** ADR من 1 صفحة: السياق · القرار (تخطّي) · 3 أسباب · البديل (ماذا ستفعل بهذا الوقت) · شرط إعادة النظر (مثال: «ظهر 3 إعلانات شهريًا تطلب Desktop»).",
             ],
             "hint": "ابدأ من `dotnet new maui -n Shop.Desktop` أو `dotnet new install Avalonia.Templates` ثم `dotnet new avalonia.mvvm`. خُد `CommunityToolkit.Mvvm` فقط. لو ضغط الوقت: نفّذ البيانات الوهمية أولًا، وضَع الاتصال بعد أن تعمل الاختبارات — بهذا تتأكد إن القرار معماري مش تقني. وشارك في README المشروع: «عيّنة قدرة» + قيود معروفة (Linux غير مدعوم في MAUI…).",
             "solution": "المساران مقبولان، لكن **مسار B أفضل لمعظم الناس**: ADR مكتوب بيحميك من التشتت. في المسار A، أسرع طريق هو: مشروع MVC template → ViewModel + 4 اختبارات (**قبل** XAML) → ثم XAML بسيط → ثم منصة ثانية (هنا تظهر مشاكل الخط/Win/التغليف، وده اللي بيقرر إن كنت هتكمل). العلامة على الجودة: (1) الـViewModels مجلد مستقل بلا مراجع UI، (2) كل حالة شاشة لها مسار اختبار، (3) لقطتان على منصتين. النتيجة: إما عيّنة تضعها في البورتفوليو، أو قرار مكتوب يوفّر عليك أسابيع.",
             "resources": [
                 "https://learn.microsoft.com/dotnet/maui/",
                 "https://learn.microsoft.com/dotnet/communitytoolkit/mvvm/",
                 "https://avaloniaui.net/",
                 "https://docs.avaloniaui.net/",
                 "https://platform.uno/",
                 "https://adr.github.io/",
             ]},
         ]},

        {"type": "resources", "title": "مصادر", "items": [
            {"label": ".NET MAUI (Microsoft Learn)", "url": "https://learn.microsoft.com/dotnet/maui/"},
            {"label": "CommunityToolkit.Mvvm", "url": "https://learn.microsoft.com/dotnet/communitytoolkit/mvvm/"},
            {"label": "Avalonia UI", "url": "https://avaloniaui.net/"},
            {"label": "توثيق Avalonia", "url": "https://docs.avaloniaui.net/"},
            {"label": "Uno Platform", "url": "https://platform.uno/"},
            {"label": "xUnit v3", "url": "https://xunit.net/"},
            {"label": "متسلسل: أنماط ADR", "url": "https://adr.github.io/"},
        ]},
    ],
}

LESSONS_S8_I = [_L5]
