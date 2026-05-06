"""Tests for the duplicate detection module."""

import numpy as np
from PIL import Image

from src.dedup import detect_duplicates, filter_duplicates


def make_staff_image(seed=0, width=400, height=100):
    """Create a synthetic staff image with some variation based on seed."""
    rng = np.random.RandomState(seed)
    pixels = np.full((height, width, 3), 255, dtype=np.uint8)
    # Draw staff lines
    for y in range(20, 80, 12):
        pixels[y, 30:width - 30] = 0
    # Add some unique "notes" based on seed
    for _ in range(5):
        x = rng.randint(50, width - 50)
        y = rng.randint(20, 75)
        pixels[y - 3:y + 3, x - 3:x + 3] = 0
    return Image.fromarray(pixels)


class TestDetectDuplicates:
    def test_identical_images_detected(self):
        """Two identical images should be flagged as duplicates."""
        img = make_staff_image(seed=0)
        images = [img, img.copy()]
        results = detect_duplicates(images, threshold=5)

        assert results[0].is_duplicate is False
        assert results[1].is_duplicate is True
        assert results[1].duplicate_of == 0

    def test_slightly_different_compression(self):
        """Same image with minor noise should still be detected."""
        img1 = make_staff_image(seed=0)
        # Add tiny noise to simulate JPEG compression artifacts
        pixels = np.array(img1)
        noise = np.random.RandomState(99).randint(-2, 3, pixels.shape, dtype=np.int16)
        pixels = np.clip(pixels.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img2 = Image.fromarray(pixels)

        images = [img1, img2]
        results = detect_duplicates(images, threshold=5)

        assert results[1].is_duplicate is True
        assert results[1].duplicate_of == 0

    def test_different_images_not_flagged(self):
        """Genuinely different images should not be flagged."""
        img1 = make_staff_image(seed=0)
        img2 = make_staff_image(seed=42)

        images = [img1, img2]
        results = detect_duplicates(images, threshold=5)

        assert results[0].is_duplicate is False
        assert results[1].is_duplicate is False

    def test_first_occurrence_kept(self):
        """The first occurrence should never be marked as duplicate."""
        img = make_staff_image(seed=0)
        images = [img, img.copy(), img.copy()]
        results = detect_duplicates(images, threshold=5)

        assert results[0].is_duplicate is False
        assert results[1].is_duplicate is True
        assert results[1].duplicate_of == 0
        assert results[2].is_duplicate is True
        assert results[2].duplicate_of == 0

    def test_strict_threshold(self):
        """Very low threshold should be stricter about matches."""
        img1 = make_staff_image(seed=0)
        # Add moderate noise
        pixels = np.array(img1)
        noise = np.random.RandomState(99).randint(-10, 11, pixels.shape, dtype=np.int16)
        pixels = np.clip(pixels.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img2 = Image.fromarray(pixels)

        images = [img1, img2]
        # With threshold=0, even small differences may not match
        results_strict = detect_duplicates(images, threshold=0)
        # With threshold=10, should still match
        results_permissive = detect_duplicates(images, threshold=10)

        # Permissive should detect as duplicate
        assert results_permissive[1].is_duplicate is True


class TestFilterDuplicates:
    def test_duplicates_removed(self):
        """Duplicate images should be filtered out."""
        img = make_staff_image(seed=0)
        images = [img, img.copy(), make_staff_image(seed=42)]
        names = ["img_01.png", "img_02.png", "img_03.png"]

        filtered_imgs, filtered_names = filter_duplicates(images, names, threshold=5)

        assert len(filtered_imgs) == 2
        assert filtered_names == ["img_01.png", "img_03.png"]

    def test_keep_dupes_flag(self):
        """With keep_dupes=True, nothing should be removed."""
        img = make_staff_image(seed=0)
        images = [img, img.copy(), img.copy()]
        names = ["a.png", "b.png", "c.png"]

        filtered_imgs, filtered_names = filter_duplicates(
            images, names, threshold=5, keep_dupes=True
        )

        assert len(filtered_imgs) == 3
        assert filtered_names == ["a.png", "b.png", "c.png"]

    def test_no_duplicates(self):
        """All unique images should pass through unchanged."""
        images = [make_staff_image(seed=i) for i in range(4)]
        names = [f"img_{i}.png" for i in range(4)]

        filtered_imgs, filtered_names = filter_duplicates(images, names, threshold=5)

        assert len(filtered_imgs) == 4
        assert filtered_names == names
