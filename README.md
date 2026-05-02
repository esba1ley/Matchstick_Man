# Matchstick Man

A 2D platformer in 8-bit console aesthetic, built with [Pyxel](https://github.com/kitao/pyxel).

The player controls a matchstick figure — split-bottom legs, ignitable head — that runs, jumps, and swims through hand-crafted levels, ultimately lighting fuses to detonate the level for completion. Score is a function of completion time: faster runs score higher.

## Status

Pre-alpha scaffold. The package opens a black 512×480 window and exits on ESC; no gameplay yet.

## Quick start

```sh
mamba env update -n matchstick -f environment.yml --prune
mamba activate matchstick
pip install -e .
python -m matchstick_man        # or: matchstick-man
```

## Development

```sh
pytest               # unit tests
ruff check .         # lint
ruff format .        # format
cd docs && make html # build documentation (output: docs/build/html/)
```

See [CLAUDE.md](CLAUDE.md) for the design brief, player state machine, and branching strategy.
