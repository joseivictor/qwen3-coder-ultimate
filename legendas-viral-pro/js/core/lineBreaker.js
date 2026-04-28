(function (root) {
  const LVP = root.LVP || (root.LVP = {});

  function words(text) {
    return String(text || "").trim().split(/\s+/).filter(Boolean);
  }

  function breakSmart(text, options) {
    const cfg = Object.assign({ target: 16, min: 10, max: 22, maxLines: 5 }, options || {});
    const tokens = words(text);
    if (!tokens.length) return [];
    const lines = [];
    let current = "";
    tokens.forEach(token => {
      const attempt = current ? `${current} ${token}` : token;
      if (attempt.length <= cfg.max && (attempt.length <= cfg.target || current.length < cfg.min)) {
        current = attempt;
      } else {
        if (current) lines.push(current);
        current = token;
      }
    });
    if (current) lines.push(current);

    if (lines.length <= cfg.maxLines) return lines;
    const compact = [];
    let bucket = "";
    lines.join(" ").split(/\s+/).forEach(token => {
      const attempt = bucket ? `${bucket} ${token}` : token;
      if (attempt.length <= cfg.max + 8 || compact.length >= cfg.maxLines - 1) {
        bucket = attempt;
      } else {
        compact.push(bucket);
        bucket = token;
      }
    });
    if (bucket) compact.push(bucket);
    return compact.slice(0, cfg.maxLines);
  }

  function lineCountForText(text) {
    return Math.min(5, Math.max(1, breakSmart(text).length));
  }

  function splitHighlightSupport(text, highlight, maxLines) {
    const clean = String(text || "").trim();
    const hit = String(highlight || "").trim();
    if (!hit) return { highlight: "", support: breakSmart(clean, { maxLines }) };
    const support = clean.replace(new RegExp(hit.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"), "").replace(/\s+/g, " ").trim();
    return {
      highlight: hit,
      highlightLines: breakSmart(hit, { target: 14, max: 18, maxLines: Math.min(2, maxLines || 2) }),
      supportLines: breakSmart(support, { target: 16, max: 22, maxLines: Math.max(1, (maxLines || 3) - 1) })
    };
  }

  LVP.LineBreaker = { breakSmart, lineCountForText, splitHighlightSupport };
  if (typeof module !== "undefined") module.exports = LVP.LineBreaker;
})(typeof window !== "undefined" ? window : globalThis);
