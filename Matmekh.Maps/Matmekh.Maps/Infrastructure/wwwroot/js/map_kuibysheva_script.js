document.addEventListener("DOMContentLoaded", async () => {
    const resp = await fetch("menu.html");
    const menuHtml = await resp.text();

    const placeholder = document.getElementById("menu-placeholder");
    placeholder.innerHTML = menuHtml;

    initMenu();
    initMap();
});

function initMenu() {
    function activateMenu(e) {
        e.stopPropagation();
        const menu = document.getElementById("myMenu");
        menu.classList.toggle("active");
    }

    const menu = document.getElementById("myMenu");
    const panel = menu.querySelector(".menu-panel");
    const burgerBtn = document.getElementById("burgerBtn");

    burgerBtn.addEventListener("click", activateMenu);

    panel.addEventListener("click", e => e.stopPropagation());
    menu.addEventListener("click", () => menu.classList.remove("active"));
}

function initMap() {
  const floorSelect = document.getElementById("floorSelect");
  const floorLabel = document.getElementById("floorLabel");

  const svg = document.getElementById("mySvgContainer");
  const floorMap = document.getElementById("floorMap");

  const zoomInBtn = document.getElementById("zoomInBtn");
  const zoomOutBtn = document.getElementById("zoomOutBtn");

  const floorImages = {
    "1 этаж": "images/enter_k.jpg",
    "3 этаж": "images/3floor_k.jpg",
    "2 этаж контуровские классы": "images/second_k_k.jpg",
    "1 этаж контуровские классы": "images/first_k_k.jpg"
  };

  let scale = 1;
  let MIN_SCALE = 0.5;
  const MAX_SCALE = 3;
  const STEP = 0.05;

  // базовый (натуральный) размер текущей картинки
  let baseW = 1000;
  let baseH = 1000;

  function applyScale() {
    svg.style.width = `${baseW * scale}px`;
    svg.style.height = `${baseH * scale}px`;
  }

  function loadFloor(value) {
    const src = floorImages[value];
    floorLabel.textContent = value;

    // грузим картинку, чтобы узнать naturalWidth/naturalHeight
    const img = new Image();
    img.onload = () => {
      baseW = img.naturalWidth;
      baseH = img.naturalHeight;

      // viewBox = координатная система под реальный размер картинки
      svg.setAttribute("viewBox", `0 0 ${baseW} ${baseH}`);

      // В SVG <image> размеры задаются через width/height
      floorMap.setAttribute("href", src);
      floorMap.setAttribute("x", "0");
      floorMap.setAttribute("y", "0");
      floorMap.setAttribute("width", baseW);
      floorMap.setAttribute("height", baseH);

      // начальный масштаб под этаж
      if (value === "3 этаж") {
        scale = 0.2;
        MIN_SCALE = 0.2;
      } else {
        scale = 0.7;
        MIN_SCALE = 0.7;
      }

      applyScale();
    };
    img.src = src;
  }

  loadFloor(floorSelect.value);

  zoomInBtn.addEventListener("click", () => {
    scale = Math.min(MAX_SCALE, scale + STEP);
    applyScale();
  });

  zoomOutBtn.addEventListener("click", () => {
    scale = Math.max(MIN_SCALE, scale - STEP);
    applyScale();
  });

  floorSelect.addEventListener("change", () => {
    loadFloor(floorSelect.value);
  });
}
