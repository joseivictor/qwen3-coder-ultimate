/* Legendas Viral Pro - Host Bridge
   CEP ExtendScript entrypoint for Premiere Pro and After Effects. */

var LVP_TICKS_PER_SECOND = 254016000000;

function LVP_hasJSON() {
  return typeof JSON !== "undefined" && JSON.parse && JSON.stringify;
}

function LVP_response(ok, data) {
  var payload = data || {};
  payload.ok = ok;
  if (LVP_hasJSON()) return JSON.stringify(payload);
  return ok ? '{"ok":true}' : '{"ok":false,"error":"JSON indisponivel no host"}';
}

function LVP_parse(jsonText) {
  if (!LVP_hasJSON()) throw new Error("JSON indisponivel no host Adobe");
  return JSON.parse(jsonText);
}

function LVP_safeName(value, fallback) {
  try {
    if (value !== undefined && value !== null && String(value).length) return String(value);
  } catch (e) {}
  return fallback;
}

function LVP_hostName() {
  try { return String(app.name || "Adobe"); } catch (e) { return "Adobe"; }
}

function LVP_getContext() {
  try {
    var host = LVP_hostName();
    var projectId = "sem_projeto";
    var sequenceId = "sem_sequencia";

    if (host.indexOf("Premiere") >= 0) {
      if (app.project) {
        projectId = app.project.path ? app.project.path : LVP_safeName(app.project.name, "premiere_sem_nome");
        if (app.project.activeSequence) {
          sequenceId = LVP_safeName(app.project.activeSequence.sequenceID, app.project.activeSequence.name);
        }
      }
    } else if (host.indexOf("After Effects") >= 0) {
      if (app.project) {
        projectId = app.project.file ? app.project.file.fsName : LVP_safeName(app.project.name, "after_sem_nome");
        if (app.project.activeItem) {
          sequenceId = LVP_safeName(app.project.activeItem.id, app.project.activeItem.name);
        }
      }
    }

    return LVP_response(true, { host: host, projectId: projectId, sequenceId: sequenceId });
  } catch (err) {
    return LVP_response(false, { error: "Falha ao ler contexto: " + err.message });
  }
}

function LVP_secondsToTicks(seconds) {
  if (seconds === null || seconds === undefined || isNaN(Number(seconds))) return "0";
  return String(Math.round(Number(seconds) * LVP_TICKS_PER_SECOND));
}

function LVP_hexToRgb(hex) {
  var clean = String(hex || "#ffffff").replace("#", "");
  if (clean.length === 3) {
    clean = clean.charAt(0) + clean.charAt(0) + clean.charAt(1) + clean.charAt(1) + clean.charAt(2) + clean.charAt(2);
  }
  var n = parseInt(clean, 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

function LVP_itemText(item) {
  var support = item.supportLines && item.supportLines.length ? item.supportLines.join("\r") : item.text;
  if (item.highlightText && item.highlightText.length) return item.highlightText + "\r" + support;
  return support;
}

function LVP_markerFallback(seq, item, warnings) {
  try {
    if (!seq || !seq.markers || !seq.markers.createMarker) return false;
    var at = item.start === null || item.start === undefined ? 0 : Number(item.start);
    var marker = seq.markers.createMarker(at);
    marker.name = "LVP - " + (item.highlightText || "Legenda");
    marker.comments = LVP_itemText(item);
    if (item.end !== null && item.end !== undefined) marker.end = Number(item.end);
    warnings.push("Sem modelo valido: criei marcador para item " + item.id + ".");
    return true;
  } catch (err) {
    warnings.push("Fallback de marcador falhou no item " + item.id + ": " + err.message);
  }
  return false;
}

function LVP_applyPremiereItem(seq, item, warnings) {
  var templateFile = item.template && item.template.file ? File(item.template.file) : null;
  if (templateFile && templateFile.exists && seq.importMGT) {
    try {
      var ticks = LVP_secondsToTicks(item.start);
      seq.importMGT(templateFile.fsName, ticks, 0, 0);
      return true;
    } catch (err) {
      warnings.push("ImportMGT falhou no item " + item.id + ": " + err.message);
    }
  }
  return LVP_markerFallback(seq, item, warnings);
}

function LVP_addAeTextLayer(comp, item, payload, warnings) {
  try {
    var layer = comp.layers.addText(LVP_itemText(item));
    var doc = layer.property("Source Text").value;
    var style = payload.style || {};
    doc.font = style.fontSupport || "Montserrat";
    doc.fillColor = LVP_hexToRgb(style.colorSupport || "#ffffff");
    doc.fontSize = item.lineCount >= 4 ? 54 : 68;
    doc.justification = ParagraphJustification.CENTER_JUSTIFY;
    layer.property("Source Text").setValue(doc);

    if (item.start !== null && item.start !== undefined) layer.startTime = Number(item.start);
    if (item.end !== null && item.end !== undefined && Number(item.end) > Number(item.start || 0)) {
      layer.outPoint = Number(item.end);
    }

    layer.property("Position").setValue([comp.width / 2, comp.height * 0.78]);
    layer.name = "LVP_" + (item.highlightText || "legenda");
    return true;
  } catch (err) {
    warnings.push("After Effects falhou no item " + item.id + ": " + err.message);
  }
  return false;
}

function LVP_applyCaptionTemplateBatch(payloadJson) {
  app.beginUndoGroup && app.beginUndoGroup("Legendas Viral Pro");
  try {
    var payload = LVP_parse(payloadJson);
    var items = payload.items || [];
    var host = LVP_hostName();
    var applied = 0;
    var warnings = [];

    if (host.indexOf("Premiere") >= 0) {
      var seq = app.project && app.project.activeSequence ? app.project.activeSequence : null;
      if (!seq) throw new Error("Abra uma sequencia no Premiere antes de aplicar.");
      for (var i = 0; i < items.length; i++) {
        if (LVP_applyPremiereItem(seq, items[i], warnings)) applied++;
      }
    } else if (host.indexOf("After Effects") >= 0) {
      var comp = app.project && app.project.activeItem ? app.project.activeItem : null;
      if (!comp || !comp.layers) throw new Error("Abra uma composicao no After Effects antes de aplicar.");
      for (var j = 0; j < items.length; j++) {
        if (LVP_addAeTextLayer(comp, items[j], payload, warnings)) applied++;
      }
    } else {
      throw new Error("Host nao suportado: " + host);
    }

    return LVP_response(true, { host: host, applied: applied, warnings: warnings });
  } catch (err) {
    return LVP_response(false, { error: err.message });
  } finally {
    try { app.endUndoGroup && app.endUndoGroup(); } catch (e) {}
  }
}
