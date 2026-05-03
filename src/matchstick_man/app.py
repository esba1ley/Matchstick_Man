"""Top-level Pyxel application class for Matchstick Man."""

from __future__ import annotations

from pathlib import Path

import pyxel

from matchstick_man.levels import LEVEL_1
from matchstick_man.player import Player, PlayerState
from matchstick_man.tiles import TILE_COLOR, Level, resolve_collisions

WIDTH = 512
HEIGHT = 480
TITLE = "Matchstick Man"

_ASSET_PATH = Path(__file__).parent / "assets" / "matchstick.pyxres"
_SPRITE_SIZE = 16
_SPRITE_Y = 0
_TRANSPARENT = 0  # black is the sprite transparency color

# Maps each player state to its sprite's u-coordinate in image bank 0.
# DEAD reuses the HEADLESS sprite — no head, no movement.
_SPRITE_U: dict[PlayerState, int] = {
    PlayerState.HEADED: 0,
    PlayerState.BURNING: 16,
    PlayerState.HEADLESS: 32,
    PlayerState.DEAD: 32,
}

# Player spawn: just above the floor in the horizontal center.
_SPAWN_TX = 1  # tile column
_SPAWN_TY = 27  # tile row — one row above the floor


class App:
    """Top-level Pyxel application.

    Construction initializes the Pyxel runtime and loads the sprite resource.
    Calling :meth:`run` enters the blocking frame loop.
    """

    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title=TITLE)
        pyxel.load(str(_ASSET_PATH))
        self._level = Level(LEVEL_1)
        ts = self._level.tile_size
        self._player = Player(
            x=float(_SPAWN_TX * ts),
            y=float(_SPAWN_TY * ts - _SPRITE_SIZE),
        )

    def run(self) -> None:
        """Enter Pyxel's blocking update/draw loop. Returns when the user quits."""
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        """Advance one frame of game state."""
        # 1. Snapshot position before movement (needed by resolve_collisions).
        prev_x = self._player.x
        prev_y = self._player.y

        # 2. Poll input
        left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
        right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)
        jump = (
            pyxel.btnp(pyxel.KEY_UP)
            or pyxel.btnp(pyxel.KEY_W)
            or pyxel.btnp(pyxel.KEY_SPACE)
        )
        jump_held = (
            pyxel.btn(pyxel.KEY_UP)
            or pyxel.btn(pyxel.KEY_W)
            or pyxel.btn(pyxel.KEY_SPACE)
        )

        # 3. Apply input (uses on_ground from last frame for jump check)
        self._player.apply_input(left=left, right=right, jump=jump, jump_held=jump_held)

        # 4. Advance state machine and integrate physics
        self._player.update()

        # 5. AABB collision resolution (also calls leave_ground internally)
        resolve_collisions(self._player, self._level, prev_x, prev_y, _SPRITE_SIZE)

        # 6. Horizontal screen boundaries
        self._player.x = max(0.0, min(self._player.x, float(WIDTH - _SPRITE_SIZE)))

    def draw(self) -> None:
        """Render one frame: tiles then player sprite."""
        pyxel.cls(0)

        # Draw tiles
        ts = self._level.tile_size
        for ty in range(self._level.height):
            for tx in range(self._level.width):
                kind = self._level.get(tx, ty)
                color = TILE_COLOR.get(kind)
                if color is not None:
                    pyxel.rect(tx * ts, ty * ts, ts, ts, color)

        # Draw player sprite (negative width mirrors horizontally when facing left)
        w = _SPRITE_SIZE if self._player.facing_right else -_SPRITE_SIZE
        pyxel.blt(
            int(self._player.x),
            int(self._player.y),
            0,
            _SPRITE_U[self._player.state],
            _SPRITE_Y,
            w,
            _SPRITE_SIZE,
            _TRANSPARENT,
        )
