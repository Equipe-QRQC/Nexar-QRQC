import os
import io
import json
import logging
import re
import sqlite3
from datetime import datetime
from typing import Literal
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google import genai
from google.genai import types as genai_types
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import smtplib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "f_err.log")

# Handler para arquivo (sempre ativo) + stderr (default do basicConfig)
logging.basicConfig(
    level=logging.INFO,
    format=_LOG_FORMAT,
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("nexar.qrqc")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexar-qrqc-secret-2026")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ── Gemini (Google GenAI SDK) ─────────────────────────────────────────────────
# Modelo: gemini-2.0-flash (free tier: 15 req/min, 1500 req/dia)
# Obter chave: https://aistudio.google.com/apikey
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

# Cadeia de modelos: tenta na ordem. Se 429/quota/404 em um, cai no próximo.
# Pode forçar um único modelo definindo GEMINI_MODEL no .env.
# Obs: modelos 1.5-flash e 1.5-flash-8b foram descontinuados em set/2025.
_DEFAULT_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]
_user_model = os.getenv("GEMINI_MODEL", "").strip()
GEMINI_MODELS = [_user_model] if _user_model else _DEFAULT_CHAIN
GEMINI_MODEL  = GEMINI_MODELS[0]  # exibido na UI

# Cadeia ESPECÍFICA para detecção de bounding boxes (visão espacial precisa).
# gemini-2.5-pro é melhor para coordenadas, mas tem free tier menor (50 req/dia)
# Se Pro estourar quota, cai pro Flash que ainda funciona razoavelmente.
_BBOX_MODELS = [
    "gemini-2.5-pro",          # melhor visão espacial
    "gemini-2.5-flash",        # fallback rápido
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
]

SYSTEM_INSTRUCTION = (
    "Você é um engenheiro sênior de manutenção industrial e qualidade (QRQC) "
    "com 20 anos de experiência em chão de fábrica. Responda em português técnico, "
    "objetivo e detalhado — manutentor precisa de informação acionável. "
    "Quando há diagrama anexado, referencia componentes e cotas observados."
)

GEN_CONFIG = genai_types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.5,
    top_p=0.9,
    max_output_tokens=4096,  # generoso para garantir 4 seções completas
)


# ── Schemas para structured output (Diagnóstico + Anotações) ──────────────────

class Anotacao(BaseModel):
    """Marcação de um componente crítico no diagrama da máquina."""
    x: float = Field(description="Posição X em % da largura (0-100)", ge=0, le=100)
    y: float = Field(description="Posição Y em % da altura (0-100)", ge=0, le=100)
    raio: float = Field(default=4.0, description="Raio do círculo em % da largura (3-8)", ge=2, le=10)
    tipo: Literal["critico", "atencao", "info"] = Field(
        description="critico=falha provável, atencao=ponto de inspeção, info=referência geral"
    )
    titulo: str = Field(description="Nome curto do componente (ex: 'Vedação do flange')")
    descricao: str = Field(description="Por que este ponto é relevante para o diagnóstico")


class ComponenteDetectado(BaseModel):
    """Componente identificado no diagrama com bounding box."""
    box_2d: list[int] = Field(
        description="Bounding box [ymin, xmin, ymax, xmax] normalizado em 0-1000",
        min_length=4,
        max_length=4,
    )
    label: str = Field(description="Nome curto do componente como aparece no diagrama")
    tipo: Literal["critico", "atencao", "info"] = Field(
        description="critico=falha provável, atencao=inspecionar, info=referência"
    )
    descricao: str = Field(description="Por que este componente é relevante (1 frase)")


class DeteccaoComponentes(BaseModel):
    """Lista de componentes detectados no diagrama com posições precisas."""
    componentes: list[ComponenteDetectado]


# Config para a 2ª chamada (detecção de bounding boxes)
GEN_CONFIG_BBOX = genai_types.GenerateContentConfig(
    system_instruction=(
        "Você é um especialista em visão computacional aplicada a diagramas técnicos industriais. "
        "Sua tarefa é localizar precisamente componentes mencionados em um diagnóstico, "
        "retornando bounding boxes no formato [ymin, xmin, ymax, xmax] normalizado em 0-1000. "
        "Seja preciso: a caixa deve cobrir EXATAMENTE o desenho/rótulo do componente, sem áreas vazias."
    ),
    temperature=0.1,  # baixa temperatura → mais determinístico para coordenadas
    top_p=0.9,
    max_output_tokens=800,
    response_mime_type="application/json",
    response_schema=DeteccaoComponentes,
)

gemini_client = None
if GEMINI_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_KEY)
        logger.info(f"Gemini inicializado — modelo {GEMINI_MODEL}")
    except Exception as e:
        logger.warning(f"Falha ao inicializar Gemini: {e}")
else:
    logger.warning("GEMINI_API_KEY não configurada — respostas da IA usarão fallback offline.")

# ── SMTP / Email de suporte ───────────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SUPORTE_EMAIL_DESTINO = os.getenv("SUPORTE_EMAIL_DESTINO", "")
SUPORTE_EMAIL_FROM    = os.getenv("SUPORTE_EMAIL_FROM", SMTP_USER)
SUPORTE_FOLDER = os.path.join("static", "uploads", "suporte")
os.makedirs(SUPORTE_FOLDER, exist_ok=True)

login_manager = LoginManager(app)
login_manager.login_view = "login"

UPLOAD_FOLDER = os.path.join("static", "uploads", "maquinas")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

TRANSLATIONS = {
    "pt": {
        "nova_ocorrencia": "Nova Ocorrência", "historico": "Histórico",
        "maquinas": "Máquinas", "sair": "Sair", "entrar": "Entrar",
        "email": "E-mail", "senha": "Senha", "bem_vindo": "Bem-vindo ao QRQC",
        "cadastro_titulo": "Cadastro de Ocorrência",
        "identificacao": "Identificação do Problema",
        "classificacao": "Classificação", "registrar": "Registrar",
        "cancelar": "Cancelar", "limpar": "Limpar",
        "maquina": "Máquina", "operador": "Operador", "setor": "Setor",
        "descricao": "Descrição do problema", "tipo": "Tipo de Ocorrência",
        "impacto": "Nível de Impacto", "recorrente": "Problema Recorrente?",
        "detalhamento": "Detalhamento Técnico", "solucao": "Solução Gerada pela IA",
        "diagnostico": "Diagnóstico Técnico", "diagrama": "Diagrama da Máquina",
        "historico_titulo": "Histórico de Ocorrências", "pesquisar": "Pesquisar...",
        "solicitar_suporte": "Solicitar Suporte", "finalizar": "Finalizar",
        "assistente": "Assistente IA", "enviar": "Enviar",
        "nova_maquina": "Nova Máquina", "cadastrar_maquina": "Cadastrar Máquina",
        "nome": "Nome", "modelo": "Modelo", "fabricante": "Fabricante",
        "ano": "Ano", "diagramas": "Diagramas Técnicos",
    },
    "en": {
        "nova_ocorrencia": "New Occurrence", "historico": "History",
        "maquinas": "Machines", "sair": "Logout", "entrar": "Sign In",
        "email": "Email", "senha": "Password", "bem_vindo": "Welcome to QRQC",
        "cadastro_titulo": "Register Occurrence",
        "identificacao": "Problem Identification",
        "classificacao": "Classification", "registrar": "Register",
        "cancelar": "Cancel", "limpar": "Clear",
        "maquina": "Machine", "operador": "Operator", "setor": "Sector",
        "descricao": "Problem description", "tipo": "Occurrence Type",
        "impacto": "Impact Level", "recorrente": "Recurring Problem?",
        "detalhamento": "Technical Detail", "solucao": "AI Generated Solution",
        "diagnostico": "Technical Diagnosis", "diagrama": "Machine Diagram",
        "historico_titulo": "Occurrence History", "pesquisar": "Search...",
        "solicitar_suporte": "Request Support", "finalizar": "Finish",
        "assistente": "AI Assistant", "enviar": "Send",
        "nova_maquina": "New Machine", "cadastrar_maquina": "Register Machine",
        "nome": "Name", "modelo": "Model", "fabricante": "Manufacturer",
        "ano": "Year", "diagramas": "Technical Diagrams",
    },
    "es": {
        "nova_ocorrencia": "Nueva Ocurrencia", "historico": "Historial",
        "maquinas": "Máquinas", "sair": "Salir", "entrar": "Ingresar",
        "email": "Correo", "senha": "Contraseña", "bem_vindo": "Bienvenido al QRQC",
        "cadastro_titulo": "Registro de Ocurrencia",
        "identificacao": "Identificación del Problema",
        "classificacao": "Clasificación", "registrar": "Registrar",
        "cancelar": "Cancelar", "limpar": "Limpiar",
        "maquina": "Máquina", "operador": "Operador", "setor": "Sector",
        "descricao": "Descripción del problema", "tipo": "Tipo de Ocurrencia",
        "impacto": "Nivel de Impacto", "recorrente": "¿Problema recurrente?",
        "detalhamento": "Detalle Técnico", "solucao": "Solución Generada por IA",
        "diagnostico": "Diagnóstico Técnico", "diagrama": "Diagrama de la Máquina",
        "historico_titulo": "Historial de Ocurrencias", "pesquisar": "Buscar...",
        "solicitar_suporte": "Solicitar Soporte", "finalizar": "Finalizar",
        "assistente": "Asistente IA", "enviar": "Enviar",
        "nova_maquina": "Nueva Máquina", "cadastrar_maquina": "Registrar Máquina",
        "nome": "Nombre", "modelo": "Modelo", "fabricante": "Fabricante",
        "ano": "Año", "diagramas": "Diagramas Técnicos",
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect("qrqc.db")
    conn.row_factory = sqlite3.Row
    return conn


def normalizar_data(raw: str) -> str:
    """
    Converte 'datetime-local' (`2024-01-15T10:30`) ou ISO em string normalizada
    'YYYY-MM-DD HH:MM'. Se vazio/inválido, devolve agora.
    """
    if not raw:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    raw = raw.strip().replace("T", " ")
    try:
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw[:16]  # corta no minuto se o parse falhar


# ── Envio de email de suporte ─────────────────────────────────────────────────
def enviar_email_suporte(ticket: dict, anexos_paths: list[str] | None = None) -> bool:
    """
    Envia notificação de novo ticket de suporte por SMTP.
    Retorna True se enviou com sucesso, False caso contrário (best-effort).
    """
    if not (SMTP_USER and SMTP_PASSWORD and SUPORTE_EMAIL_DESTINO):
        logger.warning("[suporte] SMTP não configurado — pulando envio de email")
        return False

    cor_pri = {
        "Baixa": "#10B981", "Média": "#F59E0B",
        "Alta": "#EF4444", "Crítica": "#A855F7",
    }.get(ticket.get("prioridade", ""), "#6B7280")

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#111;">
      <div style="background:#0EA5E9;color:#fff;padding:18px 24px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;font-size:18px;">🎫 Novo Ticket de Suporte — Nexar QRQC</h2>
        <p style="margin:4px 0 0;font-size:13px;opacity:.9;">Protocolo: <strong>{ticket['protocolo']}</strong></p>
      </div>
      <div style="border:1px solid #E5E7EB;border-top:none;padding:20px 24px;border-radius:0 0 8px 8px;">
        <p style="margin:0 0 8px;"><strong>Tipo:</strong> {ticket['tipo']}
          &nbsp;·&nbsp; <strong>Prioridade:</strong>
          <span style="color:{cor_pri};font-weight:700;">{ticket['prioridade']}</span></p>
        <p style="margin:0 0 16px;"><strong>Setor:</strong> {ticket['setor']}</p>
        <hr style="border:none;border-top:1px solid #E5E7EB;margin:14px 0;">
        <p style="margin:0 0 6px;"><strong>Solicitante:</strong> {ticket['nome']}</p>
        <p style="margin:0 0 6px;"><strong>Email:</strong> <a href="mailto:{ticket['email']}">{ticket['email']}</a></p>
        {f"<p style='margin:0 0 6px;'><strong>Telefone:</strong> {ticket['telefone']}</p>" if ticket.get('telefone') else ''}
        <hr style="border:none;border-top:1px solid #E5E7EB;margin:14px 0;">
        <p style="margin:0 0 4px;"><strong>Assunto:</strong></p>
        <p style="margin:0 0 14px;font-size:15px;">{ticket['assunto']}</p>
        <p style="margin:0 0 4px;"><strong>Detalhamento:</strong></p>
        <div style="background:#F9FAFB;border-left:3px solid #0EA5E9;padding:12px 14px;border-radius:4px;white-space:pre-wrap;font-size:14px;line-height:1.6;">{ticket['motivo']}</div>
        <p style="margin-top:18px;font-size:12px;color:#6B7280;">
          Para responder, use o <em>Reply-To</em> deste email — vai direto para o solicitante.
        </p>
      </div>
    </div>
    """

    try:
        msg = MIMEMultipart()
        msg["From"]     = SUPORTE_EMAIL_FROM
        msg["To"]       = SUPORTE_EMAIL_DESTINO
        msg["Reply-To"] = ticket["email"]
        msg["Subject"]  = f"[{ticket['prioridade']}] {ticket['protocolo']} — {ticket['assunto']}"
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        for path in (anexos_paths or []):
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
            msg.attach(part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"[suporte] email enviado — protocolo={ticket['protocolo']}")
        return True
    except Exception:
        logger.exception(f"[suporte] falha no envio de email — protocolo={ticket.get('protocolo')}")
        return False


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT DEFAULT 'operador',
            ativo INTEGER DEFAULT 1,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            modelo TEXT,
            fabricante TEXT,
            ano TEXT,
            setor TEXT,
            descricao TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS diagramas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            caminho TEXT NOT NULL,
            tipo TEXT,
            FOREIGN KEY (maquina_id) REFERENCES maquinas(id)
        );
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id INTEGER,
            data_ocorrencia TEXT,
            nome_operador TEXT,
            setor_area TEXT,
            descricao TEXT,
            tipo_ocorrencia TEXT,
            nivel_impacto TEXT,
            problema_recorrente TEXT,
            detalhamento_tecnico TEXT,
            resposta_ia TEXT,
            ia_status TEXT DEFAULT 'ok',
            diagrama_url TEXT,
            status TEXT DEFAULT 'Aberta',
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maquina_id) REFERENCES maquinas(id)
        );
        CREATE TABLE IF NOT EXISTS tickets_suporte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT UNIQUE NOT NULL,
            usuario_id INTEGER,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT,
            setor TEXT NOT NULL,
            tipo TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            assunto TEXT NOT NULL,
            motivo TEXT NOT NULL,
            anexos_json TEXT,
            status TEXT DEFAULT 'Aberto',
            email_enviado INTEGER DEFAULT 0,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    """)
    # Migração leve: adiciona colunas que possam estar ausentes em DBs antigos.
    cols = [r["name"] for r in c.execute("PRAGMA table_info(ocorrencias)").fetchall()]
    migracoes = {
        "ia_status":           "ALTER TABLE ocorrencias ADD COLUMN ia_status TEXT DEFAULT 'ok'",
        "anotacoes_ia":        "ALTER TABLE ocorrencias ADD COLUMN anotacoes_ia TEXT",
        "status":              "ALTER TABLE ocorrencias ADD COLUMN status TEXT DEFAULT 'Aberta'",
        "diagrama_url":        "ALTER TABLE ocorrencias ADD COLUMN diagrama_url TEXT",
        "resposta_ia":         "ALTER TABLE ocorrencias ADD COLUMN resposta_ia TEXT",
        "detalhamento_tecnico":"ALTER TABLE ocorrencias ADD COLUMN detalhamento_tecnico TEXT",
        "problema_recorrente": "ALTER TABLE ocorrencias ADD COLUMN problema_recorrente TEXT",
        "nivel_impacto":       "ALTER TABLE ocorrencias ADD COLUMN nivel_impacto TEXT",
        "tipo_ocorrencia":     "ALTER TABLE ocorrencias ADD COLUMN tipo_ocorrencia TEXT",
        "setor_area":          "ALTER TABLE ocorrencias ADD COLUMN setor_area TEXT",
        "nome_operador":       "ALTER TABLE ocorrencias ADD COLUMN nome_operador TEXT",
        "data_ocorrencia":     "ALTER TABLE ocorrencias ADD COLUMN data_ocorrencia TEXT",
        "maquina_id":          "ALTER TABLE ocorrencias ADD COLUMN maquina_id INTEGER",
        # Resolução de ocorrência
        "solucao_aplicada":    "ALTER TABLE ocorrencias ADD COLUMN solucao_aplicada TEXT",
        "componente_real":     "ALTER TABLE ocorrencias ADD COLUMN componente_real TEXT",
        "data_resolucao":      "ALTER TABLE ocorrencias ADD COLUMN data_resolucao DATETIME",
        "resolvido_por_id":    "ALTER TABLE ocorrencias ADD COLUMN resolvido_por_id INTEGER",
    }
    for col, sql in migracoes.items():
        if col not in cols:
            try:
                c.execute(sql)
                logger.info(f"Migração: coluna {col} adicionada em ocorrencias.")
            except Exception as e:
                logger.warning(f"Migração de {col} falhou: {e}")

    admin = c.execute("SELECT id FROM usuarios WHERE email = 'admin@nexar.com'").fetchone()
    if not admin:
        c.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?,?,?,?)",
            ("Administrador", "admin@nexar.com", generate_password_hash("nexar2026"), "admin"),
        )
    conn.commit()
    conn.close()


init_db()


# ── Auth ──────────────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, id, nome, email, perfil):
        self.id = id
        self.nome = nome
        self.email = email
        self.perfil = perfil


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    u = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if u:
        return User(u["id"], u["nome"], u["email"], u["perfil"])
    return None


@app.context_processor
def inject_globals():
    lang = session.get("lang", "pt")
    return {"t": TRANSLATIONS.get(lang, TRANSLATIONS["pt"]), "lang": lang}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        conn = get_db()
        u = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,)
        ).fetchone()
        conn.close()
        if u and check_password_hash(u["senha_hash"], senha):
            login_user(User(u["id"], u["nome"], u["email"], u["perfil"]))
            return redirect(url_for("dashboard"))
        lang = session.get("lang", "pt")
        erro = {"pt": "E-mail ou senha incorretos.", "en": "Invalid email or password.", "es": "Correo o contraseña incorrectos."}.get(lang)
        return render_template("login.html", erro=erro)
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/lang/<lang>")
def set_lang(lang):
    if lang in ["pt", "en", "es"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("dashboard"))


# ── AI Chat ───────────────────────────────────────────────────────────────────

def _historico_para_gemini(historico: list[dict]) -> list[dict]:
    """
    Converte histórico estilo OpenAI ({role:'user'|'assistant', content:str})
    para o formato do Gemini ({role:'user'|'model', parts:[{text}]}).
    """
    out = []
    for m in historico or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        gemini_role = "model" if role in ("assistant", "model") else "user"
        out.append({"role": gemini_role, "parts": [{"text": content}]})
    return out


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    if not gemini_client:
        return jsonify({"resposta": "⚠️ IA offline — configure GEMINI_API_KEY no .env."}), 503
    data = request.get_json(silent=True) or {}
    mensagem = (data.get("mensagem") or "").strip()
    historico = data.get("historico") or []
    if not mensagem:
        return jsonify({"resposta": "Por favor, escreva uma pergunta."}), 400

    historico_gemini = _historico_para_gemini(historico)
    ultimo_erro: Exception | None = None
    for modelo in GEMINI_MODELS:
        try:
            chat_session = gemini_client.chats.create(
                model=modelo,
                history=historico_gemini,
                config=GEN_CONFIG,
            )
            response = chat_session.send_message(mensagem)
            texto = (response.text or "").strip()
            if texto:
                return jsonify({"resposta": texto})
        except Exception as e:
            ultimo_erro = e
            if _is_quota_error(e):
                logger.warning(f"[chat/{modelo}] cota esgotada — tentando próximo modelo")
                continue
            logger.exception(f"[chat/{modelo}] erro")
            break

    if ultimo_erro and _should_try_next_model(ultimo_erro):
        msg = ("⚠️ Todos os modelos da IA falharam (cota, indisponibilidade ou modelo descontinuado). "
               "Aguarde alguns minutos ou configure uma nova chave em outra conta Google.")
        return jsonify({"resposta": msg}), 503
    return jsonify({"resposta": f"Erro ao consultar a IA: {ultimo_erro}"}), 500


# ── AI Response (com fallback robusto) ────────────────────────────────────────

def _fallback_response(prompt: str) -> str:
    """Resposta gerada localmente quando a IA está indisponível."""
    return (
        "⚠️ IA temporariamente indisponível — diagnóstico genérico:\n\n"
        "1. **Causa provável:** verificar histórico recente da máquina, possíveis falhas mecânicas, "
        "elétricas ou de processo.\n"
        "2. **Componentes a verificar:** sensores principais, atuadores, sistema de refrigeração e "
        "lubrificação, conexões elétricas.\n"
        "3. **Procedimento de inspeção:**\n"
        "   • Desligar a máquina e bloquear/sinalizar (LOTO).\n"
        "   • Inspeção visual de vazamentos, ruídos anormais e sobreaquecimento.\n"
        "   • Verificar leituras dos sensores e parâmetros do CLP.\n"
        "   • Conferir últimos planos de manutenção preventiva.\n"
        "4. **Quando escalar:** caso o problema persista após inspeção inicial ou represente risco "
        "à segurança, escalar imediatamente para o engenheiro de manutenção/fabricante.\n\n"
        "Por favor, configure GEMINI_API_KEY no arquivo .env para diagnósticos personalizados."
    )


# Componentes industriais comuns (lista priorizada — primeiros têm mais peso)
_COMPONENTES_CONHECIDOS = [
    # Acionamento / hidráulica
    "BOMBA", "MOTOR", "REDUTOR", "ACOPLAMENTO", "EIXO", "TURBINA",
    # Vedações / mecânica
    "VEDAÇÃO", "VEDACAO", "VEDAÇÕES", "VEDACOES", "ROLAMENTO", "MANCAL", "GAXETA",
    # Fluidos
    "VÁLVULA", "VALVULA", "FILTRO", "RESERVATÓRIO", "RESERVATORIO", "TANQUE",
    "CILINDRO", "PISTÃO", "PISTAO", "MANGUEIRA", "TROCADOR",
    # Elétrica / controle
    "ESTATOR", "ROTOR", "SENSOR", "MANÔMETRO", "MANOMETRO", "TERMÔMETRO", "TERMOMETRO",
    "INVERSOR", "CLP", "CONTATOR", "RELÉ", "RELE", "DISJUNTOR", "ATUADOR",
    # Estruturais
    "ENGRENAGEM", "CORREIA", "POLIA", "VENTILADOR", "CARCAÇA", "CARCACA",
    # Solda / robótica
    "ROBÔ", "ROBO", "BICO", "ELETRODO", "ARAME",
]


def _extrair_componente_primario(diagnostico: str) -> str | None:
    """
    Extrai o componente primário citado na seção '1. Causa provável'.
    Retorna o nome em UPPERCASE (formato típico de rótulos em diagramas).
    """
    if not diagnostico:
        return None

    # Tenta isolar a seção 1 (entre '1. Causa provável' e '2. ...')
    match = re.search(
        r"\*?\*?1\.\s*Causa.*?\*?\*?\s*\n+(.+?)(?=\n\s*\*?\*?2\.|\Z)",
        diagnostico,
        re.DOTALL | re.IGNORECASE,
    )
    secao = match.group(1) if match else diagnostico[:600]
    secao_upper = secao.upper()

    # Procura componentes em ordem de prioridade
    for componente in _COMPONENTES_CONHECIDOS:
        if componente in secao_upper:
            # Normaliza acentos para uppercase ASCII (compatível com diagramas)
            return (
                componente
                .replace("Ç", "C").replace("Ã", "A").replace("Õ", "O")
                .replace("Ô", "O").replace("Â", "A").replace("Ê", "E").replace("É", "E")
            )
    return None


def _bbox_para_overlay(bbox: list[int]) -> dict:
    """
    Converte bounding box do Gemini [ymin, xmin, ymax, xmax] em 0-1000
    para coordenadas de overlay (centro x%, centro y%, raio%).
    """
    ymin, xmin, ymax, xmax = bbox
    cx = (xmin + xmax) / 2 / 10  # 0-1000 → 0-100
    cy = (ymin + ymax) / 2 / 10
    largura  = (xmax - xmin) / 10
    altura   = (ymax - ymin) / 10
    # Raio = metade do menor lado, com piso/teto razoáveis
    raio = max(2.5, min(8.0, max(largura, altura) / 2))
    return {
        "x": round(cx, 2),
        "y": round(cy, 2),
        "raio": round(raio, 2),
    }


def _detectar_componentes(
    img_obj,
    diagnostico_texto: str,
    modelos: list[str],
    componente_primario: str | None = None,
) -> list[dict]:
    """
    Segunda chamada à IA: usa visão computacional para localizar componentes
    mencionados no diagnóstico, retornando bounding boxes precisos.

    Args:
        img_obj: imagem PIL do diagrama
        diagnostico_texto: texto markdown do diagnóstico (1ª call)
        modelos: cadeia de modelos a tentar (Pro primeiro)
        componente_primario: nome do componente primário extraído da seção 1
                              (ex: "BOMBA", "MOTOR") — força inclusão obrigatória
    """
    if not gemini_client or img_obj is None:
        return []

    # Guarda o melhor resultado caso nenhum modelo passe na validação rígida
    melhor_resultado: list[dict] = []
    melhor_modelo: str = ""

    hint_primario = ""
    if componente_primario:
        hint_primario = (
            f"\n\n⚠️ COMPONENTE PRIMÁRIO IDENTIFICADO PELO DIAGNÓSTICO: '{componente_primario}'\n"
            f"Este componente é a CAUSA PROVÁVEL e DEVE OBRIGATORIAMENTE estar na sua resposta com tipo='critico'.\n"
            f"Procure por esse rótulo no diagrama (pode estar escrito '{componente_primario}' ou variações)."
        )

    prompt_bbox = (
        "Analise o diagrama técnico industrial em anexo.\n\n"
        "DIAGNÓSTICO PRÉVIO DE UM ENGENHEIRO:\n"
        f"{diagnostico_texto[:2000]}"
        f"{hint_primario}\n\n"
        "TAREFA: Localize no diagrama os componentes relevantes para o diagnóstico acima "
        "e devolva bounding boxes PRECISOS.\n\n"
        "REGRAS OBRIGATÓRIAS:\n"
        "1. O COMPONENTE PRIMÁRIO (citado na seção 1 do diagnóstico) DEVE estar na lista "
        "como tipo='critico'. Não pule este componente sob nenhuma circunstância.\n"
        "2. Inclua de 3 a 6 componentes total, distribuídos como: 1-2 'critico', 2-3 'atencao', 0-1 'info'.\n"
        "3. Cada bbox deve cobrir EXATAMENTE o desenho/rótulo do componente real no diagrama — "
        "NUNCA áreas vazias. Se não tem certeza onde está o componente, OMITA-O em vez de inventar coordenadas.\n"
        "4. Use o NOME EXATO do rótulo como aparece no diagrama (ex: 'BOMBA', 'FILTRO', 'VEDACOES').\n"
        "5. Verifique cada bbox: a região [ymin, xmin, ymax, xmax] deve conter PIXELS do componente, "
        "não fundo branco.\n\n"
        "FORMATO DE CADA COMPONENTE:\n"
        "- box_2d: [ymin, xmin, ymax, xmax] em 0-1000\n"
        "- label: nome curto do componente como aparece no diagrama\n"
        "- tipo: 'critico' | 'atencao' | 'info'\n"
        "- descricao: 1 frase (max 100 chars) ligando este componente ao diagnóstico"
    )

    for modelo in modelos:
        try:
            response = gemini_client.models.generate_content(
                model=modelo,
                contents=[prompt_bbox, img_obj],
                config=GEN_CONFIG_BBOX,
            )
            parsed: DeteccaoComponentes | None = response.parsed
            if not parsed:
                try:
                    raw = json.loads(response.text or "{}")
                    parsed = DeteccaoComponentes(**raw)
                except Exception:
                    logger.warning(f"[bbox/{modelo}] resposta sem JSON parseável")
                    continue

            anotacoes: list[dict] = []
            for c in parsed.componentes:
                # Validação: bbox deve estar em 0-1000 e ter área positiva
                ymin, xmin, ymax, xmax = c.box_2d
                if not (0 <= ymin < ymax <= 1000 and 0 <= xmin < xmax <= 1000):
                    logger.warning(f"[bbox] descartado bbox inválido: {c.box_2d} ({c.label})")
                    continue
                centro = _bbox_para_overlay(c.box_2d)
                anotacoes.append({
                    **centro,
                    "tipo": c.tipo,
                    "titulo": c.label,
                    "descricao": c.descricao,
                })

            if anotacoes:
                # Verifica se o componente primário foi incluído (quando informado)
                if componente_primario:
                    nomes_marcados = " ".join(a["titulo"].upper() for a in anotacoes)
                    if componente_primario.upper() not in nomes_marcados:
                        logger.warning(
                            f"[bbox/{modelo}] componente primário '{componente_primario}' "
                            f"NÃO encontrado nas anotações ({nomes_marcados}) — tentando próximo modelo"
                        )
                        # Guarda como fallback caso todos os modelos falhem na validação
                        if len(anotacoes) > len(melhor_resultado):
                            melhor_resultado = anotacoes
                            melhor_modelo = modelo
                        continue  # tenta próximo modelo

                logger.info(f"[bbox] {len(anotacoes)} componente(s) localizado(s) por {modelo}")
                return anotacoes
            logger.warning(f"[bbox/{modelo}] retornou 0 componentes válidos")
        except Exception as e:
            if _should_try_next_model(e):
                logger.warning(f"[bbox/{modelo}] erro transitório — tentando próximo")
                continue
            logger.exception(f"[bbox/{modelo}] erro definitivo, abortando detecção")
            break

    # Fallback: nenhum modelo passou na validação do componente primário,
    # mas algum retornou anotações válidas — usa o melhor resultado.
    if melhor_resultado:
        logger.info(
            f"[bbox] usando fallback de {melhor_modelo} com {len(melhor_resultado)} "
            f"componente(s) (componente primário '{componente_primario}' não foi marcado)"
        )
        return melhor_resultado
    return []


def _should_try_next_model(err: Exception) -> bool:
    """
    Decide se vale a pena tentar o próximo modelo da cadeia.
    Inclui: 429 (cota), 404 (modelo descontinuado/inválido), 503 (indisponível).
    """
    s = str(err)
    s_low = s.lower()
    indicadores = [
        "429", "RESOURCE_EXHAUSTED", "quota", "rate limit",       # cota
        "404", "NOT_FOUND", "is not found", "is not supported",   # modelo descontinuado/inválido
        "503", "UNAVAILABLE", "overloaded",                        # serviço indisponível
        "DEADLINE_EXCEEDED", "timeout",                            # timeout
    ]
    return any(ind in s or ind.lower() in s_low for ind in indicadores)


# Mantém compatibilidade com possíveis chamadas externas
def _is_quota_error(err: Exception) -> bool:
    return _should_try_next_model(err)


def get_ai_response(
    prompt: str,
    imagem_path: str | None = None,
) -> tuple[str, list[dict], str]:
    """
    Fluxo em 2 chamadas:
    1) Diagnóstico em markdown (rápido, sem JSON)
    2) Se há imagem, detecção de componentes via bounding boxes (preciso)

    Retorna (texto_diagnostico, anotacoes, status).
    - texto_diagnostico: markdown
    - anotacoes: lista de dicts {x, y, raio, tipo, titulo, descricao}
    - status: 'ok' | 'fallback' | 'erro'
    """
    if not gemini_client:
        return (_fallback_response(prompt), [], "fallback")

    # Tenta abrir a imagem (se houver)
    img_obj = None
    if imagem_path:
        # Resolve o path relativo à raiz do app independente do CWD
        abs_path = os.path.join(app.root_path, imagem_path) if not os.path.isabs(imagem_path) else imagem_path
    if imagem_path and os.path.exists(abs_path):
        ext = imagem_path.rsplit(".", 1)[-1].lower()
        if ext in ("png", "jpg", "jpeg"):
            try:
                img_obj = Image.open(abs_path)
                if img_obj.mode in ("RGBA", "P"):
                    img_obj = img_obj.convert("RGB")
            except Exception as e:
                logger.warning(f"Não foi possível abrir imagem {abs_path}: {e}")

    has_image = img_obj is not None
    partes: list = [prompt] + ([img_obj] if has_image else [])

    ultimo_erro: Exception | None = None
    modelo_usado: str | None = None
    texto_diagnostico: str = ""

    # ── 1ª chamada: diagnóstico em texto markdown ─────────────────────────────
    for modelo in GEMINI_MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=modelo,
                contents=partes,
                config=GEN_CONFIG,
            )
            texto = (response.text or "").strip()
            if not texto:
                logger.warning(f"[{modelo}] resposta vazia, tentando próximo")
                continue
            texto_diagnostico = texto
            modelo_usado = modelo
            if modelo != GEMINI_MODELS[0]:
                logger.info(f"[ia] sucesso no modelo de fallback: {modelo}")
            break
        except Exception as e:
            ultimo_erro = e
            if _should_try_next_model(e):
                motivo = "404/descontinuado" if ("404" in str(e) or "NOT_FOUND" in str(e)) else "cota/timeout/indisponível"
                logger.warning(f"[{modelo}] {motivo} — tentando próximo modelo")
                continue
            logger.exception(f"[{modelo}] erro não-transitório")
            break

    # Se nenhum modelo respondeu o diagnóstico → erro
    if not texto_diagnostico:
        err_str = str(ultimo_erro) if ultimo_erro else ""
        is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
        if ultimo_erro and is_quota:
            msg = (
                "❌ Todas as cotas free tier do Gemini foram excedidas neste projeto.\n\n"
                "**Soluções possíveis:**\n"
                "1. Aguarde alguns minutos e tente novamente\n"
                "2. Crie uma **nova chave em outra conta Google**: https://aistudio.google.com/apikey\n"
                "3. Use um projeto Google Cloud que **nunca teve billing ativado**\n\n"
            )
        else:
            msg = f"❌ Erro ao gerar diagnóstico via Gemini: {ultimo_erro}\n\n"
        return (msg + _fallback_response(prompt), [], "erro")

    # ── 2ª chamada: detecção de componentes (bounding boxes) ──────────────────
    anotacoes: list[dict] = []
    if has_image:
        # Extrai o componente primário da seção 1 do diagnóstico (heurística regex)
        componente_primario = _extrair_componente_primario(texto_diagnostico)
        if componente_primario:
            logger.info(f"[bbox] componente primário detectado: {componente_primario}")

        # Cadeia bbox: começa com gemini-2.5-pro (melhor visão espacial)
        # Se Pro estourar quota, cai pro Flash. Remove duplicatas mantendo ordem.
        modelos_bbox = list(dict.fromkeys(_BBOX_MODELS + GEMINI_MODELS))

        anotacoes = _detectar_componentes(
            img_obj,
            texto_diagnostico,
            modelos_bbox,
            componente_primario=componente_primario,
        )

    return (texto_diagnostico, anotacoes, "ok")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Tela inicial pública (modo totem). Se o usuário já estiver logado,
    vai direto para o dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("inicialtotem.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard com KPIs, gráfico de tipo e últimas ocorrências."""
    conn = get_db()
    total       = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias").fetchone()["n"]
    abertas     = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias WHERE status = 'Aberta'").fetchone()["n"]
    resolvidas  = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias WHERE status IN ('Resolvida','Fechada')").fetchone()["n"]
    alto_imp    = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias WHERE nivel_impacto = 'Alto' AND status = 'Aberta'").fetchone()["n"]
    total_maq   = conn.execute("SELECT COUNT(*) AS n FROM maquinas").fetchone()["n"]

    por_tipo = conn.execute("""
        SELECT COALESCE(tipo_ocorrencia,'Outros') AS tipo, COUNT(*) AS n
        FROM ocorrencias GROUP BY tipo ORDER BY n DESC
    """).fetchall()

    ultimas = conn.execute("""
        SELECT o.id, o.nome_operador, o.tipo_ocorrencia, o.nivel_impacto,
               o.descricao, o.status, o.data_registro, o.ia_status,
               m.nome AS maquina_nome
        FROM ocorrencias o
        LEFT JOIN maquinas m ON o.maquina_id = m.id
        ORDER BY o.data_registro DESC LIMIT 5
    """).fetchall()
    conn.close()

    kpis = {
        "total": total, "abertas": abertas, "resolvidas": resolvidas,
        "alto_impacto": alto_imp, "maquinas": total_maq,
    }
    return render_template("telaInicial.html", kpis=kpis, por_tipo=por_tipo, ultimas=ultimas)


# Compat: rota antiga /telaInicial -> redireciona para o dashboard.
@app.route("/telaInicial")
@login_required
def telaInicial():
    return redirect(url_for("dashboard"))


@app.route("/historico")
@login_required
def historico():
    try:
        conn = get_db()
        ocorrencias = conn.execute(
            "SELECT o.*, m.nome AS maquina_nome, u.nome AS resolvido_por_nome "
            "FROM ocorrencias o "
            "LEFT JOIN maquinas m ON o.maquina_id = m.id "
            "LEFT JOIN usuarios u ON o.resolvido_por_id = u.id "
            "ORDER BY o.data_registro DESC"
        ).fetchall()
        conn.close()
        return render_template("historico.html", ocorrencias=ocorrencias)
    except Exception as e:
        logger.exception(f"Erro ao listar histórico: {e}")
        return render_template("historico.html", ocorrencias=[])


@app.route("/ocorrencias/<int:ocorrencia_id>/resolver", methods=["POST"])
@login_required
def resolver_ocorrencia(ocorrencia_id: int):
    """
    Marca uma ocorrência como Resolvida.
    Não exige descrição — basta a confirmação do operador.
    """
    try:
        conn = get_db()
        oc = conn.execute(
            "SELECT id, status FROM ocorrencias WHERE id = ?", (ocorrencia_id,)
        ).fetchone()
        if not oc:
            conn.close()
            return jsonify({"ok": False, "erro": "Ocorrência não encontrada."}), 404
        if oc["status"] in ("Resolvida", "Fechada"):
            conn.close()
            return jsonify({
                "ok": False,
                "erro": f"Ocorrência já está {oc['status']}.",
            }), 409

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """UPDATE ocorrencias
               SET status='Resolvida',
                   data_resolucao=?, resolvido_por_id=?
               WHERE id = ?""",
            (agora, current_user.id, ocorrencia_id),
        )
        conn.commit()

        # Busca dados atualizados pra resposta (UI atualiza inline)
        row = conn.execute(
            "SELECT o.status, o.data_resolucao, u.nome AS resolvido_por_nome "
            "FROM ocorrencias o "
            "LEFT JOIN usuarios u ON o.resolvido_por_id = u.id "
            "WHERE o.id = ?",
            (ocorrencia_id,),
        ).fetchone()
        conn.close()

        logger.info(f"[ocorrencia] resolvida id={ocorrencia_id} por user_id={current_user.id}")
        return jsonify({
            "ok": True,
            "status": row["status"],
            "data_resolucao": row["data_resolucao"],
            "resolvido_por_nome": row["resolvido_por_nome"],
        })
    except Exception as e:
        logger.exception("[ocorrencia] falha ao resolver")
        return jsonify({"ok": False, "erro": f"Erro ao salvar: {e}"}), 500


@app.route("/suporte")
@login_required
def solicitacao():
    return render_template("suporte.html")


@app.route("/CadastroOcorrencia")
@login_required
def CadastroOcorrencia():
    conn = get_db()
    maquinas = conn.execute("SELECT id, nome, setor FROM maquinas ORDER BY nome").fetchall()
    conn.close()
    return render_template("CadastroOcorrencia.html", maquinas=maquinas)


@app.route("/registrar_ocorrencia", methods=["POST"])
@login_required
def registrar_ocorrencia():
    """
    Registra uma ocorrência, gera diagnóstico via IA e renderiza solucao.html.
    Em caso de erro, retorna JSON (se for fetch) ou re-renderiza o formulário
    com mensagem clara — nunca silencia falhas.
    """
    # ── Validação dos campos ─────────────────────────────────────────────────
    obrigatorios = ["nome_operador", "setor_area", "descricao",
                    "tipo_ocorrencia", "nivel_impacto", "problema_recorrente",
                    "detalhamento_tecnico"]
    faltando = [c for c in obrigatorios if not (request.form.get(c) or "").strip()]
    if faltando:
        msg = f"Campos obrigatórios não preenchidos: {', '.join(faltando)}."
        logger.warning(f"[ocorrencia] {msg}")
        flash(msg, "danger")
        return redirect(url_for("CadastroOcorrencia"))

    maquina_id           = request.form.get("maquina_id") or None
    data_ocorrencia      = normalizar_data(request.form.get("data_ocorrencia", ""))
    nome_operador        = request.form.get("nome_operador", "").strip()
    setor_area           = request.form.get("setor_area", "").strip()
    descricao            = request.form.get("descricao", "").strip()
    tipo_ocorrencia      = request.form.get("tipo_ocorrencia", "").strip()
    nivel_impacto        = request.form.get("nivel_impacto", "").strip()
    problema_recorrente  = request.form.get("problema_recorrente", "").strip()
    detalhamento_tecnico = request.form.get("detalhamento_tecnico", "").strip()

    # ── Contexto da máquina ──────────────────────────────────────────────────
    maquina_info = ""
    diagrama_path = None
    maquina_nome = ""
    diagrama_url = None

    try:
        if maquina_id:
            conn = get_db()
            maquina = conn.execute("SELECT * FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
            diagrama = conn.execute(
                "SELECT * FROM diagramas WHERE maquina_id = ? AND tipo != 'PDF' LIMIT 1",
                (maquina_id,),
            ).fetchone()
            historico_maquina = conn.execute(
                "SELECT descricao, resposta_ia FROM ocorrencias "
                "WHERE maquina_id = ? ORDER BY data_registro DESC LIMIT 3",
                (maquina_id,),
            ).fetchall()
            conn.close()

            if maquina:
                maquina_nome = maquina["nome"]
                maquina_info = (
                    f"Máquina: {maquina['nome']} | Modelo: {maquina['modelo'] or '—'} | "
                    f"Fabricante: {maquina['fabricante'] or '—'} | Ano: {maquina['ano'] or '—'}\n"
                    f"Setor: {maquina['setor'] or '—'}\n"
                )
            if diagrama:
                diagrama_path = diagrama["caminho"]
                diagrama_url = "/" + diagrama_path.replace("\\", "/")
            if historico_maquina:
                maquina_info += "\nÚltimas ocorrências desta máquina:\n"
                for h in historico_maquina:
                    desc = (h["descricao"] or "")[:80]
                    maquina_info += f"- {desc}\n"
    except Exception:
        logger.exception("Erro ao carregar contexto da máquina")
        # Continua mesmo sem contexto da máquina — não é fatal.

    # ── Prompt para a IA ─────────────────────────────────────────────────────
    prompt = f"""{maquina_info}
DADOS DA OCORRÊNCIA:
- Operador: {nome_operador}
- Data: {data_ocorrencia}
- Setor: {setor_area}
- Tipo: {tipo_ocorrencia} | Impacto: {nivel_impacto} | Recorrente: {problema_recorrente}
- Descrição: {descricao}
- Detalhamento técnico: {detalhamento_tecnico}

{"O diagrama técnico da máquina está anexado — referencie componentes visíveis nele. " if diagrama_path else ""}Gere um diagnóstico técnico COMPLETO, OBRIGATORIAMENTE com TODAS as 4 seções abaixo (não pule nenhuma):

**1. Causa provável**
Hipótese principal em 3-5 linhas. Cite os sintomas específicos do detalhamento que sustentam o diagnóstico (pressão, temperatura, ruídos, histórico de manutenção). Identifique o componente primário suspeito.

**2. Componentes a verificar**
Liste 4-7 componentes em ordem de prioridade. Para cada um, escreva uma linha: "- Nome técnico: justificativa".

**3. Procedimento de inspeção**
Lista numerada de 5-8 passos. OBRIGATÓRIO começar por isolamento de segurança (LOTO, despressurização, bloqueio elétrico). Inclua medições específicas (valores e tolerâncias quando aplicável).

**4. Quando escalar para o fabricante**
Liste 3-5 critérios objetivos (com valores numéricos quando aplicável) que indicam que a manutenção interna não é suficiente.

Use linguagem técnica em português. Foque em ações práticas imediatas. Seja DETALHADO em cada seção."""

    resposta_ia, anotacoes, ia_status = get_ai_response(prompt, diagrama_path)
    logger.info(f"[ocorrencia] IA respondeu — status={ia_status}, len={len(resposta_ia)}, anotacoes={len(anotacoes)}")
    anotacoes_json = json.dumps(anotacoes, ensure_ascii=False) if anotacoes else None

    # ── Persistência ─────────────────────────────────────────────────────────
    try:
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO ocorrencias (
                maquina_id, data_ocorrencia, nome_operador, setor_area, descricao,
                tipo_ocorrencia, nivel_impacto, problema_recorrente,
                detalhamento_tecnico, resposta_ia, ia_status, anotacoes_ia, diagrama_url, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'Aberta')""",
            (maquina_id, data_ocorrencia, nome_operador, setor_area, descricao,
             tipo_ocorrencia, nivel_impacto, problema_recorrente,
             detalhamento_tecnico, resposta_ia, ia_status, anotacoes_json, diagrama_url),
        )
        ocorrencia_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"[ocorrencia] criada id={ocorrencia_id} ia_status={ia_status}")
    except Exception as e:
        logger.exception("Falha ao persistir a ocorrência")
        flash(f"Erro ao salvar a ocorrência: {e}", "danger")
        return redirect(url_for("CadastroOcorrencia"))

    dados = {
        "id": ocorrencia_id,
        "maquina_nome": maquina_nome,
        "data_ocorrencia": data_ocorrencia,
        "nome_operador": nome_operador,
        "setor_area": setor_area,
        "descricao": descricao,
        "tipo_ocorrencia": tipo_ocorrencia,
        "nivel_impacto": nivel_impacto,
        "problema_recorrente": problema_recorrente,
        "detalhamento_tecnico": detalhamento_tecnico,
    }
    return render_template(
        "solucao.html",
        dados=dados,
        resposta_ia=resposta_ia,
        ia_status=ia_status,
        diagrama_url=diagrama_url,
        anotacoes=anotacoes,
    )


# ── Máquinas ──────────────────────────────────────────────────────────────────

@app.route("/maquinas")
@login_required
def maquinas():
    conn = get_db()
    lista = conn.execute("SELECT * FROM maquinas ORDER BY nome").fetchall()
    conn.close()
    return render_template("maquinas.html", maquinas=lista)


@app.route("/maquinas/cadastro", methods=["GET", "POST"])
@login_required
def cadastro_maquina():
    if request.method == "POST":
        nome       = request.form.get("nome", "").strip()
        modelo     = request.form.get("modelo", "").strip()
        fabricante = request.form.get("fabricante", "").strip()
        ano        = request.form.get("ano", "").strip()
        setor      = request.form.get("setor", "").strip()
        descricao  = request.form.get("descricao", "").strip()

        if not nome:
            flash("O nome da máquina é obrigatório.", "danger")
            return redirect(url_for("cadastro_maquina"))

        try:
            conn = get_db()
            cursor = conn.execute(
                "INSERT INTO maquinas (nome, modelo, fabricante, ano, setor, descricao) VALUES (?,?,?,?,?,?)",
                (nome, modelo, fabricante, ano, setor, descricao),
            )
            maquina_id = cursor.lastrowid
            conn.commit()

            arquivos = request.files.getlist("diagramas")
            pasta = os.path.join(app.config["UPLOAD_FOLDER"], str(maquina_id))
            os.makedirs(pasta, exist_ok=True)
            for arquivo in arquivos:
                if arquivo and allowed_file(arquivo.filename):
                    nome_arquivo = secure_filename(arquivo.filename)
                    caminho = os.path.join(pasta, nome_arquivo)
                    arquivo.save(caminho)
                    tipo = nome_arquivo.rsplit(".", 1)[-1].upper()
                    conn.execute(
                        "INSERT INTO diagramas (maquina_id, nome, caminho, tipo) VALUES (?,?,?,?)",
                        (maquina_id, nome_arquivo, caminho, tipo),
                    )
            conn.commit()
            conn.close()
            flash(f"Máquina '{nome}' cadastrada com sucesso.", "success")
        except Exception as e:
            logger.exception("Erro ao cadastrar máquina")
            flash(f"Erro ao cadastrar máquina: {e}", "danger")
        return redirect(url_for("maquinas"))

    return render_template("cadastro_maquina.html")


@app.route("/enviar", methods=["POST"])
@login_required
def enviar():
    """
    Cria um ticket de suporte: salva no DB e dispara email (best-effort).
    Retorna JSON com {ok, protocolo, email_enviado}.
    """
    nome       = request.form.get("nome", "").strip()
    email      = request.form.get("email", "").strip()
    telefone   = request.form.get("telefone", "").strip()
    setor      = request.form.get("setor", "").strip()
    tipo       = request.form.get("tipo", "").strip()
    prioridade = request.form.get("prioridade", "").strip()
    assunto    = request.form.get("assunto", "").strip()
    motivo     = request.form.get("motivo", "").strip()

    obrigatorios = [nome, email, setor, tipo, prioridade, assunto, motivo]
    if not all(obrigatorios):
        return jsonify({"ok": False, "erro": "Campos obrigatórios faltando."}), 400

    # Protocolo único: NXR + 6 hex chars (~16M combinações)
    protocolo = f"NXR-{secrets.token_hex(3).upper()}"

    # Anexos (opcional): salva em static/uploads/suporte/<protocolo>/
    anexos_paths: list[str] = []
    anexos_meta: list[dict] = []
    arquivos = request.files.getlist("anexos")
    if arquivos:
        ticket_dir = os.path.join(SUPORTE_FOLDER, protocolo)
        os.makedirs(ticket_dir, exist_ok=True)
        for f in arquivos:
            if not f or not f.filename:
                continue
            fname = secure_filename(f.filename)
            if not fname:
                continue
            path = os.path.join(ticket_dir, fname)
            f.save(path)
            anexos_paths.append(path)
            anexos_meta.append({
                "nome": fname,
                "tamanho": os.path.getsize(path),
                "url": "/" + path.replace("\\", "/"),
            })

    anexos_json = json.dumps(anexos_meta, ensure_ascii=False) if anexos_meta else None
    ticket = {
        "protocolo": protocolo, "nome": nome, "email": email, "telefone": telefone,
        "setor": setor, "tipo": tipo, "prioridade": prioridade,
        "assunto": assunto, "motivo": motivo,
    }

    # Persistência: o ticket é salvo SEMPRE, mesmo se o email falhar
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO tickets_suporte (
                protocolo, usuario_id, nome, email, telefone, setor, tipo,
                prioridade, assunto, motivo, anexos_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (protocolo, current_user.id, nome, email, telefone, setor, tipo,
             prioridade, assunto, motivo, anexos_json),
        )
        conn.commit()
        conn.close()
        logger.info(f"[suporte] ticket criado — protocolo={protocolo} prioridade={prioridade}")
    except Exception as e:
        logger.exception("[suporte] falha ao persistir ticket")
        return jsonify({"ok": False, "erro": f"Erro ao salvar: {e}"}), 500

    # Notificação por email (best-effort — não bloqueia o sucesso)
    email_ok = enviar_email_suporte(ticket, anexos_paths)
    if email_ok:
        try:
            conn = get_db()
            conn.execute(
                "UPDATE tickets_suporte SET email_enviado = 1 WHERE protocolo = ?",
                (protocolo,),
            )
            conn.commit()
            conn.close()
        except Exception:
            logger.exception("[suporte] falha ao atualizar flag email_enviado")

    return jsonify({
        "ok": True,
        "protocolo": protocolo,
        "email_enviado": email_ok,
    })


if __name__ == "__main__":
    app.run(debug=False)
