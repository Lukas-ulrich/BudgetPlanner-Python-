def ensure_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def test_ensure_float_valid_input():
    assert ensure_float("10") == 10.0
    assert ensure_float(5) == 5.0
    assert ensure_float(3.5) == 3.5


def test_ensure_float_invalid_input():
    assert ensure_float("abc") == 0.0
    assert ensure_float("") == 0.0
    assert ensure_float(None) == 0.0
