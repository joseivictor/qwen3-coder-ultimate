const fs = require("fs");
const path = require("path");

const SRT = require("../js/core/srt");
const LineBreaker = require("../js/core/lineBreaker");
const ViralAnalyzer = require("../js/core/viralAnalyzer");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function readSamples() {
  const pluginDir = "C:\\Users\\José Victor\\Documents\\Plugin";
  if (!fs.existsSync(pluginDir)) return [];
  return fs.readdirSync(pluginDir)
    .filter(file => /^Sequência .+\.txt$/i.test(file))
    .map(file => ({
      file,
      text: fs.readFileSync(path.join(pluginDir, file), "utf8")
    }));
}

function testStandardSrt() {
  const sample = [
    "1",
    "00:00:00,000 --> 00:00:02,000",
    "Presta atenção nesse segredo",
    "",
    "2",
    "00:00:02,000 --> 00:00:04,000",
    "isso muda o resultado rápido"
  ].join("\n");
  const captions = SRT.parse(sample);
  assert(captions.length === 2, "SRT padrao deveria gerar 2 legendas");
  assert(captions[0].start === 0 && captions[1].end === 4, "Timing SRT padrao incorreto");
}

function testTranscriptSamples() {
  const samples = readSamples();
  assert(samples.length > 0, "Nenhum arquivo de referencia encontrado em Documents\\Plugin");
  let total = 0;
  samples.forEach(sample => {
    const captions = SRT.parse(sample.text);
    assert(captions.length > 0, sample.file + " nao gerou legendas");
    captions.forEach(caption => {
      assert(caption.end >= caption.start, sample.file + " tem timing invalido");
      assert(caption.text.length > 0, sample.file + " gerou texto vazio");
    });
    total += captions.length;
  });
  assert(total >= samples.length, "Poucas legendas geradas nos arquivos de referencia");
}

function testLineBreaker() {
  const lines = LineBreaker.breakSmart("voce precisa olhar isso porque o resultado e absurdo", { maxLines: 4 });
  assert(lines.length >= 2, "Quebra inteligente deveria separar texto longo");
  assert(lines.length <= 4, "Quebra inteligente excedeu limite");
}

function testViralAnalyzer() {
  const captions = SRT.parse([
    "1",
    "00:00:00,000 --> 00:00:02,000",
    "hoje eu acordei cedo",
    "",
    "2",
    "00:00:02,000 --> 00:00:05,000",
    "presta atenção nesse segredo porque o resultado foi absurdo",
    "",
    "3",
    "00:00:05,000 --> 00:00:08,000",
    "voce nunca viu dinheiro crescer tao rapido"
  ].join("\n"));
  const processed = ViralAnalyzer.analyze(captions, {
    intensity: "media",
    type: "agressivo",
    maxHighlights: 2,
    preferredTemplates: {}
  });
  const selected = processed.filter(item => item.selectedForViral);
  assert(selected.length === 2, "Analise viral deveria escolher 2 melhores destaques");
  assert(selected[0].highlightText.length > 0, "Destaque escolhido veio vazio");
  assert(selected.every(item => item.templateLineCount >= 1 && item.templateLineCount <= 5), "Modelo fora de 1-5 linhas");
}

function run() {
  testStandardSrt();
  testTranscriptSamples();
  testLineBreaker();
  testViralAnalyzer();
  console.log("OK - testes core passaram");
}

run();
