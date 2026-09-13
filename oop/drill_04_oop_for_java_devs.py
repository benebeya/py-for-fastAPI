"""DRILL 04 — PYTHON OOP: ONLY THE DELTA FROM JAVA   run: uv run oop/drill_04_oop_for_java_devs.py"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol
from pydantic import BaseModel

# 1. CLASS vs INSTANCE ATTRIBUTES — a mutable CLASS attribute is shared state
class Bad:
    items: list[str] = []                        # ONE list for the whole program
    def add(self, x): self.items.append(x)
class Good:
    def __init__(self): self.items: list[str] = []
    def add(self, x): self.items.append(x)
b1, b2 = Bad(), Bad();   b1.add("wine")
g1, g2 = Good(), Good(); g1.add("wine")
print("1  leaked:", b2.items, "| isolated:", g2.items)
# Lookup: instance __dict__ -> class -> bases. `self.x = v` always writes to the
# INSTANCE, shadowing the class attribute rather than editing it.

# 2. *** AN ANNOTATION WITH NO VALUE ASSIGNS NOTHING *** — the real Java jump
class Declared:
    name: str                                    # no assignment happens at all
    qty: int = 0                                 # this one IS a class attribute
print("2  __annotations__:", Declared.__annotations__, "| has .name?", hasattr(Declared,"name"))
class User(BaseModel):
    name: str
print("2  pydantic read those annotations and built:", User(name="med"))
# Its METACLASS reads __annotations__ at class-creation time and generates
# __init__ + validators. You are leaving metadata for a library, not declaring
# storage — closer to a Java annotation processor than to `String name;`.
# SQLAlchemy's Mapped[str] works the same way.

# 3. @property — expose the attribute now, add logic later, callers never change
class Stock:
    def __init__(self, q): self._q = q
    @property
    def qty(self): return self._q
    @qty.setter
    def qty(self, v):
        if v < 0: raise ValueError("negative")
        self._q = v
s = Stock(10); s.qty = 4
print("3  property:", s.qty)
# There is no `private`: `_x` is convention, `__x` is name-mangled to _Cls__x.
# Neither is enforced by anything.

# 4. @dataclass = Java record.  @classmethod = alternative constructor.
@dataclass
class Item:
    name: str
    qty: int = 0
    tags: list[str] = field(default_factory=list)      # NOT tags: list = []
    @classmethod
    def parse(cls, s): n, q = s.split(":"); return cls(n, int(q))
print("4  classmethod:", Item.parse("wine:500"), "| free __eq__:", Item("a") == Item("a"))
# pydantic's model_validate_json is a classmethod too: User.model_validate_json(j),
# NOT user.model_validate_json(j) as in your pydantic_basic.py:27 — that works
# but ignores the instance entirely.
# dataclass = structure only. BaseModel = structure + runtime validation + JSON.

# 5. INTERFACES: Protocol = structural (nothing to inherit), ABC = nominal (enforced)
class Repo(Protocol):
    def get(self, k: str) -> str | None: ...
class BaseRepo(ABC):
    @abstractmethod
    def get(self, k): ...
class Mem(BaseRepo):
    def get(self, k): return {"wine": "500"}.get(k)
print("5  abc:", Mem().get("wine"))
try: BaseRepo()
except TypeError as e: print("5  abstract enforced:", str(e)[:46])

# 6. super() = "NEXT IN THE MRO", not "my parent". With class Both(L, P), a super()
#    call inside L routes to P, not to their shared base — that is what makes mixins
#    work. Check any hierarchy with:  [c.__name__ for c in Both.__mro__]

# 7. DUNDERS you'll define: __repr__ __str__ __eq__ __hash__ __lt__ __len__ __bool__
#    Defining __eq__ sets __hash__ to None unless you define __hash__ too.

# ===================== EXERCISES — fill in, then uncomment =====================
class Basket:                                   # E1 fix the leak, keep add() as-is
    contents: list[str] = []
    def add(self, i): self.contents.append(i)
# x, y = Basket(), Basket(); x.add("wine"); assert y.contents == []

class Temperature:                              # E2 read/write `fahrenheit` property
    def __init__(self, c): self.celsius = c
# t = Temperature(100); assert t.fahrenheit == 212
# t.fahrenheit = 32;    assert t.celsius == 0

class Version:                                  # E3 sortable AND printable — which dunders?
    def __init__(self, *p): self.parts = p
# assert str(Version(1,2,3)) == "1.2.3" and Version(1,2,3) < Version(1,10,0)

# E4 Protocol `Priced` (.price: float) + cheapest(items); must accept a dataclass AND
#    a Pydantic model, neither of which knows Priced exists
