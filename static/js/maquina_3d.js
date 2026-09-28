/**
 * Página 3D da máquina com mapa de calor de falhas (templates/maquina_3d.html).
 * Cada peça é pintada pela quantidade de falhas; a lista ao lado traz as
 * ocorrências e as soluções de cada peça. "Frota do modelo" soma as máquinas
 * que usam o mesmo CAD.
 */
import { Viewer3D } from '/static/js/viewer3d/viewer.js';

const MID = window.MAQUINA_3D.id;
const $ = (id) => document.getElementById(id);
const estado = { frota: false, calor: true, dados: null, aberto: null };

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

// Mesma escala do visualizador: vermelho claro (1 falha) → vermelho escuro (máximo)
function corDe(n, max) {
  if (!n) return '#E2E6EB';
  const t = max > 1 ? (n - 1) / (max - 1) : 1;
  const a = [0xFC, 0xA5, 0xA5], b = [0x99, 0x1B, 0x1B];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(',')})`;
}

const viewer = new Viewer3D($('stage'), {
  // O brilho de seleção se misturaria com as cores do calor: a seleção aparece na lista
  onSelect: (id) => { viewer.selecionar(null); if (id) abrir(id, false); },
  onRaioX: (ativo) => $('btnRaioX').classList.toggle('ativo', ativo),
});
$('btnEnquadrar').addEventListener('click', () => viewer.enquadrar());
$('btnRaioX').addEventListener('click', () => {
  const ativo = !$('btnRaioX').classList.contains('ativo');
  $('btnRaioX').classList.toggle('ativo', ativo);
  viewer.raioX(ativo);
});

async function carregarModelo() {
  const r = await fetch(`/api/maquinas/${MID}/modelo3d`);
  const info = await r.json();
  await viewer.carregar(info.modelo, info.componentes);
  $('carregando').hidden = true;
}

async function carregarCalor() {
  const r = await fetch(`/api/maquinas/${MID}/calor?frota=${estado.frota ? 1 : 0}`);
  estado.dados = await r.json();
  const n = estado.dados.maquinas_na_frota;
  $('btnFrota').textContent = `Frota do modelo (${n})`;
  $('btnFrota').disabled = n < 2;
  pintar();
  montarLista();
}

function pintar() {
  const comps = estado.dados.componentes;
  const max = Math.max(0, ...comps.map(c => c.falhas));
  $('legMax').textContent = String(Math.max(1, max));
  viewer.mapaDeCalor(estado.calor ? Object.fromEntries(comps.map(c => [c.id, c.falhas])) : null);
  $('legenda').style.visibility = estado.calor ? 'visible' : 'hidden';
}

function montarLista() {
  const comps = estado.dados.componentes;
  const max = Math.max(0, ...comps.map(c => c.falhas));
  $('lista').replaceChildren(...comps.map(c => {
    const det = el('div', { class: 'mc-det' });
    if (!c.ocorrencias.length) det.append(el('small', { class: 'mc-sub' }, 'Nenhuma falha registrada nesta peça.'));
    c.ocorrencias.forEach(o => det.append(el('a', { class: 'mc-oc', href: `/ocorrencia/${o.id}` },
      el('b', {}, o.descricao),
      el('small', {}, `${o.quando}${estado.frota ? ' · ' + o.maquina : ''} · ${o.status}`),
      o.solucao ? el('small', { class: 'sol' }, `Solução: ${o.solucao}`) : null)));
    if (c.falhas > c.ocorrencias.length) det.append(el('small', { class: 'mc-sub' }, `+ ${c.falhas - c.ocorrencias.length} mais antiga(s)`));
    const n = el('span', { class: 'mc-n' }, String(c.falhas));
    if (c.abertas) n.append(el('small', {}, `${c.abertas} aberta${c.abertas > 1 ? 's' : ''}`));
    const botao = el('button', { type: 'button', 'aria-expanded': 'false', onclick: () => abrir(c.id, true) },
      el('span', { class: 'mc-cor', style: `background:${estado.calor ? corDe(c.falhas, max) : 'var(--border)'}` }),
      el('span', { class: 'mc-nome' }, c.nome, el('small', {}, c.ultima ? `última falha ${c.ultima}` : c.tipo)),
      n);
    return el('div', { class: 'mc-item' + (estado.aberto === c.id ? ' aberto' : ''), 'data-id': c.id }, botao, det);
  }));
}

function abrir(id, focar) {
  estado.aberto = estado.aberto === id && focar ? null : id;
  document.querySelectorAll('.mc-item').forEach(it => {
    const sim = it.dataset.id === estado.aberto;
    it.classList.toggle('aberto', sim);
    it.querySelector('button').setAttribute('aria-expanded', String(sim));
    if (sim && !focar) it.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
  if (estado.aberto && focar) viewer.focar(estado.aberto);
}

document.querySelectorAll('#segEscopo button').forEach(b => b.addEventListener('click', () => {
  estado.frota = b.dataset.frota === '1';
  document.querySelectorAll('#segEscopo button').forEach(x => x.classList.toggle('ativo', x === b));
  carregarCalor();
}));
document.querySelectorAll('#segCalor button').forEach(b => b.addEventListener('click', () => {
  estado.calor = b.dataset.calor === '1';
  document.querySelectorAll('#segCalor button').forEach(x => x.classList.toggle('ativo', x === b));
  pintar();
  montarLista();
}));

await carregarModelo();
await carregarCalor();
