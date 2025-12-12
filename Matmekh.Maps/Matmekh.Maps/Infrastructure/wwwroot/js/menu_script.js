document.addEventListener("DOMContentLoaded", async () => {
  const resp = await fetch("menu.html");
  const menuHtml = await resp.text();

  const placeholder = document.getElementById("menu-placeholder");
  placeholder.innerHTML = menuHtml;

  initMenu();
});

function initMenu() {
  const menu = document.getElementById('myMenu');
  const clickBtn = document.getElementById('menu-item')
  if (!menu) return;
  const panel = menu.querySelector(".menu-panel");
  window.activateMenu = function(e){
    e.stopPropagation();
    menu.classList.toggle("active");
  };
  if (panel){
    panel.addEventListener("click", (e) => e.stopPropagation());
  }
  clickBtn.addEventListener("click", () => menu.classList.remove("active"))
  menu.addEventListener("click", () => menu.classList.remove("active"));
}

