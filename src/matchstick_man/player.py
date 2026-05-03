"""Player entity and state machine for Matchstick Man.

The central mechanic is a three-state lifecycle driven by ceiling material,
water contact, and matchbook pickups:

    HEADED → (rough ceiling) → BURNING → (water) → HEADLESS → (matchbook) → HEADED
    BURNING → (timer expires) → DEAD

DEAD is terminal; no transitions leave it.
"""

from __future__ import annotations

from enum import Enum, auto

# Frames spent in BURNING before the player dies.  Pyxel runs at 30 fps by
# default, so 150 frames ≈ 5 seconds — enough time to reach water or a fuse.
BURN_DURATION_FRAMES: int = 150


class PlayerState(Enum):
    """Discrete states of the player's head-fire lifecycle."""

    HEADED = auto()
    BURNING = auto()
    HEADLESS = auto()
    DEAD = auto()


class Player:
    """Player entity tracking state transitions and movement capabilities.

    Parameters
    ----------
    burn_duration : int, optional
        Frames the BURNING state lasts before transitioning to DEAD.
        Defaults to ``BURN_DURATION_FRAMES`` (150 frames at 30 fps ≈ 5 s).
        Pass a smaller value in tests to keep test counts low.
    """

    def __init__(self, burn_duration: int = BURN_DURATION_FRAMES) -> None:
        self._burn_duration = burn_duration
        self.state: PlayerState = PlayerState.HEADED
        self._burn_frames_remaining: int = 0

    # ------------------------------------------------------------------
    # Derived capabilities — queried each frame by movement / interaction code
    # ------------------------------------------------------------------

    @property
    def can_jump(self) -> bool:
        """Return True when the player is allowed to jump."""
        return self.state in (PlayerState.HEADED, PlayerState.BURNING)

    @property
    def can_light_fuses(self) -> bool:
        """Return True when the player's ignited head can light a fuse."""
        return self.state in (PlayerState.HEADED, PlayerState.BURNING)

    @property
    def burn_frames_remaining(self) -> int:
        """Frames left before a burning player dies; 0 when not BURNING."""
        return self._burn_frames_remaining

    # ------------------------------------------------------------------
    # Event handlers — called by collision / pickup detection each frame
    # ------------------------------------------------------------------

    def hit_rough_ceiling(self) -> None:
        """Ignite the player's head on contact with a rough ceiling tile.

        Transitions HEADED → BURNING and starts the burn timer.
        No-op in all other states (already burning, headless, or dead).
        """
        if self.state is PlayerState.HEADED:
            self.state = PlayerState.BURNING
            self._burn_frames_remaining = self._burn_duration

    def hit_water(self) -> None:
        """Extinguish the player's head on contact with a water tile.

        Transitions BURNING → HEADLESS and clears the burn timer.
        No-op in all other states.
        """
        if self.state is PlayerState.BURNING:
            self.state = PlayerState.HEADLESS
            self._burn_frames_remaining = 0

    def pickup_matchbook(self) -> None:
        """Restore the player's head via a matchbook pickup.

        Transitions HEADLESS → HEADED.
        No-op in all other states.
        """
        if self.state is PlayerState.HEADLESS:
            self.state = PlayerState.HEADED

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Advance the player state by one frame.

        When BURNING, decrements the burn timer and transitions to DEAD
        when it reaches zero.  No-op in all other states.
        """
        if self.state is PlayerState.BURNING:
            self._burn_frames_remaining -= 1
            if self._burn_frames_remaining <= 0:
                self.state = PlayerState.DEAD
