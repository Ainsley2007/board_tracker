from util.logger import log
import cv2
from pathlib import Path
from typing import Dict, List, Tuple

from services.team_service import Team


def _int_to_bgr(col_int: int) -> Tuple[int, int, int]:
    return (col_int & 0xFF, (col_int >> 8) & 0xFF, (col_int >> 16) & 0xFF)


def paint_team_circles(
    board_path: str | Path,
    tiles: List[Tuple[int, int, int, int]],
    teams: List[Team],
    out_path: str = "assets/board_state.png",
    radius: int = 10,
    pad: int = 10,
    shift: int = 10,
) -> None:
    board = cv2.imread(str(board_path))
    if board is None:
        raise FileNotFoundError(board_path)

    tile_to_teams: Dict[int, List[Tuple[str, Tuple[int, int, int]]]] = {}
    tile_to_blacklists: Dict[int, List[Tuple[int, int, int]]] = {}

    for team in teams:
        bgr = _int_to_bgr(team.color)
        tile_to_teams.setdefault(int(team.position), []).append((team.name, bgr))
        for tile_id in team.blacklist_tiles:
            tile_to_blacklists.setdefault(int(tile_id), []).append(bgr)

    for idx, team_list in tile_to_teams.items():
        if idx >= len(tiles):
            print(f"⚠  Tile index {idx} not in tiles list - skipped")
            continue

        x, y, w, h = tiles[idx]
        base_cx = x + w - pad - radius
        cy = y + h - pad - radius

        for k, (_, bgr) in enumerate(team_list):
            cx = base_cx - k * shift
            if cx - radius < x + pad:
                cx = x + pad + radius

            cv2.circle(
                board,
                (cx, cy),
                radius + 2,
                (255, 255, 255),
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                board,
                (cx, cy),
                radius,
                bgr,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

    _paint_blacklist_crosses(board, tiles, tile_to_blacklists, pad)

    cv2.imwrite(out_path, board)
    log.info(f"Saved board overlay → {out_path}")


def _paint_blacklist_crosses(
    board,
    tiles: List[Tuple[int, int, int, int]],
    tile_to_blacklists: Dict[int, List[Tuple[int, int, int]]],
    pad: int,
) -> None:
    for idx, colors in tile_to_blacklists.items():
        if idx >= len(tiles):
            continue
        x, y, w, h = tiles[idx]
        base_x = x + pad + 5
        base_y = y + pad + 5
        step = 14
        marker = 5

        for k, bgr in enumerate(colors):
            cx = min(base_x + (k % 3) * step, x + w - pad - marker)
            cy = min(base_y + (k // 3) * step, y + h - pad - marker)
            _draw_cross(board, cx, cy, marker, bgr, 1)


def _draw_cross(board, cx: int, cy: int, size: int, color, thickness: int) -> None:
    cv2.line(
        board,
        (cx - size, cy - size),
        (cx + size, cy + size),
        color=color,
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.line(
        board,
        (cx - size, cy + size),
        (cx + size, cy - size),
        color=color,
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )
