"""
Converte CAD (STEP) em GLB para o visualizador 3D.

Dois modos:

  Montagem única (um STEP com várias peças, nomes e cores preservados):
      python scripts/cad_para_glb.py montagem entrada.step saida.glb

  Várias peças (um STEP por componente; o nome do componente vem do arquivo):
      python scripts/cad_para_glb.py pecas saida.glb NOME=arquivo.step[:#rrggbb] ...

Depois, reduza e comprima com o glTF-Transform (ver docs/CAD_3D.md):
      npx @gltf-transform/cli@4 optimize saida.glb final.glb --compress meshopt \
          --join true --join-named false --flatten false --simplify-ratio 0.15

Requer: pip install cadquery-ocp
"""
from __future__ import annotations

import json
import struct
import sys
import time

from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.Bnd import Bnd_Box
from OCP.IFSelect import IFSelect_RetDone
from OCP.Message import Message_ProgressRange
from OCP.Quantity import Quantity_Color, Quantity_TOC_sRGB
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.STEPControl import STEPControl_Reader
from OCP.TCollection import TCollection_AsciiString, TCollection_ExtendedString
from OCP.OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString as MapaInfo
from OCP.TDataStd import TDataStd_Name
from OCP.OCP.collections import Sequence_TDF_Label as TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopoDS import TopoDS_Shape
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool


def _novo_documento() -> TDocStd_Document:
    return TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))


def _tamanho(shape: TopoDS_Shape) -> float:
    caixa = Bnd_Box()
    BRepBndLib.Add_s(shape, caixa)
    mn, mx = caixa.CornerMin(), caixa.CornerMax()
    return max(mx.X() - mn.X(), mx.Y() - mn.Y(), mx.Z() - mn.Z())


def _malhar(shapes: list[TopoDS_Shape], tamanho_total: float) -> None:
    # Deflexão proporcional ao tamanho da máquina: detalhe suficiente sem explodir o arquivo
    deflexao = max(tamanho_total / 1500.0, 0.05)
    for s in shapes:
        BRepMesh_IncrementalMesh(s, deflexao, False, 0.35, True)


def _escrever_glb(doc: TDocStd_Document, saida: str) -> None:
    writer = RWGltf_CafWriter(TCollection_AsciiString(saida), True)  # True = binário (GLB)
    conv = writer.ChangeCoordinateSystemConverter()
    conv.SetInputLengthUnit(0.001)                       # STEP em mm
    conv.SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
    conv.SetOutputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_glTF)
    ok = writer.Perform(doc, MapaInfo(), Message_ProgressRange())
    if not ok:
        raise RuntimeError("Falha ao escrever o GLB")


def _nomear_nos_pelas_pecas(saida: str) -> None:
    """
    O OCCT nomeia cada nó pela instância do STEP (NAUO1, NAUO2...) e a peça fica no
    nome da malha. Copia o nome da peça para o nó, que é o que o modelo.json referencia.
    """
    with open(saida, "rb") as f:
        dados = f.read()
    tam_json = struct.unpack("<I", dados[12:16])[0]
    gltf = json.loads(dados[20:20 + tam_json])
    resto = dados[20 + tam_json:]
    for no in gltf.get("nodes", []):
        if "mesh" in no:
            nome = gltf["meshes"][no["mesh"]].get("name")
            if nome:
                no["name"] = nome
    novo = json.dumps(gltf, separators=(",", ":")).encode()
    novo += b" " * ((4 - len(novo) % 4) % 4)
    with open(saida, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 20 + len(novo) + len(resto)))
        f.write(struct.pack("<II", len(novo), 0x4E4F534A))
        f.write(novo)
        f.write(resto)


def montagem(entrada: str, saida: str) -> None:
    t0 = time.time()
    doc = _novo_documento()
    leitor = STEPCAFControl_Reader()
    leitor.SetNameMode(True)
    leitor.SetColorMode(True)
    leitor.SetLayerMode(False)
    if leitor.ReadFile(entrada) != IFSelect_RetDone:
        raise RuntimeError(f"Não foi possível ler {entrada}")
    leitor.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    livres = TDF_LabelSequence()
    st.GetFreeShapes(livres)
    shapes = [st.GetShape_s(livres.Value(i)) for i in range(1, livres.Length() + 1)]
    tam = max(_tamanho(s) for s in shapes)
    print(f"lido em {time.time() - t0:.0f}s — {len(shapes)} raiz(es), tamanho {tam:.0f} mm")
    _malhar(shapes, tam)
    print(f"malha em {time.time() - t0:.0f}s")
    _escrever_glb(doc, saida)
    _nomear_nos_pelas_pecas(saida)
    print(f"GLB escrito em {time.time() - t0:.0f}s → {saida}")


def pecas(saida: str, itens: list[str]) -> None:
    t0 = time.time()
    doc = _novo_documento()
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    shapes = []
    for item in itens:
        nome, resto = item.split("=", 1)
        arquivo, _, cor = resto.partition(":")
        leitor = STEPControl_Reader()
        if leitor.ReadFile(arquivo) != IFSelect_RetDone:
            raise RuntimeError(f"Não foi possível ler {arquivo}")
        leitor.TransferRoots(Message_ProgressRange())
        shape = leitor.OneShape()
        label = st.AddShape(shape, False)
        TDataStd_Name.Set_s(label, TCollection_ExtendedString(nome))
        if cor:
            r, g, b = (int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
            ct.SetColor(label, Quantity_Color(r, g, b, Quantity_TOC_sRGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
        shapes.append(shape)
        print(f"  {nome}: {arquivo.rsplit('/', 1)[-1]}")
    tam = max(_tamanho(s) for s in shapes)
    _malhar(shapes, tam)
    _escrever_glb(doc, saida)
    print(f"{len(shapes)} peças → {saida} em {time.time() - t0:.0f}s (tamanho {tam:.0f} mm)")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "montagem":
        montagem(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "pecas":
        pecas(sys.argv[2], sys.argv[3:])
    else:
        print(__doc__)
        sys.exit(1)
