document.addEventListener('DOMContentLoaded', function () {
    const buildButton = document.querySelector('.route-submit-btn');
    if (!buildButton) return;

    buildButton.addEventListener('click', async function () {
        const from = document.getElementById('routeFrom').value;
        const to   = document.getElementById('routeTo').value;

        if (!from || !to) {
            alert('Пожалуйста, заполните оба поля!');
            return;
        }

        try {
            buildButton.textContent = 'Строим...';
            buildButton.disabled = true;

            const response = await fetch('/api/route/build', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ from, to })
            });

            const result = await response.json();
            console.log('result from /api/route/build:', result);

            if (response.ok && result.success) {
                const path = Array.isArray(result.path) ? result.path : [];
                localStorage.setItem("routePoints", JSON.stringify(path));

                
                let startFloor    = null;   
                let startLocation = null;   
                
                const firstWithFloor = path.find(p => p && (p.Floor != null || p.floor != null)) || null;

                if (firstWithFloor) {
                    const floorField = String(firstWithFloor.Floor ?? firstWithFloor.floor);

                    const [loc, floorNum] = floorField.split('_'); 

                    if (loc)      startLocation = loc;
                    if (floorNum) startFloor    = floorNum;
                }
                
                if (!startFloor) {
                    const m = String(from).match(/\d+/);
                    if (m && m[0].length) startFloor = m[0][0];
                }
                
                if (!startLocation) {
                    startLocation = "matmeh";
                }

                console.log('startLocation:', startLocation, 'startFloor:', startFloor);
                
                if (startFloor) {
                    localStorage.setItem("routeStartFloor", startFloor);
                } else {
                    localStorage.removeItem("routeStartFloor");
                }

                if (startLocation) {
                    localStorage.setItem("routeStartLocation", startLocation);
                } else {
                    localStorage.removeItem("routeStartLocation");
                }

                const targetPage =
                    startLocation === "kuibysheva"
                        ? "kuibysheva_start_page.html"
                        : "matmeh_start_page.html";

                console.log('redirect to:', targetPage);
                window.location.href = targetPage;

            } else {
                alert(result.error || 'Ошибка сервера');
            }

        } catch (error) {
            console.error('Ошибка:', error);
            alert('Ошибка сети. Проверьте подключение.');
        } finally {
            buildButton.textContent = 'ПОСТРОИТЬ';
            buildButton.disabled = false;
        }
    });
});
