const WHATSAPP_PHONE = "5522981481742";
const STORAGE_KEY = "jv-editor-briefing";

const presets = {
  reels: {
    nome: "Lucas Andrade",
    whatsapp: "22 99999-9999",
    instagram: "@lucasedits",
    cidade: "Atendo Brasil todo",
    headline: "Editor de videos curtos focado em ritmo, retencao e conteudo pronto para publicar.",
    publico: "Experts, infoprodutores, podcasts, marcas locais e criadores que precisam transformar brutos em Reels fortes.",
    diferencial: "Transformo conteudos longos em cortes com gancho, legenda dinamica, ritmo de rede social e acabamento profissional.",
    servicos: ["Reels 9:16", "Cortes de live", "Cortes de podcast", "Unboxing", "Thumb/capa"],
    nichos: "negocios, podcasts, fitness, beleza, educacao e conteudo comercial",
    ferramentas: "Adobe Premiere, After Effects, Photoshop e CapCut",
    estilo: "Minimalista, moderno, azul escuro, textos fortes, cortes dinamicos e portfolio com muito movimento.",
    experiencia: "3 anos",
    videosEditados: "+700 videos",
    views: "+5 milhoes",
    clientes: "Experts locais, podcasts e criadores de conteudo. Alguns trabalhos ainda sem autorizacao para publicar nomes.",
    resultados: "Cortes com mais retencao, videos com 100k+ views e criadores postando com mais consistencia.",
    links916: "https://www.instagram.com/reel/exemplo1/\nhttps://www.instagram.com/reel/exemplo2/",
    links169: "",
    referencias: "Gosto de portfolio azul, limpo, com videos em destaque e experiencia tipo motion designer.",
    precos: "Cobro por video e tambem por pacote mensal. Acima de 8 videos posso trabalhar com desconto.",
    processo: "Recebo o bruto e referencias, separo os melhores cortes, edito, envio primeira versao, faco ajustes e entrego pronto para postar.",
    materiais: "Video bruto, objetivo do conteudo, referencia, identidade visual se tiver, prazo e formato desejado.",
    prazo: "24h a 72h para cortes simples",
    cores: "azul claro, preto, branco e prata",
    dominio: "lucasedits.vercel.app",
    evitar: "Nao quero visual vermelho, frases exageradas nem site com cara de IA.",
    observacoes: "Quero que o portfolio passe confianca, velocidade e resultado."
  },
  youtube: {
    nome: "Marcos Editor",
    whatsapp: "22 99999-9999",
    instagram: "@marcoseditor",
    cidade: "Remoto para todo o Brasil",
    headline: "Editor de YouTube, VSL e conteudos longos com foco em narrativa, clareza e retencao.",
    publico: "Infoprodutores, canais de YouTube, experts, equipes de lancamento e negocios com conteudo educativo.",
    diferencial: "Organizo conteudo longo, melhoro ritmo, corto excessos, reforco storytelling e entrego videos com acabamento de marca.",
    servicos: ["YouTube 16:9", "VSL", "Cursos", "Motion design", "Thumb/capa"],
    nichos: "educacao, negocios, direct response, podcasts, aulas e treinamentos",
    ferramentas: "Premiere, After Effects, Photoshop, Audition e DaVinci Resolve",
    estilo: "Visual premium, limpo, com secoes para YouTube, VSL e aulas. Quero passar sensacao de processo profissional.",
    experiencia: "4 anos",
    videosEditados: "+300 videos longos",
    views: "+3 milhoes",
    clientes: "Canais de YouTube, experts de negocios e produtores de cursos.",
    resultados: "Videos com maior tempo de tela, aulas mais claras e VSLs com ritmo mais persuasivo.",
    links916: "",
    links169: "https://youtu.be/exemplo1\nhttps://youtu.be/exemplo2",
    referencias: "Quero algo estilo produtora premium, minimalista, com destaque para processo e cases.",
    precos: "YouTube por video. VSL e curso sob consulta depois de analisar referencia, roteiro e volume.",
    processo: "Briefing, analise de referencia, organizacao do material, edicao, motion pontual, revisao e entrega final.",
    materiais: "Roteiro, bruto, referencias, identidade visual, trilhas, assets e objetivo do video.",
    prazo: "Depende do tamanho. YouTube simples em 3 a 7 dias.",
    cores: "azul escuro, branco e cinza",
    dominio: "marcoseditor.com.br",
    evitar: "Nao quero site poluido nem muita promessa vazia.",
    observacoes: "Preciso parecer um editor confiavel para empresas e infoprodutores."
  },
  motion: {
    nome: "Ana Motion",
    whatsapp: "22 99999-9999",
    instagram: "@anamotion",
    cidade: "Brasil e projetos internacionais",
    headline: "Motion designer para videos, apresentacoes e conteudos com acabamento premium.",
    publico: "Marcas, agencias, experts, SaaS, infoprodutores e equipes que precisam de videos mais sofisticados.",
    diferencial: "Crio movimento com criterio: tipografia, composicao, ritmo, transicoes e animacoes que deixam o video com percepcao de valor.",
    servicos: ["Motion design", "Reels 9:16", "YouTube 16:9", "VSL", "Thumb/capa"],
    nichos: "tecnologia, educacao, lancamentos, marcas pessoais e produtos digitais",
    ferramentas: "After Effects, Premiere, Photoshop, Illustrator, Blender e Figma",
    estilo: "Minimalista, futurista, azul e preto, com transicoes suaves, mockups e motion vivo.",
    experiencia: "5 anos",
    videosEditados: "+1.000 pecas animadas",
    views: "+10 milhoes",
    clientes: "Agencias, experts, marcas digitais e criadores de conteudo.",
    resultados: "Videos com mais percepcao de valor, apresentacoes mais claras e conteudos mais memoraveis.",
    links916: "https://www.instagram.com/reel/exemplo-motion/",
    links169: "https://youtu.be/exemplo-motion",
    referencias: "Sites com motion premium, dark design, Apple style, UI limpa e secoes com movimento.",
    precos: "Motion geralmente e sob consulta. Posso criar pacotes por demanda mensal ou por projeto.",
    processo: "Briefing, referencia visual, storyboard simples, animacao, revisao e entrega em formatos finais.",
    materiais: "Logo, identidade visual, roteiro, textos, exemplos de movimento e formatos de saida.",
    prazo: "Projetos simples em 3 a 5 dias. Projetos maiores sob cronograma.",
    cores: "azul, preto, branco, prata e detalhes neon discretos",
    dominio: "anamotion.studio",
    evitar: "Nao quero visual infantil, excesso de efeito nem template generico.",
    observacoes: "Quero um portfolio que pareca estudio premium."
  }
};

const form = document.querySelector("#briefingForm");
const progressNumber = document.querySelector("#progressNumber");
const progressBar = document.querySelector("#progressBar");
const progressHint = document.querySelector("#progressHint");

function getFields() {
  return [...form.querySelectorAll("input:not([type='checkbox']), textarea")];
}

function setValue(name, value) {
  const field = form.elements[name];
  if (!field) return;
  field.value = value || "";
}

function applyPreset(name) {
  const preset = presets[name];
  if (!preset) return;
  getFields().forEach(field => setValue(field.name, preset[field.name]));
  form.querySelectorAll("input[type='checkbox']").forEach(input => {
    input.checked = preset.servicos.includes(input.value);
  });
  saveDraft();
  updateProgress();
  document.querySelector(".briefing-form").scrollIntoView({ behavior: "smooth", block: "start" });
}

function getChecked(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map(item => item.value);
}

function collectData() {
  const data = {};
  getFields().forEach(field => {
    data[field.name] = field.value.trim();
  });
  data.servicos = getChecked("servicos");
  return data;
}

function saveDraft() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(collectData()));
}

function loadDraft() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    Object.entries(data).forEach(([name, value]) => {
      if (name === "servicos") return;
      setValue(name, value);
    });
    form.querySelectorAll("input[type='checkbox']").forEach(input => {
      input.checked = (data.servicos || []).includes(input.value);
    });
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function updateProgress() {
  const fields = getFields();
  const checkedGroups = getChecked("servicos").length ? 1 : 0;
  const filled = fields.filter(field => field.value.trim().length > 0).length + checkedGroups;
  const total = fields.length + 1;
  const percent = Math.round((filled / total) * 100);
  progressNumber.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  progressHint.textContent = percent < 35
    ? "Comece pelo basico. O resto eu organizo com voce."
    : percent < 75
      ? "Boa. Agora faltam provas, links e oferta para o portfolio vender melhor."
      : "Perfeito. Ja da para transformar isso em um portfolio bem direcionado.";
}

function section(title, lines) {
  const content = lines.filter(Boolean).join("\n");
  return content ? `\n*${title}*\n${content}` : "";
}

function buildMessage(data) {
  return [
    "Oi, Jose. Quero criar um portfolio para editor. Segue meu briefing:",
    section("1. Identidade", [
      `Nome: ${data.nome || "-"}`,
      `WhatsApp: ${data.whatsapp || "-"}`,
      `Instagram: ${data.instagram || "-"}`,
      `Cidade/atendimento: ${data.cidade || "-"}`
    ]),
    section("2. Posicionamento", [
      `Frase: ${data.headline || "-"}`,
      `Publico: ${data.publico || "-"}`,
      `Diferencial: ${data.diferencial || "-"}`
    ]),
    section("3. Servicos e estilo", [
      `Servicos: ${data.servicos.length ? data.servicos.join(", ") : "-"}`,
      `Nichos: ${data.nichos || "-"}`,
      `Ferramentas: ${data.ferramentas || "-"}`,
      `Estilo: ${data.estilo || "-"}`
    ]),
    section("4. Provas e numeros", [
      `Experiencia: ${data.experiencia || "-"}`,
      `Videos editados: ${data.videosEditados || "-"}`,
      `Views geradas: ${data.views || "-"}`,
      `Clientes/experts: ${data.clientes || "-"}`,
      `Resultados: ${data.resultados || "-"}`
    ]),
    section("5. Portfolio e referencias", [
      `Videos 9:16:\n${data.links916 || "-"}`,
      `Videos 16:9:\n${data.links169 || "-"}`,
      `Referencias:\n${data.referencias || "-"}`
    ]),
    section("6. Oferta e funcionamento", [
      `Precos: ${data.precos || "-"}`,
      `Processo: ${data.processo || "-"}`,
      `Materiais necessarios: ${data.materiais || "-"}`,
      `Prazo medio: ${data.prazo || "-"}`
    ]),
    section("7. Preferencias do site", [
      `Cores: ${data.cores || "-"}`,
      `Dominio/nome: ${data.dominio || "-"}`,
      `Evitar: ${data.evitar || "-"}`,
      `Observacoes: ${data.observacoes || "-"}`
    ])
  ].join("\n");
}

function openWhatsApp(message) {
  const text = encodeURIComponent(message);
  window.location.href = `whatsapp://send?phone=${WHATSAPP_PHONE}&text=${text}`;
  setTimeout(() => {
    window.open(`https://wa.me/${WHATSAPP_PHONE}?text=${text}`, "_blank", "noopener");
  }, 900);
}

document.querySelectorAll("[data-preset]").forEach(button => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});

document.querySelector("#clearForm").addEventListener("click", () => {
  form.reset();
  localStorage.removeItem(STORAGE_KEY);
  updateProgress();
});

form.addEventListener("input", () => {
  saveDraft();
  updateProgress();
});

form.addEventListener("change", () => {
  saveDraft();
  updateProgress();
});

form.addEventListener("submit", event => {
  event.preventDefault();
  const data = collectData();
  saveDraft();
  openWhatsApp(buildMessage(data));
});

loadDraft();
updateProgress();
