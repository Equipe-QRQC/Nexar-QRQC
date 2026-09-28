"""
Importação de CAD pelo próprio sistema: STEP → GLB → componentes sugeridos.

A conversão roda num processo separado (scripts/cad_para_glb.py), para um CAD
pesado não derrubar o servidor. Depois, as peças são agrupadas pelo nome
(ex.: "Bed Way (1)_Dfaut" → "Bed Way") e fixadores (parafusos, porcas...)
ficam de fora: eles acompanham o componente mais próximo no visualizador.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import unicodedata
import zipfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_ORIGEM = os.path.join(RAIZ, "cad_importados")          # fora de static: não é servido
PASTA_MODELOS = os.path.join(RAIZ, "static", "models3d")
EXTENSOES = (".step", ".stp")

FIXADORES = re.compile(
    r"\b(screw|nut|washer|bolt|rivet|pin|key|ring|spring|tie|lug|crimp|circlip|parafuso|porca|arruela|"
    r"rebite|pino|chaveta|anel|mola|abracadeira|bucha de fixacao)s?\b|\bm\d+(\.\d+)?\s?x\s?\d+", re.I)


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:48] or "modelo"


def slug_livre(base: str) -> str:
    s, n = slug(base), 2
    candidato = s
    while os.path.exists(os.path.join(PASTA_MODELOS, candidato)):
        candidato = f"{s}-{n}"
        n += 1
    return candidato


IGNORAR_ARQUIVOS = re.compile(r"working.?space|workspace|envelope|alcance", re.I)


def extrair_steps(caminho: str, destino_dir: str) -> list[str]:
    """
    Aceita .step/.stp ou um .zip. O zip pode trazer uma montagem (um STEP) ou
    uma peça por arquivo (comum em catálogos de fabricante). Retorna os STEPs.
    """
    if caminho.lower().endswith(EXTENSOES):
        return [caminho]
    if not zipfile.is_zipfile(caminho):
        raise ValueError("Envie um arquivo STEP (.step/.stp) ou um .zip com o STEP.")
    saida = []
    with zipfile.ZipFile(caminho) as z:
        for info in z.infolist():
            nome = os.path.basename(info.filename)
            if info.is_dir() or not nome.lower().endswith(EXTENSOES) or IGNORAR_ARQUIVOS.search(nome):
                continue
            alvo = os.path.join(destino_dir, re.sub(r"[^\w.\- ()]", "_", nome))
            with z.open(info) as src, open(alvo, "wb") as dst:
                shutil.copyfileobj(src, dst)
            saida.append(alvo)
    if not saida:
        raise ValueError("O .zip não tem nenhum arquivo STEP.")
    return sorted(saida)


def nomes_das_pecas(arquivos: list[str]) -> list[str]:
    """Nome de cada peça a partir do arquivo, sem o que é comum a todos (código do produto, revisão)."""
    tokens = [re.split(r"[_\s]+", os.path.splitext(os.path.basename(a))[0]) for a in arquivos]
    contagem: dict[str, int] = {}
    for ts in tokens:
        for t in set(ts):
            contagem[t.lower()] = contagem.get(t.lower(), 0) + 1
    comuns = {t for t, n in contagem.items() if len(arquivos) > 1 and n > len(arquivos) / 2}
    nomes = []
    for ts in tokens:
        uteis = [t for t in ts if t.lower() not in comuns and not re.fullmatch(r"rev\d*|cad|step|stp", t, re.I)]
        nome = " ".join(uteis) or " ".join(ts)
        while nome in nomes:
            nome += "+"
        nomes.append(nome)
    return nomes


# ── Leitura do GLB (só o JSON: nomes e caixas das peças) ─────────────────────
def _json_glb(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        f.read(12)
        tam, _ = struct.unpack("<II", f.read(8))
        return json.loads(f.read(tam))


def _nome_base(nome: str) -> str:
    """'Head Stock Casting (13)_Dfaut' → 'Head Stock Casting'; 'Screw M4 x 10 (141)_91290A144' → 'Screw M4 x 10'."""
    base = re.sub(r"_(D.?faut|Default|Compressed)$", "", nome, flags=re.I)
    base = re.sub(r"_\d+[A-Z]\d+$", "", base)           # código de catálogo (ex.: McMaster)
    base = base.replace("_", " ")
    base = re.sub(r"\((?:\d+|x+)\)", " ", base, flags=re.I)
    base = re.sub(r"\s+\d+$", "", base.strip())
    return re.sub(r"\s+", " ", base).strip() or nome


def sugerir_componentes(glb: str, pre_selecionados: int = 20) -> list[dict]:
    g = _json_glb(glb)
    acessores = g.get("accessors", [])
    malhas = g.get("meshes", [])

    def tamanho(no: dict) -> float:
        m = malhas[no["mesh"]] if "mesh" in no else None
        maior = 0.0
        for prim in (m or {}).get("primitives", []):
            a = acessores[prim["attributes"]["POSITION"]] if "POSITION" in prim.get("attributes", {}) else None
            if a and a.get("min") and a.get("max"):
                d = sum((a["max"][i] - a["min"][i]) ** 2 for i in range(3)) ** 0.5
                escala = max(abs(v) for v in no.get("scale", [1, 1, 1]))
                maior = max(maior, d * escala)
        return maior

    grupos: dict[str, dict] = {}
    for no in g.get("nodes", []):
        if "mesh" not in no or not no.get("name"):
            continue
        base = _nome_base(no["name"])
        if FIXADORES.search(base):
            continue
        chave = base.lower()
        grupo = grupos.setdefault(chave, {"nome": base, "nos": [], "tamanho": 0.0})
        if no["name"] not in grupo["nos"]:
            grupo["nos"].append(no["name"])
        grupo["tamanho"] = max(grupo["tamanho"], tamanho(no))

    lista = sorted(grupos.values(), key=lambda x: -x["tamanho"])
    usados = set()
    saida = []
    for i, gr in enumerate(lista):
        cid = slug(gr["nome"]).replace("-", "_")[:40] or f"peca_{i}"
        while cid in usados:
            cid += "_"
        usados.add(cid)
        saida.append({"id": cid, "nome": gr["nome"], "nos": [n + "*" for n in gr["nos"]],
                      "tamanho": round(gr["tamanho"], 4), "incluir": i < pre_selecionados, "tipo": "mecânico"})
    return saida


# ── Conversão em segundo plano ───────────────────────────────────────────────
def converter_em_segundo_plano(job_id: int, steps: list[str], destino_glb: str, atualizar) -> None:
    """atualizar(job_id, status, mensagem, sugestoes=None) grava o andamento no banco."""
    def rodar():
        bruto = destino_glb + ".bruto.glb"
        try:
            atualizar(job_id, "convertendo", "Lendo o STEP e gerando a malha 3D…")
            script = os.path.join(RAIZ, "scripts", "cad_para_glb.py")
            if len(steps) == 1:
                cmd = [sys.executable, script, "montagem", steps[0], bruto]
            else:
                cmd = [sys.executable, script, "pecas", bruto] + [f"{n}={a}" for n, a in zip(nomes_das_pecas(steps), steps)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if r.returncode != 0 or not os.path.exists(bruto):
                erro = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["erro desconhecido"]
                if "No module named 'OCP'" in (r.stderr or ""):
                    erro = ["O conversor de CAD não está instalado no servidor (pip install cadquery-ocp)."]
                raise RuntimeError(erro[0][:300])
            npx = shutil.which("npx") or shutil.which("npx.cmd")
            if npx:
                atualizar(job_id, "otimizando", "Reduzindo e comprimindo o modelo para abrir rápido no celular…")
                r = subprocess.run([npx, "-y", "@gltf-transform/cli@4", "optimize", bruto, destino_glb,
                                    "--compress", "meshopt", "--join", "true", "--join-named", "false",
                                    "--flatten", "false", "--simplify-ratio", "0.15", "--texture-compress", "false"],
                                   capture_output=True, text=True, timeout=3600)
            if not npx or r.returncode != 0 or not os.path.exists(destino_glb):
                shutil.copyfile(bruto, destino_glb)   # sem otimização: funciona, só fica maior
            tam_mb = os.path.getsize(destino_glb) / 1e6
            sug = sugerir_componentes(destino_glb)
            atualizar(job_id, "mapear", f"Modelo convertido ({tam_mb:.1f} MB). Confira os componentes sugeridos.", sug)
        except subprocess.TimeoutExpired:
            atualizar(job_id, "erro", "A conversão passou de 1 hora e foi interrompida.")
        except Exception as e:
            atualizar(job_id, "erro", f"Não foi possível converter: {e}")
        finally:
            if os.path.exists(bruto):
                os.remove(bruto)

    threading.Thread(target=rodar, daemon=True, name=f"cad-{job_id}").start()


def salvar_modelo(slug_modelo: str, nome: str, fonte: str, componentes: list[dict], rotacao) -> str:
    """Grava static/models3d/<slug>/modelo.json (o GLB já está na pasta)."""
    comps = []
    for c in componentes:
        palavras = sorted({p for p in re.split(r"[\s/—-]+", unicodedata.normalize("NFKD", c["nome"]).encode("ascii", "ignore").decode().lower()) if len(p) > 3})
        cor = c.get("cor") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(c.get("cor") or "")) else None
        comps.append({"id": c["id"], "nome": c["nome"][:80], "tipo": c.get("tipo") or "mecânico", "cor": cor,
                      "descricao": (c.get("descricao") or "")[:200], "nos": c["nos"],
                      "explode": [round(float(v), 2) for v in (c.get("explode") or [0, 0, 0])][:3],
                      "palavras": [c["nome"].lower()] + palavras})
    dados = {"nome": nome[:80], "fonte": fonte[:160], "arquivo": "modelo.glb", "agrupar_soltas": True,
             "componentes": comps}
    if rotacao and any(rotacao):
        dados["rotacao"] = rotacao
    caminho = os.path.join(PASTA_MODELOS, slug_modelo, "modelo.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return caminho
