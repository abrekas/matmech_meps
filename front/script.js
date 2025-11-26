function activateMenu(e) {
  e.stopPropagation();

  const menu = document.getElementById('myMenu');
  menu.classList.toggle('active');
}

document.addEventListener('DOMContentLoaded', function() {
  const menu = document.getElementById('myMenu');
  const panel = document.querySelector('.menu-panel');
  panel.addEventListener('click', function(e) {
    e.stopPropagation();
  });
  menu.addEventListener('click', function() {
    menu.classList.remove('active');
  });
});
