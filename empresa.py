"""
Cadastros da empresa usados em todo o sistema: perfis de acesso, pessoas com
qualificações (treinamentos NR, ASO) e tipos de documento configuráveis.

A conferência cruzada de documentos vive aqui: o que a IA leu no documento
(pessoas, equipamento, data) é conferido contra o cadastro da empresa — sem
enviar o cadastro para o provedor de IA (minimização de dados, LGPD).
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import date, datetime

# ── Perfis de acesso ──────────────────────────────────────────────────────────
PERFIS = {
    "admin": "Administrador",
    "rh": "RH",
    "manutencao": "Manutenção",
    "operador": "Operador",
}

# ── Qualificações com validade ────────────────────────────────────────────────
QUALIFICACOES = {
    "ASO": "Atestado de Saúde Ocupacional",
    "NR-10": "Segurança em eletricidade",
    "NR-12": "Segurança em máquinas",
    "NR-33": "Espaço confinado",
    "NR-35": "Trabalho em altura",
    "Integração": "Integração de segurança",
}
AVISO_DIAS = 30   # "vence em breve"

VINCULOS = ["CLT", "Terceiro", "Estagiário", "Aprendiz", "Temporário"]

# ── Tipos de documento que já vêm configurados ────────────────────────────────
TIPOS_PADRAO = [
    {"nome": "Permissão de Trabalho — Eletricidade", "setor": "Segurança do Trabalho",
     "descricao": "Liberação de serviço em painéis, motores e circuitos energizáveis.",
     "campos": ["Número da PT", "Data e horário de validade", "Local / equipamento",
                "Descrição da atividade", "Executante(s) com matrícula", "Riscos e medidas de controle",
                "Bloqueio e etiquetagem (LOTO) confirmado", "Assinatura do emitente",
                "Assinatura do executante"],
     "qualificacoes": ["ASO", "NR-10"], "exige_maquina": 1},
    {"nome": "Permissão de Trabalho — Altura", "setor": "Segurança do Trabalho",
     "descricao": "Liberação de serviço acima de 2 metros.",
     "campos": ["Número da PT", "Data e horário de validade", "Local", "Descrição da atividade",
                "Executante(s) com matrícula", "Ponto de ancoragem e EPI", "Assinatura do emitente",
                "Assinatura do executante"],
     "qualificacoes": ["ASO", "NR-35"], "exige_maquina": 0},
    {"nome": "Ordem de Serviço de Manutenção", "setor": "Manutenção",
     "descricao": "Registro do serviço executado no equipamento.",
     "campos": ["Número da OS", "Equipamento", "Descrição do serviço", "Executante com matrícula",
                "Horas trabalhadas", "Peças utilizadas", "Data de conclusão", "Assinatura do responsável"],
     "qualificacoes": ["ASO"], "exige_maquina": 1},
    {"nome": "Checklist NR-12 da máquina", "setor": "Segurança do Trabalho",
     "descricao": "Verificação das proteções e dispositivos de segurança da máquina.",
     "campos": ["Máquina", "Proteções verificadas", "Botão de emergência testado",
                "Responsável com matrícula", "Data", "Assinatura"],
     "qualificacoes": ["NR-12"], "exige_maquina": 1},
    {"nome": "Ficha de entrega de EPI", "setor": "RH",
     "descricao": "Entrega de equipamento de proteção individual ao colaborador.",
     "campos": ["Colaborador e matrícula", "EPIs entregues com número do CA", "Data",
                "Assinatura do colaborador"],
     "qualificacoes": [], "exige_maquina": 0},
    {"nome": "Outro documento", "setor": "Geral",
     "descricao": "Qualquer documento: a IA confere preenchimento, cálculos e assinaturas.",
     "campos": [], "qualificacoes": [], "exige_maquina": 0},
]

SQL_TABELAS = """
    CREATE TABLE IF NOT EXISTS colaboradores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        setor TEXT,
        funcao TEXT,
        vinculo TEXT,
        gestor TEXT,
        admissao DATE,
        ativo INTEGER DEFAULT 1,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS qualificacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colaborador_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        valido_ate DATE NOT NULL,
        atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (colaborador_id, tipo),
        FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS tipos_documento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        setor TEXT,
        descricao TEXT,
        campos_obrigatorios TEXT,
        qualificacoes_exigidas TEXT,
        exige_maquina INTEGER DEFAULT 0,
        ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        entidade TEXT,
        entidade_id INTEGER,
        detalhe TEXT,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_qualificacoes_validade ON qualificacoes(valido_ate);
    CREATE INDEX IF NOT EXISTS idx_auditoria_data ON auditoria(criado_em);
"""


def criar_tabelas(conn) -> None:
    conn.executescript(SQL_TABELAS)
    if not conn.execute("SELECT 1 FROM tipos_documento LIMIT 1").fetchone():
        for t in TIPOS_PADRAO:
            conn.execute(
                "INSERT INTO tipos_documento (nome, setor, descricao, campos_obrigatorios, "
                "qualificacoes_exigidas, exige_maquina) VALUES (?,?,?,?,?,?)",
                (t["nome"], t["setor"], t["descricao"], "\n".join(t["campos"]),
                 ",".join(t["qualificacoes"]), t["exige_maquina"]))


def tipo_para_dict(row) -> dict | None:
    if not row:
        return None
    return {
        "id": row["id"], "nome": row["nome"], "setor": row["setor"] or "", "descricao": row["descricao"] or "",
        "campos": [c.strip() for c in (row["campos_obrigatorios"] or "").splitlines() if c.strip()],
        "qualificacoes": [q.strip() for q in (row["qualificacoes_exigidas"] or "").split(",") if q.strip()],
        "exige_maquina": bool(row["exige_maquina"]), "ativo": bool(row["ativo"]),
    }


# ── Datas e validade ──────────────────────────────────────────────────────────
def para_data(valor) -> date | None:
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    txt = str(valor).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    return None


def situacao(valido_ate, referencia: date | None = None, hoje: date | None = None) -> str:
    """'vencida' na data de referência, 'vence_em_breve' (até 30 dias a partir de hoje) ou 'valida'."""
    hoje = hoje or date.today()
    ref = referencia or hoje
    fim = para_data(valido_ate)
    if not fim:
        return "sem_registro"
    if fim < ref:
        return "vencida"
    if (fim - hoje).days <= AVISO_DIAS:
        return "vence_em_breve"
    return "valida"


def qualificacoes_de(conn, colaborador_id: int) -> dict[str, str]:
    return {r["tipo"]: r["valido_ate"] for r in conn.execute(
        "SELECT tipo, valido_ate FROM qualificacoes WHERE colaborador_id = ?", (colaborador_id,))}


# ── Busca de pessoa e de equipamento ──────────────────────────────────────────
def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def _so_digitos(t) -> str:
    return re.sub(r"\D", "", str(t or ""))


def encontrar_pessoa(conn, nome: str | None, matricula: str | None):
    """Pela matrícula (exata); se não houver, pelo nome (todas as palavras do nome lido)."""
    mat = _so_digitos(matricula)
    if mat:
        r = conn.execute("SELECT * FROM colaboradores WHERE matricula = ?", (mat,)).fetchone()
        if r:
            return r, "matricula"
    palavras = [p for p in normalizar(nome or "").split() if len(p) > 2]
    if not palavras:
        return None, None
    candidatos = [r for r in conn.execute("SELECT * FROM colaboradores")
                  if all(p in normalizar(r["nome"]).split() for p in palavras)]
    if len(candidatos) == 1:
        return candidatos[0], "nome"
    return None, ("ambiguo" if candidatos else None)


def encontrar_maquina(conn, texto: str | None):
    """Pela etiqueta (ex.: RS-01) ou pelas palavras do nome da máquina."""
    if not texto:
        return None
    alvo = normalizar(texto)
    maquinas = conn.execute("SELECT id, nome, modelo FROM maquinas").fetchall()
    for tag in re.findall(r"[a-z]{1,4}\s?-?\s?\d{1,4}", alvo):
        tag_n = re.sub(r"[\s-]", "", tag)
        achadas = [m for m in maquinas if tag_n in re.sub(r"[\s-]", "", normalizar(m["nome"]))]
        if len(achadas) == 1:
            return achadas[0]
    melhores = sorted(((len(set(alvo.split()) & set(normalizar(m["nome"]).split())), m) for m in maquinas),
                      key=lambda x: -x[0])
    if melhores and melhores[0][0] >= 2 and (len(melhores) == 1 or melhores[1][0] < melhores[0][0]):
        return melhores[0][1]
    return None


# ── Conferência cruzada ───────────────────────────────────────────────────────
def conferir(conn, tipo: dict | None, extraido: dict, maquina_id_informada=None,
             hoje: date | None = None) -> dict:
    """
    Confere o que foi lido no documento contra o cadastro da empresa.
    Retorna {status, conferencias[], pessoas[], maquina, data_referencia}.
    status: 'bloqueado' (pessoa sem habilitação válida / desligada),
            'pendencias' (algo a corrigir) ou 'aprovado'.
    """
    hoje = hoje or date.today()
    exigidas = (tipo or {}).get("qualificacoes", [])
    data_doc = para_data(extraido.get("data_documento"))
    referencia = data_doc if data_doc and data_doc <= hoje else hoje
    conferencias: list[dict] = []
    pessoas_out: list[dict] = []

    vistos = set()
    for p in extraido.get("pessoas") or []:
        nome, mat = (p.get("nome") or "").strip(), (p.get("matricula") or "").strip()
        if not nome and not mat:
            continue
        r, como = encontrar_pessoa(conn, nome, mat)
        rotulo = nome or f"matrícula {mat}"
        if not r:
            sev = "medio" if como == "ambiguo" else "alto"
            conferencias.append({
                "categoria": "cadastro", "severidade": sev,
                "titulo": f"{rotulo}: {'mais de uma pessoa com esse nome' if como == 'ambiguo' else 'não encontrado no cadastro'}",
                "descricao": "Confira a matrícula no documento." if como == "ambiguo"
                             else "Pessoa sem cadastro não pode ser executante. Cadastre-a ou corrija a matrícula."})
            pessoas_out.append({"nome": nome, "matricula": mat, "papel": p.get("papel"), "encontrado": False})
            continue
        if r["id"] in vistos:
            continue
        vistos.add(r["id"])
        quals = qualificacoes_de(conn, r["id"])
        info = {"nome": r["nome"], "matricula": r["matricula"], "funcao": r["funcao"], "setor": r["setor"],
                "vinculo": r["vinculo"], "papel": p.get("papel"), "encontrado": True, "ativo": bool(r["ativo"]),
                "colaborador_id": r["id"], "qualificacoes": []}
        if mat and _so_digitos(mat) != r["matricula"]:
            conferencias.append({"categoria": "cadastro", "severidade": "medio",
                                 "titulo": f"{r['nome']}: matrícula diferente do cadastro",
                                 "descricao": f"No documento: {mat}. No cadastro: {r['matricula']}."})
        if not r["ativo"]:
            conferencias.append({"categoria": "cadastro", "severidade": "alto",
                                 "titulo": f"{r['nome']}: colaborador desligado",
                                 "descricao": "Pessoa inativa no cadastro não pode constar como executante."})
        # Habilitações são exigidas de quem executa; emitente e responsável só precisam estar ativos
        papel = normalizar(p.get("papel") or "")
        exigidas_pessoa = [] if papel in ("emitente", "responsavel", "aprovador") else exigidas
        info["exigido"] = bool(exigidas_pessoa)
        for q in exigidas_pessoa:
            st = situacao(quals.get(q), referencia, hoje)
            info["qualificacoes"].append({"tipo": q, "valido_ate": quals.get(q), "situacao": st})
            if st == "sem_registro":
                conferencias.append({"categoria": "habilitacao", "severidade": "alto",
                                     "titulo": f"{r['nome']}: sem {q} registrado",
                                     "descricao": f"Este documento exige {q} ({QUALIFICACOES.get(q, q)})."})
            elif st == "vencida":
                conferencias.append({"categoria": "habilitacao", "severidade": "alto",
                                     "titulo": f"{r['nome']}: {q} vencido em {para_data(quals[q]).strftime('%d/%m/%Y')}",
                                     "descricao": f"Não pode executar este serviço até renovar o {q}."})
            elif st == "vence_em_breve":
                dias = (para_data(quals[q]) - hoje).days
                conferencias.append({"categoria": "validade", "severidade": "baixo",
                                     "titulo": f"{r['nome']}: {q} vence em {dias} dia(s)",
                                     "descricao": "Válido para este documento; agende a renovação."})
        pessoas_out.append(info)

    if exigidas and not any(p.get("exigido") for p in pessoas_out):
        conferencias.append({"categoria": "cadastro", "severidade": "alto",
                             "titulo": "Nenhum executante identificado",
                             "descricao": "Informe nome e matrícula de quem vai executar o serviço."})

    maquina = None
    if maquina_id_informada:
        m = conn.execute("SELECT id, nome, modelo FROM maquinas WHERE id = ?", (maquina_id_informada,)).fetchone()
    else:
        m = encontrar_maquina(conn, extraido.get("equipamento"))
    if m:
        abertas = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias WHERE maquina_id = ? "
                               "AND status IN ('Aberta', 'Em andamento')", (m["id"],)).fetchone()["n"]
        maquina = {"id": m["id"], "nome": m["nome"], "abertas": abertas}
        if abertas:
            conferencias.append({"categoria": "equipamento", "severidade": "info",
                                 "titulo": f"{m['nome']}: {abertas} ocorrência(s) em aberto",
                                 "descricao": "Confira se o serviço deste documento trata alguma delas."})
    elif (tipo or {}).get("exige_maquina"):
        lido = extraido.get("equipamento")
        conferencias.append({"categoria": "equipamento", "severidade": "medio",
                             "titulo": f"Equipamento {'“' + lido + '” ' if lido else ''}não identificado no cadastro",
                             "descricao": "Use a etiqueta da máquina (ex.: RS-01) para rastrear o serviço."})

    if data_doc and data_doc > hoje:
        conferencias.append({"categoria": "cadastro", "severidade": "medio",
                             "titulo": f"Data do documento no futuro ({data_doc.strftime('%d/%m/%Y')})",
                             "descricao": "Confira a data preenchida."})

    bloqueia = any(c["severidade"] == "alto" and c["categoria"] in ("habilitacao", "cadastro") for c in conferencias)
    return {"conferencias": conferencias, "pessoas": pessoas_out, "maquina": maquina,
            "data_referencia": referencia.isoformat(), "bloqueia": bloqueia}


def status_final(conferencia: dict, problemas_ia: list[dict]) -> str:
    if conferencia["bloqueia"]:
        return "bloqueado"
    pend = any(c["severidade"] in ("alto", "medio") for c in conferencia["conferencias"])
    pend = pend or any((p.get("severidade") or "medio") in ("alto", "medio") for p in problemas_ia)
    return "pendencias" if pend else "aprovado"


# ── Importação de pessoas por planilha (CSV) ──────────────────────────────────
COLUNAS_CSV = ["matricula", "nome", "setor", "funcao", "vinculo", "gestor", "admissao"] + list(QUALIFICACOES)


def modelo_csv() -> str:
    linhas = [";".join(COLUNAS_CSV),
              "10001;Maria Exemplo;Manutenção;Eletricista;CLT;João Gestor;2021-03-15;2027-03-01;2027-05-10;;;;2026-12-01"]
    return "﻿" + "\n".join(linhas) + "\n"


def importar_csv(conn, conteudo: bytes) -> dict:
    """Cria ou atualiza pessoas pela matrícula. Colunas de qualificação trazem a validade."""
    texto = conteudo.decode("utf-8-sig", errors="replace")
    amostra = texto[:2000]
    sep = ";" if amostra.count(";") >= amostra.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=sep)
    cab = {normalizar(c).replace(" ", ""): c for c in (leitor.fieldnames or [])}
    def col(linha, nome):
        chave = cab.get(normalizar(nome).replace(" ", ""))
        return (linha.get(chave) or "").strip() if chave else ""
    criados = atualizados = 0
    erros: list[str] = []
    for n, linha in enumerate(leitor, 2):
        mat, nome = _so_digitos(col(linha, "matricula")), col(linha, "nome")
        if not mat or not nome:
            erros.append(f"Linha {n}: matrícula e nome são obrigatórios.")
            continue
        adm = para_data(col(linha, "admissao"))
        existe = conn.execute("SELECT id FROM colaboradores WHERE matricula = ?", (mat,)).fetchone()
        dados = (nome, col(linha, "setor"), col(linha, "funcao"), col(linha, "vinculo") or "CLT",
                 col(linha, "gestor"), adm.isoformat() if adm else None)
        if existe:
            conn.execute("UPDATE colaboradores SET nome=?, setor=?, funcao=?, vinculo=?, gestor=?, admissao=? "
                         "WHERE id=?", dados + (existe["id"],))
            cid = existe["id"]
            atualizados += 1
        else:
            cid = conn.execute("INSERT INTO colaboradores (nome, setor, funcao, vinculo, gestor, admissao, matricula) "
                               "VALUES (?,?,?,?,?,?,?)", dados + (mat,)).lastrowid
            criados += 1
        for q in QUALIFICACOES:
            valor = col(linha, q)
            if not valor:
                continue
            d = para_data(valor)
            if not d:
                erros.append(f"Linha {n}: data inválida em {q} ({valor}).")
                continue
            salvar_qualificacao(conn, cid, q, d)
    return {"criados": criados, "atualizados": atualizados, "erros": erros[:20]}


def salvar_qualificacao(conn, colaborador_id: int, tipo: str, valido_ate: date | None) -> None:
    if valido_ate is None:
        conn.execute("DELETE FROM qualificacoes WHERE colaborador_id = ? AND tipo = ?", (colaborador_id, tipo))
        return
    conn.execute(
        "INSERT INTO qualificacoes (colaborador_id, tipo, valido_ate) VALUES (?,?,?) "
        "ON CONFLICT(colaborador_id, tipo) DO UPDATE SET valido_ate = excluded.valido_ate, "
        "atualizado_em = CURRENT_TIMESTAMP", (colaborador_id, tipo, valido_ate.isoformat()))
