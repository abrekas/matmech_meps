document.addEventListener("DOMContentLoaded", async () => {
  const resp = await fetch("menu.html");
  const menuHtml = await resp.text();

  const placeholder = document.getElementById("menu-placeholder");
  placeholder.innerHTML = menuHtml;

  const floorSelect = document.getElementById("floorSelect");

  const raw = localStorage.getItem("routeStartFloor"); 
  let savedFloor = null;
  if (raw) {
    const m = String(raw).match(/\d/); 
    if (m) savedFloor = m[0];
  }

  if (savedFloor && floorSelect) {
    floorSelect.value = savedFloor;
  }

  initMap();

  if (savedFloor && floorSelect) {
    floorSelect.dispatchEvent(new Event("change"));
  }
});


function initMap() {
  const floorSelect = document.getElementById("floorSelect");
  const floorLabel  = document.getElementById("floorLabel");
  const floorMap    = document.getElementById("floorMap");

  const floorImages = {
    "5": "images/floor5.png",
    "6": "images/floor6.png"
  };

  const applyFloor = (value) => {
    if (floorLabel) floorLabel.textContent = `${value} этаж`;
    if (floorMap) {
      if (floorImages[value]) {
        floorMap.src = floorImages[value];
        floorMap.alt = "";
      } else {
        floorMap.src = "";
        floorMap.alt = "Карта не найдена";
      }
    }
  };

  applyFloor(floorSelect.value);

  const mapInner = document.getElementById("mapInner");
  const zoomInBtn = document.getElementById("zoomInBtn");
  const zoomOutBtn = document.getElementById("zoomOutBtn");

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

  floorSelect.addEventListener("change", () => {
    applyFloor(floorSelect.value);
  });
}
