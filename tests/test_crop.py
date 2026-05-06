"""Tests for the auto-crop and background normalization module."""

import numpy as np
from PIL import Image

from src.crop import normalize_background, detect_content_bounds, auto_crop, process_image


class TestNormalizeBackground:
    def test_near_white_becomes_white(self):
        """Pixels with all channels > threshold should become pure white."""
        # Create image with near-white background (250, 250, 250)
        img = Image.new("RGB", (100, 100), (250, 250, 250))
        result = normalize_background(img)
        pixels = np.array(result)
        assert np.all(pixels == 255)

    def test_dark_pixels_unchanged(self):
        """Dark pixels (content) should not be modified."""
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        result = normalize_background(img)
        pixels = np.array(result)
        assert np.all(pixels == 0)

    def test_mixed_image(self):
        """Image with both dark content and light background."""
        pixels = np.full((100, 100, 3), 245, dtype=np.uint8)
        # Add a dark region (simulating content)
        pixels[40:60, 20:80] = 0
        img = Image.fromarray(pixels)

        result = normalize_background(img)
        result_pixels = np.array(result)

        # Background should be white
        assert np.all(result_pixels[0, 0] == 255)
        # Content should still be black
        assert np.all(result_pixels[50, 50] == 0)


class TestDetectContentBounds:
    def test_content_in_center(self):
        """Should detect content region in the center of image."""
        # White image with black rectangle in center
        pixels = np.full((200, 400, 3), 255, dtype=np.uint8)
        pixels[50:150, 100:300] = 0
        img = Image.fromarray(pixels)

        top, bottom, left, right = detect_content_bounds(img)

        # Should find the black rectangle (within a small tolerance)
        assert top <= 50
        assert bottom >= 149
        assert left <= 100
        assert right >= 299

    def test_content_at_edges(self):
        """Should handle content that starts at image edges."""
        pixels = np.full((200, 400, 3), 255, dtype=np.uint8)
        pixels[0:50, 0:400] = 0  # Content at top, full width
        img = Image.fromarray(pixels)

        top, bottom, left, right = detect_content_bounds(img)

        assert top == 0
        assert bottom >= 49

    def test_blank_image(self):
        """Should return full image bounds for blank (all white) image."""
        img = Image.new("RGB", (400, 200), (255, 255, 255))
        top, bottom, left, right = detect_content_bounds(img)

        assert top == 0
        assert bottom == 200
        assert left == 0
        assert right == 400

    def test_staff_lines(self, sample_staff_image):
        """Should detect staff lines in synthetic staff image."""
        img = sample_staff_image(width=800, height=200, margin_top=40, margin_bottom=40)
        top, bottom, left, right = detect_content_bounds(img)

        # Content should be within the non-margin area
        assert top <= 60  # Should find content starting around row 40-60
        assert bottom >= 140  # Should find content ending around row 160


class TestAutoCrop:
    def test_removes_margins(self):
        """Cropped image should be smaller than original with margins."""
        pixels = np.full((200, 400, 3), 255, dtype=np.uint8)
        pixels[50:150, 100:300] = 0
        img = Image.fromarray(pixels)

        cropped = auto_crop(img, padding=5)

        assert cropped.width < img.width
        assert cropped.height < img.height

    def test_already_tight_crop(self):
        """Image with no margins should not be over-cropped."""
        # Create image where content fills the whole thing
        pixels = np.full((100, 200, 3), 128, dtype=np.uint8)
        img = Image.fromarray(pixels)

        cropped = auto_crop(img, padding=0)

        # Should be same size or very close (content fills entire image)
        assert cropped.width == img.width
        assert cropped.height == img.height

    def test_padding_applied(self):
        """Padding should add space around detected content."""
        pixels = np.full((200, 400, 3), 255, dtype=np.uint8)
        pixels[80:120, 150:250] = 0  # Small content region
        img = Image.fromarray(pixels)

        cropped_no_pad = auto_crop(img, padding=0)
        cropped_with_pad = auto_crop(img, padding=20)

        # Padded version should be larger
        assert cropped_with_pad.width > cropped_no_pad.width
        assert cropped_with_pad.height > cropped_no_pad.height


class TestProcessImage:
    def test_full_pipeline(self, sample_staff_image):
        """Full pipeline should normalize and crop."""
        img = sample_staff_image(width=800, height=200, margin_top=40, margin_bottom=40)
        result = process_image(img)

        # Should be cropped (smaller than original)
        assert result.height < img.height

    def test_no_crop_flag_bypass(self, sample_staff_image):
        """--no-crop is handled at main.py level, not here; just verify process_image works."""
        img = sample_staff_image()
        result = process_image(img)
        assert result.width > 0
        assert result.height > 0
