"""Registro de ocorrência (diagnóstico em segundo plano), resolução e histórico paginado."""
import io
import re

from openpyxl import load_workbook

from tests.conftest import esperar_diagnostico


def test_registro_responde_na_hora_e_diagnostico_chega_depois(admin, db, gemini, maquina_cad):
    import time
    falso = gemini([])
    falso._gerar_original = falso._gerar
    falso.models.generate_content = lambda **kw: (time.sleep(1), falso._gerar_original(**{k: kw[k] for k in ("model", "contents", "config")}))[1]
    falso.roteiro = ["**1. Causa provável**\nFolga."]
    mid, comp = maquina_cad
    t = time.time()
    r = admin.post("/registrar_ocorrencia", data={"maquina_id": mid, "componente_apontado": comp, "sintoma": "folga"})
    assert time.time() - t < 0.8, "o registro não pode esperar a IA"
    oc = int(r.headers["Location"].rsplit("/", 1)[-1])
    assert admin.get(f"/api/ocorrencias/{oc}/diagnostico-status").get_json()["ia_status"] == "pendente"
    assert "Gerando o diagnóstico" in admin.get(f"/ocorrencia/{oc}").get_data(as_text=True)
    assert esperar_diagnostico(db, oc) == "ok"


def test_diagnostico_pendente_no_reinicio_nao_fica_travado(A, db):
    oc = db.execute("SELECT id FROM ocorrencias WHERE componente_apontado IS NOT NULL LIMIT 1").fetchone()[0]
    db.execute("UPDATE ocorrencias SET ia_status = 'pendente', resposta_ia = NULL WHERE id = ?", (oc,)); db.commit()
    A._concluir_pendentes_do_reinicio()
    st, txt = db.execute("SELECT ia_status, resposta_ia FROM ocorrencias WHERE id = ?", (oc,)).fetchone()
    assert st == "local" and "Causa provável" in txt


def test_iniciar_e_resolver(admin, db, gemini, maquina_cad):
    gemini([Exception("500")])
    mid, comp = maquina_cad
    r = admin.post("/registrar_ocorrencia", data={"maquina_id": mid, "componente_apontado": comp, "sintoma": "folga"})
    oc = int(r.headers["Location"].rsplit("/", 1)[-1])
    assert admin.post(f"/ocorrencias/{oc}/iniciar").get_json()["status"] == "Em andamento"
    r = admin.post(f"/ocorrencias/{oc}/resolver", json={"solucao_aplicada": "Ajuste da régua", "horas_trabalho": "2,5"})
    assert r.get_json()["status"] == "Resolvida"
    assert db.execute("SELECT horas_trabalho FROM ocorrencias WHERE id = ?", (oc,)).fetchone()[0] == 2.5


def test_app_cria_ocorrencia(token_app, maquina_cad):
    token, app = token_app
    mid, comp = maquina_cad
    r = app.post("/api/mobile/ocorrencias", headers={"Authorization": "Bearer " + token},
                 json={"maquina_id": mid, "componente_apontado": comp, "sintoma": "folga"})
    assert r.status_code == 200 and r.get_json()["id"]


def test_app_limit_invalido_nao_da_500(token_app):
    token, app = token_app
    for limit in ("abc", "-1", "99999"):
        r = app.get(f"/api/mobile/ocorrencias?limit={limit}", headers={"Authorization": "Bearer " + token})
        assert r.status_code == 200 and len(r.get_json()) <= 100


def _ids(cliente, query=""):
    html = cliente.get("/historico" + query).get_data(as_text=True)
    return html, re.findall(r'<tr data-id="(\d+)"', html)


def test_historico_paginado_no_servidor(admin, db, A):
    total = db.execute("SELECT COUNT(*) FROM ocorrencias").fetchone()[0]
    html, p1 = _ids(admin)
    assert len(p1) == min(A.HISTORICO_POR_PAGINA, total) and f"{total} registro(s)" in html
    _, p2 = _ids(admin, "?pagina=2")
    assert not set(p1) & set(p2)
    assert admin.get("/historico?pagina=abc").status_code == 200


def test_historico_filtros_e_excel_iguais(admin, db):
    abertas = db.execute("SELECT COUNT(*) FROM ocorrencias WHERE COALESCE(status, 'Aberta') = 'Aberta'").fetchone()[0]
    html, _ = _ids(admin, "?status=Aberta")
    assert f"{abertas} registro(s)" in html
    wb = load_workbook(io.BytesIO(admin.get("/historico/export?status=Aberta").get_data()))
    assert wb.active.max_row - 5 == abertas     # 5 linhas de cabeçalho


def test_historico_busca_sem_acento(admin, db):
    nome = db.execute("SELECT nome FROM maquinas WHERE nome LIKE 'Rob%' LIMIT 1").fetchone()[0]   # "Robô ..."
    _, ids = _ids(admin, "?search=robo")
    assert ids, f"'robo' deveria achar '{nome}'"
    html, vazio = _ids(admin, "?search=zzzz-nada")
    assert not vazio and "Nenhuma ocorrência encontrada" in html


def test_mapa_da_fabrica_rejeita_formato_invalido(admin):
    assert admin.post("/api/fabrica/posicoes", json=[1, 2]).status_code == 400
    assert admin.post("/api/fabrica/posicoes", json={"posicoes": {"1": [10, 20]}}).get_json()["salvas"] == 1


def _ocorrencia_pelo_app(app, token, maquina_cad, **extra):
    mid, comp = maquina_cad
    r = app.post("/api/mobile/ocorrencias", headers={"Authorization": "Bearer " + token},
                 json={"maquina_id": mid, "componente_apontado": comp, "sintoma": "folga", **extra})
    return r.get_json()["id"]


def test_app_anexa_foto_do_problema(token_app, maquina_cad, foto_jpg, admin, db):
    token, app = token_app
    oc = _ocorrencia_pelo_app(app, token, maquina_cad)
    r = app.post(f"/api/mobile/ocorrencias/{oc}/foto", headers={"Authorization": "Bearer " + token},
                 data={"foto": (io.BytesIO(foto_jpg), "problema.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 200
    url = r.get_json()["foto_url"]
    assert db.execute("SELECT foto_url FROM ocorrencias WHERE id = ?", (oc,)).fetchone()[0] == url
    assert url in admin.get(f"/ocorrencia/{oc}").get_data(as_text=True)      # aparece na página da web
    assert admin.get(url).status_code == 200


def test_foto_da_ocorrencia_valida_o_envio(token_app, maquina_cad, anonimo):
    token, app = token_app
    oc = _ocorrencia_pelo_app(app, token, maquina_cad)
    h = {"Authorization": "Bearer " + token}
    falsa = {"foto": (io.BytesIO(b"nao sou uma foto"), "x.jpg")}
    assert app.post(f"/api/mobile/ocorrencias/{oc}/foto", headers=h, data=falsa, content_type="multipart/form-data").status_code == 400
    assert app.post(f"/api/mobile/ocorrencias/{oc}/foto", headers=h, data={}, content_type="multipart/form-data").status_code == 400
    assert app.post("/api/mobile/ocorrencias/999999/foto", headers=h, data={}, content_type="multipart/form-data").status_code == 404
    assert anonimo.post(f"/api/mobile/ocorrencias/{oc}/foto").status_code == 401


def test_ocorrencia_da_inspecao_herda_a_foto(token_app, maquina_cad, db):
    token, app = token_app
    pid = db.execute("INSERT INTO percepcoes (imagem_url, anomalias_json, score_saude) "
                     "VALUES ('/static/uploads/sensor/teste.jpg', '[]', 90)").lastrowid
    db.commit()
    oc = _ocorrencia_pelo_app(app, token, maquina_cad, inspecao_id=pid)
    assert db.execute("SELECT foto_url FROM ocorrencias WHERE id = ?", (oc,)).fetchone()[0] == "/static/uploads/sensor/teste.jpg"
