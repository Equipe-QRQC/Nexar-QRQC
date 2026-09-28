"""
Sintomas por tipo de peça e diagnóstico local (sem IA).

O registro de ocorrência começa pela peça tocada no 3D. Cada peça tem um tipo
(mecânico, elétrico, estrutura, segurança) e o operador escolhe o sintoma entre
os que fazem sentido para esse tipo. Quando a IA não responde, o diagnóstico é
montado aqui a partir da peça, do sintoma e das soluções que já funcionaram
nessa peça — sempre identificado como "roteiro com base no histórico", nunca
como texto gerado por IA.
"""
from __future__ import annotations

import unicodedata

# id → (nome, ícone Font Awesome, causas prováveis, passos de inspeção)
SINTOMAS: dict[str, dict] = {
    "vazamento": {
        "nome": "Vazamento", "icone": "fa-droplet",
        "causas": "desgaste ou dano na vedação, conexão frouxa ou superfície de vedação riscada",
        "passos": ["Limpar a região e localizar o ponto exato do vazamento",
                   "Verificar vedações, retentores e conexões",
                   "Inspecionar a haste ou o eixo por riscos e corrosão",
                   "Conferir o nível do fluido e completar se necessário"],
    },
    "ruido": {
        "nome": "Ruído anormal", "icone": "fa-volume-high",
        "causas": "falta de lubrificação, rolamento ou engrenagem desgastados, ou peça solta",
        "passos": ["Identificar em qual movimento o ruído aparece",
                   "Verificar nível e estado do lubrificante",
                   "Inspecionar rolamentos e engrenagens por desgaste",
                   "Reapertar fixações próximas"],
    },
    "vibracao": {
        "nome": "Vibração", "icone": "fa-wave-square",
        "causas": "fixação solta, desbalanceamento, desalinhamento ou folga em mancais",
        "passos": ["Verificar o aperto das fixações e chumbadores",
                   "Medir a vibração e comparar com o histórico",
                   "Conferir alinhamento e folgas",
                   "Inspecionar mancais e rolamentos"],
    },
    "aquecimento": {
        "nome": "Aquecimento", "icone": "fa-temperature-high",
        "causas": "ventilação obstruída, sobrecarga, falta de lubrificação ou atrito excessivo",
        "passos": ["Medir a temperatura e comparar com o normal de operação",
                   "Limpar ventiladores, aletas e entradas de ar",
                   "Verificar lubrificação",
                   "Conferir corrente e carga de trabalho"],
    },
    "folga": {
        "nome": "Folga / desgaste", "icone": "fa-arrows-left-right",
        "causas": "desgaste de guias, réguas de ajuste, engrenagens ou parafusos frouxos",
        "passos": ["Medir a folga com relógio comparador",
                   "Verificar parafusos de fixação e aplicar o torque especificado",
                   "Ajustar réguas, gibs ou pré-carga",
                   "Substituir peças desgastadas se a folga persistir"],
    },
    "medida": {
        "nome": "Peça fora de medida", "icone": "fa-ruler-combined",
        "causas": "ferramenta gasta, desalinhamento ou folga no conjunto",
        "passos": ["Medir a peça e registrar o desvio",
                   "Verificar o estado da ferramenta de corte",
                   "Conferir alinhamento do conjunto",
                   "Verificar folgas nos carros e fixações"],
    },
    "travamento": {
        "nome": "Travamento", "icone": "fa-lock",
        "causas": "sujeira, falta de lubrificação, peça deformada ou quebrada",
        "passos": ["Desligar e liberar o movimento manualmente, se seguro",
                   "Limpar e lubrificar guias e fusos",
                   "Procurar cavacos, sujeira ou peça deformada",
                   "Verificar a transmissão que aciona o movimento"],
    },
    "quebra": {
        "nome": "Quebra / trinca", "icone": "fa-burst",
        "causas": "sobrecarga, impacto ou fadiga do material",
        "passos": ["Isolar a área e não operar a máquina",
                   "Fotografar e registrar a extensão do dano",
                   "Verificar a causa (colisão, sobrecarga)",
                   "Substituir a peça antes de voltar a operar"],
    },
    "nao_liga": {
        "nome": "Não liga", "icone": "fa-power-off",
        "causas": "falta de alimentação, fusível ou disjuntor atuado, ou falha no comando",
        "passos": ["Verificar alimentação e disjuntor",
                   "Testar fusíveis",
                   "Conferir botões de emergência e intertravamentos",
                   "Medir tensões no painel com multímetro"],
    },
    "desarma": {
        "nome": "Desarma / fusível", "icone": "fa-bolt",
        "causas": "sobrecorrente por sobrecarga mecânica, curto ou isolação danificada",
        "passos": ["Medir a corrente do motor",
                   "Verificar isolação de cabos e bobinas",
                   "Conferir se há travamento mecânico",
                   "Substituir o fusível só após achar a causa"],
    },
    "alarme": {
        "nome": "Alarme no painel", "icone": "fa-triangle-exclamation",
        "causas": "condição fora do normal detectada pelo controlador",
        "passos": ["Anotar o código do alarme",
                   "Consultar o manual do fabricante para o código",
                   "Verificar sensores relacionados",
                   "Registrar se o alarme se repete"],
    },
    "intermitente": {
        "nome": "Falha intermitente", "icone": "fa-signal",
        "causas": "mau contato, cabo com condutor rompido ou conector oxidado",
        "passos": ["Verificar conectores e bornes",
                   "Movimentar o cabo e observar se a falha aparece",
                   "Inspecionar pontos de atrito do cabo",
                   "Medir continuidade dos condutores"],
    },
    "cabo": {
        "nome": "Cabo danificado", "icone": "fa-plug-circle-xmark",
        "causas": "atrito, esmagamento ou fixação inadequada",
        "passos": ["Isolar a energia antes de manusear",
                   "Avaliar se os condutores foram expostos",
                   "Refazer a fixação para eliminar o atrito",
                   "Substituir o trecho danificado"],
    },
    "nao_atua": {
        "nome": "Não atua", "icone": "fa-hand",
        "causas": "contato gasto, fiação solta ou dispositivo de segurança danificado",
        "passos": ["Bloquear a máquina: dispositivo de segurança sem função",
                   "Testar os contatos do dispositivo",
                   "Verificar fiação e relé de segurança",
                   "Substituir e testar antes de liberar a máquina"],
    },
    "danificado": {
        "nome": "Danificado", "icone": "fa-house-crack",
        "causas": "impacto, desgaste ou uso inadequado",
        "passos": ["Avaliar a extensão do dano",
                   "Verificar se a função de proteção continua",
                   "Substituir ou reparar",
                   "Registrar a causa do dano"],
    },
    "outro": {
        "nome": "Outro", "icone": "fa-ellipsis",
        "causas": "a confirmar na inspeção",
        "passos": ["Descrever o que foi observado",
                   "Verificar fixações, lubrificação e conexões da peça",
                   "Comparar com o funcionamento normal"],
    },
}

SINTOMAS_POR_TIPO = {
    "mecanico": ["vazamento", "ruido", "vibracao", "aquecimento", "folga", "medida", "travamento", "quebra"],
    "estrutura": ["vibracao", "folga", "quebra", "vazamento"],
    "eletrico": ["nao_liga", "desarma", "alarme", "intermitente", "cabo", "aquecimento"],
    "seguranca": ["nao_atua", "danificado", "folga"],
}


def _normalizar(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


def sintomas_do_tipo(tipo: str) -> list[dict]:
    ids = SINTOMAS_POR_TIPO.get(_normalizar(tipo), SINTOMAS_POR_TIPO["mecanico"]) + ["outro"]
    return [{"id": i, "nome": SINTOMAS[i]["nome"], "icone": SINTOMAS[i]["icone"]} for i in ids]


def nome_sintoma(sintoma: str | None) -> str | None:
    return SINTOMAS.get(sintoma or "", {}).get("nome")


def montar_diagnostico(componente: str, sintoma: str | None, solucoes: list[dict],
                       parada: bool = False, risco: bool = False) -> str:
    """
    Roteiro de inspeção a partir da peça, do sintoma e do histórico dessa peça.
    Mantém as 4 seções do diagnóstico da IA, para o 3D destacar a peça do mesmo jeito.
    """
    s = SINTOMAS.get(sintoma or "", SINTOMAS["outro"])
    linhas = ["**1. Causa provável**"]
    if solucoes:
        u = solucoes[0]
        linhas.append(f"{componente}: {s['nome'].lower()}. Esta peça já teve {len(solucoes)} "
                      f"ocorrência(s) resolvida(s); a última foi resolvida assim: {u['solucao']}")
    else:
        linhas.append(f"{componente}: {s['nome'].lower()}. Causas mais comuns: {s['causas']}.")
    linhas += ["", "**2. Componentes a verificar**", f"- {componente}: local indicado pelo operador no 3D"]
    linhas += ["", "**3. Procedimento de inspeção**",
               "1. Isolar a máquina com bloqueio e etiquetagem (LOTO) antes de qualquer intervenção"]
    for n, passo in enumerate(s["passos"], 2):
        linhas.append(f"{n}. {passo}")
    linhas += ["", "**4. Quando escalar para o fabricante**"]
    if risco:
        linhas.append("- Há risco para pessoas: a máquina só volta a operar após liberação da segurança")
    linhas.append("- O problema volta depois da solução aplicada")
    linhas.append("- É preciso abrir redutores, motores ou partes lacradas pelo fabricante")
    if parada:
        linhas.append("- A máquina continua parada após o procedimento acima")
    return "\n".join(linhas)
