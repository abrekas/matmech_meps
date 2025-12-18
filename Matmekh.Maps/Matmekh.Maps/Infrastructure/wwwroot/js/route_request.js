document.addEventListener('DOMContentLoaded', function () {
    const buildButton = document.querySelector('.route-submit-btn');
    if (!buildButton) return;

    buildButton.addEventListener('click', async function () {
        const from = document.getElementById('routeFrom').value.trim();
        const to = document.getElementById('routeTo').value.trim();
        
        // Проверяем валидность
        const isValid = await check_valid(from, to);
        if (!isValid) {
            return; // Если невалидно, выходим
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

                let startFloor = null;
                let startLocation = null;

                const firstWithFloor = path.find(p => p && (p.Floor != null || p.floor != null)) || null;

                if (firstWithFloor) {
                    const floorField = String(firstWithFloor.Floor ?? firstWithFloor.floor);
                    const [loc, floorNum] = floorField.split('_');

                    if (loc) startLocation = loc;
                    if (floorNum) startFloor = floorNum;
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

async function check_valid(from, to) {ы
    if (!from || !to) {
        alert('Пожалуйста, заполните оба поля!');
        return false;
    }
    
    if (from === to) {
        alert('Пункт отправления и назначения не могут быть одинаковыми!');
        return false;
    }

    try {
        const response = await fetch('../names.json');
        const data = await response.json();
        
        let from_building = null;
        let to_building = null;

        for (const cab in data) {
            if (cab === from) {
                from_building = data[cab];
            }
            if (cab === to) {
                to_building = data[cab];
            }
        }
        
        if (!from_building) {
            alert(`Комната "${from}" не найдена в базе данных`);
            return false;
        }
        if (!to_building) {
            alert(`Комната "${to}" не найдена в базе данных`);
            return false;
        }
        
        const getBuilding = (description) => {
            if (description.includes('matmeh_')) return 'matmeh';
            if (description.includes('kuibysheva_')) return 'kuibysheva';
            return null;
        };
        
        const from_building_name = getBuilding(from_building);
        const to_building_name = getBuilding(to_building);
        
        if (from_building_name !== to_building_name) {
            alert('Маршрут можно строить только в пределах одного здания!\n' +
                  `"${from}" находится в ${from_building_name || 'неизвестном здании'}\n` +
                  `"${to}" находится в ${to_building_name || 'неизвестном здании'}`);
            return false;
        }
        
        return true;
        
    } catch (error) {
        console.error('Ошибка при проверке валидности:', error);
        alert('Ошибка при проверке данных. Пожалуйста, попробуйте снова.');
        return false;
    }
}