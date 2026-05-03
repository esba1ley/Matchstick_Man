"""Player entity, state machine, and movement physics for Matchstick Man.

The central mechanic is a three-state lifecycle driven by ceiling material,
water contact, and matchbook pickups:

    HEADED → (rough ceiling) → BURNING → (water) → HEADLESS → (matchbook) → HEADED
    BURNING → (timer expires) → DEAD

DEAD is terminal; no transitions leave it.

Movement physics (horizontal run, variable-height jump, gravity) are also
managed here so that ``app.py`` only needs to poll buttons and forward
collision results.  This module has no Pyxel dependency — all logic is
pure Python arithmetic.
"""

from __future__ import annotations

from enum import Enum, auto

# ---------------------------------------------------------------------------
# State-machine constants
# ---------------------------------------------------------------------------

# Default burn duration in frames.  Pyxel runs at 30 fps, so 150 frames = 5 s.
BURN_DURATION_FRAMES: int = 150

# ---------------------------------------------------------------------------
# Physics constants
# ---------------------------------------------------------------------------

RUN_SPEED: float = 2.0
"""Horizontal speed in pixels per frame."""

JUMP_VY: float = -8.0
"""Initial vertical velocity on jump (negative = upward)."""

GRAVITY: float = 0.5
"""Downward acceleration in pixels per frame squared."""

SHORT_HOP_MULTIPLIER: float = 2.5
"""Gravity multiplier applied when the jump button is released while ascending.
Creates a lower apex for tap-jumps versus held jumps."""

MAX_FALL_SPEED: float = 8.0
"""Terminal downward velocity in pixels per frame."""


class PlayerState(Enum):
    """Discrete states of the player's head-fire lifecycle."""

    HEADED = auto()
    BURNING = auto()
    HEADLESS = auto()
    DEAD = auto()


class Player:
    """Player entity tracking state transitions, capabilities, and physics.

    Parameters
    ----------
    x : float, optional
        Initial horizontal position in pixels.
    y : float, optional
        Initial vertical position in pixels.
    burn_duration : int, optional
        Frames the BURNING state lasts before transitioning to DEAD.
        Defaults to ``BURN_DURATION_FRAMES`` (150 frames at 30 fps ≈ 5 s).
        Pass a smaller value in tests to keep test counts low.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        burn_duration: int = BURN_DURATION_FRAMES,
    ) -> None:
        # --- state machine ---
        self._burn_duration = burn_duration
        self.state: PlayerState = PlayerState.HEADED
        self._burn_frames_remaining: int = 0

        # --- physics ---
        self.x: float = x
        self.y: float = y
        self._vx: float = 0.0
        self._vy: float = 0.0
        self._on_ground: bool = True
        self._jump_held: bool = False
        self._facing_right: bool = True

    # ------------------------------------------------------------------
    # State-machine capabilities
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
    # Physics read-only properties
    # ------------------------------------------------------------------

    @property
    def vx(self) -> float:
        """Current horizontal velocity in pixels per frame."""
        return self._vx

    @property
    def vy(self) -> float:
        """Current vertical velocity in pixels per frame."""
        return self._vy

    @property
    def on_ground(self) -> bool:
        """Return True when the player is standing on a surface."""
        return self._on_ground

    @property
    def facing_right(self) -> bool:
        """Return True when the player sprite should face right."""
        return self._facing_right

    # ------------------------------------------------------------------
    # State-machine event handlers
    # ------------------------------------------------------------------

    def hit_rough_ceiling(self) -> None:
        """Ignite the player's head on contact with a rough ceiling tile.

        Transitions HEADED → BURNING and starts the burn timer.
        No-op in all other states.
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
    # Physics event handlers — called by collision detection each frame
    # ------------------------------------------------------------------

    def apply_input(
        self,
        *,
        left: bool = False,
        right: bool = False,
        jump: bool = False,
        jump_held: bool = False,
    ) -> None:
        """Apply one frame of player input to velocity and facing direction.

        Parameters
        ----------
        left : bool
            Left movement button is currently held.
        right : bool
            Right movement button is currently held.
        jump : bool
            Jump button was pressed this frame (edge trigger).
        jump_held : bool
            Jump button is currently held (sustained).
        """
        if self.state is PlayerState.DEAD:
            self._vx = 0.0
            return

        # Horizontal: only update velocity and facing while grounded.
        # Once airborne the player is committed to the velocity they launched
        # with; direction and speed can only change again on surface contact.
        if self._on_ground:
            if left and not right:
                self._vx = -RUN_SPEED
                self._facing_right = False
            elif right and not left:
                self._vx = RUN_SPEED
                self._facing_right = True
            else:
                self._vx = 0.0

        # Jump: edge trigger, grounded, state must allow it
        if jump and self._on_ground and self.can_jump:
            self._vy = JUMP_VY
            self._on_ground = False

        self._jump_held = jump_held

    def land(self, floor_y: float) -> None:
        """Snap the player onto a floor surface and clear vertical velocity.

        Parameters
        ----------
        floor_y : float
            Y-coordinate of the player's feet when touching the surface
            (i.e. top of the floor tile, or ``screen_height - sprite_height``).
        """
        self.y = floor_y
        self._vy = 0.0
        self._on_ground = True

    def bonk_ceiling(self, ceiling_y: float) -> None:
        """Snap the player's top edge to a ceiling and clear upward velocity.

        Parameters
        ----------
        ceiling_y : float
            Y-coordinate of the player's top edge when touching the ceiling
            (i.e. bottom of the ceiling tile).
        """
        self.y = ceiling_y
        self._vy = 0.0

    def leave_ground(self) -> None:
        """Mark the player as airborne.

        Call this after :meth:`update` and before collision detection each
        frame so that walking off a ledge correctly clears the ground flag.
        """
        self._on_ground = False

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Advance the player state and physics by one frame.

        Processes the burn timer (BURNING → DEAD on expiry), then
        integrates gravity and velocity into position.  Physics is frozen
        once the player reaches DEAD so the game loop can handle respawn
        or game-over without the body continuing to move.
        """
        # State machine: burn timer
        if self.state is PlayerState.BURNING:
            self._burn_frames_remaining -= 1
            if self._burn_frames_remaining <= 0:
                self.state = PlayerState.DEAD

        # Physics: frozen on death
        if self.state is PlayerState.DEAD:
            return

        # Gravity: apply short-hop multiplier when jump released while rising
        gravity = GRAVITY
        if not self._jump_held and self._vy < 0:
            gravity *= SHORT_HOP_MULTIPLIER

        self._vy = min(self._vy + gravity, MAX_FALL_SPEED)

        # Integrate
        self.x += self._vx
        self.y += self._vy
