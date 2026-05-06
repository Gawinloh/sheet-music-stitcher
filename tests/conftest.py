import pytest
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def sample_image():
    """Create a simple white image (simulates a blank screenshot)."""
    def _make(width=800, height=200, color=(255, 255, 255)):
        return Image.new("RGB", (width, height), color)
    return _make


@pytest.fixture
def sample_staff_image():
    """
    Create a synthetic staff image: white background with 5 horizontal black lines.
    Simulates a single system of sheet music for testing crop/alignment logic.
    """
    def _make(width=800, height=200, margin_top=40, margin_bottom=40, margin_left=60, margin_right=60):
        img = Image.new("RGB", (width, height), (255, 255, 255))
        pixels = np.array(img)

        # Draw 5 staff lines evenly spaced in the content area
        content_top = margin_top
        content_bottom = height - margin_bottom
        staff_height = content_bottom - content_top
        line_spacing = staff_height // 6

        for i in range(1, 6):
            y = content_top + i * line_spacing
            pixels[y, margin_left:width - margin_right] = (0, 0, 0)

        return Image.fromarray(pixels)
    return _make


@pytest.fixture
def sample_images_dir(tmp_path, sample_staff_image):
    """Create a temp directory with numbered sample images."""
    def _make(count=3):
        for i in range(1, count + 1):
            img = sample_staff_image()
            img.save(tmp_path / f"img_{i:02d}.png")
        return tmp_path
    return _make
