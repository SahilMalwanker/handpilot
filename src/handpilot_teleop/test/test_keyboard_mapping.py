import math
import pytest
from handpilot_teleop.keyboard_node import KeyAction, MotionWindow, map_key


@pytest.mark.parametrize("key,expected", [
    ("w", (0.0, 0.06)), ("s", (0.0, -0.06)),
    ("a", (-0.06, 0.0)), ("d", (0.06, 0.0)),
])
def test_direction(key, expected):
    action = map_key(key, 0.06)
    assert action.kind == "motion"
    assert (action.velocity_x, action.velocity_y) == expected


@pytest.mark.parametrize("key,kind", [
    ("e", "engage"), (" ", "stop"), ("r", "reset"),
    ("q", "quit"), ("x", "ignore"), ("\x1b", "ignore"),
])
def test_actions(key, kind):
    assert map_key(key, 0.06) == KeyAction(kind)


def test_pulse_expires_and_repeat_refreshes():
    window = MotionWindow(0.35)
    window.apply(map_key("w", 0.06), 1.0)
    assert window.sample(1.2) == (0.0, 0.06, True)
    window.apply(map_key("w", 0.06), 1.2)
    assert window.sample(1.4) == (0.0, 0.06, True)
    assert window.sample(1.56) == (0.0, 0.0, False)
    assert window.sample(10.0) == (0.0, 0.0, False)


def test_pulse_is_active_at_exact_start_and_inactive_at_deadline():
    window = MotionWindow(0.35)
    window.apply(map_key("d", 0.06), 0.2)
    assert window.sample(0.2) == (0.06, 0.0, True)
    assert window.sample(0.2 + 0.35) == (0.0, 0.0, False)


@pytest.mark.parametrize("key", [" ", "q", "r"])
def test_stop_actions_clear_motion(key):
    window = MotionWindow(0.35)
    window.apply(map_key("d", 0.06), 0.0)
    window.apply(map_key(key, 0.06), 0.1)
    assert window.sample(0.1) == (0.0, 0.0, False)


def test_engage_discards_old_direction_and_only_opens_zero_pulse():
    window = MotionWindow(0.35)
    window.apply(map_key("d", 0.06), 0.0)
    window.apply(map_key("e", 0.06), 0.1)
    assert window.sample(0.2) == (0.0, 0.0, True)
    assert window.sample(0.5) == (0.0, 0.0, False)


def test_invalid_time_cannot_extend_motion():
    window = MotionWindow(0.35)
    for invalid in (math.nan, math.inf, -1.0):
        window.apply(map_key("d", 0.06), 1.0)
        assert window.sample(invalid) == (0.0, 0.0, False)


@pytest.mark.parametrize("speed", [0.0, -0.1, math.nan, math.inf])
def test_invalid_speed(speed):
    with pytest.raises(ValueError):
        map_key("w", speed)
