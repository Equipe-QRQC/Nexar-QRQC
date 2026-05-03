"""
Gera diagramas técnicos de teste em PNG para usar no upload do Nexar QRQC.
Não substituem diagramas reais — são apenas pra validar o overlay da IA.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))


def _font(size=14, bold=False):
    """Tenta usar Arial; se não existir, cai pra default."""
    try:
        nome = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(nome, size)
    except Exception:
        return ImageFont.load_default()


# ── Diagrama 1: Prensa Hidráulica ─────────────────────────────────────────────

def diagrama_prensa():
    W, H = 1100, 700
    img = Image.new("RGB", (W, H), "#F8FAFC")
    d = ImageDraw.Draw(img)

    # Borda + título
    d.rectangle([10, 10, W-10, H-10], outline="#0D1117", width=2)
    d.text((20, 18), "PRENSA HIDRAULICA - PH200", fill="#0D1117", font=_font(20, True))
    d.text((20, 44), "Modelo: PH-200/40T  |  Pressao max: 250 bar  |  Capacidade: 40 toneladas",
           fill="#64748B", font=_font(12))

    # Reservatório de óleo (canto inferior esquerdo)
    d.rectangle([60, 480, 280, 640], outline="#0D1117", width=2, fill="#DBEAFE")
    d.text((100, 485), "RESERVATORIO DE OLEO", fill="#0D1117", font=_font(11, True))
    d.text((105, 605), "Capacidade: 80L", fill="#64748B", font=_font(10))
    # Linha de óleo (níveis)
    d.line([(60, 540), (280, 540)], fill="#1E40AF", width=1)
    d.text((230, 545), "Nivel", fill="#1E40AF", font=_font(9))

    # Bomba (centro inferior)
    d.ellipse([330, 510, 470, 620], outline="#0D1117", width=2, fill="#FEF3C7")
    d.text((355, 555), "BOMBA", fill="#0D1117", font=_font(13, True))
    d.text((357, 580), "Rexroth", fill="#0D1117", font=_font(10))
    d.text((355, 600), "A10VSO140", fill="#0D1117", font=_font(9))

    # Motor elétrico (acoplado à bomba)
    d.rectangle([200, 520, 320, 600], outline="#0D1117", width=2, fill="#E5E7EB")
    d.text((220, 530), "MOTOR", fill="#0D1117", font=_font(12, True))
    d.text((220, 555), "30 kW", fill="#64748B", font=_font(11))
    d.text((220, 575), "1750 rpm", fill="#64748B", font=_font(10))

    # Filtro
    d.rectangle([500, 530, 580, 600], outline="#0D1117", width=2, fill="#FEE2E2")
    d.text((516, 545), "FILTRO", fill="#0D1117", font=_font(11, True))
    d.text((518, 570), "10 um", fill="#64748B", font=_font(10))

    # Válvula direcional
    d.rectangle([620, 380, 760, 460], outline="#0D1117", width=2, fill="#D1FAE5")
    d.text((635, 395), "VALVULA", fill="#0D1117", font=_font(12, True))
    d.text((635, 415), "DIRECIONAL", fill="#0D1117", font=_font(11))
    d.text((640, 437), "4/3 vias", fill="#64748B", font=_font(10))

    # Cilindro hidráulico (destaque)
    d.rectangle([800, 200, 1020, 460], outline="#0D1117", width=3, fill="#FEF3C7")
    d.text((830, 215), "CILINDRO PRINCIPAL", fill="#0D1117", font=_font(12, True))
    d.text((835, 235), "D: 200mm  Curso: 400mm", fill="#64748B", font=_font(10))
    # Pistão
    d.rectangle([850, 270, 970, 330], outline="#0D1117", width=2, fill="#9CA3AF")
    d.text((875, 290), "PISTAO", fill="#FFF", font=_font(11, True))
    # Vedações
    d.line([(850, 270), (970, 270)], fill="#EF4444", width=3)
    d.line([(850, 330), (970, 330)], fill="#EF4444", width=3)
    d.text((855, 250), "Vedacoes", fill="#EF4444", font=_font(9, True))

    # Manometro
    d.ellipse([700, 250, 780, 330], outline="#0D1117", width=2, fill="#FEE2E2")
    d.text((718, 280), "P", fill="#DC2626", font=_font(20, True))
    d.text((708, 335), "Manometro", fill="#0D1117", font=_font(9))

    # Linhas de fluxo (mangueiras)
    d.line([(280, 560), (330, 560)], fill="#3B82F6", width=4)  # reservatório → bomba
    d.line([(470, 560), (500, 560)], fill="#3B82F6", width=4)  # bomba → filtro
    d.line([(580, 560), (690, 560), (690, 460)], fill="#3B82F6", width=4)  # filtro → válvula
    d.line([(760, 420), (800, 420), (800, 300)], fill="#3B82F6", width=4)  # válvula → cilindro
    d.line([(700, 290), (760, 380)], fill="#3B82F6", width=2)  # manômetro

    # Legenda
    d.rectangle([60, 120, 350, 200], outline="#0D1117", width=1, fill="#FFF")
    d.text((75, 130), "LEGENDA:", fill="#0D1117", font=_font(11, True))
    d.line([(75, 152), (100, 152)], fill="#3B82F6", width=4)
    d.text((110, 146), "Linha de pressao (oleo)", fill="#0D1117", font=_font(10))
    d.line([(75, 172), (100, 172)], fill="#EF4444", width=3)
    d.text((110, 166), "Vedacao critica", fill="#0D1117", font=_font(10))

    out = os.path.join(OUT, "diagrama_prensa_hidraulica.png")
    img.save(out, "PNG")
    print(f"OK: {out}")
    return out


# ── Diagrama 2: Motor Elétrico Trifásico ──────────────────────────────────────

def diagrama_motor():
    W, H = 1100, 700
    img = Image.new("RGB", (W, H), "#F8FAFC")
    d = ImageDraw.Draw(img)

    d.rectangle([10, 10, W-10, H-10], outline="#0D1117", width=2)
    d.text((20, 18), "MOTOR ELETRICO TRIFASICO - WEG W22", fill="#0D1117", font=_font(20, True))
    d.text((20, 44), "Modelo: 132S/M  |  Potencia: 7.5 kW  |  Polos: 4  |  IP55",
           fill="#64748B", font=_font(12))

    # Carcaça do motor
    d.rectangle([350, 200, 850, 500], outline="#0D1117", width=3, fill="#E5E7EB")
    d.text((420, 210), "CARCACA DO MOTOR", fill="#0D1117", font=_font(11, True))

    # Estator (anel externo)
    d.ellipse([400, 240, 800, 460], outline="#0D1117", width=3, fill="#FFF")
    d.text((570, 258), "ESTATOR", fill="#0D1117", font=_font(12, True))

    # Rotor (anel interno)
    d.ellipse([480, 290, 720, 410], outline="#0D1117", width=2, fill="#FEF3C7")
    d.text((570, 340), "ROTOR", fill="#0D1117", font=_font(13, True))

    # Eixo (sai do rotor)
    d.line([(720, 350), (920, 350)], fill="#0D1117", width=8)
    d.text((830, 320), "EIXO", fill="#0D1117", font=_font(11, True))

    # Rolamentos (em volta do eixo)
    d.ellipse([430, 320, 470, 380], outline="#0D1117", width=2, fill="#FEE2E2")
    d.text((420, 388), "Rolamento", fill="#DC2626", font=_font(9, True))
    d.text((430, 402), "Dianteiro", fill="#DC2626", font=_font(9))
    d.ellipse([770, 320, 810, 380], outline="#0D1117", width=2, fill="#FEE2E2")
    d.text((760, 388), "Rolamento", fill="#DC2626", font=_font(9, True))
    d.text((775, 402), "Traseiro", fill="#DC2626", font=_font(9))

    # Caixa de ligações
    d.rectangle([720, 480, 880, 580], outline="#0D1117", width=2, fill="#D1FAE5")
    d.text((735, 490), "CAIXA DE", fill="#0D1117", font=_font(11, True))
    d.text((735, 510), "LIGACOES", fill="#0D1117", font=_font(11, True))
    # Bornes
    for i in range(3):
        d.ellipse([745 + i*38, 545, 770 + i*38, 565], outline="#0D1117", width=1, fill="#FBBF24")
        d.text((751 + i*38, 548), "U" if i == 0 else ("V" if i == 1 else "W"), fill="#0D1117", font=_font(10, True))

    # Ventilador (atrás)
    d.ellipse([280, 290, 360, 410], outline="#0D1117", width=2, fill="#DBEAFE")
    d.text((290, 340), "FAN", fill="#1E40AF", font=_font(11, True))
    d.text((280, 415), "Ventilador", fill="#1E40AF", font=_font(9))

    # Sensor PT100 (na carcaça)
    d.rectangle([530, 175, 670, 200], outline="#0D1117", width=1, fill="#FEE2E2")
    d.text((545, 178), "Sensor PT100 - 78°C", fill="#DC2626", font=_font(10, True))

    # Placa de identificação
    d.rectangle([60, 540, 320, 640], outline="#0D1117", width=1, fill="#FFF")
    d.text((75, 550), "PLACA DE IDENTIFICACAO:", fill="#0D1117", font=_font(10, True))
    d.text((75, 572), "WEG W22 - 132S/M", fill="#0D1117", font=_font(10))
    d.text((75, 588), "7.5 kW / 10 cv  |  4 polos", fill="#64748B", font=_font(10))
    d.text((75, 604), "1750 rpm  |  IP55  |  ICL.F", fill="#64748B", font=_font(10))
    d.text((75, 620), "Tensao: 220/380/440V", fill="#64748B", font=_font(10))

    out = os.path.join(OUT, "diagrama_motor_eletrico.png")
    img.save(out, "PNG")
    print(f"OK: {out}")
    return out


if __name__ == "__main__":
    diagrama_prensa()
    diagrama_motor()
    print("\nDiagramas gerados! Faca upload em /maquinas/cadastro")
