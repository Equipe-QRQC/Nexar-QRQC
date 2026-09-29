/**
 * Nova ocorrência guiada pelo 3D (templates/CadastroOcorrencia.html).
 * Máquina → peça tocada no modelo CAD → sintoma e perguntas rápidas → enviar.
 * Ao escolher a peça, mostra as soluções que já funcionaram nela.
 */
import { Viewer3D } from '/static/js/viewer3d/viewer.js';

const CFG = window.NOVA_OCORRENCIA || {};
const $ = (id) => document.getElementById(id);

const estado = { maquina: null, componentes: [], peca: null, sintoma: null, parada: null, risco: null };
let viewer = null;

// ── Utilidades ──────────────────────────────────────────────────────────────
function el(tag, attrs = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  filhos.forEach(f => f != null && e.append(f));
  return e;
}
const icone = (cls) => el('i', { class: `fas ${cls}` });

function passo(n) {
  document.querySelectorAll('#passos li').forEach(li => {
    const p = +li.dataset.passo;
    li.classList.toggle('feito', p < n);
    li.classList.toggle('atual', p === n);
  });
}

function rolarPara(elemento) {
  // No celular o painel fica abaixo do 3D: leva o usuário até a próxima etapa
  if (window.matchMedia('(max-width: 900px)').matches) {
    elemento.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ── 1. Máquina ──────────────────────────────────────────────────────────────
function iniciarViewer() {
  if (viewer) return;
  viewer = new Viewer3D($('stage'), {
    onPick: (id) => escolherPeca(id, { doModelo: true }),
    onRaioX: (ativo) => $('btnRaioX').classList.toggle('ativo', ativo),
  });
  $('btnEnquadrar').addEventListener('click', () => viewer.enquadrar());
  $('btnRaioX').addEventListener('click', () => {
    const ativo = !$('btnRaioX').classList.contains('ativo');
    $('btnRaioX').classList.toggle('ativo', ativo);
    viewer.raioX(ativo);
  });
  $('sliderExplodir').addEventListener('input', (e) => viewer.explodir(e.target.value / 100));
  $('sliderExplodir').addEventListener('change', () => viewer.enquadrar());   // reenquadra ao soltar
}

async function escolherMaquina(botao) {
  const id = +botao.dataset.id;
  estado.maquina = id;
  $('fMaquina').value = id;
  limparPeca();

  // Lista vira um cartão compacto com a máquina escolhida
  $('listaMaquinas').hidden = true;
  $('trocarMaquina').hidden = false;
  const esc = $('maquinaEscolhida');
  esc.replaceChildren(botao.querySelector('.no-maquina-ic').cloneNode(true),
                      botao.querySelector('.no-maquina-txt').cloneNode(true));
  esc.hidden = false;

  $('galeria').hidden = true;
  $('stageVazio').hidden = true;
  $('stageCarregando').hidden = false;
  $('palcoBarra').hidden = false;
  $('palcoTitulo').textContent = botao.dataset.nome;
  iniciarViewer();

  try {
    const r = await fetch(`/api/maquinas/${id}/modelo3d`);
    const info = await r.json();
    if (!r.ok || !info.modelo) throw new Error(info.erro || 'Modelo 3D indisponível.');
    if (estado.maquina !== id) return;          // trocou de máquina durante o carregamento
    await viewer.carregar(info.modelo, info.componentes);
    estado.componentes = info.componentes;
    $('btnRaioX').classList.remove('ativo');
    $('sliderExplodir').value = 0;
    viewer.ativarMarcacao(true);
    montarListaPecas();
    $('etapaPeca').hidden = false;
    $('dicaToque').hidden = false;
    setTimeout(() => { $('dicaToque').hidden = true; }, 5000);
    passo(2);
    if (CFG.componente && estado.componentes.some(c => c.component_id === CFG.componente)) {
      escolherPeca(CFG.componente);
      CFG.componente = null;
    }
  } catch (e) {
    console.error(e);
    $('stageVazio').hidden = false;
    $('stageVazio').querySelector('p').textContent = 'Não foi possível carregar o modelo 3D desta máquina.';
  } finally {
    $('stageCarregando').hidden = true;
  }
}

function trocarMaquina() {
  estado.maquina = null;
  $('galeria').hidden = false;
  $('palcoBarra').hidden = true;
  $('dicaToque').hidden = true;
  $('listaMaquinas').hidden = false;
  $('maquinaEscolhida').hidden = true;
  $('trocarMaquina').hidden = true;
  $('etapaPeca').hidden = true;
  limparPeca();
  passo(1);
}

// ── 2. Peça ─────────────────────────────────────────────────────────────────
function montarListaPecas() {
  const lista = $('listaPecas');
  lista.replaceChildren(...estado.componentes.map(c =>
    el('button', { type: 'button', class: 'no-chip', 'data-id': c.component_id,
                   onclick: () => escolherPeca(c.component_id) }, c.name)));
}

async function escolherPeca(id, { doModelo = false } = {}) {
  const comp = estado.componentes.find(c => c.component_id === id);
  if (!comp) return;
  estado.peca = id;
  $('fComponente').value = id;

  viewer.selecionar(id);
  viewer.destacar([{ id, severidade: 'op', texto: comp.name }]);
  if (!doModelo) viewer.focar(id);

  $('pecaNome').textContent = comp.name;
  $('pecaDescricao').textContent = comp.description || '';
  $('pecaEscolhida').hidden = false;
  $('escolherPeca').hidden = true;
  document.querySelectorAll('#listaPecas .no-chip').forEach(b => b.classList.toggle('ativo', b.dataset.id === id));

  const r = await fetch(`/api/maquinas/${estado.maquina}/componentes/${encodeURIComponent(id)}/sintomas`);
  const info = r.ok ? await r.json() : null;
  if (estado.peca !== id) return;
  montarSintomas(info?.sintomas || []);
  montarHistorico(info?.historico);
  $('etapaSintoma').hidden = false;
  $('barraEnviar').hidden = false;
  passo(3);
  atualizar();
  rolarPara($('etapaPeca'));
}

function limparPeca() {
  estado.peca = null;
  estado.sintoma = null;
  $('fComponente').value = '';
  $('fSintoma').value = '';
  $('pecaEscolhida').hidden = true;
  $('escolherPeca').hidden = false;
  $('etapaSintoma').hidden = true;
  $('etapaHistorico').hidden = true;
  $('barraEnviar').hidden = true;
  if (viewer) {
    viewer.limparDestaques();
    viewer.limparPonto();
    viewer.selecionar(null);
  }
  document.querySelectorAll('#listaPecas .no-chip').forEach(b => b.classList.remove('ativo'));
}

// ── 3. Sintoma e perguntas ──────────────────────────────────────────────────
function montarSintomas(sintomas) {
  estado.sintoma = null;
  $('fSintoma').value = '';
  $('listaSintomas').replaceChildren(...sintomas.map(s =>
    el('button', { type: 'button', class: 'no-chip no-sintoma', role: 'radio', 'aria-checked': 'false',
                   'data-id': s.id, onclick: (ev) => escolherSintoma(s.id, ev.currentTarget) },
       icone(s.icone), s.nome)));
}

function escolherSintoma(id, botao) {
  estado.sintoma = id;
  $('fSintoma').value = id;
  document.querySelectorAll('#listaSintomas .no-chip').forEach(b => {
    const ativo = b === botao;
    b.classList.toggle('ativo', ativo);
    b.setAttribute('aria-checked', String(ativo));
  });
  $('textoOpc').textContent = id === 'outro' ? '(obrigatório)' : '(opcional)';
  atualizar();
}

function montarHistorico(hist) {
  const lista = $('listaHistorico');
  if (!hist || !hist.itens.length) {
    $('etapaHistorico').hidden = true;
    return;
  }
  lista.replaceChildren(...hist.itens.slice(0, 3).map(h =>
    el('a', { class: 'no-hist', href: `/ocorrencia/${h.id}`, target: '_blank', rel: 'noopener' },
       el('span', { class: 'no-hist-sol' }, icone('fa-wrench'), ' ', h.solucao),
       el('small', {}, `${h.descricao} · ${h.mesma_maquina ? 'esta máquina' : h.maquina} · ${h.data}`))));
  if (hist.total > 3) lista.append(el('small', { class: 'no-hist-mais' }, `+ ${hist.total - 3} registro(s) nesta peça`));
  $('etapaHistorico').hidden = false;
}

document.querySelectorAll('.no-simnao').forEach(grupo => {
  grupo.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    grupo.querySelectorAll('button').forEach(x => x.classList.toggle('ativo', x === b));
    $(grupo.dataset.campo).value = b.dataset.v;
    if (grupo.dataset.campo === 'fParada') estado.parada = b.dataset.v === '1';
    else estado.risco = b.dataset.v === '1';
    atualizar();
  }));
});

function atualizar() {
  const texto = $('fTexto').value.trim();
  const ok = estado.maquina && estado.peca && estado.sintoma &&
             estado.parada !== null && estado.risco !== null &&
             (estado.sintoma !== 'outro' || texto.length >= 5);
  $('btnEnviar').disabled = !ok;

  const impacto = $('fImpacto').value || ((estado.parada || estado.risco) ? 'Alto' : 'Médio');
  const faltam = [];
  if (!estado.sintoma) faltam.push('o que está acontecendo');
  if (estado.parada === null) faltam.push('se a máquina parou');
  if (estado.risco === null) faltam.push('se há risco');
  $('resumo').replaceChildren(faltam.length
    ? el('span', {}, icone('fa-circle-info'), ` Falta informar ${faltam.join(', ')}.`)
    : el('span', {}, icone('fa-circle-check'), ' Impacto ', el('b', { class: `no-imp-${impacto}` }, impacto),
         estado.risco ? ' · registrada como Segurança' : ''));
}
$('fTexto').addEventListener('input', atualizar);
$('fImpacto').addEventListener('change', atualizar);

// ── Envio ───────────────────────────────────────────────────────────────────
$('formOcorrencia').addEventListener('submit', (ev) => {
  if ($('btnEnviar').disabled) { ev.preventDefault(); return; }
  $('btnEnviar').disabled = true;
  $('analisando').hidden = false;
});
// Voltar do navegador com a página em cache: some o "analisando"
window.addEventListener('pageshow', () => { $('analisando').hidden = true; atualizar(); });

// ── Início ──────────────────────────────────────────────────────────────────
document.querySelectorAll('.no-maquina').forEach(b => b.addEventListener('click', () => escolherMaquina(b)));
// Cartão da galeria escolhe pelo botão correspondente da lista (de onde sai o cartão compacto)
document.querySelectorAll('.no-gcard').forEach(c => c.addEventListener('click', () =>
  escolherMaquina(document.querySelector(`.no-maquina[data-id="${c.dataset.id}"]`))));
$('trocarMaquina').addEventListener('click', trocarMaquina);
$('trocarPeca').addEventListener('click', () => { limparPeca(); passo(2); });
$('buscaMaquina')?.addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('.no-maquina, .no-gcard').forEach(b => {
    b.hidden = q && !`${b.dataset.nome} ${b.dataset.setor}`.toLowerCase().includes(q);
  });
});

if (CFG.risco) document.querySelector('[data-campo="fRisco"] [data-v="1"]').click();
const inicial = CFG.preselect && document.querySelector(`.no-maquina[data-id="${CFG.preselect}"]`);
if (inicial) escolherMaquina(inicial);
else if (document.querySelectorAll('.no-maquina').length === 1) escolherMaquina(document.querySelector('.no-maquina'));
