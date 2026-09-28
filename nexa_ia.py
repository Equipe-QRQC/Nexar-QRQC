"""
nexa_ia.py — Agente técnico Nexa IA (OpenAI tool-calling)

Investiga ocorrências industriais consultando dados reais do banco e retorna
diagnóstico estruturado com componentes do modelo 3D identificados.
"""
import os
import json
import re
import logging
import sqlite3

logger = logging.getLogger("nexar.nexa_ia")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DB_PATH = os.getenv("DATABASE_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "qrqc.db")

_openai_client = None

MSG_INDISPONIVEL = "A análise por IA está indisponível no momento. Tente novamente em alguns minutos."


def _get_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
            key = os.getenv("OPENAI_API_KEY", "")
            if key:
                _openai_client = OpenAI(api_key=key)
        except Exception as e:
            logger.warning(f"[nexa_ia] falha ao inicializar OpenAI: {e}")
    return _openai_client


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Implementação das tools ────────────────────────────────────────────────────

def _get_machine_info(machine_id: int) -> dict:
    conn = _db()
    row = conn.execute("SELECT * FROM maquinas WHERE id = ?", (machine_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": f"Máquina {machine_id} não encontrada"}
    return {k: row[k] for k in row.keys()}


def _get_machine_components(machine_id: int) -> list:
    conn = _db()
    rows = conn.execute(
        "SELECT component_id, name, type, description FROM machine_components WHERE maquina_id = ?",
        (machine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_machine_history(machine_id: int) -> list:
    conn = _db()
    rows = conn.execute(
        """SELECT id, data_ocorrencia, descricao, tipo_ocorrencia, nivel_impacto,
                  status, solucao_aplicada, componente_real, data_resolucao
           FROM ocorrencias
           WHERE maquina_id = ?
           ORDER BY data_registro DESC LIMIT 20""",
        (machine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_similar_occurrences(machine_id: int, description: str) -> list:
    conn = _db()
    words = [w for w in description.lower().split() if len(w) > 4][:5]
    if not words:
        conn.close()
        return []
    conditions = " OR ".join(["LOWER(descricao) LIKE ?" for _ in words])
    params = [f"%{w}%" for w in words] + [machine_id]
    rows = conn.execute(
        f"""SELECT id, data_ocorrencia, descricao, solucao_aplicada, componente_real
            FROM ocorrencias
            WHERE ({conditions}) AND maquina_id = ? AND status = 'Resolvida'
            LIMIT 10""",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_previous_solutions(machine_id: int) -> list:
    conn = _db()
    rows = conn.execute(
        """SELECT descricao, solucao_aplicada, componente_real, data_resolucao
           FROM ocorrencias
           WHERE maquina_id = ? AND status = 'Resolvida' AND solucao_aplicada IS NOT NULL
           ORDER BY data_resolucao DESC LIMIT 10""",
        (machine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_machine_documentation(machine_id: int) -> list:
    conn = _db()
    rows = conn.execute(
        "SELECT nome, caminho, tipo FROM diagramas WHERE maquina_id = ?",
        (machine_id,),
    ).fetchall()
    conn.close()
    return [{"nome": r["nome"], "tipo": r["tipo"]} for r in rows]


# ── Definições das tools para a API OpenAI ────────────────────────────────────

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_machine_info",
            "description": "Retorna informações gerais da máquina (nome, modelo, fabricante, setor, descrição técnica).",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"}
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_machine_components",
            "description": (
                "Retorna TODOS os componentes do modelo 3D da máquina com seus component_ids. "
                "OBRIGATÓRIO chamar antes de criar o diagnóstico final — só use component_ids "
                "retornados por esta ferramenta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"}
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_machine_history",
            "description": "Retorna o histórico de ocorrências anteriores da máquina.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"}
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_similar_occurrences",
            "description": "Busca ocorrências anteriores resolvidas com sintomas semelhantes à descrição fornecida.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"},
                    "description": {"type": "string", "description": "Descrição do problema atual"},
                },
                "required": ["machine_id", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_solutions",
            "description": "Retorna soluções aplicadas em ocorrências resolvidas desta máquina.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"}
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_machine_documentation",
            "description": "Retorna lista de documentos técnicos e diagramas disponíveis para a máquina.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "integer", "description": "ID da máquina"}
                },
                "required": ["machine_id"],
            },
        },
    },
]

_TOOL_MAP = {
    "get_machine_info": _get_machine_info,
    "get_machine_components": _get_machine_components,
    "get_machine_history": _get_machine_history,
    "get_similar_occurrences": _get_similar_occurrences,
    "get_previous_solutions": _get_previous_solutions,
    "get_machine_documentation": _get_machine_documentation,
}

_SYSTEM_PROMPT = """Você é a Nexar IA — agente especialista em diagnóstico de falhas industriais.

REGRAS ABSOLUTAS:
1. Chame get_machine_components ANTES de criar o diagnóstico final.
2. Use APENAS os component_ids retornados por get_machine_components. Nunca invente IDs.
3. Baseie hipóteses SOMENTE em dados consultados pelas ferramentas.
4. Nunca sugira controle físico de máquinas (ligar, desligar, comandos PLC).
5. O diagnóstico é sugestão — decisão final é sempre do técnico.

PROCESSO:
1. get_machine_info → entender a máquina
2. get_machine_components → obter IDs reais do modelo 3D
3. get_machine_history → padrões históricos
4. get_similar_occurrences → falhas semelhantes anteriores
5. get_previous_solutions → soluções que funcionaram antes
6. Formular hipóteses e retornar diagnóstico

RESPOSTA FINAL — retorne APENAS o JSON abaixo (sem texto antes ou depois):
{
  "summary": "Resumo técnico da possível causa em 1-2 frases",
  "severity": "high|medium|low",
  "pattern_analysis": "Análise de padrão no histórico (null se dados insuficientes)",
  "components": [
    {
      "component_id": "id_exato_retornado_por_get_machine_components",
      "component_name": "Nome legível do componente",
      "probability": 0.82,
      "severity": "high|medium|low",
      "reason": "Por que este componente é suspeito (1-2 frases baseadas nos dados)"
    }
  ],
  "recommended_actions": ["Ação 1", "Ação 2", "Ação 3"],
  "technical_warning": "O diagnóstico é sugestão baseada em dados históricos. Inspeção deve ser realizada por técnico qualificado."
}"""


def _extract_json(text: str) -> dict:
    """Extrai o primeiro objeto JSON de uma string."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise ValueError("Nenhum JSON válido encontrado na resposta")


def analisar_ocorrencia(ocorrencia: dict, machine_id: int) -> dict:
    """
    Executa o agente Nexa IA para diagnosticar uma ocorrência.
    Retorna diagnóstico estruturado ou {'error': ...}.
    """
    client = _get_client()
    if not client:
        logger.warning("[nexa_ia] OPENAI_API_KEY não configurada")
        return {"error": MSG_INDISPONIVEL}

    user_msg = (
        f"Analise esta ocorrência industrial:\n\n"
        f"Máquina ID: {machine_id}\n"
        f"Operador: {ocorrencia.get('nome_operador', 'N/A')}\n"
        f"Data: {ocorrencia.get('data_ocorrencia', 'N/A')}\n"
        f"Tipo: {ocorrencia.get('tipo_ocorrencia', 'N/A')}\n"
        f"Impacto: {ocorrencia.get('nivel_impacto', 'N/A')}\n"
        f"Recorrente: {ocorrencia.get('problema_recorrente', 'N/A')}\n\n"
        f"DESCRIÇÃO:\n{ocorrencia.get('descricao', '')}\n\n"
        f"DETALHAMENTO TÉCNICO:\n{ocorrencia.get('detalhamento_tecnico', '')}\n\n"
        "Investigue usando as ferramentas e retorne o diagnóstico estruturado em JSON."
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    steps_log: list[str] = []
    max_iter = 15

    for _ in range(max_iter):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=_TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )
        except Exception as api_err:
            err_msg = str(api_err)
            if "credit_balance_exhausted" in err_msg or "insufficient_quota" in err_msg:
                logger.error("[nexa_ia] créditos OpenAI esgotados")
                return {"error": MSG_INDISPONIVEL, "_steps": steps_log}
            if "invalid_api_key" in err_msg or "Incorrect API key" in err_msg:
                logger.error("[nexa_ia] OPENAI_API_KEY inválida")
                return {"error": MSG_INDISPONIVEL, "_steps": steps_log}
            logger.error(f"[nexa_ia] erro na API OpenAI: {api_err}")
            return {"error": MSG_INDISPONIVEL, "_steps": steps_log}

        msg = resp.choices[0].message
        messages.append(msg)

        if msg.tool_calls:
            tool_results = []
            for tc in msg.tool_calls:
                fn = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                    result = _TOOL_MAP[fn](**args)
                    steps_log.append(fn)
                    logger.info(f"[nexa_ia] {fn}({args})")
                except Exception as exc:
                    result = {"error": str(exc)}
                    logger.warning(f"[nexa_ia] {fn} erro: {exc}")

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
            messages.extend(tool_results)

        else:
            content = (msg.content or "").strip()
            try:
                diagnosis = _extract_json(content)
            except Exception as exc:
                logger.error(f"[nexa_ia] falha ao parsear JSON: {exc}\n{content[:500]}")
                diagnosis = {"error": "A IA retornou uma resposta inválida. Tente analisar novamente."}

            diagnosis["_steps"] = steps_log
            diagnosis["_model"] = OPENAI_MODEL
            return diagnosis

    return {"error": "A análise não foi concluída. Tente novamente.", "_steps": steps_log}
