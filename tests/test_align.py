"""Tests for the staff alignment module."""

import numpy as np
from PIL import Image

from src.align import detect_left_edge, align_images


def make_image_with_left_edge(width=400, height=100, content_start=50):
    """Create an image with content starting at a specific x-position."""
    pixels = np.full((height, width, 3), 255, dtype=np.uint8)
    # Draw staff lines starting at content_start
    for y in range(20, 80, 12):
        pixels[y, content_start:width - 20] = 0
    return Image.fromarray(pixels)


class TestDetectLeftEdge:
    def test_detects_known_position(self):
        """Should detect content starting at the expected x-position."""
        img = make_image_with_left_edge(content_start=60)
        edge = detect_left_edge(img)
        assert edge == 60

    def test_content_at_edge(self):
        """Content starting at x=0 should return 0."""
        img = make_image_with_left_edge(content_start=0)
        edge = detect_left_edge(img)
        assert edge == 0

    def test_blank_image(self):
        """Blank image should return 0."""
        img = Image.new("RGB", (400, 100), (255, 255, 255))
        edge = detect_left_edge(img)
        assert edge == 0


class TestAlignImages:
    def test_different_offsets_aligned(self):
        """Images with different left offsets should all get the same start position."""
        img1 = make_image_with_left_edge(content_start=30)
        img2 = make_image_with_left_edge(content_start=60)
        img3 = make_image_with_left_edge(content_start=45)

        aligned = align_images([img1, img2, img3])

        # After alignment, all should have content starting at x=60 (the max)
        edges = [detect_left_edge(img) for img in aligned]
        assert all(e == 60 for e in edges)

    def test_already_aligned_no_change(self):
        """Images already aligned should not be padded."""
        img1 = make_image_with_left_edge(content_start=50)
        img2 = make_image_with_left_edge(content_start=50)

        aligned = align_images([img1, img2])

        # Width should remain the same (no padding added)
        assert aligned[0].width == img1.width
        assert aligned[1].width == img2.width

    def test_height_unchanged(self):
        """Alignment should not change image height."""
        img1 = make_image_with_left_edge(width=400, height=80, content_start=20)
        img2 = make_image_with_left_edge(width=400, height=80, content_start=50)

        aligned = align_images([img1, img2])

        assert aligned[0].height == 80
        assert aligned[1].height == 80

    def test_padding_increases_width(self):
        """Images that need padding should be wider."""
        img1 = make_image_with_left_edge(width=400, content_start=20)
        img2 = make_image_with_left_edge(width=400, content_start=60)

        aligned = align_images([img1, img2])

        # img1 needed 40px of padding, so it should be wider
        assert aligned[0].width == 400 + 40
        # img2 had the max offset, no padding needed
        assert aligned[1].width == 400

    def test_no_align_flag(self):
        """--no-align is handled at main.py level; verify align_images works on empty list."""
        aligned = align_images([])
        assert aligned == []

    def test_single_image(self):
        """Single image should pass through unchanged."""
        img = make_image_with_left_edge(content_start=30)
        aligned = align_images([img])
        # Single image: max_left = 30, its own edge = 30, no padding
        assert aligned[0].width == img.width
