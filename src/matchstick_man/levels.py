"""Level data for Matchstick Man.

Each level is a list of strings parsed by :class:`~matchstick_man.tiles.Level`.
Characters are documented in :mod:`matchstick_man.tiles`.

Level coordinates: row 0 is the top of the screen; tile (tx, ty) occupies
pixels (tx*16, ty*16) to (tx*16+16, ty*16+16).

The 512×480 screen at tile size 16 gives 32 columns × 30 rows.
"""

from __future__ import annotations

# 32 columns × 30 rows.
# Layout overview:
#   rows 0–0   : rough ceiling (R) — ignites on contact
#   row  1     : smooth ceiling strip (S) across middle section
#   rows 2–26  : open air / platforms
#   row  27    : low platform with matchbook (m)
#   rows 28–29 : solid floor (#)
#   walls      : | at columns 0 and 31
#   water pool : ~ at rows 24–25, columns 8–13
LEVEL_1: list[str] = [
    "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",  # row  0
    "|...............................|",  # row  1
    "|...............................|",  # row  2
    "|...............................|",  # row  3
    "|...............................|",  # row  4
    "|...............................|",  # row  5
    "|...............................|",  # row  6
    "|...............................|",  # row  7
    "|...............................|",  # row  8
    "|...............................|",  # row  9
    "|...............................|",  # row 10
    "|...............................|",  # row 11
    "|...............................|",  # row 12
    "|...............................|",  # row 13
    "|...............................|",  # row 14
    "|...............................|",  # row 15
    "|...............................|",  # row 16
    "|...............................|",  # row 17
    "|...............................|",  # row 18
    "|...............................|",  # row 19
    "|.....####......................|",  # row 20
    "|~~............####.............|",  # row 21
    "|#~~~~~~~~~~~..RRRR.............|",  # row 22
    "|#~~~~~~~~~#~...................|",  # row 23
    "|.#########.~...................|",  # row 24 - platform
    "|.##RRR##...~........####.......|",  # row 25 - Rough and smooth
    "|...........~..m................|",  # row 26 - platform
    "|...........~.####..............|",  # row 27 - platform
    "|...........~...................|",  # row 28 — matchbook pickup
    "|###########~~~~~~##############|",  # row 29 — water pit
]
