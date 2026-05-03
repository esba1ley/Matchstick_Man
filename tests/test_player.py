"""Tests for the Player state machine."""

from matchstick_man.player import BURN_DURATION_FRAMES, Player, PlayerState


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
