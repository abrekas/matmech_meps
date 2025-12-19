document.addEventListener("DOMContentLoaded", () => {
    const goRouteKuibyshevaBtn = document.getElementById("goRouteK");
    const closeRouteKuibyshevaBtn = document.getElementById("closeRouteK");
    const goRouteMatMexBtn = document.getElementById("goRouteM");
    const closeRouteMatMexBtn = document.getElementById("closeRouteM");

    if (goRouteKuibyshevaBtn) {
        goRouteKuibyshevaBtn.addEventListener("click", () => {
            console.log("goRouteK click");
            window.location.href = "kuibysheva_route_page.html";
        });
    }

    if (closeRouteKuibyshevaBtn) {
        closeRouteKuibyshevaBtn.addEventListener("click", () => {
            console.log("closeRouteK click");
            window.location.href = "kuibysheva_start_page.html";
        });
    }

    if (goRouteMatMexBtn) {
        goRouteMatMexBtn.addEventListener("click", () => {
            console.log("goRouteM click");
            window.location.href = "matmeh_route_page.html";
        });
    }

    if (closeRouteMatMexBtn) {
        console.log("closeRouteM found, adding listener");
        closeRouteMatMexBtn.addEventListener("click", () => {
            console.log("closeRouteM clicked");
            window.location.href = "matmeh_start_page.html";
        });
    } else {
        console.log("closeRouteM NOT found on this page");
    }
});
