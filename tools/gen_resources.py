"""Generate src/matchstick_man/assets/matchstick.pyxres from Python sprite data.

Run once from the project root with the matchstick env active:

    mamba run -n matchstick python tools/gen_resources.py

Pyxel opens a tiny 16x16 window briefly while saving — this is expected.
The generated .pyxres is committed to the repo as a binary artifact;
re-run this script whenever the sprite data below changes.

Sprite sheet layout — image bank 0, transparent color = 0 (black):

    (  0, 0) 16x16  HEADED   — red match head, brown stick body
    ( 16, 0) 16x16  BURNING  — orange/yellow flame, brown stick body
    ( 32, 0) 16x16  HEADLESS — no head, brown stick body

Pyxel palette indices referenced here:
    0 = black (background / transparency key)
    4 = brown (match stick)
    7 = white (head highlight)
    8 = red   (match head)
    9 = orange (flame body)
    a = yellow (flame tip, index 10)
"""

from __future__ import annotations

from pathlib import Path

import pyxel

_ASSET_PATH = (
    Path(__file__).parent.parent
    / "src"
    / "matchstick_man"
    / "assets"
    / "matchstick.pyxres"
)

# Each string is one 16-pixel row; each character is a hex color index 0–f.
_HEADED: list[str] = [
    "0000008888000000",  # match head
    "0000008788000000",  # match head (white highlight)
    "0000008888000000",  # match head
    "0000008888000000",  # match head
    "0000000440000000",  # neck
    "0004444444440000",  # shoulders / upper arms
    "0040000440004000",  # arm tips
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # lower torso
    "0000004404400000",  # legs begin to split
    "0000044000440000",  # legs
    "0000440000044000",  # legs
    "0004400000004400",  # feet
]

_BURNING: list[str] = [
    "0000000a00000000",  # flame tip (yellow)
    "000000a9a0000000",  # flame narrow
    "00000a9aa0000000",  # flame wider
    "000009a980000000",  # flame base / head base
    "0000000440000000",  # neck
    "0004444444440000",  # shoulders / upper arms
    "0040000440004000",  # arm tips
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # lower torso
    "0000004404400000",  # legs begin to split
    "0000044000440000",  # legs
    "0000440000044000",  # legs
    "0004400000004400",  # feet
]

_HEADLESS: list[str] = [
    "0000000000000000",  # (no head)
    "0000000000000000",
    "0000000000000000",
    "0000000000000000",
    "0000000440000000",  # neck stub
    "0004444444440000",  # shoulders / upper arms
    "0040000440004000",  # arm tips
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # torso
    "0000000440000000",  # lower torso
    "0000004404400000",  # legs begin to split
    "0000044000440000",  # legs
    "0000440000044000",  # legs
    "0004400000004400",  # feet
]


def main() -> None:
    """Write sprite data to matchstick.pyxres."""
    _ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    pyxel.init(16, 16, title="gen_resources")
    pyxel.images[0].set(0, 0, _HEADED)
    pyxel.images[0].set(16, 0, _BURNING)
    pyxel.images[0].set(32, 0, _HEADLESS)
    pyxel.save(str(_ASSET_PATH))
    print(f"Saved {_ASSET_PATH}")


if __name__ == "__main__":
    main()
