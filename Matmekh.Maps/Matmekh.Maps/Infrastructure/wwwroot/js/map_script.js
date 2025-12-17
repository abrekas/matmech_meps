let isKuibysheva = false;
let isMatmeh     = false;
let routePoints  = null;


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


  isKuibysheva = !!document.getElementById("mySvgContainer"); 
  isMatmeh     = !isKuibysheva;                               


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

    const opt       = floorSelect.querySelector(`option[value="${value}"]`);
    const labelText = opt ? opt.textContent.trim() : value;

    if (floorLabel) {
      floorLabel.textContent = labelText;
    }
    if (floorMap) {
      const digitMatch = labelText.match(/\d+/);
      const digit      = digitMatch ? digitMatch[0] : value; 
      const src        = floorImages[digit];

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
    let scale       = 0.25;
    const MIN_SCALE = 0.25;
    const MAX_SCALE = 3;
    const STEP      = 0.25;

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
      updateRouteForCurrentFloor();   
    });
  }
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
        scale    = 0.2;
        MIN_SCALE = 0.2;
      } else {
        scale    = 0.7;
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


function updateRouteForCurrentFloor() {
  const routeLayer  = document.getElementById("routeLayer");
  const floorSelect = document.getElementById("floorSelect");

  if (!routeLayer || !floorSelect || !Array.isArray(routePoints) || routePoints.length < 2) {
    console.log("updateRouteForCurrentFloor: нет routeLayer / floorSelect / routePoints");
    return;
  }
  
  routeLayer.innerHTML = "";

  const floorSuffix = getCurrentFloorSuffix(); // "5","6","1","3","1k","2k"
  if (!floorSuffix) {
    console.log("updateRouteForCurrentFloor: не удалось определить суффикс этажа");
    return;
  }
  
  const anyFloorPoint = routePoints.find(
      p => p && (p.Floor != null || p.floor != null)
  );
  if (!anyFloorPoint) {
    console.log("updateRouteForCurrentFloor: в routePoints нет поля Floor", routePoints);
    return;
  }

  const floorField = String(anyFloorPoint.Floor ?? anyFloorPoint.floor); 
  const prefix     = floorField.split("_")[0];                           
  const floorCode  = `${prefix}_${floorSuffix}`;                         

  const pointsForFloor = routePoints.filter(p =>
      String(p.Floor ?? p.floor) === floorCode
  );

  console.log("updateRouteForCurrentFloor:", {
    floorSuffix,
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
  
  drawRoute(pointsForFloor);
}
