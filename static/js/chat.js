const chatHistorico = [];

function toggleChat() {
  const win = document.getElementById('chatWindow');
  win.classList.toggle('open');
  if (win.classList.contains('open')) {
    document.getElementById('chatInput').focus();
  }
}

function appendMsg(texto, tipo) {
  const msgs = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-msg ${tipo}`;
  div.textContent = texto;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function appendTyping() {
  const msgs = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-msg bot';
  div.id = 'typingIndicator';
  div.innerHTML = '<i class="fas fa-circle-notch fa-spin" style="font-size:12px; color:var(--text-muted);"></i> Analisando...';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const mensagem = input.value.trim();
  if (!mensagem) return;

  input.value = '';
  appendMsg(mensagem, 'user');
  chatHistorico.push({ role: 'user', content: mensagem });
  appendTyping();

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ mensagem, historico: chatHistorico.slice(-8) }),
    });
    const data = await res.json().catch(() => ({}));
    removeTyping();
    // Erros (IA fora, limite de mensagens, sessão expirada) vêm em "erro" ou com status != 200
    const texto = data.resposta || data.erro || 'Erro ao conectar com o assistente.';
    appendMsg(texto, 'bot');
    if (res.ok) {
      chatHistorico.push({ role: 'assistant', content: texto });
    } else {
      chatHistorico.pop();   // a pergunta sem resposta não vai no histórico da próxima
    }
  } catch (e) {
    removeTyping();
    chatHistorico.pop();
    appendMsg('Erro ao conectar com o assistente.', 'bot');
  }
}
