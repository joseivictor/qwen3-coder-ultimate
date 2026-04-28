(function (root) {
  const LVP = root.LVP || (root.LVP = {});
  const breaker = LVP.LineBreaker || (typeof require !== "undefined" ? require("./lineBreaker") : null);

  const STRONG_WORDS = [
    "segredo", "verdade", "nunca", "impossivel", "impossível", "cuidado", "atencao", "atenção",
    "erro", "dinheiro", "resultado", "rapido", "rápido", "simples", "importante", "chocante",
    "absurdo", "ninguem", "ninguém", "todo mundo", "voce precisa", "você precisa", "olha isso",
    "presta atencao", "presta atenção", "viral", "vender", "vendas", "milhao", "milhão",
    "milhoes", "milhões", "agora", "hoje", "pare", "nao faca", "não faça", "garantido"
  ];

  const CONTRASTS = ["mas", "porem", "porém", "só que", "na verdade", "mesmo assim", "ao contrario", "ao contrário"];
  const PROMISES = ["como", "aprenda", "descubra", "melhor", "mais rapido", "mais rápido", "sem precisar", "passo a passo"];
  const CURIOSITY = ["isso aqui", "o que acontece", "olha", "sabe por que", "por que", "ninguém te conta", "vou te mostrar"];

  function normalize(text) {
    return String(text || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function findPhrases(text, phrases) {
    const n = normalize(text);
    return phrases.filter(item => n.includes(normalize(item)));
  }

  function scoreCaption(caption) {
    const text = caption.text || "";
    const n = normalize(text);
    const hits = findPhrases(text, STRONG_WORDS);
    const contrasts = findPhrases(text, CONTRASTS);
    const promises = findPhrases(text, PROMISES);
    const curiosity = findPhrases(text, CURIOSITY);
    const numbers = text.match(/\b\d+([,.]\d+)?\s*(%|x|mil|milhao|milhão|milhoes|milhões|reais|anos|dias|horas)?\b/gi) || [];
    const questions = (text.match(/\?/g) || []).length;
    const exclamations = (text.match(/!/g) || []).length;
    const duration = Math.max(0.1, (caption.end || 0) - (caption.start || 0));
    const density = text.length / duration;
    const lengthPenalty = text.length > 160 ? -2 : text.length > 120 ? -1 : 0;

    let score = 0;
    score += hits.length * 4;
    score += numbers.length * 3;
    score += questions * 3;
    score += exclamations;
    score += contrasts.length * 2;
    score += promises.length * 2;
    score += curiosity.length * 3;
    if (density > 12 && density < 34) score += 1;
    if (/\b(você|voce|seu|sua)\b/i.test(text)) score += 1;
    score += lengthPenalty;

    return { score, hits, contrasts, promises, curiosity, numbers, questions, exclamations };
  }

  function chooseHighlight(text, analysis, type) {
    const allHits = []
      .concat(analysis.hits || [])
      .concat(analysis.numbers || [])
      .concat(analysis.curiosity || [])
      .filter(Boolean);
    if (type === "palavra" && allHits.length) return String(allHits[0]).trim();

    const sentences = String(text || "").split(/(?<=[.!?])\s+|,\s+/).map(s => s.trim()).filter(Boolean);
    const ranked = sentences
      .map(sentence => ({ sentence, analysis: scoreCaption({ text: sentence, start: 0, end: 3 }) }))
      .sort((a, b) => b.analysis.score - a.analysis.score);
    if (type === "agressivo") {
      const best = ranked[0] ? ranked[0].sentence : text;
      return breaker.breakSmart(best, { target: 14, max: 18, maxLines: 2 }).join(" ");
    }
    if (ranked[0] && ranked[0].analysis.score > 0) return ranked[0].sentence;
    if (allHits.length) return String(allHits[0]).trim();
    return "";
  }

  function thresholdFor(intensity) {
    if (intensity === "baixa") return 8;
    if (intensity === "alta") return 4;
    return 6;
  }

  function analyze(captions, options) {
    const cfg = Object.assign({
      intensity: "media",
      type: "frase",
      maxHighlights: 24,
      selectedIds: null,
      preferredTemplates: {},
      sfxEnabled: true
    }, options || {});
    const allowed = cfg.selectedIds && cfg.selectedIds.length ? new Set(cfg.selectedIds.map(Number)) : null;
    const threshold = thresholdFor(cfg.intensity);
    const scored = captions
      .filter(caption => !allowed || allowed.has(Number(caption.id)))
      .map(caption => {
        const analysis = scoreCaption(caption);
        const highlight = chooseHighlight(caption.text, analysis, cfg.type);
        const split = breaker.splitHighlightSupport(caption.text, highlight, 5);
        const lineCount = Math.min(5, Math.max(1, (split.highlightLines || []).length + (split.supportLines || []).length));
        return Object.assign({}, caption, {
          viral: analysis.score >= threshold && Boolean(highlight),
          viralScore: analysis.score,
          reasons: {
            words: analysis.hits,
            numbers: analysis.numbers,
            questions: analysis.questions,
            contrasts: analysis.contrasts,
            promises: analysis.promises,
            curiosity: analysis.curiosity
          },
          highlightText: highlight,
          supportText: split.supportLines.join(" "),
          highlightLines: split.highlightLines || [],
          supportLines: split.supportLines || [],
          lineCount,
          templateLineCount: lineCount,
          templateId: cfg.preferredTemplates[lineCount] || "",
          sfxEnabled: cfg.sfxEnabled
        });
      })
      .sort((a, b) => b.viralScore - a.viralScore);

    const selected = scored
      .filter(item => item.viral)
      .slice(0, Number(cfg.maxHighlights) || 24)
      .sort((a, b) => a.start - b.start);
    const selectedIds = new Set(selected.map(item => item.id));
    return captions.map(caption => {
      const processed = selected.find(item => item.id === caption.id);
      return processed || Object.assign({}, caption, { viral: false, viralScore: scoreCaption(caption).score });
    }).map(item => Object.assign({}, item, { selectedForViral: selectedIds.has(item.id) }));
  }

  LVP.ViralAnalyzer = { analyze, scoreCaption, chooseHighlight, STRONG_WORDS };
  if (typeof module !== "undefined") module.exports = LVP.ViralAnalyzer;
})(typeof window !== "undefined" ? window : globalThis);
