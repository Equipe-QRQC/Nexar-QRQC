# Nexar QRQC

Sistema de registro e resolução de ocorrências industriais com inteligência artificial. O operador registra um problema, a IA (**Gemini 2.0 Flash** com visão) gera um diagnóstico técnico passo a passo. A solicitação de suporte é enviada via WhatsApp pelo Twilio.

## Funcionalidades

- Cadastro de ocorrências com campos de setor, tipo, nível de impacto e detalhamento técnico
- Geração automática de diagnóstico via **Gemini 2.0 Flash** (gratuito até 1.500 req/dia)
- Análise de diagramas técnicos (PNG/JPG) via visão multimodal
- **Sensor Visual** — inspeção fotográfica de equipamentos com IA: detecta anomalias
  visuais (trinca, vazamento, corrosão, desalinhamento…), desenha bounding boxes e
  calcula o **Índice de Saúde** do ponto, sem qualquer hardware de sensoriamento
- Histórico completo de ocorrências com filtros e modal de detalhes
- Dashboard com KPIs, distribuição por tipo e últimas ocorrências
- Solicitação de suporte com envio de mensagem via WhatsApp (Twilio)

### Sensor Visual (percepção industrial aumentada)

Transforma a câmera de um celular num **sensor virtual**. O operador fotografa o
equipamento e a IA multimodal localiza anomalias físicas, classifica a severidade
(`crítico` / `atenção` / `info`) e pontua o estado do ponto de 0 a 100. Cada inspeção
confirmada pelo operador vira **dado rotulado** na tabela `percepcoes` — o dataset
proprietário que aumenta a precisão do modelo ao longo do tempo.

- Página: **Menu → Sensor Visual** (`/sensor`)
- Taxonomia de 16 classes de defeito em `sensor_visual.py`
- API: `POST /api/sensor/analisar` (foto → anomalias) e
  `POST /api/sensor/<id>/confirmar` (rotulagem)
- Testes da lógica pura: `python test_sensor_visual.py`

## Tecnologias

- **Python / Flask** — backend e rotas
- **SQLite** — banco de dados local (`qrqc.db`)
- **Google Generative AI** — Gemini 2.0 Flash (texto + visão)
- **Pillow** — processamento de imagens dos diagramas
- **Twilio** — envio de mensagens WhatsApp
- **HTML + CSS + JS** — frontend com templates Jinja2
- Bibliotecas de frontend (Font Awesome, Chart.js, Three.js, fonte Inter) auto-hospedadas em `static/vendor/` — o sistema funciona sem acesso a CDNs externos

## Pré-requisitos

- Python 3.10 ou superior
- Conta gratuita no [Google AI Studio](https://aistudio.google.com/apikey) para a chave Gemini
- (Opcional) Conta no [Twilio](https://www.twilio.com/) com WhatsApp Sandbox

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Equipe-QRQC/Nexar-QRQC.git
cd Nexar-QRQC

# 2. Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha. As principais:

| Variável | Obrigatória | Uso |
|---|---|---|
| `SECRET_KEY` | sim | Assinatura das sessões. Sem ela, uma chave temporária é gerada e os logins expiram a cada reinício. |
| `ADMIN_PASSWORD` | sim | Senha do administrador (aplicada a cada inicialização). |
| `GEMINI_API_KEY` | sim | Diagnóstico da ocorrência, marcações no diagrama e assistente. |
| `OPENAI_API_KEY` | sim | Sensor Visual, Visualização 3D e inspeção de documento (app mobile). |
| `SMTP_*`, `SUPORTE_EMAIL_*` | não | Envio de e-mail dos chamados de suporte. |

> O arquivo `.env` está no `.gitignore` e nunca deve ser commitado.

### Como obter a chave Gemini (grátis, sem cartão)

1. Acesse https://aistudio.google.com/apikey
2. Faça login com a conta Google
3. Clique em **"Create API key"**
4. Copie a chave e cole no `.env` como `GEMINI_API_KEY`

**Limites do free tier:**
- 15 requisições por minuto
- 1.500 requisições por dia
- 1 milhão de tokens por minuto

## Executando

```bash
python app.py
```

Acesse **http://localhost:5000** no navegador.

**Login:** `admin@nexar.com` com a senha definida em `ADMIN_PASSWORD`.

Para publicar na nuvem, veja [docs/DEPLOY_RAILWAY.md](docs/DEPLOY_RAILWAY.md).

### Base de demonstração

Para apresentações, popule o banco com 5 máquinas com CAD 3D (robôs ABB e tornos) e 23 ocorrências dos últimos 60 dias
(abertas, em andamento e resolvidas com a solução registrada):

```bash
python scripts/seed_demo.py              # recusa se o banco já tiver ocorrências
python scripts/seed_demo.py --forcar     # apaga máquinas/ocorrências e recria
DATABASE_PATH=demo.db python scripts/seed_demo.py   # em um banco separado
```

Com `GEMINI_API_KEY` configurada, cada diagnóstico é gerado pela IA (leva ~2 minutos
por causa do limite de requisições); sem chave, fica o roteiro padrão de inspeção.

### Como o sistema funciona

- **Nova ocorrência (3D):** o operador escolhe a máquina, toca na peça no modelo CAD 3D,
  escolhe o sintoma e responde se a máquina parou e se há risco. O sistema mostra na hora as
  soluções que já funcionaram naquela peça (nesta máquina e nas do mesmo modelo) e gera o
  diagnóstico. Só máquinas com CAD 3D recebem ocorrências.
- **Sensor Visual:** foto do equipamento → a IA marca as anomalias → o sistema aponta a peça
  provável no 3D e abre a ocorrência já com máquina e peça preenchidas.
- **Inspeção de Documento:** foto de permissão de trabalho, OS, checklist ou ficha → a IA lê
  o documento (número, data, equipamento, pessoas) e o sistema confere com o cadastro da
  empresa: quem executa está cadastrado, ativo e com as habilitações exigidas em dia (NR-10,
  NR-35, ASO…)? A máquina existe? O resultado é **Aprovado**, **Com pendências** ou
  **Bloqueado**. Sem IA, dá para conferir informando as matrículas e a máquina.
- **Pessoas e habilitações (RH):** cadastro de colaboradores com validade de ASO e treinamentos
  NR, importação por planilha (CSV) e painel de vencimentos. Não guarda salário nem laudos
  médicos; cada consulta fica na auditoria (LGPD).
- **Configurações (administrador):** usuários e perfis (Administrador, RH, Manutenção,
  Operador), tipos de documento (campos obrigatórios e habilitações exigidas) e auditoria.

- **Indicadores (Manutenção):** MTTR, MTBF, disponibilidade e custo por máquina e por mês,
  com as peças que mais falham.
- **Mapa de calor no 3D:** cada peça pintada pelo número de falhas, da máquina ou da frota do
  mesmo modelo, com as soluções de cada peça.
- **Mapa da fábrica:** planta com a situação de cada máquina (parada, com ocorrência, operando).
- **Importar CAD 3D:** envio de STEP pelo próprio sistema, conversão em segundo plano e
  conferência dos componentes numa prévia 3D (ver [docs/CAD_3D.md](docs/CAD_3D.md)).
- **Integração com o RH:** o sistema de RH envia pessoas e habilitações por uma API com chave
  (ver [docs/INTEGRACAO_RH.md](docs/INTEGRACAO_RH.md)).

**Usuários da base de demonstração** (senha igual à do administrador, `nexar2026` por padrão):
`admin@nexar.com`, `rh@nexar.com`, `manutencao@nexar.com`, `operador@nexar.com`.
Fotos de documentos para testar estão em `docs/exemplos/` (uma PT bloqueada por NR-10
vencida, uma OS com pendências e uma PT aprovada).

### Modelos 3D a partir do CAD

Máquinas podem usar o CAD do fabricante (STEP convertido em GLB) no visualizador 3D.
O passo a passo para acrescentar uma máquina está em [docs/CAD_3D.md](docs/CAD_3D.md).

## Estrutura

```
Nexar-QRQC/
├── app.py                  ← Aplicação Flask (rotas e lógica)
├── qrqc.db                 ← Banco de dados SQLite (gerado automaticamente)
├── requirements.txt        ← Dependências Python
├── .env                    ← Variáveis de ambiente (não versionado)
├── templates/              ← Páginas HTML (Jinja2)
│   ├── inicialtotem.html   ← Tela inicial do totem
│   ├── telaInicial.html    ← Dashboard com KPIs e últimas ocorrências
│   ├── login.html
│   ├── menu.html           ← Layout base com sidebar
│   ├── CadastroOcorrencia.html
│   ├── solucao.html        ← Exibe diagnóstico gerado pela IA
│   ├── historico.html      ← Histórico completo de ocorrências
│   └── ...
└── static/
    ├── css/
    ├── js/
    ├── assets/img/
    └── uploads/maquinas/   ← Diagramas técnicos por máquina
```

## Mudando de provedor de IA

O sistema foi migrado de OpenAI/GPT-4o para **Gemini 2.0 Flash** porque:
- ✅ Free tier real e generoso (sem cartão de crédito)
- ✅ Suporte nativo a visão (analisa diagramas)
- ✅ Excelente em português
- ✅ Resposta rápida (~1-2 segundos)

Se precisar usar outro modelo Gemini, basta alterar a variável `GEMINI_MODEL` no `.env`:
- `gemini-2.0-flash` — padrão, gratuito, rápido (recomendado)
- `gemini-1.5-pro` — mais capaz, ainda no free tier (50 req/dia)
- `gemini-1.5-flash` — alternativa estável

---

© 2026 NEXAR Soluções Tecnológicas
