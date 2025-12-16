document.addEventListener("DOMContentLoaded", async () => {
    try {
        const resp = await fetch("menu.html");
        if (resp.ok) {
            const menuHtml = await resp.text();
            const placeholder = document.getElementById("menu-placeholder");
            if (placeholder) placeholder.innerHTML = menuHtml;
        } else {
            console.warn("menu.html не загрузился:", resp.status);
        }
    } catch (e) {
        console.warn("Ошибка загрузки menu.html:", e);
    }
    
    initMap();
    
    const raw = localStorage.getItem("routePoints");
    if (raw) {
        try {
            const points = JSON.parse(raw);
            const floorCode = points[0].floor;
            const floorNumber = floorCode.split("_").pop();
            
            setFloor(floorNumber);
            drawRoute(points);
        } catch (e) {
            console.error("Ошибка чтения маршрута", e);
        } finally {
            localStorage.removeItem("routePoints");
        }
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

    function setFloor(value) {
        floorSelect.value = value;
        floorLabel.textContent = `${value} этаж`;
        floorMap.src = floorImages[value] || "";

        const svg = document.getElementById("routeLayer");
        if (svg) svg.innerHTML = "";
    }

    window.setFloor = setFloor;

    floorSelect.addEventListener("change", () => {
        setFloor(floorSelect.value);
    });

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