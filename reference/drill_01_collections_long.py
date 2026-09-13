"""
DRILL 01 — COLLECTIONS (list, tuple, set, dict)

Your originals (list.py, Tuple.py, set.py, dict.py) cover the METHODS.
This file covers the BEHAVIOUR — the parts that cause real bugs.

Run it:  uv run "Data structure /drill_01_collections.py"
Read top to bottom. Exercises are at the bottom.
"""

# ==========================================================================
# 1. THE #1 GOTCHA: names are labels, not boxes
# ==========================================================================
# `b = a` does NOT copy a list. Both names point at the SAME object.

a = ["apple", "orange"]
b = a
b.append("banana")
# ['apple', 'orange', 'banana']  <-- a changed!
print("1.1  a is now:", a)
print("1.2  same object?", a is b)  # True

# To actually copy:
c = a.copy()          # or list(a)  or  a[:]
c.append("coconut")
print("1.3  a unaffected:", a)

# `==` compares VALUES, `is` compares IDENTITY. Use `==` unless you mean
# "literally the same object" (or you're checking `x is None`).
print("1.4  ==", [1, 2] == [1, 2], "| is", [1, 2] is [1, 2])


# ==========================================================================
# 2. THE MUTABLE DEFAULT ARGUMENT TRAP
# ==========================================================================
# The default is created ONCE, when the function is defined. Not per call.

def add_item_broken(item, basket=[]):
    basket.append(item)
    return basket


print("2.1  broken:", add_item_broken("apple"))   # ['apple']
# ['apple', 'orange']  <-- leaked!
print("2.2  broken:", add_item_broken("orange"))


def add_item_ok(item, basket=None):
    if basket is None:
        basket = []      # fresh list every call
    basket.append(item)
    return basket


print("2.3  ok:", add_item_ok("apple"))
print("2.4  ok:", add_item_ok("orange"))
# You WILL hit this in FastAPI when a Pydantic model has a list field.


# ==========================================================================
# 3. LIST vs SET — the cost of `in`
# ==========================================================================
# list  -> scans every element     O(n)
# set   -> hashes straight to it   O(1)
# dict  -> same as set             O(1)

allowed_roles_list = ["admin", "editor", "viewer"]
allowed_roles_set = {"admin", "editor", "viewer"}

# works, but slow at scale
print("3.1  in list:", "editor" in allowed_roles_list)
print("3.2  in set: ", "editor" in allowed_roles_set)   # instant, any size

# Rule of thumb: if you only ever ask "is X in here?", use a set.


# ==========================================================================
# 4. SET — correcting your set.py comment
# ==========================================================================
# Your file says "unordered and immutable". A set IS mutable.
# What must be immutable are the ELEMENTS (they have to be hashable).

s = {"apple", "orange"}
s.add("banana")          # mutating the set: fine
print("4.1  mutable:", sorted(s))

try:
    {["a", "b"]}         # a list inside a set
except TypeError as e:
    print("4.2  elements must be hashable ->", e)

# frozenset is the genuinely immutable one — and it IS hashable,
# so it can live inside another set or be a dict key.
fs = frozenset(["apple", "orange"])
print("4.3  frozenset in a set:", {fs})

# Sets have NO order. .pop() removes an arbitrary element —
# your set.py line 10 is non-deterministic. Never rely on which one leaves.

# Set algebra is underrated — great for permissions:
required = {"read", "write", "delete"}
granted = {"read", "write"}
print("4.4  missing perms:", required - granted)          # {'delete'}
print("4.5  overlap:      ", required & granted)          # {'read', 'write'}
print("4.6  either:       ", required | granted)

# Dedupe while KEEPING order (set() loses it):
raw = ["b", "a", "b", "c", "a"]
print("4.7  deduped:", list(dict.fromkeys(raw)))          # ['b', 'a', 'c']


# ==========================================================================
# 5. TUPLE — immutable, but only one layer deep
# ==========================================================================
point = (3, 4)
try:
    point[0] = 99
except TypeError as e:
    print("5.1  cannot reassign ->", e)

# BUT: immutability is shallow. A mutable object inside stays mutable.
nested = ([1, 2], "fixed")
nested[0].append(3)
print("5.2  shallow immutability:", nested)   # ([1, 2, 3], 'fixed')

# The single-element trap — the comma makes the tuple, not the parens:
print("5.3  not a tuple:", type(("x")), "| tuple:", type(("x",)))

# Unpacking (you'll use this constantly with DB rows):
name, qty = ("tomatoes", 1000)
print(f"5.4  {name} -> {qty}")

first, *rest = ["a", "b", "c", "d"]
print("5.5  first:", first, "| rest:", rest)

# Because tuples are hashable, they can be dict keys. Lists cannot.
grid = {(0, 0): "origin", (1, 2): "target"}
print("5.6  tuple as key:", grid[(1, 2)])

# TYPE HINT DIFFERENCE (matters for FastAPI):
#   tuple[str, ...]  -> any number of strings
#   tuple[str, int]  -> EXACTLY two items: str then int


# ==========================================================================
# 6. DICT — the one you'll use most
# ==========================================================================
catalog = {
    "tomatoes": {"units": "boxes",   "qty": 1000},
    "wine":     {"units": "bottles", "qty": 500},
}

# [] raises KeyError. .get() returns None (or a default) instead.
# This is EXACTLY the bug in APIs/api.py line 19: an unknown product
# crashes with a 500 instead of returning a clean 404.
try:
    catalog["bananas"]
except KeyError as e:
    print("6.1  [] raises ->", e)

print("6.2  .get() is safe:", catalog.get("bananas"))
print("6.3  .get() w/ default:", catalog.get("bananas", {"qty": 0}))

# setdefault: read it, or create it if absent — in one step
orders: dict[str, list[str]] = {}
orders.setdefault("med", []).append("wine")
orders.setdefault("med", []).append("tomatoes")
print("6.4  setdefault:", orders)

# Merging (3.9+):
defaults = {"page": 1, "limit": 10}
user_params = {"limit": 50}
print("6.5  merged:", defaults | user_params)   # right side wins

# Dicts keep insertion order (guaranteed since 3.7).
# .keys()/.values()/.items() are LIVE VIEWS, not snapshots:
view = catalog.keys()
catalog["olives"] = {"units": "jars", "qty": 200}
print("6.6  live view:", list(view))            # includes olives

# Don't modify a dictionary's size while iterating over that same dictionary.


# ==========================================================================
# 7. COMPREHENSIONS — all four, and where the `if` goes
# ==========================================================================
nums = [1, 2, 3, 4, 5, 6]

print("7.1  list: ", [n * n for n in nums])
print("7.2  set:  ", {n % 3 for n in nums})
print("7.3  dict: ", {n: n * n for n in nums})

# FILTER: `if` goes at the END, and there is no `else`
print("7.4  filter:", [n for n in nums if n % 2 == 0])

# TRANSFORM with a choice: ternary goes at the FRONT, `else` is required
print("7.5  ternary:", ["even" if n % 2 == 0 else "odd" for n in nums])

# Both together — front picks the value, back decides membership
print("7.6  both:", ["big" if n > 4 else "small" for n in nums if n % 2 == 0])

# A generator expression: same syntax, parens instead. Computes lazily,
# holds one item in memory at a time. (Drill 05 goes deeper.)
total = sum(n * n for n in nums)
print("7.7  genexp sum:", total)

# sorted(key=...) — you will use this on every list of records
products = [
    {"name": "wine",     "qty": 500},
    {"name": "tomatoes", "qty": 1000},
    {"name": "olives",   "qty": 200},
]
by_qty = sorted(products, key=lambda p: p["qty"], reverse=True)
print("7.8  sorted:", [p["name"] for p in by_qty])


# ==========================================================================
# EXERCISES — replace the `pass` / `None`, then uncomment the asserts.
# No output from an assert = you got it right.
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

inventory = {
    "tomatoes": 1000,
    "wine": 500,
    "olives": 0,
    "bread": 0,
    "cheese": 250,
}

# --- E1 -------------------------------------------------------------------
# Build a dict of ONLY the products in stock (qty > 0). Use a dict comprehension.
in_stock = None
# assert in_stock == {"tomatoes": 1000, "wine": 500, "cheese": 250}

# --- E2 -------------------------------------------------------------------
# Return the qty for a product, or 0 if it doesn't exist.
# Must NOT raise KeyError. One line.


def get_qty(product: str) -> int:
    pass
# assert get_qty("wine") == 500
# assert get_qty("bananas") == 0


# --- E3 -------------------------------------------------------------------
# A customer asks for these. Which are NOT in the inventory at all?
# Use set algebra, not a loop.
requested = {"wine", "bananas", "olives", "coffee"}
unknown = None
# assert unknown == {"bananas", "coffee"}

# --- E4 -------------------------------------------------------------------
# Fix this function so each caller gets its own log list.


def record_sale(product, log=[]):
    log.append(product)
    return log
# assert record_sale("wine") == ["wine"]
# assert record_sale("olives") == ["olives"]   # currently fails

# --- E5 -------------------------------------------------------------------
# Return (name, qty) of the product with the highest qty, as a tuple.
# Hint: max() takes a key= too.


def top_product(inv: dict[str, int]) -> tuple[str, int]:
    pass
# assert top_product(inventory) == ("tomatoes", 1000)


# --- E6 -------------------------------------------------------------------
# Remove duplicates but KEEP the original order.
deliveries = ["wine", "bread", "wine", "olives", "bread", "cheese"]
unique_ordered = None
# assert unique_ordered == ["wine", "bread", "olives", "cheese"]

# --- E7 -------------------------------------------------------------------
# Group products by whether they're in stock.
# Expected: {True: ["tomatoes", "wine", "cheese"], False: ["olives", "bread"]}
# Hint: setdefault, or collections.defaultdict.
grouped: dict[bool, list[str]] = {}
# assert grouped == {True: ["tomatoes", "wine", "cheese"],
#                    False: ["olives", "bread"]}

print("Uncomment the asserts as you solve each one. Silence = all passed.")
