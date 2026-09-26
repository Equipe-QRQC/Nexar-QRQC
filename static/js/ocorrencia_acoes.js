/**
 * Ações de ocorrência compartilhadas (Histórico e página da ocorrência):
 * toast, iniciar atendimento e resolução com solução aplicada.
 * Requer templates/partials/modal_resolver.html na página.
 */
(function () {
  function csrf() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
  }

  function toast(msg, tipo) {
    const stack = document.getElementById('toastStack');
    if (!stack) return;
    const el = document.createElement('div');
    el.className = 'toast toast-' + (tipo || 'success');
    const icon = document.createElement('i');
    icon.className = 'fas ' + (tipo === 'danger' ? 'fa-circle-exclamation' : 'fa-circle-check');
    const txt = document.createElement('span');
    txt.textContent = msg;
    el.append(icon, txt);
    stack.appendChild(el);
    setTimeout(() => el.classList.add('saindo'), 3200);
    setTimeout(() => el.remove(), 3600);
  }

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.erro || 'Não foi possível salvar. Tente novamente.');
    return data;
  }

  async function iniciarAtendimento(id, onDone) {
    try {
      const data = await postJSON(`/ocorrencias/${id}/iniciar`);
      toast(`Ocorrência #${id} em andamento.`);
      if (onDone) onDone(data);
    } catch (e) {
      toast(e.message, 'danger');
    }
  }

  // ── Modal de resolução ──────────────────────────────────────────────────
  let atual = null; // { id, onDone }

  function fecharResolucao() {
    const ov = document.getElementById('resolverOverlay');
    if (ov) ov.hidden = true;
    atual = null;
  }

  function abrirResolucao(id, sugestoes, onDone) {
    const ov = document.getElementById('resolverOverlay');
    if (!ov) return;
    atual = { id, onDone };
    document.getElementById('rsId').textContent = id;
    document.getElementById('rsSolucao').value = '';
    document.getElementById('rsComponente').value = '';
    document.getElementById('rsErro').hidden = true;
    const dl = document.getElementById('rsSugestoes');
    dl.innerHTML = '';
    [...new Set((sugestoes || []).filter(Boolean))].forEach(s => {
      const o = document.createElement('option');
      o.value = s;
      dl.appendChild(o);
    });
    const btn = document.getElementById('rsConfirmar');
    btn.disabled = false;
    ov.hidden = false;
    document.getElementById('rsSolucao').focus();
  }

  document.addEventListener('click', e => {
    if (e.target.closest('[data-rs-fechar]') || e.target.id === 'resolverOverlay') fecharResolucao();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && atual) {
      e.preventDefault();          // sinaliza a outros listeners que o ESC já foi tratado
      fecharResolucao();
    }
  });

  document.addEventListener('submit', async e => {
    if (e.target.id !== 'resolverForm') return;
    e.preventDefault();
    if (!atual) return;
    const solucao = document.getElementById('rsSolucao').value.trim();
    const componente = document.getElementById('rsComponente').value.trim();
    const erro = document.getElementById('rsErro');
    if (solucao.length < 5) {
      erro.textContent = 'Descreva a solução aplicada.';
      erro.hidden = false;
      document.getElementById('rsSolucao').focus();
      return;
    }
    const btn = document.getElementById('rsConfirmar');
    btn.disabled = true;
    const { id, onDone } = atual;
    try {
      const data = await postJSON(`/ocorrencias/${id}/resolver`,
        { solucao_aplicada: solucao, componente_real: componente });
      fecharResolucao();
      toast(`Ocorrência #${id} resolvida.`);
      if (onDone) onDone(data);
    } catch (err) {
      erro.textContent = err.message;
      erro.hidden = false;
      btn.disabled = false;
    }
  });

  window.OcorrenciaAcoes = { abrirResolucao, iniciarAtendimento, toast };
})();
