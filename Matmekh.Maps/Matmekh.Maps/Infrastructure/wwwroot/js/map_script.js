let isKuibysheva = false;
let isMatmeh     = false;
let routePoints  = null;
let pendingFocus = null;

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
  const rawFloor       = localStorage.getItem("routeStartFloor");
  const savedFloorKey  = rawFloor ? String(rawFloor).trim() : null;


  isKuibysheva = !!document.getElementById("goRouteK");
  isMatmeh     = !!document.getElementById("goRouteM");
                              


  if (floorSelect) {
    if (isKuibysheva) {
      const kuibMap = {
        "1":  "1 этаж",
        "3":  "3 этаж",
        "1k": "1 этаж контуровские классы",
        "2k": "2 этаж контуровские классы",
        "2":  "2 этаж контуровские классы"
      };

      const mapped = savedFloorKey ? kuibMap[savedFloorKey] : null;
      if (mapped) {
        floorSelect.value = mapped;
      }

    } else {
      let desiredDigit = "5"; 
      if (savedFloorKey && /^\d+$/.test(savedFloorKey)) {
        desiredDigit = savedFloorKey; 
      }

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
  
  if (isKuibysheva) {
    initKuibyshevaMap();
  } else {
    initMatmehMap();
  }
  
  const rawRoute = localStorage.getItem("routePoints");
  if (rawRoute) {
    try {
      const points = JSON.parse(rawRoute);
      if (Array.isArray(points) && points.length) {
        routePoints = points;          
        updateRouteForCurrentFloor();   
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


function initMatmehMap() {
  const floorSelect = document.getElementById("floorSelect");
  const floorLabel  = document.getElementById("floorLabel");

  const svg      = document.getElementById("mySvgContainer");
  const floorMap = document.getElementById("floorMap");

  const zoomInBtn  = document.getElementById("zoomInBtn");
  const zoomOutBtn = document.getElementById("zoomOutBtn");

  if (!floorSelect || !floorLabel || !svg || !floorMap || !zoomInBtn || !zoomOutBtn) {
    console.warn("initMatmehMap: какие-то элементы не найдены");
    return;
  }

  const floorImages = {
    "5": "images/floor5.png",
    "6": "images/floor6.png"
  }; 

  let scale     = 0.5;
  let MIN_SCALE = 0.25;
  const MAX_SCALE = 3;
  const STEP     = 0.25;

  let baseW = 1000;
  let baseH = 1000;

  function applyScale() {
    svg.style.width  = `${baseW * scale}px`;
    svg.style.height = `${baseH * scale}px`;
  }

  function loadFloor(value) {
    console.log(value);
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
    updateRouteForCurrentFloor();
  });
}


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
    "1 этаж": "images/1floor_k.png",
    "3 этаж": "images/3floor_k.jpg",
    "2 этаж контуровские классы": "images/2floor_k_k.png",
    "1 этаж контуровские классы": "images/1floor_k_k.png"
  };

  let scale     = 0.25;
  let MIN_SCALE = 0.25;
  const MAX_SCALE = 3;
  const STEP     = 0.25;

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
        scale    = 0.2;
        MIN_SCALE = 0.2;
      } else {
        scale    = 0.7;
        MIN_SCALE = 0.25;
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
    updateRouteForCurrentFloor();
  });
}


function getCurrentFloorSuffix() {
  const floorSelect = document.getElementById("floorSelect");
  if (!floorSelect) return null;

  const value = floorSelect.value || "";
  const text  = floorSelect.options[floorSelect.selectedIndex]
      ?.textContent?.trim() || value;

  if (isKuibysheva) {
    if (value.startsWith("1 этаж контуров")) return "1k";
    if (value.startsWith("2 этаж контуров")) return "2k";

    if (value.startsWith("1 этаж")) return "1";
    if (value.startsWith("3 этаж")) return "3";
    
    if (/^1.*контуров/i.test(text)) return "1k";
    if (/^2.*контуров/i.test(text)) return "2k";
    if (/^1 этаж\b/.test(text))     return "1";
    if (/^3 этаж\b/.test(text))     return "3";

    return null;
  } else {
    const m = (value || text).match(/\d+/);
    return m ? m[0] : null; 
  }
}

function setFloorBySuffix(suffix) {
  const floorSelect = document.getElementById("floorSelect");
  if (!floorSelect) return;

  if (isKuibysheva) {
    const map = {
      "1":  "1 этаж",
      "3":  "3 этаж",
      "1k": "1 этаж контуровские классы",
      "2k": "2 этаж контуровские классы",
      "2":  "2 этаж контуровские классы"
    };
    const val = map[String(suffix)];
    if (!val) return;
    floorSelect.value = val;
  } else {
    floorSelect.value = String(suffix); 
  }

  floorSelect.dispatchEvent(new Event("change", { bubbles: true }));
}

function focusOnSvgPoint(point) {
  const svg = document.getElementById("mySvgContainer");
  const scrollBox = document.querySelector(".map-wrapper");

  if (!svg || !scrollBox || !point) return;

  const x = point.X ?? point.x;
  const y = point.Y ?? point.y;
  if (x == null || y == null) return;

  const pt = svg.createSVGPoint();
  pt.x = x; pt.y = y;

  const ctm = svg.getScreenCTM();
  if (!ctm) return;

  const screen = pt.matrixTransform(ctm);
  const rect = scrollBox.getBoundingClientRect();

  const left = scrollBox.scrollLeft + (screen.x - rect.left) - scrollBox.clientWidth / 2;
  const top  = scrollBox.scrollTop  + (screen.y - rect.top)  - scrollBox.clientHeight / 2;

  scrollBox.scrollTo({ left, top, behavior: "smooth" });
}

function updateRouteForCurrentFloor() {
  console.log("=== routePoints ===", routePoints);
  const routeLayer  = document.getElementById("routeLayer");
  const floorSelect = document.getElementById("floorSelect");
  routeLayer.innerHTML = ""
  if (!routeLayer || !floorSelect || !Array.isArray(routePoints) || routePoints.length < 2) {
    console.log("updateRouteForCurrentFloor: нет routeLayer / floorSelect / routePoints");
    return;
  }

  const floorSuffix = getCurrentFloorSuffix(); 
  if (!floorSuffix) return;

  const anyFloorPoint = routePoints.find(p => p && (p.Floor != null || p.floor != null));
  if (!anyFloorPoint) return;

  const prefix = String(anyFloorPoint.Floor ?? anyFloorPoint.floor).split("_")[0];
  const floorCode = `${prefix}_${floorSuffix}`;

  const segments = [];
  let lastCode = null;

  for (const p of routePoints) {
    const code = String(p.Floor ?? p.floor ?? "");
    const x = p.X ?? p.x;
    const y = p.Y ?? p.y;
    if (!code || x == null || y == null) continue;

    if (code !== lastCode) {
      const parts = code.split("_");
      segments.push({
        floorCode: code,
        suffix: parts[1] ?? parts[0],
        points: []
      });
      lastCode = code;
    }
    segments[segments.length - 1].points.push({ X: x, Y: y, Floor: code });
  }

  const idx = segments.findIndex(s => s.floorCode === floorCode);
  if (idx < 0) {
    console.log("updateRouteForCurrentFloor: сегмент этажа не найден", floorCode);
    return;
  }

  const seg = segments[idx];
  if (!seg.points || seg.points.length < 2) return;
  
  let prevSeg = null;
  for (let i = idx - 1; i >= 0; i--) {
    const s = segments[i];
    if (s.suffix === "2k" && s.points.length === 1) {
      continue;
    }
    prevSeg = s;
    break;
  }
  
  let nextSeg = null;
  for (let i = idx + 1; i < segments.length; i++) {
    const s = segments[i];
    if (s.suffix === "2k" && s.points.length === 1) {
      continue;
    }
    nextSeg = s;
    break;
  }


  let onEndClick = null;
  if (nextSeg && nextSeg.points && nextSeg.points.length) {
    onEndClick = () => {
      pendingFocus = { floorCode: nextSeg.floorCode, point: nextSeg.points[0] };
      setFloorBySuffix(nextSeg.suffix);
    };
  }


  let onStartClick = null;
  if (prevSeg && prevSeg.points && prevSeg.points.length) {
    const lastPrevPoint = prevSeg.points[prevSeg.points.length - 1];
    onStartClick = () => {
      pendingFocus = { floorCode: prevSeg.floorCode, point: lastPrevPoint };
      setFloorBySuffix(prevSeg.suffix);
    };
  }

  drawRoute(seg.points, { onEndClick, onStartClick });


  
  if (pendingFocus && pendingFocus.floorCode === floorCode) {
    const p = pendingFocus.point;
    pendingFocus = null;
    requestAnimationFrame(() => focusOnSvgPoint(p));
  }
}
