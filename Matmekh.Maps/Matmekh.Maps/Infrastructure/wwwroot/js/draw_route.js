function drawRoute(points) {
    const svg = document.getElementById("routeLayer");
    if (!svg || !Array.isArray(points)) return;

    const safePoints = points.filter(p =>
        p && (p.X != null || p.x != null) && (p.Y != null || p.y != null)
    );

    if (safePoints.length < 2) return;

    svg.innerHTML = "";

    const polyline = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "polyline"
    );

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

    drawPoint(safePoints[0], "green");
    drawPoint(safePoints[safePoints.length - 1], "red");
}

function drawPoint(point, color) {
    const svg = document.getElementById("routeLayer");

    const cx = point.X ?? point.x;
    const cy = point.Y ?? point.y;

    if (cx == null || cy == null) return;

    const circle = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle"
    );

    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", 8);
    circle.setAttribute("fill", color);

    svg.appendChild(circle);
}


document.addEventListener("DOMContentLoaded", () => {
    const raw = localStorage.getItem("routePoints");
    if (!raw) return;

    try {
        const points = JSON.parse(raw);
        drawRoute(points);
        
        localStorage.removeItem("routePoints");

    } catch (e) {
        console.error("Ошибка чтения маршрута", e);
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const raw = localStorage.getItem("routePoints");
    console.log("RAW routePoints =", raw); 

    if (!raw) return;

    try {
        const points = JSON.parse(raw);
        console.log("PARSED points =", points); 
        drawRoute(points);
        localStorage.removeItem("routePoints");
    } catch (e) {
        console.error("Ошибка чтения маршрута", e);
    }
});


