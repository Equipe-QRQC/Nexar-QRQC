"""Todas as páginas abrem sem erro 500 nos 4 perfis, e cada perfil só vê o que pode."""
import pytest

PAGINAS = ["/dashboard", "/analise", "/historico", "/historico/export", "/suporte", "/CadastroOcorrencia",
           "/fabrica", "/api/fabrica", "/indicadores", "/configuracoes", "/pessoas", "/pessoas/nova",
           "/sensor", "/sensor/historico", "/maquinas", "/maquinas/cadastro", "/maquinas/cad",
           "/inspecao-documento"]
PERFIS = ["admin@nexar.com", "rh@nexar.com", "manutencao@nexar.com", "operador@nexar.com"]


@pytest.mark.parametrize("email", PERFIS)
def test_nenhuma_pagina_da_erro_500(email, db):
    from tests.conftest import _login
    c = _login(email)
    oc = db.execute("SELECT id, maquina_id FROM ocorrencias ORDER BY id DESC LIMIT 1").fetchone()
    urls = PAGINAS + [f"/ocorrencia/{oc['id']}", f"/ocorrencia/{oc['id']}/pdf", f"/qrqc3d/{oc['id']}",
                      f"/maquinas/{oc['maquina_id']}/3d", f"/api/maquinas/{oc['maquina_id']}/calor"]
    erros = {u: r.status_code for u in urls if (r := c.get(u)).status_code >= 500}
    assert not erros


@pytest.mark.parametrize("url", ["/configuracoes", "/pessoas", "/indicadores", "/maquinas/cadastro", "/maquinas/cad"])
def test_operador_nao_acessa_areas_restritas(operador, url):
    assert operador.get(url).status_code == 302


@pytest.mark.parametrize("url", ["/dashboard", "/historico", "/api/fabrica", "/sensor"])
def test_sem_login_volta_para_o_login(anonimo, url):
    r = anonimo.get(url)
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_login_com_senha_errada(anonimo):
    r = anonimo.post("/login", data={"email": "admin@nexar.com", "senha": "errada"})
    assert r.status_code == 200 and "incorretos" in r.get_data(as_text=True)
