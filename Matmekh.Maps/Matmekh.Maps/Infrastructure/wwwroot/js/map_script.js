document.addEventListener("DOMContentLoaded", async () => {
  try {
    const resp = await fetch("menu.html");
    if (resp.ok) {
      const menuHtml = await resp.text();
      const placeholder = document.getElementById("menu-placeholder");
      if (placeholder) {
        placeholder.innerHTML = menuHtml;
      }
      initMenuIfExists();
    } else {
      console.warn("menu.html не загрузился:", resp.status);
    }
  } catch (e) {
    console.warn("Ошибка загрузки menu.html", e);
  }

  const floorSelect = document.getElementById("floorSelect");


  const raw = localStorage.getItem("routeStartFloor");
  let savedDigit = null;
  if (raw) {
    const m = String(raw).match(/\d/);
    if (m) savedDigit = m[0];
  }

  // 3. Определяем, какая страница: матмех или Куйбышева
  const isKuibysheva = !!document.getElementById("mySvgContainer");
  const isMatmeh     = !isKuibysheva;

  // 4. Выставляем значение select в зависимости от кампуса
  if (floorSelect) {
    if (isKuibysheva) {
      // Куйбышева – value совпадает с текстом
      const valueMap = {
        "1": "1 этаж",
        "2": "2 этаж контуровские классы",
        "3": "3 этаж"
      };
      const mapped = savedDigit ? valueMap[savedDigit] : null;
      if (mapped) {
        floorSelect.value = mapped;
      }
      // если нет сохранённого – оставляем то, что в HTML
    } else {
      // МАТМЕХ: ищем опцию, где текст начинается с цифры (5 или 6)
      const desiredDigit = savedDigit || "5"; // дефолт – 5 этаж
      let targetOption = null;

      for (const opt of floorSelect.options) {
        const txt = opt.textContent.trim();
        if (txt.startsWith(desiredDigit)) {
          targetOption = opt;
          break;
        }
      }

      // если нашли – ставим её, иначе берём первую "нормальную" опцию с цифрой
      if (targetOption) {
        floorSelect.value = targetOption.value;
      } else {
        const firstReal = Array.from(floorSelect.options)
            .find(o => /\d/.test(o.textContent));
        if (firstReal) {
          floorSelect.value = firstReal.value;
        }
      }
    }
  }

  // 5. Инициализируем карту
  if (isKuibysheva) {
    initKuibyshevaMap();
  } else {
    initMatmehMap();
  }

  // 6. Если есть сохранённый маршрут — рисуем его
  const rawRoute = localStorage.getItem("routePoints");
  if (rawRoute) {
    try {
      const points = JSON.parse(rawRoute);
      if (Array.isArray(points) && points.length) {
        drawRoute(points); // рисует в #routeLayer
      }
    } catch (e) {
      console.error("Ошибка чтения маршрута", e);
    } finally {
      localStorage.removeItem("routePoints");
    }
  }
});

function initMenuIfExists() {
  const menu      = document.getElementById("myMenu");
  const burgerBtn = document.getElementById("burgerBtn");
  if (!menu || !burgerBtn) return;

  const panel = menu.querySelector(".menu-panel");

  function activateMenu(e) {
    e.stopPropagation();
    menu.classList.toggle("active");
  }

  burgerBtn.addEventListener("click", activateMenu);

  if (panel) {
    panel.addEventListener("click", e => e.stopPropagation());
  }
  menu.addEventListener("click", () => menu.classList.remove("active"));
}

/* --------- МАТМЕХ --------- */

function initMatmehMap() {
  const floorSelect = document.getElementById("floorSelect");
  const floorLabel  = document.getElementById("floorLabel");
  const floorMap    = document.getElementById("floorMap");

  const mapInner    = document.getElementById("mapInner");
  const zoomInBtn   = document.getElementById("zoomInBtn");
  const zoomOutBtn  = document.getElementById("zoomOutBtn");

  const floorImages = {
    "5": "images/floor5.png",
    "6": "images/floor6.png"
  };

  const applyFloor = (value) => {
    if (!floorSelect) return;

    // берём красивый текст из option
    const opt = floorSelect.querySelector(`option[value="${value}"]`);
    const labelText = opt ? opt.textContent.trim() : value;

    if (floorLabel) {
      floorLabel.textContent = labelText;
    }
    if (floorMap) {
      // value может быть '5' или '6', картинку выбираем по цифре
      const digit = labelText.match(/\d/)?.[0] ?? value;
      const src   = floorImages[digit];
      if (src) {
        floorMap.src = src;
        floorMap.alt = "";
      } else {
        floorMap.src = "";
        floorMap.alt = "Карта не найдена";
      }
    }
  };

  if (floorSelect) {
    applyFloor(floorSelect.value);
  }

  if (mapInner && zoomInBtn && zoomOutBtn) {
    let scale = 0.25;
    const MIN_SCALE = 0.25;
    const MAX_SCALE = 3;
    const STEP = 0.25;

    const applyScale = () => {
      mapInner.style.transform = `scale(${scale})`;
    };

    applyScale();

    zoomInBtn.addEventListener("click", () => {
      scale = Math.min(MAX_SCALE, scale + STEP);
      applyScale();
    });

    zoomOutBtn.addEventListener("click", () => {
      scale = Math.max(MIN_SCALE, scale - STEP);
      applyScale();
    });
  }

  if (floorSelect) {
    floorSelect.addEventListener("change", () => {
      applyFloor(floorSelect.value);

      const routeLayer = document.getElementById("routeLayer");
      if (routeLayer) {
        routeLayer.innerHTML = "";
      }
    });
  }
}

/* --------- КУЙБЫШЕВА --------- */

function initKuibyshevaMap() {
  const floorSelect = document.getElementById("floorSelect");
  const floorLabel  = document.getElementById("floorLabel");

  const svg      = document.getElementById("mySvgContainer");
  const floorMap = document.getElementById("floorMap");

  const zoomInBtn  = document.getElementById("zoomInBtn");
  const zoomOutBtn = document.getElementById("zoomOutBtn");

  if (!floorSelect || !floorLabel || !svg || !floorMap || !zoomInBtn || !zoomOutBtn) {
    console.warn("initKuibyshevaMap: какие-то элементы не найдены");
    return;
  }

  const floorImages = {
    "1 этаж": "images/enter_k.jpg",
    "3 этаж": "images/3floor_k.jpg",
    "2 этаж контуровские классы": "images/second_k_k.jpg",
    "1 этаж контуровские классы": "images/first_k_k.jpg"
  };

  let scale     = 1;
  let MIN_SCALE = 0.5;
  const MAX_SCALE = 3;
  const STEP     = 0.05;

  let baseW = 1000;
  let baseH = 1000;

  function applyScale() {
    svg.style.width  = `${baseW * scale}px`;
    svg.style.height = `${baseH * scale}px`;
  }

  function loadFloor(value) {
    const src = floorImages[value];
    if (!src) return;

    floorLabel.textContent = value;

    const img = new Image();
    img.onload = () => {
      baseW = img.naturalWidth;
      baseH = img.naturalHeight;

      svg.setAttribute("viewBox", `0 0 ${baseW} ${baseH}`);

      floorMap.setAttribute("href", src);
      floorMap.setAttribute("x", "0");
      floorMap.setAttribute("y", "0");
      floorMap.setAttribute("width", baseW);
      floorMap.setAttribute("height", baseH);

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

    const routeLayer = document.getElementById("routeLayer");
    if (routeLayer) {
      routeLayer.innerHTML = "";
    }
  });
}