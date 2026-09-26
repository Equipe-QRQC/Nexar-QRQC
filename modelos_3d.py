"""
Modelos 3D das máquinas — camada semântica (componentes) compartilhada entre o
backend e o visualizador.

Cada máquina pode ter um modelo 3D de uma de duas fontes:

- "familia": modelo construído em código no navegador, por família de máquina
  (static/js/viewer3d/familias/<familia>.js). Usado quando não há CAD.
- "glb": arquivo convertido do CAD do fabricante (STEP → GLB), com um mapa
  que liga as peças do CAD aos componentes do catálogo e, opcionalmente,
  peças internas acrescentadas em código (o CAD de fabricante costuma trazer
  só a carcaça externa).

Em ambos os casos, o catálogo de componentes abaixo é a fonte da verdade: ele
é gravado em machine_components para que a Nexar IA só aponte componentes que
existem no modelo, e o visualizador usa os mesmos component_id.
"""
from __future__ import annotations

import json

# component_id: (nome exibido, tipo, descrição curta para a IA)
FAMILIAS: dict[str, dict] = {
    "prensa_hidraulica": {
        "nome": "Prensa hidráulica de 4 colunas",
        "componentes": [
            ("base",               "Base / mesa inferior",          "estrutura",  "Base fundida que apoia a mesa de trabalho e a matriz."),
            ("colunas",            "Colunas guia",                  "estrutura",  "Quatro colunas que guiam o martelo e sustentam o cabeçote."),
            ("cabecote_superior",  "Cabeçote superior",             "estrutura",  "Travessa superior onde o cilindro principal é fixado."),
            ("cilindro_principal", "Cilindro principal",            "hidráulico", "Cilindro hidráulico de dupla ação que gera a força de prensagem."),
            ("pistao",             "Pistão do cilindro",            "hidráulico", "Pistão interno do cilindro principal."),
            ("vedacao_cilindro",   "Vedação do cilindro principal", "hidráulico", "Kit de vedação da haste na saída do cilindro (gaxetas e raspador)."),
            ("haste_cilindro",     "Haste do cilindro",             "hidráulico", "Haste cromada que transmite a força ao martelo."),
            ("martelo",            "Martelo (cabeçote móvel)",      "mecânico",   "Cabeçote móvel guiado pelas colunas, onde fica o punção."),
            ("buchas_guia",        "Buchas guia do martelo",        "mecânico",   "Buchas de bronze que deslizam nas colunas."),
            ("puncao",             "Punção",                        "ferramenta", "Parte superior da ferramenta de estampagem."),
            ("matriz_corte",       "Matriz de corte",               "ferramenta", "Parte inferior da ferramenta de estampagem, sobre a mesa."),
            ("reservatorio_oleo",  "Reservatório de óleo",          "hidráulico", "Tanque da unidade hidráulica."),
            ("motor_bomba",        "Motor da bomba",                "elétrico",   "Motor elétrico que aciona a bomba hidráulica."),
            ("bomba_hidraulica",   "Bomba hidráulica",              "hidráulico", "Bomba de pistões que gera a pressão do sistema."),
            ("filtro_oleo",        "Filtro de óleo",                "hidráulico", "Filtro de retorno da unidade hidráulica."),
            ("valvula_direcional", "Bloco de válvulas direcionais", "hidráulico", "Válvulas que comandam avanço e retorno do cilindro."),
            ("manometro",          "Manômetro",                     "instrumento","Indicador da pressão do sistema (nominal 180 bar)."),
            ("mangueiras",         "Mangueiras hidráulicas",        "hidráulico", "Linhas de alta pressão entre a unidade e o cilindro."),
            ("painel_controle",    "Painel de controle (CLP/IHM)",  "elétrico",   "Painel com CLP, IHM e comandos bimanuais."),
            ("botao_emergencia",   "Botão de emergência",           "segurança",  "Botão tipo cogumelo que interrompe o ciclo."),
            ("cortina_luz",        "Cortina de luz",                "segurança",  "Barreira óptica de proteção da zona de prensagem."),
        ],
    },
}


# Palavras-chave que identificam cada componente no texto do diagnóstico.
# Comparação sem acentos e em minúsculas.
PALAVRAS: dict[str, dict[str, list[str]]] = {
    "prensa_hidraulica": {
        "base": ["base da prensa", "mesa inferior", "bolster"],
        "colunas": ["coluna"],
        "cabecote_superior": ["cabecote superior", "travessa superior", "coroa"],
        "cilindro_principal": ["cilindro"],
        "pistao": ["pistao", "embolo"],
        "vedacao_cilindro": ["vedac", "gaxeta", "retentor", "o-ring", "oring", "raspador"],
        "haste_cilindro": ["haste"],
        "martelo": ["martelo", "cabecote movel", "slide"],
        "buchas_guia": ["bucha", "guias do martelo"],
        "puncao": ["puncao"],
        "matriz_corte": ["matriz", "ferramenta de corte"],
        "reservatorio_oleo": ["reservatorio", "tanque", "nivel de oleo"],
        "motor_bomba": ["motor eletrico", "motor da bomba", "motor"],
        "bomba_hidraulica": ["bomba"],
        "filtro_oleo": ["filtro"],
        "valvula_direcional": ["valvula", "solenoide", "direcional"],
        "manometro": ["manometro", "pressostato", "transdutor de pressao"],
        "mangueiras": ["mangueira", "tubulac", "conexoes hidraulicas", "linha hidraulica", "linhas hidraulicas"],
        "painel_controle": ["clp", "ihm", "painel", "controlador"],
        "botao_emergencia": ["emergencia"],
        "cortina_luz": ["cortina de luz", "cortina"],
    },
}


def _normalizar_texto(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return t.lower()


def componentes_citados(texto: str, cfg: dict | None, limite: int = 5) -> list[dict]:
    """
    Encontra no diagnóstico em texto (seções '1. Causa provável', '2. Componentes
    a verificar'...) os componentes do modelo 3D citados. Causa provável → high,
    componentes a verificar → medium, demais seções → low. Permite destacar o 3D
    mesmo sem a análise estruturada do agente.
    """
    import re
    if not texto or not cfg or cfg.get("fonte") != "familia":
        return []
    palavras = PALAVRAS.get(cfg["familia"], {})
    nomes = {c["component_id"]: c["name"] for c in componentes_da_config(cfg)}
    norm = _normalizar_texto(texto)
    # Seções pelo título (listas numeradas dentro do procedimento não contam)
    titulos = {1: r"causa provavel", 2: r"componentes a verificar",
               3: r"procedimento de inspecao", 4: r"quando escalar"}
    cortes = sorted((m.start(), n) for n, rx in titulos.items() for m in re.finditer(rx, norm))
    def secao(pos: int) -> int:
        atual = 0
        for inicio, n in cortes:
            if inicio <= pos:
                atual = n
        return atual

    achados: dict[str, tuple[int, int]] = {}   # id → (rank de severidade, posição)
    for cid, termos in palavras.items():
        for termo in termos:
            for m in re.finditer(re.escape(termo), norm):
                sec = secao(m.start())
                rank = 0 if sec == 1 else 1 if sec == 2 else 2
                atual = achados.get(cid)
                if atual is None or (rank, m.start()) < atual:
                    achados[cid] = (rank, m.start())
    ordenados = sorted(achados.items(), key=lambda kv: kv[1])[:limite]
    sev = {0: "high", 1: "medium", 2: "low"}
    return [{"component_id": cid, "component_name": nomes.get(cid, cid),
             "severity": sev[r], "fonte": "diagnostico"} for cid, (r, _) in ordenados]


def familias_disponiveis() -> list[tuple[str, str]]:
    return [(k, v["nome"]) for k, v in FAMILIAS.items()]


def ler_config(valor: str | None) -> dict | None:
    """Lê a coluna maquinas.modelo_3d (JSON) com tolerância a lixo."""
    if not valor:
        return None
    try:
        cfg = json.loads(valor)
    except (TypeError, ValueError):
        return None
    if cfg.get("fonte") == "familia" and cfg.get("familia") in FAMILIAS:
        return cfg
    if cfg.get("fonte") == "glb" and cfg.get("arquivo"):
        return cfg
    return None


def componentes_da_config(cfg: dict | None) -> list[dict]:
    """Catálogo de componentes (component_id, name, type, description) do modelo."""
    if not cfg:
        return []
    if cfg.get("fonte") == "familia":
        itens = FAMILIAS[cfg["familia"]]["componentes"]
        return [{"component_id": c, "name": n, "type": t, "description": d} for c, n, t, d in itens]
    # GLB: o catálogo vem da própria configuração (mapa CAD → componentes + internos)
    return [
        {"component_id": c["id"], "name": c["nome"], "type": c.get("tipo", ""),
         "description": c.get("descricao", "")}
        for c in cfg.get("componentes", [])
    ]


def sincronizar_componentes(conn, maquina_id: int, cfg: dict | None) -> int:
    """
    Regrava machine_components da máquina a partir do catálogo do modelo 3D.
    Máquina sem modelo mantém os componentes que já tinha (cadastro manual).
    """
    comps = componentes_da_config(cfg)
    if not comps:
        return 0
    conn.execute("DELETE FROM machine_components WHERE maquina_id = ?", (maquina_id,))
    conn.executemany(
        "INSERT INTO machine_components (maquina_id, component_id, name, type, description) "
        "VALUES (?,?,?,?,?)",
        [(maquina_id, c["component_id"], c["name"], c["type"], c["description"]) for c in comps],
    )
    return len(comps)
