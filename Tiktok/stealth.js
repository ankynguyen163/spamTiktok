// stealth.js – full fingerprint spoof + media unlock
(() => {
  // === 1. navigator.webdriver ===
  delete Object.getPrototypeOf(navigator).webdriver;
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
  });

  // === 2. Plugins & MimeTypes ===
  const pluginList = [
    "PDF Viewer", "Chrome PDF Viewer", "Chromium PDF Viewer",
    "Microsoft Edge PDF Viewer", "WebKit built-in PDF"
  ];
  const mimeTypesList = [
    { type: "application/pdf", suffixes: "pdf", description: "Portable Document Format" },
    { type: "text/pdf", suffixes: "pdf", description: "Portable Document Format" }
  ];

  const createPlugin = (name) => {
    const plugin = Object.create(Plugin.prototype);
    Object.defineProperties(plugin, {
      name: { value: name },
      filename: { value: "internal-pdf-viewer" },
      description: { value: "Portable Document Format" },
      length: { value: mimeTypesList.length },
      item: { value: (i) => mimeTypesList[i] || null },
      namedItem: { value: (type) => mimeTypesList.find(m => m.type === type) || null }
    });
    mimeTypesList.forEach((m, i) => {
      const mime = Object.create(MimeType.prototype);
      Object.defineProperties(mime, {
        type: { value: m.type },
        suffixes: { value: m.suffixes },
        description: { value: m.description },
        enabledPlugin: { value: plugin }
      });
      plugin[i] = mime;
    });
    return plugin;
  };

  const plugins = pluginList.map(createPlugin);
  const pluginArray = Object.create(PluginArray.prototype);
  plugins.forEach((p, i) => pluginArray[i] = p);
  Object.defineProperties(pluginArray, {
    length: { value: plugins.length },
    item: { value: i => plugins[i] || null },
    namedItem: { value: name => plugins.find(p => p.name === name) || null }
  });
  Object.defineProperty(navigator, 'plugins', { value: pluginArray });

  const mimeTypeArray = Object.create(MimeTypeArray.prototype);
  const flatMime = plugins.flatMap(p => Object.values(p).filter(m => m.type));
  flatMime.forEach((m, i) => mimeTypeArray[i] = m);
  Object.defineProperties(mimeTypeArray, {
    length: { value: flatMime.length },
    item: { value: i => flatMime[i] || null },
    namedItem: { value: name => flatMime.find(m => m.type === name) || null }
  });
  Object.defineProperty(navigator, 'mimeTypes', { value: mimeTypeArray });

  // === 3. UA & platform
  Object.defineProperty(navigator, 'userAgent', {
    value: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
  });
  Object.defineProperty(navigator, 'platform', { value: 'Linux x86_64' });

  // === 4. Languages
  Object.defineProperty(navigator, 'languages', {
    value: ['vi-VN', 'vi', 'fr-FR', 'fr', 'en-US', 'en']
  });

  // === 5. Screen & Window Metrics
  const screenProps = {
    width: 1280, height: 720, availWidth: 1280, availHeight: 720,
    colorDepth: 24, pixelDepth: 24
  };
  Object.entries(screenProps).forEach(([k, v]) =>
    Object.defineProperty(window.screen, k, { value: v, configurable: true })
  );

  Object.defineProperties(window, {
    innerWidth:        { value: 1280, configurable: true },
    innerHeight:       { value: 720, configurable: true },
    outerWidth:        { value: 1288, configurable: true },
    outerHeight:       { value: 759, configurable: true },
    screenX:           { value: 76, configurable: true },
    screenY:           { value: 22, configurable: true },
    pageXOffset:       { value: 0, configurable: true },
    pageYOffset:       { value: 0, configurable: true },
    devicePixelRatio:  { value: 1, configurable: true }
  });

  // === 6. WebGL Vendor/Renderer
const originalGetSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
WebGLRenderingContext.prototype.getSupportedExtensions = function () {
  const extensions = originalGetSupportedExtensions.call(this);
  return extensions.filter(name => name !== "WEBGL_debug_renderer_info");
};

  // === 7. Touch + HW info
  Object.defineProperty(navigator, 'maxTouchPoints', { value: 10 });
  Object.defineProperty(navigator, 'deviceMemory', { value: 4 });
  Object.defineProperty(navigator, 'hardwareConcurrency', { value: 4 });

  // === 8. mediaDevices
  if ('mediaDevices' in navigator) {
    Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {
      value: () => Promise.resolve([
        { kind: 'audioinput' }, { kind: 'audiooutput' }, { kind: 'videoinput' }
      ])
    });
  }

  // === 9. Permissions
  const origPerm = navigator.permissions.query;
  navigator.permissions.query = (p) =>
    p.name === 'notifications' ? Promise.resolve({ state: 'default' }) : origPerm(p);

  // === 10. Focus / visibility spoof (TikTok, FB)
  Object.defineProperty(document, 'visibilityState', { value: 'visible' });
  Object.defineProperty(document, 'hidden', { value: false });
  document.hasFocus = () => true;

  // === 11. MediaCapabilities.decodingInfo spoof (TikTok video)
  if ('mediaCapabilities' in navigator) {
    navigator.mediaCapabilities.decodingInfo = async () => ({
      supported: true,
      smooth: true,
      powerEfficient: true
    });
  }

  // === 12. Bypass gesture autoplay policy
  const realPlay = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    const result = realPlay.call(this);
    if (result?.catch) result.catch(() => {}); // prevent gesture errors
    return result;
  };

  // === 13. Clipboard spoof (optional for TikTok stealth)
  navigator.clipboard = {
    readText: async () => '',
    writeText: async () => {},
    read: async () => [],
    write: async () => {}
  };
})();
