"""
Base dos testes: um banco de demonstração temporário (nunca o qrqc.db de verdade), clientes já
logados por perfil e IA simulada (Gemini e OpenAI falsos, sem chave e sem rede).

Rodar:  pip install -r requirements.txt -r requirements-dev.txt && pytest
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SENHA = "senha-de-teste-123"

# O app lê o ambiente ao ser importado: tudo isso precisa vir ANTES do import
_TMP = Path(tempfile.mkdtemp(prefix="nexar-testes-"))
os.environ.update({
    "DATABASE_PATH": str(_TMP / "teste.db"),
    "ADMIN_PASSWORD": SENHA,
    "SECRET_KEY": "chave-de-teste",
    "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "OPENAI_API_KEY": "",
})
os.environ.pop("GEMINI_MODEL", None)
os.environ.pop("RAILWAY_ENVIRONMENT", None)

# Base de demonstração (8 máquinas com CAD, 33 ocorrências, pessoas e usuários por perfil)
subprocess.run([sys.executable, str(RAIZ / "scripts" / "seed_demo.py"), "--sem-ia"], cwd=RAIZ, check=True,
               env=os.environ.copy(), stdout=subprocess.DEVNULL)

sys.path.insert(0, str(RAIZ))
import app as nexar  # noqa: E402
import nexa_ia  # noqa: E402

nexar.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
nexar.limiter.enabled = False

PASTAS_GERADAS = [RAIZ / "static" / "uploads", RAIZ / "static" / "models3d", RAIZ / "cad_importados"]


def _arquivos(pastas):
    return {p for pasta in pastas if pasta.exists() for p in pasta.rglob("*")}


@pytest.fixture(scope="session", autouse=True)
def _limpar_arquivos_gerados():
    """Fotos, anexos e modelos enviados pelos testes não ficam no repositório."""
    antes = _arquivos(PASTAS_GERADAS)
    yield
    for p in sorted(_arquivos(PASTAS_GERADAS) - antes, key=lambda x: len(x.parts), reverse=True):
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(scope="session")
def A():
    return nexar


@pytest.fixture
def db(A):
    conn = A.get_db()
    yield conn
    conn.close()


def _login(email):
    c = nexar.app.test_client()
    r = c.post("/login", data={"email": email, "senha": SENHA})
    assert r.status_code == 302, f"login de {email} falhou"
    return c


@pytest.fixture
def admin():
    return _login("admin@nexar.com")


@pytest.fixture
def operador():
    return _login("operador@nexar.com")


@pytest.fixture
def rh():
    return _login("rh@nexar.com")


@pytest.fixture
def anonimo(A):
    return A.app.test_client()


@pytest.fixture
def token_app(A):
    """Token do app (operador) + cliente sem sessão web."""
    c = A.app.test_client()
    r = c.post("/api/mobile/login", json={"email": "operador@nexar.com", "password": SENHA})
    return r.get_json()["token"], c


@pytest.fixture
def maquina_cad(db, A):
    """(id da máquina com CAD, id de uma peça do modelo 3D)."""
    m = db.execute("SELECT id, modelo_3d FROM maquinas WHERE modelo_3d LIKE '%torno%' LIMIT 1").fetchone()
    comps = A.modelos_3d.componentes_da_config(A.modelos_3d.ler_config(m["modelo_3d"]))
    return m["id"], comps[0]["component_id"]


@pytest.fixture
def foto_jpg():
    return (RAIZ / "test_diagrams" / "motor_eletrico_industrial.jpg").read_bytes()


# ── IA simulada ──────────────────────────────────────────────────────────────
class GeminiFalso:
    """Devolve, em ordem, as respostas do roteiro (texto ou exceção). Anota os modelos chamados."""
    def __init__(self, roteiro):
        self.roteiro, self.modelos = list(roteiro), []
        self.models = types.SimpleNamespace(generate_content=self._gerar)
        self.chats = types.SimpleNamespace(create=lambda model, history, config: types.SimpleNamespace(
            send_message=lambda m: self._gerar(model, [m], config)))

    def _gerar(self, model, contents, config):
        self.modelos.append(model)
        r = self.roteiro.pop(0) if self.roteiro else ""
        if isinstance(r, Exception):
            raise r
        return types.SimpleNamespace(text=r, parsed=None)


def resposta_openai(conteudo=None, ferramentas=None):
    return types.SimpleNamespace(choices=[types.SimpleNamespace(
        message=types.SimpleNamespace(content=conteudo, tool_calls=ferramentas, role="assistant"))])


def chamada_ferramenta(nome, args, i=1):
    return types.SimpleNamespace(id=f"call_{i}", type="function",
                                 function=types.SimpleNamespace(name=nome, arguments=json.dumps(args)))


class OpenAIFalso:
    def __init__(self, roteiro):
        self.roteiro, self.pedidos = list(roteiro), []
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._criar))

    def _criar(self, **kw):
        self.pedidos.append(kw)
        r = self.roteiro.pop(0) if self.roteiro else resposta_openai("{}")
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def gemini(A, monkeypatch):
    """gemini(roteiro) liga um Gemini falso só durante o teste."""
    def ligar(roteiro):
        falso = GeminiFalso(roteiro)
        monkeypatch.setattr(A, "gemini_client", falso)
        return falso
    return ligar


@pytest.fixture
def openai(monkeypatch):
    """openai(roteiro) liga uma OpenAI falsa só durante o teste."""
    def ligar(roteiro):
        falso = OpenAIFalso([r if not isinstance(r, (str, dict, list)) else
                             resposta_openai(r if isinstance(r, str) else json.dumps(r)) for r in roteiro])
        monkeypatch.setattr(nexa_ia, "_openai_client", falso)
        return falso
    return ligar


def esperar_diagnostico(db, oc_id, tentativas=60):
    """O diagnóstico roda em segundo plano: espera sair de 'pendente'."""
    import time
    for _ in range(tentativas):
        st = db.execute("SELECT ia_status FROM ocorrencias WHERE id = ?", (oc_id,)).fetchone()[0]
        if st != "pendente":
            return st
        time.sleep(0.1)
    return "pendente"
