import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")

from board.board_detector import detect_tiles_by_bg, write_tile_detection_outline

_ROOT = Path(__file__).resolve().parent.parent
_BG = _ROOT / "assets" / "background.png"
_BOARD = _ROOT / "assets" / "board.png"
_TILES_JSON = _ROOT / "assets" / "tiles.json"


def _expected_tile_count() -> int:
    with _TILES_JSON.open(encoding="utf-8") as fp:
        return len(json.load(fp)["tiles"])


@pytest.mark.skipif(not _BG.is_file() or not _BOARD.is_file(), reason="board PNG assets missing")
def test_detect_tiles_count_matches_tiles_json():
    expected = _expected_tile_count()
    boxes = detect_tiles_by_bg(_BG, _BOARD)
    assert len(boxes) == expected, (
        f"expected {expected} tile regions (tiles.json), got {len(boxes)} — "
        "check assets/background.png vs assets/board.png and max_area/min_area"
    )


@pytest.mark.skipif(not _BG.is_file() or not _BOARD.is_file(), reason="board PNG assets missing")
def test_detect_tiles_start_tile_is_wider_than_standard_cells():
    boxes = detect_tiles_by_bg(_BG, _BOARD)
    assert boxes, "no tiles detected"
    w0 = boxes[0][2]
    w1 = boxes[1][2]
    assert w0 > w1, "first tile should be wider (start spans two cells in art)"


@pytest.mark.skipif(not _BG.is_file() or not _BOARD.is_file(), reason="board PNG assets missing")
def test_end_tile_index_90_is_large_center_finish():
    boxes = detect_tiles_by_bg(_BG, _BOARD)
    assert len(boxes) == 91
    x, y, w, h = boxes[-1]
    assert w * h >= 35_000
    assert w >= 200 and h >= 200
    pen = boxes[-2]
    assert pen[2] * pen[3] == 10_000


@pytest.mark.skipif(not _BOARD.is_file(), reason="board PNG assets missing")
def test_write_tile_detection_outline_png(tmp_path):
    boxes = detect_tiles_by_bg(_BG, _BOARD)
    out = tmp_path / "outline.png"
    write_tile_detection_outline(_BOARD, boxes, out)
    assert out.is_file() and out.stat().st_size > 10_000
