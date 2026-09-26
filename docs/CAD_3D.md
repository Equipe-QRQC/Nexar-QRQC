# Modelos 3D a partir do CAD do fabricante

O visualizador 3D aceita dois tipos de modelo por máquina:

| Fonte | Onde fica | Quando usar |
|---|---|---|
| **Família** (código) | `static/js/viewer3d/familias/<familia>.js` + catálogo em `modelos_3d.py` | Máquina sem CAD: modelo genérico da família (ex.: prensa hidráulica). |
| **CAD do fabricante** | `static/models3d/<slug>/modelo.glb` + `modelo.json` | Quando existe o STEP do fabricante ou da comunidade. |

No cadastro da máquina, o campo **Modelo 3D** lista os dois grupos. A máquina grava só a
referência (`{"fonte":"cad","modelo":"<slug>"}`); o catálogo de componentes é copiado para
`machine_components`, e a Nexar IA passa a apontar só componentes que existem no modelo.

Modelos incluídos:

| Slug | Máquina | Origem |
|---|---|---|
| `robo-abb-irb6700` | Robô industrial ABB IRB 6700 | ABB Library (STEP público) |
| `torno-cx704` | Torno mecânico de bancada Craftex CX704 | GrabCAD (modelo da comunidade) |

Os arquivos originais ficam em `cad_origem/`.

## Passo a passo para um novo CAD

### 1. Converter STEP → GLB

```bash
pip install cadquery-ocp
python scripts/cad_para_glb.py montagem "Maquina.step" /tmp/maquina.glb
```

- Nomes e cores das peças do STEP são preservados; cada nó do GLB recebe o nome da peça.
- Se o fabricante entrega uma peça por arquivo, use o modo `pecas`:
  `python scripts/cad_para_glb.py pecas /tmp/maquina.glb base=base.step:#E8731A braco=braco.step`
- Montagens grandes (o torno tem 280 MB de STEP) levam alguns minutos e alguns GB de RAM.

### 2. Reduzir e comprimir

```bash
npx @gltf-transform/cli@4 optimize /tmp/maquina.glb static/models3d/<slug>/modelo.glb \
    --compress meshopt --join true --join-named false --flatten false \
    --simplify-ratio 0.15 --texture-compress false
```

`--join-named false` e `--flatten false` mantêm um nó por peça (é por eles que o
`modelo.json` identifica os componentes). Meta: até ~5 MB para abrir bem no celular.

### 3. Escrever o `modelo.json`

```json
{
  "nome": "Nome exibido no cadastro",
  "fonte": "De onde veio o CAD",
  "arquivo": "modelo.glb",
  "rotacao": [90, 0, 0],
  "agrupar_soltas": true,
  "componentes": [
    {"id": "cabecote", "nome": "Cabeçote fixo e árvore", "tipo": "mecânico",
     "descricao": "Texto curto mostrado no painel da peça.",
     "nos": ["Head Stock Casting*", "Spindle*"],
     "explode": [0, 0.9, -0.4],
     "palavras": ["cabecote", "arvore", "spindle", "rolamento"]}
  ]
}
```

| Campo | Para quê |
|---|---|
| `nos` | Nós do GLB que formam o componente. Terminado em `*` casa por prefixo (o CAD repete o nome em várias instâncias). |
| `explode` | Deslocamento na vista explodida, em unidades do visualizador (a máquina é normalizada para 5 de maior dimensão; Y para cima, Z para a frente). |
| `palavras` | Termos (sem acento, minúsculos) que ligam o texto do diagnóstico e o "componente real" das soluções a este componente. |
| `rotacao` | Graus em X, Y, Z. Use `[90, 0, 0]` quando o CAD foi desenhado com Y para cima e a máquina aparece deitada. |
| `agrupar_soltas` | Parafusos e arruelas não mapeados passam a acompanhar o componente mais próximo na vista explodida. |
| `internos` | (Opcional) módulo em `static/js/viewer3d/internos/` que acrescenta peças internas em código. |

Para descobrir os nomes das peças:

```bash
python - <<'EOF'
import json, struct
f = open("static/models3d/<slug>/modelo.glb", "rb"); f.read(12)
n, _ = struct.unpack("<II", f.read(8)); g = json.loads(f.read(n))
print(sorted({no.get("name", "") for no in g["nodes"]}))
EOF
```

### 4. Conferir

Abra uma ocorrência da máquina em **Visualização 3D**: o console do navegador avisa
(`[3D] nó "..." não encontrado`) quando um nome do `modelo.json` não existe no GLB. Confira a
vista explodida e se o toque em cada região seleciona o componente certo.

O `modelo.json` é lido uma vez por processo: reinicie o servidor depois de editá-lo.
