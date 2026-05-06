"""
Adaptive Multi-Page Layout.

Computes how images should be placed on pages: scaling, positioning,
and page breaks. Returns a layout plan that pdf_builder uses to assemble the PDF.
"""

from dataclasses import dataclass
from PIL import Image


# Page sizes in mm
PAGE_SIZES = {
    "a4": (210, 297),
    "letter": (215.9, 279.4),
}


@dataclass
class PageSettings:
    """Page configuration."""
    width_mm: float
    height_mm: float
    margin_mm: float
    gap_mm: float

    @property
    def usable_width(self) -> float:
        return self.width_mm - 2 * self.margin_mm

    @property
    def usable_height(self) -> float:
        return self.height_mm - 2 * self.margin_mm


@dataclass
class ImagePlacement:
    """Where and how to place a single image on a page."""
    page_index: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    image_index: int  # index into the original images list


def compute_layout(images: list[Image.Image], settings: PageSettings) -> list[ImagePlacement]:
    """
    Compute the layout for a list of images across pages.

    Greedily packs images onto pages:
    - Scale each image to fit the usable width (maintain aspect ratio)
    - If an image won't fit on the current page (with gap), start a new page
    - Center images horizontally

    Returns a list of ImagePlacement objects describing where each image goes.
    """
    placements = []
    current_page = 0
    cursor_y = settings.margin_mm

    for i, img in enumerate(images):
        img_width_px, img_height_px = img.size

        # Scale to fit page width
        scale = settings.usable_width / img_width_px
        display_width_mm = settings.usable_width
        display_height_mm = img_height_px * scale

        # If image is taller than the entire usable area, scale down further
        if display_height_mm > settings.usable_height:
            scale = settings.usable_height / img_height_px
            display_height_mm = settings.usable_height
            display_width_mm = img_width_px * scale

        # Check if image fits on current page (add gap if not first on page)
        space_needed = display_height_mm
        if cursor_y > settings.margin_mm:
            space_needed += settings.gap_mm

        if cursor_y + space_needed > settings.height_mm - settings.margin_mm:
            # Start new page
            current_page += 1
            cursor_y = settings.margin_mm
        elif cursor_y > settings.margin_mm:
            # Add gap before this image (not the first on page)
            cursor_y += settings.gap_mm

        # Center horizontally
        x = settings.margin_mm + (settings.usable_width - display_width_mm) / 2

        placements.append(ImagePlacement(
            page_index=current_page,
            x_mm=x,
            y_mm=cursor_y,
            width_mm=display_width_mm,
            height_mm=display_height_mm,
            image_index=i,
        ))

        cursor_y += display_height_mm

    return placements


def get_page_settings(page_size: str = "a4", margin: float = 15, gap: float = 8) -> PageSettings:
    """Create PageSettings from user-facing parameters."""
    size_key = page_size.lower()
    if size_key not in PAGE_SIZES:
        raise ValueError(f"Unknown page size: {page_size}. Options: {list(PAGE_SIZES.keys())}")

    width, height = PAGE_SIZES[size_key]
    return PageSettings(
        width_mm=width,
        height_mm=height,
        margin_mm=margin,
        gap_mm=gap,
    )
