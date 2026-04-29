const categories = [
  { id: "todos", label: "Todos" },
  { id: "negocios", label: "Negocios" },
  { id: "podcast", label: "Podcast" },
  { id: "live", label: "Live" },
  { id: "fitness", label: "Fitness" },
  { id: "beleza", label: "Beleza" },
  { id: "educacao", label: "Educacao" }
];

const categoryCycle = ["negocios", "podcast", "live", "negocios", "fitness", "beleza", "educacao"];
const titleMap = {
  negocios: "Corte de autoridade",
  podcast: "Corte de podcast",
  live: "Corte de live",
  fitness: "Conteudo fitness",
  beleza: "Conteudo beleza",
  educacao: "Corte educativo"
};

const videos = Array.from({ length: 23 }, (_, index) => {
  const n = String(index + 1).padStart(2, "0");
  const category = categoryCycle[index % categoryCycle.length];
  return {
    id: `zion-${n}`,
    title: `${titleMap[category]} ${n}`,
    category,
    src: `assets/videos/zion-${n}.mp4`,
    thumb: `assets/thumbs/zion-${n}.jpg`
  };
});

const filterBar = document.querySelector("#filterBar");
const videoGrid = document.querySelector("#videoGrid");
const progress = document.querySelector(".progress span");
const modal = document.querySelector("#videoModal");
const modalVideo = document.querySelector("#modalVideo");
const modalClose = document.querySelector("#modalClose");
let activeCategory = "todos";

function renderFilters() {
  filterBar.innerHTML = categories.map(cat => (
    `<button type="button" data-filter="${cat.id}" class="${cat.id === activeCategory ? "active" : ""}">${cat.label}</button>`
  )).join("");
  filterBar.querySelectorAll("button").forEach(button => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.filter;
      renderFilters();
      renderVideos();
    });
  });
}

function renderVideos() {
  const list = activeCategory === "todos" ? videos : videos.filter(video => video.category === activeCategory);
  videoGrid.innerHTML = list.map(video => `
    <article class="video-card" data-video="${video.id}" tabindex="0" role="button" aria-label="Assistir ${video.title}">
      <img src="${video.thumb}" alt="${video.title}" loading="lazy">
      <div class="video-info">
        <small>${categoryLabel(video.category)}</small>
        <strong>${video.title}</strong>
      </div>
      <span class="play">▶</span>
    </article>
  `).join("");

  const cards = videoGrid.querySelectorAll(".video-card");
  cards.forEach((card, index) => {
    const video = list.find(item => item.id === card.dataset.video);
    card.addEventListener("click", () => openVideo(video));
    card.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openVideo(video);
      }
    });
    requestAnimationFrame(() => {
      setTimeout(() => card.classList.add("show"), Math.min(index, 8) * 55);
    });
  });
}

function categoryLabel(id) {
  return categories.find(cat => cat.id === id)?.label || "Portfolio";
}

function openVideo(video) {
  if (!video) return;
  modalVideo.src = video.src;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  modalVideo.play().catch(() => {});
}

function closeVideo() {
  modalVideo.pause();
  modalVideo.removeAttribute("src");
  modalVideo.load();
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function updateProgress() {
  const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
  progress.style.transform = `scaleX(${Math.min(1, scrollY / max)})`;
}

modalClose.addEventListener("click", closeVideo);
modal.addEventListener("click", event => {
  if (event.target === modal) closeVideo();
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && !modal.classList.contains("hidden")) closeVideo();
});
addEventListener("scroll", updateProgress, { passive: true });
addEventListener("resize", updateProgress, { passive: true });

renderFilters();
renderVideos();
updateProgress();
