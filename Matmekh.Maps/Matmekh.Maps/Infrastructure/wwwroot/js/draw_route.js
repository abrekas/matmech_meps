function drawRoute(points, opts = {}) {
    const { onEndClick = null, onStartClick = null } = opts;

    const layer = document.getElementById("routeLayer"); // <g>
    if (!layer || !Array.isArray(points)) return;

    const safePoints = points.filter(p =>
        p && (p.X != null || p.x != null) && (p.Y != null || p.y != null)
    );
    if (safePoints.length < 2) return;

    layer.innerHTML = "";

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
    polyline.classList.add("route-noclick");
    layer.appendChild(polyline);

    // красная (начало) — кликабельна только если есть onStartClick
    drawPoint(safePoints[0], "red", { onClick: onStartClick });

    // зелёная (конец) — кликабельна только если есть onEndClick
    drawPoint(safePoints[safePoints.length - 1], "green", { onClick: onEndClick });
}

function drawPoint(point, color, { onClick = null } = {}) {
    const layer = document.getElementById("routeLayer");
    if (!layer) return;

    const cx = point.X ?? point.x;
    const cy = point.Y ?? point.y;
    if (cx == null || cy == null) return;

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", 11);
    circle.setAttribute("fill", color);

    if (typeof onClick === "function") {
        circle.classList.add("route-clickable");
        circle.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onClick();
        });
    } else {
        circle.classList.add("route-noclick");
    }

    layer.appendChild(circle);
}
