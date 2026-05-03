# Nexar QRQC

Sistema de registro e resolução de ocorrências industriais com inteligência artificial. O operador registra um problema, a IA (**Gemini 2.0 Flash** com visão) gera um diagnóstico técnico passo a passo. A solicitação de suporte é enviada via WhatsApp pelo Twilio.

## Funcionalidades

- Cadastro de ocorrências com campos de setor, tipo, nível de impacto e detalhamento técnico
- Geração automática de diagnóstico via **Gemini 2.0 Flash** (gratuito até 1.500 req/dia)
- Análise de diagramas técnicos (PNG/JPG) via visão multimodal
- Histórico completo de ocorrências com filtros e modal de detalhes
- Dashboard com KPIs, distribuição por tipo e últimas ocorrências
- Solicitação de suporte com envio de mensagem via WhatsApp (Twilio)

## Tecnologias

- **Python / Flask** — backend e rotas
- **SQLite** — banco de dados local (`qrqc.db`)
- **Google Generative AI** — Gemini 2.0 Flash (texto + visão)
- **Pillow** — processamento de imagens dos diagramas
- **Twilio** — envio de mensagens WhatsApp
- **HTML + CSS + JS** — frontend com templates Jinja2

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

Crie um arquivo `.env` na raiz do projeto:

```env
# Obtenha sua chave gratuita em https://aistudio.google.com/apikey
GEMINI_API_KEY=sua_chave_gemini_aqui

# Opcional: troque o modelo (padrão: gemini-2.0-flash)
GEMINI_MODEL=gemini-2.0-flash

# Twilio (opcional, só se for usar a funcionalidade de suporte WhatsApp)
TWILIO_ACCOUNT_SID=seu_account_sid
TWILIO_AUTH_TOKEN=seu_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_DESTINATARIO=whatsapp:+55119XXXXXXXX

# Sessão Flask
SECRET_KEY=alguma_string_secreta_aqui
```

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

**Login padrão:** `admin@nexar.com` / `nexar2026`

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
