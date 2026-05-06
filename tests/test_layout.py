"""Tests for the adaptive multi-page layout module."""

from PIL import Image

from src.layout import compute_layout, get_page_settings, PageSettings


def make_image(width, height):
    """Helper to create a blank image of given pixel size."""
    return Image.new("RGB", (width, height), (255, 255, 255))


class TestComputeLayout:
    def test_multiple_short_images_one_page(self):
        """Short images should all fit on one page."""
        settings = get_page_settings("a4", margin=15, gap=8)
        # Each image: 800x100px. At A4 width (180mm usable), scale = 180/800 = 0.225
        # display_height = 100 * 0.225 = 22.5mm. 5 images + 4 gaps = 5*22.5 + 4*8 = 144.5mm
        # Usable height = 297 - 30 = 267mm. Should fit.
        images = [make_image(800, 100) for _ in range(5)]
        placements = compute_layout(images, settings)

        assert all(p.page_index == 0 for p in placements)

    def test_tall_image_triggers_new_page(self):
        """An image that won't fit should go on the next page."""
        settings = get_page_settings("a4", margin=15, gap=8)
        # First image takes most of the page
        # 800x4000px -> display_height = 4000 * (180/800) = 900mm -> capped to usable_height=267mm
        # Second image won't fit
        images = [make_image(800, 4000), make_image(800, 4000)]
        placements = compute_layout(images, settings)

        assert placements[0].page_index == 0
        assert placements[1].page_index == 1

    def test_page_break_count(self):
        """Given known image heights, verify correct number of pages."""
        settings = PageSettings(width_mm=210, height_mm=297, margin_mm=15, gap_mm=8)
        # Each image: 800x500px. scale = 180/800 = 0.225. display_height = 112.5mm
        # Page usable = 267mm.
        # Image 1: 112.5mm (cursor at 127.5mm)
        # Image 2: needs 8 + 112.5 = 120.5mm. cursor would be 248mm. Fits (< 282mm)
        # Image 3: needs 8 + 112.5 = 120.5mm. cursor would be 368.5mm. Doesn't fit (> 282mm)
        images = [make_image(800, 500) for _ in range(3)]
        placements = compute_layout(images, settings)

        assert placements[0].page_index == 0
        assert placements[1].page_index == 0
        assert placements[2].page_index == 1

    def test_wide_image_scaled_down(self):
        """Images wider than page should be scaled to fit."""
        settings = get_page_settings("a4", margin=15, gap=8)
        # Image is 2000px wide, usable is 180mm
        images = [make_image(2000, 200)]
        placements = compute_layout(images, settings)

        assert placements[0].width_mm <= settings.usable_width

    def test_horizontal_centering(self):
        """Image should be centered horizontally."""
        settings = get_page_settings("a4", margin=15, gap=8)
        # Narrow image that doesn't fill the width
        # 800x2000px -> height exceeds usable, so it scales down by height
        # scale = 267/2000 = 0.1335, width = 800*0.1335 = 106.8mm (< 180mm usable)
        images = [make_image(800, 2000)]
        placements = compute_layout(images, settings)

        p = placements[0]
        # Check centering: x should be margin + (usable_width - display_width) / 2
        expected_x = settings.margin_mm + (settings.usable_width - p.width_mm) / 2
        assert abs(p.x_mm - expected_x) < 0.01

    def test_different_page_sizes(self):
        """Different page sizes should produce different layouts."""
        images = [make_image(800, 500) for _ in range(5)]

        a4_settings = get_page_settings("a4", margin=15, gap=8)
        letter_settings = get_page_settings("letter", margin=15, gap=8)

        a4_placements = compute_layout(images, a4_settings)
        letter_placements = compute_layout(images, letter_settings)

        # A4 is taller (297mm) vs letter (279.4mm), so A4 might fit more per page
        a4_pages = max(p.page_index for p in a4_placements) + 1
        letter_pages = max(p.page_index for p in letter_placements) + 1

        # At minimum, placements should differ in position due to different page widths
        assert a4_placements[0].width_mm != letter_placements[0].width_mm

    def test_gap_between_images(self):
        """There should be a gap between images on the same page."""
        settings = PageSettings(width_mm=210, height_mm=297, margin_mm=15, gap_mm=10)
        images = [make_image(800, 100) for _ in range(3)]
        placements = compute_layout(images, settings)

        # Second image should start after first image's bottom + gap
        gap_actual = placements[1].y_mm - (placements[0].y_mm + placements[0].height_mm)
        assert abs(gap_actual - 10) < 0.01

    def test_no_gap_for_first_image(self):
        """First image on a page should start at the margin, no gap."""
        settings = get_page_settings("a4", margin=15, gap=8)
        images = [make_image(800, 100)]
        placements = compute_layout(images, settings)

        assert placements[0].y_mm == settings.margin_mm


class TestGetPageSettings:
    def test_a4(self):
        settings = get_page_settings("a4")
        assert settings.width_mm == 210
        assert settings.height_mm == 297

    def test_letter(self):
        settings = get_page_settings("letter")
        assert settings.width_mm == 215.9
        assert settings.height_mm == 279.4

    def test_invalid_size(self):
        import pytest
        with pytest.raises(ValueError):
            get_page_settings("tabloid")

    def test_custom_margin_and_gap(self):
        settings = get_page_settings("a4", margin=20, gap=12)
        assert settings.margin_mm == 20
        assert settings.gap_mm == 12
        assert settings.usable_width == 170  # 210 - 2*20
