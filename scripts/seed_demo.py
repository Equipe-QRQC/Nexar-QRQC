"""
Popula o banco com uma base de demonstração realista para apresentações.

Cria 6 máquinas (com diagramas de test_diagrams/), cerca de 30 ocorrências
distribuídas nos últimos 60 dias — abertas, em andamento e resolvidas com a
solução aplicada registrada, incluindo casos recorrentes — e os componentes
da Visualização 3D para o motor do transportador.

Os diagnósticos são gerados pela IA de verdade (Gemini) quando GEMINI_API_KEY
está configurada; sem chave, fica o roteiro padrão de inspeção. Nenhum texto
é apresentado como gerado por IA sem ter sido.

Uso (na raiz do projeto, com o .env configurado):
    python scripts/seed_demo.py            # recusa se já houver ocorrências
    python scripts/seed_demo.py --forcar   # apaga ocorrências/máquinas e recria
    python scripts/seed_demo.py --sem-ia   # não chama a IA (mais rápido)

Para não tocar no banco principal, aponte outro arquivo:
    DATABASE_PATH=demo.db python scripts/seed_demo.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import app as nexar  # noqa: E402  (inicializa o banco e a IA)

MAQUINAS = [
    {"nome": "Prensa Hidráulica PH-200", "modelo": "PH-200/40T", "fabricante": "Schuler",
     "ano": "2019", "setor": "Estamparia",
     "descricao": "Prensa hidráulica de 40 t para estampagem de chapas. Pressão nominal 180 bar.",
     "diagrama": "diagrama_prensa_hidraulica.png"},
    {"nome": "Motor do Transportador MT-75", "modelo": "W22 75 cv", "fabricante": "WEG",
     "ano": "2020", "setor": "Montagem",
     "descricao": "Motor de indução trifásico que aciona a esteira principal da linha de montagem.",
     "diagrama": "diagrama_motor_eletrico.png"},
    {"nome": "Manifold Pneumático MP-12", "modelo": "VTUG-12", "fabricante": "Festo",
     "ano": "2018", "setor": "Pintura",
     "descricao": "Bloco de 12 válvulas solenoides que comanda os atuadores da cabine de pintura.",
     "diagrama": "arranjo_pneumatico_manifold.jpg"},
    {"nome": "Válvula de Controle VP-03", "modelo": "Série 8", "fabricante": "Morin",
     "ano": "2017", "setor": "Utilidades",
     "descricao": "Válvula esfera com atuador pneumático na linha de distribuição de água gelada.",
     "diagrama": "sistema_pneumatico_completo.jpg"},
    {"nome": "Torno CNC GL-240M", "modelo": "GL-240M", "fabricante": "Romi",
     "ano": "2021", "setor": "Usinagem",
     "descricao": "Torno CNC com magazine de 12 ferramentas para usinagem de eixos.",
     "diagrama_static": "static/Ficha_Tecnica_Torno_CNC_GL240M.pdf"},
    {"nome": "Compressor de Ar CA-50", "modelo": "GA 37", "fabricante": "Atlas Copco",
     "ano": "2016", "setor": "Utilidades",
     "descricao": "Compressor parafuso de 50 hp que abastece a rede de ar comprimido da planta.",
     "diagrama": None},
]

# (máquina, dias atrás, hora, operador, tipo, impacto, recorrente, descrição, detalhe,
#  status, solução aplicada, componente real, horas até resolver)
OCORRENCIAS = [
    (0, 58, "07:40", "Carlos Souza", "Manutenção", "Alto", "Não",
     "Vazamento de óleo no cilindro principal e queda de pressão",
     "Pressão caiu de 180 para 130 bar durante o ciclo. Óleo acumulado na base do cilindro.",
     "Resolvida", "Substituído o kit de vedação do cilindro principal e completado o nível de óleo.",
     "Vedação do cilindro principal", 6),
    (1, 55, "14:10", "Ana Lima", "Manutenção", "Médio", "Não",
     "Motor da esteira aquecendo acima do normal",
     "Temperatura da carcaça em 92 °C (normal até 75 °C). Ruído leve no lado acoplado.",
     "Resolvida", "Relubrificado o rolamento do lado acoplado e limpas as aletas de refrigeração.",
     "Rolamento lado acoplado", 4),
    (2, 52, "09:05", "Juliana Rocha", "Produção", "Médio", "Não",
     "Atuador da cabine de pintura não recua",
     "Válvula 7 do manifold não comuta. Bobina com tensão presente.",
     "Resolvida", "Trocada a válvula solenoide 7 do manifold; carretel estava travado por sujeira.",
     "Válvula solenoide 7", 3),
    (4, 50, "10:30", "Marcos Pereira", "Qualidade", "Médio", "Não",
     "Peças com diâmetro fora da tolerância no torno",
     "Eixos com +0,04 mm no diâmetro de 40 mm. Desvio aumenta ao longo do turno.",
     "Resolvida", "Compensado o desgaste da ferramenta e substituído o inserto T3.",
     "Inserto da ferramenta T3", 2),
    (5, 47, "06:55", "Carlos Souza", "Produção", "Alto", "Não",
     "Compressor desarmando por alta temperatura",
     "Alarme de temperatura do elemento compressor a 110 °C. Rede de ar caiu para 5 bar.",
     "Resolvida", "Limpo o radiador de óleo obstruído e substituído o filtro de ar de admissão.",
     "Radiador de óleo", 5),
    (0, 44, "15:20", "Ana Lima", "Segurança", "Alto", "Não",
     "Cortina de luz da prensa não interrompe o ciclo",
     "Teste diário: ao cruzar a cortina de luz a prensa completou o ciclo.",
     "Resolvida", "Realinhados emissor e receptor da cortina de luz e testado o relé de segurança.",
     "Cortina de luz", 2),
    (3, 41, "11:45", "Marcos Pereira", "Manutenção", "Baixo", "Não",
     "Válvula de controle com resposta lenta",
     "Tempo de abertura de 9 s (especificado 3 s). Pressão de pilotagem normal.",
     "Resolvida", "Lubrificada a haste e substituído o filtro regulador do ar de pilotagem.",
     "Filtro regulador de pilotagem", 8),
    (1, 38, "08:15", "Juliana Rocha", "Manutenção", "Alto", "Sim",
     "Motor da esteira aquecendo novamente e com vibração",
     "Temperatura 95 °C e vibração de 7 mm/s no mancal dianteiro. Segunda ocorrência no mês.",
     "Resolvida", "Substituído o rolamento 6316 do lado acoplado e corrigido o alinhamento do acoplamento.",
     "Rolamento lado acoplado", 10),
    (0, 35, "13:00", "Carlos Souza", "Manutenção", "Alto", "Sim",
     "Novo vazamento de óleo no cilindro da prensa",
     "Gotejamento na haste do cilindro. Vedação trocada há 3 semanas.",
     "Resolvida", "Haste do cilindro com riscos: haste retificada e vedação trocada; filtro de óleo substituído.",
     "Haste do cilindro principal", 12),
    (4, 33, "16:40", "Marcos Pereira", "Produção", "Médio", "Não",
     "Torno parando com alarme de lubrificação",
     "Alarme 2011 (baixa pressão de lubrificação) a cada 2 horas.",
     "Resolvida", "Completado o reservatório de lubrificação central e desobstruído o distribuidor.",
     "Distribuidor de lubrificação", 3),
    (2, 30, "07:20", "Ana Lima", "Qualidade", "Médio", "Não",
     "Falhas de pintura por pressão de ar instável",
     "Pressão na pistola oscilando entre 3 e 5 bar. Peças com escorrimento.",
     "Resolvida", "Substituído o regulador de pressão da entrada do manifold.",
     "Regulador de pressão", 4),
    (5, 27, "09:50", "Juliana Rocha", "Manutenção", "Médio", "Não",
     "Compressor com consumo de óleo elevado",
     "Reposição de 1 L de óleo por semana e óleo na rede de ar.",
     "Resolvida", "Trocado o elemento separador de óleo.",
     "Elemento separador de óleo", 6),
    (1, 24, "10:05", "Carlos Souza", "Produção", "Baixo", "Não",
     "Esteira com velocidade oscilando",
     "Velocidade variando ±8% no inversor. Sem alarmes.",
     "Resolvida", "Reajustados os parâmetros de rampa do inversor e reapertados os bornes do encoder.",
     "Encoder do motor", 2),
    (0, 21, "14:30", "Marcos Pereira", "Qualidade", "Médio", "Não",
     "Peças estampadas com rebarba",
     "Rebarba de 0,3 mm na borda das peças do lote 2231.",
     "Resolvida", "Afiada a matriz de corte e ajustada a folga punção-matriz.",
     "Matriz de corte", 5),
    (3, 18, "08:35", "Ana Lima", "Segurança", "Alto", "Não",
     "Vazamento de ar no atuador da válvula de água gelada",
     "Chiado audível próximo ao atuador; consumo de ar da rede aumentou.",
     "Resolvida", "Substituídas as vedações do atuador pneumático.",
     "Vedação do atuador", 4),
    (4, 15, "11:10", "Juliana Rocha", "Manutenção", "Alto", "Não",
     "Ruído anormal no cabeçote do torno",
     "Ruído metálico acima de 2.500 rpm. Temperatura do cabeçote normal.",
     "Resolvida", "Substituída a correia do cabeçote e ajustada a tensão.",
     "Correia do cabeçote", 7),
    (2, 13, "15:55", "Carlos Souza", "Produção", "Baixo", "Não",
     "Atuador da cabine lento no avanço",
     "Tempo de avanço de 2,5 s (normal 1,2 s).",
     "Resolvida", "Regulada a válvula reguladora de fluxo do atuador.",
     "Reguladora de fluxo", 1),
    (1, 11, "07:15", "Marcos Pereira", "Manutenção", "Médio", "Sim",
     "Vibração no motor da esteira após troca de rolamento",
     "Vibração de 5 mm/s no lado acoplado. Rolamento trocado há 27 dias.",
     "Resolvida", "Acoplamento com elemento elástico desgastado: trocado e realinhado a laser.",
     "Acoplamento", 6),
    # Em andamento
    (0, 8, "10:20", "Ana Lima", "Manutenção", "Alto", "Sim",
     "Terceiro vazamento no cilindro da prensa em 60 dias",
     "Óleo na base do cilindro e pressão caindo para 150 bar ao fim do turno.",
     "Em andamento", None, None, None),
    (5, 6, "13:40", "Juliana Rocha", "Produção", "Médio", "Não",
     "Compressor não atinge a pressão de trabalho",
     "Pressão máxima de 6,2 bar (set point 7,5 bar). Tempo em carga contínuo.",
     "Em andamento", None, None, None),
    (4, 5, "09:00", "Carlos Souza", "Qualidade", "Médio", "Não",
     "Acabamento superficial ruim nos eixos",
     "Rugosidade Ra 3,2 µm (especificado Ra 1,6 µm) nas peças do turno da noite.",
     "Em andamento", None, None, None),
    # Abertas
    (1, 3, "06:50", "Marcos Pereira", "Manutenção", "Alto", "Sim",
     "Motor da esteira desarmando por sobrecarga",
     "Relé térmico atuando com corrente de 118 A (nominal 98 A). Carga da esteira normal.",
     "Aberta", None, None, None),
    (2, 2, "11:25", "Ana Lima", "Produção", "Médio", "Não",
     "Duas válvulas do manifold sem acionamento",
     "Válvulas 3 e 4 não comutam. LED do módulo de comunicação piscando em vermelho.",
     "Aberta", None, None, None),
    (3, 2, "16:05", "Juliana Rocha", "Manutenção", "Baixo", "Não",
     "Indicador de posição da válvula VP-03 inconsistente",
     "Sinal de fim de curso indica 'fechada' com a válvula parcialmente aberta.",
     "Aberta", None, None, None),
    (0, 1, "08:10", "Carlos Souza", "Segurança", "Alto", "Não",
     "Botão de emergência da prensa com acionamento intermitente",
     "Em 2 de 5 testes o botão não interrompeu o ciclo.",
     "Aberta", None, None, None),
    (5, 1, "14:20", "Marcos Pereira", "Manutenção", "Médio", "Não",
     "Dreno automático do compressor não descarrega",
     "Água acumulada no reservatório. Dreno eletrônico sem atuar.",
     "Aberta", None, None, None),
    (4, 0, "07:30", "Ana Lima", "Produção", "Alto", "Não",
     "Torno CNC com erro de referência no eixo X",
     "Alarme 1520 ao referenciar o eixo X. Máquina parada.",
     "Aberta", None, None, None),
]

# Componentes da Visualização 3D (modelo ilustrativo) para o motor do transportador
COMPONENTES_3D = [
    ("base", "Base de fixação", "estrutura"),
    ("carcaca", "Carcaça do motor", "estrutura"),
    ("tampa_traseira", "Tampa traseira", "estrutura"),
    ("estator", "Estator / bobinado", "elétrico"),
    ("rolamento_la", "Rolamento lado acoplado (6316)", "mecânico"),
    ("eixo", "Eixo do rotor", "mecânico"),
    ("acoplamento", "Acoplamento elástico", "mecânico"),
    ("ventilador", "Ventilador de refrigeração", "mecânico"),
    ("caixa_ligacao", "Caixa de ligação", "elétrico"),
    ("redutor", "Redutor da esteira", "mecânico"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--forcar", action="store_true", help="apaga ocorrências e máquinas existentes")
    ap.add_argument("--sem-ia", action="store_true", help="não chama a IA (usa o roteiro padrão)")
    args = ap.parse_args()

    conn = nexar.get_db()
    existentes = conn.execute("SELECT COUNT(*) AS n FROM ocorrencias").fetchone()["n"]
    if existentes and not args.forcar:
        print(f"O banco {nexar.DB_PATH} já tem {existentes} ocorrência(s). "
              "Use --forcar para apagar e recriar a base de demonstração.")
        sys.exit(1)

    if args.forcar:
        for tabela in ("ai_diagnosis_components", "ai_diagnoses", "machine_components",
                       "ocorrencias", "diagramas", "percepcoes", "maquinas"):
            conn.execute(f"DELETE FROM {tabela}")
        conn.commit()

    admin = conn.execute("SELECT id FROM usuarios WHERE perfil = 'admin' ORDER BY id LIMIT 1").fetchone()
    admin_id = admin["id"] if admin else None

    # ── Máquinas e diagramas ───────────────────────────────────────────────
    ids: list[int] = []
    for m in MAQUINAS:
        cur = conn.execute(
            "INSERT INTO maquinas (nome, modelo, fabricante, ano, setor, descricao) VALUES (?,?,?,?,?,?)",
            (m["nome"], m["modelo"], m["fabricante"], m["ano"], m["setor"], m["descricao"]),
        )
        mid = cur.lastrowid
        ids.append(mid)
        origem = None
        if m.get("diagrama"):
            origem = os.path.join("test_diagrams", m["diagrama"])
        elif m.get("diagrama_static"):
            origem = m["diagrama_static"]
        if origem and os.path.exists(origem):
            pasta = os.path.join(nexar.UPLOAD_FOLDER, str(mid))
            os.makedirs(pasta, exist_ok=True)
            destino = os.path.join(pasta, os.path.basename(origem))
            shutil.copyfile(origem, destino)
            conn.execute(
                "INSERT INTO diagramas (maquina_id, nome, caminho, tipo) VALUES (?,?,?,?)",
                (mid, os.path.basename(origem), destino, origem.rsplit(".", 1)[-1].upper()),
            )
    conn.commit()
    print(f"✓ {len(ids)} máquinas cadastradas")

    motor_id = ids[1]
    for cid, nome, tipo in COMPONENTES_3D:
        conn.execute(
            "INSERT INTO machine_components (maquina_id, component_id, name, type, description) VALUES (?,?,?,?,?)",
            (motor_id, cid, nome, tipo, ""),
        )
    conn.commit()
    conn.close()
    print(f"✓ {len(COMPONENTES_3D)} componentes 3D para '{MAQUINAS[1]['nome']}'")

    # ── Ocorrências (em ordem cronológica, para o histórico alimentar a IA) ─
    if args.sem_ia:
        nexar.gemini_client = None  # get_ai_response cai no roteiro padrão
    usar_ia = nexar.gemini_client is not None
    if not usar_ia:
        print("! IA desligada ou GEMINI_API_KEY ausente — diagnósticos ficarão com o roteiro padrão.")
    agora = datetime.now()
    ordenadas = sorted(OCORRENCIAS, key=lambda o: -o[1])
    for n, (mi, dias, hora, operador, tipo, impacto, recorrente, desc, det,
            status, solucao, componente, horas) in enumerate(ordenadas, 1):
        h, mnt = map(int, hora.split(":"))
        quando = (agora - timedelta(days=dias)).replace(hour=h, minute=mnt, second=0, microsecond=0)
        campos = {
            "maquina_id": ids[mi], "data_ocorrencia": quando.strftime("%Y-%m-%d %H:%M"),
            "setor_area": MAQUINAS[mi]["setor"], "descricao": desc, "tipo_ocorrencia": tipo,
            "nivel_impacto": impacto, "problema_recorrente": recorrente, "detalhamento_tecnico": det,
        }
        diag = nexar.diagnosticar_ocorrencia(campos)
        if usar_ia:
            time.sleep(4)  # respeita o limite do plano gratuito (15 req/min)
        resolvida = status == "Resolvida"
        data_res = (quando + timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S") if resolvida else None
        conn = nexar.get_db()
        conn.execute(
            """INSERT INTO ocorrencias (
                maquina_id, data_ocorrencia, nome_operador, setor_area, descricao,
                tipo_ocorrencia, nivel_impacto, problema_recorrente, detalhamento_tecnico,
                resposta_ia, ia_status, anotacoes_ia, diagrama_url, status, data_registro,
                solucao_aplicada, componente_real, data_resolucao, resolvido_por_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ids[mi], campos["data_ocorrencia"], operador, campos["setor_area"], desc,
             tipo, impacto, recorrente, det,
             diag["resposta_ia"], diag["ia_status"],
             json.dumps(diag["anotacoes"], ensure_ascii=False) if diag["anotacoes"] else None,
             diag["diagrama_url"], status, quando.strftime("%Y-%m-%d %H:%M:%S"),
             solucao, componente, data_res, admin_id if resolvida else None),
        )
        conn.commit()
        conn.close()
        print(f"  [{n:2}/{len(ordenadas)}] {status:<12} {MAQUINAS[mi]['nome']}: {desc[:50]}")

    print(f"✓ {len(ordenadas)} ocorrências criadas em {nexar.DB_PATH}")


if __name__ == "__main__":
    main()
