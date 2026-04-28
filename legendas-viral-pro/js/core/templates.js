(function (root) {
  const LVP = root.LVP || (root.LVP = {});

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

  function normalizeLineCount(folderName) {
    const match = String(folderName || "").match(/([1-5])/);
    return match ? Number(match[1]) : 1;
  }

  function scanWithNode(extensionPath) {
    if (typeof require === "undefined") return null;
    try {
      const fs = require("fs");
      const path = require("path");
      const base = path.join(extensionPath, "templates");
      if (!fs.existsSync(base)) return null;
      const result = [];
      fs.readdirSync(base, { withFileTypes: true }).forEach(lineDir => {
        if (!lineDir.isDirectory()) return;
        const lineCount = normalizeLineCount(lineDir.name);
        const linePath = path.join(base, lineDir.name);
        fs.readdirSync(linePath, { withFileTypes: true }).forEach(templateDir => {
          if (!templateDir.isDirectory()) return;
          const templatePath = path.join(linePath, templateDir.name);
          const files = fs.readdirSync(templatePath);
          const model = files.find(file => /\.(mogrt|cgt|cga|aep)$/i.test(file));
          const thumb = files.find(file => /^thumb\.(jpg|jpeg|png|webp)$/i.test(file));
          const sfx = files.find(file => /\.(wav|mp3|aif|aiff)$/i.test(file));
          if (model) {
            result.push({
              id: `${lineCount}-${templateDir.name}`.replace(/[^\w-]+/g, "_"),
              name: templateDir.name,
              lineCount,
              category: lineDir.name,
              file: path.join(templatePath, model),
              thumb: thumb ? path.join(templatePath, thumb) : "",
              sfx: sfx ? path.join(templatePath, sfx) : ""
            });
          }
        });
      });
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

  LVP.Templates = { list, byLineCount, FALLBACK };
  if (typeof module !== "undefined") module.exports = LVP.Templates;
})(typeof window !== "undefined" ? window : globalThis);
