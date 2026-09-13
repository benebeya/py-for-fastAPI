"""DRILL 01 — COLLECTIONS    run: uv run "Data structure /drill_01_collections.py" """

# 1. NAMES ARE LABELS — `b = a` shares one object, it does not copy
a = ["x"]; b = a; b.append("y")
print("1  aliased:", a, "| a is b:", a is b)
c = a.copy(); c.append("z")                     # or list(a) / a[:]
print("1  copied:", a, "vs", c)

# 2. MUTABLE DEFAULT — built ONCE at def time, then shared by every call
def bad(x, into=[]): into.append(x); return into
def good(x, into=None): into = [] if into is None else into; into.append(x); return into
print("2  bad:", bad("a"), bad("b"), "  good:", good("a"), good("b"))

# 3. MEMBERSHIP — list scans O(n); set/dict hash straight to it O(1)
print("3  use a set when you only ask `in`:", "admin" in {"admin", "user"})

# 4. SET — the set is MUTABLE; its ELEMENTS must be hashable (your set.py says otherwise)
try: {["x"]}
except TypeError as e: print("4  unhashable element:", e)
print("4  set algebra:", {"read","write"} - {"read"},
      "| dedupe keeping order:", list(dict.fromkeys(["b","a","b","c"])))
# .pop() on a set removes an ARBITRARY element — never rely on which.

# 5. TUPLE — immutability is SHALLOW, and the comma makes it, not the parens
t = ([1], "fixed"); t[0].append(2)
print("5  shallow:", t, "| ('x') ->", type(("x")).__name__, "| ('x',) ->", type(("x",)).__name__)

# 6. DICT — [] raises KeyError, .get() does not  (the 500-vs-404 bug in api.py:19)
cat = {"wine": 500}
print("6  get:", cat.get("nope"), cat.get("nope", 0), "| merge:", {"p":1} | {"p":2})
d = {}; d.setdefault("med", []).append("wine")
print("6  setdefault:", d)

# 7. COMPREHENSIONS — `if` at the END filters; ternary at the FRONT chooses a value
n = [1,2,3,4]
print("7  filter:", [x for x in n if x%2==0],
      "| ternary:", ["e" if x%2==0 else "o" for x in n],
      "| dict:", {x:x*x for x in n},
      "| genexp:", sum(x*x for x in n))

# ===================== EXERCISES — fill in, then uncomment =====================
inv = {"tomatoes":1000, "wine":500, "olives":0, "bread":0}

in_stock = None                                          # E1 dict comp, qty > 0
# assert in_stock == {"tomatoes":1000, "wine":500}

def get_qty(p): pass                                     # E2 qty or 0, no KeyError
# assert get_qty("wine") == 500 and get_qty("x") == 0

unknown = None                                           # E3 set algebra, no loop
# assert unknown == {"coffee"}      # against requested = {"wine","olives","coffee"}

def record(p, log=[]): log.append(p); return log         # E4 fix the leak
# assert record("a") == ["a"] and record("b") == ["b"]

def top(d): pass                                         # E5 highest qty as a tuple
# assert top(inv) == ("tomatoes", 1000)

uniq = None                                              # E6 dedupe, keep order
# assert uniq == ["wine","bread","olives"]   # from ["wine","bread","wine","olives"]

grouped = {}                                             # E7 group by in-stock
# assert grouped == {True:["tomatoes","wine"], False:["olives","bread"]}
