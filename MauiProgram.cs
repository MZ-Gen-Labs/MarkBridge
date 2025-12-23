using MarkBridge.Services;
using Microsoft.Extensions.Logging;
using CommunityToolkit.Maui;

namespace MarkBridge;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder
            .UseMauiApp<App>()
            .UseMauiCommunityToolkit()
            .ConfigureFonts(fonts =>
            {
                fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
            });

        builder.Services.AddMauiBlazorWebView();

#if DEBUG
        builder.Services.AddBlazorWebViewDeveloperTools();
        builder.Logging.AddDebug();
#endif

        // Register services
        builder.Services.AddSingleton<AppStateService>();
        builder.Services.AddSingleton<PythonEnvironmentService>();
        builder.Services.AddSingleton<ConversionService>();

        return builder.Build();
    }
}
