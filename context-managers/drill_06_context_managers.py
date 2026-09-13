"""DRILL 06 — CONTEXT MANAGERS (sync + async)   run: uv run context-managers/drill_06_context_managers.py"""
import asyncio, contextlib, sqlite3

# 1. THE PROBLEM: anything opened must be closed even when the body explodes.
#    try/finally works but is 5 noisy lines every time. `with` IS that pattern, named.

# 2. THE PROTOCOL — any object with __enter__/__exit__ works. That's the whole API.
class Conn:
    def __init__(self, n): self.n = n
    def __enter__(self): print(f"     >>> open {self.n}"); return self      # <- what `as x` gets
    def __exit__(self, exc_type, exc, tb): print(f"     <<< close {self.n}"); return False
with Conn("db") as c: print("2  happy path")
try:
    with Conn("db") as c: raise ValueError("query failed")
except ValueError as e: print("2  __exit__ ran anyway, exception escaped:", e)
# Return True from __exit__ to SWALLOW the exception — that's contextlib.suppress:
with contextlib.suppress(ZeroDivisionError): 1/0
print("2  suppressed, execution continues")

# 3. @contextmanager — Drill 05's `try/finally around a yield`, with a decorator on it.
#    before yield = __enter__ | yielded value = `as x` | after yield = __exit__
@contextlib.contextmanager
def transaction(name):
    print(f"     BEGIN {name}")
    try:
        yield {"name": name}
    except Exception:
        print("     ROLLBACK"); raise        # never hide a failed write
    else:
        print("     COMMIT")
    finally:
        print("     release")
with transaction("db"): print("     INSERT ...")
try:
    with transaction("db"): raise RuntimeError("constraint")
except RuntimeError: print("3  handled upstream")
# One @contextmanager object = ONE use (it wraps a generator). Call the factory again.

# 4. A REAL ONE — sqlite3. Note the two DIFFERENT scopes:
with contextlib.closing(sqlite3.connect(":memory:")) as db:   # closing() = the CONNECTION
    db.execute("CREATE TABLE p (name TEXT, qty INT)")
    with db:                                                  # `with db` = the TRANSACTION
        db.execute("INSERT INTO p VALUES (?,?)", ("wine", 500))
    try:
        with db:
            db.execute("INSERT INTO p VALUES (?,?)", ("olives", 200)); raise RuntimeError
    except RuntimeError: pass
    print("4  olives rolled back:", db.execute("SELECT * FROM p").fetchall())
# Same split in SQLAlchemy: Session vs Session.begin().
# ExitStack() when the NUMBER of resources isn't known until runtime.

# 5. ASYNC — __aenter__/__aexit__, needed whenever setup/teardown does I/O
@contextlib.asynccontextmanager
async def async_tx(n):
    print(f"     BEGIN {n}"); yield n; print("     COMMIT")
async def main():
    async with async_tx("pg") as tx: print("5  inside", tx)
    async def rows():
        for i in range(3): await asyncio.sleep(0); yield f"row-{i}"
    print("5  async for:", [r async for r in rows()])
asyncio.run(main())
# FastAPI's lifespan IS an @asynccontextmanager: before yield = startup, after = shutdown.
#     @asynccontextmanager
#     async def lifespan(app): app.state.pool = await create_pool(); yield; await pool.close()
#     app = FastAPI(lifespan=lifespan)

# ===================== EXERCISES — fill in, then uncomment =====================
log = []
class Tracked: pass                     # E1 append "enter"/"exit", even when the body raises
# with Tracked(): log.append("body")
# assert log == ["enter","body","exit"]

@contextlib.contextmanager
def tracked(): pass                     # E2 same thing, far fewer lines

@contextlib.contextmanager
def temp_value(d, k, v): pass           # E3 set d[k]=v, RESTORE the original on exit
# cfg = {"debug": False}
# with temp_value(cfg,"debug",True): assert cfg["debug"] is True
# assert cfg["debug"] is False
# with temp_value(cfg,"new",1): pass
# assert "new" not in cfg               # and remove the key if it wasn't there

class OnlyValueError: pass              # E4 suppress ONLY ValueError, by hand, no suppress()
# E5 async version of E2, appending "aenter"/"aexit"
