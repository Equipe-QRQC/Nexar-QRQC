document.addEventListener("DOMContentLoaded", function () {
    // Lógica do modal
    const btns = document.querySelectorAll(".btn-abrir-modal");
    btns.forEach((btn) => {
      btn.addEventListener("click", function () {
        document.getElementById("modalOcorrencia").value = this.getAttribute("data-ocorrencia");
        document.getElementById("modalData").value = this.getAttribute("data-data") + " " + this.getAttribute("data-hora");
        document.getElementById("modalDescricao").value = this.getAttribute("data-descricao");
        document.getElementById("modalResposta").value = this.getAttribute("data-resposta");
      });
    });
  
    
    // Filtro
    const searchInput = document.getElementById("searchInput");
    const dateInput = document.getElementById("dateInput");
    const tipoSelect = document.getElementById("tipoSelect");
    const tableBody = document.getElementById("tableBody");
    const linhaVazia = document.getElementById("linha-vazia"); // Mensagem "Nenhum resultado encontrado"
    
    let allRows = Array.from(tableBody.querySelectorAll("tr")); // Armazenar todas as linhas
    let filteredRows = []; // Linhas filtradas
    let currentPage = 1; // Página inicial
    const rowsPerPage = 8; // Linhas por página
  
    // Função para filtrar a tabela
    function filtrarTabela() {
      const filtroTexto = searchInput.value.toLowerCase();
      const filtroData = dateInput.value;
      const filtroTipo = tipoSelect.value;
  
      filteredRows = []; // Resetar linhas filtradas
      let algumaVisivel = false;
  
      allRows.forEach((linha) => {
        const celulas = linha.querySelectorAll("td");
        if (celulas.length < 4) return; // Ignorar linha de cabeçalho ou sem dados válidos
  
        const textoOcorrencia = celulas[0].textContent.toLowerCase();
        const textoData = celulas[1].textContent.trim();
        const textoDescricao = celulas[2].textContent.toLowerCase();
        const textoResposta = celulas[3].textContent.toLowerCase();
  
        const combinaTexto = textoDescricao.includes(filtroTexto) || textoResposta.includes(filtroTexto);
        const combinaTipo = !filtroTipo || textoOcorrencia === filtroTipo.toLowerCase();
        
        // Formatar a data para comparar corretamente com a entrada
        const filtroDataFormatada = filtroData.split("-").reverse().join("/");
        const combinaData = !filtroData || textoData.includes(filtroDataFormatada);
  
        const mostrar = combinaTexto && combinaTipo && combinaData;
        linha.style.display = mostrar ? "" : "none";
        if (mostrar) {
          filteredRows.push(linha); // Adiciona a linha filtrada à lista
          algumaVisivel = true;
        }
      });
  
      // Exibir a mensagem "Nenhum resultado encontrado" se não houver resultados
      if (linhaVazia) {
        linhaVazia.style.display = algumaVisivel ? "none" : "";
      }
  
      // Após filtrar, chama a função de atualização da tabela
      currentPage = 1; // Resetar a página para 1 após a filtragem
      updateTable();
    }
  
    searchInput.addEventListener("input", filtrarTabela);
    dateInput.addEventListener("input", filtrarTabela);
    tipoSelect.addEventListener("change", filtrarTabela);
  
    // Função para obter as linhas a serem exibidas
    function getRowsToDisplay() {
      return filteredRows.length > 0 ? filteredRows : allRows;
    }
  
    // Paginação
    const pagination = document.getElementById("pagination");
  
    function renderPagination(totalPages) {
      pagination.innerHTML = "";
  
      // Se não houver páginas, esconder a paginação
      if (totalPages <= 1) {
        pagination.style.display = "none"; // Ocultar se não houver páginas
      } else {
        pagination.style.display = "flex"; // Mostrar a paginação
      }
  
      // Botão anterior
      const prevBtn = document.createElement("button");
      prevBtn.innerHTML = "&larr;";
  
      prevBtn.disabled = currentPage === 1;
      prevBtn.className = "pagination-btn";
      prevBtn.onclick = () => {
        currentPage--;
        updateTable();
      };
      pagination.appendChild(prevBtn);
  
      // Botões de páginas
      const totalPagesCount = Math.ceil(getRowsToDisplay().length / rowsPerPage);
      for (let i = 1; i <= totalPagesCount; i++) {
        const pageBtn = document.createElement("button");
        pageBtn.textContent = i;
        pageBtn.className = "pagination-btn" + (i === currentPage ? " active" : "");
        pageBtn.onclick = () => {
          currentPage = i;
          updateTable();
        };
        pagination.appendChild(pageBtn);
      }
  
      // Botão próximo
      const nextBtn = document.createElement("button");
      nextBtn.innerHTML = "&rarr;";
  
      nextBtn.disabled = currentPage === totalPagesCount;
      nextBtn.className = "pagination-btn";
      nextBtn.onclick = () => {
        currentPage++;
        updateTable();
      };
      pagination.appendChild(nextBtn);
    }
  
    // Função para atualizar a tabela
    function updateTable() {
      const rowsToDisplay = getRowsToDisplay(); // Filtradas ou todas as linhas
      const totalRows = rowsToDisplay.length;
      const totalPages = Math.ceil(totalRows / rowsPerPage);
      const start = (currentPage - 1) * rowsPerPage;
      const end = start + rowsPerPage;
  
      // Atualizar as linhas a serem exibidas
      rowsToDisplay.forEach((row, index) => {
        row.style.display = (index >= start && index < end) ? "" : "none";
      });
  
      renderPagination(totalPages); // Atualizar a paginação
    }
  
    updateTable(); // Inicia a tabela com todas as linhas
  });
  