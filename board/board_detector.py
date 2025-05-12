# file: bg_subtract_detector.py
import statistics
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple


def detect_tiles_by_bg(
    bg_path: str | Path,
    mixed_path: str | Path,
    diff_thresh: int = 25,  # 0–255 – smaller = more sensitive
    min_area: int = 400,  # filter noise blobs
    max_area: int = 80_000,  # filter huge blobs (e.g. a full row)
    close_iters: int = 2,  # dilate/erode passes to merge borders
) -> List[Tuple[int, int, int, int]]:
    bg = cv2.imread(str(bg_path))
    mixed = cv2.imread(str(mixed_path))
    if bg is None or mixed is None:
        raise FileNotFoundError("Could not read one of the images.")
    if bg.shape != mixed.shape:
        raise ValueError("Background and mixed image differ in size!")

    # 1 ▸ absolute per-pixel difference in grayscale
    diff = cv2.absdiff(
        cv2.cvtColor(mixed, cv2.COLOR_BGR2GRAY), cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    )

    # 2 ▸ threshold: anything that changed ≥ diff_thresh is 'tile'
    _, mask = cv2.threshold(diff, diff_thresh, 255, cv2.THRESH_BINARY)

    # 3 ▸ thicken slightly so thin borders become solid blobs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.dilate(mask, kernel, close_iters)
    mask = cv2.erode(mask, kernel, close_iters)

    # 4 ▸ connected components → bounding boxes
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[Tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if min_area <= area <= max_area:
            boxes.append((x, y, w, h))

    # 5 ▸ raw filtering into `boxes` …
    boxes: List[Tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if min_area <= area <= max_area:
            boxes.append((x, y, w, h))

    if not boxes:
        return []

    # ── 6. snake‐order sort ────────────────────────────────────────────────

    # 6.1 compute a y‐threshold = ~half the typical tile height
    heights = [h for (_, _, _, h) in boxes]
    median_h = statistics.median(heights)
    row_thresh = median_h * 0.5

    # 6.2 cluster into rows by y
    boxes_by_y = sorted(boxes, key=lambda b: b[1])
    rows: List[List[Tuple[int, int, int, int]]] = []
    current_row: List[Tuple[int, int, int, int]] = []
    last_y = None

    for b in boxes_by_y:
        x, y, w, h = b
        if last_y is None or abs(y - last_y) <= row_thresh:
            current_row.append(b)
            if last_y is None:
                last_y = y
            else:
                # gradually adjust last_y to the average y of the row
                last_y = (last_y + y) / 2
        else:
            rows.append(current_row)
            current_row = [b]
            last_y = y

    if current_row:
        rows.append(current_row)

    # 6.3 sort each row alternatingly, then flatten
    snake_order: List[Tuple[int, int, int, int]] = []
    for i, row in enumerate(rows):
        left_to_right = i % 2 == 0
        sorted_row = sorted(row, key=lambda b: b[0], reverse=not left_to_right)
        snake_order.extend(sorted_row)

    return snake_order


# ---------------------------------------------------------------------------
# quick demo
if __name__ == "__main__":
    BG = "assets/blank_board.png"
    MIXED = "assets/board_with_tiles.png"

    tiles = detect_tiles_by_bg(BG, MIXED)
    print(f"Detected {len(tiles)} tiles:")
    for i, (x, y, w, h) in enumerate(tiles):
        print(f"{i:2d}: (x={x}, y={y})  {w}×{h}")
