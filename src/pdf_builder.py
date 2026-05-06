"""
PDF Builder — assembles images into a multi-page PDF.

Uses layout placements to position images on pages.
Optionally adds a title page and page numbers.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fpdf import FPDF
from PIL import Image

from src.layout import PageSettings, compute_layout, get_page_settings


@dataclass
class TitleInfo:
    """Optional title page content."""
    title: str
    composer: Optional[str] = None
    date: Optional[str] = None


def _add_title_page(pdf: FPDF, title_info: TitleInfo, settings: PageSettings):
    """Add a title page with song title, composer, and optional date."""
    pdf.add_page()

    # Title — large, centered, positioned at ~40% down the page
    title_y = settings.height_mm * 0.35
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_y(title_y)
    pdf.cell(w=0, h=12, text=title_info.title, align="C", new_x="LMARGIN", new_y="NEXT")

    # Composer — smaller, below title
    if title_info.composer:
        pdf.ln(8)
        pdf.set_font("Helvetica", "", 18)
        pdf.cell(w=0, h=10, text=title_info.composer, align="C", new_x="LMARGIN", new_y="NEXT")

    # Date — even smaller, below composer
    if title_info.date:
        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(w=0, h=8, text=title_info.date, align="C", new_x="LMARGIN", new_y="NEXT")


def _add_page_numbers(pdf: FPDF, settings: PageSettings, start_page: int = 1):
    """Add page numbers to all pages starting from start_page (0-indexed in fpdf)."""
    total_music_pages = pdf.page - start_page + 1
    footer_y = settings.height_mm - settings.margin_mm + 3

    for page_num in range(start_page, pdf.page + 1):
        pdf.page = page_num
        pdf.set_font("Helvetica", "", 9)
        pdf.set_y(footer_y)
        display_num = page_num - start_page + 1
        pdf.cell(w=0, h=5, text=str(display_num), align="C")


def build_pdf(
    images: list[Image.Image],
    output_path: Path,
    settings: PageSettings = None,
    title_info: TitleInfo = None,
):
    """
    Build a PDF from a list of PIL Images using adaptive layout.

    Optionally includes a title page and page numbers on music pages.
    """
    if settings is None:
        settings = get_page_settings()

    placements = compute_layout(images, settings)

    pdf = FPDF(unit="mm", format=(settings.width_mm, settings.height_mm))
    pdf.set_auto_page_break(auto=False)

    # Track which page number music starts on
    music_start_page = 1

    # Add title page if requested
    if title_info:
        _add_title_page(pdf, title_info, settings)
        music_start_page = 2

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save all images to temp files
        img_paths = []
        for i, img in enumerate(images):
            img_path = Path(tmp_dir) / f"img_{i:04d}.png"
            img.save(img_path)
            img_paths.append(img_path)

        # Add pages and place images
        # page_offset accounts for title page
        pages_added = 0
        for placement in placements:
            while pages_added <= placement.page_index:
                pdf.add_page()
                pages_added += 1

            pdf.image(
                str(img_paths[placement.image_index]),
                x=placement.x_mm,
                y=placement.y_mm,
                w=placement.width_mm,
                h=placement.height_mm,
            )

    # Add page numbers to music pages (not title page)
    if pdf.page >= music_start_page:
        _add_page_numbers(pdf, settings, start_page=music_start_page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
