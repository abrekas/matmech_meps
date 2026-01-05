function drawRoute(points, opts = {}) {
    const {
        hasNextFloor = false,
        onNextFloor = null,   // callback при клике на стрелку
    } = opts;

    const svg = document.getElementById("routeLayer");
    if (!svg || !Array.isArray(points)) return;

    const safePoints = points.filter(p =>
        p && (p.X != null || p.x != null) && (p.Y != null || p.y != null)
    );
    if (safePoints.length < 2) return;

    svg.innerHTML = "";

    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute(
        "points",
        safePoints.map(p => `${p.X ?? p.x},${p.Y ?? p.y}`).join(" ")
    );
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", "#e11d48");
    polyline.setAttribute("stroke-width", "6");
    polyline.setAttribute("stroke-linecap", "round");
    polyline.setAttribute("stroke-linejoin", "round");
    svg.appendChild(polyline);

    // Кружок в начале участка маршрута
    drawPoint(safePoints[0], "#e11d48");

    // Конец: либо стрелка (если есть следующий этаж), либо кружок (если это последний этаж)
    if (hasNextFloor && typeof onNextFloor === "function") {
        const last = safePoints[safePoints.length - 1];
        const prev = safePoints[safePoints.length - 2] ?? last;

        drawArrow(last, prev, {
            color: "#e11d48",
            onClick: onNextFloor
        });
    } else {
        drawPoint(safePoints[safePoints.length - 1], "red");
    }
}

function drawPoint(point, color) {
    const svg = document.getElementById("routeLayer");
    if (!svg) return;

    const cx = point.X ?? point.x;
    const cy = point.Y ?? point.y;
    if (cx == null || cy == null) return;

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", 8);
    circle.setAttribute("fill", color);

    svg.appendChild(circle);
}

/**
 * Рисуем кликабельную стрелку, ориентированную по направлению последнего сегмента (prev -> end)
 */
function drawArrow(endPoint, prevPoint, { color = "#e11d48", onClick } = {}) {
    const svg = document.getElementById("routeLayer");
    if (!svg) return;

    const ex = endPoint.X ?? endPoint.x;
    const ey = endPoint.Y ?? endPoint.y;
    const px = prevPoint.X ?? prevPoint.x;
    const py = prevPoint.Y ?? prevPoint.y;
    if (ex == null || ey == null || px == null || py == null) return;

    const dx = ex - px;
    const dy = ey - py;
    const angleDeg = Math.atan2(dy, dx) * 180 / Math.PI;

    // Группа со стрелкой, повернутая в сторону движения
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${ex} ${ey}) rotate(${angleDeg})`);
    g.style.cursor = "pointer";

    // Небольшая “капсула”/обводка вокруг стрелки (чтобы лучше нажималось)
    const hit = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    hit.setAttribute("cx", "0");
    hit.setAttribute("cy", "0");
    hit.setAttribute("r", "14");
    hit.setAttribute("fill", "transparent");
    hit.setAttribute("pointer-events", "all");

    // Сама стрелка (треугольник)
    const arrow = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    // Направление "вправо" до поворота: наконечник в (16,0)
    arrow.setAttribute("points", "16,0 -6,-10 -6,10");
    arrow.setAttribute("fill", color);

    // (опционально) белая обводка для контраста
    arrow.setAttribute("stroke", "white");
    arrow.setAttribute("stroke-width", "2");
    arrow.setAttribute("stroke-linejoin", "round");

    g.appendChild(hit);
    g.appendChild(arrow);

    g.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
    });

    svg.appendChild(g);
}
