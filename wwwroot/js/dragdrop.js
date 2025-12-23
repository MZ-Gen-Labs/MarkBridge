// Drag & Drop Test - JavaScript Interop
window.setupJsDropZone = function(elementId, dotNetRef) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('Element not found:', elementId);
        return;
    }

    element.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        element.classList.add('bg-light');
    });

    element.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        element.classList.remove('bg-light');
    });

    element.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        element.classList.remove('bg-light');

        const files = e.dataTransfer.files;
        const filePaths = [];

        console.log('Drop event - files:', files.length);

        // Note: In web browsers, we can only get file names, not full paths
        // Full paths are restricted for security reasons
        // In Electron/WebView2, this might be different
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            // Try to get path - this may not work in all environments
            const path = file.path || file.webkitRelativePath || file.name;
            filePaths.push(path);
            console.log('File:', path, 'Type:', file.type, 'Size:', file.size);
        }

        // Also check for text/uri-list (file:// URLs)
        const uriList = e.dataTransfer.getData('text/uri-list');
        if (uriList) {
            console.log('URI List:', uriList);
            const uris = uriList.split('\n').filter(u => u.startsWith('file://'));
            uris.forEach(uri => {
                // Convert file:// URI to path
                const path = decodeURIComponent(uri.replace('file:///', '').replace(/\//g, '\\'));
                if (!filePaths.includes(path)) {
                    filePaths.push(path);
                }
            });
        }

        // Send to .NET
        dotNetRef.invokeMethodAsync('OnJsFileDrop', filePaths);
    });

    console.log('JS Drop Zone initialized:', elementId);
};
