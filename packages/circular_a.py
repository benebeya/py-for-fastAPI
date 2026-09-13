"""Half of a circular-import demo. See drill_08 section 7."""
import circular_b


def a_func() -> str:
    return "a -> " + circular_b.b_func()
