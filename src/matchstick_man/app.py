"""Top-level Pyxel application class for Matchstick Man.

This module currently scaffolds an empty window. Game logic — the player
state machine, tile materials, fuses, etc. — will land on subsequent feature
branches and be wired into :meth:`App.update` and :meth:`App.draw`.
"""

from __future__ import annotations

import pyxel

WIDTH = 512
HEIGHT = 480
TITLE = "Matchstick Man"


class App:
    """Top-level Pyxel application.

    Construction initializes the Pyxel runtime (window, palette, sound
    channels). Calling :meth:`run` enters the blocking frame loop. The
    construction-versus-run split exists so the class can be exercised
    in tests with ``pyxel.init(..., headless=True)`` without immediately
    blocking on the run loop.
    """

    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title=TITLE)

    def run(self) -> None:
        """Enter Pyxel's blocking update/draw loop. Returns when the user quits."""
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        """Advance one frame of game state. Currently a no-op."""

    def draw(self) -> None:
        """Render one frame. Currently a black background with a title overlay."""
        pyxel.cls(0)
        pyxel.text(10, 10, TITLE, 7)
