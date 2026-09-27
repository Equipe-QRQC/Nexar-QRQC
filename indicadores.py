"""
Indicadores de manutenção por máquina e da planta.

Definições usadas (padrão de mercado, simplificado para o dado disponível):
- Falha: ocorrência registrada no período.
- MTTR (tempo médio de reparo): média de (resolução − abertura) das ocorrências
  resolvidas no período, em horas.
- Tempo parado: soma de (resolução ou agora − abertura) das ocorrências em que
  o operador informou "a máquina parou", recortado ao período.
- MTBF (tempo médio entre falhas): (horas do período − tempo parado) ÷ falhas.
- Disponibilidade: (horas do período − tempo parado) ÷ horas do período.
- Custo: custo de peças + horas de trabalho × custo da hora de manutenção.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

CUSTO_HORA_PADRAO = 85.0


def _dt(valor) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).strip().replace("T", " ")[:19])
    except ValueError:
        return None


def custo_hora(conn) -> float:
    r = conn.execute("SELECT valor FROM config_geral WHERE chave = 'custo_hora_manutencao'").fetchone()
    try:
        return float(r["valor"]) if r else CUSTO_HORA_PADRAO
    except (TypeError, ValueError):
        return CUSTO_HORA_PADRAO


def calcular(conn, dias: int = 90, agora: datetime | None = None, nomes_componentes=None) -> dict:
    agora = agora or datetime.now()
    inicio = agora - timedelta(days=dias)
    horas_periodo = dias * 24.0
    valor_hora = custo_hora(conn)

    maquinas = {r["id"]: dict(r) for r in conn.execute("SELECT id, nome, setor FROM maquinas ORDER BY nome")}
    linhas = conn.execute(
        "SELECT id, maquina_id, COALESCE(data_ocorrencia, data_registro) AS aberta, data_registro, "
        "data_resolucao, status, maquina_parada, horas_trabalho, custo_pecas, componente_apontado "
        "FROM ocorrencias WHERE maquina_id IS NOT NULL").fetchall()

    por_maq = defaultdict(lambda: {"falhas": 0, "reparos": [], "parado_h": 0.0, "custo_pecas": 0.0,
                                   "horas_trab": 0.0, "abertas": 0, "paradas_agora": 0})
    mensal = defaultdict(lambda: {"falhas": 0, "custo": 0.0, "reparos": []})
    pecas = defaultdict(int)

    for o in linhas:
        abertura = _dt(o["aberta"]) or _dt(o["data_registro"])
        fim = _dt(o["data_resolucao"])
        m = por_maq[o["maquina_id"]]
        if o["status"] not in ("Resolvida", "Fechada"):
            m["abertas"] += 1
            if o["maquina_parada"]:
                m["paradas_agora"] += 1
        if not abertura or abertura < inicio or abertura > agora:
            continue
        m["falhas"] += 1
        mes = abertura.strftime("%Y-%m")
        mensal[mes]["falhas"] += 1
        if fim and fim >= abertura:
            horas_reparo = (fim - abertura).total_seconds() / 3600
            m["reparos"].append(horas_reparo)
            mensal[mes]["reparos"].append(horas_reparo)
        if o["maquina_parada"]:
            ate = min(fim or agora, agora)
            m["parado_h"] += max(0.0, (ate - max(abertura, inicio)).total_seconds() / 3600)
        custo = (o["custo_pecas"] or 0) + (o["horas_trabalho"] or 0) * valor_hora
        m["custo_pecas"] += o["custo_pecas"] or 0
        m["horas_trab"] += o["horas_trabalho"] or 0
        mensal[mes]["custo"] += custo
        if o["componente_apontado"]:
            pecas[(o["maquina_id"], o["componente_apontado"])] += 1

    tabela = []
    for mid, info in maquinas.items():
        m = por_maq.get(mid)
        if not m:
            m = por_maq[mid]
        falhas = m["falhas"]
        operando = max(0.0, horas_periodo - m["parado_h"])
        custo_total = m["custo_pecas"] + m["horas_trab"] * valor_hora
        tabela.append({
            "id": mid, "nome": info["nome"], "setor": info["setor"],
            "falhas": falhas,
            "mttr": sum(m["reparos"]) / len(m["reparos"]) if m["reparos"] else None,
            "mtbf": operando / falhas if falhas else None,
            "disponibilidade": operando / horas_periodo * 100,
            "parado_h": m["parado_h"],
            "custo": custo_total, "custo_pecas": m["custo_pecas"], "horas_trabalho": m["horas_trab"],
            "abertas": m["abertas"], "paradas_agora": m["paradas_agora"],
        })
    tabela.sort(key=lambda x: (-x["custo"], -x["falhas"], x["nome"]))

    todos_reparos = [h for mid in maquinas for h in por_maq[mid]["reparos"]]
    total_falhas = sum(t["falhas"] for t in tabela)
    operando_total = sum(max(0.0, horas_periodo - t["parado_h"]) for t in tabela)
    resumo = {
        "falhas": total_falhas,
        "mttr": sum(todos_reparos) / len(todos_reparos) if todos_reparos else None,
        "mtbf": operando_total / total_falhas if total_falhas else None,
        "disponibilidade": (operando_total / (horas_periodo * len(tabela)) * 100) if tabela else None,
        "custo": sum(t["custo"] for t in tabela),
        "parado_h": sum(t["parado_h"] for t in tabela),
        "maquinas": len(tabela),
    }

    # Série mensal contínua (meses sem falha aparecem com zero)
    meses = []
    cursor = datetime(inicio.year, inicio.month, 1)
    while cursor <= agora:
        chave = cursor.strftime("%Y-%m")
        d = mensal.get(chave, {"falhas": 0, "custo": 0.0, "reparos": []})
        meses.append({"mes": chave, "falhas": d["falhas"], "custo": round(d["custo"], 2),
                      "mttr": round(sum(d["reparos"]) / len(d["reparos"]), 1) if d["reparos"] else None})
        cursor = datetime(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)

    top = sorted(pecas.items(), key=lambda kv: -kv[1])[:6]
    top_pecas = [{"maquina_id": mid, "maquina": maquinas.get(mid, {}).get("nome", "—"), "componente": cid,
                  "nome": (nomes_componentes(mid, cid) if nomes_componentes else None) or cid, "falhas": n}
                 for (mid, cid), n in top]

    return {"dias": dias, "custo_hora": valor_hora, "resumo": resumo, "maquinas": tabela,
            "mensal": meses, "top_pecas": top_pecas}
