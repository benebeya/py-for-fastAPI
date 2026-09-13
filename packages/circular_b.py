"""The other half. This module imports circular_a at MODULE level, which is
what breaks. The fix is in drill_08 section 7."""
import circular_a


def b_func() -> str:
    return "b"
