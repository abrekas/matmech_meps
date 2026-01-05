document.addEventListener("DOMContentLoaded", () => {
    const grid = document.getElementById("iconGrid");
    if (!grid) return;

    // Заполни под свои реальные имена файлов в images/icons
    const icons = [
        { file: "w_wc.png", label: "Женский туалет" },
        { file: "m_wc.png", label: "Мужской туалет" },
        { file: "coffee.png", label: "Кофемат" },
        { file: "lib.png", label: "Библиотека" },
        { file: "automat.png", label: "Автомат" },
        { file: "canteen.png", label: "Столовая" },
    ];

    grid.innerHTML = "";

    icons.forEach(({ file, label }) => {
        const item = document.createElement("div");
        item.className = "icon-item";

        const img = document.createElement("img");
        img.src = `images/icons/${file}`;
        img.alt = label;

        const text = document.createElement("span");
        text.textContent = label;

        item.appendChild(img);
        item.appendChild(text);
        grid.appendChild(item);
    });
});
