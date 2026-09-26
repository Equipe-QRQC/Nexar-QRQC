/**
 * Nexar — Visualizador 3D de máquinas.
 *
 * Carrega o modelo 3D de uma máquina a partir de uma de duas fontes:
 *   - família em código  → static/js/viewer3d/familias/<familia>.js
 *   - GLB (CAD convertido) → arquivo + mapa "nó do CAD → component_id"
 * e expõe uma API para o diagnóstico: destacar componentes por gravidade,
 * voar até um componente, raio-X, vista explodida e seleção por toque.
 *
 * Convenção: todo componente é um Object3D com userData.componentId,
 * userData.nome, userData.explode ([x,y,z] em unidades do modelo) e
 * userData.casca (true = fica translúcido no raio-X para revelar internos).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const COR_SEV = { high: 0xDC2626, medium: 0xD97706, low: 0x2563EB, op: 0x0284C7 };
const COR_SELECAO = 0x0EA5E9;
const TAMANHO_ALVO = 5;          // o modelo é normalizado para caber em ~5 unidades

export class Viewer3D {
  /**
   * @param {HTMLElement} container elemento com tamanho definido (position: relative)
   * @param {{onSelect?: Function, onPick?: Function, onRaioX?: Function}} opcoes
   */
  constructor(container, opcoes = {}) {
    this.container = container;
    this.onSelect = opcoes.onSelect || null;
    this.onPick = opcoes.onPick || null;
    this.onRaioX = opcoes.onRaioX || null;   // avisa a UI quando o raio-X liga sozinho
    this.componentes = new Map();   // id → { obj, nome, basePos, explode, casca, meshes }
    this.destaques = new Map();     // id → { sev, label }
    this.selecionado = null;
    this.modoMarcar = false;
    this.pino = null;
    this.explosao = 0;
    this.raioXAtivo = false;
    this._voo = null;
    this._relogio = new THREE.Timer();

    this._criarCena();
    this._criarInteracao();
    this._loop = this._loop.bind(this);
    this._raf = requestAnimationFrame(this._loop);
  }

  // ── Cena ────────────────────────────────────────────────────────────────
  _criarCena() {
    const w = this.container.clientWidth || 800;
    const h = this.container.clientHeight || 500;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.domElement.className = 'v3d-canvas';
    this.container.appendChild(renderer.domElement);
    this.renderer = renderer;

    const labels = new CSS2DRenderer();
    labels.setSize(w, h);
    labels.domElement.className = 'v3d-labels';
    this.container.appendChild(labels.domElement);
    this.labelRenderer = labels;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xEEF2F6);
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene = scene;

    const camera = new THREE.PerspectiveCamera(40, w / h, 0.05, 200);
    camera.position.set(7, 5, 8);
    this.camera = camera;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.minDistance = 1.2;
    controls.maxDistance = 30;
    this.controls = controls;

    const sol = new THREE.DirectionalLight(0xffffff, 2.2);
    sol.position.set(6, 10, 7);
    sol.castShadow = true;
    sol.shadow.mapSize.set(2048, 2048);
    const sc = sol.shadow.camera;
    sc.left = -8; sc.right = 8; sc.top = 8; sc.bottom = -8; sc.near = 1; sc.far = 40;
    sol.shadow.bias = -0.0005;
    scene.add(sol);
    scene.add(new THREE.HemisphereLight(0xffffff, 0xb8c2cc, 0.6));

    // Piso: grade discreta + receptor de sombra
    const grade = new THREE.GridHelper(40, 40, 0xc5ced8, 0xdde3ea);
    grade.material.transparent = true;
    grade.material.opacity = 0.7;
    scene.add(grade);
    const piso = new THREE.Mesh(new THREE.PlaneGeometry(40, 40),
      new THREE.ShadowMaterial({ opacity: 0.18 }));
    piso.rotation.x = -Math.PI / 2;
    piso.position.y = 0.001;
    piso.receiveShadow = true;
    scene.add(piso);

    // Tooltip de hover
    const tip = document.createElement('div');
    tip.className = 'v3d-tip';
    tip.hidden = true;
    this.container.appendChild(tip);
    this.tip = tip;

    this._ro = new ResizeObserver(() => this._redimensionar());
    this._ro.observe(this.container);
  }

  _redimensionar() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    if (!w || !h) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.labelRenderer.setSize(w, h);
  }

  // ── Carregamento ────────────────────────────────────────────────────────
  /**
   * @param {{fonte:'familia'|'glb', familia?:string, arquivo?:string,
   *          mapa?:Object, componentes?:Array, internos?:string}} modelo
   * @param {Array<{component_id,name}>} catalogo componentes da máquina (nomes exibidos)
   */
  async carregar(modelo, catalogo = []) {
    if (this.raiz) {
      this.limparDestaques();
      this.limparPonto();
      this.selecionado = null;
      this.scene.remove(this.raiz);
      this.componentes.clear();
    }
    const nomes = Object.fromEntries(catalogo.map(c => [c.component_id, c.name]));
    let raiz;

    if (modelo.fonte === 'familia') {
      const mod = await import(`./familias/${modelo.familia}.js`);
      raiz = mod.construir(THREE);
    } else if (modelo.fonte === 'glb') {
      raiz = await this._carregarGLB(modelo);
      if (modelo.internos) {
        // Peças internas acrescentadas em código (o CAD de fabricante é só a casca)
        const mod = await import(`./internos/${modelo.internos}.js`);
        mod.acrescentar(THREE, raiz);
      }
    } else {
      throw new Error('Modelo 3D sem fonte conhecida.');
    }

    this._normalizar(raiz);
    this.scene.add(raiz);
    this.raiz = raiz;

    raiz.traverse(o => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        // Material próprio por malha: o destaque de um componente não vaza para outro
        o.material = o.material.clone();
        o.userData._mat = {
          emissive: o.material.emissive ? o.material.emissive.getHex() : 0,
          emissiveIntensity: o.material.emissiveIntensity ?? 1,
          opacity: o.material.opacity, transparent: o.material.transparent,
        };
      }
      const id = o.userData.componentId;
      if (id && !this.componentes.has(id)) {
        const meshes = [];
        o.traverse(m => { if (m.isMesh) meshes.push(m); });
        this.componentes.set(id, {
          obj: o,
          nome: nomes[id] || o.userData.nome || id,
          basePos: o.position.clone(),
          explode: new THREE.Vector3(...(o.userData.explode || [0, 0, 0])),
          casca: !!o.userData.casca,
          interno: !!o.userData.interno,
          meshes,
        });
      }
    });

    this.enquadrar(false);
    return [...this.componentes.keys()];
  }

  async _carregarGLB(modelo) {
    const loader = new GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(modelo.arquivo);
    const raiz = new THREE.Group();
    raiz.add(gltf.scene);
    gltf.scene.updateMatrixWorld(true);

    // mapa: { componentId: { nos: ["Part_17", ...], nome, explode, casca } }
    for (const [id, def] of Object.entries(modelo.mapa || {})) {
      const grupo = new THREE.Group();
      grupo.userData = { componentId: id, nome: def.nome, explode: def.explode, casca: def.casca };
      raiz.add(grupo);
      for (const nomeNo of def.nos || []) {
        const no = gltf.scene.getObjectByName(nomeNo);
        if (no) grupo.attach(no);   // attach preserva a posição no mundo
        else console.warn(`[3D] nó "${nomeNo}" não encontrado no GLB (${id})`);
      }
    }
    return raiz;
  }

  _normalizar(raiz) {
    const caixa = new THREE.Box3().setFromObject(raiz);
    const tam = caixa.getSize(new THREE.Vector3());
    const escala = TAMANHO_ALVO / Math.max(tam.x, tam.y, tam.z);
    raiz.scale.setScalar(escala);
    const c = new THREE.Box3().setFromObject(raiz);
    const centro = c.getCenter(new THREE.Vector3());
    raiz.position.x -= centro.x;
    raiz.position.z -= centro.z;
    raiz.position.y -= c.min.y;
    this.escala = escala;
  }

  // ── Câmera ──────────────────────────────────────────────────────────────
  enquadrar(animar = true) {
    if (!this.raiz) return;
    const caixa = new THREE.Box3().setFromObject(this.raiz);
    const centro = caixa.getCenter(new THREE.Vector3());
    const raio = caixa.getSize(new THREE.Vector3()).length() / 2;
    // Ajusta pela menor abertura (vertical ou horizontal) para ocupar bem o palco
    const fovV = THREE.MathUtils.degToRad(this.camera.fov / 2);
    const fovH = Math.atan(Math.tan(fovV) * this.camera.aspect);
    const dist = raio / Math.sin(Math.min(fovV, fovH)) * 0.78;
    const dir = new THREE.Vector3(0.75, 0.45, 1).normalize();
    this._voarPara(centro.clone().add(dir.multiplyScalar(dist)), centro, animar);
  }

  focar(id) {
    const c = this.componentes.get(id);
    if (!c) return;
    // Peça interna (ex.: vedação dentro do cilindro): liga o raio-X para ela aparecer
    if (c.interno && !this.raioXAtivo) {
      this.raioX(true);
      if (this.onRaioX) this.onRaioX(true);
    }
    const caixa = new THREE.Box3().setFromObject(c.obj);
    const centro = caixa.getCenter(new THREE.Vector3());
    const raio = Math.max(caixa.getSize(new THREE.Vector3()).length() / 2, 0.35);
    const dist = Math.max(raio * 3.5, 3.0);
    const dir = this.camera.position.clone().sub(this.controls.target).normalize();
    dir.y = Math.max(dir.y, 0.25);
    dir.normalize();
    this._voarPara(centro.clone().add(dir.multiplyScalar(dist)), centro, true);
  }

  _voarPara(pos, alvo, animar) {
    if (!animar) {
      this.camera.position.copy(pos);
      this.controls.target.copy(alvo);
      this.controls.update();
      return;
    }
    this._voo = {
      t: 0, dur: 0.9,
      p0: this.camera.position.clone(), p1: pos,
      a0: this.controls.target.clone(), a1: alvo,
    };
  }

  // ── Destaques (diagnóstico) ─────────────────────────────────────────────
  /**
   * @param {Array<{id, severidade:'high'|'medium'|'low'|'op', numero?:number|string, texto?:string}>} lista
   *   severidade 'op' = peça indicada pelo operador (etiqueta com ícone de toque)
   */
  destacar(lista) {
    this.limparDestaques();
    lista.forEach((d, i) => {
      const c = this.componentes.get(d.id);
      if (!c) return;
      const cor = COR_SEV[d.severidade] ?? COR_SEV.medium;
      c.meshes.forEach(m => {
        if (m.material.emissive) {
          m.material.emissive.setHex(cor);
          m.material.emissiveIntensity = 0.55;
        }
      });
      const label = this._criarEtiqueta(c, d.numero ?? i + 1, d.severidade, d.texto);
      this.destaques.set(d.id, { cor, label });
    });
  }

  limparDestaques() {
    for (const [id, d] of this.destaques) {
      const c = this.componentes.get(id);
      if (c) c.meshes.forEach(m => this._restaurarMaterial(m));
      d.label.removeFromParent();
    }
    this.destaques.clear();
    if (this.selecionado) this._aplicarSelecao(this.selecionado);
  }

  _criarEtiqueta(c, numero, sev, texto) {
    const el = document.createElement('div');
    el.className = `v3d-tag v3d-sev-${sev || 'medium'}`;
    const n = document.createElement('b');
    if (sev === 'op') {
      const ic = document.createElement('i');
      ic.className = 'fas fa-hand-pointer';
      n.appendChild(ic);
    } else {
      n.textContent = numero;
    }
    const t = document.createElement('span');
    t.textContent = texto || c.nome;
    el.append(n, t);
    // O CSS2DRenderer controla o transform do elemento raiz; o deslocamento
    // anti-sobreposição vai no elemento interno.
    const wrap = document.createElement('div');
    wrap.className = 'v3d-tag-wrap';
    wrap.appendChild(el);
    const label = new CSS2DObject(wrap);
    // Etiqueta presa ao componente: acompanha a vista explodida
    const caixa = new THREE.Box3().setFromObject(c.obj);
    const topo = new THREE.Vector3((caixa.min.x + caixa.max.x) / 2, caixa.max.y, (caixa.min.z + caixa.max.z) / 2);
    c.obj.worldToLocal(topo);
    label.position.copy(topo);
    c.obj.add(label);
    return label;
  }

  _restaurarMaterial(m) {
    const o = m.userData._mat;
    if (!o) return;
    if (m.material.emissive) {
      m.material.emissive.setHex(o.emissive);
      m.material.emissiveIntensity = o.emissiveIntensity;
    }
  }

  // ── Seleção ─────────────────────────────────────────────────────────────
  selecionar(id) {
    if (this.selecionado && this.selecionado !== id) {
      const ant = this.componentes.get(this.selecionado);
      if (ant && !this.destaques.has(this.selecionado)) ant.meshes.forEach(m => this._restaurarMaterial(m));
    }
    this.selecionado = id;
    if (id) this._aplicarSelecao(id);
  }

  _aplicarSelecao(id) {
    const c = this.componentes.get(id);
    if (!c || this.destaques.has(id)) return;
    c.meshes.forEach(m => {
      if (m.material.emissive) {
        m.material.emissive.setHex(COR_SELECAO);
        m.material.emissiveIntensity = 0.45;
      }
    });
  }

  nomeDe(id) { return this.componentes.get(id)?.nome || id; }

  // ── Raio-X e vista explodida ────────────────────────────────────────────
  raioX(ativo) {
    this.raioXAtivo = ativo;
    for (const c of this.componentes.values()) {
      if (!c.casca) continue;
      c.meshes.forEach(m => {
        const o = m.userData._mat;
        m.material.transparent = ativo ? true : o.transparent;
        m.material.opacity = ativo ? 0.14 : o.opacity;
        m.material.depthWrite = !ativo;
        m.castShadow = !ativo;
        m.material.needsUpdate = true;
      });
    }
  }

  explodir(t) {
    this.explosao = t;
    for (const c of this.componentes.values()) {
      c.obj.position.copy(c.basePos).addScaledVector(c.explode, t / (c.obj.parent?.scale.x || 1));
    }
  }

  // ── Marcação de ponto (operador toca onde viu o problema) ───────────────
  ativarMarcacao(ativo) {
    this.modoMarcar = ativo;
    this.renderer.domElement.style.cursor = ativo ? 'crosshair' : '';
  }

  marcarPonto(ponto, id) {
    if (!this.pino) {
      const g = new THREE.Group();
      const haste = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.35, 8),
        new THREE.MeshStandardMaterial({ color: 0x0F172A }));
      haste.position.y = 0.175;
      const cabeca = new THREE.Mesh(new THREE.SphereGeometry(0.07, 20, 14),
        new THREE.MeshStandardMaterial({ color: 0xDC2626, emissive: 0xDC2626, emissiveIntensity: 0.4 }));
      cabeca.position.y = 0.38;
      g.add(haste, cabeca);
      this.scene.add(g);
      this.pino = g;
    }
    this.pino.position.copy(ponto);
    this.pino.visible = true;
    this.pinoComponente = id;
  }

  limparPonto() {
    if (this.pino) this.pino.visible = false;
    this.pinoComponente = null;
  }

  // ── Interação ───────────────────────────────────────────────────────────
  _criarInteracao() {
    const el = this.renderer.domElement;
    const ray = new THREE.Raycaster();
    const ndc = new THREE.Vector2();
    let inicio = null;

    const acertar = (ev) => {
      const r = el.getBoundingClientRect();
      ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(ndc, this.camera);
      if (!this.raiz) return null;
      const hits = ray.intersectObject(this.raiz, true)
        .filter(h => h.object.visible && !(this.raioXAtivo && this._ehCasca(h.object)));
      for (const h of hits) {
        let o = h.object;
        while (o && !o.userData.componentId) o = o.parent;
        if (o) return { id: o.userData.componentId, ponto: h.point };
      }
      return null;
    };

    el.addEventListener('pointermove', ev => {
      if (ev.pointerType !== 'mouse') return;
      const h = acertar(ev);
      if (h) {
        this.tip.textContent = this.nomeDe(h.id);
        const r = this.container.getBoundingClientRect();
        this.tip.style.left = (ev.clientX - r.left + 14) + 'px';
        this.tip.style.top = (ev.clientY - r.top + 14) + 'px';
        this.tip.hidden = false;
        el.style.cursor = this.modoMarcar ? 'crosshair' : 'pointer';
      } else {
        this.tip.hidden = true;
        el.style.cursor = this.modoMarcar ? 'crosshair' : '';
      }
    });
    el.addEventListener('pointerleave', () => { this.tip.hidden = true; });
    // Clique = pressionar e soltar sem arrastar (arrastar gira a câmera)
    el.addEventListener('pointerdown', ev => { inicio = { x: ev.clientX, y: ev.clientY }; });
    el.addEventListener('pointerup', ev => {
      if (!inicio || Math.hypot(ev.clientX - inicio.x, ev.clientY - inicio.y) > 6) return;
      const h = acertar(ev);
      if (this.modoMarcar) {
        if (h) {
          this.marcarPonto(h.ponto, h.id);
          this.selecionar(h.id);
          if (this.onPick) this.onPick(h.id, this.nomeDe(h.id));
        }
        return;
      }
      this.selecionar(h ? h.id : null);
      if (this.onSelect) this.onSelect(h ? h.id : null, h ? this.nomeDe(h.id) : null);
    });
  }

  _ehCasca(obj) {
    let o = obj;
    while (o && !o.userData.componentId) o = o.parent;
    return !!(o && o.userData.casca);
  }

  // ── Loop ────────────────────────────────────────────────────────────────
  _loop() {
    this._raf = requestAnimationFrame(this._loop);
    this._relogio.update();
    const dt = this._relogio.getDelta();
    const t = this._relogio.getElapsed();

    if (this._voo) {
      const v = this._voo;
      v.t = Math.min(1, v.t + dt / v.dur);
      const e = v.t < 0.5 ? 4 * v.t ** 3 : 1 - (-2 * v.t + 2) ** 3 / 2;  // ease-in-out
      this.camera.position.lerpVectors(v.p0, v.p1, e);
      this.controls.target.lerpVectors(v.a0, v.a1, e);
      if (v.t >= 1) this._voo = null;
    }

    // Pulso suave nos componentes destacados
    const pulso = 0.4 + 0.25 * (Math.sin(t * 3) + 1) / 2;
    for (const id of this.destaques.keys()) {
      const c = this.componentes.get(id);
      if (c) c.meshes.forEach(m => { if (m.material.emissive) m.material.emissiveIntensity = pulso; });
    }

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.labelRenderer.render(this.scene, this.camera);
    this._afastarEtiquetas();
  }

  /** Empurra para cima as etiquetas que se sobrepõem e mantém todas dentro da área visível. */
  _afastarEtiquetas() {
    if (!this.destaques.size) return;
    const area = this.container.getBoundingClientRect();
    const tags = [...this.destaques.values()].map(d => d.label.element.firstChild);
    tags.forEach(t => { t.style.transform = 'translateX(-50%)'; });
    const caixas = tags.map(t => ({ t, r: t.getBoundingClientRect() }))
      .filter(c => c.r.width > 0)
      .sort((a, b) => b.r.top - a.r.top);          // de baixo para cima
    const colocadas = [];
    for (const c of caixas) {
      // Horizontal: não deixa a etiqueta sair pela lateral do visualizador
      let dx = 0;
      if (c.r.right > area.right - 8) dx = area.right - 8 - c.r.right;
      if (c.r.left + dx < area.left + 8) dx = area.left + 8 - c.r.left;
      let left = c.r.left + dx, right = c.r.right + dx;
      let top = c.r.top, bottom = c.r.bottom, dy = 0;
      for (const o of colocadas) {
        if (left < o.right && right > o.left && top < o.bottom && bottom > o.top) {
          const d = bottom - o.top + 4;
          dy += d; top -= d; bottom -= d;
        }
      }
      if (dx || dy) c.t.style.transform = `translate(calc(-50% + ${dx}px), ${-dy}px)`;
      colocadas.push({ left, right, top, bottom });
    }
  }

  dispose() {
    cancelAnimationFrame(this._raf);
    this._ro.disconnect();
    this.renderer.dispose();
    this.container.innerHTML = '';
  }
}
