"""
DRILL 05 — ITERATORS & GENERATORS

Your test.py has the infinite-ID generator, which is the right first example.
This file covers the protocol underneath it, the gotchas, and the two places
generators show up in FastAPI: streaming responses and `Depends(...)` with
yield — which is how database sessions are managed.

Run it:  uv run generators/drill_05_generators.py
"""

import itertools
import sys
from collections.abc import Iterator, Iterable, Generator


# ==========================================================================
# 1. ITERABLE vs ITERATOR — two different things
# ==========================================================================
# ITERABLE: has __iter__, can produce an iterator. (list, dict, str, set)
# ITERATOR: has __next__, produces values one at a time, and is CONSUMED.

nums = [1, 2, 3]                       # iterable
it = iter(nums)                        # iterator
print("1.1  iterator:", type(it).__name__)
print("1.2  manual next:", next(it), next(it), next(it))
try:
    next(it)
except StopIteration:
    print("1.3  exhausted -> StopIteration")

# A `for` loop is exactly this, with the StopIteration handled for you:
#     it = iter(nums)
#     while True:
#         try: x = next(it)
#         except StopIteration: break
#         ...body...

# The list is reusable; the iterator is not.
print("1.4  list re-iterates:", list(nums), list(nums))

# Writing the protocol by hand (rarely needed, but shows there's no magic):
class Countdown:
    def __init__(self, start: int) -> None:
        self.start = start
    def __iter__(self) -> Iterator[int]:
        current = self.start
        while current > 0:
            yield current
            current -= 1

print("1.5  custom iterable:", list(Countdown(3)), list(Countdown(3)))


# ==========================================================================
# 2. GENERATORS — a function that pauses
# ==========================================================================
# `yield` turns a function into a generator factory. Calling it runs NOTHING;
# it hands back a paused generator object.

def generate_ids() -> Generator[int]:
    print("     [body starts]")
    id = 1
    while True:
        yield id
        id += 1

gen = generate_ids()
print("2.1  called, nothing ran yet:", type(gen).__name__)
print("2.2  first next() runs the body:", next(gen))
print("2.3  resumes where it paused:", next(gen), next(gen))

# Each yield freezes the whole local state — variables, loop position — and
# the next next() thaws it.

def steps():
    print("     step A")
    yield 1
    print("     step B")
    yield 2
    print("     step C")

print("2.4  interleaved execution:")
for value in steps():
    print("     got", value)


# ==========================================================================
# 3. THE ONE-SHOT GOTCHA
# ==========================================================================
# A generator is an ITERATOR. Once consumed, it is dead. This catches
# everyone, usually when passing one to two different functions.

g = (n * n for n in range(4))
print("3.1  first pass:", list(g))
print("3.2  second pass:", list(g))        # [] — already exhausted

def count_and_sum(values: Iterable[int]) -> tuple[int, int]:
    return len(list(values)), sum(values)  # BUG if `values` is a generator

print("3.3  broken on a generator:", count_and_sum(n for n in range(5)))
print("3.4  fine on a list:       ", count_and_sum([0, 1, 2, 3, 4]))
# Fix: materialise once at the top -> `values = list(values)`.


# ==========================================================================
# 4. WHY BOTHER — memory
# ==========================================================================
# A list comprehension builds everything now. A generator expression builds
# nothing until asked. Same syntax, different brackets.

list_version = [n for n in range(100_000)]
gen_version  = (n for n in range(100_000))
print(f"4.1  list: {sys.getsizeof(list_version):>8,} bytes")
print(f"4.2  gen:  {sys.getsizeof(gen_version):>8,} bytes")
print("4.3  same answer:", sum(list_version) == sum(gen_version))

# Inside a single function call the parens are optional:
print("4.4  bare genexp:", sum(n * n for n in range(10)))

# Short-circuiting works too — any()/all() stop at the first decisive value:
print("4.5  any() stops early:", any(n > 2 for n in itertools.count()))

# Use a list when you need to index, re-iterate, or know the length.
# Use a generator when you stream, when data is huge, or when it's infinite.


# ==========================================================================
# 5. yield from — delegating to another generator
# ==========================================================================
def inner():
    yield 1
    yield 2

def outer_manual():
    for v in inner():
        yield v
    yield 3

def outer_clean():
    yield from inner()      # same thing, and forwards send/throw correctly
    yield 3

print("5.1  yield from:", list(outer_clean()), "==", list(outer_manual()))

# Handy for flattening:
def flatten(nested: list[list[int]]):
    for sub in nested:
        yield from sub

print("5.2  flattened:", list(flatten([[1, 2], [3], [4, 5]])))


# ==========================================================================
# 6. RETURN VALUES AND .send()
# ==========================================================================
# A generator can `return` — the value rides on StopIteration, and
# `yield from` unpacks it.

def counter():
    total = 0
    for _ in range(3):
        total += 1
        yield total
    return f"finished at {total}"

def wrapper():
    result = yield from counter()
    print("     inner returned:", result)

print("6.1  return value via yield from:")
list(wrapper())

# yield is also an EXPRESSION — .send() passes a value back in.
def accumulator():
    total = 0
    while True:
        received = yield total       # pauses here, .send() supplies `received`
        total += received

acc = accumulator()
next(acc)                            # prime it: run up to the first yield
print("6.2  send:", acc.send(10), acc.send(5), acc.send(100))


# ==========================================================================
# 7. *** try/finally IN A GENERATOR — this is FastAPI's DB session ***
# ==========================================================================
# Code after the yield runs when the generator is closed. That is the entire
# basis of `Depends()` with yield: set up, hand over, always tear down.

def get_db():
    print("     >>> open connection")
    db = {"conn": "open"}
    try:
        yield db                     # FastAPI injects this into your endpoint
    finally:
        print("     <<< close connection")   # runs even if the endpoint raises

print("7.1  normal path:")
gen = get_db()
db = next(gen)                       # setup runs, we receive the resource
print("     using", db)
try:
    next(gen)                        # resume -> generator ends -> finally runs
except StopIteration:
    pass

print("7.2  exception path (cleanup still happens):")
gen = get_db()
db = next(gen)
gen.close()                          # throws GeneratorExit at the yield

# In FastAPI you write exactly this and never call next() yourself:
#
#     def get_db():
#         db = SessionLocal()
#         try:
#             yield db
#         finally:
#             db.close()
#
#     @app.get("/items")
#     def read(db: Annotated[Session, Depends(get_db)]): ...
#
# Drill 06 shows the same pattern as a `with` block — they are two faces of
# one idea, and @contextlib.contextmanager is literally built on this.


# ==========================================================================
# 8. STREAMING — the other FastAPI use
# ==========================================================================
def read_large_file(lines: list[str]):
    """Pretend this is a 10GB file. One line in memory at a time."""
    for line in lines:
        yield line.strip().upper()

print("8.1  streamed:", list(read_large_file([" a ", " b ", " c "])))

# FastAPI's StreamingResponse takes a generator and sends each chunk as it is
# produced, so the client starts receiving before you've finished computing.
# Also the right shape for pipelines — each stage is lazy:
raw       = (f"row-{i}" for i in range(6))
filtered  = (r for r in raw if not r.endswith("3"))
formatted = (r.upper() for r in filtered)
print("8.2  lazy pipeline:", list(formatted))   # nothing ran until this line


# ==========================================================================
# 9. itertools — the ones worth memorising
# ==========================================================================
print("9.1  count:     ", list(itertools.islice(itertools.count(10, 5), 4)))
print("9.2  cycle:     ", list(itertools.islice(itertools.cycle("ab"), 5)))
print("9.3  repeat:    ", list(itertools.repeat("x", 3)))
print("9.4  chain:     ", list(itertools.chain([1, 2], [3], [4])))
print("9.5  islice:    ", list(itertools.islice(range(100), 2, 8, 2)))
print("9.6  pairwise:  ", list(itertools.pairwise([1, 2, 3, 4])))
print("9.7  batched:   ", list(itertools.batched(range(7), 3)))   # 3.12+
print("9.8  accumulate:", list(itertools.accumulate([1, 2, 3, 4])))

# groupby needs the input SORTED by the same key — the classic mistake:
rows = [("wine", 1), ("wine", 2), ("olives", 3)]
for key, group in itertools.groupby(rows, key=lambda r: r[0]):
    print(f"9.9  groupby {key}:", [q for _, q in group])

# tee is the fix for "I need to iterate this generator twice":
g1, g2 = itertools.tee(n * n for n in range(4))
print("9.10 tee:", list(g1), list(g2))


# ==========================================================================
# EXERCISES
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# A generator yielding the first `n` Fibonacci numbers.
def fib(n: int):
    pass
# assert list(fib(7)) == [0, 1, 1, 2, 3, 5, 8]

# --- E2 -------------------------------------------------------------------
# Yield only items that pass `predicate` — your own version of filter().
def only(predicate, items):
    pass
# assert list(only(lambda x: x % 2, [1, 2, 3, 4, 5])) == [1, 3, 5]

# --- E3 -------------------------------------------------------------------
# Fix count_and_sum from §3 so it works on a generator too.
def count_and_sum_fixed(values):
    pass
# assert count_and_sum_fixed(n for n in range(5)) == (5, 10)

# --- E4 -------------------------------------------------------------------
# Yield fixed-size chunks from any iterable. Last chunk may be short.
# Do NOT use itertools.batched — write the loop.
def chunks(items, size: int):
    pass
# assert list(chunks([1,2,3,4,5], 2)) == [[1,2],[3,4],[5]]

# --- E5 -------------------------------------------------------------------
# A resource manager in the get_db() shape: yields the resource, and ALWAYS
# appends "closed" to `events` — even when the caller raises.
events = []
def managed_resource():
    pass
# g = managed_resource()
# r = next(g)
# assert r == "resource"
# g.close()
# assert events == ["opened", "closed"]

# --- E6 -------------------------------------------------------------------
# Flatten arbitrarily deep nesting: [1, [2, [3, [4]]]] -> [1, 2, 3, 4]
# Hint: recursion + yield from.
def deep_flatten(items):
    pass
# assert list(deep_flatten([1, [2, [3, [4]], 5]])) == [1, 2, 3, 4, 5]

# --- E7 -------------------------------------------------------------------
# Infinite generator of page numbers, but stop as soon as one exceeds 50.
# Use itertools.count + takewhile. One line.
pages = None
# assert list(pages) == [10, 20, 30, 40, 50]   # start=10, step=10

print("Uncomment the asserts as you solve each one. Silence = all passed.")
