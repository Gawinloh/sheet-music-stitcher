"""
PDF Builder — assembles images into a multi-page PDF.

Uses layout placements to position images on pages.
"""

import tempfile
from pathlib import Path

from fpdf import FPDF
from PIL import Image

from src.layout import PageSettings, ImagePlacement, compute_layout, get_page_settings


def build_pdf(images: list[Image.Image], output_path: Path, settings: PageSettings = None):
    """
    Build a PDF from a list of PIL Images using adaptive layout.

    Images are placed according to the computed layout plan.
    """
    if settings is None:
        settings = get_page_settings()

    placements = compute_layout(images, settings)

    pdf = FPDF(unit="mm", format=(settings.width_mm, settings.height_mm))
    pdf.set_auto_page_break(auto=False)

    # Determine total pages needed
    total_pages = max(p.page_index for p in placements) + 1 if placements else 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save all images to temp files
        img_paths = []
        for i, img in enumerate(images):
            img_path = Path(tmp_dir) / f"img_{i:04d}.png"
            img.save(img_path)
            img_paths.append(img_path)

        # Add pages and place images
        pages_added = 0
        for placement in placements:
            # Add pages as needed
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
