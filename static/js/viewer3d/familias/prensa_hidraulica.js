/**
 * Família "prensa_hidraulica" — prensa hidráulica de 4 colunas (~40 t),
 * construída em código. Cada componente é um THREE.Group com
 * userData.componentId igual ao catálogo em modelos_3d.py.
 *
 * Unidades: metros. userData.explode = deslocamento na vista explodida
 * (unidades de cena). userData.casca = fica translúcido no raio-X;
 * userData.interno = peça escondida pela casca (o foco liga o raio-X).
 */
export function construir(THREE) {
  const raiz = new THREE.Group();
  raiz.name = 'prensa_hidraulica';

  // ── Materiais ────────────────────────────────────────────────────────────
  const std = (color, metalness, roughness, extra = {}) =>
    new THREE.MeshStandardMaterial({ color, metalness, roughness, ...extra });
  const M = {
    pintura:  std(0x33475B, 0.35, 0.55),   // estrutura (azul-grafite industrial)
    pinturaEscura: std(0x243344, 0.35, 0.6),
    usinado:  std(0xB9C0C8, 0.9, 0.32),
    cromo:    std(0xE6EAEE, 1.0, 0.12),
    amarelo:  std(0xD9A21B, 0.25, 0.5),    // martelo (parte móvel) em amarelo de segurança
    ferramenta: std(0x6F7882, 0.85, 0.38),
    bronze:   std(0xB08D57, 0.9, 0.35),
    borracha: std(0x1C2126, 0.0, 0.85),
    vedacao:  std(0xE0662B, 0.0, 0.6),     // poliuretano laranja (visível no raio-X)
    tanque:   std(0x4B5563, 0.4, 0.55),
    motor:    std(0x1E5AA8, 0.35, 0.45),
    cinza:    std(0x8C96A1, 0.6, 0.45),
    preto:    std(0x15191E, 0.3, 0.6),
    branco:   std(0xF4F6F8, 0.0, 0.4),
    vermelho: std(0xDC2626, 0.1, 0.45),
    verde:    std(0x16A34A, 0.1, 0.45),
    amareloSeg: std(0xFACC15, 0.1, 0.5),
    tela:     std(0x0F172A, 0.2, 0.25, { emissive: 0x1E3A5F, emissiveIntensity: 0.6 }),
    feixe:    new THREE.MeshBasicMaterial({ color: 0xEF4444, transparent: true, opacity: 0.22 }),
  };

  // ── Auxiliares ───────────────────────────────────────────────────────────
  const comp = (id, nome, opcoes = {}) => {
    const g = new THREE.Group();
    g.name = id;
    g.userData = { componentId: id, nome, explode: opcoes.explode || [0, 0, 0],
                   casca: !!opcoes.casca, interno: !!opcoes.interno };
    raiz.add(g);
    return g;
  };
  const caixa = (g, w, h, d, mat, x, y, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    g.add(m);
    return m;
  };
  const cil = (g, rTop, rBase, h, mat, x, y, z, seg = 40) => {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBase, h, seg), mat);
    m.position.set(x, y, z);
    g.add(m);
    return m;
  };
  const cilX = (g, r, comprimento, mat, x, y, z, seg = 32) => {
    const m = cil(g, r, r, comprimento, mat, x, y, z, seg);
    m.rotation.z = Math.PI / 2;
    return m;
  };
  const cilZ = (g, r, comprimento, mat, x, y, z, seg = 32) => {
    const m = cil(g, r, r, comprimento, mat, x, y, z, seg);
    m.rotation.x = Math.PI / 2;
    return m;
  };

  const COL_X = 0.85, COL_Z = 0.45;
  const colunasXZ = [[-COL_X, -COL_Z], [COL_X, -COL_Z], [-COL_X, COL_Z], [COL_X, COL_Z]];

  // ── Estrutura ────────────────────────────────────────────────────────────
  const base = comp('base', 'Base / mesa inferior', { explode: [0, -0.35, 0] });
  caixa(base, 2.2, 0.55, 1.4, M.pintura, 0, 0.275, 0);
  caixa(base, 2.3, 0.06, 1.5, M.pinturaEscura, 0, 0.03, 0);            // sapata
  caixa(base, 1.9, 0.12, 1.2, M.usinado, 0, 0.61, 0);                  // mesa (bolster)
  for (const z of [-0.3, 0, 0.3]) caixa(base, 1.8, 0.012, 0.03, M.preto, 0, 0.672, z); // rasgos em T

  const colunas = comp('colunas', 'Colunas guia');
  for (const [x, z] of colunasXZ) {
    cil(colunas, 0.085, 0.085, 2.55, M.cromo, x, 1.945, z);
    cil(colunas, 0.13, 0.13, 0.06, M.usinado, x, 0.70, z);               // colar inferior
  }

  const cab = comp('cabecote_superior', 'Cabeçote superior', { explode: [0, 0.75, 0], casca: true });
  caixa(cab, 2.2, 0.55, 1.4, M.pintura, 0, 3.495, 0);
  for (const [x, z] of colunasXZ) cil(cab, 0.14, 0.14, 0.14, M.usinado, x, 3.84, z, 6); // porcas
  caixa(cab, 0.06, 0.4, 1.3, M.pinturaEscura, -1.05, 3.495, 0);       // nervuras
  caixa(cab, 0.06, 0.4, 1.3, M.pinturaEscura, 1.05, 3.495, 0);

  // ── Cilindro principal (casca) + internos ────────────────────────────────
  const Y_CIL = 3.77;   // topo do cabeçote
  const cilindro = comp('cilindro_principal', 'Cilindro principal', { explode: [0, 1.35, 0], casca: true });
  cil(cilindro, 0.40, 0.40, 0.08, M.usinado, 0, Y_CIL + 0.04, 0);      // flange
  cil(cilindro, 0.32, 0.32, 1.0, M.pintura, 0, Y_CIL + 0.58, 0);       // camisa
  cil(cilindro, 0.36, 0.36, 0.1, M.usinado, 0, Y_CIL + 1.13, 0);       // tampa
  for (let i = 0; i < 8; i++) {                                        // tirantes
    const a = (i / 8) * Math.PI * 2;
    cil(cilindro, 0.02, 0.02, 1.05, M.usinado, Math.cos(a) * 0.36, Y_CIL + 0.6, Math.sin(a) * 0.36, 8);
  }
  cilZ(cilindro, 0.045, 0.12, M.usinado, 0.2, Y_CIL + 1.0, 0.3);        // pórtico superior
  cilZ(cilindro, 0.045, 0.12, M.usinado, 0.2, Y_CIL + 0.2, 0.3);        // pórtico inferior

  const pistao = comp('pistao', 'Pistão do cilindro', { explode: [0, 1.0, 1.3], interno: true });
  cil(pistao, 0.3, 0.3, 0.16, M.usinado, 0, Y_CIL + 0.62, 0);
  cil(pistao, 0.302, 0.302, 0.03, M.vedacao, 0, Y_CIL + 0.66, 0);      // anel do pistão

  const vedacao = comp('vedacao_cilindro', 'Vedação do cilindro principal', { explode: [0, 0.5, 1.5], interno: true });
  const toro = (r, tubo, y) => {
    const m = new THREE.Mesh(new THREE.TorusGeometry(r, tubo, 16, 48), M.vedacao);
    m.rotation.x = Math.PI / 2;
    m.position.set(0, y, 0);
    vedacao.add(m);
  };
  toro(0.15, 0.025, Y_CIL - 0.02);
  toro(0.15, 0.02, Y_CIL + 0.06);
  cil(vedacao, 0.2, 0.2, 0.05, M.borracha, 0, Y_CIL - 0.1, 0);          // raspador

  const haste = comp('haste_cilindro', 'Haste do cilindro', { explode: [0, 0.35, 0] });
  cil(haste, 0.12, 0.12, 2.15, M.cromo, 0, 3.47, 0);                    // da câmara até o martelo

  // ── Martelo (cabeçote móvel) ─────────────────────────────────────────────
  const Y_MART = 2.3;
  const martelo = comp('martelo', 'Martelo (cabeçote móvel)', { explode: [0, 0, 1.3] });
  caixa(martelo, 1.5, 0.42, 1.1, M.amarelo, 0, Y_MART, 0);
  for (const [x, z] of colunasXZ) {
    caixa(martelo, 0.28, 0.3, 0.2, M.amarelo, x * 0.9, Y_MART, z * 0.72); // braços até as buchas
    cil(martelo, 0.16, 0.16, 0.36, M.amarelo, x, Y_MART, z);             // alojamento
  }
  cil(martelo, 0.2, 0.2, 0.08, M.usinado, 0, Y_MART + 0.25, 0);          // acoplamento da haste

  const buchas = comp('buchas_guia', 'Buchas guia do martelo', { explode: [0, 0.35, 1.3] });
  for (const [x, z] of colunasXZ) cil(buchas, 0.115, 0.115, 0.5, M.bronze, x, Y_MART, z);

  const puncao = comp('puncao', 'Punção', { explode: [0, -0.3, 1.8] });
  caixa(puncao, 0.8, 0.12, 0.6, M.ferramenta, 0, Y_MART - 0.27, 0);      // porta-punção
  caixa(puncao, 0.55, 0.28, 0.4, M.usinado, 0, Y_MART - 0.47, 0);

  const matriz = comp('matriz_corte', 'Matriz de corte', { explode: [0, 0, 2.2] });
  caixa(matriz, 1.1, 0.22, 0.75, M.ferramenta, 0, 0.78, 0);
  caixa(matriz, 0.6, 0.02, 0.44, M.preto, 0, 0.9, 0);                    // cavidade
  for (const [x, z] of [[-0.45, -0.28], [0.45, -0.28], [-0.45, 0.28], [0.45, 0.28]]) {
    cil(matriz, 0.03, 0.03, 0.3, M.cromo, x, 1.04, z, 16);                // pinos guia
  }

  // ── Unidade hidráulica (lado direito) ────────────────────────────────────
  const UX = 1.95, UZ = -0.15;
  const tanque = comp('reservatorio_oleo', 'Reservatório de óleo', { explode: [1.3, 0, 0] });
  caixa(tanque, 0.9, 0.7, 0.85, M.tanque, UX, 0.35, UZ);
  caixa(tanque, 0.95, 0.04, 0.9, M.pinturaEscura, UX, 0.72, UZ);         // tampa
  cilX(tanque, 0.035, 0.05, M.preto, UX - 0.47, 0.45, UZ + 0.2);         // visor de nível
  caixa(tanque, 0.01, 0.2, 0.05, std(0xD4A017, 0.1, 0.3, { transparent: true, opacity: 0.8 }), UX - 0.455, 0.4, UZ + 0.2);

  const motorBomba = comp('motor_bomba', 'Motor da bomba', { explode: [1.4, 0.7, 0] });
  cilX(motorBomba, 0.2, 0.55, M.motor, UX - 0.15, 0.97, UZ);
  for (let i = 0; i < 6; i++) cilX(motorBomba, 0.215, 0.025, M.motor, UX - 0.38 + i * 0.09, 0.97, UZ);
  cilX(motorBomba, 0.17, 0.08, M.pinturaEscura, UX - 0.46, 0.97, UZ);    // tampa do ventilador
  caixa(motorBomba, 0.16, 0.12, 0.14, M.motor, UX - 0.1, 1.2, UZ);      // caixa de ligação
  caixa(motorBomba, 0.4, 0.05, 0.3, M.pinturaEscura, UX - 0.15, 0.76, UZ); // pés

  const bomba = comp('bomba_hidraulica', 'Bomba hidráulica', { explode: [1.9, 0.7, 0] });
  cilX(bomba, 0.09, 0.08, M.usinado, UX + 0.17, 0.97, UZ);               // lanterna/acoplamento
  cilX(bomba, 0.13, 0.25, M.cinza, UX + 0.33, 0.97, UZ);
  caixa(bomba, 0.12, 0.08, 0.12, M.cinza, UX + 0.33, 1.12, UZ);          // saída

  const filtro = comp('filtro_oleo', 'Filtro de óleo', { explode: [1.8, 0.3, 0.7] });
  cil(filtro, 0.085, 0.085, 0.34, M.preto, UX + 0.28, 0.93, UZ + 0.3);
  cil(filtro, 0.095, 0.095, 0.05, M.usinado, UX + 0.28, 1.12, UZ + 0.3);

  const valvula = comp('valvula_direcional', 'Bloco de válvulas direcionais', { explode: [1.4, 0.4, 1.0] });
  caixa(valvula, 0.36, 0.2, 0.22, M.usinado, UX - 0.1, 0.84, UZ + 0.33);
  caixa(valvula, 0.3, 0.1, 0.16, M.cinza, UX - 0.1, 0.99, UZ + 0.33);
  cilX(valvula, 0.045, 0.1, M.preto, UX - 0.33, 0.99, UZ + 0.33);        // solenoides
  cilX(valvula, 0.045, 0.1, M.preto, UX + 0.13, 0.99, UZ + 0.33);

  const manometro = comp('manometro', 'Manômetro', { explode: [1.6, 0.9, 1.2] });
  cil(manometro, 0.012, 0.012, 0.16, M.usinado, UX - 0.1, 1.12, UZ + 0.38, 8);
  cilZ(manometro, 0.09, 0.045, M.usinado, UX - 0.1, 1.28, UZ + 0.38);
  cilZ(manometro, 0.078, 0.005, M.branco, UX - 0.1, 1.28, UZ + 0.405);
  const ponteiro = caixa(manometro, 0.006, 0.065, 0.004, M.vermelho, UX - 0.1, 1.29, UZ + 0.41);
  ponteiro.rotation.z = -0.8;

  const mangueiras = comp('mangueiras', 'Mangueiras hidráulicas', { explode: [0.8, 0, 0] });
  const tubo = (pontos) => {
    const curva = new THREE.CatmullRomCurve3(pontos.map(p => new THREE.Vector3(...p)));
    mangueiras.add(new THREE.Mesh(new THREE.TubeGeometry(curva, 64, 0.028, 10, false), M.borracha));
  };
  tubo([[UX - 0.2, 1.06, UZ + 0.4], [UX - 0.35, 1.8, UZ + 0.55], [1.4, 3.3, 0.55], [0.8, 4.75, 0.5], [0.26, Y_CIL + 1.0, 0.3]]);
  tubo([[UX, 1.06, UZ + 0.4], [UX - 0.15, 1.9, UZ + 0.62], [1.5, 3.2, 0.62], [0.75, 4.05, 0.5], [0.26, Y_CIL + 0.2, 0.3]]);

  // ── Comando e segurança ──────────────────────────────────────────────────
  const PX = -1.75, PZ = 0.95;
  const painel = comp('painel_controle', 'Painel de controle (CLP/IHM)', { explode: [-1.2, 0, 0.4] });
  caixa(painel, 0.1, 1.05, 0.1, M.pinturaEscura, PX, 0.525, PZ);         // pedestal
  caixa(painel, 0.55, 0.62, 0.26, std(0xD6DAE0, 0.2, 0.5), PX, 1.36, PZ);
  caixa(painel, 0.34, 0.22, 0.01, M.tela, PX, 1.5, PZ + 0.131);          // IHM
  for (const [dx, mat] of [[-0.17, M.verde], [0.17, M.verde]]) {         // bimanuais
    cilZ(painel, 0.035, 0.03, mat, PX + dx, 1.2, PZ + 0.14, 20);
  }

  const emerg = comp('botao_emergencia', 'Botão de emergência', { explode: [-1.3, 0.1, 0.9] });
  cilZ(emerg, 0.06, 0.02, M.amareloSeg, PX, 1.22, PZ + 0.14, 28);
  cilZ(emerg, 0.045, 0.05, M.vermelho, PX, 1.22, PZ + 0.17, 28);
  const cogumelo = new THREE.Mesh(new THREE.SphereGeometry(0.05, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), M.vermelho);
  cogumelo.rotation.x = Math.PI / 2;
  cogumelo.position.set(PX, 1.22, PZ + 0.19);
  emerg.add(cogumelo);

  const cortina = comp('cortina_luz', 'Cortina de luz', { explode: [0, 0.2, 2.6] });
  for (const x of [-0.8, 0.8]) {
    caixa(cortina, 0.06, 1.25, 0.06, M.amareloSeg, x, 1.45, 0.82);
    caixa(cortina, 0.012, 1.15, 0.062, M.preto, x > 0 ? x - 0.03 : x + 0.03, 1.45, 0.82);
  }
  for (let i = 0; i < 9; i++) {
    const f = cilX(cortina, 0.004, 1.54, M.feixe, 0, 0.92 + i * 0.13, 0.82, 6);
    f.castShadow = false;
  }

  return raiz;
}
