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
