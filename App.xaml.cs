namespace MarkBridge;

public partial class App : Application
{
    public App()
    {
        // WebView2 user data folder fix for Program Files installation
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var cacheFolder = Path.Combine(localAppData, "MarkBridge", "WebView2");
        Environment.SetEnvironmentVariable("WEBVIEW2_USER_DATA_FOLDER", cacheFolder);

        InitializeComponent();

        MainPage = new MainPage();
    }
}
