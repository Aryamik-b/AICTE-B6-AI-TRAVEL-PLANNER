from fpdf import FPDF
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Remove markdown symbols
    text = re.sub(r"[*_`>#]", "", text)

    # Replace bullets and long dashes
    text = text.replace("•", "-")
    text = text.replace("–", "-").replace("—", "-")

    # Remove unicode/emojis (fpdf core fonts can't handle)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Remove weird spaces
    text = text.replace("\xa0", " ")

    return text.strip()


def force_wrap_line(line: str, max_chars: int = 90) -> list[str]:
    """
    Break any line into chunks of max_chars to avoid fpdf line-break exceptions.
    Works even if there are no spaces.
    """
    if not line:
        return [""]

    # If already short, keep it
    if len(line) <= max_chars:
        return [line]

    chunks = []
    i = 0
    while i < len(line):
        chunks.append(line[i:i + max_chars])
        i += max_chars
    return chunks


def generate_pdf_bytes(title: str, content: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Use smaller font to reduce layout issues
    pdf.set_font("Arial", style="B", size=14)
    pdf.multi_cell(180, 8, clean_text(title))
    pdf.ln(2)

    pdf.set_font("Arial", size=10)

    cleaned = clean_text(content)

    for raw_line in cleaned.split("\n"):
        raw_line = raw_line.strip()

        # blank line spacing
        if raw_line == "":
            pdf.ln(2)
            continue

        # hard wrap lines into safe chunks
        for chunk in force_wrap_line(raw_line, max_chars=90):
            try:
                pdf.multi_cell(180, 6, chunk)
            except Exception:
                # extreme fallback: remove any remaining problematic characters
                safe = chunk.encode("ascii", "ignore").decode("ascii")
                safe = safe[:90]
                pdf.multi_cell(180, 6, safe)

    out = pdf.output(dest="S")
    if isinstance(out,(bytes, bytearray)):
        return bytes(out)
    return out.encode("latin-1","ignore")
