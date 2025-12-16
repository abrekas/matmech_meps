document.addEventListener("DOMContentLoaded", async () => {
    const resp = await fetch("menu.html");   
    const menuHtml = await resp.text();

    const placeholder = document.getElementById("menu-placeholder");
    placeholder.innerHTML = menuHtml;

    initMap(); 
});


function initMap() {
    const floorSelect = document.getElementById("floorSelect");
    const floorLabel  = document.getElementById("floorLabel");
    const floorMap    = document.getElementById("floorMap");

    const floorImages = {
        "5": "images/floor5.png",
        "6": "images/floor6.png"
    };

    const initValue = floorSelect.value;
    if (floorImages[initValue]) {
        floorMap.src = floorImages[initValue];
    }

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
        const value = floorSelect.value;
        floorLabel.textContent = `${value} этаж`;

        if (floorImages[value]) {
            floorMap.src = floorImages[value];
        } else {
            floorMap.src = "";
            floorMap.alt = "Карта не найдена";
        }
    });
}