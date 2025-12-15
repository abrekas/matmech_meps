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

                if (response.ok) {
                    // Успешный ответ
                    // сохраняем точки маршрута
                    localStorage.setItem("routePoints", JSON.stringify(result.path));
                    // переходим на страницу карты
                    window.location.href = "matmeh_start_page.html";
                    // Здесь можно отобразить маршрут на карте
                    // Например: displayRouteOnMap(result);
                } else {
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