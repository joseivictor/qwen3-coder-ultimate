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
  if (!templateFile || !templateFile.exists) return LVP_markerFallback(seq, item, warnings);

  var ext = String(templateFile.name).split(".").pop().toLowerCase();
  if (ext === "mogrt" && seq.importMGT) {
    try {
      var ticks = LVP_secondsToTicks(item.start);
      seq.importMGT(templateFile.fsName, ticks, 0, 0);
      LVP_applyPremiereSfx(seq, item, warnings);
      return true;
    } catch (err) {
      warnings.push("ImportMGT falhou no item " + item.id + ": " + err.message);
    }
  }

  if (ext === "cgt" || ext === "cga") {
    try {
      var imported = LVP_importProjectItem(templateFile.fsName, warnings);
      if (imported) {
        var track = LVP_firstVideoTrack(seq);
        if (track && track.overwriteClip) {
          track.overwriteClip(imported, LVP_secondsToTicks(item.start));
          LVP_applyPremiereSfx(seq, item, warnings);
          return true;
        }
        warnings.push("Importei o modelo, mas nao achei trilha de video disponivel.");
      }
    } catch (legacyErr) {
      warnings.push("Aplicacao de CGT/CGA falhou no item " + item.id + ": " + legacyErr.message);
    }
  }

  return LVP_markerFallback(seq, item, warnings);
}

function LVP_firstVideoTrack(seq) {
  try {
    if (!seq.videoTracks || seq.videoTracks.numTracks < 1) return null;
    for (var i = seq.videoTracks.numTracks - 1; i >= 0; i--) {
      var track = seq.videoTracks[i];
      if (track) return track;
    }
  } catch (err) {}
  return null;
}

function LVP_firstAudioTrack(seq) {
  try {
    if (!seq.audioTracks || seq.audioTracks.numTracks < 1) return null;
    for (var i = 0; i < seq.audioTracks.numTracks; i++) {
      var track = seq.audioTracks[i];
      if (track) return track;
    }
  } catch (err) {}
  return null;
}

function LVP_importProjectItem(filePath, warnings) {
  var file = File(filePath);
  if (!file.exists) return null;
  var before = [];
  LVP_collectProjectItems(app.project.rootItem, before);
  app.project.importFiles([file.fsName], true, app.project.rootItem, false);
  var after = [];
  LVP_collectProjectItems(app.project.rootItem, after);
  for (var i = 0; i < after.length; i++) {
    if (!LVP_arrayContains(before, after[i])) return after[i];
  }
  var found = LVP_findProjectItemByName(app.project.rootItem, file.name);
  if (!found) warnings.push("Arquivo importado, mas item nao encontrado no projeto: " + file.name);
  return found;
}

function LVP_collectProjectItems(parent, list) {
  if (!parent || !parent.children) return;
  for (var i = 0; i < parent.children.numItems; i++) {
    var child = parent.children[i];
    list.push(child);
    LVP_collectProjectItems(child, list);
  }
}

function LVP_arrayContains(list, item) {
  for (var i = 0; i < list.length; i++) if (list[i] === item) return true;
  return false;
}

function LVP_findProjectItemByName(parent, name) {
  if (!parent || !parent.children) return null;
  for (var i = 0; i < parent.children.numItems; i++) {
    var child = parent.children[i];
    if (child && child.name === name) return child;
    var nested = LVP_findProjectItemByName(child, name);
    if (nested) return nested;
  }
  return null;
}

function LVP_applyPremiereSfx(seq, item, warnings) {
  if (!item.sfx || !seq) return false;
  try {
    var audioFile = File(item.sfx);
    if (!audioFile.exists) return false;
    var imported = LVP_importProjectItem(audioFile.fsName, warnings);
    var track = LVP_firstAudioTrack(seq);
    if (imported && track && track.overwriteClip) {
      track.overwriteClip(imported, LVP_secondsToTicks(item.start));
      return true;
    }
  } catch (err) {
    warnings.push("SFX falhou no item " + item.id + ": " + err.message);
  }
  return false;
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
