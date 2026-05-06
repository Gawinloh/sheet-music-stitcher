"""Tests for the PDF builder module."""

from pathlib import Path

from fpdf import FPDF
from PIL import Image

from src.layout import get_page_settings
from src.pdf_builder import build_pdf, TitleInfo


def make_image(width, height):
    return Image.new("RGB", (width, height), (255, 255, 255))


def count_pdf_pages(path: Path) -> int:
    """Count pages in a PDF by reading the file with fpdf2's parser isn't easy,
    so we use a simple regex approach on the raw bytes."""
    import re
    content = path.read_bytes()
    # Count page objects in PDF (each /Type /Page that isn't /Pages)
    pages = re.findall(rb"/Type\s*/Page(?!s)", content)
    return len(pages)


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
        assert count_pdf_pages(output) == 1

    def test_tall_image_triggers_new_page(self, tmp_path):
        """An image that won't fit should go on the next page."""
        images = [make_image(800, 2000), make_image(800, 2000)]
        output = tmp_path / "overflow_output.pdf"

        build_pdf(images, output)
        assert output.exists()
        assert count_pdf_pages(output) == 2


class TestTitlePage:
    def test_title_adds_extra_page(self, tmp_path):
        """With --title, output should have one extra page."""
        images = [make_image(800, 100) for _ in range(3)]
        output_no_title = tmp_path / "no_title.pdf"
        output_with_title = tmp_path / "with_title.pdf"

        build_pdf(images, output_no_title)
        build_pdf(images, output_with_title, title_info=TitleInfo(title="Test Song"))

        pages_without = count_pdf_pages(output_no_title)
        pages_with = count_pdf_pages(output_with_title)
        assert pages_with == pages_without + 1

    def test_no_title_no_extra_page(self, tmp_path):
        """Without --title, no title page is added."""
        images = [make_image(800, 100) for _ in range(3)]
        output = tmp_path / "no_title.pdf"

        build_pdf(images, output, title_info=None)

        assert count_pdf_pages(output) == 1

    def test_page_count_with_title(self, tmp_path):
        """N music pages + 1 title page = N+1 total pages."""
        # Two tall images = 2 music pages
        images = [make_image(800, 2000), make_image(800, 2000)]
        output = tmp_path / "titled.pdf"

        build_pdf(images, output, title_info=TitleInfo(title="My Song"))

        # 2 music pages + 1 title = 3
        assert count_pdf_pages(output) == 3

    def test_title_page_with_all_fields(self, tmp_path):
        """Should not crash with all title fields provided."""
        images = [make_image(800, 200)]
        output = tmp_path / "full_title.pdf"

        title_info = TitleInfo(
            title="Moonlight Sonata",
            composer="Beethoven",
            date="2024",
        )
        build_pdf(images, output, title_info=title_info)

        assert output.exists()
        assert count_pdf_pages(output) == 2  # title + 1 music page

    def test_title_page_without_optional_fields(self, tmp_path):
        """Should work with just a title, no composer or date."""
        images = [make_image(800, 200)]
        output = tmp_path / "title_only.pdf"

        build_pdf(images, output, title_info=TitleInfo(title="Simple Song"))

        assert output.exists()
        assert count_pdf_pages(output) == 2  # title + 1 music page
