import os
import re
import requests
from fpdf import FPDF


def parse_recipe_name(recipe_text: str):
    pattern = re.compile(r"(?i)(recipe name:\s*)(.*)")
    match = pattern.search(recipe_text)
    if not match:
        return None, recipe_text

    raw_name = match.group(2).strip()
    cleaned_text = recipe_text.replace(match.group(0), "", 1).strip()

    recipe_name = strip_markdown(raw_name).replace("**", "").strip()

    return recipe_name, cleaned_text


def strip_markdown(md):
    """Convert markdown text to plain text by removing common markdown syntax."""
    md = re.sub(r"\#+\s*", "", md)  # Remove headers
    md = re.sub(r"\*\*([^*]+)\*\*", r"\1", md)  # Remove bold
    md = re.sub(r"\*([^*]+)\*", r"\1", md)  # Remove italic
    md = re.sub(r"^\s*[\*\-]\s+", "", md, flags=re.MULTILINE)  # Remove bullets
    md = re.sub(r"`([^`]+)`", r"\1", md)  # Remove inline code
    md = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", md)  # Remove links
    return md


def create_pdf(recipe_name, recipe_image_url, clean_text):
    """
    1. Downloads the recipe image.
    2. Places a header with the recipe name (if any) at the top (left-aligned).
    3. Left-aligns a larger image (e.g., 80 mm wide x 80 mm high).
    4. Places the plain-text recipe below the image.
    Returns the PDF content as bytes.
    """
    # Download the image
    response = requests.get(recipe_image_url)
    if response.status_code != 200:
        return None

    # Save image to temp file
    import tempfile

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_img.write(response.content)
    temp_img.flush()
    temp_img.close()

    # Strip markdown and ensure Latin-1 encoding
    plain_text = strip_markdown(clean_text)
    plain_text_clean = plain_text.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()

    # 1) Add a header with the recipe name, left-aligned, bold font, size 16
    pdf.set_font("Times", "B", 16)
    if recipe_name:
        pdf.cell(0, 10, txt=recipe_name, ln=True, align="C")
    else:
        pdf.cell(0, 10, txt="Recipe", ln=True, align="C")
    pdf.ln(5)

    # 2) Add the image, left-aligned (x=10), bigger size (80 x 80 mm)
    image_width = 80
    image_height = 80
    pdf.image(temp_img.name, x=10, y=pdf.get_y(), w=image_width, h=image_height)
    pdf.set_y(pdf.get_y() + image_height + 2)  # move below the image

    # 3) Add the plain-text recipe
    pdf.set_font("Times", size=11)
    pdf.multi_cell(0, 8, plain_text_clean)

    os.unlink(temp_img.name)

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    return pdf_bytes
