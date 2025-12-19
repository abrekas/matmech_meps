(() => {
    const METRIC_URL = "/api/metric/build";
    const INACTIVITY_LIMIT_MS = 5 * 60 * 1000;

    let sessionStartedAt = Date.now();
    let inactivityTimerId = null;
    let ended = false;

    function sendMetric(activeMs, reason) {
        const payload = {
            name: "map_active_time",
            page: location.pathname,
            activeMs: activeMs,
            startedAt: new Date(sessionStartedAt).toISOString(),
            finishedAt: new Date().toISOString(),
            reason 
        };

        const body = JSON.stringify(payload);

        try {
            if (navigator.sendBeacon) {
                const blob = new Blob([body], { type: "application/json" });
                navigator.sendBeacon(METRIC_URL, blob);
            } else {
                fetch(METRIC_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body
                }).catch(() => {});
            }
        } catch (e) {
            console.warn("map_active_time metric send error", e);
        }
    }

    function endSession(reason, activeOverrideMs) {
        if (ended) return;
        ended = true;
        clearTimeout(inactivityTimerId);

        const now = Date.now();
        const totalMs = now - sessionStartedAt;
        const activeMs = typeof activeOverrideMs === "number"
            ? activeOverrideMs
            : totalMs;

        if (activeMs <= 0) {
            return;
        }

        sendMetric(activeMs, reason);
    }

    function onInactivityTimeout() {
        if (ended) return;

        const now = Date.now();
        const totalMs = now - sessionStartedAt;
        const activeMs = Math.max(0, totalMs - INACTIVITY_LIMIT_MS);

        endSession("inactivity_timeout", activeMs);
    }

    function scheduleInactivityTimer() {
        if (ended) return;
        clearTimeout(inactivityTimerId);
        inactivityTimerId = setTimeout(onInactivityTimeout, INACTIVITY_LIMIT_MS);
    }

    function markActivity() {
        if (ended) return;
        scheduleInactivityTimer();
    }

    scheduleInactivityTimer();
    
    const activityEvents = ["click", "mousemove", "keydown", "scroll", "touchstart"];

    activityEvents.forEach(ev => {
        window.addEventListener(ev, markActivity, { passive: true });
    });
    
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            return;
        } else {
            markActivity();
        }
    });
    
    window.addEventListener("beforeunload", () => {
        if (ended) return;
        const now = Date.now();
        const totalMs = now - sessionStartedAt;
        endSession("unload", totalMs);
    });
})();
