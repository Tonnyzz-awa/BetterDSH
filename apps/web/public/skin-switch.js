(function () {
  try {
    var skin = localStorage.getItem("dsh.skin") || "default";
    if (skin !== "betterdsh") return;
    document.documentElement.innerHTML =
      '<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>' +
      '<title>DeepSeek Harness</title>' +
      '<style>html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000}' +
      '#skin-frame{border:0;width:100vw;height:100vh;display:block}' +
      '</style></head><body>' +
      '<iframe id="skin-frame" src="/skin-betterdsh.html?v=3"></iframe>' +
      '</body>';
  } catch (e) {}
})();
