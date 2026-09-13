"""
DRILL 04 — PYTHON OOP, FOR SOMEONE WHO KNOWS JAVA

You already have classes, objects, inheritance, polymorphism. This file is
only the DELTA — the places where Python differs enough to bite you, ordered
by how much they matter for Pydantic / SQLAlchemy / FastAPI.

Run it:  uv run oop/drill_04_oop_for_java_devs.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, ClassVar


# ==========================================================================
# 1. THE SMALL SYNTAX DELTAS (30 seconds, then move on)
# ==========================================================================
class Product:
    def __init__(self, name: str, qty: int) -> None:   # the constructor
        self.name = name                                # `self` is EXPLICIT
        self.qty = qty

    def __repr__(self) -> str:                          # like toString()
        return f"Product({self.name!r}, {self.qty})"

p = Product("wine", 500)        # no `new` keyword
print("1.1  instance:", p)
print("1.2  attributes live in a dict:", p.__dict__)

# Objects are open: you can bolt on attributes that were never declared.
p.discount = 0.1
print("1.3  attached at runtime:", p.__dict__)
# Java would reject that at compile time. Python shrugs. (__slots__ can lock
# it down, but you rarely need to.)


# ==========================================================================
# 2. *** CLASS ATTRIBUTES vs INSTANCE ATTRIBUTES ***
# ==========================================================================
# This is THE one that trips up Java developers, and it is unavoidable in
# FastAPI because Pydantic and SQLAlchemy both build on it.

class Warehouse:
    country = "MR"              # CLASS attribute — one copy, shared by all
    def __init__(self, city: str) -> None:
        self.city = city        # INSTANCE attribute — one copy per object

a = Warehouse("nema")
b = Warehouse("nouakchott")
print("2.1  shared:", a.country, b.country)

Warehouse.country = "FR"        # change the class -> every instance sees it
print("2.2  after class change:", a.country, b.country)

a.country = "DZ"                # this does NOT edit the class; it SHADOWS it
print("2.3  a shadows:", a.country, "| b unaffected:", b.country)
print("2.4  a now has its own:", a.__dict__)

# Lookup order: instance __dict__ first, then the class, then base classes.

# THE TRAP — a mutable class attribute is shared state (Drill 01 §2 again,
# wearing a different hat):
class BadCart:
    items: list[str] = []       # ONE list for the whole program
    def add(self, x: str) -> None:
        self.items.append(x)    # mutates the CLASS's list

c1, c2 = BadCart(), BadCart()
c1.add("wine")
print("2.5  leaked between instances:", c2.items)   # ['wine']  <-- bug

class GoodCart:
    def __init__(self) -> None:
        self.items: list[str] = []      # fresh list per instance
    def add(self, x: str) -> None:
        self.items.append(x)

g1, g2 = GoodCart(), GoodCart()
g1.add("wine")
print("2.6  properly isolated:", g2.items)          # []


# ==========================================================================
# 3. *** THE ANNOTATION-ONLY CLASS BODY ***
# ==========================================================================
# Now the payoff. Look at a Pydantic model:
#
#     class User(BaseModel):
#         name: str
#
# In Java, `String name;` declares storage on every instance.
# In Python, `name: str` with NO VALUE assigns nothing at all. It only adds
# an entry to the class's annotations. Watch:

class Declared:
    name: str                   # no assignment happens here
    qty: int = 0                # this one DOES assign a class attribute

print("3.1  annotations:", Declared.__annotations__)
print("3.2  qty exists:", Declared.qty)
try:
    Declared.name
except AttributeError as e:
    print("3.3  name does NOT exist ->", e)

# So what makes Pydantic work? Its metaclass reads __annotations__ when the
# class is CREATED and generates validators + an __init__ from them.
# You are not declaring fields. You are leaving metadata for a library to read.
# The closest Java analogy is an annotation processor, not a field declaration.

from pydantic import BaseModel

class User(BaseModel):
    name: str
    qty: int = 0

print("3.4  pydantic generated __init__:", User(name="med"))
print("3.5  it built a schema:", list(User.model_fields))

# ClassVar is how you tell Pydantic/dataclasses "this one is NOT a field":
class Config(BaseModel):
    version: ClassVar[str] = "1.0"      # excluded from the model
    debug: bool = False                  # a real field

print("3.6  ClassVar excluded:", list(Config.model_fields), "| version:", Config.version)


# ==========================================================================
# 4. NO `private`. NO `public`. JUST CONVENTION.
# ==========================================================================
class Account:
    def __init__(self) -> None:
        self.balance = 100      # public
        self._internal = "hands off, please"   # _ = 'private by convention'
        self.__mangled = "harder to reach"     # __ = name mangling

acc = Account()
print("4.1  underscore is only a hint:", acc._internal)   # nothing stops you
print("4.2  mangled name:", acc._Account__mangled)        # renamed, not hidden
print("4.3  visible in dict:", list(acc.__dict__))

# `__x` exists to avoid accidental collisions in subclasses, NOT for security.
# There is no enforcement anywhere in the language.


# ==========================================================================
# 5. @property — Python has no getters/setters, and doesn't want them
# ==========================================================================
# In Java you write getBalance()/setBalance() up front, in case you ever need
# logic. In Python you expose the attribute directly and convert it to a
# property later IF you need logic. The calling code never changes.

class Stock:
    def __init__(self, qty: int) -> None:
        self._qty = qty

    @property
    def qty(self) -> int:                   # read: stock.qty  (no parens)
        return self._qty

    @qty.setter
    def qty(self, value: int) -> None:      # write: stock.qty = 5
        if value < 0:
            raise ValueError("qty cannot be negative")
        self._qty = value

    @property
    def is_empty(self) -> bool:             # a computed, read-only attribute
        return self._qty == 0

s = Stock(10)
s.qty = 4
print("5.1  property get:", s.qty, "| computed:", s.is_empty)
try:
    s.qty = -1
except ValueError as e:
    print("5.2  setter validated ->", e)


# ==========================================================================
# 6. @classmethod and @staticmethod
# ==========================================================================
class Order:
    tax_rate = 0.2                          # class attribute

    def __init__(self, total: float) -> None:
        self.total = total

    @classmethod
    def from_json(cls, raw: str) -> "Order":
        """Alternative constructor. `cls` is the class, so subclasses work."""
        import json
        return cls(json.loads(raw)["total"])

    @staticmethod
    def currency() -> str:
        """No self, no cls. Just a function living in the class namespace."""
        return "MRU"

    def with_tax(self) -> float:
        return self.total * (1 + self.tax_rate)

o = Order.from_json('{"total": 100}')
print("6.1  classmethod constructor:", o.total)
print("6.2  staticmethod:", Order.currency())
print("6.3  instance method:", o.with_tax())

# You have already used this pattern: in pydantic_basic.py line 27 you wrote
#     user.model_validate_json(json_data)
# model_validate_json is a CLASSMETHOD. It works from the instance, but it
# ignores that instance entirely. What you mean is:
#     User.model_validate_json(json_data)


# ==========================================================================
# 7. DUNDER METHODS — operator overloading, but systematic
# ==========================================================================
class Money:
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def __repr__(self) -> str:          # for developers (debugger, REPL)
        return f"Money({self.amount})"

    def __str__(self) -> str:           # for users (print, f-string)
        return f"{self.amount} MRU"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Money) and self.amount == other.amount

    def __hash__(self) -> int:          # define with __eq__ to stay hashable
        return hash(self.amount)

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __lt__(self, other: "Money") -> bool:
        return self.amount < other.amount

    def __len__(self) -> int:
        return len(str(self.amount))

    def __bool__(self) -> bool:
        return self.amount != 0

m1, m2 = Money(100), Money(50)
print("7.1  repr:", repr(m1), "| str:", str(m1))
print("7.2  __add__:", m1 + m2)
print("7.3  __eq__:", Money(100) == Money(100))
print("7.4  __lt__ enables sorted():", sorted([m1, m2]))
print("7.5  __bool__:", bool(Money(0)), bool(Money(5)))
print("7.6  __hash__ enables set membership:", Money(100) in {Money(100)})

# NOTE: defining __eq__ sets __hash__ to None unless you define it too.
# Python's == / hashCode() contract, enforced by the language.


# ==========================================================================
# 8. dataclasses — when you just want a data holder
# ==========================================================================
# Java records. Generates __init__, __repr__, __eq__ from the annotations.

@dataclass
class Point:
    x: int
    y: int = 0
    tags: list[str] = field(default_factory=list)   # NOT tags: list = []

print("8.1  generated:", Point(1, 2))
print("8.2  free __eq__:", Point(1, 2) == Point(1, 2))
print("8.3  isolated mutable default:", Point(1).tags is not Point(2).tags)

@dataclass(frozen=True)         # immutable + hashable
class Coord:
    lat: float
    lon: float

try:
    Coord(1.0, 2.0).lat = 9.9
except Exception as e:
    print("8.4  frozen ->", type(e).__name__, e)

# dataclass vs Pydantic BaseModel:
#   dataclass  = structure only, NO validation, stdlib, zero cost
#   BaseModel  = structure + runtime validation + JSON, needs pydantic
# Use dataclass for internal objects, BaseModel at your API boundary.


# ==========================================================================
# 9. NO INTERFACES — duck typing, Protocol, and ABC
# ==========================================================================
# Java: `class X implements Repo` — the class must declare the relationship.
# Python has two answers, and they point in opposite directions.

# (a) Protocol — STRUCTURAL. The class declares nothing; shape is enough.
class Repo(Protocol):
    def get(self, key: str) -> str | None: ...

class DictRepo:                          # does not mention Repo at all
    def __init__(self) -> None:
        self._data = {"wine": "500"}
    def get(self, key: str) -> str | None:
        return self._data.get(key)

def lookup(repo: Repo, key: str) -> str:
    return repo.get(key) or "missing"

print("9.1  protocol (structural):", lookup(DictRepo(), "wine"))

# (b) ABC — NOMINAL, the closest thing to a Java abstract class. You must
#     inherit, and Python refuses to instantiate until you implement.
class BaseRepo(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None: ...

    def get_or_raise(self, key: str) -> str:   # shared concrete logic
        v = self.get(key)
        if v is None:
            raise KeyError(key)
        return v

class MemoryRepo(BaseRepo):
    def get(self, key: str) -> str | None:
        return {"wine": "500"}.get(key)

print("9.2  abc:", MemoryRepo().get_or_raise("wine"))

class Incomplete(BaseRepo):
    pass

try:
    Incomplete()
except TypeError as e:
    print("9.3  abstract enforced ->", e)

# Rule of thumb: Protocol when you don't own the classes (or want them
# decoupled); ABC when you own the hierarchy and want shared base logic.


# ==========================================================================
# 10. INHERITANCE, super(), AND THE MRO
# ==========================================================================
# Java: single inheritance + interfaces. Python: real multiple inheritance,
# resolved by the MRO (C3 linearisation). FastAPI/Pydantic lean on mixins.

class TimestampMixin:
    def touch(self) -> str:
        return "updated_at set"

class SoftDeleteMixin:
    def delete(self) -> str:
        return "deleted_at set"

class Record(TimestampMixin, SoftDeleteMixin):
    pass

print("10.1 mixins:", Record().touch(), "|", Record().delete())
print("10.2 MRO:", [c.__name__ for c in Record.__mro__])

# super() is NOT just "my parent" — it is "the next class in the MRO",
# which is what makes cooperative multiple inheritance work.
class Base:
    def greet(self) -> str:
        return "base"

class Loud(Base):
    def greet(self) -> str:
        return super().greet().upper() + "!"

class Polite(Base):
    def greet(self) -> str:
        return "please " + super().greet()

class Both(Loud, Polite):
    pass

print("10.3 cooperative super():", Both().greet())   # 'please base' -> upper
print("10.4 MRO:", [c.__name__ for c in Both.__mro__])
# Loud.greet calls super(), which the MRO routes to Polite — NOT to Base.


# ==========================================================================
# EXERCISES
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# This class leaks state between instances. Fix it without changing `add`.
class Basket:
    contents: list[str] = []
    def add(self, item: str) -> None:
        self.contents.append(item)
# x, y = Basket(), Basket()
# x.add("wine")
# assert y.contents == []

# --- E2 -------------------------------------------------------------------
# Give Temperature a `fahrenheit` property that reads AND writes,
# backed by the celsius value.
class Temperature:
    def __init__(self, celsius: float) -> None:
        self.celsius = celsius
# t = Temperature(100)
# assert t.fahrenheit == 212
# t.fahrenheit = 32
# assert t.celsius == 0

# --- E3 -------------------------------------------------------------------
# Add a classmethod `from_string("wine:500")` that builds an Item.
class Item:
    def __init__(self, name: str, qty: int) -> None:
        self.name, self.qty = name, qty
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Item) and (self.name, self.qty) == (other.name, other.qty)
# assert Item.from_string("wine:500") == Item("wine", 500)

# --- E4 -------------------------------------------------------------------
# Make Version sortable and printable: v1 < v2, and str(v) == "1.2.3".
# Which dunders do you need?
class Version:
    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major, self.minor, self.patch = major, minor, patch
# assert str(Version(1, 2, 3)) == "1.2.3"
# assert Version(1, 2, 3) < Version(1, 10, 0)
# assert sorted([Version(2,0,0), Version(1,0,0)])[0] == Version(1,0,0)

# --- E5 -------------------------------------------------------------------
# Rewrite Item (E3) as a @dataclass. How many lines disappear?

# --- E6 -------------------------------------------------------------------
# Write a Protocol `Priced` for anything with a `.price` float attribute,
# then a function `cheapest(items)` returning the lowest-priced one.
# It must work on a dataclass AND on a Pydantic model without either of
# them knowing Priced exists.

# --- E7 -------------------------------------------------------------------
# Predict the output BEFORE running. Then run it and explain the MRO.
class A:
    def who(self): return "A"
class B(A):
    def who(self): return "B->" + super().who()
class C(A):
    def who(self): return "C->" + super().who()
class D(B, C):
    pass
# print(D().who())
# print([c.__name__ for c in D.__mro__])

print("Uncomment the asserts as you solve each one. Silence = all passed.")
