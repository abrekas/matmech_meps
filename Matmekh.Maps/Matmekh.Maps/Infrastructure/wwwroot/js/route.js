const goRouteBtn = document.getElementById("goRoute");
const closeRouteBtn = document.getElementById("closeRoute");
if (goRouteBtn) {
goRouteBtn.addEventListener("click", () => {
    window.location.href = "matmeh_route_page.html";
});
}
if (closeRouteBtn) {
closeRouteBtn.addEventListener("click", () => {
    window.location.href = "index.html";
});
}
