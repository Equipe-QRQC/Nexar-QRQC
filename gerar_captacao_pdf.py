from weasyprint import HTML, CSS

# ── paleta ──────────────────────────────────────────────
BG      = "#0a0f1e"
BG2     = "#0e1825"
BG3     = "#0d1535"
BORDER  = "#1a2e50"
BLUE    = "#3b9eff"
BLUE2   = "#1a3a6b"
WHITE   = "#ffffff"
LIGHT   = "#c8d8ec"
MUTED   = "#8aabcc"
DARK    = "#2a4a70"
GREEN   = "#3fd68f"
ORANGE  = "#f5a623"
RED     = "#e05252"

def page(content, title="", subtitle="", pagenum=""):
    header = f"""
    <div class="page-header">
      <div>
        <div class="page-logo">K<span>NEXAR</span></div>
        <div class="page-logo-sub">Soluções Tecnológicas</div>
      </div>
      <div class="page-meta">Nexar QRQC · Projeto de Captação · 2026</div>
    </div>"""
    footer = f"""
    <div class="page-footer">
      <span>NEXAR Soluções Tecnológicas — Manaus/AM</span>
      <span>Projeto Nexar QRQC · 2026</span>
    </div>"""
    return f"""
    <div class="page">
      {header}
      {f'<h1>{title}</h1><div class="section-rule"></div>' if title else ''}
      {content}
      {footer}
    </div>"""

CSS_GLOBAL = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: Arial, Helvetica, sans-serif;
  background: {BG};
  color: {LIGHT};
  font-size: 10.5pt;
  line-height: 1.65;
}}
.page {{
  background: {BG};
  padding: 38pt 48pt 52pt 48pt;
  page-break-after: always;
  min-height: 100vh;
  position: relative;
}}
.page:last-child {{ page-break-after: avoid; }}

/* HEADER */
.page-header {{
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24pt;
  padding-bottom: 10pt;
  border-bottom: 1.5pt solid {BORDER};
}}
.page-logo {{ font-size: 13pt; font-weight: 900; color: {WHITE}; letter-spacing: 1px; }}
.page-logo span {{ color: {BLUE}; }}
.page-logo-sub {{ font-size: 5.5pt; color: {DARK}; letter-spacing: 2px; text-transform: uppercase; }}
.page-meta {{ font-size: 7pt; color: {DARK}; letter-spacing: 1px; text-transform: uppercase; }}

/* FOOTER */
.page-footer {{
  position: absolute; bottom: 16pt; left: 48pt; right: 48pt;
  display: flex; justify-content: space-between;
  font-size: 7pt; color: {DARK};
  border-top: 1pt solid {BORDER}; padding-top: 7pt;
  letter-spacing: 0.8px; text-transform: uppercase;
}}

/* TITLES */
h1 {{ font-size: 22pt; font-weight: 900; color: {WHITE}; margin-bottom: 4pt; line-height: 1.2; }}
h1 .accent {{ color: {BLUE}; }}
h2 {{ font-size: 12pt; font-weight: 800; color: {BLUE}; margin: 18pt 0 7pt 0; padding-bottom: 3pt; border-bottom: 1pt solid {BLUE2}; }}
h3 {{ font-size: 10.5pt; font-weight: 700; color: #7ac4ff; margin: 12pt 0 4pt 0; }}
.section-rule {{ width: 40pt; height: 2pt; background: {BLUE}; margin-bottom: 18pt; }}

p {{ margin-bottom: 8pt; color: {LIGHT}; }}
strong {{ color: {WHITE}; font-weight: 700; }}
ul {{ padding-left: 14pt; margin-bottom: 9pt; }}
ul li {{ color: {MUTED}; margin-bottom: 3pt; font-size: 10pt; }}
ul li::marker {{ color: {BLUE}; }}

/* COVER */
.cover {{
  background: linear-gradient(155deg, #0d1b3e 0%, {BG} 65%);
  padding: 44pt 52pt;
  min-height: 100vh;
  page-break-after: always;
  display: flex; flex-direction: column; justify-content: space-between;
}}
.cover-logo {{ font-size: 22pt; font-weight: 900; color: {WHITE}; letter-spacing: 2px; }}
.cover-logo span {{ color: {BLUE}; }}
.cover-logo-sub {{ font-size: 7pt; color: {DARK}; letter-spacing: 3px; text-transform: uppercase; margin-top: 3pt; }}
.cover-center {{ flex: 1; display: flex; flex-direction: column; justify-content: center; margin-top: 70pt; }}
.cover-eyebrow {{ font-size: 8pt; color: {BLUE}; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 12pt; }}
.cover-title {{ font-size: 34pt; font-weight: 900; color: {WHITE}; line-height: 1.1; margin-bottom: 8pt; }}
.cover-title-blue {{ color: {BLUE}; font-size: 30pt; }}
.cover-rule {{ width: 60pt; height: 2pt; background: {BLUE}; margin: 16pt 0; }}
.cover-desc {{ font-size: 11pt; color: {MUTED}; max-width: 360pt; line-height: 1.6; margin-bottom: 20pt; }}
.cover-tags {{ display: flex; gap: 8pt; flex-wrap: wrap; }}
.cover-tag {{
  background: {BLUE2}; color: {BLUE}; border: 1pt solid {BLUE};
  padding: 4pt 12pt; border-radius: 20pt;
  font-size: 7.5pt; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
}}
.cover-meta {{
  background: {BG2}; border: 1pt solid {BORDER}; border-radius: 8pt;
  padding: 16pt 20pt; margin-top: 28pt;
}}
.cover-meta-grid {{ display: flex; gap: 24pt; flex-wrap: wrap; }}
.cover-meta-item {{ flex: 1; }}
.cover-meta-label {{ font-size: 6.5pt; color: {DARK}; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 3pt; }}
.cover-meta-value {{ font-size: 10pt; font-weight: 700; color: {WHITE}; }}
.cover-footer {{
  display: flex; justify-content: space-between; align-items: flex-end;
  color: {DARK}; font-size: 7.5pt; letter-spacing: 1px; text-transform: uppercase;
  border-top: 1pt solid {BORDER}; padding-top: 14pt;
}}

/* TABLE */
table {{ width: 100%; border-collapse: collapse; margin: 12pt 0; font-size: 9pt; }}
thead th {{ background: {BLUE}; color: {WHITE}; padding: 8pt 10pt; text-align: left; font-weight: 700; font-size: 8.5pt; }}
tbody tr {{ border-bottom: 1pt solid {BORDER}; }}
tbody tr:nth-child(even) {{ background: {BG2}; }}
td {{ padding: 7pt 10pt; color: {MUTED}; vertical-align: top; }}
td strong {{ color: {BLUE}; }}

/* CARDS */
.cards {{ display: flex; gap: 10pt; margin: 14pt 0; }}
.card {{ flex: 1; background: {BG2}; border: 1pt solid {BORDER}; border-radius: 7pt; padding: 14pt; }}
.card-dot {{ width: 10pt; height: 10pt; background: {BLUE}; border-radius: 2pt; margin-bottom: 7pt; }}
.card-title {{ font-size: 9.5pt; font-weight: 700; color: {BLUE}; margin-bottom: 5pt; }}
.card-text {{ font-size: 8.5pt; color: {MUTED}; line-height: 1.5; }}

/* HIGHLIGHT */
.hl {{ background: {BG3}; border-left: 3pt solid {BLUE}; border-radius: 5pt; padding: 12pt 16pt; margin: 14pt 0; }}
.hl strong {{ color: {BLUE}; }}
.hl p {{ color: {MUTED}; font-size: 9.5pt; margin-bottom: 4pt; }}
.hl p:last-child {{ margin-bottom: 0; }}

/* MINI CARDS */
.mini-cards {{ display: flex; flex-wrap: wrap; gap: 9pt; margin: 12pt 0; }}
.mini-card {{ flex: 1 1 calc(33% - 9pt); background: {BG2}; border: 1pt solid {BORDER}; border-radius: 6pt; padding: 11pt; }}
.mini-card-title {{ font-size: 9pt; font-weight: 700; color: {BLUE}; margin-bottom: 4pt; }}
.mini-card-text  {{ font-size: 8.5pt; color: {MUTED}; line-height: 1.45; }}

/* STEPS */
.steps {{ display: flex; gap: 7pt; margin: 14pt 0; }}
.step {{ flex: 1; background: {BG2}; border: 1pt solid {BORDER}; border-radius: 7pt; padding: 12pt 8pt; text-align: center; }}
.step-num {{ width: 24pt; height: 24pt; background: {BLUE}; border-radius: 50%; color: {WHITE}; font-size: 9.5pt; font-weight: 900; line-height: 24pt; margin: 0 auto 7pt; text-align: center; }}
.step-title {{ font-size: 8.5pt; font-weight: 700; color: {WHITE}; margin-bottom: 3pt; }}
.step-text  {{ font-size: 7.5pt; color: {MUTED}; line-height: 1.4; }}

/* PHASE BLOCK */
.phase {{ background: {BG2}; border: 1pt solid {BORDER}; border-radius: 7pt; padding: 12pt 15pt; margin-bottom: 9pt; }}
.phase-header {{ display: flex; align-items: center; gap: 10pt; margin-bottom: 6pt; }}
.phase-num {{ background: {BLUE}; color: {WHITE}; font-size: 8pt; font-weight: 900; padding: 3pt 8pt; border-radius: 3pt; white-space: nowrap; }}
.phase-title {{ font-size: 10pt; font-weight: 700; color: {WHITE}; }}
.phase-period {{ font-size: 8pt; color: {DARK}; margin-left: auto; }}
.phase-text {{ font-size: 9pt; color: {MUTED}; line-height: 1.5; }}

/* RISK TABLE */
.risk-high {{ color: #e05252; font-weight: 700; }}
.risk-med  {{ color: {ORANGE}; font-weight: 700; }}
.risk-low  {{ color: {GREEN}; font-weight: 700; }}

/* PITCH */
.pitch-box {{
  background: linear-gradient(135deg, {BG3}, {BG2});
  border: 1pt solid {BLUE};
  border-radius: 9pt;
  padding: 22pt 26pt;
  margin: 14pt 0;
}}
.pitch-text {{ font-size: 11pt; color: {LIGHT}; line-height: 1.75; font-style: italic; }}

/* CTA FINAL */
.cta {{
  background: linear-gradient(135deg, {BG3}, {BG2});
  border: 1pt solid {BLUE2};
  border-radius: 10pt;
  padding: 24pt 28pt;
  text-align: center;
  margin-top: 20pt;
}}
.cta-title {{ font-size: 18pt; font-weight: 900; color: {WHITE}; margin-bottom: 5pt; }}
.cta-rule  {{ width: 50pt; height: 2pt; background: {BLUE}; margin: 10pt auto; }}
.cta-sub   {{ font-size: 8.5pt; color: {DARK}; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10pt; }}
.cta-email {{ font-size: 11pt; color: {BLUE}; font-weight: 700; }}

/* CHECKLIST */
.checklist-section {{ margin-bottom: 14pt; }}
.checklist-title {{ font-size: 10pt; font-weight: 700; color: {BLUE}; margin-bottom: 5pt; }}
.checklist-item {{ display: flex; align-items: flex-start; gap: 7pt; margin-bottom: 4pt; }}
.checkbox {{ width: 9pt; height: 9pt; border: 1.5pt solid {BLUE}; border-radius: 2pt; flex-shrink: 0; margin-top: 2pt; }}
.checklist-text {{ font-size: 9pt; color: {MUTED}; }}

/* IMPACT */
.impact-grid {{ display: flex; flex-wrap: wrap; gap: 9pt; margin: 12pt 0; }}
.impact-card {{ flex: 1 1 calc(50% - 9pt); background: {BG2}; border: 1pt solid {BORDER}; border-radius: 6pt; padding: 12pt; }}
.impact-title {{ font-size: 9.5pt; font-weight: 700; color: {BLUE}; margin-bottom: 6pt; }}

/* TEAM */
.team-grid {{ display: flex; flex-wrap: wrap; gap: 9pt; margin: 12pt 0; }}
.team-card {{ flex: 1 1 calc(50% - 9pt); background: {BG2}; border: 1pt solid {BORDER}; border-radius: 7pt; padding: 12pt; display: flex; gap: 12pt; align-items: flex-start; }}
.avatar {{ width: 30pt; height: 30pt; border-radius: 50%; background: {BLUE}; color: {WHITE}; font-size: 9pt; font-weight: 900; text-align: center; line-height: 30pt; flex-shrink: 0; }}
.team-name {{ font-size: 9.5pt; font-weight: 700; color: {WHITE}; }}
.team-role {{ font-size: 8pt; color: {BLUE}; margin-bottom: 3pt; }}
.team-desc {{ font-size: 8pt; color: {MUTED}; line-height: 1.4; }}

/* BADGE */
.badge {{ display: inline-block; padding: 2pt 8pt; border-radius: 3pt; font-size: 7.5pt; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-right: 4pt; }}
.badge-blue   {{ background: {BLUE2}; color: {BLUE}; border: 1pt solid {BLUE}; }}
.badge-green  {{ background: #0f2e20; color: {GREEN}; border: 1pt solid {GREEN}; }}
.badge-orange {{ background: #2e1e0a; color: {ORANGE}; border: 1pt solid {ORANGE}; }}

/* TITLE OPTIONS */
.title-option {{ background: {BG2}; border: 1pt solid {BORDER}; border-radius: 6pt; padding: 11pt 14pt; margin-bottom: 8pt; }}
.title-option-num {{ font-size: 7.5pt; color: {BLUE}; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4pt; }}
.title-option-text {{ font-size: 10pt; color: {WHITE}; font-weight: 600; line-height: 1.4; font-style: italic; }}
.title-option-tag {{ font-size: 7pt; color: {DARK}; margin-top: 4pt; }}

/* OBJ LIST */
.obj-item {{ display: flex; gap: 10pt; align-items: flex-start; margin-bottom: 9pt; }}
.obj-num {{ background: {BLUE}; color: {WHITE}; font-size: 8pt; font-weight: 900; min-width: 22pt; height: 22pt; border-radius: 50%; text-align: center; line-height: 22pt; flex-shrink: 0; }}
.obj-title {{ font-size: 10pt; font-weight: 700; color: {WHITE}; margin-bottom: 2pt; }}
.obj-text  {{ font-size: 9pt; color: {MUTED}; line-height: 1.5; }}
"""

# ════════════════════════════════════════
# CAPA
# ════════════════════════════════════════
cover = f"""
<div class="cover">
  <div>
    <div class="cover-logo">K<span>NEXAR</span></div>
    <div class="cover-logo-sub">Soluções Tecnológicas</div>
  </div>
  <div class="cover-center">
    <div class="cover-eyebrow">Projeto de Captação de Recursos — Edital de Inovação</div>
    <div class="cover-title">Nexar<br><span class="cover-title-blue">QRQC</span></div>
    <div class="cover-rule"></div>
    <div class="cover-desc">Plataforma de Inteligência Artificial Multimodal para Registro, Diagnóstico e Resolução de Ocorrências Industriais</div>
    <div class="cover-tags">
      <span class="cover-tag">Deep Tech</span>
      <span class="cover-tag">IA Multimodal</span>
      <span class="cover-tag">Indústria 4.0</span>
      <span class="cover-tag">Polo Industrial de Manaus</span>
      <span class="cover-tag">FAPEAM · Centelha · Tecnova</span>
    </div>
    <div class="cover-meta">
      <div class="cover-meta-grid">
        <div class="cover-meta-item">
          <div class="cover-meta-label">Empresa Proponente</div>
          <div class="cover-meta-value">Nexar Soluções Tecnológicas</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Localização</div>
          <div class="cover-meta-value">Manaus — Amazonas</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Valor Pretendido</div>
          <div class="cover-meta-value">R$ 125.000,00</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Estágio (TRL)</div>
          <div class="cover-meta-value">TRL 4–5 → TRL 7</div>
        </div>
      </div>
    </div>
  </div>
  <div class="cover-footer">
    <span>NEXAR Soluções Tecnológicas · Manaus/AM</span>
    <span>Subvenção Econômica · 2026</span>
  </div>
</div>
"""

# ════════════════════════════════════════
# PÁG 2 — RESUMO EXECUTIVO
# ════════════════════════════════════════
p2 = page(f"""
<table>
  <thead><tr><th>Campo</th><th>Informação</th></tr></thead>
  <tbody>
    <tr><td><strong>Nome do Projeto</strong></td><td>Nexar QRQC — Plataforma de IA para Gestão de Ocorrências Industriais</td></tr>
    <tr><td><strong>Empresa Proponente</strong></td><td>Nexar Soluções Tecnológicas LTDA — Manaus/AM</td></tr>
    <tr><td><strong>CNAE Principal</strong></td><td>6201-5/01 — Desenvolvimento de programas de computador sob encomenda</td></tr>
    <tr><td><strong>Estágio do Projeto</strong></td><td>TRL 4–5 — MVP funcional em fase de validação industrial</td></tr>
    <tr><td><strong>Valor Pretendido</strong></td><td>R$ 125.000,00 — Recursos não reembolsáveis / Subvenção econômica</td></tr>
    <tr><td><strong>Editais Alvo</strong></td><td>FAPEAM · Programa Centelha · Tecnova III · Deep Tech Brasil · FINEP Startup</td></tr>
  </tbody>
</table>

<div style="display:flex;gap:10pt;margin:14pt 0;">
  <div class="card">
    <div class="card-dot"></div>
    <div class="card-title">Problema</div>
    <div class="card-text">Indústrias do Polo Industrial de Manaus sofrem perdas de produtividade por identificação tardia de falhas, ausência de registros padronizados, dependência de conhecimento informal e falta de ferramentas digitais acessíveis ao operador de chão de fábrica.</div>
  </div>
  <div class="card">
    <div class="card-dot"></div>
    <div class="card-title">Solução</div>
    <div class="card-text">Plataforma web com IA multimodal que digitaliza a metodologia QRQC — o operador registra a falha, anexa foto ou diagrama e recebe em tempo real análise automatizada com possíveis causas e próximos passos recomendados.</div>
  </div>
  <div class="card">
    <div class="card-dot"></div>
    <div class="card-title">Inovação</div>
    <div class="card-text">Combinação inédita de IA multimodal (texto + imagem + diagrama técnico), digitalização da metodologia QRQC e geração de base histórica de conhecimento industrial — desenvolvida por empresa de base tecnológica amazonense.</div>
  </div>
</div>

<div style="display:flex;gap:10pt;">
  <div class="card" style="flex:2;">
    <div class="card-dot"></div>
    <div class="card-title">Impacto Esperado</div>
    <div class="card-text">Redução do tempo médio de resposta a ocorrências industriais · Aumento da produtividade do PIM · Criação de base de conhecimento técnico institucional · Fortalecimento do ecossistema de tecnologia do Amazonas · Geração de empregos qualificados</div>
  </div>
  <div class="card" style="flex:1;">
    <div class="card-dot"></div>
    <div class="card-title">Público-alvo</div>
    <div class="card-text">Indústrias de manufatura · Fábricas do Polo Industrial de Manaus · Gestores de manutenção e qualidade · Operadores industriais</div>
  </div>
</div>

<div class="hl" style="margin-top:14pt;">
  <strong>Objetivo da Captação</strong>
  <p style="margin-top:7pt;">Financiar o aprimoramento técnico da plataforma, o refinamento dos modelos de IA, a migração para infraestrutura em nuvem escalável, a realização de projeto piloto com empresas industriais do Polo Industrial de Manaus e a preparação comercial para escala nacional — consolidando o Nexar QRQC como produto tecnológico de referência em gestão de ocorrências industriais com IA.</p>
</div>
""", "Resumo <span class='accent'>Executivo</span>")

# ════════════════════════════════════════
# PÁG 3 — TÍTULOS + PROBLEMA
# ════════════════════════════════════════
p3 = page(f"""
<h2>Opções de Título Técnico e Institucional</h2>
<div class="title-option">
  <div class="title-option-num">Opção 1 — Foco em IA e Indústria</div>
  <div class="title-option-text">"Desenvolvimento e Validação de Plataforma de Inteligência Artificial Multimodal para Diagnóstico e Gestão de Ocorrências em Ambientes Industriais"</div>
</div>
<div class="title-option">
  <div class="title-option-num">Opção 2 — Foco em Inovação Regional</div>
  <div class="title-option-text">"QRQC Digital: Plataforma Amazonense de IA Aplicada à Manutenção Industrial e Controle de Qualidade em Tempo Real"</div>
</div>
<div class="title-option">
  <div class="title-option-num">Opção 3 — Foco em Indústria 4.0</div>
  <div class="title-option-text">"Nexar QRQC: Solução de Base Tecnológica para Digitalização da Gestão de Falhas Industriais com Suporte de Inteligência Artificial"</div>
</div>
<div class="title-option">
  <div class="title-option-num">Opção 4 — Foco em Competitividade</div>
  <div class="title-option-text">"Plataforma Inteligente de Resposta Rápida a Ocorrências Industriais: Inovação para o Aumento da Produtividade no Polo Industrial de Manaus"</div>
</div>
<div class="title-option">
  <div class="title-option-num">Opção 5 — Linguagem Deep Tech</div>
  <div class="title-option-text">"Deep Tech Industrial: Sistema de IA Multimodal para Diagnóstico Automatizado de Falhas em Máquinas e Linhas de Produção"</div>
</div>

<h2 style="margin-top:18pt;">Descrição do Problema</h2>
<p>A gestão de ocorrências em ambientes industriais constitui um dos principais desafios de manufaturas no Brasil. No Polo Industrial de Manaus — com mais de 500 empresas e R$ 90 bilhões em faturamento anual — a ausência de ferramentas digitais adequadas representa uma vulnerabilidade estrutural. Os principais gargalos são:</p>
<div style="display:flex;gap:9pt;flex-wrap:wrap;">
  <div class="mini-card">
    <div class="mini-card-title">Demora na Identificação</div>
    <div class="mini-card-text">A comunicação verbal de falhas e o registro manual em papel estendem paradas de máquina de minutos para horas, comprometendo diretamente a eficiência da linha.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Falta de Padronização</div>
    <div class="mini-card-text">Sem sistema centralizado, cada operador registra informações de forma diferente — ou não registra. Isso inviabiliza análise de padrões e rastreabilidade histórica.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Conhecimento Informal</div>
    <div class="mini-card-text">O diagnóstico depende da experiência pessoal de técnicos específicos. Quando saem, o conhecimento acumulado vai embora — risco operacional e de competitividade.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Sem Rastreabilidade</div>
    <div class="mini-card-text">Sem registro digital estruturado, não é possível rastrear ocorrências por máquina, linha ou turno — impossibilitando análises de causa raiz baseadas em dados.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Ferramentas Inacessíveis</div>
    <div class="mini-card-text">Sistemas ERP e CMMS existentes são complexos, caros e projetados para equipes técnicas especializadas — inacessíveis ao operador de chão de fábrica.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Ausência de IA</div>
    <div class="mini-card-text">Nenhuma solução acessível ao mercado industrial de médio porte oferece hoje suporte por IA multimodal ao operador no momento do registro da ocorrência.</div>
  </div>
</div>
""", "Títulos e <span class='accent'>Problema</span>")

# ════════════════════════════════════════
# PÁG 4 — JUSTIFICATIVA + OBJ GERAL
# ════════════════════════════════════════
p4 = page(f"""
<p>O Polo Industrial de Manaus (PIM) é o maior polo industrial do Norte do Brasil — 500+ empresas, 100.000+ empregos diretos, sustentação econômica do Estado. Sua competitividade está vinculada à adoção de ferramentas de gestão alinhadas a padrões internacionais. A Nexar surge como empresa de base tecnológica amazonense capaz de desenvolver soluções pertinentes, acessíveis e adaptadas à realidade industrial da região.</p>

<div style="display:flex;gap:9pt;margin:12pt 0;">
  <div class="card">
    <div class="card-title">Alinhamento com ENIAC</div>
    <div class="card-text">Estratégia Nacional de Inteligência Artificial — fomento ao desenvolvimento e aplicação de IA em setores produtivos estratégicos.</div>
  </div>
  <div class="card">
    <div class="card-title">Zona Franca de Manaus</div>
    <div class="card-text">A SUFRAMA incentiva inovação tecnológica como mecanismo de sustentabilidade do modelo ZFM e competitividade das indústrias do PIM.</div>
  </div>
  <div class="card">
    <div class="card-title">ODS 8 e ODS 9</div>
    <div class="card-text">Crescimento econômico sustentável, emprego digno, inovação e infraestrutura industrial inclusiva — Agenda 2030 da ONU.</div>
  </div>
</div>

<div class="hl">
  <strong>Lacuna de Mercado</strong>
  <p style="margin-top:6pt;">O mercado global de software CMMS movimenta mais de <strong>US$ 1,2 bilhão/ano</strong> com crescimento de 8% a.a. No Brasil, as soluções são majoritariamente importadas, de alto custo e sem suporte especializado em PMEs industriais. O Nexar QRQC endereça essa lacuna com solução nacional, acessível, baseada em IA e desenvolvida a partir do Amazonas.</p>
</div>

<h2>Objetivo Geral</h2>
<div class="hl">
  <p style="font-size:10.5pt;color:#c8d8ec;line-height:1.7;">Desenvolver, aprimorar e validar em ambiente industrial real a plataforma <strong>Nexar QRQC</strong> — sistema web de Inteligência Artificial multimodal para registro, análise automatizada, diagnóstico e resolução de ocorrências em máquinas e linhas de produção —, com vistas à sua consolidação como produto tecnológico escalável, à geração de impacto positivo na produtividade industrial do Polo Industrial de Manaus e ao fortalecimento do ecossistema de empresas de base tecnológica do Estado do Amazonas.</p>
</div>

<h2>Objetivos Específicos</h2>
<div class="obj-item">
  <div class="obj-num">1</div>
  <div><div class="obj-title">Aprimoramento da Inteligência Artificial</div><div class="obj-text">Refinar os modelos de IA multimodal, melhorando a precisão do diagnóstico automatizado a partir da análise combinada de texto, imagens e diagramas técnicos de máquinas.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">2</div>
  <div><div class="obj-title">Migração e Estruturação de Infraestrutura</div><div class="obj-text">Migrar o banco de dados para PostgreSQL e implantar a solução em infraestrutura cloud, garantindo escalabilidade, segurança e disponibilidade industrial.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">3</div>
  <div><div class="obj-title">Aprimoramento de Interface e UX</div><div class="obj-text">Redesenhar interfaces com foco em usabilidade para operadores de chão de fábrica, priorizando acessibilidade e eficiência operacional na tela totem e painel de gestão.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">4</div>
  <div><div class="obj-title">Módulo de Relatórios e KPIs</div><div class="obj-text">Criar módulo completo de relatórios gerenciais com indicadores de manutenção e qualidade, exportação em PDF/Excel e dashboards interativos.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">5</div>
  <div><div class="obj-title">Segurança da Informação e LGPD</div><div class="obj-text">Adequar a plataforma às normas LGPD e OWASP, implementando autenticação segura, controle de acesso por perfil, criptografia e auditoria de acessos.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">6</div>
  <div><div class="obj-title">Validação em Ambiente Industrial (Piloto)</div><div class="obj-text">Realizar implantação piloto em ao menos 2 empresas industriais do PIM, coletando métricas de desempenho, satisfação e usabilidade em ambiente real.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">7</div>
  <div><div class="obj-title">Documentação Técnica e Propriedade Intelectual</div><div class="obj-text">Produzir documentação completa da plataforma e iniciar o processo de registro de software junto ao INPI.</div></div>
</div>
<div class="obj-item">
  <div class="obj-num">8</div>
  <div><div class="obj-title">Preparação para Escala Comercial</div><div class="obj-text">Estruturar modelo de negócios, precificação, estratégia de go-to-market e materiais comerciais para oferta ao mercado industrial nacional.</div></div>
</div>
""", "Justificativa e <span class='accent'>Objetivos</span>")

# ════════════════════════════════════════
# PÁG 5 — DESCRIÇÃO DA SOLUÇÃO
# ════════════════════════════════════════
p5 = page(f"""
<p>O <strong>Nexar QRQC</strong> é uma plataforma web de Inteligência Artificial que digitaliza e potencializa a metodologia Quick Response Quality Control (QRQC), incorporando IA multimodal para auxiliar operadores e gestores no registro, análise, diagnóstico e resolução de ocorrências industriais.</p>

<div class="steps" style="margin-bottom:14pt;">
  <div class="step">
    <div class="step-num">1</div>
    <div class="step-title">Registro da Ocorrência</div>
    <div class="step-text">Operador acessa a tela totem pública sem login complexo. Descreve a falha, seleciona a máquina, anexa foto e aponta o ponto no diagrama técnico.</div>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <div class="step-title">Análise por IA</div>
    <div class="step-text">Motor de IA multimodal processa texto, imagem e diagrama simultaneamente. Gera causas prováveis e próximos passos recomendados em tempo real.</div>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <div class="step-title">Gestão Técnica</div>
    <div class="step-text">Supervisor recebe a ocorrência no painel, complementa o diagnóstico, atribui responsável, registra ações tomadas e encerra com a solução adotada.</div>
  </div>
  <div class="step">
    <div class="step-num">4</div>
    <div class="step-title">Dashboard e Relatórios</div>
    <div class="step-text">Gestor acompanha KPIs em tempo real: número de ocorrências, tempo médio de resolução, máquinas críticas e causas mais frequentes.</div>
  </div>
  <div class="step">
    <div class="step-num">5</div>
    <div class="step-title">Base de Conhecimento</div>
    <div class="step-text">O acúmulo de ocorrências e resoluções cria memória técnica institucional para melhoria contínua e treinamento de novos operadores.</div>
  </div>
</div>

<div style="display:flex;gap:10pt;">
  <div style="flex:1;">
    <h3>Módulos da Plataforma</h3>
    <ul>
      <li>Tela totem pública para registro de ocorrências</li>
      <li>Painel administrativo (dashboard) para gestores</li>
      <li>Cadastro e gestão de máquinas e equipamentos</li>
      <li>Upload e gestão de diagramas técnicos</li>
      <li>Motor de análise por IA multimodal</li>
      <li>Histórico de ocorrências com filtros avançados</li>
      <li>Módulo de relatórios e KPIs exportáveis</li>
      <li>Chat com assistente de IA para suporte técnico</li>
      <li>Sistema de notificações e alertas</li>
    </ul>
  </div>
  <div style="flex:1;">
    <h3>Stack Tecnológico Atual</h3>
    <table>
      <thead><tr><th>Camada</th><th>Tecnologia</th></tr></thead>
      <tbody>
        <tr><td>Backend</td><td>Python, Flask, Flask-Login</td></tr>
        <tr><td>Banco de Dados</td><td>SQLite → PostgreSQL</td></tr>
        <tr><td>IA</td><td>Google Gemini Multimodal</td></tr>
        <tr><td>Frontend</td><td>Jinja2, CSS, JavaScript</td></tr>
        <tr><td>Infraestrutura</td><td>Cloud (AWS/GCP/Azure)</td></tr>
        <tr><td>Segurança</td><td>LGPD, OWASP, HTTPS/TLS</td></tr>
      </tbody>
    </table>
  </div>
</div>

<h2>Grau de Inovação</h2>
<div style="display:flex;gap:9pt;flex-wrap:wrap;">
  <div class="mini-card">
    <div class="mini-card-title">IA Multimodal Industrial</div>
    <div class="mini-card-text">Processamento simultâneo de texto, imagem e diagrama técnico para diagnóstico de falhas — inexistente em CMMS tradicionais acessíveis a PMEs.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Análise de Diagramas</div>
    <div class="mini-card-text">A IA interpreta diagramas de engenharia e identifica regiões de relevância a partir da falha descrita — funcionalidade inédita no segmento nacional.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">QRQC Digitalizado</div>
    <div class="mini-card-text">A metodologia QRQC — usada em indústrias automotivas globais — não possui solução digital dedicada com IA no mercado brasileiro. O Nexar preenche essa lacuna.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Apoio em Tempo Real</div>
    <div class="mini-card-text">A tela totem pública e o diagnóstico imediato da IA democratizam o acesso à gestão industrial — sem barreiras de login ou conhecimento técnico avançado.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Memória Técnica</div>
    <div class="mini-card-text">Gera ativo intelectual valioso: histórico estruturado de ocorrências e resoluções que não depende de pessoas específicas e cresce com o uso.</div>
  </div>
  <div class="mini-card">
    <div class="mini-card-title">Tecnologia Amazônica</div>
    <div class="mini-card-text">Desenvolvida integralmente em Manaus por equipe local, com potencial de escala nacional e para mercados latino-americanos.</div>
  </div>
</div>
<div class="hl" style="margin-top:12pt;">
  <strong>Nível de Prontidão Tecnológica (TRL)</strong>
  <p style="margin-top:5pt;">Situação atual: <strong>TRL 4–5</strong> (tecnologia validada em laboratório / MVP funcional). Meta ao final do projeto: <strong>TRL 7</strong> (protótipo demonstrado e validado em ambiente operacional industrial real).</p>
</div>
""", "Descrição da <span class='accent'>Solução e Inovação</span>")

# ════════════════════════════════════════
# PÁG 6 — METODOLOGIA
# ════════════════════════════════════════
p6 = page(f"""
<p>O projeto será executado em <strong>oito fases sequenciais e parcialmente sobrepostas</strong>, ao longo de 12 meses, com metodologia ágil (Scrum adaptado), revisões mensais de progresso e entregas incrementais verificáveis.</p>

<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 1</div>
    <div class="phase-title">Diagnóstico e Planejamento Detalhado</div>
    <div class="phase-period">Meses 1–2</div>
  </div>
  <div class="phase-text">Revisão da arquitetura atual, mapeamento de gaps técnicos, levantamento de requisitos com usuários industriais, definição de prioridades de desenvolvimento e seleção das empresas candidatas ao piloto. <em>Entrega: Documento de Planejamento Técnico.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 2</div>
    <div class="phase-title">Aprimoramento Técnico da Plataforma</div>
    <div class="phase-period">Meses 2–5</div>
  </div>
  <div class="phase-text">Migração para PostgreSQL, refatoração do backend, implementação de segurança (LGPD, OWASP), implantação em infraestrutura cloud e configuração de ambientes de desenvolvimento, homologação e produção. <em>Entrega: Plataforma em cloud com BD migrado.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 3</div>
    <div class="phase-title">Aprimoramento dos Modelos de IA</div>
    <div class="phase-period">Meses 2–6</div>
  </div>
  <div class="phase-text">Refinamento de prompts multimodais, expansão do corpus de diagramas industriais, desenvolvimento de métricas de avaliação, mecanismo de feedback do usuário e exploração de RAG para domínios específicos. <em>Entrega: Modelo de IA com métricas documentadas.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 4</div>
    <div class="phase-title">Redesign de Interface e UX</div>
    <div class="phase-period">Meses 3–6</div>
  </div>
  <div class="phase-text">Pesquisa com usuários, prototipação, redesign da tela totem e painel administrativo, testes de usabilidade com operadores e implementação das melhorias aprovadas. <em>Entrega: Interface aprovada em testes de usabilidade.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 5</div>
    <div class="phase-title">Desenvolvimento do Módulo de Relatórios</div>
    <div class="phase-period">Meses 4–7</div>
  </div>
  <div class="phase-text">Levantamento de KPIs industriais relevantes, desenvolvimento de dashboards interativos, exportação PDF/Excel e análises comparativas por período, máquina e tipo de falha. <em>Entrega: Módulo de relatórios funcional e testado.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 6</div>
    <div class="phase-title">Testes Internos e Controle de Qualidade</div>
    <div class="phase-period">Meses 6–8</div>
  </div>
  <div class="phase-text">Testes funcionais completos, testes de carga e performance, testes de segurança (penetration testing básico), correção de bugs e homologação da versão candidata ao piloto. <em>Entrega: Relatório de testes e versão piloto aprovada.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 7</div>
    <div class="phase-title">Validação Piloto em Ambiente Industrial</div>
    <div class="phase-period">Meses 8–11</div>
  </div>
  <div class="phase-text">Implantação em 2+ empresas industriais parceiras, treinamentos, acompanhamento presencial, coleta de métricas reais e iteração de melhorias a partir do feedback. <em>Entrega: Relatório de validação piloto com métricas.</em></div>
</div>
<div class="phase">
  <div class="phase-header">
    <div class="phase-num">Fase 8</div>
    <div class="phase-title">Documentação, PI e Preparação Comercial</div>
    <div class="phase-period">Meses 10–12</div>
  </div>
  <div class="phase-text">Documentação técnica completa, registro de software no INPI, elaboração de material comercial (pitch deck, landing page), modelo de precificação e relatório final. <em>Entrega: Pacote completo de documentação e material comercial.</em></div>
</div>
""", "Metodologia de <span class='accent'>Execução</span>")

# ════════════════════════════════════════
# PÁG 7 — CRONOGRAMA
# ════════════════════════════════════════
p7 = page(f"""
<p style="margin-bottom:12pt;">Cronograma mensal das principais atividades ao longo dos 12 meses de execução do projeto.</p>
<table style="font-size:8pt;">
  <thead>
    <tr>
      <th style="width:38%;">Atividade</th>
      <th>M1</th><th>M2</th><th>M3</th><th>M4</th><th>M5</th><th>M6</th>
      <th>M7</th><th>M8</th><th>M9</th><th>M10</th><th>M11</th><th>M12</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Diagnóstico e planejamento técnico</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Seleção de empresas piloto</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Migração banco de dados (PostgreSQL)</td><td></td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Infraestrutura cloud</td><td></td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Segurança / LGPD / OWASP</td><td></td><td></td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Aprimoramento modelos de IA</td><td></td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Métricas e feedback de IA</td><td></td><td></td><td></td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Pesquisa de usuários (UX Research)</td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Redesign de interface / tela totem</td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Testes de usabilidade</td><td></td><td></td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Módulo de relatórios e KPIs</td><td></td><td></td><td></td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Testes internos / QA completo</td><td></td><td></td><td></td><td></td><td></td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td style="color:{BLUE};font-weight:900;text-align:center;">■</td><td></td><td></td><td></td><td></td></tr>
    <tr><td>Implantação piloto — Empresa 1</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td></td><td></td></tr>
    <tr><td>Implantação piloto — Empresa 2</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td></td></tr>
    <tr><td>Coleta de métricas e ajustes piloto</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td style="color:{GREEN};font-weight:900;text-align:center;">■</td><td></td></tr>
    <tr><td>Documentação técnica</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td></tr>
    <tr><td>Registro de software (INPI)</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td></td></tr>
    <tr><td>Material comercial / go-to-market</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td><td style="color:{ORANGE};font-weight:900;text-align:center;">■</td></tr>
    <tr><td><strong>Relatório final / prestação de contas</strong></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td style="color:{RED};font-weight:900;text-align:center;">■</td></tr>
  </tbody>
</table>
<div style="display:flex;gap:14pt;margin-top:10pt;font-size:8pt;">
  <span><span style="color:{BLUE};font-weight:900;">■</span> Infraestrutura / Segurança / Relatórios</span>
  <span><span style="color:{GREEN};font-weight:900;">■</span> IA / Piloto</span>
  <span><span style="color:{ORANGE};font-weight:900;">■</span> UX / Documentação / PI</span>
  <span><span style="color:{RED};font-weight:900;">■</span> Encerramento</span>
</div>
""", "Cronograma de <span class='accent'>Execução — 12 Meses</span>")

# ════════════════════════════════════════
# PÁG 8 — ORÇAMENTO
# ════════════════════════════════════════
p8 = page(f"""
<table>
  <thead>
    <tr><th>#</th><th>Categoria de Despesa</th><th style="text-align:right;">Valor (R$)</th><th style="text-align:right;">%</th><th>Justificativa Resumida</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>1</strong></td><td><strong>Desenvolvimento de Software</strong></td><td style="text-align:right;color:{BLUE};">40.000,00</td><td style="text-align:right;">32%</td><td>Horas de desenvolvimento dos módulos de backend (Python/Flask), frontend e APIs. Inclui refatoração, novas funcionalidades, integrações e correções ao longo do projeto.</td></tr>
    <tr><td><strong>2</strong></td><td><strong>IA — Processamento e Modelos</strong></td><td style="text-align:right;color:{BLUE};">18.000,00</td><td style="text-align:right;">14,4%</td><td>Custos de API Google Gemini (tokens multimodais), experimentação com modelos alternativos, desenvolvimento de prompts especializados e implementação de RAG.</td></tr>
    <tr><td><strong>3</strong></td><td><strong>Infraestrutura Cloud</strong></td><td style="text-align:right;color:{BLUE};">15.000,00</td><td style="text-align:right;">12%</td><td>Servidores, banco de dados gerenciado PostgreSQL, armazenamento, CDN, SSL e balanceamento de carga durante os 12 meses do projeto.</td></tr>
    <tr><td><strong>4</strong></td><td><strong>Design UX/UI</strong></td><td style="text-align:right;color:{BLUE};">12.000,00</td><td style="text-align:right;">9,6%</td><td>Pesquisa de usuários, wireframes, prototipação, redesign das interfaces, testes de usabilidade com operadores industriais e design system documentado.</td></tr>
    <tr><td><strong>5</strong></td><td><strong>Segurança da Informação</strong></td><td style="text-align:right;color:{BLUE};">8.000,00</td><td style="text-align:right;">6,4%</td><td>Implementação de segurança (autenticação, criptografia), adequação à LGPD e OWASP, penetration testing básico e auditoria de vulnerabilidades.</td></tr>
    <tr><td><strong>6</strong></td><td><strong>Validação Piloto Industrial</strong></td><td style="text-align:right;color:{BLUE};">10.000,00</td><td style="text-align:right;">8%</td><td>Implantação nas empresas parceiras (deslocamentos, treinamentos, equipamentos para tela totem, acompanhamento presencial e coleta de dados de validação).</td></tr>
    <tr><td><strong>7</strong></td><td><strong>Documentação Técnica</strong></td><td style="text-align:right;color:{BLUE};">5.000,00</td><td style="text-align:right;">4%</td><td>Produção de documentação técnica: arquitetura, APIs, manual do administrador e manual do usuário em padrão auditável.</td></tr>
    <tr><td><strong>8</strong></td><td><strong>Propriedade Intelectual</strong></td><td style="text-align:right;color:{BLUE};">4.000,00</td><td style="text-align:right;">3,2%</td><td>Registro de programa de computador no INPI, assessoria jurídica especializada em PI de software e análise de proteção da solução de IA.</td></tr>
    <tr><td><strong>9</strong></td><td><strong>Gestão do Projeto</strong></td><td style="text-align:right;color:{BLUE};">8.000,00</td><td style="text-align:right;">6,4%</td><td>Coordenação executiva, reuniões de acompanhamento, ferramentas de gestão, comunicação com financiador e elaboração de relatórios mensais de progresso.</td></tr>
    <tr><td><strong>10</strong></td><td><strong>Relatórios e Prestação de Contas</strong></td><td style="text-align:right;color:{BLUE};">5.000,00</td><td style="text-align:right;">4%</td><td>Produção de relatórios técnicos e financeiros, auditoria interna dos gastos, organização de documentação comprobatória e relatório final de impacto.</td></tr>
    <tr style="background:{BLUE2};"><td colspan="2"><strong style="color:{WHITE};">TOTAL</strong></td><td style="text-align:right;"><strong style="color:{WHITE};font-size:11pt;">R$ 125.000,00</strong></td><td style="text-align:right;"><strong style="color:{WHITE};">100%</strong></td><td style="color:{MUTED};">Subvenção econômica não reembolsável</td></tr>
  </tbody>
</table>
<div class="hl" style="margin-top:14pt;">
  <strong>Nota sobre o Orçamento</strong>
  <p style="margin-top:6pt;">Os valores acima são estimativas baseadas em cotações de mercado local (Manaus/AM) e nacional. Poderão ser ajustados conforme as exigências específicas do edital e o detalhamento do plano de trabalho aprovado. A maior parcela do investimento (32%) está alocada em desenvolvimento de software — o ativo central do projeto — com a segunda maior parcela destinada ao aprimoramento da IA (14,4%), refletindo a natureza deep tech da solução.</p>
</div>
""", "Orçamento Estimado — <span class='accent'>R$ 125.000,00</span>")

# ════════════════════════════════════════
# PÁG 9 — RESULTADOS + INDICADORES
# ════════════════════════════════════════
p9 = page(f"""
<div style="display:flex;gap:10pt;">
  <div style="flex:1;">
    <h2>Resultados Técnicos</h2>
    <ul>
      <li>Plataforma em infraestrutura cloud estável e de produção</li>
      <li>Modelo de IA com precisão ≥ 75% aprovada pelos usuários</li>
      <li>BD PostgreSQL com backup, segurança e escalabilidade</li>
      <li>Interface redesenhada com usabilidade ≥ 4,0/5,0</li>
      <li>Módulo com ≥ 10 indicadores de desempenho industrial</li>
      <li>Plataforma em conformidade com LGPD e OWASP</li>
      <li>Software registrado no INPI</li>
    </ul>
  </div>
  <div style="flex:1;">
    <h2>Resultados Comerciais</h2>
    <ul>
      <li>≥ 2 empresas industriais validadas como clientes piloto</li>
      <li>Modelo de negócios SaaS estruturado com precificação</li>
      <li>Material comercial completo (pitch, landing page)</li>
      <li>Pipeline inicial de clientes no PIM</li>
      <li>Relacionamento com FIEAM, CIEAM e SUFRAMA</li>
    </ul>
    <h2>Resultados Sociais</h2>
    <ul>
      <li>Fortalecimento de empresa de base tecnológica amazonense</li>
      <li>Geração/manutenção de empregos qualificados em TI em Manaus</li>
      <li>Contribuição para transformação digital das indústrias do PIM</li>
      <li>Referência local de IA industrial desenvolvida na Amazônia</li>
    </ul>
  </div>
</div>

<h2>Indicadores de Sucesso</h2>
<table>
  <thead><tr><th>Indicador</th><th>Meta</th><th>Verificação</th><th>Prazo</th></tr></thead>
  <tbody>
    <tr><td>Plataforma implantada em cloud</td><td>100% funcional</td><td>Relatório técnico de infraestrutura</td><td>Mês 5</td></tr>
    <tr><td>Migração para PostgreSQL</td><td>Concluída</td><td>Relatório técnico</td><td>Mês 4</td></tr>
    <tr><td>Taxa de aprovação da IA pelos usuários</td><td>≥ 75%</td><td>Formulário de avaliação nos pilotos</td><td>Mês 10</td></tr>
    <tr><td>Satisfação geral dos usuários</td><td>≥ 4,0 / 5,0</td><td>Questionário de satisfação</td><td>Mês 11</td></tr>
    <tr><td>Empresas industriais piloto</td><td>≥ 2 empresas</td><td>Termo de parceria + relatório piloto</td><td>Mês 11</td></tr>
    <tr><td>Ocorrências registradas nos pilotos</td><td>≥ 100</td><td>Exportação do banco de dados</td><td>Mês 11</td></tr>
    <tr><td>Usuários testadores treinados</td><td>≥ 15 pessoas</td><td>Lista de presença dos treinamentos</td><td>Mês 10</td></tr>
    <tr><td>Máquinas cadastradas nos pilotos</td><td>≥ 10 máquinas</td><td>Exportação do sistema</td><td>Mês 9</td></tr>
    <tr><td>Tempo médio de registro de ocorrência</td><td>≤ 3 minutos</td><td>Logs do sistema</td><td>Mês 10</td></tr>
    <tr><td>Módulos de relatório disponíveis</td><td>≥ 5 relatórios distintos</td><td>Demonstração do módulo</td><td>Mês 7</td></tr>
    <tr><td>Documentação técnica</td><td>100% concluída</td><td>Entrega do documento</td><td>Mês 12</td></tr>
    <tr><td>Registro de software no INPI</td><td>Protocolo emitido</td><td>Comprovante INPI</td><td>Mês 11</td></tr>
  </tbody>
</table>
""", "Resultados e <span class='accent'>Indicadores</span>")

# ════════════════════════════════════════
# PÁG 10 — IMPACTO + EQUIPE + RISCOS
# ════════════════════════════════════════
p10 = page(f"""
<div class="impact-grid">
  <div class="impact-card">
    <div class="impact-title">Ecossistema de Tecnologia Local</div>
    <ul style="font-size:8.5pt;"><li>Demonstra que é possível criar IA de ponta a partir de Manaus</li><li>Referência local de deep tech industrial para o ecossistema regional</li><li>Atrai investimentos e atenção para o setor de tecnologia amazonense</li></ul>
  </div>
  <div class="impact-card">
    <div class="impact-title">Transformação Digital do PIM</div>
    <ul style="font-size:8.5pt;"><li>Acelera a adoção de Indústria 4.0 nas empresas do polo</li><li>Solução acessível, nacional, com suporte local e em português</li><li>Aumenta produtividade e competitividade das indústrias instaladas</li></ul>
  </div>
  <div class="impact-card">
    <div class="impact-title">Empregos Qualificados</div>
    <ul style="font-size:8.5pt;"><li>Mantém e amplia postos de trabalho em IA, software e design no AM</li><li>Parcerias com UFAM, UEA e IFAM para bolsistas e formação de talentos</li><li>Diversificação da matriz econômica além da indústria tradicional</li></ul>
  </div>
  <div class="impact-card">
    <div class="impact-title">Sustentabilidade da Zona Franca</div>
    <ul style="font-size:8.5pt;"><li>Ferramentas que reduzem perdas contribuem para a viabilidade do PIM</li><li>Competitividade industrial sustenta empregos e arrecadação no estado</li><li>Inovação local fortalece o modelo ZFM como política de desenvolvimento</li></ul>
  </div>
</div>

<h2>Perfil da Equipe</h2>
<div class="team-grid">
  <div class="team-card">
    <div class="avatar">EJ</div>
    <div>
      <div class="team-name">Enzo Jimenez</div>
      <div class="team-role">CEO / Fundador</div>
      <div class="team-desc">Analista de Sistemas. Responsável pela visão estratégica de produto, definição de requisitos, relacionamento com parceiros industriais e interface com financiadores.</div>
    </div>
  </div>
  <div class="team-card">
    <div class="avatar">GF</div>
    <div>
      <div class="team-name">Given Fellipo S. Mourão</div>
      <div class="team-role">CTO / CFO</div>
      <div class="team-desc">Engenharia de software, arquitetura de sistemas, APIs, banco de dados e gestão financeira. Responsável técnico principal e pela gestão de custos do projeto.</div>
    </div>
  </div>
  <div class="team-card">
    <div class="avatar">LP</div>
    <div>
      <div class="team-name">Luma Portela Marinho</div>
      <div class="team-role">Designer / QA Tester</div>
      <div class="team-desc">Design de interfaces, UX Research e testes de qualidade. Responsável pelo redesign de interface, testes de usabilidade e controle de qualidade das entregas.</div>
    </div>
  </div>
  <div class="team-card">
    <div class="avatar">B</div>
    <div>
      <div class="team-name">Bolsistas / Colaboradores</div>
      <div class="team-role">A contratar — UFAM / UEA / IFAM</div>
      <div class="team-desc">Desenvolvedores juniores e estagiários a incorporar via parcerias com universidades locais — apoio ao desenvolvimento, documentação, testes e suporte ao piloto.</div>
    </div>
  </div>
</div>

<h2>Riscos e Mitigação</h2>
<table style="font-size:8.5pt;">
  <thead><tr><th>Risco</th><th>Prob.</th><th>Impacto</th><th>Estratégia de Mitigação</th></tr></thead>
  <tbody>
    <tr><td>Dificuldade de acesso a indústrias piloto</td><td class="risk-med">Média</td><td class="risk-high">Alto</td><td>Mapeamento de parceiros na Fase 1 via CIEAM, FIEAM e SUFRAMA. Lista de ≥ 5 candidatas até o mês 6.</td></tr>
    <tr><td>Limitações de precisão da IA</td><td class="risk-med">Média</td><td class="risk-med">Médio</td><td>Métricas claras desde o início, mecanismo de feedback do usuário e postura conservadora: IA como suporte, não diagnóstico definitivo.</td></tr>
    <tr><td>Riscos de segurança / LGPD</td><td class="risk-low">Baixa</td><td class="risk-high">Alto</td><td>Security by Design, avaliação de vulnerabilidades por especialista externo e nenhum dado pessoal sensível sem consentimento.</td></tr>
    <tr><td>Resistência dos operadores à adoção</td><td class="risk-med">Média</td><td class="risk-med">Médio</td><td>Envolver operadores no design desde a fase UX, simplificar ao máximo a interface totem e realizar treinamentos presenciais.</td></tr>
    <tr><td>Custos cloud acima do previsto</td><td class="risk-low">Baixa</td><td class="risk-med">Médio</td><td>Monitoramento mensal de custos, alertas de orçamento, otimização de recursos e avaliação de provedores alternativos.</td></tr>
    <tr><td>Instabilidade da API de IA (Gemini)</td><td class="risk-low">Baixa</td><td class="risk-med">Médio</td><td>Camada de abstração na integração permite substituição de provedor sem reescrita. Avaliação de APIs alternativas como fallback.</td></tr>
  </tbody>
</table>
""", "Impacto, Equipe e <span class='accent'>Riscos</span>")

# ════════════════════════════════════════
# PÁG 11 — PITCH + VERSÃO COMERCIAL + CHECKLIST
# ════════════════════════════════════════
p11 = page(f"""
<h2>Pitch — 10 Linhas</h2>
<div class="pitch-box">
  <div class="pitch-text">
    Toda indústria convive com um problema invisível: o tempo perdido entre o momento em que uma máquina falha e o momento em que alguém realmente entende o que aconteceu. Esse gap custa dinheiro, produtividade e, às vezes, segurança. A <strong>Nexar Soluções Tecnológicas</strong>, empresa de base tecnológica amazonense, desenvolveu o <strong>Nexar QRQC</strong> — uma plataforma web que usa Inteligência Artificial multimodal para transformar o registro de uma ocorrência industrial em um processo inteligente, rápido e rastreável. O operador de chão de fábrica descreve a falha, anexa uma foto ou aponta o diagrama da máquina, e em segundos recebe da IA uma análise das possíveis causas e os próximos passos recomendados. Gestores têm dashboard em tempo real, histórico completo e relatórios gerenciais. É a digitalização da metodologia QRQC com IA — desenvolvida em Manaus, para a indústria brasileira. Com o apoio de fomento à inovação, vamos validar o sistema no Polo Industrial de Manaus, refinar a IA e escalar comercialmente. Estamos construindo uma referência nacional de tecnologia industrial desenvolvida na Amazônia.
  </div>
</div>

<h2>Versão Comercial — Para Empresários e Gestores Industriais</h2>
<div class="hl" style="border-left-color:#3fd68f;">
  <p style="font-size:10.5pt;color:{LIGHT};line-height:1.75;font-style:italic;">"Você já parou para calcular quanto custa, por hora, uma máquina parada na sua linha de produção?"</p>
  <p style="margin-top:8pt;">Imagine que, quando um operador identifica um problema, ele não precisa esperar o técnico chegar, não precisa ligar para ninguém e não precisa procurar o manual. Ele abre uma tela, descreve o problema em linguagem normal, tira uma foto — e em segundos recebe uma análise inteligente com as prováveis causas e o que fazer.</p>
  <p>Isso é o <strong>Nexar QRQC</strong>. Uma plataforma desenvolvida aqui em Manaus que usa Inteligência Artificial para ajudar sua equipe a identificar, registrar e resolver falhas de máquinas mais rápido. Sem papelada. Sem depender da memória de um técnico específico. Com tudo registrado, rastreável e disponível para você como gestor em tempo real.</p>
  <p>Com o tempo, o sistema acumula o histórico de tudo que já aconteceu nas suas máquinas — criando uma base de conhecimento que pertence à sua empresa. Estamos em fase de piloto com empresas do Polo Industrial de Manaus. A demonstração é gratuita e sem compromisso.</p>
</div>

<h2>Checklist — Documentos para Submissão a Editais</h2>
<div style="display:flex;gap:14pt;">
  <div style="flex:1;">
    <div class="checklist-title">Documentos Institucionais</div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">CNPJ ativo — Certidão de situação cadastral</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Contrato Social / Requerimento de Empresário</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">CND Federal (Receita Federal)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">CND Estadual (SEFAZ-AM)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">CND Municipal (Prefeitura de Manaus)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Certidão de Regularidade do FGTS</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Declaração de ME/EPP — Simples Nacional</div></div>

    <div class="checklist-title" style="margin-top:10pt;">Documentos Técnicos</div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Plano de Trabalho completo (este documento)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Cronograma no formato exigido pelo edital</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Orçamento com cotações de mercado anexadas</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Memorial descritivo da solução tecnológica</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Capturas de tela / vídeo demonstrativo do MVP</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Análise de mercado e de concorrência</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Carta de Intenção de empresa industrial parceira</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Currículo da equipe (Lattes CNPq)</div></div>
  </div>
  <div style="flex:1;">
    <div class="checklist-title">Documentos Financeiros</div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Extrato bancário dos últimos 3 meses (conta PJ)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Balanço patrimonial ou declaração de faturamento</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Declaração de capital social e composição societária</div></div>

    <div class="checklist-title" style="margin-top:10pt;">Documentos Complementares</div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Declaração de ausência de outras subvenções para o mesmo objeto</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Declaração de inexistência de impedimentos legais</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Formulário de empresa inovadora (conforme edital)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Registro de software no INPI (ou protocolo)</div></div>

    <div class="checklist-title" style="margin-top:10pt;">Materiais de Apoio</div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Pitch deck (10–15 slides) — apresentação visual</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Vídeo demonstrativo do MVP (2–5 minutos)</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Landing page do produto</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">One-pager executivo do projeto</div></div>
    <div class="checklist-item"><div class="checkbox"></div><div class="checklist-text">Carta de apresentação institucional da Nexar</div></div>
  </div>
</div>

<div class="cta">
  <div class="cta-title">Vamos construir juntos.</div>
  <div class="cta-rule"></div>
  <div class="cta-sub">Tecnologia · Inovação · Sustentabilidade</div>
  <div class="cta-email">Nexarsolucoestec@gmail.com</div>
  <div style="font-size:8pt;color:{DARK};margin-top:7pt;letter-spacing:1px;">NEXAR Soluções Tecnológicas — Manaus, AM / 2026</div>
</div>
""", "Pitch, Versão Comercial e <span class='accent'>Checklist</span>")

# ════════════════════════════════════════
# MONTAR HTML
# ════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Nexar QRQC — Projeto de Captação 2026</title>
<style>{CSS_GLOBAL}</style>
</head>
<body>
{cover}
{p2}
{p3}
{p4}
{p5}
{p6}
{p7}
{p8}
{p9}
{p10}
{p11}
</body>
</html>"""

output = "/home/user/Nexar-QRQC/Nexar_QRQC_Projeto_Captacao.pdf"
print("Gerando PDF...")
HTML(string=html).write_pdf(output, stylesheets=[CSS(string="@page{size:A4;margin:0;}")])
print(f"PDF gerado: {output}")
