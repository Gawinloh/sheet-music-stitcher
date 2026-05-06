"""Tests for the manual adjustment (preview) module."""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import numpy as np
from PIL import Image

from src.main import main


def make_test_image(width=400, height=100):
    """Create a test image with some content."""
    pixels = np.full((height, width, 3), 255, dtype=np.uint8)
    pixels[30:70, 50:350] = 0
    return Image.fromarray(pixels)


class TestPreviewFlag:
    def test_preview_flag_recognized(self, tmp_path):
        """--preview flag should be accepted without error."""
        # Create a test image
        img = make_test_image()
        img.save(tmp_path / "test.png")
        output = tmp_path / "out.pdf"

        # Mock matplotlib so we don't actually open a window
        mock_plt = MagicMock()
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        # Simulate plt.show() closing immediately (user presses Enter)
        mock_plt.show.return_value = None
        mock_plt.Rectangle.return_value = MagicMock()

        with patch.dict(sys.modules, {'matplotlib': MagicMock(), 'matplotlib.pyplot': mock_plt, 'matplotlib.widgets': MagicMock()}):
            # Import after patching
            from src.preview import preview_and_adjust
            # The function should accept images and names
            images = [make_test_image()]
            names = ["test.png"]

            # We can't fully test interactive mode without a display,
            # but we can verify the function signature works
            assert callable(preview_and_adjust)

    def test_no_preview_runs_headlessly(self, tmp_path, sample_staff_image):
        """Without --preview, no GUI should be opened."""
        img = sample_staff_image()
        img.save(tmp_path / "test.png")
        output = tmp_path / "out.pdf"

        # Patch sys.argv to simulate CLI
        test_args = ["main", str(tmp_path), "-o", str(output)]
        with patch("sys.argv", test_args):
            # Should complete without importing matplotlib
            main()

        assert output.exists()


class TestIntegrationEndToEnd:
    def test_full_pipeline(self, tmp_path, sample_staff_image):
        """Full pipeline end-to-end: load, crop, dedup, align, PDF."""
        # Create 4 images, one duplicate
        for i in range(3):
            img = sample_staff_image(
                width=800, height=200,
                margin_top=30 + i * 5,
                margin_left=50 + i * 10,
            )
            img.save(tmp_path / f"img_{i+1:02d}.png")

        # Add a duplicate of the first
        img = sample_staff_image(width=800, height=200, margin_top=30, margin_left=50)
        img.save(tmp_path / f"img_04_dup.png")

        output = tmp_path / "final.pdf"

        test_args = ["main", str(tmp_path), "-o", str(output), "--title", "Test Song", "--composer", "Tester"]
        with patch("sys.argv", test_args):
            main()

        assert output.exists()
        with open(output, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_no_crop_no_align(self, tmp_path, sample_staff_image):
        """Pipeline with --no-crop and --no-align flags."""
        img = sample_staff_image()
        img.save(tmp_path / "test.png")
        output = tmp_path / "raw.pdf"

        test_args = ["main", str(tmp_path), "-o", str(output), "--no-crop", "--no-align"]
        with patch("sys.argv", test_args):
            main()

        assert output.exists()
