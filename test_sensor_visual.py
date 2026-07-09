"""Testes da lógica pura do Sensor Visual (sem chamada de API)."""

import sensor_visual as sv


def test_indice_saude_sem_anomalia():
    assert sv.calcular_indice_saude([]) == 100


def test_indice_saude_critico_reduz():
    anomalias = [{"severidade": "critico", "confianca": 1.0}]  # 100-50=50, teto crítico 55
    assert sv.calcular_indice_saude(anomalias) == 50


def test_indice_saude_acumula_e_clampa():
    anomalias = [{"severidade": "critico", "confianca": 1.0}] * 4  # 4*50 = 200
    assert sv.calcular_indice_saude(anomalias) == 0  # clampado


def test_indice_saude_pondera_confianca():
    anomalias = [{"severidade": "atencao", "confianca": 0.5}]  # 100-11=89, teto atenção 82
    assert sv.calcular_indice_saude(anomalias) == 82


def test_indice_saude_teto_critico():
    # Um crítico de baixa confiança ainda mantém o índice no teto (não parece saudável).
    anomalias = [{"severidade": "critico", "confianca": 0.1}]  # penalidade 5 → 95, teto 55
    assert sv.calcular_indice_saude(anomalias) == 55


def test_piso_severidade_nao_rebaixa():
    # IA classificou vazamento de óleo como 'atencao' — o piso deve subir p/ 'critico'.
    a = sv.AnomaliaDetectada(box_2d=[100, 100, 400, 400], classe="vazamento_oleo",
                             rotulo="Vazamento de óleo", severidade="atencao", confianca=0.85,
                             componente="cárter", descricao="óleo escorrendo", recomendacao="trocar junta")
    out = sv._validar_anomalias([a])
    assert out[0]["severidade"] == "critico"


def test_piso_severidade_permite_escalar():
    # IA pode ESCALAR acima do baseline (corrosão baseline 'atencao' → 'critico' permitido).
    a = sv.AnomaliaDetectada(box_2d=[0, 0, 100, 100], classe="corrosao", rotulo="Corrosão",
                             severidade="critico", confianca=0.9, componente="x",
                             descricao="d", recomendacao="r")
    out = sv._validar_anomalias([a])
    assert out[0]["severidade"] == "critico"


def test_severidade_predominante():
    assert sv.severidade_predominante([]) == "ok"
    assert sv.severidade_predominante([{"severidade": "info"}]) == "info"
    assert sv.severidade_predominante(
        [{"severidade": "info"}, {"severidade": "critico"}]
    ) == "critico"


def test_bbox_para_overlay():
    ov = sv.bbox_para_overlay([100, 200, 600, 800])  # ymin,xmin,ymax,xmax /10
    assert ov == {"left": 20.0, "top": 10.0, "width": 60.0, "height": 50.0}


def test_validar_descarta_bbox_invalido():
    bom = sv.AnomaliaDetectada(
        box_2d=[100, 100, 500, 500], classe="trinca", rotulo="Trinca",
        severidade="critico", confianca=0.9, componente="carcaça",
        descricao="d", recomendacao="r",
    )
    ruim = sv.AnomaliaDetectada(
        box_2d=[500, 500, 100, 100], classe="trinca", rotulo="Trinca",  # ymax<ymin
        severidade="critico", confianca=0.9, componente="x",
        descricao="d", recomendacao="r",
    )
    out = sv._validar_anomalias([bom, ruim])
    assert len(out) == 1
    assert out[0]["classe"] == "trinca"
    assert out[0]["icone"] == "fa-bolt"


def test_validar_ordena_por_severidade():
    a_info = sv.AnomaliaDetectada(box_2d=[0, 0, 100, 100], classe="rebarba", rotulo="Rebarba",
                                  severidade="info", confianca=0.9, componente="x", descricao="d", recomendacao="r")
    a_crit = sv.AnomaliaDetectada(box_2d=[0, 0, 100, 100], classe="trinca", rotulo="Trinca",
                                  severidade="critico", confianca=0.5, componente="x", descricao="d", recomendacao="r")
    out = sv._validar_anomalias([a_info, a_crit])
    assert out[0]["severidade"] == "critico"  # crítico vem primeiro apesar de confiança menor


def test_classe_fora_taxonomia_mapeia():
    a = sv.AnomaliaDetectada(box_2d=[0, 0, 100, 100], classe="rachadura_trinca", rotulo="X",
                             severidade="critico", confianca=0.8, componente="x", descricao="d", recomendacao="r")
    out = sv._validar_anomalias([a])
    assert out[0]["classe"] == "trinca"  # 'trinca' está contido em 'rachadura_trinca'


def test_iou():
    assert sv._iou([0, 0, 100, 100], [0, 0, 100, 100]) == 1.0          # idênticos
    assert sv._iou([0, 0, 100, 100], [200, 200, 300, 300]) == 0.0      # disjuntos
    assert 0.1 < sv._iou([0, 0, 100, 100], [50, 50, 150, 150]) < 0.2   # parcial


def test_dedup_mesmo_componente():
    # Caso real: 4x "acúmulo de sujeira" no mesmo rotor -> colapsa em 1.
    def mk(conf, box):
        return sv.AnomaliaDetectada(box_2d=box, classe="acumulo_residuo", rotulo="Acúmulo de sujeira",
                                    severidade="info", confianca=conf, componente="rotor",
                                    descricao="sujeira nas ranhuras", recomendacao="limpar")
    out = sv._validar_anomalias([mk(0.6, [180, 130, 260, 170]), mk(0.6, [180, 180, 260, 220]),
                                 mk(0.6, [180, 230, 260, 270]), mk(0.6, [180, 280, 260, 320])])
    assert len(out) == 1


def test_dedup_preserva_componentes_distintos():
    # Mesma classe, componentes diferentes e caixas separadas -> mantém ambos.
    a1 = sv.AnomaliaDetectada(box_2d=[0, 0, 100, 100], classe="corrosao", rotulo="Corrosão",
                              severidade="atencao", confianca=0.8, componente="eixo",
                              descricao="d", recomendacao="r")
    a2 = sv.AnomaliaDetectada(box_2d=[500, 500, 700, 700], classe="corrosao", rotulo="Corrosão",
                              severidade="atencao", confianca=0.7, componente="carcaça",
                              descricao="d", recomendacao="r")
    out = sv._validar_anomalias([a1, a2])
    assert len(out) == 2


def test_dedup_sobreposicao_alta():
    # Mesma classe, componentes distintos mas caixas muito sobrepostas -> funde.
    a1 = sv.AnomaliaDetectada(box_2d=[100, 100, 300, 300], classe="corrosao", rotulo="Corrosão",
                              severidade="atencao", confianca=0.9, componente="ponto A",
                              descricao="d", recomendacao="r")
    a2 = sv.AnomaliaDetectada(box_2d=[110, 110, 305, 305], classe="corrosao", rotulo="Corrosão",
                              severidade="atencao", confianca=0.6, componente="ponto B",
                              descricao="d", recomendacao="r")
    out = sv._validar_anomalias([a1, a2])
    assert len(out) == 1
    assert out[0]["confianca"] == 0.9  # mantém a de maior confiança


def test_parse_json_fallback_com_cercas():
    txt = '```json\n{"anomalias": [{"box_2d":[10,10,90,90],"classe":"corrosao","rotulo":"Corrosão",' \
          '"severidade":"atencao","confianca":0.7,"componente":"flange","descricao":"d","recomendacao":"r"}]}\n```'
    parsed = sv._parse_json_fallback(txt)
    assert parsed is not None
    assert len(parsed.anomalias) == 1
    assert parsed.anomalias[0].classe == "corrosao"


def test_parse_json_fallback_lista_direta():
    txt = '[{"box_2d":[10,10,90,90],"classe":"folga","rotulo":"Folga",' \
          '"severidade":"atencao","confianca":0.6,"componente":"parafuso","descricao":"d","recomendacao":"r"}]'
    parsed = sv._parse_json_fallback(txt)
    assert parsed is not None and len(parsed.anomalias) == 1


def test_detectar_offline_sem_client():
    r = sv.detectar_anomalias(client=None, img_obj=None, modelos=["x"], should_try_next=lambda e: False)
    assert r["status"] == "offline"
    assert r["score"] is None


class _FakeResp:
    def __init__(self, parsed): self.parsed = parsed; self.text = ""

class _FakeModels:
    def __init__(self, parsed): self._parsed = parsed
    def generate_content(self, **kw): return _FakeResp(self._parsed)

class _FakeClient:
    def __init__(self, parsed): self.models = _FakeModels(parsed)


def test_detectar_fluxo_ok():
    parsed = sv.DeteccaoAnomalias(anomalias=[
        sv.AnomaliaDetectada(box_2d=[100, 100, 400, 400], classe="vazamento", rotulo="Vazamento",
                             severidade="critico", confianca=0.85, componente="junta",
                             descricao="óleo escorrendo", recomendacao="trocar junta"),
    ])
    r = sv.detectar_anomalias(
        client=_FakeClient(parsed), img_obj=object(),
        modelos=["gemini-x"], should_try_next=lambda e: True,
    )
    assert r["status"] == "ok"
    assert r["severidade_max"] == "critico"
    assert 0 <= r["score"] <= 100
    assert r["anomalias"][0]["classe"] == "vazamento"


def test_detectar_sem_anomalia():
    r = sv.detectar_anomalias(
        client=_FakeClient(sv.DeteccaoAnomalias(anomalias=[])), img_obj=object(),
        modelos=["gemini-x"], should_try_next=lambda e: True,
    )
    assert r["status"] == "sem_anomalia"
    assert r["score"] == 100


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    falhas = 0
    for fn in fns:
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
        except Exception as e:
            falhas += 1
            print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{len(fns)-falhas}/{len(fns)} testes passaram")
    sys.exit(1 if falhas else 0)
