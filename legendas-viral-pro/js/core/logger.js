(function (root) {
  const LVP = root.LVP || (root.LVP = {});
  const entries = [];

  function write(level, message, data) {
    const entry = {
      at: new Date().toISOString(),
      level,
      message,
      data: data || null
    };
    entries.push(entry);
    if (entries.length > 500) entries.shift();
    if (root.console) {
      const fn = level === "error" ? "error" : level === "warn" ? "warn" : "log";
      console[fn]("[LVP]", message, data || "");
    }
    return entry;
  }

  LVP.Logger = {
    info: (message, data) => write("info", message, data),
    warn: (message, data) => write("warn", message, data),
    error: (message, data) => write("error", message, data),
    list: () => entries.slice(),
    text: () => entries.map(e => `[${e.at}] ${e.level.toUpperCase()} ${e.message}${e.data ? " " + JSON.stringify(e.data) : ""}`).join("\n")
  };

  if (typeof module !== "undefined") module.exports = LVP.Logger;
})(typeof window !== "undefined" ? window : globalThis);
