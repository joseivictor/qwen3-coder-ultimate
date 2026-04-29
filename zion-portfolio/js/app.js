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
  negocios: "Corte",
  podcast: "Corte",
  live: "Corte",
  fitness: "Corte",
  beleza: "Corte",
  educacao: "Corte"
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
const prevVideos = document.querySelector("#prevVideos");
const nextVideos = document.querySelector("#nextVideos");
const heroVideo = document.querySelector(".hero-visual video");
const audioToggle = document.querySelector(".audio-toggle");
let activeCategory = "todos";
let carouselTimer = null;
let carouselSegment = 0;
let isLoopAdjusting = false;

if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}
let initialScrollLocked = true;
function forceTop() {
  window.scrollTo(0, 0);
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
}
forceTop();
document.addEventListener("DOMContentLoaded", forceTop);
window.addEventListener("load", () => {
  forceTop();
  setTimeout(forceTop, 80);
  setTimeout(() => {
    forceTop();
    initialScrollLocked = false;
  }, 320);
});
window.addEventListener("hashchange", () => {
  if (initialScrollLocked) forceTop();
});

function renderFilters() {
  if (!filterBar) return;
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
  const loopList = [...list, ...list, ...list];
  videoGrid.innerHTML = loopList.map(video => `
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
  requestAnimationFrame(() => {
    carouselSegment = videoGrid.scrollWidth / 3;
    videoGrid.scrollTo({ left: carouselSegment, behavior: "auto" });
  });
  restartCarousel();
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
  if (!progress) return;
  const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
  progress.style.transform = `scaleX(${Math.min(1, scrollY / max)})`;
}

function scrollPortfolio(direction = 1) {
  if (!videoGrid) return;
  const card = videoGrid.querySelector(".video-card");
  if (!card) return;
  const step = card.getBoundingClientRect().width + 16;
  videoGrid.scrollBy({ left: step * direction, behavior: "smooth" });
}

function normalizeCarouselLoop() {
  if (!videoGrid || !carouselSegment || isLoopAdjusting) return;
  const left = videoGrid.scrollLeft;
  if (left < carouselSegment * 0.35 || left > carouselSegment * 1.65) {
    isLoopAdjusting = true;
    videoGrid.scrollTo({ left: left < carouselSegment ? left + carouselSegment : left - carouselSegment, behavior: "auto" });
    requestAnimationFrame(() => { isLoopAdjusting = false; });
  }
}

function restartCarousel() {
  if (carouselTimer) clearInterval(carouselTimer);
  carouselTimer = setInterval(() => scrollPortfolio(1), 4200);
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

document.querySelectorAll("[data-service]").forEach(button => {
  button.addEventListener("click", () => {
    activeCategory = button.dataset.service || "todos";
    document.querySelectorAll("[data-service]").forEach(item => item.classList.toggle("active", item === button));
    renderVideos();
    document.querySelector("#portfolio")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

prevVideos?.addEventListener("click", () => {
  scrollPortfolio(-1);
  restartCarousel();
});
nextVideos?.addEventListener("click", () => {
  scrollPortfolio(1);
  restartCarousel();
});
videoGrid?.addEventListener("scroll", normalizeCarouselLoop, { passive: true });

audioToggle?.addEventListener("click", () => {
  if (!heroVideo) return;
  const shouldEnable = heroVideo.muted;
  heroVideo.muted = !shouldEnable;
  heroVideo.volume = shouldEnable ? 1 : 0;
  audioToggle.classList.toggle("is-on", shouldEnable);
  audioToggle.textContent = shouldEnable ? "Audio ligado" : "Ouvir audio";
  heroVideo.play().catch(() => {});
});

document.querySelectorAll("video[autoplay]").forEach(video => {
  video.muted = true;
  video.play().catch(() => {});
});

renderFilters();
renderVideos();
updateProgress();
