using Microsoft.Maui.Controls;
using System.Diagnostics;

#if WINDOWS
using Windows.ApplicationModel.DataTransfer;
using Windows.Storage;
#endif

namespace MarkBridge;

public partial class MainPage : ContentPage
{
    // Static list to store dropped file paths (accessible from Blazor)
    public static List<string> DroppedFilePaths { get; private set; } = new();
    public static event Action<List<string>>? OnFilesDropped;

    public MainPage()
    {
        InitializeComponent();
    }

    private void OnDragOver(object? sender, DragEventArgs e)
    {
        Debug.WriteLine("[MainPage] DragOver event triggered");
        e.AcceptedOperation = Microsoft.Maui.Controls.DataPackageOperation.Copy;
    }

    private async void OnDrop(object? sender, DropEventArgs e)
    {
        Debug.WriteLine("[MainPage] Drop event triggered");
        
        try
        {
            DroppedFilePaths.Clear();

#if WINDOWS
            // Windows: Use platform-specific handler
            var args = e.PlatformArgs;
            if (args?.DragEventArgs?.DataView != null)
            {
                var dataView = args.DragEventArgs.DataView;
                
                if (dataView.Contains(StandardDataFormats.StorageItems))
                {
                    var items = await dataView.GetStorageItemsAsync();
                    Debug.WriteLine($"[MainPage] Got {items.Count} storage items from Windows");
                    
                    foreach (var item in items)
                    {
                        Debug.WriteLine($"[MainPage] Item: {item.Path}");
                        if (item is StorageFile file)
                        {
                            DroppedFilePaths.Add(file.Path);
                        }
                        else if (item is StorageFolder folder)
                        {
                            DroppedFilePaths.Add(folder.Path);
                        }
                    }
                }
                else if (dataView.Contains(StandardDataFormats.Text))
                {
                    var text = await dataView.GetTextAsync();
                    Debug.WriteLine($"[MainPage] Got text: {text}");
                    
                    // Parse file paths from text
                    var lines = text.Split('\n', StringSplitOptions.RemoveEmptyEntries);
                    foreach (var line in lines)
                    {
                        var path = line.Trim();
                        if (path.StartsWith("file:///"))
                        {
                            path = Uri.UnescapeDataString(path.Substring(8).Replace('/', '\\'));
                        }
                        if (File.Exists(path) || Directory.Exists(path))
                        {
                            DroppedFilePaths.Add(path);
                        }
                    }
                }
            }
#else
            // Non-Windows: Try generic approach
            var data = e.Data;
            if (data != null)
            {
                var text = await data.GetTextAsync();
                if (!string.IsNullOrEmpty(text))
                {
                    Debug.WriteLine($"[MainPage] Got text: {text}");
                    DroppedFilePaths.Add(text);
                }
            }
#endif

            if (DroppedFilePaths.Count > 0)
            {
                Debug.WriteLine($"[MainPage] Total dropped files: {DroppedFilePaths.Count}");
                foreach (var path in DroppedFilePaths)
                {
                    Debug.WriteLine($"[MainPage]   - {path}");
                }
                
                // Notify Blazor components
                OnFilesDropped?.Invoke(new List<string>(DroppedFilePaths));
            }
            else
            {
                Debug.WriteLine("[MainPage] No files found in drop data");
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[MainPage] Error handling drop: {ex.Message}");
            Debug.WriteLine(ex.StackTrace);
        }
    }
}
