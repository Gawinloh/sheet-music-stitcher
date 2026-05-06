# Sheet Music Stitcher

A lightweight Python CLI tool that combines multiple screenshots of piano sheet music into a single, clean PDF.

Each screenshot contains one line (system) of music. The tool crops, cleans, deduplicates, aligns, and assembles them into a professional-looking score.

## Setup

```bash
pip install -r requirements.txt
```

For interactive preview mode (optional):

```bash
pip install matplotlib
```

## Usage

```bash
python -m src.main <input_folder> [options]
```

### Examples

Basic — just combine screenshots into a PDF:

```bash
python -m src.main ./screenshots/ -o output.pdf
```

With a title page:

```bash
python -m src.main ./screenshots/ -o output.pdf --title "Moonlight Sonata" --composer "Beethoven" --date "2026"
```

Skip auto-processing (raw screenshots, no crop/align):

```bash
python -m src.main ./screenshots/ -o output.pdf --no-crop --no-align
```

Interactive preview to manually adjust crop regions:

```bash
python -m src.main ./screenshots/ -o output.pdf --preview
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output PDF filename | `output.pdf` |
| `--title` | Song title (adds a title page) | — |
| `--composer` | Composer/arranger name | — |
| `--date` | Date shown on title page | — |
| `--page-size` | Page size: `a4` or `letter` | `a4` |
| `--margin` | Page margin in mm | `15` |
| `--gap` | Vertical gap between systems in mm | `8` |
| `--no-crop` | Skip auto-cropping | — |
| `--no-align` | Skip staff alignment | — |
| `--keep-dupes` | Don't skip duplicate images | — |
| `--dedup-threshold` | Hash distance for duplicate detection | `5` |
| `--preview` | Interactive crop adjustment (requires matplotlib) | — |

## How It Works

1. **Load & sort** — Collects images from the input folder, sorted naturally by filename (`img2` before `img10`).
2. **Auto-crop** — Detects staff content via pixel variance analysis and removes surrounding whitespace/UI chrome. Normalizes background to pure white.
3. **Duplicate detection** — Uses perceptual hashing to skip near-identical screenshots.
4. **Staff alignment** — Detects the left edge of each system and pads so all systems start at the same horizontal position.
5. **Adaptive layout** — Packs systems onto pages with consistent spacing, starting a new page when one is full.
6. **PDF output** — Assembles the final PDF with optional title page and page numbers.

## Running Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Project Structure

```
src/
├── main.py         CLI entry point
├── crop.py         Auto-crop & background normalization
├── dedup.py        Duplicate detection
├── align.py        Staff alignment
├── layout.py       Adaptive multi-page layout
├── pdf_builder.py  PDF assembly, title page, page numbers
└── preview.py      Interactive manual crop adjustment
```
