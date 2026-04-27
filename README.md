# Nexar QRQC

Sistema de registro e resolução de ocorrências industriais com inteligência artificial. O operador registra um problema, a IA (GPT-4) gera um plano de ação passo a passo e, opcionalmente, uma imagem explicativa (DALL-E 3). A solicitação de suporte é enviada via WhatsApp pelo Twilio.

## Funcionalidades

- Cadastro de ocorrências com campos de setor, tipo, nível de impacto e detalhamento técnico
- Geração automática de solução via GPT-4
- Geração opcional de imagem técnica via DALL-E 3
- Histórico de todas as ocorrências registradas
- Solicitação de suporte com envio de mensagem via WhatsApp (Twilio)

## Tecnologias

- **Python / Flask** — backend e rotas
- **SQLite** — banco de dados local (`qrqc.db`)
- **OpenAI API** — GPT-4 (soluções) e DALL-E 3 (imagens)
- **Twilio** — envio de mensagens WhatsApp
- **HTML + CSS + JS** — frontend com templates Jinja2

## Pré-requisitos

- Python 3.10 ou superior
- Conta na [OpenAI](https://platform.openai.com/) com acesso à API
- Conta no [Twilio](https://www.twilio.com/) com WhatsApp Sandbox configurado

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

Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:

```env
OPENAI_API_KEY=sua_chave_openai

TWILIO_ACCOUNT_SID=seu_account_sid
TWILIO_AUTH_TOKEN=seu_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_DESTINATARIO=whatsapp:+55119XXXXXXXX
```

> O arquivo `.env` está no `.gitignore` e nunca deve ser commitado.

## Executando

```bash
python app.py
```

Acesse **http://localhost:5000** no navegador.

## Estrutura

```
Nexar-QRQC/
├── app.py                  ← Aplicação Flask (rotas e lógica)
├── qrqc.db                 ← Banco de dados SQLite (gerado automaticamente)
├── requirements.txt        ← Dependências Python
├── .env                    ← Variáveis de ambiente (não versionado)
├── templates/              ← Páginas HTML (Jinja2)
│   ├── inicialtotem.html   ← Tela inicial do totem
│   ├── telaInicial.html    ← Tela de navegação
│   ├── CadastroOcorrencia.html
│   ├── solucao.html        ← Exibe solução gerada pela IA
│   ├── historico.html      ← Histórico de ocorrências
│   └── Solicitação_Suporte.html
└── static/
    ├── css/
    ├── js/
    └── assets/img/
```

---

© 2026 NEXAR Soluções Tecnológicas
