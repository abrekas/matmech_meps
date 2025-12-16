document.addEventListener('DOMContentLoaded', function () {
    const buildButton = document.querySelector('.route-submit-btn');

    if (buildButton) {
        buildButton.addEventListener('click', async function () {
            // Берем значения из полей ввода
            const from = document.getElementById('routeFrom').value;
            const to = document.getElementById('routeTo').value;

            // Проверяем, что поля заполнены
            if (!from || !to) {
                alert('Пожалуйста, заполните оба поля!');
                return;
            }

            try {
                // Показываем загрузку
                buildButton.textContent = 'Строим...';
                buildButton.disabled = true;

                // Отправляем запрос на сервер
                const response = await fetch('/api/route/build', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        from: from,
                        to: to
                    })
                });

                // Получаем ответ
                const result = await response.json();

                if (response.ok && result.success) {
                localStorage.setItem("routePoints", JSON.stringify(result.path));

                // 1) Определяем этаж старта
                let startFloor = null;

                // Вариант A (лучше): если сервер возвращает floor у точек маршрута
            if (Array.isArray(result.path) && result.path.length && result.path[0].floor != null) {
                    startFloor = String(result.path[0].floor);
                } else {
                    // Вариант B: берём из номера кабинета "509" -> 5 этаж, "632" -> 6 этаж
                    // (достаём первое число и берём его первую цифру)
                    const m = String(from).match(/\d+/); // найдёт "509" даже если введут "каб. 509"
                    if (m && m[0].length) startFloor = m[0][0];
                }

                if (startFloor) {
                    localStorage.setItem("routeStartFloor", startFloor);
                } else {
                    localStorage.removeItem("routeStartFloor");
                }

                // 2) Переходим на страницу карты
                window.location.href = "matmeh_start_page.html";
            }
            else {
                    // Ошибка от сервера
                    alert(result.error || 'Ошибка сервера');
                }

            } catch (error) {
                // Ошибка сети
                console.error('Ошибка:', error);
                alert('Ошибка сети. Проверьте подключение.');
            } finally {
                // Восстанавливаем кнопку
                buildButton.textContent = 'ПОСТРОИТЬ';
                buildButton.disabled = false;
            }
        });
    }
});