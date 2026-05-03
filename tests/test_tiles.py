"""Tests for the tile system: Level, TileKind, and AABB collision resolution."""

import pytest

from matchstick_man.player import Player, PlayerState
from matchstick_man.tiles import (
    TILE_SIZE,
    Level,
    TileKind,
    resolve_collisions,
)

TS = TILE_SIZE  # 16 — shorthand used throughout


# ---------------------------------------------------------------------------
# Level construction and access
# ---------------------------------------------------------------------------


class TestLevelConstruction:
    def test_width_from_longest_row(self):
        lvl = Level(["###", "##"])
        assert lvl.width == 3

    def test_height_from_row_count(self):
        lvl = Level(["###", "###", "###"])
        assert lvl.height == 3

    def test_empty_level(self):
        lvl = Level([])
        assert lvl.width == 0
        assert lvl.height == 0

    def test_custom_tile_size(self):
        lvl = Level(["#"], tile_size=8)
        assert lvl.tile_size == 8

    def test_known_chars_parsed(self):
        row = ".#|RSm~"
        lvl = Level([row])
        expected = [
            TileKind.EMPTY,
            TileKind.FLOOR,
            TileKind.WALL,
            TileKind.ROUGH,
            TileKind.SMOOTH,
            TileKind.MATCHBOOK,
            TileKind.WATER,
        ]
        for tx, kind in enumerate(expected):
            assert lvl.get(tx, 0) is kind

    def test_unknown_char_is_empty(self):
        lvl = Level(["?"])
        assert lvl.get(0, 0) is TileKind.EMPTY


class TestLevelGet:
    def test_in_bounds(self):
        lvl = Level(["#."])
        assert lvl.get(0, 0) is TileKind.FLOOR
        assert lvl.get(1, 0) is TileKind.EMPTY

    def test_negative_tx_is_empty(self):
        lvl = Level(["#"])
        assert lvl.get(-1, 0) is TileKind.EMPTY

    def test_negative_ty_is_empty(self):
        lvl = Level(["#"])
        assert lvl.get(0, -1) is TileKind.EMPTY

    def test_tx_beyond_row_is_empty(self):
        lvl = Level(["#"])
        assert lvl.get(5, 0) is TileKind.EMPTY

    def test_ty_beyond_height_is_empty(self):
        lvl = Level(["#"])
        assert lvl.get(0, 5) is TileKind.EMPTY

    def test_short_row_padded_with_empty(self):
        lvl = Level(["#", "###"])
        # Row 0 has width 1; columns 1 and 2 are implicitly EMPTY.
        assert lvl.get(1, 0) is TileKind.EMPTY
        assert lvl.get(2, 0) is TileKind.EMPTY


class TestLevelClear:
    def test_clear_replaces_with_empty(self):
        lvl = Level(["m"])
        lvl.clear(0, 0)
        assert lvl.get(0, 0) is TileKind.EMPTY

    def test_clear_oob_is_no_op(self):
        lvl = Level(["m"])
        lvl.clear(5, 5)  # should not raise
        assert lvl.get(0, 0) is TileKind.MATCHBOOK


# ---------------------------------------------------------------------------
# resolve_collisions — helper factories
# ---------------------------------------------------------------------------


def _floor_level(tx: int = 0, ty: int = 1, kind: str = "#") -> Level:
    """Return a minimal level with one tile at (tx, ty)."""
    empty_row = "." * (tx + 1)
    tile_row = "." * tx + kind + "." * 0
    rows: list[str] = []
    for row_idx in range(ty + 1):
        rows.append(tile_row if row_idx == ty else empty_row)
    return Level(rows)


def _player_above_tile(tx: int = 0, ty: int = 1) -> tuple[Player, float, float]:
    """Return (player, prev_x, prev_y) positioned just above tile (tx, ty).

    The player's bottom edge sits at exactly tile_top, so after a one-pixel
    downward move the player overlaps the tile from above.
    """
    tile_top = ty * TS
    x = float(tx * TS)
    prev_y = float(tile_top - TS)  # bottom edge at tile_top
    p = Player(x=x, y=prev_y + 1.0)  # moved 1 px into tile
    return p, x, prev_y


# ---------------------------------------------------------------------------
# Landing (entered from above)
# ---------------------------------------------------------------------------


class TestResolveFloorContact:
    def test_player_pushed_above_floor(self):
        lvl = _floor_level(tx=0, ty=1)
        p, prev_x, prev_y = _player_above_tile(tx=0, ty=1)
        resolve_collisions(p, lvl, prev_x, prev_y, TS)
        assert p.y == pytest.approx(float(1 * TS - TS))

    def test_player_on_ground_after_land(self):
        lvl = _floor_level(tx=0, ty=1)
        p, prev_x, prev_y = _player_above_tile(tx=0, ty=1)
        resolve_collisions(p, lvl, prev_x, prev_y, TS)
        assert p.on_ground is True

    def test_vy_zeroed_after_land(self):
        lvl = _floor_level(tx=0, ty=1)
        p, prev_x, prev_y = _player_above_tile(tx=0, ty=1)
        p._vy = 5.0  # simulate falling
        resolve_collisions(p, lvl, prev_x, prev_y, TS)
        assert p.vy == pytest.approx(0.0)

    def test_floor_detected_after_gravity_push_fractional(self):
        # Regression: after land() snaps player to floor, the next frame applies
        # gravity and adds a fractional y offset (e.g. 0.5 px).  With integer
        # truncation in the tile-range bounds the bottom edge (now 0.5 px inside
        # the tile) was silently excluded, leaving _on_ground=False and causing
        # ~50% of jump presses to be swallowed.
        lvl = _floor_level(tx=0, ty=1)
        floor_y = float(1 * TS - TS)  # = 0.0 for ty=1, ss=TS
        p = Player(x=0.0, y=floor_y)  # snapped exactly to the floor
        # Simulate gravity moving the player 0.5 px into the tile.
        p._vy = 0.5
        p.y += 0.5  # now y=0.5; bottom edge = 0.5+16 = 16.5, inside tile at ty=1
        resolve_collisions(p, lvl, 0.0, floor_y, TS)
        assert p.on_ground is True
        assert p.y == pytest.approx(floor_y)


# ---------------------------------------------------------------------------
# Ceiling bonk (entered from below)
# ---------------------------------------------------------------------------


class TestResolveCeilingContact:
    def _setup_ceiling(self, kind: str = "S") -> tuple[Player, Level, float, float]:
        """Player moving upward into a ceiling tile at (0, 0)."""
        lvl = Level([kind])  # tile at (0, 0), top=0, bottom=TS
        # Player's top was at tile_bottom (TS), now moved 1 px into tile from below
        prev_y = float(TS)  # top of player was at tile bottom
        x = 0.0
        p = Player(x=x, y=prev_y - 1.0)  # now inside ceiling tile
        p._vy = -3.0
        return p, lvl, x, prev_y

    def test_y_snapped_to_ceiling_bottom(self):
        p, lvl, px, py = self._setup_ceiling("S")
        resolve_collisions(p, lvl, px, py, TS)
        assert p.y == pytest.approx(float(TS))

    def test_vy_zeroed_after_bonk(self):
        p, lvl, px, py = self._setup_ceiling("S")
        resolve_collisions(p, lvl, px, py, TS)
        assert p.vy == pytest.approx(0.0)

    def test_smooth_ceiling_no_state_change(self):
        p, lvl, px, py = self._setup_ceiling("S")
        resolve_collisions(p, lvl, px, py, TS)
        assert p.state is PlayerState.HEADED

    def test_rough_ceiling_ignites_player(self):
        p, lvl, px, py = self._setup_ceiling("R")
        resolve_collisions(p, lvl, px, py, TS)
        assert p.state is PlayerState.BURNING

    def test_rough_ceiling_headless_no_ignite(self):
        p, lvl, px, py = self._setup_ceiling("R")
        p.hit_rough_ceiling()  # → BURNING
        p.hit_water()  # → HEADLESS
        resolve_collisions(p, lvl, px, py, TS)
        assert p.state is PlayerState.HEADLESS


# ---------------------------------------------------------------------------
# Wall contact (horizontal)
# ---------------------------------------------------------------------------


class TestResolveWallContact:
    def test_push_left_on_right_wall(self):
        """Player moving right into a wall at (1, 0)."""
        lvl = Level([".#"])
        # prev_right was at tile_left (TS), now 1 px inside from the left
        prev_x = float(TS - TS)  # right edge was at TS (tile left)
        x = prev_x + 1.0
        p = Player(x=x, y=0.0)
        resolve_collisions(p, lvl, prev_x, 0.0, TS)
        assert p.x == pytest.approx(0.0)  # pushed back to tile_left - TS

    def test_push_right_on_left_wall(self):
        """Player moving left into a wall at (0, 0)."""
        lvl = Level(["#."])
        # prev_x was at tile_right (TS), now 1 px inside from the right
        prev_x = float(TS)
        x = prev_x - 1.0
        p = Player(x=x, y=0.0)
        resolve_collisions(p, lvl, prev_x, 0.0, TS)
        assert p.x == pytest.approx(float(TS))


# ---------------------------------------------------------------------------
# Non-solid special tiles
# ---------------------------------------------------------------------------


class TestResolveWaterContact:
    def test_water_calls_hit_water_when_burning(self):
        lvl = Level(["~"])
        p = Player(x=0.0, y=0.0)
        p.hit_rough_ceiling()  # → BURNING
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert p.state is PlayerState.HEADLESS

    def test_water_no_position_change(self):
        lvl = Level(["~"])
        p = Player(x=0.0, y=0.0)
        p.hit_rough_ceiling()
        orig_x, orig_y = p.x, p.y
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert p.x == pytest.approx(orig_x)
        assert p.y == pytest.approx(orig_y)


class TestResolveMatchbookPickup:
    def test_matchbook_restores_head_when_headless(self):
        lvl = Level(["m"])
        p = Player(x=0.0, y=0.0)
        p.hit_rough_ceiling()  # → BURNING
        p.hit_water()  # → HEADLESS
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert p.state is PlayerState.HEADED

    def test_matchbook_tile_consumed(self):
        lvl = Level(["m"])
        p = Player(x=0.0, y=0.0)
        p.hit_rough_ceiling()
        p.hit_water()
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert lvl.get(0, 0) is TileKind.EMPTY

    def test_matchbook_no_position_change(self):
        lvl = Level(["m"])
        p = Player(x=0.0, y=0.0)
        p.hit_rough_ceiling()
        p.hit_water()
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert p.x == pytest.approx(0.0)
        assert p.y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# leave_ground called at start of resolve_collisions
# ---------------------------------------------------------------------------


class TestResolveCallsLeaveGround:
    def test_leave_ground_called_before_floor_check(self):
        """resolve_collisions must call leave_ground so players not on a floor
        tile end up airborne even if they were grounded last frame."""
        lvl = Level([".", "."])  # all empty — no floor
        p = Player(x=0.0, y=0.0)
        # Artificially mark as grounded
        p._on_ground = True
        resolve_collisions(p, lvl, 0.0, 0.0, TS)
        assert p.on_ground is False

    def test_grounded_after_standing_on_floor(self):
        """But if the player IS on a floor tile they should be re-grounded."""
        lvl = _floor_level(tx=0, ty=1)
        p, prev_x, prev_y = _player_above_tile(tx=0, ty=1)
        resolve_collisions(p, lvl, prev_x, prev_y, TS)
        assert p.on_ground is True
