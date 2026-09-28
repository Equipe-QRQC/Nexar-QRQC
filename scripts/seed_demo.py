"""
Popula o banco com uma base de demonstração realista para apresentações.

Cria 8 máquinas com CAD 3D (robôs ABB IRB 6700, tornos CX704, motor WEG W22,
bomba KSB Etanorm e compressor de parafuso) e cerca de 30 ocorrências distribuídas nos últimos 60 dias — abertas, em
andamento e resolvidas com a solução aplicada —, cada uma com a peça apontada
no 3D e o sintoma, incluindo casos recorrentes.

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
import sys
import time
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import app as nexar  # noqa: E402  (inicializa o banco e a IA)

ROBO = {"fonte": "cad", "modelo": "robo-abb-irb6700"}
TORNO = {"fonte": "cad", "modelo": "torno-cx704"}
MOTOR = {"fonte": "cad", "modelo": "motor-weg-w22"}
BOMBA = {"fonte": "cad", "modelo": "bomba-ksb-etanorm"}
COMPRESSOR = {"fonte": "cad", "modelo": "compressor-parafuso"}

# Só máquinas com CAD 3D: a ocorrência é registrada apontando a peça no modelo.
MAQUINAS = [
    {"nome": "Robô de Solda RS-01", "mapa": (18, 34), "modelo": "IRB 6700-235/2.65", "fabricante": "ABB",
     "ano": "2022", "setor": "Soldagem",
     "descricao": "Robô de 6 eixos da célula 1 de solda a ponto da carroceria. Carga útil 235 kg.",
     "modelo_3d": ROBO},
    {"nome": "Robô de Solda RS-02", "mapa": (38, 34), "modelo": "IRB 6700-200/2.60", "fabricante": "ABB",
     "ano": "2022", "setor": "Soldagem",
     "descricao": "Robô de 6 eixos da célula 2 de solda a ponto. Carga útil 200 kg.",
     "modelo_3d": ROBO},
    {"nome": "Robô de Paletização RP-01", "mapa": (80, 34), "modelo": "IRB 6700-150/3.20", "fabricante": "ABB",
     "ano": "2021", "setor": "Expedição",
     "descricao": "Robô de paletização de caixas no fim da linha. Alcance de 3,2 m.",
     "modelo_3d": ROBO},
    {"nome": "Torno Mecânico TM-04", "mapa": (12, 76), "modelo": "CX704", "fabricante": "Craftex",
     "ano": "2020", "setor": "Ferramentaria",
     "descricao": "Torno de bancada para reparo de peças e usinagem de buchas na ferramentaria.",
     "modelo_3d": TORNO},
    {"nome": "Torno Mecânico TM-05", "mapa": (89, 76), "modelo": "CX704", "fabricante": "Craftex",
     "ano": "2021", "setor": "Manutenção Central",
     "descricao": "Torno de bancada da oficina de manutenção para usinagem de pinos e eixos.",
     "modelo_3d": TORNO},
    {"nome": "Motor Elétrico MT-01", "mapa": (50, 76), "modelo": "W22 IR3 Premium 7,5 cv 4P", "fabricante": "WEG",
     "ano": "2019", "setor": "Utilidades",
     "descricao": "Motor do exaustor da cabine de pintura. Trabalha 24 h em dois turnos e fim de semana.",
     "modelo_3d": MOTOR},
    {"nome": "Bomba Centrífuga BC-01", "mapa": (31, 76), "modelo": "Etanorm 65-40-250", "fabricante": "KSB",
     "ano": "2018", "setor": "Utilidades",
     "descricao": "Bomba de água gelada do circuito de resfriamento das máquinas de solda. Motor carcaça 180M.",
     "modelo_3d": BOMBA},
    {"nome": "Compressor de Ar CA-01", "mapa": (69, 76), "modelo": "Parafuso 30 kW", "fabricante": "—",
     "ano": "2017", "setor": "Utilidades",
     "descricao": "Compressor de parafuso que alimenta a rede de ar comprimido da fábrica (7 bar).",
     "modelo_3d": COMPRESSOR},
]

# (máquina, dias atrás, hora, operador, componente no 3D, sintoma, parou?, risco?,
#  impacto, recorrente, descrição, detalhe, status, solução aplicada, horas até resolver)
OCORRENCIAS = [
    (0, 58, "07:40", "Carlos Souza", "eixo2", "aquecimento", True, False, "Alto", "Não",
     "Motor do eixo 2 aquecendo e robô parando com alarme",
     "Alarme 50296 após 3 horas de ciclo. Carcaça do motor do eixo 2 a 85 °C.",
     "Resolvida", "Limpo o ventilador do motor do eixo 2 e reduzida a aceleração no trecho de retorno.", 4),
    (3, 55, "14:10", "Marcos Pereira", "contraponto", "medida", False, False, "Médio", "Não",
     "Buchas saindo cônicas no torno",
     "Diferença de 0,05 mm entre as pontas em 80 mm de comprimento.",
     "Resolvida", "Realinhado o contraponto e reapertada a fixação no barramento.", 3),
    (1, 52, "09:05", "Juliana Rocha", "chicote", "intermitente", True, False, "Alto", "Não",
     "Perda de sinal do encoder durante a solda",
     "Alarme 38103 intermitente. Cabo do chicote roçando na carcaça do eixo 3.",
     "Resolvida", "Substituído o trecho do chicote de cabos entre os eixos 3 e 4 e refeita a fixação.", 9),
    (2, 50, "10:30", "Ana Lima", "eixo6", "folga", False, False, "Médio", "Não",
     "Garra da paletização com folga no flange",
     "Caixas soltando no ponto de descarga; folga visível entre a garra e o flange.",
     "Resolvida", "Reapertados os parafusos do flange com torque especificado e trocados os pinos-guia.", 2),
    (4, 47, "06:55", "Carlos Souza", "transmissao", "nao_liga", True, False, "Alto", "Não",
     "Torno não liga e fusível queimado",
     "Fusível do painel queimou duas vezes seguidas ao ligar o motor.",
     "Resolvida", "Substituídas as escovas do motor e o fusível; placa de controle testada.", 5),
    (0, 44, "15:20", "Ana Lima", "compensador", "vazamento", False, True, "Alto", "Não",
     "Óleo na haste do compensador de peso",
     "Gotejamento na haste do cilindro compensador; braço desce devagar com os freios soltos.",
     "Resolvida", "Trocado o kit de vedação do cilindro compensador e refeita a pré-carga conforme manual ABB.", 8),
    (3, 41, "11:45", "Marcos Pereira", "carro_transversal", "folga", False, False, "Médio", "Não",
     "Folga no carro transversal",
     "Volante do carro transversal com 0,2 mm de folga; acabamento com vibração.",
     "Resolvida", "Ajustada a régua (gib) do carro transversal e lubrificado o fuso.", 2),
    (1, 38, "08:15", "Juliana Rocha", "chicote", "intermitente", True, False, "Alto", "Sim",
     "Encoder do RS-02 perdendo sinal novamente",
     "Mesmo alarme 38103 da ocorrência anterior, agora no trecho do punho.",
     "Resolvida", "Substituído o chicote de cabos do punho e instalada proteção espiral no eixo 4.", 10),
    (2, 35, "13:00", "Carlos Souza", "base", "vibracao", False, False, "Médio", "Não",
     "Robô de paletização vibrando na base",
     "Vibração perceptível nos movimentos rápidos; chumbadores com sinais de folga.",
     "Resolvida", "Reapertados os chumbadores da base e refeito o graute sob o pedestal.", 12),
    (4, 33, "16:40", "Ana Lima", "placa", "folga", False, True, "Alto", "Não",
     "Castanha da placa com folga",
     "Peça escorregando na placa durante o desbaste.",
     "Resolvida", "Limpa e lubrificada a espiral da placa e substituída a castanha 2 desgastada.", 3),
    (0, 30, "07:20", "Marcos Pereira", "eixo4", "ruido", False, False, "Médio", "Não",
     "Ruído no braço superior do RS-01",
     "Ruído de engrenagem ao girar o eixo 4 em velocidade máxima.",
     "Resolvida", "Completado o óleo do redutor do eixo 4 (nível abaixo do mínimo).", 4),
    (3, 27, "09:50", "Juliana Rocha", "porta_ferramenta", "medida", False, False, "Médio", "Não",
     "Acabamento ruim nas buchas",
     "Rugosidade Ra 3,2 µm (especificado Ra 1,6 µm).",
     "Resolvida", "Substituído o inserto e ajustada a altura do porta-ferramenta ao centro.", 1),
    (1, 24, "10:05", "Carlos Souza", "eixo2", "aquecimento", True, False, "Alto", "Sim",
     "Motor do eixo 2 do RS-02 sobreaquecendo",
     "Alarme 50296 no fim do turno; ventilador do motor com acúmulo de respingos de solda.",
     "Resolvida", "Limpo o ventilador do motor do eixo 2 e instalada proteção contra respingos.", 3),
    (4, 21, "14:30", "Marcos Pereira", "emergencia", "nao_atua", False, True, "Alto", "Não",
     "Botão de emergência do torno sem efeito",
     "Ao pressionar o botão, o motor continuou girando por 2 s.",
     "Resolvida", "Substituído o bloco de contatos do botão de emergência e testado o circuito.", 2),
    (2, 18, "08:35", "Ana Lima", "eixo1", "ruido", False, False, "Baixo", "Não",
     "Estalo no giro do carrossel",
     "Estalo audível ao girar o eixo 1 no sentido anti-horário.",
     "Resolvida", "Relubrificado o rolamento do eixo 1 conforme plano de manutenção ABB.", 4),
    (3, 15, "11:10", "Juliana Rocha", "cabecote", "ruido", False, False, "Médio", "Não",
     "Ruído no cabeçote em alta rotação",
     "Ruído metálico acima de 1.800 rpm.",
     "Resolvida", "Ajustada a pré-carga dos rolamentos da árvore e trocada a graxa.", 6),
    (0, 12, "15:55", "Carlos Souza", "compensador", "vazamento", False, True, "Alto", "Sim",
     "Novo vazamento no compensador do RS-01",
     "Óleo na haste 30 dias após a troca de vedação; haste com riscos.",
     "Resolvida", "Substituída a haste riscada e o kit de vedação do compensador.", 12),
    # Em andamento
    (1, 6, "08:45", "Marcos Pereira", "eixo5", "folga", True, False, "Alto", "Não",
     "Folga no punho do RS-02",
     "Ruído de engrenagem ao girar o eixo 5 e desvio de 1,5 mm no ponto de solda.",
     "Em andamento", None, None),
    (4, 5, "13:40", "Ana Lima", "fuso", "travamento", True, False, "Médio", "Não",
     "Avanço automático travando no torno",
     "O carro para no meio do curso com o avanço engatado.",
     "Em andamento", None, None),
    # Abertas
    (0, 2, "10:05", "Carlos Souza", "compensador", "vazamento", False, True, "Alto", "Sim",
     "Vazamento no cilindro compensador do robô",
     "Óleo escorrendo pela haste do compensador de peso; terceiro caso em 60 dias.",
     "Aberta", None, None),
    (2, 1, "16:05", "Juliana Rocha", "chicote", "cabo", False, False, "Médio", "Não",
     "Capa do chicote rasgada no RP-01",
     "Capa externa do chicote rasgada perto do eixo 3; condutores ainda protegidos.",
     "Resolvida", "Substituída a capa do chicote no trecho do eixo 3 e refeita a fixação com abraçadeiras.", 3),
    (3, 0, "11:20", "Juliana Rocha", "carro_transversal", "folga", False, False, "Médio", "Sim",
     "Folga no carro transversal do torno",
     "Volante do carro transversal com 0,3 mm de folga; acabamento com vibração.",
     "Aberta", None, None),
    (4, 0, "07:30", "Marcos Pereira", "painel", "nao_liga", True, False, "Alto", "Não",
     "Torno TM-05 não liga",
     "Painel sem o LED de energia; fusível aparentemente íntegro.",
     "Aberta", None, None),
    # Utilidades: motor MT-01 (5), bomba BC-01 (6), compressor CA-01 (7)
    (6, 57, "08:10", "Roberto Alves", "selo", "vazamento", False, False, "Médio", "Não",
     "Vazamento no selo mecânico da bomba de água gelada",
     "Gotejamento contínuo no selo, cerca de 20 gotas por minuto.",
     "Resolvida", "Substituído o selo mecânico e conferido o alinhamento do acoplamento.", 6),
    (7, 49, "06:30", "Carlos Souza", "polia", "ruido", False, False, "Médio", "Não",
     "Chiado na correia do compressor na partida",
     "Correia patinando nos primeiros segundos após a partida.",
     "Resolvida", "Ajustada a tensão da correia e trocada a correia com desgaste nas laterais.", 2),
    (5, 46, "13:15", "Juliana Rocha", "tampa_traseira", "ruido", False, False, "Médio", "Não",
     "Ruído de rolamento no motor do exaustor",
     "Ruído metálico constante no lado da ventilação; vibração de 6,2 mm/s.",
     "Resolvida", "Substituído o rolamento traseiro (6205-2Z) e relubrificado o dianteiro.", 5),
    (6, 39, "10:40", "Roberto Alves", "mancal", "aquecimento", False, False, "Médio", "Não",
     "Mancal da bomba aquecendo",
     "Caixa de mancal a 78 °C; óleo escurecido no visor.",
     "Resolvida", "Trocado o óleo da caixa de mancal e desentupido o respiro.", 3),
    (7, 31, "07:05", "Carlos Souza", "carcaca", "aquecimento", True, False, "Alto", "Não",
     "Compressor desarmando por temperatura de descarga",
     "Desarme com 110 °C na descarga após 40 min em carga; radiador de óleo sujo.",
     "Resolvida", "Limpo o radiador de óleo e trocados o filtro e o óleo da unidade compressora.", 5),
    (5, 26, "15:30", "Juliana Rocha", "caixa_ligacao", "desarma", True, False, "Alto", "Não",
     "Motor do exaustor desarmando o disjuntor",
     "Disjuntor-motor desarma na partida; borne da fase T escurecido.",
     "Resolvida", "Refeita a conexão da fase T com terminal novo e reapertados os bornes com torque.", 3),
    (6, 20, "09:20", "Roberto Alves", "selo", "vazamento", False, False, "Médio", "Sim",
     "Selo da bomba vazando de novo",
     "Vazamento no selo mecânico 37 dias após a troca; acoplamento com desalinhamento.",
     "Resolvida", "Realinhado o conjunto motor-bomba a laser e substituído o selo.", 7),
    (7, 9, "11:50", "Marcos Pereira", "mancais", "vibracao", False, False, "Médio", "Não",
     "Vibração alta na unidade compressora",
     "Vibração de 7,1 mm/s no mancal do lado da polia.",
     "Em andamento", None, None),
    (6, 3, "14:20", "Roberto Alves", "acoplamento", "ruido", False, True, "Médio", "Não",
     "Batida no acoplamento da bomba",
     "Ruído de batida a cada volta; protetor do acoplamento com parafuso solto.",
     "Aberta", None, None),
    (5, 1, "08:00", "Carlos Souza", "ventilacao", "quebra", False, False, "Médio", "Não",
     "Tampa defletora do motor amassada",
     "Tampa defletora amassada raspando na ventoinha depois de uma batida de empilhadeira.",
     "Aberta", None, None),
]

# Pessoas e habilitações: validade em dias a partir de hoje (negativo = vencida).
# Alguns casos de propósito: NR-10 vencida, ASO vencendo, terceiro com NR-35 vencida, desligado.
PESSOAS = [
    ("10231", "Carlos Souza", "Manutenção", "Eletricista de manutenção", "CLT", "Fernanda Costa",
     {"ASO": 200, "NR-10": 300, "NR-12": 150, "Integração": 330}, True),
    ("10234", "Marcos Pereira", "Manutenção", "Mecânico de manutenção", "CLT", "Fernanda Costa",
     {"ASO": 90, "NR-10": -18, "NR-12": 120, "Integração": 200}, True),
    ("10240", "Ana Lima", "Produção", "Operadora de solda", "CLT", "Paulo Mendes",
     {"ASO": 12, "NR-12": 200, "Integração": 150}, True),
    ("10251", "Juliana Rocha", "Manutenção", "Técnica eletromecânica", "CLT", "Fernanda Costa",
     {"ASO": 300, "NR-10": 25, "NR-12": 310, "NR-35": 180, "Integração": 280}, True),
    ("10262", "Roberto Alves", "Utilidades", "Eletricista (terceiro)", "Terceiro", "Juliana Rocha",
     {"ASO": 100, "NR-10": 400, "NR-35": -5, "Integração": 60}, True),
    ("10270", "Fernanda Costa", "Segurança do Trabalho", "Técnica de segurança", "CLT", "Diretoria industrial",
     {"ASO": 250, "NR-10": 250, "NR-33": 250, "NR-35": 250, "Integração": 300}, True),
    ("10275", "Paulo Mendes", "Ferramentaria", "Torneiro mecânico", "CLT", "Fernanda Costa",
     {"ASO": 60, "NR-12": 40, "Integração": 90}, True),
    ("10281", "Lucas Martins", "Expedição", "Operador de empilhadeira", "Temporário", "Paulo Mendes",
     {"ASO": -3, "Integração": 20}, True),
    ("10288", "Beatriz Nunes", "RH", "Analista de RH", "CLT", "Diretoria administrativa",
     {"ASO": 180, "Integração": 200}, True),
    ("10190", "José Ribeiro", "Manutenção", "Eletricista", "CLT", "Fernanda Costa",
     {"ASO": 40, "NR-10": 100}, False),
]

# Um usuário por perfil para a demonstração (mesma senha do administrador)
USUARIOS = [
    ("Beatriz Nunes (RH)", "rh@nexar.com", "rh"),
    ("Fernanda Costa (Manutenção)", "manutencao@nexar.com", "manutencao"),
    ("Carlos Souza (Operador)", "operador@nexar.com", "operador"),
]


# Custo típico de peças por componente (R$), para os indicadores de custo
CUSTO_PECAS = {
    "compensador": 3800, "chicote": 2600, "eixo2": 950, "eixo4": 420, "eixo5": 1800, "eixo6": 640,
    "eixo1": 380, "base": 260, "contraponto": 120, "transmissao": 540, "carro_transversal": 90,
    "placa": 680, "porta_ferramenta": 210, "emergencia": 180, "cabecote": 460, "painel": 350, "fuso": 300,
    "selo": 1900, "polia": 380, "tampa_traseira": 260, "mancal": 150, "carcaca": 450, "caixa_ligacao": 120,
    "mancais": 2400, "acoplamento": 320, "ventilacao": 180,
}


def criar_pessoas_e_usuarios(conn) -> None:
    from werkzeug.security import generate_password_hash
    hoje = datetime.now().date()
    for mat, nome, setor, funcao, vinculo, gestor, quals, ativo in PESSOAS:
        cid = conn.execute(
            "INSERT INTO colaboradores (matricula, nome, setor, funcao, vinculo, gestor, admissao, ativo) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (mat, nome, setor, funcao, vinculo, gestor, (hoje - timedelta(days=400 + int(mat[-2:]) * 20)).isoformat(),
             int(ativo))).lastrowid
        for q, dias in quals.items():
            nexar.empresa.salvar_qualificacao(conn, cid, q, hoje + timedelta(days=dias))
    senha = os.getenv("ADMIN_PASSWORD", "").strip() or "nexar2026"
    for nome, email, perfil in USUARIOS:
        if not conn.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone():
            conn.execute("INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?,?,?,?)",
                         (nome, email, generate_password_hash(senha), perfil))
    conn.commit()
    print(f"✓ {len(PESSOAS)} pessoas com habilitações e {len(USUARIOS)} usuários de demonstração "
          f"({', '.join(u[1] for u in USUARIOS)})")


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
                       "ocorrencias", "diagramas", "percepcoes", "inspecoes_documento",
                       "qualificacoes", "colaboradores", "maquinas"):
            conn.execute(f"DELETE FROM {tabela}")
        conn.commit()

    admin = conn.execute("SELECT id FROM usuarios WHERE perfil = 'admin' ORDER BY id LIMIT 1").fetchone()
    admin_id = admin["id"] if admin else None

    # ── Máquinas e diagramas ───────────────────────────────────────────────
    ids: list[int] = []
    for m in MAQUINAS:
        cfg3d = nexar.modelos_3d.ler_config(json.dumps(m["modelo_3d"])) if m.get("modelo_3d") else None
        cur = conn.execute(
            "INSERT INTO maquinas (nome, modelo, fabricante, ano, setor, descricao, modelo_3d) VALUES (?,?,?,?,?,?,?)",
            (m["nome"], m["modelo"], m["fabricante"], m["ano"], m["setor"], m["descricao"],
             nexar.modelos_3d.config_para_salvar(cfg3d)),
        )
        mid = cur.lastrowid
        ids.append(mid)
        if m.get("mapa"):
            conn.execute("UPDATE maquinas SET mapa_x = ?, mapa_y = ? WHERE id = ?", (*m["mapa"], mid))
        n3d = nexar.modelos_3d.sincronizar_componentes(conn, mid, cfg3d)
        if n3d:
            print(f"  modelo 3D '{cfg3d.get('familia') or cfg3d.get('modelo')}' com {n3d} componentes → {m['nome']}")
    conn.commit()
    print(f"✓ {len(ids)} máquinas cadastradas")
    criar_pessoas_e_usuarios(conn)

    conn.close()

    # ── Ocorrências (em ordem cronológica, para o histórico alimentar a IA) ─
    if args.sem_ia:
        nexar.gemini_client = None  # get_ai_response cai no roteiro padrão
    usar_ia = nexar.gemini_client is not None
    if not usar_ia:
        print("! IA desligada ou GEMINI_API_KEY ausente — diagnósticos ficarão com o roteiro padrão.")
    agora = datetime.now()
    ordenadas = sorted(OCORRENCIAS, key=lambda o: -o[1])
    for n, (mi, dias, hora, operador, comp, sintoma, parada, risco, impacto, recorrente,
            desc, det, status, solucao, horas) in enumerate(ordenadas, 1):
        h, mnt = map(int, hora.split(":"))
        quando = (agora - timedelta(days=dias)).replace(hour=h, minute=mnt, second=0, microsecond=0)
        comp_nome = nexar._nome_componente(ids[mi], comp)
        campos = {
            "maquina_id": ids[mi], "data_ocorrencia": quando.strftime("%Y-%m-%d %H:%M"),
            "setor_area": MAQUINAS[mi]["setor"], "descricao": desc,
            "tipo_ocorrencia": "Segurança" if risco else "Manutenção",
            "nivel_impacto": impacto, "problema_recorrente": recorrente, "detalhamento_tecnico": det,
            "componente_apontado": comp, "componente_apontado_nome": comp_nome,
            "sintoma": sintoma, "maquina_parada": parada, "risco_pessoas": risco,
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
                solucao_aplicada, componente_real, data_resolucao, resolvido_por_id,
                componente_apontado, sintoma, maquina_parada, risco_pessoas, horas_trabalho, custo_pecas
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ids[mi], campos["data_ocorrencia"], operador, campos["setor_area"], desc,
             campos["tipo_ocorrencia"], impacto, recorrente, det,
             diag["resposta_ia"], diag["ia_status"],
             json.dumps(diag["anotacoes"], ensure_ascii=False) if diag["anotacoes"] else None,
             diag["diagrama_url"], status, quando.strftime("%Y-%m-%d %H:%M:%S"),
             solucao, comp_nome if resolvida else None, data_res, admin_id if resolvida else None,
             comp, sintoma, int(parada), int(risco),
             round(horas * 0.6, 1) if resolvida else None,
             CUSTO_PECAS.get(comp, 150) if resolvida else None),
        )
        conn.commit()
        conn.close()
        print(f"  [{n:2}/{len(ordenadas)}] {status:<12} {MAQUINAS[mi]['nome']}: {desc[:50]}")

    print(f"✓ {len(ordenadas)} ocorrências criadas em {nexar.DB_PATH}")


if __name__ == "__main__":
    main()
