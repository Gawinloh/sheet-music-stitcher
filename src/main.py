"""
Sheet Music Stitcher — CLI entry point.

Takes a folder of sheet music screenshot images and combines them into a single PDF.
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image

from src.crop import process_image
from src.dedup import filter_duplicates
from src.layout import get_page_settings
from src.pdf_builder import build_pdf, TitleInfo


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
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="Skip auto-cropping and background normalization.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Song title (adds a title page)",
    )
    parser.add_argument(
        "--composer",
        type=str,
        default=None,
        help="Composer/arranger name (shown on title page)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date string (shown on title page)",
    )
    parser.add_argument(
        "--keep-dupes",
        action="store_true",
        help="Don't skip duplicate images.",
    )
    parser.add_argument(
        "--dedup-threshold",
        type=int,
        default=5,
        help="Hash distance threshold for duplicates (default: 5)",
    )
    parser.add_argument(
        "--page-size",
        type=str,
        default="a4",
        choices=["a4", "letter"],
        help="Page size (default: a4)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=15,
        help="Page margin in mm (default: 15)",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=8,
        help="Vertical gap between systems in mm (default: 8)",
    )

    args = parser.parse_args()

    image_paths = collect_images(args.input)
    print(f"Found {len(image_paths)} image(s):")
    for p in image_paths:
        print(f"  {p.name}")

    # Load and optionally process images
    images = []
    for p in image_paths:
        img = Image.open(p).convert("RGB")
        if not args.no_crop:
            img = process_image(img)
        images.append(img)

    if not args.no_crop:
        print("Auto-cropped and normalized backgrounds.")

    # Duplicate detection
    names = [p.name for p in image_paths]
    images, names = filter_duplicates(
        images, names,
        threshold=args.dedup_threshold,
        keep_dupes=args.keep_dupes,
    )

    if len(images) == 0:
        print("Error: No images remaining after duplicate removal.", file=sys.stderr)
        sys.exit(1)

    settings = get_page_settings(
        page_size=args.page_size,
        margin=args.margin,
        gap=args.gap,
    )

    # Build title info if --title provided
    title_info = None
    if args.title:
        title_info = TitleInfo(
            title=args.title,
            composer=args.composer,
            date=args.date,
        )

    build_pdf(images, args.output, settings=settings, title_info=title_info)
    print(f"\nDone! Output saved to: {args.output}")


if __name__ == "__main__":
    main()
