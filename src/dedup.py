"""
Duplicate Detection.

Uses perceptual hashing to detect near-identical images and flag them
as duplicates. By default, duplicates are skipped (first occurrence kept).
"""

from dataclasses import dataclass
from typing import Optional

import imagehash
from PIL import Image


DEFAULT_THRESHOLD = 5


@dataclass
class DuplicateResult:
    """Result of duplicate detection for a single image."""
    index: int
    is_duplicate: bool
    duplicate_of: Optional[int] = None  # index of the original


def detect_duplicates(
    images: list[Image.Image],
    threshold: int = DEFAULT_THRESHOLD,
) -> list[DuplicateResult]:
    """
    Detect duplicate images using perceptual hashing.

    Compares each image against all previous images. If the hash distance
    is below the threshold, it's flagged as a duplicate of the first match.

    Returns a list of DuplicateResult, one per input image.
    """
    hashes: list[imagehash.ImageHash] = []
    results: list[DuplicateResult] = []

    for i, img in enumerate(images):
        h = imagehash.phash(img)
        duplicate_of = None

        for j, prev_hash in enumerate(hashes):
            if h - prev_hash <= threshold:
                duplicate_of = j
                break

        hashes.append(h)
        results.append(DuplicateResult(
            index=i,
            is_duplicate=duplicate_of is not None,
            duplicate_of=duplicate_of,
        ))

    return results


def filter_duplicates(
    images: list[Image.Image],
    names: list[str],
    threshold: int = DEFAULT_THRESHOLD,
    keep_dupes: bool = False,
) -> tuple[list[Image.Image], list[str]]:
    """
    Filter out duplicate images, printing warnings for skipped ones.

    Returns the filtered lists of (images, names).
    If keep_dupes is True, returns everything unchanged (no filtering).
    """
    if keep_dupes:
        return images, names

    results = detect_duplicates(images, threshold)

    filtered_images = []
    filtered_names = []

    for result, img, name in zip(results, images, names):
        if result.is_duplicate:
            original_name = names[result.duplicate_of]
            print(f"  Skipping {name} (duplicate of {original_name})")
        else:
            filtered_images.append(img)
            filtered_names.append(name)

    return filtered_images, filtered_names
