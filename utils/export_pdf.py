from fpdf import FPDF
import re


def clean_text(text: str) -> str:
    """
    Clean markdown and unsupported characters lightly for PDF.
    """
    if not text:
        return ""

    # Remove common markdown symbols
    text = re.sub(r"[*_`>#]", "", text)

    # Replace bullets
    text = text.replace("•", "-")

    return text.strip()


def generate_pdf_bytes(title: str, content: str) -> bytes:
    """
    Creates a PDF from plain text and returns PDF as bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)

    # Content
    pdf.set_font("Arial", size=11)
    cleaned = clean_text(content)

    for line in cleaned.split("\n"):
        pdf.multi_cell(0, 6, line)
    pdf.ln(2)

    # Output as bytes
    return pdf.output(dest="S").encode("latin-1", "ignore")
