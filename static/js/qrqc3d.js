/**
 * qrqc3d.js — Three.js + painel de diagnóstico Nexar IA
 *
 * Dependências (carregadas no template via CDN):
 *   three.min.js r128
 *   OrbitControls.js r128
 *   GLTFLoader.js r128  (para modelos .glb reais no futuro)
 */

/* ── Estado global ────────────────────────────────────────────── */
const State = {
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  raycaster: null,
  mouse: null,
  meshMap: {},          // component_id → THREE.Mesh
  originalMaterials: {},// component_id → material original
  diagnosis: null,      // último diagnóstico recebido
  selectedId: null,     // component_id selecionado
};

/* ── Inicialização Three.js ───────────────────────────────────── */
function initThree(canvasEl) {
  const W = canvasEl.clientWidth;
  const H = canvasEl.clientHeight;

  // Renderer
  const renderer = new THREE.WebGLRenderer({ canvas: canvasEl, antialias: true, alpha: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  State.renderer = renderer;

  // Scene
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a1628);
  scene.fog = new THREE.FogExp2(0x0a1628, 0.04);
  State.scene = scene;

  // Camera
  const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
  camera.position.set(5, 4, 6);
  State.camera = camera;

  // Orbit controls
  const controls = new THREE.OrbitControls(camera, canvasEl);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 2;
  controls.maxDistance = 20;
  controls.maxPolarAngle = Math.PI * 0.85;
  State.controls = controls;

  // Iluminação
  const ambient = new THREE.AmbientLight(0xffffff, 0.35);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
  keyLight.position.set(6, 8, 5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.near = 0.1;
  keyLight.shadow.camera.far = 50;
  keyLight.shadow.camera.left = -8;
  keyLight.shadow.camera.right = 8;
  keyLight.shadow.camera.top = 8;
  keyLight.shadow.camera.bottom = -8;
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight(0x4fc3f7, 0.5);
  fillLight.position.set(-5, 3, -4);
  scene.add(fillLight);

  const rimLight = new THREE.PointLight(0x0ea5e9, 0.8, 15);
  rimLight.position.set(-3, 5, -3);
  scene.add(rimLight);

  // Grid decorativo
  const grid = new THREE.GridHelper(20, 20, 0x1e3a5f, 0x0d2137);
  grid.position.y = -1.6;
  scene.add(grid);

  // Raycaster para seleção por clique
  State.raycaster = new THREE.Raycaster();
  State.mouse = new THREE.Vector2();

  // Resize handler
  window.addEventListener('resize', () => {
    const w = canvasEl.clientWidth;
    const h = canvasEl.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  // Loop de animação
  let hue = 0;
  function animate() {
    requestAnimationFrame(animate);
    controls.update();

    // Pulsação nos componentes destacados
    hue += 0.015;
    Object.keys(State.meshMap).forEach(cid => {
      const mesh = State.meshMap[cid];
      if (mesh.__highlighted) {
        const t = (Math.sin(hue * 2 + mesh.__phaseOffset) + 1) / 2;
        if (mesh.material && mesh.material.emissive) {
          mesh.material.emissiveIntensity = 0.25 + t * 0.45;
        }
      }
    });

    renderer.render(scene, camera);
  }
  animate();
}

/* ── Modelo demo procedural ──────────────────────────────────── */
function buildDemoMachine(components) {
  /**
   * Constrói uma máquina industrial genérica com Three.js puro.
   * Os nomes dos meshes correspondem aos component_ids do banco.
   * Se não há componentes cadastrados usa nomes padrão.
   */
  const group = new THREE.Group();

  // Materiais base
  const matFrame   = new THREE.MeshStandardMaterial({ color: 0x2d3748, roughness: 0.7, metalness: 0.5 });
  const matBase    = new THREE.MeshStandardMaterial({ color: 0x1a202c, roughness: 0.8, metalness: 0.3 });
  const matMotor   = new THREE.MeshStandardMaterial({ color: 0x0ea5e9, roughness: 0.4, metalness: 0.7 });
  const matBearing = new THREE.MeshStandardMaterial({ color: 0xc0a060, roughness: 0.3, metalness: 0.9 });
  const matShaft   = new THREE.MeshStandardMaterial({ color: 0x718096, roughness: 0.3, metalness: 0.95 });
  const matPanel   = new THREE.MeshStandardMaterial({ color: 0x0a1628, roughness: 0.6, metalness: 0.2 });
  const matCoupl   = new THREE.MeshStandardMaterial({ color: 0x4a5568, roughness: 0.5, metalness: 0.6 });
  const matBelt    = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9, metalness: 0.0 });

  // Mapeamento de nome → {geometry, material, position, rotation, scale}
  const parts = [
    {
      id: 'base_frame',     name: 'base_frame',
      geo: new THREE.BoxGeometry(4.4, 0.25, 2.2),
      mat: matBase, pos: [0, -1.5, 0],
    },
    {
      id: 'estrutura',      name: 'estrutura',
      geo: new THREE.BoxGeometry(4.0, 0.5, 2.0),
      mat: matFrame, pos: [0, -1.2, 0],
    },
    {
      id: 'cabeçote',       name: 'cabeçote',
      geo: new THREE.BoxGeometry(0.9, 1.2, 1.1),
      mat: matFrame, pos: [-1.6, -0.45, 0],
    },
    {
      id: 'motor_principal',name: 'motor_principal',
      geo: new THREE.CylinderGeometry(0.38, 0.38, 0.9, 16),
      mat: matMotor, pos: [-1.6, -0.3, 0], rot: [0, 0, Math.PI/2],
    },
    {
      id: 'rolamento_b12',  name: 'rolamento_b12',
      geo: new THREE.TorusGeometry(0.28, 0.07, 12, 24),
      mat: matBearing, pos: [-0.95, -0.3, 0], rot: [0, 0, Math.PI/2],
    },
    {
      id: 'eixo_principal', name: 'eixo_principal',
      geo: new THREE.CylinderGeometry(0.1, 0.1, 3.0, 12),
      mat: matShaft, pos: [0, -0.3, 0], rot: [0, 0, Math.PI/2],
    },
    {
      id: 'acoplamento',    name: 'acoplamento',
      geo: new THREE.CylinderGeometry(0.22, 0.22, 0.22, 8),
      mat: matCoupl, pos: [0.4, -0.3, 0], rot: [0, 0, Math.PI/2],
    },
    {
      id: 'correia',        name: 'correia',
      geo: new THREE.TorusGeometry(0.55, 0.06, 6, 30),
      mat: matBelt, pos: [-1.6, 0.5, 0], rot: [0, 0, Math.PI/2],
    },
    {
      id: 'painel_controle',name: 'painel_controle',
      geo: new THREE.BoxGeometry(0.7, 0.9, 0.08),
      mat: matPanel, pos: [1.6, -0.5, 0.98],
    },
    {
      id: 'redutor',        name: 'redutor',
      geo: new THREE.BoxGeometry(0.55, 0.55, 0.55),
      mat: matCoupl, pos: [-1.6, 0.45, 0],
    },
  ];

  // Se há componentes cadastrados no banco, remapeia os IDs
  const compMap = {};
  if (components && components.length > 0) {
    components.forEach((c, i) => {
      if (i < parts.length) {
        compMap[parts[i].id] = c.component_id;
      }
    });
  }

  parts.forEach(p => {
    const mesh = new THREE.Mesh(p.geo, p.mat.clone());
    if (p.pos) mesh.position.set(...p.pos);
    if (p.rot) mesh.rotation.set(...p.rot);
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    // component_id real (do banco se existir, senão o padrão)
    const realId = compMap[p.id] || p.id;
    mesh.name = realId;
    mesh.userData.component_id = realId;
    mesh.userData.display_name = p.name;
    mesh.__highlighted = false;
    mesh.__phaseOffset = Math.random() * Math.PI * 2;

    State.meshMap[realId] = mesh;
    State.originalMaterials[realId] = mesh.material.clone();
    group.add(mesh);
  });

  // Placa de base com sombra
  const shadowMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(5, 3),
    new THREE.ShadowMaterial({ opacity: 0.3 })
  );
  shadowMesh.rotation.x = -Math.PI / 2;
  shadowMesh.position.y = -1.62;
  shadowMesh.receiveShadow = true;
  group.add(shadowMesh);

  State.scene.add(group);
}

/* ── Highlighting ────────────────────────────────────────────── */
function highlightComponent(componentId, severity) {
  const mesh = State.meshMap[componentId];
  if (!mesh) return;

  const colors = { high: 0xef4444, medium: 0xf59e0b, low: 0x10b981 };
  const color = colors[severity] || colors.medium;

  mesh.material.color.setHex(color);
  mesh.material.emissive.setHex(color);
  mesh.material.emissiveIntensity = 0.3;
  mesh.__highlighted = true;
}

function clearHighlights() {
  Object.keys(State.meshMap).forEach(cid => {
    const mesh = State.meshMap[cid];
    const orig = State.originalMaterials[cid];
    if (mesh && orig) {
      mesh.material.color.copy(orig.color);
      mesh.material.emissive.setHex(0x000000);
      mesh.material.emissiveIntensity = 0;
      mesh.__highlighted = false;
    }
  });
}

function applyDiagnosis(diag) {
  clearHighlights();
  const components = diag.components || [];
  components.forEach(c => {
    highlightComponent(c.component_id, c.severity);
  });
}

/* ── Seleção por clique ──────────────────────────────────────── */
function setupClickSelection(canvasEl) {
  canvasEl.addEventListener('click', e => {
    const rect = canvasEl.getBoundingClientRect();
    State.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    State.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    State.raycaster.setFromCamera(State.mouse, State.camera);
    const allMeshes = Object.values(State.meshMap);
    const hits = State.raycaster.intersectObjects(allMeshes, true);

    if (hits.length > 0) {
      let obj = hits[0].object;
      while (obj && !obj.userData.component_id) obj = obj.parent;
      if (obj && obj.userData.component_id) {
        selectComponent(obj.userData.component_id);
      }
    } else {
      deselectComponent();
    }
  });

  // Tooltip no hover
  const tooltip = document.getElementById('component-tooltip');
  if (tooltip) {
    canvasEl.addEventListener('mousemove', e => {
      const rect = canvasEl.getBoundingClientRect();
      State.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      State.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      State.raycaster.setFromCamera(State.mouse, State.camera);
      const allMeshes = Object.values(State.meshMap);
      const hits = State.raycaster.intersectObjects(allMeshes, true);

      if (hits.length > 0) {
        let obj = hits[0].object;
        while (obj && !obj.userData.component_id) obj = obj.parent;
        if (obj) {
          const cid = obj.userData.component_id;
          const compInfo = getDiagComp(cid);
          tooltip.style.display = 'block';
          tooltip.style.left = (e.clientX - rect.left + 14) + 'px';
          tooltip.style.top = (e.clientY - rect.top - 10) + 'px';
          tooltip.querySelector('.ct-name').textContent = compInfo
            ? compInfo.component_name : cid;
          tooltip.querySelector('.ct-prob').textContent = compInfo
            ? `${Math.round(compInfo.probability * 100)}% probabilidade` : '';
          canvasEl.style.cursor = 'pointer';
        }
      } else {
        tooltip.style.display = 'none';
        canvasEl.style.cursor = 'grab';
      }
    });
    canvasEl.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  }
}

function getDiagComp(cid) {
  if (!State.diagnosis || !State.diagnosis.components) return null;
  return State.diagnosis.components.find(c => c.component_id === cid) || null;
}

function selectComponent(cid) {
  State.selectedId = cid;

  // Destaca item na lista de hipóteses
  document.querySelectorAll('.hypothesis-item').forEach(el => {
    el.classList.toggle('active', el.dataset.cid === cid);
  });

  // Painel de componente selecionado
  const panel = document.getElementById('selected-comp-panel');
  if (!panel) return;
  const compInfo = getDiagComp(cid);
  if (compInfo) {
    panel.querySelector('.scp-name').textContent = compInfo.component_name;
    panel.querySelector('.scp-id').textContent = `ID: ${cid}`;
    panel.querySelector('.scp-reason').textContent = compInfo.reason;
    panel.querySelector('.scp-prob').textContent =
      `${Math.round(compInfo.probability * 100)}% probabilidade`;
    panel.querySelector('.scp-sev').className =
      `severity-badge severity-${compInfo.severity} scp-sev`;
    panel.querySelector('.scp-sev').textContent =
      { high: 'Alta', medium: 'Média', low: 'Baixa' }[compInfo.severity] || compInfo.severity;
    panel.classList.add('visible');
  } else {
    panel.querySelector('.scp-name').textContent = cid;
    panel.querySelector('.scp-id').textContent = '';
    panel.querySelector('.scp-reason').textContent = 'Componente sem diagnóstico associado.';
    panel.querySelector('.scp-prob').textContent = '';
    panel.classList.add('visible');
  }
}

function deselectComponent() {
  State.selectedId = null;
  document.querySelectorAll('.hypothesis-item').forEach(el => el.classList.remove('active'));
  const panel = document.getElementById('selected-comp-panel');
  if (panel) panel.classList.remove('visible');
}

/* ── Painel de hipóteses ─────────────────────────────────────── */
/* Escapa texto vindo da IA/banco antes de inserir via innerHTML (evita XSS) */
function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function sevClass(v) {
  return ['high', 'medium', 'low'].includes(v) ? v : 'low';
}

/* Clique numa hipótese (lista renderizada no servidor ou via JS) */
document.addEventListener('click', e => {
  const item = e.target.closest('.hypothesis-item[data-cid]');
  if (!item) return;
  selectComponent(item.dataset.cid);
  focusComponent(item.dataset.cid);
});

function renderHypotheses(components) {
  const container = document.getElementById('hypothesis-list');
  if (!container) return;

  if (!components || components.length === 0) {
    container.innerHTML = '<p style="font-size:13px;color:var(--text-muted)">Nenhum componente identificado.</p>';
    return;
  }

  container.innerHTML = components
    .sort((a, b) => b.probability - a.probability)
    .map(c => `
      <div class="hypothesis-item" data-cid="${esc(c.component_id)}">
        <div class="hyp-header">
          <span class="hyp-dot ${sevClass(c.severity)}"></span>
          <span class="hyp-name">${esc(c.component_name)}</span>
          <span class="hyp-prob">${Math.round((Number(c.probability) || 0) * 100)}%</span>
        </div>
        <div class="hyp-reason">${esc(c.reason)}</div>
      </div>
    `).join('');
}

function renderActions(actions) {
  const container = document.getElementById('action-list');
  if (!container || !actions) return;
  container.innerHTML = actions.map((a, i) => `
    <div class="action-item">
      <span class="action-num">${i + 1}</span>
      <span>${esc(a)}</span>
    </div>
  `).join('');
}

function focusComponent(cid) {
  const mesh = State.meshMap[cid];
  if (!mesh) return;
  const pos = new THREE.Vector3();
  mesh.getWorldPosition(pos);
  State.controls.target.lerp(pos, 0.6);
  State.controls.update();
}

/* ── Modo investigação ───────────────────────────────────────── */
const STEP_LABELS = {
  get_machine_info: 'Identificando máquina',
  get_machine_components: 'Consultando componentes 3D',
  get_machine_history: 'Analisando histórico',
  get_similar_occurrences: 'Buscando falhas semelhantes',
  get_previous_solutions: 'Consultando soluções anteriores',
  get_machine_documentation: 'Revisando documentação técnica',
};

function showInvestigation(steps) {
  const overlay = document.getElementById('investigation-overlay');
  if (!overlay) return;

  const stepEls = steps.map((s, i) => `
    <div class="inv-step" id="inv-step-${i}">
      <span class="inv-step-icon"><i class="fas fa-circle" style="font-size:8px;color:var(--primary)"></i></span>
      ${esc(STEP_LABELS[s] || s)}
    </div>
  `).join('');

  overlay.querySelector('.inv-steps').innerHTML =
    `<div class="inv-step active"><span class="inv-step-icon"><i class="fas fa-spinner spin"></i></span>Analisando ocorrência...</div>` +
    stepEls;
  overlay.style.display = 'flex';

  // Anima os steps um a um
  let delay = 400;
  steps.forEach((_, i) => {
    setTimeout(() => {
      const el = document.getElementById(`inv-step-${i}`);
      if (el) {
        el.classList.add('done');
        el.querySelector('.inv-step-icon').innerHTML = '<i class="fas fa-check-circle" style="color:var(--success)"></i>';
      }
    }, delay += 350);
  });
}

function hideInvestigation() {
  const overlay = document.getElementById('investigation-overlay');
  if (overlay) overlay.style.display = 'none';
}

/* ── Inicializar loading overlay durante análise ─────────────── */
function showAnalysisLoading() {
  const overlay = document.getElementById('investigation-overlay');
  if (!overlay) return;
  overlay.querySelector('.inv-steps').innerHTML =
    `<div class="inv-step active"><span class="inv-step-icon"><i class="fas fa-spinner spin"></i></span>Conectando à Nexar IA...</div>`;
  overlay.style.display = 'flex';
}

/* ── API calls ───────────────────────────────────────────────── */
async function startAnalysis(ocorrenciaId) {
  const btn = document.getElementById('btn-analyze');
  const summaryBox = document.getElementById('summary-box');

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner spin"></i> Analisando...';
  showAnalysisLoading();

  try {
    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    const res = await fetch(`/api/ai/analisar/${ocorrenciaId}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/json' },
    });
    const data = await res.json();

    if (data.error) {
      hideInvestigation();
      showError(data.error);
      btn.innerHTML = '<i class="fas fa-robot"></i> Analisar com Nexar IA';
      btn.disabled = false;
      return;
    }

    State.diagnosis = data;

    // Mostra steps reais
    if (data._steps && data._steps.length > 0) {
      showInvestigation(data._steps);
      await sleep(data._steps.length * 350 + 600);
    }
    hideInvestigation();

    // Aplica destaques
    applyDiagnosis(data);

    // Atualiza painel
    if (summaryBox) summaryBox.textContent = data.summary || '';
    renderHypotheses(data.components);
    renderActions(data.recommended_actions);

    // Severity geral
    const sevEl = document.getElementById('overall-severity');
    if (sevEl && data.severity) {
      sevEl.className = `severity-badge severity-${data.severity}`;
      sevEl.textContent = { high: 'Alta', medium: 'Média', low: 'Baixa' }[data.severity] || data.severity;
    }

    // Pattern analysis
    const patternEl = document.getElementById('pattern-analysis');
    if (patternEl && data.pattern_analysis) {
      patternEl.textContent = data.pattern_analysis;
      patternEl.parentElement.style.display = 'block';
    }

    // Aviso técnico
    document.getElementById('tech-warning-section').style.display = 'block';

    // Steps chips
    renderStepChips(data._steps || []);

    // Mostra seções que estavam escondidas
    document.getElementById('result-sections').style.display = 'block';
    document.getElementById('empty-state').style.display = 'none';

    btn.innerHTML = '<i class="fas fa-redo"></i> Reanalisar';

  } catch (err) {
    hideInvestigation();
    showError('Erro de comunicação: ' + err.message);
    btn.innerHTML = '<i class="fas fa-robot"></i> Analisar com Nexar IA';
    btn.disabled = false;
  }
}

function renderStepChips(steps) {
  const container = document.getElementById('steps-chips');
  if (!container) return;
  const unique = [...new Set(steps)];
  container.innerHTML = unique.map(s => `
    <div class="step-chip">
      <i class="fas fa-check-circle"></i>
      ${esc(STEP_LABELS[s] || s)}
    </div>
  `).join('');
  document.getElementById('steps-section').style.display = 'block';
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function showError(msg) {
  let box = document.getElementById('nexa-error-box');
  if (!box) {
    box = document.createElement('div');
    box.id = 'nexa-error-box';
    box.style.cssText = `
      position:fixed; bottom:24px; right:24px; z-index:9999;
      background:#1e1e2e; border:1px solid #ef4444;
      color:#fca5a5; border-radius:10px;
      padding:14px 18px; max-width:380px;
      font-family:var(--font,sans-serif); font-size:13px; line-height:1.5;
      box-shadow:0 8px 24px rgba(0,0,0,.4);
      display:flex; gap:12px; align-items:flex-start;
    `;
    document.body.appendChild(box);
  }
  box.innerHTML = `
    <i class="fas fa-exclamation-triangle" style="color:#ef4444;margin-top:2px;flex-shrink:0"></i>
    <span>${esc(msg)}</span>
  `;
  box.style.display = 'flex';
  clearTimeout(box._timer);
  box._timer = setTimeout(() => { box.style.display = 'none'; }, 8000);
}

/* ── Camera reset ────────────────────────────────────────────── */
function resetCamera() {
  State.camera.position.set(5, 4, 6);
  State.controls.target.set(0, 0, 0);
  State.controls.update();
}

/* ── Init ────────────────────────────────────────────────────── */
function initQRQC3D(config) {
  const canvas = document.getElementById('three-canvas');
  if (!canvas) return;

  initThree(canvas);
  buildDemoMachine(config.components || []);
  setupClickSelection(canvas);

  // Se já há diagnóstico, aplica
  if (config.diagnosis && config.diagnosis.components) {
    State.diagnosis = config.diagnosis;
    applyDiagnosis(config.diagnosis);
    renderHypotheses(config.diagnosis.components);
    renderActions(config.diagnosis.recommended_actions || []);
    renderStepChips(JSON.parse(config.diagnosis.steps_used || '[]'));
    document.getElementById('result-sections').style.display = 'block';
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('tech-warning-section').style.display = 'block';

    const sevEl = document.getElementById('overall-severity');
    if (sevEl && config.diagnosis.severity) {
      sevEl.className = `severity-badge severity-${config.diagnosis.severity}`;
      sevEl.textContent = { high: 'Alta', medium: 'Média', low: 'Baixa' }[config.diagnosis.severity];
    }
    const summaryBox = document.getElementById('summary-box');
    if (summaryBox) summaryBox.textContent = config.diagnosis.summary || '';

    const patternEl = document.getElementById('pattern-analysis');
    if (patternEl && config.diagnosis.pattern_analysis) {
      patternEl.textContent = config.diagnosis.pattern_analysis;
      patternEl.parentElement.style.display = 'block';
    }
  }
}
