"""
Sensor Visual — motor de percepção industrial aumentada.

Transforma a câmera de um celular + a IA multimodal (Gemini) num "sensor
virtual": o operador tira uma foto do equipamento e a IA detecta anomalias
visuais (trinca, vazamento, corrosão, desalinhamento…), classifica a
severidade e calcula um Índice de Saúde do ponto inspecionado — sem qualquer
hardware de sensoriamento instalado.

Este módulo contém apenas a lógica pura (taxonomia, schemas, detecção e
pontuação). A integração com Flask, o banco e o cliente Gemini fica em app.py,
que injeta o `client` já inicializado. Assim o módulo é testável isoladamente.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from google.genai import types as genai_types
from pydantic import BaseModel, Field

logger = logging.getLogger("nexar.sensor_visual")


# ── Taxonomia de defeitos visuais ─────────────────────────────────────────────
# Cada classe tem um rótulo humano, a severidade típica (o modelo pode ajustar
# para o caso concreto) e um ícone Font Awesome para a UI. É a base do dataset
# proprietário: toda percepção confirmada pelo operador vira dado rotulado.

TAXONOMIA_DEFEITOS: dict[str, dict] = {
    "trinca":            {"rotulo": "Trinca / fissura",        "severidade": "critico", "icone": "fa-bolt"},
    "vazamento":         {"rotulo": "Vazamento",               "severidade": "critico", "icone": "fa-droplet"},
    "vazamento_oleo":    {"rotulo": "Vazamento de óleo",       "severidade": "critico", "icone": "fa-oil-can"},
    "superaquecimento":  {"rotulo": "Superaquecimento",        "severidade": "critico", "icone": "fa-temperature-high"},
    "deformacao":        {"rotulo": "Deformação / empeno",     "severidade": "critico", "icone": "fa-arrows-left-right-to-line"},
    "peca_faltante":     {"rotulo": "Peça faltante",           "severidade": "critico", "icone": "fa-puzzle-piece"},
    "fissura_solda":     {"rotulo": "Falha em solda",          "severidade": "critico", "icone": "fa-fire-flame-simple"},
    "corrosao":          {"rotulo": "Corrosão",                "severidade": "atencao", "icone": "fa-flask"},
    "oxidacao":          {"rotulo": "Oxidação / ferrugem",     "severidade": "atencao", "icone": "fa-shield-halved"},
    "desalinhamento":    {"rotulo": "Desalinhamento",          "severidade": "atencao", "icone": "fa-ruler-combined"},
    "folga":             {"rotulo": "Folga / afrouxamento",    "severidade": "atencao", "icone": "fa-screwdriver-wrench"},
    "desgaste":          {"rotulo": "Desgaste",                "severidade": "atencao", "icone": "fa-hourglass-half"},
    "fixacao_incorreta": {"rotulo": "Fixação incorreta",       "severidade": "atencao", "icone": "fa-wrench"},
    "rebarba":           {"rotulo": "Rebarba / acabamento",    "severidade": "info",    "icone": "fa-scissors"},
    "contaminacao":      {"rotulo": "Contaminação / sujidade", "severidade": "info",    "icone": "fa-smog"},
    "acumulo_residuo":   {"rotulo": "Acúmulo de resíduo",      "severidade": "info",    "icone": "fa-broom"},
}

SEVERIDADES = ("critico", "atencao", "info")

# Ranking de gravidade (maior = pior). Usado para impor o "piso de severidade":
# a IA pode escalar a severidade de uma classe, nunca rebaixá-la.
_RANK_SEVERIDADE = {"info": 1, "atencao": 2, "critico": 3}

# Peso de penalidade de cada severidade no Índice de Saúde (0-100).
# Calibração rigorosa: um defeito crítico derruba o índice de forma expressiva.
_PESO_SEVERIDADE = {"critico": 50, "atencao": 22, "info": 6}

# Teto do Índice de Saúde conforme a pior severidade presente. Garante que um
# ponto com anomalia crítica jamais apareça "saudável", por menor que seja a
# penalidade acumulada.
_TETO_SEVERIDADE = {"critico": 55, "atencao": 82, "info": 96, "ok": 100}


# ── Schemas de saída estruturada ──────────────────────────────────────────────

class AnomaliaDetectada(BaseModel):
    """Uma anomalia visual localizada na foto do equipamento."""
    box_2d: list[int] = Field(
        description="Bounding box [ymin, xmin, ymax, xmax] normalizado em 0-1000",
        min_length=4,
        max_length=4,
    )
    classe: str = Field(description="Chave da taxonomia (ex: 'trinca', 'vazamento', 'corrosao')")
    rotulo: str = Field(description="Nome curto do defeito em português")
    severidade: Literal["critico", "atencao", "info"] = Field(
        description="critico=risco imediato, atencao=degradação em curso, info=observação leve"
    )
    confianca: float = Field(description="Confiança da detecção, 0.0 a 1.0", ge=0.0, le=1.0)
    componente: str = Field(description="Componente/região afetada (ex: 'mancal', 'flange', 'carcaça')")
    descricao: str = Field(description="O que foi observado, 1 frase objetiva")
    recomendacao: str = Field(description="Ação recomendada, 1 frase acionável")


class DeteccaoAnomalias(BaseModel):
    """Conjunto de anomalias detectadas em uma inspeção visual."""
    anomalias: list[AnomaliaDetectada]


def build_config() -> genai_types.GenerateContentConfig:
    """Config de geração para a detecção de anomalias (saída JSON estruturada)."""
    return genai_types.GenerateContentConfig(
        system_instruction=(
            "Você é um inspetor sênior de manutenção industrial com visão computacional. "
            "Analisa FOTOS REAIS de equipamentos (não diagramas) e localiza anomalias físicas "
            "visíveis com bounding boxes precisos no formato [ymin, xmin, ymax, xmax] em 0-1000. "
            "É rigoroso e conservador: só reporta o que realmente aparece na imagem e nunca "
            "inventa coordenadas. Se a foto não mostra defeito, retorna lista vazia."
        ),
        temperature=0.1,
        top_p=0.9,
        max_output_tokens=1200,
        response_mime_type="application/json",
        response_schema=DeteccaoAnomalias,
    )


# ── Conversão de bbox e pontuação ─────────────────────────────────────────────

def bbox_para_overlay(bbox: list[int]) -> dict:
    """Converte [ymin, xmin, ymax, xmax] (0-1000) em caixa de overlay em %."""
    ymin, xmin, ymax, xmax = bbox
    return {
        "left":   round(xmin / 10, 2),
        "top":    round(ymin / 10, 2),
        "width":  round((xmax - xmin) / 10, 2),
        "height": round((ymax - ymin) / 10, 2),
    }


def calcular_indice_saude(anomalias: list[dict]) -> int:
    """
    Índice de Saúde (0-100) do ponto inspecionado. Parte de 100 e desconta por
    anomalia, ponderando severidade × confiança; várias anomalias acumulam.
    Ao final aplica um teto conforme a pior severidade presente, para que um
    ponto com defeito crítico nunca pareça saudável.
    100 = nada detectado; quanto menor, pior o estado.
    """
    if not anomalias:
        return 100
    penalidade = 0.0
    for a in anomalias:
        peso = _PESO_SEVERIDADE.get(a.get("severidade", "info"), 6)
        conf = float(a.get("confianca", 0.5) or 0.5)
        penalidade += peso * conf
    teto = _TETO_SEVERIDADE.get(severidade_predominante(anomalias), 100)
    return max(0, min(teto, round(100 - penalidade)))


def _sev_mais_grave(a: str, b: str) -> str:
    """Retorna a severidade mais grave entre duas (piso de severidade)."""
    return a if _RANK_SEVERIDADE.get(a, 0) >= _RANK_SEVERIDADE.get(b, 0) else b


def severidade_predominante(anomalias: list[dict]) -> str:
    """Retorna a maior severidade presente (critico > atencao > info)."""
    for sev in SEVERIDADES:
        if any(a.get("severidade") == sev for a in anomalias):
            return sev
    return "ok"


def _prompt_deteccao(contexto: str) -> str:
    classes = ", ".join(f"'{k}'" for k in TAXONOMIA_DEFEITOS)
    ctx = f"\nCONTEXTO INFORMADO PELO OPERADOR: {contexto.strip()}\n" if contexto and contexto.strip() else ""
    return (
        "Inspecione a FOTO REAL de um equipamento industrial em anexo.\n"
        f"{ctx}\n"
        "TAREFA: localize anomalias físicas VISÍVEIS e devolva bounding boxes precisos.\n\n"
        "REGRAS:\n"
        "1. Reporte apenas defeitos realmente visíveis na foto. Se não houver defeito, "
        "retorne anomalias: [].\n"
        f"2. Classifique cada anomalia usando uma destas classes: {classes}. "
        "Se nenhuma encaixar bem, use a mais próxima.\n"
        "3. box_2d = [ymin, xmin, ymax, xmax] em 0-1000, cobrindo EXATAMENTE a região do "
        "defeito — nunca o fundo.\n"
        "4. confianca: seja honesto (0.0 a 1.0). Detalhe borrado ou ambíguo → confiança baixa.\n"
        "5. Máximo de 6 anomalias, priorizando as mais severas.\n"
        "6. descricao e recomendacao: 1 frase cada, técnicas e acionáveis.\n\n"
        "CRITÉRIOS DE SEVERIDADE (seja RIGOROSO — na dúvida, suba a severidade):\n"
        "- critico: vazamento ATIVO (óleo/fluido escorrendo ou gotejando), trinca/fissura, "
        "superaquecimento, deformação/empeno, peça faltante, falha em solda. Risco de parada, "
        "dano ao equipamento ou à segurança.\n"
        "- atencao: corrosão, oxidação, desgaste, desalinhamento, folga, fixação incorreta. "
        "Degradação em curso, sem risco imediato.\n"
        "- info: rebarba, sujidade, acúmulo de resíduo. Observação, sem impacto funcional.\n"
        "IMPORTANTE: um vazamento com fluido escorrendo é SEMPRE 'critico', NUNCA 'atencao'. "
        "Não subestime defeitos que comprometem a integridade do equipamento."
    )


def detectar_anomalias(
    client,
    img_obj,
    modelos: list[str],
    should_try_next,
    contexto: str = "",
) -> dict:
    """
    Executa a detecção de anomalias sobre uma foto.

    Args:
        client: cliente Gemini já inicializado (genai.Client).
        img_obj: imagem PIL (RGB).
        modelos: cadeia de modelos a tentar (fallback em cota/indisponibilidade).
        should_try_next: callable(Exception)->bool que decide o fallback de modelo.
        contexto: texto opcional do operador (ex: "ruído no mancal esquerdo").

    Returns:
        dict com: anomalias (lista de overlays), score, severidade_max, resumo,
        modelo, status ('ok' | 'sem_anomalia' | 'offline' | 'erro').
    """
    if client is None or img_obj is None:
        return {
            "anomalias": [], "score": None, "severidade_max": "ok",
            "resumo": "IA indisponível — configure GEMINI_API_KEY.",
            "modelo": None, "status": "offline",
        }

    config = build_config()
    prompt = _prompt_deteccao(contexto)
    ultimo_erro: Exception | None = None

    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=[prompt, img_obj],
                config=config,
            )
            parsed: DeteccaoAnomalias | None = response.parsed
            if parsed is None:
                parsed = _parse_json_fallback(response.text or "")
            if parsed is None:
                logger.warning(f"[sensor/{modelo}] resposta sem JSON parseável")
                continue

            anomalias = _validar_anomalias(parsed.anomalias)
            score = calcular_indice_saude(anomalias)
            sev = severidade_predominante(anomalias)
            status = "ok" if anomalias else "sem_anomalia"
            logger.info(f"[sensor/{modelo}] {len(anomalias)} anomalia(s), saúde={score}")
            return {
                "anomalias": anomalias,
                "score": score,
                "severidade_max": sev,
                "resumo": _resumo(anomalias, score),
                "modelo": modelo,
                "status": status,
            }
        except Exception as e:  # noqa: BLE001 — fallback controlado de modelo
            ultimo_erro = e
            if should_try_next(e):
                logger.warning(f"[sensor/{modelo}] cota/indisponível — tentando próximo modelo")
                continue
            logger.exception(f"[sensor/{modelo}] erro definitivo")
            break

    return {
        "anomalias": [], "score": None, "severidade_max": "ok",
        "resumo": f"Falha na análise: {ultimo_erro}" if ultimo_erro else "Falha na análise.",
        "modelo": None, "status": "erro",
    }


def _validar_anomalias(itens: list[AnomaliaDetectada]) -> list[dict]:
    """Descarta bboxes inválidos e monta os overlays prontos para a UI."""
    saida: list[dict] = []
    for a in itens:
        ymin, xmin, ymax, xmax = a.box_2d
        if not (0 <= ymin < ymax <= 1000 and 0 <= xmin < xmax <= 1000):
            logger.warning(f"[sensor] bbox inválido descartado: {a.box_2d} ({a.rotulo})")
            continue
        classe = a.classe if a.classe in TAXONOMIA_DEFEITOS else _classe_mais_proxima(a.classe)
        meta = TAXONOMIA_DEFEITOS.get(classe, {})
        # Piso de severidade: a IA pode escalar acima do baseline da classe,
        # mas nunca rebaixar (ex: vazamento de óleo não vira 'atenção').
        severidade = _sev_mais_grave(a.severidade, meta.get("severidade", "info"))
        saida.append({
            **bbox_para_overlay(a.box_2d),
            "box_2d": a.box_2d,
            "classe": classe,
            "rotulo": a.rotulo or meta.get("rotulo", classe),
            "severidade": severidade,
            "confianca": round(float(a.confianca), 2),
            "componente": a.componente,
            "descricao": a.descricao,
            "recomendacao": a.recomendacao,
            "icone": meta.get("icone", "fa-triangle-exclamation"),
        })
    # Ordena por severidade e confiança (mais grave primeiro)
    ordem = {"critico": 0, "atencao": 1, "info": 2}
    saida.sort(key=lambda x: (ordem.get(x["severidade"], 3), -x["confianca"]))
    return saida


def _classe_mais_proxima(classe: str) -> str:
    """Mapeia uma classe fora da taxonomia para a chave conhecida mais parecida."""
    c = (classe or "").lower().strip()
    for chave in TAXONOMIA_DEFEITOS:
        if chave in c or c in chave:
            return chave
    return "contaminacao"  # bucket neutro de baixa severidade


def _parse_json_fallback(texto: str) -> DeteccaoAnomalias | None:
    """Alguns modelos lite embrulham o JSON em ```json ... ```; recupera isso."""
    if not texto:
        return None
    try:
        bloco = re.search(r"```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", texto)
        json_str = bloco.group(1) if bloco else texto.strip()
        raw = json.loads(json_str)
        if isinstance(raw, list):
            raw = {"anomalias": raw}
        return DeteccaoAnomalias(**raw)
    except Exception:
        return None


def _resumo(anomalias: list[dict], score: int) -> str:
    if not anomalias:
        return "Nenhuma anomalia visível detectada. Ponto em condição aparentemente normal."
    n_crit = sum(1 for a in anomalias if a["severidade"] == "critico")
    partes = [f"{len(anomalias)} anomalia(s) detectada(s)"]
    if n_crit:
        partes.append(f"{n_crit} crítica(s)")
    partes.append(f"Índice de Saúde {score}/100")
    return " · ".join(partes) + "."
