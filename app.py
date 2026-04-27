import os
import base64
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from openai import OpenAI
from dotenv import load_dotenv
from twilio.rest import Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexar-qrqc-secret-2026")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_DESTINATARIO = os.getenv("TWILIO_DESTINATARIO")
twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect("qrqc.db")
    conn.row_factory = sqlite3.Row
    return conn


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
            diagrama_url TEXT,
            status TEXT DEFAULT 'Aberta',
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maquina_id) REFERENCES maquinas(id)
        );
    """)
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
            return redirect(url_for("telaInicial"))
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
    return redirect(request.referrer or url_for("telaInicial"))


# ── AI Chat ───────────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    mensagem = data.get("mensagem", "")
    historico = data.get("historico", [])
    messages = [
        {"role": "system", "content": (
            "Você é um assistente técnico industrial da Nexar, especializado em manutenção, "
            "qualidade e resolução de ocorrências industriais (QRQC). "
            "Responda de forma objetiva, técnica e prática em português."
        )}
    ] + historico + [{"role": "user", "content": mensagem}]
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages, max_tokens=600
        )
        return jsonify({"resposta": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"resposta": f"Erro: {e}"}), 500


# ── AI Response ───────────────────────────────────────────────────────────────

def get_ai_response(prompt, imagem_path=None):
    try:
        content = [{"type": "text", "text": prompt}]
        if imagem_path and os.path.exists(imagem_path):
            with open(imagem_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = imagem_path.rsplit(".", 1)[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{img_b64}"}
            })
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Erro na IA: {e}]"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("inicialtotem.html")


@app.route("/telaInicial")
@login_required
def telaInicial():
    return render_template("telaInicial.html")


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
        print(f"Erro histórico: {e}")
        return render_template("historico.html", ocorrencias=[])


@app.route("/Solicitação_Suporte")
@login_required
def solicitacao():
    return render_template("Solicitação_Suporte.html")


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
    try:
        maquina_id = request.form.get("maquina_id") or None
        data_ocorrencia = request.form.get("data_ocorrencia")
        nome_operador = request.form.get("nome_operador")
        setor_area = request.form.get("setor_area")
        descricao = request.form.get("descricao")
        tipo_ocorrencia = request.form.get("tipo_ocorrencia")
        nivel_impacto = request.form.get("nivel_impacto")
        problema_recorrente = request.form.get("problema_recorrente")
        detalhamento_tecnico = request.form.get("detalhamento_tecnico")

        maquina_info = ""
        diagrama_path = None
        maquina_nome = ""
        diagrama_url = None

        if maquina_id:
            conn = get_db()
            maquina = conn.execute("SELECT * FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
            diagrama = conn.execute(
                "SELECT * FROM diagramas WHERE maquina_id = ? AND tipo != 'PDF' LIMIT 1", (maquina_id,)
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
                    f"Máquina: {maquina['nome']} | Modelo: {maquina['modelo']} | "
                    f"Fabricante: {maquina['fabricante']} | Ano: {maquina['ano']}\n"
                    f"Setor: {maquina['setor']}\n"
                )
            if diagrama:
                diagrama_path = diagrama["caminho"]
                diagrama_url = "/" + diagrama_path.replace("\\", "/")
            if historico_maquina:
                maquina_info += "\nÚltimas ocorrências desta máquina:\n"
                for h in historico_maquina:
                    maquina_info += f"- {h['descricao'][:80]}\n"

        prompt = f"""Você é um engenheiro sênior de manutenção industrial.

{maquina_info}
Ocorrência registrada por {nome_operador} em {data_ocorrencia}.
Setor: {setor_area} | Tipo: {tipo_ocorrencia} | Impacto: {nivel_impacto} | Recorrente: {problema_recorrente}
Detalhamento técnico: {detalhamento_tecnico}
Descrição: {descricao}

{"Analise o diagrama técnico da máquina anexado e " if diagrama_path else ""}Gere um diagnóstico técnico com:
1. Causa provável
2. Componentes a verificar {"(referencie as cotas do diagrama)" if diagrama_path else ""}
3. Procedimento de inspeção passo a passo
4. Quando escalar para o fabricante

Seja objetivo. Foque em ações práticas imediatas."""

        resposta_ia = get_ai_response(prompt, diagrama_path)

        conn = get_db()
        conn.execute(
            """INSERT INTO ocorrencias (
                maquina_id, data_ocorrencia, nome_operador, setor_area, descricao,
                tipo_ocorrencia, nivel_impacto, problema_recorrente,
                detalhamento_tecnico, resposta_ia, diagrama_url, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,'Aberta')""",
            (maquina_id, data_ocorrencia, nome_operador, setor_area, descricao,
             tipo_ocorrencia, nivel_impacto, problema_recorrente,
             detalhamento_tecnico, resposta_ia, diagrama_url),
        )
        conn.commit()
        conn.close()

        dados = {
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
        return render_template("solucao.html", dados=dados,
                               resposta_ia=resposta_ia, diagrama_url=diagrama_url)
    except Exception as e:
        print(f"Erro ao registrar: {e}")
        return redirect(url_for("CadastroOcorrencia"))


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
        nome = request.form.get("nome")
        modelo = request.form.get("modelo")
        fabricante = request.form.get("fabricante")
        ano = request.form.get("ano")
        setor = request.form.get("setor")
        descricao = request.form.get("descricao")

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
        return redirect(url_for("maquinas"))

    return render_template("cadastro_maquina.html")


@app.route("/enviar", methods=["POST"])
@login_required
def enviar():
    nome = request.form["nome"]
    setor = request.form["setor"]
    prioridade = request.form["prioridade"]
    motivo = request.form["motivo"]
    setores = {"1": "RH", "2": "TI", "3": "Financeiro", "Qualidade": "Qualidade"}
    prioridades = {"0": "Baixa", "1": "Média", "2": "Alta"}
    corpo_msg = (
        f"📌 Nexar - Solicitação de Suporte\n"
        f"👤 Nome: {nome}\n"
        f"🏢 Setor: {setores.get(setor, setor)}\n"
        f"⚠️ Prioridade: {prioridades.get(prioridade, prioridade)}\n"
        f"📝 Motivo: {motivo}"
    )
    try:
        msg = twilio_client.messages.create(
            body=corpo_msg, from_=TWILIO_WHATSAPP_NUMBER, to=TWILIO_DESTINATARIO
        )
        return render_template("sucesso.html", mensagem=f"Suporte solicitado! SID: {msg.sid}")
    except Exception as e:
        return render_template("sucesso.html", mensagem=f"Erro: {e}")


if __name__ == "__main__":
    app.run(debug=False)
