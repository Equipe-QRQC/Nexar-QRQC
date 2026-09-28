"""
Gera fotos de documentos de exemplo para demonstrar a Inspeção de Documento
com a base de demonstração (scripts/seed_demo.py):

  docs/exemplos/pt_eletricidade_RS-01.jpg  → BLOQUEADO: Marcos Pereira com NR-10 vencida
  docs/exemplos/os_manutencao_TM-04.jpg    → PENDÊNCIAS: soma de horas errada e sem assinatura
  docs/exemplos/pt_altura_telhado.jpg      → APROVADO: executante habilitado e documento completo

Uso: python scripts/gerar_documentos_exemplo.py
"""
from __future__ import annotations

import math
import os
import random
import textwrap
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "docs", "exemplos")
PASTAS_FONTES = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
                 "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental"]


def fonte(nomes: str, tam: int):
    """Primeira fonte encontrada entre as alternativas (Linux, Windows, macOS)."""
    for nome in nomes.split("|"):
        for pasta in PASTAS_FONTES:
            try:
                return ImageFont.truetype(os.path.join(pasta, nome), tam)
            except OSError:
                continue
    return ImageFont.load_default()


NEGRITO = "DejaVuSans-Bold.ttf|LiberationSans-Bold.ttf|arialbd.ttf|Arial Bold.ttf"
NORMAL = "DejaVuSans.ttf|LiberationSans-Regular.ttf|arial.ttf|Arial.ttf"
TITULO, ROTULO, CANETA = (fonte(NEGRITO, 34), fonte(NEGRITO, 19),
                          fonte("LiberationSans-Italic.ttf|ariali.ttf|Arial Italic.ttf", 27))
AZUL_CANETA = (22, 44, 120)


def assinatura(d: ImageDraw.ImageDraw, x: int, y: int, semente: int) -> None:
    rnd = random.Random(semente)
    pts = []
    for i in range(46):
        t = i / 45
        pts.append((x + t * 210, y + 18 * math.sin(t * 11 + rnd.random()) + rnd.uniform(-5, 5)))
    d.line(pts, fill=AZUL_CANETA, width=3)


def documento(nome_arquivo: str, titulo: str, numero: str, campos: list[tuple[str, str]],
              assinaturas: list[tuple[str, bool]], observacao: str = "") -> None:
    img = Image.new("RGB", (1240, 1754), (252, 252, 248))
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, 1180, 170], outline=(30, 30, 30), width=3)
    d.text((90, 78), "EMPRESA DEMONSTRAÇÃO LTDA.", font=ROTULO, fill=(60, 60, 60))
    d.text((90, 108), titulo, font=TITULO, fill=(20, 20, 20))
    d.text((960, 78), "Nº", font=ROTULO, fill=(60, 60, 60))
    d.text((960, 108), numero, font=CANETA, fill=AZUL_CANETA)

    y = 200
    for rotulo, valor in campos:
        partes = textwrap.wrap(valor, 50) or [""]
        linhas = len(partes)
        altura = 60 + 30 * (linhas - 1)
        d.rectangle([60, y, 1180, y + altura], outline=(40, 40, 40), width=2)
        d.text((76, y + 8), rotulo.upper(), font=fonte(NEGRITO, 15), fill=(70, 70, 70))
        for i, parte in enumerate(partes):
            d.text((380, y + 14 + 30 * i), parte, font=CANETA, fill=AZUL_CANETA)
        y += altura + 8

    if observacao:
        y += 10
        d.text((60, y), "OBSERVAÇÕES", font=ROTULO, fill=(40, 40, 40))
        d.text((60, y + 34), observacao, font=CANETA, fill=AZUL_CANETA)
        y += 90

    y = max(y + 40, 1420)
    largura = (1120 - 40 * (len(assinaturas) - 1)) // len(assinaturas)
    for i, (rotulo, assinada) in enumerate(assinaturas):
        x = 60 + i * (largura + 40)
        if assinada:
            assinatura(d, x + 20, y + 30, i * 7 + len(numero))
        d.line([x, y + 70, x + largura, y + 70], fill=(30, 30, 30), width=2)
        d.text((x, y + 80), rotulo, font=fonte(NORMAL, 17), fill=(60, 60, 60))

    # Aparência de foto: leve rotação, perspectiva e desfoque
    foto = img.rotate(-1.2, resample=Image.BICUBIC, expand=True, fillcolor=(205, 200, 190))
    foto = foto.filter(ImageFilter.GaussianBlur(0.6)).resize((1000, int(1000 * foto.height / foto.width)))
    os.makedirs(SAIDA, exist_ok=True)
    foto.save(os.path.join(SAIDA, nome_arquivo), quality=86)
    print("  " + os.path.join("docs", "exemplos", nome_arquivo))


def main() -> None:
    hoje = datetime.now().strftime("%d/%m/%Y")
    documento(
        "pt_eletricidade_RS-01.jpg", "PERMISSÃO DE TRABALHO — ELETRICIDADE", "PT-2026-0412",
        [("Data / validade", f"{hoje} das 08:00 às 17:00"),
         ("Local / equipamento", "Célula de solda 1 — Robô de Solda RS-01 (painel do eixo 2)"),
         ("Atividade", "Troca do cabo de alimentação do motor do eixo 2 e reaperto dos bornes"),
         ("Executante 1", "Marcos Pereira — matrícula 10234"),
         ("Executante 2", "Carlos Souza — matrícula 10231"),
         ("Riscos e controles", "Choque elétrico: bloqueio do disjuntor Q12, teste de ausência de tensão, luvas classe 0"),
         ("Bloqueio (LOTO)", "Sim — cadeado 07, etiqueta nº 3321")],
        [("Emitente — Fernanda Costa (10270)", True), ("Executante — Marcos Pereira", True),
         ("Executante — Carlos Souza", True)])
    documento(
        "os_manutencao_TM-04.jpg", "ORDEM DE SERVIÇO DE MANUTENÇÃO", "OS-8817",
        [("Equipamento", "Torno Mecânico TM-04 — Ferramentaria"),
         ("Serviço executado", "Ajuste da régua (gib) do carro transversal e lubrificação do fuso"),
         ("Executante", "Paulo Mendes — matrícula 10275"),
         ("Horas trabalhadas", "2,5 h + 3 h + 1,5 h = 6 h"),
         ("Peças utilizadas", "Graxa EP2 (200 g); parafuso de ajuste M6 (2 un.)"),
         ("Data de conclusão", hoje)],
        [("Executante — Paulo Mendes", True), ("Responsável pela manutenção", False)],
        observacao="Folga medida após ajuste: 0,02 mm.")
    documento(
        "pt_altura_telhado.jpg", "PERMISSÃO DE TRABALHO — ALTURA", "PT-2026-0415",
        [("Data / validade", f"{hoje} das 07:30 às 12:00"),
         ("Local", "Telhado do galpão 2 — calha lateral"),
         ("Atividade", "Limpeza da calha e troca de 3 telhas trincadas"),
         ("Executante", "Fernanda Costa — matrícula 10270"),
         ("Ancoragem e EPI", "Linha de vida fixa LV-02; cinturão paraquedista CA 35529; capacete com jugular"),
         ("Condições do tempo", "Sem chuva, vento fraco")],
        [("Emitente — Juliana Rocha (10251)", True), ("Executante — Fernanda Costa", True)])


if __name__ == "__main__":
    print("Gerando documentos de exemplo:")
    main()
