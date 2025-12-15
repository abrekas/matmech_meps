document.addEventListener("DOMContentLoaded", () => {
    const goRouteKuibyshevaBtn = document.getElementById("goRouteK");
    const closeRouteKuibyshevaBtn = document.getElementById("closeRouteK");
    const goRouteMatMexBtn = document.getElementById("goRouteM");
    const closeRouteMatMexBtn = document.getElementById("closeRouteM");
    if (goRouteKuibyshevaBtn) {
        goRouteKuibyshevaBtn.addEventListener("click", () => {
            window.location.href = "kuibysheva_route_page.html";
        });
    }

    if (closeRouteKuibyshevaBtn) {
        closeRouteKuibyshevaBtn.addEventListener("click", () => {
            window.location.href = "kuibysheva_start_page.html";
        });
    }

    if (goRouteMatMexBtn) {
        goRouteMatMexBtn.addEventListener("click", () => {
            window.location.href = "matmeh_route_page.html";
        });
    }

    if (closeRouteMatMexBtn) {
        closeRouteMatMexBtn.addEventListener("click", () => {
            window.location.href = "matmeh_start_page.html";
        });
    }
});
