const products = [
  ["Tenis Masculino Tan/Tabaco", 199.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/psAYiCO.webp@webp"],
  ["Tenis Masculino Tan/Tabaco", 199.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/Z3mNsd5.webp@webp"],
  ["Rasteira Feminina Conhaque", 149.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/MueHopO.jpg@webp"],
  ["Tenis Feminino Neve", 329.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/YdMCRCZ.jpg@webp"],
  ["Papete Feminino Iris", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/cVY9cqc.jpg@webp"],
  ["Mocassim Feminino Neve", 279.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/e77q0Ie.webp@webp"],
  ["Sandalia Feminina Serena Napa Sand", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/5mbjlMc.jpg@webp"],
  ["Tenis Masculino Preto Drake Pulse", 379.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/R8h52CP.jpg@webp"],
  ["Tenis Denim Preto Democrata", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/mRj5HmL.jpg@webp"],
  ["Sapatenis Masculino Preto Beat Pulse", 399.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/ShsucIw.webp@webp"],
  ["Sapato Social Masculino Preto Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/LYt5XHo.webp@webp"],
  ["Sapato Social Masculino Preto Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/1SFIZXg.webp@webp"],
  ["Sapato Social Masculino Preto Prime", 269.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/neKMyHr.webp@webp"],
  ["Tenis Masculino Preto Clay", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/bVGx0dO.webp@webp"],
  ["Tenis Masculino Preto", 349.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/QDT5k3A.webp@webp"],
  ["Sapato Casual Masculino Conhaque Leave", 289.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/tk0qZGE.jpg@webp"],
  ["Sapato Social Masculino Conhaque Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/fuv-0Sa.webp@webp"],
  ["Sapato Social Masculino Conhaque Type", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/z3VUd6t.webp@webp"],
  ["Sapatenis Conhaque Masculino", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/NkmFCQO.webp@webp"],
  ["Tenis Masculino Branco Brad Ultra Light", 399.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/dW2pVJ8.jpg@webp"],
  ["Tenis Denim Off White Democrata", 319.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/NM1pkA9.jpg@webp"],
  ["Tenis Masculino Branco Block", 329.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/2rEQ9Vd.webp@webp"],
  ["Sapato Masculino Rato Tulum", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/pSaMJQ7.jpg@webp"],
  ["Tenis Masculino Preto/Smoke", 299.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/y-dal2d.webp@webp"],
  ["Sapato Masculino Smoke Leave", 289.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/BZrOEqm.webp@webp"],
  ["Tenis Masculino Navy/Cinza Cloudy", 339.99, "https://static.stoqui.com.br/rs:fit:400:400/plain/product_images/d44a6db9-24ec-4462-9ef6-42b3b45d3bf6/Io6SPnM.webp@webp"]
].map((item, index) => {
  const [name, price, image] = item;
  return {
    id: index + 1,
    name,
    price,
    image,
    category: getCategory(name),
    gender: name.toLowerCase().includes("femin") ? "Feminino" : "Masculino",
    tone: getTone(name),
    sizes: getSizes(name)
  };
});

const filters = ["Todos", "Masculino", "Feminino", "Tenis", "Sapato", "Conhaque", "Preto"];
const formatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const WHATSAPP_PHONE = "";

let activeFilter = "Todos";
let activeProduct = null;
let activeSize = null;
let activeQty = 1;
let cart = JSON.parse(localStorage.getItem("mj-estima-cart") || "[]");
const cardSelections = {};

const grid = document.querySelector("#productGrid");
const filtersWrap = document.querySelector("#filters");
const searchInput = document.querySelector("#searchInput");
const sortSelect = document.querySelector("#sortSelect");
const productDialog = document.querySelector("#productDialog");
const productDialogContent = document.querySelector("#productDialogContent");
const cartDrawer = document.querySelector("#cartDrawer");
const cartItems = document.querySelector("#cartItems");
const cartCount = document.querySelector("#cartCount");
const cartSubtotal = document.querySelector("#cartSubtotal");
const checkoutButton = document.querySelector("#checkoutButton");
const orderNote = document.querySelector("#orderNote");

function getCategory(name) {
  const text = normalize(name);
  if (text.includes("sapatenis")) return "Sapatenis";
  if (text.includes("sapato")) return "Sapato";
  if (text.includes("sandalia") || text.includes("papete") || text.includes("rasteira") || text.includes("mocassim")) return "Feminino";
  return "Tenis";
}

function getTone(name) {
  const text = normalize(name);
  if (text.includes("preto") || text.includes("smoke")) return "Preto";
  if (text.includes("conhaque") || text.includes("tan") || text.includes("tabaco")) return "Conhaque";
  if (text.includes("branco") || text.includes("neve") || text.includes("off white")) return "Claro";
  return "Classico";
}

function getSizes(name) {
  return name.toLowerCase().includes("femin") || ["Rasteira", "Papete", "Mocassim", "Sandalia"].some(word => name.includes(word))
    ? [34, 35, 36, 37, 38, 39]
    : [38, 39, 40, 41, 42, 43, 44];
}

function normalize(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function matches(product) {
  const query = normalize(searchInput.value.trim());
  const haystack = normalize(`${product.name} ${product.category} ${product.gender} ${product.tone}`);
  const byQuery = !query || haystack.includes(query);
  const byFilter = activeFilter === "Todos"
    || product.gender === activeFilter
    || product.category === activeFilter
    || product.tone === activeFilter
    || normalize(product.name).includes(normalize(activeFilter));
  return byQuery && byFilter;
}

function getCardSelection(product) {
  if (!cardSelections[product.id]) {
    cardSelections[product.id] = {
      size: product.sizes[Math.floor(product.sizes.length / 2)],
      qty: 1
    };
  }
  return cardSelections[product.id];
}

function sortProducts(list) {
  const mode = sortSelect.value;
  return [...list].sort((a, b) => {
    if (mode === "low") return a.price - b.price;
    if (mode === "high") return b.price - a.price;
    if (mode === "az") return a.name.localeCompare(b.name, "pt-BR");
    return a.id - b.id;
  });
}

function renderFilters() {
  filtersWrap.innerHTML = filters.map(filter => `
    <button class="filter ${activeFilter === filter ? "active" : ""}" type="button" data-filter="${filter}">
      ${filter}
    </button>
  `).join("");

  filtersWrap.querySelectorAll(".filter").forEach(button => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.filter;
      renderFilters();
      renderProducts();
    });
  });
}

function renderProducts() {
  const list = sortProducts(products.filter(matches));
  grid.innerHTML = list.map(product => {
    const choice = getCardSelection(product);
    return `
      <article class="product-card">
        <button class="product-media" type="button" data-open-product="${product.id}" aria-label="Ver ${product.name}">
          <img src="${product.image}" alt="${product.name}" loading="lazy">
        </button>
        <div class="product-info">
          <span class="tag">${product.gender} / ${product.tone}</span>
          <h3>${product.name}</h3>
          <div class="price-row">
            <strong class="price">${formatter.format(product.price)}</strong>
            <span class="installment">pedido direto</span>
          </div>
          <div class="card-choice">
            <div class="mini-sizes" aria-label="Tamanhos de ${product.name}">
              ${product.sizes.map(size => `
                <button class="mini-size ${choice.size === size ? "active" : ""}" type="button" data-card-size="${product.id}:${size}">
                  ${size}
                </button>
              `).join("")}
            </div>
            <div class="mini-bottom">
              <div class="mini-qty" aria-label="Quantidade">
                <button type="button" data-card-qty="${product.id}:-1">-</button>
                <span>${choice.qty}</span>
                <button type="button" data-card-qty="${product.id}:1">+</button>
              </div>
              <button class="buy-link" type="button" data-add-fast="${product.id}">Adicionar a sacola</button>
            </div>
            <button class="card-open" type="button" data-open-product="${product.id}">Ver detalhes e tamanhos</button>
          </div>
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-open-product]").forEach(button => {
    button.addEventListener("click", () => openProduct(Number(button.dataset.openProduct)));
  });

  grid.querySelectorAll("[data-add-fast]").forEach(button => {
    button.addEventListener("click", () => {
      const product = products.find(item => item.id === Number(button.dataset.addFast));
      const choice = getCardSelection(product);
      addToCart(product, choice.size, choice.qty);
      openCart();
    });
  });

  grid.querySelectorAll("[data-card-size]").forEach(button => {
    button.addEventListener("click", () => {
      const [id, size] = button.dataset.cardSize.split(":").map(Number);
      const product = products.find(item => item.id === id);
      getCardSelection(product).size = size;
      renderProducts();
    });
  });

  grid.querySelectorAll("[data-card-qty]").forEach(button => {
    button.addEventListener("click", () => {
      const [id, amount] = button.dataset.cardQty.split(":").map(Number);
      const product = products.find(item => item.id === id);
      const choice = getCardSelection(product);
      choice.qty = Math.max(1, choice.qty + amount);
      renderProducts();
    });
  });
}

function openProduct(id) {
  activeProduct = products.find(item => item.id === id);
  if (!activeProduct) return;
  activeSize = activeProduct.sizes[0];
  activeQty = 1;
  renderProductDialog();
  productDialog.showModal();
}

function renderProductDialog() {
  productDialogContent.innerHTML = `
    <div class="product-detail">
      <div class="detail-media">
        <img src="${activeProduct.image}" alt="${activeProduct.name}">
      </div>
      <div class="detail-copy">
        <span class="tag">${activeProduct.gender} / ${activeProduct.category}</span>
        <h2>${activeProduct.name}</h2>
        <strong class="price">${formatter.format(activeProduct.price)}</strong>
        <p>Modelo selecionado para quem quer presenca sem exagero: visual limpo, tom elegante e conforto para acompanhar a rotina.</p>
        <div>
          <span class="tag">Tamanho</span>
          <div class="size-grid">
            ${activeProduct.sizes.map(size => `
              <button class="size-option ${activeSize === size ? "active" : ""}" type="button" data-size="${size}">
                ${size}
              </button>
            `).join("")}
          </div>
        </div>
        <div class="detail-actions">
          <div class="qty-control">
            <button class="qty-button" type="button" data-qty="-1">-</button>
            <span>${activeQty}</span>
            <button class="qty-button" type="button" data-qty="1">+</button>
          </div>
          <button class="button dark" type="button" data-add-detail>Adicionar a sacola</button>
        </div>
      </div>
    </div>
  `;

  productDialogContent.querySelectorAll("[data-size]").forEach(button => {
    button.addEventListener("click", () => {
      activeSize = Number(button.dataset.size);
      renderProductDialog();
    });
  });

  productDialogContent.querySelectorAll("[data-qty]").forEach(button => {
    button.addEventListener("click", () => {
      activeQty = Math.max(1, activeQty + Number(button.dataset.qty));
      renderProductDialog();
    });
  });

  productDialogContent.querySelector("[data-add-detail]").addEventListener("click", () => {
    addToCart(activeProduct, activeSize, activeQty);
    productDialog.close();
    openCart();
  });
}

function addToCart(product, size, qty) {
  const key = `${product.id}-${size}`;
  const current = cart.find(item => item.key === key);
  if (current) {
    current.qty += qty;
  } else {
    cart.push({ key, id: product.id, name: product.name, price: product.price, image: product.image, size, qty });
  }
  persistCart();
}

function removeFromCart(key) {
  cart = cart.filter(item => item.key !== key);
  persistCart();
}

function updateCartQty(key, amount) {
  const current = cart.find(item => item.key === key);
  if (!current) return;
  current.qty += amount;
  if (current.qty <= 0) {
    removeFromCart(key);
    return;
  }
  persistCart();
}

function persistCart() {
  localStorage.setItem("mj-estima-cart", JSON.stringify(cart));
  renderCart();
}

function renderCart() {
  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  cartCount.textContent = totalQty;
  cartSubtotal.textContent = formatter.format(subtotal);

  if (!cart.length) {
    cartItems.innerHTML = `<p class="empty-cart">Sua sacola ainda esta vazia. Escolha um modelo da colecao para montar o pedido.</p>`;
    checkoutButton.setAttribute("href", "#colecao");
    checkoutButton.textContent = "Escolher calcado";
    return;
  }

  cartItems.innerHTML = cart.map(item => `
    <article class="cart-line">
      <img src="${item.image}" alt="${item.name}">
      <div>
        <h3>${item.name}</h3>
        <p>Tam. ${item.size} / ${item.qty} un. / ${formatter.format(item.price * item.qty)}</p>
      </div>
      <div class="cart-line-actions">
        <div class="cart-qty" aria-label="Quantidade de ${item.name}">
          <button type="button" data-cart-qty="${item.key}:-1">-</button>
          <span>${item.qty}</span>
          <button type="button" data-cart-qty="${item.key}:1">+</button>
        </div>
        <button class="remove-line" type="button" data-remove="${item.key}" aria-label="Remover ${item.name}">x</button>
      </div>
    </article>
  `).join("");

  cartItems.querySelectorAll("[data-cart-qty]").forEach(button => {
    button.addEventListener("click", () => {
      const [key, amount] = button.dataset.cartQty.split(":");
      updateCartQty(key, Number(amount));
    });
  });

  cartItems.querySelectorAll("[data-remove]").forEach(button => {
    button.addEventListener("click", () => removeFromCart(button.dataset.remove));
  });

  checkoutButton.textContent = "Finalizar pedido";
  checkoutButton.setAttribute("href", buildCheckoutUrl(subtotal));
}

function buildCheckoutUrl(subtotal) {
  const lines = cart.map(item => `- ${item.qty}x ${item.name} tam. ${item.size} (${formatter.format(item.price * item.qty)})`);
  const note = orderNote.value.trim();
  const message = [
    "Ola, MJ Estima. Quero finalizar este pedido:",
    ...lines,
    `Subtotal: ${formatter.format(subtotal)}`,
    note ? `Observacao: ${note}` : "",
    "",
    "Pode me passar pagamento e entrega?"
  ].filter(Boolean).join("\n");
  const phonePart = WHATSAPP_PHONE ? `phone=${WHATSAPP_PHONE}&` : "";
  return `whatsapp://send?${phonePart}text=${encodeURIComponent(message)}`;
}

function openCart() {
  cartDrawer.classList.add("open");
  cartDrawer.setAttribute("aria-hidden", "false");
}

function closeCart() {
  cartDrawer.classList.remove("open");
  cartDrawer.setAttribute("aria-hidden", "true");
}

document.querySelectorAll("[data-open-cart]").forEach(button => button.addEventListener("click", openCart));
document.querySelector("[data-close-cart]").addEventListener("click", closeCart);
document.querySelector("[data-close-product]").addEventListener("click", () => productDialog.close());
document.querySelector("[data-featured-buy]").addEventListener("click", () => {
  const featured = products.find(product => product.name === "Sapato Casual Masculino Conhaque Leave");
  addToCart(featured, 40, 1);
  openCart();
});

cartDrawer.addEventListener("click", event => {
  if (event.target === cartDrawer) closeCart();
});

document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeCart();
});

searchInput.addEventListener("input", renderProducts);
sortSelect.addEventListener("change", renderProducts);
orderNote.addEventListener("input", renderCart);

renderFilters();
renderProducts();
renderCart();
