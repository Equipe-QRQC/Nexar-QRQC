"""Correções de segurança da revisão (PR #12 e #13)."""
import io

from openpyxl import load_workbook

from tests.conftest import SENHA


def test_usuario_desativado_perde_sessao_web_e_token_do_app(A, db, token_app):
    from tests.conftest import _login
    web = _login("operador@nexar.com")
    token, app = token_app
    assert web.get("/CadastroOcorrencia").status_code == 200
    db.execute("UPDATE usuarios SET ativo = 0 WHERE email = 'operador@nexar.com'"); db.commit()
    try:
        assert web.get("/CadastroOcorrencia").status_code == 302
        assert app.get("/api/mobile/maquinas", headers={"Authorization": "Bearer " + token}).status_code == 401
    finally:
        db.execute("UPDATE usuarios SET ativo = 1 WHERE email = 'operador@nexar.com'"); db.commit()


def test_trocar_a_senha_encerra_o_app(admin, db, A):
    c = A.app.test_client()
    token = c.post("/api/mobile/login", json={"email": "rh@nexar.com", "password": SENHA}).get_json()["token"]
    uid = db.execute("SELECT id FROM usuarios WHERE email = 'rh@nexar.com'").fetchone()[0]
    dados = {"id": uid, "nome": "RH", "email": "rh@nexar.com", "perfil": "rh", "ativo": "1"}
    admin.post("/configuracoes/usuarios", data={**dados, "senha": "OutraSenha123"})
    try:
        assert c.get("/api/mobile/maquinas", headers={"Authorization": "Bearer " + token}).status_code == 401
    finally:
        admin.post("/configuracoes/usuarios", data={**dados, "senha": SENHA})


def test_token_do_app_fica_so_como_hash_no_banco(A, db, token_app):
    token, app = token_app
    assert not db.execute("SELECT 1 FROM mobile_tokens WHERE token = ?", (token,)).fetchone()
    assert db.execute("SELECT 1 FROM mobile_tokens WHERE token = ?", (A._hash_token(token),)).fetchone()
    # O hash guardado no banco não serve como token
    assert app.get("/api/mobile/maquinas", headers={"Authorization": "Bearer " + A._hash_token(token)}).status_code == 401
    assert app.post("/api/mobile/logout", headers={"Authorization": "Bearer " + token}).status_code == 200
    assert app.get("/api/mobile/maquinas", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_token_antigo_em_texto_puro_e_convertido_sem_novo_login(A, db):
    import secrets
    uid = db.execute("SELECT id FROM usuarios WHERE email = 'operador@nexar.com'").fetchone()[0]
    antigo = secrets.token_hex(32)
    db.execute("INSERT INTO mobile_tokens (user_id, token, token_hash, expires_at) "
               "VALUES (?, ?, 0, datetime('now', '+1 day'))", (uid, antigo)); db.commit()
    A._ensure_mobile_tables()   # = servidor reiniciando com a versão nova
    assert not db.execute("SELECT 1 FROM mobile_tokens WHERE token = ?", (antigo,)).fetchone()
    r = A.app.test_client().get("/api/mobile/maquinas", headers={"Authorization": "Bearer " + antigo})
    assert r.status_code == 200


def test_excel_nao_executa_formula(admin, db):
    oc = db.execute("SELECT id, descricao FROM ocorrencias LIMIT 1").fetchone()
    db.execute("UPDATE ocorrencias SET descricao = ? WHERE id = ?", ('=HYPERLINK("http://x","clique")', oc["id"])); db.commit()
    try:
        wb = load_workbook(io.BytesIO(admin.get("/historico/export").get_data()))
        celulas = [c.value for linha in wb.active.iter_rows() for c in linha if isinstance(c.value, str) and "HYPERLINK" in c.value]
        assert celulas and not celulas[0].startswith("=")
    finally:
        db.execute("UPDATE ocorrencias SET descricao = ? WHERE id = ?", (oc["descricao"], oc["id"])); db.commit()


def test_operador_nao_altera_componentes_da_maquina(operador, maquina_cad):
    mid, _ = maquina_cad
    assert operador.post(f"/api/machines/{mid}/components", json={"component_id": "x", "name": "y"}).status_code == 302
    assert operador.delete(f"/api/machines/{mid}/components/x").status_code == 302


def test_uploads_exigem_login_ou_token(anonimo, token_app, db):
    caminho = db.execute("SELECT caminho FROM diagramas LIMIT 1").fetchone()
    url = "/" + caminho[0] if caminho else "/static/uploads/maquinas/1/Ficha_Tecnica_Torno_CNC_GL240M.pdf"
    token, app = token_app
    assert anonimo.get(url).status_code == 401
    assert app.get(url, headers={"Authorization": "Bearer " + token}).status_code == 200


def test_voltar_nao_redireciona_para_site_externo(admin):
    r = admin.get("/lang/pt", headers={"Referer": "https://site-malicioso.com/x"})
    assert "site-malicioso" not in r.headers["Location"]


def test_nome_de_arquivo_so_com_acentos_mantem_a_extensao(A):
    assert A.nome_arquivo_seguro("ção.png", "png").endswith(".png")
    assert A.nome_arquivo_seguro("日本.jpg", "jpg").endswith(".jpg")
