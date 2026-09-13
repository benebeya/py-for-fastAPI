"""The other half. Imports a NAME from circular_a at module level, which is
what fails. The fixes are listed in drill_08 section 6."""
from circular_a import a_func


def b_func() -> str:
    return "b"
