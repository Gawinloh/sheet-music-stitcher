# Sheet Music Stitcher — Implementation Steps

A local Python CLI tool that takes multiple screenshots of piano sheet music (one line each) and combines them into a clean, well-formatted PDF of the complete song.

## Tech Stack

- Python 3.10+
- Pillow (image manipulation)
- fpdf2 (PDF generation)
- numpy (pixel analysis for auto-crop)
- imagehash (duplicate detection)

---

## Step 1: Project Setup & Basic Pipeline

**Goal:** Get a minimal working tool that loads images and outputs a PDF.

**What to build:**

- Project structure: `main.py`, `requirements.txt`
- CLI entry point that accepts a folder path (or list of image files) and an output filename
- Sort images by filename (alphabetical/natural sort so `img2.png` comes before `img10.png`)
- Stack all images vertically into a single PDF using fpdf2
- No cropping, no layout logic — just raw images placed one after another on pages

**Acceptance criteria:**

- `python main.py ./screenshots/ -o output.pdf` produces a valid PDF with all images in filename order
- Images that overflow a page continue on the next page

**Tests:**

- Test natural sort ordering (`img1`, `img2`, `img10` sorted correctly)
- Test that output PDF is created and is a valid PDF file
- Test with a single image input
- Test with an empty folder (should error gracefully)
- Test with mixed file types in folder (should only pick up image files)

---

## Step 2: Auto-Crop & Background Normalization

**Goal:** Automatically remove surrounding whitespace/UI chrome and normalize to a clean white background.

**What to build:**

- `crop.py` module
- Convert image to grayscale
- Compute row-wise pixel variance to find top/bottom bounds of the staff (rows with musical content have high variance; blank margins have near-zero variance)
- Compute column-wise pixel variance for left/right bounds
- Add a small configurable padding around the detected bounding box
- Normalize background to pure white (threshold near-white pixels to 255)
- Integrate into the main pipeline so all images are auto-cropped before PDF assembly

**Acceptance criteria:**

- Screenshots with browser chrome, desktop backgrounds, or extra margins are cleanly cropped to just the music
- Output images have a consistent white background
- A `--no-crop` flag skips this step if needed

**Tests:**

- Test auto-crop on an image with known white margins (verify cropped dimensions are smaller)
- Test auto-crop on an image that's already tightly cropped (should not over-crop)
- Test background normalization (near-white pixels like 250,250,250 become 255,255,255)
- Test `--no-crop` flag bypasses cropping entirely
- Test with a synthetic image: white background + black rectangle (staff stand-in) + extra padding — verify the rectangle bounds are detected correctly

---

## Step 3: Adaptive Multi-Page Layout

**Goal:** Intelligently pack multiple systems onto pages with proper spacing.

**What to build:**

- `layout.py` module
- Accept a configurable page size (default A4 or Letter)
- Define page margins (top, bottom, left, right)
- Greedily place cropped images onto pages: measure each image's height, add it to the current page if it fits (with a minimum gap between systems), otherwise start a new page
- Center images horizontally within the page margins
- Scale images to fit page width if they're wider than the available area (maintain aspect ratio)

**Acceptance criteria:**

- Multiple systems fit on one page with consistent spacing
- No image is cut off between pages
- Images wider than the page are scaled down proportionally
- Configurable via flags: `--page-size`, `--margin`, `--gap`

**Tests:**

- Test that a tall image that exceeds page height triggers a new page (not cut off)
- Test that multiple short images are packed onto one page
- Test page break logic: given images of known heights + known page size, verify correct number of pages
- Test that wide images are scaled down (output image width ≤ page width minus margins)
- Test horizontal centering (image is placed equally from left and right margins)
- Test different page sizes produce different layouts

---

## Step 4: Title Page & Page Numbers

**Goal:** Add a professional title page and footer page numbers.

**What to build:**

- Extend `pdf_builder.py` (or the main pipeline)
- Optional title page with: song title (large, centered), composer/arranger (smaller, below title), optional date
- Page numbers in the footer of each page (excluding the title page)
- CLI flags: `--title`, `--composer`, `--date`

**Acceptance criteria:**

- `python main.py ./screenshots/ -o output.pdf --title "Moonlight Sonata" --composer "Beethoven"` produces a PDF with a title page followed by the music
- Page numbers appear on music pages but not the title page
- If no `--title` is provided, skip the title page entirely

**Tests:**

- Test with `--title` flag: output PDF has one extra page at the start
- Test without `--title` flag: no title page, music starts on page 1
- Test page count: N pages of music + 1 title page = N+1 total pages
- Test that page numbers start at 1 on the first music page (not the title page)
- Test title page content contains the provided title and composer strings

---

## Step 5: Duplicate Detection

**Goal:** Detect and warn about near-identical screenshots to avoid duplicating lines in the output.

**What to build:**

- `dedup.py` module
- Compute a perceptual hash (using `imagehash`) for each image after cropping
- Compare all pairs; if two images have a hash distance below a threshold, flag them as potential duplicates
- Default behavior: warn the user and skip the duplicate (keep the first occurrence)
- A `--keep-dupes` flag to disable this behavior

**Acceptance criteria:**

- If the user accidentally screenshots the same line twice, the tool warns: `"Skipping img_05.png (duplicate of img_03.png)"`
- Threshold is tunable (e.g., `--dedup-threshold 5`)
- Does not false-positive on lines that are musically similar but different (e.g., repeated sections with slight differences)

**Tests:**

- Test with two identical images: second one is flagged and skipped
- Test with two slightly different images (e.g., different JPEG compression of same source): still detected as duplicate
- Test with two genuinely different music lines: not flagged as duplicates
- Test `--keep-dupes` flag: duplicates are included without warning
- Test `--dedup-threshold` with a very low value (strict) and very high value (permissive)
- Test that the first occurrence is always kept (not the second)

---

## Step 6: Staff Alignment

**Goal:** Align all systems so the music starts at a consistent horizontal position across all lines.

**What to build:**

- `align.py` module
- For each cropped image, detect the left edge of the first staff line or barline (the leftmost significant vertical or horizontal feature)
- Determine the maximum left-offset across all images
- Pad images on the left so all systems start at the same x-position
- This ensures the output looks like a professionally typeset score where all systems are left-aligned

**Acceptance criteria:**

- All systems in the output PDF have their left edges aligned
- Images that were already well-aligned are not distorted
- A `--no-align` flag skips this step

**Tests:**

- Test with images that have different left offsets: output images all have the same left-edge position
- Test with images already aligned: no unnecessary padding added
- Test that alignment doesn't change image height (only width via padding)
- Test `--no-align` flag skips alignment
- Test with a synthetic image: staff lines starting at known x-position, verify detection accuracy

---

## Step 7: Manual Adjustment Mode (Optional Enhancement)

**Goal:** Let the user review and adjust auto-crop results when the detection isn't perfect.

**What to build:**

- A `--preview` flag that opens a simple matplotlib or Tkinter window
- Show each image with the detected crop bounding box overlaid
- User can accept (Enter), adjust (click to set new bounds), or skip the image
- After review, proceed with the confirmed crop regions

**Acceptance criteria:**

- `python main.py ./screenshots/ --preview` opens an interactive review before building the PDF
- User can override the auto-crop for any individual image
- Without `--preview`, the tool runs fully automatically (no GUI needed)

**Tests:**

- Test that `--preview` flag is recognized and doesn't crash
- Test that without `--preview`, no GUI window is opened (tool runs headlessly)
- Integration test: run full pipeline end-to-end with a set of test images and verify final PDF output

---

## Summary of CLI Interface (Final)

```
python main.py <input_folder_or_files> [options]

Options:
  -o, --output          Output PDF filename (default: output.pdf)
  --title               Song title for title page
  --composer            Composer/arranger name
  --date                Date string for title page
  --page-size           Page size: "a4" or "letter" (default: a4)
  --margin              Page margin in mm (default: 15)
  --gap                 Vertical gap between systems in mm (default: 8)
  --no-crop             Skip auto-cropping
  --no-align            Skip staff alignment
  --keep-dupes          Don't skip duplicate images
  --dedup-threshold     Hash distance threshold for duplicates (default: 5)
  --preview             Open interactive preview for manual crop adjustment
```

---

## Notes for Implementation

- Each step builds on the previous one — the tool is usable after every step.
- Keep modules loosely coupled: each step is its own file with a clear input/output contract (takes a list of PIL Images, returns a list of PIL Images).
- Write a brief docstring at the top of each module explaining what it does.
- Natural sort for filenames (so `img2` < `img10`) — use `natsort` or a simple regex-based sort.

## Testing Strategy

- Use `pytest` as the test framework. Add it to `requirements-dev.txt`.
- Tests go in a `tests/` folder, one test file per module (e.g., `tests/test_crop.py`).
- Use synthetic test images generated with Pillow in test fixtures (e.g., white rectangles with black lines to simulate staves). This avoids needing real screenshot files in the repo.
- Each step's tests should pass independently — run `pytest tests/test_<module>.py` to verify just that step.
- After each step, all previous tests must still pass (regression safety).
- Add a `conftest.py` with shared fixtures like `sample_image()`, `sample_staff_image()`, `tmp_output_dir()`.
