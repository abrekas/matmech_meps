(() => {
    const STORAGE_KEY = "mapSession";
    const METRIC_URL = "/api/metric/build";
    const INACTIVITY_LIMIT_MS = 5 * 60 * 1000; 

    let inactivityTimerId = null;

    function loadSession() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            return JSON.parse(raw);
        } catch {
            return null;
        }
    }

    function saveSession(session) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
        } catch {}
    }

    function clearSession() {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch {}
    }

    function sendMetric(session, reason) {
        const payload = {
            name: "map_session",
            activeMs: Math.round(session.activeMs),
            startedAt: new Date(session.startedAt).toISOString(),
            finishedAt: new Date().toISOString(),
            reason,                       
            page: location.pathname
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
            console.warn("map_session metric send error", e);
        }
    }
    
    let session = loadSession();

    const now = Date.now();

    if (!session || session.ended) {
        session = {
            startedAt: now,
            lastActivityAt: now,
            activeMs: 0,
            ended: false
        };
        saveSession(session);
    }

    function scheduleInactivityTimer() {
        if (session.ended) return;
        clearTimeout(inactivityTimerId);
        inactivityTimerId = setTimeout(onInactivityTimeout, INACTIVITY_LIMIT_MS);
    }

    function markActivity() {
        if (session.ended) return;

        const now = Date.now();
        const delta = now - session.lastActivityAt;
        
        if (delta > 0 && delta < INACTIVITY_LIMIT_MS) {
            session.activeMs += delta;
        }

        session.lastActivityAt = now;
        saveSession(session);
        scheduleInactivityTimer();
    }

    function onInactivityTimeout() {
        if (session.ended) return;

        session.ended = true;
        saveSession(session);
        sendMetric(session, "inactivity_timeout");
        clearSession();
    }
    
    markActivity();
    
    const activityEvents = ["click", "mousemove", "keydown", "scroll", "touchstart", "touchmove"];
    activityEvents.forEach(ev => {
        window.addEventListener(ev, markActivity, { passive: true });
    });

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            markActivity();
        }
    });
    
    window.addEventListener("beforeunload", () => {
        if (session.ended) return;
        const now = Date.now();
        const delta = now - session.lastActivityAt;
        if (delta > 0 && delta < INACTIVITY_LIMIT_MS) {
            session.activeMs += delta;
        }
        session.lastActivityAt = now;
        saveSession(session);
        
        session.ended = true;
        saveSession(session);
        sendMetric(session, "unload");
        clearSession();
    });
})();
