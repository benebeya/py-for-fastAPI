"""
DRILL 03 — DECORATORS

Goal: by the end of this file, `@app.get("/items")` should look boring.

Your ex.py has the shape right but the wrapper takes no arguments, which is
two levels below what FastAPI needs. We build up from there.

Run it:  uv run decorators/drill_03_decorators.py
"""

import functools
import inspect
import time
from collections.abc import Callable
from typing import Any


# ==========================================================================
# 1. FUNCTIONS ARE OBJECTS
# ==========================================================================
# Everything else follows from this. A function is a value: you can name it,
# pass it, return it, store it in a list.

def shout(text: str) -> str:
    return text.upper() + "!"

yell = shout                       # no parentheses = the function itself
print("1.1  aliased:", yell("wine"))
print("1.2  as data:", [f("x") for f in (shout, str.strip)][0])
print("1.3  has attributes:", shout.__name__, "|", shout.__doc__)


# ==========================================================================
# 2. CLOSURES — the actual mechanism
# ==========================================================================
# An inner function remembers the variables of the outer call, even after
# that call has returned. A decorator is just a closure over `func`.

def multiplier(n: int) -> Callable[[int], int]:
    def inner(x: int) -> int:
        return x * n               # `n` survives after multiplier() returns
    return inner

triple = multiplier(3)
print("2.1  closure:", triple(5))
print("2.2  captured cell:", triple.__closure__[0].cell_contents)

# To REBIND an outer variable (not just read it) you need `nonlocal`:
def counter() -> Callable[[], int]:
    count = 0
    def tick() -> int:
        nonlocal count             # without this: UnboundLocalError
        count += 1
        return count
    return tick

t = counter()
print("2.3  nonlocal:", t(), t(), t())


# ==========================================================================
# 3. FROM MANUAL WRAPPING TO @
# ==========================================================================
def my_decorator(func):
    def wrapper():
        print("     before")
        func()
        print("     after")
    return wrapper

def say_hello():
    print("     hello!")

# The @ symbol is pure sugar. These two are identical:
print("3.1  manual:")
say_hello_wrapped = my_decorator(say_hello)
say_hello_wrapped()

@my_decorator
def say_hi():
    print("     hi!")
print("3.2  with @:")
say_hi()
# `@my_decorator` above `def say_hi` means exactly:
#     say_hi = my_decorator(say_hi)


# ==========================================================================
# 4. THE BUG IN YOUR ex.py — wrapper must accept arguments
# ==========================================================================
@my_decorator
def greet(name):
    print(f"     hello {name}!")

try:
    greet("med")
except TypeError as e:
    print("4.1  breaks ->", e)

# Fix: *args/**kwargs makes the wrapper accept ANY signature, and you must
# RETURN what the wrapped function returned (your version dropped it).

def better_decorator(func):
    def wrapper(*args, **kwargs):
        print("     before")
        result = func(*args, **kwargs)      # forward everything
        print("     after")
        return result                        # give the value back
    return wrapper

@better_decorator
def add(a, b):
    return a + b

print("4.2  works + returns:", add(2, 3))


# ==========================================================================
# 5. functools.wraps — non-negotiable
# ==========================================================================
# Without it, the decorated function is wearing the wrapper's identity.

@better_decorator
def load_truck(product: str, qty: int) -> dict[str, int]:
    """Load product onto truck."""
    return {product: qty}

print("5.1  name:     ", load_truck.__name__)          # 'wrapper'  <-- wrong
print("5.2  docstring:", load_truck.__doc__)           # None       <-- wrong
print("5.3  signature:", inspect.signature(load_truck))# (*args, **kwargs) <-- wrong

def good_decorator(func):
    @functools.wraps(func)          # copies __name__, __doc__, __annotations__...
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@good_decorator
def load_truck2(product: str, qty: int) -> dict[str, int]:
    """Load product onto truck."""
    return {product: qty}

print("5.4  name:     ", load_truck2.__name__)
print("5.5  docstring:", load_truck2.__doc__)
print("5.6  signature:", inspect.signature(load_truck2))   # the REAL one
print("5.7  unwrap to original:", load_truck2.__wrapped__.__name__)

# WHY THIS MATTERS FOR FASTAPI, concretely:
# FastAPI builds validation by READING your route's signature. Put a
# wraps-less decorator on a route and FastAPI sees `(*args, **kwargs)`,
# finds no typed parameters, and your endpoint silently stops validating
# — or crashes. `@functools.wraps` is what keeps the hints visible.


# ==========================================================================
# 6. DECORATORS THAT TAKE ARGUMENTS — three levels
# ==========================================================================
# `@app.get("/items")` has parentheses, so it is CALLED first, and whatever
# it returns is then used as the decorator. That needs one more layer:
#
#   level 1: takes the decorator's own arguments   -> returns level 2
#   level 2: takes the function                    -> returns level 3
#   level 3: takes the call's arguments            -> returns the result

def repeat(times: int):                       # level 1
    def decorator(func):                      # level 2
        @functools.wraps(func)
        def wrapper(*args, **kwargs):         # level 3
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def ping():
    print("     ping")

print("6.1  repeat(3):")
ping()

# Unrolled, that line means:
#     ping = repeat(times=3)(ping)
# Exactly the shape of:
#     read_items = app.get("/items")(read_items)


# ==========================================================================
# 7. THE REAL FASTAPI PATTERN — registration, not wrapping
# ==========================================================================
# Surprise: @app.get() does NOT wrap your function. It records it in a
# routing table and hands it back untouched. Here is a working miniature.

class MiniApp:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Callable[..., Any]] = {}

    def get(self, path: str):
        def decorator(func):
            self.routes[("GET", path)] = func     # register
            return func                           # return UNCHANGED
        return decorator

    def handle(self, method: str, path: str, **params: Any) -> Any:
        handler = self.routes.get((method, path))
        if handler is None:
            return {"error": 404}
        return handler(**params)

app = MiniApp()

@app.get("/warehouse")
def read_warehouse(product: str) -> dict[str, str]:
    return {"product": product}

print("7.1  registered routes:", list(app.routes))
print("7.2  dispatched:", app.handle("GET", "/warehouse", product="wine"))
print("7.3  unknown path:", app.handle("GET", "/nope"))
print("7.4  still callable directly:", read_warehouse("olives"))
# 7.4 is the giveaway: your route function is completely normal afterwards.
# That is why you can unit-test FastAPI endpoints by just calling them.


# ==========================================================================
# 8. STACKING — bottom-up
# ==========================================================================
def tag(label: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return f"<{label}>{func(*args, **kwargs)}</{label}>"
        return wrapper
    return decorator

@tag("outer")
@tag("inner")
def content() -> str:
    return "hi"

print("8.1  stacked:", content())
# Applied bottom-up: content = tag("outer")(tag("inner")(content))
# So "inner" ends up closest to the text.


# ==========================================================================
# 9. USEFUL DECORATORS FROM THE STDLIB
# ==========================================================================
@functools.cache                    # memoise on the arguments
def slow_square(n: int) -> int:
    time.sleep(0.05)
    return n * n

start = time.perf_counter()
slow_square(12); slow_square(12); slow_square(12)
print(f"9.1  cache: 3 calls in {time.perf_counter() - start:.3f}s (1 was real)")
print("9.2  cache stats:", slow_square.cache_info())

# A timing decorator — the classic one you'll actually reuse:
def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:                           # runs even if func raises
            print(f"     {func.__name__} took {time.perf_counter() - t0:.4f}s")
    return wrapper

@timed
def work() -> str:
    time.sleep(0.02)
    return "done"

print("9.3  timed:", work())


# ==========================================================================
# 10. DECORATING METHODS
# ==========================================================================
# A method is just a function whose first parameter is `self`. *args catches
# it automatically — no special handling needed.

class Warehouse:
    def __init__(self) -> None:
        self.stock = {"wine": 500}

    @good_decorator
    def take(self, product: str, n: int) -> int:
        self.stock[product] -= n
        return self.stock[product]

    @property                    # built-in decorator: call it without ()
    def total(self) -> int:
        return sum(self.stock.values())

    @staticmethod                # no self, just namespaced under the class
    def units() -> str:
        return "bottles"

w = Warehouse()
print("10.1 decorated method:", w.take("wine", 100))
print("10.2 property:", w.total)
print("10.3 staticmethod:", Warehouse.units())


# ==========================================================================
# EXERCISES — replace `pass`, then uncomment the asserts.
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# Write `logged` so it prints the call then returns the result unchanged.
# Must work on any signature and preserve __name__.
def logged(func):
    pass
# @logged
# def mul(a, b): return a * b
# assert mul(3, 4) == 12
# assert mul.__name__ == "mul"

# --- E2 -------------------------------------------------------------------
# `ensure_positive` raises ValueError if ANY positional arg is negative,
# otherwise calls through.
def ensure_positive(func):
    pass
# @ensure_positive
# def ship(qty): return qty
# assert ship(5) == 5
# try:
#     ship(-1); assert False, "should have raised"
# except ValueError: pass

# --- E3 -------------------------------------------------------------------
# A decorator WITH an argument: `retry(times)` re-calls the function when it
# raises, up to `times` attempts, then lets the last exception escape.
def retry(times: int):
    pass
# attempts = []
# @retry(times=3)
# def flaky():
#     attempts.append(1)
#     if len(attempts) < 3: raise RuntimeError("boom")
#     return "ok"
# assert flaky() == "ok" and len(attempts) == 3

# --- E4 -------------------------------------------------------------------
# Add `post` to MiniApp so this works, then dispatch to it.
# @app.post("/warehouse")
# def create(product: str) -> dict[str, str]: return {"created": product}
# assert app.handle("POST", "/warehouse", product="olives") == {"created": "olives"}

# --- E5 -------------------------------------------------------------------
# Why does this print "setting up" only ONCE, before any call?
# Fix it so "setting up" prints on every call instead.
def broken_setup(func):
    print("     setting up")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# --- E6 -------------------------------------------------------------------
# Take your E1 `logged`, drop the functools.wraps, put it on a function with
# type hints, and print inspect.signature(). Explain in a comment why FastAPI
# would fail on that route. (No assert — just convince yourself.)

print("Uncomment the asserts as you solve each one. Silence = all passed.")
