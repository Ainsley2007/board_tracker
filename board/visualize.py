# file: overlay_positions.py
import cv2
from pathlib import Path
from typing import Dict, List, Tuple

# minimal HTML-style colour names → BGR tuples
HTML2BGR = {
    "red":    (  0,   0, 255),
    "yellow": (  0, 255, 255),
    "blue":   (255,   0,   0),
    "green":  (  0, 255,   0),
    "purple": (255,   0, 255),
    "orange": (  0, 165, 255),
    "black":  (  0,   0,   0),
    "white":  (255, 255, 255),
}

def paint_player_circles(
    board_path: str | Path,
    tiles: List[Tuple[int, int, int, int]],
    positions: Dict[str, Dict[str, str | int]],
    out_path: str = "assets/board_state.png",
    radius: int = 10,                 
    pad: int = 10,                
    shift: int = 7,     
) -> None:
    """
    Draw one circle per player:
        • centred (bottom-right)  = first player on that tile
        • next players shift `shift` pixels left each time
    """
    board = cv2.imread(str(board_path))
    if board is None:
        raise FileNotFoundError(board_path)

    # 1 ▸ collect players per tile in display order
    tile_to_players: Dict[int, List[Tuple[str, Tuple[int,int,int]]]] = {}
    for name, info in positions.items():
        idx   = int(info["position"])
        bgr   = HTML2BGR.get(info["color"].lower(), (200, 200, 200))
        tile_to_players.setdefault(idx, []).append((name, bgr))

    # 2 ▸ draw circles
    for idx, players in tile_to_players.items():
        try:
            x, y, w, h = tiles[idx]
        except IndexError:
            print(f"⚠  Tile index {idx} not in tiles list – skipped")
            continue

        # anchor in bottom-right corner
        base_cx = x + w - pad - radius
        cy      = y + h - pad - radius

        for k, (_, bgr) in enumerate(players):
            cx = base_cx - k * shift
            # stay inside tile (optional safeguard)
            if cx - radius < x + pad:
                cx = x + pad + radius
            cv2.circle(board, (cx, cy), radius, bgr, thickness=-1, lineType=cv2.LINE_AA)

    cv2.imwrite(out_path, board)
    print("Saved board with player dots →", out_path)