"""Funções de IA com Gemini e OpenAI simulados (sem chave, sem rede)."""
import io

from tests.conftest import chamada_ferramenta, esperar_diagnostico, resposta_openai

DIAGNOSTICO = ("**1. Causa provável**\nFolga no fuso.\n**2. Componentes a verificar**\n- Fuso\n"
               "**3. Procedimento de inspeção**\n1. LOTO\n**4. Quando escalar**\n- Se persistir")


def _registrar(cliente, maquina_cad, **extra):
    mid, comp = maquina_cad
    dados = {"maquina_id": mid, "componente_apontado": comp, "sintoma": "folga",
             "maquina_parada": "nao", "risco_pessoas": "nao", **extra}
    r = cliente.post("/registrar_ocorrencia", data=dados)
    assert r.status_code == 302
    return int(r.headers["Location"].rsplit("/", 1)[-1])


def test_cadeia_gemini_usa_modelos_atuais(A):
    # Os modelos 2.0 e 2.5 foram descontinuados pelo Google (404 para chaves novas)
    assert not any(m.startswith(("gemini-2.0", "gemini-2.5", "gemini-1.")) for m in A.GEMINI_MODELS)
    assert not any("latest" in m for m in A.GEMINI_MODELS)   # a biblioteca recebe 404 nos apelidos


def test_diagnostico_troca_de_modelo_quando_um_falha(admin, db, gemini, maquina_cad):
    falso = gemini([Exception("404 NOT_FOUND"), DIAGNOSTICO])
    oc = _registrar(admin, maquina_cad)
    assert esperar_diagnostico(db, oc) == "ok"
    assert len(falso.modelos) >= 2 and falso.modelos[0] != falso.modelos[1]
    assert "Causa provável" in db.execute("SELECT resposta_ia FROM ocorrencias WHERE id = ?", (oc,)).fetchone()[0]


def test_sem_ia_usa_o_roteiro_local_da_peca(admin, db, gemini, maquina_cad):
    gemini([Exception("500 INTERNAL")])
    oc = _registrar(admin, maquina_cad)
    assert esperar_diagnostico(db, oc) == "local"


def test_componente_primario_aceita_plural_e_acento(A):
    assert A._componente_marcado("VEDACAO", "VEDAÇÕES VALVULA")
    assert A._componente_marcado("ROLAMENTO", "ROLAMENTOS")
    assert not A._componente_marcado("FILTRO", "MOTOR BOMBA")


def test_chat(admin, gemini):
    gemini(["Verifique o rolamento."])
    r = admin.post("/chat", json={"mensagem": "o que fazer?", "historico": [{"role": "user", "content": "oi"}]})
    assert r.status_code == 200 and r.get_json()["resposta"] == "Verifique o rolamento."
    gemini([Exception("500 INTERNAL")])
    r = admin.post("/chat", json={"mensagem": "o que fazer?"})
    assert r.status_code == 503 and r.get_json()["resposta"]


ANOMALIA = {"caixa": {"x_min": 100, "y_min": 100, "x_max": 300, "y_max": 300}, "classe": "vazamento",
            "rotulo": "Vazamento de óleo", "severidade": "atencao", "confianca": 0.9, "componente": "flange",
            "descricao": "óleo escorrendo", "causa_provavel": "vedação", "recomendacao": "trocar"}


def test_sensor_grava_e_aplica_piso_de_severidade(admin, openai, foto_jpg, maquina_cad):
    openai([{"anomalias": [ANOMALIA]}])
    r = admin.post("/api/sensor/analisar", data={"foto": (io.BytesIO(foto_jpg), "m.jpg"), "maquina_id": maquina_cad[0]},
                   content_type="multipart/form-data")
    j = r.get_json()
    assert r.status_code == 200 and j["id"]
    assert j["anomalias"][0]["severidade"] == "critico"      # vazamento nunca é só "atenção"
    assert admin.get(f"/sensor/{j['id']}/laudo.pdf").status_code == 200


def test_sensor_classe_vazia_nao_vira_critico(admin, openai, foto_jpg):
    openai([{"anomalias": [{**ANOMALIA, "classe": " ", "severidade": "info"}]}])
    r = admin.post("/api/sensor/analisar", data={"foto": (io.BytesIO(foto_jpg), "m.jpg")}, content_type="multipart/form-data")
    assert r.get_json()["anomalias"][0]["severidade"] != "critico"


def test_sensor_do_app_valida_o_conteudo_da_foto(token_app, openai):
    token, app = token_app
    openai([{"anomalias": []}])
    r = app.post("/api/mobile/sensor/analisar", headers={"Authorization": "Bearer " + token},
                 data={"foto": (io.BytesIO(b"isso nao e uma foto"), "m.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_agente_3d_descarta_peca_inventada_e_nao_envia_o_nome_do_operador(admin, db, openai, maquina_cad, gemini):
    gemini([DIAGNOSTICO])
    oc = _registrar(admin, maquina_cad)
    esperar_diagnostico(db, oc)
    mid, comp = maquina_cad
    final = {"summary": "Folga", "severity": "high", "recommended_actions": ["a"],
             "components": [{"component_id": comp, "component_name": "x", "probability": 0.8, "severity": "high"},
                            {"component_id": "peca_inventada", "component_name": "y", "probability": 0.9}]}
    falso = openai([resposta_openai(ferramentas=[chamada_ferramenta("get_machine_components", {"machine_id": mid})]), final])
    assert admin.post(f"/api/ai/analisar/{oc}").status_code == 200
    ids = [r[0] for r in db.execute("SELECT d.component_id FROM ai_diagnosis_components d JOIN ai_diagnoses a "
                                    "ON a.id = d.diagnosis_id WHERE a.ocorrencia_id = ?", (oc,))]
    assert ids == [comp]
    operador = db.execute("SELECT nome_operador FROM ocorrencias WHERE id = ?", (oc,)).fetchone()[0]
    assert operador not in str(falso.pedidos[0]["messages"])


def test_agente_3d_resposta_fora_do_formato_nao_da_500(admin, db, openai):
    oc = db.execute("SELECT id FROM ocorrencias WHERE maquina_id IS NOT NULL LIMIT 1").fetchone()[0]
    openai(["[1, 2, 3]"])
    assert admin.post(f"/api/ai/analisar/{oc}").status_code == 503


def test_documento_com_matricula_numerica_e_campos_estranhos(admin, openai):
    foto = open("docs/exemplos/pt_eletricidade_RS-01.jpg", "rb").read()
    openai([{"extraido": {"numero": "PT-1", "equipamento": 101,
                          "pessoas": [{"nome": "Carlos", "matricula": 10234, "papel": "executante"}]},
             "problemas": [{"tipo": "dado_faltante", "campo": 7, "descricao": "sem assinatura",
                            "sugestao": None, "severidade": "alto"}], "score": 250}])
    r = admin.post("/api/documento/analisar", data={"foto": (io.BytesIO(foto), "d.jpg"), "tipo_id": "1"},
                   content_type="multipart/form-data")
    assert r.status_code == 200
    j = r.get_json()
    assert 0 <= j["score"] <= 100
    assert all(isinstance(v, str) for v in j["problemas"][0].values())


def test_documento_bloqueado_por_nr10_vencida_chega_ao_app(token_app, openai, db):
    pessoa = db.execute("SELECT c.nome, c.matricula FROM colaboradores c JOIN qualificacoes q ON q.colaborador_id = c.id "
                        "WHERE q.tipo = 'NR-10' AND q.valido_ate < date('now') LIMIT 1").fetchone()
    assert pessoa, "a base de demonstração tem alguém com NR-10 vencida"
    token, app = token_app
    openai([{"extraido": {"numero": "PT-9", "equipamento": "RS-01",
                          "pessoas": [{"nome": pessoa["nome"], "matricula": pessoa["matricula"], "papel": "executante"}]},
             "problemas": [], "score": 95, "resumo": "Preenchido corretamente."}])
    foto = open("docs/exemplos/pt_eletricidade_RS-01.jpg", "rb").read()
    r = app.post("/api/mobile/inspecao/documento", headers={"Authorization": "Bearer " + token},
                 data={"foto": (io.BytesIO(foto), "d.jpg"), "tipo_documento": "Permissão de Trabalho — Eletricidade"},
                 content_type="multipart/form-data")
    j = r.get_json()
    assert j["status"] == "bloqueado" and j["conferencia"]["conferencias"]
