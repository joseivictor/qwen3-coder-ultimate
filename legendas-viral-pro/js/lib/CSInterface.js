(function (global) {
  function CSInterface() {}

  global.SystemPath = global.SystemPath || { EXTENSION: "extension" };

  CSInterface.prototype.evalScript = function (script, callback) {
    if (global.__adobe_cep__ && typeof global.__adobe_cep__.evalScript === "function") {
      global.__adobe_cep__.evalScript(script, callback || function () {});
      return;
    }
    console.warn("[Legendas Viral Pro] CEP indisponivel. evalScript ignorado:", script);
    if (callback) callback(JSON.stringify({ ok: false, error: "CEP offline" }));
  };

  CSInterface.prototype.getSystemPath = function (pathType) {
    if (global.__adobe_cep__ && global.__adobe_cep__.getSystemPath) {
      return global.__adobe_cep__.getSystemPath(pathType || global.SystemPath.EXTENSION);
    }
    return "";
  };

  CSInterface.prototype.getHostEnvironment = function () {
    if (global.__adobe_cep__ && global.__adobe_cep__.getHostEnvironment) {
      try { return JSON.parse(global.__adobe_cep__.getHostEnvironment()); } catch (_) {}
    }
    return { appName: "BROWSER" };
  };

  global.CSInterface = global.CSInterface || CSInterface;
})(typeof window !== "undefined" ? window : globalThis);
