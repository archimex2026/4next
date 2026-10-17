"""Local Unicode PDF export; source material never leaves the server for conversion."""
import os
from pathlib import Path


def _unicode_font():
    candidates = [os.getenv("PDF_FONT_PATH", ""),
                  "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("Instalează un font Unicode (DejaVu Sans) sau setează PDF_FONT_PATH pentru export PDF.")


def render_study_pdf(title, language, sections):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Study", fname=_unicode_font())
    pdf.set_title(title)
    pdf.set_author("4Next")
    pdf.set_lang(language)
    pdf.add_page()
    pdf.set_font("Study", size=19)
    pdf.set_text_color(35, 71, 61)
    pdf.multi_cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    for heading, content in sections:
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_font("Study", size=13)
        pdf.set_text_color(35, 71, 61)
        pdf.multi_cell(0, 8, str(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Study", size=10)
        pdf.set_text_color(35, 40, 38)
        # Control characters do not belong in a text PDF. Preserve all printable source text.
        content = "".join(char for char in str(content) if char.isprintable() or char in "\n\t")
        pdf.multi_cell(0, 5.5, content.replace("\t", "    "), new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="WORD")
        pdf.ln(5)
    return bytes(pdf.output())
