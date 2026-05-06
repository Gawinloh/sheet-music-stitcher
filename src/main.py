"""
Sheet Music Stitcher — CLI entry point.

Takes a folder of sheet music screenshot images and combines them into a single PDF.
"""

import argparse
import re
import sys
from pathlib import Path

from src.pdf_builder import build_pdf


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def natural_sort_key(path: Path):
    """Sort key that handles numbers naturally (img2 < img10)."""
    parts = re.split(r"(\d+)", path.name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def collect_images(input_path: Path) -> list[Path]:
    """Collect and sort image files from a folder or file list."""
    if input_path.is_dir():
        files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    elif input_path.is_file():
        if input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files = [input_path]
        else:
            print(f"Error: {input_path} is not a supported image file.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"Error: No image files found in {input_path}.", file=sys.stderr)
        sys.exit(1)

    return sorted(files, key=natural_sort_key)


def main():
    parser = argparse.ArgumentParser(
        description="Combine sheet music screenshots into a single PDF."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Folder containing screenshot images, or a single image file.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output.pdf"),
        help="Output PDF filename (default: output.pdf)",
    )

    args = parser.parse_args()

    image_paths = collect_images(args.input)
    print(f"Found {len(image_paths)} image(s):")
    for p in image_paths:
        print(f"  {p.name}")

    build_pdf(image_paths, args.output)
    print(f"\nDone! Output saved to: {args.output}")


if __name__ == "__main__":
    main()
