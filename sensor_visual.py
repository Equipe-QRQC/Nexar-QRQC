"""
Sensor Visual — motor de percepção industrial aumentada.

Transforma a câmera de um celular + a IA multimodal (OpenAI) num "sensor
virtual": o operador tira uma foto do equipamento e a IA detecta anomalias
visuais (trinca, vazamento, corrosão, desalinhamento…), classifica a
severidade e calcula um Índice de Saúde do ponto inspecionado — sem qualquer
hardware de sensoriamento instalado.

Este módulo contém apenas a lógica pura (taxonomia, schemas, detecção e
pontuação). A integração com Flask, o banco e o cliente OpenAI fica em app.py,
que injeta o `client` já inicializado. Assim o módulo é testável isoladamente.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Literal

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

logger = logging.getLogger("nexar.sensor_visual")

# Cor RGB de cada severidade (mesmo padrão da tela e do laudo).
_COR_SEVERIDADE = {
    "critico": (224, 82, 82),
    "atencao": (245, 166, 35),
    "info": (59, 158, 255),
}


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
    causa_provavel: str = Field(
        default="",
        description="Causa raiz mais provável do defeito, 1 frase técnica (o 'porquê')",
    )
    recomendacao: str = Field(description="Ação recomendada, 1 frase acionável")


class DeteccaoAnomalias(BaseModel):
    """Conjunto de anomalias detectadas em uma inspeção visual."""
    anomalias: list[AnomaliaDetectada]


# Modelos de visão, do preferido ao reserva (cota/indisponibilidade → próximo).
# Comparados numa foto real: gpt-5.5 e gpt-5.4 põem as caixas sobre o defeito; gpt-4.1 e
# gpt-4o erram a posição (caixa do volante fora dele, base "no chão"). gpt-5.5 ~15 s.
MODELOS_PADRAO = ["gpt-5.5", "gpt-5.4", "gpt-4.1"]

# Antes o prompt pedia um inspetor "conservador" que devolvesse [] na dúvida: o modelo
# via a ferrugem (confirmado numa pergunta aberta) e mesmo assim devolvia lista vazia.
_SYSTEM_SENSOR = (
    "Você é um inspetor sênior de manutenção industrial fazendo a inspeção visual de rotina "
    "de um equipamento a partir de uma FOTO REAL. Seu trabalho é encontrar e localizar TODA "
    "condição anormal visível que um técnico de manutenção anotaria no relatório: de defeitos "
    "críticos (trinca, vazamento, peça quebrada) a sinais de degradação e má conservação "
    "(ferrugem, corrosão, tinta descascada, sujeira, graxa ou óleo acumulado, desgaste). "
    "Você não inventa: cada anomalia precisa estar visível na foto, com a caixa sobre ela."
)

_JSON_SCHEMA_HINT = (
    '{"equipamento": "o que é o equipamento", '
    '"condicao_geral": "estado geral de conservação em 1-2 frases", '
    '"anomalias": [{"caixa": {"x_min": 0, "y_min": 0, "x_max": 0, "y_max": 0}, '
    '"classe": "string", "rotulo": "string", '
    '"severidade": "critico|atencao|info", "confianca": 0.0, '
    '"componente": "string", "descricao": "string", '
    '"causa_provavel": "string", "recomendacao": "string"}]}'
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
        "Inspecione a FOTO REAL do equipamento em anexo.\n"
        f"{ctx}\n"
        "A foto tem uma GRADE DE REFERÊNCIA desenhada por cima, com as coordenadas de 0 a 1000 "
        "escritas nas bordas (x na horizontal, da esquerda para a direita; y na vertical, de cima "
        "para baixo). A grade NÃO faz parte do equipamento: use-a só para medir as caixas.\n\n"
        "COMO INSPECIONAR:\n"
        "1. Primeiro identifique o equipamento (campo 'equipamento') e descreva o estado geral de "
        "conservação (campo 'condicao_geral').\n"
        "2. Depois varra o equipamento parte por parte: estrutura/carcaça, superfícies metálicas e "
        "pintura, fixações e parafusos, partes móveis (eixos, polias, volantes, correias, "
        "engrenagens), vedações e conexões, parte elétrica (cabos, painéis) e a base/piso em volta.\n"
        "3. Reporte em 'anomalias' toda condição anormal visível que um técnico anotaria: ferrugem, "
        "oxidação, corrosão, tinta descascada, sujeira/graxa/poeira acumulada, óleo acumulado ou "
        "manchas de óleo, desgaste, peça quebrada, solta ou faltante, cabo exposto, vazamento, trinca, "
        "deformação. Equipamento velho e mal conservado NÃO está normal: reporte a degradação visível.\n"
        "4. Só devolva anomalias: [] se o equipamento estiver visivelmente limpo, íntegro e bem "
        "conservado.\n"
        "5. NÃO INVENTE. Cada anomalia precisa de evidência visual clara (cor de ferrugem, tinta "
        "faltando, material acumulado, fluido, peça rompida...). NÃO são defeitos: sombra, reflexo, "
        "brilho, a cor ou textura natural do material, marcas de fabricação e detalhes de projeto "
        "(aletas, rasgos de ventilação, parafusos, etiquetas íntegras). Reporte só o que está NO "
        "equipamento — nunca no fundo, na parede ou na bancada (exceto fluido/resíduo que saiu dele). "
        "Na dúvida sobre SE algo é defeito, não reporte; na dúvida sobre a GRAVIDADE, suba.\n\n"
        "REGRAS DE CADA ANOMALIA:\n"
        f"- classe: uma destas: {classes}. Se nenhuma encaixar bem, use a mais próxima.\n"
        "- caixa: x_min, y_min, x_max, y_max em 0-1000 (leia na grade), envolvendo JUSTO a região "
        "afetada, não o equipamento inteiro nem o fundo. Defeito espalhado (ex.: ferrugem na "
        "carcaça toda): uma caixa na região mais afetada. Regiões distintas: entradas distintas.\n"
        "- confianca: honesta, de 0.0 a 1.0. Detalhe borrado ou ambíguo → confiança baixa.\n"
        "- componente: a parte afetada, com o nome técnico (ex.: 'volante', 'base', 'mancal').\n"
        "- descricao: O QUE foi observado (1 frase). causa_provavel: o PORQUÊ, a causa raiz mais "
        "provável (1 frase técnica). recomendacao: a AÇÃO corretiva (1 frase acionável).\n"
        "- Máximo de 8 anomalias, as mais relevantes primeiro. NÃO repita: o mesmo defeito no mesmo "
        "componente vira UMA entrada.\n\n"
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
    Executa a detecção de anomalias sobre uma foto usando OpenAI Vision.

    Args:
        client: cliente OpenAI já inicializado.
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
            "resumo": "A análise por IA está indisponível no momento.",
            "modelo": None, "status": "offline",
        }

    # A IA recebe a foto com a grade de coordenadas (a foto salva continua limpa)
    buf = BytesIO()
    _com_grade(img_obj).save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    user_prompt = _prompt_deteccao(contexto) + f"\n\nRetorne APENAS JSON válido neste formato:\n{_JSON_SCHEMA_HINT}"
    ultimo_erro: Exception | None = None

    for modelo in modelos:
        try:
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": _SYSTEM_SENSOR},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high",
                        }},
                    ]},
                ],
                response_format={"type": "json_object"},
                timeout=50,     # API travada → erro "timeout" → próximo modelo (padrão seria 10 min)
                **_parametros_modelo(modelo),
            )
            content = (response.choices[0].message.content or "").strip()
            itens = _ler_anomalias(content)
            if itens is None:
                logger.warning(f"[sensor/{modelo}] resposta sem JSON parseável: {content[:200]!r}")
                continue

            anomalias = _validar_anomalias(itens)
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
        "resumo": "Não foi possível analisar a foto agora. Tente novamente em alguns minutos.",
        "modelo": None, "status": "erro",
    }


def _parametros_modelo(modelo: str) -> dict:
    """Modelos de raciocínio (gpt-5.x, o-series) não aceitam temperature/max_tokens."""
    if modelo.startswith(("gpt-5", "o3", "o4")):
        # O limite inclui os tokens de raciocínio: folga para não cortar o JSON
        return {"reasoning_effort": "low", "max_completion_tokens": 8000}
    return {"temperature": 0.2, "max_completion_tokens": 2500}


def _com_grade(img):
    """Cópia da foto com grade de referência 0-1000 (linhas a cada 100, números nas bordas)."""
    base = img.convert("RGB")
    W, H = base.size
    camada = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    esp = max(1, round(min(W, H) / 500))
    fonte = _carregar_fonte(max(10, round(min(W, H) * 0.028)))
    for v in range(100, 1000, 100):
        x, y = v / 1000 * W, v / 1000 * H
        # Linha dupla (escura + clara) aparece sobre fundo claro e escuro
        d.line([(x, 0), (x, H)], fill=(0, 0, 0, 90), width=esp + 1)
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 110), width=esp)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 90), width=esp + 1)
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 110), width=esp)
    for v in range(100, 1000, 100):
        x, y = v / 1000 * W, v / 1000 * H
        for (px, py) in ((x + 3, 2), (2, y + 2)):          # x no topo, y na esquerda
            t = str(v)
            l, t0, r, b = d.textbbox((px, py), t, font=fonte)
            d.rectangle([l - 2, t0 - 1, r + 2, b + 1], fill=(15, 23, 42, 170))
            d.text((px, py), t, fill=(255, 255, 255, 255), font=fonte)
    return Image.alpha_composite(base.convert("RGBA"), camada).convert("RGB")


def _num(v, padrao=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return padrao


def _caixa_do_item(item: dict) -> list[int] | None:
    """
    Caixa do item em [ymin, xmin, ymax, xmax] 0-1000. Aceita {"caixa": {x_min, y_min,
    x_max, y_max}} ou "box_2d" [ymin, xmin, ymax, xmax]; valores em 0-1 são escalados,
    cantos trocados são ordenados e tudo é limitado à foto.
    """
    c = item.get("caixa")
    if isinstance(c, dict):
        vals = [_num(c.get(k), None) for k in ("y_min", "x_min", "y_max", "x_max")]
    elif isinstance(item.get("box_2d"), (list, tuple)) and len(item["box_2d"]) == 4:
        vals = [_num(v, None) for v in item["box_2d"]]
    else:
        return None
    if any(v is None for v in vals):
        return None
    if max(vals) <= 1.0:                     # veio normalizado em 0-1
        vals = [v * 1000 for v in vals]
    y1, x1, y2, x2 = (min(1000.0, max(0.0, v)) for v in vals)
    y1, y2 = sorted((y1, y2))
    x1, x2 = sorted((x1, x2))
    if y2 - y1 < 5 or x2 - x1 < 5:           # caixa degenerada
        return None
    return [round(y1), round(x1), round(y2), round(x2)]


def _ler_anomalias(conteudo: str) -> list[AnomaliaDetectada] | None:
    """
    Lê a resposta da IA. Um item malformado é descartado sozinho — antes derrubava a
    análise inteira. Retorna None só quando não há JSON utilizável.
    """
    raw = None
    for texto in (conteudo, (re.search(r"```(?:json)?\s*([\s\S]*?)```", conteudo or "") or [None, None])[1]):
        if not texto:
            continue
        try:
            raw = json.loads(texto)
            break
        except ValueError:
            continue
    if isinstance(raw, list):
        raw = {"anomalias": raw}
    if not isinstance(raw, dict) or not isinstance(raw.get("anomalias", []), list):
        return None
    itens = []
    for item in raw.get("anomalias") or []:
        if not isinstance(item, dict):
            continue
        caixa = _caixa_do_item(item)
        if not caixa:
            logger.warning(f"[sensor] anomalia sem caixa válida descartada: {str(item)[:160]}")
            continue
        conf = _num(item.get("confianca"), 0.5)
        if conf > 1:                         # veio em porcentagem
            conf /= 100
        sev = str(item.get("severidade") or "").strip().lower()
        sev = {"crítico": "critico", "atenção": "atencao"}.get(sev, sev)
        try:
            itens.append(AnomaliaDetectada(
                box_2d=caixa,
                classe=str(item.get("classe") or "contaminacao"),
                rotulo=str(item.get("rotulo") or ""),
                severidade=sev if sev in SEVERIDADES else "atencao",
                confianca=min(1.0, max(0.0, conf)),
                componente=str(item.get("componente") or "—"),
                descricao=str(item.get("descricao") or ""),
                causa_provavel=str(item.get("causa_provavel") or ""),
                recomendacao=str(item.get("recomendacao") or ""),
            ))
        except Exception as e:  # noqa: BLE001 — item isolado, segue com os demais
            logger.warning(f"[sensor] anomalia descartada ({e}): {str(item)[:160]}")
    return itens


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
            "causa_provavel": a.causa_provavel,
            "recomendacao": a.recomendacao,
            "icone": meta.get("icone", "fa-triangle-exclamation"),
        })
    # Remove duplicatas (mesma classe em região sobreposta ou mesmo componente)
    saida = _deduplicar(saida)
    # Ordena por severidade e confiança (mais grave primeiro)
    ordem = {"critico": 0, "atencao": 1, "info": 2}
    saida.sort(key=lambda x: (ordem.get(x["severidade"], 3), -x["confianca"]))
    return saida


def _iou(b1: list[int], b2: list[int]) -> float:
    """Intersection-over-Union de dois bboxes [ymin, xmin, ymax, xmax]."""
    ay1, ax1, ay2, ax2 = b1
    by1, bx1, by2, bx2 = b2
    iy1, ix1 = max(ay1, by1), max(ax1, bx1)
    iy2, ix2 = min(ay2, by2), min(ax2, bx2)
    inter = max(0, iy2 - iy1) * max(0, ix2 - ix1)
    if inter == 0:
        return 0.0
    area1 = (ay2 - ay1) * (ax2 - ax1)
    area2 = (by2 - by1) * (bx2 - bx1)
    return inter / (area1 + area2 - inter)


def _deduplicar(anomalias: list[dict], iou_min: float = 0.5) -> list[dict]:
    """
    Funde detecções redundantes: mesma classe em caixas sobrepostas (IoU alto)
    ou no mesmo componente. Mantém a de maior confiança. Evita que o modelo
    infle a lista repetindo a mesma anomalia várias vezes.
    """
    mantidas: list[dict] = []
    for a in sorted(anomalias, key=lambda x: -x["confianca"]):
        comp_a = (a.get("componente") or "").strip().lower()
        duplicada = any(
            a["classe"] == m["classe"] and (
                _iou(a["box_2d"], m["box_2d"]) >= iou_min
                or (comp_a and comp_a == (m.get("componente") or "").strip().lower())
            )
            for m in mantidas
        )
        if not duplicada:
            mantidas.append(a)
        else:
            logger.info(f"[sensor] duplicata removida: {a['rotulo']} ({a.get('componente')})")
    return mantidas


def _classe_mais_proxima(classe: str) -> str:
    """Mapeia uma classe fora da taxonomia para a chave conhecida mais parecida."""
    c = (classe or "").lower().strip()
    for chave in TAXONOMIA_DEFEITOS:
        if chave in c or c in chave:
            return chave
    return "contaminacao"  # bucket neutro de baixa severidade


def _fonte_vera() -> str:
    """Vera (com acentos) que vem com o reportlab, dependência do projeto para o laudo PDF."""
    try:
        import reportlab
        return os.path.join(os.path.dirname(reportlab.__file__), "fonts", "VeraBd.ttf")
    except ImportError:
        return ""


def _carregar_fonte(tamanho: int):
    """
    Fonte TrueType para os rótulos. A fonte padrão do Pillow não tem "ã", "ç"...:
    sem DejaVu (Mac, imagens mínimas de Linux) os rótulos do laudo saíam com quadradinhos.
    """
    for caminho in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        _fonte_vera(),
    ):
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()


def desenhar_anomalias(img, anomalias: list[dict]):
    """
    "Queima" as bounding boxes das anomalias sobre uma cópia da foto, com cor
    por severidade e rótulo numerado. Usado no laudo em PDF (fidelidade de
    impressão) e em qualquer exportação de imagem. Retorna uma nova imagem PIL.
    """
    img = img.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    W, H = img.size
    espessura = max(2, round(min(W, H) * 0.005))
    fonte = _carregar_fonte(max(12, round(min(W, H) * 0.026)))

    # Primeiro todas as caixas, depois as etiquetas: caixa nenhuma pinta sobre a etiqueta de outra
    itens = []
    for i, a in enumerate(anomalias, 1):
        box = a.get("box_2d")
        if not box or len(box) != 4:
            continue
        ymin, xmin, ymax, xmax = box
        x1, y1 = xmin / 1000 * W, ymin / 1000 * H
        x2, y2 = xmax / 1000 * W, ymax / 1000 * H
        cor = _COR_SEVERIDADE.get(a.get("severidade"), _COR_SEVERIDADE["info"])
        draw.rectangle([x1, y1, x2, y2], outline=cor, width=espessura)
        rotulo = f"{i}  {a.get('rotulo', '')}".strip()
        try:
            l, t, r, b = draw.textbbox((0, 0), rotulo, font=fonte)
            tw, th = r - l, b - t
        except Exception:
            tw, th = len(rotulo) * 7, 12
        pad = max(3, round(th * 0.35))
        itens.append((rotulo, cor, pad, (x1, y1), (tw + 2 * pad, th + 2 * pad)))

    posicoes = _posicoes_etiquetas([(canto, tam) for _, _, _, canto, tam in itens], W, H)
    for (rotulo, cor, pad, _, _), (tx, ty, tx2, ty2) in zip(itens, posicoes):
        draw.rectangle([tx, ty, tx2, ty2], fill=cor)
        draw.text((tx + pad, ty + pad), rotulo, fill=(255, 255, 255), font=fonte)

    return img


def _posicoes_etiquetas(etiquetas: list[tuple], W: float, H: float) -> list[tuple]:
    """
    Retângulo de cada etiqueta [(canto_da_caixa, (larg, alt))] → [(x1, y1, x2, y2)]: acima da
    caixa (dentro dela se não houver espaço), sem sair da foto e sem cobrir uma etiqueta já
    posicionada — em caso de choque, desce para logo abaixo da que atrapalha.
    """
    ocupadas: list[tuple] = []
    for (x1, y1), (w, h) in etiquetas:
        tx = max(0, min(x1, W - w))
        ty = y1 - h if y1 - h >= 0 else y1
        for _ in range(len(ocupadas) + 1):
            choque = next((o for o in ocupadas
                           if tx < o[2] and tx + w > o[0] and ty < o[3] and ty + h > o[1]), None)
            if not choque:
                break
            ty = choque[3] + 1
        ty = max(0, min(ty, H - h))
        ocupadas.append((tx, ty, tx + w, ty + h))
    return ocupadas


def _resumo(anomalias: list[dict], score: int) -> str:
    if not anomalias:
        return "Nenhuma anomalia visível detectada. Ponto em condição aparentemente normal."
    n_crit = sum(1 for a in anomalias if a["severidade"] == "critico")
    partes = [f"{len(anomalias)} anomalia(s) detectada(s)"]
    if n_crit:
        partes.append(f"{n_crit} crítica(s)")
    partes.append(f"Índice de Saúde {score}/100")
    return " · ".join(partes) + "."
