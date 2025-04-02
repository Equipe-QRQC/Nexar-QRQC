//  Lógica do JS - Botão sidebar

function toggleSidebar() {
  let sidebar = document.getElementById("sidebar");
  let content = document.getElementById("content");
  let toggleBtn = document.getElementById("toggleSidebar").querySelector("i");

  sidebar.classList.toggle("collapsed");
  content.classList.toggle("expanded");

  toggleBtn.style.transition = "transform 0.3s ease";
  if (sidebar.classList.contains("collapsed")) {
    toggleBtn.style.transform = "rotate(180deg)";
  } else {
    toggleBtn.style.transform = "rotate(0deg)";
  }
}
