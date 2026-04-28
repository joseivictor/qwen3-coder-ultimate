const logoUrl = "https://bvwsyolgpsbvflhbqily.supabase.co/storage/v1/object/public/logos/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/5wr1JnM.webp";

const products = [
  ["Tenis Masculino Tan/Tabaco", 199.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/psAYiCO.webp@webp", "https://estima-calcados.stoqui.shop/produto/324887-tenis-masculino-tan-tabaco"],
  ["Tenis Masculino Tan/Tabaco", 199.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/Z3mNsd5.webp@webp", "https://estima-calcados.stoqui.shop/produto/324881-tenis-masculino-tan-tabaco"],
  ["Rasteira Feminina Conhaque", 149.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/MueHopO.jpg@webp", "https://estima-calcados.stoqui.shop/produto/324769-rasteira-feminina-conhaque"],
  ["Tenis Feminino Neve", 329.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/YdMCRCZ.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323318-tenis-feminino-neve"],
  ["Papete Feminino Iris", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/cVY9cqc.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323305-papete-feminino-iris"],
  ["Mocassim Feminino Neve", 279.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/e77q0Ie.webp@webp", "https://estima-calcados.stoqui.shop/produto/323258-mocassim-feminino-neve"],
  ["Sandalia Feminina Serena Napa Sand", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/5mbjlMc.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323275-sandalia-feminina-serena-napa-sand"],
  ["Tenis Masculino Preto Drake Pulse", 379.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/R8h52CP.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323065-tenis-masculino-preto-drake-pulse"],
  ["Tenis Denim Preto Democrata", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/mRj5HmL.jpg@webp", "https://estima-calcados.stoqui.shop/produto/324735-tenis-denim-preto-democrata"],
  ["Sapatenis Masculino Preto Beat Pulse", 399.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/ShsucIw.webp@webp", "https://estima-calcados.stoqui.shop/produto/324712-sapatenis-masculino-preto-beat-pulse"],
  ["Sapato Social Masculino Preto Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/LYt5XHo.webp@webp", "https://estima-calcados.stoqui.shop/produto/323130-sapato-social-masculino-preto-type"],
  ["Sapato Social Masculino Preto Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/1SFIZXg.webp@webp", "https://estima-calcados.stoqui.shop/produto/324683-sapato-social-masculino-preto-type"],
  ["Sapato Social Masculino Preto Prime", 269.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/neKMyHr.webp@webp", "https://estima-calcados.stoqui.shop/produto/322946-sapato-social-masculino-preto-prime"],
  ["Tenis Masculino Preto Clay", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/bVGx0dO.webp@webp", "https://estima-calcados.stoqui.shop/produto/322821-tenis-masculino-preto-clay"],
  ["Tenis Masculino Preto", 349.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/QDT5k3A.webp@webp", "https://estima-calcados.stoqui.shop/produto/322744-tenis-masculino-preto"],
  ["Sapato Casual Masculino Conhaque Leave", 289.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/tk0qZGE.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323181-sapato-casual-masculino-conhaque-leave"],
  ["Sapato Social Masculino Conhaque Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/fuv-0Sa.webp@webp", "https://estima-calcados.stoqui.shop/produto/323126-sapato-social-masculino-conhaque-type"],
  ["Sapato Social Masculino Conhaque Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/z3VUd6t.webp@webp", "https://estima-calcados.stoqui.shop/produto/323154-sapato-social-masculino-conhaque-type"],
  ["Sapatenis Conhaque Masculino", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/NkmFCQO.webp@webp", "https://estima-calcados.stoqui.shop/produto/322756-sapatenis-conhaque-masculino"],
  ["Tenis Masculino Branco Brad Ultra Light", 399.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/dW2pVJ8.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323175-tenis-masculino-branco-brad-ultra-light"],
  ["Tenis Denim Off White Democrata", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/NM1pkA9.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323191-tenis-denim-off-white-democrata"],
  ["Tenis Masculino Branco Block", 329.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/2rEQ9Vd.webp@webp", "https://estima-calcados.stoqui.shop/produto/322725-tenis-masculino-branco-block"],
  ["Sapato Masculino Rato Tulum", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/pSaMJQ7.jpg@webp", "https://estima-calcados.stoqui.shop/produto/323220-sapato-masculino-rato-tulum"],
  ["Tenis Masculino Preto/Smoke", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/y-dal2d.webp@webp", "https://estima-calcados.stoqui.shop/produto/323109-tenis-masculino-preto-smoke"],
  ["Sapato Masculino Smoke Leave", 289.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/BZrOEqm.webp@webp", "https://estima-calcados.stoqui.shop/produto/324722-sapato-masculino-smoke-leave"],
  ["Tenis Masculino Navy/Cinza Cloudy", 339.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/Io6SPnM.webp@webp", "https://estima-calcados.stoqui.shop/produto/323245-tenis-masculino-navy-cinza-cloudy"]
].map((item, index) => {
  const [name, price, image, url] = item;
  return {
    id: index + 1,
    name,
    price,
    image,
    url,
    category: getCategory(name),
    gender: name.toLowerCase().includes("femin") ? "Feminino" : "Masculino"
  };
});

const filters = ["Todos", "Tenis", "Sapato", "Sapatenis", "Feminino", "Conhaque", "Preto"];
let activeFilter = "Todos";

const formatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const grid = document.querySelector("#productGrid");
const filtersWrap = document.querySelector("#filters");
const searchInput = document.querySelector("#searchInput");
const quickView = document.querySelector("#quickView");
const quickViewContent = document.querySelector("#quickViewContent");

function getCategory(name) {
  const text = name.toLowerCase();
  if (text.includes("sapatenis")) return "Sapatenis";
  if (text.includes("sapato")) return "Sapato";
  if (text.includes("sandalia") || text.includes("papete") || text.includes("rasteira")) return "Feminino";
  if (text.includes("mocassim")) return "Feminino";
  return "Tenis";
}

function normalize(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function productMatches(product) {
  const query = normalize(searchInput.value.trim());
  const haystack = normalize(`${product.name} ${product.category} ${product.gender}`);
  const byQuery = !query || haystack.includes(query);
  const byFilter = activeFilter === "Todos"
    || product.category === activeFilter
    || product.gender === activeFilter
    || normalize(product.name).includes(normalize(activeFilter));
  return byQuery && byFilter;
}

function renderFilters() {
  filtersWrap.innerHTML = filters.map(filter => (
    `<button class="filter ${activeFilter === filter ? "active" : ""}" type="button" data-filter="${filter}">${filter}</button>`
  )).join("");
  filtersWrap.querySelectorAll(".filter").forEach(button => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.filter;
      renderFilters();
      renderProducts();
    });
  });
}

function renderProducts() {
  const list = products.filter(productMatches);
  grid.innerHTML = list.map(product => `
    <article class="product-card">
      <div class="product-media">
        <img src="${product.image}" alt="${product.name}" loading="lazy">
      </div>
      <div class="product-info">
        <span class="tag">${product.gender} · ${product.category}</span>
        <h3>${product.name}</h3>
        <div class="price-row">
          <strong class="price">${formatter.format(product.price)}</strong>
          <span class="installment">ou consulte na loja</span>
        </div>
        <div class="card-actions">
          <a class="buy-link" href="${product.url}" target="_blank" rel="noreferrer">Comprar</a>
          <button class="quick-button" type="button" data-id="${product.id}" aria-label="Ver detalhes de ${product.name}">+</button>
        </div>
      </div>
    </article>
  `).join("");

  grid.querySelectorAll(".quick-button").forEach(button => {
    button.addEventListener("click", () => openQuickView(Number(button.dataset.id)));
  });
}

function openQuickView(id) {
  const product = products.find(item => item.id === id);
  if (!product) return;
  quickViewContent.innerHTML = `
    <div class="quick-body">
      <img src="${product.image}" alt="${product.name}">
      <span class="tag">${product.gender} · ${product.category}</span>
      <h3>${product.name}</h3>
      <strong class="price">${formatter.format(product.price)}</strong>
      <p>Modelo selecionado da MJ Estima com compra redirecionada para o checkout original da Stoqui.</p>
      <a class="button primary" href="${product.url}" target="_blank" rel="noreferrer">Abrir produto</a>
    </div>
  `;
  quickView.classList.add("open");
  quickView.setAttribute("aria-hidden", "false");
}

document.querySelector(".close-view").addEventListener("click", () => {
  quickView.classList.remove("open");
  quickView.setAttribute("aria-hidden", "true");
});

document.addEventListener("keydown", event => {
  if (event.key === "Escape") {
    quickView.classList.remove("open");
    quickView.setAttribute("aria-hidden", "true");
  }
});

searchInput.addEventListener("input", renderProducts);

renderFilters();
renderProducts();
