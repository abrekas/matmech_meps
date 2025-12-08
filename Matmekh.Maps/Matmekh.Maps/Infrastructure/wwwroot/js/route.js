const goRouteBtn = document.getElementById("goRoute");
const closeRouteBtn = document.getElementById("closeRoute");
if (goRouteBtn) {
goRouteBtn.addEventListener("click", () => {
    window.location.href = "route.html";
});
}
if (closeRouteBtn) {
closeRouteBtn.addEventListener("click", () => {
    window.location.href = "map.html";
});
}
