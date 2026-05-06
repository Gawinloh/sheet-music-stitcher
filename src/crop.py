"""
Auto-Crop & Background Normalization.

Detects the bounding box of sheet music content in a screenshot by analyzing
row-wise and column-wise pixel variance, then crops to that region and
normalizes the background to pure white.
"""

from PIL import Image
import numpy as np


# Pixels with all channels above this value are considered "background"
BG_THRESHOLD = 240

# Minimum variance for a row/column to be considered "content"
VARIANCE_THRESHOLD = 50

# Default padding around detected content (pixels)
DEFAULT_PADDING = 10


def normalize_background(img: Image.Image, threshold: int = BG_THRESHOLD) -> Image.Image:
    """
    Normalize near-white pixels to pure white.

    Any pixel where all RGB channels are above the threshold is set to (255, 255, 255).
    """
    pixels = np.array(img)

    # Find pixels where all channels exceed threshold
    mask = np.all(pixels > threshold, axis=2)
    pixels[mask] = 255

    return Image.fromarray(pixels)


def detect_content_bounds(img: Image.Image, variance_threshold: float = VARIANCE_THRESHOLD) -> tuple[int, int, int, int]:
    """
    Detect the bounding box of content using pixel variance analysis.

    Returns (top, bottom, left, right) as pixel coordinates.

    - Rows with high variance contain content (staff lines, notes, etc.)
    - Rows with low variance are blank margins
    - Same logic applies to columns
    """
    grayscale = np.array(img.convert("L"), dtype=np.float64)

    # Row-wise variance (for top/bottom bounds)
    row_variance = np.var(grayscale, axis=1)

    # Column-wise variance (for left/right bounds)
    col_variance = np.var(grayscale, axis=0)

    # Find rows with content
    content_rows = np.where(row_variance > variance_threshold)[0]
    if len(content_rows) == 0:
        # No content detected — return full image bounds
        return 0, img.height, 0, img.width

    top = int(content_rows[0])
    bottom = int(content_rows[-1])

    # Find columns with content
    content_cols = np.where(col_variance > variance_threshold)[0]
    if len(content_cols) == 0:
        return top, bottom, 0, img.width

    left = int(content_cols[0])
    right = int(content_cols[-1])

    return top, bottom, left, right


def auto_crop(img: Image.Image, padding: int = DEFAULT_PADDING, variance_threshold: float = VARIANCE_THRESHOLD) -> Image.Image:
    """
    Auto-crop an image to its content region with padding.

    1. Detect content bounding box via variance analysis
    2. Add padding around the detected bounds
    3. Crop to that region
    """
    top, bottom, left, right = detect_content_bounds(img, variance_threshold)

    # Apply padding (clamped to image bounds)
    top = max(0, top - padding)
    bottom = min(img.height, bottom + padding)
    left = max(0, left - padding)
    right = min(img.width, right + padding)

    return img.crop((left, top, right, bottom))


def process_image(img: Image.Image, padding: int = DEFAULT_PADDING, variance_threshold: float = VARIANCE_THRESHOLD) -> Image.Image:
    """
    Full crop pipeline: normalize background, then auto-crop.
    """
    img = normalize_background(img)
    img = auto_crop(img, padding=padding, variance_threshold=variance_threshold)
    return img
