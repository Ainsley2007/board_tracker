# file: bg_subtract_detector.py
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple


def detect_tiles_by_bg(
    bg_path:   str | Path,
    mixed_path: str | Path,
    diff_thresh: int = 25,          # 0–255 – smaller = more sensitive
    min_area:   int = 400,          # filter noise blobs
    max_area:   int = 80_000,       # filter huge blobs (e.g. a full row)
    close_iters: int = 2,           # dilate/erode passes to merge borders
) -> List[Tuple[int, int, int, int]]:
    """
    Subtract the pristine 1600×1600 background from the board-with-tiles image
    and return a list of bounding-box tuples (x, y, w, h) for every tile.

    Requirements:
    • both images have identical resolution & alignment
    • tiles are the *only* new pixels (margin around each tile is unchanged)
    """
    bg     = cv2.imread(str(bg_path))
    mixed  = cv2.imread(str(mixed_path))
    if bg is None or mixed is None:
        raise FileNotFoundError("Could not read one of the images.")
    if bg.shape != mixed.shape:
        raise ValueError("Background and mixed image differ in size!")

    # 1 ▸ absolute per-pixel difference in grayscale
    diff = cv2.absdiff(
        cv2.cvtColor(mixed, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(bg,    cv2.COLOR_BGR2GRAY)
    )

    # 2 ▸ threshold: anything that changed ≥ diff_thresh is 'tile'
    _, mask = cv2.threshold(diff, diff_thresh, 255, cv2.THRESH_BINARY)

    # 3 ▸ thicken slightly so thin borders become solid blobs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask   = cv2.dilate(mask, kernel, close_iters)
    mask   = cv2.erode(mask,  kernel, close_iters)

    # 4 ▸ connected components → bounding boxes
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[Tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if min_area <= area <= max_area:
            boxes.append((x, y, w, h))

    # 5 ▸ sort (optional) top-to-bottom, then left-to-right
    boxes.sort(key=lambda b: (b[1], b[0]))
    return boxes


# ---------------------------------------------------------------------------
# quick demo
if __name__ == "__main__":
    BG     = "assets/blank_board.png"
    MIXED  = "assets/board_with_tiles.png"

    tiles = detect_tiles_by_bg(BG, MIXED)
    print(f"Detected {len(tiles)} tiles:")
    for i, (x, y, w, h) in enumerate(tiles):
        print(f"{i:2d}: (x={x}, y={y})  {w}×{h}")
