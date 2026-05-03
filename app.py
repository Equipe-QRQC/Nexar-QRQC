import os
import io
import json
import logging
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
from twilio.rest import Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("nexar.qrqc")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexar-qrqc-secret-2026")

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

SYSTEM_INSTRUCTION = (
    "Você é um engenheiro sênior de manutenção industrial e qualidade (QRQC). "
    "Responde em português técnico, objetivo e prático. "
    "Quando há diagrama anexado, referencia componentes e cotas observados. "
    "Estruture diagnósticos em 4 seções com markdown: "
    "**1. Causa provável**, **2. Componentes a verificar**, "
    "**3. Procedimento de inspeção**, **4. Quando escalar**."
)

GEN_CONFIG = genai_types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.4,
    top_p=0.9,
    max_output_tokens=1024,
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

# ── Twilio ────────────────────────────────────────────────────────────────────
ACCOUNT_SID            = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN             = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_DESTINATARIO    = os.getenv("TWILIO_DESTINATARIO")
twilio_client = None
if ACCOUNT_SID and AUTH_TOKEN:
    try:
        twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
    except Exception as e:
        logger.warning(f"Twilio não inicializado: {e}")

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
) -> list[dict]:
    """
    Segunda chamada à IA: usa visão computacional para localizar componentes
    mencionados no diagnóstico, retornando bounding boxes precisos.
    Retorna lista de anotações no formato {x, y, raio, tipo, titulo, descricao}.
    """
    if not gemini_client or img_obj is None:
        return []

    prompt_bbox = (
        "Analise o diagrama técnico industrial em anexo.\n\n"
        "DIAGNÓSTICO PRÉVIO DE UM ENGENHEIRO:\n"
        f"{diagnostico_texto[:1500]}\n\n"
        "TAREFA: Localize de 3 a 6 componentes do diagrama que sejam relevantes "
        "para esse diagnóstico. Para cada componente, retorne JSON com:\n"
        "- box_2d: [ymin, xmin, ymax, xmax] em 0-1000 (cubra EXATAMENTE o desenho do componente)\n"
        "- label: nome do componente como aparece no diagrama (ex: 'BOMBA', 'FILTRO', 'VEDACOES')\n"
        "- tipo: 'critico' (componente com falha provável), 'atencao' (inspecionar), 'info' (referência)\n"
        "- descricao: 1 frase explicando a relevância (max 80 caracteres)\n\n"
        "IMPORTANTE: cubra os componentes REAIS do diagrama, não áreas vazias. "
        "Priorize 1-2 'critico', 2-3 'atencao' e 1 'info'."
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
                logger.info(f"[bbox] {len(anotacoes)} componente(s) localizado(s) por {modelo}")
                return anotacoes
            logger.warning(f"[bbox/{modelo}] retornou 0 componentes válidos")
        except Exception as e:
            if _should_try_next_model(e):
                logger.warning(f"[bbox/{modelo}] erro transitório — tentando próximo")
                continue
            logger.exception(f"[bbox/{modelo}] erro definitivo, abortando detecção")
            break
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
    if imagem_path and os.path.exists(imagem_path):
        ext = imagem_path.rsplit(".", 1)[-1].lower()
        if ext in ("png", "jpg", "jpeg"):
            try:
                img_obj = Image.open(imagem_path)
                if img_obj.mode in ("RGBA", "P"):
                    img_obj = img_obj.convert("RGB")
            except Exception as e:
                logger.warning(f"Não foi possível abrir imagem {imagem_path}: {e}")

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
        # Reordena a cadeia de modelos: começa com o que funcionou na 1ª chamada
        modelos_bbox = [modelo_usado] + [m for m in GEMINI_MODELS if m != modelo_usado]
        anotacoes = _detectar_componentes(img_obj, texto_diagnostico, modelos_bbox)

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
            "SELECT o.*, m.nome as maquina_nome FROM ocorrencias o "
            "LEFT JOIN maquinas m ON o.maquina_id = m.id "
            "ORDER BY o.data_registro DESC"
        ).fetchall()
        conn.close()
        return render_template("historico.html", ocorrencias=ocorrencias)
    except Exception as e:
        logger.exception(f"Erro ao listar histórico: {e}")
        return render_template("historico.html", ocorrencias=[])


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
    prompt = f"""Você é um engenheiro sênior de manutenção industrial.

{maquina_info}
Ocorrência registrada por {nome_operador} em {data_ocorrencia}.
Setor: {setor_area} | Tipo: {tipo_ocorrencia} | Impacto: {nivel_impacto} | Recorrente: {problema_recorrente}
Detalhamento técnico: {detalhamento_tecnico}
Descrição: {descricao}

{"Analise o diagrama técnico da máquina anexado e " if diagrama_path else ""}Gere um diagnóstico técnico estruturado em 4 seções claras, separadas por linha em branco:

1. **Causa provável**
2. **Componentes a verificar**{" (referencie cotas do diagrama quando relevante)" if diagrama_path else ""}
3. **Procedimento de inspeção passo a passo**
4. **Quando escalar para o fabricante**

Use linguagem técnica objetiva, em português. Foque em ações práticas imediatas."""

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
    nome       = request.form.get("nome", "").strip()
    setor      = request.form.get("setor", "").strip()
    prioridade = request.form.get("prioridade", "").strip()
    motivo     = request.form.get("motivo", "").strip()
    setores     = {"1": "RH", "2": "TI", "3": "Financeiro", "Qualidade": "Qualidade"}
    prioridades = {"0": "Baixa", "1": "Média", "2": "Alta"}
    corpo_msg = (
        f"📌 Nexar - Solicitação de Suporte\n"
        f"👤 Nome: {nome}\n"
        f"🏢 Setor: {setores.get(setor, setor)}\n"
        f"⚠️ Prioridade: {prioridades.get(prioridade, prioridade)}\n"
        f"📝 Motivo: {motivo}"
    )
    if not twilio_client:
        return render_template(
            "sucesso.html",
            mensagem="⚠️ Twilio não configurado — verifique TWILIO_* no .env. "
                     "Solicitação registrada localmente:\n\n" + corpo_msg,
        )
    try:
        msg = twilio_client.messages.create(
            body=corpo_msg, from_=TWILIO_WHATSAPP_NUMBER, to=TWILIO_DESTINATARIO
        )
        return render_template("sucesso.html", mensagem=f"Suporte solicitado! SID: {msg.sid}")
    except Exception as e:
        logger.exception("Erro ao enviar solicitação via Twilio")
        return render_template("sucesso.html", mensagem=f"Erro: {e}")


if __name__ == "__main__":
    app.run(debug=False)
