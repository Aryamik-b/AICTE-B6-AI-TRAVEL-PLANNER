from fpdf import FPDF
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Remove common markdown symbols
    text = re.sub(r"[*_`>#]", "", text)

    # Replace bullets
    text = text.replace("•", "-")

    return text.strip()


def break_long_words(line: str, max_len: int = 80) -> str:
    """
    Break long unspaced strings so fpdf can wrap them.
    """
    if not line:
        return line

    # Split by spaces; if any token is too long, insert breaks
    parts = line.split(" ")
    new_parts = []

    for p in parts:
        if len(p) > max_len:
            # break into chunks
            chunks = [p[i:i+max_len] for i in range(0, len(p), max_len)]
            new_parts.append("\n".join(chunks))
        else:
            new_parts.append(p)

    return " ".join(new_parts)


def generate_pdf_bytes(title: str, content: str) -> bytes:
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

    for raw_line in cleaned.split("\n"):
        line = break_long_words(raw_line, max_len=80)
        pdf.multi_cell(0, 6, line)

    return pdf.output(dest="S").encode("latin-1", "ignore")
