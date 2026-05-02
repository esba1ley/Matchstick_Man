"""Smoke tests confirming the package imports and exposes its version."""

import matchstick_man


def test_version_is_nonempty_string():
    assert isinstance(matchstick_man.__version__, str)
    assert matchstick_man.__version__
