"""Tests for the Player state machine and movement physics."""

import pytest

from matchstick_man.player import (
    BURN_DURATION_FRAMES,
    GRAVITY,
    JUMP_VY,
    MAX_FALL_SPEED,
    RUN_SPEED,
    Player,
    PlayerState,
)


class TestInitialState:
    def test_starts_headed(self):
        assert Player().state is PlayerState.HEADED

    def test_can_jump(self):
        assert Player().can_jump is True

    def test_can_light_fuses(self):
        assert Player().can_light_fuses is True

    def test_burn_timer_zero(self):
        assert Player().burn_frames_remaining == 0


class TestHeadedTransitions:
    def test_rough_ceiling_ignites(self):
        p = Player()
        p.hit_rough_ceiling()
        assert p.state is PlayerState.BURNING

    def test_rough_ceiling_sets_timer(self):
        p = Player()
        p.hit_rough_ceiling()
        assert p.burn_frames_remaining == BURN_DURATION_FRAMES

    def test_water_no_effect(self):
        p = Player()
        p.hit_water()
        assert p.state is PlayerState.HEADED

    def test_matchbook_no_effect(self):
        p = Player()
        p.pickup_matchbook()
        assert p.state is PlayerState.HEADED

    def test_update_no_effect(self):
        p = Player()
        p.update()
        assert p.state is PlayerState.HEADED


class TestBurningState:
    def test_can_jump(self):
        p = Player()
        p.hit_rough_ceiling()
        assert p.can_jump is True

    def test_can_light_fuses(self):
        p = Player()
        p.hit_rough_ceiling()
        assert p.can_light_fuses is True

    def test_water_extinguishes(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        assert p.state is PlayerState.HEADLESS

    def test_water_clears_timer(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        assert p.burn_frames_remaining == 0

    def test_rough_ceiling_does_not_reset_timer(self):
        p = Player(burn_duration=50)
        p.hit_rough_ceiling()
        p.update()
        remaining_before = p.burn_frames_remaining
        p.hit_rough_ceiling()
        assert p.burn_frames_remaining == remaining_before
        assert p.state is PlayerState.BURNING

    def test_matchbook_no_effect(self):
        p = Player()
        p.hit_rough_ceiling()
        p.pickup_matchbook()
        assert p.state is PlayerState.BURNING

    def test_timer_decrements_each_frame(self):
        p = Player(burn_duration=10)
        p.hit_rough_ceiling()
        p.update()
        assert p.burn_frames_remaining == 9

    def test_burn_expires_kills(self):
        p = Player(burn_duration=3)
        p.hit_rough_ceiling()
        for _ in range(3):
            p.update()
        assert p.state is PlayerState.DEAD

    def test_burn_not_dead_before_expiry(self):
        p = Player(burn_duration=3)
        p.hit_rough_ceiling()
        for _ in range(2):
            p.update()
        assert p.state is PlayerState.BURNING


class TestHeadlessState:
    def test_cannot_jump(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        assert p.can_jump is False

    def test_cannot_light_fuses(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        assert p.can_light_fuses is False

    def test_matchbook_restores_head(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        p.pickup_matchbook()
        assert p.state is PlayerState.HEADED

    def test_rough_ceiling_no_effect(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        p.hit_rough_ceiling()
        assert p.state is PlayerState.HEADLESS

    def test_water_no_effect(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        p.hit_water()
        assert p.state is PlayerState.HEADLESS

    def test_update_no_effect(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()
        p.update()
        assert p.state is PlayerState.HEADLESS


class TestDeadState:
    def test_cannot_jump(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()
        assert p.can_jump is False

    def test_cannot_light_fuses(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()
        assert p.can_light_fuses is False

    def test_all_events_are_no_ops(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()
        p.hit_rough_ceiling()
        p.hit_water()
        p.pickup_matchbook()
        assert p.state is PlayerState.DEAD

    def test_update_is_no_op(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()
        p.update()
        assert p.state is PlayerState.DEAD

    def test_burn_timer_zero(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()
        assert p.burn_frames_remaining == 0


class TestFullLifecycle:
    def test_headed_burn_water_matchbook_headed(self):
        p = Player()
        assert p.state is PlayerState.HEADED
        p.hit_rough_ceiling()
        assert p.state is PlayerState.BURNING
        p.hit_water()
        assert p.state is PlayerState.HEADLESS
        p.pickup_matchbook()
        assert p.state is PlayerState.HEADED

    def test_headed_burn_expire_dead(self):
        p = Player(burn_duration=2)
        p.hit_rough_ceiling()
        p.update()
        p.update()
        assert p.state is PlayerState.DEAD

    def test_multiple_cycles_before_death(self):
        p = Player()
        for _ in range(3):
            p.hit_rough_ceiling()
            assert p.state is PlayerState.BURNING
            p.hit_water()
            assert p.state is PlayerState.HEADLESS
            p.pickup_matchbook()
            assert p.state is PlayerState.HEADED


# ---------------------------------------------------------------------------
# Physics tests
# ---------------------------------------------------------------------------


class TestInitialPhysics:
    def test_default_position(self):
        p = Player()
        assert p.x == pytest.approx(0.0)
        assert p.y == pytest.approx(0.0)

    def test_custom_position(self):
        p = Player(x=10.0, y=20.0)
        assert p.x == pytest.approx(10.0)
        assert p.y == pytest.approx(20.0)

    def test_starts_on_ground(self):
        assert Player().on_ground is True

    def test_starts_facing_right(self):
        assert Player().facing_right is True

    def test_zero_velocity(self):
        p = Player()
        assert p.vx == pytest.approx(0.0)
        assert p.vy == pytest.approx(0.0)


class TestHorizontalMovement:
    def test_move_right_advances_x(self):
        p = Player()
        p.apply_input(right=True)
        p.update()
        assert p.x == pytest.approx(RUN_SPEED)

    def test_move_left_decreases_x(self):
        p = Player(x=100.0)
        p.apply_input(left=True)
        p.update()
        assert p.x == pytest.approx(100.0 - RUN_SPEED)

    def test_no_input_zero_horizontal_velocity(self):
        p = Player()
        p.apply_input(right=True)
        p.apply_input()  # release
        assert p.vx == pytest.approx(0.0)

    def test_left_and_right_cancel(self):
        p = Player(x=50.0)
        p.apply_input(left=True, right=True)
        p.update()
        assert p.x == pytest.approx(50.0)

    def test_facing_right_on_right_input(self):
        p = Player()
        p.apply_input(right=True)
        assert p.facing_right is True

    def test_facing_left_on_left_input(self):
        p = Player()
        p.apply_input(left=True)
        assert p.facing_right is False

    def test_facing_preserved_when_stopped(self):
        p = Player()
        p.apply_input(left=True)
        p.apply_input()  # release — facing should not change
        assert p.facing_right is False

    def test_releasing_key_in_air_does_not_stop(self):
        p = Player()
        p.apply_input(right=True, jump=True, jump_held=True)  # jump while running
        p.leave_ground()
        p.apply_input(jump_held=True)  # release right key mid-air
        assert p.vx == pytest.approx(RUN_SPEED)

    def test_cannot_change_direction_in_air(self):
        p = Player()
        p.apply_input(right=True, jump=True, jump_held=True)  # jump while running right
        p.leave_ground()
        p.apply_input(left=True, jump_held=True)  # try to go left mid-air
        assert p.vx == pytest.approx(RUN_SPEED)  # velocity unchanged


class TestJump:
    def test_jump_sets_upward_velocity(self):
        p = Player()
        p.apply_input(jump=True, jump_held=True)
        assert p.vy == pytest.approx(JUMP_VY)

    def test_jump_clears_on_ground(self):
        p = Player()
        p.apply_input(jump=True)
        assert p.on_ground is False

    def test_no_second_jump_while_airborne(self):
        p = Player()
        p.apply_input(jump=True)
        p.leave_ground()
        p.update()
        vy_mid_air = p.vy
        p.apply_input(jump=True)  # try again in air
        assert p.vy == pytest.approx(vy_mid_air)

    def test_headless_cannot_jump(self):
        p = Player()
        p.hit_rough_ceiling()
        p.hit_water()  # HEADLESS
        p.apply_input(jump=True)
        assert p.vy == pytest.approx(0.0)
        assert p.on_ground is True

    def test_burning_can_jump(self):
        p = Player()
        p.hit_rough_ceiling()  # BURNING
        p.apply_input(jump=True)
        assert p.vy == pytest.approx(JUMP_VY)


class TestGravity:
    def test_gravity_increases_vy_when_airborne(self):
        p = Player(y=100.0)
        p.leave_ground()
        p.update()
        assert p.vy == pytest.approx(GRAVITY)

    def test_vy_capped_at_max_fall_speed(self):
        p = Player(y=0.0)
        p.leave_ground()
        for _ in range(200):
            p.update()
        assert p.vy == pytest.approx(MAX_FALL_SPEED)

    def test_short_hop_applies_extra_gravity(self):
        # One frame: jump held vs. released — released should gain more vy
        p_held = Player()
        p_held.apply_input(jump=True, jump_held=True)
        p_held.leave_ground()
        p_held.update()
        vy_held = p_held.vy

        p_released = Player()
        p_released.apply_input(jump=True, jump_held=False)
        p_released.leave_ground()
        p_released.update()
        vy_released = p_released.vy

        assert vy_released > vy_held  # short hop converges toward zero faster

    def test_no_short_hop_when_falling(self):
        # Extra gravity only applied while ascending (vy < 0); once falling,
        # only regular GRAVITY is added regardless of jump_held state.
        p = Player(y=100.0)
        p.leave_ground()
        # Advance a few frames to get vy positive but well below MAX_FALL_SPEED
        for _ in range(3):
            p.update()
        assert p.vy > 0  # confirm we're falling
        vy_before = p.vy
        p._jump_held = False
        p.update()
        assert p.vy == pytest.approx(vy_before + GRAVITY)


class TestGroundContact:
    def test_land_snaps_y_to_floor(self):
        p = Player(y=500.0)
        p.leave_ground()
        p.land(200.0)
        assert p.y == pytest.approx(200.0)

    def test_land_zeros_vy(self):
        p = Player()
        p.apply_input(jump=True)
        p.leave_ground()
        p.update()
        p.land(200.0)
        assert p.vy == pytest.approx(0.0)

    def test_land_sets_on_ground(self):
        p = Player()
        p.leave_ground()
        assert p.on_ground is False
        p.land(200.0)
        assert p.on_ground is True

    def test_leave_ground_clears_flag(self):
        p = Player()
        assert p.on_ground is True
        p.leave_ground()
        assert p.on_ground is False

    def test_grounded_player_stable_under_gravity(self):
        # Simulate the game loop: update → leave_ground → land each frame
        p = Player(y=464.0)
        floor_y = 464.0
        for _ in range(10):
            p.update()
            p.leave_ground()
            if p.y >= floor_y:
                p.land(floor_y)
        assert p.y == pytest.approx(floor_y)


class TestDeadPlayerPhysics:
    def test_dead_player_input_zeroes_vx(self):
        p = Player(burn_duration=1)
        p.hit_rough_ceiling()
        p.update()  # → DEAD
        p.apply_input(left=True, right=True, jump=True)
        assert p.vx == pytest.approx(0.0)

    def test_dead_player_physics_frozen(self):
        p = Player(burn_duration=1, y=100.0)
        p.leave_ground()
        p.hit_rough_ceiling()
        p.update()  # → DEAD; physics frozen on this frame too
        y_on_death = p.y
        p.update()
        assert p.y == pytest.approx(y_on_death)
