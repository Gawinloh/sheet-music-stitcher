"""Tests for the main CLI module."""

import subprocess
import sys
from pathlib import Path

from src.main import natural_sort_key, collect_images


class TestNaturalSort:
    def test_numeric_ordering(self, tmp_path):
        """img2 should come before img10."""
        names = ["img10.png", "img2.png", "img1.png"]
        paths = [tmp_path / n for n in names]
        for p in paths:
            p.touch()

        sorted_paths = sorted(paths, key=natural_sort_key)
        assert [p.name for p in sorted_paths] == ["img1.png", "img2.png", "img10.png"]

    def test_alphabetical_fallback(self, tmp_path):
        """Non-numeric names sort alphabetically."""
        names = ["chorus.png", "bridge.png", "verse.png"]
        paths = [tmp_path / n for n in names]
        for p in paths:
            p.touch()

        sorted_paths = sorted(paths, key=natural_sort_key)
        assert [p.name for p in sorted_paths] == ["bridge.png", "chorus.png", "verse.png"]

    def test_mixed_names(self, tmp_path):
        """Handles mix of numeric and non-numeric parts."""
        names = ["part2_line10.png", "part2_line2.png", "part1_line1.png"]
        paths = [tmp_path / n for n in names]
        for p in paths:
            p.touch()

        sorted_paths = sorted(paths, key=natural_sort_key)
        assert [p.name for p in sorted_paths] == [
            "part1_line1.png",
            "part2_line2.png",
            "part2_line10.png",
        ]


class TestCollectImages:
    def test_collects_from_folder(self, sample_images_dir):
        """Should find all image files in a folder."""
        folder = sample_images_dir(count=3)
        result = collect_images(folder)
        assert len(result) == 3

    def test_sorted_order(self, sample_images_dir):
        """Results should be naturally sorted."""
        folder = sample_images_dir(count=3)
        result = collect_images(folder)
        names = [p.name for p in result]
        assert names == ["img_01.png", "img_02.png", "img_03.png"]

    def test_single_file(self, tmp_path, sample_staff_image):
        """Should accept a single image file as input."""
        img_path = tmp_path / "single.png"
        sample_staff_image().save(img_path)
        result = collect_images(img_path)
        assert len(result) == 1
        assert result[0].name == "single.png"

    def test_empty_folder(self, tmp_path):
        """Should exit with error on empty folder."""
        import pytest
        with pytest.raises(SystemExit):
            collect_images(tmp_path)

    def test_ignores_non_image_files(self, tmp_path, sample_staff_image):
        """Should only pick up supported image extensions."""
        sample_staff_image().save(tmp_path / "music.png")
        (tmp_path / "notes.txt").write_text("not an image")
        (tmp_path / "data.csv").write_text("also not an image")

        result = collect_images(tmp_path)
        assert len(result) == 1
        assert result[0].name == "music.png"
