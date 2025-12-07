function activateMenu(e) {
    e.stopPropagation();

    const menu = document.getElementById('myMenu');
    menu.classList.toggle('active');
}

document.addEventListener('DOMContentLoaded', function() {
    const menu = document.getElementById('myMenu');
    const panel = document.querySelector('.menu-panel');
    panel.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    menu.addEventListener('click', function() {
        menu.classList.remove('active');
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const floorSelect = document.getElementById("floorSelect");
    const floorLabel  = document.getElementById("floorLabel");
    const floorMap    = document.getElementById("floorMap");
    
    const floorImages = {
        "5": "images/floor5map.png",
        "6": "images/floor6map.png"
    };
    
    const initValue = floorSelect.value;
    if (floorImages[initValue]) {
        floorMap.src = floorImages[initValue];
    }
    const mapInner = document.getElementById("mapInner");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");

    if (mapInner && zoomInBtn && zoomOutBtn) {
        let scale = 0.7;
        const MIN_SCALE = 0.7;      
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
            floorMap.alt = "Карта для этого этажа пока не загружена";
        }
    });
});
