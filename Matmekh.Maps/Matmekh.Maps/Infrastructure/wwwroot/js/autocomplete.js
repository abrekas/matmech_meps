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
        const fromInput = document.getElementById('routeFrom');
        const toInput = document.getElementById('routeTo');
        fromInput.addEventListener('input', function(event) {
            giveClue(event.target.value, fromInput);
        });
        toInput.addEventListener('input', function(event) {
            giveClue(event.target.value, toInput);
        });
    })
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });

}

function giveClue(value, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    if (value.length < 1) {
        cluesBlock.style.display = 'none';
        return;
    }
    cluesBlock.style.display = 'flex';
    const matches = Object.keys(roomnames).filter(room => 
        room.toLowerCase().startsWith(value.toLowerCase())
    ).slice(0, 5);
    updateClues(matches, input);
}

function updateClues(matches, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    
    // Очищаем предыдущие подсказки
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

function setValue(value, field){
    field.value = value;
    document.getElementById('autocomplete-clues').style.display = 'none';
}