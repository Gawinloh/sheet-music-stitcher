"""
Manual Adjustment Mode (Preview).

Opens a matplotlib window for each image showing the detected crop bounding box.
User can accept, adjust, or skip each image before the final PDF is built.
"""

from PIL import Image
import numpy as np

from src.crop import detect_content_bounds, normalize_background, DEFAULT_PADDING, VARIANCE_THRESHOLD


def preview_and_adjust(
    images: list[Image.Image],
    names: list[str],
    padding: int = DEFAULT_PADDING,
    variance_threshold: float = VARIANCE_THRESHOLD,
) -> list[Image.Image]:
    """
    Show each image with its detected crop region and let user adjust.

    Controls:
    - Enter/click 'Accept': use detected crop
    - 's' key: skip (keep original, no crop)
    - Click and drag: manually set crop region

    Returns list of cropped (or skipped) images.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.widgets import RectangleSelector
    except ImportError:
        print("Error: matplotlib is required for --preview mode.")
        print("Install it with: pip install matplotlib")
        raise SystemExit(1)

    results = []

    for i, (img, name) in enumerate(zip(images, names)):
        # Normalize background first
        normalized = normalize_background(img)
        img_array = np.array(normalized)

        # Detect bounds
        top, bottom, left, right = detect_content_bounds(normalized, variance_threshold)

        # Apply padding for display
        display_top = max(0, top - padding)
        display_bottom = min(img.height, bottom + padding)
        display_left = max(0, left - padding)
        display_right = min(img.width, right + padding)

        # State for this image
        state = {
            "action": "accept",
            "crop_box": (display_left, display_top, display_right, display_bottom),
        }

        fig, ax = plt.subplots(1, 1, figsize=(12, 4))
        ax.imshow(img_array)
        ax.set_title(f"[{i+1}/{len(images)}] {name}\n"
                     f"Enter=Accept crop | S=Skip (no crop) | Click+Drag=Manual crop")

        # Draw detected crop rectangle
        rect = plt.Rectangle(
            (display_left, display_top),
            display_right - display_left,
            display_bottom - display_top,
            linewidth=2, edgecolor='red', facecolor='none', linestyle='--'
        )
        ax.add_patch(rect)

        def on_key(event):
            if event.key == 'enter':
                state["action"] = "accept"
                plt.close(fig)
            elif event.key == 's':
                state["action"] = "skip"
                plt.close(fig)

        def on_select(eclick, erelease):
            x1, y1 = int(eclick.xdata), int(eclick.ydata)
            x2, y2 = int(erelease.xdata), int(erelease.ydata)
            # Ensure correct ordering
            left_sel = min(x1, x2)
            right_sel = max(x1, x2)
            top_sel = min(y1, y2)
            bottom_sel = max(y1, y2)
            state["crop_box"] = (left_sel, top_sel, right_sel, bottom_sel)
            state["action"] = "accept"
            # Update rectangle display
            rect.set_xy((left_sel, top_sel))
            rect.set_width(right_sel - left_sel)
            rect.set_height(bottom_sel - top_sel)
            rect.set_linestyle('-')
            rect.set_edgecolor('green')
            fig.canvas.draw()

        # Enable rectangle selector for manual crop
        selector = RectangleSelector(
            ax, on_select,
            useblit=True,
            button=[1],
            interactive=True,
        )

        fig.canvas.mpl_connect('key_press_event', on_key)
        plt.tight_layout()
        plt.show()

        # Process based on action
        if state["action"] == "skip":
            print(f"  {name}: skipped (keeping original)")
            results.append(normalized)
        else:
            l, t, r, b = state["crop_box"]
            cropped = normalized.crop((l, t, r, b))
            print(f"  {name}: cropped to ({l}, {t}, {r}, {b})")
            results.append(cropped)

    return results
