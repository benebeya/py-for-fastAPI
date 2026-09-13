"""
DRILL 07 — ASYNC (deep)

Your test.py already uses TaskGroup, which is the modern right answer. The
commented-out block above it is the classic mistake, and it's worth keeping:
it looks concurrent and isn't. We start there.

The section that matters most for production is §5 — blocking the event loop.
That is the bug that takes a FastAPI service down.

Run it:  uv run "Async programming /drill_07_async.py"
"""

import asyncio
import time


def clock() -> float:
    return time.perf_counter()


# ==========================================================================
# 1. THE MENTAL MODEL
# ==========================================================================
# asyncio is CONCURRENCY, not PARALLELISM. One thread, one event loop.
# `await` means "I'm about to wait on I/O — go run something else, and
# come back to me when it's ready."
#
# It buys you nothing for CPU work. It buys you everything for network and
# disk calls, which is ~all a web API ever does.

async def fetch_data(id: int, sleep_time: float) -> dict[str, str | int]:
    print(f"     coroutine {id} starting")
    await asyncio.sleep(sleep_time)          # stands in for a network call
    print(f"     coroutine {id} done")
    return {"id": id, "data": f"sample from {id}"}


# ==========================================================================
# 2. *** THE BUG IN YOUR COMMENTED-OUT BLOCK ***
# ==========================================================================
# Calling an async function returns a COROUTINE OBJECT. Nothing runs. It only
# starts when something awaits or schedules it. So awaiting them one at a
# time is just... sequential code with extra keywords.

async def sequential() -> float:
    t0 = clock()
    task1 = fetch_data(1, 0.3)      # no execution yet
    task2 = fetch_data(2, 0.3)      # no execution yet
    await task1                     # 0.3s
    await task2                     # another 0.3s
    return clock() - t0

async def concurrent() -> float:
    t0 = clock()
    results = await asyncio.gather(
        fetch_data(1, 0.3),
        fetch_data(2, 0.3),
    )
    return clock() - t0

async def demo_2() -> None:
    print("2.1  sequential awaits:")
    s = await sequential()
    print(f"     -> {s:.2f}s   (0.3 + 0.3)")
    print("2.2  gather:")
    c = await concurrent()
    print(f"     -> {c:.2f}s   (max(0.3, 0.3))")

asyncio.run(demo_2())

# The tell: in 2.1 you see "1 starting / 1 done / 2 starting / 2 done".
# In 2.2 both start before either finishes. That interleaving IS concurrency.


# ==========================================================================
# 3. CREATING TASKS — three ways to run things at once
# ==========================================================================
async def demo_3() -> None:
    # (a) gather — simple, returns results in ARGUMENT order, not finish order
    t0 = clock()
    results = await asyncio.gather(fetch_data(1, 0.2), fetch_data(2, 0.1))
    print(f"3.1  gather order preserved: {[r['id'] for r in results]} in {clock()-t0:.2f}s")

    # gather swallows nothing by default: the first exception propagates,
    # but the other tasks keep running unsupervised. This flag collects
    # exceptions as values instead:
    async def boom() -> str:
        raise ValueError("failed")
    mixed = await asyncio.gather(fetch_data(3, 0.1), boom(), return_exceptions=True)
    print("3.2  return_exceptions:", [type(m).__name__ for m in mixed])

    # (b) create_task — start now, await later. Lets you do work in between.
    t0 = clock()
    task = asyncio.create_task(fetch_data(4, 0.2))
    print("3.3  doing other work while it runs...")
    result = await task
    print(f"     joined after {clock()-t0:.2f}s")

    # (c) TaskGroup (3.11+) — what your test.py uses, and the best default.
    # If ANY child fails, the rest are cancelled and errors are grouped.
    t0 = clock()
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_data(i, s))
                 for i, s in enumerate([0.2, 0.1, 0.3], start=5)]
    # the `async with` exits only when every child has finished
    print(f"3.4  TaskGroup: {[t.result()['id'] for t in tasks]} in {clock()-t0:.2f}s")

asyncio.run(demo_3())


# ==========================================================================
# 4. ERRORS IN A TaskGroup — ExceptionGroup and except*
# ==========================================================================
async def demo_4() -> None:
    async def ok() -> str:
        await asyncio.sleep(0.05)
        return "fine"
    async def bad(msg: str) -> None:
        await asyncio.sleep(0.01)
        raise ValueError(msg)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok())
            tg.create_task(bad("first"))
            tg.create_task(bad("second"))
    except* ValueError as eg:                # note the STAR
        print("4.1  ExceptionGroup caught:", [str(e) for e in eg.exceptions])

    # Two failures happened at once, so a single `except ValueError` could
    # not represent both. That's why TaskGroup raises ExceptionGroup and you
    # catch with `except*`. You can have several except* clauses; each gets
    # the subgroup matching its type.

asyncio.run(demo_4())


# ==========================================================================
# 5. *** BLOCKING THE EVENT LOOP — the production incident ***
# ==========================================================================
# One thread. If a coroutine does CPU work or calls a BLOCKING library, the
# entire loop stops. Every other request waits. This is the #1 async FastAPI
# bug and it doesn't show up until you have traffic.

async def demo_5() -> None:
    async def good() -> None:
        await asyncio.sleep(0.2)             # yields control

    async def bad() -> None:
        time.sleep(0.2)                      # BLOCKS everything, no await

    t0 = clock()
    await asyncio.gather(good(), good(), good())
    print(f"5.1  3x async sleep:    {clock()-t0:.2f}s  (concurrent)")

    t0 = clock()
    await asyncio.gather(bad(), bad(), bad())
    print(f"5.2  3x blocking sleep: {clock()-t0:.2f}s  (serialised!)")

    # The fix for a blocking call you cannot replace: push it to a thread.
    t0 = clock()
    await asyncio.gather(*(asyncio.to_thread(time.sleep, 0.2) for _ in range(3)))
    print(f"5.3  via asyncio.to_thread: {clock()-t0:.2f}s  (concurrent again)")

asyncio.run(demo_5())

# Practical rules for FastAPI:
#   - `requests` is BLOCKING. Never call it in an `async def` endpoint.
#     Use httpx.AsyncClient. (Your APIs/ folder uses requests — fine in a
#     script, wrong inside an async route.)
#   - A sync DB driver (psycopg2, sqlite3) blocks. Either use an async driver
#     (asyncpg, aiosqlite) or make the endpoint `def`, not `async def`.
#   - Heavy CPU work -> asyncio.to_thread, or a real background worker.


# ==========================================================================
# 6. *** def vs async def IN FASTAPI ***
# ==========================================================================
# This confuses everyone, and it is simple:
#
#   async def endpoint  -> runs ON the event loop.
#                          Fast, but you must never block inside it.
#
#   def endpoint        -> FastAPI runs it in a THREAD POOL automatically.
#                          Blocking is safe here. Slightly more overhead.
#
# So: if all your I/O libraries are async, use `async def`.
# If you're calling blocking libraries, plain `def` is the SAFER choice.
# The worst option is `async def` + blocking calls — that's §5.2.
#
# Your APIs/api.py declares `async def load_truck(...)` but the body is pure
# dict access with no await anywhere. It's harmless today, but the moment a
# blocking DB call goes in there it becomes a live version of 5.2.


# ==========================================================================
# 7. TIMEOUTS
# ==========================================================================
async def demo_7() -> None:
    async def slow() -> str:
        await asyncio.sleep(5)
        return "never gets here"

    try:
        async with asyncio.timeout(0.1):     # 3.11+, the modern form
            await slow()
    except TimeoutError:
        print("7.1  asyncio.timeout fired")

    try:
        await asyncio.wait_for(slow(), timeout=0.1)   # older equivalent
    except TimeoutError:
        print("7.2  wait_for fired")

asyncio.run(demo_7())


# ==========================================================================
# 8. CANCELLATION
# ==========================================================================
async def demo_8() -> None:
    async def worker() -> None:
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("8.2  worker noticed cancellation, cleaning up")
            raise                # ALWAYS re-raise; do not swallow it

    task = asyncio.create_task(worker())
    await asyncio.sleep(0.05)
    task.cancel()
    print("8.1  cancel() requested")
    try:
        await task
    except asyncio.CancelledError:
        print("8.3  confirmed cancelled")

    # Cleanup that must survive cancellation goes in `finally`, exactly like
    # Drill 06. That's why DB sessions use try/finally around the yield.

asyncio.run(demo_8())


# ==========================================================================
# 9. LIMITING CONCURRENCY — Semaphore
# ==========================================================================
# "Fetch 100 URLs" should not mean 100 simultaneous sockets. Cap it.

async def demo_9() -> None:
    sem = asyncio.Semaphore(3)
    active = 0
    peak = 0

    async def limited(i: int) -> None:
        nonlocal active, peak
        async with sem:                      # a context manager again
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.05)
            active -= 1

    await asyncio.gather(*(limited(i) for i in range(12)))
    print(f"9.1  12 tasks, peak concurrency was {peak} (cap was 3)")

asyncio.run(demo_9())


# ==========================================================================
# 10. as_completed — react as results land
# ==========================================================================
async def demo_10() -> None:
    coros = [fetch_data(i, s) for i, s in [(1, 0.3), (2, 0.1), (3, 0.2)]]
    print("10.1 results in COMPLETION order:")
    for coro in asyncio.as_completed(coros):
        r = await coro
        print("     got", r["id"])
    # gather gives argument order; as_completed gives finish order.

asyncio.run(demo_10())


# ==========================================================================
# EXERCISES
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# Rewrite this so it takes ~0.2s instead of ~0.6s. Keep the return order.
async def e1_sequential():
    a = await fetch_data(1, 0.2)
    b = await fetch_data(2, 0.2)
    c = await fetch_data(3, 0.2)
    return [a, b, c]
# t0 = clock(); r = asyncio.run(e1_sequential()); dt = clock() - t0
# assert dt < 0.35, f"still sequential: {dt:.2f}s"
# assert [x["id"] for x in r] == [1, 2, 3]

# --- E2 -------------------------------------------------------------------
# `fetch_all(ids)` runs fetch_data concurrently for every id with a TaskGroup
# and returns the results in id order.
async def fetch_all(ids: list[int]):
    pass
# r = asyncio.run(fetch_all([1, 2, 3]))
# assert [x["id"] for x in r] == [1, 2, 3]

# --- E3 -------------------------------------------------------------------
# `safe_fetch(id, timeout)` returns the result, or the string "timeout"
# if it takes too long. Use asyncio.timeout.
async def safe_fetch(id: int, sleep_time: float, timeout: float):
    pass
# assert asyncio.run(safe_fetch(1, 0.05, 0.5))["id"] == 1
# assert asyncio.run(safe_fetch(1, 1.0, 0.1)) == "timeout"

# --- E4 -------------------------------------------------------------------
# This blocks the loop. Fix it without removing the blocking call.
def blocking_hash(data: str) -> str:
    time.sleep(0.1)
    return data.upper()
async def e4_process(items: list[str]) -> list[str]:
    return [blocking_hash(i) for i in items]
# t0 = clock(); r = asyncio.run(e4_process(["a","b","c"])); dt = clock()-t0
# assert dt < 0.2, f"still blocking: {dt:.2f}s"
# assert r == ["A", "B", "C"]

# --- E5 -------------------------------------------------------------------
# Run 10 fetch_data calls but never more than 2 at once. Use a Semaphore.
# Assert the whole thing takes at least 5 * sleep_time.

# --- E6 -------------------------------------------------------------------
# Two of three tasks raise ValueError inside a TaskGroup. Catch with except*
# and return the sorted list of messages.
async def e6_collect():
    pass
# assert asyncio.run(e6_collect()) == ["first", "second"]

# --- E7 -------------------------------------------------------------------
# Write an async generator `stream_rows(n)` yielding "row-0".."row-{n-1}"
# with a small await between each, and consume it with `async for`.
# (Drill 06 §8 has the shape.)

print("Uncomment the asserts as you solve each one. Silence = all passed.")
