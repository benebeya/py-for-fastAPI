"""DRILL 05 — ITERATORS & GENERATORS   run: uv run generators/drill_05_generators.py"""
import itertools, sys

# 1. A GENERATOR PAUSES. Calling it runs NOTHING — you get a paused object back.
def ids():
    print("     [body starts]")
    i = 1
    while True:
        yield i
        i += 1
g = ids()
print("1  called, nothing ran:", type(g).__name__)
print("1  next() runs to the yield:", next(g), next(g), next(g))
# ITERABLE has __iter__ (list, dict, str — reusable).
# ITERATOR has __next__ (a generator — consumed once, then StopIteration).

# 2. ONE-SHOT — the gotcha. An exhausted generator is silently empty, not an error.
gen = (n*n for n in range(4))
print("2  first pass:", list(gen), "| second pass:", list(gen))
def count_and_sum(v): return len(list(v)), sum(v)      # BUG on a generator
print("2  broken:", count_and_sum(n for n in range(5)),
      "| fine on a list:", count_and_sum([0,1,2,3,4]))   # fix: v = list(v) first

# 3. *** try/finally AROUND A yield IS FastAPI's DB SESSION ***
def get_db():
    print("     >>> open connection")
    try:
        yield {"conn": "open"}          # FastAPI injects this into your endpoint
    finally:
        print("     <<< close connection")   # runs even if the endpoint raises
print("3  normal path:")
d = get_db(); conn = next(d)
try: next(d)
except StopIteration: pass
print("3  exception path — cleanup still happens:")
d = get_db(); next(d); d.close()        # .close() throws GeneratorExit at the yield
#     def get_db():
#         db = SessionLocal()
#         try: yield db
#         finally: db.close()
#     @app.get("/x")
#     def read(db: Annotated[Session, Depends(get_db)]): ...
# Drill 06 shows the same thing as a `with` block — they are one idea.

# 4. LAZINESS = MEMORY, and it composes into pipelines
print(f"4  list {sys.getsizeof([n for n in range(100_000)]):,}b "
      f"vs genexp {sys.getsizeof(n for n in range(100_000)):,}b")
raw  = (f"row-{i}" for i in range(6))
out  = (r.upper() for r in raw if not r.endswith("3"))
print("4  nothing ran until now:", list(out))
print("4  yield from flattens:", list(itertools.chain([1,2],[3])))

# 5. ITERTOOLS worth knowing
print("5 ", list(itertools.islice(itertools.count(10,5), 3)), list(itertools.pairwise([1,2,3])),
      list(itertools.batched(range(7),3)), list(itertools.accumulate([1,2,3])))
# tee() = iterate a generator twice. groupby() needs the input SORTED by the key.

# ===================== EXERCISES — fill in, then uncomment =====================
def fib(n): pass                        # E1 first n Fibonacci numbers
# assert list(fib(7)) == [0,1,1,2,3,5,8]

def count_and_sum_fixed(v): pass        # E2 make it work on a generator too
# assert count_and_sum_fixed(n for n in range(5)) == (5, 10)

def chunks(items, size): pass           # E3 fixed-size chunks, no itertools.batched
# assert list(chunks([1,2,3,4,5], 2)) == [[1,2],[3,4],[5]]

events = []
def managed(): pass                     # E4 the get_db shape: always append "closed"
# g = managed(); assert next(g) == "resource"
# g.close(); assert events == ["opened","closed"]

def deep_flatten(x): pass               # E5 [1,[2,[3,[4]]]] -> [1,2,3,4]; recursion + yield from
# assert list(deep_flatten([1,[2,[3,[4]],5]])) == [1,2,3,4,5]
