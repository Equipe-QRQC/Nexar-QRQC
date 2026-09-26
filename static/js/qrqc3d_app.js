/**
 * Tela "Visualização 3D" da ocorrência: carrega o modelo da máquina, destaca
 * os componentes apontados (agente Nexar IA ou diagnóstico em texto), mostra o
 * histórico de soluções da peça clicada e dispara a investigação do agente.
 */
import { Viewer3D } from './viewer3d/viewer.js';

const CFG = window.QRQC3D;
const SEV_TXT = { high: 'Causa provável', medium: 'Verificar', low: 'Referência' };
const SEV_CLASSE = { high: 'severity-high', medium: 'severity-medium', low: 'severity-low' };
const PASSOS = {
  get_machine_info: 'Dados da máquina',
  get_machine_components: 'Componentes do modelo 3D',
  get_machine_history: 'Histórico de ocorrências',
  get_similar_occurrences: 'Falhas semelhantes',
  get_previous_solutions: 'Soluções já aplicadas',
  get_machine_documentation: 'Documentação técnica',
};

const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let viewer = null;
let destaques = CFG.destaques || [];

// ── Painel: lista de componentes apontados ────────────────────────────────
function renderDestaques() {
  const lista = $('hypothesis-list');
  if (!lista) return;
  $('secDestaques').style.display = destaques.length ? '' : 'none';
  lista.innerHTML = destaques.map((d, i) => `
    <div class="hypothesis-item" data-cid="${esc(d.component_id)}" tabindex="0">
      <div class="hyp-header">
        <span class="hyp-num sev-${esc(d.severity)}">${i + 1}</span>
        <span class="hyp-name">${esc(d.component_name || d.component_id)}</span>
        ${d.probability != null ? `<span class="hyp-prob">${Math.round(Number(d.probability) * 100)}%</span>`
                                 : `<span class="severity-badge ${SEV_CLASSE[d.severity] || ''}">${SEV_TXT[d.severity] || ''}</span>`}
      </div>
      ${d.reason ? `<div class="hyp-reason">${esc(d.reason)}</div>` : ''}
    </div>`).join('');
}

function renderAcoes(acoes) {
  const el = $('action-list');
  if (!el) return;
  el.innerHTML = (acoes || []).map((a, i) =>
    `<div class="action-item"><span class="action-num">${i + 1}</span><span>${esc(a)}</span></div>`).join('');
}

function aplicarDestaques() {
  if (!viewer) return;
  const lista = destaques.map((d, i) => ({ id: d.component_id, severidade: d.severity, numero: i + 1 }));
  const op = CFG.apontado;
  if (op && !lista.some(d => d.id === op.component_id)) {
    lista.push({ id: op.component_id, severidade: 'op', texto: `${op.component_name} (indicado pelo operador)` });
  }
  viewer.destacar(lista);
}

// ── Painel: componente selecionado + histórico de soluções ────────────────
async function mostrarComponente(id, nome) {
  const painel = $('compPanel');
  painel.classList.toggle('visible', !!id);
  if (!id) return;
  $('compNome').textContent = nome;
  const d = destaques.find(x => x.component_id === id);
  const sev = $('compSev');
  if (d) {
    sev.style.display = '';
    sev.className = 'severity-badge ' + (SEV_CLASSE[d.severity] || '');
    sev.textContent = SEV_TXT[d.severity] || '';
  } else {
    sev.style.display = 'none';
  }
  $('compMotivo').textContent = d?.reason || (d ? 'Citado no diagnóstico desta ocorrência.' : '');
  $('compFocar').onclick = () => viewer.focar(id);

  const hist = $('compHistorico');
  hist.innerHTML = '<span style="font-size:12px;color:var(--text-muted)"><i class="fas fa-circle-notch fa-spin"></i> Buscando histórico da peça…</span>';
  try {
    const r = await fetch(`/api/maquinas/${CFG.maquinaId}/componentes/${encodeURIComponent(id)}/historico`);
    const data = await r.json();
    if (!data.itens || !data.itens.length) {
      hist.innerHTML = '<div class="comp-hist-vazio">Nenhuma falha registrada nesta peça até agora.</div>';
      return;
    }
    hist.innerHTML = `
      <div class="panel-section-title" style="margin-bottom:6px;">
        Soluções já aplicadas nesta peça (${data.total})
      </div>
      ${data.itens.map(it => `
        <a class="comp-hist-item" href="/ocorrencia/${it.id}">
          <div class="comp-hist-top"><b>#${it.id}</b><span>${esc(it.data)}</span></div>
          <div class="comp-hist-prob">${esc(it.descricao)}</div>
          <div class="comp-hist-sol"><i class="fas fa-wrench"></i> ${esc(it.solucao)}</div>
        </a>`).join('')}`;
  } catch {
    hist.innerHTML = '';
  }
}

// ── Investigação do agente ────────────────────────────────────────────────
async function investigar() {
  const btn = $('btn-analyze');
  const overlay = $('investigation-overlay');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Investigando…';
  overlay.style.display = 'flex';
  $('inv-steps').innerHTML = '<div class="inv-step active"><span class="inv-step-icon"><i class="fas fa-circle-notch fa-spin"></i></span>Consultando dados da máquina…</div>';
  try {
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const res = await fetch(`/api/ai/analisar/${CFG.ocorrenciaId}`, {
      method: 'POST', headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Mostra as ferramentas que o agente realmente consultou
    const passos = [...new Set(data._steps || [])];
    $('inv-steps').innerHTML = passos.map(p =>
      `<div class="inv-step"><span class="inv-step-icon"><i class="fas fa-check-circle" style="color:var(--success)"></i></span>${esc(PASSOS[p] || p)}</div>`).join('');
    await new Promise(r => setTimeout(r, 900));

    const conhecidos = new Set(CFG.catalogo.map(c => c.component_id));
    destaques = (data.components || [])
      .filter(c => conhecidos.has(c.component_id))
      .sort((a, b) => (b.probability || 0) - (a.probability || 0))
      .map(c => ({ ...c, fonte: 'agente' }));
    $('tituloDestaques').textContent = 'Hipóteses da Nexar IA';
    renderDestaques();
    aplicarDestaques();
    if (destaques[0]) viewer.focar(destaques[0].component_id);

    $('summary-box').textContent = data.summary || '';
    const sev = $('overall-severity');
    sev.className = `severity-badge severity-${data.severity || 'low'}`;
    sev.textContent = { high: 'Alta', medium: 'Média', low: 'Baixa' }[data.severity] || '';
    if (data.pattern_analysis) {
      $('pattern-analysis').textContent = data.pattern_analysis;
      $('pattern-section').style.display = '';
    }
    renderAcoes(data.recommended_actions);
    $('result-sections').style.display = '';
    btn.innerHTML = '<i class="fas fa-robot"></i> Reanalisar com Nexar IA';
  } catch (e) {
    window.OcorrenciaAcoes?.toast?.(e.message, 'danger');
    alertaInline(e.message);
    btn.innerHTML = '<i class="fas fa-robot"></i> Investigar com Nexar IA';
  } finally {
    overlay.style.display = 'none';
    btn.disabled = false;
  }
}

function alertaInline(msg) {
  let el = $('erroAgente');
  if (!el) {
    el = document.createElement('p');
    el.id = 'erroAgente';
    el.style.cssText = 'font-size:12.5px;color:var(--danger);margin-top:8px;';
    $('btn-analyze').after(el);
  }
  el.textContent = msg;
}

// ── Inicialização ─────────────────────────────────────────────────────────
async function iniciar() {
  renderDestaques();
  renderAcoes(CFG.acoes);
  if (!CFG.modelo) return;

  viewer = new Viewer3D($('v3dStage'), {
    onSelect: (id, nome) => mostrarComponente(id, nome),
    onRaioX: (ativo) => $('btnRaioX')?.classList.toggle('ativo', ativo),
  });
  try {
    await viewer.carregar(CFG.modelo, CFG.catalogo);
  } catch (e) {
    console.error(e);
    $('v3dCarregando').innerHTML = '<i class="fas fa-triangle-exclamation"></i> Não foi possível carregar o modelo 3D.';
    return;
  }
  $('v3dCarregando')?.remove();
  aplicarDestaques();
  if (destaques[0]) setTimeout(() => viewer.focar(destaques[0].component_id), 400);

  $('btnEnquadrar')?.addEventListener('click', () => viewer.enquadrar());
  $('btnRaioX')?.addEventListener('click', (e) => {
    const ativo = !e.currentTarget.classList.contains('ativo');
    e.currentTarget.classList.toggle('ativo', ativo);
    viewer.raioX(ativo);
  });
  $('sliderExplodir')?.addEventListener('input', (e) => viewer.explodir(e.target.value / 100));
  $('sliderExplodir')?.addEventListener('change', () => viewer.enquadrar());   // reenquadra ao soltar
  $('btn-analyze')?.addEventListener('click', investigar);

  // Clique na lista → seleciona e voa até a peça
  $('hypothesis-list')?.addEventListener('click', (e) => {
    const item = e.target.closest('.hypothesis-item');
    if (!item) return;
    const id = item.dataset.cid;
    viewer.selecionar(id);
    viewer.focar(id);
    mostrarComponente(id, viewer.nomeDe(id));
  });
}

iniciar();
