"""
Staff Alignment.

Detects the left edge of musical content in each image and pads them
so all systems start at a consistent horizontal position.
"""

import numpy as np
from PIL import Image


# Minimum column variance to be considered "content"
COLUMN_VARIANCE_THRESHOLD = 50


def detect_left_edge(img: Image.Image, variance_threshold: float = COLUMN_VARIANCE_THRESHOLD) -> int:
    """
    Detect the x-position of the leftmost content in the image.

    Uses column-wise pixel variance on grayscale to find where content begins.
    Returns the x-coordinate of the first column with significant content.
    """
    grayscale = np.array(img.convert("L"), dtype=np.float64)
    col_variance = np.var(grayscale, axis=0)

    content_cols = np.where(col_variance > variance_threshold)[0]
    if len(content_cols) == 0:
        return 0

    return int(content_cols[0])


def align_images(images: list[Image.Image], variance_threshold: float = COLUMN_VARIANCE_THRESHOLD) -> list[Image.Image]:
    """
    Align all images so their content starts at the same horizontal position.

    1. Detect the left edge of content in each image
    2. Find the maximum left offset (the image with content starting furthest right)
    3. Pad all other images on the left to match

    This ensures all systems appear left-aligned in the final output.
    """
    if not images:
        return images

    # Detect left edges
    left_edges = [detect_left_edge(img, variance_threshold) for img in images]

    # Find the maximum left edge — all images will be padded to match this
    max_left = max(left_edges)

    if max_left == 0:
        return images

    aligned = []
    for img, left_edge in zip(images, left_edges):
        padding_needed = max_left - left_edge

        if padding_needed == 0:
            aligned.append(img)
        else:
            # Create new image with white padding on the left
            new_width = img.width + padding_needed
            new_img = Image.new("RGB", (new_width, img.height), (255, 255, 255))
            new_img.paste(img, (padding_needed, 0))
            aligned.append(new_img)

    return aligned
