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
| Web export *(no assets yet)* | `pyxel app2html src/matchstick_man` |

## Architecture map

Everything below is the current state of the code. Update this map when modules move or new ones are added.

- **`src/matchstick_man/__init__.py`** — package marker; declares `__version__`. Hatchling's `[tool.hatch.version]` reads it as the single source of truth for the project version.
- **`src/matchstick_man/__main__.py`** — defines `main()`, which does `App().run()`. Wired as the `matchstick-man` console script via `[project.scripts]`.
- **`src/matchstick_man/app.py`** — defines `class App`. `__init__` calls `pyxel.init(WIDTH, HEIGHT, title=TITLE)`; `run()` enters the blocking `pyxel.run(self.update, self.draw)` loop. The init/run split (vs. Pyxel's bundled examples, which call `pyxel.run` from inside `__init__`) is deliberate — it lets tests construct `App` without blocking. `WIDTH`, `HEIGHT`, and `TITLE` are inlined at the top of the module; promote to a `constants.py` only when there are >10 game constants.
- **`src/matchstick_man/player.py`** — defines `PlayerState` (enum: HEADED / BURNING / HEADLESS / DEAD) and `class Player`. `Player` exposes `can_jump`, `can_light_fuses`, `burn_frames_remaining` as read-only properties; event handlers `hit_rough_ceiling()`, `hit_water()`, `pickup_matchbook()`; and `update()` for per-frame burn-timer advancement. DEAD is terminal. The burn duration defaults to `BURN_DURATION_FRAMES` (150 frames ≈ 5 s at 30 fps) but is injectable via the constructor for testing. `player.py` has no Pyxel dependency — pure logic.
- **`tests/`** — pytest suite. `test_smoke.py` checks the package version string; `test_player.py` (32 tests) covers every state transition, no-op guard, and capability flag in the player state machine.
- **`docs/`** — Sphinx documentation. `docs/source/conf.py` configures the Read the Docs theme, the numpydoc extension (NumPy-style docstrings), and adds `src/` to `sys.path` for autodoc.

**Not yet present** (deliberately deferred to subsequent feature branches):

- A `.pyxres` resource file for sprites/tilemaps/sfx/music.
- Tile material classification (`rough` / `smooth`), water tiles, matchbook pickups wired into collision detection.
- Level data and the level loader.
- `LICENSE` file (license choice deferred).
