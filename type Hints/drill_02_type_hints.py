"""DRILL 02 — TYPE HINTS (the FastAPI prerequisite)   run: uv run "type Hints/drill_02_type_hints.py" """
from typing import Annotated, Literal, Protocol, get_type_hints
from collections.abc import Sequence

# 1. HINTS ARE RUNTIME DATA — libraries read them back. That is ALL of FastAPI.
def load(product: str, qty: int) -> dict[str, int]: return {product: qty}
print("1  readable at runtime:", get_type_hints(load))

# 2. "CAN BE None" != "HAS A DEFAULT" — three genuinely different signatures
def a(q: str | None): ...          # required, may be None
def b(q: str = "hi"): ...          # optional, never None
def c(q: str | None = None): ...   # optional AND nullable  <- the query param
# WRONG: def f(q: str = None) — claims str, defaults None. Pydantic rejects it.
# `Optional[str]` is just the old spelling of `str | None`.

# 3. LITERAL — a closed set. FastAPI turns it into a docs dropdown + a 422.
def sort(dir: Literal["asc", "desc"]) -> str: return dir
print("3  literal:", sort("asc"))

# 4. ANNOTATED — real type first, library instructions after. THE idiom.
def ship(qty: Annotated[int, "positive"]) -> int: return qty
print("4  with extras:", get_type_hints(ship, include_extras=True)["qty"])
print("4  stripped:   ", get_type_hints(ship)["qty"])
#     @app.get("/items/{id}")
#     def read(id:  Annotated[int, Path(gt=0)],
#              q:   Annotated[str | None, Query(max_length=50)] = None,
#              db:  Annotated[Session, Depends(get_db)]): ...

# 5. ...and Depends() is only this. A working version, in five lines:
class Inject:
    def __init__(self, f): self.f = f
def get_db() -> str: return "<conn>"
def handler(db: Annotated[str, Inject(get_db)], product: str) -> str: return f"{product} via {db}"
def call(fn, **given):
    for n, h in get_type_hints(fn, include_extras=True).items():
        for m in getattr(h, "__metadata__", ()):
            if isinstance(m, Inject): given[n] = m.f()
    return fn(**given)
print("5  injected:", call(handler, product="wine"))

# 6. PROTOCOL — a Java interface, but STRUCTURAL: no `implements` anywhere
class HasQty(Protocol):
    qty: int
class Wine: qty = 500                               # never mentions HasQty
def read(x: HasQty) -> int: return x.qty
print("6  structural:", read(Wine()))

# 7. GENERICS (3.12+ syntax) — the return type tracks the argument type
def first[T](xs: Sequence[T]) -> T | None: return xs[0] if xs else None
type UserId = int                                   # `type` = a lazy alias
print("7  generic:", first(["wine"]), first([1,2]), "| alias:", UserId.__value__)

# 8. HINTS ENFORCE NOTHING at runtime. Pydantic is what enforces them.
print("8  lying works fine:", load("x", "not an int"))
# On 3.14 annotations are LAZY (PEP 649): forward refs need no quotes.

# ===================== EXERCISES — fill in, then uncomment =====================
def build(name, tags=None): pass                    # E1 tags: optional AND nullable
# assert get_type_hints(build)["tags"] == (list[str] | None)

def sort_by(field, direction="asc"): pass           # E2 restrict with Literal
# assert get_type_hints(sort_by)["direction"] == Literal["asc","desc"]

def last(xs): pass                                  # E3 make it generic, not Any

def order(qty): pass                                # E4 Annotated[int, "positive"]
# assert get_type_hints(order, include_extras=True)["qty"].__metadata__ == ("positive",)

# E5 Protocol `Closeable` (.close() -> None), then drain(r) calls it
# E6 fix BOTH bugs: def search(q: str = None, filters: list[str] = []) -> list[str]
