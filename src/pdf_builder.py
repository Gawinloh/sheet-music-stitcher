"""
PDF Builder — assembles images into a multi-page PDF.

Takes a list of image paths and places them sequentially onto pages,
starting a new page when the current one is full.
"""

from pathlib import Path

from fpdf import FPDF
from PIL import Image


# Default page settings (A4 in mm)
PAGE_WIDTH_MM = 210
PAGE_HEIGHT_MM = 297
MARGIN_MM = 15


def build_pdf(image_paths: list[Path], output_path: Path):
    """
    Build a PDF from a list of image paths.

    Images are placed one after another vertically. When an image won't fit
    on the current page, a new page is started.
    """
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)

    usable_width = PAGE_WIDTH_MM - 2 * MARGIN_MM
    usable_height = PAGE_HEIGHT_MM - 2 * MARGIN_MM

    pdf.add_page()
    cursor_y = MARGIN_MM

    for img_path in image_paths:
        with Image.open(img_path) as img:
            img_width_px, img_height_px = img.size

        # Scale image to fit page width
        scale = usable_width / img_width_px
        display_width_mm = usable_width
        display_height_mm = img_height_px * scale

        # If image is taller than the usable area, scale it down further
        if display_height_mm > usable_height:
            scale = usable_height / img_height_px
            display_height_mm = usable_height
            display_width_mm = img_width_px * scale

        # Check if image fits on the current page
        if cursor_y + display_height_mm > PAGE_HEIGHT_MM - MARGIN_MM:
            pdf.add_page()
            cursor_y = MARGIN_MM

        # Center horizontally
        x = MARGIN_MM + (usable_width - display_width_mm) / 2

        pdf.image(str(img_path), x=x, y=cursor_y, w=display_width_mm, h=display_height_mm)
        cursor_y += display_height_mm

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
