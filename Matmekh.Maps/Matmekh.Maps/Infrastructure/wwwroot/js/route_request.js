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

            if (response.ok && result.success) {
                // сохраняем точки маршрута
                localStorage.setItem("routePoints", JSON.stringify(result.path));
                let startFloor    = null;   
                let startLocation = null;   

                if (Array.isArray(result.path) &&
                    result.path.length &&
                    result.path[0].Floor != null) {

                    const floorField = String(result.path[0].Floor); // "matmeh_5" / "kuibysheva_3"
                    const parts = floorField.split("_");             // ["matmeh","5"]

                    if (parts[0]) startLocation = parts[0];
                    if (parts[1]) startFloor    = parts[1];
                } else {
                    // fallback: вытаскиваем этаж из номера кабинета
                    const m = String(from).match(/\d+/);
                    if (m && m[0].length) startFloor = m[0][0];
                }

                // сохраняем в localStorage
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
                
                if (startLocation === "matmeh") {
                    window.location.href = "matmeh_start_page.html";
                } else {
                    window.location.href = "kuibysheva_start_page.html";
                }
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
