function drawRoute(points) {
    const svg = document.getElementById("routeLayer");

    svg.innerHTML = "";

    if (!points || points.length < 2) return;

    const polyline = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "polyline"
    );

    polyline.setAttribute(
        "points",
        points.map(p => `${p.x},${p.y}`).join(" ")
    );

    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", "#e11d48");
    polyline.setAttribute("stroke-width", "6");
    polyline.setAttribute("stroke-linecap", "round");
    polyline.setAttribute("stroke-linejoin", "round");

    svg.appendChild(polyline);
    
    drawPoint(points[0], "green");
    drawPoint(points.at(-1), "red");
}

function drawPoint(point, color) {
    const svg = document.getElementById("routeLayer");
    const circle = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle"
    );

    circle.setAttribute("cx", point.x);
    circle.setAttribute("cy", point.y);
    circle.setAttribute("r", 8);
    circle.setAttribute("fill", color);

    svg.appendChild(circle);
}

document.addEventListener("DOMContentLoaded", () => {
    const testPoints = [
        { x: 258, y: 350 },
        { x: 266, y: 285 },
        { x: 260, y: 262 },
        { x: 345, y: 224 },
        { x: 379, y: 301 }
    ];

    drawRoute(testPoints);
});

