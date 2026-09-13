"""DRILL 03 — DECORATORS: until @app.get("/x") is boring   run: uv run decorators/drill_03_decorators.py"""
import functools, inspect

# 1. A DECORATOR IS A CLOSURE, and @ is pure sugar:  @deco over `def f`  ==  f = deco(f)
def multiplier(n):
    def inner(x): return x * n          # `n` survives after multiplier() returned
    return inner
print("1  closure:", multiplier(3)(5))

# 2. YOUR ex.py BUG — wrapper() takes no args, so it dies on any real function,
#    and it never returns what the wrapped function returned.
def broken(func):
    def wrapper(): func()
    return wrapper
@broken
def greet(name): print(name)
try: greet("med")
except TypeError as e: print("2  breaks ->", e)

def better(func):
    @functools.wraps(func)              # see 3
    def wrapper(*args, **kwargs):       # accept ANY signature...
        return func(*args, **kwargs)    # ...and give the result BACK
    return wrapper

# 3. functools.wraps KEEPS THE IDENTITY. This is the FastAPI-critical one.
def naked(func):
    def wrapper(*a, **k): return func(*a, **k)
    return wrapper
@naked
def x1(product: str, qty: int) -> dict: return {}
@better
def x2(product: str, qty: int) -> dict: return {}
print("3  no wraps:", x1.__name__, inspect.signature(x1))
print("3  wraps:   ", x2.__name__, inspect.signature(x2))
# FastAPI builds validation by READING that signature. Without wraps it sees
# (*a, **k) — no typed params — and validation on that route silently dies.

# 4. A DECORATOR WITH ARGUMENTS NEEDS 3 LEVELS, because @app.get("/x") is CALLED first
def repeat(times):                      # L1: the decorator's own args
    def decorator(func):                # L2: the function
        @functools.wraps(func)
        def wrapper(*a, **k):           # L3: the call's args
            for _ in range(times): r = func(*a, **k)
            return r
        return wrapper
    return decorator
@repeat(times=3)
def ping(): return "pong"
print("4  ping = repeat(3)(ping) ->", ping())

# 5. THE REAL PATTERN: @app.get does NOT wrap. It REGISTERS and hands you back untouched.
class MiniApp:
    def __init__(self): self.routes = {}
    def get(self, path):
        def decorator(func): self.routes[("GET", path)] = func; return func   # unchanged!
        return decorator
    def handle(self, m, p, **kw):
        h = self.routes.get((m, p)); return h(**kw) if h else {"error": 404}
app = MiniApp()
@app.get("/warehouse")
def read(product: str): return {"product": product}
print("5  routes:", list(app.routes), "|", app.handle("GET","/warehouse",product="wine"))
print("5  still a plain function:", read("olives"))   # why endpoints are unit-testable

# 6. Stacking applies bottom-up. @property/@classmethod/@staticmethod/@functools.cache are built in.

# ===================== EXERCISES — fill in, then uncomment =====================
def logged(func): pass              # E1 print the call, return result, keep __name__
# @logged
# def mul(a,b): return a*b
# assert mul(3,4) == 12 and mul.__name__ == "mul"

def ensure_positive(func): pass     # E2 raise ValueError if any positional arg is negative

def retry(times): pass              # E3 three levels: re-call on exception, up to `times`
# tries = []
# @retry(times=3)
# def flaky():
#     tries.append(1)
#     if len(tries) < 3: raise RuntimeError
#     return "ok"
# assert flaky() == "ok" and len(tries) == 3

# E4 add .post() to MiniApp so handle("POST","/warehouse",product="x") works
# E5 put a wraps-LESS decorator on a hinted function, print inspect.signature(),
#    then write one comment on why FastAPI would break on that route
