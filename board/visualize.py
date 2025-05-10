import cv2
from pathlib import Path
from typing import Dict, List, Tuple

from services.team_service import Team


def _int_to_bgr(col_int: int) -> Tuple[int, int, int]:
    """Discord integer 0xRRGGBB → (B, G, R)."""
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

    for team in teams:
        idx = int(team.position)
        bgr = _int_to_bgr(team.color)
        tile_to_teams.setdefault(idx, []).append((team.name, bgr))

    for idx, team_list in tile_to_teams.items():
        if idx >= len(tiles):
            print(f"⚠  Tile index {idx} not in tiles list – skipped")
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

    cv2.imwrite(out_path, board)
    print("Saved board overlay →", out_path)
