"""
DRILL 02 — TYPE HINTS (deep)

This is the #1 prerequisite for FastAPI. In most Python code, hints are
optional documentation. In FastAPI they are the PROGRAM: they decide what
gets parsed, validated, injected, and documented.

Run it:  uv run "type Hints/drill_02_type_hints.py"
"""

from typing import Annotated, Any, Literal, Protocol, get_type_hints
from collections.abc import Callable, Iterable, Sequence
from enum import Enum
import inspect


# ==========================================================================
# 1. WHY THIS MATTERS — annotations are real runtime data
# ==========================================================================
# A hint is not a comment. Python stores it on the object, and any library
# can read it back. That is the whole trick behind FastAPI and Pydantic.

def load_truck(product: str, qty: int) -> dict[str, int]:
    return {product: qty}

print("1.1  stored hints:", get_type_hints(load_truck))
print("1.2  via signature:", inspect.signature(load_truck))
# FastAPI reads exactly this to build validation + the OpenAPI docs.


# ==========================================================================
# 2. BUILT-IN GENERICS
# ==========================================================================
# Since 3.9 use the lowercase builtins. `typing.List` / `typing.Dict` are legacy.

names: list[str] = ["med", "bob"]
stock: dict[str, int] = {"wine": 500}
pair: tuple[str, int] = ("wine", 500)        # EXACTLY 2 items, in that order
many: tuple[str, ...] = ("a", "b", "c")      # any number of strings
tags: set[str] = {"new", "sale"}
matrix: list[list[int]] = [[1, 2], [3, 4]]   # they nest

print("2.1  nested generic:", matrix)

# For PARAMETERS, prefer the abstract types from collections.abc — they accept
# more callers. For RETURNS, be concrete so the caller knows what they got.
def total(values: Iterable[int]) -> int:     # list, tuple, set, generator...
    return sum(values)

print("2.2  accepts any iterable:", total([1, 2]), total((3, 4)), total({5, 6}))


# ==========================================================================
# 3. OPTIONAL — "can be None" is NOT the same as "has a default"
# ==========================================================================
# These are two independent things, and mixing them up is the most common
# FastAPI mistake.

def a(q: str | None) -> str:      # REQUIRED, but may be None
    return q or "<none>"

def b(q: str = "hi") -> str:      # OPTIONAL, never None
    return q

def c(q: str | None = None):      # OPTIONAL and may be None  <-- query param
    return q or "<none>"

print("3.1  required-but-nullable:", a(None))
print("3.2  defaulted:", b())
print("3.3  both:", c())

# WRONG, and Pydantic will reject it:
#     def f(q: str = None)      # says "always a str" then defaults to None
# RIGHT:
#     def f(q: str | None = None)
#
# `Optional[str]` is the old spelling of `str | None`. Same thing, prefer `|`.


# ==========================================================================
# 4. UNIONS
# ==========================================================================
def parse_qty(raw: str | int | float) -> int:
    return int(raw)

print("4.1  union:", parse_qty("5"), parse_qty(5.9))

# Narrowing: isinstance tells the type checker which branch you're in.
def describe(v: int | str) -> str:
    if isinstance(v, int):
        return f"int doubled -> {v * 2}"     # here v is definitely int
    return f"str upper -> {v.upper()}"       # here v is definitely str

print("4.2  narrowed:", describe(21), "|", describe("wine"))


# ==========================================================================
# 5. LITERAL and ENUM — closed sets of allowed values
# ==========================================================================
# Literal = "one of exactly these values". FastAPI turns it into a dropdown
# in the docs and a 422 error if you send anything else.

def set_status(status: Literal["pending", "shipped", "cancelled"]) -> str:
    return f"status={status}"

print("5.1  literal:", set_status("shipped"))

class Unit(str, Enum):            # subclassing str keeps it JSON-friendly
    BOXES = "boxes"
    BOTTLES = "bottles"

print("5.2  enum value:", Unit.BOXES.value, "| is a str?", isinstance(Unit.BOXES, str))
# Literal for a handful of inline values; Enum when you reuse the set.


# ==========================================================================
# 6. ANNOTATED — the single most important FastAPI idiom
# ==========================================================================
# Annotated[T, ...extra] means "the type is T, plus metadata for whoever
# cares". Python ignores the extra. Libraries read it.

def ship(qty: Annotated[int, "must be positive"]) -> int:
    return qty

print("6.1  with extras:   ", get_type_hints(ship, include_extras=True))
print("6.2  without extras:", get_type_hints(ship))   # metadata stripped

# 6.1 keeps `Annotated[int, 'must be positive']`; 6.2 collapses it to plain
# `int`. So ordinary code and type checkers see just the type, while a
# library that asks for extras sees the instructions. Both views, one hint.

print("6.3  unwrap by hand:", Annotated[int, "x"].__origin__,
      "| metadata:", Annotated[int, "x"].__metadata__)

# This is how every modern FastAPI signature is written:
#
#     @app.get("/items/{item_id}")
#     def read(
#         item_id: Annotated[int, Path(gt=0)],
#         q:       Annotated[str | None, Query(max_length=50)] = None,
#         db:      Annotated[Session, Depends(get_db)],
#     ): ...
#
# Same shape as above: real type first, library instructions after.
# Here is a miniature version of that machinery, so it stops being magic:

class Inject:
    """Stand-in for FastAPI's Depends()."""
    def __init__(self, factory: Callable[[], Any]):
        self.factory = factory

def get_connection() -> str:
    return "<db connection>"

def handler(db: Annotated[str, Inject(get_connection)], product: str) -> str:
    return f"{product} via {db}"

def call_with_injection(fn: Callable[..., Any], **supplied: Any) -> Any:
    """Read the hints, run any Inject() we find, pass the rest through."""
    resolved = dict(supplied)
    for name, hint in get_type_hints(fn, include_extras=True).items():
        for meta in getattr(hint, "__metadata__", ()):
            if isinstance(meta, Inject):
                resolved[name] = meta.factory()
    return fn(**resolved)

print("6.4  injected:", call_with_injection(handler, product="wine"))
# That ~6-line function is, in essence, what Depends() does.


# ==========================================================================
# 7. CALLABLE — functions are values, and values have types
# ==========================================================================
# Callable[[ArgType, ArgType], ReturnType]

def apply_twice(fn: Callable[[int], int], x: int) -> int:
    return fn(fn(x))

print("7.1  callable:", apply_twice(lambda n: n * 3, 2))

# Callable[..., T] = "any arguments, returns T". Useful for decorators.


# ==========================================================================
# 8. TYPE ALIASES — the `type` statement (3.12+)
# ==========================================================================
type UserId = int
type Catalog = dict[str, tuple[str, int]]

def find(uid: UserId, cat: Catalog) -> str | None:
    return None

print("8.1  alias:", UserId, "| resolves to:", UserId.__value__)
# Aliases are lazy — you can reference a type defined further down the file.


# ==========================================================================
# 9. PROTOCOL — Python's answer to a Java interface
# ==========================================================================
# Java: a class must `implements Serializable` to qualify.
# Python: if it has the right methods, it qualifies. No declaration, no import.
# That is STRUCTURAL typing, and Protocol is how you write it down.

class SupportsQty(Protocol):
    qty: int
    def restock(self, n: int) -> None: ...

class Wine:                       # note: does NOT inherit SupportsQty
    def __init__(self) -> None:
        self.qty = 500
    def restock(self, n: int) -> None:
        self.qty += n

def top_up(item: SupportsQty) -> int:
    item.restock(100)
    return item.qty

print("9.1  structural typing:", top_up(Wine()))   # accepted on shape alone


# ==========================================================================
# 10. GENERICS — PEP 695 syntax (3.12+)
# ==========================================================================
# The [T] after the name declares a type variable. T is "whatever came in",
# so the return type tracks the argument type.

def first[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None

print("10.1 generic on str:", first(["wine", "olives"]))
print("10.2 generic on int:", first([1, 2, 3]))

class Box[T]:
    def __init__(self, item: T) -> None:
        self.item = item
    def get(self) -> T:
        return self.item

print("10.3 generic class:", Box("wine").get())
# You'll meet this as Page[UserRead] in paginated FastAPI responses.


# ==========================================================================
# 11. PYTHON 3.14: ANNOTATIONS ARE LAZY (PEP 649)
# ==========================================================================
# You are on 3.14.6. Annotations are no longer evaluated at def-time —
# they're computed on demand. Forward references just work, with no
# `from __future__ import annotations` and no quotes.

class Node:
    def add_child(self, child: "Node") -> Node:   # bare Node, before it exists
        return child

print("11.1 forward ref resolved:", get_type_hints(Node.add_child))

# Practical upshot: a hint that's wrong or undefined may stay silent until
# something actually reads it. Pydantic reads it at class-creation time,
# so you'll still find out fast.


# ==========================================================================
# 12. HINTS ENFORCE NOTHING — that is Pydantic's job
# ==========================================================================
def strict(qty: int) -> int:
    return qty

print("12.1 lying to the hint:", strict("not an int"))   # runs happily!

# Nothing checks that at runtime. Static checkers (mypy, pyright, your IDE)
# check it before you run. Pydantic/FastAPI check it AT runtime, because they
# read the hint and build a validator from it. Hints alone = documentation.
# Hints + Pydantic = enforcement. That distinction is the whole point.


# ==========================================================================
# EXERCISES — replace `pass` / `...`, then uncomment the asserts.
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# Annotate this correctly: `tags` is optional AND may be None.
# It takes a product name and returns a dict of name -> list of tags.
def build_item(name, tags=None):
    return {name: tags or []}
# assert get_type_hints(build_item)["tags"] == (list[str] | None)

# --- E2 -------------------------------------------------------------------
# Annotate so only "asc" or "desc" are allowed. Use Literal.
def sort_by(field, direction="asc"):
    return f"{field} {direction}"
# assert get_type_hints(sort_by)["direction"] == Literal["asc", "desc"]

# --- E3 -------------------------------------------------------------------
# Make this generic: it should return the SAME type it was given,
# not `Any`. Use PEP 695 syntax.
def last(items):
    return items[-1] if items else None

# --- E4 -------------------------------------------------------------------
# Write a Protocol called `Closeable` describing anything with a
# `.close() -> None` method. Then `drain` should accept it.
# (You'll reuse this exact idea in Drill 06.)
# class Closeable(Protocol): ...
def drain(resource) -> str:
    resource.close()
    return "closed"
# class FakeFile:
#     def close(self) -> None: pass
# assert drain(FakeFile()) == "closed"

# --- E5 -------------------------------------------------------------------
# Use Annotated to attach the string "positive" to an int parameter,
# then read it back out of the metadata.
def order(qty):
    return qty
# meta = get_type_hints(order, include_extras=True)["qty"].__metadata__
# assert meta == ("positive",)

# --- E6 -------------------------------------------------------------------
# Declare a type alias `Row` = tuple of (str, int, bool),
# and `Table` = a list of Row.
# type Row = ...
# type Table = ...
# assert Row.__value__ == tuple[str, int, bool]

# --- E7 -------------------------------------------------------------------
# This signature is wrong in two ways. Fix both.
#   1. a str that defaults to None
#   2. a mutable default (remember Drill 01 §2)
def search(q: str = None, filters: list[str] = []) -> list[str]:
    return filters + ([q] if q else [])

print("Uncomment the asserts as you solve each one. Silence = all passed.")
