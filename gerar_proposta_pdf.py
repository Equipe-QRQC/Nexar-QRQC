from weasyprint import HTML, CSS
import os

html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Nexar — Proposta de Parceria Tecnológica</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', Arial, sans-serif;
    background: #0a0f1e;
    color: #e0e6f0;
    font-size: 11pt;
    line-height: 1.65;
  }

  /* ── CAPA ── */
  .cover {
    width: 100%;
    min-height: 100vh;
    background: linear-gradient(160deg, #0d1b3e 0%, #0a0f1e 60%);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 48pt 52pt;
    page-break-after: always;
    position: relative;
  }

  .cover-logo {
    font-size: 22pt;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 2px;
  }
  .cover-logo span { color: #3b9eff; }

  .cover-subtitle {
    font-size: 9pt;
    color: #7a9cc0;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4pt;
  }

  .cover-center {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-top: 80pt;
  }

  .cover-title {
    font-size: 40pt;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 10pt;
  }
  .cover-title-blue {
    color: #3b9eff;
    font-size: 36pt;
  }

  .cover-rule { width: 80pt; height: 2pt; background: #3b9eff; margin: 18pt 0; }

  .cover-plan {
    font-size: 12pt;
    color: #a0bcd8;
    margin-bottom: 18pt;
  }

  .cover-tags { display: flex; gap: 10pt; flex-wrap: wrap; }
  .cover-tag {
    background: #1a3a6b;
    color: #3b9eff;
    border: 1px solid #3b9eff;
    padding: 4pt 12pt;
    border-radius: 20pt;
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .cover-footer {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    color: #4a6a90;
    font-size: 8pt;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-top: 1px solid #1a2a4a;
    padding-top: 16pt;
  }

  /* ── DECORAÇÃO GEOMÉTRICA CAPA ── */
  .circle-decoration {
    position: absolute;
    right: -80pt;
    top: 50%;
    transform: translateY(-50%);
    width: 320pt;
    height: 320pt;
    border-radius: 50%;
    border: 36pt solid rgba(59,158,255,0.06);
    box-shadow: 0 0 0 60pt rgba(59,158,255,0.04);
  }

  /* ── PÁGINAS INTERNAS ── */
  .page {
    background: #0a0f1e;
    padding: 42pt 52pt 36pt 52pt;
    page-break-after: always;
    min-height: 100vh;
    position: relative;
  }
  .page:last-child { page-break-after: avoid; }

  /* ── CABEÇALHO INTERNO ── */
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28pt;
    padding-bottom: 14pt;
    border-bottom: 2pt solid #1a2a4a;
  }
  .page-logo { font-size: 11pt; font-weight: 800; color: #3b9eff; letter-spacing: 1px; }
  .page-logo-sub { font-size: 6pt; color: #4a6a90; letter-spacing: 2px; text-transform: uppercase; }

  /* ── TÍTULOS ── */
  h1 {
    font-size: 26pt;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 6pt;
    line-height: 1.15;
  }
  h1 .accent { color: #3b9eff; }
  h2 {
    font-size: 15pt;
    font-weight: 700;
    color: #3b9eff;
    margin: 22pt 0 8pt 0;
    padding-bottom: 4pt;
    border-bottom: 1pt solid #1a3a6b;
  }
  h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #7ac4ff;
    margin: 14pt 0 4pt 0;
  }

  .section-rule {
    width: 48pt;
    height: 2pt;
    background: #3b9eff;
    margin-bottom: 20pt;
  }

  p { margin-bottom: 9pt; color: #c8d8ec; }

  /* ── CARDS ── */
  .cards { display: flex; gap: 12pt; margin: 16pt 0; }
  .card {
    flex: 1;
    background: #0e1a30;
    border: 1pt solid #1a2e50;
    border-radius: 8pt;
    padding: 16pt;
  }
  .card-icon {
    width: 12pt;
    height: 12pt;
    background: #3b9eff;
    border-radius: 2pt;
    margin-bottom: 8pt;
  }
  .card-title { font-size: 10pt; font-weight: 700; color: #3b9eff; margin-bottom: 6pt; }
  .card-text { font-size: 9pt; color: #8aabcc; line-height: 1.5; }

  /* ── TABELA ── */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 14pt 0;
    font-size: 9.5pt;
  }
  thead th {
    background: #3b9eff;
    color: #ffffff;
    padding: 9pt 12pt;
    text-align: left;
    font-weight: 700;
    font-size: 9pt;
    letter-spacing: 0.5px;
  }
  tbody tr { border-bottom: 1pt solid #1a2a4a; }
  tbody tr:nth-child(even) { background: #0d1825; }
  td {
    padding: 9pt 12pt;
    color: #b0cae4;
    vertical-align: top;
  }
  td strong { color: #3b9eff; font-weight: 700; }

  /* ── HIGHLIGHT BOX ── */
  .highlight-box {
    background: #0e1a30;
    border-left: 3pt solid #3b9eff;
    border-radius: 6pt;
    padding: 14pt 18pt;
    margin: 16pt 0;
  }
  .highlight-box strong { color: #3b9eff; }
  .highlight-box p { color: #a0bcd8; font-size: 9.5pt; margin-bottom: 5pt; }
  .highlight-box p:last-child { margin-bottom: 0; }

  /* ── LISTA ── */
  ul { padding-left: 16pt; margin-bottom: 10pt; }
  ul li { color: #b0cae4; margin-bottom: 4pt; font-size: 10pt; }
  ul li::marker { color: #3b9eff; }

  /* ── BADGES DE SOLUÇÕES ── */
  .solution-badge {
    display: inline-block;
    padding: 3pt 10pt;
    border-radius: 4pt;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6pt;
  }
  .badge-blue  { background: #1a3a6b; color: #3b9eff; border: 1pt solid #3b9eff; }
  .badge-green { background: #0f2e20; color: #3fd68f; border: 1pt solid #3fd68f; }
  .badge-purple{ background: #1e1040; color: #a87eff; border: 1pt solid #a87eff; }

  /* ── STEPS ── */
  .steps { display: flex; gap: 8pt; margin: 18pt 0; }
  .step {
    flex: 1;
    background: #0e1a30;
    border: 1pt solid #1a2e50;
    border-radius: 8pt;
    padding: 14pt 10pt;
    text-align: center;
  }
  .step-num {
    width: 28pt;
    height: 28pt;
    background: #3b9eff;
    border-radius: 50%;
    color: #fff;
    font-size: 12pt;
    font-weight: 800;
    line-height: 28pt;
    margin: 0 auto 8pt;
  }
  .step-title { font-size: 9pt; font-weight: 700; color: #ffffff; margin-bottom: 4pt; }
  .step-text  { font-size: 8pt; color: #7a9cc0; line-height: 1.4; }

  /* ── MINI CARDS 3x2 ── */
  .mini-cards { display: flex; flex-wrap: wrap; gap: 10pt; margin: 14pt 0; }
  .mini-card {
    flex: 1 1 calc(33% - 10pt);
    background: #0e1a30;
    border: 1pt solid #1a2e50;
    border-radius: 6pt;
    padding: 12pt;
  }
  .mini-card-title { font-size: 9.5pt; font-weight: 700; color: #3b9eff; margin-bottom: 5pt; }
  .mini-card-text  { font-size: 8.5pt; color: #8aabcc; line-height: 1.45; }

  /* ── EQUIPE ── */
  .team-grid { display: flex; flex-wrap: wrap; gap: 10pt; margin: 16pt 0; }
  .team-card {
    flex: 1 1 calc(33% - 10pt);
    background: #0e1a30;
    border: 1pt solid #1a2e50;
    border-radius: 8pt;
    padding: 12pt;
    display: flex;
    align-items: center;
    gap: 12pt;
  }
  .avatar {
    width: 32pt;
    height: 32pt;
    border-radius: 50%;
    background: #3b9eff;
    color: #fff;
    font-size: 10pt;
    font-weight: 800;
    text-align: center;
    line-height: 32pt;
    flex-shrink: 0;
  }
  .team-name  { font-size: 9.5pt; font-weight: 700; color: #ffffff; }
  .team-role  { font-size: 8pt; color: #5a8ab0; }

  /* ── PRÓXIMOS PASSOS ── */
  .steps-list { margin: 16pt 0; }
  .step-item {
    display: flex;
    gap: 14pt;
    align-items: flex-start;
    margin-bottom: 14pt;
  }
  .step-circle {
    width: 26pt;
    height: 26pt;
    border-radius: 50%;
    background: #3b9eff;
    color: #fff;
    font-size: 11pt;
    font-weight: 800;
    text-align: center;
    line-height: 26pt;
    flex-shrink: 0;
  }
  .step-content-title { font-size: 10.5pt; font-weight: 700; color: #3b9eff; margin-bottom: 3pt; }
  .step-content-text  { font-size: 9.5pt; color: #8aabcc; line-height: 1.5; }

  /* ── RODAPÉ FINAL ── */
  .final-cta {
    background: linear-gradient(135deg, #0e1a30, #0d2040);
    border: 1pt solid #1a3a6b;
    border-radius: 10pt;
    padding: 28pt 32pt;
    text-align: center;
    margin-top: 24pt;
  }
  .cta-title { font-size: 20pt; font-weight: 800; color: #ffffff; margin-bottom: 6pt; }
  .cta-subtitle { font-size: 10pt; color: #7a9cc0; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14pt; }
  .cta-email { font-size: 11pt; color: #3b9eff; font-weight: 600; }
  .cta-rule { width: 60pt; height: 2pt; background: #3b9eff; margin: 12pt auto; }

  /* ── PAGE FOOTER ── */
  .page-footer {
    position: absolute;
    bottom: 18pt;
    left: 52pt;
    right: 52pt;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #2a4a70;
    border-top: 1pt solid #0e1a30;
    padding-top: 8pt;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  /* ── IMPACT GRID ── */
  .impact-grid { display: flex; flex-wrap: wrap; gap: 10pt; margin: 14pt 0; }
  .impact-card {
    flex: 1 1 calc(50% - 10pt);
    background: #0e1a30;
    border: 1pt solid #1a2e50;
    border-radius: 6pt;
    padding: 14pt;
  }
  .impact-card-title { font-size: 10pt; font-weight: 700; color: #3b9eff; margin-bottom: 6pt; }
  .impact-card-text  { font-size: 9pt; color: #8aabcc; line-height: 1.5; }

</style>
</head>
<body>

<!-- ══════════════════════════════════════════════
     CAPA
══════════════════════════════════════════════ -->
<div class="cover">
  <div>
    <div class="cover-logo">K<span>NEXAR</span></div>
    <div class="cover-subtitle">Soluções Tecnológicas</div>
  </div>

  <div class="cover-center">
    <div class="cover-title">Proposta de Parceria<br><span class="cover-title-blue">Tecnológica</span></div>
    <div class="cover-rule"></div>
    <div class="cover-plan">Plano Estadual de Bioeconomia do Amazonas</div>
    <div class="cover-tags">
      <span class="cover-tag">Inovação</span>
      <span class="cover-tag">Sustentabilidade</span>
      <span class="cover-tag">Tecnologia</span>
    </div>
  </div>

  <div class="cover-footer">
    <span>NEXAR Soluções Tecnológicas</span>
    <span>Manaus — Amazonas / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 2 — O PLANO DE BIOECONOMIA
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>O Plano Estadual de<br><span class="accent">Bioeconomia</span></h1>
  <div class="section-rule"></div>

  <p>O Governo do Estado do Amazonas lançou em 2026 o <strong style="color:#ffffff">Plano Estadual de Bioeconomia do Amazonas</strong>, um marco estratégico que orienta a transição da economia regional para um modelo sustentável, inclusivo e inovador. O Amazonas concentra <strong style="color:#3b9eff">60% da Floresta Amazônica brasileira</strong>, abriga mais de <strong style="color:#3b9eff">10% de toda a biodiversidade do planeta</strong> e possui cadeias produtivas com potencial de gerar bilhões em receita anual.</p>

  <p>O Plano estrutura-se em <strong style="color:#ffffff">cinco eixos fundamentais</strong>: Governança; Descarbonização e Energias Renováveis; Pessoas e Cultura; Ecossistema de Negócios; e Patrimônio Genético e Cultural.</p>

  <div class="cards">
    <div class="card">
      <div class="card-icon"></div>
      <div class="card-title">Bioindústrias e Biotecnologia</div>
      <div class="card-text">Desenvolvimento de produtos sustentáveis — fármacos, cosméticos, nutracêuticos e bioplásticos — a partir da biodiversidade amazônica. Mercado estimado em <strong>R$ 10 bilhões</strong> nos próximos dez anos.</div>
    </div>
    <div class="card">
      <div class="card-icon"></div>
      <div class="card-title">Manejo Florestal Sustentável</div>
      <div class="card-text">Exploração responsável do açaí, castanha-do-pará, óleos vegetais e pirarucu manejado, garantindo regeneração dos ecossistemas e renda para mais de <strong>500 mil famílias</strong> extrativistas.</div>
    </div>
    <div class="card">
      <div class="card-icon"></div>
      <div class="card-title">Descarbonização e Economia Circular</div>
      <div class="card-text">Adoção de energias renováveis, reaproveitamento de biomassa, mercado de carbono verificável e práticas de baixo carbono que posicionam o Amazonas na agenda ESG global.</div>
    </div>
  </div>

  <div class="highlight-box">
    <strong>A Oportunidade para a Nexar</strong>
    <p style="margin-top:8pt">O Plano demanda soluções de <strong>rastreabilidade digital, gestão de ocorrências, controle de estoque de insumos florestais e plataformas de benefícios</strong> para cooperativas e comunidades — exatamente o portfólio que a Nexar já entrega, com tecnologia local e equipe em Manaus.</p>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 3 — POR QUE A NEXAR
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>Por que a <span class="accent">Nexar?</span></h1>
  <div class="section-rule"></div>

  <p>A Nexar Soluções Tecnológicas é uma empresa <strong style="color:#ffffff">manauara</strong>, especializada no desenvolvimento de sistemas digitais sob medida. Nosso portfólio contempla as principais demandas operacionais do ecossistema de bioeconomia — do controle de produção e rastreabilidade ao engajamento comunitário.</p>

  <table>
    <thead>
      <tr>
        <th>Eixo do Plano de Bioeconomia</th>
        <th>Solução Nexar</th>
        <th>Benefício Direto</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Rastreabilidade de produtos florestais</td>
        <td><strong>NexStock</strong> — Controle de estoque e inventário com exportação PDF/Excel</td>
        <td>Certificação de origem e acesso a mercados premium</td>
      </tr>
      <tr>
        <td>Gestão de ocorrências e falhas operacionais</td>
        <td><strong>QRQC</strong> — Plataforma com IA para diagnóstico e resolução de falhas</td>
        <td>Redução de perdas e conformidade ISO 9001</td>
      </tr>
      <tr>
        <td>Benefícios e inclusão de comunidades</td>
        <td><strong>Receb Desconto</strong> — App de cashback e benefícios para cooperados</td>
        <td>Melhoria da renda real e inclusão financeira</td>
      </tr>
      <tr>
        <td>Monitoramento e dados em tempo real</td>
        <td><strong>Dashboards</strong> gerenciais integrados com KPIs de produção</td>
        <td>Decisão baseada em dados e transparência</td>
      </tr>
      <tr>
        <td>Digitalização de processos internos</td>
        <td><strong>Sistemas personalizados</strong>, automações e plataformas web sob medida</td>
        <td>Eliminação de retrabalho e escalabilidade</td>
      </tr>
    </tbody>
  </table>

  <div class="highlight-box">
    <strong>✔ Tecnologia local, equipe em Manaus, suporte próximo ao cliente.</strong>
    <p style="margin-top:8pt">A Nexar entende a realidade do interior e das cadeias produtivas amazônicas. Conhecemos os desafios logísticos, as limitações de conectividade, a diversidade cultural das comunidades e a urgência de soluções que funcionem na prática. Nossas plataformas são desenvolvidas com foco em <strong>usabilidade, rastreabilidade e resultado</strong> — e em conformidade com SISGEN, Código Florestal, LGPD e requisitos de certificadoras internacionais.</p>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 4 — SOLUÇÕES
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>Nossas Soluções para a <span class="accent">Bioeconomia</span></h1>
  <div class="section-rule"></div>

  <div class="cards">
    <!-- NexStock -->
    <div class="card">
      <div class="solution-badge badge-blue">NexStock</div>
      <div class="card-title" style="font-size:9pt;">Gestão de Estoque</div>
      <p style="font-size:9pt;margin-top:8pt;color:#8aabcc;">Sistema de controle de estoque para cooperativas, agroindústrias e comunidades extrativistas. Gerencia produtos florestais com rastreabilidade completa do campo ao mercado.</p>
      <div style="margin-top:10pt;">
        <div style="font-size:8.5pt;font-weight:700;color:#3b9eff;margin-bottom:5pt;">Funcionalidades:</div>
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Controle de entradas e saídas por lote, fornecedor e data de coleta</li>
          <li>Inventário e rastreabilidade completa de movimentações</li>
          <li>Alertas automáticos de reposição e vencimento</li>
          <li>Exportação em PDF e Excel para auditoria e certificação</li>
          <li>Dashboard com dados em tempo real (desktop e mobile)</li>
          <li>Georreferenciamento da área de coleta por fornecedor</li>
        </ul>
      </div>
    </div>

    <!-- QRQC -->
    <div class="card" style="border-color:#1a3a26;">
      <div class="solution-badge badge-green">QRQC</div>
      <div class="card-title" style="font-size:9pt;color:#3fd68f;">Gestão de Ocorrências com IA</div>
      <p style="font-size:9pt;margin-top:8pt;color:#8aabcc;">Plataforma para identificação, acompanhamento e resolução de falhas operacionais. A IA proprietária da Nexar analisa ocorrências e indica causas prováveis com base em histórico.</p>
      <div style="margin-top:10pt;">
        <div style="font-size:8.5pt;font-weight:700;color:#3fd68f;margin-bottom:5pt;">Funcionalidades:</div>
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Registro digital de ocorrências com foto e localização no processo</li>
          <li>Diagnóstico automático por Inteligência Artificial</li>
          <li>Marcação visual do ponto de falha no diagrama da operação</li>
          <li>Plano de ação integrado com responsável e prazo</li>
          <li>Histórico rastreável por ativo ou equipamento</li>
          <li>Alinhado aos requisitos ISO 9001 e 5 Porquês / Ishikawa</li>
        </ul>
      </div>
    </div>

    <!-- Receb Desconto -->
    <div class="card" style="border-color:#2a1a50;">
      <div class="solution-badge badge-purple">Receb Desconto</div>
      <div class="card-title" style="font-size:9pt;color:#a87eff;">Benefícios e Cashback</div>
      <p style="font-size:9pt;margin-top:8pt;color:#8aabcc;">Plataforma digital de benefícios que conecta cooperados, famílias ribeirinhas e comunidades tradicionais a descontos em parceiros locais — fortalecendo renda e inclusão financeira.</p>
      <div style="margin-top:10pt;">
        <div style="font-size:8.5pt;font-weight:700;color:#a87eff;margin-bottom:5pt;">Funcionalidades:</div>
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>App de benefícios e cashback para cooperados</li>
          <li>Parcerias com empresas e instituições regionais</li>
          <li>Cartão pré-pago de desconto para famílias sem conta bancária</li>
          <li>Relatórios de uso e impacto social para gestores</li>
          <li>Módulo de comunicação interna da cooperativa</li>
          <li>Plataforma moderna, intuitiva e escalável</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 5 — COMO TRABALHAMOS
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>Como <span class="accent">Trabalhamos</span></h1>
  <div class="section-rule"></div>

  <div class="steps">
    <div class="step">
      <div class="step-num">01</div>
      <div class="step-title">Diagnóstico</div>
      <div class="step-text">Mapeamos processos, gargalos e oportunidades de digitalização com todos os usuários reais da operação.</div>
    </div>
    <div class="step">
      <div class="step-num">02</div>
      <div class="step-title">Planejamento</div>
      <div class="step-text">Definimos escopo, tecnologias e cronograma alinhados às metas do Plano de Bioeconomia.</div>
    </div>
    <div class="step">
      <div class="step-num">03</div>
      <div class="step-title">Desenvolvimento</div>
      <div class="step-text">Criamos o sistema com foco em usabilidade, rastreabilidade e conformidade regulatória.</div>
    </div>
    <div class="step">
      <div class="step-num">04</div>
      <div class="step-title">Validação</div>
      <div class="step-text">Testamos com operadores, gestores e comunidades e ajustamos até aprovação total.</div>
    </div>
    <div class="step">
      <div class="step-num">05</div>
      <div class="step-title">Entrega</div>
      <div class="step-text">Implantamos e acompanhamos os primeiros ciclos operacionais com suporte próximo.</div>
    </div>
  </div>

  <div style="text-align:center;color:#4a6a90;font-size:8.5pt;letter-spacing:2px;text-transform:uppercase;margin:6pt 0 20pt;">
    Diagnóstico claro · Processo estratégico · Entrega eficiente
  </div>

  <h2>Diferenciais Estratégicos</h2>

  <div class="mini-cards">
    <div class="mini-card">
      <div class="mini-card-title">Rastreabilidade</div>
      <div class="mini-card-text">Produtos florestais com histórico completo — do extrativista ao mercado consumidor — para certificação e acesso a mercados premium.</div>
    </div>
    <div class="mini-card">
      <div class="mini-card-title">Produtividade</div>
      <div class="mini-card-text">Processos digitais que eliminam planilhas, reduzem erros e economizam até 40% do tempo em atividades administrativas.</div>
    </div>
    <div class="mini-card">
      <div class="mini-card-title">Conformidade</div>
      <div class="mini-card-text">Soluções alinhadas a ISO 9001, LGPD, SISGEN e exigências de certificadoras como FSC, Rainforest Alliance e IFOAM.</div>
    </div>
    <div class="mini-card">
      <div class="mini-card-title">Inclusão Digital</div>
      <div class="mini-card-text">Interfaces acessíveis a cooperados com baixa familiaridade digital, funcionando em dispositivos antigos e conexões instáveis.</div>
    </div>
    <div class="mini-card">
      <div class="mini-card-title">Decisão com Dados</div>
      <div class="mini-card-text">Dashboards que transformam dados operacionais em estratégia — produção, qualidade, impacto social e desempenho financeiro em tempo real.</div>
    </div>
    <div class="mini-card">
      <div class="mini-card-title">Escalabilidade</div>
      <div class="mini-card-text">Plataformas preparadas para crescer: de 50 para 5.000 cooperados, de uma linha para vinte — sem trocar o sistema.</div>
    </div>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 6 — IMPACTO
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>Impacto <span class="accent">Esperado</span></h1>
  <div class="section-rule"></div>

  <p>A parceria entre a Nexar e os atores do Plano Estadual de Bioeconomia tem potencial de gerar impacto mensurável em quatro dimensões fundamentais:</p>

  <div class="impact-grid">
    <div class="impact-card">
      <div class="impact-card-title">Impacto Econômico</div>
      <div class="impact-card-text">
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Aumento da eficiência operacional nas cadeias florestais</li>
          <li>Acesso a mercados premium pela rastreabilidade certificada</li>
          <li>Redução de perdas por falhas não diagnosticadas</li>
          <li>Geração de renda adicional para cooperados via Receb Desconto</li>
        </ul>
      </div>
    </div>
    <div class="impact-card">
      <div class="impact-card-title">Impacto Social</div>
      <div class="impact-card-text">
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Inclusão digital de comunidades ribeirinhas e extrativistas</li>
          <li>Fortalecimento da gestão autônoma de cooperativas</li>
          <li>Valorização do trabalho dos extrativistas com dados verificáveis</li>
          <li>Acesso a serviços financeiros para famílias sem conta bancária</li>
        </ul>
      </div>
    </div>
    <div class="impact-card">
      <div class="impact-card-title">Impacto Ambiental</div>
      <div class="impact-card-text">
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Rastreabilidade que inibe entrada de produtos ilegais nas cadeias formais</li>
          <li>Dados para monitoramento de práticas sustentáveis e planos de manejo</li>
          <li>Apoio à quantificação de carbono e serviços ecossistêmicos</li>
          <li>Subsídio para políticas públicas de conservação baseadas em dados</li>
        </ul>
      </div>
    </div>
    <div class="impact-card">
      <div class="impact-card-title">Impacto na Governança</div>
      <div class="impact-card-text">
        <ul style="font-size:8.5pt;padding-left:12pt;">
          <li>Transparência no uso de recursos públicos da bioeconomia</li>
          <li>Dados consolidados para prestação de contas a financiadores</li>
          <li>Integração entre secretarias, cooperativas e comunidades</li>
          <li>Capacidade de monitoramento de KPIs do Plano em tempo real</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════
     PÁG 7 — EQUIPE + PRÓXIMOS PASSOS
══════════════════════════════════════════════ -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="page-logo">KNEXAR</div>
      <div class="page-logo-sub">Soluções Tecnológicas</div>
    </div>
    <div style="font-size:8pt;color:#2a4a70;letter-spacing:1px;text-transform:uppercase;">Proposta de Parceria · 2026</div>
  </div>

  <h1>Nossa <span class="accent">Equipe</span></h1>
  <div class="section-rule"></div>

  <div class="team-grid">
    <div class="team-card">
      <div class="avatar">EJ</div>
      <div>
        <div class="team-name">Enzo Jimenez</div>
        <div class="team-role">CEO — Estratégia e Negócios</div>
      </div>
    </div>
    <div class="team-card">
      <div class="avatar">GF</div>
      <div>
        <div class="team-name">Given Fellipo</div>
        <div class="team-role">CFO / CTO — Finanças e Tecnologia</div>
      </div>
    </div>
    <div class="team-card">
      <div class="avatar">LP</div>
      <div>
        <div class="team-name">Luma Portela</div>
        <div class="team-role">COO / Designer — Operações e UX</div>
      </div>
    </div>
    <div class="team-card">
      <div class="avatar">CH</div>
      <div>
        <div class="team-name">Carlos Henrique</div>
        <div class="team-role">Software Engineer — TI e Infraestrutura</div>
      </div>
    </div>
    <div class="team-card">
      <div class="avatar">YT</div>
      <div>
        <div class="team-name">Yan Tenorio</div>
        <div class="team-role">Developer — Automação de Processos</div>
      </div>
    </div>
    <div class="team-card">
      <div class="avatar">HM</div>
      <div>
        <div class="team-name">Henrique Mota</div>
        <div class="team-role">Data Scientist / PM — Dados e Projetos</div>
      </div>
    </div>
  </div>

  <h2>Próximos Passos</h2>

  <div class="steps-list">
    <div class="step-item">
      <div class="step-circle">1</div>
      <div>
        <div class="step-content-title">Fale com a Nexar</div>
        <div class="step-content-text">Entre em contato para agendar uma demonstração gratuita adaptada ao contexto da bioeconomia. Em 60 minutos apresentamos como nossas soluções resolvem os problemas que você enfrenta hoje.</div>
      </div>
    </div>
    <div class="step-item">
      <div class="step-circle">2</div>
      <div>
        <div class="step-content-title">Demo Personalizada</div>
        <div class="step-content-text">Nossa equipe apresenta as soluções com os dados e fluxos reais da sua operação ou cooperativa — nenhuma demonstração genérica.</div>
      </div>
    </div>
    <div class="step-item">
      <div class="step-circle">3</div>
      <div>
        <div class="step-content-title">Proposta Técnica e Comercial</div>
        <div class="step-content-text">Elaboramos uma proposta técnica detalhada com escopo, cronograma e modelo de precificação alinhado ao seu orçamento e às metas do Plano.</div>
      </div>
    </div>
    <div class="step-item">
      <div class="step-circle">4</div>
      <div>
        <div class="step-content-title">Operação Modernizada</div>
        <div class="step-content-text">Implantamos a solução e sua equipe passa a operar com mais controle, dados e eficiência — com suporte continuado da Nexar em cada etapa.</div>
      </div>
    </div>
  </div>

  <div class="final-cta">
    <div class="cta-title">Vamos construir juntos.</div>
    <div class="cta-rule"></div>
    <div class="cta-subtitle">Tecnologia · Inovação · Sustentabilidade</div>
    <div class="cta-email">Nexarsolucoestec@gmail.com</div>
    <div style="font-size:8.5pt;color:#4a6a90;margin-top:8pt;letter-spacing:1px;">NEXAR Soluções Tecnológicas — Manaus, AM</div>
  </div>

  <div class="page-footer">
    <span>KNEXAR Soluções Tecnológicas</span>
    <span>Manaus — AM / 2026</span>
  </div>
</div>

</body>
</html>
"""

output_path = "/home/user/Nexar-QRQC/Nexar_Proposta_Bioeconomia_EXPANDIDA.pdf"

print("Gerando PDF...")
HTML(string=html_content).write_pdf(
    output_path,
    stylesheets=[CSS(string="@page { size: A4; margin: 0; }")]
)
print(f"PDF gerado com sucesso: {output_path}")
