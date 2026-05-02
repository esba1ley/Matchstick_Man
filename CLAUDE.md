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

## Repository state

As of this file's creation, the repo contains only `CLAUDE.md` and `environment.yml`. **No source code exists yet.** The next scaffolding pass is expected to introduce:

- `pyproject.toml` — project metadata plus ruff and pytest config
- `src/matchstick_man/` — main package; entry point launches the Pyxel `App`
- A Pyxel resource file (`.pyxres`) for sprites, tilemaps, sfx, and music
- `tests/` — pytest suite, with the player state machine as the first thing under test (it's pure logic and the highest-leverage thing to lock down)

When the scaffold lands, **replace this section** with:
1. Concrete run / lint / test / web-build commands.
2. A short architecture map (which module owns the state machine, where tile materials are defined, where level data lives).

Until then, do not invent file paths or module names in suggestions.
