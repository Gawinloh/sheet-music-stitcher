"""Tests for the PDF builder module."""

from pathlib import Path

from src.pdf_builder import build_pdf


class TestBuildPdf:
    def test_creates_valid_pdf(self, tmp_path, sample_images_dir):
        """Output should be a valid PDF file."""
        folder = sample_images_dir(count=3)
        image_paths = sorted(folder.glob("*.png"))
        output = tmp_path / "test_output.pdf"

        build_pdf(image_paths, output)

        assert output.exists()
        # PDF files start with %PDF
        with open(output, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_single_image(self, tmp_path, sample_staff_image):
        """Should work with a single image."""
        img_path = tmp_path / "single.png"
        sample_staff_image().save(img_path)
        output = tmp_path / "single_output.pdf"

        build_pdf([img_path], output)

        assert output.exists()
        with open(output, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_multiple_images_fit_one_page(self, tmp_path, sample_staff_image):
        """Short images should all fit on one page."""
        # Create small images (200px height ~ about 15mm at page scale)
        image_paths = []
        for i in range(3):
            p = tmp_path / f"img_{i}.png"
            sample_staff_image(height=100).save(p)
            image_paths.append(p)

        output = tmp_path / "multi_output.pdf"
        build_pdf(image_paths, output)

        assert output.exists()

    def test_tall_image_triggers_new_page(self, tmp_path, sample_image):
        """An image that won't fit should go on the next page."""
        image_paths = []

        # First image: takes up most of the page
        p1 = tmp_path / "img_1.png"
        sample_image(width=800, height=2000).save(p1)
        image_paths.append(p1)

        # Second image: won't fit on same page
        p2 = tmp_path / "img_2.png"
        sample_image(width=800, height=2000).save(p2)
        image_paths.append(p2)

        output = tmp_path / "overflow_output.pdf"
        build_pdf(image_paths, output)

        assert output.exists()
