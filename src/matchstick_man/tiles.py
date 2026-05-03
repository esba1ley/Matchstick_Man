"""Tile system: kinds, level data, and AABB collision resolution.

Tile characters used in level strings::

    .  EMPTY      air
    #  FLOOR      solid ground / platform
    |  WALL       solid vertical barrier
    R  ROUGH      ceiling that ignites the player's head
    S  SMOOTH     ceiling that bonks without ignition
    ~  WATER      extinguishes a burning player
    m  MATCHBOOK  pickup that restores a headless player

This module has no Pyxel dependency — layout, Level, and collision logic
are pure Python so they can be unit-tested without a display.
"""

from __future__ import annotations

from enum import Enum, auto

from matchstick_man.player import Player

TILE_SIZE: int = 16
"""Edge length of one tile in pixels."""


class TileKind(Enum):
    """Classification of a single map tile."""

    EMPTY = auto()
    FLOOR = auto()
    WALL = auto()
    ROUGH = auto()
    SMOOTH = auto()
    WATER = auto()
    MATCHBOOK = auto()


# Mapping from level-string characters to TileKind values.
_CHAR_MAP: dict[str, TileKind] = {
    ".": TileKind.EMPTY,
    "#": TileKind.FLOOR,
    "|": TileKind.WALL,
    "R": TileKind.ROUGH,
    "S": TileKind.SMOOTH,
    "~": TileKind.WATER,
    "m": TileKind.MATCHBOOK,
}

# Tile kinds that block passage (wall / floor / ceiling).
_SOLID: frozenset[TileKind] = frozenset(
    {TileKind.FLOOR, TileKind.WALL, TileKind.ROUGH, TileKind.SMOOTH}
)

# Pyxel palette color index used when rendering each tile kind.
TILE_COLOR: dict[TileKind, int] = {
    TileKind.FLOOR: 5,  # dark gray
    TileKind.WALL: 5,  # dark gray
    TileKind.ROUGH: 8,  # red
    TileKind.SMOOTH: 7,  # white
    TileKind.WATER: 12,  # teal / cyan
    TileKind.MATCHBOOK: 10,  # yellow
}


class Level:
    """A 2-D tile map loaded from a list of character strings.

    Parameters
    ----------
    rows : list[str]
        One string per tile row.  Each character maps to a ``TileKind``
        via the table in the module docstring.  Unknown characters are
        treated as ``EMPTY``.  Rows shorter than the widest row are
        padded with ``EMPTY`` on access via :meth:`get`.
    tile_size : int, optional
        Edge length of one tile in pixels.  Defaults to ``TILE_SIZE``.
    """

    def __init__(self, rows: list[str], tile_size: int = TILE_SIZE) -> None:
        self.tile_size = tile_size
        self._grid: list[list[TileKind]] = [
            [_CHAR_MAP.get(ch, TileKind.EMPTY) for ch in row] for row in rows
        ]
        self.height: int = len(self._grid)
        self.width: int = max((len(row) for row in self._grid), default=0)

    def get(self, tx: int, ty: int) -> TileKind:
        """Return the tile at tile-coordinate (tx, ty).

        Returns ``EMPTY`` for any out-of-bounds coordinate.
        """
        if tx < 0 or ty < 0 or ty >= self.height:
            return TileKind.EMPTY
        row = self._grid[ty]
        if tx >= len(row):
            return TileKind.EMPTY
        return row[tx]

    def clear(self, tx: int, ty: int) -> None:
        """Replace the tile at (tx, ty) with EMPTY (used for consumed pickups)."""
        if 0 <= ty < self.height and 0 <= tx < len(self._grid[ty]):
            self._grid[ty][tx] = TileKind.EMPTY


def resolve_collisions(
    player: Player,
    level: Level,
    prev_x: float,
    prev_y: float,
    sprite_size: int,
) -> None:
    """Push the player out of overlapping tiles and fire state-machine events.

    Must be called after ``player.update()`` has integrated velocity into
    position.  Uses the player's previous position (before this frame's
    movement) to determine which face of each tile was entered, correctly
    distinguishing floor from ceiling and left-wall from right-wall hits.

    Also calls ``player.leave_ground()`` before checking floor contacts, so
    the caller does not need to do so separately.

    Parameters
    ----------
    player : Player
        The player whose position and state are updated in place.
    level : Level
        The tile map to collide against.
    prev_x : float
        Player ``x`` before this frame's movement was applied.
    prev_y : float
        Player ``y`` before this frame's movement was applied.
    sprite_size : int
        Width and height of the player sprite in pixels.
    """
    ts = level.tile_size
    ss = sprite_size

    player.leave_ground()

    # Tile range that could overlap with the player AABB.
    # Use float arithmetic for max bounds so that a fractional position that
    # pushes the bottom/right edge past a tile boundary is not truncated away.
    # The per-tile overlap check (p_right <= tile_left etc.) handles the exact-
    # boundary case where the edge merely touches but does not overlap.
    tx_min = max(0, int(player.x) // ts)
    tx_max = min(level.width - 1, int(player.x + ss) // ts)
    ty_min = max(0, int(player.y) // ts)
    ty_max = min(level.height - 1, int(player.y + ss) // ts)

    for ty in range(ty_min, ty_max + 1):
        for tx in range(tx_min, tx_max + 1):
            kind = level.get(tx, ty)
            if kind is TileKind.EMPTY:
                continue

            tile_left = tx * ts
            tile_top = ty * ts
            tile_right = tile_left + ts
            tile_bottom = tile_top + ts

            # Re-read bounds each iteration — prior pushes may have moved the player.
            p_left = player.x
            p_top = player.y
            p_right = player.x + ss
            p_bottom = player.y + ss

            # No overlap → nothing to do.
            if p_right <= tile_left or p_left >= tile_right:
                continue
            if p_bottom <= tile_top or p_top >= tile_bottom:
                continue

            # --- Non-solid special tiles ---
            if kind is TileKind.WATER:
                player.hit_water()
                continue
            if kind is TileKind.MATCHBOOK:
                player.pickup_matchbook()
                level.clear(tx, ty)
                continue

            # --- Solid tile: determine entry direction from previous position. ---
            prev_bottom = prev_y + ss
            prev_right = prev_x + ss

            entered_from_above = prev_bottom <= tile_top
            entered_from_below = prev_y >= tile_bottom
            entered_from_left = prev_right <= tile_left
            entered_from_right = prev_x >= tile_right

            if entered_from_above:
                player.land(float(tile_top - ss))
            elif entered_from_below:
                player.bonk_ceiling(float(tile_bottom))
                if kind is TileKind.ROUGH:
                    player.hit_rough_ceiling()
            elif entered_from_left:
                player.x = float(tile_left - ss)
            elif entered_from_right:
                player.x = float(tile_right)
            else:
                # Corner case: player was already overlapping (e.g. spawn inside tile).
                # Resolve by minimum overlap axis, preferring vertical.
                ov_top = p_bottom - tile_top
                ov_bot = tile_bottom - p_top
                ov_left = p_right - tile_left
                ov_right = tile_right - p_left
                min_v = min(ov_top, ov_bot)
                min_h = min(ov_left, ov_right)
                if min_v <= min_h:
                    if ov_top < ov_bot:
                        player.land(float(tile_top - ss))
                    else:
                        player.bonk_ceiling(float(tile_bottom))
                        if kind is TileKind.ROUGH:
                            player.hit_rough_ceiling()
                else:
                    if ov_left < ov_right:
                        player.x = float(tile_left - ss)
                    else:
                        player.x = float(tile_right)
