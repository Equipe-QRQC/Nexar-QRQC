"""
A bomba KSB veio do STEP como um sólido único. Este script divide a malha em regiões
(base, motor, caixa de ligação, ventilação, acoplamento, mancal, selo, voluta) pela posição
de cada triângulo, e endireita a bomba (o CAD está de cabeça para baixo).

    pip install trimesh numpy
    python scripts/cad_para_glb.py montagem "Pump - KSB Etanorm 65-40-250 - emotor 180M.stp" /tmp/bomba_raw.glb
    python cad_origem/bomba-ksb-etanorm/dividir_regioes.py /tmp/bomba_raw.glb /tmp/bomba_split.glb
    npx @gltf-transform/cli@4 optimize /tmp/bomba_split.glb static/models3d/bomba-ksb-etanorm/modelo.glb \
        --compress meshopt --join true --join-named false --flatten false --simplify-ratio 0.7 --palette false
"""
import sys
import trimesh, numpy as np
from collections import defaultdict
ENTRADA, SAIDA = sys.argv[1], sys.argv[2]
sc=trimesh.load(ENTRADA, force="scene")
def regiao(c):
    x,y,z=c
    if z>-0.115: return "Base"
    if y<-0.5: return "Motor Ventilacao"
    if -0.48<y<-0.32 and z<-0.44: return "Caixa Ligacao"
    if y<-0.12: return "Motor Carcaca"
    if y<0.21: return "Acoplamento"
    if y<0.435: return "Mancal"
    if y<0.48 and abs(x)<0.1 and -0.4<z<-0.15: return "Selo Mecanico"
    return "Voluta"
# baked rotation: new X = y, new Y = -z, new Z = -x
R=np.array([[0,1,0,0],[0,0,-1,0],[-1,0,0,0],[0,0,0,1]],float)
grupos=defaultdict(lambda: defaultdict(list))
mats={}
for node in sc.graph.nodes_geometry:
    M,gn=sc.graph[node]; g=sc.geometry[gn]
    v=trimesh.transform_points(g.vertices,M); f=g.faces
    cor=tuple(int(c) for c in g.visual.material.baseColorFactor)
    if cor[:3]==(41,90,248): cor=(4,22,92,255)  # azul KSB (o STEP traz um azul claro)
    cen=v[f].mean(1)
    regs=np.array([regiao(c) for c in cen])
    for r in set(regs):
        k=regs==r
        grupos[r][cor].append(trimesh.Trimesh(v, f[k], process=False))
out=trimesh.Scene()
for r,porcor in grupos.items():
    for cor,ms in porcor.items():
        m=trimesh.util.concatenate(ms); m.remove_unreferenced_vertices(); m.merge_vertices()
        m.apply_transform(R)
        m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=cor, metallicFactor=0.2, roughnessFactor=0.6))
        nome=f"{r} {'%02x%02x%02x'%cor[:3]}"
        out.add_geometry(m, node_name=nome, geom_name=nome)
    print(r, sum(len(x.faces) for ms in porcor.values() for x in ms))
out.export(SAIDA)
