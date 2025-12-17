let isKuibysheva = false;
let isMatmeh = false;
let routePoints = null;  

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Подтягиваем меню
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

  // 2. Читаем сохранённый этаж старта (цифру)
  const raw = localStorage.getItem("routeStartFloor");
  let savedDigit = null;
  if (raw) {
    const m = String(raw).match(/\d/);
    if (m) savedDigit = m[0]; // "1","2","3","5","6"
  }

  // 3. Определяем кампус по DOM
  isKuibysheva = !!document.getElementById("mySvgContainer");
  isMatmeh     = !isKuibysheva;

  // 4. Выставляем значение select
  if (floorSelect) {
    if (isKuibysheva) {
      const valueMap = {
        "1": "1 этаж",
        "2": "2 этаж контуровские классы",
        "3": "3 этаж"
      };
      const mapped = savedDigit ? valueMap[savedDigit] : null;
      if (mapped) {
        floorSelect.value = mapped;
      }
      // если нет сохранённого – остаётся дефолт из HTML
    } else {
      const desiredDigit = savedDigit || "5"; // по умолчанию 5 этаж
      let targetOption = null;

      for (const opt of floorSelect.options) {
        const txt = opt.textContent.trim();
        if (txt.startsWith(desiredDigit)) {
          targetOption = opt;
          break;
        }
      }
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

  // 6. Забираем маршрут и сохраняем его в routePoints
  const rawRoute = localStorage.getItem("routePoints");
  if (rawRoute) {
    try {
      const points = JSON.parse(rawRoute);
      if (Array.isArray(points) && points.length) {
        routePoints = points;      // храним весь путь
        updateRouteForCurrentFloor(); // рисуем только текущий этаж
      }
    } catch (e) {
      console.error("Ошибка чтения маршрута", e);
    } finally {
      // можно очистить, т.к. копия уже лежит в routePoints
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

/* ========= МАТМЕХ ========= */

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

    const opt = floorSelect.querySelector(`option[value="${value}"]`);
    const labelText = opt ? opt.textContent.trim() : value;

    if (floorLabel) {
      floorLabel.textContent = labelText;
    }
    if (floorMap) {
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
      updateRouteForCurrentFloor();   // ПЕРЕРИСОВАТЬ маршрут под новый этаж
    });
  }
}

/* ========= КУЙБЫШЕВА ========= */

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
    updateRouteForCurrentFloor();   // ПЕРЕРИСОВАТЬ маршрут
  });
}

/* ========= ОБЩАЯ ФУНКЦИЯ ДЛЯ МАРШРУТА ПО ЭТАЖУ ========= */

function updateRouteForCurrentFloor() {
  const routeLayer  = document.getElementById("routeLayer");
  const floorSelect = document.getElementById("floorSelect");

  if (!routeLayer || !floorSelect || !Array.isArray(routePoints) || routePoints.length < 2) {
    console.log("updateRouteForCurrentFloor: нет routeLayer / floorSelect / routePoints");
    return;
  }

  // очищаем слой маршрута
  routeLayer.innerHTML = "";

  // --- 1. Достаём цифру этажа из value ИЛИ из текста option ---
  const rawValue = String(floorSelect.value || "");
  const textValue = floorSelect.options[floorSelect.selectedIndex]
      ?.textContent?.trim() || "";

  const digitFromValue = rawValue.match(/\d/)?.[0] || null;
  const digitFromText  = textValue.match(/\d/)?.[0] || null;

  const digit = digitFromValue || digitFromText;
  if (!digit) {
    console.log("updateRouteForCurrentFloor: не нашли цифру этажа", { rawValue, textValue });
    return;
  }

  // --- 2. Берём префикс здания из самого маршрута ---
  const anyFloorPoint = routePoints.find(p => p && (p.Floor != null || p.floor != null));
  if (!anyFloorPoint) {
    console.log("updateRouteForCurrentFloor: в routePoints нет поля Floor", routePoints);
    return;
  }

  const floorField = String(anyFloorPoint.Floor ?? anyFloorPoint.floor); // "matmeh_6"
  const prefix = floorField.split("_")[0];                               // "matmeh" / "kuibysheva"
  const floorCode = `${prefix}_${digit}`;                                // "matmeh_6" или "matmeh_5"

  // --- 3. Фильтруем точки только этого этажа ---
  const pointsForFloor = routePoints.filter(p => {
    const code = String(p.Floor ?? p.floor);
    return code === floorCode;
  });

  console.log("updateRouteForCurrentFloor:", {
    rawValue,
    textValue,
    digit,
    floorField,
    prefix,
    floorCode,
    allFloors: [...new Set(routePoints.map(p => String(p.Floor ?? p.floor)))],
    count: pointsForFloor.length
  });

  if (pointsForFloor.length < 2) {
    console.log("updateRouteForCurrentFloor: для", floorCode, "мало точек, ничего не рисуем");
    return;
  }

  // --- 4. Рисуем только точки текущего этажа ---
  drawRoute(pointsForFloor);
}