(function (root) {
  const LVP = root.LVP || (root.LVP = {});

  function timeToSeconds(raw) {
    if (!raw) return 0;
    const clean = String(raw).trim().replace(",", ".").replace(";", ":");
    const parts = clean.split(":").map(Number);
    if (parts.length === 4) {
      const [h, m, s, f] = parts;
      return h * 3600 + m * 60 + s + (f / 30);
    }
    if (parts.length === 3) {
      const [h, m, s] = parts;
      return h * 3600 + m * 60 + s;
    }
    return Number(clean) || 0;
  }

  function secondsToSrtTime(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const h = Math.floor(safe / 3600);
    const m = Math.floor((safe % 3600) / 60);
    const s = Math.floor(safe % 60);
    const ms = Math.round((safe - Math.floor(safe)) * 1000);
    const pad = (n, size) => String(n).padStart(size, "0");
    return `${pad(h, 2)}:${pad(m, 2)}:${pad(s, 2)},${pad(ms, 3)}`;
  }

  function cleanText(text) {
    return String(text || "")
      .replace(/\r/g, "")
      .replace(/<[^>]+>/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function parseStandardSrt(input) {
    const normalized = String(input || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!normalized) return [];
    const blocks = normalized.split(/\n{2,}/);
    const captions = [];
    blocks.forEach((block, index) => {
      const lines = block.split("\n").map(line => line.trim()).filter(Boolean);
      const timeIndex = lines.findIndex(line => /-->| - /.test(line) && /\d{2}:\d{2}/.test(line));
      if (timeIndex === -1) return;
      const timeLine = lines[timeIndex].replace(" - ", " --> ");
      const match = timeLine.match(/(\d{2}:\d{2}:\d{2}[,.:\d]*)\s*-->\s*(\d{2}:\d{2}:\d{2}[,.:\d]*)/);
      if (!match) return;
      const textLines = lines.slice(timeIndex + 1);
      captions.push({
        id: captions.length + 1,
        sourceIndex: Number(lines[0]) || index + 1,
        start: timeToSeconds(match[1]),
        end: timeToSeconds(match[2]),
        text: cleanText(textLines.join(" ")),
        raw: block
      });
    });
    return captions.filter(c => c.text);
  }

  function parseTranscript(input) {
    const normalized = String(input || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const lines = normalized.split("\n");
    const captions = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i].trim();
      const match = line.match(/^(\d{2}:\d{2}:\d{2}[:.,]\d{1,3})\s*-\s*(\d{2}:\d{2}:\d{2}[:.,]\d{1,3})$/);
      if (!match) {
        i++;
        continue;
      }
      i++;
      if (lines[i] && !/\d{2}:\d{2}:\d{2}/.test(lines[i])) i++;
      const textLines = [];
      while (i < lines.length && !/^\d{2}:\d{2}:\d{2}[:.,]\d{1,3}\s*-/.test(lines[i].trim())) {
        if (lines[i].trim()) textLines.push(lines[i].trim());
        i++;
      }
      const text = cleanText(textLines.join(" "));
      if (text) {
        captions.push({
          id: captions.length + 1,
          sourceIndex: captions.length + 1,
          start: timeToSeconds(match[1]),
          end: timeToSeconds(match[2]),
          text,
          raw: text
        });
      }
    }
    return captions;
  }

  function parse(input) {
    const standard = parseStandardSrt(input);
    if (standard.length) return standard;
    return parseTranscript(input);
  }

  function serialize(captions) {
    return captions.map((caption, index) => {
      return [
        index + 1,
        `${secondsToSrtTime(caption.start)} --> ${secondsToSrtTime(caption.end)}`,
        caption.processedText || caption.text,
        ""
      ].join("\n");
    }).join("\n");
  }

  LVP.SRT = { parse, serialize, timeToSeconds, secondsToSrtTime, cleanText };
  if (typeof module !== "undefined") module.exports = LVP.SRT;
})(typeof window !== "undefined" ? window : globalThis);
