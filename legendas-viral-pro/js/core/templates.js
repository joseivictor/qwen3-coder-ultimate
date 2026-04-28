(function (root) {
  const LVP = root.LVP || (root.LVP = {});

  const LEGACY_LIBRARY_PATH = "C:\\Program Files (x86)\\Common Files\\Adobe\\CEP\\extensions\\Legendas Master 3.7\\templates";

  const FALLBACK = [1, 2, 3, 4, 5].flatMap(lineCount => ([
    {
      id: `viral-${lineCount}-default`,
      name: `Viral ${lineCount} linha${lineCount > 1 ? "s" : ""}`,
      lineCount,
      category: "Viral",
      file: `templates/${lineCount}-linha${lineCount > 1 ? "s" : ""}/ADICIONE_SEU_MODELO.mogrt`,
      sfx: ""
    }
  ]));

  function normalizeLineCount(parts) {
    const pathText = Array.isArray(parts) ? parts.join(" ") : String(parts || "");
    if (/uma linha|1[-_\s]*linha|frases?/i.test(pathText)) return 1;
    const match = pathText.match(/([1-5])\s*linha/i) || pathText.match(/\b([1-5])L\b/i);
    return match ? Number(match[1]) : 2;
  }

  function templatePriority(file) {
    if (/template\.cgt$/i.test(file)) return 0;
    if (/\.mogrt$/i.test(file)) return 1;
    if (/\.cgt$/i.test(file)) return 2;
    if (/\.cga$/i.test(file)) return 3;
    if (/\.aep$/i.test(file)) return 4;
    return 9;
  }

  function scanTemplateRoot(fs, path, base, sourceLabel) {
    if (!base || !fs.existsSync(base)) return [];
    const result = [];

    function walk(dir, parts) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      const files = entries.filter(entry => entry.isFile()).map(entry => entry.name);
      const models = files.filter(file => /\.(mogrt|cgt|cga|aep)$/i.test(file)).sort((a, b) => templatePriority(a) - templatePriority(b));
      if (models.length) {
        const thumb = files.find(file => /^thumb\.(jpg|jpeg|png|webp)$/i.test(file)) ||
          files.find(file => /\.(jpg|jpeg|png|webp)$/i.test(file));
        const preview = files.find(file => /\.(mp4|mov|webm)$/i.test(file));
        const sfx = files.find(file => /\.(wav|mp3|aif|aiff)$/i.test(file));
        const lineCount = normalizeLineCount(parts);
        const category = parts.length > 1 ? parts.slice(0, -1).join(" / ") : sourceLabel;
        const name = parts.length ? parts[parts.length - 1] : path.basename(dir);
        result.push({
          id: `${sourceLabel}-${lineCount}-${parts.join("-")}`.replace(/[^\w-]+/g, "_"),
          name,
          lineCount,
          category,
          source: sourceLabel,
          file: path.join(dir, models[0]),
          companion: models[1] ? path.join(dir, models[1]) : "",
          thumb: thumb ? path.join(dir, thumb) : "",
          preview: preview ? path.join(dir, preview) : "",
          sfx: sfx ? path.join(dir, sfx) : ""
        });
      }
      entries.filter(entry => entry.isDirectory()).forEach(entry => {
        walk(path.join(dir, entry.name), parts.concat(entry.name));
      });
    }

    walk(base, []);
    return result;
  }

  function scanWithNode(extensionPath) {
    if (typeof require === "undefined") return null;
    try {
      const fs = require("fs");
      const path = require("path");
      const localBase = path.join(extensionPath || "", "templates");
      const result = []
        .concat(scanTemplateRoot(fs, path, localBase, "Legendas Viral Pro"))
        .concat(scanTemplateRoot(fs, path, LEGACY_LIBRARY_PATH, "Legendas Master 3.7"));
      return result.length ? result : null;
    } catch (error) {
      return null;
    }
  }

  function list(extensionPath) {
    return scanWithNode(extensionPath) || FALLBACK.slice();
  }

  function byLineCount(templates) {
    return (templates || []).reduce((acc, template) => {
      const key = template.lineCount || 1;
      acc[key] = acc[key] || [];
      acc[key].push(template);
      return acc;
    }, {});
  }

  LVP.Templates = { list, byLineCount, FALLBACK, LEGACY_LIBRARY_PATH };
  if (typeof module !== "undefined") module.exports = LVP.Templates;
})(typeof window !== "undefined" ? window : globalThis);
