/**
 * Cartão 3D reutilizável (formulário de ocorrência e página da ocorrência).
 *
 *   const card = await criarCard3D(elemento, {
 *     maquinaId, modo: 'ver' | 'marcar',
 *     destaques: [{component_id, severity}], apontado: {component_id, component_name},
 *     linkCompleto: '/qrqc3d/12', onPick: (id, nome) => {}, onSemModelo: () => {},
 *   });
 *   await card.trocarMaquina(outroId);
 */
import { Viewer3D } from './viewer.js';

function el(tag, attrs = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;   // só com conteúdo estático
    else e.setAttribute(k, v);
  }
  filhos.forEach(f => f != null && e.append(f));
  return e;
}

export async function criarCard3D(container, opcoes) {
  const o = { modo: 'ver', destaques: [], ...opcoes };
  container.innerHTML = '';
  container.classList.add('v3d-card');

  const titulo = el('span', { class: 'v3d-titulo' }, el('i', { class: 'fas fa-cube' }), el('span', {}, o.titulo || 'Modelo 3D'));
  const fonte = el('span', { class: 'v3d-fonte' }, '');
  const bEnq = el('button', { class: 'v3d-btn', type: 'button', title: 'Enquadrar a máquina', html: '<i class="fas fa-expand"></i>' });
  const bRx = el('button', { class: 'v3d-btn', type: 'button', title: 'Raio-X: ver peças internas', html: '<i class="fas fa-x-ray"></i> Raio-X' });
  const barra = el('div', { class: 'v3d-toolbar' }, titulo, fonte, bEnq, bRx);
  if (o.linkCompleto) {
    barra.append(el('a', { class: 'v3d-btn', href: o.linkCompleto, title: 'Abrir a visualização completa',
                           'aria-label': 'Abrir a visualização completa',
                           html: '<i class="fas fa-up-right-and-down-left-from-center"></i>' }));
  }
  const palco = el('div', { class: 'v3d-stage' });
  const carregando = el('div', { class: 'v3d-carregando', html: '<i class="fas fa-circle-notch fa-spin"></i> Carregando modelo 3D…' });
  palco.append(carregando);
  const aviso = el('div', { class: 'v3d-aviso' });
  aviso.hidden = true;
  palco.append(aviso);
  container.append(barra, palco);

  let rodape = null;
  if (o.modo === 'marcar') {
    rodape = el('div', { class: 'v3d-legenda v3d-marcacao' });
    container.append(rodape);
  }

  const viewer = new Viewer3D(palco, {
    onPick: (id, nome) => {
      viewer.destacar([{ id, severidade: 'op', texto: `${nome} (indicado)` }]);
      mostrarMarcacao(nome);
      if (o.onPick) o.onPick(id, nome);
    },
    onRaioX: (ativo) => bRx.classList.toggle('ativo', ativo),
  });

  bEnq.addEventListener('click', () => viewer.enquadrar());
  bRx.addEventListener('click', () => {
    const ativo = !bRx.classList.contains('ativo');
    bRx.classList.toggle('ativo', ativo);
    viewer.raioX(ativo);
  });

  function mostrarMarcacao(nome) {
    if (!rodape) return;
    rodape.innerHTML = '';
    if (!nome) {
      rodape.append(el('span', { html: '<i class="fas fa-hand-pointer" style="background:none;width:auto;height:auto;color:var(--primary);margin-right:6px"></i>Opcional: toque na peça onde você viu o problema.' }));
      return;
    }
    const limpar = el('button', { class: 'v3d-btn', type: 'button', html: '<i class="fas fa-xmark"></i> Limpar' });
    limpar.style.marginLeft = 'auto';
    limpar.addEventListener('click', () => {
      viewer.limparPonto();
      viewer.selecionar(null);
      viewer.limparDestaques();
      mostrarMarcacao(null);
      if (o.onPick) o.onPick(null, null);
    });
    const txt = el('span', {});
    txt.append(el('i', { class: 'fas fa-location-dot', style: 'background:none;width:auto;height:auto;color:#DC2626' }),
               ' Local indicado: ', el('b', {}, nome));
    rodape.append(txt, limpar);
  }

  async function trocarMaquina(maquinaId) {
    o.maquinaId = maquinaId;
    carregando.style.display = '';
    const r = await fetch(`/api/maquinas/${maquinaId}/modelo3d`);
    const info = r.ok ? await r.json() : null;
    if (!info || !info.modelo) {
      carregando.style.display = 'none';
      if (o.onSemModelo) o.onSemModelo();
      return false;
    }
    if (!o.titulo) titulo.lastChild.textContent = info.maquina.nome;
    fonte.textContent = info.modelo.fonte === 'glb' ? 'Modelo do fabricante' : 'Modelo ilustrativo';
    fonte.classList.toggle('cad', info.modelo.fonte === 'glb');
    bRx.classList.remove('ativo');
    try {
      await viewer.carregar(info.modelo, info.componentes);
    } catch (e) {
      console.error(e);
      carregando.innerHTML = '<i class="fas fa-triangle-exclamation"></i> Não foi possível carregar o modelo 3D.';
      return false;
    }
    carregando.style.display = 'none';

    const lista = (o.destaques || []).map((d, i) => ({ id: d.component_id, severidade: d.severity, numero: i + 1 }));
    if (o.apontado && !lista.some(d => d.id === o.apontado.component_id)) {
      lista.push({ id: o.apontado.component_id, severidade: 'op', texto: `${o.apontado.component_name} (indicado pelo operador)` });
    }
    if (lista.length) {
      viewer.destacar(lista);
      // Foca a peça principal da IA; só a indicação do operador → máquina inteira
      if (o.destaques?.length) setTimeout(() => viewer.focar(lista[0].id), 300);
    }
    if (o.modo === 'marcar') {
      viewer.ativarMarcacao(true);
      mostrarMarcacao(null);
      aviso.innerHTML = '<i class="fas fa-hand-pointer"></i> Toque na peça onde está o problema';
      aviso.hidden = false;
      setTimeout(() => { aviso.hidden = true; }, 4000);
    }
    return true;
  }

  await trocarMaquina(o.maquinaId);
  return { viewer, trocarMaquina };
}
