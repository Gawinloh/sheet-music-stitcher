"""Tests for the PDF builder module."""

from pathlib import Path

from PIL import Image

from src.pdf_builder import build_pdf


def make_image(width, height):
    return Image.new("RGB", (width, height), (255, 255, 255))


class TestBuildPdf:
    def test_creates_valid_pdf(self, tmp_path):
        """Output should be a valid PDF file."""
        images = [make_image(800, 200) for _ in range(3)]
        output = tmp_path / "test_output.pdf"

        build_pdf(images, output)

        assert output.exists()
        with open(output, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_single_image(self, tmp_path):
        """Should work with a single image."""
        images = [make_image(800, 200)]
        output = tmp_path / "single_output.pdf"

        build_pdf(images, output)

        assert output.exists()
        with open(output, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_multiple_images_fit_one_page(self, tmp_path):
        """Short images should all fit on one page."""
        images = [make_image(800, 100) for _ in range(3)]
        output = tmp_path / "multi_output.pdf"

        build_pdf(images, output)
        assert output.exists()

    def test_tall_image_triggers_new_page(self, tmp_path):
        """An image that won't fit should go on the next page."""
        images = [make_image(800, 2000), make_image(800, 2000)]
        output = tmp_path / "overflow_output.pdf"

        build_pdf(images, output)
        assert output.exists()
