from fpdf import FPDF
import re


def clean_text(text: str) -> str:
    """
    Make text safe for FPDF core fonts by removing emojis/unicode
    and cleaning markdown symbols.
    """
    if not text:
        return ""

    # Remove markdown symbols
    text = re.sub(r"[*_`>#]", "", text)

    # Replace bullet characters
    text = text.replace("•", "-")
    text = text.replace("–", "-").replace("—", "-")

    # Remove emojis / unsupported unicode characters
    # Keep only basic ASCII characters + newline/tab
    text = text.encode("ascii", "ignore").decode("ascii")

    # Remove repeated spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def break_long_words(line: str, max_len: int = 80) -> str:
    """
    Break long strings without spaces so fpdf can wrap them.
    """
    if not line:
        return line

    parts = line.split(" ")
    new_parts = []

    for p in parts:
        if len(p) > max_len:
            chunks = [p[i:i+max_len] for i in range(0, len(p), max_len)]
            new_parts.append("\n".join(chunks))
        else:
            new_parts.append(p)

    return " ".join(new_parts)


def generate_pdf_bytes(title: str, content: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Use core font (safe)
    pdf.set_font("Arial", style="B", size=16)
    pdf.multi_cell(0, 10, clean_text(title))
    pdf.ln(4)

    pdf.set_font("Arial", size=11)

    cleaned = clean_text(content)

    for raw_line in cleaned.split("\n"):
        safe_line = break_long_words(raw_line, max_len=80)

        # Important: skip lines that become empty
        if safe_line.strip() == "":
            pdf.ln(2)
            continue

        pdf.multi_cell(0, 6, safe_line)

    return pdf.output(dest="S").encode("latin-1", "ignore")
