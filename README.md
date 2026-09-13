# py-for-fastAPI

Python review before starting FastAPI + databases. Python 3.14, managed with `uv`.

Each topic folder has the **original notes** (kept as-is) plus a **drill file**:
~60–95 dense lines of runnable examples with the gotchas made visible, then
exercises with commented `assert`s at the bottom. Uncomment each assert as you
solve it — silence means it passed.

Longer, fully-commented versions of every drill are in [`reference/`](reference/)
if you want the expanded explanation of any one topic.

## The path

Do these in order. 2–8 are the actual prerequisites for FastAPI; the first is a
fluency check.

| # | Drill | Why it's here |
|---|-------|---------------|
| 01 | [`Data structure /drill_01_collections.py`](Data%20structure%20/drill_01_collections.py) | Aliasing, mutable defaults, `in` cost, `.get()` vs `[]`, comprehensions |
| 02 | [`type Hints/drill_02_type_hints.py`](type%20Hints/drill_02_type_hints.py) | **FastAPI *is* type hints.** `X \| None`, `Annotated`, `Protocol`, generics |
| 03 | [`decorators/drill_03_decorators.py`](decorators/drill_03_decorators.py) | Until `@app.get("/x")` is boring. Closures, `functools.wraps`, registration |
| 04 | [`oop/drill_04_oop_for_java_devs.py`](oop/drill_04_oop_for_java_devs.py) | Only the delta from Java. Class vs instance attrs, `@property`, dunders, ABC |
| 05 | [`generators/drill_05_generators.py`](generators/drill_05_generators.py) | `yield` + `try/finally` — this is `Depends()` with yield, i.e. DB sessions |
| 06 | [`context-managers/drill_06_context_managers.py`](context-managers/drill_06_context_managers.py) | Every session, transaction and client. `async with`, FastAPI `lifespan` |
| 07 | [`Async programming /drill_07_async.py`](Async%20programming%20/drill_07_async.py) | Blocking the event loop, `TaskGroup`, `def` vs `async def` in routes |
| 08 | [`packages/drill_08_packages.py`](packages/drill_08_packages.py) | Imports, circular imports, and the project layout to actually use |

## Running

```bash
uv run "Data structure /drill_01_collections.py"
uv run "type Hints/drill_02_type_hints.py"
uv run decorators/drill_03_decorators.py
uv run oop/drill_04_oop_for_java_devs.py
uv run generators/drill_05_generators.py
uv run context-managers/drill_06_context_managers.py
uv run "Async programming /drill_07_async.py"
uv run packages/drill_08_packages.py
```

## Known issue: folder names

`Data structure ` and `Async programming ` have **trailing spaces**, and
`type Hints` / `args-kwargs` aren't valid identifiers either. You can *run*
those files but never `import` from them — fine for practice scripts, fatal for
an app. Drill 08 §8 covers this; renaming them is exercise E6.

## Next, after drill 08

```bash
uv add "sqlalchemy>=2.0" alembic aiosqlite
uv add --dev pytest httpx
```
