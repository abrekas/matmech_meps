document.addEventListener("DOMContentLoaded", async () => {
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('input', function() {
        if (this.value) {
            console.log('Поиск:', this.value);
        }
    });

});

function setValue(value, field){
    field.value = value;
    document.getElementById('autocomplete-clues').style.display = 'none';
    
    const overlay = document.getElementById('search-overlay');
    if (overlay) overlay.style.display = 'none';
    
    // Получаем описание комнаты
    const description = roomnames[value];
    if (!description) return;
    
    // Определяем здание и этаж
    const floor = description.split('_').pop();
    const building = description.includes('matmeh_') ? 'matmeh' : 'kuibysheva';
    
    // Сохраняем для перехода (ВАЖНО: те же ключи что в route_request.js)
    localStorage.setItem("routeStartFloor", floor);
    localStorage.setItem("routeStartLocation", building);
    
    const targetPage = building === 'kuibysheva' 
        ? 'kuibysheva_start_page.html' 
        : 'matmeh_start_page.html';
    
    console.log('Переносим на:', targetPage, 'этаж:', floor, 'здание:', building);
    window.location.href = targetPage;
}

document.addEventListener('click', function(event) {
    const cluesBlock = document.getElementById('autocomplete-clues');
    const searchInput = document.getElementById('searchInput');
    const overlay = document.getElementById('search-overlay');
    
    const burgerBtn = document.getElementById('burgerBtn');
    const menu = document.querySelector('.menu');
    
    if (cluesBlock && cluesBlock.style.display !== 'none') {
        if (!cluesBlock.contains(event.target) && 
            !searchInput.contains(event.target) &&
            !burgerBtn?.contains(event.target) &&
            !menu?.contains(event.target)) {
            
            cluesBlock.style.display = 'none';
            if (overlay) overlay.style.display = 'none';
        }
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const cluesBlock = document.getElementById('autocomplete-clues');
        const overlay = document.getElementById('search-overlay');
        
        if (cluesBlock) cluesBlock.style.display = 'none';
        if (overlay) overlay.style.display = 'none';
    }
});


let roomnames = []

document.addEventListener("DOMContentLoaded", async () => {
    parseRoomsFromJson();
});

function parseRoomsFromJson(){
    fetch('../names.json')
    .then(response => {
        if (!response.ok) {
        throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        roomnames = data
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', function(event) {
            giveClue(event.target.value, searchInput);
        });
    })
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });

}

function giveClue(value, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    const overlay = document.getElementById('search-overlay');
    
    if (value.length < 1) {
        cluesBlock.style.display = 'none';
        if (overlay) overlay.style.display = 'none';
        return;
    }
    
    // Создаем оверлей если нет
    if (!overlay) {
        const overlayDiv = document.createElement('div');
        overlayDiv.id = 'search-overlay';
        overlayDiv.className = 'search-overlay';
        document.body.appendChild(overlayDiv);
        overlayDiv.style.display = 'block';
    } else {
        overlay.style.display = 'block';
    }
    
    cluesBlock.style.display = 'flex';
    cluesBlock.style.cssText = 'position: fixed; z-index: 9999; top: 140px; left: 0;';
    
    const matches = Object.keys(roomnames).filter(room => 
        room.toLowerCase().startsWith(value.toLowerCase())
    ).slice(0, 5);
    
    updateClues(matches, input);
}


function updateClues(matches, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    
    cluesBlock.innerHTML = '<div class="clues-header"></div>';
    
    if (matches.length < 1) {
        console.log("nothing found");
        const clueElement = document.createElement('div');
        clueElement.id = 'clue1';
        clueElement.className = 'clue1';
        clueElement.innerHTML = `
            <span style="color: #666; font-size: 0.9em">
                ничего не найдено
            </span>
        `;
        cluesBlock.appendChild(clueElement);
        return; 
    }
    
    for (let i = 0; i < matches.length; i++) {
        const clueElement = document.createElement('div');
        clueElement.id = `clue${i+1}`;
        clueElement.className = `clue${i+1}`;
        clueElement.style.cursor = 'pointer';
        
        const description = roomnames[matches[i]];
        const building = getBuildingFromDescription(description);
        const floor = description.split('_').pop();
        
        clueElement.innerHTML = `
            <strong>${matches[i]}</strong> 
            <span style="color: #666; font-size: 0.9em">
                (${building}, ${floor} этаж)
            </span>
        `;
        
        clueElement.onclick = () => setValue(matches[i], input);
        cluesBlock.appendChild(clueElement);
    }
}

function getBuildingFromDescription(description) {
    if (description.includes('matmeh_')) {
        return 'матмех';
    } else if (description.includes('kuibysheva_')) {
        return 'куйбышева';
    } else {
        return 'неизвестно';
    }
}


// Перехватываем открытие меню
function activateMenu(e) {
    // Закрываем поиск
    const cluesBlock = document.getElementById('autocomplete-clues');
    const overlay = document.getElementById('search-overlay');
    
    if (cluesBlock) cluesBlock.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    
    // Вызываем оригинальную функцию (если она есть)
    if (window.originalActivateMenu) {
        window.originalActivateMenu(e);
    }
}

// Сохраняем оригинальную функцию если она есть
if (typeof window.activateMenu === 'function') {
    window.originalActivateMenu = window.activateMenu;
}