# file: overlay_positions.py
import cv2
from pathlib import Path
from typing import Dict, List, Tuple


def _int_to_bgr(col_int: int) -> Tuple[int, int, int]:
    """Discord integer 0xRRGGBB → (B,G,R)."""
    r = (col_int >> 16) & 0xFF
    g = (col_int >> 8) & 0xFF
    b = col_int & 0xFF
    return (b, g, r)


def paint_team_circles(
    board_path: str | Path,
    tiles: List[Tuple[int, int, int, int]],
    teams: Dict[str, Dict[str, any]],
    out_path: str = "assets/board_state.png",
    radius: int = 10,
    pad: int = 10,
    shift: int = 10,
) -> None:
    """
    Draw a dot per TEAM (not per player) on its current tile.

    `teams` is the dict returned by db.get_teams().
    """
    board = cv2.imread(str(board_path))
    if board is None:
        raise FileNotFoundError(board_path)

    tile_to_teams: Dict[int, List[Tuple[str, Tuple[int, int, int]]]] = {}

    for slug, row in teams.items():
        idx = int(row["pos"])
        col_raw = row.get("color")
        bgr = _int_to_bgr(col_raw)

        tile_to_teams.setdefault(idx, []).append((slug, bgr))

    # draw circles ------------------------------------------------------
    for idx, team_list in tile_to_teams.items():
        try:
            x, y, w, h = tiles[idx]
        except IndexError:
            print(f"⚠  Tile index {idx} not in tiles list – skipped")
            continue

        base_cx = x + w - pad - radius
        cy = y + h - pad - radius

        for k, (_, bgr) in enumerate(team_list):
            cx = base_cx - k * shift
            if cx - radius < x + pad:
                cx = x + pad + radius

            # --- draw white ring then coloured fill --------------------------
            cv2.circle(
                board,
                (cx, cy),
                radius + 2,
                (255, 255, 255),
                thickness=-1,
                lineType=cv2.LINE_AA,
            )  # outline
            cv2.circle(
                board, (cx, cy), radius, bgr, thickness=-1, lineType=cv2.LINE_AA
            )  # fill

    cv2.imwrite(out_path, board)
    print("Saved board overlay →", out_path)
