(function (root) {
  const LVP = root.LVP || (root.LVP = {});
  const KEY_PREFIX = "legendas_viral_pro_cache:";

  function safeKey(projectId, sequenceId) {
    return `${KEY_PREFIX}${String(projectId || "sem_projeto").replace(/[^\w.-]+/g, "_")}:${String(sequenceId || "sem_sequencia").replace(/[^\w.-]+/g, "_")}`;
  }

  function save(projectId, sequenceId, payload) {
    const data = Object.assign({}, payload, {
      projectId,
      sequenceId,
      savedAt: new Date().toISOString()
    });
    localStorage.setItem(safeKey(projectId, sequenceId), JSON.stringify(data));
    return data;
  }

  function load(projectId, sequenceId) {
    const raw = localStorage.getItem(safeKey(projectId, sequenceId));
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (_) { return null; }
  }

  function clear(projectId, sequenceId) {
    localStorage.removeItem(safeKey(projectId, sequenceId));
  }

  LVP.Cache = { save, load, clear, safeKey };
  if (typeof module !== "undefined") module.exports = LVP.Cache;
})(typeof window !== "undefined" ? window : globalThis);
