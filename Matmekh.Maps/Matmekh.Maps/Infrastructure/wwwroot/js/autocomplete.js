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
    cluesBlock.style.flexDirection = 'column';
    cluesBlock.style.bottom = '216px';
    cluesBlock.style.right = '8px';
    cluesBlock.style.background = 'white';
    cluesBlock.style.border = 'none';
    cluesBlock.style.borderRadius = '8px';
    cluesBlock.style.padding = '16px';
    cluesBlock.style.maxHeight = '300px';
    cluesBlock.style.overflowY = 'auto';
    
    const matches = Object.keys(roomnames).filter(room => 
        room.toLowerCase().startsWith(value.toLowerCase())
    ).slice(0, 5);
    
    updateClues(matches, input);
}

function updateClues(matches, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    
    cluesBlock.innerHTML = '';
    
    if (matches.length < 1) {
        const clueElement = document.createElement('div');
        clueElement.innerHTML = `
            <span style="color: #666">ничего не найдено</span>
        `;
        clueElement.style.cssText = `
            border: 2px solid #d1d5db;
            border-radius: 8px;
            height: 32px;
            padding: 8px;
            max-width: 400px;
            background: white;
            display: flex;
            align-items: center;
        `;
        cluesBlock.appendChild(clueElement);
        return; 
    }
    
    for (let i = 0; i < matches.length; i++) {
        const clueElement = document.createElement('div');
        
        const description = roomnames[matches[i]];
        const building = getBuildingFromDescription(description);
        const floor = description.split('_').pop();
        
        clueElement.innerHTML = `
            <strong>${matches[i]}</strong> 
            <span style="color: #666; font-size: 0.9em">
                (${building}, ${floor} этаж)
            </span>
        `;
        
        clueElement.style.cssText = `
            border: 2px solid #d1d5db;
            border-radius: 8px;
            height: 32px;
            padding: 8px;
            cursor: pointer;
            max-width: 400px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        `;
        
        clueElement.onmouseover = () => {
            clueElement.style.backgroundColor = '#ffffff';
            clueElement.style.borderColor = '#2f80c9';
        };
        clueElement.onmouseout = () => {
            clueElement.style.backgroundColor = 'white';
            clueElement.style.borderColor = '#d1d5db';
        };
        
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

document.addEventListener('click', function(event) {
    const cluesBlock = document.getElementById('autocomplete-clues');
    const fromInput = document.getElementById('routeFrom');
    const toInput = document.getElementById('routeTo');
    
    if (cluesBlock && cluesBlock.style.display !== 'none') {
        if (!cluesBlock.contains(event.target) && 
            !fromInput.contains(event.target) && 
            !toInput.contains(event.target)) {
            
            cluesBlock.style.display = 'none';
        }
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const cluesBlock = document.getElementById('autocomplete-clues');
        if (cluesBlock) cluesBlock.style.display = 'none';
    }
});