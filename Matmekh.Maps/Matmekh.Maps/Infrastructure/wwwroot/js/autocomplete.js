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
        for (cab in data){
            console.log(cab);
        }
        const fromInput = document.getElementById('routeFrom');
        const toInput = document.getElementById('routeTo');
        fromInput.addEventListener('input', function(event) {
            console.log('Пользователь вводит в "Откуда":', event.target.value);
            giveClue(event.target.value, fromInput);
        });
        toInput.addEventListener('input', function(event) {
            console.log('Пользователь вводит в "Куда":', event.target.value);
            giveClue(event.target.value, toInput);
        });
    })
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });

}

function giveClue(value, input){
    const cluesBlock = document.getElementById('autocomplete-clues');
    const clue1 = document.getElementById('clue1')
    cluesBlock.style.display = 'flex';
    const match = Object.keys(roomnames).find(room => 
        room.toLowerCase().startsWith(value.toLowerCase())
    );
    console.log(match)
    clue1.textContent = match;
    clue1.addEventListener('click', function() {
        setValue(match, input);
    });
}

function setValue(value, field){
    field.value = value;
}