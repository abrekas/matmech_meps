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
    const floorMap = document.getElementById("floorMap");
    const mapInner = document.getElementById("mapInner");

    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");

    const floorImages = {
        "1 этаж": "images/enter_k.jpg",
        "3 этаж": "images/third_k.jpg",
        "2 этаж контуровские классы": "images/second_k_k.jpg",
        "1 этаж контуровские классы": "images/first_k_k.jpg"
    };

    let scale = 1;
    let MIN_SCALE = 1;
    const MAX_SCALE = 3;
    const STEP = 0.25;

    function applyScale() {
        mapInner.style.transform = `scale(${scale})`;
    }

    function loadFloor(value) {
        floorMap.src = floorImages[value];
        floorLabel.textContent = value;
        floorMap.onload = () => {
            if (value === "3 этаж") {
                scale = 0.2;
                MIN_SCALE = 0.2;
            } else {
                scale = 0.7;
                MIN_SCALE = 0.7;
            }
            
            mapInner.style.transformOrigin = "top left";
            mapInner.style.transform = "none";
            applyScale();
        };
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
