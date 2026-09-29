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


def test_causa_provavel_flui():
    a = sv.AnomaliaDetectada(box_2d=[100, 100, 400, 400], classe="superaquecimento",
                             rotulo="Superaquecimento", severidade="critico", confianca=0.9,
                             componente="rolamento", descricao="metal descolorido pelo calor",
                             causa_provavel="lubrificação deficiente", recomendacao="substituir rolamento")
    out = sv._validar_anomalias([a])
    assert out[0]["causa_provavel"] == "lubrificação deficiente"


def test_causa_provavel_opcional():
    # Campo é opcional: se a IA não retornar, não quebra.
    a = sv.AnomaliaDetectada(box_2d=[100, 100, 400, 400], classe="corrosao", rotulo="Corrosão",
                             severidade="atencao", confianca=0.8, componente="carcaça",
                             descricao="ferrugem", recomendacao="tratar")
    out = sv._validar_anomalias([a])
    assert out[0]["causa_provavel"] == ""


def test_desenhar_anomalias():
    from PIL import Image
    img = Image.new("RGB", (400, 300), (100, 100, 100))
    anoms = [
        {"box_2d": [100, 100, 250, 250], "severidade": "critico", "rotulo": "Vazamento"},
        {"box_2d": [0, 0, 60, 60], "severidade": "info", "rotulo": "Sujeira"},
    ]
    out = sv.desenhar_anomalias(img, anoms)
    assert out.size == (400, 300)          # mesma dimensão
    assert out is not img                  # cópia, não muta original
    # A imagem anotada deve diferir da original (pixels desenhados)
    assert list(out.getdata()) != list(img.getdata())


def test_etiquetas_nao_se_sobrepoem():
    # Caso real do laudo: duas caixas começando quase no mesmo ponto escondiam uma etiqueta
    rets = sv._posicoes_etiquetas([((245, 40), (240, 22)), ((275, 40), (230, 22)),
                                   ((250, 45), (200, 22))], 1000, 450)
    for i, a in enumerate(rets):
        for b in rets[i + 1:]:
            assert not (a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]), (a, b)
    assert all(0 <= r[0] and r[2] <= 1000 and 0 <= r[1] and r[3] <= 450 for r in rets)


def _tem_glifo(fonte, c):
    # Caractere ausente vira o "quadradinho" (.notdef): igual ao de um código de uso privado
    return bytes(fonte.getmask(c)) != bytes(fonte.getmask(""))


def test_fonte_tem_acentos():
    # Rótulos do laudo saíam "corros□o" com a fonte padrão do Pillow
    f = sv._carregar_fonte(20)
    assert all(_tem_glifo(f, c) for c in "ãçéõÃÇ")


def test_desenhar_anomalias_sem_box():
    from PIL import Image
    img = Image.new("RGB", (200, 200), (50, 50, 50))
    out = sv.desenhar_anomalias(img, [{"severidade": "info", "rotulo": "x"}])  # sem box_2d
    assert out.size == (200, 200)          # não quebra


def test_ler_anomalias_com_cercas():
    txt = '```json\n{"anomalias": [{"box_2d":[10,10,90,90],"classe":"corrosao","rotulo":"Corrosão",' \
          '"severidade":"atencao","confianca":0.7,"componente":"flange","descricao":"d","recomendacao":"r"}]}\n```'
    itens = sv._ler_anomalias(txt)
    assert itens is not None
    assert len(itens) == 1
    assert itens[0].classe == "corrosao"


def test_ler_anomalias_lista_direta():
    txt = '[{"box_2d":[10,10,90,90],"classe":"folga","rotulo":"Folga",' \
          '"severidade":"atencao","confianca":0.6,"componente":"parafuso","descricao":"d","recomendacao":"r"}]'
    itens = sv._ler_anomalias(txt)
    assert itens is not None and len(itens) == 1


def test_ler_anomalias_formato_caixa():
    # Formato do prompt atual: caixa com chaves explícitas → box_2d [ymin, xmin, ymax, xmax]
    txt = '{"equipamento":"x","condicao_geral":"y","anomalias":[{"caixa":{"x_min":200,"y_min":100,' \
          '"x_max":600,"y_max":500},"classe":"oxidacao","rotulo":"Ferrugem","severidade":"atencao",' \
          '"confianca":0.8,"componente":"base","descricao":"d","causa_provavel":"c","recomendacao":"r"}]}'
    itens = sv._ler_anomalias(txt)
    assert itens[0].box_2d == [100, 200, 500, 600]


def test_ler_anomalias_item_ruim_nao_derruba_os_outros():
    # Antes um item malformado invalidava a resposta inteira e o sensor dava "erro"
    txt = '{"anomalias":[{"classe":"trinca"},' \
          '{"caixa":{"x_min":0.1,"y_min":0.2,"x_max":0.3,"y_max":0.4},"classe":"corrosao",' \
          '"severidade":"atenção","confianca":85,"componente":"eixo","descricao":"d","recomendacao":"r"}]}'
    itens = sv._ler_anomalias(txt)
    assert len(itens) == 1                               # o sem caixa foi descartado sozinho
    assert itens[0].box_2d == [200, 100, 400, 300]       # 0-1 escalado para 0-1000
    assert itens[0].confianca == 0.85                    # porcentagem vira 0-1
    assert itens[0].severidade == "atencao"              # acento normalizado


def test_ler_anomalias_cantos_trocados():
    itens = sv._ler_anomalias('{"anomalias":[{"caixa":{"x_min":600,"y_min":500,"x_max":200,"y_max":100},'
                              '"classe":"trinca","severidade":"critico","confianca":0.9}]}')
    assert itens[0].box_2d == [100, 200, 500, 600]


def test_ler_anomalias_sem_json():
    assert sv._ler_anomalias("não encontrei nada") is None


def test_grade_nao_altera_tamanho():
    from PIL import Image
    img = Image.new("RGB", (640, 480), (120, 120, 120))
    g = sv._com_grade(img)
    assert g.size == img.size and g is not img
    assert list(img.getdata()) == [(120, 120, 120)] * (640 * 480)   # original intacta


def test_parametros_modelo():
    assert "temperature" not in sv._parametros_modelo("gpt-5.4-mini")   # raciocínio não aceita
    assert sv._parametros_modelo("gpt-4o")["temperature"] == 0.2


def test_detectar_offline_sem_client():
    r = sv.detectar_anomalias(client=None, img_obj=None, modelos=["x"], should_try_next=lambda e: False)
    assert r["status"] == "offline"
    assert r["score"] is None


class _FakeMsg:
    def __init__(self, content): self.content = content

class _FakeChoice:
    def __init__(self, content): self.message = _FakeMsg(content)

class _FakeResp:
    def __init__(self, content): self.choices = [_FakeChoice(content)]

class _FakeCompletions:
    def __init__(self, content): self._content = content
    def create(self, **kw): return _FakeResp(self._content)

class _FakeChat:
    def __init__(self, content): self.completions = _FakeCompletions(content)

class _FakeClient:
    """Imita o cliente OpenAI: client.chat.completions.create(...).choices[0].message.content"""
    def __init__(self, parsed): self.chat = _FakeChat(parsed.model_dump_json())


def _img():
    from PIL import Image
    return Image.new("RGB", (64, 64), "gray")


def test_detectar_fluxo_ok():
    parsed = sv.DeteccaoAnomalias(anomalias=[
        sv.AnomaliaDetectada(box_2d=[100, 100, 400, 400], classe="vazamento", rotulo="Vazamento",
                             severidade="critico", confianca=0.85, componente="junta",
                             descricao="óleo escorrendo", recomendacao="trocar junta"),
    ])
    r = sv.detectar_anomalias(
        client=_FakeClient(parsed), img_obj=_img(),
        modelos=["gpt-x"], should_try_next=lambda e: True,
    )
    assert r["status"] == "ok"
    assert r["severidade_max"] == "critico"
    assert 0 <= r["score"] <= 100
    assert r["anomalias"][0]["classe"] == "vazamento"


def test_detectar_sem_anomalia():
    r = sv.detectar_anomalias(
        client=_FakeClient(sv.DeteccaoAnomalias(anomalias=[])), img_obj=_img(),
        modelos=["gpt-x"], should_try_next=lambda e: True,
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
