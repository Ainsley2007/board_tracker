# file: bg_subtract_detector.py
import statistics
import cv2
from pathlib import Path
from typing import List, Tuple

_END_TILE_MIN_AREA = 35_000


def _drop_nested_fragments(
    boxes: List[Tuple[int, int, int, int]],
) -> List[Tuple[int, int, int, int]]:
    def inside(sm: Tuple[int, int, int, int], big: Tuple[int, int, int, int]) -> bool:
        sx, sy, sw, sh = sm
        bx, by, bw, bh = big
        pad = 2
        return (
            sx >= bx - pad
            and sy >= by - pad
            and sx + sw <= bx + bw + pad
            and sy + sh <= by + bh + pad
        )

    areas = [(b[2] * b[3], b) for b in boxes]
    out: List[Tuple[int, int, int, int]] = []
    for ai, bi in areas:
        if ai < 8_000:
            if any(inside(bi, bj) for aj, bj in areas if aj > ai):
                continue
        out.append(bi)
    return out


def _pop_end_tile(
    boxes: List[Tuple[int, int, int, int]],
) -> tuple[List[Tuple[int, int, int, int]], Tuple[int, int, int, int] | None]:
    candidates = [
        (i, b) for i, b in enumerate(boxes) if b[2] * b[3] >= _END_TILE_MIN_AREA
    ]
    if not candidates:
        return boxes, None
    end_i, end = max(candidates, key=lambda ib: ib[1][2] * ib[1][3])
    path = [b for i, b in enumerate(boxes) if i != end_i]
    return path, end


def _snake_sort(boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
    if not boxes:
        return []

    heights = [h for (_, _, _, h) in boxes]
    median_h = statistics.median(heights)
    row_thresh = median_h * 0.5

    boxes_by_y = sorted(boxes, key=lambda b: b[1])
    rows: List[List[Tuple[int, int, int, int]]] = []
    current_row: List[Tuple[int, int, int, int]] = []
    row_anchor_y: float | None = None

    for b in boxes_by_y:
        _, y, _, _ = b
        if row_anchor_y is None or abs(y - row_anchor_y) <= row_thresh:
            current_row.append(b)
            if row_anchor_y is None:
                row_anchor_y = float(y)
        else:
            rows.append(current_row)
            current_row = [b]
            row_anchor_y = float(y)

    if current_row:
        rows.append(current_row)

    snake_order: List[Tuple[int, int, int, int]] = []
    for i, row in enumerate(rows):
        left_to_right = i % 2 == 0
        sorted_row = sorted(row, key=lambda b: b[0], reverse=not left_to_right)
        snake_order.extend(sorted_row)

    return snake_order


def detect_tiles_by_bg(
    bg_path: str | Path,
    mixed_path: str | Path,
    diff_thresh: int = 25,
    min_area: int = 400,
    max_area: int = 80_000,
    close_iters: int = 2,
) -> List[Tuple[int, int, int, int]]:
    bg = cv2.imread(str(bg_path))
    mixed = cv2.imread(str(mixed_path))
    if bg is None or mixed is None:
        raise FileNotFoundError("Could not read one of the images.")
    if bg.shape != mixed.shape:
        raise ValueError("Background and mixed image differ in size!")

    diff = cv2.absdiff(
        cv2.cvtColor(mixed, cv2.COLOR_BGR2GRAY), cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    )

    _, mask = cv2.threshold(diff, diff_thresh, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.dilate(mask, kernel, iterations=close_iters)
    mask = cv2.erode(mask, kernel, iterations=close_iters)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[Tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if min_area <= area <= max_area:
            boxes.append((x, y, w, h))

    boxes = _drop_nested_fragments(boxes)
    path_boxes, end_box = _pop_end_tile(boxes)
    snake_path = _snake_sort(path_boxes)

    if end_box is not None:
        return snake_path + [end_box]
    return snake_path


def write_tile_detection_outline(
    source_image_path: str | Path,
    boxes: List[Tuple[int, int, int, int]],
    out_path: str | Path,
) -> None:
    img = cv2.imread(str(source_image_path))
    if img is None:
        raise FileNotFoundError(source_image_path)
    vis = img.copy()
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2, lineType=cv2.LINE_AA)
        label = str(i)
        (tw, th), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
        )
        cv2.rectangle(vis, (x, y), (x + tw + 4, y + th + 6), (0, 255, 0), -1)
        cv2.putText(
            vis,
            label,
            (x + 2, y + th + 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            2,
            lineType=cv2.LINE_AA,
        )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out), vis):
        raise OSError(f"failed to write {out}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    BG = root / "assets" / "background.png"
    MIXED = root / "assets" / "board.png"
    out_dir = root / "tests" / "generated"

    first: List[Tuple[int, int, int, int]] | None = None
    for run in range(1, 6):
        tiles = detect_tiles_by_bg(BG, MIXED)
        if first is None:
            first = tiles
            print(f"Detected {len(tiles)} tiles:")
            for i, (x, y, w, h) in enumerate(tiles):
                print(f"{i:2d}: (x={x}, y={y})  {w}×{h}")
        elif tiles != first:
            print(f"WARNING run {run}: box list differs from run 1")
        out_png = out_dir / f"detected_tiles_outline_{run}.png"
        write_tile_detection_outline(MIXED, tiles, out_png)
        print(f"Wrote {out_png}")
