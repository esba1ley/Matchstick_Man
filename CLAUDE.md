# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Matchstick Man** is a 2D platformer in 8-bit console aesthetic. The player controls a matchstick figure — split-bottom legs, ignitable head — that runs, jumps, and swims through hand-crafted levels, ultimately lighting fuses to detonate the level for completion. Score is a function of completion time: faster runs score higher. There are no collectible-style pickups planned beyond the matchbook (see below); do not add coin/gem mechanics without explicit design discussion.

## Core mechanic — player state machine

The fire / water / matchbook loop is the central tension of the game. Levels should be designed around forcing the player through these state transitions, not just jump puzzles.

| State | Movement | Can light fuses? | Transitions out |
| --- | --- | --- | --- |
| **Headed** (default) | run, jump, swim | yes | rough-ceiling contact → Burning |
| **Burning** | run, jump, swim | yes (briefly, before death) | water contact → Headless · countdown expires → death |
| **Headless** | run, swim only — no jump | no | matchbook pickup → Headed |

Implementation implications of the design (to be honored when code lands):

- Holding the jump button longer raises the apex. Jumping into a ceiling tile checks that tile's material.
- Ceiling tiles carry a material classification — at minimum `rough` (sandpaper, brick, etc., ignites) vs. `smooth` (bonks without ignition). New materials should slot into this taxonomy rather than living as one-off flags.
- Water tiles (pools, waterfalls) trigger extinguish on contact while Burning.
- Matchbook pickups are the gating resource for headless segments. Treat them as level-design currency — placement is the puzzle, not abundance.
- "Headless can't jump" is a hard rule: it gates progression and forces the player to seek out a matchbook before continuing past any vertical obstacle.

## Tech stack

- **Engine**: [Pyxel](https://github.com/kitao/pyxel) 2.9.4 — Python game engine with a built-in 16-color palette, sprite/sfx/music editors, and HTML5 export. The hard limits (palette size, sound channel count) enforce the 8-bit aesthetic by construction; do not work around them.
- **Resolution**: **512×480** (2× NES). Confirmed working at this size on Pyxel 2.9.4. Do not change without design discussion.
- **Targets**: macOS desktop (primary dev) and web (via `pyxel app2html` for HTML5/WebAssembly export).
- **Python**: 3.12 (per global preference). Pyxel's wheel is `cp310-abi3`, so 3.11 and 3.13 should work too — verify before claiming cross-version support.

## Environment

Dev environment is a miniforge3 conda env named **`matchstick`**. Pyxel is **not** on conda-forge — it is installed via pip *inside* the conda env. The reproducible spec is [environment.yml](environment.yml).

```sh
mamba activate matchstick                                    # activate for an interactive shell
mamba run -n matchstick <cmd>                                # one-shot without activating
mamba env update -n matchstick -f environment.yml --prune    # rebuild after spec changes
```

Sanity check after activation: `python -c "import pyxel; print(pyxel.VERSION)"` should print `2.9.4`.

## Branching strategy

This repo uses **Git Flow** with abbreviated prefixes, hybridized with the global `esbailey/issue-<n>-<desc>` naming rule where it fits.

| Type | Prefix | Branch name pattern | Cut from → merged to |
| --- | --- | --- | --- |
| Feature | `ft` | `ft/esbailey/issue-<n>-<short-kebab-desc>` | `develop` → `develop` |
| Release | `rc` | `rc/v<MAJOR>.<MINOR>.<PATCH>` | `develop` → `main` *and* `develop` (tag on `main`) |
| Hotfix  | `hf` | `hf/esbailey/issue-<n>-<short-kebab-desc>` | `main` → `main` *and* `develop` (tag on `main`) |

When no GitHub issue exists for a feature/hotfix, use `ft/esbailey/<short-kebab-desc>` (or `hf/...`) and prompt the user to consider filing one — per the global convention.

Long-lived branches:

- `main` — production-ready; contains only the initial seed commit plus tagged release-merge commits. Never commit feature work directly here.
- `develop` — integration branch; all feature merges land here. This is the working branch by default.

Pushes are always manual; do not push branches or tags without explicit instruction.

## Common commands

All commands assume the matchstick env is active (`mamba activate matchstick`). To run a one-shot without activating, prefix with `mamba run -n matchstick`.

| Task | Command |
| --- | --- |
| Install package in editable mode | `pip install -e .` |
| Run the game (module form) | `python -m matchstick_man` |
| Run the game (console script) | `matchstick-man` |
| Run all tests | `pytest` |
| Run a single test | `pytest tests/test_smoke.py::test_version_is_nonempty_string` |
| Lint | `ruff check .` |
| Auto-format | `ruff format .` |
| Build HTML docs | `cd docs && make html` (output: `docs/build/html/`) |
| Rebuild docs from clean | `cd docs && make clean html` |
| Update conda env from spec | `mamba env update -n matchstick -f environment.yml --prune` |
| Regenerate sprite resources | `python tools/gen_resources.py` |
| Web export | `pyxel app2html src/matchstick_man` |

## Architecture map

Everything below is the current state of the code. Update this map when modules move or new ones are added.

- **`src/matchstick_man/__init__.py`** — package marker; declares `__version__`. Hatchling's `[tool.hatch.version]` reads it as the single source of truth for the project version.
- **`src/matchstick_man/__main__.py`** — defines `main()`, which does `App().run()`. Wired as the `matchstick-man` console script via `[project.scripts]`.
- **`src/matchstick_man/app.py`** — defines `class App`. `__init__` calls `pyxel.init(WIDTH, HEIGHT, title=TITLE)`, loads `matchstick.pyxres`, builds a `Level` from `LEVEL_1`, and spawns `Player` at the defined tile spawn point. `update()` snapshots `prev_x/prev_y`, polls input, calls `player.update()`, then hands off to `resolve_collisions()`. `draw()` iterates the tile grid (drawing colored rectangles per `TILE_COLOR`) then blits the player sprite. The init/run split is deliberate — it lets tests construct `App` without blocking. `WIDTH`, `HEIGHT`, and `TITLE` are inlined; promote to a `constants.py` only when there are >10 game constants.
- **`src/matchstick_man/player.py`** — defines `PlayerState` (enum: HEADED / BURNING / HEADLESS / DEAD) and `class Player`. `Player` exposes `can_jump`, `can_light_fuses`, `burn_frames_remaining` as read-only properties; event handlers `hit_rough_ceiling()`, `hit_water()`, `pickup_matchbook()`; and `update()` for per-frame burn-timer advancement. Physics methods: `apply_input(*, left, right, jump, jump_held)`, `land(floor_y)`, `bonk_ceiling(ceiling_y)`, `leave_ground()`. Horizontal velocity locked while airborne (air control disabled). DEAD is terminal; physics frozen on death. No Pyxel dependency — pure logic.
- **`src/matchstick_man/tiles.py`** — tile system with no Pyxel dependency. `TileKind` enum (EMPTY / FLOOR / WALL / ROUGH / SMOOTH / WATER / MATCHBOOK). `Level` parses character-string rows into a 2-D grid, provides `get(tx, ty)` (OOB → EMPTY) and `clear(tx, ty)` (consumed pickups). `resolve_collisions(player, level, prev_x, prev_y, sprite_size)` performs AABB push-back using previous-position entry-direction logic; fires `player.land()`, `player.bonk_ceiling()`, `player.hit_rough_ceiling()`, `player.hit_water()`, and `player.pickup_matchbook()` as appropriate.
- **`src/matchstick_man/levels.py`** — level data module. `LEVEL_1` is a 32-column × 30-row list of strings encoding the first level: rough ceiling (row 0), smooth ceiling strip (row 1), open air with mid-level platforms (rows 2–23), water pool (rows 24–25), matchbook pickup (row 27), solid floor (rows 28–29), walls at columns 0 and 31.
- **`src/matchstick_man/assets/matchstick.pyxres`** — Pyxel resource file (zip/TOML, binary). Image bank 0 holds three 16×16 sprites at u=0 (HEADED), u=16 (BURNING), u=32 (HEADLESS). Generated by `tools/gen_resources.py`; committed as a binary artifact. Transparent color = 0 (black).
- **`tools/gen_resources.py`** — standalone script that defines all sprite pixel data as hex-string lists and writes `matchstick.pyxres` via `pyxel.init()` + `pyxel.images[0].set()` + `pyxel.save()`. Re-run after any sprite change. Pyxel opens a 16×16 window briefly — this is expected.
- **`tests/`** — pytest suite. `test_smoke.py` checks the package version string; `test_player.py` covers every state transition, capability flag, physics constant, and air-control behavior; `test_tiles.py` covers `Level` construction/access and all `resolve_collisions` paths (floor, ceiling, wall, water, matchbook). 98 tests total.
- **`docs/`** — Sphinx documentation. `docs/source/conf.py` configures the Read the Docs theme, the numpydoc extension (NumPy-style docstrings), and adds `src/` to `sys.path` for autodoc. PlantUML diagrams live in `docs/diagrams/` and are embedded in the Sphinx output via `sphinxcontrib-plantuml`.

**Not yet present** (deliberately deferred to subsequent feature branches):

- Fuse entities and detonation logic.
- Score system (completion-time based).
- Animation frames (walk cycle, jump, etc.) — current sprites are static, one per state.
- Multiple levels / level progression.
- Sound effects and music.
- `LICENSE` file (license choice deferred).
