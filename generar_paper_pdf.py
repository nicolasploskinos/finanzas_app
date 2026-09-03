"""Genera "Montor - Paper.pdf" a partir de paper_montor.md.

Uso: python generar_paper_pdf.py

Convierte el markdown del paper a PDF con portada, índice clickeable,
encabezado/pie corridos y numeración de páginas. Usa Arial embebida (no las
fuentes core de PDF) porque el texto tiene acentos y comillas tipográficas
que las fuentes core no cubren.
"""
import os
import re
import sys

from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(BASE, "paper_montor.md")
PDF = os.path.join(BASE, "Montor - Paper.pdf")

FUENTES = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
ARIAL = {
    "": os.path.join(FUENTES, "arial.ttf"),
    "B": os.path.join(FUENTES, "arialbd.ttf"),
    "I": os.path.join(FUENTES, "ariali.ttf"),
    "BI": os.path.join(FUENTES, "arialbi.ttf"),
}

TITULO = "Montor"
SUBTITULO = "Aplicación web de finanzas personales multi-moneda con asistencia de IA"


class Paper(FPDF):
    def __init__(self):
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(22, 20, 22)
        for estilo, ruta in ARIAL.items():
            self.add_font("Arial", estilo, ruta)

    def header(self):
        if self.page_no() == 1:  # portada
            return
        self.set_font("Arial", "", 8)
        self.set_text_color(130)
        self.cell(0, 6, TITULO, align="L")
        self.set_x(-self.r_margin - 60)
        self.cell(60, 6, "Paper técnico", align="R")
        self.set_draw_color(220)
        self.line(self.l_margin, 22, self.w - self.r_margin, 22)
        self.ln(8)
        self.set_text_color(0)

    def footer(self):
        if self.page_no() == 1:  # portada
            return
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(130)
        self.cell(0, 8, str(self.page_no() - 1), align="C")
        self.set_text_color(0)


def limpiar(texto):
    """Markdown inline -> texto plano (fpdf write_html no se usa acá)."""
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", texto)
    texto = re.sub(r"`(.+?)`", r"\1", texto)
    return texto


def parsear(md):
    """Devuelve una lista de bloques (tipo, texto) desde el markdown."""
    bloques = []
    for linea in md.split("\n"):
        s = linea.strip()
        if not s or s == "---":
            continue
        if s.startswith("### "):
            bloques.append(("h3", limpiar(s[4:])))
        elif s.startswith("## "):
            bloques.append(("h2", limpiar(s[3:])))
        elif s.startswith("# "):
            bloques.append(("h1", limpiar(s[2:])))
        elif s.startswith("- "):
            bloques.append(("li", limpiar(s[2:])))
        else:
            bloques.append(("p", limpiar(s)))
    return bloques


def main():
    if not all(os.path.exists(r) for r in ARIAL.values()):
        sys.exit("No se encontraron las fuentes Arial en " + FUENTES)

    md = open(MD, encoding="utf-8").read()
    bloques = parsear(md)

    pdf = Paper()

    # ── Portada ──
    pdf.add_page()
    pdf.ln(70)
    pdf.set_font("Arial", "B", 30)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 13, TITULO, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "", 13)
    pdf.set_text_color(70)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 7, SUBTITULO, align="C")
    pdf.ln(24)
    pdf.set_text_color(0)
    pdf.set_font("Arial", "", 12)
    for linea in ("Nicolás Ploskinos", "Septiembre de 2026"):
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, linea, align="C")

    # ── Índice (se completa al final, cuando se conocen las páginas) ──
    pdf.add_page()
    pagina_indice = pdf.page_no()
    pdf.set_font("Arial", "B", 17)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 10, "Índice")
    pdf.ln(4)
    y_indice = pdf.get_y()

    # ── Cuerpo ──
    pdf.add_page()
    indice = []  # (nivel, titulo, pagina, y)
    primera = True
    for tipo, texto in bloques:
        if tipo == "h1":
            continue  # el título ya está en la portada
        if tipo == "h2":
            if not primera:
                pdf.ln(4)
            indice.append((2, texto, pdf.page_no() - 1, pdf.get_y()))
            pdf.set_font("Arial", "B", 15)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 8, texto)
            pdf.ln(2)
        elif tipo == "h3":
            indice.append((3, texto, pdf.page_no() - 1, pdf.get_y()))
            pdf.set_font("Arial", "B", 12)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, texto)
            pdf.ln(1)
        elif tipo == "li":
            pdf.set_font("Arial", "", 10.5)
            pdf.set_x(pdf.l_margin)
            x = pdf.get_x()
            pdf.cell(5, 5.6, "•")
            pdf.set_x(x + 5)
            pdf.multi_cell(0, 5.6, texto)
            pdf.ln(1)
        else:
            pdf.set_font("Arial", "", 10.5)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5.6, texto, align="J")
            pdf.ln(2.5)
        primera = False

    # ── Índice, ahora con las páginas reales y links clickeables ──
    pdf.page = pagina_indice
    pdf.set_y(y_indice)
    for nivel, texto, pagina, y in indice:
        link = pdf.add_link()
        pdf.set_link(link, y=y, page=pagina + 1)
        pdf.set_font("Arial", "B" if nivel == 2 else "", 10.5 if nivel == 2 else 10)
        pdf.set_x(pdf.l_margin + (0 if nivel == 2 else 6))
        ancho = pdf.w - pdf.l_margin - pdf.r_margin - (0 if nivel == 2 else 6) - 12
        pdf.cell(ancho, 6.5, texto, link=link)
        pdf.cell(12, 6.5, str(pagina), align="R", link=link)
        pdf.ln(6.5)

    pdf.output(PDF)
    print(f"OK: {PDF} ({pdf.pages_count} páginas)")


if __name__ == "__main__":
    main()
