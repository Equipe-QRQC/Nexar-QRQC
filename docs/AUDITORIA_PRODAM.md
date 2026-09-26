# Auditoria Nexar QRQC — preparação para apresentação ao PRODAM

**Data da auditoria:** 26/09/2026 (sábado) · **Apresentação:** terça-feira, 29/09/2026
**Escopo:** todo o repositório — backend Flask (`app.py`, `nexa_ia.py`, `sensor_visual.py`), 16 templates web, CSS/JS e o app Flutter (`qrqc-mobile/`).
**Método:** leitura integral do código e execução real do sistema em navegador headless (Chromium), em desktop (1440×900) e mobile (390×844), percorrendo todos os fluxos com banco limpo e sem chaves de IA.

Itens marcados com **[verificado]** foram reproduzidos rodando o sistema. Os demais foram identificados na leitura do código, com arquivo e linha.

Legenda de prioridade:
🔴 **CRÍTICO**: corrigir antes da apresentação ·
🟠 **IMPORTANTE**: deveria ser corrigido antes da apresentação ·
🟡 **MELHORIA**: importante para a evolução do produto ·
🟢 **FUTURO**: próxima versão

---

## Status das correções (atualizado em 26/09/2026)

**Corrigido e verificado no navegador** (32 verificações automatizadas em desktop e mobile, sem erros de JavaScript; 25/25 testes unitários):
S1, S2, S3 (chave aleatória quando ausente + `ADMIN_PASSWORD`), S7, S8, S9 · O1 (PRG + página `/ocorrencia/<id>`), O2, O3, O4 (operador), O5, O7, O9 · H1, H2, H3, H7 (ESC), confirmação ao resolver · D1, D2, D5, D6 · V1, V3 · Q1/Q2/Q3 (3D fora do menu, "beta" dentro da ocorrência), Q4 · X1 (texto), X2, X3, X6, X7, X8 (PT fixo; `ENABLE_I18N=1` reativa), X9 · MB1, MB2, MB10 · seção 4.3 (bibliotecas em `static/vendor/`) · A1 (`.env.example` + README), A3, A6 · parte de A10 (arquivos mortos removidos) · emojis de status removidos (Dashboard, Histórico, formulário, PDF).
Bug extra encontrado e corrigido: a página de Análise rodava o script dos gráficos duas vezes (bloco `scripts` aninhado dentro de `content`).

**Segunda rodada — corrigido e verificado** (mais 29 verificações no navegador sobre a base de demonstração, sem erros de JavaScript):
H4/UX-5 (resolução com solução aplicada + componente, gravadas e usadas no prompt da IA), H5 (Iniciar atendimento), H9/UX-7 (toast), V2 (ocorrência a partir da inspeção, com máquina, descrição, impacto e setor pré-preenchidos), V4 (rótulo "Validar laudo"), O4 (setor pela máquina), O11 (diagrama em PDF vira link), S4 (uploads exigem login ou token mobile), S10 (logout mobile revoga o token), S12 parcial (nome do operador não é mais enviado à IA), AP1 (ocorrência do app recebe operador, setor e diagnóstico em segundo plano), MB3 (tabelas viram cards no celular), MB6 (modal em tela cheia no celular), resolução no PDF da ocorrência e `scripts/seed_demo.py` (base de demonstração).

**Pendente:** S5/S6 (perfis e cadastro de usuários), MB4 (filtros recolhíveis no celular), AP2–AP4 (app Flutter), página de máquina (M1/M2), paginação no servidor (H8), demais itens 🟡/🟢.

---

## 0. Resumo executivo

O Nexar QRQC tem um **núcleo de valor real e demonstrável**. O operador registra uma ocorrência, a IA devolve um diagnóstico técnico estruturado e marca no diagrama da máquina os componentes suspeitos. Também existe o **Sensor Visual**, que analisa a foto de um equipamento e devolve anomalias localizadas e um índice de saúde. Os dois fluxos funcionam de ponta a ponta e ambos geram PDF.

O sistema ainda está em **fase de protótipo avançado**, com três tipos de problema que um órgão público de TI vai notar rapidamente:

1. **Segurança visível.** As credenciais de administrador aparecem impressas na tela de login. Há uma falha de XSS armazenado que confirmei executando o sistema, a chave de sessão tem valor padrão no código e os arquivos enviados ficam acessíveis sem login.
2. **Quebras visíveis na demo.** Um filtro sem resultados mostra todos os registros. Dashboard e Histórico ficam quebrados no celular. O PDF dá erro 500 com certos textos. Com a rede restrita, a interface perde todos os ícones, os gráficos e o 3D, porque depende de CDN externo. A mensagem "Configure GEMINI_API_KEY no .env" aparece para o usuário final.
3. **Promessas que o produto ainda não cumpre.** O selo "ISO 9001" aparece na tela inicial. O "QRQC 3D AI" usa um modelo 3D genérico marcado como "MODELO DEMO". O "aprendizado" da IA depende de um campo que o sistema nunca preenche. Existe um seletor de idioma EN/ES que traduz só metade das telas.

**Recomendação central para terça:** apresentar o sistema como um **piloto focado em um único fluxo principal**: *registrar ocorrência → diagnóstico com IA → acompanhar → resolver registrando a solução → indicadores*. O Sensor Visual entra como segundo destaque. O 3D fica marcado como "beta" ou fora do roteiro. As correções 🔴 levam em torno de **1 a 1,5 dia de trabalho** e estão listadas na seção 7.

---

## 1. Entendimento do sistema

### 1.1 Objetivo e problema resolvido
QRQC (*Quick Response Quality Control*) é uma metodologia industrial de resposta rápida a problemas no chão de fábrica: detectar, registrar, conter, analisar a causa e resolver. O Nexar QRQC digitaliza esse ciclo e acrescenta **IA como engenheiro de manutenção virtual**. A cada ocorrência registrada, a IA sugere causa provável, componentes a verificar, procedimento de inspeção com LOTO e critérios para escalar ao fabricante.

O problema atacado é o **tempo de diagnóstico** e a **perda de conhecimento**: hoje a solução de uma falha fica na cabeça do técnico mais experiente, ou em papel.

### 1.2 Usuários (inferidos do código)
| Perfil | O que faz no sistema | Onde |
|---|---|---|
| **Operador** (chão de fábrica) | Registra ocorrência, fotografa o equipamento (Sensor Visual), consulta o diagnóstico | Web (totem/tablet) e app Flutter |
| **Técnico de manutenção** | Lê o diagnóstico, inspeciona e marca como resolvida | Web |
| **Supervisor / Qualidade** | Acompanha dashboard e análise (Pareto), exporta Excel e PDF | Web |
| **Administrador** | Cadastra máquinas e diagramas | Web |

A tabela `usuarios` tem a coluna `perfil` (`admin`/`operador`), mas **nenhuma rota verifica o perfil**. Na prática todos podem tudo, e não há tela para cadastrar usuários.

### 1.3 Módulos existentes

| Módulo | Rota | Estado real |
|---|---|---|
| Tela de totem | `/` | Pronto (decorativo) |
| Login | `/login` | Funciona, com problemas de segurança |
| Dashboard | `/dashboard` | Funciona; sobrepõe-se à Análise |
| Nova ocorrência + diagnóstico IA | `/CadastroOcorrencia` → `/registrar_ocorrencia` | **Núcleo do produto. Pronto para uso**, com ajustes |
| Histórico + modal + resolver + Excel + PDF | `/historico` | Funciona, com bugs sérios (filtro, XSS, datas) |
| Máquinas (cadastro/edição + diagramas) | `/maquinas` | Básico: sem exclusão, sem gerenciar diagramas, sem página de detalhe |
| Sensor Visual (foto → anomalias → laudo PDF) | `/sensor`, `/sensor/historico` | **Pronto para demo** (depende da chave OpenAI) |
| Análise (Pareto, por tipo, por impacto) | `/analise` | Funciona se o Chart.js carregar do CDN |
| QRQC 3D AI (agente com ferramentas + modelo 3D) | `/qrqc3d/<id>` | **Protótipo.** O modelo 3D é um procedural genérico igual para toda máquina; os componentes não têm tela de cadastro |
| Assistente (chat flutuante) | `/chat` | Funciona; genérico, não conhece o contexto da tela |
| Solicitar suporte (ticket + e-mail) | `/suporte` → `/enviar` | Grava o ticket, mas **não existe tela para vê-lo** |
| API mobile + app Flutter | `/api/mobile/*`, `qrqc-mobile/` | Funcional; a ocorrência criada pelo app não recebe diagnóstico da IA |
| Idiomas PT/EN/ES | `/lang/<x>` | Parcial: Sensor, Dashboard, Suporte, Análise e 3D têm textos fixos em PT |

### 1.4 Como os módulos se relacionam (hoje)
```
Máquina (+diagramas) ──┬──> Ocorrência ──> Diagnóstico IA (Gemini) + marcações no diagrama
                       │         │
                       │         ├──> Histórico ──> Resolver (só troca status)
                       │         │               └─> QRQC 3D (OpenAI, agente com ferramentas)
                       │         └──> Dashboard / Análise / Excel / PDF
                       └──> Sensor Visual (OpenAI Vision) ──> Laudo PDF      ✗ não gera ocorrência
Suporte (ticket) ──> e-mail                                                   ✗ sem tela de consulta
Chat ──> Gemini                                                               ✗ sem contexto
```
**Elos faltantes:** a inspeção do Sensor Visual não vira ocorrência; resolver a ocorrência não registra a solução aplicada, o que quebra o "aprendizado"; o ticket de suporte não tem ligação com a ocorrência.

### 1.5 Fluxo ideal de ponta a ponta (proposto)
1. **Operador** abre o app ou a web → **Nova ocorrência**. Escolhe a máquina; setor e operador vêm preenchidos. Descreve o problema e, opcionalmente, anexa uma foto.
2. **IA** devolve o diagnóstico em até ~15 s. Se houver foto, o Sensor Visual roda junto e as anomalias entram no diagnóstico.
3. A ocorrência entra como **Aberta** e o técnico a vê no painel **"Minhas pendências / Abertas por prioridade"**.
4. O **técnico** abre a ocorrência, muda para **Em andamento** e executa a inspeção sugerida.
5. O técnico **resolve** informando *solução aplicada* e *componente real* (obrigatórios). Esse dado alimenta a IA nas próximas ocorrências da mesma máquina.
6. O **supervisor** acompanha em **Indicadores**: MTTR, abertas por idade, Pareto por máquina e tipo, taxa de recorrência. Exporta para Excel/PDF.

---

## 2. Auditoria funcional

### 2.1 Segurança e acesso

| # | Pri. | Problema | Onde | Correção |
|---|---|---|---|---|
| S1 | 🔴 | **Credenciais de administrador impressas na tela de login** ("Admin padrão: admin@nexar.com / nexar2026") | `templates/login.html:274` | Remover a linha. Trocar a senha do admin em todo ambiente de demo. |
| S2 | 🔴 | **XSS armazenado [verificado].** Um operador com nome `<img src=x onerror=...>` executa JavaScript quando alguém abre o modal no Histórico. Os campos máquina, operador e tipo, e o título/descrição das anotações da IA, entram via `innerHTML` | `templates/historico.html` (montagem de `modalChipsRow` e `listWrap`); `static/js/qrqc3d.js:387-405` (`renderHypotheses`, `renderActions` com texto da IA) | Usar `textContent` ou uma função `esc()` (já existe em `sensor.html`) em todo dado dinâmico. |
| S3 | 🔴 | **SECRET_KEY com valor padrão no código** (`"nexar-qrqc-secret-2026"`). Quem lê o repositório consegue forjar sessões | `app.py:48` | Exigir `SECRET_KEY` no ambiente e abortar a inicialização se estiver ausente. |
| S4 | 🟠 | **Arquivos enviados são públicos [verificado].** `/static/uploads/...` (diagramas, fotos do Sensor, anexos de suporte) retorna 200 **sem login** | `app.py:170,176,1949` | Mover os uploads para fora de `static/` e servi-los por uma rota com `@login_required`. |
| S5 | 🟠 | **Nenhum controle por perfil.** `perfil` existe e nunca é verificado; operador pode editar máquinas e cadastrar componentes | todas as rotas | Decorator `@requer_perfil('admin')` para máquinas, componentes e exportações. |
| S6 | 🟠 | **Sem tela de usuários.** O único usuário é o admin criado automaticamente; não há como cadastrar operadores sem SQL. **O PRODAM vai perguntar isso** | — | CRUD mínimo de usuários (admin), com troca de senha no primeiro acesso. |
| S7 | 🟠 | **Login web sem limite de tentativas** (só o login mobile tem `10/min`) | `app.py:648` | `@limiter.limit("5 per minute")` no `/login`. |
| S8 | 🟠 | E-mail de suporte monta HTML com dados do usuário sem escapar | `app.py:392-417` | `html.escape()` em cada campo. |
| S9 | 🟠 | Tamanho de upload ilimitado: a tela diz "máx. 10 MB", mas não existe `MAX_CONTENT_LENGTH` | `app.py` | `app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024` e handler 413 amigável. |
| S10 | 🟡 | Token mobile não é revogado no logout; o app permite HTTP sem TLS (`usesCleartextTraffic="true"`) | `app.py:2885`, `AndroidManifest.xml:15` | Rota `/api/mobile/logout`; HTTPS em produção. |
| S11 | 🟡 | Cookies de sessão sem `Secure`/`SameSite` explícitos | `app.py` | `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE="Lax"`. |
| S12 | 🟡 | **LGPD / soberania de dados:** fotos, descrições e nomes de operadores são enviados ao Google (Gemini) e à OpenAI. Um órgão público vai perguntar **onde os dados são processados** | `app.py`, `nexa_ia.py`, `sensor_visual.py` | Levar para a apresentação uma resposta pronta: dados enviados, retenção e alternativas (Azure OpenAI / Vertex AI em região Brasil, ou modelo local). Não enviar o nome do operador ao modelo. |

### 2.2 Nova ocorrência → diagnóstico (núcleo)

| # | Pri. | Problema | Onde | Correção |
|---|---|---|---|---|
| O1 | 🔴 | **F5 na tela de diagnóstico reenvia o formulário:** duplica a ocorrência e chama a IA de novo. O POST renderiza o template direto, sem Post/Redirect/Get | `app.py:1937` | Após salvar, `redirect(url_for('ver_ocorrencia', oc_id=...))` e criar a rota `GET /ocorrencia/<id>`, que também serve como página de detalhe permanente. |
| O2 | 🔴 | **Mensagens técnicas para o usuário final [verificado]:** "Configure GEMINI_API_KEY no .env", "Verifique sua chave Gemini nos logs", "Crie uma nova chave em outra conta Google" e o texto bruto de exceções (`f"Erro ao salvar: {e}"`) | `solucao.html:31-40`, `app.py:756,1057-1065,1922,2049,2617` | Mensagem única para o usuário ("Diagnóstico automático indisponível no momento. A ocorrência foi registrada e pode ser reanalisada.") e botão **Reanalisar**. Detalhes só no log. |
| O3 | 🟠 | **"Tipo" vem pré-selecionado como "Qualidade" [verificado]:** quem não escolhe grava Qualidade, o que distorce o Pareto | `CadastroOcorrencia.html:79` | Primeira opção vazia `— Selecione —` com `required`. |
| O4 | 🟠 | **Operador e setor são digitados à mão**, mesmo com o usuário logado e a máquina já tendo setor | `CadastroOcorrencia.html:43-58` | Pré-preencher operador com `current_user.nome` (editável) e setor com o da máquina ao selecioná-la. |
| O5 | 🟠 | **Data/hora vazia por padrão** e obrigatória; o operador sempre precisa preencher | idem:36 | Preencher com o momento atual. |
| O6 | 🟠 | **Máquina é opcional.** Sem máquina não há diagrama, histórico nem 3D, e a IA fica genérica | idem:26 | Tornar obrigatória, com a opção "Outro / não cadastrada" explícita. |
| O7 | 🟠 | **O botão "Limpar" não limpa Impacto e Recorrente** (são `div` com estado próprio) | idem:143 | Usar `input type=radio` estilizados (como em `suporte.html`); o reset nativo passa a funcionar. |
| O8 | 🟡 | O "loading" em quatro etapas é **simulado por timer**, não reflete o progresso real | idem:250-290 | Aceitável para a demo. No futuro, processamento assíncrono com status real. |
| O9 | 🟡 | "Cancelar" aponta para `/telaInicial` (rota legada que redireciona) | idem:141 | `url_for('dashboard')`. |
| O10 | 🟡 | A tela de diagnóstico não permite **resolver** nem **mudar status**; só leva a Histórico, PDF, Suporte ou Nova ocorrência | `solucao.html:12-27` | Na página de detalhe (O1), incluir ações de status. |
| O11 | 🟡 | Com o diagrama em PDF, a IA analisa o arquivo, mas a tela diz "Nenhum diagrama disponível" (só imagem gera `diagrama_url` útil) | `app.py:1842-1863` | Mostrar o link para o PDF. |
| O12 | 🟢 | IA síncrona dentro da requisição (duas chamadas, 10–40 s). Atrás de proxy com timeout de 30–60 s pode estourar | `app.py:1899` | Fila (RQ/Celery) + polling. |

### 2.3 Histórico

| # | Pri. | Problema | Onde | Correção |
|---|---|---|---|---|
| H1 | 🔴 | **Filtro sem resultado mostra TODOS os registros [verificado].** Com a busca "zzzznada", a tabela exibe as linhas e o contador diz "2 registro(s)" | `historico.html` `renderPagina()`: `linhasFiltradas.length ? linhasFiltradas : todasLinhas` | Usar sempre `linhasFiltradas` (inicializado com todas) e mostrar "Nenhum resultado para os filtros". |
| H2 | 🔴 | XSS no modal (ver S2) | — | — |
| H3 | 🟠 | **Data errada no modal [verificado]:** aparece "25 10:30/09/2026". O código trata `T`, mas a data é salva com espaço | `historico.html`, `dataRaw.replace(/T.+/,'')` | `dataRaw.slice(0,10).split('-').reverse().join('/')` + hora. |
| H4 | 🟠 | **Resolver não pede confirmação nem a solução aplicada.** Um clique e pronto. Com isso `solucao_aplicada` e `componente_real` **nunca são preenchidos**, e as ferramentas `get_previous_solutions` e `get_similar_occurrences` do agente devolvem sempre vazio: o "aprendizado" anunciado não acontece | `app.py:1733-1784`, `nexa_ia.py:73-103` | Modal de resolução com *Solução aplicada* (obrigatória) e *Componente real* (sugerido pela IA), gravando nos campos existentes. É a mudança de maior valor de produto por esforço. |
| H5 | 🟠 | Status "Em andamento" existe no filtro e nos badges, mas **não há como definir** | — | Botão "Iniciar atendimento" (Aberta → Em andamento). |
| H6 | 🟠 | Status "Fechada" no filtro, mas nenhum fluxo gera "Fechada" | `historico.html:62` | Remover do filtro ou definir: Resolvida (técnico) → Fechada (supervisor valida). |
| H7 | 🟡 | O modal não fecha com ESC nem prende o foco (acessibilidade) | — | Listener `keydown` e foco no primeiro botão. |
| H8 | 🟡 | Toda a tabela, com diagnósticos completos da IA em `data-*`, é renderizada de uma vez; a paginação é só no cliente | `app.py:1198`, `historico.html` | Paginação e filtros no servidor (`LIMIT/OFFSET`); modal busca `/api/ocorrencia/<id>`. |
| H9 | 🟡 | Erro ao resolver usa `alert()` nativo | `historico.html` | Toast padronizado. |

### 2.4 Dashboard e Análise

| # | Pri. | Problema | Correção |
|---|---|---|---|
| D1 | 🟠 | **Métricas inconsistentes entre telas.** O Dashboard conta "Abertas" como `status='Aberta'`; a Análise conta `status NOT IN ('Resolvida','Fechada')`, que inclui "Em andamento". Os números vão divergir na frente do cliente | Uma função única `kpis_ocorrencias()` usada pelas duas telas. |
| D2 | 🟠 | O rótulo "Alto Imp." significa, na verdade, "alto impacto **em aberto**" | Renomear para "Críticas em aberto". |
| D3 | 🟠 | **Dashboard e Análise duplicam conteúdo** (distribuição por tipo, KPIs) e nenhum traz o que um gestor QRQC quer: tempo de resposta, MTTR, abertas há mais de X dias, recorrência | Ver UX-2. |
| D4 | 🟠 | Análise sem filtro de período; tudo é "desde sempre" | Seletor de período: 7 dias / 30 dias / 90 dias / personalizado. |
| D5 | 🟡 | A coluna "IA" do Dashboard mostra ✓ / offline / erro, jargão técnico para o gestor | Remover a coluna. |
| D6 | 🟡 | "Quando" mostra `data_registro` (hora do servidor, UTC do SQLite) e não a data da ocorrência | Exibir `data_ocorrencia` no formato dd/mm/aaaa hh:mm. |

### 2.5 Máquinas

| # | Pri. | Problema | Correção |
|---|---|---|---|
| M1 | 🟠 | Sem **página de detalhe da máquina**: histórico de ocorrências, inspeções, diagramas e componentes 3D | Criar `/maquinas/<id>`, que vira o hub do ativo. |
| M2 | 🟠 | Não dá para **ver, trocar ou excluir diagramas** já enviados; a edição só adiciona | Lista de diagramas com "definir como principal" e "remover". |
| M3 | 🟡 | Não dá para desativar ou excluir uma máquina | Desativar (soft delete) em vez de excluir. |
| M4 | 🟡 | Upload com mesmo nome de arquivo sobrescreve o anterior no disco e duplica o registro no banco (`INSERT OR IGNORE` sem `UNIQUE`) | Prefixo aleatório no nome, como já é feito no Sensor. |
| M5 | 🟡 | O diagrama "principal" é escolhido por `ORDER BY tipo='PDF'`, sem controle do usuário | Coluna `principal`. |

### 2.6 Sensor Visual

| # | Pri. | Problema | Correção |
|---|---|---|---|
| V1 | 🔴 | **O status de IA está errado:** o badge "IA ativa" verifica o cliente **Gemini**, mas o Sensor usa **OpenAI**. Mostra "ativa" e falha, ou mostra "offline" e funciona | `app.py:1973`: `ia_online=nexa_ia._get_client() is not None`. |
| V2 | 🟠 | **A inspeção não vira ocorrência.** Detectada uma anomalia crítica, o usuário não tem para onde ir | Botão **"Abrir ocorrência a partir desta inspeção"**, que pré-preenche máquina, descrição (anomalias) e impacto (severidade). |
| V3 | 🟠 | O texto de abertura promete demais ("Sem sensores, sem hardware… o celular vira um sensor virtual… ensina o sistema") | Texto sóbrio: "Fotografe o equipamento. A IA aponta sinais visuais de falha e gera um laudo para apoiar a inspeção técnica." |
| V4 | 🟡 | Rótulo "Confirmar" é ambíguo: confirma o quê? | "Validar laudo" com opção "Discordo da IA", que registra o rótulo corrigido. |
| V5 | 🟡 | Erros via `alert()` | Mensagem inline no card de resultado. |
| V6 | 🟡 | A API mobile do Sensor não valida magic bytes (a web valida) | Reusar `content_is_valid`. |

### 2.7 QRQC 3D AI

| # | Pri. | Problema | Correção |
|---|---|---|---|
| Q1 | 🔴 | **É mockup:** o mesmo modelo procedural (motor, eixo, correia…) aparece para qualquer máquina, com selo "MODELO DEMO". Não há tela para cadastrar componentes (só API), então a IA recebe lista vazia e **não destaca nada** | Para terça: **tirar do menu principal** e deixar como botão "Visualização 3D (beta)" dentro da ocorrência, **só** para uma máquina de demonstração com componentes cadastrados via script. |
| Q2 | 🟠 | **O item de menu "QRQC 3D AI" leva ao Histórico** (a tela exige uma ocorrência); o usuário clica e cai em outra tela | Remover do menu (Q1). |
| Q3 | 🟠 | **Rótulo invisível [verificado]:** com o item ativo, o texto fica azul sobre fundo azul | Some com Q1/Q2. |
| Q4 | 🟠 | **Nome inconsistente:** "Nexa IA" (3D) versus "Nexar IA" (resto do sistema) | Padronizar para "Nexar IA". |
| Q5 | 🟡 | Os passos da "investigação" são animados com `sleep` artificial | Aceitável como beta. |

### 2.8 Suporte, Chat e demais

| # | Pri. | Problema | Correção |
|---|---|---|---|
| X1 | 🟠 | **Tickets são "write-only":** a mensagem de sucesso diz "visível na lista", mas **não existe lista** | Tela "Meus chamados" com status. Alternativa para terça: remover a frase. |
| X2 | 🟠 | O formulário aceita DOCX/XLSX, mas o backend **descarta em silêncio** (só aceita png/jpg/pdf) | Alinhar o `accept` com o backend ou aceitar os formatos no backend. |
| X3 | 🟠 | Nome e e-mail do solicitante não vêm preenchidos | Pré-preencher com `current_user`. |
| X4 | 🟡 | O tipo "Máquina CNC" no suporte é específico demais | "Equipamento". |
| X5 | 🟠 | **Chat:** não renderiza markdown (aparecem `**`), duplica a mensagem atual no histórico enviado ao modelo e não conhece a ocorrência aberta | Renderizar markdown com escape; enviar `historico[:-1]`; injetar o contexto da ocorrência quando o usuário estiver nela. |
| X6 | 🟠 | **O botão flutuante do chat cobre o botão "Alto" do formulário no celular [verificado]** | Esconder o FAB em telas de formulário no mobile, ou movê-lo para o menu. |
| X7 | 🔴 | **Totem exibe selo "ISO 9001"** sem certificação. Diante de um órgão público, isso é risco institucional | Remover. |
| X8 | 🟠 | **Idiomas parciais:** trocar para EN/ES deixa telas misturadas | Remover o seletor para o PRODAM (público 100% PT-BR) e manter o dicionário para o futuro. |
| X9 | 🔴 | **PDF da ocorrência dá erro 500 [verificado]** quando algum campo contém texto parecido com HTML (nome de máquina `<b>…</b>`, `<img…>`), porque o texto vai sem escape para o ReportLab. Emojis (🔴🟡🟢) também não existem na fonte Helvetica e saem como caixas | `app.py:1405-1730`, `2087-2338` | `xml.sax.saxutils.escape()` antes de aplicar `limpar()`; trocar emojis por texto e cor. |

### 2.9 Estados de tela

| Tela | Vazio | Carregando | Erro | Sucesso |
|---|---|---|---|---|
| Dashboard | ✅ tem | — | ❌ exceção = página 500 | — |
| Nova ocorrência | — | ✅ overlay (simulado) | ⚠️ `flash` com texto técnico | ⚠️ sem PRG (O1) |
| Histórico | ✅ tem / ❌ filtro vazio quebrado (H1) | — | ⚠️ `alert()` | ⚠️ badge atualizado, sem toast |
| Máquinas | ✅ tem | — | ⚠️ `flash` com exceção crua | ✅ `flash` |
| Sensor | ✅ tem | ✅ spinner | ⚠️ `alert()` | ✅ |
| Análise | ✅ tem | ❌ gráfico em branco se o CDN falhar | ❌ | — |
| 3D | ✅ tem | ✅ | ⚠️ canvas preto se o CDN falhar [verificado] | ✅ |
| Suporte | — | ✅ | ⚠️ `alert()` | ✅ protocolo |
| Toda a app | — | — | ❌ **não há páginas 404/500 próprias** | — |

---

## 3. Experiência do usuário (UX)

Premissa: um operador de chão de fábrica, em pé, com luva ou tablet, e um supervisor no desktop.

**UX-1. Reorganizar o menu de 9 para 6 itens, agrupados por tarefa.**
Hoje: Dashboard, Nova Ocorrência, Histórico, Máquinas, Sensor Visual, Análise, QRQC 3D AI, Solicitar Suporte, mais o seletor de idioma.
Proposto:
```
[ + Nova ocorrência ]        ← botão primário no topo do menu, não um item a mais
Painel                        (Dashboard)
Ocorrências                   (Histórico renomeado; o detalhe inclui 3D/PDF/Resolver)
Inspeção por foto             (Sensor Visual renomeado)
Máquinas
Indicadores                   (Análise renomeada)
─────────
Ajuda e suporte               (rodapé do menu, junto do usuário)
```
- **Remover "QRQC 3D AI" do menu** e incorporá-lo como aba ou botão "Visualização 3D" dentro do detalhe da ocorrência, porque ele só existe no contexto de uma ocorrência.
- **"Histórico" → "Ocorrências":** "histórico" sugere passado, mas é ali que o técnico trabalha as ocorrências abertas. O filtro padrão passa a ser **Status = Abertas + Em andamento**.
- **"Sensor Visual" → "Inspeção por foto":** o termo "sensor" confunde num ambiente com sensores físicos (IoT, CLP).
- **"Análise" → "Indicadores":** é o termo que o gestor usa.

**UX-2. Dashboard orientado à ação, não a contagens.**
Trocar "Distribuição por tipo" (já está em Indicadores) e "Ações rápidas" (duplicam o menu) por:
1. **"Requer atenção":** lista das ocorrências abertas ordenada por impacto e idade, com botão "Atender".
2. **KPIs com contexto:** Abertas (e quantas há mais de 48 h), Críticas em aberto, Resolvidas em 7 dias, Tempo médio de resolução.
3. **Máquinas com mais ocorrências no mês** (top 5).
Remover a saudação com emoji "Olá, Administrador 👋" ou trocar por "Bom dia, Maria · sexta, 29/09".

**UX-3. Uma página de detalhe da ocorrência** (`/ocorrencia/<id>`) substitui três coisas: a tela `solucao.html` (que só existe logo após o POST), o modal do Histórico e o acesso ao 3D. Estrutura: cabeçalho (nº, status, impacto, máquina) + ações (Iniciar atendimento / Resolver / PDF / 3D beta) → Dados → Diagnóstico IA → Diagrama anotado → Linha do tempo (criada, em andamento, resolvida por X com solução Y). O modal do Histórico vira só um link para essa página.

**UX-4. Formulário de ocorrência em uma coluna e na ordem natural:** Máquina → (setor preenchido automaticamente) → O que aconteceu (descrição) → Impacto → Tipo → É recorrente? → Detalhes técnicos (opcional, recolhido em "Adicionar detalhes técnicos"). Data/hora e operador vêm preenchidos numa linha discreta "Registrado por Maria em 26/09 14:32 · alterar". Ganho: menos campos visíveis e ordem igual ao raciocínio do operador.

**UX-5. Resolução com confirmação e registro de conhecimento** (ver H4). Modal: "Qual foi a solução aplicada?" (obrigatório), "Componente que falhou" (lista de sugestões da IA + texto livre) e botão "Confirmar resolução". Feedback: toast "Ocorrência #12 resolvida". Isso sustenta o discurso de que a IA aprende com a planta.

**UX-6. Linguagem.** Trocar:
| Hoje | Proposto |
|---|---|
| "IA offline — Configure GEMINI_API_KEY no .env" | "Diagnóstico automático indisponível. Tente reanalisar em alguns minutos." |
| "Fallback offline" / "Erro IA" (badges) | "Diagnóstico padrão" / "Não gerado" |
| "✨ Nexar IA" | "Gerado por Nexar IA" |
| "Alto Imp." | "Críticas em aberto" |
| "Percepção #12" (laudo) | "Inspeção nº 12" |
| "Confirmar" (Sensor) | "Validar laudo" |
| "Iniciar Análise Nexa IA" | "Analisar com Nexar IA" |

**UX-7. Confirmações e feedback.** Confirmar antes de: resolver, reanalisar (sobrescreve o diagnóstico 3D) e remover diagrama. Usar **um componente de toast** para sucesso e erro em todo o sistema, no lugar de `alert()` e `flash` com estilos inline diferentes.

---

## 4. Design — Web

### 4.1 Diagnóstico visual
**O que está bom:** existe um design system (`design-system.css`) com tokens de cor, raio, sombra e fonte Inter; sidebar escura com conteúdo claro; cards e tabelas limpos; hierarquia correta nos títulos de página. A base é aproveitável e **não precisa de redesign**, precisa de **disciplina e remoção de excessos**.

**O que parece protótipo, template ou pouco institucional:**
1. **Emojis como linguagem visual:** 🔴🟡🟢 nos badges de impacto, 👋 na saudação, ✨ no badge da IA, ⚠️ nas mensagens, 🔵 no select de tipo. Em sistema institucional, isso passa informalidade. Trocar por badge com ponto colorido (CSS) + texto.
2. **Paleta de destaque dispersa:** azul-céu primário, roxo em "Máquinas", amarelo em "Suporte", gradiente com brilho no "QRQC 3D AI", indigo para "Aberta" e verde-água para "Resolvida". Cada tela tem acentos próprios.
3. **Efeitos decorativos:** marcadores do diagrama com pulsação e brilho (`@keyframes pulse-*`), `translateY` no hover dos cards de máquina, gradiente e brilho no item de menu, animação de ripple no totem e névoa no 3D. Em conjunto, lembram demo de produto de consumo, não ferramenta de trabalho.
4. **Mais de 300 estilos inline** nos templates (`style="..."`: 47 no histórico, 46 na solução, 33 na análise…). É a causa das inconsistências de espaçamento e cor entre telas.
5. **O botão de recolher a sidebar** é um círculo branco solto na borda entre sidebar e conteúdo [verificado]; parece um elemento quebrado.
6. **Tela de totem** (`/`) com "Toque para iniciar": para acesso via navegador corporativo é uma etapa a mais. Manter só se houver totem físico.
7. **Tabela do dashboard** com 8 colunas, incluindo "IA" e "#": ruído para o gestor.
8. **Sem estados de foco visíveis** consistentes (acessibilidade e-MAG, relevante para órgão público).

### 4.2 Identidade visual proposta (sóbria / institucional)
Manter a marca Nexar (logo e navy) e reduzir o resto:

| Token | Valor | Uso |
|---|---|---|
| `--brand-navy` | `#0B1F3A` | Sidebar, cabeçalho de PDF e Excel |
| `--primary` | `#1D4ED8` (azul mais sóbrio que o `#0EA5E9` atual) | Botão primário, links, item ativo |
| `--primary-soft` | `#EFF4FF` | Fundo de item ativo, seleção |
| Neutros | `#0F172A` texto · `#475569` secundário · `#E2E8F0` borda · `#F8FAFC` fundo | Tudo o mais |
| Semânticas | Crítico `#B91C1C` · Atenção `#B45309` · OK `#047857` · Info `#1D4ED8` | **Somente** status/impacto/severidade, em badge: fundo 10% + texto 100% + ponto |

Regras:
- **Uma cor de ação** (primary). Cards de atalho sem cores próprias.
- **Status** sempre como `badge` com texto: Aberta (cinza-azulado), Em andamento (âmbar), Resolvida (verde), Fechada (cinza).
- **Tipografia:** Inter, escala fixa 12 / 13 / 14 (base) / 16 / 20 / 24; números de KPI em 28 com `font-variant-numeric: tabular-nums`; títulos em peso 600.
- **Espaçamento:** grade de 4 px; padding de card 20 px; gap de grid 16 px; raio 8 px em cards e 6 px em inputs e botões (hoje há 6/12/20).
- **Sombras:** só `--shadow-sm` em cards; sem elevação no hover (usar mudança de borda).
- **Ícones:** Font Awesome **auto-hospedado**, sempre acompanhado de texto no menu e nos botões principais.
- **Gráficos:** Chart.js auto-hospedado; paleta categórica derivada da primária (tons de azul) e cores semânticas só para impacto. Sem pizza/rosca para mais de 4 categorias; o Pareto por máquina está correto.
- **Diagrama anotado:** marcadores numerados com borda sólida, sem pulsação; destaque só no hover.
- **3D:** fundo claro neutro, sem névoa, para combinar com o restante (se mantido).

### 4.3 Dependência de CDN — 🔴 CRÍTICO [verificado]
Font Awesome (cdnjs), Chart.js (jsdelivr), Three.js e OrbitControls (cdnjs/jsdelivr) e Inter (Google Fonts) vêm de CDNs externos. **No meu ambiente de teste, com rede restrita, o sistema ficou sem nenhum ícone** (botões de sidebar e chat viraram círculos vazios), **a Análise sem gráficos e o 3D com o canvas preto.** Redes de órgãos públicos costumam ter proxy e filtro de conteúdo. **Baixar esses arquivos para `static/vendor/` antes de terça.**

---

## 5. Design — Mobile

### 5.1 Web responsiva
| # | Pri. | Problema | Correção |
|---|---|---|---|
| MB1 | 🔴 | **Dashboard e Histórico estouram a largura no celular [verificado]:** a página renderiza com 1066 px (dashboard) e 1269 px (histórico) numa tela de 390 px; o navegador reduz o zoom e tudo fica ilegível. Causa: `.main-content` é item flex sem `min-width: 0`, então a tabela empurra a largura da página e o `overflow-x: auto` do `.table-wrapper` nunca age | `design-system.css:269`: adicionar `min-width: 0;` em `.main-content`. |
| MB2 | 🔴 | **O botão de detalhes (👁) do Histórico não é clicável no celular [verificado]:** o topbar intercepta o toque | Sai junto com MB1; validar depois. |
| MB3 | 🟠 | **Tabelas no celular:** mesmo com scroll, oito colunas não funcionam | Abaixo de 768 px, renderizar **lista de cards**: linha 1 = máquina + badge de status; linha 2 = descrição (2 linhas); linha 3 = impacto · data. O card inteiro é clicável. |
| MB4 | 🟠 | **Filtros do Histórico** ocupam meia tela no celular (5 campos empilhados) | Busca visível + botão "Filtros (2)" que abre painel inferior. |
| MB5 | 🟠 | **FAB do chat sobrepõe controles** (ver X6) | Esconder em formulários no mobile. |
| MB6 | 🟠 | **Modal de detalhes** no celular: duas colunas viram uma, mas continua modal com rolagem interna | Abaixo de 640 px, levar à página de detalhe (UX-3) em vez de abrir modal. |
| MB7 | 🟡 | O KPI "Máquinas" fica sozinho numa linha (grade 2×2 + 1) | No mobile, mostrar 4 KPIs (2×2) e tirar "Máquinas". |
| MB8 | 🟡 | Em 390 px, os botões "Cancelar"/"Limpar" ficam abaixo de "Registrar" com peso visual parecido | "Registrar" fixo no rodapé (sticky); "Limpar" removido no mobile. |
| MB9 | 🟡 | Alvos de toque: botões `btn-sm` com cerca de 30 px de altura | Mínimo de 44 px em telas de toque. |
| MB10 | 🟡 | Análise com leve estouro (438 px) | Gráficos com `maintainAspectRatio:false` e altura fixa. |

**Prioridade de informação no celular (operador):**
1. Botão **Nova ocorrência** e **Inspeção por foto**: primeira dobra, grandes.
2. **Minhas ocorrências abertas** (cards).
3. Resultado do diagnóstico (texto primeiro; diagrama recolhível).
Ocultar ou recolher no celular: gráficos de Indicadores (link "ver no computador"), exportação Excel, cadastro de máquinas, 3D, coluna "IA", saudação.

### 5.2 App Flutter (`qrqc-mobile/`)
Estrutura correta: login com token Bearer, armazenamento seguro, telas de ocorrência, Sensor e resultado. Pontos:
| # | Pri. | Problema | Correção |
|---|---|---|---|
| AP1 | 🟠 | Ocorrência criada no app **não recebe diagnóstico da IA** nem operador/setor; aparece no web com "—" | O `POST /api/mobile/ocorrencias` deve reusar a mesma função de diagnóstico da web e gravar `nome_operador` do token. |
| AP2 | 🟠 | O app não anexa foto à ocorrência (só no Sensor) | Foto opcional na ocorrência, com o Sensor rodando junto. |
| AP3 | 🟠 | **"Inspeção de documento"** (auditoria de formulários por foto) é outro produto, fora do escopo QRQC | Esconder para terça; avaliar depois. |
| AP4 | 🟡 | A URL do servidor é digitada no login (`http://127.0.0.1:5000` como padrão) | Para a demo, fixar a URL do ambiente via build flavor e esconder o campo. |
| AP5 | 🟡 | Teste de widget é só smoke test | — |
| AP6 | 🟢 | Offline-first (registrar sem rede e sincronizar depois) é muito relevante no chão de fábrica | Próxima versão. |

---

## 6. Tecnologias e arquitetura

### 6.1 Inventário
| Camada | Tecnologia | Avaliação |
|---|---|---|
| Backend | Python 3.11 + Flask 3, Flask-Login, Flask-WTF (CSRF), Flask-Limiter | ✅ Adequado para o porte. Manter. |
| Templates | Jinja2 + HTML/CSS/JS puro | ✅ Adequado. **Não** há necessidade de React/Vue para este produto. |
| Banco | SQLite (`qrqc.db`, modo WAL) | ⚠️ Ok para demo e piloto de 1 unidade. Para produção multiusuário, PostgreSQL. |
| IA | **Dois provedores:** Google Gemini (diagnóstico, bounding boxes, chat) e **OpenAI GPT-4o** (Sensor, 3D/agente, documento mobile) | ⚠️ Ver 6.3. |
| PDF / Excel | ReportLab / openpyxl | ✅ Adequados. |
| 3D | Three.js r128 (2021) via CDN | ⚠️ Versão antiga; só se justifica se o 3D continuar. |
| Gráficos | Chart.js 4 via CDN | ✅ Adequado; auto-hospedar. |
| Mobile | Flutter (Android/iOS) | ✅ Adequado. |
| Servidor | `app.run()` (servidor de desenvolvimento do Flask) | ❌ Não usar em apresentação/produção: Waitress (Windows) ou Gunicorn (Linux) atrás de Nginx. |

**Conclusão: não é necessário trocar tecnologias.** As trocas recomendadas são pontuais: SQLite → PostgreSQL (produção), servidor de desenvolvimento → Gunicorn/Waitress, e unificar o provedor de IA.

### 6.2 Problemas de arquitetura
| # | Pri. | Problema | Correção |
|---|---|---|---|
| A1 | 🔴 | **Duas chaves de IA obrigatórias e README desatualizado.** O README fala só em Gemini, mas Sensor, 3D e mobile exigem `OPENAI_API_KEY` com crédito. Se faltar crédito na terça, metade das funcionalidades cai | Antes de terça: validar as duas chaves e o saldo; criar `.env.example`. Depois: um provedor só (ver 6.3). |
| A2 | 🟠 | **`app.py` monolítico com 3.168 linhas:** rotas, prompts, geração de PDF, Excel, e-mail, API mobile e traduções num arquivo só | Blueprints: `auth`, `ocorrencias`, `maquinas`, `sensor`, `relatorios`, `api_mobile`; `services/ia.py`, `services/pdf.py`; `i18n.py`. |
| A3 | 🟠 | **Caminho do banco relativo** (`sqlite3.connect("qrqc.db")` em `app.py:357` e `nexa_ia.py:35`): se o servidor for iniciado de outra pasta, cria um banco vazio **e o sistema "perde" os dados na frente do cliente** | Caminho absoluto baseado em `app.root_path` ou `DATABASE_URL`. |
| A4 | 🟠 | **Sem migrações:** `init_db()` com `ALTER TABLE` ad hoc; `mobile_tokens` criada em outro lugar | Flask-Migrate (Alembic) quando for para PostgreSQL. |
| A5 | 🟠 | **Conexões sem `try/finally`:** várias rotas fazem `conn = get_db()` e, em exceção, a conexão fica aberta (ex.: `/dashboard`, `/sensor`, `/maquinas`) | Context manager `with get_db() as conn` / `teardown_appcontext`. |
| A6 | 🟠 | **Testes quebrados:** `python test_sensor_visual.py` → **23/25 passam**. Os 2 que falham ainda simulam a API do Gemini, mas o Sensor migrou para OpenAI | Atualizar os mocks; adicionar testes de rota com `app.test_client()` para os fluxos 🔴. |
| A7 | 🟡 | Rate limiter em memória (`memory://`) zera a cada reinício e não funciona com vários processos | Redis em produção. |
| A8 | 🟡 | `f_err.log` cresce indefinidamente | `RotatingFileHandler`. |
| A9 | 🟡 | Sem health check nem página 404/500 própria | `/healthz` + `errorhandler(404/500)` com layout. |
| A10 | 🟡 | **Higiene do repositório:** arquivo `=1.2.0` (saída de `pip` salva por engano); propostas de captação (`Nexar_*.md/pdf`, `gerar_*_pdf.py`) na raiz; templates mortos (`Solicitação_Suporte.html`, `sucesso.html`); CSS mortos (`cadastro.css`, `historico.css`, `menu.css`, `telainicial.css`, `Solicitação_Suporte.css`); JS mortos (`historico.js`, `telainicial.js`); arquivos de exemplo em `static/uploads/maquinas/` versionados sem registro no banco. Se o PRODAM pedir acesso ao código, isso pesa | Remover ou mover para `docs/` e `legacy/`. |
| A11 | 🟡 | Dependência `openai` e `google-genai` + chaves; `twilio` citado no README, mas comentado no `requirements.txt` | Atualizar o README. |
| A12 | 🟢 | Sem Docker nem pipeline de CI | `Dockerfile` + GitHub Actions (lint + testes). |
| A13 | 🟢 | Autenticação local apenas | Integração LDAP/AD ou SSO corporativo (padrão em órgãos públicos). |

### 6.3 Provedor de IA — recomendação
Hoje o sistema usa **Gemini** para o diagnóstico e o chat e **OpenAI** para o Sensor e o agente 3D. Isso significa duas contas, duas faturas, dois pontos de falha e dois tratamentos de erro diferentes.
**Recomendação:** criar uma camada `services/ia.py` com uma interface única (`gerar_texto`, `analisar_imagem`, `detectar_caixas`, `agente_com_ferramentas`) e **escolher um provedor principal** pelo critério que mais pesa para o PRODAM: **onde os dados são processados e sob qual contrato**. Na prática: **Azure OpenAI** ou **Google Vertex AI** em região Brasil, contratáveis como serviço de nuvem por órgão público. Sai das chaves de "free tier", que o próprio sistema hoje orienta o usuário a contornar ("crie uma nova chave em outra conta Google"). **Para terça, não trocar nada**: só garantir que as duas chaves funcionam.

---

## 7. Plano de ação até terça-feira

### Sábado/domingo — bloqueadores (🔴), cerca de 1 a 1,5 dia
1. **Segurança visível:** remover as credenciais da tela de login (S1); `SECRET_KEY` obrigatória (S3); trocar a senha do admin; escapar XSS no Histórico e no 3D (S2).
2. **Bugs visíveis:** filtro vazio do Histórico (H1); PDF com escape e sem emoji (X9); Post/Redirect/Get na ocorrência + rota de detalhe (O1); badge de IA do Sensor (V1); data do modal (H3).
3. **Mobile web:** `min-width:0` em `.main-content` (MB1/MB2); esconder o FAB do chat nos formulários (X6).
4. **CDN:** auto-hospedar Font Awesome, Chart.js, Three.js e Inter (seção 4.3).
5. **Mensagens ao usuário:** remover toda referência a `.env`/chave/Gemini da interface (O2).
6. **Credibilidade:** remover "ISO 9001" (X7); tirar "QRQC 3D AI" do menu, deixando-o como "Visualização 3D (beta)" na ocorrência (Q1/Q2); remover o seletor EN/ES (X8); padronizar "Nexar IA" (Q4).
7. **Ambiente:** validar as chaves Gemini e OpenAI e o saldo; rodar com Waitress/Gunicorn; caminho absoluto do banco (A3).

### Segunda — importantes (🟠) de maior retorno na demo, cerca de 1 dia
8. Resolver com "solução aplicada" e confirmação (H4/UX-5): fecha o ciclo QRQC e dá sustentação ao discurso de aprendizado.
9. Formulário: tipo sem padrão, operador/data/setor pré-preenchidos, máquina obrigatória (O3–O6).
10. "Abrir ocorrência a partir da inspeção" no Sensor (V2).
11. KPIs consistentes e renomeados (D1/D2).
12. Trocar emojis de status por badges (4.1.1); remover pulsação e gradientes (4.1.3).
13. Suporte: remover "visível na lista", alinhar formatos, pré-preencher usuário (X1–X3).
14. **Popular uma base de demonstração realista:** 5 a 6 máquinas com diagramas (já existem em `test_diagrams/`), cerca de 30 ocorrências em 60 dias, com parte resolvida e *solução aplicada*, algumas recorrentes, e 5 inspeções do Sensor. Um dashboard vazio não convence.
15. **Ensaio completo** do roteiro em rede restrita (sem acesso a CDN) e no celular.

### Roteiro sugerido para a apresentação (≈15 min)
1. Problema: tempo de diagnóstico e perda de conhecimento técnico (1 min).
2. **Registrar uma ocorrência real** na prensa hidráulica → diagnóstico + diagrama anotado (4 min).
3. **Inspeção por foto** de um vazamento → laudo PDF → "abrir ocorrência" (3 min).
4. **Técnico resolve** registrando a solução → mostrar que a próxima ocorrência da mesma máquina cita a solução anterior (3 min).
5. **Indicadores** + exportação Excel (2 min).
6. Segurança e dados: onde roda, quem acessa, LGPD, próximos passos (2 min).

### Depois da apresentação (🟡/🟢)
Página de máquina; usuários e perfis; tela de chamados; paginação no servidor; blueprints; PostgreSQL + migrações; provedor de IA único em nuvem com contrato; IA assíncrona; Docker + CI; SSO/LDAP; app mobile offline-first; 3D com modelo real (GLB) por máquina.

---

## Anexo — evidências da execução
- Ambiente: cópia do repositório, banco novo, sem chaves de IA (caminho de fallback), Chromium headless.
- XSS: operador `<img src=x onerror="window.__xss=1">João` → ao abrir o modal do Histórico, `window.__xss === 1`.
- Filtro: busca "zzzznada" → 2 linhas visíveis, contador "2 registro(s)".
- PDF: `GET /ocorrencia/1/pdf` → **500** (`ValueError: paraparser: syntax error: invalid attribute name onerror`).
- Uploads: `GET /static/uploads/maquinas/1/diagrama_prensa_hidraulica.png` sem sessão → **200**.
- Mobile 390 px: `scrollWidth` = 1066 (`/dashboard`), 1269 (`/historico`), 438 (`/analise`); demais telas, 390.
- Mobile: clique no botão de detalhes do Histórico falha (elemento coberto pelo topbar).
- CDN bloqueado: ícones ausentes em todas as telas, gráficos da Análise vazios, canvas do 3D preto.
- Testes: `test_sensor_visual.py` → 23/25 (falham `test_detectar_fluxo_ok` e `test_detectar_sem_anomalia`).
