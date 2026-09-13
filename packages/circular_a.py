"""Half of a circular-import demo — see drill_08 section 6.
`from X import name` is the form that actually breaks: it needs the NAME to
exist right now, and on the second pass through the cycle it does not yet."""
from circular_b import b_func


def a_func() -> str:
    return "a -> " + b_func()
