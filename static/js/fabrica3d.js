/**
 * Vista 3D da fábrica (templates/fabrica.html).
 * Monta numa cena só o CAD de cada máquina, na posição do mapa 2D (x/y em %),
 * com as áreas de cada setor no piso e a situação de cada máquina (anel colorido
 * e etiqueta). Clique numa máquina → onSelect(id); a página mostra o painel.
 *
 *   const f3d = await criarFabrica3D(elemento, { onSelect: (id) => {} });
 *   f3d.atualizar(maquinas, selecionada);   // a cada atualização da página
 *   f3d.selecionar(id | null);              // voa até a máquina / volta à visão geral
 *   f3d.ligar(true | false);                // renderiza só com a vista aberta
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Viewer3D } from '/static/js/viewer3d/viewer.js';

const LARG = 40, PROF = 22.5;               // planta 16:9 em unidades de cena
const COR = { ok: 0x059669, atencao: 0xD97706, parada: 0xDC2626 };
const COR_SELECAO = 0x0EA5E9;
// ponytail: tamanho de cada modelo no mapa (maior dimensão, em unidades de cena) —
// escala "de vitrine", não real: um torno de bancada ao lado de um robô sumiria.
// Modelo novo sem entrada usa o padrão; mover para o modelo.json se a lista crescer.
const TAMANHO = { 'robo-abb-irb6700': 4.6, 'torno-cx704': 4.2, 'bomba-ksb-etanorm': 4,
                  'compressor-parafuso': 3.2, 'motor-weg-w22': 2.8 };
const TAMANHO_PADRAO = 4;

const naPlanta = (x, y) => new THREE.Vector3((x / 100 - 0.5) * LARG, 0, (y / 100 - 0.5) * PROF);

function el(tag, classe, ...filhos) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  filhos.forEach(f => f != null && e.append(f));
  return e;
}

/** Texto "pintado" no piso (nome da área), como na planta 2D. */
function textoNoChao(texto, altura) {
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  const fonte = '700 64px Inter, system-ui, sans-serif';
  ctx.font = fonte;
  ctx.letterSpacing = '6px';
  const w = Math.ceil(ctx.measureText(texto).width) + 24;
  c.width = w; c.height = 96;
  ctx.font = fonte;
  ctx.letterSpacing = '6px';
  ctx.fillStyle = '#475569';
  ctx.textBaseline = 'middle';
  ctx.fillText(texto, 12, 50);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  const largura = altura * w / 96;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(largura, altura),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2;
  m.userData.largura = largura;
  return m;
}

export async function criarFabrica3D(container, { onSelect } = {}) {
  // ── Cena ──────────────────────────────────────────────────────────────
  const w0 = container.clientWidth || 900, h0 = container.clientHeight || 500;
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(w0, h0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.domElement.className = 'fb3-canvas';
  container.append(renderer.domElement);

  const etiquetas = new CSS2DRenderer();
  etiquetas.setSize(w0, h0);
  etiquetas.domElement.className = 'fb3-etiquetas';
  container.append(etiquetas.domElement);

  const carregando = el('div', 'fb3-carregando', el('i', 'fas fa-circle-notch fa-spin'), el('span', '', 'Montando a fábrica em 3D…'));
  container.append(carregando);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xE2E8F0);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(40, w0 / h0, 0.5, 400);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.maxPolarAngle = Math.PI * 0.47;
  controls.minDistance = 4;
  controls.maxDistance = 70;
  controls.screenSpacePanning = false;        // arrastar com o botão direito anda pelo piso

  const sol = new THREE.DirectionalLight(0xffffff, 2.2);
  sol.position.set(12, 30, 18);
  sol.castShadow = true;
  sol.shadow.mapSize.set(4096, 4096);
  Object.assign(sol.shadow.camera, { left: -26, right: 26, top: 18, bottom: -18, near: 1, far: 90 });
  sol.shadow.bias = -0.0004;
  scene.add(sol, new THREE.HemisphereLight(0xffffff, 0xb8c2cc, 0.6));

  // Piso da fábrica: planta clara com grade, em volta um piso mais escuro
  const piso = new THREE.Mesh(new THREE.PlaneGeometry(LARG, PROF), new THREE.MeshStandardMaterial({ color: 0xF8FAFC, roughness: 0.95 }));
  piso.rotation.x = -Math.PI / 2;
  piso.receiveShadow = true;
  const grade = new THREE.GridHelper(LARG, 20, 0xE2E8F0, 0xE2E8F0);
  grade.scale.z = PROF / LARG;
  grade.position.y = 0.005;
  const borda = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(LARG, 0.01, PROF)),
    new THREE.LineBasicMaterial({ color: 0x94A3B8 }));
  scene.add(piso, grade, borda);

  const camadaAreas = new THREE.Group();
  const camadaMaquinas = new THREE.Group();
  scene.add(camadaAreas, camadaMaquinas);

  // ── Câmera ────────────────────────────────────────────────────────────
  let voo = null;
  // Visão geral: menor distância em que os cantos da planta (e o alto das máquinas do fundo)
  // cabem na tela — busca binária, vale para tela deitada ou em pé
  const visaoGeral = () => {
    const alvo = new THREE.Vector3(0, 0, 0.5);
    const dir = (camera.aspect < 1 ? new THREE.Vector3(0, 0.88, 0.5) : new THREE.Vector3(0, 0.68, 0.8)).normalize();
    const cantos = [[-1, -1, 5], [1, -1, 5], [1, 1, 0], [-1, 1, 0]]
      .map(([sx, sz, y]) => new THREE.Vector3(sx * LARG / 2, y, sz * PROF / 2));
    const cam = camera.clone();
    let perto = 5, longe = 250;
    for (let i = 0; i < 24; i++) {
      const d = (perto + longe) / 2;
      cam.position.copy(alvo).addScaledVector(dir, d);
      cam.lookAt(alvo);
      cam.updateMatrixWorld();
      const cabe = cantos.every(p => { const v = p.clone().project(cam); return Math.abs(v.x) <= 0.97 && Math.abs(v.y) <= 0.92; });
      if (cabe) longe = d; else perto = d;
    }
    return { pos: alvo.clone().addScaledVector(dir, longe), alvo };
  };
  const voarPara = ({ pos, alvo }, animar = true) => {
    if (!animar) { camera.position.copy(pos); controls.target.copy(alvo); controls.update(); return; }
    voo = { t: 0, p0: camera.position.clone(), p1: pos, a0: controls.target.clone(), a1: alvo };
  };

  // ── Máquinas ──────────────────────────────────────────────────────────
  const maquinas3d = new Map();       // id → { grupo, anel, disco, tag, meshes, raio, altura, dados }
  const cacheGLB = new Map();         // arquivo → Promise<Object3D> (os dois tornos usam o mesmo CAD)
  let selecionada = null, sobre = null;

  async function montarModelo(m) {
    const r = await fetch(`/api/maquinas/${m.id}/modelo3d`);
    const info = r.ok ? await r.json() : null;
    const modelo = info?.modelo;
    if (!modelo || modelo.fonte !== 'glb') return null;
    if (!cacheGLB.has(modelo.arquivo)) cacheGLB.set(modelo.arquivo, Viewer3D.carregarGLB(modelo));
    const obj = (await cacheGLB.get(modelo.arquivo)).clone(true);
    obj.traverse(o => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      o.material = o.material.clone();           // destaque de uma máquina não vaza para a outra
      let dono = o;
      while (dono && !dono.userData.componentId) dono = dono.parent;
      if (dono?.userData.cor && o.material.color) {  // mesma cor do visualizador da máquina
        o.material.color.set(dono.userData.cor);
        o.material.map = null;
        o.material.vertexColors = false;
      }
    });
    // Normaliza: maior dimensão = tamanho do modelo no mapa, centrado e apoiado no piso
    const caixa = new THREE.Box3().setFromObject(obj);
    const tam = caixa.getSize(new THREE.Vector3());
    obj.scale.setScalar((TAMANHO[modelo.modelo] || TAMANHO_PADRAO) / Math.max(tam.x, tam.y, tam.z));
    const c = new THREE.Box3().setFromObject(obj);
    obj.position.set(-(c.min.x + c.max.x) / 2, -c.min.y, -(c.min.z + c.max.z) / 2);
    return obj;
  }

  function caixaGenerica() {
    // Máquina sem CAD: bloco neutro, para ela não sumir do mapa
    const g = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.6, 2.4), new THREE.MeshStandardMaterial({ color: 0x94A3B8, roughness: 0.7 }));
    g.position.y = 0.8;
    g.castShadow = g.receiveShadow = true;
    return g;
  }

  function criarEtiqueta(m) {
    const tag = el('button', 'fb3-tag');
    tag.type = 'button';
    tag.addEventListener('click', (ev) => { ev.stopPropagation(); onSelect?.(m.id); });
    return tag;
  }

  function preencherEtiqueta(item) {
    const m = item.dados;
    const partes = [el('i', `fb3-bola ${m.status}`),
                    el('span', 'fb3-nome-longo', m.nome), el('span', 'fb3-nome-curto', m.nome.split(' ').pop())];
    if (m.total_abertas) partes.push(el('b', '', String(m.total_abertas)));
    item.tag.replaceChildren(...partes);
    item.tag.className = `fb3-tag ${m.status}${selecionada === m.id ? ' sel' : ''}`;
    item.tag.title = m.nome;
    item.tag.setAttribute('aria-label', `${m.nome}${m.total_abertas ? ', ' + m.total_abertas + ' ocorrência(s) aberta(s)' : ''}`);
  }

  async function adicionarMaquina(m) {
    const grupo = new THREE.Group();
    grupo.userData.maquinaId = m.id;
    const item = { grupo, dados: m, meshes: [], raio: 2, altura: 2 };
    maquinas3d.set(m.id, item);
    camadaMaquinas.add(grupo);

    let modelo = null;
    if (m.cad) {
      try { modelo = await montarModelo(m); } catch (e) { console.error(`[fábrica 3D] ${m.nome}`, e); }
    }
    if (!maquinas3d.has(m.id)) return;           // removida enquanto carregava
    const corpo = modelo || caixaGenerica();
    grupo.add(corpo);
    corpo.traverse(o => { if (o.isMesh) item.meshes.push(o); });
    const caixa = new THREE.Box3().setFromObject(corpo);
    const tam = caixa.getSize(new THREE.Vector3());
    item.raio = Math.max(tam.x, tam.z) * 0.45 + 0.3;
    item.altura = tam.y;

    // Situação no piso: disco translúcido + anel na cor do status
    item.disco = new THREE.Mesh(new THREE.CircleGeometry(item.raio, 48),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.16, depthWrite: false }));
    item.anel = new THREE.Mesh(new THREE.RingGeometry(item.raio - 0.14, item.raio, 64),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.9, depthWrite: false }));
    for (const d of [item.disco, item.anel]) { d.rotation.x = -Math.PI / 2; d.position.y = 0.02; grupo.add(d); }

    item.tag = criarEtiqueta(m);
    const rotulo = new CSS2DObject(item.tag);
    rotulo.position.set(0, item.altura + 0.5, 0);
    grupo.add(rotulo);
    aplicarDados(item, item.dados);               // dados mais recentes (a página pode ter atualizado)
  }

  function aplicarDados(item, m) {
    item.dados = m;
    item.grupo.position.copy(naPlanta(m.x, m.y));
    if (!item.anel) return;                        // ainda carregando: aplica ao terminar
    item.anel.material.color.setHex(COR[m.status] || COR.ok);
    item.disco.material.color.setHex(COR[m.status] || COR.ok);
    preencherEtiqueta(item);
    pintar(item);
  }

  function pintar(item) {
    const id = item.dados.id;
    const [cor, forca] = id === selecionada ? [COR_SELECAO, 0.2] : id === sobre ? [COR_SELECAO, 0.12] : [0x000000, 0];
    item.meshes.forEach(o => { if (o.material.emissive) { o.material.emissive.setHex(cor); o.material.emissiveIntensity = forca || 1; } });
  }

  // ── Áreas (setores) no piso: mesmo cálculo das zonas da planta 2D ───────
  function desenharAreas(lista) {
    camadaAreas.children.forEach(o => o.traverse(x => { x.geometry?.dispose(); x.material?.map?.dispose(); x.material?.dispose(); }));
    camadaAreas.clear();
    const setores = {};
    lista.forEach(m => (setores[m.setor || 'Sem setor'] ||= []).push(m));
    for (const [nome, grupo] of Object.entries(setores)) {
      const xs = grupo.map(m => m.x), ys = grupo.map(m => m.y);
      const a = naPlanta(Math.max(1, Math.min(...xs) - 8), Math.max(1, Math.min(...ys) - 17));
      const b = naPlanta(Math.min(99, Math.max(...xs) + 8), Math.min(99, Math.max(...ys) + 15));
      const larg = b.x - a.x, prof = b.z - a.z;
      const fundo = new THREE.Mesh(new THREE.PlaneGeometry(larg, prof),
        new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6, depthWrite: false }));
      fundo.rotation.x = -Math.PI / 2;
      fundo.position.set(a.x + larg / 2, 0.008, a.z + prof / 2);
      const contorno = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(a.x, 0.012, a.z), new THREE.Vector3(b.x, 0.012, a.z),
        new THREE.Vector3(b.x, 0.012, b.z), new THREE.Vector3(a.x, 0.012, b.z)]),
        new THREE.LineDashedMaterial({ color: 0x94A3B8, dashSize: 0.6, gapSize: 0.4 }));
      contorno.computeLineDistances();
      // Nome na borda da frente da área: fica legível e nenhuma máquina o cobre
      const rotulo = textoNoChao(nome.toUpperCase(), 1.05);
      const caber = Math.min(1, (larg - 0.8) / rotulo.userData.largura);   // nome longo em área estreita encolhe
      rotulo.scale.setScalar(caber);
      rotulo.position.set(a.x + 0.4 + rotulo.userData.largura * caber / 2, 0.015, b.z - 0.75 * Math.max(caber, 0.6));
      camadaAreas.add(fundo, contorno, rotulo);
    }
  }

  // ── Interação ─────────────────────────────────────────────────────────
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  function maquinaEm(ev) {
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    for (const h of ray.intersectObject(camadaMaquinas, true)) {
      let o = h.object;
      while (o && o.userData.maquinaId == null) o = o.parent;
      if (o) return o.userData.maquinaId;
    }
    return null;
  }
  let inicio = null;
  renderer.domElement.addEventListener('pointerdown', (ev) => { inicio = { x: ev.clientX, y: ev.clientY }; });
  renderer.domElement.addEventListener('pointerup', (ev) => {
    if (!inicio || Math.hypot(ev.clientX - inicio.x, ev.clientY - inicio.y) > 6) return;   // arrastou = girou a câmera
    onSelect?.(maquinaEm(ev));
  });
  renderer.domElement.addEventListener('pointermove', (ev) => {
    if (ev.pointerType !== 'mouse') return;
    const id = maquinaEm(ev);
    if (id === sobre) return;
    const antes = maquinas3d.get(sobre);
    sobre = id;
    if (antes) pintar(antes);
    if (maquinas3d.get(id)) pintar(maquinas3d.get(id));
    renderer.domElement.style.cursor = id ? 'pointer' : '';
  });

  // ── Loop (só com a vista aberta) ──────────────────────────────────────
  const relogio = new THREE.Timer();
  function quadro() {
    relogio.update();
    const dt = relogio.getDelta(), t = relogio.getElapsed();
    if (voo) {
      voo.t = Math.min(1, voo.t + dt / 0.9);
      const e = voo.t < 0.5 ? 4 * voo.t ** 3 : 1 - (-2 * voo.t + 2) ** 3 / 2;
      camera.position.lerpVectors(voo.p0, voo.p1, e);
      controls.target.lerpVectors(voo.a0, voo.a1, e);
      if (voo.t >= 1) voo = null;
    }
    // Máquina parada: anel pulsando
    const pulso = 1 + 0.12 * (Math.sin(t * 4) + 1) / 2;
    for (const item of maquinas3d.values()) {
      if (item.anel) item.anel.scale.setScalar(item.dados.status === 'parada' ? pulso : 1);
    }
    controls.update();
    renderer.render(scene, camera);
    etiquetas.render(scene, camera);
  }

  const ro = new ResizeObserver(() => {
    const w = container.clientWidth, h = container.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    etiquetas.setSize(w, h);
  });
  ro.observe(container);

  // ── API ───────────────────────────────────────────────────────────────
  const api = {
    async atualizar(lista, sel = selecionada) {
      desenharAreas(lista);
      const ids = new Set(lista.map(m => m.id));
      for (const [id, item] of maquinas3d) {
        if (!ids.has(id)) { camadaMaquinas.remove(item.grupo); maquinas3d.delete(id); }
      }
      selecionada = sel;
      const novas = [];
      for (const m of lista) {
        const item = maquinas3d.get(m.id);
        if (item) aplicarDados(item, m);
        else novas.push(adicionarMaquina(m));
      }
      await Promise.all(novas);
      carregando.hidden = true;
    },
    selecionar(id) {
      const antes = maquinas3d.get(selecionada);
      selecionada = id;
      if (antes) { pintar(antes); preencherEtiqueta(antes); }
      const item = maquinas3d.get(id);
      if (!item) { voarPara(visaoGeral()); return; }
      pintar(item);
      preencherEtiqueta(item);
      const alvo = item.grupo.position.clone().setY(item.altura * 0.4);
      const dist = Math.max(item.raio * 3.2, item.altura * 2.4, 9);
      voarPara({ pos: alvo.clone().add(new THREE.Vector3(0.35, 0.6, 1).normalize().multiplyScalar(dist)), alvo });
    },
    enquadrar() { voarPara(visaoGeral()); },
    ligar(ativo) {
      renderer.setAnimationLoop(ativo ? quadro : null);
      if (ativo) relogio.reset?.();
    },
  };

  voarPara(visaoGeral(), false);
  return api;
}
