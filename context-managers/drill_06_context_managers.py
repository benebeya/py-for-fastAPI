"""
DRILL 06 — CONTEXT MANAGERS (sync and async)

Not in your repo at all, and you cannot avoid it: every database session,
transaction, HTTP client and file handle you touch in FastAPI is a context
manager. FastAPI's own `lifespan` is one too.

Run it:  uv run context-managers/drill_06_context_managers.py
"""

import asyncio
import contextlib
import sqlite3
import time
from collections.abc import Iterator, AsyncIterator


# ==========================================================================
# 1. THE PROBLEM IT SOLVES
# ==========================================================================
# Anything you open must be closed, even when the code in between explodes.

def without_manager(path: str) -> None:
    f = open(path, "w")
    f.write("data")
    raise RuntimeError("boom")      # f.close() never runs -> leaked handle
    f.close()

scratch = "/tmp/drill06_demo.txt"
try:
    without_manager(scratch)
except RuntimeError:
    print("1.1  raised; the file handle leaked")

# try/finally fixes it, but it's noisy and easy to forget:
f = open(scratch, "w")
try:
    f.write("data")
finally:
    f.close()
print("1.2  try/finally works, but this is 5 lines every time")

# `with` is that pattern, named and reusable:
with open(scratch, "w") as f:
    f.write("data")
print("1.3  with-block closed it:", f.closed)


# ==========================================================================
# 2. THE PROTOCOL — __enter__ and __exit__
# ==========================================================================
# Any object with these two methods works in a `with`. That is the whole API.

class Connection:
    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self) -> "Connection":
        print(f"     >>> open {self.name}")
        return self                  # this is what `as x` receives

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        print(f"     <<< close {self.name}")
        return False                 # False = do not suppress exceptions

    def query(self, sql: str) -> str:
        return f"result of {sql!r}"

print("2.1  happy path:")
with Connection("db") as conn:
    print("    ", conn.query("SELECT 1"))

print("2.2  exception path — __exit__ still runs:")
try:
    with Connection("db") as conn:
        raise ValueError("query failed")
except ValueError as e:
    print("     exception escaped as expected:", e)


# ==========================================================================
# 3. __exit__ CAN SWALLOW THE EXCEPTION
# ==========================================================================
# Return True and the exception stops there. Use sparingly — silent failures
# are worse than loud ones — but this is how contextlib.suppress works.

class Ignore:
    def __init__(self, *exc_types: type[BaseException]) -> None:
        self.exc_types = exc_types
    def __enter__(self) -> None:
        return None
    def __exit__(self, exc_type, exc_value, tb) -> bool:
        return exc_type is not None and issubclass(exc_type, self.exc_types)

with Ignore(ZeroDivisionError):
    1 / 0
print("3.1  swallowed, execution continues")

# The stdlib version:
with contextlib.suppress(ZeroDivisionError, KeyError):
    {}["missing"]
print("3.2  contextlib.suppress: same thing, already written")

# The three __exit__ parameters are (type, value, traceback) — all None on
# the happy path. That's how you can log or roll back only on failure.


# ==========================================================================
# 4. @contextmanager — write one as a generator
# ==========================================================================
# Drill 05 §7 ended with a generator that yields once inside try/finally.
# This decorator turns exactly that shape into a context manager.
#
#   everything before yield  ->  __enter__
#   the yielded value        ->  `as x`
#   everything after yield   ->  __exit__

@contextlib.contextmanager
def timer(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"     {label}: {time.perf_counter() - start:.4f}s")

print("4.1  timer:")
with timer("sleep"):
    time.sleep(0.02)

@contextlib.contextmanager
def transaction(conn_name: str) -> Iterator[dict[str, str]]:
    print(f"     BEGIN {conn_name}")
    conn = {"name": conn_name}
    try:
        yield conn
    except Exception:
        print("     ROLLBACK")
        raise                       # re-raise: never hide a failed write
    else:
        print("     COMMIT")        # only when no exception occurred
    finally:
        print("     release connection")

print("4.2  commit path:")
with transaction("db") as c:
    print("     INSERT INTO ...")

print("4.3  rollback path:")
try:
    with transaction("db") as c:
        raise RuntimeError("constraint violated")
except RuntimeError:
    print("     handled upstream")

# try/except/else/finally inside the generator gives you the full lifecycle.
# This IS how SQLAlchemy's Session.begin() is written.


# ==========================================================================
# 5. ONE-SHOT: a @contextmanager cannot be reused
# ==========================================================================
# It wraps a generator, and a generator is consumed (Drill 05 §3).

t = timer("reuse-test")
with t:
    pass
try:
    with t:                      # second use of the SAME object
        pass
except (RuntimeError, AttributeError) as e:
    print("5.1  reuse fails ->", type(e).__name__, e)
print("5.2  call the factory again each time: `with timer('x'):`")

# (The exact exception type is a CPython implementation detail — older
# versions raised RuntimeError, 3.14 raises AttributeError. Either way:
# one context manager object, one use.)
#
# A class-based manager CAN be reusable if you write it that way — our
# Connection above works fine twice — but it still isn't REENTRANT
# (nesting the same instance inside itself) unless you design for it.


# ==========================================================================
# 6. MULTIPLE MANAGERS
# ==========================================================================
with Connection("read-db") as src, Connection("write-db") as dst:
    print("6.1  two at once; closed in reverse order")

# 3.10+ lets you wrap them in parentheses, which is much nicer when long:
with (
    Connection("a") as a,
    Connection("b") as b,
):
    print("6.2  parenthesised form")

# ExitStack: when the NUMBER of resources isn't known until runtime.
with contextlib.ExitStack() as stack:
    conns = [stack.enter_context(Connection(f"shard-{i}")) for i in range(3)]
    print("6.3  ExitStack managing", len(conns), "connections")


# ==========================================================================
# 7. A REAL ONE — sqlite3 (stdlib, no install needed)
# ==========================================================================
with contextlib.closing(sqlite3.connect(":memory:")) as db:
    db.execute("CREATE TABLE product (name TEXT, qty INT)")
    with db:                        # a sqlite3 connection commits/rolls back
        db.execute("INSERT INTO product VALUES (?, ?)", ("wine", 500))
    print("7.1  committed:", db.execute("SELECT * FROM product").fetchall())

    try:
        with db:
            db.execute("INSERT INTO product VALUES (?, ?)", ("olives", 200))
            raise RuntimeError("something failed mid-transaction")
    except RuntimeError:
        pass
    print("7.2  rolled back:", db.execute("SELECT * FROM product").fetchall())

# Note `closing()` — sqlite3's own `with` handles the TRANSACTION, not the
# connection. Two different scopes. You'll meet the same distinction in
# SQLAlchemy: `Session` vs `Session.begin()`.


# ==========================================================================
# 8. ASYNC CONTEXT MANAGERS — `async with`
# ==========================================================================
# Same idea, awaitable. __aenter__/__aexit__ instead of __enter__/__exit__.
# Needed whenever setup or teardown does I/O — which is every async DB pool
# and every HTTP client.

class AsyncConnection:
    def __init__(self, name: str) -> None:
        self.name = name

    async def __aenter__(self) -> "AsyncConnection":
        await asyncio.sleep(0.01)            # pretend: network handshake
        print(f"     >>> async open {self.name}")
        return self

    async def __aexit__(self, exc_type, exc_value, tb) -> bool:
        await asyncio.sleep(0.01)            # pretend: graceful close
        print(f"     <<< async close {self.name}")
        return False

    async def fetch(self, sql: str) -> str:
        await asyncio.sleep(0.01)
        return f"rows for {sql!r}"


@contextlib.asynccontextmanager
async def async_transaction(name: str) -> AsyncIterator[str]:
    print(f"     BEGIN {name}")
    try:
        yield name
    except Exception:
        print("     ROLLBACK")
        raise
    else:
        print("     COMMIT")


async def demo_async() -> None:
    print("8.1  async with (class-based):")
    async with AsyncConnection("pg") as conn:
        print("    ", await conn.fetch("SELECT 1"))

    print("8.2  @asynccontextmanager:")
    async with async_transaction("pg") as tx:
        print("     writing inside", tx)

    print("8.3  async for — the streaming counterpart:")
    async def rows() -> AsyncIterator[str]:
        for i in range(3):
            await asyncio.sleep(0.01)
            yield f"row-{i}"
    async for row in rows():
        print("    ", row)

asyncio.run(demo_async())


# ==========================================================================
# 9. WHERE YOU'LL ACTUALLY SEE THIS IN FASTAPI
# ==========================================================================
# (a) lifespan — startup/shutdown for the whole app. It IS an
#     asynccontextmanager. Everything before yield runs at startup,
#     everything after at shutdown:
#
#         @asynccontextmanager
#         async def lifespan(app: FastAPI):
#             app.state.pool = await create_pool()
#             yield
#             await app.state.pool.close()
#
#         app = FastAPI(lifespan=lifespan)
#
# (b) the async DB session dependency:
#
#         async def get_session() -> AsyncIterator[AsyncSession]:
#             async with async_session_maker() as session:
#                 yield session
#
# (c) the test client:
#
#         async with AsyncClient(app=app) as client: ...
#
# All three are this drill plus Drill 05. Nothing new.


# ==========================================================================
# EXERCISES
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# Class-based: append "enter" on the way in and "exit" on the way out,
# even if the body raises.
log: list[str] = []
class Tracked:
    pass
# with Tracked(): log.append("body")
# assert log == ["enter", "body", "exit"]
# log.clear()
# try:
#     with Tracked(): raise ValueError
# except ValueError: pass
# assert log == ["enter", "exit"]

# --- E2 -------------------------------------------------------------------
# The same thing with @contextlib.contextmanager. Far fewer lines.
@contextlib.contextmanager
def tracked():
    pass

# --- E3 -------------------------------------------------------------------
# `temp_value` sets d[key] to a new value, then restores the ORIGINAL on exit
# (and removes the key entirely if it wasn't there before).
@contextlib.contextmanager
def temp_value(d: dict, key: str, value):
    pass
# cfg = {"debug": False}
# with temp_value(cfg, "debug", True):
#     assert cfg["debug"] is True
# assert cfg["debug"] is False
# with temp_value(cfg, "new", 1):
#     assert cfg["new"] == 1
# assert "new" not in cfg

# --- E4 -------------------------------------------------------------------
# A context manager that SUPPRESSES only ValueError and records it.
# Everything else propagates. (Write __exit__ by hand, don't use suppress.)
caught: list[str] = []
class OnlyValueError:
    pass
# with OnlyValueError(): raise ValueError("ok")
# assert caught == ["ok"]
# try:
#     with OnlyValueError(): raise TypeError("nope")
# except TypeError: pass
# else: assert False, "TypeError should propagate"

# --- E5 -------------------------------------------------------------------
# Async version of E2: an @asynccontextmanager that appends
# "aenter"/"aexit" around the body.

# --- E6 -------------------------------------------------------------------
# Using the sqlite3 block in §7 as a model: write `get_db()` as a
# @contextmanager that yields a connection with the `product` table already
# created, and closes it afterwards. Then use it in a `with`.

# --- E7 -------------------------------------------------------------------
# Rewrite §7's rollback demo using ExitStack so the number of tables created
# is decided by a list passed in at runtime.

print("Uncomment the asserts as you solve each one. Silence = all passed.")
